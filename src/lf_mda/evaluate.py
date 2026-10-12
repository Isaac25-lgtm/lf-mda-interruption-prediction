"""Performance metrics: discrimination, calibration and top-k capture.

Top-k capture uses an expected-value tie policy: when tied scores straddle the capacity
cut-off, the tied group contributes in proportion to the share of it that fits, which is
the expectation under random ordering within ties. This keeps coarse rule scores and
continuous model scores comparable.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import rankdata

EPS = 1e-6


def _valid(y, p):
    y, p = np.asarray(y, dtype=float), np.asarray(p, dtype=float)
    ok = ~np.isnan(y) & ~np.isnan(p)
    return y[ok], p[ok]


def auroc(y, score) -> float:
    y, score = _valid(y, score)
    n1 = int(y.sum())
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rankdata(score)
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def pr_auc(y, score) -> float:
    """Average precision (step-wise area under the precision-recall curve)."""
    y, score = _valid(y, score)
    if y.sum() == 0:
        return float("nan")
    order = np.argsort(-score, kind="mergesort")
    ys, ss = y[order], score[order]
    tp = np.cumsum(ys)
    last = np.r_[ss[1:] != ss[:-1], True]  # evaluate at the end of each tied block
    precision = tp[last] / (np.flatnonzero(last) + 1)
    recall = tp[last] / y.sum()
    return float(np.sum(np.diff(np.r_[0.0, recall]) * precision))


def brier(y, p) -> float:
    y, p = _valid(y, p)
    return float(np.mean((p - y) ** 2)) if len(y) else float("nan")


def log_loss(y, p) -> float:
    y, p = _valid(y, p)
    if not len(y):
        return float("nan")
    p = np.clip(p, EPS, 1 - EPS)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def _logit(p):
    p = np.clip(np.asarray(p, dtype=float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def _irls(X, y, offset=None, iters=50):
    beta = np.zeros(X.shape[1])
    off = np.zeros(len(y)) if offset is None else offset
    for _ in range(iters):
        eta = np.clip(X @ beta + off, -30, 30)
        mu = 1 / (1 + np.exp(-eta))
        w = mu * (1 - mu)
        H = X.T @ (X * w[:, None])
        g = X.T @ (y - mu)
        try:
            step = np.linalg.solve(H + 1e-10 * np.eye(len(beta)), g)
        except np.linalg.LinAlgError:
            return np.full(X.shape[1], np.nan)
        beta = beta + step
        if np.max(np.abs(step)) < 1e-8:
            break
    return beta


def calibration_intercept(y, p) -> float:
    """Calibration-in-the-large: intercept of a logistic model with logit(p) as offset."""
    y, p = _valid(y, p)
    if len(y) == 0 or y.min() == y.max():
        return float("nan")
    return float(_irls(np.ones((len(y), 1)), y, offset=_logit(p))[0])


def calibration_slope(y, p) -> float:
    y, p = _valid(y, p)
    lp = _logit(p)
    if len(y) == 0 or y.min() == y.max() or np.ptp(lp) < 1e-9:
        return float("nan")
    return float(_irls(np.column_stack([np.ones(len(y)), lp]), y)[1])


def observed_expected(y, p) -> float:
    y, p = _valid(y, p)
    return float(y.sum() / p.sum()) if p.sum() > 0 else float("nan")


def top_k_counts(y, score, frac: float) -> tuple[float, float]:
    """Expected (true positives, number selected) when the top `frac` of units is selected."""
    y, score = _valid(y, score)
    n = len(y)
    k = frac * n
    if n == 0:
        return float("nan"), float("nan")
    order = np.argsort(-score, kind="mergesort")
    ys, ss = y[order], score[order]
    starts = np.r_[0, np.flatnonzero(ss[1:] != ss[:-1]) + 1]
    sizes = np.diff(np.r_[starts, n])
    group_events = np.add.reduceat(ys, starts)
    cum = np.cumsum(sizes)
    n_full = int(np.searchsorted(cum, k, side="right"))   # tied groups that fit entirely
    tp = float(group_events[:n_full].sum())
    taken = float(cum[n_full - 1]) if n_full else 0.0
    if n_full < len(sizes) and k > taken:                  # boundary group, shared pro rata
        tp += float(group_events[n_full]) * (k - taken) / float(sizes[n_full])
    return tp, float(k)


def capture_at(y, score, frac: float) -> float:
    """Share of all events captured in the top `frac` (sensitivity at capacity)."""
    yv, _ = _valid(y, score)
    if yv.sum() == 0:
        return float("nan")
    tp, _ = top_k_counts(y, score, frac)
    return tp / float(yv.sum())


def precision_at(y, score, frac: float) -> float:
    tp, k = top_k_counts(y, score, frac)
    return tp / k if k and k > 0 else float("nan")


def stratified_auroc(y, score, strata) -> float:
    """Concordance using only pairs from the same stratum (e.g. the same country-year).

    This removes between-country and between-year differences, so it measures whether a
    score ranks IUs correctly inside a country in a given year.
    """
    y, score, strata = np.asarray(y, float), np.asarray(score, float), np.asarray(strata)
    ok = ~np.isnan(y) & ~np.isnan(score)
    y, score, strata = y[ok], score[ok], strata[ok]
    num = den = 0.0
    order = np.argsort(strata, kind="mergesort")
    y, score, strata = y[order], score[order], strata[order]
    bounds = np.r_[0, np.flatnonzero(strata[1:] != strata[:-1]) + 1, len(y)]
    for a, b in zip(bounds[:-1], bounds[1:]):
        ys = y[a:b]
        n1 = ys.sum()
        n0 = (b - a) - n1
        if n1 == 0 or n0 == 0:
            continue
        r = rankdata(score[a:b])
        num += r[ys == 1].sum() - n1 * (n1 + 1) / 2
        den += n1 * n0
    return float(num / den) if den > 0 else float("nan")


def all_metrics(y, p, rank_score=None, strata=None) -> dict:
    """Metric set for one model. `p` is a probability; `rank_score` (default p) ranks units."""
    s = p if rank_score is None else rank_score
    yv, _ = _valid(y, p)
    out = {
        "n": len(yv), "events": int(yv.sum()),
        "prevalence": float(yv.mean()) if len(yv) else float("nan"),
        "auroc": auroc(y, s), "pr_auc": pr_auc(y, s), "brier": brier(y, p),
        "log_loss": log_loss(y, p), "calibration_intercept": calibration_intercept(y, p),
        "calibration_slope": calibration_slope(y, p),
        "observed_expected_ratio": observed_expected(y, p),
        "capture_at_10pct": capture_at(y, s, 0.10), "capture_at_20pct": capture_at(y, s, 0.20),
        "precision_at_10pct": precision_at(y, s, 0.10),
        "precision_at_20pct": precision_at(y, s, 0.20),
    }
    if strata is not None:
        out["within_country_year_auroc"] = stratified_auroc(y, s, strata)
    return out


RANKING_METRICS = ["auroc", "pr_auc", "capture_at_10pct", "capture_at_20pct",
                   "precision_at_10pct", "precision_at_20pct", "within_country_year_auroc"]
PROBABILITY_METRICS = ["brier", "log_loss", "calibration_intercept", "calibration_slope",
                       "observed_expected_ratio"]
