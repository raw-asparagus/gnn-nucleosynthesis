"""Schema invariants: dt grids, shape checks, provenance tags, leakage-safe splits.

Two layers: synthetic invariants (always run) and a smoke test against the
REAL extracted training CSVs (skipped when data/zenodo/ is absent, e.g. CI).
"""

import math
from pathlib import Path

import pytest

from gnn_nucleo.data.schema import (
    DT_GRID_SECONDS,
    DT_LABELS,
    EPS_NORMALIZATION,
    EPS_NU_QUARANTINED,
    FINAL_X_FLOOR,
    N_TIMESTEPS,
    NETWORKS,
    Provenance,
    SplitSpec,
    StepInputs,
    StepLabels,
    load_measured_dt,
)

REPO = Path(__file__).resolve().parents[1]
TRAINING = REPO / "data/zenodo/NuclearNeuralNetworks/training_sets"


def test_nominal_dt_grid_is_nine_log_spaced_labels_over_1em6_to_1e2():
    assert len(DT_GRID_SECONDS) == N_TIMESTEPS == len(DT_LABELS) == 9
    assert math.isclose(DT_GRID_SECONDS[0], 1e-6, rel_tol=1e-12)
    assert math.isclose(DT_GRID_SECONDS[-1], 1e2, rel_tol=1e-12)
    ratios = [DT_GRID_SECONDS[k + 1] / DT_GRID_SECONDS[k] for k in range(8)]
    for r in ratios:  # exactly one decade per step
        assert math.isclose(r, 10.0, rel_tol=1e-12)


@pytest.mark.parametrize("network", sorted(NETWORKS))
def test_measured_dt_grid_loads_and_tracks_nominal_within_6_percent(network):
    grid = load_measured_dt(network)
    assert len(grid) == N_TIMESTEPS
    for measured, nominal in zip(grid, DT_GRID_SECONDS):
        assert 0.94 * nominal < measured < 1.06 * nominal
    # The grids are genuinely per-network — mesa_80 "1e2" is 105.08 s,
    # mesa_151 is 102.93 s (RESULTS.md 2026-07-08).
    assert load_measured_dt("mesa_80")[-1] != load_measured_dt("mesa_151")[-1]


def test_network_species_counts():
    assert NETWORKS == {"mesa_80": 80, "mesa_151": 151}


def test_normalization_constants():
    assert EPS_NORMALIZATION == 1e16
    assert FINAL_X_FLOOR == 1e-15
    # Measured empty (RESULTS.md 2026-07-08); a nonempty set means a loader
    # somewhere must refuse eps_nu labels — keep this visible.
    assert EPS_NU_QUARANTINED == frozenset()


def _inputs(network="mesa_80", dt_index=0, **overrides):
    n = NETWORKS[network]
    kwargs = dict(
        state_id=42,
        network=network,
        log_T=9.5,
        log_rho=8.0,
        X=(1.0 / n,) * n,
        dt_index=dt_index,
        dt_seconds=load_measured_dt(network)[dt_index],
    )
    kwargs.update(overrides)
    return StepInputs(**kwargs)


def test_inputs_accept_consistent_record():
    rec = _inputs()
    assert rec.state_id == 42
    assert len(rec.X) == 80


def test_inputs_reject_wrong_composition_length():
    with pytest.raises(ValueError, match="expected 80"):
        _inputs(X=(0.5, 0.5))


def test_inputs_reject_unknown_network():
    with pytest.raises(ValueError, match="unknown network"):
        StepInputs(
            state_id=1,
            network="mesa_999",
            log_T=9.5,
            log_rho=8.0,
            X=(0.5, 0.5),
            dt_index=0,
            dt_seconds=1e-6,
        )


def test_inputs_reject_dt_mismatch():
    with pytest.raises(ValueError, match="dt_seconds"):
        _inputs(dt_index=3, dt_seconds=load_measured_dt("mesa_80")[4])


def test_inputs_reject_nominal_dt_where_measured_differs():
    # The nominal decade value is a LABEL; real records must carry the
    # measured timestep (5% off nominal at dt_index 8).
    with pytest.raises(ValueError, match="dt_seconds"):
        _inputs(dt_index=8, dt_seconds=100.0)


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


# --- real-CSV smoke layer (skipped without the local Zenodo extraction) ----


@pytest.mark.skipif(not TRAINING.exists(), reason="data/zenodo/ not present")
@pytest.mark.parametrize("network", sorted(NETWORKS))
def test_real_csv_header_and_measured_dt(network):
    """First batch of one real CSV: header layout, isotope order, Age == measured dt."""
    import pyarrow.csv as pv
    import yaml

    path = TRAINING / network / f"{network}_1e-6_sec.csv"
    reader = pv.open_csv(path)
    names = reader.schema.names
    batch = reader.read_next_batch()

    n = NETWORKS[network]
    assert names[:3] == ["Age", "logT", "logRho"]
    assert names[-2:] == ["eps_nuc", "eps_nu"]
    initial = [c for c in names if c.startswith("initial_")]
    final = [c for c in names if c.startswith("final_")]
    assert len(initial) == len(final) == n

    # Column order matches the authoritative isotope YAML exactly.
    with open(REPO / "configs" / f"isotopes_{network.replace('_', '')}.yaml") as fh:
        iso = [e["name"] for e in yaml.safe_load(fh)["isotopes"]]
    assert initial == [f"initial_{name}" for name in iso]
    assert final == [f"final_{name}" for name in iso]

    # Age column equals the measured grid value (full precision, this file).
    measured = load_measured_dt(network)[0]
    ages = set(batch.column(names.index("Age")).to_pylist())
    assert ages == {measured}

    # A real row round-trips through the schema types.
    row = {c: batch.column(i)[0].as_py() for i, c in enumerate(names)}
    rec = StepInputs(
        state_id=0,
        network=network,
        log_T=row["logT"],
        log_rho=row["logRho"],
        X=tuple(row[f"initial_{name}"] for name in iso),
        dt_index=0,
        dt_seconds=row["Age"],
    )
    lab = StepLabels(
        X_post=tuple(row[f"final_{name}"] for name in iso),
        e_nuc=row["eps_nuc"] * EPS_NORMALIZATION,
        neutrino_loss=row["eps_nu"] * EPS_NORMALIZATION,
    )
    assert len(rec.X) == len(lab.X_post) == n
    assert all(x >= FINAL_X_FLOOR for x in lab.X_post)
