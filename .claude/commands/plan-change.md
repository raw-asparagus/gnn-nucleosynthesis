---
description: Plan a change against a physics invariant or gate before writing any code
argument-hint: <what you want to change>
---

Plan — do not implement — the following change: **$ARGUMENTS**

This repo's failure mode is a change that is locally reasonable and globally wrong:
it passes tests, and silently violates an invariant or drifts from the spec. Plan
accordingly, in this order.

1. **Read the spec before the code.** Find the `docs/` section that governs this
   component and the ADR in `docs/decisions/` that settled it. Docs are the spec: if
   the change contradicts a documented decision, the deliverable is a superseding ADR,
   not an edit.
2. **Name the invariants in scope.** From CLAUDE.md "Non-negotiable physics invariants"
   and "Hard numeric gates", list the specific ones this change can break. Say for each
   whether it is measured by an existing test/script, or has no instrument.
3. **State the oracle.** CLAUDE.md requires tests before implementation for anything
   with a physics oracle. Name the test that would fail if this change were wrong,
   and whether it exists yet.
4. **Delegate the reconnaissance you need**, per CLAUDE.md's delegation policy —
   `physics-auditor` for current measured numbers, `Explore` for where a concept lives,
   `lit-fetch` for what a cited paper actually says. Do not guess numbers from memory.
5. **Produce the plan**: files to touch, order, the docs/ADR updates that must land in
   the same commit, and the verification step that closes it.

Stop at the plan. Present it and wait.
