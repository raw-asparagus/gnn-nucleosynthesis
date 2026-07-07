#!/usr/bin/env python
"""Regenerate mesa_stub/data/chem_data/isotopes.data (committed for record).

The upstream evaluation reads ``<MESA>/data/chem_data/isotopes.data`` for
per-isotope (name, mass, Z, N). MESA r23.05.1 is not installed in Step 2 and
that file is not in the MESA git tree (release tarball only), so we
reconstruct the needed subset — union of the mesa_80, mesa_151 and approx21
isotope lists — in the same layout their parser expects (one data line per
record, every 4th line starting at line 1). A, Z, N are exact; masses come
from pynucastro (AME) and only affect the Q diagnostic, which is not among
the compared metrics.

Run from the REPO ROOT env (needs pynucastro):
  uv run python repro/nnn/make_isotopes_data.py
"""

from __future__ import annotations

from pathlib import Path

import pynucastro as pyna
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
OUT = HERE / "mesa_stub" / "data" / "chem_data" / "isotopes.data"


def main() -> None:
    names: set[str] = set()
    for cfg in ["isotopes_mesa80.yaml", "isotopes_mesa151.yaml"]:
        spec = yaml.safe_load((REPO / "configs" / cfg).read_text())
        names |= {e["name"] for e in spec["isotopes"]}
    # approx21_cr60_plus_co56 list, read from a shipped test-set header:
    approx21_dir = (REPO / "data" / "zenodo" / "NuclearNeuralNetworks" /
                    "test_datasets" / "mesa_80" / "approx21_output_files")
    header_file = sorted(p for p in approx21_dir.iterdir()
                         if p.name.startswith("output"))[0]
    names |= set(header_file.read_text().splitlines()[0].split()[4:])

    records = []
    for n in sorted(names):
        pyna_name = {"neut": "n", "prot": "p"}.get(n, n)
        nuc = pyna.Nucleus(pyna_name)
        records.append((n, nuc.A_nuc, nuc.Z, nuc.N))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        f.write("reconstructed subset (pynucastro AME masses) in MESA "
                "chem_data/isotopes.data layout\n")
        for name, m, z, nn in records:
            f.write(f"{name:>8s} {m:.7f} {z:4d} {nn:4d}\n0\n0\n0\n")
    print(f"wrote {OUT} ({len(records)} records)")


if __name__ == "__main__":
    main()
