# HOSTILE REFEREE AUDIT — "Weak-Interaction Physics and the Yₑ Accuracy Floor for a Conservation-by-Construction GNN Nucleosynthesis Emulator (Run 2 of 2)"

## VERDICT HEADLINE
**ACCEPT WITH CORRECTIONS.** After attempting to break the report, I found **zero hallucinated citations** — every load-bearing reference verified against primary sources (IOP, NASA ADS, arXiv, OSTI, A&A, ScienceDirect, Springer). The report's headline Yₑ floor and per-step error budget are **NOT wrong by an order of magnitude**, so the kill-test threshold is not corrupted. However, the floor-derivation reasoning contains (a) a genuine systematic-vs-statistical conflation, (b) a floor band shifted downward and inconsistent with its own cited anchor, and (c) several pieces of manufactured precision. These must be corrected before the numbers enter the evidence base, but they do not invalidate the go/no-go.

---

## (i) SEVERITY-TIERED FINDINGS

### FATAL
- **NONE.** No hallucinated source was found. No floor/budget number is wrong by an order of magnitude in a way that flips the go/no-go decision. The most suspicious citation candidates (GeValNet25, arXiv:2412.00650, the GXPF1J ApJ-2020 table, NuGNN) all verified as real and correctly attributed.

### MAJOR
1. **The synthesized floor band (3×10⁻³–1×10⁻²) is internally inconsistent with its own anchor.** The TL;DR correctly cites the FFN→LMP shift as ΔYₑ = 0.005–0.015 (verbatim from Heger et al. 2001 ApJ 560, 307 abstract: *"Values for the central electron mole number at the time of iron core collapse in the new models are typically larger, by delta Y_e = 0.005 to 0.015, than those of Woosley & Weaver 1995"*). Yet the synthesized floor is restated as 3×10⁻³–1×10⁻². The **lower bound 3×10⁻³ is below the sourced 5×10⁻³ and is unsourced**; the **upper bound 1×10⁻² truncates the literature's 1.5×10⁻²**. The band was compressed and shifted downward relative to its anchor. The direction is conservative-strict (it would reject a marginal emulator rather than pass it), but a downward-biased floor can over-kill a viable architecture and must be corrected.

2. **Systematic-vs-statistical conflation in the floor anchor.** The floor is anchored on the FFN→LMP table swap (ΔYₑ = 0.005–0.015), which is a **one-time historical SYSTEMATIC correction between two rate sets**, not a statistical uncertainty band. Using it as an "uncertainty floor" is defensible ONLY as a *sensitivity scale* ("weak-physics choices move central Yₑ at this magnitude") — NOT as a propagated error bar. The report blurs this distinction. The genuine residual uncertainty *within* modern shell-model (LMP/Suzuki/GXPF1J-class) rates is unquantified in the literature and is plausibly smaller than the full historical FFN→LMP jump.

3. **Endpoint/quantity mismatch in the synthesis (the studies are not like-for-like).** The four studies fused into one "floor" answer different questions at different evolutionary endpoints:
   - **Heger 2001** = weak-rate-SET comparison (FFN vs LMP) to onset of collapse — *the only like-for-like weak-physics anchor.*
   - **Fields 2018** = THERMONUCLEAR (strong) rates only, **weak rates held FIXED**, stops at **O-depletion** (not collapse).
   - **Sullivan 2016 / Pascal 2020 / Johnston 2022** = EC rates varied **DURING hydrodynamic collapse/infall**, not during presupernova burning.
   - **Farmer 2016** = **network size + mass resolution**, not weak rates.
   Presenting a single unified floor from these heterogeneous endpoints/quantities is a conflation that must be stated explicitly rather than flattened.

4. **Manufactured precision: the 5×10⁻³ "working point" and the per-step 3×10⁻⁶ target are the report's own inferences, not sourced values.** They are defensible engineering choices, but they must be **labeled as inference**, not presented as literature-derived.

### MINOR
5. **⁶⁰Co "EC rate dropped ~2 dex FFN→LMP" — the exact 2-dex figure is UNVERIFIED.** Heger et al. 2001 (arXiv:astro-ph/0011507, §4.3) confirms verbatim: *"By far the most important electron-capture rate in calculations that use the FFN rates is ⁶⁰Co(e⁻,ν)⁶⁰Fe. This dominates the evolution of Yₑ in the center of the star from silicon depletion onwards. This particular rate is greatly reduced in the new LMP rate set."* "Greatly reduced" is confirmed; the precise **~2 orders of magnitude** quantification is not corroborated by any accessible source and remains UNVERIFIED.
6. **Fields 2018 fine-grained Yₑ figures UNVERIFIED.** Paper, 127-isotope network, 665 sampled rates, 1000/2000 MC models, O-depletion endpoint, and weak-rates-held-FIXED are all CONFIRMED. The specific spreads (≲1% C-dep, ≲0.25% Ne-dep, central Yₑ ≈ 0.492/0.493 at O-dep, −2% negative tail, ¹⁶O(¹⁶O,n)³¹S Spearman rₛ ≈ −0.6) are buried in the paper body and were not independently verifiable from accessible secondary sources.
7. **η-reinterpretation of Farmer's 30% is the report's speculation — but handled honestly.** The report explicitly flagged it as "must be confirmed locally" and did NOT quietly assert it as established (good practice). Caveat: a literal ~30% *relative* variation in central Yₑ is plausible when comparing a grossly inadequate small network to a converged one, so the η reframe may be unnecessary. Confirm against Farmer's actual figures locally.
8. **MESA grid (11 ρYₑ points, 12 T points) and pynucastro TabularLibrary default precedence ["ffn","langanke","suzuki"] UNVERIFIED.** MESA shipping LMP(2001) > Oda(1994) > FFN(1985), plus Suzuki(2016), is confirmed; the exact grid-point counts and the pynucastro default ordering were not independently checked.
9. **Aufderheide 1994 "Table 25 / top ~90 EC nuclei for 0.40 ≤ Yₑ ≤ 0.50" — table number UNVERIFIED.** Paper, 5-author list (incl. Stanford), title ("Search for important weak interaction nuclei in presupernova evolution"), and ApJS 91, 389–417 are all CONFIRMED; the specific table number/count were not verified.

---

## (ii) CORRECTIONS TABLE

| Claim | Report's version | Verified version | Source |
|---|---|---|---|
| FFN four papers | ApJS 42 447 (1980); ApJS 48 279 (1982); ApJ 252 715 (1982); ApJ 293 1 (1985) | ALL CONFIRMED exactly, incl. effective-log(ft) in 1985 paper IV | ADS; Springer; Wikipedia (G. Fuller) |
| Oda 1994 | ADNDT 56, 231; A=17–39 sd USD; FFN grid | CONFIRMED; grid 10≤ρYₑ≤10¹¹, 0.01–30×10⁹ K (same as FFN) | OSTI 7140143 |
| LMP 2000/2001 | NuPhA 673,481 (2000); ADNDT 79,1 (2001); >100 nuclei A=45–65; ~1 dex smaller EC | CONFIRMED; "more than 100 nuclei A=45–65"; EC rates "smaller than the FFN rates by approximately one order of magnitude" | arXiv nucl-th/0001018; ScienceDirect S0092640X01908654; A&A aa14276-10 |
| Suzuki 2016 | ApJ 817,163; sd A=20,23,24,25,27 USDB; fine mesh | CONFIRMED title/venue/Hamiltonian/pairs | IOP 10.3847/0004-637X/817/2/163 |
| Heger table-swap | ΔYₑ = 0.005–0.015 | CONFIRMED verbatim (FFN→LMP vs Woosley & Weaver 1995) | ApJ 560,307; arXiv astro-ph/0011507 |
| LMP review value | "central values of Yₑ increased by 0.01–0.015" | CONFIRMED verbatim | arXiv:1008.2144 |
| **Synthesized floor** | **3×10⁻³–1×10⁻²** | **SHOULD BE 5×10⁻³–1.5×10⁻² (sourced); 3×10⁻³ lower bound unsourced; 1.5×10⁻² upper truncated** | Heger 2001 + 1008.2144 |
| ⁵⁵Co most important EC nucleus | Heger 2001, 25 M⊙ | CONFIRMED; pre-revision dYe/dt ≈50% from ⁵⁵Co, 25% from ⁵⁶Ni; with LMP rates ⁵⁶Ni becomes dominant and dYe/dt drops ~2× | scielo bjp; arXiv:2505.01024; nucl-th/9809081 |
| Sullivan 2016 | +16/−4% inner-core mass; ±20% peak νe-L; 5× the 32-progenitor study; N=50/Z=28 | CONFIRMED verbatim (all figures) | ApJ 816,44; arXiv:1508.07348 |
| Pascal 2020 | "individual EC rates most important source of uncertainty…others marginal" | CONFIRMED verbatim | PRC 101,015803; arXiv:1906.05114 |
| Johnston 2022 | arXiv:2202.09370, N=50 follow-up | CONFIRMED; 200 progenitors, 1D CCSN | arXiv:2202.09370 |
| Fields 2018 | ApJS 234,19; 1000 MC 15 M⊙; 665 rates; 127 iso; weak FIXED; O-dep | CONFIRMED (methodology/scope); fine Yₑ figures UNVERIFIED | arXiv:1712.06057; OSTI 1542031 |
| Farmer 2016 | ApJS 227,22; ≈30% central-Yₑ variation; ≥127 iso for ≈10% convergence | CONFIRMED verbatim quote | ApJS 227,22; arXiv:1611.01207 |
| ⁶⁰Co FFN→LMP | "~2 dex" | "greatly reduced"/"much smaller" CONFIRMED; exact 2-dex UNVERIFIED | ApJ 560,307; astro-ph/0011507 §4.3 |
| Patton/Lunardini/Farmer 2017 | ApJ 851,6 | CONFIRMED (arXiv:1709.01877; 204-isotope presupernova ν network) | IOP 10.3847/1538-4357/aa95c4 |
| GeValNet25 | A&A 2025, aa51816-24; adds ⁵³Fe,⁵⁵Fe,⁵⁵Co,⁵⁷Co | CONFIRMED — Griffiths et al. 2025, A&A 693, A93; arXiv:2408.03368; isotopes verbatim; **note lead author is Griffiths (not Sibony/Tsiatsiou)** | A&A aa51816-24 |
| GXPF1J table | Suzuki ApJ 2020 abbb32 | CONFIRMED — screening EC paper; GXPF1J, ρYₑ=10⁵–10¹¹ mol/cm³, T=10⁷–10¹¹ K | IOP 10.3847/1538-4357/abbb32 |
| arXiv:2412.00650 | FT-pnRQRPA EDF, 1652 nuclei | CONFIRMED (Ravlić, Giraud, Paar, Zegers; self-consistent EC+β) | arXiv:2412.00650 |
| arXiv:2508.05456 | sd Urca USDB 2025 | CONFIRMED (Sharma, Srivastava, Suzuki) | arXiv:2508.05456 |
| arXiv:2505.01024 | recent pn-QRPA ⁵⁵Co | CONFIRMED (expanded pn-QRPA EC on ⁵⁵Co) | arXiv:2505.01024 |
| NuGNN | arXiv:2606.04491, 3 Jun 2026; 690-iso XRB GNN; "few percent"; no hard conservation | CONFIRMED — Kim, Chae, Ko, Mumpower, Smith; abstract verbatim *"errors of only a few percent"*; no conservation-by-construction claimed | arXiv:2606.04491 |
| Grichener NNN | arXiv:2503.00115, ApJS 279,49 | CONFIRMED — authors/venue; **ApJS vol 279 page 49 now VERIFIED (Bibcode 2025ApJS..279...49G)**; Yₑ improvement 280–660% verbatim | arXiv:2503.00115; IOP ade717; ADS |
| PRL 86,1678 vs ApJ 560,307 | both exist | CONFIRMED DISTINCT companion papers: PRL = collapse-models Letter (author order Heger/Langanke/Martínez-Pinedo/Woosley, arXiv astro-ph/0007412); ApJ = long presupernova-evolution paper (Heger/Woosley/Martínez-Pinedo/Langanke, astro-ph/0011507). NOT the same result published twice — companion papers with different scope. | arXiv astro-ph/0007412 & 0011507 |

---

## (iii) QUESTION-BY-QUESTION COVERAGE GRADES
- **Tabulation comparison (FFN/Oda/LMP/Suzuki — grids, mass ranges, models):** ANSWERED-WITH-EVIDENCE.
- **Interpolation (effective log(ft)):** ANSWERED-WITH-EVIDENCE for FFN-1985 paper IV; the "bilinear in log T, log ρYₑ" implementation detail is ANSWERED-THINLY / UNVERIFIED.
- **How weak rates enter the ODEs / energy bookkeeping:** ANSWERED-THINLY (mechanism asserted; not deeply sourced in the audited text).
- **Ranked controllers (stage-by-stage nuclei):** ANSWERED-WITH-EVIDENCE for the Si-burning/pre-collapse controllers (⁵⁵Co, ⁵⁶Ni, ⁶⁰Co — all directly corroborated); ANSWERED-THINLY for the O-burning ³³S/³⁵Cl/³⁷Ar attribution (plausible, not verified to a specific table).
- **Table-swap Yₑ effects:** ANSWERED-WITH-EVIDENCE (the single best-sourced claim in the report; verbatim-confirmed twice).
- **Uncertainty-propagation studies:** ANSWERED-WITH-EVIDENCE, but with the endpoint/quantity mismatch (Finding #3) that the report does not flag.
- **Synthesized floor + per-step budget:** ANSWERED-WITH-EVIDENCE on the arithmetic; the floor band and working point contain inference mislabeled as synthesis (Findings #1, #4).
- **Network-truncation floor:** ANSWERED-WITH-EVIDENCE (Farmer verbatim quote correct); the η interpretation is honestly flagged as inference.
- **Novelty re-check:** ANSWERED-WITH-EVIDENCE for the *existence* of NuGNN and Grichener NNN. The narrower claim — "a conservation-by-construction GNN in the Si-burning/CCSN-progenitor regime is novel as of June 2026" — is PARTIALLY-VERIFIED: the two nearest neighbors (NuGNN = XRB regime, no hard conservation; Grichener NNN = late-burning MESA emulator, dense NN not GNN, no hard conservation) confirm no exact match exists among the works I reached, but my dedicated independent novelty sweep for "conservation-by-construction ML reaction-network surrogates" was cut off by search-budget exhaustion. Treat the novelty claim as well-supported but not exhaustively swept.

---

## (iv) MY OWN INDEPENDENTLY DEFENDED FLOOR AND PER-STEP BUDGET
*(This is the output feeding the real go/no-go threshold.)*

**Arithmetic re-derivation (done independently — confirms the report's table):**
- Systematic/linear δ = F/N, with F = 5×10⁻³: F/10³ = **5×10⁻⁶**; F/10⁴ = **5×10⁻⁷**. ✓
- Random-walk δ = F/√N: 5×10⁻³/31.62 = **1.58×10⁻⁴**; 5×10⁻³/100 = **5×10⁻⁵**. ✓
All four entries match the report exactly.

**Independent end-to-end Yₑ floor.** The ONLY quantified, like-for-like anchor for "how much does weak-interaction physics move presupernova central Yₑ" is the FFN→LMP shift: **ΔYₑ = 0.005–0.015** (Heger 2001, verbatim; independently corroborated by the Langanke–Martínez-Pinedo review at 0.010–0.015). I confirmed via a dedicated targeted search that **no published study propagates weak-rate uncertainties through the presupernova O/Si-burning phase to a central-Yₑ band** — the report's "literature gap" claim is **CORRECT**. (The closest item, Griffiths et al. 2025/GeValNet25, runs only a single deterministic "10× slower EC rate" sensitivity test, not a band.) Because the within-modern-rates residual uncertainty is unquantified and plausibly smaller than the full historical FFN→LMP jump, the FFN→LMP shift is best read as an **upper-bound sensitivity scale**, not a statistical floor.

I therefore defend the floor as:

> **ΔYₑ(floor) ≈ 5×10⁻³ to 1.5×10⁻² end-to-end per trajectory**, anchored directly on the sourced number.

I **reject the report's 3×10⁻³ lower bound as unsourced** and **restore the 1.5×10⁻² upper bound** the report truncated to 1×10⁻².

**Independent per-step budget.** For an autoregressive ML emulator, directional (systematic) bias is the realistic failure mode, so the conservative kill-test must assume **LINEAR accumulation**. Using F = 5×10⁻³–1.5×10⁻² over N = 10³–10⁴:
- **Linear:** per-step ≈ 5×10⁻⁷ (best case, large N, small F) to 1.5×10⁻⁵ (worst case, small N, large F) → a single defensible conservative target of **~10⁻⁶** (i.e., in the window 5×10⁻⁷–5×10⁻⁶).
- **Random-walk:** per-step ≈ 5×10⁻⁵ to ~4.7×10⁻⁴.

**Confirm or amend.** I **CONFIRM the report's core recommendation, with amendments.** The report's conservative per-step target of **|ΔYₑ| ≲ 3×10⁻⁶** sits squarely inside the defensible systematic-accumulation window (5×10⁻⁷–5×10⁻⁶) and is **sound to hand to the kill-test.** Its verdict — provisional 10⁻⁵–10⁻⁴ budget CONFIRMED under random-walk, and ≈1.3 orders too loose under systematic accumulation — is **arithmetically supported.** Amendments required: (1) use the sourced floor **F = 5×10⁻³–1.5×10⁻²** in the derivation (not 3×10⁻³–1×10⁻²); (2) treat 5×10⁻³ and 3×10⁻⁶ as **inference-labeled** working values. Most important single methodological recommendation: **the accumulation model (√N vs linear) must be measured empirically**, not assumed — test whether the emulator's per-step Yₑ error is zero-mean (random-walk) or biased (systematic) along a full trajectory. That choice alone moves the budget by ~1.5 orders of magnitude and is the largest lever on the pass/fail line.

---

## (v) OVERALL VERDICT
**ACCEPT WITH CORRECTIONS.**

Citation integrity is excellent: roughly 25 distinct references were checked and **none were hallucinated or materially misattributed.** The two highest-risk hallucination candidates flagged for extra suspicion — the post-2020 GeValNet25 A&A table and the GXPF1J ApJ-2020 reference — both verified as real, correctly cited, and saying what the report attributes to them. The PRL 86,1678 / ApJ 560,307 pair are confirmed as distinct companion papers, not a double-published single result. The kill-test threshold is **not** corrupted by an order of magnitude.

**Corrected content to fold into the evidence base:**
1. **Floor:** restate as **ΔYₑ ≈ 5×10⁻³ to 1.5×10⁻²** end-to-end; drop the unsourced 3×10⁻³ lower bound; restore the 1.5×10⁻² upper bound.
2. **Label the FFN→LMP shift as a systematic sensitivity scale**, not a statistical uncertainty band.
3. **Explicitly flag the endpoint/quantity mismatches** among Heger 2001 (collapse-onset, weak-set comparison), Fields 2018 (O-depletion, strong rates only, weak FIXED), Sullivan/Pascal/Johnston (during collapse), and Farmer 2016 (network/resolution).
4. **Label the 5×10⁻³ working point and the 3×10⁻⁶ per-step target as the report's own inference**, both of which I independently judge defensible.
5. **Make the √N-vs-linear accumulation choice an empirical measurement**, not an assumption; default to linear for the conservative kill-test.
6. **Carry forward as UNVERIFIED pending local confirmation:** ⁶⁰Co "~2 dex"; the Fields 2018 fine Yₑ figures (0.492/0.493, −2% tail, rₛ ≈ −0.6); the MESA 11×12 grid-point counts and pynucastro default precedence; the Aufderheide Table-25 number; and an exhaustive conservation-by-construction-GNN novelty sweep.

With these six corrections applied, the report's central deliverable — a per-step kill-test threshold of **|ΔYₑ| ≲ 3×10⁻⁶** under conservative (systematic) accumulation — stands and may proceed to the architecture bet.