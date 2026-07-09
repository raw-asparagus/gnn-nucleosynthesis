"""Step-4 Task-3 detailed-balance / kappa-floor screen at NSE.

At true equilibrium every strong/EM forward-reverse pair must satisfy
f+ ~= f-, so kappa_r = |f+ - f-| / (f+ + f-) -> 0 to rate-evaluation
precision. A kappa floor at NSE is a spurious artifact of inconsistent
forward/reverse rate construction, and would contaminate every Step-5/6
kill-test kappa conclusion.

Three rate sources are screened for attribution:

* ``pyna``    — the graphs as built (pynucastro forwards + pf-free JINA
                v-flag reverses): the configuration Step 5/6 would use.
* ``mesa24``  — MESA 24.08.1 (gh-575 fixed, pf-corrected DB reverses):
                the corrected reference.
* ``mesa``    — stock r23.05.1 (label MESA minus the authors' fix):
                shows the gh-575 channels.

MESA-side gross fluxes reuse pynucastro's Y-product factors: within a
pair comparison the composition factors are common, so
f_mesa = f_pyna * (lambda_mesa / lambda_pyna) with bare (unscreened,
T-only) rates on both sides.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .canonical import reverse_key
from .probe import PROBE_BIN, t9_stdin


def nse_composition(network: str, t9: float, rho: float, ye: float):
    """NSE composition via pynucastro's solver, with a retry ladder over
    initial guesses. Returns (Composition, converged: bool)."""
    import pynucastro as pyna

    from gnn_nucleo.graph import build_rate_collection, load_isotope_table

    if not hasattr(nse_composition, "_cache"):
        nse_composition._cache = {}
    if network not in nse_composition._cache:
        table = load_isotope_table(network)
        rc, _ = build_rate_collection(table)
        nse_composition._cache[network] = pyna.NSENetwork(
            rates=rc.get_rates()
        )
    nse = nse_composition._cache[network]
    for guess in ((-3.5, -15), (-6, -12), (-10, -10), (-3, -20)):
        try:
            comp = nse.get_comp_nse(
                rho, t9 * 1e9, ye, init_guess=guess, use_coulomb_corr=False
            )
            return comp, True
        except Exception:
            continue
    return None, False


def strong_pairs(network: str) -> list[tuple[str, str]]:
    """(forward fname, reverse fname) for every strong/EM pair present in
    both directions, keyed canonically. Forward = the non-derived member
    when determinable, else lexicographic."""
    from .reconcile import pyna_inventory

    inv = pyna_inventory(network)
    by_key = {r["key"]: r for r in inv}
    pairs = []
    seen = set()
    for r in inv:
        if r["is_weak"]:
            continue
        k, rk = r["key"], reverse_key(r["key"])
        if rk not in by_key or by_key[rk]["is_weak"]:
            continue
        pk = tuple(sorted((k, rk)))
        if pk in seen:
            continue
        seen.add(pk)
        other = by_key[rk]
        if r["derived_from_inverse"] and not other["derived_from_inverse"]:
            fwd, rev = other, r
        else:
            fwd, rev = r, other
        pairs.append((fwd["fname"], rev["fname"]))
    return pairs


def mesa_ratio_tables(network: str, t9s) -> dict[str, dict]:
    """{variant: {(pyna fname, t9): log10(lambda_mesa / lambda_pyna)}}."""
    import subprocess

    from .rates_compare import mesa_reaclib_table, pyna_reaclib_values
    from .reconcile import pyna_inventory

    fname_by_key = {r["key"]: r["fname"] for r in pyna_inventory(network)}
    pyna_vals = pyna_reaclib_values(network, t9s)
    pyna_vals["fname"] = pyna_vals["key"].map(fname_by_key)

    out: dict[str, dict] = {}
    # stock r23.05.1 via the standard probe
    mesa = mesa_reaclib_table(network, t9s)
    m = mesa.merge(pyna_vals, on=["key", "t9"])
    out["mesa"] = {
        (r.fname, r.t9): float(np.log10(r.raw_rate) - np.log10(r.pyna_rate))
        if (r.raw_rate > 0 and r.pyna_rate > 0)
        else np.nan
        for r in m.itertuples()
    }
    # 24.08.1 via mesa_probe24 (same net files)
    probe24 = PROBE_BIN.parent / "mesa_probe24"
    if probe24.exists():
        import os

        from .probe import CACHE_DIR, mesa_dir

        env = os.environ.copy()
        env["MESA_DIR"] = str(mesa_dir().parent / "mesa-24.08.1")
        env["MESA_CACHES_DIR"] = str(CACHE_DIR / "cache24")
        (CACHE_DIR / "cache24" / "rates_cache").mkdir(parents=True, exist_ok=True)
        out_csv = CACHE_DIR / f"probe24_eval_rates_{network}.csv"
        subprocess.run(
            [str(probe24), "eval_rates", f"{network}.net", str(out_csv)],
            input=t9_stdin(t9s),
            text=True,
            capture_output=True,
            env=env,
            cwd=PROBE_BIN.parent,
            check=True,
        )
        r24 = pd.read_csv(out_csv)
        meta = mesa[["name", "key", "t9"]].drop_duplicates()
        m24 = r24.merge(meta, on=["name", "t9"]).merge(
            pyna_vals, on=["key", "t9"]
        )
        out["mesa24"] = {
            (r.fname, r.t9): float(
                np.log10(r.raw_rate) - np.log10(r.pyna_rate)
            )
            if (r.raw_rate > 0 and r.pyna_rate > 0)
            else np.nan
            for r in m24.itertuples()
        }
    return out


def kappa_at_state(
    network: str,
    t9: float,
    rho: float,
    ye: float,
    pairs: list[tuple[str, str]],
    ratios: dict[str, dict],
) -> pd.DataFrame | None:
    """kappa_r per pair per rate-source variant at one NSE state."""
    from gnn_nucleo.graph import build_rate_collection, load_isotope_table

    comp, ok = nse_composition(network, t9, rho, ye)
    if not ok:
        return None
    if not hasattr(kappa_at_state, "_rc"):
        kappa_at_state._rc = {}
    if network not in kappa_at_state._rc:
        rc, _ = build_rate_collection(load_isotope_table(network))
        kappa_at_state._rc[network] = rc
    rc = kappa_at_state._rc[network]
    rvals_raw = rc.evaluate_rates(rho=rho, T=t9 * 1e9, composition=comp)
    rvals = {r.fname: v for r, v in rvals_raw.items()}

    rows = []
    for fwd, rev in pairs:
        f_p, r_p = rvals.get(fwd, np.nan), rvals.get(rev, np.nan)
        if not (f_p > 0 and r_p > 0):
            continue
        rec = {
            "network": network,
            "t9": t9,
            "rho": rho,
            "ye": ye,
            "fwd": fwd,
            "rev": rev,
            "kappa_pyna": abs(f_p - r_p) / (f_p + r_p),
        }
        for variant, tab in ratios.items():
            df_ = tab.get((fwd, t9), np.nan)
            dr_ = tab.get((rev, t9), np.nan)
            if np.isnan(df_) or np.isnan(dr_):
                rec[f"kappa_{variant}"] = np.nan
                continue
            f_m = f_p * 10.0**df_
            r_m = r_p * 10.0**dr_
            rec[f"kappa_{variant}"] = abs(f_m - r_m) / (f_m + r_m)
        rows.append(rec)
    return pd.DataFrame(rows)
