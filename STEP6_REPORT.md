# Step 6 report — relaxed manifold, kill-test verdict, label pathology (2026-07-12)

New instruments: `src/gnn_nucleo/killtest/`, `src/gnn_nucleo/fluxes/integrate.py`,
`src/gnn_nucleo/data/trajectories.py`, `scripts/bbq_campaign/`. All numbers are
measured (RESULTS.md 2026-07-11/12 rows; scripts named there). ADRs 0005, 0006.

## 1. eps_nuc pin + guards (Task 0)
- Trajectory-file eps_nuc PINNED: INTEGRATED over the row's own dt [erg/g],
  NET of neutrino losses, no 1e16 normalization (sign agreement 0.993/0.998,
  log-ratio IQR ≈ 0, slope vs dt-decade 0.000 across 20 decades; the rate
  reading shows the wrong-convention slope +1.00). Matches bbq source
  (lib_bbq.f90:453). Converters + guard in `data/trajectories.py`; Step-5
  OPEN item retired.
- Stall guard codified with TWO semantics: `terminal` (default; excludes only
  a trajectory-ending quiet tail) and `first_quiet` (Step-5 rule, = arrival
  at the attractor). The rules differ on 459/1508 shipped files: after
  arrival, composition keeps drifting under weak reactions (eps_nuc rising) —
  the Step-5 "stall" anomaly is now fully mechanistic (see §2b).
- CLAUDE.md conventions codified: two κ conventions (unscreened for
  detection), Si-group boundary as a config variant, Target-A Φ = ∫φ dt.

## 2. Rerun campaign (Task 1) — and the label-pathology discovery
a. Campaign: 418/418 bbq runs OK (zero failures), ~54 core-h, hydrostatic
   mode @ 40 pts/decade from 1e-8 s (ADR 0005; stock r23.05.1 = label
   config). Families: 20 shipped-initial + 63 canonical + 126 sobol per net.
   Ingested: 171,904 rows/net × {chugunov, unscreened} into FluxStore
   (hashes in RESULTS). Early-time comparability vs shipped at identical
   (T, ρ, X₀): species-age agreement median 0.996/0.998. Shipped-class
   mid-burn stall artifact ABSENT in reruns.
b. **HEADLINE FINDING — the shipped TRAINING LABELS at T9 ≳ 5 carry the
   MESA gh-575/Appendix-B bug**: 100% of sampled hot states (both nets) sit
   6.7–13.0 dex from true NSE at displaced pseudo-equilibria (si30-class at
   high ρ, c12/o16-class at low ρ), frozen across dt decades. Attribution
   is dispositive: stock r23.05.1 bbq reproduces the labels to 0.01–0.03
   dex; MESA 24.08.1 (fix verified) relaxes to NSE, agreeing with our
   pf-true integrator and independent Saha solver. Controlling channels =
   the chapter-8 1→3 reverses (c12→3α class) found "beyond the paper" in
   Step 4. The labels' Yₑ evolution itself is wrong at T9 ≳ 5 (0.4713 vs
   0.4619 at the witness state). Supersedes "labels used FIXED MESA"
   (checklist annotated). The Step-5 trajectory stall = arrival at these
   displaced attractors. Novelty sweep: finding appears UNREPORTED anywhere
   (docs/novelty/2026-07-11-step6-phase-boundary.md) — candidate standalone
   publication.
c. Terminal T9 ≥ 5 rerun states: 8.6/9.0 dex from NSE = the displaced
   attractor (expected on stock; 24.08.1 witnesses are the physics anchor).
   r_QSE single-cluster plateau NOT confirmed on clean data (0/303, 0/316
   rows < 0.1 dex) — Step-5 deferral retired with a negative verdict.

## 3. Kill-test, both distributions (Task 2)
- Training grid (corpus scale, 1.03M states/net): vacuous pass confirmed —
  frac κ>0.1 = 0.974–0.999 everywhere, κ<1e-3 = 0.000; cond(S_active) =
  cond(ν net columns) = 41.8/57.4.
- Relaxed manifold (4,693 rows/net; the verdict distribution):
  κ↔δ Spearman +0.491/+0.498; frac κ>0.1 down to 0.70/0.64 at T9 [5.0,6.3);
  Guidry maskable set EMPTY at every ε (median = p90 = 0; the manifold's
  own equilibria are displaced) ⇒ cond(S_active) = 41.8/57.4, ≪ 1e6 gate;
  |dẎₑ| coverage = 1.0000 (weak κ = 1.0 verified on 8.8M/33.2M samples);
  dominant-isotope coverage SPLIT — median species ≥95% except [5.0,6.3)
  (0.62–0.80), worst species per row 0.002–0.17 across [4.0,6.3);
  spread ≤ 24% median (< 30% FAIL line); churn ≤ 0.03 flips/step; top-5
  |dẎₑ| channels carry 0.96/0.75 (⁵⁶Ni EC #1); bridge sets finalized
  (mesa_80: Ne22(α,n)Mg25 / Al27(p,α)Mg24 / P31(p,α)Si28; mesa_151 incl.
  Ca44(p,γ)Sc45 feeder) and **⁴⁵Sc(p,γ)⁴⁶Ti rank 2/251** (a24_46) on the
  full relaxed manifold; "6–8 orders" timescale figure RETIRED by
  measurement (medians −12.2…+1.4 dex — no separated fast sector).

## 4. Integrated-flux prototype (Task 3)
- `fluxes/integrate.py` (ADR 0006): augmented [Y, Φ] BDF, sparse analytic
  Jacobian; returned Y := Y0 + νΦ ⇒ ΔY = νΦ and conservation EXACT by
  construction (solver-vs-identity residual 2.1e-16); BDF ≡ Radau ≡
  rtol 1e-10 to 5e-8 rel.
- Same-fluxes energy identity: frac ≤1% = 1.000 everywhere measured
  (median ~1e-5; near-algebraic with constant Q). Independent-leg
  cross-check 0.979/0.996 median — mesa_80 at 2.1%, OPEN margin item.
- Label agreement (T9 < 5, where labels are physical): QSE window
  0.74–0.99 of species in the handshake band across the nine dts.
- Throughput: ≥383/1,519 s per nine-dt state (17/36, 10/24 states censored
  at 4,800 s — all censored are T9 ≥ 5; cause diagnosed: the neglected
  tabular-EC ρYₑ Jacobian chain dominates the hot weak-drift phase; the
  ADR-0006 contingency is the unlock). Corpus-scale local Φ generation
  INFEASIBLE (≥1.1e5/4.4e5 core-h); stratified T9 < 5 subsets feasible
  (10³–10⁴ states ≈ 4–40 core-days) ⇒ Phase-1 supervision = shipped-ΔX
  primary + local-Φ auxiliary on QSE-window subsets.

## 5. THE VERDICT
**TARGET A — full-width (the hybrid's equilibrium mask is measured EMPTY on
the relaxed label manifold); conditional band T9 ∈ [4.0, 6.3) as stated in
docs/phase0-killtest-verdict.md.** No Target-B switch condition fires.

## 6. Blocked / human decisions (do not proceed without them)
1. **Benchmark-vs-physics fork at T9 ≳ 5**: should Phase 1 train on the
   shipped (bug-displaced) labels there (benchmark fidelity to NNN) or on
   corrected physics (24.08.1-class reruns / pf-true Φ labels)? Affects
   supervision, evaluation, and any NNN comparison claims.
2. **External communication**: the label pathology implicates the published
   NNN training sets (and NNN itself trained on them). Contact the
   Grichener et al. authors? Timing interacts with our Paper-1 plan (the
   novelty sweep recommends accelerating it).
3. gh-575 backport patch decision (carried from Step 4; less urgent now —
   24.08.1-bbq exists and serves as the physics witness).

## 7. Manual items
- 4 TB bbq-superset email: **SENT, awaiting reply** (user, 2026-07-11).
  Note the request's value changed: the superset shares the label MESA, so
  it extends the BENCHMARK manifold, not the physics-true one.
- GPU fleet: unchanged; becomes BLOCKING at Step-7 ablations.
- Division-of-labor: unchanged. CPU allocation: now Phase-1-only (the
  Step-6 campaign consumed ~54 core-h locally; local capacity sufficed).
