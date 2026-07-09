"""Missing-Sobol-rows analysis helpers (Step 4, Task 5).

The training CSVs carry no Ye column and no sample id; Ye_initial is
reconstructed from the initial mass fractions as Ye = sum_i Z_i X_i / A_i
(integer Z, A from the isotope tables), and rows are matched back to the
shipped 2^20 Sobol grid file by nearest-neighbour search in box-normalized
(logT, logRho, Ye) coordinates.  The grid was generated with an UNSEEDED
scrambled scipy Sobol sampler (gridGenerator.py), so regeneration cannot
reproduce it — the shipped grid file is the only ground truth.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from gnn_nucleo.graph import load_isotope_table

#: published sampling box (gridGenerator.py; sourced)
BOX = {"logT": (9.2, 9.9), "logRho": (7.0, 9.0), "ye": (0.45, 0.5)}


def ye_from_initial(df: pd.DataFrame, network: str) -> np.ndarray:
    """Reconstruct Ye_initial = sum Z_i X_i / A_i from initial_* columns."""
    table = load_isotope_table(network)
    ye = np.zeros(len(df), dtype=np.float64)
    xsum = np.zeros(len(df), dtype=np.float64)
    for name, z, a in zip(table.names, table.Z, table.A, strict=True):
        x = df[f"initial_{name}"].to_numpy(dtype=np.float64)
        ye += x * (float(z) / float(a))
        xsum += x
    return ye / xsum


def xsum_initial(df: pd.DataFrame, network: str) -> np.ndarray:
    table = load_isotope_table(network)
    xsum = np.zeros(len(df), dtype=np.float64)
    for name in table.names:
        xsum += df[f"initial_{name}"].to_numpy(dtype=np.float64)
    return xsum


def normalize_states(
    logT: np.ndarray, logRho: np.ndarray, ye: np.ndarray
) -> np.ndarray:
    """Map states into the unit cube using the published box."""
    out = np.column_stack(
        [
            (logT - BOX["logT"][0]) / (BOX["logT"][1] - BOX["logT"][0]),
            (logRho - BOX["logRho"][0]) / (BOX["logRho"][1] - BOX["logRho"][0]),
            (ye - BOX["ye"][0]) / (BOX["ye"][1] - BOX["ye"][0]),
        ]
    )
    return out


def load_grid_file(path: Path) -> np.ndarray:
    """Load the shipped Sobol grid file -> (N, 3) [logT, logRho, ye]."""
    arr = np.loadtxt(path)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError(f"unexpected grid file shape {arr.shape} in {path}")
    return arr


def match_rows_to_grid(
    states: np.ndarray, grid: np.ndarray, tol: float = 1e-4
) -> tuple[np.ndarray, np.ndarray]:
    """Nearest-neighbour match of empirical states onto the Sobol grid.

    Both inputs are (N, 3) in [logT, logRho, ye]; matching happens in
    box-normalized coordinates.  Returns (grid_index_per_row, distance).
    Rows further than ``tol`` from any grid point get index -1.
    """
    from scipy.spatial import cKDTree

    tree = cKDTree(normalize_states(grid[:, 0], grid[:, 1], grid[:, 2]))
    q = normalize_states(states[:, 0], states[:, 1], states[:, 2])
    dist, idx = tree.query(q, k=1)
    idx = np.asarray(idx)
    idx[dist > tol] = -1
    return idx, np.asarray(dist)
