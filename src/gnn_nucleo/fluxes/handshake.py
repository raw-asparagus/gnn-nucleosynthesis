"""dt = 1e-6 s label handshake: engine fluxes vs shipped bbq labels.

Premise: at the shortest measured timestep dt₁ (≈1.011e-6 / 1.009e-6 s), the
label step is linear wherever the state is not stiff on dt₁:
ΔXᵢ ≈ Aᵢ·(νR)ᵢ·dt₁. This ties OUR fluxes to THEIR solver output with no
model in between (flux-side analogue of the Step-2 model handshake).

Interpretation contract (Step-5 brief): the linearization legitimately fails
where the per-isotope destruction timescale τᵢ = Yᵢ/|Ẏᵢ| ≲ dt (fast (γ,n)/
(n,γ) at high T9). Agreement is therefore judged on cells with τ > 10·dt,
and the DEPARTURE must track τ/dt — that tracking is itself evidence the
fluxes are right. Cells failing WITHOUT a stiffness explanation indicate a
configuration mismatch and are attributed to their dominant reaction channel.

Tolerance: |ΔX_pred − ΔX_lab| ≤ max(REL_TOL·|ΔX_lab|, 3·ε_lab·(Xᵢ+X_f), ABS_FLOOR)
- REL_TOL = 0.1: the linearization error itself is O(dt/τ) ≤ 10% at τ = 10·dt;
- ε_lab: EMPIRICAL per-unit-X label noise (robust 10×median), calibrated on
  ultra-slow cells (τ > 1e3·dt) where ΔX_pred ≈ 0 — labels are float64-printed
  but carry bbq solver tolerance; we measure it instead of assuming float32;
- ABS_FLOOR = 2e-15: below the 1e-15 label clamp resolution.
Cells with final_X at the 1e-15 floor are censored (excluded).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "REL_TOL",
    "ABS_FLOOR",
    "HandshakeCells",
    "build_cells",
    "calibrate_label_noise",
    "agreement_by_bin",
    "attribute_outliers",
]

REL_TOL = 0.1
ABS_FLOOR = 2e-15
FINAL_FLOOR = 1e-15
STATIC_TAU_FACTOR = 1e3  # τ/dt above which a cell is calibration-grade static
LINEAR_TAU_FACTOR = 10.0  # τ/dt above which the linearization must hold


RHS_STABLE_FACTOR = 0.2  # |ẏ_end − ẏ_start| ≤ this × |ẏ_start| for stability
GROSS_REL_TOL = 0.05  # rate-level (gross-relative) agreement threshold


@dataclass
class HandshakeCells:
    """Per-(state, isotope) handshake quantities (arrays (n_states, n_species))."""

    dX_pred: np.ndarray
    dX_lab: np.ndarray
    resid: np.ndarray
    tau_over_dt: np.ndarray
    censored: np.ndarray  # final at label floor
    linearizable: np.ndarray  # τ > 10·dt, RHS-stable (if known), not censored
    tol: np.ndarray
    agree: np.ndarray
    eps_lab: float  # calibrated per-unit-X label noise (robust 10×median)
    #: |resid| / (A·gross·dt) — rate-level residual, immune to net-flux
    #: cancellation amplification; None when gross was not supplied
    resid_gross: np.ndarray | None = None
    #: per-isotope cancellation |Σⱼνᵢⱼφⱼ| / Σⱼ|νᵢⱼφⱼ|; None w/o gross
    cancellation: np.ndarray | None = None


def build_cells(
    ydot: np.ndarray,
    X_init: np.ndarray,
    X_fin: np.ndarray,
    A: np.ndarray,
    dt: float | np.ndarray,
    ydot_end: np.ndarray | None = None,
    gross: np.ndarray | None = None,
) -> HandshakeCells:
    """Assemble handshake cells.

    Parameters
    ----------
    ydot   : (n_species, n_states) engine molar RHS ν·R at the initial state
    X_init : (n_states, n_species) label initial mass fractions
    X_fin  : (n_states, n_species) label final mass fractions (floored 1e-15)
    A      : (n_species,) mass numbers
    dt     : step length [s] — scalar (training grid dt₁) or (n_states,)
             (trajectory output intervals)
    ydot_end : optional engine RHS at the END state. When given, the
        prediction is TRAPEZOID (½(ẏ₀+ẏ₁)·dt — kills the 2nd-order midpoint
        error, measured 10× on the trajectory residual median), and cells
        whose RHS changed by more than RHS_STABLE_FACTOR over the interval
        are excluded from ``linearizable`` (cascade-production class: a
        species whose reactants appear mid-interval has ẏ 0 → nonzero).
    gross : optional (n_species, n_states) per-species gross molar turnover
        Σⱼ|νᵢⱼ|Rⱼ at the initial state. Enables ``resid_gross`` (the
        rate-level residual: net-flux errors are amplified by 1/cancellation,
        so the NET tolerance alone cannot separate flux errors from QSE
        cancellation) and ``cancellation``.
    """
    dt_col = np.broadcast_to(
        np.atleast_1d(np.asarray(dt, dtype=np.float64))[:, None]
        if np.ndim(dt)
        else np.float64(dt),
        (X_init.shape[0], 1),
    )
    y_pred = ydot if ydot_end is None else 0.5 * (ydot + ydot_end)
    dX_pred = (A[:, None] * y_pred).T * dt_col  # (n_states, n_species)
    dX_lab = X_fin - X_init
    resid = dX_pred - dX_lab

    Y = X_init / A[None, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        tau = np.where(np.abs(ydot.T) > 0, Y / np.abs(ydot.T), np.inf)
    tau_over_dt = tau / dt_col

    # censor at the training-label floor on BOTH ends: final_* is clamped at
    # 1e-15 upstream, and trajectory files print bbq internals down to 1e-99
    # — sub-floor abundances are invisible to the emulator's labels
    censored = (X_fin <= FINAL_FLOOR) | (X_init <= FINAL_FLOOR)
    eps_lab = calibrate_label_noise(resid, X_init, X_fin, tau_over_dt, censored)

    linearizable = (tau_over_dt > LINEAR_TAU_FACTOR) & ~censored
    if ydot_end is not None:
        y0, y1 = ydot.T, ydot_end.T
        stable = np.where(
            y0 != 0.0, np.abs(y1 - y0) <= RHS_STABLE_FACTOR * np.abs(y0), y1 == 0.0
        )
        linearizable &= stable
    tol = np.maximum(
        REL_TOL * np.abs(dX_lab),
        np.maximum(3.0 * eps_lab * (X_init + X_fin), ABS_FLOOR),
    )
    agree = np.abs(resid) <= tol

    resid_gross = cancellation = None
    if gross is not None:
        gross_dX = (A[:, None] * gross).T * dt_col
        with np.errstate(divide="ignore", invalid="ignore"):
            resid_gross = np.abs(resid) / np.maximum(gross_dX, 1e-300)
            cancellation = np.abs(y_pred.T) / np.maximum(gross.T, 1e-300)

    return HandshakeCells(
        dX_pred=dX_pred,
        dX_lab=dX_lab,
        resid=resid,
        tau_over_dt=tau_over_dt,
        censored=censored,
        linearizable=linearizable,
        tol=tol,
        agree=agree,
        eps_lab=eps_lab,
        resid_gross=resid_gross,
        cancellation=cancellation,
    )


def calibrate_label_noise(
    resid: np.ndarray,
    X_init: np.ndarray,
    X_fin: np.ndarray,
    tau_over_dt: np.ndarray,
    censored: np.ndarray,
) -> float:
    """Empirical per-unit-X label noise: 10 × median of |resid|/(Xᵢ+X_f)
    over ultra-slow uncensored cells with meaningful abundance (X > 1e-10).

    Median (not p99): the calibration set must be ROBUST to a genuinely
    corrupted channel — a tail statistic would let bad cells inflate the
    noise floor and mask themselves (caught by
    tests/test_handshake_synthetic.py::test_corrupted_channel_surfaces).
    The ×10 covers the median→tail ratio of a heavy-tailed noise floor
    (Gaussian p99/median ≈ 3.8) with margin."""
    static = (tau_over_dt > STATIC_TAU_FACTOR) & ~censored & (X_init > 1e-10)
    if not static.any():
        return 0.0
    s = np.abs(resid[static]) / (X_init[static] + X_fin[static])
    return float(10.0 * np.median(s))


def agreement_by_bin(
    cells: HandshakeCells, bin_index: np.ndarray, n_bins: int
) -> list[dict]:
    """Agreement fraction over linearizable cells, per state-level bin
    (e.g. T9 stratum). bin_index: (n_states,) ints, −1 = unbinned."""
    rows = []
    for b in range(n_bins):
        in_bin = bin_index == b
        cell_mask = cells.linearizable & in_bin[:, None]
        n = int(cell_mask.sum())
        n_agree = int((cells.agree & cell_mask).sum())
        rows.append(
            {
                "bin": b,
                "n_states": int(in_bin.sum()),
                "n_cells": n,
                "n_agree": n_agree,
                "fraction": n_agree / n if n else np.nan,
                "n_censored": int((cells.censored & in_bin[:, None]).sum()),
            }
        )
    return rows


def agreement_by_stiffness(cells: HandshakeCells) -> list[dict]:
    """Agreement fraction by τ/dt decade over UNCENSORED cells — must rise
    with τ/dt if departures are stiffness-explained."""
    edges = [0.0, 0.1, 1.0, 10.0, 100.0, 1e3, np.inf]
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (cells.tau_over_dt >= lo) & (cells.tau_over_dt < hi) & ~cells.censored
        n = int(m.sum())
        rows.append(
            {
                "tau_over_dt": f"[{lo:g}, {hi:g})",
                "n_cells": n,
                "fraction": float((cells.agree & m).sum() / n) if n else np.nan,
            }
        )
    return rows


def attribute_outliers(
    cells: HandshakeCells,
    nu: np.ndarray,
    f_plus: np.ndarray,
    rate_fnames: tuple[str, ...],
    top_n: int = 30,
    bad_mask: np.ndarray | None = None,
) -> list[dict]:
    """For every bad cell (default: linearizable-but-disagreeing; pass
    ``bad_mask`` for e.g. rate-level failures resid_gross > GROSS_REL_TOL),
    attribute to the reaction with the largest |ν_ij·R_j| for that
    isotope/state; aggregate per channel.

    nu: (n_species, n_rxn); f_plus: (n_rxn, n_states).
    """
    bad = (
        bad_mask if bad_mask is not None else cells.linearizable & ~cells.agree
    )
    states, species = np.nonzero(bad.T.T)  # (n_states, n_species) order
    counts: dict[int, int] = {}
    worst: dict[int, float] = {}
    for s, i in zip(states, species):
        contrib = np.abs(nu[i, :] * f_plus[:, s])
        j = int(np.argmax(contrib))
        counts[j] = counts.get(j, 0) + 1
        rel = float(
            np.abs(cells.resid[s, i]) / max(np.abs(cells.dX_lab[s, i]), 1e-300)
        )
        worst[j] = max(worst.get(j, 0.0), rel)
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])[:top_n]
    return [
        {
            "channel": rate_fnames[j],
            "column": j,
            "n_cells": c,
            "worst_rel_resid": worst[j],
        }
        for j, c in ranked
    ]
