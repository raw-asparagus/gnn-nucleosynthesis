"""Stoichiometric matrix ν, lepton ledgers, and constraint matrix C.

This module is the single source of truth for the fixed conservation layer
(root CLAUDE.md invariant #1): everything downstream — Target A's
dY = ν φ, Target B's null-space projector, the blocking gate in
tests/test_conservation.py — consumes the arrays built here.

Conventions
-----------
ν[i, j]   net stoichiometric coefficient of species i in reaction j
          (products +, reactants −), float64, rows in the isotope-table
          (YAML = CSV-header) order.
Lepton ledgers per reaction (columns of the extended ν̃):
          d_electron, d_neutrino, d_antineutrino — assigned from the rate's
          ``weak_type``, NEVER back-derived from Z·ν (that would make the
          charge-to-lepton closure a tautology):

          =================  ====  ====  ====
          weak_type          d_e   d_ν   d_ν̄
          =================  ====  ====  ====
          electron_capture    −1    +1     0
          beta_neg            +1     0    +1
          beta_pos            −1    +1     0   (annihilated-positron convention)
          =================  ====  ====  ====

C (3 × (n+3)) with extended-species columns [nuclei…, e⁻, ν, ν̄]:
          baryon row  [Aᵢ…, 0, 0, 0]
          charge row  [Zᵢ…, −1, 0, 0]
          lepton row  [0…,  +1, +1, −1]
Every column of ν̃ = vstack(ν, ledgers) must satisfy C ν̃ = 0 exactly; the
build aborts naming the offending reaction otherwise.

β⁺ note: the emitted positron annihilates with a plasma electron, so its net
effect on the electron ledger is −1 (charge closes: nucleus loses one unit to
the electron sea) and lepton number closes through the emitted ν. EC and β⁺
therefore share a ledger signature — both lower Yₑ; β⁻ raises it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pynucastro as pyna

from .isotopes import IsotopeTable

#: weak_type → (d_electron, d_neutrino, d_antineutrino)
WEAK_LEDGERS: dict[str, tuple[float, float, float]] = {
    "electron_capture": (-1.0, +1.0, 0.0),
    "beta_neg": (+1.0, 0.0, +1.0),
    "beta_pos": (-1.0, +1.0, 0.0),
}

#: number of lepton ledger rows appended to ν in ν̃ (e⁻, ν, ν̄)
N_LEPTON_ROWS = 3


@dataclass(frozen=True)
class Stoich:
    """Validated stoichiometry of one network. All float64."""

    network: str
    species: tuple[str, ...]          # YAML names, row order of nu
    nu: np.ndarray                    # (n, r)
    nu_ext: np.ndarray                # (n+3, r) — nu stacked with the ledgers
    A: np.ndarray                     # (n,)
    Z: np.ndarray                     # (n,)
    C: np.ndarray                     # (3, n+3)
    weak_mask: np.ndarray             # (r,) bool
    weak_type: tuple[str, ...]        # '' for strong/EM
    d_electron: np.ndarray            # (r,)
    d_neutrino: np.ndarray            # (r,)
    d_antineutrino: np.ndarray        # (r,)
    rate_fnames: tuple[str, ...]
    rate_strings: tuple[str, ...]
    Q: np.ndarray                     # (r,) rate Q-values [MeV]
    is_tabular: np.ndarray            # (r,) bool
    derived_from_inverse: np.ndarray  # (r,) bool (ReacLib 'v' reverse marker)
    chapter: np.ndarray               # (r,) int64, −1 for tabular
    source_label: tuple[str, ...]

    @property
    def n_species(self) -> int:
        return self.nu.shape[0]

    @property
    def n_reactions(self) -> int:
        return self.nu.shape[1]


def constraint_matrix(A: np.ndarray, Z: np.ndarray) -> np.ndarray:
    """C (3 × (n+3)) over extended species [nuclei…, e⁻, ν, ν̄] (see module doc)."""
    n = len(A)
    C = np.zeros((3, n + N_LEPTON_ROWS), dtype=np.float64)
    C[0, :n] = np.asarray(A, dtype=np.float64)          # baryon (leptons: 0)
    C[1, :n] = np.asarray(Z, dtype=np.float64)          # charge
    C[1, n] = -1.0                                      #   e⁻
    C[2, n] = +1.0                                      # lepton number: e⁻
    C[2, n + 1] = +1.0                                  #   ν
    C[2, n + 2] = -1.0                                  #   ν̄
    return C


def build_stoich(rc: pyna.RateCollection, table: IsotopeTable) -> Stoich:
    """Build and validate ν, the lepton ledgers, and C for ``rc``.

    Raises ``ValueError`` naming the offending reaction on ANY violated
    column: baryon leak, strong-column charge leak, weak column whose nuclear
    charge change disagrees with its weak_type ledger, |ΔZ| ≠ 1 weak column,
    or an unrecognised weak_type.
    """
    rates = list(rc.get_rates())
    idx = table.index()
    n, r = table.n, len(rates)

    nu = np.zeros((n, r), dtype=np.float64)
    weak_mask = np.zeros(r, dtype=bool)
    weak_types: list[str] = []
    d_e = np.zeros(r, dtype=np.float64)
    d_nu = np.zeros(r, dtype=np.float64)
    d_nubar = np.zeros(r, dtype=np.float64)

    A = table.A.astype(np.float64)
    Z = table.Z.astype(np.float64)

    for j, rate in enumerate(rates):
        for sp in rate.reactants:
            nu[idx[sp], j] -= 1.0
        for sp in rate.products:
            nu[idx[sp], j] += 1.0

        wt = getattr(rate, "weak_type", "") or ""
        is_weak = bool(getattr(rate, "weak", False))
        if is_weak != (wt in WEAK_LEDGERS):
            raise ValueError(
                f"{table.network}: rate {rate.fname}: weak={is_weak} but "
                f"weak_type={wt!r} — unrecognised weak classification"
            )
        weak_mask[j] = is_weak
        weak_types.append(wt)
        if is_weak:
            d_e[j], d_nu[j], d_nubar[j] = WEAK_LEDGERS[wt]

    # --- fail-loud column validation (exact: entries are small integers) ----
    for j, rate in enumerate(rates):
        da = float(A @ nu[:, j])
        if da != 0.0:
            raise ValueError(
                f"{table.network}: baryon leak ΣAν = {da} in column {j} ({rate.fname})"
            )
        dq = float(Z @ nu[:, j])
        if not weak_mask[j]:
            if dq != 0.0:
                raise ValueError(
                    f"{table.network}: charge leak ΣZν = {dq} in strong/EM "
                    f"column {j} ({rate.fname})"
                )
        else:
            if abs(dq) != 1.0:
                raise ValueError(
                    f"{table.network}: weak column {j} ({rate.fname}) has |ΔZ| = "
                    f"{abs(dq)} ≠ 1 — not a single-nucleon weak transition"
                )
            if dq != d_e[j]:
                raise ValueError(
                    f"{table.network}: weak column {j} ({rate.fname}, "
                    f"weak_type={weak_types[j]!r}): nuclear ΔZ = {dq} but ledger "
                    f"d_electron = {d_e[j]} — charge-to-lepton closure broken"
                )

    nu_ext = np.vstack([nu, d_e, d_nu, d_nubar])
    C = constraint_matrix(A, Z)
    residual = float(np.abs(C @ nu_ext).max())
    if residual != 0.0:
        raise ValueError(f"{table.network}: C @ nu_ext residual {residual} != 0")

    return Stoich(
        network=table.network,
        species=table.names,
        nu=nu,
        nu_ext=nu_ext,
        A=A,
        Z=Z,
        C=C,
        weak_mask=weak_mask,
        weak_type=tuple(weak_types),
        d_electron=d_e,
        d_neutrino=d_nu,
        d_antineutrino=d_nubar,
        rate_fnames=tuple(rate.fname for rate in rates),
        rate_strings=tuple(str(rate) for rate in rates),
        Q=np.array([float(rate.Q) for rate in rates], dtype=np.float64),
        is_tabular=np.array(
            [isinstance(rate, pyna.rates.TabularRate) for rate in rates], dtype=bool
        ),
        derived_from_inverse=np.array(
            [bool(getattr(rate, "derived_from_inverse", False)) for rate in rates],
            dtype=bool,
        ),
        chapter=np.array(
            [
                rate.chapter if isinstance(getattr(rate, "chapter", None), int) else -1
                for rate in rates
            ],
            dtype=np.int64,
        ),
        source_label=tuple(
            str((getattr(rate, "source", None) or {}).get("Label", "")) for rate in rates
        ),
    )
