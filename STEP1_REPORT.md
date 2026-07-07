# STEP 1 REPORT — Phase 0 infrastructure (2026-07-07)

Six commits on `master` (992803c → this one). All work infrastructure-only:
no data downloads (metadata only), no model code, no science derivations.

## 1. What was created

```
CLAUDE.md                     extended: hard gates, physics/eng conventions, regime box
README.md                     project description + layout map (was empty)
RESULTS.md                    append-only measured-numbers log (header only)
STEP1_REPORT.md               this file
pyproject.toml                pinned deps, hatchling build, ruff+pytest config
uv.lock                       full transitive lock
.gitignore                    merged snippet + data/** (except MANIFEST/.gitkeep),
                              MESA/bbq trees, *.h5/hdf5/parquet, checkpoints
.github/workflows/ci.yml      push+PR: uv sync --frozen, ruff check, pytest
configs/                      empty (.gitkeep)
notebooks/README.md           exploratory-only contract
data/MANIFEST.yaml            Zenodo 14873443 file list, status not_downloaded
scripts/download_zenodo.py    manifest refresh + selective download (--file, md5 check)
scripts/install_mesa.sh       MESA r23.05.1 scaffold, check mode only
src/gnn_nucleo/{graph,fluxes,qse,killtest}/   docstring stubs (Steps 3/5/6)
src/gnn_nucleo/data/schema.py StepInputs/StepLabels, DerivedExtension, Provenance,
                              SplitSpec (sobol_id-keyed, leakage-safe), HDF5+Parquet decision
tests/test_imports.py         all stubs import
tests/test_schema.py          dt grid, shape/provenance/split invariants
docs/reports/consolidated-*.md  the four consolidated reports, copied from docs/archive/
```
Pre-existing and untouched: `src/conservation/`, `tests/test_conservation.py`,
`.claude/` agents+hooks, docs living-spec dirs, existing scripts (lint fixes only).
Removed: uv-template `main.py`, merged `.gitignore-snippet.txt`.

## 2. Installed versions (exact, from uv.lock)

Python 3.14.4 (`.python-version` pin kept — no wheel fallback needed) · uv 0.11.21
numpy 2.5.1 · scipy 1.18.0 · h5py 3.16.0 · pyarrow 24.0.0 · pandas 3.0.3 ·
networkx 3.6.1 · matplotlib 3.11.0 · pynucastro 2.12.0 · **torch 2.12.1+cu130** ·
**torch-geometric 2.8.0** (pure-Python wheel, no compiled companions) ·
pyyaml 6.0.3 · pytest 9.1.1 · ruff 0.15.20 · gfortran 15.2.0 (system)

`uv run pytest -q`: **23 passed, 1 skipped** (skip = stoich-export test, pending
Step 3). `uv run ruff check .`: clean.

## 3. Machine

12 cores · 60 GiB RAM (~41 free) · 168 GB disk free on / ·
GPU: **NVIDIA RTX 5070, 12 GB, visible to torch** (`cuda_available=True`, cu130 build).

## 4. Zenodo manifest — RETRIEVED

Record 14873443 API reachable. Two files, total **49.06 GB**
(brief said ~80 GB — actual record is 49 GB; worth double-checking whether the
~80 GB figure referred to the unzipped size or another record):
- `README.txt` (1.6 kB, md5 e560d6df…) — not downloaded (kept session data-free)
- `NuclearNeuralNetworks.zip` (49.057 GB, md5 ab31e569…) — not downloaded
Both `status: not_downloaded` in `data/MANIFEST.yaml`. Selective fetch later:
`uv run python scripts/download_zenodo.py --file README.txt`
(zip additionally needs `--yes-large`).

## 5. Failures / skips / decisions needed

- **No failures.** torch-geometric resolved first try on Python 3.14; the
  planned 3.13/3.12 fallback was unnecessary.
- Pre-existing lint debt fixed in `scripts/` (2 long lines, unused `args` in
  the kill-test skeleton); `tests/test_conservation.py` got a per-file E702
  exemption for its one-reaction-per-line ν-matrix layout.
- CI installs full torch (+CUDA libs, ~1 GB) per cold cache; acceptable now,
  revisit with a CPU-only torch index if CI time hurts. CI is untested until
  the repo is pushed to GitHub (no remote configured yet).
- Layout mismatch (pre-existing, not resolved here — docs are the spec, so
  flagging, not fixing): root CLAUDE.md's LaTeX command targets `tex/main.tex`,
  but the actual LaTeX lives in `docs/{project-scope,gnn-architecture,qse,
  training-data}/main.tex`; `tex/` holds only its CLAUDE.md. Decide: move the
  papers to `tex/` or update the command.
- MESA note: system gfortran 15.2.0 exists but MESA r23.05.1 is only supported
  under the matching MESA SDK; `install_mesa.sh` documents the SDK route and
  disk budget (~17 GB). Nothing downloaded.
- `data/zenodo/` write-protection: `.claude/settings.json` denies Edit/Write
  there; downloads happen only through the script at your command.

## 6. Open manual items (yours)

1. Confirm institutional CPU allocation (bbq regeneration + kill-test grids).
2. Confirm GPU fleet access (local RTX 5070 12 GB is fine for prototyping,
   not for the full training matrix).
3. Email the Grichener et al. corresponding author re: the ~4 TB bbq superset
   (the Zenodo package is the 49 GB curated subset).
4. Open the division-of-labor conversation (advisor/collaborators).
5. Push to GitHub so CI runs; decide on the `tex/` vs `docs/` LaTeX layout.
