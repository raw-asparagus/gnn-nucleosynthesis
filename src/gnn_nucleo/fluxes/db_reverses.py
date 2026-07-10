"""Replace pf-free JINA v-flag reverse rates with DerivedRate(use_pf=True).

Step-4 blocking gate (RESULTS.md 2026-07-10; docs/rate-crosscheck.md
§κ-floor): the canonical rate collections carry REACLIB v-flag reverses whose
fits ignore partition functions; at T9 ≥ 3 these manufacture spurious κ
floors up to 0.8 at NSE. Every flux/κ computation must instead derive the
reverse from its forward partner via detailed balance WITH partition
functions — pynucastro's ``DerivedRate(source_rate=fwd, use_pf=True)``.

Replacement is positional: the returned rate list preserves the collection's
column order, and every replaced column is asserted to keep its exact
reactant/product multisets — ν is untouched.
"""

from __future__ import annotations

import warnings
from collections import Counter
from dataclasses import dataclass

from gnn_nucleo.crosscheck.canonical import directed_key, from_pyna, reverse_key
from gnn_nucleo.graph.isotopes import IsotopeTable

from .guards import assert_reconciled_build

__all__ = ["ReplaceReport", "replace_vflag_reverses"]


@dataclass(frozen=True)
class ReplaceReport:
    """Outcome of one v-flag replacement pass (goes into run provenance)."""

    network: str
    n_rates: int
    n_vflag: int
    n_replaced: int
    n_forward_in_collection: int
    n_forward_from_library: int
    #: (fname, reason) for channels DerivedRate could not be built for —
    #: must be empty for the pf gate to pass; non-empty means those channels
    #: need mesa_probe24 values or an exclude-with-footnote decision.
    failed: tuple[tuple[str, str], ...]
    #: nuclei lacking pf tables (log_pf = 0 fallback, same as pynucastro)
    missing_pf_nuclei: tuple[str, ...]


def _key_of(rate) -> str:
    return directed_key(
        [from_pyna(n) for n in rate.reactants],
        [from_pyna(n) for n in rate.products],
    )


def _is_raw_vflag(rate) -> bool:
    import pynucastro as pyna

    return isinstance(rate, pyna.rates.ReacLibRate) and bool(
        getattr(rate, "derived_from_inverse", False)
    )


def replace_vflag_reverses(
    rc, table: IsotopeTable, info=None
) -> tuple[list, ReplaceReport]:
    """Return ``rc``'s rates in collection order with every raw v-flag
    reverse replaced by ``DerivedRate(source_rate=forward, use_pf=True)``.

    The forward partner is looked up by canonical directed key first within
    the collection itself, then in the raw ``ReacLibLibrary`` linking the same
    nuclei (covers forwards absent from the reconciled set). Channels where
    DerivedRate construction fails (missing spin states) are reported in
    ``ReplaceReport.failed`` and left UNREPLACED — the compile-level pf gate
    will then refuse the set, forcing an explicit decision.
    """
    import pynucastro as pyna

    if info is not None:
        assert_reconciled_build(info)

    rates = list(rc.get_rates())
    by_key: dict[str, object] = {}
    for r in rates:
        if isinstance(r, pyna.rates.TabularRate) or getattr(r, "weak", False):
            continue
        by_key.setdefault(_key_of(r), r)

    fallback_library = None  # built lazily; ~seconds

    def _forward_for(rev):
        nonlocal fallback_library
        fwd_key = reverse_key(_key_of(rev))
        cand = by_key.get(fwd_key)
        if cand is not None and not _is_raw_vflag(cand):
            return cand, "collection"
        if fallback_library is None:
            fallback_library = pyna.ReacLibLibrary().linking_nuclei(
                list(table.nuclei)
            )
        for r in fallback_library.get_rates():
            if _is_raw_vflag(r) or getattr(r, "weak", False):
                continue
            if _key_of(r) == fwd_key:
                return r, "library"
        return None, "no forward partner found"

    out: list = []
    failed: list[tuple[str, str]] = []
    n_vflag = n_replaced = n_in_rc = n_in_lib = 0
    missing_pf: set[str] = set()

    for rate in rates:
        if not _is_raw_vflag(rate):
            out.append(rate)
            continue
        n_vflag += 1
        fwd, where = _forward_for(rate)
        if fwd is None:
            failed.append((rate.fname, where))
            out.append(rate)
            continue
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", UserWarning)
                derived = pyna.rates.DerivedRate(source_rate=fwd, use_pf=True)
            for w in caught:
                msg = str(w.message)
                if "partition function is not supported" in msg:
                    missing_pf.add(msg.split(" ", 1)[0])
        except (ValueError, TypeError) as exc:
            failed.append((rate.fname, f"DerivedRate failed: {exc}"))
            out.append(rate)
            continue

        if Counter(map(str, derived.reactants)) != Counter(
            map(str, rate.reactants)
        ) or Counter(map(str, derived.products)) != Counter(map(str, rate.products)):
            raise ValueError(
                f"{table.network}: replacement for {rate.fname} changed the "
                "reactant/product multisets — ν column identity broken"
            )
        # missing pf tables also surface lazily at eval time; record the
        # source-side nuclei without tables now for the report
        for nuc in set(derived.source_rate.reactants + derived.source_rate.products):
            if nuc.partition_function is None and str(nuc) not in ("p", "n", "he4"):
                missing_pf.add(str(nuc))
        out.append(derived)
        n_replaced += 1
        if where == "collection":
            n_in_rc += 1
        else:
            n_in_lib += 1

    report = ReplaceReport(
        network=table.network,
        n_rates=len(rates),
        n_vflag=n_vflag,
        n_replaced=n_replaced,
        n_forward_in_collection=n_in_rc,
        n_forward_from_library=n_in_lib,
        failed=tuple(failed),
        missing_pf_nuclei=tuple(sorted(missing_pf)),
    )
    return out, report
