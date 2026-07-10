"""Stratified-subsample logic: reproducibility, quotas, overweighting, and
trajectory selection (pure functions on synthetic inputs — the real-CSV path
runs through scripts/step5_make_subsample.py)."""

from __future__ import annotations

import numpy as np

from gnn_nucleo.data.subsample import (
    LOGRHO_EDGES,
    T9_EDGES,
    YE_EDGES,
    compute_ye_initial,
    select_trajectories,
    stratified_sample,
)


def _synth(n=200_000, seed=1):
    rng = np.random.default_rng(seed)
    t9 = 10 ** rng.uniform(np.log10(1.6), np.log10(7.9), n)
    logrho = rng.uniform(7.0, 9.0, n)
    ye = rng.uniform(0.45, 0.5, n)
    return t9, logrho, ye


class TestStratifiedSample:
    def test_reproducible(self):
        t9, lr, ye = _synth()
        ids1, _ = stratified_sample(t9, lr, ye, n_target=10_000, seed=42)
        ids2, _ = stratified_sample(t9, lr, ye, n_target=10_000, seed=42)
        np.testing.assert_array_equal(ids1, ids2)

    def test_seed_changes_draw(self):
        t9, lr, ye = _synth()
        ids1, _ = stratified_sample(t9, lr, ye, n_target=10_000, seed=1)
        ids2, _ = stratified_sample(t9, lr, ye, n_target=10_000, seed=2)
        assert not np.array_equal(ids1, ids2)

    def test_target_achieved_and_bounds(self):
        t9, lr, ye = _synth()
        ids, spec = stratified_sample(t9, lr, ye, n_target=10_000)
        assert 0.99 * 10_000 <= spec["n_achieved"] <= 10_000
        assert ids.min() >= 0 and ids.max() < len(t9)
        assert len(np.unique(ids)) == len(ids)

    def test_qse_window_overweighted(self):
        t9, lr, ye = _synth()
        ids, _ = stratified_sample(t9, lr, ye, n_target=10_000)
        t9s = t9[ids]
        n_qse = ((t9s >= 3.3) & (t9s < 5.0)).sum()
        n_low = ((t9s >= 1.6) & (t9s < 3.3)).sum()
        # QSE window spans 2 of 6 T9 bins at weight 2: expect ≈ 2·(2/6)/norm —
        # about twice the per-bin rate of the unweighted bins
        rate_qse = n_qse / 2  # per bin
        rate_low = n_low / 2
        assert rate_qse > 1.6 * rate_low

    def test_small_stratum_taken_whole_and_redistributed(self):
        # put almost everything in one stratum: tiny strata are exhausted and
        # the shortfall lands in the big one
        n = 50_000
        t9 = np.full(n, 4.5)
        lr = np.full(n, 8.0)
        ye = np.full(n, 0.47)
        t9[:10] = 2.0  # 10 states in a low-T stratum
        ids, spec = stratified_sample(t9, lr, ye, n_target=5_000)
        assert spec["n_achieved"] == 5_000
        assert ((t9[ids] == 2.0).sum()) == 10  # taken whole

    def test_edges_definition(self):
        assert len(T9_EDGES) - 1 == 6
        assert len(LOGRHO_EDGES) - 1 == 3
        assert len(YE_EDGES) - 1 == 3


class TestYeInitial:
    def test_pure_ni56(self):
        X = np.array([[1.0]])
        assert compute_ye_initial(X, np.array([28.0]), np.array([56.0]))[0] == 0.5

    def test_mix(self):
        # 50/50 ni56 (ye .5) / fe56 (ye 26/56)
        X = np.array([[0.5, 0.5]])
        got = compute_ye_initial(X, np.array([28.0, 26.0]), np.array([56.0, 56.0]))[0]
        assert abs(got - (0.25 + 0.5 * 26.0 / 56.0)) < 1e-15


class TestTrajectorySelection:
    def test_grid_coverage_and_uniqueness(self):
        rng = np.random.default_rng(0)
        files = [
            f"output_T_{t:.3f}_rho_{r:.3f}.txt"
            for t, r in zip(rng.uniform(9.2, 9.9, 300), rng.uniform(7, 9, 300))
        ]
        chosen = select_trajectories(files)
        assert len(chosen) == 20
        assert len(set(chosen)) == 20

    def test_fewer_files_than_cells(self):
        files = ["output_T_9.500_rho_8.000.txt", "output_T_9.300_rho_7.500.txt"]
        chosen = select_trajectories(files)
        assert sorted(chosen) == sorted(files)
