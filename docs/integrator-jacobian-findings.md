# Reference-integrator hot-state cost: two Jacobian/structure fixes measured and rejected (2026-07-22)

**Verdict: no cheap integrator-level change unlocks hot-strata (T9 ≳ 5) Φ
generation. The augmented `[Y, Φ]` state with the reactant-only analytic
Jacobian (ADR 0006, unchanged) is near the practical limit. Both candidate
improvements were implemented/measured and rejected.** This memo records the
measurements so the negative results are not re-derived; no code from either
attempt was retained.

## Motivation

RESULTS.md 2026-07-12 (throughput row, `scripts/step6_integrate_check.py`)
diagnosed the corpus-infeasibility of local Φ labels as a hot-state cost:
17/36 (mesa_80) and 10/24 (mesa_151) sampled states censored at the 4800 s
deadline, all T9 ≥ 5, and it named "the deliberately neglected tabular-EC ρYₑ
Jacobian chain" as the suspected cause and the ADR-0006 Yₑ-chain contingency as
the candidate unlock. This investigation tested that hypothesis and the
ADR-0006 dimension-fallback hypothesis directly.

Measurements below are from investigation probes (scratchpad, not committed
scripts) during 2026-07-20…22, on mesa_80. Benchmark runs use the pinned
`scripts/step6_integrate_check.py` selection (seed 20260711, `--deadline 4800`,
`--n 36`, 10 workers); the "old vs new" hot-state probes toggle a candidate in
one process (in-process monkeypatch) so both versions see the identical state.

## Attempt 1 — analytic Yₑ-chain Jacobian (the ADR-0006 contingency)

Added the ∂λ/∂Y term for the tabular-EC columns (through log₁₀(ρYₑ)) and the
ρYₑ-weighted REACLIB EC columns (through Yₑ) — the rank-structured
`ΔD[j,i] = R_j · p_j · (Z_i − Yₑ A_i)/(Yₑ · ΣA_kY_k)`. It was **correct**
(returned composition unchanged to ~3e-10; conservation exact; the term matched
finite differences on the tabular + ye_weighted columns the reactant-only
Jacobian cannot model), and it is dense across all species on the ~40 EC rows.

Result: **marginal, and neutral on the hot states it targeted.**

- Single-state si28/si30 at T9 = 4, dt = 1e-2 s: nfev 15246 → 2004 (7.6×),
  njev 647 → 18. **This state is NOT representative** of the Sobol corpus
  (which carries free nucleons / different stiffness) — it drove an
  over-optimistic initial read.
- mesa_80 corpus (matched OLD/NEW, per-state join): every state that converges
  is 1.0–1.7× faster (median ~1.15×), solver failures 7 → 5, **no per-state
  regression**; censored count 17 → 18 (unchanged in practice). The summary
  "median wall 356.8 → 2923.6 s" is a bimodal-median artifact (18 fast vs 18
  censored-at-4800 straddles the gap), not a real regression.
- Hot-state probe (T9 6–7, dt = 1e-1 s, OLD vs NEW same state):

  | state | T9 | OLD wall | NEW wall | OLD nfev | NEW nfev |
  |------:|---:|---------:|---------:|---------:|---------:|
  | 310 | 6.64 | 26.1 s | 23.8 s | 10831 | 9646 |
  | 429 | 6.35 | 210.2 s | **218.4 s** | 78864 | 76761 |
  | 577 | 6.35 | 14.0 s | 13.9 s | 6170 | 6069 |

  Hot states get only 2–11% fewer nfev, and on the expensive one (429) NEW is
  **4% slower in wall** — the denser Jacobian's per-step LU cost cancels the
  nfev gain. The hot bottleneck is the number of stiff steps, which an
  accurate-per-step Jacobian does not reduce.

Decision: **reverted.** A change that is neutral on the hot states it targeted
is not worth the added Jacobian density/complexity.

## Attempt 2 — Y-only + quadrature (ADR-0006's own dimension fallback)

ADR 0006's switch condition lists "switch to the Y-only + quadrature fallback
if … throughput falls below what Phase-1 needs," on the premise that the
augmented dimension (687 for mesa_80: 80 species + 607 reactions) makes the
sparse LU the bottleneck. Tested by integrating **Y-only** (80-dim, jac = νD)
vs the augmented system on the hot states.

Result: **refuted — 25× slower.**

  | state | T9 | augmented (687-dim) | y-only (80-dim) |
  |------:|---:|--------------------:|----------------:|
  | 310 | 6.64 | 25.0 s / 9646 nfev | **616.5 s / 231741 nfev** |
  | 429 | 6.35 | 217.2 s | did not finish in 40 min |

The augmented dimension is **not** the bottleneck; the opposite — carrying Φ
(a non-stiff pure quadrature, `dΦ/dt = R`) alongside Y stabilises BDF's error
control. Integrating the net dynamics νR alone is far stiffer, because the huge
near-cancelling gross fluxes wreck the step-size control. This retires ADR
0006's Y-only fallback with a measurement and **supports ADR 0006 point 1**
(augmented state) as already correct; ADR 0006 is unchanged.

## Conclusion and the genuine unlock

Within "improve the integrator's Jacobian or state structure," there is no
cheap unlock for hot-strata Φ. The remaining in-scope lever, the
screening-chain Jacobian, was assessed as low-probability and not pursued (the
*dominant* weak Yₑ chain was already neutral, and screening couples every
charged species → an even denser Jacobian). Looser rtol on hot strata is a pure
accuracy trade, not a structural fix.

This **confirms the standing Step-6 verdict** (RESULTS.md 2026-07-12): corpus-
scale local Φ generation is infeasible; the feasible Phase-1 path is Φ
auxiliary labels on **T9 < 5 stratified subsets** (10³–10⁴ states,
≈ 4–40 core-days), with shipped-ΔX as the primary supervision.

The genuine unlock for hot/NSE-approaching states is **QSE-reduced
integration**: algebraically equilibrate the fast strong sector (the
near-cancelling forward/reverse pairs that force the tiny steps) and integrate
only the slow weak sector. That is a major separate implementation (a reduced
network with algebraic QSE constraints) and is recorded here as future work,
not attempted in this task.
