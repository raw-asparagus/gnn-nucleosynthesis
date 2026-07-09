"""Data-dependent Step-4 tests: Ye reconstruction and probe smoke test.

Both skip cleanly when their external dependency (Zenodo training CSVs /
the built MESA probe) is absent, so the core suite stays hermetic.
"""

from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
TRAINING = REPO / "data/zenodo/NuclearNeuralNetworks/training_sets"


@pytest.mark.parametrize("network", ["mesa_80", "mesa_151"])
def test_ye_reconstruction_in_box(network):
    """Ye_initial = sum Z_i X_i / A_i must land in the published box
    (0.45, 0.5) and initial mass fractions must sum to ~1."""
    pd = pytest.importorskip("pandas")
    from gnn_nucleo.crosscheck import xsum_initial, ye_from_initial

    csv = TRAINING / network / f"{network}_1e-1_sec.csv"
    if not csv.exists():
        pytest.skip(f"training CSV not present: {csv}")
    df = pd.read_csv(csv, nrows=5000)
    ye = ye_from_initial(df, network)
    xsum = xsum_initial(df, network)
    assert np.all(ye > 0.4499) and np.all(ye < 0.5001)
    # builder floors mass fractions at 1e-15; sums stay within float-csv noise
    assert np.all(np.abs(xsum - 1.0) < 1e-6)


@pytest.mark.parametrize("net", ["mesa_80.net", "mesa_151.net"])
def test_probe_dump_net_smoke(net):
    """dump_net emits one row per net reaction and every participant maps."""
    from gnn_nucleo.crosscheck import parse_participants, probe_available
    from gnn_nucleo.crosscheck.probe import run_probe

    if not probe_available():
        pytest.skip("mesa_probe binary or MESA_DIR not available")
    df = run_probe("dump_net", net)
    assert len(df) > 500
    assert df["name"].is_unique
    for s in df["inputs"]:
        parse_participants(s)
    for s in df["outputs"]:
        parse_participants(s)
    # weak sector must be present and every weaklib id non-negative
    assert (df["is_weak"] == 1).sum() > 0
    assert (df["weaklib_id"] >= 0).all()
