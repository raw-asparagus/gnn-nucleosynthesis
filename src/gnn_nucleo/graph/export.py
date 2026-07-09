"""Serialisation of the validated stoichiometry and the bipartite graph.

Artifacts (regenerable, gitignored; content hashes go to RESULTS.md):

- ``data/stoich/nu_<net>.npz``     — ν, ν̃, C, ledgers, per-rate metadata.
  A superset of the original prototype schema (nu, A, Z, weak_mask,
  d_electron, species, rate_strings), so pre-existing consumers keep working.
- ``data/graphs/<net>.graphml``    — heterogeneous bipartite digraph:
  isotope nodes and reaction nodes; I→R reactant-incidence edges and R→I
  signed product-incidence edges (``coeff`` attribute). The I→I
  intra-reaction coupling view is derived, not stored (see metrics.py).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import networkx as nx
import numpy as np

from .isotopes import IsotopeTable, canonical_network, load_isotope_table
from .network import BuildInfo, build_rate_collection
from .stoich import Stoich, build_stoich

_REPO = Path(__file__).resolve().parents[3]


def npz_path(network: str) -> Path:
    return _REPO / "data/stoich" / f"nu_{canonical_network(network).replace('_', '')}.npz"


def graphml_path(network: str) -> Path:
    return _REPO / "data/graphs" / f"{canonical_network(network).replace('_', '')}.graphml"


def export_npz(stoich: Stoich, info: BuildInfo, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out,
        # prototype-compatible keys
        nu=stoich.nu,
        A=stoich.A,
        Z=stoich.Z,
        weak_mask=stoich.weak_mask,
        d_electron=stoich.d_electron,
        species=np.array(stoich.species),
        rate_strings=np.array(stoich.rate_strings),
        # extended conservation layer
        nu_ext=stoich.nu_ext,
        C=stoich.C,
        d_neutrino=stoich.d_neutrino,
        d_antineutrino=stoich.d_antineutrino,
        weak_type=np.array(stoich.weak_type),
        rate_fnames=np.array(stoich.rate_fnames),
        Q=stoich.Q,
        is_tabular=stoich.is_tabular,
        derived_from_inverse=stoich.derived_from_inverse,
        chapter=stoich.chapter,
        source_label=np.array(stoich.source_label),
        # build provenance
        network=np.array(info.network),
        pynucastro_version=np.array(info.pynucastro_version),
        tabular_ordering=np.array(list(info.tabular_ordering)),
        n_duplicate_groups_resolved=np.array(info.n_duplicate_groups_resolved),
        provisional_reaction_set=np.array(info.provisional_reaction_set),
        disposition_sha256=np.array(info.disposition_sha256),
        n_dropped=np.array(info.n_dropped),
    )
    return out


def bipartite_digraph(stoich: Stoich) -> nx.DiGraph:
    """Heterogeneous bipartite digraph: I→R reactant edges, R→I product edges.

    Node attrs: isotopes carry kind/Z/A; reactions carry kind/weak/weak_type/
    Q/tabular. Edge attr ``coeff``: consumed count on I→R (positive),
    signed net production on R→I. A catalyst-like species (consumed and
    produced) gets both edges.
    """
    g = nx.DiGraph()
    for name, z, a in zip(stoich.species, stoich.Z, stoich.A):
        g.add_node(name, kind="isotope", Z=int(z), A=int(a))
    for j, fname in enumerate(stoich.rate_fnames):
        rnode = f"rxn:{fname}"
        g.add_node(
            rnode,
            kind="reaction",
            weak=bool(stoich.weak_mask[j]),
            weak_type=stoich.weak_type[j],
            Q=float(stoich.Q[j]),
            tabular=bool(stoich.is_tabular[j]),
        )
        col = stoich.nu[:, j]
        for i in np.flatnonzero(col < 0):
            g.add_edge(stoich.species[i], rnode, coeff=float(-col[i]))
        for i in np.flatnonzero(col > 0):
            g.add_edge(rnode, stoich.species[i], coeff=float(col[i]))
    return g


def export_graphml(stoich: Stoich, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(bipartite_digraph(stoich), out)
    return out


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def content_hash(npz: Path) -> str:
    """Reproducible sha256 of the npz CONTENT (keys + array bytes).

    The .npz container embeds zip timestamps, so the file hash differs
    between identical exports; this one does not. RESULTS.md records this.
    """
    h = hashlib.sha256()
    with np.load(npz, allow_pickle=False) as data:
        for key in sorted(data.files):
            arr = np.ascontiguousarray(data[key])
            h.update(key.encode())
            h.update(str(arr.dtype).encode())
            h.update(str(arr.shape).encode())
            h.update(arr.tobytes())
    return h.hexdigest()


def build_and_export(
    network: str,
    tabular_ordering: tuple[str, ...] | None = None,
) -> tuple[Stoich, BuildInfo, IsotopeTable, Path, Path]:
    """One-call pipeline: YAML → RateCollection → validated Stoich → artifacts."""
    table = load_isotope_table(network)
    rc, info = build_rate_collection(table, tabular_ordering)
    stoich = build_stoich(rc, table)
    npz = export_npz(stoich, info, npz_path(network))
    gml = export_graphml(stoich, graphml_path(network))
    return stoich, info, table, npz, gml
