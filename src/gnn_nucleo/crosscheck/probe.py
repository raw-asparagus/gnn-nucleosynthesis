"""Subprocess runner for the Fortran MESA probe (src/mesa_probes/mesa_probe).

The probe binary carries RPATHs into the mesasdk, so at runtime it only
needs MESA_DIR.  Rate-table cache writes are redirected away from the MESA
tree via MESA_CACHES_DIR (kept under data/mesa_cache, gitignored), keeping
the upstream installation byte-identical to the verified Zenodo release.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = REPO_ROOT / "src" / "mesa_probes"
PROBE_BIN = PROBE_DIR / "mesa_probe"
CACHE_DIR = REPO_ROOT / "data" / "mesa_cache"

MODES = ("dump_net", "dump_inverse", "eval_rates", "eval_weak", "eval_screen")


def mesa_dir() -> Path:
    return Path(os.environ.get("MESA_DIR", Path.home() / "mesa-r23.05.1"))


def probe_available() -> bool:
    return PROBE_BIN.exists() and mesa_dir().is_dir()


def ensure_built() -> None:
    if PROBE_BIN.exists():
        return
    subprocess.run(
        ["bash", str(PROBE_DIR / "build.sh")], check=True, capture_output=True
    )


def run_probe(
    mode: str,
    net: str,
    stdin_text: str | None = None,
    screening: str | None = None,
    timeout: float = 600.0,
) -> pd.DataFrame:
    """Run one probe mode against a net file and return the CSV as a DataFrame.

    Parameters
    ----------
    mode : one of MODES
    net : MESA net file name, e.g. 'mesa_80.net'
    stdin_text : grid lines for the eval_* modes (one state per line)
    screening : screening mode string for eval_screen (default 'chugunov')
    """
    if mode not in MODES:
        raise ValueError(f"unknown probe mode {mode!r}")
    ensure_built()
    (CACHE_DIR / "rates_cache").mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.setdefault("MESA_DIR", str(mesa_dir()))
    env["MESA_CACHES_DIR"] = str(CACHE_DIR)
    env.setdefault("OMP_NUM_THREADS", str(os.cpu_count() or 1))

    out_csv = CACHE_DIR / f"probe_{mode}_{net.replace('.net', '')}.csv"
    cmd = [str(PROBE_BIN), mode, net, str(out_csv)]
    if screening is not None:
        cmd.append(screening)
    res = subprocess.run(
        cmd,
        input=stdin_text or "",
        text=True,
        capture_output=True,
        env=env,
        cwd=PROBE_DIR,
        timeout=timeout,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"mesa_probe {mode} {net} failed (rc={res.returncode}):\n"
            f"{res.stdout[-2000:]}\n{res.stderr[-2000:]}"
        )
    return pd.read_csv(out_csv, dtype={"weak_lhs": str, "weak_rhs": str})


def grid_stdin(states: list[tuple[float, float, float]]) -> str:
    return "\n".join(f"{t9:.6g} {rho:.6g} {ye:.6g}" for t9, rho, ye in states) + "\n"


def t9_stdin(t9s: tuple[float, ...] | list[float]) -> str:
    return "\n".join(f"{t9:.6g}" for t9 in t9s) + "\n"


def read_probe_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)
