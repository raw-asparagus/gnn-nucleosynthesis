"""C(ᴬZ) coefficient construction vs pynucastro's _nucleon_fraction_nse at
fixed chemical potentials — same inputs, independent code path, ≤1e-12 rel."""

from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture(scope="module")
def inputs80():
    from gnn_nucleo.qse.coeffs import build_inputs

    return build_inputs("mesa_80")


class TestCoeffsVsPyna:
    @pytest.mark.parametrize("t9,rho", [(5.0, 1e7), (6.3, 1e8), (7.9, 1e9)])
    def test_mass_fractions_match_at_fixed_u(self, inputs80, t9, rho):
        import pynucastro as pyna
        from pynucastro.constants import constants
        from pynucastro.networks.nse_network import NseState

        from gnn_nucleo.graph import build_rate_collection, load_isotope_table
        from gnn_nucleo.qse.coeffs import nse_log_coeffs

        table = load_isotope_table("mesa_80")
        rc, _ = build_rate_collection(table)
        nse = pyna.NSENetwork(rates=rc.get_rates())
        T = t9 * 1e9
        state = NseState(T, rho, 0.48)
        u = (-4.0, -14.0)
        u_c = {n: 0 for n in nse.unique_nuclei}
        ref = nse._nucleon_fraction_nse(u, u_c, state)

        kT = constants.k_MeV * T
        logC = nse_log_coeffs(inputs80, T, rho)
        X = np.exp(
            np.minimum(
                logC + (inputs80.Z * u[0] + inputs80.N * u[1]) / kT, 500.0
            )
        )
        nuclei = list(table.nuclei)
        ref_arr = np.array([ref[n] for n in nuclei])
        rel = np.abs(X - ref_arr) / np.maximum(np.abs(ref_arr), 1e-300)
        assert rel.max() <= 1e-12, f"worst rel {rel.max():.3e}"

    def test_inputs_cover_all_species(self, inputs80):
        assert inputs80.n == 80
        assert np.all(inputs80.spin_states >= 1)
        assert np.all(inputs80.nucbind[inputs80.A > 1] > 0)
        # neut/h1 have no binding
        names = list(inputs80.names)
        assert inputs80.nucbind[names.index("neut")] == 0.0
