# Phase-0 kill-test verdict (Step 6, 2026-07-12)

**VERDICT: TARGET A — with the hybrid's equilibrium mask measured EMPTY on
the relaxed label manifold (full-width flux head; no Guidry masking
deployed; weak sector structural as always).** Conditional statement for
T9 ∈ [4.0, 6.3) below. No ADR-0001 Target-B switch condition fires; PIVOT
criteria are not met.

Numbers are **measured** and cite RESULTS.md rows of 2026-07-11/12 unless
tagged otherwise (instruments per row: `scripts/run_killtest.py`,
`scripts/bbq_campaign/validate_campaign.py`,
`scripts/step6_label_nse_census.py`, `scripts/step6_integrate_check.py`,
`scripts/step6_eps_pin.py`). The verdict is rendered on the RELAXED
manifold (20 shipped + 209 local bbq rerun trajectories per network,
4,693 sampled rows/net, unscreened κ convention, δ_r vs the independent
Saha NSE, phase-split at the first-quiet arrival row). The training-grid
distribution is shown beside it for contrast only.

## The two distributions

| quantity | training grid (2A) | relaxed manifold (2B) |
| --- | --- | --- |
| κ_r picture | vacuous: med log₁₀κ ≈ −0.05 everywhere; frac κ>0.1 = 0.985–0.999 / 0.974–0.997 (mesa_80/151, unscreened 30k subsample; corpus-scale confirmation on the screened full run per the two-κ rule, 1.03M in-strata states/net) | structured: frac κ>0.1 falls to 0.70/0.64 at T9 [5.0,6.3); κ-balanced (κ<1e-3) pairs ≤ 0.4% everywhere — a cancellation CONTINUUM, not a clean equilibrated sector |
| Guidry maskable set (ε ∈ {3e-3, 1e-2, 3e-2}) | n/a (nothing equilibrated) | median AND p90 = 0 columns per row at every ε, both nets — δ_r vs true NSE effectively never crosses threshold (the manifold's own equilibria are Appendix-B-displaced; RESULTS 2026-07-11) |
| cond(S_active), rank-revealing | 41.8 / 57.4 (ν net-column submatrix; κ-active union = all net columns; full ν 41.6 / 57.9) | 41.8 / 57.4 at every ε (mask empty ⇒ S_active = all net columns) |
| κ↔δ Spearman | n/a | +0.491 / +0.498 (657k / 1.59M carrying-pair samples); +0.650/+0.666 on the pre-arrival shipped subset |

## Thresholds (CLAUDE.md gates, restated for the two-distribution reality)

1. **≥95% of |ΔYₑ| carried by {κ_r > 0.1}** — PASS at 1.0000. Weak
   columns are unpaired in the engine (f⁻ ≡ 0), so κ = 1 wherever a weak
   column carries flux; verified κ = 1.0 exactly on 8,825,170 /
   33,189,419 (weak column × relaxed row) samples with f⁺ > 0 (measured,
   RESULTS 2026-07-12 weak-κ row; fluxless weak columns have κ = 0 by the
   zero-denominator convention and contribute nothing). Weak columns are
   also never maskable (invariant #2, structural). Per-channel
   concentration: top-5 weak channels carry 0.96/0.75, top-20 ≈ 1.00 of
   Σ|dẎₑ| on high-Yₑ QSE-window rows; #1 = ⁵⁶Ni EC.
2. **≥95% of dominant-isotope |ΔX| carried by {κ_r > 0.1} at the median
   relaxed state** — SPLIT:
   - median dominant isotope: ≥95% in most strata/phases (1.00 typical),
     EXCEPT T9 [5.0,6.3) (med-cov 0.62–0.80);
   - worst dominant isotope per row (min-cov median): 0.90/0.75 at
     [1.6,2.5) (relaxing) falling to 0.0022–0.1658 (mesa_80) /
     0.0084–0.0700 (mesa_151) across the [4.0,6.3) strata × phases —
     a few dominant species' net evolution rides on near-cancelled
     (κ ∈ 1e-3…1e-1) columns, with 1/κ error amplification if φ were
     inferred from gross-scale features. Mitigation in the Step-7 handoff
     (Φ-level supervision where feasible + loss weighting); not a target
     switch — Target B faces the same cancelled sums inside its dY labels.
3. **FAIL if net flow spreads over >~30% of reactions near the κ floor**
   — PASS: the per-row low-κ column share of active net columns has
   median 0.9%–24% in every stratum × phase (worst median: attractor
   T9 [5.0,6.3), 0.24/0.21); no diffuse-spread failure at the median.
4. **cond(S_active) < 1e6 pass / > 1e8 fail** — PASS: 41.8/57.4 (mask
   empty at every ε ⇒ S_active = all net columns; rank-revealing
   definition, conservation null vectors structural; full ν 41.6/57.9).
5. **Guidry ε sweep** — measured; the result is EMPTINESS at every ε
   (median and p90 both 0). The Component-B hybrid-vs-frozen-mask
   decision is settled by emptiness, not churn.
6. **Mask churn** — 0.00–0.03 flips/step (n = 35 QSE-window trajectories,
   per output step, every ε): far below the 5%/step freeze trigger, and
   moot per (5).
7. **Timescale separation** ("6–8 orders", previously an assumed figure)
   — RETIRED with a measured replacement: per-stratum medians of
   log₁₀[(fastest κ-balanced gross rate)/(slowest
   95%-inter-group-bottleneck net rate)] span −12.2…+1.4 (p10 −25,
   p90 +3.5) — no cleanly-separated fast equilibrated sector exists on
   the label manifold.
8. **Energy consistency (invariant #5)** — two readings, stated
   separately:
   - the gate as written ("e_nuc = ΣQⱼφⱼ from the SAME net fluxes as
     composition"): PASSES — residual median 6e-6…2.5e-5, max 8.7e-4,
     frac ≤1% = 1.000 in every measured stratum, both nets. Caveat: with
     constant mass-derived Q this comparison is near-algebraic (it bounds
     Q-table rounding, not route physics), and Qⱼ(T) corrections are not
     modeled;
   - the independent-leg cross-check (engine-rate energy vs label-ΔX
     energy on rate-stable shipped intervals; scripts/step6_eps_pin.py):
     median ratio 0.979 / 0.996 — mesa_80 sits at 2.1% median, OUTSIDE a
     1% band. Carried as an OPEN MARGIN item to Phase 1 (contributions
     from trapezoid quadrature and float32 label noise are not separated
     from rate-config differences here).

## Qualitative evidence

- **Bridge concentration** (finalized, both boundary variants; verdict
  insensitive to the variant at the ≤0.02 level): mesa_80
  Ne22(α,n)Mg25 / Al27(p,α)Mg24 / P31(p,α)Si28 (+ Na23(α,p)Mg26,
  Mg24(n,γ)Mg25), top-20 carry 0.88; mesa_151 Mg24(p,α)Na21 /
  Mg24(p,γ)Al25 / Cl35(p,α)S32 / P31(p,α)Si28 / Ca44(p,γ)Sc45, and
  **⁴⁵Sc(p,γ)⁴⁶Ti rank 2/251 (share 0.10–0.12)** under a24_46 — the
  literature bottleneck (sourced: Grichener et al. 2025, ApJS 279, 49)
  CONFIRMED on the full relaxed manifold.
- **r_QSE single-cluster plateau**: NOT confirmed even on clean rerun
  data (0/303 and 0/316 late-relaxation rows below 0.1 dex; intra-group
  std ≈ 0.8 dex) — the single-Si-cluster QSE reference (sourced: Hix &
  Thielemann 1996/1999, per ADR 0001) does not describe the
  (bug-displaced) relaxed label manifold. Group-ORGANIZED structure
  exists (non-group spread 1.3–2.2 dex ≫ intra-group), which is what the
  GNN's group-aware features rely on; single-cluster ALGEBRAIC reduction
  does not hold.
- **Label pathology context** (RESULTS 2026-07-11): at T9 ≳ 5 the label
  manifold sits at Appendix-B bug-displaced pseudo-equilibria (per-bin
  medians of max-species |Δlog₁₀X| vs NSE: 6.7–13.0 dex; stock bbq
  reproduces the labels to 0.01–0.03 dex, MESA 24.08.1 relaxes to NSE).
  The [5.0,6.3) part of the gate-2 failure band co-locates with this
  stratum. The rerun campaign is exactly label-comparable (early-time
  agreement 0.996/0.998), so the kill-test on the LABEL manifold is
  well-posed regardless; what physics Phase 1 should target there is the
  escalated human decision (STEP6_REPORT §6).

## Why not the alternatives

- **TARGET A bottleneck-only (frozen Guidry mask)**: there is no nonempty
  mask to freeze.
- **TARGET B (projection)**: ADR-0001's switch conditions are
  (i) cond(S_active) > 1e6 — measured 41.8/57.4; (ii) >~90% of reactions
  carrying net flux below the Yₑ floor — the measured low-κ share is
  0.9–24% (median), nowhere near; (iii) Target B matching A within 2×
  |dYₑ| while being materially simpler — untestable before Phase-1
  training and carried as a fallback trigger, not a reason to switch now.
  B would also surrender the per-reaction structure that the concentrated
  bridge/EC channels reward, without removing the cancellation from the
  labels themselves.
- **PIVOT**: no threshold fails catastrophically on the relaxed manifold;
  the one hard failure (worst-species coverage in [4.0,6.3)) has a
  concrete supervision-level mitigation in the feasible band and an
  identified unlock (ADR-0006 Yₑ-chain Jacobian) plus a pending human
  decision in the pathological band.

## Conditional statement (nuance rule)

Target A is UNCONDITIONAL for T9 < 4.0: every gate passes there,
including worst-species coverage (min-cov median ≥ 0.36 at [3.3,4.0),
≥ 0.61 below 3.3, with median-species coverage 1.00).
For **T9 ∈ [4.0, 5.0)** (upper QSE window, physical labels): the
worst-species κ-active coverage fails the 95% bar (min-cov median
0.1658/0.0700) while median-species coverage stays ≥ 0.95 — Target A
holds structurally (cond/spread/churn all pass), and the mitigation is
MEASURED-FEASIBLE here: local Φ-label generation is proven for T9 < 5
(agreement 0.74–0.99 in band, ~9.4/2.4 states·h⁻¹·core⁻¹ upper bounds).
For **T9 ∈ [5.0, 6.3)** (label-pathological stratum): median-species
coverage also fails (0.62–0.80), label physics is bug-displaced, and
local Φ labels are currently blocked by integrator cost (all censored
states are T9 ≥ 5; the ADR-0006 Yₑ-chain contingency is the unlock) —
Target A remains structurally viable (no conditioning/spread failure),
but supervision design there is DEFERRED to the escalated
benchmark-vs-physics decision. No stratum supports switching to B.

## Step-7 handoff

- **Flux head dims** (sourced: RESULTS 2026-07-09 reconciliation): 607 /
  1,518 columns (mesa_80/151), net view via `pair_col` (327 / 846 net
  columns); decode = fixed ν (conservation by construction); weak sector
  structural (never masked).
- **Mask parameters**: NONE deployed (measured-empty at ε ∈ {3e-3, 1e-2,
  3e-2}, both boundary variants). Carry κ diagnostics as FEATURES, not
  masks. Group boundary: default 24 ≤ A < 45 for group features; a24_46
  variant retained for ⁴⁵Sc analyses (verdict-insensitive).
- **Supervision plan**: shipped ΔX primary. Φ auxiliary labels from
  `fluxes/integrate.py` for the low-κ carriers, RESTRICTED to T9 < 5
  strata (QSE window first) where generation is proven: median ≥ 383 /
  1,519 s per nine-dt state (censored lower bounds) ⇒ corpus-scale local
  generation INFEASIBLE (≥ 1.1e5 / 4.4e5 core-h), stratified subsets of
  10³–10⁴ states feasible (≈ 4–40 core-days). Hot-strata (T9 ≥ 5) Φ
  labels require the ADR-0006 Yₑ-chain Jacobian first, and their rate
  config awaits the pathology decision (pf-true vs label-comparable rates
  differ there by construction).
- **Loss-weight targets**: top-|dẎₑ| channels (⁵⁶Ni EC, ³¹S EC, ⁵²Fe EC,
  p EC) and the finalized bridge sets above.
- **Target-B fallback triggers carried into Phase 1** (ADR 0001): cond(S_active)
  > 1e6 on any future masked configuration; >~90% of net-flux-carrying
  reactions below the Yₑ floor on Phase-1 validation data; Target B
  matching A within 2× |dYₑ| while materially simpler. (Separately, the
  kill-test ≥30%-spread line and the 2×-over-three-seeds mask-freeze
  trigger remain attached to their own decisions.)
- **Open margin item**: independent-leg energy cross-check at 2.1% median
  (mesa_80) vs the 1% band — see threshold 8.
- **Accumulation-slope measurement** (checklist row 12) remains the
  Phase-1 pass/fail gate for the |ΔYₑ| ≲ 3e-6 per-step budget.
