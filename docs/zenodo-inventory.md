# Zenodo 14873443 package inventory (Grichener et al. 2025 NNN)

Date: 2026-07-08. Source: `NuclearNeuralNetworks.zip`, md5
`ab31e56950e696aba7747f2cfca2d403` (verified), 49.06 GB compressed →
115.15 GB extracted to `data/zenodo/NuclearNeuralNetworks/` (3605 files +
195 dirs, exact match with the zip listing; zip deleted). All numbers below
are **measured** from the extracted package unless labelled otherwise;
provenance rows in `RESULTS.md`. Google-Drive `desktop.ini` droppings appear
in every directory and are ignored throughout.

## Top level

| component | size | contents |
| --- | --- | --- |
| `MESA_models/` | 0.55 GB | 4 MESA stellar models (parameter-space provenance) |
| `training_sets/` | 83.7 GB | 18 training CSVs (9 dt × 2 networks) + Sobol grid |
| `test_datasets/` | 6.1 GB | bbq test trajectories, large-net + approx21 pairs |
| `trained_NNN_models/` | 23.8 GB | PyTorch Lightning checkpoints (production + layer scan) |
| `python_scripts_for_analysis/` | 1.0 GB | generation/train/eval/figure scripts + shipped result files |

## MESA_models/

MESA r23.05.1 `history.data`/profile text files (version string embedded):
`20M_mesa80/`, `20M_mesa151/` (20 M☉ test-case runs to core collapse, used to
set the training T/ρ box), `40M_CHE_Gottlieb_et_al_2024/`, and
`8.8M_ECSN_Wang_et_al_2024/` (comparison tracks in paper Fig. 1). No inlists,
no MESA source, no bbq runs here.

## training_sets/

- `logT_9.2_to_9.9_logRho_7_to_9_Ye_0.45_to_0.5.txt`: 1,048,576 (=2²⁰) Sobol
  triplets `logT, logRho, Ye` — the training grid.
- `mesa_80/mesa_80_<dt>_sec.csv`, `mesa_151/mesa_151_<dt>_sec.csv` for
  dt ∈ {1e-6 … 1e2}: **1,041,400 data rows each** (7,176 Sobol points, 0.68%,
  absent — presumably failed/filtered bbq runs). ~3 GB (mesa_80) / ~6 GB
  (mesa_151) per file.
- Columns: `Age, logT, logRho, initial_<iso>×N, final_<iso>×N, eps_nuc,
  eps_nu` (N = 80/151, isotope order identical to test-set headers and to
  `configs/isotopes_mesa{80,151}.yaml`). No `Ye`, no sample id.
- `Age` = actual bbq age at the grid point nearest the nominal dt, e.g.
  mesa_80: 1.011e-6, 1.031e-5, 1.051e-4, 1.013e-3, 1.032e-2, 1.051e-1,
  1.013e0, 1.032e1, **1.0508e2** s; mesa_151 differs (e.g. 1.0293e2 s) —
  nominal-vs-actual deviations up to ~5%, and per-network.
- `final_*` mass fractions floored at 1e-15 (their generator clips before
  log-training). `eps_nuc`, `eps_nu` divided by 1e16 (their NormalizeEps.py).
  Per the paper, e_nuc is the *integrated* specific energy [erg/g] while
  ε_ν is a *rate* [erg/g/s]. A commented-out line in their eval warns that for
  dt ≥ 10 s ε_ν may have been normalized by 1e13 instead — verify before using
  those two labels (does not affect composition).

## test_datasets/

- `logT_9.2_to_9.9_logRho_7_to_9_Ye_0.45_to_0.5_for_Test.txt`: 1024 (=2¹⁰)
  Sobol triplets.
- `mesa_80/{mesa_80,approx21}_output_files/`: **684** files each;
  `mesa_151/{mesa_151,approx21}_output_files/`: **824** files each (paper says
  ≈700). Matching filenames = same (T,ρ) initial condition run with the large
  net and with approx21_cr60_plus_co56 — i.e. **the approx21 comparison runs
  ARE shipped**; nothing blocks the improvement-ratio reproduction.
- Format: whitespace text, header `age dt eps_nuc eps_neu <iso...>`, then
  1002 rows: age 0 (initial state) + 1001 bbq steps with dt log-spaced
  (0.02 dex) from 1e-10 s, cumulative age ≈ 1e-8.7 → ~2e2 s. Initial
  compositions restricted to approx21 isotopes (paper §3). Filenames
  `output_T_<logT>_rho_<logRho>.txt` (no Ye field — their own scripts expect
  one more `_Ye_*` component and need a patch to parse these).
- These are constant-(T,ρ) composition *trajectories* — the only
  trajectory-like data in the package.

## trained_NNN_models/

Per network: `different_timesteps/age_<dt>_trainingdata_1e6_l1loss_layers_
<L>_factor_8_<net>/checkpoints/epoch=*.ckpt` — the 9 production models
(L=12 for mesa_80, L=9 for mesa_151), single checkpoint each; plus
`different_layers/` = layer scan L ∈ {3…20} at dt=1e-1 (hyperparameter study,
paper App. C). Checkpoint = PyTorch Lightning 2.4.0 full training state
(state_dict + Adam optimizer state + loops), float32. Verified shapes:
mesa_80: 12 Linear layers 82→1024→2048×10→82; mesa_151: 9 layers
153→1024→2048×7→153; log-softmax (natural log) applied to the first N_iso
outputs in `forward`, last 2 outputs linear. Loading requires their
`nuclearNN` class (or a plain state_dict walk — both verified to work).

## python_scripts_for_analysis/

- `GenerateTrainingSets/`: Sobol grid generator, bbq driver, CSV builder,
  eps normalizer. Reference the full "4 TB" bbq output tree (not shipped).
- `TrainNNNs/NNNfunctionsCompPlusEps.py` (model/data classes; module-level
  CSV read), `NuclearNeuralNetwork.py` (train driver).
- `TestNNNs/runNNNsOnTestMesa80.py`: the evaluation pipeline (only the
  mesa_80 variant shipped; parameterizable for mesa_151). As shipped it does
  NOT run verbatim: hardcoded Windows/WSL paths, filename parsing expects a
  `_Ye_` suffix, `c_light` undefined, checkpoint glob picks up desktop.ini,
  and non-`output*` files corrupt prediction/target alignment. Patched copies
  + diffs: `repro/nnn/patched/`, `repro/nnn/patches/`.
- `CompareLargeAndSmallNets/`: approx21-vs-large-net error pipeline.
- `CreateFigures/Figure4_main_results/{mesa_80,mesa151}_results/<dt>/
  timeStepIndex_<idx>/*.csv`: **their shipped per-dt result files** (NNN and
  approx21 losses, averages/medians) — the exact numbers behind paper
  Figs. 4–5; our reproduction targets. (`OldDatabase*`/`12_layers_worse*`
  variants exist; ignore.)
- MESA dependency: eval reads `<MESA>/data/chem_data/isotopes.data` (not in
  the package, not in the MESA git tree — release tarball only). We
  reconstructed the needed 159-isotope subset from pynucastro AME data
  (`repro/nnn/isotopes_data_reconstructed.data`); affects only the Q
  diagnostic; A, Z, Z/A are exact integers/ratios either way.

## Flux / trajectory data: mostly ABSENT (4 TB request justified)

- **No per-reaction data of any kind** (no fluxes φ, no rates, no reaction
  lists): nothing in the package identifies individual reactions. Target A's
  flux labels cannot be derived from this package — they require the bbq
  re-runs planned in Phase 0/1 (and/or the authors' 4 TB archive).
- Trajectory data: only the constant-(T,ρ) test trajectories above (684+824
  files, 6 GB); training data is strictly single-step (state → state after
  one dt). No stellar-profile-conditioned burning sequences.
- README + paper Data Availability both state the full bbq runs (more
  timesteps, extended density range, 4 TB) are available on request.

## Mapping onto `src/gnn_nucleo/data/schema.py` (deltas ⇒ do not code against the schema until amended)

| schema assumption | package reality | severity |
| --- | --- | --- |
| `dt_seconds == DT_GRID_SECONDS[dt_index]` exactly (rel_tol 1e-12), same grid for both networks | actual ages deviate from nominal 10^k by up to ~5% and differ per network (105.08 s vs 102.93 s for "1e2") | **breaks ingestion** — validation raises on every real row |
| `sobol_id: int` per record | no id column anywhere; row ↔ Sobol-point mapping implicit (same row count across all 9 dts per network suggests consistent ordering — unverified) | **blocks SplitSpec** until row-identity is established (join on (logT,logRho) pair, which is unique per point) |
| `StepLabels.e_nuc` documented [erg/g/s] | e_nuc is integrated [erg/g] (÷1e16 in CSVs); ε_ν is a rate [erg/g/s] (÷1e16, with the dt≥10 s 1e13 caveat above) | docstring/unit fix + un-normalization constant |
| X, X_post full-precision float64 | CSV text full precision, but `final_*` floored at 1e-15, and the models are float32 with a log-softmax head (ΣX=1 enforced in float32) | note for conservation analysis: shipped labels sum to 1 only to ~1e-15 (floor), NNN outputs to float32 |
| single-step records only | test sets are 1001-step trajectories; training sets are single-step | schema fine for training data; test trajectories need their own (future) record type |
| `N_TIMESTEPS = 9`, log-spaced 1e-6…1e2 | confirmed (nominally) | ok |
| `NETWORKS = {mesa_80: 80, mesa_151: 151}` | confirmed (definitive isotope lists in `configs/`) | ok |
| inputs `log_T`, `log_rho`, linear X | confirmed (`logT`, `logRho` columns; linear mass fractions) | ok |

No `schema.py` changes made in Step 2 (per task spec); the deltas above are
the required amendments.
