# Prediction-Target Conditioning and the Electron-Fraction Accuracy Floor for a Conservation-by-Construction GNN Emulator of Silicon Burning

*Synthesis of two research runs and their adversarial audits — (1) QSE structure and prediction-target conditioning, (2) weak-interaction physics and the Yₑ accuracy floor, June 2026. Corrections from both hostile-referee passes are incorporated directly into the text; figures, citations, and numerical bands below reflect the post-verification state.*

---

## Abstract

The conservation-by-construction GNN emulator of silicon burning rests on a single architectural decision: how to parameterize the network output so that baryon number and charge are conserved exactly while the electron fraction Yₑ — the quantity that controls core-collapse outcomes through M_ch^eff ∝ Yₑ² — is computed accurately. This report synthesizes the two research runs that bound that decision and the two adversarial audits that verified them. The first run establishes the numerical conditioning of two candidate prediction targets against the quasi-statistical-equilibrium (QSE) structure of silicon burning; the second establishes the nuclear-physics accuracy floor on Yₑ set by the tabulated weak-interaction rates that drive its evolution. The two runs converge on one experiment — the QSE-cancellation kill-test — in which the accuracy floor from the second run supplies the pass/fail thresholds for the target choice in the first.

The headline conclusions, post-audit, are five. (1) The signed-net-flux target mapped through a fixed stoichiometric matrix (Target A) is the better-conditioned choice, provided its outputs live in a linear (or stably-invertible asinh) space and the near-equilibrated reaction subset is explicitly identified and masked. (2) Direct-ΔX prediction with a fixed null-space conservation projection (Target B) conserves exactly by one linear operation but degrades the instant its output space becomes logarithmic — the documented NuGNN failure mode — so it must be built only in a linear space, as benchmark and fallback. (3) The decisive cross-domain resolution is to make the conserved quantity the network's native *linear* output and keep any nonlinear transform internal/latent; this is precisely Target A done correctly, validated in atmospheric photochemistry (Sturm & Wexler) and combustion (CRNN/Döppel–Votsmeier). (4) The defensible Yₑ nuclear-physics floor is ΔYₑ ≈ 5×10⁻³ to 1.5×10⁻² end-to-end per trajectory, anchored on the FFN→LMP rate-set shift; under the conservative assumption of systematic (linear) error accumulation appropriate to an autoregressive neural emulator, this translates to a per-step kill-test threshold of |ΔYₑ| ≲ 3×10⁻⁶. (5) Both citation bases survived hostile line-by-line verification with zero hallucinated load-bearing references; the required corrections concerned mislabeled inference, one wrong substitute number, an internally inconsistent floor band, and the executability of the kill-test against the public dataset — all folded into the text below.

The unifying message is that the project's central design tension and its accuracy gate are now quantified well enough to commit to the hybrid Target-A architecture, conditional on the kill-test, with the error-accumulation model measured rather than assumed.

---

## 1. Framing: one decision, two bounds

The emulator's headline differentiator is conservation by construction. Every nuclear reaction *j* satisfies Σᵢ Aᵢ νᵢⱼ = 0 and, with lepton bookkeeping, the appropriate charge balance, so any update of the form ΔY = ν F lies exactly on the conservation manifold regardless of the error in the predicted flux F. But conservation is not accuracy: a trajectory can sit exactly on the manifold while drifting to the wrong point on it. Two questions therefore decide whether the differentiator is viable for silicon burning.

The first is **conditioning**. In the QSE regime that defines silicon burning, can any conservation-respecting parameterization of the output recover Yₑ accurately, given that the dynamics are dominated by near-cancelling forward and reverse fluxes? The second is **tolerance**. How small must the per-step Yₑ error be before the emulator is no longer the dominant error source relative to the weak-interaction physics it is emulating? Run 1 answers the first; Run 2 answers the second; and the second sets the threshold for the first. The remainder of this report develops them in that order, then unifies them in the kill-test that operationalizes the go/no-go and closes with the recommendations, novelty status, and the open questions that only local numerical experiments on the bbq/MESA data can resolve.

---

## 2. The QSE cancellation problem — the physics that conditions the target

### 2.1 Equilibrium structure

A photodisintegration channel becomes competitive when the reaction Q-value drops below ≈30 k_B T. With silicon-group Q-values of 8–12 MeV this occurs once temperature exceeds ~3×10⁹ K, with full QSE clusters established somewhat higher. The two primary sources differ slightly and should be attributed separately: Hix & Thielemann 1999 ("Silicon Burning II") give a threshold of *approximately* 3×10⁹ K, while the Thielemann, Nomoto & Hashimoto review gives ≈3.3×10⁹ K for establishment of the lower QSE cluster over 28 < A < 45. The spread is a minor numerical disagreement, not a substantive one, but the emulator's conditioning analysis should carry both values rather than collapse them to one.

Above this temperature the fast capture/photodisintegration pairs — (γ,α)/(α,γ), (γ,p)/(p,γ), (γ,n)/(n,γ) — balance, and the abundance of any nucleus in QSE with ²⁸Si is fixed by just three free abundances (free n, free p, ²⁸Si) plus the thermodynamic state:

> Y_QSE(ᴬZ) = [C(ᴬZ)/C(²⁸Si)] · Y(²⁸Si) · Y_n^(N−14) · Y_p^(Z−14),
> with C(ᴬZ) = [G(ᴬZ)/2ᴬ]·(ρN_A/θ)^(A−1)·A^(3/2)·exp(B(ᴬZ)/k_BT).

As Y(²⁸Si), Y_p, and Y_n approach their NSE values, Y_QSE → Y_NSE(ᴬZ) = C(ᴬZ)·Y_n^N·Y_p^Z, the global NSE result that depends on only two abundances. The membership diagnostic r_QSE(ᴬZ) = log[Y_QSE/Y] is constant (= 0 for the silicon group) across all members of a group, so distinct groups appear as offset plateaus — the operational signature the kill-test will use to assign group membership.

### 2.2 Group structure across temperature, density, and Yₑ

A single NSE cluster exists for T ≳ 6 GK; as temperature falls it splits, first between ⁴He and ¹²C at ~6 GK and later between the silicon group and the iron-peak species at ~4 GK. In the project's 1.6–7.9 GK regime there are three pools: a light-particle pool (n, p, α, and light nuclei), a silicon group (A ≈ 24–45: ²⁸Si, ³²S, ³⁶Ar, ⁴⁰Ca, ⁴⁴Ti), and an iron-peak group (A ≈ 50+: ⁴⁸Cr, ⁵²Fe, ⁵⁶Ni, ⁶⁰Zn). The two heavy groups are separated by the Z = N = 20 shell closures and the small Q-values and cross-sections that result.

Critically, lower Yₑ delays the merging of the two heavy groups. At Yₑ = 0.498 a merged group (within 10%) forms once X(Si group) drops to 0.85, whereas at Yₑ = 0.46 the iron-peak group reaches 90% of its silicon-QSE abundance only after 70–75% of the silicon-group mass is gone. The NSE transition in this density range is fairly sharp in temperature (the steep exp(B/k_BT) factor) but its location shifts with both ρ and Yₑ. The emulator must therefore reproduce a moving group boundary, not a fixed one — a point that recurs in the bottleneck analysis below.

### 2.3 The cancellation hierarchy and the bottleneck reactions

Within a QSE group, the net flux of each internal reaction is driven toward zero while the gross forward and reverse fluxes remain enormous. The slow, well-conditioned net flow through the network is carried by a small number of *bottleneck* reactions linking groups. The equilibria form a strict hierarchy: (γ,n)/(n,γ) pairs equilibrate earliest (lowest Q-values; neutrons are not Coulomb-blocked), (γ,p)/(p,γ) early, (γ,α)/(α,γ) early-to-intermediate, and (α,p)/(p,α) latest of the strong pairs — the (α,p)/(p,α) channel carries the dominant late net flow after group merger at 4–5 GK.

The bottleneck reactions are Yₑ-dependent, and the two regimes are reconciled by the Yₑ-dependence of the group boundary itself:

- **High Yₑ (≈ 0.498):** the inter-group linkage is dominated by ⁴⁵Sc(p,γ)⁴⁶Ti. Woosley, Arnett & Clayton (1973), as reported by Hix & Thielemann (1996), attribute ~75% of the flow to this single reaction, with "perhaps a quarter of the flow going through less important reactions" such as ⁴²Ca(α,γ)⁴⁶Ti and ⁴⁵Ti(n,γ)⁴⁶Ti. This ~75% fraction carries no attachment to specific thermodynamic conditions in the source and should be cited as a high-Yₑ result with conditions unspecified.
- **Low Yₑ (≈ 0.46):** the bridge shifts to proton capture on neutron-rich Ca, with an unbalanced upward flow by neutron capture from the silicon group. Hix & Thielemann state explicitly that "it is hard to see how the reaction ⁴⁵Sc(p,γ)⁴⁶Ti can be the link between QSE groups" at Yₑ = 0.46. No published numeric flux fraction exists for the low-Yₑ bridge; the description is qualitative only.

Both pictures are correct in their respective Yₑ regimes, which is itself a constraint: the emulator must respect the shift in the dominant bottleneck across the full 0.45 < Yₑ < 0.5 range. The structural fact that decides Target A versus B is that the inter-group net flow concentrates in this handful of well-conditioned reactions (net ≈ gross), while the overwhelming majority of strong/EM reactions are near-equilibrated and carry tiny net flux relative to their gross fluxes.

### 2.4 Numerical-methods conditioning literature

The stiffness is quantified directly. Hix & Meyer (2006) report that the overall stiffness ratio S = max|Re λ|/min|Re λ| "> 10¹⁵ is not uncommon in astrophysics," and that near equilibrium the production and destruction timescales become so short relative to the dynamical timestep that their difference is "close to the numerical accuracy (i.e. 14 or more orders of magnitude)." This stiffness is why nuclear networks are integrated implicitly — Timmes (1999) recommends variable-order Bader–Deuflhard integration with the MA28 sparse solver as the best accuracy/efficiency balance; Longland et al. (2014) confirm Bader–Deuflhard and Gear methods are robust where Wagoner's two-step method is not — and bbq itself uses the Bulirsch–Stoer (Bader–Deuflhard-class) algorithm at constant T, ρ.

Two solver lineages show how to defeat cancellation without integrating the equilibrated reactions, and both inform the emulator's target design. The hybrid QSE/NSE network of Hix et al. (1998, 2007) evolves group-total abundances (Y_SiG, Y_FeG, Y_αG) plus a few light nuclei — seven variables instead of fourteen for the α-chain — and reconstructs group members algebraically, giving order-of-magnitude speedups with no significant loss of accuracy. The Guidry explicit-integration lineage classifies three stiffness types: (i) negative-population, (ii) *macroscopic* equilibration (F⁺ − F⁻ → 0 for an entire species equation), and (iii) *microscopic* equilibration (individual forward/reverse pairs f⁺ − f⁻ → 0). Asymptotic and quasi-steady-state methods remove (i)–(ii) but become non-competitive near equilibrium precisely because they cannot remove (iii); partial-equilibrium methods target (iii) directly, detecting equilibrated pairs and replacing their net flux with an algebraic equilibrium constraint. Their statement of the pathology is the canonical one: "Near equilibrium the difference Fᵢ = Fᵢ⁺ − Fᵢ⁻ can be orders of magnitude smaller than Fᵢ⁺ or Fᵢ⁻ and small numerical errors in Fᵢ⁺ or Fᵢ⁻ can produce large errors in the difference." The equilibration criterion is |yᵢ − ȳᵢ|/ȳᵢ < ε with ε of order 10⁻².

On the magnitude of the timescale separation, the defensible sourced anchors are the CNO figure of ~10¹⁴ explicit integration steps (a ~100 s fastest β-decay rate over ~10¹⁶ s of burning; Guidry et al. 2011, arXiv:1112.4738) and the rate-span statement that "the fastest and slowest rates can differ by 10–20 orders of magnitude" (Guidry et al. 2023, arXiv:2312.09090). The project's working "6–8 orders of magnitude" figure for the fast-equilibration versus slow-net-flow separation remains unsourced — it is an internal estimate — and must be measured directly from bbq trajectories as the ratio of the fastest equilibrated-pair rate to the slowest bottleneck net rate.

This is the structural picture the target choice must accommodate: slow net flow concentrated in a few well-conditioned bottlenecks, fast equilibration spread across a near-cancelling majority, and a stiffness span exceeding any practical floating-point margin.

---

## 3. The two candidate prediction targets

### 3.1 Target A — signed net flux through the stoichiometric matrix

Target A predicts the *signed net* per-reaction flux φ_r = f_r⁺ − f_r⁻ as a single quantity and maps it to abundance changes through the stoichiometric matrix, ΔY = ν φ. Conservation is exact via Σᵢ Aᵢ νᵢⱼ = 0, independent of the error in φ.

The crucial distinction — and the reason this is sound where the naive "predict non-negative forward and reverse fluxes, then subtract" option is not — is that in Target A the *target itself* is the net flux. The model never forms the difference of two large *learned* numbers; the cancellation between the enormous gross fluxes was already performed by the ground-truth solver that generated the training data. What remains is a *dynamic-range* problem rather than a *cancellation* problem: the vector of signed net fluxes spans from O(bottleneck flux) down to the round-off floor for fully-equilibrated reactions (Hix & Meyer's "14 or more orders of magnitude"), and the task is to represent small signed numbers accurately.

The combustion/QSS literature handles exactly this case by not solving for the net flux of the equilibrated subset at all. The ML analog of the Guidry partial-equilibrium criterion (ε ≈ 0.01) is to predict net flux only for the active (non-equilibrated, bottleneck) reactions and set the remainder to their constraint-implied values — mirroring both the Hix QSE-reduced solver and the Guidry partial-equilibrium scheme.

### 3.2 Target B — direct ΔX with a null-space projection

Target B predicts ΔX directly — the NuGNN-style target, which empirically works — and projects onto the conservation manifold {Σ Aᵢ ΔYᵢ = 0, Σ Zᵢ ΔYᵢ = 0} via a fixed null-space layer. This is a single linear operator that conserves baryon number and charge exactly to machine precision. It is well-posed in a *linear* output space. The difficulty is dynamic range: near equilibrium ΔX over a timestep is itself tiny for most isotopes (QSE members barely move while bottleneck-fed species change by O(1)), and a single linear output cannot simultaneously resolve O(1) bottleneck changes and O(10⁻²⁰) trace changes. This is why every prior ΔX emulator reaches for a log or signed-log transform — and that transform is precisely where exact linear conservation breaks.

### 3.3 The NuGNN precedent — the cautionary tale for Target B in log space

NuGNN (Kim, Chae, Ko, Mumpower & Smith 2026, arXiv:2606.04491) is the direct precedent and the decisive evidence against naive direct-ΔX with a hard conservation layer in a nonlinear output space. It predicts ΔX for a 690-isotope Type I X-ray-burst network with signed-log preprocessing of the target labels. The authors note that Σᵢ ΔXᵢ = 0 could in principle be enforced via a physics-informed loss term or output activation "as done in previous studies (Fan et al. 2022; Grichener et al. 2025; Zhang et al. 2025)," but that "in this study, we found that such approaches made the training unstable because the target labels were preprocessed into logarithmic form… Enforcing the explicit conservation constraint requires transforming the network outputs back from the signed log representation to ΔX… In practice, this inverse transformation made the optimization unstable and degraded the training performance." NuGNN therefore relied on the model learning conservation implicitly, achieving "errors of only a few percent" and reproducing the final abundance patterns in-solver where its dense and convolutional baselines fail.

The contrast with the Grichener NNN sharpens the point. The NNN uses a log-softmax composition head that enforces Σ Xᵢ = 1 (normalization/mass) but *not* charge conservation (Yₑ), and it predicts the new composition X rather than ΔX — which hides the small-net-change problem inside a quantity of order the full abundance. Neither incumbent enforces baryon-and-charge conservation by construction, which is exactly the gap the project targets; NuGNN's experience defines the trap to avoid in closing it.

### 3.4 The linear-versus-nonlinear conservation clash, and its resolution

The asinh (inverse hyperbolic sine) transform of Döppel & Votsmeier fits *actual rates* — smooth through zero and through sign changes — rather than log-rates, avoiding both log's singularity at zero and its inability to represent sign. It is the natural transform for signed net fluxes. But the underlying clash is general: a conservation projection (Aᵀ ΔY = 0) is *linear* in ΔY, whereas log, signed-log, and asinh output spaces are *nonlinear*. Exact conservation requires summing in linear space; if the native output is nonlinear, one must invert the transform before projecting — and that inversion is what destabilized NuGNN.

The clean resolution from the literature is to make the *conserved* quantity the network's native *linear* output and keep the nonlinear transform internal/latent. Sturm & Wexler (2020, 2022) build a fixed final linear layer equal to the stoichiometric/A-matrix acting on predicted fluxes, so atoms are conserved to machine precision by construction, stating that "training ML algorithms on target fluxes S rather than tendencies ΔC would allow for mass conservation to numerical precision." This *is* Target A's architecture: predict fluxes in a latent transformed space, multiply by the fixed stoichiometric matrix, and obtain ΔY in linear space, conserved exactly. The same principle underlies the Chemical Reaction Neural Network (Ji & Deng 2021), whose output-layer weights *are* the stoichiometric coefficients (the original does not conserve atoms; Döppel et al. 2024 add an element-balance layer as a hard constraint, and Kircher & Votsmeier 2025 add positivity-preserving projection with linear-interpolation backtracking). The combustion partial-equilibrium/QSS formalism (Mott 1999; Goussis 2012) is the chemistry-side analog of the silicon bottleneck picture: identify the equilibrated subset, solve only for the slow net flow.

### 3.5 Reaction-class conditioning

The following table estimates, by reaction class, where the gross-to-net flux disparity is severe (ill-conditioned, must be masked) and where the net flux is comparable to the gross flux (well-conditioned, must be predicted). The literature states the disparity only as "orders of magnitude" and gives no tabulated per-class ratio; the ratios below are inferences anchored on the sourced statements (S > 10¹⁵ overall stiffness; 14+ orders near-equilibrium cancellation; the ~75% high-Yₑ bottleneck fraction). Each cell should carry its sourced/derived/guessed status forward.

| Reaction class | Equilibrates first? | Approx. T range where the pair is balanced (this regime) | Estimated gross/net flux ratio | Basis |
|---|---|---|---|---|
| (γ,n)/(n,γ) | Earliest (lowest Q; neutrons not Coulomb-blocked) | balanced from ≳3 GK down to ~3 GK n-freezeout | very large (≫10³; → accuracy floor near NSE) | H&T 1996; inference |
| (γ,p)/(p,γ) | Early | ≳3.5 GK | very large in group interior; O(1) for bottleneck ⁴⁵Sc(p,γ)⁴⁶Ti | H&T 1996 (~75% inter-group flux at high Yₑ) |
| (γ,α)/(α,γ) | Early–intermediate | ≳3.5–4 GK | large interior; moderate for low-Yₑ feeders | H&T 1996 |
| (α,p)/(p,α) | Latest strong pair; carries late net flow after merger | dominant net carrier at 4–5 GK late burning | nearer O(1) for ⁴⁴Ti(α,p)⁴⁷V, ⁴³Sc(α,p)⁴⁶Ti, ⁴⁵Ti(α,p)⁴⁸V | H&T 1996 |
| Inter-group bottleneck (⁴⁵Sc(p,γ)⁴⁶Ti high Yₑ; neutron-rich-Ca proton capture low Yₑ) | Never (rate-limiting) | whole ~3.3–5 GK QSE window | O(1) — net ≈ gross; **well-conditioned** | H&T 1996 (qualitative for the low-Yₑ bridge) |

The operational message is that the well-conditioned targets are a small, Yₑ-dependent set; the conditioning question is therefore equivalent to asking what fraction of the network falls into that set, which is what the kill-test measures.

---

## 4. The weak-interaction machinery — what drives and bounds Yₑ

### 4.1 The four tabulations and their division of labor

Four tabulations dominate this regime, partitioned by nuclear shell. The Yₑ-controlling Fe-peak nuclei sit in the LMP (pf-shell) regime, which is the most consequential row for the emulator.

| Tabulation | Mass range / shell | Nuclear model | (T, ρYₑ) grid | Key systematics vs. others |
|---|---|---|---|---|
| **FFN** — Fuller, Fowler & Newman (ApJS 42, 447, 1980; ApJS 48, 279, 1982a; ApJ 252, 715, 1982b; ApJ 293, 1, 1985) | A = 21–60 (226 nuclei), sd+pf | Independent-particle model with single GT resonance + experimental low-lying transitions | ρYₑ = 10–10¹¹ g cm⁻³; T = 10⁷–10¹¹ K (≈0.01–100 GK) | Overestimates pf-shell EC by ~order of magnitude (misplaced GT centroid, no GT quenching/fragmentation); paper IV (1985) introduced the effective-log(ft) interpolation scheme |
| **Oda et al. 1994** (ADNDT 56, 231) | A = 17–39, sd-shell | Full sd-shell diagonalization, Wildenthal USD interaction | Same FFN grid (10 ≤ ρYₑ ≤ 10¹¹, 0.01–30 GK) | Agrees well with FFN for sd-shell (ground-state-dominated); provides effective rates + ⟨ν⟩ energies |
| **LMP** — Langanke & Martínez-Pinedo (NuPhA 673, 481, 2000; ADNDT 79, 1, 2001) | A = 45–65 (>100 nuclei), pf-shell | Large-scale shell-model diagonalization (KB3G-class) | Same FFN grid | EC rates ~1 dex smaller than FFN; β-decay changes less; provides effective ⟨ft⟩ and average (anti)neutrino energies |
| **Suzuki et al. 2016** (ApJ 817, 163) | sd-shell Urca pairs A = 20, 23, 24, 25, 27 | Shell model, USDB Hamiltonian, Coulomb corrections | Fine mesh for Urca densities | Aimed at O–Ne–Mg-core Urca cooling; companion pf-shell GXPF1J tables (later screening/Type Ia papers, e.g. ApJ 2020 abbb32) give EC smaller than KB3G and must be cited separately, not conflated with the 2016 sd-shell paper |

Recent additions through 2026 (sd Urca extensions; Chen & Wang 2023 pf-shell; pn-QRPA sets covering 709–728 nuclei; the FT-pnRQRPA EDF set for 1652 nuclei) mostly use FFN-compatible grids; QRPA EC rates on ⁵⁵Co are enhanced relative to the shell model at presupernova temperatures, but these matter chiefly for neutron-rich A > 65 nuclei outside the small networks.

### 4.2 Interpolation in practice

A direct tabulation of log-rates can produce large interpolation errors because the phase-space factor varies rapidly across the coarse grid cells. The standard remedy is the effective-log(ft) method (FFN 1985): the continuum capture phase-space factors and neutrino-loss integrals are expressed via standard Fermi integrals and removed from the rate, leaving a slowly varying effective log(ft) that is interpolated bilinearly in log T and log ρYₑ, after which the phase-space factor is reattached at the target point. Oda 1994 and LMP both provide effective ⟨ft⟩ tabulations expressly to support this.

The code-level behaviors that the emulator inherits and must verify locally: MESA's `rates` module ships FFN (1985), Oda (1994), and LMP (2000) with precedence LMP > Oda > FFN on a coarse grid (assuming complete ionization), and its own documentation flags the average neutrino energies for reactions not in the tables as "mostly fantasies or inappropriate" — a direct caveat for the neutrino-loss output head. pynucastro's `TabularRate` stores weak rates as functions of (T, ρYₑ) with bilinear interpolation (the `PythonNetwork` made consistent with the C++ path from v2.1, where it previously returned the nearest table entry) and edge-value extrapolation off-table with no error raised. bbq drives MESA's solver directly and so inherits MESA's weak-rate tables and interpolation exactly. The grid-point counts (on the order of ~11 ρYₑ points and ~12 T points) and the pynucastro default precedence are flagged for local confirmation.

### 4.3 How weak rates enter the ODEs and the energy bookkeeping

Weak rates appear as the reaction terms in the abundance ODEs dXᵢ/dt and change Yₑ directly: electron capture lowers Yₑ, β⁻ decay raises it. The energy bookkeeping is *separated*: nuclear energy generation uses nuclear mass differences (Q-values), while neutrino losses are computed from the tabulated average neutrino energies ⟨Eν⟩ supplied per process per (T, ρYₑ) cell. Heger et al. 2001 emphasize that LMP neutrino energies during the post-silicon-burning phase (T₉ ≈ 5) are generally *larger* than FFN's, so the entropy/energy loss for a given amount of electron capture differs between tables — making the ⟨Eν⟩ tabulation choice itself a source of floor uncertainty for the neutrino-loss head, and one that is larger in relative terms than the Yₑ floor. A timing subtlety matters for that head: *during* silicon burning the neutrino losses are dominated by thermal/pair processes, not β-process neutrinos; β-process neutrinos dominate only in the post-Si, pre-collapse phase (Patton, Lunardini & Farmer 2017).

### 4.4 The Yₑ-controlling nuclei

The controllers cluster in the Fe-peak A = 45–65 band — exactly the LMP regime. Aufderheide et al. 1994 tabulated the top electron-capture nuclei averaged over the trajectory for 0.40 ≤ Yₑ ≤ 0.50; Heger et al. 2001 re-ranked these in self-consistent presupernova models, stage by stage.

| Evolutionary stage | Dominant EC nuclei (lower Yₑ) | Dominant β-decay nuclei (raise Yₑ) | Network membership |
|---|---|---|---|
| Oxygen burning (T₉ ≈ 1.5–2.5) | ³³S, ³⁵Cl, ³⁷Ar (sd-shell EC), ⁵⁴,⁵⁶Fe | (β minor) | sd-shell EC → check Oda coverage; likely partly in mesa_80 |
| Silicon burning (T₉ ≈ 3–4) | ⁵⁵Co (top), ⁵⁶Ni, ⁵⁵Fe, ⁵⁴Fe, ⁵¹V, ⁵³Cr | ⁵⁶Mn, ⁵⁶Cr, ⁵⁹Fe, ⁶¹Fe, ⁶¹,⁶³Co | Fe-peak pf-shell (LMP regime A = 45–65) |
| Pre-collapse / β-equilibrium (T₉ ≈ 4–10) | ⁶⁰Co (EC rate greatly reduced FFN→LMP), ⁵⁹Co, neutron-rich Fe/Mn | β⁻ on neutron-rich Fe/Mn establishes transient β-equilibrium | Neutron-rich → partly mesa_151; some beyond both nets |

⁵⁵Co is repeatedly identified as the single most important electron-capture nucleus (Heger et al. 2001, 25 M⊙): pre-revision, roughly half of dYₑ/dt came from ⁵⁵Co and a quarter from ⁵⁶Ni, and with the LMP rates ⁵⁶Ni becomes dominant while dYₑ/dt drops by about a factor of two. The ⁶⁰Co electron-capture rate is "greatly reduced" from FFN to LMP and dominates the central Yₑ evolution from silicon depletion onward; the precise magnitude of the reduction is to be confirmed against the rate tables locally.

The network-membership column is the load-bearing local check. mesa_151 (>127 isotopes) very likely contains the full stable and mildly-neutron-rich Fe-peak set including the LMP nuclei; mesa_80 likely contains the main controllers (⁵⁴,⁵⁶Fe, ⁵⁶Ni, ⁵⁵Co, ⁵⁶Mn) but is more likely to truncate the neutron-rich β-decay partners (⁶¹Fe, ⁶¹,⁶³Co) and the most neutron-rich EC nuclei. The explicit mesa_80/mesa_151 isotope lists (Grichener et al. 2025, Appendix A) must be checked directly. For external context, the GENEC GeValNet25 reduced network (Griffiths et al. 2025) explicitly adds ⁵³Fe, ⁵⁵Fe, ⁵⁵Co, and ⁵⁷Co and uses the minimal A = 56 EC chain (⁵⁶Fe → ⁵⁶Mn → ⁵⁶Cr) to mimic a much larger network.

### 4.5 The documented Yₑ effect of table swaps

Heger et al. 2001 quantify the sensitivity directly: going from the Woosley–Weaver FFN-EC + old-β-decay set to the LMP set raises central Yₑ at iron-core collapse by ΔYₑ = 0.005–0.015 (≈1–4%, ~3% most common, larger for more massive stars), with "about half of this change [a] consequence of including beta decay; the other half, the result of the smaller rates for electron capture." The Langanke–Martínez-Pinedo review quotes the upper/central part of this range (0.01–0.015), consistent rather than contradictory. Paradoxically, iron-core masses are *smaller* despite the larger Yₑ, owing to reduced outer-core entropy. This single, well-sourced number is the anchor for the accuracy floor in the next section.

---

## 5. The Yₑ accuracy floor and the per-step error budget

### 5.1 The propagation studies are not like-for-like

The floor is a synthesis across heterogeneous bounds, and the heterogeneity must be stated rather than flattened. The four studies usually cited together answer different questions at different evolutionary endpoints:

- **Heger 2001** is a weak-rate-*set* comparison (FFN vs. LMP) carried to collapse onset — the only like-for-like weak-physics anchor.
- **Fields 2018** varies *thermonuclear* (strong) rates only, holds weak rates fixed, and stops at oxygen depletion (never reaching Si-depletion or collapse).
- **Sullivan 2016 / Pascal 2020 / Johnston 2022** vary electron-capture rates *during* hydrodynamic collapse/infall, slightly past the emulator's T₉ ≤ 7.9 training ceiling.
- **Farmer 2016** varies network size and mass resolution, not weak rates.

Sullivan 2016 found that EC-rate variations consistent with charge-exchange and β-decay calibration produce a +16/−4% range in inner-core mass at shock formation and a ±20% range in peak νₑ-luminosity — five times the spread from 32 progenitor models — with the collapse most sensitive to *reductions* in EC rates and to neutron-rich nuclei near the N = 50, Z = 28 closed shells. Pascal 2020 independently found the individual EC rates to be the most important uncertainty source, with EOS, mass model, and progenitor only marginal. Fields 2018, the only in-regime study, found central Yₑ among the narrowest distributions in its survey: a 95% spread ≲1% at C-depletion and ≲0.25% at Ne-depletion, with central Yₑ ≈ 0.492/0.493 at O-depletion and an asymmetric negative tail extending to ≃ −2% (ΔYₑ ≈ −0.010 at the extreme), driven by the thermonuclear ¹⁶O(¹⁶O,n)³¹S rate. Even *strong*-rate uncertainties therefore move bulk central Yₑ by only a few ×10⁻³, reaching ~10⁻² only in the extreme tail. There is a genuine and confirmed literature gap: **no published study propagates *weak*-rate uncertainties through the presupernova O/Si-burning phase to a central-Yₑ band**, so the floor must bridge that gap by combining bounds.

### 5.2 The synthesized floor

The FFN→LMP shift (ΔYₑ = 0.005–0.015) is a one-time historical *systematic* correction between two rate sets, not a propagated statistical uncertainty band. It is best read as an upper-bound *sensitivity scale* — "weak-physics choices move central Yₑ at this magnitude" — and the residual uncertainty *within* the modern shell-model (LMP/Suzuki/GXPF1J-class) rate set is unquantified in the literature and plausibly smaller. Anchored directly on the sourced number, the floor is:

> **ΔYₑ(floor) ≈ 5×10⁻³ to 1.5×10⁻² end-to-end per trajectory.** Working point 5×10⁻³ (an engineering inference, not a literature-derived value).

An emulator whose accumulated Yₑ error sits well below ~5×10⁻³ is no longer the dominant error source relative to the weak-rate physics itself.

### 5.3 The per-step budget under both accumulation models

Translating the end-to-end floor to a per-step budget over N = 10³–10⁴ burn steps requires stating the accumulation model explicitly, because the two models differ by ~1.5 orders of magnitude. Using the working floor F = 5×10⁻³:

| Accumulation model | Per-step budget δ | N = 10³ | N = 10⁴ |
|---|---|---|---|
| **Systematic / linear** (biased per-step error) | δ = F/N | 5×10⁻⁶ | 5×10⁻⁷ |
| **Random walk / √N** (zero-mean per-step error) | δ = F/√N | ~1.6×10⁻⁴ | ~5×10⁻⁵ |

Because neural-network emulators typically exhibit *biased* (non-zero-mean) per-step errors, the conservative gate assumes linear accumulation. The defensible target handed to the kill-test is therefore:

> **per-step |ΔYₑ| ≲ 3×10⁻⁶** (systematic-safe; an inference-labeled working value sitting inside the 5×10⁻⁷–5×10⁻⁶ window),

relaxing toward ~5×10⁻⁵–10⁻⁴ *only* if the emulator's per-step Yₑ residuals are empirically demonstrated to be zero-mean and serially uncorrelated. The provisional 10⁻⁵–10⁻⁴ budget is confirmed under the random-walk assumption and is roughly 1.3 orders of magnitude too loose under systematic accumulation. The single most decision-relevant experiment in the whole exercise is therefore to *measure* whether the per-step residual is zero-mean or biased along a full trajectory — that choice alone is the largest lever on the pass/fail line.

### 5.4 The network-truncation floor (secondary, not charged to the emulator)

Farmer et al. 2016 find ≈30% variations in central Yₑ and in the mass locations of the main burning shells across network choices, with a minimum of ≈127 isotopes needed to converge these at the ≈10% level. A literal 30% of Yₑ ≈ 0.49 (= 0.15) is unphysical as an absolute shift; the percentages most likely refer either to a neutron-excess measure η = 1 − 2Yₑ (η ≈ 0.01–0.04 in this regime, so ~10–30% maps to ΔYₑ of a few ×10⁻³ to ~10⁻²) or to a relative-Yₑ variation when comparing a grossly inadequate small net to a converged one — to be confirmed against Farmer's figures locally. Either way, the crucial point for target-setting is that the emulator need only reproduce its *own* ground-truth network, so network truncation is **not** charged against the emulator. It does, however, cap the physical meaningfulness of a mesa_80-trained emulator at the ~10% (Farmer) level regardless of emulator fidelity: mesa_151 (>127 isotopes) is near convergence, mesa_80 is below it.

---

## 6. The QSE-cancellation kill-test — the unifying experiment

This is where the two runs meet. Run 2's per-step floor supplies the accuracy threshold that turns Run 1's conditioning question into a measurable go/no-go: **any reaction whose net flux contributes to ΔYₑ below ~3×10⁻⁶ is, for accuracy purposes, equilibrated** — which directly sets the masking threshold for Target A and the per-isotope error tolerance for Target B. The kill-test must be run, on the mesa_80 and mesa_151 data, before the architecture is committed.

### 6.1 Goal

Quantify the cancellation severity across the regime and decide Target A versus Target B empirically rather than by appeal to the literature, which gives only "orders of magnitude" and never a distribution.

### 6.2 Data provenance — what is computable, and what is not

This is the gating practical constraint and was the weakest part of the original kill-test design. The public Zenodo record 14873443 contains nine *fixed* timesteps of Sobol-sampled states for mesa_80/mesa_151; it does **not** directly contain the quantities the kill-test needs, and the dependencies must be made explicit before any conclusion is drawn:

- The **cancellation ratio** κ_r = |φ_r|/(f_r⁺ + f_r⁻) needs per-reaction *gross* forward and reverse fluxes. A MESA/bbq net-flux solver outputs net Ẏ, not the separated f_r⁺ and f_r⁻; these must be *recomputed externally* from REACLIB rates × abundances × screening.
- The **equilibrium deviation** δ_r needs the QSE/NSE equilibrium abundances Ȳ, which require an *independent C(ᴬZ) QSE solver* the project must build (Hix & Thielemann Eqs. 2–7).
- The proposed (T₉, ρ, Yₑ, dt) sampling grid does not match the nine-fixed-timestep Sobol public data and *likely requires new bbq runs*.
- **Screening/detailed-balance artifacts must be screened first.** Grichener et al. 2025 (Appendix B) document a real MESA bug in which the four-particle reaction n + n + ⁴He + ⁴He → ³H + ⁷Li had a rate 20–24 orders of magnitude too large, from an omitted phase-space factor when computing endo-energetic multi-body rates from detailed balance. Such artifacts corrupt κ_r directly, and any near-equilibrium rate-table interpolation error can introduce a spurious κ floor.

### 6.3 Quantities to compute at each saved (state, timestep)

1. For every reaction *r*: gross forward flux f_r⁺ = ρN_A⟨σv⟩∏Y_reactants and gross reverse f_r⁻; net φ_r; and the cancellation ratio κ_r ∈ [0,1] (κ → 0 fully equilibrated / ill-conditioned; κ → 1 net-dominated / well-conditioned).
2. The equilibrium-deviation δ_r = maxᵢ |Yᵢ − Ȳᵢ|/Ȳᵢ over participating species, flagging δ_r < 0.01 as equilibrated (Guidry criterion).
3. Per-isotope ΔYᵢ over the timestep, decomposed into contributing reaction net fluxes, and the isotope-level cancellation analog (|ΔYᵢ| over the sum of absolute stoichiometric gross contributions).
4. The condition number of the active-set stoichiometric matrix S (active = δ_r ≥ 0.01).
5. The fraction of total |ΔYₑ| carried by the top-k reactions, testing that net flow concentrates in the bottlenecks.

### 6.4 Sampling grid

T₉ ∈ {1.6, 2.5, 3.3, 4.0, 5.0, 6.3, 7.9} (O-burning through the QSE window to near-NSE); ρ ∈ {10⁷, 10⁸, 10⁹} g cm⁻³; Yₑ ∈ {0.45, 0.48, 0.498}; dt ∈ {10⁻⁶, 10⁻³, 1, 10²} s — prioritizing the QSE-active window 3.3–5 GK, where the cancellation is worst and the bottleneck picture is sharpest.

### 6.5 Pass/fail thresholds (provisional, to be calibrated against the floor)

These are engineering targets to be calibrated against the measured κ_r distribution and the Yₑ floor, not derived constants:

- **Target A viable** if, at the median timestep, {r : κ_r > 0.1} captures ≥95% of |ΔYₑ| and of |ΔX| for the dominant isotopes — a tractable active set carries the physics. *Fail* (→ Target B or bottleneck-only A) if net flow spreads across more than ~30% of all reactions with κ near the floor.
- **Target B viable** if a linear (or stably-invertible asinh) ΔX output with null-space projection reproduces bbq ΔX to within the Yₑ floor *without* the conservation layer destabilizing training. *Fail* if conservation enforcement degrades training as in NuGNN.
- **Stoichiometric-map health** (affects A): cond(S_active) < 10⁶ pass; > 10⁸ fail.
- **Cancellation-floor calibration:** report the full κ_r distribution; reactions whose 10th-percentile κ across the active set falls below the Yₑ floor expressed as a relative flux error are formally indistinguishable from equilibrated and must be masked.

---

## 7. Recommendations — the architecture decision

**Stage 0 — Run the kill-test (the gate).** Resolve the data-provenance dependencies first (build the C(ᴬZ) QSE solver, recompute gross fluxes from REACLIB × screening, screen for detailed-balance artifacts, and confirm whether new bbq runs are needed), then measure the κ_r distribution and the per-step Yₑ residual character. Hand the systematic-safe floor (per-step |ΔYₑ| ≲ 3×10⁻⁶) to this stage as the calibration target. Until the |net|/gross distribution is measured on real mesa_80/mesa_151 trajectories, neither target is locked in.

**Stage 1 — Default to a hybrid Target A.** Predict signed net flux in an asinh latent space for the *active* (non-equilibrated) reaction set; detect equilibrated pairs with the ε ≈ 0.01 partial-equilibrium criterion; map to ΔY through the fixed stoichiometric matrix so that baryon number and charge are conserved exactly by construction. This mirrors the most successful solver precedents (Hix QSE-reduced; Guidry partial-equilibrium) and the most successful ML-surrogate precedents (Sturm–Wexler flux target; CRNN with element-balance layer).

**Stage 2 — Build Target B as benchmark and fallback,** in a *linear* output space with an additive null-space projection onto {Σ Aᵢ ΔYᵢ = 0, Σ Zᵢ ΔYᵢ = 0}. Do *not* attempt conservation enforcement in signed-log space — that is the documented NuGNN failure mode. If dynamic range forces a transform, test asinh and verify the projection still trains stably (a NuGNN-replication check).

**Stage 3 — Benchmark both against bbq** on published metrics (per-timestep error ≤ 1%; the NNN beat the 22-isotope approx21 baseline by 280–400% for mesa_151 and 390–660% for mesa_80 on Yₑ). Compare per-isotope ΔX error *distributions* (not just means), the conservation residual (≈ machine-ε for both by construction), and stability under autoregressive rollout — NuGNN's discriminating test, in which only the conserving GNN reproduced the final abundance patterns when looped.

**Thresholds that change the recommendation.** If more than ~90% of reactions have |net|/gross below the Yₑ floor at the median timestep, Target A's reaction-space output is mostly noise → switch to Target B or to a bottleneck-only Target A. If the active-set stoichiometric matrix has cond(S_active) > 10⁶, flux errors amplify unacceptably → prefer Target B. If asinh + linear-projection Target B matches Target A's rollout stability, choose Target B for simplicity.

**The accuracy gate, separately.** Hand |ΔYₑ| ≲ 3×10⁻⁶ to the kill-test, *measure* the accumulation model rather than assuming it, and treat the neutrino-loss head's floor as a distinct problem — it inherits the ⟨Eν⟩ tabulation uncertainty, which is larger in relative terms than the Yₑ floor and depends on which weak-rate table is loaded.

**Local code-level checks to retire before sizing or training.** The mesa_80/mesa_151 isotope lists and which Yₑ-controllers each contains (especially the neutron-rich β-decay partners); which weak-rate tables bbq/MESA r23.05.1 actually loads for these networks and the off-grid-edge extrapolation behavior; MESA's average-neutrino-energy handling for the neutrino head; the precise meaning of Farmer 2016's "30%/10%" (η versus Yₑ); and the condition numbers of the mesa_80/mesa_151 stoichiometric matrices (full and active-set), which have never been published and directly determine the flux-head output dimension.

---

## 8. Novelty status (June 2026)

A conservation-by-construction GNN emulator in the silicon-burning/CCSN-progenitor regime remains unclaimed as of June 2026. The two nearest neighbors confirm no exact match: NuGNN (Kim et al. 2026, arXiv:2606.04491, 3 June 2026) is a GNN on the bipartite isotope/reaction graph but for a 690-isotope Type I X-ray-burst network, achieving "errors of only a few percent," with *no* hard conservation; the Grichener NNN (ApJS 279, 49) is a late-burning MESA emulator in the right regime but a dense fully-connected network, not a GNN, again without hard conservation. The distinctive combination — hard baryon/charge conservation built into a graph architecture, the silicon-burning weak-interaction regime, and a quantified Yₑ accuracy floor — is intact. NuGNN establishes that the GNN-on-reaction-network idea is now public, so speed of publication matters; lead with the two features NuGNN lacks (hard conservation by construction and the Si-burning weak-interaction regime). One caveat from the audit cycle: the dedicated independent novelty sweep for "conservation-by-construction ML reaction-network surrogates" was cut short by search-budget exhaustion, so the novelty claim should be treated as well-supported but not exhaustively swept, and re-checked against arXiv at each phase boundary.

---

## 9. Caveats and open questions requiring local experiments

The following are the load-bearing unknowns the literature cannot resolve; they are forward-looking experimental requirements, not corrections.

- **The load-bearing unknown:** the actual per-reaction κ_r = |net|/(gross_f + gross_r) distribution for mesa_80/mesa_151 across this regime. The literature gives only "orders of magnitude," never a distribution.
- Whether the working "6–8 orders of magnitude" fast/slow timescale-separation figure holds for these networks (unsourced; measure as the ratio of the fastest equilibrated-pair rate to the slowest bottleneck net rate).
- The condition number of the mesa_80/mesa_151 stoichiometric matrices, full and active-set — never published.
- Whether MESA's softwired inverse (detailed-balance) rates reproduce equilibrium cleanly enough that κ_r → 0 without a spurious floor, or whether rate-table interpolation (and Appendix-B-style multi-body-rate bugs) introduce one — this must be screened before any kill-test conclusion.
- How many bottleneck reactions are simultaneously active and how that set evolves with Yₑ along a real trajectory (the literature names them only at fixed grid points).
- Whether asinh-latent flux prediction with a fixed stoichiometric layer actually trains stably on a nuclear network of this size — no prior work has applied the Sturm–Wexler flux-target architecture at this scale.
- The empirical rollout stability of each target under autoregressive feedback at the project's timesteps.
- **The empirical accumulation model (√N versus linear)** for the per-step Yₑ residual — the single largest lever on the pass/fail line, to be measured rather than assumed.
- Items pending local code-level confirmation: the exact ⁶⁰Co FFN→LMP rate reduction; the fine-grained Fields 2018 Yₑ figures; the MESA weak-rate grid-point counts and pynucastro default table precedence; the η-versus-Yₑ interpretation of Farmer 2016's "30%"; and the mesa_80/mesa_151 isotope lists themselves.

---

## 10. Conclusion

The two research runs jointly resolve the central architectural question of the conservation-by-construction GNN emulator and bound the accuracy it must reach. On the conditioning side, the silicon-burning regime is dominated by quasi-statistical equilibrium, in which the net flux of a near-equilibrated reaction is the small difference of two enormous gross fluxes — the cancellation pathology that the QSE literature has documented since Hix & Thielemann 1996 and that the project must not walk into. Predicting non-negative forward and reverse fluxes and subtracting them is unsound for exactly this reason. The viable choices are to predict the *signed net* flux directly and map it through a fixed stoichiometric matrix (Target A), which never forms the difference of two large learned numbers and conserves exactly, or to predict ΔX directly and project onto the conservation manifold (Target B), which conserves by one linear operation but breaks the instant its output goes logarithmic — the failure NuGNN documented and abandoned. The decisive cross-domain lesson, from atmospheric photochemistry and combustion alike, is that the conserved quantity should be the network's native *linear* output with any nonlinear transform kept internal; that is Target A done correctly, and it is the recommended default, with the equilibrated subset masked via the Guidry partial-equilibrium criterion and Target B built in linear space as benchmark and fallback.

On the tolerance side, the weak-interaction physics that drives Yₑ — the LMP-regime Fe-peak electron-capture and β-decay nuclei, led by ⁵⁵Co — sets a defensible nuclear-physics floor of ΔYₑ ≈ 5×10⁻³ to 1.5×10⁻² end-to-end per trajectory, anchored on the FFN→LMP rate-set shift read as a sensitivity scale. Under the conservative assumption of systematic error accumulation appropriate to an autoregressive neural emulator, this becomes a per-step kill-test threshold of |ΔYₑ| ≲ 3×10⁻⁶, with the accumulation model itself the largest single lever on the gate and therefore something to measure rather than assume.

These two bounds converge on one experiment. The QSE-cancellation kill-test, calibrated to the weak-physics floor and run against recomputed gross fluxes and an independently-solved QSE equilibrium on the public mesa_80/mesa_151 data, converts both the conditioning question and the tolerance question into a single go/no-go. Both citation bases underlying this synthesis survived hostile, line-by-line verification with no hallucinated load-bearing references; the corrections required — mislabeled inference, one wrong substitute number, a compressed floor band, and the executability of the kill-test against the public data — have been folded in above and do not move the Target-A lean or the floor's order of magnitude. The decision is empirically gated, the thresholds are quantified, and the principal failure modes — the QSE cancellation pathology, NuGNN's log-space conservation collapse, and the systematic-accumulation budget — are understood well enough to commit to the hybrid Target-A architecture conditionally, with clearly specified thresholds at which to switch targets rather than persist.
