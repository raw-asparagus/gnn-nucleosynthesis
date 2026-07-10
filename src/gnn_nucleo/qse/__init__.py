"""QSE/NSE reference-abundance solver (Step 5 — stub).

Will compute quasi-statistical-equilibrium / nuclear-statistical-equilibrium
reference abundances ybar(T, rho, Ye) and the per-species departure
delta_r = |y - ybar| / ybar used by the Guidry equilibrium criterion
(epsilon sweep {3e-3, 1e-2, 3e-2}).

Contract: the equilibrium gate built from these quantities must NEVER include
weak-reaction columns in its eligible set (CLAUDE.md invariant #2) — the
eligible mask is constructed structurally from weak_mask, not by convention.
"""

from .coeffs import NseInputs, build_inputs, nse_log_coeffs
from .diagnostics import (
    delta_species,
    eligible_mask,
    load_group_mask,
    r_qse,
    reaction_delta,
)
from .solver import NSEResult, QSEResult, solve_nse, solve_qse

__all__ = [
    "NseInputs",
    "build_inputs",
    "nse_log_coeffs",
    "NSEResult",
    "QSEResult",
    "solve_nse",
    "solve_qse",
    "delta_species",
    "r_qse",
    "reaction_delta",
    "eligible_mask",
    "load_group_mask",
]
