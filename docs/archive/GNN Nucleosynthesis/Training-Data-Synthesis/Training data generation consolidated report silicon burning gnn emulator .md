# Training-Data Generation for a Conservation-by-Construction GNN Emulator of Silicon Burning: Consolidated Specification — Inventory, Pipeline, Sampling, Data Shapes, and Cost Model

*Synthesis of four research artifacts — two training-data design runs (the generation/pipeline/cost report and the sampling/data-shapes report) and their two adversarial referee audits, June 2026. All audit corrections are folded directly into the text; citations, physics thresholds, and numerical bands reflect the post-verification state. The architecture, scientific case, and Yₑ-accuracy decision are established in separate documents and are summarized here only as far as needed to make the data plan self-contained.*

---

## Abstract

This report specifies the complete training-data layer for a conservation-by-construction graph neural network (GNN) emulator of MESA's softwired silicon-burning networks (mesa_80, mesa_151), benchmarked against the Grichener et al. 2025 fully-connected "Nuclear Neural Network" (NNN) on its public Zenodo data. It covers four things end to end: what public data exist and where they fall short; the bbq/MESA generation pipeline and how to derive the conservation and kill-test quantities the architecture gates on; how to sample the constrained composition space and what data shapes to generate; and the cost, storage, format, validation, and new-regime roadmap that make the plan executable.

Four conclusions dominate. **First, the public reproducibility package is not a flux database.** Zenodo 14873443 stores single-step (state, dt → composition + nuclear energy + neutrino loss) tuples at nine fixed timesteps for two networks, but contains no per-reaction gross fluxes, no signed net fluxes, and no quasi-statistical-equilibrium (QSE)/nuclear-statistical-equilibrium (NSE) reference abundances. Every quantity the project gates on — the signed net per-reaction flux φ that is the emulator's primary prediction target (Target A), the gross forward/reverse fluxes f±, the equilibrium references, and the cancellation/deviation diagnostics κ_r and δ_r — must be derived externally with pynucastro on rate inputs matched to MESA's, or by re-instrumenting bbq. A detailed-balance/phase-space artifact screen, anchored on a documented and severe MESA bug, gates all flux work and must run before any flux quantity is trusted. **Second, the sampling design replaces the baseline's weakest link with a constrained, low-discrepancy scheme and a three-way mixture.** The constrained composition object is the intersection of the probability simplex with the electron-fraction hyperplane — an (n−2)-dimensional polytope — and the recommended generator draws thermodynamics by Sobol and composition on that polytope, then blends ~60% broad/deliberately-unphysical coverage, ~25% trajectory-aware seeding, and ~15% deterministic densification of the QSE-cancellation window and the iron-peak weak-rate nuclei. **Third, the canonical data shape is the dense cumulative trajectory, but it is cheap only for new burns.** One bbq integration checkpointed at 16–24 log-spaced times makes any timestep derivable and feeds both the variable-Δt head and a latent-ODE upgrade; the single-step/pushforward/perturbed training mix is then a sampling policy over stored trajectories with no further burns. Crucially, the public set stored only its nine checkpoints, so obtaining dense trajectories for the existing ~10⁶ states requires either the on-request 4 TB superset or a fresh ~10⁶-burn campaign — variable-Δt data is not a free retrofit of the public data. **Fourth, sequencing follows cost.** A from-scratch 10⁶-grid is a multi-month, cluster-scale campaign (~1–5×10⁵ CPU-hr; roughly 6–29 node-months on a single 24-core node), whereas every derivation above is CPU-cheap and embarrassingly parallel. Year-1 therefore lives on the public data, derives all kill-test quantities immediately, negotiates the 4 TB superset early, and defers fresh burns to mesa_204 and new regimes. The single number that reshapes everything downstream — the per-step Yₑ accuracy gate — is fixed by the error-accumulation slope of the trained emulator, a quantity no external paper settles and that only a local rollout experiment can measure.

---

## 1. Inherited project context (the established basis this plan serves)

The data plan is downstream of decisions made elsewhere and not re-derived here; they are stated so the plan stands alone.

The **emulator** is a heterogeneous GNN operating on the bipartite isotope↔reaction graph of MESA's softwired networks, targeting the same problem as Grichener et al. 2025 (ApJS 279, 49) — fast surrogate evaluation of single-zone burning — but adding the property both the NNN and the closest competitor NuGNN (Kim et al. 2026, arXiv:2606.04491) lack: hard baryon-number and charge conservation built into the architecture.

The **prediction target (Target A)** is a signed net per-reaction flux φ, mapped to the abundance change through the fixed stoichiometric matrix as dY = νφ, so that baryon and charge conservation hold to machine precision for any φ; the electron fraction Yₑ ≡ Σᵢ Zᵢ Xᵢ/Aᵢ = Σᵢ Zᵢ Yᵢ is left free to evolve through the weak interactions that drive it. The fallback parameterization (Target B) predicts ΔX directly and projects onto the conservation null-space in a linear space. The data plan must therefore deliver φ and its supporting quantities as first-class training labels, not merely the abundance changes the public set provides.

The **accuracy gate** is set by weak-interaction physics, not by beating the baseline. The defensible nuclear-physics floor — anchored on the shift from the older Fuller–Fowler–Newman (FFN) weak rates to the modern Langanke–Martínez-Pinedo (LMP) set, led by the iron-peak electron-capture/β-decay nuclei — is ΔYₑ ≈ 5×10⁻³ to 1.5×10⁻² end-to-end per trajectory. Under the conservative systematic-accumulation model appropriate to an autoregressive emulator, at a trajectory length N ≈ 1.6×10³ this implies a per-step kill-test threshold of |ΔYₑ| ≲ 3×10⁻⁶, which is the operative per-step gate throughout. The alternatives — 5×10⁻⁷ (systematic at N = 10⁴) and ≈5×10⁻⁵ (zero-mean random-walk at N = 10⁴) — are not adopted until the accumulation model is measured (§7).

The **regime box** is the Grichener Sobol domain: T ≈ 1.6–7.9 GK (10⁹·² – 10⁹·⁹ K), ρ ≈ 10⁷–10⁹ g cm⁻³, 0.45 < Yₑ < 0.5; the silicon-burning core of that box sits at T ≈ 3.5–5 GK. The **equilibrium mask** that protects the flux head from resolving the near-zero net flux of a balanced forward/reverse pair acts on the latent flux only and never on weak reactions — a rule the artifact screen and the off-trajectory perturbation scheme below both respect.

The **tools** are bbq (Farmer 2023, a one-zone MESA wrapper), MESA r23.05.1, pynucastro (Willcox & Zingale 2018; Smith et al. 2023), the solver-independent codes SkyNet (Lippuner & Roberts 2017) and WinNet (Reichert et al. 2023), and the JINA REACLIB rate database (Cyburt et al. 2010).

---

## 2. Data inventory and coverage

### 2.1 What the public record actually contains

Zenodo record 10.5281/zenodo.14873443 is the **reproducibility package** for Grichener et al. 2025, not a flux database. Its stated contents are the MESA stellar models used to set the parameter space, the training/validation/test sets, the trained NNN models, the test datasets, and the analysis and figure-generation scripts. The outer container is a single archive, `NuclearNeuralNetworks.zip` (≈49.1 GB), plus a `README.txt`. This reconciles cleanly with the paper's stated ~80 GB total: 80 GB is the uncompressed footprint — nine timesteps × (≈3 GB mesa_80 + ≈6 GB mesa_151) — and 49.1 GB is the zipped deposit, an unremarkable ~0.6 compression ratio on numerical arrays. The container is confirmed; the zip-internal breakdown and the on-disk format of the arrays (CSV, Parquet, or NumPy) remain a local-confirmation target.

The headline data are **(state, dt → composition + e_nuc + ε_ν) tuples** at **nine logarithmically spaced fixed timesteps from 10⁻⁶ s to 10² s**, with ≈1,048,576 ≈ 10⁶ combinations per network, for **mesa_80** (80 isotopes) and **mesa_151** (151 isotopes); a separate NNN was trained per timestep. Thermodynamics were drawn by Sobol quasi-random sampling over log T and log ρ within the regime box, with the per-point composition generated randomly to match the sampled Yₑ in 0.45–0.5. The held-out comparison set is ≈700 bbq outputs whose initial compositions are restricted to the isotopes present in the `approx21_cr60_plus_co56` network, chosen to enable a like-for-like comparison against the small net. The mesa_204 network is a future project target and is **not** present.

What the public set does **not** contain is decisive: no per-reaction gross f± , no signed net per-reaction flux φ, and no QSE/NSE equilibrium abundances. Every quantity the conservation architecture gates on must be derived or rebuilt externally.

### 2.2 What the on-request superset adds

The complete bbq runs — additional timesteps beyond the public nine, and datasets for extended density ranges beyond 10⁷–10⁹ g cm⁻³, ≈4 TB in total — are **available on request from the corresponding author**. This is a discretionary external dependency and a non-trivial 4 TB transfer, not a deposited fact, and it must be treated and scheduled as such. The superset adds finer/more timesteps and wider density coverage but still advertises neither fluxes nor equilibrium abundances.

### 2.3 Coverage matrix

| Needed quantity | In public Zenodo 14873443? | In on-request 4 TB? | Gap / action |
|---|---|---|---|
| Single-step (state, dt → dY) + e_nuc + ε_ν | **Yes** — 9 fixed dt, ~10⁶/net, mesa_80 & mesa_151 | Yes (more dt) | None for mesa_80/151; derive dY = X_final − X_init |
| Variable-dt data | Partial (9 discrete dt only) | **Yes** (extra timesteps) | Negotiate 4 TB; else new bbq runs (see §6) |
| Per-reaction gross f+ and f− | **No** | No | **Derive externally** (pynucastro) or re-instrument bbq |
| Signed net per-reaction flux φ (Target A) | **No** | No | **Derive/rebuild** (f+ − f−), or MESA `add_raw_rates` |
| QSE/NSE equilibrium abundances | **No** | No | **Build independent C(A,Z) solver** + pynucastro NSE cross-check |
| Trajectory sequences | Partial (same state across 9 dt is not a trajectory) | Closer (more dt) | Mostly **new bbq runs** / 4 TB |
| Off-trajectory / perturbed states | **Yes, implicitly** — Sobol deliberately includes off-trajectory compositions | Yes | Already covered by design |
| Real-MESA-track trajectories | **No** (Sobol space ≠ stellar tracks; MESA *models* present only to set bounds) | No | **New work**: extract core compositions from MESA runs |
| New-regime data (low-T ECSNe, low-ρ PPISNe) | **No** | Partial (extended ρ) | **New bbq runs** (§9) |
| mesa_204 data | **No** | No | **New bbq runs** (new network) |

---

## 3. The bbq/MESA generation pipeline

**What bbq is.** bbq (Farmer 2023; Zenodo 10.5281/zenodo.7585202; LGPL v2.1) is a Fortran one-zone burn calculator that wraps MESA's nuclear-network solver without modifying its underlying code. It burns a single zone at **constant T and ρ**, treating the burn as decoupled from stellar structure, and is pinned to MESA **r23.05.1**.

**Integrator.** bbq integrates the stiff abundance ODEs with the **Bulirsch–Stoer / Bader–Deuflhard** scheme (Deuflhard 1983), solving dX_i/dt = (A_i m_u/ρ)[−Σ_j(1+δ_ij)r_ij + Σ_{k,l} r_{kl,i}].

**Inputs.** The initial temperature, density, and composition of the zone, plus the choice of MESA softwired network (mesa_80, mesa_151, …).

**Native outputs.** The final composition {X_i}, the nuclear energy generation per unit mass e_nuc (erg g⁻¹), and the neutrino-loss term ε_ν (erg g⁻¹ s⁻¹). A MESA convention matters for downstream energy bookkeeping: the `net` module's `eps_nuc` **already has nuclear neutrino losses subtracted** (eps_nuc ≡ ε_nuc − ε_ν,nuc), while thermal neutrino losses (`non_nuc_neu`) come from the separate `neu` module. The exact bbq inlist control names, the output container (HDF5 versus text), and the column headers are **local-confirmation items**: direct reads of the bbq repository were blocked by an automated-access policy, so the pipeline description is corroborated from Grichener et al. and MESA documentation rather than the repo's own files.

**What must be post-computed.** bbq returns the net dY/dt-equivalent (via final abundances) and the energy terms, but **not** per-reaction signed flux φ, **not** gross f±, and **not** equilibrium abundances. Target A's φ and all kill-test quantities are post-processing products (§4). To emit per-reaction quantities natively instead, MESA's reaction-rate output can be enabled — `add_raw_rates`, `add_screened_rates`, `add_eps_nuc_rates`, `add_eps_neu_rates`, or `raw_rate <name>` for individual reactions.

**Parallelization and throughput.** Generation is embarrassingly parallel — each burning region computes independently; hundreds of isotopes in one zone run in a few minutes, and building a ~10⁶-sample set costs of order "few × 10⁵ CPU hours" (Grichener et al. §2.1).

**Failure modes.** Stiff-ODE non-convergence appears at the highest T/ρ and largest dt (bbq runtime grows with dt because larger compositional change demands more substeps), manifesting as solver step-count exhaustion governed by the standard MESA tolerances and maximum internal steps. The detailed-balance rate bug below is a *correctness* failure that does not crash the solver — it silently produces wrong equilibria.

**Reproducible campaign configuration.** Pin MESA r23.05.1 and a fixed REACLIB snapshot plus weak-rate tables; record the exact net file. MESA's standalone one-zone burn supports both fixed-(T,ρ) burns and arbitrary (T,ρ) histories (`read_T_Rho_history`, `T_Rho_history_filename`), the machinery bbq exposes; which of these controls bbq surfaces is a local-confirmation item.

---

## 4. Deriving the conservation, kill-test, and masking quantities

This is where Target A's φ and the mask's inputs come from. All flux work is gated by the artifact screen in §4.3.

### 4.1 Per-reaction gross f+ and f− (and net φ)

Use **pynucastro** built on the **same** REACLIB rates and tabulated weak rates (in T, ρYₑ) as MESA. pynucastro supplies nuclear partition functions, reverse rates by detailed balance, weak-rate-table support, NSE state determination, and electron screening. The workflow builds a `RateCollection`/`PythonNetwork` from `ReacLibLibrary().linking_nuclei([...])` matching the mesa_80/mesa_151 isotope list, and for each rate at a `Composition` and (T, ρ):

- `rc.evaluate_rates(rho, T, composition)` returns the per-rate molar flux (rate × density-power × Y-products × screening) for every rate.
- Each reaction's forward and reverse legs form a `RatePair`; evaluate both directions to obtain the **gross f+ (forward) and f− (reverse)**, with **net φ = f+ − f−**. Screening enters via `evaluate_screening`/`get_screening_map` (use symmetric screening to match aprox-style nets where appropriate).

The route is valid **only if pynucastro and MESA use matching REACLIB version, weak-rate tabulation, and screening prescription** — otherwise φ diverges from the abundance target the network must reproduce. Validate by reproducing a sample of bbq net dY/dt before trusting φ. (The exact pynucastro API entry points should be checked against current pynucastro documentation; this is a forward verification item, listed in §11.)

### 4.2 Independent C(A,Z) QSE/NSE equilibrium reference

Implement the Hix & Thielemann formalism (1996, ApJ 460:869; 1999, ApJ 511:862; cross-validated with Hix et al. 2007, ApJ 667:476). The QSE abundance of nucleus (A,Z) in equilibrium with ²⁸Si is

  Y_QSE(A,Z) = [C(A,Z)/C(²⁸Si)] · Y(²⁸Si) · Y_n^(N−14) · Y_p^(Z−14),

with

  C(A,Z) = [G(A,Z)/2^A] · (ρN_A/θ)^(A−1) · A^(3/2) · exp(B(A,Z)/k_B T),  θ = (2πm_u k_B T/h²)^(3/2),

where G is the partition function, B the binding energy, and N_A Avogadro's number. Two independent implementations are recommended: a hand-coded C(A,Z) with AME2020 masses and partition functions, and pynucastro's `NSENetwork.get_comp_nse(rho, T, ye, use_coulomb_corr=True)` for full NSE as a cross-check. Agreement between them in the NSE limit validates the solver before any QSE-group work. NSE is the high-temperature limit; QSE is NSE with the inter-group balance constraints relaxed, a useful approximation above ~3 GK.

### 4.3 The detailed-balance / phase-space artifact screen (gates everything)

The failure mode is documented and severe. Grichener et al. 2025 Appendix B — and the corresponding MESA GitHub Issue #575, filed by Grichener, which names the offending reaction `r_neut_nuet_he4_he4_to_h3_li7` — found that MESA computed the reverse rates of endo-energetic reactions involving more than two reactants and/or products from detailed balance while **omitting a phase-space factor** tied to the number of particles. For the four-particle reaction n + n + ⁴He + ⁴He → ³H + ⁷Li this made the MESA rate roughly **20–24 orders of magnitude larger** than the literature value (Malaney & Fowler 1989). The bug is fixed in current MESA, but any rate library or version used for flux work must be re-screened. The screen, run before any flux-based analysis:

1. For every reverse rate with more than two reactants/products, verify the phase-space factor is present.
2. Compare equilibrium composition across network sizes; tritium-bearing channels in the medium networks were exactly what swung the published equilibria, so flag any net whose equilibrium shifts when tritium channels are added.
3. Spot-check the four-particle reaction against Malaney & Fowler 1989 — a 20–24 order-of-magnitude discrepancy is the diagnostic signature.
4. Independently recompute reverse = forward × (detailed-balance factor from partition functions) with pynucastro and compare to the rate-library reverse.

Any reaction failing these is masked out of κ_r/δ_r and the flux losses. The screen targets **strong, >2-body, endo-energetic reverse rates only** — it never touches weak reactions, consistent with the equilibrium-mask rule.

### 4.4 Cancellation and equilibrium-deviation diagnostics (κ_r, δ_r)

Both are per-sample post-processing passes over the gross fluxes and the equilibrium reference:

- **Cancellation ratio** κ_r = |f+ − f−| / (f+ + f−) ∈ [0,1]. As κ_r → 0 a reaction sits in near-perfect forward/reverse balance (QSE), where the net flux is a small difference of large numbers and is numerically fragile — precisely the reactions the conservation-by-construction head and its mask must handle with care.
- **Equilibrium deviation** δ_r = max_i |Y_i − Ȳ_i| / Ȳ_i, where Ȳ_i is the QSE/NSE reference from §4.2; δ_r quantifies how far a sampled state is from equilibrium for the species linked by reaction r.

---

## 5. Sampling design

### 5.1 The constrained-composition geometry

A composition is a probability vector summing to one, so it lives on the (n−1)-dimensional probability simplex. One further independent weighted linear equality — the electron-fraction constraint Yₑ = Σ(Zᵢ/Aᵢ)Xᵢ — reduces this to an **(n−2)-dimensional bounded convex polytope** (n−2 = 78 for mesa_80, 149 for mesa_151). Grichener et al. correctly noted that quasi-random sampling is not directly applicable to non-independent abundances that must sum to unity, and fell back to generating compositions randomly to match each sampled Yₑ. That ad-hoc step is the weakest link in the baseline pipeline and the point at which the Sobol low-discrepancy guarantee is lost.

### 5.2 Three candidate samplers

- **Dirichlet sampling.** Dirichlet(α = 1) is exactly uniform on the simplex (realizable from n uniforms by the sorted-spacings construction, Willms 2021), and concentration α ≠ 1 gives controlled bias toward sparse, simplex-edge/few-isotope compositions (small α) or dense, iron-peak-spread compositions (large α) — useful for deliberately spanning unphysical states. But conditioning on a *second* weighted linear equality has **no closed form**; the conditional uniform distribution on the (n−2)-polytope is not in general a Dirichlet. *Excellent for controlled-bias bulk generation; cannot natively honor Yₑ exactly.*
- **Sobol-on-simplex via a cube→simplex transform.** Pillards & Cools (2005) give five cube-to-simplex mappings with a Koksma–Hlawka guarantee that the convergence order can be preserved under suitable conditions, and Basu & Owen (2015) achieve near-optimal discrepancy on the two-dimensional triangle. But Basu & Owen (2016) show that *symmetric* simplex maps can destroy bounded Hardy–Krause variation, forfeiting those rates. *Preserves low-discrepancy only with a carefully chosen non-symmetric transform; the equality is handled by reducing to the (n−2)-polytope first, then mapping. The positive QMC results are two-dimensional and must not be over-generalized to n = 78–149.*
- **Constrained QMC on the polytope (hit-and-run / billiard walk).** volesti-style billiard-walk samplers (Gryazina & Polyak 2012) target uniform-on-polytope for arbitrary linear constraints and converge faster than hit-and-run, but they are MCMC samplers with **no proven QMC star-discrepancy bound**. The Dirichlet-Rescale (DRS) algorithm (Griffin et al. 2020) is shown by Willemsen et al. (2025) to be non-uniform under multiple constraints; their Dirichlet-Rescale-Constraints (DRSC) fix restores uniformity. *Use only when low-discrepancy is being sacrificed deliberately.*

### 5.3 Recommended generator

A two-stage hybrid. **(1)** Draw Yₑ and (log T, log ρ) jointly with a Sobol sequence over the three-dimensional box, preserving the thermodynamic low-discrepancy property the baseline relied on. **(2)** For each Yₑ, sample the composition on the (n−2)-polytope: for the *bulk* broad-coverage set, use **Dirichlet-with-DRSC-projection** — draw Dirichlet(α) with α swept to span sparse→dense states, then apply a minimal DRSC-style projection to the Yₑ hyperplane (cheap, embarrassingly parallel, spans unphysical states); for a *low-discrepancy core* (~20% of the broad set), drive a **Pillards–Cools non-symmetric cube→polytope transform** with Sobol points, accepting that exact star-discrepancy on a >2-D constrained polytope is unproven (§11). This is a concrete, defensible replacement for the baseline's "generate randomly" step.

### 5.4 Reconciling "unphysical helps" with the Sobol→real transfer risk

Grichener et al. found that broad, deliberately unphysical composition sampling was *required*: narrowing the parameter space to typical compositions from the inner regions of MESA-evolved massive stars produced NNNs with poor performance, because broad coverage substantially improves generalization. The complementary failure mode is shown by the DeePODE line of work (Yao et al. 2024; nuclear adaptation Zhang et al. 2025): manifold-only sampling along real trajectories generalizes poorly to test points that deviate from the manifold. Both literatures point to a **mixture** — global Monte-Carlo/QMC coverage plus trajectory-evolved points on the dynamically important manifold.

A precise caveat governs how strongly this can be claimed. The literature **motivates** the mixture but does **not** establish the specific transfer worry this project must guard against: Grichener shows broad beats narrow on its *own* Sobol test set, not transfer to the thin real-MESA manifold, and DeePODE shows manifold-only fails *off*-manifold, which does not by itself establish the converse. The Sobol→real transfer ratio is therefore a quantity to **measure locally** (§7), not a settled result.

The resolution is a division of labour by data subset. The broad/unphysical bulk exists to teach the *function class* — the network must represent dX/dt correctly even off-manifold, because pushforward rollouts and eventual hydrodynamic coupling will visit perturbed states. The trajectory-aware subset exists to densify the *thin correlated manifold* where validation Yₑ error is actually scored. At training time, **importance reweighting** up-weights samples near the real manifold and near the iron-peak weak-rate nuclei, letting one dataset serve both generalization and on-manifold accuracy without regenerating data. The monitored quantity that says whether the mix is right is the real-track-versus-Sobol 99th-percentile Yₑ-error ratio, with a retrain trigger at R > 3.

### 5.5 Adaptive and active-learning strategies, head to head

- **(a) DeePODE / Evolutionary-Monte-Carlo-Sampling (EMCS)** — Yao et al. 2024 (arXiv:2401.01220), nuclear adaptation Zhang et al. 2025 (arXiv:2504.14180). Mechanism: global Monte-Carlo sampling, then evolve each seed along its local ODE trajectory at the system's characteristic timescales, concentrating points in the early stiff stage. The procedure has three sequential steps — range estimation, MC sampling within a hypercube plus filtering, and evolution-augmented generation — but each seed is integrated **once**, with no generational resampling loop, so the strategy stays embarrassingly parallel. The nuclear adaptation used a 13-isotope α-network (⁴He…⁵⁶Ni, overlapping the silicon group), a Box–Cox transform (λ = 0.1, introduced in the DeePODE paper) instead of a logarithm to handle mass fractions down to 𝒪(10⁻²⁵), and temperature-gradient filtering retaining ~75–100% of high-gradient (stiff) samples versus ~8–10% of low-gradient samples, yielding ~17M (3-species) / ~28M (13-species) points and ≲1% composition accuracy with a ~2.6× CPU speedup and a temperature-thresholded deployment sustaining neural-network utilization above 75%. *Cost:* cheap — the same embarrassingly-parallel burn already costed, plus checkpoint storage. *Effort:* low (it is the trajectory-storage scheme of §6 plus stiff-region filtering). *QSE suitability:* high, since concentrating samples in the early stiff stage maps onto the cancellation window. **Important transfer caveat:** the ≲1% figure is *composition* accuracy on an α-network with **no weak reactions and no Yₑ**, so it does not exercise the Yₑ-controlling weak physics that is this project's entire point; its filter bands are tuned to white-dwarf combustion and need local re-tuning.
- **(b) Deep-ensemble-variance active learning** — CODES (Janssen, Sulzer & Buck 2024, arXiv:2410.20886). A five-member deep ensemble gives a generally reliable uncertainty estimate (predicted uncertainty correlates positively with error), and latent-ODE surrogates show higher errors at larger gradients; ensemble variance then serves as the acquisition signal for new (T, ρ, X, dt) points. *Cost:* dominated by training the ensemble members plus a new bbq burn per acquired point; the burns are cheap, but the loop is serial across acquisition rounds, eroding the embarrassingly-parallel advantage. *Effort:* medium-high. *QSE suitability:* high but indirect — variance spikes naturally in the cancellation window.
- **(c) Stiffness-/timescale-adaptive density.** Deterministically over-sample the QSE-cancellation window and the Yₑ-controlling iron-peak nuclei using a physics prior (Hix & Thielemann; Guidry partial-equilibrium timescales). *Cost:* lowest — no retraining loop, just a non-uniform sampling density. *Effort:* low. *QSE suitability:* highest and most controllable; the cheapest way to buy cancellation-window accuracy and the default densification.

**Verdict.** Combine (c) as the cheap deterministic prior with EMCS (a) for manifold and stiffness coverage; reserve ensemble-variance active learning (b) for a single late-stage refinement round targeted at whatever the validation test flags. The trajectory-aware component is *EMCS-style*; the full three-way mixture is not itself "exactly EMCS."

### 5.6 Budget split

A starting allocation, moved only by the validation test in §7: **~60% broad Sobol+Dirichlet** (function-class coverage, deliberately unphysical, preserving the Grichener finding); **~25% trajectory-aware** (EMCS-evolved seeds plus real-MESA-seeded burns, for manifold fidelity); **~15% active/stiffness densification**, of which ~10% is the cheap deterministic QSE-window + iron-peak prior (c) and ~5% is reserved for one ensemble-variance round (b).

### 5.7 Moving regime boundaries to sample deliberately

Three boundaries must be sampled by design rather than left to chance (physics from Hix & Thielemann 1996/1999):

- **The QSE-cancellation window.** Densify it. Guidry (2011, arXiv:1112.4778) identifies the pathology precisely: the net flux in a forward–reverse reaction pair tends to zero as the system approaches equilibrium, so the net is the difference of two large numbers and errors blow up. The signed-net-flux architecture lives or dies in this window. The constant-temperature study of Hix & Thielemann 1996 spans roughly 3.5–5 GK; the lower freeze-out edge of the window is a project working assumption, not a sourced threshold.
- **The NSE transition.** QSE holds for temperatures above approximately 3 GK (Hix & Thielemann 1999, "Silicon Burning II," ApJ 511:862); sample across the upper temperature edge so the emulator learns the approach to full equilibrium.
- **The Yₑ-dependent silicon/iron-peak group-merger boundary** — the key Hix & Thielemann 1996 result, and strongly neutronization-dependent. At Yₑ = 0.498 a single QSE group has formed (within 10%) by the time the silicon-group mass fraction reaches X(Si) ≈ 0.85; at Yₑ = 0.46 the iron-peak group reaches 90% of its silicon-QSE abundance only once the silicon-group mass fraction has fallen to 0.25–0.30 (two condition-specific values, for T₉ = 5.0/ρ = 10⁷ and T₉ = 3.5/ρ = 10⁹, not a continuous band). The implication is that **sampling density in composition space must be correlated with Yₑ** — the group structure, and hence the correct equilibrium mask, changes shape across the 0.45–0.5 band, and uniform-in-Yₑ sampling under-resolves the low-Yₑ merger delay. The iron-peak group stretches from roughly A = 45–50 to the top of the network (Ge, A ≈ 78); the A ≈ 45–65 band used for densification is a project simplification picking out the LMP-active iron-peak nuclei.

---

## 6. Data shapes

### 6.1 Variable-Δt: dense cumulative trajectories, with the right cost framing

The baseline trained a separate network per timestep over nine fixed dt. Generating nine independent integrations per state would be wasteful, because bbq's Bulirsch–Stoer integrator already passes through every intermediate time en route to 10² s. The recommended canonical shape is therefore the **dense cumulative trajectory**: run one burn and checkpoint it, then sub-sample any dt.

- **Marginal cost multiplier** of checkpointing one burn at more times: ≈1.0–1.3 versus a single-endpoint burn, since the extra cost is additional integrator output, not additional burns — contrast the naive ≈N_dt multiplier of running independent integrations for each dt.
- **Checkpoint density:** ~16–24 log-spaced times across [10⁻⁶, 10²] s (≈2–3 per decade), over-resolving the baseline's nine so the single variable-Δt head and a latent-ODE upgrade can interpolate dt accurately, especially in the early stiff stage where EMCS also concentrates points.

The cost framing must be stated carefully, because the cheapness is marginal and applies only to **new** burns. The public set stored **only its nine checkpoints**; the dense intermediate states were not saved. Obtaining 16–24 checkpoints for the existing ~10⁶ Sobol states therefore requires **either** the on-request 4 TB superset — which exists precisely to hold finer/more timesteps, but whose sufficiency for this purpose is unconfirmed until inspected — **or** re-running all ~10⁶ burns, a fresh campaign costed at "few × 10⁵ CPU-hr" (6–29 node-months, §8). Dense trajectory data is consequently a *needs-new-bbq-runs / negotiate-the-4-TB-set* item, not a free retrofit of the public data. Whether bbq can cheaply emit dense intermediate checkpoints from a single stiff integration, and whether one burn to 10² s resolves the early stiff stage down to 10⁻⁶ s finely enough to checkpoint accurately, are local-confirmation items (§11).

- **Storage** scales the public footprint (≈3 GB mesa_80 + ≈6 GB mesa_151 per checkpoint) to 16–24 checkpoints: ≈48–72 GB for mesa_80 and ≈96–144 GB for mesa_151, i.e. **≈0.14–0.22 TB for both networks** at training precision (budget more for float64-at-rest or additional per-checkpoint state). This sits comfortably inside the 4 TB envelope either way.
- **How the heads consume it.** The single variable-Δt head trains on (state, log dt) → (state(dt), e_nuc, ε_ν) tuples drawn from arbitrary checkpoints; a latent-ODE upgrade consumes the *same* trajectories as continuous-time supervision, integrating the learned latent vector field between checkpoints (the MACE pattern, trained with torchode). Storing cumulative trajectories is thus forward-compatible with both heads and is the recommended canonical shape.

### 6.2 Trajectory, rollout, and off-trajectory data

**How rollout-stable neighbour surrogates generated their data.** Chemulator (Holdship et al. 2021, A&A 653:A76) trained a single-timestep map yet stayed stable over 1000 iterations — its log-scaled-temperature MSE rose only from 3×10⁻³ after one step to 6×10⁻³ after a thousand (single-step MSE 1.7×10⁻⁴), running ~50,000× faster than the time-dependent model — via a **training-time noise layer** that exposed the network to perturbed inputs resembling its own accumulated error; its dimensionality reducer was an autoencoder alone (33→8 variables). MACE (Maes et al. 2024, ApJ 969:79) paired an autoencoder with a **trainable latent ODE** integrated and supervised across the rollout with torchode, outperforming its classical analogue by a factor of ≈26 on one-dimensional AGB-outflow circumstellar-envelope models (a 468-species RATE12-derived network). van de Bor et al. 2025 (arXiv:2503.10736) is the cautionary tale — a DeepONet emulator of the Grackle cosmological cooling/chemistry solver is prone to instability from accumulated prediction error — and motivates a pushforward-first stance. Ono & Sugimura 2025 (arXiv:2508.16114) added a **timescale-based update** that rescales a long-step prediction to a short step by the variable's characteristic timescale, avoiding the failure where, at tiny dt, the time variation is dominated by error rather than physical evolution — directly relevant to the project's smallest dt (10⁻⁶ s). The pushforward trick (Brandstetter et al. 2022, MP-PDE, arXiv:2202.03376) unrolls the solver K steps, feeds the model its own output, and backpropagates only the last step, improving stability and ensuring the perturbations match the rollout error distribution; K = 2 is standard, with K = 2–4 corroborated.

**QSE-respecting off-trajectory perturbations.** The data-side counterpart of noise injection must not push equilibrated species off-manifold, because within a QSE group the intra-group abundances are algebraically slaved to the group-controlling abundances and a few thermodynamic variables. The recipe: (1) compute QSE-group membership for each stored state via the Guidry partial-equilibrium prior used by the mask; (2) inject noise **only into non-equilibrated channels** — the light-particle pool, the weak-reaction-controlled Yₑ, and species whose net flux is not near catastrophic cancellation; (3) for equilibrated groups, perturb only the group-controlling coordinates and re-impose the QSE relation, so the perturbed state remains a physically reachable point. This is consistent with the project rules — the mask acts on the latent flux and never on weak reactions, and Yₑ is free to evolve, so perturbing the weak-controlled Yₑ is legitimate.

**Single-step-versus-sequence data mix.** Drawn entirely as a sampling policy over the stored cumulative trajectories, adding no new burns beyond §6.1:

- **~70% single-step pairs** (state, dt) → state(dt), from stored trajectories at all dt — the bulk supervision and what the variable-Δt head fundamentally learns.
- **~20% K = 2–4 pushforward sequences** from consecutive checkpoints, for unrolled training — the primary rollout lever.
- **~10% QSE-respecting perturbed off-trajectory states** paired with their true one-step evolution — the noise-injection counterpart, restricted to non-equilibrated channels.

---

## 7. Validation and solver-independent cross-checks

**Held-out real-MESA-track validation (the Sobol→real transfer test).** Hold out entire real MESA pre-collapse trajectories (15–25 M⊙ progenitors from the public models), never used in training. At each held-out state and dt, measure the per-step Yₑ error and report its 99th percentile over the real-track distribution alongside the matched 99th percentile over the Sobol test distribution. The ratio **R = (real-track 99th-pct) / (Sobol 99th-pct)** is the transfer metric, with a **retrain trigger at R > 3**; when triggered, shift budget toward the trajectory-aware fraction and re-run targeted densification rather than abandoning broad Sobol. Use a *separate* set of real tracks as EMCS seeds — never seed from and validate on the same trajectory.

**The error-accumulation slope — the single biggest open lever.** On full real-track rollouts, also regress log|cumulative Yₑ error| against log N. A slope of ≈1 (systematic accumulation) versus ≈0.5 (random walk) sets the per-step gate, and at fixed N the two models differ by ≈√N. At N ≈ 1.6×10³ this is roughly a factor of 40 — about 3×10⁻⁶ systematic versus ≈1.25×10⁻⁴ random-walk; at N = 10⁴ it is a factor of 100 — 5×10⁻⁷ systematic versus 5×10⁻⁵ random-walk. No external paper settles which model applies to silicon burning; it must be measured locally, and it reshapes the gate, the required pushforward depth, and the single-step fraction.

**Solver-independent cross-checks.** Because bbq wraps MESA's Bulirsch–Stoer solver, a systematic solver bias would be invisible to internal validation. Cross-check a sample of bbq states against **SkyNet** (Lippuner & Roberts 2017, ApJS 233:18; a deliberately different first-order implicit backward-Euler scheme) and **WinNet** (Reichert et al. 2023, ApJS 268:66; implicit Euler and Gear's method with Newton–Raphson, plus an NSE solver descending from high T — a useful check on the NSE-transition boundary of §5.7). Agreement across all three solvers to within the per-step Yₑ gate certifies that the training labels themselves are not solver-limited before the emulator is blamed. (The precise method descriptions of these two codes are a forward verification item, §11.)

---

## 8. Cost, throughput, storage, and format

### 8.1 Cost and throughput model

| Quantity | Value | Basis |
|---|---|---|
| Per-sample cost | ~0.1–0.5 CPU-hr | project figure |
| Node capacity | ~17,000 core-hr/month (24-core node) | project figure |
| Samples/month/node | ~34,000–170,000 | 17,000 ÷ (0.1–0.5) |
| Fresh 10⁶ grid (one net) | ~1×10⁵–5×10⁵ CPU-hr | per-sample × 10⁶; matches Grichener "few × 10⁵ CPU hours" |
| Wall-time on one node | ~6–29 months | (1–5)×10⁵ ÷ 17,000 |
| Cluster threshold | A fresh 10⁶ grid is impractical on one node; needs a multi-hundred-core allocation to finish in weeks | derived |

The model carries no dollar figures: the relevant context is an institutional cluster allocation, where CPU-hours and node-months are the right currency and cloud on-demand rates would mislead. The implication is the sequencing already stated — a from-scratch 10⁶-grid is a cluster-scale, multi-month campaign, so Year-1 lives on the public sets, derives all kill-test quantities immediately (those derivations are CPU-cheap and embarrassingly parallel and need no new burns), negotiates the 4 TB superset early, and reserves fresh burns for mesa_204 and new regimes.

### 8.2 Storage at scale

The public set is ~80 GB and the bbq superset is ~4 TB. Adding per-reaction φ, f±, and equilibrium references multiplies per-sample storage by the reaction count (mesa_80 has hundreds of reactions, mesa_151 of order 10³), so a fully fluxed mesa_151 set can dwarf the abundance set. Plan for **tens of TB** if storing full per-reaction tensors, and mitigate by storing only the signed net φ plus a sparse subset of f± for reactions whose κ_r falls below a threshold, recomputing the rest on demand.

### 8.3 On-disk format, schema, provenance, versioning

A columnar/array store — **HDF5 or Parquet** with chunking and compression (blosc/zstd) — with HDF5 suiting the dense (sample × reaction) flux tensors and Parquet the tabular (state, dt, scalars) layer. Store abundances and fluxes as **float64 at rest** (φ is a difference of large numbers and κ_r needs the precision), with a **float32** training-ready mirror. The per-sample schema is {sample_id; net_name; T; ρ; Yₑ_init; X_init[Niso]; dt; X_final[Niso]; e_nuc; ε_ν; φ[Nreac]; f_plus[Nreac]; f_minus[Nreac]; κ_r[Nreac]; Y_QSE[Niso]; δ_r; artifact_flags[Nreac]}. **Provenance is mandatory** — MESA version (r23.05.1), bbq commit/Zenodo DOI (7585202), REACLIB snapshot ID, weak-rate table set and precedence, pynucastro version, screening prescription, Sobol seed, and the artifact-screen pass/version — without which φ is unreproducible. Versioning uses content-hash or DVC/git-LFS pointers and never overwrites; new derivation versions are appended so the artifact-screen fix stays traceable.

### 8.4 Preprocessing and normalization

For signed quantities (φ, dY) use a **signed-log / asinh transform**. The borrowed NuGNN convention (Kim et al. 2026, arXiv:2606.04491) is sign(ΔX)·(C + log₁₀(|ΔX/X|)) with C = 17 — about the maximum magnitude of log₁₀(|ΔX/X|) when |ΔX/X| < 1 — with values below 10⁻¹⁵ clipped to zero; the additive shift makes the log positive while preserving magnitude ordering before the sign is applied, mapping the label into [−1, 1]. For net flux the convention is sign(f)·log₁₀(|f|) with no additive constant. An asinh(x/x₀) form is an equivalent smooth alternative that avoids the clip. After the signed-log, standardize each channel (per-isotope, per-reaction) to zero mean and unit variance using **train-split statistics only**. Keep the math in float64 — especially φ and κ_r — and cast back to float64 from the network's float32 I/O before reconstructing X_{t+Δt} = X_t + ΔX.

### 8.5 Weak-rate tables and off-grid behaviour

MESA's weak rates are used in order of precedence Langanke & Martínez-Pinedo (2000) > Oda et al. (1994) > Fuller et al. (1985), tabulated in (ρYₑ, T) on a coarse grid (1 ≤ log ρYₑ ≤ 11, step 1; 7 ≤ log T < 10.5, step ~0.25), assuming complete ionization. Within the regime box (log T 9.2–9.9, log ρYₑ ≈ 6.65–8.70) the data are **on-grid for the weak tables and below the thermonuclear-rate cap** (MESA caps thermonuclear rates at their log T = 10 value rather than extrapolating, and the weaklib edge-blends are documented-unphysical). The off-grid concern is real only for the **future regime extensions** of §9 (low-T ECSNe, low-ρ PPISNe), where the box leaves the tabulated domain.

### 8.6 Leakage-safe train/validation/test splits

Split by **trajectory ID**, with all steps of a trajectory assigned to the same fold, to prevent trajectory-level leakage. To prevent timestep-level leakage, either keep per-dt splits aligned — the same underlying (T, ρ, X) initial points assigned to the same fold across all timesteps — or hold out entire (T, ρ, X) initial conditions across all timesteps. Reserve a **matched-context test partition** whose initial compositions are restricted to the `approx21_cr60_plus_co56` isotopes (the ≈700-sample protocol) for an apples-to-apples comparison against the published NNN baseline. Stratify the folds across the Sobol (T, ρ, Yₑ) volume so each fold spans the full parameter space.

---

## 9. New-regime data roadmap

Prioritized by scientific leverage per CPU-hour; a fresh ~10⁶-grid is ~6–29 node-months on a single 24-core node.

| Priority | Regime | Conditions | Why / data needed | Rough cost |
|---|---|---|---|---|
| **P1** | mesa_151 fine-tuning sets (size-transfer test) | Same Si box | *Modest* sets to test mesa_80→mesa_151 transfer; fine-tune rather than regenerate a full grid; reuse existing public data first | ~10⁴–10⁵ CPU-hr (0.5–6 node-months) |
| **P2** | Oxygen burning | T ≈ 1.5–2.6 GK, just below the Si box | Extends the temporal domain backward; same isotopes, lower-T edge — a cheap extension of the existing networks | ~1–5×10⁵ CPU-hr per net (6–29 node-months) |
| **P3** | ECSN (electron-capture SN) | ONe core, Yₑ ≈ 0.493–0.499 at O-ignition, central ρ ≳ 10¹⁰ g cm⁻³ — lower T, higher ρ than the Si box | Needs density coverage beyond 10⁷–10⁹ → the **4 TB superset's extended density is the enabler**; electron capture on ²⁰Ne, ²⁴Mg dominates Yₑ → high LMP loss weight | ~1–5×10⁵ CPU-hr per net; **partly satisfiable from the 4 TB set without new burns** |
| **P4** | PPISN / PISN | T ≈ 1.5–2.2 GK (PPISN O-shell) to ~3–5 GK (PISN explosive O-burn), ρ ≈ 10³–5×10⁵ g cm⁻³ — far lower density | Lowest-ρ regime; requires extending below 10⁷ g cm⁻³, a genuinely new grid with no overlap with public/4 TB density coverage; lowest overlap with the Si surrogate | ~1–5×10⁵ CPU-hr per net (6–29 node-months); new allocation |
| **P5** | mesa_204-scale sets | Si box, 204 isotopes | Future network target; per-sample cost and storage scale with isotope count (≥1.3× mesa_151); defer until the mesa_151 surrogate is validated | >5×10⁵ CPU-hr (>29 node-months) |

The negotiated 4 TB set sits on the critical path twice: it supplies the finer/more timesteps that the dense trajectories of §6 need without new burns (if sufficient), and the extended density coverage that P3's high-ρ edge requires. Because it is a discretionary external dependency, negotiate it early — its absence forces expensive re-generation. (The ECSN/PPISN/PISN T/ρ/Yₑ figures are a forward verification item, §11.)

---

## 10. Prioritized generate/derive/build plan and staged recommendations

### 10.1 Generate vs derive vs build

| # | Data product | Tag | Effort | Cost |
|---|---|---|---|---|
| 1 | mesa_80/151 (state, dt→dY) + e_nuc + ε_ν, 9 dt | **already-public** | download | ~80 GB |
| 2 | Extra-timestep / extended-ρ bbq superset | **available on request (discretionary)** | email corresponding author; negotiate transfer early | 4 TB transfer/storage |
| 3 | Signed net φ per reaction (Target A) | **needs-new-code** (derive from public abundances via pynucastro) or re-instrument bbq | medium–high | CPU-cheap, embarrassingly parallel |
| 4 | Gross f+, f− per reaction | **needs-new-code** (derivable from public via pynucastro) | medium | CPU-cheap |
| 5 | QSE/NSE equilibrium reference Y_QSE(A,Z) | **needs-new-code** (independent C(A,Z) solver + pynucastro NSE cross-check) | medium–high | CPU-cheap |
| 6 | Detailed-balance / artifact screen | **needs-new-code** (gates 3–5) | medium | CPU-cheap |
| 7 | κ_r and δ_r per reaction/sample | **derivable** (from 3–5) | low | CPU-cheap |
| 8 | Variable-dt / dense trajectory sequences | **needs-new-bbq-runs** (unless the 4 TB set suffices) | high | cluster-scale or 4 TB |
| 9 | Real-MESA-track trajectories | **needs-new-bbq-runs + new MESA runs** | high | cluster-scale |
| 10 | mesa_204 dataset | **needs-new-bbq-runs** | very high | full fresh 10⁶ grid (~1–5×10⁵ CPU-hr) |
| 11 | New-regime (low-T ECSNe, low-ρ PPISNe) | **needs-new-bbq-runs** | high | cluster-scale |
| 12 | HDF5/Parquet schema + provenance + leakage-safe splits | **needs-new-code** (infrastructure) | medium | storage as above |

**Recommended order:** 1 → 6 → 4 → 3 → 5 → 7 — derive every kill-test quantity on the existing public abundances first, gated by the artifact screen — while in parallel starting 2 (negotiate the 4 TB set) and 12 (infrastructure), and deferring 8–11 (new burns) until a cluster allocation is secured.

### 10.2 Staged execution with explicit thresholds

- **Stage 0 — fix the sampler and the trajectory storage (before any new campaign).** Replace the baseline's ad-hoc per-Yₑ random composition with the two-stage Sobol(thermo) + Dirichlet-with-DRSC-projection scheme of §5.3, reserving ~20% for a non-symmetric Pillards–Cools Sobol→polytope core. Design bbq output for **dense cumulative trajectories** (16–24 log-dt checkpoints). *Benchmarks:* the marginal trajectory-generation multiplier must stay ≤1.3× the single-endpoint grid, and storage ≤~0.22 TB for both networks.
- **Stage 1 — generate the mixture set (one node-scale campaign, ~6–29 node-months for 10⁶ states).** Allocate 60% broad Sobol+Dirichlet / 25% trajectory-aware (EMCS-style + real-MESA seeds) / 15% stiffness-active (10% deterministic densification, 5% reserved), and build the 70% single-step / 20% K = 2–4 pushforward / 10% QSE-respecting-perturbed data mix as a sampling policy over the stored trajectories.
- **Stage 2 — validate and adapt.** Run the Sobol→real validation test of §7, measuring R and the error-accumulation slope; **if R > 3, retrain**, shifting ~10 percentage points of budget from broad Sobol to trajectory-aware and densification and re-running one targeted ensemble-variance round. Run the SkyNet + WinNet cross-checks on a label sample; agreement within the per-step Yₑ gate is the go/no-go for trusting bbq labels.
- **Stage 3 — phase out to new regimes** in order P1 → P2 → P3 → P4 → P5, each gated on the prior phase passing its validation test. Negotiate the 4 TB superset now, as it is prerequisite for both Stage-0 trajectory data and Stage-3 P3.

**Benchmarks that change the plan:** R > 3 → rebalance budget; error-accumulation slope ≈1 (systematic) → tighten the per-step gate to 3×10⁻⁶ and add pushforward steps; slope ≈0.5 (random walk) → the gate relaxes toward ~5×10⁻⁵ and the single-step fraction can rise; the QSE-window 99th-percentile flux error dominating → increase the deterministic densification (c) before paying for ensemble active learning (b).

---

## 11. Open items: what only a local experiment or confirmation can settle

The literature resolves several questions and leaves a hard residue. **Resolved by the literature:** unphysical sampling helps (Grichener); single-step emulators drift under rollout, with the cross-domain fixes being a training-time noise layer, a trained iterative update, and the pushforward trick; QMC can preserve low-discrepancy on a simplex only partially — the O(log N / N) rate is proven for the two-dimensional triangle and symmetric transforms degrade it.

**Requires a local numerical experiment.**

1. **The error-accumulation slope** (systematic ≈1 versus random-walk ≈0.5) — the single biggest open lever, moving the per-step gate by ≈√N. *Experiment:* roll out the trained emulator on held-out real tracks and regress log|cumulative ΔYₑ| against log N.
2. **Whether star-discrepancy is preserved on the (n−2)-polytope at n = 78–149** — the verified QMC theory is two-dimensional only, and conditioning a Dirichlet on a weighted linear equality has no closed form. *Experiment:* compute the empirical discrepancy / integration error of the chosen Sobol→polytope transform against a reference at the real isotope count.
3. **Whether QSE-respecting perturbation keeps states on-manifold.** *Experiment:* perturb equilibrated-group coordinates, re-impose QSE, integrate one bbq step, and confirm the perturbed-state error does not exceed the on-trajectory error.
4. **The Sobol→real transfer ratio R** — the literature only motivates the mixture; the transfer worry is a local measurement.
5. **mesa_80 → mesa_151 size-transfer feasibility** with modest fine-tuning sets — no literature precedent for this specific transfer.
6. **The κ_r distribution and the stoichiometric-matrix condition numbers** across the box — only a numerical experiment characterizes the cancellation severity the architecture must absorb.

**Requires local engineering confirmation.**

- The **zip-internal contents and on-disk format** of Zenodo 14873443 (CSV/Parquet/NumPy); the outer container is confirmed, the contents are not.
- bbq's **exact output columns and inlist control names**, including whether bbq can cheaply emit dense intermediate checkpoints from one stiff integration and whether a single burn to 10² s resolves the early stiff stage down to 10⁻⁶ s finely enough — both require a local bbq run.
- MESA r23.05.1 **rate values at the box corners** and the actual interpolation/edge behaviour — requires the local install.
- The **pynucastro–MESA REACLIB / weak-table / screening match**, on which the entire external-φ route depends — validate by reproducing bbq net dY/dt before trusting φ, and confirm the pynucastro API entry points (`evaluate_rates`, `RatePair`, `NSENetwork.get_comp_nse`, `get_screening_map`) against current documentation.
- Whether the **4 TB superset's density/timestep coverage is sufficient** for ECSN and variable-Δt — verifiable only after transfer.
- Confirm against source PDFs: the **SkyNet/WinNet method descriptions**; the **ECSN/PPISN/PISN regime numbers**; the nuclear DeePODE paper's λ = 0.1-down-to-𝒪(10⁻²⁵), 17M/28M datapoint counts, and gradient-retention percentages; and the **NuGNN signed-log/conservation details**.

---

## 12. Conclusion

The training-data layer is the project's first real cost-and-risk gate, and the synthesis above sorts it cleanly into what is cheap and reversible versus expensive and irreversible. The public Grichener data are enough to start, but only because the work that can begin immediately — downloading the public sets and deriving every kill-test quantity (the signed net flux φ that is Target A, the gross fluxes, the equilibrium references, and the κ_r/δ_r diagnostics) on the existing abundances, all CPU-cheap and embarrassingly parallel and gated by the mandatory detailed-balance artifact screen — is exactly the work that does not need new burns. What the public data are *not* is equally important: not a flux database, so φ and its supporting quantities must be built; and not a trajectory dataset, so the dense variable-Δt trajectories that are the canonical data shape require either the on-request 4 TB superset or a fresh cluster-scale campaign.

The sampling redesign replaces the baseline's weakest link — ad-hoc per-Yₑ random composition — with constrained draws on the (n−2)-polytope and a three-way mixture, and it resolves the "unphysical sampling helps" tension by division of labour: broad coverage teaches the function class, trajectory-aware seeding densifies the scored manifold, and deterministic densification buys cancellation-window accuracy, while the Sobol→real transfer is left honestly as a local measurement the literature can only motivate. The data shapes follow one principle — store dense cumulative trajectories once and treat the single-step, pushforward, and QSE-respecting-perturbed mixtures as sampling policies over them — and the validation plan checks both that the labels are not solver-limited (SkyNet, WinNet) and that error measured on Sobol compositions transfers to real tracks (the R > 3 test).

The single number that reshapes everything downstream — the per-step Yₑ gate, and through it the required pushforward depth and the single-step fraction — is set by the error-accumulation slope of the trained emulator, which no external paper settles and which only a local rollout experiment can measure. The recommended sequencing front-loads everything cheap and reversible (the derivations, the infrastructure, the sampler, the label cross-checks), defers everything expensive and irreversible behind explicit validation thresholds, and negotiates the 4 TB superset early because it sits on the critical path for both the variable-Δt trajectories and the first new regime.

---

## References (consolidated, post-verification)

**Anchor works and tools.** Grichener, Renzo, Farmer et al. 2025, "Nuclear Neural Networks," ApJS 279, 49 (DOI 10.3847/1538-4365/ade717; arXiv:2503.00115); reproducibility package Zenodo 10.5281/zenodo.14873443 (`NuclearNeuralNetworks.zip`); MESA GitHub Issue #575 (`r_neut_nuet_he4_he4_to_h3_li7`). Kim, Chae, Ko, Mumpower & Smith 2026, "NuGNN," arXiv:2606.04491. Farmer 2023, bbq, Zenodo 10.5281/zenodo.7585202. MESA r23.05.1 (Paxton et al. 2011–2019; Jermyn et al. 2023, ApJS 265:15). pynucastro: Willcox & Zingale 2018, JOSS 3:588; Smith et al. 2023, ApJ 947:65. JINA REACLIB: Cyburt et al. 2010, ApJS 189:240.

**Nuclear and QSE physics.** Hix & Thielemann 1996, ApJ 460:869; Hix & Thielemann 1999, "Silicon Burning II," ApJ 511:862 (astro-ph/9808203); Hix et al. 2007, ApJ 667:476. Guidry 2011, "Algebraic Stabilization of Explicit Numerical Integration for Extremely Stiff Reaction Networks," arXiv:1112.4778 (partial-equilibrium criterion set 1112.4716/4738/4750). Malaney & Fowler 1989. Weak rates: Langanke & Martínez-Pinedo 2000; Oda et al. 1994; Fuller, Fowler & Newman 1985. Farmer, Fields, Petermann et al. 2016, ApJS 227:22 (arXiv:1611.01207). Suzuki et al. 2016. Rauscher & Thielemann 2000; Rauscher 2003.

**Sampling and QMC.** Willms 2021, Missouri J. Math. Sci. 33(1):119. Pillards & Cools 2005, J. Comput. Appl. Math. 174(1):29. Basu & Owen 2015, SIAM J. Numer. Anal. 53(2):743; Basu & Owen 2016, SIAM J. Numer. Anal. 54(3):1946. Gryazina & Polyak 2012, arXiv:1211.3932 (EJOR 238:497). Griffin et al. 2020 (DRS, RTSS 2020); Willemsen, van den Heuvel & van de Velden 2025, arXiv:2501.16936 (DRSC).

**Surrogate and rollout ML.** Yao et al. 2024, "Solving multiscale dynamical systems by deep learning" (DeePODE/EMCS), arXiv:2401.01220. Zhang, Yi, Wang, Xu, Zhang & Zhou 2025, "Deep Neural Networks for Modeling Astrophysical Nuclear Reacting Flows," arXiv:2504.14180. Holdship et al. 2021 (Chemulator), A&A 653:A76 (arXiv:2106.14789). Maes et al. 2024 (MACE), ApJ 969:79 (arXiv:2405.03274). van de Bor, Brennan, Regan & Mackey 2025, "Bridging Machine Learning and Cosmological Simulations," arXiv:2503.10736 (OJAp 8). Ono & Sugimura 2025, "Neural-Network Chemical Emulator for First-Star Formation," arXiv:2508.16114. Brandstetter, Worrall & Welling 2022 (MP-PDE, pushforward), arXiv:2202.03376. Janssen, Sulzer & Buck 2024 (CODES), arXiv:2410.20886. Sulzer & Buck 2023, arXiv:2312.06015. Battaglia et al. 2018; Sanchez-Gonzalez et al. 2020 (GNS, arXiv:2002.09405); Pfaff et al. 2020 (MeshGraphNets, arXiv:2010.03409).

**Solver-independent cross-checks.** Lippuner & Roberts 2017 (SkyNet), ApJS 233:18. Reichert et al. 2023 (WinNet), ApJS 268:66 (arXiv:2305.07048). Deuflhard 1983 (Bulirsch–Stoer / Bader–Deuflhard).
