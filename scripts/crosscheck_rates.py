#!/usr/bin/env python
"""Step 4, Task 2 — rate-level numerical cross-check on the regime grid.

Compares MESA (label configuration: stock r23.05.1 REACLIB 20171020 +
weaklib LMP>Oda>FFN, chugunov screening — bbq defaults) against
pynucastro 2.12.0 for every matched reaction:

1. bare REACLIB rates (screening off, T-only) on T9_GRID;
2. weak rates over the full (T9, rho, Ye) grid, per-pair table sources;
3. chugunov screening factors on identical plasma states
   (vs pynucastro chugunov_2007 and chugunov_2009).

Appendix-B channels are excluded from all gates
(configs/appendixb_excluded_channels.yaml). Outputs:
configs/rate_outliers.yaml + CSVs under data/mesa_cache/ + stdout summary
for RESULTS.md / docs/rate-crosscheck.md.

Usage: uv run python scripts/crosscheck_rates.py [--net ...] [--part bare|weak|screen|all]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from gnn_nucleo.crosscheck import T9_GRID, state_grid  # noqa: E402
from gnn_nucleo.crosscheck.rates_compare import (  # noqa: E402
    band_for,
    compare_bare,
    compare_screening,
    compare_weak,
    summarize,
)

CACHE = REPO / "data/mesa_cache"


#: individual-flag thresholds: channels beyond these are NOT explained by the
#: class-level attributions (pf handling for DB inverses, interpolation for
#: weak tabular, bit-identical fits for forwards) and are carried as open
#: flags into Step 5. Class-level bulk behaviour is documented in
#: docs/rate-crosscheck.md.
SEVERE = {
    "reaclib_forward": 0.05,  # >> 0.004 band: REACLIB snapshot refit
    "db_inverse": 0.5,
    "weak_reaclib": 0.5,
    "weak_tabular": 0.5,
}


def outliers_from(df: pd.DataFrame, network: str) -> list[dict]:
    out = []
    for (key, cat), sub in df.groupby(["key", "category"]):
        band = band_for(cat)
        severe = SEVERE.get(cat)
        if band is None or severe is None:
            continue
        worst = sub.loc[sub["dlog10"].abs().idxmax()]
        if abs(worst["dlog10"]) <= severe:
            continue
        rec = {
            "network": network,
            "key": str(key),
            "mesa_handle": str(worst.get("name", "")),
            "category": str(cat),
            "band": float(band),
            "worst_dlog10": round(float(worst["dlog10"]), 4),
            "worst_at": {
                "t9": float(worst["t9"]),
                **(
                    {"rho": float(worst["rho"]), "ye": float(worst["ye"])}
                    if "rho" in sub.columns
                    else {}
                ),
            },
        }
        out.append(rec)
    return sorted(out, key=lambda r: -abs(r["worst_dlog10"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", default="all", choices=["mesa_80", "mesa_151", "all"])
    ap.add_argument(
        "--part", default="all", choices=["bare", "weak", "screen", "all"]
    )
    args = ap.parse_args()
    nets = ["mesa_80", "mesa_151"] if args.net == "all" else [args.net]
    grid = state_grid()
    all_outliers: list[dict] = []

    for net in nets:
        print(f"\n================ {net} ================")
        if args.part in ("bare", "all"):
            bare = compare_bare(net, T9_GRID)
            bare.to_csv(CACHE / f"crosscheck_bare_{net}.csv", index=False)
            print("\n-- bare rates (screening off), |dlog10| by category --")
            print(summarize(bare).to_string(index=False, float_format=lambda x: f"{x:10.4g}"))
            all_outliers += outliers_from(
                bare[~bare.category.isin(["appendixb_excluded", "construction_swap"])],
                net,
            )
            swaps = bare[bare.category == "construction_swap"]
            if not swaps.empty:
                a = swaps.dlog10.abs()
                print(
                    f"construction-swapped pairs (no band): median {a.median():.3g}, "
                    f"p95 {a.quantile(0.95):.3g}, max {a.max():.3g}"
                )
        if args.part in ("weak", "all"):
            weak = compare_weak(net, grid)
            weak.to_csv(CACHE / f"crosscheck_weak_{net}.csv", index=False)
            print("\n-- weak rates over full grid, |dlog10| by category --")
            print(summarize(weak).to_string(index=False, float_format=lambda x: f"{x:10.4g}"))
            src_mismatch = weak[
                (weak.category == "weak_tabular")
                & (weak.mesa_table_source.map(
                    {"LMP": "langanke", "OHMT": "oda", "FFN": "ffn"}
                ) != weak.pyna_source)
            ]
            print(f"per-pair table-source mismatches: {src_mismatch.key.nunique()}")
            all_outliers += outliers_from(weak, net)
        if args.part in ("screen", "all"):
            scr = compare_screening(net, grid)
            scr.to_csv(CACHE / f"crosscheck_screen_{net}.csv", index=False)
            print("\n-- chugunov screening factor ratios (mesa/pyna) --")
            for col in ("ratio_2007", "ratio_2009"):
                r = scr[col].dropna()
                print(
                    f"{col}: median {r.median():.6f}, "
                    f"[p1, p99] = [{r.quantile(0.01):.6f}, {r.quantile(0.99):.6f}], "
                    f"max|log10| = {np.abs(np.log10(r)).max():.4g}"
                )

    if args.part == "all" and args.net == "all":
        doc = {
            "derived": "scripts/crosscheck_rates.py, 2026-07-10",
            "policy": (
                "every entry is either explained in docs/rate-crosscheck.md "
                "or carried as an open flag into Step 5 (flux derivations "
                "exclude or footnote unexplained channels)"
            ),
            "explained_classes": {
                "db_inverse_bulk": (
                    "signed median dlog10 grows 0.005->0.013 dex over "
                    "T9 1.6->7.9: partition-function handling (MESA applies "
                    "pf ratios to DB reverses; pynucastro evaluates JINA "
                    "v-flag fits pf-free) plus winvn-vs-REACLIB mass/Q "
                    "provenance. Individual flags only beyond 0.5 dex."
                ),
                "weak_tabular_bulk": (
                    "interpolation scheme on the shared coarse tables: at "
                    "the T9=5 table node median |dlog10| = 0.003; off-node "
                    "medians 0.03-0.18 dex are MESA-bilinear vs pynucastro "
                    "interpolant differences, largest for steep beta-minus "
                    "channels. Labels used MESA's bilinear values."
                ),
                "reaclib_forward_bulk": (
                    "median |dlog10| = machine zero (bit-identical fits); "
                    "channels beyond 0.05 dex are REACLIB snapshot refits "
                    "(MESA jina 20171020 vs pynucastro 2.12.0 snapshot)."
                ),
                "appendixb": (
                    "stock-r23.05.1 gh-575 channels, see "
                    "configs/appendixb_excluded_channels.yaml; verified "
                    "fixed in MESA 24.08.1 to <= 1.9 dex residual except "
                    "r_h1_h1_he4_to_he3_he3 (2.7 dex in BOTH MESA versions "
                    "=> not a gh-575 channel; open flag)."
                ),
            },
            "n_outliers": len(all_outliers),
            "outliers": all_outliers,
        }
        (REPO / "configs/rate_outliers.yaml").write_text(
            yaml.safe_dump(doc, sort_keys=False, width=100)
        )
        print(f"\nwrote configs/rate_outliers.yaml ({len(all_outliers)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
