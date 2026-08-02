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

**Standing open items** live in [`tier1.md` Part VIII](tier1.md#part-viii--open-prerequisites-what-is-still-not-covered)
— the cross-tier register, not Tier-1-specific. Two audit passes so far: §VIII.C
(physics the code implements) and §VIII.E (the project's spec documents vs this
map). Priorities in §VIII.F.

⚠ **The map below stops at Tier 3.** The emulator itself — Components A, C, D of
`docs/reports/consolidated-gnn-architecture.md`, and most of B — has **no node**,
and `docs/architecture/` (the named living spec) is empty. A sketched Tier 4
(S17–S22: backbone, learned mask, time conditioning, rollout stability, tail-risk
losses, UQ/OOD) is in [§VIII.E.1](tier1.md#viiie1-the-model-side-has-no-study-node-at-all).
Four of the eight open Phase-0 checklist rows are Tier-4 measurements.

One file per tier — everything needed before Tier 1, read top to bottom.

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
 TIER 0 — SUBSTRATE                      "what is a nuclear network, what is the data"
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
 TIER 1 — MICROPHYSICS                   "where a single number λ_j(T,ρ,Yₑ) comes from"
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
 TIER 2 — NETWORK ALGEBRA                "from rates to dY, exactly and conservatively"
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
 TIER 3 — ASTROPHYSICS & VERDICT         "silicon burning, the labels, the decision"
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
| 1 | S0 → S1 → S7 | Ends where you can read every assertion in `tests/test_conservation.py`. |
| 2 | S2 → S3 → S4 → S5 → S6 | Heaviest derivation load. S3 is the load-bearing one. |
| 3 | S8 → S9 → S10 | The κ error-amplification inequality and the Saha derivation, cold. |
| 4 | S11 → S12 → S13 → S14 → S15 | S16 anywhere. |

Running things while you study: `uv run pytest -q` for the full suite. The
notebooks all execute headless in ~94 s total, but run
`uv run nbstripout --install` once first so outputs never land in git. Anything
touching `compile_network` is multi-minute — notebook 11 gates those cells
deliberately.
