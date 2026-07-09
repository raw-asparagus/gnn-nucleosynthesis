"""Convert a mesa_probe dump_net DataFrame into the canonical MESA reaction
inventory (configs/reactions_mesa{80,151}_mesa.yaml).

Source attribution per reaction (measured from the probe, not assumed):

* ``weaklib``          — weak reaction with a weaklib table id (>0); the
                         per-pair table source (LMP/OHMT/FFN/GMP) is parsed
                         from $MESA_DIR/data/rates_data/weakreactions.tables.
* ``reaclib_forward``  — direct REACLIB fit (reaclib_fwd_idx > 0).
* ``reaclib_reverse``  — detailed-balance reverse of a REACLIB forward
                         (reaclib_rev_idx > 0).
* ``weak_reaclib``     — weak reaction with no weaklib table; the net uses
                         the raw REACLIB fit (e.g. wc12 beta decays).
* ``other``            — none of the above (flagged, must be explained).
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import yaml

from .canonical import (
    directed_key,
    from_mesa,
    pair_key,
    parse_participants,
    tag_weak_channels,
)
from .probe import mesa_dir


def weaklib_pair_sources(tables_path: Path | None = None) -> dict[tuple[str, str], str]:
    """Parse per-(lhs, rhs) table source labels from weakreactions.tables.

    Entry headers look like ``p    n      by positron emission and electron
    capture; LMP``.  Returns {(lhs, rhs): source_label} with project chem ids.
    """
    if tables_path is None:
        tables_path = mesa_dir() / "data" / "rates_data" / "weakreactions.tables"
    pat = re.compile(
        r"^([a-z]+[0-9]*)\s+([a-z]+[0-9]*)\s+by\s+.*;\s*(\S+)\s*$"
    )
    out: dict[tuple[str, str], str] = {}
    for line in tables_path.read_text().splitlines():
        m = pat.match(line.strip())
        if not m:
            continue
        lhs, rhs, src = m.groups()
        try:
            out[(from_mesa(lhs), from_mesa(rhs))] = src
        except ValueError:
            # 'p'/'n' style names in this file
            special = {"p": "h1", "n": "neut"}
            lhs2 = special.get(lhs, lhs)
            rhs2 = special.get(rhs, rhs)
            out[(from_mesa(lhs2), from_mesa(rhs2))] = src
    if not out:
        raise RuntimeError(f"no weak table headers parsed from {tables_path}")
    return out


def attribute_source(row: pd.Series) -> str:
    if row["is_weak"] == 1 and row["weaklib_id"] > 0:
        return "weaklib"
    if row["is_weak"] == 1:
        return "weak_reaclib"
    if row["reaclib_rev_idx"] > 0:
        return "reaclib_reverse"
    if row["reaclib_fwd_idx"] > 0:
        return "reaclib_forward"
    return "other"


def dump_to_records(df: pd.DataFrame) -> list[dict]:
    """Canonicalize a dump_net DataFrame into inventory records."""
    weak_sources = weaklib_pair_sources()
    records: list[dict] = []
    for _, row in df.iterrows():
        reactants = parse_participants(row["inputs"])
        products = parse_participants(row["outputs"])
        key = directed_key(reactants, products)
        source = attribute_source(row)
        rec: dict = {
            "mesa_handle": row["name"],
            "key": key,
            "pair_key": pair_key(key),
            "category": row["category"] if isinstance(row["category"], str) else "",
            "q_mev": float(row["q"]),
            "qneu_mev": float(row["qneu"]),
            "source": source,
            "is_weak": bool(row["is_weak"]),
        }
        if source == "weaklib":
            lhs = from_mesa(str(row["weak_lhs"]))
            rhs = from_mesa(str(row["weak_rhs"]))
            rec["weak_table_source"] = weak_sources.get((lhs, rhs), "UNKNOWN")
        records.append(rec)
    tag_weak_channels(
        records,
        lambda r: "ec" if "_ec_" in r["mesa_handle"] else "wk",
    )
    return records


def write_inventory(records: list[dict], network: str, out_path: Path) -> None:
    doc = {
        "network": network,
        "generator": "scripts/reconcile_reactions.py (mesa_probe dump_net)",
        "mesa_version": "r23.05.1",
        "n_reactions": len(records),
        "reactions": records,
    }
    out_path.write_text(yaml.safe_dump(doc, sort_keys=False, width=100))
