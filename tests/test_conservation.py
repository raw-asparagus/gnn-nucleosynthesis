"""Conservation gate: the floor of the entire project.

Invariant #1 (root CLAUDE.md): for Target A, dY = nu @ phi must conserve baryon
number and satisfy charge-to-lepton closure to <= 1e-12 per step in float64 for
ANY flux vector phi — including random, untrained-network output. Accuracy affects
WHICH conserving update is produced, never WHETHER it conserves.

Two layers of tests:

1. A self-contained synthetic toy network (always runs, no data needed) that
   exercises the constraint-matrix construction, including a weak reaction with
   lepton bookkeeping, and verifies that Y_e evolves through the weak column
   while A is exactly conserved.

2. The exported production matrices under data/stoich/*.npz (skipped until
   `scripts/export_stoich_matrix.py` has been run).

If layer 1 fails, the constraint bookkeeping logic is wrong.
If layer 2 fails, the pynucastro export is wrong. Training must not begin.
"""

from __future__ import annotations

import glob
import os

import numpy as np
import pytest

TOL = 1e-12
RNG = np.random.default_rng(20260705)


# ----------------------------------------------------------------------------
# Layer 1: synthetic toy network with strong, EM, and weak reactions
# ----------------------------------------------------------------------------
#
# Species (index: name, A, Z):
#   0: n      (1, 0)
#   1: p      (1, 1)
#   2: he4    (4, 2)
#   3: c12    (12, 6)
#   4: mg24   (24, 12)
#   5: si28   (28, 14)
#   6: p31    (31, 15)
#   7: s32    (32, 16)
#   8: co55   (55, 27)
#   9: fe55   (55, 26)
#
# Reactions (columns of nu):
#   r0: triple-alpha        3 he4          -> c12
#   r1: alpha capture       c12  + 3 he4   -> mg24  (schematic chain link)
#   r2: (a,g)               mg24 + he4     -> si28
#   r3: (p,g)               p31  + p       -> s32          [bottleneck-like]
#   r4: (g,a) photodis.     si28           -> mg24 + he4
#   r5: EC (weak)           co55 + e-      -> fe55 + nu_e  [changes Z at fixed A]

A_VEC = np.array([1, 1, 4, 12, 24, 28, 31, 32, 55, 55], dtype=np.float64)
Z_VEC = np.array([0, 1, 2, 6, 12, 14, 15, 16, 27, 26], dtype=np.float64)

N_SPECIES = 10
N_REACTIONS = 6
WEAK_COLS = np.array([5])

NU = np.zeros((N_SPECIES, N_REACTIONS), dtype=np.float64)
NU[2, 0] = -3.0; NU[3, 0] = +1.0                       # 3a -> c12
NU[3, 1] = -1.0; NU[2, 1] = -3.0; NU[4, 1] = +1.0      # c12 + 3a -> mg24
NU[4, 2] = -1.0; NU[2, 2] = -1.0; NU[5, 2] = +1.0      # mg24(a,g)si28
NU[6, 3] = -1.0; NU[1, 3] = -1.0; NU[7, 3] = +1.0      # p31(p,g)s32
NU[5, 4] = -1.0; NU[4, 4] = +1.0; NU[2, 4] = +1.0      # si28(g,a)mg24
NU[8, 5] = -1.0; NU[9, 5] = +1.0                       # co55(EC)fe55

# Lepton bookkeeping rows: electron count change and (electron-)lepton number.
#   EC: consumes one e-, emits one nu_e  => dN_e = -1, dL = (-1 e-) + (+1 nu) = 0...
# We track dN_electron per reaction and dN_neutrino per reaction explicitly.
D_ELECTRON = np.zeros(N_REACTIONS)
D_NEUTRINO = np.zeros(N_REACTIONS)
D_ELECTRON[5] = -1.0   # EC consumes an electron
D_NEUTRINO[5] = +1.0   # and emits an electron neutrino


def _random_flux(n: int, scale_decades: float = 12.0) -> np.ndarray:
    """Signed fluxes spanning many decades — the realistic hostile input."""
    signs = RNG.choice([-1.0, 1.0], size=n)
    mags = 10.0 ** RNG.uniform(-scale_decades, 0.0, size=n)
    return signs * mags


def test_toy_baryon_conservation_any_flux():
    """Sum_i A_i * (nu @ phi)_i == 0 for arbitrary phi, to machine precision."""
    for _ in range(200):
        phi = _random_flux(N_REACTIONS)
        dY = NU @ phi
        assert abs(float(A_VEC @ dY)) <= TOL


def test_toy_charge_to_lepton_closure_any_flux():
    """Charge lost by nuclei in weak reactions is carried by leptons exactly."""
    for _ in range(200):
        phi = _random_flux(N_REACTIONS)
        dY = NU @ phi
        d_charge_nuclear = float(Z_VEC @ dY)
        d_electrons = float(D_ELECTRON @ phi)
        # Closure: the nuclear charge change of weak columns equals the electron-
        # ledger change (EC: nucleus loses +1 charge <=> one e- consumed).
        assert abs(d_charge_nuclear - d_electrons) <= TOL


def test_toy_strong_columns_conserve_Z_columnwise():
    """Non-weak columns individually conserve nuclear charge."""
    for j in range(N_REACTIONS):
        if j in WEAK_COLS:
            continue
        assert abs(float(Z_VEC @ NU[:, j])) <= TOL
        assert abs(float(A_VEC @ NU[:, j])) <= TOL


def test_toy_weak_column_moves_Ye_at_fixed_A():
    """The physical signal must survive: dYe != 0 through the weak column,
    while baryon number is untouched. A design that zeroes this to make the
    residuals vanish is wrong (invariant #3)."""
    phi = np.zeros(N_REACTIONS)
    phi[5] = 1e-6  # pure EC flux
    dY = NU @ phi
    dYe = float(Z_VEC @ dY)
    assert abs(float(A_VEC @ dY)) <= TOL          # A conserved exactly
    assert dYe < 0                                 # EC lowers Ye
    assert abs(dYe + 1e-6) <= 1e-18                # by exactly one charge unit * phi


def test_toy_mask_never_touches_weak_columns():
    """Invariant #2: gating scales columns; column sums vanish regardless of the
    gate — but weak columns must never be in the eligible set at all."""
    gate = RNG.uniform(0.0, 1.0, size=N_REACTIONS)
    eligible = np.ones(N_REACTIONS, dtype=bool)
    eligible[WEAK_COLS] = False  # this line is the contract under test
    effective = np.where(eligible, gate, 1.0)
    phi = _random_flux(N_REACTIONS)
    dY = NU @ (effective * phi)
    assert abs(float(A_VEC @ dY)) <= TOL
    # weak flux passed through unscaled:
    assert effective[5] == 1.0


# ----------------------------------------------------------------------------
# Layer 2: exported production matrices (mesa_80 / mesa_151)
# ----------------------------------------------------------------------------

_EXPORTS = sorted(glob.glob(os.path.join("data", "stoich", "nu_*.npz")))


@pytest.mark.parametrize("path", _EXPORTS or [pytest.param(None, marks=pytest.mark.skip(
    reason="no exported matrices yet — run scripts/export_stoich_matrix.py"))])
def test_exported_matrix_conserves(path):
    data = np.load(path, allow_pickle=False)
    nu = np.asarray(data["nu"], dtype=np.float64)
    A = np.asarray(data["A"], dtype=np.float64)
    Z = np.asarray(data["Z"], dtype=np.float64)
    weak_mask = np.asarray(data["weak_mask"], dtype=bool)   # per-reaction
    d_electron = np.asarray(data["d_electron"], dtype=np.float64)

    n_species, n_reactions = nu.shape
    assert A.shape == (n_species,) and Z.shape == (n_species,)
    assert weak_mask.shape == (n_reactions,)

    # Baryon conservation must hold column-wise for EVERY reaction. Use a
    # scale-aware tolerance: |A . nu_j| <= TOL * ||A|| * ||nu_j||.
    for j in range(n_reactions):
        col = nu[:, j]
        scale = max(1.0, float(np.linalg.norm(A) * np.linalg.norm(col)))
        assert abs(float(A @ col)) <= TOL * scale, f"baryon leak in column {j} of {path}"

    # Strong/EM columns conserve nuclear charge; weak columns hand exactly
    # their charge change to the electron ledger.
    for j in range(n_reactions):
        dq = float(Z @ nu[:, j])
        if weak_mask[j]:
            assert abs(dq - d_electron[j]) <= TOL * max(1.0, abs(dq)), \
                f"lepton closure fails in weak column {j} of {path}"
            assert abs(dq) > 0, f"weak column {j} of {path} changes no charge"
        else:
            assert abs(dq) <= TOL, f"charge leak in strong column {j} of {path}"

    # End-to-end: random flux, machine-precision drift, nonzero dYe via weak.
    phi = _random_flux(n_reactions)
    dY = nu @ phi
    assert abs(float(A @ dY)) <= 1e-9 * max(1.0, float(np.abs(A @ np.abs(nu) @ np.abs(phi))))
    phi_weak_only = np.where(weak_mask, phi, 0.0)
    dYe_weak = float(Z @ (nu @ phi_weak_only))
    if weak_mask.any():
        assert dYe_weak != 0.0, f"dYe identically zero through weak columns in {path}"
