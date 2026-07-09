# Step 4 report — MESA reconciliation of the provisional graphs (2026-07-09/10)

Every number below is measured and logged in RESULTS.md (sections dated
2026-07-09/10) with script + commit provenance. New instruments:
`src/mesa_probes/` (Fortran driver against MESA net/rates: dump_net,
dump_inverse, eval_rates, eval_weak, eval_screen) and
`src/gnn_nucleo/crosscheck/` (canonical keys, reconciliation, rate/κ
comparison). MESA/bbq trees untouched; probe cache writes redirected.

## 1. Reaction-set reconciliation (Task 1) — RESOLVED, flag flipped

- Canonical counts (directed sorted-multiset keys, pp/pep lepton-channel
  disambiguation — the only split): **MESA 607 / pyna 610** (mesa_80),
  **1518 / 1522** (mesa_151). **MESA_ONLY = 0 on both nets** — the
  headline risk (labels containing physics the graph lacks) did not
  materialize; the graphs were strict supersets.
- Dispositions: 3 / 4 PYNA_ONLY channels dropped (p+be9 ⇄ n+p+2α both
  directions, n+p+2α→he3+li7; + n16→c12+α β⁻-delayed α in mesa_151);
  the 14 / 23 weak-table mismatches (all MESA=OHMT vs pyna=suzuki,
  sd-shell A=17–28) were eliminated by adopting the MESA-matched tabular
  ordering `suzuki<pruet_fuller<ffn<oda<langanke` (reproduces weaklib
  LMP > Oda > FFN with use_suzuki=.false. — the label configuration).
  Remaining MATCHED_DIFF_PROVENANCE: 28 / 32 fit-vs-derived direction
  swaps (snapshot labeling; numerically consistent to 0.0004 dex median)
  + be7 EC (S13 table vs reaclib fit) → carried to Task 2.
- Regenerated graphs: **607 / 1518 reactions** (new flux-head dims), weak
  sector 46 / 173 (mesa_151 β⁻ 85→84); radius/diameter/K unchanged
  (r=3, d=6, K=5); conservation gate + projector PASS at unchanged
  tolerances; **provisional_reaction_set=False** (ADR 0003), disposition
  sha256 recorded in every npz. Zero residue.
- Files: configs/reactions_mesa{80,151}_mesa.yaml,
  configs/reaction_disposition_mesa{80,151}.yaml,
  docs/reaction-reconciliation.md.

## 2. Rate-level cross-check (Task 2) — label config pinned

- Bare REACLIB forwards: **bit-identical at the median** (4e-16 dex);
  tail = REACLIB snapshot refits (worst: n13(p,γ)o14 pair, −3.7 dex),
  25 channels flagged, all pp/CNO-sector. DB inverses: pf-handling
  systematic (signed median +0.005→+0.013 dex with T; pyna v-flag fits
  are pf-free); 93 channels > 0.5 dex flagged.
- Weak sector: **0 per-pair table-source mismatches** (post-ADR-0003).
  At the T9=5 table node median |Δ| = 0.003 dex; off-node spread
  (0.03–0.18 dex median, β⁻ tail ≤ 0.8) is interpolation only (MESA
  bilinear — the labels' values). Yₑ-controllers agree ≤ 0.012 dex
  at-node. Edge behavior: box is interior to all weak tables; outside it
  MESA clips, pynucastro extrapolates (measured). be7 EC: 2.6–2.8 dex
  provenance flag (S13 h5 vs reaclib fit).
- **Screening determination:** MESA chugunov ≡ pynucastro `chugunov_2007`
  (max |Δlog10| = 0.0021 over all pairs × grid, both nets); NOT
  chugunov_2009. bbq default chugunov + empty Zenodo namelists ⇒ the
  training labels used exactly this; pyna screening fns return ln(factor).
- configs/rate_outliers.yaml: **135 severe channels**, each class-explained
  or open-flagged; none touch the Yₑ-controller set. docs/rate-crosscheck.md.

## 3. κ-floor screen at NSE (Task 3) — spurious floor found & attributed

- Graphs as built (raw JINA v-flag reverses): median κ at NSE = 6.6e-2 /
  1.3e-1; **268/280 and 656/672 pairs above the 1e-3 suspect line** — a
  pervasive spurious floor.
- Attribution (dispositive): `DerivedRate(source_rate=fwd, use_pf=True)`
  collapses the worst pairs 0.44–0.64 → **1e-13–1e-11**; the floor lives
  entirely in the pf-free v-flag reverses (pf corrections 0.22×–4.5× at
  NSE T). Stock MESA's own floor: median 3.4e-3 (pf interpolation);
  κ→1 exactly on its gh-575 channels. 24.08.1 shows independent-fit pair
  inconsistencies on a subset (open observation, not the label config).
- **New blocking gate for Step 5/6** (RESULTS.md 2026-07-10; root
  CLAUDE.md): reverse rates in any κ/flux computation must be
  DerivedRate(use_pf=True) or MESA-side; raw v-flag reverses forbidden at
  T9 ≥ 3.

## 4. Appendix-B verdict (Task 4) — bug confirmed; 24.08.1 installed

- **Stock r23.05.1 HAS the gh-575 bug** (static: compute_rev_ratio applies
  the phase-space factor only in the No==1 branch; empirical: 10.0–11.1
  dex for |ΔN|=1, 20.6–22.7 dex for |ΔN|=2 on the 7/8 multi-body inverse
  channels, tracking |ΔN|·log10(fac·T9^{3/2})). Beyond the paper: ch-8
  photodisintegrations (c12→3α, be9→n+2α, li6→n+p+α) are LOW by ~10 dex.
  Neither net contains ³H, so the paper's example channels cannot appear.
- The Zenodo labels were generated with the authors' locally FIXED
  r23.05.1 ⇒ labels clean; our stock tree is the outlier. Fix first
  shipped upstream in release **24.08.1** (changelog cites gh-575).
- User decision (2026-07-09, after empirical confirmation): install
  24.08.1 side-by-side. Done: ~/mesa-24.08.1 (Zenodo 13353788, md5
  verified, self-tests passed; scripts/install_mesa_24081.sh) + probe
  binary mesa_probe24. **Fix verified:** affected channels collapse to
  ≤ 1.9 dex — except r_h1_h1_he4_to_he3_he3 (2.7 dex in BOTH versions ⇒
  not a gh-575 channel; open flag). The minimal backport
  patches/0001-reaclib-reverse-phase-space.patch remains drafted and
  NOT applied (r23.05.1 stays pristine).
- Consequence: stock-MESA values on 9 / 11 channels excluded from all
  rate-agreement gates and κ/flux analyses
  (configs/appendixb_excluded_channels.yaml); Step 5 flux work on those
  channels uses pynucastro-with-pf or mesa_probe24.

## 5. Missing-Sobol-rows (Task 5) — benign, block-structured

- All 1,041,400 rows NN-matched to the shipped 2²⁰ grid exactly
  (0 unmatched, 0 collisions; missing = 7,176 per net precisely).
  Structure: **contiguous head + tail blocks** of the Sobol sequence
  (mesa_80: [0,4100) ∪ [1045500,2²⁰) exactly; mesa_151 same minus 2
  recovered, plus 2 isolated genuine failures) — lost first/last
  job-array batches, not scattered bbq crashes.
- Spatially hyper-uniform (χ²/dof ≤ 0.1 on all marginals, as stratified
  Sobol blocks must be): **no corner or edge under-coverage** — benign
  for OOD gating and kill-test interpretation. Missing sets 7,174/7,176
  shared between nets. Figures docs/figures/sobol_missing_*.png.
  (The grid was unseeded-scrambled: the shipped file is the only ground
  truth; regeneration is impossible.)

## 6. Blocked / needs human decision

- Nothing blocks Step 5. Open flags (carried, not blocking):
  r_h1_h1_he4_to_he3_he3 (2.7 dex vs pyna in both MESA versions),
  be7 EC provenance, 135 severe rate outliers (pp/CNO sector),
  24.08.1 snapshot pair-inconsistencies.
- Standing decision honored: r23.05.1 unpatched; backport in patches/
  if label-exact multi-body inverse rates are ever needed from that tree.

## 7. Manual-item reminders (unchanged from Step 3 §9)

- 4 TB test-set email to the authors — still pending (local hosting
  viable, 5.5 TB free). Not yet blocking; needed before Phase-1 rollout
  evaluation.
- CPU allocation for bbq batch runs — now RELEVANT for Step 5 (fresh bbq
  runs for flux labels); arrange before Step-5 label generation.
- GPU fleet (Step 7) — not requisitioned; not yet blocking.
- Division-of-labor conversation — pending; none of the above blocks
  Step 5's kill-test prep.
