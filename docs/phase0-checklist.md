# Phase-0 measurement program (living checklist)

Source: Consolidated Architecture Specification §7 (docs/reports/). Each item is a
measurement only the bbq/MESA data can settle. Tick when measured; record value, date,
and the script that produced it (derived-label discipline). The `docs-sync` agent
updates this file; the `physics-auditor` agent produces the numbers.

Operative gate until item 12 is measured: per-step |ΔYₑ| ≲ 3e-6 (systematic accumulation).

| # | Done | Measurement | Sets / gates | Measured value (script, date) |
|---|------|-------------|--------------|-------------------------------|
| 1 | [x] | Reaction count + graph radius/diameter of mesa_80/151/204 (pynucastro export) | Depth K ≈ ⌈radius⌉+2; flux-head output dim | 2026-07-08: mesa_80 610 reactions / mesa_151 1522, PROVISIONAL rate set pending Step-4 MESA cross-check (scripts/graph_metrics.py, RESULTS.md 2026-07-08). 2026-07-09 UPDATE — PROVISIONAL caveat RETIRED by measurement (Step 4 Task 1): reconciled against MESA r23.05.1 softwired nets, MESA_ONLY = 0 on both networks and post-drop counts equal MESA exactly — mesa_80: **607** reactions, mesa_151: **1518** (= flux-head output dims); conservation gate + projector re-passed at unchanged tolerances; bipartite radius 3 / diameter 6 unchanged ⇒ K = 5 (K = 4 with I→I edges); mesa_204 not in scope of the shipped data (measured, scripts/reconcile_reactions.py + scripts/export_stoich_matrix.py, commit b559dde, RESULTS.md 2026-07-09; ADR 0003) |
| 2 | [ ] | Feature distributions of all proposed channels across the regime box | Normalization; dead-channel detection | |
| 3 | [ ] | Per-channel ablation of the 4 added physics channels (retain if ≥0.005 MAE) | Component A feature set | |
| 4 | [ ] | Weight-shared vs untied processor at equal step count (within 0.01 MAE?) | Recurrent vs untied default; latent-ODE option | |
| 5 | [ ] | Zero-shot mesa_80→151 transfer on neutron-rich isotopes (≤2× internal Yₑ error?) | Size-transfer claim (transferable vs adaptable) | |
| 6 | [x] | Per-reaction κ_r = \|net\|/(gross_f+gross_r) distribution | Target A vs B; mask design; **the load-bearing unknown** | Step-5 delivered the instrument + first distributions (measured, scripts/step5_run_fluxes.py + step5_bridges.py, commit d1a9c4a, RESULTS.md 2026-07-10): pf gate implemented (DerivedRate(use_pf=True) compiled in, PfGateError otherwise); κ at NSE unscreened median 2.6e-12 (floor eliminated); label-screening config adds a REAL ~7e-2 κ offset at NSE (per-reaction screening asymmetry) — equilibrium detection must use UNSCREENED κ; on the TRAINING DISTRIBUTION κ ≈ 1 everywhere ({κ>0.1} covers 97–100% of carrying pairs — random compositions are nowhere near flux balance); full-corpus per-reaction fluxes precomputed (data/fluxes/, hashes in RESULTS.md). Remaining for Step 6: κ on RELAXED states (pre-stall trajectory rows only — shipped trajectories stall, RESULTS.md anomaly row) + the Target-A active-set verdict. 2026-07-12 UPDATE — both remaining items MEASURED and CLOSED (Step 6): training-grid picture confirmed at full corpus scale (1,034,704 in-strata states/net; frac κ>0.1 = 0.985–0.999 / 0.974–0.997, mesa_80/151); on the RELAXED manifold (20 shipped + 209 local bbq rerun trajectories/net, 4,693 sampled rows/net, unscreened κ, terminal-tail row selection) the distribution is STRUCTURED: frac κ>0.1 falls to 0.70/0.64 at T9 [5.0,6.3), κ-balanced (κ<1e-3) pairs ≤ 0.4% of carrying pairs everywhere — a cancellation CONTINUUM, not a clean equilibrated sector; Target-A active-set VERDICT RENDERED: **TARGET A, full-width flux head, no Guidry mask deployed** (conditional statement for T9 ∈ [4.0,6.3) in the verdict doc) (measured, scripts/run_killtest.py --training-grid / --relaxed --include-reruns, commits 590dfcd/c7a3b2e, RESULTS.md 2026-07-11/12; docs/phase0-killtest-verdict.md 2026-07-12) |
| 7 | [x] | cond(ν) full and active-set | Target A→B switch at cond(S_active) > 1e6 | FULL: cond(ν) = 41.7 (mesa_80) / 57.6 (mesa_151), nullity 1; cond(CCᵀ) = 3.9e4 / 1.0e5 (scripts/graph_metrics.py, 2026-07-08, RESULTS.md). Active-set cond(S_active) is the Step-6 kill-test quantity — row stays open until then. 2026-07-12 CLOSED (Step 6 kill-test): cond(S_active) = **41.8 / 57.4** (mesa_80/151; rank-revealing definition, ν restricted to net columns — conservation left-null vectors structural; full ν 41.6 / 57.9) at every ε, on both the training grid and the relaxed manifold, because the Guidry maskable set is measured EMPTY (row 8) ⇒ S_active = all net columns — ≪ the 1e6 gate, no Target-A→B switch (measured, scripts/run_killtest.py, commits 590dfcd/c7a3b2e, RESULTS.md 2026-07-11/12; docs/phase0-killtest-verdict.md) |
| 8 | [x] | Guidry ε sweep {3e-3, 1e-2, 3e-2} on Si-burning trajectories | Mask threshold; ε≈0.01 transfer hypothesis | 2026-07-12 MEASURED (Step 6, relaxed manifold): maskable columns per row median AND p90 = **0 at every ε, both nets** — δ_r vs true (Saha) NSE effectively never crosses threshold, because the manifold's own equilibria are Appendix-B bug-displaced (cross-ref RESULTS.md 2026-07-11 label-pathology rows). Mask design settled by EMPTINESS: no Guidry mask deployed (κ diagnostics carried as features); the ε≈0.01 transfer hypothesis is moot on this data (measured, scripts/run_killtest.py --relaxed --include-reruns, commit c7a3b2e, RESULTS.md 2026-07-12; docs/phase0-killtest-verdict.md) |
| 9 | [x] | Mask membership churn per step along real T(t), ρ(t) tracks | Hybrid vs frozen-Guidry fallback (freeze if >5%/step) | 2026-07-12 MEASURED (Step 6): flips/step median 0.00–0.03 (churn fraction ≤ 0.002%/step), n = 35 QSE-window trajectories, per output step, at every ε, both nets — nowhere near the 5%/step freeze trigger; the hybrid-vs-frozen decision is settled by mask EMPTINESS (row 8), not churn (measured, scripts/run_killtest.py --relaxed --include-reruns, commit c7a3b2e, RESULTS.md 2026-07-12; docs/phase0-killtest-verdict.md) |
| 10 | [x] | Target B projection drift at realistic (20-decade) dynamic range | Target B viability | max relative constraint residual 6.7e-17 / 1.0e-16 (mesa_80/151) across dY scales 1e0…1e-20, gate ≤ 1e-12; weak dYₑ preserved to ≤ 3.4e-21 (scripts/check_projector.py, 2026-07-08, RESULTS.md). Static-operator viability confirmed; training-stability half of the question stays with the kill-test |
| 11 | [x] | e_nuc flux-route − composition-route residual, 3–4 GK band (≤1%?) | Energy-head partition-function consistency | Prerequisite convention pin MEASURED (Step 6 Task 0), retiring the Step-5 open item "trajectory eps_nuc units not pinned": trajectory-file eps_nuc is INTEGRATED per output row [erg/g] over the row's own dt, NET of neutrino losses, NO 1e16 normalization (the training CSVs differ: ÷1e16), and eps_neu is a RATE [erg/g/s] — Step-5's rate-vs-column comparison was a convention mismatch, not an engine error (measured, scripts/step6_eps_pin.py, commit efaffd4, RESULTS.md 2026-07-11). Engine cross-check on the pin: flux-route/composition-route median 0.979 / 0.996 (mesa_80/151) on rate-stable pre-stall intervals (same provenance). The ≤1% gate proper is measured by the Step-6 integrator (src/gnn_nucleo/fluxes/integrate.py, the reference producer of (Φ, ΔY = νΦ) pairs) — row stays open until then. 2026-07-12 MEASURED (Step-6 integrator), two readings stated separately: (a) the gate as written (e_nuc from the SAME net fluxes as composition, invariant #5): flux route ΣQⱼΦⱼ vs mass-excess bookkeeping residual median 6e-6…2.5e-5, max 8.7e-4, **frac ≤ 1% = 1.000 in every measured stratum, both nets** (incl. the whole 3–4 GK band) — PASS. Caveat: with constant mass-derived Q this comparison is near-algebraic (it bounds Q-table rounding, not route physics), and Qⱼ(T) corrections are not modeled; (b) the INDEPENDENT-leg cross-check (engine-rate energy vs label-ΔX energy on rate-stable shipped intervals): median ratio 0.979 / 0.996 (mesa_80/151) — mesa_80 sits at 2.1% median, OUTSIDE a 1% band, carried as an OPEN MARGIN item to Phase 1 (contributions from trapezoid quadrature and float32 label noise are not separated from rate-config differences) (measured, scripts/step6_integrate_check.py + scripts/step6_eps_pin.py, commits c7a3b2e/efaffd4, RESULTS.md 2026-07-11/12; docs/phase0-killtest-verdict.md threshold 8) |
| 12 | [ ] | Yₑ-residual accumulation slope: log\|cumulative\| vs log N (≈1 systematic, ≈0.5 random walk) | **The pass/fail gate — biggest single lever** (3e-6 vs 5e-7 vs 5e-5) | |
| 13 | [ ] | Sobol→real-MESA 99th-pct Yₑ error ratio | Retrain trajectory-aware if >3× | |
| 14 | [ ] | Per-isotope error distribution, Fe-peak A≈45–65 nuclei | Loss up-weighting (raise until 99th-pct effect on Yₑ ≤3e-6/step) | |
| 15 | [ ] | Timescale-governor holds gate at Δt ≥ 0.1 s; noise-on-non-eq vs noise-on-all; log-Δt-grid vs latent-NODE need | Components C/D | |

**Trajectory-data caveat (2026-07-10)** for every row measured on the shipped
constant-(T,ρ) test trajectories (rows 8, 9, 13; also row 6's remaining
relaxed-κ item, already noted there): the shipped trajectories STALL —
composition frozen (max \|ΔX\| < 1e-10 per interval) from median age
2.2e5 s / 3.9e4 s (mesa_80/151) at non-equilibrium states while eps_nuc keeps
rising; the frozen states are NOT NSE. Use PRE-STALL rows only; fully relaxed
trajectories need bbq reruns (measured, scripts/step5_qse.py, RESULTS.md
2026-07-10 trajectory-anomaly row).

2026-07-11 update: the pre-stall rule is now enforced in code — shipped-trajectory
consumers go through `gnn_nucleo.data.trajectories.select_rows`, which defaults to
`prestall=True`; post-stall rows require an explicit override. The stall caveat
itself REMAINS TRUE for the shipped data. Separately, the eps-convention
ambiguity noted here ("eps_nuc keeps rising") is RESOLVED by the row-11 pin
(integrated per row, net of ν losses, no 1e16 normalization; eps_neu a rate;
measured, scripts/step6_eps_pin.py, commit efaffd4, RESULTS.md 2026-07-11).

2026-07-12 update: the caveat above is SUPERSEDED for rows 6, 8 and 9 by the
Step-6 kill-test reruns — those rows are now measured on the relaxed manifold
(20 shipped + 209 local bbq rerun trajectories per net), not on shipped
pre-stall rows alone — and the stall itself is REINTERPRETED under the
terminal-tail guard: the "stall" is ARRIVAL at the Appendix-B bug-displaced
attractor, not trajectory death (first-quiet vs terminal-tail rules differ on
459/1508 shipped files; after arrival the strong sector is frozen at the
displaced attractor while weak-sector evolution continues), so tail rows are
LEGITIMATE relaxed label-dynamics states and belong IN the kill-test manifold
(measured, tests/test_trajectories.py stall-rule regression +
scripts/bbq_campaign/validate_campaign.py, commit ea970b4, RESULTS.md
2026-07-11; scripts/run_killtest.py --relaxed --include-reruns, commit
c7a3b2e, RESULTS.md 2026-07-12). Row 13 remains OPEN and should use the
terminal-tail row selection when measured. The original caveat text is
retained above as history (Rule 3); the shipped-data stall phenomenon itself
remains real — only its interpretation and the pre-stall-only restriction
are superseded.

**Timescale-separation working figure RETIRED by measurement (2026-07-12).**
The "6–8 orders of magnitude" fast/slow separation (the standing
never-sourced assumed figure in docs/CLAUDE.md Rule 1) is NOT SUPPORTED on
the label manifold: per-stratum medians of log₁₀[(fastest κ-balanced gross
rate)/(slowest 95%-inter-group-bottleneck net rate)] span −12.2…+1.4 dex
(p10 −25, p90 +3.5) — no cleanly-separated fast equilibrated sector exists
(κ-balanced pairs ≤ 0.4% and mostly low-flux) (measured,
scripts/run_killtest.py --relaxed --include-reruns, commit c7a3b2e,
RESULTS.md 2026-07-12; docs/phase0-killtest-verdict.md threshold 7).
Feeds row 15's governor-design premises: do not assume a separated fast
sector.

## Local code-level confirmations (retire before sizing or training)

- [ ] Exact mesa_80/mesa_151 isotope lists (Grichener 2025 App. A) and which Yₑ-controllers
      each contains (esp. neutron-rich β-decay partners ⁶¹Fe, ⁶¹,⁶³Co)
- [x] Which weak-rate tables bbq/MESA r23.05.1 loads (LMP > Oda > FFN precedence) and
      off-grid-edge extrapolation behavior — MEASURED and CLOSED (2026-07-10, Step 4
      Task 2): per-pair table sources parsed from the weakreactions.tables headers,
      0 mismatches vs the graphs post-ADR-0003 — LMP > Oda > FFN with
      use_suzuki_weak_rates=.false. confirmed as the label configuration. Off-grid:
      the regime box is interior to all weak tables (T9 ≤ 7.9 < 30,
      logρYₑ ≤ 8.7 < 11); outside the table MESA CLIPS to the edge
      (rates/private/eval_weak.f90) while pynucastro EXTRAPOLATES (measured at
      T9 = 40, 100) (measured, scripts/crosscheck_rates.py, commit 156c73f,
      RESULTS.md 2026-07-10; docs/rate-crosscheck.md)
- [ ] MESA average-neutrino-energy handling (⟨Eν⟩) for the neutrino head
- [x] Softwired inverse-rate equilibrium cleanliness: does κ_r → 0 without a spurious
      floor? (Appendix-B-class artifact screen — MUST precede any kill-test conclusion)
      — MEASURED and CLOSED (2026-07-10, Step 4 Tasks 3–4). Appendix-B state: stock
      r23.05.1 HAS the gh-575 bug (10.0–22.7 dex on 9/11 multi-body inverse channels;
      measured, scripts/appendixb_check.py, commit b8665c0); the training labels used
      the authors' FIXED MESA [SUPERSEDED 2026-07-11 at the fixed-point level for
      T9 ≳ 5: stock r23.05.1 bbq reproduces the shipped labels to 0.01/0.03 dex
      INCLUDING the bug-displaced pseudo-equilibrium (si30- / c12,o16-attractors,
      7–13 dex from NSE, frozen across dt decades), while MESA 24.08.1 relaxes to
      NSE — the labels were generated with the chapter-8 1→3 reverses (c12→3α
      class) still bugged; measured, scripts/step6_label_nse_census.py, commit
      3479512, RESULTS.md 2026-07-11]; MESA 24.08.1 installed side-by-side and the fix
      verified (residual ≤ 1.9 dex; measured, scripts/appendixb_check.py +
      mesa_probe24, commit 156c73f). κ screen at NSE: graphs-as-built raw v-flag
      reverses give a pervasive SPURIOUS floor (median κ 6.6e-2 / 1.3e-1, suspects
      268/280 and 656/672 pairs > 1e-3, mesa_80/151), attributed dispositively to
      pf-free v-flag fits — DerivedRate(use_pf=True) reverses collapse to
      1e-13…1e-11; stock-MESA's own residual floor median 3.6e-3 / 3.3e-3 (measured,
      scripts/kappa_floor_screen.py, commit f66328a). Consequence: NEW BLOCKING
      Step-5/6 gate recorded in root CLAUDE.md + RESULTS.md 2026-07-10 — reverse
      rates must be DerivedRate(use_pf=True) or MESA-side; raw v-flag reverses
      FORBIDDEN at T9 ≥ 3 (see checklist row 6 note)
- [ ] Precise meaning of Farmer 2016 "30%/10%" (η = 1−2Yₑ vs relative Yₑ)
- [x] pynucastro TabularRate precedence and interpolation defaults in the installed version
      — precedence MEASURED (2.12.0 default ordering ffn < oda < pruet_fuller < langanke
      < suzuki, later wins; exposed as a parameter in gnn_nucleo.graph.network;
      RESULTS.md 2026-07-08). Comparison against MESA weaklib MEASURED and CLOSED
      (2026-07-09, Step 4 Task 1): DEFAULT_TABULAR_ORDERING now suzuki < pruet_fuller
      < ffn < oda < langanke (later wins), reproducing MESA weaklib's LMP > Oda > FFN
      with use_suzuki_weak_rates=.false. — the training-label configuration; zero
      weak-table source mismatches remain (measured, scripts/reconcile_reactions.py,
      commit b559dde, RESULTS.md 2026-07-09; ADR 0003). Interpolation-default behavior
      is a rate-VALUE question carried with the Task-2 numeric rate cross-check
      (RESULTS.md 2026-07-09 "carried to Task 2" row). 2026-07-10 UPDATE — carried
      interpolation-default sub-question MEASURED and CLOSED (Step 4 Task 2): at the
      T9 = 5 weak-table node median |Δlog10| = 0.003 (0.7%); off-node spreads of
      0.03–0.18 dex are MESA-bilinear vs pynucastro-interpolant differences on the
      same tables (β⁻ tail ≤ 0.8 dex); the training labels contain MESA's bilinear
      values (measured, scripts/crosscheck_rates.py, commit 156c73f, RESULTS.md
      2026-07-10; docs/rate-crosscheck.md)

## Kill-test grid (from the prediction-target report §6.4)

T₉ ∈ {1.6, 2.5, 3.3, 4.0, 5.0, 6.3, 7.9} × ρ ∈ {1e7, 1e8, 1e9} g/cm³ ×
Yₑ ∈ {0.45, 0.48, 0.498} × dt ∈ {1e-6, 1e-3, 1, 1e2} s — prioritize 3.3–5 GK.

Note (2026-07-10): the dt = 1e-6 s point's linear-step premise is measured
VOID on the training grid — 99.99% / 100.00% (mesa_80/151) of
(state, isotope) cells have τ < dt (Sobol initial compositions carry free
nucleons, median X_neut 1.7e-2), so the shortest label step is a STIFF
RELAXATION, not a linear step; dt = 1e-6 labels encode full relaxations
everywhere in the box (measured, scripts/step5_handshake.py --grid,
RESULTS.md 2026-07-10 grid-mode-premise row).

Conventions codified 2026-07-11 (root CLAUDE.md, Physics conventions):
- **Two κ conventions — never mixed in one analysis.** Equilibrium detection and
  every κ threshold below (incl. the 0.1 active-set gate) are evaluated on
  UNSCREENED κ_r; the label config (chugunov_2007, per-reaction screening)
  carries a REAL ~7e-2 κ offset at NSE (κ ≈ |Δln scor|) — screened κ is used
  only for screening-offset diagnostics (measured, RESULTS.md 2026-07-10;
  docs/rate-crosscheck.md screened-κ caveat).
- **Si-group boundary is a config variant** (configs/qse_groups.yaml): default
  24 ≤ A < 45 vs a24_46 (boundary at A = 46, ⁴⁵Sc inside the group). Every
  group/bridge/inter-group analysis reports BOTH variants; a verdict that flips
  between them is promoted to a measured decision (ADR 0004 revisit clause).
- **Target A's φ is a TIME-INTEGRATED effective flux per step**, Φⱼ = ∫φⱼ dt over
  the label interval, not an instantaneous rate — every label encodes a
  relaxation (dt = 1e-6 s is already stiff over the box: grid-premise note
  above); src/gnn_nucleo/fluxes/integrate.py (Step-6 integrator) is the
  reference producer of (Φ, ΔY = νΦ) pairs. Instantaneous fluxes remain the
  right objects for κ_r itself.

2026-07-12: the kill-test VERDICT IS RENDERED — see docs/phase0-killtest-verdict.md
(TARGET A, full-width, mask measured empty; rows 6–9 above). The provisional
criteria below are retained as history.

Provisional pass/fail (to calibrate against measured κ_r and the floor):
- Target A viable: {r : κ_r > 0.1} carries ≥95% of |ΔYₑ| and dominant-isotope |ΔX|
  at the median timestep. Fail → Target B or bottleneck-only A.
- Target B viable: linear/asinh-latent dY + projection reaches the Yₑ floor without
  the conservation layer destabilizing training (NuGNN-replication check).
