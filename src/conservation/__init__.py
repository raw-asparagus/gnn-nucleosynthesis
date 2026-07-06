"""Conservation-critical module: constraint matrices, stoichiometric map,
null-space projection, drift diagnostics.

Rules (enforced by tests/test_conservation.py and the PostToolUse hook):
- numpy-only, float64-only.
- The conservation map is a FIXED linear operator applied in the decode step.
- No nonlinear transform downstream of the conservation map, ever.
"""
