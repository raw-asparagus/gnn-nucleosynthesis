# Step 3 report — graph + conservation layer (2026-07-08)

All measured numbers below have RESULTS.md rows (date 2026-07-08, commits
57241e3…edef464, Zenodo 14873443 / pynucastro 2.12.0 provenance).

## 1. Push / CI

Pushed the 19 pending commits (5f80b00..2469c88) plus this session's work.
`ci.yml` ran for the first time and **passed** (lint + full pytest on
ubuntu-latest; run 28931898647). No CI fixes were needed. Repo is public, so
unauthenticated Actions-API verification works.

## 2. Schema amendments + ε_ν verdict

- **Join-key correction (user-approved deviation from the brief):**
  (logT, logRho) is NOT unique — 154,405 of 1,041,400 rows per file collide
  (3-decimal rounding). The brief's premise ("uniqueness verified in Step 2")
  is retired. The 9 dt files per network are exactly row-aligned (verified
  full-column), so **state_id = row index** is the identity/split key;
  `SplitSpec` keys on it.
- **Measured dt grids** (Age column, constant per file; deviates ≤ ~5% from
  nominal, differs per network) live in `configs/dt_grid_measured.yaml`,
  loaded by `schema.load_measured_dt()`; `DT_GRID_SECONDS` demoted to nominal
  labels; validation now rel_tol 1e-9 against the measured value.
- **ε_ν verdict: the 1e13 suspicion is ABSENT from the training sets.**
  Row-exact adjacent-dt |eps_nu| ratios are smooth (worst 0.712 at
  mesa_151 1e2/1e1) — no ~1e3 jump. All 18 CSVs are uniformly ÷1e16;
  `EPS_NU_QUARANTINED` ships empty. The upstream comment refers to their
  inference pipeline only.
- Units fixed (e_nuc integrated [erg/g]; ε_ν rate [erg/g/s]); `final_*` floor
  measured exactly 1e-15; float32-upstream / float64-here documented.
  `tests/test_schema.py` now includes a real-CSV smoke layer (skips off-box).
- CLAUDE.md corrected: ⁴⁵Sc(p,γ)⁴⁶Ti instrument scoped to mesa_151 only;
  ca41-in-both note; mesa_80 thin-weak-sector note.

## 3. Conservation-code audit decision: SUPERSEDE (ADR 0002)

`src/conservation/` was an empty docstring stub; the real prototype logic sat
in the two scripts and inline in the test. Ported (npz schema as a superset,
fail-loud column validation, drift metrics), fixed (lepton ledgers from
`weak_type` instead of the tautological `d_electron = Z·ν`; heuristic weak
classifier removed; explicit tabular-wins duplicate-link resolution), and
deleted `src/conservation/`. Canonical home: `src/gnn_nucleo/graph/`
(torch-free). Hook watched-paths, pyproject wheel list, README, CLAUDE.md
maps updated in the same commit. Exactly one source of truth for ν and C.

## 4. Graph export (PROVISIONAL reaction set)

| | mesa_80 | mesa_151 |
| --- | --- | --- |
| isotopes (asserted) | 80 | 151 |
| reactions (= flux-head dim) | 610 (572 ReacLib + 38 tabular) | 1522 (1358 + 164) |
| duplicate links resolved | 19 | 78 |
| weak columns | 46 = 21 EC + 19 β⁻ + 6 β⁺ | 174 = 84 EC + 85 β⁻ + 5 β⁺ |
| Yₑ direction | 27 lower / 19 raise | 89 lower / 85 raise |
| radius/diameter (bipartite) | 3 / 6 | 3 / 6 |
| … with I→I edges | 2 / 4 | 2 / 4 |
| implied K | **5** (4 with I→I) | **5** (4 with I→I) |

mesa_80's weak sector is NOT one-directional at rate level (19 β⁻ channels)
— the Step-2 "0/8 β-decay partners" finding concerns the named NNN
controllers only. Full 220-row inventory: `docs/weak-inventory-step3.md`.
**Caveat, explicitly flagged everywhere:** pynucastro's REACLIB-filtered set
+ suzuki-topped tabular ordering is not MESA r23.05.1's softwired net +
weaklib (LMP>Oda>FFN); every artifact carries `provisional_reaction_set=True`
until the Step-4 bbq cross-check (switch condition in ADR 0002).

## 5. Conservation gate + condition numbers

The blocking test never skips: `tests/conftest.py` regenerates missing npz
(~7 s/network, offline). Both networks PASS — column drifts (baryon, strong
charge, weak charge-to-lepton, lepton number) **exactly 0.0**; random-φ drift
within max(1e-12·s, 1e-13·G) over 10 seeds × 6 scales (1e0…1e-20; tolerance
rationale in the module docstring + CLAUDE.md gate section); dYₑ ≠ 0 through
weak columns; weak columns structurally excluded from any gate. 73 tests
green repo-wide. cond(ν) = 41.7 / 57.6 (nullity 1), cond(CCᵀ) = 3.9e4 /
1.0e5 — nowhere near the 1e6 Target-B trigger (which formally binds on the
Step-6 active set).

## 6. Target B projector

QR null-space form on the extended [nuclei…, e⁻, ν, ν̄] space (nuclei-only
projection would erase weak dYₑ — tested). Measured: max relative constraint
residual 6.7e-17 / 1.0e-16 across 20 decades of dY (gate ≤ 1e-12);
‖P²−P‖∞ ≤ 1.0e-15; rank = m−3 exactly; weak dYₑ preserved to ≤ 3.4e-21.
Linear-output-space-only warning (NuGNN failure mode) in code.

## 7. MESA / bbq install: **built + tested; bbq built and executes**

- mesasdk 23.7.3 → `~/mesasdk`; MESA r23.05.1 (Zenodo 7983526, md5 verified
  against the API) → `~/mesa-r23.05.1`; `./install` 570 s on 12 cores,
  "MESA installation was successful" banner confirmed (module self-tests).
- bbq @ 9783df31 linked and runs (loads MESA weak-rate tables; exits asking
  for a run mode absent an inlist — expected). Ready for Step 4.
- Deviations (no root): csh absent (warning only); libX11 dev symlink via
  `~/.local/lib` + LIBRARY_PATH. Clean fix: `sudo apt install csh libx11-dev`.
- Three installer iterations were needed (RC2-vs-final Zenodo record; nounset
  vs mesasdk_init; zipfile dropping exec bits) — all fixed in
  `scripts/install_mesa_full.sh`, which is resumable with a machine-readable
  STATUS file and per-phase logs.

## 8. Blocked / skipped / needs a human

- Nothing blocked. Two watch items: (i) the provisional-reaction-set caveat
  (§4) is the single biggest Step-4 risk; (ii) checklist row 7 stays half-open
  (active-set cond) and row 1's mesa_204 is not in the shipped data.
- Human look invited: the CLAUDE.md gate now documents the scale-aware
  tolerance form (docs-sync flagged the wording drift; entry added with the
  RESULTS.md row per the gates rule).

## 9. Manual-item reminders

- **4 TB test-set email**: local capacity is no longer a constraint — the data
  filesystem has ~5.5 TB free, so hosting the full set locally is viable.
- CPU allocation for bbq batch runs (Step 4+) still to be arranged.
- GPU fleet for the Step-7 ablation matrix — not yet requisitioned.
- Division-of-labor conversation with the group — still pending.
