# 0002 — gnn_nucleo.graph is the canonical home of ν, C, and the projector
Date: 2026-07-08    Status: accepted

## Decision
The fixed conservation layer — isotope tables, pynucastro rate-collection
build, stoichiometric matrix ν with the (e⁻, ν, ν̄) lepton ledgers, constraint
matrix C, bipartite graph export, and the Target B null-space projector —
lives in `src/gnn_nucleo/graph/` as the single source of truth. The
pre-Step-3 `src/conservation/` package (an empty docstring stub; the actual
prototype logic sat in `scripts/export_stoich_matrix.py`,
`scripts/check_conservation.py`, and inline in `tests/test_conservation.py`)
is superseded and deleted. Scripts are thin CLIs over the package. The gate
hook, wheel packaging, and repo maps were updated in the same commit
(1cde6a5). The package stays torch-free (numpy / pyyaml / pynucastro /
networkx) so the PostToolUse conservation gate stays fast.

Ported from the prototype: the npz schema (kept as a superset for
compatibility), fail-loud per-column validation, drift metrics. Fixed in the
port: lepton ledgers are assigned from pynucastro `weak_type`, not
back-derived from Z·ν (the prototype's `d_electron = Z @ nu[:, j]` made the
charge-to-lepton closure test a tautology); the string-matching weak
classifier is gone; ReacLib-vs-tabular duplicate links are resolved
explicitly (tabular wins).

## Basis
- derived: `src/conservation/` contained no code to promote (session audit,
  STEP3_REPORT.md §3); the graph builder needs pynucastro, so a "numpy-only
  conservation package" separate from the builder would split ν's source of
  truth in two.
- measured: both networks build and pass the blocking gate — column drifts
  exactly 0.0, dYₑ nonzero through weak columns (RESULTS.md 2026-07-08).
- assumed → flagged, not silent: the pynucastro reaction set (610 / 1522
  reactions; tabular ordering ffn<oda<pruet_fuller<langanke<suzuki) equals
  MESA r23.05.1's softwired set closely enough for architecture sizing. Every
  artifact carries `provisional_reaction_set=True`; the tabular ordering is
  an exposed parameter.

## Switch condition
If the Step-4 bbq/MESA cross-check shows a reaction-set mismatch that is
material to κ_r distributions or kill-test conclusions (not merely to counts),
rebuild the collection from MESA's net definition files (and weaklib
precedence LMP > Oda > FFN) inside the same package, bump the artifact
metadata, and re-run the gate + graph metrics. The package location and API
do not reverse; only the rate source does.
