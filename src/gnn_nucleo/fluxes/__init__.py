"""Gross/net per-reaction flux derivation (Step 5 — stub).

Will derive forward/reverse gross fluxes f+, f-, the signed net flux
phi = f+ - f-, and the cancellation ratio kappa_r = |f+ - f-| / (f+ + f-)
from bbq single-zone output, in float64.

Contract: fluxes feed both the composition route (dY = nu phi) and the energy
route (e_nuc = sum_j Q_j(T) phi_j); the two must agree to <= 1% of |e_nuc|
across the 3-4 GK band (CLAUDE.md invariant #5).
"""
