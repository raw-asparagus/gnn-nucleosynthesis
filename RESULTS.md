# RESULTS — measured-numbers log

Every measured number in this project lands here, append-only, with full
provenance. Docs and papers cite this file; nothing numeric is claimed without
a row (or an explicit `sourced`/`derived` label pointing elsewhere).

Columns:
- **date** — ISO date the number was produced
- **quantity** — what was measured
- **value** — the number (with units)
- **tag** — sourced / derived / measured
- **script** — the `scripts/` entry point that produced it
- **code version** — git commit hash
- **data version** — dataset + version/checksum it was computed on

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-07 | free disk on /home/ikaros/projects BEFORE Zenodo zip download | 5 637 349 257 216 B avail (5.5 T fs, 15 G used, 1%) | measured | `df -h` / `df --output=avail -B1` (shell) | 33fad39 | n/a |
| 2026-07-08 | NuclearNeuralNetworks.zip download: size and md5 | 49 057 047 245 B; md5 ab31e56950e696aba7747f2cfca2d403 = manifest value (match) | measured | scripts/download_zenodo.py | 33fad39 | Zenodo 14873443 |
| 2026-07-08 | NuclearNeuralNetworks.zip uncompressed size / file count (`unzip -l`, no extraction) | 115 148 407 532 B (115.15 GB), 3800 entries, single top-level dir `NuclearNeuralNetworks/` | measured | `unzip -l` (shell) | 33fad39 | Zenodo 14873443, md5 ab31e569… |
| 2026-07-08 | zip second-level breakdown (entries, uncompressed) | MESA_models 24 / 0.55 GB; python_scripts_for_analysis 433 / 0.99 GB; test_datasets 3030 / 6.07 GB; trained_NNN_models 282 / 23.80 GB; training_sets 24 / 83.73 GB | measured | `unzip -l` + awk (shell) | 33fad39 | Zenodo 14873443, md5 ab31e569… |
| 2026-07-08 | exact isotope counts of mesa_80 / mesa_151 (test-set headers; model input dims 82/153 concur) | 80 / 151 (paper App. A table omits ca41 from both — paper typo) | measured | configs/isotopes_mesa{80,151}.yaml generation (see file headers) | 33fad39 | Zenodo 14873443 test_datasets |
| 2026-07-08 | extraction verification | 3605 files + 195 dirs on disk == zip listing; 115 148 407 532 B extracted; zip deleted after verification | measured | `unzip`/`find`/`du` (shell) | 0a8dca0 | Zenodo 14873443, md5 ab31e569… |
| 2026-07-08 | free disk AFTER extraction + zip deletion | 5 521 075 277 824 B avail (5.5 T fs, 123 G used, 3%) | measured | `df` (shell) | 0a8dca0 | n/a |

## NNN baseline reproduction (2026-07-08)

Shipped trained models + shipped test sets, run through the upstream
evaluation pipeline (patched for portability only; `repro/nnn/patches/`).
Reference values from the shipped per-dt result CSVs
(`CreateFigures/Figure4_main_results/...`, the numbers behind paper
Figs. 4–5) and from the paper text (arXiv:2503.00115 §3). Pass criterion for
Step 2 was "within ~2×"; achieved exact.

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-08 | ours vs shipped AverageLossesNNN.csv, all 18 (net,dt), 6 metrics each (LinearLoss, YeLoss, AbarLoss, ZbarLoss, EpsNucLoss, EpsNuLoss), last row | ratio ours/theirs = 1.000 in all 108 comparisons (worst factor 1.0000) | measured | repro/nnn/run_all.sh + compare_published.py | de11c8b | Zenodo 14873443, md5 ab31e569… |
| 2026-07-08 | model handshake: independent state_dict-walk loader vs upstream nuclearNN class, 128 test samples, mesa_80 dt=1e-1 | max abs deviation 0.0 (gate ≤ 1e-6) PASS | measured | repro/nnn/check_handshake.py | de11c8b | Zenodo 14873443 |
| 2026-07-08 | Yₑ improvement over approx21, mesa_80 (across 9 dt) | reproduced 377–651 % | measured | repro/nnn/compare_published.py | de11c8b | Zenodo 14873443 |
| 2026-07-08 | Yₑ improvement over approx21, mesa_80 — published | 390–660 % | sourced | Grichener et al. 2025 (arXiv:2503.00115) §3 | n/a | n/a |
| 2026-07-08 | Yₑ improvement over approx21, mesa_151 | reproduced 277–390 % | measured | repro/nnn/compare_published.py | de11c8b | Zenodo 14873443 |
| 2026-07-08 | Yₑ improvement over approx21, mesa_151 — published | 280–400 % | sourced | arXiv:2503.00115 §3 | n/a | n/a |
| 2026-07-08 | Ā improvement, mesa_80 / mesa_151 | reproduced 149–291 % / 256–357 % | measured | repro/nnn/compare_published.py | de11c8b | Zenodo 14873443 |
| 2026-07-08 | Ā improvement — published | 150–290 % / 260–360 % | sourced | arXiv:2503.00115 §3 | n/a | n/a |
| 2026-07-08 | e_nuc improvement, mesa_80 / mesa_151 | reproduced 249–419 % / 284–772 % | measured | repro/nnn/compare_published.py | de11c8b | Zenodo 14873443 |
| 2026-07-08 | e_nuc improvement — published | 250–450 % / 280–750 % | sourced | arXiv:2503.00115 §3 | n/a | n/a |
| 2026-07-08 | ν-loss crossover sign | NNN better than approx21 for dt ≤ 1e-1 s (improvement 108–1.3e6 %), worse for dt ∈ {1e0, 1e1, 1e2} s (93–3 %) — both nets | measured | repro/nnn/compare_published.py | de11c8b | Zenodo 14873443 |
| 2026-07-08 | ν-loss crossover — published | comparable around dt = 0.1 s; NNN worse after | sourced | arXiv:2503.00115 §3 | n/a | n/a |
| 2026-07-08 | NNN relative Yₑ error (ΔYₑ/Yₑ, per-dt averages) | mesa_80 0.332–0.535 %, mesa_151 0.548–0.726 % | measured | repro/nnn/compare_published.py | de11c8b | Zenodo 14873443 |
| 2026-07-08 | NNN relative Yₑ error — published | 0.4–0.75 % (below 0.75 % at all dt) | sourced | arXiv:2503.00115 §3/§5 | n/a | n/a |
| 2026-07-08 | per-isotope mean ΔX band | mesa_80 dt=1e-3: 90 % of isotopes in [1e-4, 1e-1], median 3.2e-3, outliers all BELOW band; mesa_151 dt=1e0: 80 % in band, median 7.8e-4, outliers all below | measured | repro/nnn/check_dx_band.py | de11c8b | Zenodo 14873443 |
| 2026-07-08 | per-isotope ΔX band — published | most isotopes in 1e-4 ≲ ΔXᵢ ≲ 1e-1; light isotopes smallest errors | sourced | arXiv:2503.00115 §3, Fig. 3 | n/a | n/a |

Notes: (i) NNN-vs-approx21 ratios use the SHIPPED approx21-vs-large-net loss
files (`AverageLosses21to80.csv`); the approx21 bbq runs themselves are also
shipped, so an end-to-end recomputation of the small-net errors is possible
later if needed — not blocked.

## Yₑ-controller membership in mesa_80 / mesa_151 (2026-07-08)

Derived from the exact network isotope lists (`configs/isotopes_mesa80.yaml`,
`configs/isotopes_mesa151.yaml`; sourced from Zenodo 14873443 test-set column
headers, cross-checked against Grichener et al. 2025 App. A). Controller sets
per the Step-2 task spec (EC controllers; β-decay partners). Tag: measured
(membership lookup), code version 33fad39.

| nucleus | role | mesa_80 | mesa_151 |
| --- | --- | --- | --- |
| co55 | EC | yes | yes |
| ni56 | EC | yes | yes |
| fe55 | EC | **NO** | yes |
| fe54 | EC | yes | yes |
| v51 | EC | **NO** | yes |
| cr53 | EC | **NO** | yes |
| s33 | EC | yes | yes |
| cl35 | EC | yes | yes |
| ar37 | EC | yes | yes |
| mn56 | β partner | **NO** | yes |
| cr56 | β partner | **NO** | **NO** |
| fe59 | β partner | **NO** | yes |
| fe61 | β partner | **NO** | yes |
| co61 | β partner | **NO** | yes |
| co63 | β partner | **NO** | **NO** |
| co60 | β partner | **NO** | yes |
| co59 | β partner | **NO** | yes |

**Flags (see also the Step-3 pynucastro rate-level inventory below):** mesa_80
carries only 6/9 EC controllers and 0/8 β-decay partners —
its Yₑ evolution runs through a materially thinner weak-reaction set than
mesa_151. cr56 and co63 are in NEITHER shipped network. Also relevant: sc45
(the ⁴⁵Sc(p,γ)⁴⁶Ti bottleneck reactant named in CLAUDE.md) is absent from
mesa_80 (mesa_80 has only sc43; mesa_151 has sc43–sc49) — that kill-test
instrument applies to mesa_151 only. These asymmetries feed size-transfer and
loss-weighting design directly.

## Training-CSV audit (2026-07-08, Step 3)

Full-column audit of the 18 training CSVs (both networks × 9 dt files),
measuring the real dt grid, row identity, and label normalization. These
rows retire the Step-2 open flags on the dt grid, the join key, and the
ε_ν normalization at dt ≥ 10 s.

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-08 | rows per training CSV (all 18 files) | 1 041 400 each (identical across dt and networks) | measured | scripts/check_training_csvs.py | 57241e3 | Zenodo 14873443, md5 ab31e569… |
| 2026-07-08 | measured dt grid, mesa_80 [s] | 1.0110e-6, 1.0314e-5, 1.0508e-4, 1.0128e-3, 1.0316e-2, 1.0508e-1, 1.0128e0, 1.0316e1, 1.0508e2 (full precision in configs/dt_grid_measured.yaml) | measured | scripts/check_training_csvs.py | 57241e3 | Zenodo 14873443, md5 ab31e569… |
| 2026-07-08 | measured dt grid, mesa_151 [s] | 1.0090e-6, 1.0292e-5, 1.0484e-4, 1.0013e-3, 1.0199e-2, 1.0388e-1, 1.0582e0, 1.0105e1, 1.0293e2 (full precision in configs/dt_grid_measured.yaml) | measured | scripts/check_training_csvs.py | 57241e3 | Zenodo 14873443, md5 ab31e569… |
| 2026-07-08 | Age constancy within each CSV | exactly 1 unique Age value per file (all 18) | measured | scripts/check_training_csvs.py | 57241e3 | Zenodo 14873443, md5 ab31e569… |
| 2026-07-08 | row alignment across the 9 dt files (logT, logRho + 4 sentinel initial_* columns, full-column equality vs the 1e-6 file) | ALIGNED, both networks — row index is a valid per-network identity key (state_id) | measured | scripts/check_training_csvs.py | 57241e3 | Zenodo 14873443, md5 ab31e569… |
| 2026-07-08 | (logT, logRho) duplicate rows per file | 154 405 of 1 041 400 (values rounded to 3 decimals) — NOT unique, rejected as join key; corrects the Step-2 uniqueness claim | measured | scripts/check_training_csvs.py | 57241e3 | Zenodo 14873443, md5 ab31e569… |
| 2026-07-08 | full-initial-state duplicate rows (logT, logRho, all initial_*) | 0, both networks | measured | scripts/check_training_csvs.py | 57241e3 | Zenodo 14873443, md5 ab31e569… |
| 2026-07-08 | final_* floor | min over all final_* columns = 1.000e-15 exactly, both networks (matches upstream buildDatabase 1e-15 clamp) | measured | scripts/check_training_csvs.py | 57241e3 | Zenodo 14873443, md5 ab31e569… |
| 2026-07-08 | ε_ν normalization at dt ≥ 10 s (adjacent-dt row-exact median |eps_nu| ratios) | mesa_80: 1e1/1e0 = 0.983, 1e2/1e1 = 0.878; mesa_151: 0.898, 0.712 — smooth continuity, NO ~1e3 jump ⇒ uniform ÷1e16 in ALL 18 training CSVs; the upstream 1e13 comment (TestNNNs/runNNNsOnTestMesa80.py:263) does not apply to the training sets; quarantine EMPTY | measured | scripts/check_training_csvs.py | 57241e3 | Zenodo 14873443, md5 ab31e569… |

## Graph export + conservation layer (2026-07-08, Step 3)

pynucastro 2.12.0 export of mesa_80 / mesa_151 from the authoritative isotope
YAMLs (REACLIB + tabular weak rates, duplicate links resolved tabular-wins;
tabular ordering ffn<oda<pruet_fuller<langanke<suzuki, later wins).
**PROVISIONAL reaction set** — pynucastro's REACLIB-filtered set is not
guaranteed to equal MESA r23.05.1's softwired net; retired at the Step-4
bbq cross-check (ADR 0002). Conservation exactness holds for ANY rate set.
Artifacts data/stoich/nu_mesa{80,151}.npz + data/graphs/mesa{80,151}.graphml
are regenerable + gitignored; npz content hashes below are timestamp-free.

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-08 | isotope counts (graph export, asserted at build) | mesa_80: 80, mesa_151: 151 (ca41 in both) | measured | scripts/export_stoich_matrix.py | 1cde6a5 | configs isotope YAMLs (Zenodo 14873443) + pynucastro 2.12.0 |
| 2026-07-08 | reaction counts (= flux-head output dim) | mesa_80: 610 (572 ReacLib + 38 tabular; 19 duplicate links resolved); mesa_151: 1522 (1358 + 164; 78 resolved) | measured | scripts/export_stoich_matrix.py | 1cde6a5 | pynucastro 2.12.0 |
| 2026-07-08 | weak-sector breakdown | mesa_80: 46 weak = 21 EC + 19 β⁻ + 6 β⁺ (27 lower Yₑ, 19 raise; 8 ReacLib-only); mesa_151: 174 = 84 EC + 85 β⁻ + 5 β⁺ (89 lower, 85 raise; 10 ReacLib-only). mesa_80 weak sector NOT one-directional at rate level — the Step-2 0/8 finding concerns the named NNN controller partners, not β⁻ channels generally. Full 220-row inventory: docs/weak-inventory-step3.md | measured | scripts/graph_metrics.py --weak-inventory | 1cde6a5 | pynucastro 2.12.0 |
| 2026-07-08 | per-chapter reaction census | mesa_80: ch1:4, ch2:149, ch3:2, ch4:151, ch5:246, ch6:6, ch7:3, ch8:2, ch9:6, ch10:3, tabular:38; mesa_151: ch1:5, ch2:348, ch3:3, ch4:349, ch5:630, ch6:7, ch7:3, ch8:3, ch9:7, ch10:3, tabular:164 | measured | scripts/graph_metrics.py | 1cde6a5 | pynucastro 2.12.0 |
| 2026-07-08 | forward/reverse composition (both definitions; pynucastro 2.12.0 has no per-rate .reverse) | mesa_80: 282 derived-from-inverse, 301 reverse-by-Q-sign (of 610); mesa_151: 674 / 756 (of 1522) | measured | scripts/graph_metrics.py | 1cde6a5 | pynucastro 2.12.0 |
| 2026-07-08 | graph radius/diameter, undirected views (both networks identical) | bipartite (no I→I): r=3, d=6; bipartite + I→I: r=2, d=4; isotope projection (I→I only): r=1, d=2; all connected, 1 component | measured | scripts/graph_metrics.py | 1cde6a5 | pynucastro 2.12.0 |
| 2026-07-08 | implied processor depth K = ⌈radius⌉ + 2 | K=5 on the bipartite message-passing graph (K=4 counting I→I shortcut edges) — phase0-checklist row 1 | measured | scripts/graph_metrics.py | 1cde6a5 | pynucastro 2.12.0 |
| 2026-07-08 | cond(ν) full (nonzero singular values), rank, nullity | mesa_80: 41.70, rank 79, nullity 1; mesa_151: 57.55, rank 150, nullity 1; extended ν̃: 41.02 / 54.17, full row rank. (Active-set cond(S_active) is a Step-6 kill-test quantity.) | measured | scripts/graph_metrics.py | 1cde6a5 | pynucastro 2.12.0 |
| 2026-07-08 | cond(CCᵀ) | mesa_80: 3.947e4; mesa_151: 1.029e5 | measured | scripts/graph_metrics.py | 1cde6a5 | pynucastro 2.12.0 |
| 2026-07-08 | conservation gate (BLOCKING; 30 tests: column exactness, random-φ drift 10 seeds × 6 scales 1e0…1e-20, dYₑ survival, structural weak-mask contract, both networks) | PASS — column drifts exactly 0.0 (D_A = D_Q = strong-leak = 0.0); random-flux drift within max(1e-12·s, 1e-13·G); dYₑ ≠ 0 through weak columns (e.g. −0.432 / −1.584 under seed-0 12-decade flux) | measured | uv run pytest tests/test_conservation.py + scripts/check_conservation.py | 1cde6a5 | pynucastro 2.12.0 |
| 2026-07-08 | npz content hashes (timestamp-free sha256) | nu_mesa80: 691016f07e7fb17e…; nu_mesa151: cfe43868ad21c4dc… (full hashes printed by export script; deterministic across re-exports) | measured | scripts/export_stoich_matrix.py | 1cde6a5 | pynucastro 2.12.0 |
| 2026-07-08 | Target B projector (extended space, QR form) | max relative constraint residual over 20 decades of dY: 6.68e-17 (mesa_80) / 1.04e-16 (mesa_151) [gate ≤ 1e-12]; ‖P²−P‖∞ ≤ 1.0e-15; P symmetric to 0.0; rank = m−3 exactly; weak dYₑ change through projection ≤ 3.4e-21 | measured | scripts/check_projector.py | edef464 | pynucastro 2.12.0 |

## MESA r23.05.1 + bbq install (2026-07-08, Step 3)

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-08 | MESA SDK installed | mesasdk-x86_64-linux-23.7.3 (md5 82ba6f4da21c8afe8e50bb0bce1b9435; SDK page md5 unscrapable — recorded, not verified against page), at ~/mesasdk (538 MB) | measured | scripts/install_mesa_full.sh | 57241e3 | Townsend SDK page |
| 2026-07-08 | MESA r23.05.1 source | Zenodo record 7983526, mesa-r23.05.1.zip, md5 77d598cc6db7e1714c0c2ecab61973ad = API checksum (match), at ~/mesa-r23.05.1 (17 GB built) | measured | scripts/install_mesa_full.sh | 57241e3 | Zenodo 7983526 |
| 2026-07-08 | MESA build + module self-tests | "MESA installation was successful" banner confirmed; ./install wall time 570 s on 12 cores (OMP_NUM_THREADS=12) | measured | scripts/install_mesa_full.sh (logs scripts/mesa_install_logs/) | 57241e3 | Zenodo 7983526 |
| 2026-07-08 | bbq build + smoke run | github.com/rjfarmer/bbq @ 9783df31 (2023-08-29) linked against MESA_DIR in 3 s; binary executes, loads MESA weak-rate tables, exits with "Must select one mode" absent an inlist (expected) | measured | scripts/install_mesa_full.sh | 57241e3 | bbq 9783df31 |
| 2026-07-08 | install deviations from supported config | no root: csh/tcsh not installed (SDK prereq warning; build unaffected); libX11 dev symlink absent → user-local ~/.local/lib/libX11.so → libX11.so.6 + LIBRARY_PATH workaround; clean fix later: sudo apt install csh libx11-dev | measured | scripts/install_mesa_full.sh | 57241e3 | n/a |

## Missing Sobol rows in the training sets (2026-07-09, Step 4 Task 5)

The training CSVs have no sample id and no Yₑ column; rows were matched back
to the shipped 2²⁰-point Sobol grid file by nearest neighbour in
box-normalized (logT, logRho, Yₑ) with Yₑ_initial reconstructed as
Σ Zᵢ Xᵢ/Aᵢ from the initial_* columns. Match validity is enforced by exact
counts (0 unmatched rows, 0 grid-point collisions, missing = 2²⁰ − N_rows
exactly). The grid was generated by an UNSEEDED scrambled scipy Sobol
sampler (gridGenerator.py), so the shipped grid file is the only ground
truth; regeneration cannot reproduce it.

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-09 | rows matched to Sobol grid | 1 041 400 matched, 0 unmatched, 0 collisions, 7 176 grid points missing — both networks exactly | measured | scripts/sobol_missing_rows.py | 98cee91 | Zenodo 14873443 training_sets |
| 2026-07-09 | match distance (normalized) | p99 = 2.05e-3 / 2.06e-3, max = 5.1e-3 / 5.0e-3 (mesa_80 / mesa_151); dominated by the CSVs' 3-decimal logT/logRho rounding plus reconstructed-Yₑ offsets up to ~1.5e-4 (shipped compositions only approximate the target Yₑ); typical grid NN spacing ~1e-2 | measured | scripts/sobol_missing_rows.py | 98cee91 | Zenodo 14873443 training_sets |
| 2026-07-09 | missing-row index structure | BLOCK-STRUCTURED, not random: mesa_80 = exactly 2 contiguous Sobol-index runs [0, 4100) + [1045500, 1048576); mesa_151 = same two blocks minus 2 points recovered (4034, 1048346) plus 2 isolated genuine failures (440690, 608682) and run split (0,4034)+(4035,65)+(1045500,2846)+(1048347,229) — consistent with lost first/last job-array batches, not with scattered bbq crashes | measured | scripts/sobol_missing_rows.py | 98cee91 | Zenodo 14873443 training_sets |
| 2026-07-09 | missing-set spatial uniformity | χ²/dof ≤ 0.1 on all three 20-bin marginals (bins 356–361 vs 359 uniform), both networks — HYPER-uniform, as expected for contiguous blocks of a stratified Sobol sequence; no corner or edge under-coverage anywhere in the box | measured | scripts/sobol_missing_rows.py | 98cee91 | Zenodo 14873443 training_sets |
| 2026-07-09 | missing-set overlap between networks | 7 174 of 7 176 shared | measured | scripts/sobol_missing_rows.py | 98cee91 | Zenodo 14873443 training_sets |
| 2026-07-09 | dt-file row alignment | logT/logRho arrays byte-identical between 1e-1 and 1e2 files, both networks — confirms state_id = row index is a valid join key across the 9 dt files | measured | scripts/sobol_missing_rows.py | 98cee91 | Zenodo 14873443 training_sets |

**Verdict (Task 5): benign.** The 0.68% missing mass is two contiguous
chunks at the head and tail of the Sobol sequence (≈ first 4 100 + last
3 076 samples), spatially quasi-uniform over the box by construction of the
sequence. No OOD-gating or kill-test region is preferentially under-covered;
only 2 isolated mid-sequence failures exist (mesa_151), 0 in mesa_80.
Figures: docs/figures/sobol_missing_mesa{80,151}.png.

## Reaction-set reconciliation vs MESA r23.05.1 (2026-07-09, Step 4 Task 1)

MESA-side inventories extracted from the softwired mesa_80.net / mesa_151.net
by the src/mesa_probes/ Fortran driver (dump_net mode); diffed against the
raw pynucastro graphs on canonical directed sorted-multiset keys with
lepton-channel disambiguation (pp/pep). Convention, per-entry dispositions,
and analysis: docs/reaction-reconciliation.md + configs/reaction_disposition_
mesa{80,151}.yaml. Decision: ADR 0003.

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-09 | canonical reaction counts | MESA 607 / pyna 610 (mesa_80); MESA 1518 / pyna 1522 (mesa_151) | measured | scripts/reconcile_reactions.py | b559dde | MESA r23.05.1 (Zenodo 7983526) + pynucastro 2.12.0 |
| 2026-07-09 | disposition tallies (original suzuki-topped ordering) | mesa_80: 565 CLEAN + 42 DIFF_PROVENANCE (14 weak-table OHMT-vs-suzuki + 28 construction) + 0 MESA_ONLY + 3 PYNA_ONLY; mesa_151: 1463 + 55 (23 + 32) + 0 + 4 | measured | scripts/reconcile_reactions.py | b559dde | ditto |
| 2026-07-09 | disposition tallies (adopted MESA-matched ordering) | mesa_80: 579 CLEAN + 28 DIFF_PROVENANCE (construction only) + 0 + 3; mesa_151: 1486 + 32 + 0 + 4 — weak-table mismatches 14/23 → 0/0 | measured | scripts/reconcile_reactions.py | b559dde | ditto |
| 2026-07-09 | MESA_ONLY entries | 0 both networks — graphs were a strict superset; nothing added | measured | scripts/reconcile_reactions.py | b559dde | ditto |
| 2026-07-09 | PYNA_ONLY dropped channels | p+be9⇄n+p+he4+he4 (2), n+p+he4+he4→he3+li7 (both nets); + n16→c12+he4 β⁻-delayed α (mesa_151) | measured | scripts/reconcile_reactions.py | b559dde | ditto |
| 2026-07-09 | reconciled graph exports (= new flux-head dims) | mesa_80: 607 reactions (569 ReacLib + 38 tabular; 46 weak = 21 EC + 19 β⁻ + 6 β⁺); mesa_151: 1518 (1354 + 164; 173 weak = 84 EC + 84 β⁻ + 5 β⁺); provisional_reaction_set=False, disposition_sha256 in npz | measured | scripts/export_stoich_matrix.py | b559dde | ditto |
| 2026-07-09 | npz content hashes (post-reconciliation) | nu_mesa80: d2edb3e90403a8be…; nu_mesa151: dc8430ce977b492a… | measured | scripts/export_stoich_matrix.py | b559dde | ditto |
| 2026-07-09 | graph extents + conditioning (post-reconciliation) | radius/diameter/K unchanged (bipartite r=3 d=6 K=5; +I→I r=2 d=4 K=4); cond(ν): 41.57 / 57.86 (were 41.70 / 57.55); cond(CCᵀ) unchanged (3.947e4 / 1.029e5) | measured | scripts/graph_metrics.py | b559dde | ditto |
| 2026-07-09 | conservation gate + projector (post-reconciliation, BLOCKING) | PASS, 49 tests, unchanged tolerances; column drifts exactly 0.0; dYₑ nonzero through weak columns; projector residual ≤ 1.04e-16 | measured | uv run pytest tests/test_conservation.py tests/test_projector.py | b559dde | ditto |
| 2026-07-09 | weak-table provenance (per matched pair, MESA side parsed from weakreactions.tables headers) | pre-fix mismatches all sd-shell A=17–28, MESA=OHMT vs pyna=suzuki (14 mesa_80 / 23 mesa_151); post-fix 0 — every matched weak pair uses the label configuration's table family (LMP > Oda > FFN, use_suzuki=.false.) | measured | scripts/reconcile_reactions.py | b559dde | ditto |
| 2026-07-09 | carried to Task 2 (rate values, not membership) | 14 / 16 REACLIB fit-vs-derived direction-swapped pairs (snapshot 20171020 vs pynucastro 2.12.0); be7→li7 EC (MESA S13 h5 table vs pyna REACLIB ec fit); r_he4_ap_li7 (MESA source=other) | measured | scripts/reconcile_reactions.py | b559dde | ditto |

## Appendix-B bug state of stock MESA r23.05.1 (2026-07-09, Step 4 Task 4)

Static locus: rates/private/reaclib_support.f90 compute_rev_ratio applies the
detailed-balance phase-space factor fac = (1e9·kB/(2πℏ²N_A))^{3/2}/N_A
(= 9.868e9, log₁₀ = 9.994) and its T^{3/2} only in the single-product branch;
upstream fix = MESAHub/mesa gh-575, first released in 24.08.1 (changelog:
"incorrect phase space factors for reverse reaction rates involving greater
than 2 reactants or products… inconsistent equilibrium compositions … NSE, at
temperatures exceeding 4 GK"). The Zenodo training labels were generated with
the authors' LOCALLY FIXED r23.05.1 (paper App. B), so labels are clean and
OUR stock MESA is the outlier on the affected channels.

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-09 | affected channels (multi-body DB inverses, fwd Nout≠1 & ΔN≠0, inverse_exp=0) | 7 (mesa_80) / 8 (mesa_151): all light-nuclide (he3/be7/li7/b8/b11/be9/h2 sector); the paper's ³H channels cannot appear (no tritium in either net) | measured | scripts/appendixb_check.py (dump_inverse probe) | b8665c0 | MESA r23.05.1 stock |
| 2026-07-09 | empirical discrepancy vs pynucastro 2.12.0, T9∈{1.6,4.0,7.9} | \|Δlog10\| = 10.0–11.1 (\|ΔN\|=1, sign follows ΔN) and 20.6–22.7 (\|ΔN\|=2: h1+h1+he4+he4→he3+be7), tracking \|ΔN\|·log10(fac·T9^{3/2}) within ≲0.35 dex | measured | scripts/appendixb_check.py | b8665c0 | MESA r23.05.1 stock + pynucastro 2.12.0 |
| 2026-07-09 | BEYOND the paper: chapter-8 photodisintegration reverses (1→3) | c12→3·he4, be9→neut+2·he4, li6→neut+h1+he4 all LOW by 9.5–11.3 dex (fac¹·T^{3/2} applied where fac²·T³ required) — includes the triple-α reverse | measured | scripts/appendixb_check.py | b8665c0 | ditto |
| 2026-07-09 | anomalous channel | r_h1_h1_he4_to_he3_he3: Δlog10 only +0.6/+1.8/+2.7 (T9 1.6/4/7.9), not the ~10.9 predicted — partial cancellation unexplained; excluded regardless | measured | scripts/appendixb_check.py | b8665c0 | ditto |
| 2026-07-09 | harness control (all matched clean REACLIB forwards, T9=4) | median \|Δlog10\| = 0.0 exactly (mesa_80 & mesa_151); tails (p99 0.67/0.14, max 2.4/0.85) are REACLIB-snapshot differences → Task 2 scope | measured | scripts/appendixb_check.py | b8665c0 | ditto |
| 2026-07-09 | verdict + consequence | stock r23.05.1 HAS the bug; labels (patched MESA) do NOT ⇒ our-MESA≠label-MESA on 9/11 channels (configs/appendixb_excluded_channels.yaml) — excluded from all rate-agreement gates and κ/flux analyses; backport patch drafted (patches/0001-reaclib-reverse-phase-space.patch, dry-run clean, NOT applied — user decision pending) | measured | scripts/appendixb_check.py | b8665c0 | full table data/mesa_cache/appendixb_comparison.csv |

## Rate-level cross-check vs label configuration (2026-07-10, Step 4 Task 2)

Label configuration = stock r23.05.1 + bbq defaults (REACLIB jina 20171020,
weaklib LMP>Oda>FFN, use_suzuki=.false., screening chugunov) + the authors'
gh-575 fix. Grid: 7 T9 × 3 ρ × 3 Yₑ. Full analysis:
docs/rate-crosscheck.md; outliers configs/rate_outliers.yaml; raw tables
data/mesa_cache/crosscheck_*.csv.

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-10 | REACLIB forwards, matched clean | median \|Δlog10\| = 4.4e-16 / 8.9e-16 (mesa_80/151) — bit-identical; tail = snapshot refits, 25 channels flagged (worst n13(p,γ)o14 pair −3.7 dex; pp/CNO sector) | measured | scripts/crosscheck_rates.py | 156c73f | MESA r23.05.1 + pynucastro 2.12.0 |
| 2026-07-10 | DB inverses | median \|Δlog10\| = 0.048 / 0.095; signed median +0.005→+0.013 dex over T9 1.6→7.9 ⇒ pf-handling systematic (MESA applies winvn pf ratios, pyna v-flag fits are pf-free); 93 channels > 0.5 dex flagged | measured | scripts/crosscheck_rates.py | 156c73f | ditto |
| 2026-07-10 | construction-swapped pairs (14/16) | median \|Δlog10\| = 0.0004 / 0.0006 — snapshots numerically consistent, only fit/derived labels differ; NOT a defect | measured | scripts/crosscheck_rates.py | 156c73f | ditto |
| 2026-07-10 | weak tabular, per-pair sources | 0 table-source mismatches (post-ADR 0003); at T9=5 table node median \|Δlog10\| = 0.003; off-node 0.03–0.18 dex = interpolation (MESA bilinear vs pyna interpolant); β⁻ tail ≤ 0.8 dex (13 channels > 0.5 flagged) | measured | scripts/crosscheck_rates.py | 156c73f | ditto |
| 2026-07-10 | Yₑ-controller EC channels (LMP/OHMT-matched) | median \|Δ\| 0.009–0.095 dex, at-node ≤ 0.012 dex (co55, ni56, fe54, fe56, v51, s33, cl35, ar37) | measured | scripts/crosscheck_rates.py | 156c73f | ditto |
| 2026-07-10 | weak-table edge behavior | all box states interior (T9 ≤ 7.9 < 30, logρYₑ ≤ 8.7 < 11); outside: MESA CLIPS to edge (eval_weak.f90), pynucastro EXTRAPOLATES (measured T9=40, 100) | measured | scripts/crosscheck_rates.py + source | 156c73f | ditto |
| 2026-07-10 | be7→li7 EC provenance | MESA S13 h5 (T,ρYₑ) table vs pyna reaclib ec fit: 2.58–2.77 dex — open flag, light sector | measured | scripts/crosscheck_rates.py | 156c73f | ditto |
| 2026-07-10 | screening determination (training labels) | MESA chugunov ≡ pynucastro chugunov_2007: median ratio 0.99999, max \|log10\| = 0.0021 over all strong pairs × grid (both nets); chugunov_2009 does NOT match (max 0.52 dex); MESA extended ≡ pyna screen5 to ~1e-4 (harness validation); pyna screening fns return ln(factor) | measured | scripts/crosscheck_rates.py | 156c73f | ditto |
| 2026-07-10 | MESA 24.08.1 side-by-side install | Zenodo 13353788, mesa-24.08.1.zip md5 75418c76… verified; built + module self-tests passed ("MESA installation was successful"); probe binary mesa_probe24 | measured | scripts/install_mesa_24081.sh | 156c73f | Zenodo 13353788 |
| 2026-07-10 | gh-575 fix verification | affected channels collapse 10.0–22.7 dex (stock) → ≤ 1.9 dex (24.08.1) except r_h1_h1_he4_to_he3_he3: 2.7 dex in BOTH versions ⇒ not a gh-575 channel, open flag | measured | scripts/appendixb_check.py + mesa_probe24 | 156c73f | MESA 24.08.1 + pynucastro 2.12.0 |
| 2026-07-10 | severe outlier census | 135 channels (93+ db_inverse, 25 forward refits, 13 weak tabular, 4 weak reaclib) — every one class-explained or open-flagged; clustered in pp/CNO light sector, none in the Yₑ-controller set | measured | scripts/crosscheck_rates.py | 156c73f | ditto |

## κ-floor screen at NSE (2026-07-10, Step 4 Task 3)

NSE compositions from pynucastro's solver (all 27 states per net converged;
T9 ∈ {5, 6.3, 7.9} × ρ ∈ {1e7,1e8,1e9} × Yₑ ∈ {0.45,0.48,0.498}; Coulomb
corrections and screening off, consistent with the bare-rate comparison).
κ_r per strong/EM forward-reverse pair; suspect = min-over-states κ > 1e-3.
Analysis: docs/rate-crosscheck.md §κ-floor; raw data
data/mesa_cache/kappa_nse_mesa_{80,151}.csv.

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-10 | κ at NSE, graphs as built (pyna raw v-flag reverses) | median 6.6e-2 / 1.3e-1 (mesa_80/151), p90 0.39/0.49; suspects 268/280 and 656/672 pairs — pervasive SPURIOUS floor | measured | scripts/kappa_floor_screen.py | f66328a | pynucastro 2.12.0 |
| 2026-07-10 | attribution (dispositive) | DerivedRate(source_rate=fwd, use_pf=True) reverses collapse worst pairs κ 0.44–0.64 → 1.7e-12…1.3e-11 (rate-eval precision); pf corrections 0.22×–4.5× at NSE T ⇒ floor lives ENTIRELY in the pf-free v-flag reverses (pynucastro side of the comparison, not physics) | measured | scripts/kappa_floor_screen.py (inline DerivedRate test) | f66328a | pynucastro 2.12.0 |
| 2026-07-10 | κ at NSE, stock MESA r23.05.1 | median 3.6e-3 / 3.3e-3, p90 1.2e-2/7.2e-3 (own pf-interpolation + winvn provenance); κ → 1.0 exactly on gh-575 channels | measured | scripts/kappa_floor_screen.py | f66328a | MESA r23.05.1 |
| 2026-07-10 | κ at NSE, MESA 24.08.1 | median 5.3e-3/4.9e-3 but p90 0.76: subset of (n,α)/(p,α) pairs κ ~ 0.75 that are clean in stock — consistent with its newer REACLIB snapshot carrying independently-fitted non-DB-linked pair members; open observation (not the label config) | measured | scripts/kappa_floor_screen.py | f66328a | MESA 24.08.1 |
| 2026-07-10 | BLOCKING Step-5/6 gate | every κ_r / kill-test computation must build reverse rates as DerivedRate(use_pf=True) or take MESA-side rates; raw v-flag reverses forbidden at T9 ≥ 3 (they manufacture κ floors up to 0.8 and would corrupt the Target-A viability verdict) | measured (basis) | scripts/kappa_floor_screen.py | f66328a | — |

## Flux engine: compiled evaluator + pf-corrected reverses (2026-07-10, Step 5 WP2)

Engine = src/gnn_nucleo/fluxes/ (compile/engine/screening/db_reverses):
canonical 607/1518 collections with every raw v-flag reverse replaced by
DerivedRate(source_rate=fwd, use_pf=True) (the Step-4 gate), all rates
evaluated as one coefficient-tensor matmul + rebuilt pf splines + vectorized
tabular bilinear + vectorized chugunov_2007. Column order = ν export.
Oracles: pynucastro 2.12.0 scalar paths on the same states.

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-10 | v-flag replacement census | mesa_80: 280/280 replaced, mesa_151: 672/672 replaced; ALL forward partners found in-collection; 0 failures (spin states available throughout); pf-table-less nuclei (log_pf=0 fallback, same as pyna): light sector only (d, He3, He4, Li7, Be7/9/10, B8, C12/13, N13/14/15) | measured | tests/test_flux_compile.py + fluxes.db_reverses | 20f1bb2 | pynucastro 2.12.0 |
| 2026-07-10 | engine λ vs pyna rate.eval (all rates × 6 box states) | worst rel 1.3e-12 (gate 5e-12; floor = fp association of DB terms baked into set coefficients vs added at runtime, \|Q/kT\| ~ O(500) in exponent); tabular + screened paths within same gate; chugunov_2007 vec vs scalar ≤ 1e-12 | measured | tests/test_flux_compile.py | 20f1bb2 | pynucastro 2.12.0 |
| 2026-07-10 | ν·R vs pyna evaluate_ydots (NSE states) | within 1e-12 × per-species GROSS flux Σ_j\|ν_ij\|R_j on every species/state (net ẏ is cancellation-dominated at NSE — gross-relative is the honest gate, cf. conservation-gate convention) | measured | tests/test_flux_engine.py | 20f1bb2 | pynucastro 2.12.0 |
| 2026-07-10 | κ at NSE, pf-corrected engine, screening OFF (T9 ≥ 5, flux-carrying strong pairs = upper half by f⁺) | median 2.6e-12, p90 8.2e-12, max 1.5e-11 — Step-4 spurious floor (6.6e-2/1.3e-1) ELIMINATED; detailed balance exact to rate-eval precision | measured | tests/test_flux_engine.py + inline bench | 20f1bb2 | pynucastro 2.12.0 |
| 2026-07-10 | κ at NSE, label screening config (chugunov_2007 ON) | median ~7.4e-2 over flux-carrying strong pairs (mesa_80, T9 6.3, ρ 1e9): screening is applied per reaction from its OWN reactant pairs, so a screened capture pairs with an unscreened photodissociation and κ ≈ \|Δln scor\| — REAL property of the rate configuration (pyna and MESA net_screen both per-reaction), NOT a pf artifact; Step-6 κ thresholds must use the unscreened κ for equilibrium detection or account for the screening offset | measured | tests/test_flux_engine.py | 20f1bb2 | pynucastro 2.12.0 |
| 2026-07-10 | mesa_probe24 spot checks (mesa_80) | clean forwards (si28/s32/ca40 (α,γ) fwd) ≤ 0.004 dex; pf-corrected DB reverses ≤ 0.1 dex vs 24.08.1 reverses; gh-575 channel c12→3α within fixed-class band (≤2 dex vs stock's ~10) | measured | tests/test_flux_mesa_spot.py | 20f1bb2 | MESA 24.08.1 |
| 2026-07-10 | engine throughput (4096-state batches, single core) | mesa_80: 7.06e5 states/min/core, mesa_151: 2.20e5 states/min/core (gate ≥ 1e3: exceeded 706×/220×); full 1,041,400-state corpus = 1.5 / 4.7 core-minutes compute (I/O-dominated in practice); compile 6.0/6.4 s | measured | inline bench (README of data/fluxes run to follow) | 20f1bb2 | pynucastro 2.12.0 |

## dt = 1e-6 s label handshake (2026-07-10, Step 5 Task 2)

Flux-side analogue of the Step-2 model handshake: engine ΔX_pred vs shipped
labels, no model in between. Grid mode on the 30k stratified subsample
(configs/step5_subsample_*), trajectory mode on the 20 selected
constant-(T,ρ) test trajectories per net (trapezoid prediction from engine ẏ
at both interval ends; RHS-stability + 1e-15-floor censoring; net tolerance
max(0.1·|ΔX_lab|, 3ε_lab(Xᵢ+X_f), 2e-15) with ε_lab = robust 10×median
calibration; rate-level residual = |ΔX_pred−ΔX_lab|/(A·gross·dt)).
Script: scripts/step5_handshake.py.

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-10 | grid-mode premise (dt₁ = 1.0110e-6/1.0090e-6 s) | VOID: 99.99% / 100.00% (mesa_80/151) of (state,isotope) cells have τ < dt — Sobol initial compositions carry free nucleons (median X_neut 1.7e-2), the shortest label step is a STIFF RELAXATION (label \|ΔX\|/X median ~1), not a linear step; 20 / 0 linearizable cells of 2.4M/4.5M. Consequence for the emulator: dt=1e-6 labels encode full relaxations everywhere in the box | measured | scripts/step5_handshake.py --grid | 8394ed0 | Zenodo 14873443 |
| 2026-07-10 | trajectory handshake, rate-level residual (linearizable cells: τ>10Δt, RHS-stable, uncensored) | mesa_80: median 3.6e-3, p90 4.7e-2, ≤5% for 90.3% of 292,959 cells; mesa_151: median 2.8e-3, p90 2.6e-2, ≤5% for 94.4% of 596,607 cells | measured | scripts/step5_handshake.py --trajectories | 8394ed0 | ditto |
| 2026-07-10 | trajectory handshake, net-tolerance agreement vs per-isotope cancellation c | rises monotonically: c≥0.1 → 0.894/0.937, c≥0.5 → 0.923/0.959, c≥0.9 → 0.937/0.970 (mesa_80/151) — net-flux errors amplify as 1/c, exactly the QSE-cancellation structure the kill-test targets | measured | scripts/step5_handshake.py --trajectories | 8394ed0 | ditto |
| 2026-07-10 | departure classification (rate-level failures, 9.7%/5.6% of linearizable cells) | mesa_80: 69.4% DB-reverse pf-provenance class (Step-4 0.05–0.1 dex band), 25.1% subfloor-controller (dominant channel's reactant below the 1e-15 label floor — unresolvable to the emulator), 5.4% weak-tabular interpolation class, 9 cells UNEXPLAINED (He3_Li7_to_n_p_He4_He4, light-sector multibody — footnoted). mesa_151: 63.6% / 12.6% / 23.8%, UNEXPLAINED **NONE** | measured | scripts/step5_handshake.py --trajectories | 8394ed0 | ditto |
| 2026-07-10 | stiffness tracking | agreement rises monotonically with τ/Δt decade: 0.000 → 0.005/0.006 → 0.23/0.36 → 0.63/0.71 → 0.75/0.79 → 0.87/0.89 (mesa_80/151) — departures track the stiffness proxy as required | measured | scripts/step5_handshake.py --trajectories | 8394ed0 | ditto |
| 2026-07-10 | e_nuc flux-route vs bbq eps_nuc column (trajectories) | UNRESOLVED: ratio off by orders with sign scatter — trajectory-file eps_nuc units/normalization/sign convention not yet pinned (training-CSV 1e16 normalization does not obviously apply). OPEN item; invariant-#5 proper (flux-route vs composition-route, both engine-internal) is a Step-6 quantity | measured (open) | scripts/step5_handshake.py --trajectories | 8394ed0 | ditto |
| 2026-07-10 | screening confirmation | removing chugunov_2007 drops trajectory net agreement 0.76 → 0.53 (single-trajectory probe) — labels definitively carry screening; exact-vs-filename-rounded (T,ρ) changes agreement by <0.3% | measured | inline diagnostics | 8394ed0 | ditto |

## Independent QSE/NSE solver + equilibrium diagnostics (2026-07-10, Step 5 Task 3)

Solver: src/gnn_nucleo/qse/ (Saha coefficients from the same pynucastro
nuclear inputs — Rauscher pf, nucbind, A_nuc, spin states; independent
log-space damped Newton + bisection fallback). Cross-check states: the
canonical 27-state grid (T9 ∈ {5, 6.3, 7.9} × ρ × Yₑ, crosscheck/grids.py),
reference = pynucastro NSENetwork.get_comp_nse(use_coulomb_corr=False).
Script: scripts/step5_qse.py.

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-10 | NSE cross-check vs pynucastro, 27-state grid | max \|Δlog10 X\| over X > 1e-10: **2.7e-10** (mesa_80) / **1.5e-10** (mesa_151), gate 1e-6; 27/27 states, all Newton (no fallback needed); pyna unconverged: 0 | measured | scripts/step5_qse.py | 30373cc | pynucastro 2.12.0 |
| 2026-07-10 | coefficient identity | C(ᴬZ) mass fractions at fixed (μ_p, μ_n) match pynucastro _nucleon_fraction_nse to ≤ 1e-12 rel (tests/test_qse_coeffs.py); QSE solve degenerates to NSE when the group-mass constraint equals the NSE value (u_group < 1e-6 MeV) | measured | tests | 30373cc | pynucastro 2.12.0 |
| 2026-07-10 | TRAJECTORY DATA ANOMALY (blocking for late-row use) | shipped constant-(T,ρ) test trajectories STALL: composition frozen (max \|ΔX\| < 1e-10 per interval) from median age 2.2e5 s / 3.9e4 s (mesa_80/151, T9 ≥ 3.5 files) while eps_nuc keeps RISING; frozen states are NOT NSE (e.g. T9 = 6.1, ρ = 1.8e8, Yₑ = 0.467: si30-dominated X = 0.58, vs NSE fe56 = 0.69 — our engine AND the labels' own early rows agree matter must keep evolving, 99.0% ≤ 5% rate-level agreement at the filename T9 on early rows, sharp scan peak at T9 = 6.1). Hypothesis: bbq implicit stepping stalls once output dt (grows to ~1e10 s) ≫ physical timescales. Consequence: Step 6 may use PRE-STALL rows only; proper relaxed trajectories need bbq reruns (feeds the CPU-allocation request) | measured | scripts/step5_qse.py + inline scans | 30373cc | Zenodo 14873443 |
| 2026-07-10 | r_QSE single-Si-cluster plateau | NOT confirmed on the shipped trajectories: intra-group std(r_QSE) median 1.33 / 1.45 dex (mesa_80/151; plateau criterion < 0.1: 0/129 and 0/130 pre-stall rows) vs non-group spread 3.5 / 2.4 dex — group-organized but not single-cluster-equilibrated; states descend from RANDOM nucleon-loaded compositions and the stall truncates relaxation. Plateau confirmation deferred to physical trajectories (bbq rerun) | measured | scripts/step5_qse.py | 30373cc | ditto |
| 2026-07-10 | κ_r ↔ δ_r consistency | anchor: at exact NSE (δ_r ≡ 0) measured unscreened κ median 2.6e-12 (RESULTS 2026-07-10 WP2 row) — κ → small exactly where δ → 0. Graded: Spearman(log κ_r unscreened, log δ_r) = +0.39 / +0.21 (p ≈ 0; 18k/44k row × carrying-strong-pair samples) on pre-stall trajectory rows; NO cells with δ_r < 0.01 exist there (nothing NSE-equilibrated on these anomalous trajectories — consistent) | measured | scripts/step5_qse.py | 30373cc | ditto |
| 2026-07-10 | QSE group rule (operational) | default 24 ≤ A < 45 (H&T single Si cluster): 29 / 50 members (mesa_80/151); sensitivity variant A ≥ 28: 40 / 105; u_group on pre-stall rows median +4.3 / +4.1 MeV (strongly non-NSE, as expected mid-burn) | measured | scripts/step5_qse.py | 30373cc | ditto |

## Decomposition + preliminary bridge discovery (2026-07-10, Step 5 Task 4)

Subsample = 30k stratified states/net (label screening config; κ from the
unscreened twin run); trajectory rows = PRE-STALL rows of the 20 selected
constant-(T,ρ) trajectories. All PRELIMINARY (Step 6 finalizes).
Script: scripts/step5_bridges.py.

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-10 | κ_r on the TRAINING DISTRIBUTION (random Sobol compositions, carrying strong pairs, unscreened) | median ≈ 1.0 in EVERY T9 stratum; frac κ > 0.1 = 0.985–0.999 (mesa_80) / 0.974–0.997 (mesa_151); frac κ < 1e-3 = 0.000 — training-grid states are nowhere near flux balance (free-nucleon-loaded random compositions): fluxes are essentially one-directional, the Target-A active set {κ > 0.1} covers ~everything THERE; the QSE cancellation structure lives on RELAXED states (trajectories), not the training distribution | measured | scripts/step5_bridges.py | d1a9c4a | Zenodo 14873443 |
| 2026-07-10 | per-isotope cancellation cᵢ on the training distribution | median 0.87–1.0 across strata (both nets), frac cᵢ < 1e-2 ≤ 0.005 — same picture: little cancellation on random states | measured | scripts/step5_bridges.py | d1a9c4a | ditto |
| 2026-07-10 | \|dẎₑ\| per-reaction concentration (training distribution) | top-20 weak channels carry 92.9–99.9% of Σ\|dẎₑ\| in every stratum (both nets); top-5 ≈ 0.58–0.60 (mesa_80); #1 = Ne18→F18 EC (proton-rich fast EC on random comps; p→n above T9 6.3) — strong concentration, feeds loss weighting | measured | scripts/step5_bridges.py | d1a9c4a | ditto |
| 2026-07-10 | mesa_151 ⁴⁵Sc(p,γ)⁴⁶Ti literature cross-check | CONFIRMED on relaxed states: rank **2/251** inter-group carriers (share 0.094) on pre-stall trajectory rows at Yₑ ≥ 0.483, T9 ∈ [3.3, 5.0) under the a24_46 group (boundary at A = 46; the default 24 ≤ A < 45 places ⁴⁵Sc outside the group — boundary placement matters and is now a config variant); its feeder Ca44(p,γ)Sc45 is #4 under the default boundary. On the RANDOM subsample it ranks only 31/251 — the bottleneck is a relaxed-flow feature, invisible on the training distribution | measured | scripts/step5_bridges.py --trajectories | d1a9c4a | ditto |
| 2026-07-10 | mesa_80 empirical bridge set (no ⁴⁵Sc) | relaxed high-Yₑ QSE-window rows: Ne22(α,n)Mg25 (0.18), Al27(p,α)Mg24 (0.12), P31(p,α)Si28 (0.10), Na23(α,p)Mg26, Mg26(p,γ)Al27 — top-20 carry 0.86; on the random subsample the boundary flow is instead (n,α)-dominated (Al26(n,α)Na23 0.34, S31(n,α)Si28, Si27(n,α)Mg24 — free-neutron artifact of random comps) | measured | scripts/step5_bridges.py --trajectories | d1a9c4a | ditto |
| 2026-07-10 | inter-group concentration (top-k) | relaxed high-Yₑ rows: top-10 ≈ 0.66–0.67, top-20 ≈ 0.82–0.86 (both nets, both group variants) — Si-group boundary flow is concentrated in ≲20 channels, GOOD for Target A's active-set premise on physical states | measured | scripts/step5_bridges.py --trajectories | d1a9c4a | ditto |

## Step-5 flux-data artifacts (2026-07-10, provenance)

data/fluxes/<net>/<run_id>/chunk_*.h5 (gitignored). Generation:
scripts/step5_run_fluxes.py at commit 75b32b7 (engine 20f1bb2), screening
chugunov_2007 unless noted; ids from configs/step5_subsample_<net>_ids.json
(sha256 4b87368b…/6a492ec6…); chunk = 16,384 states; f⁺/ydot/dYe_weak stored,
f⁻/φ/κ derived on read. sha256 over sorted chunk files:

| run | mesa_80 | mesa_151 |
| --- | --- | --- |
| subsample (30,000 states) | 2 chunks, 76c9485e4ee16ce8… | 2 chunks, 3a511290c5e28f21… |
| subsample-unscreened | 2 chunks, 145029819880cb48… | 2 chunks, 5de65620f9a5a221… |
| trajectories (20 × 1002 rows) | 20 chunks, c438c19f09b10f98… | 20 chunks, 46f6592b62f02f0d… |
| full corpus (1,041,400 states) | 64 chunks, 1892e1e3b87c2491… (4.9 GB) | 64 chunks, 56effd5b6eabc1db… (12 GB) |

## Trajectory-file eps_nuc convention pin (2026-07-11, Step 6 Task 0)

Retires the 2026-07-10 OPEN row "e_nuc flux-route vs bbq eps_nuc column".
Per pre-stall output interval (state k−1 → k over the row's own dt), the
file column is compared against the engine-independent composition route
E_comp = −N_A Σᵢ mᵢ[MeV] ΔYᵢ · MeV2erg (label ΔX × pynucastro atomic
masses; exact, quadrature-free) and the flux route (trapezoid of ΣQⱼRⱼ on
rate-stable intervals), under candidates {integrated, rate} × {×1, ×1e-16}
× {gross, net-of-neutrinos}. Script: scripts/step6_eps_pin.py.

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-11 | trajectory eps_nuc convention | **INTEGRATED over the row's own dt [erg/g], NET of neutrino losses, NO 1e16 normalization**: vs (E_comp − ∫eps_neu dt) median log10\|ratio\| −0.000 with IQR [−0.000, +0.000], sign agreement 0.9933 / 0.9981 (mesa_80/151; 15,746 / 13,506 pre-stall intervals, dt spanning 1e-10…9.5e9 s), slope of median log-ratio vs dt decade 0.000; the RATE reading shows the wrong-convention slope +1.00 and median offset −2.2/−1.3 dex. Net-of-ν beats gross decisively (sign agreement 0.91/0.81 gross). Matches the source read (sourced: bbq src/lib_bbq.f90:453, out%eps_nuc = avg_eps_nuc·in%time; eps_neu written as a rate). Consequence: eps_neu column is a RATE [erg/g/s]; Step-5's rate-vs-column comparison was a convention mismatch, not an engine error | measured | scripts/step6_eps_pin.py | efaffd4 | Zenodo 14873443 |
| 2026-07-11 | engine cross-check on the pin | flux-route ∫ΣQⱼRⱼdt / E_comp on rate-stable pre-stall intervals: median 0.979 / 0.996 (mesa_80/151) — engine energies consistent with label composition changes at the few-% level (heavy tails on near-cancelling intervals where E_comp → 0, as expected); invariant-#5 proper (≤1% gate) is measured by the Step-6 integrator | measured | scripts/step6_eps_pin.py | efaffd4 | ditto |

## HIGH-T9 TRAINING-LABEL PATHOLOGY: labels carry the Appendix-B bug (2026-07-11, Step 6)

Discovered while validating the reference integrator against shipped labels.
Every measured number: scripts/step6_label_nse_census.py (witness bbq runs
under data/bbq_reruns/diag_state{80,646}_{stock,24081}/). SUPERSEDES the
Step-4 working premise "training labels used the authors' FIXED MESA"
(RESULTS 2026-07-09 verdict row; docs/phase0-checklist.md Appendix-B row) at
the fixed-point level for T9 ≳ 5: the premise may still hold for the paper's
own light-sector channel list, but the chapter-8 1→3 reverses this project
found "beyond the paper" (c12→3α low by 9.5–11.3 dex in stock; RESULTS
2026-07-09) control light↔heavy equilibration and are demonstrably
label-active.

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-11 | label(dt=1e2) vs independent Saha NSE, T9 > 5 subsample (120 states/bin) | max \|Δlog10 X\| over X > 1e-6 species: median rises 6.9 → 11.5 dex (mesa_80) and 6.7 → 13.0 dex (mesa_151) across T9 bins [5.0,5.5)…[7.0,7.94); frac > 1 dex = **1.000 in every bin, both nets** — NO sampled high-T9 label endpoint is near NSE | measured | scripts/step6_label_nse_census.py | 3479512 | Zenodo 14873443 |
| 2026-07-11 | displaced-attractor classes | high ρ: si30/si29/mg26-dominated (e.g. state 80: T9 7.08, ρ 3.0e8 — si30 X = 0.578 vs NSE fe56 = 0.72); low ρ: c12/o16-dominated (state 646: T9 7.78, ρ 2.0e7 — c12 0.294 + o16 0.266 vs NSE he4/fe-group). Same class as the Step-5 trajectory-stall frozen states (si30-dominated at T9 6.1) | measured | scripts/step6_label_nse_census.py | 3479512 | ditto |
| 2026-07-11 | dt-freeze signature | state 80 final composition FROZEN across dt = 1e-5 … 1e1 (si30 5.615e-1 identical to 4 digits; reached already at dt 1e-6) — the attractor is a fixed point of the label generator, not a slow transient | measured | scripts/step6_label_nse_census.py | 3479512 | ditto |
| 2026-07-11 | **attribution witness** (exact label conditions, initial comps) | stock r23.05.1 bbq reproduces the shipped labels to **0.01 / 0.03 dex** (states 80 / 646) including the displaced attractor; MESA **24.08.1** bbq (gh-575 fix verified) instead relaxes toward NSE (state 80: fe56 0.985, 1.2 dex residual with Yₑ still evolving; state 646: he4 0.521 + fe56 0.378). Independent pf-true reference integrator agrees with 24.08.1/NSE (state 80 @ 1e-6 s: fe56 0.70 vs 24.08.1's 0.66) | measured | scripts/step6_label_nse_census.py | 3479512 | MESA r23.05.1 stock + 24.08.1 + pyna 2.12.0 |
| 2026-07-11 | Yₑ consequence | at state 80 the label/stock path evolves Yₑ 0.4717 → 0.4713 over 1e2 s while the fixed-MESA path gives 0.4717 → 0.4619 — the bug displaces WHICH species host EC, so **the labels' Yₑ evolution itself is wrong at T9 ≳ 5**, not just the composition detail | measured | scripts/step6_label_nse_census.py | 3479512 | ditto |
| 2026-07-11 | consequences recorded | (a) rerun-campaign comparability VALIDATED (stock = label behavior to 0.01 dex — ADR 0005's choice measured-correct); (b) Step-5 trajectory-stall anomaly reinterpreted: frozen states are the bug's displaced pseudo-equilibria (the output-dt-blowup hypothesis is at most secondary); (c) validate_campaign's terminal-NSE check must expect the DISPLACED equilibrium on stock reruns at T9 ≳ 5 (24.08.1 witness = the physics-true reference); (d) Phase-1 supervision at T9 ≳ 5 faces a benchmark-vs-physics fork — escalated to the user in STEP6_REPORT (human decision); (e) NNN itself was trained on these labels — external-communication decision also escalated | measured | scripts/step6_label_nse_census.py | 3479512 | ditto |

## Kill-test Task 2A: training-grid distribution at full corpus scale (2026-07-11, Step 6)

Instrument: src/gnn_nucleo/killtest/ + scripts/run_killtest.py
--training-grid. κ convention: UNSCREENED (thresholds) from the 30k
stratified subsample twin; corpus-scale confirmation from the screened
full run (κ ≈ 1 dwarfs the 7e-2 offset there). cond = rank-revealing
(nonzero singular values, graph/metrics definition — the conservation
left-null vectors of ν are structural).

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-11 | κ on the training grid, corpus scale (1,034,704 in-strata states/net) | vacuous-pass picture CONFIRMED at full scale: med log10 κ ≈ −0.05 in EVERY stratum, frac κ>0.1 = 0.985–0.999 (mesa_80) / 0.974–0.997 (mesa_151), frac κ<1e-3 = 0.000; per-state κ-active fraction median 0.987–1.000 (subsample, unscreened). Matches the Step-5 subsample numbers exactly — the training distribution has no cancellation structure anywhere | measured | scripts/run_killtest.py --training-grid | 590dfcd | Zenodo 14873443 + data/fluxes full runs |
| 2026-07-11 | cond(S_active) on the training grid | union κ-active net columns = ALL net columns (327/327, 846/846) in every stratum ⇒ S_active ≈ full ν: cond 41.8 / 57.4 (mesa_80/151; full-ν 41.6 / 57.9) — ≪ the 1e6 gate, trivially PASS but vacuous (nothing equilibrated on this distribution; the verdict quantity is the relaxed-manifold cond) | measured | scripts/run_killtest.py --training-grid | 590dfcd | ditto |

## Stall-guard refinement: the shipped "stall" is attractor arrival, not trajectory death (2026-07-11, Step 6)

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-11 | first-quiet vs terminal-tail stall semantics on ALL shipped trajectories | rules differ on **459/1508** files (both nets): after the first-quiet row (arrival at the bug-displaced strong-equilibrium attractor, RESULTS 2026-07-11 pathology rows) composition RESUMES super-tolerance changes at late giant output dts — slow weak-sector drift (eps_nuc rising), i.e. the Step-5 "stall while eps_nuc rises" anomaly is now fully mechanistic: strong sector frozen at the displaced attractor + continuing weak evolution. Tail rows are legitimate relaxed label-dynamics states (equilibrated strong pairs + active weak columns) and belong IN the kill-test manifold. Guard default switched to terminal-tail; Step-5 selections reproducible via mode="first_quiet" (tests) | measured | tests/test_trajectories.py + inline census (stall-rule regression, commit ea970b4) | ea970b4 | Zenodo 14873443 |
| 2026-07-11 | rerun cold-start guard fix | canonical Si mixes at T9 2.5 produce exactly-zero early-interval changes (nothing burnable in 1e-8-s steps) — first-quiet truncated whole runs at row 0; terminal rule keeps them (they evolve at the wall, eps rate 1e6–1e7 erg/g/s) | measured | scripts/bbq_campaign/validate_campaign.py preview | ea970b4 | local bbq campaign |

## bbq rerun campaign: execution, validation, ingestion (2026-07-11, Step 6 Task 1)

Campaign per ADR 0005: hydrostatic mode, times_from_file (40 pts/decade
from 1e-8 s, dt cap 1e5 s), stock r23.05.1 + bbq, chugunov screening +
weaklib defaults; 209 runs/net (20 shipped-initial + 63 canonical + 126
sobol; state_ids in the manifest). Scripts: scripts/bbq_campaign/*,
scripts/step6_ingest_reruns.py. Raw outputs data/bbq_reruns/ (gitignored;
campaign.yaml sha256 eb118de5af1ae4c1… / e042f9c2eec5886b… mesa_80/151).

| date | quantity | value | tag | script | code version | data version |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-11 | campaign execution | **418/418 runs OK, zero failures** (10-run pilot + 408), 19,486 s wall on 10 workers ≈ 54 core-h; mesa_80 ≈ 2–3 min/run, mesa_151 ≈ 4–6 min at high T9, low-T9 walls (1e8 s, ~2600 rows) up to ~1 h/run; 1.1 GB text output | measured | scripts/bbq_campaign/run_campaign.py | da3cf42 | MESA r23.05.1 stock + bbq |
| 2026-07-11 | stall signature in reruns | terminal-guard census: frozen-before-wall 38/209 (mesa_80) / 56/209 (mesa_151), median frozen-run T9 = 7.9 — fast arrival at the (displaced) terminal attractor, LEGITIMATE; frozen at T9 < 3.3: 9 / 7 runs = exactly the canonical-family inert-fuel cells at 1.6 GK (si28/si30/ne22 mixes cannot burn there; NSE distance meaningless at that T). The shipped-class mid-burn output-dt artifact is ABSENT: every non-inert run either evolves at its stated wall or terminates at the attractor | measured | scripts/bbq_campaign/validate_campaign.py | ea970b4 | local campaign eb118de5/e042f9c2 |
| 2026-07-11 | terminal T9≥5 states vs true NSE | median 8.6 / 9.0 dex (mesa_80/151), frac ≤ 0.05 dex = 0.000 — the DISPLACED pseudo-equilibrium, as the label-pathology rows predict for stock; the 24.08.1 witness runs (RESULTS 2026-07-11 attribution row) are the physics-true anchor | measured | scripts/bbq_campaign/validate_campaign.py | ea970b4 | ditto |
| 2026-07-11 | early-time comparability vs shipped (family-1, identical logT/logRho/X₀) | per-pair species-age agreement within max(5%, 1e-8): median 0.9963 / 0.9977, min 0.9508 / 0.9449 (20 pairs/net); worst |ΔX| median 2.3e-3 / 1.5e-3 — reruns are label-grade comparable (same code, same config; residuals = cadence/solver-path differences) | measured | scripts/bbq_campaign/validate_campaign.py | ea970b4 | ditto |
| 2026-07-11 | r_QSE single-cluster plateau on CLEAN relaxed rows | NOT confirmed: intra-group std(r_QSE) median 0.87 / 0.80 dex, plateau (<0.1 dex) rows 0/303 and 0/316 (QSE window, late pre-stall) vs non-group spread 2.19 / 1.29 dex — group-organized but never single-cluster-equilibrated; retires the Step-5 deferral with a NEGATIVE verdict: the H&T single-Si-cluster reference does not describe the (bugged) relaxed label manifold | measured | scripts/bbq_campaign/validate_campaign.py | ea970b4 | ditto |
| 2026-07-11 | ingestion | 171,904 rows/net through the flux engine into FluxStore rerun-trajectories (chugunov) + rerun-trajectories-unscreened; sha256 1043ba8253b7088e… / 956f424adb65d4af… (mesa_80), b660e835a6763553… / d22b57f6b9559256… (mesa_151); shipped-trajectory unscreened twins 9894a16283b19715… / fdaf251e5cd373e7… | measured | scripts/step6_ingest_reruns.py | 9ea0897 | ditto |
