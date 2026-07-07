"""gnn_nucleo: conservation-by-construction GNN emulator of silicon burning.

Package layout (stubs filled in by later Phase-0 steps):

- ``graph``    — pynucastro network export, stoichiometric/lepton matrices (Step 3)
- ``fluxes``   — gross/net per-reaction flux derivation from bbq output (Step 5)
- ``qse``      — QSE/NSE reference-abundance solver (Step 5)
- ``killtest`` — kill-test harness for the Target A viability gates (Step 6)
- ``data``     — dataset schema, splits, storage conventions (Step 1)

Conservation-critical linear algebra lives in the separate top-level
``conservation`` package (numpy-only, float64-only) so the gate hook stays
free of ML dependencies.
"""
