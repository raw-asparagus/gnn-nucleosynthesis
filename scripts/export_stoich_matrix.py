#!/usr/bin/env python3
"""Export the stoichiometric matrix ν, constraint matrix C, lepton ledgers,
and the bipartite reaction graph for a project network.

Thin CLI over the canonical implementation in ``gnn_nucleo.graph`` (the
single source of truth for the fixed conservation layer; see
src/gnn_nucleo/graph/). Artifacts land in data/stoich/ (npz) and
data/graphs/ (graphml), both regenerable and gitignored; the reproducible
content hash printed here is what RESULTS.md records.

Usage:
    uv run python scripts/export_stoich_matrix.py --net mesa80
    uv run python scripts/export_stoich_matrix.py --net mesa151
"""

from __future__ import annotations

import argparse

from gnn_nucleo.graph import build_and_export, content_hash, sha256_of


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--net", required=True, choices=["mesa80", "mesa151", "mesa_80", "mesa_151"])
    args = ap.parse_args()

    stoich, info, table, npz, gml = build_and_export(args.net)

    print(
        f"{info.network}: {stoich.n_species} species x {stoich.n_reactions} reactions "
        f"({info.n_reaclib} ReacLib + {info.n_tabular} tabular, "
        f"{info.n_duplicate_groups_resolved} duplicate links resolved tabular-wins), "
        f"{int(stoich.weak_mask.sum())} weak columns"
    )
    print(
        f"provisional_reaction_set={info.provisional_reaction_set} "
        f"(pynucastro {info.pynucastro_version}, tabular ordering "
        f"{'<'.join(info.tabular_ordering)}; Step-4 MESA cross-check pending)"
    )
    print(f"wrote {npz}  (content sha256 {content_hash(npz)})")
    print(f"wrote {gml}  (file sha256 {sha256_of(gml)})")


if __name__ == "__main__":
    main()
