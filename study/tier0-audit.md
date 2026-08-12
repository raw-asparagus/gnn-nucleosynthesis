# tier0.md literature audit — claim-by-claim log

**Date:** 2026-08-12.
**Method:** ten parallel verification agents, one per thematic chunk of
`study/tier0.md`, each instructed to (1) inventory every checkable claim,
(2) classify it scholarly / arithmetic / project-internal / interpretation,
(3) verify scholarly claims only against sources actually fetched (arXiv TeX
cached into `data/literature/`, AME2020/ENSDF/CODATA data pages, GitHub
issues, local MESA r23.05.1 and bbq installations), recording the supporting
passage, and (4) recompute all worked arithmetic in float64 via `uv run
python`. Findings were reconciled in the main thread; corrections were applied
in place per the user's instruction, each logged below. Project-internal
numbers (RESULTS.md measurements, config contents) were **not**
literature-verified — `RESULTS.md` is their source of truth — but several were
re-derived directly from the repo's configs/exports as a consistency check.

Verdict key: **VERIFIED** = supporting passage/value found in a fetched
source, or arithmetic reproduced exactly; **CORRECTED** = document changed in
place; **ASSUMED** = order-of-magnitude estimate with no direct source, now
tagged as such in the text; **PROJECT-INTERNAL** = repo-measured, excluded
from literature verification.

---

## 1. Corrections applied (before → after)

### Incorrect values or statements

| # | Location | Before | After | Source / evidence |
|---|---|---|---|---|
| 1 | §0.3.1 worked example + table | Δ(⁵⁶Fe) = −60.601 MeV; B = 492.24 MeV | Δ = **−60.607** MeV; B = **492.26** MeV (inputs upgraded to Δ(¹H) = 7.2890, Δ(n) = 8.0713) | AME2020 (IAEA AMDC mass table): −60 607.163 keV. The old value matches neither AME2020 nor AME2003 (−60 605.352). B/A = 8.790 unchanged. |
| 2 | §0.3.1 table | ⁶²Ni B/A = 8.794 (also §II.2) | **8.795** | AME2020 B/A = 8794.555 keV; Fewell 1995: 8794.60 ± 0.03 keV. Also Δ(⁵⁶Ni) −53.90 → −53.908, Δ(⁵⁸Fe) −62.153 → −62.155 (roundings). |
| 3 | §0.3.3 table, LMP row | "factor ~2–10, GT-strength dependent" presented as an uncertainty | No blanket figure exists; LMP-vs-FFN *differences* reach factors ~10–350 for key EC nuclei | nucl-th/0001018 verbatim: "smaller than the FFN rates by factors 39, 12, 10, 346, and 19". No 2–10 uncertainty statement in LMP 2000/2003. |
| 4 | §0.4.2 | Coherent-scattering enhancement "roughly A²/6" | "roughly **N²/16 ≈ A²/60**" | Janka 2017 (arXiv:1702.08713), eq. for σ_A,coh = (1/16)σ₀(E/m_ec²)²N². A²/6 is ~10× too large; no source states it. Trapping-density conclusion unaffected. |
| 5 | §0.5 chapter table | ch-6 example "¹²C(¹²C,α) class" | "¹¹B(p,2α)α, ³He(³He,2p)⁴He class" | All ¹²C+¹²C rates in REACLIB are chapter 5 (two products; pynucastro 2.12.0 query). The 13 real ch-6 forwards are light-ion 2→3. |
| 6 | §0.5 chapter table | ch-7 example "heavy-ion breakup" | "light-ion 2→4 breakup, e.g. ⁷Li(³He,npα)α" | The 5 tabulated ch-7 forwards are all light-ion (⁷Li/⁷Be/⁹Be + ³H/³He/p). |
| 7 | §0.5 | "Chapters 10 and 11 do not appear because REACLIB tabulates no forward of that arity in these two networks" | Refined rather than reversed: REACLIB's five ch-10 entries are all **v-flagged detailed-balance reverses** of the ch-7 forwards (three touch only in-network species, e.g. n+p+α+α→³He+⁷Li — the raw-reverse class the pf gate forbids); ch-11 forwards are dripline β-delayed multi-neutron emitters, outside these networks. The original "no forward of that arity" was defensible; the text now states the full picture. | pynucastro 2.12.0 ReacLibLibrary query; v-flags checked by the Phase-D verifier (labelprops mafonv/cf88cv). |
| 8 | §0.5 | `class: multi_body_inverse` "names the real criterion" (singular) | Two class values: `multi_body_inverse` (15 rows, ch 6/7/9) and `photo_of_multibody` (5 rows, ch 8 — including the 3α inverse) | `configs/appendixb_excluded_channels.yaml`, recounted programmatically. |
| 9 | §I.1 | "A star above ~8 M⊙ burns through a sequence of fuels" ending at Fe; table header "(8–25 M⊙)" | Full sequence needs ≳10–11 M⊙; 8–11 M⊙ stars end as ONeMg cores; header now "(15–25 M⊙ models)" | Pols lecture notes ch. 12 (M_up ≈ 8 M⊙ ignites carbon; M_ec ≈ 11 M⊙ for beyond-carbon). |
| 10 | §I.1, §0.7, §IV.2 | Si-burning duration "~1 day" / "~10⁵ s" | "~1 day–2 weeks", "~10⁵–10⁶ s (mass-dependent)" | WHW02 via Pols Table 12.1: 18 d at 15 M⊙; Woosley AY220: ~1 week at 20 M⊙; José & Iliadis 2011: "may last only one day". |
| 11 | §I.1 | "from ²⁰Ne onward, photodisintegration initiates the burning" | Photodisintegration-initiated stages are Ne and Si; **oxygen burning in between is true heavy-ion fusion** | Woosley AY220 Lecture 12 stage table ("Oxygen burning — heavy ion fusion"; "a true fusion reaction, not just a rearrangement"). |
| 12 | §I.3 table | LU ratio mesa_151/mesa_80 "6.5×" | **6.7×** | (151/80)³ = 6.73; 6.5 was an artifact of dividing rounded table entries. |
| 13 | §I.3 | "Dense LU is n³/3 FLOPs" | "≈ 2n³/3 FLOPs, i.e. n³/3 multiply–add pairs" | Modern flop convention (Golub & Van Loan); table relabelled to multiply–adds. Ratios unchanged. |
| 14 | §I.3 | "~10⁶ timesteps" per stellar model | "of order 10⁴–10⁶ timesteps to core collapse" | No source for 10⁶; typical MESA runs are 10⁴–10⁵ steps. |
| 15 | §I.4 figure | (N,Z) sketch omitted the Ne row, so legend species `ne18` was undisplayed | Ne row added (`ne18● ne19 ne20 ne21 ne22 ○`) | Recomputed from `configs/isotopes_mesa{80,151}.yaml`: all other rows exact; ne23 is the one mesa_151-only Ne isotope. |
| 16 | §I.4 | mesa_80 "structurally incapable of representing the neutron-rich β-decay chains… one-way Yₑ ratchet with no restoring channel" | Qualified to the named controller-partner set; mesa_80 carries 19 β⁻ / 19 Yₑ-raising weak channels; bias is "downward", not one-way | RESULTS.md row 130 (2026-07-08): "mesa_80 weak sector NOT one-directional at rate level". |
| 17 | §I.7 | NNN "a fixed-width map from an 80-vector to an 80-vector" | (80+2)-in/(80+2)-out; separate net per timestep, different depth per network | Grichener et al. 2025 §2.3 (arXiv:2503.00115): inputs (logT, logρ, X), outputs (X′, e_nuc, ε_ν); N_layers 12 vs 9. |
| 18 | §II.4 | **R = ρN_A Y₁Y₂⟨σv⟩N_A/(1+δ₁₂)** — duplicated N_A (off by ~6×10²³; dimensionally inconsistent with the doc's own [mol g⁻¹ s⁻¹]) | **R = ρN_A Y₁Y₂⟨σv⟩/(1+δ₁₂)** | Hix & Thielemann 1999b eq. 10 verbatim (two-body ρN_A, three-body ρ²N_A²); dimensional recomputation. The hardest error found in the document. |
| 19 | §II.3 / §0.6 | e_nuc = −N_A Σ m_i ΔY_i (missing c²) | −N_A Σ m_i c² ΔY_i | Hix & Thielemann 1999b eq. 12. |
| 20 | §IV.1 | "**Nobody solves this monolithically.**" | MESA's *default* is a monolithic fully-coupled solve; the split mode is `op_split_burn` — fixed-(T,ρ) sub-steps, often the only tractable option in Si/Fe burning | Paxton et al. 2011 verbatim ("simultaneously solves the full set of coupled equations"); Jermyn et al. 2023 (`op_split_burn`, "may be the only way to make certain problems tractable"). Also *answers* §IV.1's boxed open question in split mode: constant-(T,ρ) sub-steps, no in-step T feedback. |
| 21 | §V.2 (×2) | Rank-revealing cond "41.7 / 57.6" | **41.57 / 57.86** | Stale 2026-07-08 values; RESULTS.md 2026-07-09 & 07-12 + fresh recompute on current `data/stoich/nu_*.npz`. Project-internal fix per RESULTS.md, not literature. |
| 22 | §VI.2, §II.6 | I→I view "giving K ≥ 2 there" (and "diameter 3" for the I→I projection) | Two-stage fix. First pass: K ≥ 2 → K ≥ 3 by halving. Phase-D verifier then found the repo's *measured* I→I projection is radius 2, **diameter 4** (RESULTS.md 2026-07-09, row 196) — the projection is its own graph object, not the bipartite metric halved. Final text: I→I view measured at d = 4, requiring K ≥ 4 at one hop/round; K = 5 exceeds the requirement either way. | RESULTS.md row 196 (project-internal; RESULTS.md wins); arithmetic. |
| 23 | §VI.4 | hardwired/softwired/approx presented as MESA's taxonomy | "hard-wired" is MESA's term; "softwired" is community usage (Farmer et al. 2016) | Exhaustive grep of MESA r23.05.1 tree + instrument papers: "softwired" absent; Farmer et al. 2016 defines it and classifies `mesa_*.net` as softwired. |
| 24 | §VI.3 | "The NuGNN failure mode was applying the *projector* in the warped space" | NuGNN never applied a projector: enforcement attempts (loss/activation) required inverting the signed-log warp, destabilized training, and were **dropped entirely**; ships unconstrained + retry-on-drift heuristic | Kim et al. 2026 (arXiv:2606.04491) §Training (line 226) and §Discussion (retry, line 308), read in TeX. |

### Imprecisions tightened

| # | Location | Change | Source |
|---|---|---|---|
| 25 | §0.1.5 | "textbook critical density" 1.2×10⁷ now attributed (Shapiro & Teukolsky 1983; Bildsten & Cumming 1998 for the ρ ≳ 10⁷ statement) — the number itself is this document's own derivation at Yₑ = 1 | S&T not fetchable; B&C 1998 fetched (quotes Rosenbluth et al. 1973). |
| 26 | §0.2.2 | First-excited-state window "0.5–2 MeV" → real span 14 keV–2.7 MeV with named examples; G "~1.5–3" → ~1.5–3 typical, up to ~4–7 (⁵⁷Fe 6.6); ⁵⁶Ni G = 1.002 confirmed | ENSDF levels via IAEA API; discrete Boltzmann sums recomputed. |
| 27 | §0.3.2 | "6-day decay chain" → half-lives stated per step (6.08 d, 77.2 d; the 77-d step dominates the tail) | ENSDF: 6.075 d, 77.236 d; Diehl et al. 2015. |
| 28 | §0.3.3 | Direct-experiment "10–20%" (unverifiable as blanket figure) → "a few % to a few tens of %" + Iliadis et al. 2010 | No source states 10–20%; grepped RT2000, Rauscher 2003, NACRE materials. |
| 29 | §0.4.1 | Thermal losses "(T,ρ) only" → (T, ρYₑ) + Z̄/Ā for bremsstrahlung; "~T⁹" → relativistic-limit asymptote, steeper (~T¹¹) below | Itoh-family fits take abar/zbar (Timmes' implementation); LMP RMP: "scales approximately like T¹¹" at 5×10⁸ K; T⁹ derivation valid kT ≳ m_ec². |
| 30 | §0.5 | gh-575 mechanism "either no factor, or one power where \|ΔN\| were needed" → issue reports the factor omitted; per-channel power count marked as inference | Neither the issue nor Grichener App. B states the finer mechanism. |
| 31 | §0.7 | dt-grid bullet: 10⁻⁶ s floor sits *at* (not below) the fastest charged-capture timescales | Internal consistency with the table's own 10⁻⁶–10⁰ s row. |
| 32 | §III.2 | NSE-from-≈5-GK now quantified via τ_NSE = exp(196.02/T₉ − 41.645) s | Calder et al. 2007 (fetched): 1572 s at 4 GK, 0.087 s at 5 GK. |
| 33 | §III.3 | dt-range rationale: covers "most" (per the source paper), not the whole envelope — fully-coupled MESA steps < 10⁻¹⁰ s near collapse | Grichener et al. 2025 ("encompassing most timesteps"); Jermyn et al. 2023 ("δt < 10⁻¹⁰ s are common"). |
| 34 | §III.3, §IV.1 | ν_T ≈ 20–40 qualified to the photodisintegration rates (ν_T ≈ Q/kT = 18.6–46.4 for Q = 8–12 MeV, T₉ 3–5); charged-particle captures ~4–17 | Q-range from Hix & Thielemann 1999b; Gamow ν_T = (τ−2)/3 recomputed. |
| 35 | §III.4 | Dyadic-box exactness limited to elementary intervals of volume ≥ 2^(t−m); t grows with d; net-vs-sequence log exponent (d−1 vs d) footnoted; Owen-scrambling RMSE given with its (log N)^((d−1)/2) factor | Owen 2022; Owen 1997a,b / 2008 via Owen 2022. |
| 36 | §II.3 | m_u = 1/N_A footnoted (post-2019 SI deviation +1.05×10⁻⁹); (M−Au)/(Au) table flagged atomic-convention (bare proton +0.73%) | CODATA 2022 molar-mass constant; AME2020. |
| 37 | §II.5 | Positron-capture folding: true of the *evaluated* rate (weaklib sums decay+capture); raw tables carry a separate leps⁺ column | MESA r23.05.1 `weaklib_tables.f90` line 260 (`lambda = decay + capture`); `weakreactions.tables` header. |
| 38 | §II.7 | Path `data/subsample.py` → `src/gnn_nucleo/data/subsample.py` | Repo (ambiguity with gitignored `data/`). |
| 39 | §V.2 | "rank-revealing condition number" flagged as borrowed terminology (Chan 1987; "effective condition number" nearest standard term) | Chan 1987 (record). |
| 40 | §V.3 | Fastest/slowest rate endpoints (10¹⁰ s⁻¹; 10⁻⁵–10⁻² s⁻¹) tagged **assumed** pending the Jacobian measurement; bracket shown consistent with H&T 1999b and Guidry et al. 2013 | No source states the endpoints; "S > 10¹⁵ not uncommon" (H&T99b), "10–20 orders" (Guidry). |
| 41 | §V.3 | Stiffness ⟺ slow manifold ⟺ QSE: one-directionality caveat added (cf. ILDM, Maas & Pope 1992) | Logical point; standard singular-perturbation picture. |
| 42 | §VI.2 | 1-WL bound: "on unlabelled graphs" dropped (theorems hold for labelled graphs; features make the bound non-binding from iteration 0) | Xu et al. 2019; Morris et al. 2019 (both fetched). |
| 43 | §VI.6 | "constrain progenitor Yₑ" → "the Yₑ of the ejected burning region" | Jerkstrand et al. 2015 framing. |
| 44 | §I.2, §VI.6 | ξ_2.5 "evaluated at bounce" qualifier added | O'Connor & Ott 2011 (fetched): defined at t = t_bounce; precollapse evaluation "ambiguous". |

---

## 2. Verification log by part (verified claims and their anchors)

Everything below was checked against a fetched source or recomputed; only the
highlights and load-bearing anchors are listed. All worked arithmetic in the
document reproduces in float64 except where a correction above says otherwise.

**§0.1 EOS & plasma.** All ~20 worked numbers reproduce (n_e, n_i, kT, p_Fc,
E_F, pressure shares 92.6/4.8/2.6%, degeneracy table, Γ table 0.40–25.1, EC
threshold chain ρ_crit = 2.448×10⁷). Constants match CODATA 2022 exactly.
Γ = Z²e²/(a kT) with ion-sphere a: verbatim in Chugunov et al. 2007, whose fit
covers Γ ≪ 1 (Salpeter 1954 Debye–Hückel limit) through Γ ~ hundreds; MESA
`screen_chugunov.f90` header confirms the config link. Pre/post-threshold
capture physics: Bildsten & Cumming 1998. Note: P_e ≈ ¼n_e p_Fc overestimates
the exact Fermi integral ~6.5% at x = 3.7 (labelled an approximation in the
text; conclusion robust).

**§0.2–0.3 statistical mechanics & nuclear data.** Σνμ = 0 → NSE
μ(Z,N) = Zμ_p + Nμ_n: verbatim in Pitrou et al. 2018 and Hix & Thielemann
1999b (two constraints: ΣAY = 1, Yₑ). QSE cluster offset: equivalent
focal-nucleus form in Hix & Thielemann 1996 (r_QSE constant within a group,
"blends simply into the NSE distribution"). G(T) definition: RT2000/Rauscher
2003 verbatim (both add a level-density integral above the last discrete
state — noted). Reverse-rate ∝ G_i/G_m · e^(−Q/kT): RT2000 eq. (invpart)
verbatim — linear in G, so factor 2 in G = factor 2 in reverse rate ✓.
Time-reversal → detailed balance: Mitchell, Richter & Weidenmüller 2010
(the load-bearing citation; the Rauscher papers do not state the microscopic
form). Mass-excess conventions and eqs. (0.5)–(0.7): reproduce AME2020's own
B/A column to < 0.1 keV/A. ²⁸Si(α,γ)³²S chain: all four inputs match AME2020
(−21.4928, +2.4249, −26.0155), Q = 6.9477 ✓. Magic numbers: Otsuka et al.
2020. ⁵⁶Ni doubly magic, most-bound Z = N (checked against ⁴⁰Ca…⁶⁴Ge),
dominant NSE product at Yₑ = 0.5 (H&T96 verbatim). Hauser–Feshbach factor
1.5–2: RT2000 verbatim. REACLIB 7-coefficient/summed-sets: JINA docs.

**§0.4–0.5 neutrinos & REACLIB.** Four thermal channels: Kato et al. 2020
verbatim (Itoh et al. 1996 adds recombination, negligible). Pair dominance at
Si-burning conditions: Kato 2020, Odrzywolek et al. 2004, Patton et al. 2017.
σ₀ = 1.761×10⁻⁴⁴ cm², σ ∝ (E/m_ec²)²: Janka 2017 verbatim. λ arithmetic ✓;
trapping 10¹¹–10¹² g/cm³ and β-equilibration-if-trapped: Janka 2017 verbatim.
β⁻ counter-current: LMP RMP verbatim ("counteracts the reduction of Y_e").
⟨E_ν⟩ in tables: FFN (via LMP RMP), LMP 2001, Patton et al. 2017 eq. (aveE).
A(b,c)D: José & Iliadis 2011. REACLIB chapter forms 1–11 and ΔN: all rows
verified against the JINA format page. Phase-space factor per excess product:
pynucastro paper appendix (power r−p) — structure exact. gh-575: verified
against the fetched GitHub issue (title, scope, ~24-orders overestimate, fix
PR #632) and Grichener et al. 2025 App. B; config convention and row counts
(20 rows; 13 with |dN| = 1; ch-8 dlog10 ≈ 10.1–10.9) recounted exactly.

**§0.6–0.7 + I.1 topology & timescales.** α-ladder and ⁵⁶Ni endpoint: H&T96 +
BCF68 (via H&T96) + Timmes's aprox13 rung list. Two-cluster A ≃ 45 division
and ⁴⁵Sc(p,γ)⁴⁶Ti dominance: H&T96 quoting WAC73 verbatim ("this linkage was
dominated by a single reaction, ⁴⁵Sc(p,γ)⁴⁶Ti"). Category-count table: all 20
counts match `configs/reactions_mesa80_mesa.yaml` exactly (total 607; photo
151 largest). Energy-route identity: algebraically exact (residual 6.2×10⁻¹⁶
on the real ν); shipped q_mev vs −νᵀΔm ≤ 17.2 keV — bounds Q-table rounding
exactly as the text claims. Free-fall √(3π/32Gρ) = 0.0664 s at 10⁹ ✓.
Q ≲ 30 kT photodisintegration criterion: H&T96. Convective corners 10/10³ s ✓
(measured 3-D Si-shell point: v ≈ 10⁷ cm/s, τ ≈ 20 s — Couch et al. 2015).
Burning-stage table rows H/He/C/Ne/O: verified against WHW02 (via Pols Table
12.1 and Woosley's AY220 tables); "photodisintegration rearrangement" is
literally Woosley's phrase. Si+Si Z₁Z₂ = 196 ✓. Pair-ν T⁹ regime: Woosley
L11 ("P± = 4.6×10¹⁵ T₉⁹, T₉ > 3"). Neutrino-dominated from C ignition:
Limongi 2017. Timescale-table interior rows (charged captures, intra-group,
bridge, weak windows): order-of-magnitude, no literature point values —
treated as derive-yourself estimates, consistent with H&T 1999a/b
qualitative statements.

**§I.2–I.3 explodability & cost.** P = (3π²)^{1/3}ħc n_e^{4/3}/4: verbatim
prefactor in Suwa et al. 2018 appendix. Lane–Emden M₃ = 2.018236 (recomputed
by integration); M_ch/Yₑ² = 5.8237 → 1.4559/1.1793 M⊙, 19.0% ✓; Suwa's
M_Ch0 = 1.46 M⊙(Yₑ/0.5)² concurs. Thermal correction: origin Baron &
Cooperstein 1990 (doc's bracket is its first order; exact form
[1+(2/3)x²]^{3/2}). Fe photodissociation ≳ 7 GK: Janka 2012 (after B²FH);
⁵⁶Fe → 13α+4n = 124.416 MeV = 2.2217 MeV/nucleon from AME2020 ✓ . EC runaway:
Janka et al. 2007. t_coll ≈ 0.21/√ρ₈ s: Janka 2012. ξ_2.5 definition exact:
O'Connor & Ott 2011. Implicit necessity, 90+% matrix time, "doubly bordered
band diagonal" free-nucleon structure: H&T 1999b verbatim; hub fractions
recounted from the config (neut 40.7%, h1 40.5%, either 72.5%).

**§I.4–I.9.** Species diffs all exact against the isotope configs (six
mesa_80-only species; Z caps; neutron-rich lists; sc43 only). Accumulation
trichotomy (Nδ/√Nδ/δ(1−c)): derived and Monte-Carlo-checked. nε = 3.353×10⁻¹⁴
(1.47 decades under gate), float32 misses by 7.26 orders ✓. Soft-vs-hard
constraints: Beucler et al. 2021 (fetched) — monotonic trade-off in the
penalty weight; hard-constrained variant conserves to machine precision.
Projector derivation: verified line-by-line and numerically (CP, P²−P, P−Pᵀ
at 10⁻¹⁵; rank n+3−m; rank-deficient C → cond(CCᵀ) ~ 10¹⁶); QR-vs-normal-
equations conditioning: cond(CCᵀ) = cond(C)² verified numerically. asinh
counterexample: exact (ΣAu = −6.9078). Bipartite species/reaction precedent:
Kim et al. 2026 verbatim. NNN architecture claims: Grichener et al. 2025
(also noted: the NNN enforces ΣX = 1 via log-softmax — it is not
conservation-free, though it lacks charge/lepton closure).

**Parts III–IV.** Box edges and nine-dt grid: Grichener et al. 2025 verbatim.
D*_N and Koksma–Hlawka: Owen & Rudolf 2021 verbatim. i.i.d. LIL rate: Chung
1949 / Philipp (via Aistleitner et al.). Sobol XOR construction and direction
numbers: verified (Sobol' 1967; Bratley & Fox 1988; Joe & Kuo 2008).
(log N)^82/2²⁰ ≈ 10⁸⁸–10¹⁰¹ — "astronomically ≫ 1" ✓. Effective dimension:
Caflisch, Morokoff & Owen 1997. Owen scrambling unbiasedness and
N^{−3/2}(log N)^{(d−1)/2} RMSE: Owen 1997a,b/2008 via Owen 2022. Poisson
collision arithmetic exact (λ = 0.7439; 0.5247/0.2946; measured 0.148 = 0.50×
Poisson excess; 3.54× against the wrong formula). 0.684% missing ✓. Strang
orders: Strang 1968 / Blanes et al. 2008. Constant-(T,ρ) labels: Grichener et
al. 2025 verbatim; bbq one-zone: bbq README + defaults verbatim. Semigroup
property: standard (Encyclopedia of Mathematics). Rollout trichotomy: rederived;
Yₑ-no-restoring-force from strong-sector charge conservation: H&T 1999b.

**Part V.** Cancellation bound (V.1)–(V.2): derived, tight, Monte-Carlo-
checked; κ = 1/κ_sub of subtraction (Higham/Goldberg). Amplification table:
all cells ✓. A·ν = 0 exact on both exports; naive cond 1.54×10¹⁶/1.01×10¹⁶
reproduces the anecdote; one zero SV nuclei-only, three on extended ν̃
(recomputed; C·ν̃ = 0.0 exactly). h ≤ 2/|λ|: derived + Guidry et al. 2013
("precisely two over the fastest rate"). Machine epsilons, nε bounds, 7.26
orders ✓. Newton quadratic convergence, damping, bisection guarantees:
standard, verified via accessible sources. rtol/atol semantics, t_eval
interpolation, BDF Jacobian-reuse, Radau IIA order-5 L-stability: verified
against the installed SciPy source (`_ivp/ivp.py`, `bdf.py`, `radau.py`) and
Hairer & Wanner via secondary sources. Saha-exponent overshoot arithmetic
(≈187/MeV at kT = 0.345, Z = N = 28) ✓.

**Part VI.** DeepONet/FNO function-space characterization: fetched TeX
verbatim. MPNN eq. (VI.1) = Gilmer et al. 2017 eqs. verbatim; permutation-
invariant aggregators: Battaglia et al. 2018 verbatim. Sum-aggregation
expressivity: Xu et al. 2019 verbatim. Oversmoothing: Li, Han & Wu 2018
verbatim. MESA module list and weaklib precedence (LMP > Oda > FFN): Paxton
et al. 2011 verbatim + r23.05.1 source (machinery now inside `rates/`).
`.net` mechanism (isotopes only, links at runtime): `mesa_80.net` inspected —
supports "reaction count must be measured". bbq description and
`use_hydrostatic`/`times_from_file`: bbq repo verbatim. QSE-reduction and
Guidry prior-art paraphrases: H&T 1996/1999a,b and Guidry et al. 2013
(both papers fetched) verbatim. Half-lives 6.075 d/77.236 d: ENSDF.
Light-curve tail → M(⁵⁶Ni): Arnett 1982 (concept), Diehl et al. 2015.
Ni/Fe: Jerkstrand et al. 2015. ξ_2.5-explodability: O'Connor & Ott 2011.
SN 1987A: Hirata et al. 1987 (11 events), Bionta et al. 1987 (8 events),
total ν energy ~3–6×10⁵³ erg consistent with NS binding energy.

**Part VII.** Repo-internal working practice — no scholarly claims beyond
recaps of Part 0 (spot-checked: kT(T₉=3) = 0.2585 MeV ✓; EC threshold recap ✓).

---

## 3. Items that remain assumed / unverifiable (tagged in text where relevant)

- §0.7 timescale-table interior rows (charged-capture, intra-group, bridge,
  weak windows) — order-of-magnitude estimates, presented as derive-yourself;
  no literature point values fetched. Consistent with H&T 1999a/b qualitative
  statements.
- §V.3 fastest/slowest rate endpoints — now explicitly tagged assumed in the
  text, pending the self-check item 6 Jacobian measurement.
- §I.1 "runtime majority-holder" and §I.3 zones/timesteps — plausible,
  order-of-magnitude; the network-internal 90+% matrix-solve share is sourced
  (H&T 1999b) but the whole-code runtime share is not.
- Iron-core radius ~10³ km — order-of-magnitude consistent with review
  snippets (Burrows 2017 fetch was 403-blocked); λ/R conclusion robust to 2×.
- Shapiro & Teukolsky 1983 and several classic pre-arXiv papers (BCF68,
  WAC73, FFN, Chandrasekhar-era polytropes) were verified through fetched
  secondary quotations, not primary text — noted per-entry in References.
- Two soft attributions, flagged by the fidelity spot-check and left as-is:
  RT2000's "worse off stability" qualifier is an inference from the paper's
  discussion (the stated accuracy figure is only the 1.5–2); and the
  net-vs-sequence "one log factor sharper" contrast is standard Niederreiter —
  Owen 2022 states the net-side bound but not the explicit contrast. Diehl et
  al. 2015 is a Type Ia study; the decay-chain mechanism it is cited for is
  supernova-generic.

## 4. Follow-ups outside this document's scope (not applied)

1. **CLAUDE.md carries the same NuGNN gloss** ("the NuGNN signed-log failure
   mode") that correction #24 reworded here. The paper shows NuGNN *dropped*
   enforcement rather than projecting in log space. CLAUDE.md is project spec
   — flagged for the maintainer, not edited by this audit.
2. **Chapter-10 v-flag reverses** (correction #7): the three in-network ch-10
   REACLIB entries are v-flagged detailed-balance reverses of the ch-7
   forwards — the same channels whose MESA-side inverses the config already
   flags via its two chapter-7 rows. No new gap is implied; the residual
   question is only whether MESA's instantiated rate set ever loads the
   REACLIB v-entries directly (in which case the pf gate already refuses them
   at T₉ ≥ 3).
3. **`scripts/fetch_arxiv_source.py` bugs** (hit by four agents): legacy
   slash-ids fail for (a) bare-gzip single-file e-prints and (b) the PDF-only
   fallback — the `/` in the id is not sanitized when building the output
   filename. Two-line fix.
4. **Tier-1/S2 rate-form derivation** should be checked for the same
   duplicated-N_A slip corrected here (#18), since §II.4 defers the general
   derivation to S2.
5. Two reference records were verified only at bibliographic level and are
   worth a second look if ever cited hard: Jerkstrand et al. 2015 volume/page,
   and the exact publication venue of Müller et al. 2016 (not cited in the
   text; excluded from References).

## 5. Adversarial verification pass (Phase D)

Two independent verifiers ran after the corrections were applied:

- **Corrections re-check** — every one of the 44 logged corrections was
  re-verified against its cited source and the current file text, with a
  stale-string sweep. Result: 41/44 confirmed outright; 3 findings, all fixed
  in a second pass: (a) correction #7 reworded — the in-network ch-10 REACLIB
  entries are v-flagged reverses, not forwards (see the updated #7 row);
  (b) correction #22 reconciled with RESULTS.md's *measured* I→I projection
  (radius 2, diameter 4), which supersedes the naive halve-the-bipartite
  argument in both §VI.2 and §II.6; (c) one unqualified "one-way Yₑ ratchet"
  in the Part-0 intro table (line 133) brought in line with the qualified
  net-ratchet wording used everywhere else. Residual nits, noted but not
  edited: this log's #5 said "13 real ch-6 forwards" — it is 12 tabulated
  forwards plus one v-flagged entry; and WHW02's 15 M⊙ Si duration (18 d ≈
  1.6×10⁶ s) sits at the edge of the "~1 day–2 weeks / ~10⁵–10⁶ s" phrasing,
  covered by the tildes.
- **Citation fidelity spot-check** — 20 inline citations sampled across all
  parts, biased toward the highest-risk attributions: **20/20 OK**, all
  quoted fragments verbatim in the fetched sources, all numeric attributions
  exact. Two soft attributions noted in §3 above; two cache gaps (Diehl 2015,
  Farmer 2016) were filled after the check.
- **Mechanical consistency** — every inline author–year has a References
  entry and vice versa (acronym forms B²FH/FFN resolve to entries carrying
  the acronym); 156 `$$` delimiters balance; tables render (two flagged rows
  are pre-existing escaped-pipe cells).

## 6. Literature cache

`data/literature/` after this audit (all fetched as TeX source per project
convention; PDF-only items noted): 0707.3500, 0812.0377, 1001.2422,
1009.1622, 1010.5550, 1107.2234, 1109.3265, 1112.4716, 1112.4738, 1206.2503,
1409.0540, 1503.02199, 1506.03146, 1511.02820, 1605.01393, 1608.03274,
1702.08713, 1704.01212, 1706.01913, 1801.07606, 1801.08023, 1806.01261,
1808.02328, 1810.00826, 1810.02244, 1903.01426, 1904.08427, 1909.00912,
1910.03193, 2001.03978 (PDF-only), 2002.07859, 2006.02519, 2008.08051,
2010.08895, 2104.13478, 2208.03651, 2210.09965, 2306.17381, 2403.12942,
2503.00115, 2606.04491, astro-ph/{0004059, 0004317, 0011507,
0304047, 0311012, 0611009, 0612072, 0702176, 9510136 (PS-only), 9511088,
9807012, 9808203, 9906478}, nucl-th/{0001018, 0203071}. Removed as
mis-fetches or failed fetches: 1306.6141 (signal-processing paper, not
Nomoto et al. 2013); astro-ph/0201457 (wrong-id guess for WHW02, removed by
the fetching agent); astro-ph/0601261 (empty remnant of a failed PDF-only
fetch).
