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
