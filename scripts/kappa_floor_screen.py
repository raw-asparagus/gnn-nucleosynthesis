#!/usr/bin/env python
"""Step 4, Task 3 — detailed-balance / kappa-floor screen at NSE.

At T9 in {5.0, 6.3, 7.9} x rho x Ye (NSE guaranteed), computes
kappa_r = |f+ - f-|/(f+ + f-) for every strong/EM forward-reverse pair at
the NSE composition, under three rate sources (pyna graphs as built /
MESA 24.08.1 corrected / stock r23.05.1). Pairs with a kappa floor
>~ 1e-3 at NSE are spurious-floor suspects; the variant comparison
attributes each floor to pynucastro (pf-free v-flag reverses), MESA
(gh-575), or the comparison itself. Gates all Step-5/6 kappa conclusions.

Usage: uv run python scripts/kappa_floor_screen.py [--net ...]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from gnn_nucleo.crosscheck import T9_NSE, state_grid  # noqa: E402
from gnn_nucleo.crosscheck.kappa import (  # noqa: E402
    kappa_at_state,
    mesa_ratio_tables,
    strong_pairs,
)

CACHE = REPO / "data/mesa_cache"
SUSPECT = 1e-3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", default="all", choices=["mesa_80", "mesa_151", "all"])
    args = ap.parse_args()
    nets = ["mesa_80", "mesa_151"] if args.net == "all" else [args.net]
    states = state_grid(T9_NSE)

    for net in nets:
        pairs = strong_pairs(net)
        ratios = mesa_ratio_tables(net, T9_NSE)
        print(f"\n=== {net}: {len(pairs)} strong/EM pairs, "
              f"{len(states)} NSE states, variants: pyna, {', '.join(ratios)} ===")
        frames = []
        failed = []
        for t9, rho, ye in states:
            df = kappa_at_state(net, t9, rho, ye, pairs, ratios)
            if df is None:
                failed.append((t9, rho, ye))
                continue
            frames.append(df)
        if failed:
            print(f"NSE solver failed at {len(failed)} states: {failed}")
        all_df = pd.concat(frames, ignore_index=True)
        all_df.to_csv(CACHE / f"kappa_nse_{net}.csv", index=False)

        variants = [c for c in all_df.columns if c.startswith("kappa_")]
        print(f"{'variant':14s} {'median':>10s} {'p90':>10s} {'p99':>10s} "
              f"{'max':>10s} {'pairs>1e-3':>11s}")
        for v in variants:
            per_pair = all_df.groupby(["fwd", "rev"])[v].min()  # floor = best case
            a = all_df[v].dropna()
            print(
                f"{v:14s} {a.median():10.2e} {a.quantile(0.9):10.2e} "
                f"{a.quantile(0.99):10.2e} {a.max():10.2e} "
                f"{(per_pair > SUSPECT).sum():6d}/{per_pair.notna().sum()}"
            )

        # suspects: pairs whose MINIMUM kappa over states exceeds 1e-3
        # (a genuine floor, not a single bad state)
        floor = all_df.groupby(["fwd", "rev"]).agg(
            kappa_pyna_floor=("kappa_pyna", "min"),
            **{
                f"{v}_floor": (v, "min")
                for v in variants
                if v != "kappa_pyna"
            },
        )
        suspects = floor[floor["kappa_pyna_floor"] > SUSPECT].sort_values(
            "kappa_pyna_floor", ascending=False
        )
        print(f"\npyna-variant floor suspects (min-over-states > {SUSPECT}): "
              f"{len(suspects)}")
        print(suspects.head(15).to_string(float_format=lambda x: f"{x:9.2e}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
