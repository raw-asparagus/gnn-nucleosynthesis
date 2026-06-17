# RUN 3 of 3 — Components C (Variable-dt Temporal Head) + D (Rollout Stability + Training Recipe)
## Conservation-by-Construction GNN Emulator of the Silicon-Burning Network

---

## 1. EXECUTIVE SUMMARY (headline decisions, one line each)

- **C1 — Temporal head (PARALLEL-WITH-KILL-TEST):** Ship **dt-as-global-input-feature on a stiffness-aware logarithmic-dt grid** as the v1 interim; design the latent neural-ODE (MACE pattern) as the v2 upgrade only behind a measured stability win. *Switch to latent NODE only if log-dt-grid rollout drift exceeds the per-step Ye gate at dt ≥ 0.1 s.*
- **C2 — Conservation-in-latent (A/B-DEPENDENT):** Keep ALL conservation structure in the **decode step**, never in the latent dynamics; the latent ODE/operator is unconstrained and the Run-2 head (stoichiometric map for A, null-space projection for B) is applied AFTER decode. *Reject any latent-space soft conservation loss — MACE found it requires computing the decoder Jacobian every training pass and "slowed down the training immensely."*
- **C3 — Iterative instability (PARALLEL):** A continuous-time formulation does NOT automatically help; van de Bor et al. 2025 showed a DeepONet emulator diverges under iteration. Adopt **Ono & Sugimura's (2026) timescale-based rescaled-update** as the rollout governor.
- **D1 — Noise-injection transfer (HYPOTHESIS, not remedy):** GNS-style random-walk noise injection is **NOT safe to import unmodified** near QSE; injecting noise into a near-equilibrated abundance can push it off the QSE manifold where stiff dynamics amplify it. Use **pushforward/unrolled training (backprop through K steps)** as the primary stability lever, noise only on non-equilibrium channels.
- **D2 — Accumulation model (THE pass/fail lever; HAND TO PHASE 0):** Measure zero-mean-vs-biased per-step Ye residual with a cumulative-sum drift test + slope regression of cumulative |dYe| vs N (slope≈1 ⇒ systematic/F/N gate; slope≈0.5 ⇒ random-walk/F/√N gate). Push residuals toward zero-mean via signed/symmetric loss + conservation structure + ensemble averaging.
- **D3 — Loss + UQ:** Use **signed-log (asinh) MAE** as base, ADD a **quantile/worst-case tail term** (the NNN weak point was per-isotope tails reported as means), and **up-weight Fe-peak A=45–65 LMP nuclei**. UQ = **deep ensemble on the flux head** feeding an OOD flag → fallback-to-solver gate. Biggest single risk: **Sobol→real-MESA-track error-transfer failure.**

**Single biggest risk in the proposed design:** the accumulation model is unmeasured; if Ye residuals are even weakly biased (systematic), the per-step gate tightens from ~5e-5 to 5e-7 at N=1e4 — a 100× harder target that no surveyed emulator has demonstrated for a controlled scalar like Ye.

---

## 2. BODY — survey → analysis → DECISION + threshold

### 2.1 Component C — the variable-dt temporal head

**Problem framing (inherited).** The baseline NNN (Grichener et al. 2025, ApJS 279, 49 — published, verified; arXiv:2503.00115) spans 1e-6–100 s using **nine per-timestep models with runtime interpolation between the two nearest** [SOURCED]. As characterized by Yao et al. 2025, Grichener et al. "employed neural networks to replace the reaction network solver for approximately 100 isotopes in a zero-dimensional case, achieving errors of no more than 1% per time step" (for 80- and 151-isotope networks, with T/ρ training ranges spanning ~1–2 orders of magnitude) [SOURCED]. The goal is to span that 8-decade range with ONE model. Three candidate approaches:

**(i) dt as a global input feature.** This is the NuGNN approach (Kim et al. 2026, arXiv:2606.04491 — preprint, verified; 690-isotope Type I X-ray burst network, heterogeneous isotope/reaction graph, signed-log MAE loss, retry-with-smaller-dt heuristic, "errors of only a few percent," reproduces final abundance patterns in-solver where Res-U-Net and FCN fail) [SOURCED]. Simplest to implement; composes trivially with the Run-1 graph backbone and Run-2 head; dt enters as a conditioning scalar on nodes/globals.

**(ii) Latent neural ODE on the GNN encoding (MACE pattern).** MACE (Maes et al. 2024, ApJ 969:79 — published, verified; arXiv:2405.03274) uses an autoencoder + latent ODE solved with torchode, achieving "a mean speedup of factor 26 (factor 24 for low-density and factor 28 for high-density outflows)" with sub-linear scaling in the number of hydro particles [SOURCED]. Crucially, MACE reports that implementing a **soft element-conservation loss "slowed down the training immensely, because, for every pass of training data through mace, the jacobian of the decoder neural network needs to be calculated and multiplied by the tensor coefficients of the latent ODE, which involves many operations on large matrices"** [SOURCED — verbatim]. This is the central warning for conservation-in-latent.

**(iii) Operator head (DeepONet/FNO with dt as trunk input).** Goswami et al. 2023 (CMAME 419:116674 — published, verified; arXiv:2302.12645) learns the solution propagator for stiff kinetics with DeepONet + PoU-DeepONet extensions (ROBER 3-species, POLLU 25-species, syngas 11-species/21-reaction) [SOURCED]. AMORE (Nath et al., arXiv:2510.12999 — preprint, verified; Oct 2025) is the mass-conserving adaptive multi-output operator: it designs the trunk to "automatically satisfy Partition of Unity" and enforces the unity mass-fraction constraint exactly via "an invertible analytical map that transforms the n-dimensional species mass-fraction vector into an (n−1)-dimensional space" [SOURCED]. This is structurally the same idea as the Run-2 null-space projection for Target B. Sulzer & Buck 2023 (arXiv:2312.06015; 29 species/224 reactions) is the cost-benchmark: their "neural ODE model achieves a speed-up factor of 55" over solve_ivp, and the linear-latent alternative reaches "a factor of 4270" — the strongest evidence that a cheap analytically-integrable latent dynamic can dramatically outpace a full neural-ODE [SOURCED].

**Iterative instability of continuous-time/operator emulators.** van de Bor et al. 2025 ("Bridging Machine Learning and Cosmological Simulations," arXiv:2503.10736; The Open Journal of Astrophysics — published, verified) found the Branca & Pallottini 2024 (A&A 684, A203 — published, verified; "achieves a speed-up of a factor of 128× with respect to stiff ODE solvers") DeepONet emulator is "prone to instability due to the accumulation of prediction errors" under iteration [SOURCED]. So a continuous-time formulation is NOT a free stability win.

**The decisive recent result (subagent-verified).** Ono & Sugimura 2026 (ApJ 996, 9; DOI 10.3847/1538-4357/ae1ca9 — PUBLISHED, verified; arXiv:2508.16114, submitted Aug 2025) diagnose exactly the QSE-relevant failure and fix it. Mechanism, verbatim: *"If the timestep is very short, the physical change over that step can be smaller than the prediction error. In such a case, the time variation is dominated by the error rather than by the physical evolution, and iterating such updates drives the solution away from the physical one."* [SOURCED]. Their **timescale-based method** defines a characteristic timescale τ_ε at which a variable changes by fraction ε (they use ε=0.1), and updates:

> Δx(Δt) = (Δt/τ_ε)·Δx_pred(τ_ε)  when Δt < τ_ε; else Δx_pred(Δt)

i.e., when the requested step is too short (error-dominated), it **rescales a reliable longer-step prediction down** rather than trusting the short-step prediction [SOURCED]. They cap τ_ε at the max learned timestep (NNs are unreliable outside the learned region), enforce conservation (hydrogen-nucleus + charge neutrality) after each update, and remain accurate "even with many iterations at a timestep as short as 10⁻⁴ of the free-fall time," whereas simple iteration drifts (a 300 K constant-reference test drifted to 600 K, "twice the constant reference value") [SOURCED]. The model uses 5 density subregions with separate DeepONets per variable, tracks 6 primordial species, and achieves "relative errors below 10% in over 90% of cases." They explicitly note noise injection (Holdship 2021) and train-the-update (Maes 2024) "are known to increase one-step prediction errors," whereas their method keeps one-step error low [SOURCED].

**DECISION C1 (PARALLEL):** v1 = **dt-as-global-input-feature on a stiffness-aware log-dt grid** (the NuGNN-proven, lowest-risk choice that composes cleanly with Runs 1/2). Defer latent NODE/operator to v2. **Threshold to upgrade to latent NODE:** if, on a constant-(T,ρ) 1000-step rollout, the log-dt-grid head's per-step |dYe| residual exceeds the accuracy gate (~3e-6) at any dt in [1e-6, 1e2] s while a latent-NODE prototype demonstrably holds it, switch. **Threshold to reject operator head:** if the AMORE-style trunk cannot be made compatible with the bipartite isotope/reaction graph node structure from Run 1 without flattening it (which would discard the inductive bias that made NuGNN beat the FCN).

**DECISION C2 (A/B-DEPENDENT):** Conservation lives in DECODE, never latent. For **Target A**, the latent head emits the signed net per-reaction flux φ; decode maps dY = ν·φ through the fixed stoichiometric matrix (conserves exactly since Σ A_i ν_ij = 0). For **Target B**, decode applies the fixed null-space projection onto {Σ A_i dY_i = 0, Σ Z_i dY_i = 0} in LINEAR space. **Falsifiable rule:** reject any architecture that requires the decoder Jacobian inside the training loop (the MACE failure); if conservation cannot be made exact by a fixed linear decode layer, do not adopt that latent formulation.

**DECISION C3 (PARALLEL):** Adopt Ono & Sugimura's timescale-based rescaled-update as the rollout governor on top of whichever temporal head wins, REPLACING NuGNN's cruder retry-with-smaller-dt heuristic. **Threshold:** keep the retry heuristic as fallback only if the timescale-based update fails the constant-(T,ρ) drift test.

### 2.2 Component D — rollout stability + training recipe

**The core transfer question (HYPOTHESIS).** Does "noise injection + conservation defeats autoregressive divergence" transfer from non-stiff particle dynamics to a stiff system near QSE? The non-stiff evidence is strong: GNS (Sanchez-Gonzalez et al. 2020, ICML) introduced random-walk noise injection so the model "learns to deal with accumulating noise leading to a distribution shift during longer rollouts" [SOURCED]; MeshGraphNets (Pfaff et al. 2020, ICLR 2021) generalized it; Dynami-CAL GraphNet (Sharma & Fink, Nature Communications 17:1045, 2026 — published, verified; arXiv:2501.07373) "delivers highly accurate predictions over 16000-rollout steps" via pairwise momentum conservation in edge-local frames, where "the GNS baseline violates conservation laws and exhibits unphysical kinetic energy gain" [SOURCED].

**Reasoning about the transfer GAP (DERIVED).** Two gaps: (a) **momentum is not species mass** — Dynami-CAL conserves an additive extensive vector via edge-antisymmetry; our conserved quantities (A, Z) are ALSO additive linear invariants, so the *conservation* mechanism transfers, but (b) **near-QSE stiffness has no particle-dynamics analog**: above ~3 GK fast forward/reverse pairs near-cancel and a species' net change is orders of magnitude below its gross rates (Hix & Thielemann 1996/1998 confirm QSE holds for T>~3 GK with "relatively little nucleosynthesis" after breakdown) [SOURCED]. Injecting GNS-style noise into a near-equilibrated abundance perturbs it OFF the QSE manifold, and the stiff Jacobian (large negative eigenvalues toward the manifold, but cross-coupling) can amplify the off-manifold component before it relaxes — the exact failure Ono & Sugimura describe at small dt [INFERRED, consistent with SOURCED stiffness physics].

**Strategies ranked (for stiff/QSE).**
1. **Pushforward / unrolled multi-step loss (Brandstetter et al. 2022, ICLR — verified).** Backprop through K steps brings the training distribution toward the test (rollout) distribution; "the pushforward trick can be seen to minimize κ directly" (the zero-stability constant) [SOURCED]. Safest for stiff systems because it trains on the model's OWN error distribution without injecting artificial off-manifold noise.
2. **Train-the-update (MACE pattern).** Train the iterative update directly so multi-step error is in the objective; known to increase one-step error (per Ono & Sugimura) but improves rollout.
3. **Log/asinh-space dynamics for 20+ decade spans (Döppel & Votsmeier, React. Chem. Eng. 8, 2620, 2023, D3RE00212H — verified; "embed the hyperbolic sine function into neural networks and fit the actual rates").** Required for the abundance dynamic range; asinh handles signed near-zero net fluxes better than log [SOURCED]. NOTE: the inherited QSE-cancellation rule forbids differencing two large LEARNED fluxes — asinh is for the SINGLE native linear output, transform kept internal.
4. **Random-walk noise injection (GNS) — DEMOTE to non-equilibrium channels only**, because of the QSE off-manifold risk above.

**DECISION D1 (PARALLEL):** Primary stability lever = **pushforward/unrolled training through K≥2 steps + conservation-in-decode**; asinh internal transform on the single linear output; GNS noise applied ONLY to channels flagged non-equilibrated by an equilibrium mask (this is a REQUIREMENT imposed on the Run-2 equilibrium-masking head). **Falsifiable threshold:** if ablation shows noise-on-all-channels degrades the constant-(T,ρ) Ye drift relative to noise-on-non-eq-channels, lock noise to non-eq channels permanently.

**Accumulation model — measurement protocol (DECISION D2; the single largest lever).** Under linear/systematic accumulation the per-step budget is F/N (5e-6 at N=1e3, 5e-7 at N=1e4 for F=5e-3); under random-walk it is F/√N (~1.6e-4 at N=1e3, ~5e-5 at N=1e4) [DERIVED from inherited constraints]. The gap is 100× at N=1e4 — decisive. **Protocol (hand to Phase 0):**
1. Run M independent constant-(T,ρ) rollouts of N=1e3–1e4 steps; record the per-step Ye residual r_k = dYe_pred − dYe_true.
2. **Drift test:** cumulative sum S_N = Σ r_k. Regress log|S_N| vs log N; **slope ≈ 1.0 ⇒ systematic (biased) ⇒ gate = F/N**; **slope ≈ 0.5 ⇒ zero-mean random walk ⇒ gate = F/√N.**
3. **Zero-mean test:** one-sample t-test / bootstrap CI on mean(r_k); autocorrelation function of r_k (significant positive lag-1 autocorrelation ⇒ effectively systematic even if marginal mean≈0).
4. **Cross-check:** regress cumulative |dYe error| vs N for slope ~N vs ~√N.

**Training choices that push residuals toward zero-mean (DERIVED):** signed/symmetric loss (not asymmetric); explicit bias-correction term; conservation structure (Target A's exact stoichiometric map makes the A,Z residual identically zero, isolating the Ye residual to weak reactions only); ensemble averaging (averages out the zero-mean component, NOT the systematic component — so ensemble mean is itself a diagnostic: if ensemble averaging reduces drift ∝1/√members, residual is random; if not, it's systematic).

**Loss design (DECISION D3).** NNN used L1; NuGNN used signed-log MAE [SOURCED]. The NNN weak point: large per-isotope composition errors (1e-4 to 1e-1, worst-case predictions unrelated to target) reported as MEANS not DISTRIBUTIONS [SOURCED inherited]. **Recommendation:** base = signed-log/asinh MAE; ADD a tail term (e.g., 90th/99th-percentile or CVaR weighting) so worst-case isotopes are optimized, not just the mean; multi-objective weights across composition/energy/neutrino; **up-weight Fe-peak A=45–65 LMP nuclei** (electron-capture/β-decay nuclei that set Ye; QSE neutronization physics from Hix 1996 shows a decrease in Ye drastically increases iron-peak QSE abundances, so these nuclei dominate the Ye budget) [SOURCED physics]. **Falsifiable threshold:** report per-isotope error as full distribution (CDF/quantiles); if 99th-percentile per-isotope error for any Fe-peak nucleus exceeds the level that moves Ye by >3e-6/step, increase that nucleus's loss weight until it doesn't.

**UQ / OOD (DECISION D3 cont.).** Use a **deep ensemble on the flux head** (Lakshminarayanan-style; cited in NuGNN's own references) over MC-dropout — ensembles give better-calibrated tails, and the ensemble spread doubles as the accumulation diagnostic above. An **OOD flag** (ensemble variance threshold, or distance to training manifold) feeds a **fallback-to-solver gate**: when flagged, hand the zone back to the bbq/MESA network solver. **The Sobol→real-MESA transfer risk** is the biggest UQ risk: error distributions measured on quasi-random Sobol compositions are NOT guaranteed to transfer to the thin, correlated manifold of real MESA trajectories [SOURCED inherited; DeePODE/Yao et al. 2025, ApJ, DOI 10.3847/1538-4357/adf331 — published, verified — addresses exactly this via evolutionary Monte Carlo sampling that evolves each sample "along its local ODE trajectory"] [SOURCED]. **Threshold:** measure error on held-out REAL MESA tracks, not just Sobol; if real-track 99th-percentile Ye error exceeds Sobol-measured by >3×, retrain with trajectory-aware (EMCS/DeePODE-style) sampling.

---

## 3. THIS RUN'S SLICE OF "EMULATOR DESIGN v1" SPEC

**C — Temporal head (v1):**
- dt enters as a global conditioning feature (log-scaled) on the Run-1 graph; training data on a stiffness-aware logarithmic dt grid spanning 1e-6–1e2 s (one model, vs NNN's nine).
- Rollout governor = Ono & Sugimura timescale-based rescaled update with ε≈0.1, τ_ε capped at max trained dt, conservation re-enforced after each step.
- All nonlinear transforms (asinh) internal/latent; the network's native output is the single linear conserved quantity (φ for A, dX for B).
- **Composes with Run-1:** requires the backbone to expose a global feature slot for dt and to keep the bipartite node structure intact (do NOT flatten for an operator trunk in v1).
- **Composes with Run-2:** temporal head outputs the latent/linear quantity; Run-2 decode applies the stoichiometric map (A) or null-space projection (B). Conservation is Run-2's job; the temporal head must NEVER apply a nonlinear transform after the conservation map.

**D — Stability + training (v1):**
- Loss = asinh-MAE base + quantile/CVaR tail term + Fe-peak (A=45–65) up-weight + multi-objective (composition/energy/neutrino).
- Training = pushforward/unrolled through K≥2 steps; GNS noise restricted to non-equilibrium channels (requires Run-2 equilibrium mask as input).
- UQ = deep ensemble on flux head; OOD flag → fallback-to-solver.
- Accumulation-model measurement (drift/slope/autocorrelation protocol) is a GATING deliverable before any pass/fail claim.
- Training-set design: Sobol for coverage PLUS real-MESA-track validation and EMCS/DeePODE-style trajectory sampling for the correlated manifold.

---

## 4. HAND TO PHASE 0 TO MEASURE (empirical, only bbq/MESA can settle)

1. **Accumulation model of the Ye residual** — systematic vs random-walk (slope of log|cumulative| vs log N). *Decides the per-step gate: 5e-7 vs 5e-5 at N=1e4. THE single biggest lever.*
2. **Sobol→real-MESA error transfer ratio** — 99th-percentile Ye error on real tracks ÷ on Sobol. *Decides whether trajectory-aware sampling is mandatory.*
3. **Per-isotope error DISTRIBUTION** (not mean) for Fe-peak A=45–65 nuclei — the level at which the worst-case isotope moves Ye by >3e-6/step.
4. **Whether the timescale-based update holds the Ye gate** at dt≥0.1 s (where NNN's neutrino losses become worse than the small net).
5. **Whether noise-on-non-eq-channels beats noise-on-all-channels** for constant-(T,ρ) Ye drift (the QSE off-manifold hypothesis).
6. **Whether the log-dt-grid head needs the latent-NODE upgrade** (constant-(T,ρ) 1000-step drift vs gate).

---

## 5. VERIFIED-REFERENCES TABLE

| Source | Load-bearing claim | Status | Preprint vs Published |
|---|---|---|---|
| Grichener et al. 2025, ApJS 279, 49; arXiv:2503.00115 | NNN baseline: 9 per-timestep models + interpolation; "errors of no more than 1% per time step"; Ye most robust; per-isotope errors as means | SOURCED | **Published** (ApJS), v2 on arXiv |
| Kim et al. 2026, arXiv:2606.04491 | NuGNN: 690-isotope, dt as input, signed-log MAE, retry-smaller-dt, "errors of only a few percent," beats FCN/Res-U-Net | SOURCED | **Preprint** |
| Maes et al. 2024, ApJ 969:79; arXiv:2405.03274 | MACE latent ODE; mean speedup factor 26 (24 low-ρ, 28 high-ρ); soft element-conservation loss "slowed down the training immensely" (decoder Jacobian) | SOURCED | **Published** (ApJ) |
| Goswami et al. 2023, CMAME 419:116674; arXiv:2302.12645 | DeepONet + PoU-DeepONet for stiff kinetics | SOURCED | **Published** (CMAME) |
| Nath et al. (AMORE), arXiv:2510.12999 | Mass-conserving operator; invertible analytical map to (n−1)-dim; trunk auto-satisfies PoU | SOURCED | **Preprint** (Oct 2025) |
| Branca & Pallottini 2024, A&A 684, A203 | DeepONet ISM emulator, "speed-up of a factor of 128×" | SOURCED | **Published** (A&A) |
| van de Bor et al. 2025, OJAp; arXiv:2503.10736 | Branca&Pallottini emulator unstable under iteration (error accumulation) | SOURCED | **Published** (Open Journal of Astrophysics) |
| Ono & Sugimura 2026, ApJ 996, 9; DOI 10.3847/1538-4357/ae1ca9; arXiv:2508.16114 | Timescale-based rescaled update; short-dt error-domination mechanism; stable to 1e-4 t_ff; 5 subregions, 6 species, >90% <10% error | SOURCED | **Published** (ApJ 2026) |
| Sanchez-Gonzalez et al. 2020, arXiv:2002.09405 (ICML) | GNS random-walk noise injection for rollout stability | SOURCED | **Published** (ICML/PMLR) |
| Pfaff et al. 2020, arXiv:2010.03409 | MeshGraphNets noise injection | SOURCED | **Published** (ICLR 2021) |
| Sharma & Fink 2026, Nat. Commun. 17:1045; arXiv:2501.07373 | Dynami-CAL: pairwise momentum conservation, "16000-rollout steps"; "GNS baseline violates conservation laws and exhibits unphysical kinetic energy gain" | SOURCED | **Published** (Nat. Commun.) |
| Brandstetter et al. 2022, arXiv:2202.03376 (ICLR) | Pushforward trick + temporal bundling; minimizes zero-stability κ | SOURCED | **Published** (ICLR 2022) |
| Holdship et al. 2021, A&A 653, A76 | Chemulator: noise layer for iterative robustness; "≈50 000 times faster"; stable 1000 iters (MSE 6×10⁻³ on log-T after 1000 steps) | SOURCED | **Published** (A&A) |
| Döppel & Votsmeier 2023, React. Chem. Eng. 8, 2620; D3RE00212H | asinh latent rate transform | SOURCED | **Published** (RSC) |
| Döppel & Votsmeier 2024, Proc. Combust. Inst. 40, 105507 | Atom-conserving CRNN; element-conservation subspace (hard constraint) | SOURCED | **Published** |
| Sulzer & Buck 2023, arXiv:2312.06015 | 29 species/224 reactions; neural-ODE "speed-up factor of 55," linear-latent "factor of 4270" | SOURCED | **Preprint** (NeurIPS ML4PS workshop) |
| Yao et al. 2025 (DeePODE), ApJ; DOI 10.3847/1538-4357/adf331; arXiv:2504.14180 | EMCS evolutionary Monte Carlo sampling for stiff nuclear reacting flows | SOURCED | **Published** (ApJ) |
| Wang et al. 2025 (ANN-hard) / PIML-combustion review arXiv:2509.03347 | Hard element-conservation correction term; soft-constraint violations accumulate over long horizons | SOURCED | Preprint (review) + published primary |
| Hix & Thielemann 1996/1998 (astro-ph/9511088, /9808203) | QSE holds T>~3 GK; lower Ye drastically raises iron-peak QSE abundances | SOURCED | **Published** (ApJ) |
| CODES, arXiv:2410.20886 | Coupled-ODE surrogate benchmarking framework | SOURCED | Preprint |
| SPIN-ODE, arXiv:2505.05625 | Stiff PINN neural ODE for reaction-rate estimation | SOURCED | Preprint |

***Corrections made vs the inherited brief:*** **(a)** van de Bor et al. 2025 is **arXiv:2503.10736 (OJAp)**, NOT 2508.16114; the latter is **Ono & Sugimura** (who CITE van de Bor) — the brief conflated them. **(b)** Ono & Sugimura is now **published as ApJ 996, 9 (2026)**, DOI 10.3847/1538-4357/ae1ca9 (journal year 2026, submitted Aug 2025). **(c)** Dynami-CAL Nature Communications DOI is 10.1038/s41467-025-67802-5 (vol 17, art 1045, 2026). **(d)** MACE mean speedup is a factor of 26 (24–28 range), not a single fixed figure. **(e)** Döppel & Votsmeier's asinh paper is dated 2023 (React. Chem. Eng. 8, 2620), with the atom-conserving CRNN (Proc. Combust. Inst. 40, 105507) being the 2024 work.

---

## 6. OPEN QUESTIONS FOR THE ADVERSARIAL AUDIT (my load-bearing assumptions)

1. **I assume the QSE off-manifold noise-amplification failure is real for THIS network.** It is INFERRED from stiffness physics + Ono & Sugimura's small-dt diagnosis, not directly demonstrated for a silicon-burning GNN. A referee should demand the noise-on-all vs noise-on-non-eq ablation before I lock D1.
2. **I assume the accumulation model can be measured cleanly on constant-(T,ρ) rollouts.** Real MESA tracks have time-varying T,ρ; the residual's bias may itself be state-dependent, breaking the clean slope-1-vs-0.5 dichotomy. The drift test may need to be conditioned on (T,ρ) bins.
3. **I assume dt-as-input on a log-dt grid actually spans 1e-6–1e2 s with one model.** NuGNN demonstrated variable-dt input but for X-ray-burst conditions, not the 8-decade silicon-burning range; the single-model claim is INFERRED, not proven for this regime.
4. **I assume the timescale-based update composes with the conservation decode.** Ono & Sugimura enforce conservation after each update by simple re-imposition; whether their rescaling commutes with the Run-2 stoichiometric/null-space map without breaking exactness is unverified — a potential interaction bug between C and Run-2.
5. **I assume deep-ensemble variance is a valid OOD signal on the thin MESA manifold.** Ensembles can be jointly overconfident off a correlated training manifold; the OOD gate could fail silently exactly where Sobol→MESA transfer fails.
6. **I treat asinh as strictly superior to log for the linear net output.** For a quantity that is genuinely the small difference left after QSE cancellation, even asinh of the native output may lose precision; a referee could argue for a dedicated residual-scaling scheme.
7. **The Target-A exact-conservation claim isolates Ye error to weak reactions — but I have not verified the lepton bookkeeping closes** when φ is learned with error; a biased weak-reaction flux could still drift Ye even with A,Z exactly conserved.

---

### Flagged neighboring-component interdependencies (do not re-decide; requirements imposed)
- **C ↔ Run-1 backbone:** the backbone MUST expose a global (graph-level) feature slot for log-dt and MUST preserve the bipartite isotope/reaction node structure (no flattening) so the temporal head's conditioning and any future operator trunk can attach without destroying the inductive bias.
- **C/D ↔ Run-2 head:** (i) conservation lives entirely in Run-2's decode (stoichiometric map for A / null-space projection for B); the temporal head must hand off the *linear* native quantity and apply no post-conservation nonlinearity; (ii) Run-2's equilibrium mask is a REQUIRED input to D's noise-injection gate (noise only on non-equilibrated channels); (iii) the timescale-based rescaled update (C3) must be verified to commute with the Run-2 conservation map (open question #4).