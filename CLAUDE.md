# gnn-nucleosynthesis — Claude Code project memory

Conservation-by-construction GNN emulator of silicon burning (MESA/bbq, mesa_80/mesa_151),
benchmarked against the Grichener et al. 2025 NNN (ApJS 279, 49; Zenodo 14873443).
Closest competitor: NuGNN (Kim et al. 2026, arXiv:2606.04491).

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
- Conservation gate:   `uv run pytest tests/test_conservation.py -q`
- Export ν matrix:     `uv run python scripts/export_stoich_matrix.py --net mesa80`
- Drift diagnostics:   `uv run python scripts/check_conservation.py data/stoich/nu_mesa80.npz`
- Kill-test skeleton:  `uv run python scripts/run_killtest.py --help`
- Fetch paper source:  `uv run python scripts/fetch_arxiv_source.py <arxiv-id> --meta`
                       (literature is read as TeX source from data/literature/,
                        never by parsing PDFs; PDF-only papers → arxiv.org/html/)
- LaTeX build:         `latexmk -pdf -cd tex/main.tex`

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

## Operative accuracy gates (until Phase-0 measurements say otherwise)

- Per-step |ΔYₑ| ≲ 3e-6 (systematic/linear accumulation assumed; the accumulation model
  is MEASURED, not assumed — see docs/phase0-checklist.md).
- End-to-end trajectory floor: ΔYₑ ≈ 5e-3 (working point).
- Switch Target A → Target B if cond(S_active) > 1e6, or if >~90% of reactions carry
  net flux below the Yₑ floor at the median timestep.
- Guidry mask ε sweep: {3e-3, 1e-2, 3e-2}; freeze to imposed-Guidry mask if the learned
  gate regresses validation |ΔYₑ| by >2× over three seeds or churn >5%/step.
- Size-transfer falsifier: zero-shot mesa_151 Yₑ error > 2× mesa_80-internal error ⇒
  report as size-ADAPTABLE (few-shot), not size-TRANSFERABLE.
- Sobol→real-MESA: retrain with trajectory-aware sampling if real-track 99th-pct Yₑ
  error > 3× the Sobol-measured value.

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

- `src/`             implementation (see src/CLAUDE.md)
- `src/conservation/` ν export, constraint matrices, projection, drift diagnostics —
                      conservation-critical; edits here auto-trigger the gate hook
- `tests/`           pytest suite; conservation gate is the floor
- `scripts/`         reproducible entry points (every derived number in docs comes from here)
- `docs/`            living spec, phase-0 checklist, ADRs, novelty reports, archived
                     reports — documentation rules in docs/CLAUDE.md
- `tex/`             LaTeX papers (see tex/CLAUDE.md)
- `data/`            local data; `data/zenodo/` is READ-ONLY raw ground truth (never edit);
                     `data/literature/` is a gitignored TeX-source cache of papers

## Subagents (in .claude/agents/)

- `docs-sync`        updates docs after implementation changes (no Bash access)
- `physics-auditor`  runs conservation/drift/kill-test checks, returns numbers only
- `test-runner`      runs pytest, reports only failures
- `referee`          hostile review of claims vs code vs labels (read-only)
- `novelty-checker`  arXiv sweep at phase boundaries

## Style

- Python ≥3.11, type hints on public functions, numpy-style docstrings.
- float64 for anything touching conservation or the Xₜ₊Δₜ update; float32 allowed in
  model internals only.
- No new abstractions until used twice. Prefer plain functions over classes for scripts.
