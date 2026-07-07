#!/usr/bin/env python
"""Model handshake: our own loader vs the upstream pipeline.

Loads one trained NNN checkpoint WITHOUT the upstream ``nuclearNN`` class —
plain ``torch.load`` of the Lightning checkpoint, state_dict walk, and an
explicit Linear/ReLU/log-softmax forward pass reimplemented from the paper's
architecture description — and compares its outputs, on real test-set inputs,
against the upstream class-based path (patched/NNNfunctionsCompPlusEps.py).

Pass criterion (Step-2 spec): max abs deviation <= 1e-6 in model output space
(log-softmax composition outputs + the two linear eps outputs) on >= 100
samples. This is the handshake later phase-6 comparisons rely on.

Run from repro/nnn/:  uv run python check_handshake.py
"""

from __future__ import annotations

import glob
import os
import sys

import numpy as np
import torch

REPO = "/home/ikaros/projects/gnn-nucleosynthesis"
ZENODO = f"{REPO}/data/zenodo/NuclearNeuralNetworks"
MODEL_DIR = (
    f"{ZENODO}/trained_NNN_models/mesa_80/different_timesteps/"
    "age_1e-1_trainingdata_1e6_l1loss_layers_12_factor_8_mesa_80"
)
TEST_DIR = f"{ZENODO}/test_datasets/mesa_80/mesa_80_output_files"
N_ISO = 80
N_SAMPLES = 128
INITIAL_AGE_INDEX = 385  # dt=1e-1 -> timeStepIndex 384 (their mapping), +1


def our_forward(state_dict: dict, x: torch.Tensor, n_iso: int) -> torch.Tensor:
    """Independent forward pass: Linear+ReLU stack, log-softmax on isotopes."""
    n_layers = max(int(k.split("_")[1].split(".")[0]) for k in state_dict)
    for i in range(1, n_layers + 1):
        w, b = state_dict[f"layer_{i}.weight"], state_dict[f"layer_{i}.bias"]
        x = torch.nn.functional.linear(x, w, b)
        if i < n_layers:
            x = torch.relu(x)
    comp = torch.log_softmax(x[:, :n_iso], dim=1)
    return torch.cat([comp, x[:, n_iso:]], dim=1)


def main() -> int:
    ckpt_path = glob.glob(f"{MODEL_DIR}/checkpoints/*.ckpt")[0]

    # --- our loader path: no upstream code involved -------------------------
    ck = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    sd = {k: v for k, v in ck["state_dict"].items()}

    # --- real inputs from the shipped test set ------------------------------
    xs = []
    files = sorted(f for f in os.listdir(TEST_DIR) if f.startswith("output"))
    for fname in files[:N_SAMPLES]:
        with open(f"{TEST_DIR}/{fname}") as fh:
            lines = fh.readlines()
        comp = [float(v) for v in lines[INITIAL_AGE_INDEX].split()[4:]]
        log_t = float(fname.split("_")[2])
        log_rho = float(fname.split("_")[4].removesuffix(".txt"))
        xs.append([log_t, log_rho] + comp)
    x = torch.tensor(xs, dtype=torch.float32)
    print(f"{len(xs)} samples from {TEST_DIR}")

    with torch.no_grad():
        ours = our_forward(sd, x, N_ISO)

    # --- upstream path: their nuclearNN class on the same inputs ------------
    os.environ.setdefault("NNN_ISOTOPES_NUM", str(N_ISO))
    os.environ.setdefault(
        "NNN_DATABASE_FILE",
        f"{ZENODO}/python_scripts_for_analysis/CreateFigures/"
        "Figure3_density_maps/database_files/approx21_cr60_plus_co56_database.csv",
    )
    sys.path.insert(0, f"{REPO}/repro/nnn/patched")
    from NNNfunctionsCompPlusEps import nuclearNN

    model = nuclearNN.load_from_checkpoint(
        ckpt_path, layersNum=12, neuronsNumFactor=8,
        map_location=torch.device("cpu"),
    ).to("cpu")
    model.eval()
    with torch.no_grad():
        theirs = model(x)

    dev = (ours - theirs).abs().max().item()
    comp_dev = (ours[:, :N_ISO] - theirs[:, :N_ISO]).abs().max().item()
    eps_dev = (ours[:, N_ISO:] - theirs[:, N_ISO:]).abs().max().item()
    print(f"max abs deviation (all outputs):     {dev:.3e}")
    print(f"max abs deviation (log-softmax comp): {comp_dev:.3e}")
    print(f"max abs deviation (eps outputs):      {eps_dev:.3e}")
    ok = dev <= 1e-6
    print(f"HANDSHAKE {'PASS' if ok else 'FAIL'} (threshold 1e-6, n={len(xs)})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
