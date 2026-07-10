"""Vectorized chugunov_2007 screening, mirroring pynucastro term-for-term.

pynucastro's ``chugunov_2007`` / ``PlasmaState`` / ``smooth_clip``
(pynucastro/screening/screen.py, 2.12.0) are numba jitclass/scalar-only; this
module reimplements the identical arithmetic over numpy state vectors so the
compiled evaluator can screen every reaction at every state in one pass.
Validated against the scalar functions to ≤ 1e-12 in tests/test_flux_compile.py.

Conventions (same as pynucastro):
- functions return **ln(screening factor)** (log_scor), not the factor;
- per-rate screening = Σ log_scor over the rate's ``screening_pairs``
  (pynucastro's own pair construction, including composite intermediates for
  ≥3-reactant rates — NOTE this pair construction differs from MESA
  net_screen's neutron-swap two-stage rule on some multi-body channels; the
  Step-4 screening cross-check bounded the per-factor MESA↔pyna difference at
  ≤ 0.0021 dex, and multi-body channels are pp-chain territory, negligible in
  the Si-burning box).
"""

from __future__ import annotations

import numpy as np
from pynucastro.constants import constants

__all__ = ["plasma_arrays", "smooth_clip_vec", "chugunov_2007_vec"]


def plasma_arrays(
    rho: np.ndarray, Y: np.ndarray, Z: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Per-state electron density and Γₑ prefactor (PlasmaState fields).

    Parameters
    ----------
    rho : (n_states,) density [g/cm³]
    Y   : (n_species, n_states) molar fractions
    Z   : (n_species,) proton numbers

    Returns
    -------
    (n_e, gamma_e_fac) : each (n_states,)
        ``n_e = ρ · ΣᵢZᵢYᵢ / m_u`` (PlasmaState: zbar·ntot after cancelling),
        ``gamma_e_fac = q_e²/k · (4π/3)^⅓ · n_e^⅓``.
    """
    zy = Z @ Y  # (n_states,)
    n_e = rho * zy / constants.m_u_C18
    gamma_e_fac = (
        constants.q_e**2 / constants.k * np.cbrt(4 * np.pi / 3) * np.cbrt(n_e)
    )
    return n_e, gamma_e_fac


def smooth_clip_vec(x: np.ndarray, limit: float, start: float) -> np.ndarray:
    """Vectorized pynucastro ``smooth_clip`` (half-cosine transition)."""
    if limit < start:
        lower, upper = np.full_like(x, limit), x
    else:
        lower, upper = x, np.full_like(x, limit)
    lo, hi = min(limit, start), max(limit, start)
    tmp = np.pi * (x - lo) / (start - limit)
    f = (1 - np.cos(tmp)) / 2
    mid = (1 - f) * lower + f * upper
    return np.where(x < lo, lower, np.where(x > hi, upper, mid))


def chugunov_2007_vec(
    temp: np.ndarray,
    n_e: np.ndarray,
    gamma_e_fac: np.ndarray,
    z1: np.ndarray,
    a1: np.ndarray,
    z2: np.ndarray,
    a2: np.ndarray,
) -> np.ndarray:
    """ln(screening factor) for every (pair, state).

    Parameters
    ----------
    temp, n_e, gamma_e_fac : (n_states,)
    z1, a1, z2, a2 : (n_pairs,) — pair charges/masses (composites included)

    Returns
    -------
    (n_pairs, n_states) float64 log_scor ≥ 0
    """
    temp = np.asarray(temp, dtype=np.float64)[None, :]
    n_e = np.asarray(n_e, dtype=np.float64)[None, :]
    gamma_e_fac = np.asarray(gamma_e_fac, dtype=np.float64)[None, :]
    z1 = np.asarray(z1, dtype=np.float64)[:, None]
    a1 = np.asarray(a1, dtype=np.float64)[:, None]
    z2 = np.asarray(z2, dtype=np.float64)[:, None]
    a2 = np.asarray(a2, dtype=np.float64)[:, None]

    ztilde = 0.5 * (np.cbrt(z1) + np.cbrt(z2))

    mu12 = a1 * a2 / (a1 + a2)
    z_factor = z1 * z2
    n_i = n_e / ztilde**3
    m_i = 2 * mu12 * constants.m_u_C18

    T_p = (
        constants.hbar
        / constants.k
        * constants.q_e
        * np.sqrt(4 * np.pi * z_factor * n_i / m_i)
    )
    T_norm = temp / T_p
    T_norm = smooth_clip_vec(T_norm, limit=0.1, start=0.2)

    Gamma = gamma_e_fac * z1 * z2 / (ztilde * T_norm * T_p)
    Gamma = smooth_clip_vec(Gamma, limit=600.0, start=590.0)

    zeta = np.cbrt(4 / (3 * np.pi**2 * T_norm**2))

    fit_alpha = 0.022
    fit_beta = 0.41 - 0.6 / Gamma
    fit_gamma = 0.06 + 2.2 / Gamma
    poly = 1 + zeta * (fit_alpha + zeta * (fit_beta + fit_gamma * zeta))
    gamtilde = Gamma / np.cbrt(poly)

    A1 = 2.7822
    A2 = 98.34
    A3 = np.sqrt(3) - A1 / np.sqrt(A2)
    B1 = -1.7476
    B2 = 66.07
    B3 = 1.12
    B4 = 65
    gamtilde2 = gamtilde**2

    term1 = 1 / np.sqrt(A2 + gamtilde)
    term2 = 1 / (1 + gamtilde)
    term3 = gamtilde**2 / (B2 + gamtilde)
    term4 = gamtilde2 / (B4 + gamtilde2)

    h = gamtilde ** (3 / 2) * (A1 * term1 + A3 * term2) + B1 * term3 + B3 * term4
    return np.maximum(h, 0.0)
