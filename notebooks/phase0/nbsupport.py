"""Shared presentation helpers for the Phase-0 notebook series.

Notebooks are EXPLORATORY (root CLAUDE.md): they visualize quantities whose
citable values live in RESULTS.md, produced by scripts/. Nothing here computes
a number anyone may cite; the helpers exist so every notebook renders the same
provenance header, cites RESULTS.md rows on every figure, and respects the
repo's plotting conventions (two-κ rule, QUICK-subset banners).

Import cost: module level touches numpy/matplotlib/yaml plus the cheap
``gnn_nucleo.killtest.strata`` constants only. Anything that would pull
pynucastro/pandas (graph package, labels, flux compilation) stays inside
functions at call sites in the notebooks themselves.
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import subprocess
import textwrap
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from gnn_nucleo.killtest.strata import (  # cheap import: numpy only
    T9_EDGES,
    T9_LABELS,
    YE_EDGES,
    YE_LABELS,
    assign_strata,
)

__all__ = [
    "REPO",
    "QUICK",
    "T9_EDGES",
    "T9_LABELS",
    "YE_EDGES",
    "YE_LABELS",
    "assign_strata",
    "style",
    "git_commit",
    "provenance_header",
    "caption",
    "parse_checklist",
    "status_of",
    "stoich_path",
    "graphml_path",
    "load_nu",
    "flux_store",
    "iter_chunk_attrs",
    "kappa_hist_by_stratum",
    "quick_banner",
    "CYCLE",
    "KAPPA_BINS",
]


def _find_repo(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "pyproject.toml").exists():
            return p
    raise RuntimeError(f"no pyproject.toml above {start}")


REPO: Path = _find_repo(Path(__file__).resolve())

#: Notebooks default to the QUICK subset (NB_QUICK=0 for full depth).
QUICK: bool = os.environ.get("NB_QUICK", "1") != "0"

_BADGE = {
    "done": "✅ DONE",
    "partial": "🟡 PARTIAL",
    "unbuilt": "⬜ NOT BUILT",
    "unknown": "▨ STATUS UNKNOWN",
}

#: Okabe–Ito colorblind-safe cycle (also the rcParams prop_cycle).
CYCLE = [
    "#0072B2",
    "#E69F00",
    "#009E73",
    "#D55E00",
    "#CC79A7",
    "#56B4E9",
    "#F0E442",
    "#000000",
]


def style() -> None:
    """Apply the series-wide matplotlib style (call once per notebook)."""
    plt.rcParams.update(
        {
            "figure.figsize": (9.0, 5.0),
            "figure.dpi": 110,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "axes.axisbelow": True,
            "axes.prop_cycle": mpl.cycler(color=CYCLE),
            "legend.frameon": False,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
        }
    )


def git_commit() -> tuple[str, bool]:
    """(short hash, dirty flag) of the repo; ("unknown", False) outside git."""
    try:
        head = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=REPO,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        )
        return head, dirty
    except Exception:
        return "unknown", False


def provenance_header(
    nb_id: str,
    title: str,
    status: str,
    results_rows: list[str],
    data: list[str],
    scripts: list[str],
) -> None:
    """Render the mandatory provenance header cell (IPython Markdown).

    ``status`` is one of done/partial/unbuilt/unknown — usually the output of
    :func:`status_of`. ``results_rows`` name the RESULTS.md rows (by date +
    quantity) this notebook illustrates; ``scripts`` the producing scripts.
    """
    from IPython.display import Markdown, display

    commit, dirty = git_commit()
    badge = _BADGE.get(status, _BADGE["unknown"])
    lines = [
        f"### {nb_id} — {title}",
        "",
        f"**Pipeline-node status:** {badge}  ",
        f"**Rendered:** {_dt.date.today().isoformat()} at commit `{commit}`"
        + (" (dirty tree)" if dirty else "")
        + "  ",
        f"**Mode:** {'QUICK subset (NB_QUICK=0 for full depth)' if QUICK else 'FULL depth'}",
        "",
        "**RESULTS.md rows visualized:**",
        *[f"- {r}" for r in results_rows],
        "",
        "**Data provenance:** " + "; ".join(data),
        "",
        "**Producing scripts:** " + ", ".join(f"`{s}`" for s in scripts),
        "",
        "> EXPLORATORY — this notebook mints no citable numbers. Citable values"
        " live in RESULTS.md with commit + data hashes; figures here re-plot or"
        " quick-look them (root CLAUDE.md notebook rule).",
    ]
    display(Markdown("\n".join(lines)))


def caption(fig, text: str, results: list[str], scripts: list[str] | tuple = ()) -> None:
    """Figure footer: caption + mandatory RESULTS.md citation.

    Refuses an empty ``results`` list — every figure must cite the rows (or
    the doc) whose numbers it illustrates.
    """
    if not results:
        raise ValueError(
            "every figure must cite at least one RESULTS.md row / provenance doc"
        )
    cite = "Cites: " + "; ".join(results)
    if scripts:
        cite += ". Producer: " + ", ".join(scripts)
    body = textwrap.fill(text, 130) + "\n" + textwrap.fill(cite, 130)
    fig.text(0.01, -0.02, body, ha="left", va="top", fontsize=8, color="0.35")


# --- phase0-checklist parsing -------------------------------------------------

_CHECKLIST = REPO / "docs" / "phase0-checklist.md"
_PIPE_SENTINEL = "\x00"


def parse_checklist(path: Path | None = None) -> dict:
    """Parse docs/phase0-checklist.md into statuses (defensive, never raises).

    Returns ``{"rows": {n: bool}, "rowdata": {n: (measurement, gates)},
    "local": [(text, bool), ...]}``. Unknown/missing structure simply yields
    fewer entries; consumers map absence to "unknown".
    """
    rows: dict[int, bool] = {}
    rowdata: dict[int, tuple[str, str]] = {}
    local: list[tuple[str, bool]] = []
    try:
        text = (path or _CHECKLIST).read_text()
    except OSError:
        return {"rows": rows, "rowdata": rowdata, "local": local}
    for line in text.splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|\s*\[([ x])\]", line)
        if m:
            n = int(m.group(1))
            rows[n] = m.group(2) == "x"
            # cell split honouring escaped \| inside the table
            cells = [
                c.replace(_PIPE_SENTINEL, "|").strip()
                for c in line.replace(r"\|", _PIPE_SENTINEL).split("|")
            ]
            if len(cells) >= 5:
                rowdata[n] = (cells[3], cells[4])
            continue
        m = re.match(r"^- \[([ x])\]\s+(.*)", line)
        if m:
            local.append((m.group(2).strip(), m.group(1) == "x"))
    return {"rows": rows, "rowdata": rowdata, "local": local}


def status_of(
    rows: list[int],
    local_keys: list[str] | tuple = (),
    checklist: dict | None = None,
) -> str:
    """Aggregate checklist rows (+ local-confirmation bullets matched by
    substring) into done/partial/unbuilt/unknown."""
    cl = checklist if checklist is not None else parse_checklist()
    states: list[bool] = []
    for r in rows:
        if r not in cl["rows"]:
            return "unknown"
        states.append(cl["rows"][r])
    for key in local_keys:
        hits = [done for text, done in cl["local"] if key.lower() in text.lower()]
        if not hits:
            return "unknown"
        states.extend(hits)
    if not states:
        return "unknown"
    if all(states):
        return "done"
    if any(states):
        return "partial"
    return "unbuilt"


# --- artifact paths -----------------------------------------------------------


def stoich_path(network: str) -> Path:
    """data/stoich npz for a network (mesa_80 → nu_mesa80.npz)."""
    return REPO / "data" / "stoich" / f"nu_{network.replace('_', '')}.npz"


def graphml_path(network: str) -> Path:
    return REPO / "data" / "graphs" / f"{network.replace('_', '')}.graphml"


def load_nu(network: str) -> dict[str, np.ndarray]:
    """Plain ``np.load`` of the stoichiometric export (float64 throughout).

    Deliberately avoids ``gnn_nucleo.graph`` (whose package import pulls
    pynucastro + networkx); the npz is the canonical exported artifact.
    """
    with np.load(stoich_path(network), allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def flux_store(network: str, run_id: str):
    """Open an EXISTING FluxStore run (raises instead of mkdir-ing a typo)."""
    from gnn_nucleo.fluxes.store import FluxStore, fluxes_root

    d = fluxes_root() / network / run_id
    if not d.is_dir() or not any(d.glob("chunk_*.h5")):
        raise FileNotFoundError(f"no flux run at {d}")
    return FluxStore(network, run_id)


def iter_chunk_attrs(store):
    """Yield attrs dicts of completed chunks WITHOUT reading datasets."""
    import h5py

    for p in sorted(store.dir.glob("chunk_*.h5")):
        try:
            with h5py.File(p, "r") as f:
                if f.attrs.get("complete", False):
                    yield dict(f.attrs)
        except OSError:
            continue


# --- κ plotting helpers (two-κ rule is structural here) ------------------------

#: log10-κ histogram bins for plotting (clipped into [-16, 0]).
KAPPA_BINS = np.linspace(-16.0, 0.0, 81)


def kappa_hist_by_stratum(
    store,
    *,
    convention: str,
    allow_screened: bool = False,
    max_chunks: int | None = None,
    carrying: bool = True,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Streaming per-T9-stratum log10-κ histograms over a FluxStore run.

    Presentation-grade companion to ``killtest.distributions.kappa_summary``
    (same carrying-pair selection); returns raw histograms for plotting where
    kappa_summary returns summary statistics. ``convention`` must be
    "UNSCREENED" or "SCREENED" and must MATCH what the run's chunks record —
    the CLAUDE.md two-κ rule (κ thresholds are evaluated unscreened; screened
    κ only for screening-offset diagnostics) is enforced, not advisory.

    Returns ``(hist[n_strata, n_bins], KAPPA_BINS, n_chunks_read)``.
    """
    if convention not in ("UNSCREENED", "SCREENED"):
        raise ValueError("convention must be 'UNSCREENED' or 'SCREENED'")
    n_strata = len(T9_EDGES) - 1
    hist = np.zeros((n_strata, len(KAPPA_BINS) - 1), dtype=np.int64)
    n_read = 0
    for chunk in store.iter_chunks():
        scr = str(chunk.attrs.get("screening", "None"))
        screened = scr not in ("None", "none")
        if screened and not allow_screened:
            raise ValueError(
                f"run records screening={scr!r}: κ thresholds use the UNSCREENED "
                "convention (CLAUDE.md two-κ rule); pass allow_screened=True only "
                "for screening-offset diagnostics"
            )
        if screened != (convention == "SCREENED"):
            raise ValueError(
                f"declared convention {convention!r} does not match the run "
                f"(chunk screening={scr!r}) — never mix the two κ conventions"
            )
        strong_fwd = chunk.is_forward_member & (chunk.pair_col >= 0)
        f = chunk.f_plus[strong_fwd]
        k = chunk.kappa[strong_fwd]
        tb, _ = assign_strata(chunk.T, chunk.ye)
        for b in range(n_strata):
            m = tb == b
            if not m.any():
                continue
            fs = f[:, m]
            ks = k[:, m]
            if carrying:
                pos = fs[fs > 0]
                if pos.size == 0:
                    continue
                sel = fs > np.median(pos)
            else:
                sel = fs > 0
            kk = ks[sel]
            if kk.size == 0:
                continue
            logk = np.clip(np.log10(np.maximum(kk, 1e-300)), -16.0, 0.0)
            hist[b] += np.histogram(logk, bins=KAPPA_BINS)[0]
        n_read += 1
        if max_chunks is not None and n_read >= max_chunks:
            break
    return hist, KAPPA_BINS, n_read


def quick_banner(
    fig,
    note: str = "QUICK-LOOK SUBSET — citable numbers live in RESULTS.md",
) -> None:
    """Loud stamp for figures computed on capped/QUICK subsets."""
    fig.text(
        0.99,
        0.99,
        note,
        ha="right",
        va="top",
        fontsize=9,
        fontweight="bold",
        color="#b3261e",
        bbox=dict(boxstyle="round", fc="#fde7e9", ec="#b3261e", alpha=0.9),
    )
