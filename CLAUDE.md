# gnn-nucleosynthesis — Claude Code project memory

Conservation-by-construction GNN emulator of silicon burning (MESA/bbq, mesa_80/mesa_151),
benchmarked against the Grichener et al. 2025 NNN (ApJS 279, 49; Zenodo 14873443;
MESA r23.05.1 + bbq). Closest competitor: NuGNN (Kim et al. 2026, arXiv:2606.04491).
Primary target = **Target A**: signed net per-reaction flux φ mapped through the fixed
stoichiometric matrix, dY = ν φ. Fallback = **Target B**: direct dY in a **linear**
output space with additive null-space projection P = I − Cᵀ(CCᵀ)⁻¹C.

## Environment policy (STRICT)

- This project is managed with **uv only**. NEVER initialise, activate, or suggest conda.
- Run all Python via `uv run <cmd>`. Install deps via `uv add` / `uv sync`. Never `pip install`.
- MESA / bbq are external Fortran source builds, not Python packages — they are driven
  through shell scripts, never through a package manager.
- If a dependency genuinely cannot be resolved by uv/PyPI, STOP and ask the user before
  reaching for any other package manager.

## Commands

- Sync env:            `uv sync`
- All tests:           `uv run pytest -q`
- Lint:                `uv run ruff check .`
- Conservation gate:   `uv run pytest tests/test_conservation.py -q`
- Export ν matrix:     `uv run python scripts/export_stoich_matrix.py --net mesa80`
- Drift diagnostics:   `uv run python scripts/check_conservation.py data/stoich/nu_mesa80.npz`
- Kill-test skeleton:  `uv run python scripts/run_killtest.py --help`
- Zenodo manifest:     `uv run python scripts/download_zenodo.py` (metadata only by default)
- MESA scaffold:       `bash scripts/install_mesa.sh` (check mode; downloads nothing)
- Fetch paper source:  `uv run python scripts/fetch_arxiv_source.py <arxiv-id> --meta`
                       (literature is read as TeX source from data/literature/,
                        never by parsing PDFs; PDF-only papers → arxiv.org/html/)
- LaTeX build:         `latexmk -pdf -cd docs/<paper>/main.tex` where `<paper>` ∈
                       {project-scope, gnn-architecture, qse, training-data}
                       (LaTeX rules in docs/CLAUDE.md)

## Non-negotiable physics invariants

These are testable facts, not preferences. Code that violates them is wrong by definition.

1. **Exact conservation by construction.** For Target A, dY = ν φ must satisfy
   |Σᵢ Aᵢ dYᵢ| ≤ 1e-12 and charge-to-lepton closure |Σᵢ Zᵢ dYᵢ + dN_lep| ≤ 1e-12 per step
   in float64 **for ANY φ, including a randomly initialised untrained network**.
   `tests/test_conservation.py` enforces this. If it fails, the ν export is wrong;
   training must not begin until fixed.
2. **Weak-reaction columns are NEVER eligible for the equilibrium mask.** β-decays and
   electron captures are not in detailed-balance equilibrium in this regime. Masking any
   weak column is a correctness bug, full stop.
3. **The physical signal must survive:** dYₑ through weak reactions
   (Σ_{j∈weak} (Σᵢ Zᵢ νᵢⱼ) φⱼ) must be nonzero and accurate. A design that zeroes it to
   make the drift residuals vanish is wrong.
4. **Conservation lives in the decode step, never inside latent dynamics.** The decoded
   native output is the linear conserved quantity (φ for Target A, dY for Target B).
   No nonlinear transform may sit between the conservation map and the output.
   Target B's null-space projection is only valid in a LINEAR output space
   (the NuGNN signed-log failure mode is documented and must not be repeated).
5. **Energy consistency:** e_nuc = Σⱼ Qⱼ(T) φⱼ from the SAME net fluxes as composition;
   flux-route vs composition-route residual ≤ 1% of |e_nuc| across the 3–4 GK band.

## Hard numeric gates (do not change without an entry in RESULTS.md)

- Conservation unit test: with a *randomly initialized* flux head, baryon drift
  |Σᵢ Aᵢ dYᵢ| ≤ 1e-12 and charge-to-lepton closure ≤ 1e-12 per step in float64, while
  dYₑ through weak columns is nonzero. Training never starts until this passes.
  Across φ magnitude scales 1e-20…1e0 the test bounds drift by
  max(1e-12·s, 1e-13·G), s = min(1, max|φ|), G = |A|·(|ν|·|φ|) — the absolute
  1e-12 gate at O(1) scale, relative-to-gross at the small end where an absolute
  bound is vacuous (Step-3 brief; RESULTS.md 2026-07-08; tests/test_conservation.py
  module docstring). Column drifts measured exactly 0.0.
- Operative per-step accuracy gate: |ΔYₑ| ≲ 3e-6 per step (systematic/linear accumulation
  assumption, N ≈ 1.6e3 steps), held until the accumulation slope is MEASURED
  (see docs/phase0-checklist.md): slope ≈ 1 → keep/tighten; slope ≈ 0.5 (random-walk)
  → may relax toward ~5e-5.
- End-to-end Yₑ physics floor: 5e-3 to 1.5e-2 per trajectory (FFN→LMP anchor).
- κ/flux construction gate (Step 4, RESULTS.md 2026-07-10): every κ_r or flux
  computation builds reverse rates as pynucastro DerivedRate(use_pf=True) or takes
  MESA-side rates — raw JINA v-flag reverses are FORBIDDEN at T9 ≥ 3 (pf-free fits
  manufacture spurious κ floors up to 0.8 at NSE; docs/rate-crosscheck.md §κ-floor).
- Kill-test thresholds: Target A viable if the active set {r : κ_r > 0.1} carries ≥95%
  of |ΔYₑ| (and of |ΔX| for dominant isotopes) at the median timestep; FAIL if net flow
  spreads over >~30% of reactions near the κ floor. cond(S_active) < 1e6 pass,
  > 1e8 fail (between: judgement call, logged in RESULTS.md). Guidry equilibrium
  criterion |y − ȳ|/ȳ < ε, ε sweep {3e-3, 1e-2, 3e-2}.
- Switch Target A → Target B if cond(S_active) > 1e6, or if >~90% of reactions carry
  net flux below the Yₑ floor at the median timestep.
- Guidry mask: freeze to imposed-Guidry mask if the learned gate regresses validation
  |ΔYₑ| by >2× over three seeds or churn >5%/step.
- Size-transfer falsifier: zero-shot mesa_151 Yₑ error > 2× mesa_80-internal error ⇒
  report as size-ADAPTABLE (few-shot), not size-TRANSFERABLE.
- Sobol→real-MESA: retrain with trajectory-aware sampling if real-track 99th-pct Yₑ
  error > 3× the Sobol-measured value.
- Energy consistency: flux-route vs composition-route e_nuc residual ≤ 1% of |e_nuc|
  across the 3–4 GK band.

## Physics conventions

- Weak-reaction columns are NEVER masked by the equilibrium gate (β-decays/EC are not
  in detailed balance here; masking one is by definition a bug). The eligible set is
  built structurally from `weak_mask` at construction time, not by convention.
- Lepton bookkeeping: constraint matrix C has a baryon row (Aᵢ), a charge row including
  the electron column (Zᵢ for nuclei, −1 electron, 0 neutrino), and a lepton-number row
  (e⁻ +1, ν +1, ν̄ −1). Weak reactions change Z at fixed A; Yₑ = Σᵢ Zᵢ Yᵢ must evolve.
- All conservation checks in float64. asinh/signed-log transforms are internal latents
  only — never the space where a sum constraint or projection is evaluated (the NuGNN
  failure mode).
- Regime box: T = 1.6–7.9 GK (1e9.2–1e9.9 K), ρ = 1e7–1e9 g/cm³, 0.45 < Yₑ < 0.5.
  QSE onset ~3–3.3 GK; kill-test priority window 3.3–5 GK. High-Yₑ bottleneck reaction
  to instrument: ⁴⁵Sc(p,γ)⁴⁶Ti — **mesa_151 only** (⁴⁵Sc is absent from mesa_80, whose
  only Sc is ⁴³Sc; mesa_80 bridge reactions must be discovered empirically in the
  kill-test). See RESULTS.md 2026-07-08.
- Isotope lists: exactly 80/151 species; ⁴¹Ca is present in BOTH networks (the paper's
  App. A table omits it — paper typo; the data headers are authoritative).
- mesa_80 weak sector is materially thinner than mesa_151: only 6/9 EC controllers and
  0/8 β-decay partners of the Yₑ-controller set (RESULTS.md membership table). Feeds
  size-transfer and loss-weighting design.

## Engineering conventions

- Every derived quantity carries a **sourced / derived / measured** tag.
- Measured numbers go to `RESULTS.md` with date, code version (commit hash), and data
  provenance; docs and papers cite RESULTS.md rows, never bare numbers.
- Tests before implementation for anything with a physics oracle.
- Notebooks are exploratory only; promoted to `src/` + `scripts/` when stable.
- No large data in git: `data/**` is ignored except `data/MANIFEST.yaml`.

## Docs-while-implementing contract

- **Docs are the spec.** If code and `docs/` disagree, stop, flag it, and resolve
  explicitly — never silently "fix" the docs to match the code.
- Any change to the conservation map, equilibrium mask, feature set, loss, temporal head,
  or any gate/threshold above MUST update the corresponding file under `docs/` in the
  same commit (delegate to the `docs-sync` subagent).
- Every settled design decision gets a short ADR in `docs/decisions/` (see the template).
- Every numeric claim in docs must be labelled **sourced** (citation), **derived**
  (from a script in `scripts/`), or **assumed** (with the retirement plan). The `referee`
  subagent enforces this.
- Novelty re-check against arXiv is REQUIRED at every phase boundary
  (`novelty-checker` subagent → dated report in `docs/novelty/`).

## Repo map

- `src/gnn_nucleo/`  main package: graph export, fluxes, QSE, kill-test, data schema.
                     `gnn_nucleo/graph/` holds ν export, constraint matrices,
                     projection, drift diagnostics — conservation-critical; edits
                     there auto-trigger the gate hook (superseded the old
                     `src/conservation/` stub in Step 3, ADR 0002)
- `tests/`           pytest suite; conservation gate is the floor
- `scripts/`         reproducible entry points (every derived number in docs comes from here)
- `configs/`         run/experiment configuration files
- `docs/`            living spec, phase-0 checklist, ADRs, novelty reports, archived
                     reports, and the LaTeX papers (`docs/<paper>/main.tex`) —
                     documentation rules in docs/CLAUDE.md
- `notebooks/`       exploratory only; promoted to src/ when stable
- `data/`            local data (gitignored except `data/MANIFEST.yaml`);
                     `data/zenodo/` is READ-ONLY raw ground truth (never edit);
                     `data/literature/` is a gitignored TeX-source cache of papers
- `RESULTS.md`       append-only measured-numbers log with provenance

## Subagents (in .claude/agents/)

- `docs-sync`        updates docs after implementation changes (no Bash access)
- `physics-auditor`  runs conservation/drift/kill-test checks, returns numbers only
- `test-runner`      runs pytest, reports only failures
- `referee`          hostile review of claims vs code vs labels (read-only)
- `novelty-checker`  arXiv sweep at phase boundaries

## Style

- Python ≥3.11 (env pinned at 3.14), type hints on public functions, numpy-style docstrings.
- float64 for anything touching conservation or the Xₜ₊Δₜ update; float32 allowed in
  model internals only.
- No new abstractions until used twice. Prefer plain functions over classes for scripts.
