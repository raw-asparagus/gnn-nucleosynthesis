"""Every package stub must import cleanly under the pinned environment."""

import importlib

import pytest

MODULES = [
    "conservation",
    "gnn_nucleo",
    "gnn_nucleo.graph",
    "gnn_nucleo.fluxes",
    "gnn_nucleo.qse",
    "gnn_nucleo.killtest",
    "gnn_nucleo.data",
    "gnn_nucleo.data.schema",
]


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    importlib.import_module(name)
