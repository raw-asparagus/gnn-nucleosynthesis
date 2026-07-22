#!/usr/bin/env python
"""Phase-0 QSE-cancellation kill-test driver (Step 6, Task 2).

Measures, never concludes — pass/fail thresholds live in
docs/phase0-checklist.md and docs/phase0-killtest-verdict.md renders the
verdict. Two distributions:

--training-grid   Task 2A: κ_r distributions per T9 stratum on the training
                  distribution — convention-exact from the UNSCREENED
                  stratified subsample, corpus-scale confirmation from the
                  screened full run (flagged; κ ≈ 1 dwarfs the ~7e-2
                  screened offset there); cond(S_active ≈ full ν).

--relaxed         Task 2B: the verdict distribution — pre-stall shipped
                  trajectory rows (+ --include-reruns: the local bbq rerun
                  campaign) through unscreened flux runs. κ_r & δ_r + their
                  Spearman; Guidry ε sweep {3e-3, 1e-2, 3e-2} (active-set
                  size, cond(S_active), carried fractions); κ-active
                  coverage of dominant-isotope |ΔX| (the CLAUDE.md ≥95%
                  gate) + low-κ spread; top-k |dẎₑ| and inter-group
                  concentration under BOTH group-boundary variants +
                  bridge sets + the ⁴⁵Sc cross-check; timescale-separation
                  distribution; Guidry-mask churn per output step per ε.

Usage:
  uv run python scripts/run_killtest.py --net mesa_80 --training-grid
  uv run python scripts/run_killtest.py --net mesa_80 --relaxed --include-reruns
"""

from __future__ import annotations

import argparse
import warnings

import numpy as np

TOP_K = (1, 5, 10, 20)


# --------------------------------------------------------------------------
# Task 2A — training grid
# --------------------------------------------------------------------------

def training_grid(net: str) -> None:
    from gnn_nucleo.fluxes.store import FluxStore
    from gnn_nucleo.graph import npz_path
    from gnn_nucleo.killtest.distributions import kappa_summary
    from gnn_nucleo.killtest.strata import T9_EDGES

    print(f"== {net} TRAINING GRID (Task 2A) ==")
    print("-- κ per stratum, UNSCREENED stratified subsample "
          "(carrying strong pairs) --")
    for r in kappa_summary(FluxStore(net, "subsample-unscreened")):
        print(
            f"  T9 {r['stratum']:<11} states {r['n_states']:>6} "
            f"med log10κ {r['log10_kappa_median']:+6.2f}  "
            f"frac κ>0.1 {r['frac_gt_0p1']:.3f}  frac κ<1e-3 {r['frac_lt_1em3']:.3f}  "
            f"active-frac med {r['active_fraction_median']:.3f}"
        )
    print("-- corpus-scale confirmation, FULL run (label screening — "
          "κ ≈ 1 dwarfs the ~7e-2 offset; thresholds still read from the "
          "unscreened rows above) --")
    for r in kappa_summary(FluxStore(net, "full"), allow_screened=True):
        print(
            f"  T9 {r['stratum']:<11} states {r['n_states']:>7} "
            f"med log10κ {r['log10_kappa_median']:+6.2f}  "
            f"frac κ>0.1 {r['frac_gt_0p1']:.3f}  frac κ<1e-3 {r['frac_lt_1em3']:.3f}"
        )

    # cond(S_active): nothing is equilibrated on this distribution — the
    # active set is essentially every net column. cond = rank-revealing
    # (nonzero-singular-value) definition, as in graph/metrics.
    from gnn_nucleo.killtest.active_set import cond_s_active

    with np.load(npz_path(net), allow_pickle=False) as z:
        nu = z["nu"]
    store = FluxStore(net, "subsample-unscreened")
    chunks = list(store.iter_chunks())
    f_plus = np.concatenate([c.f_plus for c in chunks], axis=1)
    kappa = np.concatenate([c.kappa for c in chunks], axis=1)
    T = np.concatenate([c.T for c in chunks])
    c0 = chunks[0]
    net_cols = c0.is_forward_member | (c0.pair_col < 0)
    all_cols = np.ones(nu.shape[1], dtype=bool)
    print("-- cond(S_active), rank-revealing --")
    print(f"  cond(ν full)          = {cond_s_active(nu, all_cols):.1f}")
    print(f"  cond(ν net columns)   = {cond_s_active(nu, net_cols):.1f}")
    t9b = np.digitize(T / 1e9, T9_EDGES) - 1
    for b in range(len(T9_EDGES) - 1):
        m = t9b == b
        if not m.any():
            continue
        active_union = net_cols & (
            ((kappa[:, m] > 0.1) & (f_plus[:, m] > 0)).any(axis=1)
        )
        print(
            f"  T9 bin {b}: union κ-active net cols {int(active_union.sum())}"
            f"/{int(net_cols.sum())}, cond {cond_s_active(nu, active_union):.1f}"
        )


# --------------------------------------------------------------------------
# Task 2B — relaxed manifold
# --------------------------------------------------------------------------

def relaxed(net: str, include_reruns: bool, churn: bool) -> None:
    from scipy.stats import spearmanr

    from gnn_nucleo.graph import load_isotope_table, npz_path
    from gnn_nucleo.killtest.active_set import (
        EPS_SWEEP,
        carried_fractions,
        cond_s_active,
        guidry_masks,
        timescale_separation,
        topk_concentration,
    )
    from gnn_nucleo.killtest.manifold import assemble
    from gnn_nucleo.killtest.strata import T9_LABELS, assign_strata
    from gnn_nucleo.qse import load_group_mask

    table = load_isotope_table(net)
    A = table.A.astype(np.float64)
    with np.load(npz_path(net), allow_pickle=False) as z:
        nu = z["nu"]
        rate_strings = [str(s) for s in z["rate_strings"]]
        rate_fnames = [str(s) for s in z["rate_fnames"]]
        Zrow = z["Z"]
        weak = z["weak_mask"].astype(bool)

    run_ids = ["trajectories-unscreened"]
    if include_reruns:
        run_ids.append("rerun-trajectories-unscreened")
    rows = assemble(net, run_ids, prestall=True, max_rows_per_traj=24)
    print(f"== {net} RELAXED MANIFOLD (Task 2B) — {rows.n_rows} rows from "
          f"{len(set(rows.traj_key))} trajectories ({run_ids}) ==")
    if rows.n_rows == 0:
        return
    t9b, yeb = assign_strata(rows.T, rows.ye)
    from gnn_nucleo.fluxes.store import FluxStore

    c0 = next(iter(FluxStore(net, run_ids[0]).iter_chunks()))
    net_cols = c0.is_forward_member | (c0.pair_col < 0)
    strong_fwd = c0.is_forward_member & (c0.pair_col >= 0)
    ok = rows.nse_converged

    # ---- 1. κ & δ distributions + correlation --------------------------
    logk, logd, kbin = [], [], []
    for r in np.nonzero(ok)[0]:
        f = rows.f_plus[:, r]
        sel = strong_fwd & (f > 0) & np.isfinite(rows.delta_r[:, r])
        pos = f[sel & (f > 0)]
        if pos.size == 0:
            continue
        m = sel & (f > np.median(pos))
        logk.extend(np.log10(np.maximum(rows.kappa[m, r], 1e-16)))
        logd.extend(np.log10(np.maximum(rows.delta_r[m, r], 1e-16)))
        kbin.extend([t9b[r]] * int(m.sum()))
    logk, logd, kbin = np.array(logk), np.array(logd), np.array(kbin)
    rho_s, p = spearmanr(logk, logd)
    print(f"-- κ↔δ (carrying strong pairs, {len(logk)} samples): "
          f"Spearman {rho_s:+.3f} (p={p:.1e}) --")
    eqd = logd < -2
    if eqd.any():
        print(f"  κ where δ_r<0.01: median 10^{np.median(logk[eqd]):.2f} "
              f"(n={int(eqd.sum())})  vs δ_r≥0.01: 10^{np.median(logk[~eqd]):.2f}")
    for b, lab in enumerate(T9_LABELS):
        m = kbin == b
        if m.sum() < 50:
            continue
        print(f"  T9 {lab:<11} n {int(m.sum()):>7}  med log10κ "
              f"{np.median(logk[m]):+6.2f}  frac κ>0.1 {np.mean(logk[m] > -1):.3f}"
              f"  frac κ<1e-3 {np.mean(logk[m] < -3):.3f}")

    # ---- 2. ε sweep: active-set size, cond, coverage --------------------
    dom_thresh = 1e-3
    print("-- Guidry ε sweep (weak structurally never maskable) --")
    for eps in EPS_SWEEP:
        n_mask, conds, cov_min, cov_med = [], [], [], []
        union_active = np.zeros(nu.shape[1], dtype=bool)
        for r in np.nonzero(ok)[0]:
            maskable = guidry_masks(rows.delta_r[:, r], weak, (eps,))[eps]
            active = ~maskable
            n_mask.append(int(maskable.sum()))
            act_net = active & net_cols
            union_active |= act_net
            conds.append(cond_s_active(nu, act_net))
            dom = rows.X[r] > dom_thresh
            cov = carried_fractions(
                nu[:, net_cols], rows.phi[net_cols, r], act_net[net_cols]
            )[dom]
            cov = cov[np.isfinite(cov)]
            if cov.size:
                cov_min.append(float(cov.min()))
                cov_med.append(float(np.median(cov)))
        print(
            f"  ε={eps:g}: maskable/row median {np.median(n_mask):.0f} "
            f"(p90 {np.quantile(n_mask, .9):.0f}) of {nu.shape[1]}; "
            f"cond(S_active) median {np.nanmedian(conds):.1f} "
            f"p99 {np.nanquantile(conds, .99):.1f}, union {cond_s_active(nu, union_active):.1f}; "
            f"dominant-X coverage by Guidry-active: median-of-min {np.median(cov_min):.4f}, "
            f"median {np.median(cov_med):.4f}"
        )

    # ---- κ-active coverage (the CLAUDE.md primary gate), split by ------
    # relaxation phase: RELAXING (before first-quiet arrival) vs ATTRACTOR
    # (the weak-drift tail — Target A's hybrid operating regime)
    print("-- κ-active {κ>0.1} coverage of dominant-isotope |ΔX| turnover "
          "(per stratum × phase: median over rows of min/median over "
          "dominant isotopes) --")
    for phase, pmask in (("relaxing", ~rows.attractor), ("attractor", rows.attractor)):
        for b, lab in enumerate(T9_LABELS):
            sel_rows = np.nonzero((t9b == b) & pmask)[0]
            if sel_rows.size == 0:
                continue
            mins, meds, spread, kbal = [], [], [], []
            for r in sel_rows:
                act = (rows.kappa[:, r] > 0.1) & net_cols
                dom = rows.X[r] > dom_thresh
                cov = carried_fractions(
                    nu[:, net_cols], rows.phi[net_cols, r], act[net_cols]
                )[dom]
                cov = cov[np.isfinite(cov)]
                if cov.size == 0:
                    continue
                mins.append(float(cov.min()))
                meds.append(float(np.median(cov)))
                contrib = np.abs(rows.phi[net_cols, r])
                low = ~act[net_cols]
                spread.append(
                    float((contrib[low] > 0).sum() / max((contrib > 0).sum(), 1))
                )
                sf = strong_fwd & (rows.f_plus[:, r] > 0)
                kbal.append(
                    float((rows.kappa[sf, r] < 1e-3).sum() / max(sf.sum(), 1))
                )
            if not mins:
                continue
            print(
                f"  [{phase:<9}] T9 {lab:<11} rows {len(mins):>5}  "
                f"min-cov median {np.median(mins):.4f} p10 {np.quantile(mins, .1):.4f}  "
                f"med-cov median {np.median(meds):.4f}  "
                f"low-κ col share {np.median(spread):.3f}  "
                f"κ-balanced pair frac {np.median(kbal):.3f}"
            )
    # dYe: weak columns are unpaired (f⁻ ≡ 0) ⇒ κ = 1 wherever f⁺ > 0 —
    # verify on the assembled rows, then the coverage is 1 by arithmetic
    wk = weak[:, None] & (rows.f_plus > 0)
    assert np.all(rows.kappa[wk] == 1.0), "weak κ convention violated"
    print(f"  |dẎₑ| coverage by the κ-active set: 1.0000 — verified κ = 1.0 "
          f"exactly on {int(wk.sum())} (weak column × row) samples with "
          "f⁺ > 0 (weak also never maskable; invariant #2)")

    # ---- 3. top-k concentration -----------------------------------------
    zeta = Zrow @ nu
    print("-- top-k |dẎₑ| concentration (weak channels), high-Yₑ QSE-window "
          "rows --")
    hi = (yeb == 2) & ((t9b == 2) | (t9b == 3))
    if hi.any():
        contrib = np.abs(zeta[weak, None] * rows.f_plus[weak][:, hi]).sum(axis=1)
        tk = topk_concentration(contrib, TOP_K)
        print("   " + "  ".join(f"top-{k}: {v:.3f}" for k, v in tk.items()))
        order = np.argsort(-contrib)
        wcols = np.nonzero(weak)[0]
        for j in order[:3]:
            print(f"    {rate_strings[wcols[j]]:<44} share "
                  f"{contrib[j] / contrib.sum():.4f}")
    for variant in ("default", "a24_46"):
        g = load_group_mask(net, variant)
        ag = (A * g) @ nu
        cross = (np.abs(ag) > 0) & net_cols
        xc = np.nonzero(cross)[0]
        if not hi.any():
            continue
        share = np.abs(ag[xc, None] * rows.phi[xc][:, hi]).sum(axis=1)
        tk = topk_concentration(share, TOP_K)
        print(f"-- inter-group flow [{variant}] high-Yₑ QSE rows: "
              + "  ".join(f"top-{k}: {v:.3f}" for k, v in tk.items()))
        order = np.argsort(-share)
        for r_ in order[:5]:
            print(f"    {rate_strings[xc[r_]]:<44} share {share[r_] / share.sum():.4f}")
        if net == "mesa_151" and variant == "a24_46":
            sc = [j for j, s in enumerate(rate_fnames)
                  if "Sc45" in s and "Ti46" in s and s.startswith("p_")]
            for j in sc:
                hit = np.nonzero(xc[order] == j)[0]
                if hit.size:
                    rank = int(hit[0]) + 1
                    print(f"    ⁴⁵Sc(p,γ)⁴⁶Ti rank {rank}/{len(xc)} "
                          f"(share {share[order][rank - 1] / share.sum():.4f})")

    # ---- 4. timescale separation ----------------------------------------
    # Two equilibrated-set definitions: Guidry maskable(ε=1e-2) — empty
    # wherever δ_r is referenced to TRUE NSE but the label manifold sits at
    # the displaced attractor (RESULTS 2026-07-11) — and κ-balance
    # (strong pairs with κ < 1e-3), which detects pair equilibrium directly
    # from the fluxes on the label manifold.
    print("-- timescale separation: fastest equilibrated gross rate / "
          "slowest 95%-inter-group-bottleneck net rate --")
    gdef = load_group_mask(net)
    ag = (table.A.astype(float) * gdef) @ nu
    cross = (np.abs(ag) > 0) & net_cols
    ratios_g = {b: [] for b in range(len(T9_LABELS))}
    ratios_k = {b: [] for b in range(len(T9_LABELS))}
    for r in np.nonzero(ok)[0]:
        maskable = guidry_masks(rows.delta_r[:, r], weak, (1e-2,))[1e-2]
        kappa_eq = strong_fwd & (rows.kappa[:, r] < 1e-3) & (rows.f_plus[:, r] > 0)
        flow = np.abs(ag * rows.phi[:, r]) * cross
        order = np.argsort(-flow)
        cum = np.cumsum(flow[order])
        if cum[-1] <= 0:
            continue
        n95 = int(np.searchsorted(cum / cum[-1], 0.95)) + 1
        bottleneck = np.zeros_like(cross)
        bottleneck[order[:n95]] = True
        for eq, ratios in ((maskable, ratios_g), (kappa_eq, ratios_k)):
            ratio = timescale_separation(
                rows.f_plus[:, r], rows.phi[:, r], eq, bottleneck
            )
            if np.isfinite(ratio) and t9b[r] >= 0:
                ratios[t9b[r]].append(np.log10(ratio))
    for tag, ratios in (("Guidry ε=1e-2", ratios_g), ("κ<1e-3 pairs", ratios_k)):
        for b, lab in enumerate(T9_LABELS):
            v = np.array(ratios[b])
            if v.size < 5:
                continue
            print(f"  [{tag}] T9 {lab:<11} n {v.size:>5}  log10 ratio median "
                  f"{np.median(v):+5.2f}  [p10 {np.quantile(v, .1):+5.2f}, "
                  f"p90 {np.quantile(v, .9):+5.2f}]")

    # ---- 5. mask churn ----------------------------------------------------
    if churn:
        churn_report(net, run_ids, nu, weak)


def churn_report(net: str, run_ids: list[str], nu: np.ndarray, weak: np.ndarray) -> None:
    """Guidry-mask membership flips per OUTPUT STEP along each trajectory."""
    from gnn_nucleo.data.trajectories import select_rows
    from gnn_nucleo.fluxes.store import FluxStore
    from gnn_nucleo.graph import load_isotope_table
    from gnn_nucleo.killtest.active_set import EPS_SWEEP, mask_churn
    from gnn_nucleo.killtest.manifold import _traj_for_chunk
    from gnn_nucleo.qse import build_inputs, delta_species, solve_nse_batch
    from gnn_nucleo.qse.diagnostics import eligible_mask, reaction_delta_batch

    table = load_isotope_table(net)
    A = table.A.astype(np.float64)
    inputs = build_inputs(net)
    out = {e: [] for e in EPS_SWEEP}
    n_traj = 0
    for run_id in run_ids:
        for chunk in FluxStore(net, run_id).iter_chunks():
            t9 = 10.0 ** float(chunk.attrs["logT"]) / 1e9
            if not 3.3 <= t9 < 5.0:
                continue  # churn measured in the QSE window (mask regime)
            traj = _traj_for_chunk(net, chunk.attrs)
            rows = select_rows(traj, prestall=True)[1:]
            if rows.size < 10:
                continue
            rho = 10.0 ** float(chunk.attrs["logRho"])
            # NSE reference per row, deduplicated on rounded Yₑ (t9/ρ constant
            # within the chunk) and solved in one batched Newton pass.
            Yr = traj.X[rows] / A  # (rows, n_species)
            ye = np.round(
                (table.Z @ Yr.T) / (A @ Yr.T), 4
            )  # (rows,) rounded key = solved Yₑ
            uye, inv = np.unique(ye, return_inverse=True)
            res = solve_nse_batch(
                inputs,
                np.full(uye.size, t9 * 1e9),
                np.full(uye.size, rho),
                uye,
            )
            good = res.converged[inv]
            deltas = np.where(
                good[:, None], delta_species(Yr, res.X[inv] / A), np.inf
            )
            if good.sum() < 10:
                continue
            d_r = reaction_delta_batch(nu, deltas[good])
            n_traj += 1
            for eps in EPS_SWEEP:
                masks = np.stack([eligible_mask(d, weak, eps) for d in d_r])
                out[eps].append(mask_churn(masks))
    print(f"-- Guidry-mask churn per output step (QSE-window trajectories, "
          f"n={n_traj}) --")
    for eps in EPS_SWEEP:
        if not out[eps]:
            continue
        fl = np.array([c["flips_per_step"] for c in out[eps]])
        fr = np.array([c["churn_fraction"] for c in out[eps]])
        print(f"  ε={eps:g}: flips/step median {np.median(fl):.2f} "
              f"(p90 {np.quantile(fl, .9):.2f}); churn fraction median "
              f"{100 * np.median(fr):.3f}%/step")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--net", required=True, choices=["mesa_80", "mesa_151"])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--training-grid", action="store_true")
    mode.add_argument("--relaxed", action="store_true")
    ap.add_argument("--include-reruns", action="store_true")
    ap.add_argument("--no-churn", action="store_true")
    args = ap.parse_args()
    warnings.simplefilter("ignore")
    if args.training_grid:
        training_grid(args.net)
    else:
        relaxed(args.net, args.include_reruns, not args.no_churn)


if __name__ == "__main__":
    main()
