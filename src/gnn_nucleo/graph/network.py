"""pynucastro rate-collection construction for the project networks.

Builds REACLIB strong/EM rates (with detailed-balance reverse rates as
pynucastro derives them) plus tabulated weak rates linking exactly the
network's isotopes, resolving ReacLib-vs-tabular duplicate links in favour of
the tabular rate.

PROVISIONAL REACTION SET: pynucastro's REACLIB-filtered set for an isotope
list is NOT guaranteed to match MESA r23.05.1's softwired net for the same
list, and pynucastro's tabular-source precedence (default ffn < oda <
pruet_fuller < langanke < suzuki, later wins) is not MESA weaklib's.
``BuildInfo.provisional_reaction_set`` stays True until the Step-4 MESA/bbq
cross-check; never assume equivalence silently.
"""

from __future__ import annotations

from dataclasses import dataclass

import pynucastro as pyna

from .isotopes import IsotopeTable

#: pynucastro 2.12.0 default tabular-source precedence (later overrides earlier).
DEFAULT_TABULAR_ORDERING: tuple[str, ...] = (
    "ffn", "oda", "pruet_fuller", "langanke", "suzuki",
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


def build_rate_collection(
    table: IsotopeTable,
    tabular_ordering: tuple[str, ...] | None = None,
) -> tuple[pyna.RateCollection, BuildInfo]:
    """Build the RateCollection for ``table``'s isotopes.

    Duplicate links (same reactants → products covered by both a ReacLib rate
    and a tabular weak rate) are resolved by dropping the ReacLib member —
    tabular weak rates are the (T, ρYₑ)-dependent ones the Yₑ physics needs.
    The nucleus set of the result must equal the table exactly.
    """
    ordering = tuple(tabular_ordering) if tabular_ordering else DEFAULT_TABULAR_ORDERING
    nuclei = list(table.nuclei)

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
    )
    return rc, info
