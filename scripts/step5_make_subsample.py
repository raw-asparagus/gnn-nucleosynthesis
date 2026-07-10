#!/usr/bin/env python
"""Draw and PERSIST the Step-5 stratified subsample (state_ids → configs/).

The Sobol grid is non-regenerable, so the drawn state_ids are the artifact:
configs/step5_subsample_<net>_ids.json (the ids) +
configs/step5_subsample_<net>.yaml (parameters, achieved counts, trajectory
selection). Step 6 reuses these files verbatim.

Usage: uv run python scripts/step5_make_subsample.py --net mesa_80
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow.csv as pv
import yaml

REPO = Path(__file__).resolve().parent.parent
TEST_SETS = REPO / "data/zenodo/NuclearNeuralNetworks/test_datasets"


def ye_and_coords(network: str):
    """(t9, logrho, ye_init) over the full training grid (single CSV pass)."""
    from gnn_nucleo.data.labels import training_csv_path
    from gnn_nucleo.graph import load_isotope_table

    table = load_isotope_table(network)
    cols = ["logT", "logRho"] + [f"initial_{n}" for n in table.names]
    t = pv.read_csv(
        training_csv_path(network, "1e-6"),
        convert_options=pv.ConvertOptions(include_columns=cols),
    )
    logT = t.column("logT").to_numpy()
    logrho = t.column("logRho").to_numpy()
    za = table.Z.astype(np.float64) / table.A.astype(np.float64)
    ye = np.zeros(len(logT))
    for name, w in zip(table.names, za):
        ye += t.column(f"initial_{name}").to_numpy() * w
    t9 = 10.0**logT / 1e9
    return t9, logrho, ye


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--net", required=True, choices=["mesa_80", "mesa_151"])
    ap.add_argument("--n", type=int, default=30_000)
    ap.add_argument("--seed", type=int, default=20260710)
    args = ap.parse_args()

    from gnn_nucleo.data.subsample import (
        select_trajectories,
        stratified_sample,
        subsample_ids_path,
    )

    t9, logrho, ye = ye_and_coords(args.net)
    ids, spec = stratified_sample(t9, logrho, ye, n_target=args.n, seed=args.seed)

    traj_dir = TEST_SETS / args.net / f"{args.net}_output_files"
    files = sorted(p.name for p in traj_dir.glob("output_T_*_rho_*.txt"))
    trajectories = select_trajectories(files)

    ids_path = subsample_ids_path(args.net)
    ids_path.write_text(
        json.dumps({"network": args.net, "state_ids": ids.tolist()}) + "\n"
    )
    ids_sha = hashlib.sha256(ids_path.read_bytes()).hexdigest()

    spec_doc = {
        "network": args.net,
        "derived": f"scripts/step5_make_subsample.py, {_dt.date.today().isoformat()}",
        "provenance": "Zenodo 14873443 training grid (state_id = row index)",
        "ids_file": ids_path.name,
        "ids_sha256": ids_sha,
        **spec,
        "trajectories": trajectories,
        "n_trajectories": len(trajectories),
    }
    out_yaml = REPO / "configs" / f"step5_subsample_{args.net}.yaml"
    out_yaml.write_text(yaml.safe_dump(spec_doc, sort_keys=False, width=100))

    print(f"{args.net}: {spec['n_achieved']} state_ids → {ids_path}")
    print(f"  ids sha256 {ids_sha}")
    print(f"  {len(trajectories)} trajectories → {out_yaml}")
    ok = ids[(t9[ids] >= 3.3) & (t9[ids] < 5.0)]
    print(f"  QSE-window states: {len(ok)} ({100 * len(ok) / len(ids):.1f}%)")
    print(f"  outside-strata states in grid: {spec['n_outside_strata']}")


if __name__ == "__main__":
    main()
