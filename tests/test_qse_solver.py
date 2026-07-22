"""Independent NSE/QSE solvers: cross-check vs pynucastro's NSE solver
(shared inputs ⇒ near-exact agreement expected), QSE→NSE degeneracy, and the
structural weak-column exclusion of the eligible mask."""

from __future__ import annotations

import warnings

import numpy as np
import pytest


@pytest.fixture(scope="module")
def inputs80():
    from gnn_nucleo.qse.coeffs import build_inputs

    return build_inputs("mesa_80")


class TestNSECrossCheck:
    @pytest.mark.parametrize(
        "t9,rho,ye",
        [(5.0, 1e8, 0.48), (6.3, 1e9, 0.45), (7.9, 1e7, 0.498)],
    )
    def test_matches_pyna_solver(self, inputs80, t9, rho, ye):
        from gnn_nucleo.crosscheck.kappa import nse_composition
        from gnn_nucleo.graph import load_isotope_table
        from gnn_nucleo.qse.solver import solve_nse

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            comp, ok = nse_composition("mesa_80", t9, rho, ye)
        assert ok
        res = solve_nse(inputs80, t9 * 1e9, rho, ye)
        assert res.converged, f"solver failed: {res}"
        nuclei = list(load_isotope_table("mesa_80").nuclei)
        ref = np.array([comp.X[n] for n in nuclei])
        ours = res.X
        m = ref > 1e-10
        dlog = np.abs(np.log10(ours[m]) - np.log10(ref[m]))
        assert dlog.max() <= 1e-6, f"max |dlog10 X| = {dlog.max():.3e}"

    def test_constraints_satisfied(self, inputs80):
        from gnn_nucleo.qse.solver import solve_nse

        res = solve_nse(inputs80, 5e9, 1e8, 0.47)
        assert res.converged
        assert abs(res.X.sum() - 1.0) < 1e-10
        ye = ((inputs80.Z / inputs80.A) * res.X).sum()
        assert abs(ye - 0.47) < 1e-10

    def test_low_t9_converges_but_flagged_regime(self, inputs80):
        # T9 < 3 solutions are computed (converge) but are non-physical for
        # gating (QSE onset ~3-3.3 GK) — the solver must still behave
        from gnn_nucleo.qse.solver import solve_nse

        res = solve_nse(inputs80, 2.0e9, 1e8, 0.48)
        assert res.converged


class TestQSE:
    def test_degenerates_to_nse_when_group_mass_is_nse(self, inputs80):
        """With group_mass set to the NSE group mass, u_group → 0 and the
        QSE composition equals NSE."""
        from gnn_nucleo.qse.diagnostics import load_group_mask
        from gnn_nucleo.qse.solver import solve_nse, solve_qse

        T, rho, ye = 5e9, 1e8, 0.48
        nse = solve_nse(inputs80, T, rho, ye)
        g = load_group_mask("mesa_80")
        gm = float(nse.X[g].sum())
        qse = solve_qse(inputs80, T, rho, ye, g, gm)
        assert qse.converged
        assert abs(qse.u_group) < 1e-6
        np.testing.assert_allclose(qse.X, nse.X, rtol=1e-6)

    def test_offset_group_mass_moves_u_group(self, inputs80):
        from gnn_nucleo.qse.diagnostics import load_group_mask
        from gnn_nucleo.qse.solver import solve_nse, solve_qse

        T, rho, ye = 4.0e9, 1e8, 0.48
        nse = solve_nse(inputs80, T, rho, ye)
        g = load_group_mask("mesa_80")
        gm = float(nse.X[g].sum())
        qse = solve_qse(inputs80, T, rho, ye, g, min(0.9, gm * 2.0))
        assert qse.converged
        assert qse.u_group != 0.0
        assert abs(qse.X[g].sum() - min(0.9, gm * 2.0)) < 1e-9
        # constraints still hold
        assert abs(qse.X.sum() - 1.0) < 1e-9

    def test_group_mask_contains_si28_not_light(self):
        from gnn_nucleo.graph import load_isotope_table
        from gnn_nucleo.qse.diagnostics import load_group_mask

        table = load_isotope_table("mesa_80")
        names = list(table.names)
        g = load_group_mask("mesa_80")
        assert g[names.index("si28")]
        for light in ("neut", "h1", "he4"):
            assert not g[names.index(light)]


class TestBatchedSolvers:
    """The batched entry points must reproduce a per-state scalar loop: the
    vectorized Newton handles the well-conditioned majority, and any row it
    fails to converge is delegated to the proven scalar solver (Newton retry +
    bisection). Grid spans the full regime box incl. cold T9 (bisection path)."""

    def _grid(self):
        from gnn_nucleo.crosscheck.grids import state_grid

        grid = state_grid()  # full 63-state box (incl. cold T9 → fallback)
        T = np.array([t9 * 1e9 for t9, _, _ in grid])
        rho = np.array([r for _, r, _ in grid])
        ye = np.array([y for _, _, y in grid])
        return T, rho, ye

    def test_nse_batch_matches_scalar_loop(self, inputs80):
        from gnn_nucleo.qse.solver import solve_nse, solve_nse_batch

        T, rho, ye = self._grid()
        scal = [solve_nse(inputs80, T[i], rho[i], ye[i]) for i in range(T.size)]
        bat = solve_nse_batch(inputs80, T, rho, ye)

        assert np.array_equal(
            np.array([s.converged for s in scal]), bat.converged
        )
        assert bat.converged.all(), "every box state must converge"
        # both newton and bisection-fallback rows are exercised on this grid
        assert set(bat.method.tolist()) == {"newton", "bisection"}
        for i, s in enumerate(scal):
            m = (s.X > 1e-10) & (bat.X[i] > 1e-10)
            dlog = np.abs(np.log10(bat.X[i][m]) - np.log10(s.X[m]))
            assert dlog.max() <= 1e-6, f"state {i}: max |dlog10 X| {dlog.max():.2e}"
            assert abs(bat.u_p[i] - s.u_p) <= 1e-6
            assert abs(bat.u_n[i] - s.u_n) <= 1e-6
        # .row() accessor yields a scalar-equivalent NSEResult
        r0 = bat.row(0)
        assert r0.converged == bool(bat.converged[0])
        np.testing.assert_array_equal(r0.X, bat.X[0])

    def test_qse_batch_matches_scalar_loop(self, inputs80):
        from gnn_nucleo.crosscheck.grids import state_grid
        from gnn_nucleo.qse.diagnostics import load_group_mask
        from gnn_nucleo.qse.solver import solve_nse, solve_qse, solve_qse_batch

        # NSE-guaranteed subgrid (QSE seeded from NSE); group_mass from NSE
        grid = state_grid((5.0, 6.3, 7.9))
        T = np.array([t9 * 1e9 for t9, _, _ in grid])
        rho = np.array([r for _, r, _ in grid])
        ye = np.array([y for _, _, y in grid])
        g = load_group_mask("mesa_80")
        gm = np.array(
            [solve_nse(inputs80, T[i], rho[i], ye[i]).X[g].sum() for i in range(T.size)]
        )
        scal = [
            solve_qse(inputs80, T[i], rho[i], ye[i], g, gm[i]) for i in range(T.size)
        ]
        bat = solve_qse_batch(inputs80, T, rho, ye, g, gm)
        assert np.array_equal(np.array([s.converged for s in scal]), bat.converged)
        for i, s in enumerate(scal):
            m = (s.X > 1e-10) & (bat.X[i] > 1e-10)
            assert np.abs(np.log10(bat.X[i][m]) - np.log10(s.X[m])).max() <= 1e-6
            assert abs(bat.u_group[i] - s.u_group) <= 1e-6

    def test_qse_batch_degenerates_to_nse(self, inputs80):
        """group_mass = NSE group mass ⇒ u_group → 0 and X → NSE, per row."""
        from gnn_nucleo.qse.diagnostics import load_group_mask
        from gnn_nucleo.qse.solver import solve_nse_batch, solve_qse_batch

        T, rho, ye = self._grid()
        keep = T / 1e9 >= 5.0  # NSE-guaranteed
        T, rho, ye = T[keep], rho[keep], ye[keep]
        g = load_group_mask("mesa_80")
        nse = solve_nse_batch(inputs80, T, rho, ye)
        gm = nse.X[:, g].sum(1)
        qse = solve_qse_batch(inputs80, T, rho, ye, g, gm)
        assert qse.converged.all()
        assert np.abs(qse.u_group).max() < 1e-6
        np.testing.assert_allclose(qse.X, nse.X, rtol=1e-6)

    def test_qse_batch_rejects_bad_group_mass(self, inputs80):
        from gnn_nucleo.qse.diagnostics import load_group_mask
        from gnn_nucleo.qse.solver import solve_qse_batch

        g = load_group_mask("mesa_80")
        with pytest.raises(ValueError):
            solve_qse_batch(
                inputs80,
                np.array([5e9, 6e9]),
                np.array([1e8, 1e8]),
                np.array([0.48, 0.48]),
                g,
                np.array([0.5, 1.5]),  # second is out of (0, 1)
            )


class TestEligibleMask:
    def test_weak_columns_structurally_excluded(self):
        from gnn_nucleo.qse.diagnostics import eligible_mask

        delta_r = np.zeros(6)  # everything "equilibrated"
        weak = np.array([False, True, False, True, False, False])
        m = eligible_mask(delta_r, weak, epsilon=1e-2)
        assert not m[weak].any()
        assert m[~weak].all()

    def test_delta_and_r_qse(self):
        from gnn_nucleo.qse.diagnostics import delta_species, r_qse

        Y = np.array([1.0, 2.0, 0.5])
        Yr = np.array([1.0, 1.0, 1.0])
        np.testing.assert_allclose(delta_species(Y, Yr), [0.0, 1.0, 0.5])
        np.testing.assert_allclose(r_qse(Y, Yr), [0.0, -np.log10(2.0), np.log10(2.0)])

    def test_reaction_delta_max_over_participants(self):
        from gnn_nucleo.qse.diagnostics import reaction_delta

        nu = np.array([[-1.0, 0.0], [1.0, -1.0], [0.0, 1.0]])
        delta = np.array([0.1, 0.01, 0.5])
        np.testing.assert_allclose(reaction_delta(nu, delta), [0.1, 0.5])
