#!/usr/bin/env python
"""Validate the bbq rerun campaign (Step 6 Task 1.3) — RESULTS-ready numbers.

Checks, per network over all DONE runs:

1. STALL census: stall_row on every rerun. Frozen tails are EXPECTED where
   matter reached its terminal attractor; on stock r23.05.1 at T9 ≳ 5 that
   attractor is the Appendix-B DISPLACED pseudo-equilibrium, NOT true NSE
   (RESULTS.md 2026-07-11) — so frozen runs are classified by distance to
   NSE and reported, not gated. The failure signature to flag is freezing
   at LOW T9 far from any attractor with physical timescales still short
   (the shipped-data stall class).
2. Terminal T9 ≥ 5 states vs solve_nse: distance distribution (expected:
   the displaced attractor, several dex — measured, with the 24.08.1
   witness as the physics-true reference).
3. Early-time match vs shipped trajectories (family-1 runs share exact
   (logT, logRho, X₀) with a shipped file): per matched age point, the
   fraction of species with |X_rerun − X_shipped| ≤ max(0.05·max(X_r,X_s),
   1e-8) — same-code same-config runs, differing only in output cadence.
4. r_QSE plateau on clean relaxed rows (QSE-window runs): intra-group
   std(r_QSE) on late pre-stall rows — the deferred Step-5 measurement.

Usage: uv run python scripts/bbq_campaign/validate_campaign.py --net mesa_80
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]


def load_done_runs(net: str):
    from gnn_nucleo.data.trajectories import load_trajectory

    manifest = yaml.safe_load(
        (REPO / "data/bbq_reruns" / net / "campaign.yaml").read_text()
    )
    for spec in manifest["runs"]:
        rd = REPO / "data/bbq_reruns" / net / spec["run_key"]
        if not (rd / "DONE").exists():
            continue
        traj = load_trajectory(
            net, rd / "output.txt", source="rerun",
            logT=float(spec["logT"]), logRho=float(spec["logRho"]),
        )
        yield spec, traj


def stall_and_terminal(net: str) -> None:
    from gnn_nucleo.data.trajectories import stall_row
    from gnn_nucleo.graph import load_isotope_table
    from gnn_nucleo.qse import build_inputs, solve_nse

    table = load_isotope_table(net)
    A = table.A.astype(float)
    Z = table.Z.astype(float)
    inputs = build_inputs(net)
    census = {"evolving-at-wall": 0, "frozen": 0}
    frozen_t9 = []
    nse_d_hot, nse_d_frozen_cold = [], []
    n = 0
    for spec, traj in load_done_runs(net):
        n += 1
        sr = stall_row(traj.X)
        t9 = spec["t9"]
        frozen = sr < traj.n_rows - 1
        census["frozen" if frozen else "evolving-at-wall"] += 1
        if frozen:
            frozen_t9.append(t9)
        Xe = traj.X[-1]
        ye = float(Xe @ (Z / A))
        if t9 >= 5.0 or (frozen and t9 < 3.3):
            nse = solve_nse(inputs, t9 * 1e9, 10.0 ** spec["logRho"], ye)
            if nse.converged:
                m = (Xe > 1e-6) | (nse.X > 1e-6)
                d = np.abs(
                    np.log10(np.maximum(Xe[m], 1e-15))
                    - np.log10(np.maximum(nse.X[m], 1e-15))
                ).max()
                (nse_d_hot if t9 >= 5.0 else nse_d_frozen_cold).append(d)
    print(f"== {net} stall census ({n} runs) ==")
    print(f"  frozen before wall: {census['frozen']}  "
          f"evolving at wall: {census['evolving-at-wall']}")
    if frozen_t9:
        ft = np.array(frozen_t9)
        print(f"  frozen-run T9: median {np.median(ft):.1f} "
              f"[min {ft.min():.1f}, max {ft.max():.1f}] "
              f"(frozen at T9 < 3.3: {int((ft < 3.3).sum())})")
    if nse_d_hot:
        d = np.array(nse_d_hot)
        print(f"  terminal T9≥5 vs NSE: median {np.median(d):.2f} dex "
              f"[p10 {np.quantile(d, .1):.2f}, p90 {np.quantile(d, .9):.2f}] "
              f"(displaced attractor EXPECTED on stock — RESULTS 2026-07-11; "
              f"frac ≤ 0.05 dex: {(d <= 0.05).mean():.3f})")
    if nse_d_frozen_cold:
        d = np.array(nse_d_frozen_cold)
        print(f"  FLAG — frozen at T9<3.3, terminal vs NSE: "
              f"median {np.median(d):.2f} dex over {d.size} runs")


def early_match(net: str) -> None:
    from gnn_nucleo.data.trajectories import load_trajectory, stall_row

    fracs, worst = [], []
    n_pairs = 0
    for spec, traj in load_done_runs(net):
        if spec["family"] != "shipped":
            continue
        shipped = load_trajectory(net, spec["comp_source"])
        n_pairs += 1
        s_end = shipped.age[stall_row(shipped.X)]
        lo, hi = 1e-8, min(traj.age[-1], s_end)
        m = (shipped.age >= lo) & (shipped.age <= hi)
        ages = shipped.age[m]
        Xs = shipped.X[m]
        # interpolate rerun onto shipped ages (linear in log t per species)
        lg = np.log10(np.maximum(traj.age, 1e-30))
        Xr = np.empty_like(Xs)
        for i in range(traj.X.shape[1]):
            Xr[:, i] = np.interp(np.log10(ages), lg, traj.X[:, i])
        tol = np.maximum(0.05 * np.maximum(Xs, Xr), 1e-8)
        okm = np.abs(Xr - Xs) <= tol
        fracs.append(float(okm.mean()))
        worst.append(float(np.abs(Xr - Xs).max()))
    if not fracs:
        print(f"== {net} early-time match: no shipped-family runs done yet ==")
        return
    f = np.array(fracs)
    print(f"== {net} early-time match vs shipped ({n_pairs} pairs, "
          f"band max(5%, 1e-8)) ==")
    print(f"  per-pair species-age agreement: median {np.median(f):.4f} "
          f"[min {f.min():.4f}]  worst |ΔX| median {np.median(worst):.2e}")


def rqse_plateau(net: str) -> None:
    from gnn_nucleo.data.trajectories import select_rows
    from gnn_nucleo.graph import load_isotope_table
    from gnn_nucleo.qse import build_inputs, load_group_mask, r_qse, solve_nse, solve_qse

    table = load_isotope_table(net)
    A = table.A.astype(float)
    Z = table.Z.astype(float)
    inputs = build_inputs(net)
    group = load_group_mask(net)
    in_std, out_spread = [], []
    plateau = checked = 0
    for spec, traj in load_done_runs(net):
        if not 3.3 <= spec["t9"] < 5.0:
            continue
        rows = select_rows(traj)[1:]
        if rows.size < 6:
            continue
        # late relaxed rows: last decade of the pre-stall range
        late = rows[traj.age[rows] >= traj.age[rows[-1]] / 10.0]
        pick = np.unique(np.geomspace(max(late[0], 1), late[-1], 6).astype(int))
        for k in pick:
            Y = traj.X[k] / A
            ye = float((Z * Y).sum() / (A * Y).sum())
            nse = solve_nse(inputs, spec["t9"] * 1e9, 10.0 ** spec["logRho"], ye)
            if not nse.converged:
                continue
            gm = float(traj.X[k][group].sum())
            if not 1e-8 < gm < 1.0 - 1e-8:
                continue
            qse = solve_qse(
                inputs, spec["t9"] * 1e9, 10.0 ** spec["logRho"], ye, group, gm
            )
            if not qse.converged:
                continue
            checked += 1
            rq = r_qse(Y, qse.X / A)
            present = traj.X[k] > 1e-8
            g_in = group & present
            g_out = (~group) & present & (Z > 2)
            if g_in.sum() >= 5 and g_out.sum() >= 3:
                s_in = float(np.std(rq[g_in]))
                in_std.append(s_in)
                out_spread.append(float(np.std(rq[g_out])))
                if s_in < 0.1:
                    plateau += 1
    print(f"== {net} r_QSE plateau on clean relaxed rows (QSE window, late "
          f"pre-stall; {checked} rows) ==")
    if in_std:
        print(f"  intra-group std: median {np.median(in_std):.4f} dex "
              f"(plateau <0.1: {plateau}/{len(in_std)})  "
              f"non-group spread median {np.median(out_spread):.4f} dex")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--net", required=True, choices=["mesa_80", "mesa_151"])
    args = ap.parse_args()
    warnings.simplefilter("ignore")
    stall_and_terminal(args.net)
    early_match(args.net)
    rqse_plateau(args.net)


if __name__ == "__main__":
    main()
