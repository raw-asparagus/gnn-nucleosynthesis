"""Gross/net per-reaction flux derivation (Step 5 — stub).

Will derive forward/reverse gross fluxes f+, f-, the signed net flux
phi = f+ - f-, and the cancellation ratio kappa_r = |f+ - f-| / (f+ + f-)
from bbq single-zone output, in float64.

Contract: fluxes feed both the composition route (dY = nu phi) and the energy
route (e_nuc = sum_j Q_j(T) phi_j); the two must agree to <= 1% of |e_nuc|
across the 3-4 GK band (CLAUDE.md invariant #5).

Inherited Step-4 gates are enforced programmatically in ``guards`` (pf gate,
Appendix-B routing, screening pin, ADR-0003 build assertion); every flux/kappa
entry point must pass through them.
"""

from .guards import (
    PfGateError,
    assert_appendixb_routing,
    assert_pf_gate,
    assert_reconciled_build,
    assert_screening_allowed,
)

__all__ = [
    "PfGateError",
    "assert_appendixb_routing",
    "assert_pf_gate",
    "assert_reconciled_build",
    "assert_screening_allowed",
]
