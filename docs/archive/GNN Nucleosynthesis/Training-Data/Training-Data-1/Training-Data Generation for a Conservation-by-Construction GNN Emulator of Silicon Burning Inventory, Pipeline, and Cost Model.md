# Training-Data Generation for a Conservation-by-Construction GNN Emulator of Silicon Burning: Data Inventory, Pipeline Mechanics, and Cost Model

## (1) Executive Summary

This report covers the factual/engineering-mechanics half of training-data generation (it deliberately does not design the sampling methodology or re-litigate the architecture). The four most consequential findings:

1. **The public Zenodo record (10.5281/zenodo.14873443) is a reproducibility package, not a flux database.** It contains training/validation/test sets, trained NNN models, the MESA stellar models used to set the parameter space, and analysis scripts — but the headline ~10⁶-per-network data are *(state, dt → composition + e_nuc + ε_ν)* tuples at 9 fixed timesteps. It does **not** contain per-reaction gross forward/reverse fluxes (f+, f−), signed net per-reaction fluxes φ, or QSE/NSE equilibrium abundances. Every kill-test quantity the project gates on must be **derived or rebuilt externally**. (sourced)

2. **Target A (signed net per-reaction flux φ) is not a stored quantity anywhere in the public set and must be reconstructed.** Two viable routes exist: (a) re-instrument MESA/bbq to emit per-reaction rates (MESA already supports `add_raw_rates`, `add_screened_rates`, `add_eps_nuc_rates`, `add_eps_neu_rates` to history/profile output), or (b) recompute rates × abundances × screening externally with pynucastro on the *identical* REACLIB + weak-rate inputs. Route (b) also yields the gross f+ and f− needed for κ_r. (sourced + derived-by-inference)

3. **A detailed-balance/phase-space artifact screen is mandatory before trusting any flux quantity, and the failure mode is documented and severe.** Grichener et al. (2025, ApJS 279, 49) Appendix B reports, verbatim, that "MESA miscalculated the rates of the endo-energetic reactions for all reactions involving more than two reactants and/or products … calculated these reaction rates from detailed balance considerations omitting a phase space factor related to the number of particles involved in the reactions." For the four-particle reaction n+n+⁴He+⁴He→³H+⁷Li they state: "We found that the rate of this reaction in MESA is **20-24 orders of magnitude larger than the rate in the literature (Malaney & Fowler 1989)**." This was fixed in current MESA, but any rate library/version used for flux work must be re-screened. (sourced)

4. **A fresh 10⁶-sample regime is a multi-month, cluster-scale job; the Year-1 strategy of living on public data + negotiating the on-request 4 TB set early is the correct sequencing.** At the project's stated ~0.1–0.5 CPU-hr/sample and ~17,000 core-hr/month on a 24-core node, one fresh 10⁶ grid costs ~10⁵–5×10⁵ CPU-hr — consistent with Grichener et al. §2.1, verbatim: building "sufficiently large (≃ 10⁶) training datasets within **few × 10⁵ CPU hours**" — i.e. several node-months even before storage/preprocessing. (sourced + derived-by-inference)

---

## (2) Data-Coverage Matrix (Research Question A)

### 2.1 What Zenodo 14873443 actually contains (sourced; file-level listing **must be confirmed locally**)

From the record's own description and the paper's Data Availability statement:
- **Reproducibility package** for Grichener et al. 2025. Stated contents (verbatim): "mesa stellar models used to determine the parameter space of the training sets, training sets, trained nuclear neural network (NNN) models, test datasets, and python scripts used for the analysis … including scripts and result files used to generate the figures."
- **Sampling scheme (paper §2.2, sourced):** Sobol quasi-random sampling over log T and log ρ; verbatim, "sample the temperatures and densities of each burning region logarithmically in the regimes 10⁹·² K < T < 10⁹·⁹ K and 10⁷ g cm⁻³ < ρ < 10⁹ g cm⁻³ … The electron fraction range, 0.45 < Ye < 0.5, was chosen to correspond to values typical of silicon core burning." Per-point composition is randomly generated to match the sampled Ye. **1,048,576 ≈ 10⁶ combinations per network.**
- **Networks:** mesa_80 (80 isotopes) and mesa_151 (151 isotopes); full isotope lists in paper Appendix A. mesa_204 is **not** present (it is a future project target).
- **Timesteps:** training compositions saved at **9 logarithmically spaced times from 10⁻⁶ s to 10² s**; a separate NNN trained per timestep.
- **Dataset sizes (sourced, paper §2.2 verbatim):** "The size of the training sets for each NNN is about 3 GB in the case of mesa_80 and 6 GB for mesa_151, amounting to **approximately 80 GB in total**."
- **Test set (sourced, paper §3 verbatim):** "approximately Ntest ≃ 700 bbq outputs … limiting the initial compositions to start with isotopes present in approx21_cr60_plus_co56 to enable this comparison."
- **On-disk format: must confirm locally.** The paper lists pandas + numpy as software; CSV/parquet/npy are plausible but the container format is not stated in any primary source I could verify.

### 2.2 What the on-request 4 TB bbq set adds (sourced)
Record + paper, verbatim: "The complete bbq runs that include **additional timesteps** for training the NNNs and **datasets for extended density ranges**, comprising a total of **4TB**, will be shared upon request from the corresponding author." So the 4 TB superset adds (i) more/finer timesteps beyond the 9 public ones, and (ii) density coverage beyond 10⁷–10⁹ g/cm³. It still does **not** advertise gross fluxes or equilibrium abundances.

### 2.3 Coverage matrix (needed-quantity × source × gap)

| Needed quantity | In public Zenodo 14873443? | In on-request 4 TB? | Gap / action |
|---|---|---|---|
| Single-step (state, dt → dY) pairs | **Yes** — 9 fixed dt, ~10⁶/net, mesa_80 & mesa_151 | Yes (more dt) | None for mesa_80/151; derive dY = X_final − X_init |
| Variable-dt data | Partial (9 discrete dt only) | **Yes** (extra timesteps) | Negotiate 4 TB; else new bbq runs |
| Per-reaction gross f+ and f− | **No** | No | **Derive externally** (pynucastro) or re-instrument bbq |
| Signed net per-reaction flux φ (Target A) | **No** | No | **Derive/rebuild** (f+ − f−), or MESA `add_raw_rates` |
| QSE/NSE equilibrium abundances | **No** | No | **Build independent C(A,Z) solver** (Hix & Thielemann) or pynucastro NSENetwork |
| Trajectory sequences | Partial (same state across 9 dt is not a trajectory) | Closer (more dt) | Mostly **new bbq runs** at sequential dt |
| Off-trajectory / perturbed states | **Yes, implicitly** — Sobol sampling deliberately includes off-trajectory compositions | Yes | Already covered by design |
| Real-MESA-track trajectories | **No** (Sobol space ≠ stellar tracks; MESA *models* present only to set bounds) | No | **New work**: extract core compositions from MESA runs (paper found this gives poor NNN energy accuracy) |
| New-regime data (lower T for ECSNe, lower ρ for PPISNe) | **No** | Partial (extended ρ) | **New bbq runs** |
| mesa_204 data | **No** | No | **New bbq runs** (new network) |

---

## (3) Pipeline-and-Derivation Document (Research Questions B and F-mechanics)

### 3.1 The bbq/MESA generation pipeline (B)

**What bbq is (sourced):** bbq (Farmer 2023; `github.com/rjfarmer/bbq`; Zenodo 10.5281/zenodo.7585202) is a Fortran "one zone burn calculator," LGPL v2.1, that wraps MESA's nuclear network solver "without modifying its underlying code" (Grichener et al. §2.1). It burns a single zone at **constant T and ρ**, treating the burn as decoupled from stellar structure.

**Integrator (sourced):** bbq uses the **Bulirsch–Stoer / Bader–Deuflhard** stiff ODE scheme (Deuflhard 1983), solving dX_i/dt = (A_i m_u/ρ)[−Σ_j(1+δ_ij)r_ij + Σ_{k,l} r_{kl,i}].

**Inputs (sourced):** initial temperature, density, and composition of the zone, plus the choice of MESA softwired network (mesa_80, mesa_151, etc.). Pinned to MESA **r23.05.1**.

**Native outputs (physical content sourced; column/format details must confirm locally):** the change in composition (final abundances {X}_i), the nuclear energy generation per unit mass e_nuc (erg/g), and the neutrino-loss term ε_ν (erg/g/s). Note the MESA convention (sourced): the `net` module's `eps_nuc` **already has nuclear neutrino losses subtracted** (eps_nuc ≡ ε_nuc − ε_ν,nuc); thermal neutrino losses (`non_nuc_neu`) come from the separate `neu` module. The exact bbq inlist/namelist control names, the output container (HDF5 vs text), and column headers are **must-confirm-locally** items — my direct attempts to read the bbq repository's README/inlist/source files were blocked (GitHub robots policy), so the technical description above is corroborated from Grichener et al. (which used bbq) and MESA documentation, not from the repo's own files.

**What must be post-computed (derived-by-inference):** bbq natively returns net dY/dt-equivalent (via final abundances) and energy terms, but **not** per-reaction signed flux φ, **not** gross f+/f−, and **not** equilibrium abundances. Target A's φ and all kill-test quantities are post-processing products.

**Reproducible campaign configuration (derived-by-inference + sourced for MESA pieces):**
- Pin MESA r23.05.1 and a fixed REACLIB snapshot + weak-rate tables; record the exact net file (e.g. `mesa_80.net`).
- MESA's standalone one-zone burn supports fixed-(T,ρ) burns and arbitrary (T,ρ) histories (`read_T_Rho_history`, `T_Rho_history_filename`) — the machinery bbq exposes. Verify which controls bbq surfaces. (must confirm locally)
- To emit per-reaction quantities natively, enable MESA reaction-rate output: `add_raw_rates`, `add_screened_rates`, `add_eps_nuc_rates`, `add_eps_neu_rates`, or `raw_rate <name>` for individual reactions. (sourced)

**Parallelization & throughput (sourced):** "embarrassingly parallel — each burning region can be computed independently" (paper §2.1). The paper reports hundreds of isotopes for one zone "in a few minutes," and building ~10⁶ sets "within few × 10⁵ CPU hours."

**Failure / non-convergence modes (derived-by-inference):** stiff-ODE non-convergence at the highest T/ρ and largest dt (paper notes bbq runtime grows with dt due to larger compositional change); these manifest as solver step-count exhaustion. The Appendix-B rate bug is a *correctness* failure that does not crash the solver — it silently produces wrong equilibria. Standard MESA tolerances (rtol/atol) and max internal steps govern convergence.

**Standard vs new code:**
- *Standard:* installing MESA r23.05.1, building/running bbq, choosing nets, fixed-(T,ρ) burns, energy outputs.
- *New code:* per-reaction φ/f± extraction harness; independent C(A,Z) equilibrium solver; artifact screen; κ_r/δ_r computation; HDF5 schema + provenance layer; leakage-safe splitter.

### 3.2 F-MECHANICS — deriving kill-test/masking quantities

**(i) Per-reaction gross f+ and f− (sourced API + derived-by-inference workflow).**
Use pynucastro (Willcox & Zingale 2018, JOSS 3:588; Smith et al. 2023, ApJ 947:65) built on the **same** REACLIB rates (Cyburt et al. 2010, ApJS 189:240) and tabulated weak rates (in T, ρYe) as MESA. Smith et al. 2023 confirm pynucastro provides, verbatim, "nuclear partition functions and the derivation of reverse rates via detailed balance, support for weak rate tables, nuclear statistical equilibrium state determination, electron screening support." Workflow: build a `RateCollection`/`PythonNetwork` from `ReacLibLibrary().linking_nuclei([...])` matching the mesa_80/mesa_151 isotope list. For each rate and a `Composition` at (T, ρ):
- `rc.evaluate_rates(rho, T, composition)` returns the per-rate molar flux (ẏ contribution) for every rate, including rate × density-power × Y-products × screening.
- pynucastro represents each reaction's forward/reverse as a `RatePair` (forward Q≥0, reverse); evaluate both directions separately to obtain **gross f+ (forward) and f− (reverse)**; net φ = f+ − f−. Screening via `evaluate_screening`/`get_screening_map` (use `symmetric_screening` to match aprox-style nets if needed).
- **Consistency requirement (derived-by-inference):** pynucastro and MESA must use matching REACLIB version, weak-rate tabulation set, and screening prescription, or φ will be inconsistent with the bbq target. Cross-check a sample of net dY/dt against bbq output before trusting φ.

**(ii) Independent C(A,Z) QSE/NSE equilibrium reference (sourced formalism).**
Implement Hix & Thielemann 1996 (ApJ 460:869) / 1999 (ApJ 511:862); cross-validate with Hix et al. 2007 (ApJ 667:476). The QSE abundance of nucleus (A,Z) in equilibrium with ²⁸Si (confirmed verbatim against Hix & Thielemann 1996 Eqs. 2–3):

  Y_QSE(A,Z) = [C(A,Z)/C(²⁸Si)] · Y(²⁸Si) · Y_n^(N−14) · Y_p^(Z−14)

with

  C(A,Z) = [G(A,Z)/2^A] · (ρN_A/θ)^(A−1) · A^(3/2) · exp(B(A,Z)/k_B T),

where G is the partition function, B the binding energy, θ = (2πm_u k_B T/h²)^(3/2), N_A Avogadro's number.
- **Two independent implementations recommended (derived-by-inference):** (a) hand-coded C(A,Z) with AME2020 masses + partition functions; (b) pynucastro `NSENetwork.get_comp_nse(rho, T, ye, use_coulomb_corr=True)` for full NSE as a cross-check. Agreement between (a) and (b) in the NSE limit validates the solver before QSE-group work. NSE is the high-T limit; QSE = NSE with extra group-balance constraints relaxed (a most useful approximation above ~3 GK per Hix & Thielemann).

**(iii) Detailed-balance / Appendix-B artifact screen (sourced).**
Before any flux-based analysis: (1) For every reverse rate with >2 reactants/products, verify the phase-space factor is present (precisely what MESA omitted, per Appendix B). (2) Compare equilibrium composition across network sizes — Grichener et al. examined networks of "22, 55, 80, 151, 201, 330, 495, 833, 1508, and 3335 isotopes" and found "the presence of tritium in the medium nets … led to this prominent difference in the equilibrium compositions"; flag any net where adding tritium-bearing channels swings the equilibrium. (3) Spot-check n+n+⁴He+⁴He→³H+⁷Li against Malaney & Fowler (1989) — a 20–24 order-of-magnitude discrepancy is the diagnostic signature. (4) Independently recompute reverse = forward × (detailed-balance factor from partition functions) with pynucastro and compare to the rate-library reverse. Any reaction failing these is masked out of κ_r/δ_r and flux losses.

**(iv) κ_r and δ_r (sourced definitions, derived-by-inference computation).**
- Per-reaction cancellation ratio: **κ_r = |net| / (gross_f + gross_r) = |f+ − f−| / (f+ + f−)**, in [0,1]; κ_r → 0 flags a reaction in near-perfect forward/reverse balance (QSE), where the net flux is a small difference of large numbers and is numerically fragile — exactly the reactions the conservation-by-construction architecture must handle carefully.
- Equilibrium deviation: **δ_r = max_i |Y_i − Ȳ_i| / Ȳ_i**, where Ȳ_i is the QSE/NSE reference abundance from (ii); δ_r quantifies how far a sampled state is from equilibrium for the species linked by reaction r.
- Both are computed per-sample as a post-processing pass over (f+, f−) from (i) and Ȳ from (ii).

---

## (4) Cost/Throughput Model and Storage/Format/Versioning Recommendation (Research Question I)

### 4.1 Cost/throughput model (sourced figures, derived-by-inference aggregation)

| Quantity | Value | Basis |
|---|---|---|
| Per-sample cost | ~0.1–0.5 CPU-hr | project documents |
| Node capacity | ~17,000 core-hr/month (24-core node) | project documents |
| Samples/month/node | ~34,000–170,000 | 17,000 ÷ (0.1–0.5) |
| Fresh 10⁶ grid (one net) | ~1×10⁵–5×10⁵ CPU-hr | per-sample × 10⁶; matches Grichener "few × 10⁵ CPU hours" |
| Wall-time on one node | ~6–29 months | 10⁵–5×10⁵ ÷ 17,000 |
| Cluster threshold | A fresh 10⁶ grid is impractical on one node; needs a multi-hundred-core allocation to finish in weeks | derived-by-inference |

**Implication:** a from-scratch 10⁶ grid is a cluster-scale, multi-month campaign. **Year-1 must (a) live on the public ~10⁶ sets for mesa_80/mesa_151 and (b) negotiate the on-request 4 TB superset early**, reserving fresh bbq runs for mesa_204 and new regimes only. Gross-flux/equilibrium derivation (CPU-cheap, embarrassingly parallel) can proceed immediately on the existing public abundances without new burns.

### 4.2 Storage at multi-TB scale (derived-by-inference, anchored to the 4 TB figure)
- The public set is ~80 GB; the bbq superset is ~4 TB. Adding per-reaction φ, f+, f−, and equilibrium references multiplies per-sample storage by the reaction count (mesa_80 ≈ hundreds of reactions; mesa_151 ≈ ~10³), so a fully fluxed mesa_151 set can dwarf the abundance set. Plan for **tens of TB** if storing full per-reaction tensors; mitigate by storing only φ (signed net) plus sparse f± for reactions with κ_r below a threshold, and recomputing the rest on demand.

### 4.3 Recommended on-disk format / schema / versioning / provenance (derived-by-inference)
- **Format:** columnar/array store — **HDF5 or Parquet** with chunking + compression (e.g. blosc/zstd). HDF5 suits dense (sample × reaction) flux tensors; Parquet suits the tabular (state, dt, scalars) layer. Store abundances and fluxes as **float64** at rest (φ is a difference of large numbers; precision matters for κ_r), with a **float32** training-ready mirror.
- **Schema (per sample):** {sample_id; net_name; T; ρ; Ye_init; X_init[Niso]; dt; X_final[Niso]; e_nuc; ε_ν; φ[Nreac]; f_plus[Nreac]; f_minus[Nreac]; κ_r[Nreac]; Y_QSE[Niso]; δ_r; artifact_flags[Nreac]}.
- **Provenance (mandatory):** record MESA version (r23.05.1), bbq commit/Zenodo DOI (7585202), REACLIB snapshot ID, weak-rate table set + precedence, pynucastro version, screening prescription, Sobol seed, and the artifact-screen pass/version. Without this, φ is unreproducible.
- **Versioning:** content-hash or DVC/git-LFS pointers; never overwrite — append new derivation versions so the artifact-screen fix is traceable.

### 4.4 Preprocessing / normalization conventions (sourced for the transform, derived-by-inference for application)
- **Signed-log / asinh transform:** for signed quantities (φ, dY) use a signed logarithm. The NuGNN convention (Kim et al. 2026, arXiv:2606.04491, §III.2) is, verbatim, **sign(ΔX)·(C + log₁₀(|ΔX/X|)) with C = 17** — "C was 17 which is about the maximum absolute magnitude of log₁₀(|ΔX/X|) when |ΔX/X| is lower than 1"; values with magnitude below 10⁻¹⁵ are clipped to zero; the constant shift makes log values positive "while preserving the original magnitude ordering before applying the sign," mapping the label into [−1,1]. For net flux NuGNN uses **sign(f)·log₁₀(|f|)** (no additive constant on the flux form). asinh(x/x₀) is an equivalent smooth alternative avoiding the clip.
- **Per-channel standardization:** after signed-log, standardize each channel (per-isotope, per-reaction) to zero mean/unit variance using **train-split statistics only**.
- **Precision:** float64 for the math (especially φ and κ_r); float32 for network I/O, casting back to float64 before reconstructing X_{t+Δt} = X_t + ΔX (NuGNN does exactly this — "the output was transformed back and cast to float64 before evaluating X_{t+Δt} = X_t + ΔX").

### 4.5 Train/validation/test split design (derived-by-inference)
- **Prevent trajectory-level leakage:** if/when trajectory sequences exist, split by **trajectory ID**, never by individual step — all steps of a trajectory go to the same fold.
- **Prevent timestep-level leakage:** because the public data train a separate model per dt, either (a) keep per-dt splits aligned (same underlying (T,ρ,X) initial points assigned to the same fold across all 9 dt) so the test set is unseen at every dt, or (b) hold out entire (T,ρ,X) initial conditions across all timesteps.
- **Matched-context NNN comparison:** reserve a test partition whose initial compositions are restricted to approx21_cr60_plus_co56 isotopes (the ≈700-sample protocol), enabling an apples-to-apples comparison against the published NNN baseline.
- **Stratify** folds across the Sobol (T,ρ,Ye) volume so each fold spans the full parameter space.

---

## (5) Prioritized "Generate vs. Derive vs. Build" List

| # | Data product | Tag | Effort | Cost |
|---|---|---|---|---|
| 1 | mesa_80/mesa_151 (state, dt→dY) + e_nuc + ε_ν, 9 dt | **already-public** | Download | ~80 GB |
| 2 | Extra-timestep / extended-ρ bbq superset | **already-public (on request)** | Email corresponding author; negotiate transfer early | 4 TB transfer/storage |
| 3 | Signed net φ per reaction (Target A) | **needs-new-code** (derive from public abundances via pynucastro) OR re-instrument bbq | Medium–high | CPU-cheap, embarrassingly parallel |
| 4 | Gross f+, f− per reaction | **needs-new-code** (derivable-from-public via pynucastro) | Medium | CPU-cheap |
| 5 | QSE/NSE equilibrium reference Y_QSE(A,Z) | **needs-new-code** (independent C(A,Z) solver + pynucastro NSE cross-check) | Medium–high | CPU-cheap |
| 6 | Detailed-balance/Appendix-B artifact screen | **needs-new-code** (gates everything in 3–5) | Medium | CPU-cheap |
| 7 | κ_r and δ_r per reaction/sample | **derivable** (from 3–5) | Low | CPU-cheap |
| 8 | Variable-dt / trajectory sequences | **needs-new-bbq-runs** (unless 4 TB suffices) | High | cluster-scale |
| 9 | Real-MESA-track trajectories | **needs-new-bbq-runs + new MESA runs** | High | cluster-scale |
| 10 | mesa_204 dataset | **needs-new-bbq-runs** | Very high | full fresh 10⁶ grid (~10⁵–5×10⁵ CPU-hr) |
| 11 | New-regime (ECSNe low-T, PPISNe low-ρ) | **needs-new-bbq-runs** | High | cluster-scale |
| 12 | HDF5/Parquet schema + provenance + leakage-safe splits | **needs-new-code** (infrastructure) | Medium | storage as above |

**Recommended order:** 1 → 6 → 4 → 3 → 5 → 7 (derive all kill-test quantities on existing public data first, gated by the artifact screen); in parallel start 2 (negotiate 4 TB) and 12 (infrastructure); defer 8–11 (new burns) until a cluster allocation is secured.

---

## Caveats and Verification Flags

- **Must confirm locally:** exact file listing and on-disk format of Zenodo 14873443; bbq's native output container (HDF5 vs text) and column headers; bbq's exact inlist control names and MESA subroutine entry points (my direct reads of the bbq repo files were blocked by GitHub's automated-access policy, so bbq internals are corroborated only via Grichener et al. and MESA docs); MESA's weak-rate-table precedence at off-grid (T, ρYe) and its interpolation/edge behavior; real-hardware throughput on the target node.
- **MESA weak-rate precedence (sourced):** rates module uses, in order of precedence, Langanke & Martínez-Pinedo (2000), Oda et al. (1994), Fuller et al. (1985), tabulated in (ρYe, T) on a coarse grid (1 ≤ log ρYe ≤ 11, step 1; 7 ≤ log T < 10.5, step ~0.25), assuming complete ionization — off-grid/edge behavior must be checked for the silicon-burning regime.
- **Consistency risk (derived-by-inference):** externally derived φ/f± are valid only if pynucastro's REACLIB/weak/screening inputs match MESA r23.05.1's exactly; otherwise the flux target diverges from the abundance target. Validate by reproducing bbq net dY/dt before trusting φ.
- **REACLIB chapters (sourced):** the JINA REACLIB seven-parameter fit format (Cyburt et al. 2010) organizes reactions into chapters by reactant/product counts (chapters 1–11; e.g. ch. 4 = 2→1, ch. 7 = 2→4, ch. 8 = 3→1); reverse rates require partition-function prefactors — the same physics MESA mishandled for >2-body endo-energetic rates.
- **Architecture/sampling out of scope:** sampling methodology and architecture choices are deliberately not addressed here.
- **NuGNN context (sourced):** NuGNN (arXiv:2606.04491) trains on PRISM/WinNet Type-I X-ray-burst data, not bbq silicon-burning data; only its preprocessing convention (signed-log, C=17) is borrowed here.
- **Cross-check tooling (sourced):** SkyNet (Lippuner & Roberts 2017, ApJS 233:18) and WinNet (Reichert et al. 2023, ApJS 268:66) are recommended solver-independent reaction-network codes for validating bbq abundances and the equilibrium reference outside the MESA ecosystem.