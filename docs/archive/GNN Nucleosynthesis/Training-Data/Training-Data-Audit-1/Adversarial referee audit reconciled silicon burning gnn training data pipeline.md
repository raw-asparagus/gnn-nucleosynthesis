# Adversarial Referee Audit — RECONCILED
## "Training-Data Generation for a Conservation-by-Construction GNN Emulator of Silicon Burning: Inventory, Pipeline, and Cost Model"

**VERDICT: COMMIT, after four small folds.** *(Supersedes the initial blind verdict of REVISE / six must-fix errors — see reconciliation note.)*

---

## Reconciliation note (supersedes the original framing caveat)

The audit was first run as a hostile, **web-only** verification pass *without* the report text or the project's other documents in hand. Its findings were therefore written as conditionals ("*if* the report states X…") and its verdict (REVISE, six must-fix errors) reflected worst-case assumptions about what the report might say.

It has now been reconciled against (a) the **full text of the report under audit** and (b) the **three ground-truth project documents**: the Consolidated Report & PhD Plan, the Architecture Specification, and the Prediction-Target Conditioning & Yₑ Accuracy Floor. On that reconciliation the conditionals resolve **false almost everywhere** — the report is consistently more careful than the audit assumed. **None of the six "must-fix errors" is an error in the report:** five are confirmations (the report already does the right thing) and one (the Yₑ gate) is wrong as framed *and* out of scope for this report. The audit's durable value reduces to **three concrete contributions plus one relabel**, folded in below. The verdict flips from REVISE to **COMMIT-after-folds**.

---

## Substrate (verified and correct; warning satisfied)

The report is built on **Grichener et al. 2025, "Nuclear Neural Networks," ApJS 279, 49** (DOI 10.3847/1538-4365/ade717; arXiv:2503.00115), its reproducibility package (Zenodo DOI 10.5281/zenodo.14873443), and the tools **bbq** (Farmer 2023; Zenodo 7585202) and **MESA r23.05.1**. All real and correctly named. The source paper builds a *fully-connected* NNN, not a GNN; the GNN-by-construction and conservation-mask design are the student's project. **Warning satisfied:** the report correctly treats the Grichener NNN as the dense-FNN *data-source baseline* and NuGNN (arXiv:2606.04491) as a *preprocessing-convention* source only — it never attributes the GNN or the mask to Grichener et al.

---

## Reconciled corrections table

| Audit finding | Original (blind) call | Reconciled against actual report + project docs | Action |
|---|---|---|---|
| **Zenodo 14873443 is 49.1 GB, not multi-TB** | must-fix | Report §1/§2.1 already says "reproducibility package, **not** a flux database," cites the paper's "~80 GB in total," keeps the 4 TB separate and on-request, and flags the file listing as "**must be confirmed locally**." No multi-TB claim exists. | **Confirmation.** Fold the 49.1 GB *datum* in as a partial local confirmation (Fold 1). |
| **4 TB is "shared on request," not deposited** | must-fix | Report §2.2 / matrix / §5: "**will be shared upon request from the corresponding author**"; "negotiate early." Already correct. | **Confirmation.** Tighten one tag only (Fold 4). |
| **Hix & Thielemann = 1996 ApJ 460, not Physics Reports 1999** | must-fix | Report §3.2(ii) cites **1996 ApJ 460:869 / 1999 ApJ 511:862 / Hix et al. 2007 ApJ 667:476**; Architecture Spec ref list is identical. **No project file cites "Physics Reports 1999."** | **Phantom — strike.** The error lived only in the audit *brief's* instruction, not the report. |
| **3×10⁻⁶ Yₑ gate is unsourced & ~1000× too tight** | must-fix | **Derived** in Yₑ doc §5.3 / Arch Spec §1 (end-to-end floor 5×10⁻³–1.5×10⁻², ÷ N≈1.6×10³ → 3×10⁻⁶); labeled "**an inference-labeled working value**"; flagged across all three docs as conditional on measurement. **Not asserted in the data report at all.** | **Wrong as framed — strike.** See dedicated note. |
| **Detailed-balance screen must carry the phase-space term; cite Issue #575** | must-fix | Report §3.2(iii) step (1) "verify the **phase-space factor is present**"; step (4) "reverse = forward × (**detailed-balance factor from partition functions**)." Sourced to Grichener Appendix B (primary). | **Confirmation.** Add Issue #575 as a second citation (Fold 2). |
| **Weak-rate precedence = LMP > Oda > FFN** | must-fix | Report caveats: "**Langanke & Martínez-Pinedo (2000), Oda et al. (1994), Fuller et al. (1985)**." Exactly correct. | **Confirmation — strike from must-fix.** |
| **MESA off-grid: weak-blend vs thermonuclear cap at log T = 10** | feasibility | Report gives correct weaklib bounds (1 ≤ log ρYe ≤ 11; 7 ≤ log T < 10.5) and flags off-grid as must-confirm. | **Partial enrichment, but over-scoped.** Fold the cap detail in, scoped to *future* regimes (Fold 3). |
| **bbq native outputs = {X_i, e_nuc, ε_ν}** | verified | Report §3.1 states exactly that + Bulirsch–Stoer (Deuflhard 1983), **and adds** the `eps_nuc ≡ ε_nuc − ε_ν,nuc` MESA convention the audit missed. | **Confirmation; report is ahead of the audit.** |
| **CPU-hour figure needs re-derivation** | re-derive | Report §4.1 uses **0.1–0.5 CPU-hr/sample** (project figure) → 1–5×10⁵ CPU-hr → "few × 10⁵" ✓. Arithmetic chains correctly (17,000÷0.5=34k; 10⁶×0.5=5×10⁵; ÷17,000≈29 mo). | **False positive.** The audit's "3 min → 5×10⁴" is a calculation the report never makes. |
| **Dollar cost needs a sourced rate (~$2k–75k AWS)** | needs rate | **The report gives no dollar figures** — it stays in CPU-hr / node-months, correct for an institutional allocation. | **Moot; do not add.** AWS on-demand rates would mislead for a cluster-allocation context. |
| **Storage: distinguish ~80 GB from 4 TB** | check | Report §4.2 already separates ~80 GB / 4 TB on-request / tens-of-TB derived flux tensors. | **Confirmation.** Add the 49.1 GB datum (Fold 1). |

---

## The four folds (what to actually change in the report)

**Fold 1 — Zenodo outer-container datum + size reconciliation.** Record that the record is one file, `NuclearNeuralNetworks.zip` (≈49.1 GB), plus `README.txt`. This *partially* resolves the report's "file listing must be confirmed locally" flag — **the outer container, not the contents.** Reconcile the two sizes explicitly: 80 GB ≈ 9 timesteps × (3 GB mesa_80 + 6 GB mesa_151) **uncompressed**; 49.1 GB is the **zipped** deposit (~0.6 compression on numerical arrays is unremarkable). Most likely benign compression, not missing data — but the **zip-internal breakdown and on-disk format remain the genuine local-confirmation target**, untouched by the audit.

**Fold 2 — MESA GitHub Issue #575 as a second primary citation** for the Appendix-B bug. Grichener filed it; it names the offending reaction `r_neut_nuet_he4_he4_to_h3_li7` and quantifies the ~24-order overestimate. The report's Appendix-B citation is already valid; #575 strengthens the screen's provenance and hands the student the exact reaction string to test against.

**Fold 3 — Thermonuclear-rate-capping nuance, scoped correctly.** MESA caps thermonuclear rates at their log T = 10 value (it does not extrapolate), and weaklib edge-blends are documented-unphysical. **But within the stated regime box this is largely moot:** log T runs 9.2–9.9 (below the log T = 10 cap, inside weaklib's log T < 10.5) and log ρYe ≈ 6.65–8.70 (inside weaklib's 1–11). **The box is on-grid for the weak tables and below the thermonuclear cap.** The off-grid concern is real only for the **future regime extensions** (ECSNe low-T, PPISNe low-ρ in §2.3/§5). The report should say so explicitly — it currently over-flags off-grid generically.

**Fold 4 — Relabel the 4 TB set.** The §5 tag "already-public (on request)" overstates availability. It is *available on request* — discretionary, plus a non-trivial 4 TB transfer. The Consolidated Report already calls it "an external dependency, not a fact"; align the data report's tag with that.

---

## The one finding that is wrong — STRUCK (do not apply)

The original audit claimed the 3×10⁻⁶ Yₑ gate is unsourced and ~1000× tighter than the Grichener NNN's demonstrated accuracy. **This is a unit-mismatch artifact:**

- It compared a **per-step** gate (3×10⁻⁶) to an **end-to-end** number (0.004 × 0.47 ≈ 2×10⁻³). Different quantities.
- The project's **end-to-end** floor (5×10⁻³–1.5×10⁻²) is *looser* than the NNN's ~2×10⁻³ end-to-end accuracy — the correct direction, since the floor is set by FFN→LMP nuclear-physics uncertainty, not by beating the FNN.
- The per-step gate = end-to-end floor ÷ N, with N ≈ 1.6×10³, giving 5×10⁻³ / 1.6×10³ ≈ 3×10⁻⁶. **The factor of ~1000 the audit "found" is just the trajectory length N, by construction** — not a tension.

The audit's *instinct* has a real kernel — 3×10⁻⁶/step is ambitious and unproven for a GNN — but the project already owns this exactly (Architecture Spec §9: "*if the residual is even weakly biased, the gate tightens to a level no surveyed emulator has demonstrated for a controlled scalar like Yₑ*"), flagging it as the single biggest lever conditional on measuring the accumulation model. Credit the kernel; discard the framing. It does not belong in a critique of the *data* report.

---

## Confirmations (the former "must-fix" list, corrected)

Independently verified, and the report already gets each one right:

1. **bbq native outputs** are {X_i, e_nuc, ε_ν}, integrated by Bulirsch–Stoer / Bader–Deuflhard (Deuflhard 1983). The report states this *and* the `eps_nuc ≡ ε_nuc − ε_ν,nuc` convention.
2. **The detailed-balance screen** correctly restores the full reverse-rate relation (phase-space + partition-function factors), not exp(−Q/k_BT) alone — exactly the term MESA r23.05.1 omitted (Issue #575 / Appendix B).
3. **Weak-rate-table precedence** reads LMP (2000) > Oda (1994) > FFN (1985).
4. **The Hix & Thielemann citations** are correct: C(A,Z)/QSE physics from 1996 ApJ 460:869; the C(A,Z) and Y_QSE formulae match the canonical form and are internally consistent with the project's Yₑ doc.
5. **The cost arithmetic** is internally consistent and matches the paper's "few × 10⁵ CPU-hr" via the project's 0.1–0.5 CPU-hr/sample figure (a labeled extrapolation, not asserted as measured).

The report is also consistent with **every established project decision**: Target-A-first, hard baryon/charge conservation, the mask never touching weak reactions (the report's screen targets *strong* >2-body endo-energetic reverse rates only), the regime box, public-data-first, and the per-step Yₑ gate.

---

## Open local-confirmation list (the true residue — already owned by the report)

The audit retired none of these; the report flags most in its Caveats:

- **Zip-internal contents and on-disk format** of Zenodo 14873443 (CSV/parquet/npy?) — the audit confirmed only the container.
- **bbq's exact output columns and inlist control names** — both the report's repo reads and the audit were blocked; needs a local bbq run.
- **MESA r23.05.1 rate values at the box corners** and the actual interpolation/edge behavior — needs the local install.
- **The pynucastro–MESA REACLIB / weak-table / screening match** — the entire "derive φ externally" route is valid only if these match; validate by reproducing bbq net dY/dt before trusting φ.
- **The κ_r distribution, stoichiometric-matrix condition numbers, and the Yₑ-residual accumulation slope** — the project-wide Phase-0 program; only a numerical experiment settles these.

---

## Citations the audit did not reach (honest gap)

Despite the brief's "every load-bearing citation," the blind pass concentrated on Zenodo / bbq / MESA / Hix–Thielemann / cost and **did not verify** several pipeline-enabling citations (which this reconciliation has also not independently checked): the **pynucastro API specifics** (`evaluate_rates`, `RatePair`, `NSENetwork.get_comp_nse(...)`, `get_screening_map`, `symmetric_screening`) on which the external-φ route depends; the **NuGNN C = 17 signed-log convention** (§4.4, quoted from arXiv:2606.04491 §III.2); and the **SkyNet / WinNet** cross-check citations. These are more load-bearing for the data pipeline than several items the audit did check, and should be verified against current pynucastro docs and the NuGNN paper before the student builds on them.
