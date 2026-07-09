"""pynucastro rate-collection construction for the project networks.

Builds REACLIB strong/EM rates (with detailed-balance reverse rates as
pynucastro derives them) plus tabulated weak rates linking exactly the
network's isotopes, resolving ReacLib-vs-tabular duplicate links in favour of
the tabular rate, then reconciling against MESA r23.05.1's softwired net
(Step 4, ADR 0003): PYNA_ONLY phantom channels recorded in
``configs/reaction_disposition_<net>.yaml`` are dropped, and the tabular
precedence reproduces MESA weaklib's LMP > Oda > FFN (measured via
scripts/reconcile_reactions.py; non-MESA tables ranked lowest).
``provisional_reaction_set`` flips to False only when a disposition file is
applied and it records zero MESA_ONLY entries.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pynucastro as pyna
import yaml

from .isotopes import IsotopeTable, canonical_network

_REPO = Path(__file__).resolve().parents[3]

#: Tabular-source precedence, later overrides earlier. Chosen to reproduce
#: MESA weaklib's per-pair sources (LMP > Oda > FFN, use_suzuki=.false. —
#: the training-label configuration) on every matched weak pair; tables MESA
#: does not use (suzuki, pruet_fuller) rank lowest. Step 4, ADR 0003;
#: measured by scripts/reconcile_reactions.py. The pre-Step-4 provisional
#: ordering was ("ffn", "oda", "pruet_fuller", "langanke", "suzuki").
DEFAULT_TABULAR_ORDERING: tuple[str, ...] = (
    "suzuki", "pruet_fuller", "ffn", "oda", "langanke",
)


@dataclass(frozen=True)
class BuildInfo:
    """Provenance of one rate-collection build (goes into the npz metadata)."""

    network: str
    pynucastro_version: str
    tabular_ordering: tuple[str, ...]
    n_reaclib: int
    n_tabular: int
    n_duplicate_groups_resolved: int
    provisional_reaction_set: bool = True
    disposition_sha256: str = ""
    n_dropped: int = 0


def disposition_path(network: str) -> Path:
    short = canonical_network(network).replace("_", "")
    return _REPO / "configs" / f"reaction_disposition_{short}.yaml"


def load_drop_list(network: str) -> tuple[frozenset[str], str]:
    """PYNA_ONLY fnames to drop + sha256 of the disposition file.

    Raises if the disposition records MESA_ONLY entries: those would demand
    ADDING physics the graph lacks, which cannot be done by filtering —
    the reconciliation must be redone before the build can proceed.
    """
    path = disposition_path(network)
    doc = yaml.safe_load(path.read_text())
    if doc["tallies"].get("MESA_ONLY", 0) != 0:
        raise ValueError(
            f"{network}: disposition file records MESA_ONLY entries — the "
            "graph is missing MESA physics; re-run the reconciliation "
            "(scripts/reconcile_reactions.py) and resolve before building"
        )
    drops = frozenset(
        e["pyna_fname"]
        for e in doc["entries"]
        if e["disposition"] == "PYNA_ONLY"
    )
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return drops, sha


def build_rate_collection(
    table: IsotopeTable,
    tabular_ordering: tuple[str, ...] | None = None,
    disposition: str | None = "auto",
) -> tuple[pyna.RateCollection, BuildInfo]:
    """Build the RateCollection for ``table``'s isotopes.

    Duplicate links (same reactants → products covered by both a ReacLib rate
    and a tabular weak rate) are resolved by dropping the ReacLib member —
    tabular weak rates are the (T, ρYₑ)-dependent ones the Yₑ physics needs.
    The nucleus set of the result must equal the table exactly.

    ``disposition="auto"`` applies configs/reaction_disposition_<net>.yaml
    when present (drops PYNA_ONLY channels; flips provisional_reaction_set
    to False); ``disposition=None`` builds the raw pynucastro set.
    """
    ordering = tuple(tabular_ordering) if tabular_ordering else DEFAULT_TABULAR_ORDERING
    nuclei = list(table.nuclei)

    drop_fnames: frozenset[str] = frozenset()
    disposition_sha = ""
    if disposition == "auto":
        if disposition_path(table.network).exists():
            drop_fnames, disposition_sha = load_drop_list(table.network)
    elif disposition is not None:
        raise ValueError(f"disposition must be 'auto' or None, got {disposition!r}")

    reaclib = pyna.ReacLibLibrary().linking_nuclei(nuclei)
    tabular = pyna.TabularLibrary(ordering=list(ordering)).linking_nuclei(
        nuclei, print_warning=False
    )
    full = reaclib + tabular

    dup_groups = full.find_duplicate_links()
    for group in dup_groups:
        survivors = []
        for rate in group:
            if isinstance(rate, pyna.rates.TabularRate):
                survivors.append(rate)
            else:
                full.remove_rate(rate)
        if len(survivors) != 1:
            raise ValueError(
                f"{table.network}: duplicate link {group} did not resolve to exactly "
                f"one tabular rate ({len(survivors)} survivors)"
            )

    if drop_fnames:
        dropped = 0
        for rate in list(full.get_rates()):
            if rate.fname in drop_fnames:
                full.remove_rate(rate)
                dropped += 1
        if dropped != len(drop_fnames):
            raise ValueError(
                f"{table.network}: disposition drop list has {len(drop_fnames)} "
                f"fnames but only {dropped} matched the built collection — "
                "stale disposition file, re-run scripts/reconcile_reactions.py"
            )

    rc = pyna.RateCollection(libraries=[full])

    got = set(rc.unique_nuclei)
    want = set(nuclei)
    if got != want:
        raise ValueError(
            f"{table.network}: rate collection nuclei != isotope table; "
            f"missing={sorted(str(n) for n in want - got)}, "
            f"extra={sorted(str(n) for n in got - want)}"
        )

    rates = rc.get_rates()
    n_tab = sum(isinstance(r, pyna.rates.TabularRate) for r in rates)
    info = BuildInfo(
        network=table.network,
        pynucastro_version=pyna.__version__,
        tabular_ordering=ordering,
        n_reaclib=len(rates) - n_tab,
        n_tabular=n_tab,
        n_duplicate_groups_resolved=len(dup_groups),
        # ADR 0003: reconciled against MESA's softwired net iff a disposition
        # with zero MESA_ONLY entries was applied (load_drop_list enforces).
        provisional_reaction_set=not disposition_sha,
        disposition_sha256=disposition_sha,
        n_dropped=len(drop_fnames),
    )
    return rc, info
