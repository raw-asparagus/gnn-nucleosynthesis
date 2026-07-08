"""gnn_nucleo: conservation-by-construction GNN emulator of silicon burning.

Package layout (stubs filled in by later Phase-0 steps):

- ``graph``    — pynucastro network export, stoichiometric/lepton matrices,
                 constraint matrix C, Target B projector (Step 3; the
                 conservation-critical layer — numpy/pyyaml/pynucastro/networkx
                 only, no torch, so the gate hook stays fast)
- ``fluxes``   — gross/net per-reaction flux derivation from bbq output (Step 5)
- ``qse``      — QSE/NSE reference-abundance solver (Step 5)
- ``killtest`` — kill-test harness for the Target A viability gates (Step 6)
- ``data``     — dataset schema, splits, storage conventions (Step 1)

The former top-level ``conservation`` stub package was superseded by
``gnn_nucleo.graph`` in Step 3 (ADR 0002).
"""
