#!/usr/bin/env python
"""Step 4, Task 4 — Appendix-B bug-state determination for stock r23.05.1.

Grichener et al. 2025 (App. B; MESAHub/mesa#575) report that MESA computed
endo-energetic multi-particle inverse rates from detailed balance while
omitting the particle-number phase-space factor.  Static source inspection
(rates/private/reaclib_support.f90 compute_rev_ratio) shows the factor
fac = (1e9 kB / 2 pi hbar^2 N_A)^1.5 / N_A and the accompanying T^{3/2}
are applied ONLY when the forward has a single product (photodisintegration
reverse); every reverse of a chapter with Nout != 1 and Nin != Nout gets
inverse_exp = 0 and no fac.

This script makes that empirical: it evaluates the affected channels with
the MESA probe (raw rates, screening off) and compares against pynucastro
2.12.0 (JINA v-flag reverse fits) and against the analytically expected
missing factor |dN| * log10(fac * T9^{3/2} * (amu-mass ratio)^{3/2}).
Controls: all MATCHED_CLEAN REACLIB forwards and the ordinary
photodisintegration reverses (chapter 4), where agreement should be tight.

Usage: uv run python scripts/appendixb_check.py [--net mesa_80|mesa_151|all]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from gnn_nucleo.crosscheck import T9_GRID, run_probe, t9_stdin  # noqa: E402
from gnn_nucleo.crosscheck.mesa_dump import dump_to_records  # noqa: E402
from gnn_nucleo.crosscheck.reconcile import pyna_inventory  # noqa: E402

# fac in cgs: (1e9 kB / (2 pi hbar^2 N_A))^{3/2} / N_A  [reaclib_support.f90:197]
KB = 1.380649e-16
HBAR = 1.054571817e-27
NA = 6.02214076e23
FAC = (1e9 * KB / (2 * np.pi * HBAR**2 * NA)) ** 1.5 / NA

T9_CHECK = (1.6, 4.0, 7.9)


def mesa_rates(network: str) -> pd.DataFrame:
    return run_probe("eval_rates", f"{network}.net", stdin_text=t9_stdin(T9_GRID))


def pyna_rates_by_key(network: str, t9s) -> dict[str, dict[float, float]]:
    """{canonical key: {t9: rate}} for every non-tabular pynucastro rate."""
    from gnn_nucleo.graph import build_rate_collection, load_isotope_table

    inv = {r["fname"]: r["key"] for r in pyna_inventory(network)}
    table = load_isotope_table(network)
    rc, _ = build_rate_collection(table, disposition=None)
    out: dict[str, dict[float, float]] = {}
    for rate in rc.get_rates():
        if rate.tabular if hasattr(rate, "tabular") else False:
            continue
        import pynucastro as pyna

        if isinstance(rate, pyna.rates.TabularRate):
            continue
        vals = {}
        for t9 in t9s:
            try:
                vals[t9] = float(rate.eval(t9 * 1e9))
            except Exception:
                vals[t9] = np.nan
        out[inv[rate.fname]] = vals
    return out


def analyze(network: str) -> pd.DataFrame:
    dump = run_probe("dump_net", f"{network}.net")
    inv = run_probe("dump_inverse", f"{network}.net")
    mesa = mesa_rates(network)
    mesa_records = dump_to_records(dump)
    key_by_name = {r["mesa_handle"]: r["key"] for r in mesa_records}
    pyna = pyna_rates_by_key(network, T9_CHECK)

    inv["dN"] = inv.n_in - inv.n_out
    # affected: forward Nout != 1 and particle number changes -> fac omitted
    affected = inv[(inv.n_out != 1) & (inv.dN != 0)].copy()
    # photodisintegration reverses of multi-body forwards (ch8: 3->1):
    # fac^1 applied where fac^{dN} would be needed
    photo_multi = inv[(inv.n_out == 1) & (inv.dN > 1)].copy()

    mesa_by_name = dict(
        zip(zip(mesa["name"], mesa["t9"]), mesa["raw_rate"], strict=True)
    )

    def compare(rows: pd.DataFrame, klass: str) -> list[dict]:
        recs = []
        for row in rows.itertuples():
            key = key_by_name[row.name]
            for t9 in T9_CHECK:
                m = mesa_by_name.get((row.name, t9), np.nan)
                p = pyna.get(key, {}).get(t9, np.nan)
                if not (m > 0 and p > 0):
                    continue
                dlog = np.log10(m) - np.log10(p)
                # expected missing factor if MESA omitted fac^dN T^{1.5 dN}
                # (reverse direction: MESA reverse too LARGE by fac^{|dN|}
                # for endothermic ch6/7 reverses)
                miss = abs(row.dN) * np.log10(FAC * t9**1.5)
                recs.append(
                    {
                        "network": network,
                        "class": klass,
                        "mesa_name": row.name,
                        "chapter": row.chapter,
                        "dN": row.dN,
                        "q_fwd": row.reaclib_q,
                        "t9": t9,
                        "log10_mesa": np.log10(m),
                        "log10_pyna": np.log10(p),
                        "dlog10": dlog,
                        "expected_missing_log10": miss,
                    }
                )
        return recs

    recs = compare(affected, "multi_body_inverse")
    recs += compare(photo_multi, "photo_of_multibody")

    # control: matched-clean ch4 photodisintegration reverses + fwds
    ctrl = inv[(inv.chapter == 4)].head(30)
    recs += compare(ctrl, "control_ch4_reverse")
    return pd.DataFrame(recs)


def control_forwards(network: str) -> pd.Series:
    """|dlog10| distribution over ALL matched non-weak REACLIB rates at
    T9=4 (harness sanity: should sit at ~0)."""
    dump = run_probe("dump_net", f"{network}.net")
    mesa = mesa_rates(network)
    mesa_records = dump_to_records(dump)
    key_by_name = {r["mesa_handle"]: r["key"] for r in mesa_records}
    fwd_names = {
        r["mesa_handle"]
        for r in mesa_records
        if r["source"] == "reaclib_forward" and not r["is_weak"]
    }
    pyna = pyna_rates_by_key(network, (4.0,))
    rows = mesa[(mesa.t9 == 4.0) & (mesa.name.isin(fwd_names))]
    d = []
    for row in rows.itertuples():
        p = pyna.get(key_by_name[row.name], {}).get(4.0, np.nan)
        if row.raw_rate > 0 and p > 0:
            d.append(abs(np.log10(row.raw_rate) - np.log10(p)))
    return pd.Series(d)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", default="all", choices=["mesa_80", "mesa_151", "all"])
    args = ap.parse_args()
    nets = ["mesa_80", "mesa_151"] if args.net == "all" else [args.net]

    print(f"fac = (1e9 kB/(2 pi hbar^2 NA))^1.5/NA = {FAC:.6e}  "
          f"(log10 = {np.log10(FAC):.4f})")
    all_frames = []
    for net in nets:
        ctrl = control_forwards(net)
        print(
            f"\n=== {net} ===\n"
            f"control (all {len(ctrl)} matched clean REACLIB forwards, T9=4): "
            f"median |dlog10| = {ctrl.median():.2e}, p99 = {ctrl.quantile(0.99):.2e}, "
            f"max = {ctrl.max():.2e}"
        )
        df = analyze(net)
        all_frames.append(df)
        for klass in ("multi_body_inverse", "photo_of_multibody", "control_ch4_reverse"):
            sub = df[df["class"] == klass]
            if sub.empty:
                continue
            print(f"\n[{klass}] ({sub.mesa_name.nunique()} channels)")
            with pd.option_context("display.width", 200):
                print(
                    sub[
                        ["mesa_name", "chapter", "dN", "t9", "log10_mesa",
                         "log10_pyna", "dlog10", "expected_missing_log10"]
                    ].to_string(index=False, float_format=lambda x: f"{x:9.3f}")
                    if klass != "control_ch4_reverse"
                    else f"|dlog10|: median={sub.dlog10.abs().median():.3f} "
                    f"p99={sub.dlog10.abs().quantile(0.99):.3f} "
                    f"max={sub.dlog10.abs().max():.3f}"
                )
    out = REPO / "data/mesa_cache/appendixb_comparison.csv"
    pd.concat(all_frames).to_csv(out, index=False)
    print(f"\nfull table: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
