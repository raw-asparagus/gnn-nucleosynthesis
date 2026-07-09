#!/usr/bin/env python
"""Step 4, Task 5 — characterize the missing Sobol rows in the training sets.

The training CSVs have 1,041,400 rows vs the 2^20 = 1,048,576 shipped Sobol
grid points (0.68% missing; the Zenodo builder silently drops bbq runs whose
output is truncated, plus a logT/logRho range guard).  There is no sample id,
so rows are matched back to the grid by nearest-neighbour search in
box-normalized (logT, logRho, Ye_initial) space; Ye_initial is reconstructed
from the initial_* mass fractions.  CSV logT/logRho are rounded to 3
decimals (measured), which is ~40x smaller than the typical grid spacing —
match validity is enforced by requiring a unique grid index per row and
missing count == 2^20 - N_rows exactly.

Outputs: docs/figures/sobol_missing_<net>.png + a stdout summary whose
numbers go to RESULTS.md.

Usage: uv run python scripts/sobol_missing_rows.py [--net mesa_80|mesa_151|all]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from gnn_nucleo.crosscheck import (  # noqa: E402
    BOX,
    load_grid_file,
    match_rows_to_grid,
    ye_from_initial,
)

TRAINING = REPO / "data/zenodo/NuclearNeuralNetworks/training_sets"
GRID_FILE = TRAINING / "logT_9.2_to_9.9_logRho_7_to_9_Ye_0.45_to_0.5.txt"
FIG_DIR = REPO / "docs/figures"

#: match tolerance in box-normalized coords: CSV logT/logRho rounding
#: contributes <= 8e-4 and the reconstructed Ye deviates from the grid Ye by
#: up to ~1.5e-4 (~3e-3 normalized; the shipped compositions only
#: approximate the target Ye).  Typical NN spacing of 2^20 points in the
#: unit cube is ~1e-2; validity is enforced by exact-count checks, not tol.
MATCH_TOL = 8e-3

AXES = ("logT", "logRho", "Ye")


def load_states(network: str, dt: str = "1e-1") -> np.ndarray:
    csv = TRAINING / network / f"{network}_{dt}_sec.csv"
    usecols = pd.read_csv(csv, nrows=0).columns
    usecols = [c for c in usecols if c in ("logT", "logRho") or c.startswith("initial_")]
    df = pd.read_csv(csv, usecols=usecols)
    ye = ye_from_initial(df, network)
    return np.column_stack(
        [df["logT"].to_numpy(np.float64), df["logRho"].to_numpy(np.float64), ye]
    )


def check_dt_alignment(network: str, dt_a: str = "1e-1", dt_b: str = "1e2") -> bool:
    cols = ["logT", "logRho"]
    a = pd.read_csv(TRAINING / network / f"{network}_{dt_a}_sec.csv", usecols=cols)
    b = pd.read_csv(TRAINING / network / f"{network}_{dt_b}_sec.csv", usecols=cols)
    return len(a) == len(b) and bool(
        np.array_equal(a.to_numpy(), b.to_numpy())
    )


def analyze(network: str, grid: np.ndarray) -> dict:
    states = load_states(network)
    idx, dist = match_rows_to_grid(states, grid, tol=MATCH_TOL)
    n_rows = len(states)
    n_unmatched_rows = int((idx < 0).sum())
    unique, counts = np.unique(idx[idx >= 0], return_counts=True)
    n_collisions = int((counts > 1).sum())
    missing_mask = np.ones(len(grid), dtype=bool)
    missing_mask[unique] = False
    n_missing = int(missing_mask.sum())
    return {
        "network": network,
        "n_rows": n_rows,
        "n_unmatched_rows": n_unmatched_rows,
        "n_collisions": n_collisions,
        "n_missing": n_missing,
        "expected_missing": len(grid) - n_rows,
        "match_dist_p99": float(np.quantile(dist[idx >= 0], 0.99)),
        "match_dist_max": float(dist[idx >= 0].max()),
        "missing_mask": missing_mask,
    }


def index_runs(missing_mask: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous runs of missing Sobol indices as (start, length)."""
    miss = np.flatnonzero(missing_mask)
    runs = np.split(miss, np.flatnonzero(np.diff(miss) > 1) + 1)
    return [(int(r[0]), len(r)) for r in runs]


def uniformity_stats(grid: np.ndarray, missing_mask: np.ndarray, nbins: int = 20):
    """Per-axis chi-square of missing-point counts against uniformity."""
    out = {}
    n_missing = int(missing_mask.sum())
    expected = n_missing / nbins
    for k, name in enumerate(AXES):
        lo, hi = BOX[("logT", "logRho", "ye")[k]]
        counts, _ = np.histogram(
            grid[missing_mask, k], bins=nbins, range=(lo, hi)
        )
        chi2 = float(((counts - expected) ** 2 / expected).sum())
        out[name] = {
            "counts": counts,
            "chi2": chi2,
            "dof": nbins - 1,
            "min": int(counts.min()),
            "max": int(counts.max()),
            "expected": expected,
        }
    return out


def plot_network(network: str, grid: np.ndarray, missing_mask: np.ndarray) -> Path:
    miss = grid[missing_mask]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    ranges = [BOX["logT"], BOX["logRho"], BOX["ye"]]
    n_missing = len(miss)
    for k, name in enumerate(AXES):
        ax = axes[0, k]
        ax.hist(miss[:, k], bins=40, range=ranges[k], color="tab:red", alpha=0.8)
        ax.axhline(n_missing / 40, color="k", ls="--", lw=1, label="uniform expectation")
        ax.set_xlabel(name)
        ax.set_ylabel("missing rows / bin")
        ax.legend(fontsize=8)
    pairs = [(0, 1), (0, 2), (1, 2)]
    for k, (i, j) in enumerate(pairs):
        ax = axes[1, k]
        h = ax.hist2d(
            miss[:, i], miss[:, j], bins=30,
            range=[ranges[i], ranges[j]], cmap="Reds",
        )
        fig.colorbar(h[3], ax=ax, label="missing rows")
        ax.set_xlabel(AXES[i])
        ax.set_ylabel(AXES[j])
    fig.suptitle(
        f"{network}: {n_missing} missing Sobol rows "
        f"({100 * n_missing / len(grid):.2f}% of 2^20) in (logT, logRho, Ye)"
    )
    fig.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / f"sobol_missing_{network.replace('_', '')}.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", default="all", choices=["mesa_80", "mesa_151", "all"])
    args = ap.parse_args()
    nets = ["mesa_80", "mesa_151"] if args.net == "all" else [args.net]

    grid = load_grid_file(GRID_FILE)
    print(f"grid file: {GRID_FILE.name}  points={len(grid)} (2^20={2**20})")

    masks = {}
    for net in nets:
        aligned = check_dt_alignment(net)
        res = analyze(net, grid)
        masks[net] = res["missing_mask"]
        uni = uniformity_stats(grid, res["missing_mask"])
        print(f"\n=== {net} ===")
        print(f"rows={res['n_rows']}  dt-files row-aligned (1e-1 vs 1e2): {aligned}")
        print(
            f"unmatched_rows={res['n_unmatched_rows']}  "
            f"collisions={res['n_collisions']}  "
            f"missing_grid_points={res['n_missing']} "
            f"(expected {res['expected_missing']})"
        )
        print(
            f"match distance (normalized): p99={res['match_dist_p99']:.2e} "
            f"max={res['match_dist_max']:.2e} (tol {MATCH_TOL:.0e})"
        )
        for name, s in uni.items():
            print(
                f"missing marginal {name:7s}: chi2/dof={s['chi2']:.1f}/{s['dof']} "
                f"bins min/max={s['min']}/{s['max']} (uniform: {s['expected']:.0f})"
            )
        runs = index_runs(res["missing_mask"])
        print(
            f"missing Sobol-index structure: {len(runs)} contiguous runs "
            f"(start, length): {runs if len(runs) <= 10 else runs[:10]}"
        )
        fig = plot_network(net, grid, res["missing_mask"])
        print(f"figure: {fig.relative_to(REPO)}")
        ok = (
            res["n_unmatched_rows"] == 0
            and res["n_collisions"] == 0
            and res["n_missing"] == res["expected_missing"]
        )
        print(f"match-validity: {'OK' if ok else 'FAILED'}")

    if len(masks) == 2:
        m80, m151 = masks["mesa_80"], masks["mesa_151"]
        inter = int((m80 & m151).sum())
        print(
            f"\nmissing-set overlap mesa_80 ∩ mesa_151 = {inter} "
            f"(|80|={int(m80.sum())}, |151|={int(m151.sum())})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
