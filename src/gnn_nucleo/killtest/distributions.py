"""Streaming κ/active-set distributions over FluxStore runs (Task 2A).

The full-corpus runs are ~1M states × n_rxn — never loaded whole; every
statistic accumulates per chunk. κ thresholds follow the UNSCREENED
convention: ``kappa_summary`` REFUSES runs whose chunks record a screening
config unless ``allow_screened=True`` is passed explicitly (CLAUDE.md
two-κ rule; the ~7e-2 screened offset at NSE is physical, not maskable).
"""

from __future__ import annotations

import numpy as np

from .strata import T9_EDGES, T9_LABELS

__all__ = ["kappa_summary"]

#: log10-κ histogram bins (floor bin catches exact zeros / 1e-16 clamp)
_KBINS = np.concatenate([[-np.inf], np.linspace(-16.0, 0.0, 161)])


def _quantile_from_hist(counts: np.ndarray, q: float) -> float:
    """Quantile of log10 κ from the accumulated histogram (bin centers)."""
    tot = counts.sum()
    if tot == 0:
        return float("nan")
    c = np.cumsum(counts) / tot
    k = int(np.searchsorted(c, q))
    k = min(k, len(counts) - 1)
    if k == 0:
        return -16.0
    lo, hi = _KBINS[k], _KBINS[k + 1]
    return float(0.5 * (lo + hi))


def kappa_summary(
    store,
    *,
    allow_screened: bool = False,
    carrying: bool = True,
) -> list[dict]:
    """Per-T9-stratum κ distribution over a FluxStore run, streaming.

    Returns one dict per stratum: n_states, n_samples, median/p10 of κ
    (from a log10 histogram), frac κ>0.1, frac κ<1e-3, and the per-state
    active-set fraction (share of carrying strong pairs with κ>0.1),
    median over states.

    ``carrying``: restrict to strong forward pairs with f⁺ above the
    per-chunk-per-stratum median of positive f⁺ (the Step-5 convention;
    medians over ≥10⁵-sample strata are stable chunk-to-chunk).
    """
    nbins = len(_KBINS) - 1
    n_strata = len(T9_EDGES) - 1
    hist = np.zeros((n_strata, nbins), dtype=np.int64)
    n_states = np.zeros(n_strata, dtype=np.int64)
    n_gt = np.zeros(n_strata, dtype=np.int64)
    n_lt = np.zeros(n_strata, dtype=np.int64)
    n_tot = np.zeros(n_strata, dtype=np.int64)
    active_frac: list[list[float]] = [[] for _ in range(n_strata)]

    for chunk in store.iter_chunks():
        scr = str(chunk.attrs.get("screening", "None"))
        if scr not in ("None", "none") and not allow_screened:
            raise ValueError(
                f"run records screening={scr!r}: κ thresholds use the "
                "UNSCREENED convention (CLAUDE.md); pass allow_screened=True "
                "only for screening-offset diagnostics"
            )
        strong_fwd = chunk.is_forward_member & (chunk.pair_col >= 0)
        f = chunk.f_plus[strong_fwd]  # (n_pairs, n_states)
        k = chunk.kappa[strong_fwd]
        t9 = chunk.T / 1e9
        tb = np.digitize(t9, T9_EDGES) - 1
        tb[(tb < 0) | (tb >= n_strata)] = -1
        for b in range(n_strata):
            m = tb == b
            if not m.any():
                continue
            fs = f[:, m]
            ks = k[:, m]
            if carrying:
                pos = fs[fs > 0]
                if pos.size == 0:
                    continue
                sel = fs > np.median(pos)
            else:
                sel = fs > 0
            kk = ks[sel]
            logk = np.log10(np.maximum(kk, 1e-300))
            hist[b] += np.histogram(logk, bins=_KBINS)[0]
            n_states[b] += int(m.sum())
            n_gt[b] += int((kk > 0.1).sum())
            n_lt[b] += int((kk < 1e-3).sum())
            n_tot[b] += kk.size
            # per-state active fraction
            with np.errstate(invalid="ignore"):
                af = (sel & (ks > 0.1)).sum(axis=0) / np.maximum(sel.sum(axis=0), 1)
            active_frac[b].extend(af.tolist())

    out = []
    for b in range(n_strata):
        if n_tot[b] == 0:
            continue
        out.append(
            dict(
                stratum=T9_LABELS[b],
                n_states=int(n_states[b]),
                n_samples=int(n_tot[b]),
                log10_kappa_median=_quantile_from_hist(hist[b], 0.5),
                log10_kappa_p10=_quantile_from_hist(hist[b], 0.1),
                frac_gt_0p1=float(n_gt[b] / n_tot[b]),
                frac_lt_1em3=float(n_lt[b] / n_tot[b]),
                active_fraction_median=float(np.median(active_frac[b])),
            )
        )
    return out
