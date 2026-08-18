# Tier 3 — Astrophysics and the Verdict

**Complete deep dive: the star this project is about, the data that came out of
it, and the decision Phase 0 was built to make.**

Tier 2 ended with instruments. ν and C were exported and their null spaces
measured; κ was defined four ways and computed; the Saha solver was validated
against an independent implementation; a reference integrator was built that
produces (Φ, ΔY = νΦ) pairs by construction. Every one of those exists to answer
one question, and Tier 3 is where the question gets asked of real data and
answered.

Six nodes:

- **S11** — bbq and MESA as *operated*: what a one-zone burner is, what
  hydrostatic mode does, how the shipped labels were generated, and how the
  209-run-per-network rerun campaign that supplies the verdict distribution was
  designed, executed and validated.
- **S12** — the trajectory files: format, the eps_nuc convention that had to be
  *pinned by measurement* rather than read off a header, and the "stall" that
  turned out to be an attractor arrival.
- **S13** — silicon burning on actual burning histories, and **the label
  pathology**: the shipped training labels carry a MESA bug that displaces the
  equilibrium the network relaxes to, at T₉ ≳ 5, and therefore gets Yₑ itself
  wrong there. This is the tier's headline result and its most consequential.
- **S14** — the kill-test: the active set, cond(S_active), coverage, spread,
  churn, timescale separation, measured on two distributions that turn out to be
  different worlds.
- **S15** — the ML target decided: Target A, full-width, with the equilibrium
  mask measured empty; why the decision is *not* about expressivity; and what
  the split verdict costs.
- **S16** — the baseline: what the NNN actually is, what it achieves, what
  "beating it" has to mean, and the evaluation protocol that claim requires.

Plus the front part the map does not show: **Part 0**, the astrophysics. Tier 0
Part I gave the motivation chain as a sequence of claims to defend; Tier 2 Part 0
gave the equilibrium theory the algebra needs. This part gives the *whole
astrophysical setting*, derived: the star as a thermodynamic engine, the burning
staircase and why it accelerates, silicon burning in its hydrostatic and
explosive forms, the collapse in detail, the observables at the far end, and the
computational situation that makes emulation worth attempting. It is long on
purpose. Everything in Tiers 0–2 is *for* this, and none of it is derivable from
the code.

---

## Status of this document

**Personal study material, not project spec.** Deliberately written without
reference to `docs/` — everything is derived from first principles or read off
the business code, configs, notebooks, and tests.

- Textbook physics and derivations here are **mine to check**, not citable
  project output. Where I compute something myself it is tagged
  **[derived here]**: reproducible from the numbers given, but not a
  `RESULTS.md` row.
- Measured project numbers quoted here originate in `RESULTS.md` with script +
  commit + data provenance, tagged **[RESULTS]**. This file is **not** their
  source of truth; if a number here disagrees with `RESULTS.md`, `RESULTS.md`
  wins.
- **Bibliographic details were verified in the 2026-08-18 literature audit**
  (the former **[sourced — verify]** tags are resolved). Every
  externally-attributable claim now carries an inline author-year citation
  resolved in the **References** section at the end; ~700 claims were
  inventoried across twelve chunks, every worked number was recomputed in
  float64, and every `[RESULTS]` quotation was cross-checked against
  `RESULTS.md`. Corrections found by the audit were applied in place, with an
  inline "(corrected in the 2026-08-18 audit)" note wherever the physics content
  itself changed. The headline ones: MESA has **no** NSE switch (§0.3.6, T-21 —
  the "5–7 GK handoff" is a KEPLER/hydro-code property); MESA's own
  `op_split_burn` route zeroes the ∂ε_nuc/∂T, ∂ρ terms, so T-25's derivatives are
  route-dependent (§0.8.6, §I.2b); the coherent-scattering formula and the
  Bethe-era trapped lepton fraction (0.35 → 0.29–0.30, homologous core
  0.7 → 0.5 M⊙) in §0.5.4–0.5.5; the τ_ign "prediction" in §0.2.1 was a
  bookkeeping identity; the two-group QSE picture is Woosley, Arnett & Clayton
  1973's, not BCF68's, and the ⁴⁵Sc(p,γ)⁴⁶Ti bottleneck is WAC73/HT96's, not the
  NNN paper's (§0.3.2); the NNN's architecture is 12/9 layers of 1024/2048, not
  the code's 4-layer default, and its author list is Grichener, Renzo,
  Kerzendorf et al. (§VI.1); the NuGNN column of the novelty table understated
  that paper (§V.3, §VI.4); Ovadia et al. 2019 was cited against its own
  conclusion (§X.5, T-37); the binomial in §IX.3.1 (5% is ≥ 63/108, not ≥ 60);
  and the "≈75%" premise of T-41 is sourced (WAC73 via HT96) but for a different
  quantity. Pre-arXiv classics were verified only bibliographically this session
  (ADS abstract pages were unreachable; CrossRef/INSPIRE and cached
  bibliographies were used) — their content is marked ASSUMED-with-attribution
  where no cached secondary states it. Part 0 leans on the CCSN and
  nucleosynthesis literature more heavily than any earlier tier; the References
  provenance notes say, entry by entry, what was actually opened.
- Astrophysical numbers that are *representative of a model class* rather than
  measured — pre-supernova core masses, explosion energies, ⁵⁶Ni yields — are
  tagged **[typical]**. They vary by progenitor, code and mechanism, and quoting
  them as if they were constants is the single easiest way to write something
  false in this subject.

**Maths formatting.** Every *equation* — anything with its own line — is LaTeX in
a `$$ … $$` block with the delimiters on their own lines. Short conditions
embedded in a sentence are inline `$…$`. Symbols named in running prose stay in
unicode; maths is never set in `monospace`, which is reserved for code
identifiers, filenames and literal values.

**Cross-references.** §0.x, §I.x, §V.x with no other qualifier point into
[`tier0.md`](tier0.md); §II.x–§VII.x with an (S2)…(S6) label into
[`tier1.md`](tier1.md); §0.x/§I.x–§VII.x with a (S7)…(S10) label into
[`tier2.md`](tier2.md). Within *this* file, Part 0 sections are §0.x and node
sections are §I.x (S11), §II.x (S12), §III.x (S13), §IV.x (S14), §V.x (S15),
§VI.x (S16).

**One convention carried forward from Tier 2**, because Part IV depends on it:

| symbol | meaning | units |
|---|---|---|
| R_j, f⁺_j | **gross** rate of reaction j, one direction | mol g⁻¹ s⁻¹ |
| φ_j | **net instantaneous** flux, f⁺_j − f⁻_j | mol g⁻¹ s⁻¹ |
| Φ_j | **time-integrated** flux over a label step, ∫R_j dt | mol g⁻¹ |

κ_j = |φ_j| / (f⁺_j + f⁻_j) is the cancellation ratio, evaluated in the
**unscreened** convention for every equilibrium statement (`CLAUDE.md`'s two-κ
rule).

---

## How to study each node

```
  ① DERIVE      pen-and-paper: get the equation from physics before reading code
  ② READ        the module, top-to-bottom; its docstring states the contract
  ③ ORACLE      the test file — it encodes what "correct" means, numerically
  ④ SEE         the notebook figure — the measured behaviour on real data
```

Tier 3 is where this loop changes character. In Tiers 0–2 the oracle was usually
an exact algebraic statement or an independent implementation. Here there are
three nodes (**S11**, **S12**, **S13**) whose "oracle" is *an experiment on
external software you do not control*: run bbq under two MESA versions and see
which one reproduces the shipped labels. The epistemics of that are different
and worth naming — §III.6 does it explicitly.

The other change: **this tier's headline results are all negative or
qualified.** The QSE single-cluster plateau is not confirmed, the maskable set is
empty, the timescale separation the design assumed does not exist, and the
training labels are wrong above 5 GK. Not one of those was the expected answer.
A tier that returns four surprises either has broken instruments or is measuring
something real; §IV.8 is the argument that it is the latter, and it is the
argument you should be most sceptical of.

---

## Contents

| Part | Covers |
|---|---|
| [**0** — The astrophysics](#part-0--the-astrophysics-this-project-is-for) | The star as a self-gravitating engine (virial theorem, negative heat capacity, the ρ–T plane); the burning staircase derived (ignition temperatures, energy per gram, the T⁹ neutrino clock, why Si burning lasts a day); silicon burning hydrostatic *and* explosive, α-rich freeze-out; the onion, the iron core, compactness; **core collapse derived end to end** (Γ₁ < 4/3, trapping, the homologous core, why the prompt shock fails, the delayed mechanism, the mass cut); the observable end (⁵⁶Ni light curves, isotopic ratios, GCE, remnants); where Yₑ comes from; the computational setting and the emulation landscape; **the astrophysics → gate mapping table** |
| [**I** (S11) — bbq / MESA operation](#part-i-s11--bbq-and-mesa-as-operated) | What a one-zone burner is and what it deliberately is not; MESA's network solver; bbq's four modes and why only one of them can produce a trajectory; the inlist as a config surface; the shipped-label pipeline reconstructed; the rerun campaign (ADR 0005) — design, families, cadence, execution, validation |
| [**II** (S12) — Trajectories & eps_nuc](#part-ii-s12--trajectories-and-the-eps_nuc-pin) | The file format; the composition route to energy derived from mass excesses; **the convention pin as a hypothesis test over 2 × 2 × 2 candidates**; the stall, reinterpreted twice; `terminal` vs `first_quiet` and why the default moved |
| [**III** (S13) — Si burning & the label pathology](#part-iii-s13--silicon-burning-on-real-histories-and-the-label-pathology) | What a real trajectory looks like; the NSE census; **the gh-575 mechanism traced from a Fortran branch to a displaced attractor to a wrong Yₑ**; the witness experiment; the dt-freeze signature; the benchmark-vs-physics fork; what a negative result about your own dataset obliges you to do |
| [**IV** (S14) — The kill-test](#part-iv-s14--the-kill-test) | The question as a matrix question; the instruments and the strata; **the two distributions**; every gate, measured; the split verdict and the 1/κ amplification it names; the statistics the verdict does not carry (R-08); what would have changed the answer |
| [**V** (S15) — The ML target](#part-v-s15--the-ml-target-decided) | Target A/B restated post-verdict; why the decision is about conditioning and supervision, not expressivity; the empty mask and what Component B becomes; Φ-supervision feasibility and the identifiability cost; the NuGNN failure mode as a design constraint |
| [**VI** (S16) — The baseline](#part-vi-s16--the-baseline-you-are-trying-to-beat) | The NNN as an object: architecture, training set, loss, the nine-model structure; what it achieves and where it fails; the reproduction; NuGNN; **what "beating it" must mean and the evaluation protocol that requires** |
| [**VII** — Handoff](#part-vii--what-tier-3-hands-forward) | What Phase 0 established, what it retired, the four escalations, and the state Tier 4 inherits |
| [**VIII** — The open register](#part-viii--the-open-register) | T-01 … T-32, each pointing at the section that derives it, plus a ranked top eight and the cross-tier links |
| [**IX** — Prerequisites outside the map](#part-ix--prerequisites-outside-the-map-a-cross-tier-audit) | **The cross-tier boundary audit**: ten areas with no study node anywhere in Tiers 0–3 — mixing, the NSE transition, progenitor diversity, what computes explodability, the error hierarchy, the runtime fraction, the seven-item call-site contract, simplex geometry, experiment design, the artifact lifecycle. Plus the axes checked and found covered, and an honest convergence assessment |
| [**X** — The emulator as an object](#part-x--the-third-pass-the-emulator-as-an-object) | **The fourth pass**, run without waiting for an artifact: the learned map's **own fixed points** (this tier's headline failure mode, aimed at the model); its **Jacobian spectrum** (does stiffness survive learning — under- vs over-contraction); a **fallback dispatcher as a discontinuity in the host's Newton solve**; **ρ is not a free input dimension**; what *calibrated* means (conformal, and the four free physics-residual OOD scores the project already computes); rates as inputs; the host's real Δt distribution; capacity allocation; **one unretired design premise found while sweeping**; and why the audit has now localised to a single subject |

<details>
<summary>Full section list</summary>

```
0.1  The star as an engine        hydrostatic eq · virial theorem · negative heat
     capacity · the ρ–T plane · why massive stars stay non-degenerate
0.2  The burning staircase        ignition from the Gamow peak · energy per gram
     computed · the T⁹ neutrino clock · why Si burning lasts a day
     0.2.5 ⚠ CONVECTION: the Damköhler competition; mixing homogenises Yₑ but
           averages away none of a correlated error
0.3  Silicon burning              rearrangement mechanically · hydrostatic vs
     EXPLOSIVE · complete/incomplete burning · α-rich freeze-out
     0.3.6 ⚠ the NSE TRANSITION: where a host replaces the network with a table
0.4  The onion and the Fe core    shells · effective M_ch · entropy · compactness
     0.4.5 ⚠ which stars? mass · metallicity · rotation · BINARITY (n = 1 today)
0.5  Core collapse, derived       Γ₁<4/3 · the two runaways · free-fall ·
     TRAPPING with numbers · the homologous core · why the prompt shock fails ·
     the delayed mechanism · the mass cut · where Yₑ enters, five times
     0.5.9 ⚠ what "explodability" operationally IS — and why its derivative is
           a threshold on a non-monotonic function, not a number to look up
0.6  The observable end           ⁵⁶Ni + Arnett · isotopic ratios · GCE ·
     remnants and ⁴⁴Ti · ⚠ the missing derivative (R-14 / T-01)
     0.6.6 ⚠ THE ERROR HIERARCHY — artificial vs physical error, the framing
           the project should be using and is not
0.7  Where Yₑ comes from          EC threshold · the ratchet · the controllers
0.8  The computational setting    MESA's inner loop · the cost model · the
     emulation landscape · what this project adds
     0.8.5 ⚠ THE BOTTLENECK PREMISE IS UNMEASURED — Amdahl × the 1/f ceiling
     0.8.6 ⚠ THE CALL-SITE CONTRACT — seven requirements, six with no gate
0.9  Astrophysics → gates         the mapping table + the requirements with NO
     gate at all                  0.10 self-check (16 questions)

I.1-I.4   one-zone burners · MESA's solver · ⚠ I.2b what the network RETURNS
          (derivatives; the convergence flag) · bbq's modes · the inlist
I.5-I.8   the shipped-label pipeline · the campaign · ⚠ I.6b coverage geometry ·
          execution · validation
II.1-II.4 format · ⚠ II.1b what a row is NOT (float32 vs cancellation) ·
          the composition route · the PIN · the stall
III.1-III.7 real trajectories · the NSE census · gh-575 · the witness ·
            ⚠ III.4b the fixed-point audit that would have caught it on day one ·
            the freeze · the Yₑ consequence · the fork
IV.1-IV.9  the question · instruments · two distributions · every gate ·
           the split · ⚠ IV.8b the statistics package (bootstrap · θ sweep ·
           the positive control nobody ran) · what would have changed the answer
V.1-V.6    A vs B post-verdict · the empty mask · Φ supervision · identifiability
           ⚠ V.5b the SIMPLEX: positivity and linear conservation pull apart
           ⚠ V.5c host-side derivatives ≡ tier1 §VIII.E.2's unimplemented Q(T)
VI.1-VI.6  the NNN · the reproduction · NuGNN · what beating it means ·
           ⚠ VI.5b the protocol, written out
VII        handoff        VIII  the register T-01 … T-42 (two ranked lists)
IX         ⚠ THE BOUNDARY AUDIT — ten areas with no node in any tier;
           experiment design & multiplicity; the artifact lifecycle;
           nuclear-data uncertainty promoted; is the audit converging?
X          ⚠ THE EMULATOR AS AN OBJECT — its own fixed points · its Jacobian
           spectrum · the dispatcher discontinuity in the host's Newton ·
           ρ is not a free dimension · conformal + the free physics scores ·
           rates as inputs · the host's real Δt · capacity allocation ·
           an unretired premise (⁴⁵Sc "75%") · the audit has LOCALISED
```

</details>

---

# Part 0 — The astrophysics this project is for

Three earlier documents touch this material and none of them is a substitute for
it. Tier 0 Part I lists the motivation chain as claims to defend. Tier 2 Part 0
derives the equilibrium hierarchy and the Yₑ → M_ch link because the algebra of
that tier is unreadable without them. This part is the *setting*: the star, the
last day, the collapse, and the light that comes out. It is written so that
someone who has never opened a stellar-structure textbook can follow every step,
and so that someone who has can check every one.

The organising claim, stated once so that everything below can be measured
against it:

> **The project exists because a one-day episode of nuclear burning in a
> sphere a few thousand km in radius sets a single scalar — Yₑ — that propagates
> through a collapse,
> a bounce, a shock and an explosion to become a number an astronomer measures.
> The episode is stiff, the network is expensive, and every stellar-evolution
> calculation currently pays for it by using a network too small to get Yₑ
> right.**

Every clause of that has to be earned. §0.1–0.4 earn "one-day episode of nuclear
burning". §0.5 earns "propagates through a collapse". §0.6 earns "a number an
astronomer measures". §0.7 earns "sets a single scalar". §0.8 earns "expensive"
and "too small".

---

## 0.1 The star as a self-gravitating thermodynamic engine

Everything about late stellar evolution follows from one structural fact: a star
is a bound system whose gravity is its own, so its thermodynamics has a sign
that laboratory thermodynamics does not.

### 0.1.1 Hydrostatic equilibrium, and the pressure a star needs

A spherically symmetric star in mechanical balance satisfies (textbook:
Kippenhahn, Weigert & Weiss 2012, Ch. 2; Clayton 1968, Ch. 2)

$$
\frac{dP}{dr} \;=\; -\,\frac{G\,m(r)\,\rho(r)}{r^{2}},
\qquad
\frac{dm}{dr} \;=\; 4\pi r^{2}\rho(r).
$$

Integrating the first crudely — replace dP/dr by −P_c/R, m by M, ρ by the mean
M/(4πR³/3) — gives the central pressure a star of mass M and radius R must
supply:

$$
P_c \;\sim\; \frac{3}{4\pi}\,\frac{GM^{2}}{R^{4}}
\qquad\text{(and }\tfrac{3}{8\pi}\text{ if the uniform-density case is
integrated exactly rather than estimated).}
$$

The exact coefficient depends on the density profile — the two above differ by a
factor of two and neither is right for a real star — so the scaling P_c ∝ M²/R⁴
is what matters, and it is robust. Two consequences to hold onto:

1. **Contraction raises the required pressure steeply.** Halving R multiplies the
   demand by 16.
2. **The star must supply that pressure from *something*.** Which something —
   ideal gas, radiation, degenerate electrons — is the entire story of stellar
   evolution, and in silicon burning it is degenerate electrons at ~93–95% of the
   total (Tier 0 §0.1.2's worked example at ρ = 10⁸, T₉ = 4, Yₑ = 0.5, Ā = 28;
   recomputed 92–95% depending on the electron treatment), which is exactly why
   Yₑ matters.

### 0.1.2 The virial theorem, and the negative heat capacity — derived

Take the hydrostatic equation, multiply by 4πr³, and integrate over the star (the
textbook derivation — Kippenhahn, Weigert & Weiss 2012, Ch. 3; Clayton 1968,
Ch. 2 — reproduced here so the sign of the heat capacity is not taken on trust):

$$
\int_0^R 4\pi r^{3}\,\frac{dP}{dr}\,dr
\;=\; -\int_0^R \frac{G m}{r}\,4\pi r^{2}\rho\,dr \;=\; E_{\mathrm{grav}},
$$

where E_grav is the (negative) gravitational binding energy. Integrating the left
side by parts, with P(R) = 0,

$$
\Big[4\pi r^{3}P\Big]_0^R - \int_0^R 12\pi r^{2} P\,dr
\;=\; -3\int_0^R \frac{P}{\rho}\,dm .
$$

So

$$
\boxed{\;-3\int \frac{P}{\rho}\,dm \;=\; E_{\mathrm{grav}}.\;}
$$

Now specialise. For a non-relativistic ideal gas, P/ρ = (γ−1) u with γ = 5/3 and
u the specific internal energy, so ∫(P/ρ)dm = (2/3) E_int and

$$
E_{\mathrm{int}} \;=\; -\tfrac{1}{2}E_{\mathrm{grav}},
\qquad
E_{\mathrm{tot}} \;=\; E_{\mathrm{int}} + E_{\mathrm{grav}} \;=\; \tfrac12 E_{\mathrm{grav}} \;=\; -E_{\mathrm{int}} .
$$

**Read the last equality.** The star's total energy is *minus* its internal
energy. Radiate energy away — make E_tot more negative — and E_int goes **up**.
The star heats when it loses energy. Its effective heat capacity is negative.
[derived here; standard — Kippenhahn, Weigert & Weiss 2012, Ch. 3]

This is the engine. It explains, with no further physics:

- why a star contracts and heats after each fuel is exhausted, with no need for
  anything to "trigger" the next stage;
- why the burning stages form an ordered staircase in temperature;
- why the process runs away at the end rather than settling;
- and, crucially for this project, why the *rate* of the sequence is set by the
  **cooling** rate. A star that loses energy faster contracts faster and burns
  faster. §0.2.3 turns that into the day-long silicon-burning timescale.

For an ultra-relativistic gas (γ = 4/3, P/ρ = u/3) the same algebra gives
E_int = −E_grav and hence E_tot = 0: the star is marginally bound, and the
negative heat capacity vanishes (Shapiro & Teukolsky 1983 §3.4 for the Γ = 4/3
marginal case). **That is not a curiosity — it is the collapse condition**, and
§0.5.1 is the same statement with the corrections restored.

### 0.1.3 What temperature a contracting core reaches

Combine the virial relation with an ideal-gas equation of state,
P = ρkT/(μ̄ m_u), evaluated crudely at the centre:

$$
\frac{k T_c}{\mū m_u} \;\sim\; \frac{G M}{3R}
\qquad\Longrightarrow\qquad
T_c \;\sim\; \frac{G M \mū m_u}{3kR}
\;\propto\; M^{2/3}\rho^{1/3}.
$$

The last proportionality uses R ∝ (M/ρ)^{1/3}. Two things fall straight out.

**The mass dependence sets which stars get anywhere.** T_c ∝ M^{2/3} at fixed ρ:
a more massive core is hotter at the same density, which is why only stars above
~8–10 M⊙ reach silicon burning at all (Heger et al. 2003: stars below ∼9 M⊙ end
as white dwarfs, ∼9–10 M⊙ form degenerate ONe cores, above ∼10 M⊙ core collapse
is the only alternative) — below that, electron degeneracy (§0.1.4) halts
contraction before the core is hot enough.

**The density dependence sets the staircase.** T_c ∝ ρ^{1/3}: to raise the core
temperature by a factor of 10 you must raise its density by a factor of 1000.
Numerically, for a 1.4 M⊙ core with μ̄ ≈ 1.87 (fully ionised ²⁸Si:
μ = A/(Z + 1) = 28/15; an earlier version used μ̄ ≈ 1.4, which is no silicon-ash
composition — corrected in the 2026-08-18 audit): [derived here]

| ρ_c [g cm⁻³] | T_c from the virial estimate [GK] |
|---|---|
| 10² | 0.074 |
| 10⁶ | 1.59 |
| 10⁸ | 7.4 |

The last row is the punchline: **a Chandrasekhar-mass core compressed to
~10⁸ g cm⁻³ is, by this estimate, at 7.4 GK — silicon-burning temperature to
within the factor ~2 that the ideal-gas assumption costs.** The actual ~3.5 GK
is the regime box's centre; the crude estimate lands at its upper edge. The
pairing was not chosen — it is where the star puts itself. The box (T₉ 1.6–7.9,
ρ 10⁷–10⁹, Tier 0 §III.2) spans ±1 decade in ρ and ±0.35 dex in T around
(10⁸ g cm⁻³, 3.5 GK).

The estimate is crude by a factor of ~2 in T (7.4 GK against the ~3.5 GK at
which silicon actually burns; the ideal-gas assumption is already wrong at
10⁸ g cm⁻³, where electrons are degenerate — §0.1.4), and it should not be
quoted as a prediction. It is here to show that the regime box is *derivable*
from M, G and k, not sampled from a paper.

### 0.1.4 Degeneracy: the wall the star runs into

Electron degeneracy pressure is independent of temperature (in the T → 0 limit;
Kippenhahn, Weigert & Weiss 2012, Ch. 15; Shapiro & Teukolsky 1983 §2.3), so a
degenerate core does **not** heat when it contracts — the virial argument above
assumed an ideal gas and fails. Whether a core is degenerate is decided by
comparing the electron Fermi energy with kT (the zero-temperature Fermi momentum
and kinetic Fermi energy in the form of Chabrier & Potekhin 1998 §II):

$$
E_F \;=\; \sqrt{(p_F c)^2 + (m_e c^2)^2} - m_e c^2,
\qquad
p_F = \hbar\left(3\pi^{2} n_e\right)^{1/3},
\qquad
n_e = \rho N_A Y_e .
$$

At T₉ = 4 (kT = 0.345 MeV), Yₑ = 0.5 (Yₑ = 0.46 lowers E_F by 3–5%): [derived
here]

| ρ [g cm⁻³] | E_F [MeV] | E_F / kT | regime |
|---|---|---|---|
| 10⁶ | 0.14 | 0.4 | non-degenerate |
| 10⁷ | 0.51 | 1.5 | marginal |
| 10⁸ | 1.46 | 4.2 | degenerate |
| 10⁹ | 3.61 | 10.5 | strongly degenerate |

So the regime box spans the degeneracy transition — its low-density edge is only
marginally degenerate (E_F/kT ≈ 1.5) and its high-density edge is strongly so. That single fact is why the box
is a box rather than a line, why the equation of state has four competing
components (Tier 0 §0.1.1), and why the electron-capture threshold (which needs
E_F above a nuclear threshold) is a *box edge* rather than a global on/off switch
(Tier 0 §0.1.5).

**The astrophysical role of degeneracy.** A star that becomes degenerate before
igniting its next fuel is stuck: contraction no longer heats it, so it cools into
a white dwarf. That is the fate of everything below ~8–10 M⊙ (Heger et al. 2003). Above that mass the
core stays hot enough, relative to E_F, to keep igniting — until the iron core,
where there is no next fuel and degeneracy is all that is holding the star up.
**The whole massive-star story is a race between contraction-heating and
degeneracy, and the iron core is where degeneracy finally wins and then
immediately loses** (§0.5).

---

## 0.2 The burning staircase, derived rather than tabulated

Tier 0 §I.1 tabulates the stages. This section derives *why the table looks like
that*, because three of the project's design facts — the Si-burning temperature,
the one-day duration, and the neutrino-dominated energetics — are consequences of
the derivation rather than of the table.

### 0.2.1 Why each fuel ignites where it does

Tier 1 §1.2 derives the Gamow peak (textbook: Clayton 1968 §4-3; Iliadis 2015
§3.2.1; the E₀/kT and exp(−3E₀/kT) forms are also in Adelberger et al. 2011
§II.A): for a non-resonant charged-particle reaction between nuclei of charges
Z₁, Z₂ and reduced mass μ, the effective burning energy and the rate's
temperature dependence are governed by

$$
E_0 \;=\; \left(\frac{b\,kT}{2}\right)^{2/3},
\qquad
b \;=\; \frac{\sqrt{2\mu}\,\pi Z_1 Z_2 e^{2}}{\hbar},
\qquad
\langle\sigma v\rangle \;\propto\; \exp\!\left[-\,3\left(\frac{b}{2}\right)^{2/3}\!(kT)^{-1/3}\right].
$$

It is convenient to name the combination b² ≡ E_G, the **Gamow energy**, and to
write the exponent as a single dimensionless number:

$$
E_G \;=\; 2\mu c^{2}\left(\pi\alpha Z_1Z_2\right)^{2}
\;=\; 0.979\,\left(Z_1Z_2\right)^{2}A_{\mathrm{red}}\ \mathrm{MeV},
\qquad
\tau \;\equiv\; \frac{3E_0}{kT} \;=\; 3\left(\frac{E_G}{4kT}\right)^{1/3},
$$

so that ⟨σv⟩ ∝ e^{−τ} (the coefficient 0.979 (Z₁Z₂)²A_red MeV is Rolfs & Rodney
1988's; CODATA α gives 0.9791). Ignition happens when the rate becomes fast enough to
balance the star's losses. **The tempting move at this point is wrong and worth
doing carefully**, because getting it wrong is how one ends up with a staircase
that does not exist.

The tempting move: hold the exponent fixed at ignition, τ_ign ≈ const, and read
off T_ign ∝ E_G ∝ (Z₁Z₂)²μ. That would make carbon ignite at 36² × 12 ≈ 1.6 × 10⁴
times the pp ignition temperature, i.e. at ~60 GK — hotter than anything short of
the bounce shock. It does not; the actual factor is 200. Inverting the definition
of τ instead,

$$
kT_{\mathrm{ign}} \;=\; \frac{E_G}{4}\left(\frac{3}{\tau_{\mathrm{ign}}}\right)^{3}
\qquad\Longrightarrow\qquad
T_{\mathrm{ign}} \;\propto\; \frac{E_G}{\tau_{\mathrm{ign}}^{3}} ,
$$

and **τ_ign is not slowly varying** — it is the whole story. Check against the
fuels, with E_G computed from the formula above and τ_ign evaluated at each
stage's actual ignition temperature: [derived here; ignition temperatures after
Woosley, Heger & Weaver 2002 (not re-read here), bracketed by Kato, Ishidoshiro &
Yoshida 2020 for a 15 M⊙ MESA model — H 4 × 10⁷, He 1.5 × 10⁸, C 7 × 10⁸,
Ne 1.4 × 10⁹, O 1.6 × 10⁹, Si ~3 × 10⁹ K — and by Arnett et al. 1989 for 20 M⊙
(via Odrzywolek et al. 2004): C 0.81, Ne 1.69, O 2.10, Si 3.70 GK]

| fuel | dominant channel | Z₁Z₂ | A_red | E_G [MeV] | T_ign (actual) | τ_ign |
|---|---|---|---|---|---|---|
| H (pp) | p + p | 1 | 0.50 | 0.49 | 0.004 GK (pp threshold in the lowest-mass stars; H ignites at 0.03–0.04 GK in a massive star, Kato et al. 2020) | 21.3 |
| H (CNO) | ¹⁴N(p,γ)¹⁵O | 7 | 0.933 | 44.8 | 0.03 GK | 48.9 |
| He | α + α (→ ¹²C) | 4 | 2.0 | 31.3 | 0.15–0.2 GK | *resonant* |
| C | ¹²C + ¹²C | 36 | 6.0 | 7 617 | 0.8 GK | 90.7 |
| Ne | ²⁰Ne(γ,α) | — | — | — (**photo**) | 1.5 GK | — |
| O | ¹⁶O + ¹⁶O | 64 | 8.0 | 32 100 | 2.0 GK | 107.9 |
| Si | ²⁸Si(γ,α) | — | — | — (**photo**) | 3–4 GK | — |

Because τ_ign is *defined* from the actual T_ign, E_G/τ_ign³ = 4kT_ign/27
reproduces the ignition temperatures *identically* — that is a bookkeeping
identity, not a test (an earlier version of this paragraph presented the
agreement as a prediction "to better than 1%"; corrected in the 2026-08-18
audit). What the table does show is *how the ratio is made*: from pp to oxygen,
**E_G grows by 6.6 × 10⁴ while T_ign grows by only 500, so τ_ign³ must absorb a
factor of 130** (τ_ign rising from 21 to 108). The Coulomb barrier really is
enormous; the reason the staircase is compressed into under three decades of
temperature rather than nearly five is that the star simply burns deeper into
the exponential tail for each successive fuel (τ_ign ≈ 21 → 49 → 91 → 108). What
sets τ_ign is the rate the star needs — E_fuel divided by the loss rate — which
is why it is not universal.

Two rows do not belong to that scaling at all, for two different reasons.

**Helium is resonant.** Triple-α proceeds through the ⁸Be ground state and the
Hoyle resonance in ¹²C (Salpeter 1952; Hoyle 1954; textbook, Iliadis 2015
§5.2.2), so its rate is set by a narrow-resonance formula, not by the
non-resonant Gamow integral; its τ is not the controlling quantity and the
row is listed only for the barrier comparison.

**Neon and silicon are not fusion at all.** They do not ignite because their
Coulomb barriers become penetrable; they ignite because the thermal photon bath
acquires enough γ-rays above the (γ,α) threshold (Kato et al. 2020 for neon;
Boccioli & Roberti 2024 for the "re-adjustment of the chemical composition"
character of the O-to-Fe stages). Take the same estimate seriously for
²⁸Si + ²⁸Si: Z₁Z₂ = 196 and A_red = 14 give E_G = 5.3 × 10⁵ MeV, 16.4× oxygen's,
and extrapolating the slowly-rising τ_ign ≈ 115–130 puts fusion ignition at
**≈ 20 GK** (19–27 GK across that τ range) — far above where the star ever gets
in hydrostatic burning, and above the temperature at which the Fe peak itself
dismantles. More directly: at T₉ = 3.5 the Si + Si exponent is τ = 228 against
108 for O + O at its ignition, i.e. a penetrability suppressed by e^{−120}.

**This is the single most important structural fact in the project**, and it is
worth stating in the sharpest available form:

> ²⁸Si cannot burn by fusing with itself, at any temperature the star survives.
> It burns by being taken apart.

Everything downstream — the near-balanced forward/reverse pairs, the
quasi-equilibrium clustering, the catastrophic cancellation, the κ diagnostic,
the stiffness, and the entire Target A design — is a consequence of that
sentence.

The photodisintegration threshold itself is derivable. The relevant quantity is
Q/kT for the (γ,α) channel, with kT = 86.2 keV × T₉:

$$
{}^{28}\mathrm{Si}(\gamma,\alpha)^{24}\mathrm{Mg}: \quad Q = 9.98\ \mathrm{MeV}
\qquad\Longrightarrow\qquad
\frac{Q}{kT} = \frac{115.8}{T_9}.
$$

At T₉ = 3 that exponent is 38.6; at T₉ = 4 it is 28.9. [derived here — Q from
the AME2020 mass excesses (S_α(²⁸Si) = 9.984 MeV), Tier 0 §0.3.1] Between those
two temperatures the Boltzmann suppression changes by a factor
e^{9.65} ≈ 1.6 × 10⁴. The transition from "no
photodisintegration" to "photodisintegration controls everything" occupies less
than a factor of 1.5 in temperature, which is why §0.2 of Tier 2 can say the
regime change happens across less than a factor of two in T, and why the kill-test
priority window is 3.3–5 GK.

### 0.2.2 The energy per gram of each stage, computed

Take the binding energies (Tier 0 §0.3.1's sign convention: B > 0, and the energy
released is ΔB) and compute the specific energy release of each stage. For a
reaction with total ΔB over A nucleons, the release per gram is
N_A × (ΔB/A) [MeV] × 1.602 × 10⁻⁶ erg/MeV. [derived here; Q-values from the
AME2020 mass excesses (Wang et al. 2021) with CODATA 2018 constants (Tiesinga et
al. 2021), all four rows recomputed in the 2026-08-18 audit]

| stage | representative reaction | ΔB [MeV] | per nucleon [MeV] | per gram [erg/g] |
|---|---|---|---|---|
| H → He | 4p → ⁴He + 2e⁺ + 2ν | 26.7 (gross; ν carry off ~2–7%) | 6.7 | 6.5 × 10¹⁸ |
| C burning | 2 ¹²C → ²⁰Ne + α | 4.62 | 0.192 | 1.9 × 10¹⁷ |
| O burning | 2 ¹⁶O → ²⁸Si + α | 9.60 | 0.300 | 2.9 × 10¹⁷ |
| Si burning | 2 ²⁸Si → ⁵⁶Ni | 10.92 | 0.195 | 1.9 × 10¹⁷ |

Two lessons.

**(i) Hydrogen burning releases 22–35× more per gram than anything after it**
(34× against carbon and silicon, 22× against oxygen). The
first stage carries almost the whole nuclear energy budget of the star's life;
everything from carbon onward is scraping the barrel. This is why the late stages
cannot last: there is very little fuel value left, and (§0.2.3) the losses are
enormous.

**(ii) Silicon burning is not even the most productive late stage.** Oxygen
burning releases 50% more per gram. Silicon's distinction is not its energy
yield — it is that it is the *last* one, that it produces the iron peak, and that
it is where the composition acquires the neutron excess that decides what
happens next.

For the record, the binding-energy-per-nucleon values that matter at the top of
the curve: ⁵⁶Fe 8.790, ⁶²Ni 8.795, ⁵⁶Ni 8.643 MeV/nucleon. [AME2020: 8790.36,
8794.56, 8642.78 keV] ⁶²Ni is the maximum, not ⁵⁶Fe (Fewell 1995) — the
standard shorthand is false, and Tier 2 §0.2.3 explains why ⁵⁶Fe nonetheless wins in NSE at
Yₑ ≈ 0.46: the free energy is minimised at fixed Yₑ, and the winner is the
nucleus whose Z/A *matches* Yₑ among the near-maximally-bound ones.

### 0.2.3 The neutrino clock — why the last stages are short

Here is the fact that turns an ordered staircase into an accelerating collapse.

**From carbon burning onward, the star's dominant energy loss is neutrino
emission from the plasma, not photon radiation from the surface** (Limongi 2017:
pair-neutrino emission "starts to become efficient when the central temperature
exceeds ∼8 × 10⁸ K, i.e., at the beginning of core C burning"; Odrzywolek,
Misiaszek & Kutschera 2004). The contrast is in *how the energy gets out*, not in
how long a fuel lasts. Photons are trapped: the interior is optically thick, so
energy random-walks outward on a thermal (Kelvin–Helmholtz) timescale of ~10⁴
years for a massive main-sequence star (much shorter for the extended supergiant
envelope), is
reprocessed on the way, and emerges from the surface at whatever rate the
star's structure permits — the luminosity is set by the envelope, not by the
burning region. Neutrinos have cross-sections around 10⁻⁴⁴ cm² at these energies
(Odrzywolek et al. 2004: spectrum-averaged σ(ν̄ₑp) ≈ 7 × 10⁻⁴⁴ cm² for
pre-supernova neutrinos) and mean free paths vastly exceeding the stellar radius,
so they leave **at the speed of light, directly from the point of production**
(Tier 0 §0.4.2; Limongi 2017), and the
loss rate is set by the local plasma conditions alone. The core is optically thin
to its own dominant coolant, and that is what decouples its cooling rate from its
structure.

(The *duration* of each stage is E_fuel/L, a nuclear timescale — 10⁷ years for
hydrogen (Kato, Ishidoshiro & Yoshida 2020 for a 15 M⊙ model; Limongi 2017:
10⁷–10⁶ yr over 13–120 M⊙) because there is a great deal of hydrogen and
§0.2.2's release per gram is large, not because of any transport time. What the transport argument
establishes is the switch of coolant, and §0.2.3's remaining paragraphs are what
turn that into a duration.)

The dominant thermal channel here is **electron–positron pair annihilation**,
e⁺e⁻ → νν̄ (Kato et al. 2020; Patton, Lunardini & Farmer 2017). Its emissivity
requires a thermal positron population, which requires kT no longer negligible
against m_e c² = 0.511 MeV — kT/m_ec² ≈ 0.17 at T₉ = 1, where the Boltzmann
factor e^{−2m_ec²/kT} ≈ 10⁻⁵ already makes the pair population non-negligible;
onset ~0.8–1 GK (Limongi 2017; Odrzywolek et al. 2004). Once that threshold is
crossed the positron number density rises as roughly exp(−2m_ec²/kT) times
phase-space factors, and the emissivity per gram rises extremely steeply —
approximately as T⁹ in the relativistic non-degenerate limit (Fowler & Hoyle
1964; Itoh et al. 1996, ApJS 102, 411, for the fitting formulae stellar codes
use); across 2–3.5 GK the effective exponent of the pair rate is ≈ 7–8 [derived
here from the non-relativistic form ε ∝ T₉³ e^{−11.86/T₉}], and the emissivity
per gram is further reduced by electron degeneracy at ρ ≳ 10⁷–10⁸ g cm⁻³ (Kato
et al. 2020 §2).

Put the two facts together with the virial engine of §0.1.2:

$$
\text{contraction}
\;\longrightarrow\; T\uparrow
\;\longrightarrow\; \varepsilon_\nu \propto T^{9}\ \text{rises catastrophically}
\;\longrightarrow\; \text{must burn faster}
\;\longrightarrow\; \text{contraction}
$$

The runaway is not in the burning; it is in the **cooling** (Limongi 2017: "an
almost constant nuclear energy … coupled to the dramatic increase of the total
luminosity"). Each stage must generate energy at the rate the neutrinos remove
it, and that rate rises by roughly seven to nine powers of T while the available
fuel energy per gram (§0.2.2) is roughly constant. So the duration of stage n scales as

$$
\tau_n \;\sim\; \frac{E_{\mathrm{fuel}}}{\varepsilon_\nu(T_n)} \;\propto\; T_n^{-9}
$$

to leading order (effective exponent closer to 7–8 across 2–3.5 GK; ρ and
degeneracy neglected). Check it: from oxygen burning (T₉ ≈ 2, months — 180 d for
20 M⊙, Arnett et al. 1989 via Odrzywolek et al. 2004; 14 months for 15 M⊙, Kato et
al. 2020) to silicon burning (T₉ ≈ 3.5), the temperature ratio is 1.75 and
1.75⁹ = 154 (with the effective exponent 7.5 the factor is 1.75^{7.5} ≈ 70 —
still "of order a day"). Months / 154 is of order a day. **The one-day
silicon-burning timescale is a T⁹ scaling law applied to the oxygen-burning
duration.** [derived here — order-of-magnitude only; the actual duration depends
on core mass and shell structure: roughly a day (shorter for the most massive
cores) to a couple of weeks — 2 d (20 M⊙; Arnett et al. 1989 via Odrzywolek et
al. 2004), 4.5 d (15 M⊙ MESA model; Kato et al. 2020), ~10⁻² yr ≈ 4 d (Limongi
2017); the ~2-week upper end is Tier 0 §I.1 (after Woosley, Heger & Weaver 2002),
not re-verified here [typical]]

Three consequences that shape this project:

1. **The regime is transient and the star never settles.** There is no
   steady-state silicon-burning configuration to compute; the whole episode is a
   relaxation with continuously changing (T, ρ). That is why the training data is
   a grid of *initial states* burned for fixed Δt rather than a library of
   equilibria, and why the operator-splitting framing of Tier 0 §IV.1 is the
   right one.
2. **Neutrino losses are a first-class output, not an afterthought.** ε_ν appears
   in the NNN's loss function and in the emulator's specified output head for the
   same reason it appears in the star's energy equation: it is the dominant term.
   Tier 1 §VIII.C.3 flags that the flux route currently drops the tabulated NU
   column; §0.2.3 is why that flag matters.
3. **"Burning" and "cooling" are not separable.** The T⁹ coolant and the
   temperature-sensitive burning are locked together. An emulator validated at
   *imposed* (T, ρ) — which is all of this project's data — has never been tested
   inside that loop. This is `tier1.md` §VIII.C.4 / Tier 2 **R-11**, and §0.8.1
   returns to it.

### 0.2.4 What the star is doing while the network is being called

To ground the above: at silicon-burning conditions, the star's core is ~1.4 M⊙
of matter a few thousand km in radius, with central density ρ_c ~ 10⁸ g cm⁻³
(4.9 × 10⁷ in the 20 M⊙ model of Arnett et al. 1989 via Odrzywolek et al. 2004;
a uniform 1.4 M⊙ sphere at 10⁸ would be only 1.9 × 10³ km, a centrally condensed
core with ρ_c ~ 10⁸ is ~7 × 10³ km — an earlier version wrote "a ~10⁴ km sphere
at ρ ~ 10⁸", an inconsistent triple; corrected in the 2026-08-18 audit) and
T_c ~ 3.5 GK (3.7 GK in that model), converting silicon to iron-peak nuclei over
about a day (Farmer et al. 2016: "Silicon ignites at the center within one day
of core-collapse"), radiating almost all of that energy as neutrinos that leave
instantly, contracting as the fuel is depleted and the entropy is drained by
neutrinos, and building an iron core that grows toward a mass limit it cannot
exceed.

Meanwhile, in a MESA calculation of the same object, the nuclear network is being
evaluated for every zone at every Newton iteration of every timestep in the
default fully coupled mode (once per hot zone per step, with internal sub-steps,
in `op_split_burn` mode) — hundreds to thousands of zones (Paxton et al. 2011
§6.1), and timesteps so short at the end that the last day of the star's life can
consume a large fraction of the total run time of the whole 10⁷-year calculation.
§0.8 quantifies that.

### 0.2.5 Convection — the transport a one-zone burner cannot see

Tier 0 §0.7 puts the convective turnover time in the timescale table (10¹–10³ s,
with an honest warning that both factors in L/v_conv are uncertain by a decade;
the 3D Si- and O-shell simulations of Couch et al. 2015 and Müller et al. 2016
give ≈ 20 s)
and concludes "one-zone is an approximation". That is where the treatment stops
in every existing tier. It should not, because mixing is not a small correction
to late-stage burning — **it is co-dominant with it**, and it changes what the
emulator's error budget means.

**Silicon shell burning is convective** (Couch et al. 2015: "strong convection
driven by violent Si burning in the shell surrounding the iron core"). The energy
generation rate is a steep function of temperature, so the burning region is
strongly superadiabatic and convection sets in immediately. In a 1D
stellar-evolution code this is modelled by mixing-length theory (MLT): convection
becomes a diffusive process with diffusivity D ≈ ⅓ v_conv ℓ (Paxton et al. 2011
§5.2; MESA r23.05.1 `turb/private/mlt.f90:156`, `D = conv_vel*Lambda/3d0`), and
the composition equation acquires a transport term (Paxton et al. 2011 §6):

$$
\frac{\partial Y_i}{\partial t}
\;=\; \underbrace{\big[\nu\,\mathbf R(\mathbf Y;T,\rho)\big]_i}_{\text{the network — what this project emulates}}
\;+\;\underbrace{\frac{\partial}{\partial m}\!\left[(4\pi r^2\rho)^2 D\,\frac{\partial Y_i}{\partial m}\right]}_{\text{mixing — outside the split}} .
$$

Those two terms can be **operator-split** from each other. With MESA's
`op_split_burn` option (Jermyn et al. 2023 §10.2 — off by default, but switched on
in MESA's own core-collapse test-suite models and the mode the NNN paper §4
envisages plugging into; the default solver couples burning, mixing and structure
in one Newton solve, Paxton et al. 2011 §6.1), each hot zone is burned first at
fixed (T, ρ), and mixing is then solved together with the structure. The emulator
replaces the burn operator only. (An earlier version described the burn-mix-
structure sequence as MESA's universal behaviour; corrected in the 2026-08-18
audit.)

**The competition is quantified by a Damköhler number.** Define

$$
\mathrm{Da}_i \;=\; \frac{\tau_{\mathrm{mix}}}{\tau_{\mathrm{burn},i}} ,
$$

the ratio of the mixing time to the timescale on which process i changes the
composition (the standard combustion definition, Da = τ_transport/τ_reaction, so
Da > 1 means burning is faster than mixing). Da ≫ 1 means
burning wins and gradients survive; Da ≪ 1 means mixing wins and the region is
homogeneous in that quantity. Read the numbers off Tier 0
§0.7's table with τ_mix ≈ 10¹–10³ s: [derived here]

| process | τ | Da = τ_mix/τ | verdict |
|---|---|---|---|
| intra-group equilibration | ≲ 10⁻³ s | **10⁴ – 10⁶** | burning wins overwhelmingly |
| inter-group (bridge) flow | 10⁻¹ – 10² s | **10⁻¹ – 10⁴** | *comparable* — no clean answer |
| weak reactions / Yₑ | 10² – 10⁵ s | **10⁻⁴ – 10¹** | **mixing wins, mostly** |

Three consequences, and the second is the one that matters most.

**(i) The fast species are local; Yₑ is not.** Group-internal equilibrium is
established far faster than material can be transported, so the QSE composition
is a *local* function of the local state — which is what licenses treating the
network call as a per-zone problem at all. But Yₑ evolves on a timescale
comparable to or longer than mixing, so **Yₑ is spatially homogenised across the
convective region**. The quantity the whole project is organised around is the
one mixing most strongly averages.

**(ii) That averaging does not save a systematic error — and the arithmetic is
§0.4.2's argument, in space instead of time.** Suppose the emulator makes a
per-zone Yₑ error δ, and the convective region spans N_z zones (of order 10²–10³
[assumed — order of magnitude; Paxton et al. 2011 §6.1 give "hundreds to
thousands" of cells for the *whole* model]
in a MESA model). After mixing, the region's error is

$$
\delta_{\text{mixed}} \;=\;
\begin{cases}
\delta/\sqrt{N_z} & \text{if per-zone errors are independent},\\[2pt]
\delta & \text{if the error is a systematic function of the state.}
\end{cases}
$$

Zones in one convective region have *similar* (T, ρ, X) — that is what being in
one convective region means — so a learned model's error on them is strongly
correlated, not independent. **Mixing averages away almost none of a neural
network's error, while it would have averaged away most of a random one.** A
third independent argument for the conclusion Tier 2 §0.4.2 reaches for soft
penalties and Tier 0 §IV.3 reaches for rollout: *the character of the error
matters more than its size, and correlated error is the enemy.* [derived here]

**(iii) Mixing feeds the network states that are mixtures, not trajectories.**
The composition arriving at a network call is a blend of burnt and unburnt
material from different depths — not the endpoint of any single burning history.
This cuts *in favour* of the Sobol design in a way nobody in the project has said
out loud:

> The relaxed manifold (§IV.3, distribution B) is built from constant-(T, ρ)
> single-history relaxations, the *opposite* extreme from the training grid's
> random mixtures. Real convective burning sits **between** them: compositions
> partially relaxed *and* partially mixed. Neither measured distribution is the
> deployment distribution, and the true one is probably not bracketed by them
> either, because mixing can inject fuel no relaxation would produce.

That is a sharper statement of the distribution problem than §IV.3 gives alone,
and it means the Sobol → real-MESA gate is testing something more complicated
than "physical versus unphysical states".

**And the modelling caveat that tempers all of it.** MLT captures the bulk
velocity scale of late-stage shell convection reasonably well (Meakin & Arnett
2007; Müller et al. 2016) but misses the boundary physics. Three-dimensional
hydrodynamic simulations of oxygen and silicon shell burning show turbulent
entrainment at convective boundaries (Meakin & Arnett 2007; Müller et al. 2016:
the O shell grew from 0.51 to 0.56 M⊙ by entrainment), large-scale bulk motions
at Mach numbers approaching 0.1 in the oxygen shell at collapse (Müller et al.
2016; ~0.03 in Meakin & Arnett 2007; ~0.02 in the Si shell of Couch et al. 2015
as estimated by Müller et al. 2016), and — in some models — **shell mergers**,
where the oxygen and neon shells convectively merge and the composition changes
qualitatively (in 1D: Sukhbold, Woosley & Heger 2018; 3D "encroachment" short of
a full merger before collapse: Müller 2016; the full 3D O–Ne merger of Yadav et
al. 2020 and the 1D shell-merger survey of Collins, Müller & Heger 2018 were not
opened here). Shell mergers change the pre-supernova structure
and the compactness (Sukhbold et al. 2018: "when this occurs, the compactness is
usually small") and the yields [assumed], and 1D codes reproduce them only
through calibrated prescriptions. (An earlier version said MLT "is known to
describe late-stage convection poorly"; both cited 3D papers say the opposite of
the bulk flow — corrected in the 2026-08-18 audit.)

So the honest hierarchy of modelling error in a pre-supernova model is
**3D convection ≫ network size ≳ rate uncertainties ≫ emulator target** (the
network-size rung: Farmer et al. 2016 find the isotope count "plays a more
significant role in determining the span of the variations for neon, oxygen and
silicon burning" than resolution; the rate-uncertainty rung is Fields et al.
2018, not opened here; the ordering itself is this author's judgement)
— §0.6.6 assembles it properly, because it determines what the project can claim.

Nothing about mixing appears in any tier's register. Registered as **T-19**, and
it feeds **T-20** (the error hierarchy).

---
## 0.3 Silicon burning proper

Tier 2 §0.2 gives the mechanism in outline. This section is the fuller physical
picture, including the part Tier 2 explicitly deferred: silicon burning happens
in **two different astrophysical settings**, with different consequences, and the
project's data is a model of only one of them.

### 0.3.1 The mechanism, mechanically

Start from a zone of ²⁸Si and ³²S (the ash of oxygen burning; Hix & Thielemann
1996 §1: "silicon isotopes and their α-nuclei neighbors, S, Ar, and Ca") at
T₉ ≈ 3.5, ρ ≈ 10⁸.

**Step 1 — the photon bath finds the weakest link.** The Planck distribution at
kT = 0.30 MeV has an exponentially small but nonzero population above 10 MeV
(Hix & Thielemann 1996: a photodisintegration channel becomes important once its
Q-value falls below ≈ 30 k_BT). Nuclei with the *lowest* particle-separation
energies are attacked first: the (γ,α), (γ,p) and (γ,n) channels on whichever
species in the mixture happens to be least bound against that channel. For a
silicon-group mixture, that is not ²⁸Si — ²⁸Si is comparatively tightly bound
(S_α = 9.98 MeV, S_p = 11.6 MeV, the highest along the α-chain; AME2020) — but
the odd-A and less-bound neighbours.

**Step 2 — a reservoir of light particles appears.** Every photodisintegration
deposits a free α, p or n into the plasma. These particles have no Coulomb
barrier problem worth speaking of (n) or a small one (p, α on light targets), so
their capture rates are enormous. A free neutron at these conditions is captured
in a time of order 10⁻¹⁰ s — and that figure is deliberately conservative:
n_target⟨σv⟩ with n_target ~ 10³⁰ cm⁻³ and ⟨σv⟩ ~ 10⁻¹⁷ cm³ s⁻¹ gives closer to
10⁻¹³ s, so the true separation from the bridge timescales of step 4 is wider
than the number quoted here. [derived here — order of magnitude]

**Step 3 — the reservoir is spent on whatever is most bound.** The captured
light particles are distributed over the whole silicon group by the fast
capture/photodisintegration pairs, and net flow proceeds toward higher binding
energy. The material walks up in A, one light particle at a time.

**Step 4 — the flow encounters bottlenecks.** Not every step is fast. A few
reactions have small rates relative to the rest — because of an unfavourable
Q-value, a Coulomb barrier on a heavier target, or a structural feature of the
nucleus. Those are the **bridges**: the reactions the net flow has to pass
through, connecting the silicon group to the iron group. Everything else is
running back and forth in near-balance.

**Step 5 — the endpoint is set by Yₑ.** Material accumulates in the iron peak,
and *which* iron-peak nuclei depends on the neutron-to-proton ratio available,
i.e. on Yₑ. §0.3.3.

The end-to-end result: 2 ²⁸Si → ⁵⁶Ni, releasing 0.195 MeV/nucleon (§0.2.2;
Q = 10.922 MeV from the AME2020 mass excesses), achieved by disassembling some
fraction of the silicon completely and reassembling it (Hix & Thielemann 1996: "a
complex series of photodissociation and capture reactions"). No ²⁸Si nucleus
ever touches another ²⁸Si nucleus.

**The signature of this mechanism in the equations** — the reason it dominates
everything in Tiers 1–2 — is that steps 1–3 are *fast and nearly balanced*, while
step 4 is *slow and one-directional*. Fast near-balanced pairs are exactly:

- **near-zero κ** (Tier 2 §II.4): |φ| ≪ f⁺ + f⁻;
- **large Jacobian eigenvalues with tiny net effect**: stiffness (Tier 2 §IV.1);
- **quasi-statistical equilibrium**: the balanced subnetwork's composition is a
  function of a few parameters (Tier 2 §0.1);
- **catastrophic cancellation in floating point** (Tier 0 §V.1).

Those are four names for step 1–3. And the *interesting* physics — the net flow,
the energy release, the Yₑ evolution — lives entirely in step 4 and in the weak
sector, which is a small fraction of the columns (Hix & Thielemann 1996 §6: one
can "ignore the reactions within the quasi-equilibrium groups … [and]
concentrate on those reactions which enter or leave the QSE groups"). That
asymmetry is the project's central bet.

### 0.3.2 The two clusters, and what the group boundary means physically

The balanced subnetwork does not connect everything to everything. It splits: a
**silicon group** (roughly 24 ≤ A ≲ 45) and an **iron group** (A ≳ 45), each
internally equilibrated on a timescale short compared with the burning, but
connected to each other only through the slow bridges (Hix & Thielemann 1996
§§4, 6.1: "two groups, roughly divided by A ≃ 45", the bottom edge of the
silicon group being Mg). Quasi-equilibrium itself is Bodansky, Clayton & Fowler's
(1968) result — a *single* group from ²⁸Si to the iron peak; the split into two
groups joined by bridges is Woosley, Arnett & Clayton's (1973), confirmed and
made Yₑ-dependent by Hix & Thielemann (1996) (an earlier version of this
sentence credited the two-group split to BCF68; corrected in the 2026-08-18
audit). It is the reason the composition during silicon burning is neither a
free ODE trajectory (too many degrees of freedom) nor a state function (NSE —
too few).

**Why the split exists at all** is worth understanding physically rather than
taking as an empirical fact. The equilibration of a group requires that every
member be connected to every other by reactions fast compared with the burning
timescale. In the A ≈ 45 region there is a gap in the reaction network's
effective conductivity, and it has two causes pulling the same way.

**(a) The boundary nuclei are *loosely* bound against α emission, not tightly.**
This is the one that is easy to get backwards. The α-separation energies say:

$$
S_\alpha({}^{40}\mathrm{Ca}) = 7.04\ \mathrm{MeV},
\qquad
S_\alpha({}^{44}\mathrm{Ti}) = 5.13\ \mathrm{MeV},
$$

[sourced: AME2020 via the IAEA Live Chart — Q_α(⁴⁰Ca) = −7039.78 keV,
Q_α(⁴⁴Ti) = −5127.10 keV] — so ⁴⁴Ti photodisintegrates *more* readily than the
⁴⁰Ca below it, and the (γ,α) reverse on the ⁴⁰Ca(α,γ)⁴⁴Ti step runs hard. The
bridge is slow in **net** terms precisely because its reverse is fast: material
pushed across is pushed straight back. A local dip in the binding-energy-per-
nucleon curve (⁴⁴Ti at 8.534 MeV/nucleon, *below* ⁴⁰Ca's 8.551) is what a
bottleneck looks like from the thermodynamic side. (This is the α-chain step
⁴⁰Ca(α,γ)⁴⁴Ti; the (p,γ) bridges into ⁴⁶Ti feed a tightly bound product,
S_p(⁴⁶Ti) = 10.3 MeV, and are limited instead by the small feeder abundances —
Hix & Thielemann 1996 §6.2.)

**(b) The capture reactions that would carry flow across face Coulomb barriers on
targets with Z ≈ 20–21**, which suppresses the forward direction independently of
(a) (Hix & Thielemann 1996 §1, after Thielemann & Arnett 1985: the bottleneck
"coinciding roughly with Z = 21" is bridged on the proton-rich side).

Together these make the crossing slow relative to the silicon-group internal
reactions but not slow enough to stop the flow entirely — which is exactly the
condition for two separately-equilibrated groups joined by identifiable bridges.

**And therefore the boundary is not sharp** (Hix & Thielemann 1996 §4: "some
ambiguity in defining the boundary between the QSE groups"). Whether ⁴⁵Sc counts
as silicon-group or iron-group is a *modelling choice about a continuum*. The repo
handles this correctly by making it a config variant
(`configs/qse_groups.yaml`: `default` 24 ≤ A < 45 vs `a24_46` with the boundary
at A = 46, putting ⁴⁵Sc inside the group) and requiring every group/bridge
analysis to report both (`CLAUDE.md`). The measured consequence — the verdict is
insensitive to the variant at the ≤0.02 level in top-k shares, **[RESULTS]**
2026-07-12 — is exactly the kind of result the discipline exists to produce: the
choice was declared a choice *before* it turned out not to matter.

**The bridge sets, measured.** For mesa_80 on the relaxed manifold:
Ne22(α,n)Mg25 (share 0.20), Al27(p,α)Mg24 (0.13), P31(p,α)Si28 (0.11),
Na23(α,p)Mg26, Mg24(n,γ)Mg25; top-20 columns carry 0.88 of the inter-group flux.
For mesa_151: Mg24(p,α)Na21 (0.14), Mg24(p,γ)Al25, Cl35(p,α)S32, P31(p,α)Si28,
Ca44(p,γ)Sc45 — and the literature bottleneck **⁴⁵Sc(p,γ)⁴⁶Ti at rank 2 of 251**
under the `a24_46` boundary. **[RESULTS]** 2026-07-12.

That last one deserves a moment. The reaction was named in the literature as the
high-Yₑ bottleneck of silicon burning (Woosley, Arnett & Clayton 1973 §VIb; Hix &
Thielemann 1996 §6.2: ⁴⁵Sc(p,γ)⁴⁶Ti "accounts for approximately 70% of the entire
flux into the iron peak group" at Yₑ = 0.498 — and *not* the link at Yₑ = 0.46;
an earlier version of this sentence cited Grichener et al. 2025 for the claim,
whose paper does not mention the reaction; corrected in the 2026-08-18 audit),
and this project found it independently at rank 2 of 251 inter-group carriers on
relaxed high-Yₑ trajectory rows in the 3.3–5 GK window. That is a genuine
external validation of the whole flux machinery: a published physical claim,
reproduced by an independent pipeline (one that shares the REACLIB/pynucastro
rate-library family with the literature, so "independent" is about the code, not
the inputs). It is also a warning about distribution — on the *training*
distribution (random Sobol compositions) the same reaction ranks only 31/251
**[RESULTS]** 2026-07-10. The bottleneck is a property of relaxed flow, and it is
invisible where the model will be trained. §IV.3 is about that gap.

### 0.3.3 The endpoint, and why Yₑ chooses it

Silicon burning ends when the material reaches the iron peak and there is nothing
more exothermic to do. *Which* iron-peak nucleus is the endpoint is a selection
problem, and the selection rule is Yₑ.

Consider NSE at fixed (T, ρ, Yₑ). The composition minimises free energy subject to
ΣXᵢ = 1 and Σ(Zᵢ/Aᵢ)Xᵢ = Yₑ (the chemical-potential formulation of NSE, Hix &
Thielemann 1999b §5, after Clifford & Tayler 1965). At low enough temperature
that the binding-energy term dominates the entropy term, the winner is the
nucleus that maximises binding energy per nucleon **subject to having the right
Z/A** (Hix & Thielemann 1999b: "the most abundant nuclei at low temperatures are
the most bound nuclei for which Z/A ∼ Yₑ"; Hartmann, Woosley & El Eid 1985
Fig. 2). Since Yₑ = ⟨Z/A⟩ for the
mixture, and a single dominant species must therefore have Z/A ≈ Yₑ:

| Yₑ | Z/A match | dominant NSE species |
|---|---|---|
| 0.500 | 28/56 = 0.500 | **⁵⁶Ni** (doubly magic, B/A = 8.643) |
| 0.482 | 26/54 = 0.4815 | **⁵⁴Fe** (and ⁵⁸Ni, 28/58 = 0.483, B/A 8.732 vs 8.736) |
| 0.464 | 26/56 = 0.4643 | **⁵⁶Fe** (B/A = 8.790) |
| 0.452 | 28/62 = 0.4516 | ⁶²Ni region (⁵⁸Fe, at 26/58 = 0.448, sits just below) [dominance assumed here; no source opened] |

[derived here — the Z/A arithmetic recomputed, B/A values AME2020; the NSE
dominance rule is Hix & Thielemann 1999b §5 and Hartmann, Woosley & El Eid 1985
Fig. 2, and the repo's own Saha solver reproduces it: **[RESULTS]** 2026-07-10
NSE fe56 = 0.69 at Yₑ = 0.467 and 2026-07-11 fe56 = 0.72 at Yₑ = 0.472.]

So the composition arriving at the iron peak is a **direct readout of Yₑ**, and
the ⁵⁶Ni mass — the thing that powers the supernova light curve (Boccioli &
Roberti 2024; Arnett 1982) — is set by how much of the burnt material stayed
near Yₑ = 0.5.

**This is the reason the entire project is organised around Yₑ and not around
⁵⁶Ni.** Yₑ is upstream; ⁵⁶Ni is downstream. An emulator that gets Yₑ right gets
the endpoint right for the right reason. One tuned to reproduce ⁵⁶Ni can be right
about ⁵⁶Ni and wrong about the physics — and will then be wrong about ⁵⁷Ni,
⁵⁸Ni, ⁴⁴Ti and everything else at once, because those *also* depend on Yₑ and the
tuning did not.

### 0.3.4 Hydrostatic versus explosive silicon burning

Tier 2 deferred this and it matters, because the two settings are physically
different and the project's data models one of them.

**Hydrostatic (pre-supernova) silicon burning** is what §0.2.3 described: the
core burns for ~a day (0.01 yr for a 20 M⊙ star in Hix & Thielemann 1999b's
Table 1) at T₉ ≈ 3–4, ρ ≈ 10⁷–10⁹ (Hix & Thielemann 1996 study 3.5–5 GK and
10⁷–10¹⁰ g cm⁻³ as the core-Si-burning cube), cooling by neutrinos, in
quasi-equilibrium, with electron captures having plenty of time to act. Yₑ falls
substantially. The product is the iron core.

**Explosive silicon burning** happens seconds later, when the bounce shock passes
through the silicon and oxygen shells. Conditions: peak T₉ ≈ 4–5+ (Boccioli &
Roberti 2024: incomplete Si burning for 4 < T₉ < 5, full NSE above 5; Hix &
Thielemann 1999a: T₉ᵢ < 5 incomplete), ρ ≈ 10⁷–10⁸, and a duration set by the
*hydrodynamic expansion timescale* — τ_HD = (24πGρ)^{−1/2} = 446 ρ₆^{−1/2} ms
(Fowler & Hoyle 1964, as used by Hix & Thielemann 1999a eq. 1), i.e. 0.05–0.4 s
for ρ = 10⁶–10⁸ g cm⁻³, with the temperature falling on 3τ_HD. The material is
heated, burns, and then expands and cools on that same timescale.

Three differences with real consequences:

| | hydrostatic | explosive |
|---|---|---|
| duration at peak T | ~10⁵ s | ~10⁻¹ s |
| weak reactions | have time; Yₑ drops | **frozen**: Yₑ ≈ inherited value |
| endpoint | true QSE → NSE approach | interrupted; freeze-out matters |
| product | iron core (collapses) | **the ejecta** (observable) |

**The weak-freeze difference is the important one** (Hix & Thielemann 1996 §2:
"the timescales for changes in Yₑ via weak reactions … are much longer than the
timescales for the strong and electromagnetic reactions", so they treat Yₑ as a
constant parameter). Electron-capture rates across the box span 10⁻⁵–10² s⁻¹ per
nucleus (Tier 1 §V.1 table; magnitudes from Langanke & Martínez-Pinedo 2000
Figs. 5–6) [assumed band — the upper decades belong to collapse densities
ρYₑ ≳ 10⁹–10¹⁰; retire by tabulating λ_EC for the §0.7.3 top-20 at the box
corners; an earlier version quoted 10⁻²–10⁰ s⁻¹, inconsistent with Tier 1's own
table]. Over 10⁵ s that changes Yₑ by a lot; over 0.1 s it changes it by ~10⁻²
at most and often much less. So **explosive burning largely inherits the Yₑ that
hydrostatic burning produced** — the Yₑ statement itself is the HT96 timescale
argument above; the shock's *thermodynamic* conditions likewise "are determined
by the pre-explosive structure" (Woosley & Heger 2007) — and the ejecta
composition is a fossil of the pre-supernova core structure.

Which closes the loop on why the project's regime box is the right one: the box
is the hydrostatic-burning box, and hydrostatic burning is what *sets* the Yₑ
that everything downstream inherits. The explosive episode redistributes it into
species but does not create it.

**A caveat the study notes should carry.** The box (T₉ 1.6–7.9, ρ 10⁷–10⁹) is
wide enough to overlap explosive conditions too, and the training data is a Sobol
grid over that box with random compositions — which corresponds to no physical
setting in particular. Whether the induced sampling measure resembles either the
hydrostatic or the explosive trajectory density has never been checked; that is
Tier 2 **R-07**, and §IV.3 shows it is not an academic question.

### 0.3.5 α-rich freeze-out — the third regime

One more setting, because it produces two of the observables in §0.6 and it is
the case where "NSE" most badly misleads.

Material shocked to **high temperature and low density** (T₉ ≳ 5 with
ρ ≲ 10⁷–10⁸ g cm⁻³ — equivalently high radiation entropy; the boundary between
normal and α-rich freeze-out is a line of constant entropy per gram, with
ρ_i ≈ 10⁸ separating the two in Hix & Thielemann 1999a §2 and Fig. 1; the
canonical parameter study is T₉ = 5.5, ρ = 10⁷, s/k ≈ 5, The et al. 1998)
reaches (or nearly reaches) NSE, which at those conditions is dominated by free α
particles and nucleons rather than by the iron peak (Hix & Thielemann 1999b §5)
— high temperature favours the high-entropy, many-particle state. As the
material then expands and cools, the composition tries to follow NSE back down
toward the iron peak. Reassembling α particles into heavy nuclei requires the
**triple-α reaction** (and ⁴He(αn,γ)⁹Be), which is a three-body process and
therefore has a rate ∝ ρ² (Hix & Thielemann 1999a: "the quadratic density
dependence of the rates for α+α+α → ¹²C and α+α+n → ⁹Be"; The et al. 1998). At
low density that rate cannot keep up with the expansion.

The result is a **freeze-out with leftover α particles** — 1–10% by mass (the
⁴He contours of Hix & Thielemann 1999a Fig. 1; 8% in their T₉ = 6, ρ = 10⁷
example) — which then capture onto the iron-peak nuclei that did form.
Consequences:

- extra ⁴⁴Ti (an α-capture product; observable, §0.6.4; The et al. 1998;
  Jordan et al. 2003);
- shifted iron-peak isotopic ratios relative to a normal freeze-out (Hix &
  Thielemann 1999a §5);
- a composition that is *not* NSE and, in the canonical α-rich freeze-out example
  (pure ²⁸Si at T₉ = 5.5, ρ = 10⁷; The et al. 1998, after Meyer, Krishnan &
  Clayton 1998: a QSE with a heavy-nucleus deficit), never fully was, despite
  having passed through NSE conditions.

**Why this belongs in a study document about a network emulator.** It is the
cleanest example of the general rule that **passing through equilibrium
conditions does not make the composition an equilibrium function** — the history
matters, because the *rate* of departure from equilibrium competes with the rate
of change of the conditions. That is the same statement as "QSE is a reduction,
not a solution" (Tier 2 §0.1.1), and the same statement as "NSE-as-a-predictor is
a baseline that has never been run" (Tier 2 **R-16**). It is also, incidentally,
the physical reason that the low-density corner of this project's regime box is
the awkward one — Tier 1 §VIII.C.6's e⁺e⁻ pair problem lives at exactly
(T₉ = 7.9, ρ = 10⁷).

### 0.3.6 The NSE transition — where a network is replaced by a table

There is a boundary inside the regime box that no tier has treated, and it is the
boundary the emulator's *domain* should probably be defined against.

**Some stellar-evolution and supernova hydro codes stop integrating the network
at high temperature — MESA does not.** Above a code-parameter threshold [typical
~5–7 GK; Paxton et al. 2015 §5.2 quote the generic switch ranges as > 3 GK (QSE)
and > 5 GK (NSE); KEPLER's actual parameter not read here] the strong reactions are so fast that
the ODE system becomes maximally stiff, the composition is a function of state to
high accuracy (Hix & Thielemann 1999b: hundreds of abundances "uniquely defined
by the thermodynamic conditions and a single measure of the weak interaction
history"), and integrating it is both expensive and pointless. KEPLER-family
codes (Weaver, Zimmerman & Woosley 1978) and SN Ia/CCSN hydro codes (e.g. Calder
et al. 2007; Seitenzahl et al. 2009; Timmes, Hoffman & Woosley 2000 for the
NSE-energy-generation approach) therefore switch to an **NSE solve or table**:
compute X(T, ρ, Yₑ) from Saha, and evolve only Yₑ through the weak reactions
evaluated on that composition. **MESA does not**: it runs the same in-situ
network at all temperatures — "no NSE or QSE approximation was used; the same 204
isotope reaction network was used throughout" (Paxton et al. 2015 §6.1, and §5.2
for why they avoid the switch: ad-hoc NSE/QSE switching "can introduce unphysical
discontinuities" and instabilities) — and neither does bbq (grep of the r23.05.1
and bbq trees: no NSE control or code path). So the NSE regime below is a
*deployment-host* property, not a universal one. (An earlier version of this
section stated the switch as universal stellar-code behaviour; corrected in the
2026-08-18 audit.)

That is a *different mathematical object* from a network step:

| | network regime | NSE regime |
|---|---|---|
| composition | integrated ODE, path-dependent | algebraic function of (T, ρ, Yₑ) |
| free variables | n abundances | **one** (Yₑ) |
| what is integrated | dY/dt = νR | dYₑ/dt = Σ_weak (…) evaluated at X_NSE (Hix & Thielemann 1999b §5: NSE "requires monitoring of weak reaction activity") |
| cost | stiff implicit solve | one Newton solve on 2 unknowns (Y_p, Y_n; Hix & Thielemann 1999b) |
| stiffness | ≥ 10¹⁴ (Tier 2 §IV.1) | none |

Four consequences the project should be carrying and is not — each scoped, after
the 2026-08-18 audit, to the kind of host.

**(i) For an NSE-switching host, the emulator's competitor above the threshold is
not a network — it is a Saha solve.** And a Saha solve is *fast*: this project's
own batched solver does 27 states with no fallback and agrees with pynucastro to
10⁻¹⁰ dex **[RESULTS]** 2026-07-10. If a host code with an NSE switch would use
NSE at T₉ > 5 anyway, then an emulator competing there is competing with
something already cheap and already exact. This is exactly Tier 2 **R-16** / this
tier's **T-08** (NSE-as-a-predictor as a baseline) arriving from the *deployment*
side rather than the evaluation side, and it is a strong independent argument for
**T-03**'s validity domain. For MESA the competitor at T₉ > 5 is the in-situ
network at its stiffest, and the argument reverts to §0.8's cost case.

**(ii) In NSE-switching hosts the handoff is discontinuous, and the
discontinuity is a physical modelling error nobody in this project has sized.**
At the switch temperature the composition jumps from "whatever the network
integrated" to "exactly NSE". Those differ, because the network was *approaching*
NSE, not at it (§0.3.5's freeze-out is the general form of this). Paxton et al.
(2015 §5.2) describe exactly these discontinuities and instabilities as the reason
MESA avoids the switch; `tier1.md` §VIII.E.6's "unspecified handoff" is the
*emulator ↔ solver* handoff, a different seam. The sharper statement is that
**the transition is where the label generator changes character**, and it sits
inside the regime box.

**(iii) The pathology of §III lives on the wrong side of it — for
NSE-switching hosts.** The Appendix-B-displaced labels are at T₉ ≳ 5 — i.e. in
the band where an NSE-switching host would have handed off and never called the
network at all. For MESA that band is network territory (Farmer et al. 2016 run
204 isotopes to collapse), so the "least deployment-relevant" argument holds only
for NSE-switching hosts, and the benchmark-comparability tip toward **T-03**'s
third option is correspondingly weaker than an earlier version of this section
claimed: if the host does not call a network there, training an emulator to
reproduce buggy labels there costs nothing scientifically and buys benchmark
comparability; if the host is MESA, it does call the network there.

It also has a sharp corollary: **the shipped test trajectories run bbq's network
at temperatures where an NSE-switching stellar code would not (MESA would).** bbq
is a bare burner with no NSE switch, so the dataset explores a regime that one
class of deployment path avoids.

**(iv) Yₑ still evolves in NSE, and that is the *only* thing that evolves.** In
the NSE regime the entire dynamical content is the weak sector — the same 20
channels of §0.7.3 while the Saha composition stays in the Yₑ ≳ 0.46 band
(Paxton et al. 2015 §8 note that NSE-regime weak rates need large isotope pools,
Juodagalvis et al. 2010), evaluated on a Saha composition. An emulator for that regime
would be a very different and much smaller object: a map (T, ρ, Yₑ) → dYₑ/dt,
three inputs and one output. Whether that is worth building separately, and
whether it is in fact the *easiest and most valuable* part of the problem, is not
a question the project has asked.

Registered as **T-21**.

---

## 0.4 The onion, the iron core, and the shell that builds it

### 0.4.1 The structure at the end

A massive star at the end of its life has an onion structure: each burning stage
leaves its ash behind and moves outward as a shell.

```
        ┌──────────────────────────────────────────┐
        │  H envelope            (if not stripped) │
        │  ┌────────────────────────────────────┐  │
        │  │  He shell                          │  │
        │  │  ┌──────────────────────────────┐  │  │
        │  │  │  C/O shell                   │  │  │
        │  │  │  ┌────────────────────────┐  │  │  │
        │  │  │  │  O/Ne/Mg               │  │  │  │
        │  │  │  │  ┌──────────────────┐  │  │  │  │
        │  │  │  │  │  Si/S shell   ◀──┼──┼──┼──┼──┼── SILICON SHELL BURNING
        │  │  │  │  │  ┌────────────┐  │  │  │  │  │   feeds the core
        │  │  │  │  │  │  Fe CORE   │  │  │  │  │  │
        │  │  │  │  │  │ ~1.2-2.0 M⊙│  │  │  │  │  │   [typical: O'Connor & Ott 2011 Table 1 spans 1.24–2.08 M⊙; Sukhbold, Woosley & Heger 2018 max ≈ 2.0]
        │  │  │  │  │  └────────────┘  │  │  │  │  │
        │  │  │  │  └──────────────────┘  │  │  │  │
        │  │  │  └────────────────────────┘  │  │  │
        │  │  └──────────────────────────────┘  │  │
        │  └────────────────────────────────────┘  │
        └──────────────────────────────────────────┘
```

Two features drive everything downstream.

**(i) The iron core is inert and grows.** Nothing exothermic happens in it. It is
supported by degenerate electrons and it is being *fed* by the silicon shell
burning just outside it, which converts silicon to iron-peak material and
deposits it onto the core (Timmes, Woosley & Weaver 1996: the iron core "does
not grow by radiative diffusion, but by a series of convective shell burning
episodes"; Suwa et al. 2018). The core mass is therefore a monotonically
increasing function of time, approaching a limit it cannot exceed.

**(ii) The shell is where the interesting nuclear physics happens, and it is not
in a steady state.** Silicon shell burning is episodic — the shell ignites,
burns, exhausts, contracts, reignites (TWW96: "usually there are just one or two
such episodes"; Heger et al. 2001 place "the most important period for
determining core structure" in silicon shell burning) — and its conditions sweep
through the regime box rather than sitting at a point. The project's per-state,
imposed-(T, ρ) framing is a model of *one call inside one zone inside one
timestep* of that process.

### 0.4.2 The effective Chandrasekhar mass

The core collapses when it exceeds the mass its degenerate electrons can support.
Tier 0 §I.2 and Tier 2 §0.3.1 derive the zero-temperature result; the version
that actually applies has at least two corrections (Timmes, Woosley & Weaver 1996
list finite entropy, GR, Coulomb corrections and the surface boundary pressure).

The cold, fully relativistic limit (Chandrasekhar 1931, 1939; Shapiro & Teukolsky
1983 eq. 3.3.17):

$$
M_{\mathrm{ch}} \;=\; 4\pi\left(\frac{K'}{\pi G}\right)^{3/2}\!\!\left(-\xi_1^2\theta'(\xi_1)\right),
\qquad K' = \frac{\hbar c}{4}(3\pi^2)^{1/3}\left(\frac{Y_e}{m_u}\right)^{4/3},
$$

with the n = 3 Lane–Emden constant −ξ₁²θ′(ξ₁) = 2.018, giving

$$
\boxed{\;M_{\mathrm{ch}} \;=\; 5.83\,Y_e^{2}\,M_\odot.\;}
$$

(the coefficient recomputes to 5.825 with CODATA constants; Timmes, Woosley &
Weaver 1996 eq. 1 and Heger et al. 2001 write 5.83 Yₑ²). Numerically: 1.46 M⊙ at
Yₑ = 0.5, 1.18 at 0.45, 1.03 at 0.42, 0.71 at 0.35 (an earlier version printed
three decimals inconsistent with 5.83 at the 0.1% level; corrected in the
2026-08-18 audit). [derived here] The derivative is

$$
\frac{dM_{\mathrm{ch}}}{dY_e} \;=\; 11.66\,Y_e\,M_\odot \;=\; 5.83\,M_\odot\ \text{per unit } Y_e \text{ at } Y_e = 0.5,
$$

so **δYₑ = 10⁻³ moves M_ch by 5.8 × 10⁻³ M⊙**, and δYₑ = 10⁻² moves it by
0.058 M⊙. Hold onto those two numbers; §0.6.5 needs them.

**Correction 1 — finite entropy raises it.** A hot core supports more mass,
because thermal pressure adds to degeneracy pressure:

$$
M_{\mathrm{ch,eff}} \;\approx\; 5.83\,Y_e^{2}\left[1 + \left(\frac{s_e}{\pi Y_e}\right)^{2}\right] M_\odot ,
$$

with s_e the electron entropy per baryon in units of k (Timmes, Woosley & Weaver
1996, eq. 6, following Baron & Cooperstein 1990; the same expression is eq. 1 of
Heger et al. 2001 and is used by Suwa et al. 2018). At s_e ≈ 1 and Yₑ = 0.45 the
bracket is 1.5 — a 50% correction, not a small one (s_e ranges 0.4–1 across a
15 M⊙ iron core, TWW96, so 50% is an upper-end illustration). So the core mass
at collapse is a *two-parameter* function (Yₑ and entropy), and the entropy is
set by the burning history too (Heger et al. 2001: "the entropy can be just as
important as Yₑ").

**Correction 2 — general relativity, Coulomb corrections and the surrounding
pressure lower it** (Timmes, Woosley & Weaver 1996: SR/GR alone reduce
5.83 Yₑ² to 1.42 M⊙ at Yₑ = 0.5). The real collapse threshold is not a clean
crossing of M_ch; it is a stability question about a core embedded in a star,
with GR corrections, and it is decided by the equation of state's adiabatic
index (§0.5.1).

The honest summary: **M_ch ∝ Yₑ² is the correct scaling and the right way to see
why Yₑ matters, but the pre-supernova core mass in a real model is a
several-parameter outcome of the whole burning history, of which Yₑ is the one
that nuclear burning most directly controls.** Overselling the formula is a real
risk in this project's framing; §0.6.5 is where that risk gets named as an open
item.

### 0.4.3 Compactness: the structural predictor

The observable-facing quantity in the modern literature is not the core mass but
the **compactness parameter** (O'Connor & Ott 2011, ApJ 730, 70):

$$
\xi_{M} \;=\; \frac{M/M_\odot}{R(M_{\mathrm{bary}}=M)/1000\ \mathrm{km}}\bigg|_{t=\text{bounce}},
\qquad \text{usually } M = 2.5\,M_\odot .
$$

It measures how much mass sits inside a given radius — i.e. how steeply the
density falls outside the core (Sukhbold et al. 2016 evaluate it at collapse
onset instead, with little difference). Its usefulness: it correlates with
whether the neutrino-driven mechanism succeeds (§0.5.7): O'Connor & Ott (2011)
find explosion the likely outcome for ξ_2.5 ≲ 0.45 and black-hole formation
above; the two-parameter criterion of Ertl et al. (2016) refines it. High
compactness → a lot of material raining onto the shock at high rate → harder to
explode → black hole. Low compactness → the accretion rate drops sharply after
the core → the shock revives → neutron star and a supernova.

The compactness is set by the mass and entropy structure of the carbon/oxygen
(and silicon) shells at collapse, and it is famously **non-monotonic in
progenitor mass** — the migration of the C- and O-burning shells with mass, and
convective-versus-radiative core burning, produce large changes in ξ_2.5 for
small changes in initial mass (O'Connor & Ott 2011 §4.6; Sukhbold et al. 2016
§7.1; Sukhbold, Woosley & Heger 2018), and hence in the predicted outcome. That sensitivity is *why* the
composition and energetics of late shell burning are worth computing accurately,
and it is the strongest available argument for this project's existence that does
not route through M_ch.

It is also, honestly, an argument the project does not currently make with
numbers. Nobody here has computed ∂ξ_2.5/∂Yₑ or ∂ξ_2.5/∂(network size). §0.6.5
and register item **T-01** are that gap.

### 0.4.4 What pre-supernova Yₑ actually looks like

For orientation [typical; pinned in the 2026-08-18 audit to the central-Yₑ time
series of the 15 and 25 M⊙ models of Heger et al. 2001 (Tables 1–2, Figs 3–5),
the iron-core Yₑ(m) profile of Timmes, Woosley & Weaver 1996 (0.42 at the centre
rising to 0.48 at the core edge), and the MESA 15 M⊙ Yₑ,c ≈ 0.43 of Farmer et al.
2016]:

- **Yₑ = 0.5 exactly** only for material that has never had a weak interaction
  and started from equal N and Z. Not realistic anywhere in a real star: even
  the initial metallicity (¹⁴N → ²²Ne through He burning; Woosley & Heger 2007)
  introduces neutron excess.
- **Yₑ ≈ 0.85–0.87** in a surviving hydrogen envelope — hydrogen has Z/A = 1, so any
  H-rich layer sits nowhere near 0.5. The figures below are for the CO core and
  inward, i.e. everything the network is ever called on; the envelope is outside
  the regime box entirely and is only mentioned so the number is not misread.
- **Yₑ ≈ 0.498–0.499** in the He-burnt but otherwise unprocessed layers (the
  ²²Ne-bearing C/O material; 0.498 at O-depletion in Heger et al. 2001).
- **Yₑ ≈ 0.49–0.50** in the oxygen shell (0.495 at the O-shell epoch, Heger et
  al. 2001).
- **Yₑ ≈ 0.42–0.49** in the silicon-burning region and the iron core, with the
  central value lowest (0.489 at Si ignition → 0.44–0.45 at core contraction in
  Heger et al. 2001; 0.42 → 0.48 across the iron core in Timmes, Woosley &
  Weaver 1996).
- **Yₑ ≈ 0.42–0.43** at the centre at collapse onset in the ~15 M⊙ models (the
  25–40 M⊙ LMP models of Heger et al. 2001 end at 0.445–0.447).

The project's regime box specifies **0.45 < Yₑ < 0.5**, which brackets the
silicon-burning and iron-core range and stops just above the most extreme central
values. The neutron excess η = 1 − 2Yₑ is the more natural variable for the
weak-sector physics: η = 0 at Yₑ = 0.5, 0.02 at 0.49, 0.06 at 0.47, 0.10 at 0.45.
**The box spans η from 0 to 0.1** — i.e. the entire dynamic range of the quantity
runs from zero to ten percent, which is why relative errors in Yₑ are a bad
figure of merit and absolute ones are the right ones. `CLAUDE.md`'s gates are
absolute (|ΔYₑ| ≲ 3 × 10⁻⁶ per step, 5 × 10⁻³ per trajectory); that is the
correct choice and this is the reason.

### 0.4.5 Which stars are these, actually?

Every number in §0.4 is quoted for "a massive star", and the project's one
real-track comparison (Tier 2 §V.2 / **R-07**) uses a **single 20 M⊙ model**.
That is one point in a parameter space with at least four axes, and the axes
matter for which observable in §0.6 even applies.

**Mass.** The pre-supernova core mass, compactness and the burning history are
all non-monotonic in initial mass (§0.4.3; Ertl et al. 2016; Sukhbold, Woosley &
Heger 2018). A conclusion drawn from a 20 M⊙ track
does not automatically transfer to 12 or 30 M⊙, and the *shape* of the
(T, ρ) locus in the regime box — which is what **R-07** measures — is a function
of the progenitor.

**Metallicity.** Metallicity sets the initial CNO abundance, hence the ²²Ne
produced during helium burning, hence the **initial neutron excess** of the
material entering carbon burning (Woosley & Heger 2007). So η at the start of
silicon burning is not zero and is metallicity-dependent. It also sets the
line-driven mass-loss rate, hence whether the hydrogen envelope survives (Heger
et al. 2003: "the principal physics connecting the final evolution of a star to
its metallicity is its mass loss").

**Rotation.** Rotation induces chemical mixing (rotational instabilities feeding
composition across boundaries), enlarges cores, and changes the shell structure
and hence the compactness (Heger et al. 2003; Heger, Langer & Woosley 2000). It
also produces the angular momentum that some explosion mechanisms need.

**Binarity — the axis that changes the observable.** The majority of massive stars
are in binaries that interact (Sana et al. 2012: > 70% of Galactic O stars will
exchange mass with a companion). Interaction strips the hydrogen envelope, which
converts a Type IIP into a Type Ib/c (Heger et al. 2003, Table 1, for the
envelope-mass classification). And §0.6.1's Arnett-rule reading of ⁵⁶Ni
mass **applies to the stripped case and not to the H-rich case** — so the
progenitor's binary history decides which of the two observational readings of
the same nuclear quantity is the right one.

**Why this belongs in a study document about a network emulator.** Two reasons,
both about scope discipline.

1. **The single-track comparison is a sample of size one.** **R-07**'s finding —
   that the 20 M⊙ track sits within 0.12–0.18 dex of a *line* in the regime box,
   and that only 35% / 62% / 82% of the box is within 0.1 / 0.2 / 0.3 dex of a
   visited point (numbers from Tier 2 §V.2 [derived there]; not yet a RESULTS.md
   row) — is a statement about one star. Whether the union over a
   progenitor grid fills the box, or merely traces a family of nearby lines, is
   the question that decides whether the box's uniform sampling measure is
   defensible. Nobody has run it, and it needs no new physics — just more tracks.
   Registered as **T-22**.
2. **"Which observable" is progenitor-dependent**, so a motivation chain that
   ends at "the ⁵⁶Ni mass sets the peak luminosity" has silently assumed a
   stripped-envelope progenitor. §0.6.1 flags this; §0.4.5 is where the
   assumption actually enters.

---

## 0.5 Core collapse, derived end to end

This is the longest derivation in Part 0, and it is here because the project's
entire justification is that Yₑ propagates through it. You cannot judge whether
3 × 10⁻⁶ per step is a sane requirement without knowing what the number feeds.

### 0.5.1 The instability: Γ₁ < 4/3

A self-gravitating sphere is dynamically stable against radial perturbations if
its pressure responds to compression strongly enough. The condition, derivable
from a linear perturbation analysis of the hydrostatic equations, is on the
**adiabatic index**

$$
\Gamma_1 \;\equiv\; \left(\frac{\partial \ln P}{\partial \ln \rho}\right)_{s} ,
\qquad\text{stability requires}\qquad \bar\Gamma_1 \;>\; \frac{4}{3}.
$$

(the pressure-averaged form is textbook — Shapiro & Teukolsky 1983 §6.7 — and the
criterion as the trigger of collapse is Janka 2012.) The 4/3 is not arbitrary. §0.1.2 derived it: for a γ = 4/3 gas the virial theorem
gives E_tot = 0, so the star is marginally bound and an infinitesimal compression
neither costs nor releases net energy. Above 4/3 compression costs energy and the
star springs back; below, compression releases energy and the collapse runs away.

An iron core is supported by **relativistic** degenerate electrons, for which
Γ₁ → 4/3 in the ideal limit (Shapiro & Teukolsky 1983 §2.3). A real core sits a
little above that — partial degeneracy, finite temperature and the residual
electron mass all push Γ₁ up by a few percent [textbook; magnitude assumed] —
while general relativity pushes the *threshold* up by O(GM/Rc²) (§0.4.2's
Correction 2; Chandrasekhar 1964; Janka 2012, 2017 — rotation lowers it
slightly). **Both margins are small, and the point
survives: the pre-collapse iron core is balanced on a knife edge**, not
stable-with-margin, and any physical process that reduces Γ₁ below the threshold
anywhere in the core tips it.

Two such processes are present, and they are the two runaways; which dominates
depends on the core's entropy (Müller 2016: electron capture for the degenerate
low-mass cores, with photodisintegration contributing for the higher-entropy
massive ones).

### 0.5.2 The two runaways

**(a) Photodisintegration of the iron peak.** Above T ≈ 7–10 GK (strongly
density-dependent, and *above* the project's regime box; Janka 2017 places the
onset of substantial disintegration where the central temperature approaches
1 MeV ≈ 10¹⁰ K) the thermal photon bath dismantles iron-peak nuclei:

$$
{}^{56}\mathrm{Fe} \;\to\; 13\,{}^{4}\mathrm{He} + 4n
\qquad Q = -124.4\ \mathrm{MeV} \;=\; -2.22\ \mathrm{MeV/nucleon},
$$

and then, at higher T still, ⁴He → 2p + 2n. That second step costs 7.07 MeV per
*helium* nucleon, which is 13 × 28.30/56 = 6.57 MeV per **iron** nucleon, so the
two steps chain to

$$
2.22 + 6.57 \;=\; 8.79\ \mathrm{MeV/nucleon}
\;=\; \frac{B({}^{56}\mathrm{Fe})}{56},
$$

the total cost of taking iron all the way to free nucleons — which is of course
just ⁵⁶Fe's binding energy per nucleon, and the check that the bookkeeping is
right. [derived here, from AME2020 binding energies: B(⁵⁶Fe) = 492.26 MeV,
B(⁴He) = 28.30 MeV]

This is *endothermic*. It consumes thermal energy, so the temperature (and hence
the thermal contribution to pressure) fails to rise as fast as adiabatic
compression would demand. In the Γ₁ language: energy that should have gone into
pressure goes into breaking nuclei instead, and Γ₁ drops below 4/3 (Janka 2017:
"converts thermal energy to rest-mass energy … causes a reduction of the
effective adiabatic index … below the critical value of 4/3").

> **A caution the study notes should carry**, because it is easy to get wrong.
> This dismantling is a *collapse* phenomenon, not a silicon-burning one. Silicon
> burning at 3–4 GK **produces** the iron peak, and the full dissociation to free
> nucleons that drives Γ₁ below 4/3 requires temperatures above the regime box.
> Tier 0 §I.2 flags exactly this trap.
>
> **But do not over-read that into "the whole box is iron-peak dominated".** The
> top of the box is iron-peak dominated only at its *high-density* edge. NSE
> favours the high-entropy, many-particle state as density falls, so at
> (T₉ = 7.9, ρ = 10⁷) the equilibrium is already α-rich — §0.3.5's freeze-out
> regime — and this file's own witness state 646 (T₉ = 7.78, ρ = 2.0 × 10⁷)
> measures he4 = 0.521 against fe56 = 0.378 under fixed MESA (§III.4). The
> distinction that matters for §0.5.2 is that neither corner has dissociated to
> *free nucleons*, which is the step that costs 8.79 MeV/nucleon.

**(b) Electron capture.** Free protons liberated by (a), and iron-peak nuclei
directly, capture electrons (Langanke & Martínez-Pinedo 2003: both channels
"control the neutronization of the matter"):

$$
e^- + p \to n + \nu_e, \qquad e^- + (Z,A) \to (Z-1,A) + \nu_e .
$$

Each capture does two damaging things at once: it **removes a pressure-supporting
electron** (lowering P at fixed ρ), and it emits a neutrino that — until trapping
sets in (§0.5.4) — **leaves the star entirely**, carrying away energy and entropy
(Janka et al. 2007; Janka 2017). Yₑ drops, so M_ch ∝ Yₑ² drops (Janka 2012: the
inner core "scales with the instantaneous Chandrasekhar mass"), so the core that
was marginally supportable no longer is.

The two reinforce: dissociation makes free protons, which are the best EC targets
per particle — though in aggregate captures on *nuclei* dominate during infall,
because Y_p ~ 10⁻⁶ (Langanke & Martínez-Pinedo 2003; Janka et al. 2007: "what
matters is the product of abundance times capture rate"); EC lowers the
pressure, accelerating contraction, raising T, accelerating dissociation.
Collapse becomes dynamical.

### 0.5.3 The free-fall timescale

Once pressure support is lost, the core falls essentially freely. The
characteristic time is

$$
t_{\mathrm{ff}} \;=\; \sqrt{\frac{3\pi}{32\,G\rho}} ,
$$

giving [derived here; the textbook homogeneous-sphere free-fall time — Janka 2017
quotes the order-of-magnitude form t_ff ~ 0.004 ρ₁₂^{−1/2} s]

| ρ [g cm⁻³] | t_ff |
|---|---|
| 10⁹ | 66 ms |
| 10¹⁰ | 21 ms |
| 10¹² | 2.1 ms |

**The whole collapse takes a few hundred milliseconds** [typical; ~10²–10³ ms in
simulations from the onset at ρ ~ 10¹⁰ g cm⁻³, Janka 2017]. Compare with the
silicon-burning episode that set the initial conditions: the ratio is ~10⁵–10⁷
(a day to two weeks of silicon burning against 0.1–0.3 s of collapse [typical]).
This extreme separation is why the collapse can be treated as taking the composition
as an initial condition — the nuclear network has no time to do anything the
weak reactions do not do — and it is why the accuracy of the *pre-collapse* Yₑ is
what matters.

### 0.5.4 Neutrino trapping — derived, with numbers

Early in the collapse, neutrinos from electron capture stream out freely and Yₑ
falls fast. At some density they stop escaping, and the *lepton fraction* Y_L
freezes (Yₑ itself keeps falling slightly as e⁻ → νₑ inside the trapped core;
Janka 2017). Deriving where that happens is worth doing because the trapped
lepton fraction is the number that sets the homologous core mass.

The relevant opacity is **coherent neutral-current scattering off nuclei**
(Freedman 1974; Langanke & Martínez-Pinedo 2003; Janka 2017), whose cross-section
is enhanced by A² (more precisely ∝ N²) because the whole nucleus scatters in
phase when the neutrino wavelength exceeds the nuclear size:

$$
\sigma_{\mathrm{coh}} \;\approx\; \frac{\sigma_0}{16}\left(\frac{E_\nu}{m_ec^2}\right)^{2} N^{2},
\qquad \sigma_0 = 1.761\times10^{-44}\ \mathrm{cm}^2 ,
$$

(Janka 2017; the coherent-scattering idea is Freedman 1974; the full form
A²[1 − Z/A + (4 sin²θ_W − 1) Z/A]² in place of N² is textbook — Shapiro &
Teukolsky 1983 §18.4 — not in Janka 2017. An earlier version of this
section wrote (σ₀/4)(E_ν/mₑc²)² A²/6, a form found in no source and 2.3–2.7×
too large for ⁵⁶Fe; corrected in the 2026-08-18 audit.) For A = 56, N = 30 and
E_ν = 20 MeV this gives σ ≈ 1.5 × 10⁻³⁹ cm² (1.3 × 10⁻³⁹ with the full factor).
The mean free path is λ = 1/(n_A σ) with n_A = ρN_A/A, and the neutrinos
random-walk out of a core of radius R ≈ 100 km in a diffusion time
t_diff ≈ 3R²/(λc) (R held fixed for the estimate; a 0.5 M⊙ core has R ≈ 130 km
at 10¹¹ and 60 km at 10¹² g cm⁻³). Trapping happens when t_diff exceeds the
dynamical time t_ff:

| ρ [g cm⁻³] | λ [cm] | t_diff [s] | t_ff [s] | trapped? |
|---|---|---|---|---|
| 10¹¹ | 6.1 × 10⁵ | 0.016 | 0.0066 | yes (marginally) |
| 10¹² | 6.1 × 10⁴ | 0.16 | 0.0021 | firmly |

[derived here — an order-of-magnitude calculation with fixed A = 56, E_ν = 20 MeV
and R = 100 km; trapping sets in at a few × 10¹¹ g cm⁻³ (Janka 2017; Langanke &
Martínez-Pinedo 2003) and is complete by ~10¹² g cm⁻³ (Janka et al. 2007; Müller
2016), which this reproduces.] **The A = 56 choice biases the answer in a known
direction**: nuclei in the collapsing core are heavier [typical; A > 65 by
~10¹² g cm⁻³, Janka et al. 2007], and since σ ∝ N² while n_A ∝ ρ/A, the mean
free path goes roughly as 1/(ρA). Using the real A shortens λ and traps
*earlier*, so the densities in the table are upper bounds.

**Consequences.**

1. **The lepton fraction freezes at trapping.** Its value there — Y_L ≈ 0.29–0.30
   with modern capture rates (Yₑ,c ≈ 0.25–0.27; Janka 2012; Müller 2016); the
   classic Bethe 1990 figure Y_L ≈ 0.36–0.39 predates the LMP rates (Tier 2
   §0.3.2) — is the *lepton fraction* Y_L that the inner core carries through the
   rest of the collapse (the trapped neutrinos contribute their own pressure, and
   the relevant conserved quantity becomes Y_L = Yₑ + Y_ν; Janka 2017). An
   earlier version of this item put the value "around 0.35"; corrected in the
   2026-08-18 audit.
2. **The homologous core mass is set by that trapped value**, through the same
   M ∝ Y_L² relation (§0.5.5; Janka 2012; Langanke & Martínez-Pinedo 2003 —
   the sources write the scaling in Yₑ).
3. **Everything the network does before trapping matters; nothing after does.**
   The chain from silicon burning to explosion runs through a single number,
   evaluated once, at the moment the core stops being able to talk to the
   outside.

That is the sharpest available statement of why this project cares about Yₑ.

### 0.5.5 The homologous core and the bounce

During collapse the inner part of the core — where the infall velocity is
subsonic and proportional to radius, v ∝ r — moves **homologously**: it collapses
self-similarly, maintaining its shape (Goldreich & Weber 1980; Yahil 1983; Janka
2017). Outside a sonic point the infall is supersonic and cannot communicate;
that outer material simply rains down.

The homologous core's mass is again set by a Chandrasekhar-like relation, now
evaluated at the trapped lepton fraction:

$$
M_{\mathrm{hom}} \;\approx\; 5.83\,Y_L^{2}\,M_\odot \;\times\;(\text{corrections}),
$$

which at Y_L ≈ 0.3 gives ≈ 0.5 M⊙ [derived here; Janka 2012, 2017 and Müller
2016 give 0.4–0.5 M⊙ for the shock-formation mass; the older 0.7–0.8 M⊙
corresponds to Bethe-1990-era Y_L, and an earlier version of this section used
0.7 M⊙ — corrected in the 2026-08-18 audit]. Collapse continues until the
central density reaches nuclear saturation, ρ ≈ 2.7 × 10¹⁴ g cm⁻³ (Janka 2012,
2017), at which point the nuclear force provides sudden, enormous stiffness: Γ₁
jumps well above 4/3 (Janka 2012).

The inner core overshoots, halts, and **bounces**. The bounce launches a shock at
the *edge of the homologous core* — i.e. at a mass coordinate of ≈ 0.4–0.5 M⊙
(Janka 2012) — inside material that is still falling in at ~0.1c near the sonic
point and up to ~0.3c further out (Janka 2017).

**This is where the whole Yₑ chain lands.** The shock's birth radius, and how much
overlying material it must traverse, are set by M_hom, which is set by Y_L, which
is set by Yₑ at collapse onset, which is set by silicon burning. M_hom ∝ Y_L² is
the squared link; the Y_L ← Yₑ,onset link is O(1) and set by infall electron
capture (Janka 2017: Yₑ drops from ~0.46 to < 0.3 during infall).

### 0.5.6 Why the prompt shock fails — the energy budget

The naive picture (a "prompt" explosion: the bounce shock propagates out and blows
the star apart) does not work (Janka 2012, 2017), and the arithmetic showing why
is short and worth doing.

The shock must traverse the outer iron core — of order 0.5–1 M⊙ of iron-peak
material outside the ~0.4–0.5 M⊙ homologous core [typical; Janka 2012, 2017]; in
fact it stagnates after traversing only 0.3–0.35 M⊙ (Janka 2012) or at an
enclosed mass of around 1 M⊙ (Janka 2017) — and it **dissociates every nucleus it
passes through**, because the post-shock temperature is far above the
dissociation threshold (Janka 2017: "roughly 8.8 MeV per nucleon or 1.7 × 10⁵¹
erg per 0.1 M⊙"). The cost, from §0.5.2, is 8.79 MeV per nucleon, illustrated
for 0.5 M⊙:

$$
E_{\mathrm{diss}} \;=\; \frac{0.5\,M_\odot}{m_u}\times 8.79\ \mathrm{MeV}
\;=\; 8.4\times10^{51}\ \mathrm{erg}.
$$

[derived here] Compare with the energy available to the shock — a few × 10⁵¹ erg
[typical — inferred from Janka 2012: ~1.7 × 10⁵¹ erg per 0.1 M⊙ dissociated and
stagnation after 0.3–0.35 M⊙; the classic estimate is Bethe 1990] — and with
the observed explosion energy of a typical core-collapse supernova, ~10⁵¹ erg
(Burrows & Vartanyan 2021; Woosley & Heger 2007). **The dissociation cost alone
exceeds the shock's entire energy budget by a factor of a few — the shock's
initial energy is spent after only 0.3–0.35 M⊙ (Janka 2012)** (an earlier
version said "by roughly an order of magnitude"; corrected in the 2026-08-18
audit). On top of that, the dissociated free nucleons are excellent
electron-capture targets, so the shocked material rapidly deleptonises and emits
a burst of neutrinos that carries away more energy still (the "neutronisation
burst", ~2 × 10⁵¹ erg within ~20 ms at a peak luminosity near 4 × 10⁵³ erg s⁻¹;
Janka 2017). Whether the burst is causal for the stall is disputed between the
review authorities: Janka (2012) argues stagnation happens before breakout, so
the burst is not causal; Burrows & Vartanyan (2021) rank the burst first and
dissociation second.

The prompt shock **stalls**, typically within tens of milliseconds, at a radius
of ~100–200 km (Janka et al. 2007; Burrows & Vartanyan 2021), and becomes a
standing accretion shock: material continues to fall through it and pile onto
the proto-neutron star.

For context, the energy reservoir that exists but is not being used: the
gravitational binding energy of the newly formed neutron star is

$$
E_{\mathrm{bind}} \;\approx\; \frac{3}{5}\frac{GM^{2}}{R} \;\approx\; 2.6\times10^{53}\ \mathrm{erg}
\qquad (M = 1.4\,M_\odot,\ R = 12\ \mathrm{km}),
$$

i.e. ~96 MeV per baryon, or ~10% of the rest mass. [derived here; the same
Newtonian estimate is Janka 2017's E_b ≈ 3.6 × 10⁵³ (M/1.5 M⊙)² (R/10 km)⁻¹ erg,
and GR estimates give ~2.8–3 × 10⁵³ erg, Lattimer & Prakash 2001] **The
explosion needs < 1% of that (Janka et al. 2007; ≈ 0.4% for 10⁵¹/2.6 × 10⁵³ [derived here])** — though Burrows &
Vartanyan (2021) caution that this "1% tolerance" framing misleads: over the
~1 s during which the explosion energy is set, 4–10% of the emitted neutrino
energy is absorbed in the gain region. The entire core-collapse supernova problem
is the question of how to transfer that small fraction of the available energy
from the neutron star to the overlying material.

### 0.5.7 The delayed neutrino-driven mechanism

The standard answer (Wilson 1985; Bethe & Wilson 1985 — the neutrino idea goes
back to Colgate & White 1966; reviews Janka et al. 2007, Janka 2012): the
proto-neutron star radiates its binding energy as neutrinos of all flavours over
~10 s (the SN 1987A signal lasted ~12 s, and Bayesian fits to it give a total
neutrino energy of a few × 10⁵³ erg, Loredo & Lamb 2002; tens of seconds to full
transparency —
Janka 2017; Janka et al. 2007). A small fraction of those neutrinos — a few
percent of the luminosity during the accretion phase (Janka 2012: "several
percent"; Burrows & Vartanyan 2021 quote 4–10%) — is **reabsorbed** in the
semi-transparent region behind the stalled shock (the "gain region", Bethe &
Wilson 1985), through

$$
\nu_e + n \to p + e^-, \qquad \bar\nu_e + p \to n + e^+ .
$$

The absorbed energy heats the gain region, raising its pressure, and if the
heating exceeds the cooling for long enough, the shock is revived and the
explosion succeeds (Janka et al. 2007; Müller 2016 for the τ_adv > τ_heat
criterion). Modern simulations show the process is aided substantially by
multi-dimensional hydrodynamic instabilities (convection in the gain region —
Herant et al. 1994; Burrows, Hayes & Fryxell 1995 — and the standing accretion
shock instability, Blondin, Mezzacappa & DeMarino 2003) that increase the dwell
time of material in the heating region (Janka 2012).

**Where Yₑ enters, five separate times.** Worth enumerating because the project's
motivation chain usually names only the first:

1. **Pre-collapse core mass** — M_ch ∝ Yₑ² (§0.4.2), setting how much iron there
   is to collapse.
2. **The homologous core mass and shock birth radius** — via Y_L at trapping
   (§0.5.5; Janka 2012: shock formation at 0.4–0.5 M⊙ for Y_L ≈ 0.29–0.30).
3. **The mass the shock must traverse** — the difference between the iron core
   mass (1) and the homologous core mass (2) is precisely the material whose
   dissociation drains the shock (§0.5.6).
4. **The accretion rate history and compactness** — set by the shell structure
   the same burning produced (§0.4.3), which decides whether the delayed
   mechanism has time to work (Burrows & Vartanyan 2021; Ertl et al. 2016;
   Boccioli & Roberti 2024 on the Si/Si–O interface).
5. **The ejecta composition** — the neutron excess of what actually escapes,
   which is what telescopes measure (§0.6).

Items 1–4 are why the emulator matters for *whether the star explodes*; item 5 is
why it matters for *what comes out*. The project's gates are written against
item 5's proxy (Yₑ itself), because 1–4 have no assembled derivative — §0.6.5.

### 0.5.8 The mass cut, and the honest caveat

The **mass cut** is the mass coordinate separating what falls onto the neutron
star from what is ejected. It is not a free parameter of nature but it *is*
effectively a free parameter of piston/thermal-bomb nucleosynthesis calculations
(Boccioli & Roberti 2024 call it "an arbitrary quantity"), because it emerges
from a multi-dimensional simulation nobody runs inside a nucleosynthesis study;
calibrated-engine grids such as Sukhbold et al. (2016) compute it, and Woosley &
Heger (2007) argue it is bracketed by the iron-core edge and by nucleosynthesis
and neutron-star-mass constraints. Material just inside the cut is the most
neutron-rich (deepest, most processed), so the cut's location strongly affects
the ejected iron-peak composition and the ⁵⁶Ni mass (Woosley & Heger 2007; The
et al. 1998 for ⁴⁴Ti).

**Why this matters for how the project frames its claims.** A chain of the form

> better network → better Yₑ → better M_ch → better explodability → better
> ⁵⁶Ni prediction

has, at the "explodability" and "⁵⁶Ni" links, dependencies on the explosion
mechanism and mass cut that are *larger and less well constrained* than the
composition improvement being sold. The defensible framing is narrower and still
strong:

> A stellar-evolution code currently uses a network too small to get the
> pre-collapse Yₑ and shell structure right, and *knows* it (§0.8.2). An
> emulator that removes that compromise improves the **initial condition** every
> downstream calculation starts from, whatever mechanism the downstream
> calculation then assumes.

That version survives referee contact. The longer chain is a motivation, not a
claim, and the study notes should keep the distinction visible — which is
exactly what Tier 2 §0.3.5 / **R-14** is about.

### 0.5.9 What "explodability" actually means operationally

**T-01** asks for ∂(explodability)/∂Yₑ. Before that can be a well-posed request
you have to know what computes explodability, and the answer explains why the
derivative is hard to get and why it may not be the right thing to ask for.

**What a modern core-collapse simulation is.** The state of the art couples
relativistic hydrodynamics to **neutrino transport** — the hard part, since the
neutrinos are the energy carrier (§0.5.7) and their transport is a 6-dimensional
Boltzmann problem (3 space + 2 angle + 1 energy) per flavour (Müller 2016;
Couch, Warren & O'Connor 2020). Practical schemes truncate it: two-moment (M1)
closures, ray-by-ray approximations, IDSA, or full Boltzmann in reduced
dimensionality (also leakage and flux-limited diffusion; Müller 2016 §on
neutrino transport). A 3D simulation of one progenitor to ~1 s post-bounce costs
millions of node-hours, i.e. ≳ 10⁷ core-hours (Couch et al. 2020; Burrows &
Vartanyan 2021: "a year on a supercomputer"). **You cannot run a grid of
those.**

**So explodability is computed by proxies**, and there are three families:

| method | what it does | what it costs |
|---|---|---|
| **1D with a calibrated parametrisation** (PUSH, STIR, "neutrino light-bulb" / calibrated inner-boundary engines) | run 1D with an added, calibrated ingredient — extra heating (PUSH, Perego et al. 2015; light-bulb / calibrated engines, Ugliano et al. 2012, Sukhbold et al. 2016) or MLT-turbulence terms fitted to 3D (STIR, Couch et al. 2020) — so that models explode when the calibration set says they should | grids of ~200 progenitors are routine (Sukhbold et al. 2016; Couch et al. 2020) [per-model cost of hours: assumed] |
| **semi-analytic criteria** | compare a heating timescale with an advection timescale (Müller 2016), or evaluate a critical-luminosity condition (Burrows & Goshy 1993; Pejcha & Thompson 2015); the **compactness** ξ_2.5 (§0.4.3; O'Connor & Ott 2011) is the crudest of these | seconds |
| **full multi-D** | the real calculation | ≳ 10⁷ core-hours each (Couch et al. 2020) |

**The crucial structural fact: explodability is a threshold on a non-monotonic
function.** 1D simulations of most progenitors do *not* explode without help
(except the lowest-mass, ECSN-like cores; Janka 2012; Couch et al. 2020; Burrows
& Vartanyan 2021); whether a given star explodes depends on whether the accretion
rate drops fast enough at the right moment, which depends on the shell structure,
which is non-monotonic in progenitor mass (Ertl et al. 2016; Sukhbold, Woosley &
Heger 2018). The outcome map "initial mass → explodes or not" is famously
**islands, not a boundary** (Ugliano et al. 2012; Ertl et al. 2016; Sukhbold et
al. 2016 — though the island locations disagree between methods, Boccioli &
Roberti 2024).

Two consequences for the project's motivation.

**(i) ∂(explodability)/∂Yₑ is not a derivative of a smooth function.** Near a
threshold it is a delta function; away from one it is zero. The scientifically
meaningful quantity is not the derivative but something like *the probability
that a δYₑ perturbation flips the outcome*, integrated over a progenitor
population — which requires a grid, which requires the parametrised 1D methods,
which are themselves calibrated. That is a real research programme, not a
literature lookup. **T-01 should therefore be split**: the ⁵⁶Ni and isotopic-ratio
derivatives are extractable from published yield tables (cheap, do it); the
explodability derivative is not (expensive, and the honest move is to stop
claiming it).

**(ii) The parametrised-1D grids are exactly where the emulator would be
used.** Those grids consume presupernova model sets that were run to core
collapse hundreds of times (Sukhbold et al. 2016 and Couch et al. 2020 both use
the same ~200 KEPLER progenitors) — i.e. someone pays the network cost hundreds
of times, in the phase where it dominates (§0.8.2). **That is the deployment story with the clearest economics**, and it is
better than the vaguer "improve the initial condition" framing of §0.5.8, because
it names a workload that exists, is compute-bound, and is run by people who would
notice a 20× speedup. It should be in the project's motivation and is not.
Registered as **T-23**.

---
## 0.6 The observable end

The chain has to terminate in something measurable, or the project is engineering
rather than science. This section is what the measurements are, how they connect
to Yₑ, and — at the end — the derivative nobody has assembled.

### 0.6.1 ⁵⁶Ni and the light curve

The supernova's optical display is powered by radioactive decay of the iron-peak
material the explosion synthesised. The chain:

$$
{}^{56}\mathrm{Ni} \xrightarrow{\ t_{1/2} = 6.075\ \mathrm{d}\ } {}^{56}\mathrm{Co}
\xrightarrow{\ t_{1/2} = 77.24\ \mathrm{d}\ } {}^{56}\mathrm{Fe} .
$$

Both steps are weak, and they are **not the same weak channel**: ⁵⁶Ni decays by
electron capture essentially 100% (its β⁺ branch is 1.3 × 10⁻⁵), while ⁵⁶Co is
≈80% EC and ≈20% β⁺ (ENSDF via the IAEA Live Chart: β⁺ 19.7%, EC 80.3%; half-lives
6.075 d and 77.24 d — ENSDF, retrieved 2026-08-18). Given how carefully Tier 2 §I.5 separates the
lepton ledgers for β⁺ versus EC, this distinction is worth keeping straight.

The specific energy deposition rates are ε_Ni ≈ 3.9 × 10¹⁰ and
ε_Co ≈ 6.8 × 10⁹ erg g⁻¹ s⁻¹ at t = 0 (Nadyozhin 1994; re-derived here from the
ENSDF mean energies per decay, 1.735 and 3.739 MeV: 3.95 × 10¹⁰ and
6.70 × 10⁹). **Arnett's rule** (Arnett 1982) — the statement that at light-curve
peak the luminosity approximately equals the instantaneous radioactive energy
deposition rate — then gives, for M(⁵⁶Ni) = 0.07 M⊙ [typical of neutrino-driven
models above ~12 M⊙, Sukhbold et al. 2016; SN 1987A: 0.072–0.077 M⊙], a peak
time ~18 days [typical of stripped-envelope events; Lyman et al. 2016, not opened
here], and the *mean* lives τ = t₁/₂/ln 2 (τ_Ni = 8.76 d, τ_Co = 111.4 d; Diehl et
al. 2015 quote "τ ∼ 8 days" and "τ ∼ 111 days"):

$$
L_{\mathrm{peak}} \;\approx\; M_{\mathrm{Ni}}\left[\varepsilon_{\mathrm{Ni}}e^{-t/\tau_{\mathrm{Ni}}} + \varepsilon_{\mathrm{Co}}\left(e^{-t/\tau_{\mathrm{Co}}} - e^{-t/\tau_{\mathrm{Ni}}}\right)\right]
\;\approx\; 1.4\times10^{42}\ \mathrm{erg\ s^{-1}} .
$$

[derived here — 1.38 × 10⁴² recomputed with the mean lives; using the half-lives
in the exponents would give 9.8 × 10⁴¹; right order of magnitude for a
stripped-envelope event]

**A qualification that matters and is routinely botched.** Arnett's rule applies
at *peak* to **stripped-envelope** supernovae (Types Ib/c), where there is no
hydrogen envelope and the light curve is radioactivity-powered throughout. A
20 M⊙ progenitor that retains its envelope produces a **Type IIP**, whose plateau
is powered by hydrogen recombination (Popov 1993; Kasen & Woosley 2009) — there
⁵⁶Ni sets the post-plateau radioactive tail and modulates the plateau *length*,
not the peak luminosity (Kasen & Woosley 2009; Nakar, Poznanski & Katz 2016).
Tier 2 §0.3.3 makes this point; it is repeated here because "⁵⁶Ni mass sets the
peak brightness" is a sentence that will be wrong for most of the events this
project's progenitors produce.

Either way, the connection to Yₑ is direct: **Yₑ sets how much of the ejecta
reaches ⁵⁶Ni rather than ⁵⁴Fe or ⁵⁸Ni** (§0.3.3; Woosley & Heger 2007), so the
⁵⁶Ni mass — a comparatively well-determined nucleosynthetic quantity (Sukhbold
et al. 2016 call the SN 1987A and Crab ⁵⁶Ni masses "fairly well determined") —
is a readout of the neutron excess of the
burnt material.

### 0.6.2 Isotopic ratios and the neutron excess

The sharper observables are ratios, because they cancel much of the dependence on
the total ejected mass and the mass cut.

- **⁵⁷Ni/⁵⁶Ni** (observed as ⁵⁷Co/⁵⁶Co in the late light curve, since ⁵⁷Ni →
  ⁵⁷Co → ⁵⁷Fe). ⁵⁷Ni has one extra neutron, so its yield relative to ⁵⁶Ni
  increases with the neutron excess η = 1 − 2Yₑ [assumed — standard], but it is
  nonzero at η = 0 and set by the freeze-out type (Seitenzahl, Timmes &
  Magkotsios 2014, Fig. 1, computed at Yₑ = 0.5 exactly). Measured in SN 1987A
  from the light-curve tail shape (Seitenzahl et al. 2014: 2.5 ± 1.1 × solar)
  and directly from the ⁵⁷Co γ-lines (Kurfess et al. 1992: 1.5 ± 0.3 ± 0.2 ×
  solar).
- **⁵⁸Ni/⁵⁶Fe** and **⁵⁴Fe/⁵⁶Fe** in the solar abundance pattern. The Sun's
  iron-peak isotopic composition is a stringent constraint on the *average* Yₑ of
  all the core-collapse ejecta that ever enriched the interstellar medium.
  Overproducing the neutron-rich iron-peak isotopes relative to solar is a
  classic failure mode of supernova nucleosynthesis models (Woosley & Heger
  2007: a mass cut deeper than the iron core gives "unacceptable overproductions
  of ⁵⁴,⁵⁸Fe"), and it is a direct Yₑ diagnostic.
- **⁴⁴Ti**, produced in α-rich freeze-out (§0.3.5; The et al. 1998) and observed
  as γ-ray lines from Cas A (Grefenstette et al. 2014) and SN 1987A (Boggs et al.
  2015). Sensitive to the freeze-out conditions and hence to the shock energetics
  and mass cut as well as to Yₑ.

The general shape: **η ranges over 0–0.10 across the regime box (§0.4.4), and the
neutron-rich isotopic yields are roughly proportional to η.** The amplification
follows from η = 1 − 2Yₑ, so δη = 2 δYₑ and

$$
\frac{\delta\eta}{\eta} \;=\; \frac{2\,\delta Y_e}{1-2Y_e}
\;=\; \frac{2Y_e}{1-2Y_e}\cdot\frac{\delta Y_e}{Y_e}
\;\approx\; 49\times\frac{\delta Y_e}{Y_e}
\quad\text{at } Y_e = 0.49 .
$$

So a *fractional* error in Yₑ of 10⁻³ near Yₑ = 0.49 (i.e. δYₑ = 4.9 × 10⁻⁴) is a
**4.9% error in η**, and a 4.9% error in the yields that depend on it. *That* is
the correct way to see why absolute Yₑ accuracy at the 10⁻³–10⁻² level is
scientifically meaningful: the small quantity is η, not Yₑ, and near the
neutron-poor end of the box a relative error in Yₑ is amplified by ~50 into a
relative error in the observable. Solar isotopic ratios are known to percent
precision; individual-supernova ratios (⁵⁷Ni/⁵⁶Ni in SN 1987A) to ~20–40%.

[The η-linearity claim is an approximation valid for the mildly neutron-rich
isotopes — and, since the ⁵⁷Ni/⁵⁶Ni ratio is nonzero at η = 0 (Seitenzahl et al.
2014), the 49× lever is an upper bound on the sensitivity; it is not a
substitute for the missing derivative in §0.6.5. Tagged **[derived here —
approximate]**.]

### 0.6.3 Galactic chemical evolution

Zoom out. Core-collapse supernovae are the dominant source of the α elements
(O, Ne, Mg, Si, S, Ca) and a major source of the iron peak; Type Ia supernovae
contribute roughly half of the iron-peak elements, on a delayed timescale
(Kobayashi, Karakas & Lugaro 2020). The observed [α/Fe] versus [Fe/H] trend in
Galactic stars — a plateau at low metallicity followed by a downturn — is the
fingerprint of that timing difference (Tinsley 1979; Kobayashi et al. 2020).

The relevance here: **GCE models take supernova yields as inputs, integrated over
an initial mass function** (Kobayashi et al. 2020). The yields are computed from progenitor models whose
pre-supernova structure and composition come from stellar-evolution codes running
nuclear networks. A systematic error in the network's Yₑ propagates into every
yield table, into every GCE model that uses it, and into the inferred history of
the Galaxy. That is a genuinely large lever, and it is the argument that survives
even if one is sceptical about explodability predictions.

It is also an argument with a specific vulnerability: yield tables are dominated
by uncertainties in the explosion mechanism and mass cut (§0.5.8), and the
composition improvement this project offers sits underneath those. The correct
claim is *reducing one identified systematic in the input*, not *fixing yield
tables*.

### 0.6.4 Remnants: the two objects everyone cites

**SN 1987A.** The only core-collapse supernova with detected neutrinos (~24
events: 11 in Kamiokande II, Hirata et al. 1987; 8 in IMB, Bionta et al. 1987;
5 in Baksan, Alekseev et al. 1988; review Janka 2017), which confirmed the basic
energetic picture — total neutrino energy of a few × 10⁵³ erg ("some 10⁵³ erg",
Janka 2017) over ~10 s (the signal spanned about 12 s), matching §0.5.6's
neutron-star binding energy to within the uncertainties. Its light curve gave
M(⁵⁶Ni) ≈ 0.07 M⊙ [sourced: 0.072–0.077 M⊙, Utrobin et al. via Sukhbold et al.
2016], and its late-time tail constrained ⁵⁷Ni/⁵⁶Ni (Seitenzahl, Timmes &
Magkotsios 2014).

**Cassiopeia A.** A ~350-year-old remnant (explosion date 1681 ± 19, Fesen et
al. 2006), spatially resolved, with X-ray and γ-ray maps of individual elements
including ⁴⁴Ti (Grefenstette et al. 2014). It shows that the ejecta are strongly
asymmetric (Milisavljevic & Fesen 2013; Grefenstette et al. 2014) and that the
iron-peak material is not distributed as a spherical model would predict — a
reminder that the one-dimensional chain in §0.5 is a caricature of a
three-dimensional process.

Both are cited in this project's framing as the observational anchors of the Yₑ
chain. Both deserve the caveat that they constrain the *combination* of
progenitor structure, explosion mechanism and mass cut, and that isolating the
nuclear-network contribution from them has not been done here.

### 0.6.5 ⚠ The derivative nobody has assembled

Everything above is qualitative. The quantitative link — what error in Yₑ changes
a scientific conclusion — has never been assembled in this project, and it is the
weakest joint in the motivation.

What exists:

$$
\frac{dM_{\mathrm{ch}}}{dY_e} \;=\; 5.83\ M_\odot \text{ per unit } Y_e \text{ at } Y_e = 0.5
\qquad\text{(§0.4.2, derived)}
$$

and the operative per-step gate, |ΔYₑ| ≲ 3 × 10⁻⁶, which comes from dividing the
**weak-rate-physics shift** (5 × 10⁻³ to 1.5 × 10⁻² — Heger, Woosley,
Martínez-Pinedo & Langanke 2001: the amount by which the central Yₑ at core
collapse of their LMP + β-decay models exceeds the WW95/FFN models', about half
from adding β-decays and half from the smaller LMP capture rates; the project
reads it as "per trajectory") by N ≈ 1.6 × 10³ steps under a
systematic-accumulation assumption (Tier 2 §0.3.4).

Note what that is: **an input uncertainty used as an output tolerance.** The
logic — "an emulator whose error is below the disagreement between two defensible
rate libraries is not the limiting factor" — is sound as a *floor*, and it is the
right way to set one. But it says nothing about what error would change a
conclusion, because

$$
\frac{\partial M({}^{56}\mathrm{Ni})}{\partial Y_e},\qquad
\frac{\partial\,\xi_{2.5}}{\partial Y_e},\qquad
\frac{\partial(\text{explodability})}{\partial Y_e},\qquad
\frac{\partial(\text{isotopic ratios})}{\partial Y_e}
$$

have not been measured here, cited from the literature, or estimated. The chain
in §0.5 stops at "shock birth radius" and resumes at "observed ⁵⁶Ni" with nothing
connecting them numerically.

Why closing it is worth the day it would take:

- **It could move the gate by orders of magnitude in either direction.** If
  explodability is insensitive to δYₑ at 10⁻³, the 3 × 10⁻⁶ per-step gate is
  over-engineered by a factor of hundreds — and the project is paying enormously
  for it (Tier 2 §IV.9's cost wall is downstream of exactly this demand). If some
  observable is sensitive at 10⁻⁴, the gate is right and should be defended
  loudly.
- **It is the referee's first question.** "You built a 3 × 10⁻⁶-per-step
  emulator. What observable changes at 3 × 10⁻⁶?" The current answer routes
  through an input uncertainty. That is a defensible proxy and it is not an
  answer.
- **Much of it is sourceable rather than computable.** Progenitor and explosion
  model grids in the literature vary Yₑ (usually implicitly, through metallicity,
  rotation, or rate choices) and report yields. The derivative may be extractable
  from published tables without running anything.

Carried as Tier 2 **R-14** and as this tier's **T-01**. It is the justification
for the project's most expensive requirement, and it is missing.

### 0.6.6 The error hierarchy — what the emulator is actually competing with

§0.6.5 asks how accurate the emulator needs to be. This section asks the
complementary and more uncomfortable question: **how accurate is everything
else?** An improvement that lands two orders below the dominant error term is
real engineering and not a scientific result, and the only way to know which
situation you are in is to assemble the terms.

Ranked by size, for the pre-supernova Yₑ and composition of a massive-star model:

| # | error term | size (in Yₑ or its consequences) | status |
|---|---|---|---|
| 1 | **3D convection vs MLT** — entrainment, shell mergers, the burning/mixing competition (Meakin & Arnett 2007; Couch et al. 2015; Müller et al. 2016) | qualitative changes to shell structure and yields; **not expressible as a δYₑ** | §0.2.5; unquantified anywhere |
| 2 | **explosion mechanism + mass cut** (for ejecta quantities only) | dominates all ejecta composition claims | §0.5.8 |
| 3 | **progenitor parameters** (mass, Z, rotation, binarity) | the spread across a progenitor grid | §0.4.5 |
| 4 | **weak-rate physics** (WW95/FFN → LMP + β-decays) | **5 × 10⁻³ – 1.5 × 10⁻² per model** in central Yₑ at collapse (about half from adding β-decays, half from smaller LMP capture rates) | sourced (Heger et al. 2001), adopted as the project's floor |
| 5 | **network size** (approx21 vs mesa_80 / mesa_151) | the term this project removes: the NNN improves Yₑ over approx21 by 377–651% (mesa_80) / 277–390% (mesa_151); the NNN's own per-step Yₑ error is ≈ 2.4 × 10⁻³ absolute (0.33–0.54% relative on mesa_80), so the approx21 error it improves on is correspondingly (4–7×) larger | **[RESULTS]** 2026-07-08, §VI.2 |
| 6 | **rate uncertainties within a library** (Hauser–Feshbach factor ~2 on unmeasured channels; Rauscher & Thielemann 2000: "within a factor of 1.5–2") | unpropagated | `tier1.md` §VIII.C.1 |
| 7 | **emulator target** | 3 × 10⁻⁶ per step → 5 × 10⁻³ per trajectory | the gate |
| 8 | **conservation drift** | ≤ 10⁻¹² per step | measured 0.0 |

Read the table honestly and three things follow.

**(i) The project's gate is set *equal to* term 4 and is therefore correctly
placed relative to the input physics.** The design logic — do not be the limiting
factor — is sound, and rows 7 and 4 agreeing at the trajectory level is exactly
the intended relationship. Row 8 being six orders below row 7 is why conservation
is free.

**(ii) But rows 1–3 are larger and are *not* reduced by anything this project
does.** The defensible claim is therefore narrow and should be stated in this
form: **the project removes term 5 and pushes term 7 below term 4.** It does not
improve the pre-supernova model's total accuracy, because that is dominated by
terms 1–3. What it *does* is remove a term that is (a) currently large, (b)
entirely artificial — a compute compromise rather than a physical uncertainty —
and (c) removable at no accuracy cost, which none of terms 1–3 are.

That distinction — **artificial versus physical error** — is the strongest
framing available and it is not the one the project currently uses. An artificial
error is one you would not make if compute were free. Removing artificial error
is exactly what surrogate modelling is *for*, and it does not require beating the
physical uncertainties to be worth doing.

**(iii) Term 6 is the one that could embarrass the project.** If unmeasured
Hauser–Feshbach rates carry factor-2 uncertainties on channels that matter for
Yₑ, then a 3 × 10⁻⁶ emulator and a 3 × 10⁻⁴ emulator produce indistinguishable
science, and the gate is over-engineered by two orders. `tier1.md` §VIII.C.1 has
been open since Tier 1 and the machinery to close it (perturb rates, re-integrate,
measure δYₑ) is entirely built — the batch engine evaluates every rate and the
reference integrator exists.

**Term 6 is the cheapest of the three ways to answer "is the gate right?"** — the
other two being **T-01** (the output derivative, partly infeasible per §0.5.9)
and **R-11** (the operator-split comparison). It should be first.

Registered as **T-20** (assemble the hierarchy as a project document) and it
promotes `tier1.md` §VIII.C.1 to the top of the cross-tier list.

---

## 0.7 Where Yₑ comes from — the weak sector, quantitatively

§0.3–0.6 established that Yₑ is the quantity. This section is where it actually
changes, which is the sector this project's invariants protect most fiercely.

### 0.7.1 The identity, and what can move it

From the definitions (Tier 0 §II.5),

$$
Y_e \;=\; \sum_i Z_i Y_i \;=\; \sum_i \frac{Z_i}{A_i}X_i ,
$$

and the key structural fact:

> **No strong or electromagnetic reaction can change Yₑ.** They conserve Z and A
> separately, so ΣZᵢ dYᵢ = 0 identically for every strong/EM column of ν.

Nullity ≥ 2 follows by construction (strong and electromagnetic reactions
conserve Z and A separately; Langanke & Martínez-Pinedo 2003 §I); that the left
null space of ν restricted to strong/EM columns is *exactly* 2-dimensional and
equals span{A, Z} — the strong subgraph is connected — is measured in Tier 2
§I.2.1 (no RESULTS.md row yet: RESULTS 2026-07-08 logs the full-ν nullity 1
only). So
**every bit of Yₑ evolution comes through the weak columns**, which are 46 of 607
in mesa_80 and 173 of 1518 in mesa_151 **[RESULTS]** 2026-07-09.

Three consequences that shape everything:

1. **Invariant #2 is structural, not stylistic.** Masking a weak column as
   "equilibrated" does not lose a little accuracy; it deletes part of the only
   channel that can produce the signal. And weak reactions are *not* in detailed
   balance in this regime — the inverse of an electron capture is neutrino
   absorption on the daughter, and the neutrinos have already left the star (no
   final-state neutrino blocking; Langanke & Martínez-Pinedo 2000 set S_ν = 0
   for exactly this reason); the Z-restoring channels — β⁻ decay and positron
   capture — are separate reactions with their own phase space, not the
   time-reverse of EC. There is nothing to balance against. (An earlier version
   called positron capture "the inverse" of EC; corrected in the 2026-08-18
   audit.)
2. **κ ≡ 1 on weak columns, structurally**, because the engine stores them
   unpaired (f⁻ ≡ 0). Verified exactly on 8.8 million / 33.2 million (weak column
   × relaxed row) samples with f⁺ > 0 **[RESULTS]** 2026-07-12. So weak columns
   are automatically in any {κ > threshold} active set — the 95% Yₑ-coverage gate
   passes at 1.0000 *structurally* (§IV.4).
3. **The signal is small and rides on top of large strong-sector activity.** The
   strong sector moves individual Yᵢ by O(1) relative amounts while leaving Yₑ
   exactly invariant; the weak sector moves Yₑ by ~10⁻³ over a label-length
   trajectory segment (and by several × 10⁻² over the whole Si-burning-to-collapse
   evolution; Heger et al. 2001). A
   model that gets the strong sector slightly wrong in a way that *leaks* into
   the charge row destroys the signal. That is Tier 2 §0.4's entire argument for
   conservation-by-construction, and this is the physical reason it bites.

### 0.7.2 Electron capture in a degenerate plasma — why it is (nearly) a one-way ratchet

The rate of electron capture on a nucleus depends on the number of electrons
above the capture threshold. In a degenerate plasma the electrons fill states up
to E_F, so the rate is controlled by whether E_F exceeds the threshold energy
Q_EC — and E_F rises with density as ρ^{1/3} (§0.1.4; Langanke &
Martínez-Pinedo 2003 §IV).

$$
\lambda_{\mathrm{EC}} \;\propto\; \int_{Q_{\mathrm{EC}}}^{\infty} \!\!(E - Q_{\mathrm{EC}})^{2}E^{2}\,f(E,\mu_e,T)\,dE
\quad\xrightarrow[\text{degenerate}]{}\quad \lambda \sim \frac{\ln 2}{K}\,\frac{(E_F - Q)^{5}}{(m_ec^2)^5}\ \text{-ish},
$$

i.e. a steep (roughly fifth-power) sensitivity to how far the Fermi energy
exceeds threshold [derived here from the LMP phase-space integral — Langanke &
Martínez-Pinedo 2000, eq. 5a: the exact integrand is w p (Q + w)² F(Z, w) S_e;
the ~E⁵ sensitivity is stated in Langanke & Martínez-Pinedo 2003 §IV; it is
(E_F − Q)⁵ far above threshold and ∝ (E_F − Q)³ just above it; Tier 0 §0.1.5
does this properly]. The practical consequences:

- **Rising density switches EC on hard.** As the core contracts, E_F rises,
  crosses thresholds one nucleus at a time, and the capture rates jump by orders
  of magnitude (Suzuki, Toki & Nomoto 2016: 3–4 orders over Δlog₁₀ ρYₑ = 0.02 at
  a threshold). Yₑ falls faster as the collapse proceeds — the runaway of §0.5.2.
- **The restoring channels — β⁻ decay and positron capture — are suppressed**:
  β⁻ decay is **Pauli-blocked** in a degenerate plasma, since the emitted
  electron must find an empty state above E_F, and there are few (Langanke &
  Martínez-Pinedo 2003). So the restoring force is suppressed exactly where the
  driving force is strongest.
- **Therefore Yₑ ratchets downward** — monotone-non-increasing to a good
  approximation once E_F ≫ typical Q. During Si burning at ρ ~ 10⁷–10⁹ g cm⁻³,
  however, β⁻ decay can balance EC for a period (Heger et al. 2001: β-decay
  balances electron capture around log(t_b − t) = 3.5–4.5 in the 15 M⊙ model, and
  accounts for about half of the ΔYₑ = 0.005–0.015 by which the new models'
  central Yₑ at collapse exceeds WW95's), so the strict ratchet is a
  collapse-phase statement; what the gate arithmetic needs is the *sign* of the
  bias, not irreversibility (an earlier version said Yₑ "essentially never goes
  back up in this regime"; corrected in the 2026-08-18 audit). Any error in the
  weak sector accumulates in a preferred direction — which is precisely the
  "systematic" row of the accumulation trichotomy (Tier 0 §IV.3) and the reason
  the per-step gate is set by N·δ rather than √N·δ (Tier 2 §0.3.4).

**And this is where the two networks differ most.** mesa_80 contains only 6 of 9
electron-capture controllers and **0 of 8** β-decay partners of the Yₑ-controller
set **[RESULTS]** 2026-07-08. It lacks the β⁻ partners of the named Yₑ
controllers (it does carry 19 β⁻ channels elsewhere — RESULTS 2026-07-08
weak-sector breakdown), a more extreme form of the asymmetry than the physics
itself imposes. Tier 0 §I.4 asks
you to predict the bias direction from that; the answer is that mesa_80 should
over-drive Yₑ downward relative to mesa_151 in any regime where the missing
β-decay partners are populated.

That is a *testable prediction about the dataset* which, as far as these notes
can tell, has never been run. Registered here as **T-02**.

### 0.7.3 The measured Yₑ carriers

On the relaxed manifold, in the high-Yₑ QSE window, the |dẎₑ| budget is
extremely concentrated **[RESULTS]** 2026-07-12:

| rank | mesa_80 | share | mesa_151 | share |
|---|---|---|---|---|
| 1 | ⁵⁶Ni EC | 0.62 | ⁵⁶Ni EC | 0.28 |
| 2–5 | ³¹S EC, ⁵²Fe EC, p EC | → 0.96 cumulative | (ditto class) | → 0.75 |
| top-20 | | **1.00** | | **1.00** |

Twenty channels out of 46/173 weak columns carry essentially the entire Yₑ
signal, and one channel carries a majority of it in mesa_80. Two design
consequences follow directly and are already in the project's plan:

- **Loss weighting** should be concentrated on those channels (a flat per-column
  loss would spend almost all its capacity on columns that do not matter for the
  headline quantity).
- **The ⁵⁶Ni EC rate's uncertainty is a first-order term in the emulator's error
  budget**, on par with everything the model itself does. That is the
  rate-uncertainty → Yₑ propagation flagged as `tier1.md` §VIII.C.1 and still
  open.

Note the contrast with the *training* distribution, where the #1 carrier is
Ne18 → F18 EC — a proton-rich fast capture that exists because the Sobol
compositions are random and proton-loaded, not because it happens in a star
**[RESULTS]** 2026-07-10. The Yₑ physics on the training grid is not the Yₑ
physics of silicon burning. §IV.3 again.

---

## 0.8 The computational setting

The last piece of motivation: why any of this needs an emulator.

### 0.8.1 What MESA actually does per timestep

A stellar-evolution code advances a 1D model of hundreds to thousands of zones
(Paxton et al. 2011 §6.1). Per timestep, per zone, it must:

1. solve the structure equations (hydrostatic balance, energy transport, energy
   conservation) implicitly and simultaneously across all zones;
2. call an **equation of state** for P, internal energy, and their derivatives,
   given (ρ, T, composition) — needing Ā and Z̄, hence needing ΣXᵢ = 1 to mean
   something (Tier 2 §0.5);
3. call **opacities**;
4. call the **nuclear network** to advance the composition over Δt and return
   e_nuc and ε_ν;
5. handle mixing (convection, overshoot, semiconvection) as a diffusion problem
   on the composition (Paxton et al. 2011 §6; Jermyn et al. 2023).

Step 4 is the one this project replaces. It *can be* operator-split from the
rest: MESA's default is a fully coupled Newton solve of structure and composition
together (Paxton et al. 2011 §6.1: MESA "does not require the structure equations
to be solved separately from the composition equations (operator splitting)"),
but its `op_split_burn` option — off by default, applied to cells above
`op_split_burn_min_T` = 2 × 10⁹ K, and the mode Jermyn et al. (2023 §10.2)
recommend beyond core C-depletion — integrates the network at fixed (T, ρ) over
the timestep and lets the structure solve use the result (Tier 0 §IV.1). That is
the mode an emulator plugs into (the NNN paper §4 says as much), and an earlier
version of this paragraph presented the split as MESA's only behaviour (corrected
in the 2026-08-18 audit). The split is what makes the network call a well-posed
map

$$
\Phi_{\Delta t}:(T,\rho,\mathbf X)\;\longmapsto\;(\mathbf X', e_{\mathrm{nuc}}, \varepsilon_\nu),
$$

and it is what makes an emulator possible at all. It also has an error of its own
— a local O(Δt²) (global O(Δt)) commutator term for first-order Lie splitting
(Hairer & Wanner 1996) — whose size relative to the emulator's error nobody has
measured (Tier 2 **R-11**; Jermyn et al. 2023 §10.2 likewise decline to say
which treatment is more accurate). If the split error dominates, the 3 × 10⁻⁶ gate
is over-specified; if not, the gate binds.

**And the coupling is a feedback loop, not a one-way call.** Burning heats the
zone, which raises T, which accelerates burning. Every measurement in this
project is at *imposed* (T, ρ). An emulator validated at imposed (T, ρ) has not
been validated in the loop it will run in, and that loop has positive feedback.
`tier1.md` §VIII.C.4 / **R-11**.

### 0.8.2 The cost model, and the compromise everybody makes

Tier 0 §I.3 quantifies the three costs; the summary and the consequence:

- **Stiffness forces implicit integration.** The stiffness ratio reaches
  10¹²–10¹⁵ (Tier 0 §V.3; sourced as a range — Hix & Thielemann 1999b call
  𝒮 > 10¹⁵ "not uncommon", Guidry 2012 gives 10–20 orders between the fastest
  and slowest timescales — and assumed for mesa_80/151 until measured). Explicit
  methods would need ~10¹² steps per physical step [derived here from the
  stiffness ratio; Guidry 2012 quotes 10¹⁴ explicit steps for CNO hydrogen
  burning]. This is not an
  optimisation choice.
- **Each implicit step costs a Jacobian build and a dense-ish LU.** n³/3
  multiply–adds (≈ 2n³/3 flops; Golub & Van Loan 2013): 1.7 × 10⁵ for n = 80,
  1.1 × 10⁶ for n = 151
  (6.7×), 2.8 × 10⁶ for n = 204 (17×). For n ≲ 100 dense LU is what wins in
  practice (Hix & Thielemann 1999b); the Jacobian is "doubly bordered, band
  diagonal" (Hix & Thielemann 1999b) because free nucleons couple to everything,
  so sparse solvers only pay off beyond a few hundred species (Timmes 1999;
  Paxton et al. 2011). At
  mesa_80/151 the dense n³ estimate is the right one; at 204 it is an upper
  bound. (An earlier version said "sparsity does not rescue it" outright and
  "6.5×"; corrected in the 2026-08-18 audit.)
- **Every zone, every step**, 10²–10⁴ zones (hundreds to thousands, Paxton et al.
  2011 §6.1) × ~10⁶ steps [assumed, order of magnitude].

So the network's cost scales steeply in the number of species, and the number of
species is exactly what controls whether the weak sector — the Yₑ physics — is
represented at all (§0.7.2). **The compromise every stellar-evolution
calculation makes is to run a network small enough to afford and accept that it
gets Yₑ wrong.** MESA's `approx21` is the canonical example: 21 species, fast,
and structurally incapable of representing the neutron-rich β-decay chains (the
NNN's baseline is the 22-species variant `approx21_cr60_plus_co56`, whose entire
weak sector is one effective reaction ⁵⁶Fe + 4n + 2e⁻ → ⁶⁰Cr + 2νₑ; Grichener et
al. 2025 §3).

The measured size of that compromise is the baseline this project's target is
defined against: the NNN paper reports that a large-network emulator improves Yₑ
accuracy over `approx21` by **390–660%** on mesa_80 and **280–400%** on mesa_151
(Grichener et al. 2025 §3); this repo reproduces **377–651%** and **277–390%**
from the shipped loss files (**[RESULTS]** 2026-07-08 — an earlier version
attributed the reproduced figures to the paper). That is the error a real
calculation is currently carrying.

### 0.8.3 The emulation landscape

Emulating or reducing nuclear networks is not new, and the honest framing needs
the alternatives on the table.

| approach | idea | why it is not enough |
|---|---|---|
| **small/α networks** (`approx21`) | drop species, lump chains | the measured Yₑ error above; structurally cannot carry the weak sector |
| **QSE-reduced networks** (Hix & Thielemann 1996, 1999b; Hix et al. 2007) | solve equilibrated groups algebraically, integrate only bridges | correct in principle; requires the QSE assumption to hold — and this tier measures that it does **not** hold cleanly on the label manifold (§IV.5) |
| **adaptive networks** (e.g. the KEPLER adaptive network of Rauscher et al. 2002 [assumed; not opened]) | activate species dynamically | reduces cost but not the stiff solve; bookkeeping-heavy |
| **NSE tabulation** | above some T, replace the network with a table X(T, ρ, Yₑ) | works only where NSE genuinely holds; the transition handling is where switching codes see discontinuities and instabilities (Paxton et al. 2015 §5.2, on why MESA avoids the switch) and where this tier found the labels pathological (§III) |
| **direct ML emulation** (Fan et al. 2022 — 3 isotopes in MAESTROeX; Zhang et al. 2025 — 3/13 isotopes; NNN — 80/151, MLP; NuGNN, Kim et al. 2026 — 690 isotopes, GNN; this project) | learn Φ_Δt | needs the accuracy and the invariants; no free lunch on rollout stability |

**What ML brings that the others do not** is the cost scaling. A GNN forward pass
costs O(K(n + m)d²) (the standard message-passing complexity, Gilmer et al. 2017;
Battaglia et al. 2018) — linear in graph size and **independent of stiffness**. The
classical cost *grows* as the problem stiffens; the surrogate's does not. In the
hardest states, which are exactly where the network dominates runtime, the ratio
is most favourable. That is the whole prize (Tier 0 §I.5).

**What it costs.** Two things, and this tier measures both:

1. **The emulator inherits its training labels' physics, bugs included.** §III.
2. **The speedup is capped at 1/f by the fallback rate**, not by the raw model
   speed (Tier 2 §0.5b): S → 1/f as S_raw → ∞. f = 5% caps you at 20×. So the
   OOD-detector design is an economics problem before it is a statistics
   problem, and **R-12** is the arithmetic that turns S22's unspecified gate into
   a number.

### 0.8.4 What this project adds, stated narrowly

Against that landscape, the defensible novelty claims are:

1. **Exact conservation by construction** rather than by penalty or a mass-sum
   activation (the NNN's softmax; Fan et al. 2022; Zhang et al. 2025) — an
   architecture-level hard constraint in the sense of Beucler et al. (2021),
   here realised through a fixed integer stoichiometric matrix, dY = νΦ, so
   mass, charge-to-lepton closure and lepton number hold to float64 at once for
   *any* Φ, including an untrained network's. Measured: drift exactly 0.0 on column tests, ≤ max(10⁻¹²s,
   10⁻¹³G) under random 12-decade fluxes **[RESULTS]** 2026-07-08.
2. **A flux-space target**, which makes errors attributable to named reactions
   and makes the equilibrium structure expressible — conditional on the kill-test,
   which is §IV.
3. **A graph representation whose node features are raw (Z, N)**, posed
   explicitly as a size-transfer question rather than a retraining exercise
   (NuGNN also uses learned N, Z embeddings on isotope nodes, but on a fixed
   690-isotope graph and without claiming transfer — Kim et al. 2026).
4. **Phase-0 discipline**: every claim measured, every gate falsifiable, every
   negative result recorded. This tier is what that buys — four negative results
   that a less careful project would have discovered during training, or never.

And the honest ledger of what it does *not* add: nothing about the explosion
mechanism, nothing about the mass cut, and no measured derivative connecting Yₑ
accuracy to an observable (§0.6.5).

### 0.8.5 ⚠ The bottleneck premise has never been measured

The project's founding claim is that the nuclear network dominates runtime in
late burning. Tier 0 §I.3 derives *why* it should — stiffness forces implicit
integration, LU is n³/3 with fill-in, every zone every step — and the derivation
is sound. But the derivation gives a scaling, not a fraction, and **no one has
measured what fraction of a real MESA run is spent inside `net`** (the fraction
*within* a network step is known — the matrix solve takes ≳ 90% of it, Hix &
Thielemann 1999b — the whole-run fraction is not).

That is remarkable, because the measurement is cheap and the project already has
everything it needs: MESA r23.05.1 is built and tested, the SDK is installed,
and MESA reports per-module timing natively (`first_model_for_timing`,
`star_job.defaults:2897`; note that in the fully coupled mode the network's cost
is spread over `time_nonburn_net` and `time_solver_matrix`, the latter shared
with the structure LU — only `op_split_burn` isolates it in `time_solve_burn`).
Running a 20 M⊙ model to core
collapse with `net` split out — with mesa_80 and mesa_151 and `approx21` — would
give:

- the actual runtime fraction of the network, **by evolutionary phase** (the
  claim is specifically about the last day, not the whole life);
- the achievable end-to-end speedup ceiling by Amdahl's law, which is the number
  that decides whether the project is worth doing: if the network is 40% of
  runtime, a perfect emulator gives 1.7× overall, and the 1/f fallback analysis
  of Tier 2 §0.5b is arguing about a factor that Amdahl already caps;
- the **scaling with network size**, which is the actual quantity the "accuracy
  versus cost compromise" (§0.8.2) is about — is going from 21 to 151 species a
  ~370× network cost ((151/21)³ if LU-dominated; 80 → 151 alone is 6.7× — an
  earlier version wrote "6.5×" here, the 80 → 151 figure mislabelled), and what
  does that do to *total* runtime?

Amdahl's law deserves to be written down, because it composes with the fallback
ceiling and nobody has multiplied them:

$$
S_{\mathrm{total}} \;=\; \left[(1-p) + \frac{p}{S_{\mathrm{net}}}\right]^{-1}
\;\xrightarrow[\ S_{\mathrm{net}}\to\infty\ ]{}\; \frac{1}{1-p},
\qquad
S_{\mathrm{net}} \;\le\; \frac{1}{f}\ \text{(Tier 2 §0.5b)} .
$$

So the achievable end-to-end speedup is bounded by **min(1/(1−p), 1/f)** where p
is the network's runtime fraction and f the fallback rate. Both factors are
currently unknown. At p = 0.5 the ceiling is 2× no matter what the emulator does;
at p = 0.9 it is 10×. [derived here from Amdahl 1967]

**This is the single most consequential unmeasured number in the project**, it
costs one afternoon of compute, and it could either strongly justify the work or
force a rescoping toward the specific workloads where p is high (§0.5.9's
parametrised-1D grids are the candidate). Registered as **T-24**.

### 0.8.6 ⚠ The call-site contract — seven requirements nobody has written down

Tier 1 §VIII.E.6 and Tier 2 **R-11** flag "the deployment coupling contract" as
unspecified and discuss two aspects: the operator-split error and imposed-versus-
fed-back (T, ρ). The contract is considerably larger than that, and the missing
parts are not physics — they are the interface a stellar-evolution code actually
requires. Enumerating them changes what Component D and S22 have to deliver.

**1. ΣX = 1 and X ≥ 0, hard.** The EOS computes Ā and Z̄ from the composition and
will produce nonsense from a negative or non-normalised one (Tier 2 §0.5). Target
A gives ΣX = 1 exactly; **positivity is enforced nowhere** and is not even
diagnosed (Tier 2 **R-04**). A single negative mass fraction handed to `eos` is a
crash or a silently wrong pressure.

**2. e_nuc *and its partial derivatives* — on one of MESA's two routes.** This is
the requirement that is completely absent from every document in the project.
MESA solves the structure equations implicitly (Paxton et al. 2011 §6), and the
energy equation contains e_nuc. In the default fully-coupled scheme the Newton
solve therefore needs

$$
\frac{\partial e_{\mathrm{nuc}}}{\partial \ln T},\qquad
\frac{\partial e_{\mathrm{nuc}}}{\partial \ln \rho},
$$

which MESA's own network returns alongside the energy (`net_get` returns
`d_eps_nuc_dT`, `d_eps_nuc_dRho`; the log-conversion is trivial). But MESA has a
second route: in `op_split_burn` mode — the mode Jermyn et al. (2023, §10.2)
recommend beyond core C-depletion, and the mode that mirrors the one-zone-burn
call the labels come from — the network is integrated at fixed (T, ρ) by
`net_1_zone_burn`, ε_nuc is computed from the composition difference, and "these
partial derivative matrix terms are thus set to zero" (Jermyn et al. 2023 §10.2;
`hydro_energy.f90:233–235`). So a derivative-free emulator has a MESA precedent
on route (b), at the documented cost that "the physics in the partial
derivatives" is ignored; on route (a) it must supply the derivatives (and the
composition Jacobian, §I.2b). An earlier version of this item said the
derivatives were "not optional" for MESA outright; corrected in the 2026-08-18
audit. **On the fully-coupled route a black-box emulator must supply them.** The
good news is that this is a natural strength of a
differentiable model — autodiff gives them for free and they are *smoother* than
the ODE solver's finite-difference versions. The bad news is that nobody has
specified them as outputs, so nothing in the training loss constrains them, and
an emulator can be accurate in e_nuc while having a wildly wrong derivative. A
derivative that is wrong in **sign** would break the host's Newton convergence.

This is a first-class, checkable requirement with a natural training term
(supervise ∂e_nuc/∂lnT against finite differences of the reference integrator),
and it has never been named. Registered as **T-25**.

**3. The host chooses Δt adaptively — and it uses network failure as a signal.**
The emulator is trained on nine fixed Δt values; MESA picks Δt per step from
change limits and convergence behaviour. Two problems follow:

- the emulator will be called at Δt values it never saw (this is S19's job, and
  it is why **R-10**'s Δt/τ conditioning matters);
- more subtly, **an implicit solver that fails to converge is how the code learns
  its timestep was too large.** An emulator has no failure mode. It always
  returns something. Removing the network's convergence failure removes a
  feedback signal the timestep controller depends on.

That reframes S22 substantially. **The OOD detector's real job may not be
"decide when to fall back" — it may be "supply the error estimate that the ODE
solver used to provide".** Those are different specifications: the second needs a
*calibrated, continuous* error estimate rather than a binary flag, and it is
consumed by the timestep controller rather than by a dispatcher. Registered as
**T-26**.

**4. Retries must be deterministic.** Stellar codes back up and retry timesteps
with smaller Δt, and they may redo the same call. Bitwise-identical output for
identical input is required, which constrains reduction order, threading, and
device (`tier1.md` §VIII.E.4's determinism item, arriving here as a hard
interface requirement rather than a nice-to-have).

**5. The call is per zone, per step, from Fortran.** A PyTorch model called from
MESA's inner loop pays interpreter, marshalling and dispatch overhead **per
call**. For a small graph at batch size 1 on CPU, that overhead can exceed the
FLOPs by orders of magnitude — a GNN forward pass with n ≈ 150 nodes is a
sequence of tiny GEMMs, which is the worst case for framework overhead. The
realistic deployments are (a) batch all zones of a timestep into one call, which
is natural since they share Δt, or (b) export to a compiled artifact
(TorchScript / ONNX / a hand-written C kernel) with no Python in the loop.

Neither has been costed, and this is a place where a "1000× faster in FLOPs"
claim can arrive at the call site as a slowdown. Tier 2 §0.5b's batching analysis
assumed batching works and asked about fallback; this asks whether the batch
exists at all. Registered as **T-27**.

**6. Memory and model size.** The NNN ships **23.8 GB of checkpoints** (54
files: the 18 production models are 7.3 GB, plus a 36-model layer scan; each
checkpoint carries Adam optimizer state, ~3× the weights). A stellar code that
loads a model per network per Δt has a startup and memory profile that matters
on a shared cluster. One conditioned model (S19) is not just more elegant — it is
~9× smaller per network (one Δt-conditioned model replaces the nine dt-specific
ones), which is a deployment argument the project has not made.

**7. Failure and provenance.** What does the host do when the emulator is asked
for something outside its domain, and how does a finished stellar model record
which emulator version produced its composition? The second is the reproducibility
half of Tier 2 **R-25** (shelf life) and it is an interface requirement: the model
identity has to end up in the output.

**Why this section matters more than it looks.** Six of the seven items are
invisible from inside the physics, and every one of them can invalidate a project
that is otherwise correct. They are also cheap to settle — most are decisions and
a specification document, not measurements. The pattern is the one Tier 1
§VIII.D names: *the questions that never get asked are the ones that no test
could fail.*

---

## 0.9 Astrophysics → gates: the mapping table

Every numeric gate in `CLAUDE.md` traces to a physical statement in this part.
Assembling the map in one place is the fastest way to check whether a gate is
defensible — and to see which ones are not.

| gate (`CLAUDE.md`) | value | traces to | status of the trace |
|---|---|---|---|
| conservation drift | ≤ 10⁻¹² per step, float64 | §0.7.1: strong sector is Yₑ-neutral **exactly**, so any leak is pure error in the only signal that matters; Tier 2 §0.4.2: leaks are systematic | **solid** — algebraic |
| per-step \|ΔYₑ\| | ≲ 3 × 10⁻⁶ | 5 × 10⁻³ trajectory budget ÷ N ≈ 1.6 × 10³, systematic accumulation | **conditional** — slope unmeasured (**R-21**) |
| Yₑ physics floor | 5 × 10⁻³ – 1.5 × 10⁻² | the WW95 → LMP+β-decay weak-physics shift in central Yₑ at collapse (Heger et al. 2001: about half from adding β-decays, half from smaller LMP electron-capture rates) | **solid as a floor**, but it is an *input* uncertainty used as an *output* tolerance (§0.6.5, **T-01**) |
| regime box T₉ 1.6–7.9 | | §0.1.3 virial estimate lands at T₉ ≈ 7.4 (crude, ideal-gas) for a 1.4 M⊙ core at 10⁸; §0.2.1 puts Si ignition at 3–4 GK; §0.5.2 puts Fe dissociation above the box | **solid** for the support; the *measure* on the box is not (**R-07**) |
| regime box ρ 10⁷–10⁹ | | §0.1.4: spans the degeneracy transition (E_F/kT 1.5 → 10.5) | **solid** |
| regime box 0.45 < Yₑ < 0.5 | | §0.4.4: η = 0 … 0.10, the full physical range of Si-burning/Fe-core material | **solid** |
| QSE onset ~3–3.3 GK | | §0.2.1: Q/kT for ²⁸Si(γ,α) moves 38.6 → 28.9 between T₉ = 3 and 4 | **plausible** — that establishes a sharp transition *somewhere* in the interval, not the 3–3.3 boundary specifically |
| kill-test window 3.3–5 GK | | where structure is neither absent (cold ladder) nor total (NSE) | **solid** |
| κ > 0.1 active set | | *nothing* — the threshold has no derivation; Tier 2 **R-01** proposes an entropy-weighted replacement | ⚠ **unsourced** |
| cond(S_active) < 10⁶ / > 10⁸ | | error amplification in solving for φ from ΔY | **plausible**, never calibrated against an actual training run |
| 95% coverage of \|ΔYₑ\| and \|ΔX\| | | the active-set premise: net flow is carried by few columns | **measured** (§IV.4) — and it split |
| energy residual ≤ 1% | | e_nuc feeds the star's energy equation, which sets the contraction rate (§0.2.3) | **solid in motivation**; the gate as implemented is near-algebraic (Tier 2 §IV.8) |
| size-transfer falsifier (2×) | | §0.7.2: mesa_151 is not a superset — it is reshaped toward the weak sector | **solid** |
| Sobol → real-MESA (3×) | | §0.3.4 / §IV.3: the training measure corresponds to no physical setting | **solid, and predicted to fire** (**R-07**) |

Two rows in that table are worth staring at. The **κ > 0.1 threshold** is the
single most load-bearing number in the kill-test and it is an unsourced choice.
And the **3 × 10⁻⁶ per-step gate** — the project's most expensive requirement —
is conditional on an unmeasured accumulation slope and justified by an input
uncertainty. Both are known; both are registered; neither is closed.

**And now the complementary table: the physical requirements that have no gate at
all.** Every row above is a gate looking for a justification; every row below is a
requirement looking for a gate. The asymmetry is informative — the project
gate-ified everything it could measure from the data it had, and left ungated
everything that requires an experiment outside that data.

| requirement | why it is a requirement | gate |
|---|---|---|
| **X ≥ 0** | the EOS is called on the output (§0.8.6.1) | **none** — not enforced, not diagnosed (**R-04**) |
| **∂e_nuc/∂lnT, ∂e_nuc/∂lnρ** | the host's fully-coupled structure solve needs them (§0.8.6.2; MESA's own `op_split_burn` route zeroes them, Jermyn et al. 2023 §10.2) | **none** — not even specified as outputs (**T-25**) |
| **determinism under retry** | stellar codes back up and re-call (§0.8.6.4) | **none** (`tier1.md` §VIII.E.4) |
| **a calibrated error estimate** | replaces the convergence-failure signal the timestep controller lost (§0.8.6.3) | **none** — S22 is specified as a binary flag (**T-26**) |
| **per-call latency at the real batch size** | a Fortran inner loop calling PyTorch (§0.8.6.5) | **none** (**T-27**) |
| **network runtime fraction p** | Amdahl caps the whole enterprise at 1/(1−p) (§0.8.5) | **none** — the project's premise (**T-24**) |
| **error character (systematic vs random)** | it survives both time-accumulation and spatial mixing (§0.2.5, §0.3.4) | partially — the accumulation slope is **R-21**; the spatial half is new (**T-19**) |

Six of seven rows have no gate. That is the shape of the gap this deep-dive
found, and it is why Part IX exists.

---

## 0.10 Self-check for Part 0

Answer without scrolling up.

1. Derive the virial statement E_tot = −E_int for a non-relativistic ideal-gas
   star, and say in one sentence why it makes stellar evolution a *sequence*
   rather than an equilibrium.
2. T_c ∝ M^{2/3}ρ^{1/3}. Use it to explain both why 8 M⊙ is roughly the
   threshold for reaching silicon burning and why the regime box sits at
   ρ ~ 10⁸.
3. Why does ²⁸Si not burn by fusing with ²⁸Si, and what single structural
   consequence does that have for every equation in Tiers 1–2?
4. Silicon burning releases *less* energy per gram than oxygen burning. Why is it
   nevertheless the stage this project emulates?
5. The last stages of a massive star's life accelerate. Name the coolant, its
   temperature scaling, and use it to get the silicon-burning duration from the
   oxygen-burning duration.
6. State the collapse instability condition and explain why 4/3 appears in both
   it and the virial theorem.
7. The bounce shock has ~10⁵¹ erg. Compute the cost of dissociating 0.5 M⊙ of
   iron and say what follows.
8. Name the five distinct places Yₑ enters the collapse-to-explosion chain.
9. Why is β⁻ decay unable to undo electron capture in a *strongly* degenerate
   collapsing core — and when, during Si burning, does it manage to? What does that
   imply about how an emulator's Yₑ error accumulates?
10. Which two gates in §0.9 rest on the weakest foundations, and what would close
    each?
11. Compute the Damköhler number for intra-group equilibration, bridge flow and
    the weak sector, and say which composition quantity convection homogenises.
12. A convective region spans 300 zones. By how much does mixing reduce the
    emulator's Yₑ error if it is random? If it is a smooth function of the
    state? What does that add to the case for structural conservation?
13. Above ~5–7 GK some stellar/hydro codes replace the network with an NSE
    solve; MESA does not. Give three consequences for this project, one of which
    concerns where the label pathology lives, and say which survive when the
    host is MESA.
14. Write Amdahl's law for the network's runtime fraction p, compose it with the
    1/f fallback ceiling, and say which of the two numbers the project knows.
15. Name the two outputs a host code needs that are not composition or energy,
    and say what breaks if the emulator's version of one has the wrong sign.
16. An implicit network that fails to converge tells the timestep controller
    something. What, and what must replace it?

---
# Part I (S11) — bbq and MESA as operated

**What produced the data.** Every number in Tiers 0–2 is downstream of a label
that a Fortran program wrote to a text file. This node is what that program is,
what it was asked to do, and what the project did when it needed data the shipped
set did not contain.

## I.1 What a one-zone burner is — and what it deliberately is not

A stellar-evolution code solves a coupled boundary-value problem over ~10³ zones.
A **one-zone burner** throws all of that away and keeps only step 4 of §0.8.1:
given (T, ρ, X) and a duration Δt, integrate

$$
\frac{d\mathbf Y}{dt} \;=\; \nu\,\mathbf R(\mathbf Y;\,T,\rho)
$$

at **constant** T and ρ, and report the final composition plus the integrated
energy release.

What is deliberately absent, and why each absence is a modelling decision rather
than an oversight:

| absent | consequence |
|---|---|
| hydrodynamics | no expansion/compression during the burn; no explosive-burning freeze-out (§0.3.5) |
| the energy equation feeding back on T | **the burn does not heat the zone** — no thermonuclear runaway, no self-consistent ignition |
| mixing | composition is local; no advection of fuel or ash |
| neighbouring zones | no shell structure; no gradient-driven anything |

The third column of the argument is that this is *exactly* the operator-split
sub-problem a stellar code solves (§0.8.1), so a one-zone burner is not a
simplified physics model — it is a **faithful reproduction of one call**. That is
what makes it a legitimate label generator for an emulator that will be dropped
into that same call site.

**And the caveat that carries all the way to Part VII:** the split's own error,
and the (T, ρ) feedback the split removes, are outside everything measured here
(§0.8.1, **R-11**). An emulator can be perfect on this data and still misbehave
in the loop.

## I.2 MESA's network solver, in enough detail to read the config

MESA r23.05.1's `net` module does the following per call (MESA r23.05.1 source:
`net/public/net_lib.f90:557–666` `net_get`, `:970–1031` `net_1_zone_burn`;
`rates/private/reaclib_support.f90:178–250`; Paxton et al. 2011 §6; Jermyn et
al. 2023 §10.2 — behaviour also confirmed by the Fortran probe of Tier 1 §VI.8 and
by the rate cross-check):

1. **Assemble the reaction set.** For a *softwired* net (`mesa_80.net`,
   `mesa_151.net`) the species list is fixed and the links are assembled at
   runtime from whichever rates connect those species. This is why the reaction
   count is a **measured** quantity: 607 / 1518 canonical reactions, with
   MESA_ONLY = 0 against the pynucastro export **[RESULTS]** 2026-07-09.
2. **Evaluate rates** — REACLIB fits for strong/EM channels (Cyburt et al. 2010;
   Tier 1 §II), tabulated weak rates on a (T, ρYₑ) grid from the weaklib
   compilation (one source per rate: LMP where available, else Oda et al. 1994,
   else Fuller, Fowler & Newman 1985, plus a private-communication source for
   the ¹⁴C↔¹⁴N pair — MESA `data/rates_data/weakreactions.tables` header; Tier 1
   §V), and reverse rates by detailed balance with partition functions
   (`reaclib_support.f90:246–247`; Tier 1 §III).
3. **Apply screening** — `chugunov` in this configuration (Chugunov, DeWitt &
   Yakovlev 2007; MESA `screen_chugunov.f90:26`), established by measurement to
   be `chugunov_2007` in pynucastro's naming: median ratio 0.99999,
   max |log₁₀| = 0.0021 over all strong pairs × the cross-check grid
   **[RESULTS]** 2026-07-10.
4. **Integrate** with a semi-implicit (Bader–Deuflhard) extrapolation stepper
   (`net_burn_support.f90:209`) under tolerances `eps` and `odescal`.
5. **Return** the new composition, e_nuc, and neutrino losses
   (`net_1_zone_burn`).

Two configuration facts are load-bearing for everything downstream and both were
*measured* rather than read from documentation:

- **Screening is `chugunov_2007`, and it is applied per reaction from that
  reaction's own reactants.** So a screened capture pairs with an unscreened
  photodisintegration, and κ at NSE carries a real offset of ~7 × 10⁻²
  (κ ≈ |Δ ln scor|) that is a property of the rate *configuration*, not an
  artifact **[RESULTS]** 2026-07-10. Hence `CLAUDE.md`'s two-κ rule: equilibrium
  detection on unscreened κ, always.
- **The weak-table family ordering is LMP > Oda > FFN with `use_suzuki` false**
  — the ordering that reproduces MESA's fixed one-source-per-rate compilation.
  Getting this wrong produced 14 / 23 mismatched weak pairs in the first
  reconciliation pass; matching it dropped them to 0 **[RESULTS]** 2026-07-09.

## I.2b What the network returns — the interface, as the host sees it

§0.8.6 states the call-site contract from the deployment side. Here is the same
thing from inside MESA, because it is the concrete specification the emulator has
to match and reading it once removes a whole class of surprise.

MESA has **two** entry points, and they have different contracts (MESA r23.05.1
`net/public/net_lib.f90:557–666` `net_get`, `:970–1031` `net_1_zone_burn`;
op-split routing `star/private/struct_burn_mix.f90:1127, 1156`; energy-equation
use `star/private/hydro_energy.f90:233–240`; Paxton et al. 2011 §6; Jermyn et
al. 2023 §10.2). An earlier version of this section listed a single merged table
and concluded that a derivative-free emulator "cannot be dropped into MESA at
all"; that is true of route (a) only (corrected in the 2026-08-18 audit).

**(a) `net_get` — the fully-coupled default (Paxton et al. 2011 §6):**

| returned | consumed by | emulator status |
|---|---|---|
| `dxdt(:)` — rate of change of mass fractions | the composition equations of the structure solve | Target A gives ΔY = νΦ over the step, i.e. an *integrated* dxdt — an interface mismatch to note (Φ, not a rate) |
| `eps_nuc` (net of reaction neutrinos) | the energy equation | specified (invariant #5) |
| `d_eps_nuc_dT`, `d_eps_nuc_dRho` | **the structure solve's Jacobian** (`hydro_energy.f90:239–240`) | **unspecified** (**T-25**) — needed on this route only |
| `d_eps_nuc_dx(:)` | the same Jacobian, composition part | unspecified |
| `d_dxdt_dRho(:)`, `d_dxdt_dT(:)`, `d_dxdt_dx(:,:)` | the composition-equation Jacobian | **unspecified** — the full composition Jacobian; not previously listed |
| `eps_nuc_categories(:)`, `eps_neu_total` | diagnostics; neutrino losses to the energy equation | specified, unsupervised (**T-17**) |
| `ierr` | error return; retries are the host's | **has no analogue** (**T-26**) |

**(b) `net_1_zone_burn` — what `op_split_burn` calls per hot cell (Jermyn et al.
2023 §10.2; `struct_burn_mix.f90:1156`, or the constant-density variant at
`:1127`):**

| returned | consumed by | emulator status |
|---|---|---|
| `ending_x(:)` — the new composition | the EOS, opacities, mixing, the next call | **Target A's output** |
| `avg_eps_nuc` (from the composition difference), `eps_nuc_categories(:)` | the energy equation, with **∂ε_nuc/∂lnT = ∂ε_nuc/∂lnρ = 0** in the matrix (`hydro_energy.f90:233–235`) | specified (invariant #5); **no derivatives required on this route** |
| `eps_neu_total` | the energy equation, separately | specified, unsupervised (**T-17**) |
| `nfcn, njac, nstep, naccpt, nrejct` | burner statistics | no analogue (harmless) |
| `ierr` | error return; retry is the host's | **has no analogue** (**T-26**) |

On route (b) — MESA's own recommended mode beyond core C-depletion (Jermyn et al.
2023 §10.2: "operator-split burning cannot calculate the partial derivatives of
these terms with respect to T or ρ for the matrix solver. These partial
derivative matrix terms are thus set to zero") — the emulator's contract is
composition + ε_nuc + ε_ν + a failure signal, and T-25's derivatives are not
consumed; on route (a) it must additionally return ∂ε_nuc/∂T, ∂ε_nuc/∂ρ,
∂ε_nuc/∂x and the composition Jacobian ∂ẋ/∂x. The failure signal is the row with
no counterpart on either route, and it is not exotic — it is what lets the
host's timestep controller work.

**The reason this is worth a section rather than a footnote**: it is the
difference between an emulator that is scientifically correct and one that can be
installed. On route (a), a model that predicts composition to 10⁻⁶ and returns no
∂e_nuc/∂lnT cannot be dropped in — the host would have to finite-difference it,
which costs two extra forward passes per zone per step and gives back a noisy
derivative, destroying both the speedup and the convergence. On route (b) MESA
already lives without those derivatives, at the documented cost that "the physics
in the partial derivatives" is ignored (Jermyn et al. 2023 §10.2).

**And it is a design opportunity, not just a requirement.** A differentiable
emulator can return exact derivatives by autodiff, at a small constant factor over
the forward pass, and those derivatives are *smoother* than what an adaptive ODE
solver produces (which differences a discontinuous step-size controller). That is
a genuine advantage over the incumbent, and it is currently unclaimed because
nobody wrote the requirement down.

## I.3 bbq's four modes, and why only one made the shipped trajectories

`bbq` (github.com/rjfarmer/bbq, pinned at commit 9783df31) is a thin driver
around MESA's `net` module. Its source has five `lib_*.f90` files — a shared
burn core `lib_bbq.f90` plus one file per mode — and `main.f90:22–29` dispatches
on exactly four flags (`defaults/bbq.defaults:14–17`); choosing among them is the
whole of ADR 0005's first decision. (An earlier version of this table listed five
modes with two non-existent flags and mapped `use_input_file` to the shared core;
corrected in the 2026-08-18 audit.)

| mode (flag) | file | behaviour | can it produce a trajectory? |
|---|---|---|---|
| `use_input_file` | `lib_sampler.f90` (`run_sampler_from_file`) | burn each row of an input file **independently** from that row's own composition, for its own duration | **no** — no state carry-over (`lib_sampler.f90:71`) |
| `use_random_sampling` | `lib_random.f90` | draw random (T, ρ, composition) states and burn each | no |
| `use_profile` | `lib_profile.f90` | burn a (t, logT, logρ) list **carrying composition forward** through the list (`:53–57`); header `age dt logt logrho <isos>` | **yes** — the one mode that follows a *non-constant* (T, ρ) track — but it **writes no eps_nuc** (`:128, 160–165`), and it was not used for any shipped file |
| `use_hydrostatic` | `lib_hydrostatic.f90` | burn a sequence of durations at constant (T, ρ) **carrying composition forward**, one output row each; header `age dt eps_nuc eps_neu <isos>` (`:115`) | **yes** — the mode that made every shipped trajectory |

Only `use_hydrostatic` gives all three of (i) composition carry-over between
rows, (ii) per-row eps_nuc, and (iii) exact cadence control, because each line
of `times.txt` is a per-step burn *duration* (`use_profile` gives (i) and (iii)
but not (ii)). The shipped test trajectories have `lib_hydrostatic.f90`'s exact
header — `age dt eps_nuc eps_neu <isos>` — which is how the project knows which
mode generated them (bbq commit 9783df31, `src/main.f90:22–29`,
`defaults/bbq.defaults:14–17`, `src/lib_profile.f90:53–57, 128`,
`src/lib_hydrostatic.f90:115`, `src/lib_sampler.f90:71`; ADR 0005).

The rejected alternative is instructive: `use_input_file` with cumulative
durations would burn each row from the *initial* state rather than continuing, so
reproducing an N-row trajectory would need N sequential bbq invocations, each
paying full network setup. That is not a small constant factor — network setup
dominates a short burn.

## I.4 The inlist as a configuration surface

`scripts/bbq_campaign/inlist.template` is short enough to read whole and every
line is a decision:

```fortran
&bbq
   net_name = '{net}.net'
   max_steps = 1000000
   eps = 1d-8            ! solver relative tolerance
   odescal = 1d-10       ! ODE scaling floor
   stptry = 0            ! 0 = MESA's 'try in one step'; r23.05.1 overrides stptry internally (net_burn.f90:254)
   use_hydrostatic = .true.
/
&hydrostatic
   logT = {logT}
   logRho = {logRho}
   times_from_file = .true.
   input_filename = 'times.txt'
   input_composition_filename = 'comp.txt'
   output_filename = 'output.txt'
/
&nuclear
   screening_mode = 'chugunov'
   use_suzuki_weak_rates = .false.
/
```

Three observations worth internalising.

**(i) `eps = 1e-8` is the tolerance the reference integrator inherits.** ADR 0006
sets the project's own BDF integrator to rtol = 1e-8 explicitly *because* that is
bbq's `eps` — so that disagreements between the two are physics differences, not
tolerance differences. Matching a competitor's tolerance before comparing to it
is a small discipline with a large payoff.

**(ii) The `&nuclear` block pins what the defaults would have given anyway.**
`screening_mode` and `use_suzuki_weak_rates` are written explicitly even though
they match bbq's defaults. This is the "pin what you rely on" habit: a future bbq
version changing a default would silently change the labels, and an explicit
inlist turns that into a diff.

**(iii) Constant (logT, logRho).** Each run is at a single point in the regime
box. There is no trajectory through (T, ρ) — the "trajectory" is only in
composition (bbq's `use_profile` mode could have followed a (T, ρ) track, but no
shipped or campaign file used it). Everything this project calls a trajectory is
a **constant-(T, ρ) relaxation**, which is a specific and limited object; §IV.3 is where that limit
becomes a measured problem.

## I.5 The shipped-label pipeline, reconstructed

The Zenodo dataset (record 14873443, 115 GB uncompressed, 3800 entries) was
produced by the NNN authors, and reconstructing their pipeline from the artifacts
was Steps 1–3 of this project. The reconstruction:

1. **A Sobol grid over the regime box.** 2²⁰ = 1,048,576 points in
   (log T, log ρ, Yₑ), generated by an **unseeded scrambled** `scipy.stats.qmc`
   Sobol sampler (Sobol' 1967; SciPy, Virtanen et al. 2020 — `Sobol(d)` defaults
   to `scramble=True, seed=None`; Grichener et al. 2025 §2.2;
   `gridGenerator.py`). This is the single most consequential engineering fact in the
   dataset: **it is non-regenerable.** The shipped grid file is the only ground
   truth, and anything keyed to states must persist explicit `state_id` lists
   (Tier 0 §III.4/§III.5).
2. **A composition per grid point**, constructed to hit the target Yₑ. Not a
   physical composition — random, and free-nucleon-loaded (median X_neut ≈ 1.7 ×
   10⁻²). §IV.3 is the consequences.
3. **bbq runs** at each state for each of nine timesteps, yielding 18 training
   CSVs (2 networks × 9 dt), 1,041,400 rows each.
4. **Test trajectories** — 684 (mesa_80) + 824 (mesa_151) = 1508 constant-(T, ρ)
   hydrostatic runs in total, shipped as `output_T_<logT>_rho_<logRho>.txt`.

The audits that made this usable, all **[RESULTS]** 2026-07-08/09:

| audited fact | value |
|---|---|
| rows per training CSV | 1,041,400, identical across all 18 |
| the real dt grid | deviates from nominal by up to ~5% and **differs between networks** (the "1e2" file is 105.08 s for mesa_80, 102.93 s for mesa_151) |
| row alignment across dt files | byte-identical (logT, logRho) arrays ⇒ `state_id` = row index is a valid join key |
| (logT, logRho) as a join key | **rejected** — 154,405 collisions from 3-decimal rounding |
| missing Sobol rows | 7,176 (0.68%), in **two contiguous blocks** at the head and tail of the sequence — lost job-array batches, spatially quasi-uniform (χ²/dof ≤ 0.1 on all marginals), **benign** |
| `final_*` floor | exactly 1e-15, censored not physical |
| ε_ν normalisation | uniform ÷1e16 in all 18 files; the hinted alternate 1e13 at dt ≥ 10 s is **absent** |

That table is what "read the dataset before trusting it" produces. Every row of
it retired an assumption that would otherwise have become a silent bug: a join on
(logT, logRho) would have silently mixed 15% of the rows; a nominal dt would have
introduced a 5% error in every rate comparison; the 1e-15 floor treated as data
would have taught the model to predict a clamp.

## I.6 Why a rerun campaign was necessary

The shipped test trajectories have a defect that Step 5 discovered and Step 6
diagnosed: they **stall**. Composition freezes (max |ΔX| per interval < 10⁻¹⁰)
from median age 2.2 × 10⁵ s (mesa_80) / 3.9 × 10⁴ s (mesa_151), while eps_nuc
keeps *rising* **[RESULTS]** 2026-07-10. §II.4 is the anatomy; the operational
consequence was that only pre-stall rows could be used, which left too few
relaxed states to render a kill-test verdict on.

So Step 6 generated its own: **209 runs per network**, locally, with bbq.

ADR 0005 settles four points, and each is worth understanding as a
methodological choice:

**1. Mode: `use_hydrostatic` with `times_from_file`** — §I.3.

**2. Cadence: 40 points per decade, log-spaced ages from 10⁻⁸ s, dt capped at
10⁵ s**, to t_end = 10⁴ s (T₉ ≥ 5), 10⁶ s (3.3–5), 10⁸ s (< 3.3). This directly
attacks the stall mechanism: the shipped files used ~10 points/decade, letting
the output dt grow to ~10¹⁰ s, at which point a single output interval is longer
than any physical timescale in the problem.

**3. MESA: stock r23.05.1, NOT 24.08.1.** This is the subtle one. Stock
r23.05.1 carries the gh-575 multi-body-inverse bug (Tier 1 §VI.6, §III); 24.08.1
fixes it. Choosing the *buggy* version looks perverse until you state the goal:
the reruns must be **comparable to the shipped labels**, and the shipped labels
were produced by r23.05.1-class code. Choosing the fixed version would have
produced better physics and a worse experiment.

That choice was validated after the fact, and this is the part that makes it
defensible rather than lucky: stock r23.05.1 bbq reproduces the shipped labels to
**0.01 / 0.03 dex** on the two witness states **[RESULTS]** 2026-07-11, and
early-time agreement against shipped trajectories at identical (logT, logRho, X₀)
is 0.996 / 0.998 **[RESULTS]** 2026-07-11. The reruns are label-grade.

**4. Three composition families**, covering three different senses of "a state
worth burning":

| family | construction | purpose | n |
|---|---|---|---|
| `shipped` | row-0 state of each Step-5 selected shipped trajectory, at the file's exact (logT, logRho) | early-time comparability — the control | 20 |
| `canonical` | two-isotope Si-burning-like mixes solving ΣXᵢZᵢ/Aᵢ = Yₑ: si28+si30 above Yₑ = 0.4667, si30+ne22 below | *physically plausible* fuel, unlike the Sobol compositions | 63 |
| `sobol` | nearest training-grid states per (T₉, ρ, Yₑ) cell, `state_id`s in the manifest | ties the relaxed manifold back to the training distribution | 126 |

A detail worth noticing, because it is the kind of thing that quietly breaks an
analysis: the Yₑ = 0.45 target is **unreachable** with the three Si-burning fuel
species the family uses (²⁸Si, ³⁰Si, ²²Ne), whose Z/A floor is ²²Ne at 0.45455 —
the networks do contain neutron-richer species (¹⁸O, Z/A = 0.444, in both nets,
the only such A ≥ 12 species in mesa_80; mesa_151 adds ~40 more, e.g. ³²Si,
⁴⁸Ca, ⁵⁸Fe, ⁶⁴Ni) but none is silicon-burning fuel (an earlier version called
²²Ne "the network's Z/A floor"; corrected in the 2026-08-18 audit). The campaign
substitutes 0.455 and **records the substitution in the
manifest**. That is the sourced/derived/assumed discipline applied to a
composition.

## I.6b The campaign's coverage geometry — and what 209 runs can and cannot say

The verdict rests on this campaign, so it is worth asking what it covers.

**The design grid** is 7 T₉ values × 3 log ρ × 3 Yₑ = 63 cells, populated by three
families (§I.6) to 209 runs per network. Compare with the space it is sampling:

| | campaign | training corpus | the box |
|---|---|---|---|
| T₉ | 7 discrete values | 2²⁰ Sobol points, continuous | continuous 1.6–7.9 |
| log ρ | 3 discrete values | continuous | continuous 7–9 |
| Yₑ | 3 targets (one substituted) | continuous | continuous 0.45–0.5 |
| compositions | 3 structured families | 1 random per state | — |
| rows used in the verdict | ≤ 24 per trajectory, 4,693 total | 1.04M states | — |

Three honest observations.

**(i) The relaxed manifold is a lattice, not a sample.** Three densities is
enough to see a trend and not enough to fit one; the ρ-dependence of every
kill-test statistic is resolved at three points across two decades. Any statement
of the form "κ structure varies with density" is an interpolation between three
values.

**(ii) The composition families are not a probability distribution.** They are
three *purposes* — comparability, plausibility, and traceability to the training
grid — which is a good design for a diagnostic and a bad one for an estimate.
When §IV reports "the median over the relaxed manifold", the median is over a set
whose composition mixture was chosen by hand. This does not bias the *structural*
results (the empty mask, κ ≡ 1 on weak columns) but it does mean the coverage
fractions of §IV.6 are conditional on the family mix.

**(iii) Nothing checks representativeness against a real track.** Tier 2 **R-07**
measured that a 20 M⊙ track sits within 0.12–0.18 dex of a line in the box; the
campaign samples a lattice over the whole box. Whether the campaign's cells
include the cells a real star actually visits — and with what weight — was never
checked. That is a half-hour of work given both datasets exist, and it would
convert "the verdict on the relaxed manifold" into "the verdict on the part of
the manifold a star visits". Registered as **T-13**, and §0.4.5 / **T-22** is the
question of whether *one* track is enough to define "visits".

**What the campaign nevertheless establishes securely**, and it is a lot: the
structural results (weak κ ≡ 1, empty maskable set, cond(S_active), the bridge
identities, the r_QSE negative verdict) are either exact or so far from their
thresholds that no plausible reweighting moves them. The results that are
genuinely conditional on the sampling design are the *fractions* — coverage,
low-κ share, and the concentration shares — and those are exactly the ones §IV.8
also flags for missing error bars. The two caveats compound and should be quoted
together.

## I.7 Execution

**[RESULTS]** 2026-07-11: **418 of 418 runs completed, zero failures.** 19,486 s
wall on 10 workers ≈ 54 core-hours; mesa_80 ≈ 2–3 min/run, mesa_151 ≈ 4–6 min at
high T₉, and low-T₉ runs (walls at 10⁸ s, ~2600 output rows) up to ~1 h. 1.1 GB
of text output.

Two engineering points from `run_campaign.py` and `make_campaign.py` worth
carrying:

- **Completion is defined by an invariant, not by the exit code.** A run counts
  as complete iff bbq exits 0 **and** `output.txt` has exactly `n_times + 1`
  rows. bbq aborts a hydrostatic run mid-way if a step hits `max_steps`, exiting
  cleanly with a truncated file. Checking the row count is the difference between
  a validated campaign and a silently 80%-complete one.
- **The queue is resumable and priority-ordered** (QSE window first, via
  `T9_PRIORITY = [3.3, 4.0, 5.0, 6.3, 2.5, 1.6, 7.9]`), with a `DONE` sentinel
  per run directory. A 54-core-hour campaign that cannot resume is a campaign you
  will run twice.

## I.8 Validation — four checks, and what each was for

`validate_campaign.py` runs four checks. Reading them as a *design* is
instructive, because each one is aimed at a specific way the campaign could have
been worthless.

**1. Stall census.** Terminal-guard census: 38/209 (mesa_80) and 56/209
(mesa_151) runs frozen before their wall, median frozen-run T₉ = 7.9 — fast
arrival at the terminal attractor, which is legitimate. Frozen at T₉ < 3.3: 9 and
7 runs, and these are **exactly** the canonical-family inert-fuel cells at 1.6 GK
(si28/si30/ne22 mixes cannot burn there). Crucially: *the shipped-class mid-burn
output-dt artifact is absent* — every non-inert run either evolves at its stated
wall or terminates at an attractor. **[RESULTS]** 2026-07-11. The cadence fix
worked.

**2. Terminal T₉ ≥ 5 states vs true NSE.** Median distance 8.6 / 9.0 dex,
fraction within 0.05 dex = 0.000. This *looks* like a failure and is not — it is
the displaced pseudo-equilibrium the label-pathology rows predict for stock MESA
(§III). The check was designed to *report* rather than gate precisely because the
expected answer was known to be "far from NSE, for a known reason". A gate here
would have failed the campaign for being correct.

**3. Early-time comparability.** Per-pair species-age agreement within
max(5%, 10⁻⁸): median 0.9963 / 0.9977, min 0.9508 / 0.9449 over 20 pairs per
network; worst |ΔX| median 2.3 × 10⁻³ / 1.5 × 10⁻³. Same code, same config,
differing only in output cadence — the reruns are label-grade comparable.

**4. The r_QSE plateau, on clean data.** The Step-5 measurement had been deferred
on the grounds that the shipped trajectories were anomalous. On clean rerun data:
intra-group std(r_QSE) median **0.87 / 0.80 dex**, plateau rows (< 0.1 dex)
**0 of 303 and 0 of 316** in the QSE window, versus non-group spread 2.19 /
1.29 dex. **[RESULTS]** 2026-07-11.

That fourth check deserves emphasis because of what it does: it takes a deferral
("we cannot tell, the data is bad") and converts it into a **negative verdict on
clean data**. The intra-Si-group r_QSE plateau of Hix & Thielemann 1996 (their
Si group, A ≈ 24–45, is one of two QSE clusters; the *single*-group picture is
Bodansky, Clayton & Fowler 1968's) does not describe this manifold. Group-*organised* structure exists — non-group spread is
1.5–2.5× the intra-group spread, which is what a GNN's group-aware features would
exploit — but single-cluster *algebraic reduction* does not hold.

> **How to read a deferral that comes back negative.** The honest reading is
> narrow: the plateau is absent on *the label manifold*, which is
> constant-(T, ρ), started from unphysical compositions, and (above 5 GK)
> bug-displaced. It is not a statement about silicon burning in a star. The
> project's own **R-18** goes further and asks whether the r_QSE diagnostic's
> null distribution is even known — i.e. whether 0.8 dex of intra-group spread is
> large. Until that is answered, the negative verdict is a fact about a statistic
> whose scale has not been calibrated.

## I.9 Self-check for S11

1. Name the four things a one-zone burner deliberately omits, and say for each
   whether it makes the burner a *worse model of a star* or *not a model of a
   star at all*.
2. Why is `use_hydrostatic` the only bbq mode that can produce a trajectory?
3. The campaign used the MESA version with a known bug. Give the argument, and
   the measurement that validated it.
4. `run_campaign.py` does not trust bbq's exit code. What does it check instead
   and why?
5. The Yₑ = 0.45 canonical cell was substituted by 0.455. What forced that, and
   what makes the substitution acceptable practice?
6. Validation check 2 reports a 9-dex distance from NSE and does not fail. Explain
   in one sentence.

---

# Part II (S12) — Trajectories and the eps_nuc pin

**A short node with one long lesson**: a column in a data file whose meaning is
not documented has to be established by *experiment*, and doing it properly looks
like hypothesis testing.

## II.1 The file format

One trajectory file, from `lib_hydrostatic.f90`:

```
age  dt  eps_nuc  eps_neu  <iso_1> <iso_2> … <iso_n>
0.0  1e-10  …                                        ← row 0: initial state
…
```

- one row per output interval; **row 0 is the initial state**, with `dt` a
  10⁻¹⁰ placeholder;
- `dt` is the *per-row burn duration*, not a cumulative age;
- the isotope columns are mass fractions in the network's own order — and
  `load_trajectory` **validates that order against the project's isotope table**
  and raises if it differs. That check has no cost and closes an entire class of
  silent-corruption bug;
- the shipped files encode (logT, logRho) in the filename; rerun files do not,
  so `load_trajectory` **refuses** to guess for `source="rerun"` and requires
  them explicitly from the campaign manifest.

That last design choice is worth naming: the function could have parsed a rerun
filename and been right most of the time. Refusing instead makes the manifest
authoritative and makes a mismatch impossible rather than unlikely.

## II.1b What a trajectory row is *not*

Four things that a row in these files looks like but is not, each of which has
bitten someone.

**Not a solver step.** The output cadence is `times.txt`; the solver takes as
many internal substeps as it needs inside each interval. So the composition
change across a row is an *integral*, and any comparison against an instantaneous
rate is a quadrature question. This is why the handshake restricts to
linearisable cells (τ > 10Δt) and why the flux-route energy comparison uses a
trapezoid and inherits its error (§IV.7's 2.1% open margin).

**Not full precision.** The shipped label CSVs are float32 upstream; this project
parses everything as float64 but cannot recover what float32 destroyed. For a
cancelled quantity — and §IV.6 shows dominant species whose net evolution rides
on κ ~ 10⁻³ columns — float32 label noise is ~10⁻⁷ relative, which is
**larger than the net signal divided by the gross scale** in the worst cases.
`tier1.md` §VIII.E.4 flags the float32/float64 boundary; the sharpest form of it
is: *the labels may not contain the cancellation the model is being asked to
learn.* That is a genuinely alarming sentence and it has never been quantified.
Registered as **T-28**.

**Not uncensored.** `final_*` is floored at exactly 10⁻¹⁵ (measured attained),
so trace species are clamped, not measured. A model trained on log X will learn
the clamp as a target. The Step-5 handshake already found that 25.1% / 12.6% of
its rate-level failures are the "subfloor controller" class — the dominant
channel's reactant is below the label floor, so the label cannot express what
drove the change. **[RESULTS]** 2026-07-10.

**Not a state a star was in.** Constant (T, ρ), a hand-built initial mixture, no
mixing, no expansion (§I.1, §0.2.5). It is one operator of a split, exercised
alone.

## II.2 The composition route to energy — derived

To pin the eps_nuc column you need an *independent* way to compute the energy
released over an interval. The composition route is the one that needs no rates
at all.

Nuclear energy release is the decrease in total rest mass. Over an interval where
the composition changes by ΔYᵢ (molar abundances, per gram),

$$
E_{\mathrm{comp}} \;=\; -\,N_A \sum_i m_i\,\Delta Y_i \;\times\; c^2 ,
$$

and using mass excesses Δmᵢ = mᵢ − Aᵢ m_u (Tier 0 §0.3.1) with
Σ Aᵢ ΔYᵢ = 0 exactly by baryon conservation, the m_u term drops and

$$
\boxed{\;E_{\mathrm{comp}} \;=\; -\,N_A \sum_i \Delta m_i\,[\mathrm{MeV}]\;\Delta Y_i \times (1.602\times10^{-6}\ \mathrm{erg/MeV})\;}
$$

in erg per gram (mass excesses from AME2020, Wang et al. 2021). [derived here]
This is **exact and quadrature-free**: it uses only the endpoint compositions and
a table of nuclear masses. It does not care about rates, screening, the solver,
or the timestep. That independence is what makes it a valid oracle. (E_comp as
written is the *gross* release; the file quantity the pin compares to is
E_comp − ∫ε_ν dt, **[RESULTS]** 2026-07-11.)

The flux route, for contrast, is

$$
E_{\mathrm{flux}} \;=\; \sum_j Q_j \Phi_j ,
$$

which needs the rates, a quadrature over the interval, and the Q-values. It is
the route the *emulator* will use (invariant #5), and it is therefore the one
that must be checked — not the one to check against.

> **A trap Tier 2 §IV.8 names and this node inherits.** If the Q-values are
> themselves derived from the same mass table as E_comp, then E_flux ≡ E_comp is
> an algebraic identity given ΔY = νΦ, and comparing them checks arithmetic, not
> physics. The comparison is only informative when the two legs have independent
> provenance — which is exactly why §II.3's pin compares against the **file
> column** (bbq's own accounting) rather than against the project's flux route.

## II.3 The pin, as a hypothesis test

The question: what does the trajectory file's `eps_nuc` column mean? The
candidates, from reading bbq and knowing the training CSVs' conventions:

| axis | options |
|---|---|
| integration | **integrated** over the row's dt [erg/g] vs **rate** [erg/g/s] |
| normalisation | ×1 vs ×10¹⁶ (the training CSVs divide by 10¹⁶) |
| neutrinos | gross vs **net of neutrino losses** |

Eight candidates. `scripts/step6_eps_pin.py` evaluates all of them against
E_comp (§II.2) on 15,746 / 13,506 pre-stall intervals per network, with dt
spanning 10⁻¹⁰ to 9.5 × 10⁹ s — twenty decades.

The discriminating statistics, and *why each one discriminates*:

| statistic | what it rules out |
|---|---|
| median log₁₀ of the ratio | the normalisation axis — a factor 10¹⁶ is a 16-dex offset |
| **slope of median log-ratio vs dt decade** | the integration axis — an integrated quantity read as a rate has a ratio ∝ dt, i.e. **slope exactly +1** |
| sign agreement | the neutrino axis — gross vs net differ in sign exactly where burning and neutrino losses nearly cancel |

The result, **[RESULTS]** 2026-07-11:

- **integrated, net of neutrinos, no 1e16 normalisation.** Median log₁₀|ratio| =
  −0.000 with IQR [−0.000, +0.000]; sign agreement 0.9933 / 0.9981; **slope vs dt
  decade = 0.000 across twenty decades**.
- The rate reading shows the predicted wrong-convention slope **+1.00** and a
  median offset of −2.2 / −1.3 dex.
- Net-of-ν beats gross decisively: sign agreement 0.91 / 0.81 for gross.
- And the conclusion matches the source read: `bbq src/lib_bbq.f90:453`,
  `out% eps_nuc = avg_eps_nuc * in% time`.

**Why this is a good piece of work and not just a lookup.** The source read alone
would have given the answer in five minutes. The measurement gives the answer
*plus* a slope over twenty decades that would have caught a per-row dt bug, a
sign-agreement statistic that independently confirms the neutrino handling, and a
falsifiable record. Tier 1 §VIII.D's habit — *ask of any green check what would
still be wrong if it passed* — applied here says: reading the source would not
have told you whether the `dt` column you divide by is the right one.

The consequence is pinned in code, and pinned defensively:

```python
TRAJ_EPS_CONVENTION: str | None = "integrated"
# the converters REFUSE to run if this is reset to None
```

`eps_nuc_rate()` and `eps_nuc_integrated()` both route through
`_resolve_convention`, which raises if the pin is unset. A module-level constant
that a function refuses to work without is a small piece of executable policy —
the same pattern as Tier 1 §VII's guards.

**A cross-check that arrived free.** With the convention pinned, the *flux* route
could be compared: ∫ΣQⱼRⱼ dt / E_comp on rate-stable pre-stall intervals gives
median **0.979 / 0.996** **[RESULTS]** 2026-07-11. mesa_80 sitting at a 2.1%
median is outside a 1% band, and the verdict document carries it as an **open
margin item** rather than declaring the energy gate passed on that leg. Which is
correct: the trapezoid quadrature error, float32 label noise, and rate-config
differences have not been separated, and until they are, 2.1% is a number with an
unknown decomposition.

## II.4 The stall, and its two reinterpretations

This is the tier's best example of a measurement being reinterpreted twice, each
time getting sharper.

**Reading 1 (Step 5, 2026-07-10) — "the trajectories are broken."** Composition
freezes (max |ΔX| per interval < 10⁻¹⁰) from median age 2.2 × 10⁵ / 3.9 × 10⁴ s
while eps_nuc keeps rising. The frozen states are **not** NSE: at T₉ = 6.1,
ρ = 1.8 × 10⁸, Yₑ = 0.467 the file says ³⁰Si-dominated with X = 0.58, while NSE
says ⁵⁶Fe = 0.69. Hypothesis: bbq's implicit stepping stalls once the output dt
grows to ~10¹⁰ s, far beyond any physical timescale. Consequence: use pre-stall
rows only. **[RESULTS]** 2026-07-10.

**Reading 2 (Step 6, 2026-07-11) — "it is an attractor arrival, and the tail is
real."** Two things changed the reading:

1. The rerun campaign, with a cadence that cannot produce the output-dt blowup,
   **still** shows terminal freezing at high T₉ — so the blowup is at most
   secondary.
2. A census over *all* 1508 shipped files found that after the first-quiet row,
   composition **resumes** super-tolerance changes at late giant output dts, with
   eps_nuc rising. The rules differ on **459 / 1508** files. **[RESULTS]**
   2026-07-11.

The mechanistic picture that explains both: **the strong sector reaches its
(displaced) equilibrium and freezes, while the weak sector keeps running.** Weak
reactions are slow, one-directional, and not in balance (§0.7.1; the
quasi-equilibrium of Hix & Thielemann 1996 is equilibrium with respect to the
strong and electromagnetic reactions only) — so once the strong pairs
equilibrate, composition changes at the weak timescale, which is long. Those tail rows are legitimate relaxed states of the label dynamics
(equilibrated strong pairs + active weak columns) and **belong in the kill-test
manifold** — indeed they are the *most* relevant rows, since deployment happens
on relaxed states.

The guard was changed accordingly:

| mode | rule | what it marks |
|---|---|---|
| `terminal` (**default**) | the row after the *last* interval reaching tolerance | excludes only a trajectory-ending quiet tail |
| `first_quiet` | the *first* interval below tolerance | **arrival at the attractor** — now used as a phase marker, not a cutoff |

And `first_quiet` was retained rather than deleted, for two reasons: it
reproduces Step-5 row selections exactly (so old numbers stay checkable), and it
is the natural **phase split** for the kill-test — `RelaxedRows.attractor` marks
rows at or after arrival, letting §IV report "relaxing" and "attractor" phases
separately. A discarded rule that becomes a useful diagnostic is a good sign
about the original measurement.

**The cold-start bug the change also fixed.** Canonical Si mixes at T₉ = 2.5
produce *exactly zero* early-interval changes — nothing is burnable in 10⁻⁸-s
steps — so a first-quiet rule truncated whole runs at row 0. The terminal rule
keeps them, and they do evolve at the wall (eps rate 10⁶–10⁷ erg/g/s).
**[RESULTS]** 2026-07-11. A rule that was merely conservative on one dataset was
catastrophic on another; only running it on both revealed that.

## II.5 Self-check for S12

1. Write the composition route to energy from mass excesses and say which
   conservation law makes the m_u term drop out.
2. Why is the composition route a valid oracle for the file column but *not* for
   the project's own flux route?
3. The pin's decisive statistic is a slope, not an offset. Why?
4. What would you conclude from a slope of exactly +1?
5. Give the mechanism that reconciles "composition frozen" with "eps_nuc rising".
6. Why was `first_quiet` kept after the default moved to `terminal`?

---
# Part III (S13) — Silicon burning on real histories, and the label pathology

**The payoff node, and the one that changed the project.** Everything before this
was instrumentation. Here the instruments get pointed at the dataset the emulator
is supposed to learn, and the dataset fails.

## III.1 What a real trajectory looks like

Take one constant-(T, ρ) hydrostatic run at, say, T₉ = 4, ρ = 10⁸, starting from
a silicon-rich mix. Read the output rows in order and you see four phases:

| phase | age | what happens |
|---|---|---|
| **1 — free-particle relaxation** | 10⁻⁸ … ~10⁻⁶ s | whatever free n, p, α the initial composition carried are captured almost instantly: $\lvert \Delta X\rvert / X \sim 1$ in a single step. A **stiff relaxation**, not a linear step |
| **2 — strong-sector equilibration** | ~10⁻⁶ … 10⁰ s | the fast capture/photodisintegration pairs balance within each group; κ on those columns falls; the composition organises into the Si and Fe groups |
| **3 — QSE burning** | 10⁰ … 10⁴–10⁶ s | net flow through the bridges carries material from the Si group to the Fe group. **This is the physics the project is about**; e_nuc is roughly steady |
| **4 — weak drift** | after arrival | strong sector frozen at its attractor; Yₑ continues to fall through electron captures; composition changes slowly |

Phase 1 is the single most under-appreciated fact about the *training* labels.
The Sobol initial compositions carry free nucleons (median X_neut ≈ 1.7 × 10⁻²),
so even the **shortest label timestep** is not a linear step. The measurement:
**99.99% / 100.00% of (state, isotope) cells have τ < dt** at dt₁ ≈ 1.01 × 10⁻⁶ s,
with label |ΔX|/X median ≈ 1, and only **20 / 0** linearisable cells out of
2.4M / 4.5M **[RESULTS]** 2026-07-10.

Read that again. **Every label in the shipped training set encodes a full stiff
relaxation, at every timestep, everywhere in the box.** There is no "small step"
regime in this dataset. Consequences:

- Target A's Φ is a *time-integrated effective flux* Φⱼ = ∫φⱼ dt over the label
  interval, never an instantaneous rate. `CLAUDE.md` states this and
  `fluxes/integrate.py` is the reference producer.
- Conditioning the model on log Δt is conditioning on the wrong variable; the
  natural one is Δt/τ, since what varies across the dataset is *how many
  relaxation times* the step covers (Tier 2 **R-10**).
- Any handshake between the engine's instantaneous rates and the labels can only
  be attempted on the small subset where τ > 10Δt; that is why the trajectory
  handshake is restricted to linearisable cells (median rate-level residual
  3.6 × 10⁻³ / 2.8 × 10⁻³, ≤5% for 90.3% / 94.4% of cells **[RESULTS]**
  2026-07-10).

## III.2 The census: how far are the labels from NSE?

The question that started the investigation is simple. At high temperature,
silicon burning should approach NSE (§0.2, §0.3.3): the fast pairs balance, and
with enough time the composition should be the Saha solution X(T, ρ, Yₑ). So take
the **longest** label (dt = 10² s), at **high** T₉, and compare against the
project's independent Saha solver.

The solver is independent in the sense that matters: it is built from the same
pynucastro nuclear inputs (Smith Clark et al. 2023; Rauscher et al. 1997 /
Rauscher 2003 partition functions, binding energies, spins)
but solves the equilibrium conditions itself, in log space with a damped Newton
and a bisection fallback, and it agrees with pynucastro's own NSE solver to
**2.7 × 10⁻¹⁰ / 1.5 × 10⁻¹⁰ dex** over a 27-state grid **[RESULTS]** 2026-07-10.
It is a trustworthy reference.

The result, over T₉ bins from [5.0, 5.5) to [7.0, 7.94), 120 states per bin,
**[RESULTS]** 2026-07-11:

| quantity | mesa_80 | mesa_151 |
|---|---|---|
| median max\|Δlog₁₀X\| over X > 10⁻⁶ species | **6.9 → 11.5 dex** across bins | **6.7 → 13.0 dex** |
| fraction of states more than 1 dex from NSE | **1.000 in every bin** | **1.000** |

**Not one sampled high-T₉ label endpoint is anywhere near NSE.** And the
discrepancy *grows* with temperature, which is the opposite of the physical
expectation — hotter should mean faster equilibration.

The displaced states have structure, which is the first clue that this is a
mechanism rather than noise:

- **high ρ**: ³⁰Si / ²⁹Si / ²⁶Mg dominated. State 80 (T₉ = 7.08, ρ = 3.0 × 10⁸):
  si30 X = 0.578, where NSE says fe56 = 0.72.
- **low ρ**: ¹²C / ¹⁶O dominated. State 646 (T₉ = 7.78, ρ = 2.0 × 10⁷):
  c12 = 0.294 + o16 = 0.266, where NSE says ⁴He and the Fe group.

And these are **the same class of state** as the Step-5 trajectory-stall frozen
compositions (³⁰Si-dominated at T₉ = 6.1). Two independent investigations, from
different directions, landed on the same anomaly.

## III.3 The mechanism: gh-575, traced from a Fortran branch

The cause is a bug in MESA r23.05.1's detailed-balance reverse-rate
construction — MESAHub/mesa issue **gh-575** (opened 2023-08-07, closed
2024-05-06; the fix, PR #632, merged May 2024 and first shipped in release
24.08.1 — verified by measurement, **[RESULTS]** 2026-07-10; the release-note text
is recorded in **[RESULTS]** 2026-07-09: "incorrect phase space factors for
reverse reaction rates involving greater than 2 reactants or products …
inconsistent equilibrium compositions … at temperatures exceeding 4 GK").

**The static locus.** In `rates/private/reaclib_support.f90`, `compute_rev_ratio`
applies the detailed-balance phase-space factor

$$
\mathrm{fac} \;=\; \frac{1}{N_A}\left(\frac{10^{9}k_B}{2\pi\hbar^{2}N_A}\right)^{3/2} \;=\; 9.868\times10^{9},
\qquad \log_{10}\mathrm{fac} = 9.994,
$$

together with its accompanying T^{3/2}, **only in the single-product branch**
(`reaclib_support.f90:197, 222–235`; the constant is Rauscher & Thielemann
2000's 9.8685 × 10⁹ T₉^{3/2}, recomputed 9.86846 × 10⁹ with CODATA 2018). Tier 1
§III derives why that factor is there: the reverse of an
A + B → C reaction involves a change ΔN in the number of free particles, and each
unit of ΔN brings a factor of (2πμkT/h²)^{3/2}/(ρN_A) from the phase-space
integration. A reverse rate with more than one product needs the factor raised to
the power $|\Delta N|$; the buggy code applies it once, or not at all.

**The empirical size.** Measured against pynucastro at T₉ ∈ {1.6, 4.0, 7.9}
**[RESULTS]** 2026-07-09:

| channel class | \|Δlog₁₀\| |
|---|---|
| \|ΔN\| = 1 multi-body inverses | **10.0 – 11.1 dex** |
| \|ΔN\| = 2 (h1+h1+he4+he4 → he3+be7) | **20.6 – 22.7 dex** |
| chapter-8 photodisintegration reverses (1 → 3) | **low by 9.5 – 11.3 dex** |
| harness control: all matched clean REACLIB forwards | median **0.0 exactly** |

The last row is what makes the rest credible: the comparison harness reproduces
clean channels bit-for-bit, so the 10-dex discrepancies are not the harness.

**The chapter-8 row is the one that matters here, and it goes beyond what the
NNN paper's own Appendix B names.** The paper names one light-sector channel
(n + n + ⁴He + ⁴He → ³H + ⁷Li) and states the class — "all reactions involving
more than two reactants and/or products" — which contains the 1 → 3 reverses
without identifying them, and it states that mesa_80's equilibrium composition is
"qualitatively consistent" with the larger networks; this project found that the
1 → 3 photodisintegration reverses — including **c12 → 3α,
the reverse of the triple-α reaction**, and be9 → n + 2α, li6 → n + p + α — are
low by 9.5–11.3 dex in stock r23.05.1. Those reactions control **light ↔ heavy
equilibration**: they are how the free-α reservoir talks to the carbon/oxygen
sector.

Now the mechanism is visible. If c12 → 3α is suppressed by ten orders of
magnitude while 3α → c12 is correct, then detailed balance is broken by ten
orders of magnitude on the reaction that links the α reservoir to everything
above it. The system relaxes to a **fixed point of the broken rate set** — an
equilibrium of a rate network that satisfies no thermodynamic constraint. At high
ρ that fixed point is ³⁰Si-dominated; at low ρ it is ¹²C/¹⁶O-dominated, because
carbon cannot be photodisintegrated back into α particles.

**This also explains the κ floor.** Tier 2 §IV.8b's Wegscheider measurement (the
cycle condition of Wegscheider 1901, in the generalised form of Schuster &
Schuster 1989) found Q ∉ rowspace(ν) for the strong sector and predicted a κ data floor of
6 × 10⁻⁴ … 4 × 10⁻³; the measured stock-MESA κ floor at NSE is median
3.6 × 10⁻³ / 3.3 × 10⁻³ **[RESULTS]** 2026-07-10, and **κ → 1.0 exactly on
gh-575 channels** — a broken pair is maximally out of balance by construction.

## III.4 The witness experiment

A mechanism is a story until it makes a prediction that could fail. The
prediction: *if gh-575 is the cause, then running the exact same label states
under the exact same configuration but with the fixed MESA should relax toward
NSE instead.*

`scripts/step6_label_nse_census.py` ran it on the two witness states, with bbq
built against both MESA versions, under exact label conditions and initial
compositions **[RESULTS]** 2026-07-11:

| | state 80 (T₉ 7.08, ρ 3.0e8) | state 646 (T₉ 7.78, ρ 2.0e7) |
|---|---|---|
| **shipped label** | si30 = 0.5615 | c12 0.294 + o16 0.266 |
| **stock r23.05.1 bbq** | reproduces the label to **0.01 dex** | reproduces to **0.03 dex** |
| **MESA 24.08.1 bbq** (gh-575 verified fixed) | **fe56 = 0.985**, 1.2 dex residual, Yₑ still evolving | **he4 = 0.521 + fe56 = 0.378** |
| **independent pf-true reference integrator** | fe56 = 0.70 at 10⁻⁶ s (vs 24.08.1's 0.66) | — |

Three independent codes — stock bbq, fixed bbq, and this project's own BDF
integrator with pf-corrected reverse rates — arrange themselves exactly as the
mechanism predicts. Stock reproduces the pathology; fixed and independent both
relax toward NSE.

**This is the strongest single piece of evidence in the whole of Phase 0**, and
it is worth naming why. It is a *controlled* experiment: same inlist, same
initial composition, same solver tolerances, same screening, same weak tables —
one code version changed (whose relevant diff is the gh-575 fix; 24.08.1 also
carries a minor spillover into approx21), and the outcome switches from
"reproduces the shipped
labels" to "does the physically expected thing". Everything else in this project
is a comparison of computed numbers; this is an intervention.

**The dt-freeze signature** seals it. State 80's final composition is *identical
to four digits* (si30 = 5.615 × 10⁻¹) across **dt = 10⁻⁵ … 10¹ s**, and is
already reached at dt = 10⁻⁶ **[RESULTS]** 2026-07-11. A slow transient would
show dt dependence. A fixed point does not. The labels are sitting at an
attractor of the label generator, reached almost immediately and held for seven
decades of time.

## III.4b How this could have been caught on day one

Worth extracting as a reusable test, because the pathology was found in Step 6
and could have been found in Step 1 with an hour's work and no MESA at all.

**The generic test: is the label set a fixed point of its own generator, and is
that fixed point the one physics predicts?**

For a sample of high-temperature states:

1. take the label at the **longest** Δt;
2. compare it against an independent equilibrium reference — the Saha solution
   X_NSE(T, ρ, Yₑ);
3. compare the label **across Δt decades** — the freeze signature.

Step 2 needs a Saha solver, which pynucastro ships. Step 3 needs nothing but the
shipped CSVs — and it is the *decisive* one: a composition identical to four
digits across dt = 10⁻⁵ … 10¹ s is a fixed point, full stop. **That check reads
nine files and takes a minute.** It would have fired on day one.

Three general lessons, stated so they transfer:

**(i) A benchmark dataset is a fixed point of its generator, and that is a
testable claim about the generator, not about nature.** Any dataset produced by
running a solver to completion encodes the solver's attractors. Checking those
attractors against an independent equilibrium theory is the cheapest possible
audit of a labelled dataset, and it is not, to our knowledge, standard practice in
scientific ML.

**(ii) Invariance across a control parameter is a stronger signal than agreement
with a reference.** The dt-freeze is more convincing than the NSE distance,
because it needs no reference at all — it is internal to the data. Look for
quantities that *should* vary and do not.

**(iii) The check that fires is the one comparing to something the pipeline does
not share.** Tier 1 §VIII.D's habit — *ask of any green test what would still be
wrong if it passed* — generalises to *any check whose two sides share a
provenance can only find typos.* The rate cross-check (Tier 1 §VI) compared MESA
against pynucastro and found the bug's *static* form in Step 4; it took an
independent **equilibrium** reference, which shares no code with either, to find
the bug's *dynamical consequence*.

Registered as **T-29**: adopt the fixed-point audit as a standing check on any
labelled dataset the project ingests, including its own future Φ labels.

## III.5 The consequence: Yₑ itself is wrong

If the bug only displaced *which* silicon isotope dominates, it would be a
composition-detail problem. It is not, and this is the finding that forced an
escalation.

At state 80, over 10² s **[RESULTS]** 2026-07-11:

| path | Yₑ evolution |
|---|---|
| labels / stock r23.05.1 | 0.4717 → **0.4713** (Δ = −4 × 10⁻⁴) |
| fixed MESA (24.08.1) | 0.4717 → **0.4619** (Δ = −9.8 × 10⁻³) |

**A factor of ~25 in the Yₑ change** (24.5 at the quoted 4-digit precision). The
reason is direct: electron-capture rates are per-nucleus and species-specific
(§0.7.3; Heger et al. 2001 tabulate the dominant EC flows; Langanke &
Martínez-Pinedo 2000 give the iron-peak rates), so *which species host the
material* determines which EC channels are active. A composition frozen at
si30-dominated hosts EC on silicon-group nuclei; a composition relaxed to
fe56-dominated hosts EC on the iron peak, where the rates are much larger and the
thresholds much more favourable. The bug displaces the composition, the
composition selects the EC channels, and the EC channels set dYₑ/dt.

Put in the terms of §0.9's budget: the **discrepancy between the label Yₑ
evolution and the physically-correct one is ~9 × 10⁻³ over 10² s** — which is
larger than the project's entire per-trajectory Yₑ budget (5 × 10⁻³) and three
thousand times the per-step gate. At T₉ ≳ 5, the labels are not merely imprecise;
they are outside the tolerance the emulator is being asked to achieve, in the
quantity the emulator exists to predict.

## III.6 The epistemics: what a negative result about your own dataset obliges

This is the part of Tier 3 that is about method rather than physics, and it is
the part most worth internalising.

**What was superseded.** Step 4 had established a working premise: the training
labels were assumed to have been generated with the authors' *locally fixed*
MESA — an inference from the paper's Appendix B, which reports "We fixed the bug
in the current mesa version" without stating which build produced the training
sets, and whose software list names mesa-23.05.1 — so labels are clean and *our*
stock MESA is the outlier. That premise was reasonable, an inference from the
paper rather than a statement in it, and recorded (RESULTS 2026-07-09 phrases it
as "the paper's App. B says so", which over-reads the appendix in the same way;
corrected here in the 2026-08-18 audit). It is now known to be false
at the fixed-point level for T₉ ≳ 5 — because the chapter-8 1 → 3 reverses this
project found "beyond the paper" are demonstrably label-active, whatever the
paper's own channel list says. The `RESULTS.md` entry states the supersession
explicitly and identifies which earlier row it overrides. **That is the
discipline: a superseding measurement names its predecessor.**

**What was validated by accident.** ADR 0005 chose stock r23.05.1 for the rerun
campaign on *comparability* grounds, before the pathology was known. The
pathology measurement then showed stock reproduces label behaviour to 0.01 dex —
so the choice was measured-correct after the fact. A decision made for one good
reason turning out to be right for a stronger one is luck, and it should be
recorded as luck rather than as foresight.

**What it forces.** Five consequences were recorded **[RESULTS]** 2026-07-11, and
two of them are *escalations to a human*, not technical fixes:

1. rerun-campaign comparability **validated** (above);
2. the Step-5 stall anomaly **reinterpreted** — the frozen states are the bug's
   displaced pseudo-equilibria; the output-dt hypothesis is at most secondary
   (§II.4);
3. `validate_campaign`'s terminal-NSE check must **expect** the displaced
   equilibrium on stock reruns at T₉ ≳ 5, with 24.08.1 as the physics-true
   witness (§I.8, check 2);
4. ⚠ **Phase-1 supervision at T₉ ≳ 5 faces a benchmark-versus-physics fork** —
   escalated, human decision;
5. ⚠ **NNN itself was trained on these labels** — an external-communication
   decision, escalated.

**The fork (item 4) is a genuine dilemma, and it is worth stating both horns
fairly.**

> **Horn A — train on the labels.** The emulator's job is to reproduce the
> reference solver. The published benchmark (NNN) was trained on these labels,
> and comparability requires matching them. Training on physics-true labels at
> T₉ ≳ 5 would make every published comparison in that band meaningless — the
> emulator would "lose" against a baseline that is reproducing a bug.
>
> **Horn B — train on corrected physics.** The emulator's job is to be a fast
> nuclear network. A network that reproduces a known bug is a liability the
> moment anyone uses its output for science, and the bug is *in the quantity the
> project exists to predict* (§III.5). Every downstream Yₑ conclusion in that
> band would be wrong by design.

There is a third option that the study notes should name because it is probably
right and nobody has written it down: **declare a validity domain.** T₉ < 5 is
where local Φ labels are proven feasible (§V.4), where every kill-test gate
passes, and where the labels are not pathological. Restricting the emulator's
claimed domain to T₉ < 5 and handing T₉ ≥ 5 to an NSE table or the real solver
(which is the §0.8.3 hybrid anyway, and exactly what an OOD-fallback gate is
*for*) resolves the fork by refusing it. It costs a claim about the hot band and
buys a defensible product. Registered as **T-03**.

**Item 5 is the uncomfortable one.** The published NNN model, its reported
accuracies, and this project's own reproduction of them (**[RESULTS]**
2026-07-08, ratio 1.000 in all 108 comparisons) are all measured against labels
that are wrong above 5 GK. That does not make the NNN paper's *methods* wrong —
its errors are measured against its own labels, which is the standard and correct
protocol — but it does mean that a statement like "the NNN reproduces the
composition to X%" carries an unstated qualifier in that band. How and whether to
communicate that externally is a judgement call for a person, and the project
correctly escalated it rather than deciding it inside a results log.

## III.7 What the pathology does *not* invalidate

Being precise about the blast radius matters, because a finding this large
invites over-generalisation.

**Still valid:**

- **Everything below T₉ ≈ 5.** The gh-575 channels are light-sector and
  chapter-8 multi-body; they matter where the α/nucleon reservoir controls
  equilibration, which is the hot regime. The QSE window (3.3–5 GK) shows
  integrator/label agreement of 0.74–0.99 in band **[RESULTS]** 2026-07-12.
- **The kill-test itself.** It is a measurement *on the label manifold*, and the
  reruns are exactly label-comparable (0.996/0.998 early-time agreement). The
  question "is Target A viable on this data" is well-posed regardless of whether
  the data is physically right — because that is the data the model will see.
  §IV.8 develops this.
- **All the algebra.** Conservation, the projector, the flux engine's rate
  agreement, the Saha solver — none of it depends on the labels being right.
- **The bridge sets and the ⁴⁵Sc confirmation**, which live in the QSE window.

**Compromised:**

- Any *physical* claim about equilibrium structure at T₉ ≳ 5 on this data.
- The Guidry ε-sweep result read as a statement about silicon burning (as opposed
  to about the label manifold) — see §IV.5, which is careful about exactly this.
- Yₑ supervision in the hot band (§III.5).

## III.8 Self-check for S13

1. Why does the *shortest* label timestep in the shipped set encode a full stiff
   relaxation? Give the measurement.
2. Reproduce the argument from "a phase-space factor applied only in the
   single-product branch" to "the labels sit at a ¹²C/¹⁶O-dominated fixed point
   at low density".
3. The census found the NSE distance *growing* with temperature. Why is that the
   opposite of the physical expectation, and why is it the signature of a
   mechanism rather than of noise?
4. Describe the witness experiment, name its one changed variable, and say what
   result would have falsified the mechanism.
5. The bug displaces composition. Explain in two steps why it therefore
   corrupts Yₑ, and give the measured factor.
6. State both horns of the benchmark-versus-physics fork fairly, then give the
   third option and what it costs.
7. Name three things the pathology does not invalidate, with the reason for each.

---
# Part IV (S14) — The kill-test

**The decision Phase 0 was built to make.** Tier 2 §0.6 states it as a question
about a matrix; this part asks it of data and reports what came back.

## IV.1 The question, restated

> Let 𝒜 = {j : κ_j > 0.1} be the **active set** — the columns not in
> near-balance. Restricted to 𝒜, is the map φ ↦ νφ well-conditioned, and does it
> carry the physics?

If yes, **Target A** with an equilibrium mask is the architecture: the model
predicts a per-reaction flux, the mask switches off the equilibrated columns, and
dY = νφ conserves everything exactly. If no — either because the net flow spreads
over too many near-cancelled columns, or because the restricted ν is
ill-conditioned — the project falls back to **Target B**: predict dY directly in
a linear space and project onto the constraint manifold.

Six measurable clauses, from `CLAUDE.md`:

| # | quantity | pass | fail |
|---|---|---|---|
| 1 | fraction of \|ΔYₑ\| carried by 𝒜 | ≥ 95% | — |
| 2 | fraction of dominant-isotope \|ΔX\| carried by 𝒜 | ≥ 95% | — |
| 3 | share of net columns near the κ floor | — | > ~30% |
| 4 | cond(S_active) | < 10⁶ | > 10⁸ |
| 5 | maskable-set size under the Guidry ε sweep | non-empty | empty ⇒ full-width |
| 6 | mask churn per step | < 5% | > 5% ⇒ freeze |

Plus two that were carried as assumptions and became measurements: the
**timescale separation** ("6–8 orders", never sourced) and the **energy
consistency** residual.

## IV.2 The instruments

`src/gnn_nucleo/killtest/` is four small modules, and their design is worth
reading as an argument.

**`strata.py` — one definition of the grid, imported everywhere.**

```python
T9_EDGES = [1.6, 2.5, 3.3, 4.0, 5.0, 6.3, 7.95]
YE_EDGES = [0.45, 0.4667, 0.4833, 0.5001]
```

Six T₉ bins × three Yₑ bins. The bin edges are the regime box's, with extra
resolution across the QSE window. Lifting them into a module "so scripts stop
redefining them" is a small thing that prevents a large class of
almost-but-not-quite comparisons.

**`active_set.py` — primitives that measure and never conclude.** Its docstring
says so explicitly: *"Numbers only — pass/fail thresholds live in
docs/phase0-checklist.md and the verdict document, never here."* Six functions:

| function | what it computes |
|---|---|
| `guidry_masks` | maskable columns per ε, **strictly** via `qse.diagnostics.eligible_mask` so weak columns are excluded structurally (invariant #2) |
| `cond_s_active` | cond of ν restricted to active columns, **rank-revealing** (ratio of extreme *nonzero* singular values; A·ν = 0 always, and Z·ν = 0 on the strong columns / the lepton-extended ν, so the naive condition number is infinite) |
| `carried_fractions` | per-species covᵢ = Σ_{j∈𝒜}\|νᵢⱼφⱼ\| / Σⱼ\|νᵢⱼφⱼ\| |
| `topk_concentration` | cumulative share of the top-k entries |
| `mask_churn`, `timescale_separation` | per-step flips; fastest-balanced-gross / slowest-bottleneck-net |

Two details that are easy to get wrong and are got right here. **`cond_s_active`
excludes the structural null vectors**: A·ν = 0 and Z·ν = 0 hold by construction
(Tier 2 §I.2), so a naive condition number would be infinite for every possible
active set and the gate would be vacuous. And **`carried_fractions` expects ν and
φ restricted to net columns** (forward-or-unpaired), because counting a
forward/reverse pair twice would double the denominator and halve every coverage
number.

**`manifold.py` — row assembly, with a refusal.** It builds the relaxed manifold
from FluxStore trajectory runs, and:

```python
if scr not in ("None", "none"):
    raise ValueError(f"{run_id}: κ/δ analysis requires the UNSCREENED run …")
```

`CLAUDE.md`'s two-κ rule, encoded as code that will not run. Given that the
screened κ floor at NSE is ~7 × 10⁻² and the active-set threshold is 10⁻¹, using
a screened run would put a large fraction of genuinely balanced pairs on the
wrong side of the gate. This is the single highest-value guard in the node.

It also computes the **phase split**: `attractor` marks rows at or after the
`first_quiet` arrival row (§II.4), so every statistic can be reported separately
for the *relaxing* phase (strong sector still equilibrating) and the *attractor*
phase (strong sector done, weak drift continuing).

## IV.3 The two distributions — and why they are different worlds

This is the measurement that reframed the project, and it is the one to
understand before reading any gate.

**Distribution A — the training grid.** 1.03M in-strata states per network,
random Sobol compositions. **[RESULTS]** 2026-07-11:

- median log₁₀ κ ≈ **−0.05 in every stratum** — i.e. κ ≈ 1 everywhere;
- fraction κ > 0.1: **0.985–0.999** (mesa_80), 0.974–0.997 (mesa_151);
- fraction κ < 10⁻³: **0.000**;
- per-state active fraction, median **0.987–1.000**;
- consequently the κ-active union is **all** net columns (327/327, 846/846) in
  every stratum, so S_active ≈ full ν and cond = 41.8 / 57.4.

**Every gate passes, and the pass is vacuous.** There is no cancellation
structure on the training distribution at all. The reason is physical, not
statistical: random compositions carry free nucleons at percent level, so every
capture reaction runs hard in one direction and nothing is near balance. **The
training states are *relaxing*, not *relaxed*.**

**Distribution B — the relaxed manifold.** Pre-terminal rows of 20 shipped + 209
rerun trajectories per network, 4,693 sampled rows each. **[RESULTS]**
2026-07-12:

- fraction κ > 0.1 falls to **0.70 / 0.64** in the T₉ [5.0, 6.3) stratum;
- κ-balanced pairs (κ < 10⁻³) are **≤ 0.4% of carrying pairs everywhere** —
  clean detailed balance essentially never occurs;
- the cancellation structure is a **continuum** of κ ∈ 10⁻³ … 10⁻¹, not a clean
  split into "equilibrated" and "active".

So the QSE cancellation structure — the thing the whole architecture is designed
around — **lives on the relaxed manifold and is absent from the training
distribution**.

**Why this is a regime shift, not a covariate shift.** Tier 2 §III.9 gives the
dynamical reason and it is worth stating here in the form that matters for Tier
4: relaxation *onto* the slow manifold and motion *along* it are different
functions. A model trained on the first and deployed on the second is not
extrapolating — it is being asked a different question. No amount of data
augmentation on the training distribution fixes that; the fix is training data
from the right distribution, which is what `CLAUDE.md`'s Sobol → real-MESA gate
(retrain if real-track 99th-percentile Yₑ error > 3× the Sobol-measured value)
exists to detect. **That gate is predicted to fire**, and Tier 2 **R-07**'s
measurement — the 20 M⊙ track sits within 0.12–0.18 dex of a *line* in the box,
and only 35% / 62% / 82% of the box is within 0.1 / 0.2 / 0.3 dex of a visited
point — is the thermodynamic half of the same mismatch.

**And it is why the kill-test verdict had to be rendered on distribution B.** A
verdict on the training grid would have been a confident, fully-passing,
completely uninformative "yes".

## IV.4 Gate 1 — Yₑ coverage: a structural pass

**PASS at 1.0000**, and the reason is structural rather than fortunate.

Weak columns are stored unpaired in the flux engine (f⁻ ≡ 0), so κ = |φ|/(f⁺+f⁻)
= 1 wherever a weak column carries any flux at all. Verified exactly on
**8,825,170 / 33,189,419** (weak column × relaxed row) samples with f⁺ > 0
**[RESULTS]** 2026-07-12; fluxless weak columns have κ = 0 by the
zero-denominator convention and contribute nothing. Weak columns are also never
maskable, by invariant #2, enforced structurally in `eligible_mask`.

So the |dẎₑ| coverage by any active set of the form {κ > θ}, θ < 1, is exactly 1.

**Read this carefully, because it is a pass that proves less than it looks.**
The gate asks "does the active set carry the Yₑ physics?" and the answer is
"yes, by construction of the active set". It is not evidence that the flux head
will *predict* those columns well; it is evidence that the mask will not delete
them. Tier 1 §VIII.D's habit applies: what would still be wrong if this passed?
Answer — everything about the accuracy of the weak columns, which the gate does
not touch.

What the gate *does* deliver, as a side effect, is the concentration measurement:
top-5 weak channels carry **0.96 / 0.75** and top-20 carry **1.00 / 1.00** of
Σ|dẎₑ| on high-Yₑ QSE-window rows, #1 being ⁵⁶Ni EC at 0.62 / 0.28 (§0.7.3).
That is a real, actionable result: it tells the loss function where to spend.

## IV.5 Gate 5 — the Guidry sweep returns EMPTY

The most consequential single number in the tier.

The Guidry departure criterion (Guidry, Billings & Hix 2013 — their near-
equilibrium test |yᵢ − ȳᵢ|/ȳᵢ < εᵢ, applied with εᵢ = 0.01 in their examples;
Tier 2 §III.10) declares a species equilibrated
when |y − ȳ|/ȳ < ε against a reference equilibrium, and a *reaction* maskable
when all its participants are. The ε sweep is {3 × 10⁻³, 10⁻², 3 × 10⁻²}.

**Measured: maskable columns per row have median AND p90 = 0, at every ε, both
networks.** **[RESULTS]** 2026-07-12.

Not "few". Zero, at the 90th percentile, everywhere.

**Why.** δ_r is measured against **true NSE**, and the label manifold's own
equilibria are Appendix-B-displaced (§III). The manifold does reach *an*
equilibrium — that is what the attractor phase is — but not the one the
criterion tests against. The two are 6.7–13.0 dex apart at T₉ ≳ 5 (mesa_151;
6.9–11.5 for mesa_80) and displaced
by an unknown amount below that.

**Consequences, in order of severity:**

1. **cond(S_active) = cond(ν restricted to all net columns) = 41.8 / 57.4 at
   every ε** (full ν: 41.6 / 57.9) — five orders below the 10⁶ gate. Gate 4
   passes, but for a degenerate reason: the mask is empty, so there is nothing to
   restrict.
2. **The hybrid design's maskable set is empty. Target A operates full-width.**
   Component B's "Guidry prior + learned L₀ gate" loses its prior; the mask
   becomes a purely learned object with no physics initialisation, or is dropped.
3. **Gate 6 (churn) is moot.** Measured churn is 0.00–0.03 flips/step
   (≤ 0.002%/step) at every ε over 35 QSE-window trajectories — trivially below
   the 5%/step freeze trigger. But the mask is empty, so the hybrid-versus-frozen
   decision is settled by **emptiness, not churn**. Recording both, and saying
   which one decided, is the right way to report it.

**What this result is and is not.** It is a measurement about *this label
manifold*, and the manifold is (a) constant-(T, ρ), (b) started from unphysical
compositions, (c) bug-displaced above 5 GK, and (d) evaluated against a criterion
whose reference is true NSE rather than the manifold's own attractor. Every one
of those is a reason the result might not transfer to a physical silicon-burning
trajectory. It is *not* a demonstration that QSE does not occur in stars.

The correct statement, and the one the verdict document makes: **on the data the
model will be trained and evaluated on, there is no maskable set.** That is a
statement about an engineering decision, and it settles that decision.

An open question the notes should carry: δ_r is measured against **true NSE**
when the physically meaningful comparison might be against **the manifold's own
attractor**. Testing departure from an equilibrium the system is not heading
toward is arguably the wrong test. Redoing the sweep with the attractor as
reference is cheap and might well produce a non-empty mask. Registered as
**T-04**.

## IV.6 Gate 2 — the split verdict, and the 1/κ amplification

The gate that did not cleanly pass.

Coverage is measured two ways per row: for the **median** dominant isotope, and
for the **worst** dominant isotope (min over species with X > 10⁻³). **[RESULTS]**
2026-07-12 (the two "≥" entries below are from the verdict document,
`docs/phase0-killtest-verdict.md`, not RESULTS.md):

| stratum × phase | median-dominant coverage | **worst-dominant coverage** |
|---|---|---|
| T₉ < 3.3 | 1.00 typical | ≥ 0.61 |
| [3.3, 4.0) | 1.00 | ≥ 0.36 |
| [4.0, 5.0) relaxing | ≥ 0.95 | **0.1658 / 0.0700** |
| [5.0, 6.3) | **0.62 – 0.80** | **0.0022 – 0.0290 / 0.0084 – 0.0475** |
| [1.6, 2.5) relaxing | 1.00 | 0.90 / 0.75 |

So: the *typical* species' evolution is carried by the active set almost
everywhere, but in the 4–6.3 GK band there exist dominant species (X > 10⁻³!)
whose net evolution rides almost entirely on **near-cancelled columns** —
κ ∈ 10⁻³ … 10⁻¹, i.e. outside the active set.

**Why that is dangerous, quantitatively.** If φ is inferred from features that
scale with the *gross* flux, then an error δ in a gross-scale quantity produces
an error δ/κ in the net flux, because φ = f⁺ − f⁻ and the relative error of a
difference is amplified by (f⁺+f⁻)/|φ| = 1/κ. At κ = 10⁻³ that is a factor of
1000. This is exactly the "κ as a condition number" reading of Tier 2 §II.4(b),
and here it is being measured on the species the composition is made of.

**Why it is nevertheless not a Target-B switch.** Two arguments, both in the
verdict document, and both correct:

1. **ADR 0001's switch conditions do not fire.** cond(S_active) = 41.8/57.4, not
   > 10⁶. Low-κ share is 0.9–24%, not > 90%.
2. **Target B faces the same problem.** The cancellation is in the *labels*: ΔY
   for those species is itself a small difference of large opposing contributions.
   Predicting ΔY directly does not remove the cancellation, it just hides it
   inside the label. Target B would surrender the per-reaction structure (which
   the concentrated bridge and EC channels reward) without removing the
   conditioning problem.

**What it does force** is supervision-level mitigation: Φ-level supervision where
feasible, plus loss weighting on the affected columns. §V.4 is the feasibility.

## IV.7 Gates 3, 7, 8 — spread, timescales, energy

**Gate 3 (spread) — PASS.** The low-κ (κ ≤ 0.1) column share of active net
columns has median 0.9%–24% across every stratum × phase, worst case 0.24/0.21
in the attractor phase of [5.0, 6.3) **[RESULTS]** 2026-07-12. The ~30% FAIL line
is not approached. So the failure mode "net flow spreads diffusely over hundreds
of near-cancelled columns" does **not** occur: the problematic carriers of §IV.6
are **few and identifiable**, which is what makes targeted mitigation possible.

**Gate 7 (timescale separation) — an assumed number, RETIRED by measurement.**
The design documents carried a working figure of "6–8 orders of magnitude" of
separation between the fast equilibrated sector and the slow bottleneck flow —
unsourced (the phrase "6–8 orders of magnitude" does occur in Guidry, Billings &
Hix 2013, but there it compares a realistic network's fastest rates to an
α-network's — a different quantity; Guidry 2012 gives 10–20 orders between the
fastest and slowest timescales of a thermonuclear network). Measured as log₁₀[(fastest κ-balanced gross rate)/(slowest
95%-bottleneck net rate)]: per-stratum medians span **−12.2 … +1.4**, with p10 at
−25 and p90 at +3.5 **[RESULTS]** 2026-07-12.

The distribution is broad and **mostly negative** — i.e. there is no cleanly
separated fast sector at all, because κ-balanced pairs are ≤ 0.4% of carrying
pairs and are mostly low-flux. The assumed figure is not merely imprecise; it
describes a structure that is absent.

**This retirement has teeth.** The rollout governor specified for Component C
(the Ono & Sugimura 2026 timescale-rescaled update) was adopted for row 15 on the
premise of "a separated fast sector" — a project premise, not the paper's: Ono &
Sugimura's own stated premise is that at short Δt the physical change is smaller
than the prediction error, and their rescaling Δt/τ_ε · Δx_pred(τ_ε) presumes
approximately linear evolution over τ_ε. That premise is now measured false. `tier1.md` §VIII.F ranks
"a design with a falsified premise and no study node" as the highest-leverage
open item in the project, and it is right to.

**Gate 8 (energy) — two readings, reported separately.** The verdict document
does something unusual and correct here: it declines to collapse two different
measurements into one verdict.

- *The gate as written* (e_nuc = ΣQⱼφⱼ from the same net fluxes as composition):
  **PASSES** with ≥3 orders of margin — residual median 6 × 10⁻⁶ … 2.5 × 10⁻⁵,
  max 8.7 × 10⁻⁴, fraction ≤ 1% = 1.000 in every stratum **[RESULTS]**
  2026-07-12. With the caveat that with constant mass-derived Q on both sides
  this comparison is near-algebraic (Tier 2 §IV.8): it bounds Q-table rounding,
  not route physics.
- *The independent-leg check* (engine-rate energy vs label-ΔX energy, §II.3):
  median ratio **0.979 / 0.996** **[RESULTS]** 2026-07-11. mesa_80 at a 2.1%
  median is **outside** a 1%
  band, and is carried as an **open margin item** into Phase 1.

Reporting "passes with margin" and "fails by 2×" side by side, with the
explanation of why they measure different things, is what an honest gate looks
like.

## IV.8 The verdict, and the statistics it does not carry

**VERDICT: Target A, full-width, no Guidry masking, weak sector structural.**
Unconditional for T₉ < 4.0; conditional for [4.0, 5.0) (worst-species coverage
fails, mitigation measured-feasible); deferred for [5.0, 6.3) (label physics
bug-displaced, Φ labels blocked on integrator cost). No ADR-0001 switch condition
fires; no PIVOT criterion is met.

**Now the part the verdict document does not have, and should.**

Every headline number above is a median or a fraction over ~4,693 rows per
network, and **those rows are not independent.** They are ≤ 24 rows sampled from
each of 229 trajectories, and rows within a trajectory share a (T, ρ), an initial
composition, and a continuous dynamical history. Tier 2 §V.3 measured the
intraclass correlation: **ICC 0.22–0.70 across trajectories, design effect
6.5–18.6** (Kish 1965's deff = 1 + (m − 1)ρ; Shrout & Fleiss 1979 for the ICC).
So `RESULTS.md`'s "657k carrying-pair samples" carry roughly **300 independent
systems**.

What that does and does not affect:

| affected | not affected |
|---|---|
| every p-value and confidence interval (all currently unstated) | point estimates — medians and fractions are unbiased |
| any claim of the form "significantly below the 30% line" | the **empty-mask** result, which is p90 = 0 (a hard zero cannot be a sampling artifact) |
| the Spearman correlations' stated significance (+0.491/+0.498, "p ≈ 0" over 657k samples — the p-value is meaningless at n_eff ≈ 300) | the structural results (κ ≡ 1 on weak columns) |

The fix is one afternoon's work: **bootstrap over trajectories, not rows.** Tier 2
**R-08**, and this tier's **T-05**. Until it is done, the verdict's point
estimates stand and its inferential language should be removed.

**A second missing control**, and it is the one a hostile referee reaches for
first: **there is no null distribution for any of these statistics.** Is 0.87 dex
of intra-group r_QSE spread large? Is a Spearman of +0.49 between log κ and log δ
good agreement or mediocre? Nobody knows, because neither statistic has been
computed on a case where the answer is known — e.g. on states drawn from exact
NSE (where δ ≡ 0 by construction), or on a synthetic manifold with an imposed
known mask. Tier 2 **R-18** raises this for r_QSE specifically; it generalises.
Registered as **T-06**.

## IV.8b What a complete statistics package would look like

§IV.8 names two gaps. This section designs the fix, because "add error bars" is
not actionable and the design is where the difficulty is.

**1. Cluster bootstrap over trajectories** (Davison & Hinkley 1997 §3.8; Field &
Welsh 2007; Cameron & Miller 2015). Resample *trajectories* with
replacement (229 of them per network), recompute every headline statistic on each
resample, report the 2.5/97.5 percentiles. Two design points that are easy to get
wrong:

- **Resample whole trajectories, not rows.** The whole point is that rows within
  a trajectory are correlated; a row bootstrap reproduces the false 657k.
- **Stratify the resample by (T₉, phase)** if the statistic is reported per
  stratum, otherwise a resample can empty a cell. With ~30 trajectories per
  stratum, the intervals will be *wide*, and that is the honest answer rather
  than a problem with the method.

Expected outcome, predicted here so it can be checked: with n ≈ 300 nominal
rows per stratum × phase cell, the 95% interval on a fraction near 0.8 is
roughly ±0.045 if the rows were independent and **±0.12 – ±0.20** at design
effects 6.5–18.6 [derived here, from 1.96 √(p(1−p)·deff/n): 0.045, 0.115, 0.195;
an earlier version wrote "n_eff ≈ 300", which would double-count the design
effect — corrected in the 2026-08-18 audit]. So the §IV.6 coverage numbers — 0.62, 0.80, 0.95 — are
separated by less than their intervals. **The split verdict's *boundaries* are
statistically soft even though its extremes (0.002 vs 1.00) are not.**

**2. Threshold sensitivity: sweep θ.** The active set is {κ > θ} with θ = 0.1,
unsourced. Every gate that mentions the active set is a function of θ. Sweeping
θ ∈ {0.03, 0.1, 0.3} over the already-computed flux stores costs minutes and
answers a question the verdict cannot currently answer: *is the [4.0, 6.3)
coverage failure a fact about the physics or an artifact of where the line was
drawn?*

Two possible outcomes, both useful:

- coverage rises steeply as θ falls → the failing species' carriers sit just
  below 0.1, the failure is a threshold artifact, and Tier 2 **R-01**'s
  entropy-weighted active set (σ_j = 2k_B s_j κ_j artanh κ_j — the flux–force
  relation of Beard & Qian 2007 in κ form; parameter-free)
  should replace the threshold outright;
- coverage is flat in θ → the carriers are genuinely deep in the cancelled
  regime, the failure is real, and Φ-level supervision is the only fix.

Registered as **T-14**, and it is two hours on data already on disk.

**3. Null distributions.** Three statistics currently have no scale:

| statistic | measured | null needed |
|---|---|---|
| intra-group std(r_QSE) | 0.87 / 0.80 dex | its value on states drawn from **exact NSE** (where the answer should be ≈ 0) and on random compositions (the upper bound) |
| Spearman(log κ, log δ_r) | +0.491 / +0.498 | its value when κ and δ are computed from *independent* random states — the floor — and at exact NSE — the ceiling |
| maskable-set size | 0 | its value on a synthetic manifold with an **imposed known mask** — does the instrument find a mask that is there? |

The third is the important one and it is the standard missing control in this
whole class of work: **the mask-detection instrument has never been shown to
detect a mask.** Constructing the positive control is easy — take an NSE
composition, perturb a handful of species, and check that `guidry_masks` returns
everything except the perturbed reactions. Without it, "the maskable set is
empty" and "the detector does not work" are indistinguishable.

Registered as **T-06**, and it should block any external claim of the negative
verdicts.

## IV.9 What would have changed the answer

A useful exercise for reading any verdict: what result would have flipped it?

| finding | would have implied |
|---|---|
| cond(S_active) > 10⁶ on the relaxed manifold | **Target B**, immediately — ADR 0001's first switch condition |
| low-κ share > 90% of carrying columns | **Target B** — the net flow is everywhere-cancelled and per-reaction fluxes are unrecoverable |
| low-κ share > 30% (but < 90%) | FAIL on gate 3: diffuse spread, no identifiable carriers, no targeted mitigation possible |
| a non-empty maskable set with churn > 5%/step | freeze to the imposed Guidry mask (the `CLAUDE.md` rule) |
| \|dẎₑ\| coverage < 95% | would have indicated a *bug*, since it is structurally 1 — a useful tripwire |
| median-dominant coverage failing below 4 GK | Target A unviable in the QSE window, i.e. in the regime the project exists for |

None of those fired. What did fire — worst-species coverage in [4.0, 6.3) — is
the one outcome the threshold list did not anticipate, because `CLAUDE.md`'s gate
says "dominant isotopes" without specifying median or worst-case. Measuring both
and reporting the split, rather than picking the flattering one, is the single
best decision in the verdict document.

## IV.10 Self-check for S14

1. State the kill-test as a question about a matrix, and name which module
   supplies each measured quantity.
2. Why does `cond_s_active` use only the nonzero singular values? What would the
   gate report otherwise?
3. The training grid passes every gate. Explain in one sentence why that is
   uninformative, and give the physical reason κ ≈ 1 there.
4. Gate 1 passes at exactly 1.0000. Is that evidence about the emulator's future
   accuracy? Justify.
5. The Guidry sweep returns zero maskable columns at p90. Give the mechanism, and
   then give the reason this might be an artifact of the reference choice.
6. Derive the 1/κ amplification factor and apply it to a species with worst-case
   coverage 0.002.
7. "657k samples" — what is the effective sample size, why, and which of the
   tier's results survive the correction?
8. Name three findings that would have flipped the verdict to Target B.

---
# Part V (S15) — The ML target, decided

**A short node, because Tier 2 §I did the algebra.** What remains is what the
verdict changed.

## V.1 The two targets, restated

**Target A.** The network predicts a signed net per-reaction flux (internally, in
an asinh latent; the decoded quantity is linear), and the composition change is

$$
d\mathbf Y \;=\; \nu\,\boldsymbol\varphi ,
$$

with ν the fixed integer stoichiometric matrix. Because C ν = 0 by construction
(Tier 2 §I.7), **every conservation law holds exactly for any φ**, including the
output of an untrained network with random weights. Output dimension: 607 / 1518.

**Target B.** The network predicts dY directly in a **linear** output space, and
the result is projected onto the constraint manifold:

$$
P \;=\; I - C^{\mathsf T}(CC^{\mathsf T})^{-1}C
\qquad\text{(shipped as the QR form } I - QQ^{\mathsf T}\text{)},
\qquad d\mathbf Y_{\mathrm{cons}} = P\,d\mathbf Y_{\mathrm{raw}} .
$$

Output dimension: n + 3 = 83 / 154 (the extended vector includes e⁻, ν, ν̄).

**The theorem that reframes the choice** (Tier 2 §I.10): the two targets reach
**the same set**. image(ν̃) = null(C) exactly. So the decision is **not about
expressivity** — it never was — and any document framing it that way is wrong
(Tier 2 **R-22** is a referee pass to check that none does).

What the decision *is* about, in three words: **parameterisation, conditioning,
supervision.**

| | Target A | Target B |
|---|---|---|
| conservation | exact, structural | exact, by projection |
| output dim | 607 / 1518 | 83 / 154 |
| error attribution | per named reaction | per species |
| equilibrium structure | expressible (mask columns) | not expressible |
| conditioning | inherits 1/κ on cancelled columns | cancellation hidden inside dY labels |
| supervision available | Φ labels must be **generated** (§V.4) | ΔY labels ship with the dataset |
| identifiability | **528 / 1368 unidentifiable directions** under a ΔY-only loss (Tier 2 **R-03**) | fully identified |

## V.2 What the verdict decided, and what it left open

**Decided: Target A, full-width.** No switch condition fires (§IV.9). The
per-reaction structure is worth keeping precisely because the physics is
concentrated in few columns — top-20 bridges carry 0.88 of inter-group flux
(mesa_80), top-20 weak channels carry 1.00 of the Yₑ budget — and that
concentration is
expressible in flux space and invisible in dY space.

**Decided: the equilibrium mask is gone.** The specified Component B was a
*hybrid*: a Guidry physics prior, refined by a learned L₀ / hard-concrete gate
(Louizos, Welling & Kingma 2018).
The prior is measured empty (§IV.5). What remains is one of:

- **(a) no mask** — a full-width flux head, which is the verdict document's
  reading;
- **(b) a purely learned gate** with no physics initialisation — now an
  unmotivated sparsity regulariser rather than a physics-informed structure;
- **(c) a mask against the manifold's own attractor** rather than true NSE —
  untested, cheap, and possibly non-empty (**T-04**).

The verdict picks (a) and is right to for now, but (c) has not been ruled out and
should be before Component B is written.

**Left open: the [4.0, 6.3) worst-species coverage failure** (§IV.6), which is a
*supervision* problem rather than a target problem, and whose mitigation depends
on §V.4.

## V.3 Why conservation must live in the decode step — the NuGNN failure mode

`CLAUDE.md` invariant #4 says conservation lives in the decode step, never inside
latent dynamics, and that Target B's projection is valid **only in a linear
output space**. The reason is one line of algebra and one documented failure.

A sum constraint evaluated in a warped space conserves nothing in the physical
space. If the network's output is s = signed-log(dY) and you project s onto
{Cs = 0}, then

$$
\sum_i c_i\,s_i = 0 \quad\not\Longrightarrow\quad \sum_i c_i\,dY_i = 0 ,
$$

because the map s ↦ dY is nonlinear. The projected vector satisfies a constraint
on a transformed quantity that has no physical meaning. This is the
linear-constraint case in which architecture-level ("hard") enforcement is exact
to machine precision (Beucler et al. 2021); the linearity is the load-bearing
hypothesis.

NuGNN (Kim et al. 2026, arXiv:2606.04491, §Training Method and §Conclusions)
documents the empirical half: with signed-log outputs, explicit enforcement of
ΣΔX = 0 — as a loss term or an output transform, either requiring inversion of
the signed-log representation back to ΔX — made optimisation unstable and
degraded training, so the model shipped without an enforcing term; the paper
reports that conservation was nonetheless learned "sufficiently well" from data,
backed by a rollout retry (smaller Δt) when ΣΔX "deviated significantly from
zero". The algebraic half — a linear constraint imposed in warped coordinates is
not the physical constraint — is derived here, and is not what NuGNN did (its
enforcement attempts evaluated the sum in linear ΔX space). An earlier version of
this paragraph said NuGNN "documents exactly this instability"; that overstated
the paper (corrected in the 2026-08-18 audit). The repo encodes the lesson as a
refusal in `graph/projector.py`'s docstring and as invariant #4.

**Two corollaries that are easy to miss.**

1. **Target A's asinh latent is safe** precisely because the *decoded* quantity is
   φ, which is linear, and the conservation map ν acts on φ. The nonlinearity is
   upstream of the conservation map, never between it and the output.
2. **The projector acts on the extended vector** [dY_nuclei, dY_e⁻, dY_ν, dY_ν̄],
   not on the nuclei alone. Projecting a nuclei-only vector against a nuclei-only
   C would force Σ Zᵢ dYᵢ = 0 — i.e. **erase the weak dYₑ signal entirely**
   (invariant #3). Tier 2 §I.9 calls this the laundering trap; the measured
   confirmation is that weak dYₑ changes by ≤ 3.4 × 10⁻²¹ through projection
   **[RESULTS]** 2026-07-08.

## V.4 Φ supervision: proven where it matters, blocked where it does not

Target A predicts Φ. The shipped dataset contains ΔY. **Φ labels do not exist and
must be generated**, which is what `fluxes/integrate.py` (ADR 0006) is for: an
augmented state u = [Y, Φ] with dΦⱼ/dt = Rⱼ, integrated by BDF (Hairer & Wanner
1996) with a sparse
analytic Jacobian, returning Y := Y₀ + ν(Φ − Φ₀) so that ΔY = νΦ and
conservation hold **by construction**.

Measured **[RESULTS]** 2026-07-12:

| | value |
|---|---|
| internal identity residual | 2.1 × 10⁻¹⁶ molar (machine precision) |
| RHS ≡ engine | ≤ 10⁻¹² rel |
| BDF ≡ Radau ≡ BDF(rtol 10⁻¹⁰) | 5 × 10⁻⁸ rel on the stiffest test state |
| **energy identity (invariant #5)** | median 6 × 10⁻⁶ … 2.5 × 10⁻⁵ rel, max 8.7 × 10⁻⁴, **fraction ≤ 1% = 1.000 in every stratum**, both nets |
| ΔX vs shipped labels, QSE window [3.3, 5.0) | median species-fraction in band **0.74 – 0.99** |
| ΔX vs labels, cold strata | 0.62 – 0.90 |
| T₉ ≥ 5 | **unmeasurable within deadline AND label-pathological** |

**Feasibility, which is the binding constraint:** median wall ≥ 383 s (mesa_80) /
1519 s (mesa_151) per state, with 17/36 and 10/24 states **censored** at the
4800-s deadline — and every censored state is T₉ ≥ 5. That is ≤ 9.4 / 2.4 states
per hour per core, so the full corpus would cost **≥ 110,647 / 439,302
core-hours**. Full-corpus Φ supervision is **infeasible**. Stratified subsets of
10³–10⁴ states in the T₉ < 5 band, QSE window first, cost ≈ 4–40 core-days and
are feasible.

**The cost cause is diagnosed, which turns a wall into a task.** The deliberately
neglected tabular-EC ρYₑ Jacobian chain dominates the weak-drift phase at
T₉ ≥ 5: the solver is taking tiny steps because it has no derivative information
for the term that is actually driving the evolution. ADR 0006's contingency —
add the Yₑ-chain term to the Jacobian — is the identified unlock.

So the picture for Phase 1 is coherent:

| band | Φ labels | label physics | kill-test gates | verdict |
|---|---|---|---|---|
| **T₉ < 5** | generatable — 4–40 core-days for 10³–10⁴ states | sound | all pass at median coverage | **this is where Target A is trained and validated** |
| **T₉ ≥ 5** | blocked on integrator cost (unlock identified) | bug-displaced (Part III) | median coverage fails in [5.0, 6.3) | deferred; declare a validity domain (**T-03**) |

## V.5 The identifiability cost nobody has paid attention to

Tier 2 §IV.4b derives it and it belongs in the target decision.

Under a **ΔY-only** loss, the flux head is unidentifiable in **528 / 1368
directions** — the dimension of null(ν) restricted to the relevant column space.
Any φ and φ + n with n ∈ null(ν) produce identical ΔY, identical conservation,
identical energy (if Q ⊥ null(ν), which Tier 2 §IV.8b measured to be *false* at
the 0.55 keV rms level, but nearly true). The loss cannot distinguish them.

Three consequences:

1. **The learned fluxes are not the physical fluxes**, even for a perfectly
   accurate model, unless Φ-level supervision pins the null directions. The
   "physical interpretability of errors" advantage of Target A (Tier 2 §0.1.3)
   is *conditional on Φ supervision*.
2. **Gradient descent will wander in the null space**, which is a training
   pathology (no gradient signal, but also no penalty) rather than an accuracy
   one.
3. **It is a second, independent cost of Target A**, alongside the 1/κ
   conditioning of §IV.6 — and it is one Target B does not have.

None of that overturns the verdict; Target B's costs (loss of per-reaction
structure, loss of the equilibrium expressibility, the same label-level
cancellation) are judged larger. But the honest statement of the decision is
"Target A, with two known costs and a mitigation plan for one of them", not
"Target A wins".

## V.5b The output space is a simplex, and nothing in the project treats it as one

A prerequisite that no tier covers: **the geometry of the space the answer lives
in.**

A composition is a point on the (n−1)-simplex

$$
\Delta^{n-1} \;=\; \Big\{\,X \in \mathbb R^{n} \;:\; X_i \ge 0,\ \textstyle\sum_i X_i = 1 \,\Big\},
$$

and increments live in its tangent space, which is where Tier 2 §I.7b's
positivity discussion starts. The project handles the **equality** constraint
beautifully — it is the whole conservation story — and handles the **inequality**
constraint nowhere. Three things follow that are not in any register.

**(i) There is a mature literature for exactly this and it is uncited.**
Compositional data analysis (Aitchison 1982, 1986; ilr: Egozcue et al. 2003)
treats data on a simplex through log-ratio transforms — additive (alr), centred
(clr) and isometric (ilr) — under which the
simplex becomes a real vector space with its own inner product, and standard
statistics apply. The relevant facts:

- **clr and ilr are linear-in-log-ratio**, which is *not* the same as "log space",
  and the distinction is exactly the one invariant #4 is about. A clr coordinate
  is Σ-free by construction: the closure constraint is absorbed into the
  coordinate system rather than imposed on top of it.
- The NNN's log-softmax output (§VI.1; Grichener et al. 2025 §2.3–2.4) is precisely the **inverse clr/alr map**
  applied without anyone saying so — softmax is the standard simplex
  parameterisation. So the baseline is already doing compositional data analysis
  by accident, and the vocabulary would have told it that the corresponding
  *loss* should be a log-ratio distance rather than an L1 on logs.
- The Aitchison geometry's pathology is also known: **zeros are not
  representable** (log 0 = −∞), and compositional data analysis has a whole
  sub-literature on zero replacement (e.g. Martín-Fernández, Barceló-Vidal &
  Pawlowsky-Glahn 2003). This project's data has a hard floor at
  10⁻¹⁵ (§II.1b) — i.e. it has *already made* a zero-replacement choice,
  upstream, without calling it that.

**(ii) Target A sidesteps the simplex and pays for it elsewhere.** dY = νφ
guarantees ΣA dY = 0 exactly, so the *hyperplane* is respected; the *facets* are
not. Nothing prevents an individual Yᵢ from going negative, and Tier 2 §I.7b
argues it is not a small problem here because trace species span fifteen decades.
The available options, none of which is in the plan:

| option | cost |
|---|---|
| diagnose only (count violations, magnitude) | free; **should exist already** (**R-04**) |
| clip and renormalise | breaks conservation — the exact thing the design forbids |
| project onto the simplex (Euclidean or Aitchison) | conservation-preserving if done in the tangent space; changes the loss landscape |
| parameterise so positivity is structural (predict in a log-ratio coordinate and decode) | **puts a nonlinearity between the conservation map and the output — forbidden by invariant #4** |

The last row is the interesting one: **positivity and exact linear conservation
pull in opposite directions.** Structural positivity wants an exponential map;
structural conservation wants linearity. You can have either structurally, or one
structurally and the other by projection, but the obvious way to get both at once
is exactly the NuGNN failure mode. That tension is real, is not written down
anywhere in the project, and is the correct framing of **R-04**.

**(iii) The metric on the correction is a choice nobody recorded.** Tier 2
**R-17** notes that the Target B projector is orthogonal in the *unweighted
Euclidean* metric — the minimum-Σ(δY)² correction. On a simplex, the natural
metrics are Aitchison's or an abundance-weighted one, and the difference matters
precisely for trace species: an unweighted projector distributes the correction
uniformly, so it makes a relatively enormous change to a 10⁻¹² species and a
negligible one to a 0.5 species. Registered as **T-30**, extending **R-17** with
the reason the choice is not innocuous.

## V.5c Gradients through the conservation map — two different questions

`tier1.md` §VIII.E.5 flags "gradients through ν and P" as a gap. It is worth
separating two things that the single flag conflates, because one is a training
question and one is the deployment requirement of §0.8.6.2.

**Question 1 — training.** Backpropagating through dY = νφ is a constant linear
map, so the gradient is νᵀ, which is exact, cheap and well conditioned
(cond(ν) = 41.6 / 57.9). The real subtlety is ν's **nullity**: the gauge freedom
of Tier 2 §I.2.1 means gradient descent receives no signal in null(ν), which is
the identifiability statement of §V.5 seen from the optimiser's side. Nothing
diverges; the parameters simply drift in those directions, which is a slow
pathology and an unexamined one.

**Question 2 — deployment.** The host needs ∂e_nuc/∂lnT and ∂e_nuc/∂lnρ
(§0.8.6.2, **T-25**). Through the flux route,

$$
e_{\mathrm{nuc}} = \sum_j Q_j \Phi_j
\qquad\Longrightarrow\qquad
\frac{\partial e_{\mathrm{nuc}}}{\partial \ln T}
= \sum_j Q_j\,\frac{\partial \Phi_j}{\partial \ln T}
\;+\;\sum_j \Phi_j\,\frac{\partial Q_j}{\partial \ln T},
$$

and the second term is **exactly the Q(T) correction that `tier1.md` §VIII.E.2
says is specified, unimplemented, and invisible to the current energy gate** —
where it reaches −19.2% on ⁴⁰Ca(α,γ)⁴⁴Ti at T₉ = 7.9 [derived there, tier1
§VIII.E.2 table]. So an open Tier-1 item and
an unrecognised deployment requirement are the same term. Closing §VIII.E.2 is
therefore worth more than it looked: it is not only an energy-accuracy item, it
is a *prerequisite for supplying the host with a correct derivative*.

That connection is new here and it is the kind of thing a cross-tier audit is
for. Folded into **T-25**.

## V.6 Self-check for S15

1. State the reachability theorem and say what it removes from the A-vs-B
   argument.
2. Give three axes on which A and B genuinely differ, with the measured number
   supporting each.
3. Why is Target A's asinh latent safe when NuGNN's signed-log conservation was
   not?
4. What does projecting a *nuclei-only* dY vector against a nuclei-only C do to
   Yₑ, and which invariant forbids it?
5. Φ labels cost ≥ 110k core-hours for the full corpus. What is the diagnosed
   cause, what is the unlock, and what is the feasible fallback?
6. How many directions is the flux head unidentifiable in, under what loss, and
   what fixes it?

---

# Part VI (S16) — The baseline you are trying to beat

**Know your competitor better than they do.** This node is the NNN as an object,
what it achieves, where it does not, and what "beating it" has to mean.

## VI.1 What the NNN actually is

Grichener, Renzo, Kerzendorf et al. 2025, *Nuclear Neural Networks: Emulating
Late Burning Stages in Core-collapse Supernova Progenitors* (ApJS 279, 49;
arXiv:2503.00115; data and models at Zenodo 10.5281/zenodo.14873443). Read from
the shipped code (`repro/nnn/patched/NNNfunctionsCompPlusEps.py`) and checked
against the paper (§2.3):

**Architecture.** A plain feed-forward MLP:

```
  input  (n_iso + 2)  ──▶ Linear 1024 ──ReLU──▶ Linear 2048 ──ReLU──▶ … ──▶
                          Linear 2048 ──ReLU──▶ Linear (n_iso + 2)
```

Twelve (mesa_80) or nine (mesa_151) Linear layers: input → 1024 → 2048 (×10 or
×7) → out (Grichener et al. 2025 §2.3, Fig. 2; `docs/zenodo-inventory.md`). The
class constructor's defaults — four layers of 128/256/256 with
`neuronsNumFactor = 1, layersNum = 4` — are *not* the shipped configuration,
which is loaded with factor 8 and 12/9 layers (`runNNNsOnTestMesa80.py:491`); an
earlier version of this section quoted the defaults (corrected in the 2026-08-18
audit). Input = the initial mass fractions plus log T and log ρ (dims 82 / 153,
confirmed against the checkpoints **[RESULTS]** 2026-07-08). Output = the final
mass fractions plus e_nuc and ε_ν (the energies normalised by 10¹⁶).

**The output transform is the interesting part.** The isotope block passes
through a **log-softmax**:

```python
first_80_log_softmax = torch.log_softmax(x[:, :isotopesNum], dim=1)
x = torch.cat([first_80_log_softmax, x[:, isotopesNum:]], dim=1)
```

So the predicted mass fractions satisfy Σ exp(outᵢ) = 1 **exactly, by
construction** (in float32; Grichener et al. 2025 §2.3: "to ensure the abundances
sum to one"). The NNN *does* conserve mass — through a normalisation, not
through stoichiometry.

**The loss** is L1 in log space on the isotopes plus L1 in linear space on the
two energy outputs (Grichener et al. 2025 §2.4):

```python
isotopes_loss = F.l1_loss(nnComp_isotopes, torch.log(bbqComp_isotopes))
eps_loss      = F.l1_loss(nn_eps, bbq_eps)
total_loss    = isotopes_loss + eps_loss
```

**Nine models per network.** One MLP per timestep — the dt grid is not a model
input, it is a model *index* (Grichener et al. 2025 §2.2: "a separate neural
network for every timestep"; the paper's burner interpolates between the two
nearest trained dt, §4). Eighteen production models ship (7.3 GB; the 23.8 GB
`trained_NNN_models/` tree also holds a 36-model layer scan, each checkpoint
carrying Adam optimizer state).

**Training data.** The 2²⁰ Sobol grid, 1,041,400 usable states per network per dt
(§I.5), cast to float32 by the loader.

## VI.2 Reading that design critically

Four observations, each of which is a design axis this project takes
differently.

**(i) Mass is conserved; charge is not.** The softmax fixes ΣXᵢ = 1 exactly and
says nothing about Σ ZᵢYᵢ. **Yₑ is entirely unconstrained**, which is why the
paper reports a Yₑ *loss* as a separate metric rather than an invariant
(Grichener et al. 2025 §3, their δYₑ = Σᵢ(Zᵢ/Aᵢ)|ΔXᵢ| — an upper bound on the
signed error), and why the reproduced relative Yₑ error is 0.33–0.54% (mesa_80) /
0.55–0.73% (mesa_151) **[RESULTS]** 2026-07-08 (the paper quotes 0.4–0.75%).

Put that number in the project's own units. Yₑ ≈ 0.47, so 0.5% relative is
**|ΔYₑ| ≈ 2.4 × 10⁻³ per step** (the measured band gives 1.6–3.4 × 10⁻³). The
project's per-step gate is 3 × 10⁻⁶. **The baseline is ~800× (520–1140×) outside
the gate this project sets itself.** That is a
startling gap, and it is the single most important number for calibrating
ambition. Two honest readings coexist:

- the gate may be over-specified (§0.6.5 / **T-01** — the derivative that would
  tell you is missing);
- or the NNN's Yₑ accuracy is genuinely inadequate for the science, which is
  exactly the claim this project is built on.

Either way, **this comparison should be in the project's own documents and is
not.** Registered as **T-07**.

**(ii) Normalisation is not conservation.** Softmax rescales; it does not respect
stoichiometry. Tier 2 §0.5 makes the general argument: a leak is
species-specific, a renormalisation is uniform, so renormalising after a leak
silently redistributes abundance between species. The NNN never "leaks" mass
because it never computes a change — it predicts the final state directly — but
the same criticism applies in the form: *there is no mechanism forcing the
predicted state to be reachable from the initial one.* Charge, lepton number, and
the reachable-manifold structure (Tier 2 §0.4.3) are all unconstrained.

**(iii) The loss is in log space, which is the right choice for dynamic range and
the wrong space for constraints.** Mass fractions span 1e-15 to 1; an L1 loss in
linear space would be dominated entirely by the top few species. Log space fixes
that and is a genuinely good decision. But it means the loss weights a relative
error on a 10⁻¹⁴ species the same as on a 0.5 species — consistent with the
paper's per-isotope error band of 10⁻⁴ … 10⁻¹ with light isotopes *best*
(Grichener et al. 2025 §3 attribute the ordering to abundance: absolute errors
grow with X) — and it means
no linear constraint can be imposed in the space where the loss lives. This is
the same structural point as invariant #4, arriving from the loss side.

**(iv) Nine models is a strong statement about the hard part.** Training one
model per dt admits that the Δt dependence is the difficult axis. Tier 4's S19
takes the opposite bet — one model over eight decades, with Δt as conditioning —
and Tier 2 **R-10** argues the conditioning variable should be Δt/τ rather than
log Δt precisely because §III.1 measured that *every* label is a full relaxation.
Nine models is the safe design; one conditioned model is the better one if it
works, and it is 9× cheaper to store and deploy.

## VI.3 What the NNN achieves

Reproduced exactly by this project (`repro/nnn/`), which is worth its own
paragraph. **[RESULTS]** 2026-07-08:

| claim | reproduced | published |
|---|---|---|
| all 18 (net, dt) × 6 metrics vs shipped result CSVs | **ratio 1.000 in all 108 comparisons** | — |
| independent state_dict-walk loader vs upstream class, 128 samples | **max deviation 0.0** (gate ≤ 10⁻⁶) | — |
| Yₑ improvement over approx21, mesa_80 | 377–651% | 390–660% |
| Yₑ improvement, mesa_151 | 277–390% | 280–400% |
| Ā improvement | 149–291% / 256–357% | 150–290% / 260–360% |
| e_nuc improvement | 249–419% / 284–772% | 250–450% / 280–750% |
| ν-loss crossover | better than approx21 for dt ≤ 0.1 s; **worse** for dt ∈ {1, 10, 100} s | comparable at 0.1 s, worse after |
| per-isotope mean ΔX band (mesa_80, dt = 10⁻³ s) | 90% of isotopes in [10⁻⁴, 10⁻¹], median 3.2 × 10⁻³ | most in that band (their Fig. 3) |

Two things stand out.

**The reproduction is exact, not approximate.** The Step-2 pass criterion was
"within ~2×"; the result was 1.000 in all 108 comparisons and a bit-identical
model handshake. That establishes the baseline as a *fixed, checkable reference*
rather than a quoted number — this project can rerun it against any future
change.

**The ν-loss crossover is the baseline's honest weakness**, reported by the
authors and reproduced here: at long timesteps the NNN is *worse* than approx21
on neutrino losses. Any claim of improvement must be made per-dt, because the
sign of the comparison changes across the grid.

## VI.4 NuGNN, the closer competitor

Kim, Chae, Ko, Mumpower & Smith 2026, *NuGNN: a Graph Neural Network for
Nuclear Reaction Network Equations* (arXiv:2606.04491, preprint) is the nearer
prior art: a graph neural network surrogate for a 690-isotope X-ray-burst
network, hence the same architectural family as this project.

Its documented difficulty is the one that shaped this project's invariant #4:
attempted enforcement of ΣΔX = 0 (as a loss term or an output activation), which
requires inverting the signed-log label transform, **made training unstable and
was dropped**; ΣΔX ≈ 0 is learned from data (the paper: "sufficiently well"),
backed by a rollout retry with smaller Δt when the predicted sum deviates
significantly (Kim et al. 2026, §Training Method and §Conclusions; §V.3). That
is a useful competitor to have — it establishes that the GNN framing is live and
publishable, and it leaves the *exact-conservation* claim open.

The novelty position this leaves, stated narrowly (and re-checkable at every
phase boundary by the `novelty-checker` sweep, which `CLAUDE.md` makes mandatory):

| axis | NNN | NuGNN | this project |
|---|---|---|---|
| architecture | MLP | GNN, heterogeneous isotope/reaction bipartite, learned (N,Z) embeddings | GNN, heterogeneous, raw (Z,N) node features — *not* a differentiator by itself |
| conservation | ΣX = 1 by softmax | enforcement through the inverse signed-log made training unstable; shipped unenforced (learned + retry) | **exact by construction, all three laws** |
| target | final X | ΔX (as signed offset-log of ΔX/X) | **per-reaction flux Φ** |
| Δt handling | 9 models | one model, Δt as input (10⁻¹⁵–10⁻⁴ s) | one model, conditioned — *not* a differentiator vs NuGNN |
| reported error | Yₑ 0.4–0.75% | MAE 0.037 (offset-log metric); XRB rollout deviations mostly < 15% | — |
| size transfer | retrain | not addressed | (Z,N) embedding — a stated falsifier |

(The NuGNN column was corrected in the 2026-08-18 audit: the earlier table left
its Δt handling and node features blank, which overstated this project's
differentiators — the surviving ones are exact three-law conservation, the
flux-space target, and the size-transfer question.)

## VI.5 What "beating it" has to mean

This is the part that needs deciding before Phase 1 rather than after, and it is
not decided anywhere in the repo. The trap: an emulator can be better on the
metric the baseline optimises and worse on the thing that matters, or vice versa.

A defensible comparison protocol needs at least these five components, and none
of them is currently specified.

**1. The same test set, and the pathology declared.** The shipped test sets are
labelled by the same bbq that produced the training labels, so they carry the
same pathology above 5 GK (§III). A comparison in that band measures agreement
with a bug. Either restrict to T₉ < 5 or report the band separately with the
caveat attached.

**2. Per-dt reporting.** The ν-loss crossover (§VI.3) proves that an aggregate
over the dt grid can hide a sign change. Every metric, every dt.

**3. Yₑ in absolute units, not relative improvement.** "377–651% improvement over
approx21" is a ratio of losses whose definition is upstream's. The project's own
quantity is |ΔYₑ| per step, absolute, against the 3 × 10⁻⁶ gate and the
2.4 × 10⁻³ baseline (§VI.2). Both should be reported; only the second is
comparable across papers.

**4. Rollout, not just one-step.** The NNN's quantitative results are one-step;
the paper reports a 1000-step constant-(T, ρ) rollout only qualitatively (Yₑ error
stays below approx21's, the other metrics become comparable or worse) and argues
that recursion is not the intended use (Grichener et al. 2025 §4). The
scientific use is a *sequence* of steps (N ≈ 1.6 × 10³), where the accumulation
character — systematic vs random-walk vs contractive — dominates the outcome
(Tier 0 §IV.3). A one-step comparison cannot distinguish a model that drifts from
one that does not. **This is where exact conservation should show its value**, and
it is measurable only in rollout. That the accumulation slope is still unmeasured
(**R-21**) makes this the highest-leverage missing experiment in the project.

**5. Trivial baselines, which nobody has run.** Tier 2 **R-16**: *persistence*
(X' = X), *nearest neighbour* in the training set, and above all **NSE as a
predictor**. If NSE predicts the labels well at T₉ > 5 (it does not on this data,
because the labels are displaced — but it might on physically-correct labels),
then the emulator's real domain is T₉ < 5 and its competitor there is a Saha
solve, not a neural network. Running three cheap baselines could redefine the
problem. Registered as **T-08**.

Add one more that follows from §IV.8: **6. Cluster-robust error bars over
trajectories**, so that "better" is a claim with an interval rather than a
comparison of two medians.

## VI.5b The protocol, written out

§VI.5 names six components. Since the point of naming them is to fix them before
Phase 1, here is the concrete version — a specification that could be adopted as
an ADR today, with the open decisions marked.

**Test sets.**

| set | source | purpose |
|---|---|---|
| **held-out Sobol states** | `state_id` split from the training corpus | in-distribution, matches the NNN's own protocol exactly |
| **relaxed manifold** | the §I.6 campaign, trajectories held out from any training use | the deployment distribution (§IV.3) — the NNN was never evaluated here, and this is where a conservation-exact model should win |
| **a real MESA track** | a 20 M⊙ (and ideally ≥3 progenitors, **T-22**) evolution's actual zone states | the `CLAUDE.md` Sobol → real gate |
| **NSE-reachable hot states** | T₉ ≥ 5 | reported **separately and with the pathology caveat** (§III), or excluded per **T-03** |

**Metrics, all reported per (network, Δt, T₉ stratum):**

| metric | why |
|---|---|
| \|ΔYₑ\| **absolute**, median and p99 | the project's quantity; comparable across papers unlike a loss ratio |
| per-isotope ΔX distribution | comparable to the paper's Fig. 3 band |
| e_nuc relative error | feeds the energy equation |
| ε_ν relative error | **the NNN's known weak spot** (the crossover, §VI.3) |
| ΣX − 1 and min X | conservation and positivity; the NNN's softmax gives it the first for free, so this is a *tie* not a win — the win is charge |
| Σ Z dY + dN_lep | **the charge-to-lepton ledger the baseline has no analogue for** |

**Rollout, which is the discriminating experiment.** N ≈ 10³ autoregressive
steps on the relaxed manifold, reporting the *accumulation slope* of |ΔYₑ| vs N
on a log-log plot. Three outcomes, and the project's whole conservation argument
predicts the first:

- slope ≈ ½ → random-walk accumulation; the operative gate can relax toward
  5 × 10⁻⁵ (**R-21**);
- slope ≈ 1 → systematic; the 3 × 10⁻⁶ gate stands;
- slope ≈ 0 → contractive; the attractor is doing the work, and the model's
  per-step accuracy matters less than anyone thought.

**Baselines**, all of them (**T-08**): the NNN, `approx21` (strictly the
22-isotope `approx21_cr60_plus_co56` the NNN paper compares against, §2.3),
persistence, nearest-neighbour, and **NSE** — the last on the hot strata, where
§0.3.6 says it is the real incumbent for NSE-switching hosts.

**Uncertainty.** Cluster bootstrap over trajectories (§IV.8b), reported as
intervals, on every number.

**Open decisions this specification does not make**, and which a person should:

1. whether T₉ ≥ 5 is in scope at all (**T-03**);
2. whether the headline comparison is against the NNN's *published* numbers or a
   *retrained* NNN on identical splits — the second is fairer and costs a
   training run;
3. what counts as "beating": strictly better on every metric, or better on Yₑ and
   conservation with parity elsewhere. The second is the honest target and should
   be declared **before** the numbers exist.

Registered as **T-18**.

## VI.6 Self-check for S16

1. Describe the NNN's architecture and identify the single line that makes it
   conserve mass.
2. Which conservation law does the NNN *not* have, and what is the measured
   consequence in absolute units?
3. The NNN's loss is L1 in log space. Give one strong reason for that choice and
   one structural cost.
4. Why is the ν-loss crossover the most important row in the reproduction table
   for anyone claiming an improvement?
5. Name the five components a defensible "we beat the baseline" claim requires,
   and say which one exact conservation is expected to win on.
6. What would running NSE-as-a-predictor as a baseline potentially do to the
   project's scope?

---
# Part VII — What Tier 3 hands forward

## VII.1 What Phase 0 established

Positively, and in order of how load-bearing each is:

1. **Conservation by construction works and costs nothing.** dY = νΦ through a
   fixed integer matrix gives exactly-zero column drifts and random-flux drift
   within max(10⁻¹²s, 10⁻¹³G) over random fluxes spanning twelve decades within
   each draw, at overall φ scales 10⁰…10⁻²⁰, with dYₑ
   surviving through the weak columns. The gate blocks training and has never
   failed since the export was fixed. **[RESULTS]** 2026-07-08/09.
2. **The rate pipeline is trustworthy to 0.004 dex** against an independent
   Fortran code, with every one of 135 severe outliers class-explained or
   open-flagged. **[RESULTS]** 2026-07-10.
3. **The reference integrator produces valid Φ labels** with machine-precision
   internal identities and an energy residual three orders inside the 1% gate —
   for T₉ < 5, at 4–40 core-days for a useful subset. **[RESULTS]** 2026-07-12.
4. **The bridge structure is real and concentrated.** Top-20 inter-group columns
   carry 0.88 of the flux (mesa_80); the literature bottleneck ⁴⁵Sc(p,γ)⁴⁶Ti
   (Woosley, Arnett & Clayton 1973; Hix & Thielemann 1996) is recovered
   independently at rank 2/251 (mesa_151). **[RESULTS]** 2026-07-12. That the
   quasi-equilibrium picture of Bodansky, Clayton & Fowler 1968 survives on
   relaxed states is the author's gloss on those rows, not a RESULTS statement.
5. **Target A is viable and is the decision**, unconditionally below 4 GK.

## VII.2 What Phase 0 retired

Four assumptions died, and a project that had gone straight to training would
have discovered them as unexplained training failures, or not at all:

| retired | replaced by | where |
|---|---|---|
| "the training labels are clean" (Step 4 premise) | labels are Appendix-B displaced at T₉ ≳ 5, with a wrong Yₑ evolution | §III |
| "the single-Si-cluster QSE plateau describes this regime" | not confirmed on clean rerun data: 0/303 and 0/316 rows below the plateau criterion | §I.8 |
| "6–8 orders of timescale separation" (unsourced working figure) | per-stratum medians −12.2 … +1.4; **no separated fast sector** | §IV.7 |
| "there is a maskable equilibrium set to exploit" | median and p90 = 0 columns at every ε | §IV.5 |

The fourth invalidates the specified Component B hybrid; the third invalidates
the specified Component C rollout governor's premise. **Two of the four
architecture components have had a stated premise retired by measurement, and
neither has been redesigned.** That is the state Tier 4 inherits, and it is the
most important sentence in this section.

## VII.3 The four escalations

Decisions that were correctly *not* made inside a results log:

1. **Benchmark versus physics at T₉ ≳ 5** (§III.6). Train on labels that
   reproduce a bug, or on corrected physics that breaks comparability? Third
   option: declare a validity domain (**T-03**).
2. **External communication about the NNN's labels** (§III.6). The published
   baseline was trained on the same labels. A person, not a script, decides how
   that is said.
3. **Backporting the gh-575 fix** into r23.05.1 — a drafted, dry-run-clean patch
   that is deliberately not applied, because applying it would change what "the
   label configuration" means.
4. **Whether to accept the [4.0, 5.0) conditional verdict** or narrow the claimed
   domain further (§IV.8, §V.4).

## VII.4 The state Tier 4 inherits

| **decided** | **open / retired** |
|---|---|
| Target A, full-width | Component B's mask: the prior is **empty** |
| conservation in the decode step | Component C's governor: premise **false** |
| (Z, N) node features | Δt conditioning variable (Δt/τ? **R-10**) |
| K = 5 message-passing rounds | rollout accumulation slope **unmeasured** (**R-21**) |
| loss weighting → top-20 weak + top-20 bridge columns | Φ supervision: T₉ < 5 only |
| unscreened κ for equilibrium detection | validity domain: undeclared (**T-03**) |
| float64 at the conservation map | evaluation protocol vs the NNN: unspecified (**T-18**) |
| | OOD / fallback target rate: underivable without S_target (**R-12**) |

and, from the boundary audit (Part IX) — requirements the plan does not know it
has:

| requirement | status |
|---|---|
| the runtime fraction p | **unmeasured**, and Amdahl caps everything at min(1/(1−p), 1/f) (**T-24**) |
| ∂e_nuc/∂lnT, ∂e_nuc/∂lnρ | an output nobody specified; **MESA's fully-coupled route cannot run without it** (its `op_split_burn` route zeroes it) (**T-25**) |
| the timestep controller's lost convergence signal | respecifies S22 as a *calibrated error estimate* rather than a flag (**T-26**) |
| per-call latency at the real batch size | uncosted (**T-27**) |
| positivity vs linear conservation | structurally in tension (**T-30**) |

**Read the right-hand column as one thing.** Four of its entries are decided
elsewhere in the project's plan and merely unfinished; the five boundary items
are different — they are requirements the plan does not know it has. An emulator
can satisfy every left-hand entry perfectly and still be uninstallable.

Four of the eight open Phase-0 checklist rows are Tier-4 measurements, including
the accumulation slope — the single number that moves the project's operative
gate by two orders of magnitude.

## VII.5 The three ideas to carry, if you carry nothing else

**One.** *Silicon burning is a rearrangement, and everything algebraic in this
project is a consequence.* ²⁸Si does not fuse appreciably with ²⁸Si at any
temperature the star survives, so the flow proceeds by disassembly and reassembly through a
light-particle reservoir. Fast near-balanced pairs plus slow bridges *is* κ, *is*
stiffness, *is* QSE, *is* catastrophic cancellation — four names for one
mechanism.

**Two.** *Yₑ is the whole point, and the strong sector cannot change it.* The
left null space of the strong/EM columns is exactly span{A, Z}, so every bit of
Yₑ evolution runs through 46/607 or 173/1518 weak columns, of which twenty carry
essentially all of it. That is why the weak sector is never maskable, why
conservation must be structural rather than penalised, and why the gates are
absolute rather than relative.

**Three.** *The training distribution and the deployment distribution are
different worlds, and it is measured.* κ ≈ 1 everywhere on the Sobol grid; a
κ-continuum from 10⁻³ to 10⁻¹ on the relaxed manifold. Relaxation *onto* the slow
manifold and motion *along* it are different functions, not a covariate shift. No
architecture fixes that; only data from the right distribution does.

---

# Part VIII — The open register

**This is the single register for Tier 3.** One row per open item; the content
lives in the section that owns it. Cross-tier items stay in
[`tier1.md` §VIII](tier1.md#part-viii--open-prerequisites-what-is-still-not-covered)
and [`tier2.md` §VI](tier2.md#part-vi--the-open-register); where a row here
extends one of those, it says so.

## VIII.1 The register

| ID | open item | derived in | cost | what closing it changes |
|---|---|---|---|---|
| **T-01** | **∂M(⁵⁶Ni)/∂Yₑ, ∂ξ_2.5/∂Yₑ, ∂(explodability)/∂Yₑ have never been assembled.** The per-step gate is an *input* uncertainty used as an *output* tolerance | [§0.6.5](#065--the-derivative-nobody-has-assembled) | ~1 d, mostly literature | justifies — or relaxes by orders — the project's most expensive requirement. Extends **R-14** |
| **T-02** | mesa_80 has the EC ratchet and **0/8** β-decay partners. The predicted Yₑ bias direction vs mesa_151 has never been tested on the shipped labels | [§0.7.2](#072-electron-capture-in-a-degenerate-plasma--why-it-is-nearly-a-one-way-ratchet) | ~2 h | a physics-level validation (or refutation) of the size-transfer premise, on data already on disk |
| **T-03** | **No validity domain is declared.** T₉ < 5 is where labels are sound, gates pass, and Φ labels are feasible; T₉ ≥ 5 is none of those | [§III.6](#iii6-the-epistemics-what-a-negative-result-about-your-own-dataset-obliges) | decision + ADR | resolves the benchmark-vs-physics fork by refusing it; makes the OOD gate's job concrete |
| **T-04** | The Guidry sweep measures δ_r against **true NSE**, but the manifold relaxes to a *displaced* attractor. Departure from an equilibrium the system is not heading toward may be the wrong test | [§IV.5](#iv5-gate-5--the-guidry-sweep-returns-empty) | ~3 h | could turn the empty maskable set non-empty, reviving Component B's physics prior |
| **T-05** | No kill-test statistic carries a cluster-robust interval; ICC 0.22–0.70, n_eff ≈ 300 not 657k [derived here, §IV.8 / Tier 2 §V.3] | [§IV.8](#iv8-the-verdict-and-the-statistics-it-does-not-carry) | ~1 h | supplies the missing uncertainty on every headline number. Extends **R-08** |
| **T-06** | **No null distribution for any kill-test statistic.** Is 0.87 dex of r_QSE spread large? Is Spearman +0.49 good? Unknown | [§IV.8](#iv8-the-verdict-and-the-statistics-it-does-not-carry) | ~4 h | calibrates the scale of two published negative verdicts. Generalises **R-18** |
| **T-07** | The NNN's Yₑ error in the project's own units — **≈ 2.4 × 10⁻³/step vs the 3 × 10⁻⁶ gate, a factor ~800** — appears in no project document | [§VI.2](#vi2-reading-that-design-critically) | ~0 | calibrates ambition; forces either a defence of the gate or an admission it is over-specified. Couples to **T-01** |
| **T-08** | **Trivial baselines never run**: persistence, nearest-neighbour, and NSE-as-a-predictor | [§VI.5](#vi5-what-beating-it-has-to-mean) | ~1 h | may redefine the emulator's real domain and its real competitor. Extends **R-16** |
| **T-09** | The pathology attribution rests on **two witness states**. A stratified 24.08.1 census (≈50 states) would give the affected *fraction* and the *band boundary* | [§III.4](#iii4-the-witness-experiment) | ~1 d compute | turns "the labels are wrong above ~5 GK" into a quantified contamination map — which **T-03** needs to draw its line |
| **T-10** | **What fraction of the 1.04M-state training corpus is pathological?** The census sampled 120 states/bin at dt = 10² s | [§III.2](#iii2-the-census-how-far-are-the-labels-from-nse) | ~3 h | sizes the damage; decides whether hot-band data is discarded, reweighted, or relabelled |
| **T-11** | **Everything is constant-(T, ρ).** No data exists on time-varying conditions, which is the only mode deployment has | [§I.4](#i4-the-inlist-as-a-configuration-surface), [§0.8.1](#081-what-mesa-actually-does-per-timestep) | experiment | the label manifold is a measure-zero slice of the deployment manifold. Extends **R-11** / `tier1.md` §VIII.C.4 |
| **T-12** | **Explosive Si burning and α-rich freeze-out are outside the data** although the box overlaps their conditions | [§0.3.4](#034-hydrostatic-versus-explosive-silicon-burning), [§0.3.5](#035-α-rich-freeze-out--the-third-regime) | ~2 h analysis | states what the emulator does and does not claim to model; feeds **T-03** |
| **T-13** | **The relaxed manifold is coarse**: 7 T₉ × 3 ρ × 3 Yₑ cells, 209 runs. Nothing quantifies how representative it is of the box, or of a real track | [§I.6](#i6-why-a-rerun-campaign-was-necessary) | ~2 h | bounds the generalisability of the verdict. Couples to **R-07** |
| **T-14** | **The verdict's sensitivity to θ = 0.1 has never been swept.** The active-set threshold is unsourced and the split verdict depends on it | [§IV.6](#iv6-gate-2--the-split-verdict-and-the-1κ-amplification), [§0.9](#09-astrophysics--gates-the-mapping-table) | ~2 h | tells you whether the split verdict is a fact or a threshold artifact. Consumes **R-01**'s entropy-weighted replacement |
| **T-15** | **No solver-independent ground truth.** Every check compares MESA against pynucastro-derived rates — now known insufficient, since MESA was *wrong* | [§III](#part-iii-s13--silicon-burning-on-real-histories-and-the-label-pathology) | ~1 wk | SkyNet (Lippuner & Roberts 2017) / WinNet (Reichert et al. 2023) would have caught the pathology directly. Elevates `tier1.md` §VIII.E.3 from debt to priority |
| **T-16** | **Φ labels blocked at T₉ ≥ 5** on the neglected tabular-EC ρYₑ Jacobian chain; the unlock is identified and unimplemented | [§V.4](#v4-φ-supervision-proven-where-it-matters-blocked-where-it-does-not) | ~2 d | opens hot-strata supervision — but only matters if **T-03** keeps that band in scope |
| **T-17** | **The neutrino head has no flux-level labels.** ⟨E_ν⟩ per reaction is unsourced; the trajectory eps_nuc is *net* of ν losses, conflating the two | [§II.3](#ii3-the-pin-as-a-hypothesis-test), [§0.2.3](#023-the-neutrino-clock--why-the-last-stages-are-short) | ~1 d | ε_ν is a first-class output of the star's energy equation and is currently unsupervisable. Extends `tier1.md` §VIII.C.3 and Tier 0 §0.4.3 |
| **T-18** | **The evaluation protocol against the NNN is unspecified** — six components named, none decided. §VI.5b writes the specification; three decisions remain | [§VI.5](#vi5-what-beating-it-has-to-mean), [§VI.5b](#vi5b-the-protocol-written-out) | design, ~½ d | decides before Phase 1 what the project will claim, instead of after |

### The second-pass items (Part IX)

| ID | open item | derived in | cost | what closing it changes |
|---|---|---|---|---|
| **T-19** | **Mixing is co-dominant with burning and appears in no tier.** Da = τ_mix/τ_burn is 10⁴–10⁶ for intra-group, 10⁻⁴–10¹ for the weak sector — convection **homogenises Yₑ** and leaves the fast species local; correlated emulator error survives that averaging intact | [§0.2.5](#025-convection--the-transport-a-one-zone-burner-cannot-see) | ~3 h | a third independent argument for structural conservation, and a sharper statement of the distribution problem (real states are partly relaxed *and* partly mixed — bracketed by neither measured distribution) |
| **T-20** | **The error hierarchy has never been assembled**: 3D convection ≫ mechanism/mass cut ≫ progenitor spread ≫ rate library ≳ network size ≫ emulator target ≫ conservation drift | [§0.6.6](#066-the-error-hierarchy--what-the-emulator-is-actually-competing-with) | ~½ d | supplies the **artificial-vs-physical error** framing, which is the strongest defensible claim the project has and is not the one it currently makes |
| **T-21** | **The NSE transition is unexamined.** Some host codes (KEPLER-family, SN hydro codes) replace the network with a Saha solve above ~5–7 GK — where the labels are pathological — but MESA, the NNN's own host, runs the network throughout (Paxton et al. 2015); the emulator's competitor there is a Saha solve for NSE-switching hosts and the in-situ network for MESA | [§0.3.6](#036-the-nse-transition--where-a-network-is-replaced-by-a-table) | ~2 h | tips the benchmark-vs-physics fork toward **T-03** for NSE-switching hosts (weaker for MESA, §0.3.6 iii); identifies a much smaller (T,ρ,Yₑ)→dYₑ/dt emulator as possibly the valuable object |
| **T-22** | Every real-track statement rests on **one 20 M⊙ model**. Mass, metallicity, rotation and binarity all move the (T, ρ) locus — and binarity decides which §0.6 observable applies | [§0.4.5](#045-which-stars-are-these-actually) | ~1 d | turns **R-07**'s n = 1 measurement into a population statement; decides whether the box's uniform measure is defensible |
| **T-23** | **The deployment story with the best economics is unnamed**: parametrised-1D explodability grids run stellar evolution to collapse hundreds of times, paying the network cost each time | [§0.5.9](#059-what-explodability-actually-means-operationally) | ~0 (framing) | names a compute-bound workload that exists and would notice a 20× speedup; also splits **T-01** into its feasible and infeasible halves |
| **T-24** | ⚠ **The bottleneck premise is unmeasured.** Nobody has profiled MESA. Amdahl caps the achievable speedup at min(1/(1−p), 1/f) and **neither p nor f is known** | [§0.8.5](#085--the-bottleneck-premise-has-never-been-measured) | **~1 afternoon** | the project's founding claim, with everything needed already installed. Could justify the work strongly or force a rescope onto **T-23**'s workload |
| **T-25** | ⚠ **The host's fully-coupled route needs ∂e_nuc/∂lnT and ∂e_nuc/∂lnρ** for its implicit structure solve (MESA's `op_split_burn` route sets them to zero — Jermyn et al. 2023 §10.2 — so the requirement is route-dependent). Never specified as outputs, so nothing constrains them — and a sign error breaks the host's Newton. The second term of the derivative **is** `tier1.md` §VIII.E.2's unimplemented Q(T) | [§0.8.6](#086--the-call-site-contract--seven-requirements-nobody-has-written-down), [§I.2b](#i2b-what-the-network-returns--the-interface-as-the-host-sees-it), [§V.5c](#v5c-gradients-through-the-conservation-map--two-different-questions) | design + ~1 d | converts an installation blocker into a claimed advantage (autodiff gives exact, *smoother* derivatives than the incumbent); promotes §VIII.E.2 |
| **T-26** | ⚠ **An emulator has no convergence failure**, so the host's timestep controller loses the signal it used to reduce Δt on. S22's OOD detector may really need to be a *calibrated continuous error estimate*, not a binary fallback flag | [§0.8.6](#086--the-call-site-contract--seven-requirements-nobody-has-written-down) | design | respecifies S22 before it is built; changes what UQ has to deliver and to whom |
| **T-27** | **Per-call latency at the real batch size is uncosted.** A Fortran inner loop calling PyTorch on a 150-node graph is framework-overhead-bound; the FLOP speedup may not survive the call site | [§0.8.6](#086--the-call-site-contract--seven-requirements-nobody-has-written-down) | ~1 d | decides whether deployment needs batched-per-timestep calls, a compiled export, or both. Composes with **T-24**'s Amdahl bound |
| **T-28** | ⚠ **float32 labels versus the cancellation the model must learn.** Label noise ~10⁻⁷ relative, against dominant species whose net evolution rides on κ ~ 10⁻³ columns — *the labels may not contain the signal* | [§II.1b](#ii1b-what-a-trajectory-row-is-not) | ~2 h | either retires a serious worry or invalidates supervision on exactly the species §IV.6 flags. Sharpens `tier1.md` §VIII.E.4 |
| **T-29** | Adopt the **fixed-point audit** as a standing check on any labelled dataset: compare the longest-dt label against an independent equilibrium reference, and check invariance across dt decades. Would have caught §III on day one, in a minute | [§III.4b](#iii4b-how-this-could-have-been-caught-on-day-one) | ~0 (policy) | protects the project's own future Φ labels; a transferable method result worth stating publicly |
| **T-30** | **Positivity and exact linear conservation pull in opposite directions** — structural positivity wants an exponential map, structural conservation wants linearity, and combining them naively *is* the NuGNN failure mode. Compositional data analysis (clr/ilr, zero replacement) is the uncited literature; the projector's unweighted metric is a recorded-nowhere choice | [§V.5b](#v5b-the-output-space-is-a-simplex-and-nothing-in-the-project-treats-it-as-one) | ~½ d | the correct framing of **R-04**; extends **R-17** with why the metric choice is not innocuous |
| **T-31** | **No experiment design for the comparison.** 2 nets × 9 Δt × 6 metrics = 108 cells; a coin-flip model wins ≥60 of them ~15% of the time (≥63: ~5%). No pre-registered primary metric, no seed replication on the headline, no declared definition of "beating" | [§IX.3.1](#ix31-experiment-design-and-the-multiplicity-problem) | ~0 (policy) | `RESULTS.md`'s provenance discipline is one policy line away from pre-registration; prevents a null result becoming a paper |
| **T-32** | **The artifact lifecycle is unspecified**: no serving artifact without Python in the loop, no determinism contract across batch size / threads / device, no model identity in the consumer's output — and **the conservation guarantee must be pinned to float64 in the exported graph**, which nothing tests | [§IX.3.2](#ix32-the-artifact-lifecycle--what-actually-ships) | ADR + tests | decides whether the work is usable or merely correct; batch-size-dependent output would silently break retries |

### The third-pass items (Part X) — the emulator as an object

Nine of these ten are measurements *of a trained model* or of its coupling to a
host solver, so most cannot run before an artifact exists. They are therefore
best read as **the measurement plan the first training run should be gated on**,
not as a backlog.

| ID | open item | derived in | cost | what closing it changes |
|---|---|---|---|---|
| **T-33** | ⚠ **The emulator has its own fixed points and nobody has asked what they are.** The true map at large Δt is nearly a projection onto the NSE manifold indexed by Yₑ; the learned map's attractor is whatever the weights make it, and a per-step loss is nearly blind to it because true increments are smallest exactly there | [§X.1](#x1-the-emulator-has-its-own-fixed-points-and-nobody-has-asked-what-they-are) | ~½ d | **the same failure mode as the label pathology, in the model.** Long rollouts converge to the learned attractor, not the physical one. Runs `step6_label_nse_census.py` against a model instead of a dataset; suggests a free fixed-point consistency loss at Saha solutions. Complements **R-13** (which bounds divergence but not *which* fixed point) |
| **T-34** | **Does stiffness survive learning?** The true flow map is severely rank-deficient (spec ≈ e^{λΔt}); a learned map can be **under-contracting** (rollout blow-up — what S20's heuristics hope to prevent) or **over-contracting** (collapses the slow manifold and destroys the Yₑ signal while looking stable) | [§X.2](#x2-the-learned-jacobian--does-stiffness-survive-learning) | ~½ d | turns rollout stability from a hoped-for property into a measured one, *before* an expensive rollout study. Reference ∂Φ/∂X is available from ADR-0006's analytic ∂R/∂Y |
| **T-35** | ⚠ **A fallback dispatcher is a discontinuity in the host's Newton residual.** As the structure solve iterates, the OOD score moves and the dispatch can flip — jumping the residual by exactly the emulator-vs-solver difference the gate exists because it is large | [§X.3](#x3-the-fallback-gate-is-a-discontinuity-in-the-hosts-implicit-solve) | design | classic discontinuous-EOS pathology, reproduced. Three mitigations, none specified; the training-side analogue (mask churn) *is* specified in the architecture report, which shows the pattern was seen one level up and not carried down |
| **T-36** | **ρ is not a free input dimension.** One-/two-/three-body sectors scale as ρ⁰/ρ¹/ρ², so a two-body-only network would be exactly invariant under (ρ, Δt) → (λρ, Δt/λ) | [§X.4](#x4-ρ-is-not-a-free-input-dimension) | ~2 h | a structured conditioning variable (ρΔt) composing with **R-10**'s Δt/τ; a **label-free consistency test** (the model's invariance violation must match the reference's); and a rate-free probe of QSE onset |
| **T-37** | **"Calibrated" has a literature the project has not named.** Deep ensembles are the most expensive UQ (**R-12**'s critical path) and, like every UQ method, lose calibration under the distribution shift §IV.3 *measured* — they degrade least in Ovadia et al. (2019), but still substantially. Conformal prediction is the tool; its exchangeability assumption fails in two already-quantified ways | [§X.5](#x5-what-calibrated-means-for-a-deterministic-map) | ~½ d | **weighted conformal needs exactly R-07/T-13's density ratio** — two unrelated-looking items are one measurement. And the project already computes four free physics-residual OOD scores (entropy sign **R-05**, energy consistency, positivity **R-04**, fixed-point distance **T-33**) without labelling them as such |
| **T-38** | **Rates as inputs — the capability nobody claimed.** With a low-dimensional rate-perturbation input, autodiff gives ∂Yₑ′/∂θ at inference, i.e. §IX.3.3's propagation study in milliseconds | [§X.6](#x6-rates-as-inputs--the-capability-nobody-claimed) | scope decision | changes what the artifact *is*: from a fast network to a differentiable model of the network's dependence on its own inputs. Affordable restricted forms: a categorical FFN/LMP selector, or multipliers on the top-20 Yₑ carriers |
| **T-39** | **Which Δt does the host actually take?** The nine-decade grid is inherited from the NNN, which inherited it from nobody's measurement | [§X.7](#x7-which-δt-does-the-host-actually-use) | ~0 (same run as **T-24**) | tells you which decades are training capacity spent on regions never visited, and where extrapolation risk actually lives |
| **T-40** | **Sample complexity / capacity allocation.** Training compositions are random, hence spread over the full 80-dim simplex; deployment lies on a 3–9 dim manifold (**R-02**) — so most of the corpus and most of the model's capacity go to states it will never be asked about | [§X.8](#x8-sample-complexity--a-million-points-in-82-dimensions) | ~2 h | an argument for trajectory-derived data on **sample-efficiency** grounds, independent of distribution shift; predicts a few 10³ on-manifold states could beat a great many off-manifold ones, which would make §V.4's Φ-label budget the right design rather than a compromise |
| **T-41** | ⚠ **An unretired design premise, found while sweeping**: the architecture report's "⁴⁵Sc(p,γ)⁴⁶Ti carries **≈75%** of the inter-group flow" versus the measured **share 0.10–0.12, rank 2/251 (mesa_151); top-20 carry 0.88 (mesa_80)**. Both documents report this as CONFIRMED — which it is *qualitatively* and is not *quantitatively* | [§X.10](#x10-one-unretired-premise-found-while-sweeping) | ~1 h | second instance of a named pattern — **a magnitude attached to a correct qualitative claim that does not survive measurement**: unsourced for "6–8 orders" (retired §IV.7), sourced-but-transplanted for the 75% (Woosley, Arnett & Clayton 1973 via Hix & Thielemann 1996: ≈70% of the flux *into the iron-peak group* at one state, not the share of all inter-group carriers on the relaxed manifold). Retire with the measured replacement, then audit the remaining inherited premises for others. A `referee` task |
| **T-42** | **Write the Tier-4 Part 0 before the first training run.** §X.1–X.5 plus **R-03/R-05/R-13/R-21/R-24** are its contents; four open Phase-0 checklist rows are its measurements; two architecture components have retired premises waiting there | [§X.11](#x11-is-the-audit-converging-now) | ~1 wk | converts a list of post-hoc diagnostics into a **gate on the first training run**, which is the only time most of them are cheap |

## VIII.2 Ranked — the top eight

By (leverage on a project conclusion) ÷ (cost to close). The second-pass items
displace two of the original six, and the top of the list has changed character:
it is now dominated by **questions about whether the project is aimed correctly**,
which is what a boundary audit produces.

| # | item | cost | why it is here |
|---|---|---|---|
| 1 | ⚠ **T-24** — profile MESA; get p, then Amdahl | **1 afternoon** | The founding premise, unmeasured, with MESA already built. min(1/(1−p), 1/f) bounds the entire enterprise and **neither factor is known**. If p = 0.5 the ceiling is 2× and everything downstream is differently valuable. Nothing else is this cheap and this decisive. |
| 2 | **T-03** — declare the validity domain | decision + ADR | Free. Resolves an escalated fork, scopes **T-16**, gives the OOD gate a target, and — with **T-21**'s observation that host codes use NSE there anyway — is now clearly the right call rather than merely a defensible one. |
| 3 | **T-07 + T-01 + §IX.3.3** — is 3 × 10⁻⁶ the right gate? | ~1 d each | Three independent routes to the same question, which sets the project's whole cost. **Do §IX.3.3 first** (rate-uncertainty propagation): the machinery exists, and it is the only one of the three that is both cheap and complete. **T-07** is a division whose inputs both exist — the baseline sits ≈800× outside the gate and nobody has written that down. |
| 4 | **T-08 + T-21** — the real incumbent | ~1 h | Run NSE, persistence and nearest-neighbour as baselines; and notice that above 5 GK an NSE-switching host code would use a Saha solve, not a network (MESA, the NNN's own host, would not — §0.3.6). Together these may redefine the emulator's domain *and* its competitor, which is a scoping result, not a measurement. |
| 5 | **T-05 + T-06 + T-14** — make the verdict a claim | ~½ d | Cluster bootstrap over trajectories, null distributions (including the **positive control that the mask detector can detect a mask**), and the θ sweep. §IV.8b predicts the intervals will be wide enough that the split verdict's *boundaries* are soft. A referee finds all three immediately. |
| 6 | ⚠ **T-25 + T-26** — the interface requirements | design + ~1 d | An emulator with no ∂e_nuc/∂lnT cannot be installed on MESA's fully-coupled route (its `op_split_burn` route already runs without them), and removing the network's convergence failure silently breaks the host's timestep controller. Both respecify S22 *before* it is built. **T-25** also promotes `tier1.md` §VIII.E.2 from an accuracy item to a prerequisite. |
| 7 | **T-31 + T-18 + T-29** — decide the rules before the numbers | ~0, policy | Pre-register a primary metric, declare what "beating" means, and adopt the fixed-point audit as a standing dataset check. All three are policy lines on infrastructure the project already has, and all three become impossible to adopt honestly once results exist. |
| 8 | **T-09 + T-10 + T-28** — quantify the damage | ~1 d compute | The pathology rests on n = 2 witnesses and a 120-state-per-bin census; and **T-28** asks whether float32 labels even contain the cancellation the model must learn. **T-03** needs the first two to draw its line honestly. |

Displaced but not dismissed: **T-19** (mixing) and **T-20** (the error hierarchy)
are the two that most change how the project *talks about itself* — the
artificial-versus-physical error framing is the strongest claim available and is
not currently made — but neither changes what to do next week.

The shape of the ranking is worth naming. **Six of the eight are cheap; five are
about knowing what you already have rather than measuring something new; and four
are scoping decisions rather than experiments.** That is the characteristic
signature of a project that has done a great deal of careful work and has not yet
stopped to ask what it establishes, for whom, and against what.

**The third-pass items rank separately, and deliberately so.** Nine of the ten
require a trained model, so they cannot compete with the eight above on
do-it-now grounds. They form a second list — *the gate on the first training
run* — with its own order:

| # | item | why in this order |
|---|---|---|
| 1 | **T-42** — write the Tier-4 Part 0 first | It is the container for everything below, and it is the item `tier1.md` §VIII.E.1 has been asking for since Tier 1. Doing it *before* training is the difference between a measurement plan and a post-mortem. |
| 2 | **T-33** — the fixed-point census | The largest single risk that no existing gate can see, it is this tier's own headline failure mode aimed at the model, and the instrument (`step6_label_nse_census.py` + `solve_nse`) already exists. |
| 3 | **T-34** — the Jacobian spectrum | Turns S20 from heuristics into a checked property, and can be run on a half-trained model to catch a bad architecture early. |
| 4 | **T-35 + T-37** — the deployment numerics of the gate | Both respecify S22 before it is built: one says a dispatcher breaks the host's Newton, the other says the specified ensemble is the wrong tool on both statistical and economic grounds — and that four free physics-residual scores already exist. |
| 5 | **T-36 + T-39 + T-40** — conditioning and data design | All three change what the training run *is* (inputs, Δt coverage, which states to label), so they are worth settling before spending the compute, and all three are cheap. |
| 6 | **T-41** — audit the inherited premises | An hour, a `referee` task, and it is the second instance of a named pattern rather than a one-off. |
| 7 | **T-38** — rates as inputs | A scope decision to *record*, most likely deferred; it changes what the artifact is for, and deciding it late costs a retraining. |

## VIII.3 How this register was built

Two passes, mirroring `tier2.md` §VII's method.

**Pass 1 — per-node gap sweep.** For each of S11–S16, three questions: what does
this node assume that nothing measures? what does it measure whose *scale* is
uncalibrated? what does it decide that could have been decided otherwise?
Produced T-02, T-04, T-05, T-06, T-09, T-10, T-13, T-14, T-16, T-18.

**Pass 2 — swept along axes the nodes do not organise by.** Domain of validity
(T-03, T-12), deployment realism (T-11), external references (T-01, T-07, T-08),
independent verification (T-15), and outputs other than composition (T-17).

**Axes checked and found already covered**, listed so the sweep is auditable:

| axis | already covered by |
|---|---|
| conservation exactness | Tier 2 §I.2, gate is blocking |
| rate provenance | Tier 1 §VI, 135 outliers class-explained |
| join keys and dataset identity | §I.5, `state_id` discipline |
| screening convention | `CLAUDE.md` two-κ rule + `manifold.py`'s refusal |
| group-boundary sensitivity | config variant, both reported, ≤0.02 effect |
| campaign reproducibility | manifests + sha256 + DONE sentinels |
| energy convention | §II.3, pinned by measurement |
| positivity | Tier 2 **R-04** (open there, not duplicated here) |
| identifiability | Tier 2 **R-03** (referenced in §V.5, not duplicated) |
| the speedup ceiling | Tier 2 **R-12** |

**Pass 3 — the boundary sweep**, run as a separate audit and written up as
[Part IX](#part-ix--prerequisites-outside-the-map-a-cross-tier-audit). It swept
three axes the tier map does not organise by (the physical setting outside the
burning zone; the interface; the mathematics and practice of producing the
result) and produced **T-19 … T-32**.

**Pass 4 — the emulator as an object**, written up as
[Part X](#part-x--the-third-pass-the-emulator-as-an-object). Run without waiting
for an artifact, by asking what one would measure *of* a trained model and what a
host solver would do *with* it. Produced **T-33 … T-42**.

**Is it converging?** [§IX.5](#ix5-is-the-audit-converging) gives the answer after
pass 3 and [§X.11](#x11-is-the-audit-converging-now) the answer after pass 4 — the
short version being that the yield stopped *spreading*: pass 3's ten items sat on
four axes, pass 4's ten sit on one. The remaining unexplored prerequisite is
essentially a single subject — **the theory and practice of a learned flow map** —
which is a Tier-4 Part 0 (**T-42**). The fuller reasoning follows;
the short version is that **the physics audit has converged and the boundary audit
has not.** Pass 3's physics axis found exactly one gap (mixing) — and that one was
already a flagged caveat in Tier 0, so the audit upgraded a known approximation
rather than discovering an unknown. Its *interface* axis found four items from
four questions. A pass that scores every time it looks is not finished, and the
structural reason is that the project has no artifact yet: there is nothing to ask
interface questions of. Expect another audit's worth when the first model is
deployed.

The honest statement, now across all three passes: **the measurement debt in Tier
3 is small, the interpretation debt is large, and the interface debt is entirely
unpaid.** Of thirty-two items, eleven cost an hour or less; five of those are
about reading numbers that already exist; and four of the top eight are scoping
decisions rather than experiments.

---

# Part IX — Prerequisites outside the map: a cross-tier audit

The tier map (S0–S16, plus the sketched S17–S22) organises the project by
*where the physics lives*. This part asks the orthogonal question: **what is
prerequisite to this project that the map has no node for at all?** It is a
second-pass audit across all four written tiers, and it is the reason several
sections of Part 0 exist.

## IX.1 What was swept, and how

Three passes over different axes, deliberately chosen to be ones the map does not
organise by:

- **Pass A — the physical setting outside the burning zone.** Everything a
  stellar-evolution model does that is *not* the network: transport, structure,
  the progenitor's history, and the collapse's numerics. Produced **T-19**
  (mixing), **T-21** (the NSE transition), **T-22** (the progenitor grid),
  **T-23** (what actually runs these calculations).
- **Pass B — the interface.** What consumes the emulator's output, in the
  concrete sense of a function signature. Produced **T-24** (the bottleneck
  fraction and Amdahl), **T-25** (host-side derivatives), **T-26** (the lost
  convergence signal), **T-27** (per-call latency and interop).
- **Pass C — the mathematics of the answer, and the practice of producing it.**
  The geometry of the output space, the statistics of the claims, and the
  lifecycle of the artifact. Produced **T-28** (float32 vs cancellation),
  **T-30** (the simplex), **T-31** (multiplicity), **T-32** (the artifact
  lifecycle), plus **T-20** (the error hierarchy) and **T-29** (the fixed-point
  audit) as methodological items.

Each pass asked the same three questions of its axis: *what does the project
assume here? what would a practitioner in this area immediately ask? and is there
any test that could currently fail?*

## IX.2 The areas with no study node anywhere

| area | prerequisite because | nearest existing coverage | now at |
|---|---|---|---|
| **Convection and mixing** | the network's output is immediately mixed; the burning/mixing competition decides whether Yₑ errors average out | Tier 0 §0.7's timescale row + a one-line caveat | §0.2.5, **T-19** |
| **The NSE transition** | the host replaces the network with a table exactly where the labels are pathological | `tier1.md` §VIII.E.6 ("the handoff is unspecified") | §0.3.6, **T-21** |
| **Progenitor diversity** | every real-track statement rests on one 20 M⊙ model | Tier 2 §V.2 (that one model) | §0.4.5, **T-22** |
| **What computes explodability** | **T-01** asks for a derivative of it | nothing | §0.5.9, **T-23** |
| **The error hierarchy** | decides whether the improvement is scientifically visible | scattered; never assembled | §0.6.6, **T-20** |
| **The runtime fraction p** | the project's founding premise; Amdahl caps everything | Tier 0 §I.3 derives the *scaling*, never the fraction | §0.8.5, **T-24** |
| **The call-site contract** (7 items) | an emulator that cannot be installed is not a result | Tier 2 **R-11** covers 2 of the 7 | §0.8.6, §I.2b, **T-25/26/27** |
| **Simplex geometry / compositional data** | it is the space the output lives in, with a mature literature | Tier 2 §I.7b (positivity, as a physics worry) | §V.5b, **T-30** |
| **Experiment design & multiplicity** | 18 cells × 6 metrics makes "we win" cheap | nothing | §IX.3.1, **T-31** |
| **Artifact lifecycle** | what ships, and whether it reproduces | Tier 2 **R-25** (shelf life, physics side only) | §IX.3.2, **T-32** |

Ten areas. Note the shape: **one is physics-internal (mixing), four are about the
physical setting the project sits inside, three are about the interface, and two
are about the practice of producing and shipping the result.** The map's blind
spot is not the physics — Tiers 0–2 are thorough — it is everything on the
boundary of the physics.

## IX.3 Three developed here, having no home section

### IX.3.1 Experiment design and the multiplicity problem

The project will compare an emulator against a baseline across
**2 networks × 9 Δt × 6 metrics = 108 cells**, and it has already done exactly
that once, for the reproduction (**[RESULTS]** 2026-07-08, "ratio 1.000 in all
108 comparisons"). For a *reproduction* that is a strength — 108 exact matches is
overwhelming evidence. For a *comparison* it is a trap.

**The arithmetic.** If two models are genuinely equivalent and each cell is a coin
flip, the probability that one wins **at least 60 of 108** cells is about 15%
(at least 63 of 108: about 5% — corrected in the 2026-08-18 audit; the earlier
text put 5% at 60), and the probability of winning at least one cell "by a lot"
is essentially 1. With
per-cell noise from training seeds and test-set sampling, a table of 108 numbers
will always contain a flattering subset. [derived here — binomial]

**What the project needs and does not have:**

1. **A pre-registered primary metric.** One number, chosen before training,
   against which the claim is made. Everything else is secondary and labelled as
   such. The obvious candidate is absolute |ΔYₑ| p99 on the relaxed manifold in
   the QSE window — it is the project's own quantity, on the deployment
   distribution, in the regime it claims.
2. **Seed replication.** `CLAUDE.md` already requires three seeds for the
   *learned-mask regression* trigger, which shows the instinct is present; it is
   not required for the headline comparison. Without ≥3 seeds there is no way to
   distinguish a model improvement from an initialisation.
3. **Correction for multiplicity** on the secondary table — or, more honestly,
   the discipline of reporting the whole table and claiming nothing from
   individual cells.
4. **A pre-declared definition of "beating"** (§VI.5b's open decision 3), because
   deciding it after seeing the numbers is how a null result becomes a paper.

None of this is exotic; it is standard experimental practice imported from fields
that had a replication crisis. The project's `RESULTS.md` discipline — every
number dated, scripted, and provenanced — is *exactly* the infrastructure that
makes pre-registration cheap, and it is one line of policy away from having it.
Registered as **T-31**.

### IX.3.2 The artifact lifecycle — what actually ships

Tier 2 **R-25** asks what a rate-library or MESA version bump does to a trained
emulator. That is the *physics* half of a larger question the project has not
posed: **what is the deliverable, and can someone else run it in five years?**

Six components, with the project's current status:

| component | status |
|---|---|
| the trained weights | n/a (pre-training) |
| the **exact ν, C, isotope order, and column order** the weights were trained against | **excellent** — exported deterministically with content hashes, `disposition_sha256` in the npz |
| the rate configuration (REACLIB snapshot, weaklib ordering, screening) | **excellent** — pinned, reconciled, measured |
| a **serving artifact** with no Python in the loop | **nonexistent** (§0.8.6.5, **T-27**) |
| **determinism** across thread counts, devices, and batch sizes | **unspecified** (`tier1.md` §VIII.E.4) |
| **model identity recorded in the consumer's output** | **unspecified** (§0.8.6.7) |

The first three are as good as any project of this kind. The last three are
absent, and they are the ones that decide whether the work is *usable* rather than
merely *correct*.

Two specific traps worth naming because they are cheap to avoid in advance and
expensive to fix later:

- **Batch-size-dependent output.** Many frameworks produce bitwise-different
  results at different batch sizes (different GEMM kernels, different reduction
  orders) [engineering, assumed — no source opened]. A stellar code that batches a variable number of zones per timestep
  will therefore get different answers for the same zone depending on how many
  neighbours were in the batch — and, worse, a *retry* (§0.8.6.4) may batch
  differently. This must be a declared, tested contract, not a hope.
- **The conservation guarantee must survive export.** dY = νφ in float64 is
  exact; the same computation in a float32 inference graph is not. The
  conservation map has to be pinned to float64 *in the exported artifact*, which
  is a concrete constraint on how the model is compiled, and `CLAUDE.md`'s
  "float32 in model internals only" rule is the policy that anticipates it —
  but nothing tests it end to end.

Registered as **T-32**. It is an ADR plus a test, not a research programme.

### IX.3.3 Nuclear-data uncertainty is probably the binding term — promote it

This is not a new area; it is `tier1.md` §VIII.C.1 (rate uncertainty → Yₑ
propagation) and §VIII.C.5 (mass/Q provenance). The audit's contribution is to
argue that they should be **first**, not twelfth.

The argument, in three steps:

1. §0.6.6's hierarchy puts the emulator's target (3 × 10⁻⁶/step) *below* the
   weak-library shift (5 × 10⁻³/trajectory) by design. That is the intended
   relationship — but it is a comparison against **one** known systematic.
2. The *unknown* systematics are the Hauser–Feshbach rate uncertainties on
   unmeasured channels, which Tier 1 §1.3.3 puts at factor-of-two scale for the
   experimentally inaccessible ones (Rauscher & Thielemann 2000 estimate their
   rates "within a factor of 1.5–2"), and the mass/Q differences, which Tier 1
   §VIII.C.5 notes enter as e^{−Q/kT} with Q/kT ≈ 20–50 for individual channels
   (Q ≈ 7–13 MeV at kT ≈ 0.26–0.43 MeV; hundreds to ~2000 only for total binding
   energies in the Saha exponent) — a 100 keV Q difference is a **47% rate
   difference** at kT = 0.26 MeV.
3. Nobody has propagated either to Yₑ. If the propagated uncertainty is 10⁻³ per
   trajectory, the gate is well placed. If it is 10⁻², the gate is
   over-engineered by orders and **the entire cost wall of Tier 2 §IV.9 is being
   paid for nothing.**

**Everything needed to answer it exists**: the batch engine evaluates every rate
in milliseconds, the reference integrator produces trajectories, and the outlier
census (135 channels, all class-explained) already identifies which channels are
uncertain. A Monte Carlo over rate perturbations on a few hundred states in the
QSE window is a day's compute.

It is the cheapest of the three routes to answering *"is 3 × 10⁻⁶ the right
gate?"* — the others being **T-01** (the output derivative, partly infeasible per
§0.5.9) and **R-11** (the split-error comparison, which needs an experiment). The
audit's recommendation is to do this one first and let it inform the other two.

## IX.4 Axes checked and found already covered

Listed so the sweep is auditable rather than merely asserted:

| axis | covered by |
|---|---|
| plasma EOS, degeneracy, Coulomb coupling | Tier 0 §0.1 |
| statistical mechanics, detailed balance | Tier 0 §0.2, Tier 1 §III |
| rate theory, Gamow, Hauser–Feshbach | Tier 1 §I |
| screening | Tier 1 §IV, with the two-κ rule as executable policy |
| the weak sector, EC in a degenerate plasma | Tier 1 §V |
| stoichiometry, conservation, projection | Tier 2 §I |
| cancellation, κ, entropy production | Tier 2 §II |
| NSE/QSE algebra | Tier 2 §III |
| stiff integration, the augmented state | Tier 2 §IV |
| dataset identity, join keys, censoring | Tier 0 §III, §I.5 here |
| CRN theory, flux cones, deficiency | Tier 2 §I.2b |
| the speedup ceiling under fallback | Tier 2 §0.5b |
| e⁺e⁻ pairs at the hot corner | Tier 1 §VIII.C.6 (promoted to a decision) |
| isomers, ground-state vs stellar rates | Tier 1 §VIII.C.2, §VIII.C.8 |
| neutrino loss channels | Tier 0 §0.4, Tier 1 §V.8 |
| learning theory / operator learning | Tier 2 **R-24** (sketch) |
| rollout accumulation theory | Tier 0 §IV.3 |
| GNN architecture specifics | Tier 4 sketch, `tier1.md` §VIII.E.1 |

Eighteen axes, all genuinely covered. The audit's yield (ten new areas) came
entirely from asking about the *boundary* of the physics rather than its
interior.

## IX.5 Is the audit converging?

Honestly: **the physics audit has converged; the boundary audit has not.**

Evidence for the first: passes A–C found exactly one physics-internal gap
(mixing), and it was already flagged as a caveat in Tier 0 — the audit upgraded a
known approximation to a quantified one rather than discovering something
unknown. Four tiers of derivation have found essentially everything a physicist
would ask.

Evidence against the second: pass B (the interface) found four items from four
questions, at a 100% hit rate, and pass C found four more. **A pass that finds
something every time it looks has not converged**, and the reason is structural:
the project has no artifact yet, so there has been nothing to ask interface
questions *of*. Those questions will keep producing answers until an emulator
exists and is called from something.

The practical reading: **expect another audit's worth of items when the first
model is deployed, and budget for it.** The right response is not to try to
enumerate them now — that is how you get a speculative list — but to notice that
the current register's cheapest and highest-ranked items (**T-24**, **T-03**,
**T-08**) are all *scoping* decisions that would make the eventual interface work
smaller. Doing scope before capability is the correct order and the register
already reflects it.

---

# Part X — The third pass: the emulator as an object

[§IX.5](#ix5-is-the-audit-converging) predicted that another audit's worth of
items would appear once there was an artifact to ask questions of, and that the
interface axis had not converged. This part is that prediction tested early — a
third pass run *without* waiting for a model, by asking what one would measure
**of** a trained emulator and what a stellar code would do **with** it.

It found ten more. They are not scattered: **nine of the ten are about the model
as a dynamical object or about its interaction with a host solver**, which is the
same region pass B found. That localisation is the useful result — §X.11.

## X.1 The emulator has its own fixed points, and nobody has asked what they are

This is the strongest item in the pass, and it is a direct generalisation of the
tier's own headline finding.

**The true map's fixed-point structure.** At constant (T, ρ) the one-step map
Φ_Δt is the time-Δt flow of an autonomous ODE, and its fixed points are that
ODE's equilibria. For the strong/EM sector that is **NSE at the current Yₑ** — a
one-parameter family, since the strong sector cannot move Yₑ (§0.7.1; the
Yₑ-parametrised NSE of Hix & Thielemann 1996 — physics reasoning here, not a
quoted result). Include
the weak sector and the family collapses to a single point (β-equilibrium), but
only on timescales far longer than anything here. So:

$$
\Phi_{\Delta t}(X) \;\xrightarrow[\ \Delta t \gg \tau_{\text{strong}}\ ]{}\;
X_{\mathrm{NSE}}\big(T,\rho,Y_e(X)\big) ,
$$

i.e. **at large Δt the true map is very nearly a projection onto a
one-dimensional attracting manifold indexed by Yₑ.**

**The learned map's fixed-point structure is whatever the weights make it.**
Φ̂_Δt is some smooth function; its fixed set {X : Φ̂(X) = X} is determined by
parameters fitted to minimise a per-step loss. Nothing in the training objective
mentions fixed points. There is no reason for the learned attractor to be the
NSE manifold, to be one-dimensional, to be indexed by Yₑ, or to exist at all.

Four consequences, in increasing order of how much they should worry someone:

1. **A long rollout converges to the learned attractor, not the physical one.**
   Per-step accuracy controls the transient; the fixed-point structure controls
   the destination. For N ≈ 10³ steps in a strongly contracting system, the
   destination is most of the answer.
2. **Per-step loss is nearly blind to it.** Near an attracting fixed point the
   true increment is *small*, so a model can have tiny per-step error there and
   still put its own fixed point somewhere else entirely — the errors that
   relocate an attractor are exactly the ones a small-increment loss weighs
   least.
3. **This is the same failure the labels have.** §III found the *label generator*
   sitting at a displaced fixed point and called it a pathology. A trained
   emulator can acquire a displaced fixed point of its own, from a different
   cause, with the same consequence — and it would be invisible to every gate the
   project currently specifies.
4. **Yₑ is the parameter of the true attractor manifold.** If the learned
   attractor does not depend on Yₑ in the right way, the model gets the
   *endpoint* of silicon burning wrong as a function of the very quantity the
   project exists to predict (§0.3.3).

**And it is trivially measurable, with tools already built.** Iterate the trained
map to convergence at fixed (T, ρ) from many starting compositions, and compare
the limit against `qse.solve_nse`:

$$
X_\infty \;=\; \lim_{k\to\infty}\hat\Phi_{\Delta t}^{\,k}(X_0)
\quad\text{(iterate until } \|\Delta X\| < \mathrm{tol}\text{)},
\qquad
d \;=\; \big\|\log X_\infty - \log X_{\mathrm{NSE}}\big(T,\rho,Y_e(X_\infty)\big)\big\|_\infty ,
$$

sweeping X₀ over many starting compositions to find how many distinct attractors
exist and how far each sits from the Saha solution.

That is `scripts/step6_label_nse_census.py` pointed at a model instead of at a
dataset — the same census, the same reference solver, the same statistics. It is
also the direct extension of **T-29**'s fixed-point audit from datasets to
models, and it should be a standing gate, not a one-off.

**It also suggests a training term nobody has proposed.** Add a fixed-point
consistency penalty ‖Φ̂(X_NSE) − X_NSE‖ evaluated at Saha solutions — free
supervision (the Saha solver is cheap and exact), aimed precisely at the property
the per-step loss cannot see. It pins the model's attractor to the physical one
without touching the conservation map.

Note how this sits against Tier 2 **R-13**: a second-law-consistent emulator
cannot *diverge* — the Helmholtz free energy bounds the fast sector — but a
Lyapunov bound says nothing about **which** fixed point the descent reaches.
R-13 gives stability; this gives correctness of the destination. They are
complementary and only the first is on the register. Registered as **T-33**.

## X.2 The learned Jacobian — does stiffness survive learning?

The companion diagnostic, equally cheap and equally absent.

**What the true map's Jacobian looks like.** If J = ν ∂R/∂Y is the ODE Jacobian
with eigenvalues λ_i (Tier 0 §V.3: spread 10¹²–10¹⁵), then the flow map's
Jacobian has eigenvalues ≈ e^{λ_i Δt} (the standard linearisation of a stiff
flow, Hairer & Wanner 1996). With most λ_i strongly negative and
Δt large:

$$
\text{spec}\!\left(\frac{\partial \Phi_{\Delta t}}{\partial X}\right)
\;\approx\; \big\{\,e^{\lambda_i \Delta t}\,\big\}
\;\longrightarrow\; \{\underbrace{\approx 0,\dots,\approx 0}_{\text{the stiff directions}},\ \underbrace{O(1)}_{\text{the slow manifold}}\} .
$$

**The true one-step map is severely rank-deficient**: it annihilates almost every
direction and preserves a handful. That is the same statement as "stiff", as
"QSE", and as "the reachable set has effective dimension 3.4 / 8.6" (**R-02**,
Tier 2 §I.10b [derived there]) —
this tier's §0.3.1 list of four names for one mechanism, now seen through the
flow map's spectrum.

**What that demands of the emulator, as two failure modes with opposite signs:**

| failure | signature | consequence |
|---|---|---|
| **under-contraction** — learned singular values > 1 where the true map has ≈ 0 | the model preserves directions physics destroys | rollout amplifies its own error along stiff directions: the classic autoregressive blow-up (Brandstetter, Worrall & Welling 2022), and precisely what S20's pushforward loss (Brandstetter et al. 2022) and noise injection (Sanchez-Gonzalez et al. 2020) are *heuristics* for |
| **over-contraction** — learned singular values ≈ 0 where the true map has O(1) | the model collapses the slow manifold too | it destroys the Yₑ signal and the bridge flow — the physics — while looking beautifully stable |

Both are measurable in one line with autodiff, against a reference the project
already produces: `fluxes/integrate.py` can supply the true ∂Φ/∂X by forward
sensitivity, and its analytic ∂R/∂Y is already implemented (ADR 0006).

**Why this matters more than a diagnostic usually would.** S20 is currently
specified entirely in terms of *training tricks* — pushforward losses, noise
injection restricted to non-equilibrated channels, the Ono & Sugimura governor —
with no measurement that says whether the trained map is contracting on the right
subspace. A spectral comparison turns rollout stability from a hoped-for property
into a checked one, and it does so **before** an expensive rollout study rather
than after. Registered as **T-34**.

## X.3 The fallback gate is a discontinuity in the host's implicit solve

A specific and serious interaction that no document anticipates.

MESA's structure solve is a **Newton iteration** over the whole stellar model
(Paxton et al. 2011 §6; Jermyn et al. 2023 — the partial derivatives are now
supplied by automatic differentiation), and the network's output enters the
residual (through e_nuc, the composition, and the EOS's dependence on Ā and Z̄).
Newton needs a residual function that is smooth in the iterates.

Now insert S22's design: an OOD detector computes a score s(X, T, ρ) and
**dispatches** to either the emulator or the real solver. As Newton adjusts the
state during its iteration, s changes; if it crosses the dispatch threshold, the
residual function **jumps** by the emulator-vs-solver difference — which is
precisely the quantity the gate exists because it is large.

The consequences are the standard ones for a discontinuous residual, and they are
not subtle: Newton fails to converge, or cycles between two branches, or
converges to a spurious point on one side. The host responds by **cutting the
timestep**, which changes the state, which may flip the dispatch again. This is a
well-known pathology with discontinuous EOS tables and phase transitions (MESA
blends its EOS and opacity tables, Paxton et al. 2011, and had to handle the
discontinuous derivatives of the Skye crystallisation transition explicitly,
Jermyn et al. 2023), and it is exactly reproduced here.

**Three mitigations, none currently specified:**

| mitigation | cost |
|---|---|
| **freeze the dispatch for the duration of one Newton solve** (decide once from the incoming state) | free; probably the right default |
| **blend continuously in a band** — a weighted average of emulator and solver over a threshold interval | pays the solver's cost across the whole band, worsening the effective f of the 1/f ceiling |
| **require agreement to within solver tolerance in the switching band** — i.e. only switch where it does not matter | strongest, but constrains where the gate is allowed to fire |

**Credit where it is due, and the distinction.** `docs/reports/consolidated-gnn-
architecture.md` §5 already identifies that *mask membership flips* inject
discontinuities in dY and e_nuc that destabilise **the rollout gradient**, and
proposes churn penalties, annealed gates and hysteresis. That is the same
mathematics one level up, applied to training. What is new here is that the same
problem appears **at the host's Newton solve at deployment**, where the switch is
not the mask but the *fallback dispatcher*, and where the remedies available
during training (annealing, soft gates) are unavailable. Registered as **T-35**.

## X.4 ρ is not a free input dimension

An architecture insight that falls out of the rate structure and that nothing in
the project uses.

Write the ODE by reaction order. At fixed T, with Y-dependence factored out:

| sector | contribution to dY/dt | ρ-dependence |
|---|---|---|
| one-body (photodisintegration, β-decay) | λ(T)·Y | **none** |
| two-body (captures) | ρ N_A⟨σv⟩(T)·Y_aY_b | **∝ ρ** |
| three-body (triple-α and friends) | ρ² …·Y_aY_bY_c | **∝ ρ²** |
| tabulated weak (EC) | λ(T, ρYₑ)·Y | through **ρYₑ** |

Change variables to τ = ρ t. Then the two-body sector becomes ρ-free, the
three-body sector carries one power of ρ, the one-body sector carries ρ⁻¹, and
the tabulated sector carries whatever the table does. So:

> **If the network contained only two-body reactions, the map would be exactly
> invariant under (ρ, Δt) → (λρ, Δt/λ).** ρ would not be an independent input at
> all — only the product ρΔt would matter. (With screening off: the screening
> enhancement depends on ρ through Γ and breaks the invariance.)

The real network is not two-body-only, and the symmetry-breaking terms are
*exactly the physically interesting ones* — photodisintegration is what creates
the equilibrium (§0.2.1), and electron capture is what moves Yₑ. That is the
point rather than an objection, and it yields three usable consequences:

1. **A better conditioning variable.** The model is currently conditioned on
   log ρ and log Δt as separate features. **ρΔt** captures the entire two-body
   sector — the numerical majority of columns (ch. 4–5 alone are 397/979 of the
   reactions **[RESULTS]** 2026-07-08; ch. 6–7 are two-body too) — in one variable, leaving the network to
   learn only the *departure* from that scaling. This composes with Tier 2
   **R-10**'s Δt/τ proposal rather than competing with it: R-10 says condition on
   how many relaxation times the step covers, and this says the density enters
   that relaxation through a known power law.
2. **An exact consistency test.** Evaluate the trained model at (ρ, Δt) and at
   (λρ, Δt/λ) and compare against the same pair evaluated on the reference
   integrator. The *reference* violates the invariance by a known, computable
   amount (the one- and three-body contributions); the model's violation should
   match it. A model whose violation is the wrong size has learned the wrong
   decomposition, and this test needs no labels.
3. **A physical diagnostic for free.** The measured degree of invariance
   violation, per stratum, **is** a measure of how much of the local dynamics is
   photodisintegration-driven — i.e. an independent, rate-free probe of exactly
   the QSE onset that §0.2.1 derives from Q/kT.

Registered as **T-36**.

## X.5 What "calibrated" means for a deterministic map

**T-26** concluded that S22 needs a *calibrated continuous error estimate* rather
than a binary flag. That conclusion has a literature and an assumption problem,
neither of which is in any document.

**The specified approach is deep ensembles**, and it has two independent
difficulties here:

- **Economics.** An ensemble of size k costs k× per call, and every call — not
  just the fallbacks. Tier 2 §0.5b's cost model puts t_det on the critical path
  and shows a detector costing 10% of the solver caps the speedup at 10× before
  a single fallback happens. An ensemble is the most expensive UQ there is, in a
  setting where **R-12** shows the detector's cost is a first-order term.
- **Statistics.** All UQ methods, deep ensembles (Lakshminarayanan, Pritzel &
  Blundell 2017) included, **lose calibration under distribution shift** — ensembles degrade least in the benchmark of Ovadia
  et al. (2019) but still substantially — and distribution shift is not a risk
  here — it is a *measured fact* (§IV.3). (The earlier wording "worst-calibrated
  under shift" inverted the source; corrected in the 2026-08-18 audit.) The consolidated architecture report already names
  this as a load-bearing risk ("a jointly-overconfident ensemble could fail the
  OOD gate silently exactly where the transfer fails"), which is the right worry
  and has no proposed remedy.

**The tool the project has not named is conformal prediction** (Vovk,
Gammerman & Shafer 2005; Angelopoulos & Bates 2021), which gives
distribution-free, finite-sample-valid prediction intervals from a calibration
set. Its assumption is exchangeability, and here the assumption fails in two
*known* ways, which is the useful part:

| failure | already measured as | the conformal variant that handles it |
|---|---|---|
| rows within a trajectory are correlated | ICC 0.22–0.70 (**T-05**) | block / cluster conformal — calibrate over **trajectories** [assumed; e.g. the block-conformal methods of Chernozhukov, Wüthrich & Zhu 2018, not opened here] |
| the deployment measure ≠ the training measure | §IV.3, **R-07**, **T-13** | **weighted** conformal (Tibshirani et al. 2019), which needs the likelihood ratio between the two measures — its covariate-shift form assumes P(Y\|X) unchanged, true for a deterministic emulator target |

The second row is the striking one: **weighted conformal prediction requires
exactly the density ratio that R-07 / T-13 set out to measure.** A sampling-
measure study filed under "is the Sobol grid representative?" turns out to be the
input to a principled UQ method. Two open items that looked unrelated are the same
measurement.

**And there is a cheap alternative the project owns and has not connected to
S22.** It already computes several *physics residuals* that require no ensemble
and cost essentially nothing:

- the **entropy-production sign** check (Tier 2 **R-05**: a learned φ̂ can violate
  the second law and pass every current gate);
- the **energy-consistency** residual between the flux route and the composition
  route;
- **positivity** violations (**R-04**);
- the **fixed-point distance** of §X.1.

Each is a scalar, deterministic, single-forward-pass validity score derived from
physics rather than from statistics — which is precisely the "cheap UQ" that Tier
2 §0.5b argues is structurally preferred on economic grounds. **The project has
been building OOD scores for two tiers without labelling them as such.**
Registered as **T-37**, and it is a reframing rather than a new measurement.

## X.6 Rates as inputs — the capability nobody claimed

A design question with a scientific payoff, unasked.

The emulator's inputs are (T, ρ, X). The *rates* are baked into the weights.
Suppose instead the model took a low-dimensional rate-perturbation vector θ —
multipliers on a chosen set of channels, or a categorical selector over weak-rate
library families (FFN / Oda / LMP). Then autodiff gives

$$
\frac{\partial X'}{\partial \theta}, \qquad \frac{\partial Y_e'}{\partial \theta}
$$

**for free, at inference time.** That is exactly §IX.3.3's rate-uncertainty →
Yₑ propagation — currently a day of compute per study — reduced to a
milliseconds-per-state gradient evaluation, and it is the kind of thing surrogate
models are uniquely good for.

**Honest assessment of the cost.** Training data would have to *vary* the rates,
which means regenerating labels under perturbed rate sets. For a full continuous
θ that is prohibitive. But two restricted versions are affordable and useful:

- **A categorical library selector** with 2–3 values (the FFN/LMP pair being the
  obvious one, since that shift *is* the project's accuracy floor, §0.6.6 row 4).
  This costs one extra label campaign per library and would let a user ask "how
  much of my Yₑ is the rate library?" directly.
- **A handful of scalar multipliers on the top-20 Yₑ carriers** (§0.7.3), which
  are few, identified, and dominate the budget.

Whether to do this in Phase 1 is a scope call and probably "no". Whether to *say*
it is a scope call is not — because it changes what the artifact is **for**:
from "a fast network" to "a differentiable model of the network's dependence on
its own inputs". That is a stronger scientific product and it is not in any plan.
Registered as **T-38**.

## X.7 Which Δt does the host actually use?

The emulator is trained on nine values spanning 10⁻⁶ … 10² s, inherited from the
NNN's grid, which its authors chose to bracket the timesteps of their three MESA
test-case tracks (Grichener et al. 2025 §2.2 and Fig. 1) and extended "several
orders of magnitude" below them "which might be needed for hydrodynamical
simulations". **Nobody has measured the distribution of Δt that MESA actually
takes during silicon burning** — the paper's Fig. 1 is three tracks, not a
per-phase histogram.

If the host spends most of its steps in 10⁻² … 10⁰ s, then three of the nine
decades are training capacity spent on regions never visited, and the extrapolation
risk lives at a different end of the grid than assumed. If the host takes steps
*shorter* than 10⁻⁶ s — the NNN authors say the grid's low end already lies
below MESA's steps, so this would need a hydrodynamic phase — the emulator is
being extrapolated from its first step, and §III.1's finding that even the shortest
label is a full stiff relaxation acquires a sharper edge.

**This is the same MESA run as T-24**, so it is free once that profiling exists:
histogram `dt` by evolutionary phase alongside the `net` timing. Registered as
**T-39**, and it should be done in the same afternoon.

## X.8 Sample complexity — a million points in 82 dimensions

A framing that the project's own measurements make sharp, and that nothing states.

The training corpus is ~10⁶ states per network, with inputs of dimension
n + 2 = 82 / 153. The naive covering estimate for a smooth function on a d-
dimensional set at resolution ε is ε^{−d} samples; at d = 82 the number is not
worth writing down. **Uniform coverage is not merely infeasible, it is absurd by
seventy orders of magnitude.**

The reason it can nonetheless work is that the *deployment* set is much smaller
than the input space: **R-02** measures the effective dimension of visited
compositions at 3.4 / 8.6. At d = 8.6 and ε = 0.1 the covering estimate is
~10^{8.6} ≈ 4 × 10⁸ — still **two to three orders above the corpus**, though this
is a worst-case bound that smoothness and the map's near-projection structure
(§X.2) both improve substantially.

But the real point is a *capacity allocation* argument, distinct from the
distribution-shift argument of §IV.3 and, as far as these notes can tell, not made
anywhere:

> The training compositions are **random**, hence spread over the full high-
> dimensional simplex. The deployment compositions lie on a ~3–9 dimensional
> manifold. So the model spends the overwhelming majority of its capacity, and of
> the corpus, learning behaviour on states it will never be asked about — while
> the manifold it *will* be asked about is covered by whatever small fraction of
> the corpus happens to lie near it.

That is an argument for trajectory-derived training data on grounds of **sample
efficiency**, independent of whether the distributions match. It also predicts
that a modest number of on-manifold states could be worth a great many
off-manifold ones — which, if true, makes the 10³–10⁴-state Φ-label budget of
§V.4 look much less like a compromise and much more like the right design.
Registered as **T-40**.

## X.9 Two smaller ones

**Network switching mid-run.** MESA can change nets during an evolution
(`star_job` `change_net` / `new_net_name`, r23.05.1 `star_job.defaults:2364`; a
star does not need an iron-peak network during hydrogen burning). An emulator trained
on `mesa_80` has nothing to say about the step at which the host switches nets,
and the composition must be mapped between species lists at that point. Minor,
but it is a real code path and it interacts with the size-transfer story. Folded
into **T-32**.

**Licensing, attribution, and data reuse.** The project redistributes nothing but
depends on Zenodo 14873443 (someone else's data and trained models), MESA, bbq
and pynucastro, and will publish a head-to-head comparison against the NNN using
the NNN authors' own shipped artifacts. The licence terms, the citation
obligations, and the norms around benchmarking someone's published model with
their own weights are a genuine publication prerequisite that appears in no
document. It is half an hour of checking and it is the kind of thing that is
embarrassing rather than fatal — which is exactly why it gets skipped. Folded
into **T-32**.

## X.10 One unretired premise, found while sweeping

Not an area, but a finding, and it is the same *class* as the "6–8 orders"
timescale figure that §IV.7 retired.

`docs/reports/consolidated-gnn-architecture.md` §1 states, as inherited design
basis:

> "the net flow between the silicon and iron-peak groups is carried predominantly
> by the single bottleneck reaction **⁴⁵Sc(p,γ)⁴⁶Ti** (**≈75% of the flow** at
> the proton-rich Z = 21 edge), which is therefore the reaction whose flux the
> Phase-0 kill-test instruments."

The measurement **[RESULTS]** 2026-07-12 says: ⁴⁵Sc(p,γ)⁴⁶Ti is **rank 2 of 251**
inter-group carriers (mesa_151) with **share 0.10–0.12** under the `a24_46`
boundary on the full relaxed manifold (0.094 on the 2026-07-10 pre-stall high-Yₑ
QSE-window subset), and the **top-20 columns carry 0.88** (the mesa_80 bridge
figure, RESULTS 2026-07-12).

Both the verdict document and §0.3.2 of this file report that as **CONFIRMED** —
and it is, as a confirmation that the reaction is a leading carrier, which is a
genuine and pleasing independent recovery of a literature claim. But **the
magnitude the design leaned on is off by a factor of six or seven**, and nothing
retires it. "Predominantly carried by a single reaction" and "top-20 carry 0.88,
of which the leader has 0.11" are different physical pictures, and they imply
different architectures: the first justifies a bottleneck-focused design, the
second justifies exactly the concentrated-but-not-singular loss weighting the
project actually adopted.

Three things should happen: pin the 75% figure to what it actually measures — it
*is* sourced (Woosley, Arnett & Clayton 1973, via Hix & Thielemann 1996: WAC
"contended that this linkage was dominated by a single reaction, ⁴⁵Sc(p,γ)⁴⁶Ti,
with perhaps a quarter of the flow going through less important reactions"; Hix &
Thielemann 1996's own value is ≈70% of the flux *into the iron-peak group* at
T₉ = 5, ρ = 10⁷, Yₑ = 0.498, integrated while X(Si group) falls 0.95 → 0.85), but
it is a different quantity at a different state from "share of all inter-group
carriers on the relaxed manifold under `a24_46`"; retire the transplanted magnitude
in `RESULTS.md` with the measured replacement, exactly as the timescale figure was
retired; and audit the remaining inherited design premises for others of the same
kind. The two found so far share a pattern worth naming: **a magnitude attached to
a correct qualitative claim, either unsourced (the 6–8 orders) or sourced for a
different quantity and state (the 75%)** (corrected in the 2026-08-18 audit).
Registered as **T-41**, and it is a `referee`-subagent task.

## X.11 Is the audit converging *now*?

Better than after pass 3, and the reason is the shape of the yield rather than
its size.

**Pass 3** (Part IX) found ten areas spread across four axes: physics-adjacent
(mixing), setting (progenitors, NSE handoff, explodability), interface (four
items), and practice (three items). Spread means *not localised* means *not
converging*.

**This pass** found ten items of which **nine sit in one place**: the emulator
considered as a dynamical system (§X.1, X.2, X.4, X.8), and its coupling to a
host solver (§X.3, X.5, X.6, X.7). The tenth (§X.10) is a documentation finding,
not an area. That is what localisation looks like, and it supports a specific
prediction:

> **The remaining unexplored prerequisite is essentially one subject: the theory
> and practice of a learned flow map — its fixed points, its spectrum, its
> conditioning symmetries, its calibration, and the numerics of embedding it in
> an implicit solver.** That is a Tier-4 Part 0, and it is exactly the "no study
> node at all" gap `tier1.md` §VIII.E.1 identified from the architecture side.

Two further observations that make the convergence claim honest rather than
convenient:

- **Diminishing novelty, not diminishing count.** This pass found as many items
  as the last, but they are far more homogeneous, and four of them (§X.1, X.2,
  X.5, X.8) are *reframings of things already measured* rather than new
  territory: the fixed-point census is §III's method aimed at a model; the
  spectral test is stiffness seen through the flow map; conformal weighting needs
  R-07's density ratio; sample complexity needs R-02's effective dimension. **The
  project increasingly already owns the inputs to its own open questions.**
- **The one thing that would genuinely change the picture is having an artifact.**
  Every item in §X.1–X.5 is a measurement *of a trained model*, and none can be
  run before one exists. So the correct reading is not "keep auditing" but
  "the audit has identified what to measure the moment there is something to
  measure, and that list should be a gate on the first training run rather than a
  retrospective."

**The recommendation the two passes converge on**, stated once: *before the first
training run, write the Tier-4 Part 0 and the measurement plan it implies.*
Sections §X.1–X.5 and Tier 2's **R-03**, **R-05**, **R-13**, **R-21**, **R-24**
are its contents; four of the eight open Phase-0 checklist rows are its
measurements; and two of the four architecture components have retired premises
waiting there (§VII.2).

---

# Where Tier 3 hands off

Tier 0 gave the substrate, Tier 1 the microphysics, Tier 2 the algebra, Tier 3
the astrophysics and the verdict. What remains is **Tier 4 — the emulator**, which
has no study node at all (`tier1.md` §VIII.E.1 sketches S17–S22).

It inherits a decided target, a conservation map that provably costs nothing, a
loss-weighting map, two architecture components whose stated premises have been
retired by measurement, an unmeasured accumulation slope that moves the operative
gate by 100×, an undeclared validity domain, and a training distribution that is
measurably not the deployment distribution.

That is a good position to be in. Every one of those is *known*, and every one was
found before a single model was trained.


---

# References

Sources verified during the 2026-08-18 literature audit (inline author-year
citations in the text point here). Cite the papers, never any local snapshot:
arXiv-available papers were verified against their arXiv TeX sources (fetched
via `scripts/fetch_arxiv_source.py` into the ephemeral `data/literature/`
cache at audit time); pre-arXiv papers were read from the ADS scanned
originals during the 2026-08-14 (tier 2) audit where so noted, or verified
through the secondary sources named in their provenance notes. ADS abstract
pages were unreachable this session, so bibliographic data for pre-arXiv and
uncached papers came from CrossRef (DOI lookups), INSPIRE, or the cached
bibliographies (`.bbl`/`refs.bib`) of the arXiv sources named in each note.
Nuclear data were checked against AME2020/NUBASE2020 and ENSDF via the IAEA
Live Chart and NNDC. Provenance notes distinguish "verified against arXiv TeX"
(content read) from "bibliographic data only; content ASSUMED-with-attribution"
(the paper is the standard citation for the claim but was not opened here).

- Adelberger, E. G., García, A., Robertson, R. G. H., et al. 2011, "Solar fusion cross sections. II. The pp chain and CNO cycles", Rev. Mod. Phys. 83, 195. arXiv:1004.2318. (Gamow-peak formalism E₀/kT and exp(−3E₀/kT) verified against arXiv TeX `SolarFusionII.tex:648–672`; vol/page from CrossRef DOI 10.1103/RevModPhys.83.195.)
- Aitchison, J. 1982, "The Statistical Analysis of Compositional Data", J. R. Stat. Soc. B 44, 139. (Bibliographic data from CrossRef DOI 10.1111/j.2517-6161.1982.tb01195.x; content textbook-standard, mathematics recomputed here — ASSUMED-with-attribution.)
- Aitchison, J. 1986, *The Statistical Analysis of Compositional Data* (Chapman & Hall). (Textbook; CrossRef DOI 10.1007/978-94-009-4109-0.)
- Alekseev, E. N., Alekseeva, L. N., Krivosheina, I. V. & Volchenko, V. I. 1988, "Detection of the neutrino signal from SN 1987A in the LMC using the INR Baksan underground scintillation telescope", Phys. Lett. B 205, 209. (Pre-arXiv; bibliographic data from CrossRef DOI 10.1016/0370-2693(88)91651-6, where the authors are transliterated "Alexeyev"; event count not verified from the abstract — secondary via Janka 2017.)
- Amdahl, G. M. 1967, "Validity of the single processor approach to achieving large scale computing capabilities", AFIPS Conf. Proc. 30 (SJCC), 483. (Bibliographic data from CrossRef DOI 10.1145/1465482.1465560; content textbook-standard — ASSUMED-with-attribution.)
- Angelopoulos, A. N. & Bates, S. 2021, "A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification", arXiv:2107.07511; published as "Conformal Prediction: A Gentle Introduction", Found. Trends Mach. Learn. 16, 494 (2023). (Distribution-free / exchangeability statements verified against arXiv TeX `main.tex:137, 253`; journal vol/page from CrossRef DOI 10.1561/2200000101; the text cites the 2021 arXiv version.)
- Arnett, W. D. 1982, "Type I Supernovae. I. Analytic Solutions for the Early Part of the Light Curve", ApJ 253, 785. (Pre-arXiv; rule and attribution verified via ADS and Lyman et al. 2016 in the 2026-08-14 audit (tier2); vol/page re-confirmed via CrossRef DOI 10.1086/159681.)
- Arnett, W. D., Bahcall, J. N., Kirshner, R. P. & Woosley, S. E. 1989, "Supernova 1987A", ARA&A 27, 629. (Pre-arXiv; bibliographic data from CrossRef DOI 10.1146/annurev.aa.27.090189.003213; the 20 M⊙ burning-stage table is quoted secondhand from Odrzywolek et al. 2004 Table 2 — content ASSUMED-with-attribution.)
- Bader, G. & Deuflhard, P. 1983, "A semi-implicit mid-point rule for stiff systems of ordinary differential equations", Numer. Math. 41, 373. (Cited by MESA VI (Jermyn et al. 2023 `rates.tex`) for the `op_split_burn` integrator; bibliographic data from CrossRef DOI 10.1007/BF01418331; content not opened.)
- Baron, E. & Cooperstein, J. 1990, "The effect of iron core structure on supernovae", ApJ 353, 597. (Pre-arXiv; bibliographic data from Suwa et al. 2018 `ns_minimum.bbl:24–27` and CrossRef DOI 10.1086/168649; origin of the electron-entropy correction to M_Ch, cited via Timmes, Woosley & Weaver 1996 and Suwa et al. 2018 — content ASSUMED-with-attribution.)
- Battaglia, P. W., Hamrick, J. B., Bapst, V., et al. 2018, "Relational inductive biases, deep learning, and graph networks", arXiv:1806.01261. (arXiv preprint only; TeX cached, not quoted.)
- bbq (R. Farmer), github.com/rjfarmer/bbq, commit 9783df31 (2023-08-29). Files cited: `src/main.f90`, `src/lib_bbq.f90:439, 453` (single `net_1_zone_burn` path, no NSE code), `src/lib_profile.f90`, `src/lib_hydrostatic.f90:115`, `defaults/bbq.defaults`, `defaults/nuclear.defaults`. (Local clone.)
- Beard, D. A. & Qian, H. 2007, "Relationship between Thermodynamic Driving Force and One-Way Fluxes in Reversible Processes", PLoS ONE 2, e144. arXiv:q-bio/0607020. (Exponential flux-force relation and sign statement only; the tanh form of §II.4 is not in this paper.)
- Bethe, H. A. & Wilson, J. R. 1985, "Revival of a stalled supernova shock by neutrino heating", ApJ 295, 14. (Pre-arXiv; bibliographic data from CrossRef DOI 10.1086/163343 and the Janka et al. 2007 / Janka 2012 bibliographies; content cited secondarily via those reviews — ASSUMED-with-attribution.)
- Bethe, H. A. 1990, "Supernova Mechanisms", Rev. Mod. Phys. 62, 801. (Pre-arXiv; full text read during the audit — quotes trapped *lepton* fraction Y_L ≈ 0.36–0.39, not the modern Yₑ values, see §0.3.2.) (Read from the ADS scan in the 2026-08-14 audit (tier2); ADS unreachable this session, bibliographic data re-confirmed via the Janka et al. 2007 bibliography `Jankaetal-astroph.tex:2688`.)
- Beucler, T., Pritchard, M., Rasp, S., Ott, J., Baldi, P. & Gentine, P. 2021, "Enforcing Analytic Constraints in Neural Networks Emulating Physical Systems", Phys. Rev. Lett. 126, 098302. arXiv:1909.00912. (Verified against arXiv TeX; journal ref from meta.xml, confirmed via CrossRef DOI 10.1103/PhysRevLett.126.098302.)
- Bionta, R. M., Blewitt, G., Bratton, C. B., et al. 1987, "Observation of a Neutrino Burst in Coincidence with Supernova 1987A in the Large Magellanic Cloud", Phys. Rev. Lett. 58, 1494. (Pre-arXiv; abstract via INSPIRE/APS: "eight neutrino events … six seconds … 20–40 MeV"; vol/page confirmed via CrossRef DOI 10.1103/PhysRevLett.58.1494.)
- Blondin, J. M., Mezzacappa, A. & DeMarino, C. 2003, "Stability of Standing Accretion Shocks, with an Eye toward Core-Collapse Supernovae", ApJ 584, 971. arXiv:astro-ph/0210634. (Verified against arXiv TeX abstract; journal ref from meta.xml, confirmed via CrossRef DOI 10.1086/345812.)
- Boccioli, L. & Roberti, L. 2024, "The Physics of Core-Collapse Supernovae: Explosion Mechanism and Explosive Nucleosynthesis", Universe 10, 148. arXiv:2403.12942. (Verified against arXiv TeX `main.tex:291, 504–556` — note its explosive-burning thresholds are NOT hydrostatic ignition temperatures; journal ref from meta.xml, confirmed via CrossRef DOI 10.3390/universe10030148.)
- Bodansky, D., Clayton, D. D. & Fowler, W. A. 1968, "Nuclear Quasi-Equilibrium during Silicon Burning", ApJS 16, 299 (BCF68). (Pre-arXiv; read from the ADS scan — describes a *single* quasi-equilibrium group, 28 ≤ A ≤ 62, see §0.1.2.) (Read from the ADS scan in the 2026-08-14 audit (tier2); single-group content re-verified secondarily via HT96 `9511088.tex:203–213`.)
- Boggs, S. E., Harrison, F. A., Miyasaka, H., et al. 2015, "⁴⁴Ti gamma-ray emission lines from SN1987A reveal an asymmetric explosion", Science 348, 670. (Uncached, no arXiv TeX; abstract via CrossRef/Semantic Scholar DOI 10.1126/science.aaa2259.)
- Brandstetter, J., Worrall, D. & Welling, M. 2022, "Message Passing Neural PDE Solvers", ICLR 2022. arXiv:2202.03376. (Verified against arXiv TeX; venue from the meta.xml comment "Published at ICLR 2022"; not indexed in CrossRef.)
- Burrows, A. & Goshy, J. 1993, "A Theory of Supernova Explosions", ApJ 416, L75. (Pre-arXiv; critical-luminosity concept cited secondarily via Pejcha & Thompson 2015 `:93`; bibliographic data from CrossRef DOI 10.1086/187074 — content ASSUMED-with-attribution.)
- Burrows, A., Hayes, J. & Fryxell, B. A. 1995, "On the Nature of Core-Collapse Supernova Explosions", ApJ 450, 830. (Pre-arXiv; cited secondarily via Janka et al. 2007 `Jankaetal-astroph.tex:2877–2878`; title/vol/page from CrossRef DOI 10.1086/176188.)
- Burrows, A. & Vartanyan, D. 2021, "Core-collapse supernova explosion theory", Nature 589, 29. arXiv:2009.14157. (Verified against arXiv TeX; journal ref from meta.xml, confirmed via CrossRef DOI 10.1038/s41586-020-03059-w.)
- Calder, A. C., Townsley, D. M., Seitenzahl, I. R., et al. 2007, "Capturing the Fire: Flame Energetics and Neutronization for Type Ia Supernova Simulations", ApJ 656, 313. arXiv:astro-ph/0611009. (Uncached; named only as an example of a code that switches to an NSE solver; bibliographic data from CrossRef DOI 10.1086/510709 — content ASSUMED-with-attribution.)
- Cameron, A. C. & Miller, D. L. 2015, "A Practitioner's Guide to Cluster-Robust Inference", J. Human Resources 50, 317.
- Chabrier, G. & Potekhin, A. Y. 1998, "Equation of state of fully ionized electron-ion plasmas", Phys. Rev. E 58, 4941. arXiv:physics/9807042. (Verified against arXiv TeX `cp98e.tex:143–156`; journal ref from meta.xml, confirmed via CrossRef DOI 10.1103/PhysRevE.58.4941.)
- Chandrasekhar, S. 1931, "The Maximum Mass of Ideal White Dwarfs", ApJ 74, 81. (Pre-arXiv.)
- Chandrasekhar, S. 1939, *An Introduction to the Study of Stellar Structure* (University of Chicago Press).
- Chandrasekhar, S. 1964, "The Dynamical Instability of Gaseous Masses Approaching the Schwarzschild Limit in General Relativity", ApJ 140, 417. (Pre-arXiv; the GR correction to Γ_crit = 4/3; bibliographic data from CrossRef DOI 10.1086/147938 — content ASSUMED-with-attribution.)
- Chernozhukov, V., Wüthrich, K. & Zhu, Y. 2018, "Exact and robust conformal inference methods for predictive machine learning with dependent data", Proc. Machine Learning Research 75 (COLT 2018), 732. arXiv:1802.06300. (Uncached; block/cluster conformal for dependent data; CrossRef lists only the CeMMAP working-paper DOI 10.1920/wp.cem.2018.1618 — PMLR vol/page from memory, not verified; content ASSUMED-with-attribution.)
- Chugunov, A. I., DeWitt, H. E. & Yakovlev, D. G. 2007, "Coulomb tunneling for fusion reactions in dense matter: Path integral Monte Carlo versus mean field", Phys. Rev. D 76, 025028. arXiv:0707.3500. (Bibliographic data from meta.xml, confirmed via CrossRef DOI 10.1103/PhysRevD.76.025028; MESA `screen_chugunov.f90:26` and pynucastro `chugunov_2007` cite it; content not read.)
- Clayton, D. D. 1968, *Principles of Stellar Evolution and Nucleosynthesis* (McGraw-Hill; University of Chicago Press reprint 1983). (Textbook; §4-3 Gamow peak, §5 neutrino losses, Ch. 2 hydrostatic/virial estimates — section numbers from memory.)
- Clifford, F. E. & Tayler, R. J. 1965, "The Equilibrium Distribution of Nuclides in Matter at High Temperatures", Mem. RAS 69, 21. (Pre-arXiv, not opened — cited via the attributions in BCF68 and Hix & Thielemann 1999b.)
- Colgate, S. A. & White, R. H. 1966, "The Hydrodynamic Behavior of Supernovae Explosions", ApJ 143, 626. (Pre-arXiv; origin of the neutrino-driven explosion idea, cited via Janka et al. 2007 / Janka 2012; title/vol/page from CrossRef DOI 10.1086/148549 — content ASSUMED-with-attribution.)
- Collins, C., Müller, B. & Heger, A. 2018, "Properties of convective oxygen and silicon burning shells in supernova progenitors", MNRAS 473, 1695. arXiv:1712.09400. (Uncached; 1D shell-merger survey; CrossRef DOI 10.1093/mnras/stx2470 confirms title/journal but returned no vol/page — vol/page from the verifier report, not verified; content ASSUMED-with-attribution.)
- Couch, S. M., Chatzopoulos, E., Arnett, W. D. & Timmes, F. X. 2015, "The Three-dimensional Evolution to Core Collapse of a Massive Star", ApJ 808, L21. arXiv:1503.02199. (Verified against arXiv TeX `ms.tex:243`; vol/page from CrossRef DOI 10.1088/2041-8205/808/1/L21.)
- Couch, S. M., Warren, M. L. & O'Connor, E. P. 2020, "Simulating Turbulence-aided Neutrino-driven Core-collapse Supernova Explosions in One Dimension", ApJ 890, 127. arXiv:1902.01340. (Verified against arXiv TeX; vol/page from CrossRef DOI 10.3847/1538-4357/ab609e — meta.xml carries the DOI only.)
- Cyburt, R. H., Amthor, A. M., Ferguson, R., et al. 2010, "The JINA REACLIB Database: Its Recent Updates and Impact on Type-I X-ray Bursts", ApJS 189, 240. (Bibliographic data from CrossRef DOI 10.1088/0067-0049/189/1/240 (cached `web/cyburt2010.md`); REACLIB format from `web/reaclib-format.md`.)
- Davison, A. C. & Hinkley, D. V. 1997, *Bootstrap Methods and their Application* (Cambridge University Press), §3.8.
- Diehl, R., Siegert, T., Hillebrandt, W., et al. 2015, "SN2014J gamma rays from the ⁵⁶Ni decay chain", A&A 574, A72. arXiv:1409.5477. (Verified against arXiv TeX `SN2014J_56Co_revised_astroph.tex:131` for the chain mean lives only; journal ref from CrossRef DOI 10.1051/0004-6361/201424991.)
- Egozcue, J. J., Pawlowsky-Glahn, V., Mateu-Figueras, G. & Barceló-Vidal, C. 2003, "Isometric Logratio Transformations for Compositional Data Analysis", Math. Geol. 35, 279. (Bibliographic data from CrossRef DOI 10.1023/A:1023818214614; content textbook-standard — ASSUMED-with-attribution.)
- ENSDF — Evaluated Nuclear Structure Data File, National Nuclear Data Center, Brookhaven National Laboratory. (A = 56 chain: Huo Junde, Huo Su & Yang Dong 2011, Nucl. Data Sheets 112, 1513; accessed via the IAEA Live Chart API, 2026-08-14 and re-retrieved 2026-08-18: ⁵⁶Ni T½ 6.075(10) d, EC+β⁺ 100 %, Q_EC 2132.9 keV; ⁵⁶Co T½ 77.236(26) d, β⁺ 19.7 %, EC 80.3 %, Q 4566.6 keV; ⁵⁷Ni 35.60 h; ⁵⁷Co 271.74 d, EC 100 %; ⁴⁴Ti 59.1(3) y, EC 100 %.)
- Ertl, T., Janka, H.-T., Woosley, S. E., Sukhbold, T. & Ugliano, M. 2016, "A Two-parameter Criterion for Classifying the Explodability of Massive Stars by the Neutrino-driven Mechanism", ApJ 818, 124. arXiv:1503.07522. (Verified against arXiv TeX; vol/page from CrossRef DOI 10.3847/0004-637X/818/2/124.)
- Fan, D., Willcox, D. E., DeGrendele, C., Zingale, M. & Nonaka, A. 2022, "Neural Networks for Nuclear Reactions in MAESTROeX", ApJ 940, 134. arXiv:2202.09348. (Uncached; bibliographic data from the NNN and NuGNN bibliographies (`main.bbl:91–92`, `Eq_Solver.tex`) and CrossRef DOI 10.3847/1538-4357/ac9a4b; content ASSUMED-with-attribution — 3-isotope MAESTROeX emulator per NuGNN's description.)
- Farmer, R., Fields, C. E., Petermann, I., et al. 2016, "On Variations of Pre-supernova Model Properties", ApJS 227, 22. arXiv:1611.01207. (Verified against arXiv TeX `paper.tex:1611–1612`; vol/page from the NNN `refs.bib:110–125` and CrossRef DOI 10.3847/1538-4365/227/2/22.)
- Fesen, R. A., Hammell, M. C., Morse, J., et al. 2006, "The Expansion Asymmetry and Age of the Cassiopeia A Supernova Remnant", ApJ 645, 283. arXiv:astro-ph/0603371. (Uncached; abstract via CrossRef/Semantic Scholar DOI 10.1086/504254 — convergence date 1681 ± 19.)
- Fewell, M. P. 1995, "The atomic nuclide with the highest mean binding energy", Am. J. Phys. 63, 653. (Bibliographic data from CrossRef DOI 10.1119/1.17828; the ⁶²Ni-vs-⁵⁶Fe point re-derived here from AME2020 — content ASSUMED-with-attribution.)
- Field, C. A. & Welsh, A. H. 2007, "Bootstrapping Clustered Data", J. R. Stat. Soc. B 69, 369.
- Fields, C. E., Timmes, F. X., Farmer, R., et al. 2018, "The Impact of Nuclear Reaction Rate Uncertainties on the Evolution of Core-collapse Supernova Progenitors", ApJS 234, 19. arXiv:1712.06057. (Uncached; bibliographic data from CrossRef DOI 10.3847/1538-4365/aaa29b; content ASSUMED-with-attribution.)
- Fowler, W. A. & Hoyle, F. 1964, "Neutrino Processes and Pair Formation in Massive Stars and Supernovae", ApJS 9, 201. (Pre-arXiv; bibliographic data from CrossRef DOI 10.1086/190103; pair-emissivity limits ∝ T⁹ and T₉³ e^{−11.86/T₉} are textbook-standard — content ASSUMED-with-attribution.)
- Freedman, D. Z. 1974, "Coherent effects of a weak neutral current", Phys. Rev. D 9, 1389. (Pre-arXiv; vol/page from the Langanke & Martínez-Pinedo 2003 `.bbl:4741–4744`; title confirmed via CrossRef DOI 10.1103/PhysRevD.9.1389; content ASSUMED-with-attribution.)
- Fuller, G. M., Fowler, W. A. & Newman, M. J. 1980, "Stellar weak-interaction rates for sd-shell nuclei", ApJS 42, 447 (FFN). (Pre-arXiv; citation set verified via Heger et al. 2001's bibliography.)
- Fuller, G. M., Fowler, W. A. & Newman, M. J. 1982a, "Stellar weak interaction rates for intermediate-mass nuclei. II. A = 21 to A = 60", ApJ 252, 715 (FFN). (Pre-arXiv; bibliographic data from the Langanke & Martínez-Pinedo 2003 `.bbl:4879–4912`, confirmed via CrossRef DOI 10.1086/159597; content not opened.)
- Fuller, G. M., Fowler, W. A. & Newman, M. J. 1982b, "Stellar weak interaction rates for intermediate mass nuclei. III. Rate tables for the free nucleons and nuclei with A = 21 to A = 60", ApJS 48, 279 (FFN). (Pre-arXiv; as above, CrossRef DOI 10.1086/190779.)
- Fuller, G. M., Fowler, W. A. & Newman, M. J. 1985, "Stellar weak interaction rates for intermediate-mass nuclei. IV", ApJ 293, 1 (FFN). (Pre-arXiv; as above.) (Also the attribution printed in the MESA `weakreactions.tables` header.)
- Gilmer, J., Schoenholz, S. S., Riley, P. F., Vinyals, O. & Dahl, G. E. 2017, "Neural Message Passing for Quantum Chemistry", Proc. 34th Int. Conf. Machine Learning (ICML), PMLR 70, 1263. arXiv:1704.01212. (Verified against arXiv TeX; venue/PMLR vol/page from memory — not indexed in CrossRef, journal ref not verified.)
- Goldreich, P. & Weber, S. V. 1980, "Homologously Collapsing Stellar Cores", ApJ 238, 991. (Pre-arXiv.) (Bibliographic data re-confirmed via the Janka et al. 2007 bibliography `Jankaetal-astroph.tex:2706–2707`.)
- Golub, G. H. & Van Loan, C. F. 2013, *Matrix Computations* (4th ed.; Johns Hopkins University Press). (Textbook; dense LU cost ≈ 2n³/3 flops.)
- Grefenstette, B. W., Harrison, F. A., Boggs, S. E., et al. 2014, "Asymmetries in core-collapse supernovae from maps of radioactive ⁴⁴Ti in Cassiopeia A", Nature 506, 339. arXiv:1403.4978. (PDF-only cache; abstract verified at arxiv.org/abs/1403.4978; journal ref from meta.xml, confirmed via CrossRef DOI 10.1038/nature12997.)
- Grichener, A., Renzo, M., Kerzendorf, W. E., et al. 2025, "Nuclear Neural Networks: Emulating Late Burning Stages in Core-collapse Supernova Progenitors", ApJS 279, 49 (NNN). arXiv:2503.00115. (Volume/page confirmed via Kim et al. 2026's bibliography; the arXiv source predates final assignment.) (Re-confirmed via CrossRef DOI 10.3847/1538-4365/ade717 (vol 279, article 49, 2025-08-01); author order Grichener, Renzo, Kerzendorf, Farmer, de Mink, Bellinger, Chan, Chen, Farag, Justham per `main.tex:76–113`; data and models: Zenodo 10.5281/zenodo.14873443; §2.2 Sobol sampling, Appendix B MESA rate bug, and the log-softmax/L1-on-log loss verified against arXiv TeX `main.tex:190, 229, 238`.)
- Guidry, M. W. 2012, "Algebraic Stabilization of Explicit Numerical Integration for Extremely Stiff Reaction Networks", J. Comp. Phys. 231, 5266. arXiv:1112.4778. (10–20-order stiffness ratio verified against arXiv TeX `jcp.tex:239–240`; journal ref from meta.xml.)
- Guidry, M. W., Billings, J. J. & Hix, W. R. 2013, "Explicit Integration of Extremely-Stiff Reaction Networks: Partial Equilibrium Methods", Comput. Sci. Disc. 6, 015003. arXiv:1112.4738. (Source of the |y − ȳ|/ȳ < ε departure criterion, their eq. 8b, ε = 0.01.) (Criterion, ε = 0.01 and the "6–8 orders" sentence re-verified against arXiv TeX `peCSD.tex:696–704, 2479, 2806, 3279`.)
- Guidry, M. W., Budiardja, R., Feger, E., et al. 2013, "Explicit Integration of Extremely-Stiff Reaction Networks: Asymptotic Methods", Comput. Sci. Disc. 6, 015001. arXiv:1112.4716.
- Hairer, E. & Wanner, G. 1996, *Solving Ordinary Differential Equations II: Stiff and Differential-Algebraic Problems* (2nd ed.; Springer).
- Hartmann, D., Woosley, S. E. & El Eid, M. F. 1985, "Nucleosynthesis in Neutron-rich Supernova Ejecta", ApJ 297, 837 (HWE85). (Pre-arXiv; Fig. 2 read from the ADS scan.) (Read from the ADS scan in the 2026-08-14 audit (tier2).)
- Heger, A., Langer, N. & Woosley, S. E. 2000, "Presupernova Evolution of Rotating Massive Stars. I. Numerical Method and Evolution of the Internal Stellar Structure", ApJ 528, 368 (HLW00). arXiv:astro-ph/9904132. (Uncached; cited secondarily via Heger et al. 2003 `23.tex:965–970` for rotation enlarging He cores; bibliographic data from CrossRef DOI 10.1086/308158 — content ASSUMED-with-attribution.)
- Heger, A., Woosley, S. E., Martínez-Pinedo, G. & Langanke, K. 2001, "Presupernova Evolution with Improved Rates for Weak Interactions", ApJ 560, 307. arXiv:astro-ph/0011507. (Source of the FFN→LMP shift ΔYₑ = 0.005–0.015; PRL companion: Heger et al. 2001, Phys. Rev. Lett. 86, 1678, arXiv:astro-ph/0007412.) (Re-verified against arXiv TeX `apj.tex:414–420`: the ΔYₑ = 0.005–0.015 shift is relative to WW95 and about half of it is the inclusion of β-decays; M_Ch ≃ 5.83 Yₑ² at `apj.tex:1019`; vol/page also in the Langanke & Martínez-Pinedo 2003 `.bbl:5214–5220`.)
- Heger, A., Fryer, C. L., Woosley, S. E., Langer, N. & Hartmann, D. H. 2003, "How Massive Single Stars End their Life", ApJ 591, 288. arXiv:astro-ph/0212469. (Verified against arXiv TeX `23.tex:353–361, 965–980`; journal ref from meta.xml, confirmed via CrossRef DOI 10.1086/375341.)
- Herant, M., Benz, W., Hix, W. R., Fryer, C. L. & Colgate, S. A. 1994, "Inside the supernova: A powerful convective engine", ApJ 435, 339. (Pre-arXiv; cited secondarily via Janka et al. 2007 `Jankaetal-astroph.tex:2874–2875`; title/vol/page from CrossRef DOI 10.1086/174817.)
- Hirata, K., Kajita, T., Koshiba, M., et al. 1987, "Observation of a Neutrino Burst from the Supernova SN1987A", Phys. Rev. Lett. 58, 1490. (Pre-arXiv; abstract via INSPIRE/APS: "11 electron events of energy 7.5 to 36 MeV" over "13 sec"; vol/page confirmed via CrossRef DOI 10.1103/PhysRevLett.58.1490.)
- Hix, W. R. & Thielemann, F.-K. 1996, "Silicon Burning. I. Neutronization and the Physics of Quasi-Equilibrium", ApJ 460, 869 (HT96). arXiv:astro-ph/9511088. (Two QSE groups + light group `9511088.tex:249–256, 540–544`, parameter cube 3.5–5 GK `:292–293`, TA85 Z ≈ 21 bottleneck `:271–274` verified against arXiv TeX; vol/page confirmed via CrossRef DOI 10.1086/177016.)
- Hix, W. R. & Thielemann, F.-K. 1999a, "Silicon Burning. II. Quasi-Equilibrium and Explosive Burning", ApJ 511, 862. arXiv:astro-ph/9808203. (Verified against arXiv TeX `HT98.tex:242–246, 828–833`; no meta.xml in cache — vol/page as in the tier2 audit.)
- Hix, W. R. & Thielemann, F.-K. 1999b, "Computational methods for nucleosynthesis and nuclear energy generation", J. Comput. Appl. Math. 109, 321. arXiv:astro-ph/9906478. (Review carrying the reduced-network scheme; vol/page from the published record.)
- Hix, W. R., Messer, O. E. B., Mezzacappa, A., et al. 2003, "Consequences of Nuclear Electron Capture in Core Collapse Supernovae", Phys. Rev. Lett. 91, 201102. (Uncached this session; named as the natural citation for EC-on-nuclei during collapse — content ASSUMED-with-attribution.)
- Hix, W. R., Parete-Koon, S. T., Freiburghaus, C. & Thielemann, F.-K. 2007, "The QSE-reduced Nuclear Reaction Network for Silicon Burning", ApJ 667, 476. (Journal-only, no arXiv posting.)
- Hoyle, F. 1954, "On Nuclear Reactions Occuring in Very Hot Stars. I. The Synthesis of Elements from Carbon to Nickel", ApJS 1, 121. (Pre-arXiv; bibliographic data from CrossRef DOI 10.1086/190005; not cached — content ASSUMED-with-attribution.)
- Iliadis, C. 2015, *Nuclear Physics of Stars* (2nd ed.; Wiley-VCH). (Textbook; §3.2.1 Gamow-peak coefficients E₀ = 0.1220 (Z₁²Z₂²A T₉²)^{1/3} MeV and τ = 4.248 (Z₁²Z₂²A/T₉)^{1/3}, eq. 3.75 — recomputed here and match; DOI 10.1002/9783527692668.)
- Itoh, N., Hayashi, H., Nishikawa, A. & Kohyama, Y. 1996, "Neutrino Energy Loss in Stellar Interiors. VII. Pair, Photo-, Plasma, Bremsstrahlung, and Recombination Neutrino Processes", ApJS 102, 411. (Pre-arXiv; bibliographic data from CrossRef DOI 10.1086/192264 and the Kato et al. 2020 `.bbl`; content not read — cited as the fitting reference by three cached secondaries.)
- Janka, H.-T., Langanke, K., Marek, A., Martínez-Pinedo, G. & Müller, B. 2007, "Theory of core-collapse supernovae", Phys. Rep. 442, 38. arXiv:astro-ph/0612072. (Verified against arXiv TeX `Jankaetal-astroph.tex:207, 1866–1869`; meta.xml absent — vol/page from CrossRef DOI 10.1016/j.physrep.2007.02.002.)
- Janka, H.-T. 2012, "Explosion Mechanisms of Core-Collapse Supernovae", Annu. Rev. Nucl. Part. Sci. 62, 407. arXiv:1206.2503. (Re-verified against arXiv TeX `JankaText-arxiv.tex:441–442, 2727`; vol/page from DOI 10.1146/annurev-nucl-102711-094901 in meta.xml.)
- Janka, H.-T. 2017, "Neutrino Emission from Supernovae", in *Handbook of Supernovae*, eds. A. W. Alsabti & P. Murdin (Springer), 1575. arXiv:1702.08713. (Verified against arXiv TeX `janka-neutrinos.tex:136–137, 166–167, 264–267`; DOI 10.1007/978-3-319-21846-5_4 from meta.xml; chapter page 1575 from CrossRef.)
- Jermyn, A. S., Bauer, E. B., Schwab, J., et al. 2023, "Modules for Experiments in Stellar Astrophysics (MESA): Time-dependent Convection, Energy Conservation, Automatic Differentiation, and Infrastructure", ApJS 265, 15 (MESA VI). arXiv:2208.03651. (Verified against arXiv TeX `src/rates.tex:25–71` — `op_split_burn` zeroes ∂ε_nuc/∂T, ∂ρ and computes ε_nuc from the composition difference; meta.xml has no journal_ref — vol/page from CrossRef DOI 10.3847/1538-4365/acae8d and the NuGNN `.bbl`.)
- Jordan, G. C., Gupta, S. S., Meyer, B. S. & The, L.-S. 2003, "Nuclear reactions important in α-rich freezeouts", Phys. Rev. C 68, 065801 (JGM 2003). arXiv:nucl-th/0211022. (Verified against arXiv TeX; journal ref from meta.xml, confirmed via CrossRef DOI 10.1103/PhysRevC.68.065801.)
- Juodagalvis, A., Langanke, K., Hix, W. R., Martínez-Pinedo, G. & Sampaio, J. M. 2010, "Improved estimate of electron capture rates on nuclei during stellar core collapse", Nucl. Phys. A 848, 454. arXiv:0909.0179. (Uncached; cited via Paxton et al. 2015 §6 (`\citep{Juodagalvis10}`) for the large NSE weak-rate pools; bibliographic data from CrossRef DOI 10.1016/j.nuclphysa.2010.09.012 — content ASSUMED-with-attribution.)
- Kasen, D. & Woosley, S. E. 2009, "Type II Supernovae: Model Light Curves and Standard Candle Relationships", ApJ 703, 2205. arXiv:0910.1590. (Re-verified against arXiv TeX `ms.tex:225–232, 284–288`.)
- Kato, C., Ishidoshiro, K. & Yoshida, T. 2020, "Theoretical Prediction of Presupernova Neutrinos and Their Detection", Annu. Rev. Nucl. Part. Sci. 70, 121. arXiv:2006.02519. (Stage temperatures/durations for a 15 M⊙ model verified against arXiv TeX `Section2/Section2.tex:41–95`; cache has no meta.xml — vol/page from CrossRef DOI 10.1146/annurev-nucl-040620-021320.)
- Kim, C. H., Chae, K. Y., Ko, S., Mumpower, M. R. & Smith, M. S. 2026, "NuGNN: a Graph Neural Network for Nuclear Reaction Network Equations", arXiv:2606.04491 (NuGNN). (arXiv preprint only as of the audit date.) (Verified against arXiv TeX `Eq_Solver.tex:49, 59` — 690-isotope GNN surrogate; landscape citations of Fan et al. 2022 / Zhang et al. 2025.)
- Kippenhahn, R., Weigert, A. & Weiss, A. 2012, *Stellar Structure and Evolution* (2nd ed.; Springer) (KWW). (Textbook; DOI 10.1007/978-3-642-30304-3; Ch. 2 hydrostatic equilibrium, Ch. 3 virial theorem / t_KH, Ch. 15 degenerate electron gas, §18.6 pair neutrinos — chapter numbers from memory.)
- Kish, L. 1965, *Survey Sampling* (Wiley). (The design effect.)
- Kobayashi, C., Karakas, A. I. & Lugaro, M. 2020, "The Origin of Elements from Carbon to Uranium", ApJ 900, 179. arXiv:2008.04660. (Verified against arXiv TeX; vol/page from CrossRef DOI 10.3847/1538-4357/abae65.)
- Kurfess, J. D., Johnson, W. N., Kinzer, R. L., et al. 1992, "Oriented Scintillation Spectrometer Experiment Observations of ⁵⁷Co in SN 1987A", ApJ 399, L137. (Pre-arXiv.) (The 1.5 ± 0.3 ± 0.2 ⁵⁷Ni/⁵⁶Ni ratio quoted secondarily via Seitenzahl et al. 2014 `ms.tex:132–134`.)
- Lakshminarayanan, B., Pritzel, A. & Blundell, C. 2017, "Simple and Scalable Predictive Uncertainty Estimation using Deep Ensembles", Advances in Neural Information Processing Systems 30 (NIPS 2017). arXiv:1612.01474. (Venue from the meta.xml comment "NIPS 2017"; TeX cached, content not needed; not indexed in CrossRef.)
- Langanke, K. & Martínez-Pinedo, G. 2000, "Shell-model calculations of stellar weak interaction rates: II. Weak rates for nuclei in the mass range A = 45–65 in supernovae environments", Nucl. Phys. A 673, 481 (LMP). arXiv:nucl-th/0001018. (Journal ref re-confirmed from meta.xml; rate magnitudes are in figures only.)
- Langanke, K. & Martínez-Pinedo, G. 2003, "Nuclear weak-interaction processes in stars", Rev. Mod. Phys. 75, 819 (LMP 2003). arXiv:nucl-th/0203071. (Verified against arXiv TeX; journal ref from meta.xml, confirmed via CrossRef DOI 10.1103/RevModPhys.75.819; its `.bbl` (`rmp-bbl.tex`) is the secondary source for several pre-arXiv entries here.)
- Langanke, K., Martínez-Pinedo, G., Sampaio, J. M., et al. 2003, "Electron Capture Rates on Nuclei and Implications for Stellar Core Collapse", Phys. Rev. Lett. 90, 241102. (Uncached this session; named as the natural citation for EC on nuclei dominating during collapse — content ASSUMED-with-attribution.)
- Lattimer, J. M. & Prakash, M. 2001, "Neutron Star Structure and the Equation of State", ApJ 550, 426. arXiv:astro-ph/0002232. (Uncached; the binding-energy formula 0.6β/(1 − 0.5β) (their eq. 35) quoted secondarily via Suwa et al. 2018 `:284`; bibliographic data from CrossRef DOI 10.1086/319702 — content ASSUMED-with-attribution.)
- Limongi, M. 2017, "Supernovae from Massive Stars", in *Handbook of Supernovae*, eds. A. W. Alsabti & P. Murdin (Springer). arXiv:1706.01913. (Neutrino-dominated phases, τ_nuc ~ E_nuc M/L_tot, and the C/Ne/O/Si lifetimes verified against arXiv TeX `src/limongi.tex:48`; book ref from the meta.xml comment, chapter DOI 10.1007/978-3-319-20794-0_119-1 via CrossRef.)
- Lippuner, J. & Roberts, L. F. 2017, "SkyNet: A Modular Nuclear Reaction Network Library", ApJS 233, 18. arXiv:1706.06198. (Uncached; bibliographic data from CrossRef DOI 10.3847/1538-4365/aa94cb only.)
- Loredo, T. J. & Lamb, D. Q. 2002, "Bayesian analysis of neutrinos observed from supernova SN 1987A", Phys. Rev. D 65, 063002. arXiv:astro-ph/0107260. (Uncached; the fitted total neutrino energy of SN 1987A; bibliographic data from CrossRef DOI 10.1103/PhysRevD.65.063002 — content ASSUMED-with-attribution.)
- Louizos, C., Welling, M. & Kingma, D. P. 2018, "Learning Sparse Neural Networks through L₀ Regularization", ICLR 2018. arXiv:1712.01312. (Verified against arXiv TeX `sl0.tex:94`; venue from the meta.xml comment; not indexed in CrossRef.)
- Lyman, J. D., Bersier, D., James, P. A., et al. 2016, "Bolometric light curves and explosion parameters of 38 stripped-envelope core-collapse supernovae", MNRAS 457, 328. arXiv:1406.3667. (Uncached this session; named for SE-SN peak times/⁵⁶Ni masses.)
- Martín-Fernández, J. A., Barceló-Vidal, C. & Pawlowsky-Glahn, V. 2003, "Dealing with Zeros and Missing Values in Compositional Data Sets Using Nonparametric Imputation", Math. Geol. 35, 253. (Bibliographic data from CrossRef DOI 10.1023/A:1023866030544; content textbook-standard — ASSUMED-with-attribution.)
- Meakin, C. A. & Arnett, D. 2007, "Turbulent Convection in Stellar Interiors. I. Hydrodynamic Simulation", ApJ 667, 448. arXiv:astro-ph/0611315. (Verified against arXiv TeX `ms.new.tex`; vol/page from the meta.xml journal_ref, confirmed via CrossRef DOI 10.1086/520318.)
- MESA r23.05.1 source (local build at `~/mesa-r23.05.1`; Paxton et al. 2011, 2015, 2019; Jermyn et al. 2023). Files cited: `turb/private/mlt.f90:156`; `star/private/struct_burn_mix.f90:89–177`; `star/defaults/controls.defaults:9052, 9068`; `star/defaults/star_job.defaults:2364–2377`; `star/public/star_lib.f90:305`; `net/public/net_lib.f90`; `net/private/net_burn.f90`; `net/private/net_burn_support.f90`; `rates/private/reaclib_support.f90`; `rates/private/screen_chugunov.f90:26`; `data/rates_data/weakreactions.tables` (header attributions FFN / OHMT / LMP); `data/net_data/nets/mesa_80.net`. (Local tree; no NSE-switch control or code path found in `star/`, `net/`.)
- MESAHub/mesa GitHub issue #575, "Bug in the nuclear reaction rates of reactions with more than two reactants and/or products" (A. Grichener, opened 2023-08-07, closed 2024-05-06; fix announced for the next release, comment of 2024-05-06). (Cached `data/literature/web/gh575.md`; the bug is described in Grichener et al. 2025 Appendix B.)
- Meyer, B. S., Krishnan, T. D. & Clayton, D. D. 1998, "Theory of Quasi-Equilibrium Nucleosynthesis and Applications to Matter Expanding from High Temperature and Density", ApJ 498, 808 (MKC98). (Uncached; cited by The et al. 1998 (`\cite{mkc97}`) for the QSE-not-NSE constraint in α-rich freeze-out; bibliographic data from CrossRef DOI 10.1086/305562 — content ASSUMED-with-attribution.)
- Milisavljevic, D. & Fesen, R. A. 2013, "A Detailed Kinematic Map of Cassiopeia A's Optical Main Shell and Outer High-velocity Ejecta", ApJ 772, 134. arXiv:1306.2310. (Uncached; bibliographic data from CrossRef DOI 10.1088/0004-637X/772/2/134; content ASSUMED-with-attribution.)
- Müller, B. 2016, "The Status of Multi-Dimensional Core-Collapse Supernova Models", PASA 33, e048. arXiv:1608.03274. (Verified against arXiv TeX `paper.tex:1062–1069, 2418–2420`; article number e048 from CrossRef DOI 10.1017/pasa.2016.40 (meta.xml carries the DOI only).)
- Müller, B., Viallet, M., Heger, A. & Janka, H.-T. 2016, "The Last Minutes of Oxygen Shell Burning in a Massive Star", ApJ 833, 124. arXiv:1605.01393. (Verified against arXiv TeX `paper.tex:185–186`; vol/page from CrossRef DOI 10.3847/1538-4357/833/1/124.)
- Nadyozhin, D. K. 1994, "The properties of Ni → Co → Fe decay", ApJS 92, 527. (Pre-arXiv; bibliographic data from CrossRef DOI 10.1086/192008; the ε values are ASSUMED-with-attribution and were independently re-derived from ENSDF here.)
- Nakar, E., Poznanski, D. & Katz, B. 2016, "The Importance of ⁵⁶Ni in Shaping the Light Curves of Type II Supernovae", ApJ 823, 127. arXiv:1506.07185. (Uncached this session; named for the ⁵⁶Ni contribution to IIP light curves.)
- O'Connor, E. & Ott, C. D. 2011, "Black Hole Formation in Failing Core-Collapse Supernovae", ApJ 730, 70. arXiv:1010.5550. (Verified against arXiv TeX; journal ref from meta.xml, confirmed via CrossRef DOI 10.1088/0004-637X/730/2/70.)
- Oda, T., Hino, M., Muto, K., Takahara, M. & Sato, K. 1994, "Rate Tables for the Weak Processes of sd-Shell Nuclei in Stellar Matter", At. Data Nucl. Data Tables 56, 231 (OHMT). (Pre-arXiv; attribution as printed in the MESA `weakreactions.tables` header; vol/page confirmed via CrossRef DOI 10.1006/adnd.1994.1007; content not opened.)
- Odrzywolek, A., Misiaszek, M. & Kutschera, M. 2004, "Detection possibility of the pair-annihilation neutrinos from the neutrino-cooled pre-supernova star", Astropart. Phys. 21, 303. arXiv:astro-ph/0311012. (Table 2 stage properties, ν cross sections and the T > 10⁹ K pair onset verified against arXiv TeX; journal ref from meta.xml, confirmed via CrossRef DOI 10.1016/j.astropartphys.2004.02.002.)
- Ono, S. & Sugimura, K. 2026, "Neural-network Chemical Emulator for First-star Formation: Robust Iterative Predictions over a Wide Density Range", ApJ 996, 9. arXiv:2508.16114 (posted 2025). (Method and stated premise verified against arXiv TeX `main_accepted.tex:176–210`; journal ref from meta.xml, confirmed via CrossRef DOI 10.3847/1538-4357/ae1ca9 — CrossRef's "issued" date is the 2025 online date, the volume-996 print year is 2026; cited in the text as 2026, alias "Ono & Sugimura 2025".)
- Ovadia, Y., Fertig, E., Ren, J., et al. 2019, "Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty Under Dataset Shift", Advances in Neural Information Processing Systems 32 (NeurIPS 2019). arXiv:1906.02530. (Verified against arXiv TeX; venue from the meta.xml comment; not indexed in CrossRef.)
- Patton, K. M., Lunardini, C. & Farmer, R. J. 2017, "Presupernova Neutrinos: Realistic Emissivities from Stellar Evolution", ApJ 840, 2. arXiv:1511.02820. (Pair dominance in the core, O months / Si days (citing WHW02) verified against arXiv TeX `:152, :405`; vol/page from the Kato et al. 2020 `.bbl:68–70`, confirmed via CrossRef DOI 10.3847/1538-4357/aa6ba8.)
- Paxton, B., Bildsten, L., Dotter, A., Herwig, F., Lesaffre, P. & Timmes, F. 2011, "Modules for Experiments in Stellar Astrophysics (MESA)", ApJS 192, 3 (MESA I). arXiv:1009.1622. (Verified against arXiv TeX `mesa.tex:1108–1116` (cells "hundreds to thousands", coupled structure + composition solve), §6.1 analytic-Jacobian requirement, §6.4 retries/backups and timestep controls; journal ref from meta.xml.)
- Paxton, B., Marchant, P., Schwab, J., et al. 2015, "Modules for Experiments in Stellar Astrophysics (MESA): Binaries, Pulsations, and Explosions", ApJS 220, 15 (MESA III). arXiv:1506.03146. (Verified against arXiv TeX (§6 weak-rate pools); journal ref from meta.xml, confirmed via CrossRef DOI 10.1088/0067-0049/220/1/15.)
- Paxton, B., Smolec, R., Schwab, J., et al. 2019, "Modules for Experiments in Stellar Astrophysics (MESA): Pulsating Variable Stars, Rotation, Convective Boundaries, and Energy Conservation", ApJS 243, 10 (MESA V). arXiv:1903.01426. (TeX cached, not needed for any claim; vol/page from CrossRef DOI 10.3847/1538-4365/ab2241.)
- Pejcha, O. & Thompson, T. A. 2015, "The Landscape of the Neutrino Mechanism of Core-collapse Supernovae: Neutron Star and Black Hole Mass Functions, Explosion Energies, and Nickel Yields", ApJ 801, 90 (PT15). arXiv:1409.0540. (Verified against arXiv TeX `:93, :116`; meta.xml absent — vol/page from CrossRef DOI 10.1088/0004-637X/801/2/90.)
- Perego, A., Hempel, M., Fröhlich, C., et al. 2015, "PUSHing Core-collapse Supernovae to Explosions in Spherical Symmetry I: the Model and the Case of SN 1987A", ApJ 806, 275. arXiv:1501.02845. (Verified against arXiv TeX; journal ref from meta.xml, confirmed via CrossRef DOI 10.1088/0004-637X/806/2/275.)
- Popov, D. V. 1993, "An Analytical Model for the Plateau Stage of Type II Supernovae", ApJ 414, 712. (Pre-arXiv.)
- Rauscher, T., Thielemann, F.-K. & Kratz, K.-L. 1997, "Nuclear level density and the determination of thermonuclear rates for astrophysics", Phys. Rev. C 56, 1613. (Cited via pynucastro's `rauscher:1997` partition-function tables; not cached — vol/page confirmed via CrossRef DOI 10.1103/PhysRevC.56.1613; content not opened.)
- Rauscher, T. & Thielemann, F.-K. 2000, "Astrophysical reaction rates from statistical model calculations", At. Data Nucl. Data Tables 75, 1. arXiv:astro-ph/0004059. (The 9.8685×10⁹ T₉^{3/2} reciprocity constant, verified verbatim against the arXiv TeX source.) (Re-verified at `0004059.tex:107–109, 575`; journal ref from meta.xml.)
- Rauscher, T., Heger, A., Hoffman, R. D. & Woosley, S. E. 2002, "Nucleosynthesis in Massive Stars with Improved Nuclear and Stellar Physics", ApJ 576, 323. arXiv:astro-ph/0112478. (Uncached; candidate citation for adaptive networks (KEPLER); bibliographic data from CrossRef DOI 10.1086/341728 — content ASSUMED-with-attribution.)
- Rauscher, T. 2003, "Nuclear Partition Functions at Temperatures Exceeding 10¹⁰ K", ApJS 147, 403. arXiv:astro-ph/0304047. (Bibliographic data from the meta.xml journal_ref, confirmed via CrossRef DOI 10.1086/375733; content not read.)
- Reichert, M., Winteler, C., Korobkin, O., et al. 2023, "The Nuclear Reaction Network WinNet", ApJS 268, 66. arXiv:2305.07048. (Uncached; bibliographic data from CrossRef DOI 10.3847/1538-4365/acf033 only.)
- Rolfs, C. E. & Rodney, W. S. 1988, *Cauldrons in the Cosmos: Nuclear Astrophysics* (University of Chicago Press). (Textbook; §4.2, eq. 4.42 E_G ≈ 0.978–0.979 (Z₁Z₂)² μ MeV — section/equation numbers from memory.)
- Salpeter, E. E. 1952, "Nuclear Reactions in Stars Without Hydrogen", ApJ 115, 326. (Pre-arXiv; vol/page confirmed via CrossRef DOI 10.1086/145546; not cached — content ASSUMED-with-attribution; NB the cached `salpeter1954.md` is the screening paper Aust. J. Phys. 7, 373, not this one.)
- Sana, H., de Mink, S. E., de Koter, A., et al. 2012, "Binary Interaction Dominates the Evolution of Massive Stars", Science 337, 444. arXiv:1207.6397. (PDF-only cache; abstract verified from meta.xml; journal ref confirmed via CrossRef DOI 10.1126/science.1223344.)
- Sanchez-Gonzalez, A., Godwin, J., Pfaff, T., Ying, R., Leskovec, J. & Battaglia, P. W. 2020, "Learning to Simulate Complex Physics with Graph Networks", Proc. 37th Int. Conf. Machine Learning (ICML), PMLR 119, 8459. arXiv:2002.09405. (Uncached; bibliographic data secondary via the Brandstetter et al. 2022 `.bbl:317–319`; PMLR vol/page from memory — not indexed in CrossRef, journal ref not verified.)
- Schuster, S. & Schuster, R. 1989, "A generalization of Wegscheider's condition. Implications for properties of steady states and for quasi-steady-state approximation", J. Math. Chem. 3, 25.
- Seitenzahl, I. R., Timmes, F. X., Marin-Laflèche, A., et al. 2008, "Proton-rich Nuclear Statistical Equilibrium", ApJ 685, L129. arXiv:0808.2033.
- Seitenzahl, I. R., Townsley, D. M., Peng, F. & Truran, J. W. 2009, "Nuclear statistical equilibrium for Type Ia supernova simulations", At. Data Nucl. Data Tables 95, 96. (Journal-only; named as an example of an NSE-switching code — content not re-opened this session.)
- Seitenzahl, I. R., Timmes, F. X. & Magkotsios, G. 2014, "The Light Curve of SN 1987A Revisited: Constraining Production Masses of Radioactive Nuclides", ApJ 792, 10. arXiv:1408.5986. (Re-verified against arXiv TeX `ms.tex:132–134`.)
- Shapiro, S. L. & Teukolsky, S. A. 1983, *Black Holes, White Dwarfs, and Neutron Stars: The Physics of Compact Objects* (Wiley-Interscience) (ST83). (M_ch = 1.457 (2/μₑ)² M_⊙, eq. 3.3.17.) (Also §2.3 degenerate electron EOS, §6.7 pressure-averaged Γ criterion, §18.4 coherent-scattering formula — section numbers from memory.)
- Shrout, P. E. & Fleiss, J. L. 1979, "Intraclass correlations: uses in assessing rater reliability", Psychol. Bull. 86, 420.
- Smith Clark, A., Johnson, E. T., Chen, Z., et al. 2023, "pynucastro: A Python Library for Nuclear Astrophysics", ApJ 947, 65. arXiv:2210.09965. (Verified against arXiv TeX `:405, :498, :881, :885, :970` — NSE solver, partition functions, no weak inverses, screening options; vol/page from CrossRef DOI 10.3847/1538-4357/acbaff.)
- Smith, M. S. & Lu, D. 2024, "Machine learning opportunities for nucleosynthesis studies", Front. Astron. Space Sci. 11, 1494439. (Uncached; bibliographic data from the NNN `refs.bib` (`SmithLu2024`) only; content ASSUMED-with-attribution — review of ML in nucleosynthesis.)
- Sobol', I. M. 1967, "On the distribution of points in a cube and the approximate evaluation of integrals", USSR Comput. Math. Math. Phys. 7, 86. (Cited by Grichener et al. 2025 `main.tex:190` for the training-grid sampler; bibliographic data from CrossRef DOI 10.1016/0041-5553(67)90144-9; content not opened.)
- Sukhbold, T., Ertl, T., Woosley, S. E., Brown, J. M. & Janka, H.-T. 2016, "Core-collapse Supernovae from 9 to 120 Solar Masses Based on Neutrino-powered Explosions", ApJ 821, 38. arXiv:1510.04643. (Verified against arXiv TeX `ms.tex:1389–1392, 2102–2103`; vol/page from CrossRef DOI 10.3847/0004-637X/821/1/38.)
- Sukhbold, T., Woosley, S. E. & Heger, A. 2018, "A High-resolution Study of Presupernova Core Structure", ApJ 860, 93 (SWH18). arXiv:1710.03243. (Verified against arXiv TeX `ms.tex:1775–1778`; vol/page from CrossRef DOI 10.3847/1538-4357/aac2da; NB the arXiv title differs: "High Resolution Study of Presupernova Compactness".)
- Suwa, Y., Yoshida, T., Shibata, M., Umeda, H. & Takahashi, K. 2018, "On the minimum mass of neutron stars", MNRAS 481, 3305. arXiv:1808.02328. (ΔM = 0.084 M⊙ (M/M⊙)² formula and the App. B K constant verified against arXiv TeX `ns_minimum.tex:284, 531`; meta.xml absent — vol/page from CrossRef DOI 10.1093/mnras/sty2460.)
- Suzuki, T., Toki, H. & Nomoto, K. 2016, "Electron-capture and β-decay Rates for sd-shell Nuclei in Stellar Environments Relevant to High-density O–Ne–Mg Cores", ApJ 817, 163. arXiv:1512.00132. (Verified against arXiv TeX; vol/page not in meta.xml — from CrossRef DOI 10.3847/0004-637X/817/2/163.)
- The, L.-S., Clayton, D. D., Jin, L. & Meyer, B. S. 1998, "Nuclear Reactions Governing the Nucleosynthesis of ⁴⁴Ti", ApJ 504, 500. arXiv:astro-ph/9806211. (Verified against arXiv TeX `ms.tex:400–406`; vol/page from CrossRef DOI 10.1086/306057 (ApJ 504, 500–515) and JGM 2003's bibcode 1998ApJ...504..500T — the arXiv meta.xml journal_ref "vol. 487, Sept 1, 1998" is WRONG and was not used.)
- Thielemann, F.-K. & Arnett, W. D. 1985, "Hydrostatic Nucleosynthesis. II. Core Neon to Silicon Burning and Presupernova Abundance Yields of Massive Stars", ApJ 295, 604 (TA85). (Pre-arXiv; the Z ≈ 21 QSE-group bottleneck bridged on the proton-rich side, cited secondarily via HT96 `9511088.tex:271–274`; bibliographic data from CrossRef DOI 10.1086/163403 — content ASSUMED-with-attribution.)
- Tibshirani, R. J., Barber, R. F., Candès, E. J. & Ramdas, A. 2019, "Conformal Prediction Under Covariate Shift", Advances in Neural Information Processing Systems 32 (NeurIPS 2019). arXiv:1904.06019. (Exchangeability assumption verified against arXiv TeX `paper.tex:52`; venue not in meta.xml, from memory — not indexed in CrossRef.)
- Tiesinga, E., Mohr, P. J., Newell, D. B. & Taylor, B. N. 2021, "CODATA recommended values of the fundamental physical constants: 2018", Rev. Mod. Phys. 93, 025010 (CODATA 2018). (Constants used in the arithmetic recomputations here (α, ħc, m_u, 1 MeV = 1.6021766×10⁻⁶ erg, the 9.86846×10⁹ reciprocity constant); bibliographic data from CrossRef DOI 10.1103/RevModPhys.93.025010.)
- Timmes, F. X., Woosley, S. E. & Weaver, T. A. 1996, "The Neutron Star and Black Hole Initial Mass Function", ApJ 457, 834 (TWW96). arXiv:astro-ph/9510136. (Verified against text strings extracted from the cached dvips PostScript (eq. 1, M_Ch0 = 5.83 Yₑ²); vol/page from the Heger et al. 2001 and Suwa et al. 2018 bibliographies, confirmed via CrossRef DOI 10.1086/176778.)
- Timmes, F. X. 1999, "Integration of Nuclear Reaction Networks for Stellar Hydrodynamics", ApJS 124, 241. (Pre-arXiv-cache; bibliographic data from the NuGNN `.bbl` (`Eq_Solver.tex:642–645`), confirmed via CrossRef DOI 10.1086/313257; ADS unreachable — content ASSUMED-with-attribution.)
- Timmes, F. X., Hoffman, R. D. & Woosley, S. E. 2000, "An Inexpensive Nuclear Energy Generation Network for Stellar Hydrodynamics", ApJS 129, 377. arXiv:astro-ph/0002007. (Uncached; named for the NSE-switch practice in hydro codes; bibliographic data from CrossRef DOI 10.1086/313407 — content ASSUMED-with-attribution.)
- Tinsley, B. M. 1979, "Stellar lifetimes and abundance ratios in chemical evolution", ApJ 229, 1046. (Pre-arXiv; bibliographic data from CrossRef DOI 10.1086/157039; the [α/Fe] timing argument is textbook-standard — content ASSUMED-with-attribution.)
- Ugliano, M., Janka, H.-T., Marek, A. & Arcones, A. 2012, "Progenitor-explosion Connection and Remnant Birth Masses for Neutrino-driven Supernovae of Iron-core Progenitors", ApJ 757, 69. arXiv:1205.3657. (Uncached; bibliographic data secondary via the Ertl et al. 2016 `.tex` bibitem `:2783–2784`, confirmed via CrossRef DOI 10.1088/0004-637X/757/1/69.)
- Virtanen, P., Gommers, R., Oliphant, T. E., et al. 2020, "SciPy 1.0: fundamental algorithms for scientific computing in Python", Nat. Methods 17, 261. (Software citation for `scipy.stats.qmc.Sobol` (scramble=True, seed=None default — the non-regenerable training grid); vol/page from memory of the standard citation — CrossRef query returned only a review of the paper; journal ref not verified.)
- Vovk, V., Gammerman, A. & Shafer, G. 2005, *Algorithmic Learning in a Random World* (Springer). (Textbook; the origin of conformal prediction; uncached, named as the classic citation.)
- Wang, M., Huang, W. J., Kondev, F. G., Audi, G. & Naimi, S. 2021, "The AME 2020 atomic mass evaluation (II). Tables, graphs and references", Chinese Phys. C 45, 030003 (AME2020). (Mass excesses and B/A retrieved via the IAEA Live Chart API `nds.iaea.org/relnsd/v1/data?fields=ground_states` on 2026-08-18: B/A(⁵⁶Ni) 8642.7811, (⁵⁴Fe) 8736.3846, (⁵⁸Ni) 8732.0621, (⁵⁶Fe) 8790.3563, (⁵⁸Fe) 8792.2534, (⁶²Ni) 8794.5555, (⁴He) 7073.916 keV; S_α(²⁸Si) = 9.984 MeV recomputed from pynucastro's AME2020 masses.)
- Weaver, T. A., Zimmerman, G. B. & Woosley, S. E. 1978, "Presupernova evolution of massive stars", ApJ 225, 1021. (Pre-arXiv; the KEPLER code, named as an example of an NSE-switching stellar code; bibliographic data from CrossRef DOI 10.1086/156569 — content ASSUMED-with-attribution.)
- Wegscheider, R. 1901, "Über simultane Gleichgewichte und die Beziehungen zwischen Thermodynamik und Reactionskinetik homogener Systeme", Monatsh. Chem. 22, 849. (Reused from the tier2 References; the cycle condition Q ∉ rowspace(ν) is applied through Schuster & Schuster 1989.)
- Wilson, J. R. 1985, "Supernovae and post-collapse behavior", in *Numerical Astrophysics*, eds. J. M. Centrella, J. M. LeBlanc & R. L. Bowers (Jones & Bartlett, Boston), 422. (Pre-arXiv conference volume; bibliographic data secondary via the Janka et al. 2007 bibliography `Jankaetal-astroph.tex:2779–2781`; not in CrossRef — page not independently verified; content ASSUMED-with-attribution.)
- Woosley, S. E., Arnett, W. D. & Clayton, D. D. 1973, "The Explosive Burning of Oxygen and Silicon", ApJS 26, 231 (WAC73). (Pre-arXiv; read from the ADS scan — the two-group structure and the ⁴⁵Sc(p,γ)⁴⁶Ti bridge, §VIb, Fig. 17.) (Read from the ADS scan in the 2026-08-14 audit (tier2); two-group content re-verified secondarily via HT96 `9511088.tex:249–256, 1288–1296`.)
- Woosley, S. E., Heger, A. & Weaver, T. A. 2002, "The evolution and explosion of massive stars", Rev. Mod. Phys. 74, 1015 (WHW02). (No arXiv posting; bibliographic data from CrossRef DOI 10.1103/RevModPhys.74.1015; ADS page not retrievable — Table 1 burning-stage values not re-read, bracketed by cached secondaries (Kato et al. 2020, Patton et al. 2017, Odrzywolek et al. 2004); content ASSUMED-with-attribution.)
- Woosley, S. & Janka, T. 2005, "The physics of core-collapse supernovae", Nat. Phys. 1, 147. arXiv:astro-ph/0601261. (Si-ignition 2.7–3.5 GK; verified at abstract/secondary level.) (Cache dir empty this session; abstract fetched from arxiv.org/abs — silent on Si-burning temperatures.)
- Woosley, S. E. & Heger, A. 2007, "Nucleosynthesis and remnants in massive stars of solar metallicity", Phys. Rep. 442, 269 (WH07). arXiv:astro-ph/0702176. (Verified against arXiv TeX `ms.tex:415–418`; journal ref from meta.xml, confirmed via CrossRef DOI 10.1016/j.physrep.2007.02.009.)
- Yadav, N., Müller, B., Janka, H.-T., Melson, T. & Heger, A. 2020, "Large-scale Mixing in a Violent Oxygen–Neon Shell Merger Prior to a Core-collapse Supernova", ApJ 890, 94. arXiv:1905.04378. (Uncached; the 3D O–Ne shell-merger simulation; bibliographic data from CrossRef DOI 10.3847/1538-4357/ab66bb — content ASSUMED-with-attribution.)
- Yahil, A. 1983, "Self-similar Stellar Collapse", ApJ 265, 1047. (Pre-arXiv.) (Bibliographic data re-confirmed via the Müller 2016 `.bbl:1711–1713`.)
- Zhang, X., Yi, Y., Wang, L., et al. 2025, "Deep Neural Networks for Modeling Astrophysical Nuclear Reacting Flows", ApJ 990, 105. (Uncached; bibliographic data from the NuGNN `.bbl` (`Eq_Solver.tex:679–682`), confirmed via CrossRef DOI 10.3847/1538-4357/adf331; arXiv id not determined; content ASSUMED-with-attribution — 3- and 13-isotope networks per NuGNN's description.)
