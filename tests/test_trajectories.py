"""Tests for gnn_nucleo.data.trajectories — trajectory access + stall guard.

The stall rule is the exact lift of the Step-5 inline logic
(scripts/step5_qse.py, scripts/step5_bridges.py; RESULTS.md 2026-07-10
trajectory-stall anomaly): a trajectory row is stalled once the composition
stops changing (max_i |ΔX_i| < 1e-10 per output interval) while the file's
own eps_nuc keeps evolving. Only PRE-STALL rows are physical evolution, so
``select_rows`` defaults to ``prestall=True`` and post-stall access must be
requested explicitly.
"""

from __future__ import annotations

import numpy as np
import pytest

from gnn_nucleo.data import trajectories as tj


def _synthetic_X(n_rows: int, n_species: int, freeze_at: int | None) -> np.ndarray:
    """Composition that evolves by O(1e-3) per row, frozen from ``freeze_at``
    (diffs strictly below the stall tolerance afterwards)."""
    rng = np.random.default_rng(0)
    X = np.empty((n_rows, n_species))
    X[0] = rng.dirichlet(np.ones(n_species))
    for k in range(1, n_rows):
        if freeze_at is not None and k > freeze_at:
            X[k] = X[k - 1]  # exactly frozen
        else:
            step = rng.normal(scale=1e-3, size=n_species)
            X[k] = np.abs(X[k - 1] + step)
            X[k] /= X[k].sum()
    return X


class TestStallRow:
    def test_freeze_at_known_row(self):
        X = _synthetic_X(50, 8, freeze_at=20)
        # first sub-tolerance diff is X[21]-X[20] → diff index 20
        assert tj.stall_row(X) == 20

    def test_no_stall_returns_last_row(self):
        X = _synthetic_X(50, 8, freeze_at=None)
        assert tj.stall_row(X) == 49

    def test_matches_step5_inline_rule(self):
        """Behavior-identical to the code lifted from step5_qse/step5_bridges."""
        X = _synthetic_X(80, 12, freeze_at=33)
        dmax = np.abs(np.diff(X, axis=0)).max(axis=1)
        stalled = np.nonzero(dmax < 1e-10)[0]
        expected = int(stalled[0]) if stalled.size else len(X) - 1
        assert tj.stall_row(X) == expected


class TestSelectRows:
    def _frame(self, freeze_at):
        n = 40
        X = _synthetic_X(n, 6, freeze_at=freeze_at)
        age = np.geomspace(1e-8, 1e6, n)
        dt = np.diff(age, prepend=age[0])
        return tj.TrajectoryFrame(
            network="mesa_80", fname="synthetic.txt", source="rerun",
            logT=9.5, logRho=8.0, age=age, dt=dt,
            eps_nuc_raw=np.ones(n), eps_neu_raw=np.zeros(n), X=X,
        )

    def test_prestall_default_excludes_frozen_rows(self):
        traj = self._frame(freeze_at=15)
        rows = tj.select_rows(traj)
        assert rows[-1] < 15 + 1
        np.testing.assert_array_equal(rows, np.arange(tj.stall_row(traj.X)))

    def test_poststall_requires_explicit_override(self):
        traj = self._frame(freeze_at=15)
        rows = tj.select_rows(traj, prestall=False)
        np.testing.assert_array_equal(rows, np.arange(traj.X.shape[0]))

    def test_unstalled_trajectory_keeps_all_but_last(self):
        traj = self._frame(freeze_at=None)
        rows = tj.select_rows(traj)
        np.testing.assert_array_equal(rows, np.arange(traj.X.shape[0] - 1))


class TestLoadTrajectory:
    def _write_bbq_file(self, path, names, n_rows=6):
        """Emit the bbq hydrostatic output format: header
        'age dt eps_nuc eps_neu <isos>', row 0 = initial state."""
        rng = np.random.default_rng(1)
        age = np.concatenate([[0.0], np.geomspace(1e-8, 1e-3, n_rows - 1)])
        dt = np.diff(age, prepend=1e-10)
        dt[0] = 1e-10  # bbq placeholder on the initial row
        X = rng.dirichlet(np.ones(len(names)), size=n_rows)
        with open(path, "w") as fh:
            fh.write("age dt eps_nuc eps_neu " + " ".join(names) + " \n")
            for k in range(n_rows):
                row = [age[k], dt[k], 1e15 * k, 1e12 * k, *X[k]]
                fh.write(" ".join(f"{v:.16e}" for v in row) + "\n")
        return age, dt, X

    def test_roundtrip_and_fields(self, tmp_path):
        from gnn_nucleo.graph import load_isotope_table

        names = list(load_isotope_table("mesa_80").names)
        path = tmp_path / "output.txt"
        age, dt, X = self._write_bbq_file(path, names)
        traj = tj.load_trajectory(
            "mesa_80", path, source="rerun", logT=9.4, logRho=8.2
        )
        assert traj.network == "mesa_80"
        assert traj.source == "rerun"
        assert traj.X.shape == (6, len(names))
        np.testing.assert_allclose(traj.age, age)
        np.testing.assert_allclose(traj.X, X)
        assert traj.X.dtype == np.float64

    def test_wrong_isotope_order_refused(self, tmp_path):
        from gnn_nucleo.graph import load_isotope_table

        names = list(load_isotope_table("mesa_80").names)
        names[0], names[1] = names[1], names[0]  # swap two columns
        path = tmp_path / "output.txt"
        self._write_bbq_file(path, names)
        with pytest.raises(ValueError, match="isotope column"):
            tj.load_trajectory("mesa_80", path, source="rerun", logT=9.4, logRho=8.2)

    def test_zenodo_filename_parses_logT_logRho(self, tmp_path):
        from gnn_nucleo.graph import load_isotope_table

        names = list(load_isotope_table("mesa_80").names)
        path = tmp_path / "output_T_9.201_rho_7.666.txt"
        self._write_bbq_file(path, names)
        traj = tj.load_trajectory("mesa_80", path, source="zenodo")
        assert traj.logT == pytest.approx(9.201)
        assert traj.logRho == pytest.approx(7.666)

    def test_rerun_requires_explicit_coords(self, tmp_path):
        from gnn_nucleo.graph import load_isotope_table

        names = list(load_isotope_table("mesa_80").names)
        path = tmp_path / "output.txt"
        self._write_bbq_file(path, names)
        with pytest.raises(ValueError, match="logT"):
            tj.load_trajectory("mesa_80", path, source="rerun")


class TestEpsConverters:
    def _frame(self):
        n = 10
        age = np.geomspace(1e-6, 1e2, n)
        dt = np.diff(age, prepend=0.0)  # every bbq row has dt > 0
        return tj.TrajectoryFrame(
            network="mesa_80", fname="synthetic.txt", source="rerun",
            logT=9.5, logRho=8.0, age=age, dt=dt,
            eps_nuc_raw=np.linspace(1e14, 1e16, n),
            eps_neu_raw=np.linspace(1e10, 1e12, n),
            X=_synthetic_X(n, 6, freeze_at=None),
        )

    def test_unpinned_convention_raises(self):
        traj = self._frame()
        if tj.TRAJ_EPS_CONVENTION is None:
            with pytest.raises(RuntimeError, match="not pinned"):
                tj.eps_nuc_rate(traj)
            with pytest.raises(RuntimeError, match="not pinned"):
                tj.eps_nuc_integrated(traj)

    def test_integrated_convention_roundtrip(self):
        traj = self._frame()
        rate = tj.eps_nuc_rate(traj, convention="integrated")
        integ = tj.eps_nuc_integrated(traj, convention="integrated")
        np.testing.assert_allclose(integ, traj.eps_nuc_raw)
        np.testing.assert_allclose(rate * traj.dt, integ)

    def test_rate_convention_roundtrip(self):
        traj = self._frame()
        rate = tj.eps_nuc_rate(traj, convention="rate")
        integ = tj.eps_nuc_integrated(traj, convention="rate")
        np.testing.assert_allclose(rate, traj.eps_nuc_raw)
        np.testing.assert_allclose(integ, rate * traj.dt)

    def test_unknown_convention_refused(self):
        traj = self._frame()
        with pytest.raises(ValueError, match="convention"):
            tj.eps_nuc_rate(traj, convention="per-fortnight")
