#!/usr/bin/env python
"""Step-6: high-T9 training-label pathology census + MESA-version attribution.

Discovered while validating the reference integrator (Step 6 Task 3): shipped
training-set final_* states at T9 ≳ 5 are NOT near NSE — they sit at a
DISPLACED PSEUDO-EQUILIBRIUM (si30/si29/mg26-dominated at high ρ,
c12/o16-dominated at low ρ), frozen across dt decades. Three-way attribution
witness at exact label conditions:

  stock r23.05.1 bbq  (gh-575 Appendix-B bug PRESENT, incl. the chapter-8
                       1→3 reverses c12→3α / be9 / li6 found in Step 4
                       "beyond the paper")   → reproduces the label,
  MESA 24.08.1 bbq    (gh-575 fix verified)  → goes to NSE,
  pf-true reference integrator + independent Saha NSE solver → NSE.

⇒ the labels were generated with a MESA still carrying the bug on the
channels controlling light↔heavy equilibration; the Step-4/-5 working
premise "training labels used the authors' FIXED MESA" is falsified at the
fixed-point level for T9 ≳ 5 (it may hold for the paper's own light-sector
channel list, which is dynamically irrelevant here).

Sections:
  1. census      label(dt=1e2) vs solve_nse by T9 bin, both networks
  2. dt-freeze   witness states' final composition across the nine dts
  3. witness     stock-bbq vs 24.08.1-bbq at witness-state conditions,
                 endpoints vs label and vs NSE (runs bbq if outputs absent;
                 build ~/bbq_24081 against MESA 24.08.1 first)

Usage: uv run python scripts/step6_label_nse_census.py [--witness]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import warnings
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
RUN_ONE = REPO / "scripts" / "bbq_campaign" / "run_one.sh"
DIAG_ROOT = REPO / "data" / "bbq_reruns"

#: witness states (mesa_80 subsample; both displaced-attractor classes)
WITNESS = {
    80: "si-group attractor (T9 7.08, rho 3.0e8)",
    "lowrho": "c12/o16 attractor (hottest low-rho subsample state)",
}


def nse_distance(inputs, X, t9, rho, Z, A):
    from gnn_nucleo.qse import solve_nse

    ye = float(X @ (Z / A))
    nse = solve_nse(inputs, t9 * 1e9, rho, ye)
    if not nse.converged:
        return np.nan, None
    m = (X > 1e-6) | (nse.X > 1e-6)
    d = np.abs(
        np.log10(np.maximum(X[m], 1e-15)) - np.log10(np.maximum(nse.X[m], 1e-15))
    ).max()
    return float(d), nse


def census(net: str, n_per_bin: int = 120) -> None:
    from gnn_nucleo.data.labels import load_step_frame
    from gnn_nucleo.data.subsample import load_subsample_ids
    from gnn_nucleo.graph import load_isotope_table
    from gnn_nucleo.qse import build_inputs

    table = load_isotope_table(net)
    A = table.A.astype(float)
    Z = table.Z.astype(float)
    names = list(table.names)
    inputs = build_inputs(net)
    ids = load_subsample_ids(net)
    cols = ["logT", "logRho"] + [f"final_{n}" for n in names]
    df = load_step_frame(net, "1e2", columns=cols, state_ids=ids[:12000])
    t9 = 10.0 ** df["logT"].to_numpy() / 1e9
    rho = 10.0 ** df["logRho"].to_numpy()
    Xf = df[[f"final_{n}" for n in names]].to_numpy()
    print(f"== {net}: label(dt=1e2) vs NSE by T9 bin "
          f"(max|dlog10 X| over species with X > 1e-6) ==")
    for lo, hi in [(5.0, 5.5), (5.5, 6.0), (6.0, 6.5), (6.5, 7.0), (7.0, 7.94)]:
        sel = np.nonzero((t9 >= lo) & (t9 < hi))[0][:n_per_bin]
        ds = [
            nse_distance(inputs, Xf[k], t9[k], rho[k], Z, A)[0] for k in sel
        ]
        ds = np.array([d for d in ds if np.isfinite(d)])
        print(
            f"  T9 [{lo},{hi}): n {len(ds):>4}  median {np.median(ds):6.2f} dex"
            f"  frac>1dex {(ds > 1).mean():.3f}  frac>3dex {(ds > 3).mean():.3f}"
        )


def find_lowrho_witness() -> int:
    """Hottest low-rho mesa_80 subsample state (c12/o16 attractor class)."""
    from gnn_nucleo.data.labels import load_step_frame
    from gnn_nucleo.data.subsample import load_subsample_ids

    ids = load_subsample_ids("mesa_80")[:12000]
    df = load_step_frame("mesa_80", "1e2", columns=["logT", "logRho"], state_ids=ids)
    t9 = 10.0 ** df["logT"].to_numpy() / 1e9
    rho = 10.0 ** df["logRho"].to_numpy()
    m = (t9 > 7.5) & (rho < 3e7)
    k = int(np.nonzero(m)[0][0])
    return int(ids[k])


def dt_freeze(state_id: int) -> None:
    from gnn_nucleo.data.labels import load_step_frame
    from gnn_nucleo.data.schema import DT_LABELS
    from gnn_nucleo.graph import load_isotope_table

    table = load_isotope_table("mesa_80")
    names = list(table.names)
    print(f"-- state {state_id}: label final dominants across dts --")
    for lab in DT_LABELS:
        df = load_step_frame(
            "mesa_80", lab, columns=[f"final_{n}" for n in names],
            state_ids=[state_id],
        )
        X = df.to_numpy()[0]
        top = np.argsort(-X)[:4]
        print(f"  dt {lab:>5}: " + ", ".join(f"{names[i]} {X[i]:.3e}" for i in top))


def run_witness_bbq(state_id: int) -> dict[str, Path]:
    """Run stock + 24.08.1 bbq at the state's exact label conditions (skips
    existing outputs). Returns dict of output paths."""
    from gnn_nucleo.data.labels import load_step_frame
    from gnn_nucleo.graph import load_isotope_table

    table = load_isotope_table("mesa_80")
    cols = ["logT", "logRho"] + [f"initial_{n}" for n in table.names]
    df = load_step_frame("mesa_80", "1e-6", columns=cols, state_ids=[state_id])
    Xi = df[[f"initial_{n}" for n in table.names]].to_numpy()[0]
    lT = float(df["logT"].iloc[0])
    lR = float(df["logRho"].iloc[0])
    template = (REPO / "scripts/bbq_campaign/inlist.template").read_text()
    out = {}
    for tag, bbq_bin, mesa in [
        ("stock", Path.home() / "bbq/bbq", Path.home() / "mesa-r23.05.1"),
        ("24081", Path.home() / "bbq_24081/bbq", Path.home() / "mesa-24.08.1"),
    ]:
        rd = DIAG_ROOT / f"diag_state{state_id}_{tag}"
        out[tag] = rd / "output.txt"
        out["logT"], out["logRho"] = lT, lR
        if (rd / "output.txt").exists():
            continue
        if not bbq_bin.exists():
            print(f"  [{tag}] SKIPPED: {bbq_bin} not built")
            continue
        rd.mkdir(parents=True, exist_ok=True)
        np.savetxt(rd / "comp.txt", Xi / Xi.sum(), fmt="%.16e")
        ages = np.geomspace(1e-8, 1e2, 101)
        np.savetxt(rd / "times.txt", np.diff(ages, prepend=0.0), fmt="%.16e")
        (rd / "inlist").write_text(template.format(net="mesa_80", logT=lT, logRho=lR))
        env = dict(os.environ, BBQ_BIN=str(bbq_bin), MESA_DIR=str(mesa))
        r = subprocess.run(["bash", str(RUN_ONE), str(rd)], env=env, timeout=3600)
        if r.returncode != 0:
            print(f"  [{tag}] bbq failed rc={r.returncode} (see {rd}/run.log)")
    return out


def witness(state_id: int) -> None:
    from gnn_nucleo.data.labels import load_step_frame
    from gnn_nucleo.data.trajectories import load_trajectory
    from gnn_nucleo.graph import load_isotope_table
    from gnn_nucleo.qse import build_inputs

    table = load_isotope_table("mesa_80")
    A = table.A.astype(float)
    Z = table.Z.astype(float)
    names = list(table.names)
    inputs = build_inputs("mesa_80")
    paths = run_witness_bbq(state_id)
    lT, lR = paths["logT"], paths["logRho"]
    t9, rho = 10.0**lT / 1e9, 10.0**lR

    df = load_step_frame(
        "mesa_80", "1e2", columns=[f"final_{n}" for n in names],
        state_ids=[state_id],
    )
    Xl = df.to_numpy()[0]
    d, _ = nse_distance(inputs, Xl, t9, rho, Z, A)
    print(f"-- state {state_id} witness (T9 {t9:.2f}, rho {rho:.1e}) --")
    top = np.argsort(-Xl)[:4]
    print(f"  label(1e2):   vs NSE {d:6.2f} dex | "
          + ", ".join(f"{names[i]} {Xl[i]:.3f}" for i in top))
    for tag in ("stock", "24081"):
        p = paths.get(tag)
        if p is None or not Path(p).exists():
            continue
        tr = load_trajectory("mesa_80", p, source="rerun", logT=lT, logRho=lR)
        Xe = tr.X[-1]
        d, _ = nse_distance(inputs, Xe, t9, rho, Z, A)
        m = (Xe > 1e-6) | (Xl > 1e-6)
        dl = np.abs(
            np.log10(np.maximum(Xe[m], 1e-15)) - np.log10(np.maximum(Xl[m], 1e-15))
        ).max()
        top = np.argsort(-Xe)[:4]
        print(
            f"  {tag:>5} bbq:    vs NSE {d:6.2f} dex, vs label {dl:6.2f} dex | "
            + ", ".join(f"{names[i]} {Xe[i]:.3f}" for i in top)
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--witness", action="store_true",
                    help="also run/refresh the bbq attribution witnesses")
    ap.add_argument("--n-per-bin", type=int, default=120)
    args = ap.parse_args()
    warnings.simplefilter("ignore")
    for net in ("mesa_80", "mesa_151"):
        census(net, args.n_per_bin)
    dt_freeze(80)
    if args.witness:
        witness(80)
        witness(find_lowrho_witness())


if __name__ == "__main__":
    main()
