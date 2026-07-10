"""Stratified Step-5 subsample over the training grid (persisted state_ids).

The Sobol training grid is NON-REGENERABLE (CLAUDE.md): everything keyed to
states persists explicit state_id lists in configs/, never a re-samplable
recipe. This module draws the ~30k-state stratified subsample over
(T9, logρ, Yₑ_init) with the QSE window T9 ∈ [3.3, 5.0) overweighted ×2, and
selects ~20 constant-(T,ρ) test trajectories per network on a 5×4
(logT, logρ) grid.

Stratum edges (sourced: regime box + kill-test grid, crosscheck/grids.py):
T9 [1.6, 2.5, 3.3, 4.0, 5.0, 6.3, 7.95] × logρ [7, 7.667, 8.333, 9.001]
× Yₑ [0.45, 0.4667, 0.4833, 0.5001] → 54 strata.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

__all__ = [
    "T9_EDGES",
    "LOGRHO_EDGES",
    "YE_EDGES",
    "stratified_sample",
    "compute_ye_initial",
    "select_trajectories",
    "subsample_ids_path",
    "load_subsample_ids",
]

T9_EDGES = np.array([1.6, 2.5, 3.3, 4.0, 5.0, 6.3, 7.95])
LOGRHO_EDGES = np.array([7.0, 7.667, 8.333, 9.001])
YE_EDGES = np.array([0.45, 0.4667, 0.4833, 0.5001])
#: T9 bins receiving double weight (QSE window [3.3, 5.0))
OVERWEIGHT_T9_BINS = (2, 3)
OVERWEIGHT_FACTOR = 2.0

_REPO = Path(__file__).resolve().parents[3]


def subsample_ids_path(network: str) -> Path:
    return _REPO / "configs" / f"step5_subsample_{network}_ids.json"


def load_subsample_ids(network: str) -> np.ndarray:
    doc = json.loads(subsample_ids_path(network).read_text())
    return np.asarray(doc["state_ids"], dtype=np.int64)


def compute_ye_initial(X: np.ndarray, Z: np.ndarray, A: np.ndarray) -> np.ndarray:
    """Yₑ = Σᵢ Zᵢ Xᵢ / Aᵢ per state (X rows = states)."""
    return X @ (Z / A)


def _bin_index(
    t9: np.ndarray, logrho: np.ndarray, ye: np.ndarray
) -> tuple[np.ndarray, int]:
    """Flat stratum index per state; −1 where outside all edges."""
    bt = np.digitize(t9, T9_EDGES) - 1
    br = np.digitize(logrho, LOGRHO_EDGES) - 1
    by = np.digitize(ye, YE_EDGES) - 1
    nt, nr, ny = len(T9_EDGES) - 1, len(LOGRHO_EDGES) - 1, len(YE_EDGES) - 1
    ok = (bt >= 0) & (bt < nt) & (br >= 0) & (br < nr) & (by >= 0) & (by < ny)
    flat = np.where(ok, (bt * nr + br) * ny + by, -1)
    return flat, nt * nr * ny


def stratified_sample(
    t9: np.ndarray,
    logrho: np.ndarray,
    ye: np.ndarray,
    n_target: int = 30_000,
    seed: int = 20260710,
) -> tuple[np.ndarray, dict]:
    """Draw ≈n_target state indices stratified over the 54-stratum grid.

    Per-stratum quota ∝ weight (×2 for the QSE-window T9 bins), capped at the
    stratum population with iterative proportional redistribution of the
    shortfall. Sampling within a stratum is uniform without replacement,
    ``numpy.random.default_rng(seed)``.

    Returns (sorted state indices, spec dict with quotas/achieved counts).
    """
    flat, n_strata = _bin_index(t9, logrho, ye)
    nr, ny = len(LOGRHO_EDGES) - 1, len(YE_EDGES) - 1
    weights = np.ones(n_strata)
    for bt in OVERWEIGHT_T9_BINS:
        weights[bt * nr * ny : (bt + 1) * nr * ny] = OVERWEIGHT_FACTOR

    pops = np.bincount(flat[flat >= 0], minlength=n_strata)
    quotas = np.zeros(n_strata, dtype=np.int64)
    remaining_w = weights.copy()
    remaining_n = n_target
    # iterative fill: strata smaller than their proportional share are taken
    # whole and the leftover re-spread over the rest
    for _ in range(n_strata):
        open_ = (quotas < pops) & (remaining_w > 0)
        if not open_.any() or remaining_n <= 0:
            break
        share = remaining_n * remaining_w / remaining_w[open_].sum()
        want = np.minimum(pops, quotas + np.where(open_, share, 0).astype(np.int64))
        newly = want - quotas
        if newly.sum() == 0:
            # distribute the last few one by one to the largest open strata
            order = np.argsort(-(pops - quotas))
            for s in order:
                if remaining_n <= 0:
                    break
                if quotas[s] < pops[s] and open_[s]:
                    quotas[s] += 1
                    remaining_n -= 1
            break
        quotas = want
        remaining_n = n_target - quotas.sum()
        remaining_w = np.where(quotas >= pops, 0.0, weights)

    rng = np.random.default_rng(seed)
    picked: list[np.ndarray] = []
    for s in range(n_strata):
        if quotas[s] == 0:
            continue
        members = np.nonzero(flat == s)[0]
        if quotas[s] >= len(members):
            picked.append(members)
        else:
            picked.append(rng.choice(members, size=int(quotas[s]), replace=False))
    ids = np.sort(np.concatenate(picked)) if picked else np.array([], dtype=np.int64)

    spec = {
        "seed": seed,
        "n_target": n_target,
        "n_achieved": int(ids.size),
        "t9_edges": T9_EDGES.tolist(),
        "logrho_edges": LOGRHO_EDGES.tolist(),
        "ye_edges": YE_EDGES.tolist(),
        "overweight_t9_bins": list(OVERWEIGHT_T9_BINS),
        "overweight_factor": OVERWEIGHT_FACTOR,
        "stratum_population": pops.tolist(),
        "stratum_quota": quotas.tolist(),
        "n_outside_strata": int((flat < 0).sum()),
    }
    return ids.astype(np.int64), spec


_TRAJ_RE = re.compile(r"output_T_([0-9.]+)_rho_([0-9.]+)\.txt$")


def select_trajectories(
    files: list[str], n_logt: int = 5, n_logrho: int = 4, seed: int = 20260710
) -> list[str]:
    """Pick one shipped constant-(T,ρ) trajectory per cell of an
    (n_logt × n_logrho) grid over the box — nearest file to each cell center,
    each file used at most once (next-nearest on collision)."""
    coords = []
    for f in files:
        m = _TRAJ_RE.search(f)
        if not m:
            continue
        coords.append((f, float(m.group(1)), float(m.group(2))))
    if not coords:
        return []
    logt_c = np.linspace(9.2, 9.9, n_logt)
    logrho_c = np.linspace(7.0, 9.0, n_logrho)
    # scale distances by box extent so both axes count comparably
    lt = np.array([c[1] for c in coords])
    lr = np.array([c[2] for c in coords])
    chosen: list[str] = []
    used = np.zeros(len(coords), dtype=bool)
    for tc in logt_c:
        for rc in logrho_c:
            d = ((lt - tc) / 0.7) ** 2 + ((lr - rc) / 2.0) ** 2
            d = np.where(used, np.inf, d)
            k = int(np.argmin(d))
            if np.isfinite(d[k]):
                used[k] = True
                chosen.append(coords[k][0])
    return sorted(chosen)
