# STEP 2 REPORT — Zenodo package, inventory, NNN baseline reproduction (2026-07-08)

## 1. Download / extraction

- `NuclearNeuralNetworks.zip` (49.06 GB) downloaded via `scripts/download_zenodo.py`,
  now resumable (HTTP Range into `.part`, retry/backoff, post-completion full-file md5).
  Resume verified by killing the transfer at 0.69 GB and re-invoking. md5
  `ab31e56950e696aba7747f2cfca2d403` — matches manifest. `README.txt` also verified.
- **Disk premise correction:** the task assumed ~168 GB free; the filesystem has
  **5.5 TB (5.64 TB free at start)**. Extraction decision collapsed to "extract everything".
- Extracted to `data/zenodo/NuclearNeuralNetworks/`: 115.15 GB, 3605 files + 195 dirs —
  exact match with `unzip -l`. Zip deleted after verification; MANIFEST updated
  (`status: extracted`, `zip_deleted: true`, md5 kept). 5.52 TB free at end.

## 2. Inventory highlights (full detail: `docs/zenodo-inventory.md`)

- training_sets: 9 dt × 2 nets single-step CSVs, **1,041,400 rows each** (2²⁰ Sobol grid
  minus 0.68%); columns `Age, logT, logRho, initial_*, final_*, eps_nuc, eps_nu`.
- test_datasets: constant-(T,ρ) bbq trajectories (1001 log-spaced ages to ~200 s),
  **684 (mesa_80) / 824 (mesa_151) files, each with a matching approx21 run** —
  the approx21 comparison is shipped, nothing blocked.
- trained_NNN_models: 9 production Lightning-2.4.0 checkpoints per net (+ a layer scan
  L∈{3–20} at dt=0.1 s). Architectures verified from state_dicts: 82→1024→2048×10→82
  (12 layers) / 153→1024→2048×7→153 (9 layers), float32, natural-log log-softmax head.
- **No flux/per-reaction data anywhere; no stellar-trajectory training data** — README and
  paper both say the full 4 TB bbq output is available on request. → 4 TB request justified.
- Schema deltas (recorded, `schema.py` untouched): (1) real dt values deviate from nominal
  10^k by up to ~5% and differ per network (mesa_80 "1e2" = 105.08 s vs mesa_151 102.93 s) —
  `DT_GRID_SECONDS` + rel_tol 1e-12 validation rejects all real data; (2) no `sobol_id`
  column — row identity must be joined on (logT, logRho), verified unique across all 2²⁰
  points; (3) `e_nuc` is integrated [erg/g] (÷1e16 in CSVs), not [erg/g/s] as the schema
  docstring says; ε_ν is a rate (÷1e16; a code comment hints dt≥10 s files may use 1e13 —
  verify before using those labels); (4) `final_*` floored at 1e-15; models are float32.
- Bonus finding: the paper's Appendix A isotope table omits **ca41** from both networks
  (data is authoritative: exactly 80/151).

## 3. Reproduction results (details + provenance: RESULTS.md; scripts: `repro/nnn/`)

Their trained models + their test sets + their (minimally patched) evaluation:

| metric | published | reproduced | ratio | verdict |
| --- | --- | --- | --- | --- |
| per-dt loss CSVs (6 metrics × 18 runs) | shipped Fig-4 CSVs | identical | 1.000 (all 108) | PASS |
| Yₑ improvement, mesa_80 | 390–660 % | 377–651 % | ≈1 | PASS |
| Yₑ improvement, mesa_151 | 280–400 % | 277–390 % | ≈1 | PASS |
| Ā improvement, m80 / m151 | 150–290 / 260–360 % | 149–291 / 256–357 % | ≈1 | PASS |
| e_nuc improvement, m80 / m151 | 250–450 / 280–750 % | 249–419 / 284–772 % | ≈1 | PASS |
| ν-loss crossover | worse for dt ≳ 0.1 s | better ≤0.1 s, worse {1,10,100} s | sign ✓ | PASS |
| NNN ΔYₑ/Yₑ | 0.4–0.75 % | 0.33–0.54 / 0.55–0.73 % | ≈1 | PASS |
| per-isotope ΔX band | most in 1e-4–1e-1 | 90 % / 80 % in band, rest below | — | PASS |

- **Model handshake (Step-6 dependency): PASS at 0.0** — an independent state_dict-walk
  loader (no upstream classes) reproduces their pipeline outputs bit-exactly on 128 real
  test inputs (gate was ≤1e-6). `repro/nnn/check_handshake.py`.
- Improvement ratios use the shipped approx21-vs-large loss files; the approx21 bbq runs
  are also shipped, so a fully independent recomputation remains possible (not needed for
  the ≤2× gate — everything already matches exactly).

## 4. Environment pins & patches

- `repro/nnn/` isolated uv project (root lockfile untouched): python 3.12,
  **torch 2.4.1+cpu, pytorch-lightning 2.4.0** (checkpoint version), pandas 3.0.3,
  numpy 2.5.1. CPU-only: torch 2.4 has no sm_120 (RTX 5070) support; MLP inference
  doesn't need it (full sweep ≈ 7 min).
- The shipped eval **cannot run verbatim**; patches (all in `repro/nnn/patches/`, upstream
  math untouched): env-var paths (Windows/WSL hardcodes), test filename parse (`_Ye_`
  suffix assumed but absent), `c_light` undefined, checkpoint glob caught `desktop.ini`,
  non-`output*` files corrupted prediction/target alignment, memoized a ~150 MB csv
  re-read per test file, dropped an unused multi-GB DataModule load.
- MESA dependency dodged: eval needs `<MESA>/data/chem_data/isotopes.data` (release
  tarball only). Reconstructed the 159-isotope subset from pynucastro AME
  (`repro/nnn/make_isotopes_data.py`); A/Z exact, masses affect only the uncompared Q
  diagnostic.

## 5. Isotope lists & Yₑ controllers (configs/isotopes_mesa{80,151}.yaml; RESULTS.md table)

- Lists sourced from test-set headers (= training CSV column order), cross-checked
  against paper App. A (which omits ca41) and model input dims (82/153).
- **mesa_80 carries only 6/9 EC controllers — ⁵⁵Fe, ⁵¹V, ⁵³Cr missing — and 0/8 β-decay
  partners. ⁵⁶Cr and ⁶³Co are in NEITHER network.** mesa_151 has everything else.
- Also: ⁴⁵Sc is absent from mesa_80, so the ⁴⁵Sc(p,γ)⁴⁶Ti bottleneck instrument
  (CLAUDE.md regime box) applies to mesa_151 only.
- Direct consequences: size-transfer mesa_80→mesa_151 must bridge a much richer weak
  sector, and mesa_80-internal Yₑ dynamics run through a thinner EC set — factor this
  into loss weighting and the transfer falsifier.

## 6. Blocked / skipped / decisions needed

- Nothing blocked in this step. Not done (deliberately): schema.py amendments (deltas
  recorded only — decide field/unit fixes before ingestion code); independent
  recomputation of approx21-vs-large losses; row-order identity between the 9 dt CSVs
  (assumed consistent, join key verified available); the dt≥10 s ε_ν normalization
  question (affects 2 of 18 label columns; check before using ε_ν labels at 10/100 s).
- Handshake script lives in `repro/nnn/` (needs torch), not `scripts/` — root env stays
  torch-free by design; revisit when Step 6 harness lands.

## 7. Manual items (yours)

- **Remote/CI:** remote `origin` exists (raw-asparagus/gnn-nucleosynthesis). CI has
  NEVER run the repo workflow — local master was 9 commits ahead before this session
  (now ~19); the only Actions run is a dependabot graph job. `gh` CLI not installed.
  → push when ready; first push will exercise ci.yml.
- **4 TB data request e-mail** to A. Grichener — now concretely justified: package
  confirmed to contain no flux/per-reaction data and no extended-dt/density sets.
- Still open from Step 1: CPU allocation for bbq training-data generation, GPU fleet
  decision, division-of-labor conversation.
