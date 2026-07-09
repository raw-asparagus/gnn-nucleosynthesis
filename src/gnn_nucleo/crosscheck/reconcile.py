"""Reaction-set reconciliation: MESA softwired nets vs pynucastro graphs.

Dispositions (exactly one per union directed key; ADR 0002 / Step-4 brief):

* ``MESA_ONLY``               — physics in the labels the graph lacks.
* ``PYNA_ONLY``               — phantom channel in the graph.
* ``MATCHED_DIFF_PROVENANCE`` — same link, different construction
                                (rate source, reverse method, weak table).
* ``MATCHED_CLEAN``           — same link, same construction class.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from gnn_nucleo.graph import build_rate_collection, load_isotope_table

from .canonical import directed_key, from_pyna, pair_key, tag_weak_channels

DISPOSITIONS = (
    "MESA_ONLY",
    "PYNA_ONLY",
    "MATCHED_DIFF_PROVENANCE",
    "MATCHED_CLEAN",
)

#: MESA weaklib entry labels -> pynucastro tabular source labels
WEAK_TABLE_MAP = {
    "LMP": "langanke",
    "OHMT": "oda",
    "FFN": "ffn",
    # GMP (Martinez-Pinedo private communication) has no pynucastro analogue
}


def pyna_inventory(network: str) -> list[dict]:
    """Canonical inventory of the RAW pynucastro rate collection.

    disposition=None on purpose: the disposition file is defined as the diff
    between the raw pynucastro set and MESA; building with the disposition
    applied here would make reconciliation self-erasing.
    """
    table = load_isotope_table(network)
    rc, info = build_rate_collection(table, disposition=None)
    records: list[dict] = []
    for rate in rc.get_rates():
        reactants = [from_pyna(n) for n in rate.reactants]
        products = [from_pyna(n) for n in rate.products]
        key = directed_key(reactants, products)
        import pynucastro as pyna  # local import: heavy

        is_tabular = isinstance(rate, pyna.rates.TabularRate)
        rec = {
            "fname": rate.fname,
            "key": key,
            "pair_key": pair_key(key),
            "q_mev": float(rate.Q),
            "is_weak": bool(getattr(rate, "weak", False)),
            "is_tabular": bool(is_tabular),
            "derived_from_inverse": bool(
                getattr(rate, "derived_from_inverse", False)
            ),
            "source_label": str(
                (getattr(rate, "source", None) or {}).get("Label", "")
            ),
        }
        rec["weak_type"] = str(getattr(rate, "weak_type", "") or "")
        records.append(rec)
    tag_weak_channels(
        records,
        lambda r: "ec" if r["weak_type"] == "electron_capture" else "wk",
    )
    return records


def _mesa_class(rec: dict) -> str:
    return rec["source"]


def _pyna_class(rec: dict) -> str:
    if rec["is_weak"] and rec["is_tabular"]:
        return "weaklib"
    if rec["is_weak"]:
        return "weak_reaclib"
    if rec["derived_from_inverse"]:
        return "reaclib_reverse"
    return "reaclib_forward"


def _provenance_notes(mesa: dict, pyna_rec: dict) -> list[str]:
    notes: list[str] = []
    mc, pc = _mesa_class(mesa), _pyna_class(pyna_rec)
    if mc != pc:
        notes.append(f"construction: mesa={mc} pyna={pc}")
    if mc == "weaklib" and pc == "weaklib":
        mesa_src = mesa.get("weak_table_source", "UNKNOWN")
        pyna_src = pyna_rec["source_label"]
        if WEAK_TABLE_MAP.get(mesa_src) != pyna_src:
            notes.append(f"weak table: mesa={mesa_src} pyna={pyna_src}")
    return notes


def diff_inventories(
    mesa_records: list[dict], pyna_records: list[dict], network: str
) -> dict:
    """Produce the machine-readable disposition document."""
    mesa_by_key = {r["key"]: r for r in mesa_records}
    pyna_by_key = {r["key"]: r for r in pyna_records}
    entries: list[dict] = []
    for key in sorted(set(mesa_by_key) | set(pyna_by_key)):
        m = mesa_by_key.get(key)
        p = pyna_by_key.get(key)
        if m is not None and p is not None:
            notes = _provenance_notes(m, p)
            disposition = "MATCHED_DIFF_PROVENANCE" if notes else "MATCHED_CLEAN"
            entry = {
                "key": key,
                "disposition": disposition,
                "mesa_handle": m["mesa_handle"],
                "pyna_fname": p["fname"],
            }
            if notes:
                entry["notes"] = notes
        elif m is not None:
            entry = {
                "key": key,
                "disposition": "MESA_ONLY",
                "mesa_handle": m["mesa_handle"],
                "mesa_source": m["source"],
            }
        else:
            assert p is not None
            entry = {
                "key": key,
                "disposition": "PYNA_ONLY",
                "pyna_fname": p["fname"],
                "pyna_source": p["source_label"],
            }
        entries.append(entry)

    tallies = {d: 0 for d in DISPOSITIONS}
    for e in entries:
        tallies[e["disposition"]] += 1
    doc = {
        "network": network,
        "convention": (
            "directed key = sorted reactant/product multisets in project chem "
            "ids; forward and reverse are distinct reactions on both sides"
        ),
        "n_mesa": len(mesa_records),
        "n_pyna": len(pyna_records),
        "tallies": tallies,
        "entries": entries,
    }
    validate_disposition(doc)
    return doc


def validate_disposition(doc: dict) -> None:
    """Schema check: every union key appears exactly once with exactly one
    valid disposition, and the tallies are consistent."""
    entries = doc["entries"]
    keys = [e["key"] for e in entries]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate keys in disposition entries")
    tallies = {d: 0 for d in DISPOSITIONS}
    for e in entries:
        d = e["disposition"]
        if d not in DISPOSITIONS:
            raise ValueError(f"invalid disposition {d!r} for {e['key']}")
        tallies[d] += 1
    if tallies != doc["tallies"]:
        raise ValueError("tallies do not match entries")
    n_matched = tallies["MATCHED_CLEAN"] + tallies["MATCHED_DIFF_PROVENANCE"]
    if n_matched + tallies["MESA_ONLY"] != doc["n_mesa"]:
        raise ValueError("MESA side count mismatch")
    if n_matched + tallies["PYNA_ONLY"] != doc["n_pyna"]:
        raise ValueError("pynucastro side count mismatch")


def write_disposition(doc: dict, out_path: Path) -> None:
    out_path.write_text(yaml.safe_dump(doc, sort_keys=False, width=100))


def load_disposition(path: Path) -> dict:
    doc = yaml.safe_load(path.read_text())
    validate_disposition(doc)
    return doc
