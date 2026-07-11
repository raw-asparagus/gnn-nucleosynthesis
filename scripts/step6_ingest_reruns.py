#!/usr/bin/env python
"""Ingest the bbq rerun campaign through the flux engine into FluxStore.

For every DONE campaign run (data/bbq_reruns/<net>/campaign.yaml) evaluates
per-row fluxes over ALL output rows (the pre-stall guard applies downstream
via data.trajectories) and writes trajectory-style chunks (one per run) to

  data/fluxes/<net>/rerun-trajectories            (chugunov_2007 — label config)
  data/fluxes/<net>/rerun-trajectories-unscreened (κ/δ convention twin)

attrs mirror step5_run_fluxes.run_trajectories plus source="rerun",
run_key, family, ye_target — manifold.assemble consumes them directly.

Usage: uv run python scripts/step6_ingest_reruns.py --net both --workers 8
"""

from __future__ import annotations

import argparse
import hashlib
import multiprocessing as mp
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parent.parent
_G: dict = {}

#: chunk-start stride per run (max rows/run ≈ 2600 at the low-T9 wall)
STRIDE = 4096


def _worker_init(network: str, screening: str | None):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        from gnn_nucleo.fluxes.compile import compile_network

        _G["cn"] = compile_network(network, screening=screening)


def _ingest_run(args) -> tuple[str, int]:
    idx, spec, net, run_id = args
    from gnn_nucleo.data.trajectories import load_trajectory
    from gnn_nucleo.fluxes.engine import evaluate_fluxes
    from gnn_nucleo.fluxes.store import FluxStore

    cn = _G["cn"]
    rel = f"data/bbq_reruns/{net}/{spec['run_key']}/output.txt"
    traj = load_trajectory(
        net, REPO / rel, source="rerun",
        logT=float(spec["logT"]), logRho=float(spec["logRho"]),
    )
    n = traj.n_rows
    T = np.full(n, 10.0 ** traj.logT)
    rho = np.full(n, 10.0 ** traj.logRho)
    Y = (traj.X / cn.stoich.A[None, :]).T
    ye = (cn.stoich.Z @ Y) / (cn.stoich.A @ Y)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        batch = evaluate_fluxes(cn, T, rho, Y)
    store = FluxStore(net, run_id)
    store.write_chunk(
        idx * STRIDE,
        np.arange(n),
        T,
        rho,
        ye,
        batch,
        cn.pair_col,
        cn.is_forward_member,
        cn.stoich.weak_mask,
        extra_attrs={
            "screening": str(cn.screening),
            "rate_fnames_sha256": hashlib.sha256(
                "\n".join(cn.stoich.rate_fnames).encode()
            ).hexdigest(),
            "state_id_semantics": "row index within rerun output file",
            "trajectory_file": rel,
            "source": "rerun",
            "run_key": spec["run_key"],
            "family": spec["family"],
            "ye_target": float(spec["ye_target"] or -1.0),
            "logT": float(spec["logT"]),
            "logRho": float(spec["logRho"]),
            "age": traj.age,
        },
    )
    return spec["run_key"], n


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--net", default="both", choices=["mesa_80", "mesa_151", "both"])
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    nets = ["mesa_80", "mesa_151"] if args.net == "both" else [args.net]
    for net in nets:
        manifest = yaml.safe_load(
            (REPO / "data/bbq_reruns" / net / "campaign.yaml").read_text()
        )
        done = [
            (i, s)
            for i, s in enumerate(manifest["runs"])
            if (REPO / "data/bbq_reruns" / net / s["run_key"] / "DONE").exists()
        ]
        for screening, run_id in [
            ("chugunov_2007", "rerun-trajectories"),
            (None, "rerun-trajectories-unscreened"),
        ]:
            t0 = time.perf_counter()
            jobs = [(i, s, net, run_id) for i, s in done]
            n_states = 0
            ctx = mp.get_context("fork")
            with ProcessPoolExecutor(
                max_workers=args.workers,
                mp_context=ctx,
                initializer=_worker_init,
                initargs=(net, screening),
            ) as ex:
                for key, n in ex.map(_ingest_run, jobs):
                    n_states += n
            print(
                f"{net}/{run_id}: {len(done)} runs, {n_states} rows in "
                f"{time.perf_counter() - t0:.0f}s",
                flush=True,
            )


if __name__ == "__main__":
    main()
