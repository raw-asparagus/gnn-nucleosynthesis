"""Compiled-evaluator correctness: the vectorized rate evaluation must match
pynucastro's own scalar evaluation to near machine precision (the pyna-internal
consistency oracle), and no pf-free v-flag reverse may survive compilation.

Gates (Step-5 brief / plan):
- per-rate λ (ReacLib forwards, DerivedRate(use_pf=True) reverses, tabular
  weak) vs ``rate.eval`` : |rel| ≤ 5e-12 where λ > 0. The bound sits just
  above the measured fp-association floor (~1.3e-12): the compiled path bakes
  the DB correction into the set coefficients (pynucastro's own derived_sets
  construction) while rate.eval adds the identical terms at runtime — with
  |Q/kT| ~ O(500) in the exponent, association differences reach ~1e-12 rel;
- vectorized chugunov_2007 vs pynucastro scalar calls : |rel| ≤ 1e-12;
- compiled set tensor contains zero v-flag sets (PfGateError otherwise).
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest

# regime-box probe states (T9, rho, ye): corners + QSE window + NSE anchor
STATES = [
    (1.6, 1e7, 0.45),
    (1.6, 1e9, 0.50),
    (3.3, 1e8, 0.48),
    (4.0, 1e8, 0.465),
    (5.0, 1e7, 0.498),
    (7.9, 1e9, 0.45),
]


@pytest.fixture(scope="session", params=["mesa_80", "mesa_151"])
def compiled(request):
    from gnn_nucleo.fluxes.compile import compile_network

    with warnings.catch_warnings():
        # DerivedRate warns per missing-pf nucleus; the compile records them
        warnings.simplefilter("ignore", UserWarning)
        return compile_network(request.param, screening="chugunov_2007")


@pytest.fixture(scope="session")
def box_compositions(compiled):
    """Deterministic strictly-positive compositions over the network species."""
    rng = np.random.default_rng(20260710)
    n = compiled.stoich.n_species
    X = rng.dirichlet(np.full(n, 0.5), size=len(STATES)).T  # (n_species, n_states)
    X = np.maximum(X, 1e-12)
    X /= X.sum(axis=0)
    return X


def _pyna_composition(compiled, X_col):
    import pynucastro as pyna

    from gnn_nucleo.graph import load_isotope_table

    table = load_isotope_table(compiled.network)
    comp = pyna.Composition(list(table.nuclei))
    comp.set_array(np.asarray(X_col, dtype=np.float64))
    return comp


class TestPfGateAtCompile:
    def test_no_vflag_sets_survive(self, compiled):
        assert compiled.coeffs.shape[1] == 7
        assert not any(lp[5] == "v" for lp in compiled.set_labelprops)

    def test_no_raw_vflag_rates_survive(self, compiled):
        import pynucastro as pyna

        raw = [
            r.fname
            for r in compiled.rates
            if isinstance(r, pyna.rates.ReacLibRate) and r.derived_from_inverse
        ]
        assert raw == []

    def test_replacement_covered_every_vflag_column(self, compiled):
        rep = compiled.replace_report
        assert rep.n_replaced == int(compiled.stoich.derived_from_inverse.sum())
        assert rep.failed == ()

    def test_column_identity_preserved(self, compiled):
        # replacement must not have changed any column's participants:
        # non-replaced columns keep their fname; replaced ones are DerivedRate
        # with identical reactant/product multisets (asserted at build) whose
        # fname swaps only the label suffix (_reaclib → _derived)
        import pynucastro as pyna

        for j, r in enumerate(compiled.rates):
            if compiled.stoich.derived_from_inverse[j]:
                assert isinstance(r, pyna.rates.DerivedRate)
                assert r.fname.replace("_derived", "") == compiled.stoich.rate_fnames[
                    j
                ].replace("_reaclib", "")
            else:
                assert r.fname == compiled.stoich.rate_fnames[j]


class TestLambdaMatchesPyna:
    def test_all_rates_match_scalar_eval(self, compiled, box_compositions):
        """Engine λ (screening OFF) vs rate.eval for every rate, every state."""
        from gnn_nucleo.fluxes.compile import compile_network
        from gnn_nucleo.fluxes.engine import evaluate_lambda

        cn = compile_network(compiled.network, screening=None)
        t9 = np.array([s[0] for s in STATES])
        rho = np.array([s[1] for s in STATES])
        T = t9 * 1e9

        lam = evaluate_lambda(cn, T, rho, box_compositions / cn.stoich.A[:, None])

        worst = 0.0
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            for k in range(len(STATES)):
                comp = _pyna_composition(cn, box_compositions[:, k])
                for j, rate in enumerate(cn.rates):
                    ref = rate.eval(T[k], rho=rho[k], comp=comp)
                    if ref == 0.0 and lam[j, k] == 0.0:
                        continue
                    rel = abs(lam[j, k] - ref) / max(abs(ref), abs(lam[j, k]))
                    worst = max(worst, rel)
        assert worst <= 5e-12, f"{cn.network}: worst λ rel error {worst:.3e}"

    def test_screened_lambda_matches_scalar_eval(self, compiled, box_compositions):
        """Engine λ WITH chugunov_2007 vs rate.eval(screen_func=...) on a
        reaction subsample (screening path exercises pyna's own pair walk)."""
        from pynucastro.screening import chugunov_2007

        from gnn_nucleo.fluxes.engine import evaluate_lambda

        t9 = np.array([s[0] for s in STATES])
        rho = np.array([s[1] for s in STATES])
        T = t9 * 1e9
        Y = box_compositions / compiled.stoich.A[:, None]
        lam = evaluate_lambda(compiled, T, rho, Y)

        rng = np.random.default_rng(7)
        sample = rng.choice(len(compiled.rates), size=60, replace=False)
        worst = 0.0
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            for k in range(len(STATES)):
                comp = _pyna_composition(compiled, box_compositions[:, k])
                for j in sample:
                    rate = compiled.rates[j]
                    ref = rate.eval(
                        T[k], rho=rho[k], comp=comp, screen_func=chugunov_2007
                    )
                    if ref == 0.0 and lam[j, k] == 0.0:
                        continue
                    rel = abs(lam[j, k] - ref) / max(abs(ref), abs(lam[j, k]))
                    worst = max(worst, rel)
        assert worst <= 5e-12, f"{compiled.network}: worst screened rel {worst:.3e}"


class TestScreeningVectorized:
    def test_matches_pyna_scalar(self, compiled, box_compositions):
        from pynucastro.screening import (
            ScreenFactors,
            chugunov_2007,
            make_plasma_state,
        )

        from gnn_nucleo.fluxes.screening import chugunov_2007_vec, plasma_arrays
        from gnn_nucleo.graph import load_isotope_table

        table = load_isotope_table(compiled.network)
        t9 = np.array([s[0] for s in STATES])
        rho = np.array([s[1] for s in STATES])
        T = t9 * 1e9
        Y = box_compositions / compiled.stoich.A[:, None]

        n_e, gamma_e_fac = plasma_arrays(rho, Y, compiled.stoich.Z)
        z1, a1, z2, a2 = (compiled.screen_pairs[:, i] for i in range(4))
        vec = chugunov_2007_vec(T, n_e, gamma_e_fac, z1, a1, z2, a2)

        nuclei = list(table.nuclei)
        for k in range(len(STATES)):
            molar = {
                nuc: float(Y[i, k]) for i, nuc in enumerate(nuclei)
            }
            state = make_plasma_state(T[k], rho[k], molar)
            assert abs(state.n_e - n_e[k]) / state.n_e <= 1e-12
            assert abs(state.gamma_e_fac - gamma_e_fac[k]) / state.gamma_e_fac <= 1e-12
            for p in range(len(z1)):
                ref = chugunov_2007(
                    state, ScreenFactors(int(z1[p]), int(a1[p]), int(z2[p]), int(a2[p]))
                )
                got = vec[p, k]
                assert abs(got - ref) <= 1e-12 * max(1.0, abs(ref)), (
                    f"pair {p} state {k}: {got} vs {ref}"
                )
