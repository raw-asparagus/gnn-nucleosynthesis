# Reaction-set reconciliation: pynucastro graphs vs MESA r23.05.1 (Step 4, Task 1)

Derived: `scripts/reconcile_reactions.py` (MESA side extracted by
`src/mesa_probes/mesa_probe dump_net` from the softwired `mesa_80.net` /
`mesa_151.net`), 2026-07-09. Machine-readable results:
`configs/reactions_mesa{80,151}_mesa.yaml` (MESA inventories) and
`configs/reaction_disposition_mesa{80,151}.yaml` (dispositions). Decision
record: ADR 0003. Measured rows: RESULTS.md 2026-07-09.

## Counting convention (fixed BEFORE diffing)

- One reaction = one **directed** canonical key: sorted reactant and product
  multisets in project chem ids (`al25*1+neut*1=>al26*1`). Forward and
  reverse are distinct reactions on both sides — MESA softwires them as
  separate entries and pynucastro derives reverse rates as separate Rate
  objects, so no forward/reverse counting mismatch is possible under this
  convention.
- Electrons/neutrinos are not part of the key (weak reactions are identified
  by their nuclide transition; lepton bookkeeping lives in C). Where one
  inventory carries two lepton channels of the same transition (pp vs pep:
  `h1*2=>h2*1`), the colliding keys get an `;ec`/`;wk` channel tag — the
  only such split in either network.
- Canonical counts under this convention: **MESA 607 / pynucastro 610**
  (mesa_80) and **MESA 1518 / pynucastro 1522** (mesa_151). The apparent
  Step-3 vs MESA count gap is real physics content, not convention.

## Disposition tallies (raw pre-Step-4 graph vs MESA)

| network | MESA | pyna | MATCHED_CLEAN | MATCHED_DIFF_PROVENANCE | MESA_ONLY | PYNA_ONLY |
| --- | --- | --- | --- | --- | --- | --- |
| mesa_80 (original ordering) | 607 | 610 | 565 | 42 (14 weak-table + 28 construction) | 0 | 3 |
| mesa_151 (original ordering) | 1518 | 1522 | 1463 | 55 (23 weak-table + 32 construction) | 0 | 4 |
| mesa_80 (adopted ordering) | 607 | 610 | 579 | 28 (construction only) | 0 | 3 |
| mesa_151 (adopted ordering) | 1518 | 1522 | 1486 | 32 (construction only) | 0 | 4 |

**MESA_ONLY = 0 on both networks**: the pynucastro graphs were a strict
superset — nothing had to be added, so the headline Step-4 risk (labels
containing physics the graph lacks) did not materialize.

## PYNA_ONLY — dropped from the graphs (ADR 0003)

| key | pyna rate | why MESA lacks it |
| --- | --- | --- |
| `be9*1+h1*1=>h1*1+he4*2+neut*1` | p_Be9_to_n_p_He4_He4 (cf88) | not softwired in either net |
| `h1*1+he4*2+neut*1=>be9*1+h1*1` | n_p_He4_He4_to_p_Be9 (cf88) | ditto (reverse) |
| `h1*1+he4*2+neut*1=>he3*1+li7*1` | n_p_He4_He4_to_He3_Li7 (mafo) | MESA carries only the he3+li7 → n+p+he4+he4 direction |
| `n16*1=>c12*1+he4*1` (mesa_151) | N16_to_He4_C12 (wc12) | β⁻-delayed α of ¹⁶N; MESA does not softwire it |

All four are light-nuclide channels far from the Yₑ-controller sector;
dropping them changes mesa_151's weak census from 174 to 173 columns
(β⁻ 85 → 84) and leaves mesa_80's weak sector untouched.

## Weak-table provenance (the ordering fix)

Under the pre-Step-4 suzuki-topped ordering, 14 / 23 matched weak pairs used
Suzuki tables where MESA weaklib uses OHMT (Oda) — every one an sd-shell
nuclide with A = 17–28 (o17…si28), exactly Suzuki et al.'s coverage.
MESA r23.05.1 + bbq defaults (the training-label configuration, empty
`&nuclear` namelist) run `use_suzuki_weak_rates=.false.` with weaklib
precedence LMP > Oda > FFN. `DEFAULT_TABULAR_ORDERING` is now
`suzuki < pruet_fuller < ffn < oda < langanke` (later wins), after which
**zero weak-table source mismatches remain** — every matched weak pair uses
the same table family as the labels. Per-pair sources on the MESA side are
parsed from the entry headers of
`$MESA_DIR/data/rates_data/weakreactions.tables`.

## MATCHED_DIFF_PROVENANCE — carried into Task 2 (rate cross-check)

- **Construction direction-swaps (28 mesa_80 / 32 mesa_151, = 14 / 16
  forward-reverse pairs):** for pairs like ¹³C(p,n)¹³N ⇄ ¹³N(n,p)¹³C, MESA's
  REACLIB snapshot (jina 20171020) and pynucastro 2.12.0's snapshot disagree
  on which direction is the fitted rate and which is detailed-balance
  derived. Membership is identical; the *values* can differ where JINA
  refits changed, so all these channels are flagged for the numerical
  comparison with a looser stated band.
- **be7 → li7 EC:** MESA evaluates it from the shipped
  `rate_tables/S13_r_be7_wk_li7.h5` table (weaklib-managed); pynucastro uses
  a REACLIB `ec` fit. Genuine provenance difference — compared numerically
  in Task 2; ⁷Be is peripheral to the silicon-burning Yₑ sector.
- **he4*2=>h1*1+li7*1 (`r_he4_ap_li7`):** MESA evaluates it outside its
  REACLIB dictionaries (`source=other`, one per net); pynucastro derives it
  from the ⁷Li(p,α)α fit. Compared numerically in Task 2.

## Post-disposition state (measured, RESULTS.md 2026-07-09)

Regenerated graphs: mesa_80 607 reactions (569 ReacLib + 38 tabular, 46
weak), mesa_151 1518 (1354 + 164, 173 weak); flux-head output dims change
610 → 607 and 1522 → 1518. Radius/diameter and implied K unchanged (r=3,
d=6, K=5 bipartite). Conservation gate + projector tests pass at unchanged
tolerances; `provisional_reaction_set=False` with `disposition_sha256`
recorded in every npz.
