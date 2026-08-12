---
description: Run the mandatory phase-boundary checks (novelty sweep + hostile audit)
argument-hint: [phase name or step number]
---

Run the phase-boundary protocol for: **$ARGUMENTS**

CLAUDE.md makes the novelty re-check MANDATORY at every phase boundary. Run the
independent checks concurrently, then reconcile.

1. Delegate to `novelty-checker`: full arXiv sweep, dated report written to
   `docs/novelty/`. Pass it the phase name so the report says what it gated.
2. Delegate to `referee` in parallel: hostile review of everything the phase
   produced — claims vs code, sourced/derived/assumed labelling, invariant hunt.
3. Delegate to `physics-auditor` in parallel: re-run the conservation gate and the
   drift diagnostics so the phase closes on freshly executed numbers, not remembered
   ones.

Then, in the main thread:

4. Reconcile. A `referee` finding that a gate has no measuring instrument, or a
   `novelty-checker` THREAT verdict, blocks the phase boundary — surface it to the
   user in the first line of your summary rather than filing it.
5. Route any `UNVERIFIED-SOURCE` finding to `lit-fetch` to resolve.
6. Delegate to `docs-sync` to tick the completed rows in `docs/phase0-checklist.md`
   and record measured values with their dates and producing scripts.

Report: novelty verdict per leg, blocking findings first, then the checklist delta.
