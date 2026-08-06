# Tier 2 — Network Algebra

**Complete deep dive: from rates to dY, exactly and conservatively.**

Tier 1 ended with a number: λ_j(T, ρ, Yₑ), one per reaction, trustworthy to
0.004 dex against an independent Fortran code. Tier 2 is what you do with 607
(or 1518) such numbers. It is the tier where the project's central design
commitment — *conservation by construction* — stops being a slogan and becomes
a rank computation, and where the equilibrium structure that the whole emulator
bets on (QSE) gets defined, solved for, and measured.

Four nodes:

- **S7** — the stoichiometric matrix ν, the lepton ledgers, the constraint
  matrix C, the null-space projector P, and the exact sense in which
  conservation is a property of a matrix rather than of a loss function.
- **S8** — gross fluxes f⁺/f⁻, the net flux φ, the pair map, and κ: the
  cancellation ratio that is simultaneously a detailed-balance diagnostic and a
  condition number.
- **S9** — nuclear statistical equilibrium and quasi-statistical equilibrium:
  the Saha algebra, the two-parameter (three-parameter) reduction, the Guidry
  departure criterion, and what "the Si group" actually means.
- **S10** — stiff integration of the augmented system [Y, Φ], the Jacobian, and
  why the flux Φ must be carried as a state variable rather than recovered.

Plus a front part the map does not show: **Part 0**, the astrophysical theory
and context that the algebra of this tier is *for*. Everything needed before
Tier 3 (silicon burning proper, the labels, the kill-test verdict), in one
document.

---

## Status of this document

**Personal study material, not project spec.** Deliberately written without
reference to `docs/` — everything is derived from first principles or read off
the business code, configs, notebooks, and tests.

- Textbook physics and derivations here are **mine to check**, not citable
  project output. Where I compute something myself — rank and null-space
  structure, the Saha monotonicity proof, the energy-identity collapse, the
  Target-A/Target-B equivalence theorem — it is tagged **[derived here]**:
  reproducible from the snippets given, but not a `RESULTS.md` row.
- Measured project numbers quoted here originate in `RESULTS.md` with script +
  commit + data provenance, tagged **[RESULTS]**. This file is **not** their
  source of truth; if a number here disagrees with `RESULTS.md`, `RESULTS.md`
  wins.
- **Bibliographic details in Part 0 are from memory** and are tagged
  **[sourced — verify]**. The physics content is what matters for study; the
  volume/page numbers must be checked against the actual papers before any of
  it is quoted in `docs/` or a paper draft. This is exactly the
  sourced/derived/assumed discipline of Tier 0 §VII.1 applied to myself.

**Maths formatting.** Every *equation* — anything with its own line — is LaTeX in
a `$$ … $$` block with the delimiters on their own lines, which is the form
GitHub, VS Code and Obsidian all render. Short conditions embedded in a sentence
are inline `$…$`. Symbols and quantities named in running prose stay in unicode
(the convention below); maths is never set in `monospace`, which is reserved for
code identifiers, filenames and literal values.

Notation otherwise follows the repo, Tier 0, and Tier 1: unicode math, `⁵⁶Ni` in prose,
`ni56` in code-adjacent contexts, Yₑ / ν / φ / κ as in the codebase. Section
references of the form §0.x, §I.x, §V.x point back into
[`tier0.md`](tier0.md); of the form §II.x, §III.x with an (S2)…(S6) label,
into [`tier1.md`](tier1.md). Within this file, Part 0 sections are §0.x and
node sections are §I.x (S7), §II.x (S8), §III.x (S9), §IV.x (S10).

**One convention worth stating loudly up front**, because two different
objects in this tier are both called "the flux":

| symbol | meaning | units | where |
|---|---|---|---|
| R_j, f⁺_j | **gross** rate of reaction j, one direction | mol g⁻¹ s⁻¹ | engine, integrator |
| φ_j | **net instantaneous** flux, f⁺_j − f⁻_j | mol g⁻¹ s⁻¹ | κ, kill-test |
| Φ_j | **time-integrated** flux over a label step, ∫R_j dt | mol g⁻¹ | Target A's label |

Target A predicts **Φ**, not φ. `integrate.py` produces Φ as a *gross*
per-column cumulative (dΦ/dt = R), and the net view is recovered downstream
through `pair_col` exactly as `store.py` does it. Mixing these up makes §IV
incomprehensible.

---

## How to study each node

```
  ① DERIVE      pen-and-paper: get the equation from physics before reading code
  ② READ        the module, top-to-bottom; its docstring states the contract
  ③ ORACLE      the test file — it encodes what "correct" means, numerically
  ④ SEE         the notebook figure — the measured behaviour on real data
```

Tier 2 is the tier where ① and ③ come closest to being the same thing. Two of
its four nodes (**S7**, **S10**) have oracles that are *exact* — zero
tolerance, integer arithmetic in float64 — because the underlying statement is
algebraic rather than physical. When a test in this tier says `== 0.0` and
means it, that is the tell: you are looking at a theorem, and the test is
checking the export, not the physics.

The other tell runs the other way. **S9**'s headline measurement is a
*negative* result (the single-Si-cluster plateau is not confirmed; the maskable
set is empty), and **S8**'s headline measurement is a *vacuous pass* (κ ≈ 1
everywhere on the training grid). Both are cases where the instrument worked
and the expected structure was absent. Learning to read those without either
explaining them away or over-claiming them is most of what this tier teaches.

---

## Contents

| Part | Covers |
|---|---|
| [**0** — Astrophysical prerequisites](#part-0--the-astrophysics-this-tier-is-for) | The equilibrium hierarchy (kinetics → QSE → NSE) and its history; silicon burning as photodisintegration rearrangement; the Yₑ → observable chain derived end to end **and the derivative nobody has assembled**; why conservation is structural; **what consumes the output and what speedup is achievable (the 1/f ceiling)**; the kill-test as a matrix question |
| [**I** (S7) — Stoichiometry & conservation](#part-i-s7--stoichiometry-and-the-conservation-layer) | ν as a linear map; conservation laws **are** the left null space (with the rank measurement proving C is complete); **the same object in CRN theory — deficiency, weak reversibility, the flux cone**; lepton ledgers and the tautology trap; Target A's theorem **and what it does not guarantee (positivity)**; the projector derived twice; the **Target-A ≡ Target-B reachability theorem**; **the effective dimension of the reachable set and where Yₑ hides**; the graph and K |
| [**II** (S8) — Fluxes & cancellation](#part-ii-s8--fluxes-pairs-and-cancellation) | The pair map and the net identity; κ four ways — DB diagnostic, condition number, **thermodynamic affinity**, **entropy production**; **the entropy-weighted active set, the second-law constraint on a learned flux, and the Lyapunov bound**; the weak κ ≡ 1 contract; the store; the handshake **and the Δt/τ conditioning variable it implies**; the vacuous pass |
| [**III** (S9) — NSE and QSE](#part-iii-s9--nse-and-qse) | Statistical equilibrium from the grand canonical ensemble; μ_i = Zμ_p + Nμ_n derived; the Saha coefficient term-by-term; the Newton system and its analytic Jacobian; **the monotonicity proof**; QSE clusters and u_G; QSE as a slow manifold; the Guidry δ criterion; the empty-mask verdict |
| [**IV** (S10) — Stiff integration](#part-iv-s10--stiff-integration-and-the-augmented-flux-state) | Stiffness from the Jacobian spectrum; BDF and L-stability; the augmented [Y, Φ] state; **why Φ cannot be recovered — and why that makes the flux head unidentifiable under a ΔY-only loss**; the analytic ∂R/∂Y; the energy identity as a *data* check **and the Wegscheider measurement that explains its residual**; the cost wall |
| [**V** — Policy & measurement discipline](#part-v--executable-policy-and-the-measurement-discipline-it-does-not-encode) | The structural invariants encoded in code that refuses — then the three the repo does **not** encode: **the sampling measure on the regime box**, **cluster-robust inference (657k samples ≈ 300 independent ones)**, and verification practice (convergence order, manufactured solutions, trivial baselines) |
| [**VI** — The open register](#part-vi--the-open-register) | **The single register: 25 items (R-01 … R-25), each pointing at the section that derives it, plus a ranked top eight.** R-24 (learning theory) and R-25 (shelf life) are written out here, having no home section |
| [**VII** — How the register was built](#part-vii--how-this-register-was-built-and-whether-it-is-finished) | The two gap-audit passes and the axes each swept; **thirteen candidate axes checked and found already covered**; is the audit converging? (yes, with three qualifications) |

<details>
<summary>Full section list</summary>

```
0.1  The equilibrium hierarchy          NSE / QSE / kinetics as flux statements
     counting DOF · the historical arc · what the project bets on it
0.2  Silicon burning, mechanically      why ~3 GK · two clusters, one bridge set
                                        the Fe-peak endpoint · not a ladder
0.3  The Yₑ chain, end to end            M_ch ∝ Yₑ² · deleptonisation · the observable
     0.3.4 the error budget → the 3e-6 gate
     0.3.5 ⚠ the OUTPUT end: dM_Ni/dYₑ has never been assembled
0.4  Why conservation is structural      left null vectors · the soft-penalty failure
0.5  What breaks on a leak
0.5b Deployment                          what consumes the output · imposed vs fed-back
                                         ⚠ the cost ceiling is 1/f, not the raw speed
0.6  The decision this tier serves        0.7 what is NOT here · 0.8 self-check

I.1  ν as a linear map                   I.8  The projector derived twice
I.2  Conservation = left null space      I.9  Extended space & the laundering trap
     the rank measurement                I.10 Target A ≡ Target B (reachability)
     why float64 is exact here           I.10b ⚠ effective dimension; Yₑ in the tail
I.2b CRN theory, deficiency, flux cone   I.11 The bipartite graph, radius, K
     deficiency 126/327 — the DZT does   I.12 Code walkthrough
     NOT apply, measured, and why        I.13 Oracles: the 30-test gate
I.3-I.6 weak sector · ledgers · β⁺ · C   I.14 self-check
I.7  Target A's theorem
I.7b ⚠ …and what it does NOT guarantee: positivity

II.1 From λ to R to f⁺/f⁻                II.6  The store: lossless derivation
II.2 The pair map                        II.7  The handshake: premise & tolerance
II.3 The net identity, proved            II.7b ⚠ condition on Δt/τ, not log Δt
II.4 κ four ways: DB · condition number  II.8  Cancellation-aware residuals
     · affinity · entropy production     II.9  Measured: the vacuous pass
II.4b ⚠ σ = 2k_B s κ artanh κ            II.10 Code + oracles
      → entropy-weighted active set      II.11 self-check
      → sign(φ̂) from the affinity
      → the Lyapunov bound in F (S20)    II.5 weak columns: κ ≡ 1 structurally
      ALL strong/EM-only: σ, 𝒜 and F
      are undefined on weak columns

III.1-III.7  Saha derived; the two constraints; Newton + analytic Jacobian;
             ⚠ the dYₑ/du_p > 0 proof; batching & the scalar fallback
III.8-III.11 QSE clusters & u_G; the slow manifold; δ vs r_QSE; the group boundary
III.12-III.14 the three negative results; code + oracles; self-check

IV.1 Stiffness from the spectrum         IV.6  Conservation by construction
IV.2 Why BDF, and what L-stability buys  IV.7  Error control for Φ
IV.3 The augmented state [Y, Φ]          IV.8  The energy identity is a DATA check
IV.4 ⚠ Why Φ is not recoverable          IV.8b ⚠ Wegscheider: Q ⊥ null(ν) FAILS
IV.4b ⚠ …so the flux head is                   rms 0.55 keV, max 3.5 keV
      unidentifiable in 528 directions         predicts the stock-MESA κ floor
IV.5 ∂R/∂Y by the product rule           IV.9  The cost wall, diagnosed
                                         IV.10 Code + oracles · IV.11 self-check

V.1  Invariants encoded in code that refuses
V.2  ⚠ the sampling MEASURE on the box (not its support): 35/62/82% within .1/.2/.3 dex
V.3  ⚠ cluster-robust inference: ICC 0.22-0.70, deff 6.5-18.6, n_eff ≈ 300
V.4  V&V: convergence order · manufactured solutions · NSE-as-a-baseline

VI.1 The register, R-01 … R-25           VII.1 The method: two passes, which axes
VI.2 R-24 learning theory                VII.2 13 axes checked, 13 already covered
     R-25 shelf life                     VII.3 Is the audit converging?
VI.3 Ranked: the top eight
```

</details>

# Part 0 — The astrophysics this tier is for

Tier 0 Part I asked *why the project exists*. This part asks a narrower and
more technical question: **why does the algebra of Tier 2 take the shape it
does?** Why is there a cluster solver at all? Why is the central design bet
"most reactions are in near-balance"? Why is Yₑ the quantity every gate in
`CLAUDE.md` is written around, rather than, say, the ⁵⁶Ni mass fraction?

None of that is derivable from the code. It comes from sixty years of silicon
burning theory, and the code is unreadable as *physics* without it.

---

## 0.1 The equilibrium hierarchy

### 0.1.1 Three regimes, stated as claims about fluxes

Take the network ODE (Tier 0 §II.4)

$$
\dot Y_i \;=\; \sum_j \nu_{ij} R_j(Y; T, \rho),
$$

and pair every strong/EM reaction j with its inverse j̄ (Tier 1 §III). Then the
whole of nuclear astrophysics's equilibrium taxonomy is a statement about which
of the differences φ_j = R_j − R_j̄ are negligible.

| regime | claim | composition parameters *before* constraints | …of which still free once (T, ρ, Yₑ) is given |
|---|---|---|---|
| **full kinetics** | nothing is assumed balanced | n (all abundances) | n − 2 |
| **QSE** (quasi-statistical equilibrium) | reactions *within* each of g clusters balance; reactions *between* clusters do not | 2 + g | **g** (the group masses) |
| **NSE** (nuclear statistical equilibrium) | every strong/EM reaction balances | 2 | **0** |

Read the two right-hand columns together, because the familiar "NSE has two free
parameters" is shorthand for the third column and the *point* of NSE is the
fourth: (μ_p, μ_n) parameterise the composition, and the two constraints
(ΣX = 1, Yₑ) then fix them, leaving nothing free. QSE's g leftover degrees of
freedom are exactly the group masses, which is why they have to come from the
slow dynamics.

The counting is the whole point, and it deserves to be derived rather than
asserted.

**NSE → 2.** If every strong/EM reaction is balanced, then for each such
reaction the chemical potentials of reactants and products are equal
(§III.1–III.2). Because every nucleus is reachable from free nucleons by some
chain of *strong* reactions, the balance conditions collapse to

$$
\mu_i \;=\; Z_i\,\mu_p + N_i\,\mu_n \quad\text{for every } i.
$$

Two numbers, (μ_p, μ_n), determine all n abundances. Fixing them requires two
constraints: ΣX_i = 1 and Σ(Z_i/A_i)X_i = Yₑ. So NSE composition is a
*function*, X(T, ρ, Yₑ) — no history, no rates, no network. This is why NSE is
so seductive computationally and why `qse/solver.py` exists at all.

**The reachability step is measurable, and the right measurement is not the one
you would reach for first.** "Every nucleus is reachable from free nucleons"
is a connectivity property of the *strong/EM* subgraph, so `graph_metrics`'
statement that the full exported graph is connected (**[RESULTS]** 2026-07-08)
does not establish it — the full graph carries weak edges too. The evidence that
does is §I.2.1's: the left null space of ν **restricted to strong/EM columns**
is exactly 2-dimensional and equals span{A, Z}. A strong subgraph that fell into
c disconnected pieces would conserve each piece's mass separately and push that
nullity above 2; the measured 2 is precisely the statement this collapse needs.

**QSE → 2 + g.** Now suppose the network's reaction graph, restricted to
*fast* reactions, is disconnected: it falls into g clusters, plus the free
nucleons. Within cluster G the balance conditions still collapse, but only
relative to a cluster-local reference. The general solution is

$$
\mu_i \;=\; Z_i\,\mu_p + N_i\,\mu_n + u_G \quad\text{for } i \in G,
$$

with one extra offset u_G per cluster — an integration constant of the
cluster's internal equilibrium that the *slow* inter-cluster reactions must
determine. Setting all u_G = 0 recovers NSE. This is exactly the structure in
`qse/solver.py`'s docstring, and it is why the QSE solve has three unknowns
(u_p, u_n, u_G) with a third constraint: the measured group mass fraction
Σ_{i∈G} X_i.

That third constraint is worth pausing on, because it is where QSE stops being
a closed theory. NSE needs (T, ρ, Yₑ) and nothing else. QSE needs (T, ρ, Yₑ)
**plus the group mass** — a dynamical quantity that only the slow bridge
reactions can supply. QSE is therefore a *reduction*, not a solution: it turns
an n-dimensional ODE into a (g+1)-dimensional one. That is the entire content
of the Hix & Thielemann reduced-network programme, and it is the structural
ancestor of this project's Target-A design.

**Full kinetics → n.** No reduction. What MESA/bbq actually integrates, and
what the emulator has to reproduce.

### 0.1.2 The historical arc — and why each step mattered

This is worth knowing properly, because the project's design choices are
reactions to specific historical findings, not to a generic "networks are
slow" complaint.

- **Hoyle 1946** (MNRAS 106, 343) **[sourced — verify]** — the *e-process*.
  The iron-peak abundance pattern is not the record of a reaction sequence; it
  is a thermodynamic equilibrium distribution. Peak abundance at ⁵⁶Fe at
  Yₑ ≈ 0.46–0.47. This is the origin of the idea that composition can be a
  *state function*.

  > **Say this one carefully.** The usual shorthand — "⁵⁶Fe maximises binding
  > energy per nucleon" — is not true: ⁶²Ni does (8.7945 vs 8.7903 MeV/A). What
  > NSE actually minimises is the free energy at fixed (ΣX = 1, Yₑ), and near
  > Yₑ = 0.464 = 26/56 the winner is the nucleus whose Z/A *matches* Yₑ while
  > having near-maximal B/A — which is ⁵⁶Fe. The Yₑ qualifier is not decoration;
  > it is the whole selection rule, and §0.2.3 is the same statement read as a
  > function of Yₑ.
- **Burbidge, Burbidge, Fowler & Hoyle 1957** (Rev. Mod. Phys. 29, 547)
  **[sourced — verify]** — B²FH systematises the e-process alongside s, r, p.
  Still equilibrium-first.
- **Bodansky, Clayton & Fowler 1968** (ApJS 16, 299, "Nuclear
  quasi-equilibrium during silicon burning") **[sourced — verify]** — the
  decisive correction, and the paper this tier is really downstream of. Full
  NSE is *not* reached in silicon burning on the available timescale. Instead
  the network organises into **quasi-equilibrium groups** — a silicon group and
  an iron group — each internally equilibrated, connected by a small number of
  comparatively slow *bridge* reactions that carry the net flow. Composition is
  neither a free ODE trajectory nor a state function; it is a state function
  *of the group masses*, which evolve slowly.
- **Woosley, Arnett & Clayton 1973** (ApJS 26, 231) **[sourced — verify]** —
  large explicit silicon-burning networks; QSE confirmed as an emergent
  property of the kinetics rather than an imposed assumption.
- **Hix & Thielemann 1996** (ApJ 460, 869) and 1999 **[sourced — verify;
  the 1996 reference is the one cited in `configs/qse_groups.yaml`]** — QSE
  *reduced* networks made operational: solve for (μ_p, μ_n, u_G) plus the group
  masses, integrate only the bridges. The 24 ≤ A < 45 single-silicon-cluster
  span in the repo's default group config comes from this line of work.
- **Guidry and collaborators, ~2011–2013** (J. Comp. Phys. / Comp. Phys. Comm.)
  **[sourced — verify]** — *partial equilibrium* and *asymptotic* methods:
  rather than imposing group membership by A-range, detect equilibrated
  reaction pairs dynamically via a departure criterion, and stabilise explicit
  integration by algebraically removing them. The repo's ε-sweep criterion
  |y − ȳ|/ȳ < ε (`qse/diagnostics.delta_species`) is this lineage.
- **Machine-learning era** — NNN (Grichener et al. 2025) and NuGNN (Kim et al.
  2026): learn the map directly. The physics-structural question these
  inherited but did not resolve is precisely BCF68's: *is the net flow carried
  by a small identifiable set of bridges?* If yes, a flux-space target with an
  equilibrium mask is the right architecture. If no, it is a liability.

**That question, restated as a measurement, is the kill-test** (§0.6). Tier 2
builds every instrument it needs.

### 0.1.3 What the project bets on this hierarchy

Target A predicts a per-reaction flux Φ and maps it through the fixed ν. Three
things make that attractive, and all three are QSE-dependent:

1. **The mask.** If most columns are equilibrated, the model only has to get a
   few dozen bridge fluxes right. That is a far easier learning problem than n
   coupled abundances.
2. **Sparsity of the *net* flow.** Even without a mask, if |φ| is concentrated
   in ≲20 columns, a loss weighted toward those columns is well-posed.
3. **Physical interpretability of errors.** A flux error is attributable to a
   named reaction; an abundance error is not.

Every one of those is a claim about the *data*, not about the architecture. The
honest posture — and the one the repo takes — is that Target A is a hypothesis
with a falsifier attached. §0.6 states the falsifier; Tier 3 reports the
verdict.

> **Read this before Tier 3:** the measured answer is not a clean yes or no.
> The bridge flow *is* concentrated (top-20 columns carry 0.82–0.88 of
> inter-group flux, **[RESULTS]** 2026-07-12) — BCF68's picture survives. But
> the *maskable* set on the label manifold is **empty at every ε**
> (**[RESULTS]** 2026-07-12), because the shipped labels' own equilibria are
> displaced by a MESA bug (Tier 3, S13). Two different claims; the data
> separates them.

---

## 0.2 Silicon burning, mechanically

### 0.2.1 Why ~3 GK is the threshold

Tier 1 §1.4 derived the photodisintegration rate: a reverse (γ, α) rate carries
the factor exp(−Q/kT) relative to its forward (α, γ) partner, times a
phase-space ratio ∝ T^{3/2}. With Q ≈ 5–10 MeV for typical α-captures in the
Si–Ca range and kT = 86.2 keV × T₉,

$$
\frac{Q}{kT} \;=\; \frac{Q\,[\mathrm{MeV}]}{0.0862\,T_9}.
$$

At T₉ = 2 and Q = 7 MeV that exponent is ≈ 41 — reverse rates are suppressed by
e⁻⁴¹ ≈ 10⁻¹⁸, utterly negligible; the flow is a one-way ladder. At T₉ = 4 it is
≈ 20, i.e. e⁻²⁰ ≈ 2×10⁻⁹. At T₉ = 6 it is ≈ 13.5.

**The exponent alone does not give the crossover, and it is worth doing the
comparison honestly**, because the shorthand "e⁻²⁰ against a 10⁻⁹ abundance
factor, so they become comparable" quietly drops the largest term. The
quantity that decides is the ratio of *fluxes*, not of rates:

$$
\frac{\text{reverse flux}}{\text{forward flux}}
\;=\; \frac{\lambda_\gamma\,Y_B}{\rho N_A\langle\sigma v\rangle\,Y_A Y_\alpha},
\qquad
\frac{\lambda_\gamma}{\rho N_A\langle\sigma v\rangle}
\;=\; \frac{9.87\times10^{9}}{\rho}\,T_9^{3/2}\,\Theta\,e^{-Q/kT},
$$

with Θ the O(1) ratio of spin/partition-function/reduced-mass factors. At
ρ = 10⁸ and T₉ = 4 the prefactor is ~10²–10³, so the rate ratio is ~10⁻⁶ rather
than the 2×10⁻⁹ the exponent alone suggests — and *that* is what the light-particle
abundance factor Y_α/Y_B ~ 10⁻⁶ meets. Two factors, both large, pulling the same
way; the qualitative conclusion below survives, but it does not follow from
e^{−Q/kT} on its own. [derived here]

The crossover is sharp because the exponent moves by ~Q/kT per unit relative
change in T: dropping from T₉ = 4 to 3 raises Q/kT from 20 to 27, i.e.
suppresses the reverse by e⁻⁷ ≈ 10⁻³. **The entire regime change from "ladder"
to "equilibrium" happens across less than a factor of two in T** — which is why
the regime box (T₉ 1.6–7.9) spans both, why QSE onset is quoted at ~3–3.3 GK,
and why the kill-test priority window is 3.3–5 GK: that is where the structure
is neither absent (cold) nor total (NSE).

### 0.2.2 Two clusters, one set of bridges

Once photodisintegration is fast, the picture is:

```
        ┌──────────────────────────┐          ┌──────────────────────────┐
        │  SILICON GROUP           │  bridge  │  IRON GROUP              │
        │  24 ≤ A ≤ 44             │ ───────▶ │  45 ≤ A ≲ 60             │
        │  ²⁸Si ²⁹Si ³⁰Si ³¹P ³²S  │  slow    │  ⁴⁵Sc … ⁵²Fe ⁵⁴Fe ⁵⁶Ni …  │
        │  … ⁴⁰Ca ⁴⁴Ti             │          │                          │
        │  internally equilibrated │          │  internally equilibrated │
        └───────────┬──────────────┘          └───────────┬──────────────┘
                    │  ⇅ fast (γ,α)(α,γ)(p,γ)(γ,p)(n,γ)(γ,n)  │
                    └────────── free n, p, α reservoir ────────┘
```

The edges are drawn for the **`default`** group variant, and they are drawn to
the *nucleon*: `configs/qse_groups.yaml` gives `a_max: 45` and the loader applies
`A < a_max` (`qse/diagnostics.py`), so `default` is 24 ≤ A ≤ 44 and ⁴⁵Sc sits on
the **iron** side. The `a24_46` variant moves the line one nucleon up and puts
⁴⁵Sc inside. Getting this off by one is not cosmetic — it is exactly the
difference between ⁴⁵Sc(p,γ)⁴⁶Ti being a bridge and being an internal reaction,
which is the whole content of §III.11.

The mechanism BCF68 identified: ²⁸Si does not fuse with ²⁸Si (the Coulomb
barrier at Z = 14 on Z = 14 is prohibitive at these temperatures — Tier 1
§1.2.4). Instead, *some* ²⁸Si photodisintegrates, releasing α, p, n into a
reservoir; those light particles are then captured by *other* silicon-group
nuclei, walking them upward. The net effect is ²⁸Si → ⁵⁶Ni, but the mechanism
is disassembly-and-reassembly, not direct fusion. Hence "rearrangement".

Consequences that matter for the algebra downstream:

- **The light-particle reservoir is the coupling.** n, p, α are the shared
  currency; they appear in nearly every column of ν. This is why the isotope
  projection of the bipartite graph has radius 1 and diameter 2
  (**[RESULTS]** 2026-07-08): *any* two species are two hops apart through the
  light particles. Message passing over this graph saturates almost
  immediately, which is both good (K = 5 suffices, §I.11) and dangerous (a
  GNN can shortcut everything through p/n/α node features).
- **The bridge set is small and identifiable.** BCF68's structural prediction.
  Measured, on the relaxed manifold: mesa_80's top-5 inter-group carriers are
  Ne22(α,n)Mg25 (share 0.20), Al27(p,α)Mg24 (0.13), P31(p,α)Si28 (0.11),
  Na23(α,p)Mg26, Mg24(n,γ)Mg25; top-20 carry 0.88. mesa_151 adds the
  literature bottleneck ⁴⁵Sc(p,γ)⁴⁶Ti at rank 2/251 under the boundary-at-46
  group variant. **[RESULTS]** 2026-07-12.
- **The group boundary is a modelling choice, not a fact.** Whether ⁴⁵Sc is
  "in" the silicon group changes which reactions count as bridges. The repo
  makes this a config variant (`configs/qse_groups.yaml`: `default`
  24 ≤ A < 45 vs `a24_46`) and requires both to be reported — §III.11.

### 0.2.3 The Fe-peak endpoint, and why Yₑ picks it

At Yₑ = 0.5 (equal protons and neutrons) the most-bound nucleus available is
⁵⁶Ni (Z = N = 28, doubly magic — Tier 0 §0.3.2). Silicon burning at Yₑ = 0.5
terminates on ⁵⁶Ni, which later decays down the A = 56 chain
(⁵⁶Ni → ⁵⁶Co → ⁵⁶Fe, half-lives 6.1 d and 77 d) and powers the supernova light
curve. Both steps are weak, but not the same weak channel: **⁵⁶Ni decays by
electron capture, essentially 100%** — it is not a β⁺ emitter — while ⁵⁶Co is
~81% EC and ~19% β⁺. Worth keeping straight given how carefully §I.5 separates
the two ledgers.

But Yₑ is not 0.5. Electron captures during silicon burning drive it down (Tier
0 §II.5), and at Yₑ < 0.5 the equilibrium favours more neutron-rich Fe-peak
species: ⁵⁴Fe, ⁵⁸Ni, and at lower Yₑ still, ⁵⁶Fe itself. The endpoint of
silicon burning is therefore *a function of Yₑ*, and the ⁵⁶Ni mass that
eventually lights the supernova is set by how much of the burnt material stayed
near Yₑ = 0.5.

This is the physical reason the whole project is organised around Yₑ rather
than around ⁵⁶Ni: **Yₑ is the upstream variable, ⁵⁶Ni the downstream
consequence.** An emulator that gets Yₑ right will get the endpoint right for
the right reason; one tuned on ⁵⁶Ni can be right about ⁵⁶Ni and wrong about
everything else.

### 0.2.4 Why the flow is not a ladder — the trap for intuition

It is very tempting to picture silicon burning as ²⁸Si → ³²S → ³⁶Ar → ⁴⁰Ca →
⁴⁴Ti → ⁴⁸Cr → ⁵²Fe → ⁵⁶Ni, an α-ladder with each rung a net flux. Tier 0 §0.6
already warns about this. Here is why it matters *algebraically*:

If the flow were a ladder, ν restricted to the flow-carrying columns would be
nearly bidiagonal, the net fluxes would be a chain of comparable magnitudes,
and κ would be O(1) on every carrying column. Target A would be trivially
well-posed.

What actually happens is that each ladder rung is a *nearly balanced pair*
(κ ≪ 1) whose small net difference is what advances the chain, while the
light-particle reservoir couples every rung to every other. The net flow
through the ladder is the *residual* of large opposing gross fluxes — which is
precisely the catastrophic-cancellation structure of Tier 0 §V.1, and precisely
what makes κ a condition number (§II.4). **The ladder picture and the
cancellation problem are the same fact seen from two sides.**

---

## 0.3 The Yₑ chain, derived end to end

This section is the "theory behind the motivation". Every gate in `CLAUDE.md`
is a Yₑ gate; this is why.

### 0.3.1 M_ch ∝ Yₑ² — the derivation

Tier 0 §I.2 does this; the short version, because §0.3.4 needs the constant.

A cold, fully degenerate, relativistic electron gas has pressure

$$
P_e \;=\; K\,n_e^{4/3}, \qquad K = \frac{\hbar c}{4}\left(3\pi^2\right)^{1/3},
$$

and n_e = ρ Yₑ / m_u. So P = K (Yₑ/m_u)^{4/3} ρ^{4/3} — a polytrope of index
n = 3. For an n = 3 polytrope the mass is *independent of central density*:

$$
M \;=\; 4\pi\left(\frac{K'}{\pi G}\right)^{3/2}\!\!\cdot\,(-\xi_1^2\theta'(\xi_1)) ,\qquad K' = K\,(Y_e/m_u)^{4/3},
$$

with the Lane–Emden constant −ξ₁²θ′(ξ₁) ≈ 2.018. Since M ∝ K′^{3/2} ∝ Yₑ²,

$$
\boxed{M_{\mathrm{ch}} \;\approx\; 5.83\,Y_e^2\ M_\odot.}
$$

At Yₑ = 0.5, M_ch = 1.46 M_⊙; at Yₑ = 0.45, 1.18 M_⊙. **A 10% change in Yₑ
moves the Chandrasekhar mass by 0.28 M_⊙ — about 19%.** [derived here]

### 0.3.2 Deleptonisation and the homologous core

The iron core grows by silicon shell burning until it exceeds M_ch and
collapses. During collapse, electron capture on free protons and on Fe-peak
nuclei continues to lower Yₑ (to ~0.35 at neutrino trapping, ~0.28 at bounce
**[sourced — verify; Bethe 1990, Rev. Mod. Phys. 62, 801]**). The *inner*
core — the part that collapses subsonically and homologously — has a mass set
by the same M_ch ∝ Yₑ² relation evaluated at the trapped Yₑ, and it is the
inner core's mass that determines where the bounce shock forms.

Two chains, then, both keyed on Yₑ:

```
  Si-burning Yₑ  ──▶ pre-collapse core mass & structure ──▶ compactness
                 ──▶ initial Yₑ for collapse ──▶ trapped Yₑ ──▶ M_inner
                                                            ──▶ shock birth radius
                                                            ──▶ explodability
```

The first is why an *emulator's* Yₑ matters even before collapse: it sets the
initial condition of everything after.

### 0.3.3 The observable end

The chain terminates in things telescopes see:

- **⁵⁶Ni mass** — sets the radioactive tail of the light curve, and in
  *stripped-envelope* events (Ib/c) approximately the peak too, via Arnett's
  rule. **The Arnett-rule-at-peak statement does not transfer to the H-rich
  Type II events a 20 M⊙ progenitor typically produces**: there the plateau is
  powered by hydrogen recombination, and ⁵⁶Ni sets the tail and modulates the
  plateau *length*, not the peak luminosity. Either way, Yₑ sets how much of the
  ejecta reaches ⁵⁶Ni rather than ⁵⁴Fe/⁵⁸Ni.
- **The Fe-peak isotopic ratios** — ⁵⁷Ni/⁵⁶Ni, ⁵⁸Ni/⁵⁶Fe — measured in SN
  remnants and in the solar abundance pattern, and directly sensitive to the
  neutron excess η = 1 − 2Yₑ.
- **The explosion/failure branch** itself, hence the observed
  progenitor-mass–outcome mapping.

Tier 0 **R-21** has the observational grounding in detail. The point for Tier 2 is
just that the chain is *long and multiplicative*, which is what makes the error
budget in §0.3.4 tight.

### 0.3.4 The error budget this implies

Now the part that produces the numbers in `CLAUDE.md`.

Suppose the emulator makes a per-step error δ in Yₑ, and a trajectory has N
steps. Tier 0 §IV.3 derives the accumulation trichotomy:

| error character | accumulated after N steps |
|---|---|
| systematic (biased) | N·δ |
| random walk | √N·δ |
| contractive (stable attractor) | O(δ) |

With N ≈ 1.6×10³ steps and the *conservative* systematic assumption,
demanding a total |ΔYₑ| below the physics floor of ~5×10⁻³ gives

$$
\delta \;\lesssim\; \frac{5\times10^{-3}}{1.6\times10^{3}} \;\approx\; 3\times10^{-6},
$$

which is exactly the operative per-step gate in `CLAUDE.md`. The 5×10⁻³ floor
itself is the FFN→LMP weak-rate-library shift — i.e. **the gate is set by the
size of a known systematic uncertainty in the input physics.** That is the
right way to set it: an emulator whose error is smaller than the disagreement
between two defensible rate libraries is not the limiting factor.

Note what the gate is *conditional on*: the assumption that error accumulates
linearly. `docs/phase0-checklist.md` requires the slope to be measured; if it
turns out to be √N, the gate can relax to ~5×10⁻⁵. This is Tier 0 §VII.3 —
decisions carry their own reversal condition — applied to the project's most
load-bearing number.

**And this is why conservation is not negotiable.** A conservation violation is
*by construction* systematic: it has a fixed sign per step (§0.4.2). It lands
in the worst row of that table. Nothing else in the error budget does.

---

### 0.3.5 The output end — and the derivative nobody has assembled

§0.3.1–§0.3.3 walked Yₑ → M_ch → collapse → ⁵⁶Ni → light curve, and §0.3.4 set
the per-step gate. Before leaving the chain it is worth being explicit about the
end of it that is **not** closed. `tier1.md` §VIII.C.1 flags rate-uncertainty →
Yₑ propagation — the *input* end. This is the *output* end, and nothing flags
it.

§0.3 derives Yₑ → M_ch → collapse → ⁵⁶Ni → light curve qualitatively, and
§0.3.4 sets the per-step gate from the FFN→LMP shift, ΔYₑ = 5×10⁻³–1.5×10⁻².
Note what that is: **an input uncertainty used as an output tolerance**. The
logic — "an emulator whose error is smaller than the disagreement between two
defensible rate libraries is not the limiting factor" — is sound and is the
right way to set a *floor*. But it says nothing about what error would actually
change a scientific conclusion, because the derivatives

$$
\frac{\partial M(^{56}\mathrm{Ni})}{\partial Y_e},\qquad
\frac{\partial (\text{explodability})}{\partial Y_e},\qquad
\frac{\partial (\text{isotopic ratios})}{\partial Y_e}
$$

have never been assembled — not measured here, not cited from the literature,
not estimated. §0.3.1 gets as far as dM_ch/dYₑ (M_ch ≈ 5.83 Yₑ² M_⊙, so
dM_ch/dYₑ = 2 × 5.83 Yₑ = 11.7 Yₑ M_⊙, i.e. **5.8 M_⊙ per unit δYₑ at
Yₑ = 0.5**), and then the chain stops.

Why this is worth closing:

- **It could relax or tighten the gate by orders of magnitude.** If explodability
  is insensitive to δYₑ at 10⁻³, the 3×10⁻⁶ per-step gate is over-engineered by
  a factor of hundreds and the project is paying enormously for it (§IV.9's cost
  wall is downstream of exactly this kind of demand). If some observable is
  sensitive at 10⁻⁴, the gate is right.
- **It is the referee's first question.** "You have built a 3×10⁻⁶-per-step
  emulator; what observable changes at 3×10⁻⁶?" The current answer routes
  through an *input* uncertainty, which is a defensible proxy but is not an
  answer.
- **Much of it is sourceable rather than computable.** The CCSN literature has
  progenitor studies with Yₑ variations; the derivative may be extractable from
  published model grids without running anything. That makes this a *literature*
  task, which is cheaper than it sounds.

`tier1.md` §VIII.E.7 ("residual sourcing gaps in the motivation chain") is the
nearest existing item; this is the specific, actionable form of it.

Open (register: **R-14**) — it is the justification for the project's most
expensive requirement.

---

## 0.4 Why conservation is structural, not a penalty term

### 0.4.1 Conservation laws are left null vectors

Here is the theorem the entire S7 node rests on, stated cleanly.

Let ν ∈ ℝ^{n×r} be the stoichiometric matrix. A vector c ∈ ℝⁿ defines a
**conserved quantity** Q = c·Y of the dynamics ẏ = νR **iff** c is a left null
vector of ν:

$$
\frac{d}{dt}(c\cdot Y) \;=\; c^{\mathsf T}\nu R \;=\; 0 \ \ \forall R
\quad\Longleftrightarrow\quad c^{\mathsf T}\nu = 0.
$$

The "for all R" is the crucial quantifier. It says the conservation law holds
*regardless of the rates* — regardless of temperature, density, screening,
whether the rate library is right, whether the network is converged, or whether
the thing producing R is a stiff ODE solver or an untrained neural network with
random weights. Conservation is a property of the **stoichiometry**, and
stoichiometry is integer bookkeeping.

The set of conserved quantities is therefore exactly the left null space of ν,
a linear subspace, and its dimension is n − rank(ν). This is measurable, and
§I.2.1 measures it.

### 0.4.2 The soft-penalty failure mode, quantified

Suppose instead you train with a penalty: minimise L = L_data + λ‖C·dY‖².
Three things go wrong, in increasing order of severity.

**(i) The violation is O(1/λ), never zero.** At the optimum the penalty
gradient balances the data gradient: ‖C·dY‖ ~ ‖∇L_data‖ / (2λ‖C‖²). You buy
accuracy in conservation with accuracy in the fit, and never reach exact.

**(ii) The violation is systematic.** This is the part people miss. The penalty
is minimised *on the training distribution*; the residual violation is whatever
the data loss pays for. That is a *learned, input-dependent* function, not
noise — it has the same sign for similar inputs. Over a rollout on a smooth
trajectory, consecutive states are similar, so the violations *add coherently*.
Referring to §0.3.4's table: a soft-penalty violation accumulates as N·δ, not
√N·δ.

Do the arithmetic against the right budget, because it is easy to compare an
*accumulated* violation with a *per-step* tolerance and get a wrong answer by
three orders of magnitude. With N = 1.6×10³ the two budgets are δ ≤ 3×10⁻⁶ per
step and 5×10⁻³ over the trajectory (§0.3.4):

| per-step violation | accumulated over N = 1.6×10³ | as a share of the 5×10⁻³ total budget |
|---|---|---|
| 10⁻⁸ | 1.6×10⁻⁵ | 0.3% — genuinely negligible |
| 10⁻⁷ | 1.6×10⁻⁴ | 3% |
| **10⁻⁶** | **1.6×10⁻³** | **32% — a third of the budget, on bookkeeping** |
| 3×10⁻⁶ | 4.8×10⁻³ | 96% — the entire budget, before the model errs at all |

So the honest statement is *not* that a penalty reaching 10⁻⁸ is disqualifying:
at 10⁻⁸ it is fine. It is that (a) the penalty gives you no control over where on
that table you land — §0.4.2(i) says the residual is set by λ against the data
gradient, not by a specification — and (b) because the violation is systematic,
the column that matters is the *accumulated* one, so every decade you fail to buy
costs a factor of ten on a budget you are also spending on real modelling error.
The exact route costs nothing and lands at row zero.

**(iii) It corrupts the physics you care about.** The cheapest way for an
optimiser to reduce ‖C·dY‖ is to shrink dY. The charge row of C includes the
weak-sector dYₑ signal. A penalty therefore applies gradient pressure *against*
the one quantity the project exists to predict. This is `CLAUDE.md` invariant
#3 stated as an optimisation fact: "a design that zeroes it to make the drift
residuals vanish is wrong."

**The alternative costs nothing.** dY = νφ is a matrix multiply with a fixed,
integer-valued, precomputed ν. It is *cheaper* than the penalty (no extra loss
term, no λ to tune) and exactly conserving for any φ. There is no trade-off
being made here — which is why the repo treats it as a floor rather than a
feature.

### 0.4.3 The reachable manifold, restated

Tier 0 §IV.2 introduced the reachable manifold: the set of compositions that a
one-zone burner can actually be in. Tier 2 gives the *linear-algebraic* version
of the same idea, and it is sharper.

At any state Y, the set of *permissible* increments is

$$
\mathcal{M} \;=\; \{\,d\tilde Y \in \mathbb{R}^{n+3} : C\,d\tilde Y = 0\,\},
$$

a linear subspace of codimension rank(C) = 3. Target A's outputs live in
image(ν̃) ⊆ 𝓜 automatically. Target B's outputs are forced into 𝓜 by
projection. §I.10 proves those two sets are **the same** — which reframes the
Target A/B choice entirely: it is not about *what can be expressed*, it is
about parameterisation and conditioning.

---

## 0.5 What physically breaks when a leak happens

Concretely, three things, in the order they bite.

**1. The composition stops being a composition.** ΣXᵢ = ΣAᵢYᵢ = 1 is not a
normalisation convention you can re-impose; it is the statement that the mass
in the zone is the mass in the zone. If Σ Aᵢ dYᵢ = ε per step, then after N
steps ΣXᵢ = 1 + Nε, and every downstream quantity that divides by it — mean
molecular weight, Yₑ = ΣZᵢYᵢ, the mass density of any species — is wrong by that
factor. Renormalising afterwards does not fix it: renormalisation is a
*multiplicative* correction applied uniformly, whereas the leak was
species-specific. You have silently redistributed abundance between species.

**2. The EOS call downstream receives a state that does not exist.** In a real
stellar-evolution timestep the network's output composition is handed to the
equation of state, which computes P(ρ, T, composition) via Ā and Z̄ (Tier 0
§0.1). A composition with ΣX ≠ 1 makes those means ill-defined. The hydro then
integrates a pressure that corresponds to no physical matter. This is the
"deployment coupling contract" that Tier 1 §VIII.E.6 flags as still
unspecified — but the *requirement* is unambiguous: whatever the coupling is,
it will consume ΣX = 1.

**3. Yₑ drifts, so M_ch drifts, so the answer to the science question drifts.**
The charge row is the one with observable consequences. §0.3.1: δYₑ = 10⁻⁴
moves M_ch by ~6×10⁻⁴ M_⊙; accumulated over a trajectory at 10⁻⁶/step it is
1.6×10⁻³ in Yₑ and ~10⁻² M_⊙ — comparable to the differences between
progenitor models that people write papers about.

Which is the argument for the *charge-to-lepton* form of the constraint rather
than plain charge conservation. Yₑ **must** change — that is the physics. What
must not happen is charge appearing or disappearing without a lepton to account
for it. §I.4 builds the ledger that makes this testable rather than tautological.

---

## 0.5b Deployment — what consumes the output, and what speedup is achievable

§0.5 said what breaks when conservation fails, by naming three downstream
consumers. This section makes them explicit — they are **upstream of every
accuracy target in the project** — and then asks the question that decides
whether the project is worth doing at all: what speedup is actually achievable.
`tier1.md` §VIII.E.6 flags the first half as unspecified.

The unanswered question: *what consumes the emulator's output, and what does it
need?*

Concretely, in a stellar-evolution timestep the network's output feeds:

| consumer | needs | sensitivity |
|---|---|---|
| the EOS | Ā, Z̄ from the composition; **requires ΣX = 1** | §0.5 |
| the energy equation | e_nuc (and neutrino losses separately) | §IV.8 |
| the next network call | Y itself — errors compound (§0.3.4) | Tier 0 §IV.3 |
| the opacity / mixing modules | composition | unquantified |

And the operator-split structure (Tier 0 §IV.1) means the emulator's error sits
*inside* an outer error the split already commits. Two things follow that
nobody has computed:

1. **Is the emulator's per-step error large or small compared with the operator
   split's own O(Δt²) commutator error?** If the split error dominates, a
   tighter emulator buys nothing, and the 3×10⁻⁶ gate is over-specified. If it
   does not, the gate is the binding constraint. This is a one-experiment
   question — integrate a zone with split and unsplit couplings and compare —
   and it would either justify or relax the project's most load-bearing number.
2. **Is the coupling (T, ρ)-imposed or thermodynamically fed back?**
   `tier1.md` §VIII.C.4 already flags that everything here is at *imposed*
   (T, ρ), whereas real burning heats the zone, which changes the rates. An
   emulator validated at imposed (T, ρ) has not been validated in the loop it
   will run in, and the loop has a positive feedback (burning → heating →
   faster burning) that can amplify small errors.

Both remain open (register: **R-11**) — the second is the reason the accuracy
gate has the value it has.

### The cost ceiling — why the fallback rate matters more than the speed

---

Tier 0 §I.3 and §I.5 quantify the cost of the network and the speedup that would
matter; the Tier-4 sketch has **S22: UQ, OOD, and the fallback-to-solver gate.**
The arithmetic connecting them is one line, and it is written nowhere.

Let S_raw = t_solver / t_emu be the raw speedup, f the fraction of calls that
fall back to the real solver, and t_det the cost of the out-of-distribution
detector that decides. The emulator and the detector are paid on **every** call;
the solver is paid on the fallback fraction:

$$
S \;=\; \frac{t_{\mathrm{solver}}}{t_{\mathrm{emu}} + t_{\mathrm{det}} + f\,t_{\mathrm{solver}}}
\;=\; \Big(\tfrac{1}{S_{\mathrm{raw}}} + \tfrac{t_{\mathrm{det}}}{t_{\mathrm{solver}}} + f\Big)^{-1}
\;\xrightarrow[\ S_{\mathrm{raw}}\to\infty\ ]{}\; \frac{1}{f}. \qquad\text{[derived here]}
$$

**The achievable speedup is capped at 1/f regardless of how fast the emulator
is.** Tabulated:

| fallback rate f | ceiling on speedup |
|---|---|
| 0.1% | 1000× |
| 1% | 100× |
| 5% | **20×** |
| 20% | **5×** |

Three consequences the project should be carrying and is not:

1. **S22's gate has no target.** A fallback-to-solver gate is specified with no
   stated acceptable fallback rate — but the acceptable rate is *derivable* from
   the speedup that would make the project worthwhile (Tier 0 §I.5 has that
   number). f_max = 1/S_target. That single division turns an unspecified gate
   into a specified one.
2. **The detector is not free and is on the critical path.** t_det is paid on
   every call including the 1 − f that succeed. A detector costing 10% of the
   solver caps the speedup at 10× before any fallback happens. This makes
   "expensive UQ" (ensembles, MC-dropout at inference) structurally
   questionable, and cheap UQ (a single deterministic score) structurally
   preferred — an architecture constraint arriving from economics rather than
   from statistics.
3. **Batching interacts badly with fallback.** In a stellar code the network is
   called per zone per timestep, and zones are naturally batched. If fallback is
   decided per zone, a batch containing one fallback zone pays both costs and
   may lose vectorisation on the rest. The effective f is then closer to
   *the probability that a batch contains any fallback* — which for batch size
   B and independent zones is 1 − (1−f)^B, dramatically worse: at f = 1% and
   B = 100, 63% of batches contain a fallback. Whether that matters depends
   entirely on the coupling contract (§0.5b), which is unspecified.

Open (register: **R-12**) — arithmetic, an hour's work, and it converts two
unspecified design targets into numbers.

---

## 0.6 The decision this tier serves

Everything in Tier 2 is instrumentation for one decision, and it is worth
writing the decision down as a linear-algebra question before building the
tools.

> **Kill-test.** Let 𝒜 = {j : κ_j > 0.1} be the *active set* — the columns not
> in near-balance. Restricted to 𝒜, is the map φ ↦ νφ well-conditioned, and
> does it carry the physics?

Operationally, from `CLAUDE.md`:

| quantity | pass | fail | tool |
|---|---|---|---|
| coverage: fraction of dominant-isotope \|ΔX\| and of \|ΔYₑ\| carried by 𝒜 | ≥ 95% | — | §II.4, `killtest.active_set.carried_fractions` |
| spread: share of net columns near the κ floor | — | > ~30% | §II.9 |
| cond(S_active) = cond(ν restricted to 𝒜) | < 10⁶ | > 10⁸ | §I.2.1, `cond_s_active` |
| maskable-set size under the Guidry ε sweep | non-empty | empty ⇒ full-width | §III.10 |

If it passes, Target A with an equilibrium mask is the architecture. If it
fails — either because the flow spreads over too many near-cancelled columns,
or because the restricted ν is ill-conditioned — the project falls back to
Target B: predict dY directly in a linear space and project.

**Notice what each tool in this tier is for**, now that the question is stated:

- S7 gives ν, C, P, and cond(·) — the *conditioning* half of the question, and
  the fallback (Target B) if the answer is no.
- S8 gives κ and the coverage statistics — the *active set* half.
- S9 gives the independent NSE/QSE reference, without which "in equilibrium"
  has no measurable definition, and the Guidry δ criterion that defines
  maskability.
- S10 gives the reference integrator that produces the Φ labels Target A needs
  and that the shipped dataset does not contain.

Nothing in this tier is exploratory. Every module answers a clause of that one
question.

---

## 0.7 What is *not* in this tier

To keep the boundaries clean:

- **Where λ comes from** — Tier 1. Tier 2 consumes λ and asks nothing about its
  provenance except that the pf gate held.
- **Silicon burning as a physical process on real trajectories, the label
  pathology, the verdict** — Tier 3 (S11–S16). Part 0 gives the *theory* of Si
  burning because the algebra needs it; the *measurements* on actual burning
  histories are one tier later.
- **The emulator** — Tier 4, unwritten (`tier1.md` §VIII.E.1).
- **Screening and the two-κ convention** — Tier 1 §IV. Tier 2 uses the rule
  (equilibrium detection on unscreened κ) without re-deriving the offset.

## 0.8 Self-check for Part 0

Answer without scrolling up.

1. NSE has 2 free parameters given (T, ρ, Yₑ). Where does the number 2 come
   from, and what breaks the count for QSE?
2. Why does silicon burning proceed by disassembly-and-reassembly rather than
   by ²⁸Si + ²⁸Si?
3. Write M_ch ∝ Yₑ² and say which step of the derivation makes the mass
   independent of central density.
4. State the theorem "conservation laws are left null vectors" including the
   quantifier that makes it load-bearing.
5. A soft conservation penalty achieves ‖C dY‖ ~ 10⁻⁸ per step. Work out what
   that accumulates to over N = 1.6×10³ steps and compare it against the *right*
   budget — then say why the penalty is still the wrong design in two
   independent ways that have nothing to do with that number.
6. Why is the constraint *charge-to-lepton closure* rather than charge
   conservation?
7. State the kill-test as a question about a matrix, and name which Tier-2 node
   supplies each of its four measured quantities.

---

# Part I (S7) — Stoichiometry and the conservation layer

**The floor.** `tests/test_conservation.py` is the one test in the repo that is
allowed to block training. This part is what it means.

The plan of attack: build ν (§I.1), prove that conservation laws are its left
null space and *measure* that null space (§I.2), watch the weak sector break
charge conservation (§I.3), repair it with an independent lepton ledger
(§I.4–I.5), assemble C (§I.6), get Target A's theorem for free (§I.7), derive
the Target B projector twice (§I.8–I.9), prove the two targets reach the same
set (§I.10), and read the code and the oracle (§I.12–I.13).

---

## I.1 ν as a linear map

`graph/stoich.py` builds ν in nine lines:

```python
for j, rate in enumerate(rates):
    for sp in rate.reactants:
        nu[idx[sp], j] -= 1.0
    for sp in rate.products:
        nu[idx[sp], j] += 1.0
```

That is the entire construction. ν[i, j] is the **net** change in the count of
species i per unit progress of reaction j: products positive, reactants
negative, with repeated participants accumulating (triple-α gives ν[he4, j] =
−3).

Three structural facts follow immediately, and each matters later.

**(a) Column order is the contract.** ν's columns are `list(rc.get_rates())` in
pynucastro's order, and *every* downstream array — λ, R, f⁺, φ, κ, Φ,
`pair_col`, `weak_mask`, `Q`, `chapter` — is indexed by the same j.
`fluxes/compile.py` asserts this alignment against `Stoich.rate_fnames` and
raises if a v-flag replacement changed a column identity. Tier 1 **R-17**'s
canonical key exists so that "same reaction" is decidable; this is where that
decidability is cashed in. A column-order bug would be silent and catastrophic:
every conservation test would still pass (§I.2 holds for *any* ν), while every
flux would be attached to the wrong reaction.

**(b) ν is *net*, so catalysts vanish.** A species that appears on both sides
(consumed and produced) gets the difference. This is why `export.bipartite_digraph`
adds *both* an I→R and an R→I edge for such a species: the graph keeps the
information ν throws away. For the conservation algebra the net form is what
you want; for message passing it is not, and the graph is the compensating
structure.

**(c) ν is extremely sparse and hub-dominated.** [derived here] Measured on the
reconciled export:

| | mesa_80 | mesa_151 |
|---|---|---|
| shape (n × r) | 80 × 607 | 151 × 1518 |
| nonzeros | 2012 | 5004 |
| density | 4.1% | 2.2% |
| participants per column (mean / max) | 3.31 / 5 | 3.30 / 5 |
| ⁴He appears in | 319 columns (52.6%) | 695 (45.8%) |
| ¹H / n appear in | 246 / 247 | 644 / 643 |
| next-highest species degree | ¹²C, ¹⁶O: 32 | ¹⁶O: 35 |

```python
import numpy as np
d = np.load("data/stoich/nu_mesa80.npz"); nu = d["nu"]; sp = list(d["species"])
part = nu != 0
print(part.sum(), part.sum()/nu.size, part.sum(0).mean(), part.sum(0).max())
print([(sp[i], int(part.sum(1)[i])) for i in np.argsort(-part.sum(1))[:6]])
```

The degree distribution has a cliff: three light species with degree 250–700,
then everything else at ≤ 35. **⁴He, ¹H and n are not species in this network so
much as they are the network's wiring.** This single fact explains §0.2.2's
reservoir picture, the graph radius of 1 in the isotope projection (§I.11), and
a real architectural hazard: a message-passing model can route almost any
influence through three hub nodes in two hops, which is both why K = 5 suffices
and why an ablation that damages the hub features would be uninformative about
whether the model learned the chemistry.

---

## I.2 Conservation is the left null space — with the measurement

§0.4.1 stated the theorem. Here it is used.

### I.2.1 The rank measurement — and why it is the most informative number in S7

The left null space of ν is $\operatorname{null}(\nu^{\mathsf T})$ — the set of all
conserved linear combinations. Its dimension is n − rank(ν). Measure it:

```python
import numpy as np
d  = np.load("data/stoich/nu_mesa80.npz")
nu, A, Z = d["nu"], d["A"], d["Z"]
U, S, Vt = np.linalg.svd(nu)
k = (S > 1e-12 * S[0]).sum()                 # numerical rank
L = U[:, k:]                                 # basis of the left null space
print(nu.shape, k, nu.shape[0] - k, np.linalg.norm(L.T @ (A/np.linalg.norm(A))))
```

**[derived here]**, at the reconciled export:

| quantity | mesa_80 | mesa_151 |
|---|---|---|
| rank(ν) | 79 | 150 |
| **left-nullity of ν** | **1** | **1** |
| ‖proj of Â onto left-null(ν)‖ | 1.0000 | 1.0000 |
| left-nullity of ν restricted to *strong/EM* columns | **2** | **2** |
| … and it is exactly span{A, Z} (both principal angles 0) | ✓ | ✓ |
| rank(ν̃) (extended, with lepton rows) | 80 | 151 |
| **left-nullity of ν̃** | **3** | **3** |
| … and it is exactly rowspace(C) (all three principal angles 0) | ✓ | ✓ |
| right-nullity of ν (= r − rank) | **528** | **1368** |
| cond(ν) (extreme nonzero singular values) | 41.57 | 57.86 |
| cond(ν̃) | 40.90 | 54.54 |
| cond(CCᵀ) | 3.947×10⁴ | 1.029×10⁵ |

Read those rows one at a time; each is a physical statement.

**Left-nullity of ν is 1, and the null vector is A.** Mass number is the *only*
linear combination of nuclear abundances conserved by every column. There are
no accidental extra conservation laws hiding in the network — no coincidental
degeneracy that a naive projector would have to be told about, and no missing
constraint the gate could be blind to. It also means the constraint set cannot
be *over*-specified: C's three rows are all doing work.

**Restricted to strong/EM columns, the nullity is 2, and the space is exactly
span{A, Z}.** This is §I.3's fact, measured: charge is conserved by the strong
sector and only by the strong sector. The measurement (principal angles between
span{A, Z} and the computed left null space, both exactly 1.0 in cosine) is a
much stronger statement than "Z·ν = 0 on strong columns" — it says there is
nothing *else* conserved there either.

> **Corollary, and it is the most consequential thing in this table.** Every
> increment the strong sector can produce satisfies Z·dY = 0 exactly, i.e.
> **dYₑ = 0**. The strong sector is fast and carries essentially all of the
> composition change; therefore essentially all of the *composition variance* is
> Yₑ-neutral, and the Yₑ signal is structurally confined to the slow, small weak
> sector. Measured consequence: over the visited compositions, Var(X) converges
> to 99.7% / 98.1% by 30 principal components while Var(Yₑ) stalls at 93.0% /
> 95.3% — the Yₑ signal is smeared across a long low-variance tail, and the
> per-step budget needs 1 − 6.5×10⁻⁸ of it. Variance-truncated compression of
> the composition is therefore arithmetically excluded, not merely risky.
> **§I.10b** measures it; this row is the reason it must come out that way.

**Left-nullity of ν̃ is 3, and the space is exactly rowspace(C).** This is the
completeness statement, and it is the one I would not have guessed. It says C is
neither missing a constraint (else the nullity would exceed 3) nor imposing a
redundant one (else rank(C) < 3, caught by `build_projector`). **The projector
removes exactly the physical constraints and nothing else.**

```python
nx, C = d["nu_ext"], d["C"]
Ue, Se, _ = np.linalg.svd(nx); ke = (Se > 1e-12*Se[0]).sum()
Qc, _ = np.linalg.qr(C.T)
print(np.linalg.svd(Qc.T @ Ue[:, ke:], compute_uv=False))   # -> [1. 1. 1.]
```

**Right-nullity is 528 (1368).** The map φ ↦ νφ has a 528-dimensional kernel.
Take this seriously: **the flux vector is not determined by the abundance
change.** Given a target ΔY there is a 528-parameter family of φ producing it.
Consequences, all of which reappear later:

- A loss defined only on ΔY leaves 528 directions of φ completely
  unconstrained. Target A therefore *needs* flux-space supervision, which is
  why `integrate.py` exists (§IV.3–IV.4) and why the shipped Zenodo labels
  (which carry only ΔX) are insufficient for it.
- Conversely, the redundancy is what makes the mask meaningful: killing a
  column changes φ without necessarily changing νφ much.
- And it is why cond(ν) alone does not settle the kill-test. cond(ν) = 41.6 is
  benign; the kill-test's cond(S_active) restricts to the *active* columns,
  which is a different matrix (**[RESULTS]** 2026-07-12: 41.8/57.4, essentially
  the full-ν value, because the active set turned out to be everything).

**cond(ν) ≈ 42–58 is small, and that is a real result.** It bounds how much a
relative error in φ can be amplified into dY: ‖δ(νφ)‖/‖νφ‖ ≤ cond(ν)·‖δφ‖/‖φ‖
for φ in the row space. Two orders of magnitude of headroom below the 10⁶ gate.
The dangerous conditioning in this project is *not* in ν; it is in the
cancellation within φ itself (§II.4).

### I.2.2 Why the tests can demand exactly 0.0

`tests/test_conservation.py::test_exported_columns_conserve_exactly` asserts

```python
assert dA[j] == 0.0
```

Zero tolerance. That is unusual enough to justify.

ν's entries are small integers — measured over both exports, the set is exactly
{−3, −2, −1, +1, +2, +3}, with max 5 participants per column and no coefficient
beyond 3 (±3 is triple-α and its reverse). A and Z are integers ≤ 151 and
≤ 28. The column sum Σᵢ Aᵢνᵢⱼ is therefore a sum of at most 5 products of
integers bounded by ~450 in magnitude. **Every intermediate value is exactly
representable in float64** (integers up to 2⁵³), and IEEE-754 addition of
exactly-representable integers whose exact sum is also representable is exact.
So the computed sum is the exact mathematical sum, and the exact sum is 0 by
construction of the reaction.

This is why `build_stoich` uses `!= 0.0` rather than a tolerance in its
fail-loud validation, and why `graph/metrics.drift_metrics` reports D_A = D_Q =
0.0 exactly rather than "≤ 10⁻¹⁶". **[RESULTS]** 2026-07-08 records the column
drifts as exactly 0.0.

The *random-φ* drift test is a different animal, because φ is not an integer.
There, Σᵢ Aᵢ(νφ)ᵢ = Σⱼ (Σᵢ Aᵢνᵢⱼ) φⱼ = Σⱼ 0·φⱼ mathematically, but the
computation does the sums in the other order and float64 rounding of the
intermediate νφ survives. The residual is bounded by float64 ε times the
*gross* throughput G = |A|·(|ν|·|φ|), which is exactly the tolerance the module
docstring defines:

$$
\text{tol} \;=\; \max\!\big(10^{-12} s,\ 10^{-13} G\big),\qquad s = \min(1, \max_j|\varphi_j|).
$$

The rationale is Tier 0 §V.4's: an absolute bound is the right statement at
O(1) magnitudes and *vacuous* at φ ~ 10⁻²⁰ (where any implementation passes),
so the small end gets a relative-to-gross bound instead — at 10⁻¹³·G, about a
thousand times looser than float64 ε accumulation, i.e. tight enough to catch a
real bug and loose enough not to be a fp-noise flake. **Every threshold in this
project sits just above a measured floor** (Tier 1's closing habit); this one
sits above ε·G.

---

## I.2b The same object in another literature — CRN theory, deficiency, and the flux cone

Everything §I.2 just derived — ν, its left null space as conservation laws, its
right null space as flux redundancy, the reachable set as an affine subspace
intersected with the positive orthant — is standard material in two mature
literatures that nuclear astrophysics and this repo do not appear to cite. Worth
knowing here rather than later: the vocabulary unlocks fifty years of results,
and one of the theorems very nearly applies.

- **Chemical Reaction Network Theory** (Horn & Jackson 1972; Feinberg's
  deficiency theory, 1972–1987, collected in *Foundations of Chemical Reaction
  Network Theory*, Springer 2019) **[sourced — verify]**;
- **Stoichiometric / metabolic network analysis** (Schuster & Hilgetag 1994 on
  elementary flux modes; Palsson's flux balance analysis; Klamt & Stelling on
  extreme pathways) **[sourced — verify]**.

### The vocabulary map

Worth memorising, because it unlocks fifty years of results and algorithms:

| this project | CRN / systems biology | where in Tier 2 |
|---|---|---|
| ν, stoichiometric matrix | S, the stoichiometric matrix | §I.1 |
| left null space of ν | *conservation relations*, moiety conservation | §I.2.1 |
| right null space of ν | the **null space of S**; steady-state flux space | §I.2.1, §IV.4 |
| φ, net flux vector | v, the flux vector | §II.1 |
| Y₀ + image(ν) ∩ {Y ≥ 0} | **stoichiometric compatibility class** | Tier 0 §IV.2, §I.7b |
| the equilibrium mask | *blocked* / *fixed* reactions | §III.10 |
| bridge reactions carrying the net flow | **elementary flux modes**, extreme pathways | §0.2.2 |
| Target A (predict φ, map through ν) | flux-based network parameterisation | §I.7 |

### Deficiency — measured, and the honest answer

The headline theorems of CRN theory are stated in terms of the **deficiency**

$$
\delta \;=\; n_{\mathrm{complexes}} \;-\; \ell \;-\; \operatorname{rank}(\nu),
$$

with n_complexes the number of distinct reactant/product multisets and ℓ the
number of linkage classes (connected components of the complex graph). The
**Deficiency Zero Theorem** says: a weakly reversible network with δ = 0 has,
for *every* choice of positive rate constants, exactly one positive equilibrium
in each stoichiometric compatibility class, and it is locally asymptotically
stable. That would be an extraordinarily strong statement about this system —
existence and uniqueness of NSE, and stability of the QSE manifold, *for free*,
independent of the rate library.

It does not apply. **[derived here]**:

```python
# complexes = distinct reactant / product multisets, one edge per column
```

| | mesa_80 | mesa_151 |
|---|---|---|
| complexes n_c | 278 | 561 |
| linkage classes ℓ | 73 | 84 |
| rank(ν) | 79 | 150 |
| **deficiency δ** | **126** | **327** |
| strongly connected components (directed complex graph) | 81 | 93 |
| weakly connected components | 73 | 84 |
| **weakly reversible?** | **no** | **no** |

Both hypotheses fail, and instructively:

- **δ = 126 / 327 is enormous**, not marginal. Deficiency counts the mismatch
  between the *complex*-level and *species*-level descriptions; a network of
  607 reactions built from three light particles interacting with 77 heavy
  species has an enormous number of distinct complexes relative to its
  stoichiometric rank. No amount of tidying reduces this to zero.
- **Weak reversibility fails by exactly the weak sector.** The SCC/WCC gap is 8
  and 9 — the same order as the number of one-way weak channel families. β-decay
  and electron capture have no inverse in this regime (§II.2), which is a
  *physical* irreversibility, not a modelling omission.

So: the theorems give nothing. That is a real, checkable, negative result, and
it is worth having because the natural hope ("surely CRN theory tells us the
QSE manifold is stable") is now closed rather than open.

### What CRN theory *does* give: the flux cone

The part that transfers directly is the geometry of the flux space.

With irreversibility constraints (weak columns are one-way, φ_j ≥ 0), the set
of admissible steady-state flux vectors is a **polyhedral cone**

$$
\mathcal{C} \;=\; \{\varphi : \nu\varphi = 0,\ \varphi_j \ge 0 \ \forall j \in \text{irrev}\},
$$

and the **elementary flux modes** are its extreme rays — the minimal sets of
reactions that can sustain a steady flow. "Which small set of reactions carries
the net flow from the silicon group to the iron group" (§0.2.2, the whole bridge
programme) *is* the extreme-pathway question, and it has:

- an exact algorithm (the double-description method; `efmtool` and successors),
- a large literature on **network reduction** driven by the same question,
- and known scaling limits (EFM enumeration is combinatorially explosive, which
  is why flux-*sampling* and flux-balance optimisation are used instead at
  scale).

The repo's bridge discovery (`scripts/step5_bridges.py`) is an empirical,
flux-weighted, per-state version: rank columns by |ν φ| across the group
boundary. That is a perfectly reasonable estimator, and it answers a slightly
different question — *which bridges are used on this manifold*, not *which
bridges exist*. Both are worth having, and the second is currently unasked.

**What remains open** (register: **R-09**). Not because the project is doing
anything wrong, but because (i) a reviewer from computational systems biology
will ask why elementary flux modes are not cited, (ii) the reduction literature
there is directly relevant to the network-reduction prior art `tier1.md`
§VIII.C.7 already flags as under-surveyed, and (iii) the flux cone is the correct
geometric object for "what fluxes are admissible" — exactly what a
flux-predicting emulator should be constrained to. A literature and framing gap,
not a correctness gap.

---

## I.3 The weak sector breaks charge conservation — on purpose

For a strong or electromagnetic reaction, both A and Z are conserved by the
*nuclei alone*:

$$
\sum_i A_i \nu_{ij} = 0, \qquad \sum_i Z_i \nu_{ij} = 0 \qquad (j \text{ strong/EM}).
$$

For a weak reaction, the first still holds — β-decay and electron capture move
a nucleon between the proton and neutron states without changing A — but the
second does not:

$$
\sum_i Z_i \nu_{ij} = \Delta Z_j = \pm 1 \qquad (j \text{ weak}).
$$

Measured over the whole export: `(Z @ nu)[~weak]` is exactly 0 everywhere, and
`(Z @ nu)[weak]` takes exactly the values {−1, +1} — no other value occurs, in
either network. [derived here]

This is not a defect to be repaired; **it is the physics the project exists to
predict.** Yₑ = ΣZᵢYᵢ, so

$$
\frac{dY_e}{d\varphi_j} \;=\; \sum_i Z_i \nu_{ij} \;=\; \Delta Z_j,
$$

and a network in which Σ Zᵢνᵢⱼ = 0 for *every* column is a network in which Yₑ
can never change. `CLAUDE.md` invariant #3 is the guard against
"fixing" it: any design that zeroes the weak dYₑ to make residuals vanish has
deleted the answer.

So the constraint cannot be "charge is conserved". It has to be **charge is
conserved once you count the leptons**, which requires knowing, per column,
where the charge went. That is the ledger.

---

## I.4 Lepton ledgers — and the tautology trap

`stoich.py` assigns three extra rows per column from the rate's `weak_type`:

| weak_type | d_e⁻ | d_ν | d_ν̄ | effect on Yₑ |
|---|---|---|---|---|
| `electron_capture` | −1 | +1 | 0 | lowers |
| `beta_neg` | +1 | 0 | +1 | raises |
| `beta_pos` | −1 | +1 | 0 | lowers |

Then ν̃ = vstack(ν, d_e, d_ν, d_ν̄), shape (n+3) × r.

**The trap, and why the docstring shouts about it.** There is an obvious way to
fill these rows: read Δ Z_j = Σᵢ Zᵢνᵢⱼ off the nuclear part and set
d_e = ΔZ. It would always work, would never fail a test, and would make the
entire charge-to-lepton closure check **a tautology** — you would be verifying
that a number equals itself.

Instead the ledger is assigned from the rate's *declared type*, which comes
from a completely different place: pynucastro's classification of the rate
object (`rate.weak_type`, ultimately from the REACLIB/tabular metadata),
reconciled against MESA in Tier 1 §VI. The closure check

```python
if dq != d_e[j]:
    raise ValueError(f"... nuclear ΔZ = {dq} but ledger d_electron = {d_e[j]} "
                     "— charge-to-lepton closure broken")
```

is then a genuine cross-check between two independent descriptions of the same
reaction: *the stoichiometry of the nuclei* and *the declared weak channel*.
If a rate were mislabelled — an EC filed as a β⁻ — this catches it, loudly, by
name, at build time.

This is Tier 1 §VIII.D's habit applied prospectively rather than
retrospectively: *ask of any green test what would still be wrong if it
passed.* A back-derived ledger passes always and detects nothing. Two of the
build's five fail-loud validations ($|\Delta Z| \ne 1$; `dq != d_e[j]`) exist only
because the ledger is independent.

**The lepton-number row.** The third row makes lepton number close per column:

$$
\Delta L_j \;=\; d_{e^-,j} + d_{\nu,j} - d_{\bar\nu,j} \;=\; 0.
$$

Check each: EC gives (−1) + (+1) − 0 = 0 ✓; β⁻ gives (+1) + 0 − (+1) = 0 ✓;
β⁺ gives (−1) + (+1) − 0 = 0 ✓. The sign on ν̄ is −1 because an antineutrino
carries lepton number −1. `test_toy_lepton_number_closes_per_weak_column` and
`test_exported_lepton_ledgers_close` assert exactly this, and additionally that
the ledger rows are identically zero on strong columns.

---

## I.5 β⁺ and the annihilated positron

β⁺ and EC share a ledger signature — (−1, +1, 0) — which looks wrong at first
sight, because β⁺ *emits* a positron whereas EC *absorbs* an electron.

The resolution is the plasma. A positron emitted into silicon-burning matter at
T₉ ~ 4, ρ ~ 10⁸ has a mean free path against annihilation vastly shorter than
anything else in the problem: it finds an ambient electron and annihilates
essentially instantly (the e⁺e⁻ → 2γ cross-section at thermal energies, times
n_e ~ 10³¹ cm⁻³, gives a lifetime far below any timestep in the regime box).
So the *net* effect of a β⁺ decay on the composition is:

```
  nucleus:      Z → Z−1              (ΔZ_nuclear = −1)
  positron:     emitted, then annihilates with a plasma electron
  net electron ledger:  −1           (one electron removed from the sea)
  neutrino:     +1 ν_e emitted
  photons:      2 × 511 keV, thermalised
```

Charge closes: the nucleus loses one unit, the electron sea loses one electron,
total change zero. Lepton number closes through the ν_e: the emitted e⁺
(L = −1) and the absorbed e⁻ (L = +1) cancel, leaving the ν_e's +1 balanced
against… nothing? No — the emitted e⁺ has L = −1, so the pair (e⁺, ν_e) from
the decay already has ΔL = 0, and the *subsequent* annihilation removes an
ambient e⁻ (L = +1) together with the e⁺ (L = −1), also ΔL = 0. In the
ledger's bookkeeping, which tracks only the persistent species, the composite
process is "one electron removed, one neutrino emitted": (−1) + (+1) − 0 = 0. ✓

**Both EC and β⁺ therefore lower Yₑ; only β⁻ raises it.** Which is why the
weak-sector census counts *directions*: mesa_80 has 46 weak columns = 21 EC +
19 β⁻ + 6 β⁺ (27 lower Yₑ, 19 raise); mesa_151 has 174 = 84 + 85 + 5 (89 lower,
85 raise). **[RESULTS]** 2026-07-08 — note this is the provisional 610/1522
export; the reconciled export has 46/173 weak columns [derived here].

The 511 keV photons are *not* in any ledger, and that is a deliberate omission
worth noting: they go into the thermal bath, i.e. into e_nuc. §IV.8's energy
identity accounts for them only insofar as the rate Q-value does. Tier 1
§VIII.C.3's dropped-neutrino-column item lives in the same neighbourhood.

---

## I.6 The constraint matrix C

```python
def constraint_matrix(A, Z):
    n = len(A)
    C = np.zeros((3, n + 3))
    C[0, :n] = A                # baryon number
    C[1, :n] = Z; C[1, n] = -1  # charge  (electron carries −1)
    C[2, n] = +1; C[2, n+1] = +1; C[2, n+2] = -1   # lepton number
    return C
```

Three rows over the extended species list [nuclei…, e⁻, ν, ν̄]:

| row | reads | why the entries are what they are |
|---|---|---|
| baryon | Σ Aᵢ dYᵢ | leptons have A = 0 |
| charge | Σ Zᵢ dYᵢ − dY_{e⁻} | the electron's charge is −1, so its *column* entry is −1; ν, ν̄ are neutral |
| lepton | dY_{e⁻} + dY_ν − dY_{ν̄} | e⁻ and ν carry L = +1, ν̄ carries −1; nuclei carry 0 |

And the build asserts `max |C @ nu_ext| == 0.0` exactly, for the same
integer-arithmetic reason as §I.2.2.

**Why the charge row is the interesting one.** It does *not* say "nuclear
charge is conserved". It says nuclear charge change is exactly matched by the
electron ledger. Yₑ is free to move; the *books* must balance. This is the
formal version of §0.5's third point.

**rank(C) = 3, and cond(CCᵀ) = 3.95×10⁴ / 1.03×10⁵.** [derived here; matches
**[RESULTS]** 2026-07-08]. The conditioning is entirely a units artefact: row 0
has entries up to 151, row 2 has entries of size 1, so CCᵀ has diagonal entries
spanning ~4–5 orders. `build_projector` sidesteps it by never forming CCᵀ
(§I.8). Nothing here is near-singular in any physical sense — rank-deficiency
would mean one of the three bookkeeping laws was a combination of the others,
which it manifestly is not, and `test_projector_rejects_rank_deficient_C`
checks that the guard fires when it is.

---

## I.7 Target A's theorem

Now everything is in place, and the central result is one line.

> **Theorem (Target A conserves).** For *any* φ ∈ ℝ^r,
> dỸ = ν̃φ satisfies C·dỸ = (Cν̃)φ = 0·φ = 0.

That is it. No assumption on φ: not smallness, not sign, not smoothness, not
that it came from a trained model. A randomly initialised flux head satisfies
it. A flux head predicting nonsense satisfies it. A flux head with NaNs
satisfies it in the sense that the constraint residual is NaN·0 — which is why
the gate also checks finiteness implicitly through the magnitude sweep.

**Accuracy determines *which* conserving update is produced; it can never
determine *whether* it conserves.** That sentence is the docstring of
`tests/test_conservation.py` and the design principle of the entire project.

Two immediate corollaries used later:

**Corollary 1 (masking is safe).** If the flux head's output is multiplied
elementwise by any gate g ∈ ℝ^r, the result ν̃(g ⊙ φ) is still in null(C) —
because g ⊙ φ is still just some vector in ℝ^r. Column-scaling a stoichiometric
matrix cannot break its column sums. `test_toy_mask_never_touches_weak_columns`
and `test_exported_mask_contract_on_real_matrix` verify this with a *random*
gate, which is the right test: the point is that no property of the gate is
required.

But note carefully what that corollary does *not* license. Masking is safe for
conservation and unsafe for physics: gating a weak column to zero conserves
everything perfectly while deleting dYₑ. Hence invariant #2 is a *separate*
structural rule — `eligible_mask` takes `weak_mask` and excludes it by
construction — rather than something conservation could have enforced.

**Corollary 2 (the update is exact in float64 too).** dY = νφ is a matvec with
integer entries; the error is bounded by ε·(|ν|·|φ|), the gross throughput,
which is exactly the tolerance shape of §I.2.2.

---

## I.7b What Target A does *not* guarantee — positivity

§I.7's theorem holds for *any* φ, and its corollaries drew out what that buys.
This section draws out what it does **not**. Conservation is enforced to machine
precision by a matrix multiply; **positivity is not enforced at all**, at any
point in the emulator design. The same "for all φ" quantifier is responsible for
both.

### The geometry

The physical state space is not a linear subspace. It is the polytope

$$
\mathcal{P} \;=\; \Big\{\,Y \in \mathbb{R}^n \ :\ Y_i \ge 0\ \forall i,\ \ \textstyle\sum_i A_iY_i = 1 \,\Big\},
$$

a simplex-like object with n facets. In CRN language (§I.2b) the reachable set
from Y₀ is the **stoichiometric compatibility class** (Y₀ + image(ν)) ∩ 𝒫 —
Tier 0 §IV.2's "reachable manifold", now with its correct geometry: an affine
subspace intersected with a cone.

Conservation-by-construction handles the *affine subspace* exactly. Nothing
handles the *cone*.

### Why it is not a small problem here

- **dY = νφ can take any species negative**, for the same reason it conserves:
  the theorem holds for arbitrary φ, and "arbitrary" includes fluxes that drain
  a species past zero. The projector P has the same property.
- **Abundances span 15+ decades**, so "slightly negative" is not
  well-defined — a species at 10⁻²⁵ is thirty orders below the dominant one, and
  an absolute error of 10⁻¹⁸ makes it negative.
- **Rates are built from products of Y** (§II.1). A negative Y propagates into
  R with an unphysical sign, and for a column with a repeated reactant (Y³ in
  triple-α) it propagates with an unphysical *magnitude* too.
- **In rollout it compounds**: a negative abundance produces a negative
  destruction rate, which *grows* the negative value. This is a divergence
  mechanism entirely separate from the usual rollout-instability story, and it
  belongs in the Tier-4 S20 node that does not exist yet.

The reference integrator does address it, minimally and correctly: Y is clipped
at 0 **inside rate evaluation only**, never in the solver state (§IV.2), so the
regularisation cannot inject mass. That is the right pattern, and it is a
*solver* pattern — nothing equivalent exists on the emulator side.

### What the literature offers

Two families, and the second is the one the project has not met:

1. **Positivity-preserving projection** — project onto the constraint manifold,
   then backtrack along the correction until positivity holds. The
   architecture docs cite Kircher & Votsmeier 2025 for exactly this
   **[sourced — verify]**, so this is known to the project at the *citation*
   level; it is absent from the study map, from the code, and from the gate
   list.
2. **Modified Patankar schemes** — Burchard, Deleersnijder & Meister 2003, *A
   high-order conservative Patankar-type discretisation for stiff systems of
   production–destruction equations* **[sourced — verify]**. These are built for
   exactly the system shape here, ẏ = P(y) − D(y), and are **unconditionally
   positive *and* exactly conservative**, simultaneously, for any step size. The
   trick is to weight destruction terms by y_i^{n+1}/y_i^{n}, which makes the
   scheme implicit in a way that cannot cross zero. That is a strong existence
   result: **conservation and positivity are not in tension**, and a scheme
   achieving both already exists in the production–destruction literature.

Whether an MPRK-style construction can be made differentiable and cheap enough
to sit in a decode step is an open question — but the fact that the two
constraints are jointly achievable is exactly the sort of thing you want to know
before designing around a supposed trade-off.

### The minimum that should exist now

A diagnostic, not an architecture: on any predicted update, report
`min_i (Y_i + dY_i)` and the fraction of (state, species) cells going negative,
stratified by abundance decade. Zero cost, and it converts an unknown into a
number. Open (register: **R-04**).

---

## I.8 The Target B projector, derived twice

Target B predicts dỸ directly and repairs it. The repair operator:

### Derivation 1 — minimum correction (Lagrange)

Given a raw output v ∈ ℝ^{n+3}, find the nearest point on the constraint
manifold:

$$
\min_{w}\ \tfrac12\|w - v\|_2^2 \quad\text{s.t.}\quad Cw = 0 .
$$

Lagrangian L = ½‖w−v‖² + λᵀCw. Stationarity: w − v + Cᵀλ = 0 ⇒ w = v − Cᵀλ.
Impose the constraint: Cv − CCᵀλ = 0 ⇒ λ = (CCᵀ)⁻¹Cv (invertible because
rank(C) = 3). Substitute:

$$
w \;=\; \big(I - C^{\mathsf T}(CC^{\mathsf T})^{-1}C\big)\,v \;\equiv\; P v .
$$

So **P is the orthogonal projector, and orthogonality is a choice**: it is the
projector that makes the *smallest Euclidean correction*. That is a real
modelling assumption, not a mathematical necessity — any oblique projector onto
null(C) would also conserve. The Euclidean metric treats a correction of 10⁻⁶
to Y_neut and to Y_si28 as equally costly, which is not obviously right when
their abundances differ by ten orders of magnitude. See **R-17**.

### Derivation 2 — QR, which is what ships

```python
Q, R = np.linalg.qr(C.T)      # reduced: Q is (m, 3) with orthonormal columns
P = np.eye(m) - Q @ Q.T
```

Q's columns are an orthonormal basis for rowspace(C) = colspace(Cᵀ). QQᵀ is the
orthogonal projector *onto* that space, so I − QQᵀ projects onto its orthogonal
complement, which is null(C). Equality with Derivation 1: write C = RᵀQᵀ. Then
CCᵀ = RᵀQᵀQR = RᵀR, and

$$
C^{\mathsf T}(CC^{\mathsf T})^{-1}C \;=\; QR(R^{\mathsf T}R)^{-1}R^{\mathsf T}Q^{\mathsf T}
\;=\; QRR^{-1}R^{-\mathsf T}R^{\mathsf T}Q^{\mathsf T} \;=\; QQ^{\mathsf T}. \qquad\checkmark
$$

**Why QR is the one that ships.** The normal-equations form requires inverting
CCᵀ, whose condition number is cond(C)². With cond(CCᵀ) ≈ 4×10⁴, cond(C) ≈ 200
— so the normal-equations route throws away ~2.3 decimal digits for nothing.
Here that is harmless (10⁻¹⁶ → 10⁻¹⁴, still far inside the 10⁻¹² gate), but the
QR form is free and additionally gives symmetry and idempotence to near machine
precision by construction rather than by luck. The docstring says exactly this,
and the measured result confirms it: ‖P² − P‖_∞ ≤ 1.0×10⁻¹⁵, P symmetric to
0.0 exactly, rank(P) = m − 3 exactly, max relative constraint residual over 20
decades of dY = 6.68×10⁻¹⁷ (mesa_80) / 1.04×10⁻¹⁶ (mesa_151) against a 10⁻¹²
gate. **[RESULTS]** 2026-07-08.

`build_projector` also guards rank explicitly:

```python
if np.abs(np.diag(R)).min() <= 1e-12 * np.abs(np.diag(R)).max():
    raise ValueError("C is rank-deficient — constraint rows are not independent")
```

which is a rank test on R's diagonal — valid because for a full-rank matrix QR
gives |R_ii| > 0, and the ratio to the largest is the natural scale-free
threshold.

---

## I.9 Why the projector acts on the extended vector — the laundering trap

P is (n+3) × (n+3), not n × n. If instead you built a nuclei-only constraint
matrix C_nuc = [A; Z] (2 × n) and projected dY_nuclei, you would be imposing

$$
\sum_i Z_i\,dY_i = 0 \quad\Longleftrightarrow\quad dY_e = 0 .
$$

**The projector would delete the weak signal.** Not degrade it — delete it,
exactly, by orthogonal projection. And it would do so while making every
conservation diagnostic look perfect. This is the sharpest instance in the repo
of "ask what would still be wrong if the test passed": a nuclei-only projector
passes baryon conservation, passes charge conservation, passes idempotence,
passes symmetry, and has destroyed the physics.

`test_projection_preserves_weak_dYe_signal` is the guard: build a weak-only
flux, compute dỸ = ν̃φ, record dYₑ = Z·dY_nuclei ≠ 0, project, and require the
value to be unchanged to 10⁻¹² relative. Measured change: ≤ 3.4×10⁻²¹.
**[RESULTS]** 2026-07-08.

Why is it unchanged? Because ν̃φ is *already* in null(C) (§I.7), and P is the
identity on null(C) — `test_on_manifold_input_is_unchanged` states this
directly. The extended projector's action on a genuinely conserving update is
the identity; only the *nuclei-only* projector would move it, and it would move
it in exactly the dYₑ direction.

**The other half of invariant #4: P is valid in a LINEAR output space only.**
Suppose the head emits u = asinh(dY/s) or a signed-log, and you project u. Then
C·P(u) = 0 says a linear constraint holds *in the warped coordinates*. Mapping
back, Σ Aᵢ · sinh(uᵢ)·s ≠ 0 in general — the constraint you imposed is not the
constraint you wanted. This is the documented NuGNN failure mode. The rule that
falls out is stated in `CLAUDE.md` invariant #4 and in `projector.py`'s
docstring: **conservation lives in the decode step; no nonlinear transform may
sit between the conservation map and the output.** asinh/signed-log are
legitimate *latent* representations (Tier 0 **R-18**) — they must simply not be
the space where the sum is evaluated.

---

## I.10 ⚠ Target A and Target B reach the same set

A result I had assumed was false until I measured the ranks, and which changes
how the Target A/B decision should be framed.

> **Theorem [derived here].** image(ν̃) = null(C).

*Proof.* (⊆) Cν̃ = 0, so every ν̃φ lies in null(C). (⊇) Dimension count:
dim null(C) = (n+3) − rank(C) = (n+3) − 3 = n. And rank(ν̃) = n — measured: 80
for mesa_80, 151 for mesa_151 (§I.2.1). A subspace contained in another of the
same finite dimension is equal to it. ∎

The measurement is what makes the second half non-trivial: rank(ν̃) *could*
have been less than n (a network too small to reach every conserving direction),
and for a sufficiently truncated network it would be. It is not, for either
network here.

**What this means.**

| | Target A | Target B |
|---|---|---|
| output | φ ∈ ℝ^r (607 / 1518) | dỸ ∈ ℝ^{n+3} (83 / 154) |
| conserving? | by construction (Cν̃ = 0) | by construction (P) |
| **reachable set** | **null(C)** | **null(C)** |
| parameterisation | redundant: 528- / 1368-dim fibre | minimal |
| error amplification into dY | cond(ν̃) ≈ 41 / 55 | 1 (P is an orthogonal projection) |
| per-output physical meaning | a named reaction's flux | a species' abundance change |
| maskable? | yes, per reaction | no natural analogue |
| needs Φ labels? | **yes** (§IV.3) | no — ΔX suffices |

So the choice is **not** about expressivity. Both can express exactly the
conserving updates and nothing else. The trade is:

- Target A buys physical structure — per-reaction attribution, the equilibrium
  mask, reaction-level loss weighting, direct comparability to the bridge sets —
  at the cost of a badly over-parameterised output (528 unconstrained
  directions), a conditioning factor of ~40–60 from φ to dY, and a label
  requirement the shipped dataset does not meet.
- Target B buys a minimal, well-conditioned parameterisation and works with the
  labels that exist, at the cost of throwing away every per-reaction handle.

Framed that way, `CLAUDE.md`'s switch condition — "Target A → Target B if
cond(S_active) > 10⁶, or if >~90% of reactions carry net flux below the Yₑ
floor" — reads correctly: it is triggered by the *conditioning* and the
*structure*, which is exactly what Target A is being bought for. When the
structure is not there, Target A's costs remain and its benefits do not.

---

## I.10b The effective dimension of the reachable set — and where Yₑ hides

§I.10 established *which increments* are reachable — the whole of null(C), by
either target. The complementary question is which **states** are actually
visited. Tier 0 §IV.2 introduced the reachable manifold qualitatively; nothing
anywhere puts a number on it, and the number matters in a way I did not
anticipate.

### The measurement

PCA over pre-stall rows of 80 randomly chosen shipped trajectories per network
(≤ 25 log-spaced rows each; `data/trajectories.select_rows(prestall=True)`).
**[derived here]**:

```python
X = np.vstack(...)                     # (rows, n_species) mass fractions
Xc = X - X.mean(0)
s = np.linalg.svd(Xc, compute_uv=False)
c = np.cumsum(s**2) / (s**2).sum()
```

| | mesa_80 (n = 80) | mesa_151 (n = 151) |
|---|---|---|
| rows / trajectories | 2079 / 80 | 2076 / 80 |
| PCs for 90% of Var(X) | **7** | **14** |
| PCs for 99% | 22 | 38 |
| PCs for 99.9% | 37 | 61 |
| participation ratio (Σλ)²/Σλ² | 3.42 | 8.58 |
| PCs for 90% of Var(X) in **log₁₀** space | 6 | 5 |

**The compositions actually visited occupy an effective manifold of dimension
≈ 3–14, not 80 or 151.** The participation ratio — a basis-free effective rank —
is 3.4 and 8.6.

This is worth internalising, because it reframes the difficulty of the learning
problem. It is very likely *why* a plain feed-forward network (the NNN baseline,
S16) works at all on a nominally 151-dimensional map: the target is not a
151-dimensional function, it is a ~10-dimensional one embedded in 151
coordinates. It also gives the size-transfer question (mesa_80 → mesa_151) a
sharper form: the effective dimension roughly *doubles* (3.4 → 8.6), which is a
more informative statement about "how much harder is the big network" than
80 → 151 is.

**Caveats, stated up front.** These are the *shipped* trajectories, which stall
at a bug-displaced attractor (Tier 3, S13) and are constant-(T, ρ); 80 files per
network; linear-X PCA is dominated by the few abundant species. The number is a
lower bound on the diversity a full corpus would show, and the measurement
should be repeated on the clean reruns and across the (T, ρ) box. The
*qualitative* conclusion — effective dimension ≪ n — is robust; the specific
integer is not.

### ⚠ The part that changes a design decision

The obvious next move is dangerous, so it is worth doing the second measurement
before anyone makes it: if the manifold is ~10-dimensional, why not compress —
a PCA basis, a latent bottleneck, a variance-weighted loss?

Because **Yₑ does not live in the leading directions.** Yₑ = Σ_i (Z_i/A_i)X_i is
a linear functional w·X, so the fraction of Var(Yₑ) captured by the top-k PCs of
X is computable exactly. **[derived here]**:

| | mesa_80 | mesa_151 |
|---|---|---|
| std(Yₑ) across the sample | 1.18×10⁻² | 1.61×10⁻² |
| PCs for 90% of **Var(X)** | 7 | 14 |
| PCs for 90% of **Var(Yₑ)** | **16** | 11 |
| PCs for 99% of Var(X) | 22 | 38 |
| PCs for 99% of **Var(Yₑ)** | **43** | **65** |
| cumulative Var(X) / Var(Yₑ) at k = 10 | 0.9491 / 0.8716 | 0.8565 / 0.8799 |
| … at k = 20 | 0.9875 / 0.9082 | 0.9521 / 0.9426 |
| … at k = 30 | **0.9966 / 0.9295** | **0.9811 / 0.9527** |

Read this carefully, because the effect is **in the tail, not in the leading
directions**. At small k the two are comparable — mesa_151 at k = 10 even
captures Yₑ slightly *better* than X. What differs is convergence: to reach 99%,
Yₑ needs **43 vs 22** components (mesa_80) and **65 vs 38** (mesa_151), i.e.
1.7–2× as many; and by k = 30, X has converged to 99.7% / 98.1% while Yₑ has
stalled at 93.0% / 95.3%. **The last few percent of the Yₑ signal is smeared
across many low-variance directions and cannot be recovered by truncation.**

### The arithmetic that settles it

That tail behaviour would be a mild caution if the Yₑ tolerance were loose. It
is not. The per-step budget is 3×10⁻⁶ (§0.3.4) against std(Yₑ) = 1.18×10⁻², so
the tolerable *relative* error is

$$
\frac{3\times10^{-6}}{1.18\times10^{-2}} \;=\; 2.5\times10^{-4},
$$

and a rank-k truncation's Yₑ error is √(1 − cumVar_Yₑ(k))·std(Yₑ). Meeting the
budget therefore requires

$$
\text{cumVar}_{Y_e}(k) \;\ge\; 1 - (2.5\times10^{-4})^2 \;=\; 1 - 6.5\times10^{-8}
\;=\; 99.999993\% . \qquad\text{[derived here]}
$$

**No truncation achieves that.** Not k = 30, not k = 60, not any k short of the
full rank — the measured curve is at 93% by k = 30. So this is not "variance
compression is risky for Yₑ"; it is **arithmetically excluded**: any
variance-truncated reduction of the composition — PCA basis, POD, a linear
autoencoder bottleneck sized by reconstruction error — destroys the Yₑ budget by
three to four orders of magnitude before the model has made a single error of
its own.

### And it is not an accident — it is §I.2.1

This is not an empirical quirk of these trajectories; it is forced by the
stoichiometry, and the proof is a result already in this file.

§I.2.1 measured that the left null space of ν restricted to strong/EM columns is
exactly **span{A, Z}**. So *every* increment produced by the strong sector
satisfies Z·dY = 0, i.e. **dYₑ = 0 exactly**. The strong sector is fast, carries
essentially all the composition change, and is therefore responsible for
essentially all the composition variance — and every bit of it is Yₑ-neutral.

> **Yₑ moves only through the weak sector, which is slow. The dominant variance
> directions are therefore Yₑ-blind by construction, and the Yₑ signal is pushed
> into the low-variance tail.** [derived here]

Consequences, all actionable:

1. **Never size a latent bottleneck by explained composition variance.** The
   requirement is 1 − 6.5×10⁻⁸ of Var(Yₑ); reconstruction error is simply the
   wrong instrument, by four orders of magnitude. If a bottleneck is used at
   all, Yₑ must be carried *outside* it — as an explicit conserved coordinate,
   not as something reconstructed.
2. **A plain MSE-on-X (or on ΔX) loss is variance-weighted**, hence subject to
   the same blindness. An explicit Yₑ term is not a nicety, it is structurally
   required. (`CLAUDE.md`'s loss-weighting discussion and the |dẎₑ|
   concentration measurements — top-5 weak channels carrying 0.96/0.75,
   **[RESULTS]** 2026-07-12 — are the right instinct; this is the quantitative
   argument for it.)
3. **Any PCA/POD/autoencoder-based reduction must be validated on Yₑ
   separately**, not on reconstruction error.
4. **It suggests a genuinely better decomposition**: split the update as
   dY = dY_strong + dY_weak with dY_strong ∈ null(Zᵀ) enforced structurally. The
   strong part then lives in a lower-dimensional, well-conditioned space, and
   the weak part — small, slow, and *the entire Yₑ signal* — is a separate head
   with its own loss and its own error budget. That is a Tier-4 architecture
   idea and, like §II.4b's, it needs a novelty check before anyone gets attached
   to it.

Open (register: **R-02**) — repeat on the clean reruns and across the (T, ρ) box
before the Tier-4 choices above are made.

---

## I.11 The bipartite graph, the radius, and K

`export.bipartite_digraph` builds a heterogeneous digraph: isotope nodes and
reaction nodes; I→R edges for reactants (coefficient = consumed count,
positive), R→I edges for products (signed net production). A catalyst-like
species gets both.

`metrics.graph_extents` reports three undirected views. **[RESULTS]**
2026-07-08, identical for both networks:

| view | radius | diameter | reading |
|---|---|---|---|
| bipartite (incidence only) | 3 | 6 | I→R→I = 2 hops, so this counts half-reactions |
| bipartite + I→I coupling edges | 2 | 4 | shortcut edges added |
| isotope projection (I→I only) | **1** | **2** | one reaction = one hop |

All connected, one component.

**Isotope-projection radius 1** is the hub structure of §I.1(c) restated: there
exists a species (⁴He) adjacent to *every* other species — it shares a reaction
with all of them. Diameter 2: any two species are at most two reactions apart.

**K = ⌈radius⌉ + 2 = 5** on the bipartite graph is the checklist's implied
processor depth (`GraphExtent.implied_K`). The reasoning that makes it coherent:
in the bipartite view one *reaction hop* costs two message-passing layers, so
K = 5 layers ≈ 2.5 reaction hops — which covers the isotope-projection
*diameter* of 2 reaction hops with one layer to spare. That is the honest
justification; note that the formula as written uses **radius**, which for a
graph-level readout from a central node would be the right base, but for a
node-level output (which this is — every species needs its own dY) the stricter
base is eccentricity, and the fact that K = 5 also clears the diameter is a
happy coincidence of this particular graph rather than something the formula
guarantees. Logged as an open item in **R-19**.

**The hazard the number hides.** A radius of 1 in the isotope projection means
the graph carries almost no long-range structure to learn: everything is two
hops from everything through three hub nodes. Depth beyond K ≈ 4–5 buys nothing
topologically, and — more importantly — an architecture that appears to "use
the graph" may in fact be routing all information through n/p/⁴He node
features. That is a Tier-4 experimental-design problem, but it is *this* number
that raises it.

---

## I.12 Code walkthrough

Reading order, ~600 lines total.

**`graph/isotopes.py`** — the isotope table: names, A, Z, pynucastro `Nucleus`
objects, and `index()`. The row order of ν is the YAML order, which is the
CSV-header order of the training data. This is the join key for everything.
(Tier 0 §II.7 covers it.)

**`graph/network.py`** — builds the pynucastro `RateCollection` with duplicate
resolution and the reconciliation disposition applied. Tier 1 §VI.4.

**`graph/stoich.py`** (211 lines) — the node. Read in this order:
1. The module docstring — it *is* the spec for the conservation layer.
2. `WEAK_LEDGERS` — the three-row table of §I.4.
3. `constraint_matrix` — §I.6.
4. `build_stoich`: the ν loop, then the **five fail-loud validations**
   (baryon leak; strong-column charge leak; weak |ΔZ| ≠ 1; ledger/ΔZ mismatch;
   unrecognised weak classification), then `C @ nu_ext` residual, then the
   frozen dataclass.
5. `Stoich` — note what it carries beyond ν: `weak_mask`, `weak_type`, `Q`,
   `is_tabular`, `derived_from_inverse`, `chapter`, `source_label`. Every one
   of those is a Tier-1 output becoming a Tier-2 column attribute (Tier 1's
   "threads that carry forward").

**`graph/projector.py`** (47 lines) — §I.8. Two functions; the docstring
carries the invariant.

**`graph/export.py`** — serialisation. Two details worth noticing:
`content_hash` hashes the *content* (sorted keys, dtypes, shapes, bytes) rather
than the file, because `.npz` embeds zip timestamps and would otherwise differ
between identical exports. This is Tier 0 §VII.5 (non-regenerable artifacts are
persisted) meeting reproducibility: the artifact *is* regenerable, so what gets
recorded in `RESULTS.md` is a content hash that proves the regeneration is
identical.

**`graph/metrics.py`** — the measurement layer: `reaction_census`,
`weak_inventory`, `graph_extents`, `condition_numbers`, `drift_metrics`.
Everything here exists to produce a `RESULTS.md` row. Note
`_SVD_RANK_RTOL = 1e-12` and the *rank-revealing* condition number (ratio of
extreme **nonzero** singular values): using the naive σ_max/σ_min would report
∞, because the structural left-null vector A guarantees a zero singular value.
The same definition is reused by `killtest.active_set.cond_s_active`, and that
consistency is deliberate — the kill-test's cond gate would be meaningless if
the two definitions differed.

**`scripts/export_stoich_matrix.py`**, **`scripts/check_conservation.py`**,
**`scripts/check_projector.py`** — the reproducible entry points behind the
`RESULTS.md` rows.

---

## I.13 The oracle: what the 30-test gate actually asserts

`tests/test_conservation.py` has two layers, and the *layering* is the design.

**Layer 1 — the synthetic toy network.** Ten species, eight columns, hand-built
in the test file: triple-α, an α-capture chain, an (α,γ), a (p,γ) bottleneck, a
photodisintegration, and **one of each weak type**. No pynucastro. No I/O.

Its purpose is to isolate *the convention* from *the export*. If Layer 1 fails,
the bookkeeping convention itself is wrong — the ledger table, the sign of ν̄ in
the lepton row, the β⁺ treatment. If Layer 1 passes and Layer 2 fails, the
convention is fine and the pynucastro export is wrong. Two failure modes,
cleanly separated by construction. This is worth stealing as a habit.

Layer 1 also encodes the physics-direction assertions that the production
matrices cannot conveniently state:

```python
@pytest.mark.parametrize(("col", "expected_sign"),
    [(5, -1.0), (6, +1.0), (7, -1.0)],
    ids=["EC_lowers_Ye", "beta_minus_raises_Ye", "beta_plus_lowers_Ye"])
```

— i.e. §I.5's conclusion, as a test with human-readable ids.

**Layer 2 — the production matrices.** Auto-generated by the session fixture in
`conftest.py` if absent (~7 s/net), so this layer **never skips**. That is a
deliberate anti-pattern-avoidance: a gate that silently skips when its data is
missing is not a gate. Assertions:

| test | asserts | tolerance |
|---|---|---|
| `test_exported_shapes_and_species` | n = 80/151, C is 3 × (n+3), ν̃ is (n+3) × r | exact |
| `test_exported_columns_conserve_exactly` | per column: ΣAν = 0; strong ΣZν = 0; weak \|ΔZ\| = 1 and ΔZ = d_e | **`== 0.0`** (§I.2.2) |
| `test_exported_lepton_ledgers_close` | ΔL = 0 on weak; ledgers zero on strong; max\|C ν̃\| = 0 | `== 0.0` |
| `test_exported_weak_mask_matches_weak_type` | `weak_mask ⟺ weak_type != ""`; types ⊆ the three known | exact |
| `test_exported_random_flux_drift` | **the blocking gate**: 10 seeds × 6 scales (1e0…1e-20) × 2 networks; baryon drift and charge-to-lepton closure within max(1e-12·s, 1e-13·G); dYₑ through weak columns ≠ 0 | scaled |
| `test_exported_mask_contract_on_real_matrix` | random gate on the eligible set (= ~weak, *structurally*) leaves conservation intact and weak columns unscaled | scaled |

The magnitude sweep is the part I would have under-specified if writing it
myself. One scale is not a test: at φ ~ 1 an absolute 10⁻¹² bound is
meaningful; at φ ~ 10⁻²⁰ it is vacuous, and a broken implementation would pass.
Six scales spanning 20 decades with a tolerance that *changes character* across
them (absolute at the top, relative-to-gross at the bottom) is what makes the
gate informative everywhere.

`tests/test_projector.py` mirrors the structure for Target B: shape, symmetry
(≤ 10⁻¹⁴), idempotence (≤ 10⁻¹³), rank = m − 3 via eigenvalue sum, constraint
residuals across the same 20 decades with a *relative* bound (P is linear hence
exactly scale-equivariant, so the meaningful statement is relative),
fixed-point on the manifold, weak-dYₑ preservation, and the rank-deficiency
guard.

**④ SEE:** notebook `03-graph-conservation.ipynb` — Figure 1 the ν sparsity
structure, Figure 2 drift vs φ magnitude (the tolerance's two regimes visible
as a kink), Figure 3 the projector residual across 20 decades, Figure 4 the
graph extents and K.

---

## I.14 Self-check for S7

1. State the theorem relating conserved quantities to ν, with the quantifier.
2. left-nullity(ν) = 1, left-nullity(ν restricted to strong columns) = 2,
   left-nullity(ν̃) = 3. Say what each of the three numbers rules out.
3. Why can `test_exported_columns_conserve_exactly` assert `== 0.0` while
   `test_exported_random_flux_drift` cannot?
4. Why is the lepton ledger assigned from `weak_type` rather than from Z·ν?
   What would the closure test detect if it were back-derived?
5. Derive P = I − Cᵀ(CCᵀ)⁻¹C from a constrained least-squares problem, then
   show the QR form is equal to it.
6. What exactly goes wrong if P is built from a nuclei-only C? Which test
   catches it?
7. Prove image(ν̃) = null(C), and say which half of the proof required a
   measurement.
8. The right-nullity of ν is 528. Give two distinct consequences for the
   emulator's design.
9. Why is `cond_s_active` defined with the ratio of extreme *nonzero* singular
   values rather than σ_max/σ_min?

---

# Part II (S8) — Fluxes, pairs, and cancellation

S7 gave the map φ ↦ dY. S8 gives the φ: how a gross rate becomes a net flux,
what the pairing structure is, and why the single scalar κ shows up in three
different roles — detailed-balance diagnostic, condition number, and
thermodynamic affinity — that turn out to be the same thing.

---

## II.1 From λ to R to f⁺/f⁻

Tier 1 §II.4 ended at the gross rate. Restated in the engine's variables
(`fluxes/engine.py`):

$$
R_j \;=\; \underbrace{\frac{1}{\prod_s c_s!}}_{\texttt{prefactor}} \cdot
\rho^{\,\texttt{dens\_exp}_j} \cdot \prod_{r \in \text{reactants}(j)} Y_r \cdot \lambda_j ,
$$

with `dens_exp = n_reactants − 1` (plus one more ρ for REACLIB EC fits that
carry ρYₑ, flagged `ye_weighted`), the prefactor removing double-counting of
identical reactants, and λ_j the screened, pf-corrected rate of Tier 1.

Units: R is mol g⁻¹ s⁻¹, matching Ẏ. In code the whole thing is three array
operations —

```python
R = lam * cn.prefactor[:, None] * rho[None, :] ** cn.dens_exp[:, None]
Ypad = np.vstack([Y, np.ones((1, n_states))])          # sentinel row for absent slots
for k in range(cn.reactant_idx.shape[1]):
    R *= Ypad[cn.reactant_idx[:, k]]
```

— and the sentinel-row trick (index `n_species` means "no reactant in this
slot", multiply by 1) is what makes the loop uniform over chapters with
different reactant counts. Max slots is 4 in these networks (§I.1(c) reported
max 5 *participants*, reactants + products).

Then the pair semantics, which are the actual content of this node:

$$
f^+_j = R_j, \qquad
f^-_j = \begin{cases} R_{\text{pair}(j)} & \text{paired}\\ 0 & \text{unpaired (always, for weak)}\end{cases},
\qquad \varphi_j = f^+_j - f^-_j,
\qquad \kappa_j = \frac{|\varphi_j|}{f^+_j + f^-_j}.
$$

**Every column has its own f⁺, f⁻, φ, κ.** Both members of a forward/reverse
pair are columns of ν, so the pair (j, k) has φ_j = −φ_k and κ_j = κ_k. The
information is duplicated; §II.3 shows how to sum without double counting.

---

## II.2 The pair map

`fluxes/compile.py::_pair_maps` builds two arrays:

- `pair_col[j]` — the column index of j's reverse, or −1 if unpaired;
- `is_forward_member[j]` — whether j is the designated representative of its
  pair (or an unpaired strong column, which counts as its own representative).

The matching is by *canonical directed key* (Tier 1 **R-17**): `directed_key(j)`
encodes the reactant and product multisets in a canonical order, and
`reverse_key` swaps them. Two columns pair iff one's key is the other's
reversed key. This is exactly the decidability machinery Tier 1 built for the
MESA reconciliation, reused — which is the point of having built it as a
general canonicaliser rather than a one-off.

Two rules deserve attention.

**Weak columns are always unpaired**, by an explicit `continue` before the key
lookup:

```python
for j in range(r):
    if stoich.weak_mask[j]:
        continue                      # never enters col_by_key
```

Not "no partner was found" — *structurally excluded from the search*. β-decay
and electron capture are not detailed-balance partners of each other in this
regime (Tier 1 §V.1): the inverse of an electron capture is a neutrino capture,
which does not occur at these densities because the neutrinos free-stream out
(Tier 0 §0.4.2). Pairing an EC with the corresponding β⁻ would be physically
wrong and would manufacture a spurious equilibrium. `CLAUDE.md` invariant #2
lives here in its most upstream form.

**Forward-member selection is deterministic and provenance-aware.** If exactly
one member of a pair was a REACLIB v-flag reverse, the *other* one is the
forward:

```python
if dj != dk:
    is_fwd[j] = dk                      # forward = the one that was NOT the v-flag
else:
    is_fwd[j] = stoich.rate_fnames[j] < stoich.rate_fnames[k]   # lexicographic tiebreak
```

The tiebreak matters only for reproducibility (the same pair must always elect
the same representative across runs and across networks); the v-flag rule
matters physically, because after the Tier-1 replacement the non-v-flag member
carries the *fitted* rate and its partner is a `DerivedRate` computed from it.
Electing the derived one as "forward" would not be wrong, but it would make the
provenance labelling in downstream reports incoherent. `crosscheck.kappa.strong_pairs`
uses the identical rule — again, consistency by shared definition rather than
by two implementations agreeing.

---

## II.3 The net identity, proved

The physical right-hand side is ẏ = νR, summing over **all** r columns
including both members of each pair. The kill-test and every concentration
statistic instead want to sum over *net* columns only. These agree:

> **Claim.** $\displaystyle \sum_{j=1}^{r}\nu_{ij}R_j \;=\;
> \sum_{j\,\in\,\mathcal{F}\cup\mathcal{U}}\nu_{ij}\varphi_j$
> where 𝓕 = forward members, 𝓤 = unpaired columns.

*Proof.* Partition the columns into paired couples {j, k = pair(j)} and
unpaired singletons.

For a couple: the reverse reaction has exactly the reactants and products of
the forward swapped, so its stoichiometric column is the negative,
**ν_{·k} = −ν_{·j}** — this is not an assumption, it is what `reverse_key`
matching *means*, and it is asserted by
`test_pair_map_is_involution_on_strong_pairs`. Hence

$$
\nu_{ij}R_j + \nu_{ik}R_k \;=\; \nu_{ij}R_j - \nu_{ij}R_k \;=\; \nu_{ij}(R_j - R_k) \;=\; \nu_{ij}\varphi_j,
$$

and only the forward member appears. For a singleton, f⁻ = 0 so φ_j = R_j and
the term is unchanged. Summing over all couples and singletons gives the
claim. ∎

`test_net_identity` checks it numerically on physical states; `test_pair_antisymmetry`
checks φ_{pair(j)} = −φ_j, which is the couple half of the proof.

**Why this identity is load-bearing.** Every "fraction of turnover carried by
the active set" statistic (`killtest.active_set.carried_fractions`) sums
|ν_ij φ_j| over columns. If you summed over all r columns you would count every
equilibrated pair *twice* with the same tiny φ, inflating the denominator and
deflating every coverage fraction. The docstring says so explicitly: "`phi`/`nu`
should be restricted to net columns (forward|unpaired) by the caller to avoid
double counting pairs." The identity is what licenses the restriction.

---

## II.4 κ, three ways

κ_j = |φ_j| / (f⁺_j + f⁻_j) ∈ [0, 1]. Three readings, all exact, all useful.

### (a) κ as a detailed-balance diagnostic

At exact detailed balance f⁺ = f⁻ ⇒ κ = 0. Tier 1 §III.6 uses this as the
numerical test of the reverse-rate construction, and it is how the pf-free
v-flag pathology was found: raw v-flag reverses gave κ medians of 6.6×10⁻² /
1.3×10⁻¹ at NSE and p90 ≈ 0.4–0.5, versus 2.6×10⁻¹² with `DerivedRate(use_pf=True)`.
**[RESULTS]** 2026-07-10.

The sensitivity is the useful part. Suppose f⁻ carries a multiplicative error
(1 + ε) at a state where the true fluxes balance. Then φ = f⁺ − (1+ε)f⁺ = −εf⁺,
denominator (2+ε)f⁺, so

$$
\kappa \;=\; \frac{\varepsilon}{2+\varepsilon} \;\approx\; \frac{\varepsilon}{2}.
$$

**κ measures a relative rate error at 1:2 gearing.** A 20% error in a reverse
rate shows up as κ ≈ 0.1 — right at the active-set threshold. This one line
unifies the v-flag floor (Tier 1 §III.5), the screening offset (§IV.7), and the
next reading.

### (b) κ as a condition number

Suppose f⁺ and f⁻ each carry relative error ε (from the rate library, from
screening, from a neural network). Worst case the errors are coherent:

$$
|\delta\varphi| \;\le\; \varepsilon\,(f^+ + f^-) \;=\; \frac{\varepsilon}{\kappa}\,|\varphi|
\qquad\Longrightarrow\qquad
\boxed{\ \frac{|\delta\varphi|}{|\varphi|} \;\le\; \frac{\varepsilon}{\kappa}\ }
$$

**1/κ is the error amplification factor** from gross-flux accuracy to net-flux
accuracy. This is Tier 0 §V.1's catastrophic cancellation, in the variables of
this tier. At κ = 10⁻³ a rate known to 1% gives a net flux known to a factor of
10 — i.e. not known at all.

Two consequences that shape the whole project:

1. **The active-set threshold κ > 0.1 is an error-budget threshold, not a
   physics threshold.** It says: only trust columns where amplification is
   ≤ 10×. `CLAUDE.md`'s kill-test asks whether such columns carry ≥ 95% of the
   physics.
2. **Any accuracy statement about net quantities must be normalised by the
   gross**, or it is meaningless in the cancellation-dominated regime. This is
   why `test_flux_engine.py`'s ydot oracle uses a *gross-relative* gate ("within
   1e-12 × per-species gross flux Σ_j|ν_ij|R_j"), and why the handshake grew a
   `resid_gross` field (§II.8).

### (c) κ as a thermodynamic affinity — the bridge to S9

Write the log flux ratio h = ln(f⁺/f⁻). Then

$$
\kappa \;=\; \left|\frac{f^+-f^-}{f^++f^-}\right| \;=\; \left|\tanh\!\left(\tfrac{h}{2}\right)\right| .
$$

And h is not an arbitrary quantity: for a reaction at chemical potentials μ_i,
the ratio of forward to reverse rate is set by detailed balance as

$$
h \;=\; \ln\frac{f^+}{f^-} \;=\; \frac{\mathcal{A}}{kT},\qquad
\mathcal{A} \;=\; \sum_i (-\nu_{ij})\,\mu_i \ \ \text{(the reaction affinity)} .
$$

So

$$
\boxed{\ \kappa_j \;=\; \left|\tanh\!\left(\frac{\mathcal{A}_j}{2kT}\right)\right|\ }
$$

**κ is a monotone reparameterisation of the reaction's distance from chemical
equilibrium, measured in units of kT.** [derived here] Near equilibrium
(𝒜 ≪ kT) it reduces to κ ≈ 𝒜/(2kT) and φ ≈ (f⁺+f⁻)𝒜/(2kT) — the standard
near-equilibrium linear-response law, flux proportional to affinity. Far from
equilibrium (𝒜 ≫ kT) it saturates at 1.

This is the honest reason κ and the Guidry departure δ are *correlated but not
equal*: both measure distance from equilibrium, κ in reaction-affinity space
and δ in abundance space, related by a nonlinear (tanh) and
composition-weighted map. **[RESULTS]** 2026-07-12 measures the correlation:
Spearman(log κ, log δ_r) = +0.491 / +0.498 on the relaxed manifold. "Agree on
ordering, not on threshold crossings" is exactly what a monotone-but-nonlinear
relationship with different normalisations predicts.

It also explains the screened-κ offset (Tier 1 §IV.7) in one line: if screening
multiplies f⁺ by e^{Δh} and not f⁻, it shifts the affinity by Δh, so
κ = |tanh(Δh/2)| — the measured form, exact to 1.4×10⁻¹¹.

### (d) …and therefore κ as entropy production

Once κ is an affinity, the second law is one more line. The entropy production
of column j is σ_j = φ_j𝒜_j/T, and substituting f⁺ = s(1+κ)/2, f⁻ = s(1−κ)/2
with s = f⁺ + f⁻:

$$
\sigma_j \;=\; 2k_B\,s_j\,\kappa_j\operatorname{artanh}(\kappa_j)
\;\xrightarrow[\ \kappa\to0\ ]{}\; 2k_B\,s_j\,\kappa_j^2 \;\ge\; 0 .
\qquad\text{[derived here]}
$$

**Entropy production is quadratic in κ, and linear in the gross flux.** Two
things follow that the project does not currently use, both worked in
**§II.4b**:

- a near-balanced pair does no thermodynamic work no matter how enormous its
  gross rate — which is the *thermodynamic* form of the cancellation problem;
- ranking columns by σ_j rather than thresholding on κ gives a **flux-weighted,
  dimensionally meaningful, parameter-free** active set, and hence the
  derivation that the κ > 0.1 gate currently lacks (**R-01**).

**Domain of validity, stated before the identity gets used.** Everything above
assumes the column *has* a reverse — f⁻ is a real rate and h = ln(f⁺/f⁻) is a
real affinity. That is true of the strong/EM pairs and false of the weak sector,
where f⁻ ≡ 0 by construction (§II.2, §II.5), hence κ ≡ 1 and
artanh(κ) = ∞. **σ_j = 2k_B s_j κ_j artanh κ_j is therefore defined on strong/EM
paired columns only**, and §II.4b's constructions inherit that restriction.
The divergence is a bookkeeping artefact, not physics: a real EC has finite
entropy production, but computing it requires the neutrino's phase space and
the electron chemical potential, none of which this identity carries.

---

## II.4b Entropy production — a derived active set, a second-law constraint, and a Lyapunov bound

§II.4(d) derived σ_j = 2k_B s_j κ_j artanh(κ_j) and flagged two consequences
without working them. Both are worked here, because between them they supply the
two things the project most conspicuously lacks: **a principled basis for the
active-set threshold**, and **a hard physical constraint on a learned flux that
costs nothing to enforce**.

### This derives the active set

**R-01** complained that κ > 0.1 has no derivation — it is an assumed threshold on
a dimensionless ratio, with no floor beneath it and no retirement plan. The
entropy identity supplies a threshold-free replacement:

> **Define the active set as the smallest set of columns carrying ≥ 95% of the
> total entropy production Σ_j σ_j — over the strong/EM paired columns, with the
> weak sector admitted unconditionally.**

**That second clause is not a detail, and getting it wrong would invalidate the
whole proposal.** σ_j diverges on every weak column (κ ≡ 1 ⇒ artanh κ = ∞), so a
naive "rank all columns by σ_j" has no defined ordering on the 46 / 173 columns
that carry *all* of dYₑ — the quantity every gate in `CLAUDE.md` is written
around. The fix is the one the rest of the repo already uses: weak columns are
handled **structurally, not by threshold**. They are in the active set by
construction, exactly as κ ≡ 1 already puts them there today (§II.5), and the
entropy ranking replaces the κ > 0.1 threshold only where that threshold was
doing real work — on the strong/EM pairs. So the honest claim is narrower than
"a parameter-free replacement for the active-set gate": it is a parameter-free
replacement for the *strong-sector half* of it, which is nonetheless the half
that the split verdict of **[RESULTS]** 2026-07-12 turns on (§II.9's
worst-dominant-isotope row is a strong-sector statement).

Properties this has and κ > 0.1 does not, on that domain:

- **It is dimensionally and physically meaningful.** σ has units; the ranking is
  over a conserved, additive, non-negative physical quantity, not over a ratio.
- **It automatically weights by flux magnitude.** κ > 0.1 admits a column with
  κ = 0.9 carrying 10⁻³⁰ of the flow and excludes one with κ = 0.05 carrying
  half of it. σ_j = 2k_B s_j κ_j artanh κ_j cannot make that mistake, because
  s_j is in the formula.
- **It has no free parameter beyond the 95%**, which is already the form of the
  kill-test's other clauses.
- **It is cheap**: s_j and κ_j are already materialised by
  `FluxStore.read_chunk` (§II.6). This is a dozen lines in
  `killtest/active_set.py`.
- And it is *monotone in κ at fixed s*, so it does not overturn the existing
  picture — it re-weights it. Given §II.9's finding that the low-κ columns are
  0.9%–24% of active net columns but that *some dominant isotopes ride on them*,
  the entropy ranking is exactly the instrument that would separate "near-
  balanced and irrelevant" from "near-balanced and load-bearing".

I would run this before treating the split verdict of **[RESULTS]** 2026-07-12
as final. Open (register: **R-01**).

### The second-law constraint on a learned flux

For φ computed from a rate library, φ_j and 𝒜_j share a sign automatically —
they are built from the same f⁺, f⁻. **For a learned φ̂ there is no such
guarantee.** A flux head can emit a net flux pointing *up* the affinity
gradient: thermodynamically forbidden, and entirely invisible to every gate in
`CLAUDE.md`, because such a φ̂ conserves baryon number, charge and lepton number
perfectly (§I.7 — conservation holds for *any* φ, including unphysical ones).

**Same domain restriction as above, and here it costs more.** 𝒜_j is a
detailed-balance quantity, so all three responses below apply to strong/EM
paired columns only. For a weak column the nuclear sum Σ_i(−ν_{ij})μ_i is *not*
the affinity — it omits the electron chemical potential, and with the neutrinos
free-streaming out of the zone (Tier 0 §0.4.2) there is no μ_ν and no
detailed-balance relation at all, which is precisely why §II.2 refuses to pair
weak columns in the first place. So the weak sector — 46 / 173 columns, all of
dYₑ — gets **no** second-law guard from any of this. That is the uncomfortable
part: the blind spot is smallest exactly where the physics is least interesting,
and total where it matters most. Closing it would need an electron-capture
affinity built from μ_e and the (escaping) neutrino phase space, which is a
different and much larger piece of work; the honest position is to scope the
guard to the strong sector and say so.

With that scope, three levels of response, in increasing ambition:

1. **As a diagnostic (free).** Report the fraction of columns where
   sign(φ̂_j) ≠ sign(𝒜_j), and the total negative entropy production
   Σ_j min(0, φ̂_j 𝒜_j). A trained model that violates the second law on 5% of
   columns is telling you something no MSE curve will.
2. **As a soft penalty.** Penalise Σ_j max(0, −φ̂_j𝒜_j) — one-sided, so it costs
   nothing where the physics is respected.
3. **As a hard constraint — the interesting option.** Have the flux head predict
   only the **magnitude** and take the **sign from thermodynamics**:

   $$
   \hat\varphi_j \;=\; \operatorname{sign}(\mathcal{A}_j)\cdot \exp(\hat u_j).
   $$

   The affinity 𝒜_j = Σ_i(−ν_{ij})μ_i is computable from (T, ρ, Y) with the
   Saha coefficients of §III.3 — one exponential per species, no rate evaluation
   at all. The second law then holds by construction, exactly like conservation
   does, and the head's output space collapses from "signed quantity spanning 15
   decades with a sign flip at the equilibrium crossing" to "positive magnitude
   in log space" — which removes the single nastiest feature of Target A's
   target (Tier 0 **R-18**'s dynamic-range problem *is* the sign flip).

   Caveats to state honestly: the sign is *discontinuous* at 𝒜 = 0, which is
   precisely where the near-balanced columns live, so this trades a
   representation problem for a classification problem at the crossing — and
   near-equilibrium columns are where the crossing happens. Whether that is a
   net win is an experiment, not an argument. It also requires μ_i for the
   *actual* composition, not the equilibrium one, which is exactly what
   `qse/coeffs.py` computes.

   **This is a design idea, and I have not novelty-checked it.** Enforcing
   thermodynamic sign consistency in a learned chemical-kinetics surrogate is
   the kind of thing that plausibly exists in the combustion or atmospheric
   surrogate literature. It should go to the `novelty-checker` before anyone
   gets attached to it.

Open (register: **R-05**) — (1) is a free diagnostic on any trained model; (3)
is an architecture experiment for Tier 4.

### The Lyapunov corollary — rollout stability, structurally

---

This is why the constraint above is worth *enforcing* rather than merely
diagnosing.

Constant (T, ρ) is constant T and **volume**, so the potential that decreases is
the **Helmholtz** free energy F = U − TS, not the Gibbs free energy — G is the
constant-(T, P) potential and is the wrong object here. (It is an easy slip
because the chemical-kinetics literature usually works at constant pressure. The
identity below is unaffected; only the name is.) For the strong/EM sector,

$$
\frac{dF}{dt} \;=\; -T\sum_j \sigma_j \;=\; -\sum_j \varphi_j\mathcal{A}_j \;\le\; 0,
$$

with equality only at equilibrium. This is the second law, and it says the
strong/EM dynamics at fixed Yₑ is **contracting toward NSE in F**. Every
trajectory is confined to a sublevel set of F forever.

**A learned dynamics has no such guarantee, and could be given one.** If the
emulator's update satisfies Σ_j Φ̂_j𝒜_j ≥ 0 (§II.4b's constraint, integrated
over the step), then F̂ is non-increasing and **rollout cannot diverge** — the
iterate is trapped in the initial sublevel set of F, which is compact within the
composition polytope. That is a *structural* stability guarantee, of the same
character as conservation-by-construction, and obtained the same way: by
enforcing a physical law in the decode step rather than hoping training
delivers it.

This is directly the missing Tier-4 **S20** node (rollout stability: pushforward
vs noise injection in a stiff system, and "the governor"). The standard ML
answers there — noise injection, pushforward training, teacher forcing
schedules — are all *statistical* stabilisers with no guarantee. A
thermodynamic Lyapunov constraint is a *hard* one. Whether it is achievable
cheaply is open; that it is the right thing to want is not.

Three caveats worth keeping, the third of which is the one that bites.

1. F is a Lyapunov function at *constant* (T, ρ), which is the regime the labels
   are generated in but not the regime of deployment (§0.5b, point 2).
2. The QSE manifold is not the F-minimum, it is a slow descent along it
   (§III.9), so monotone F decrease does not by itself pin the *rate* of
   descent — which is exactly the quantity the emulator has to get right.
3. **The zone is not a closed system, and the weak sector is where it leaks.**
   Neutrinos free-stream out (Tier 0 §0.4.2), carrying energy and lepton number
   with them, so the descent argument is a statement about the strong/EM sector
   *at fixed Yₑ*, not about the full dynamics. The full system has no
   closed-system equilibrium at these conditions — it keeps deleptonising — and
   NSE is only the attractor of the strong sector on the Yₑ slice it currently
   occupies. Two things follow. The guarantee is still real (a bound on the fast,
   large-amplitude sector is exactly where rollout blows up), but it is **not** a
   bound on Yₑ drift, which is the failure mode the project actually fears; and
   the enforceable constraint Σ_j Φ̂_j𝒜_j ≥ 0 runs over strong/EM columns only,
   for the reasons given two subsections up. R-13 should be scoped that way.

Open (register: **R-13**), logged against S20.

---

## II.5 Weak columns: κ ≡ 1, structurally

Chained consequence of §II.2's `continue`:

- `compile.py` — weak columns never enter `col_by_key`, so `pair_col = -1`;
- `engine.py` — `f_minus` therefore stays 0 for unpaired columns, so

$$
\kappa_j \;=\; \frac{|\varphi_j|}{f^+_j + 0} \;=\; 1 .
$$

So every weak column with flux has κ = 1 exactly, and is therefore *always* in
the active set {κ > 0.1}. Verified at scale: κ = 1.0 exactly on all
8,825,170 / 33,189,419 (weak column × relaxed row) samples with f⁺ > 0, both
networks. **[RESULTS]** 2026-07-12.

This is why the |dẎₑ| coverage by the active set is **1.0000 structurally**
rather than empirically — a fact worth appreciating, because it means the
kill-test's Yₑ clause cannot fail for a reason having to do with masking. It
can only fail for reasons having to do with the *strong* sector's coverage of
the isotopes.

Fluxless weak columns get κ = 0 by the engine's zero-denominator convention
(`np.where(denom > 0, ..., 0.0)`) and contribute nothing. Worth knowing when
reading a κ histogram: the spike at 0 is not "equilibrated", it is "no flux".
`test_kappa_definition` and `test_weak_columns_have_zero_reverse_and_kappa_one`
pin both branches.

---

## II.6 The store: why f⁻, φ, κ are not stored

`fluxes/store.py` persists per chunk: `state_id`, `T`, `rho`, `ye`, `f_plus`
(n × n_rxn), `ydot`, `dye_weak`, and the three pair-map arrays. It does **not**
persist f⁻, φ or κ. On read:

```python
f_minus = np.zeros_like(f_plus)
f_minus[paired] = f_plus[pair_col[paired]]
phi   = f_plus - f_minus
kappa = np.where(denom > 0.0, np.abs(phi)/np.where(denom > 0.0, denom, 1.0), 0.0)
```

`f_minus = f_plus[pair_col]` is an **exact gather** — a permutation of stored
values, no arithmetic, no loss. So the reconstruction is bit-identical to what
the engine computed, and storing four arrays instead of one would double the
disk for zero information. At corpus scale that is the difference between 4.9 GB
and ~10 GB (mesa_80) or 12 GB and ~24 GB (mesa_151). **[RESULTS]** 2026-07-10.

Two operational details worth copying:

- **`complete=True` is written last**, after `f.flush()`. A crashed writer
  leaves the attribute absent, `completed_starts()` skips the file, and the run
  resumes. One-writer-per-file means no SWMR and no lock.
- **`state_id` is run-defined and joined on only.** For grid runs it is the
  training-grid row index; for trajectory runs, the row index within the
  trajectory. Never join on (logT, logRho) — Tier 0 §III.5, the Sobol grid's
  non-regenerability makes state identity the only stable key.

---

## II.7 The dt = 1e-6 label handshake

`fluxes/handshake.py` ties *our* fluxes to *their* labels with no model in
between. It is the flux-side analogue of the Step-2 model handshake, and its
value is that it can only be passed by getting the physics right — there is
nothing to tune.

**The premise.** At the shortest measured label timestep dt₁ ≈ 1.011×10⁻⁶ s,
*if* the state is not stiff on dt₁, then the label step is linear:

$$
\Delta X_i \;\approx\; A_i\,(\nu R)_i\,dt_1 .
$$

**The stiffness proxy.** Per (state, isotope), the destruction timescale

$$
\tau_i \;=\; \frac{Y_i}{|\dot Y_i|}
$$

decides whether the premise applies. The contract (from the Step-5 brief) is
sharp and worth internalising:

> Agreement is judged on cells with τ > 10·dt, **and the departure must track
> τ/dt** — that tracking is itself evidence the fluxes are right. Cells failing
> *without* a stiffness explanation indicate a configuration mismatch and are
> attributed to their dominant reaction channel.

That second clause is the interesting one. A test that only reports "90% of
cells agree" is weak; a test that predicts *which* cells will disagree and by
how much, and then confirms the prediction, is strong. Measured: agreement
rises monotonically with the τ/dt decade — 0.000 → 0.005/0.006 → 0.23/0.36 →
0.63/0.71 → 0.75/0.79 → 0.87/0.89. **[RESULTS]** 2026-07-10.

**The trapezoid refinement.** With `ydot_end` supplied, the prediction becomes
½(ẏ₀ + ẏ₁)·dt rather than ẏ₀·dt. The Euler form has local error ½ÿ·dt²; the
trapezoid form has −(1/12)y⃛·dt³. Measured effect: 10× on the trajectory
residual median. Additionally, cells whose RHS changed by more than
`RHS_STABLE_FACTOR = 0.2` over the interval are excluded from `linearizable` —
these are the *cascade-production* class, a species whose reactants only appear
mid-interval, so ẏ goes 0 → nonzero and no two-point quadrature can be
expected to work.

**The four-part tolerance.**

$$
|\Delta X_{\mathrm{pred}} - \Delta X_{\mathrm{lab}}| \;\le\;
\max\Big(\underbrace{0.1\,|\Delta X_{\mathrm{lab}}|}_{\text{linearisation}},\;
\underbrace{3\,\varepsilon_{\mathrm{lab}}(X_i + X_f)}_{\text{label noise}},\;
\underbrace{2\times10^{-15}}_{\text{floor}}\Big)
$$

- **REL_TOL = 0.1** is not a fudge: it is the linearisation error *at the
  admission boundary*. If a cell is admitted at τ = 10·dt, the O(dt/τ) error is
  10%. The tolerance is derived from the admission criterion.
- **ε_lab is measured, not assumed.** `calibrate_label_noise` takes
  10 × median of |resid|/(X_i + X_f) over *ultra-slow* cells (τ > 10³·dt,
  uncensored, X > 10⁻¹⁰) — cells where ΔX_pred ≈ 0, so the residual *is* the
  label's own noise. The labels are printed as float64 but carry the bbq
  solver's tolerance; measuring beats assuming float32.
- **Median, not p99, for the calibration**, with a documented reason: the
  calibration set must be robust to a genuinely corrupted channel. A tail
  statistic would let bad cells inflate the noise floor and thereby *mask
  themselves*. `test_handshake_synthetic.py::test_corrupted_channel_surfaces`
  is the regression. The ×10 covers the median→tail ratio of a heavy-tailed
  floor (Gaussian p99/median ≈ 3.8) with margin.
- **Censoring.** Cells at the 10⁻¹⁵ label clamp on either end are excluded: a
  clamped value carries no information, and its "residual" is an artefact of
  the clamp.

That is four different failure modes each getting its own term, with each term
traceable to a measurement or a derivation. It is the best-engineered tolerance
in the repo and a good template.

---

## II.7b The conditioning variable this suggests — Δt/τ, not log Δt

§II.7's admission criterion is τ_i/Δt, and that quantity is the answer to a
Tier-4 question nobody has framed as a question. The sketch lists **S19: time
conditioning (one model over 8 decades of Δt)**, and the natural implementation
is to feed log Δt as a scalar feature. Standard dimensional analysis says that is
the wrong variable.

### The argument

The state's response over an interval depends on Δt only through the
**dimensionless** products Δt·λ_j — equivalently, per species, through

$$
\frac{\Delta t}{\tau_i}, \qquad \tau_i = \frac{Y_i}{|\dot Y_i|},
$$

which is exactly the quantity `handshake.py` already computes and uses as its
admission criterion (§II.7). A model conditioned on raw log Δt must *learn* the
map (log Δt, T, ρ, Y) ↦ Δt/τ internally — and τ varies over 15+ decades with
(T, ρ) (§IV.1). It is being asked to learn a multiplication it could be handed.

Feeding Δt/τ_i as a **node feature** instead (or alongside) has three
properties worth having:

- it is already dimensionless, so the 8 decades of Δt and the 15 decades of rate
  scale collapse onto the single axis that governs the physics;
- it is *per species*, so it tells each node how relaxed it is over this step —
  which is precisely the information a GNN node needs and cannot easily compute
  from a global scalar;
- it is nearly free at inference: τ_i needs Ẏ_i, which is one evaluation of the
  rates the emulator is replacing — **which is the catch**.

### The catch, stated properly

If computing τ_i requires evaluating the network's rates, you have paid the cost
you were trying to avoid, and §0.5b's t_det argument applies with force. Three
escapes, in increasing ambition:

1. Use a **cheap proxy** — Δt·λ_ref for a small set of reference rates (the
   dominant photodisintegrations), interpolated from a small table in (T, ρ).
   This is O(10) evaluations rather than O(600).
2. Use the **previous step's** τ, which is free in a rollout.
3. Learn τ as an auxiliary output head with its own loss, so the model builds
   the representation explicitly rather than implicitly.

None is obviously right. The point is that "condition on log Δt" is a choice
that was never framed as one, and the physically correct variable is known,
already implemented elsewhere in the repo, and measurably better-scaled.

Open (register: **R-10**) — a Tier-4 design input that should be on the table
before S19 is built, not after.

---

## II.8 Cancellation-aware residuals

The handshake's original net tolerance conflates two very different failures:
a wrong rate, and a correct rate evaluated where cancellation amplifies its
error. §II.4(b) says the amplification is 1/κ at the column level; the
per-*isotope* analogue is

$$
c_i \;=\; \frac{\big|\sum_j \nu_{ij}\varphi_j\big|}{\sum_j |\nu_{ij}\varphi_j|}
\;=\; \frac{|\dot Y_i|}{\text{gross turnover}_i} \in [0,1].
$$

`build_cells` computes both this and the *rate-level* residual

$$
\text{resid\_gross}_i \;=\; \frac{|\Delta X_{\mathrm{pred}} - \Delta X_{\mathrm{lab}}|}{A_i\,\text{gross}_i\,dt},
$$

whose whole point is that it is **immune to cancellation amplification**: it
asks "is the flux right at the scale of the fluxes", not "is the difference of
two large fluxes right at the scale of the difference".

Both are needed, and the measured pair is the evidence that the framework is
correct:

| statistic | mesa_80 | mesa_151 | **[RESULTS]** |
|---|---|---|---|
| rate-level residual, linearizable cells: median | 3.6×10⁻³ | 2.8×10⁻³ | 2026-07-10 |
| … p90 | 4.7×10⁻² | 2.6×10⁻² | |
| … fraction ≤ 5% | 90.3% (of 292,959) | 94.4% (of 596,607) | |
| net-tolerance agreement at c ≥ 0.1 | 0.894 | 0.937 | |
| … at c ≥ 0.5 | 0.923 | 0.959 | |
| … at c ≥ 0.9 | 0.937 | 0.970 | |

**Agreement rises monotonically with c.** That is the 1/c amplification law
showing up in a measurement — the fluxes are equally good everywhere, and the
*net* comparison degrades exactly where cancellation says it must. Reading it
the other way round: the residual structure of the handshake is a direct
measurement of the QSE cancellation the kill-test targets.

And the departure classification closes the loop. Of the rate-level failures
(9.7% / 5.6% of linearizable cells), mesa_80: 69.4% are the DB-reverse
pf-provenance class (Tier 1's 0.05–0.1 dex band), 25.1% subfloor-controller
(the dominant channel's reactant is below the 10⁻¹⁵ label floor — invisible to
the emulator too, so not a defect), 5.4% weak-tabular interpolation, and **9
cells unexplained**. mesa_151: 63.6% / 12.6% / 23.8%, **unexplained: none**.
**[RESULTS]** 2026-07-10. Nine unexplained cells out of ~293k, all in one
light-sector multibody channel, is what a genuinely closed error budget looks
like.

---

## II.9 The measurement that reframed the project: the vacuous pass

Now the headline, and the thing most worth understanding correctly.

**On the training grid, κ ≈ 1 essentially everywhere.**

| | mesa_80 | mesa_151 | **[RESULTS]** |
|---|---|---|---|
| median log₁₀κ, every T₉ stratum | ≈ −0.05 | ≈ −0.05 | 2026-07-11 |
| fraction κ > 0.1 | 0.985–0.999 | 0.974–0.997 | |
| fraction κ < 10⁻³ | 0.000 | 0.000 | |
| per-isotope cancellation cᵢ, median | 0.87–1.0 | 0.87–1.0 | 2026-07-10 |
| κ-active union over strata | **all** 327/327 net cols | **all** 846/846 | 2026-07-11 |
| ⇒ cond(S_active) | 41.8 | 57.4 | |

Confirmed at full corpus scale (1,034,704 in-strata states per network).

The gate — "active set carries ≥ 95%, cond < 10⁶" — passes *trivially*, and the
pass is **vacuous**: the active set is everything, so of course it carries
everything.

**Why.** The training grid is Sobol-sampled in composition space. A random
composition is nucleon-loaded (median X_neut ≈ 1.7×10⁻²) and nowhere near any
equilibrium: affinities are enormous, so by §II.4(c) κ = |tanh(𝒜/2kT)| ≈ 1.
The states are not *wrong*; they are simply not the states where QSE lives.

**The consequence that reorganises everything downstream.** The cancellation
structure — the thing Target A is designed for and the kill-test is designed to
measure — **exists only on relaxed states**, i.e. on trajectories, not on the
training distribution. Which means:

1. The kill-test verdict must be computed on the relaxed manifold, not the
   grid. Hence Step 6's whole shape: pre-terminal trajectory rows, plus a bbq
   rerun campaign to get clean ones.
2. The dt = 1e-6 grid-mode handshake premise is **void** — 99.99% / 100.00% of
   cells have τ < dt. The shortest label step is a *stiff relaxation*, not a
   linear step (label |ΔX|/X median ≈ 1). **[RESULTS]** 2026-07-10. Only the
   trajectory-mode handshake is informative.
3. And it says something uncomfortable about the training data itself: the
   emulator is being trained on states whose dynamics are dominated by relaxing
   an unphysical initial condition, while it will be *deployed* on states that
   have already relaxed. That is a distribution-shift problem no architecture
   fixes — it is the "Sobol → real-MESA" gate in `CLAUDE.md`, and the reason the
   trajectory-aware-resampling clause exists.

**What the relaxed manifold looks like instead.** Not the clean bimodal
picture QSE theory would suggest, either:

- strong pairs with κ < 10⁻³ (clean detailed balance): **≤ 0.4%** of carrying
  pairs in every stratum/phase — clean balance essentially never occurs;
- instead a **continuum** of κ ∈ 10⁻³…10⁻¹, with the fraction κ > 0.1 dropping
  to 0.70/0.64 in the T₉ ∈ [5.0, 6.3) stratum;
- the low-κ share of active net columns is 0.9%–24%, **below the ~30% spread
  FAIL line everywhere**;
- coverage of dominant-isotope |ΔX| turnover: ≥ 0.95 in most strata, but the
  *worst* dominant isotope per row falls to 0.0022–0.166 (mesa_80) /
  0.0084–0.070 (mesa_151) across the [4.0, 6.3) strata.

**[RESULTS]** 2026-07-12. A split verdict, and Tier 3 is where it gets read.

Note the last row carefully, because it is the most consequential number in the
node: **some dominant species' net evolution rides on near-cancelled columns**,
with 1/κ amplification of 10–10³ on gross-scale errors. That is Target A's real
exposure, and it is not visible in any aggregate statistic — only in the
per-row *minimum* over dominant isotopes.

---

## II.10 Code and oracles

**Read:** `fluxes/engine.py` (207 lines) — `evaluate_lambda` then
`evaluate_fluxes`; the pair block is 5 lines and the κ block is 3.
`fluxes/store.py` — the round-trip. `fluxes/handshake.py` — read the docstring
first, it is the interpretation contract.

**Oracles** (`tests/test_flux_engine.py`):

| test | what it pins |
|---|---|
| `test_matches_pyna_evaluate_ydots` | νR vs pynucastro on the same states — the external oracle |
| `test_baryon_drift_within_gate` | S7's conservation, now on *physical* fluxes |
| `test_dye_weak_nonzero` | invariant #3 on physical states |
| `test_weak_columns_have_zero_reverse_and_kappa_one` | §II.5 |
| `test_pair_antisymmetry`, `test_pair_map_is_involution_on_strong_pairs` | the ν_{·k} = −ν_{·j} half of §II.3 |
| `test_net_identity` | §II.3 |
| `test_kappa_definition` | both branches incl. zero denominator |
| `test_kappa_vanishes_at_nse_unscreened` | §II.4(a) — the DB reading |
| `test_screening_asymmetry_offsets_kappa_at_nse` | §II.4(c) — the tanh reading |

`tests/test_flux_store.py` checks the round-trip is lossless and the
`complete` attribute semantics. `tests/test_handshake_synthetic.py` builds a
network with a deliberately corrupted channel and requires it to surface —
the regression that keeps the median-based calibration honest.

**④ SEE:** notebook `05-flux-engine.ipynb` — Fig 1 κ on the training grid
(unscreened), Fig 2 the vacuous pass summarised, Fig 3 the screened-κ offset
diagnostic. Note the notebook helper requires a **declared κ convention** before
it will plot: `nbsupport.py` refuses a κ figure that does not say whether it is
screened. That is `CLAUDE.md`'s two-κ rule as executable policy.

---

## II.11 Self-check for S8

1. Write R_j in full and say what `dens_exp` and `prefactor` each correct for.
2. Prove νR = Σ_{net} ν φ. Which property of the pair map does the proof need,
   and which test asserts it?
3. Derive κ = |tanh(𝒜/2kT)|. What does it predict about the relationship
   between κ and the Guidry δ?
4. A reverse rate is 20% too large at a state in balance. What κ do you
   measure?
5. Why is the *rate-level* residual needed in addition to the net-tolerance
   agreement? What does the monotone rise of agreement with c demonstrate?
6. Why is the handshake's label-noise floor calibrated with a median rather
   than a p99, and what test would fail if it were changed?
7. κ > 0.1 covers 98.5–99.9% of the training grid. Why is that a *bad* result?
8. The store does not persist φ or κ. Why is nothing lost?

---

# Part III (S9) — NSE and QSE

Part 0 said equilibrium is what makes silicon burning tractable. This node
makes it *computable*: an independent Saha solver, a cluster generalisation, and
two departure diagnostics. Without it, "this reaction is equilibrated" has no
measurable meaning, and the kill-test has no reference.

The independence matters. `qse/` deliberately uses **the same nuclear inputs**
as pynucastro (Rauscher partition functions, `Nucleus.nucbind`, `Nucleus.A_nuc`,
`Nucleus.spin_states`) but an entirely separate solver. Shared data + separate
algorithm = the cross-check tests the *solver*, not the data. If it used its own
masses too, agreement would prove nothing about either.

---

## III.1 Equilibrium from the ensemble

### The distribution

For a species i treated as an ideal, non-degenerate, non-relativistic gas with
ground-state spin degeneracy (2J_i + 1) and internal partition function G_i(T),
the grand-canonical number density is

$$
n_i \;=\; (2J_i+1)\,G_i(T)\left(\frac{m_i kT}{2\pi\hbar^2}\right)^{3/2}
\exp\!\left(\frac{\mu_i - m_i c^2}{kT}\right),
$$

with μ_i the full chemical potential (rest mass included). Define the **kinetic**
chemical potential u_i ≡ μ_i − m_i c²; this is what the code's `u_p`, `u_n`
are, in MeV.

**Is Maxwell–Boltzmann legitimate here?** It must be checked, because the
*electrons* in this plasma are strongly degenerate (Tier 0 §0.1). The criterion
is n_i λ_i³ ≪ 1 with λ = h/√(2πm kT). At box centre (T₉ = 4, ρ = 10⁸ g/cm³) for
A = 28: m = 4.65×10⁻²³ g, kT = 5.52×10⁻⁷ erg, so λ = 5.2×10⁻¹³ cm, λ³ =
1.4×10⁻³⁷ cm³, and at X = 1, n = ρ/(A m_u) = 2.2×10³⁰ cm⁻³. Hence

$$
n\lambda^3 \;\approx\; 3\times10^{-7} \;\lll\; 1. \qquad\text{[derived here]}
$$

Six and a half orders of margin. Nuclei are classical here; electrons are not,
because m_e is 5×10⁴ times smaller and λ_e³ correspondingly 10⁷ times larger.
**The same plasma is simultaneously classical in its nuclei and degenerate in
its electrons**, which is why the electron sector needs a Fermi treatment (Tier
1 §V.4) while the Saha algebra can stay Boltzmann.

### The equilibrium condition

Chemical equilibrium for reaction j is Σ_i ν_{ij} μ_i = 0 (in the full μ). Since
the reaction graph is connected through the light particles (§I.11) and every
nucleus is reachable from free nucleons by strong reactions, all such conditions
collapse to a single family:

$$
\mu_i \;=\; Z_i\,\mu_p + N_i\,\mu_n .
$$

---

## III.2 Where the binding energy comes from

Substituting μ = u + mc²:

$$
u_i + m_ic^2 \;=\; Z_i(u_p + m_pc^2) + N_i(u_n + m_nc^2)
$$

$$
\Longrightarrow\quad u_i \;=\; Z_i u_p + N_i u_n + \underbrace{\big[Z_i m_p + N_i m_n - m_i\big]c^2}_{\textstyle B_i}.
$$

**The binding energy appears as the rest-mass bookkeeping of the equilibrium
condition, not as an extra assumption.** This is worth doing once by hand,
because it is the reason `nucbind` shows up in a *chemical-potential* formula
and the reason the equilibrium distribution favours the most-bound nucleus:
B_i/kT is an exponential reward for binding.

At T₉ = 4, kT = 0.345 MeV, and B(⁵⁶Ni) = 484 MeV, so B/kT ≈ 1400. The Saha
exponent is enormous; what keeps abundances finite is the competition against
the −ln ρ and (Z u_p + N u_n)/kT terms, with u_p and u_n both strongly negative.
Measured, at ρ = 10⁸ g/cm³ **[derived here]**:

| (T₉, Yₑ) | u_p [MeV] | u_n [MeV] | dominant species |
|---|---|---|---|
| (4, 0.50) | −5.09 | −12.41 | ⁵⁶Ni (X = 0.94) |
| (4, 0.47) | −7.47 | −10.14 | ⁵⁶Fe, ⁵⁴Fe, ⁵⁸Ni |
| (3.5, 0.47) | −7.43 | −10.15 | ⁵⁶Fe, ⁵⁴Fe, ⁵⁸Ni |
| (5, 0.47) | −7.58 | −10.10 | ⁵⁶Fe, ⁵⁴Fe, ⁵⁸Ni |

Two things to read off. The Yₑ = 0.47 rows are §0.2.3's endpoint claim, measured:
drop Yₑ three points below 0.5 and the equilibrium abandons ⁵⁶Ni for the
neutron-richer Fe-peak species. And the *difference* u_p − u_n is the free-nucleon
ratio, exactly — since B_p = B_n = 0 and the mass/spin factors are ≈ 1,

$$
\frac{X_p}{X_n} \;\approx\; \exp\!\frac{u_p - u_n}{kT},
$$

which the solver confirms: at Yₑ = 0.50, u_p − u_n = 7.32 MeV = 21 kT and
X_p/X_n = 1.7×10⁹ (X_p = 6.3×10⁻⁴, X_n = 3.8×10⁻¹³); at Yₑ = 0.47,
u_p − u_n = 2.67 MeV = 7.7 kT and the ratio is 2.3×10³. Note the free nucleons
are *not* balanced even at Yₑ = 0.5 — with ⁵⁶Ni holding 94% of the mass there is
almost no neutron the composition needs to leave free, so u_p − u_n runs to tens
of kT. The lesson for reading a solver trace is that u_p − u_n is a steep,
directly interpretable function of Yₑ, not that it is small. [derived here]

> **Do not read the solver's `init=(-3.5, -15.0)` as typical values.** It is a
> seed chosen to sit safely inside the convergence basin, not a converged
> answer, and nothing in the table above lands near it — u_p is 1.5–4 MeV too
> high and u_n 2–5 MeV too low. The arrow in the original claim runs backwards:
> the seed is "somewhere Newton reliably converges *from*", which is a numerical
> property, and inferring physics from it is exactly the mistake.

---

## III.3 The Saha coefficient, term by term

Convert to mass fraction: X_i = n_i m_i/ρ with m_i = A_nuc,i · m_u.

$$
\ln X_i = \ln(A_{{\mathrm{nuc}},i} m_u) - \ln\rho + \ln(2J_i+1) + \ln G_i
+ \tfrac32\ln\!\frac{m_i kT}{2\pi\hbar^2} + \frac{Z_iu_p + N_iu_n + B_i}{kT}.
$$

Collect the two mass terms: ln(A_nuc m_u) + (3/2)ln(A_nuc m_u) = **2.5**·ln(A_nuc m_u).
Hence

$$
\boxed{\ \ln X_i \;=\; \underbrace{\tfrac52\ln(A_{{\mathrm{nuc}},i}m_u) + \ln(2J_i+1) - \ln\rho
+ \tfrac32\ln\!\frac{kT}{2\pi\hbar^2} + \ln G_i(T) + \frac{B_i}{kT}}_{\textstyle \log C_i(T,\rho)}
\; + \; \frac{Z_iu_p + N_iu_n}{kT}\ }
$$

which is `qse/coeffs.py::nse_log_coeffs_batch`, line for line:

```python
species = 2.5*np.log(inputs.A_nuc * constants.m_u_C18) + np.log(inputs.spin_states)
bind    = inputs.nucbind * inputs.A                     # B/A × A = B
state   = -np.log(rho) + 1.5*np.log(constants.k*T / (2.0*np.pi*constants.hbar**2))
return species[None,:] + state[:,None] + log_pf + bind[None,:]/kT_MeV[:,None]
```

**Three details that are easy to get subtly wrong.**

1. **A_nuc vs A.** The mass prefactor uses `A_nuc` (the *actual* mass in amu:
   27.9769 for ²⁸Si), the binding term uses the integer `A` (nucleon count).
   Using A for both would introduce a factor exp(2.5·ln(A/A_nuc)) ≈ 1.002 —
   a 0.2% error, invisible in a plot and fatal to a 10⁻¹² cross-check.
2. **G vs (2J+1)G.** Tier 1 §III.3 flags this normalisation trap on the rate
   side; the same trap exists here, and the code splits the two explicitly
   (`spin_states` and `log_pf` as separate terms) rather than relying on a
   library convention.
3. **`EXP_CLIP = 500`.** The Saha exponent is clipped before exponentiation,
   matching pynucastro (`nse_network.py:212`). exp(500) ≈ 10²¹⁷, comfortably
   inside float64's 1.8×10³⁰⁸ — so the clip prevents overflow during Newton
   excursions from a bad guess *without* affecting any converged answer, where
   X ≤ 1.

**The cross-check.** `tests/test_qse_coeffs.py` compares these mass fractions
at *fixed* (u_p, u_n) against pynucastro's `_nucleon_fraction_nse`, ≤10⁻¹² rel.
Fixing u removes the solver from the comparison entirely: this test isolates
the coefficient construction. Only then does `test_qse_solver.py` compare
converged solutions. **Layered oracles again** — the same discipline as
`test_conservation.py`'s two layers (§I.13).

---

## III.4 The two constraints

logC determines the *shape*; two constraints fix (u_p, u_n):

$$
F_0(u_p,u_n) = \sum_i X_i - 1 = 0, \qquad
F_1(u_p,u_n) = \sum_i \frac{Z_i}{A_i}X_i - Y_e = 0 .
$$

The second is Yₑ = Σ Z_i Y_i = Σ (Z_i/A_i) X_i (Tier 0 §II.5). Note what is
*not* a constraint: nothing about neutrons separately, because baryon number is
already carried by ΣX = 1. Two constraints, two unknowns — the count of §0.1.1.

**And note the convention mix, because §III.3 just made a fuss about exactly this
distinction.** X_i is built from the *actual* mass A_nuc, but F₁ uses the
**integer** A (`solver.py`: `((Z / A) * X).sum() - ye`). Strictly, if
ΣA_nuc,i Y_i = 1 then Yₑ = Σ Z_i X_i / A_nuc,i, and using Z/A instead shifts it by
~0.1%. This is deliberate and correct, for a reason worth stating: **Yₑ here is
not a derived quantity being computed accurately, it is a boundary condition
being imposed**, and the convention that must match is the one used by everything
that consumes it — pynucastro's NSE solver, MESA's `ye`, and the Yₑ column of the
training data all define Yₑ = Σ(Z_i/A_i)X_i with integer A. Using A_nuc here
would make the solver internally prettier and externally inconsistent, which is
the wrong trade. §III.3's detail (1) is about a quantity being *computed*; this
is a quantity being *matched*.

---

## III.5 Newton with an analytic Jacobian

Since ∂X_i/∂u_p = X_i Z_i/kT and ∂X_i/∂u_n = X_i N_i/kT, the Jacobian is
available in closed form and costs nothing beyond the residual evaluation:

$$
J \;=\; \frac{1}{kT}
\begin{pmatrix}
\sum X_iZ_i & \sum X_iN_i\\[2pt]
\sum X_iZ_i^2/A_i & \sum X_iZ_iN_i/A_i
\end{pmatrix}
$$

```python
J = np.array([[(X*Z).sum(),       (X*N).sum()],
              [(X*Z*Z/A).sum(),   (X*Z*N/A).sum()]]) / kT
```

**Step damping.** `_MAX_STEP_MEV = 2.0`: the Newton step is capped at 2 MeV in
∞-norm. Why a cap is *necessary* rather than merely prudent falls straight out
of §III.6's derivative: when one species dominates, the compositional variance
of Z/A collapses and the Jacobian becomes nearly singular in the u_p direction,
so an undamped step can be tens of MeV — which lands in a region where the
exponent clips and the residual carries no gradient at all. The cap is a trust
region; 2 MeV is ~6 kT at T₉ = 4, so it never obstructs a well-scaled step.

---

## III.6 ⚠ The monotonicity proof — why the bisection fallback works

The fallback is a nested bisection, and it rests on two monotonicity claims
that the code states as comments. Both are provable, and the second is not
obvious.

**Claim 1.** At fixed u_p, ΣX is strictly increasing in u_n.

$$
\frac{\partial}{\partial u_n}\sum_i X_i \;=\; \frac{1}{kT}\sum_i X_iN_i \;>\;0
$$

whenever any species with N > 0 has nonzero abundance. Immediate. This licenses
`u_n_for_mass`, the inner bisection.

**Claim 2.** Along the curve ΣX = 1, Yₑ is strictly increasing in u_p.

Not immediate — u_n must move to keep ΣX = 1, and it moves *down*, which pushes
Yₑ up further but also removes mass. Do it properly. Write w_i = X_iA_i,
a_i = Z_i/A_i, and

$$
S_Z=\sum X_iZ_i,\quad S_N=\sum X_iN_i,\quad M_{ZZ}=\sum X_i\frac{Z_i^2}{A_i},\quad M_{ZN}=\sum X_i\frac{Z_iN_i}{A_i}.
$$

Implicit differentiation of ΣX = 1 gives du_n/du_p = −S_Z/S_N. Then

$$
kT\,\frac{dY_e}{du_p}\bigg|_{\Sigma X=1}
= M_{ZZ} - \frac{S_Z}{S_N}M_{ZN}
= \frac{1}{S_N}\Big(M_{ZZ}S_N - M_{ZN}S_Z\Big).
$$

Substitute Z_i = a_iA_i, N_i = (1−a_i)A_i so that M_ZZ = Σw a², S_N = Σw(1−a),
M_ZN = Σw a(1−a), S_Z = Σw a:

$$
M_{ZZ}S_N - M_{ZN}S_Z
= \sum_{i,j} w_iw_j\big[a_i^2(1-a_j) - a_i(1-a_i)a_j\big]
= \sum_{i,j} w_iw_j\big[a_i^2 - a_ia_j\big].
$$

Symmetrise in (i, j):

$$
= \tfrac12\sum_{i,j} w_iw_j\,(a_i-a_j)^2 \;=\; W^2\operatorname{Var}_w\!\left(\frac{Z}{A}\right),
\qquad W=\sum_i w_i,
$$

with Var_w the w-normalised variance. Therefore

$$
\boxed{\ \frac{dY_e}{du_p}\bigg|_{\Sigma X=1}
\;=\; \frac{W^2}{kT\,S_N}\operatorname{Var}_w\!\left(\frac{Z}{A}\right) \;>\; 0\ }
\qquad\text{[derived here]}
$$

strictly, unless every abundant species has the same Z/A. ∎

This is a satisfying result for three reasons. It **licenses the outer
bisection** (`if F[1] > 0: hi_p = u_p`) as a theorem rather than a hope. It
**explains the damping cap** (§III.5): the derivative is proportional to the
compositional spread in Z/A, so near a single-species composition the map is
nearly flat and Newton overshoots. And it **identifies the exact degenerate
case** — a composition of species all with identical Z/A (e.g. pure α-chain
matter, Z/A = 1/2 throughout) makes Yₑ independent of u_p entirely.

Be precise about what that degeneracy is, because the natural way to say it is
backwards. With every Z/A = ½, Yₑ ≡ 0.5 *identically*, whatever u_p does. So
Yₑ = 0.5 is not the unachievable value — it is the **only** achievable one, and
F₁ ≡ 0 leaves u_p completely undetermined (the Jacobian's second row vanishes);
any target Yₑ ≠ 0.5 is infeasible, and the bisection has no sign change to
bracket. Both failure modes — an undetermined u_p and an infeasible constraint —
are the same vanishing Var_w(Z/A). That is not hypothetical: an α-chain-only
network at exactly Yₑ = 0.5 is the textbook NSE example, and it is precisely
where the solve is degenerate. The production networks avoid it by containing
odd-A species.

**Honest caveat.** Claim 2 is proved *along the ΣX = 1 curve for the exact
solution*. The fallback's outer loop calls an inner solve that terminates on a
finite tolerance, so the composed map is monotone only up to that tolerance —
which is why the fallback still returns `converged=False` with a residual rather
than assuming success. The code is right not to trust the proof further than it
goes.

---

## III.7 Batching, and why the scalar path survives

`solve_nse_batch` / `solve_qse_batch` run one vectorised damped-Newton loop over
all states with per-row convergence masking and per-row damping, then hand any
row that did not converge in the Newton phase to the **scalar** solver, which
retries Newton and applies the bisection fallback.

Two design points worth stealing:

- **`_batched_2x2_step` / `_batched_3x3_step` use closed-form Cramer/adjugate
  solves, not `np.linalg.solve`.** The reason is in the docstring: a batched
  LAPACK solve *aborts the whole batch* if any single row is singular. A
  closed-form solve never raises; singular rows are flagged and dropped to the
  fallback. Vectorisation must not make robustness worse than the loop it
  replaces.
- **The batched result is required to be identical to a per-state loop**, and
  that is a test (`test_nse_batch_matches_scalar_loop`,
  `test_qse_batch_matches_scalar_loop`), not a hope. Same `EXP_CLIP`, same
  `_MAX_STEP_MEV`, same `_MAX_ITER`, same tol, same float64.

---

## III.8 QSE: the cluster and u_G

Now the generalisation of §0.1.1. Group G (the silicon group) is internally
equilibrated but not equilibrated with the free nucleons; non-members are in
NSE with the nucleons. The chemical-potential ansatz gains one offset:

$$
\mu_i \;=\; Z_i\mu_p + N_i\mu_n + u_G\,\mathbf{1}[i\in G],
$$

so in the Saha exponent,

```python
expo = logC + (Z*u_p + N*u_n)/kT
if group is not None:
    expo = expo + np.where(group, u_g/kT, 0.0)
```

Three unknowns (u_p, u_n, u_G) need three constraints; the third is the
**measured group mass fraction**:

$$
F_2 \;=\; \sum_{i\in G} X_i - X_G^{\mathrm{meas}} \;=\; 0 .
$$

The 3×3 Jacobian is the same construction with dg = 1_G:

$$
J = \frac{1}{kT}\begin{pmatrix}
\sum XZ & \sum XN & \sum X\mathbf{1}_G\\
\sum XZ^2/A & \sum XZN/A & \sum XZ\mathbf{1}_G/A\\
\sum XZ\mathbf{1}_G & \sum XN\mathbf{1}_G & \sum X\mathbf{1}_G
\end{pmatrix}
$$

Note J[0,2] = J[2,2]: both are Σ_{i∈G} X_i, because ∂(ΣX)/∂u_G and
∂(X_G)/∂u_G are the same sum. A useful hand-check when reading the code.

**u_G = 0 recovers NSE**, and that is a test:
`test_degenerates_to_nse_when_group_mass_is_nse` — feed the QSE solver the group
mass *taken from the NSE solution*, and require |u_G| < 10⁻⁶ MeV.
**[RESULTS]** 2026-07-10 records it. A solver that could not do this would be
solving a different problem.

**What u_G means physically.** exp(u_G/kT) is the factor by which the whole
silicon group is over- or under-populated relative to NSE at the same nucleon
potentials. Measured on pre-stall trajectory rows: median **+4.3 / +4.1 MeV**
(**[RESULTS]** 2026-07-10). At kT ≈ 0.35 MeV that is exp(12) ≈ 2×10⁵ — the Si
group is over five orders of magnitude *over*-populated relative to NSE, which
is exactly what "mid-burn, not yet at the iron peak" means quantitatively.
Reading u_G is the cleanest single number for "how far through silicon burning
is this state".

---

## III.9 QSE as a slow manifold

The reason QSE is a *dynamical* statement and not just an algebraic one.

Split the RHS by timescale:

$$
\dot Y \;=\; \frac{1}{\epsilon}f_{\mathrm{fast}}(Y) + f_{\mathrm{slow}}(Y), \qquad \epsilon \ll 1,
$$

where f_fast collects the near-balanced strong pairs and f_slow the bridges and
weak columns. Singular perturbation theory (Tikhonov) says: from generic
initial conditions the system relaxes on timescale ε onto the manifold
𝓜_slow = {f_fast(Y) = 0}, and thereafter moves *within* 𝓜_slow at the rate set
by f_slow.

- **𝓜_slow is exactly the QSE manifold.** f_fast = 0 is "every intra-cluster
  reaction balances", which is the chemical-potential ansatz of §III.8.
- **Its dimension is the QSE parameter count**, 2 + g (plus Yₑ), which is why
  the reduction works at all.
- **The stiffness ratio is 1/ε.** So *stiffness and QSE are the same
  phenomenon* — Tier 0 §V.3 says this, and here is the reason: a stiff system
  is one with an attracting low-dimensional manifold, and the manifold is the
  equilibrium.
- **The group mass is the slow coordinate.** This is why QSE needs a measured
  X_G: the reduction removes the fast directions and leaves the slow ones to be
  supplied dynamically.

Two consequences that carry into §IV and Tier 4:

1. An implicit solver's step size is limited by the *slow* dynamics once on the
   manifold; an explicit solver's by the *fast* ones forever. That is the whole
   argument for BDF (§IV.2).
2. An emulator learning one Δt step is learning the **flow map restricted to
   𝓜_slow** for states already on it, and the *relaxation onto* 𝓜_slow for
   states off it. Those are different functions with different smoothness. The
   training grid consists overwhelmingly of the second kind (§II.9); deployment
   is the first. Naming this makes the distribution-shift problem concrete
   rather than vague.

---

## III.10 The two departure diagnostics — and they are not the same

`qse/diagnostics.py` provides two, computed against **different references**.
Conflating them is easy and wrong.

| | δ (Guidry) | r_QSE |
|---|---|---|
| formula | δ_i = \|Y_i − Ȳ_i\|/Ȳ_i | r_i = log₁₀(Ȳ_i/Y_i) |
| reference Ȳ | **NSE** at the row's (T, ρ, Yₑ) | **QSE** solution fitted to the row |
| per-reaction form | δ_r = max over participants | — (species-level) |
| used for | the maskable set (`eligible_mask`) | the single-cluster plateau signature |

**δ_r = max over participants** (`reaction_delta`) is deliberately conservative:
one badly-departed participant disqualifies the whole column from masking. The
alternative (mean, or a flux-weighted combination) would mask columns with a
badly-wrong minority participant, and the mask's whole safety argument is that a
masked column's dynamics are negligible. Max is the right choice and the
docstring does not say why, so: *the failure mode of masking is deleting real
flux, and the participant that carries the real flux is the departed one.*

**`eligible_mask` is where invariant #2 lives structurally:**

```python
return (delta_r < epsilon) & ~np.asarray(weak_mask, dtype=bool)
```

The `& ~weak_mask` is not an optimisation. β/EC are not in detailed balance in
this regime, so their δ against an NSE reference is meaningless — an NSE
reference *has* a Yₑ, imposed as a constraint, so "the weak sector is in
equilibrium" is baked into the reference by construction. Masking on that basis
would be circular. `killtest.active_set.guidry_masks` routes exclusively through
this function, and `test_weak_never_maskable` asserts it structurally.

**The r_QSE plateau, derived.** Why should log₁₀(Ȳ/Y) be *constant across group
members* if the group is internally equilibrated? If both the actual composition
and the reference satisfy the Saha form with potentials (u_p, u_n, u_G) and
(u_p′, u_n′, u_G′) respectively, then for i ∈ G

$$
\ln\frac{\bar Y_i}{Y_i} \;=\; \frac{Z_i\Delta u_p + N_i\Delta u_n + \Delta u_G}{kT}.
$$

If the fitted reference recovers the actual nucleon potentials (Δu_p = Δu_n = 0)
this is a constant Δu_G/kT — a **plateau**. So the plateau is the operational
signature of "the group is a single Saha cluster".

**And here is the caveat that the measured negative result needs.** The QSE
reference is fitted with three constraints — ΣX = 1, Yₑ, and the group mass —
all evaluated on the *whole* composition, including the non-group sector. On a
mid-burn trajectory the non-group sector (free nucleons, Fe group) is badly
described by the NSE-with-nucleons ansatz, and a poor fit there **pulls
(u_p, u_n) away from the group's own values**, leaving a (Z, N)-**linear tilt**
in r_QSE across group members that is *not* a failure of cluster equilibrium.
Group members span Z ≈ 12–21 and N ≈ 12–24, so a Δu_p of only ~0.1 MeV produces
~1 dex of intra-group spread at T₉ = 4 — the same order as the measured
std. [derived here]

I cannot settle this from the reported numbers, and it should be settled: the
sharper test is to fit (u_p, u_n, u_G) to the **group members alone** by least
squares and report the residual after removing the (Z, N)-linear trend. Logged
as **R-18**.

---

## III.11 The group boundary is a config variant, not a fact

`configs/qse_groups.yaml`:

```yaml
default: {a_min: 24, a_max: 45, exclude_light: true}   # Hix & Thielemann span
a28_up:  {a_min: 28,            exclude_light: true}
a24_46:  {a_min: 24, a_max: 46, exclude_light: true}   # ⁴⁵Sc inside the group
```

`exclude_light: true` forces Z > 2 — free n, p, ⁴He are never group members
(they are the reservoir the group exchanges *with*; putting them inside would
make the cluster the whole network). `load_group_mask` additionally refuses any
variant that excludes ²⁸Si, the canonical anchor.

Membership counts: 29 / 50 (default, mesa_80/151), 40 / 105 (a28_up).
**[RESULTS]** 2026-07-10.

**Why the boundary matters and is not resolvable by argument.** A reaction is a
*bridge* iff it crosses the boundary. ⁴⁵Sc(p,γ)⁴⁶Ti — the literature high-Yₑ
bottleneck — is a boundary crossing under `a24_46` and an internal reaction
under `default`. Under `a24_46` it ranks **2/251** inter-group carriers (share
0.10–0.12) on relaxed high-Yₑ QSE-window rows; under `default` its *feeder*
Ca44(p,γ)Sc45 ranks #4 instead. **[RESULTS]** 2026-07-10 / 2026-07-12.

`CLAUDE.md`'s rule — every group/bridge/inter-group analysis reports **both**
variants, and a verdict that flips between them is a *measured decision* — is
the correct response to an unfalsifiable modelling choice. Measured outcome:
the boundary variant changes top-k concentration by ≤ 0.02, so no verdict
depends on it (**[RESULTS]** 2026-07-12). That is the result you want from a
sensitivity variant: it was worth checking and it did not matter.

---

## III.12 What was measured — three negative results, read carefully

S9's headline outputs are negative, and each is informative in a different way.

**(1) The solver is right.** NSE cross-check vs pynucastro on the canonical
27-state grid: max |Δlog₁₀X| over X > 10⁻¹⁰ is **2.7×10⁻¹⁰** (mesa_80) /
**1.5×10⁻¹⁰** (mesa_151) against a 10⁻⁶ gate; 27/27 states, all Newton, no
fallback needed. **[RESULTS]** 2026-07-10. Two independent solvers on shared
data agreeing to ten digits is as strong as this kind of check gets.

**(2) The single-Si-cluster plateau is NOT confirmed.** Twice:

| | intra-group std(r_QSE) | plateau rows (< 0.1 dex) | non-group spread |
|---|---|---|---|
| Step 5, shipped trajectories | 1.33 / 1.45 dex | 0/129, 0/130 | 3.5 / 2.4 dex |
| Step 6, clean rerun trajectories | 0.87 / 0.80 dex | 0/303, 0/316 | 2.19 / 1.29 dex |

**[RESULTS]** 2026-07-10, 2026-07-11. The verdict: *group-organised but never
single-cluster-equilibrated* — the intra-group spread is 2.5–3× tighter than the
non-group spread, so the group *is* a real structure, but it is not a single
Saha cluster to within the plateau criterion. The Hix & Thielemann reference
does not describe this manifold.

Two honest qualifications on that verdict. (a) §III.10's tilt caveat may account
for a substantial part of the residual. (b) The label manifold's own equilibria
are displaced by the Appendix-B bug (Tier 3, S13), so "this manifold" is not
"physical silicon burning" — the clean-rerun repeat *narrowed* the spread
(1.33 → 0.87) but the reruns are stock MESA and carry the same bug.

**(3) The maskable set is EMPTY.** Guidry ε sweep {3×10⁻³, 10⁻², 3×10⁻²}:
maskable columns per row have **median 0 at every ε, both networks, p90 = 0**.
**[RESULTS]** 2026-07-12. Consequently cond(S_active) = cond(ν restricted to net
columns) = 41.8 / 57.4 at every ε, and **the hybrid design's maskable set does
not exist: Target A operates full-width on this data.**

Note precisely what is and is not concluded. It is *not* "there is no
cancellation" — §II.9 measured a continuum of κ ∈ 10⁻³…10⁻¹, i.e. plenty of
near-balance. It is that **δ measured against true NSE never crosses the mask
thresholds**, because the labels' equilibria are elsewhere. κ and δ correlate
(+0.491/+0.498) on *ordering* but not on threshold crossings — exactly the
monotone-but-differently-normalised relationship §II.4(c) predicts.

And the mask-churn measurement becomes moot: flips/step median 0.00–0.03,
churn ≤ 0.002%/step, trivially under the 5%/step freeze trigger — but the mask
is empty, so **the Component-B hybrid-vs-frozen decision is settled by
emptiness, not by churn** (**[RESULTS]** 2026-07-12). Worth noticing as a
process lesson: the project had a threshold and an instrument ready for a
question that turned out not to arise.

---

## III.13 Code and oracles

**Read:** `qse/coeffs.py` (132 lines — the derivation of §III.3 as code),
`qse/solver.py` (581 lines: scalar NSE → scalar QSE → batched, in that order),
`qse/diagnostics.py` (85 lines — small and load-bearing).

**Oracles:**

| test | pins |
|---|---|
| `test_qse_coeffs.py::test_mass_fractions_match_at_fixed_u` | §III.3, ≤10⁻¹² rel, solver excluded |
| `test_qse_solver.py::TestNSECrossCheck::test_matches_pyna_solver` | the converged solution, 3 box states |
| `test_constraints_satisfied` | F₀, F₁ at the returned solution |
| `test_degenerates_to_nse_when_group_mass_is_nse` | u_G → 0 (§III.8) |
| `test_offset_group_mass_moves_u_group` | the converse — u_G responds |
| `test_group_mask_contains_si28_not_light` | the config contract (§III.11) |
| `test_nse_batch_matches_scalar_loop`, `test_qse_batch_matches_scalar_loop` | §III.7 |
| `test_weak_columns_structurally_excluded` | **invariant #2** (§III.10) |
| `test_reaction_delta_max_over_participants` | the conservative δ_r |

**④ SEE:** notebook `06-qse-bridges.ipynb` — Fig 1 the Si group under both
boundary conventions, Fig 2 inter-group carriers side by side, Fig 3 whether
the boundary changes the answer (it does not).

---

## III.14 Self-check for S9

1. Show that nuclei are non-degenerate at box centre while electrons are not.
   Which quantity differs, and by how much?
2. Derive u_i = Z_i u_p + N_i u_n + B_i and say where the binding energy came
   from.
3. Write logC_i and identify each of its six terms. Why is A_nuc used in one
   place and integer A in another?
4. Prove dYₑ/du_p > 0 along ΣX = 1. What does the result say about when the
   solve is degenerate, and about why the Newton step is capped?
5. QSE has three unknowns. Name them and name the three constraints. Which one
   is dynamical rather than thermodynamic?
6. Explain "stiffness and QSE are the same phenomenon" in terms of a slow
   manifold.
7. δ and r_QSE use different references. Which uses which, and what breaks if
   you swap them?
8. The maskable set is empty, but κ shows a continuum of near-balance. Are
   these consistent? Explain in one sentence.

---

# Part IV (S10) — Stiff integration and the augmented flux state

The last node of the tier, and the one that produces something the shipped
dataset does not contain: **per-reaction integrated fluxes Φ**, the labels
Target A needs.

---

## IV.1 Stiffness, from the Jacobian

The network's Jacobian is a product of the two objects this tier is about:

$$
J_{ij} \;=\; \frac{\partial \dot Y_i}{\partial Y_j}
\;=\; \sum_k \nu_{ik}\frac{\partial R_k}{\partial Y_j}
\;=\; (\nu D)_{ij}, \qquad D = \frac{\partial R}{\partial Y}\in\mathbb{R}^{r\times n}.
$$

Its eigenvalues are (minus) inverse relaxation timescales. The spectrum here is
spectacularly spread, and the spread is *measured* rather than estimated:

- At the shortest label step dt₁ ≈ 1.011×10⁻⁶ s, **99.99% / 100.00%** of
  (state, isotope) cells on the training grid have τ_i = Y_i/|Ẏ_i| < dt₁
  (**[RESULTS]** 2026-07-10). So the fastest modes are ≪ 10⁻⁶ s.
- Trajectories are integrated out to ~10⁸ s.

That is a **stiffness ratio of at least 10¹⁴** within a single problem — and it
is not an artefact of a pathological state, it is the generic case here. Tier 0
§0.7's timescale hierarchy, now with a number attached.

**Why this kills explicit methods.** Forward Euler on ẏ = λy is stable only for
|1 + hλ| ≤ 1, i.e. h ≤ 2/|λ| for real negative λ. With |λ| ~ 10⁶ s⁻¹ the step
is capped at 2×10⁻⁶ s **regardless of how smooth the solution is**, and
reaching 10⁸ s needs ~5×10¹³ steps. The fast modes are long dead — they
contribute nothing to the answer — and they still dictate the cost. That is the
definition of stiffness: *step size limited by stability rather than by
accuracy.*

And §III.9 says why the fast modes die: they are the relaxation onto the QSE
manifold. **The stiffness and the equilibrium structure are the same fact.**

---

## IV.2 Why BDF, and what L-stability buys

An implicit method evaluates f at the new point, so the linear stability
function does not blow up for large negative hλ. The relevant hierarchy:

- **A-stable**: stable for all Re(hλ) < 0. Backward Euler and the trapezoidal
  rule are; **Dahlquist's second barrier** says no linear multistep method of
  order > 2 can be. So high-order multistep methods must settle for A(α)-stability.
- **BDF-k**: Σ_{m} α_m y_{n−m} = h β f(t_n, y_n). Zero-stable for k ≤ 6; A-stable
  for k ≤ 2; A(α)-stable with shrinking α for k = 3…5. scipy's `BDF` is
  variable-order 1–5 with adaptive steps, which is the right compromise: it
  drops order where the α-wedge bites.
- **L-stable**: A-stable *and* the amplification factor → 0 as hλ → −∞.
  Backward Euler has R(z) = 1/(1−z) → 0 ✓. The trapezoidal rule has
  R(z) → −1 ✗ — it is A-stable but leaves stiff transients **ringing** with
  undamped sign-alternating error.

**L-stability is the property that matters here**, and it is worth being
explicit about why: the physical content of a stiff transient in this system is
*relaxation onto the QSE manifold*. A method that keeps the transient
oscillating at amplitude 1 does not merely lose accuracy, it produces a
composition that oscillates around the manifold — and since abundances near the
manifold can be many orders below the dominant species, the oscillation goes
negative. Which is why `integrate.py` clips Y at 0 inside rate evaluation:

```python
Yc = np.maximum(np.asarray(Y, dtype=np.float64), 0.0)
```

with the docstring's justification — "transient small negatives from the linear
multistep are not propagated into powers". Note the clip is applied **only
inside rate evaluation**, not to the solver state: clipping the state would
inject mass and break conservation. Clipping the rate argument is a
regularisation of the RHS, and it is safe because the returned composition is
reconstructed from Φ (§IV.6) rather than from the clipped values.

**Radau IIA** (implicit RK, order 5, L-stable) is available for cross-checks,
and the cross-check was run: BDF ≡ Radau ≡ BDF(rtol 10⁻¹⁰) to **5×10⁻⁸** rel on
the stiffest test state. **[RESULTS]** 2026-07-12. Two structurally different
integrators agreeing is the only honest way to establish that neither is
lying — Tier 1 **R-23**'s Fortran-probe logic, applied to the ODE side.

---

## IV.3 The augmented state [Y, Φ]

`integrate_state` integrates

$$
\frac{dY}{dt} = \nu R(Y; T,\rho), \qquad \frac{d\Phi_j}{dt} = R_j(Y; T,\rho),
$$

with u = [Y, Φ] ∈ ℝ^{n+r} and Φ(0) = 0.

Φ is a pure quadrature: R depends on Y only, never on Φ. So the Φ block adds no
dynamics — mathematically it is n_rxn running integrals carried alongside. What
it adds is:

- **exactness**: ΔY = νΔΦ becomes an identity of the *discretisation*, not just
  of the continuum equations, because both are advanced by the same solver
  using the same R at the same stages;
- **cost**: the state vector grows from 80 → 687 (mesa_80) or 151 → 1669
  (mesa_151), and — more consequentially — the error test applies to all Φ
  components too (§IV.7, §IV.9).

**Gross, not net.** dΦ_j/dt = R_j is the *gross* per-column rate, matching the
engine's f⁺ convention exactly, so that the net view is recovered downstream
through `pair_col` in precisely the same way `store.py` does it (§II.6). One
convention, one place to be wrong. The docstring is explicit that this mirrors
the flux engine, and `test_rhs_matches_engine` pins it to ≤10⁻¹² rel.

---

## IV.4 ⚠ Why Φ cannot be recovered from ΔY

This is the reason the node exists, and it is a one-line consequence of §I.2.1.

Given a target ΔY, the solutions of νΦ = ΔY form an affine set of dimension

$$
r - \operatorname{rank}(\nu) \;=\; 607 - 79 \;=\; \mathbf{528}\quad(\text{mesa\_80}),
\qquad 1518 - 150 \;=\; \mathbf{1368}\quad(\text{mesa\_151}).
$$

So:

> **The shipped Zenodo labels (initial and final X, per state per dt) do not
> determine Φ.** Not "determine it noisily" — do not determine it at all, up to
> a 528-dimensional subspace.

Consequences, each of which shows up somewhere else in the repo:

1. **Target A cannot be supervised from the shipped labels alone.** A loss on
   ΔY = νΦ̂ constrains 79 of 607 directions. The remaining 528 are free, and a
   network is free to put arbitrary structure there — including physically
   absurd flux patterns that happen to produce the right ΔY. Hence
   `integrate.py`.
2. **The minimum-norm pseudo-inverse Φ = ν⁺ΔY is not the physical answer.** It
   is *a* solution, the one of smallest Euclidean norm, and there is no reason
   the physics should choose it. (Near QSE the physical Φ has enormous nearly
   cancelling components — precisely a *large*-norm solution.) Anyone tempted
   by `np.linalg.lstsq` as a shortcut should reread §II.9's κ ≈ 1 vs the relaxed
   continuum.
3. **Conversely, the redundancy is what makes masking meaningful** (§I.2.1) —
   the same fact, read the other way.

---

## IV.4b The flux head is unidentifiable under a ΔY-only loss

§IV.4 drew the *label* consequence of the 528- (1368-) dimensional solution set:
Φ is not recoverable from ΔY, hence `integrate.py`. There is a second
consequence, about **training**, and it is arguably the sharper one.

Suppose Target A is trained with a loss on ΔY alone (which is what the shipped
labels permit). Then the loss depends on the flux head's output only through
νφ̂, so:

$$
\nabla_{\theta}\mathcal{L} \;=\; \Big(\tfrac{\partial \hat\varphi}{\partial\theta}\Big)^{\!\mathsf T}\nu^{\mathsf T}\,\nabla_{\nu\hat\varphi}\mathcal{L},
$$

and **every parameter direction that moves φ̂ within null(ν) receives exactly
zero gradient.** The optimisation problem is rank-deficient by 528 dimensions
out of 607.

What actually happens to those directions in practice:

- they are set by **initialisation** and moved only by weight decay,
  regularisation, and the implicit bias of the optimiser — i.e. by everything
  except the physics;
- under SGD they can **random-walk**, since noise in the gradient estimate has
  components there even when the true gradient does not;
- and they are **invisible to every validation metric defined on ΔY**.

Three consequences:

1. **Target A's per-reaction interpretability is not guaranteed by a ΔY loss.**
   The selling point — "a flux error is attributable to a named reaction"
   (§0.1.3) — requires the flux head to be predicting *the physical* Φ, and a
   ΔY-only loss does not ask it to. The predicted fluxes could be arbitrarily
   wrong per column while ΔY is perfect. This substantially weakens the Target-A
   case *unless* flux-space supervision is used, which §IV.9 showed is
   affordable only on stratified subsets at T₉ < 5.
2. **It interacts with the mask.** Masking a column changes φ̂ and therefore
   changes νφ̂ *only* through the component outside null(ν). A mask trained under
   a ΔY loss is being optimised on a projection of its own effect.
3. **It is a rollout hazard, and a mild one.** Drift within null(ν) does not
   affect ΔY at all, so it cannot destabilise the trajectory directly — but it
   does mean the flux diagnostics one would use to *understand* an instability
   are unreliable.

The cheap mitigations are worth naming: regularise φ̂ toward small norm in
null(ν) (a fixed linear projection, exactly the machinery of §I.8 applied to the
flux space rather than the species space); or supervise on Φ for the subset
where it is affordable and on ΔY elsewhere; or report the null-space component
of φ̂ as a diagnostic so the drift is at least visible.

Open (register: **R-03**) — it bears directly on the Target A vs B decision,
which §I.10 showed is not about expressivity. This is a second, independent cost
of Target A, and §I.10's trade table now carries it.

---

## IV.5 ∂R/∂Y by the product rule

The dominant Jacobian term comes from the reactant product. With
R_j = base_j · Π_{k} Y_{idx[j,k]} (base_j collecting λ, ρ powers, prefactor):

$$
D_{ji} \;=\; \frac{\partial R_j}{\partial Y_i}
\;=\; \text{base}_j \sum_{k\,:\,\text{idx}[j,k]=i}\ \prod_{k'\neq k} Y_{\text{idx}[j,k']}.
$$

The code implements exactly the sum over slots:

```python
for k in range(K):
    pe = base.copy()
    for k2 in range(K):
        if k2 != k:
            pe *= Ypad[cn.reactant_idx[:, k2]]
    ...  # accumulate (row=j, col=idx[j,k], value=pe[j])
```

Two properties this construction has and the obvious alternative does not:

- **Repeated reactants are handled by the slot sum.** Triple-α has three slots
  all holding ⁴He; the sum of three products-of-the-other-two gives 3Y², which
  is d(Y³)/dY. Correct by construction, no special case.
- **No division.** The tempting shortcut is `R_j / Y_i`, which is faster and
  wrong: Y_i = 0 happens routinely (species below the floor, or exactly zero at
  t = 0), giving 0/0. Building the product with the differentiated factor
  *removed* is exact everywhere.

The sparse assembly `D.tocsr()` then feeds the block Jacobian

$$
J_{\mathrm{aug}} = \begin{pmatrix}\nu D & 0\\ D & 0\end{pmatrix},
$$

whose (2, 2) block is zero because R does not depend on Φ.

**A structural observation worth making** [derived here]: the BDF Newton matrix
is I − hβJ_aug, i.e.

$$
M \;=\; \begin{pmatrix} I_n - h\beta\,\nu D & 0\\ -h\beta\,D & I_r\end{pmatrix},
$$

which is **block lower triangular with an identity block**. Solving Mx = b is
therefore exactly: solve the n×n system (I − hβνD)x_Y = b_Y, then
x_Φ = b_Φ + hβ D x_Y — no r×r factorisation is needed at all. scipy's `BDF`
does not know this; it hands the whole (n+r)×(n+r) sparse matrix to `splu`.
Whether that costs anything real depends on the fill-in the ordering produces,
but it is a concrete optimisation candidate for the §IV.9 cost wall, and it is
*not* the same as the ADR-0006 contingency (which is about Jacobian
*accuracy*). Logged in **R-20**.

**The deliberately neglected chain (ADR 0006).** ∂λ/∂Y through (i) screening
(the plasma state depends on composition) and (ii) the Yₑ-weighting and tabular
ρYₑ inputs is *not* differentiated. The justification is standard and correct:
**an approximate Jacobian affects only the Newton convergence rate and hence
step efficiency, never the answer** — the residual that BDF drives to zero uses
the *exact* RHS. Measured: the neglected chain is ≲1% of entries
(`test_neglected_screening_chain_is_subdominant`), and the Jacobian is validated
against finite differences unscreened (`test_jacobian_vs_finite_differences_unscreened`).

But §IV.9 records the bill: at T₉ ≥ 5 the neglected **tabular-EC ρYₑ chain
dominates the weak-drift phase**, the quasi-Newton iteration stops converging
well, and the cost explodes. "Only affects efficiency" is true and can still be
the thing that makes a computation infeasible.

---

## IV.6 Conservation by construction, inside the solver

The returned composition is **not** the solver's error-controlled Y. It is

```python
Y = Y0 + cn.stoich.nu @ Phi
```

so that:

- ΔY = νΦ is an **identity**, not an approximation;
- baryon and charge conservation hold because Cν̃ = 0 (§I.7), with the same
  integer-exactness argument as §I.2.2;
- the solver's own Y is exposed as a *diagnostic*, `identity_resid` =
  max|Y_solver − Y|.

Measured: **2.1×10⁻¹⁶ molar** — machine precision. **[RESULTS]** 2026-07-12.

This is a small design decision with a big property, and it is worth naming the
pattern: **when two routes to a quantity exist and one is exactly conserving,
return that one and report the other as a residual.** You get exactness *and* a
free consistency check, and the check is sensitive to anything that would break
the correspondence (a wrong ν column, a solver bug, an inconsistent RHS).
`test_success_and_identity_by_construction`, `test_solver_consistency_residual`,
and `test_conservation_by_construction` split those three claims apart.

---

## IV.7 Error control for Φ

```python
rtol = 1e-8, atol_y = 1e-18, atol_phi = 1e-18
atol = np.concatenate([np.full(n_s, atol_y), np.full(n_rxn, atol_phi)])
```

Per-component absolute tolerances, which scipy supports and which matters here.
Tier 0 §V.6's point applies with force: **atol matters more than usual** when
the dynamic range is 15+ decades. rtol alone would demand 8 significant digits
on abundances at 10⁻³⁰ — unachievable and pointless. atol = 10⁻¹⁸ says "below
this, don't care", and 10⁻¹⁸ molar is ~5×10⁻¹⁷ in mass fraction for a
mid-network A ≈ 50 — **about one and a half decades** below the 10⁻¹⁵ label
floor (Tier 0 §III.6). (Compare the two in the *same* units before quoting a
margin: the three-decade figure is atol in molar against the floor in mass
fraction, which is not a comparison.) One and a half decades is still the right
call — the floor is chosen relative to what the labels can express, with enough
room that the integrator is never the binding constraint on a quantity the
labels could resolve.

The consequence for cost: the error test runs over **all** n + r components. For
mesa_151 that is 1669 error tests per step, of which 1518 are Φ components whose
magnitudes span the full range of reaction rates. A single fast-but-irrelevant
column near its atol threshold can throttle the step. This is the second
structural contributor to §IV.9, alongside the Jacobian one.

---

## IV.8 ⚠ The energy identity is a *data* check, not a dynamics check

`CLAUDE.md` invariant #5 requires the flux route and the composition route to
agree on e_nuc to ≤1%. It is worth seeing what that actually tests, because it
is not what it looks like.

The Q-value of reaction j is the mass-excess balance:

$$
Q_j \;=\; -\sum_i \nu_{ij}\,\Delta_i ,
$$

with Δ_i the mass excess of species i (reactants carry ν < 0, so this is
Σ_reactants Δ − Σ_products Δ, as it should be). Then

$$
\underbrace{\sum_j Q_j\Phi_j}_{\text{flux route}}
\;=\; -\sum_j\sum_i \nu_{ij}\Delta_i\Phi_j
\;=\; -\sum_i \Delta_i(\nu\Phi)_i
\;=\; \underbrace{-\sum_i \Delta_i\,\Delta Y_i}_{\text{composition route}} .
$$

**The two routes are algebraically identical, given ΔY = νΦ** — which §IV.6
makes true by construction. So the residual **cannot** be measuring integration
error. What it measures is the inconsistency between two nuclear-data sources:
the Q-values attached to the rate objects (`Rate.Q`, ultimately REACLIB/tabular
metadata) and the mass excesses attached to the nuclide objects
(`Nucleus`). If those were derived from the same mass table to full precision,
the residual would be at machine epsilon.

Measured: median 6×10⁻⁶…2.5×10⁻⁵ rel, max 8.7×10⁻⁴, **fraction ≤ 1% = 1.000 in
every measured stratum, both networks, including the whole 3–4 GK band**.
**[RESULTS]** 2026-07-12. Gate passed with ≥3 orders of margin — and now you
know what the margin is margin *on*: nuclear-data self-consistency at the
10⁻⁵ level, which is a perfectly reasonable thing to have measured and a
perfectly unreasonable thing to describe as validating the integrator.

**And the inconsistency is now measured directly.** §IV.8b runs the test this
argument implies — project Q onto rowspace(ν) and look at the residual — and
finds that the strong-sector Q-values are **not** reproducible by any single
mass table (rms 0.55 keV, max 3.5 keV per column, 331/561 and 972/1345 columns
above 0.1 keV), while the stored Q's differ from pynucastro's own nuclide masses
by up to 17–31 keV. On Q ~ 3–11 MeV that is 0.2–0.6% on the worst channels,
which is exactly the shape of the residual distribution above: tiny in the
median, 10⁻³-ish in the tail. The energy identity's residual is no longer an
unexplained number.

This does not devalue the check; it relocates it. **Ask of any green test what
would still be wrong if it passed** (Tier 1 §VIII.D): here, an integration error
would still be wrong, and this test would not see it. That is what
`identity_resid`, the Radau cross-check, and the label handshake are for.

Two known gaps in the identity's coverage, both already on the register:

- **Neutrino losses.** Weak reactions emit neutrinos that free-stream out (Tier
  0 §0.4.2), so the energy *deposited* is less than Q. Whether the tabular
  weak Q-values used here are already net-of-neutrino is a per-source
  convention — Tier 1 §VIII.C.3's dropped-NU-column item.
- **Thermal Q(T).** `CLAUDE.md` specifies e_nuc = Σ Q_j(T)Φ_j with a
  *temperature-dependent* Q; the implementation uses the constant Q. Tier 1
  §VIII.E.2 flags it as specified-but-unimplemented, and the current gate
  cannot detect the difference precisely *because* of the algebraic collapse
  above.

---

## IV.8b ⚠ Wegscheider — the rate set is not globally consistent, measured

§IV.8 closed by saying the energy residual measures nuclear-data
self-consistency rather than dynamics. This section measures it — and the
measurement has consequences well beyond the energy gate.

### The condition

Detailed balance constrains rate constants *globally*, not just pairwise.
Around any cycle in the reaction graph the free-energy changes must sum to
zero, so the equilibrium constants must multiply to one. In this project's
linear algebra the statement is startlingly simple.

Q-values are mass-excess differences: Q_j = −Σ_i ν_{ij}Δ_i (§IV.8). Therefore
for **any** c in the right null space of ν — i.e. any cycle —

$$
\sum_j c_j Q_j \;=\; -\sum_j c_j\sum_i \nu_{ij}\Delta_i \;=\; -\sum_i \Delta_i(\nu c)_i \;=\; 0 .
$$

> **Wegscheider condition, linear-algebraic form: Q must lie in the row space of
> ν.** Equivalently, Q ⊥ null(ν). If it does not, no assignment of masses to
> nuclides reproduces the tabulated Q-values, the network has no globally
> consistent equilibrium, and κ acquires an irreducible floor.

This is a *free* consistency test on `Stoich.Q` — no rates, no temperatures, no
states. Nothing in the repo performs it.

### The measurement

Project Q onto rowspace(ν) via the SVD and take the residual. **[derived here]**:

```python
d = np.load("data/stoich/nu_mesa80.npz"); nu, Q = d["nu"], d["Q"]
w = d["weak_mask"].astype(bool)
U, S, Vt = np.linalg.svd(nu[:, ~w], full_matrices=False)
Vr = Vt[:(S > 1e-12 * S[0]).sum()]              # orthonormal basis of rowspace
r  = Q[~w] - Vr.T @ (Vr @ Q[~w])                # the Wegscheider residual
```

| | mesa_80 | mesa_151 |
|---|---|---|
| ‖resid‖, **weak columns only** | 1.8×10⁻¹⁴ MeV | 4.4×10⁻¹⁴ MeV |
| ‖resid‖, **strong/EM columns** | 1.31×10⁻² MeV | 1.98×10⁻² MeV |
| rms per strong column | 5.53×10⁻⁴ MeV | 5.39×10⁻⁴ MeV |
| max per strong column | 3.47×10⁻³ MeV | 3.57×10⁻³ MeV |
| strong columns with \|resid\| > 10⁻⁴ MeV | **331 / 561** | **972 / 1345** |
| Q quantised to 10⁻⁵ MeV | 94.1% | 92.1% |

And separately, comparing the stored Q against the *nuclide mass table*
directly (Q_pred = −m_u·νᵀA_nuc):

| | mesa_80 | mesa_151 |
|---|---|---|
| max \|Q_stored − Q_masstable\|, strong | **17.2 keV** | **30.6 keV** |
| max \|Q_stored − Q_masstable\|, weak | 1.1 keV | 1.1 keV |

### Reading it

**Three separate facts, and they are not the same fact.**

1. **The weak sector is exactly consistent** (10⁻¹⁴ = machine precision). Its
   Q-values come from a single coherent table. Good news, and a control: it
   shows the test is not measuring an artefact of the method.

2. **The strong sector is not consistent with any mass table whatsoever.** The
   rowspace projection *finds the best-fit mass vector*; the residual is what
   survives that fit. rms 0.55 keV, max 3.5 keV, and it is not round-off: the
   tabulated Q's are quantised at 10⁻⁵ MeV = 10 eV, so the residual is ~50–350
   quanta. The top offenders are unmistakable —

   ```
   C12_Ne20_to_p_P31      Q =  10.1040   resid = −3.47e−3 MeV
   C12_C12_to_He4_Ne20    Q =   4.6210   resid = +2.97e−3
   He4_Ne21_to_Mg25       Q =   9.8820   resid = −2.84e−3
   ```

   — REACLIB entries whose Q is quoted to only 3–4 decimals, i.e. older or
   experimentally-derived Q-values carried alongside Q's computed from a modern
   mass evaluation. (Forward and reverse of a pair show equal and opposite
   residuals, which is a useful internal check on the method: they share |Q| and
   have opposite ν.)

3. **The stored Q's differ from pynucastro's own nuclide masses by up to 31
   keV.** pynucastro's `Rate._set_q()` computes Q from `Nucleus.A_nuc`, but
   `ReacLibRate` overrides it with the library's tabulated Q. So the export
   carries REACLIB's Q, and the *mass excesses* used elsewhere (NSE in §III.3,
   the composition-route energy in §IV.8) are a different data source.

### Why this matters, quantitatively

**(a) It explains §IV.8's residual, and retires it as a mystery.** The energy
identity compares Σ_j Q_jΦ_j (REACLIB Q) against −Σ_i Δ_iΔY_i (nuclide masses).
Since the two routes collapse algebraically given ΔY = νΦ, the measured residual
*is* fact (3): 17–31 keV on Q ~ 3–11 MeV is 0.2–0.6% on the worst channels, and
the measured energy residual was median 6×10⁻⁶…2.5×10⁻⁵ with max 8.7×10⁻⁴ —
exactly what you expect when the bad channels are rare and low-flux. §IV.8 said
"the residual measures nuclear-data self-consistency"; this section measures it.

**(b) It predicts a κ floor.** A Q error δQ shifts f⁻/f⁺ ∝ exp(−Q/kT) by a
relative ε = δQ/kT, and §II.4(a) turns that into κ ≈ ε/2. At T₉ = 5,
kT = 0.431 MeV:

$$
\kappa_{\mathrm{floor}} \;\approx\; \frac{\delta Q}{2kT}
\;=\; \begin{cases} 6.4\times10^{-4} & \delta Q = 0.55\ \text{keV (rms)}\\
4.0\times10^{-3} & \delta Q = 3.5\ \text{keV (max)}\end{cases}\qquad\text{[derived here]}
$$

Now compare with **[RESULTS]** 2026-07-10: **κ at NSE for stock MESA r23.05.1
has median 3.6×10⁻³ / 3.3×10⁻³**, recorded there as attributable to "own
pf-interpolation + winvn provenance" — i.e. attributed loosely and not
quantified. The predicted range brackets the measured value.

**This is a hypothesis with a decisive test**, and the test is cheap: run the
rowspace projection on MESA's *own* Q set against MESA's winvn masses. If the
residual is ~3–7 keV, the stock-MESA κ floor is explained, and the corollary
follows immediately — **that floor is irreducible without fixing the mass data,
so no κ threshold below ~10⁻² is measuring physics in MESA-derived quantities.**
Given that §III.12's κ-balance census reports "strong pairs with κ < 10⁻³:
≤ 0.4% of carrying pairs", knowing whether 10⁻³ is above or below the data floor
is not optional.

Note this is *not* a problem with the project's own engine: `DerivedRate`
constructs reverses from the forward using consistent nuclide data, which is why
the engine's κ at NSE collapses to 2.6×10⁻¹² (**[RESULTS]** 2026-07-10). The
inconsistency does not vanish — it is *relocated* into the forward-rate-vs-Q
mismatch, where nothing currently looks for it.

**(c) It is the general form of a bug the project already found.**
**[RESULTS]** 2026-07-10 records, for MESA 24.08.1, "a subset of (n,α)/(p,α)
pairs κ ~ 0.75 that are clean in stock — consistent with its newer REACLIB
snapshot carrying independently-fitted non-DB-linked pair members; open
observation". That is a Wegscheider violation, unnamed. The cycle test above
is the instrument that would have found it structurally rather than by
noticing an odd κ tail, and would find the next one.

Open (register: **R-06**). A two-line test that retires one open observation,
quantifies §IV.8, and may put a floor under a threshold the kill-test depends
on.

---

## IV.9 The cost wall, diagnosed

`scripts/step6_integrate_check.py` measured feasibility on stratified Sobol
states (36 / 24, one integration to 10² s serving all nine measured dts, 11
workers, 4800 s deadline; censored states are lower bounds). **[RESULTS]**
2026-07-12:

| | mesa_80 | mesa_151 |
|---|---|---|
| median wall per state | ≥ 383 s | ≥ 1519 s |
| censored at 4800 s | 17/36 | 10/24 |
| … and every censored state is | T₉ ≥ 5 | T₉ ≥ 5 |
| throughput | ≤ 9.4 states/h/core | ≤ 2.4 |
| **full-corpus cost** | **≥ 110,647 core-h** | **≥ 439,302 core-h** |
| stratified subset (10³–10⁴ states, T₉ < 5) | ≈ 4–40 core-days | feasible |

**Full-corpus local Φ supervision is infeasible; stratified subsets are not.**

And the diagnosis is specific rather than "it's slow": the deliberately
neglected tabular-EC ρYₑ Jacobian chain (§IV.5) dominates the weak-drift phase
at T₉ ≥ 5. The physical picture is clean — once the strong sector reaches its
attractor, all that is left is slow weak-driven Yₑ drift through the tabular EC
rates, whose λ depends on ρYₑ, i.e. on Y, through a chain the Jacobian does not
see. The quasi-Newton iteration then converges poorly exactly in the phase that
takes the most wall time. The ADR-0006 contingency (add the Yₑ-chain term) is
the named unlock.

**Label agreement, where it could be measured:**

| stratum | median species-fraction in the handshake band |
|---|---|
| QSE window [3.3, 5.0) | 0.74–0.99 (best 0.99 at [4.0, 5.0), dt = 10⁻¹ s) |
| cold strata | 0.62–0.90 |
| T₉ ≥ 5 | unmeasurable within deadline **and** label-pathological |

So: **local Φ-label generation is proven for T₉ < 5.** The T₉ ≥ 5 gap is a
double blocker — cost *and* the fact that the shipped labels there carry the
Appendix-B bug (Tier 3, S13), so agreement would be uninterpretable anyway.

**④ SEE:** notebook `11-integrator-and-handoff.ipynb` — Fig 1 conservation is
exact by construction (not by tolerance), Fig 2 the cost wall, which is why the
node is marked PARTIAL. The notebook deliberately gates the `compile_network`
cells; anything touching it is multi-minute.

---

## IV.10 Code and oracles

**Read:** `fluxes/integrate.py` (265 lines). `StatePoint` first — it hoists
everything Y-independent for one (T, ρ): the ReacLib set sums, the pf
corrections, `prefactor·ρ^dens_exp`. Then `_lam` (what must be re-evaluated per
call: screening, tabular ρYₑ), `gross_rates`, `rate_jacobian`,
`integrate_state`.

The hoisting is the reason this is usable at all: at constant (T, ρ) the
expensive part of Tier 1's machinery is evaluated **once**, and the RHS is
reduced to a screening call, a tabular interpolation, and a product loop.

**Oracles** (`tests/test_integrate.py`):

| test | pins |
|---|---|
| `test_rhs_matches_engine` | the integrator's R **is** the engine's R (≤10⁻¹² rel) — no second implementation of the physics |
| `test_jacobian_vs_finite_differences_unscreened` | §IV.5's product rule |
| `test_neglected_screening_chain_is_subdominant` | the ADR-0006 approximation, quantified |
| `test_success_and_identity_by_construction` | ΔY = νΦ exactly |
| `test_solver_consistency_residual` | `identity_resid` at machine precision |
| `test_conservation_by_construction` | Cν = 0 propagated through the solve |
| `test_something_burned` | the anti-vacuity test — the integration actually did something |
| `test_energy_identity` | §IV.8 |
| `test_t_eval_multiple_dts` | one integration serves all nine label dts |
| `test_vs_shipped_labels` | the external comparison |

`test_something_burned` deserves a note: it is the guard against a test suite
that passes on a null integration. Every identity above holds trivially for
Φ = 0. Without it, a bug that made the RHS return zeros would pass eight of the
nine tests.

---

## IV.11 Self-check for S10

1. Write J = νD and explain why the stiffness ratio here exceeds 10¹⁴, citing
   the measurement.
2. Backward Euler and the trapezoidal rule are both A-stable. Why is only one
   of them acceptable here?
3. Why is Φ carried as a state variable rather than reconstructed from ΔY
   afterwards? Give the dimension of the ambiguity.
4. Why does `rate_jacobian` build products with the differentiated factor
   removed instead of dividing?
5. `integrate_state` returns Y0 + νΔΦ rather than the solver's Y. What is
   gained, and what does `identity_resid` then measure?
6. Show that Σ_j Q_jΦ_j = −Σ_i Δ_i ΔY_i identically. What, therefore, does the
   1% energy gate actually test?
7. The augmented Newton matrix is block lower triangular. What does that imply
   about the cost of carrying Φ, and does the current implementation exploit it?
8. Full-corpus Φ labels are infeasible. What is the measured cause, and what is
   the named unlock?

---

# Part V — Executable policy, and the measurement discipline it does not encode

## V.1 The invariants encoded in code that refuses

Tier 1's Part VII made the point that this repo encodes invariants as code that
*refuses* rather than as comments that ask. Tier 2's contribution to that
pattern is different in kind from Tier 1's: where Tier 1's guards check a
*configuration* (is the pf gate satisfied? is this screening prescription
allowed?), Tier 2's guards are mostly **structural** — they make the wrong thing
unrepresentable rather than detectable.

| mechanism | where | invariant | style |
|---|---|---|---|
| `build_stoich`'s five `raise ValueError`s naming the offending reaction | `graph/stoich.py` | column-wise baryon/charge/ledger closure | fail-loud at build |
| `C @ nu_ext` residual `!= 0.0` abort | `graph/stoich.py` | #1 | fail-loud at build |
| ledger from `weak_type`, never from Z·ν | `graph/stoich.py` | non-tautological closure (§I.4) | **structural** |
| `if stoich.weak_mask[j]: continue` before pair lookup | `fluxes/compile.py::_pair_maps` | #2, upstream form | **structural** |
| `(delta_r < eps) & ~weak_mask` | `qse/diagnostics.py::eligible_mask` | #2 | **structural** |
| `guidry_masks` routes *only* through `eligible_mask` | `killtest/active_set.py` | #2, downstream | **structural** |
| P acts on the extended vector | `graph/projector.py` | #3 (§I.9) | **structural** |
| rank check on diag(R) | `graph/projector.py::build_projector` | C independence | fail-loud |
| `group_mass` outside (0, 1) → raise | `qse/solver.py` | domain | fail-loud |
| `si28` not in group → raise | `qse/diagnostics.py::load_group_mask` | anchor contract | fail-loud |
| Y clipped at 0 **inside rate eval only** | `fluxes/integrate.py` | conservation not perturbed (§IV.2) | **structural** |
| returned Y := Y0 + νΔΦ | `fluxes/integrate.py` | #1 in the solver (§IV.6) | **structural** |
| `stoich_export` fixture regenerates a missing npz | `tests/conftest.py` | **the gate never skips** | policy |
| `caption()` raises if a figure cites no measured row | `notebooks/phase0/nbsupport.py` | provenance (Tier 0 §VII.1) | fail-loud |
| κ helper raises unless the convention is declared `UNSCREENED`/`SCREENED` | `nbsupport.py::kappa_hist_by_stratum` | the two-κ rule | fail-loud |
| `flux_store` raises instead of `mkdir`-ing a typo | `nbsupport.py` | no silent empty runs | fail-loud |
| PostToolUse hook runs `tests/test_conservation.py` on any edit under `graph/` | `.claude/hooks/conservation_gate.sh` | #1 | policy |

**The three worth internalising as *habits*, not facts:**

1. **Make it unrepresentable before you make it detectable.** `eligible_mask`
   could have been a function that checks, after the fact, whether a mask
   contains weak columns. Instead it is the only way to build a mask, and it
   takes `weak_mask` as a required argument. There is no code path that
   produces an invalid mask, so there is no code path that needs checking.
2. **A gate that can skip is not a gate.** `conftest.py`'s docstring says it
   outright. Regenerating a 7-second artifact is cheaper than the class of bug
   where the blocking test silently no-ops in CI for a month.
3. **Refuse ambiguous provenance at the point of display.** The notebook helper
   that will not plot a κ histogram without a declared convention is doing more
   work than a comment ever would — because the failure mode it prevents
   (comparing screened κ against an unscreened threshold) produces a plot that
   looks entirely reasonable.

---

---

The rest of this part is the mirror image: **three pieces of measurement
discipline the repo does *not* encode**, and in two cases has never applied. They
sit here rather than in the register because each is a substantive statement
about what the tier's own numbers can support — §V.2 about the *measure* the
error statistics are taken over, §V.3 about the *independence* the sample sizes
assume, §V.4 about what the verification suite establishes and what it merely
agrees with. Two of the three come with a measurement.

## V.2 The sampling measure on the regime box

Tier 0 §III.2 derives the regime box edge by edge and every edge is defensible.
Tier 0 §III.4 covers Sobol sampling theory, and §III.9 covers stratification.
**What no node asks is whether the uniform measure on that box is the right
measure** — i.e. whether the density of training states matches the density of
states a star actually occupies.

§II.9 already established a *compositional* mismatch (random Sobol compositions
are nucleon-loaded and nowhere near equilibrium; the cancellation structure
lives only on relaxed states). This is the *thermodynamic* analogue, on the
(T, ρ) axes, and it is a different measurement.

### The measurement

Using the shipped 20 M⊙ MESA models (`data/zenodo/.../MESA_models/20M_mesa{80,151}/`)
— the final profile, which gives the *spatial* (logT, logRho) locus of the star
at one instant, and `history_to_cc.data`, which gives the *central* track
through time. **[derived here]**:

| | 20M_mesa80 | 20M_mesa151 |
|---|---|---|
| profile zones inside the full regime box | 297 / 1587 (18.7%) | 249 / 1621 (15.4%) |
| in-box logT span | 9.495 – 9.778 | 9.541 – 9.750 |
| in-box logRho span | 7.002 – 8.914 | 7.005 – 8.687 |
| best-fit locus | logρ = 7.86 logT − 67.95 | logρ = 8.41 logT − 73.47 |
| **residual about the locus** | **0.182 dex** (max 0.404) | **0.127 dex** (max 0.285) |
| central history, in-box models | 917 / 917 | — |
| central-track locus | logρ = 6.41 logT − 53.64, resid **0.117 dex** | — |

And the union — profiles plus histories, both models, 1,795 in-box points —
against a grid over the box:

| tolerance | fraction of the (logT, logRho) box within that distance of **any** visited point |
|---|---|
| 0.1 dex | **0.352** |
| 0.2 dex | 0.623 |
| 0.3 dex | 0.816 |

### Reading it honestly

Two statements, and only the first is strong:

1. **The occupation is locally one-dimensional.** At any instant, and along the
   central track through time, the star lies within ~0.12–0.18 dex of a *line*
   in (logT, logRho). It is a curve with thickness, not an area. The Sobol grid
   samples the area uniformly.
2. **The box is not mostly empty, but it is far from uniformly occupied.** About
   two-thirds of the box lies more than 0.1 dex from anything this progenitor
   visits; at 0.3 dex tolerance, coverage is 82%. So "most of the box is
   unphysical" would be an overstatement — but "the training density is uniform
   where the physical density is concentrated on a band" is measured and true.

**And the correct caveat, which changes the recommendation.** This is *one*
progenitor (20 M⊙), one final profile, one central history. Different progenitor
masses sweep different loci, and the box is presumably sized as a *union* over
progenitors — which is a legitimate design choice for a general-purpose
emulator. So the finding is **not** "the box is too big". It is:

> **Nobody has measured the induced density.** The box's *support* is
> defensible; its *measure* has never been compared with the measure the
> deployment distribution actually carries, and the two are measurably
> different by at least a factor of a few in the region that matters.

That matters for three concrete things, none of which is currently instrumented:

- **Where accuracy is bought.** Uniform sampling spends the same modelling
  capacity on a corner of the box the star crosses briefly as on the band where
  it spends its life. A tighter emulator on the band would be worth more than a
  uniformly tighter one.
- **What the reported error statistics mean.** A p99 error over the uniform box
  is not the p99 error a star would experience. This is the same category of
  error as §V.3 — the *reference measure* of a summary statistic is
  unstated.
- **It sharpens the Sobol→real-MESA gate.** `CLAUDE.md` already has the right
  instrument ("retrain with trajectory-aware sampling if real-track 99th-pct Yₑ
  error > 3× the Sobol-measured value"). This measurement says what the gate is
  *for*, and predicts it will fire: the two measures differ, so the two error
  statistics should too.

Open (register: **R-07**) — a density comparison on files already in
`data/zenodo/`, to be run across the progenitor set rather than one model before
any conclusion is drawn.

---

## V.3 ⚠ Cluster-robust inference — the effective sample size is ~300, not 657,000

### The problem

`RESULTS.md` reports statistics with impressive-looking sample sizes:

> Spearman(log κ unscr, log δ_r) = **+0.491 / +0.498** over **657k / 1.59M**
> carrying-pair samples … (**[RESULTS]** 2026-07-12)

and, in the same block, the provenance of those samples:

> pre-terminal rows of 20 shipped + 209 rerun trajectories per net (**4,693
> rows/net** sampled ≤ 24/trajectory)

Put those together. The 657,000 "samples" are (row × reaction-pair) cells drawn
from **4,693 rows**, which are themselves drawn from **229 trajectories**. Both
multiplications are *within-cluster*: consecutive rows of one trajectory are
nearly the same physical state, and reaction pairs within one row share that
state entirely. **Neither multiplication adds independent information.**

This is the classic clustered-sampling error, and it is not a pedantic one — it
inflates apparent precision by the *design effect*

$$
\text{deff} \;=\; 1 + (\bar m - 1)\,\rho_{\mathrm{ICC}}, \qquad
n_{\mathrm{eff}} \;=\; \frac{n}{\text{deff}},
$$

with ρ_ICC the intraclass correlation and m̄ the cluster size.

### The measurement

ICC computed by one-way random effects over 80 shipped mesa_80 trajectories,
26 pre-stall rows each, for four per-row scalars of the kind `RESULTS.md`
aggregates. **[derived here]**:

| per-row quantity | ICC | m̄ | nominal n | design effect | **n_eff** |
|---|---|---|---|---|---|
| Yₑ | 0.630 | 26.0 | 2079 | 16.7 | **124** |
| Si-group mass fraction | 0.417 | 26.0 | 2079 | 11.4 | **182** |
| # species above 10⁻³ | 0.219 | 26.0 | 2079 | 6.5 | **322** |
| log₁₀ X(²⁸Si) | 0.704 | 26.0 | 2079 | 18.6 | **112** |

```python
def icc(vals):                      # vals: one 1-D array per trajectory
    k = len(vals); ns = np.array([len(v) for v in vals]); m = ns.mean()
    g = np.concatenate(vals).mean()
    msb = sum(len(v) * (v.mean() - g)**2 for v in vals) / (k - 1)
    msw = sum(((v - v.mean())**2).sum() for v in vals) / (ns.sum() - k)
    return (msb - msw) / (msb + (m - 1) * msw)
```

**ICC of 0.22–0.70 at m̄ = 26 gives design effects of 6.5–18.6.** Applied to the
kill-test manifold (4,693 rows over 229 trajectories, so m̄ ≈ 20.5 and
deff = 1 + 19.5ρ ranges 5.3–14.7), the row-level effective sample size is
**≈ 320–890, and ≈ 320 for the Yₑ-like quantities that matter here** — and the
reaction axis, which takes 4,693 rows to 657,000 cells, adds no independent
physical systems at all.

**So the honest denominator for the κ↔δ correlation is a few hundred, not
657,000 — an overstatement of roughly 10³ in nominal n, i.e. ~30× in standard
error.**

### What this does and does not invalidate

Being precise matters here, because the temptation is to over-correct.

**Unaffected:**
- **Point estimates.** Clustering biases *precision*, not (much) the estimate.
  Spearman ≈ +0.49 is probably about right.
- **Degenerate results.** "Maskable columns: median 0 at every ε, p90 = 0"
  (**[RESULTS]** 2026-07-12) is a statement about a distribution that is
  identically zero. No sample size argument touches it.
- **Structural results.** κ = 1.0 exactly on all weak columns is an identity
  (§II.5), not a statistic.

**Affected:**
- **Every p-value and confidence interval.** "p ≈ 0" on 657k clustered samples
  is not evidence of anything. The correct statement needs a trajectory-level
  bootstrap.
- **Concentration statistics with no reported spread.** "top-20 carry 0.88",
  "top-5 = 0.96 / 0.75", the bridge shares (0.20, 0.13, 0.11 …). These are
  *rankings and shares* whose between-trajectory variability is never reported.
  With n_eff ≈ 300 the ranking of #4 vs #7 in a 251-item list is likely not
  resolvable, and the current output gives no way to tell.
- **The split verdict.** The 95% coverage gate's most consequential row —
  worst-dominant-isotope coverage falling to 0.0022–0.166 across [4.0, 6.3)
  strata — is a *tail* statistic (a per-row minimum) computed within strata,
  where the effective n is smaller still. A tail statistic at n_eff ~ tens is a
  different object from one at n ~ 10⁵.

### The fix, which is cheap

**Bootstrap over trajectories, not rows.** Resample the 229 trajectories with
replacement, recompute the statistic on each resample, and report the
percentile interval. That is the correct unit of independence — one trajectory
is one physical system integrated from one initial condition — and it
automatically handles both levels of clustering without needing ICC estimates
at all. It is perhaps thirty lines in `killtest/`, and it converts every
headline number from a point estimate into a point estimate with an honest
interval.

Related and equally cheap: report **m̄ and the number of clusters** alongside
every n. `RESULTS.md` already records both, in different rows of the same
block; joining them at the point of reporting would have made this visible.

Open (register: **R-08**). It does not overturn any verdict I can see, but it
means several published numbers carry no uncertainty statement at all, and one
of them (the split verdict's tail row) is the basis of a design decision.

---

## V.4 Verification practice — three standard steps that are absent

The repo's testing culture is unusually good (layered oracles, external
cross-checks, executable policy). Three standard computational-science
verification steps are nonetheless missing, and they are missing in a way that
is characteristic: the tests verify *agreement*, rarely *order*.

**(a) Convergence-order verification of the integrator.** `test_integrate.py`
checks BDF ≡ Radau ≡ BDF(rtol 10⁻¹⁰) to 5×10⁻⁸ on the stiffest test state
(**[RESULTS]** 2026-07-12) — an agreement test. It never verifies that the error
decreases at the *expected rate* as rtol tightens. Two methods agreeing is
strong evidence neither is grossly wrong; a measured convergence order is
evidence the error estimator is trustworthy, which is a different claim and the
one that licenses running at rtol = 10⁻⁸ in production. Cost: one loop over rtol
on one state.

**(b) A manufactured solution.** The method of manufactured solutions —
construct a source term making a chosen analytic function an exact solution,
then verify the code reproduces it to the expected order — is the standard way
to verify a solver against *itself* with no reference implementation. Here it
would need a toy ν (one already exists: `test_conservation.py`'s Layer-1 network,
§I.13) and a synthetic rate law. This is the one verification technique that
does not require a second code, and the project's ground truth (MESA/bbq) is
known to carry a bug, so a reference-free check has real value.

**(c) Trivial baselines.** Tier 0 §III.2's caveat already observes that "at these
densities NSE is effectively established from ≈ 5 GK upward, so the top ~3 GK of
the box is *already* algebraic and the emulator is being trained on states it
does not strictly need to learn." The obvious experiment that follows is not
listed anywhere: **evaluate NSE-as-a-predictor as a baseline** across the box.
`qse/solver.py` already computes it, and it costs milliseconds. If NSE matches
the labels at T₉ ≥ 5 to within the Yₑ gate, then the honest framing of the
emulator's job is "T₉ < 5", and the strata where it is hardest to train
(§IV.9: T₉ ≥ 5 is unmeasurable *and* label-pathological) are also the strata
where it is least needed. Other near-free baselines in the same spirit:
persistence (ΔY = 0), and nearest-neighbour in the training set.

A baseline you can beat trivially is not interesting; a baseline you *cannot*
beat is the most valuable measurement in the project. Neither is currently
known.

Open (register: **R-15** for (a)/(b), **R-16** for (c)) — (c) is nearly free and
may substantially redefine the target domain.

---

# Part VI — The open register

**This is the single register for Tier 2.** Every open item lives here as one
row; the *content* — the derivation, the measurement, the argument — lives in
the section that owns it, and each row points there. Nothing in this part is
material you have to read to understand the tier; it is the index you come back
to when deciding what to work on.

Items promoted out of the two gap-audit passes carry their derivation in the
body (Parts 0–V). **R-24** and **R-25** are the two that have no natural home
section and are written out here. [Part VII](#part-vii--how-this-register-was-built-and-whether-it-is-finished)
records how the list was built and whether it is finished.

Cross-tier items stay in
[`tier1.md` §VIII](tier1.md#part-viii--open-prerequisites-what-is-still-not-covered);
where a row extends one of those, it says so.

## VI.1 The register

| ID | open item | derived in | cost | what closing it changes |
|---|---|---|---|---|
| **R-01** | κ > 0.1 has no derivation. Replace the threshold with an **entropy-weighted** active set: σ_j = 2k_B s_j κ_j artanh κ_j is flux-weighted and parameter-free — **on strong/EM pairs only**; σ diverges on weak columns (κ ≡ 1), which stay in the active set structurally | [§II.4b](#ii4b-entropy-production--a-derived-active-set-a-second-law-constraint-and-a-lyapunov-bound) | ~1 d | supplies the missing derivation for the strong-sector half of the project's central threshold and re-runs the split verdict on a principled basis |
| **R-02** | Effective dimension + Yₑ-variance measured only on shipped (bug-displaced, constant-(T,ρ)) trajectories | [§I.10b](#i10b-the-effective-dimension-of-the-reachable-set--and-where-yₑ-hides) | ~2 h | constrains every Tier-4 latent and loss decision before they are made |
| **R-03** | The flux head is unidentifiable in 528 / 1368 directions under a ΔY-only loss | [§IV.4b](#iv4b-the-flux-head-is-unidentifiable-under-a-δy-only-loss) | design | a second, independent cost of Target A; bears on the A-vs-B decision |
| **R-04** | Positivity is enforced nowhere. Add the diagnostic; decide whether to enforce | [§I.7b](#i7b-what-target-a-does-not-guarantee--positivity) | ~1 h | converts an unenforced physical constraint from unknown to measured |
| **R-05** | A learned φ̂ can violate the second law and pass every gate. Diagnostic → one-sided penalty → sign-from-affinity | [§II.4b](#ii4b-entropy-production--a-derived-active-set-a-second-law-constraint-and-a-lyapunov-bound) | ~1 h / design | a free correctness check on any trained model; possibly a hard constraint |
| **R-06** | Run the Wegscheider projection on **MESA's own** Q + winvn masses | [§IV.8b](#iv8b--wegscheider--the-rate-set-is-not-globally-consistent-measured) | ~1 h | tells you whether κ < 10⁻² is measurable at all in MESA-derived quantities |
| **R-07** | The induced (T, ρ) density has never been compared with the training measure, across progenitors | [§V.2](#v2-the-sampling-measure-on-the-regime-box) | ~3 h | tells you where accuracy is worth buying; predicts the Sobol→real gate |
| **R-08** | No kill-test statistic carries a cluster-robust interval. Bootstrap over **trajectories** | [§V.3](#v3--cluster-robust-inference--the-effective-sample-size-is-300-not-657000) | ~1 h | supplies the missing uncertainty on every headline number, incl. the split verdict |
| **R-09** | CRN / elementary-flux-mode literature uncited; the flux cone is the right admissibility object | [§I.2b](#i2b-the-same-object-in-another-literature--crn-theory-deficiency-and-the-flux-cone) | literature | closes a framing gap a systems-biology referee will find; extends `tier1.md` §VIII.C.7 |
| **R-10** | Time conditioning should use Δt/τ, not log Δt | [§II.7b](#ii7b-the-conditioning-variable-this-suggests--δtτ-not-log-δt) | design | a Tier-4 (S19) design input, wanted before S19 is built |
| **R-11** | The deployment coupling contract: what consumes the output; split error vs emulator error; imposed vs fed-back (T, ρ) | [§0.5b](#05b-deployment--what-consumes-the-output-and-what-speedup-is-achievable) | experiment | could relax or justify the per-step gate; extends `tier1.md` §VIII.E.6 / §VIII.C.4 |
| **R-12** | No target fallback rate. f_max = 1/S_target; the OOD detector sits on the critical path | [§0.5b](#05b-deployment--what-consumes-the-output-and-what-speedup-is-achievable) | ~1 h | turns S22's unspecified gate into a number; rules out expensive UQ |
| **R-13** | The **Helmholtz** free energy is a Lyapunov function of the strong/EM sector at constant (T, ρ); a second-law-consistent emulator cannot diverge. Bounds the fast sector, **not** Yₑ drift — the weak sector is open (neutrinos leave) | [§II.4b](#ii4b-entropy-production--a-derived-active-set-a-second-law-constraint-and-a-lyapunov-bound) | design | a *structural* rollout-stability guarantee rather than a statistical one (S20) |
| **R-14** | dM(⁵⁶Ni)/dYₑ and d(explodability)/dYₑ have never been assembled | [§0.3.5](#035-the-output-end--and-the-derivative-nobody-has-assembled) | ~1 d | justifies — or relaxes by orders — the project's most expensive requirement |
| **R-15** | No convergence-order verification, no manufactured solution | [§V.4](#v4-verification-practice--three-standard-steps-that-are-absent) | ~2 h | licenses running the integrator at rtol = 10⁻⁸ in production |
| **R-16** | NSE-as-a-predictor (and persistence, nearest-neighbour) never run as baselines | [§V.4](#v4-verification-practice--three-standard-steps-that-are-absent) | ~1 h | may redefine the emulator's real domain to T₉ < 5 |
| **R-17** | The projector's metric is unweighted — orthogonal P is the *minimum-Euclidean* correction, which is a choice nobody recorded | [§I.8](#i8-the-target-b-projector-derived-twice) | ~1 h | matters only if Target B is adopted; blocking then |
| **R-18** | The r_QSE plateau test may be measuring a (Z, N)-linear fit residual rather than cluster departure | [§III.10](#iii10-the-two-departure-diagnostics--and-they-are-not-the-same) | ~3 h | a published negative verdict rests on a diagnostic whose null distribution is unknown |
| **R-19** | K = ⌈radius⌉ + 2 uses radius where node-level output makes eccentricity the honest base | [§I.11](#i11-the-bipartite-graph-the-radius-and-k) | ~0 | the number is right for *this* graph; the formula is not general |
| **R-20** | The augmented Newton solve does not exploit block triangularity | [§IV.5](#iv5-ry-by-the-product-rule) | ~1 d | a cost-wall candidate independent of the ADR-0006 Jacobian contingency |
| **R-21** | The rollout accumulation slope is unmeasured, so the 3×10⁻⁶ gate is conditional | [§0.3.4](#034-the-error-budget-this-implies) | Tier 4 | the project's most load-bearing number; slope ½ would relax it to ~5×10⁻⁵ |
| **R-22** | Check that no document frames Target A vs B as an *expressivity* difference | [§I.10](#i10--target-a-and-target-b-reach-the-same-set) | ~1 h | documentation consistency; a `referee` pass item |
| **R-23** | The energy gate cannot detect an integration error (the two routes collapse algebraically) | [§IV.8](#iv8--the-energy-identity-is-a-data-check-not-a-dynamics-check) | ~0 | documentation; also why the Q(T) gap is currently unmeasurable |
| **R-24** | Learning-theory prerequisites: operator learning, the *measured* regime shift, rollout accumulation, OOD economics | §VI.2 below | Tier 4 | — |
| **R-25** | Shelf life: what a rate-library or MESA version bump does to a trained emulator | §VI.2 below | ADR | — |

## VI.2 The two items with no home section

### R-24 — Learning-theory prerequisites

Tier-4 material; the architecture side is sketched in `tier1.md` §VIII.E.1.
What that sketch does *not* cover, and what belongs in a Tier-4 Part 0
analogous to this file's:

- **What kind of object is being learned.** A one-step flow map
  Y ↦ Y + ΔY(Y, T, ρ, Δt) is a *parameterised family of operators*, not a
  function. The neural-operator framing (discretisation invariance, resolution
  independence) has vocabulary and results the project does not use, and it is
  the natural setting for generalising over 8 decades of Δt (S19, and **R-10**).
- **Distribution shift, which is already measured.** §II.9 established that
  training states (random Sobol compositions, κ ≈ 1, *relaxing*) and deployment
  states (relaxed, *on* the QSE manifold) are different distributions, and
  §III.9 gave the dynamical reason: they are different **functions** — relaxation
  onto the slow manifold versus motion along it. This is a change of regime, not
  a covariate shift, and no architecture fixes it. `CLAUDE.md`'s Sobol→real-MESA
  gate is the right instrument; §III.9 is the theory of why it will fire. See
  also **R-07** for the thermodynamic half of the same mismatch.
- **Error accumulation under autoregressive rollout** — the trichotomy of Tier 0
  §IV.3, slope still unmeasured (**R-21**).
- **Extrapolation, OOD detection, and the fallback gate** (S22) — whose *cost
  model* is **R-12** and whose stability guarantee could be **R-13**.

### R-25 — Shelf life under library and code drift

An emulator trained against a frozen snapshot of REACLIB + MESA r23.05.1 is a
function of that snapshot, and the project has already observed the snapshot
moving:

- **[RESULTS]** 2026-07-10 records MESA 24.08.1 giving materially different
  reverse rates from stock r23.05.1 for a subset of (n,α)/(p,α) pairs (κ ~ 0.75
  where stock is clean) — the observation **R-06**'s test is designed to
  explain;
- Tier 3's label pathology is a MESA *bug* that a later version presumably
  fixes, so the training labels are keyed to a specific broken version;
- weak-rate table families get superseded, and the FFN→LMP shift is precisely
  the number the whole accuracy budget is anchored to (§0.3.4).

Three unasked questions: **(i)** does a library update invalidate a trained
emulator, or can it be corrected? (Φ depends on rates nonlinearly through the
trajectory, so probably not — which makes retraining a *recurring* cost that
belongs in §0.5b's economics.) **(ii)** What is versioned well enough to
reproduce a training set *forward*, given a future library? The repo is
exemplary about backward provenance and silent about this. **(iii)** Is the
sensitivity measurable in advance — i.e. `tier1.md` §VIII.C.1's
rate-uncertainty propagation, which would tell you *which* updates matter.

Not a physics gap; a **product** gap, and the kind that surfaces after the
science is done and is expensive then. Worth an ADR rather than a measurement.

## VI.3 Ranked

If only a few of these get done, these in this order:

| rank | ID | item | cost | what it changes |
|---|---|---|---|---|
| 1 | **R-06** | Wegscheider projection on MESA's own Q + winvn masses | ~1 h | whether κ < 10⁻² is measurable at all in MESA-derived quantities — the kill-test depends on it |
| 2 | **R-08** | trajectory-level bootstrap on the kill-test statistics | ~1 h | supplies the missing uncertainty on every headline number, including the split verdict |
| 3 | **R-16** | NSE-as-a-predictor baseline across the box | ~1 h | may redefine the emulator's target domain to T₉ < 5 |
| 4 | **R-02** | repeat PCA + Yₑ-variance on the clean reruns | ~2 h | constrains every Tier-4 latent and loss decision |
| 5 | **R-04** | positivity diagnostic on any predicted update | ~1 h | converts an unenforced constraint from unknown to measured |
| 6 | **R-07** | induced-density comparison across the progenitor set | ~3 h | tells you where accuracy is worth buying; predicts the Sobol→real gate |
| 7 | **R-01** | entropy-weighted active set | ~1 d | supplies the missing derivation for κ > 0.1 and re-runs the split verdict |
| 8 | **R-14** | assemble dM_Ni/dYₑ from the literature | ~1 d | justifies (or relaxes) the project's most expensive requirement |

Ranks 1–6 are hours, on data already on disk. Nothing in the top six needs a
compute allocation, new labels, or a decision from anyone.

# Part VII — How this register was built, and whether it is finished

Part VI lists what is open. This part records **how the list was arrived at**,
which matters for exactly one reason: a register is only as trustworthy as the
search that produced it, and "I could not think of anything else" is not
evidence of coverage.

## VII.1 The method — two passes, and the axes each swept

The register was built by asking, twice and deliberately, a question that
studying the map does not ask:

> **What does this project need that no node in the map has a claim on?**

**Pass 1** swept — in hindsight almost exclusively — the *mathematical structure
of the network*: the algebra of ν, the thermodynamics of the fluxes, the
geometry of the state space. It produced **R-01 … R-09** and **R-13**, of which
three came with measurements runnable in an afternoon on artifacts already in
`data/`.

**Pass 2** was run *after* noticing that bias, and deliberately swept elsewhere:
**inference and statistics**, **sampling measure**, **cost and deployment
economics**, **dimensional analysis**, **training dynamics**, **the output end of
the motivation chain**, **verification practice**, and **provenance over time**.
It produced **R-10 … R-12**, **R-14 … R-16**, **R-25**, and — the one that
reaches furthest back into work already published — **R-08**.

Two things are worth extracting from that, because they generalise:

1. **A single audit sweeps one axis.** Pass 1 felt exhaustive while it was
   happening and was not. The correction is not to think harder; it is to
   enumerate axes *first* and then sweep each, which is what pass 2 did.
2. **The cheapest findings live in the areas nobody assigned a node to.** Five
   of the twenty-five items came with a measurement that took under three hours
   on data already on disk, and two of those changed how an existing result
   should be read (**R-06** → §IV.8 and the κ floor; **R-08** → every confidence
   interval in the kill-test block). Nothing in the *covered* territory was
   nearly that cheap, because it had already been worked.

## VII.2 Candidate axes that came back covered

The calibration data for §VII.3. These are things I went looking for across both
passes and found **already handled**, usually well and often with the caveat I
would have raised already attached:

| candidate | where it is covered |
|---|---|
| Operator splitting and its error | Tier 0 §IV.1 (the open half is **R-11**) |
| Catastrophic cancellation, conditioning | Tier 0 §V.1–V.2; the spine of §II.4 here |
| Thermal neutrino losses (pair, photo, plasmon, brems.) | Tier 0 §0.4.1, incl. the composition-independence and the units trap |
| Free-streaming and the Yₑ ratchet | Tier 0 §0.4.2 — with an explicit warning against the overstatement that free-streaming *drives* Yₑ down |
| The regime box's edges | Tier 0 §III.2, every edge derived, and the T-upper caveat already stated (§V.2 is about the *measure*, not the support) |
| Semigroup / composability across the nine Δt | Tier 0 §IV.3 |
| Sobol theory, stratification, leakage-safe splits, grid non-regenerability | Tier 0 §III.4–III.9 |
| Rate-uncertainty → Yₑ sensitivity | `tier1.md` §VIII.C.1 (**R-14** is its output-side mirror) |
| Solver-independent ground truth (SkyNet, WinNet) | `tier1.md` §VIII.E.3 |
| Gradients through the conservation map | `tier1.md` §VIII.E.5 — note **R-05**'s sign-from-affinity idea would add a discontinuity there; the two interact |
| Determinism, float32/float64, BLAS reduction order | `tier1.md` §VIII.E.4 |
| Network-reduction prior art | `tier1.md` §VIII.C.7 (**R-09** names the specific literature it should include) |
| Isomers, mass provenance, e⁺e⁻ pairs, Coulomb-corrected NSE | `tier1.md` §VIII.C.5, .6, .8, .9 |

## VII.3 Is the audit converging?

Worth asking explicitly, because "are there more gaps?" has no natural stopping
rule and the honest answer is evidence rather than a feeling.

| | pass 1 | pass 2 |
|---|---|---|
| axis swept | mathematical structure of the network | statistics, sampling measure, economics, dimensional analysis, training dynamics, motivation output, V&V, provenance |
| new items | 10 | 9 (+6 pre-existing, folded in) |
| with a measurement | 3 | 2 |
| **that changed how an existing result reads** | **2** (**R-06** → §IV.8 and the κ floor; **R-02** → Tier-4 latents) | **1** (**R-08** → every CI in `RESULTS.md`) |
| that reframed a design decision | 2 (**R-01** active set; **R-04** positivity) | 2 (**R-03** Target A's second cost; **R-16** the target domain) |
| candidate axes checked and found covered | not tracked | **13 of ~22** |

**The last row is the signal.** On pass 1 nearly everything I looked at was a
gap, because the axis had never been swept. On pass 2, most of what I looked at
was already covered — and covered *well*. That is what approaching coverage
looks like, and it is a far better stopping criterion than item count.

Three honest qualifications on "converging":

1. **Tier 3 and Tier 4 are unwritten**, so this audit is structurally blind to
   their own Part-0-style prerequisites. **R-10**, **R-13** and **R-24** are the
   visible edges of that — all Tier-4 material that became visible only because
   Tier 2 touches it. Expect a comparable yield when Tier 4 is written, on axes
   not visible from here.
2. **Every audit inherits its author's blind spots**, and the correction is not
   more passes by the same author. The axes I have not swept and cannot sweep
   well: experimental nuclear-physics practice (what a rate evaluator would find
   naive), stellar-evolution modelling practice (what a MESA developer would),
   and ML-systems practice at training scale. Those need the corresponding
   specialist, or the `referee` and `novelty-checker` subagents pointed
   deliberately at *methods* rather than at claims.
3. **Diminishing returns is not zero returns, and items are not equal-sized.**
   **R-08** is small in words and touches every statistic in `RESULTS.md`;
   **R-25** is a whole topic and touches nothing until release. Counting items is
   the wrong metric — §VI.3 ranks instead.

**Assessment: two further passes of this kind would find real but progressively
less consequential items, and the better use of the next unit of effort is
§VI.3's top six — all measurements on data that already exists, three of which
change how a published number should be read.**

# Where Tier 2 hands off

## What Tier 2 upgraded

| Statement, before | Now derived / measured |
|---|---|
| "conservation is by construction" | conserved quantities **are** the left null space of ν; left-nullity(ν) = 1 = span{A}, left-nullity(ν restricted to strong) = 2 = span{A, Z}, left-nullity(ν̃) = 3 = rowspace(C) exactly — so C is **complete** (§I.2.1) |
| "the tests demand 1e-12" | column sums are integer arithmetic in float64 and are exactly 0.0; only the random-φ sweep needs a tolerance, and its two-regime form (absolute at O(1), relative-to-gross at 1e-20) is what makes it non-vacuous (§I.2.2) |
| "Target B projects onto the constraint manifold" | P is the *minimum-Euclidean-correction* projector, derived from a Lagrangian; the QR form avoids squaring cond(C) ≈ 200 (§I.8) |
| "Target A and Target B are different designs" | **image(ν̃) = null(C)** — same reachable set. The trade is parameterisation (528-dim fibre), conditioning (cond ν̃ ≈ 41/55), and physical structure — not expressivity (§I.10) |
| "κ is the cancellation ratio" | κ = \|tanh(𝒜/2kT)\| — a monotone reparameterisation of the reaction affinity in units of kT; hence κ ≈ ε/2 for a relative rate error ε, 1/κ as the error-amplification factor, and the tanh form of the screening offset (§II.4) |
| "νR sums over reactions" | νR = Σ_{forward ∪ unpaired} νφ exactly, because ν_{·pair(j)} = −ν_{·j}; this is what licenses restricting every coverage statistic to net columns (§II.3) |
| "κ ≈ 1 on the training grid" | …because Sobol compositions are nucleon-loaded, affinities are ≫ kT, and κ saturates. The pass is **vacuous**, the cancellation structure lives on relaxed states only, and the dt=1e-6 grid handshake premise is void (§II.9) |
| "NSE is Saha" | logC_i derived term-by-term from the grand-canonical distribution, with B_i emerging from rest-mass bookkeeping; nuclei are classical (nλ³ ≈ 3e-7) while electrons are degenerate (§III.1–III.3) |
| "the solver falls back to bisection" | dYₑ/du_p\|_{ΣX=1} = W² Var_w(Z/A)/(kT S_N) > 0 — a proof, which also explains the 2 MeV damping cap and identifies the degenerate case (§III.6) |
| "QSE adds a cluster offset" | u_G is the log over-population of the group relative to NSE; median +4.3 MeV ⇒ ~10⁵× over-populated mid-burn; u_G = 0 recovers NSE and that is a test (§III.8) |
| "QSE reduces the network" | QSE **is** the slow manifold of a singular perturbation; stiffness ratio = 1/ε; the group mass is the slow coordinate; hence "stiffness and QSE are the same phenomenon" (§III.9) |
| "Φ labels come from the integrator" | …because they *have* to: νΦ = ΔY has a 528- (1368-) dimensional solution set, so Φ is not recoverable from the shipped labels at all (§IV.4) |
| "the energy check validates the flux route" | the two routes collapse algebraically given ΔY = νΦ; the residual measures **nuclear-data self-consistency**, not dynamics (§IV.8) — and §IV.8b measures that inconsistency: rms 0.55 keV, max 3.5 keV, 331/561 columns |
| "the rate set is detailed-balance consistent" | **pairwise yes, globally no.** Q ∉ rowspace(ν) for the strong sector, so no mass table reproduces the tabulated Q's; this is a Wegscheider violation and it predicts a κ data floor of 6e-4…4e-3 that brackets the measured stock-MESA κ floor (§IV.8b) |
| "κ > 0.1 selects the reactions that matter" | κ alone is flux-blind. σ_j = 2k_B s_j κ_j artanh κ_j is the entropy production, quadratic in κ and **linear in the gross flux** — an entropy-weighted active set is parameter-free and cannot admit a high-κ, no-flux column. It is defined on **strong/EM pairs only**: weak columns have κ ≡ 1 by construction, so σ diverges there and they must be admitted structurally, exactly as they are today (§II.4(d), §II.4b, §II.5) |
| "the composition is 80- or 151-dimensional" | the *visited* manifold has effective dimension ≈ 3.4 / 8.6 (participation ratio); 7 / 14 PCs carry 90% of Var(X). But the strong sector is Yₑ-neutral by §I.2.1, so **Yₑ hides in a long low-variance tail**: by k = 30, Var(X) is at 99.7%/98.1% and Var(Yₑ) stalls at 93.0%/95.3%, against a budget needing 1 − 6.5e-8 — variance-truncated compression is arithmetically excluded (§I.10b) |
| "657k samples" | ≈ 300 independent physical systems. Per-row quantities have ICC 0.22–0.70 across trajectories (design effect 6.5–18.6), so every p-value and CI in the kill-test block is unstated or wrong — point estimates and the empty-mask result survive (§V.3, **R-08**) |
| "the regime box is derived edge by edge" | its *support* is; its **measure** is not. The 20 M⊙ track sits within 0.12–0.18 dex of a *line*, and only 35% / 62% / 82% of the box lies within 0.1 / 0.2 / 0.3 dex of a visited point — the training density is uniform where the physical density is a band (§V.2, **R-07**) |
| "conservation-by-construction makes the update physical" | it makes it *conserving*. It does not make it **positive** (§I.7b) and it does not make it obey the **second law** — a learned φ̂ can point up the affinity gradient and pass every gate in `CLAUDE.md` (§II.4b). The second-law guard is available on strong/EM pairs; on the weak sector there is no detailed-balance affinity to guard with, so the blind spot is total exactly where Yₑ lives (§II.4b) |

## Threads that carry forward

- **To S11–S13 (bbq, trajectories, the label pathology):** §II.9's vacuous pass
  is *why* Step 6 needed a bbq rerun campaign at all — the kill-test cannot be
  run on the training grid. §III.12's displaced equilibria are the first
  symptom of the Appendix-B bug that S13 diagnoses; the NSE solver of §III is
  the instrument that measures the displacement (terminal T₉ ≥ 5 states sit
  8.6/9.0 dex from true NSE).
- **To S14 (the kill-test):** every measured quantity in the verdict comes from
  this tier — κ (§II), δ_r and `eligible_mask` (§III.10), `cond_s_active`
  (§I.2.1's rank-revealing definition), `carried_fractions` (§II.3's net-column
  identity). The verdict document is a reading of Tier 2 instruments on Tier 3
  data.
- **To S15 (the ML target):** §I.10 is the theorem that reframes the choice;
  §I.9 is the NuGNN failure mode in its exact form; §IV.4 is the label
  requirement that makes Target A expensive.
- **To Tier 4 (the emulator):** the flux head's output dimension is r = 607 /
  1518 (§I.1); the mask is per-column and structurally weak-excluded (§III.10);
  the conditioning from φ to dY is ~41–55 (§I.2.1); the 528-dimensional fibre is
  the reason a ΔY-only loss under-determines the head (§IV.4); and K ≈ 5 with a
  hub-dominated graph (§I.11) is the backbone's starting point.

## The three ideas to carry, if you carry nothing else

1. **Conservation is a rank statement.** Conserved quantities are the left null
   space of ν; the measurement says that space is exactly 3-dimensional in the
   extended system and exactly equals rowspace(C). Nothing is missing, nothing
   is redundant, and the whole thing is integer arithmetic — which is why the
   tests can assert `== 0.0` and why no loss term is involved.
2. **κ = |tanh(𝒜/2kT)|.** One identity that makes κ simultaneously a
   thermodynamic distance from equilibrium, a detailed-balance error gauge
   (κ ≈ ε/2), and a condition number (amplification 1/κ). If you can write it
   down cold, S8 reconstructs itself — and so does the screening offset, the
   v-flag floor, and the κ↔δ correlation.
3. **Stiffness, QSE, and cancellation are one phenomenon.** A stiff system has
   an attracting low-dimensional manifold; the manifold is the equilibrium; the
   fast directions off it are the near-balanced pairs whose gross fluxes cancel.
   Every difficulty in this project — the integrator's cost, the emulator's
   conditioning, the kill-test's premise, the training-grid distribution shift —
   is one face of that single structure.

## And one habit, from the negative results

Tier 1's closing habit was *ask of any green test what would still be wrong if
it passed.* Tier 2's is its mirror, and this tier produced three occasions to
use it:

> **Ask of any negative result whether the instrument could have produced it
> anyway.**

The vacuous κ pass (§II.9) — the instrument was fine, the *distribution* was
wrong. The empty maskable set (§III.12) — the instrument was fine, the
*reference* was displaced. The absent r_QSE plateau (§III.10, **R-18**) — here I
genuinely do not know, and the honest move was to write down the null
distribution I would need and log it rather than accept the verdict. A negative
result is a measurement of the instrument and the world jointly; the tier that
teaches that is worth its length.

## And one more, from building the register

Part VI exists because of an exercise that is distinct from studying, and does
not happen unless it is scheduled:

> **Ask what the *problem* needs, not what the plan lists.**

A study map is a plan for covering known territory. It is silent by construction
about what is not on it, and the silence looks exactly like coverage. Ripping
the map out and asking what the problem needs found twenty-five open items, five
of them measurable in an afternoon on data already on disk.

Part VII adds the refinement that makes it repeatable: **a single audit sweeps
one axis**, so enumerate axes first and sweep each. And the stopping rule is not
"I cannot think of more" — it is the ratio in §VII.3: **track how many candidate
axes come back already covered.** On the first pass almost none did; on the
second, thirteen of twenty-two. That number, not the item count, is what says
the audit is converging.
