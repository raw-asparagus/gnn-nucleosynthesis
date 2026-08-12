# Tier 0 — Substrate

**Complete deep dive: physical foundations, project motivation, S0 (species and
abundance algebra), S1 (the dataset), the modelling frame, and the numerical /
ML prerequisites.**

Everything needed before Tier 1 (reaction rates and detailed balance), in one
document.

---

## Status of this document

**Personal study material, not project spec.** Deliberately written without
reference to `docs/` — everything is derived from first principles or read off
the business code, configs, notebooks, and tests.

- Textbook physics and derivations here are **mine to check**, not citable
  project output.
- Measured project numbers quoted here originate in `RESULTS.md` with script +
  commit + data provenance. This file is **not** their source of truth; if a
  number here disagrees with `RESULTS.md`, `RESULTS.md` wins.
- **Literature audit 2026-08-12.** Every scholarly claim, constant, and
  derivation chain was verified against primary sources (arXiv TeX cached in
  `data/literature/`, AME2020/ENSDF/CODATA data pages) with all worked
  arithmetic recomputed in float64; errors found were corrected in place.
  Inline author–year citations point to the References section at the end;
  the claim-by-claim audit log, including every correction with its
  before/after and supporting source passage, is `study/tier0-audit.md`.

Notation follows the repo: unicode math, `⁵⁵Co` in prose, `co55` in
code-adjacent contexts, Yₑ / ν / φ / κ as in the codebase.

---

## How to study each node

```
  ① DERIVE      pen-and-paper: get the equation from physics before reading code
  ② READ        the module, top-to-bottom; its docstring states the contract
  ③ ORACLE      the test file — it encodes what "correct" means, numerically
  ④ SEE         the notebook figure — the measured behaviour on real data
```

Tests are the physics oracle here (project rule: *tests before implementation
for anything with a physics oracle*), and module docstrings state *contracts*
rather than describing code. So ③ is where correctness is pinned.

---

## Contents

| Part | Covers |
|---|---|
| [**0** — Physical foundations](#part-0--physical-foundations) | Plasma thermodynamics & EOS, statistical mechanics, nuclear structure & data, neutrinos, reaction nomenclature, Si-burning topology, the timescale hierarchy |
| [**I** — Why this project exists](#part-i--why-this-project-exists) | Stellar context, Yₑ and explodability, the cost problem, conservation, why a GNN |
| [**II** (S0) — Species & abundances](#part-ii-s0--species-abundances-and-the-nz-plane) | Y = X/A, Yₑ, the two networks, the bipartite graph |
| [**III** (S1) — The dataset](#part-iii-s1--the-dataset-as-a-physical-object) | Regime box, dt grid, Sobol design, identity, label noise, splits |
| [**IV** — The modelling frame](#part-iv--the-modelling-frame) | Operator splitting, one-zone & the reachable manifold, semigroup & rollout |
| [**V** — Numerical analysis](#part-v--numerical-analysis-prerequisites) | Catastrophic cancellation (= κ), conditioning, stiffness, floating point, Newton & globalization, ODE error control |
| [**VI** — ML framing & context](#part-vi--ml-prerequisites-and-context) | Operator learning, message passing, feature & loss design, MESA/bbq, prior art, observations |
| [**VII** — Working practice](#part-vii--working-practice-the-discipline-the-repo-runs-on) | Provenance labels, thresholds & instruments, ADR switch conditions, guards that refuse, non-regenerable artifacts |

<details>
<summary>Full section list</summary>

```
0.1  Thermodynamic state          0.1.1 pressure components · 0.1.2 box centre
                                  0.1.3 degeneracy · 0.1.4 Γ and screening
                                  0.1.5 the EC threshold · 0.1.6 self-check
0.2  Statistical mechanics        0.2.1 chemical potential · 0.2.2 partition functions
                                  0.2.3 detailed balance · 0.2.4 self-check
0.3  Nuclear structure & data     0.3.1 the mass-excess trap · 0.3.2 magic numbers
                                  0.3.3 where rates come from · 0.3.4 self-check
0.4  Neutrinos                    0.4.1 two channels · 0.4.2 free streaming
                                  0.4.3 ⟨E_ν⟩ · 0.4.4 self-check
0.5  Reaction nomenclature        channel notation · REACLIB chapters · why ΔN
0.6  Si-burning topology          the α ladder · two clusters & bridges · energy routes
0.7  The timescale hierarchy      τᵢ · the table · the separation that isn't
                                  0.7.1 self-check

I.1  The last day of a massive star        I.5  Why ML emulation
I.2  What determines explodability         I.6  What breaks without conservation
I.3  Why networks are the bottleneck       I.7  Why a graph neural network
I.4  Softwired networks                    I.8  Where conservation may live
                                           I.9  self-check

II.1 Nuclide bookkeeping                   II.5 The electron fraction Yₑ
II.2 Binding energy & the iron peak        II.6 The bipartite graph
II.3 Deriving Y = X/A                      II.7 Code walkthrough
II.4 Why Y and not X                       II.8 self-check

III.1 What one record is                   III.7  Leakage-safe splits
III.2 The regime box                       III.8  The missing rows
III.3 The dt grid                          III.9  Stratification
III.4 Sobol sampling                       III.10 Code reading order
III.5 Identity and state_id                III.11 self-check
III.6 Label noise, floors, censoring

IV.1 Operator splitting                    V.1 Catastrophic cancellation
IV.2 One-zone & the reachable manifold     V.2 Conditioning
IV.3 Semigroup & rollout error             V.3 Stiffness
IV.4 self-check                            V.4 Floating point
                                           V.5 Newton, damping, globalization
                                           V.6 ODE error control (rtol/atol)
                                           V.7 self-check

VI.1 What kind of learning problem         VI.5 Prior art in acceleration
VI.2 Message passing                       VI.6 Observational grounding
VI.3 Feature & loss design                 VI.7 self-check
VI.4 MESA and bbq

VII.1 Provenance labels                    VII.5 Non-regenerable artifacts
VII.2 Thresholds need instruments          VII.6 Notebooks explore, scripts produce
VII.3 ADR switch conditions                VII.7 self-check
VII.4 Guards that refuse
```

</details>

---

# Part 0 — Physical foundations

The physics that must be in place before "a nuclide has (Z,N)" and
"the network is dY/dt = νR" mean anything.

| § | Area | Why it is prerequisite, not optional |
|---|---|---|
| 0.1 | Plasma thermodynamics & EOS | Fixes the regime box, determines *which* screening prescription is valid, sets whether electron capture is even energetically allowed |
| 0.2 | Statistical mechanics | NSE, partition functions, and detailed balance are one framework; without it S3 and S9 are memorized formulae |
| 0.3 | Nuclear structure & data | Mass excess vs binding energy is a real sign trap; and most rates here are *theoretical*, not measured |
| 0.4 | Neutrino physics | Explains the acceleration of late burning, the net one-way Yₑ ratchet, and an open project item (⟨E_ν⟩) |

Numbers below are computed at box-centre conditions and are worth re-deriving
yourself — several justify configuration choices that otherwise look arbitrary.

## 0.1 The thermodynamic state of silicon-burning matter

### 0.1.1 The four pressure components

$$
P = P_{\mathrm{ion}} + P_{e} + P_{\mathrm{rad}} + P_{\mathrm{Coulomb}}
$$

- **Ions** — ideal gas, P_ion = n_i kT, n_i = ρN_A/Ā
- **Electrons** — degenerate, relativistic; the dominant term here
- **Radiation** — P_rad = aT⁴/3, a = 7.566×10⁻¹⁵ erg cm⁻³ K⁻⁴ (CODATA 2022)
- **Coulomb** — negative correction from ion–ion and ion–electron correlation;
  small for pressure, but *this is the term that becomes screening* (§0.1.4)

### 0.1.2 Worked example — box centre (ρ = 10⁸ g/cm³, T₉ = 4, Yₑ = 0.5, Ā ≈ 28)

$$
\begin{aligned}
n_e &= \rho N_A Y_e = 10^{8}\times 6.022\times10^{23}\times 0.5 = 3.01\times10^{31}\ \mathrm{cm^{-3}}\\
n_i &= \rho N_A/\bar{A} = 10^{8}\times 6.022\times10^{23}/28 = 2.15\times10^{30}\ \mathrm{cm^{-3}}\\
kT  &= 8.617\times10^{-2}\ \mathrm{MeV\,GK^{-1}}\times 4\ \mathrm{GK} = 0.345\ \mathrm{MeV}
\end{aligned}
$$

Fermi momentum from n_e (degenerate, T → 0 limit):

$$
\begin{aligned}
p_F c &= \hbar c\,(3\pi^2 n_e)^{1/3}, \qquad \hbar c = 1.9733\times10^{-11}\ \mathrm{MeV\,cm}\\
&= 1.9733\times10^{-11}\times(29.608\times 3.01\times10^{31})^{1/3}\\
&= 1.9733\times10^{-11}\times 9.62\times10^{10}\\
&= 1.90\ \mathrm{MeV}
\end{aligned}
$$

Relativity parameter x = p_F c / m_e c² = 1.90 / 0.511 = **3.7** — relativistic.
Total Fermi energy including rest mass:

$$
E_F = \sqrt{p_F^2c^2 + m_e^2c^4} = \sqrt{3.60+0.26} = 1.97\ \mathrm{MeV}
$$

Pressures (ultra-relativistic degenerate approximation P_e ≈ ¼ n_e p_F c):

| Component | Value (erg/cm³) | Share |
|---|---|---|
| P_e | 2.3×10²⁵ | **~93%** |
| P_ion | 1.2×10²⁴ | ~5% |
| P_rad | 6.5×10²³ | ~3% |

**Electrons carry the pressure.** This is the quantitative content of §I.2 —
the core is an electron-degeneracy-supported object, so a composition variable
that changes n_e changes the structure directly.

### 0.1.3 Degeneracy across the box

Degeneracy is measured by E_F,kin/kT, with E_F,kin = E_F − m_ec²:

| ρ (g/cm³) | p_F c (MeV) | E_F,kin (MeV) | E_F,kin/kT at T₉=4 | Regime |
|---|---|---|---|---|
| 10⁷ | 0.88 | 0.51 | 1.5 | mildly degenerate |
| 10⁸ | 1.90 | 1.46 | 4.2 | degenerate |
| 10⁹ | 4.09 | 3.61 | 10.5 | strongly degenerate |

The box spans exactly the transition from "electrons barely notice each other"
to "electrons dominate everything" — not a coincidence, but the physically
interesting range.

### 0.1.4 The Coulomb coupling parameter Γ — and why chugunov_2007

Ion-sphere radius and coupling parameter:

$$
a_i = \left(\frac{3}{4\pi n_i}\right)^{1/3}, \qquad \Gamma = \frac{Z^2 e^2}{a_i kT}, \qquad e^2 = 1.44\times10^{-13}\ \mathrm{MeV\,cm}
$$

At ρ = 10⁸, T₉ = 4:

$$
a_i = \left(\frac{3}{4\pi\times 2.15\times10^{30}}\right)^{1/3} = 4.81\times10^{-11}\ \mathrm{cm}
$$

$$
\begin{aligned}
\text{Silicon }(Z=14):\quad \Gamma &= \frac{196\times 1.44\times10^{-13}}{4.81\times10^{-11}\times 0.345} = 1.7\\
\text{Iron }(Z=26):\quad \Gamma &= \frac{676\times 1.44\times10^{-13}}{6.05\times10^{-11}\times 0.345} = 4.7
\end{aligned}
$$

Now scale it across the box. Γ ∝ n_i^{1/3}/T ∝ ρ^{1/3}/T, so **both** axes of the
box move it, and the temperature axis moves it by more:

| | Si (Z=14, Ā=28) | Fe (Z=26, Ā=56) |
|---|---|---|
| ρ = 10⁷, T₉ = 7.9 | **0.40** | 1.10 |
| ρ = 10⁷, T₉ = 4 | 0.79 | 2.16 |
| ρ = 10⁸, T₉ = 4 | 1.70 | 4.66 |
| ρ = 10⁹, T₉ = 4 | 3.67 | 10.05 |
| ρ = 10⁹, T₉ = 1.6 | 9.18 | **25.1** |

So across the **full** box (ρ = 10⁷–10⁹ *and* T = 1.6–7.9 GK, Si → Fe)
**Γ ranges roughly 0.4 to 25**. The often-quoted "0.8 to 10" is the ρ-only span
at fixed T₉ = 4 — correct as far as it goes, but it silently freezes the axis
that matters most. Quote the wider range.

> **This is the derivation that justifies the screening config.**
> Salpeter weak screening (Salpeter 1954) assumes Γ ≪ 1. Strong-screening
> asymptotics assume Γ ≫ 1. Silicon burning sits in **neither** — and the
> full-box range makes the point more forcefully than the fixed-T one does,
> because Γ ~ 0.4 to ~25 is two orders of magnitude straddling unity, with no
> sub-region where either asymptotic is safe. You need a prescription that
> *interpolates across both limits*. That is exactly what `chugunov_2007` is —
> the fit of Chugunov, DeWitt & Yakovlev (2007) reproduces the Debye–Hückel
> Γ ≪ 1 asymptote and is calibrated through Γ ~ hundreds, spanning this box —
> and it is why the label configuration pins `screening_mode = 'chugunov'` in
> `scripts/bbq_campaign/inlist.template`.

Carry this into **S4**: when you read `fluxes/screening.py`, you are reading an
intermediate-coupling interpolation, and you now know why nothing simpler would
do.

### 0.1.5 The electron-capture threshold — a box edge derived from scratch

Electron capture on free protons, p + e⁻ → n + ν, requires the total electron
energy to exceed the neutron–proton mass difference (CODATA 2022):

$$
E_e \geq (m_n-m_p)c^2 = 1.2933\ \mathrm{MeV} \qquad (\text{kinetic threshold } 0.782\ \mathrm{MeV})
$$

In a degenerate gas the *available* electron energy is E_F. Setting
E_F = 1.2933 MeV:

$$
\begin{aligned}
p_F c &= \sqrt{1.2933^2 - 0.511^2} = 1.188\ \mathrm{MeV}\\
n_e &= \frac{(p_F c)^3}{3\pi^2(\hbar c)^3} = \frac{1.6765}{29.608\times 7.684\times10^{-33}} = 7.37\times10^{30}\ \mathrm{cm^{-3}}\\
\rho &= \frac{n_e}{N_A Y_e} = \frac{7.37\times10^{30}}{6.022\times10^{23}\times 0.5} = 2.4\times10^{7}\ \mathrm{g\,cm^{-3}}
\end{aligned}
$$

Sanity check: at Yₑ = 1 this gives 1.2×10⁷ g/cm³ — the classic neutronization
threshold for hydrogen (Shapiro & Teukolsky 1983; captures on H switch on once
ρ ≳ 10⁷ g/cm³, Bildsten & Cumming 1998). ✓

> **Result:** free-proton electron capture switches on at ρ ≈ 2.4×10⁷ g/cm³ for
> Yₑ = 0.5 — *inside* the regime box, near its lower edge.

Below that density captures are thermally suppressed (only the distribution's
tail has enough energy); above it they are degeneracy-driven and vigorous.
**The box's lower density edge of 10⁷ g/cm³ sits just below the threshold on
purpose** — it brackets the turn-on of the process that controls Yₑ.

Captures on nuclei have their own thresholds set by their Q-values and in
practice carry most of the capture flux — heavy nuclei outnumber free protons
by orders of magnitude at these conditions (Langanke & Martínez-Pinedo 2003);
the free-proton number is the clean reference point.

### 0.1.6 Self-check

1. Recompute p_F c, E_F, and Γ at ρ = 10⁹, T₉ = 3, and confirm degeneracy and
   coupling both increase. Which pressure component is largest?
2. Show P_e ∝ (ρYₑ)^(4/3) in the ultra-relativistic limit, and connect it to
   the M_ch ∝ Yₑ² derivation in §I.2.
3. At what temperature would radiation pressure overtake ion pressure at
   ρ = 10⁸? Is that inside the box?
4. Why does Γ *increase* as burning proceeds at fixed (ρ, T)? (Hint: what
   happens to Z̄?) What does that imply about screening corrections drifting
   along a trajectory?

## 0.2 Statistical mechanics you actually need

Three results, one framework. Everything in S3 (detailed balance) and S9 (NSE
and QSE) is a corollary of this section.

### 0.2.1 Chemical potential and the equilibrium condition

For a system at fixed (T, V), the Helmholtz free energy F is minimized. The
chemical potential of species i is

$$
\mu_i = \left(\frac{\partial F}{\partial N_i}\right)_{T,V,N_{j\neq i}}
$$

For a reaction with stoichiometric coefficients ν_i (products +, reactants −),
advancing by dξ changes N_i by ν_i dξ, so dF = Σ_i μ_i ν_i dξ. Equilibrium
(dF = 0 for arbitrary dξ) gives the **chemical equilibrium condition**:

$$
\sum_i \nu_i \mu_i = 0 \tag{0.1}
$$

This single equation generates everything:

- **NSE.** Every strong/EM reaction is equilibrated. Apply (0.1) to the
  build-up of nuclide (Z,N) from free nucleons, A(Z,N) ⇌ Z p + N n:

$$
\mu(Z,N) = Z\mu_p + N\mu_n \tag{0.2}
$$

  Every nuclide's chemical potential is determined by just **two** numbers —
  the standard NSE condition (Hix & Thielemann 1996, 1999b; Pitrou et al.
  2018). That is why the NSE solver in `qse/solver.py` has exactly two
  unknowns (u_p, u_n).

- **QSE.** Only a *subset* of reactions is equilibrated — those internal to a
  cluster. Cluster members satisfy (0.2) up to a shared offset:

$$
\mu_i = Z_i\mu_p + N_i\mu_n + u_G \quad \text{for } i\in G \tag{0.3}
$$

  One extra unknown per cluster — the focal-nucleus form of Hix & Thielemann
  (1996), whose r_QSE is constant within a group and offset between groups, and
  whose QSE distribution "blends simply into the NSE distribution" as the
  offset vanishes. That is the third unknown in `solve_qse`, and u_G = 0
  recovers NSE exactly — which is why the QSE→NSE degeneracy is a test case in
  `tests/test_qse_solver.py`.

- **Detailed balance.** Apply (0.1) to a single forward/reverse pair; the ratio
  of rate coefficients is fixed by the Q-value and partition functions. This is
  S3.

### 0.2.2 Nuclear partition functions

A nucleus has excited states. The internal partition function is

$$
G(T) = \frac{\sum_{\text{states}} (2J_s+1)\,e^{-E_s/kT}}{2J_0+1} \tag{0.4}
$$

normalized so G → 1 as T → 0 (only the ground state populated).

**Why it matters here, quantitatively.** First excited states in Si–Fe-peak
nuclei span a wide range (ENSDF): tens of keV for odd-A and odd–odd species
(⁵⁷Fe at 14.4 keV, ⁵⁴Mn at 54.9 keV), ~0.8–1.2 MeV for even–even Fe-group
nuclei (⁵⁶Fe at 0.847 MeV), up to 1.8–2.7 MeV for the Si-shell even–even and
near-magic cases (²⁸Si at 1.78 MeV, ⁵⁶Ni at 2.70 MeV). At T₉ = 4,
kT = 0.345 MeV, so a ~0.85 MeV state carries e^(−2.5) ≈ 0.08 per magnetic
substate while states below ~kT are populated at order unity. G reaches
~1.5–3 for typical odd-A Fe-group nuclei — and up to ~4–7 for the extreme
low-lying cases (⁵⁷Fe ≈ 6.6 at T₉ = 4) — while the doubly-magic and
near-magic Fe-peak nuclei (⁵⁶Ni above all, G = 1.002 at T₉ = 4) stay at
G ≈ 1 (Rauscher & Thielemann 2000; Rauscher 2003). So the pf correction is
strongly species-dependent, and largest exactly where the level density is,
not where the abundance is. ("Deformation" is the wrong word for this regime;
near N = Z and Z = 28 these nuclei are close to spherical. What raises G here
is level density at E* ~ kT.)

> A factor of 2 in G is a factor of 2 in a detailed-balance reverse rate. That
> is the entire reason `DerivedRate(use_pf=True)` is mandatory above T₉ ≈ 3,
> and why raw pf-free fits manufacture spurious κ floors.

**In the code:** partition functions come from Rauscher tables (Rauscher &
Thielemann 2000; Rauscher 2003 — the reverse-rate ratio is linear in G, so a
factor of 2 in G is exactly a factor of 2 in the reverse rate), rebuilt as
splines with constant extrapolation, in both `fluxes/compile.py` and
`qse/coeffs.py` — and the two paths are cross-checked against each other,
because a pf mismatch between the rate side and the equilibrium side would
silently corrupt every κ comparison.

### 0.2.3 Detailed balance from time reversal

The microscopic statement: for a transition a → b, the squared matrix element
is invariant under time reversal — T-invariance implies S-matrix symmetry
S_ab = S_ba and hence detailed balance |S_ab|² = |S_ba|² (Mitchell, Richter &
Weidenmüller 2010) —

$$
\bigl|\langle b|T|a\rangle\bigr|^2 = \bigl|\langle a|T|b\rangle\bigr|^2
$$

The *rates* differ only through phase-space density of final states and
statistical weights. In equilibrium, forward and reverse rates per unit volume
must be equal — that is what "detailed" balance means: not just net zero
overall, but **pairwise** zero, reaction by reaction.

This pairwise statement is exactly what κ measures:

$$
\kappa_r = \frac{|f^+ - f^-|}{f^+ + f^-} \;\longrightarrow\; 0 \quad \text{at true equilibrium}
$$

So κ is not an arbitrary diagnostic — it is the numerical test of detailed
balance, reaction by reaction. A nonzero κ floor at NSE means the code's
forward and reverse rates are *mutually inconsistent*, which is a bug, not
physics. That is the logic of the whole κ-floor screen. (§V.1 gives κ its
second, independent meaning as a condition number — the two readings coincide,
which is why κ is load-bearing everywhere in this project.)

### 0.2.4 Self-check

1. Derive (0.2) from (0.1) for the specific case ²⁸Si ⇌ 14p + 14n.
2. Explain why NSE needs exactly two constraints (ΣX = 1, Yₑ) given (0.2) has
   two free parameters. What breaks if you impose a third?
3. Estimate G(T) at T₉ = 5 for a nucleus with first excited state at 0.85 MeV
   and J = 2 (ground J = 0). By what factor would omitting it change a
   detailed-balance reverse rate?
4. Argue why detailed balance is *pairwise* and not merely a statement about
   net flow. Then explain how a code could satisfy overall equilibrium while
   having every individual κ_r ≠ 0.

## 0.3 Nuclear structure minimum

### 0.3.1 The mass-excess convention — a real sign trap

Nuclear data tables give the **mass excess**, not the binding energy:

$$
\Delta(A,Z) \equiv \bigl[M_{\text{atomic}}(A,Z) - A\,u\bigr]\,c^2 \tag{0.5}
$$

Tabulated masses are **atomic** (electrons included). Binding energy is
recovered by (mass excesses throughout from AME2020 — Wang et al. 2021):

$$
\begin{aligned}
B(A,Z) &= Z\,\Delta(^{1}\mathrm{H}) + N\,\Delta(n) - \Delta(A,Z),\\
\Delta(^{1}\mathrm{H}) &= 7.2890\ \mathrm{MeV}, \qquad \Delta(n) = 8.0713\ \mathrm{MeV}
\end{aligned}
\tag{0.6}
$$

**Worked example — ⁵⁶Fe** (Δ = −60.607 MeV):

$$
\begin{aligned}
B &= 26\times 7.2890 + 30\times 8.0713 + 60.607\\
&= 189.51 + 242.14 + 60.61 = 492.26\ \mathrm{MeV}\\
B/A &= 8.790\ \mathrm{MeV} \qquad \checkmark\ \text{textbook value}
\end{aligned}
$$

| Nuclide | Δ (MeV) | B/A (MeV) |
|---|---|---|
| ⁵⁶Ni (Z=N=28) | −53.908 | 8.643 |
| ⁵⁶Fe | −60.607 | **8.790** |
| ⁵⁸Fe | −62.155 | 8.792 |
| ⁶²Ni | −66.746 | **8.795** ← most bound nuclide |

(⁶²Ni as the most bound nuclide — not ⁵⁶Fe, a common misconception — is
Fewell 1995: B/A = 8794.60 ± 0.03 keV.)

**Q-values follow directly:**

$$
Q = \sum \Delta_{\text{reactants}} - \sum \Delta_{\text{products}} \tag{0.7}
$$

**Worked example — ²⁸Si(α,γ)³²S:**

$$
\begin{aligned}
Q &= \bigl[\Delta(^{28}\mathrm{Si}) + \Delta(^{4}\mathrm{He})\bigr] - \Delta(^{32}\mathrm{S})\\
&= [-21.493 + 2.425] - (-26.016)\\
&= -19.068 + 26.016 = 6.948\ \mathrm{MeV} \qquad \checkmark
\end{aligned}
$$

This matters concretely: `configs/reactions_mesa{80,151}_mesa.yaml` carries a
`q_mev` field per reaction, and the energy identity e_nuc = Σ_j Q_j Φ_j in S10
consumes it. You should be able to reproduce any entry by hand.

### 0.3.2 Magic numbers and why ⁵⁶Ni is the Si-burning endpoint

Shell closures at N or Z = 2, 8, 20, 28, 50, 82, 126 produce extra binding
(Otsuka et al. 2020). **Z = N = 28 makes ⁵⁶Ni doubly magic**, which is why:

- it is the most bound nuclide accessible at Yₑ = 0.5,
- it is the dominant Si-burning product (Hix & Thielemann 1996),
- and its decay chain ⁵⁶Ni (T½ = 6.08 d) → ⁵⁶Co (T½ = 77.2 d) → ⁵⁶Fe powers
  supernova light curves (Diehl et al. 2015; half-lives from ENSDF), which is
  how we *measure* how much of it was made (§VI.6).

Note the mechanism connecting to §I.2: the binding-energy maximum (⁶²Ni) and the
actual product (⁵⁶Ni) differ because the **Yₑ constraint** binds. Weak reactions
are the only way to relax it, and they are slow. The composition is set by a
*constrained* optimum, and the constraint is the project's central variable.

### 0.3.3 Where the rates actually come from — and how well they are known

The part most easily assumed away. In a network reaching to Ni and beyond:

| Source | Coverage | Typical uncertainty |
|---|---|---|
| Direct experiment | light nuclei, a minority of channels | a few % (best-measured channels) to a few tens of % (Iliadis et al. 2010) |
| Hauser–Feshbach statistical model | **the large majority** of (n,γ), (p,γ), (α,γ) on mid/heavy nuclei | factor ~1.5–2, worse off stability (Rauscher & Thielemann 2000) |
| Shell-model weak rates (LMP) | Fe-peak electron capture / β-decay | no blanket figure; GT-strength dependent — the LMP revision moved key FFN EC rates by factors ~10–350 (Langanke & Martínez-Pinedo 2000) |

REACLIB is a *fit library* (Cyburt et al. 2010): seven coefficients per set,
several sets summed per rate, fitted to whichever of the above is best
available. Two consequences:

1. **The seven-coefficient form is a fitting basis with physical asymptotics,
   not an exact theory** (S2 derives why those particular terms).
2. **There is an irreducible physics-uncertainty floor.** An emulator
   reproducing MESA to 10⁻⁶ is reproducing *MESA*, not nature. This is why the
   project frames its gates as fidelity-to-labels — and why the label-pathology
   finding (S13) matters so much: it is the case where MESA and nature part
   company by 7–13 dex.

### 0.3.4 Self-check

1. Reproduce B/A for ⁵⁶Ni from (0.6) and confirm 8.643 MeV.
2. Compute Q for ³²S(α,γ)³⁶Ar and for the reverse. What is the sign relation?
3. Pick five reactions from `configs/reactions_mesa80_mesa.yaml` and verify
   `q_mev` by hand from a mass table.
4. Given that most (n,γ) rates carry factor-~2 theoretical uncertainty, what is
   the strongest *defensible* claim an emulator can make about physical
   accuracy? Write it as one sentence.

## 0.4 Neutrinos

### 0.4.1 Two distinct neutrino channels

Do not conflate these; the dataset carries them differently.

**(a) Thermal neutrino losses** — pair annihilation (e⁺e⁻ → νν̄), photoneutrino,
plasmon decay, bremsstrahlung (Itoh et al. 1996; Kato et al. 2020). Depend on
the thermodynamic state — (T, ρYₑ) for the e± processes, plus mean Z̄/Ā for
bremsstrahlung — not on the detailed isotopic abundances. Pair production
dominates at silicon-burning temperatures (Kato et al. 2020) and approaches
its relativistic-limit ∝T⁹ scaling there (steeper, ~T¹¹ or more, at lower T).

**(b) Weak-reaction neutrinos** — emitted by every electron capture and β decay.
Depend on composition, carry away lepton number as well as energy, and are
inseparable from the Yₑ evolution.

In the data: `eps_nu` / `eps_neu` columns. Note the units trap from §III.6 — a
**rate** [erg/g/s] in the training CSVs while `eps_nuc` beside it is
**integrated** [erg/g].

### 0.4.2 Why neutrinos free-stream — and why that accelerates everything

Neutrino–nucleon cross sections scale as (Janka 2017, where
σ₀ = (4/π)G_F²(m_ec²)²/(ħc)⁴ = 1.761×10⁻⁴⁴ cm²)

$$
\sigma \approx \sigma_0\left(\frac{E_\nu}{m_e c^2}\right)^{\!2}, \qquad \sigma_0 \approx 1.7\times10^{-44}\ \mathrm{cm^2}
$$

At E_ν ≈ 3 MeV: σ ≈ 5.9×10⁻⁴³ cm². At ρ = 10⁸ g/cm³, n_baryon = 6.0×10³¹ cm⁻³:

$$
\lambda = \frac{1}{n\sigma} = \frac{1}{6.0\times10^{31}\times 5.9\times10^{-43}} \approx 2.8\times10^{10}\ \mathrm{cm} \approx 2.8\times10^{5}\ \mathrm{km}
$$

The iron core radius is ~10³ km, so **λ/R ≈ 300**: neutrinos escape without
scattering. (Coherent scattering on nuclei enhances σ by roughly N²/16 ≈ A²/60
— the vector amplitudes on the N neutrons add in phase (Janka 2017) — cutting
λ, but trapping only sets in around ρ ≈ 10¹¹–10¹² g/cm³ (Janka 2017), well
above this box.)

**Two consequences, both structural:**

1. **Energy leaves instantly.** No diffusion time. This is the mechanism behind
   the burning-stage acceleration table in §I.1 — the core must burn ever faster
   to replace energy leaking at c.
2. **Lepton number leaves with it.** Each capture emits a ν that never comes
   back. This is why the constraint matrix needs a *separate neutrino ledger*:
   lepton number is conserved by the reaction but then physically removed from
   the zone.

   **Be careful with the next step, which is easy to overstate.** Free-streaming
   does not itself *drive* Yₑ down — what drives it down is electron capture
   outpacing β⁻ decay, a statement about net rates and about how degenerate the
   electrons are (§0.1.5). What free-streaming does is *prevent the drop from
   stopping*: if neutrinos were trapped they would build up a chemical potential
   until forward and reverse weak rates balanced, and Yₑ would freeze at β
   equilibrium. Escape removes that back-reaction, so the ratchet has nothing to
   push against. Hence Yₑ declines essentially monotonically **through the
   burning phase in aggregate**, not term-by-term — β⁻ decays run the other way
   throughout, which is precisely why §I.4 treats mesa_80's *absence* of β-decay
   partners as a structural defect rather than a harmless omission.

That second point is worth pausing on. The three-row structure of C — baryon,
charge (with the electron column), lepton number (e⁻ +1, ν +1, ν̄ −1) — is not
bookkeeping fussiness. It is what lets you state "lepton number is conserved by
the reaction" while the neutrino column subsequently leaves the system.

### 0.4.3 ⟨E_ν⟩ — an open item to understand before you meet it

Energy loss per capture is not simply the Q-value: the emitted neutrino carries
a *spectrum*, and what the zone loses is ⟨E_ν⟩ per reaction. Weak-rate tables
therefore provide both a rate and a neutrino energy-loss rate — FFN onward;
Langanke & Martínez-Pinedo (2001) tabulate effective rates *and* average
neutrino energies, and Patton et al. (2017) show exactly how ⟨E_ν⟩ is
reconstructed from those tables — and codes handle the latter with varying
care.

This is a **standing open item in the project** ("MESA average-neutrino-energy
handling (⟨E_ν⟩) for the neutrino head"). When you design a neutrino output
head, you will need to know exactly what MESA reports and on what grid.

### 0.4.4 Self-check

1. Recompute λ at ρ = 10⁹ and E_ν = 5 MeV. Is free-streaming still safe?
2. Explain, in terms of §0.4.2, why carbon burning onward is neutrino-cooled
   while hydrogen burning is not.
3. The lepton-number row of C assigns ν +1 and ν̄ −1. Write the row entries for
   an electron capture and for a β⁻ decay, and verify each column closes.
4. Why can thermal neutrino losses be computed from (T,ρ) alone, while weak
   neutrino losses cannot? Which one does the emulator have to learn?

## 0.5 Reaction nomenclature and REACLIB chapters

Basic literacy. The configs index reactions by these categories, and the
project's headline bug is indexed by *chapter*.

### Channel notation

$$
A(b,c)D \qquad \text{means} \qquad A + b \to c + D
$$

with the light participants abbreviated: n, p, α, γ, e⁻, ν (standard notation
— José & Iliadis 2011). Channels that appear in this network:

| Channel | Meaning | Role in Si burning |
|---|---|---|
| (α,γ) / (γ,α) | α capture / α photodisintegration | **the ladder** — Si → S → Ar → … → Ni |
| (p,γ) / (γ,p) | proton capture / release | side flow, bottlenecks |
| (n,γ) / (γ,n) | neutron capture / release | fastest pairs; set the stiffness ceiling |
| (p,α), (α,p) | rearrangement | bridges between groups |
| (n,α), (α,n) | rearrangement | bridges |
| (p,n), (n,p) | charge exchange, strong | conserves Yₑ (both A and Z conserved overall) |
| (e⁻,ν) | electron capture | **weak** — lowers Yₑ |
| β⁻, β⁺ | beta decay | **weak** — raises / lowers Yₑ |

**A reverse is a distinct reaction**, not a sign flip: (α,γ) and (γ,α) are two
columns of ν, two rate evaluations, two rows in the config. §II.6 explains why
that representational choice is what makes κ measurable.

### REACLIB chapters

REACLIB indexes every rate by a **chapter**, which is simply the reactant and
product counts (Cyburt et al. 2010; all eleven forms below verified against
the JINA REACLIB format definition):

| Chapter | Form | ΔN = n_out − n_in | Example |
|---|---|---|---|
| 1 | e₁ → e₂ | 0 | β decay, electron capture |
| 2 | e₁ → e₂ + e₃ | +1 | (γ,n), (γ,p), (γ,α) |
| 3 | e₁ → e₂ + e₃ + e₄ | +2 | ¹²C → 3α |
| 4 | e₁ + e₂ → e₃ | −1 | (n,γ), (p,γ), (α,γ) |
| 5 | e₁ + e₂ → e₃ + e₄ | 0 | (p,α), (α,n), (n,p) |
| 6 | e₁ + e₂ → e₃ + e₄ + e₅ | +1 | ¹¹B(p,2α)α, ³He(³He,2p)⁴He class |
| 7 | e₁ + e₂ → e₃ + e₄ + e₅ + e₆ | +2 | light-ion 2→4 breakup, e.g. ⁷Li(³He,npα)α |
| 8 | e₁ + e₂ + e₃ → e₄ | −2 | **3α → ¹²C** |
| 9 | e₁ + e₂ + e₃ → e₄ + e₅ | −1 | |
| 10 | e₁ + e₂ + e₃ + e₄ → e₅ + e₆ | −2 | |
| 11 | e₁ → e₂ + e₃ + e₄ + e₅ | +3 | |

**Why the chapter is the quantity that matters.** Detailed balance relates a
forward rate to its reverse through a phase-space factor carrying one power of

$$
\left(\frac{\mu\,kT}{2\pi\hbar^2}\right)^{3/2}\Big/ N_A
$$

**per excess product** — i.e. per unit of |ΔN| (§0.2.3, and derived properly in
S3; the general reverse-ratio formula carries the factor to the power r − p —
Rauscher & Thielemann 2000; Smith et al. 2023, appendix). Note the reduced
mass μ inside: without it the factor is not a number density, and the
bookkeeping does not close dimensionally.

⚠ **Do not compress this to "|ΔN| ≠ 1 is the bug".** That is the natural guess
and it is wrong — see below. The discriminator is the *arity* of the tabulated
direction, not |ΔN|.

The gh-575 / Appendix-B bug lives here (MESA issue #575; Grichener et al.
2025, App. B): stock MESA's detailed-balance path handles only the **2 → 1**
forward (chapter 4, giving the chapter-2 reverse), where exactly one power of
the factor is required, plus the factor-free 2 → 2 case. Any tabulated
direction with **three or more participants on a side** falls outside that
path — the issue reports the phase-space factor is omitted there, producing
reverse rates wrong by up to ~24 orders of magnitude (exactly how many powers
are missing per channel is an inference from the formula, not stated in the
issue). So the affected forward chapters are **6** (2→3), **7** (2→4), **8**
(3→1), and **9** (3→2), and it is their *inverses* that MESA gets wrong.

**Read the config with its convention in hand**, because it is not stated in the
file: in `configs/appendixb_excluded_channels.yaml`, `chapter` is the chapter of
the **tabulated forward**, while `mesa_handle` and `dN` describe the **inverse**
— the direction actually being flagged. Hence rows like

```
chapter: 8   dN: +2    r_c12_to_he4_he4_he4     ← forward 3α→¹²C is ch-8;
                                                  the flagged handle is its 1→3 inverse
chapter: 6   dN: −1    r_he4_he4_he4_to_h1_b11  ← forward h1+b11→3α is ch-6;
                                                  the flagged handle is its 3→2 inverse
```

> **The falsification you should perform yourself.** Count `dN` over the 20 rows
> of that config (11 for mesa_151, 9 for mesa_80): **13 of them have |dN| = 1** —
> all eleven chapter-6 rows and both chapter-9 rows. The only rows with |dN| ≠ 1
> are the two chapter-7 (dN = −2) and five chapter-8 (dN = +2) entries. If
> "|ΔN| ≠ 1" were the bug, the other thirteen rows could not
> be there. Conversely chapter 8's forward *does* have a single product, so a
> rule phrased on product count alone would wrongly exonerate `3α → ¹²C` — whose
> inverse is in the config with `dlog10` in the tens. The config's own `class`
> values name the real criterion (`multi_body_inverse` for the ch-6/7/9 rows,
> `photo_of_multibody` for the five ch-8 rows — the 3α inverse is the latter).
> The `dlog10` column is how far wrong the rate was.

Chapter 5 (2→2) is safe for a different reason again — ΔN = 0, so no factor is
needed at all. Chapters 10 and 11 do not appear as tabulated-*forward*
chapters: REACLIB's five ch-10 entries are all v-flagged detailed-balance
reverses of the ch-7 forwards (three touch only in-network species, e.g.
n+p+α+α → ³He+⁷Li — i.e. exactly the raw-reverse class the pf gate forbids
using), and its ch-11 forwards are all β-delayed multi-neutron emitters near
the dripline, outside these networks. Not because either arity would be safe.

### In the code

`configs/reactions_mesa{80,151}_mesa.yaml` carries `category` per reaction (see
§0.6); `configs/appendixb_excluded_channels.yaml` carries `chapter` and `dN`.
`crosscheck/canonical.py` builds the directed multiset key that makes
"same reaction" decidable across MESA and pynucastro.

## 0.6 The topology of silicon burning

What actually flows where. §I.1 said "photodisintegration rearrangement"; this
is the mechanism in detail.

### The α ladder

Photodisintegration of the least-bound nuclei liberates α, p, n. Those light
particles are captured by the rest, walking composition up an α-chain
(Bodansky, Clayton & Fowler 1968; Woosley, Arnett & Clayton 1973; Hix &
Thielemann 1996):

```
   ²⁸Si ─(α,γ)→ ³²S ─(α,γ)→ ³⁶Ar ─(α,γ)→ ⁴⁰Ca ─(α,γ)→ ⁴⁴Ti
        ←(γ,α)─      ←(γ,α)─      ←(γ,α)─      ←(γ,α)─
                                                    │
                      ⁵⁶Ni ←(α,γ)─ ⁵²Fe ←(α,γ)─ ⁴⁸Cr ←┘
```

**The config category names are literally this ladder.** Count them in
`configs/reactions_mesa80_mesa.yaml`:

| Category | Count (mesa_80) | What it is |
|---|---|---|
| `photo` | **151** | photodisintegration — the largest single category |
| `si_alpha`, `s_alpha`, `ar_alpha`, `ca_alpha`, `ti_alpha`, `cr_alpha` | 27, 22, 19, 17, 14, 14 | the rungs of the ladder |
| `fe_co_ni` | 17 | the top of the ladder |
| `c_alpha`, `n_alpha`, `o_alpha`, `ne_alpha`, `na_alpha`, `mg_alpha` | 7, 10, 23, 32, 25, 27 | below Si — inherited from earlier stages |
| `tri_alpha` | 1 | 3α → ¹²C (its 1→3 inverse is the gh-575 casualty, §0.5) |
| `c12_c12`, `o16_o16` | 3, 3 | heavy-ion fusion, earlier stages |
| `pp`, `cno` | 15, 33 | hydrogen burning, essentially inert here |
| `other` | 147 | (p,n), (n,p), weak, everything else |
| **total** | **607** | ← the table sums; check it |

That `photo` is the largest category is the whole story of §I.1 in one number.

### Two clusters and the bridges between them

Both ends of the ladder equilibrate internally faster than material crosses the
middle. This produces the structure the project's QSE machinery targets — two
QSE groups divided near A ≈ 45 (Woosley, Arnett & Clayton 1973; Hix &
Thielemann 1996):

```
   ┌──────────────────────┐   bridges    ┌──────────────────────┐
   │   SILICON GROUP      │ ──────────▶  │    IRON GROUP        │
   │   24 ≤ A < 45        │  bottleneck  │    A ≳ 45            │
   │   internally fast     │  reactions   │   internally fast     │
   └──────────────────────┘              └──────────────────────┘
             ▲                                       │
             └────────── free n, p, α ───────────────┘
```

- **Within a group**, forward and reverse rates are fast and nearly balanced —
  so κ is small there, and the abundances follow an equilibrium (Saha-like)
  distribution up to one cluster-wide offset (§0.2.1, eq. 0.3).
- **Between groups**, flow is rate-limited by a handful of **bridge** reactions.
  These carry the net baryon flux and therefore control how fast Si becomes Fe.

This is what `configs/qse_groups.yaml` encodes (`a_min: 24`, `a_max: 45`, with
the `a24_46` variant moving the boundary so that ⁴⁵Sc falls inside), and what
the bridge analysis of S9 measures. It also explains why a *bottleneck*
reaction like ⁴⁵Sc(p,γ)⁴⁶Ti is worth naming individually: a small number of
reactions carry a large share of the inter-group flow — in the classic
analysis that single reaction dominated the linkage, with perhaps a quarter of
the flow through lesser channels (Woosley, Arnett & Clayton 1973, as quoted by
Hix & Thielemann 1996).

### A note on energy accounting

Two independent routes to the same specific energy release, both used by the
project as a mutual check:

$$
\begin{aligned}
\text{composition route:}\quad e_{\text{nuc}} &= -N_A\sum_i m_i c^2\,\Delta Y_i && \text{(mass excesses, §0.3.1)}\\
\text{flux route:}\quad e_{\text{nuc}} &= \sum_j Q_j\,\Phi_j && \text{($Q$-values} \times \text{fluxes)}
\end{aligned}
$$

They must agree, because Q-values are themselves differences of mass excesses.
Agreement is therefore *near-algebraic* when Q is taken constant — it bounds
Q-table rounding, not route physics. A genuinely independent check needs the
energy from one code's rates against another's composition change, which is why
the project reports two separate readings and treats only the second as
informative. Keep that distinction; it is easy to over-claim here.

## 0.7 The timescale hierarchy

Every structural feature of this problem is a statement about a ratio of
timescales. Assembling them in one place is the single most useful organizing
device in Tier 0.

### The species destruction timescale

For species i, define

$$
\tau_i = \frac{Y_i}{|\dot{Y}_i|} \tag{0.8}
$$

— the e-folding time of that species at the current state. This is the quantity
that decides whether a label step is "linear" (τ ≫ Δt) or a full relaxation
(τ ≲ Δt), and it is what the handshake analysis bins on (§III.3).

### The hierarchy, at box centre

Order-of-magnitude estimates at T₉ ≈ 4, ρ ≈ 10⁸ — derive each yourself rather
than trusting the table:

| Process | Timescale | Set by |
|---|---|---|
| (γ,n) / (n,γ) on loosely bound nuclei | 10⁻¹⁰ – 10⁻⁶ s | e^(−Q/kT) with Q ~ few MeV |
| charged-particle captures | 10⁻⁶ – 10⁰ s | Coulomb barrier + screening |
| intra-group equilibration | ≲ 10⁻³ s | the above, within a cluster |
| **inter-group (bridge) flow** | 10⁻¹ – 10² s | bottleneck reactions |
| **weak reactions (EC, β)** | 10² – 10⁵ s | ft values, E_F |
| label dt grid | 10⁻⁶ – 10² s | ← the emulator's window |
| convective turnover | 10¹ – 10³ s | v_conv ~ 10⁶–10⁷ cm/s over L ~ 10⁸–10⁹ cm |
| core Si burning duration | ~10⁵–10⁶ s (≈1 day to ~2 weeks, mass-dependent; WHW02) | neutrino cooling |
| free-fall collapse | ~0.07 s | √(3π/32Gρ) at ρ = 10⁹ |

**Read the consequences straight off the table:**

- **Stiffness ratio** (§V.3) is the ratio of the extremes: ~10¹⁰/10⁻⁵ ≈ 10¹⁵.
- **QSE exists** because intra-group ≪ inter-group. The separation *is* the
  cluster structure.
- **Yₑ is slow** — weak timescales are the longest in the burning problem, which
  is why Yₑ evolution is the thing you must integrate accurately for a long time,
  and why it has no restoring force on the fast manifold (§IV.3).
- **The dt grid brackets the interesting range** — its 10⁻⁶ s floor sits at
  (not below) the fastest charged-particle capture timescales, and its top
  end reaches past the bridge timescale.
- **Operator splitting is safe at the short end, questionable at the long end**
  (§IV.1): Δt = 10² s is comparable to the bridge and convective timescales.
- **One-zone is an approximation** because convective turnover (10¹–10³ s) is
  *not* long compared to the bridge timescale (§IV.2).

> ⚠ **Do the convective row's arithmetic yourself, and notice it is a range you
> cannot pin.** τ_conv = L/v_conv, and both factors are uncertain by a decade:
> L ~ 10⁸–10⁹ cm for the convective Si-burning core, v_conv ~ 10⁶–10⁷ cm/s. The
> corners give 10 s and 10³ s. Quoting a tight "10²–10³ s" requires committing to
> L ~ 10⁹ cm, which is defensible but is a choice, not a derivation. This matters
> because two conclusions lean on the comparison: whether Δt = 10² s violates the
> splitting assumption (§IV.1) and whether one-zone is safe (§IV.2). At the fast
> corner mixing is *faster* than the bridge flow and one-zone is worse than the
> table suggests; at the slow corner they are comparable. Carry the range, not a
> point value.

### ⚠ The separation you are tempted to assume does not exist

The natural next move is: "the fast sector is 6–8 orders faster than the slow
sector, so equilibrate it algebraically and integrate only the slow part."

That figure was carried in this project as an *assumed* number and has been
**retired by measurement**. On the actual label manifold, per-stratum medians of

$$
\log_{10}\left[\frac{\text{fastest } \kappa\text{-balanced gross rate}}{\text{slowest inter-group bottleneck net rate}}\right]
$$

span roughly **−12 to +1.4 dex** (p10 ≈ −25, p90 ≈ +3.5). There is no cleanly
separated fast equilibrated sector: κ-balanced pairs are ≤ 0.4% of carrying
pairs and are mostly low-flux.

> **So the hierarchy above is a real and useful organizing device, but it is a
> hierarchy of *typical* values with enormous overlap — not a spectral gap.**
> Any design that assumes a clean gap (a frozen equilibrium mask, a two-timescale
> reduction) has to justify itself against that measurement. This is the
> quantitative reason the Guidry mask came up empty and the flux head ended up
> full-width.

### 0.7.1 Self-check for §0.5–0.7

1. Write ⁴⁰Ca(α,γ)⁴⁴Ti and its reverse in chapter notation. What is ΔN for each?
   Why is this pair safe — and state the reason in terms of arity, not |ΔN|.
2. Take three entries from `configs/appendixb_excluded_channels.yaml` and verify
   both fields against the table in §0.5 — remembering that `chapter` describes
   the tabulated *forward* while `dN` describes the flagged *inverse*. Then
   tabulate |dN| over all 20 rows and confirm that most of them are 1, i.e. that
   |ΔN| ≠ 1 is *not* the criterion.
3. Why is `photo` the largest reaction category in the network? Connect to §I.1.
4. Estimate τ for a (γ,n) with Q = 8 MeV at T₉ = 4 and at T₉ = 5. How many
   decades does one GK buy you?
5. Given the hierarchy table, predict which pairs of processes could plausibly
   *swap order* somewhere in the box. Check against the −12…+1.4 dex measurement.
6. State in one sentence why "6–8 orders of separation" being false does not
   invalidate the QSE *concept*, only its algebraic exploitation.

---

# Part I — Why this project exists

Each link in this chain is a physical claim you should be able to defend.

## I.1 The last day of a massive star

### The burning sequence

A star above ~10–11 M⊙ burns through the full sequence of fuels to an iron
core, each stage ignited when the ash of the previous one contracts and heats
until the next Coulomb barrier becomes penetrable. (Stars of ~8–11 M⊙ ignite
carbon but generally stop there, ending as ONeMg cores rather than completing
the chain to silicon.) Temperatures, reactions, and durations below follow
Woosley, Heger & Weaver (2002) — durations shorten steeply with mass:

| Stage | Core T (GK) | Principal reactions | Ash | Duration (15–25 M⊙ models) |
|---|---|---|---|---|
| H | 0.03 | pp chains, CNO cycle | ⁴He | ~10⁷ yr |
| He | 0.2 | 3α → ¹²C; ¹²C(α,γ)¹⁶O | ¹²C, ¹⁶O | ~10⁶ yr |
| C | 0.8 | ¹²C(¹²C,α)²⁰Ne, (¹²C,p)²³Na | ²⁰Ne, ²³Na, ²⁴Mg | ~10³ yr |
| Ne | 1.5 | ²⁰Ne(γ,α)¹⁶O then ²⁰Ne(α,γ)²⁴Mg | ¹⁶O, ²⁴Mg | ~1 yr |
| O | 2.0 | ¹⁶O(¹⁶O,α)²⁸Si, (¹⁶O,p)³¹P | ²⁸Si, ³²S | ~months (up to ~yr with convection) |
| **Si** | **3–4** | **photodisintegration rearrangement** | **Fe peak** | **~1 day–2 weeks** |

Note the qualitative change at neon: at neon, and again at silicon,
**photodisintegration initiates the burning** — oxygen burning, in between, is
still true heavy-ion fusion. The Coulomb barrier for ²⁸Si + ²⁸Si is prohibitive
(Z₁Z₂ = 196), so silicon does not fuse with itself. Instead γ-rays in the thermal
tail knock α-particles, protons, and neutrons off the least-bound nuclei, and
those light particles are captured by others. **Silicon burning is a
rearrangement, not a fusion reaction.**

This single fact explains most of the project's structure: rearrangement
proceeds through many competing forward/reverse channels near balance, which is
where cancellation (κ), quasi-equilibrium clustering, and stiffness all come
from.

### Why the acceleration

From carbon burning onward, energy leaves the core as **neutrinos**, not
photons (Limongi 2017; José & Iliadis 2011). Photons diffuse — the radiative
diffusion time through a stellar interior is enormous, which is what makes
hydrogen burning last 10⁷ years. Neutrinos free-stream at essentially the
speed of light (§0.4.2).

The dominant thermal loss is pair annihilation, whose volumetric emissivity
rises roughly as **T⁹** here (the relativistic regime, T₉ ≳ 2–3; §0.4.1). A core that contracts and heats loses energy catastrophically
faster, so it must burn faster to compensate. Each successive stage is shorter
by a large factor, and the sequence terminates at the iron peak where no
exothermic fusion remains.

### Why this is the regime to emulate

Silicon burning concentrates the computational pain: highest temperatures
(fastest rates, stiffest equations), largest networks (the iron peak needs many
species), shortest timesteps — all in the phase that determines what the star
leaves behind, and where a stellar-evolution code spends a disproportionate
fraction of total runtime inside the network.

## I.2 What actually determines whether the star explodes

At the end of Si burning the core is an iron sphere supported by **degenerate
electron pressure**, which carries ~93% of the total at box-centre conditions
(§0.1.2).

### Derivation — M_ch ∝ Yₑ²

For an ultra-relativistic degenerate electron gas, pressure depends only on
electron number density:

$$
P = \frac{(3\pi^2)^{1/3}\,\hbar c\, n_e^{4/3}}{4}
$$

Charge neutrality ties n_e to matter density through Yₑ (derived in §II.5):

$$
n_e = \rho N_A Y_e \qquad \implies \qquad P = K\,(\rho Y_e)^{4/3}
$$

A polytrope with γ = 4/3, index n = 3. The Lane–Emden solution for n = 3 has the
property that total mass is **independent of central density**:

$$
M = 4\pi M_3\left(\frac{K}{\pi G}\right)^{3/2}, \qquad M_3 \approx 2.018
$$

Since K ∝ Yₑ^(4/3) and M ∝ K^(3/2):

$$
M_{\text{ch}} \propto Y_e^2 \qquad \text{numerically} \qquad M_{\text{ch}} \approx 5.83\,Y_e^2\,M_\odot
$$

(Lane–Emden constant ξ₁²|θ′| = 2.01824; the same derivation appears in Suwa et
al. 2018, whose M_Ch0 = 1.46 M⊙ (Yₑ/0.5)² is this formula.)

**Check:** Yₑ = 0.5 gives 1.457 M⊙ — the textbook value. Yₑ = 0.45 gives
1.18 M⊙, a **19% reduction** in supportable mass from a 10% change in one
composition scalar.

### The thermal correction

$$
M_{\text{ch,eff}} \approx 5.83\,Y_e^2\left[1 + \left(\frac{s_e}{\pi Y_e}\right)^{\!2}\right] M_\odot
$$

where s_e is the electron entropy per baryon in units of k. This is the
first-order form of Baron & Cooperstein (1990), whose exact bracket is
[1 + (2/3)(s_e/πYₑ)²]^{3/2} (see also Timmes, Woosley & Weaver 1996; Suwa et
al. 2018). So **entropy also raises the effective Chandrasekhar mass** — a
hotter core supports more. Yₑ remains the dominant lever and the one nuclear
burning directly controls, but the picture is two-parameter.

### The collapse trigger

Collapse begins when pressure support fails, via two coupled runaways:

1. **Photodisintegration of the iron peak.** Once the core reaches
   **T ≳ 7–10 GK** (Janka 2012, after B²FH) — above the regime box, and
   strongly density-dependent — ⁵⁶Fe(γ,α)-type reactions dismantle the Fe peak
   back to α-particles and free nucleons. This is strongly **endothermic**:
   ⁵⁶Fe → 13α + 4n costs 124.4 MeV (AME2020 mass excesses), i.e.
   2.22 MeV/nucleon, consuming thermal energy and reducing pressure.

   > **Do not put this turn-on at ~5 GK.** Si burning *produces* the Fe peak at
   > 3–4 GK (§I.1), and the box's own upper edge of 7.9 GK is characterized as
   > full NSE that is still Fe-peak dominated (§III.2). A dismantling threshold
   > at 5 GK would contradict both. The Fe peak survives NSE across the whole
   > box; it is collapse — not silicon burning — that reaches the temperatures
   > where it does not.
2. **Electron capture.** Free protons liberated by (1), and Fe-peak nuclei
   directly, capture electrons. Each capture removes a pressure-supporting
   electron *and* emits a neutrino that leaves. Yₑ drops, so M_ch drops, so the
   marginally stable core no longer is.

These reinforce each other, and collapse becomes dynamical on a free-fall
timescale of ~0.1 s (t_coll ≈ 0.21/√ρ̄₈ s — Janka 2012).

### The observable end of the chain

Yₑ at collapse onset sets: the iron core mass, the bounce shock location, how
much material the shock must traverse, and therefore whether the explosion
succeeds. Downstream it sets ejecta neutron-richness and hence observed
abundance patterns. The **compactness parameter**
ξ_M = (M/M⊙)/(R(M)/1000 km) at M = 2.5 M⊙, evaluated at core bounce
(O'Connor & Ott 2011) — the standard explodability predictor — is set by
exactly this core structure (§VI.6 for how it is measured).

**This is why every accuracy gate in this repository is written in Yₑ**, and
why the invariants say the weak sector may never be masked, frozen, or
projected away. An emulator that conserves mass and charge perfectly but gets
Yₑ wrong has failed at the only thing that mattered.

## I.3 Why nuclear networks are the computational bottleneck

$$
\frac{d\mathbf{Y}}{dt} = \nu\,\mathbf{R}(\mathbf{Y};\,T,\rho) \qquad n_{\text{species}} \text{ equations}, \; n_{\text{rxn}} \text{ terms}
$$

### The three costs, quantified

**1. Stiffness forces implicit integration.** The stiffness ratio
S = max|Re λ|/min|Re λ| reaches 10¹²–10¹⁵ here (§V.3; "S > 10¹⁵ is not
uncommon in astrophysics" — Hix & Thielemann 1999b). An explicit method needs
~S steps. Implicit is not an optimization, it is a necessity.

**2. Each implicit step costs a Jacobian build plus a linear solve.** Newton
iteration on the backward-Euler / BDF residual requires forming J = ν ∂R/∂Y
(n × n) and factorizing (I − hJ). Dense LU is ≈ 2n³/3 FLOPs, i.e. n³/3
multiply–add pairs (Golub & Van Loan 2013); the table counts the latter:

| Network | n | Dense LU (multiply–adds/factorization) | Ratio |
|---|---|---|---|
| mesa_80 | 80 | 1.7×10⁵ | 1× |
| mesa_151 | 151 | 1.1×10⁶ | **6.7×** |
| mesa_204 | 204 | 2.8×10⁶ | 17× |

**Why sparsity does not rescue you.** The Jacobian is sparse *structurally* —
each species couples only to reaction partners — but LU factorization
**fills in**: eliminating one variable creates couplings between all its
neighbours. Nuclear networks are strongly connected through free nucleons —
`neut` and `h1` each appear in ~41% of mesa_80's 607 reactions (either in
72%), and Hix & Thielemann (1999b) describe exactly this structure as a
"doubly bordered, band diagonal" matrix whose dense border carries the free
n, p, α — so those rows and columns are nearly dense and the fill-in
propagates. Reordering helps but
does not restore the sparsity. On top of that, each *step* takes several Newton
iterations, and each iteration may re-factorize.

**3. Every zone, every step.** A stellar model has 10³–10⁴ zones (Hix &
Thielemann 1999b: "hundreds to thousands" for 1-D models) and takes of order
10⁴–10⁶ timesteps to core collapse. The multiplication is what makes the
network a runtime majority-holder in late burning stages (within the network
step itself, the matrix solve alone consumes 90+% of the time — Hix &
Thielemann 1999b).

**The compromise no one is happy with:** use a network small enough to afford,
and accept that it gets the composition — and therefore Yₑ — wrong.

## I.4 Softwired networks: the compromise MESA makes

MESA's response is the **softwired** network: a fixed species list, with
reaction links assembled at runtime from whichever rates connect those species
(as opposed to *hardwired* fixed lists or *approx* lumped networks — §VI.4).

An immediate methodological consequence: **the reaction count is a measured
quantity, not a documented one.** You have to ask MESA what it built. That is
the entire purpose of the Fortran probe (`src/mesa_probes/probe.f90`) and the
reconciliation of S6, which established 607 / 1518 reactions with
MESA_ONLY = 0.

### The actual shape of the trade-off

Computed from the repository's own isotope lists:

```
                          Z
        30 ┤ zn60●                          ● = in mesa_80 only (6 species)
        29 ┤ cu59●                          ○ = in mesa_151 only (77 species)
        28 ┤ ni56 ni57 ni58 ni59 ○○○○○○     (unmarked) = in both (74 species)
        26 ┤ fe52 fe53 fe54 __ fe56 ○○○○○○
        24 ┤ cr48 cr49 cr50 ○○○○○
        22 ┤ ti44 ti45 ti46 ○○○○○
        21 ┤ sc43 ○○○○○○              ← mesa_80 has ONE scandium
        20 ┤ ca39● ca40 ca41 ca42 ○○○○○○○
        18 ┤ ar35● ar36 ar37 ar38 ○○○
        14 ┤ si27 si28 si29 si30 ○○○
        10 ┤ ne18● ne19 ne20 ne21 ne22 ○
         8 ┤ o14● o15 o16 o17 o18 ○
           └────────────────────────────────────────▶ N
                        (neutron-rich direction ⟶)
```

**The two networks are not "small" and "large" — they are differently shaped.**
This is the most important structural fact in Tier 0, and it is invisible
unless you diff the lists:

- **mesa_151 is not a superset of mesa_80.** Six species — `o14`, `ne18`,
  `ar35`, `ca39`, `cu59`, `zn60` — are in mesa_80 and *absent* from mesa_151.
- mesa_80 reaches **Z = 30 (Zn)** but is narrow in neutron number.
- mesa_151 caps at **Z = 28 (Ni)** but extends deep into neutron-rich
  territory: `fe55`, `fe57`–`fe61`, `ni60`–`ni65`, `ca43`–`ca49`,
  `sc44`–`sc49`, `ti47`–`ti51`, `mn52`–`mn56`.

So the 77 extra species mesa_151 buys are almost entirely **neutron-rich**,
purchased partly by *dropping* the proton-rich upper-Z corner. That is a
deliberate physics choice: neutron-rich isotopes are exactly the β-decay and
electron-capture partners that govern Yₑ. **mesa_151 is not "more of the same"
— it is a network reshaped toward getting the weak sector right.**

### The measured consequence

mesa_80 contains only 6 of 9 electron-capture controllers and **0 of 8**
β-decay partners of the Yₑ-controller set. It is structurally incapable of
representing those *dominant* neutron-rich β-decay chains — though not
weak-one-sided overall: it still carries 19 β⁻ channels and 19 Yₑ-raising
weak reactions in total (RESULTS.md, 2026-07-08).

Two things follow:

- The "zero-shot mesa_80 → mesa_151 size transfer" falsifier is not testing a
  superset extension. It tests whether a model trained on a network with **no**
  β-decay partners can predict a network dominated by them. Expect it to be
  hard, and know the reason.
- The high-Yₑ bottleneck ⁴⁵Sc(p,γ)⁴⁶Ti is a **mesa_151-only** phenomenon.
  mesa_80 has exactly one scandium isotope, ⁴³Sc. You cannot even pose the
  question in mesa_80.

**Predict the bias direction yourself** (§II.8, item 4): with EC present but
the dominant β-decay partners absent, mesa_80's Yₑ evolution is biased
downward — the restoring flux that remains is carried by weaker channels.

## I.5 Why machine-learning emulation

The network step is a **map**, and a well-posed one:

$$
\Phi_{\Delta t} : (T, \rho, \mathbf{X}) \;\mapsto\; (\mathbf{X}', e_{\text{nuc}}, \varepsilon_\nu)
$$

For fixed (T, ρ) it is the time-Δt flow of an *autonomous* ODE — deterministic,
smooth almost everywhere, fixed finite-dimensional input and output. The
autonomy is not free: it is granted by operator splitting, examined properly in
§IV.1.

### The cost model — what speedup would actually matter

Replace an adaptive implicit solve (several Newton iterations × several
substeps × O(n³) each) with one forward pass. For a GNN with K = 5 rounds and
hidden width d over n nodes and m edges, forward cost is O(K(n + m)d²) — linear
in graph size, and **independent of stiffness**.

That last clause is the real prize. Classical cost grows as the problem
stiffens; surrogate cost does not. In the hardest states — precisely where the
network dominates runtime — the ratio is most favourable.

**The strategic payoff:** if the surrogate is accurate, you can afford the
*large* network everywhere, ending the accuracy-vs-cost compromise of §I.4
rather than merely optimizing within it.

### Framing it honestly

This is operator learning with a twist. The operator has exact algebraic
invariants (mass, charge, lepton number), and those invariants are not
decoration — they are the observable (§I.2). Note also what is *not* the
difficulty: expressivity. An MLP can represent this map. The difficulties are
dynamic range, stiffness, exact constraints, and rollout drift (§VI.1).

## I.6 What breaks when an emulator does not conserve

### Mode 1 — accumulation

Let the per-step conservation violation be δ. Linearizing error propagation
about the true trajectory with contraction factor c = ‖∂Φ/∂X‖ gives three
regimes (derived in §IV.3):

| Regime | Accumulated after N steps | log–log slope |
|---|---|---|
| Systematic (c = 1, correlated δ) | N δ | 1 |
| Random walk (c = 1, independent δ) | √N δ | 0.5 |
| Contracting (c < 1) | δ/(1−c) — saturates | → 0 |

At N ≈ 10³–10⁶ steps per stellar model, even δ = 10⁻⁶ is fatal in the
systematic case. This is exactly why the project's per-step Yₑ budget
(≲ 3×10⁻⁶) is stated *under a stated accumulation model*, and why measuring the
slope is the biggest single lever.

**The prediction worth carrying** (§IV.3): silicon burning contracts toward
quasi-equilibrium, so *composition* error should saturate — but Yₑ has no
restoring force, because strong reactions conserve it exactly. Expect the two to
behave differently, and expect the gate to belong on Yₑ.

### Mode 2 — physical inconsistency

Σᵢ Xᵢ ≠ 1 — equivalently Σᵢ Aᵢ Yᵢ ≠ 1, the doc's equation (2) — means the
equation of state, the opacity, and the energy generation are evaluated on a
composition that does not exist. The host code does not error; it silently
produces a wrong star. (Note it is Σ Xᵢ that is normalized, not Σ AᵢXᵢ: the
latter is ≈ Ā ~ 30 and is not conserved by anything.)

### Why soft penalties are the wrong fix

The standard ML response is a loss term λ‖C·dY‖². This gives conservation *on
average, on the training distribution, to within optimization tolerance*. Every
qualifier fails where you need it: rollouts leave the training distribution, and
averages do not constrain individual steps. Worse, λ becomes a hyperparameter
trading accuracy against conservation — you are tuning how much physics to
violate.

**Conservation by construction** removes the trade-off. If the decoder is
dY = νφ and ν is the exact integer stoichiometric matrix, then A·ν = 0
*identically*, so A·dY = 0 for **any** φ — including a randomly initialized,
untrained network. Conservation becomes a property of the architecture, not of
the training. (The same soft-vs-hard contrast has been measured directly in
climate-model emulation: soft-constrained networks show a monotonic
accuracy–conservation trade-off in the penalty weight and large per-sample
violations, while the architecturally constrained variant conserves to machine
precision without losing accuracy — Beucler et al. 2021.)

This is why the conservation test asserts the gate holds **with random flux
heads**, and why it is a blocking gate rather than a metric. Note the further
precision this buys: floating-point analysis (§V.4) shows residual drift is
bounded by ~nε ≈ 3.4×10⁻¹⁴ in float64 — 1.5 decades under the 10⁻¹² gate. In
float32 it would miss by seven orders of magnitude.

## I.7 Why a graph neural network

The reaction network *is* a graph — not an analogy:

- **Nodes**: species (80 or 151), with features (Z, A, binding energy,
  abundance).
- **Edges**: reactions; naturally **bipartite**, with species nodes and
  reaction nodes, since one reaction touches several species (the same
  representation NuGNN adopts — Kim et al. 2026).

Three properties follow — formalism in §VI.2:

1. **Locality.** A reaction couples 2–4 species; information propagates in hops.
   Measured bipartite radius 3, diameter 6 — and since one *round* is
   species → reaction → species, i.e. **2 bipartite hops**, K = 3 rounds already
   spans the graph. K = 5 is the project's choice and carries margin (§VI.2).
2. **Permutation equivariance.** The physics does not depend on species
   ordering; a GNN has this built in, an MLP must learn it, spending capacity on
   a symmetry that could have been free.
3. **Transferability.** Weights attach to node/edge *types*, not to slots in a
   fixed-length vector — which is what makes the mesa_80 → mesa_151 question
   askable at all, though §I.4 says why it is harder than it looks.

**One design point worth noting now:** on the reaction → species half-step, the
correct aggregator is **sum**, because the true update is literally a signed
sum, dY_i = Σ_r ν_ir φ_r. Mean or max would destroy extensivity. The
architecture's aggregator choice is fixed by physics, not by ablation.

The competing published surrogate (a dense feed-forward network) has none of
these; it is a fixed-width map from an (80+2)-vector to an (80+2)-vector —
(T, ρ, X) in, (X′, e_nuc, ε_ν) out — retrained from scratch for 151, with a
separate network per timestep and even a different depth per network size
(Grichener et al. 2025).

## I.8 Where conservation is allowed to live

### Target A

Predict signed net per-reaction fluxes φ, decode through fixed stoichiometry:

$$
d\mathbf{Y} = \nu\,\boldsymbol{\varphi}
$$

Conserves for any φ. Also carries per-reaction structure: you can inspect which
reaction the model thinks is carrying flux, which is what makes bridge and
bottleneck analysis possible at all.

### Target B — and the full projector derivation

Predict dY directly, then project onto the constraint manifold. We want the
**orthogonal projector onto ker C**, where C is the m × (n+3) constraint
matrix (the construction is standard linear algebra — e.g. Golub & Van Loan
2013).

Seek P such that (i) CP = 0, (ii) P v = v for v ∈ ker C, (iii) P = Pᵀ. Decompose
any vector into row-space and null-space parts. The row space of C is spanned by
Cᵀ, so write the row-space component as Cᵀa. Requiring C(v − Cᵀa) = 0 gives

$$
C\mathbf{v} = CC^{\mathsf{T}}\mathbf{a} \quad\implies\quad \mathbf{a} = (CC^{\mathsf{T}})^{-1} C\mathbf{v} \qquad (CC^{\mathsf{T}} \text{ invertible} \iff C \text{ full row rank})
$$

Hence the null-space component is

$$
\mathbf{v} - C^{\mathsf{T}}(CC^{\mathsf{T}})^{-1}C\mathbf{v} \quad\implies\quad \boxed{\;P = I - C^{\mathsf{T}}(CC^{\mathsf{T}})^{-1}C\;}
$$

Verify the three properties:

- **CP** = C − CCᵀ(CCᵀ)⁻¹C = C − C = 0 ✓
- **P²** = I − 2Cᵀ(CCᵀ)⁻¹C + Cᵀ(CCᵀ)⁻¹CCᵀ(CCᵀ)⁻¹C = I − Cᵀ(CCᵀ)⁻¹C = P ✓
- **Pᵀ** = P, since (CCᵀ)⁻¹ is symmetric ✓
- **rank P** = (n+3) − rank C ✓

Note the requirement **C must be full row rank** — otherwise CCᵀ is singular.
This is why `tests/test_projector.py` includes a rank-deficient-C rejection
test: it guards the existence condition of the derivation, not just input
validation. In practice the implementation uses a QR null-space form, which is
numerically better conditioned than forming (CCᵀ)⁻¹ explicitly.

### The critical theorem — and the documented failure mode

P is valid **only in a linear output space**. Suppose you predict in a
signed-log space, u = sinh⁻¹(dY/s), and apply P there. Then you have enforced

$$
\sum_i A_i u_i = 0
$$

which says *nothing whatever* about Σᵢ Aᵢ dYᵢ, because a sum constraint does not
commute with a nonlinear map. You get a beautifully conserved quantity in a
space with no physical meaning, and unconserved physics.

**Make the failure concrete.** Take two species with A = 1 and dY = ±10⁻³, so
Σ A dY = 0 exactly. Apply u = sinh⁻¹(dY/s) with s = 10⁻⁶: u = ±sinh⁻¹(10³) ≈
±7.6, and Σ A u = 0 too — the symmetric case survives. Now take
(+2×10⁻³, −10⁻³, −10⁻³): Σ A dY = 0 still, but
Σ A u = 8.29 − 7.60 − 7.60 = −6.9 ≠ 0. Enforcing Σ A u = 0 would therefore
*require* Σ A dY ≠ 0. The constraint sets are genuinely different manifolds.

The rule that follows:

> **Conservation lives in the decode step, never inside latent dynamics.**
> No nonlinear transform may sit between the conservation map and the output.

Internal asinh/signed-log latents are fine — they just may never be the space
where a sum constraint is evaluated.

## I.9 Self-check for Part I

1. Explain why the burning-stage durations shorten by orders of magnitude,
   naming the mechanism and the temperature scaling.
2. Derive M_ch ∝ Yₑ² from the ultra-relativistic degenerate EOS and the n = 3
   polytrope. Where does the density-independence of M come from?
3. State the two coupled runaways that trigger collapse and explain how each
   reduces pressure support.
4. Why does sparsity fail to make the Jacobian factorization cheap? Name the
   specific species responsible.
5. Give the one-sentence argument for why soft conservation penalties cannot
   substitute for architectural conservation, referencing rollout.
6. Derive P = I − Cᵀ(CCᵀ)⁻¹C and verify idempotence. What breaks if C is rank
   deficient, and which test guards it?

---

# Part II (S0) — Species, abundances, and the (N,Z) plane

## II.1 Nuclide bookkeeping

A nuclide is specified by (Z, N): Z protons, N neutrons, A = Z + N.

- Names are **MESA/pynucastro chem ids**, lowercase: `si28`, `fe56`, `he4`, and
  critically `neut` for the free neutron, `h1` for the free proton.
- Free nucleons are **network species**, not a background bath. `neut` carries
  (Z=0, A=1); `h1` carries (Z=1, A=1). At silicon-burning temperatures
  photodisintegration liberates free nucleons in abundance — the Sobol initial
  compositions carry median X_neut ≈ 1.7×10⁻². They participate in the same
  algebra as every other species, and this is not incidental: §I.1 established
  that Si burning *is* the traffic in free nucleons and α particles.

## II.2 Binding energy and why the iron peak exists

$$
B(Z,N) = \bigl[Z m_p + N m_n - m(Z,N)\bigr]\,c^2
$$

Semi-empirical mass formula (Krane 1988; this coefficient set is the
least-squares fit of Eisberg & Resnick 1985):

$$
B \approx a_V A - a_S A^{2/3} - a_C \frac{Z(Z-1)}{A^{1/3}} - a_A \frac{(A-2Z)^2}{A} \pm \delta
$$

| Term | Coefficient | Effect |
|---|---|---|
| Volume | a_V ≈ 15.8 MeV | grows as A — favours heavy nuclei |
| Surface | a_S ≈ 18.3 | penalizes small A — B/A rises steeply at low A |
| Coulomb | a_C ≈ 0.714 | grows as Z²/A^(1/3) — penalizes heavy nuclei |
| Asymmetry | a_A ≈ 23.2 | penalizes N ≠ Z |
| Pairing | ±δ | even–even favoured |

Surface losses fade with A while Coulomb losses grow, so B/A peaks near
A ≈ 56–62 and declines. Fusion is exothermic below the peak, endothermic above.
**This is why silicon burning is the last stage.**

> ⚠ **The mass-excess trap.** Data tables give the mass *excess* Δ, and masses
> are *atomic*. Converting takes B = ZΔ(¹H) + NΔ(n) − Δ, and Q-values are
> Q = ΣΔ_in − ΣΔ_out. Worked examples and a verification exercise against
> `configs/reactions_*_mesa.yaml` are in §0.3.1.

### The subtlety to internalize now

The most bound nuclide is ⁶²Ni (B/A = 8.795 MeV; Fewell 1995), the most bound
at A = 56 is ⁵⁶Fe (8.790) — yet silicon burning at Yₑ ≈ 0.5 produces **⁵⁶Ni**
(8.643). The
reason: the equilibrium composition maximizes binding *subject to the Yₑ
constraint*. At Yₑ = 0.5 matter cannot reach ⁵⁶Fe (Yₑ = 26/56 = 0.464) without
weak reactions, which are slow. ⁵⁶Ni is the most bound nuclide with Z = N, and
doubly magic on top of that (§0.3.2).

**Carry this forward:** "the equilibrium composition" is always *at a given Yₑ*.
That is why the NSE solver has exactly two constraints, ΣX = 1 and Yₑ, and why
the label-pathology finding is stated as a distance from NSE *at the label's own
Yₑ*.

## II.3 From number density to molar abundance — derive Y = X/A

The mass density in species i is ρX_i, and each nucleus has mass ≈ A_i m_u:

$$
n_i = \frac{\rho X_i}{A_i m_u} = \frac{\rho N_A X_i}{A_i}
$$

using m_u = 1/N_A in cgs. Define the **molar abundance**:

$$
Y_i \equiv \frac{X_i}{A_i} \qquad \text{so} \qquad n_i = \rho N_A Y_i \tag{1}
$$

The mass-fraction normalization becomes

$$
\sum_i X_i = 1 \qquad \iff \qquad \sum_i A_i Y_i = 1 \tag{2}
$$

Equation (2) is the baryon conservation law the entire conservation layer is
built on. It is **linear in Y** — not an accident; it is the reason Y is the
right variable (and the standard network variable: Hix & Thielemann 1999b
introduce Y_i = n_i/ρN_A for exactly these reasons). A pedantic aside on
m_u = 1/N_A: exact in the pre-2019 cgs convention; since the 2019 SI
redefinition, m_u N_A = 1 g/mol × (1 + 1.05×10⁻⁹) (CODATA 2022) — six orders
below anything tabulated here.

**A precision note.** Strictly A_i m_u is not the nuclear mass. The deviation is
exactly the mass excess of §0.3.1, (M − A u)/(A u) = Δ/(A · 931.494 MeV), and it
is worth tabulating because its *sign and size are both counter-intuitive*:

| | `neut` | `h1` | `he4` | `si28` | `fe56` |
|---|---|---|---|---|---|
| (M − A u)/(A u) | **+0.87%** | **+0.78%** | +0.065% | −0.082% | −0.116% |

Two traps here (values from AME2020; note these are atomic-convention numbers
— the h1 entry includes the electron, and the bare proton would read +0.73%).
First, the largest deviations belong to the **free nucleons**,
and they are **positive** — n and p are *heavier* than A·u, because the atomic
mass unit is defined by ¹²C, which is itself bound. Second, for the heavy nuclei
that carry the mass the deviation is only ~10⁻³, an order of magnitude smaller.
The ~0.9% figure that is easy to reach for is B/(A m_u c²) — the defect relative
to *free constituent nucleons* — which is a different quantity and answers a
different question.

Using the integer A means Σ A_i Y_i = 1 holds *exactly by definition* rather than
approximately, and the mass defect is accounted separately in the energy equation
(e_nuc = −N_A Σ m_i c² ΔY_i, with the mass excess usable in place of m_i c²
because nucleon number is conserved — Hix & Thielemann 1999b, eq. 12). This is a deliberate bookkeeping split: **exact
integer arithmetic for the constraint, mass excesses for the energy.** It is what
makes A·ν = 0 hold to machine zero rather than to the ~10⁻³ set by the heavy-
nucleus column of the table above.

**In the code:** `src/gnn_nucleo/data/subsample.py::compute_ye_initial` is
`X @ (Z/A)`, i.e. exactly Σ Zᵢ Xᵢ/Aᵢ — a one-line implementation of (1) and (4).

## II.4 Why networks integrate Y and not X — the real reason

### Argument 1 — Y is a per-baryon quantity, invariant under compression

From (1), Y_i = n_i/(ρN_A) = (number of species i) / (number of baryons).
Compressing or expanding a fluid element changes ρ and every n_i in proportion,
leaving every Y_i untouched. So in the Lagrangian frame:

$$
\left.\frac{dY_i}{dt}\right|_{\text{total}} = \left.\frac{dY_i}{dt}\right|_{\text{reactions}}
$$

with no advection or compression term. Working in n_i you would carry a spurious
−n_i(ρ̇/ρ) term in every equation; in X you would carry it too, hidden inside a
nonlinear rate expression.

### Argument 2 — the constraint stays linear with constant coefficients

$$
\begin{aligned}
\text{In } Y: &\quad \sum_i A_i Y_i = 1 && \text{coefficients } A_i \text{ are integers, fixed forever}\\
\text{In } n: &\quad \sum_i A_i n_i = \rho N_A && \text{right-hand side is time-dependent}
\end{aligned}
$$

This is what makes the conservation layer a *fixed* linear operator, precomputed
once and applied in decode. In any other variable the constraint matrix would be
state-dependent and the architecture would collapse. Trace the dependency:
linear constraint → fixed ν and C → exact A·ν = 0 → conservation survives a
random φ → conservation-by-construction is possible at all.

### The network ODE

With rate R_j [mol g⁻¹ s⁻¹] and ν_ij the net stoichiometric coefficient
(products +, reactants −):

$$
\frac{dY_i}{dt} = \sum_j \nu_{ij} R_j \qquad \iff \qquad \frac{d\mathbf{Y}}{dt} = \nu\,\mathbf{R} \tag{3}
$$

For a two-body reaction 1 + 2 → 3, r = n₁n₂⟨σv⟩/(1+δ₁₂) per unit volume;
converting with (1) and R = r/(ρN_A):

$$
R = \frac{\rho N_A Y_1 Y_2 \langle\sigma v\rangle}{1+\delta_{12}}
$$

— one net power of N_A (Hix & Thielemann 1999b, eq. 10: two-body terms carry
ρN_A, three-body ρ²N_A²); equivalently R = ρY₁Y₂·[N_A⟨σv⟩]/(1+δ₁₂), where
N_A⟨σv⟩ is the tabulated REACLIB quantity.

The general form — density exponent ρ^(N−1) for N reactants, 1/n! for n
identical reactants — is derived in S2. Note now only that R is a **product of
abundances times a function of (T, ρ)**, which makes ∂R/∂Y analytically
available by the product rule — the fact S10's integrator Jacobian rests on.

## II.5 The electron fraction Yₑ — the central variable

### Derivation

Charge neutrality: electron number density equals total proton number density,

$$
n_e = \sum_i Z_i n_i = \rho N_A \sum_i Z_i Y_i
$$

Define, in exact parallel to (1):

$$
Y_e \equiv \frac{n_e}{\rho N_A} = \sum_i Z_i Y_i = \sum_i \frac{Z_i X_i}{A_i} \tag{4}
$$

Yₑ is the number of electrons per baryon. For any nuclide with Z = A/2,
Z_i/A_i = 1/2, so symmetric matter has Yₑ = 0.5 exactly. Yₑ < 0.5 is
neutron-rich.

### The neutron excess

$$
\eta = \sum_i (N_i - Z_i)\,Y_i = \sum_i A_i Y_i - 2\sum_i Z_i Y_i = 1 - 2Y_e \tag{5}
$$

So η and Yₑ carry the same information (η is the standard neutron excess —
Hix & Thielemann 1999b). The literature uses both, and confusing
them is a real source of misread thresholds — this repo carries an explicit open
item on exactly that ambiguity in a cited paper.

**Percentages quoted "in η" and "in Yₑ" are not interchangeable**, and the
amplification is larger than it first looks. Differentiating (5) gives
δη = **−2** δYₑ, so the relative-error amplification is

$$
\frac{|\delta\eta|/\eta}{|\delta Y_e|/Y_e} \;=\; \frac{2Y_e}{\eta} \;=\; \frac{2Y_e}{1-2Y_e}
$$

At Yₑ = 0.47, η = 0.06 and the factor is 2(0.47)/0.06 = **15.7**: a 1% error in
Yₑ is a **~16%** error in η, not 8%. (Dropping the factor of 2 from (5) is the
easy way to get 7.8 and it is wrong.) The amplification diverges as Yₑ → 0.5 —
precisely the upper edge of the regime box — which is why η is the worse variable
to write a tolerance in here, and why every gate in this project is stated in Yₑ.

### What changes Yₑ

Strong and electromagnetic reactions conserve Z and A separately, so they cannot
change Yₑ at all. Only **weak reactions** can:

| Process | Effect on (Z, N) | Effect on Yₑ | Emits |
|---|---|---|---|
| electron capture, e⁻ + p → n + ν | Z−1, N+1 | **decreases** | ν |
| β⁺ decay, p → n + e⁺ + ν | Z−1, N+1 | **decreases** | ν |
| β⁻ decay, n → p + e⁻ + ν̄ | Z+1, N−1 | **increases** | ν̄ |
| positron capture, e⁺ + n → p + ν̄ | Z+1, N−1 | **increases** | ν̄ |

All at **fixed A** (process definitions as in Langanke & Martínez-Pinedo 2000,
2003; the grouping is verbatim in Heger et al. 2001 — EC and β⁺ decay decrease
Yₑ, positron capture and β⁻ decay increase it). Note the pairing carefully,
because it is easy to get backwards: the processes group by **which way Z
moves**, not by which lepton is named. EC and β⁺ decay both *lower* Z and Yₑ and emit a ν; β⁻ decay and positron
*capture* both *raise* Z and Yₑ and emit a ν̄. Grouping "β⁺ decay / positron
capture" together — the intuitive but wrong reading — puts a Yₑ-raising process
in the Yₑ-lowering row, which is exactly the sign error the project's invariant
#3 exists to catch.

**What the code carries.** `graph/stoich.py::WEAK_LEDGERS` has three keys —
`electron_capture`, `beta_neg`, `beta_pos` — with EC and β⁺ sharing the ledger
signature (−1, +1, 0) under the annihilated-positron convention (the emitted
positron annihilates on a plasma electron, so the net electron-ledger effect is
−1). Positron capture has no separate entry: it is folded into the *evaluated*
β⁻-direction weak rate — MESA's weaklib sums decay + capture per direction at
evaluation time, although the raw tables do carry a separate positron-capture
column before that sum (and its contribution is small at these conditions —
Langanke & Martínez-Pinedo 2000; Heger et al. 2001 neglected it outright). So the fourth row above is physics you
must know in order to read a weak-rate table correctly, not a column you will
find in `weak_mask`.

Hence a structural statement you should verify against the exported matrix:

> A column of ν is a weak column **if and only if** it moves Yₑ, i.e.
> Σᵢ Zᵢ ν_ij ≠ 0 while Σᵢ Aᵢ ν_ij = 0 — with **both sums taken over the nuclei
> block only.** On the extended ν̃ (which appends the e⁻/ν/ν̄ ledger rows) the
> charge sum is zero for *every* column, weak included, because charge is
> conserved by the reaction.

Verify it, but do not adopt it as a *definition*: `graph/stoich.py` assigns the
lepton ledger from the rate's `weak_type` and warns explicitly against
back-deriving it from Z·ν, "that would make the charge-to-lepton closure a
tautology". The eligible-mask machinery is built structurally from `weak_mask`
at construction time for the same reason.

### Why silicon burning drives Yₑ down — now quantitatively

Electron capture on free protons requires total electron energy
E_e ≥ (m_n − m_p)c² = 1.293 MeV. In a degenerate gas the available energy is
E_F, and setting E_F = 1.293 MeV gives a **critical density ρ ≈ 2.4×10⁷ g/cm³**
at Yₑ = 0.5 (§0.1.5).

That is *inside the regime box, near its lower edge*. Below it captures are
thermally suppressed; above it they are degeneracy-driven and vigorous. At
ρ = 10⁸ the Fermi energy is 1.97 MeV — comfortably above threshold — and at 10⁹
it is 4.1 MeV.

The emitted neutrinos escape (§0.4.2), so nothing accumulates to push the weak
sector back toward equilibrium: **Yₑ ratchets downward in net**, and by §I.2 the
Chandrasekhar mass follows it. The individual channels still run both ways —
β⁻ decay raises Yₑ every step — so "monotonic" is a statement about the sum over
weak columns, not about any one of them (§0.4.2). That net one-way ratchet over
~10⁵ s is the physical signal this entire project exists to reproduce accurately.

### The lepton ledger

Because neutrinos leave, bookkeeping must be explicit. C carries three rows:

1. **baryon** — Aᵢ on nuclei
2. **charge** — Zᵢ on nuclei, **−1 on the electron column**, 0 on neutrinos
3. **lepton number** — e⁻ +1, ν +1, ν̄ −1

The projector therefore acts on the **extended** vector
[dY_nuclei…, dY_e⁻, dY_ν, dY_ν̄].

**Why the extension is not optional.** Projecting a nuclei-only vector would
force Σ Zᵢ dYᵢ = 0 — precisely the statement that Yₑ never changes. It would
silently erase the physical signal. This is the concrete content of the
invariant "a design that zeroes dYₑ to make drift residuals vanish is wrong":
zeroing the signal is the *easy* way to pass a conservation test, and the
architecture must make it impossible by accident. `test_projector.py` carries a
dedicated `test_projection_preserves_weak_dYe_signal` for exactly this.

Note the conceptual subtlety the third row encodes: lepton number is *conserved
by the reaction*, and then the neutrino physically leaves the zone. The ledger
lets you state both facts without contradiction.

## II.6 The network as a bipartite graph

Two node types:

- **Isotope nodes** I: one per species (80 or 151).
- **Reaction nodes** R: one per reaction (607 or 1518 after reconciliation).

Two edge types:

- **I → R** reactant incidence.
- **R → I** signed product incidence, carrying the stoichiometric coefficient.

ν is exactly the (signed, summed) biadjacency matrix — the graph and the linear
algebra are two views of one object.

**Why bipartite rather than species-only.** A reaction with three reactants is a
genuine 3-way interaction — a **hyperedge**. Collapsing it to pairwise I→I edges
loses the information that the three must act *jointly*: from the projected
graph you cannot tell whether {a,b,c} came from one ternary reaction or three
binary ones, and the rate expressions differ (ρ² Y_aY_bY_c versus sums of
ρ Y·Y). The bipartite form represents the hyperedge exactly. The cost is a
doubled hop count: an I→I step corresponds to two bipartite hops along an
alternating path, which is why the bipartite diameter measures 6 while the
derived I→I view is measured at diameter 4 (RESULTS.md — not exactly half,
because the projection is its own graph object). One message-passing round
traverses both halves — see §VI.2 for the depth arithmetic and for why the
shipped K = 5 is margin rather than a minimum.

**Forward and reverse are separate columns**, not one signed column. MESA
softwires them separately and pynucastro treats them as distinct rates, so the
canonical key convention makes a directed key per direction, and `pair_col`
recovers the pairing downstream. This is exactly what makes κ computable per
pair — and note that it is a *choice*: a signed-column representation would make
conservation just as exact but would destroy the ability to measure detailed
balance, because f⁺ and f⁻ would already have been summed.

## II.7 Code walkthrough

**`configs/isotopes_mesa80.yaml` / `isotopes_mesa151.yaml`** — authoritative
species tables. Read the provenance headers: lists come from the *data column
headers*, cross-checked against the published paper's appendix table, which
**omits ⁴¹Ca**. Resolution recorded: "paper typo; data is authoritative." The
working principle it establishes — when paper and data disagree, the data wins,
and the disagreement is recorded rather than smoothed over — recurs throughout
the project.

**`graph/isotopes.py`** — `IsotopeTable`, `load_isotope_table`,
`canonical_network`. The job is naming discipline: YAML names and order define
ν's row order, the npz `species` array, and graph node names, matching the
training-CSV column suffixes `initial_<name>`. pynucastro's capitalization
(`"Neut"`, `"H1"`) is **never stored** — mapping is fail-loud at the boundary.

**Oracle:** `tests/test_schema.py::test_network_species_counts`

**Notebook:** `01-data-inventory` Fig 2 ((N,Z) plane), Fig 3 (Yₑ-controller
membership)

## II.8 Self-check for S0

1. Derive Y = X/A and Σ Aᵢ Yᵢ = 1 from nᵢ = ρN_A Xᵢ/Aᵢ without looking.
2. Show that the *only* columns of ν with Σ Zᵢ ν_ij ≠ 0 are weak columns, and
   confirm numerically against the exported `weak_mask`.
3. Given M_ch = 5.83 Yₑ² M⊙, compute the fractional change for
   Yₑ: 0.50 → 0.47 → 0.45. Then compute what per-step Yₑ error, accumulated
   systematically over 1.6×10³ steps, produces a 1% M_ch error. Compare to the
   3×10⁻⁶ gate.
4. Using the diff in §I.4: list three β-decay chains representable in mesa_151
   but not mesa_80. Predict which direction mesa_80's Yₑ evolution is biased.
5. Explain why `neut` must be a network species rather than a bath, in terms of
   equation (2).
6. Explain the §II.3 precision note: why use integer A in the constraint when
   M ≠ A·u? Compute (M − A u)/(A u) yourself for `neut`, `he4`, and `fe56` from
   the mass excesses in §0.3.1 — get the signs right — and say which of those
   numbers sets the 10⁻³ that A·ν = 0 would otherwise be limited to. What breaks
   if you use real masses in the constraint row instead?
7. Construct a three-species example showing that Σ A u = 0 and Σ A dY = 0 are
   different constraints under u = sinh⁻¹(dY/s). (Sketched in §I.8.)
8. Explain what is lost by projecting the bipartite graph onto species-only
   edges, using a concrete ternary reaction from the network.

---

# Part III (S1) — The dataset as a physical object

The dataset is a *discretization of an operator*, and every design choice in it
encodes a physical assumption. Study it as physics.

## III.1 What one record is

> **One record = one (state, dt) pair.**

- **Inputs**: (log T, log ρ, X, dt)
- **Labels**: (X′, e_nuc, ε_ν)

Each underlying state is stepped at **nine** timesteps, giving nine records per
state. So the dataset does not sample a single map — it samples the operator
*family* {Φ_Δt} at nine Δt values over the same initial conditions. What is being
taught is the flow map *as a function of Δt*, which is a strictly harder object
than a fixed-step map and a strictly more useful one: a host code chooses its
own timestep.

**A consequence nobody exploits yet.** For an autonomous flow,
Φ_{s+t} = Φ_s ∘ Φ_t. Having nine Δt values on the *same* states makes this a
free, label-independent consistency test of any learned Φ̂ — arguably the
cheapest available diagnostic of rollout health (§IV.3).

In code: `data/schema.py::StepInputs` and `StepLabels`.
`StepInputs.__post_init__` validates `dt_seconds` against the **measured** grid
to `rel_tol=1e-9` — passing a nominal 10^k value is rejected (§III.3).

## III.2 The regime box, derived rather than assumed

$$
\begin{aligned}
T &= 1.6\text{–}7.9\ \mathrm{GK} \qquad (10^{9.2}\text{–}10^{9.9}\ \mathrm{K})\\
\rho &= 10^{7}\text{–}10^{9}\ \mathrm{g\,cm^{-3}}\\
0.45 &< Y_e < 0.5
\end{aligned}
$$

Each bound is physical, and now quantitative:

| Edge | Value | Derivation |
|---|---|---|
| T lower | 1.6 GK | Below this, Si photodisintegration is negligible — you are in oxygen burning, a different network |
| T upper | 7.9 GK | Above this, matter is unambiguously in full NSE: composition is *algebraic* in (T,ρ,Yₑ), so no ODE — and no emulator — is needed. **The emulator's domain ends where equilibrium begins**; see the caveat below on where it actually begins |
| ρ lower | 10⁷ | Just below the free-proton EC threshold ρ ≈ 2.4×10⁷ (§0.1.5) — the box brackets the turn-on of the Yₑ-controlling process |
| ρ upper | 10⁹ | Strongly degenerate (E_F/kT ≈ 10); above this you are into collapse |
| Yₑ upper | 0.5 | Oxygen-burning ash is near-symmetric |
| Yₑ lower | 0.45 | By here the core is collapsing — the box covers the *entire* physical excursion |

Also note what the box implies about screening: Γ ranges ≈ 0.4–25 across it
(varying with ρ^{1/3}/T, so the temperature edges dominate), the
intermediate-coupling regime where neither weak- nor strong-screening
asymptotics apply (§0.1.4). That is the derivation behind pinning
`screening_mode = 'chugunov'`.

> ⚠ **Do not read the T-upper row backwards.** "Above 7.9 GK it is NSE" is true;
> "below 7.9 GK it is not NSE" is false. At these densities NSE is effectively
> established from ≈5 GK upward (the NSE relaxation time
> τ ≈ exp(196.02/T₉ − 41.645) s falls from ~10³ s at 4 GK to ~0.1 s at 5 GK —
> Calder et al. 2007), so the top ~3 GK of the box is *already*
> algebraic and the emulator is being trained on states it does not strictly need
> to learn. 7.9 GK is therefore a **conservative** edge — chosen so the box
> certainly contains the whole non-equilibrium region — not the location of the
> NSE transition. The honest statement of the T-upper rationale is "safely past
> the transition", and §III.11 item 5 is exactly the exercise of noticing this.

**QSE onset ≈ 3–3.3 GK**, kill-test priority window **3.3–5 GK** — where
clustering has appeared but full NSE has not taken over. Physically richest and
hardest.

In code: `crosscheck/grids.py::state_grid` is the single source;
`data/subsample.py` lifts the same edges into strata.

## III.3 The dt grid — and why nominal values are a lie

Nine nominal steps: 10⁻⁶ … 10² s, one per decade (`DT_GRID_SECONDS`,
`DT_LABELS`).

**Why this range?** It covers *most* of the timesteps a stellar evolution code
takes during silicon burning — burning-limited steps once T ≳ 3 GK, up to
~10² s early on when other physics limits — which is exactly the claim the
source paper makes (Grichener et al. 2025: "encompassing most timesteps taken
by the MESA simulations"). It is not the whole envelope: fully-coupled MESA
steps near collapse drop below 10⁻¹⁰ s (Jermyn et al. 2023). Nine decades is
the operator's main usage envelope.

**The trap.** Nominal values are **labels only**. Real steps deviate by up to
~5% and **differ between networks** — the "1e2" file is 105.08 s for mesa_80 but
102.93 s for mesa_151. Using 100 s where the data means 105.08 s is a 5% error
in the independent variable of every fit.

```
Measured values:  configs/dt_grid_measured.yaml
Loader:           schema.load_measured_dt()
Producer:         scripts/check_training_csvs.py (from the real Age column)
```

### Two deeper traps at opposite ends of the grid

**Short end — the linearity premise is void.** The premise that dt = 10⁻⁶ s is a
"small, linear step" is false *everywhere in this box*: 99.99% of
(state, isotope) cells have destruction timescale τᵢ = Yᵢ/|Ẏᵢ| shorter than dt₁,
because Sobol initial compositions carry free nucleons. Every label — even the
shortest — encodes a full stiff **relaxation**, not a linear increment. This is
why the flux target Φ is *time-integrated*, Φ = ∫φ dt, rather than an
instantaneous rate.

**Long end — the splitting premise gets shaky.** The labels are constant-(T,ρ)
burns. The photodisintegration rates that control Si burning have temperature
sensitivity ν_T = ∂lnλ/∂lnT ≈ 20–40 (ν_T ≈ Q/kT with Q ≈ 8–12 MeV at
T₉ = 3–5; charged-particle captures are milder, ~4–17), so a 3% temperature
rise can double a dominant rate. At Δt = 10² s in vigorous burning, the
energy released may well raise T appreciably — meaning a constant-T burn and a
self-heating burn are different operators. Whether the host code calls the
network the same way at large Δt is a genuine open question, developed in §IV.1.

## III.4 Sobol sampling: the theory, and its limits here

### Discrepancy

For P = {x₁…x_N} ⊂ [0,1]^d, the star discrepancy is

$$
D^*_N(P) = \sup_{B \text{ anchored at origin}} \left|\frac{\#(P \cap B)}{N} - \mathrm{vol}(B)\right|
$$

The **Koksma–Hlawka inequality** bounds integration error by it (Niederreiter
1992; Owen & Rudolf 2021):

$$
\left|\frac{1}{N}\sum_k f(x_k) - \int f\right| \;\leq\; V(f)\cdot D^*_N(P)
$$

with V(f) the Hardy–Krause variation. Lower discrepancy ⟹ better coverage, for
every function of bounded variation simultaneously.

| Design | D*_N |
|---|---|
| i.i.d. uniform | O(N^(−1/2) √(log log N)) — probabilistic (Chung 1949) |
| Sobol (digital (t,m,s)-net) | O((log N)^d / N) — deterministic (Sobol' 1967; Niederreiter 1992) |

(The (log N)^d/N rate is the arbitrary-prefix sequence bound; the fixed
N = 2^m net bound is one log factor sharper, O((log N)^{d−1}/N) — Owen 2022.)

### How Sobol is actually built

Each dimension j has a set of **direction numbers** v_{j,1}, v_{j,2}, …
generated from a primitive polynomial over GF(2) via a recurrence (Sobol'
1967; implementations differ in their direction numbers — Bratley & Fox 1988;
Joe & Kuo 2008). The n-th
point's j-th coordinate is

$$
x_{n,j} = \bigoplus_k b_k\,v_{j,k} \qquad (\oplus = \text{bitwise XOR},\; b_k = \text{bits of } n)
$$

The construction guarantees exact equidistribution in **dyadic boxes**: an
elementary box of the form [k/2^a, (k+1)/2^a) × … contains exactly the right
number of points once N is a power of 2 — though only down to the resolution
set by the net's t parameter (boxes of volume ≥ 2^{t−m} for N = 2^m; t grows
with dimension, so at d ≈ 82 the guaranteed resolution is coarse —
Niederreiter 1992; Owen 2022). This is why **N = 2²⁰** — powers of two are
where the guarantee is tight, and taking a non-power-of-2 prefix degrades it
(Owen 2022).

### ⚠ The gap you must fill honestly

Sampled dimension is not small: 2 thermodynamic + 80 or 151 composition
coordinates ⟹ d ≈ 82 or 153. At d = 82, (log N)^d/N with N = 2²⁰ is
astronomically larger than 1 — **the asymptotic bound is vacuous**.

The real justification in high dimension is *low effective dimension*
(Caflisch, Morokoff & Owen 1997): the
integrand depends strongly on a few coordinates and their low-order
interactions, and Sobol's low-order projections are well-distributed. This is an
assumption, not a theorem.

Write down for yourself: which coordinates dominate, and does composition really
have low effective dimension when normalized to Σ X = 1 (which removes one
degree of freedom and correlates all the rest)? And note the sharper version of
the concern from §IV.2: uniform coverage of composition space is coverage of a
set that is *mostly physically unreachable*.

### Scrambling

Owen scrambling applies random permutations to the digits of each coordinate,
preserving equidistribution while making the estimator **unbiased** and
improving RMSE from O(N⁻¹) toward O(N^(−3/2)) for smooth integrands — the
exact rate is O(N^(−3/2)(log N)^((d−1)/2)) (Owen 1997a,b; corrected in Owen
2008). It also breaks the regular lattice artifacts plain Sobol shows in some
2-D projections (the motivation for the Joe & Kuo 2008 direction numbers).

### The consequence that shapes this entire repository

The grid used an **unseeded** scrambled sampler: permutations drawn from system
entropy and never recorded. Therefore:

> **The Sobol grid is NON-REGENERABLE. The shipped file is the only ground
> truth.**

Everything follows: anything keyed to states persists **explicit state_id
lists** (`configs/step5_subsample_*_ids.json`), never a re-samplable recipe;
joins happen on `state_id` only; and generating more same-distribution data is
impossible — future data needs a fresh sampling design.

Study `data/subsample.py` with this in mind: it looks like over-engineering
until you realize a re-drawn sample would be a *different* sample, and every
measured number keyed to it would become unreproducible.

## III.5 The identity problem — why `state_id`

The raw CSVs carry **no sample id**. Three measured facts resolve identity:

1. The nine dt files are **exactly row-aligned** — row i holds the same
   (logT, logRho, initial_*) in every file.
2. **(logT, logRho) is NOT unique**: 154,405 of 1,041,400 rows collide, because
   those columns are rounded to 3 decimals.
3. The **full initial state has zero duplicates**.

Therefore `state_id` = row index (0-based); `(state_id, dt_index)` identifies a
record.

### Do this estimate yourself

Rounding logT ∈ [9.2, 9.9] and logρ ∈ [7, 9] to 3 decimals gives ~700 × ~2000 ≈
1.4×10⁶ cells for ~1.04×10⁶ rows, so Poisson occupancy λ ≈ 0.74.

**Be precise about which fraction you are estimating** — there are two, they
differ by nearly 2×, and picking the wrong one changes the conclusion:

| Quantity | Formula | Value at λ = 0.74 |
|---|---|---|
| Rows **living in** a cell with ≥2 rows | 1 − e^(−λ) | 0.52 |
| **Excess** rows (total − distinct occupied cells) | 1 − (1−e^(−λ))/λ | 0.29 |

The measured 154,405 / 1,041,400 = **0.148** is a `duplicated()`-style count —
rows minus distinct initial states — so the second row is the right comparison,
and the measurement comes in at about **half** the Poisson expectation. Against
the first row it would look 3.5× low, which would be comparing two different
things.

The direction is itself evidence: a low-discrepancy point set is *more uniform*
than random, so it collides less. The pigeonhole argument survives regardless —
collisions are structural, and coordinate joins are forbidden.

**In code:** `data/labels.py::join_on_state_id` **refuses** frames that are not
state_id-indexed. The invariant is not documented and hoped for; a coordinate
join is *inexpressible*. Note the pattern — the repo uses it repeatedly
(`guards.py`, `eligible_mask`, the screened-κ refusal in `distributions.py`).

## III.6 Label noise, floors, and censoring

### float32 labels

Upstream models and label tensors are float32: ε ≈ 1.19×10⁻⁷. Any agreement band
must be at least ~3ε(X_i + X_f) wide, or you are measuring rounding — which is
exactly the band used in the handshake and integrator tests. This project parses
raw CSVs as **float64** and does conservation arithmetic in float64; float32 is
permitted in model internals only (§V.4 derives why).

### The 1×10⁻¹⁵ floor

`final_*` mass fractions are clamped at `FINAL_X_FLOOR = 1e-15` upstream before
logs were taken, and the floor is *exactly attained* in both networks. So:

> Values at the floor are **censored, not physical.**

A value at 10⁻¹⁵ means "≤ 10⁻¹⁵", not "= 10⁻¹⁵". The statistically correct
treatment is a one-sided (censored) likelihood, not a squared error against the
clamp. Note also the dynamic range: X spans 15 decades, so plain MSE in linear X
is dominated entirely by the handful of species near unity (§VI.3).

### Energy normalization

`eps_nuc` and `eps_nu` in the training CSVs are stored **divided by 10¹⁶**
(`EPS_NORMALIZATION`); loaders must multiply back. And `eps_nuc` is
**integrated** [erg/g] over the step while `eps_nu` is a **rate** [erg/g/s] —
different units in adjacent columns.

**The convention trap.** The *trajectory* (test-set) files use a **different**
convention: integrated per output row, **net of neutrino losses**, and with
**no** 10¹⁶ normalization. Mixing these up produces a comparison that fails by
orders of magnitude with a characteristic +1.00 slope against dt-decade — which
is exactly how the mismatch was eventually diagnosed. (Note the diagnostic
logic: a *slope* against a control variable identifies a units error, where a
raw magnitude discrepancy would not.)

`EPS_NU_QUARANTINED` is machinery kept live (currently empty) so any future
re-extraction re-checks before training touches ε_ν.

## III.7 Leakage-safe splits

All nine records of one state share its `state_id` and therefore **must** land in
the same split. Otherwise the same (T, ρ, X) appears in train at dt = 10⁻³ and in
test at dt = 10⁻², and your test score measures interpolation in dt, not
generalization.

`SplitSpec.validate()` raises on any overlap; `split_of()` is keyed on state_id
only.

**Gap worth thinking about:** even state-level splitting may not suffice. Sobol
points are **not independent** — consecutive points are constructed to fill gaps
left by their predecessors, so nearby indices are spatially correlated *by
design*. A random state_id split therefore puts near-neighbours on both sides.
Whether that is leakage depends on the smoothness of Φ_Δt relative to point
spacing. Form your own view; the repository does not settle this.

## III.8 The missing rows

1,041,400 rows against 2²⁰ = 1,048,576 grid points — **0.68% missing**. Two
mechanisms: the upstream builder silently dropped runs whose output was
truncated, plus a logT/logρ range guard.

With no sample id, rows are matched back by nearest-neighbour search in
box-normalized (logT, logρ, Yₑ_initial) space, Yₑ_initial reconstructed via (4)
— `crosscheck/sobol.py::ye_from_initial`. Validity is enforced by requiring a
**unique** grid index per row.

**Why care about 0.68%?** Because *silent* dropping is non-random: runs were
dropped because they were hard, so the missing set is biased toward difficult
states. `scripts/sobol_missing_rows.py` measures whether it is uniform over the
box or clustered. A clustered gap would mean the training set has a hole exactly
where the physics is hardest — a very different problem from losing 0.68% at
random.

## III.9 Stratification: encoding physics into sampling

The Sobol grid is uniform over the box; the *physics* is not uniformly
interesting. `data/subsample.py` draws ~30,000 states stratified over 54 strata:

```
T9    [1.6, 2.5, 3.3, 4.0, 5.0, 6.3, 7.95]
logρ  [7.0, 7.667, 8.333, 9.001]
Yₑ    [0.45, 0.4667, 0.4833, 0.5001]
```

with the **QSE window T9 ∈ [3.3, 5.0) overweighted ×2**
(`OVERWEIGHT_T9_BINS = (2, 3)`, `OVERWEIGHT_FACTOR = 2.0`).

That factor of 2 is a physics statement in code: the QSE window is where
clustering is emerging but equilibrium has not taken over, so it carries the
most structure per sample. Strata edges are the same as `crosscheck/grids.py` —
one source, reused.

Note the design discipline: `stratified_sample` takes an explicit
`seed = 20260710`, but the *output* is persisted as an id list anyway, because
reproducibility-by-seed depends on library versions while an id list does not.

## III.10 Code reading order for S1

```
data/schema.py          ← start here; the docstring is the specification
  ↓
configs/dt_grid_measured.yaml     (measured grid; note per-network difference)
  ↓
data/labels.py          ← join discipline; why coordinate joins are inexpressible
  ↓
crosscheck/sobol.py     ← ye_from_initial, box-normalized NN matching
  ↓
data/subsample.py       ← strata, overweighting, persistence
  ↓
configs/step5_subsample_mesa_{80,151}.yaml + _ids.json
```

**Scripts:** `check_training_csvs.py`, `sobol_missing_rows.py`,
`download_zenodo.py`, `fetch_arxiv_source.py`

**Oracles:** `tests/test_schema.py`, `tests/test_subsample.py`,
`tests/test_crosscheck_data.py::test_ye_reconstruction_in_box`

**Notebook:** `01-data-inventory` Figure 1

## III.11 Self-check for S1

1. State Koksma–Hlawka and explain why the Sobol bound is vacuous at d ≈ 82.
   Give the actual argument for using Sobol here, and name its assumption.
2. Explain in one sentence why unseeded scrambling makes the grid
   non-regenerable, and list three design decisions that follow.
3. Do the collision estimate of §III.5. Explain why the measured value comes in
   *below* Poisson, and what that says about the point set.
4. Given ε_float32 ≈ 1.19×10⁻⁷ and the 10⁻¹⁵ floor, derive the narrowest
   defensible agreement band for ΔX. Compare with
   max(0.1|ΔX_lab|, 3ε(X_i+X_f), 2×10⁻¹⁵).
5. The box's upper edge is 7.9 GK. Argue why an emulator is unnecessary above it
   — then ask why the dataset includes states up to that edge anyway.
6. Sketch a *trajectory-aware* sampling design and predict how it would change
   the measured error distribution.
7. Design the semigroup consistency test (§III.1): which dt pairs, what metric,
   what constitutes failure.
8. Why is N = 2²⁰ specifically, and what is lost by taking a prefix of 700,000
   points?

---

# Part IV — The modelling frame

What sits between the physics and the model. This part contains the single most
load-bearing unexamined assumption in the project (§IV.1).

## IV.1 Operator splitting — the assumption everything rests on

### The setup

A stellar evolution code solves, per zone, a coupled system:

$$
\begin{aligned}
\frac{\partial \mathbf{X}}{\partial t} &= \text{burn}(\mathbf{X};\,T,\rho) \;+\; \text{mix}(\mathbf{X}) && \text{(composition)}\\
\frac{\partial T}{\partial t} &= \frac{e_{\text{nuc}}(\mathbf{X};T,\rho) - e_\nu - \nabla\!\cdot\!F}{c_p} && \text{(energy)}\\
&\quad\ \text{hydrostatic equilibrium} && \text{(structure)}
\end{aligned}
$$

These are coupled: burning changes X, which changes e_nuc, which changes T,
which changes the rates, which changes the burning. **MESA's default actually
solves this monolithically** — it "simultaneously solves the full set of
coupled equations" for all cells (Paxton et al. 2011). But in the Si/Fe-burning
regime this project targets, the *split* mode is the practical one: over a
timestep Δt, hold (T, ρ) fixed, advance the network alone, then update the
thermodynamics with the resulting energy release, then handle mixing. That is
MESA's `op_split_burn`, which sub-steps the composition at fixed (T, ρ) and
"may be the only way to make certain problems tractable" during Si and Fe
burning (Jermyn et al. 2023).

This is Godunov / Lie–Trotter (first-order) or Strang (second-order) operator
splitting (Strang 1968; Blanes, Casas & Murua 2008), with splitting error:

$$
\text{Godunov:}\ \ O(\Delta t) \qquad\qquad \text{Strang:}\ \ O(\Delta t^2)
$$

### Why this is the project's foundational assumption

**The emulator is a drop-in for the network sub-step.** Its contract is
therefore precisely:

> Given (T, ρ, X) held *constant* over Δt, return X′.

And that is exactly what the training data is. Read the campaign inlist:

```
&hydrostatic
   logT = {logT}
   logRho = {logRho}
   times_from_file = .true.
```

`scripts/bbq_campaign/inlist.template` fixes logT and logRho for the entire run.
The labels are **constant-(T,ρ) burns**. The Sobol training set is generated the
same way.

So the operator being learned is well-defined and matches how a host code would
call it. Good. But three things follow that you should hold consciously:

### Consequence 1 — the split's validity is a physical constraint on Δt

Silicon-burning rates are exponentially temperature-sensitive. If burning
releases enough energy to raise T appreciably *within* the step, then a
constant-T burn is the wrong operator.

Estimate the danger. A rate with effective temperature sensitivity
ν_T ≡ ∂ln λ/∂ln T (typically 20–40 for the controlling photodisintegration
rates in this regime, ν_T ≈ Q/kT; captures are milder — §III.3) changes by a
factor

$$
\frac{\lambda(T+\delta T)}{\lambda(T)} \approx \left(1 + \frac{\delta T}{T}\right)^{\!\nu_T} \approx \exp\!\left(\nu_T\,\frac{\delta T}{T}\right)
$$

With ν_T = 30, a mere δT/T = 3% doubles the rate. At the long end of the dt grid
(Δt = 10² s) in vigorous burning, δT/T of a few percent is entirely plausible.

> **This is a real open question, not a settled one.** The constant-(T,ρ) labels
> are self-consistent and the emulator will faithfully learn them. The question
> is whether the *host code* calls the network the same way at large Δt, or
> whether it sub-cycles with temperature feedback. If they differ, the emulator
> is accurate at the wrong thing.
>
> Partial answer from the code: in `op_split_burn` mode MESA does call the
> network exactly this way — constant-(T,ρ) sub-steps with an adaptive
> sub-timestep and no in-step temperature feedback (Jermyn et al. 2023). The
> fully-coupled default, by contrast, does not call it as a Δt-map at all.

Worth checking directly against how MESA's `net` module is invoked in
production, and worth knowing that the nine-decade dt grid spans from
definitely-safe to questionable.

### Consequence 2 — the emulator inherits the split's error, it does not fix it

An emulator that reproduces the constant-(T,ρ) operator to 10⁻⁸ still carries the
O(Δt) splitting error of the host scheme. **Accuracy of the surrogate is bounded
above by the accuracy of the scheme it plugs into.** A useful sanity anchor when
someone proposes tightening a gate: below the splitting error, extra fidelity
buys nothing.

### Consequence 3 — it makes the problem tractable at all

The flip side: because (T, ρ) are frozen, the network ODE is **autonomous**.
That is what makes Φ_Δt a genuine flow map with a semigroup structure (§IV.3),
and what makes the augmented-state integrator of S10 well-posed.

## IV.2 The one-zone approximation — and the reachable manifold

### What bbq is

`bbq` is a **one-zone burner**: a single fluid element at fixed (T, ρ), no
neighbours, no mixing, no transport. It integrates the network and nothing else.
This matches the split of §IV.1 exactly — mixing is the host's job.

### The subtlety nobody states

Silicon-burning cores are **convective**. Convective turnover times are
~10¹–10³ s (§0.7 — seconds to tens of minutes, and the range is genuinely that
wide; the one well-measured 3-D Si-shell point sits at the fast corner,
v ≈ 10⁷ cm/s and τ ≈ 20 s — Couch et al. 2015); core Si burning lasts days,
~10⁵–10⁶ s (WHW02). So mixing is *not* a small correction — it runs 10²–10⁴
turnovers over the burning phase, continuously resupplying fuel and
homogenizing composition.

The one-zone burner does not model this, and correctly so under splitting. But
it means:

> The compositions a real star presents to the network are the output of burning
> **plus** mixing **plus** the star's history. They lie on a low-dimensional
> **reachable manifold**, not spread over composition space.

### This is the deepest structural insight in Tier 0

The Sobol design samples composition space **uniformly over the box**. The
physically reachable set is a manifold of far lower dimension. Therefore:

```
     composition space (dim ≈ 80 or 151)
     ┌────────────────────────────────────────────────┐
     │  ·   ·    ·   ·   ·   ·   ·   ·   ·   ·   ·    │  ← Sobol training grid:
     │    ·   ·    ·  ╭─────────────╮ ·   ·   ·   ·   │    uniform, ~10⁶ points,
     │  ·   ·   ·  ╭──╯ reachable   ╰──╮  ·   ·   ·   │    mostly UNREACHABLE
     │    ·   ·  ╭─╯   manifold       ╰───╮ ·   ·  ·  │
     │  ·   ·   ╰──╮  (trajectories) ╭────╯   ·   ·   │  ← relaxed manifold:
     │    ·   ·    ╰────────────────╯   ·   ·   ·   · │    where the physics is
     │  ·   ·    ·   ·   ·   ·   ·   ·   ·   ·   ·    │
     └────────────────────────────────────────────────┘
```

**Three project findings are direct corollaries, and you can now predict them
before reading them:**

1. **κ ≈ 1 everywhere on the training grid.** A random composition is nowhere
   near flux balance — forward and reverse rates of a pair are unrelated, so
   |f⁺−f⁻| ≈ f⁺+f⁻. Cancellation is a property of *relaxed* states, and there
   are none in a uniform sample. This is why the kill-test on the training grid
   was a *vacuous* pass.
2. **The kill-test had to be re-run on a relaxed manifold**, populated by actual
   bbq trajectory reruns. Measuring a cancellation phenomenon requires sampling
   where cancellation exists.
3. **The Sobol→real-MESA distribution-shift check exists** for exactly this
   reason, with a retrain trigger if the real-track error exceeds the
   Sobol-measured value by more than 3×.

> **Generalize the lesson:** when the training distribution is chosen for
> *coverage* and the deployment distribution is set by *dynamics*, they are
> different objects. Measuring a dynamical property on the coverage distribution
> can produce a confident, meaningless answer.

## IV.3 The semigroup structure and rollout error

### The semigroup property

For an autonomous flow (which §IV.1 guarantees), the exact solution operator
satisfies

$$
\Phi_{s+t} = \Phi_s \circ \Phi_t \tag{IV.1}
$$

The training set contains **nine** dt values for the *same* initial states. So
(IV.1) is a hard consistency condition the data satisfies and a learned Φ̂
generally will not:

$$
\hat{\Phi}_{10^{-5}} \circ \hat{\Phi}_{10^{-5}} \;\neq\; \hat{\Phi}_{10^{-4}} \qquad \text{in general}
$$

> **This is a free, label-independent test** — a self-consistency check
> requiring no ground truth. It is not currently used anywhere in the project,
> and it is arguably the cheapest available diagnostic of rollout health.

### Rollout error propagation — deriving the accumulation trichotomy

In deployment the emulator is applied autoregressively: X_{n+1} = Φ̂(X_n). Let
e_n be the error after n steps and δ the per-step error injected. Linearizing
about the true trajectory with J = ∂Φ/∂X:

$$
e_{n+1} = J\,e_n + \delta_n \tag{IV.2}
$$

Three regimes, depending on the contraction factor c = ‖J‖:

| Regime | Condition | Accumulated after N steps | log–log slope |
|---|---|---|---|
| **Systematic, neutral** | c = 1, δ_n correlated | N δ | **1** |
| **Random walk** | c = 1, δ_n independent | √N δ | **0.5** |
| **Contracting** | c < 1 | δ/(1−c), saturates | **→ 0** |

The project states the first two and treats measuring the slope as its biggest
single lever — correctly, since the per-step Yₑ budget moves by more than an
order of magnitude between them.

**But the third case is the one worth predicting.** Silicon burning *contracts*
toward quasi-equilibrium and then NSE: nearby compositions converge. So ‖J‖ < 1
over much of the regime, and the physically expected behaviour is **saturation**,
not growth — at least in the strong sector.

The catch, and it is a big one: **Yₑ has no restoring force.** Strong reactions
conserve it exactly (§II.5), so contraction of the strong sector says nothing
about Yₑ error. Yₑ error should behave like a random walk or systematic drift on
top of a contracting background.

> **Prediction to test:** composition errors saturate (slope → 0), while Yₑ error
> accumulates (slope 0.5 or 1). If the measurement shows that split, the gate
> should be written on Yₑ alone — which is what the project already does, for
> what would then be a *derived* rather than assumed reason.

## IV.4 Self-check for Part IV

1. Write the split step explicitly for one Δt: what is held fixed, what is
   updated, in what order. Where does the O(Δt) error enter?
2. Using ν_T ≈ 30, compute the δT/T that would change rates by 10×. Then
   estimate whether a Δt = 10² s burn at T₉ = 4 could plausibly reach it.
3. Estimate the dimension of the reachable manifold during quasi-equilibrium
   silicon burning. (Hint: if a cluster is internally equilibrated, how many free
   parameters describe it?) Compare with 80.
4. Predict what κ would look like on states drawn from a real MESA track, then
   check against the measured relaxed-manifold distribution.
5. Argue both sides: is training on unreachable states harmful (wasted capacity,
   wrong inductive bias) or helpful (regularization, robustness during rollout
   excursions)?
6. Derive (IV.2) and the three regimes. Under what condition does the contracting
   case still fail? (Hint: what if δ is itself biased?)
7. Explain why strong-sector contraction cannot damp Yₑ error, using the
   structure of ν.

**Code anchors:** `scripts/bbq_campaign/inlist.template` (the split made
concrete), `scripts/bbq_campaign/make_campaign.py` (composition families —
"shipped" vs "canonical" vs "sobol" is exactly the reachable-vs-sampled
distinction), `data/trajectories.py` (the reachable manifold as data),
`killtest/manifold.py` (its assembly).

---

# Part V — Numerical analysis prerequisites

## V.1 Catastrophic cancellation — κ is a condition number

The single most important piece of numerical analysis in the project, and it
deserves a derivation rather than an assertion.

### The derivation

Compute d = a − b where a ≈ b > 0, with each input carrying relative error ε
(the standard rounding model — Goldberg 1991; Higham 2002):

$$
\mathrm{fl}(a) = a(1+\varepsilon_1), \qquad \mathrm{fl}(b) = b(1+\varepsilon_2), \qquad |\varepsilon_i| \leq \varepsilon
$$

$$
\text{computed } d = (a-b) + (a\varepsilon_1 - b\varepsilon_2)
$$

Relative error of the result:

$$
\frac{|\Delta d|}{|d|} \;\leq\; \varepsilon\,\frac{a+b}{|a-b|} \tag{V.1}
$$

Now recognize the denominator. With f⁺ = a and f⁻ = b:

$$
\kappa \equiv \frac{|f^+ - f^-|}{f^+ + f^-} \qquad \implies \qquad \frac{|\Delta d|}{|d|} \leq \frac{\varepsilon}{\kappa} \tag{V.2}
$$

> **κ is exactly the reciprocal condition number of the subtraction.**
> (The condition number of a − b is (|a|+|b|)/|a−b| — Higham 2002; for
> positive f± that is exactly 1/κ.)
> It is not a heuristic equilibrium diagnostic that happens to be useful. It is
> *the* error-amplification factor for recovering net flux from gross quantities.

Note that §0.2.3 arrived at κ from a completely different direction — as the
numerical test of detailed balance. The two meanings coincide, which is why κ is
load-bearing in both the physics and the numerics of this project.

### The numbers that follow

| κ | Amplification 1/κ | Net error from float32 gross (ε = 1.2×10⁻⁷) | float64 (ε = 2.2×10⁻¹⁶) |
|---|---|---|---|
| 1 | 1 | 1.2×10⁻⁷ | 2.2×10⁻¹⁶ |
| 10⁻¹ | 10 | 1.2×10⁻⁶ | 2.2×10⁻¹⁵ |
| 10⁻³ | 10³ | 1.2×10⁻⁴ | 2.2×10⁻¹³ |
| 10⁻⁶ | 10⁶ | 0.12 — **destroyed** | 2.2×10⁻¹⁰ |
| 10⁻⁹ | 10⁹ | — | 2.2×10⁻⁷ |

**Now the project's thresholds are derivable rather than arbitrary:**

- The **κ > 0.1 active-set gate** is the statement "amplification ≤ 10×" — one
  decade of precision loss, tolerable.
- **float64 everywhere in conservation arithmetic** buys the headroom: the same
  κ = 10⁻⁶ that would be fatal in float32 is harmless in float64.
- The **1/κ error amplification if φ were inferred from gross-scale features** —
  the phrasing used in the verdict document — is precisely (V.2).
- And the reason the worst-species coverage failure in T₉ ∈ [4.0, 6.3) matters:
  those species' net evolution rides on columns with κ ∈ 10⁻³–10⁻¹, i.e.
  10–1000× amplification.

### Why this reframes the whole kill-test

The kill-test asks: *can a model that predicts gross-scale quantities recover the
net?* (V.2) says the answer is governed entirely by the κ distribution. The
kill-test is therefore a **numerical conditioning study wearing a physics
costume** — and that is why its thresholds are stated in κ and in
cond(S_active), both condition numbers.

## V.2 Conditioning and the rank-revealing subtlety

For a linear system A x = b, relative error amplification is the condition
number

$$
\mathrm{cond}(A) = \frac{\sigma_{\max}}{\sigma_{\min}} \qquad (\text{ratio of extreme singular values})
$$

**The project's use.** Given dY, recover φ from dY = νφ. With n_species ≈ 80–151
equations and n_reactions ≈ 607–1518 unknowns this is massively
**underdetermined** — infinitely many φ produce the same dY, and the
minimum-norm solution is φ = ν⁺ dY via the Moore–Penrose pseudo-inverse. The
sensitivity of that recovery to perturbations in dY is set by the condition
number of the relevant submatrix. Hence the cond(S_active) < 10⁶ pass /
> 10⁸ fail gate, where S_active is ν restricted to the net columns that are
actually carrying flux.

Underdetermination is not itself a problem — it is *why* Target A works, since
any φ in the null space decodes to the same conserving dY. The problem would be
ill-conditioning within the active set, which is what the gate measures.

**The subtlety you must not get wrong.** ν has an *exact structural left-null
vector*: A·ν = 0, by baryon conservation, to machine precision. So σ_min = 0
identically, and a naive `np.linalg.cond` returns ~10¹⁶ — which is not
ill-conditioning, it is the conservation law showing up as a zero singular value.

The meaningful quantity is the **rank-revealing** condition number — the ratio
of extreme *nonzero* singular values, i.e. restricted to the row space (the
name borrows from rank-revealing factorizations, Chan 1987; "effective
condition number" is the closest standard term). That gives the measured
41.57 / 57.86 — perfectly well-conditioned.

> **Say which matrix, because the nullity differs.** On the nuclei-only ν (n × r)
> the only exact left-null vector is A, so there is **one** zero singular value
> to drop — Z is *not* one, because Z·ν_j = d_electron_j ≠ 0 on weak columns
> (§II.5). On the extended ν̃ = vstack(ν, lepton ledgers) ((n+3) × r), which is
> what `graph/stoich.py` builds and validates, **every row of C annihilates it**:
> C ν̃ = 0 exactly for all three independent rows, so ν̃ has a **three**-dimensional
> exact left-null space and a rank-revealing cond must discard three singular
> values, not one. Dropping the wrong number silently reports either a spurious
> 10¹⁶ or a spurious well-conditioning. The 41.57 / 57.86 figures are the
> nuclei-only reading (RESULTS.md 2026-07-09, post-reconciliation, superseding
> the earlier 41.70 / 57.55).

> A prior session in this repo rendered $\mathrm{cond}(\nu) = 1.5\times10^{16}$ in a figure whose
> caption claimed ≈42. It was caught in review. The lesson generalizes: **an
> exact structural null space is not ill-conditioning**, and any condition number
> computed on a matrix with known exact null vectors must be rank-revealing.

## V.3 Stiffness, defined properly

"Stiff" is often used loosely to mean "fast". It means something specific.

Let J = ν ∂R/∂Y be the Jacobian of the network ODE, with eigenvalues λ_i (mostly
with Re λ_i < 0 — decaying modes). Define the **stiffness ratio** (Hix &
Thielemann 1999b, after Lambert)

$$
S = \frac{\max_i |\mathrm{Re}\,\lambda_i|}{\min_i |\mathrm{Re}\,\lambda_i|} \tag{V.3}
$$

An explicit method is stable only for step h ≲ 2/max|λ| — forward-Euler
stability, observed to the fourth digit in a real network ("precisely two over
the fastest rate" — Guidry et al. 2013). Integrating out to the
*slowest* timescale t ~ 1/min|λ| therefore requires

$$
N_{\text{steps}} \sim S
$$

At silicon-burning conditions: fastest modes are photodisintegration /
(n,γ)-(γ,n) pairs with rates up to ~10¹⁰ s⁻¹; slowest are weak reactions at
~10⁻⁵–10⁻² s⁻¹ (both endpoints are order-of-magnitude estimates — *assumed*,
pending the Jacobian measurement of self-check item 6 — but the bracket they
produce sits inside the literature envelope: "S > 10¹⁵ is not uncommon in
astrophysics", Hix & Thielemann 1999b; fastest-to-slowest spans of 10–20
orders, Guidry et al. 2013). So

$$
S \sim 10^{12}\text{–}10^{15}
$$

Explicit integration would need ~10¹⁵ steps to follow the Yₑ evolution.
**Implicit is not an optimization, it is a necessity.**

### Stiffness and QSE are the same phenomenon

The fast modes decay quickly, after which the trajectory lies on a
low-dimensional **slow manifold** in composition space. On that manifold the fast
reactions are in balance — which is exactly the definition of quasi-statistical
equilibrium.

> **Stiffness ⟺ the existence of a slow manifold ⟺ QSE.**
> S9 (equilibrium theory) and S10 (stiff integration) are two views of one
> structure. Reading them as unrelated topics is the main way people fail to
> understand this domain. (Strictly the arrows run one way — stiffness alone
> guarantees a fast decaying mode, not a physically meaningful equilibrated
> sector; the identification is the standard singular-perturbation picture,
> cf. ILDM — Maas & Pope 1992.)

Note this also connects back to §IV.2: the slow manifold *is* the reachable
manifold, approached after transients decay. The three concepts — stiffness, QSE,
and the reachable set — are one object seen from numerics, thermodynamics, and
sampling respectively.

This also explains why the *genuine* unlock for hot-state integration cost — as
the project's own negative-results investigation concluded — is **QSE-reduced
integration**: algebraically eliminate the fast equilibrated sector and integrate
only the slow one. Not a solver trick; exploiting the slow manifold directly.

## V.4 Floating point, concretely

| Type | ε (machine epsilon) | Decimal digits |
|---|---|---|
| float32 | 1.19×10⁻⁷ | ~7 |
| float64 | 2.22×10⁻¹⁶ | ~16 |

**Why the conservation gate is achievable.** Naive summation of n terms
accumulates error ~nε in the worst case (the sharp bound is
(n−1)u·Σ|xᵢ| + O(u²) — Higham 2002; nε at O(1) gross scale is the fair
simplification). For the largest network:

$$
n\,\varepsilon = 151 \times 2.22\times10^{-16} \approx 3.4\times10^{-14}
$$

comfortably below the 10⁻¹² gate — about 1.5 decades of margin. In float32 the
same sum gives 1.8×10⁻⁵, missing the gate by seven orders of magnitude. **This is
the derivation behind "float64 for anything touching conservation."**

**Why the drift bound is scaled rather than absolute.** An absolute bound of
10⁻¹² is meaningless when |φ| ~ 10⁻²⁰ — every quantity involved is already below
it, so the test would pass vacuously. Hence the project's bound

$$
\max\!\bigl(10^{-12}\,s,\; 10^{-13}\,G\bigr), \qquad s = \min(1, \max|\varphi|), \qquad G = |A|\cdot(|\nu|\cdot|\varphi|)
$$

which reduces to the hard absolute gate at O(1) magnitudes and stays
machine-precision-tight relative to the *gross* scale at the small end. Read
`tests/test_conservation.py` with this in mind — the tolerance design is the
interesting part of that file.

(In practice the measured column drifts are exactly 0.0, because ν is integer and
the products are exactly representable. The bound exists for the general random-φ
case.)

## V.5 Newton's method, damping, and globalization

Prerequisite for reading `qse/solver.py`, whose structure looks defensive until
you know what it is defending against.

### The method

To solve **F**(**u**) = **0**, iterate

$$
\mathbf{u}_{k+1} = \mathbf{u}_k - J^{-1}F(\mathbf{u}_k), \qquad J = \frac{\partial F}{\partial \mathbf{u}} \tag{V.4}
$$

Near a simple root, convergence is **quadratic**: the error squares each step,
so 10⁻² → 10⁻⁴ → 10⁻⁸ → 10⁻¹⁶. That is why Newton is the default whenever an
analytic Jacobian is available — and here it is, because the Saha form
differentiates in closed form.

### Why it fails, specifically here

The NSE residual involves X_i = exp(logC_i + (Z_i u_p + N_i u_n)/kT). With
Z, N ~ 28 and kT ~ 0.3 MeV, the exponent has a coefficient of order 100 per MeV
of chemical potential. A Newton step that overshoots by even a few MeV pushes
the exponent by hundreds — producing `inf`, then `nan`, then a dead iteration.

Two guards, both visible in the code:

1. **Step damping.** Cap the step, ‖δu‖ ≤ 2 MeV per iteration. This sacrifices
   quadratic convergence far from the root in exchange for never leaving the
   representable region. Standard globalization; a line search would be the
   fancier alternative.
2. **Exponent clipping** at `EXP_CLIP` (mirroring pynucastro), so an overshoot
   saturates rather than overflowing.

### Globalization: the fallback that cannot fail

Damped Newton is still only *locally* convergent. `solve_nse` therefore falls
back to **nested bisection**: slow (linear convergence, one bit per iteration)
but *guaranteed* on a bracketed monotone problem. The residual is monotone in
each chemical potential, which is what makes bracketing valid.

Convergence tolerance is `tol = 1e-11` on the residual.

> **The pattern is worth extracting, because the repo uses it repeatedly:**
> a fast method, a provably convergent fallback, and a **record of which one
> ran** — `NSEResult.method` is `"newton"` or `"bisection"`. Silent fallback
> would hide a systematic problem; recorded fallback turns it into a measurable
> rate. The batched solvers added later preserve exactly this: vectorized Newton
> with per-row convergence masking, delegating non-converged rows to the proven
> scalar path.

## V.6 ODE error control: what rtol and atol actually promise

Prerequisite for reading `fluxes/integrate.py`.

### Local versus global error

An adaptive solver controls the **local** error per step against

$$
\text{tolerance}_i = \mathrm{rtol}\cdot|y_i| + \mathrm{atol}_i \tag{V.5}
$$

(Hairer, Nørsett & Wanner 1993; SciPy's `solve_ivp` documents exactly this
contract — "keeps the local error estimates less than atol + rtol·abs(y)".)
It does **not** control global error. The relationship between them is exactly
§IV.3's accumulation problem applied to the integrator: global error is the
accumulation of local errors under the flow's own contraction. For a contracting
(dissipative) problem — which this is — local control is a good proxy. For a
chaotic or neutrally stable one it would not be.

**So `rtol = 1e-8` does not mean "the answer is right to 1e-8".** It means each
step's local error estimate was held there. Verifying the actual accuracy needs
either a tolerance sweep or an independent method.

Both are done here: the integrator is checked BDF versus Radau (a multistep
method versus an implicit Runge–Kutta — different error structures entirely) and
across rtol from 1e-10 to 5e-8. Agreement across *method* and *tolerance* is the
real accuracy evidence; the tolerance number alone is not.

### Why atol matters more than usual

With a state spanning 15 decades, $\mathrm{rtol}\cdot|y|$ is meaningless for trace species:
a species at Y ~ 10⁻²⁰ would have a tolerance of 10⁻²⁸, and the solver would
take absurdly small steps chasing numerical noise. **atol sets the "I do not
care below this" floor**, and choosing it is a physics decision, not a numerical
one.

The integrator uses `atol_y = atol_phi = 1e-18`, and — the point worth noting —
carries them as **separate parameters**. The augmented state is [Y, Φ], and
abundances and cumulative fluxes have different natural scales; a single atol
would impose one species' notion of negligible on the other.

### Dense output and t_eval

`t_eval` requests values at specified times. The solver does **not** change its
step sequence to land on them — it interpolates using the polynomial it already
built for error estimation. This is why one integration to dt = 10² s with
`t_eval` at all nine label dts costs essentially the same as integrating to 10²
s alone, and gives all nine labels. That is the design that makes the label
prototype affordable at all.

### BDF versus Radau

- **BDF** — multistep, variable order 1–5, cheap per step (one Jacobian reused
  across steps), the standard choice for large stiff systems.
- **Radau** — implicit Runge–Kutta (Radau IIA, order 5), L-stable, more robust
  on very stiff or strongly nonlinear problems, more expensive per step.

(Hairer & Wanner 1996; properties confirmed against the SciPy implementation.
BDF above order 2 is only A(α)-stable — the Dahlquist barrier — which is
precisely why an L-stable Radau cross-check is meaningful.)

Using BDF as production and Radau as cross-check is the right split: you get
throughput from one and solver-independence evidence from the other.

## V.7 Self-check for Part V

1. Derive (V.1) carefully, tracking signs.
2. At what κ does float64 gross-flux arithmetic fail to deliver the 3×10⁻⁶
   per-step Yₑ gate? Compare with the measured κ distribution.
3. Target A predicts φ directly rather than differencing f⁺ and f⁻. Does that
   escape (V.2)? Argue both ways — then note what the labels themselves are made
   of.
4. Explain why dY = νφ is underdetermined, why that is *not* a problem for
   Target A, and what would actually constitute a conditioning failure.
5. Compute `np.linalg.cond` on an exported ν and reproduce the ~10¹⁶ artifact.
   Then compute the rank-revealing version and recover ≈42 / ≈58.
6. Estimate S from a real Jacobian at T₉ = 4 and compare with the 10¹²–10¹⁵
   claim. Which reactions set each end?
7. Show that the scaled drift bound reduces to the absolute 10⁻¹² gate at
   |φ| ~ 1, and explain why an absolute bound alone would be vacuous at 10⁻²⁰.
8. Estimate how far a single undamped Newton step can move the Saha exponent if
   δu = 10 MeV, at kT = 0.345 MeV and Z = N = 28. Now justify the 2 MeV cap.
9. Why is bisection a *valid* fallback here — what property of the residual does
   bracketing require, and does the QSE residual have it too?
10. State precisely what `rtol = 1e-8` promises and what it does not. Then
    describe the two independent checks that would establish actual accuracy.
11. Why does the augmented integrator carry separate `atol_y` and `atol_phi`?
    Construct a state where a single shared atol would be wrong for one of them.

**Code anchors:** `tests/test_conservation.py` (tolerance design),
`graph/metrics.py::condition_numbers` and `drift_metrics`,
`killtest/active_set.py::cond_s_active`, `fluxes/engine.py` (where κ is formed),
`qse/solver.py` (damped Newton + bisection, `NSEResult.method`),
`fluxes/integrate.py` (BDF/Radau, rtol/atol, `t_eval`).

---

# Part VI — ML prerequisites and context

## VI.1 What kind of learning problem this is

**It is not neural operator learning in the DeepONet/FNO sense.** Those target
maps between *function spaces* (infinite-dimensional — Lu et al. 2021; Li et
al. 2021). Here input and output are
fixed finite vectors: **83 or 154 numbers in** — (log T, log ρ, X, dt) per §III.1
— and **82 or 153 out** — (X′, e_nuc, ε_ν). The "operator" framing refers to the
*family* {Φ_Δt} indexed by timestep.

(Do not confuse this 83 with the d ≈ 82 of §III.4. That is the *Sobol sampling*
dimension, 2 thermodynamic + 80 composition, where dt is not a sampled coordinate
but a nine-point grid applied to every drawn state. Same-looking number, different
object.)

**So what is hard about it?** Not expressivity — a sufficiently large MLP can
represent the map. The difficulties are:

1. **Dynamic range.** X spans 15 decades; φ spans more. Standard initialization
   and standard losses both implicitly assume O(1) targets.
2. **Stiffness in the target.** Neighbouring inputs can map to very different
   outputs when a state is near a fast-mode threshold — the learned map must
   have large, spatially varying Lipschitz constants, which is exactly what
   smooth function approximators resist.
3. **Exact constraints.** No amount of capacity produces exact conservation; it
   must be architectural (§I.6, §I.8).
4. **Extrapolation under rollout.** The deployment distribution is the reachable
   manifold (§IV.2), and rollout drifts off it.

Recognizing that expressivity is *not* the bottleneck is what justifies spending
the effort on the decoder structure rather than on backbone scale.

## VI.2 Message passing, concretely

A GNN layer updates node states by aggregating over neighbours (the
message-passing scheme of Gilmer et al. 2017; Battaglia et al. 2018):

$$
h_i^{(k+1)} = \phi\Bigl(h_i^{(k)},\; \bigoplus_{j \in N(i)} \psi\bigl(h_i^{(k)}, h_j^{(k)}, e_{ij}\bigr)\Bigr) \tag{VI.1}
$$

with ⊕ a permutation-invariant aggregator (sum, mean, max).

**Bipartite version**, which is what this network is:

$$
\begin{aligned}
\text{reaction node:}\quad h_r &\leftarrow \psi_{IR}\bigl(\{h_i : i \in \text{reactants}(r)\},\; \text{edge features}\bigr)\\
\text{species node:}\quad h_i &\leftarrow \psi_{RI}\Bigl(h_i,\; \bigoplus_{r \ni i} (\nu_{ir},\, h_r)\Bigr)
\end{aligned}
$$

One full round = species → reaction → species. **Sum aggregation is the
physically correct choice on the R→I half-step**, because the true update is
literally a signed sum: dY_i = Σ_r ν_ir φ_r. Mean or max would destroy
extensivity (and sum is independently the most expressive aggregator in the
multiset sense — Xu et al. 2019).

**Depth — and state the hop convention, or the arithmetic does not close.**
One full round is species → reaction → species = **2 bipartite hops**, so K
rounds propagate information 2K bipartite hops, not K. With measured bipartite
radius 3 and diameter 6:

$$
2K \geq \text{diameter} = 6 \quad\Longrightarrow\quad K \geq 3
$$

So **K = 3 rounds suffice to span the graph**, and the project's K = 5 carries
~4 hops of margin. (The derived I→I projection does *not* simply halve these
numbers: the repo measures it at radius 2, diameter 4 — RESULTS.md 2026-07-09
— because the projection is its own graph object, not the bipartite metric
divided by two. At one I→I hop per round, that view requires K ≥ 4. Either
way, K = 5 exceeds the requirement.) Beware the version of this claim that reads "radius 3, diameter 6
⟹ K = 5": under a one-hop-per-round convention K = 5 would *fail* to cover a
diameter-6 graph, and under the two-hop convention it overshoots. Neither
reading yields 5 — the number is a design margin, and should be defended as one.

Deeper is not obviously better:

- **Oversmoothing:** as K grows, node representations converge toward a common
  value and become indistinguishable (Li, Han & Wu 2018). At K = 5 not yet
  serious, but it bounds how much depth can help.
- **Expressivity:** message passing is bounded above by the 1-Weisfeiler-Lehman
  test in distinguishing power (Xu et al. 2019; Morris et al. 2019 — the
  theorems hold for labelled graphs too; 1-WL runs on the initial node
  labels). Irrelevant here — nodes carry distinguishing features (Z, A, Y), so
  the colouring separates nodes from iteration 0 and the bound never binds.

**Equivariance.** The physics is invariant to relabelling species. (VI.1) is
permutation-equivariant by construction (Battaglia et al. 2018; Bronstein et
al. 2021). A dense MLP must learn this from data,
spending capacity on a symmetry that could have been free.

## VI.3 Feature and loss design under 15 decades of dynamic range

### Inputs first — the transform that is legal

The raw composition vector spans 15 decades, which no standard initialization or
normalization scheme tolerates. The conventional fix is a signed-log or
inverse-hyperbolic-sine transform on the *inputs*:

$$
\tilde{x}_i = \sinh^{-1}\!\left(\frac{X_i}{s}\right) \qquad \text{or} \qquad \log_{10}(X_i + X_0)
$$

**This is legal, and it is important to be clear about why**, given §I.8 spends
its length forbidding exactly this function. The rule is not "asinh is banned".
The rule is:

> asinh/signed-log are fine as **internal latents**, including on inputs.
> They may never be the space in which a **sum constraint or projection** is
> evaluated.

Encoding X into a latent and decoding φ (or dY) in a linear space keeps the
conservation map downstream of every nonlinearity, which is the whole
requirement. The NuGNN failure mode was subtler than "projecting in the warped
space": because its outputs live in a signed-log space, any explicit
conservation enforcement (loss term or output activation) required inverting
the warp inside training, which destabilized optimization — so enforcement was
dropped entirely, leaving an unconstrained model plus a retry-on-drift
heuristic at rollout (Kim et al. 2026). The lesson is the same, not the warp
itself: a sum constraint is only enforceable where the output is linear.

Other input channels worth having, most of them free:

- (log T, log ρ) — already logarithmic, already O(1) after box normalization
- per-node static features: Z, A, N−Z, binding energy per nucleon, the
  weak/strong flag
- per-node dynamic features: Yᵢ, and the equilibrium departure δᵢ if computed
- per-reaction features: Q-value, chapter/ΔN, screening factor, and **κ
  diagnostics**

That last one is a project decision worth understanding: once the Guidry mask
was measured empty, the κ information did not become useless — it was demoted
from a *mask* (a hard architectural gate) to a *feature* (something the model
may condition on). Carrying a diagnostic as a feature is the fallback when it is
informative but not cleanly separable.

**The zero problem.** Many Xᵢ are exactly 0 in initial conditions, and log(0) is
undefined. asinh handles it (sinh⁻¹0 = 0); log needs an additive floor, which
then becomes a hyperparameter encoding what counts as negligible. Prefer asinh
on inputs for this reason alone.

### Then losses — where the naive choices all fail

| Loss | Failure mode |
|---|---|
| MSE on X | Dominated entirely by the few species with X ~ 1; trace species contribute nothing |
| MSE on log X | Undefined at X = 0; and the 10⁻¹⁵ floor is *censored*, so log-space error there measures a clamp |
| Relative error \|ΔX\|/X | Explodes for trace species; amplifies label noise where X is at the float32 noise level |
| Relative with floor \|ΔX\|/(X + X₀) | Workable — but X₀ is now a hyperparameter encoding what you consider negligible |

**The structural observations that reframe the problem:**

- The quantity that must be accurate is **Yₑ = Σ Z_i Y_i**, a weighted sum.
  Errors in species with small Z_i/A_i deviation from 0.5 barely matter. A loss
  weighted toward Yₑ-controlling species is physically motivated, not a hack —
  and the project already identifies the target channels (top-|dẎₑ| weak
  channels: ⁵⁶Ni EC, ³¹S EC, ⁵²Fe EC, p EC).
- Supervising in **Φ space** rather than ΔX space side-steps the dynamic-range
  problem partly, because fluxes are more nearly log-uniform. This is exactly
  what the auxiliary Φ labels from the reference integrator are for.
- **Censoring must be handled explicitly.** A value at 10⁻¹⁵ means "≤ 10⁻¹⁵", not
  "= 10⁻¹⁵". The correct treatment is a one-sided (censored) likelihood — the
  standard Tobit treatment (Tobin 1958) — not a squared error against the clamp.

## VI.4 MESA and bbq, concretely

**MESA** (Modules for Experiments in Stellar Astrophysics) is a modular 1-D
stellar evolution code (Paxton et al. 2011; Jermyn et al. 2023). The relevant
modules:

- `net` — the nuclear reaction network solver
- `rates` — REACLIB fits, tabulated weak rates, screening
- `weaklib` — tabulated weak rates on (T, ρYₑ) grids, with source precedence
  LMP > Oda > FFN (Paxton et al. 2011; in r23.05.1 this machinery lives inside
  the `rates` module rather than as a separate directory)

**Network types** in MESA ("hard-wired" is MESA's own terminology; "softwired"
is community usage — Farmer et al. 2016 classify the `mesa_*.net` family
exactly this way):

| Type | Meaning |
|---|---|
| *hardwired* | Fixed species and fixed reaction list, compiled in |
| **softwired** | Fixed species list; reaction links assembled at runtime from whatever rates connect them — **what mesa_80/mesa_151 are** |
| *approx* | Reduced networks with lumped/approximated links (e.g. `approx21`) |

A `.net` file declares the species; the links follow. This is why the reaction
*count* (607 / 1518) is something you have to *measure* by asking MESA what it
built, rather than read off a list — the entire point of the Fortran probe in
`src/mesa_probes/probe.f90` and the reconciliation in S6.

**bbq** is a one-zone burner utility built on MESA's `net` (Farmer's `bbq`,
Zenodo record 7585202; the tool behind Grichener et al. 2025): give it
(T, ρ, X₀) and a time grid, get back the composition history and energetics. Its
`use_hydrostatic` + `times_from_file` mode produced both the shipped test
trajectories and the local rerun campaign.

## VI.5 Prior art in network acceleration — where ML actually sits

ML is the newest entry in a long line of attempts. Knowing the line matters,
because the project's vocabulary is borrowed from it:

| Approach | Idea | Why it appears in this project |
|---|---|---|
| **NSE tabulation** | Above ~7 GK, skip the ODE — composition is algebraic in (T,ρ,Yₑ) (Hix & Thielemann 1999b) | Sets the box's upper edge (§III.2) |
| **QSE / cluster reduction** (Hix & Thielemann 1996, 1999a; Hix et al. 2007) | Equilibrated groups collapse to one unknown per cluster; integrate only bridges + weak | The `qse/` solver, the Si-group config, `r_QSE` |
| **Partial equilibrium / explicit asymptotic** (Guidry et al. 2013) | Detect equilibrated forward–reverse *pairs* dynamically, drop them from integration, use explicit methods for the rest | The "Guidry mask", the δ_r criterion, the ε sweep |
| **Adaptive networks** | Grow/shrink the species set by local importance | Related to the active-set framing of the kill-test |
| **ML surrogates** | Learn the flow map | This project, and the NNN baseline |

> **Read the kill-test as a test of whether the QSE-reduction idea applies to
> *this* data.** The Guidry mask being measured *empty* is a statement that the
> classical reduction strategy does not have a clean target here — itself a
> result, and why the flux head ended up full-width.

## VI.6 The observational grounding — how we know Yₑ matters

Chains of inference worth being able to state:

1. **⁵⁶Ni masses from light curves.** The decay chain ⁵⁶Ni → ⁵⁶Co → ⁵⁶Fe
   (half-lives 6.08 d, 77.2 d — ENSDF) powers the tail of a supernova light
   curve (Arnett 1982; Diehl et al. 2015). Fitting the tail gives the ejected
   ⁵⁶Ni mass directly. That mass depends on how much material burned to NSE
   and at what Yₑ.
2. **Abundance patterns in metal-poor stars.** Fe-peak element ratios (Ni/Fe,
   Cr/Fe, Mn/Fe) are sensitive to Yₑ in the explosive burning region. Observed
   ratios constrain the Yₑ of the ejected burning region (e.g. Jerkstrand et
   al. 2015 for Ni/Fe).
3. **Explodability studies.** The compactness parameter
   ξ_M = (M/M⊙)/(R(M)/1000 km) at M = 2.5 M⊙, evaluated at bounce, correlates
   with whether simulations explode (O'Connor & Ott 2011). It is set by the
   core structure at collapse — set in turn by the Si-burning history.
4. **SN 1987A.** Direct neutrino detection confirmed the core-collapse
   energetics picture and the neutrino emission scale (Hirata et al. 1987;
   Bionta et al. 1987).

This is what makes the accuracy targets *meaningful* rather than
self-referential: there is a measurement at the end of the chain.

## VI.7 Self-check for Part VI

1. Explain why this is not neural-operator learning in the DeepONet/FNO sense,
   and what the "operator" framing does refer to.
2. Write (VI.1) for the bipartite network and justify sum aggregation on the
   R→I half-step from equation (3).
3. Give a concrete failure case for each of the four losses in §VI.3, using real
   numbers from the box (X ~ 1 species vs X ~ 10⁻¹² species).
4. Explain why the reaction count must be *measured* in a softwired network, and
   name the code path that measures it.
5. For each entry in the §VI.5 prior-art table, name the module or config in
   this repository that inherits its vocabulary.
6. Trace the inference chain from "an emulator gets Yₑ wrong by 1%" to "an
   observable changes", naming each physical link.

---

# Part VII — Working practice: the discipline the repo runs on

**The one non-physics part.** It is here because you cannot read this codebase
without it: several modules look like over-engineering until you know which
epistemic rule they enforce. Every pattern below appears in code you will read
in Tier 1.

## VII.1 Every number carries a provenance label

Exactly one of:

| Label | Meaning | Failure mode it prevents |
|---|---|---|
| **sourced** | has a citation — paper plus where in it | laundering an estimate into a citation's vicinity so it reads as authoritative |
| **derived** | names the script in `scripts/` that produces it | a number nobody can regenerate |
| **measured** | measured in this project, with a `RESULTS.md` row carrying date, commit, and data provenance | a number that drifts as the code changes |
| **assumed** | an internal estimate, stated **with its retirement plan** | an assumption hardening into a fact by repetition |

The `assumed` category is the interesting one, and §0.7 gave you its canonical
example: the "6–8 orders of magnitude" timescale separation was carried as
assumed, with a checklist row naming the measurement that would retire it — and
then that measurement retired it, in the opposite direction from the assumption.
**That is the system working**, and it only worked because the number was never
allowed to be quoted as sourced.

## VII.2 Thresholds must have instruments

Any gate written down — per-step |ΔYₑ| ≲ 3×10⁻⁶, cond(S_active) > 10⁶,
mask churn > 5%/step, the 2× transfer falsifier — must name the test, script, or
checklist item that measures it.

> A threshold with no measuring instrument is not a standard, it is a slogan.

This is why the Phase-0 checklist is a *measurement program* rather than a task
list: each row is a quantity, the gate it sets, and the script that will produce
it. When you see a number in `CLAUDE.md`, look for its instrument; if you cannot
find one, that is a finding.

## VII.3 Decisions carry their own reversal condition

Settled decisions become ADRs, and every ADR must state a **switch condition**:
the measured threshold at which the decision reverses.

```
"We chose Target A"                          — incomplete
"We chose Target A; we abandon it when
 cond(S_active) > 10⁶ or >90% of net-flux-
 carrying reactions fall below the Yₑ floor" — complete
```

Accepted ADRs are immutable; a changed decision *supersedes* rather than
rewrites, so the history of what was believed when survives. The same reasoning
governs measurements: a redone measurement never silently overwrites the old
value.

## VII.4 Invariants live in code that refuses, not in comments

The pattern you will meet repeatedly: rather than documenting a rule and hoping,
make the violation **inexpressible**.

| Rule | How it is enforced |
|---|---|
| No raw pf-free v-flag reverses at T₉ ≥ 3 | `fluxes/guards.py::assert_pf_gate` raises `PfGateError` at compile time |
| Never join labels on (logT, logRho) | `data/labels.py::join_on_state_id` refuses non-state_id-indexed frames |
| Weak columns are never maskable | `qse/diagnostics.py::eligible_mask` excludes them *structurally*, from `weak_mask`, so `killtest.active_set.guidry_masks` cannot produce one |
| Never mix the two κ conventions | `killtest/distributions.py` refuses runs recording a screening config unless explicitly overridden |
| Conservation must hold for any φ | `tests/test_conservation.py` is a **blocking gate** run against a *randomly initialized* flux head |

Note the difference between a *test* and a *gate*. A test reports; a gate
blocks. The conservation check is a gate: training does not begin until it
passes, and edits to `graph/` trigger it automatically.

## VII.5 Non-regenerable artifacts are persisted, not re-derived

§III.4 established that the Sobol grid cannot be regenerated. The general rule
that follows:

> When an artifact cannot be reproduced from a recipe, **persist the artifact**,
> not the recipe.

Hence `configs/step5_subsample_*_ids.json` holds explicit state_id lists even
though `stratified_sample` takes a seed — because seeded reproducibility depends
on library versions, while a list of integers does not. Same reasoning behind
content hashes recorded for every generated flux store.

## VII.6 Notebooks explore; scripts produce

Notebooks are **exploratory only**. Every citable number comes from `scripts/`
and lands in `RESULTS.md`; notebooks load cached artifacts and re-plot them.

This is enforced structurally too — `nbsupport.caption()` raises if a figure
cites no `RESULTS.md` row, and the κ helper requires a declared
UNSCREENED/SCREENED convention that must match the store's own attributes, so
mixing conventions fails loudly rather than silently.

## VII.7 Self-check for Part VII

1. Pick five numbers from `CLAUDE.md` and classify each as sourced / derived /
   measured / assumed. For any `assumed`, find its retirement plan.
2. Take the cond(S_active) > 10⁶ gate and name its instrument, its ADR, and its
   switch condition.
3. Find one guard in `fluxes/guards.py` and write the failure it makes
   impossible. Then write the comment-only version and explain what would
   eventually go wrong with it.
4. Why does `NSEResult` record `method` ("newton" / "bisection")? Connect to
   §V.5 and to VII.2.
5. Argue the cost side honestly: what does this discipline make *slower* or
   harder, and when would it be the wrong trade?

---

# Where Tier 0 hands off

## What Part 0 upgraded

| Statement, before | Now derived |
|---|---|
| "the regime box is ρ = 10⁷–10⁹" | 10⁷ sits just below the free-proton EC threshold (2.4×10⁷); 10⁹ is strongly degenerate. The box brackets the turn-on of the Yₑ-controlling process (§0.1.5) |
| "screening uses chugunov_2007" | Γ ≈ 0.4–25 across the box (ρ^{1/3}/T, so the T edges dominate) — intermediate coupling, where neither weak- nor strong-screening asymptotics are valid (§0.1.4) |
| "partition functions matter above T₉ ≈ 3" | kT ≈ 0.26 MeV at T₉ = 3 vs first excited states at 0.5–2 MeV — thermal population becomes order-unity exactly there (§0.2.2) |

## Threads that carry forward

- **From Part 0:** Γ ≈ 0.4–25 fixes the screening prescription (**S4**);
  partition functions at kT ≈ 0.3 MeV fix the pf gate (**S3**); chemical
  equilibrium Σν_iμ_i = 0 generates NSE and QSE (**S9**); ΔN per REACLIB chapter
  is the index of the gh-575 bug (**S3**); the α-ladder and two-cluster topology
  is what the group/bridge machinery measures (**S9**, **S13**); and the
  timescale hierarchy — *with* its measured absence of a clean spectral gap — is
  the premise every reduction scheme must argue against (**S9**, **S14**).
- **From S0:** the linearity of Σ Aᵢ Yᵢ = 1 in Y makes the conservation layer a
  fixed matrix — **S7** turns that into ν, C, and P.
- **From S1:** "dt = 10⁻⁶ s" is already a full stiff relaxation, which forces the
  time-integrated flux target Φ = ∫φ dt — **S8** and **S10**.
- **From the frame:** κ is a condition number (**S8**, **S14**); stiffness, QSE,
  and the reachable manifold are one structure (**S9**, **S10**, **S14**).

## The three ideas to carry, if you carry nothing else

1. **κ is a condition number** (§V.1), and independently the numerical test of
   detailed balance (§0.2.3). Every κ threshold is a statement about tolerable
   error amplification; the kill-test is a conditioning study.
2. **Stiffness ⟺ slow manifold ⟺ QSE ⟺ the reachable set** (§V.3, §IV.2). Four
   vocabularies, one object.
3. **The training distribution is not the deployment distribution** (§IV.2). The
   Sobol box covers composition space; physics lives on a low-dimensional
   manifold inside it. Several project findings are corollaries.

---

**Next:** Tier 1 — **S2** (REACLIB rates: ⟨σv⟩, the Gamow peak, the
seven-coefficient fit) and **S3** (detailed balance, partition functions, the
gh-575 phase-space factor).

---

# References

Sources verified during the 2026-08-12 literature audit (`study/tier0-audit.md`
records which passage of each source supports which claim). arXiv-available
papers are cached as TeX under `data/literature/`.

- Arnett, W. D. 1982, "Type I supernovae. I. Analytic solutions for the early part of the light curve", ApJ 253, 785.
- Baron, E. & Cooperstein, J. 1990, "The effect of iron core structure on supernovae", ApJ 353, 597. (No arXiv; thermal-correction form verified via Suwa et al. 2018 and Mori et al. 2023, arXiv:2306.17381.)
- Battaglia, P. W., et al. 2018, "Relational inductive biases, deep learning, and graph networks", arXiv:1806.01261.
- Beucler, T., Pritchard, M., Rasp, S., Ott, J., Baldi, P., & Gentine, P. 2021, "Enforcing Analytic Constraints in Neural Networks Emulating Physical Systems", Phys. Rev. Lett. 126, 098302. arXiv:1909.00912.
- Bildsten, L. & Cumming, A. 1998, "Hydrogen Electron Capture in Accreting Neutron Stars and the Resulting g-Mode Oscillation Spectrum", ApJ 506, 842. arXiv:astro-ph/9807012.
- Bionta, R. M., et al. 1987, "Observation of a neutrino burst in coincidence with supernova 1987A in the Large Magellanic Cloud", Phys. Rev. Lett. 58, 1494.
- Blanes, S., Casas, F., & Murua, A. 2008, "Splitting and composition methods in the numerical integration of differential equations", Bol. Soc. Esp. Mat. Apl. 45, 89. arXiv:0812.0377.
- Bodansky, D., Clayton, D. D., & Fowler, W. A. 1968, "Nuclear Quasi-Equilibrium during Silicon Burning", ApJS 16, 299. (Pre-arXiv; content verified via Hix & Thielemann 1996.)
- Bratley, P. & Fox, B. L. 1988, "Algorithm 659: Implementing Sobol's quasirandom sequence generator", ACM Trans. Math. Softw. 14, 88.
- Bronstein, M. M., Bruna, J., Cohen, T., & Veličković, P. 2021, "Geometric Deep Learning: Grids, Groups, Graphs, Geodesics, and Gauges", arXiv:2104.13478.
- Burbidge, E. M., Burbidge, G. R., Fowler, W. A., & Hoyle, F. 1957 (B²FH), "Synthesis of the Elements in Stars", Rev. Mod. Phys. 29, 547.
- Caflisch, R. E., Morokoff, W., & Owen, A. B. 1997, "Valuation of mortgage-backed securities using Brownian bridges to reduce effective dimension", J. Comput. Finance 1(1), 27.
- Calder, A. C., et al. 2007, "Capturing the Fire: Flame Energetics and Neutronization for Type Ia Supernova Simulations", ApJ 656, 313. arXiv:astro-ph/0611009.
- Chan, T. F. 1987, "Rank revealing QR factorizations", Linear Algebra Appl. 88–89, 67.
- Chugunov, A. I., DeWitt, H. E., & Yakovlev, D. G. 2007, "Coulomb tunneling for fusion reactions in dense matter: Path integral Monte Carlo versus mean field", Phys. Rev. D 76, 025028. arXiv:0707.3500.
- Chung, K. L. 1949, "An estimate concerning the Kolmogoroff limit distribution", Trans. Am. Math. Soc. 67, 36.
- CODATA 2022 — recommended values of the fundamental physical constants, via the NIST Reference on Constants, Units, and Uncertainty (physics.nist.gov/cuu).
- Couch, S. M., Chatzopoulos, E., Arnett, W. D., & Timmes, F. X. 2015, "The Three-dimensional Evolution to Core Collapse of a Massive Star", ApJL 808, L21. arXiv:1503.02199.
- Cyburt, R. H., et al. 2010, "The JINA REACLIB Database: Its Recent Updates and Impact on Type-I X-ray Bursts", ApJS 189, 240. (Chapter definitions verified against the JINA REACLIB format page, reaclib.jinaweb.org.)
- Diehl, R., et al. 2015, "SN2014J gamma rays from the ⁵⁶Ni decay chain", A&A 574, A72. arXiv:1409.5477.
- Eisberg, R. & Resnick, R. 1985, *Quantum Physics of Atoms, Molecules, Solids, Nuclei, and Particles*, 2nd ed. (Wiley), p. 528 (SEMF coefficient set).
- ENSDF — Evaluated Nuclear Structure Data File, via NNDC NuDat3 (nndc.bnl.gov) and the IAEA Live Chart of Nuclides (level energies, half-lives).
- Farmer, R. — `bbq`, a one-zone nuclear burning wrapper around MESA. Zenodo, doi:10.5281/zenodo.7585202.
- Farmer, R., Fields, C. E., Petermann, I., et al. 2016, "On Variations of Pre-supernova Model Properties", ApJS 227, 22. arXiv:1611.01207 (source of the hardwired/softwired network taxonomy).
- Fewell, M. P. 1995, "The atomic nuclide with the highest mean binding energy", Am. J. Phys. 63, 653.
- Fuller, G. M., Fowler, W. A., & Newman, M. J. (FFN) 1980, ApJS 42, 447; 1982, ApJS 48, 279; 1985, ApJ 293, 1. (Pre-arXiv; process list verified via Langanke & Martínez-Pinedo 2003 and Heger et al. 2001.)
- Gilmer, J., Schoenholz, S. S., Riley, P. F., Vinyals, O., & Dahl, G. E. 2017, "Neural Message Passing for Quantum Chemistry", ICML 70, 1263. arXiv:1704.01212.
- Goldberg, D. 1991, "What Every Computer Scientist Should Know About Floating-Point Arithmetic", ACM Comput. Surv. 23, 5.
- Golub, G. H. & Van Loan, C. F. 2013, *Matrix Computations*, 4th ed. (Johns Hopkins Univ. Press).
- Grichener, A., et al. 2025, "Nuclear Neural Networks: Emulating Late Burning Stages in Core Collapse Supernova Progenitors", ApJS 279, 49. arXiv:2503.00115 (dataset: Zenodo 14873443).
- Guidry, M. W., et al. 2013, "Explicit integration of extremely stiff reaction networks", Comput. Sci. Disc. 6, 015001 (asymptotic methods) & 015003 (partial equilibrium methods). arXiv:1112.4716, arXiv:1112.4738.
- Hairer, E., Nørsett, S. P., & Wanner, G. 1993, *Solving Ordinary Differential Equations I*, 2nd ed. (Springer).
- Hairer, E. & Wanner, G. 1996, *Solving Ordinary Differential Equations II: Stiff and Differential-Algebraic Problems*, 2nd ed. (Springer).
- Heger, A., Woosley, S. E., Martínez-Pinedo, G., & Langanke, K. 2001, "Presupernova Evolution with Improved Rates for Weak Interactions", ApJ 560, 307. arXiv:astro-ph/0011507.
- Higham, N. J. 2002, *Accuracy and Stability of Numerical Algorithms*, 2nd ed. (SIAM).
- Hirata, K., et al. 1987, "Observation of a neutrino burst from the supernova SN1987A", Phys. Rev. Lett. 58, 1490.
- Hix, W. R. & Thielemann, F.-K. 1996, "Silicon Burning. I. Neutronization and the Physics of Quasi-Equilibrium", ApJ 460, 869. arXiv:astro-ph/9511088.
- Hix, W. R. & Thielemann, F.-K. 1999a, "Silicon Burning. II. Quasi-Equilibrium and Explosive Burning", ApJ 511, 862. arXiv:astro-ph/9808203.
- Hix, W. R. & Thielemann, F.-K. 1999b, "Computational methods for nucleosynthesis and nuclear energy generation", J. Comput. Appl. Math. 109, 321. arXiv:astro-ph/9906478.
- Hix, W. R., Parete-Koon, S. T., Freiburghaus, C., & Thielemann, F.-K. 2007, "The QSE-reduced Nuclear Reaction Network for Silicon Burning", ApJ 667, 476.
- Iliadis, C., Longland, R., Champagne, A. E., Coc, A., & Fitzgerald, R. 2010, "Charged-particle thermonuclear reaction rates II: Tables and graphs of reaction rates and probability density functions", Nucl. Phys. A 841, 31.
- Itoh, N., Hayashi, H., Nishikawa, A., & Kohyama, Y. 1996, "Neutrino Energy Loss in Stellar Interiors. VII. Pair, Photo-, Plasma, Bremsstrahlung, and Recombination Neutrino Processes", ApJS 102, 411.
- Janka, H.-T. 2012, "Explosion Mechanisms of Core-Collapse Supernovae", Annu. Rev. Nucl. Part. Sci. 62, 407. arXiv:1206.2503.
- Janka, H.-T. 2017, "Neutrino Emission from Supernovae", in *Handbook of Supernovae* (Springer). arXiv:1702.08713.
- Janka, H.-T., Langanke, K., Marek, A., Martínez-Pinedo, G., & Müller, B. 2007, "Theory of core-collapse supernovae", Phys. Rep. 442, 38. arXiv:astro-ph/0612072.
- Jerkstrand, A., et al. 2015, "Constraints on explosive silicon burning in core-collapse supernovae from measured Ni/Fe ratios", ApJ 807, 110.
- Jermyn, A. S., et al. 2023, "Modules for Experiments in Stellar Astrophysics (MESA): Time-dependent Convection, Energy Conservation, Automatic Differentiation, and Infrastructure", ApJS 265, 15. arXiv:2208.03651.
- Joe, S. & Kuo, F. Y. 2008, "Constructing Sobol sequences with better two-dimensional projections", SIAM J. Sci. Comput. 30, 2635.
- José, J. & Iliadis, C. 2011, "Nuclear astrophysics: the unfinished quest for the origin of the elements", Rep. Prog. Phys. 74, 096901. arXiv:1107.2234.
- Kato, C., Ishidoshiro, K., & Yoshida, T. 2020, "Theoretical Prediction of Presupernova Neutrinos and Their Detection", Annu. Rev. Nucl. Part. Sci. 70, 121. arXiv:2006.02519.
- Kim, Y., et al. 2026, "NuGNN: a Graph Neural Network for Nuclear Reaction Network Equations", arXiv:2606.04491.
- Krane, K. S. 1988, *Introductory Nuclear Physics* (Wiley).
- Langanke, K. & Martínez-Pinedo, G. 2000, "Shell-model calculations of stellar weak interaction rates II: Weak rates for nuclei in the mass range A = 45–65 in supernovae environments", Nucl. Phys. A 673, 481. arXiv:nucl-th/0001018.
- Langanke, K. & Martínez-Pinedo, G. 2001, "Rate tables for the weak processes of pf-shell nuclei in stellar environments", At. Data Nucl. Data Tables 79, 1.
- Langanke, K. & Martínez-Pinedo, G. 2003, "Nuclear weak-interaction processes in stars", Rev. Mod. Phys. 75, 819. arXiv:nucl-th/0203071.
- Li, Q., Han, Z., & Wu, X.-M. 2018, "Deeper Insights into Graph Convolutional Networks for Semi-Supervised Learning", AAAI 32. arXiv:1801.07606.
- Li, Z., et al. 2021, "Fourier Neural Operator for Parametric Partial Differential Equations", ICLR. arXiv:2010.08895.
- Limongi, M. 2017, "Supernovae from Massive Stars", in *Handbook of Supernovae* (Springer). arXiv:1706.01913.
- Lu, L., Jin, P., Pang, G., Zhang, Z., & Karniadakis, G. E. 2021, "Learning nonlinear operators via DeepONet based on the universal approximation theorem of operators", Nat. Mach. Intell. 3, 218. arXiv:1910.03193.
- Maas, U. & Pope, S. B. 1992, "Simplifying chemical kinetics: Intrinsic low-dimensional manifolds in composition space", Combust. Flame 88, 239.
- MESA issue #575 — "Bug in the nuclear reaction rates of reactions with more than two reactants and/or products", github.com/MESAHub/mesa/issues/575 (opened 2023-08-07; fixed via PR #632).
- Mitchell, G. E., Richter, A., & Weidenmüller, H. A. 2010, "Random matrices and chaos in nuclear physics: nuclear reactions", Rev. Mod. Phys. 82, 2845. arXiv:1001.2422.
- Morris, C., et al. 2019, "Weisfeiler and Leman Go Neural: Higher-Order Graph Neural Networks", AAAI 33, 4602. arXiv:1810.02244.
- Niederreiter, H. 1992, *Random Number Generation and Quasi-Monte Carlo Methods* (SIAM).
- O'Connor, E. & Ott, C. D. 2011, "Black Hole Formation in Failing Core-Collapse Supernovae", ApJ 730, 70. arXiv:1010.5550.
- Oda, T., Hino, M., Muto, K., Takahara, M., & Sato, K. 1994, "Rate tables for the weak processes of sd-shell nuclei in stellar matter", At. Data Nucl. Data Tables 56, 231.
- Otsuka, T., Gade, A., Sorlin, O., Suzuki, T., & Utsuno, Y. 2020, "Evolution of shell structure in exotic nuclei", Rev. Mod. Phys. 92, 015002. arXiv:1805.06501.
- Owen, A. B. 1997a, "Monte Carlo variance of scrambled net quadrature", SIAM J. Numer. Anal. 34, 1884.
- Owen, A. B. 1997b, "Scrambled net variance for integrals of smooth functions", Ann. Statist. 25, 1541.
- Owen, A. B. 2008, "Local antithetic sampling with scrambled nets", Ann. Statist. 36, 2319.
- Owen, A. B. 2022, "On dropping the first Sobol' point", in *Monte Carlo and Quasi-Monte Carlo Methods 2020* (Springer). arXiv:2008.08051.
- Owen, A. B. & Rudolf, D. 2021, "A strong law of large numbers for scrambled net integration", SIAM Rev. 63, 360. arXiv:2002.07859.
- Patton, K. M., Lunardini, C., Farmer, R. J., & Timmes, F. X. 2017, "Neutrinos from beta processes in a presupernova: probing the isotopic evolution of a massive star", ApJ 840, 2. arXiv:1511.02820.
- Paxton, B., et al. 2011, "Modules for Experiments in Stellar Astrophysics (MESA)", ApJS 192, 3. arXiv:1009.1622.
- Pitrou, C., Coc, A., Uzan, J.-P., & Vangioni, E. 2018, "Precision big bang nucleosynthesis with improved Helium-4 predictions", Phys. Rep. 754, 1. arXiv:1801.08023.
- Rauscher, T. 2003, "Nuclear Partition Functions at Temperatures Exceeding 10¹⁰ K", ApJS 147, 403. arXiv:astro-ph/0304047.
- Rauscher, T. & Thielemann, F.-K. 2000, "Astrophysical reaction rates from statistical model calculations", At. Data Nucl. Data Tables 75, 1. arXiv:astro-ph/0004059.
- Salpeter, E. E. 1954, "Electron screening and thermonuclear reactions", Aust. J. Phys. 7, 373.
- Shapiro, S. L. & Teukolsky, S. A. 1983, *Black Holes, White Dwarfs, and Neutron Stars* (Wiley), ch. 2 (neutronization thresholds).
- Smith, A. I., et al. 2023, "pynucastro: A Python Library for Nuclear Astrophysics", ApJ 947, 65. arXiv:2210.09965.
- Sobol', I. M. 1967, "On the distribution of points in a cube and the approximate evaluation of integrals", USSR Comput. Math. Math. Phys. 7, 86.
- Strang, G. 1968, "On the construction and comparison of difference schemes", SIAM J. Numer. Anal. 5, 506.
- Suwa, Y., Yoshida, T., Shibata, M., Umeda, H., & Takahashi, K. 2018, "On the minimum mass of neutron stars", MNRAS 481, 3305. arXiv:1808.02328.
- Timmes, F. X., Woosley, S. E., & Weaver, T. A. 1996, "The Neutron Star and Black Hole Initial Mass Function", ApJ 457, 834. arXiv:astro-ph/9510136 (PostScript-only source; thermal-correction attribution verified via Suwa et al. 2018).
- Tobin, J. 1958, "Estimation of relationships for limited dependent variables", Econometrica 26, 24.
- Wang, M., Huang, W. J., Kondev, F. G., Audi, G., & Naimi, S. 2021, "The AME2020 atomic mass evaluation (II). Tables, graphs and references", Chin. Phys. C 45, 030003 (companion: Huang et al. 2021, Chin. Phys. C 45, 030002). Values fetched from IAEA AMDC / Live Chart.
- Woosley, S. E., Arnett, W. D., & Clayton, D. D. 1973, "The Explosive Burning of Oxygen and Silicon", ApJS 26, 231. (Pre-arXiv; QSE-linkage content verified via Hix & Thielemann 1996.)
- Woosley, S. E., Heger, A., & Weaver, T. A. 2002 (WHW02), "The evolution and explosion of massive stars", Rev. Mod. Phys. 74, 1015. (No arXiv posting; stage tables verified via the 15 M⊙ table reproduced in Pols's lecture notes ch. 12 and Woosley's own AY220 course tables.)
- Xu, K., Hu, W., Leskovec, J., & Jegelka, S. 2019, "How Powerful are Graph Neural Networks?", ICLR. arXiv:1810.00826.
