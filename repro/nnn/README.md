# repro/nnn — Grichener et al. 2025 NNN baseline reproduction (Step 2)

Isolated uv project (own `pyproject.toml`/`uv.lock`; **never** part of the
root env) that reruns the published NNN evaluation with the shipped trained
models on the shipped test sets. Upstream code in `data/zenodo/` stays
pristine; everything we changed is in `patched/` with unified diffs in
`patches/`.

## Environment pins

- python 3.12, `torch==2.4.1+cpu` (pytorch-cpu index), `pytorch-lightning==2.4.0`
  (the version in the shipped checkpoints), pandas 3.0.3, numpy 2.5.1,
  matplotlib. CPU inference only (torch 2.4 has no sm_120 support for the
  local RTX 5070; irrelevant for MLP inference).

## Contents

- `patched/NNNfunctionsCompPlusEps.py` — upstream model/data module;
  paths + isotope count via env vars (`NNN_BASE_DIR`, `NNN_DATABASE_FILE`,
  `NNN_ISOTOPES_NUM`).
- `patched/runNNNsOnTestMesa80.py` — upstream evaluation; env-parameterized
  driver (`NNN_ZENODO_DIR`, `NNN_MESA_DIR`, `NNN_RESULTS_DIR`, `NNN_NET`,
  `NNN_DT`). Fixes required to run at all (shipped script cannot run
  verbatim): filename `logRho` parse without `_Ye_` suffix, `c_light`
  definition, `.ckpt`-only checkpoint glob, `output*`-only file listing
  (desktop.ini would corrupt prediction/target alignment), memoized
  `findIsoParams` (upstream re-reads a ~150 MB csv per test file), dropped
  an unused multi-GB `DataModule` load. Upstream math untouched.
- `patches/*.patch` — `diff -u` of each file against `data/zenodo/` originals.
- `mesa_stub/data/chem_data/isotopes.data` — reconstructed subset of MESA's
  isotope table (regenerate: `uv run python repro/nnn/make_isotopes_data.py`
  from the repo root env). A/Z/N exact; masses pynucastro-AME (Q diagnostic
  only).
- `run_all.sh` — full sweep: 2 networks × 9 dt → `results/<net>/<dt>/`
  (gitignored).
- `compare_published.py` — reproduction table: ours vs the shipped
  per-dt result CSVs (paper Figs. 4–5) + improvement percentages + paper
  range checks. Numbers logged in `RESULTS.md`.
- `check_handshake.py` — independent checkpoint loader (state_dict walk, no
  upstream classes) vs upstream class outputs on 128 real test inputs;
  Step-2 gate: max abs deviation ≤ 1e-6 (measured: 0.0).

## Reproduce

```bash
cd repro/nnn && uv sync
bash run_all.sh                      # ~7 min CPU
uv run python compare_published.py
uv run python check_handshake.py
```
