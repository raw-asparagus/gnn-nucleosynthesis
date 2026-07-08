"""Measured quantities of the exported graph and conservation layer.

Everything here feeds RESULTS.md rows (tag: measured) and the phase-0
checklist: reaction census, graph radius/diameter (with/without the I→I
intra-reaction coupling edges), implied processor depth K, condition
numbers, and the drift diagnostics ported from the prototype
scripts/check_conservation.py.
"""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
import numpy as np

from .export import bipartite_digraph
from .stoich import Stoich

_SVD_RANK_RTOL = 1e-12  # singular values below rtol * s_max count as zero


def reaction_census(stoich: Stoich) -> dict:
    """Counts by weak type, REACLIB chapter, source, and direction.

    'Direction' is reported under BOTH available definitions (pynucastro
    2.12.0 has no per-rate .reverse): the ReacLib derived-from-inverse
    marker, and the Q-sign convention RateCollection.get_forward_rates()
    uses (Q < 0 ⇒ reverse).
    """
    weak = stoich.weak_mask
    wt = np.array(stoich.weak_type)
    census = {
        "n_reactions": stoich.n_reactions,
        "n_weak": int(weak.sum()),
        "n_strong_em": int((~weak).sum()),
        "n_tabular": int(stoich.is_tabular.sum()),
        "n_reaclib": int((~stoich.is_tabular).sum()),
        "weak_by_type": {
            t: int((wt == t).sum())
            for t in ("electron_capture", "beta_neg", "beta_pos")
        },
        "weak_reaclib_only": int((weak & ~stoich.is_tabular).sum()),
        "by_chapter": {
            int(c): int((stoich.chapter == c).sum())
            for c in np.unique(stoich.chapter)
        },
        "n_derived_from_inverse": int(stoich.derived_from_inverse.sum()),
        "n_reverse_by_Q_sign": int((stoich.Q < 0).sum()),
    }
    return census


def weak_inventory(stoich: Stoich) -> list[dict]:
    """Per weak reaction: name, type, source, and Yₑ direction.

    dYe/dφ = ΔZ_nuclear = d_electron (EC/β⁺ → −1, lowers Yₑ; β⁻ → +1,
    raises it).
    """
    out = []
    for j in np.flatnonzero(stoich.weak_mask):
        out.append(
            {
                "rate": stoich.rate_strings[j],
                "fname": stoich.rate_fnames[j],
                "weak_type": stoich.weak_type[j],
                "source": stoich.source_label[j],
                "tabular": bool(stoich.is_tabular[j]),
                "dYe_sign": int(stoich.d_electron[j]),
            }
        )
    return out


@dataclass(frozen=True)
class GraphExtent:
    n_nodes: int
    n_edges: int
    connected: bool
    n_components: int
    radius: int          # of the largest component if disconnected
    diameter: int
    implied_K: int       # ceil(radius) + 2 (docs/phase0-checklist row 1)


def _extent(g: nx.Graph) -> GraphExtent:
    comps = list(nx.connected_components(g))
    largest = g.subgraph(max(comps, key=len))
    ecc = nx.eccentricity(largest)
    radius = min(ecc.values())
    diameter = max(ecc.values())
    return GraphExtent(
        n_nodes=g.number_of_nodes(),
        n_edges=g.number_of_edges(),
        connected=len(comps) == 1,
        n_components=len(comps),
        radius=radius,
        diameter=diameter,
        implied_K=int(np.ceil(radius)) + 2,
    )


def graph_extents(stoich: Stoich) -> dict[str, GraphExtent]:
    """Radius/diameter of the undirected views.

    - 'bipartite'         : isotope+reaction nodes, incidence edges only
                            (distances count I→R→I as two hops).
    - 'bipartite_plus_II' : incidence edges plus I→I intra-reaction coupling
                            (any two species of one reaction adjacent).
    - 'isotope_projection': I→I view alone (species graph; one reaction = one
                            hop) — the classic network-topology numbers.
    """
    bip = bipartite_digraph(stoich).to_undirected()

    ii_edges = set()
    for j in range(stoich.n_reactions):
        members = np.flatnonzero(stoich.nu[:, j] != 0.0)
        for a in range(len(members)):
            for b in range(a + 1, len(members)):
                ii_edges.add((stoich.species[members[a]], stoich.species[members[b]]))

    plus = bip.copy()
    plus.add_edges_from(ii_edges)

    proj = nx.Graph()
    proj.add_nodes_from(stoich.species)
    proj.add_edges_from(ii_edges)

    return {
        "bipartite": _extent(bip),
        "bipartite_plus_II": _extent(plus),
        "isotope_projection": _extent(proj),
    }


def condition_numbers(stoich: Stoich) -> dict:
    """SVD condition numbers: full ν (ratio of extreme NONZERO singular
    values, rectangular-safe), extended ν̃, and cond(CCᵀ)."""

    def _cond(m: np.ndarray) -> tuple[float, int]:
        s = np.linalg.svd(m, compute_uv=False)
        nz = s[s > _SVD_RANK_RTOL * s[0]]
        return float(nz[0] / nz[-1]), int(len(nz))

    cond_nu, rank_nu = _cond(stoich.nu)
    cond_ext, rank_ext = _cond(stoich.nu_ext)
    cct = stoich.C @ stoich.C.T
    return {
        "cond_nu": cond_nu,
        "rank_nu": rank_nu,
        "nullity_nu": stoich.n_species - rank_nu,
        "cond_nu_ext": cond_ext,
        "rank_nu_ext": rank_ext,
        "cond_CCt": float(np.linalg.cond(cct)),
    }


def drift_metrics(stoich: Stoich, seed: int = 0) -> dict:
    """Prototype check_conservation.py metrics on the validated arrays.

    D_A / D_Q / strong-column charge leak are column-wise maxima (must be
    ≤ 1e-12; here exactly 0 by construction). dYe_weak under a random
    12-decade flux restricted to weak columns must be NONZERO (invariant #3).
    """
    nu, A, Z = stoich.nu, stoich.A, stoich.Z
    weak = stoich.weak_mask
    D_A = float(np.abs(A @ nu).max())
    D_Q = float(np.abs((Z @ nu)[weak] - stoich.d_electron[weak]).max()) if weak.any() else 0.0
    D_Q_strong = float(np.abs((Z @ nu)[~weak]).max()) if (~weak).any() else 0.0

    rng = np.random.default_rng(seed)
    phi = rng.standard_normal(stoich.n_reactions) * 10.0 ** rng.uniform(
        -12, 0, stoich.n_reactions
    )
    dYe_weak = float(Z @ (nu @ np.where(weak, phi, 0.0)))
    return {
        "D_A": D_A,
        "D_Q": D_Q,
        "D_Q_strong": D_Q_strong,
        "dYe_weak_random_flux": dYe_weak,
        "passes": bool(
            D_A <= 1e-12
            and D_Q <= 1e-12
            and D_Q_strong <= 1e-12
            and (not weak.any() or dYe_weak != 0.0)
        ),
    }
