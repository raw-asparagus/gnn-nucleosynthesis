# Phase-0 notebook series

One notebook per node of the Phase-0 pipeline flowchart (see `00-phase0-map`),
detailing and visualizing what each pipeline did and where its measured numbers
live. Notebooks are **exploratory** (root CLAUDE.md): they re-plot artifacts and
quick-look subsets; every citable number lives in `RESULTS.md`, produced by
`scripts/`. Every figure carries a caption citing its RESULTS.md rows.

| # | Notebook | Pipeline node |
|---|----------|---------------|
| 00 | `00-phase0-map.ipynb` | The flowchart itself, with live status from `docs/phase0-checklist.md` |
| 01 | `01-data-inventory.ipynb` | Zenodo corpus, isotope lists, Yₑ-controller membership |
| 02 | `02-nnn-baseline.ipynb` | NNN baseline reproduction (`repro/nnn/`) |
| 03 | `03-graph-conservation.ipynb` | ν export, conservation gate, projector, graph metrics |
| 04 | `04-rates-crosscheck.ipynb` | MESA↔pynucastro reconciliation, Appendix-B, κ-floor screen |
| 05 | `05-flux-engine.ipynb` | Flux engine + corpus store; training-grid κ |
| 06 | `06-qse-bridges.ipynb` | Si-group structure + inter-group bridges (both boundary variants) |
| 07 | `07-trajectories.ipynb` | Trajectory ingestion: eps_nuc pin, stall semantics |
| 08 | `08-rerun-campaign.ipynb` | bbq rerun campaign coverage + shipped-vs-rerun agreement |
| 09 | `09-label-pathology.ipynb` | The headline finding: bug-displaced labels at T9 ≳ 5 |
| 10 | `10-killtest-verdict.ipynb` | Kill-test distributions + verdict dashboard |
| 11 | `11-integrator-and-handoff.ipynb` | Reference Φ integrator (🟡) + Step-7/Phase-1 open items |

## Running

```bash
uv sync                                  # dev group has jupyterlab/ipykernel
uv run jupyter lab notebooks/phase0      # interactive
NB_QUICK=1 uv run jupyter execute notebooks/phase0/03-graph-conservation.ipynb  # headless
```

Environment flags:

- `NB_QUICK` (default **1**): notebooks load capped subsets (single FluxStore
  chunks, few trajectories, few NSE solves) and stamp affected figures with a
  QUICK-LOOK banner. `NB_QUICK=0` runs full depth — notebooks 05/09/10 then
  take minutes to tens of minutes.
- `NB_RUN_INTEGRATE` (default **0**): notebook 11's integration cells compile
  the pynucastro network (minutes) only when set to 1.
- `NB_FORCE_NO_REPRO=1`: makes notebook 02 exercise its missing-results path
  (`repro/nnn/results/` is gitignored; regenerate via `repro/nnn/run_all.sh`).

## Conventions (enforced by `nbsupport.py`)

- Provenance header cell in every notebook: node status parsed live from
  `docs/phase0-checklist.md`, commit hash, RESULTS.md rows visualized.
- `nbs.caption(...)` refuses figures that cite no RESULTS.md row.
- Two-κ rule is structural: κ helpers require a declared UNSCREENED/SCREENED
  convention matching the FluxStore run, and refuse mixing.
- Group/bridge figures show BOTH Si-group boundary variants (default, a24_46).
- Trajectory row selection states its rule (`select_rows(prestall=True,
  mode="terminal")` defaults).

## Committing

Outputs are never committed. Run once per clone:

```bash
uv run nbstripout --install    # activates the .gitattributes filter locally
```
