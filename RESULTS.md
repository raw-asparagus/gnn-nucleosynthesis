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
