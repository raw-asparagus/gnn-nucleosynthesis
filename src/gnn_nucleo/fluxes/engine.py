"""Batched flux evaluation: λ, gross rates, f⁺/f⁻/φ/κ over state vectors.

All arithmetic mirrors pynucastro 2.12.0 term-for-term (validated to ≤1e-12
against the scalar paths in tests/test_flux_compile.py):

- ReacLib/Derived sets: λ = Σ_sets exp(a·[1, T9⁻¹, T9⁻⅓, T9⅓, T9, T9^5/3, lnT9]),
  with the DerivedRate pf correction and chugunov_2007 screening added inside
  the exponent (applied here as a factor after the set sum — algebraically
  identical, fp-equal to ~1 ulp);
- tabular weak: bilinear in (log10 ρYₑ, log10 T), clamped-searchsorted;
- gross rate R_j = prefactor_j · ρ^{densexp_j} · Πᵣ Y_r · λ_j (rate.eval_full_rate).

Pair semantics (column j): f⁺_j = R_j; f⁻_j = R_{pair(j)} (0 if unpaired,
ALWAYS 0 for weak columns); φ_j = f⁺_j − f⁻_j; κ_j = |φ_j|/(f⁺_j + f⁻_j)
(κ ≡ 1 for weak columns with flux — they are never "equilibrated" in the mask
sense, CLAUDE.md invariant #2). The physical RHS is ydot = ν·R, which equals
Σ_{j ∈ forward ∪ unpaired} ν_ij φ_j exactly (tests/test_flux_engine.py).

Everything float64. Callers chunk over states for memory (the run scripts use
O(4k)-state chunks); this module evaluates one batch densely.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .compile import CompiledNetwork
from .screening import chugunov_2007_vec, plasma_arrays

__all__ = ["FluxBatch", "evaluate_lambda", "evaluate_fluxes"]


@dataclass(frozen=True)
class FluxBatch:
    """Per-reaction fluxes for one batch of states. Shapes (n_rxn, n_states)
    except ydot (n_species, n_states) and dye_weak (n_states,)."""

    f_plus: np.ndarray
    f_minus: np.ndarray
    phi: np.ndarray
    kappa: np.ndarray
    ydot: np.ndarray
    dye_weak: np.ndarray


def _bilinear_vec(
    rhoy: np.ndarray,
    temp: np.ndarray,
    f2d: np.ndarray,
    logrhoy: np.ndarray,
    logT: np.ndarray,
) -> np.ndarray:
    """Vectorized TableInterpolator.interpolate (identical arithmetic)."""
    if np.any(logT < temp.min()) or np.any(logT > temp.max()):
        raise ValueError("temperature out of table bounds")
    if np.any(logrhoy < rhoy.min()) or np.any(logrhoy > rhoy.max()):
        raise ValueError("rhoy out of table bounds")

    i = np.maximum(0, np.minimum(len(rhoy) - 1, np.searchsorted(rhoy, logrhoy)) - 1)
    j = np.maximum(0, np.minimum(len(temp) - 1, np.searchsorted(temp, logT)) - 1)

    dlogrho = rhoy[i + 1] - rhoy[i]
    dlogT = temp[j + 1] - temp[j]

    f_ij = f2d[i, j]
    f_ip1j = f2d[i + 1, j]
    f_ijp1 = f2d[i, j + 1]
    f_ip1jp1 = f2d[i + 1, j + 1]

    D = f_ij
    C = (f_ijp1 - f_ij) / dlogT
    B = (f_ip1j - f_ij) / dlogrho
    A = (f_ip1jp1 - B * dlogrho - C * dlogT - D) / (dlogrho * dlogT)

    return (
        A * (logrhoy - rhoy[i]) * (logT - temp[j])
        + B * (logrhoy - rhoy[i])
        + C * (logT - temp[j])
        + D
    )


def evaluate_lambda(
    cn: CompiledNetwork, T: np.ndarray, rho: np.ndarray, Y: np.ndarray
) -> np.ndarray:
    """Per-reaction λ (screened, pf-corrected) for a batch of states.

    Parameters
    ----------
    T   : (n_states,) temperature [K]
    rho : (n_states,) density [g/cm³]
    Y   : (n_species, n_states) molar fractions (needed for ρYₑ of tabular
          rates and for the screening plasma state)

    Returns
    -------
    (n_reactions, n_states) float64
    """
    T = np.atleast_1d(np.asarray(T, dtype=np.float64))
    rho = np.atleast_1d(np.asarray(rho, dtype=np.float64))
    Y = np.asarray(Y, dtype=np.float64)
    n_states = T.size
    if rho.shape != (n_states,) or Y.shape != (cn.stoich.n_species, n_states):
        raise ValueError("state array shapes inconsistent")

    # T factors — expressions mirror pynucastro Tfactors exactly
    T9 = T / 1.0e9
    T9i = 1.0 / T9
    Tpow = np.stack(
        [
            np.ones_like(T9),
            T9i,
            T9i ** (1.0 / 3.0),
            T9 ** (1.0 / 3.0),
            T9,
            T9 ** (5.0 / 3.0),
            np.log(T9),
        ]
    )  # (7, n_states)

    lam = np.zeros((cn.n_reactions, n_states), dtype=np.float64)
    if cn.coeffs.size:
        log_sets = cn.coeffs @ Tpow  # (n_sets, n_states)
        lam[cn.owned_cols] = np.add.reduceat(np.exp(log_sets), cn.set_starts, axis=0)

        corr = None
        if cn.pf_matrix.nnz:
            log_pf = np.empty((len(cn.pf_splines), n_states), dtype=np.float64)
            for m, spl in enumerate(cn.pf_splines):
                log_pf[m] = spl(T9)
            corr = cn.pf_matrix @ log_pf
        if cn.screening is not None and cn.screen_map.nnz:
            n_e, gamma_e_fac = plasma_arrays(rho, Y, cn.stoich.Z)
            log_scor = chugunov_2007_vec(
                T,
                n_e,
                gamma_e_fac,
                cn.screen_pairs[:, 0],
                cn.screen_pairs[:, 1],
                cn.screen_pairs[:, 2],
                cn.screen_pairs[:, 3],
            )
            sc = cn.screen_map @ log_scor
            corr = sc if corr is None else corr + sc
        if corr is not None:
            lam *= np.exp(corr)

    if len(cn.tab_cols):
        ye = (cn.stoich.Z @ Y) / (cn.stoich.A @ Y)
        logrhoy = np.log10(rho * ye)
        logT = np.log10(T)
        for i, col in enumerate(cn.tab_cols):
            r = _bilinear_vec(
                cn.tab_rhoy[i], cn.tab_temp[i], cn.tab_rate2d[i], logrhoy, logT
            )
            lam[col] = 10.0**r

    return lam


def evaluate_fluxes(
    cn: CompiledNetwork, T: np.ndarray, rho: np.ndarray, Y: np.ndarray
) -> FluxBatch:
    """Gross/net per-reaction fluxes for a batch of states (see module doc)."""
    T = np.atleast_1d(np.asarray(T, dtype=np.float64))
    rho = np.atleast_1d(np.asarray(rho, dtype=np.float64))
    Y = np.asarray(Y, dtype=np.float64)
    n_states = T.size

    lam = evaluate_lambda(cn, T, rho, Y)

    R = lam * cn.prefactor[:, None] * rho[None, :] ** cn.dens_exp[:, None]
    if cn.ye_weighted.any():
        # REACLIB EC fits carry ρYₑ: dens_exp already has the extra ρ,
        # multiply by Yₑ (pyna Composition.ye ≡ ΣZᵢYᵢ / ΣAᵢYᵢ)
        ye = (cn.stoich.Z @ Y) / (cn.stoich.A @ Y)
        R[cn.ye_weighted] *= ye[None, :]
    Ypad = np.vstack([Y, np.ones((1, n_states), dtype=np.float64)])
    for k in range(cn.reactant_idx.shape[1]):
        R *= Ypad[cn.reactant_idx[:, k]]

    f_plus = R
    f_minus = np.zeros_like(R)
    paired = cn.pair_col >= 0
    f_minus[paired] = R[cn.pair_col[paired]]

    phi = f_plus - f_minus
    denom = f_plus + f_minus
    with np.errstate(invalid="ignore", divide="ignore"):
        kappa = np.where(denom > 0.0, np.abs(phi) / np.where(denom > 0.0, denom, 1.0), 0.0)

    ydot = cn.stoich.nu @ R

    zeta = cn.stoich.Z @ cn.stoich.nu  # ΣᵢZᵢν_ij per column
    w = cn.stoich.weak_mask
    dye_weak = zeta[w] @ R[w]

    return FluxBatch(
        f_plus=f_plus,
        f_minus=f_minus,
        phi=phi,
        kappa=kappa,
        ydot=ydot,
        dye_weak=dye_weak,
    )
