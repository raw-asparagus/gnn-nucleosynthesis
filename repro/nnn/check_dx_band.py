#!/usr/bin/env python
"""Per-isotope mean |dX| band check (paper Fig. 3 claim: most isotopes in
1e-4 <= dX_i <= 1e-1, light isotopes smallest).

Uses the NNNcomps.npz written by run_all.sh and the bbq targets parsed
directly from the shipped test files, at the last compared age (same row as
every other reproduced metric).

Run from repro/nnn/ after run_all.sh:  uv run python check_dx_band.py
"""

from __future__ import annotations

import os

import numpy as np

REPO = "/home/ikaros/projects/gnn-nucleosynthesis"
Z = f"{REPO}/data/zenodo/NuclearNeuralNetworks"
CASES = [("mesa_80", "1e-3", 284), ("mesa_151", "1e0", 434)]  # paper Fig.3 panels


def main() -> None:
    for net, dt, idx in CASES:
        nnn = np.load(f"{REPO}/repro/nnn/results/{net}/{dt}/Results/Files/"
                      "NNNcomps.npz")["allNNNcompsToSave"]
        tdir = f"{Z}/test_datasets/{net}/{net}_output_files"
        files = sorted(f for f in os.listdir(tdir) if f.startswith("output"))
        ini, fin = idx + 1, idx + 15
        targets, steps = [], None
        for fname in files:
            with open(f"{tdir}/{fname}") as fh:
                lines = fh.readlines()
            targets.append([max(float(v), 1e-15) for v in lines[fin].split()[4:]])
            if steps is None:
                t0 = float(lines[ini].split()[0])
                t1 = float(lines[fin].split()[0])
                steps = round((t1 - t0) / float(lines[idx].split()[0]))
        dx = np.abs(nnn[:, steps, :] - np.array(targets)).mean(axis=0)
        in_band = float(((dx >= 1e-4) & (dx <= 1e-1)).mean())
        print(f"{net} dt={dt}: per-isotope mean|dX| in "
              f"[{dx.min():.2e}, {dx.max():.2e}]; {100 * in_band:.0f}% of "
              f"isotopes in [1e-4, 1e-1]; median {np.median(dx):.2e}; "
              f"out-of-band all below: {bool((dx[dx < 1e-4] < 1e-4).all() and (dx <= 1e-1).all())}")


if __name__ == "__main__":
    main()
