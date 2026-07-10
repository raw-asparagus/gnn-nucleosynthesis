"""Equilibrium-deviation diagnostics: δ (Guidry), r_QSE, reaction eligibility.

CLAUDE.md invariant #2 is structural here: the eligible set for any
equilibrium mask NEVER contains weak columns — ``eligible_mask`` takes
``weak_mask`` and excludes it by construction, not by convention.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

__all__ = [
    "delta_species",
    "r_qse",
    "reaction_delta",
    "eligible_mask",
    "load_group_mask",
]

_REPO = Path(__file__).resolve().parents[3]


def delta_species(Y: np.ndarray, Y_ref: np.ndarray) -> np.ndarray:
    """Guidry departure δᵢ = |Yᵢ − Ȳᵢ| / Ȳᵢ (ε sweep {3e-3, 1e-2, 3e-2})."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(Y_ref > 0, np.abs(Y - Y_ref) / Y_ref, np.inf)


def r_qse(Y: np.ndarray, Y_ref: np.ndarray, floor: float = 1e-30) -> np.ndarray:
    """r_QSE = log10(Ȳ/Y) per species — plateaus by group when the group is
    internally equilibrated (operational QSE signature)."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.log10(np.maximum(Y_ref, floor) / np.maximum(Y, floor))


def reaction_delta(nu: np.ndarray, delta: np.ndarray) -> np.ndarray:
    """δ_r per reaction column = max δᵢ over participating species."""
    part = nu != 0.0  # (n_species, n_rxn)
    d = np.where(np.isfinite(delta), delta, np.inf)
    out = np.full(nu.shape[1], 0.0)
    for j in range(nu.shape[1]):
        out[j] = d[part[:, j]].max() if part[:, j].any() else np.inf
    return out


def eligible_mask(
    delta_r: np.ndarray, weak_mask: np.ndarray, epsilon: float
) -> np.ndarray:
    """Columns eligible for equilibrium masking: δ_r < ε AND structurally
    never weak (invariant #2 — β/EC are not in detailed balance here)."""
    return (delta_r < epsilon) & ~np.asarray(weak_mask, dtype=bool)


def load_group_mask(network: str, variant: str = "default") -> np.ndarray:
    """Silicon-group membership from configs/qse_groups.yaml → (n,) bool."""
    from gnn_nucleo.graph import load_isotope_table

    doc = yaml.safe_load((_REPO / "configs" / "qse_groups.yaml").read_text())
    rule = doc["variants"][variant]
    table = load_isotope_table(network)
    A = table.A.astype(int)
    mask = (A >= rule["a_min"]) & (A < rule.get("a_max", 10**9))
    if rule.get("exclude_light", True):
        mask &= table.Z.astype(int) > 2
    names = list(table.names)
    if "si28" in names and not mask[names.index("si28")]:
        raise ValueError(f"{network}: group variant {variant!r} excludes si28")
    return mask
