"""Relaxed-manifold row assembly (Task 2B): pre-stall shipped trajectory
rows + local bbq rerun rows, with per-row δ_r (vs NSE) and unscreened κ.

Rows come from FluxStore trajectory-style runs (one chunk per trajectory,
attrs: trajectory_file, logT, logRho, age, source). The pre-stall guard is
applied through data.trajectories (composition read from the same file the
fluxes were computed on). NSE references are cached on rounded
(T9, logρ, Yₑ) keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = ["RelaxedRows", "assemble"]


@dataclass
class RelaxedRows:
    """Column-stacked per-row arrays over the relaxed manifold.

    phi/kappa/f_plus are (n_rxn, n_rows) in the run's ν-column order;
    X is (n_rows, n_species). ``delta_r`` is (n_rxn, n_rows) Guidry
    reaction departure vs the row's NSE reference. ``attractor`` marks rows
    at/after the first-quiet arrival row (strong-relaxation done; the
    weak-drift tail) — the relaxation-degree split of the kill-test.
    """

    network: str
    traj_key: list[str] = field(default_factory=list)
    source: list[str] = field(default_factory=list)
    age: np.ndarray | None = None
    T: np.ndarray | None = None
    rho: np.ndarray | None = None
    ye: np.ndarray | None = None
    X: np.ndarray | None = None
    f_plus: np.ndarray | None = None
    phi: np.ndarray | None = None
    kappa: np.ndarray | None = None
    delta_r: np.ndarray | None = None
    nse_converged: np.ndarray | None = None
    attractor: np.ndarray | None = None

    @property
    def n_rows(self) -> int:
        return 0 if self.T is None else self.T.size


def _traj_for_chunk(network: str, attrs) -> "object":
    from gnn_nucleo.data.trajectories import load_trajectory

    src = str(attrs.get("source", "zenodo"))
    fname = attrs["trajectory_file"]
    if src == "zenodo":
        return load_trajectory(network, fname)
    return load_trajectory(
        network,
        fname,
        source="rerun",
        logT=float(attrs["logT"]),
        logRho=float(attrs["logRho"]),
    )


def assemble(
    network: str,
    run_ids: list[str],
    *,
    prestall: bool = True,
    max_rows_per_traj: int = 24,
    with_delta: bool = True,
    t9_min: float = 0.0,
) -> RelaxedRows:
    """Assemble relaxed-manifold rows from UNSCREENED trajectory-style runs.

    Rows are log-spaced over each trajectory's pre-stall range (row 0
    excluded — diff-based guards need a predecessor), at most
    ``max_rows_per_traj`` per trajectory. δ_r per row via the independent
    NSE solver (cached on rounded state keys).
    """
    from gnn_nucleo.data.trajectories import select_rows, stall_row
    from gnn_nucleo.fluxes.store import FluxStore
    from gnn_nucleo.graph import load_isotope_table, npz_path
    from gnn_nucleo.qse import build_inputs, delta_species, solve_nse_batch
    from gnn_nucleo.qse.diagnostics import reaction_delta_batch

    table = load_isotope_table(network)
    A = table.A.astype(np.float64)
    inputs = build_inputs(network) if with_delta else None
    with np.load(npz_path(network), allow_pickle=False) as z:
        nu = z["nu"]

    out = RelaxedRows(network=network)
    cols: dict[str, list] = {k: [] for k in
                             ("age", "T", "rho", "ye", "X", "f_plus", "phi",
                              "kappa", "attractor")}
    # Per-row NSE-reference key (rounded state) + the first-occurrence exact
    # (T, ρ, Yₑ) for each distinct key — the NSE reference is solved ONCE per
    # key at the first row that hits it (preserves the scalar cache semantics),
    # then all distinct keys are solved in ONE batched Newton pass below.
    row_keys: list[tuple] = []
    key_state: dict[tuple, tuple[float, float, float]] = {}

    for run_id in run_ids:
        store = FluxStore(network, run_id)
        for chunk in store.iter_chunks():
            scr = str(chunk.attrs.get("screening", "None"))
            if scr not in ("None", "none"):
                raise ValueError(
                    f"{run_id}: κ/δ analysis requires the UNSCREENED run "
                    f"(got screening={scr!r})"
                )
            t9 = 10.0 ** float(chunk.attrs["logT"]) / 1e9
            if t9 < t9_min:
                continue
            traj = _traj_for_chunk(network, chunk.attrs)
            rows = select_rows(traj, prestall=prestall)[1:]
            if rows.size == 0:
                continue
            if rows.size > max_rows_per_traj:
                pick = np.unique(
                    np.geomspace(rows[0], rows[-1], max_rows_per_traj).astype(int)
                )
                rows = pick
            rho = 10.0 ** float(chunk.attrs["logRho"])
            arrival = stall_row(traj.X, mode="first_quiet")
            key_base = str(chunk.attrs.get("run_key", traj.fname))
            for r in rows:
                Y = traj.X[r] / A
                ye = float((table.Z * Y).sum() / (A * Y).sum())
                cols["age"].append(traj.age[r])
                cols["T"].append(t9 * 1e9)
                cols["rho"].append(rho)
                cols["ye"].append(ye)
                cols["X"].append(traj.X[r])
                cols["f_plus"].append(chunk.f_plus[:, r])
                cols["phi"].append(chunk.phi[:, r])
                cols["kappa"].append(chunk.kappa[:, r])
                cols["attractor"].append(bool(r >= arrival))
                out.traj_key.append(f"{run_id}:{key_base}")
                out.source.append(traj.source)
                if with_delta:
                    key = (round(t9, 3), round(np.log10(rho), 3), round(ye, 4))
                    row_keys.append(key)
                    key_state.setdefault(key, (t9 * 1e9, rho, ye))

    if not cols["T"]:
        return out
    out.age = np.array(cols["age"])
    out.T = np.array(cols["T"])
    out.rho = np.array(cols["rho"])
    out.ye = np.array(cols["ye"])
    out.X = np.vstack(cols["X"])
    out.f_plus = np.column_stack(cols["f_plus"])
    out.phi = np.column_stack(cols["phi"])
    out.kappa = np.column_stack(cols["kappa"])
    out.attractor = np.array(cols["attractor"], dtype=bool)
    if with_delta:
        # One batched Newton over the DISTINCT NSE-reference keys, then scatter
        # per-row and compute δ_r for every row at once (reaction_delta_batch is
        # row-vectorized). Equivalent to the former per-row cached scalar solves.
        keys = list(key_state)
        kT = np.array([key_state[k][0] for k in keys])
        krho = np.array([key_state[k][1] for k in keys])
        kye = np.array([key_state[k][2] for k in keys])
        res = solve_nse_batch(inputs, kT, krho, kye)
        conv_by_key = {k: bool(res.converged[i]) for i, k in enumerate(keys)}
        yref_by_key = {k: res.X[i] / A for i, k in enumerate(keys)}
        n_rows = out.X.shape[0]
        Y_all = out.X / A
        yref = np.ones_like(Y_all)  # placeholder for non-converged rows
        conv = np.zeros(n_rows, dtype=bool)
        for j, k in enumerate(row_keys):
            conv[j] = conv_by_key[k]
            if conv[j]:
                yref[j] = yref_by_key[k]
        delta = delta_species(Y_all, yref)  # (n_rows, n_species)
        dr = reaction_delta_batch(nu, delta)  # (n_rows, n_rxn)
        dr[~conv] = np.nan
        out.delta_r = dr.T
        out.nse_converged = conv
    return out
