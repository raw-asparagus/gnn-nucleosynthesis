"""Step-5 Task-0 inherited-invariant guards (written before implementation).

These tests pin the PROGRAMMATIC form of the Step-4 gates that every flux/κ
computation must pass through (STEP4_REPORT.md; RESULTS.md 2026-07-10):

1. pf gate — raw JINA v-flag reverses are refused outright (they manufacture
   spurious κ floors at T9 ≥ 3; the engine's regime box reaches 7.9).
2. Appendix-B routing — gh-575 channels never take stock r23.05.1 values.
3. Screening pin — chugunov_2007 (the label configuration) or off, nothing else.
4. ADR-0003 — only reconciled canonical builds (pinned tabular ordering,
   provisional_reaction_set False) may feed the engine.
5. Label joins happen on state_id (row index) ONLY — never on (logT, logRho).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from gnn_nucleo.fluxes.guards import (
    PfGateError,
    assert_appendixb_routing,
    assert_pf_gate,
    assert_reconciled_build,
    assert_screening_allowed,
)

# ---------------------------------------------------------------------------
# 1. pf gate
# ---------------------------------------------------------------------------


class TestPfGate:
    def test_raises_on_any_vflag_reverse(self):
        flags = np.array([False, True, False])
        with pytest.raises(PfGateError, match="v-flag"):
            assert_pf_gate(flags, context="unit-test")

    def test_error_names_the_context(self):
        with pytest.raises(PfGateError, match="mesa_80"):
            assert_pf_gate(np.array([True]), context="mesa_80")

    def test_passes_when_clean(self):
        assert_pf_gate(np.zeros(5, dtype=bool), context="unit-test")

    def test_exported_npz_trips_the_gate(self, stoich_export):
        # The as-built ν export still carries pf-free v-flag reverses; the
        # gate must refuse it until replace_vflag_reverses has run (WP2).
        network, data = stoich_export
        assert data["derived_from_inverse"].any(), (
            "export unexpectedly free of v-flag reverses — if the builder now "
            "derives pf-corrected reverses, retire this test deliberately"
        )
        with pytest.raises(PfGateError):
            assert_pf_gate(data["derived_from_inverse"], context=network)


# ---------------------------------------------------------------------------
# 2. Appendix-B routing
# ---------------------------------------------------------------------------


class TestAppendixBRouting:
    # r_c12_to_he4_he4_he4 is excluded in BOTH networks (gh-575 photo class)
    EXCLUDED = "r_c12_to_he4_he4_he4"

    @pytest.mark.parametrize("network", ["mesa_80", "mesa_151"])
    def test_stock_mesa_source_refused_on_excluded_channel(self, network):
        with pytest.raises(ValueError, match="gh-575|[Aa]ppendix"):
            assert_appendixb_routing(network, [self.EXCLUDED], source="mesa")

    @pytest.mark.parametrize("source", ["mesa24", "pyna_pf"])
    def test_corrected_sources_pass_on_excluded_channel(self, source):
        assert_appendixb_routing("mesa_80", [self.EXCLUDED], source=source)

    def test_stock_mesa_passes_on_unaffected_channel(self):
        assert_appendixb_routing("mesa_80", ["r_si28_ag_s32"], source="mesa")

    def test_unknown_source_tag_rejected(self):
        with pytest.raises(ValueError, match="source"):
            assert_appendixb_routing("mesa_80", [self.EXCLUDED], source="mesa_r23")

    def test_counts_match_config(self):
        from gnn_nucleo.crosscheck.rates_compare import load_appendixb_handles

        assert len(load_appendixb_handles("mesa_80")) == 9
        assert len(load_appendixb_handles("mesa_151")) == 11


# ---------------------------------------------------------------------------
# 3. Screening pin
# ---------------------------------------------------------------------------


class TestScreeningPin:
    @pytest.mark.parametrize("name", ["chugunov_2007", None])
    def test_allowed(self, name):
        assert_screening_allowed(name)

    @pytest.mark.parametrize("name", ["chugunov_2009", "screen5", "", "chugunov"])
    def test_rejected(self, name):
        with pytest.raises(ValueError, match="screening"):
            assert_screening_allowed(name)


# ---------------------------------------------------------------------------
# 4. ADR-0003 reconciled-build assertion
# ---------------------------------------------------------------------------


def _fake_info(**overrides):
    from gnn_nucleo.graph.network import DEFAULT_TABULAR_ORDERING, BuildInfo

    kw = dict(
        network="mesa_80",
        pynucastro_version="2.12.0",
        tabular_ordering=DEFAULT_TABULAR_ORDERING,
        n_reaclib=569,
        n_tabular=38,
        n_duplicate_groups_resolved=4,
        provisional_reaction_set=False,
        disposition_sha256="deadbeef",
        n_dropped=3,
    )
    kw.update(overrides)
    return BuildInfo(**kw)


class TestReconciledBuild:
    def test_reconciled_build_passes(self):
        assert_reconciled_build(_fake_info())

    def test_provisional_set_refused(self):
        with pytest.raises(ValueError, match="provisional"):
            assert_reconciled_build(_fake_info(provisional_reaction_set=True))

    def test_wrong_tabular_ordering_refused(self):
        stale = ("ffn", "oda", "pruet_fuller", "langanke", "suzuki")
        with pytest.raises(ValueError, match="ordering"):
            assert_reconciled_build(_fake_info(tabular_ordering=stale))


# ---------------------------------------------------------------------------
# 5. state_id-only label joins
# ---------------------------------------------------------------------------


class TestStateIdJoins:
    @staticmethod
    def _frame(ids, **cols):
        df = pd.DataFrame(cols, index=pd.Index(ids, name="state_id"))
        return df

    def test_joins_on_state_id_index(self):
        from gnn_nucleo.data.labels import join_on_state_id

        left = self._frame([0, 1, 2], a=[1.0, 2.0, 3.0])
        right = self._frame([1, 2, 3], b=[10.0, 20.0, 30.0])
        out = join_on_state_id(left, right)
        assert list(out.index) == [1, 2]
        assert out.index.name == "state_id"
        assert list(out.columns) == ["a", "b"]

    def test_refuses_unnamed_index(self):
        from gnn_nucleo.data.labels import join_on_state_id

        left = pd.DataFrame({"a": [1.0]})  # RangeIndex, not named state_id
        right = self._frame([0], b=[1.0])
        with pytest.raises(ValueError, match="state_id"):
            join_on_state_id(left, right)

    def test_refuses_coordinate_index(self):
        from gnn_nucleo.data.labels import join_on_state_id

        left = pd.DataFrame({"a": [1.0]}, index=pd.Index([9.4], name="logT"))
        right = self._frame([0], b=[1.0])
        with pytest.raises(ValueError, match="state_id"):
            join_on_state_id(left, right)


# ---------------------------------------------------------------------------
# Label loading (needs the local Zenodo data; skipped where absent)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mesa80_csv():
    from gnn_nucleo.data.labels import training_csv_path

    path = training_csv_path("mesa_80", "1e-6")
    if not path.exists():
        pytest.skip("Zenodo training CSVs not present")
    return path


class TestLoadStepFrame:

    def test_subset_load(self, mesa80_csv):
        from gnn_nucleo.data.labels import load_step_frame

        df = load_step_frame(
            "mesa_80",
            "1e-6",
            columns=["logT", "logRho", "initial_si28", "final_si28", "eps_nuc"],
            state_ids=[0, 5, 17],
        )
        assert list(df.index) == [0, 5, 17]
        assert df.index.name == "state_id"
        assert df["initial_si28"].dtype == np.float64

    def test_eps_rescaled_to_physical_units(self, mesa80_csv):
        import pyarrow.csv as pv

        from gnn_nucleo.data.labels import load_step_frame
        from gnn_nucleo.data.schema import EPS_NORMALIZATION

        raw = pv.read_csv(
            mesa80_csv,
            convert_options=pv.ConvertOptions(include_columns=["eps_nuc"]),
        ).column("eps_nuc").to_numpy()[:8]
        df = load_step_frame(
            "mesa_80", "1e-6", columns=["eps_nuc"], state_ids=list(range(8))
        )
        np.testing.assert_allclose(
            df["eps_nuc"].to_numpy(), raw * EPS_NORMALIZATION, rtol=0
        )

    def test_unknown_dt_label_rejected(self):
        from gnn_nucleo.data.labels import training_csv_path

        with pytest.raises(ValueError, match="dt_label"):
            training_csv_path("mesa_80", "1e-7")
