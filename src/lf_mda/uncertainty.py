"""Country-clustered uncertainty: bootstrap intervals and leave-one-country-out jackknife.

Resampling whole countries respects both repeated IU observations and country-wide
shocks. With few event-contributing countries the percentile interval is itself
unstable, so the jackknife range is always reported next to it.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .evaluate import all_metrics


def _metrics_for(df: pd.DataFrame, models: list[str], rank_cols: dict[str, str]) -> dict:
    strata = (df["iso2"].astype(str) + "_" + df["year"].astype(str)).to_numpy()
    y = df["y"].to_numpy()
    return {m: all_metrics(y, df[f"p_{m}"].to_numpy(),
                           df[rank_cols[m]].to_numpy() if m in rank_cols else None, strata)
            for m in models}


def point_estimates(df: pd.DataFrame, models: list[str],
                    rank_cols: dict[str, str] | None = None) -> pd.DataFrame:
    res = _metrics_for(df, models, rank_cols or {})
    return pd.DataFrame(res).T.rename_axis("model").reset_index()


def cluster_bootstrap(df: pd.DataFrame, models: list[str], comparator: str,
                      rank_cols: dict[str, str] | None = None, n_boot: int = 2000,
                      seed: int = 0, cluster: str = "iso2") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Percentile intervals for each metric and for paired differences versus `comparator`.

    Returns (intervals, differences), both long tables.
    """
    rank_cols = rank_cols or {}
    rng = np.random.default_rng(seed)
    groups = {k: g.index.to_numpy() for k, g in df.groupby(cluster)}
    keys = list(groups)
    point = _metrics_for(df, models, rank_cols)
    metric_names = [k for k in next(iter(point.values())) if k not in ("n", "events")]
    draws = {m: {k: np.full(n_boot, np.nan) for k in metric_names} for m in models}
    for b in range(n_boot):
        pick = rng.integers(0, len(keys), len(keys))
        idx = np.concatenate([groups[keys[i]] for i in pick])
        res = _metrics_for(df.loc[idx], models, rank_cols)
        for m in models:
            for k in metric_names:
                draws[m][k][b] = res[m][k]
    rows, diffs = [], []
    for m in models:
        for k in metric_names:
            d = draws[m][k]
            ok = ~np.isnan(d)
            lo, hi = (np.percentile(d[ok], [2.5, 97.5]) if ok.sum() >= 50 else (np.nan, np.nan))
            rows.append({"model": m, "metric": k, "estimate": point[m][k], "ci_low": lo,
                         "ci_high": hi, "boot_valid": int(ok.sum())})
            if m != comparator:
                dd = d - draws[comparator][k]
                ok2 = ~np.isnan(dd)
                lo2, hi2 = (np.percentile(dd[ok2], [2.5, 97.5]) if ok2.sum() >= 50
                            else (np.nan, np.nan))
                diffs.append({"model": m, "comparator": comparator, "metric": k,
                              "difference": point[m][k] - point[comparator][k],
                              "ci_low": lo2, "ci_high": hi2, "boot_valid": int(ok2.sum()),
                              "interval_excludes_zero":
                                  bool(ok2.sum() >= 50 and (lo2 > 0 or hi2 < 0))})
    out = pd.DataFrame(rows)
    out["n_clusters"] = len(keys)
    return out, pd.DataFrame(diffs)


def country_jackknife(df: pd.DataFrame, models: list[str],
                      rank_cols: dict[str, str] | None = None,
                      metrics: tuple[str, ...] = ("auroc", "capture_at_20pct",
                                                  "within_country_year_auroc", "brier")
                      ) -> pd.DataFrame:
    """Recompute key metrics leaving out one country at a time."""
    rank_cols = rank_cols or {}
    rows = []
    for iso2 in sorted(df["iso2"].unique()):
        sub = df[df["iso2"] != iso2]
        dropped = df[df["iso2"] == iso2]
        res = _metrics_for(sub, models, rank_cols)
        for m in models:
            row = {"dropped_country": iso2, "dropped_n": len(dropped),
                   "dropped_events": int(dropped["y"].sum()), "model": m}
            row |= {k: res[m][k] for k in metrics}
            rows.append(row)
    return pd.DataFrame(rows)
