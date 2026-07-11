#!/usr/bin/env python
"""Generate the Step-6 bbq rerun campaign: run directories + manifest.

Mode: bbq ``use_hydrostatic`` with ``times_from_file`` — the mode that
produced the shipped test trajectories (header/format identical,
lib_hydrostatic.f90), the only mode with both composition carry-over and
per-row eps_nuc, and exact cadence control per line. Each ``times.txt`` line
is a per-step burn DURATION; we generate a log-spaced age grid (default 40
points/decade from 1e-8 s, dt additionally capped) — directly preventing the
shipped-data stall mechanism (output dt grown to ~1e10 s; RESULTS.md
2026-07-10).

Composition families per (T9, rho, Ye) cell of the kill-test grid:
  shipped    row-0 state of each Step-5 selected shipped trajectory, run at
             the file's EXACT (logT, logRho) — early-time comparability.
  canonical  Si-burning-like two-isotope mixes solving Sum X_i Z_i/A_i = Ye:
             si28+si30 for Ye >= 0.46667, si30+ne22 below; the network floor
             over sensible (A >= 12 abundant) species is ne22's Z/A = 0.45455,
             so the Ye = 0.45 target is SUBSTITUTED by 0.455 (recorded in the
             manifest; Ye = 0.45 proper is covered by the sobol family).
  sobol      nearest training-grid states per cell (state_ids persisted in
             the manifest — join discipline, CLAUDE.md).

Layout: data/bbq_reruns/<net>/<run_key>/{inlist,times.txt,comp.txt} +
data/bbq_reruns/<net>/campaign.yaml. Guard step 0: a bbq write_iso_list probe
per network must match the project isotope table before anything is written.

Usage:
  uv run python scripts/bbq_campaign/make_campaign.py --net both
"""

from __future__ import annotations

import argparse
import datetime
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

# kill-test grid (scripts/run_killtest.py), priority order: QSE window first
T9_PRIORITY = [3.3, 4.0, 5.0, 6.3, 2.5, 1.6, 7.9]
LOGRHO = [7.0, 8.0, 9.0]
YE_TARGETS = [0.45, 0.48, 0.498]
AGE_START = 1e-8

# family-2 mixing basis: (name, Z/A); si28+si30 above the si30 ratio,
# si30+ne22 below; floor = ne22 (see module docstring)
ZA = {"si28": 14.0 / 28.0, "si30": 14.0 / 30.0, "ne22": 10.0 / 22.0}
YE_FLOOR_SUBSTITUTE = 0.455


def t_end_for(t9: float) -> float:
    if t9 >= 5.0:
        return 1e4
    if t9 >= 3.3:
        return 1e6
    return 1e8


def make_times(t_end: float, ppd: int, dt_cap: float) -> np.ndarray:
    """Per-step durations: log-spaced ages (ppd points/decade) from
    AGE_START, each dt additionally capped at dt_cap."""
    f = 10.0 ** (1.0 / ppd)
    ages = [AGE_START]
    while ages[-1] < t_end:
        dt = min(ages[-1] * (f - 1.0), dt_cap)
        ages.append(ages[-1] + dt)
    ages = np.array(ages)
    return np.diff(ages, prepend=0.0)


def canonical_mix(ye: float) -> tuple[dict[str, float], float]:
    """Two-isotope mass-fraction mix hitting Ye (or the floor substitute).
    Returns (mix, ye_actual)."""
    if ye >= ZA["si30"]:
        a, b = "si28", "si30"
    else:
        a, b = "si30", "ne22"
        if ye < ZA["ne22"]:
            ye = YE_FLOOR_SUBSTITUTE
    x_b = (ZA[a] - ye) / (ZA[a] - ZA[b])
    if not 0.0 <= x_b <= 1.0:
        raise ValueError(f"Ye={ye} not reachable with ({a},{b})")
    return {a: 1.0 - x_b, b: x_b}, ye


def iso_order_guard(net: str) -> None:
    """Run bbq write_iso_list and assert net_iso order == isotope table."""
    from gnn_nucleo.graph import load_isotope_table

    table = load_isotope_table(net)
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "inlist").write_text(
            f"&bbq\n net_name = '{net}.net'\n just_write_isos = .true.\n"
            " write_iso_list = .true.\n iso_list_filename = 'isos.txt'\n/\n"
            "&sampling /\n&random /\n&profile /\n&hydrostatic /\n"
            "&eos /\n&rates /\n&nuclear /\n"
        )
        r = subprocess.run(["bash", str(HERE / "run_one.sh"), td], timeout=600)
        if r.returncode != 0:
            raise RuntimeError(f"bbq iso probe failed for {net} (see {td}/run.log)")
        isos = (Path(td) / "isos.txt").read_text().split()
    if isos != list(table.names):
        diff_at = next(
            i for i, (a, b) in enumerate(zip(isos, table.names)) if a != b
        )
        raise RuntimeError(
            f"{net}: bbq net_iso order != isotope table (first diff at {diff_at})"
        )
    print(f"{net}: iso-order guard OK ({len(isos)} species)")


def shipped_family(net: str) -> list[dict]:
    from gnn_nucleo.data.trajectories import load_trajectory

    spec = yaml.safe_load(
        (REPO / "configs" / f"step5_subsample_{net}.yaml").read_text()
    )
    runs = []
    for fname in spec["trajectories"]:
        traj = load_trajectory(net, fname)
        t9 = 10.0**traj.logT / 1e9
        runs.append(
            dict(
                run_key=f"f1_{Path(fname).stem.removeprefix('output_')}",
                family="shipped",
                logT=traj.logT,
                logRho=traj.logRho,
                t9=round(t9, 4),
                ye_target=None,
                ye_actual=None,  # filled from X below
                comp_source=fname,
                X0=traj.X[0].tolist(),
            )
        )
    return runs


def canonical_family(net: str) -> list[dict]:
    runs = []
    for t9 in T9_PRIORITY:
        for lr in LOGRHO:
            for ye in YE_TARGETS:
                mix, ye_act = canonical_mix(ye)
                runs.append(
                    dict(
                        run_key=f"f2_T{t9}_r{lr:.0f}_ye{ye}",
                        family="canonical",
                        logT=float(round(np.log10(t9 * 1e9), 4)),
                        logRho=lr,
                        t9=t9,
                        ye_target=ye,
                        ye_actual=round(ye_act, 6),
                        comp_source="+".join(
                            f"{k}:{v:.6f}" for k, v in mix.items()
                        ),
                        mix=mix,
                    )
                )
    return runs


def sobol_family(net: str, per_cell: int = 2) -> list[dict]:
    import pyarrow.csv as pv

    from gnn_nucleo.data.labels import training_csv_path
    from gnn_nucleo.data.subsample import compute_ye_initial
    from gnn_nucleo.graph import load_isotope_table

    table = load_isotope_table(net)
    cols = ["logT", "logRho"] + [f"initial_{n}" for n in table.names]
    t = pv.read_csv(
        training_csv_path(net, "1e-6"),
        convert_options=pv.ConvertOptions(include_columns=cols),
    )
    logT = t.column("logT").to_numpy()
    logRho = t.column("logRho").to_numpy()
    X = np.column_stack([t.column(f"initial_{n}").to_numpy() for n in table.names])
    ye = compute_ye_initial(X, table.Z.astype(float), table.A.astype(float))

    runs = []
    for t9 in T9_PRIORITY:
        lt = np.log10(t9 * 1e9)
        for lr in LOGRHO:
            for ye_t in YE_TARGETS:
                d = (
                    ((logT - lt) / 0.7) ** 2
                    + ((logRho - lr) / 2.0) ** 2
                    + ((ye - ye_t) / 0.05) ** 2
                )
                nearest = np.argsort(d)[:per_cell]
                for k, sid in enumerate(nearest):
                    runs.append(
                        dict(
                            run_key=f"f3_T{t9}_r{lr:.0f}_ye{ye_t}_{k}",
                            family="sobol",
                            logT=float(round(lt, 4)),
                            logRho=lr,
                            t9=t9,
                            ye_target=ye_t,
                            ye_actual=float(round(float(ye[sid]), 6)),
                            comp_source=f"state_id:{int(sid)}",
                            state_id=int(sid),
                            X0=X[sid].tolist(),
                        )
                    )
    return runs


PILOT_KEYS_F2 = [
    f"f2_T{t9}_r{lr:.0f}_ye0.48" for t9 in (3.3, 5.0) for lr in (7.0, 9.0)
]


def build(net: str, root: Path, ppd: int, dt_cap: float) -> None:
    from gnn_nucleo.graph import load_isotope_table

    iso_order_guard(net)
    table = load_isotope_table(net)
    Z = table.Z.astype(float)
    A = table.A.astype(float)
    names = list(table.names)
    idx = {n: i for i, n in enumerate(names)}

    runs = shipped_family(net) + canonical_family(net) + sobol_family(net)

    # pilot = 4 canonical cells + the shipped run nearest (logT 9.6, logRho 8)
    shipped = [r for r in runs if r["family"] == "shipped"]
    d = [(abs(r["logT"] - 9.6) + abs(r["logRho"] - 8.0), r["run_key"]) for r in shipped]
    pilot_keys = set(PILOT_KEYS_F2) | {min(d)[1]}

    prio_rank = {t9: i for i, t9 in enumerate(T9_PRIORITY)}
    fam_rank = {"shipped": 0, "canonical": 1, "sobol": 2}

    net_dir = root / net
    net_dir.mkdir(parents=True, exist_ok=True)
    template = (HERE / "inlist.template").read_text()

    manifest_runs = []
    for r in runs:
        # composition vector in net_iso order
        X0 = np.zeros(len(names))
        if "mix" in r:
            for iso, x in r["mix"].items():
                X0[idx[iso]] = x
        else:
            X0[:] = np.asarray(r.pop("X0"))
        s = X0.sum()
        if not 0.999 <= s <= 1.001:
            raise ValueError(f"{r['run_key']}: sum X = {s}")
        X0 /= s
        ye_act = float(X0 @ (Z / A))
        if r["ye_actual"] is None:
            r["ye_actual"] = round(ye_act, 6)

        t_end = t_end_for(r["t9"])
        times = make_times(t_end, ppd, dt_cap)

        rd = net_dir / r["run_key"]
        rd.mkdir(exist_ok=True)
        (rd / "inlist").write_text(
            template.format(net=net, logT=r["logT"], logRho=r["logRho"])
        )
        np.savetxt(rd / "times.txt", times, fmt="%.16e")
        np.savetxt(rd / "comp.txt", X0, fmt="%.16e")

        # shipped-family t9 values are file-exact, not grid members: rank by
        # the nearest grid T9
        nearest_t9 = min(T9_PRIORITY, key=lambda g: abs(g - r["t9"]))
        r.pop("mix", None)
        r.update(
            n_times=int(len(times)),
            t_end=t_end,
            pilot=r["run_key"] in pilot_keys,
            priority=prio_rank[nearest_t9] * 10 + fam_rank[r["family"]],
        )
        manifest_runs.append(r)

    manifest = dict(
        network=net,
        generated=datetime.date.today().isoformat(),
        code="scripts/bbq_campaign/make_campaign.py",
        mesa_dir="~/mesa-r23.05.1 (stock; gh-575 channels excluded from "
        "conclusions per ADR 0005)",
        bbq="~/bbq (github.com/rjfarmer/bbq)",
        config="chugunov screening, weaklib defaults, eps=1d-8, odescal=1d-10",
        points_per_decade=ppd,
        dt_cap_seconds=dt_cap,
        age_start_seconds=AGE_START,
        ye_floor_note=(
            "canonical family: Ye=0.45 substituted by 0.455 (network Z/A "
            "floor over A>=12 species is ne22 = 0.45455); Ye=0.45 proper is "
            "covered by the sobol family"
        ),
        n_runs=len(manifest_runs),
        runs=manifest_runs,
    )
    (net_dir / "campaign.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    n_pilot = sum(r["pilot"] for r in manifest_runs)
    print(
        f"{net}: {len(manifest_runs)} runs "
        f"({sum(r['family'] == 'shipped' for r in manifest_runs)} shipped, "
        f"{sum(r['family'] == 'canonical' for r in manifest_runs)} canonical, "
        f"{sum(r['family'] == 'sobol' for r in manifest_runs)} sobol; "
        f"{n_pilot} pilot) -> {net_dir}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--net", default="both", choices=["mesa_80", "mesa_151", "both"])
    ap.add_argument("--root", default=str(REPO / "data" / "bbq_reruns"))
    ap.add_argument("--points-per-decade", type=int, default=40)
    ap.add_argument("--dt-cap", type=float, default=1e5)
    args = ap.parse_args()
    nets = ["mesa_80", "mesa_151"] if args.net == "both" else [args.net]
    for net in nets:
        build(net, Path(args.root), args.points_per_decade, args.dt_cap)


if __name__ == "__main__":
    main()
