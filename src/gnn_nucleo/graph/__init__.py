"""Network graph export and the fixed conservation layer (Step 3).

Canonical home of the pynucastro export of mesa_80 / mesa_151: species tables
(A, Z), reaction lists, the stoichiometric matrix ν with the electron/
neutrino/antineutrino ledgers, the constraint matrix C, and the Target B
null-space projector. Supersedes the pre-Step-3 ``src/conservation`` stub
(decision recorded in STEP3_REPORT.md / ADR 0002).

Conservation-critical: edits here trigger the PostToolUse gate hook. Keep it
free of ML dependencies (numpy / pyyaml / pynucastro / networkx only) so the
gate stays fast. float64 everywhere; the conservation map is a FIXED linear
operator applied in decode — no nonlinear transform may sit between it and
the output (root CLAUDE.md invariant #4).

Contract: the exported ν must pass tests/test_conservation.py (baryon
conservation column-wise, charge-to-lepton closure on weak columns, nonzero
weak dYₑ) before anything downstream may use it.
"""

from .export import (
    bipartite_digraph,
    build_and_export,
    content_hash,
    export_graphml,
    export_npz,
    graphml_path,
    npz_path,
    sha256_of,
)
from .isotopes import IsotopeTable, canonical_network, load_isotope_table
from .network import DEFAULT_TABULAR_ORDERING, BuildInfo, build_rate_collection
from .projector import build_projector, project
from .stoich import (
    N_LEPTON_ROWS,
    WEAK_LEDGERS,
    Stoich,
    build_stoich,
    constraint_matrix,
)

__all__ = [
    "IsotopeTable",
    "Stoich",
    "BuildInfo",
    "DEFAULT_TABULAR_ORDERING",
    "N_LEPTON_ROWS",
    "WEAK_LEDGERS",
    "bipartite_digraph",
    "build_and_export",
    "build_projector",
    "build_rate_collection",
    "build_stoich",
    "canonical_network",
    "constraint_matrix",
    "content_hash",
    "export_graphml",
    "export_npz",
    "graphml_path",
    "load_isotope_table",
    "npz_path",
    "project",
    "sha256_of",
]
