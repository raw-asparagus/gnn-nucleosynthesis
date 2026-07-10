# 0004 — Compiled flux engine: DerivedRate(use_pf=True) reverses, pyna-tabular weak λ, QSE group rule
Date: 2026-07-10    Status: accepted

## Decision
Step 5's flux/κ machinery (`src/gnn_nucleo/fluxes/`, `src/gnn_nucleo/qse/`)
settles four design points:

1. **Reverse rates**: every raw JINA v-flag reverse in the canonical
   collections is replaced positionally by pynucastro
   `DerivedRate(source_rate=forward, use_pf=True)` at compile time
   (`fluxes/db_reverses.py`); compilation raises `PfGateError` if any v-flag
   set survives. This implements the Step-4 blocking gate (RESULTS.md
   2026-07-10 κ-floor rows). Replacement is participant-preserving — ν and
   the column order are untouched; the ν-export fnames remain the canonical
   column names (replaced columns' live fnames swap `_reaclib` → `_derived`).
   Measured: 280/280 (mesa_80) and 672/672 (mesa_151) replaced, zero
   spin-state failures; κ at NSE collapses to median 2.6e-12 (unscreened).

2. **Compiled evaluation**: production rate evaluation never calls
   pynucastro per state. All ReacLib/Derived SingleSets are stacked into an
   (n_sets, 7) coefficient tensor evaluated as one matmul over the T-factor
   matrix; pf corrections use per-nucleus splines rebuilt bit-identically
   from pynucastro's public fields; tabular weak rates are vectorized
   clamped-searchsorted bilinear tables; screening is a numpy chugunov_2007
   mirror over deduplicated pairs. Validation calls pynucastro's scalar
   paths on small samples: per-rate λ agrees to ≤5e-12 rel (the bound sits
   above the ~1.3e-12 fp-association floor of coefficient-baked DB terms),
   ν·R matches `evaluate_ydots` within 1e-12 of per-species gross flux.
   Throughput 7.1e5 / 2.2e5 states/min/core (gate was ≥1e3).

3. **Weak λ from pynucastro tabular (ADR-0003 ordering) in the engine**;
   mesa_probe24 only for spot checks and outlier diagnosis. Rationale:
   weak columns never enter κ (f⁻ = 0 structurally, κ ≡ 1, never
   mask-eligible); the documented 0.03–0.18 dex off-node interpolation
   difference is small against ranking gaps; the probe is a per-T-grid
   Fortran subprocess, not per-state-batchable. β⁻ tabular columns carry a
   `weak_offnode_risky` mask. Handshake attribution confirmed the class is
   visible but bounded (5–24% of rate-level departures).

4. **QSE group rule**: `configs/qse_groups.yaml` — default silicon group
   24 ≤ A < 45, Z > 2 (Hix & Thielemann single cluster); variants `a28_up`
   (A ≥ 28) and `a24_46` (boundary at 46, placing the ⁴⁵Sc edge inside the
   group — required for the literature bridge ⁴⁵Sc(p,γ)⁴⁶Ti to be a
   boundary crossing; measured rank 2/251 on relaxed high-Yₑ rows).
   The eligible set for any equilibrium mask excludes weak columns
   STRUCTURALLY (`qse/diagnostics.py::eligible_mask`).

Storage deviation from the Step-5 brief, recorded deliberately: chunked HDF5
runs store f⁺ (gross, ν-column order) + pair maps; f⁻/φ/κ are exact derived
views materialized on read (`fluxes/store.py`) — f⁻ is a permutation of f⁺,
so this halves disk with zero information loss.

## Context
Step 4 proved the raw v-flag reverses manufacture spurious κ floors
(median 6.6e-2/1.3e-1 at NSE) that would corrupt the Target-A kill-test
verdict, and pinned the label configuration (chugunov_2007, ADR-0003 weak
ordering). Step 5 needed every-reaction fluxes over ~1e6 states — scalar
pynucastro evaluation (~0.5 s/state) was 4 orders too slow.

## Consequences
- Every κ/flux entry point passes through `compile_network` → the pf gate,
  screening pin, and ADR-0003 assertions cannot be bypassed silently.
- The full 1,041,400-state corpus per network is minutes of compute; Step 6
  consumes precomputed data/fluxes/ runs (hashes in RESULTS.md).
- NEW measured caveat: with the label screening ON, κ at NSE carries a real
  ~7e-2 offset (per-reaction screening asymmetry: screened capture vs
  unscreened photodissociation). Step-6 equilibrium detection uses
  UNSCREENED κ or must account for the offset.

## Revisit if
- pynucastro is upgraded past 2.12.0 (coefficient/pf/tabular mirrors must be
  revalidated against the new scalar paths);
- a channel's DerivedRate construction fails (spin states) on a future
  network — the compile fails loud and the channel needs a mesa_probe24 or
  exclude-with-footnote decision;
- Step 6 shows the Si-group boundary choice (45 vs 46) changes a kill-test
  verdict — then the variant must be promoted to a measured decision.
