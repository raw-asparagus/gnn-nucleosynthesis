"""FluxStore roundtrip, derived-quantity reconstruction, and resume logic."""

from __future__ import annotations

import numpy as np
import pytest

from gnn_nucleo.fluxes.engine import FluxBatch
from gnn_nucleo.fluxes.store import FluxStore


def _tiny_batch(rng, n_rxn=7, n_species=4, n_states=5):
    f_plus = rng.uniform(0.0, 1e5, (n_rxn, n_states))
    # pairs: (0,1) and (2,3); 4 unpaired strong; 5,6 weak
    pair_col = np.array([1, 0, 3, 2, -1, -1, -1], dtype=np.int64)
    is_fwd = np.array([True, False, False, True, True, False, False])
    weak = np.array([False] * 5 + [True, True])
    f_minus = np.zeros_like(f_plus)
    paired = pair_col >= 0
    f_minus[paired] = f_plus[pair_col[paired]]
    phi = f_plus - f_minus
    denom = f_plus + f_minus
    kappa = np.where(denom > 0, np.abs(phi) / np.where(denom > 0, denom, 1), 0.0)
    ydot = rng.normal(size=(n_species, n_states))
    dye_weak = rng.normal(size=n_states)
    return (
        FluxBatch(f_plus, f_minus, phi, kappa, ydot, dye_weak),
        pair_col,
        is_fwd,
        weak,
    )


@pytest.fixture
def store(tmp_path):
    return FluxStore("mesa_80", "unit-test", root=tmp_path)


class TestRoundtrip:
    def test_derived_quantities_reconstructed_exactly(self, store):
        rng = np.random.default_rng(3)
        batch, pair_col, is_fwd, weak = _tiny_batch(rng)
        n = batch.f_plus.shape[1]
        store.write_chunk(
            0,
            np.arange(n),
            T=np.full(n, 4e9),
            rho=np.full(n, 1e8),
            ye=np.full(n, 0.48),
            batch=batch,
            pair_col=pair_col,
            is_forward_member=is_fwd,
            weak_mask=weak,
            extra_attrs={"screening": "chugunov_2007"},
        )
        chunk = store.read_chunk(0)
        np.testing.assert_array_equal(chunk.f_plus, batch.f_plus)
        np.testing.assert_array_equal(chunk.f_minus, batch.f_minus)
        np.testing.assert_array_equal(chunk.phi, batch.phi)
        np.testing.assert_array_equal(chunk.kappa, batch.kappa)
        np.testing.assert_array_equal(chunk.ydot, batch.ydot)
        np.testing.assert_array_equal(chunk.dye_weak, batch.dye_weak)
        assert chunk.attrs["screening"] == "chugunov_2007"
        assert chunk.attrs["complete"]

    def test_weak_columns_zero_reverse(self, store):
        rng = np.random.default_rng(4)
        batch, pair_col, is_fwd, weak = _tiny_batch(rng)
        n = batch.f_plus.shape[1]
        store.write_chunk(
            0, np.arange(n), np.full(n, 4e9), np.full(n, 1e8), np.full(n, 0.48),
            batch, pair_col, is_fwd, weak,
        )
        chunk = store.read_chunk(0)
        assert np.all(chunk.f_minus[chunk.weak_mask] == 0.0)


class TestResume:
    def test_incomplete_chunk_not_counted(self, store):
        import h5py

        rng = np.random.default_rng(5)
        batch, pair_col, is_fwd, weak = _tiny_batch(rng)
        n = batch.f_plus.shape[1]
        store.write_chunk(
            0, np.arange(n), np.full(n, 4e9), np.full(n, 1e8), np.full(n, 0.48),
            batch, pair_col, is_fwd, weak,
        )
        store.write_chunk(
            16384, np.arange(n), np.full(n, 4e9), np.full(n, 1e8), np.full(n, 0.48),
            batch, pair_col, is_fwd, weak,
        )
        # simulate a crash on the second chunk: strip the complete attr
        with h5py.File(store.chunk_path(16384), "a") as f:
            del f.attrs["complete"]
        assert store.completed_starts() == {0}

    def test_rewrite_after_crash(self, store):
        rng = np.random.default_rng(6)
        batch, pair_col, is_fwd, weak = _tiny_batch(rng)
        n = batch.f_plus.shape[1]
        args = (
            np.arange(n), np.full(n, 4e9), np.full(n, 1e8), np.full(n, 0.48),
            batch, pair_col, is_fwd, weak,
        )
        store.write_chunk(0, *args)
        store.write_chunk(0, *args)  # overwrite is clean
        assert store.completed_starts() == {0}
        assert len(list(store.iter_chunks())) == 1
