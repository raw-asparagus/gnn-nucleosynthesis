# 0003 — Reaction set reconciled against MESA r23.05.1; provisional flag retired
Date: 2026-07-09    Status: accepted

## Decision
The pynucastro rate collection is now reconciled against MESA r23.05.1's
softwired nets (the label-generating configuration) and
`provisional_reaction_set` flips to False on both networks. Three changes,
all in `src/gnn_nucleo/graph/network.py` and driven by machine-readable
disposition files:

1. **Tabular ordering** `DEFAULT_TABULAR_ORDERING` becomes
   `suzuki < pruet_fuller < ffn < oda < langanke` (later wins), reproducing
   MESA weaklib's per-pair precedence LMP > Oda > FFN with
   `use_suzuki_weak_rates=.false.` — the configuration the Zenodo training
   labels were generated with (empty `&nuclear` namelist ⇒ bbq defaults).
   The pre-Step-4 suzuki-topped ordering disagreed with MESA on 14 (mesa_80)
   / 23 (mesa_151) sd-shell pairs (A = 17–28), all `MESA=OHMT vs
   pyna=suzuki`; after the reorder, zero weak-table source mismatches remain.
2. **PYNA_ONLY drops**: `build_rate_collection(disposition="auto")` reads
   `configs/reaction_disposition_<net>.yaml` and drops the channels MESA
   does not softwire — 3 in mesa_80 (p+be9 ⇄ n+p+he4+he4 both directions,
   n+p+he4+he4 → he3+li7) and those plus n16 → c12+he4 (β⁻-delayed α,
   wc12) in mesa_151. Post-drop counts equal MESA's exactly:
   **607 / 1518 reactions** (were 610 / 1522).
3. **Provenance**: `BuildInfo`/npz gain `disposition_sha256` and
   `n_dropped`; `provisional_reaction_set=False` is set if and only if a
   disposition file with zero MESA_ONLY entries was applied (`load_drop_list`
   fails loud otherwise).

MESA_ONLY = 0 on both networks — the graphs were a strict superset of
MESA's sets; no physics had to be added.

## Basis
- measured: reaction-set diff on canonical sorted-multiset keys (with
  lepton-channel disambiguation for the pp/pep split),
  `scripts/reconcile_reactions.py`, RESULTS.md 2026-07-09. MESA-side
  inventory extracted by the `src/mesa_probes/` Fortran driver (`dump_net`)
  from the actual softwired nets.
- measured: post-reconciliation conservation gate + projector tests pass at
  unchanged tolerances; column drifts exactly 0.0 (RESULTS.md 2026-07-09).
- sourced: MESA weaklib precedence and blend controls,
  `$MESA_DIR/rates/public/rates_def.f90`; training-label bbq configuration
  from the Zenodo generator scripts (empty `&eos`/`&nuclear` namelists).
- Remaining MATCHED_DIFF_PROVENANCE entries (28 / 32 construction
  direction-swaps: MESA and pynucastro disagree on which member of a
  forward/reverse pair is the REACLIB fit vs detailed-balance-derived —
  REACLIB snapshot difference; plus be7→li7 EC: MESA uses the shipped
  S13 table, pynucastro a REACLIB fit) are rate-VALUE concerns carried
  into the Task-2 numerical cross-check, not membership defects.

## Switch condition
Reverse (rebuild from MESA net-definition files directly, per ADR 0002's
escape hatch) if the Task-2 rate cross-check or the Task-3 κ-floor screen
shows the pynucastro-sourced rates for MATCHED_CLEAN channels deviating from
MESA beyond the stated bands (|Δlog10| > 0.004 for strong/EM forwards) in a
way that is material to κ_r or kill-test conclusions. Re-run
`scripts/reconcile_reactions.py` after any pynucastro upgrade or MESA
version change; a nonzero MESA_ONLY tally re-blocks the build.
