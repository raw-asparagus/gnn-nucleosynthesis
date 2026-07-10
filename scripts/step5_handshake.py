#!/usr/bin/env python
"""Step-5 Task 2: label handshake (RESULTS.md-ready output).

Two modes:

--grid (dt = 1e-6 s training-grid step): compares ΔX_pred = A·(νR)·dt₁
  against label (final − initial) on the stratified subsample. MEASURED
  FINDING (2026-07-10): the premise is void on the training grid — Sobol
  initial compositions carry free nucleons (median X_neut ≈ 1.7e-2), every
  state relaxes by |ΔX|/X ~ 1 within the first microsecond at ALL T9, and
  only ~20 of 2.4M cells are linearizable. The mode reports the stiffness
  census that documents this.

--trajectories (PRIMARY quantitative handshake): consecutive rows of the
  constant-(T,ρ) test trajectories give ΔX over output intervals from 1e-10 s
  upward — small enough that even ns-stiff states are linear at the early
  steps. Engine ẏ at each row is compared over the following interval,
  stratified by stiffness τ/Δt and T9. Bonus: per-row eps_nuc from bbq vs the
  flux-route ΣQ_j R_j (invariant-#5 dry run).

Usage:
  uv run python scripts/step5_handshake.py --net mesa_80 --trajectories
  uv run python scripts/step5_handshake.py --net mesa_80 --grid
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
TEST_SETS = REPO / "data/zenodo/NuclearNeuralNetworks/test_datasets"

T9_BIN_LABELS = [
    "[1.6,2.5)", "[2.5,3.3)", "[3.3,4.0)", "[4.0,5.0)", "[5.0,6.3)", "[6.3,7.95)",
]


def _print_common(cells, tag):
    from gnn_nucleo.fluxes.handshake import agreement_by_stiffness

    n_lin = int(cells.linearizable.sum())
    n_cells = cells.dX_pred.size
    frac = cells.agree[cells.linearizable].mean() if n_lin else float("nan")
    print(f"calibrated label noise eps_lab (10x median, per unit X): {cells.eps_lab:.3e}")
    print(
        f"VERDICT ({tag}): {frac:.6f} of {n_lin} linearizable cells agree "
        f"(tau > 10 dt; {n_cells} total cells, "
        f"{int(cells.censored.sum())} censored at the 1e-15 floor)"
    )
    print("by stiffness (tau/dt decade, uncensored cells):")
    for r in agreement_by_stiffness(cells):
        f = "nan" if np.isnan(r["fraction"]) else f"{r['fraction']:.4f}"
        print(f"  tau/dt {r['tau_over_dt']:<12} cells {r['n_cells']:>9}  agree {f}")


def _print_outliers(cells, net, f_plus, bad_mask=None):
    import yaml

    from gnn_nucleo.crosscheck.rates_compare import load_appendixb_handles
    from gnn_nucleo.fluxes.handshake import attribute_outliers
    from gnn_nucleo.graph import npz_path

    with np.load(npz_path(net), allow_pickle=False) as z:
        nu = z["nu"]
        rate_fnames = tuple(str(s) for s in z["rate_fnames"])
        is_tabular = z["is_tabular"]
        weak_type = z["weak_type"]
    out = attribute_outliers(cells, nu, f_plus, rate_fnames, bad_mask=bad_mask)
    appb = load_appendixb_handles(net)
    outdoc = yaml.safe_load((REPO / "configs" / "rate_outliers.yaml").read_text())
    severe = set()
    for entries in outdoc.get("networks", {}).get(net, {}).values():
        if isinstance(entries, list):
            severe |= {e.get("pyna_fname", "") for e in entries if isinstance(e, dict)}
    print(f"outlier channels (linearizable & disagreeing), top {len(out)}:")
    if not out:
        print("  NONE — handshake clean")
    for r in out:
        j = r["column"]
        klass = []
        if weak_type[j]:
            klass.append(f"weak:{weak_type[j]}" + ("/tabular" if is_tabular[j] else ""))
        if r["channel"] in severe:
            klass.append("rate_outliers.yaml")
        if r["channel"] in appb:
            klass.append("appendixB")
        print(
            f"  {r['channel']:<40} cells {r['n_cells']:>6}  "
            f"worst rel {r['worst_rel_resid']:.2e}  {','.join(klass) or 'UNEXPLAINED?'}"
        )


def run_grid_mode(net: str, run_id: str = "subsample") -> None:
    from gnn_nucleo.data.labels import load_step_frame
    from gnn_nucleo.data.schema import load_measured_dt
    from gnn_nucleo.data.subsample import T9_EDGES, load_subsample_ids
    from gnn_nucleo.fluxes.handshake import agreement_by_bin, build_cells
    from gnn_nucleo.fluxes.store import FluxStore
    from gnn_nucleo.graph import load_isotope_table

    table = load_isotope_table(net)
    dt = load_measured_dt(net)[0]
    ids = load_subsample_ids(net)
    cols = (
        ["logT", "logRho"]
        + [f"initial_{n}" for n in table.names]
        + [f"final_{n}" for n in table.names]
    )
    df = load_step_frame(net, "1e-6", columns=cols, state_ids=ids)
    X_init = df[[f"initial_{n}" for n in table.names]].to_numpy()
    X_fin = df[[f"final_{n}" for n in table.names]].to_numpy()
    t9 = 10.0 ** df["logT"].to_numpy() / 1e9

    store = FluxStore(net, run_id)
    chunks = list(store.iter_chunks())
    got_ids = np.concatenate([c.state_id for c in chunks])
    if not np.array_equal(got_ids, ids):
        raise ValueError("stored flux run does not match the subsample ids")
    ydot = np.concatenate([c.ydot for c in chunks], axis=1)
    f_plus = np.concatenate([c.f_plus for c in chunks], axis=1)

    cells = build_cells(ydot, X_init, X_fin, table.A.astype(np.float64), dt)
    print(f"== {net} GRID handshake @ dt = {dt!r} s ==")
    _print_common(cells, "grid")
    t9_bin = np.digitize(t9, T9_EDGES) - 1
    t9_bin[(t9_bin < 0) | (t9_bin >= len(T9_EDGES) - 1)] = -1
    print("by T9 stratum (linearizable cells):")
    for r in agreement_by_bin(cells, t9_bin, len(T9_EDGES) - 1):
        print(
            f"  T9 {T9_BIN_LABELS[r['bin']]:<11} states {r['n_states']:>6} "
            f"cells {r['n_cells']:>8}  agree {r['fraction']}  "
            f"censored {r['n_censored']}"
        )
    _print_outliers(cells, net, f_plus)
    stiff = (cells.tau_over_dt < 1).mean()
    print(
        f"\nstiffness census: {100 * stiff:.2f}% of cells have tau < dt at dt=1e-6 s "
        "— the training-grid step is a stiff relaxation, not a linear step "
        "(free-nucleon-loaded Sobol compositions)"
    )


def run_trajectory_mode(net: str, run_id: str = "trajectories") -> None:
    from pynucastro.constants import constants

    from gnn_nucleo.data.subsample import T9_EDGES
    from gnn_nucleo.fluxes.handshake import agreement_by_bin, build_cells
    from gnn_nucleo.fluxes.store import FluxStore
    from gnn_nucleo.graph import load_isotope_table, npz_path

    table = load_isotope_table(net)
    A = table.A.astype(np.float64)
    with np.load(npz_path(net), allow_pickle=False) as z:
        Q = z["Q"]

    abs_nu = np.abs(np.load(npz_path(net), allow_pickle=False)["nu"])

    store = FluxStore(net, run_id)
    all_cells = []
    t9_states = []
    fplus_list = []
    X_init_list = []
    e_ratio = []
    pair_col = None
    for chunk in store.iter_chunks():
        pair_col = chunk.pair_col
        fname = chunk.attrs["trajectory_file"]
        path = TEST_SETS / net / f"{net}_output_files" / fname
        data = np.loadtxt(path, skiprows=1)
        X = data[:, 4:]
        age = np.asarray(chunk.attrs["age"])
        if not np.allclose(age, data[:, 0]):
            raise ValueError(f"{fname}: stored ages != file ages")
        dts = np.diff(age)  # (n_rows-1,)
        # interval k: state k -> k+1; trapezoid prediction from ydot at both
        # ends; gross turnover at the start for the rate-level residual
        gross = abs_nu @ chunk.f_plus[:, :-1]
        cells = build_cells(
            chunk.ydot[:, :-1],
            X[:-1],
            np.maximum(X[1:], 1e-15),
            A,
            dts,
            ydot_end=chunk.ydot[:, 1:],
            gross=gross,
        )
        all_cells.append(cells)
        t9_states.append(np.full(len(dts), 10.0 ** chunk.attrs["logT"] / 1e9))
        fplus_list.append(chunk.f_plus[:, :-1])
        X_init_list.append(X[:-1])
        # energy route: bbq eps_nuc column (rate) vs Sum Q_j R_j
        e_flux = (Q @ chunk.f_plus) * constants.MeV2erg * constants.N_A
        e_bbq = data[:, 2]
        ok = np.abs(e_bbq) > 0
        t9_here = 10.0 ** chunk.attrs["logT"] / 1e9
        with np.errstate(divide="ignore", invalid="ignore"):
            e_ratio.append((e_flux[ok] / e_bbq[ok], np.full(ok.sum(), t9_here)))

    # merge
    from dataclasses import fields

    from gnn_nucleo.fluxes.handshake import GROSS_REL_TOL, HandshakeCells

    merged = {}
    for f in fields(HandshakeCells):
        if f.name == "eps_lab":
            continue
        merged[f.name] = np.concatenate(
            [getattr(c, f.name) for c in all_cells], axis=0
        )
    eps = float(np.median([c.eps_lab for c in all_cells]))
    cells = HandshakeCells(**merged, eps_lab=eps)
    t9 = np.concatenate(t9_states)
    f_plus = np.concatenate(fplus_list, axis=1)

    print(f"== {net} TRAJECTORY handshake (trapezoid; intervals 1e-10 s … ~1e1 s) ==")
    _print_common(cells, "trajectories")

    lin = cells.linearizable
    rg = cells.resid_gross[lin]
    print(
        f"\nRATE-LEVEL residual |ΔX_pred − ΔX_lab| / (A·gross·dt) on "
        f"linearizable cells (n={int(lin.sum())}):"
    )
    print(
        f"  median {np.median(rg):.3e}  p90 {np.quantile(rg, .9):.3e}  "
        f"p99 {np.quantile(rg, .99):.3e}  max {rg.max():.3e}"
    )
    print(
        f"  fraction ≤ {GROSS_REL_TOL:.0%}: {(rg <= GROSS_REL_TOL).mean():.4f}"
        f"   ≤ 1%: {(rg <= 0.01).mean():.4f}"
    )
    print("\nNET agreement conditioned on per-isotope cancellation c:")
    for thr in (0.0, 0.1, 0.5, 0.9):
        m = lin & (cells.cancellation >= thr)
        print(
            f"  c ≥ {thr:<4} cells {int(m.sum()):>8}  agree "
            f"{cells.agree[m].mean():.4f}"
        )

    t9_bin = np.digitize(t9, T9_EDGES) - 1
    t9_bin[(t9_bin < 0) | (t9_bin >= len(T9_EDGES) - 1)] = -1
    print("\nby T9 stratum (linearizable cells, net tolerance):")
    for r in agreement_by_bin(cells, t9_bin, len(T9_EDGES) - 1):
        frac = "nan" if np.isnan(r["fraction"]) else f"{r['fraction']:.6f}"
        print(
            f"  T9 {T9_BIN_LABELS[r['bin']]:<11} states {r['n_states']:>6} "
            f"cells {r['n_cells']:>8}  agree {frac}  censored {r['n_censored']}"
        )
    # outliers = RATE-LEVEL failures (net failures at small c are cancellation
    # amplification of documented rate-level differences, not config bugs)
    bad = lin & (cells.resid_gross > GROSS_REL_TOL)
    print(f"\nrate-level outliers (resid_gross > {GROSS_REL_TOL:.0%}): "
          f"{int(bad.sum())} cells ({bad.sum() / max(lin.sum(), 1):.2%})")

    # classify every bad cell against the DOCUMENTED Step-4 difference classes
    import yaml

    from gnn_nucleo.crosscheck.rates_compare import load_appendixb_handles

    with np.load(npz_path(net), allow_pickle=False) as z:
        nu = z["nu"]
        rate_fnames = [str(s) for s in z["rate_fnames"]]
        derived = z["derived_from_inverse"]
        is_tab = z["is_tabular"]
        wtype = z["weak_type"]
    outdoc = yaml.safe_load(
        (REPO / "configs" / "rate_outliers.yaml").read_text()
    )
    severe = set()
    for entries in outdoc.get("networks", {}).get(net, {}).values():
        if isinstance(entries, list):
            severe |= {e.get("pyna_fname", "") for e in entries if isinstance(e, dict)}
    appb = load_appendixb_handles(net)
    X_init_all = np.concatenate(X_init_list, axis=0)

    states, species = np.nonzero(bad)
    class_counts: dict[str, int] = {}
    unexplained: dict[str, int] = {}
    for s, i in zip(states, species):
        contrib = np.abs(nu[i, :] * f_plus[:, s])
        j = int(np.argmax(contrib))
        reactants = np.nonzero(nu[:, j] < 0)[0]
        if reactants.size and X_init_all[s, reactants].min() <= 1e-15:
            k = "subfloor-controller (reactant below label floor)"
        elif wtype[j] and is_tab[j]:
            k = "weak-tabular interpolation (0.03-0.18 dex class)"
        elif wtype[j]:
            k = "weak reaclib"
        elif derived[j] or (pair_col[j] >= 0 and derived[pair_col[j]]):
            k = "DB-reverse pf provenance (0.05-0.1 dex class)"
        elif rate_fnames[j] in severe:
            k = "snapshot refit (rate_outliers.yaml)"
        elif rate_fnames[j] in appb:
            k = "appendixB"
        else:
            k = "UNEXPLAINED"
            unexplained[rate_fnames[j]] = unexplained.get(rate_fnames[j], 0) + 1
        class_counts[k] = class_counts.get(k, 0) + 1
    print("bad-cell classification:")
    for k, v in sorted(class_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {k:<55} {v:>7} ({v / max(bad.sum(), 1):.1%})")
    if unexplained:
        print("UNEXPLAINED channels (dominant-attribution):")
        for ch, n in sorted(unexplained.items(), key=lambda kv: -kv[1])[:15]:
            print(f"  {ch:<45} cells {n}")
    else:
        print("UNEXPLAINED channels: NONE")

    print("\ne_nuc flux route (ΣQ_jR_j) vs bbq eps_nuc column, by T9:")
    ratios = np.concatenate([r for r, _ in e_ratio])
    r_t9 = np.concatenate([t for _, t in e_ratio])
    for lo, hi, lab in zip(T9_EDGES[:-1], T9_EDGES[1:], T9_BIN_LABELS):
        m = (r_t9 >= lo) & (r_t9 < hi)
        if m.sum() < 5:
            continue
        print(
            f"  T9 {lab:<11} n {m.sum():>6}  median {np.median(ratios[m]):.4f}  "
            f"[p10 {np.quantile(ratios[m], 0.1):.4f}, p90 {np.quantile(ratios[m], 0.9):.4f}]"
        )
    print("(constant-Q; neutrino losses not subtracted — bbq eps_nuc may include ν share)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--net", required=True, choices=["mesa_80", "mesa_151"])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--grid", action="store_true")
    mode.add_argument("--trajectories", action="store_true")
    ap.add_argument("--run-id", default=None)
    args = ap.parse_args()
    if args.grid:
        run_grid_mode(args.net, args.run_id or "subsample")
    else:
        run_trajectory_mode(args.net, args.run_id or "trajectories")


if __name__ == "__main__":
    main()
