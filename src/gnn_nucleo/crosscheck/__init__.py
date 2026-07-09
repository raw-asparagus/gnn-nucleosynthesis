"""Step-4 MESA <-> pynucastro cross-check package.

Reaction-set reconciliation, rate-level numerical comparison, kappa-floor
screen inputs, and the missing-Sobol-rows analysis.  The Fortran probe that
feeds this lives in src/mesa_probes/ (built by its build.sh).
"""

from .canonical import (
    directed_key,
    from_mesa,
    from_pyna,
    pair_key,
    parse_participants,
    reverse_key,
)
from .grids import RHO_GRID, T9_GRID, T9_NSE, YE_GRID, state_grid
from .probe import grid_stdin, probe_available, run_probe, t9_stdin
from .reconcile import (
    DISPOSITIONS,
    diff_inventories,
    load_disposition,
    pyna_inventory,
    validate_disposition,
    write_disposition,
)
from .sobol import (
    BOX,
    load_grid_file,
    match_rows_to_grid,
    normalize_states,
    xsum_initial,
    ye_from_initial,
)

__all__ = [
    "BOX",
    "DISPOSITIONS",
    "RHO_GRID",
    "T9_GRID",
    "T9_NSE",
    "YE_GRID",
    "diff_inventories",
    "directed_key",
    "from_mesa",
    "from_pyna",
    "grid_stdin",
    "load_disposition",
    "load_grid_file",
    "match_rows_to_grid",
    "normalize_states",
    "pair_key",
    "parse_participants",
    "probe_available",
    "pyna_inventory",
    "reverse_key",
    "run_probe",
    "state_grid",
    "t9_stdin",
    "validate_disposition",
    "write_disposition",
    "xsum_initial",
    "ye_from_initial",
]
