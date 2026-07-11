# Rate-level cross-check: MESA (label configuration) vs pynucastro 2.12.0 (Step 4, Task 2)

Derived: `scripts/crosscheck_rates.py` + `scripts/appendixb_check.py`
(probe: `src/mesa_probes/`), 2026-07-09/10. Measured rows: RESULTS.md
2026-07-10. Machine-readable outliers: `configs/rate_outliers.yaml`
(135 severe channels + class-level explanations). Raw comparison tables:
`data/mesa_cache/crosscheck_{bare,weak,screen}_mesa_{80,151}.csv`.

**Comparison target.** The label configuration is stock MESA r23.05.1 +
bbq defaults (empty `&nuclear`/`&eos` namelists): REACLIB snapshot
jina 20171020, weaklib LMP > Oda > FFN with `use_suzuki=.false.`,
`screening_mode='chugunov'` — with the authors' gh-575 fix applied
(Appendix B). Accordingly, bare/weak/screening comparisons run against
stock r23.05.1 with the gh-575 channels excluded
(`configs/appendixb_excluded_channels.yaml`), and those channels are
verified separately against MESA 24.08.1 (first release with the fix).

Grid: T9 ∈ {1.6, 2.5, 3.3, 4.0, 5.0, 6.3, 7.9} × ρ ∈ {1e7, 1e8, 1e9} ×
Yₑ ∈ {0.45, 0.48, 0.498} (T-only for REACLIB). Screening OFF for the bare
pass on both sides.

## Bands (stated per Task-2 brief)

| category | band | justification |
| --- | --- | --- |
| REACLIB forward (matched clean) | 0.004 dex (~1%) | same REACLIB lineage; only a snapshot refit or a harness bug can exceed it |
| DB inverse | 0.05 dex | partition-function provenance differs: MESA multiplies its DB reverses by winvn pf ratios; pynucastro evaluates JINA v-flag reverse fits pf-free; plus mass/Q-table provenance |
| weak tabular | 0.1 dex | same table families after ADR 0003, but MESA interpolates bilinearly in log λ on the coarse (T9, log ρYₑ) grid; pynucastro uses its own interpolant |
| weak reaclib | 0.05 dex | same lineage as forwards |

Individual channels are flagged in `rate_outliers.yaml` only beyond the
"severe" thresholds (0.05 forward / 0.5 elsewhere); the in-band-to-severe
bulk is explained class-by-class below.

## Results — bare rates (screening off)

| category (net) | channels | median \|Δlog10\| | p95 | max | beyond band |
| --- | --- | --- | --- | --- | --- |
| reaclib_forward (80) | 268 | 4.4e-16 | 0.037 | 3.69 | 169/1876 evals |
| reaclib_forward (151) | 658 | 8.9e-16 | 2.0e-13 | 1.12 | 168/4606 |
| db_inverse (80) | 257 | 0.048 | 0.47 | 3.69 | 884/1799 |
| db_inverse (151) | 645 | 0.095 | 0.57 | 1.39 | 2822/4515 |
| construction swaps (80/151) | 28/32 | 0.0004/0.0006 | 0.63/0.70 | — | no band |

- **Forwards are bit-identical at the median** — the evaluation pipelines
  agree exactly where the underlying fit is unchanged. The tail is REACLIB
  snapshot refits (20171020 vs pynucastro 2.12.0), which travel in
  forward/reverse pairs: worst offender n13(p,γ)o14 and its reverse at
  −3.7 dex, then he3(n,γ)he4 (+1.1), o17(α,γ)ne21 (+0.99), n14(p,γ)o15
  (+0.88) — all pp/CNO-sector channels with little leverage on
  silicon-burning Yₑ; 25 forward channels total are flagged.
- **DB inverses:** signed median Δ grows 0.005 → 0.013 dex over
  T9 1.6 → 7.9, consistent with pf-ratio handling (see band note); the
  symmetric ±0.05–0.5 dex spread follows the paired forward refits and pf
  magnitudes. 93 channels beyond 0.5 dex are flagged individually.
  **Consequence for Step 5/6:** pynucastro's raw v-flag reverses are
  pf-free; any κ_r computation at T9 ≥ 5 must either use pf-corrected
  derived rates or inherit an artificial κ floor (measured in Task 3).
- **Construction swaps** (fit-vs-derived direction disagreements, 14/16
  pairs): median 0.0004/0.0006 dex — the two snapshots' fit/derived pairs
  are numerically consistent; only the labels differ. Not a defect.

## Results — weak sector (full grid)

| category (net) | channels | median \|Δlog10\| | p95 | max |
| --- | --- | --- | --- | --- |
| weak_tabular (80) | 38 | 0.066 | 0.40 | 0.52 |
| weak_tabular (151) | 164 | 0.073 | 0.33 | 0.80 |
| weak_reaclib (80/151) | 7/8 | ~1e-7 | 0.88 | 1.08 |
| be7→li7 EC (provenance) | 1 | 2.58 | — | 2.77 |

- **Per-pair table sources match exactly** (0 mismatches after ADR 0003).
- **The tabular spread is interpolation, not physics:** at the T9 = 5.0
  table node the median collapses to 0.003 dex (0.7%); off-node medians
  (0.03–0.18 dex) and the β⁻ tail (≤ 0.8 dex, steep low-λ channels:
  ca43/ca48/k40/sc44 wk-minus) are MESA-bilinear-vs-pynucastro-interpolant
  differences on the same coarse tables. The labels contain MESA's
  bilinear values — Step-5 flux work that needs weak λ at off-node states
  should evaluate MESA-side (probe) rather than pynucastro tabular.
- **Yₑ-controllers (all LMP/OHMT-matched):** median \|Δ\| 0.009–0.095 dex,
  at-node \|Δ\| ≤ 0.012 dex (co55, ni56, fe54, fe56, v51, s33, cl35, ar37;
  cr53 absent from both nets, fe55/mn54/… channels absent from mesa_80 —
  membership per RESULTS.md 2026-07-08).
- **Edge behavior:** every grid state is interior to the weak tables
  (T9 ≤ 7.9 < 30; log ρYₑ ≤ 8.7 < 11) — no extrapolation affects the box.
  Outside it, MESA clips to the table edge (rates/private/eval_weak.f90)
  while pynucastro extrapolates (measured at T9 = 40, 100); any future
  out-of-box use must respect this. Weaklib↔reaclib blend is fixed below
  T9 = 0.02 — irrelevant in-box.
- **be7→li7 EC** is a genuine provenance difference (MESA: shipped
  S13_r_be7_wk_li7.h5 (T, ρYₑ)-dependent table; pynucastro: REACLIB ec
  fit): 2.6–2.8 dex. Light-sector, carried as an open flag.
- Severe weak_reaclib flags: the pp channel (r_h1_h1_wk_h2, 1.08 dex) and
  b8/he3+p positron channels — REACLIB-vs-MESA pp-chain provenance,
  negligible at silicon-burning conditions.

## Results — screening (the training-label determination)

MESA's `screening_mode='chugunov'` (bbq default, hence the label
configuration) equals **pynucastro `chugunov_2007`** to
median ratio 0.99999, max \|log10 ratio\| = 0.0021 over every strong pair ×
grid state (both nets); pynucastro's `chugunov_2009` does NOT match
(max 0.52 dex). MESA `extended` likewise equals pynucastro `screen5` to
~1e-4 (harness validation). Note pynucastro's screening functions return
ln(factor) — `exp` before comparing (encoded in
`crosscheck.rates_compare.compare_screening`).

## Appendix-B channels (verified against 24.08.1)

Stock-r23.05.1 errors of 10.0–11.1 dex (\|ΔN\|=1) / 20.6–22.7 dex (\|ΔN\|=2)
collapse to ≤ 1.9 dex under MESA 24.08.1 (ordinary DB-provenance scale) on
all channels except `r_h1_h1_he4_to_he3_he3`, which sits at 2.7 dex in BOTH
MESA versions — not a gh-575 channel; open flag. Full table:
`data/mesa_cache/appendixb_comparison.csv`; RESULTS.md 2026-07-09/10.

## κ-floor screen at NSE (Task 3)

Derived: `scripts/kappa_floor_screen.py` (2026-07-10); raw tables
`data/mesa_cache/kappa_nse_mesa_{80,151}.csv`. NSE compositions from
pynucastro's solver (converged at all 27 states per net, T9 ∈ {5, 6.3, 7.9}
× ρ × Yₑ, `use_coulomb_corr=False`, screening off — consistent with the
bare-rate comparison). κ_r = |f⁺−f⁻|/(f⁺+f⁻) per strong/EM pair; a pair is
a *suspect* when its minimum κ over all NSE states exceeds 1e-3.

| variant | median κ | p90 | suspects (mesa_80 / mesa_151) |
| --- | --- | --- | --- |
| pyna (graphs as built) | 6.6e-2 / 1.3e-1 | 0.39 / 0.49 | 268/280 · 656/672 |
| MESA stock r23.05.1 | 3.6e-3 / 3.3e-3 | 1.2e-2 / 7.2e-3 | 208 · 484 (κ→1 on gh-575 channels) |
| MESA 24.08.1 | 5.3e-3 / 4.9e-3 | 0.76 / 0.76 | 227 · 527 |

**Attribution (dispositive):** replacing the raw JINA v-flag reverse with
pynucastro's own `DerivedRate(source_rate=forward, use_pf=True)` collapses
κ from 0.44–0.64 to **1e-13–1e-11** (rate-evaluation precision) on the
worst pairs — the pervasive pyna floor is entirely the pf-free v-flag
reverses (pf corrections reach 0.22×–4.5× at NSE temperatures). The
stock-MESA residual ~3.4e-3 median floor is MESA's own pf-interpolation +
winvn-mass provenance. The 24.08.1 variant shows a subset of (n,α)/(p,α)
pairs at κ ~ 0.75 that are clean in stock — consistent with its newer
REACLIB snapshot carrying independently-fitted (non-DB-linked) pair
members; not our label configuration, recorded as an open observation.

**Gate for Step 5/6 (blocking):** every κ_r / kill-test computation must
construct reverse rates as `DerivedRate(use_pf=True)` (or take MESA-side
rates); raw v-flag reverses are forbidden at T9 ≥ 3 — they manufacture
κ floors up to 0.8 that would fake near-floor net flow and corrupt the
Target-A viability verdict. (Light nuclei lacking pf tables default to
log pf = 0 — harmless, pf ≈ 1 there.)

**Status update 2026-07-10 — gate IMPLEMENTED and measured (Step 5 WP2).**
The compiled flux engine (`src/gnn_nucleo/fluxes/`) enforces the gate at
compile time: every raw v-flag reverse is replaced by
`DerivedRate(source_rate=forward, use_pf=True)` (280/280 mesa_80,
672/672 mesa_151; measured, tests/test_flux_compile.py), and any
non-compliant construction raises `PfGateError`. κ at NSE with the
pf-corrected engine, screening off: median 2.6e-12, p90 8.2e-12,
max 1.5e-11 — the spurious floor above is ELIMINATED (measured,
RESULTS.md 2026-07-10 Step 5 WP2 rows; ADR 0004).

**New measured caveat for κ thresholds (2026-07-10):** with the
label-screening configuration (chugunov_2007 ON), κ at NSE carries a
REAL median offset of ~7.4e-2 (mesa_80 probe at T9 = 6.3, ρ = 1e9):
screening is applied per reaction from its own reactant pairs, so a
screened capture pairs with an unscreened photodissociation and
κ ≈ \|Δln scor\|. This is a property of the rate configuration (both
pynucastro and MESA net_screen screen per-reaction), NOT a pf artifact —
equilibrium detection (mask/κ thresholds) must use UNSCREENED κ or
explicitly account for the screening offset (measured, RESULTS.md
2026-07-10 Step 5 WP2 row).

*Codified 2026-07-11 as the two-κ-conventions rule (root CLAUDE.md,
Physics conventions): equilibrium detection and every κ threshold — e.g.
the 0.1 active-set gate — are evaluated on UNSCREENED κ runs; screened κ
serves only screening-offset diagnostics; the two conventions are never
mixed within one analysis.*

## Step-5 consequences

1. Flux derivations use pynucastro forwards freely (bit-identical), but
   DB reverses need pf-corrected evaluation (or MESA-side rates) — gates
   the κ screen (Task 3).
2. Off-node weak λ for label-side work should come from the MESA probe.
3. 135 severe channels (`rate_outliers.yaml`) are excluded-or-footnoted in
   any Step-5 flux derivation until individually explained; they cluster
   in the pp/CNO light sector, away from the Yₑ-controller set.

*2026-07-10 note: item 1 is implemented and measured — pf-corrected
reverses are compiled into `src/gnn_nucleo/fluxes/` and the κ-at-NSE
floor is eliminated (unscreened median 2.6e-12; measured, RESULTS.md
2026-07-10 Step 5 WP2 rows; ADR 0004). See the gate status update in the
κ-floor section above, including the new measured screened-κ caveat.*
