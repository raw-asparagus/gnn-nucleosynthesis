"""Target B null-space projector P = I − Cᵀ(CCᵀ)⁻¹C.

Fixed linear operator projecting a raw network output dY onto the
constraint manifold C·dY = 0 (baryon, charge-to-lepton, lepton number).

VALID IN A LINEAR OUTPUT SPACE ONLY. P may never be applied downstream of a
log / signed-log / asinh transform: a sum constraint evaluated in a warped
space conserves nothing in the physical space (the documented NuGNN failure
mode; root CLAUDE.md invariant #4). Conservation lives in the decode step.

P acts on the EXTENDED species vector [dY_nuclei…, dY_e⁻, dY_ν, dY_ν̄]
(length n+3): the charge row of C couples nuclei to the electron column, so
projecting a nuclei-only vector with a nuclei-only C would force ΣZ·dY = 0
and erase the weak dYₑ signal (invariant #3). Callers hand P the extended
vector and read the nuclear part back out.

Implementation: QR null-space form. With C = QR (Qᵀ Q = I, Q spanning
row-space(C)), P = I − QQᵀ — algebraically equal to I − Cᵀ(CCᵀ)⁻¹C for
full-row-rank C but with better symmetry/idempotence in float64 than the
normal-equations form. C here is 3 × (n+3) with cond(CCᵀ) ~ 1e3, so either
form works; QR is the one we ship.
"""

from __future__ import annotations

import numpy as np


def build_projector(C: np.ndarray) -> np.ndarray:
    """Orthogonal projector onto null(C), float64, shape (m, m) for C (k, m).

    Requires full row rank (the physical C has rank 3: baryon, charge,
    lepton rows are independent).
    """
    C = np.asarray(C, dtype=np.float64)
    if C.ndim != 2 or C.shape[0] >= C.shape[1]:
        raise ValueError(f"C must be wide (k constraints × m species), got {C.shape}")
    Q, R = np.linalg.qr(C.T)  # reduced QR: Q is (m, k)
    if np.abs(np.diag(R)).min() <= 1e-12 * np.abs(np.diag(R)).max():
        raise ValueError("C is rank-deficient — constraint rows are not independent")
    m = C.shape[1]
    return np.eye(m, dtype=np.float64) - Q @ Q.T


def project(P: np.ndarray, dY: np.ndarray) -> np.ndarray:
    """Apply the projector: returns P @ dY (float64, linear space only)."""
    return np.asarray(P, dtype=np.float64) @ np.asarray(dY, dtype=np.float64)
