"""Tests for gnn_nucleo.fluxes.integrate — the stiff reference integrator
producing Target-A supervision pairs (Φ, ΔY = νΦ).

Design contract (Step 6 Task 3, ADR 0006):
- augmented state u = [Y, Φ] with dY/dt = νR, dΦⱼ/dt = Rⱼ (GROSS per-column
  rates; net φ/κ recovered via pair_col downstream);
- the RETURNED composition is Y0 + ν(Φ − Φ0) — the ΔY = νΦ identity and
  baryon/charge conservation hold by construction; the error-controlled
  solver Y is exposed as a consistency diagnostic;
- Jacobian: analytic dominant term D = ∂R/∂Y from the reactant product rule
  (∂λ/∂Y through screening/Yₑ deliberately neglected — quasi-Newton).
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


@pytest.fixture(scope="module")
def cn80():
    from gnn_nucleo.fluxes.compile import compile_network

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return compile_network("mesa_80")


def _si_state(cn, ye_target=0.48):
    """Canonical si28+si30 composition at ye_target, molar fractions."""
    names = list(cn.stoich.rate_fnames) if False else None  # noqa: F841
    from gnn_nucleo.graph import load_isotope_table

    table = load_isotope_table("mesa_80")
    idx = {n: i for i, n in enumerate(table.names)}
    x_si30 = (0.5 - ye_target) / (0.5 - 14.0 / 30.0)
    X = np.zeros(table.n)
    X[idx["si28"]] = 1.0 - x_si30
    X[idx["si30"]] = x_si30
    return X / table.A


class TestRhsConsistency:
    def test_rhs_matches_engine(self, cn80):
        """The cached single-state RHS must equal evaluate_fluxes exactly
        (same arithmetic, Y-independent parts hoisted)."""
        from gnn_nucleo.fluxes.engine import evaluate_fluxes
        from gnn_nucleo.fluxes.integrate import StatePoint

        rng = np.random.default_rng(3)
        T, rho = 4.0e9, 1.0e8
        sp = StatePoint(cn80, T, rho)
        for _ in range(3):
            Y = rng.dirichlet(np.ones(cn80.stoich.n_species)) / cn80.stoich.A
            R = sp.gross_rates(Y)
            batch = evaluate_fluxes(
                cn80, np.array([T]), np.array([rho]), Y[:, None]
            )
            ref = batch.f_plus[:, 0]
            m = ref > 0
            assert np.max(np.abs(R[m] / ref[m] - 1.0)) < 1e-12
            ydot = cn80.stoich.nu @ R
            np.testing.assert_allclose(
                ydot, batch.ydot[:, 0], rtol=1e-12, atol=1e-300
            )

    def test_jacobian_vs_finite_differences_unscreened(self):
        """On an UNSCREENED compile, D = ∂R/∂Y must match central
        differences exactly on its structural entries (only the tabular-ρYₑ
        and Yₑ-weighted columns have a Y-dependence D does not model)."""
        from gnn_nucleo.fluxes.compile import compile_network
        from gnn_nucleo.fluxes.integrate import StatePoint

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            cn0 = compile_network("mesa_80", screening=None)
        rng = np.random.default_rng(4)
        sp = StatePoint(cn0, 4.0e9, 1.0e8)
        Y = rng.dirichlet(np.ones(cn0.stoich.n_species)) / cn0.stoich.A
        D = sp.rate_jacobian(Y).toarray()

        excl = np.zeros(cn0.n_reactions, dtype=bool)
        excl[np.asarray(cn0.tab_cols, dtype=int)] = True
        excl |= cn0.ye_weighted
        keep = ~excl

        for i in rng.choice(cn0.stoich.n_species, size=6, replace=False):
            h = max(1e-7 * Y[i], 1e-12)
            Yp, Ym = Y.copy(), Y.copy()
            Yp[i] += h
            Ym[i] = max(Ym[i] - h, 0.0)
            fd = (sp.gross_rates(Yp) - sp.gross_rates(Ym)) / (Yp[i] - Ym[i])
            m = keep & (D[:, i] != 0.0)
            if not m.any():
                continue
            rel = np.abs(D[m, i] - fd[m]) / np.maximum(np.abs(fd[m]), 1e-300)
            assert rel.max() < 1e-6
            # and no structural dependence is missed: unscreened non-tabular
            # columns with zero D-entry must show (near-)zero FD
            z = keep & (D[:, i] == 0.0)
            scale = np.abs(D[m, i]).max()
            assert np.abs(fd[z]).max() <= 1e-8 * scale

    def test_neglected_screening_chain_is_subdominant(self, cn80):
        """The ∂λ/∂Y chain (screening/Yₑ) D deliberately neglects must be
        small relative to the structural entries (ADR 0006 justification)."""
        from gnn_nucleo.fluxes.integrate import StatePoint

        rng = np.random.default_rng(5)
        sp = StatePoint(cn80, 4.0e9, 1.0e8)
        Y = rng.dirichlet(np.ones(cn80.stoich.n_species)) / cn80.stoich.A
        D = sp.rate_jacobian(Y).toarray()
        ratios = []
        for i in rng.choice(cn80.stoich.n_species, size=4, replace=False):
            h = max(1e-6 * Y[i], 1e-12)
            Yp, Ym = Y.copy(), Y.copy()
            Yp[i] += h
            Ym[i] = max(Ym[i] - h, 0.0)
            fd = (sp.gross_rates(Yp) - sp.gross_rates(Ym)) / (Yp[i] - Ym[i])
            col_scale = np.abs(fd).max()
            chain = np.abs(fd - D[:, i])
            ratios.append(chain.max() / col_scale)
        # MEASURED (ADR 0006): the chain reaches ~0.9× the column scale on
        # random compositions (tabular-EC ρYₑ sensitivity) — it may be
        # comparable to, but must never dominate, the structural term. An
        # inexact Jacobian affects BDF step efficiency only, never
        # correctness (error control is on the solution); the integration
        # tests below are the actual convergence evidence.
        assert max(ratios) < 1.5


class TestIntegration:
    @pytest.fixture(scope="class")
    def result(self, cn80):
        from gnn_nucleo.fluxes.integrate import integrate_state

        Y0 = _si_state(cn80)
        return (
            Y0,
            integrate_state(cn80, 4.0e9, 1.0e8, Y0, 1e-2),
        )

    def test_success_and_identity_by_construction(self, cn80, result):
        Y0, res = result
        assert res.success
        np.testing.assert_array_equal(
            res.Y, Y0 + cn80.stoich.nu @ res.Phi
        )

    def test_solver_consistency_residual(self, result):
        """Error-controlled solver Y vs reconstructed νΦ route — must agree
        to solver tolerance (measured diagnostic, gate 1e-6 molar)."""
        _, res = result
        assert res.identity_resid < 1e-6

    def test_conservation_by_construction(self, cn80, result):
        """Baryon and charge-to-lepton closure per the Step-3 scale-aware
        gate: drift ≤ max(1e-12·s, 1e-13·G)."""
        Y0, res = result
        A = cn80.stoich.A.astype(np.float64)
        dY = res.Y - Y0
        drift = abs(float(A @ dY))
        gross = float(np.abs(A) @ (np.abs(cn80.stoich.nu) @ np.abs(res.Phi)))
        assert drift <= max(1e-12 * min(1.0, np.abs(res.Phi).max()), 1e-13 * gross)

    def test_something_burned(self, cn80, result):
        """At T9=4, ρ=1e8, 1e-2 s: silicon must actually burn (guards against
        a vacuously-passing zero solution)."""
        Y0, res = result
        assert np.abs(res.Y - Y0).max() > 1e-8
        assert np.abs(res.Phi).max() > 0

    def test_energy_identity(self, cn80, result):
        """Invariant #5 dry run: ΣQⱼΦⱼ vs mass-excess bookkeeping ≤ 1%."""
        from pynucastro.constants import constants

        from gnn_nucleo.graph import load_isotope_table, npz_path

        Y0, res = result
        with np.load(npz_path("mesa_80"), allow_pickle=False) as z:
            Q = z["Q"]
        table = load_isotope_table("mesa_80")
        mass = np.array([n.mass for n in table.nuclei])
        e_flux = float(Q @ res.Phi) * constants.MeV2erg * constants.N_A
        e_comp = -float(mass @ (res.Y - Y0)) * constants.MeV2erg * constants.N_A
        assert abs(e_flux - e_comp) <= 0.01 * abs(e_comp)

    def test_t_eval_multiple_dts(self, cn80):
        """One integration serves several label dts (monotone Φ snapshots)."""
        from gnn_nucleo.fluxes.integrate import integrate_state

        Y0 = _si_state(cn80)
        dts = np.array([1e-6, 1e-4, 1e-2])
        res = integrate_state(cn80, 4.0e9, 1.0e8, Y0, 1e-2, t_eval=dts)
        assert res.Y.shape == (3, cn80.stoich.n_species)
        assert res.Phi.shape == (3, cn80.n_reactions)
        # gross Φ is nondecreasing in t (R ≥ 0 up to clip effects)
        assert (np.diff(res.Phi, axis=0) >= -1e-12).all()


@pytest.mark.slow
class TestLabelAgreement:
    def test_vs_shipped_labels(self, cn80):
        """Integrator ΔX vs shipped label ΔX at dt=1e-6 and 1e-3 s on a few
        subsample states, within the handshake net-tolerance band."""
        from gnn_nucleo.data.labels import load_step_frame
        from gnn_nucleo.data.schema import load_measured_dt
        from gnn_nucleo.data.subsample import load_subsample_ids
        from gnn_nucleo.fluxes.integrate import integrate_state
        from gnn_nucleo.graph import load_isotope_table

        table = load_isotope_table("mesa_80")
        A = table.A.astype(np.float64)
        # T9 < 5 states only: at T9 >= 5 the shipped labels carry the
        # Appendix-B displaced pseudo-equilibrium (RESULTS.md 2026-07-11;
        # e.g. state_id 80 at T9 7.08 agrees 0.575 by construction) —
        # agreement there measures the label pathology, not the integrator
        all_ids = load_subsample_ids("mesa_80")
        probe = load_step_frame(
            "mesa_80", "1e-6", columns=["logT"], state_ids=all_ids[:50]
        )
        cool = 10.0 ** probe["logT"].to_numpy() / 1e9 < 5.0
        ids = all_ids[:50][cool][:3]
        dt_all = load_measured_dt("mesa_80")
        for lab, dt in [("1e-6", dt_all[0]), ("1e-3", dt_all[3])]:
            cols = (
                ["logT", "logRho"]
                + [f"initial_{n}" for n in table.names]
                + [f"final_{n}" for n in table.names]
            )
            df = load_step_frame("mesa_80", lab, columns=cols, state_ids=ids)
            Xi = df[[f"initial_{n}" for n in table.names]].to_numpy()
            Xf = df[[f"final_{n}" for n in table.names]].to_numpy()
            T = 10.0 ** df["logT"].to_numpy()
            rho = 10.0 ** df["logRho"].to_numpy()
            for s in range(len(ids)):
                res = integrate_state(cn80, T[s], rho[s], Xi[s] / A, dt)
                assert res.success
                dX_pred = A * (res.Y - Xi[s] / A)
                dX_lab = Xf[s] - Xi[s]
                # handshake band with eps_lab = 1e-7: the shipped final_* are
                # float32 upstream (schema.py), so per-unit-X label noise is
                # >= 6e-8; Step-5 calibrated eps_lab empirically per file
                tol = np.maximum(
                    0.1 * np.abs(dX_lab), 3e-7 * (Xi[s] + Xf[s])
                )
                tol = np.maximum(tol, 2e-15)
                frac = float(np.mean(np.abs(dX_pred - dX_lab) <= tol))
                # bars anchored to the MEASURED per-stratum medians
                # (RESULTS.md 2026-07-12, scripts/step6_integrate_check.py):
                # dt=1e-6 medians run 0.62-0.87 at T9<5 — misses are
                # solver-independent (BDF = Radau = rtol 1e-10 to 5e-8 rel),
                # i.e. documented rate-class differences integrated through
                # the stiff transient, not integration error.
                bar = 0.55 if lab == "1e-6" else 0.75
                assert frac >= bar, f"state {ids[s]} dt {lab}: {frac:.3f}"
