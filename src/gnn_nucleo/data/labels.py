"""Zenodo training-label access, keyed strictly on ``state_id``.

``state_id`` is the 0-based row index within a network's row-aligned dt CSVs
(see ``schema.py``): (logT, logRho) is NOT unique (154,405 collisions per
network at 3-decimal rounding) and must never be a join key. This module is
the ONLY place label frames are joined; ``join_on_state_id`` refuses frames
that are not state_id-indexed, so a coordinate join cannot be expressed.

Units follow ``StepLabels``: eps columns are rescaled to physical units
(× ``EPS_NORMALIZATION``) on load; ``final_*`` stay as shipped — floored at
``FINAL_X_FLOOR`` = 1e-15 (values AT the floor are censored, not physical)
and float32-precision upstream even though parsed as float64.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.csv as pv

from .schema import (
    DT_LABELS,
    EPS_NORMALIZATION,
    EPS_NU_QUARANTINED,
    NETWORKS,
)

__all__ = ["training_csv_path", "load_step_frame", "join_on_state_id"]

_REPO = Path(__file__).resolve().parents[3]
TRAINING_DIR = _REPO / "data" / "zenodo" / "NuclearNeuralNetworks" / "training_sets"


def training_csv_path(network: str, dt_label: str) -> Path:
    """Path of one per-network per-dt training CSV (existence not checked)."""
    if network not in NETWORKS:
        raise ValueError(f"unknown network {network!r}")
    if dt_label not in DT_LABELS:
        raise ValueError(f"unknown dt_label {dt_label!r}; expected one of {DT_LABELS}")
    return TRAINING_DIR / network / f"{network}_{dt_label}_sec.csv"


def load_step_frame(
    network: str,
    dt_label: str,
    columns: list[str] | None = None,
    state_ids: list[int] | np.ndarray | None = None,
) -> pd.DataFrame:
    """Load label columns for one (network, dt) file, indexed by state_id.

    Parameters
    ----------
    columns : CSV columns to read (None = all). Reading a subset is much
        cheaper — pyarrow skips parsing the rest.
    state_ids : rows to keep, in the given order (None = all). These are row
        indices into the full file; the returned index holds them verbatim.

    Notes
    -----
    eps_nuc / eps_nu are returned in PHYSICAL units (× 1e16); eps_nu is
    refused for quarantined (network, dt_label) pairs. All floats float64.
    """
    path = training_csv_path(network, dt_label)
    convert = (
        pv.ConvertOptions(include_columns=list(columns)) if columns is not None else None
    )
    table = pv.read_csv(path, convert_options=convert)
    df = table.to_pandas()
    df.index = pd.RangeIndex(len(df), name="state_id")

    if "eps_nuc" in df.columns:
        df["eps_nuc"] = df["eps_nuc"].astype(np.float64) * EPS_NORMALIZATION
    if "eps_nu" in df.columns:
        if (network, dt_label) in EPS_NU_QUARANTINED:
            raise ValueError(
                f"eps_nu labels quarantined for ({network}, {dt_label}) — "
                "see schema.EPS_NU_QUARANTINED"
            )
        df["eps_nu"] = df["eps_nu"].astype(np.float64) * EPS_NORMALIZATION

    if state_ids is not None:
        ids = np.asarray(state_ids, dtype=np.int64)
        if ids.size and (ids.min() < 0 or ids.max() >= len(df)):
            raise IndexError(
                f"state_ids outside [0, {len(df)}) for {network} {dt_label}"
            )
        df = df.iloc[ids]
    return df


def join_on_state_id(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    how: str = "inner",
    validate: str | None = "one_to_one",
    suffixes: tuple[str, str] = ("_l", "_r"),
) -> pd.DataFrame:
    """Join two label/derived frames on their state_id index — the only
    sanctioned join. Frames whose index is not named ``state_id`` are
    refused, so joining on (logT, logRho) cannot be expressed here."""
    for name, df in (("left", left), ("right", right)):
        if df.index.name != "state_id":
            raise ValueError(
                f"{name} frame index is {df.index.name!r}, not 'state_id' — "
                "label joins happen on state_id ONLY (never on logT/logRho; "
                "see data/schema.py row-identity notes)"
            )
    return pd.merge(
        left,
        right,
        left_index=True,
        right_index=True,
        how=how,
        validate=validate,
        suffixes=suffixes,
    )
