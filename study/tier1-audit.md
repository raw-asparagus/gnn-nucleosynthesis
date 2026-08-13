# tier1.md literature audit — claim-by-claim log

**Date:** 2026-08-13.
**Method:** nine parallel verification agents, one per thematic chunk of
`study/tier1.md`, each instructed to (1) inventory every checkable claim,
(2) classify it scholarly / arithmetic / project-internal / interpretation,
(3) verify scholarly claims only against sources actually fetched (arXiv TeX
cached into `data/literature/`, the REACLIB format specification, the open
OSTI preprint of Cyburt et al. 2010, the ADS scan of Salpeter 1954, GitHub
issues via API, the local MESA r23.05.1 tree, and pynucastro 2.12.0),
recording the supporting passage, and (4) recompute all worked arithmetic in
float64 via `uv run python`. Findings were reconciled in the main thread;
corrections were applied in place per the user's instruction, each logged
below. Project-internal numbers (RESULTS.md measurements, config contents,
code file:line quotes) were **not** literature-verified — `RESULTS.md` is
their source of truth — but every [RESULTS] tag and code quote in the
document was cross-checked against the repo, and several were re-derived
from the shipped exports as a consistency check.

Verdict key: **VERIFIED** = supporting passage/value found in a fetched
source, or arithmetic reproduced exactly; **CORRECTED** = document changed in
place; **ASSUMED** = order-of-magnitude estimate or textbook-standard form
with no opened primary source, tagged where relevant; **PROJECT-INTERNAL** =
repo-measured, excluded from literature verification.

Headline: ~330 claims inventoried across nine chunks; 28 incorrect statements
corrected, 15 imprecisions tightened, 13 items left as ASSUMED, zero
unresolved [RESULTS]-tag mismatches (two stale status citations and two
RESULTS-quote fidelity slips were themselves among the corrections). The
inline citations added by this audit point to the References section at the
end of `tier1.md`.

## 1. Corrections applied (before → after)

### Incorrect values or statements

| # | Location | Before | After | Source / evidence |
|---|---|---|---|---|
| 1 | §1.1.3 (was L277) | "the `ec` label; ⁷Be(e⁻,ν)⁷Li is the one in mesa_80" | "in mesa_80 there are **two**: ⁷Be(e⁻,ν)⁷Li and the pep reaction p(p e⁻,ν)d" | MEASURED: compiled mesa_80 has 2 Yₑ-weighted columns (Be7_to_Li7_reaclib, p_p_to_d_reaclib_electron_capture); pynucastro 2.12.0 maps ec/bec → electron_capture (phaseB-1 §A). |
| 2 | §1.3.3 table (was L606) | "Shell-model weak (LMP) … factor ~2–10" | "no blanket figure; GT-strength dependent — the LMP revision moved key FFN EC rates by factors ~10–350 (Langanke & Martínez-Pinedo 2000)" | Mirrors tier0-audit #3; nucl-th/0001018 verbatim "smaller than the FFN rates by factors 39, 12, 10, 346, and 19"; no 2–10 statement exists in LMP (phaseB-2 A2). Col-4 "Gamow–Teller strength (§V.3)" retained (Why-column semantics), minor deviation from proposed After noted. |
| 3 | §1.3.4 (was L641–642) | "Wigner limit, Γ_ℓ ≤ 3ℏ²/(μR²) roughly" | reduced width γ² ≤ γ_W² = 3ℏ²/(2μR²), observable Γ_ℓ = 2P_ℓγ² ≤ 3ℏ²P_ℓ/(μR²) | Descouvemont & Baye 2010 (1001.0678, Chap5:122–126) γ_W² = 3ℏ²/(2μa²) after Teichmann & Wigner 1952; Longland et al. 2010 Γ = 2Pγ² (phaseB-2 A3). |
| 4 | §1.4.2 (was L745–747) | "balance point moves by ≈ +0.8 in T₉ per decade of Y_α" | "≈ +0.5/decade on average (steepening from ≈ +0.4/decade at Y_α = 10⁻⁷–10⁻⁴ to ≈ +0.8/decade at 10⁻³–10⁻²)" | Recomputed float64 (brentq on the printed a-sets): steps 0.396/0.601/0.776 per decade; four balance points 3.31/4.50/5.10/5.87 all VERIFIED and kept (phaseB-2 A4). |
| 5 | §1.3.5 (was L697–698) | "α ladder and the Fe-peak captures are `ths8r` throughout" | "…throughout except ⁴⁰Ca(α,γ)⁴⁴Ti (label `chw0`, a resonance-based re-evaluation)" | MEASURED, pynucastro 2.12.0 labelprops census: ca40(a,g)ti44 = 'chw0 ', all other (α,γ) ladder links 'ths8r ' (phaseB-2 A5). |
| 6 | §1.4.4 (was L792–793) | "Thomson mean free path is ~10⁻² cm … optically thick by twenty orders of magnitude" | "~5×10⁻⁷ cm (λ = 1/(n_eσ_T), n_e = ρN_AYₑ ≈ 3×10³⁰ cm⁻³) … ~13–14 orders of magnitude" | Recomputed: σ_T = 6.6525e-25 cm², n_e(1e7 g/cm³) ≈ 3e30 cm⁻³ ⇒ λ ≈ 5e-7 cm, τ ≈ 2e13–2e14; old mfp off ~4.3 dex. LTE conclusion unchanged/strengthened (phaseB-2 A1). |
| 7 | §II.2 (was L913–915) | labelprops "positions 0–5 hold the data source label (`ths8r `, …, `ec    `, `bet+  `)" | 4-char label (pos 0–3) + resonance/weak flag (pos 4: blank/n, r, w) + reverse flag v (pos 5); weak examples `wc12w `, `  ecw `, `bet+w ` | reaclibFormat.pdf field spec (a4,a1,a1) verbatim; measured mesa_80 set_labelprops contain `wc12w `, `  ecw `, `bet+w ` — the doc's 6-char "labels" do not occur (phaseB-3 §A). |
| 8 | §II.6b (was L1086–1089) | "43 of 1834 sets underflow to exactly 0 at T₉ = 1.6" | "43 of the 1834 set-evaluations across the two box-edge temperatures underflow to exactly 0 (mesa_80 has 917 sets; 7 at T₉ = 1.6 and 36 at T₉ = 7.9)" | MEASURED: zeros per T₉ {1.6,3.3,5.0,7.9} = {7,18,26,36}; 917×2 = 1834, 7+36 = 43; count rises toward the HOT edge — old attribution wrong in direction (phaseB-3 §A). |
| 9 | §II.6 (was L1053–1054) | "for the largest Q-values in the network it reaches several hundred" | "approaches two hundred (max \|Q\| = 23.85 MeV → \|Q\|/kT ≈ 173 at T₉ = 1.6); other exponent terms do reach O(500) (c12(a,g)o16 a₃T₉^{1/3} ≈ −492)" | MEASURED: max \|Q\| = 23.847 MeV both nets; max \|a₁\|·T₉⁻¹ = 172.95 at 1.6; O(500) survives as exponent-term bound (phaseB-3 §A). |
| 10 | §II.8 (was L1147) | "mesa_151 (1518 columns, ~2000 sets, 4096 states)" | "~1700 sets" | MEASURED: compiled mesa_151 n_sets = 1720, n_reactions = 1518 (phaseB-3 §A). |
| 11 | §III.1 (was L1260–1261) | "the two forms being identical because 1/N_A = m_u to ten digits" | "agreeing to nine digits because 1/N_A = m_u to one part in 10⁹ (CODATA 2022: m_u = 1.66053906892×10⁻²⁴ g vs 1/N_A = 1.66053906717×10⁻²⁴ g, relative difference 1.05×10⁻⁹ = M_u − 1 g/mol; the equality was exact only pre-2019 SI)" | float64 recompute, CODATA 2022; agreement is through the 9th significant digit (phaseB-4 A1). |
| 12 | §III.1 sanity box (was L1268–1271) | "agreement to 6×10⁻⁴ relative at T₉ = 3, the residual being pynucastro using its own recomputed Q (ΔQ ≈ 1.6×10⁻⁴ MeV rounding)" | "Using the literal six factors of (3.4): 1.3×10⁻³ relative, splitting into 6.4×10⁻⁴ (recomputed Q, ΔQ = 1.6×10⁻⁴ MeV) + 7.0×10⁻⁴ (DerivedRate's exact-mass molar prefactor convention, ratio 1.00070 for this channel)" | pynucastro 2.12.0 float64 recompute: ratio_factor 24.893503 vs (3.4) prefactor 24.892803; the old 6×10⁻⁴ tested the code against itself (phaseB-4 A2). [derived here] tag kept. |
| 13 | §III.7 blockquote (was L1592–1593) | "> \|Δlog₁₀\| = 10.0–11.1 for one missing power and 20.6–22.7 for two, tracking \|ΔN_s − e\|·log₁₀(fac·T₉^{3/2}) within ≲0.35 dex [RESULTS 2026-07-09]" — silently rewrote the row's \|ΔN\| to \|ΔN_s − e\| inside a quotation | Blockquote now quotes RESULTS.md row 216 VERBATIM (its own \|ΔN\| wording, ASCII log10/T9 style, "(\|ΔN\| = 1, sign follows ΔN)… (\|ΔN\| = 2: h1+h1+he4+he4→he3+be7)"); the \|ΔN_s − e\| refinement follows AFTER the quote as a separate paragraph: dev ≤ 0.31 dex except three-identical-particle channels (b11, c12→3α) at ≈ 0.78 dex ≈ log₁₀3! low; row's range/bound match the mesa_80 ch-6/7/9 screen exactly (9.99–11.13, max dev 0.308) but not mesa_151 or chapter 8 (low 9.5–11.3 dex [RESULTS 2026-07-09]). New paragraph tagged **[derived here]**. | phaseB-5 A1 as amended by adjudication item 13 (RESULTS quotes must match verbatim; refinement after, clearly separated). Recomputed from data/mesa_cache/appendixb_comparison.csv. |
| 14 | §III.8 (was L1665) | "light sector only (d, ³He, ⁴He, ⁷Li, ⁷⁹Be, ⁸B, ¹²⁻¹³C, ¹³⁻¹⁵N)" | "(d, ³He, ⁴He, ⁷Li, ⁷,⁹,¹⁰Be, ⁸B, ¹²,¹³C, ¹³⁻¹⁵N)" | RESULTS.md row 272 (same tag): "Be7/9/10"; doc dropped ¹⁰Be and "⁷⁹Be" was a broken rendering (phaseB-5 A3). |
| 15 | §IV.5 (was L2189–2191) | "As γ̃ → ∞ the B-terms dominate and h grows linearly in γ̃" | "the A₁ and B₁ terms both go linear and partially cancel, leaving h → (A₁+B₁)γ̃ + B₃" | Recomputed: A₁γ̃ = 2.78γ̃, B₁ term −1.75γ̃ (negative slope alone), B₃ → 1.12; h/γ̃ → A₁+B₁ = 1.0346 (phaseB-6 A3). Doc's own §IV.3 already used A₁+B₁. |
| 16 | §IV.9 MU bullet (was L2311) | "including rest mass" | "rest-mass convention varies by table family (langanke: without; suzuki: with)" | Empirical, pynucastro 2.12.0 tables at logρYₑ = 9, logT = 9: langanke mu = 4.665 MeV (kinetic), suzuki 5.145 MeV (incl. rest mass) (phaseB-6 A2). |
| 17 | §IV.9 DQ bullet (was L2314–2315) | "effective Q-value shift from thermal population of parent excited states" | "Coulomb correction to the threshold: ΔQ_C = μ_C(Z−1) − μ_C(Z) (Suzuki, Toki & Nomoto 2016); thermal excited-state population is folded into RATE itself" | Suzuki+2016 TeX lines 537–551; the FFN-family files carry dQ ≡ 0 (phaseB-6 A1). |
| 18 | §IV.9 (was L2344–2346) | "the flux-route vs bbq eps_nuc comparison is already recorded as UNRESOLVED [RESULTS 2026-07-10]" | "(Status: the 2026-07-10 UNRESOLVED row … was retired by the 2026-07-11 eps_nuc convention pin — a units/convention mismatch, not an engine error [RESULTS 2026-07-11]; invariant-#5 proper passed 2026-07-12 with the constant-Q caveat of §III.12 [RESULTS 2026-07-12]; the NU-column gap itself stands.)" | phaseB-6 A4 with adjudication item-6 wording; RESULTS.md:352 (pin retires the row), :362 (convention mismatch), :458 (2026-07-12 ENERGY IDENTITY pass, frac ≤ 1% = 1.000). |
| 19 | §V.5b point 3 (was L2722–2723) | "steep β⁻ channels sit at log λ ≈ −27 in the box" | "log λ ≈ −15…−9 **on the in-box table nodes**: ⁴³Ca→⁴³Sc reaches −15.3, ⁴⁸Ca→⁴⁸Sc −12.3, ⁴⁴Sc→⁴⁴Ti −12.8, ⁴⁰K→⁴⁰Ca −9.3; interpolated at the cold-dense box corner the steepest reaches ≈ −24 (node qualifier added in the Phase-D pass)" | Recomputed from the shipped weak tables box-restricted (⁴⁸Ca from the langanke family; ⁴³Ca/⁴⁴Sc/⁴⁰K from FFN — Phase D corrected the initial all-langanke attribution). Node minima −15.31/−12.29/−12.82/−9.29; the old −27 is not reached on any in-box node but IS approached (−24.4) by bilinear interpolation at the logρYₑ = 8.70, logT = 9.204 corner (phaseB-7 A1; phaseD-1 row 19). |
| 20 | §V.5b point 3 (was L2723–2724) | "a rate 25 decades below the dominant one" | "a rate 10–14 decades below the dominant one on the nodes (up to ~25 at the interpolated cold-dense corner)" | Dominant EC controller ⁵⁶Ni→⁵⁶Co spans log₁₀λ = −2.96…−0.72 in-box; max node gap 14.1 decades, interpolated corner gap 25.1 — the old "25 decades" was node-wrong but state-defensible, so the Phase-D pass restored it as a parenthetical. Benign/anti-correlated conclusion unchanged under both readings (phaseB-7 A2; phaseD-1 row 20). |
| 21 | §V.4b index table intro (was L2589–2590) | "Measuring the local power-law index … inside the box" | "…on the table nodes spanning the box (log ρYₑ segments 6–7, 7–8, 8–9; log T nodes 9.0–10.0)" | Quoted ranges reproduce exactly only when the log T = 9.0 column (below the box's 1.6 GK edge) is included; qualitative claims (EC positive bracketing 5/3, β⁻ negative) hold under both windows (phaseB-7 A3). [derived here] kept. |
| 22 | §V.5b measurement caption (was L2696) | "Second differences of the real tables, restricted to the box" | "…on the table nodes spanning the box (see note below)" + a windowing note after the table: steep-channel maxima centered on nodes outside the strict in-box stencil (⁵⁴Fe 3.95 and ⁴⁸Ca 1.73 at logρYₑ=7,logT=9.0; ⁴⁸Ca T-dir 3.92 at 9/9.176); strict-stencil maxima ⁵⁴Fe 2.11 → 0.264, ⁴⁸Ca 0.94 → 0.117; ⁵⁶Ni row and controller-scale conclusion unaffected | phaseB-7 A4; table values themselves are genuine second differences (all located to <0.006 dex) so the table is unchanged. [derived here] kept. |
| 23 | §V.8 (was L2827) | "`crosscheck/mesa_dump.py:92–93`" | "`crosscheck/mesa_dump.py:91–92`" | q_mev at line 91, qneu_mev at 92 (awk-verified); off-by-one (phaseB-7 A5). |
| 24 | Part VII item 3 (was L3280–3281) | "`compile_network` calls all four. There is no path into the flux engine that bypasses them" | "calls three of the four (`assert_screening_allowed`, `assert_reconciled_build`, `assert_pf_gate`); the fourth, `assert_appendixb_routing`, guards a different chokepoint — any request for MESA-side rate *values* (the spot-check harness) — since compilation never consumes stock-MESA values. No path into the flux engine bypasses the three compilation gates — which is a stronger property than 'all current callers check'." | compile.py imports/calls exactly three guards (lines 33, 162, 165, 251); `assert_appendixb_routing` has no production caller (tests only) (phaseB-8 A1). Stronger-property clause retained, now scoped to the three compilation gates. |
| 25 | §VI.4 (was L3032) | "**construction direction-swaps** (§III.4a)" | "(§III.4, construction (a))" | No §III.4a exists; content is §III.4's bullet (a) (phaseB-8 A2). |
| 26 | §VIII.C.6 pair table (was L3476) | n₊/n_net = 3×10⁻⁴ on the ρ=10⁹ row | **1.4×10⁻⁴** | Recomputed 1.373×10⁻⁴; the 2.7×10⁻⁴≈3×10⁻⁴ transcribed value is 2n₊/n_net, the pair excess of the total column (phaseB-9 A1). μ_e = 3.598 and total 1.000 unchanged; [derived here] kept. |
| 27 | §VIII.C.6 point 1 (was L3488) | "Γ(Si–Si) at that corner is only 0.40, so h is small and the enhancement is ~1.1× either way" | "Γ(Si–Si) at that corner is only 0.40, and for the α/p captures the network actually carries (Γ₁₂ ≤ 0.21) the enhancement is ~1.03–1.16× either way" | At Γ₁₂ = 0.40 chugunov_2007 gives 1.39×, not 1.1×; the ~1.1× band is true only of the network's real charged-particle channels (phaseB-9 A2). "The rate error is real but not large" survives. |
| 28 | §VIII.C.3 (was L3421–3424) | "The flux-route vs bbq comparison is already logged as UNRESOLVED [RESULTS 2026-07-10]. A missing loss term is a candidate explanation that nobody can currently test" | "(Status: the 2026-07-10 UNRESOLVED flux-route-vs-bbq row was retired by the 2026-07-11 eps_nuc convention pin — a units/convention mismatch, not an engine error [RESULTS 2026-07-11]; invariant-#5 proper passed 2026-07-12 with the constant-Q caveat of §III.12 [RESULTS 2026-07-12].) The gap itself stands: the engine still cannot compute ν losses — the pin leaned on the labels' own eps_neu column — so a missing loss term remains something nobody can test flux-route-side" | phaseB-9 A4 with adjudication item-6 wording, consistent with C2's §IV.9 fix; RESULTS.md rows 298/362 + phase0-checklist row 11. Gap entry remains open (item 12: still an open-gap entry). |
### Imprecisions tightened

| # | Location | Change | Source |
|---|---|---|---|
| 1 | §1.2.4 item 3 (was L462–464) | "not by the factor of 30" → "E_C/E₀ ≈ 1.7 here, not the factor of 10–100 … (≈ 12 for ¹²C+α at T₉ = 0.2, ≈ 76 for ¹²C+p at T₉ = 0.02, ≈ 100 for p+p)" | phaseB-1 imprecision 1 (recomputed examples); adjudication item 2. |
| 2 | §1.2.4 (was L468) | "reappears verbatim in §II.3" → "reappears to 0.01% in §II.3" | §II.3's own residual: a₂ = −59.4896 vs τ = 59.482 (phaseB-1 imprecision 2). |
| 3 | §1.1.4 code quote (was L306) | restored `dtype=np.float64` in the engine.py Ypad snippet | src/gnn_nucleo/fluxes/engine.py:180; project float64 convention is load-bearing (phaseB-1 imprecision 3). |
| 4 | §1.3.2 (was L583) | "In the Fe-peak at E₀ ≈ 4–7 MeV excitation" → "α-capture Gamow peaks sit at E₀ ≈ 4–7 MeV (compound-nucleus excitation E* = Q + E₀ ≈ 11–17 MeV)" | E₀ is CM entrance energy, not excitation; doc's own E* = Q + E₀ at §1.3.4 (phaseB-2 A6). |
| 5 | §1.4.3 (was L777–781) | Q/kT ≈ 27 attributed to the e^{−Q/kT} factor alone; parenthetical added: full fitted slope ≈ 35, ×~30 per 10% T rise; ≈15 rescoped to the threshold factor | Recomputed d lnλ_γ/d lnT of the reverse fit at T₉ = 3 = 35.0 (a₁ +26.9, Gamow +13.7, rest −5.6) (phaseB-2 A7; adjudication item 4). |
| 6 | §1.3.3 table (was L604) | Direct experiment "10–20%" → "a few % (best channels) to a few tens of %" | Align with corrected tier0 §0.3.3 (Iliadis et al. 2010 band) (phaseB-2 A8). |
| 7 | §II.2 code quote (was L918) | restored `, dtype=bool` in the compile.py:250 snippet | src/gnn_nucleo/fluxes/compile.py:250 (phaseB-3 minor; adjudication item 3). |
| 8 | §II.5 table (was L1022) | "the ±1 incidence matrix" → "the ± multiplicity-count incidence matrix (+n per reactant occurrence, −n per product occurrence)" | compile.py:232–239 and field comment "± counts"; ±1 wrong for e.g. triple-α (+3) (adjudication item 3 wording). |
| 9 | §III.7 (was L1595–1596) | "Three significant figures, from a one-line formula." → "Within ≲0.3 dex for most channels — and to three significant figures on the chapter-7 row (21.787 measured vs 21.795 predicted) — from a one-line formula." | Only the chapter-7 row agrees to 3 s.f. (dev 0.008); conforming ch6/9 devs 0.25–0.31 (phaseB-5 A2). |
| 10 | §VIII.B0 errata, 1.4.2 row (was L3324) | "the sensitivity is ≈ +0.8 in T₉ per decade of Y_α" → "≈ +0.5–0.8 in T₉ per decade of Y_α (steepening toward high Y_α)" | +0.8 holds only for the top decade (+0.76 measured); full-range mean +0.51 (phaseB-9 A3). Now consistent with fragment 1's §1.4.2 body fix. |
| 11 | Part VII closing (was L3287–3289) | "five separate physics conclusions in one file" + "(the fourth guard encodes two: the ordering pin and the reconciled-membership flag)" | Adjudication item 5: 4 guard functions genuinely carry 5 raise-backed conclusions; `assert_reconciled_build` has two independent raise blocks (guards.py, the two independent raise blocks of assert_reconciled_build) (phaseB-8 adjudication row 34). |
| 12 | §VIII.C.4 (was L3427–3443) | "(§1.4.3: d ln λ_γ / d ln T ≈ 27)" → "(§1.4.3: Q/kT ≈ 27 from the e^{−Q/kT} factor alone; the full fitted slope d ln λ_γ / d ln T ≈ 35 at T₉ = 3)" | Adjudication item 4: the restatement claimed the full slope (d ln λ_γ/d ln T form), so the ≈35 parenthetical was required, matching fragment 1's §1.4.3 rescope. |
| 13 | Handoff, gh-575 row (was L3810) | "matching measurement to ≲0.35 dex (§III.7)" → "matching measurement to ≲0.31 dex on non-identical-particle channels, with structured log₁₀k! offsets on the rest (§III.7)" | Adjudication item 7 (brief form), inheriting C2's correction #3 refinement. |
| 14 | §VIII.E.7 Farmer row (was L3742–3745) | "explicitly unconfirmed" → located verbatim in the abstract ("≈30% variations in the central electron fraction … ≈127 isotopes … at the ≈10% level"; Farmer et al. 2016); metric still undefined in the paper; η = 1−2Yₑ reading quantitatively consistent (η spreads ≈30%) while relative Yₑ is not (6–11%); interpretation half of the gap stands | Adjudication item 8; phaseB-9 §F (paper.tex:119–123 abstract + variations_med table recompute). |
| 15 | §VIII.C.2 cost paragraph (was L3494–3496) | "the α ladder and the Fe-peak captures are `ths8r` throughout" → "…throughout, with the single exception of ⁴⁰Ca(α,γ)⁴⁴Ti (label `chw0`, a resonance-based re-evaluation — one named channel for the tally to check; §1.3.5)" | Follow-up handed from fragment 1 (phaseB-2 A5 α-ladder label census: ca40(a,g)ti44 = 'chw0'); restores consistency with the corrected §1.3.5. |

## 2. Verification log by part (verified claims and their anchors)

**Part I, §1.1–1.2 (⟨σv⟩, conventions, code contract; Coulomb barrier, Gamow peak).**
Every equation (1.1)–(1.9) was verified against Rauscher & Thielemann 2000 and
Adelberger et al. 2011 (Solar Fusion II, fetched this session), with all algebra
recomputed symbolically (sympy) and all numerics in float64: RT2000's eq. (rate) is
verbatim the doc's (1.1) — "⟨σ*v⟩ = (8/πμ)^{1/2} 1/(kT*)^{3/2} ∫₀^∞ σ*(E) E exp(−E/kT*) dE" —
and Adelberger et al. give the MB relative-velocity distribution (their eq. 4), the
identical-particle 1/(1+δ₁₂) (eq. 2), the S-factor definition "σ(E) = S(E)/E exp[−2πη(E)]",
and the Gamow-window identities E₀, "ΔE₀/kT = 4√(E₀/3kT)", and the T₉^{−2/3}exp[−3E₀/kT]
rate form. The molar/gross-flux bookkeeping (1.2) is term-by-term Cyburt et al. 2010
eq. 2 ("For binary rates, lambda = N_A⟨σv⟩ has units of cm³ s⁻¹ mol⁻¹"). All six rows of
the E₀/Δ/kT table, the E_C table, τ = 59.48, and the Δ/E₀ = 4/√τ examples recomputed to
quoted precision; the adjudicated 4.2487-vs-4.2486 question resolved in the doc's favor
(CODATA 2018 gives 4.248710; Cyburt Table 1's 4.2486 is truncated). The reciprocity
theorem (1.11) was checked by explicit thermal averaging into RT2000's detailed-balance
ratio (symbolic, exact); its primary form (Blatt & Weisskopf) remains textbook-standard
(see §3). Project-internal quotes (compile.py:285–286, engine.py:174/179–182, sentinel,
7×10⁵ states/min/core [RESULTS 2026-07-10]) all matched the repo; the one factual error
found and fixed was the mesa_80 `ec` census (two Yₑ-weighted columns, not one).

**Part I, §1.3–1.6 (resonances, HF, photodisintegration, mapping, self-check).**
The narrow-resonance formula (1.10) with constant 1.54×10¹¹ and exp(−11.605E_r/T₉) is
verbatim Longland et al. 2010 (fetched this session): "N_A⟨σv⟩_r = (1.5399·10¹¹/T₉^{3/2})
((M₀+M₁)/(M₀M₁))^{3/2} Σᵢ(ωγ)ᵢ e^{−11.605 Eᵢ/T₉}"; the constant recomputes from CODATA
2018 as 1.539518×10¹¹. HF formula, ingredients, applicability ("level densities will
eventually become too low for the application of the statistical model"), the ≥10-levels
criterion, and the back-shifted Fermi gas ρ(U) = exp(2√(aU))/U^{5/4} anchor to RT2000 and
Rauscher, Thielemann & Kratz 1997. The load-bearing stellar-rate claim is RT2000 verbatim:
"only the use of the stellar cross section σ* yields a reaction rate with the desired
behavior that the inverse reaction can be calculated by using detailed balance." The
§1.4.2 crossover table was reproduced to all quoted digits (forward from the printed
a-set; reverse matches the pf-corrected DerivedRate values); balance points 3.31/4.50/
5.10/5.87 confirmed, the per-decade slope corrected (item 4). Triple-α sequential
mechanism per José & Iliadis 2011 ("The composite nucleus ⁸Be lives for only ∼10⁻¹⁶ s…");
Hoyle state 7.65 MeV per Freer & Fynbo 2014. Corrections: LMP uncertainty row, Wigner
limit coefficient, Thomson mfp, chw0 exception, E₀-vs-excitation wording, Q/kT hedge.

**Part II (REACLIB).** The seven-coefficient form (2.1) matches, index-for-index, the
REACLIB format spec, Cyburt et al. 2010 eq. 1, and RT2000 eq. (fitpar) — no off-by-one.
The fitting-rule table anchors to Cyburt Table 1 ("a1 = −11.6045Er", "a2 = −4.2486(Z1²Z2²A)^(1/3)",
a₆ ∈ {−2/3, ℓ, −3/2}) and the reverse shifts to RT2000 eq. (revcoff) ("a₁^rev = a₁ − 11.6045Q",
"a₆^rev = a₆ + 1.5"). The §II.3 dissection was verified digit-for-digit against
pynucastro 2.12.0 (both a-sets; differences +24.8918/−80.626/+1.5 exactly; ratio_factor
24.8935; Q = 6.94782 MeV); the v-flag-is-pf-free claim is a verified composite of the
format spec, RT2000's "has to be multiplied by the ratio of the partition functions",
Cyburt p. 30, and the data (only a₀/a₁/a₆ shift). The §II.6b λ-range table reproduced
exactly (spans 75/44/39/37 decades; exponents −4.4×10⁶…+38); corrections: labelprops
anatomy, underflow attribution (hot-edge, not cold), Q/kT "several hundred" → ≈173 max,
mesa_151 ~1700 sets. All RESULTS.md tags in range ([RESULTS 2026-07-10] ×4, 2026-07-08
gate form) matched their rows verbatim.

**Part III, §III.1–III.6 (the ratio derived; phase space; pf; three constructions;
v-flag; κ).** Eq (3.1) verified verbatim against Hix & Thielemann 1999b (JCAM98
eq. \label{eq:mu}, inverted); (3.2)'s 1/∏c! multiplicity factors against pynucastro
`Rate.counter_factors` and Smith et al. 2023 eq \label{eq:reverse}; (3.3) by symbolic
substitution; boxed (3.4) factor-for-factor against RT2000 eq. \label{invpart}/\label{invphot}
and Smith et al. 2023 (all six factors, identically arranged). fac = 9.868459969×10⁹
recomputed in float64 (RT2000 print the identical constant); the MESA form verified in
reaclib_support.f90:197 and RESULTS.md:203–205. All 35 pf-table entries and all 9
channel-table entries reproduced exactly from the shipped Rauscher tables (span
T₉ = 0.01–275); the normalisation-trap analysis confirmed against RT2000 eq.
\label{eq:partfunc} and Rauscher 2003 ((2J₀+1)-normalized, G → 1 as T → 0), with the
low-T diagnostic (⁴⁵Sc g = 8 reads 1.803 not ≈8) verified numerically. The v-flag
three-coefficient transform verified three ways (RT2000 eq. \label{revcoff}; Smith et
al. 2023 / DerivedRate source; measured on the ths8r/ths8rv library pair — exactly
{a₀, a₁, a₆} shift). κ = |ε|/(2+ε) algebra exact (0.200/0.333); all four κ-table rows
match RESULTS.md 2026-07-10; kappa.py's f_MESA = f_pyna·(λ_MESA/λ_pyna) trick verbatim
in the module docstring. Two corrections applied (#1, #2 above).

**Part III, §III.7–III.13 (gh-575; db_reverses; oracles; two κ conventions;
Coulomb-in-NSE; Q(T); self-check).** The `No == 1` branch verified at
reaclib_support.f90:228 (exact line, stock r23.05.1); the |ΔN_s − e| law and the
six-chapter table recomputed (all ΔN_s/e/powers correct; measured columns match
configs/appendixb_excluded_channels.yaml); the chapter-8 flagship (one power, not two;
c12→3α −10.118 at T₉ = 4) confirmed; the affected-set reconstruction (9 mesa_80 /
11 mesa_151 rows) recounted from the config; the completeness caveat's tabulated-arity
set re-derived from probe_dump_net CSVs (identical in both nets). Grichener et al. 2025
Appendix B read in full — it names only the n+n+⁴He+⁴He→³H+⁷Li class, so "Beyond the
paper" stands; gh-575 issue facts (opened 2023-08-07, fix via PR #632, closed
2024-05-06) cross-checked with no misattribution. db_reverses.py signature, two-tier
lookup (280/280, 672/672 in-collection), Counter assertion, and ReplaceReport.failed
semantics all verbatim in source; all five §III.9 oracle tests located with matching
thresholds (including the `f > median(f[f>0])` carrying cut and the retire-comment).
§III.10's 7.4×10⁻² screened median matches RESULTS row 276. §III.11's CP98 fit,
constants (A₁ = −0.9052, A₂ = 0.6322, A₃ = −√3/2 − A₁/√A₂ at cp98e.tex:665–669), and
DH-limit reading verified against the cached TeX (f_C → −Γ^{3/2}/√3 exactly; numeric
check 1.000000 at Γ = 10⁻⁶); the Z^{5/3}/Fe-peak direction and cold-dense magnitude
anchored to Hix & Thielemann 1996 (screening factors ~10⁶ at T₉ = 3.5, ρ = 10⁹).
§III.12: eq (3.6) is an algebraic identity; all 21 ⟨E*⟩ entries and all Q(T)−Q^gs
percentages reproduced in float64 (⁴⁰Ca(α,γ)⁴⁴Ti −19.16% at T₉ = 7.9; "nineteen times
the gate" ✓); the three qualifications' quotes verbatim in
docs/phase0-killtest-verdict.md:74–78 and docs/gnn-architecture/main.tex:137.
Corrections #3, #4, #9 applied.

**Part IV (screening).** (4.1) is Salpeter 1954 eq. 21 verbatim (coefficient 0.18791
recomputed → their 0.188), with the degenerate-electron caveat taken from Salpeter's
own §IV (f′/f → 3/2D); the ion-only collapse onto √3Γ^{3/2} exact algebraically and
numerically (two-component excess √(15/14) = 3.51% for Si). Ion-sphere 9/10 and the
strong-screening form match Salpeter eqs. 28–29 (0.205 = 0.9×0.22747 recomputed, and
Salpeter's own eq. 29 carries 0.205); h/Γ₁₂ = 1.057 vs A₁+B₁ = 1.0346 (2.20% apart) ✓.
Every chugunov_2007 constant in (4.6)–(4.7) verified against BOTH the cached
PIMCvsMF.tex (eqs. 3, 19, 21; A₃ = √3 − A₁/√A₂ = 1.4514924) and the code
(screening.py, pynucastro scalar; returned max(h, 0)); DH asymptote replicated to
6×10⁻⁶ at γ̃ = 10⁻⁶; the large-γ̃ wording corrected (#5). Γ corner table and the
16-entry enhancement table reproduced to ≤ 0.6% (offsets one-signed, consistent with an
unstated Yₑ slightly below 0.5); T_p = 1.2384×10⁷/10⁸ K and T_norm ~13–640 confirmed
(clip never engages in-box). (4.3) κ = |tanh(Δh/2)| exact; the replication run
reproduced the identity to 1.4×10⁻¹¹ and the RESULTS 7.4×10⁻² median (subset-sensitive
at the few-% level); bounds tanh(ln 3.3/2) = 0.535 ✓. §IV.9's TableIndex enum verified
against pynucastro source and the .dat file headers; MU/DQ bullets corrected (#6, #7)
per Suzuki, Toki & Nomoto 2016 (cached TeX, lines 516–551); compile.py:222 reads only
column 5 (grep-confirmed no other tabular column anywhere in fluxes/); the stale
UNRESOLVED citation replaced with the item-6 status wording (#8). The κ ≈ |Δ ln scor|
factor-2 passage at §IV.7 REMAINS a deliberate flag, untouched (adjudication item 12).

**Part V (weak sector).** Equations (5.1)–(5.3) verified verbatim against LMP 2000
(eqs. 1, 8c, 8a: K = 6146 ± 6 s from superallowed Fermi transitions; the vacuum
limit S_e = S_ν = 0 of Φ^{β−} is exactly (5.2)) and Bildsten & Cumming 1998 (eq. 5
and "the 1293 keV threshold" verbatim); the no-detailed-balance-pair claim anchors
to LMP 2000's "there is no neutrino blocking of the phase space, i.e. S_ν = 0",
and Pauli blocking of β⁻ to LMP 2000's density statement plus the RMP. All
[derived here] blocks recomputed independently: E_F table (1.019/1.967/3.983 MeV),
free-proton threshold (−0.78233/1.29333 MeV, CODATA), the ρ ≈ 2.4×10⁷ crossing
(2.448×10⁷), the finite-T μ_e = 0.161 MeV / η = −0.514 non-degeneracy, the
(143, 8) table anatomy with all 13 log T nodes and the 8-column header, box-edge
logs (6.6532/8.6990/9.2041/9.8976), the h²/8 bilinear bound, and every quoted
second difference (located to <0.006 dex). Two numeric errors fixed (in-box β⁻
floor and the 25-decade gap) and two windowing captions tightened — the physics
conclusions (anti-correlated error/importance budgets, EC-positive/β⁻-negative
indices, 0.1-dex controller band) survive the strict-stencil recompute. All
project-internal quotes (compile.py/_pair_maps weak skip, κ≡1, clamped
searchsorted, ye normalisation, WEAK_LEDGERS triples, |ΔZ|=1 abort, pinned
ordering + guard, duplicate-link resolution, census 607/38/46 and 1518/164/173,
6/9 EC + 0/8 β partners) matched repo files and RESULTS.md rows exactly; the one
mismatch was the mesa_dump line-number off-by-one (#5). Table-family provenance
(FFN/Oda/LMP/Suzuki/Pruet-Fuller coverage, MESA precedence LMP > Oda > FFN,
use_suzuki=.false., 14/23 → 0 sd-shell mismatches) verified against pynucastro
2.12.0, the MESA source tree, and RESULTS 2026-07-09.

**Parts VI–VII (reconciliation + guards).** Dominantly project-internal; every
[RESULTS] number in range matched RESULTS.md with zero mismatches (tallies
607/610/579/28/0/3 and 1518/1522/1486/32/0/4; medians 4.4/8.9×10⁻¹⁶, 0.048/0.095,
swaps 0.0004/0.0006; weak 38/164 at 0.066/0.073; +0.005→+0.013 signed drift; 135
outliers = 93+/25/13/4; screening 0.99999/0.0021/0.52/~1e-4; 69.4%/63.6%;
169/1876 with exact ×7 denominator arithmetic; 75 decades ↔ §II.6b). The
scholarly cluster verified against the cached Grichener et al. 2025 TeX: Appendix
B names exactly one reaction plus a mechanism (no channel list), so §III.7/VI.6's
"channels the paper missed" framing stands; the ≤1.9 dex collapse and the
2.7-dex both-version anomaly are correctly attributed to project measurement
(RESULTS 240–241), and the `No==1` single-product branch was verified at
reaclib_support.f90:178–250 in the local MESA tree. gh-575 facts (2023-08-07,
PR #632, closed 2024-05-06) consistent with scratchpad gh575.md. Two corrections
applied: the guards-chokepoint claim (three of four called by compile_network —
the range's only substantive finding) and the phantom §III.4a anchor; plus the
adjudicated four-guards/five-conclusions parenthetical. One inline citation
added at the VI.6 defect location per report 8's section C.

**Part VIII + handoff.** All twelve B0-errata AFTER values re-verified by report 9
(arithmetic, MESA source, RT2000, Salpeter/Chugunov constants); the 1.4.2 row's
sensitivity clause tightened to the measured +0.5–0.8 steepening band. C.5's
4%/47% ΔQ leverage, C.9's 228/0.045/≈10/≈26, the C.6 pair table (three rows to
all printed digits; row 4's n₊/n_net corrected ~2×), the tanh identity, the E_F
pair 1.02→3.98 MeV, the a₂ = 4.2487 constant, and the float32 facts all
recomputed. NuGNN's C = 17 shift trick verified verbatim in the cached 2606.04491
TeX and now cited (Kim et al. 2026); Ono & Sugimura 2026 confirmed real
(arXiv 2508.16114, ApJ 996, 9 — timescale-rescaled update matches the doc's
description) and the E.1 mention converted to citation form; the Guidry
ε-criterion verified verbatim in 1112.4738. C.3's stale UNRESOLVED citation
replaced with the item-6 status wording (gap stands); C.4's ≈27 restatement
gained the full-slope ≈35 parenthetical (it used the d ln λ_γ/d ln T form);
the E.7 Farmer row upgraded from "unconfirmed" to located-verbatim with the
η-consistency finding (interpretation half open); the handoff's ≲0.35 dex repeat
replaced by the item-7 brief form; C.2 now names the ⁴⁰Ca(α,γ)⁴⁴Ti/`chw0`
exception. E-section cross-references (architecture report components A–D,
checklist open rows {2,3,4,5,12,13,14,15}, row-15 RETIRES quote, commit 1cb6f47,
cond(CCᵀ), ν nullity 1, SkyNet/WinNet plan line) all verified by report 9
against the repo; none needed edits.

## 3. Items that remain assumed / unverifiable (tagged in text where relevant)

From phaseB-1 §D:
1. **r₀ ≈ 1.2 fm touching-spheres convention** (§1.2.1). Universal textbook convention
   (Iliadis §2.1, Krane, Blatt & Weisskopf), no reachable primary opened; passage is
   [derived here] and the arithmetic recomputes exactly. Left as is.
2. **Threshold law T_ℓ ∝ k^{2ℓ+1}** (§1.2.6). Wigner 1948 / Blatt & Weisskopf pre-arXiv,
   not opened; content textbook-standard and internally consistent with Cyburt Table 1's
   a₆ = ℓ rule. Cited by attribution.
3. **Reciprocity theorem exact form (1.11)**. Blatt & Weisskopf not reachable; attribution
   supported by Cyburt et al. 2010 p. 30 verbatim; form proven consistent with RT2000's
   ratio by explicit thermal averaging (symbolic check True).

From phaseB-2 §D:
4. **Equilibration ordering (n,γ) → (p,γ) → (α,γ)** (§1.5). No cached source states the
   three-step ordering explicitly (JCAM98 supports the n-capture step; the rest is the
   doc's own barrier-scaling §1.2). Kept with internal cross-reference only.
5. **Y_α ≈ 10⁻⁷ early in Si burning** (§1.4.2). Premise linking the balance table to the
   project band; no quotable source located. Candidate for derivation from a shipped
   trajectory row.
6. **"For most capture reactions SEF > 1"** (§1.3.5). Plausible, consistent with RT2000's
   f* tables; no verbatim statement found.
7. **Structure scales 10⁷–10⁸ cm** (§1.4.4). Generic stellar-structure magnitude; only
   feeds an inequality that now holds by ~13 orders.

From phaseB-3 §D: none — every scholarly claim in Part II traced to an opened source.

From phaseB-4 §D and phaseB-5 §D: none — every scholarly claim in §III.1–III.13
resolved against an opened source, every [derived here] number was recomputed, every
[RESULTS] tag matched.

From phaseB-6 §D:
1. **Yakovlev et al. 2006, eq. 10 as the source of the T_p / Γ₁₂ pair generalization**
   (Z² → Z₁Z₂, n_i → n_e/z̃³, m_i → 2μ₁₂) used for unlike pairs (§IV.5). Supported
   only by pynucastro's source comment ("This also matches Yakovlev et al. 2006,
   eq. 10"); the paper (presumably Phys. Rev. C 74, 035803) was NOT opened. The
   inserted inline text is deliberately hedged accordingly: "the Z₁Z₂, 2μ₁₂ pair form
   is pynucastro's generalization, attributed there to Yakovlev et al. 2006." Fetch
   and verify before promoting to a bare citation; References entry flagged below.

From phaseB-7 §D:
1. **GT/Fermi ΔJ selection rules** (§V.2) — standard textbook (allowed
   approximation); LMP sources give operators and isospin selection only, no
   explicit ΔJ sentence. Left uncited as standard (Krane-style textbook entry
   not adopted).
2. **"Rate scale in this box: strong/EM 10³–10⁸ s⁻¹" row** (§V.1 table) —
   order-of-magnitude characterization, no single source; weak 10⁻⁵–10² is loose
   for the steep β⁻ tail but acceptable for dominant channels. Left as
   interpretation.

From phaseB-9 §D:
3. **"MESA switches to an NSE solver above some temperature"** (§VIII.E.6) — no
   cached source pins a hard NSE-solver switch (closest: op_split_burn at
   T ≳ 3 GK). Phrasing loose; not in any approved correction list, left as is.
4. **²⁶Al isomer "at kT ≈ 0.3 MeV thermal coupling is fast"** (§VIII.C.8) —
   plausibility argument inside an explicitly-open gap item; unsourced, low
   stakes, left.
5. **Salpeter's printed "0.205"** (§VIII.B0 IV.3 row) — numerically reproduced
   (0.20472) but the ADS scan has no text layer; a verbatim quote would need the
   page read visually.

## 4. Follow-ups outside this document's scope (not applied)

1. **Equation numbering (1.10)/(1.11) out of order** ((1.11) at §1.2.6 precedes (1.10) at
   §1.3.1). NOT renumbered per adjudication item 1 — cross-references elsewhere depend on
   these tags. Editorial quirk, logged only.
2. **§VIII SEF open-item scope** should name ⁴⁰Ca(α,γ)⁴⁴Ti / `chw0` explicitly now that
   the ladder census found it (phaseB-2 A5 note) — §VIII is outside this fragment's
   range; handed to the Part VIII application agent.
3. **§1.4.2 crossover-table provenance parenthetical** ("reverse pf-corrected via
   DerivedRate(use_pf=True)") suggested by phaseB-2 §B but not in its §A correction list;
   not applied (table verified as printed; provenance note is a candidate RESULTS.md row,
   coordinator's call).
4. **L883 constant 11.605** left as is (rounding of 11.6045; adjudication item 3, log-only).
5. **L987–993 `evaluate_lambda` snippet** left as is (elision marked by `...`;
   adjudication item 3, log-only).
6. **Candidate RESULTS.md rows** surfaced by phaseB-2 §F (α-ladder label census;
   crossover-table pf provenance) — not added here (append-only log is coordinator scope).
7. **Deviation from proposed wording, logged**: correction #2's proposed After put
   "(§V.3)" alone in the Why column; I kept "Gamow–Teller strength (§V.3)" so the Why
   column keeps its meaning. Content of the Uncertainty cell is exactly as proposed.

1. **phaseB-5 bonus finding (RESULTS.md follow-up candidate, NOT a doc edit):** the
   0.77–0.78-dex residuals on r_he4_he4_he4_to_h1_b11 / r_c12_to_he4_he4_he4 equal
   log₁₀3!, and ~0.30-dex residuals on two-identical-particle channels equal log₁₀2!,
   across all three temperatures — structured, suggesting stock MESA
   `compute_rev_ratio` ALSO omits identical-particle multiplicity factors (a second,
   multiplicity-shaped defect on top of the missing fac·T₉^{3/2} power; possibly
   relevant to the still-open he3_he3 anomaly, though 1.79 dex is not obviously
   factorial-shaped). tier1.md now carries only what correction #3's refinement
   paragraph states; the RESULTS.md row is coordinator scope (append-only log).
2. **Line ~3810 (Part VIII) cross-range repeat** of "≲0.35 dex (§III.7)" inherits
   correction #3; adjudication item 7 prescribes the brief form ("matching measurement
   to ≲0.31 dex on non-identical-particle channels, with structured log₁₀k! offsets on
   the rest (§III.7)"). Part VIII is outside this fragment's range — hand to C3.
3. **§III.2 forward reference** (now ~L1385): "Hold those numbers — §III.7 matches
   them against a measurement to three significant figures." Not in any approved
   correction list, so left as printed; after correction #9 the 3-s.f. claim holds
   only on the chapter-7 row. Candidate one-word softening for the coordinator.
4. **RT2000 eq-number anchors dropped** from the inserted citations (report 4 proposed
   "eq. 13", "eq. 12", "eq. 17" but instructed: spot-check against the published ADNDT
   PDF before freezing, drop if not confirmed — no PDF check was possible here). The
   "(e.g. Rauscher & Thielemann 2000, §2)" option likewise inserted without the §2.
   Chugunov et al. 2007 and Salpeter 1954 eq numbers WERE kept (corroborated
   independently: pynucastro source comments / the published ADS scan itself).
5. **Report-6 minor log-only items** (no edits, per its §A note): the
   `# T_norm*T_p == T` comment in the §IV.3 code quote is a doc annotation not present
   in screening.py:110 (true in-box where the clips are inactive); §IV.8's "≤10⁻¹² abs"
   is strictly abs-with-relative-guard (`1e-12 * max(1, |ref|)`); the §IV.4 Γ and
   enhancement tables assume an unstated composition with Yₑ slightly < 0.5
   (deviations ≤ 0.4%/0.6%, one-signed, immaterial).
6. **Yakovlev et al. 2006 fetch-and-verify** before promoting the §IV.5 attribution
   (item 3 above) to a bare citation.

1. **Optional (Rauscher, Heger, Hoffman & Woosley 2002) citation** at
   §VIII.C.7's "adaptive networks in astrophysics" (report 9 C, marked optional)
   — not applied; paper not cached and the sentence's named methods are now
   individually cited.
2. **§VI.6 step 3's "≲0.35 dex"** left as printed: it restates the RESULTS.md
   row-216 bound that report 8 verified ok (adjudication items 7/13 govern the
   L1592 quote and the handoff repeat only; the RESULTS row's own wording keeps
   0.35).
3. **§VIII.E.6 NSE-switch softening** suggested by report 9 §D — not in any
   section-A list; logged as assumed item 3 above.
4. **GT selection-rule textbook entry (Krane 1988)** — offered as an option by
   report 7 §D1; not adopted (rules are correct and standard).
5. **grids.py "reused by … the kill-test" soft staleness** (§VI.8b; report 8
   minor note — run_killtest.py currently uses killtest.strata.T9_EDGES) — no
   correction proposed; log-only for the coordinator.
6. **Farmer η-table promotion** — report 9 recommends attaching the recomputed
   η-spread table to the checklist item and promoting the reading to
   "derived-from-source data"; checklist/RESULTS.md edits are coordinator scope.
   The doc row now carries the finding narratively.
7. **Candidate RESULTS.md rows** from report 7 (in-box β⁻ floor scan;
   strict-stencil Δ² maxima) — append-only log is coordinator scope.
8. **§VIII.E.7 intro "Three open checklist items are *sourcing*"** retained
   although Farmer's sourcing half is now closed — the row itself explains the
   split; rewording the intro was not in any approved list.

## 5. Adversarial verification pass (Phase D)

Three independent agents ran after all corrections and citations were applied.

**D-1 — corrections re-check.** All 43 rows independently re-verified (arithmetic
recomputed from scratch; both networks recompiled; balance points re-solved from
the printed coefficient sets; weak tables re-read node-by-node; every cited TeX
passage re-opened): **41 CONFIRMED, 2 PARTIAL, 0 not-applied, 0 wrong.** The two
PARTIALs (rows 19–20, the in-box β⁻ floor and the decade gap) were node-correct
but missing an interpolation qualifier — bilinear interpolation at the cold-dense
box corner reaches ≈ −24 (gap ≈ 25 decades), so the pre-audit "−27 / 25 decades"
was node-wrong but state-defensible. Fixed in place; rows 19–20 above now carry
the amended wording. D-1 also caught two stale restatements of the old
"factor 2–10" LMP figure (§V.3 point 3 and §VIII.C.1) that correction #2 had
missed — both now fixed — plus three evidence-cell imprecisions in this log
(row 16's suzuki value, row 19's table-family attribution, the guards.py line
spans), corrected above; and it tightened two wordings ("Fe-peak α-captures" in
§1.3.5/§VIII.C.2, since a handful of Fe-peak n/p captures are `ks03`-class
experimental fits; the §IV.5 large-γ̃ limit now reads (A₁+B₁)γ̃ + O(√γ̃)).

**D-2 — citation-fidelity spot-check.** 27 instances sampled across all six
high-frequency sources, every eq/table/§ anchor, and Parts I–VIII: **0 misplaced
citations.** Five wrong anchors were found and fixed: Chugunov et al. 2007
"§V.A" → §IV.C; Bildsten & Cumming 1998 "eq. 5" → eq. 3 (confirmed against the
published ApJ 506, 842); and the three LMP 2000 equation anchors (1/8a/8c),
which disagree with the cached arXiv TeX numbering (2/9a/9c) and could not be
checked against the paywalled published version — dropped to bare
(Langanke & Martínez-Pinedo 2000) citations. The two Salpeter 1954 anchors the
spot-check could not confirm from the extracted notes (eqs. 28, 29 — the ADS
scan has no text layer) were adjudicated by reading the scan pages visually:
both are correct (eq. 28 is the ion-sphere energy with the explicit
(3/2 − 3/5) = 9/10 structure; eq. 29 carries the 0·205[(Z₁+Z₂)^{5/3} −
Z₁^{5/3} − Z₂^{5/3}] form verbatim); the confirmation is recorded in
`data/literature/web/salpeter1954.md`.

**D-3 — mechanical consistency.** Citation ↔ References bijection: one orphan
found (Hix & Thielemann 1996, cited at §III.11 with no entry) and fixed by
adding the entry; zero orphan entries — all 37 References entries are cited at
least once. Math/markdown: $$ delimiters even; code fences balanced; 47 tables
with zero column-count mismatches; no duplicated headers. Tags: 34
[derived here] and 34 [RESULTS …] occurrences, none malformed. Cross-file: the
status-block link to this log resolves; the README's Part-VIII anchor still
resolves; `# References` is h1, matching tier0.md. Repo hygiene: git porcelain
shows only `study/tier1.md` modified and `study/tier1-audit.md` added.

The detailed D-1/D-2/D-3 reports were produced in the session scratchpad; every
fix they prompted is reflected in the document and in the tables above.

## 6. Literature cache

New arXiv TeX fetched into `data/literature/` during this audit:
`physics/9807042` (Chabrier & Potekhin 1998), `astro-ph/0009261` (Potekhin &
Chabrier 2000, fetched but ultimately uncited), `1512.00132` (Suzuki, Toki &
Nomoto 2016), `astro-ph/0211262` (Pruet & Fuller 2003), `astro-ph/9706294`
(Rauscher, Thielemann & Kratz 1997), `1004.2318` (Adelberger et al. 2011),
`1004.4136` (Longland et al. 2010), `1001.0678` (Descouvemont & Baye 2010).

Web-fetched sources preserved under `data/literature/web/` (see its
MANIFEST.md): the JINA REACLIB format specification PDF, the open OSTI
preprint of Cyburt et al. 2010 (LLNL-JRNL-452312; the paper has no arXiv
posting), the ADS article scan of Salpeter 1954, and the MESA issue #575
body + comments (GitHub API). Bibliographic data for pre-arXiv, non-open
papers (Oda et al. 1994; Langanke & Martínez-Pinedo 2001; the FFN series;
NACRE) was Crossref/ADS-resolved; NACRE ended up uncited. The full phase-B
verification reports (per-claim verdicts with verbatim supporting passages)
were produced in the session scratchpad; this log is their durable summary.
