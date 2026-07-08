"""Authoritative isotope tables for mesa_80 / mesa_151.

The YAML files under ``configs/`` are the single source of the network
composition (extracted from the Zenodo 14873443 data headers; ca41 included,
exactly 80/151 species). Everything in this package — ν row order, npz
``species`` arrays, graph node names — uses the YAML names and order, which
match the training-CSV column suffixes (``initial_<name>``). pynucastro's
``str(Nucleus)`` capitalisation ("Neut", "H1") is never stored.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml
from pynucastro import Nucleus

from gnn_nucleo.data.schema import NETWORKS

_CONFIG_DIR = Path(__file__).resolve().parents[3] / "configs"


def _config_path(network: str) -> Path:
    return _CONFIG_DIR / f"isotopes_{network.replace('_', '')}.yaml"


def canonical_network(name: str) -> str:
    """Normalise 'mesa80' / 'mesa_80' → 'mesa_80'."""
    key = name if "_" in name else name.replace("mesa", "mesa_")
    if key not in NETWORKS:
        raise ValueError(f"unknown network {name!r}; expected one of {sorted(NETWORKS)}")
    return key


@dataclass(frozen=True)
class IsotopeTable:
    """Species table of one network, in canonical (YAML = CSV-header) order."""

    network: str
    names: tuple[str, ...]
    Z: np.ndarray  # int64, shape (n,)
    A: np.ndarray  # int64, shape (n,)
    nuclei: tuple[Nucleus, ...]

    @property
    def n(self) -> int:
        return len(self.names)

    def index(self) -> dict[Nucleus, int]:
        return {nuc: i for i, nuc in enumerate(self.nuclei)}


def load_isotope_table(network: str) -> IsotopeTable:
    """Load and validate the isotope table for ``network``.

    Every YAML entry is cross-checked against pynucastro's ``Nucleus`` (name
    resolves; Z and A agree), and the species count must equal the network's
    exact size (80/151). Any mismatch is a hard error — the table feeds the
    conservation layer.
    """
    network = canonical_network(network)
    with open(_config_path(network)) as fh:
        cfg = yaml.safe_load(fh)

    entries = cfg["isotopes"]
    if len(entries) != NETWORKS[network] or cfg.get("n_isotopes") != NETWORKS[network]:
        raise ValueError(
            f"{network}: YAML lists {len(entries)} isotopes "
            f"(n_isotopes={cfg.get('n_isotopes')}), expected {NETWORKS[network]}"
        )

    names, zs, azs, nuclei = [], [], [], []
    for e in entries:
        nuc = Nucleus(e["name"])
        if nuc.Z != e["Z"] or nuc.A != e["A"]:
            raise ValueError(
                f"{network}: {e['name']} YAML (Z={e['Z']}, A={e['A']}) disagrees "
                f"with pynucastro (Z={nuc.Z}, A={nuc.A})"
            )
        names.append(e["name"])
        zs.append(e["Z"])
        azs.append(e["A"])
        nuclei.append(nuc)

    if len(set(names)) != len(names):
        raise ValueError(f"{network}: duplicate isotope names in YAML")

    return IsotopeTable(
        network=network,
        names=tuple(names),
        Z=np.asarray(zs, dtype=np.int64),
        A=np.asarray(azs, dtype=np.int64),
        nuclei=tuple(nuclei),
    )
