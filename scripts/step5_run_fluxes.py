#!/usr/bin/env python
"""Run the flux engine over the subsample / trajectories / full corpus.

Modes (exactly one):
  --subsample     the persisted configs/step5_subsample_<net>_ids.json states
  --trajectories  ALL rows of the ~20 selected constant-(T,ρ) test trajectories
  --full          the full 1,041,400-state training grid (chunked, resumable)

Output: data/fluxes/<net>/<run_id>/chunk_*.h5 (gitignored; content hash and
generation parameters go to RESULTS.md). Resume with --resume (skips chunks
whose complete attr is set). Parallelism: --workers N (fork; the state arrays
are shared copy-on-write, each worker compiles its own network once).

Usage:
  uv run python scripts/step5_run_fluxes.py --net mesa_80 --subsample
  uv run python scripts/step5_run_fluxes.py --net mesa_151 --full --workers 12 --resume
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
import pyarrow.csv as pv

REPO = Path(__file__).resolve().parent.parent
TEST_SETS = REPO / "data/zenodo/NuclearNeuralNetworks/test_datasets"

# fork-shared globals (read-only in workers)
_G: dict = {}


def _load_grid_states(network: str, state_ids: np.ndarray | None):
    """(state_ids, T, rho, X) for grid states (initial_* of the 1e-6 file —
    row-aligned across dt files, so this is THE initial state)."""
    from gnn_nucleo.data.labels import training_csv_path
    from gnn_nucleo.graph import load_isotope_table

    table = load_isotope_table(network)
    cols = ["logT", "logRho"] + [f"initial_{n}" for n in table.names]
    t = pv.read_csv(
        training_csv_path(network, "1e-6"),
        convert_options=pv.ConvertOptions(include_columns=cols),
    )
    n_all = t.num_rows
    if state_ids is None:
        state_ids = np.arange(n_all, dtype=np.int64)
    logT = t.column("logT").to_numpy()[state_ids]
    logrho = t.column("logRho").to_numpy()[state_ids]
    X = np.empty((len(state_ids), table.n), dtype=np.float64)
    for i, name in enumerate(table.names):
        X[:, i] = t.column(f"initial_{name}").to_numpy()[state_ids]
    return state_ids, 10.0**logT, 10.0**logrho, X


def _rate_fnames_sha(cn) -> str:
    return hashlib.sha256("\n".join(cn.stoich.rate_fnames).encode()).hexdigest()


def _worker_init(network: str, screening: str | None):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        from gnn_nucleo.fluxes.compile import compile_network

        _G["cn"] = compile_network(network, screening=screening)


def _run_chunk(args) -> tuple[int, int]:
    start, run_id = args
    from gnn_nucleo.fluxes.engine import evaluate_fluxes
    from gnn_nucleo.fluxes.store import FluxStore

    cn = _G["cn"]
    ids, T, rho, X = _G["states"]
    chunk = _G["chunk_size"]
    sl = slice(start, min(start + chunk, len(ids)))
    Y = (X[sl] / cn.stoich.A[None, :]).T  # (n_species, n_states)
    ye = (cn.stoich.Z @ Y) / (cn.stoich.A @ Y)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        batch = evaluate_fluxes(cn, T[sl], rho[sl], Y)
    store = FluxStore(cn.network, run_id)
    store.write_chunk(
        start,
        ids[sl],
        T[sl],
        rho[sl],
        ye,
        batch,
        cn.pair_col,
        cn.is_forward_member,
        cn.stoich.weak_mask,
        extra_attrs={
            "screening": str(cn.screening),
            "rate_fnames_sha256": _rate_fnames_sha(cn),
            "state_id_semantics": "training-grid row index",
        },
    )
    return start, sl.stop - sl.start


def run_grid(network, run_id, state_ids, screening, workers, chunk_size, resume):
    from gnn_nucleo.fluxes.store import FluxStore

    ids, T, rho, X = _load_grid_states(network, state_ids)
    _G["states"] = (ids, T, rho, X)
    _G["chunk_size"] = chunk_size
    starts = list(range(0, len(ids), chunk_size))
    if resume:
        done = FluxStore(network, run_id).completed_starts()
        starts = [s for s in starts if s not in done]
        print(f"resume: {len(done)} chunks done, {len(starts)} to go")
    t0 = time.perf_counter()
    n_states = 0
    if workers <= 1:
        _worker_init(network, screening)
        for s in starts:
            _, n = _run_chunk((s, run_id))
            n_states += n
            print(f"  chunk {s:>8d} done ({n} states)", flush=True)
    else:
        # fork explicitly: 3.14 defaults to forkserver, which would not
        # inherit the copy-on-write state arrays in _G
        ctx = mp.get_context("fork")
        with ProcessPoolExecutor(
            max_workers=workers,
            mp_context=ctx,
            initializer=_worker_init,
            initargs=(network, screening),
        ) as ex:
            for s, n in ex.map(_run_chunk, [(s, run_id) for s in starts]):
                n_states += n
                print(f"  chunk {s:>8d} done ({n} states)", flush=True)
    dt = time.perf_counter() - t0
    if n_states:
        print(
            f"{network}/{run_id}: {n_states} states in {dt:.1f}s "
            f"({60 * n_states / dt:,.0f} states/min wall, {workers} workers)"
        )


def run_trajectories(network, screening, run_id="trajectories"):
    import yaml

    from gnn_nucleo.fluxes.engine import evaluate_fluxes
    from gnn_nucleo.fluxes.store import FluxStore
    from gnn_nucleo.graph import load_isotope_table

    spec = yaml.safe_load(
        (REPO / "configs" / f"step5_subsample_{network}.yaml").read_text()
    )
    table = load_isotope_table(network)
    _worker_init(network, screening)
    cn = _G["cn"]
    store = FluxStore(network, run_id)
    t0 = time.perf_counter()
    n_states = 0
    for fi, fname in enumerate(spec["trajectories"]):
        path = TEST_SETS / network / f"{network}_output_files" / fname
        with open(path) as fh:
            header = fh.readline().split()
        iso_cols = header[4:]
        if list(iso_cols) != list(table.names):
            raise ValueError(f"{fname}: isotope column order != isotope table")
        data = np.loadtxt(path, skiprows=1)
        logT = float(fname.split("_T_")[1].split("_rho_")[0])
        logrho = float(fname.split("_rho_")[1].removesuffix(".txt"))
        X = data[:, 4:]
        n = len(X)
        T = np.full(n, 10.0**logT)
        rho = np.full(n, 10.0**logrho)
        Y = (X / cn.stoich.A[None, :]).T
        ye = (cn.stoich.Z @ Y) / (cn.stoich.A @ Y)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            batch = evaluate_fluxes(cn, T, rho, Y)
        store.write_chunk(
            fi * 2048,
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
                "rate_fnames_sha256": _rate_fnames_sha(cn),
                "state_id_semantics": "row index within trajectory file",
                "trajectory_file": fname,
                "logT": logT,
                "logRho": logrho,
                "age": data[:, 0],  # bbq ages (float array attr) for the dt view
            },
        )
        n_states += n
        print(f"  {fname}: {n} rows", flush=True)
    dt = time.perf_counter() - t0
    print(f"{network}/{run_id}: {n_states} states in {dt:.1f}s")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--net", required=True, choices=["mesa_80", "mesa_151"])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--subsample", action="store_true")
    mode.add_argument("--trajectories", action="store_true")
    mode.add_argument("--full", action="store_true")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--screening", default="chugunov_2007")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--chunk", type=int, default=16384)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    screening = None if args.screening in ("none", "None") else args.screening

    if args.trajectories:
        run_trajectories(args.net, screening, args.run_id or "trajectories")
        return

    if args.subsample:
        from gnn_nucleo.data.subsample import load_subsample_ids

        state_ids = load_subsample_ids(args.net)
        run_id = args.run_id or (
            "subsample" if screening else "subsample-unscreened"
        )
    else:
        state_ids = None
        run_id = args.run_id or "full"
    run_grid(
        args.net, run_id, state_ids, screening, args.workers, args.chunk, args.resume
    )


if __name__ == "__main__":
    main()
