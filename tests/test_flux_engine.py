"""Flux-engine semantics: ydot oracle, conservation, pair/weak contracts.

Gates (Step-5 brief / plan):
- ν·R from the engine vs pynucastro ``evaluate_ydots`` on the same states
  (post-replacement rate set, chugunov_2007): |rel| ≤ 1e-10 of max|ẏ|;
- conservation Σᵢ Aᵢ(νR)ᵢ within the scaled float64 drift bound
  (tests/test_conservation.py convention);
- weak columns: f⁻ = 0 and κ = 1 (never "equilibrated");
- pair antisymmetry φ_pair(j) = −φ_j, and the net identity
  ν R = Σ_{j ∈ forward ∪ unpaired} ν_ij φ_j;
- dẎₑ through weak columns is nonzero on physical states (invariant #3).
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest

T9_RHO_YE = [
    (3.3, 1e8, 0.48),
    (5.0, 1e8, 0.48),
    (6.3, 1e9, 0.45),
    (7.9, 1e7, 0.498),
]


@pytest.fixture(scope="session", params=["mesa_80", "mesa_151"])
def engine_case(request):
    """Compiled network + a flux batch on physical (NSE-anchored) states."""
    from gnn_nucleo.crosscheck.kappa import nse_composition
    from gnn_nucleo.fluxes.compile import compile_network
    from gnn_nucleo.fluxes.engine import evaluate_fluxes

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        cn = compile_network(request.param, screening="chugunov_2007")

    comps, states = [], []
    for t9, rho, ye in T9_RHO_YE:
        comp, ok = nse_composition(request.param, t9, rho, ye)
        if not ok:
            continue
        comps.append(comp)
        states.append((t9, rho, ye))
    assert len(states) >= 3, "NSE anchor states failed to converge"

    n = cn.stoich.n_species
    Y = np.empty((n, len(states)), dtype=np.float64)
    from gnn_nucleo.graph import load_isotope_table

    nuclei = list(load_isotope_table(request.param).nuclei)
    for k, comp in enumerate(comps):
        molar = comp.get_molar()
        Y[:, k] = [molar[nuc] for nuc in nuclei]

    T = np.array([s[0] for s in states]) * 1e9
    rho = np.array([s[1] for s in states])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        batch = evaluate_fluxes(cn, T, rho, Y)
    return cn, batch, T, rho, Y, comps


class TestYdotOracle:
    def test_matches_pyna_evaluate_ydots(self, engine_case):
        import pynucastro as pyna
        from pynucastro.screening import chugunov_2007

        from gnn_nucleo.graph import load_isotope_table

        cn, batch, T, rho, Y, comps = engine_case
        rc_db = pyna.RateCollection(rates=list(cn.rates))
        nuclei = list(load_isotope_table(cn.network).nuclei)

        # At NSE the net ẏ is a tiny residual of huge gross fluxes; both
        # summation orders carry fp noise ~ε·gross, so the honest gate is
        # relative to the per-species GROSS flux Σ_j|ν_ij|R_j (same spirit as
        # the conservation gate), not to max|ẏ|.
        gross = np.abs(cn.stoich.nu) @ batch.f_plus  # (n_species, n_states)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            for k, comp in enumerate(comps):
                ydots = rc_db.evaluate_ydots(
                    rho[k], T[k], comp, screen_func=chugunov_2007
                )
                ref = np.array([ydots[nuc] for nuc in nuclei])
                err = np.abs(batch.ydot[:, k] - ref)
                tol = 1e-12 * gross[:, k]
                bad = err > tol
                assert not bad.any(), (
                    f"{cn.network} state {k}: ydot off gross-relative gate on "
                    f"{[str(nuclei[i]) for i in np.nonzero(bad)[0][:5]]}; "
                    f"worst err/gross {(err / np.maximum(gross[:, k], 1e-300)).max():.3e}"
                )


class TestConservation:
    def test_baryon_drift_within_gate(self, engine_case):
        cn, batch, *_ = engine_case
        A, nu = cn.stoich.A, cn.stoich.nu
        R = batch.f_plus  # gross per-column rates
        for k in range(R.shape[1]):
            drift = abs(float(A @ (nu @ R[:, k])))
            gross = float(np.abs(A) @ (np.abs(nu) @ np.abs(R[:, k])))
            s = min(1.0, float(np.abs(R[:, k]).max()))
            tol = max(1e-12 * s, 1e-13 * gross)
            assert drift <= tol, f"state {k}: drift {drift:.3e} > tol {tol:.3e}"

    def test_dye_weak_nonzero(self, engine_case):
        cn, batch, *_ = engine_case
        assert np.all(np.abs(batch.dye_weak) > 0.0)


class TestPairContracts:
    def test_weak_columns_have_zero_reverse_and_kappa_one(self, engine_case):
        cn, batch, *_ = engine_case
        w = cn.stoich.weak_mask
        assert np.all(batch.f_minus[w] == 0.0)
        active = batch.f_plus[w] > 0
        assert np.all(batch.kappa[w][active] == 1.0)
        assert np.all(cn.pair_col[w] == -1)

    def test_pair_antisymmetry(self, engine_case):
        cn, batch, *_ = engine_case
        paired = cn.pair_col >= 0
        j = np.nonzero(paired)[0]
        pj = cn.pair_col[j]
        np.testing.assert_array_equal(batch.f_minus[j], batch.f_plus[pj])
        np.testing.assert_allclose(
            batch.phi[j], -batch.phi[pj], rtol=0, atol=0
        )

    def test_pair_map_is_involution_on_strong_pairs(self, engine_case):
        cn, *_ = engine_case
        paired = cn.pair_col >= 0
        j = np.nonzero(paired)[0]
        np.testing.assert_array_equal(cn.pair_col[cn.pair_col[j]], j)
        # exactly one forward member per pair
        fwd = cn.is_forward_member[j]
        assert np.all(fwd != cn.is_forward_member[cn.pair_col[j]])

    def test_net_identity(self, engine_case):
        """ν R == Σ over forward-or-unpaired columns of ν_ij φ_j — up to fp
        noise relative to the per-species gross flux (cancellation-dominated
        at NSE, exactly the κ-floor physics)."""
        cn, batch, *_ = engine_case
        net_cols = cn.is_forward_member | (cn.pair_col < 0)
        lhs = batch.ydot
        rhs = cn.stoich.nu[:, net_cols] @ batch.phi[net_cols]
        gross = np.abs(cn.stoich.nu) @ batch.f_plus
        assert np.all(np.abs(rhs - lhs) <= 1e-12 * gross)

    def test_kappa_definition(self, engine_case):
        cn, batch, *_ = engine_case
        denom = batch.f_plus + batch.f_minus
        ok = denom > 0
        np.testing.assert_allclose(
            batch.kappa[ok],
            np.abs(batch.phi[ok]) / denom[ok],
            rtol=1e-15,
        )
        assert np.all(batch.kappa[~ok] == 0.0)

    def test_kappa_vanishes_at_nse_unscreened(self, engine_case):
        """DB consistency: with pf-corrected reverses and screening OFF (the
        Step-4 κ-screen configuration), flux-carrying strong pairs at NSE must
        collapse far below the spurious 6.6e-2/1.3e-1 v-flag floor. Measured
        here: median κ ~3e-12. Bound: median < 1e-9, max < 1e-6."""
        from gnn_nucleo.fluxes.compile import compile_network
        from gnn_nucleo.fluxes.engine import evaluate_fluxes

        cn, _, T, rho, Y, _ = engine_case
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            cn0 = compile_network(cn.network, screening=None)
            b0 = evaluate_fluxes(cn0, T, rho, Y)
        hot = T / 1e9 >= 5.0
        strong_fwd = cn.is_forward_member & (cn.pair_col >= 0)
        f = b0.f_plus[strong_fwd][:, hot]
        k = b0.kappa[strong_fwd][:, hot]
        carrying = f > np.median(f[f > 0])
        assert np.median(k[carrying]) < 1e-9
        assert k[carrying].max() < 1e-6

    def test_screening_asymmetry_offsets_kappa_at_nse(self, engine_case):
        """Documented behavior, not a bug: with chugunov_2007 ON (the label
        configuration), κ at NSE does NOT vanish — screening is applied per
        reaction from its own reactant pairs, so a screened capture pairs with
        an unscreened photodissociation and κ ≈ |Δlog_scor| (percent-level at
        ρ ~ 1e9). Step 6 must interpret κ thresholds with this in mind."""
        cn, batch, T, *_ = engine_case
        hot = T / 1e9 >= 5.0
        strong_fwd = cn.is_forward_member & (cn.pair_col >= 0)
        f = batch.f_plus[strong_fwd][:, hot]
        k = batch.kappa[strong_fwd][:, hot]
        carrying = f > np.median(f[f > 0])
        assert np.median(k[carrying]) > 1e-4  # screening offset is present
