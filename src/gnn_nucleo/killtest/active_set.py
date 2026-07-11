"""Active-set / concentration / churn / timescale primitives (Step 6 Task 2).

Numbers only — pass/fail thresholds live in docs/phase0-checklist.md and the
verdict document, never here. All κ inputs are expected in the UNSCREENED
convention (CLAUDE.md two-κ rule); enforcement happens at the data-loading
layer (distributions/manifold), these primitives are convention-agnostic.
"""

from __future__ import annotations

import numpy as np

from gnn_nucleo.qse.diagnostics import eligible_mask

__all__ = [
    "guidry_masks",
    "cond_s_active",
    "topk_concentration",
    "carried_fractions",
    "mask_churn",
    "timescale_separation",
    "EPS_SWEEP",
]

#: the CLAUDE.md Guidry ε sweep
EPS_SWEEP = (3e-3, 1e-2, 3e-2)


def guidry_masks(
    delta_r: np.ndarray,
    weak_mask: np.ndarray,
    eps: tuple[float, ...] = EPS_SWEEP,
) -> dict[float, np.ndarray]:
    """MASKABLE columns per ε — strictly via qse.diagnostics.eligible_mask,
    so weak columns are excluded structurally (invariant #2). The dynamic
    active set at ε is the complement (~maskable)."""
    return {e: eligible_mask(delta_r, weak_mask, e) for e in eps}


_SVD_RANK_RTOL = 1e-12


def cond_s_active(nu: np.ndarray, active_cols: np.ndarray) -> float:
    """cond of ν restricted to the active columns: ratio of extreme NONZERO
    singular values (rank-revealing, same definition as
    graph/metrics.condition_numbers — the conservation left-null vectors
    A·ν = 0 are structural and excluded by construction). NaN if empty."""
    cols = np.asarray(active_cols, dtype=bool)
    if not cols.any():
        return float("nan")
    s = np.linalg.svd(nu[:, cols], compute_uv=False)
    nz = s[s > _SVD_RANK_RTOL * s[0]]
    return float(nz[0] / nz[-1])


def topk_concentration(
    shares: np.ndarray, k: tuple[int, ...] = (1, 5, 10, 20)
) -> dict[int, float]:
    """Cumulative share of Σ|shares| carried by the top-k entries."""
    s = np.abs(np.asarray(shares, dtype=np.float64))
    tot = s.sum()
    if tot == 0.0:
        return {kk: float("nan") for kk in k}
    c = np.cumsum(np.sort(s)[::-1]) / tot
    return {kk: float(c[min(kk, len(c)) - 1]) for kk in k}


def carried_fractions(
    nu: np.ndarray, phi: np.ndarray, active: np.ndarray
) -> np.ndarray:
    """Per-species fraction of gross net-flux turnover carried by the active
    columns: covᵢ = Σ_{j∈active}|νᵢⱼφⱼ| / Σⱼ|νᵢⱼφⱼ| (NaN where the species
    has zero turnover). ``phi``/``nu`` should be restricted to net columns
    (forward|unpaired) by the caller to avoid double counting pairs."""
    contrib = np.abs(nu * phi[None, :])  # (n_species, n_cols)
    tot = contrib.sum(axis=1)
    act = contrib[:, np.asarray(active, dtype=bool)].sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(tot > 0, act / np.maximum(tot, 1e-300), np.nan)


def mask_churn(masks: np.ndarray) -> dict[str, float]:
    """Membership churn along a trajectory: ``masks`` is (n_steps, n_cols)
    bool. flips_per_step = mean XOR count between consecutive steps;
    churn_fraction normalizes by n_cols."""
    m = np.asarray(masks, dtype=bool)
    if m.shape[0] < 2:
        return {"flips_per_step": float("nan"), "churn_fraction": float("nan")}
    flips = np.logical_xor(m[1:], m[:-1]).sum(axis=1)
    return {
        "flips_per_step": float(flips.mean()),
        "churn_fraction": float(flips.mean() / m.shape[1]),
    }


def timescale_separation(
    f_plus: np.ndarray,
    phi: np.ndarray,
    eq_cols: np.ndarray,
    bottleneck_cols: np.ndarray,
) -> float:
    """Ratio (fastest equilibrated-pair GROSS rate) / (slowest bottleneck
    NET rate) for one state — the measured replacement for the unsourced
    "6–8 orders" working figure. NaN if either set is empty or the
    bottleneck net rates vanish."""
    eq = np.asarray(eq_cols, dtype=bool)
    bn = np.asarray(bottleneck_cols, dtype=bool)
    if not eq.any() or not bn.any():
        return float("nan")
    fast = float(np.max(f_plus[eq]))
    slow = float(np.min(np.abs(phi[bn])))
    if slow <= 0.0:
        return float("nan")
    return fast / slow
