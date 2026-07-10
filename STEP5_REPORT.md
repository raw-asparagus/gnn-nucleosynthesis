# Step 5 report — flux engine, label handshake, QSE/NSE solver, bridges (2026-07-10)

Every number below is measured and logged in RESULTS.md (sections dated
2026-07-10, Step 5) with script + commit provenance. New instruments:
`src/gnn_nucleo/fluxes/` (guards, DerivedRate replacement, compiled
evaluator, engine, store, handshake) and `src/gnn_nucleo/qse/` (coefficients,
NSE/QSE solvers, diagnostics). MESA/bbq trees untouched; data/zenodo/
read-only; all flux artifacts gitignored under data/fluxes/ with content
hashes in RESULTS.md.

## 1. Invariant guards (Task 0) — programmatic, tested

- `fluxes/guards.py`: pf gate (`PfGateError` — compilation refuses any
  surviving v-flag set), Appendix-B routing assertion (stock r23.05.1 values
  refused on gh-575 channels), screening pinned to chugunov_2007 (or off,
  validation only), ADR-0003 reconciled-build assertion.
- `data/labels.py::join_on_state_id` is the only label join; coordinate
  joins are inexpressible. CLAUDE.md records the Sobol grid as
  unseeded-scrambled, NON-REGENERABLE.

## 2. Flux engine (Task 1) — correct, 2–3 orders above the throughput gate

- All 280/672 raw v-flag reverses replaced positionally by
  `DerivedRate(source_rate=fwd, use_pf=True)`; zero failures; ν untouched.
- Compiled evaluator vs pynucastro scalar paths: worst λ rel 1.3e-12
  (gate 5e-12, fp-association floor); ν·R vs `evaluate_ydots` within
  1e-12 × per-species gross flux; conservation gate passes; mesa_probe24
  spot checks: clean forwards ≤0.004 dex, pf reverses ≤0.1 dex vs 24.08.1.
- κ at NSE (carrying strong pairs, UNSCREENED): median 2.6e-12 — the Step-4
  spurious floor (6.6e-2/1.3e-1) is eliminated. NEW: with the label
  screening config ON, κ at NSE has a REAL ~7e-2 offset (screening applies
  per reaction's own reactants: screened capture vs unscreened
  photodissociation). Step-6 κ thresholds must use unscreened κ for
  equilibrium detection or account for the offset.
- Throughput: 7.1e5 / 2.2e5 states/min/core (mesa_80/151) — gate ≥1e3.
  Coverage: 30k-state stratified subsample (screened + unscreened twins),
  20 trajectories/net, AND the FULL 1,041,400-state corpus per net
  (59 s / 171 s wall on 10 workers; 4.9 + 12 GB) — full-corpus κ/flux data
  already on disk for Step 6.

## 3. Handshake verdict (Task 2) — fluxes tied to the labels; no unexplained mesa_151 outliers

- Grid mode (dt₁ ≈ 1e-6 s): premise MEASURED VOID — Sobol compositions carry
  free nucleons (median X_neut 1.7e-2); 99.99–100% of cells have τ < dt.
  The shortest training label is a stiff relaxation, not a linear step
  (consequence for emulator design: dt=1e-6 labels encode full relaxations).
- Trajectory mode (intervals from 1e-10 s, trapezoid, RHS-stability filter,
  1e-15-floor censoring): rate-level residual |ΔX_pred−ΔX_lab|/(A·gross·dt)
  median 3.6e-3/2.8e-3; ≤5% for 90.3%/94.4% of 293k/597k linearizable cells.
  Net-tolerance agreement rises monotonically with per-isotope cancellation
  (0.94/0.97 at c ≥ 0.9) and with τ/Δt — departures track stiffness.
- Departure classification: 99.97–100% attributed to documented classes
  (DB-reverse pf provenance 69/64%, subfloor-controller 25/13%,
  weak-tabular interpolation 5/24%). Unexplained: mesa_80 ONE channel,
  9 cells (He3+Li7→n+p+2α, light multibody — footnoted); mesa_151 NONE.
- Screening confirmation: removing chugunov_2007 drops agreement 0.76→0.53.
- OPEN: trajectory-file eps_nuc units/sign not pinned — flux-route vs label
  energy comparison deferred (invariant #5 proper is engine-internal, Step 6).

## 4. QSE/NSE solver (Task 3) — cross-check exact; trajectory data anomalous

- NSE cross-check vs pynucastro on the 27-state grid: max |Δlog10 X| =
  2.7e-10 / 1.5e-10 (gate 1e-6), 27/27 states, Newton only. Coefficients
  match `_nucleon_fraction_nse` to ≤1e-12 at fixed potentials; QSE
  degenerates to NSE exactly when the group constraint is NSE-valued.
- **TRAJECTORY DATA ANOMALY (new, load-bearing):** the shipped test
  trajectories STALL — composition frozen from median age 2.2e5/3.9e4 s
  while their own eps_nuc keeps rising; frozen states are NOT NSE (T9=6.1
  file: si30-dominated vs NSE fe56). Engine agrees with the labels' EARLY
  evolution at the filename T9 (99% ≤5%, sharp scan peak at T9=6.1) — the
  stall is a bbq artifact once output dt (→1e10 s) outgrows the physics.
  Step 6 may use PRE-STALL rows only; relaxed-trajectory physics needs bbq
  reruns (→ CPU allocation, §7).
- r_QSE single-cluster plateau NOT confirmed on these anomalous trajectories
  (intra-group std ~1.3–1.5 dex vs non-group 2.4–3.5); deferred to reruns.
- κ↔δ consistency: anchor exact (δ≡0 at NSE ↔ κ median 2.6e-12); graded
  Spearman(log κ, log δ) = +0.39/+0.21 (p≈0) on pre-stall rows; no
  δ_r < 0.01 cells exist there (nothing equilibrated — consistent).

## 5. Preliminary findings (Task 4) — subsample + trajectory views

- κ_r on the TRAINING DISTRIBUTION: median ≈ 1.0 everywhere; {κ>0.1} covers
  97–100% of carrying pairs. Random compositions are nowhere near flux
  balance — the QSE cancellation structure lives on relaxed states only.
  Kill-test implication: Target A's active set is ~everything on the
  training grid; the interesting sparsity appears along trajectories.
- |dẎₑ| concentration: top-20 weak channels carry 93–99.9% in every stratum
  (top-5 ≈ 0.6) — strong concentration, feeds loss weighting.
- mesa_151 ⁴⁵Sc(p,γ)⁴⁶Ti: CONFIRMED as #2 of 251 inter-group carriers
  (share 0.094) on relaxed high-Yₑ QSE-window rows under the boundary-at-46
  group variant (default 24≤A<45 places ⁴⁵Sc outside the group — boundary
  placement is now a config variant; feeder Ca44(p,γ)Sc45 is #4 under the
  default). Invisible (rank 31) on the random subsample.
- mesa_80 empirical bridge set (no ⁴⁵Sc): Ne22(α,n)Mg25 (0.18),
  Al27(p,α)Mg24 (0.12), P31(p,α)Si28 (0.10), Na23(α,p)Mg26, Mg26(p,γ)Al27;
  top-20 boundary channels carry 0.86 of the inter-group flow.

## 6. Blocked / needs a human decision

- Nothing blocks Step 6. Carried flags: He3+Li7→n+p+2α handshake cells (9),
  be7 EC provenance, trajectory eps_nuc units, r_h1_h1_he4_to_he3_he3.
- Decision pending: gh-575 backport patch (unchanged from Step 4).
- The trajectory-stall anomaly caps what "trajectory-resolved" evidence
  Step 6 can claim — pre-stall rows only until reruns exist.

## 7. Manual items

- **4 TB superset email — SEND THIS WEEK.** Justification now assembled:
  (a) the training grid's dt=1e-6 labels are stiff relaxations, so
  flux-level supervision needs finer-dt data; (b) the shipped trajectories
  stall at non-equilibrium states (RESULTS 2026-07-10) — the 4 TB tree
  (finer timesteps) is the only shipped-adjacent source of valid relaxed
  trajectories; (c) Sobol grid non-regenerable — no same-distribution
  alternative exists.
- **CPU allocation:** does NOT gate Step 6 (full-corpus fluxes already
  computed locally in minutes). Wanted for bbq reruns of clean trajectories
  (stall anomaly) and any fresh-label generation.
- **GPU fleet + division-of-labor:** unchanged from Step 4; training does
  not start until the Step-6 kill-test verdict.
