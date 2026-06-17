# Technical Design Specification — Component A: Graph Backbone & Message Passing
## Conservation-by-Construction GNN Emulator of Silicon Burning (Run 1 of 3)

## 1. Executive Summary (headline decisions)

- **Architecture:** Adopt an encode–process–decode (GNS/Battaglia) backbone on a heterogeneous bipartite isotope↔reaction graph, keeping NuGNN's three connection types and per-reaction-type message functions but replacing its fixed 5-block stack with a **weight-shared recurrent processor** to keep a latent-ODE head open for Run 3. PARALLEL-WITH-KILL-TEST.
- **Hyperedge encoding:** Keep the **bipartite reaction-NODE** construction (NuGNN's choice); do NOT adopt explicit hypergraph convolution (ChemHGNN/Rxn-Hypergraph) — reaction arity ≤ 3 makes it unnecessary. PARALLEL-WITH-KILL-TEST.
- **Features (most consequential):** Feed **pre-evaluated signed-log rates at the current (T, ρYe)** rather than raw REACLIB coefficients, and add the four physics channels NuGNN omits that the Si-burning/Ye regime needs: **electron screening factors, T-dependent partition functions, explicit ρYe conditioning for tabulated weak rates, and reverse/detailed-balance linkage.** PARALLEL-WITH-KILL-TEST (with one A/B-dependent sub-item on the reverse-rate channel).
- **Depth:** **6 weight-shared message-passing steps**, scaling with graph radius (K ≈ ⌈radius⌉ + 2), with a Dirichlet-energy over-smoothing diagnostic. PARALLEL-WITH-KILL-TEST.
- **Symmetry:** Plain heterogeneous permutation-equivariant message passing; **reject E(n)/SE(3) equivariance** — the graph lives on the (N,Z) chart, not in 3D space. PARALLEL-WITH-KILL-TEST.
- **Size transfer:** Shared node-TYPE/reaction-TYPE embeddings + a learned *continuous* (Z,N) embedding MLP (NOT isotope-index one-hots); flag chemically-new-isotope transfer as a HYPOTHESIS distinct from established count-transfer. PARALLEL-WITH-KILL-TEST.
- **Biggest risk:** The size-transfer hypothesis. The GNS/MeshGraphNets precedent is for *more of the same node*, whereas mesa_151∖mesa_80 are neutron-rich isotopes carrying *new weak physics* exactly where mesa_80 fails. Featurization can maximize transfer odds but cannot guarantee it; this must be falsified empirically in Phase 0.

---

## 2. Body — survey, analysis, decision per area

### Area 1 — Message-passing architecture

**Survey (SOURCED).** The encode-process-decode (EPD) paradigm is the dominant inductive bias for learned physical simulators: Battaglia et al. 2018 (arXiv:1806.01261, relational inductive biases / Graph Networks); Sanchez-Gonzalez et al. 2020 GNS (arXiv:2002.09405, ICML 2020); Pfaff et al. 2020 MeshGraphNets (arXiv:2010.03409, ICLR 2021 outstanding paper). GNS encodes particles/relations into latent node/edge vectors, applies a stack of identical message-passing (MP) blocks ("processor"), then decodes. Heterogeneous GNN designs assign distinct weights per node/edge type (R-GCN, Schlichtkrull et al. 2018; Heterogeneous Graph Transformer, Hu et al. 2020). Graph attention: GAT (Veličković et al. 2018), GATv2 (Brody et al. 2021, arXiv:2105.14491, which fixes GAT's "static attention" limitation), Graphormer (Ying et al. 2021).

**NuGNN verification (SOURCED; verified against arXiv:2606.04491v1 full text + a dedicated quote-check pass).** NuGNN is a surrogate for a **690-isotope Type I X-ray-burst (XRB) network** — *not* silicon burning — trained on PRISM/WinNet data. Confirmed architecture:
- Heterogeneous bipartite graph: isotope nodes + reaction nodes. **VERIFIED.**
- Three connection types: Isotope→Reaction, Reaction→Isotope, Isotope→Isotope. **VERIFIED.**
- **Five** message-passing blocks, each "with attention, message dropout." **VERIFIED** ("The NuGNN consists of five message-passing blocks").
- Seven reaction-type embeddings: (p,γ), (γ,p), (α,γ), (γ,α), (p,α), (α,p), β⁺. **VERIFIED verbatim**; message/update functions are **separated per reaction type** ("each reaction type has its own learned message and update functions").
- Separation-energy node features (1- and 2-proton). **VERIFIED.**
- Two-channel sigmoid output head: two sigmoid outputs ∈[0,1], prediction = channel1 − channel2 ∈ [−1,1]. **VERIFIED** (the paper gives no explicit positive/negative physical labeling of the two channels).
- Hidden width = **64 channels**, Leaky ReLU, message/update = 2 FC layers. **VERIFIED.**
- Attention = **GAT (Veličković 2018) + sigmoid gates (Qiu et al. 2025)** — a custom GAT variant, **NOT GATv2**. **CORRECTION to the brief**: the layer is graph-attention-based but is not GATv2.
- A dedicated **flux preprocessor** refines the net-flux channel before MP. **VERIFIED** (novel; directly relevant to our Target A — see Area 3).
- Training: **90,000 samples (30k each of Types A/B/C), split 0.8/0.1/0.1 = 72k/9k/9k. VERIFIED.** Adam; LR 1e-3 for 1000 epochs, then best checkpoint trained 200 more epochs at 1e-4. **VERIFIED.** **Batch size NOT stated; number of attention heads NOT stated; a separate embedding dimension NOT stated** (only the hidden width 64). **FLAGGED unverifiable.** Loss = Smooth-L1 (β=0.001), 10× weight on p and α channels, Type-C samples down-weighted.
- Results: the headline signed-log-relative-abundance-change MAE (Table 2, "All X / Total Error" row): **NuGNN 0.037, Res-U-Net 0.11, FNN 0.56. VERIFIED.** (A separate "Non-zero X" row gives 0.11/0.32/1.69 — do not conflate with the headline figures.) Sign accuracy ~97%. Inference (TensorRT): NuGNN 1.9 ms, Res-U-Net 4.2 ms, FNN 0.1 ms.
- **Publication status: v1 preprint only, submitted 3 Jun 2026, AASTeX (ApJ/ApJS-bound), no journal DOI yet. VERIFIED.**

**Analysis.** NuGNN validates the core thesis (structure-aware GNN beats dense FNN by ~15× in signed-log MAE) but in a *different regime* (XRB rp/αp-process, proton-rich, ~690 isotopes) than silicon burning (neutron-rich, QSE, weak-rate-driven Ye). The EPD separation is what enables (a) target-agnostic latent representations (serving both Target A flux φ and Target B dX) and (b) a clean processor swap for Run 3's temporal head. NuGNN's fixed 5-block stack is a *processor with untied weights*; this forecloses nothing for a fixed-depth latent-ODE but is suboptimal for a weight-shared recurrent / continuous-depth processor.

**DECISION (PARALLEL-WITH-KILL-TEST).** Adopt EPD with NuGNN's heterogeneous topology and per-reaction-type message functions. Use **GATv2-style attention** (strictly more expressive than GAT for heterogeneous, feature-conditioned edges; resolves GAT's static-attention limitation) rather than NuGNN's GAT+sigmoid-gate. Make the processor a **weight-shared recurrent block** unrolled for K steps (Area 4), not K untied blocks.
- **Falsifiable threshold / switch rule:** If weight-shared recurrence underperforms untied blocks by > 0.01 absolute signed-log MAE (>~25% relative to NuGNN's 0.037 floor) at equal step count in Phase-0, switch to untied blocks and accept the latent-ODE foreclosure (escalate to Run 3). If GATv2 gives < 0.003 MAE improvement over mean/sum aggregation, drop attention entirely to save parameters.

### Area 2 — Hyperedge encoding

**Survey (SOURCED).** Nuclear reactions are formally hyperedges (triple-α: 3 ⁴He→¹²C; (α,p), (p,γ) chains). Two encodings: (1) **bipartite reaction-node** — each reaction is its own node connected to all reactant/product isotopes (NuGNN's approach; the standard tractable hypergraph encoding). (2) **Explicit hypergraph convolution** — ChemHGNN (Huang et al., arXiv:2506.11041, submitted 21 May 2025; "naturally models multi-reactant reactions through hyperedges… outperforms HGNN and GNN baselines, particularly in large-scale settings" on USPTO, for *reaction virtual screening*, not dynamics) and Rxn-Hypergraph (Tavakoli, Shmakov, Ceccarelli, Baldi, arXiv:2201.01196, Jan 2022; hypergraph-attention for reaction *property prediction*). Both VERIFIED to exist.

**Analysis (DERIVED).** The bipartite reaction-node construction *is* a hypergraph encoding — the reaction node materializes the hyperedge, and incident isotope↔reaction edges carry the stoichiometric incidence. ChemHGNN/Rxn-Hypergraph are motivated by organic reactions with *many* reactants/products and combinatorial reactant matching; nuclear reactions in REACLIB chapters have **arity ≤ 3** (triple-α is the extreme). The bipartite construction captures this exactly and preserves the stoichiometry that Target A's conservation map relies on (Σ_i A_i ν_ij = 0). Explicit hypergraph convolution adds machinery (incidence-matrix normalization, hyperedge-degree weighting) that buys nothing at arity ≤ 3 and complicates per-reaction-type weight sharing.

**DECISION (PARALLEL-WITH-KILL-TEST).** Keep the bipartite reaction-node encoding; signed stoichiometric coefficients ride on Reaction→Isotope edges (as NuGNN does).
- **Falsifiable threshold / switch rule:** Adopt explicit hypergraph convolution only if (a) the network contains a meaningful population of reactions with ≥ 4 distinct participating species AND (b) an ablation shows reaction-node MP loses > 0.01 signed-log MAE on those high-arity reactions vs. a hypergraph-conv variant. Given mesa_80/151/204 are softwired networks dominated by 1-, 2-, and 3-body channels, this threshold is unlikely to trip.

### Area 3 — Feature design (most consequential)

**Survey (SOURCED).** NuGNN isotope-node features: mass fraction X, net flux f(Y;T,ρ) (signed-log, refined by a learned flux preprocessor), reaction rates mapped to the isotope, 1p- and 2p-separation energies, T, ρ, Δt, learned (N,Z) embeddings. Reaction-node features: reaction rate, T, ρ, Δt, learned 7-type reaction embedding. pynucastro (Willcox & Zingale 2018, arXiv:1803.08920, JOSS; Smith et al. 2023, ApJ, arXiv:2210.09965) exports a NetworkX graph and provides, per nucleus, Z/N/A, mass excess/binding energy, ground-state spin, **T-dependent partition functions** (Rauscher 2003 high-T tables, FRDM default), REACLIB 7-coefficient fits, **tabulated weak rates in (T, ρYe)** (electron captures, β-decays), Q-values, and **detailed-balance reverse rates**. pynucastro-generated Fortran networks also implement **weak/intermediate/strong screening** (Graboske 1973; Alastuey & Jancovici 1978; Itoh 1979).

**What NuGNN omits that silicon burning / the Ye regime specifically needs (DERIVED + SOURCED physics).**
1. **Electron screening factors.** At ρ ~ 1e7–1e9 g/cm³ charged-particle rates are screening-enhanced, and screening shifts the QSE distribution itself: Hix & Thielemann, *Silicon Burning I* (arXiv:astro-ph/9511088), found "Coulomb screening is also important in reconciling the network abundance calculations with quasi-equilibrium." NuGNN's low-density XRB envelope could neglect this; silicon burning cannot.
2. **Partition-function T-dependence.** Required for correct reverse rates above 3 GK (Rauscher & Thielemann 2000). pynucastro supplies these; feed as an isotope-node channel.
3. **Explicit ρYe conditioning for tabulated weak rates.** The electron-capture/β-decay rates that *drive Ye* are tabulated in (T, ρYe), not REACLIB fits. NuGNN feeds only T, ρ, Δt globally. The electron fraction in this regime is bounded (0.45 < Ye < 0.5; e.g., a MESA 15 M☉ outer Fe core reaches Ye ≈ 0.486, and shell-model LMP weak rates raise central Ye at collapse onset by 0.01–0.015 over older rates, Heger et al. 2001), and — critically — Hix & Thielemann establish QSE governs T ≳ 3 GK while the **final Ye is fixed during silicon shell burning**: "the final Y_e is set to within a percent or so well before the iron core begins its final Kelvin-Helmholtz contraction (the last hour)… the most important period for determining core structure… occurs, not during the dynamic implosion of the star, but during silicon shell burning" (Heger, Woosley, Martínez-Pinedo & Langanke 2001, arXiv:astro-ph/0011507). Therefore the weak-rate conditioning variable ρYe **must** be an explicit feature on weak-reaction nodes.
4. **Detailed-balance / reverse-rate linkage.** Above ~3 GK forward/reverse pairs nearly cancel: Hix & Thielemann, *Silicon Burning II* (arXiv:astro-ph/9808203), "the important abundances obey quasi-equilibrium for temperatures greater than approximately 3 GK, with relatively little nucleosynthesis occurring following the breakdown of quasi-equilibrium." The net flux is then a small difference of large numbers; the model must see both members of each forward/reverse pair (or the pre-computed net) to avoid catastrophic cancellation error — this is the direct backbone-level expression of the project's QSE-cancellation rule (the conserved/net quantity must be the network's native LINEAR output, with the nonlinear transform kept internal/latent).

**Raw REACLIB coefficients vs. pre-evaluated log-rate (DECISION-critical, DERIVED).** Feeding raw REACLIB 7-tuples forces the GNN to *relearn* λ(T) across 1.6–7.9 GK — wasteful and error-prone. Pre-evaluating the rate at the current state (which pynucastro does analytically and cheaply) hands the network the physically meaningful quantity directly; NuGNN already feeds *evaluated* signed-log rates. The only reason to feed raw coefficients is if Run-3's latent-ODE head must internally re-evaluate rates at intermediate substeps at a different T.

**DECISION (PARALLEL-WITH-KILL-TEST, with one A/B-DEPENDENT sub-item).**
- Feed **pre-evaluated signed-log rates at the current (T, ρYe)**, NOT raw REACLIB coefficients. *Switch rule:* if the Run-3 latent-ODE head needs sub-step rate re-evaluation at varying T, add raw coefficients as an auxiliary reaction-node channel; threshold = if rollout error from frozen-rate substeps exceeds the per-step accuracy floor.
- Isotope node x_I (dim 16 + d_emb): [log/asinh X, signed-log net flux, isotope-mapped signed-log rate aggregate, 1p-sep, 2p-sep, 1n-sep, 2n-sep, mass-excess / binding-energy-per-A, log partition function G(T), log T, log ρ, log Δt, Ye (broadcast), screening aggregate, Z/A, N/A] ⊕ learned (Z,N) embedding.
- Reaction node x_R (dim 8 + d_rxntype_emb): [signed-log evaluated rate, Q-value, log T, log ρ, log Δt, log(ρYe) (weak rxns only; else masked), screening factor (charged-particle rxns), reverse-rate / detailed-balance value-or-flag] ⊕ learned reaction-type embedding.
- **A/B-DEPENDENT:** For **Target A** (signed net flux φ), add the **reverse-rate pair value** explicitly on the reaction node so the QSE near-cancellation lives as an internal latent quantity (native-linear-output rule). For **Target B** (dX), screening and ρYe matter equally, but the reverse-rate value is less load-bearing because dX is the directly-supervised linear output.
- **Falsifiable threshold:** Each added channel (screening, partition function, ρYe, reverse-rate) must improve Ye-error or signed-log MAE by ≥ 0.005 absolute in Phase-0 ablation to be retained; drop any that does not.

### Area 4 — Message-passing depth

**Survey (SOURCED).** Over-smoothing: Li, Han & Wu 2018 (AAAI; arXiv:1801.07606 — graph convolution = Laplacian smoothing, deep stacks homogenize features); Oono & Suzuki 2020 (ICLR — GNNs "exponentially lose expressive power for node classification"); PairNorm (Zhao & Akoglu 2020, ICLR); DropEdge (Rong et al. 2020, ICLR); Dirichlet-energy diagnostic (Rusch et al. 2023 survey, arXiv:2303.10993). "Reaction reach": K MP steps propagate information across K hops; isotope→isotope coupling traverses isotope→reaction→isotope (2 hops per reaction link), so K steps reach ~K/2 reaction-links across the chart of nuclides. NuGNN used 5 blocks.

**Analysis (DERIVED + SOURCED).** The relevant length scale is the graph **radius** (max shortest-path between dynamically-coupled isotopes within one Δt). In silicon burning the QSE clusters are tightly internally coupled and linked by few bridging reactions: Hix & Thielemann (*Silicon Burning I*) show the Si-group QSE is anchored entirely on three abundances — free protons, free neutrons, and ²⁸Si — via Y_QSE(ᴬZ) = [C(ᴬZ)/C(²⁸Si)]·Y(²⁸Si)·Yₙ^(N−14)·Yₚ^(Z−14); the inter-group link (e.g., ⁴⁴Ti(α,γ)⁴⁸Cr bridging the ²⁸Si and ⁵⁶Ni groups) carries the net flow (SOURCED, GENEC, arXiv:2408.03368). Within a cluster, equilibration is effectively all-to-all; the *net* inter-cluster flux is carried by few links. Depth must (a) bridge QSE groups (a handful of hops) and (b) carry Ye-changing weak information from neutron-rich edge isotopes inward. Over-smoothing risk rises with depth but is mitigated by heterogeneous per-type weights and EPD residual connections. (Context: full networks are stiff and costly; the classical QSE-reduced network of Hix et al. 2007, ApJ 667, 476, is "approximately an order of magnitude faster than the full network it replaces and requires the tracking of less than a third as many abundance variables, without significant loss of accuracy" — the GNN emulator is competing against that efficiency frontier, not just the full solver.)

**DECISION (PARALLEL-WITH-KILL-TEST).** Use **K = 6 propagation steps** for mesa_80, implemented as a **weight-shared recurrent processor** (one weight set unrolled 6×) so depth can grow at test time without new parameters — the key enabler for both size-transfer and the latent-ODE head. Scale with measured graph radius: **K ≈ ⌈graph_radius⌉ + 2** as networks grow mesa_80→151→204.
- **Falsifiable over-smoothing diagnostic / threshold:** Monitor layer-wise **Dirichlet energy** E(Hˡ). If E(Hˡ⁺¹)/E(Hˡ) < 0.5 for two consecutive steps, over-smoothing is active: cap K and insert **PairNorm** between blocks. If validation MAE does not improve from K to K+1 by ≥ 0.002, freeze depth at K. Conversely, if mesa_151/204 inter-QSE-group flux error exceeds the floor, increase K before widening.

### Area 5 — Symmetry / equivariance

**Survey (SOURCED).** E(n)-equivariant GNN (Satorras, Hoogeboom, Welling 2021, arXiv:2102.09844, ICML 2021); SE(3)-Transformers (Fuchs et al. 2020). These enforce equivariance to rotations/translations/reflections in **3D Euclidean space** for point clouds / molecular geometries. The chart-of-nuclides cross-section GNN (Choi, Mitra et al., arXiv:2404.02332, now published in Phys. Rev. C, 2025) uses the 2D (N,Z) grid topology but for *static* property prediction, not dynamics.

**Analysis (DERIVED).** The isotope/reaction graph lives on the **(N,Z) chart of nuclides**, not in 3D physical space. There is **no rotational/translational symmetry to exploit** — (N,Z) are physically meaningful labels, not arbitrary coordinates; rotating them is meaningless. The only symmetry a GNN must respect is **permutation equivariance over nodes**, which plain message passing already provides. E(n)/SE(3) machinery (spherical harmonics, equivariant tensor products) would be pure overhead and could *hurt* by imposing false isotropy. There is a *weak* exploitable structure — local regularity of nuclear properties on the (N,Z) lattice (mass-excess/separation-energy smoothness) — best captured by the learned (Z,N) embeddings and separation-energy features, not by geometric equivariance.

**DECISION (PARALLEL-WITH-KILL-TEST).** Use **plain heterogeneous permutation-equivariant message passing.** Reject E(n)/SE(3) equivariance.
- **Falsifiable threshold / switch rule:** Adopt geometric (lattice-translation-equivariant) layers only if a Phase-0 test shows that imposing (N,Z)→(N+1,Z+1) weight-tying improves chemically-new-isotope transfer (Area 6) by ≥ 0.01 MAE; otherwise keep learned embeddings.

### Area 6 — Size transfer

**Survey (SOURCED).** GNS (arXiv:2002.09405) generalizes "from… thousands of particles during training, to… at least an order of magnitude more particles at test time" (VERIFIED verbatim). MeshGraphNets "can scale to more complex state spaces at test time" via resolution-independent dynamics (VERIFIED). NuGNN's transfer-enabling choices: shared node-TYPE and reaction-TYPE embeddings + learned (N,Z) embeddings, NOT fixed isotope-index one-hots.

**Critical analysis — ESTABLISHED vs HYPOTHESIS (DERIVED).**
- **ESTABLISHED (count transfer):** Adding *more of the same kind* of node (more particles, finer mesh) transfers well because the learned per-type functions are size-agnostic. A mesa_80-trained model with type/embedding-based features can mechanically *run* on mesa_151/204 (more isotope and reaction nodes, same types).
- **HYPOTHESIS (chemically-new-isotope transfer):** The isotopes in mesa_151 ∖ mesa_80 are **neutron-rich species** that become dynamically important *precisely where mesa_80 fails* — they carry the weak-driven Ye decrease during Si shell burning (SOURCED, Hix & Thielemann; Heger et al. 2001). These are NOT "more of the same": they occupy unvisited regions of (N,Z) space and carry new weak-rate physics. **The GNS/MeshGraphNets precedent does not cover this.** This is the load-bearing transfer gap.

**DECISION (PARALLEL-WITH-KILL-TEST).**
- Use **shared type embeddings + a learned continuous (Z,N) embedding MLP** (ℝ²→ℝ^{d_emb}, NOT a lookup table), so a never-seen isotope still gets a smooth embedding by interpolation/extrapolation over (N,Z). Feed *physical* features (separation energies, mass excess, partition functions, screening) that are defined for new isotopes too — these maximize transfer odds because the model keys off physics, not identity.
- **Falsification test:** Train on mesa_80, evaluate zero-shot on the mesa_151∖mesa_80 neutron-rich isotopes. The hypothesis is **falsified** if zero-shot Ye-error on mesa_151 exceeds the mesa_80-internal Ye-error by more than ~2× (transfer degrading the very quantity the larger network exists to fix). **Switch rule:** if falsified, require few-shot fine-tuning on mesa_151 data and report the model as size-*adaptable* (few-shot), not size-*transferable* (zero-shot). Benchmark to preserve the NNN advantage: Grichener et al. 2025 report NNNs "improve the accuracy of the electron fraction by 280–660%" (and nuclear energy generation by 250–750%) over the 22-isotope small net; a successful backbone should keep zero-shot mesa_151 Ye-error within that improvement band.

---

## 3. Emulator Design v1 — Backbone slice (implementable)

**Graph.** Heterogeneous bipartite: isotope nodes I, reaction nodes R. Edge types: I→R (reactant incidence), R→I (signed stoichiometric incidence carrying ν sign), I→I (intra-reaction coupling). Exported from the pynucastro NetworkX graph; stoichiometric matrix ν retained externally for the Run-2 conservation map.

**Embedding tables.**
- Reaction-type embedding: table over REACLIB-chapter-derived types — at least the 7 NuGNN types plus **e-capture, (n,γ)/(γ,n), and 3-body (triple-α)** channels needed for the Si/neutron-rich regime; dim d_rxntype_emb = 8.
- (Z,N) embedding: a 2-layer MLP ℝ²→ℝ^{d_emb}, d_emb = 8 (continuous; supports unseen isotopes). NOT per-isotope one-hot.

**Feature vectors (final dims).**
- Isotope node x_I ∈ ℝ²⁴: 16 physics/state channels (Area 3) ⊕ 8-d (Z,N) embedding.
- Reaction node x_R ∈ ℝ¹⁶: 8 physics channels (Area 3) ⊕ 8-d type embedding.
- Global g ∈ ℝ³: [log T, log ρ, log Δt], with Ye broadcast to nodes; injected via FiLM into each block.

**Encoder.** Two-layer MLP per node type → latent dim **h = 128** (wider than NuGNN's 64 to carry extra physics channels and serve both targets; revisit in Phase-0). Leaky ReLU. NuGNN-style flux preprocessor applied to the net-flux channel before encoding for Target A.

**Processor.** **Weight-shared recurrent MP block**, unrolled **K = 6** steps. Each step, per reaction type, runs three sub-updates (I→I, I→R, R→I) with **GATv2 attention** (heads = 4, revisit), residual connections, and PairNorm (activated only if the Dirichlet diagnostic trips). Signed stoichiometric coefficients on R→I messages (NuGNN's sign-preservation). Message/update MLPs: 2 FC layers, width h.

**Decoder.** Left to Run 2 (output head + conservation map). Backbone exposes per-node latent h_I and per-reaction latent h_R; Target A reads φ from reaction latents, Target B reads dX from isotope latents.

**Normalization.** Signed-log for fluxes/rates/dX with NuGNN's constant-shift trick sign(·)(C+log₁₀|·/X|), C≈17, to preserve magnitude ordering; per-channel standardization fit on Phase-0 data; float32 inference with float64 cast for the Xₜ₊Δₜ = Xₜ + ΔX update (NuGNN-verified safe).

**Composition with neighbors.**
- → **Run 2** (output head / conservation / masking): backbone is target-agnostic; the contract is latent dims h_I (for dX null-space projection, Target B) and h_R (for the φ→ν·φ map, Target A). Keep h_R dimensioned to reaction count, h_I to isotope count.
- → **Run 3** (temporal / latent-ODE head): **the weight-shared recurrent processor is the enabling choice** — it is one step from a continuous-depth Neural-ODE processor (MACE-style GNN-encoder + latent neural ODE; Maes et al. 2024, ApJ 969:79, arXiv:2405.03274). EPD separation keeps encoder/decoder fixed while the processor becomes the ODE RHS. A DeepONet head is also not foreclosed (branch = latent state, trunk = Δt). **Flag:** if Phase-0 forces untied blocks (Area 1 switch rule), the continuous-depth interpretation weakens to a fixed-step residual integrator, though a fixed-depth latent-ODE remains possible. Choosing h and keeping the processor recurrent are the two backbone decisions that most directly enable or foreclose Run 3's options.

---

## 4. Hand to Phase 0 to measure

1. **Actual reaction count and graph diameter/radius** of mesa_80, mesa_151, mesa_204 (pynucastro NetworkX export). Sets K (Area 4). Expectation: order several hundred to ~1000 reactions; small radius (tightly linked QSE clusters).
2. **Feature distributions** of all proposed channels across T∈1.6–7.9 GK, ρ∈1e7–1e9 g/cm³, 0.45<Ye<0.5 — to set normalization and detect dead/degenerate channels.
3. **Pre-evaluated log-rate vs raw REACLIB coefficients** — which trains to lower signed-log MAE (Area 3 verification).
4. **Per-channel ablation** of the four added physics channels (screening, partition function, ρYe, reverse-rate) against the ≥0.005 MAE retention threshold.
5. **Dirichlet-energy depth sweep** K = 2…10 to locate over-smoothing onset and the marginal-improvement floor.
6. **Weight-shared vs untied processor** at equal step count (Area 1 switch test; gates the latent-ODE head).
7. **Zero-shot mesa_80→mesa_151 transfer test** on neutron-rich isotopes (Area 6 falsification).
8. **GATv2 vs mean/sum aggregation** ablation (Area 1).

## 5. Verified-references table

| Source | Claim used | Status | Pub status |
|---|---|---|---|
| NuGNN — Kim, Chae, Ko, Mumpower & Smith, arXiv:2606.04491 | 690-isotope XRB GNN; bipartite isotope+reaction nodes; 3 connection types; 5 MP blocks; 7 reaction-type embeddings; sep-energy features; 2-channel sigmoid head; 90k samples 72k/9k/9k; Adam LR 1e-3×1000 + 1e-4×200; MAE 0.037/0.11/0.56; GAT+sigmoid-gate (NOT GATv2); hidden width 64; flux preprocessor | SOURCED (full text + quote-verified) | v1 preprint, submitted 3 Jun 2026, ApJ/ApJS-bound, no journal DOI |
| Grichener et al., arXiv:2503.00115 | NNN baseline (dense MLP, normalization-only, offline); mesa_80/mesa_151; **Ye improvement 280–660%, energy generation 250–750%** over 22-isotope small net | SOURCED (verbatim) | Published, ApJS 279, 49 (2025) |
| Battaglia et al., arXiv:1806.01261 | Relational inductive biases / Graph Networks (EPD) | SOURCED | Preprint, widely cited |
| Sanchez-Gonzalez et al., arXiv:2002.09405 | GNS; generalizes to ≥1 order of magnitude more particles at test | SOURCED (verbatim) | ICML 2020 |
| Pfaff et al., arXiv:2010.03409 | MeshGraphNets; scales to more complex state spaces at test | SOURCED | ICLR 2021 (outstanding paper) |
| ChemHGNN, arXiv:2506.11041 | Hypergraph NN for multi-reactant reactions; reaction virtual screening (not dynamics) | SOURCED | Preprint, submitted 21 May 2025 |
| Rxn-Hypergraph, arXiv:2201.01196 | Hypergraph-attention for reaction representation/property prediction | SOURCED | Preprint, Jan 2022 |
| Chart-of-nuclides GNN, arXiv:2404.02332 (Choi, Mitra et al.) | GNN on (N,Z) grid; static cross-section prediction; 9×9 missing-nuclei block | SOURCED | Published, Phys. Rev. C (2025) |
| Padiyar, Dash & Aditya, arXiv:2603.22318 | GNN combustion mechanism reduction; GNN-AE up to 95% species/reaction reduction; methane (53/325), ethylene (96/1054), iso-octane (1034/8453) | SOURCED (verbatim) | Preprint, submitted 20 Mar 2026 |
| E(n)-GNN, Satorras et al., arXiv:2102.09844 | E(n) equivariance for 3D geometry (overkill here) | SOURCED | ICML 2021 |
| SE(3)-Transformers, Fuchs et al. 2020 | 3D-equivariant attention (overkill here) | SOURCED | NeurIPS 2020 |
| Li, Han & Wu, arXiv:1801.07606 | Graph conv = Laplacian smoothing; over-smoothing | SOURCED | AAAI 2018 |
| Oono & Suzuki 2020 | GNNs exponentially lose expressive power | SOURCED | ICLR 2020 |
| PairNorm (Zhao & Akoglu); DropEdge (Rong et al.) | Over-smoothing mitigation | SOURCED | ICLR 2020 |
| pynucastro — arXiv:1803.08920 (Willcox & Zingale 2018); arXiv:2210.09965 (Smith et al. 2023) | NetworkX export; REACLIB fits; tabulated weak rates in (T,ρYe); Q-values; T-dep partition functions; sep energies; detailed-balance reverse rates; screening | SOURCED | Published (JOSS 2018; ApJ 2023) |
| Hix & Thielemann — arXiv:astro-ph/9511088 (Si Burning I), astro-ph/9808203 (Si Burning II) | QSE for T ≳ 3 GK; Coulomb screening shifts QSE; Si-group QSE anchored on p, n, ²⁸Si | SOURCED (verbatim) | Published, ApJ 1996/1999 |
| Hix, Parete-Koon, Freiburghaus & Thielemann 2007, ApJ 667, 476 | QSE-reduced network ~order-of-magnitude faster, <1/3 the variables, no significant accuracy loss | SOURCED (verbatim) | Published, ApJ 2007 |
| Heger, Woosley, Martínez-Pinedo & Langanke 2001, arXiv:astro-ph/0011507 | Final Ye set during Si shell burning, before final contraction | SOURCED (verbatim) | Published, ApJ 2001 |
| MACE — Maes et al., arXiv:2405.03274 | GNN/autoencoder + latent neural ODE chemistry emulator (Run-3 template) | SOURCED | Published, ApJ 969:79 (2024) |

## 6. Open questions for the adversarial audit (this run's own load-bearing assumptions)

1. **The recurrent-processor bet.** Choosing a weight-shared recurrent processor (for latent-ODE openness) over NuGNN's proven untied 5-block stack is unproven: NuGNN's 0.037 floor was achieved with *untied* blocks, and we have no evidence weight-sharing matches it. (Mitigated by the Phase-0 switch test, but the project's central novelty path depends on it.)
2. **Size transfer to chemically-new isotopes is a hypothesis, not a result.** Featurization maximizes odds but the GNS/MeshGraphNets precedent covers only *count* transfer, not new-physics nodes. The entire mesa_80→204 transfer narrative rests here.
3. **Regime mismatch in the closest template.** NuGNN is XRB (proton-rich, rp/αp), not Si-burning (neutron-rich, QSE, weak-driven Ye). Choices "verified" against NuGNN may not transfer — indeed, the four omitted physics channels are *why* we expect to need a different feature set, so NuGNN's success is weaker evidence for our regime than it appears.
4. **Latent width h = 128 is a guess.** Chosen wider than NuGNN's 64 to serve both targets plus extra physics; unjustified until Phase-0, and over-width risks overfitting the narrow 0.45<Ye<0.5 band.
5. **Pre-evaluated rates vs coefficients may interact with Run 3.** If the latent-ODE head re-evaluates rates at sub-steps with varying T, the "feed evaluated rates" decision could foreclose accurate continuous-time integration — a cross-run dependency not fully resolved here.
6. **The Dirichlet-energy threshold (0.5 ratio) is heuristic.** Not calibrated to this graph; it may fire spuriously on the tightly-coupled QSE clusters, where feature homogenization is *physical* (QSE equilibration), not pathological over-smoothing.
7. **The GATv2-over-GAT claim is asserted, not measured** for this heterogeneous, physics-conditioned graph; NuGNN's GAT+sigmoid-gate may in fact be the better choice in this regime.

---

### Missed considerations surfaced beyond the six listed questions
- **Reaction-type taxonomy gap:** NuGNN's seven types are XRB-centric (αp/rp). The Si/neutron-rich regime additionally needs **electron-capture, (n,γ)/(γ,n), and 3-body (triple-α)** types; omitting them would leave the very Ye-driving and α-network channels untyped. Folded into the spec (Area 3, §3 embedding table).
- **The flux preprocessor is a Target-A gift.** NuGNN's learned flux-correction block is directly aligned with Target A's signed-net-flux φ prediction and the QSE-cancellation rule; it should be retained and is arguably more important for our signed-flux target than for NuGNN's dX target.
- **QSE clusters as a physical prior for pooling/diagnostics.** Because QSE makes intra-cluster abundances functions of {p, n, anchor}, a cluster-aware readout or diagnostic (not solved here) could both reduce variables and provide a physically-grounded over-smoothing reference — flagged for Run-2/Run-3 synthesis.