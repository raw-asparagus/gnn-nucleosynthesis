"""Network graph export (Step 3 — stub).

Will hold the pynucastro export of mesa_80 / mesa_151: species tables (A, Z),
reaction lists, the stoichiometric matrix nu, the weak-reaction mask, and the
electron/neutrino ledger columns consumed by ``conservation``.

Contract: the exported nu must pass tests/test_conservation.py layer 2
(baryon conservation column-wise, charge-to-lepton closure on weak columns)
before anything downstream may use it.
"""
