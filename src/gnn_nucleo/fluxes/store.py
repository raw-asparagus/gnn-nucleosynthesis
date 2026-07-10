"""Chunked HDF5 persistence for per-state per-reaction fluxes.

Layout: ``data/fluxes/<network>/<run_id>/chunk_<start:08d>.h5`` — one file
per contiguous slice of the run's ordered state list (default 16,384 states),
one writer per file (parallel-safe without SWMR).

Stored per chunk (float64):
- ``state_id`` (n,)   — run-defined identity (training-grid row index for
  grid runs; row index within a trajectory for trajectory runs — see attrs);
- ``T``, ``rho``, ``ye`` (n,) — state coordinates for stratification;
- ``f_plus`` (n, n_rxn) — GROSS per-column rates (ν-export column order);
- ``ydot`` (n, n_species), ``dye_weak`` (n,);
- ``pair_col``, ``is_forward_member``, ``weak_mask`` (n_rxn,) — pair maps.

f⁻/φ/κ are NOT stored: ``f_minus = f_plus[pair_col]`` is an exact
permutation (0 where unpaired), so the reader materializes φ = f⁺ − f⁻ and
κ = |φ|/(f⁺+f⁻) losslessly — this halves disk versus storing all four
(deliberate deviation from the Step-5 brief, recorded in the plan/report).

``complete=True`` is written LAST (after data flush): resumable runs skip
files whose attr is present; a crashed writer leaves it absent.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path

import h5py
import numpy as np

__all__ = ["FluxStore", "FluxChunk", "CHUNK_STATES", "fluxes_root"]

CHUNK_STATES = 16384

_REPO = Path(__file__).resolve().parents[3]


def fluxes_root() -> Path:
    return _REPO / "data" / "fluxes"


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


@dataclass(frozen=True)
class FluxChunk:
    """One chunk read back, with derived quantities materialized."""

    state_id: np.ndarray
    T: np.ndarray
    rho: np.ndarray
    ye: np.ndarray
    f_plus: np.ndarray
    f_minus: np.ndarray
    phi: np.ndarray
    kappa: np.ndarray
    ydot: np.ndarray
    dye_weak: np.ndarray
    pair_col: np.ndarray
    is_forward_member: np.ndarray
    weak_mask: np.ndarray
    attrs: dict


class FluxStore:
    """Writer/reader for one run directory (network × run_id)."""

    def __init__(self, network: str, run_id: str, root: Path | None = None):
        self.network = network
        self.run_id = run_id
        self.dir = (root or fluxes_root()) / network / run_id
        self.dir.mkdir(parents=True, exist_ok=True)

    def chunk_path(self, start: int) -> Path:
        return self.dir / f"chunk_{start:08d}.h5"

    def write_chunk(
        self,
        start: int,
        state_id: np.ndarray,
        T: np.ndarray,
        rho: np.ndarray,
        ye: np.ndarray,
        batch,
        pair_col: np.ndarray,
        is_forward_member: np.ndarray,
        weak_mask: np.ndarray,
        extra_attrs: dict | None = None,
    ) -> Path:
        """Write one chunk atomically-ish (complete attr last).

        ``batch`` is a ``FluxBatch``; only f_plus/ydot/dye_weak are persisted
        (states along rows — transposed from the engine's (n_rxn, n_states)).
        """
        n = len(state_id)
        path = self.chunk_path(start)
        row_chunk = min(1024, n)
        with h5py.File(path, "w") as f:
            f.create_dataset("state_id", data=np.asarray(state_id, dtype=np.int64))
            for name, arr in (("T", T), ("rho", rho), ("ye", ye)):
                f.create_dataset(name, data=np.asarray(arr, dtype=np.float64))
            f.create_dataset(
                "f_plus",
                data=np.ascontiguousarray(batch.f_plus.T),
                chunks=(row_chunk, batch.f_plus.shape[0]),
                compression="gzip",
                compression_opts=4,
                shuffle=True,
            )
            f.create_dataset(
                "ydot",
                data=np.ascontiguousarray(batch.ydot.T),
                chunks=(row_chunk, batch.ydot.shape[0]),
                compression="gzip",
                compression_opts=4,
                shuffle=True,
            )
            f.create_dataset("dye_weak", data=np.asarray(batch.dye_weak))
            f.create_dataset("pair_col", data=np.asarray(pair_col, dtype=np.int64))
            f.create_dataset(
                "is_forward_member", data=np.asarray(is_forward_member, dtype=bool)
            )
            f.create_dataset("weak_mask", data=np.asarray(weak_mask, dtype=bool))
            f.attrs["network"] = self.network
            f.attrs["run_id"] = self.run_id
            f.attrs["start"] = start
            f.attrs["git_commit"] = _git_commit()
            f.attrs["created_utc"] = _dt.datetime.now(_dt.UTC).isoformat()
            for k, v in (extra_attrs or {}).items():
                f.attrs[k] = v
            f.flush()
            f.attrs["complete"] = True
        return path

    def completed_starts(self) -> set[int]:
        done = set()
        for p in sorted(self.dir.glob("chunk_*.h5")):
            try:
                with h5py.File(p, "r") as f:
                    if f.attrs.get("complete", False):
                        done.add(int(f.attrs["start"]))
            except OSError:
                continue
        return done

    def read_chunk(self, start: int) -> FluxChunk:
        with h5py.File(self.chunk_path(start), "r") as f:
            f_plus = f["f_plus"][:].T  # back to (n_rxn, n_states)
            pair_col = f["pair_col"][:]
            paired = pair_col >= 0
            f_minus = np.zeros_like(f_plus)
            f_minus[paired] = f_plus[pair_col[paired]]
            phi = f_plus - f_minus
            denom = f_plus + f_minus
            kappa = np.where(
                denom > 0.0, np.abs(phi) / np.where(denom > 0.0, denom, 1.0), 0.0
            )
            return FluxChunk(
                state_id=f["state_id"][:],
                T=f["T"][:],
                rho=f["rho"][:],
                ye=f["ye"][:],
                f_plus=f_plus,
                f_minus=f_minus,
                phi=phi,
                kappa=kappa,
                ydot=f["ydot"][:].T,
                dye_weak=f["dye_weak"][:],
                pair_col=pair_col,
                is_forward_member=f["is_forward_member"][:],
                weak_mask=f["weak_mask"][:],
                attrs=dict(f.attrs),
            )

    def iter_chunks(self):
        for start in sorted(self.completed_starts()):
            yield self.read_chunk(start)

    def content_hash(self) -> str:
        """sha256 over the sorted chunk files' bytes (RESULTS.md provenance)."""
        h = hashlib.sha256()
        for p in sorted(self.dir.glob("chunk_*.h5")):
            h.update(p.name.encode())
            h.update(p.read_bytes())
        return h.hexdigest()
