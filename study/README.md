# Study notes

Personal study material for working through the repository's theory
file-by-file — **not project spec**, and deliberately written without reference
to `docs/`. Everything is derived from first principles or read off the
business code, configs, notebooks, and tests.

Measured project numbers quoted in these notes originate in `RESULTS.md` with
full provenance; these files are not their source of truth.

| File | Covers |
|---|---|
| [`tier0.md`](tier0.md) | **Tier 0, complete.** Part 0 (plasma EOS, statistical mechanics, nuclear data, neutrinos) · Part I (motivation) · Part II = **S0** (species, abundances, (N,Z)) · Part III = **S1** (the dataset) · Part IV (operator splitting, the reachable manifold, rollout) · Part V (cancellation, conditioning, stiffness, floating point) · Part VI (ML framing, MESA/bbq, prior art, observations) |
| [`tier1.md`](tier1.md) | **Tier 1, complete.** Part I (rate theory: ⟨σv⟩, Gamow peak, reciprocity, Hauser–Feshbach, photodisintegration) · Part II = **S2** (REACLIB, the seven-coefficient form, the compiled evaluator) · Part III = **S3** (detailed balance, partition functions, the pf gate, gh-575, Coulomb-NSE) · Part IV = **S4** (screening, Γ regimes, the screened-κ offset, weak-sector screening) · Part V = **S5** (weak sector: GT strength, EC in a degenerate plasma, Pauli blocking, the (T, ρYₑ) tables) · Part VI = **S6** (MESA ⟷ pynucastro reconciliation) · Part VII (the guards) · **Part VIII (open prerequisites — ten gaps nothing in the plan covers)** |
| [`tier2.md`](tier2.md) | **Tier 2, complete.** **Part 0** (the astrophysics the algebra is *for*: the NSE/QSE/kinetics hierarchy and its history, Si burning as photodisintegration rearrangement, the Yₑ→observable chain and the error budget it forces, deployment and the 1/f speedup ceiling, the kill-test as a matrix question) · Part I = **S7** (ν, conservation as the left null space, CRN theory and the flux cone, lepton ledgers, C, the projector derived twice, **Target A ≡ Target B reachability**, positivity, the 528-dim fibre, **effective dimension and where Yₑ hides**) · Part II = **S8** (pairs, the net identity, **κ = \|tanh(𝒜/2kT)\|**, **entropy production → a derived active set + a second-law constraint + a Lyapunov bound**, the store, the handshake, the vacuous pass) · Part III = **S9** (Saha term-by-term, the **dYₑ/du_p > 0 proof**, QSE clusters and u_G, the slow manifold, δ vs r_QSE, the empty mask) · Part IV = **S10** (stiffness, BDF/L-stability, the augmented [Y, Φ] state, why Φ is unrecoverable **and the flux head unidentifiable**, ∂R/∂Y, the energy identity as a *data* check **+ the Wegscheider measurement**, the cost wall) · Part V (executable policy **+ the measurement discipline it does not encode**) · **Part VI = the open register (R-01 … R-25)** · Part VII (how the register was built; is it converging?) |

**Standing open items.** [`tier1.md` Part VIII](tier1.md#part-viii--open-prerequisites-what-is-still-not-covered)
remains the cross-tier register for Tiers 0–1; **Tier 2's own register is
[`tier2.md` Part VI](tier2.md#part-vi--the-open-register)** — 25 items, `R-01 …
R-25`, each pointing at the section of Tier 2 that derives it, with a ranked top
eight in [§VI.3](tier2.md#vi3-ranked). It was built by two deliberate gap-audit
passes; [Part VII](tier2.md#part-vii--how-this-register-was-built-and-whether-it-is-finished)
records the method, the thirteen candidate axes that came back **already
covered**, and the convergence argument.

The five items that came with a measurement, all runnable on data already in
`data/`:

| | finding | consequence |
|---|---|---|
| **R-06** | **Wegscheider fails**: Q ∉ rowspace(ν) for the strong sector (rms 0.55 keV, max 3.5 keV, 331/561 and 972/1345 columns); stored Q vs pynucastro nuclide masses differ by up to 17–31 keV | explains the §IV.8 energy residual; predicts a **κ data floor of 6e-4…4e-3** bracketing the measured stock-MESA κ floor (RESULTS 2026-07-10) |
| **R-08** | **cluster-robust inference is absent**: per-row quantities have ICC 0.22–0.70 across trajectories (design effect 6.5–18.6), so `RESULTS.md`'s "657k samples" carry ~300 independent systems | every p-value and CI in the kill-test block is unstated or wrong; point estimates and the empty-mask result are unaffected. Fix = bootstrap over **trajectories** |
| **R-02** | visited compositions have effective dimension ≈ 3.4 / 8.6, but **Yₑ hides in a long low-variance tail** — by k = 30 PCs, Var(X) reaches 99.7% / 98.1% while Var(Yₑ) stalls at 93.0% / 95.3%; the budget needs 1 − 6.5e-8 | forced by §I.2.1 (the strong sector is Yₑ-neutral). Variance-truncated compression is **arithmetically excluded**, not merely risky |
| **R-07** | the regime box's **measure** was never checked against the stellar one: the 20 M⊙ track sits within 0.12–0.18 dex of a *line*; only 35% / 62% / 82% of the box is within 0.1 / 0.2 / 0.3 dex of a visited point | the box's *support* is defensible, its uniform *density* is not; predicts the Sobol→real-MESA gate will fire |
| **R-09** | CRN deficiency = 126 / 327, and the network is not weakly reversible | the Deficiency Zero Theorem gives nothing here — closed, not open. The flux-cone / elementary-flux-mode machinery still transfers |

Four more that are derivations rather than measurements: **R-01** (entropy
production σ = 2k_B s κ artanh κ ⇒ a parameter-free active set, i.e. the missing
derivation for κ > 0.1), **R-03** (the flux head is unidentifiable in 528
directions under a ΔY-only loss — a second, independent cost of Target A),
**R-12** (the speedup ceiling is 1/f in the fallback rate, so S22's gate has a
derivable target), and **R-16** (NSE-as-a-predictor has never been run as a
baseline — it may redefine the emulator's domain to T₉ < 5).

⚠ **The map below stops at Tier 3.** The emulator itself — Components A, C, D of
`docs/reports/consolidated-gnn-architecture.md`, and most of B — has **no node**,
and `docs/architecture/` (the named living spec) is empty. A sketched Tier 4
(S17–S22: backbone, learned mask, time conditioning, rollout stability, tail-risk
losses, UQ/OOD) is in [§VIII.E.1](tier1.md#viiie1-the-model-side-has-no-study-node-at-all).
Four of the eight open Phase-0 checklist rows are Tier-4 measurements.

One file per tier, each self-contained and read top to bottom. Tiers 0–2 are
written; Tier 3 and Tier 4 are not.

---

## Method — four passes per node

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

## The map

```
═══════════════════════════════════════════════════════════════════════════════════
 TIER 0 — SUBSTRATE  ✓ tier0.md          "what is a nuclear network, what is the data"
═══════════════════════════════════════════════════════════════════════════════════

   ┌─────────────────────────────┐        ┌─────────────────────────────┐
   │ S0  SPECIES & ABUNDANCE     │        │ S1  THE DATASET             │
   │     Y=X/A, Yₑ=ΣZᵢYᵢ, (N,Z)  │        │     Sobol grid, dt grid,    │
   │     graph/isotopes.py       │───────▶│     state_id, label noise   │
   │     configs/isotopes_*.yaml │        │     data/{schema,labels}.py │
   │     nb 01                   │        │     nb 01                   │
   └──────────────┬──────────────┘        └──────────────┬──────────────┘
                  │                                      │
                  ▼                                      ▼
═══════════════════════════════════════════════════════════════════════════════════
 TIER 1 — MICROPHYSICS  ✓ tier1.md       "where a single number λ_j(T,ρ,Yₑ) comes from"
═══════════════════════════════════════════════════════════════════════════════════

   ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
   │ S2  REACLIB RATES   │   │ S4  SCREENING       │   │ S5  WEAK SECTOR     │
   │ ⟨σv⟩, Gamow peak,   │   │ Debye–Hückel →      │   │ β∓/EC, FFN/Oda/LMP, │
   │ the 7-coeff fit     │   │ Chugunov 2007       │   │ (T, ρYₑ) tables     │
   │ fluxes/compile.py   │   │ fluxes/screening.py │   │ graph/network.py    │
   │ fluxes/engine.py    │   │                     │   │ crosscheck/mesa_dump│
   └──────────┬──────────┘   └──────────┬──────────┘   └──────────┬──────────┘
              │                         │                         │
              ▼                         │                         │
   ┌─────────────────────┐              │                         │
   │ S3  DETAILED BALANCE│              │                         │
   │ time-reversal, G(T),│              │                         │
   │ the T^{3/2ΔN} factor│              │                         │
   │ ⚠ gh-575 lives here │              │                         │
   │ fluxes/db_reverses  │              │                         │
   │ crosscheck/kappa.py │              │                         │
   └──────────┬──────────┘              │                         │
              └────────────┬────────────┴─────────────────────────┘
                           ▼
              ┌─────────────────────────────┐
              │ S6  RATE RECONCILIATION     │  ← the whole crosscheck/ package
              │ MESA ⟷ pynucastro, per rate │     + Fortran probe + nb 04
              └──────────────┬──────────────┘
                             ▼
═══════════════════════════════════════════════════════════════════════════════════
 TIER 2 — NETWORK ALGEBRA  ✓ tier2.md     "from rates to dY, exactly and conservatively"
                                         (+ Part 0: the astrophysics it is for)
═══════════════════════════════════════════════════════════════════════════════════

   ┌─────────────────────────────┐        ┌─────────────────────────────┐
   │ S7  STOICHIOMETRY + CONSERV.│        │ S8  FLUXES & CANCELLATION   │
   │ ν, A·ν=0, C, lepton ledgers,│───────▶│ f⁺,f⁻, φ=f⁺−f⁻, κ=|φ|/(f⁺+f⁻)│
   │ P = I − Cᵀ(CCᵀ)⁻¹C          │        │ fluxes/{engine,store}.py    │
   │ graph/{stoich,projector}.py │        │ fluxes/handshake.py         │
   │ nb 03  ⟵ THE FLOOR          │        │ nb 05                       │
   └──────────────┬──────────────┘        └──────────────┬──────────────┘
                  │                                      │
                  │        ┌─────────────────────────────┘
                  ▼        ▼
   ┌─────────────────────────────┐        ┌─────────────────────────────┐
   │ S9  EQUILIBRIUM: NSE / QSE  │        │ S10 STIFF INTEGRATION       │
   │ Saha, μ=Zμₚ+Nμₙ, cluster uᴳ,│        │ stiffness ratio, BDF,       │
   │ Guidry δ_r criterion        │        │ ∂R/∂Y, augmented [Y,Φ]      │
   │ qse/{coeffs,solver,diagn.}  │        │ fluxes/integrate.py         │
   │ nb 06                       │        │ nb 11                       │
   └──────────────┬──────────────┘        └──────────────┬──────────────┘
                  │                                      │
                  ▼                                      ▼
═══════════════════════════════════════════════════════════════════════════════════
 TIER 3 — ASTROPHYSICS & VERDICT  ⚠ NOT YET WRITTEN   "silicon burning, labels, decision"
═══════════════════════════════════════════════════════════════════════════════════

   ┌─────────────────────────────┐        ┌─────────────────────────────┐
   │ S11 bbq / MESA OPERATION    │───────▶│ S12 TRAJECTORIES & eps_nuc  │
   │ one-zone burner, hydrostatic│        │ integrated vs rate, stall = │
   │ mode, inlists, campaign     │        │ attractor arrival           │
   │ scripts/bbq_campaign/, nb 08│        │ data/trajectories.py, nb 07 │
   └──────────────┬──────────────┘        └──────────────┬──────────────┘
                  │                                      │
                  └──────────────┬───────────────────────┘
                                 ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │ S13 SILICON BURNING + THE LABEL PATHOLOGY  (the payoff node)         │
   │ photodisintegration rearrangement, Fe-peak, Yₑ as the CCSN observable│
   │ scripts/step6_label_nse_census.py, nb 09                             │
   └──────────────┬──────────────────────────────────────────────────────┘
                  ▼
   ┌─────────────────────────────┐        ┌─────────────────────────────┐
   │ S14 THE KILL-TEST           │        │ S15 THE ML TARGET           │
   │ active set, cond(S), churn, │───────▶│ Target A vs B, why decode-  │
   │ timescale separation        │        │ only, the NuGNN failure mode│
   │ killtest/*, nb 10           │        │ graph/projector.py, nb 11   │
   └─────────────────────────────┘        └─────────────────────────────┘
                                 ▲
   ┌─────────────────────────────┴───────┐
   │ S16 BASELINE: what you're beating   │  repro/nnn/, nb 02
   └─────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════
 TIER 4 — THE EMULATOR  ⚠ NOT YET WRITTEN     "the model, conditioning, training"
═══════════════════════════════════════════════════════════════════════════════════
   S17 backbone (3 edge types, GATv2, (Z,N) embedding, K = radius+2, 4 physics channels)
   S18 the mask as a learned L0 / hard-concrete gate
   S19 time conditioning (one model over 8 decades of Δt)
   S20 rollout stability (pushforward vs noise injection in a STIFF system; the governor)
   S21 losses under tail risk (CVaR / p99, Fe-peak weighting)
   S22 UQ, OOD, and the fallback-to-solver gate
                                          → sketched in tier1.md §VIII.E.1
```

---

## Cross-cutting nodes

Study once; they recur everywhere.

| Node | Files | Why |
|---|---|---|
| **Executable policy** | `fluxes/guards.py`, `tests/test_flux_guards.py` | Five physics gates encoded as code that refuses to run — an invariant that can't be forgotten. |
| **Package contracts** | every `__init__.py` | Each states a contract and often a prohibition. |
| **Notebook discipline** | `notebooks/phase0/nbsupport.py` | `caption()` raises if a figure cites no measured row; the κ helper requires a declared convention. |
| **Progress dashboard** | `notebooks/phase0/00-phase0-map.ipynb` | The live DAG with status. |
| **Sanity** | `tests/test_imports.py`, `tests/conftest.py` | Why the conservation gate is never skipped. |

---

## Sequencing

| Pass | Stages | Focus |
|---|---|---|
| 1 | S0 → S1 → S7 | Ends where you can read every assertion in `tests/test_conservation.py`. Read `tier2.md` Part 0 first — it is the astrophysical context all of Tier 2 assumes. |
| 2 | S2 → S3 → S4 → S5 → S6 | Heaviest derivation load. S3 is the load-bearing one. |
| 3 | S8 → S9 → S10 | The κ error-amplification inequality and the Saha derivation, cold. |
| 4 | S11 → S12 → S13 → S14 → S15 | S16 anywhere. |

Tier 2's three keepers, if you carry nothing else out of it: conservation is a
**rank statement** (left-nullity of ν̃ is exactly 3 and equals rowspace(C));
**κ = |tanh(𝒜/2kT)|** unifies the detailed-balance, condition-number and
thermodynamic readings; and **stiffness, QSE and cancellation are one
phenomenon** seen from three sides.

Running things while you study: `uv run pytest -q` for the full suite. The
notebooks all execute headless in ~94 s total, but run
`uv run nbstripout --install` once first so outputs never land in git. Anything
touching `compile_network` is multi-minute — notebook 11 gates those cells
deliberately.
