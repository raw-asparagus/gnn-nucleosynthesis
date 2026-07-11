# 0005 — bbq rerun campaign: hydrostatic mode, stock r23.05.1, fine log cadence
Date: 2026-07-11    Status: accepted

## Decision
The Step-6 relaxed-manifold data (the kill-test verdict distribution) comes
from local bbq reruns (`scripts/bbq_campaign/`, outputs under
`data/bbq_reruns/` — gitignored, manifest + hashes in RESULTS.md), with four
settled points:

1. **Mode: `use_hydrostatic` with `times_from_file`.** It is the mode that
   produced the shipped test trajectories (identical output format,
   `lib_hydrostatic.f90`: header `age dt eps_nuc eps_neu <isos>`, sourced),
   the only bbq mode with both composition carry-over between rows and
   per-row eps_nuc, and each `times.txt` line is a per-step burn duration —
   exact cadence control. `use_input_file` burns rows independently (no
   trajectory); `use_profile` writes no eps_nuc.

2. **Cadence: 40 points/decade log-spaced ages from 1e-8 s, dt capped at
   1e5 s** (assumed → pilot-verified), to `t_end` = 1e4 s (T9 ≥ 5) / 1e6 s
   (3.3–5) / 1e8 s (< 3.3), a stated wall at low T9. This directly attacks
   the shipped-data stall mechanism (output dt grown to ~1e10 s at ~10
   points/decade; RESULTS.md 2026-07-10 anomaly row). Every rerun passes
   `data.trajectories.stall_row`; frozen rows are acceptable only where the
   frozen state matches `solve_nse`.

3. **MESA: stock r23.05.1 (the tree bbq is linked against), NOT 24.08.1** —
   matches the shipped-label config (screening chugunov, weaklib
   LMP > Oda > FFN via defaults, eps=1d-8/odescal=1d-10), so reruns are
   comparable to shipped data. Stock r23.05.1 carries the gh-575
   multi-body-inverse bug (RESULTS.md 2026-07-09) which the authors' label
   MESA had fixed: **gh-575 channels (configs/appendixb_excluded_channels
   .yaml) are excluded from rerun-based conclusions**; the pilot handshake
   verifies contamination stays confined to them.

4. **Composition families**: (i) shipped-trajectory row-0 states at the
   file's exact (logT, logRho) — early-time comparability; (ii) canonical
   two-isotope Si-burning mixes (si28+si30, si30+ne22) solving
   ΣXᵢZᵢ/Aᵢ = Yₑ — the Yₑ = 0.45 target is substituted by 0.455 (network
   Z/A floor over A ≥ 12 species is ne22 = 0.45455; recorded in the
   manifest); (iii) nearest Sobol-grid states per (T9, ρ, Yₑ) cell, with
   state_ids persisted in the manifest (join discipline). 209 runs/net.

## Alternatives rejected
- `use_input_file` with cumulative durations: no state carry-over — N
  sequential bbq invocations per trajectory, paying full net setup per row.
- Rebuilding bbq against 24.08.1: fixes gh-575 but breaks label
  comparability (the labels' own MESA was r23.05.1 + fix, not 24.08.1);
  Step-4 measured 24.08.1 rate deltas are small but nonzero.
- Backporting the gh-575 fix into r23.05.1: still open as a follow-up human
  decision (Step-4/5 carry-over); not needed while the excluded-channel set
  covers the affected columns.

## Switch condition
Rebuild against a patched MESA (or 24.08.1) if the pilot/campaign early-time
handshake vs shipped trajectories fails outside the documented Step-4
difference classes, or if gh-575 contamination shows up beyond the excluded
channels. Revisit the cadence if any rerun still exhibits the stall
signature at non-NSE states (tighten dt cap / shorten t_end).
