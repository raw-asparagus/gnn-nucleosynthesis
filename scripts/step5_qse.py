#!/usr/bin/env python
"""Step-5 Task 3: independent QSE/NSE solver — cross-check + diagnostics.

Parts (RESULTS.md-ready output):
1. NSE cross-check vs pynucastro's solver on the canonical 27-state grid
   (T9 ∈ {5, 6.3, 7.9} × ρ × Yₑ; shared nuclear inputs ⇒ near-exact expected).
2. Trajectory diagnostics on the high-T9 selected trajectories:
   - r_QSE = log10(Y_ref/Y) intra-group plateau (operational QSE signature);
   - δ_r ↔ κ_r consistency: Spearman correlation between the Guidry
     reaction-level departure (vs NSE) and the UNSCREENED cancellation ratio
     (screening breaks pair DB symmetry — RESULTS.md 2026-07-10), over strong
     forward columns at late trajectory times.

Usage: uv run python scripts/step5_qse.py --net mesa_80
"""

from __future__ import annotations

import argparse
import warnings

import numpy as np


def crosscheck_27grid(net: str) -> None:
    from gnn_nucleo.crosscheck.grids import RHO_GRID, T9_NSE, YE_GRID, state_grid
    from gnn_nucleo.crosscheck.kappa import nse_composition
    from gnn_nucleo.graph import load_isotope_table
    from gnn_nucleo.qse import build_inputs, solve_nse

    inputs = build_inputs(net)
    nuclei = list(load_isotope_table(net).nuclei)
    worst = 0.0
    n_ok = n_pyna_fail = 0
    methods = {}
    for t9, rho, ye in state_grid(T9_NSE):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            comp, ok = nse_composition(net, t9, rho, ye)
        if not ok:
            n_pyna_fail += 1
            continue
        res = solve_nse(inputs, t9 * 1e9, rho, ye)
        assert res.converged, f"our solver failed at {(t9, rho, ye)}"
        methods[res.method] = methods.get(res.method, 0) + 1
        ref = np.array([comp.X[n] for n in nuclei])
        m = ref > 1e-10
        dlog = np.abs(np.log10(res.X[m]) - np.log10(ref[m])).max()
        worst = max(worst, dlog)
        n_ok += 1
    n_grid = len(T9_NSE) * len(RHO_GRID) * len(YE_GRID)
    print(f"== {net} NSE cross-check on the {n_grid}-state grid ==")
    print(f"  compared {n_ok} states (pyna unconverged: {n_pyna_fail})")
    print(f"  max |dlog10 X| over X > 1e-10: {worst:.3e}  (gate 1e-6)")
    print(f"  our solver methods: {methods}")


def trajectory_diagnostics(net: str, t9_min: float = 3.5) -> None:
    from scipy.stats import spearmanr

    from gnn_nucleo.data.trajectories import load_trajectory
    from gnn_nucleo.data.trajectories import stall_row as tj_stall_row
    from gnn_nucleo.fluxes.compile import compile_network
    from gnn_nucleo.fluxes.engine import evaluate_fluxes
    from gnn_nucleo.fluxes.store import FluxStore
    from gnn_nucleo.qse import (
        build_inputs,
        delta_species,
        load_group_mask,
        r_qse,
        reaction_delta,
        solve_nse,
        solve_qse,
    )

    inputs = build_inputs(net)
    A = inputs.A
    group = load_group_mask(net)
    group_alt = load_group_mask(net, "a28_up")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        cn0 = compile_network(net, screening=None)
    strong_fwd = cn0.is_forward_member & (cn0.pair_col >= 0)

    store = FluxStore(net, "trajectories")
    rows_all = []
    plateau_rows = 0
    checked_rows = 0
    corr_pairs_k = []
    corr_pairs_d = []
    stall_report = []
    for chunk in store.iter_chunks():
        t9 = 10.0 ** chunk.attrs["logT"] / 1e9
        if t9 < t9_min:
            continue
        rho = 10.0 ** chunk.attrs["logRho"]
        fname = chunk.attrs["trajectory_file"]
        traj = load_trajectory(net, fname)
        X = traj.X
        age = traj.age
        # historical Step-5 selection: rows before ARRIVAL AT THE ATTRACTOR
        # (first-quiet rule; reinterpretation RESULTS.md 2026-07-11)
        stall_row = tj_stall_row(X, mode="first_quiet")
        stall_report.append((fname, t9, stall_row, float(age[stall_row])))
        # sample pre-stall mid-burn rows, log-spaced
        lo = int(np.searchsorted(age, 1e-6))
        rows = sorted(
            set(np.unique(np.geomspace(max(lo, 1), max(stall_row - 1, 2), 12).astype(int)))
        )
        for k in rows:
            Y = X[k] / A
            ye = float((inputs.Z * Y).sum() / (A * Y).sum())
            nse = solve_nse(inputs, t9 * 1e9, rho, ye)
            if not nse.converged:
                continue
            gm = float(X[k][group].sum())
            if not 1e-8 < gm < 1.0 - 1e-8:
                continue
            qse = solve_qse(inputs, t9 * 1e9, rho, ye, group, gm)
            if not qse.converged:
                continue
            checked_rows += 1
            Y_qse = qse.X / A
            rq = r_qse(Y, Y_qse)
            present = X[k] > 1e-8
            g_in = group & present
            g_out = (~group) & present & (inputs.Z > 2)
            if g_in.sum() >= 5 and g_out.sum() >= 3:
                in_std = float(np.std(rq[g_in]))
                out_spread = float(np.std(rq[g_out]))
                rows_all.append((t9, in_std, out_spread, float(qse.u_group)))
                if in_std < 0.1:
                    plateau_rows += 1
            # kappa (unscreened) vs delta_r on this row
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                b = evaluate_fluxes(
                    cn0,
                    np.array([t9 * 1e9]),
                    np.array([rho]),
                    Y[:, None],
                )
            delta = delta_species(Y, nse.X / A)
            d_r = reaction_delta(cn0.stoich.nu, delta)
            k_r = b.kappa[:, 0]
            f_r = b.f_plus[:, 0]
            sel = strong_fwd & (f_r > 0) & np.isfinite(d_r)
            carrying = f_r > np.median(f_r[sel & (f_r > 0)])
            m = sel & carrying
            corr_pairs_k.extend(np.log10(np.maximum(k_r[m], 1e-16)))
            corr_pairs_d.extend(np.log10(np.maximum(d_r[m], 1e-16)))

    print(f"\n== {net} trajectory QSE diagnostics (T9 ≥ {t9_min}, PRE-STALL rows) ==")
    if stall_report:
        ages = np.array([a for *_, a in stall_report])
        print(
            f"  trajectory stall census: {len(stall_report)} files, "
            f"stall ages median {np.median(ages):.2e} s "
            f"[min {ages.min():.2e}, max {ages.max():.2e}] — composition "
            "frozen at non-equilibrium states beyond (bbq artifact, see RESULTS)"
        )
    print(f"  rows checked: {checked_rows}")
    if rows_all:
        arr = np.array([(a, b, c) for a, b, c, _ in rows_all])
        print(
            f"  r_QSE intra-group std: median {np.median(arr[:, 1]):.4f} "
            f"(plateau rows, std<0.1: {plateau_rows}/{len(rows_all)})"
        )
        print(f"  r_QSE non-group spread: median {np.median(arr[:, 2]):.4f}")
        ug = np.array([u for *_, u in rows_all])
        p90u = np.quantile(np.abs(ug), 0.9)
        print(f"  u_group [MeV]: median {np.median(ug):+.4f}, p90 |u| {p90u:.4f}")
    if corr_pairs_k:
        rho_s, p = spearmanr(corr_pairs_k, corr_pairs_d)
        print(
            f"  Spearman(log κ_r [unscreened], log δ_r) over "
            f"{len(corr_pairs_k)} (row × carrying strong pair) samples: "
            f"{rho_s:.3f} (p={p:.1e})"
        )
        k_arr = np.array(corr_pairs_k)
        d_arr = np.array(corr_pairs_d)
        eq = d_arr < -2  # δ_r < 0.01
        if eq.any():
            print(
                f"  κ_r where δ_r < 0.01: median 10^{np.median(k_arr[eq]):.2f}"
                f"  vs δ_r ≥ 0.01: median 10^{np.median(k_arr[~eq]):.2f}"
            )
    # group-rule sensitivity: report the two variants' member counts
    print(
        f"  group sizes: default(24≤A<45) {int(group.sum())} species, "
        f"a28_up(A≥28) {int(group_alt.sum())} species"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--net", required=True, choices=["mesa_80", "mesa_151"])
    ap.add_argument("--skip-trajectories", action="store_true")
    args = ap.parse_args()
    crosscheck_27grid(args.net)
    if not args.skip_trajectories:
        trajectory_diagnostics(args.net)


if __name__ == "__main__":
    main()
