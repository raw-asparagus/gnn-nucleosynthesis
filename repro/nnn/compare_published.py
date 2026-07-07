#!/usr/bin/env python
"""Compare our reproduced NNN evaluation against the shipped published values.

For every (network, dt): read OUR AverageLossesNNN.csv (from repro/nnn/results/,
produced by the patched upstream pipeline on the shipped models + test sets)
and THEIR shipped result CSVs under CreateFigures/Figure4_main_results/ (the
exact numbers behind paper Figs. 4-5). Their plotting uses the LAST row of
each series (extractLastValue); we compare on that row.

Improvement percentages use their Fig. 5 formula: 100 * (small-net loss /
NNN loss), with the small-net (approx21) losses from the shipped
AverageLosses21to80.csv. Paper range checks (sourced, arXiv:2503.00115 §3):
Ye improvement 390-660% (mesa_80) / 280-400% (mesa_151); Abar 150-290% /
260-360%; e_nuc 250-450% / 280-750%; eps_nu crossover: NNN better at short
dt, worse for dt >~ 0.1 s; NNN normalized Ye error 0.4-0.75%.

Run from repro/nnn/:  uv run python compare_published.py
"""

from __future__ import annotations

import csv
import os

REPO = "/home/ikaros/projects/gnn-nucleosynthesis"
FIG4 = (
    f"{REPO}/data/zenodo/NuclearNeuralNetworks/python_scripts_for_analysis/"
    "CreateFigures/Figure4_main_results"
)
OURS = f"{REPO}/repro/nnn/results"
DTS = ["1e-6", "1e-5", "1e-4", "1e-3", "1e-2", "1e-1", "1e0", "1e1", "1e2"]
IDX = dict(zip(DTS, [134, 184, 234, 284, 334, 384, 434, 484, 534]))
NET_DIR = {"mesa_80": "mesa_80_results", "mesa_151": "mesa151_results"}
LOSS_COLS = [
    "AverageLinearLoss", "AverageYeLoss", "AverageAbarLoss",
    "AverageZbarLoss", "AverageEpsNucLoss", "AverageEpsNuLoss",
]
PAPER_RANGES = {  # sourced: arXiv:2503.00115 section 3
    ("mesa_80", "Ye"): (390, 660), ("mesa_151", "Ye"): (280, 400),
    ("mesa_80", "Abar"): (150, 290), ("mesa_151", "Abar"): (260, 360),
    ("mesa_80", "EpsNuc"): (250, 450), ("mesa_151", "EpsNuc"): (280, 750),
}


def last_row(path: str) -> dict[str, float]:
    rows = list(csv.DictReader(open(path)))
    return {k: float(v) for k, v in rows[-1].items() if v not in ("", None)}


def main() -> None:
    print("== per-(net,dt) reproduction: ours vs shipped published CSVs "
          "(ratio ours/theirs on the last row) ==")
    worst = {}
    for net in ["mesa_80", "mesa_151"]:
        for dt in DTS:
            ours_p = f"{OURS}/{net}/{dt}/Results/Files/AverageLossesNNN.csv"
            theirs_p = f"{FIG4}/{NET_DIR[net]}/{dt}/timeStepIndex_{IDX[dt]}/AverageLossesNNN.csv"
            if not (os.path.exists(ours_p) and os.path.exists(theirs_p)):
                print(f"{net} {dt}: MISSING {'ours' if not os.path.exists(ours_p) else 'theirs'}")
                continue
            o, t = last_row(ours_p), last_row(theirs_p)
            ratios = {c: o[c] / t[c] for c in LOSS_COLS if c in o and c in t and t[c] != 0}
            bad = {c: r for c, r in ratios.items() if not 0.5 <= r <= 2.0}
            tag = "PASS" if not bad else f"FAIL {bad}"
            rmin, rmax = min(ratios.values()), max(ratios.values())
            print(f"{net:9s} {dt:>5s}  ratio[{rmin:6.3f},{rmax:6.3f}]  {tag}")
            for c, r in ratios.items():
                k = (net, c)
                worst[k] = max(worst.get(k, 1.0), max(r, 1 / r))

    print("\n== worst ours/theirs disagreement per metric ==")
    for (net, c), w in sorted(worst.items()):
        print(f"{net:9s} {c:22s} worst-factor {w:.4f}")

    print("\n== improvement % (their Fig.5 formula; shipped approx21 losses / OUR NNN losses) ==")
    print(f"{'net':9s} {'dt':>5s} {'Ye%':>9s} {'Abar%':>9s} {'EpsNuc%':>10s}"
          f" {'EpsNu%':>12s} {'NNN dYe/Ye %':>13s}")
    summary: dict[tuple[str, str], list[float]] = {}
    for net in ["mesa_80", "mesa_151"]:
        for dt in DTS:
            base = f"{FIG4}/{NET_DIR[net]}/{dt}/timeStepIndex_{IDX[dt]}"
            ours_p = f"{OURS}/{net}/{dt}/Results/Files/AverageLossesNNN.csv"
            small_p = f"{base}/AverageLosses21to80.csv"
            if not (os.path.exists(ours_p) and os.path.exists(small_p)):
                continue
            o = last_row(ours_p)
            s = last_row(small_p)
            params = last_row(f"{OURS}/{net}/{dt}/Results/Files/AverageParamNNN.csv")
            imp = {
                "Ye": 100 * s["AverageYeLoss21to80"] / o["AverageYeLoss"],
                "Abar": 100 * s["AverageAbarLoss21to80"] / o["AverageAbarLoss"],
                "EpsNuc": 100 * s["AverageEpsNucLoss21to80"] / o["AverageEpsNucLoss"],
                "EpsNu": 100 * s["AverageEpsNuLoss21to80"] / o["AverageEpsNuLoss"],
            }
            ye_rel = 100 * o["AverageYeLoss"] / params["bbqAverageYe"]
            print(f"{net:9s} {dt:>5s} {imp['Ye']:9.0f} {imp['Abar']:9.0f} "
                  f"{imp['EpsNuc']:10.0f} {imp['EpsNu']:12.0f} {ye_rel:13.3f}")
            for k, v in imp.items():
                summary.setdefault((net, k), []).append(v)
            summary.setdefault((net, "YeRel"), []).append(ye_rel)

    print("\n== reproduced ranges vs paper (sourced) ==")
    for (net, k), vals in sorted(summary.items()):
        lo, hi = min(vals), max(vals)
        if (net, k) in PAPER_RANGES:
            plo, phi = PAPER_RANGES[(net, k)]
            ok = lo / plo >= 0.5 and hi / phi <= 2.0
            print(f"{net:9s} {k:6s} reproduced [{lo:.0f}, {hi:.0f}]%  paper [{plo}, {phi}]%  "
                  f"{'PASS(<=2x)' if ok else 'CHECK'}")
        elif k == "EpsNu":
            crossover = [v < 100 for v in vals]  # worse than small net
            print(f"{net:9s} EpsNu  improvement [{lo:.0f}, {hi:.0f}]%; "
                  f"NNN worse (<100%) at dts: "
                  f"{[d for d, w in zip(DTS, crossover) if w]} (paper: worse for dt >~ 0.1 s)")
        elif k == "YeRel":
            print(f"{net:9s} NNN dYe/Ye reproduced [{lo:.3f}, {hi:.3f}]%  paper 0.4-0.75%")


if __name__ == "__main__":
    main()
