"""Tests for gnn_nucleo.killtest — synthetic oracles for every pure function.

The invariant test is structural: Guidry masks produced by
``killtest.active_set.guidry_masks`` can NEVER mask a weak column, because
they route through ``qse.diagnostics.eligible_mask`` (CLAUDE.md invariant #2).
"""

from __future__ import annotations

import numpy as np

from gnn_nucleo.killtest import active_set as ks
from gnn_nucleo.killtest import strata


class TestStrata:
    def test_assign(self):
        T = np.array([2.0e9, 3.5e9, 7.0e9, 1.0e9])
        ye = np.array([0.455, 0.47, 0.49, 0.499])
        t9b, yeb = strata.assign_strata(T, ye)
        assert t9b.tolist() == [0, 2, 5, -1]
        assert yeb.tolist() == [0, 1, 2, 2]

    def test_outside_marked(self):
        t9b, yeb = strata.assign_strata(np.array([9e9]), np.array([0.3]))
        assert t9b[0] == -1 and yeb[0] == -1


class TestGuidryMasks:
    def test_weak_never_maskable(self):
        rng = np.random.default_rng(0)
        n = 50
        weak = rng.random(n) < 0.3
        delta_r = np.zeros(n)  # everything looks equilibrated
        masks = ks.guidry_masks(delta_r, weak, eps=(3e-3, 1e-2, 3e-2))
        for eps, maskable in masks.items():
            assert not (maskable & weak).any(), f"weak column maskable at {eps}"
            # non-weak fully maskable here
            assert (maskable | weak).all()

    def test_eps_monotone(self):
        rng = np.random.default_rng(1)
        delta_r = rng.lognormal(-4, 2, size=200)
        weak = np.zeros(200, dtype=bool)
        masks = ks.guidry_masks(delta_r, weak)
        sizes = [m.sum() for m in masks.values()]
        assert sizes == sorted(sizes)  # larger eps ⇒ more maskable


class TestCondSActive:
    def test_known_cond(self):
        nu = np.array([[1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 4.0]])
        assert np.isclose(ks.cond_s_active(nu, np.array([True, True, False])), 2.0)
        assert np.isclose(ks.cond_s_active(nu, np.array([True, False, True])), 4.0)

    def test_empty_active(self):
        nu = np.eye(3)
        assert np.isnan(ks.cond_s_active(nu, np.zeros(3, dtype=bool)))


class TestTopK:
    def test_concentration(self):
        shares = np.array([5.0, 3.0, 1.0, 1.0])
        out = ks.topk_concentration(shares, k=(1, 2, 4, 10))
        assert np.isclose(out[1], 0.5)
        assert np.isclose(out[2], 0.8)
        assert np.isclose(out[4], 1.0)
        assert np.isclose(out[10], 1.0)  # k beyond length saturates


class TestCarriedFractions:
    def test_hand_built(self):
        # 2 species × 3 columns; species 0 receives |1*2|, |1*1|, |2*0.5|
        nu = np.array([[1.0, -1.0, 2.0], [0.0, 1.0, -2.0]])
        phi = np.array([2.0, 1.0, 0.5])
        active = np.array([True, False, True])
        cov = ks.carried_fractions(nu, phi, active)
        assert np.isclose(cov[0], (2.0 + 1.0) / (2.0 + 1.0 + 1.0))
        assert np.isclose(cov[1], 1.0 / (1.0 + 1.0))

    def test_all_active_is_one(self):
        rng = np.random.default_rng(2)
        nu = rng.normal(size=(4, 9))
        phi = rng.normal(size=9)
        cov = ks.carried_fractions(nu, phi, np.ones(9, dtype=bool))
        np.testing.assert_allclose(cov, 1.0)


class TestMaskChurn:
    def test_known_flips(self):
        m = np.array(
            [
                [True, False, False],
                [True, True, False],   # 1 flip
                [False, True, False],  # 1 flip
                [False, True, True],   # 1 flip
            ]
        )
        out = ks.mask_churn(m)
        assert out["flips_per_step"] == 1.0
        assert np.isclose(out["churn_fraction"], 1.0 / 3.0)

    def test_static_mask_zero(self):
        m = np.tile(np.array([True, False, True]), (5, 1))
        assert ks.mask_churn(m)["flips_per_step"] == 0.0


class TestReactionDeltaBatch:
    def test_matches_loop_version(self):
        from gnn_nucleo.qse.diagnostics import reaction_delta, reaction_delta_batch

        rng = np.random.default_rng(7)
        nu = rng.integers(-2, 3, size=(6, 15)).astype(float)
        nu[:, 3] = 0.0  # an empty column
        for _ in range(3):
            delta = rng.lognormal(-2, 1, size=6)
            delta[rng.integers(0, 6)] = np.inf
            ref = reaction_delta(nu, delta)
            got = reaction_delta_batch(nu, delta[None, :])[0]
            np.testing.assert_array_equal(got, ref)


class TestTimescaleSeparation:
    def test_constructed(self):
        f_plus = np.array([1e6, 1e5, 3.0, 2.0])
        phi = np.array([1e-2, 1e-3, 3.0, 2.0])
        eq = np.array([True, True, False, False])
        bottleneck = np.array([False, False, True, True])
        r = ks.timescale_separation(f_plus, phi, eq, bottleneck)
        assert np.isclose(r, 1e6 / 2.0)

    def test_no_eq_columns_nan(self):
        r = ks.timescale_separation(
            np.array([1.0]), np.array([1.0]),
            np.array([False]), np.array([True]),
        )
        assert np.isnan(r)
