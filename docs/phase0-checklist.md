# Phase-0 measurement program (living checklist)

Source: Consolidated Architecture Specification §7 (docs/reports/). Each item is a
measurement only the bbq/MESA data can settle. Tick when measured; record value, date,
and the script that produced it (derived-label discipline). The `docs-sync` agent
updates this file; the `physics-auditor` agent produces the numbers.

Operative gate until item 12 is measured: per-step |ΔYₑ| ≲ 3e-6 (systematic accumulation).

| # | Done | Measurement | Sets / gates | Measured value (script, date) |
|---|------|-------------|--------------|-------------------------------|
| 1 | [x] | Reaction count + graph radius/diameter of mesa_80/151/204 (pynucastro export) | Depth K ≈ ⌈radius⌉+2; flux-head output dim | mesa_80: 610 reactions; mesa_151: 1522; bipartite radius 3 / diameter 6 (both nets) ⇒ K = 5 (K = 4 with I→I edges); PROVISIONAL rate set pending Step-4 MESA cross-check; mesa_204 not in scope of the shipped data (scripts/graph_metrics.py, 2026-07-08, RESULTS.md) |
| 2 | [ ] | Feature distributions of all proposed channels across the regime box | Normalization; dead-channel detection | |
| 3 | [ ] | Per-channel ablation of the 4 added physics channels (retain if ≥0.005 MAE) | Component A feature set | |
| 4 | [ ] | Weight-shared vs untied processor at equal step count (within 0.01 MAE?) | Recurrent vs untied default; latent-ODE option | |
| 5 | [ ] | Zero-shot mesa_80→151 transfer on neutron-rich isotopes (≤2× internal Yₑ error?) | Size-transfer claim (transferable vs adaptable) | |
| 6 | [ ] | Per-reaction κ_r = \|net\|/(gross_f+gross_r) distribution | Target A vs B; mask design; **the load-bearing unknown** | |
| 7 | [~] | cond(ν) full and active-set | Target A→B switch at cond(S_active) > 1e6 | FULL: cond(ν) = 41.7 (mesa_80) / 57.6 (mesa_151), nullity 1; cond(CCᵀ) = 3.9e4 / 1.0e5 (scripts/graph_metrics.py, 2026-07-08, RESULTS.md). Active-set cond(S_active) is the Step-6 kill-test quantity — row stays open until then |
| 8 | [ ] | Guidry ε sweep {3e-3, 1e-2, 3e-2} on Si-burning trajectories | Mask threshold; ε≈0.01 transfer hypothesis | |
| 9 | [ ] | Mask membership churn per step along real T(t), ρ(t) tracks | Hybrid vs frozen-Guidry fallback (freeze if >5%/step) | |
| 10 | [x] | Target B projection drift at realistic (20-decade) dynamic range | Target B viability | max relative constraint residual 6.7e-17 / 1.0e-16 (mesa_80/151) across dY scales 1e0…1e-20, gate ≤ 1e-12; weak dYₑ preserved to ≤ 3.4e-21 (scripts/check_projector.py, 2026-07-08, RESULTS.md). Static-operator viability confirmed; training-stability half of the question stays with the kill-test |
| 11 | [ ] | e_nuc flux-route − composition-route residual, 3–4 GK band (≤1%?) | Energy-head partition-function consistency | |
| 12 | [ ] | Yₑ-residual accumulation slope: log\|cumulative\| vs log N (≈1 systematic, ≈0.5 random walk) | **The pass/fail gate — biggest single lever** (3e-6 vs 5e-7 vs 5e-5) | |
| 13 | [ ] | Sobol→real-MESA 99th-pct Yₑ error ratio | Retrain trajectory-aware if >3× | |
| 14 | [ ] | Per-isotope error distribution, Fe-peak A≈45–65 nuclei | Loss up-weighting (raise until 99th-pct effect on Yₑ ≤3e-6/step) | |
| 15 | [ ] | Timescale-governor holds gate at Δt ≥ 0.1 s; noise-on-non-eq vs noise-on-all; log-Δt-grid vs latent-NODE need | Components C/D | |

## Local code-level confirmations (retire before sizing or training)

- [ ] Exact mesa_80/mesa_151 isotope lists (Grichener 2025 App. A) and which Yₑ-controllers
      each contains (esp. neutron-rich β-decay partners ⁶¹Fe, ⁶¹,⁶³Co)
- [ ] Which weak-rate tables bbq/MESA r23.05.1 loads (LMP > Oda > FFN precedence) and
      off-grid-edge extrapolation behavior
- [ ] MESA average-neutrino-energy handling (⟨Eν⟩) for the neutrino head
- [ ] Softwired inverse-rate equilibrium cleanliness: does κ_r → 0 without a spurious
      floor? (Appendix-B-class artifact screen — MUST precede any kill-test conclusion)
- [ ] Precise meaning of Farmer 2016 "30%/10%" (η = 1−2Yₑ vs relative Yₑ)
- [~] pynucastro TabularRate precedence and interpolation defaults in the installed version
      — precedence MEASURED (2.12.0 default ordering ffn < oda < pruet_fuller < langanke
      < suzuki, later wins; exposed as a parameter in gnn_nucleo.graph.network;
      RESULTS.md 2026-07-08). Interpolation defaults + comparison against MESA weaklib's
      LMP > Oda > FFN remain open for Step 4

## Kill-test grid (from the prediction-target report §6.4)

T₉ ∈ {1.6, 2.5, 3.3, 4.0, 5.0, 6.3, 7.9} × ρ ∈ {1e7, 1e8, 1e9} g/cm³ ×
Yₑ ∈ {0.45, 0.48, 0.498} × dt ∈ {1e-6, 1e-3, 1, 1e2} s — prioritize 3.3–5 GK.

Provisional pass/fail (to calibrate against measured κ_r and the floor):
- Target A viable: {r : κ_r > 0.1} carries ≥95% of |ΔYₑ| and dominant-isotope |ΔX|
  at the median timestep. Fail → Target B or bottleneck-only A.
- Target B viable: linear/asinh-latent dY + projection reaches the Yₑ floor without
  the conservation layer destabilizing training (NuGNN-replication check).
