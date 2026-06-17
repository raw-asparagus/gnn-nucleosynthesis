# Training-Data Generation for a Conservation-by-Construction GNN Emulator of Silicon Burning — Report 2: Sampling and Data Shapes

## TL;DR
- **Adopt a three-way mixture design — ~60% broad Sobol (deliberately unphysical, for function-class coverage), ~25% trajectory-aware/EMCS seeding (real MESA tracks + ODE-evolved points, for manifold fidelity), ~15% uncertainty-driven active densification of the QSE-cancellation window (3.3–5 GK) and the Ye-controlling Fe-peak A≈45–65 nuclei.** This directly resolves Grichener's "unphysical sampling helps" finding against the Sobol→real-track transfer risk: broad coverage teaches the function class; targeted densification fixes the thin manifold where Ye accuracy is graded.
- **Generate variable-dt data as DENSE CUMULATIVE TRAJECTORIES, not per-state multi-dt integrations.** A single bbq burn to 10² s already traverses every dt of interest; checkpointing it at ~16–24 log-spaced times costs essentially the same CPU as the existing 9-timestep grid (multiplier ≈1.0–1.3) while making any dt derivable, feeding both the single variable-dt head and a latent-ODE upgrade. Storage rises from the public ~80 GB (3 GB mesa_80 + 6 GB mesa_151 per timestep × 9 timesteps) to ~0.4–0.8 TB — inside the negotiated 4 TB envelope.
- **Use a single-step-dominant data mix with a K=2–4 pushforward minority and QSE-respecting off-trajectory perturbations.** The astrochemistry/combustion precedent is unambiguous: pure single-step emulators drift under iteration (van de Bor et al. 2025), and the two fixes that worked were noise injection (Holdship et al. 2021 — Chemulator stayed "stable over 1000 iterations" with log-temperature MSE rising only from 3×10⁻³ to 6×10⁻³) and training the iterative update on its own rollout (MACE; Maes et al. 2024). Perturb only non-equilibrated channels so equilibrated QSE-group members stay on-manifold.

---

## Key Findings

1. **Citation corrections (sourced).** Three starting citations are misattributed and must be fixed before they become load-bearing: (a) **DeePODE/Evolutionary-Monte-Carlo-Sampling (EMCS)** is *Yao et al.* "Solving multiscale dynamical systems by deep learning," **arXiv:2401.01220** — the nuclear application the brief intends, arXiv:2504.14180, is **Zhang, Yi, Wang, Xu, Zhang & Zhou 2025**, "Deep Neural Networks for Modeling Astrophysical Nuclear Reacting Flows," which *adapts* DeePODE to a 13-isotope α-network and reports "≲1% accuracy relative to semi-implicit numerical solutions and … a ∼2.6× speedup on CPUs," with "neural network utilization above 75%" via a temperature-thresholded deployment. (b) **arXiv:2508.16114** is **Ono & Sugimura 2025**, "Neural-Network Chemical Emulator for First-Star Formation," NOT van de Bor; it introduces a timescale-based iterative-update fix. (c) The **van de Bor et al. 2025 iterative-instability finding** is in **arXiv:2503.10736**, "Bridging Machine Learning and Cosmological Simulations" (van de Bor, Brennan, Regan & Mackey), which emulates the Grackle solver and reports instability from accumulated iteration error. All other starting citations verified as real with correct venues (Grichener 2025 ApJS 279,49; Kim et al. 2026 NuGNN arXiv:2606.04491; Maes 2024 ApJ 969:79; Holdship 2021 A&A 653:A76; Guidry 2012 arXiv:1112.4778; Hix & Thielemann 1996 ApJ 460:869 / arXiv:astro-ph/9511088; Lippuner & Roberts 2017 ApJS 233:18; Reichert 2023 ApJS 268:66; CODES arXiv:2410.20886; Sulzer & Buck 2023 arXiv:2312.06015).

2. **The Sobol→real tension is a coverage-vs-density problem, and the literature already shows the resolution (sourced + derived).** Grichener et al. (2025 §2.2) found broad/unphysical composition sampling was *required*, stating verbatim: "we find that narrowing our parameter space by using typical composition from inner regions of massive star evolved with MESA results in NNNs with poor performance, as the broader coverage significantly enhance the generalizations ability of the NNN trained models." DeePODE (Yao 2025; Zhang 2025) demonstrates the complementary failure mode — manifold-only sampling (real trajectories) also fails to generalise off-manifold, "perform[ing] poorly on the test samples deviating from it." The synthesis both literatures converge on is a **mixture**: global MC/QMC for coverage *plus* trajectory-evolved points for the dynamically-important manifold. This is exactly EMCS.

3. **Simplex-under-Ye geometry is an (n−2)-dimensional polytope, and naive symmetric cube→simplex maps degrade QMC (sourced).** For n isotopes, the probability simplex is (n−1)-dimensional; one further independent linear equality (Ye = Σ(Zᵢ/Aᵢ)Xᵢ) reduces it to an **(n−2)-dimensional convex polytope** (n−2 = 78 for mesa_80, 149 for mesa_151). Dirichlet(α=1) is exactly uniform on the simplex (the "flat Dirichlet"), but **no closed-form conditional Dirichlet exists for a general weighted linear constraint** — the correct target is uniform-on-the-(n−2)-polytope. Critically, Basu & Owen (2016, SIAM J. Numer. Anal. 54(3):1946) show "popular symmetric transformations to the simplex … satisfy neither condition" for preserving bounded Hardy–Krause variation, so a careless Sobol→simplex map silently forfeits the low-discrepancy advantage.

4. **Rollout stability is governed by the error-accumulation slope, which only a local experiment can measure (derived from project ground truth).** The per-step Ye gate moves ~2 orders of magnitude (3×10⁻⁶ systematic at N≈1.6×10³ vs ~5×10⁻⁵ random-walk) depending on whether cumulative error grows with slope ≈1 (systematic) or ≈0.5 (random walk). No external paper settles this for silicon burning; it must be measured on bbq/MESA rollouts. This is the single biggest lever and the top entry in the local-experiment risk register.

5. **Variable-dt is nearly free if you store trajectories (derived from Report 1 cost model).** bbq runtime grows with dt because larger compositional change requires more Bulirsch–Stoer substeps; the expensive part is reaching 10² s. Grichener et al. (2025 §2.1) confirm BBQ can "create sufficiently large (≃10⁶) training datasets within few ×10⁵ CPU hours." Checkpointing intermediate states adds negligible CPU. Thus the naive "9× (or 24×) cost for 9 (or 24) separate dt grids" is avoided: the multiplier is ≈1, not ≈N_dt.

---

## Details

### C. Sampling and Experimental Design

#### C(i) Sampling the composition simplex under the linear Ye constraint

**The geometry (sourced).** Grichener et al. correctly noted that "compositions … consist of non-independent abundances that sum to unity, making quasi-random sampling non-applicable," and fell back to ad-hoc random composition generation matching each sampled Ye. This is the weakest link in the baseline pipeline and the place where the Sobol low-discrepancy guarantee is currently lost. The constrained object is the intersection of the unit simplex Δⁿ⁻¹ with the hyperplane {Σ(Zᵢ/Aᵢ)Xᵢ = Ye}, an **(n−2)-dimensional bounded convex polytope** (confirmed via Dubins' theorem on polytope∩hyperplane and standard affine-dimension arithmetic).

**Three candidate methods, compared:**

- **Dirichlet sampling.** Dirichlet(α=1) gives exactly uniform-on-simplex; the sorted-spacings construction (Willms 2021, *Missouri J. Math. Sci.* 33(1):119) realises it from n uniforms. But conditioning on a *second weighted* linear constraint has **no closed form** — the conditional uniform distribution on the (n−2)-polytope is generally not a Dirichlet. Concentration parameters α≠1 give controlled bias toward sparse (small-α, simplex-edge/few-isotope) or dense (large-α, iron-peak-spread) compositions, useful for deliberately spanning unphysical states. Verdict: **excellent for controlled-bias bulk generation; cannot natively honour Ye exactly.**

- **Sobol-on-simplex via cube→simplex transform.** Pillards & Cools (2005, *J. Comput. Appl. Math.* 174(1):29) give five mappings from the unit cube to a simplex and a Koksma–Hlawka inequality showing "under certain conditions the order of convergence using the new point set is the same as that of the original set." Basu & Owen (2015, *SIAM J. Numer. Anal.* 53(2):743) achieve triangle discrepancy "below 12/√N" (van der Corput) and "O(log(N)/N), which is the best possible rate" (rotated lattice). **But** Basu & Owen (2016) warn that symmetric simplex maps can destroy bounded variation, forfeiting these rates. Verdict: **preserves low-discrepancy only with a carefully chosen (non-symmetric) transform; the equality constraint is handled by reducing to the (n−2)-polytope first, then mapping.**

- **Constrained QMC on the polytope (hit-and-run / billiard walk).** volesti-style billiard-walk samplers (Gryazina & Polyak 2012, arXiv:1211.3932) target uniform-on-polytope for arbitrary linear constraints and "demonstrate much faster convergence to the uniform distribution" than hit-and-run. **Caveat (sourced):** these are MCMC samplers and carry **no proven QMC star-discrepancy bound** — they sacrifice the low-discrepancy property the project wants. The DRS algorithm (Griffin et al. 2020) is shown by Willemsen et al. (2025, arXiv:2501.16936) to **not** produce uniform samples under multiple constraints; their DRSC fix does.

**Recommendation (derived).** Two-stage hybrid: **(1)** draw Ye and (logT, logρ) jointly with a Sobol sequence over the 3-D box (preserving the property Grichener relied on for thermodynamics); **(2)** for each Ye, sample the composition on the (n−2)-polytope. For the *bulk* (broad-coverage) set, use a **Dirichlet-with-projection** scheme: draw Dirichlet(α) with α swept to span sparse→dense states, then project/rescale to the Ye hyperplane (DRSC-style minimal correction) — cheap, embarrassingly parallel, spans unphysical states. For a *low-discrepancy core* (~20% of the broad set), use a Pillards–Cools non-symmetric cube→polytope transform driven by Sobol points, accepting that exact star-discrepancy on >2-D constrained polytopes is unproven (see Caveats). This is a concrete, defensible replacement for Grichener's "generate randomly" step.

#### C(ii) Reconciling "unphysical helps" with Sobol→real transfer failure

The resolution is **division of labour by data subset (derived)**: the broad/unphysical Sobol+Dirichlet bulk exists to teach the *function class* (the network must represent dX/dt correctly even off-manifold, because pushforward rollouts and hydro coupling will visit perturbed states); the trajectory-aware subset exists to densify the *thin correlated manifold* where validation Ye error is actually scored. Concretely: **(a)** keep broad coverage as the majority; **(b)** add targeted densification on/near real MESA tracks; **(c)** at training time, apply **importance reweighting** so the loss up-weights samples near the real manifold and the Fe-peak A≈45–65 LMP nuclei — this lets one dataset serve both generalisation and on-manifold accuracy without regenerating data. The retrain trigger (real-track 99th-percentile Ye error > 3× Sobol value) is the monitored quantity that tells you whether the mix is right.

#### C(iii) Adaptive / active-learning strategies, head-to-head

- **(a) DeePODE/EMCS (Yao 2025 arXiv:2401.01220; nuclear: Zhang 2025 arXiv:2504.14180).** Mechanism: global MC sampling, then evolve each seed along its local ODE trajectory at the system's characteristic timescales, "concentrat[ing time points] on the initial reaction stages where reaction stiffness typically peaks." The nuclear adaptation used a 13-isotope α-network (⁴He…⁵⁶Ni — directly overlapping the silicon group), a Box–Cox transform (λ=0.1) instead of log to handle mass fractions down to 𝒪(10⁻²⁵), and **temperature-gradient filtering** retaining ~75–100% of high-gradient (stiff) samples vs ~8–10% of low-gradient samples, yielding ~17M (3-species) / ~28M (13-species) points and "≲1% accuracy." **Cost vs Report 1 model:** EMCS is cheap — evolving a seed and checkpointing is the *same* embarrassingly-parallel bbq burn already costed at 0.1–0.5 CPU-hr/sample; the only addition is checkpoint storage. **Implementation effort: low** (it is the trajectory-storage scheme of section D plus stiff-region filtering). **QSE suitability: high** — concentrating samples in the early stiff stage maps onto the 3.3–5 GK cancellation window.

- **(b) Deep-ensemble-variance active learning.** CODES (Janssen, Sulzer & Buck 2024, arXiv:2410.20886) shows DeepEnsemble (n=5) gives "a generally reliable uncertainty estimate" with positive Pearson correlation between predicted uncertainty and prediction error, and that latent-ODE surrogates show "higher errors at points with larger gradients." Use ensemble variance as the acquisition signal to choose new (T,ρ,X,dt) points. **Cost:** dominant cost is training N ensemble members (compute, not CPU-hr of data) plus a *new* bbq burn per acquired point (0.1–0.5 CPU-hr each) — the burns are cheap but the loop is serial across acquisition rounds, eroding the embarrassingly-parallel advantage. **Implementation effort: medium-high** (retraining loop, acquisition infra). **QSE suitability: high but indirect** — variance will naturally spike in the cancellation window where the map is hardest.

- **(c) Stiffness-/timescale-adaptive density.** Deterministically over-sample the QSE-cancellation window (3.3–5 GK) and the Ye-controlling Fe-peak nuclei using a known physics prior (Hix & Thielemann 1996; Guidry partial-equilibrium timescales). **Cost: lowest** (no retraining loop; just a non-uniform sampling density — pure data generation at 0.1–0.5 CPU-hr/sample). **Implementation effort: low.** **QSE suitability: highest and most controllable.** This is the cheapest way to buy QSE-window accuracy and should be the default densification; ensemble-variance AL is the more expensive refinement layer if (c) proves insufficient.

**Verdict:** Combine (c) as a cheap deterministic prior with EMCS (a) for manifold/stiffness coverage; reserve ensemble-variance AL (b) for a single late-stage refinement round targeted at whatever the validation test (G) flags.

#### C(iv) Trajectory-aware sampling and budget split

Seed bbq burns from **real MESA pre-collapse tracks** (the public 20 M⊙ test-case trajectory underlying Grichener's regime box, and 15–25 M⊙ progenitors) and from EMCS-evolved points, storing full trajectories. **Recommended budget split (derived, assumption-flagged):**
- **~60% broad Sobol+Dirichlet** (function-class coverage, deliberately unphysical) — preserves the Grichener finding.
- **~25% trajectory-aware** (EMCS-evolved seeds + real-MESA-seeded burns) — manifold fidelity, the Sobol→real fix.
- **~15% active/stiffness densification** (QSE window 3.3–5 GK + Fe-peak A≈45–65), of which the first ~10% is the cheap deterministic prior (c) and ~5% reserved for one ensemble-variance round (b).

This split is the starting allocation; the benchmark that moves it is the validation test in G (below).

#### C(v) Coverage of moving regime boundaries

Three boundaries must be deliberately sampled, not left to chance (sourced physics from Hix & Thielemann 1996/1999):
- **QSE-cancellation window (~3.3–5 GK):** densify (section C-iii-c). Guidry (2012, arXiv:1112.4778) identifies the precise pathology — "the net flux in specific forward-reverse reaction pairs (fᵢ⁺ fᵢ⁻) tends to zero as the system approaches equilibrium; this leads to large errors … the net flux is derived from the difference of two large numbers." The signed-net-flux architecture lives or dies in this window.
- **NSE transition (~6 GK for explosive, ~3.5 GK hydrostatic — Hix & Thielemann note QSE holds for T ≳ 3 GK):** sample across the upper temperature edge so the emulator learns the approach to full equilibrium.
- **Ye-dependent silicon/iron-peak group-merger boundary (sourced, the key Hix & Thielemann 1996 result):** the merger is strongly neutronization-dependent. At Ye=0.498 a single QSE group forms when X(Si group)≈0.85; at Ye=0.46 the iron-peak group reaches 90% of its Si-QSE abundance only when the Si-group mass fraction has fallen to 0.25–0.30. **Implication:** sampling density in composition space must be correlated with Ye — the group structure (hence the correct GNN equilibrium mask) changes shape across the 0.45–0.5 Ye band. Uniform-in-Ye sampling under-resolves the low-Ye merger delay.

### D. Variable-dt Data

**Per-state multi-dt vs dense trajectories (derived from Report 1 pipeline facts).** The baseline trained a *separate network per timestep* (the NNN) over 9 fixed dt. Generating 9 independent integrations per state would be wasteful: bbq's Bulirsch–Stoer/Bader–Deuflhard integrator already passes through all intermediate times en route to 10² s. **Store cumulative trajectories** and sub-sample any dt:
- **Cost multiplier:** ≈1.0–1.3 vs the existing single-endpoint grid (the extra cost is only additional integrator output, not additional burns). Contrast with the naive ≈N_dt multiplier of independent multi-dt runs.
- **dt-grid density:** ~16–24 log-spaced checkpoints across the 8 decades [10⁻⁶, 10²] s (≈2–3 per decade), versus the baseline's 9. This over-resolves the original grid so the single variable-dt head and a latent-ODE can interpolate dt accurately, especially in the early stiff stage where EMCS also concentrates points.
- **Storage:** the public set is ~80 GB for 9 timesteps × ~10⁶ states (3 GB mesa_80 + 6 GB mesa_151 per timestep, per Grichener §2.2). Scaling to ~16–24 checkpoints gives **~0.15–0.4 TB per network**, ~0.4–0.8 TB for both — comfortably within the on-request 4 TB superset envelope (which exists precisely to hold finer/more timesteps).

**How the heads consume it:** the single variable-dt head trains on (state, log dt) → (state(dt), e_nuc, ε_ν) tuples drawn from arbitrary checkpoints of the stored trajectory; a latent-ODE upgrade consumes the *same* trajectories as continuous-time supervision (integrating the learned latent vector field between checkpoints, exactly the MACE pattern, which uses torchode to train the latent ODE and "outperforms its classical analogue on average by a factor 26"). Storing cumulative trajectories is therefore **forward-compatible with both heads** and is the recommended canonical data shape.

### E. Trajectory, Rollout, and Off-Trajectory Data

**How rollout-stable neighbour surrogates generated their data (sourced):**
- **Holdship et al. 2021 (Chemulator; A&A 653:A76, arXiv:2106.14789):** trained a single-timestep map and achieved stability "over 1000 iterations with an MSE of 3 × 10⁻³ on the log-scaled temperature after one time step and 6 × 10⁻³ after 1000 time steps" (single-step MSE 1.7×10⁻⁴), "approximately 50 000 times faster than the time-dependent model" — explicitly via **Gaussian noise injection during training** so the network sees perturbed (off-trajectory) inputs resembling its own accumulated error.
- **MACE (Maes et al. 2024; ApJ 969:79, arXiv:2405.03274):** autoencoder + trainable latent ODE; the stabilising choice was **training the iterative update itself** (the latent ODE is integrated and supervised across the rollout, using torchode), rather than a one-step map. Training data came from 1-D AGB-outflow CSE models (UMIST Rate22 network, 468 species).
- **van de Bor et al. 2025 (arXiv:2503.10736):** the cautionary tale — DeepONet emulation of Grackle "is prone to instability due to the accumulation of prediction errors," motivating the project's pushforward-first stance.
- **Ono & Sugimura 2025 (arXiv:2508.16114):** confirmed the instability and added a **timescale-based update** (rescaling a long-step prediction to a short step by the variable's characteristic timescale) so that the "time variation is dominated by the error rather than by the physical evolution" failure mode is avoided when dt is tiny. Directly relevant to the project's smallest dt (10⁻⁶ s) where per-step physical ΔYe can be below the emulator's error floor.
- **Pushforward trick (Brandstetter et al. 2022, MP-PDE, arXiv:2202.03376):** unroll the solver K steps, feed the model its own output, "only backpropagat[e] errors on the last unroll step" — "it also seems to be more stable" and ensures "the perturbations are large enough" to match the rollout error distribution. K=2 is standard; CODES and multiple PDE benchmarks corroborate K=2–4.

**QSE-respecting off-trajectory perturbations (derived).** The data-side counterpart of noise injection must **not** push equilibrated species off-manifold, because within a QSE group the intra-group abundances are algebraically slaved to the group's controlling abundances and a few thermodynamic variables (Hix & Thielemann 1996). The recipe: **(1)** compute QSE-group membership for each stored state (via the Guidry partial-equilibrium ε≈0.01 prior used by the architecture's mask); **(2)** inject noise **only into non-equilibrated channels** — the light-particle pool, weak-reaction-controlled Ye, and species whose net flux is *not* near catastrophic cancellation; **(3)** for equilibrated groups, perturb only the *group-controlling* coordinates and re-impose the QSE relation, so the perturbed state remains a physically reachable point. This keeps the off-trajectory data on the slow manifold the emulator must track.

**Recommended single-step-vs-sequence DATA MIX (derived):**
- **~70% single-step pairs** (state, dt)→state(dt), drawn from stored trajectories at all dt — the bulk supervision, cheapest, and what the variable-dt head fundamentally learns.
- **~20% K=2–4 pushforward sequences** (consecutive trajectory checkpoints) for unrolled training — the primary rollout lever per the project's established decision.
- **~10% QSE-respecting perturbed off-trajectory states** paired with their true one-step evolution — the noise-injection counterpart, restricted to non-equilibrated channels.

Because all three are *derived from the same stored cumulative trajectories*, this mix adds **no new burns** beyond section D — it is a sampling policy over existing data, not a new generation campaign.

### G. Real-MESA-Track Validation Data and Solver-Independent Cross-Checks

**(i) Held-out validation for the Sobol→real transfer test (derived, concrete design).**
- **Hold out entire real MESA trajectories** (15–25 M⊙ pre-collapse progenitors from the public models) — never used in training.
- **Measure:** at each held-out track state and each dt, the per-step Ye error |ΔYe_pred − ΔYe_true|; report the **99th-percentile** of this error over the real-track distribution, and the matched 99th-percentile over the Sobol test distribution.
- **The ratio R = (real-track 99th-pct Ye error) / (Sobol 99th-pct Ye error)** is the transfer metric. **Retrain trigger: R > 3** (the project's established threshold). When triggered, the response is to shift budget toward the trajectory-aware fraction (section C-iv) and re-run targeted densification, not to abandon broad Sobol.
- **Also report** the error-accumulation slope (log|cumulative Ye error| vs log N) on full real-track rollouts — this is the quantity that sets the per-step gate (3×10⁻⁶ systematic vs ~5×10⁻⁵ random-walk) and must be measured locally.

**(ii) Real tracks as seeds for trajectory-aware sampling.** The same held-out-for-validation discipline requires a *separate* set of real tracks used only as EMCS seeds (section C-iv). Do not seed from and validate on the same trajectory.

**Solver-independent cross-checks (sourced).** bbq wraps MESA r23.05.1's Bulirsch–Stoer/Bader–Deuflhard solver; systematic solver bias would be invisible to internal validation. Cross-check a sample of bbq states against:
- **SkyNet (Lippuner & Roberts 2017, ApJS 233:18):** first-order implicit backward-Euler integrator — a deliberately different scheme.
- **WinNet (Reichert et al. 2023, ApJS 268:66, arXiv:2305.07048):** implicit Euler and Gear's method with Newton–Raphson, plus an NSE solver descending from high T. WinNet's explicit NSE/temperature-regime handling is a useful check on the NSE-transition boundary (section C-v).
Agreement to within the per-step Ye gate across all three solvers certifies that the *training labels themselves* are not solver-limited before the emulator is blamed.

### H. New-Regime Data Roadmap (Phases 2–4)

Prioritisation by scientific leverage per CPU-hr (sourced regime physics; costs derived from Report 1 model: a fresh ~10⁶-grid is "few ×10⁵ CPU hours" ≈ 6–29 node-months on one 24-core node at ~17,000 core-hr/month):

| Priority | Regime | Conditions (sourced) | Why / data needed | Rough cost |
|---|---|---|---|---|
| **P1** | **mesa_151 fine-tuning sets** (size-transfer test) | Same Si-burning box | *Modest* sets to test mesa_80→mesa_151 transfer; don't regenerate a full grid — fine-tune. | ~10⁴–10⁵ CPU-hr (0.5–6 node-months); reuse existing public data first |
| **P2** | **Oxygen burning** | T≈1.5–2.6 GK, just below the Si box; the natural pre-Si phase already partly in Grichener's "post-oxygen-depletion" tracks | Extends the temporal domain backward; same isotopes, lower-T edge — cheap extension of existing networks. | ~1–5×10⁵ CPU-hr per network (6–29 node-months) |
| **P3** | **ECSN (electron-capture SN)** | ONe core, **Ye≈0.493–0.499** at O-ignition, central ρ≳10¹⁰ g/cm³ — *lower T, higher ρ than the Si box* | Needs density coverage beyond the public 10⁷–10⁹ band → **the on-request 4 TB superset's extended-density coverage is the enabler.** Weak rates (electron capture on ²⁰Ne, ²⁴Mg) dominate Ye → high LMP loss weight. | ~1–5×10⁵ CPU-hr per network; **partly satisfiable from negotiated 4 TB set without new burns** |
| **P4** | **PPISN / PISN** | **T~1.5–2.2 GK (PPISN O-shell) to ~3–5 GK (PISN explosive O-burn), ρ~10³–5×10⁵ g/cm³** — *far lower density than the Si box* | Lowest-ρ regime; requires extending below 10⁷ g/cm³ — a genuinely new grid, no overlap with public/4 TB density coverage. Lowest scientific overlap with the Si-burning surrogate. | ~1–5×10⁵ CPU-hr per network (6–29 node-months); new allocation |
| **P5** | **mesa_204-scale sets** | Si box, 204 isotopes | Future network target; per-sample cost and storage scale with isotope count (≥1.3× mesa_151). Defer until mesa_151 surrogate is validated. | >5×10⁵ CPU-hr (>29 node-months) — full new campaign |

**Role of the negotiated 4 TB set (sourced):** it adds finer/more timesteps (supporting section D's dense trajectories *for free*, no new burns) AND extended density coverage beyond 10⁷–10⁹ g/cm³ (directly enabling P3 ECSN's high-ρ edge). Because it is a discretionary external dependency (on request from the corresponding author, non-trivial transfer, not deposited), **negotiate it early** — it is on the critical path for both variable-dt data and ECSN, and its absence forces expensive re-generation.

---

## Recommendations (staged, with thresholds)

**Stage 0 — Fix the simplex sampler and trajectory storage (before any new campaign).**
1. Replace Grichener's ad-hoc "generate composition randomly per Ye" with the **two-stage Sobol(thermo) + Dirichlet-with-DRSC-projection(composition)** scheme; reserve ~20% for a non-symmetric Pillards–Cools Sobol→polytope core.
2. Switch bbq output to **dense cumulative trajectories** (16–24 log-dt checkpoints). Benchmark: trajectory generation cost multiplier must stay ≤1.3× the single-endpoint grid; storage ≤0.8 TB for both networks.

**Stage 1 — Generate the mixture training set (one node-scale campaign, ~6–29 node-months for 10⁶ states).**
3. Allocate **60% broad Sobol+Dirichlet / 25% trajectory-aware (EMCS + real-MESA seeds) / 15% stiffness-active** (10% deterministic QSE-window+Fe-peak densification, 5% reserved).
4. Build the **single-step 70% / pushforward-K=2–4 20% / QSE-respecting-perturbed 10%** data mix as a *sampling policy over stored trajectories* (no new burns).

**Stage 2 — Validate and adapt.**
5. Run the **Sobol→real validation test**: measure R = real/Sobol 99th-pct Ye-error ratio and the cumulative-error slope. **If R > 3 → retrain**, shifting ~10 percentage points of budget from broad Sobol to trajectory-aware + densification, and re-run one ensemble-variance AL round targeted at the flagged region.
6. Run **SkyNet + WinNet cross-checks** on a label sample; agreement within the per-step Ye gate is the go/no-go for trusting bbq labels.

**Stage 3 — Phase out to new regimes** in order P1→P2→P3→P4→P5, gated on the prior phase passing its validation test. **Negotiate the 4 TB superset now** — it is prerequisite for Stage-0 trajectory data and Stage-3 P3.

**Benchmarks that change the plan:** R>3 → rebalance budget; cumulative-error slope ≈1 (systematic) → tighten per-step gate to 3×10⁻⁶ and add pushforward steps; slope ≈0.5 → gate relaxes to ~5×10⁻⁵ and single-step fraction can rise; QSE-window 99th-pct flux error dominating → increase deterministic densification (c) before paying for ensemble AL (b).

---

## Caveats and Risk Register

**Risks the LITERATURE CAN SETTLE (resolved above):**
- *Does unphysical sampling help?* — Yes (Grichener 2025, sourced verbatim); resolved by the mixture design.
- *Do single-step emulators drift under rollout?* — Yes (van de Bor 2025); fixed by noise injection (Holdship 2021) + trained iterative update (MACE 2024) + pushforward (Brandstetter 2022).
- *Can QMC preserve low-discrepancy on a simplex?* — Partially: O(log N/N) proven for the 2-D triangle (Basu & Owen 2015); symmetric transforms degrade it (Basu & Owen 2016).
- *What are the new-regime conditions?* — Sourced (ECSN Ye≈0.493–0.499, ρ≳10¹⁰; PPISN/PISN T~1.5–5 GK, ρ~10³–10⁶).

**Risks needing a LOCAL NUMERICAL EXPERIMENT on bbq/MESA data:**
1. **The error-accumulation slope (≈1 systematic vs ≈0.5 random-walk).** SINGLE BIGGEST LEVER; moves the per-step gate ~2 orders of magnitude. No external paper settles it for silicon burning. *Experiment:* roll out the trained emulator on held-out real tracks, regress log|cumulative ΔYe| vs log N.
2. **Whether star-discrepancy is actually preserved on the (n−2)-polytope at n=78–149.** Basu & Owen's positive results are 2-D; the high-dimensional constrained-simplex case is unproven (subagent confirmed no theorem exists for >2-D). *Experiment:* compute empirical discrepancy / integration error of the chosen Sobol→polytope transform against a reference, at the real isotope count.
3. **Whether QSE-respecting perturbation actually keeps states on-manifold.** *Experiment:* perturb equilibrated-group coordinates, re-impose QSE, integrate one bbq step, and check the perturbed-state error does not exceed the on-trajectory error — the test that noise injection is helping not hurting.
4. **Whether the 4 TB superset's density/timestep coverage is sufficient for ECSN/variable-dt** — only verifiable by inspecting the set after transfer. Discretionary external dependency = schedule risk.
5. **mesa_80→mesa_151 size-transfer feasibility with modest fine-tuning sets** (P1) — no precedent in the literature for this specific transfer; must be measured.

**Standing caveats:** hit-and-run/billiard-walk constrained samplers carry no QMC guarantee (use only if low-discrepancy is sacrificed deliberately); the DRS algorithm is non-uniform under multiple constraints (use DRSC; Willemsen et al. 2025); EMCS's temperature-gradient filtering thresholds (Zhang 2025) are tuned to white-dwarf combustion, not silicon burning, and must be re-tuned. All CPU-hr and node-month figures derive from Report 1's cost model (0.1–0.5 CPU-hr/sample; ~17,000 core-hr/month/24-core node; "few ×10⁵ CPU hours" per 10⁶-grid, Grichener 2025 §2.1) and inherit its ±factor-of-a-few uncertainty.