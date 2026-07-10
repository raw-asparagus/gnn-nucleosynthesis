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
| 6 | [~] | Per-reaction κ_r = \|net\|/(gross_f+gross_r) distribution | Target A vs B; mask design; **the load-bearing unknown** | Step-5 delivered the instrument + first distributions (measured, scripts/step5_run_fluxes.py + step5_bridges.py, commit d1a9c4a, RESULTS.md 2026-07-10): pf gate implemented (DerivedRate(use_pf=True) compiled in, PfGateError otherwise); κ at NSE unscreened median 2.6e-12 (floor eliminated); label-screening config adds a REAL ~7e-2 κ offset at NSE (per-reaction screening asymmetry) — equilibrium detection must use UNSCREENED κ; on the TRAINING DISTRIBUTION κ ≈ 1 everywhere ({κ>0.1} covers 97–100% of carrying pairs — random compositions are nowhere near flux balance); full-corpus per-reaction fluxes precomputed (data/fluxes/, hashes in RESULTS.md). Remaining for Step 6: κ on RELAXED states (pre-stall trajectory rows only — shipped trajectories stall, RESULTS.md anomaly row) + the Target-A active-set verdict |
| 7 | [~] | cond(ν) full and active-set | Target A→B switch at cond(S_active) > 1e6 | FULL: cond(ν) = 41.7 (mesa_80) / 57.6 (mesa_151), nullity 1; cond(CCᵀ) = 3.9e4 / 1.0e5 (scripts/graph_metrics.py, 2026-07-08, RESULTS.md). Active-set cond(S_active) is the Step-6 kill-test quantity — row stays open until then |
| 8 | [ ] | Guidry ε sweep {3e-3, 1e-2, 3e-2} on Si-burning trajectories | Mask threshold; ε≈0.01 transfer hypothesis | |
| 9 | [ ] | Mask membership churn per step along real T(t), ρ(t) tracks | Hybrid vs frozen-Guidry fallback (freeze if >5%/step) | |
| 10 | [x] | Target B projection drift at realistic (20-decade) dynamic range | Target B viability | max relative constraint residual 6.7e-17 / 1.0e-16 (mesa_80/151) across dY scales 1e0…1e-20, gate ≤ 1e-12; weak dYₑ preserved to ≤ 3.4e-21 (scripts/check_projector.py, 2026-07-08, RESULTS.md). Static-operator viability confirmed; training-stability half of the question stays with the kill-test |
| 11 | [ ] | e_nuc flux-route − composition-route residual, 3–4 GK band (≤1%?) | Energy-head partition-function consistency | |
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
      the authors' FIXED MESA; MESA 24.08.1 installed side-by-side and the fix
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

Provisional pass/fail (to calibrate against measured κ_r and the floor):
- Target A viable: {r : κ_r > 0.1} carries ≥95% of |ΔYₑ| and dominant-isotope |ΔX|
  at the median timestep. Fail → Target B or bottleneck-only A.
- Target B viable: linear/asinh-latent dY + projection reaches the Yₑ floor without
  the conservation layer destabilizing training (NuGNN-replication check).
