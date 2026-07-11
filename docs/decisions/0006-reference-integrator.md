# 0006 — Reference integrator: augmented gross-Φ state, conservation-exact return, approximate sparse Jacobian
Date: 2026-07-11    Status: accepted

## Decision
`src/gnn_nucleo/fluxes/integrate.py` is the reference producer of Target-A
supervision pairs (Φ, ΔY = νΦ) from arbitrary initial states over arbitrary
dt at constant (T, ρ). Four settled points:

1. **Augmented state u = [Y, Φ] with GROSS per-column rates**:
   dY/dt = νR, dΦⱼ/dt = Rⱼ. Gross columns (not pair-netted φ) because
   ydot = νR is exact in the engine; net φ/κ are recovered downstream via
   `pair_col` exactly as `store.py` does. Error control runs on Y directly
   (per-species accuracy for trace isotopes), Φ rides along.

2. **The returned composition is Y0 + ν(Φ − Φ0)** — the ΔY = νΦ identity
   and baryon/charge conservation hold BY CONSTRUCTION (Cν = 0), in the
   spirit of the project's conservation-by-construction decode rule. The
   solver's error-controlled Y is exposed as `identity_resid`; measured
   2.1e-16 molar on the state-80 stiff relaxation (machine precision).

3. **Solver: scipy BDF with a sparse analytic Jacobian**
   J = [[νD, 0], [D, 0]], D = ∂R/∂Y from the reactant product rule (exact,
   slot products with the differentiated factor removed, no division).
   The ∂λ/∂Y chain (screening plasma state, tabular ρYₑ, Yₑ weighting) is
   deliberately NEGLECTED: measured to reach ~0.9× the structural column
   scale on random compositions (tests/test_integrate.py) — an inexact
   Jacobian affects step efficiency only, never correctness. Convergence
   evidence: BDF ≡ Radau ≡ BDF(rtol 1e-10) to 5e-8 rel on the stiffest
   test state. Tolerances rtol 1e-8 (bbq's eps), atol 1e-18 both blocks.
   Radau stays available as a cross-check method.

4. **Rates**: exact `engine.evaluate_lambda`/`evaluate_fluxes` arithmetic
   with Y-independent parts hoisted per (T, ρ) (`StatePoint`); Y clipped at
   0 inside rate evaluation only. RHS ≡ engine to ≤1e-12 rel (tested).

## Consequences
- One integration to dt = 1e2 s with t_eval at the nine measured label dts
  serves all nine labels of a state (scripts/step6_integrate_check.py).
- Label-agreement interpretation is T9-stratified: at T9 ≳ 5 the shipped
  labels carry the Appendix-B displaced pseudo-equilibrium (RESULTS.md
  2026-07-11) while this integrator carries pf-true rates — disagreement
  there measures the LABEL pathology, not integrator error.
- Energy identity ΣQⱼΦⱼ vs mass-excess bookkeeping is testable per state
  (invariant #5); gate ≤1% in the 3–4 GK band.

## Alternatives rejected
- Φ-only state with Y = Y0 + νΦ substituted into the RHS: identity exact
  but per-species error control is lost — trace-species ΔX accuracy becomes
  hostage to cancellation between large gross Φ errors.
- Y-only integration + quadrature of R(t) from dense output: ΔY = νΦ then
  holds only to quadrature error. Kept as the documented fallback if the
  augmented dimension (1669, mesa_151) ever makes sparse LU the bottleneck
  — not observed.

## Switch condition
Add the analytic Yₑ-chain Jacobian terms if BDF Newton convergence
degrades on production workloads (nfev per state ≫ the measured ~5e3 on
stiff states); switch to the Y-only+quadrature fallback if mesa_151
throughput falls below what Phase-1 auxiliary supervision needs
(threshold set by the step6_integrate_check.py feasibility row).
