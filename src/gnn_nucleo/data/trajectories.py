"""Trajectory-file access with the stall guard (Step 6, Task 0).

Single home for reading bbq hydrostatic-mode trajectory output — both the
shipped Zenodo test trajectories and local reruns under ``data/bbq_reruns/``
share one format (bbq ``lib_hydrostatic.f90``): header
``age dt eps_nuc eps_neu <isos>``, one row per output interval, row 0 = the
initial state (dt is a 1e-10 placeholder there).

Stall guard
-----------
The shipped constant-(T, rho) trajectories STALL at non-equilibrium states
(RESULTS.md 2026-07-10): composition frozen (max_i |dX_i| < 1e-10 per
interval) from median age 2.2e5 s (mesa_80) / 3.9e4 s (mesa_151) while the
file's own eps_nuc keeps rising. Only PRE-STALL rows are physical evolution.
``select_rows`` therefore defaults to ``prestall=True``; consumers wanting
post-stall rows must override explicitly. ``stall_row`` is the exact rule
previously inlined in scripts/step5_qse.py and scripts/step5_bridges.py.

eps_nuc convention
------------------
Trajectory files carry a DIFFERENT eps convention from the training CSVs
(``schema.EPS_NORMALIZATION`` does NOT apply here). PINNED (measured,
scripts/step6_eps_pin.py; RESULTS.md 2026-07-11): the eps_nuc column is the
INTEGRATED specific energy release over the row's own dt [erg/g], NET of
neutrino losses (median log10 ratio vs the composition route minus ∫eps_neu:
0.000, IQR ≈ 0, sign agreement 0.9933/0.9981 for mesa_80/151, slope vs dt
decade 0.000 across 20 decades; the rate reading shows the wrong-convention
slope +1.0). The eps_neu column is a RATE [erg/g/s]. Matches the source read
(bbq src/lib_bbq.f90:453: ``out% eps_nuc = avg_eps_nuc * in% time``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

__all__ = [
    "STALL_TOL",
    "TRAJ_EPS_CONVENTION",
    "TrajectoryFrame",
    "zenodo_trajectory_dir",
    "load_trajectory",
    "stall_row",
    "select_rows",
    "eps_nuc_rate",
    "eps_nuc_integrated",
]

_REPO = Path(__file__).resolve().parents[3]

#: Composition-freeze tolerance of the stall rule (max_i |dX_i| per interval).
#: Exact value from the Step-5 inline detection (RESULTS.md 2026-07-10).
STALL_TOL: float = 1e-10

#: Empirically pinned meaning of the trajectory-file eps_nuc column:
#: "integrated" (erg/g over the row's own dt, NET of neutrino losses) or
#: "rate" (erg/g/s). Pinned "integrated" by scripts/step6_eps_pin.py
#: (RESULTS.md 2026-07-11); the converters refuse to run if reset to None.
TRAJ_EPS_CONVENTION: str | None = "integrated"

_FNAME_RE = re.compile(r"_T_(?P<logT>[0-9.]+)_rho_(?P<logRho>[0-9.]+)\.txt$")


@dataclass(frozen=True)
class TrajectoryFrame:
    """One parsed constant-(T, rho) bbq trajectory.

    ``eps_nuc_raw`` / ``eps_neu_raw`` are the file columns verbatim — use
    ``eps_nuc_rate`` / ``eps_nuc_integrated`` for physical values once the
    convention is pinned.
    """

    network: str
    fname: str
    source: str  # "zenodo" | "rerun"
    logT: float
    logRho: float
    age: np.ndarray  # (n_rows,) [s]
    dt: np.ndarray  # (n_rows,) per-row burn duration [s]; row 0 placeholder
    eps_nuc_raw: np.ndarray  # (n_rows,) file column, convention-unresolved
    eps_neu_raw: np.ndarray  # (n_rows,) file column
    X: np.ndarray  # (n_rows, n_species) mass fractions, float64

    @property
    def n_rows(self) -> int:
        return self.X.shape[0]


def zenodo_trajectory_dir(network: str) -> Path:
    """Directory of the shipped test-trajectory output files."""
    return (
        _REPO
        / "data/zenodo/NuclearNeuralNetworks/test_datasets"
        / network
        / f"{network}_output_files"
    )


def load_trajectory(
    network: str,
    path: str | Path,
    *,
    source: str = "zenodo",
    logT: float | None = None,
    logRho: float | None = None,
) -> TrajectoryFrame:
    """Parse one bbq trajectory file, validating the isotope column order.

    ``path`` may be a bare filename (resolved under the Zenodo trajectory
    directory when ``source="zenodo"``) or any explicit path. For
    ``source="zenodo"`` the (logT, logRho) coordinates are parsed from the
    ``output_T_<logT>_rho_<logRho>.txt`` filename; for ``source="rerun"``
    they must be passed explicitly (rerun filenames do not encode them —
    the campaign manifest is authoritative).
    """
    from gnn_nucleo.graph import load_isotope_table

    if source not in ("zenodo", "rerun"):
        raise ValueError(f"unknown source {source!r}")
    p = Path(path)
    if not p.is_absolute() and source == "zenodo" and len(p.parts) == 1:
        p = zenodo_trajectory_dir(network) / p

    if logT is None or logRho is None:
        m = _FNAME_RE.search(p.name)
        if source == "rerun" or m is None:
            raise ValueError(
                f"logT/logRho not derivable from {p.name!r} — pass them "
                "explicitly (rerun coordinates come from the campaign manifest)"
            )
        logT = float(m.group("logT"))
        logRho = float(m.group("logRho"))

    table = load_isotope_table(network)
    with open(p) as fh:
        header = fh.readline().split()
    if header[:4] != ["age", "dt", "eps_nuc", "eps_neu"]:
        raise ValueError(f"{p.name}: unexpected header prefix {header[:4]}")
    if header[4:] != list(table.names):
        raise ValueError(
            f"{p.name}: isotope column order != {network} isotope table"
        )
    data = np.loadtxt(p, skiprows=1, dtype=np.float64)
    if data.ndim == 1:
        data = data[None, :]
    return TrajectoryFrame(
        network=network,
        fname=p.name,
        source=source,
        logT=logT,
        logRho=logRho,
        age=data[:, 0],
        dt=data[:, 1],
        eps_nuc_raw=data[:, 2],
        eps_neu_raw=data[:, 3],
        X=data[:, 4:],
    )


def stall_row(X: np.ndarray, tol: float = STALL_TOL) -> int:
    """First row index at which the composition freeze sets in.

    Exact lift of the Step-5 rule: the first output interval whose
    max_i |dX_i| drops below ``tol`` marks the stall; if none does, the last
    row index is returned (so pre-stall selection drops only the final row).
    """
    dmax = np.abs(np.diff(X, axis=0)).max(axis=1)
    stalled = np.nonzero(dmax < tol)[0]
    return int(stalled[0]) if stalled.size else X.shape[0] - 1


def select_rows(
    traj: TrajectoryFrame, *, prestall: bool = True, tol: float = STALL_TOL
) -> np.ndarray:
    """Row indices eligible for physics analysis.

    ``prestall=True`` (the default and the guard) returns rows strictly
    before the stall onset; ``prestall=False`` must be passed explicitly to
    see post-stall rows (frozen non-equilibrium states — RESULTS.md
    2026-07-10). Row 0 (the initial state) is included; slice it off at the
    call site when diff-based quantities are needed.
    """
    if prestall:
        return np.arange(stall_row(traj.X, tol))
    return np.arange(traj.n_rows)


def _resolve_convention(convention: str | None) -> str:
    conv = convention if convention is not None else TRAJ_EPS_CONVENTION
    if conv is None:
        raise RuntimeError(
            "trajectory eps_nuc convention not pinned — run "
            "scripts/step6_eps_pin.py and set TRAJ_EPS_CONVENTION"
        )
    if conv not in ("integrated", "rate"):
        raise ValueError(f"unknown eps convention {conv!r}")
    return conv


def eps_nuc_rate(
    traj: TrajectoryFrame, *, convention: str | None = None
) -> np.ndarray:
    """eps_nuc as a RATE [erg/g/s] per row (interval-averaged, net of
    neutrino losses), under the pinned convention."""
    conv = _resolve_convention(convention)
    if conv == "rate":
        return traj.eps_nuc_raw.copy()
    with np.errstate(divide="ignore", invalid="ignore"):
        return traj.eps_nuc_raw / traj.dt


def eps_nuc_integrated(
    traj: TrajectoryFrame, *, convention: str | None = None
) -> np.ndarray:
    """eps_nuc INTEGRATED over each row's own dt [erg/g], net of neutrino
    losses, under the pinned convention."""
    conv = _resolve_convention(convention)
    if conv == "integrated":
        return traj.eps_nuc_raw.copy()
    return traj.eps_nuc_raw * traj.dt
