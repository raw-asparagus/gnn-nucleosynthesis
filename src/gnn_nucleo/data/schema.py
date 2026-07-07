"""Single-step dataset schema mirroring the Grichener et al. 2025 Zenodo sets.

Layout
------
One record = one (state, dt) pair. The underlying thermodynamic/composition
state comes from a Sobol sample (or, later, a real MESA track point); each
state is stepped at the nine log-spaced timesteps in ``DT_GRID``, giving nine
records per state. Records carry the Sobol sample ID so splits can be made
leakage-safe (see ``SplitSpec``).

Inputs:  log10 T [K], log10 rho [g/cm^3], composition mass fractions X
         (length = species count of the network), dt index into DT_GRID and
         its value in seconds.
Labels:  post-step composition X', specific nuclear energy generation e_nuc,
         neutrino loss.

Derived extensions (filled in later Phase-0 steps, absent in raw data): gross
forward/reverse fluxes f+, f-, signed net flux phi = f+ - f-, cancellation
ratio kappa_r, Guidry departure delta_r = |y - ybar|/ybar, and QSE reference
abundances ybar. Every derived array carries a ``Provenance`` tag.

Storage decision (documented, not yet implemented)
--------------------------------------------------
- **HDF5** for arrays: large homogeneous float blocks (X, X', per-reaction
  fluxes) with chunked partial reads — training never needs whole-file loads,
  and float64 label arrays must round-trip losslessly.
- **Parquet** for tabular metadata: sample IDs, split assignment, provenance
  tags, per-record scalars — columnar predicate pushdown ("all test rows of
  mesa_80 at dt_index 3") without touching the arrays.
Cross-reference is by ``sobol_id`` + ``dt_index``, which together identify a
record uniquely within a network.

All conservation-relevant quantities are float64 end-to-end (CLAUDE.md).
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass, field

__all__ = [
    "NETWORKS",
    "DT_GRID_SECONDS",
    "N_TIMESTEPS",
    "Provenance",
    "StepInputs",
    "StepLabels",
    "DerivedExtension",
    "SplitSpec",
]

# Species counts of the two MESA softwired networks under study.
NETWORKS: dict[str, int] = {"mesa_80": 80, "mesa_151": 151}

# Nine log-spaced timesteps spanning [1e-6, 1e2] s — one per decade.
N_TIMESTEPS: int = 9
DT_GRID_SECONDS: tuple[float, ...] = tuple(
    10.0 ** (-6 + 8 * k / (N_TIMESTEPS - 1)) for k in range(N_TIMESTEPS)
)


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
    sobol_id : int
        ID of the underlying Sobol sample (thermodynamic/composition state).
        The split key — never split on the record level.
    network : str
        Key into ``NETWORKS``.
    log_T : float
        log10 temperature [K].
    log_rho : float
        log10 density [g/cm^3].
    X : tuple[float, ...]
        Mass fractions, length ``NETWORKS[network]``, float64.
    dt_index : int
        Index into ``DT_GRID_SECONDS``.
    dt_seconds : float
        Timestep value; must equal ``DT_GRID_SECONDS[dt_index]``.
    """

    sobol_id: int
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
        if not math.isclose(self.dt_seconds, DT_GRID_SECONDS[self.dt_index], rel_tol=1e-12):
            raise ValueError(
                f"dt_seconds {self.dt_seconds!r} != DT_GRID_SECONDS[{self.dt_index}]"
            )


@dataclass(frozen=True)
class StepLabels:
    """Post-step targets for one record.

    Parameters
    ----------
    X_post : tuple[float, ...]
        Post-step mass fractions, same length/order as the input X, float64.
    e_nuc : float
        Specific nuclear energy generation over the step [erg/g/s].
    neutrino_loss : float
        Neutrino energy loss over the step [erg/g/s].
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
    """Leakage-safe train/val/test split, keyed on Sobol sample ID.

    All nine timestep records of one underlying state share its ``sobol_id``
    and therefore land in the same split — the same thermodynamic/composition
    state never appears in train and test at different dt.

    Use ``validate()`` before persisting; it raises on any overlap.
    """

    train_ids: frozenset[int] = field(default_factory=frozenset)
    val_ids: frozenset[int] = field(default_factory=frozenset)
    test_ids: frozenset[int] = field(default_factory=frozenset)

    def validate(self) -> None:
        """Raise ``ValueError`` if any Sobol ID appears in more than one split."""
        overlaps = {
            "train/val": self.train_ids & self.val_ids,
            "train/test": self.train_ids & self.test_ids,
            "val/test": self.val_ids & self.test_ids,
        }
        bad = {k: sorted(v) for k, v in overlaps.items() if v}
        if bad:
            raise ValueError(f"split leakage — overlapping sobol_ids: {bad}")

    def split_of(self, sobol_id: int) -> str | None:
        """Return 'train' / 'val' / 'test' for a sample ID, or None if unassigned."""
        if sobol_id in self.train_ids:
            return "train"
        if sobol_id in self.val_ids:
            return "val"
        if sobol_id in self.test_ids:
            return "test"
        return None
