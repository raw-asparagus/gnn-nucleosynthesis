"""Shared fixtures. The conservation gate must ALWAYS run: the stoichiometric
exports are regenerable from the wheel-shipped pynucastro rate library
(~7 s/network, offline), so a missing npz is built on demand rather than
skipping Layer 2 — locally, in CI, and inside the gate hook alike."""

from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture(scope="session", params=["mesa_80", "mesa_151"])
def stoich_export(request):
    """(network, dict-of-arrays) for the exported ν npz, generating if absent."""
    from gnn_nucleo.graph import build_and_export, npz_path

    path = npz_path(request.param)
    if not path.exists():
        build_and_export(request.param)
    with np.load(path, allow_pickle=False) as data:
        return request.param, {k: data[k] for k in data.files}
