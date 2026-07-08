#!/usr/bin/env python3
"""Measured Target B projector residuals for RESULTS.md.

Usage: uv run python scripts/check_projector.py

Per network: max constraint residual |C @ P @ dY| over random dY spanning
20 decades of magnitude (relative bound, see tests/test_projector.py),
idempotence ||P^2 - P||_inf, symmetry, rank, and the weak-dYe preservation
error on a conserving update.
"""

from __future__ import annotations

import numpy as np

from gnn_nucleo.graph import build_and_export, build_projector


def report(network: str) -> None:
    stoich, info, table, npz, gml = build_and_export(network)
    C, nu_ext, Z = stoich.C, stoich.nu_ext, stoich.Z
    P = build_projector(C)
    m = C.shape[1]
    row_norms = np.linalg.norm(C, axis=1)

    worst_rel = 0.0
    for k in range(6):  # scales 1e0 ... 1e-20
        scale = 10.0 ** (-4 * k)
        for seed in range(20):
            rng = np.random.default_rng(seed)
            dY = scale * rng.choice([-1.0, 1.0], m) * 10.0 ** rng.uniform(-3, 0, m)
            residual = np.abs(C @ (P @ dY))
            rel = float((residual / np.maximum(1.0, row_norms * np.linalg.norm(dY))).max())
            worst_rel = max(worst_rel, rel)

    idem = float(np.abs(P @ P - P).max())
    sym = float(np.abs(P - P.T).max())
    rank = int(np.round(np.linalg.eigvalsh(P).sum()))

    phi = np.where(stoich.weak_mask, 1e-6, 0.0)
    dY = nu_ext @ phi
    n = len(Z)
    dYe_before = float(Z @ dY[:n])
    dYe_after = float(Z @ (P @ dY)[:n])

    print(f"== {network} ==")
    print(f"P shape: {P.shape}, rank {rank} (= m-3 = {m - 3})")
    print(f"max relative constraint residual over 20 decades = {worst_rel:.3e}  [<= 1e-12]")
    print(f"||P^2 - P||_inf = {idem:.3e}   ||P - P^T||_inf = {sym:.3e}")
    print(f"weak dYe through projection: {dYe_before:.6e} -> {dYe_after:.6e} "
          f"(abs change {abs(dYe_after - dYe_before):.3e})")


def main() -> None:
    for net in ("mesa_80", "mesa_151"):
        report(net)


if __name__ == "__main__":
    main()
