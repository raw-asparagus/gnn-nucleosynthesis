"""Step-4 Task-2 rate-level comparison: MESA (label configuration) vs
pynucastro 2.12.0, bare rates first, weak sector in detail, screening last.

Comparison bands (stated + justified in docs/rate-crosscheck.md):

* ``reaclib_forward`` MATCHED_CLEAN:      |dlog10| <= 0.004 (~1%) — same
  REACLIB lineage; anything beyond it is a snapshot refit or a harness bug.
* ``reaclib_reverse`` (DB inverses):      |dlog10| <= 0.05 — partition
  function provenance and nuclide-mass tables differ between MESA winvn
  and pynucastro; both are smooth O(few %) effects in the box.
* construction-swapped pairs + snapshot refits: reported separately,
  no hard band (REACLIB 20171020 vs pynucastro 2.12.0 snapshot).
* weak tabular:                            |dlog10| <= 0.1 — same source
  tables after ADR 0003, but interpolation schemes differ (MESA bilinear
  in log lambda on the shipped grid vs pynucastro's interpolant).
* Appendix-B channels: excluded from all gates
  (configs/appendixb_excluded_channels.yaml), verified against 24.08.1.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .canonical import from_mesa
from .mesa_dump import dump_to_records
from .probe import run_probe, t9_stdin

BAND_FORWARD = 0.004
BAND_REVERSE = 0.05
BAND_WEAK = 0.1

_REPO = Path(__file__).resolve().parents[3]


def load_disposition_index(network: str) -> dict[str, str]:
    """{canonical key: disposition} from the committed disposition file."""
    short = network.replace("_", "")
    doc = yaml.safe_load(
        (_REPO / "configs" / f"reaction_disposition_{short}.yaml").read_text()
    )
    return {e["key"]: e["disposition"] for e in doc["entries"]}


def load_appendixb_handles(network: str) -> frozenset[str]:
    doc = yaml.safe_load(
        (_REPO / "configs" / "appendixb_excluded_channels.yaml").read_text()
    )
    return frozenset(c["mesa_handle"] for c in doc["networks"][network])


def mesa_reaclib_table(network: str, t9s) -> pd.DataFrame:
    """MESA raw rates (screening off, T-only) joined with dump_net metadata
    and canonical keys."""
    dump = run_probe("dump_net", f"{network}.net")
    records = dump_to_records(dump)
    meta = pd.DataFrame(
        {
            "name": [r["mesa_handle"] for r in records],
            "key": [r["key"] for r in records],
            "source": [r["source"] for r in records],
            "is_weak": [r["is_weak"] for r in records],
        }
    )
    rates = run_probe("eval_rates", f"{network}.net", stdin_text=t9_stdin(t9s))
    return rates.merge(meta, on="name", validate="many_to_one")


def pyna_reaclib_values(network: str, t9s) -> pd.DataFrame:
    """pynucastro non-tabular rate values per canonical key x T9."""
    import pynucastro as pyna

    from gnn_nucleo.graph import build_rate_collection, load_isotope_table

    from .reconcile import pyna_inventory

    key_by_fname = {r["fname"]: r["key"] for r in pyna_inventory(network)}
    rc, _ = build_rate_collection(load_isotope_table(network), disposition=None)
    rows = []
    for rate in rc.get_rates():
        if isinstance(rate, pyna.rates.TabularRate):
            continue
        for t9 in t9s:
            try:
                v = float(rate.eval(t9 * 1e9))
            except Exception:
                v = np.nan
            rows.append({"key": key_by_fname[rate.fname], "t9": t9, "pyna_rate": v})
    return pd.DataFrame(rows)


def compare_bare(network: str, t9s) -> pd.DataFrame:
    """Joined bare-rate comparison with dlog10 and per-row category."""
    mesa = mesa_reaclib_table(network, t9s)
    pyna = pyna_reaclib_values(network, t9s)
    df = mesa.merge(pyna, on=["key", "t9"], how="inner")
    disp = load_disposition_index(network)
    appb = load_appendixb_handles(network)
    df["disposition"] = df["key"].map(disp)
    with np.errstate(divide="ignore", invalid="ignore"):
        df["dlog10"] = np.log10(df["raw_rate"]) - np.log10(df["pyna_rate"])

    def category(row) -> str:
        if row["name"] in appb:
            return "appendixb_excluded"
        if row["disposition"] == "MATCHED_DIFF_PROVENANCE":
            return "construction_swap"
        if row["is_weak"]:
            return "weak_reaclib"
        if row["source"] == "reaclib_reverse":
            return "db_inverse"
        if row["source"] == "reaclib_forward":
            return "reaclib_forward"
        return "other"

    df["category"] = df.apply(category, axis=1)
    return df


def band_for(category: str) -> float | None:
    return {
        "reaclib_forward": BAND_FORWARD,
        "db_inverse": BAND_REVERSE,
        "weak_reaclib": BAND_REVERSE,
        "weak_tabular": BAND_WEAK,
    }.get(category)


def summarize(df: pd.DataFrame, value: str = "dlog10") -> pd.DataFrame:
    """Per-category |dlog10| distribution + outlier counts vs bands."""
    rows = []
    for cat, sub in df.groupby("category"):
        a = sub[value].abs().dropna()
        band = band_for(cat)
        rows.append(
            {
                "category": cat,
                "n_channels": sub["key"].nunique(),
                "n_evals": len(a),
                "median": a.median(),
                "p95": a.quantile(0.95),
                "p99": a.quantile(0.99),
                "max": a.max(),
                "band": band if band is not None else np.nan,
                "n_beyond_band": int((a > band).sum()) if band else -1,
            }
        )
    return pd.DataFrame(rows).sort_values("category")


def weak_composition(ye: float):
    """The probe's piecewise ni56/fe56/neut mix as a pynucastro Composition."""
    import pynucastro as pyna

    ye1, ye2 = 28.0 / 56.0, 26.0 / 56.0
    comp = pyna.Composition(["ni56", "fe56", "n"])
    if ye >= ye2:
        x_ni = (ye - ye2) / (ye1 - ye2)
        xs = {"Ni56": x_ni, "Fe56": 1.0 - x_ni, "n": 0.0}
    else:
        xs = {"Ni56": 0.0, "Fe56": ye / ye2, "n": 1.0 - ye / ye2}
    for nuc in comp.X:
        comp.X[nuc] = xs[str(nuc)]
    return comp


def pyna_weak_values(network: str, states) -> pd.DataFrame:
    """pynucastro tabular + weak reaclib rates over the (T9, rho, ye) grid."""
    import pynucastro as pyna

    from gnn_nucleo.graph import build_rate_collection, load_isotope_table

    from .reconcile import pyna_inventory

    key_by_fname = {r["fname"]: r["key"] for r in pyna_inventory(network)}
    rc, _ = build_rate_collection(load_isotope_table(network), disposition=None)
    rows = []
    comps = {}
    for rate in rc.get_rates():
        if not getattr(rate, "weak", False):
            continue
        tab = isinstance(rate, pyna.rates.TabularRate)
        for t9, rho, ye in states:
            if ye not in comps:
                comps[ye] = weak_composition(ye)
            try:
                v = float(rate.eval(t9 * 1e9, rho=rho, comp=comps[ye]))
            except Exception:
                v = np.nan
            rows.append(
                {
                    "key": key_by_fname[rate.fname],
                    "t9": t9,
                    "rho": rho,
                    "ye": ye,
                    "pyna_rate": v,
                    "pyna_tabular": tab,
                    "pyna_source": (getattr(rate, "source", None) or {}).get(
                        "Label", ""
                    ),
                }
            )
    return pd.DataFrame(rows)


def mesa_weak_table(network: str, states) -> pd.DataFrame:
    from .probe import grid_stdin

    dump = run_probe("dump_net", f"{network}.net")
    records = dump_to_records(dump)
    key_by_name = {r["mesa_handle"]: r["key"] for r in records}
    src_by_name = {r["mesa_handle"]: r.get("weak_table_source", "") for r in records}
    df = run_probe("eval_weak", f"{network}.net", stdin_text=grid_stdin(states))
    df["key"] = df["name"].map(key_by_name)
    df["mesa_table_source"] = df["name"].map(src_by_name)
    # the rate the net actually uses: weaklib lambda when a table exists
    # (T9 >= 1.6 >> blend range), else the raw reaclib rate
    df["mesa_rate"] = np.where(df["weaklib_id"] > 0, df["lambda_weaklib"], df["raw_reaclib_rate"])
    df["mesa_is_weaklib"] = df["weaklib_id"] > 0
    return df


def compare_screening(network: str, states) -> pd.DataFrame:
    """MESA chugunov screen factors (as bbq/net would apply them) vs
    pynucastro chugunov_2007 / chugunov_2009 on identical plasma states.

    The probe reports the per-reaction factor (two-stage product for
    triples); the pynucastro side mirrors that construction exactly,
    including the neutron-swap rules from net_screen.f90.
    """
    from pynucastro import Nucleus
    from pynucastro.screening import (
        ScreenFactors,
        chugunov_2007,
        chugunov_2009,
        make_plasma_state,
    )

    from gnn_nucleo.graph import load_isotope_table

    from .probe import grid_stdin

    table = load_isotope_table(network)
    za = {n: (int(z), int(a)) for n, z, a in zip(table.names, table.Z, table.A)}

    df = run_probe(
        "eval_screen", f"{network}.net", stdin_text=grid_stdin(states),
        screening="chugunov",
    )

    class _FakeNuc:
        """Composite (A1+A2, Z1+Z2) pseudo-nucleus for the two-stage triple."""

        def __init__(self, z: float, a: float):
            self.Z = z
            self.A = a

    def molar_fractions(x_ni, x_fe, x_n):
        return {
            Nucleus("ni56"): x_ni / 56.0,
            Nucleus("fe56"): x_fe / 56.0,
            Nucleus("n"): x_n / 1.0,
        }

    states_cache: dict[tuple, object] = {}
    rows = []
    for r in df.itertuples():
        skey = (r.t9, r.rho, r.x_ni56, r.x_fe56, r.x_neut)
        if skey not in states_cache:
            states_cache[skey] = make_plasma_state(
                r.t9 * 1e9, r.rho, molar_fractions(r.x_ni56, r.x_fe56, r.x_neut)
            )
        state = states_cache[skey]

        isos = [r.scr_iso_1, r.scr_iso_2]
        if isinstance(r.scr_iso_3, str) and r.scr_iso_3.strip():
            isos.append(r.scr_iso_3)
        nucs = []
        for iso in isos:
            z, a = za[from_mesa(iso)]
            nucs.append(_FakeNuc(float(z), float(a)))

        def factor(fn, nucs=nucs, state=state):
            # pynucastro screening functions return ln(scor), not the
            # factor (verified against pynucastro/screening/screen.py:
            # chugunov_2007 returns log_scor) — exponentiate to compare
            # with MESA's scor.
            if len(nucs) == 2:
                n1, n2 = nucs
                if n1.Z == 0 or n2.Z == 0:
                    return 1.0
                return float(
                    np.exp(fn(state, ScreenFactors(n1.Z, n1.A, n2.Z, n2.A)))
                )
            n1, n2, n3 = nucs
            # mirror net_screen.f90: move a neutron (Z=0) to the front,
            # screen (2,3) then (1, 2+3)
            if n2.Z == 0:
                if n1.Z == 0:
                    return 1.0
                n1, n2 = n2, n1
            if n3.Z == 0:
                n1, n3 = n3, n1
            h23 = fn(state, ScreenFactors(n2.Z, n2.A, n3.Z, n3.A))
            if n1.Z == 0:
                return float(np.exp(h23))
            h1_23 = fn(
                state, ScreenFactors(n1.Z, n1.A, n2.Z + n3.Z, n2.A + n3.A)
            )
            return float(np.exp(h23 + h1_23))

        rows.append(
            {
                "network": network,
                "t9": r.t9,
                "rho": r.rho,
                "ye": r.ye,
                "name": r.name,
                "mesa_scor": r.scor,
                "pyna_2007": factor(chugunov_2007),
                "pyna_2009": factor(chugunov_2009),
            }
        )
    out = pd.DataFrame(rows)
    out["ratio_2007"] = out["mesa_scor"] / out["pyna_2007"]
    out["ratio_2009"] = out["mesa_scor"] / out["pyna_2009"]
    return out


def compare_weak(network: str, states) -> pd.DataFrame:
    mesa = mesa_weak_table(network, states)
    pyna = pyna_weak_values(network, states)
    df = mesa.merge(pyna, on=["key", "t9", "rho", "ye"], how="inner")
    with np.errstate(divide="ignore", invalid="ignore"):
        df["dlog10"] = np.log10(df["mesa_rate"]) - np.log10(df["pyna_rate"])
    df["category"] = np.where(
        df["mesa_is_weaklib"] & df["pyna_tabular"],
        "weak_tabular",
        np.where(
            ~df["mesa_is_weaklib"] & ~df["pyna_tabular"],
            "weak_reaclib",
            "weak_provenance_mismatch",  # be7 class
        ),
    )
    return df
