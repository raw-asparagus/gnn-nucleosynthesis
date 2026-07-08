#!/usr/bin/env python3
"""Measured graph/conservation-layer quantities for RESULTS.md.

Usage: uv run python scripts/graph_metrics.py [--net mesa80|mesa151|all]
                                              [--weak-inventory]

Prints, per network: reaction census (per-chapter, weak breakdown,
forward/reverse under both definitions), graph radius/diameter for the
bipartite view with and without I->I intra-reaction edges plus the isotope
projection, implied processor depth K = ceil(radius) + 2, condition numbers
(full nu, extended nu, CC^T), drift metrics, and reproducible artifact
hashes. --weak-inventory additionally lists every weak reaction with its
type, source, and Ye direction.
"""

from __future__ import annotations

import argparse
import json

from gnn_nucleo.graph import build_and_export, content_hash, npz_path
from gnn_nucleo.graph.metrics import (
    condition_numbers,
    drift_metrics,
    graph_extents,
    reaction_census,
    weak_inventory,
)


def report(network: str, show_weak: bool) -> None:
    stoich, info, table, npz, gml = build_and_export(network)
    print(f"== {info.network} ==")
    print(f"species x reactions: {stoich.n_species} x {stoich.n_reactions}")
    print(f"build: {info}")
    print(f"census: {json.dumps(reaction_census(stoich), indent=2)}")
    for name, ext in graph_extents(stoich).items():
        print(f"{name}: radius={ext.radius} diameter={ext.diameter} "
              f"nodes={ext.n_nodes} edges={ext.n_edges} connected={ext.connected} "
              f"implied_K={ext.implied_K}")
    print(f"condition numbers: {json.dumps(condition_numbers(stoich))}")
    print(f"drift: {json.dumps(drift_metrics(stoich))}")
    print(f"npz content sha256: {content_hash(npz_path(network))}")
    if show_weak:
        print("weak inventory (dYe_sign: -1 lowers Ye, +1 raises):")
        for row in weak_inventory(stoich):
            print(f"  {row['dYe_sign']:+d}  {row['weak_type']:<16} "
                  f"{'tab' if row['tabular'] else 'lib':<3} "
                  f"{row['source']:<12} {row['rate']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--net", default="all",
                    choices=["mesa80", "mesa151", "mesa_80", "mesa_151", "all"])
    ap.add_argument("--weak-inventory", action="store_true")
    args = ap.parse_args()

    nets = ["mesa_80", "mesa_151"] if args.net == "all" else [args.net]
    for net in nets:
        report(net, args.weak_inventory)


if __name__ == "__main__":
    main()
