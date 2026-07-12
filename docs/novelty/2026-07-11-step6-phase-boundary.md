# Novelty check — 2026-07-11 (Step 6 / Phase-0 → Phase-1 boundary)

**Checker:** novelty-checker subagent (Claude)
**Date of sweep:** 2026-07-11
**Scope:** first dated novelty report in this repo (docs/novelty/ previously empty).
Defends the four-leg conjunction claim of CLAUDE.md — (i) GNN on the nuclear reaction
network, (ii) hard baryon/charge conservation by construction, (iii) silicon-burning /
CCSN-progenitor regime, (iv) in-the-loop MESA coupling — plus one NEW claim measured in
Step 6 (RESULTS.md 2026-07-11, "HIGH-T9 TRAINING-LABEL PATHOLOGY"): the shipped NNN
training labels at T9 ≳ 5 sit at gh-575 bug-displaced pseudo-equilibria 7–13 dex from
NSE, with wrong Yₑ evolution, attributed by a stock-r23.05.1 vs 24.08.1 witness.

## Queries run (all 2026-07-11)

Web searches (general, US index):
1. `NuGNN graph neural network nuclear reaction network Kim Mumpower Smith 2026`
2. `arXiv 2026 Grichener nuclear neural networks MESA coupling emulator stellar evolution`
3. `"citing" OR "builds on" NuGNN arXiv 2606.04491 conservation graph neural network`
4. `"Nuclear Neural Networks" Grichener citation 2026 emulator training data silicon burning follow-up`
5. `MESA "gh-575" OR "inverse reaction rate bug" reaction network equilibrium bug r23.05.1`
6. `MESA reverse reaction rate "phase space" bug nucleosynthesis training labels neural network pseudo-equilibrium`
7. `SPIRIT solver r-process nucleosynthesis sparse preconditioning arXiv 2026` (+ retry `"SPIRIT" nucleosynthesis solver 2026 preconditioning reaction network GPU`)
8. `machine learning emulator silicon burning conservation baryon number neural network 2026`
9. `"chemical reaction neural network" OR "CRNN" mass conservation stoichiometry hard constraint surrogate 2025 2026 combustion`
10. `RHINE r-process neural network emulator nucleosynthesis 2025 2026 arXiv`
11. `graph neural network nucleosynthesis reaction network stellar 2026 message passing isotopes`
12. `"quasi-statistical equilibrium" OR "QSE" machine learning neural network nucleosynthesis masking flux`
13. `MESA stellar evolution code neural network surrogate "in the loop" coupled burning nucleosynthesis acceleration 2026`
14. `MACE machine learning astrochemistry emulator chemical kinetics conservation 2025 2026`
15. `neural network predicts "reaction fluxes" stoichiometric matrix conservation nucleosynthesis OR astrophysics surrogate`
16. `"14873443" OR "Grichener" Zenodo dataset bbq training set reuse benchmark neural network`
17. `"integrated flux" OR "time-integrated fluxes" per-reaction supervision training neural network stiff kinetics implicit solver labels`

Structured lookups:
- arXiv abs page 2606.04491 (version/journal-ref check).
- arXiv API `au:"Grichener"` (15 most recent), `au:"Chae" AND cat:nucl-th` (10 most
  recent), `(au:"Renzo" OR au:"Kerzendorf" OR au:"de Mink") AND (neural|ML|emulator)`
  (15 most recent), `all:"nuclear reaction network" AND all:"neural network"` (20 most
  recent, date-descending).
- Semantic Scholar citations of arXiv:2503.00115 (7 citing papers) and of
  arXiv:2606.04491 (0 citing papers).
- arXiv abs pages: 2504.14180, 2604.22605.

## Hits and triage

| Hit | ID | Triage | One-line relevance |
|---|---|---|---|
| NuGNN (Kim, Chae, Ko, Mumpower, Smith) | arXiv:2606.04491 | **ADJACENT (nearest neighbour, leg i)** | Still **v1 (2026-06-03), no journal ref, 0 recorded citations, no v2/follow-up**; hetero isotope/reaction-node GNN, 690-isotope XRB regime; no hard conservation, no MESA coupling. Status unchanged since claim was framed. |
| Grichener et al. NNN | arXiv:2503.00115 / ApJS 279, 49 | **ADJACENT (nearest neighbour, leg iii)** | Dense MLP, normalization-only conservation, offline (MESA integration stated as future work). No published follow-up emulator paper found. |
| Grichener et al., rotating CHE SN/LGRB progenitor grid | arXiv:2606.21824 (2026-06-20) | IRRELEVANT to legs | MESA 128-isotope physics paper, no ML, no bug discussion — shows the constellation's current output is progenitor physics, not emulation. |
| DeePODE astrophysical reacting flows (Zhang, Yi, Wang, Xu, T. Zhang, Zhou) | arXiv:2504.14180 / ApJ (adf331), v2 2025-10-13 | ADJACENT | Dense-NN surrogate for stiff astro networks (EMC sampling); no conservation-by-construction, no GNN, no Si-burning/MESA. Cites NNN. |
| Myers et al., RSG pre-collapse structure | arXiv:2604.22605 (2026-04-24) | IRRELEVANT | MESA 206-isotope physics paper citing NNN; abstract/summary has no emulator, no bug, no rate-quality discussion. |
| "SPIRIT Solver: Accelerating r-process Nucleosynthesis with Sparse Preconditioning" (2026) | arXiv id **not located** (Semantic Scholar entry citing NNN; not in web/arXiv index yet) | ADJACENT (unresolved) | Classical sparse-preconditioning solver acceleration, r-process, not ML by title; re-check next sweep for the id and content. |
| First-star chemical-network emulator | arXiv:2508.16114 | ADJACENT | Astrochemistry NN emulator, iterative rollout stability focus; no hard conservation, wrong domain. |
| RHINE (r-process heating in hydro sims) | arXiv:2507.09040 / PRD 2026 | ADJACENT | NN emulation of r-process *heating* in hydro loops — in-the-loop coupling exists here, but hydro not stellar-evolution, no composition/conservation architecture. |
| r-process final-abundance FFN emulator | arXiv:2412.17918 | ADJACENT | Endpoint-pattern emulator, no per-step dynamics, no conservation. |
| BBNet (BBN abundances) | arXiv:2512.15266 | IRRELEVANT | BBN observable emulator, different problem class. |
| MACE (Maes et al.) | arXiv:2405.03274 + JOSS 10(108) 7148 | ADJACENT | Autoencoder+latent-ODE astrochemistry emulator; latest activity is the 2025 JOSS software paper; no conservation mechanism. |
| AC-CRNN: atom-conserving chemical reaction neural networks | Comb. & Flame 2024 (S1540748924003158) | ADJACENT (**mechanism prior art**) | Hard atom-conservation layer constraining stoichiometric coefficients — conservation-by-construction exists in combustion mechanism *discovery*; not a network-state emulator, not nuclear, no charge/lepton sector. |
| ANN-hard conservation for chemical source terms (Xu group) | Comb. & Flame 2025 (S0010218025001439) | ADJACENT (**mechanism prior art**) | Hard mass/element/energy conservation in combustion kinetics surrogates (H2/air); dense NN, no graph, no weak sector, no nuclear regime. |
| Sturm & Wexler, atom-balance flux architecture for photochemistry | GMD 15, 3417 (2022) | ADJACENT (**closest mechanism prior art for Target A**) | Predict fluxes, map through stoichiometric matrix ΔC = A·S — the Target-A mechanism itself, published 2022 in atmospheric photochemistry. Must be cited in Paper 1; does not break the conjunction (no GNN, no nuclear network, no Yₑ/weak sector, no MESA). |
| Structure-preserving graph neural solver for hyperbolic conservation laws | arXiv:2604.15617 | ADJACENT | Conservation-preserving GNN, but PDE/finite-volume domain, not reaction networks. |
| AI surrogates for multiscale combustion (review) | arXiv:2604.25617 (2026-04) | ADJACENT | Review naming "conservation-explicit neural kinetic surrogates" as an open thread — the mechanism race in combustion is live. |
| Smith & Lovell, ML opportunities for nucleosynthesis (review) | Front. Astron. Space Sci. (2024) | ADJACENT | Only published QSE×ML discussion found: *speculative* (CNNs to classify QSE groups); no implemented equilibrium masking or flux-cancellation analysis in any emulator. |
| Guidry et al., partial-equilibrium explicit integration | arXiv:1112.4738 (non-ML) | ADJACENT (known prior art) | The equilibrium-detection lineage this project already builds on; no ML supervision use. |

## Verdicts

**Leg (i) — GNN on the reaction network:** shared with NuGNN only (v1, XRB regime,
0 citations, no follow-ups by Kim/Chae/Ko/Mumpower/Smith found via `au:` sweeps —
their only 2025-26 nucl-th outputs are NuGNN and a ¹⁹Ne Bayesian evaluation).
Leg not unique alone; conjunction unbroken. **HOLDS.**

**Leg (ii) — hard conservation by construction:** absent from every nuclear/astro
emulator found. Present in adjacent domains: Sturm & Wexler 2022 (flux-through-
stoichiometry, photochemistry), AC-CRNN and ANN-hard (combustion, 2024-25). These are
mechanism prior art to cite, not conjunction breakers (none nuclear, none GNN, none
with a weak/Yₑ sector). **HOLDS, with mandatory prior-art citations.**

**Leg (iii) — silicon-burning / CCSN-progenitor regime:** NNN remains the only ML
emulator in this regime; no new emulator on the Grichener dataset or any MESA/bbq
training set found (query 16: only the authors' own Zenodo record). **HOLDS.**

**Leg (iv) — in-the-loop MESA coupling:** no one has published it, including the NNN
team (still framed as future work; their 2026 output is a progenitor grid). RHINE does
in-the-loop coupling but into *hydro*, for heating only. **HOLDS — and this leg looks
like the shortest-fuse race, since the NNN paper explicitly names it as next.**

**NEW claim — NNN training-label pathology (gh-575 displaced pseudo-equilibria):**
the bug itself is public (MESAHub/mesa issue #575, Aug 2023; MESA known_bugs pages;
NNN Appendix B acknowledges rate errors up to ~24 dex qualitatively). **Not found
anywhere:** (a) that the *shipped training labels* sit at bug-displaced fixed points
7–13 dex from NSE at T9 ≳ 5 with frac>1dex = 1.000; (b) the dt-freeze signature;
(c) the stock-vs-24.08.1 attribution witness; (d) that the labels' Yₑ evolution itself
is wrong. Queries 5, 6, 16 returned zero third-party discussion of NNN data quality.
**Candidate standalone finding — currently unclaimed in the literature.** Framing
caution for any write-up: the *existence* of the bug is the NNN authors' own
disclosure; the new content is the measured consequence for the training labels.

**QSE masking / flux-cancellation / integrated-flux supervision:** no implemented
prior art found in any ML emulator (queries 12, 17); nearest items are the Smith &
Lovell speculative review and the non-ML Guidry lineage. **HOLDS.**

## Caveats / inconclusive edges

- Semantic Scholar citation counts for June-2026 papers (NuGNN: 0) may lag by weeks;
  a fast follow-up to NuGNN could exist unindexed.
- The SPIRIT solver paper could not be resolved to an arXiv id; title indicates
  classical numerics, but it must be re-triaged once indexed.
- Web search cannot exhaustively cover conference proceedings (e.g. NeurIPS ML4PS
  2025/26 workshop papers) — a conservation-GNN-for-kinetics workshop paper would not
  necessarily surface under these queries.

These edges do not change any verdict above, but the sweep is **conclusive on indexed
arXiv/journal literature only**.

## Recommendation

**Proceed — and accelerate Paper 1.** All four legs hold and the conjunction is
intact, but (a) NuGNN is one obvious revision away from adding a conservation layer,
(b) the NNN team has publicly named MESA integration as their next step, and (c) the
combustion community is actively publishing hard-conservation kinetic surrogates and
reviews that name the gap. The label-pathology finding is unreported and time-sensitive
(it concerns another group's public dataset): the external-communication decision
already escalated in STEP6_REPORT should be resolved with the user promptly, and the
finding is strong enough to anchor either Paper 1's data section or a short standalone
note. Next scheduled re-check: next phase boundary, or immediately upon any NuGNN v2 /
NNN follow-up appearing.
