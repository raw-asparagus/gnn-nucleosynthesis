#!/usr/bin/env python
"""Audit the Zenodo training CSVs and write the measured dt grid.

For each network (mesa_80, mesa_151) and each of the nine dt files this
script measures, from the REAL data (never from filenames):

* the actual timestep (``Age`` column; asserted constant per file) and the
  row count;
* row alignment across the nine dt files (identical ``logT``, ``logRho`` and
  sentinel ``initial_*`` columns) — the property that makes the row index a
  valid per-network identity key (``state_id``);
* duplicate counts for the (logT, logRho) pair (NOT unique — rounded to
  3 decimals) and for the full initial state (expected 0);
* the ``final_*`` floor (minimum positive value; expected 1e-15, the floor
  applied by the upstream buildDatabase script);
* eps_nu and eps_nuc magnitude continuity across neighbouring dt files
  (row-exact ratios) — a ~1e3 jump between dt=1e0 and dt=1e1 would expose
  the alternate 1e13 normalization hinted at in the upstream comment
  (python_scripts_for_analysis/TestNNNs/runNNNsOnTestMesa80.py:263).

Outputs ``configs/dt_grid_measured.yaml`` (full-precision measured dt per
network, keyed by the nominal label) and prints RESULTS.md-ready rows.
All numbers are *measured*; provenance Zenodo 14873443.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path

import numpy as np
import pyarrow.csv as pv

REPO = Path(__file__).resolve().parent.parent
TRAINING = REPO / "data/zenodo/NuclearNeuralNetworks/training_sets"
OUT_YAML = REPO / "configs/dt_grid_measured.yaml"

DT_LABELS = ["1e-6", "1e-5", "1e-4", "1e-3", "1e-2", "1e-1", "1e0", "1e1", "1e2"]
NETWORKS = ["mesa_80", "mesa_151"]
# Columns compared across dt files to establish row alignment. h1/he4/si28/
# ni56 span the abundance range; logT/logRho are the state coordinates.
SENTINELS = ["logT", "logRho", "initial_h1", "initial_he4", "initial_si28", "initial_ni56"]
# A jump of this factor between adjacent dt files flags the alternate
# normalization (the hinted discrepancy is 1e16/1e13 = 1e3).
JUMP_FACTOR = 30.0


def csv_path(network: str, label: str) -> Path:
    return TRAINING / network / f"{network}_{label}_sec.csv"


def read_cols(path: Path, cols: list[str]):
    return pv.read_csv(path, convert_options=pv.ConvertOptions(include_columns=cols))


def audit_network(network: str) -> dict:
    res: dict = {"network": network, "dt": {}, "rows": {}}

    # --- measured dt + row count per file ------------------------------
    for label in DT_LABELS:
        t = read_cols(csv_path(network, label), ["Age"])
        ages = np.unique(t.column("Age").to_numpy())
        assert len(ages) == 1, f"{network} {label}: Age not constant ({len(ages)} values)"
        res["dt"][label] = float(ages[0])
        res["rows"][label] = t.num_rows

    # --- row alignment across dt files ---------------------------------
    ref = read_cols(csv_path(network, "1e-6"), SENTINELS)
    aligned = True
    for label in DT_LABELS[1:]:
        t = read_cols(csv_path(network, label), SENTINELS)
        for c in SENTINELS:
            if not np.array_equal(ref.column(c).to_numpy(), t.column(c).to_numpy()):
                aligned = False
                print(f"  MISALIGNED: {network} {label} column {c}")
    res["row_aligned"] = aligned

    # --- duplicate counts (on the 1e-6 file; alignment extends them) ----
    tt = read_cols(csv_path(network, "1e-6"), ["logT", "logRho"])
    pairs = np.rec.fromarrays([tt.column("logT").to_numpy(), tt.column("logRho").to_numpy()])
    res["dup_logT_logRho"] = int(len(pairs) - len(np.unique(pairs)))

    header = pv.open_csv(csv_path(network, "1e-6")).schema.names
    initial_cols = [c for c in header if c.startswith("initial_")]
    res["n_isotopes"] = len(initial_cols)
    full = read_cols(csv_path(network, "1e-6"), ["logT", "logRho"] + initial_cols)
    mat = np.column_stack([full.column(c).to_numpy() for c in ["logT", "logRho"] + initial_cols])
    res["dup_full_state"] = int(mat.shape[0] - np.unique(mat, axis=0).shape[0])

    # --- final_* floor (min positive over all final_ cols, dt=1e-6) -----
    final_cols = [c for c in header if c.startswith("final_")]
    fin = read_cols(csv_path(network, "1e-6"), final_cols)
    fmin = min(float(np.min(fin.column(c).to_numpy())) for c in final_cols)
    res["final_floor"] = fmin

    # --- eps continuity across the dt grid ------------------------------
    eps: dict[str, dict[str, np.ndarray]] = {}
    for label in DT_LABELS:
        t = read_cols(csv_path(network, label), ["eps_nuc", "eps_nu"])
        eps[label] = {c: t.column(c).to_numpy() for c in ["eps_nuc", "eps_nu"]}
    res["eps_ratio"] = {}
    for col in ["eps_nuc", "eps_nu"]:
        ratios = {}
        for a, b in zip(DT_LABELS[:-1], DT_LABELS[1:]):
            x, y = np.abs(eps[a][col]), np.abs(eps[b][col])
            ok = (x > 0) & (y > 0)
            ratios[f"{b}/{a}"] = float(np.median(y[ok] / x[ok]))
        res["eps_ratio"][col] = ratios
    jumps = {
        k: r
        for k, r in res["eps_ratio"]["eps_nu"].items()
        if r > JUMP_FACTOR or r < 1.0 / JUMP_FACTOR
    }
    res["eps_nu_verdict"] = (
        "uniform 1e16 normalization (no discontinuity)" if not jumps else f"ANOMALY: {jumps}"
    )
    res["eps_nu_quarantine"] = sorted({lab for k in jumps for lab in k.split("/")})
    return res


def write_yaml(results: list[dict]) -> None:
    lines = [
        "# Measured per-network dt grid [s] — the actual (constant) Age column of each",
        "# training CSV. Nominal 10^k values are labels only; real steps deviate by up",
        "# to ~5% and differ between networks.",
        f"# derived: scripts/check_training_csvs.py, {_dt.date.today().isoformat()},",
        "#          Zenodo 14873443 (md5 ab31e56950e696aba7747f2cfca2d403)",
    ]
    for r in results:
        lines.append(f"{r['network']}:")
        for label in DT_LABELS:
            lines.append(f'  "{label}": {r["dt"][label]!r}')
    OUT_YAML.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_YAML}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="dump full results as JSON")
    args = ap.parse_args()

    results = []
    for network in NETWORKS:
        print(f"== {network} ==")
        r = audit_network(network)
        results.append(r)
        rows = set(r["rows"].values())
        print(f"  rows per file: {rows} (identical across dt: {len(rows) == 1})")
        print(f"  row-aligned across dt files: {r['row_aligned']}")
        print(f"  (logT,logRho) duplicate rows: {r['dup_logT_logRho']}")
        print(f"  full-initial-state duplicate rows: {r['dup_full_state']}")
        print(f"  n_isotopes: {r['n_isotopes']}")
        print(f"  final_* floor (min value): {r['final_floor']:.3e}")
        for label in DT_LABELS:
            print(f"  dt[{label}] = {r['dt'][label]!r} s")
        for col in ["eps_nuc", "eps_nu"]:
            print(f"  {col} adjacent-dt median |ratio|: {r['eps_ratio'][col]}")
        print(f"  eps_nu verdict: {r['eps_nu_verdict']}")
        if r["eps_nu_quarantine"]:
            print(f"  QUARANTINE eps_nu labels at dt: {r['eps_nu_quarantine']}")

    write_yaml(results)
    if args.json:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
