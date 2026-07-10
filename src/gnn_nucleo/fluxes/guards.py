"""Step-4 inherited invariants as programmatic guards (Step-5 Task 0).

Every flux/κ computation must pass through these guards. They encode the
blocking gates from STEP4_REPORT.md / docs/rate-crosscheck.md / RESULTS.md
(2026-07-10) as code, not comments:

1. **pf gate** — reverse rates must be ``DerivedRate(use_pf=True)`` or
   MESA-side. Raw JINA v-flag reverses are forbidden at T9 ≥ 3 (pf-free fits
   manufacture spurious κ floors up to 0.8 at NSE). The engine's regime box
   reaches T9 = 7.9, so compilation refuses v-flag reverses outright.
2. **Appendix-B routing** — channels listed in
   ``configs/appendixb_excluded_channels.yaml`` (gh-575 phase-space bug) must
   never take stock r23.05.1 values; only pynucastro-with-pf or MESA 24.08.1
   (``mesa_probe24``) values are admissible on them.
3. **Screening pin** — the labels used MESA ``'chugunov'`` ≡ pynucastro
   ``chugunov_2007`` (max |Δlog10| = 0.0021, docs/rate-crosscheck.md); the
   engine accepts exactly that, or ``None`` (screening off, validation only).
4. **ADR-0003** — only reconciled canonical builds feed the engine: the
   pinned tabular ordering and ``provisional_reaction_set == False``.

Deliberately light-weight: no pynucastro import at module scope so the
guards can gate cheap code paths (npz-only checks) without the heavy import.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import numpy as np

__all__ = [
    "PfGateError",
    "APPENDIXB_SOURCES",
    "SCREENING_ALLOWED",
    "assert_pf_gate",
    "assert_appendixb_routing",
    "assert_screening_allowed",
    "assert_reconciled_build",
]

_REPO = Path(__file__).resolve().parents[3]

#: admissible screening configurations (label config, or off for validation)
SCREENING_ALLOWED: frozenset[str | None] = frozenset({"chugunov_2007", None})

#: rate-source tags for Appendix-B routing checks. Matches the Step-4 variant
#: names (crosscheck.kappa): "mesa" = stock r23.05.1, "mesa24" = 24.08.1
#: probe (gh-575 fixed), "pyna_pf" = pynucastro with DerivedRate(use_pf=True).
APPENDIXB_SOURCES: frozenset[str] = frozenset({"mesa", "mesa24", "pyna_pf"})


class PfGateError(RuntimeError):
    """Raised when a flux/κ computation would use raw v-flag reverse rates.

    Step-4 blocking gate (RESULTS.md 2026-07-10; docs/rate-crosscheck.md
    §κ-floor): pf-free v-flag reverses manufacture spurious κ floors at
    T9 ≥ 3 and would corrupt the Target-A kill-test verdict.
    """


def assert_pf_gate(derived_from_inverse: np.ndarray | Iterable[bool], context: str) -> None:
    """Refuse any reaction set that still contains raw v-flag reverses.

    Parameters
    ----------
    derived_from_inverse : bool array, one entry per reaction column —
        True where the rate is a pf-free JINA v-flag reverse (the ν-export
        ``derived_from_inverse`` field, or recomputed from live Rate objects).
    context : str
        Where the check ran (network / call site), for the error message.
    """
    flags = np.asarray(list(derived_from_inverse) if not isinstance(
        derived_from_inverse, np.ndarray) else derived_from_inverse, dtype=bool)
    n_bad = int(flags.sum())
    if n_bad:
        raise PfGateError(
            f"{context}: {n_bad} raw JINA v-flag reverse rate(s) present — "
            "forbidden for any κ/flux computation at T9 ≥ 3 (Step-4 gate, "
            "RESULTS.md 2026-07-10). Rebuild reverses with "
            "DerivedRate(use_pf=True) (fluxes.db_reverses.replace_vflag_reverses) "
            "or take MESA-side rates."
        )


def _appendixb_handles(network: str) -> frozenset[str]:
    # thin local loader so the guard has no crosscheck import at module scope
    import yaml

    doc = yaml.safe_load(
        (_REPO / "configs" / "appendixb_excluded_channels.yaml").read_text()
    )
    return frozenset(c["mesa_handle"] for c in doc["networks"][network])


def assert_appendixb_routing(
    network: str, mesa_handles: Iterable[str], source: str
) -> None:
    """Refuse stock-r23.05.1 values on gh-575 Appendix-B channels.

    ``mesa_handles`` are the MESA handles whose rate values ``source``
    provides; raises if ``source == "mesa"`` (stock r23.05.1) intersects the
    excluded set for ``network``.
    """
    if source not in APPENDIXB_SOURCES:
        raise ValueError(
            f"unknown rate source tag {source!r}; expected one of "
            f"{sorted(APPENDIXB_SOURCES)}"
        )
    if source != "mesa":
        return
    excluded = _appendixb_handles(network)
    hit = sorted(excluded.intersection(mesa_handles))
    if hit:
        raise ValueError(
            f"{network}: stock r23.05.1 values requested on Appendix-B "
            f"(gh-575) excluded channel(s) {hit} — route via pynucastro-with-pf "
            "or mesa_probe24 (configs/appendixb_excluded_channels.yaml)"
        )


def assert_screening_allowed(screening: str | None) -> None:
    """Pin screening to the label configuration (or off, for validation)."""
    if screening not in SCREENING_ALLOWED:
        raise ValueError(
            f"screening {screening!r} not admissible: labels used MESA "
            "'chugunov' ≡ pynucastro chugunov_2007 (docs/rate-crosscheck.md); "
            "pass 'chugunov_2007' or None (off, validation only)"
        )


def assert_reconciled_build(info) -> None:
    """Refuse non-canonical rate-collection builds (ADR 0003).

    ``info`` is a ``graph.network.BuildInfo`` (duck-typed to keep this module
    import-light): the tabular ordering must be the pinned default and the
    build must be reconciled (``provisional_reaction_set`` False, i.e. a
    disposition file with zero MESA_ONLY entries was applied).
    """
    from gnn_nucleo.graph.network import DEFAULT_TABULAR_ORDERING

    if tuple(info.tabular_ordering) != DEFAULT_TABULAR_ORDERING:
        raise ValueError(
            f"{info.network}: tabular ordering {info.tabular_ordering!r} != "
            f"pinned ADR-0003 ordering {DEFAULT_TABULAR_ORDERING!r}"
        )
    if info.provisional_reaction_set:
        raise ValueError(
            f"{info.network}: provisional (non-reconciled) reaction set — "
            "build with disposition='auto' so the ADR-0003 disposition file "
            "is applied"
        )
