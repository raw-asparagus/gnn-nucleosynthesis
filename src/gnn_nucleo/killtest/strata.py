"""Kill-test stratum grid — single source for (T9, Yₑ) binning.

Edges are the Step-5 subsample strata (data/subsample.py; sourced from the
regime box + kill-test grid). Lifted here so scripts stop redefining them.
"""

from __future__ import annotations

import numpy as np

__all__ = ["T9_EDGES", "YE_EDGES", "T9_LABELS", "YE_LABELS", "assign_strata"]

T9_EDGES = np.array([1.6, 2.5, 3.3, 4.0, 5.0, 6.3, 7.95])
YE_EDGES = np.array([0.45, 0.4667, 0.4833, 0.5001])
T9_LABELS = ["[1.6,2.5)", "[2.5,3.3)", "[3.3,4.0)", "[4.0,5.0)", "[5.0,6.3)", "[6.3,7.95)"]
YE_LABELS = ["[.45,.467)", "[.467,.483)", "[.483,.5]"]


def assign_strata(T: np.ndarray, ye: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(t9_bin, ye_bin) per state; −1 where outside the edges. T in K."""
    t9 = np.asarray(T, dtype=np.float64) / 1e9
    tb = np.digitize(t9, T9_EDGES) - 1
    yb = np.digitize(np.asarray(ye, dtype=np.float64), YE_EDGES) - 1
    tb[(tb < 0) | (tb >= len(T9_EDGES) - 1)] = -1
    yb[(yb < 0) | (yb >= len(YE_EDGES) - 1)] = -1
    return tb, yb
