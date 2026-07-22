#!/usr/bin/env python
"""Step-6 Task 3: integrated-flux label prototype — end-to-end measurement.

Per sampled Sobol state, ONE stiff integration (fluxes/integrate.py) to
dt = 1e2 s with t_eval at ALL NINE measured label dts serves every label:

1. label agreement: fraction of species within the handshake net band
   |ΔX_pred − ΔX_lab| ≤ max(0.1·|ΔX_lab|, 3ε(Xᵢ+X_f), 2e-15), ε = 1e-7
   (float32 label precision), per T9 stratum × dt.
   INTERPRETATION CAVEAT (RESULTS.md 2026-07-11): at T9 ≳ 5 the shipped
   labels carry the Appendix-B displaced pseudo-equilibrium while this
   integrator carries pf-true rates — disagreement there is the LABEL
   pathology, not integrator error (solver-independence verified BDF vs
   Radau vs rtol 1e-10 to 5e-8 rel).
2. energy identity (CLAUDE.md invariant #5): ΣⱼQⱼΦⱼ vs mass-excess
   bookkeeping −Σᵢmᵢ ΔYᵢ, residual ≤ 1% gate, reported per T9 stratum
   (the 3–4 GK band is the gate's scope).
3. throughput: wall s/state for the full nine-dt integration → states/hour/
   core and corpus-scale extrapolation (1,041,400 states/net) — the number
   that decides shipped-ΔX-only vs shipped-ΔX + local-Φ supervision.

Usage: uv run python scripts/step6_integrate_check.py --net mesa_80 [--n 36]
"""

from __future__ import annotations

# Single-thread the BLAS/OpenMP pools BEFORE numpy is imported. This script fans
# out over states with a fork-based ProcessPoolExecutor; each worker runs one
# scipy BDF solve at a time (single-threaded NumPy/sparse), so letting every
# worker's OpenBLAS spawn its own thread pool oversubscribes the cores. A fork
# inherits the parent's already-initialized pool, so setting these in the worker
# initializer is too late — they must precede `import numpy`. setdefault lets an
# explicit outer environment override win.
import os

for _v in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ.setdefault(_v, "1")

import argparse
import time
import warnings

import numpy as np

T9_EDGES = [1.6, 2.5, 3.3, 4.0, 5.0, 6.3, 7.95]
T9_LABELS = ["[1.6,2.5)", "[2.5,3.3)", "[3.3,4.0)", "[4.0,5.0)", "[5.0,6.3)", "[6.3,7.95)"]
EPS_LAB = 1e-7  # float32 label precision class (schema.py; Step-5 calibration)


def pick_states(net: str, n: int) -> np.ndarray:
    """~n subsample states, evenly spread over T9 strata (state_ids)."""
    from gnn_nucleo.data.labels import load_step_frame
    from gnn_nucleo.data.subsample import load_subsample_ids

    ids = load_subsample_ids(net)
    df = load_step_frame(net, "1e-6", columns=["logT"], state_ids=ids)
    t9 = 10.0 ** df["logT"].to_numpy() / 1e9
    per = max(1, n // (len(T9_EDGES) - 1))
    rng = np.random.default_rng(20260711)
    picked = []
    for lo, hi in zip(T9_EDGES[:-1], T9_EDGES[1:]):
        pool = np.nonzero((t9 >= lo) & (t9 < hi))[0]
        picked.append(rng.choice(pool, size=min(per, len(pool)), replace=False))
    return np.sort(ids[np.concatenate(picked)])


_G: dict = {}


def _worker_init(net: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        from gnn_nucleo.fluxes.compile import compile_network

        _G["cn"] = compile_network(net)


def _measure_state(args) -> tuple[int, float, int, bool, np.ndarray, np.ndarray]:
    s, T, rho, Xi, dts = args
    import warnings as w

    w.simplefilter("ignore")
    from gnn_nucleo.fluxes.integrate import integrate_state

    cn = _G["cn"]
    A = cn.stoich.A.astype(np.float64)
    t0 = time.perf_counter()
    res = integrate_state(cn, T, rho, Xi / A, dts[-1], t_eval=dts)
    wall = time.perf_counter() - t0
    if not res.success:
        n = len(dts)
        return s, wall, res.nfev, False, np.full((n, len(Xi)), np.nan), np.full(
            (n, cn.n_reactions), np.nan
        )
    return s, wall, res.nfev, True, res.Y, res.Phi


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--net", required=True, choices=["mesa_80", "mesa_151"])
    ap.add_argument("--n", type=int, default=36)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--deadline", type=float, default=5400.0,
                    help="global wall cap [s]; unfinished states are "
                    "reported as censored (>= their elapsed wall)")
    args = ap.parse_args()
    net = args.net
    warnings.simplefilter("ignore")

    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor

    from gnn_nucleo.data.labels import load_step_frame
    from gnn_nucleo.data.schema import DT_LABELS, load_measured_dt
    from gnn_nucleo.graph import load_isotope_table, npz_path

    table = load_isotope_table(net)
    A = table.A.astype(np.float64)
    mass = np.array([nuc.mass for nuc in table.nuclei])
    with np.load(npz_path(net), allow_pickle=False) as z:
        Q = z["Q"]
    dts = np.array(load_measured_dt(net))

    ids = pick_states(net, args.n)
    cols = ["logT", "logRho"] + [f"initial_{x}" for x in table.names]
    df0 = load_step_frame(net, "1e-6", columns=cols, state_ids=ids)
    Xi = df0[[f"initial_{x}" for x in table.names]].to_numpy()
    T = 10.0 ** df0["logT"].to_numpy()
    rho = 10.0 ** df0["logRho"].to_numpy()
    finals = {}
    for lab in DT_LABELS:
        f = load_step_frame(
            net, lab, columns=[f"final_{x}" for x in table.names], state_ids=ids
        )
        finals[lab] = f.to_numpy()
    print(f"{net}: labels loaded for {len(ids)} states; integrating with "
          f"{args.workers} workers", flush=True)

    n_states = len(ids)
    frac = np.full((n_states, len(DT_LABELS)), np.nan)
    e_resid = np.full((n_states, len(DT_LABELS)), np.nan)
    wall = np.full(n_states, np.nan)
    nfev = np.zeros(n_states, dtype=int)
    from concurrent.futures import TimeoutError as FutTimeout
    from concurrent.futures import wait

    jobs = [(s, T[s], rho[s], Xi[s], dts) for s in range(n_states)]
    ctx = mp.get_context("fork")
    censored = np.zeros(n_states, dtype=bool)
    t_start = time.perf_counter()
    ex = ProcessPoolExecutor(
        max_workers=args.workers,
        mp_context=ctx,
        initializer=_worker_init,
        initargs=(net,),
    )
    futs = {ex.submit(_measure_state, j): j[0] for j in jobs}
    pending = set(futs)
    try:
        while pending:
            left = args.deadline - (time.perf_counter() - t_start)
            if left <= 0:
                raise FutTimeout
            done, pending = wait(pending, timeout=min(left, 60.0),
                                 return_when="FIRST_COMPLETED")
            for fut in done:
                s, w_s, nf, ok, Yk, Phik = fut.result()
                wall[s] = w_s
                nfev[s] = nf
                if not ok:
                    print(f"  state {ids[s]}: solver FAILED", flush=True)
                    continue
                for k, lab in enumerate(DT_LABELS):
                    dX_pred = A * (Yk[k] - Xi[s] / A)
                    Xf = finals[lab][s]
                    dX_lab = Xf - Xi[s]
                    tol = np.maximum(
                        0.1 * np.abs(dX_lab), 3 * EPS_LAB * (Xi[s] + Xf)
                    )
                    tol = np.maximum(tol, 2e-15)
                    frac[s, k] = float(np.mean(np.abs(dX_pred - dX_lab) <= tol))
                    e_flux = float(Q @ Phik[k])
                    e_comp = -float(mass @ (Yk[k] - Xi[s] / A))
                    if e_comp != 0.0:
                        e_resid[s, k] = abs(e_flux - e_comp) / abs(e_comp)
                print(
                    f"  state {ids[s]:>7} T9 {T[s] / 1e9:5.2f}: "
                    f"wall {wall[s]:6.1f}s nfev {nfev[s]:>6} "
                    f"frac(1e-6) {frac[s, 0]:.3f} frac(1e2) {frac[s, -1]:.3f}",
                    flush=True,
                )
    except FutTimeout:
        for fut in pending:
            censored[futs[fut]] = True
        print(
            f"  DEADLINE {args.deadline:.0f}s: {len(pending)} states censored "
            f"(wall >= {args.deadline - 60:.0f}s each): "
            f"{[int(ids[futs[f]]) for f in pending]}",
            flush=True,
        )
    finally:
        ex.shutdown(wait=False, cancel_futures=True)
    wall[censored] = args.deadline  # lower bound for the throughput stats

    t9 = T / 1e9
    t9_bin = np.digitize(t9, T9_EDGES) - 1
    print(f"\n== {net} integrator-vs-label agreement (fraction of species in "
          "the net band), median over states per stratum ==")
    hdr = "  T9 stratum   " + "  ".join(f"{lab:>6}" for lab in DT_LABELS)
    print(hdr)
    for b, blab in enumerate(T9_LABELS):
        m = t9_bin == b
        if not m.any():
            continue
        row = "  ".join(
            f"{np.nanmedian(frac[m, k]):6.3f}" for k in range(len(DT_LABELS))
        )
        print(f"  {blab:<11}  {row}")
    print("  (T9 ≥ 5 strata measure the LABEL pathology, not integrator error "
          "— RESULTS.md 2026-07-11)")

    print(f"\n== {net} energy identity |ΣQΦ − (−Σm ΔY)| / |e_comp| ==")
    for b, blab in enumerate(T9_LABELS):
        m = t9_bin == b
        if not m.any():
            continue
        r = e_resid[m]
        r = r[np.isfinite(r)]
        if r.size == 0:
            continue
        print(
            f"  T9 {blab:<11} median {np.median(r):.2e}  max {r.max():.2e}  "
            f"frac ≤ 1%: {(r <= 0.01).mean():.3f}"
        )

    ok = np.isfinite(wall)
    per_state = float(np.median(wall[ok]))
    per_hour = 3600.0 / per_state
    corpus_core_h = 1_041_400 * per_state / 3600.0
    print(f"\n== {net} throughput (full nine-dt integration per state) ==")
    print(
        f"  median wall {per_state:.1f} s/state (p90 {np.quantile(wall[ok], .9):.1f}; "
        f"{int(censored.sum())}/{n_states} censored at the deadline — medians are "
        f"LOWER BOUNDS if any censored), median nfev {int(np.median(nfev[ok & (nfev > 0)]))} "
        f"→ ≤ {per_hour:.1f} states/h/core"
    )
    print(
        f"  corpus extrapolation: 1,041,400 states ≥ {corpus_core_h:,.0f} core-h "
        f"({corpus_core_h / 12:,.0f} h on 12 cores)"
    )


if __name__ == "__main__":
    main()
