---
description: Hostile audit of claims vs code vs sources, with citation verification
argument-hint: [file or component, e.g. docs/qse/main.tex]
---

Audit the claims in: **$ARGUMENTS** (default: all of `docs/`).

1. Delegate to `referee` — read-only adversarial review. Label discipline
   (sourced/derived/assumed), invariant hunt, claim↔code agreement, staleness.
2. For every `UNVERIFIED-SOURCE` finding the referee returns, delegate to `lit-fetch`
   with the arXiv id and the exact claim. The referee cannot fetch; that gap is what
   `lit-fetch` exists to close, so do not let an UNVERIFIED-SOURCE finding stand
   unresolved when an id is available.
3. Merge the results into one severity-ordered list: BLOCKING / MAJOR / MINOR, each
   with a `file:line` reference and the exact quoted claim, and each citation marked
   VERIFIED / MISCITED / NOT FOUND.

Findings only — no fixes in this pass. End with the referee's one-line verdict.
An empty findings list is suspicious; if there genuinely is nothing, say what was
checked.
