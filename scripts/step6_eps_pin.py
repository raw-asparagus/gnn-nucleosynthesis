#!/usr/bin/env python
"""Step-6 Task 0.1: pin the trajectory-file eps_nuc convention empirically.

The Step-5 open invariant (STEP5_REPORT §3): the trajectory files' eps_nuc
column did not match the flux-route RATE ΣQⱼRⱼ ("off by orders with sign
scatter"). Sourced prior (bbq src/lib_bbq.f90:453):
``out% eps_nuc = avg_eps_nuc * in% time`` — i.e. the column is the
INTEGRATED specific energy release over the row's own dt [erg/g], while
eps_neu is written as a RATE [erg/g/s].

Verdict machinery — per pre-stall output interval k (state k-1 → k over
dt[k]) of every stored trajectory, two engine-independent-to-engine routes:

  composition route  E_comp[k] = −N_A · Σᵢ mᵢ[MeV] · ΔYᵢ · MeV2erg  [erg/g]
      (label ΔX between rows; exact integral, no quadrature error; mᵢ from
       pynucastro atomic masses — the baryon-conservation term cancels)
  flux route         E_flux[k] = trapezoid of ΣⱼQⱼRⱼ · MeV2erg · N_A over dt[k]
      (engine rates; only on RATE-STABLE intervals |Δlog₁₀ rate| < 0.3)

Candidates: {integrated, rate} × {×1, ×1e-16 CSV normalization} × {gross,
net of neutrinos}. Discriminators: median log₁₀(eps_bbq/route) ≈ 0 with
tight IQR, sign agreement ≈ 1, and — decisive for rate-vs-integrated —
STABILITY ACROSS dt DECADES (a wrong convention drifts with slope ±1 in
log dt; the intervals span 1e-10 … ~1e7 s).

Usage: uv run python scripts/step6_eps_pin.py --net mesa_80
"""

from __future__ import annotations

import argparse

import numpy as np


def pin(net: str) -> None:
    from pynucastro.constants import constants

    from gnn_nucleo.data.trajectories import load_trajectory, stall_row
    from gnn_nucleo.fluxes.store import FluxStore
    from gnn_nucleo.graph import load_isotope_table, npz_path

    table = load_isotope_table(net)
    A = table.A.astype(np.float64)
    mass_mev = np.array([n.mass for n in table.nuclei])  # atomic masses [MeV]
    with np.load(npz_path(net), allow_pickle=False) as z:
        Q = z["Q"]

    mev2erg_na = constants.MeV2erg * constants.N_A

    rows = {
        "e_bbq": [],       # file column, verbatim
        "E_comp": [],      # composition route, integrated [erg/g]
        "E_neu": [],       # trapezoid of eps_neu column (rate per source)
        "E_flux": [],      # flux route, integrated [erg/g] (NaN if unstable)
        "dt": [],
        "t9": [],
    }
    n_files = 0
    for chunk in FluxStore(net, "trajectories").iter_chunks():
        traj = load_trajectory(net, chunk.attrs["trajectory_file"])
        if not np.allclose(np.asarray(chunk.attrs["age"]), traj.age):
            raise ValueError(f"{traj.fname}: stored ages != file ages")
        n_files += 1
        n_pre = stall_row(traj.X)
        if n_pre < 3:
            continue
        Y = traj.X / A[None, :]
        e_rate = (Q @ chunk.f_plus) * mev2erg_na  # [erg/g/s] per row
        k = np.arange(1, n_pre)  # interval k: rows k-1 -> k
        dt = traj.age[k] - traj.age[k - 1]
        ok = dt > 0
        k, dt = k[ok], dt[ok]
        rows["e_bbq"].append(traj.eps_nuc_raw[k])
        rows["E_comp"].append(-((Y[k] - Y[k - 1]) @ mass_mev) * mev2erg_na)
        rows["E_neu"].append(0.5 * (traj.eps_neu_raw[k] + traj.eps_neu_raw[k - 1]) * dt)
        e_int = 0.5 * (e_rate[k] + e_rate[k - 1]) * dt
        with np.errstate(divide="ignore", invalid="ignore"):
            unstable = np.abs(np.log10(np.abs(e_rate[k] / e_rate[k - 1]))) > 0.3
        unstable |= np.sign(e_rate[k]) != np.sign(e_rate[k - 1])
        e_int[unstable] = np.nan
        rows["E_flux"].append(e_int)
        rows["dt"].append(dt)
        rows["t9"].append(np.full(len(k), 10.0 ** chunk.attrs["logT"] / 1e9))

    v = {key: np.concatenate(val) for key, val in rows.items()}
    print(f"== {net} eps_nuc convention pin: {n_files} trajectories, "
          f"{v['dt'].size} pre-stall intervals, dt ∈ "
          f"[{v['dt'].min():.1e}, {v['dt'].max():.1e}] s ==")

    candidates = {
        "integrated, gross": v["E_comp"],
        "integrated, net-of-nu": v["E_comp"] - v["E_neu"],
        "rate, gross": v["E_comp"] / v["dt"],
        "rate, net-of-nu": (v["E_comp"] - v["E_neu"]) / v["dt"],
    }
    m0 = np.abs(v["e_bbq"]) > 0
    dt_dec = np.floor(np.log10(v["dt"])).astype(int)
    for name, ref in candidates.items():
        m = m0 & np.isfinite(ref) & (np.abs(ref) > 0)
        r = v["e_bbq"][m] / ref[m]
        sign_ok = float((np.sign(v["e_bbq"][m]) == np.sign(ref[m])).mean())
        lr = np.log10(np.abs(r[r != 0]))
        med, q1, q3 = np.median(lr), np.quantile(lr, 0.25), np.quantile(lr, 0.75)
        # slope of median log-ratio vs dt decade — 0 for the right convention
        decs = np.unique(dt_dec[m])
        med_by_dec = [
            (d, np.median(lr[dt_dec[m] == d]))
            for d in decs
            if (dt_dec[m] == d).sum() >= 20
        ]
        slope = (
            np.polyfit([d for d, _ in med_by_dec], [x for _, x in med_by_dec], 1)[0]
            if len(med_by_dec) >= 3
            else np.nan
        )
        print(
            f"  [{name:<22}] n {m.sum():>6}  median log10|r| {med:+.3f}  "
            f"IQR [{q1:+.3f}, {q3:+.3f}]  sign-agree {sign_ok:.4f}  "
            f"slope vs dt-decade {slope:+.3f}"
        )
    print("  (×1e-16 CSV-normalization variants would shift median log10|r| "
          "by ∓16 — read directly off the medians above)")

    # engine cross-check: flux route vs composition route on stable intervals
    m = m0 & np.isfinite(v["E_flux"]) & (np.abs(v["E_comp"]) > 0)
    rr = v["E_flux"][m] / v["E_comp"][m]
    print(
        f"  engine cross-check E_flux/E_comp (stable intervals, n {m.sum()}): "
        f"median {np.median(rr):.4f}  [p10 {np.quantile(rr, .1):.4f}, "
        f"p90 {np.quantile(rr, .9):.4f}]"
    )
    # and the winning candidate per T9 stratum for the RESULTS row
    ref = candidates["integrated, gross"]
    m = m0 & (np.abs(ref) > 0)
    r = v["e_bbq"][m] / ref[m]
    t9 = v["t9"][m]
    print("  [integrated, gross] ratio by T9:")
    for lo, hi in [(1.6, 3.3), (3.3, 5.0), (5.0, 8.0)]:
        mm = (t9 >= lo) & (t9 < hi)
        if mm.sum() < 10:
            continue
        print(
            f"    T9 [{lo},{hi}): n {mm.sum():>6}  median {np.median(r[mm]):.4f}  "
            f"[p10 {np.quantile(r[mm], .1):.4f}, p90 {np.quantile(r[mm], .9):.4f}]"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--net", required=True, choices=["mesa_80", "mesa_151"])
    args = ap.parse_args()
    pin(args.net)


if __name__ == "__main__":
    main()
