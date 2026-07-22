"""NSE/QSE coefficient construction C(ᴬZ) — same inputs as pynucastro.

The Saha-form mass fraction at chemical potentials (u_p, u_n) [MeV] is

    X_i = exp( logC_i(T, ρ) + (Z_i·u_p + N_i·u_n) / (k_MeV·T) )

with logC_i = 2.5·ln(A_nuc,i·m_u) + ln(2J_i+1) − ln ρ
            + 1.5·ln(kT / 2πℏ²) + log_pf_i(T) + B_i·A_i / (k_MeV·T),

mirroring pynucastro's ``NSENetwork._nucleon_fraction_nse``
(networks/nse_network.py:214) term-for-term: partition functions from the
same Rauscher tables (rebuilt splines, ext='const'), binding energies from
``Nucleus.nucbind``, masses from ``Nucleus.A_nuc``, spins from
``Nucleus.spin_states``. "Same inputs" makes the cross-check against
pynucastro's solver a genuine independence test of the SOLVER, not the data.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "NseInputs",
    "build_inputs",
    "nse_log_coeffs",
    "nse_log_coeffs_batch",
    "EXP_CLIP",
]

#: pynucastro clips the Saha exponent at 500 (nse_network.py:212)
EXP_CLIP = 500.0


@dataclass(frozen=True)
class NseInputs:
    """Per-nucleus data for the Saha coefficients (network order)."""

    network: str
    names: tuple[str, ...]
    A: np.ndarray  # (n,) mass number (int-valued float)
    Z: np.ndarray  # (n,)
    N: np.ndarray  # (n,)
    A_nuc: np.ndarray  # (n,) actual mass in amu
    spin_states: np.ndarray  # (n,) 2J+1
    nucbind: np.ndarray  # (n,) binding energy per nucleon [MeV]
    pf_splines: tuple  # per nucleus: spline over T9 → log(pf), or None

    @property
    def n(self) -> int:
        return len(self.names)


def build_inputs(network: str) -> NseInputs:
    """Extract the pynucastro nuclear data for the network's isotopes."""
    from scipy.interpolate import InterpolatedUnivariateSpline

    from gnn_nucleo.graph import load_isotope_table

    table = load_isotope_table(network)
    nuclei = list(table.nuclei)
    splines = []
    for nuc in nuclei:
        pf = nuc.partition_function
        if pf is None:
            splines.append(None)
        else:
            splines.append(
                InterpolatedUnivariateSpline(
                    pf.T9_points, pf.log_pf_data, k=pf.interpolant_order, ext="const"
                )
            )
        if not nuc.spin_states:
            raise ValueError(f"{network}: {nuc} has no spin_states — NSE undefined")
    return NseInputs(
        network=network,
        names=table.names,
        A=np.array([float(n.A) for n in nuclei]),
        Z=np.array([float(n.Z) for n in nuclei]),
        N=np.array([float(n.N) for n in nuclei]),
        A_nuc=np.array([float(n.A_nuc) for n in nuclei]),
        spin_states=np.array([float(n.spin_states) for n in nuclei]),
        nucbind=np.array([float(n.nucbind) for n in nuclei]),
        pf_splines=tuple(splines),
    )


def nse_log_coeffs(inputs: NseInputs, T: float, rho: float) -> np.ndarray:
    """logC_i(T, ρ) per species (see module docstring). float64 (n,).

    Thin scalar wrapper over :func:`nse_log_coeffs_batch` (one shared code
    path — no drift between the scalar and batched solvers).
    """
    return nse_log_coeffs_batch(
        inputs, np.atleast_1d(np.float64(T)), np.atleast_1d(np.float64(rho))
    )[0]


def nse_log_coeffs_batch(
    inputs: NseInputs, T: np.ndarray, rho: np.ndarray
) -> np.ndarray:
    """Vectorized :func:`nse_log_coeffs` over states.

    ``T``, ``rho`` are ``(M,)`` [K, g/cm³] → ``(M, n)`` float64, one row per
    state in network species order. Same term-for-term arithmetic as the
    scalar form; only the state axis is added (broadcast), so the pynucastro
    cross-check tolerance (tests/test_qse_coeffs.py, ≤1e-12) carries over.
    """
    from pynucastro.constants import constants

    T = np.asarray(T, dtype=np.float64).ravel()
    rho = np.asarray(rho, dtype=np.float64).ravel()
    kT_MeV = constants.k_MeV * T  # (M,)
    T9 = T / 1.0e9  # (M,)
    log_pf = np.zeros((T.shape[0], inputs.n), dtype=np.float64)  # (M, n)
    for m, s in enumerate(inputs.pf_splines):
        if s is not None:
            log_pf[:, m] = s(T9)
    species = 2.5 * np.log(inputs.A_nuc * constants.m_u_C18) + np.log(
        inputs.spin_states
    )  # (n,)
    bind = inputs.nucbind * inputs.A  # (n,)
    state = -np.log(rho) + 1.5 * np.log(
        constants.k * T / (2.0 * np.pi * constants.hbar**2)
    )  # (M,)
    return (
        species[None, :]
        + state[:, None]
        + log_pf
        + bind[None, :] / kT_MeV[:, None]
    )
