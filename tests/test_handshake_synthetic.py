"""Handshake machinery on manufactured labels: exact linear labels must give
100% agreement; true-exponential stiff cells must depart in a τ-tracking way;
a corrupted channel must surface in the outlier attribution."""

from __future__ import annotations

import numpy as np
import pytest

from gnn_nucleo.fluxes.handshake import (
    agreement_by_bin,
    agreement_by_stiffness,
    attribute_outliers,
    build_cells,
)

DT = 1.011e-6


@pytest.fixture
def synth():
    """Small synthetic system: 6 species, 4 reactions, 500 states with a
    spread of destruction timescales around dt."""
    rng = np.random.default_rng(11)
    n_species, n_states = 6, 500
    A = np.array([1.0, 4.0, 12.0, 16.0, 28.0, 56.0])
    X = rng.dirichlet(np.ones(n_species), size=n_states)
    X = np.maximum(X, 1e-8)
    X /= X.sum(axis=1, keepdims=True)
    Y = X / A

    # per-state per-species decay rates spanning τ/dt from 1e-3 to 1e6
    tau = DT * 10 ** rng.uniform(-3, 6, (n_states, n_species))
    ydot = -(Y / tau).T  # (n_species, n_states), pure destruction
    return A, X, Y, ydot, tau


class TestExactLinearLabels:
    def test_full_agreement(self, synth):
        A, X, Y, ydot, tau = synth
        X_fin = X + (A[None, :] * ydot.T * DT)
        cells = build_cells(ydot, X, np.maximum(X_fin, 1e-15), A, DT)
        lin = cells.linearizable
        assert lin.sum() > 1000
        assert cells.agree[lin].all()

    def test_agreement_with_label_noise(self, synth):
        A, X, Y, ydot, tau = synth
        rng = np.random.default_rng(12)
        noise = 1e-11 * X * rng.standard_normal(X.shape)
        X_fin = np.maximum(X + (A[None, :] * ydot.T * DT) + noise, 1e-15)
        cells = build_cells(ydot, X, X_fin, A, DT)
        # calibration must pick the injected noise up
        assert 1e-11 < cells.eps_lab < 1e-9
        lin = cells.linearizable
        assert cells.agree[lin].mean() > 0.999


class TestStiffDepartures:
    def test_exponential_labels_depart_where_stiff(self, synth):
        A, X, Y, ydot, tau = synth
        # true solution of dY/dt = -Y/τ over dt: ΔX = X(e^{-dt/τ} - 1)
        X_fin = np.maximum(X * np.exp(-DT / tau), 1e-15)
        cells = build_cells(ydot, X, X_fin, A, DT)
        rows = agreement_by_stiffness(cells)
        fracs = [r["fraction"] for r in rows if r["n_cells"] > 0]
        # agreement must rise monotonically with τ/dt and be ~1 at the top
        assert fracs[-1] > 0.999
        assert fracs[0] < 0.2
        assert all(b >= a - 0.02 for a, b in zip(fracs[:-1], fracs[1:]))
        # and the τ>10dt verdict must still be excellent (linearization error
        # ≤ (dt/τ)/2 ≤ 5% < REL_TOL at the boundary)
        assert cells.agree[cells.linearizable].mean() > 0.999

    def test_censoring_at_floor(self, synth):
        A, X, Y, ydot, tau = synth
        X_fin = np.maximum(X + (A[None, :] * ydot.T * DT), 1e-15)
        X_fin[:, 0] = 1e-15  # species 0 clamped everywhere
        cells = build_cells(ydot, X, X_fin, A, DT)
        assert cells.censored[:, 0].all()
        assert not cells.linearizable[:, 0].any()


class TestOutlierAttribution:
    def test_corrupted_channel_surfaces(self, synth):
        A, X, Y, ydot, tau = synth
        n_states = X.shape[0]
        # 4 reactions; reaction 2 exclusively feeds species 3
        nu = np.zeros((6, 4))
        nu[0, 0] = -1
        nu[1, 0] = 1
        nu[2, 1] = -1
        nu[4, 1] = 1
        nu[3, 2] = 1
        nu[5, 2] = -1
        nu[1, 3] = -1
        nu[2, 3] = 1
        f_plus = np.abs(np.random.default_rng(13).normal(1, 0.1, (4, n_states)))
        f_plus[2] *= 100.0  # channel 2 dominates species 3

        # labels exact except species 3 corrupted where slow (an un-stiff lie)
        X_fin = X + (A[None, :] * ydot.T * DT)
        slow3 = tau[:, 3] > 100 * DT
        X_fin[slow3, 3] *= 1.001
        cells = build_cells(ydot, X, np.maximum(X_fin, 1e-15), A, DT)
        out = attribute_outliers(
            cells, nu, f_plus, ("r0", "r1", "r_bad", "r3")
        )
        assert out, "no outliers found"
        assert out[0]["channel"] == "r_bad"

    def test_bins(self, synth):
        A, X, Y, ydot, tau = synth
        X_fin = np.maximum(X + (A[None, :] * ydot.T * DT), 1e-15)
        cells = build_cells(ydot, X, X_fin, A, DT)
        bins = np.zeros(X.shape[0], dtype=int)
        bins[250:] = 1
        rows = agreement_by_bin(cells, bins, 2)
        assert rows[0]["n_states"] == 250 and rows[1]["n_states"] == 250
        assert all(r["fraction"] > 0.999 for r in rows)
