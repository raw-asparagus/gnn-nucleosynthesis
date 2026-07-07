# gnn-nucleosynthesis

Conservation-by-construction graph neural network emulator of silicon burning in
MESA's softwired nuclear networks (`mesa_80`, `mesa_151`), benchmarked against the
Grichener et al. 2025 "Nuclear Neural Network" (NNN; ApJS 279, 49) on its public
reproducibility data (Zenodo record 14873443; MESA r23.05.1 + bbq). Closest
competitor: NuGNN (Kim et al. 2026, arXiv:2606.04491).

Primary prediction target ("Target A"): signed net per-reaction flux φ mapped
through the fixed stoichiometric matrix, dY = ν φ, so baryon number and
charge-to-lepton closure hold to machine precision for *any* network output.
Fallback ("Target B"): direct dY in a linear output space with additive
null-space projection.

## Layout

| Path | Contents |
| --- | --- |
| `CLAUDE.md` | Project memory: invariants, hard gates, conventions |
| `RESULTS.md` | Log of every measured number, with provenance |
| `src/gnn_nucleo/` | Package: graph export, fluxes, QSE, kill-test, data schema |
| `src/conservation/` | Conservation-critical (numpy-only) constraint machinery |
| `tests/` | Pytest suite; `test_conservation.py` is the project floor |
| `scripts/` | Reproducible entry points for every derived number |
| `configs/` | Run/experiment configuration files |
| `docs/` | Living spec, consolidated reports, ADRs, novelty reports |
| `data/` | Gitignored local data; only `data/MANIFEST.yaml` is tracked |
| `notebooks/` | Exploratory only; promoted to `src/` when stable |
| `tex/` | LaTeX papers |

## Environment

Managed with **uv only** (never conda/pip):

```bash
uv sync                 # install pinned environment
uv run pytest -q        # full test suite
uv run ruff check .     # lint
```

MESA r23.05.1 and bbq are external Fortran builds driven by
`scripts/install_mesa.sh` (scaffold; see its header before running).
