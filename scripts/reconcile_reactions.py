#!/usr/bin/env python
"""Step 4, Task 1 — extract MESA's softwired reaction sets and diff them
against the pynucastro graphs on the canonical multiset key.

Produces:
  configs/reactions_mesa{80,151}_mesa.yaml        (MESA-side inventory)
  configs/reaction_disposition_mesa{80,151}.yaml  (machine-readable diff)
and prints the canonical counts + disposition tallies for RESULTS.md.

Usage: uv run python scripts/reconcile_reactions.py [--net mesa_80|mesa_151|all]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from gnn_nucleo.crosscheck import (  # noqa: E402
    diff_inventories,
    pyna_inventory,
    run_probe,
    write_disposition,
)
from gnn_nucleo.crosscheck.mesa_dump import dump_to_records, write_inventory  # noqa: E402

CONFIGS = REPO / "configs"


def reconcile(network: str) -> dict:
    net_file = f"{network}.net"
    short = network.replace("_", "")
    print(f"\n=== {network} ===")

    df = run_probe("dump_net", net_file)
    mesa_records = dump_to_records(df)
    write_inventory(
        mesa_records, network, CONFIGS / f"reactions_{short}_mesa.yaml"
    )
    mesa_src = Counter(r["source"] for r in mesa_records)
    print(f"MESA reactions: {len(mesa_records)}  by source: {dict(mesa_src)}")

    pyna_records = pyna_inventory(network)
    pyna_cls = Counter(
        (
            "weaklib" if (r["is_weak"] and r["is_tabular"])
            else "weak_reaclib" if r["is_weak"]
            else "reaclib_reverse" if r["derived_from_inverse"]
            else "reaclib_forward"
        )
        for r in pyna_records
    )
    print(f"pyna reactions: {len(pyna_records)}  by class: {dict(pyna_cls)}")

    doc = diff_inventories(mesa_records, pyna_records, network)
    write_disposition(doc, CONFIGS / f"reaction_disposition_{short}.yaml")
    print(f"tallies: {doc['tallies']}")

    for cls in ("MESA_ONLY", "PYNA_ONLY"):
        keys = [e for e in doc["entries"] if e["disposition"] == cls]
        print(f"{cls} ({len(keys)}):")
        for e in keys[:40]:
            handle = e.get("mesa_handle", e.get("pyna_fname"))
            src = e.get("mesa_source", e.get("pyna_source", ""))
            print(f"  {e['key']:55s} {handle} [{src}]")
        if len(keys) > 40:
            print(f"  ... and {len(keys) - 40} more")
    n_prov = doc["tallies"]["MATCHED_DIFF_PROVENANCE"]
    prov = [e for e in doc["entries"] if e["disposition"] == "MATCHED_DIFF_PROVENANCE"]
    notes = Counter(n.split(":")[0] for e in prov for n in e["notes"])
    print(f"MATCHED_DIFF_PROVENANCE ({n_prov}) note classes: {dict(notes)}")
    return doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", default="all", choices=["mesa_80", "mesa_151", "all"])
    args = ap.parse_args()
    nets = ["mesa_80", "mesa_151"] if args.net == "all" else [args.net]
    for net in nets:
        reconcile(net)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
