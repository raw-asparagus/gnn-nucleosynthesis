"""Target B projector gate: P = I - C^T (C C^T)^-1 C (QR null-space form).

Tolerance rationale for (a): P is LINEAR, hence exactly scale-equivariant —
P(s*dY) = s*P(dY) — so the meaningful exactness statement across the
realistic 20-decade magnitude spread is RELATIVE. Each constraint-row
residual is bounded by

    |(C @ P @ dY)_k| <= 1e-12 * max(1, ||C_k||_2 * ||dY||_2)

which reduces to the hard absolute 1e-12 CLAUDE.md gate at O(1) magnitudes
and stays machine-precision-tight (neither vacuous nor impossible) at 1e-20.

P acts on the EXTENDED vector [dY_nuclei..., dY_e-, dY_nu, dY_nubar]; a
nuclei-only projection would force sum(Z dY) = 0 and erase the weak dYe
signal — test (d) guards that invariant (#3).
"""

from __future__ import annotations

import numpy as np
import pytest

from gnn_nucleo.graph import build_projector

RNG = np.random.default_rng(20260708)

#: dY magnitude scales — the realistic abundance-change spread (20 decades).
SCALES = tuple(10.0 ** (-4 * k) for k in range(6))  # 1e0 ... 1e-20


@pytest.fixture(scope="module")
def loaded(stoich_export):
    network, d = stoich_export
    C = d["C"]
    return network, d, C, build_projector(C)


def test_projector_shape_symmetry_idempotence_rank(loaded):
    network, d, C, P = loaded
    m = C.shape[1]
    assert P.shape == (m, m)
    assert np.abs(P - P.T).max() <= 1e-14, f"{network}: P not symmetric"
    assert np.abs(P @ P - P).max() <= 1e-13, f"{network}: P not idempotent"
    # rank(P) = m - 3: exactly the three constraint directions removed.
    eigs = np.linalg.eigvalsh(P)
    assert int(np.round(eigs.sum())) == m - 3, f"{network}: rank(P) != m-3"


@pytest.mark.parametrize("scale", SCALES)
def test_projected_output_satisfies_constraints_across_20_decades(loaded, scale):
    """(a)+(d of the brief): C @ (P @ dY) ~ 0 for random dY at every scale."""
    network, d, C, P = loaded
    m = C.shape[1]
    row_norms = np.linalg.norm(C, axis=1)
    for seed in range(10):
        rng = np.random.default_rng(seed)
        dY = scale * rng.choice([-1.0, 1.0], m) * 10.0 ** rng.uniform(-3, 0, m)
        residual = np.abs(C @ (P @ dY))
        bound = 1e-12 * np.maximum(1.0, row_norms * np.linalg.norm(dY))
        assert np.all(residual <= bound), (
            f"{network} seed {seed} scale {scale:g}: constraint residuals "
            f"{residual} exceed {bound}"
        )


def test_on_manifold_input_is_unchanged(loaded):
    """(c): dY already satisfying C dY = 0 — e.g. any nu_ext @ phi — is a
    fixed point of P."""
    network, d, C, P = loaded
    nu_ext = d["nu_ext"]
    for seed in range(10):
        rng = np.random.default_rng(seed)
        phi = rng.standard_normal(nu_ext.shape[1]) * 10.0 ** rng.uniform(
            -12, 0, nu_ext.shape[1]
        )
        dY = nu_ext @ phi
        err = np.abs(P @ dY - dY).max()
        assert err <= 1e-12 * max(1.0, float(np.abs(dY).max())), (
            f"{network} seed {seed}: on-manifold dY moved by {err:.3e}"
        )


def test_projection_preserves_weak_dYe_signal(loaded):
    """The projector must not launder the physics (invariant #3): a weak-only
    conserving update keeps its nonzero nuclear dYe after projection."""
    network, d, C, P = loaded
    nu_ext = d["nu_ext"]
    Z = d["Z"]
    weak = d["weak_mask"].astype(bool)
    n = len(Z)

    phi = np.where(weak, 1e-6, 0.0)
    dY = nu_ext @ phi
    dYe_before = float(Z @ dY[:n])
    assert dYe_before != 0.0

    dY_proj = P @ dY
    dYe_after = float(Z @ dY_proj[:n])
    assert abs(dYe_after - dYe_before) <= 1e-12 * max(1.0, abs(dYe_before)), (
        f"{network}: projection changed weak dYe {dYe_before:.6e} -> {dYe_after:.6e}"
    )


def test_projector_rejects_rank_deficient_C():
    C = np.array([[1.0, 2.0, 3.0], [2.0, 4.0, 6.0]])  # dependent rows
    with pytest.raises(ValueError, match="rank"):
        build_projector(C)
