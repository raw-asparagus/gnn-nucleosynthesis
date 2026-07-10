"""Compile a canonical network into numpy tensors for batched rate evaluation.

One ``CompiledNetwork`` per network, built once: every ReacLib SingleSet
(forward fits as-is; ``DerivedRate(use_pf=True)`` derived sets for reverses)
stacked into an (n_sets, 7) coefficient tensor evaluated as one matmul over
the T-factor matrix; per-nucleus partition-function splines (rebuilt from
pynucastro's public fields, array-callable); tabular weak rates as vectorized
bilinear tables; chugunov_2007 screening over deduplicated pairs.

Column order is ``list(rc.get_rates())`` — identical to the ν export
(asserted against ``Stoich.rate_fnames``), so column j of every output aligns
with column j of ν.

The Step-4 pf gate is enforced HERE: compilation raises ``PfGateError`` if
any v-flag set survives (see ``guards``); every flux/κ entry point goes
through ``compile_network``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import yaml

from gnn_nucleo.graph.isotopes import load_isotope_table
from gnn_nucleo.graph.network import BuildInfo, build_rate_collection
from gnn_nucleo.graph.stoich import Stoich, build_stoich

from .db_reverses import ReplaceReport, replace_vflag_reverses
from .guards import assert_pf_gate, assert_reconciled_build, assert_screening_allowed

__all__ = ["CompiledNetwork", "compile_network"]

_REPO = Path(__file__).resolve().parents[3]


@dataclass
class CompiledNetwork:
    """All tensors needed to evaluate every rate over a batch of states."""

    network: str
    screening: str | None
    stoich: Stoich
    info: BuildInfo
    replace_report: ReplaceReport
    rates: list  # live Rate objects, column order (validation oracle only)

    # ReacLib/Derived coefficient tensor
    coeffs: np.ndarray  # (n_sets, 7) float64
    set_owner: np.ndarray  # (n_sets,) int64 — owning reaction column
    set_starts: np.ndarray  # (n_owned,) int64 — reduceat boundaries
    owned_cols: np.ndarray  # (n_owned,) int64 — column of each reduceat row
    set_labelprops: tuple[str, ...]  # per-set ReacLib labelprops (guard/tests)

    # partition-function correction (DerivedRate columns only)
    pf_nuclei: tuple[str, ...]
    pf_splines: list  # scipy splines over T9 → log(pf), ext='const'
    pf_matrix: sp.csr_matrix  # (n_rxn, n_pf) ± counts (source reac + / prod −)

    # tabular weak rates
    tab_cols: np.ndarray  # (n_tab,) int64
    tab_rhoy: list  # per rate: (n_rhoy,) log10(ρYₑ) grid
    tab_temp: list  # per rate: (n_temp,) log10(T) grid
    tab_rate2d: list  # per rate: (n_rhoy, n_temp) log10(rate)

    # ydot prefactors
    prefactor: np.ndarray  # (n_rxn,) float64 — 1/Π count! double-counting
    dens_exp: np.ndarray  # (n_rxn,) int64 — n_reactants − 1 (+1 if ye-weighted)
    reactant_idx: np.ndarray  # (n_rxn, max_nr) int64, sentinel = n_species
    ye_weighted: np.ndarray  # (n_rxn,) bool — REACLIB EC rates carrying ρYₑ

    # screening
    screen_pairs: np.ndarray  # (n_pairs, 4) int64 — z1, a1, z2, a2
    screen_map: sp.csr_matrix  # (n_rxn, n_pairs) pair multiplicities

    # forward/reverse pair view
    pair_col: np.ndarray  # (n_rxn,) int64, −1 = unpaired (all weak are −1)
    is_forward_member: np.ndarray  # (n_rxn,) bool

    # bookkeeping masks
    appendixb_cols: np.ndarray = field(default=None)  # (n_rxn,) bool
    weak_offnode_risky: np.ndarray = field(default=None)  # (n_rxn,) bool (β⁻ tabular)

    @property
    def n_reactions(self) -> int:
        return self.stoich.n_reactions


def _appendixb_columns(network: str, rate_fnames: tuple[str, ...]) -> np.ndarray:
    """Columns whose channel is Appendix-B excluded (gh-575), mapped via the
    disposition file's mesa_handle ↔ pyna_fname pairing."""
    short = network.replace("_", "")
    appb = yaml.safe_load(
        (_REPO / "configs" / "appendixb_excluded_channels.yaml").read_text()
    )
    handles = {c["mesa_handle"] for c in appb["networks"][network]}
    disp = yaml.safe_load(
        (_REPO / "configs" / f"reaction_disposition_{short}.yaml").read_text()
    )
    fnames = {
        e["pyna_fname"]
        for e in disp["entries"]
        if e.get("mesa_handle") in handles and "pyna_fname" in e
    }
    col_of = {f: i for i, f in enumerate(rate_fnames)}
    mask = np.zeros(len(rate_fnames), dtype=bool)
    for f in fnames:
        if f in col_of:
            mask[col_of[f]] = True
    return mask


def _pair_maps(stoich: Stoich, keys: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """pair_col / is_forward_member from canonical directed keys.

    Weak columns are ALWAYS unpaired (β/EC are not detailed-balance partners;
    their κ ≡ 1 and they never enter the equilibrium mask — CLAUDE.md
    invariant #2). Forward member = the non-v-flag column when exactly one of
    the pair was a v-flag reverse, else the lexicographically smaller fname
    (mirrors crosscheck.kappa.strong_pairs).
    """
    from gnn_nucleo.crosscheck.canonical import reverse_key

    r = stoich.n_reactions
    col_by_key: dict[str, int] = {}
    for j in range(r):
        if stoich.weak_mask[j]:
            continue
        col_by_key[keys[j]] = j

    pair_col = np.full(r, -1, dtype=np.int64)
    is_fwd = np.zeros(r, dtype=bool)
    for j in range(r):
        if stoich.weak_mask[j]:
            continue
        k = col_by_key.get(reverse_key(keys[j]))
        if k is None:
            is_fwd[j] = True  # unpaired strong columns count as net carriers
            continue
        pair_col[j] = k
        dj = bool(stoich.derived_from_inverse[j])
        dk = bool(stoich.derived_from_inverse[k])
        if dj != dk:
            is_fwd[j] = dk  # forward = the member that was NOT the v-flag
        else:
            is_fwd[j] = stoich.rate_fnames[j] < stoich.rate_fnames[k]
    return pair_col, is_fwd


def compile_network(
    network: str, *, screening: str | None = "chugunov_2007"
) -> CompiledNetwork:
    """Build the compiled evaluator for ``network`` (canonical set only)."""
    import pynucastro as pyna
    from scipy.interpolate import InterpolatedUnivariateSpline

    from gnn_nucleo.crosscheck.canonical import directed_key, from_pyna

    assert_screening_allowed(screening)
    table = load_isotope_table(network)
    rc, info = build_rate_collection(table)  # disposition="auto"
    assert_reconciled_build(info)
    stoich = build_stoich(rc, table)

    rates, report = replace_vflag_reverses(rc, table)
    # Column identity: replacement is positional and participant-preserving
    # (multisets asserted inside replace_vflag_reverses). fnames swap the
    # label suffix (_reaclib → _derived) on replaced columns ONLY; the
    # canonical column names remain stoich.rate_fnames (the ν-export names).
    if len(rates) != stoich.n_reactions:
        raise ValueError(f"{network}: rate count changed by v-flag replacement")
    for j, r in enumerate(rates):
        if r.fname != stoich.rate_fnames[j] and not (
            stoich.derived_from_inverse[j]
            and isinstance(r, pyna.rates.DerivedRate)
        ):
            raise ValueError(
                f"{network}: column {j} changed unexpectedly "
                f"({stoich.rate_fnames[j]} → {r.fname})"
            )

    n_rxn = stoich.n_reactions
    idx = table.index()
    n_species = table.n

    coeff_rows: list[np.ndarray] = []
    set_owner: list[int] = []
    set_labelprops: list[str] = []

    pf_index: dict[str, int] = {}
    pf_splines: list = []
    pf_entries: dict[tuple[int, int], float] = {}

    tab_cols: list[int] = []
    tab_rhoy: list[np.ndarray] = []
    tab_temp: list[np.ndarray] = []
    tab_rate2d: list[np.ndarray] = []

    def _pf_col(nuc) -> int | None:
        pf = nuc.partition_function
        if pf is None:
            return None
        name = str(nuc)
        if name not in pf_index:
            pf_index[name] = len(pf_splines)
            pf_splines.append(
                InterpolatedUnivariateSpline(
                    pf.T9_points, pf.log_pf_data, k=pf.interpolant_order, ext="const"
                )
            )
        return pf_index[name]

    for j, rate in enumerate(rates):
        if isinstance(rate, pyna.rates.TabularRate):
            data = rate.tabular_data_table
            n_temp = int(rate.table_temp_lines)
            rhoy = data[::n_temp, 0].copy()
            temp = data[:n_temp, 1].copy()
            f2d = data[:, 5].reshape(len(rhoy), n_temp).copy()
            tab_cols.append(j)
            tab_rhoy.append(rhoy)
            tab_temp.append(temp)
            tab_rate2d.append(f2d)
            continue
        if isinstance(rate, pyna.rates.DerivedRate):
            if rate.derived_sets is None:
                raise ValueError(f"{network}: {rate.fname} has no derived sets")
            sets = rate.derived_sets
            for nuc in rate.source_rate.reactants:
                m = _pf_col(nuc)
                if m is not None:
                    pf_entries[(j, m)] = pf_entries.get((j, m), 0.0) + 1.0
            for nuc in rate.source_rate.products:
                m = _pf_col(nuc)
                if m is not None:
                    pf_entries[(j, m)] = pf_entries.get((j, m), 0.0) - 1.0
        elif isinstance(rate, pyna.rates.ReacLibRate):
            sets = rate.sets
        else:
            raise TypeError(f"{network}: unsupported rate type {type(rate)!r}")
        for s in sets:
            coeff_rows.append(np.asarray(s.a, dtype=np.float64))
            set_owner.append(j)
            set_labelprops.append(s.labelprops)

    # ---- pf gate: no v-flag set may survive compilation --------------------
    vflag_sets = np.array([lp[5] == "v" for lp in set_labelprops], dtype=bool)
    assert_pf_gate(vflag_sets, context=f"{network} compiled set tensor")
    if report.failed:
        raise ValueError(
            f"{network}: v-flag replacement failed for {report.failed} — "
            "route those channels via mesa_probe24 or record an "
            "exclude-with-footnote decision before compiling"
        )

    coeffs = np.vstack(coeff_rows)
    set_owner_arr = np.asarray(set_owner, dtype=np.int64)
    if np.any(np.diff(set_owner_arr) < 0):
        raise ValueError(f"{network}: set tensor not grouped by column")
    set_starts = np.flatnonzero(np.r_[True, np.diff(set_owner_arr) != 0])
    owned_cols = set_owner_arr[set_starts]

    pf_matrix = sp.csr_matrix((n_rxn, len(pf_splines)), dtype=np.float64)
    if pf_entries:
        rows, cols, vals = zip(
            *[(rj, m, v) for (rj, m), v in pf_entries.items() if v != 0.0]
        )
        pf_matrix = sp.csr_matrix(
            (vals, (rows, cols)), shape=(n_rxn, len(pf_splines)), dtype=np.float64
        )

    # ---- ydot prefactors ----------------------------------------------------
    prefactor = np.empty(n_rxn, dtype=np.float64)
    dens_exp = np.empty(n_rxn, dtype=np.int64)
    max_nr = max(len(r.reactants) for r in rates)
    reactant_idx = np.full((n_rxn, max_nr), n_species, dtype=np.int64)
    ye_weighted = np.zeros(n_rxn, dtype=bool)
    for j, rate in enumerate(rates):
        # REACLIB electron-capture fits (e.g. be7 EC) carry ρYₑ: pynucastro
        # sets use_ye_weighting, increments dens_exp, and multiplies by Yₑ in
        # eval_full_rate — mirrored in engine.evaluate_fluxes
        ye_weighted[j] = bool(getattr(rate, "use_ye_weighting", False))
        prefactor[j] = rate.prefactor
        dens_exp[j] = rate.dens_exp
        for k, nuc in enumerate(rate.reactants):
            reactant_idx[j, k] = idx[nuc]  # index keyed by Nucleus (as build_stoich)

    # ---- screening pairs -----------------------------------------------------
    pair_index: dict[tuple[int, int, int, int], int] = {}
    pair_rows: list[int] = []
    pair_cols_: list[int] = []
    pair_vals: list[float] = []
    for j, rate in enumerate(rates):
        for n1, n2 in getattr(rate, "screening_pairs", []):
            key = (int(n1.Z), int(n1.A), int(n2.Z), int(n2.A))
            if key not in pair_index:
                pair_index[key] = len(pair_index)
            pair_rows.append(j)
            pair_cols_.append(pair_index[key])
            pair_vals.append(1.0)
    screen_pairs = np.array(sorted(pair_index, key=pair_index.get), dtype=np.int64)
    screen_pairs = screen_pairs.reshape(-1, 4) if screen_pairs.size else np.zeros(
        (0, 4), dtype=np.int64
    )
    screen_map = sp.csr_matrix(
        (pair_vals, (pair_rows, pair_cols_)),
        shape=(n_rxn, len(pair_index)),
        dtype=np.float64,
    )

    # ---- pair view ------------------------------------------------------------
    keys = [
        directed_key(
            [from_pyna(n) for n in r.reactants], [from_pyna(n) for n in r.products]
        )
        for r in rates
    ]
    pair_col, is_forward = _pair_maps(stoich, keys)

    weak_risky = stoich.weak_mask & stoich.is_tabular & (
        np.asarray(stoich.weak_type) == "beta_neg"
    )

    return CompiledNetwork(
        network=network,
        screening=screening,
        stoich=stoich,
        info=info,
        replace_report=report,
        rates=rates,
        coeffs=coeffs,
        set_owner=set_owner_arr,
        set_starts=set_starts,
        owned_cols=owned_cols,
        set_labelprops=tuple(set_labelprops),
        pf_nuclei=tuple(sorted(pf_index, key=pf_index.get)),
        pf_splines=pf_splines,
        pf_matrix=pf_matrix,
        tab_cols=np.asarray(tab_cols, dtype=np.int64),
        tab_rhoy=tab_rhoy,
        tab_temp=tab_temp,
        tab_rate2d=tab_rate2d,
        prefactor=prefactor,
        dens_exp=dens_exp,
        reactant_idx=reactant_idx,
        ye_weighted=ye_weighted,
        screen_pairs=screen_pairs,
        screen_map=screen_map,
        pair_col=pair_col,
        is_forward_member=is_forward,
        appendixb_cols=_appendixb_columns(network, stoich.rate_fnames),
        weak_offnode_risky=weak_risky,
    )
