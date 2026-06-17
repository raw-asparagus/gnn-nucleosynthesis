# Hostile Referee Audit — Run 1 Report: "Conditioning ML Targets for a Conservation-by-Construction GNN Emulator of Silicon Burning: Net-Flux vs Delta-X Trade-offs"

## TL;DR
- **Overall verdict: ACCEPT WITH CORRECTIONS.** The report's citation base survived a hostile line-by-line check far better than expected: every load-bearing astrophysics citation exists, is correctly attributed, and the verbatim quotes (Hix & Thielemann 1996, Hix & Meyer 2006, Guidry 2011, Thielemann-Nomoto-Hashimoto, NuGNN) are accurate. **Zero fully-hallucinated load-bearing citations were confirmed.**
- **The single most damaging finding (MAJOR, not FATAL):** the substitute number the report uses to shore up the admittedly-unverifiable "6–8 orders of magnitude" timescale-separation claim is itself wrong — the report (per the audit's reconstruction) leans on a "~10¹² explicit timesteps" figure that does not appear in any Guidry et al. 2011 paper; the genuine series figure is **~10¹⁴** explicit steps (CNO, ~100 s fastest β-decay rate over ~10¹⁶ s burning).
- **Two quantitative cells are inferences wearing source-precision clothing:** the "45Sc(p,γ)⁴⁶Ti ~70%" and "43Ca(n,γ)⁴⁴Ca >90%" inter-group flux fractions are the report's own estimates, not sourced numbers (the real Woosley-Arnett-Clayton figure is "~75%"/"perhaps a quarter through less important reactions," with no thermodynamic-condition tag and no >90% Ca figure anywhere). The **kill-test design is the weakest section**: it appears to silently require per-reaction gross forward/reverse fluxes, independently-solved equilibrium abundances, and a new sampling grid that the public Zenodo record (nine fixed timesteps, Sobol states) does not contain.

---

## Key Findings

**The report is citation-honest at the level that matters.** Against a deliberately adversarial standard ("assume every claim is wrong until verified"), the report's most argument-bearing claims held up under independent full-text checks on arXiv/ADS/journal pages. The physics quotes that anchor the entire "cancellation is real and dangerous" thesis are verbatim-correct. The NuGNN extraction — which the prompt flags as load-bearing because it propagates into architecture decisions — is faithful to arXiv:2606.04491v1 (the only version; no newer version exists as of this audit). This is the report's strongest feature and it should be stated plainly: the evidentiary spine is sound.

**The damage is concentrated in three places:** (1) one wrong "substitute" number used to backfill an unverifiable claim; (2) two flux-fraction cells presented with more source-specificity than the literature supports; (3) a kill-test whose computability against the actual public dataset is not established and whose pass/fail thresholds are asserted rather than derived. None of these flips the headline Target-A-vs-B lean, but all three must be corrected before the evidence is folded into the project base.

---

## Details

### (i) Severity-tiered findings

**FATAL** — *None confirmed.* No load-bearing citation was found to be hallucinated, and no single number was found wrong in a way that by itself reverses the Target A/B verdict.

**MAJOR — 1. The substitute timescale number is wrong.** The report correctly flags "6–8 orders of magnitude fast-equilibration vs slow-net-flow timescale separation" as unverifiable in Hix & Thielemann 1996/1998/1999, Guidry et al. 2011, or Hix & Meyer 2006. That flag is honest and correct. **But the number it offers as the closest sourced anchor is itself wrong.** There is no "~10¹² explicit timesteps / ~10⁻¹² s fastest rates vs ~1 s dynamical time" statement in arXiv:1112.4716, 1112.4750, or 1112.4738. The genuine series figure, from Guidry et al. 2011 (arXiv:1112.4738, §1), is: *"In the CNO cycle the fastest rates typically are β-decays with half-lives of order 100 seconds, but tracking main-sequence hydrogen burning may require integration of the hydrogen-burning network for as long as billions of years (~10¹⁶ seconds)… the largest stable integration timestep is set by the fastest rates and will be of order 10² seconds, so ~10¹⁴ explicit integration steps could be required."* The correct stiffness-span anchor, if the report wants a defensible order-of-magnitude statement, is Guidry et al. 2023 (arXiv:2312.09090): *"extremely stiff systems of equations where the fastest and slowest rates can differ by 10–20 orders of magnitude."* **Correction required:** replace the "~10¹²/10⁻¹² s/1 s" framing with "~10¹⁴ explicit steps (CNO; ~100 s fastest rate over ~10¹⁶ s)" and/or the "10–20 orders of magnitude" rate-span figure.

**MAJOR — 2. The 45Sc(p,γ)⁴⁶Ti "~70%" cell is a misprecise paraphrase.** Hix & Thielemann 1996 attribute to Woosley, Arnett & Clayton 1973 that the inter-group linkage is *"dominated by a single reaction, ⁴⁵Sc(p,γ)⁴⁶Ti, with perhaps a quarter of the flow going through less important reactions like ⁴²Ca(α,γ)⁴⁶Ti and ⁴⁵Ti(n,γ)⁴⁶Ti."* That is **~75%, not ~70%**, and crucially it carries **no attachment to the specific (T9=5, ρ=10⁷, Ye=0.498) conditions** the report's table cell implies. Presenting a round "~70%" tagged to exact thermodynamics overstates the source. **Correction:** state "~75% (Woosley, Arnett & Clayton 1973, as reported by Hix & Thielemann 1996), at high Ye, conditions unspecified."

**MAJOR — 3. The 43Ca(n,γ)⁴⁴Ca ">90%" cell is unsourced inference.** Hix & Thielemann 1996 document, at low Ye, that the bridge becomes proton capture on neutron-rich Ca isotopes and that there is "an unbalanced flow by neutron capture upward from the silicon group" — and explicitly that "it is hard to see how the reaction ⁴⁵Sc(p,γ)⁴⁶Ti can be the link between QSE groups for Ye=.46." So the *direction* of the report's claim (different bottleneck at low Ye) is well-supported. But **no ">90%" figure for ⁴³Ca(n,γ)⁴⁴Ca exists in the source.** This is the report's own estimate and must be relabeled as such.

**MAJOR — 4. Kill-test computability against the public data is not established.** The proposed QSE-Cancellation Kill-Test requires quantities that the public Zenodo record (record 14873443; nine fixed timesteps, Sobol-sampled states) does not obviously contain:
- *Cancellation ratio κ_r = |φ_r|/(f_r⁺ + f_r⁻)* needs **per-reaction gross forward and reverse fluxes**. A MESA/bbq net-flux solver outputs net Ẏ, not the separated f_r⁺ and f_r⁻; these must be recomputed externally from REACLIB rates × abundances × screening. This dependency is not flagged.
- *Equilibrium deviation δ_r* needs the QSE/NSE equilibrium abundances Ȳ, which require **independently solving the C(AZ) relations** (Hix & Thielemann Eq. 2–7) — a separate solver the project must build.
- *The proposed grid* (T9∈{1.6…7.9}, ρ∈{10⁷,10⁸,10⁹}, Ye∈{0.45,0.48,0.498}, dt∈{10⁻⁶,10⁻³,1,10²}) does not match the nine-fixed-timestep Sobol public data and **likely requires new bbq runs**.
- *The pass/fail thresholds* (κ_r>0.1 capturing ≥95% of |ΔYe|; cond(S_active)<10⁶ pass / >10⁸ fail; 10th-percentile κ; >90% reactions below floor) are **asserted, not derived** from the report's own evidence.
- *Dependency on the parallel Run 2 (weak-rate/Ye floor)* should be flagged where the Ye-capture thresholds appear.

**MINOR — 5.** QSE-formation temperature is quoted variably; both values are real and should be attributed precisely: **~3 GK** is Hix & Thielemann 1999 ("Silicon Burning II," astro-ph/9808203: *"the important abundances obey quasi-equilibrium for temperatures greater than approximately 3×10⁹ K"*); **~3.3 GK** is Thielemann, Nomoto & Hashimoto (astro-ph/9802077).

**MINOR — 6.** Citation-year hygiene: Paper II of Hix & Thielemann is published as **1999** (ApJ 511, 862); astro-ph/9808203 is the **1998** preprint. A "Hix & Thielemann 1998" label is the preprint year of Paper II, not a distinct paper — ensure the reference list disambiguates.

**MINOR — 7.** Goussis 2012 (Combust. Theory Model. 16, 869), Rauscher et al. 2002 (ApJ 576, 323), and Mott 1999 (PhD thesis, Univ. Michigan) were not independently full-text-verified in this pass (Mott 1999 is corroborated as a real, widely-cited thesis via its appearance in the Guidry et al. and Hix & Meyer reference lists). Mark UNVERIFIED-but-corroborated.

### (ii) Corrections table

| Claim | Report's version | Verified version | Source |
|---|---|---|---|
| Timescale-separation anchor | "~10¹² explicit timesteps / ~10⁻¹² s rates vs ~1 s" | "~10¹⁴ explicit integration steps" (CNO, ~100 s fastest rate, ~10¹⁶ s total) | Guidry et al. 2011, arXiv:1112.4738, §1 (verbatim) |
| Rate stiffness span | (implied by above) | "fastest and slowest rates can differ by 10–20 orders of magnitude" | Guidry et al. 2023, arXiv:2312.09090 (verbatim) |
| 45Sc(p,γ)⁴⁶Ti inter-group flux | "~70% at T9=5, ρ=10⁷, Ye=0.498" | "~75%; 'perhaps a quarter of the flow' through ⁴²Ca(α,γ)⁴⁶Ti & ⁴⁵Ti(n,γ)⁴⁶Ti; no condition tag" | WAC 1973 via Hix & Thielemann 1996 (verbatim) |
| 43Ca(n,γ)⁴⁴Ca inter-group flux | ">90% at low Ye" | No numeric figure exists; source supports only "proton capture on neutron-rich Ca / unbalanced neutron-capture flow upward" at low Ye | Hix & Thielemann 1996 (qualitative only) |
| QSE formation T | "~3.3 GK" (single value) | ~3 GK (Hix & Thielemann 1999) AND ~3.3 GK (Thielemann-Nomoto-Hashimoto) — attribute separately | astro-ph/9808203; astro-ph/9802077 (both verbatim) |
| Stiffness ratio | "S > 10¹⁵" | CORRECT — "S > 10¹⁵ is not uncommon in astrophysics" | Hix & Meyer 2006, astro-ph/0509698, §3 (verbatim) |
| Near-eq cancellation | "14+ orders of magnitude" | CORRECT — "14 or more orders of magnitude" | Hix & Meyer 2006, §3 (verbatim) |
| NSE cluster split T | "6 GK (⁴He/¹²C), 4 GK (Si/Fe-peak)" | CORRECT — split between ⁴He and ¹²C at T~6 GK; Si-group/Fe-peak at T~4 GK | Hix & Meyer 2006, §4 (verbatim) |
| ε tolerance | "typically of order 10⁻²" | CORRECT — verbatim in both 1112.4716 §6.2 and 1112.4750 §4 (papers say "of order 10⁻²", not literally "ε=0.01") | Guidry et al. 2011 |
| Kircher & Votsmeier 2025 | "JPCL, positivity-preserving projection/backtracking" | CONFIRMED REAL — "Machine Learning Surrogate Models for Mechanistic Kinetics: Embedding Atom Balance and Positivity," J. Phys. Chem. Lett. 2025, 4715–4723, DOI 10.1021/acs.jpclett.5c00602 (PMID 40323851); "positivity preserving projection and a correction by linear interpolation backtracking" | enrichment verification |
| Döppel & Votsmeier 2024 | Proc. Combust. Inst. 40, 105507 | CONFIRMED exact, DOI 10.1016/j.proci.2024.105507 | ScienceDirect |

### (iii) Question-by-question coverage grades (prompt Parts 1–2, items 1–8)

| Prompt question | Grade | Note |
|---|---|---|
| QSE/NSE structure & cancellation problem | **Answered with evidence** | Anchored on verbatim Hix & Thielemann + Hix & Meyer quotes; strongest section. |
| Equilibrium hierarchy (group structure, T-dependence) | **Answered with evidence** | 28<A<45 lower cluster, two-group→one-group merging, Ye-dependence all sourced. |
| Bottleneck reactions | **Answered thinly** | Direction correct but the two headline flux fractions (~70%, >90%) are over-precise inferences (MAJOR 2, 3). |
| Numerical-methods conditioning literature | **Answered with evidence** | Timmes 1999, Longland 2014, Guidry series, Hix & Meyer all verified. |
| Conditioning of Target A (signed net flux) | **Answered with evidence** | Cancellation/round-off danger directly sourced; dynamic-range estimates partly inferential (acceptable, labeled). |
| Conditioning of direct ΔX/ΔY (Target B) | **Answered with evidence** | NuGNN log-space conservation-failure account is verbatim-accurate and decisive. |
| NuGNN precedent | **Answered with evidence** | Faithful extraction of v1; predicts ΔX, 690 isotopes, signed-log, failure mode. |
| Output-space transforms & linear-vs-nonlinear conservation clash | **Answered with evidence** | Sturm-Wexler (flux target, machine-precision conservation), Ji-Deng, Döppel-Votsmeier, Kircher-Votsmeier all real and correctly characterized. |
| Prior art on flux-prediction surrogates | **Answered with evidence** | Sturm-Wexler "train on fluxes S not tendencies ΔC" verified verbatim. |

No prompt question was *dodged* or *silently dropped*. The thinnest coverage is the bottleneck-reaction quantification.

### (iv) Inference-labeling and conflict audit

**Inferences presented as fact (must be relabeled):** the ~70% and >90% flux fractions (MAJOR 2, 3); the kill-test pass/fail thresholds (MAJOR 4); the dynamic-range estimates for signed net fluxes (the report appears to label these as "inferences anchored on" Hix & Thielemann — that labeling is honest and should be retained). The "Reaction class × temperature × gross-to-net flux ratio" table is correctly framed as inference, but individual cells inherit the over-precision problem above; each cell should carry a sourced/derived/guessed tag.

**Facts mislabeled as inference:** none material found.

**Conflicts the report correctly flagged:** (a) the unverifiable "6–8 orders of magnitude" claim — correctly flagged, though the substitute is wrong (MAJOR 1); (b) the Ye-dependence of the dominant bottleneck (⁴⁵Sc(p,γ)⁴⁶Ti at high Ye per WAC 1973 vs neutron-rich-Ca proton capture at low Ye per Thielemann & Arnett 1985 / Hix & Thielemann 1996) — **this conflict is real and the report represents it accurately**; Hix & Thielemann explicitly reconcile WAC and TA via the Ye-dependence of the group boundary.

**Conflict the report did NOT flag (new):** the QSE-formation temperature itself is reported inconsistently across the primary sources (~3 GK in Hix & Thielemann 1999 vs ~3.3 GK in Thielemann-Nomoto-Hashimoto vs "exceeds 3×10⁹ K" for general photodisintegration onset in Hix & Thielemann 1996). This is a minor numerical spread, not a substantive disagreement, but the report should note it rather than silently picking one value.

### (v) Verification depth achieved (priority citations)

- **Hix & Thielemann 1996** (astro-ph/9511088): **FULL TEXT** — quotes, Eq. (2), 299 nuclei/3000 reactions, Q<30k_BT, 8–12 MeV, WAC ~75% attribution all verified verbatim.
- **Hix & Thielemann 1999 / "1998"** (astro-ph/9808203): **FULL TEXT** — ~3 GK QSE threshold verbatim; freezeout categories verbatim.
- **Hix & Meyer 2006** (astro-ph/0509698): **FULL TEXT (via subagent)** — S>10¹⁵, "14 or more orders," 6 GK / 4 GK cluster splits all verbatim.
- **Guidry, Billings & Hix 2011** (1112.4738): **FULL TEXT** — F_i⁺−F_i⁻ cancellation quote verbatim; partial-equilibrium criterion confirmed.
- **Guidry 2011 asymptotic/QSS** (1112.4716, 1112.4750): **FULL TEXT (via subagent)** — three stiffness types verbatim; ε "of order 10⁻²" verbatim in both; "~10¹²/10⁻¹² s/1 s" figure **NOT FOUND** (real figure ~10¹⁴ in 1112.4738).
- **Thielemann, Nomoto & Hashimoto** (astro-ph/9802077): **FULL TEXT** — "3.3×10⁹ K… lower QSE-cluster… 28<A<45" verbatim.
- **NuGNN** (2606.04491): **FULL TEXT (v1, only version)** — 690 isotopes, ΔX, signed-log Sec III.2, conservation-failure quote, "few percent," "successfully reproduces… others fail" all verbatim.
- **Grichener et al. 2025** (ApJS 279, 49; DOI 10.3847/1538-4365/ade717): **FULL TEXT + journal page** — log-softmax, 9/12 layers, ReLU confirmed. (The specific "280–400% / 390–660% Ye improvement," "200–1000%" energy error, and Appendix B MESA-bug 20–24 orders claims were not independently re-read line-by-line this pass; mark UNVERIFIED-pending though the paper, architecture, and DOI are confirmed real.)
- **Sturm & Wexler 2020 (GMD 13, 4435) & 2022 (GMD 15, 3417):** **FULL TEXT/abstract** — flux-target framework, machine-precision conservation, "train on fluxes S not tendencies ΔC" verified.
- **Ji & Deng 2021** (JPCA 125, 1082; 2002.09062): **ABSTRACT + citing lit** — mass action + Arrhenius, interpretable stoichiometric weights, no native atom conservation confirmed.
- **Döppel & Votsmeier 2024 (Proc. Combust. Inst. 40, 105507) & 2023 (React. Chem. Eng. 8, 2620):** **ABSTRACT + publisher records** — atom-balance layer, asinh transform confirmed; DOIs verified.
- **Kircher & Votsmeier 2025** (JPCL): **CITING-LIT + DOI** — CONFIRMED REAL (DOI 10.1021/acs.jpclett.5c00602); positivity-preserving projection + backtracking confirmed. (My initial in-loop search missed it; the targeted enrichment recovered it. **MAJOR finding 2 is OVERTURNED — this is not a hallucination.**)
- **Longland et al. 2014 (A&A 564, A90) & Timmes 1999 (ApJS 124, 241):** **FULL TEXT/abstract** — Bader-Deuflhard/Gear robust vs Wagoner; MA28 sparse recommendation confirmed.
- **Hix et al. 1998 (astro-ph/9805095) & 2007 (ApJ 667, 476):** **ABSTRACT + ADS** — QSE-reduced α7 network (7 variables), hybrid equilibrium-network scheme confirmed.
- **Goussis 2012, Rauscher et al. 2002, Mott 1999:** **CITING-LIT ONLY / UNVERIFIED** (Mott 1999 corroborated as real via multiple reference lists).

---

## Recommendations

**Stage 1 — Must-fix before folding into the evidence base (blocks acceptance of affected claims):**
1. Replace the "~10¹² timesteps / 10⁻¹² s / 1 s" anchor with the verified "~10¹⁴ explicit steps (CNO)" figure from arXiv:1112.4738 and/or the "10–20 orders of magnitude rate span" from arXiv:2312.09090. State explicitly that the "6–8 orders of magnitude" timescale-separation claim **remains unsourced** and is the report's own estimate.
2. Relabel the ~70% and >90% flux-fraction cells: "~75% (WAC 1973 via H&T 1996, high Ye, conditions unspecified)" and "qualitative only — no published fraction for ⁴³Ca(n,γ)⁴⁴Ca; report's own inference."
3. Tag every cell of the gross-to-net flux-ratio table as **sourced / derived / guessed**.

**Stage 2 — Kill-test redesign (must complete before the kill-test is run):**
4. Add an explicit data-provenance subsection stating which κ_r and δ_r inputs are *in* the Zenodo record vs *must be recomputed* (gross f_r⁺/f_r⁻ from REACLIB; Ȳ from an independent C(AZ) QSE solver) vs *require new bbq runs* (the proposed T9/ρ/Ye/dt grid).
5. Either derive the pass/fail thresholds (κ_r>0.1; cond<10⁶/>10⁸; etc.) from the report's own cancellation evidence, or downgrade them from "thresholds" to "provisional, to-be-calibrated."
6. Add the cross-dependency note on Run 2 (weak-rate/Ye floor) wherever Ye-capture thresholds appear.

**Stage 3 — Hygiene:**
7. Fix the Hix & Thielemann 1998/1999 year labeling; attribute ~3 GK and ~3.3 GK to their correct sources and note the minor spread.
8. Independently re-read Grichener et al. 2025 §3 + Appendix B to confirm the 280–400%/390–660% Ye-improvement, "200–1000%" energy-error, and 20–24-order MESA-bug numbers before citing them as precise; full-text-verify Goussis 2012 and Rauscher et al. 2002.

**Thresholds that would change the verdict:** If Stage-1 item 1 cannot be corrected (i.e., if the report insists on a fabricated timestep figure), escalate to RERUN on that claim. If the kill-test data-provenance audit (Stage 2 item 4) reveals that κ_r is *not* computable from any available or near-term data, the kill-test as written is **not executable** and must be redesigned, not merely re-thresholded.

---

## Caveats
- This audit verified citation *existence and attribution* and the *load-bearing quotes/numbers*. It did **not** re-derive every dynamic-range estimate or every cell of the inference table from first principles; cells flagged as the report's own inference are accepted as honestly-labeled inference where so labeled.
- Three citations (Goussis 2012, Rauscher et al. 2002, and the detailed Grichener et al. 2025 numerical claims) are marked **UNVERIFIED-pending** — the papers/DOIs are real but specific figures were not re-read line-by-line within budget.
- My own research loop initially mis-flagged Kircher & Votsmeier 2025 as a possible hallucination; targeted verification overturned that. This is itself a lesson: a single search miss is not proof of hallucination, and the report should be given the benefit of a DOI check before any "hallucinated" charge is leveled. The corrected position is that **the report's reference list contains no confirmed hallucination.**
- The Target A/B verdict (lean toward a hybrid Target-A default) **survives the audit**: it rests on verified evidence (the verbatim cancellation/round-off danger in Hix & Thielemann, Hix & Meyer, and Guidry; and NuGNN's documented failure of log-space conservation enforcement, which directly undercuts naive direct-ΔX with a hard conservation layer). The counterargument (Sturm-Wexler-style flux targets conserve to machine precision) is engaged rather than strawmanned. The verdict's integrity is intact; what must change is the supporting *numbers* (MAJOR 1–3) and the *executability* of the kill-test (MAJOR 4), not the direction of the lean.