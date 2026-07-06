#!/usr/bin/env python3
"""Export the stoichiometric matrix nu, invariant vectors (A, Z), the weak-reaction
mask, and the electron-ledger vector for a pynucastro network.

This is the single source of truth for Component B's fixed conservation layer.
Everything downstream (Target A's dY = nu @ phi, Target B's null-space projection,
the conservation gate in tests/test_conservation.py) reads the .npz written here.

Usage:
    uv run python scripts/export_stoich_matrix.py --net mesa80
    uv run python scripts/export_stoich_matrix.py --isotope-file data/nets/mesa_80.txt

NOTE (verify locally, per docs): the definitive mesa_80 / mesa_151 isotope lists
are in Grichener et al. 2025 Appendix A and in MESA's net data files. The small
built-in list below is a PLACEHOLDER for smoke-testing the pipeline only — do not
size the architecture from it.

The convention exported here:
    nu[i, j]      = net stoichiometric coefficient of species i in reaction j
                    (products positive, reactants negative)
    A[i], Z[i]    = mass and charge number of species i
    weak_mask[j]  = True if reaction j is a weak interaction (EC / beta+/-)
    d_electron[j] = electron-number change of reaction j (EC: -1, beta-: +1, beta+: -1
                    via positron ledger — reviewed below; the conservation test only
                    requires that Z @ nu[:, j] == d_electron[j] for weak columns)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

# Placeholder smoke-test network. Replace with the real mesa_80/151 lists.
SMOKE_NUCLEI = [
    "n", "p", "he4", "c12", "o16", "ne20", "mg24", "si28", "s32",
    "ar36", "ca40", "ti44", "cr48", "fe52", "fe54", "fe56", "ni56",
    "co55", "mn55",
]


def build_network(nuclei: list[str]):
    try:
        import pynucastro as pyna
    except ImportError:
        sys.exit(
            "pynucastro is not installed. Run `uv sync` (it is a project dependency); "
            "never use conda/pip for this project."
        )

    reaclib = pyna.ReacLibLibrary()
    lib = reaclib.linking_nuclei(nuclei)

    # Tabulated weak rates (T, rho*Ye) — required for the Ye-driving channels.
    rates = list(lib.get_rates())
    try:
        tab = pyna.TabularLibrary().linking_nuclei(nuclei)
        # Prefer tabular weak rates over any ReacLib duplicates.
        rc = pyna.RateCollection(rates=rates + list(tab.get_rates()))
    except Exception as exc:  # tabular tables unavailable / API drift
        print(f"[warn] tabular weak rates not loaded ({exc}); continuing with ReacLib only",
              file=sys.stderr)
        rc = pyna.RateCollection(rates=rates)

    # TODO(verify): deduplicate forward/reverse and ReacLib-vs-tabular overlaps the
    # same way MESA r23.05.1 does, so the exported reaction set matches ground truth.
    return rc


def is_weak(rate) -> bool:
    """Heuristic weak-reaction classifier. VERIFY against pynucastro's own labels
    (rate.weak / rate.label / TabularRate type) before production use."""
    if getattr(rate, "weak", False):
        return True
    name = type(rate).__name__.lower()
    if "tabular" in name:
        return True
    label = str(getattr(rate, "label", "")).lower()
    return any(k in label for k in ("ec", "beta", "wc", "weak", "pos_", "electron_capture"))


def export(rc, out_path: Path) -> None:
    nuclei = list(rc.unique_nuclei)
    idx = {n: i for i, n in enumerate(nuclei)}
    rates = list(rc.get_rates())

    n_s, n_r = len(nuclei), len(rates)
    nu = np.zeros((n_s, n_r), dtype=np.float64)
    weak_mask = np.zeros(n_r, dtype=bool)
    d_electron = np.zeros(n_r, dtype=np.float64)

    A = np.array([float(n.A) for n in nuclei])
    Z = np.array([float(n.Z) for n in nuclei])

    for j, rate in enumerate(rates):
        for sp in rate.reactants:
            nu[idx[sp], j] -= 1.0
        for sp in rate.products:
            nu[idx[sp], j] += 1.0
        # Collapse duplicate entries (e.g. triple-alpha lists he4 three times) is
        # handled by the -=/+= accumulation above.

        weak_mask[j] = is_weak(rate)
        if weak_mask[j]:
            # The nuclear-charge change of the column IS the electron-ledger entry;
            # by construction Z @ nu[:, j] == d_electron[j] then closes exactly.
            d_electron[j] = float(Z @ nu[:, j])

    # --- verification before writing (fail loudly, per invariant #1) -------------
    bad = [j for j in range(n_r) if abs(float(A @ nu[:, j])) > 1e-12]
    if bad:
        sys.exit(f"FATAL: baryon-number leak in columns {bad[:10]}... export aborted.")
    bad = [j for j in range(n_r)
           if (not weak_mask[j]) and abs(float(Z @ nu[:, j])) > 1e-12]
    if bad:
        sys.exit(f"FATAL: charge leak in non-weak columns {bad[:10]}... "
                 "either the weak classifier missed them or the network is wrong.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_path,
        nu=nu, A=A, Z=Z, weak_mask=weak_mask, d_electron=d_electron,
        species=np.array([str(n) for n in nuclei]),
        rate_strings=np.array([str(r) for r in rates]),
    )
    print(f"wrote {out_path}: nu is {n_s} species x {n_r} reactions, "
          f"{int(weak_mask.sum())} weak columns")
    print(f"cond(nu) full = {np.linalg.cond(nu):.3e}  "
          "(active-set condition number is a kill-test quantity)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--net", default="smoke", help="label for the output file")
    ap.add_argument("--isotope-file", type=Path, default=None,
                    help="one isotope name per line (e.g. the real mesa_80 list)")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    if args.isotope_file:
        nuclei = [ln.strip() for ln in args.isotope_file.read_text().splitlines()
                  if ln.strip() and not ln.startswith("#")]
    else:
        print("[warn] using built-in SMOKE-TEST nucleus list — not mesa_80. "
              "Provide --isotope-file with the Grichener Appendix A list.",
              file=sys.stderr)
        nuclei = SMOKE_NUCLEI

    out = args.out or Path("data/stoich") / f"nu_{args.net}.npz"
    export(build_network(nuclei), out)


if __name__ == "__main__":
    main()
