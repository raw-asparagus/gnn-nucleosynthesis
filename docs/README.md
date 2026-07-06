# docs/ — living specification

Docs are the SPEC: if code and docs disagree, stop and resolve explicitly.

Layout:
- architecture/      per-component spec files split from the consolidated reports
                     (backbone.md, output-heads-conservation.md, temporal-rollout.md,
                     data-generation.md). Split the big reports into these; the
                     docs-sync agent edits these small files, not the monoliths.
- phase0-checklist.md  the living Phase-0 measurement program (tick as measured)
- decisions/         short ADRs, numbered, one settled decision each
- novelty/           dated arXiv novelty-check reports (novelty-checker output)
- reports/           ARCHIVE: the four consolidated research reports, verbatim.
                     Read-only reference; never edited to track code changes.

Label every numeric claim: **sourced** / **derived** (name the script) /
**assumed** (with retirement plan).
