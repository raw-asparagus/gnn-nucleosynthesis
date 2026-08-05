# Tier 1 — Microphysics

**Complete deep dive: where a single number λ_j(T, ρ, Yₑ) comes from.**

Thermonuclear reaction-rate theory from cross-sections up, the REACLIB fit
library and its evaluation (**S2**), detailed balance and the partition-function
gate (**S3**), plasma screening (**S4**), the weak sector (**S5**), and the
MESA ⟷ pynucastro reconciliation that makes the whole rate set trustworthy
(**S6**).

Everything needed before Tier 2 (stoichiometry, fluxes, and the conservation
algebra), in one document.

---

## Status of this document

**Personal study material, not project spec.** Deliberately written without
reference to `docs/` — everything is derived from first principles or read off
the business code, configs, notebooks, and tests.

- Textbook physics and derivations here are **mine to check**, not citable
  project output. Where I compute a number myself (Gamow peaks, screening
  factors, Fermi energies, coefficient dissections) it is tagged
  **[derived here]** — reproducible from the snippets given, but not a
  `RESULTS.md` row.
- Measured project numbers quoted here originate in `RESULTS.md` with script +
  commit + data provenance, tagged **[RESULTS]**. This file is **not** their
  source of truth; if a number here disagrees with `RESULTS.md`, `RESULTS.md`
  wins.

Notation follows the repo and Tier 0: unicode math, `⁵⁵Co` in prose, `co55` in
code-adjacent contexts, Yₑ / ν / φ / κ as in the codebase. Section references
of the form §0.x, §I.x, §V.x point back into [`tier0.md`](tier0.md).

---

## How to study each node

```
  ① DERIVE      pen-and-paper: get the equation from physics before reading code
  ② READ        the module, top-to-bottom; its docstring states the contract
  ③ ORACLE      the test file — it encodes what "correct" means, numerically
  ④ SEE         the notebook figure — the measured behaviour on real data
```

Tier 1 is the tier where ① is heaviest and ③ is subtlest. Two of its five
nodes (**S3**, **S6**) exist *only* because a measurement contradicted an
assumption; their tests encode the contradiction, not a textbook identity.

---

## Contents

| Part | Covers |
|---|---|
| [**I** — Rate theory](#part-i--the-theory-of-a-thermonuclear-reaction-rate) | ⟨σv⟩ from cross-sections, Coulomb barrier & Gamow peak, resonances & Hauser–Feshbach, photodisintegration, what the rates *do* in Si burning |
| [**II** (S2) — REACLIB](#part-ii-s2--reaclib-the-library-and-its-evaluation) | The seven-coefficient form derived, sets/chapters/labels, λ → gross flux R_j, the compiled evaluator |
| [**III** (S3) — Detailed balance](#part-iii-s3--detailed-balance-⚠-the-load-bearing-node) | The reverse/forward ratio derived in full, the phase-space factor per \|ΔN\|, partition functions, the v-flag dissection, κ as the DB test, gh-575 |
| [**IV** (S4) — Screening](#part-iv-s4--screening) | Debye–Hückel derived, Γ regimes, chugunov_2007 term-by-term, the per-reaction pairing and its κ consequence |
| [**V** (S5) — The weak sector](#part-v-s5--the-weak-sector) | Fermi golden rule → ft → allowed rates, Gamow–Teller, EC in a degenerate plasma, the (T, ρYₑ) tables, table families, the network asymmetry |
| [**VI** (S6) — Reconciliation](#part-vi-s6--rate-reconciliation) | Canonical keys, membership vs values, dispositions, the measured comparison, the Fortran probe, what it licenses |
| [**VII** — Executable policy](#part-vii--the-guards-tier-1-as-executable-policy) | `fluxes/guards.py`: the four Tier-1 gates as code that refuses to run |
| [**VIII** — Open prerequisites](#part-viii--open-prerequisites-what-is-still-not-covered) | Standing cross-tier register. Two audit passes: the physics the code implements (**§VIII.C**, ten gaps) and the project's own spec documents vs the study map (**§VIII.E** — an entire missing **Tier 4**: the model, its conditioning, its training) |

<details>
<summary>Full section list</summary>

```
1.1  From cross-section to ⟨σv⟩    1.1.1 rate per volume · 1.1.2 double counting
                                   1.1.3 the molar convention · 1.1.4 code contract
1.2  Coulomb barrier & Gamow peak  1.2.1 tunnelling · 1.2.2 the S-factor
                                   1.2.3 saddle point → E₀, Δ · 1.2.4 numbers in the box
                                   1.2.5 neutrons have no Gamow peak
                                   1.2.6 the 1/v law · the reciprocity theorem
1.3  Resonances & Hauser–Feshbach  narrow-resonance rate · the HF regime
                                   1.3.3 where the uncertainty actually is
                                   1.3.4 Γ/D, level densities, the Wigner limit
                                   1.3.5 ⚠ ground-state vs stellar rates (SEF)
1.4  Photodisintegration           the Planck tail · the Q/kT exponential
                                   worked crossover ²⁸Si ⇌ ³²S · why QSE turns on at ~3 GK
                                   1.4.4 LTE for photons · triple-α & the Hoyle state
1.5  What the rates do             mapping Part I onto the Tier-0 topology
1.6  self-check

II.1 The seven-coefficient form    II.5  Code: the coefficient tensor
II.2 Sets, chapters, labels        II.6  Oracle: the 5e-12 gate
II.3 One rate dissected            II.6b λ's 75-decade range; overflow/underflow
II.4 λ → R_j                       II.6c multiple sets; fit validity range
                                   II.7  A fit library, not a theory · II.8 self-check

III.1 DB from chemical equilibrium III.7  gh-575 derived from the same algebra
III.2 The phase-space factor       III.8  Code: db_reverses + the pf gate
III.3 Partition functions          III.9  Oracles
      ⚠ the G vs (2J+1)G trap      III.10 The two κ conventions
      spline extrapolation         III.11 Coulomb corrections to NSE
III.4 Three ways to build a reverse III.12 Q(T) derived + measured
III.5 The v-flag dissected         III.13 self-check
III.6 κ as the numerical DB test

IV.1 Why screening exists          IV.6  Per-reaction pairs
IV.2 Debye–Hückel derived          IV.7  The screened-κ offset derived
IV.3 Strong screening & Γ          IV.8  Code + oracle
      the free-energy derivation   IV.9  Screening of the WEAK sector (MU/DQ/VS)
IV.4 Where the box sits            IV.10 self-check
IV.5 chugunov_2007 term by term

V.1 Why weak is categorical        V.6  The three channels & the ledger
V.2 Golden rule → ft               V.7  The table families
V.3 Gamow–Teller strength          V.8  Neutrino losses
V.4 EC in a degenerate plasma      V.9  Code
      V.4b Pauli blocking = the ratchet   V.10 The mesa_80/151 asymmetry
V.5 The (T, ρYₑ) table             V.11 self-check
      V.5b interpolation error derived

VI.1 Why this node exists          VI.6  Appendix-B as a measurement
VI.2 The canonical key             VI.7  The screening determination
VI.3 Membership vs values          VI.8  The Fortran probe
VI.4 The disposition algebra       VI.8b probe modes & the grid
VI.5 The measured comparison       VI.8c reading the statistics honestly
                                   VI.9  What it licenses · VI.10 self-check

VIII.A deferred by design          VIII.C ⚠ ten genuine gaps (physics pass)
VIII.B closed in this revision     VIII.D the common-mode habit
                                   VIII.E ⚠⚠ the missing TIER 4 (spec pass)
                                   VIII.F priorities across both passes
```

</details>

---

# Part I — The theory of a thermonuclear reaction rate

Tier 0 treated λ_j as a black box: a number that arrives from somewhere and
multiplies abundances. This part opens the box. The target is to be able to
answer, for any column j of ν, *what physical quantity is being evaluated, what
approximations are inside it, and how well is it known* — because every
downstream gate in this project is a statement about agreement between two
evaluations of that quantity.

| § | Area | Why it is prerequisite, not optional |
|---|---|---|
| 1.1 | ⟨σv⟩ and its conventions | The molar/double-counting bookkeeping is where sign-and-factor bugs live; the code contract in `compile.py` is unreadable without it |
| 1.2 | Coulomb barrier, Gamow peak | Explains the *functional form* of the REACLIB fit — three of the seven coefficients are the Gamow integral |
| 1.3 | Resonances, Hauser–Feshbach | Explains where the rates come from and hence the irreducible uncertainty floor (§0.3.3) |
| 1.4 | Photodisintegration | Explains why QSE turns on at ~3 GK and why reverse rates are the whole story here |

## 1.1 From cross-section to ⟨σv⟩

### 1.1.1 The reaction rate per unit volume

Two species 1 and 2 with number densities n₁, n₂ and relative velocity v. In
time dt a particle of species 1 sweeps a volume σ(v)·v·dt; the number of
reactions per unit volume per unit time is

$$
r_{12} = n_1 n_2 \,\sigma(v)\,v
$$

In a plasma v is distributed. Non-relativistically and in the absence of
degeneracy for the *ions* (which holds throughout the box — §0.1.3 established
that the electrons are degenerate but the ions are not), the relative velocity
of an uncorrelated pair is Maxwell–Boltzmann with the **reduced mass**

$$
\mu = \frac{m_1 m_2}{m_1+m_2}
$$

so that

$$
\phi(v)\,dv = 4\pi v^2 \left(\frac{\mu}{2\pi kT}\right)^{3/2}
              e^{-\mu v^2/2kT}\,dv
$$

and the thermally averaged rate coefficient is

$$
\langle\sigma v\rangle = \int_0^\infty \sigma(v)\,v\,\phi(v)\,dv
$$

Changing variable to the centre-of-mass kinetic energy E = ½μv²,

$$
\boxed{\;
\langle\sigma v\rangle
= \left(\frac{8}{\pi\mu}\right)^{1/2}\!\!(kT)^{-3/2}
  \int_0^\infty \sigma(E)\,E\,e^{-E/kT}\,dE
\;}
\tag{1.1}
$$

**Everything in Part I is an evaluation of the integral in (1.1).** The three
regimes (non-resonant barrier penetration, isolated resonance, statistical
continuum) are three different σ(E), and the REACLIB seven-coefficient form is
a fitting basis wide enough to hold all three.

> Note the assumption you just made: that the two colliding nuclei are in their
> **ground states** and that their relative motion is thermal and uncorrelated.
> The first fails at these temperatures — kT = 0.34 MeV at T₉ = 4 and the level
> spacings are ~1 MeV — which is exactly what partition functions repair (§0.2.2,
> and quantitatively §III.3). The second fails once the plasma is strongly
> coupled, which is what screening repairs (§IV).

### 1.1.2 Double counting: the identical-particle factor

The number of *distinct pairs* per unit volume is n₁n₂ for distinct species but
n²/2 for identical ones — writing n₁n₂ would count every pair twice. In general
for a reaction with reactant multiset {…}, the rate per unit volume carries

$$
\frac{1}{\prod_s (c_s!)}
\qquad c_s = \text{multiplicity of species } s \text{ among the reactants}
$$

For 3α → ¹²C, that is 1/3! = 1/6.

**In the code:** this is exactly `Rate.prefactor`, built in pynucastro as

$$
\text{prefactor}_j = \frac{1}{\prod_s c_s!},
\qquad c_s = \text{multiplicity of species } s \text{ among reactants}(j)
$$

and carried through the compile step as the
`prefactor` array (`fluxes/compile.py:286`). It is a *pure combinatorial
factor* with no temperature dependence — which is why it lives outside the
coefficient tensor.

There is a second, independent place the same factorial appears: the
**detailed-balance ratio**, where the forward and reverse multiplicities do not
cancel. pynucastro handles that separately in `DerivedRate.counter_factors()`
(§III.1). Do not conflate the two; a reaction can have prefactor 1 and still
carry a nontrivial counter-factor ratio.

### 1.1.3 Why the molar convention, and what N_A⟨σv⟩ means

Networks integrate molar abundances Y = X/A (§II.3 of Tier 0), so it is
convenient to express rates per mole rather than per particle. Writing
n_i = ρ N_A Y_i, the two-body rate per unit volume becomes

$$
r_{12} = \rho N_A Y_1 \cdot \rho N_A Y_2 \cdot \langle\sigma v\rangle
$$

and the corresponding change in molar abundance per unit time
(dividing by ρN_A, since Ẏ = ṅ/ρN_A) is

$$
\dot Y \sim \rho\,Y_1 Y_2 \cdot \bigl(N_A\langle\sigma v\rangle\bigr)
$$

So the natural tabulated quantity is **N_A⟨σv⟩** in cm³ mol⁻¹ s⁻¹, and each
additional reactant beyond the first brings one power of ρ. That is the entire
content of

$$
\boxed{\;
R_j = \frac{1}{\prod_s c_s!}\;\rho^{\,n_j-1}\;\Bigl(\textstyle\prod_{r\in\text{reactants}(j)} Y_r\Bigr)\;\lambda_j(T,\rho,Y)
\;}
\tag{1.2}
$$

with n_j the number of reactants. R_j is the **gross flux** of column j in
mol g⁻¹ s⁻¹ — the same units as Ẏ, which is what makes ẏ = ν R dimensionally
clean.

**Special cases you must not fumble:**

- **n_j = 1** (photodisintegration, β decay): ρ⁰ = 1, and λ is a plain
  frequency in s⁻¹. Photodisintegration rates are *density-independent* — worth
  internalising, because it is half of why the reverse of a capture behaves so
  differently from the capture itself (§1.4).
- **Yₑ-weighted REACLIB electron captures.** A handful of REACLIB fits (the
  `ec` label; ⁷Be(e⁻,ν)⁷Li is the one in mesa_80) tabulate the rate *per
  electron*, so the physical rate carries an extra factor ρYₑ. pynucastro sets
  `use_ye_weighting`, increments `dens_exp` by one, and multiplies by Yₑ at
  evaluation. The compiled engine mirrors both halves:

  ```python
  ye_weighted[j] = bool(getattr(rate, "use_ye_weighting", False))   # compile.py:285
  ...
  R[cn.ye_weighted] *= ye[None, :]                                   # engine.py:179
  ```

  If you ever see a factor-of-ρYₑ discrepancy on exactly one channel, this is
  the first thing to check.

### 1.1.4 The code contract

`CompiledNetwork` stores exactly the pieces of (1.2):

| Field | Shape | Meaning |
|---|---|---|
| `prefactor` | (n_rxn,) | 1/∏ c_s! |
| `dens_exp` | (n_rxn,) | n_reactants − 1 (+1 if Yₑ-weighted) |
| `reactant_idx` | (n_rxn, max_nr) | species indices, sentinel = n_species |
| `ye_weighted` | (n_rxn,) bool | the ρYₑ carriers |

and `engine.evaluate_fluxes` assembles them:

```python
R = lam * cn.prefactor[:, None] * rho[None, :] ** cn.dens_exp[:, None]
...
Ypad = np.vstack([Y, np.ones((1, n_states))])       # sentinel row = 1.0
for k in range(cn.reactant_idx.shape[1]):
    R *= Ypad[cn.reactant_idx[:, k]]
```

The sentinel trick is worth pausing on: reactions have different arities, so the
reactant index array is ragged. Padding with an index that points at a row of
ones turns the ragged product into a fixed-length dense one, at the cost of one
wasted multiply per unused slot. This is the recurring shape of the whole
`fluxes/` package — *turn per-reaction control flow into dense array algebra*,
which is what makes 7×10⁵ states/min/core possible [RESULTS 2026-07-10].

## 1.2 The Coulomb barrier and the Gamow peak

### 1.2.1 The problem

Two positively charged nuclei must reach ~nuclear-force range against Coulomb
repulsion. The barrier height at contact is

$$
E_C = \frac{Z_1 Z_2 e^2}{R}, \qquad R \approx 1.2\,\bigl(A_1^{1/3}+A_2^{1/3}\bigr)\ \text{fm}
$$

with e² = 1.44 MeV·fm. **[derived here]**

| Pair | E_C |
|---|---|
| ²⁸Si + α | 7.27 MeV |
| ²⁸Si + p | 4.16 MeV |
| ⁵⁶Ni + α | 12.41 MeV |

against kT = 0.26 / 0.34 / 0.43 MeV at T₉ = 3 / 4 / 5. The barrier is **one to
two orders of magnitude above kT everywhere in the box.** Classically nothing
happens. Reactions proceed by tunnelling in the far tail of the Maxwell
distribution, and the interplay of those two exponentials is the whole story.

### 1.2.2 The Gamow factor and the S-factor

The WKB transmission through a pure Coulomb barrier at E ≪ E_C gives the
**Gamow factor**

$$
P(E) \propto \exp\!\left(-\frac{2\pi Z_1Z_2 e^2}{\hbar v}\right)
      = \exp\!\left(-\sqrt{\frac{E_G}{E}}\right),
\qquad
E_G = 2\mu c^2 (\pi \alpha Z_1 Z_2)^2
\tag{1.3}
$$

E_G is the **Gamow energy** (a constant of the pair, not of T). Since the
cross-section also carries the geometric factor σ ∝ πƛ² ∝ 1/E, it is
conventional to strip both known energy dependences and define the
**astrophysical S-factor**

$$
\sigma(E) = \frac{S(E)}{E}\,e^{-\sqrt{E_G/E}}
\tag{1.4}
$$

S(E) is smooth and slowly varying for non-resonant reactions — that is the
entire point of the definition: it isolates the *nuclear* physics from the
*Coulomb* physics, so that experimental data taken at MeV energies can be
extrapolated down to the astrophysically relevant tens-to-hundreds of keV
without extrapolating an exponential.

### 1.2.3 The saddle point: E₀ and Δ

Substituting (1.4) into (1.1) and pulling S out as approximately constant:

$$
\langle\sigma v\rangle \propto \int_0^\infty
\exp\!\left[-\frac{E}{kT} - \sqrt{\frac{E_G}{E}}\right] dE
$$

The integrand is a product of a falling exponential and a rising tunnelling
probability: sharply peaked. Setting the derivative of the exponent to zero,

$$
-\frac{1}{kT} + \frac{1}{2}\frac{\sqrt{E_G}}{E^{3/2}} = 0
\;\Longrightarrow\;
\boxed{\;E_0 = \left(\frac{\sqrt{E_G}\,kT}{2}\right)^{2/3}
        = \left(\frac{E_G (kT)^2}{4}\right)^{1/3}\;}
\tag{1.5}
$$

— the **Gamow peak**. Expanding the exponent to second order about E₀ gives a
Gaussian of width

$$
\Delta = \frac{4}{\sqrt{3}}\sqrt{E_0\,kT}
\tag{1.6}
$$

and evaluating the exponent at the peak,

$$
\frac{E_0}{kT} + \sqrt{\frac{E_G}{E_0}} = 3\frac{E_0}{kT} \equiv \tau,
\qquad
\tau = 3\left(\frac{E_G}{4kT}\right)^{1/3} \propto T^{-1/3}
\tag{1.7}
$$

so that, with the Gaussian integral supplying a factor Δ ∝ T^{2/3}·T^{-1/3}…
collecting the powers carefully:

$$
\boxed{\;
N_A\langle\sigma v\rangle \;\propto\;
\frac{S(E_0)}{\mu\,Z_1Z_2}\;\tau^2 e^{-\tau}
\;\propto\; T^{-2/3}\exp\!\left(-\,a\,T^{-1/3}\right)
\;}
\tag{1.8}
$$

(the T dependence is the whole point: τ ∝ T^{−1/3} from (1.7), so τ² supplies
exactly the T^{−2/3} prefactor.)

**This is the single most important equation in Tier 1**, because it is
literally the shape of the REACLIB fit. In practical units,

$$
\tau = 4.2487\,\bigl(Z_1^2 Z_2^2\,\mu_{\rm amu}\,/\,T_9\bigr)^{1/3}
\tag{1.9}
$$

### 1.2.4 The numbers in this box

Evaluating (1.5)–(1.6) at box temperatures **[derived here]**:

| Pair | T₉ | E₀ (MeV) | Δ (MeV) | kT (MeV) |
|---|---|---|---|---|
| ²⁸Si + α | 3.0 | 3.55 | 2.21 | 0.259 |
| | 4.0 | 4.30 | 2.81 | 0.345 |
| | 5.0 | 4.99 | 3.39 | 0.431 |
| ²⁸Si + p | 4.0 | 1.77 | 1.80 | 0.345 |
| ⁵⁶Ni + α | 4.0 | 6.98 | 3.58 | 0.345 |
| ⁵⁴Fe + p | 4.0 | 2.68 | 2.22 | 0.345 |

Three things to take from this table.

1. **E₀ ≫ kT by an order of magnitude.** Reactions are powered by particles in
   the far Maxwell tail; the effective energy is set by the *barrier*, not the
   temperature.
2. **Δ is comparable to E₀ here — but so it is everywhere.** Combining
   (1.5)–(1.7) gives the exact identity **Δ/E₀ = 4/√τ**, so the *relative*
   width is set by τ alone. At T₉ = 4 for ²⁸Si+α, τ = 37.5 ⇒ Δ/E₀ = 0.65;
   at hydrogen-burning temperatures it is not dramatically smaller
   (¹²C(p,γ) at T₉ = 0.02: τ = 50.3 ⇒ 0.56; p+p at T₉ = 0.015: τ = 13.7
   ⇒ 1.08). **[derived here]** The "narrow Gamow window" is never narrow in
   the Δ/E₀ sense — Δ/E₀ = 0.1 would need τ ≈ 1600, which no astrophysical
   pair reaches. What actually changes between the two regimes is the
   *absolute* width against the level spacing: Δ ≈ 3 MeV here versus a few
   keV in hydrogen burning. That is the formal reason the *statistical*
   (Hauser–Feshbach) treatment is the right one in this box — the window
   spans hundreds of levels — and it is a statement about Δ, not about Δ/E₀.
3. **E₀ is still below E_C** (4.3 vs 7.27 MeV for Si+α): tunnelling, not
   over-the-barrier. But not by the factor of 30 that low-temperature
   nucleosynthesis enjoys — silicon burning sits in an awkward middle where
   neither the deep-tunnelling nor the classical limit is clean.

A useful sanity identity: τ from (1.9) at T₉ = 1 for ²⁸Si+α gives
**τ = 59.48**, and E₀ = τkT/3 reproduces the table exactly. Hold that number —
it reappears verbatim in §II.3 as a REACLIB coefficient.

### 1.2.5 Neutrons have no Gamow peak

Z₂ = 0 kills E_G, so (1.3)–(1.8) collapse. For neutron capture, σ ∝ 1/v at low
energy (the 1/v law, from phase space alone), so ⟨σv⟩ → constant, and the
temperature dependence of an (n,γ) rate is weak and non-exponential.

This has a structural consequence that matters far beyond S2: **(n,γ)/(γ,n)
pairs are the fastest in the network and set the stiffness ceiling** (§0.5's
channel table said so; now you know why). They equilibrate first, they dominate
the QSE cluster interior, and they are the pairs whose κ collapses earliest.

### 1.2.6 The 1/v law, derived — and the reciprocity theorem

Both deserve doing properly, because §1.2.5 asserted the first and Part III
leans on the second.

**The 1/v law.** For an exothermic reaction with no barrier, the cross-section
at low energy is dominated by the entrance-channel phase space. Write
σ = πƛ²·T(E)·(branching), with ƛ = ℏ/p ∝ 1/√E. For s-wave neutrons the
transmission through the (absent) barrier tends to a constant times k ∝ √E
as E → 0 (the standard threshold law T_ℓ ∝ k^{2ℓ+1}), so

$$
\sigma \propto \frac{1}{E}\cdot\sqrt{E} = \frac{1}{\sqrt E} \propto \frac{1}{v}
\;\Longrightarrow\; \sigma v = \text{const}
$$

Hence ⟨σv⟩ is temperature-independent at low energy, and (n,γ) rates in REACLIB
are nearly flat in T. Contrast the charged-particle case, where the barrier
transmission (1.3) overwhelms everything.

**The reciprocity theorem** is the *microscopic* statement, independent of any
equilibrium assumption. Time-reversal invariance of the strong interaction gives
|⟨b|T|a⟩|² = |⟨a|T|b⟩|², and converting matrix elements to cross-sections by
dividing out incident flux and multiplying by final-state density gives

$$
\boxed{\;
(2J_1+1)(2J_2+1)\,k_{12}^2\,\sigma_{12\to34}
= (2J_3+1)(2J_4+1)\,k_{34}^2\,\sigma_{34\to12}
\;}
\tag{1.11}
$$

with k the centre-of-mass wavenumbers. **This is a relation between cross-sections
at the same total energy, valid reaction-by-reaction, with no reference to a
thermal bath.** Thermally averaging (1.11) with (1.1) reproduces the ratio
(3.4) — spins, masses, the phase-space power, and e^{−Q/kT} all fall out.

Why have both routes? Because they justify different things:

| Route | Says | Used for |
|---|---|---|
| Reciprocity (1.11) | the *rates* are related, always | licenses computing a reverse from a forward at any composition |
| Chemical equilibrium (0.1) | the *fluxes* balance at NSE | licenses κ → 0 as an equilibrium test |

If you only had the second, you could not justify using detailed-balance reverse
rates *out* of equilibrium — which is exactly what the network does at every
timestep. The first is what makes `DerivedRate` legitimate at κ = 0.9998.

## 1.3 Resonances and the Hauser–Feshbach regime

### 1.3.1 The isolated narrow resonance

If the compound nucleus has a level at E_r in the Gamow window, σ(E) is
Breit–Wigner:

$$
\sigma_{BW}(E) = \pi\bar\lambda^2\,\omega\,
\frac{\Gamma_a \Gamma_b}{(E-E_r)^2 + \Gamma^2/4}
$$

For Γ ≪ kT the Lorentzian acts as a delta function inside (1.1), giving

$$
N_A\langle\sigma v\rangle
= 1.54\times10^{11}\,(\mu_{\rm amu} T_9)^{-3/2}\,(\omega\gamma)_{\rm MeV}\,
  \exp\!\left(-\frac{11.605\,E_r[\text{MeV}]}{T_9}\right)
\tag{1.10}
$$

i.e. **λ ∝ T^{-3/2} exp(−E_r/kT)**. Note the constant 11.605 = 1/(k·10⁹ K in
MeV) = 1/0.0861733 — the conversion you will meet again in every Q/kT term in
this document.

Compare (1.8) and (1.10):

| Regime | T dependence of ln λ |
|---|---|
| non-resonant | a₂ T₉^(−1/3) + a₆ ln T₉ with a₆ = −2/3 |
| narrow resonance | a₁ T₉⁻¹ + a₆ ln T₉ with a₆ = −3/2 |

**Two different basis functions.** A fit library that has to hold both needs
*both* T₉⁻¹ and T₉^(−1/3) terms and a free ln T₉ coefficient. That is three of
REACLIB's seven, and §II.1 gets the remaining four.

### 1.3.2 Why Hauser–Feshbach dominates here

Once the level density in the compound nucleus is high enough that many
resonances overlap within the Gamow window, individual levels are neither
resolvable nor relevant. The **statistical model** (Hauser–Feshbach) replaces
them with averaged transmission coefficients:

$$
\sigma_{a b}(E) = \frac{\pi\bar\lambda^2}{(2J_1+1)(2J_2+1)}
\sum_J (2J+1)\frac{T_a^J\,T_b^J}{\sum_c T_c^J}
$$

The inputs are (i) an optical model for the entrance/exit transmissions, (ii) a
level-density prescription, (iii) γ-ray strength functions. All three are
*models*, calibrated where data exist.

**Validity condition:** enough levels in the window. In the Fe-peak at
E₀ ≈ 4–7 MeV excitation with Δ ≈ 3 MeV, this is comfortably satisfied for
mid-shell nuclei — and marginal exactly at shell closures, where level densities
plunge. Note which nuclei those are: ⁵⁶Ni (Z = N = 28) and ⁴⁰Ca (Z = N = 20),
both doubly magic, and ²⁸Si (Z = N = 14), which is not magic but sits at the
d₅/₂ *sub*-shell closure and is correspondingly level-poor. **The most abundant
species in this problem are the ones where the statistical model is weakest.**

That is not quite the coincidence it looks like, though the mechanism differs by
species. ⁵⁶Ni and ⁴⁰Ca are abundant because they are tightly bound *and* their
binding comes from the same shell closure that suppresses their level density —
one cause, two effects. ²⁸Si's abundance has a different origin: it is the last
member of the α ladder to photodisintegrate, because its α separation energy is
9.98 MeV against 6.95 MeV for ³²S (§1.4.3). Its low level density is a
consequence of the sub-shell closure, not of the bottleneck.

### 1.3.3 Where the uncertainty actually is

Tier 0 §0.3.3 gave the summary table; the mechanism is now visible:

| Source | Coverage | Uncertainty | Why |
|---|---|---|---|
| Direct experiment | light nuclei | 10–20% | measured, extrapolated via S(E) |
| Hauser–Feshbach | most (n,γ), (p,γ), (α,γ) mid/heavy | factor ~2 | level density + optical model + γSF |
| Shell-model weak (LMP) | Fe-peak EC/β | factor ~2–10 | Gamow–Teller strength (§V.3) |

The practical consequence, which you should be able to state without hedging:

> **An emulator that reproduces MESA to 10⁻⁶ reproduces MESA, not nature.**
> The project's gates are therefore fidelity-to-labels gates, and every physics
> claim built on them inherits a factor-~2 rate uncertainty that no amount of
> ML accuracy touches.

This is also why **S6** exists. If the underlying rates carry factor-2
uncertainty, then a 0.05 dex (12%) disagreement between two *implementations*
is a bookkeeping question, not a physics question — and bookkeeping questions
have right answers. S6 is the node that separates the two.

### 1.3.4 When are resonances "overlapping"? The Γ/D criterion

The statistical model requires many contributing levels. The quantitative
condition compares the average total width Γ to the average level spacing D at
the relevant excitation energy:

- **Γ/D ≪ 1** — isolated resonances; the rate is a sum of terms like (1.10) and
  is sensitive to individual level positions.
- **Γ/D ≳ 1** — overlapping; individual levels are unresolvable and Hauser–Feshbach
  averaging is appropriate.

Level densities follow a back-shifted Fermi-gas form, ρ(E) ∝ exp(2√(aU))/U^{5/4}
with a ≈ A/8 MeV⁻¹ and U the shifted excitation. Two features matter here:

1. **ρ rises steeply with excitation.** The compound nucleus is formed at
   E* = Q + E₀, which for ²⁸Si(α,γ)³²S is 6.95 + 4.30 ≈ 11 MeV. At A ≈ 32 and
   11 MeV excitation the level density is high — HF is comfortable.
2. **ρ is suppressed at shell closures** by the pairing/shell correction in the
   back-shift. This is the mechanism behind §1.3.2's warning: ⁵⁶Ni, ⁴⁰Ca, ²⁸Si
   sit exactly where the denominator of Γ/D is largest.

There is also a hard ceiling on any single resonance's strength — the **Wigner
limit**, Γ_ℓ ≤ 3ℏ²/(μR²) roughly, i.e. a level cannot be more strongly coupled
to a channel than a single-particle state. Useful as a sanity check when a
tabulated rate looks impossibly large.

### 1.3.5 ⚠ Ground-state versus stellar rates — a partly-settled convention

A subtlety that Tier 0 §0.2.2 gestured at and Part III makes operational, but
which deserves naming as a distinct concept.

A **laboratory** (ground-state) rate assumes the target nucleus is in its ground
state. A **stellar** rate averages over the thermal population of target excited
states:

$$
\langle\sigma v\rangle^{*}
= \frac{\sum_s (2J_s+1)e^{-E_s/kT}\,\langle\sigma v\rangle_s}
       {\sum_s (2J_s+1)e^{-E_s/kT}}
$$

and the **stellar enhancement factor** is SEF = ⟨σv⟩*/⟨σv⟩_{gs}. For most
capture reactions SEF > 1, because excited target states have larger phase space
and often larger cross-sections.

Now the part to be careful about, and the part where the algebra already
constrains the answer more than it first appears.

> **Do the REACLIB forward fits in this network represent ground-state rates or
> stellar rates?** And if ground-state, does either MESA or pynucastro apply a
> separate SEF to the forward before use?

Neither code exposes anything named `sef` / `stellar_enhancement`; the pf
machinery in both is confined to the DB ratio. But note what (3.4) *is*: the
partition-function ratio ∏G_ℛ/∏G_𝒫 appears there because the thermal average
over excited **target** states has already been taken on both sides. The
Rauscher–Thielemann reverse-ratio relation holds between **stellar** rates; it
is not the relation between two ground-state rates. So a pipeline that derives
every reverse through (3.4) — which is exactly what the pf gate mandates — has
already committed to its forwards being stellar. The two branches are therefore
not symmetric:

- **The `ths8r` (NON-SMOKER statistical-model) fits are stellar rates.** This is
  the branch (3.4) presupposes, the pf ratio is then the correct and complete
  treatment, and there is nothing to add. Anything else would make
  `DerivedRate(use_pf=True)` — the project's mandated construction — the wrong
  relation, which the κ-at-NSE collapse to 2.6×10⁻¹² argues strongly against.
- **The genuinely open subset is the experimentally-fitted channels** (`nac2`,
  `ks03` and similar labels), which are laboratory ground-state rates by
  construction, and for which no SEF is visibly applied anywhere. Those carry an
  unapplied O(1) enhancement at these temperatures — a *common-mode* effect
  cancelling in the forward/reverse ratio (so κ and the equilibrium diagnostics
  are untouched) but **not** cancelling in the absolute flux magnitudes that feed
  ΔY and e_nuc.

So the question to actually answer is narrower than "are REACLIB forwards
stellar": it is **which label classes in these two networks are experimental
fits, how much flux do they carry in the Si-burning box, and what is their SEF
there?** Given that the α ladder and the Fe-peak captures are `ths8r`
throughout, the exposure is probably small — but "probably small" on a
systematic multiplier is not a measurement. **Recorded in §VIII as an open
prerequisite, with that narrower scope.**

## 1.4 Photodisintegration: the reverse rates that run this regime

### 1.4.1 A rate with a thermal photon bath

A (γ,α) reaction is driven by the Planck tail: the photon must supply the
separation energy Q. The rate per target nucleus is

$$
\lambda_\gamma(T) = \int_{Q}^\infty c\, n_\gamma(E,T)\,\sigma_{\gamma\alpha}(E)\,dE
$$

and since n_γ ∝ E² /(e^{E/kT} − 1) ≈ E²e^{−E/kT} for E ≫ kT, the rate carries
the factor **e^{−Q/kT}** — steeply increasing in T, and completely
density-independent (§1.1.3).

You do not, in practice, evaluate this integral. **Detailed balance gives
λ_γ from the capture rate exactly** (that is Part III). But it is worth
understanding the physical statement independently, because it explains the
whole shape of silicon burning: the light-particle liberation that drives the α
ladder is a *thermal* process with an exponential threshold, so it switches on
over a narrow temperature range.

### 1.4.2 Worked crossover — ²⁸Si(α,γ)³²S ⇌ ³²S(γ,α)²⁸Si

Compare the forward rate per ²⁸Si nucleus, ρ Y_α N_A⟨σv⟩, against the reverse
rate per ³²S nucleus, λ_γ, at ρ = 10⁸ g/cm³ **[derived here]**:

| T₉ | forward (s⁻¹), Y_α = 10⁻³ | reverse λ_γ (s⁻¹) | reverse/forward |
|---|---|---|---|
| 2.0 | 1.4×10⁴ | 8.2×10⁻⁸ | 5.7×10⁻¹² |
| 2.5 | 1.1×10⁵ | 2.9×10⁻³ | 2.5×10⁻⁸ |
| 3.0 | 4.5×10⁵ | 3.2 | 7.2×10⁻⁶ |
| 3.3 | 8.1×10⁵ | 78 | 9.6×10⁻⁵ |
| 4.0 | 2.2×10⁶ | 2.0×10⁴ | 9.3×10⁻³ |
| 5.0 | 5.0×10⁶ | 3.7×10⁶ | **0.75** |

**Read this table carefully — several project facts fall out of it at once.**

1. **The reverse rate climbs 14 orders of magnitude between T₉ = 2 and 5.**
   The forward climbs by a factor of ~350. Everything about the temperature
   structure of this regime is the reverse rate.
2. **The pair reaches balance at T₉ = 5.10** for Y_α = 10⁻³. Solving
   rev/fwd = 1 from the same coefficients **[derived here]**, the balance point
   moves by **≈ +0.8 in T₉ per decade of Y_α**: 3.31 / 4.50 / 5.10 / 5.87 at
   Y_α = 10⁻⁷ / 10⁻⁴ / 10⁻³ / 10⁻². QSE onset is composition-dependent, not a
   fixed temperature — and the numbers land exactly where the project's band
   does: **Y_α ≈ 10⁻⁷, which is the α abundance early in Si burning, puts this
   pair's balance at T₉ = 3.31.** That is the quantitative content of "QSE onset
   ~3–3.3 GK" being a band, and of the kill-test priority window being 3.3–5 GK
   rather than a point: it is the same pair, walked across four decades of Y_α.
3. **κ is directly readable off the last column.** κ = |f⁺−f⁻|/(f⁺+f⁻), so
   ratio 9.6×10⁻⁵ ⇒ κ ≈ 0.9998 (nowhere near equilibrium) and ratio 0.75 ⇒
   κ ≈ 0.14 (approaching it). The active-set threshold κ > 0.1 sits precisely
   in the transition this table walks through.
4. **The rate that must be *right* is the reverse — but be careful about why.**
   κ depends only on the *ratio* f⁻/f⁺, so it is exactly as sensitive to a 20%
   error in the forward as to one in the reverse; "f⁺ − f⁻ is a small difference
   of large numbers" is true but symmetric, and is not on its own an argument
   for privileging the reverse. The asymmetry comes from *how the two are
   built*: the reverse is constructed **from** the forward through (3.4), so an
   error in the forward propagates into the reverse and **cancels exactly** in
   the ratio — it is common-mode (§VIII.D). Only an error in the detailed-balance
   factor itself — a missing partition-function ratio, a missing power of
   fac·T₉^{3/2} — survives into κ, and it survives at full strength because
   κ is a condition number (§V.1 of Tier 0). **That is the physical reason S3 is
   the load-bearing node and why the pf gate is blocking:** the gate protects the
   one factor that has no common-mode partner.

### 1.4.3 Why ~3 GK

Set the reverse rate of the *weakest-bound* abundant species equal to its
destruction rate. The α separation energy of ²⁸Si is 9.98 MeV, of ³²S 6.95 MeV,
and the exponential e^{−Q/kT} at Q ≈ 7 MeV gives

$$
\frac{d\ln\lambda_\gamma}{d\ln T} \approx \frac{Q}{kT} \approx 27 \ \text{at } T_9=3
$$

A 10% temperature rise multiplies the photodisintegration rate by e^{2.7} ≈ 15.
That extreme sensitivity is what makes the QSE transition sharp in temperature
and what makes the label distribution so structured (§IV.2 of Tier 0 — the
reachable manifold).

### 1.4.4 Two assumptions inside the photon rate

**Is the photon field Planckian?** Photodisintegration assumes an equilibrium
blackbody spectrum at the matter temperature. That requires the photon mean free
path to be short compared with the temperature scale height and the
photon–matter coupling time short compared with the burning time. At ρ ≥ 10⁷
g/cm³ the Thomson mean free path is ~10⁻² cm against structure scales of
10⁷–10⁸ cm, so the medium is optically thick by twenty orders of magnitude.
**LTE for photons is safe here** — which is worth stating once, because it is
the assumption that fails for the neutrinos (§0.4.2) and the contrast is the
whole reason Yₑ is a one-way variable.

**Triple-α, and why it is chapter 8.** The reaction 3α → ¹²C is not a genuine
three-body collision. It proceeds sequentially: α + α ⇌ ⁸Be (unbound, lifetime
~10⁻¹⁶ s, held at a small equilibrium abundance), then ⁸Be + α → ¹²C* through
the **Hoyle state** at 7.65 MeV, which then γ-decays. REACLIB folds the ⁸Be
equilibrium abundance into an effective three-body rate — hence chapter 8
(3 → 1) and the ρ² density dependence, and hence `prefactor` = 1/3! = 1/6.

Two consequences:

1. Its reverse ¹²C → 3α is a **chapter-8 inverse with ΔN_s = −2**, requiring two
   powers of the phase-space factor — which is exactly the class stock MESA gets
   wrong by ~10 dex (§III.7), and it is the flagship member of the
   `photo_of_multibody` class in `appendixb_excluded_channels.yaml`.
2. The "effective rate" construction embeds an equilibrium assumption (⁸Be in
   equilibrium with α) *inside a rate coefficient*. That is a QSE approximation
   hiding one level down from the QSE machinery this project builds — worth
   noticing, because it means the network is already, quietly, a reduced model.

## 1.5 What the rates do — mapping Part I onto the Tier-0 topology

Tier 0 §0.6 gave the α ladder and the two-cluster structure; you can now
annotate it with mechanism:

```
   ²⁸Si ─(α,γ)→ ³²S ─(α,γ)→ ³⁶Ar ─(α,γ)→ ⁴⁰Ca ─(α,γ)→ ⁴⁴Ti ⋯ ⁵⁶Ni
        ←(γ,α)─      ←(γ,α)─      ←(γ,α)─      ←(γ,α)─
        ▲                                            ▲
        │ forward: Gamow-peak tunnelling,            │ same, but E₀ larger
        │ E₀ ≈ 4.3 MeV, weakly T-dependent           │ (6.98 MeV for Ni+α)
        │ reverse: e^{−Q/kT}, 14 decades over the box
```

- **The forward rates set the *scale*; the reverse rates set the *structure*.**
  Every κ, every equilibrium mask, every QSE cluster boundary is a statement
  about a reverse rate.
- **(n,γ)/(γ,n) pairs equilibrate first** (no barrier, §1.2.5), then
  (p,γ)/(γ,p), then (α,γ)/(γ,α) — the ordering of cluster formation.
- **The weak reactions are outside all of this.** No barrier, no photon bath, no
  detailed-balance partner in the network (§V.1). They set Yₑ, they are slow,
  and they are the reason the composition is a *constrained* optimum (§0.3.2).

## 1.6 Self-check for Part I

1. Derive (1.1) from r₁₂ = n₁n₂σv by changing variables from v to E. Where does
   the (8/πμ)^{1/2} come from?
2. Compute E₀ and Δ for ³²S(α,γ)³⁶Ar at T₉ = 3.5 from (1.5)–(1.6). Is Δ/E₀
   larger or smaller than for ²⁸Si+α, and why?
3. Explain in one sentence why an (n,γ) rate is nearly temperature-independent
   while its (γ,n) reverse spans 14 decades over the same range.
4. A reaction has prefactor 1/2 and dens_exp 1. What is its arity, and what are
   its reactants? Now do the same for prefactor 1/6.
5. Estimate the temperature at which ³²S(γ,α) balances ³²S production at
   ρ = 10⁹, Y_α = 10⁻². Which direction does raising ρ move it, and why does
   that follow from §1.1.3 rather than from any nuclear physics?
6. Given factor-2 Hauser–Feshbach uncertainties, write the strongest defensible
   accuracy claim for this emulator in one sentence. (Compare with your answer
   to the Tier-0 §0.3.4 version — it should not have changed.)

---

# Part II (S2) — REACLIB: the library and its evaluation

Files: `configs/isotopes_mesa{80,151}.yaml` → `graph/network.py` →
`fluxes/compile.py` → `fluxes/engine.py`. Oracle: `tests/test_flux_compile.py`.
Notebook: 05.

## II.1 The seven-coefficient form, derived

REACLIB stores every rate as a sum of **sets**, each set seven coefficients:

$$
\boxed{\;
N_A\langle\sigma v\rangle
= \sum_{\text{sets}} \exp\Bigl[
a_0 + \frac{a_1}{T_9} + \frac{a_2}{T_9^{1/3}} + a_3 T_9^{1/3}
+ a_4 T_9 + a_5 T_9^{5/3} + a_6 \ln T_9 \Bigr]
\;}
\tag{2.1}
$$

Every term has a physical origin. Derive them rather than memorising:

| Term | Origin |
|---|---|
| a₀ | overall normalisation: S-factor scale, statistical weights, constants |
| a₁/T₉ | **resonance**: exp(−E_r/kT), with a₁ = −11.605·E_r[MeV] (1.10). Also **detailed-balance Q**: a₁ = −11.605·Q (§III) |
| a₂/T₉^{1/3} | **the Gamow exponent** −τ from (1.7)/(1.9): a₂ = −4.2487(Z₁²Z₂²μ)^{1/3} |
| a₃T₉^{1/3}, a₄T₉, a₅T₉^{5/3} | **empirical shape terms, not a derived expansion.** They absorb the higher orders of the saddle-point approximation and the energy dependence of S(E) near E₀, and they form the odd ladder T₉^{1/3}, T₉^{3/3}, T₉^{5/3} continuing the a₂ term's T₉^{−1/3}. Do **not** claim a clean derivation here: expanding S(E) ≈ S₀ + S′E₀ + … with E₀ ∝ T^{2/3} generates T^{2/3}, T^{4/3}, which is not this ladder. The honest statement is that the basis was chosen wide enough to fit both §1.2's and §1.3's asymptotics with three free shape parameters left over (§II.7) |
| a₆ ln T₉ | the power-law prefactor: **−2/3** for non-resonant (1.8), **−3/2** for a narrow resonance (1.10), and **+3/2·ΔN** shifts for a detailed-balance reverse (§III) |

Two properties of this basis are load-bearing downstream:

1. **It is linear in the coefficients inside the exponent.** So evaluating every
   rate in a network at every state is one matrix product
   `coeffs @ Tpow` followed by `exp` and a segment-sum. That is exactly
   `engine.evaluate_lambda`, and it is why the compiled evaluator is fast.
2. **Multiplicative corrections are additive in the exponent.** Partition
   functions, screening, and the detailed-balance ratio can each be *either*
   baked into a₀/a₁/a₆ *or* added at runtime, with identical results up to
   floating-point association. This equivalence is what the 5×10⁻¹² test gate
   is measuring (§II.6) — and, less happily, it is what allowed the v-flag
   reverses to silently omit the partition-function term (§III.5).

**Sets, not one fit.** Multiple sets are summed because a real rate often has a
non-resonant component plus one or more resonances; each gets its own seven
coefficients, and (2.1) sums the exponentials. `c12(a,g)o16` carries two sets;
`si28(a,g)s32` carries one.

## II.2 Sets, chapters, labels, and the v flag

Three pieces of REACLIB metadata matter here.

**Chapter** — reactant/product counts (Tier 0 §0.5's table). Determines arity,
hence `dens_exp` and `prefactor`, and it is the index of the gh-575 bug (§III.7).

**labelprops** — a six-character field per set. Positions 0–5 hold the data
source label (`ths8r `, `nac2  `, `ks03  `, `wc12  `, `ec    `, `bet+  `), and
**position 5 carries the `v` flag** marking a set as a *pf-free inverse fit*:

```python
vflag_sets = np.array([lp[5] == "v" for lp in set_labelprops])   # compile.py:250
assert_pf_gate(vflag_sets, context=f"{network} compiled set tensor")
```

That one character is the entire discriminator for the project's blocking gate.
`ths8r ` (trailing space at position 5) is a forward; `ths8rv` is its v-flag
reverse.

**derived_from_inverse** — pynucastro's boolean surfacing of the same fact at
the Rate level, exported into the ν npz as `derived_from_inverse` and consumed
by `assert_pf_gate`.

## II.3 One rate dissected

This is the exercise to actually do. `si28(a,g)s32` and its library reverse
**[derived here]**:

```
si28(a,g)s32   chapter 4  prefactor 1.0  dens_exp 1  derived_from_inverse False
   labelprops 'ths8r '
   a = [ 47.9212,   0.0,     -59.4896,  4.47205, -4.78989,  0.5572, -0.66667]

s32(g,a)si28   chapter 2  prefactor 1.0  dens_exp 0  derived_from_inverse True
   labelprops 'ths8rv'
   a = [ 72.8130, -80.626,   -59.4896,  4.47205, -4.78989,  0.5572, +0.83333]
```

Now check every coefficient against Part I:

- **a₂ = −59.4896.** From (1.9), τ(T₉=1) = 4.2487·(14²·2²·3.5)^{1/3}
  = 4.2487·(2744)^{1/3} = 4.2487·14 = **59.482**. Agreement to 0.01%
  (the residual is the difference between integer A and true reduced mass in
  the fit). **The third REACLIB coefficient of every charged-particle forward
  is the Gamow exponent.** Verify one yourself and this stops being an
  incantation.
- **a₆ = −0.66667 = −2/3.** Exactly the non-resonant prefactor of (1.8).
- **a₁ = 0** in the forward: no resonance term needed for this channel.
- **a₃, a₄, a₅** are the saddle-point/S(E) corrections — identical in the
  forward and the reverse, because detailed balance does not touch them.

And now the reverse, which is where S3 begins:

| Coefficient | forward | v-flag reverse | difference |
|---|---|---|---|
| a₀ | 47.9212 | 72.8130 | **+24.8918** |
| a₁ | 0.0 | −80.626 | **−80.626** |
| a₆ | −0.66667 | +0.83333 | **+1.5 exactly** |
| a₂,a₃,a₄,a₅ | — | — | **identical** |

Three numbers changed. Compute what they should be:

- **−80.626** = −Q/(k·10⁹) = −6.94782 MeV / 0.0861733 MeV = **−80.626** ✓
- **+1.5** = 1.5·ΔN with ΔN = +1 (chapter 4 → chapter 2, one extra product) ✓
- **+24.8918** = ln of the temperature-independent phase-space and statistical
  ratio. pynucastro computes the same thing from first principles as
  `DerivedRate.ratio_factor` = **24.8935** — agreeing to 0.0017, the difference
  being the mass table used. ✓

**Nothing else changed. In particular, no partition-function term appears
anywhere in the v-flag reverse.** Hold that observation; §III.5 turns it into
the project's blocking gate.

## II.4 From λ to the gross flux

Equation (1.2), implemented. Two subtleties visible only in the code:

**Screening and pf enter as a post-multiplication.** `evaluate_lambda` computes
the set sum first, then multiplies by exp(corr):

```python
lam[cn.owned_cols] = np.add.reduceat(np.exp(log_sets), cn.set_starts, axis=0)
...
corr = cn.pf_matrix @ log_pf          # DerivedRate columns
corr = corr + cn.screen_map @ log_scor
lam *= np.exp(corr)
```

This is algebraically identical to adding inside each set's exponent — provided
the correction is the same for all sets of a column, which it is (both pf and
screening are properties of the *reaction*, not of the fit component). The
module docstring says exactly this, and says it is "fp-equal to ~1 ulp".

**Tabular weak rates bypass the coefficient tensor entirely** — they are
interpolated, then written into the same `lam` array (§V.5). One array, two
completely different evaluation mechanisms, unified by column index. That
unification is the design decision that makes everything downstream
(`stoich.nu @ R`, the pair map, κ) indifferent to rate provenance.

**Column identity is the invariant that makes it safe.** `compile_network`
asserts the compiled column order equals `stoich.rate_fnames`, i.e. the ν export
order (`compile.py:173–183`). If that ever drifts, every flux is silently
attributed to the wrong reaction — a failure mode with no numerical signature.
Hence the assertion rather than a comment.

## II.5 Code: the coefficient tensor

The compile step's job is to turn a ragged object graph (rates, each with a list
of sets, each with seven coefficients) into flat arrays:

| Field | Meaning |
|---|---|
| `coeffs` (n_sets, 7) | every set of every rate, stacked |
| `set_owner` (n_sets,) | which reaction column owns each set |
| `set_starts`, `owned_cols` | `reduceat` boundaries for the segment sum |
| `pf_splines`, `pf_matrix` | per-nucleus log-pf splines + the ±1 incidence matrix |
| `tab_*` | per-tabular-rate grids and 2-D log-rate arrays |
| `screen_pairs`, `screen_map` | deduplicated (Z,A) pairs + per-reaction multiplicity |

Two design points worth internalising, because they recur:

1. **Deduplicate over pairs, not reactions.** Many reactions share the same
   screening pair (everything capturing an α on a Z = 14 nucleus). `screen_pairs`
   holds unique pairs; `screen_map` is a sparse (n_rxn × n_pairs) multiplicity
   matrix. Screening is then one evaluation per unique pair per state, plus a
   sparse matmul. Same idea for `pf_splines`/`pf_matrix` over nuclei.
2. **The pf incidence matrix carries signs, and the signs are of the *source*
   rate.** In `compile.py:232–239`, source-rate *reactants* get +1 and
   *products* −1 — because the correction being applied is the ratio
   ∏G_reactants/∏G_products of the **forward** rate, applied to the derived
   reverse (§III.3). Getting that sign backwards would invert every
   partition-function correction while leaving all shapes and magnitudes
   plausible. This is the kind of bug the κ-at-NSE test (§III.9) exists to catch.

## II.6 Oracle: `tests/test_flux_compile.py` and the 5×10⁻¹² gate

The test asserts the compiled path matches `rate.eval` per rate per state to
|rel| ≤ 5×10⁻¹². **Why not 10⁻¹⁵?** The docstring answers it, and the answer is
pure Part-I physics:

> the compiled path bakes the DB correction into the set coefficients
> (pynucastro's own `derived_sets` construction) while `rate.eval` adds the
> identical terms at runtime — with |Q/kT| ~ O(500) in the exponent,
> association differences reach ~10⁻¹² rel.

Check the magnitude yourself: at T₉ = 1.6, Q/kT for a 7 MeV channel is
80.6/1.6 ≈ 50; for the largest Q-values in the network it reaches several
hundred. Adding two numbers of order 500 and exponentiating amplifies a
1-ulp (≈10⁻¹⁶) association difference to 500×10⁻¹⁶ = 5×10⁻¹⁴ relative — and
summing several sets, plus the pf and screening terms, gets you to the measured
1.3×10⁻¹² floor [RESULTS 2026-07-10]. **The gate is set just above a measured
floor, not at an arbitrary round number.** That is the pattern to look for in
every gate in this repo.

The same file also pins the compile-time pf gate (`test_no_vflag_sets_survive`,
`test_replacement_covered_every_vflag_column`) and column identity
(`test_column_identity_preserved`) — S3's business, tested here because compile
is where it is enforced.

## II.6b The numerical range of λ, and why nothing overflows

A deep-dive worth doing once, because it explains several design choices at
once. Measured on mesa_80, screening off, ρ = 10⁸ **[derived here]**:

| T₉ | λ range (log₁₀) | span | λ = 0 | λ non-finite |
|---|---|---|---|---|
| 1.6 | −63.83 … +11.61 | **75 decades** | 0 | 0 |
| 3.3 | −30.61 … +12.93 | 44 decades | 0 | 0 |
| 5.0 | −24.59 … +14.01 | 39 decades | 0 | 0 |
| 7.9 | −20.37 … +16.62 | 37 decades | 0 | 0 |

And at the level of individual sets, the exponent a·basis ranges from
**−4.4×10⁶ to +38** across the box edges.

Three readings:

1. **Nothing ever overflows.** The maximum exponent (+38) is nowhere near
   ln(DBL_MAX) = 709.78. The evaluator can compute `exp` unguarded.
2. **43 of 1834 sets underflow to exactly 0** at T₉ = 1.6. This is *correct* —
   those are rates whose true value is e^{−4×10⁶}, i.e. zero to any meaning of
   the word. The compiled path relies on IEEE graceful underflow rather than
   masking, which is the right call: a masked branch would cost a comparison on
   every set at every state to reproduce the answer the hardware already gives.
3. **The 75-decade span at T₉ = 1.6 is the reason everything downstream is
   log-space or ratio-based.** It is also the reason the conservation gate is
   phrased relative to *gross* flux rather than absolutely (Tier 0's
   max(1e-12·s, 1e-13·G) form): an absolute tolerance is meaningless against a
   quantity spanning 75 decades. The dynamic range narrows as T rises — the
   Gamow exponent τ ∝ T^{−1/3} compresses everything — which is why the box's
   cold corner is the numerically hardest, not the hot one.

## II.6c What multiple sets mean, and fit validity

`c12(a,g)o16` carries two sets:

```
'nac2  '  a = [254.634, -1.84097, 103.411, -420.567, 64.0874, -12.4624, 137.303]
'nac2  '  a = [ 69.6526, -1.39254, 58.9128, -148.273,  9.08324, -0.54104, 70.3554]
```

Neither set has a₂ resembling a Gamow exponent (τ(T₉=1) = 32.12 for C+α), and
a₆ is +137 and +70. **These are not physically-interpretable components; they
are two terms of a numerical fit to a rate with strong resonance structure.**
The lesson generalises: a₂ = −τ is a reliable reading only for the smooth
non-resonant channels — exactly the α-ladder captures that dominate here.

Which raises the question the form invites: **what happens outside the fitted
range?** With a₆ = +137, extrapolating below the fit's lower T bound produces
nonsense fast. REACLIB fits are typically valid over T₉ ∈ [0.01, 10]; the box
(1.6–7.9) sits comfortably inside, so this project never tests it. Worth knowing
as a boundary of the tooling rather than of the physics — and worth contrasting
with the weak tables (§V.5), where the out-of-range behaviour *is* specified and
the two codes disagree about it.

## II.7 A fit library, not a theory

Two things REACLIB is *not*:

- **Not a physics model.** (2.1) is a fitting basis chosen so that its
  asymptotics match the physics of §1.2–1.3. Coefficients outside the fitted
  temperature range can extrapolate to nonsense; pynucastro and MESA both use
  it in-range here.
- **Not versionless.** REACLIB is a *snapshot*. MESA r23.05.1 ships
  `jina 20171020`; pynucastro 2.12.0 ships a later one. Those two disagree on
  25 forward channels beyond the 0.004 dex band, worst ¹³N(p,γ)¹⁴O at −3.7 dex
  [RESULTS 2026-07-10] — and, more subtly, they disagree on *which direction of
  a pair is the fitted one* on 14/16 pairs (mesa_80). §VI is the node that
  measured all of this.

## II.8 Self-check for S2

1. From (1.9), predict a₂ for ³²S(α,γ)³⁶Ar and ⁴⁰Ca(α,γ)⁴⁴Ti. Look them up in
   pynucastro and check.
2. `fe54(n,g)fe55` has a₂ = −8.6662. Why is this *not* a Gamow exponent, and
   what is it doing in the fit?
3. A rate has a₆ = −1.5 and a₁ = −23.2. What kind of term is it, and what is
   the resonance energy in MeV?
4. Write out `lam` for a chapter-8 rate (3 reactants → 1 product) with two sets,
   symbolically, all the way to R_j including prefactor and ρ powers.
5. Why does `set_starts` exist rather than a loop over columns? Estimate the
   speedup for mesa_151 (1518 columns, ~2000 sets, 4096 states).
6. `compile_network` raises if `set_owner` is not sorted. What downstream
   computation would silently produce wrong answers if it were not?

---

# Part III (S3) — Detailed balance ⚠ the load-bearing node

Files: `fluxes/db_reverses.py`, `fluxes/guards.py`, `crosscheck/kappa.py`.
Oracles: `tests/test_flux_compile.py` (pf gate), `tests/test_flux_engine.py`
(κ at NSE), `tests/test_flux_guards.py` (the gate as policy). Notebook: 04.

This is the node where a *textbook identity* and a *code defect* have the same
algebra, and where the project's only blocking construction gate lives. Tier 0
said "S3 is the load-bearing one". Here is why: **every equilibrium statement in
this project — QSE clusters, the Guidry mask, the active set, the kill-test
verdict — is a statement about the ratio of a forward rate to its reverse.** If
that ratio is constructed wrongly, all of them are wrong in a way that looks
like physics.

## III.1 The reverse/forward ratio, derived in full

Start from chemical equilibrium (Tier 0, eq. 0.1): Σᵢ νᵢμᵢ = 0. For nuclei in
a non-degenerate, non-relativistic gas the number density at chemical potential
μᵢ is

$$
n_i = g_i\,G_i(T)\left(\frac{m_i kT}{2\pi\hbar^2}\right)^{3/2}
      \exp\!\left(\frac{\mu_i - m_i c^2}{kT}\right)
\tag{3.1}
$$

with g_i = 2Jᵢ+1 the ground-state degeneracy and G_i(T) the internal partition
function of (0.4). (Ions are non-degenerate everywhere in the box — §0.1.3.
This is the step that would fail for the *electrons*, and it is why the weak
sector cannot be treated this way at all; see §V.4.)

Take a reaction with reactant multiset ℛ and product multiset 𝒫. **Detailed**
balance means the forward and reverse rates per unit volume are equal
*pairwise*, so

$$
\frac{1}{\prod_{\mathcal R} c!}\,\Bigl(\prod_{\mathcal R} n_i\Bigr)\,
\tilde\lambda_{\rm fwd}
=
\frac{1}{\prod_{\mathcal P} c!}\,\Bigl(\prod_{\mathcal P} n_k\Bigr)\,
\tilde\lambda_{\rm rev}
\tag{3.2}
$$

Substituting (3.1) and using Σ_ℛ μ = Σ_𝒫 μ (the equilibrium condition, which
kills every chemical potential), the μ's cancel and the rest-mass exponentials
combine into the Q-value:

$$
\frac{\prod_{\mathcal R} n_i}{\prod_{\mathcal P} n_k}
=
\frac{\prod_{\mathcal R} g_i G_i}{\prod_{\mathcal P} g_k G_k}
\cdot
\left(\frac{\prod_{\mathcal R} m_i}{\prod_{\mathcal P} m_k}\right)^{3/2}
\cdot
\left(\frac{kT}{2\pi\hbar^2}\right)^{\tfrac{3}{2}\Delta N_s}
\cdot e^{-Q/kT}
\tag{3.3}
$$

where

$$
\Delta N_s \equiv |\mathcal R| - |\mathcal P|,
\qquad
Q = \sum_{\mathcal R} m c^2 - \sum_{\mathcal P} m c^2
$$

Now convert to the molar convention of §1.1.3 (nᵢ = ρN_A Yᵢ, λ = N_A^{n−1}⟨σv⟩;
each side of (3.2) carries ρ^{|ℛ|} and ρ^{|𝒫|} respectively). Writing masses as
mᵢ = A_iᵐᵃˢˢ m_u, everything collects into

$$
\boxed{\;
\frac{\lambda_{\rm rev}}{\lambda_{\rm fwd}}
=
\underbrace{\frac{\prod_{\mathcal P} c!}{\prod_{\mathcal R} c!}}_{\text{multiplicity}}
\cdot
\underbrace{\frac{\prod_{\mathcal R} g_i}{\prod_{\mathcal P} g_k}}_{\text{spins}}
\cdot
\underbrace{\frac{\prod_{\mathcal R} G_i(T)}{\prod_{\mathcal P} G_k(T)}}_{\text{partition functions}}
\cdot
\underbrace{\left(\frac{\prod_{\mathcal R} A_i}{\prod_{\mathcal P} A_k}\right)^{3/2}}_{\text{mass phase space}}
\cdot
\underbrace{\bigl(\mathrm{fac}\cdot T_9^{3/2}\bigr)^{\Delta N_s}}_{\text{thermal phase space}}
\cdot
\underbrace{e^{-Q/kT}}_{\text{energetics}}
\;}
\tag{3.4}
$$

with the **molar phase-space constant**

$$
\mathrm{fac} \equiv \frac{1}{N_A}\left(\frac{m_u\,k\cdot 10^9\,\mathrm{K}}{2\pi\hbar^2}\right)^{3/2}
= 9.8685\times10^{9},
\qquad \log_{10}\mathrm{fac} = 9.9942
\tag{3.5}
$$

**[derived here]** — and this is precisely the constant MESA computes in
`rates/private/reaclib_support.f90` as

$$
\mathrm{fac} = \frac{1}{N_A}\left(\frac{10^9\,\mathrm{K}\cdot k}{2\pi\hbar^2 N_A}\right)^{3/2}
$$

[RESULTS 2026-07-09], the two forms being identical because
$1/N_A = m_u$ to ten digits.

Six factors. **Miss any one of them and the reverse rate is wrong by a
multiplicative constant that looks completely plausible.** The rest of Part III
is a tour of which implementations miss which.

> **Sanity check to do once, by hand.** Verify (3.4) against pynucastro for
> ²⁸Si(α,γ)³²S: reproduce `rev.eval(T)` from `fwd.eval(T)` and the six factors.
> I get agreement to 6×10⁻⁴ relative at T₉ = 3, the residual being pynucastro
> using its own recomputed Q rather than the library's (a ΔQ ≈ 1.6×10⁻⁴ MeV
> rounding). **[derived here]**

## III.2 The thermal phase-space factor and why |ΔN| is the index

Read the factor (fac·T₉^{3/2})^{ΔN_s} dimensionally. (m kT/2πℏ²)^{3/2} is a
**number density** — the quantum concentration, the density at which the
thermal de Broglie volume holds one particle. Each *net* particle destroyed in
the forward direction has to be re-created from the thermal bath in the
reverse, and the price of doing so is one quantum concentration.

Hence:

| Forward chapter | ℛ → 𝒫 | ΔN_s | powers of fac·T₉^{3/2} in the reverse ratio |
|---|---|---|---|
| 4 | 2 → 1 | +1 | 1 |
| 5 | 2 → 2 | 0 | **none** |
| 2 | 1 → 2 | −1 | 1 (inverted) |
| 3 | 1 → 3 | −2 | 2 |
| 8 | 3 → 1 | +2 | 2 |
| 6 | 2 → 3 | −1 | 1 |
| 7 | 2 → 4 | −2 | 2 |
| 9 | 3 → 2 | +1 | 1 |

Magnitudes **[derived here]**: log₁₀(fac·T₉^{3/2}) = 10.30 / 10.90 / 11.34 at
T₉ = 1.6 / 4.0 / 7.9. So *one missing power is ten to eleven orders of
magnitude*, and two is twenty-one to twenty-three. Hold those numbers — §III.7
matches them against a measurement to three significant figures.

**Chapter 5 is the special case worth naming:** 2 → 2 rearrangements
((p,α), (n,α), (n,p)) have ΔN_s = 0 and need no phase-space factor at all.
Tier 0 §0.5 flagged those as the *bridge* reactions between QSE groups. They are
therefore the reactions most immune to this entire class of error — a small
mercy, since they are the ones the group/bridge analysis depends on.

## III.3 Partition functions in the ratio

The G-ratio in (3.4) is the *only* temperature-dependent factor besides
T₉^{3/2} and e^{−Q/kT}, and it is the one most easily dropped, because at low
temperature it is 1.

Measured pf values exp(log_pf) from the Rauscher tables pynucastro ships
**[derived here]**:

| Nucleus | T₉=3 | 4 | 5 | 6.3 | 7.9 |
|---|---|---|---|---|---|
| ²⁸Si | 1.005 | 1.029 | 1.081 | 1.191 | 1.379 |
| ³²S | 1.001 | 1.008 | 1.029 | 1.090 | 1.233 |
| ⁵⁶Ni | 1.000 | 1.002 | 1.011 | 1.046 | 1.168 |
| ⁵⁵Co | 1.000 | 1.003 | 1.014 | 1.063 | 1.245 |
| ⁵⁶Fe | 1.192 | 1.459 | 1.829 | 2.536 | **4.045** |
| ⁴⁵Sc | 1.803 | 2.133 | 2.556 | 3.240 | **4.344** |
| ⁴⁴Ti | 1.078 | 1.234 | 1.486 | 1.982 | 2.931 |

Exactly the structure §0.2.2 predicted: **doubly-magic and near-magic species
stay near 1; odd-A and mid-shell species reach 2–4.** The ratio in (3.4)
therefore does *not* cancel — it is a ratio of dissimilar nuclei.

Net pf corrections on complete channels **[derived here]**:

| Channel | pf factor at T₉=3 | 5 | 7.9 |
|---|---|---|---|
| ²⁸Si(α,γ)³²S | 1.004 | 1.050 | 1.119 |
| ⁴⁰Ca(α,γ)⁴⁴Ti | 0.928 | 0.675 | **0.371** |
| ⁵⁴Fe(n,γ)⁵⁵Fe | 0.877 | 0.774 | 0.830 |

So the correction ranges over roughly 0.37× to 1.12× on these three alone, and
the project measured **0.22×–4.5× across the network at NSE temperatures**
[RESULTS 2026-07-10]. A factor of 4.5 in a reverse rate is not a refinement.

### ⚠ The normalisation trap: G versus (2J+1)G

(3.4) contains **two separate statistical factors** — ∏g/∏g with g = 2J₀+1, and
∏G/∏G. If G were defined as the *unnormalised* sum Σ(2J_s+1)e^{−E_s/kT}, these
would double-count the ground state.

The tables are normalised, i.e. (0.4)'s form G = Σ(2J_s+1)e^{−E_s/kT}/(2J₀+1),
so G → 1 as T → 0. **Check it in the §III.3 table:** every entry at T₉ = 3 is
≥ 1.000 and the near-magic ones are 1.000–1.005. If the tables were
unnormalised, ⁵⁶Ni (J₀ = 0, g = 1) would still read ≈1 but ⁴⁵Sc (J₀ = 7/2,
g = 8) would read ≈8, not 1.803. **[derived here]**

So the code is right to carry both factors separately:

```python
F *= math.prod(nucr.spin_states for nucr in ...)   # g = 2J₀+1     (DerivedRate)
...
net_log_pf += nucr.partition_function.eval(T)      # ln G, normalised
```

This is worth internalising because the failure mode is silent and
species-selective: double-counting would multiply reverse rates by g-ratios of
order 1–10, look like a "pf problem", and be indistinguishable from the v-flag
defect without checking the low-T limit. **The T → 1 limit of a partition
function is a free diagnostic; use it.**

### The pf spline and what happens past the table

Both `fluxes/compile.py` and `qse/coeffs.py` rebuild the same object:

```python
InterpolatedUnivariateSpline(pf.T9_points, pf.log_pf_data,
                             k=pf.interpolant_order, ext="const")
```

`ext="const"` means **constant extrapolation** — past the last tabulated T₉ the
spline holds its final value rather than continuing the (steeply rising) trend.
Three notes:

1. Constant extrapolation of log G is conservative: it *under*-estimates G at
   high T rather than diverging. The alternative (`ext=0`, spline extrapolation)
   with a cubic would run away.
2. The Rauscher tables extend well past T₉ = 7.9, so the box never triggers it.
   Like the `smooth_clip` in the screening module (§IV.5), it is a guard that
   should never fire, present so that out-of-box calls degrade rather than
   explode.
3. **The two rebuilds must agree.** Rate-side pf (§III.3) and Saha-side pf
   (`qse/coeffs.py`) are constructed from the same fields with the same spline
   order and the same `ext` — deliberately, because κ-at-NSE compares a rate
   ratio against a composition computed from the equilibrium side. A mismatch
   there would produce a nonzero κ floor with no defect in either component.
   The `qse/coeffs.py` docstring makes the point explicitly: using the same
   inputs is what makes the solver cross-check "a genuine independence test of
   the SOLVER, not the data".

**In the code**, the correction is applied as a sparse incidence matmul:

```python
for nuc in rate.source_rate.reactants:   pf_entries[(j, m)] += 1.0
for nuc in rate.source_rate.products:    pf_entries[(j, m)] -= 1.0   # compile.py:232–239
...
corr = cn.pf_matrix @ log_pf ;  lam *= np.exp(corr)                   # engine.py:133,148
```

Note again (§II.5) that the signs are keyed to the **source (forward) rate's**
reactants and products, matching ∏G_ℛ/∏G_𝒫 in (3.4). The same splines, from
the same Rauscher tables, are rebuilt independently in `qse/coeffs.py` for the
Saha side — and the two are cross-checked, because a pf mismatch between the
rate side and the equilibrium side would make κ-at-NSE nonzero for reasons that
have nothing to do with the rates.

## III.4 Three ways to build a reverse, and what each omits

| Construction | spins | masses | fac^ΔN | Q | **partition functions** |
|---|---|---|---|---|---|
| **(a)** Independent REACLIB fit of the reverse | implicit | implicit | implicit | implicit | implicit in the fit — but *only at the temperatures fitted* |
| **(b)** REACLIB **v-flag** inverse fit | ✓ | ✓ | ✓ | ✓ | ✗ **omitted** |
| **(c)** `DerivedRate(source_rate=fwd, use_pf=True)` | ✓ | ✓ | ✓ | ✓ | ✓ evaluated at runtime |
| **(d)** MESA `compute_rev_ratio` | ✓ | ✓ | **exactly one power, and only when the tabulated direction has one product** — so zero powers where one or two are needed, and one where two are needed (chapter 8) | ✓ | ✓ (winvn pf ratios) |

- **(a)** exists and causes a subtler problem: when MESA's REACLIB snapshot and
  pynucastro's disagree about *which direction was fitted*, the two codes have
  independently-fitted pair members that need not satisfy detailed balance
  exactly. That is the 14/16 "construction swap" class in §VI, and it is why
  MESA 24.08.1 shows a subset of (n,α)/(p,α) pairs sitting at κ ≈ 0.75 while
  stock is clean [RESULTS 2026-07-10] — a *newer snapshot* traded DB-linkage for
  fit quality.
- **(b)** is the project's blocking problem. Next section.
- **(c)** is the mandated construction.
- **(d)** is the gh-575 bug. §III.7.

## III.5 The v-flag dissected — and why it is fatal above T₉ ≈ 3

Return to the §II.3 table. The v-flag reverse of ²⁸Si(α,γ)³²S is the forward's
seven coefficients with exactly three changed:

$$
a_0 \mathrel{+}= \ln F, \qquad
a_1 \mathrel{+}= -\frac{Q}{k\cdot10^9}, \qquad
a_6 \mathrel{+}= \tfrac{3}{2}\,\Delta N_s
$$

Compare with (3.4). The a₁ shift is e^{−Q/kT}. The a₆ shift is T₉^{(3/2)ΔN_s}.
The a₀ shift is fac^{ΔN_s} together with the spin, mass and multiplicity
factors — all temperature-independent, all correctly folded into a constant.

**Everything in (3.4) is present except the partition-function ratio — because
the partition-function ratio is the one factor that is temperature-dependent
and cannot be absorbed into a constant.** The v-flag construction is not sloppy;
it is *structurally incapable* of carrying pf within a seven-coefficient fit
whose basis functions are fixed.

The consequence is bounded and predictable: the v-flag reverse is wrong by
exactly ∏G_ℛ/∏G_𝒫, which is ≈1 below T₉ ≈ 2 and reaches 0.22×–4.5× at NSE
temperatures. Now recall §1.4.2: **near equilibrium f⁺ ≈ f⁻, so a systematic
multiplicative error in f⁻ appears at full strength in κ.** From
f⁻ = f⁻_true·(1+ε):

$$
\kappa = \frac{|f^+-f^-|}{f^++f^-} = \frac{|\varepsilon|}{2+\varepsilon}
\;\approx\; \frac{|\varepsilon|}{2}\ \ (|\varepsilon|\ll1)
\qquad\text{at true equilibrium}
$$

Note that the pf errors in play here are **not** small, so use the exact form:
an ε of 0.5–1 (a factor 1.5–2 in pf) manufactures κ = **0.20–0.33** **at a state
where the true κ is zero**, where the linearised ε/2 would have said 0.25–0.5.
The distinction matters precisely here, because this is the number being
compared against a measured p90. That is the measurement:

| variant | median κ at NSE (mesa_80 / mesa_151) | p90 |
|---|---|---|
| pyna graphs as built (raw v-flag) | 6.6×10⁻² / 1.3×10⁻¹ | 0.39 / 0.49 |
| stock MESA r23.05.1 | 3.6×10⁻³ / 3.3×10⁻³ | 1.2×10⁻² / 7.2×10⁻³ |
| MESA 24.08.1 | 5.3×10⁻³ / 4.9×10⁻³ | 0.76 / 0.76 |
| **pf-corrected engine (screening off)** | **2.6×10⁻¹²** | **8.2×10⁻¹²** |

[RESULTS 2026-07-10]. The worst individual pairs move from κ = 0.44–0.64 to
1.7×10⁻¹²–1.3×10⁻¹¹ under (c) — **the attribution is dispositive**, not
circumstantial: the entire floor was the missing G-ratio.

**Why this would have destroyed the kill-test.** The active-set gate is
κ_r > 0.1. A spurious floor with p90 = 0.39 puts a large fraction of
*equilibrated* pairs above the threshold, so they enter the active set as if
they carried net flow. cond(S_active) would be computed on a set inflated with
noise columns, |ΔYₑ| attribution would be spread across reactions carrying
nothing, and the Target-A verdict would be a measurement of a rate-construction
artifact. Hence:

```python
class PfGateError(RuntimeError):
    """Raised when a flux/κ computation would use raw v-flag reverse rates."""
```

and compilation *refuses*, rather than warning.

## III.6 κ as the numerical test of detailed balance

Tier 0 §0.2.3 gave this its first reading; now it has teeth.

$$
\kappa_r = \frac{|f^+_r - f^-_r|}{f^+_r + f^-_r}
$$

- At **true** equilibrium, detailed balance says f⁺ = f⁻ *pairwise*, so
  κ_r → 0 to rate-evaluation precision.
- A **nonzero κ floor at NSE is therefore a self-consistency failure of the
  rate set**, measurable without any reference to the truth — you do not need to
  know the correct rate, only that forward and reverse must agree at a
  composition you can compute independently (from Saha).
- This is what makes the κ-floor screen a *clean* experiment: NSE compositions
  come from `pynucastro`'s solver, the rates come from three different sources,
  and the only thing being tested is mutual consistency.

`crosscheck/kappa.py` implements exactly that, with one trick worth noting:

> MESA-side gross fluxes reuse pynucastro's Y-product factors: within a pair
> comparison the composition factors are common, so
>
> $$
> f_{\rm MESA} = f_{\rm pyna}\cdot\frac{\lambda_{\rm MESA}}{\lambda_{\rm pyna}}
> $$
>
> with bare (unscreened, T-only) rates on both sides.

Because κ is a *ratio* within a pair, the abundance products cancel — so a
MESA-side κ can be computed from MESA/pyna rate ratios alone, without ever
evaluating a MESA composition. That is why the screen only needs the probe's
T-only `eval_rates` mode.

## III.7 gh-575, derived from the same algebra

MESA's `compute_rev_ratio` implements (3.4) — but gets the *number of powers* of
fac·T₉^{3/2} wrong. Read the source rather than paraphrasing it
(`rates/private/reaclib_support.f90:228`):

```fortran
if (No==1) then
   rates% inverse_exp(i) = 1        ! ... and multiply/divide coefficient(1) by fac
else
   rates% inverse_exp(i) = 0
end if
```

**The branch key is `No == 1` — the number of *products* of the tabulated
direction — and nothing else.** It is not "three or more participants on a
side", and it is not |ΔN| ≠ 1. The applied exponent is therefore

$$
e = \begin{cases} \pm1 & N_{\rm out}^{\rm tab} = 1\\ 0 & \text{otherwise}\end{cases}
\qquad\text{against the correct } \Delta N_s = N_{\rm in}^{\rm tab} - N_{\rm out}^{\rm tab}
$$

so the reverse is displaced by |ΔN_s − e| powers, **not |ΔN_s| powers**:

$$
\boxed{\;
|\Delta\log_{10}| = \bigl|\Delta N_s - e\bigr| \cdot \log_{10}\bigl(\mathrm{fac}\cdot T_9^{3/2}\bigr)
= \bigl|\Delta N_s - e\bigr| \times \{10.30,\ 10.90,\ 11.34\}\ \text{at } T_9 = \{1.6,\,4.0,\,7.9\}
\;}
$$

**[derived here]**. Tabulating it over the chapters that actually occur (arities
read off `probe_dump_net_mesa_{80,151}.csv`) **[derived here]**:

| Tabulated | chapter | ΔN_s | e | powers missing | measured Δlog₁₀ at T₉ = 4 |
|---|---|---|---|---|---|
| 2 → 1 | 4 | +1 | 1 | **0** | — (correct) |
| 2 → 2 | 5 | 0 | 0 | **0** | — (correct) |
| 2 → 3 | 6 | −1 | 0 | 1 | +10.1 … +10.6 ⁽*⁾ |
| 3 → 2 | 9 | +1 | 0 | 1 | −10.59 |
| **3 → 1** | **8** | **+2** | **1** | **1** | **−10.12 … −10.89** |
| 2 → 4 | 7 | −2 | 0 | 2 | +21.79 |

⁽*⁾ over the conforming chapter-6 rows. One member,
`r_h1_h1_he4_to_he3_he3`, sits at 1.79 dex instead of ~10.9 — and that is
exactly the channel §VI.6 identifies as *not* a gh-575 case (it is unchanged in
MESA 24.08.1). The predicted-vs-measured comparison is what isolates it: a row
that fails a mechanism-derived prediction is the signal that the mechanism does
not apply to it.

⚠ **Chapter 8 is the case the naive formula gets wrong, and it is the flagship
one.** It has |ΔN_s| = 2, so "|ΔN_s| powers" predicts ≈ 21.8 dex — but its
tabulated direction *does* have a single product, so MESA applies one power and
the deficit is **one** power, ≈ 10 dex. That is exactly what the screen measured
for c12 → 3α (−10.118 dex at T₉ = 4 in
`configs/appendixb_excluded_channels.yaml`). Reconstructing the affected set
from the branch condition alone reproduces the config exactly: 9 rows for
mesa_80, 11 for mesa_151 **[derived here]**.

With the corrected formula the measurement lands where it should:

> |Δlog₁₀| = 10.0–11.1 for one missing power and 20.6–22.7 for two, tracking
> |ΔN_s − e|·log₁₀(fac·T₉^{3/2}) within ≲0.35 dex [RESULTS 2026-07-09].

Three significant figures, from a one-line formula. **This is what "dispositive
attribution" means** — the notebook-04 figure plots measured vs predicted
displacement side by side precisely so the agreement is visible rather than
asserted.

⚠ **The compression trap.** Tier 0 §0.5 flagged it and it is worth repeating
because *two* natural summaries are wrong. The criterion is **not** "|ΔN| ≠ 1":
of the 20 config rows across both networks, **13 have |dN| = 1**. And the
displacement is **not** |ΔN| powers, per the chapter-8 row above. The
discriminator is the *product arity of the tabulated direction*, which is why
the config's own class field says `multi_body_inverse`. Read
`configs/appendixb_excluded_channels.yaml` with its (unstated) convention in
hand: `chapter` **and** `dN` both describe the tabulated direction, while
`mesa_handle` names the **inverse** being flagged — so `r_c12_to_he4_he4_he4`,
which is itself 1 → 3 with its own ΔN = −2, correctly carries `chapter: 8,
dN: 2`.

**A completeness caveat.** Chapters 2 (1→2), 3 (1→3), 10 (4→2) and 11 (1→4)
would fail `No == 1` in exactly the same way. They are absent from the flagged
set because they are **empty in these two networks** — the tabulated arities
present are only (2,1), (2,2), (3,1), (2,3), (2,4), (3,2) **[derived here]** —
not because the mechanism spares them. If the isotope list ever widens, the
screen must be re-run rather than assumed to still enumerate the same classes.

**Beyond the paper.** The project's own screen found a class the Grichener et
al. Appendix B does not list: the inverses of chapter-8 rates (the 1 → 3
photodisintegrations), including **c12 → 3α**, low by 9.5–11.3 dex
[RESULTS 2026-07-09]. Worth noticing
as a matter of method — the paper's list was taken as a starting hypothesis, the
*mechanism* was derived, and then the mechanism was used to search for channels
the paper missed.

**Whose problem is it?** The Zenodo labels were generated with the authors'
*locally patched* r23.05.1, so:

- the **labels are clean** on these channels,
- **our stock MESA is the outlier**,
- therefore MESA-side values on those channels must never be used as a
  reference — which is exactly `assert_appendixb_routing`.

## III.8 Code: `db_reverses.py` and the gate

```python
def replace_vflag_reverses(rc, table, info=None) -> tuple[list, ReplaceReport]
```

Positional replacement — the returned list preserves collection order, so ν is
untouched. Three details that are each a lesson:

1. **Forward lookup is two-tier.** Canonical directed key within the collection
   first, then a lazily-built `ReacLibLibrary().linking_nuclei(...)` fallback —
   because a v-flag reverse can be in the reconciled set while its forward is
   not. Measured outcome: **all** forward partners were found in-collection
   (280/280 mesa_80, 672/672 mesa_151) [RESULTS 2026-07-10], so the fallback
   never fired. It exists because the failure would otherwise be silent.
2. **Multiset identity is asserted, not assumed.**
   ```python
   if Counter(map(str, derived.reactants)) != Counter(map(str, rate.reactants)) or ...:
       raise ValueError("... changed the reactant/product multisets — ν column identity broken")
   ```
   The replacement is the one operation in the pipeline that swaps a live object
   in a column; the assertion pins the only thing that must not change.
3. **Failures are reported, not swallowed.** `ReplaceReport.failed` must be
   empty for the pf gate to pass. A channel whose spin states are missing cannot
   get a `DerivedRate`, and the design decision is to *stop* and force an
   explicit routing decision (mesa_probe24 values, or exclude-with-footnote)
   rather than fall back to the v-flag.

The `missing_pf_nuclei` field records nuclei with no Rauscher table, where
pynucastro defaults log_pf = 0. Measured: light sector only (d, ³He, ⁴He, ⁷Li,
⁷⁹Be, ⁸B, ¹²⁻¹³C, ¹³⁻¹⁵N) [RESULTS 2026-07-10] — harmless, since G ≈ 1 there for
exactly the §0.2.2 reason (few low-lying levels in light nuclei).

## III.9 Oracles

| Test | What it pins |
|---|---|
| `test_no_vflag_sets_survive` | zero `labelprops[5] == 'v'` in the compiled tensor |
| `test_replacement_covered_every_vflag_column` | `n_replaced == derived_from_inverse.sum()`, `failed == ()` |
| `test_column_identity_preserved` | replaced columns are `DerivedRate` with the same fname stem |
| `test_exported_npz_trips_the_gate` | the *raw* ν export still trips `PfGateError` — a deliberate negative control |
| `test_kappa_vanishes_at_nse_unscreened` | median κ < 1e-9, max < 1e-6 on flux-carrying strong pairs at T₉ ≥ 5 |

That fourth one deserves attention: it asserts that the as-exported npz **fails**
the gate, with a comment saying "if the builder now derives pf-corrected
reverses, retire this test deliberately". It is a test that the safety net is
still load-bearing — the sort of test that stops a gate from quietly becoming a
no-op.

And the fifth is the physics oracle proper. It recompiles with
`screening=None`, evaluates at NSE, and requires κ to collapse. Note the
restriction to *flux-carrying* pairs (`f > median(f[f>0])`): κ on a pair
carrying no flux is a ratio of two denormal numbers and means nothing.

## III.10 The two κ conventions ⚠

There is a second, entirely real reason κ ≠ 0 at NSE, and it is not a bug:
**screening**. Deriving it is §IV.7, but the rule belongs here, next to the
gate:

> **Equilibrium detection uses UNSCREENED κ. Screened κ is for
> screening-offset diagnostics only. Never mix them in one analysis.**

With `chugunov_2007` on — the label configuration — the measured median κ at
NSE is **7.4×10⁻²** [RESULTS 2026-07-10], within a factor of a few of the
spurious v-flag floor it replaced. Two effects of similar size and completely
different natures; conflating them is exactly the failure the convention
prevents. Every κ threshold in the project (the 0.1 active-set gate above all)
is evaluated on unscreened runs.

## III.11 The other equilibrium correction: Coulomb terms in NSE

There is a second place plasma physics enters the equilibrium side, and the κ
screen turns it **off**. Worth understanding, because "off" is a deliberate
choice with a stated reason.

The Saha relation (3.1) assumed an ideal gas of nuclei. In a strongly-coupled
plasma each nucleus also carries a **Coulomb free energy** — the interaction
energy with its screening cloud — which shifts its chemical potential by

$$
\mu_i \to \mu_i + \mu^c_i(Z_i, \Gamma_e)
$$

pynucastro implements the Chabrier & Potekhin (1998) fit:

$$
\frac{\mu^c}{kT} =
A_1\Bigl[\sqrt{\Gamma(A_2+\Gamma)} - A_2\ln\bigl(\sqrt{\Gamma/A_2}+\sqrt{1+\Gamma/A_2}\bigr)\Bigr]
+ 2A_3\bigl[\sqrt\Gamma - \arctan\sqrt\Gamma\,\bigr]
$$

with A₁ = −0.9052, A₂ = 0.6322, **A₃ = −√3/2 − A₁/√A₂**, and Γ = Γ_e Z^{5/3}.

> **Notice the structure.** That A₃ definition is the *same kind of object* as
> `chugunov_2007`'s A₃ = √3 − A₁/√A₂ (§IV.5): a coefficient defined so the fit
> reproduces the Debye–Hückel √Γ³ limit at weak coupling. Two different fits,
> two different sign conventions, one shared boundary condition. Once you have
> seen it in one, you can read it in the other — and you know immediately that
> "clean up A₃ to a literal" is a bug in both.

**The Z^{5/3} scaling is the important physics.** μ^c grows much faster than
linearly with charge, so the correction *differentially* favours heavy nuclei in
NSE — it shifts the NSE composition toward the Fe peak at fixed T, ρ, Yₑ. At the
box's cold, dense corner (Γ_e large) this is not a small effect.

**Why the κ screen sets `use_coulomb_corr=False`.** The screen compares *bare*
(unscreened) rates on both sides (§III.6). Detailed balance for bare rates
balances at the *ideal-gas* NSE composition; balancing them at a
Coulomb-corrected composition would introduce a mismatch that looks exactly like
a κ floor. The choice is not "Coulomb corrections are negligible" — it is
**"the equilibrium condition must be the one the rates actually satisfy."**
Screening on the rate side and Coulomb corrections on the equilibrium side are
the same physics entering two ways, and they must be switched on and off
together.

That is the same principle as the two-κ conventions rule (§III.10), stated for
the equilibrium side instead of the rate side. It is worth extracting as a
general rule, because it will recur in S9:

> **Rate-side and equilibrium-side plasma corrections are a matched pair.
> Any consistency test must use both or neither.**

## III.12 Q(T): the thermal Q-value, derived and measured

The architecture spec calls for the energy head to use **Qⱼ(T)** — "tabulated
from the same temperature-dependent partition functions the backbone sees (not
T-independent values)" — while `docs/phase0-killtest-verdict.md` records that
"Qⱼ(T) corrections are not modeled", and pynucastro's `Rate.Q` is a scalar
float. So there is a specified quantity that nothing computes and nothing in the
study plan defines. Here it is.

**Derivation.** The mass-excess Q of (0.7) is the *ground-state to ground-state*
energy release. In a thermal ensemble each nucleus carries a mean excitation
energy, which follows from the partition function by the standard
statistical-mechanics identity

$$
\langle E^*\rangle_i = kT^2\,\frac{d\ln G_i}{dT}
= kT\cdot T_9\frac{d\ln G_i}{dT_9}
\tag{3.6}
$$

and the effective energy released when thermally-populated reactants become
thermally-populated products is

$$
\boxed{\;
Q_j(T) = Q_j^{\rm gs}
+ \sum_{i\in\mathcal R_j}\langle E^*\rangle_i
- \sum_{k\in\mathcal P_j}\langle E^*\rangle_k
\;}
\tag{3.7}
$$

**The pleasing part:** the bracket in (3.7) is the *derivative* of exactly the
same pf combination ln∏G_ℛ − ln∏G_𝒫 that appears in the detailed-balance ratio
(3.4). The engine already builds splines of ln G per nucleus and the ± incidence
matrix `pf_matrix`. **Q(T) needs no new data — only `spline.derivative()` and the
matrix that already exists.** That is a three-line change, which makes the fact
that it is unimplemented a genuine oversight rather than a deferred cost.

**Measured magnitudes** **[derived here]**. Mean excitation energies ⟨E*⟩ [MeV]:

| Nucleus | T₉=3 | 5 | 7.9 |
|---|---|---|---|
| ²⁸Si | 0.009 | 0.133 | 0.520 |
| ³²S | 0.002 | 0.065 | 0.516 |
| ⁴⁰Ca | 0.000 | 0.010 | 0.358 |
| ⁵⁶Ni | 0.000 | 0.031 | 0.553 |
| ⁴⁴Ti | 0.080 | 0.440 | 1.340 |
| ⁴⁵Sc | 0.121 | 0.393 | 1.004 |
| ⁵⁶Fe | 0.140 | 0.509 | **1.698** |

⁵⁶Fe holds **1.7 MeV of thermal excitation** at the top of the box — the same
species-selectivity as §III.3, for the same reason.

And the channel-level correction Q(T) − Q^gs:

| Channel | Q^gs | T₉=3 | T₉=5 | T₉=7.9 |
|---|---|---|---|---|
| ²⁸Si(α,γ)³²S | 6.948 | +0.1% | +1.0% | +0.1% |
| ³²S(α,γ)³⁶Ar | 6.641 | −0.0% | −0.6% | −2.3% |
| ⁴⁴Ti(α,γ)⁴⁸Cr | 7.696 | −1.2% | −0.3% | +3.8% |
| **⁴⁰Ca(α,γ)⁴⁴Ti** | 5.127 | −1.6% | **−8.4%** | **−19.2%** |

**Against invariant #5's ≤1% gate on e_nuc.** ⁴⁰Ca(α,γ)⁴⁴Ti — a core α-ladder
step, not an exotic channel — carries a 19% Q correction at the box top and 8%
in the QSE window. Note also the *non-monotonicity* and *sign changes*: this is
not a smooth offset that could be absorbed into a calibration.

⚠ **But be careful about what this does and does not show.** Three honest
qualifications:

1. **The aggregate is a flux-weighted sum, and the terms partially cancel.**
   The α ladder shares nuclei between consecutive steps, so ⟨E*⟩ of ⁴⁴Ti enters
   ⁴⁰Ca(α,γ)⁴⁴Ti with one sign and ⁴⁴Ti(α,γ)⁴⁸Cr with the other. The
   per-channel 19% is an upper bound on a single term, not a measured e_nuc
   error.
2. **It is a bookkeeping-convention question, not obviously an error.** Nuclear
   excitation energy is *real* internal energy of the matter. Whether it belongs
   in e_nuc (the nuclear source term) or in the EOS internal energy depends on
   whether the EOS accounts for nuclear excitation — and most stellar EOSs do
   not. The requirement is **consistency between the two**, not that either
   convention is right. Using Q^gs while the EOS ignores excitation may well be
   the self-consistent pair.
3. **Invariant #5's current PASS is near-algebraic.** The verdict doc says so
   explicitly: with constant mass-derived Q, flux-route vs mass-excess
   bookkeeping "bounds Q-table rounding, not route physics". The 1.000 pass
   fraction is not evidence that Q(T) does not matter — it is a measurement that
   cannot see Q(T) at all. This is the §VIII.D common-mode blindness in its
   purest form: identical Q on both sides of a comparison.

So the finding is not "e_nuc is 19% wrong". It is: **the project has a specified
quantity it does not compute, a gate that structurally cannot detect its
absence, and a per-channel magnitude nineteen times the gate.** Resolving it
needs one decision (which convention MESA/bbq uses) and one three-line
implementation. Recorded in §VIII.E.2.

## III.13 Self-check for S3

1. Derive (3.4) from (3.1)–(3.3) yourself, keeping the molar conversion
   explicit. Where exactly does 1/N_A^{ΔN_s} enter?
2. Verify (3.5) numerically. Then confirm that MESA's stated form
   $N_A^{-1}\bigl(10^9 k/(2\pi\hbar^2 N_A)\bigr)^{3/2}$ is the same number,
   and say why.
3. For a chapter-5 rearrangement, which factors of (3.4) survive? Why is this
   class immune to gh-575?
4. Predict the pf correction on ²⁸Si(α,γ)³²S at T₉ = 7.9 from the table in
   §III.3, then check it against pynucastro. Why is it so much smaller than for
   ⁴⁰Ca(α,γ)⁴⁴Ti?
5. Given ε = 1.0 (a factor-2 error in f⁻), compute κ at true equilibrium.
   Compare with the measured p90 of the raw-v-flag variant. Are they consistent?
6. Explain, in two sentences, why the κ-floor screen needs *no* ground-truth
   rate to reach a verdict.
7. `test_exported_npz_trips_the_gate` asserts a failure. Argue for and against
   this style of test.
8. Show that the Rauscher pf tables are normalised, using only the T₉ = 3 column
   of §III.3 and the ground-state spins of ⁵⁶Ni and ⁴⁵Sc. What would the table
   look like if they were not?
9. State the reciprocity theorem (1.11) and explain why chemical equilibrium
   alone would not license using a DB reverse at κ = 0.9998.
10. `use_coulomb_corr=False` in the κ screen. Construct the spurious κ floor you
    would measure if you set it True while keeping the rates bare, and estimate
    its size at ρ = 10⁹, Z = 26.

---

# Part IV (S4) — Screening

Files: `fluxes/screening.py`, applied in `fluxes/engine.py`, pinned by
`fluxes/guards.py`. Oracle: `tests/test_flux_compile.py::TestScreeningVectorized`.
Cross-check: `crosscheck/rates_compare.py::compare_screening`.

## IV.1 Why screening exists

Everything in §1.2 assumed two *bare* nuclei approaching through vacuum. In a
plasma each nucleus carries a polarisation cloud: electrons (and, at strong
coupling, a correlated ion distribution) pile up around positive charge. A
second nucleus approaching sees a **partially neutralised** target, so the
Coulomb barrier is lower and the tunnelling probability higher.

Because the rate depends exponentially on the barrier, a *small* potential
change is a *large* rate change. Define the enhancement factor

$$
f_{\rm scr} = \frac{\langle\sigma v\rangle_{\rm plasma}}{\langle\sigma v\rangle_{\rm bare}}
= e^{h}, \qquad h \equiv \ln f_{\rm scr} \ge 0
$$

**Convention warning, stated once and enforced by the code:** pynucastro's
screening functions return **h = ln(factor)**, MESA returns the **factor**. The
cross-check module exponentiates before comparing, with a comment saying so,
and the vectorised module's docstring states it in its first Conventions bullet.
This is a genuine trap: both are dimensionless numbers near 1 for weak
screening, so a missing `exp` produces plausible-looking wrong answers.

## IV.2 Weak screening: Debye–Hückel from scratch

Linearise Poisson–Boltzmann around a test charge Z₁e. With ion densities
nᵢ ∝ exp(−Zᵢeφ/kT) ≈ nᵢ(1 − Zᵢeφ/kT),

$$
\nabla^2\phi = -4\pi\rho_{\rm ch}
= \frac{4\pi e^2}{kT}\Bigl(\sum_i n_i Z_i^2 + n_e\Bigr)\phi
\equiv \frac{\phi}{\lambda_D^2}
$$

giving the screened potential φ = (Z₁e/r)e^{−r/λ_D} with

$$
\lambda_D = \left(\frac{kT}{4\pi e^2\bigl(\sum_i n_i Z_i^2 + n_e\bigr)}\right)^{1/2}
$$

The reacting pair must approach to r ≪ λ_D, where

$$
U(r) = \frac{Z_1Z_2e^2}{r}e^{-r/\lambda_D}
\approx \frac{Z_1Z_2e^2}{r} - \frac{Z_1Z_2e^2}{\lambda_D}
$$

— the barrier is **uniformly lowered by a constant** Z₁Z₂e²/λ_D. Since the
tunnelling integral responds to the barrier and the Boltzmann factor to the
energy, the net effect is a constant multiplicative enhancement:

$$
\boxed{\;h_{\rm weak} = \frac{Z_1Z_2 e^2}{\lambda_D\,kT}\;}
\tag{4.1}
$$

Salpeter's classic result. Two things to notice, both of which matter for what
follows:

- **h depends on Z₁Z₂, not on the reaction.** Screening is a property of the
  *entering pair*, not of the exit channel. This is the seed of the §IV.7
  asymmetry.
- **h = 0 whenever either charge is zero.** Neutron-induced reactions are
  unscreened, exactly. So are photodisintegrations — a single nucleus and a
  photon have no pair to screen.

⚠ **The electron term is not innocent, and the code does not use it.** Writing
the screening sum as (Σᵢ nᵢZᵢ² + n_e) treats the electrons as a *classical*
Boltzmann gas — the same 1/kT linearisation applied to the ions. §V.4 will
establish that over most of this box the electrons are **degenerate**, and a
degenerate electron sea barely polarises: its contribution is set by dn_e/dμ_e,
not by n_e/kT, and it vanishes in the strongly degenerate limit. The correct
weak-coupling limit for the regime the code targets is therefore the **ion-only**
Debye length, i.e. a rigid neutralising electron background (the one-component
plasma).

This is not a quibble about a 7% term: it is what makes §IV.5's check work.
Dropping n_e from the sum, (4.1) collapses **exactly** onto √3·Γ₁₂^{3/2}, which
is the asymptote `chugunov_2007`'s A₃ is defined to reproduce. Keeping the
classical electron term instead gives √((Z+1)/Z)·√3 Γ^{3/2} (a 3.5% excess for
Si), and the boundary condition no longer closes. **[derived here]** So read
(4.1) as the pedagogical two-component result, and read §IV.5's √3 as the
OCP one — they are different limits, and the code implements the second.

Validity: the linearisation requires the interaction energy between neighbours
to be small compared with kT, i.e. weak coupling.

## IV.3 The coupling parameter Γ and the strong-screening limit

Define the ion-sphere radius and the **Coulomb coupling parameter**

$$
a_e = \left(\frac{3}{4\pi n_e}\right)^{1/3},
\qquad
\Gamma_{12} = \frac{Z_1Z_2e^2}{\tilde z\,a_e\,kT},
\qquad
\tilde z = \tfrac{1}{2}\bigl(Z_1^{1/3}+Z_2^{1/3}\bigr)
\tag{4.2}
$$

Γ is the ratio of typical Coulomb energy to thermal energy.

- **Γ ≪ 1**: weak coupling, Debye–Hückel (4.1) valid.
- **Γ ≫ 1**: the ion is inside a correlated ion sphere; the enhancement grows
  only **linearly**, h ∝ Γ (ion-sphere / Salpeter strong screening), rather than
  as Γ^{3/2} — what saturates is the logarithmic slope, not h itself — and the
  physics is a *free-energy difference* between the separated ions and the fused
  compound, not a potential shift.
- **Γ ~ 1**: neither asymptotic form is valid; you need a fit to Monte-Carlo
  free energies of the one-component plasma. **This is where the box lives.**

The code's Γ is exactly (4.2). Read `screening.py:47–49` and `:110`:

```python
gamma_e_fac = constants.q_e**2 / constants.k * np.cbrt(4*np.pi/3) * np.cbrt(n_e)
...
Gamma = gamma_e_fac * z1 * z2 / (ztilde * T_norm * T_p)      # T_norm*T_p == T
```

`gamma_e_fac` = e²(4πn_e/3)^{1/3}/k = e²/(a_e k), so Γ = gamma_e_fac·Z₁Z₂/(z̃T).
That is (4.2) term for term.

### The strong-screening limit, derived as a free-energy difference

Worth doing, because it is a *different kind* of argument from §IV.2 and the
difference is the whole reason a single formula has to interpolate.

At Γ ≫ 1 each ion sits in a neutralising sphere of radius a_i = (3Z_i/4πn_e)^{1/3}.
The electrostatic energy of one such ion sphere is the classic

$$
E_{\rm sphere}(Z) = -\frac{9}{10}\frac{Z^2e^2}{a_i} \;\propto\; -Z^{5/3}
$$

Screening enhancement is then the **change in Coulomb free energy on fusing**
the two reactants into the compound nucleus, since the tunnelling happens at a
separation small compared with a_i:

$$
h_{\rm strong} = \frac{E(Z_1)+E(Z_2)-E(Z_1+Z_2)}{kT}
\;\simeq\; \frac{9}{10}\,\Gamma_e\Bigl[(Z_1+Z_2)^{5/3}-Z_1^{5/3}-Z_2^{5/3}\Bigr],
\qquad \Gamma_e = \frac{e^2}{a_e kT}
$$

— note the 9/10 is the *same* 9/10 as in E_sphere; nothing else enters. Two
cross-checks, both worth doing once **[derived here]**:

- In cgs this is the classic Salpeter form,
  h = 0.205 (ρ/μ_e)^{1/3} T₆⁻¹ [(Z₁+Z₂)^{5/3} − Z₁^{5/3} − Z₂^{5/3}], since
  Γ_e = 0.2274 (ρ/μ_e)^{1/3}/T₆ and 0.9 × 0.2274 = 0.205.
- For an equal-charge pair it gives h/Γ₁₂ = 0.9(2^{5/3} − 2) = **1.057**,
  against `chugunov_2007`'s own γ̃ → ∞ asymptote A₁ + B₁ = **1.0346** (§IV.5).
  Two percent apart, which is the right amount for an ion-sphere estimate
  versus a Monte-Carlo fit. If you ever see a coefficient here that does *not*
  land near 1.05 in these units, it is wrong.

— **linear in Γ_e**, versus Γ^{3/2} in the weak limit (4.1). Two things follow:

1. The Z^{5/3} scaling is the same one that appears in the NSE Coulomb
   correction (§III.11). It is not a coincidence: both are the ion-sphere
   self-energy, once entering a rate and once entering a chemical potential.
2. **The weak and strong limits have different powers of Γ**, so no simple
   formula covers both — hence a fit anchored at both ends, which is exactly
   what §IV.5 shows `chugunov_2007` to be.

The physical picture also changes: weak screening is a *potential shift* at
fixed configuration, strong screening is a *thermodynamic* statement about
rearranging a correlated fluid. At Γ ~ 1–10, where this box lives, neither
picture is clean — the reactants are neither free nor caged.

## IV.4 Where the box sits — and hence which prescription

Tier 0 §0.1.4 established Γ ≈ 0.4–25 across the regime box. Recomputing for a
²⁸Si–²⁸Si pair **[derived here]**:

| T₉ | ρ | Γ(Si–Si) |
|---|---|---|
| 1.6 | 10⁹ | 9.14 |
| 3.0 | 10⁹ | 4.87 |
| 3.0 | 10⁷ | 1.05 |
| 7.9 | 10⁹ | 1.85 |
| 7.9 | 10⁷ | 0.40 |

**Intermediate coupling, all of it.** Neither (4.1) nor the ion-sphere limit is
quantitative here, which is precisely why the label configuration uses
`chugunov_2007` — a fit valid across the whole Γ range, with quantum
corrections. This is a case where the config choice, which looks arbitrary in
isolation, is forced by a number you can compute in three lines.

And the size of the effect **[derived here]**, at a representative Si-burning
composition:

| T₉, ρ | ²⁸Si+α | ²⁸Si+p | ⁵⁶Ni+α | ⁵⁴Fe+p |
|---|---|---|---|---|
| 3.0, 10⁸ | 1.430 | 1.173 | 1.988 | 1.343 |
| 4.0, 10⁹ | 1.903 | 1.349 | **3.281** | 1.711 |
| 5.0, 10⁹ | 1.635 | 1.251 | 2.522 | 1.504 |
| 7.9, 10⁹ | 1.319 | 1.129 | 1.717 | 1.255 |

Enhancements of 1.1× to 3.3×. **Screening is not a correction here; it is a
factor-of-three effect on the heaviest pairs.** Which is also why the project
measured, rather than assumed, that removing it drops trajectory-level
agreement from 0.76 to 0.53 [RESULTS 2026-07-10] — that measurement is how the
labels were *proved* to carry screening.

Read the ρ = 10⁹ rows alone (T₉ = 4.0 → 5.0 → 7.9: 1.903 → 1.635 → 1.319): the
enhancement falls monotonically with temperature, and rises with density — which
is exactly Γ ∝ n_e^{1/3}/T from (4.2). Screening is strongest at the cold, dense
corner of the box, which is also where the composition is furthest from NSE.

## IV.5 `chugunov_2007` term by term

`fluxes/screening.py` reimplements pynucastro's scalar jitclass over numpy state
vectors. Reading it as physics rather than code:

**1. The plasma state** (`plasma_arrays`).

$$
n_e = \frac{\rho\sum_i Z_i Y_i}{m_u},
\qquad
\text{gamma\_e\_fac} = \frac{e^2}{k}\left(\frac{4\pi}{3}\right)^{1/3} n_e^{1/3}
= \frac{e^2}{a_e k}
\tag{4.4}
$$

Note that Σ_i Z_i Y_i = Yₑ·Σ_i A_i Y_i = Yₑ for a normalised composition, so

$$
n_e = \frac{\rho\,Y_e}{m_u}
$$

— the same combination the weak tables index on (§V.5). Two different physics
modules, one plasma variable.

**2. The ion plasma temperature** (the quantum correction).

$$
T_p = \frac{\hbar}{k}\,e\sqrt{\frac{4\pi Z_1Z_2\,n_i}{m_i}} = \frac{\hbar\omega_p}{k},
\qquad
\omega_p^2 = \frac{4\pi (Z_1Z_2) e^2 n_i}{m_i}
\tag{4.5}
$$

ω_p is the plasma frequency of the reduced-mass ion pair — the scale at which
**zero-point ion motion** matters. T_norm = T/T_p is the classical-to-quantum
ratio; for T ≪ T_p the ions are quantum oscillators, not a classical fluid.
`smooth_clip_vec(T_norm, 0.1, 0.2)` floors it with a half-cosine so the fit never
extrapolates into a regime it was not built for. **[derived here]**
T_p = 1.23×10⁷ K at ρ = 10⁷ and 1.23×10⁸ K at ρ = 10⁹ for Si–Si, so T_norm
ranges ~13–640 across the box: firmly classical, and the clip never engages.
Good — but the clip's presence is what makes the module safe to call outside the
box.

**3. The quantum-corrected coupling.**

$$
\zeta = \left(\frac{4}{3\pi^2 T_{\rm norm}^2}\right)^{1/3},
\qquad
\tilde\gamma = \frac{\Gamma}{\bigl[\,1 + \zeta\bigl(\alpha_1 + \zeta(\alpha_2 + \alpha_3\zeta)\bigr)\bigr]^{1/3}}
\tag{4.6}
$$

$$
\alpha_1 = 0.022,\qquad
\alpha_2 = 0.41 - \frac{0.6}{\Gamma},\qquad
\alpha_3 = 0.06 + \frac{2.2}{\Gamma}
$$

ζ ∝ T_norm^{−2/3} is the quantum-diffraction parameter; the cubic in ζ is
Chugunov's fit to the Monte-Carlo free energy, and γ̃ is the *effective*
classical coupling that reproduces the quantum result.

**4. The enhancement.**

$$
\boxed{\;
h = \tilde\gamma^{3/2}\left(\frac{A_1}{\sqrt{A_2+\tilde\gamma}} + \frac{A_3}{1+\tilde\gamma}\right)
+ \frac{B_1\tilde\gamma^{2}}{B_2+\tilde\gamma}
+ \frac{B_3\tilde\gamma^{2}}{B_4+\tilde\gamma^{2}}
\;}
\tag{4.7}
$$

$$
A_1 = 2.7822,\quad A_2 = 98.34,\quad
\boxed{A_3 = \sqrt3 - \frac{A_1}{\sqrt{A_2}}},\quad
B_1 = -1.7476,\quad B_2 = 66.07,\quad B_3 = 1.12,\quad B_4 = 65
$$

and the returned value is max(h, 0).

**Check the asymptotics — this is the payoff of §IV.2.** As γ̃ → 0 the B-terms
vanish as γ̃² and the first bracket tends to a constant, so

$$
h \;\longrightarrow\; \tilde\gamma^{3/2}\left(\frac{A_1}{\sqrt{A_2}} + A_3\right)
= \sqrt3\,\tilde\gamma^{3/2}
$$

**because A₃ is *defined* as √3 − A₁/√A₂.** That is the weak-screening
(Debye–Hückel) limit of the one-component plasma, recovered exactly. As γ̃ → ∞
the B-terms dominate and h grows linearly in γ̃ — the strong-screening /
ion-sphere limit of §IV.3. **One functional form, both asymptotics, fitted in
between.** The A₃ line in the code is not a magic constant; it is a boundary
condition, and you can read it as such.

The final max(h, 0) enforces that screening never *suppresses* a rate.

## IV.6 Per-reaction pair construction — and the MESA difference

A reaction with three reactants needs more than one pair. pynucastro walks the
reactants building `screening_pairs`, including **composite intermediates**
(screen A against B, then the composite A+B against C). The compiled evaluator
just records the multiplicities:

```python
for n1, n2 in getattr(rate, "screening_pairs", []):
    key = (n1.Z, n1.A, n2.Z, n2.A)  ... screen_map[j, pair_index[key]] += 1
```
and the per-reaction correction is Σ over its pairs of h — i.e. the **product**
of factors, since h is a log.

MESA's `net_screen` uses a slightly different rule for ≥3 reactants (a
neutron-swap two-stage construction, mirrored explicitly in
`rates_compare.compare_screening` so the comparison is apples-to-apples). The
Step-4 measurement bounded the per-factor difference at **≤ 0.0021 dex**
[RESULTS 2026-07-10], and multi-body channels are pp-chain territory —
negligible in this box. The module docstring says exactly this, and it is a good
example of a known, bounded, documented discrepancy that is *not* a defect.

The same measurement is what **determined** the label configuration: MESA
`screening_mode='chugunov'` ≡ pynucastro `chugunov_2007` to median ratio
0.99999, max 0.0021 dex; `chugunov_2009` does **not** match (max 0.52 dex)
[RESULTS 2026-07-10]. Hence

```python
SCREENING_ALLOWED = frozenset({"chugunov_2007", None})
```

— a pin derived from a measurement, not a preference.

## IV.7 The screened-κ offset, derived

Here is the derivation §III.10 promised, and it is short enough to do in your
head once you see it.

Screening multiplies each *reaction* by exp(h) built from **that reaction's own
reactant pairs**. Consider a capture/photodisintegration pair at true
equilibrium:

- forward A + a → B: reactants are two charged nuclei, so h⁺ > 0;
- reverse B → A + a: a single reactant, **no pair at all**, so h⁻ = 0.

Let f⁺₀ = f⁻₀ = f₀ be the (equal) unscreened equilibrium fluxes. Then

$$
\kappa
= \frac{\bigl|f_0e^{h^+} - f_0e^{h^-}\bigr|}{f_0e^{h^+} + f_0e^{h^-}}
= \left|\tanh\!\left(\frac{h^+-h^-}{2}\right)\right|
\;\approx\; \frac{|\Delta h|}{2}\ \ \text{for } |\Delta h|\ll 1
\tag{4.3}
$$

**Verified numerically** on mesa_80 at T₉ = 6.3, ρ = 10⁹, NSE composition:
κ_screened = |tanh(Δh/2)| holds to 1.4×10⁻¹¹ — i.e. exactly, down to the
unscreened κ floor. Median κ = **7.361×10⁻²**, reproducing the RESULTS.md
7.4×10⁻² row; median |Δh| = 0.1475. **[derived here]**

Three consequences:

1. **This is real, not a bug.** Both pynucastro and MESA `net_screen` screen
   per-reaction; a screened capture genuinely does pair with an unscreened
   photodissociation in any code that does this. It is a property of the *rate
   configuration*, and the labels carry it.
2. **It is bounded by the screening factor itself.** κ_screened ≤ tanh(h_max/2),
   and with h ≤ ln(3.3) ≈ 1.2 on the heaviest pairs, κ ≲ 0.54 in the worst case
   — comparable to the v-flag floor it replaced. Hence the two-κ rule.
3. **Neutron pairs are exempt.** h = 0 on both sides for (n,γ)/(γ,n), so their
   screened κ is clean. Since those are the fastest-equilibrating pairs
   (§1.2.5), the *most* equilibrated pairs are also the ones least affected —
   which softens the practical impact but does not remove the need for the rule.

> ⚠ **A discrepancy to raise, not to paper over.** `docs/rate-crosscheck.md` and
> root `CLAUDE.md` characterise this as "κ ≈ |Δ ln scor|". The exact relation
> (4.3) is |tanh(Δh/2)|, i.e. **|Δh|/2** in the small-offset limit — a factor of
> two. The measured numbers confirm the halved form: median |Δh| = 0.1475 gives
> κ = 0.0736, and 0.0736 is the number in `RESULTS.md`, not 0.1475. The
> *measured* row is right; the *characterisation* next to it is loose by 2×.
> Per the docs contract this is a docs question, not a code question — flag it,
> do not silently edit.

## IV.8 Code and oracle

`TestScreeningVectorized::test_matches_pyna_scalar` checks three things in
sequence, and the ordering is deliberate:

1. `n_e` and `gamma_e_fac` against `make_plasma_state` (≤10⁻¹² rel) — *the
   plasma state* first,
2. then `chugunov_2007_vec` against the scalar `chugunov_2007` for **every pair
   at every state** (≤10⁻¹² abs) — *the function*,
3. and separately, `test_screened_lambda_matches_scalar_eval` checks the
   *integration* into λ via `rate.eval(..., screen_func=chugunov_2007)`.

State → function → integration. Each layer is pinned independently, so a failure
localises. Worth copying as a pattern for any reimplementation-of-a-reference
work.

## IV.9 Screening of *weak* rates — a separate mechanism entirely

Everything above is screening of a **charged-particle entrance channel**. Weak
reactions have no such channel — but they are not unscreened, and this is a
prerequisite that neither Tier 0 nor anything above covers.

Electron capture depends on the electron chemical potential μ_e (§V.4), and μ_e
in a strongly-coupled plasma is not the ideal-Fermi-gas value: the electron sea
is polarised around each nucleus, which shifts the energy of the captured
electron. The tables carry this explicitly. Reading the eight columns of a
weaklib/LMP table:

```
TableIndex:  RHOY=0  T=1  MU=2  DQ=3  VS=4  RATE=5  NU=6  GAMMA=7
```

- **MU** — the electron chemical potential at that (ρYₑ, T), including rest mass.
- **VS** — the **screening potential**: the Coulomb correction to μ_e, i.e.
  exactly this effect.
- **DQ** — the effective Q-value shift from thermal population of parent excited
  states (§V.3's "stellar rate" statement, tabulated).

**And the engine reads only column 5.**

```python
f2d = data[:, 5].reshape(len(rhoy), n_temp).copy()     # compile.py:222
```

That is *correct* for the rate itself — the tabulated RATE already has the
screening and thermal-population physics folded in, which is the entire point of
tabulating on a (T, ρYₑ) grid. MU, DQ and VS are diagnostic columns describing
*how* the tabulator arrived at RATE, not corrections to be applied.

But two consequences are worth carrying:

1. **Weak-rate screening is not the chugunov screening.** The two-κ conventions
   rule (§III.10) concerns `chugunov_2007` on strong pairs. Turning screening
   "off" in the engine (`screening=None`) does **not** turn off the screening
   inside the weak tables — it cannot, because that physics is baked into the
   tabulated numbers. An "unscreened" run is unscreened *on the strong sector
   only*. Since weak columns are unpaired and carry κ ≡ 1 regardless, this does
   not corrupt any κ threshold — but it does mean "unscreened" is a
   sector-specific statement, not a global one.
2. **Column 6 (NU) is dropped, and it is the one invariant #5 needs.** The
   neutrino energy-loss rate per reaction is tabulated and pynucastro exposes it
   as `TabularRate.get_nu_loss`, but the compiled evaluator never builds it. Any
   flux-route energy accounting that must be "net of neutrino losses" — which is
   the trajectory-file `eps_nuc` convention [RESULTS 2026-07-11] — needs this
   column compiled in. Named in §VIII as an open prerequisite, since the
   flux-route vs bbq `eps_nuc` comparison is already recorded as UNRESOLVED
   [RESULTS 2026-07-10].

## IV.10 Self-check for S4

1. Derive (4.1) from the linearised Poisson–Boltzmann equation. Where does the
   assumption of weak coupling enter, and what does it mean physically?
2. Compute Γ for a ⁵⁶Ni–α pair at T₉ = 4, ρ = 10⁹. Is `chugunov_2007` the right
   prescription there? What would `screen5` (Salpeter/Graboske) get wrong?
3. Show that A₃ = √3 − A₁/√A₂ enforces the Debye–Hückel limit. What would break
   if someone "cleaned up" A₃ to a rounded literal?
4. Why does the composite-intermediate rule for three-body screening not matter
   for this project's verdicts? Name the measurement that bounds it.
5. Derive (4.3). Then predict κ_screened for a pair whose forward enhancement is
   1.9× and whose reverse is unscreened, and check it against §IV.4's table.
6. A colleague proposes evaluating the equilibrium mask on screened κ "because
   that is what the labels use". Give the two-sentence rebuttal.

---

# Part V (S5) — The weak sector

Files: `graph/network.py` (table precedence), `graph/stoich.py` (the lepton
ledgers), `fluxes/compile.py` + `engine.py` (the tabular path),
`crosscheck/mesa_dump.py` (MESA-side table provenance). Inventory:
`docs/weak-inventory-step3.md`.

**This is the sector the entire project is about.** Yₑ is the target
observable (§I.2), and Yₑ changes only through weak reactions. Everything in
Parts I–IV is, from the project's point of view, the machinery that determines
*which nuclei are around* for the weak reactions to act on.

## V.1 Why weak reactions are categorically different

Six differences, each with a downstream consequence:

| | Strong/EM | Weak |
|---|---|---|
| Interaction | strong / electromagnetic | weak (G_F) |
| Rate scale in this box | 10³–10⁸ s⁻¹ | 10⁻⁵–10² s⁻¹ |
| Barrier | Coulomb (§1.2) | none — the electron is *bound to the plasma*, not tunnelling |
| Reverse partner in-network | yes, and it equilibrates | **no** |
| Conserves Z | yes | **no** — ΔZ = ±1 at fixed A |
| Neutrino | — | escapes, carrying energy and lepton number |

The fourth row is the one that generates a project invariant. A β⁻ decay's
formal inverse is not the corresponding electron capture: the true inverse of

$$
A \;\longrightarrow\; B + e^- + \bar\nu
\qquad\text{is}\qquad
B + e^- + \bar\nu \;\longrightarrow\; A
$$

which requires an antineutrino to be *absorbed* — and the neutrinos free-stream
out (§0.4.2). **There is no detailed-balance pair.** Hence:

> **CLAUDE.md invariant #2: weak columns are NEVER eligible for the equilibrium
> mask.** Not by convention — by the absence of the reverse process.

and, in code, three separate places enforce it structurally:

```python
# compile.py _pair_maps: weak columns are ALWAYS unpaired
if stoich.weak_mask[j]: continue          # never gets a pair_col
# engine.py: f_minus stays 0 for unpaired columns → κ = |φ|/(f⁺+0) = 1
# test_flux_engine.py::test_weak_columns_have_zero_reverse_and_kappa_one
```

κ ≡ 1 for every weak column carrying flux — the mask threshold κ > 0.1 can
therefore never exclude one, *even if someone forgets the rule*. That is the
difference between an invariant and a comment.

## V.2 From the golden rule to ft values

The allowed-approximation β-decay rate. Fermi's golden rule for a transition
with lepton phase space:

$$
\lambda = \frac{2\pi}{\hbar}\overline{|M_{fi}|^2}\,\rho_f
$$

For an allowed transition (leptons carry no orbital angular momentum, so their
wavefunctions are evaluated at the nucleus and factor out), the nuclear matrix
element separates from the lepton phase-space integral, giving

$$
\lambda = \frac{\ln 2}{K}\,\bigl[\,g_V^2 B(F) + g_A^2 B(GT)\,\bigr]\; f(Z,W_0)
\tag{5.1}
$$

with the **phase-space integral** (in units of m_ec²)

$$
f(Z,W_0) = \int_1^{W_0} F(Z,W)\,W\sqrt{W^2-1}\,(W_0-W)^2\,dW
\tag{5.2}
$$

W the total electron energy, W₀ the endpoint, F(Z,W) the Fermi function
(Coulomb distortion of the outgoing electron wave). The **comparative
half-life** ft = f·t₁/₂ then isolates the nuclear physics: ft is small for
strong transitions, large for hindered ones, and the tabulated log ft is the
experimental handle.

**Two matrix elements, two selection rules:**

- **Fermi (vector)**, B(F) = |⟨τ₊⟩|²: operator Στ, ΔJ = 0, no parity change.
  Non-zero essentially only for isobaric analogue transitions, so B(F) is
  concentrated in a single state at high excitation. Largely irrelevant for
  stellar EC on Fe-peak nuclei.
- **Gamow–Teller (axial)**, B(GT) = |⟨στ₊⟩|²: operator Σστ, ΔJ = 0, ±1
  (no 0→0), no parity change. **This is the one that matters.**

Note the crucial feature of (5.2): **f ∝ W₀⁵ for large endpoints.** The rate is
a very steep function of the available energy. In a plasma, "available energy"
includes the electron Fermi energy — which is what §V.4 exploits.

## V.3 Gamow–Teller strength, and why these rates are shell-model calculations

The GT⁺ strength (the direction relevant to electron capture) is not
concentrated in a single state; it is distributed over a **Gamow–Teller
resonance** spread over several MeV of excitation in the daughter, with
substantial strength at low excitation energy.

Three facts that follow, all of which shape the project:

1. **Stellar rates ≠ laboratory rates.** In the lab, the decay samples only
   states below the ground-state Q-value. In a star at T₉ = 4, the *parent* is
   thermally excited (kT = 0.34 MeV, and §III.3's table shows pf up to 4 for
   mid-shell nuclei) — so transitions from excited parent states, some with
   much larger B(GT) or much more favourable energetics, contribute. **A
   stellar weak rate is a thermal average over parent states**, which is why it
   must be tabulated as a function of T, not just of ρYₑ.
2. **The strength distribution must be calculated, not measured.** (p,n) and
   (n,p) charge-exchange experiments constrain total strengths and
   distributions for stable targets, but the network needs rates for unstable
   nuclei at finite temperature. Hence large-scale shell-model diagonalisation
   in the pf shell — Langanke & Martínez-Pinedo (LMP).
3. **Hence the factor 2–10 uncertainty** (§0.3.3): quenching of the axial
   coupling, model-space truncation, and the placement of GT strength all enter.
   This is the largest physics uncertainty anywhere in this problem, and it sits
   directly on the project's target variable.

> Worth sitting with: the quantity this project emulates to 10⁻⁶ per step is
> computed from rates known to a factor of a few. §1.3.3's sentence applies with
> full force here.

## V.4 Electron capture in a degenerate plasma

Now the plasma physics, which is what makes the weak sector density-dependent.

In the lab, EC uses a bound atomic electron. In this plasma the atoms are fully
ionised, and capture proceeds on the **degenerate free-electron sea**. The rate
becomes an integral over the electron Fermi–Dirac distribution:

$$
\lambda_{\rm EC} \propto \int_{W_{\rm thr}}^{\infty}
W\sqrt{W^2-1}\,(W+q)^2\,F(Z,W)\,
\frac{dW}{1+\exp\bigl[(W-\mu_e)/kT\bigr]}
\tag{5.3}
$$

Compare with (5.2): the outgoing-electron phase space has been replaced by an
**incoming-electron occupation**, and the neutrino now carries the surplus
(W + q)². Two structural consequences:

- **Threshold.** If the nuclear transition is endothermic by |Q|, capture
  requires W ≥ W_thr ≈ |Q| + m_ec². At low density the Fermi sea does not reach
  that energy and the rate is exponentially suppressed; once μ_e exceeds the
  threshold the rate turns on hard.
- **Steepness.** With μ_e ≫ kT (degenerate), the occupation factor is a near
  step function, so λ_EC ≈ ∫₁^{μ_e}. The **integrand** goes as W⁴ at large W
  (W√(W²−1) → W² from the electron phase space, times (W+q)² → W² from the
  neutrino), so the **integral** goes as the fifth power:

$$
\lambda_{\rm EC} \sim \mu_e^5 \qquad (\mu_e \gg W_{\rm thr})
$$

  **A fifth-power dependence on the electron chemical potential** — and
  μ_e ∝ (ρYₑ)^{1/3} in the relativistic degenerate limit, so λ_EC ∝ (ρYₑ)^{5/3}.
  This is why the tables are indexed on ρYₑ, and why the box's two decades in ρ
  matter enormously to Yₑ.

**Numbers across the box** (relativistic degenerate E_F = √(p_F²c² + m_e²c⁴),
p_F = ℏ(3π²n_e)^{1/3}) **[derived here]**:

| ρ (g/cm³) | Yₑ | n_e (cm⁻³) | E_F (MeV) |
|---|---|---|---|
| 10⁷ | 0.50 | 3.01×10³⁰ | 1.019 |
| 10⁸ | 0.50 | 3.01×10³¹ | 1.967 |
| 10⁹ | 0.45 | 2.71×10³² | 3.983 |

⚠ **Get the free-proton threshold right — it is easy to double-count the
electron rest mass.** For p + e⁻ → n + ν the reaction Q is
(m_p + m_e − m_n)c² = **−0.782 MeV**, so by the rule just stated the threshold
*total* electron energy is W_thr = |Q| + m_ec² = 0.782 + 0.511 =
**1.293 MeV** — which is just (m_n − m_p)c², as it must be. It is **not**
m_ec² + 1.293; the 1.293 MeV already includes the rest mass.

Set against W_thr = 1.293 MeV: **the box's lower ρ edge sits just below it and
the upper edge far above.** Solving E_F(ρ) = W_thr gives the crossing at
**ρ ≈ 2.4×10⁷ g/cm³** at Yₑ = 0.5 **[derived here]** — inside the box, near its
bottom edge, rather than somewhere between the 10⁷ and 10⁸ rows of the table.
Tier 0 §0.1.5 derived that edge; you can now see it is a *fifth-power* switch,
not a soft one. The regime box brackets the turn-on of the Yₑ-controlling
process — the box is defined by this physics.

⚠ **And read that table as a T = 0 quantity.** E_F above is the cold-degenerate
Fermi energy; it is the right variable at the cold, dense end of the box and
*not* at the hot, thin corner. Solving the finite-temperature charge-neutrality
condition instead, at T₉ = 7.9, ρ = 10⁷, Yₑ = 0.498 the electron chemical
potential is **μ_e = 0.16 MeV < m_ec²** — degeneracy parameter
(μ_e − m_ec²)/kT ≈ −0.5, i.e. the electrons there are **not degenerate at all**
**[derived here]**. The "degenerate free-electron sea" framing of this section,
and the μ_e⁵ scaling that follows from it, are statements about the cold/dense
part of the box. See §VIII.C.6, which is the same corner seen from the
screening side.

Also note the **self-limiting feedback**: capture lowers Yₑ, which lowers n_e,
which lowers μ_e, which suppresses further capture. The Yₑ evolution is
stiffly self-damping, which is part of why the "one-way ratchet" (§0.4.2) is
gradual rather than catastrophic.

### V.4b Pauli blocking — the microphysical cause of the one-way ratchet

Tier 0 §0.4.2 established that Yₑ ratchets *down* and attributed it to neutrino
free-streaming (which removes the inverse process). There is a second, entirely
independent mechanism, and it is stronger:

**β⁻ decay emits an electron into a Fermi sea that is already full.** The
final-state electron must land above μ_e. If the decay endpoint W₀ < μ_e, the
transition is **Pauli-blocked** — the phase-space integral (5.2) is truncated at
μ_e instead of W₀:

$$
f_{\beta^-} \;\longrightarrow\; \int_{\mu_e}^{W_0} F(Z,W)\,W\sqrt{W^2-1}\,(W_0-W)^2\,dW
\;\;\to\; 0 \ \text{ as } \mu_e \to W_0
$$

So in a degenerate plasma, **electron capture is enhanced (λ ∝ μ_e⁵) while β⁻
decay is suppressed, both by the same μ_e.** That is the ratchet, and it is a
much sharper statement than "neutrinos escape".

**This is directly visible in the tables.** Measuring the local power-law index
d log₁₀λ / d log₁₀(ρYₑ) inside the box **[derived here]**:

| Channel | type | index range |
|---|---|---|
| ⁵⁶Ni → ⁵⁶Co | EC | +0.07 … +2.35 |
| ⁵⁵Co → ⁵⁵Fe | EC | +0.07 … +2.46 |
| ⁵⁴Fe → ⁵⁴Mn | EC | +0.08 … **+5.39** |
| ⁴⁸Ca → ⁴⁸Sc | β⁻ | **−4.88 … −0.04** |

EC indices are positive and bracket the 5/3 degenerate scaling (rising well
above it near threshold, where the exponential turn-on dominates, and falling to
~0 where the rate saturates). **The β⁻ index is negative throughout** — the rate
*falls* by up to five decades per decade of ρYₑ. Nothing else in the network
behaves this way.

Two consequences worth carrying:

1. **The 5/3 scaling of §V.4 is the asymptotic middle of a range, not a law.**
   Quote it as the degenerate limit, not as the behaviour in the box.
2. **The Yₑ-raising sector is density-suppressed exactly where the project's
   interesting physics lives** (ρ → 10⁹). This sharpens the mesa_80 concern of
   §V.10: mesa_80 carries 19 β⁻ channels, but at high density those carry little
   flux anyway — so the *dominant* asymmetry between the networks is on the EC
   side (21 vs 84), which is the side that matters. Good news for size transfer;
   bad news for anyone hoping the β⁻ deficit is the whole story.

## V.5 The (T, ρYₑ) table: what is actually in the file

Read one **[derived here]**. `Ni56_to_Co56_weaktab` (source: langanke):

```
shape (143, 8) = 11 log10(ρYₑ) nodes × 13 log10(T) nodes × 8 columns
log10 ρYₑ grid : 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
log10 T   grid : 7, 8, 8.30103, 8.60206, 8.845098, 9, 9.176091,
                 9.30103, 9.477121, 9.69897, 10, 10.477121, 11
columns        : [log ρYₑ, log T, μ, ΔQ, Vs, log₁₀ rate, log₁₀ ν-loss, log₁₀ γ-heating]
```

Four observations that each explain a project measurement:

1. **The grid is coarse.** One full decade per ρYₑ cell. The box spans
   log ρYₑ ∈ [6.65, 8.70] — two and a bit cells — and log T ∈ [9.204, 9.898].
   Interpolating a fifth-power function on a one-decade grid is where the
   accuracy goes.
2. **T₉ = 5 is exactly a node** (log₁₀(5×10⁹) = 9.69897). That is why the
   cross-check's median |Δlog₁₀| collapses to **0.003 dex at the T₉ = 5 node**
   while off-node medians are 0.03–0.18 dex [RESULTS 2026-07-10]. The
   discrepancy is *interpolation scheme*, not physics — MESA bilinear vs
   pynucastro's own interpolant on the same table.
3. **The box is interior everywhere.** T₉ ≤ 7.9 ≪ 10¹¹ K, log ρYₑ ≤ 8.7 < 11.
   No extrapolation. Outside the box the two codes diverge qualitatively —
   MESA **clips** to the table edge (`rates/private/eval_weak.f90`), pynucastro
   **extrapolates** [RESULTS 2026-07-10]. A fact to carry if the regime ever
   widens.
4. **The rate is stored as log₁₀.** So bilinear interpolation is bilinear *in
   the log* — a geometric interpolation of the rate, which is the right choice
   for a quantity spanning decades.

**In the code**, `compile.py:217–226` slices the flat table into
`(n_rhoy, n_temp)` and the engine interpolates with a clamped searchsorted:

```python
i = maximum(0, minimum(len(rhoy)-1, searchsorted(rhoy, logrhoy)) - 1)
...
lam[col] = 10.0 ** _bilinear_vec(...)
```

and raises on out-of-bounds rather than clipping — a deliberate divergence from
MESA's behaviour, chosen so the engine cannot silently produce edge values.

**And the ρYₑ that indexes it comes from the composition:**
```python
ye = (cn.stoich.Z @ Y) / (cn.stoich.A @ Y)     # engine.py:151
logrhoy = np.log10(rho * ye)
```
Note Yₑ is computed as ΣZᵢYᵢ / ΣAᵢYᵢ, i.e. normalised, matching pynucastro's
`Composition.ye`. Since ΣAᵢYᵢ = 1 for a valid composition this is a no-op — but
it is a *robust* no-op, and it means the tabular path degrades gracefully on
slightly unnormalised inputs instead of drifting.

### V.5b Interpolation error, derived — and why it lands where it does

The cross-check reported weak-tabular medians of 0.03–0.18 dex off-node with a
β⁻ tail to 0.8 dex, and attributed it to "MESA bilinear vs pynucastro
interpolant" [RESULTS 2026-07-10]. That attribution can be *predicted* rather
than asserted, and doing so is a good exercise in reading an error budget.

**The theory.** Bilinear interpolation of a function f on a cell of width h has
error bounded by the second derivative:

$$
|f_{\rm interp} - f| \;\le\; \frac{h^2}{8}\max|f''|
\;=\; \frac{1}{8}\max\bigl|\Delta^2 f\bigr| \quad\text{(midpoint, } h = \text{one grid step)}
$$

Here f = log₁₀λ and the grid step is one full decade in log ρYₑ, so Δ²f is
just the **second difference of the tabulated log-rates**. And the key
structural fact:

> **Bilinear interpolation in log–log is exact for a power law.** If
> λ ∝ (ρYₑ)^p with constant p, the second difference is zero and the error
> vanishes identically. All interpolation error therefore lives where the
> *power-law index changes* — i.e. at thresholds and saturation knees.

**The measurement.** Second differences of the real tables, restricted to the
box **[derived here]**:

| Channel | class | max\|Δ²\| ρYₑ dir | predicted err | max\|Δ²\| T dir | predicted err |
|---|---|---|---|---|---|
| ⁵⁶Ni → ⁵⁶Co | EC controller | 0.80 dex | **0.100** | 0.90 | 0.113 |
| ⁵⁵Co → ⁵⁵Fe | EC controller | 0.93 | **0.116** | 1.01 | 0.126 |
| ⁴⁴Sc → ⁴⁴Ca | EC | 0.68 | **0.085** | 0.87 | 0.109 |
| ⁵⁴Fe → ⁵⁴Mn | EC, steep | 3.95 | **0.494** | 1.10 | 0.137 |
| ⁴⁸Ca → ⁴⁸Sc | β⁻, steep | 1.73 | 0.216 | 3.92 | **0.490** |

Compare with the measurement: off-node medians 0.03–0.18 dex, β⁻/steep tail
≤ 0.8 dex, and the docs name `ca43/ca48/k40/sc44 wk-minus` as the tail
channels. **The bound predicts both the scale and the membership.** The Yₑ
controllers sit at ~0.1 dex, matching their measured at-node ≤0.012 / off-node
0.009–0.095 dex; the steep channels sit at 0.2–0.5 dex, matching the ≤0.8 dex
tail.

Three things this buys you:

1. **The residual is fully explained** — it is a grid-resolution artifact of a
   *shared* table, not a physics disagreement. The 0.1 dex band was the right
   band, and it was justified before the measurement rather than after.
2. **The remedy is known and cheap**: evaluate weak λ MESA-side at off-node
   states (which is exactly the Step-5 rule), or refuse to interpolate and
   restrict analyses to node temperatures — T₉ = 5.0 being a node is why that
   state recurs throughout the project.
3. **The error is largest exactly where λ is smallest** (steep β⁻ channels sit
   at log λ ≈ −27 in the box). A 0.5 dex error on a rate 25 decades below the
   dominant one is irrelevant to ΔYₑ. **The error budget and the importance
   budget are anti-correlated**, which is why a 0.8 dex outlier in this sector
   was correctly classified as benign rather than blocking.

## V.6 The three channels and the lepton ledger

| weak_type | reaction | ΔZ | d_e⁻ | d_ν | d_ν̄ | effect on Yₑ |
|---|---|---|---|---|---|---|
| `electron_capture` | A(Z) + e⁻ → A(Z−1) + ν | −1 | −1 | +1 | 0 | **lowers** |
| `beta_pos` | A(Z) → A(Z−1) + e⁺ + ν | −1 | −1 | +1 | 0 | **lowers** |
| `beta_neg` | A(Z) → A(Z+1) + e⁻ + ν̄ | +1 | +1 | 0 | +1 | **raises** |

The β⁺ row is the one that trips people. The emitted positron annihilates
promptly with a plasma electron, so its *net* effect on the electron ledger is
−1 — the nucleus loses a unit of charge to the electron sea, exactly as in EC.
EC and β⁺ therefore share a ledger signature. `graph/stoich.py`'s module
docstring states this and the code enforces it:

```python
if dq != d_e[j]:
    raise ValueError("... nuclear ΔZ = ... but ledger d_electron = ... — "
                     "charge-to-lepton closure broken")
```

**The ledgers are assigned from `weak_type`, never back-derived from Z·ν.** The
docstring says why: back-deriving would make the charge-to-lepton closure a
tautology, and the conservation gate would pass vacuously. This is the single
best example in the repo of a test being designed so it *can* fail.

Also enforced: **|ΔZ| = 1 exactly** on every weak column — a weak reaction is a
single-nucleon transition. A |ΔZ| = 2 weak column would be a double-β process,
absent from these networks, and the build aborts naming the reaction.

## V.7 The table families and the precedence question

Five families appear in pynucastro's `TabularLibrary`, four of which have a MESA
analogue:

| Label | Source | Coverage |
|---|---|---|
| `ffn` | Fuller, Fowler & Newman (1980–85) | broad, early, independent-particle-model based |
| `oda` (MESA "OHMT") | Oda et al. (1994) | sd shell, A = 17–39 |
| `langanke` (MESA "LMP") | Langanke & Martínez-Pinedo (2001) | pf shell, the Fe peak — large-scale shell model |
| `suzuki` | Suzuki et al. | sd shell, more modern than Oda |
| `pruet_fuller` | — | no MESA analogue |

MESA weaklib's precedence is **LMP > Oda > FFN**, with `use_suzuki_weak_rates`
defaulting to `.false.` — and bbq runs with an empty `&nuclear` namelist, so
that default *is* the label configuration.

pynucastro expresses precedence as an ordering where later wins, so the pinned
constant is

```python
DEFAULT_TABULAR_ORDERING = ("suzuki", "pruet_fuller", "ffn", "oda", "langanke")
```

**This was measured, not assumed.** Under the pre-Step-4 suzuki-topped
ordering, 14 (mesa_80) / 23 (mesa_151) matched weak pairs used Suzuki tables
where MESA uses Oda — *every one an sd-shell nuclide with A = 17–28*, exactly
Suzuki's coverage. After the reordering: **zero mismatches** [RESULTS
2026-07-09]. That the residual set was exactly Suzuki's coverage region is the
tell that made the diagnosis certain.

The consequence is a guard, because a build with the wrong ordering would be
subtly wrong in a way no conservation test can catch:

```python
if tuple(info.tabular_ordering) != DEFAULT_TABULAR_ORDERING:
    raise ValueError("... != pinned ADR-0003 ordering ...")
```

**One genuine provenance difference survives:** ⁷Be → ⁷Li electron capture,
where MESA uses a shipped `S13_r_be7_wk_li7.h5` (T, ρYₑ) table and pynucastro
uses a REACLIB `ec` fit — 2.58–2.77 dex apart [RESULTS 2026-07-10]. Carried as
an open flag; ⁷Be is light-sector and peripheral to Si-burning Yₑ. Note the
discipline: it is *not* rounded down to "agreement", it is named and bounded.

**Duplicate-link resolution.** Where both a REACLIB fit and a tabular rate cover
the same transition, `build_rate_collection` drops the ReacLib member:

```python
for rate in group:
    if isinstance(rate, pyna.rates.TabularRate): survivors.append(rate)
    else: full.remove_rate(rate)
```

Correct, because the tabular rate is the (T, ρYₑ)-dependent one — and §V.4 just
showed that the ρYₑ dependence *is* the physics. A REACLIB weak fit carries only
T dependence and would miss the fifth-power μ_e switch entirely.

## V.8 Neutrino losses

Column 6 of the table is log₁₀ of the neutrino energy-loss rate. Two roles:

- **Energetics.** Tier 0 §0.4 established that neutrinos free-stream out
  (§0.4.2), so their energy is *lost*, not thermalised. The trajectory-file
  `eps_nuc` is net of neutrino losses [RESULTS 2026-07-11] — a convention
  difference from the training CSVs that has bitten before.
- **The open item.** ⟨E_ν⟩ per capture (§0.4.3) is needed to convert a weak flux
  into an energy loss; the tables give the loss directly, which is why the
  project can defer it. But any *flux-route* energy accounting (invariant #5)
  must decide whether Q_j is the full Q or Q − Q_ν. Worth knowing that the
  MESA-side dump carries both `q` and `qneu` per reaction
  (`crosscheck/mesa_dump.py:92–93`) precisely so the question is answerable.

## V.9 Code path summary

```
isotopes_mesa80.yaml
   ↓ load_isotope_table
graph/network.py: ReacLibLibrary + TabularLibrary(ordering=PINNED)
   ↓ linking_nuclei → duplicate resolution (tabular wins) → disposition drop
   ↓ build_stoich → weak_mask, weak_type, d_electron/d_neutrino/d_antineutrino
fluxes/compile.py: tabular rates → (tab_cols, tab_rhoy, tab_temp, tab_rate2d)
   ↓                strong rates → coefficient tensor (Part II)
fluxes/engine.py:  lam[tab_cols] = 10**bilinear(log ρYₑ, log T)
   ↓                R = prefactor · ρ^densexp · ΠY · lam
   ↓                dye_weak = (Z ν)[weak] @ R[weak]
```

That last line is invariant #3 made computable: the physical Yₑ signal carried
by the weak columns, asserted nonzero by
`test_flux_engine.py::test_dye_weak_nonzero`.

## V.10 The two networks are not the same weak network

Census [RESULTS 2026-07-09]:

| | reactions | ReacLib | tabular | weak | EC | β⁻ | β⁺ |
|---|---|---|---|---|---|---|---|
| mesa_80 | 607 | 569 | 38 | 46 | 21 | 19 | 6 |
| mesa_151 | 1518 | 1354 | 164 | 173 | 84 | 84 | 5 |

**mesa_151 has 3.8× the weak channels of mesa_80 for 1.9× the species.** The
asymmetry is not uniform, either: mesa_80 carries only **6/9 EC controllers and
0/8 β-decay partners** of the Yₑ-controller set [RESULTS 2026-07-08]. Reading
the inventory tables directly, mesa_80's Fe-peak weak sector is essentially
{⁵⁶Ni, ⁵⁶Co, ⁵⁶Fe, ⁵⁹Cu, ⁵⁹Ni, n ⇌ p}, while mesa_151 carries the full
V–Cr–Mn–Fe–Co–Ni block from A = 45 to 61.

Three consequences to carry forward:

1. **Size transfer is not just "more nodes".** A model trained on mesa_80 has
   never seen a ⁵⁵Fe or ⁵³Mn electron capture. The zero-shot mesa_151 falsifier
   (Yₑ error > 2× internal ⇒ report as size-*adaptable*, not size-transferable)
   is testing exactly this.
2. **Loss weighting must account for it.** The weak columns are a much smaller
   fraction of mesa_80's 607 than of mesa_151's 1518, while carrying the same
   physical importance.
3. **The Yₑ physics floor differs between the networks**, so the 5×10⁻³–1.5×10⁻²
   per-trajectory floor is not automatically a shared number.

## V.11 Self-check for S5

1. Derive the W₀⁵ scaling of (5.2) in the ultrarelativistic limit. Then explain
   the (ρYₑ)^{5/3} scaling of λ_EC.
2. Compute E_F at ρ = 3×10⁸, Yₑ = 0.47. Is free-proton capture allowed? By how
   much energy?
3. Why must a stellar weak rate be tabulated in T even at fixed ρYₑ, when the
   *strong* rates need only T? (Two distinct reasons; name both.)
4. Verify from the inventory that EC and β⁺ share a ledger signature but have
   different reaction arities. What does that imply for `prefactor` and
   `dens_exp` on the two classes?
5. The engine raises on out-of-table states while MESA clips. Argue which is
   correct for *this project*, and name a situation where the other choice would
   be right.
6. Given the mesa_80 weak census, predict qualitatively how a mesa_80-trained
   emulator will fail on mesa_151 high-Yₑ trajectories. Which isotopes first?
7. Why does dropping the ReacLib member of a duplicate weak link matter more
   at ρ = 10⁹ than at 10⁷?
8. Derive the Pauli-blocking truncation of (5.2) and show it gives a *negative*
   d log λ / d log(ρYₑ). Predict the sign for an EC channel and check both
   against §V.4b.
9. A weak channel has max|Δ²log₁₀λ| = 2.4 dex across a grid cell. Bound its
   interpolation error, then decide whether it belongs on the outlier list —
   and say what else you need to know to decide.
10. The engine reads only column 5 of the weak tables. Name one quantity the
    project needs that lives in another column, and say which invariant it
    blocks.

---

# Part VI (S6) — Rate reconciliation

The whole `crosscheck/` package, plus the Fortran probe in `src/mesa_probes/`.
Docs: `docs/reaction-reconciliation.md`, `docs/rate-crosscheck.md`. Configs:
`reactions_mesa{80,151}_mesa.yaml`, `reaction_disposition_mesa{80,151}.yaml`,
`rate_outliers.yaml`, `appendixb_excluded_channels.yaml`. Notebook: 04.

## VI.1 Why this node exists at all

The project trains on labels produced by **MESA r23.05.1 + bbq**, but computes
fluxes, κ, and equilibrium diagnostics with **pynucastro 2.12.0**. Those are two
independent implementations of the same physics. Every downstream claim of the
form "reaction r carries 40% of ΔYₑ" is a statement about the *label* dynamics,
inferred from the *pynucastro* rate set.

That inference is only valid if the two rate sets are the same object. S6 is the
node that establishes it — and it decomposes into two questions that must not be
conflated:

1. **Membership.** Do the two sides contain the same reactions? (§VI.2–VI.4)
2. **Values.** Where they agree on membership, do they agree numerically?
   (§VI.5–VI.7)

A failure of (1) is unfixable by tuning; a failure of (2) is a bounded error you
can quantify and carry. Answering them separately is what makes the result
actionable.

## VI.2 The canonical key: making "same reaction" decidable

Two codes name reactions differently (`r_si28_ag_s32` vs `Si28 + He4 ⟶ S32 + 𝛾`),
so identity must be defined structurally. `crosscheck/canonical.py`:

```
directed key := "<lhs>=><rhs>",  each side = sorted multiset rendered "name*count"
pair key     := unordered pair joined by "<=>", smaller side first
```

e.g. `al25*1+neut*1=>al26*1`. Four design decisions inside that, each
deliberate:

1. **Directed, not undirected.** Forward and reverse are *distinct* reactions on
   both sides — MESA softwires them separately, pynucastro builds separate Rate
   objects. Under this convention a forward/reverse counting mismatch is
   *impossible*, which removes an entire class of spurious diff.
2. **Multisets with counts**, so 3α → ¹²C is `he4*3=>c12*1` and cannot collide
   with anything else.
3. **Electrons and neutrinos are not in the key.** Weak reactions are identified
   by their nuclide transition; lepton bookkeeping lives in C, not in reaction
   identity. This is the right call because the two inventories describe leptons
   differently, and it costs exactly one exception (below).
4. **Species names are fail-loud.** `from_pyna` / `from_mesa` map to project
   chem ids through explicit whitelists and *raise* on anything unrecognised —
   no silent passthrough. Isomers (`al26-1`) are deliberately unmapped, since
   they are absent from both networks and a silent map would hide their
   appearance.

**The one exception, and how it is handled.** Dropping leptons from the key
makes pp and pep collide: both are `h1*2=>h2*1`, one β⁺ and one EC.
`tag_weak_channels` detects colliding keys, requires *all* members of a
colliding group to be weak (raising otherwise), and appends `;ec` / `;wk`. Both
inventories resolve the same split identically, so cross-matching survives.

> This is a small function that repays reading. It is what a decidable identity
> convention looks like when the world does not quite cooperate: state the rule,
> detect the exception, assert the exception is of the expected kind, tag it
> symmetrically on both sides, then assert no collision survives.

## VI.3 Membership vs values

| | Instrument | Output |
|---|---|---|
| Membership | `mesa_probe dump_net` → `mesa_dump.dump_to_records` vs `reconcile.pyna_inventory` | `reaction_disposition_*.yaml` |
| Values | `mesa_probe eval_rates / eval_weak / eval_screen` vs `rate.eval` | `crosscheck_{bare,weak,screen}_*.csv`, `rate_outliers.yaml` |

Note that `pyna_inventory` builds with `disposition=None` **on purpose**:

```python
# the disposition file is defined as the diff between the raw pynucastro set and
# MESA; building with the disposition applied here would make reconciliation
# self-erasing.
```

A subtle and important trap avoided: if the disposition were applied before
diffing, the diff would be empty by construction and the file would validate
itself. Circular-validation bugs are the hardest kind to notice, because
everything passes.

## VI.4 The disposition algebra

Exactly one of four labels per union key:

| Disposition | Meaning | Fixable by filtering? |
|---|---|---|
| `MATCHED_CLEAN` | same link, same construction class | — |
| `MATCHED_DIFF_PROVENANCE` | same link, different construction (rate source, reverse method, weak table) | no — carried to value comparison |
| `PYNA_ONLY` | phantom channel in the graph | **yes** — drop it |
| `MESA_ONLY` | physics in the labels the graph lacks | **no** — must be *added* |

The asymmetry in that last column is the whole point, and the code encodes it:

```python
if doc["tallies"].get("MESA_ONLY", 0) != 0:
    raise ValueError("... the graph is missing MESA physics; re-run the "
                     "reconciliation ... and resolve before building")
```

**A disposition file with MESA_ONLY entries cannot be used.** Dropping channels
is a filter; adding them is not.

Measured tallies [RESULTS 2026-07-09]:

| network | MESA | pyna | CLEAN | DIFF_PROV | MESA_ONLY | PYNA_ONLY |
|---|---|---|---|---|---|---|
| mesa_80 | 607 | 610 | 579 | 28 | **0** | 3 |
| mesa_151 | 1518 | 1522 | 1486 | 32 | **0** | 4 |

**MESA_ONLY = 0 on both networks: the graphs were a strict superset.** The
headline Step-4 risk did not materialise. Note this is a *result*, not a design
— it was entirely possible for it to come out otherwise, and the code path for
that outcome is a hard failure rather than a workaround.

The four dropped PYNA_ONLY channels are all light-nuclide (p+⁹Be breakup, an
n+p+2α → ³He+⁷Li direction MESA carries only one way, and ¹⁶N's β⁻-delayed α in
mesa_151). Dropping them changes mesa_151's weak census 174 → 173.

The 28/32 `MATCHED_DIFF_PROVENANCE` entries after the ordering fix are all
**construction direction-swaps** (§III.4a): 14/16 forward-reverse pairs where
the two REACLIB snapshots disagree about which direction was fitted. Membership
identical, values possibly not — hence carried forward with a stated looser band.

## VI.5 The measured value comparison

Bands stated *before* measuring, with justification (this ordering matters —
a band chosen after seeing the data measures nothing):

| Category | Band | Justification |
|---|---|---|
| REACLIB forward, matched clean | 0.004 dex | same lineage; only a snapshot refit or harness bug can exceed it |
| DB inverse | 0.05 dex | pf provenance differs (MESA winvn ratios vs pyna pf-free v-flag fits) + mass/Q tables |
| weak tabular | 0.1 dex | same tables post-ADR-0003, different interpolants |
| weak reaclib | 0.05 dex | same lineage as forwards |

Results [RESULTS 2026-07-10]:

| Category (net) | channels | median \|Δlog₁₀\| | p95 | max |
|---|---|---|---|---|
| reaclib_forward (80) | 268 | **4.4×10⁻¹⁶** | 0.037 | 3.69 |
| reaclib_forward (151) | 658 | **8.9×10⁻¹⁶** | 2.0×10⁻¹³ | 1.12 |
| db_inverse (80) | 257 | 0.048 | 0.47 | 3.69 |
| db_inverse (151) | 645 | 0.095 | 0.57 | 1.39 |
| construction swaps | 28/32 | 0.0004 / 0.0006 | — | — |
| weak_tabular (80/151) | 38/164 | 0.066 / 0.073 | 0.40/0.33 | 0.52/0.80 |

**Read the first two rows.** Median 10⁻¹⁶ is *bit-identical* — two independent
codebases, two independent parsers, two independent evaluators, agreeing to the
last bit of a float64. That is the strongest possible evidence that the
evaluation pipeline is correct, and it is what licenses treating any *other*
disagreement as meaningful signal rather than noise.

Then read each remaining row as a diagnosis, not a defect:

- **The forward tail** (25 flagged channels, worst ¹³N(p,γ)¹⁴O at −3.7 dex) is
  REACLIB *snapshot refits*, travelling in forward/reverse pairs. All pp/CNO
  sector — no leverage on Si-burning Yₑ.
- **DB inverses** show a signed median growing **+0.005 → +0.013 dex over
  T₉ 1.6 → 7.9**. A *drift with temperature* is the fingerprint of a
  partition-function handling difference (§III.3 — pf grows with T), and it is
  exactly what §III.5 predicted. The κ screen then made the attribution
  dispositive.
- **Construction swaps at 0.0004 dex** prove the two snapshots' fit/derived
  pairs are numerically consistent — only the *labels* differ. Not a defect.
- **Weak tabular** collapses to 0.003 dex at the T₉ = 5 node (§V.5) — interpolation,
  not physics. With one operational consequence: *"the labels contain MESA's
  bilinear values — Step-5 flux work that needs weak λ at off-node states should
  evaluate MESA-side."*
- **Yₑ controllers specifically**: median |Δ| 0.009–0.095 dex, at-node ≤ 0.012.
  The sector that matters most agrees best. That is not luck — LMP tables are
  matched exactly after ADR 0003, so only interpolation remains.

The 135 severe outliers are enumerated in `rate_outliers.yaml`, each either
class-explained or carried as a named open flag. Note the policy line in that
file: *"every entry is either explained in docs/rate-crosscheck.md or carried as
an open flag into Step 5"*. No entry is allowed to be merely tolerated.

## VI.6 Appendix-B as a measurement

Covered mechanistically in §III.7. What belongs here is the *method*, because it
is the template for how this project handles a suspected upstream defect:

1. **Read the source.** Locate the defect statically:
   `rates/private/reaclib_support.f90::compute_rev_ratio` applies the
   phase-space factor only in the single-product branch.
2. **Derive the predicted signature.** |ΔN|·log₁₀(fac·T₉^{3/2}) from (3.4)–(3.5).
3. **Measure it.** 10.0–11.1 dex (|ΔN|=1), 20.6–22.7 (|ΔN|=2), tracking the
   prediction within ≲0.35 dex.
4. **Search for channels the prediction implies but the source paper missed.**
   Found: chapter-8 photodisintegration reverses including c12 → 3α.
5. **Verify against a fixed version.** Install MESA 24.08.1 side-by-side,
   rebuild the probe against it, confirm the channels collapse to ≤ 1.9 dex.
6. **Name what does not fit.** `r_h1_h1_he4_to_he3_he3` sits at 2.7 dex in
   **both** versions ⇒ not a gh-575 channel; recorded as an open flag rather
   than folded into the explained class.
7. **Encode the conclusion as a routing rule**, not a note:
   `assert_appendixb_routing` refuses stock-r23.05.1 values on the 9/11 excluded
   channels.

Step 6 later found the same bug *in the shipped training labels* at T₉ ≳ 5 — but
that is S13's story, and it is downstream of this node existing.

## VI.7 The screening determination

A neat sub-result worth isolating: nobody documented which screening MESA's
`'chugunov'` string selects. It was **determined by measurement** — compare
MESA's per-reaction `scor` against pynucastro's `chugunov_2007` and
`chugunov_2009` on identical plasma states:

| | median ratio | max \|Δlog₁₀\| |
|---|---|---|
| MESA chugunov vs pyna `chugunov_2007` | 0.99999 | **0.0021** |
| MESA chugunov vs pyna `chugunov_2009` | — | 0.52 |

[RESULTS 2026-07-10]. Unambiguous. And the harness itself was validated by a
second, independent identification (MESA `extended` ≡ pyna `screen5` to ~10⁻⁴)
— so the method was shown to work on a case whose answer was already known
before being trusted on the case that mattered.

## VI.8 The Fortran probe: why an external oracle was necessary

`src/mesa_probes/` is a small Fortran driver linked against MESA itself, with
five modes: `dump_net`, `dump_inverse`, `eval_rates`, `eval_weak`,
`eval_screen`. It exists because **the only trustworthy statement about what
MESA computes is what MESA computes.** Reimplementing MESA's rate path in Python
to compare against pynucastro would compare two Python programs.

Two operational details worth copying:

- **The upstream tree stays byte-identical.** `MESA_CACHES_DIR` redirects rate
  cache writes into `data/mesa_cache/`, so the verified Zenodo installation is
  never modified. Reproducibility of the *reference* is itself a requirement.
- **Two MESA versions coexist.** `mesa_probe` (r23.05.1) and `mesa_probe24`
  (24.08.1), the second built specifically to verify the gh-575 fix. Having both
  is what turned "we believe this is the bug" into "the channels collapse when
  the fix is applied".

## VI.8b The probe's five modes, and the grid they run on

```
dump_net      → every reaction in the softwired net: participants, Q, qneu,
                is_weak, weaklib_id, reaclib_fwd_idx, reaclib_rev_idx
dump_inverse  → the inverse-rate construction metadata (the gh-575 screen)
eval_rates    → bare REACLIB λ(T), screening off, T-only
eval_weak     → weaklib λ and raw reaclib λ over a (T9, ρ, Yₑ) grid
eval_screen   → per-reaction screening factor scor over the same grid
```

Note that `dump_net` returns *both* `reaclib_fwd_idx` and `reaclib_rev_idx`, so
`mesa_dump.attribute_source` can classify a MESA reaction as
`reaclib_forward` / `reaclib_reverse` / `weaklib` / `weak_reaclib` / `other`
**from MESA's own bookkeeping** rather than by inference. That is what makes the
`MATCHED_DIFF_PROVENANCE` construction-swap detection possible at all: it
compares MESA's declared construction class against pynucastro's, rather than
guessing from names.

The `other` bucket is designed to be visible: it is flagged and must be
explained, which is how `r_he4_ap_li7` (MESA evaluates it outside its REACLIB
dictionaries, one per net) surfaced.

**The grid** (`crosscheck/grids.py`) is a single source of truth reused by the
cross-check, the κ screen, and the kill-test:

```python
T9_GRID  = (1.6, 2.5, 3.3, 4.0, 5.0, 6.3, 7.9)     # 7
RHO_GRID = (1e7, 1e8, 1e9)                          # 3
YE_GRID  = (0.45, 0.48, 0.498)                      # 3
T9_NSE   = (5.0, 6.3, 7.9)                          # NSE-guaranteed subset
```

Reading it as a design: the T₉ points are **not uniform**. They are the box
edges (1.6, 7.9), the QSE onset band (2.5, 3.3), the kill-test window (4.0, 5.0),
and 6.3 — roughly log-spaced, and **5.0 is a weak-table node** (§V.5). The Yₑ
points bracket the box (0.45, 0.498) with one interior. Sixty-three states per
network is small enough to run a Fortran probe over and large enough to expose
temperature trends — the DB-inverse signed-median drift of §VI.5 needs at least
the seven T points to be visible as a *drift* rather than a scatter.

## VI.8c Reading the comparison statistics honestly

Small points, but they are where a cross-check quietly becomes meaningless.

- **Why dex.** Rates span 75 decades (§II.6b). A relative error is unusable and
  an absolute one absurd; log₁₀ ratio is the only scale on which "agreement"
  means the same thing for a 10¹⁶ rate and a 10⁻⁶⁰ one.
- **Why signed *and* unsigned.** The tables report median |Δlog₁₀| for size and
  a **signed** median for the DB inverses. Only the signed statistic can reveal
  a systematic — |Δ| would show the pf drift as growth in spread, which is
  ambiguous between "systematic" and "noisier". §VI.5's diagnosis depends on the
  sign.
- **Channels vs evals.** `n_channels` counts reactions; `n_evals` counts
  reaction×state pairs. `n_beyond_band` is reported over evals (e.g. "169/1876"),
  so a single bad channel contributes up to 7 evals. Never read a beyond-band
  eval count as a channel count.
- **Why medians and p95 rather than means.** The distribution is bimodal —
  bit-identical bulk plus a snapshot-refit tail. A mean is a number describing
  neither population.
- **The outlier census is complete, not sampled.** All 135 severe channels are
  enumerated with a per-entry disposition. This matters because the alternative —
  "we spot-checked and it looked fine" — cannot support the claim in §VI.9(2)
  that later disagreements are signal.

## VI.9 What the reconciliation licenses downstream

State this precisely, because it is the deliverable:

1. **Membership is identical** (MESA_ONLY = 0, PYNA_ONLY dropped) ⇒ a
   pynucastro-side flux decomposition of a label trajectory is attributing flow
   to reactions that exist in the labels. Without this, every kill-test
   statement would be unfounded.
2. **Forward values are bit-identical** ⇒ disagreements found later are signal.
3. **DB inverses differ systematically, and the mechanism is known** ⇒ the
   pf gate (§III), and the "DB-reverse pf-provenance class" that later accounts
   for **69.4% / 63.6%** of the Step-5 handshake's rate-level departures
   [RESULTS 2026-07-10]. A residual class you have already characterised is not
   a mystery.
4. **Weak tables match exactly per pair; only interpolation differs** ⇒ the
   Yₑ sector is trustworthy, with a stated rule for off-node work.
5. **Screening is pinned** ⇒ `SCREENING_ALLOWED`.
6. **135 outliers are enumerated, classified, and quarantined** ⇒ no flux
   derivation silently includes an unexplained channel.

`provisional_reaction_set=False` plus `disposition_sha256` in every npz is the
machine-readable form of "this build is the reconciled one" — and
`assert_reconciled_build` refuses anything else.

## VI.10 Self-check for S6

1. Why is the directed-key convention (rather than pair keys) what makes a
   forward/reverse counting mismatch impossible? Construct the diff that would
   appear under the pair-key convention.
2. `pyna_inventory` builds with `disposition=None`. Describe the exact bug that
   would result from using `disposition="auto"` there, and why no test would
   catch it.
3. Why is MESA_ONLY ≠ 0 a hard failure while PYNA_ONLY ≠ 0 is routine?
4. The DB-inverse signed median grows with T₉ but the forward median does not.
   From §III.3 alone, predict the sign of that drift and check it against the
   measurement.
5. The screening determination compared against a *known* answer first. Name the
   failure mode that guards against.
6. Suppose a rerun found MESA_ONLY = 2 on mesa_151. Walk through what would have
   to happen, in order, before any flux work could resume.

---

# Part VII — The guards: Tier 1 as executable policy

`fluxes/guards.py` is the tier's conclusions compiled into code that refuses to
run. Four gates, each traceable to a measurement in Parts III–VI:

| Guard | Encodes | From |
|---|---|---|
| `assert_pf_gate` | no raw v-flag reverses, ever | §III.5 — spurious κ floor to 0.8 |
| `assert_appendixb_routing` | gh-575 channels never take stock r23.05.1 values | §III.7 — 10–23 dex |
| `assert_screening_allowed` | `chugunov_2007` or `None`, nothing else | §IV.6/VI.7 — 0.0021 dex determination |
| `assert_reconciled_build` | pinned tabular ordering + `provisional_reaction_set == False` | §V.7/VI.4 — ADR 0003 |

Four properties of this module are worth studying as *design*, independently of
the physics:

1. **They raise, they do not warn.** A warning in a batch job is a log line
   nobody reads. `PfGateError` stops compilation.
2. **They are import-light on purpose.** "No pynucastro import at module scope
   so the guards can gate cheap code paths (npz-only checks) without the heavy
   import." A guard that is expensive to call gets called less.
3. **They are placed at the chokepoint.** *Every* flux/κ entry point goes
   through `compile_network`, and `compile_network` calls all four. There is no
   path into the flux engine that bypasses them — which is a stronger property
   than "all current callers check".
4. **They are tested for their failure behaviour**, not their success behaviour:
   `test_flux_guards.py` is mostly `pytest.raises`. Including
   `test_exported_npz_trips_the_gate`, which asserts that a real artifact in the
   repo still fails the gate.

This is the pattern Tier 0 §VII.4 named ("invariants live in code that refuses,
not in comments"). Tier 1 is where you see it applied to five separate physics
conclusions in one file.

---

# Part VIII — Open prerequisites: what is still not covered

An honest audit of the whole study plan (Tier 0 + Tier 1 + the S7–S16 map),
asking: *what does this project rest on that nothing in the plan explains?*

Three categories. Only the third is a gap.

## VIII.A Deferred by design — covered later, correctly

Not gaps; listed so they are not mistaken for gaps.

| Topic | Where it lands |
|---|---|
| Saha solved as a two/three-unknown root find; cluster chemical potentials u_G | S9 (`qse/`) |
| Jacobian sparsity, BDF, the augmented [Y, Φ] system | S10 (`fluxes/integrate.py`) |
| Reaction-flow decomposition, active sets, cond(S_active) | S14 |
| Null-space projector P, the linear-output-space theorem | S7 / S15 |
| bbq operation, inlists, the rerun campaign | S11 |
| The label pathology (gh-575 *in the shipped labels*) | S13 |

## VIII.B0 ⚠ Corrections to earlier revisions of this file

An audit pass caught errors in the previous revision. Listed because study
material gets memorised, and a wrong number carried forward is worse than one
never written. If you learned any of these, relearn them.

| § | Was | Is |
|---|---|---|
| V.4 | free-proton EC threshold W_thr = 1.804 MeV | **1.293 MeV** — the n–p mass difference *is* the threshold total energy; adding m_ec² double-counts it. Crossing at ρ ≈ 2.4×10⁷, inside the box |
| IV.3 | h_strong ≃ 0.624 Γ_e[ΔZ^{5/3}] | **9/10** Γ_e[ΔZ^{5/3}] — the same 9/10 as the ion-sphere energy two lines above. Cross-checks: Salpeter's 0.205 in cgs, and h/Γ₁₂ = 1.057 against Chugunov's 1.0346 |
| III.7 | gh-575 displaces the reverse by \|ΔN_s\| powers | **\|ΔN_s − e\|** powers, e = 1 iff the tabulated direction has one product. Chapter 8 is off by one power (~10 dex), not two (~21.8). The source branch is `No == 1`, not "three or more participants on a side" |
| 1.4.2 | ×10 in Y_α moves the Si⇌S balance to T₉ ≈ 5.3 | **5.87**; the sensitivity is ≈ +0.8 in T₉ per decade of Y_α |
| 1.4.2 | a forward-rate error "moves the balance point negligibly" | symmetric in the ratio; the real asymmetry is that forward errors are **common-mode** through the DB construction and cancel |
| 1.2.4 | Δ/E₀ ~ 0.1 in hydrogen burning | Δ/E₀ = 4/√τ exactly, so ≈ 0.5–1 there. 0.1 needs τ ≈ 1600, which nothing reaches |
| III.5 | ε = 0.5–1 gives κ ≈ 0.25–0.5 | κ = ε/(2+ε) = **0.20–0.33**; the linearised ε/2 is out of validity at these ε |
| V.4 | λ_EC integrand ~W⁵ | integrand ~W⁴; the **integral** ~μ_e⁵ |
| VIII.C.6 | pair density "probably fine" | n₊ = 1.8 n_net at the hot/thin corner, and the electrons there are **not degenerate** |
| VIII.C.9 | Γ ≈ Γ_e·26^{5/3} of order 10² | order **10** (≈26 at the cold corner) |
| 1.3.2 | ²⁸Si listed as a closed shell | d₅/₂ *sub*-shell closure; and its abundance comes from the α-separation bottleneck, not from magicity |
| 1.3.5 | "is REACLIB stellar or ground-state?" fully open | (3.4) is a relation between *stellar* rates, so `ths8r` must be stellar; only the experimentally-fitted labels remain open |

Two of these (III.7, IV.3) were caught by the same move: **re-deriving a
coefficient the text had already derived one line earlier and not propagated.**
Worth internalising as a proofreading habit for anything in this file.

## VIII.B Closed in this revision

Gaps that existed after the first pass and are now covered:

- **Reciprocity theorem** as a route to detailed balance independent of
  equilibrium (§1.2.6) — without it, using DB reverses at κ = 0.9998 is
  unjustified.
- **The 1/v law**, derived rather than asserted (§1.2.6).
- **Γ/D and level-density criteria** for when Hauser–Feshbach is valid (§1.3.4).
- **LTE for the photon field** — the assumption inside every photodisintegration
  rate (§1.4.4).
- **Triple-α as a sequential process through the Hoyle state**, and the hidden
  equilibrium assumption inside its "three-body" rate (§1.4.4).
- **Numerical range of λ**; why nothing overflows and why 43 sets correctly
  underflow to zero (§II.6b).
- **Partition-function normalisation** (G vs (2J+1)G) and the free low-T
  diagnostic (§III.3).
- **pf spline extrapolation** (`ext='const'`) and the rate-side/Saha-side
  consistency requirement (§III.3).
- **Coulomb corrections to NSE** (Chabrier–Potekhin), why the κ screen sets them
  off, and the matched-pair rule (§III.11).
- **Strong-screening as a free-energy difference**, and why weak/strong limits
  have different powers of Γ (§IV.3).
- **Screening of the weak sector** — the MU/DQ/VS columns, and what "screening
  off" does and does not mean (§IV.9).
- **Pauli blocking of β⁻ decay** as the microphysical cause of the Yₑ ratchet,
  measured as a negative power-law index in the tables (§V.4b).
- **Interpolation-error theory** for the weak tables, predicting both the scale
  and the membership of the measured tail (§V.5b).
- **The probe's modes, the grid rationale, and the comparison statistics**
  (§VI.8b, §VI.8c).

## VIII.C ⚠ Genuine gaps — nothing in the plan covers these

Ordered by how much they could change a project conclusion.

### VIII.C.1 Rate-uncertainty → Yₑ sensitivity propagation

**The gap.** §1.3.3 establishes factor-~2 Hauser–Feshbach and factor-2–10
shell-model weak uncertainties. The project has a Yₑ *physics floor*
(5×10⁻³–1.5×10⁻² per trajectory) anchored on the FFN→LMP difference. But there
is no node that computes **δYₑ / δ ln λ_r** — the sensitivity of the target
observable to each rate.

**Why it matters.** It is the missing denominator for every gate. "Reaction r
carries 40% of ΔYₑ" and "λ_r is known to a factor 2" together determine whether
r deserves emulator accuracy at all. It would also give the kill-test a second,
independent importance measure to cross-check the flux-based active set — one
that is about *physical* importance rather than *numerical* magnitude.

**Cost.** Cheap: the compiled engine already evaluates all rates in batch, so a
one-at-a-time log-perturbation over 607 columns on the trajectory set is a
straightforward run. Nothing new needs building.

### VIII.C.2 Ground-state vs stellar forward rates (the SEF question)

**The gap.** §1.3.5, at the narrower scope established there. The `ths8r`
statistical-model forwards must be stellar rates — (3.4) is a relation between
stellar rates, so the project's mandated `DerivedRate(use_pf=True)` construction
already presupposes it. What is genuinely open is the **experimentally-fitted
subset** (`nac2`, `ks03` and similar), which are laboratory ground-state rates
by construction and to which no SEF is visibly applied anywhere.

**Why it matters.** Those channels carry an unapplied O(1) temperature-dependent
multiplier. It cancels in forward/reverse ratios — so κ, the equilibrium mask,
and the kill-test verdict are all safe — but it does **not** cancel in ΔY
magnitudes or e_nuc. It is precisely the class of error that passes every
consistency test in the repository.

**Cost.** Now mostly mechanical rather than a literature question: tally the
label classes over both networks, weight by flux carried in the box, and check
Rauscher's SEF tables for whatever survives that filter. Hours, not days — and
the expected answer is "negligible exposure", since the α ladder and the Fe-peak
captures are `ths8r` throughout.

### VIII.C.3 Neutrino losses in the flux route (the dropped NU column)

**The gap.** §IV.9. `compile.py` builds only `TableIndex.RATE`; the tabulated
neutrino energy-loss rate (column 6) is discarded, though pynucastro exposes it
as `get_nu_loss`.

**Why it matters.** Invariant #5 requires flux-route vs composition-route e_nuc
agreement to ≤1%, and the trajectory-file `eps_nuc` is *net of neutrino losses*.
The flux-route vs bbq comparison is already logged as UNRESOLVED
[RESULTS 2026-07-10]. A missing loss term is a candidate explanation that
nobody can currently test, because the quantity is not compiled.

**Cost.** Small: one more `tab_*` array and a second bilinear pass.

### VIII.C.4 Imposed (T, ρ) versus thermodynamic feedback

**The gap.** bbq runs one-zone at fixed (T, ρ); the labels are Δ-composition at
imposed thermodynamic state. Tier 0 §IV.2 analyses the **compositional**
reachable manifold beautifully. Nothing analyses the **thermal** one.

**Why it matters.** In a real star ε_nuc heats the zone, T rises,
photodisintegration rates rise steeply (§1.4.3: d ln λ_γ / d ln T ≈ 27), and the
composition responds. Deployment couples the emulator into exactly that loop.
Two specific questions: (i) does the operator-splitting error analysis (§IV.1)
still bound the error when T is *changing* over the step rather than fixed?
(ii) is the Sobol box's (T, ρ) coverage adequate for the trajectories a coupled
run actually traverses, given that self-heating makes T a fast variable near
ignition?

**Cost.** Analysis, not a new measurement. But it deserves a written section,
because it is the assumption that most directly limits the deliverable.

### VIII.C.5 Nuclear mass and Q-value provenance

**The gap.** The DB-inverse band (0.05 dex) is justified partly by
"mass/Q-table provenance" differing between MESA's `winvn` and pynucastro's
tables. No node explains what those tables are, how they differ, or how large
the induced Q differences actually are.

**Why it matters.** Q enters the DB ratio as e^{−Q/kT} with Q/kT up to several
hundred (§II.6). A ΔQ of 10 keV at kT = 0.26 MeV is a 4% rate difference; a
100 keV difference is 47%. **The band's justification is currently qualitative
for a quantity with exponential leverage.** I measured one instance in §III.1 —
pynucastro's internal Q vs the library Q differ by ~1.6×10⁻⁴ MeV — which is
harmless, but that is one channel, not a survey.

**Cost.** Cheap and mechanical: dump Q per reaction from both sides (the probe's
`dump_net` already returns `q`), histogram the difference, convert to dex at box
temperatures.

### VIII.C.6 Electron–positron pairs at the hot, low-density corner

**The gap — and it is not the small one it looks like.** The screening module
computes n_e = ρYₑ/m_u, the **net** electron density. At T₉ = 7.9, kT = 0.68 MeV
against 2m_ec² = 1.02 MeV, so thermal pair production is not negligible. I did
the estimate this item used to defer. Solving finite-temperature charge
neutrality n₋(μ_e) − n₊(μ_e) = ρYₑ/m_u over the box **[derived here]**:

| ρ | Yₑ | T₉ | μ_e (MeV) | n₊/n_net | (n₋+n₊)/n_net |
|---|---|---|---|---|---|
| 10⁷ | 0.498 | 7.9 | 0.161 | **1.81** | **4.62** |
| 10⁷ | 0.498 | 5.0 | 0.412 | 0.20 | 1.40 |
| 10⁸ | 0.500 | 7.9 | 1.210 | 0.041 | 1.08 |
| 10⁹ | 0.450 | 7.9 | 3.598 | 3×10⁻⁴ | 1.000 |

**At the hot, thin corner the positrons outnumber the net electrons**, and the
total charged-lepton density is 4.6× the number the code uses. It is nowhere
near "below a percent".

**Why it matters.** Two things, and the second is larger than the one this item
was originally about:

1. Pairs add to the *polarisable* lepton density while leaving Yₑ unchanged, so
   Γ_e keyed on net n_e is low by 4.62^{1/3} ≈ 1.66× there. Bounded in
   consequence: Γ(Si–Si) at that corner is only 0.40, so h is small and the
   enhancement is ~1.1× either way. The rate error is real but not large.
2. **μ_e = 0.16 MeV < m_ec² means the electrons there are not degenerate at
   all.** That undercuts more than the screening call: §V.4's cold-degenerate
   E_F table, the μ_e⁵ scaling, and `chugunov_2007`'s rigid-background premise
   all assume degeneracy. The corner is outside the design regime of three
   separate pieces of machinery at once, and §V.4 now says so.

**Status.** Estimate done; the item is no longer "probably fine, go check". What
remains is a *decision*: either state the hot-thin corner as an explicit validity
boundary on the screening and weak prescriptions, or exclude it from the
sampling box. It also bears on the EOS and on the neutrino losses. This is the
cleanest illustration in the whole list of why "probably fine" at a box corner
deserves the ten minutes.

### VIII.C.7 Network-reduction and reaction-importance prior art

**The gap.** Tier 0 §VI.5 surveys prior art in *ML* acceleration. The kill-test
is not an ML method — it is a reaction-importance / network-reduction study, a
field with decades of literature (integrated reaction flows, principal-component
and directed-relation-graph reduction in combustion, adaptive networks in
astrophysics). None of it is surveyed.

**Why it matters.** Two risks. First, novelty: the `novelty-checker` sweeps
arXiv for ML-emulator work; a reduction-methods claim could be anticipated in a
literature nobody is sweeping. Second, method: combustion chemistry solved
"which reactions matter, adaptively" long ago, and their importance measures
(DRG, DRGEP, computational singular perturbation) are directly analogous to the
κ/active-set machinery. Reinventing them is a waste; citing them is free.

### VIII.C.8 Isomers, and what a ground-state-only network omits

**The gap.** `canonical.py` deliberately does not map `al26-1` / `al26-2`, on
the grounds that they are absent from both networks. True, but the *physics*
consequence is unstated: a ground-state-only treatment assumes isomeric states
are either in thermal equilibrium with the ground state or irrelevant.

**Why it matters.** Probably genuinely irrelevant here (²⁶Al matters for
galactic γ-ray astronomy, not Si-burning Yₑ, and at kT ≈ 0.3 MeV thermal
coupling is fast). But it is an assumption, currently unwritten, and the
fail-loud whitelist means an isomer appearing in a future network raises rather
than silently mis-maps — so the code is safe and only the *documentation* is
missing.

### VIII.C.9 Coulomb-corrected NSE, quantified in-box

**The gap.** §III.11 explains *why* `use_coulomb_corr=False` is right for the κ
screen. Nobody has measured **how different the Coulomb-corrected NSE
composition is** at box conditions, where Γ_e Z^{5/3} is large for Fe-peak Z.

**Why it matters.** The κ screen's choice is correct regardless. But S9's QSE
work, and any comparison of a computed NSE state against a MESA/bbq attractor,
needs to know whether the ideal-gas NSE is the right reference — and at
ρ = 10⁹ with Z ≈ 26, Γ = Γ_e·26^{5/3} ≈ 0.045 × 228 ≈ **10** at T₉ = 4, rising
to ≈ 26 at the box's cold corner **[derived here]**. Order 10, not 10² — and
consistent with §IV.4's 0.4–25 range rather than in tension with it. Still
firmly out of the weak-coupling regime, so the item stands; it is the
*magnitude* of the claim that needed correcting, not the conclusion.

**Cost.** Two calls to `get_comp_nse` with the flag flipped, at a few box
corners. Minutes.

### VIII.C.10 Gate-design statistics

**The gap.** Gates are stated as point thresholds on medians/p90s over 63-state
grids or 30k subsamples, with no statement of sampling uncertainty. §VI.8c
covers how to *read* the comparison statistics; nothing covers how to *choose*
the sample size or express confidence.

**Why it matters.** Lowest priority of the ten: most gates here are separated
from their floors by many orders of magnitude (κ 2.6×10⁻¹² against a 0.1
threshold), so sampling noise is irrelevant. It matters only for the near-run
gates — the 2× size-transfer falsifier and the 3× Sobol trigger, both of which
compare two measured distributions and could plausibly land near their
thresholds.

## VIII.D The habit that finds these: common-mode blindness

Every consistency test in this tier is a test of **mutual** consistency —
forward against reverse, pynucastro against MESA, vectorised against scalar,
rate side against equilibrium side. That is enormously powerful: it is how the
v-flag κ floor and gh-575 were both caught with no ground truth at all.

It is also, by construction, blind to **common-mode** error: anything identical
on both sides of the comparison.

Look at what that predicts, then check it against the list:

| Gap | The quantity that is identical on both sides |
|---|---|
| §VIII.C.2 (SEF) | an unapplied stellar enhancement cancels in every ratio |
| §VIII.C.3 (NU column) | never appears in any rate comparison |
| §VIII.C.4 (imposed T, ρ) | identical on both sides of every handshake |
| §VIII.E.2 (Q(T)) | the *same constant Q* on both sides of the ≤1% gate |
| §VIII.E.3 (no third solver) | both sides read REACLIB |

Five of the highest-priority items, one generating principle.

> **Ask of any green test: what would still be wrong if it passed?**

## VIII.E ⚠⚠ Second-pass audit: an entire missing tier

The §VIII.C audit searched the *physics* the code implements. A second pass
searching the **project's own specification documents** against the study map
turns up something larger than any individual gap.

### VIII.E.1 The model side has no study node at all

`docs/reports/consolidated-gnn-architecture.md` specifies the emulator as
**Components A–D**. Cross-referencing against the study map (S0–S16):

| Component | Specified content | Study node |
|---|---|---|
| **A** — backbone | heterogeneous bipartite graph with **three** edge types (I→R, R→I signed, I→I); per-reaction-type message functions; GATv2 attention; latent width h = 128; encode–process–decode; **continuous (Z,N) embedding** as the size-transfer mechanism; depth K ≈ ⌈radius⌉+2 = 5; hypergraph convolution rejected with a switch rule; the **four added physics channels**; signed-log with NuGNN's shift trick C ≈ 17; learned flux preprocessor | **none** |
| **B** — heads | Target A/B · **S15** ✓; **hybrid equilibrium mask = Guidry prior + learned L0 hard-concrete gate**; energy head e_nuc = ΣQⱼ(T)φⱼ; **neutrino head ε_ν = Σ⟨E_ν⟩ⱼφⱼ** | **partial** (S15 covers the target choice only) |
| **C** — temporal head | **Δt as global conditioning on a stiffness-aware log grid, ONE model spanning 10⁻⁶–10² s** (vs the NNN's nine); **Ono & Sugimura 2026 timescale-rescaled update** as rollout governor; its **commutation with the conservation map is an open interaction** | **none** |
| **D** — training | **pushforward/unrolled loss through K ≥ 2 steps** as the primary stability lever; **GNS noise injection restricted to non-equilibrated channels**; **worst-case tail term (p90/p99 or CVaR)**; Fe-peak up-weighting; **deep ensembles → OOD flag → fallback-to-solver gate** | **none** |

**And `docs/architecture/` — which `docs/CLAUDE.md` names as the living spec —
is empty** (only `.gitkeep`). The four reports in `docs/reports/` are read-only
audit artifacts by Rule 5. So the model side is specified only in documents that
must not be edited, and studied nowhere.

This is consistent with Phase 0 being pre-training, and it is not a defect in
the *project*. But the question asked was what is prerequisite and unexplored,
and the answer is: **roughly a whole tier.** Sketching it in the map's own idiom:

```
═══════════════════════════════════════════════════════════════════════════════════
 TIER 4 — THE EMULATOR                    "the model, its conditioning, its training"
═══════════════════════════════════════════════════════════════════════════════════

   ┌─────────────────────────────┐   ┌─────────────────────────────┐
   │ S17 HETEROGENEOUS BACKBONE  │   │ S18 THE MASK AS A LEARNED   │
   │ 3 edge types, per-type msg  │   │     GATE                    │
   │ fns, GATv2, K = radius + 2, │   │ L0 / hard-concrete, condi-  │
   │ (Z,N) embedding = transfer  │   │ tional computation, why the │
   │ the 4 physics channels      │   │ Guidry prior is a prior     │
   └──────────────┬──────────────┘   └──────────────┬──────────────┘
                  ▼                                 ▼
   ┌─────────────────────────────┐   ┌─────────────────────────────┐
   │ S19 TIME CONDITIONING       │   │ S20 ROLLOUT STABILITY       │
   │ one model over 8 decades of │   │ pushforward vs noise inject-│
   │ Δt, log-Δt grid, latent-ODE │   │ ion in a STIFF system;      │
   │ alternative                 │   │ governor ⟷ conservation map  │
   └──────────────┬──────────────┘   └──────────────┬──────────────┘
                  ▼                                 ▼
   ┌─────────────────────────────┐   ┌─────────────────────────────┐
   │ S21 LOSSES UNDER TAIL RISK  │   │ S22 UQ, OOD, AND THE        │
   │ CVaR / p99, multi-objective,│   │     FALLBACK GATE           │
   │ Fe-peak weighting           │   │ deep ensembles, calibration,│
   │                             │   │ hand-back-to-solver         │
   └─────────────────────────────┘   └─────────────────────────────┘
```

Six nodes. Note that **four of the eight open Phase-0 checklist rows (2, 3, 4,
15) are Tier-4 measurements**, including row 15's governor design — whose stated
premise ("a separated fast sector") was **retired by measurement on 2026-07-12**.
A design whose premise is now known false, with no study node, is the highest-
leverage gap in this list.

Also note row 12 — *"the pass/fail gate — biggest single lever"* (the Yₑ-residual
accumulation slope). Tier 0 §IV.3 derives the accumulation *trichotomy*, so the
theory is covered; what is not covered is the **measurement design** — how many
steps, on which trajectories, with what estimator, to distinguish slope 1 from
slope 0.5 with confidence. A two-orders-of-magnitude gate hinges on it.

### VIII.E.2 Q(T) — specified, unimplemented, unmeasurable by the current gate

Fully worked in §III.12. Summary: the energy head is specified with Qⱼ(T); it is
not implemented; the ≤1% invariant-#5 gate uses identical constant Q on both
sides and therefore cannot detect its absence; and the per-channel correction
reaches **−19.2% on ⁴⁰Ca(α,γ)⁴⁴Ti at T₉ = 7.9** and −8.4% in the QSE window.
Needs one convention decision (does MESA/bbq's EOS carry nuclear excitation
energy?) and a three-line implementation using splines that already exist.

### VIII.E.3 Solver-independent ground truth (SkyNet, WinNet)

The PhD-plan report calls for bbq/MESA as primary "cross-checked against SkyNet
and WinNet for solver-independent validation". Nothing in the study map, the
code, or `RESULTS.md` touches either.

**Why it matters, sharply.** §1.3.3 and §VIII.C.2 establish that this project can
only make *fidelity-to-MESA* claims. S6 verified MESA against pynucastro — but
pynucastro is a *rate library*, not an independent integrator, and both sides
read REACLIB. **There is currently no independent check of the integrated
dynamics at all.** That matters most where MESA is known to be wrong: the
gh-575-displaced label attractors (S13). A third solver is the only instrument
that distinguishes "the labels are pathological" from "our reading of the labels
is pathological".

### VIII.E.4 Determinism, and the float32/float64 boundary

Two connected items, both absent.

**Determinism.** The conservation gate asserts column drifts of *exactly* 0.0 and
bounds at 10⁻¹²–10⁻¹³. Floating-point reductions are not associative, so a
threaded or GPU reduction's result depends on thread count and scheduling. The
repo already carries BLAS thread-pinning (commit `1cb6f47`), which suggests the
issue has been felt. Nothing states the contract: **is the conservation gate
reproducible bit-for-bit across thread counts and devices, and if not, what is
the guaranteed bound?**

**Precision boundary.** The spec says inference in float32 with a float64 cast
for the Xₜ₊Δₜ update, and separately flags as load-bearing that "whether even
asinh of a genuinely tiny post-cancellation net flux loses precision — is
unproven". Tier 0 §V.4 covers floating point generically; §II.6b here measures
75 decades of λ. Nobody has put the two together: **float32 has ~7 decimal
digits and a ~10⁻³⁸ normal floor; a post-cancellation net flux at κ = 10⁻⁶ of a
gross flux is exactly the quantity that boundary destroys.** This is a
computable, decidable question and it gates the architecture's precision plan.

### VIII.E.5 Gradients through the conservation map

Target A decodes φ then applies fixed ν; Target B applies the projector
P = I − Cᵀ(CCᵀ)⁻¹C. Both are fixed linear maps, so the backward pass is
multiplication by νᵀ and Pᵀ = P respectively. Consequences nobody has written
down:

- **P annihilates gradient in the constrained directions exactly.** Any loss
  component that depends on the violating part of dY produces *zero* gradient —
  which is the point, but it means the network receives no signal about
  three directions of its output space, and cond(CCᵀ) = 3.9×10⁴ / 1.0×10⁵
  (measured, RESULTS.md 2026-07-08) says those directions are not equally
  conditioned.
- **ν has nullity 1** (measured, same row). So for Target A there is a
  one-dimensional family of φ producing identical dY: the flux head is
  *unidentifiable* along it, and nothing in the loss selects a member. Whether
  that harms training, or merely leaves a harmless gauge freedom, is unexamined —
  and it interacts with the flux-magnitude regularisation the mask implies.

Neither is exotic ML; both are two-line linear algebra on matrices already
exported. Genuinely prerequisite, genuinely absent.

### VIII.E.6 The deployment coupling contract

§VIII.C.4 raised imposed (T, ρ). The PhD-plan report is broader, listing
"coupling-specific gates added by audit": energy-generation error feeding back
into the structure solve, behaviour across the NSE transition, composition
coupling in convective zones, and Sobol→real-track transfer. Only the last has a
node (S1/§III.9, and checklist row 13).

**The one to name specifically is the NSE transition.** MESA switches to an NSE
solver above some temperature; the emulator would have to either reproduce that
switch or be handed off across it. There is no node for the handoff contract,
and S13's finding — that the labels sit at bug-displaced pseudo-equilibria at
T₉ ≳ 5 — is precisely a statement about what happens near that switch.

### VIII.E.7 Residual sourcing gaps in the motivation chain

Three open checklist items are *sourcing* rather than measurement, and all three
sit in the chain Tier 0 Part I uses to justify the project:

- **Farmer 2016's "30%/10%"** — is it η = 1−2Yₑ or relative Yₑ? Tier 0 §I.2 and
  docs/CLAUDE.md both carry this as explicitly unconfirmed. It is an
  interpretation of the *observational* leverage of Yₑ, i.e. the number that says
  why the project matters.
- **⟨E_ν⟩ per reaction** for the neutrino head. Distinct from §VIII.C.3's dropped
  NU column: that is a tabulated *loss rate*, this is a *mean energy per capture*
  needed for ε_ν = Σ⟨E_ν⟩ⱼφⱼ. Open since Tier 0 §0.4.3.
- **Which Yₑ-controllers each network contains**, specifically the neutron-rich
  β-decay partners ⁶¹Fe and ⁶¹,⁶³Co. §V.10 gives the census by count; the
  per-nuclide membership question for those three is still open in the
  checklist.

## VIII.F Summary: priority across both audit passes

Sixteen open items across §VIII.C and §VIII.E. Ranked by (leverage on a project
conclusion) ÷ (cost to close):

**Close now — hours each, machinery already exists**

| # | Item | Why first |
|---|---|---|
| 1 | **§VIII.E.2 · Q(T)** | Specified, unimplemented, and the ≤1% gate structurally cannot see it while a core α-ladder channel carries −19%. `spline.derivative()` plus the existing `pf_matrix`. |
| 2 | **§VIII.C.1 · rate-uncertainty → Yₑ sensitivity** | Supplies the missing *physical*-importance axis for the kill-test; the batch engine already evaluates every rate. |
| 3 | **§VIII.E.4 · float32 vs post-cancellation flux** | Decidable arithmetic, and it gates the architecture's stated precision plan. |
| 4 | **§VIII.E.5 · gradients through ν and P** | Two-line linear algebra on already-exported matrices; ν's nullity-1 gauge freedom is an unexamined identifiability question in the primary target. |
| 5 | **§VIII.C.2 · the SEF question, at its narrowed scope** | `ths8r` forwards must be stellar (3.4 presupposes it); only the experimentally-fitted label classes are exposed. Tally them, weight by flux, check Rauscher's tables for the survivors. Closes a common-mode hazard invisible to every existing test. |

**Design work with no premise — highest leverage, needs thought not compute**

| # | Item | Why |
|---|---|---|
| 6 | **§VIII.E.1 · the Tier-4 gap, and row 15 first** | The rollout governor's premise (a separated fast sector) was retired by measurement on 2026-07-12. A design with a falsified premise and no study node. |
| 7 | **§VIII.E.1 · row 12 measurement design** | The accumulation slope moves the operative gate by 100×; the theory is covered, the estimator design is not. |
| 8 | **§VIII.C.4 + §VIII.E.6 · the coupling contract** | Bounds what the finished emulator can claim; the NSE-transition handoff is unspecified and is exactly where S13 found the labels pathological. |

**Standing verification debt**

| # | Item |
|---|---|
| 9 | §VIII.E.3 · solver-independent ground truth (SkyNet/WinNet) — currently **no** independent check of the integrated dynamics exists |
| 10 | §VIII.E.4 · determinism contract across thread counts/devices |
| 11 | §VIII.C.5 · mass/Q-table provenance survey |
| 12 | §VIII.E.7 · Farmer 2016 interpretation · ⟨E_ν⟩ · the ⁶¹Fe/⁶¹,⁶³Co membership question |
| 13–16 | §VIII.C.7 reduction prior art · §VIII.C.8 isomers · §VIII.C.9 Coulomb-NSE in-box · §VIII.C.10 gate statistics |

**Promoted out of that bucket: §VIII.C.6 (e± pairs).** It was filed as a
probably-fine corner check. The estimate is now done and it is not fine:
at T₉ = 7.9, ρ = 10⁷ the positrons outnumber the net electrons and the
electrons are non-degenerate, so three separate prescriptions — `chugunov_2007`'s
rigid background, §V.4's cold-degenerate E_F, and the μ_e⁵ scaling — are all
outside their design regime at that corner simultaneously. What remains is a
*decision* (declare a validity boundary, or trim the box), not a measurement, so
it belongs with items 6–8 rather than here.

**The pattern worth naming.** Items 1, 3, 5 and 9 are all the same shape: a
quantity or convention that is *identical on both sides* of every check the
project runs. §VIII.D's habit — *ask of any green test what would still be wrong
if it passed* — is what surfaced all four.

---

# Where Tier 1 hands off

## What Tier 1 upgraded

| Statement, before | Now derived |
|---|---|
| "λ comes from REACLIB" | λ = Σ_sets exp(a·basis) where a₂ **is** the Gamow exponent −4.2487(Z₁²Z₂²μ)^{1/3} and a₆ = −2/3 is the saddle-point prefactor (§II.1, §II.3) |
| "reverse rates come from detailed balance" | six explicit factors (3.4); the v-flag construction carries five and structurally cannot carry the sixth (§III.5) |
| "use `DerivedRate(use_pf=True)`" | pf corrections reach 0.22×–4.5×, and near equilibrium a factor ε in f⁻ appears as κ ≈ ε/2 — hence a floor to 0.8 (§III.5) |
| "gh-575 is a phase-space bug" | $\|\Delta N_s - e\|$ powers of $\mathrm{fac}\cdot T_9^{3/2}$ = 10.3–11.3 dex each, with $e = 1$ iff the tabulated direction has one product — so chapter 8 is off by **one** power, not two, matching measurement to ≲0.35 dex (§III.7) |
| "screening uses chugunov_2007" | Γ ≈ 0.4–9 for Si–Si across the box ⇒ intermediate coupling; enhancements 1.1×–3.3×; A₃ = √3 − A₁/√A₂ *is* the Debye–Hückel boundary condition (§IV.3–IV.5) |
| "screened κ has an offset at NSE" | κ = \|tanh(Δh/2)\|, exact to 1.4×10⁻¹¹; median 7.361×10⁻² reproduces the RESULTS row (§IV.7) |
| "weak rates are tabulated in (T, ρYₑ)" | λ_EC ∝ μ_e⁵ ∝ (ρYₑ)^{5/3} past threshold; E_F = 1.02 → 3.98 MeV across the box brackets the free-proton threshold (§V.4) |
| "the tables are coarse" | 1 dex per ρYₑ cell; T₉ = 5 is a node, which is why the cross-check median collapses there to 0.003 dex (§V.5) |
| "the rate sets are reconciled" | MESA_ONLY = 0, forwards bit-identical at the median, every residual class named and bounded (§VI) |

## Threads that carry forward

- **To S7 (stoichiometry):** column identity is the invariant the v-flag
  replacement is built around; `derived_from_inverse`, `weak_mask`, `weak_type`,
  `chapter`, and `Q` all come out of this tier and become columns of the ν
  export.
- **To S8 (fluxes and cancellation):** R_j = prefactor·ρ^{densexp}·ΠY·λ (1.2) is
  the definition of gross flux; the pair map, f⁺/f⁻, and κ are all built on the
  forward/reverse structure derived in §III; and κ's two readings — DB test
  (§III.6) and condition number (§V.1 of Tier 0) — meet here.
- **To S9 (NSE/QSE):** the same partition functions, spins, and masses feed both
  the rate side (§III.3) and the Saha side (`qse/coeffs.py`); their consistency
  is what makes κ-at-NSE a meaningful test at all. §1.4.2's crossover table is
  the mechanism of QSE onset.
- **To S13 (the label pathology):** §III.7's derivation is the tool that later
  identifies gh-575 *in the shipped labels*.
- **To S14/S15 (kill-test and target):** the active-set threshold κ > 0.1 is
  evaluated on **unscreened** κ from **pf-corrected** reverses. Both
  qualifications are Tier-1 results, and either one violated invalidates the
  verdict.

## The three ideas to carry, if you carry nothing else

1. **The reverse rate is where the physics and the bugs both live.** Forwards
   are bit-identical between two independent codes; every consequential
   disagreement in this project — pf, gh-575, snapshot construction swaps — is
   about a reverse. And §1.4.2 shows why: near equilibrium the reverse *is* the
   answer.
2. **A multiplicative error ε in f⁻ becomes κ ≈ ε/2 at equilibrium.** One line
   of algebra that unifies the v-flag floor (§III.5), the screening offset
   (§IV.7), and the κ-as-condition-number reading of Tier 0 §V.1. If you can
   write this down cold, most of Tier 1 reconstructs itself.
3. **Every threshold in this tier sits just above a measured floor.** 5×10⁻¹²
   (above 1.3×10⁻¹² fp association), 0.004 dex (above bit-identical), 0.05 dex
   (above the pf drift), κ < 10⁻⁹ (above 2.6×10⁻¹²). None is a round number
   chosen for comfort. When you meet a new gate, ask what floor it sits above —
   and if there isn't one, that is the finding.

## And one habit, from Part VIII

The tier's tests are all **mutual**-consistency tests, which is their strength
(no ground truth needed) and their blind spot (common-mode error survives them).
Five of the highest-priority open items in §VIII.F are common-mode — worked in
§VIII.D.

> **Ask of any green test: what would still be wrong if it passed?**

---

**Next:** Tier 2 — **S7** (ν, the constraint matrix C, the null-space
projector) and **S8** (f⁺, f⁻, φ = f⁺ − f⁻, and κ as a condition number).
