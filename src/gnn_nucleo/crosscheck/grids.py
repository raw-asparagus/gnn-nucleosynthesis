"""Canonical Step-4/kill-test state grids (single source of truth).

Sourced: regime box from CLAUDE.md / project scope (T = 1.6-7.9 GK,
rho = 1e7-1e9 g/cm^3, 0.45 < Ye < 0.5); grid points chosen in the Step-2
brief and reused by scripts/run_killtest.py.
"""

from __future__ import annotations

from itertools import product

T9_GRID: tuple[float, ...] = (1.6, 2.5, 3.3, 4.0, 5.0, 6.3, 7.9)
RHO_GRID: tuple[float, ...] = (1e7, 1e8, 1e9)
YE_GRID: tuple[float, ...] = (0.45, 0.48, 0.498)

#: high-T subset where NSE is guaranteed (kappa-floor screen, Task 3)
T9_NSE: tuple[float, ...] = (5.0, 6.3, 7.9)


def state_grid(t9s: tuple[float, ...] = T9_GRID) -> list[tuple[float, float, float]]:
    """Full (T9, rho, ye) product grid in a stable order."""
    return [(t9, rho, ye) for t9, rho, ye in product(t9s, RHO_GRID, YE_GRID)]
