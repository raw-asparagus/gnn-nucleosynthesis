"""Schema invariants: dt grid, shape checks, provenance tags, leakage-safe splits."""

import math

import pytest

from gnn_nucleo.data.schema import (
    DT_GRID_SECONDS,
    N_TIMESTEPS,
    NETWORKS,
    Provenance,
    SplitSpec,
    StepInputs,
    StepLabels,
)


def test_dt_grid_is_nine_log_spaced_steps_over_1em6_to_1e2():
    assert len(DT_GRID_SECONDS) == N_TIMESTEPS == 9
    assert math.isclose(DT_GRID_SECONDS[0], 1e-6, rel_tol=1e-12)
    assert math.isclose(DT_GRID_SECONDS[-1], 1e2, rel_tol=1e-12)
    ratios = [DT_GRID_SECONDS[k + 1] / DT_GRID_SECONDS[k] for k in range(8)]
    for r in ratios:  # exactly one decade per step
        assert math.isclose(r, 10.0, rel_tol=1e-12)


def test_network_species_counts():
    assert NETWORKS == {"mesa_80": 80, "mesa_151": 151}


def _inputs(network="mesa_80", dt_index=0, **overrides):
    n = NETWORKS[network]
    kwargs = dict(
        sobol_id=42,
        network=network,
        log_T=9.5,
        log_rho=8.0,
        X=(1.0 / n,) * n,
        dt_index=dt_index,
        dt_seconds=DT_GRID_SECONDS[dt_index],
    )
    kwargs.update(overrides)
    return StepInputs(**kwargs)


def test_inputs_accept_consistent_record():
    rec = _inputs()
    assert rec.sobol_id == 42
    assert len(rec.X) == 80


def test_inputs_reject_wrong_composition_length():
    with pytest.raises(ValueError, match="expected 80"):
        _inputs(X=(0.5, 0.5))


def test_inputs_reject_unknown_network():
    with pytest.raises(ValueError, match="unknown network"):
        StepInputs(
            sobol_id=1,
            network="mesa_999",
            log_T=9.5,
            log_rho=8.0,
            X=(0.5, 0.5),
            dt_index=0,
            dt_seconds=DT_GRID_SECONDS[0],
        )


def test_inputs_reject_dt_mismatch():
    with pytest.raises(ValueError, match="dt_seconds"):
        _inputs(dt_index=3, dt_seconds=DT_GRID_SECONDS[4])


def test_labels_hold_post_step_targets():
    lab = StepLabels(X_post=(1.0,) * 80, e_nuc=1.0e17, neutrino_loss=1.0e15)
    assert len(lab.X_post) == 80


def test_provenance_tags_round_trip():
    for tag in ("sourced", "derived", "measured"):
        assert Provenance(tag).value == tag
    assert set(Provenance) == {Provenance.SOURCED, Provenance.DERIVED, Provenance.MEASURED}


def test_split_spec_disjoint_passes():
    spec = SplitSpec(
        train_ids=frozenset({1, 2, 3}),
        val_ids=frozenset({4}),
        test_ids=frozenset({5, 6}),
    )
    spec.validate()
    assert spec.split_of(4) == "val"
    assert spec.split_of(99) is None


def test_split_spec_rejects_overlap():
    spec = SplitSpec(
        train_ids=frozenset({1, 2}),
        val_ids=frozenset({2}),
        test_ids=frozenset({3}),
    )
    with pytest.raises(ValueError, match="split leakage"):
        spec.validate()
