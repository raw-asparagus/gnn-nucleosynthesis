"""Single-step dataset schema mirroring the Grichener et al. 2025 Zenodo sets.

Layout
------
One record = one (state, dt) pair. The underlying thermodynamic/composition
state comes from a Sobol sample (or, later, a real MESA track point); each
state is stepped at the nine timesteps of the network's measured dt grid,
giving nine records per state.

Row identity (``state_id``)
---------------------------
The raw CSVs carry NO sample-id column. The audited facts
(scripts/check_training_csvs.py; RESULTS.md 2026-07-08):

- the nine dt files of a network are exactly row-aligned — row i holds the
  same (logT, logRho, initial_*) state in every file;
- (logT, logRho) is NOT unique (154,405 of 1,041,400 rows collide — the
  columns are rounded to 3 decimals) and must never be used as a join key;
- the full initial state has zero duplicates.

Therefore ``state_id`` = the row index (0-based) within the row-aligned
per-network CSV set. It identifies the underlying state; (state_id,
dt_index) identifies a record. Splits are keyed on state_id only.

Timestep grid
-------------
``DT_GRID_SECONDS`` holds the NOMINAL 10^k decade values — labels for
indexing and file naming only. The real timesteps deviate from nominal by up
to ~5% and differ between networks (e.g. the "1e2" file is 105.08 s for
mesa_80 but 102.93 s for mesa_151). The measured per-network grids live in
``configs/dt_grid_measured.yaml`` (derived, full precision) and are loaded by
``load_measured_dt()``; validation compares against the measured value.

Units and normalization of raw labels
-------------------------------------
- ``eps_nuc`` (CSV) is the INTEGRATED specific nuclear energy release over
  the step [erg/g] — not a rate. ``eps_nu`` is the neutrino-loss RATE
  [erg/g/s]. Both are stored divided by ``EPS_NORMALIZATION`` = 1e16 in ALL
  18 training CSVs (upstream GenerateTrainingSets/NormalizeEps.py; the
  hinted alternate 1e13 normalization at dt ≥ 10 s was measured ABSENT from
  the training sets — see RESULTS.md 2026-07-08). Loaders must multiply by
  ``EPS_NORMALIZATION``; ``StepLabels`` carries physical units.
  TRAJECTORY (test-set output) files carry a DIFFERENT convention — see
  ``data/trajectories.py``: eps_nuc integrated per output row NET of
  neutrino losses, eps_neu a rate, and NO 1e16 normalization (pinned by
  scripts/step6_eps_pin.py; RESULTS.md 2026-07-11).
- ``EPS_NU_QUARANTINED`` lists (network, dt_label) pairs whose eps_nu labels
  failed the normalization-continuity check. Measured empty; the mechanism
  stays so any future re-extraction re-checks before training touches ε_ν.
- ``final_*`` mass fractions are floored at ``FINAL_X_FLOOR`` = 1e-15
  (upstream clamp before taking logs; measured exactly attained). Values at
  the floor are censored, not physical.
- Upstream NNN models and their label tensors are float32; this project's
  conservation checks and X_{t+dt} updates are float64 end-to-end
  (CLAUDE.md) — raw CSVs are parsed as float64.

Storage decision (documented, not yet implemented)
--------------------------------------------------
- **HDF5** for arrays: large homogeneous float blocks (X, X', per-reaction
  fluxes) with chunked partial reads — training never needs whole-file loads,
  and float64 label arrays must round-trip losslessly.
- **Parquet** for tabular metadata: sample IDs, split assignment, provenance
  tags, per-record scalars — columnar predicate pushdown ("all test rows of
  mesa_80 at dt_index 3") without touching the arrays.
Cross-reference is by ``state_id`` + ``dt_index``, which together identify a
record uniquely within a network.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

__all__ = [
    "NETWORKS",
    "DT_GRID_SECONDS",
    "DT_LABELS",
    "N_TIMESTEPS",
    "EPS_NORMALIZATION",
    "EPS_NU_QUARANTINED",
    "FINAL_X_FLOOR",
    "load_measured_dt",
    "Provenance",
    "StepInputs",
    "StepLabels",
    "DerivedExtension",
    "SplitSpec",
]

# Species counts of the two MESA softwired networks under study.
NETWORKS: dict[str, int] = {"mesa_80": 80, "mesa_151": 151}

# Nine NOMINAL log-spaced timesteps spanning [1e-6, 1e2] s — one per decade.
# Labels only (file naming, dt_index semantics); the REAL grids are measured
# per network and loaded via load_measured_dt().
N_TIMESTEPS: int = 9
DT_GRID_SECONDS: tuple[float, ...] = tuple(
    10.0 ** (-6 + 8 * k / (N_TIMESTEPS - 1)) for k in range(N_TIMESTEPS)
)
DT_LABELS: tuple[str, ...] = (
    "1e-6", "1e-5", "1e-4", "1e-3", "1e-2", "1e-1", "1e0", "1e1", "1e2",
)

# Raw eps_nuc/eps_nu CSV columns are stored divided by this (upstream
# NormalizeEps.py); measured uniform across all 18 files (RESULTS.md).
EPS_NORMALIZATION: float = 1e16

# (network, dt_label) pairs whose eps_nu labels failed the normalization
# continuity check in scripts/check_training_csvs.py. Measured EMPTY on
# 2026-07-08; loaders must refuse eps_nu labels listed here.
EPS_NU_QUARANTINED: frozenset[tuple[str, str]] = frozenset()

# Upstream clamp applied to final_* before logging; values AT the floor are
# censored, not physical (measured exactly attained in both networks).
FINAL_X_FLOOR: float = 1e-15

_MEASURED_DT_PATH = Path(__file__).resolve().parents[3] / "configs" / "dt_grid_measured.yaml"


@cache
def load_measured_dt(network: str) -> tuple[float, ...]:
    """Measured dt grid [s] for ``network``, in dt_index order.

    Reads ``configs/dt_grid_measured.yaml`` (derived by
    scripts/check_training_csvs.py from the Age column of the real CSVs) —
    never hardcoded, never the nominal decades.
    """
    import yaml

    if network not in NETWORKS:
        raise ValueError(f"unknown network {network!r}")
    with open(_MEASURED_DT_PATH) as fh:
        grids = yaml.safe_load(fh)
    grid = grids[network]
    return tuple(float(grid[label]) for label in DT_LABELS)


class Provenance(enum.StrEnum):
    """Origin tag every derived quantity must carry (CLAUDE.md convention).

    SOURCED  — taken from a citation / upstream dataset as-is.
    DERIVED  — computed by a script in ``scripts/`` from sourced inputs.
    MEASURED — measured in this project; must have a RESULTS.md row.
    """

    SOURCED = "sourced"
    DERIVED = "derived"
    MEASURED = "measured"


@dataclass(frozen=True)
class StepInputs:
    """Pre-step state for one record.

    Parameters
    ----------
    state_id : int
        Row index (0-based) of the underlying state within the row-aligned
        per-network CSV set — see the module docstring for why this, and not
        (logT, logRho), is the identity. The split key — never split on the
        record level.
    network : str
        Key into ``NETWORKS``.
    log_T : float
        log10 temperature [K].
    log_rho : float
        log10 density [g/cm^3].
    X : tuple[float, ...]
        Mass fractions, length ``NETWORKS[network]``, float64.
    dt_index : int
        Index into the dt grid (0 = "1e-6" … 8 = "1e2", see ``DT_LABELS``).
    dt_seconds : float
        Timestep value; must equal the MEASURED grid value
        ``load_measured_dt(network)[dt_index]`` (rel_tol 1e-9).
    """

    state_id: int
    network: str
    log_T: float
    log_rho: float
    X: tuple[float, ...]
    dt_index: int
    dt_seconds: float

    def __post_init__(self) -> None:
        if self.network not in NETWORKS:
            raise ValueError(f"unknown network {self.network!r}")
        if len(self.X) != NETWORKS[self.network]:
            raise ValueError(
                f"X has {len(self.X)} entries, expected {NETWORKS[self.network]}"
                f" for {self.network}"
            )
        if not 0 <= self.dt_index < N_TIMESTEPS:
            raise ValueError(f"dt_index {self.dt_index} outside [0, {N_TIMESTEPS})")
        measured = load_measured_dt(self.network)[self.dt_index]
        if not math.isclose(self.dt_seconds, measured, rel_tol=1e-9):
            raise ValueError(
                f"dt_seconds {self.dt_seconds!r} != measured grid value "
                f"{measured!r} for {self.network}[{self.dt_index}] "
                f"(label {DT_LABELS[self.dt_index]!r})"
            )


@dataclass(frozen=True)
class StepLabels:
    """Post-step targets for one record, in PHYSICAL units.

    Loaders converting raw CSV rows must multiply eps_nuc/eps_nu by
    ``EPS_NORMALIZATION`` and must refuse eps_nu for (network, dt_label)
    pairs in ``EPS_NU_QUARANTINED``.

    Parameters
    ----------
    X_post : tuple[float, ...]
        Post-step mass fractions, same length/order as the input X, float64.
        Raw values are floored at ``FINAL_X_FLOOR`` (censored below 1e-15).
    e_nuc : float
        INTEGRATED specific nuclear energy release over the step [erg/g].
    neutrino_loss : float
        Neutrino energy loss RATE (ε_ν) [erg/g/s].
    """

    X_post: tuple[float, ...]
    e_nuc: float
    neutrino_loss: float


@dataclass(frozen=True)
class DerivedExtension:
    """Per-reaction derived quantities added in later steps (Steps 3/5/6).

    All fields default to ``None`` (absent in raw Zenodo data). When present,
    each is a tuple of length n_reactions (network-dependent), float64, and
    ``provenance`` states how it was produced.

    Fields
    ------
    f_plus, f_minus : gross forward/reverse fluxes.
    phi             : signed net flux, f+ - f-.
    kappa           : cancellation ratio |f+ - f-| / (f+ + f-).
    delta           : Guidry departure |y - ybar| / ybar (per species).
    y_qse           : QSE reference abundances ybar (per species).
    """

    f_plus: tuple[float, ...] | None = None
    f_minus: tuple[float, ...] | None = None
    phi: tuple[float, ...] | None = None
    kappa: tuple[float, ...] | None = None
    delta: tuple[float, ...] | None = None
    y_qse: tuple[float, ...] | None = None
    provenance: Provenance = Provenance.DERIVED


@dataclass(frozen=True)
class SplitSpec:
    """Leakage-safe train/val/test split, keyed on ``state_id``.

    All nine timestep records of one underlying state share its ``state_id``
    and therefore land in the same split — the same thermodynamic/composition
    state never appears in train and test at different dt.

    Use ``validate()`` before persisting; it raises on any overlap.
    """

    train_ids: frozenset[int] = field(default_factory=frozenset)
    val_ids: frozenset[int] = field(default_factory=frozenset)
    test_ids: frozenset[int] = field(default_factory=frozenset)

    def validate(self) -> None:
        """Raise ``ValueError`` if any state_id appears in more than one split."""
        overlaps = {
            "train/val": self.train_ids & self.val_ids,
            "train/test": self.train_ids & self.test_ids,
            "val/test": self.val_ids & self.test_ids,
        }
        bad = {k: sorted(v) for k, v in overlaps.items() if v}
        if bad:
            raise ValueError(f"split leakage — overlapping state_ids: {bad}")

    def split_of(self, state_id: int) -> str | None:
        """Return 'train' / 'val' / 'test' for a state_id, or None if unassigned."""
        if state_id in self.train_ids:
            return "train"
        if state_id in self.val_ids:
            return "val"
        if state_id in self.test_ids:
            return "test"
        return None
