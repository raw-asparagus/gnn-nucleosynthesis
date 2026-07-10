"""Spot-check engine rates against the MESA 24.08.1 probe (mesa_probe24).

Skipped when the probe binary / MESA tree is unavailable. Bands are the
Step-4 measured ones (docs/rate-crosscheck.md): clean REACLIB forwards agree
to ≲0.004 dex; pf-corrected DB reverses vs MESA-side reverses differ by pf /
mass-table provenance within ~0.1 dex in the box. Appendix-B channels are
checked against mesa_probe24 ONLY (guards.assert_appendixb_routing).
"""

from __future__ import annotations

import os
import subprocess
import warnings

import numpy as np
import pandas as pd
import pytest

T9S = (3.3, 5.0, 7.9)


def _probe24_available():
    from gnn_nucleo.crosscheck.probe import PROBE_BIN, mesa_dir

    probe24 = PROBE_BIN.parent / "mesa_probe24"
    try:
        return probe24.exists() and (mesa_dir().parent / "mesa-24.08.1").exists()
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _probe24_available(), reason="mesa_probe24 / MESA 24.08.1 not available"
)


@pytest.fixture(scope="module")
def mesa24_rates():
    """MESA 24.08.1 bare rates (screening off, T-only) for mesa_80 at T9S,
    joined to canonical keys."""
    from gnn_nucleo.crosscheck.mesa_dump import dump_to_records
    from gnn_nucleo.crosscheck.probe import CACHE_DIR, PROBE_BIN, mesa_dir, run_probe, t9_stdin

    dump = run_probe("dump_net", "mesa_80.net")
    records = dump_to_records(dump)
    meta = pd.DataFrame(
        {
            "name": [r["mesa_handle"] for r in records],
            "key": [r["key"] for r in records],
        }
    )

    probe24 = PROBE_BIN.parent / "mesa_probe24"
    env = os.environ.copy()
    env["MESA_DIR"] = str(mesa_dir().parent / "mesa-24.08.1")
    env["MESA_CACHES_DIR"] = str(CACHE_DIR / "cache24")
    (CACHE_DIR / "cache24" / "rates_cache").mkdir(parents=True, exist_ok=True)
    out_csv = CACHE_DIR / "probe24_eval_rates_mesa_80.csv"
    subprocess.run(
        [str(probe24), "eval_rates", "mesa_80.net", str(out_csv)],
        input=t9_stdin(T9S),
        text=True,
        capture_output=True,
        env=env,
        cwd=PROBE_BIN.parent,
        check=True,
    )
    df = pd.read_csv(out_csv)
    return df.merge(meta, on="name", validate="many_to_one")


@pytest.fixture(scope="module")
def engine_bare():
    """Engine bare λ (screening OFF) for mesa_80 at T9S, keyed canonically."""
    from gnn_nucleo.crosscheck.canonical import directed_key, from_pyna
    from gnn_nucleo.fluxes.compile import compile_network
    from gnn_nucleo.fluxes.engine import evaluate_lambda

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        cn = compile_network("mesa_80", screening=None)
        T = np.array(T9S) * 1e9
        rho = np.full(len(T9S), 1e8)
        Y = np.full((cn.stoich.n_species, len(T9S)), 1e-3)
        lam = evaluate_lambda(cn, T, rho, Y)

    keys = [
        directed_key(
            [from_pyna(n) for n in r.reactants], [from_pyna(n) for n in r.products]
        )
        for r in cn.rates
    ]
    return cn, dict(zip(keys, lam)), keys


# channels: clean forwards + their pf-corrected DB reverses in the Si-burning
# window, away from the 135-outlier list and the weak sector
SPOT_FORWARD = [
    "he4*1+si28*1=>s32*1",
    "he4*1+s32*1=>ar36*1",
    "ca40*1+he4*1=>ti44*1",
]
SPOT_REVERSE = [
    "s32*1=>he4*1+si28*1",
    "ar36*1=>he4*1+s32*1",
    "ti44*1=>ca40*1+he4*1",
]


class TestMesaSpotCheck:
    @pytest.mark.parametrize("key", SPOT_FORWARD)
    def test_forward_within_band(self, mesa24_rates, engine_bare, key):
        _, lam_by_key, _ = engine_bare
        sub = mesa24_rates[mesa24_rates["key"] == key]
        assert len(sub) == len(T9S), f"{key} missing from probe dump"
        for i, t9 in enumerate(T9S):
            mesa = float(sub[sub["t9"] == t9]["raw_rate"].iloc[0])
            ours = float(lam_by_key[key][i])
            dlog = abs(np.log10(mesa) - np.log10(ours))
            assert dlog <= 0.004, f"{key} @T9={t9}: {dlog:.4f} dex"

    @pytest.mark.parametrize("key", SPOT_REVERSE)
    def test_pf_reverse_within_band(self, mesa24_rates, engine_bare, key):
        _, lam_by_key, _ = engine_bare
        sub = mesa24_rates[mesa24_rates["key"] == key]
        assert len(sub) == len(T9S), f"{key} missing from probe dump"
        for i, t9 in enumerate(T9S):
            mesa = float(sub[sub["t9"] == t9]["raw_rate"].iloc[0])
            ours = float(lam_by_key[key][i])
            dlog = abs(np.log10(mesa) - np.log10(ours))
            assert dlog <= 0.1, f"{key} @T9={t9}: {dlog:.4f} dex"

    def test_appendixb_channel_vs_mesa24_only(self, mesa24_rates, engine_bare):
        """gh-575 channel r_c12_to_he4_he4_he4 (photo_of_multibody): engine vs
        24.08.1 must agree to ≲1.9 dex-class residuals FIXED (Step-4: stock was
        ~10 dex off). Use a generous 2.0 dex band — the point is stock-vs-fixed."""
        from gnn_nucleo.fluxes.guards import assert_appendixb_routing

        assert_appendixb_routing("mesa_80", ["r_c12_to_he4_he4_he4"], source="mesa24")
        _, lam_by_key, _ = engine_bare
        key = "c12*1=>he4*3"
        sub = mesa24_rates[mesa24_rates["key"] == key]
        if sub.empty:
            pytest.skip("channel not in probe dump")
        for i, t9 in enumerate(T9S):
            mesa = float(sub[sub["t9"] == t9]["raw_rate"].iloc[0])
            ours = float(lam_by_key[key][i])
            if mesa <= 0 or ours <= 0:
                continue
            dlog = abs(np.log10(mesa) - np.log10(ours))
            assert dlog <= 2.0, f"{key} @T9={t9}: {dlog:.3f} dex vs 24.08.1"
