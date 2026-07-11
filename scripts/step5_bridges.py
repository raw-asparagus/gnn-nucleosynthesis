#!/usr/bin/env python
"""Step-5 Task 4: per-isotope decomposition + preliminary bridge discovery.

Over the persisted stratified subsample (label screening config for the
rankings; unscreened run for the κ distribution):

1. per-isotope cancellation cᵢ = |Σⱼ νᵢⱼφⱼ| / Σⱼ |νᵢⱼφⱼ| distributions by T9;
2. κ_r distribution shape by T9 stratum (UNSCREENED — DB diagnostic;
   the screened config carries the documented screening-asymmetry offset);
3. dẎₑ = Σ_{j∈weak} ζⱼRⱼ (ζⱼ = ΣᵢZᵢνᵢⱼ) per-reaction breakdown: per-stratum
   top-k share-of-|dẎₑ| concentration (k = 1, 5, 10, 20);
4. inter-group net baryon flow through the Si-group boundary
   (Σ_{i∈G} Aᵢνᵢⱼ·φⱼ over net columns): per-stratum top-k concentration;
   mesa_151: rank of ⁴⁵Sc(p,γ)⁴⁶Ti at high Yₑ; mesa_80: empirical bridge set.

All PRELIMINARY (subsample-level; Step 6 finalizes on fuller coverage).

Usage: uv run python scripts/step5_bridges.py --net mesa_80
"""

from __future__ import annotations

import argparse

import numpy as np

T9_EDGES_LOCAL = [1.6, 2.5, 3.3, 4.0, 5.0, 6.3, 7.95]
T9_LABELS = ["[1.6,2.5)", "[2.5,3.3)", "[3.3,4.0)", "[4.0,5.0)", "[5.0,6.3)", "[6.3,7.95)"]
YE_EDGES_LOCAL = [0.45, 0.4667, 0.4833, 0.5001]
YE_LABELS = ["[.45,.467)", "[.467,.483)", "[.483,.5]"]
TOP_K = (1, 5, 10, 20)


def _load_run(net: str, run_id: str):
    from gnn_nucleo.fluxes.store import FluxStore

    store = FluxStore(net, run_id)
    chunks = list(store.iter_chunks())
    f_plus = np.concatenate([c.f_plus for c in chunks], axis=1)
    ydot = np.concatenate([c.ydot for c in chunks], axis=1)
    T = np.concatenate([c.T for c in chunks])
    ye = np.concatenate([c.ye for c in chunks])
    c0 = chunks[0]
    return f_plus, ydot, T, ye, c0.pair_col, c0.is_forward_member, c0.weak_mask


def trajectory_bridges(net: str) -> None:
    """Inter-group concentration on PRE-STALL trajectory rows in the QSE
    window — the relaxed-state view the random subsample cannot give."""
    from gnn_nucleo.data.trajectories import load_trajectory, select_rows
    from gnn_nucleo.fluxes.store import FluxStore
    from gnn_nucleo.graph import npz_path
    from gnn_nucleo.qse import load_group_mask

    with np.load(npz_path(net), allow_pickle=False) as z:
        nu = z["nu"]
        rate_fnames = [str(s) for s in z["rate_fnames"]]
        rate_strings = [str(s) for s in z["rate_strings"]]
        Arow = z["A"]

    store = FluxStore(net, "trajectories")
    phi_rows = []
    ye_rows = []
    pair_col = is_fwd = None
    for chunk in store.iter_chunks():
        t9 = 10.0 ** chunk.attrs["logT"] / 1e9
        if not 3.3 <= t9 < 5.0:
            continue
        pair_col, is_fwd = chunk.pair_col, chunk.is_forward_member
        traj = load_trajectory(net, chunk.attrs["trajectory_file"])
        # pre-stall rows only (guard in data.trajectories); drop the initial row
        sel = select_rows(traj)[1:]
        phi_rows.append(chunk.phi[:, sel])
        ye_rows.append(chunk.ye[sel])
    print(f"\n== {net} inter-group concentration on PRE-STALL trajectory rows "
          "(T9 ∈ [3.3, 5.0)) ==")
    if not phi_rows:
        print("  no trajectories in the window")
        return
    phi = np.concatenate(phi_rows, axis=1)
    ye = np.concatenate(ye_rows)
    net_cols = is_fwd | (pair_col < 0)
    for variant in ("default", "a24_46"):
        g = load_group_mask(net, variant)
        ag = (Arow * g) @ nu
        cross = (np.abs(ag) > 0) & net_cols
        xc = np.nonzero(cross)[0]
        m = ye >= 0.483
        if not m.any():
            print(f"  [{variant}] no high-Ye rows")
            continue
        share = np.abs(ag[xc, None] * phi[xc][:, m]).sum(axis=1)
        order = np.argsort(-share)
        cum = np.cumsum(share[order]) / share.sum()
        tops = "  ".join(f"top-{k}: {cum[min(k, len(cum)) - 1]:.3f}" for k in TOP_K)
        print(f"  [{variant}] high-Yₑ rows {int(m.sum())}: {tops}")
        for r in order[:5]:
            print(f"      {rate_strings[xc[r]]:<42} share {share[r] / share.sum():.4f}")
        if net == "mesa_151":
            sc = [
                j for j, s in enumerate(rate_fnames)
                if "Sc45" in s and "Ti46" in s and s.startswith("p_")
            ]
            for j in sc:
                hit = np.nonzero(xc[order] == j)[0]
                if hit.size:
                    rank = int(hit[0]) + 1
                    print(
                        f"      45Sc(p,γ)46Ti rank {rank}/{len(xc)} "
                        f"(share {share[order][rank - 1] / share.sum():.4f})"
                    )
                else:
                    print(f"      45Sc(p,γ)46Ti not boundary-crossing [{variant}]")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--net", required=True, choices=["mesa_80", "mesa_151"])
    ap.add_argument("--trajectories", action="store_true",
                    help="also run the pre-stall trajectory-row analysis")
    args = ap.parse_args()
    net = args.net

    from gnn_nucleo.graph import load_isotope_table, npz_path
    from gnn_nucleo.qse import load_group_mask

    with np.load(npz_path(net), allow_pickle=False) as z:
        nu = z["nu"]
        rate_fnames = [str(s) for s in z["rate_fnames"]]
        rate_strings = [str(s) for s in z["rate_strings"]]
        Zrow = z["Z"]
        Arow = z["A"]
    table = load_isotope_table(net)

    f_plus, ydot, T, ye, pair_col, is_fwd, weak = _load_run(net, "subsample")
    t9 = T / 1e9
    t9_bin = np.digitize(t9, T9_EDGES_LOCAL) - 1
    ye_bin = np.digitize(ye, YE_EDGES_LOCAL) - 1

    # φ per column (pair-netted; weak φ = R), net view via forward|unpaired
    f_minus = np.zeros_like(f_plus)
    paired = pair_col >= 0
    f_minus[paired] = f_plus[pair_col[paired]]
    phi = f_plus - f_minus
    net_cols = is_fwd | (pair_col < 0)

    # ---- 1. per-isotope cancellation by T9 stratum -------------------------
    gross = np.abs(nu) @ f_plus  # (n_species, n_states)
    with np.errstate(divide="ignore", invalid="ignore"):
        c_iso = np.abs(ydot) / np.maximum(gross, 1e-300)
    print(f"== {net} per-isotope cancellation c_i (states × species, X-agnostic) ==")
    for b, lab in enumerate(T9_LABELS):
        m = t9_bin == b
        if not m.any():
            continue
        cc = c_iso[:, m][gross[:, m] > 0]
        print(
            f"  T9 {lab:<11} median {np.median(cc):.3e}  p10 {np.quantile(cc, .1):.3e}"
            f"  frac c<1e-2 {np.mean(cc < 1e-2):.3f}  frac c<1e-4 {np.mean(cc < 1e-4):.3f}"
        )

    # ---- 2. κ_r distribution by T9 (unscreened run) ------------------------
    fu, _, Tu, _, pc_u, fwd_u, _ = _load_run(net, "subsample-unscreened")
    fmu = np.zeros_like(fu)
    pu = pc_u >= 0
    fmu[pu] = fu[pc_u[pu]]
    with np.errstate(divide="ignore", invalid="ignore"):
        ku = np.abs(fu - fmu) / np.maximum(fu + fmu, 1e-300)
    strong_fwd = fwd_u & pu
    t9u = Tu / 1e9
    t9u_bin = np.digitize(t9u, T9_EDGES_LOCAL) - 1
    print(f"\n== {net} κ_r distribution (UNSCREENED, carrying strong pairs) ==")
    for b, lab in enumerate(T9_LABELS):
        m = t9u_bin == b
        if not m.any():
            continue
        f_sub = fu[strong_fwd][:, m]
        k_sub = ku[strong_fwd][:, m]
        carrying = f_sub > np.median(f_sub[f_sub > 0])
        k_c = k_sub[carrying]
        print(
            f"  T9 {lab:<11} median {np.median(k_c):.3e}  p10 {np.quantile(k_c, .1):.3e}"
            f"  frac κ>0.1 {np.mean(k_c > 0.1):.3f}  frac κ<1e-3 {np.mean(k_c < 1e-3):.3f}"
        )

    # ---- 3. dYe per-reaction concentration ---------------------------------
    zeta = Zrow @ nu  # (n_rxn,)
    wcols = np.nonzero(weak)[0]
    contrib = np.abs(zeta[wcols, None] * f_plus[wcols])  # (n_weak, n_states)
    print(f"\n== {net} |dYe| per-reaction concentration (weak channels) ==")
    for b, lab in enumerate(T9_LABELS):
        m = t9_bin == b
        if not m.any():
            continue
        share = contrib[:, m].sum(axis=1)
        tot = share.sum()
        order = np.argsort(-share)
        cum = np.cumsum(share[order]) / tot
        tops = "  ".join(f"top-{k}: {cum[min(k, len(cum)) - 1]:.3f}" for k in TOP_K)
        top1 = rate_fnames[wcols[order[0]]]
        print(f"  T9 {lab:<11} {tops}  | #1: {top1}")

    # ---- 4. inter-group flow through the Si-group boundary -----------------
    group = load_group_mask(net)
    ag = (Arow * group) @ nu  # baryons into G per unit flux, per column
    cross = (np.abs(ag) > 0) & net_cols
    xcols = np.nonzero(cross)[0]
    flow = np.abs(ag[xcols, None] * phi[xcols])
    print(f"\n== {net} inter-group (Si-group boundary) net-flow concentration ==")
    print(f"  boundary-crossing net columns: {len(xcols)}")
    for b, lab in enumerate(T9_LABELS):
        m = t9_bin == b
        if not m.any():
            continue
        share = flow[:, m].sum(axis=1)
        tot = share.sum()
        order = np.argsort(-share)
        cum = np.cumsum(share[order]) / tot
        tops = "  ".join(f"top-{k}: {cum[min(k, len(cum)) - 1]:.3f}" for k in TOP_K)
        print(f"  T9 {lab:<11} {tops}")
        for r in order[:5]:
            print(f"      {rate_strings[xcols[r]]:<42} share {share[r] / tot:.3f}")

    # ---- literature cross-check: sc45(p,g)ti46 -----------------------------
    if net == "mesa_151":
        sc_cols = [
            j
            for j, s in enumerate(rate_fnames)
            if "Sc45" in s and "Ti46" in s and s.startswith("p_")
        ]
        print("\n== mesa_151 ⁴⁵Sc(p,γ)⁴⁶Ti literature cross-check ==")
        if not sc_cols:
            print("  COLUMN NOT FOUND — check fname convention")
        # the bridge is a boundary crossing only when the Si group includes
        # the A=45 edge — use the a24_46 variant (default 24≤A<45 places sc45
        # outside G, so the channel is group-external there)
        g46 = load_group_mask(net, "a24_46")
        ag46 = (Arow * g46) @ nu
        cross46 = (np.abs(ag46) > 0) & net_cols
        xcols46 = np.nonzero(cross46)[0]
        flow46 = np.abs(ag46[xcols46, None] * phi[xcols46])
        m = (ye_bin == 2) & ((t9_bin == 2) | (t9_bin == 3))
        share46 = flow46[:, m].sum(axis=1)
        order46 = np.argsort(-share46)
        for j in sc_cols:
            in_def = bool(np.isin(j, xcols))
            in_46 = np.nonzero(xcols46 == j)[0]
            print(
                f"  column {j} ({rate_fnames[j]}): crossing under default "
                f"(24≤A<45) = {in_def}; under a24_46 = {len(in_46) > 0}"
            )
            if len(in_46):
                rank = int(np.nonzero(xcols46[order46] == j)[0][0]) + 1
                print(
                    f"  rank among a24_46 inter-group carriers at "
                    f"Yₑ∈[.483,.5], T9∈[3.3,5.0): {rank}/{len(xcols46)} "
                    f"(share {share46[order46][rank - 1] / share46.sum():.4f})"
                )
        print("  top-5 a24_46 boundary carriers at high Yₑ, QSE-window T9:")
        for r in order46[:5]:
            print(
                f"    {rate_strings[xcols46[r]]:<42} share {share46[r] / share46.sum():.4f}"
            )
    else:
        names = list(table.names)
        assert "sc45" not in names, "sc45 unexpectedly present in mesa_80"
        print("\n== mesa_80: ⁴⁵Sc absent (only sc43) — bridge set is empirical ==")
        m = (ye_bin == 2) & ((t9_bin == 2) | (t9_bin == 3))
        share = flow[:, m].sum(axis=1)
        order = np.argsort(-share)
        print("  top-10 inter-group carriers at high Yₑ, QSE-window T9:")
        for r in order[:10]:
            print(
                f"    {rate_strings[xcols[r]]:<42} share {share[r] / share.sum():.4f}"
            )

    if args.trajectories:
        trajectory_bridges(net)


if __name__ == "__main__":
    main()
