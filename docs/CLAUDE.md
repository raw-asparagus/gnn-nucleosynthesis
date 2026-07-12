# docs/ — documentation rules for Claude Code

These rules govern every edit under `docs/`. They exist because this project's docs
came out of multiple adversarial audit cycles; the value of the docs is that every
claim in them is traceable and every threshold is falsifiable. Do not erode that.

## Rule 0 — docs are the spec

If code and docs disagree, the docs win until a human decides otherwise. Never
"fix" a doc to match code behaviour without an explicit instruction; report the
conflict and stop. The one exception is recording a *measurement* (see Rule 3).

## Rule 1 — every number carries a label

Every numeric claim must be tagged with exactly one of:

- **sourced** — carries a citation (paper + where in it). Do not launder a derived
  or assumed number into a citation's vicinity so it reads as sourced.
- **derived** — names the script in `scripts/` (and, where relevant, the data file)
  that produces it. A derived number with no producing script is a defect: either
  write the script or relabel as assumed.
- **assumed** — an internal estimate, stated with its retirement plan (usually a
  Phase-0 checklist item). Known standing examples that must NEVER appear as
  sourced: the "6–8 orders of magnitude" timescale separation (RETIRED by
  measurement 2026-07-12 — not supported on the label manifold; see the
  phase0-checklist retirement note and RESULTS.md 2026-07-12; the entry stays
  here as the canonical example of the rule), the 0.1–0.5
  CPU-hr/sample cost, GPU training-time estimates, the per-step Yₑ budget
  derivation (the floor's *anchor* is sourced; the per-step translation is an
  inference under a stated accumulation model).

Verification of sourced claims uses the TeX source cache: fetch with
`scripts/fetch_arxiv_source.py`, read from `data/literature/<id>/src/`.
The cache is ephemeral and uncommitted — cite the paper, never the snapshot.

When editing near a number, preserve its label. When a label is missing, add the
correct one rather than deleting the number.

## Rule 2 — thresholds must have instruments

Any gate or switch condition written into docs (e.g. per-step |ΔYₑ| ≲ 3e-6,
cond(S_active) > 1e6, mask churn > 5%/step, 2× transfer falsifier, 3× Sobol
trigger) must reference the test, script, or checklist item that measures it.
A threshold with no measuring instrument is a finding the `referee` agent will
raise — pre-empt it.

## Rule 3 — recording measurements

When a Phase-0 quantity is measured:
1. Fill the row in `phase0-checklist.md`: value, date, producing script.
2. If the measurement moves an operative gate or reverses a decision, update the
   root `CLAUDE.md` gate section AND write/supersede an ADR — in the same commit.
3. Never overwrite the previous value silently; if a measurement is redone, keep
   the history in the checklist row or the ADR.

## Rule 4 — ADRs (`decisions/`)

- One settled decision per file, numbered `NNNN-short-title.md`, using the template
  in `decisions/README.md` (Decision / Basis with labels / Switch condition).
- Accepted ADRs are immutable: never rewrite one — supersede it with a new ADR that
  sets the old one's Status to `superseded by NNNN`.
- Every ADR must state its switch condition: the measured threshold at which the
  decision reverses. "We chose X" without "we abandon X when Y" is incomplete.

## Rule 5 — the archive is read-only

`reports/` holds the four consolidated research reports verbatim. They are the
audit trail, not living docs: never edit them to track code, never delete their
caveats, never quote them as if they reflect the current implementation. The
living spec is `architecture/`; when splitting report content into it, copy —
don't move — and adapt tense ("the design proposes" → "the code does") only when
the code actually does it.

## Rule 6 — novelty reports (`novelty/`)

- Written only by the `novelty-checker` agent (or a human), named
  `YYYY-MM-DD-novelty-check.md`, append-only.
- An inconclusive sweep is recorded as inconclusive — never rounded up to
  "novelty confirmed". A THREAT verdict must be surfaced to the user, not just filed.

## Rule 7 — caveats are load-bearing

Audit caveats, "hypothesis, not established" hedges, and sourced-vs-inferred
distinctions (e.g. size transfer is a hypothesis; the rollout governor is an
out-of-regime transfer; Farmer 2016's "30%" interpretation is unconfirmed) are
part of the content. Do not tighten, soften, or delete them while editing for
style. If a caveat has been retired by a measurement, retire it via Rule 3 with
the evidence named.

## Rule 8 — style

- Prose-first; tables only for genuinely tabular content (checklists, rate-table
  comparisons, gates). Keep files small and per-component so `docs-sync` edits
  stay targeted.
- Isotope notation: `⁵⁵Co` in prose docs, `co55` in anything code-adjacent
  (matching pynucastro names). Yₑ, ν, φ as in the reports.
- Cite as: Author(s) year, journal/arXiv id — enough for the `referee` to verify.
- No marketing language. "First", "novel", and "state of the art" claims belong
  only in novelty reports and paper drafts, backed by a dated sweep.

## Rule 9 — LaTeX papers

The papers live at `docs/{project-scope,gnn-architecture,qse,training-data}/main.tex`
(built with `latexmk -pdf -cd docs/<paper>/main.tex`).

- Never edit generated files (.aux, .bbl, .fls, .fdb_latexmk, .synctex.gz, build/).
- Every numeric claim in a paper draft must trace to a script in `scripts/` or a
  citation (Rule 1 applies to .tex exactly as to .md); run the `referee` agent on
  drafts before sharing.
- Figures are generated by scripts into the paper's `figures/` directory —
  regenerate, do not hand-edit.

## Division of labour

- `docs-sync` agent: edits `architecture/`, `phase0-checklist.md`, `decisions/`.
- `novelty-checker` agent: writes `novelty/` only.
- `referee` agent: read-only enforcement of Rules 1–7.
- Nothing under `docs/` is edited by the `physics-auditor` or `test-runner` agents.
