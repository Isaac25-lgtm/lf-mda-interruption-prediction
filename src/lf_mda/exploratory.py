"""EXPLORATORY, POST HOC models proposed after the locked test had been opened.

Nothing in this module is confirmatory. These approaches were designed on 2026-10-12
after the locked-test results for the pre-specified models were known. They are
developed and tuned on development folds only, but their held-out numbers cannot count
as an independent test: the design choices were made with knowledge of how the
pre-specified models performed on those same years. A new, untouched year of data is
needed before any of them can be claimed to work.

Motivation, from the audit and the pre-specified results:
  * about 60% of outcome variance lies between country-years, so a model should
    separate "which country-year" from "which IU inside it";
  * the fixed rule ranked well across countries but not within them on the locked
    test, while fitted models did the reverse.

Approaches:
  X1 within_between_logistic  - ridge logistic on country-year means of the IU
     predictors plus each IU's deviation from its country-year mean (a Mundlak-type
     within/between decomposition). Means use predictors only, never outcomes.
  X2 two_level_rank           - rank countries by prior-year non-delivery rate, then
     IUs within a country by the history rule (no fitting for the ranking).
  X3 rule_plus_rounds         - the history rule with one extra term: fewer cumulative
     rounds raises the score (the strongest single within-country predictor on
     development data).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from . import paths
from .baselines import SingleScoreModel
from .evaluate import log_loss
from .pipeline import frame_digest, load_frames, write_run_manifest
from .splits import final_training_index, held_out_index, rolling_origin_folds
from .uncertainty import cluster_bootstrap, point_estimates

OUT = paths.EVALUATION / "exploratory_posthoc"
IU_FEATURES = ["h_nd_recent", "h_nd_count_3", "h_ineffective_recent", "h_epi_cov_last_round",
               "h_cum_mda", "h_eff_rounds_obs", "h_log_pop_tot", "a_nd_rate_recent"]
C_GRID = [0.001, 0.01, 0.1]
LABELS = {"within_between_logistic": "X1 within/between-country logistic",
          "two_level_rank": "X2 country then district ranking",
          "rule_plus_rounds": "X3 history rule + fewer cumulative rounds"}
REFERENCE = ["history_rule", "logistic_iu_only"]


def add_exploratory_columns(feat: pd.DataFrame) -> pd.DataFrame:
    """Add within/between features and the two rank scores. Uses predictors only."""
    out = feat.copy()
    key = [out["iso2"], out["year"]]
    for c in IU_FEATURES:
        mean = out.groupby(key)[c].transform("mean")
        out[f"b_{c}"] = mean                       # between: country-year mean
        out[f"w_{c}"] = out[c] - mean              # within: deviation from that mean
    # X2: country prior-year rate dominates; the rule orders IUs inside a country-year
    rule_pct = out.groupby(key)["rule_score"].rank(pct=True, method="average")
    out["x2_score"] = out["c_nd_rate_recent_full"].fillna(0) + 0.001 * rule_pct
    # X3: rule plus a bounded bonus for fewer cumulative rounds (0 to 1 point)
    rounds = out["h_cum_mda"].clip(0, 12).fillna(12)
    out["x3_score"] = out["rule_score"] + (1 - rounds / 12)
    return out


class WithinBetweenLogistic:
    def __init__(self, C: float):
        self.C = C
        self.cols = [f"{p}_{c}" for c in IU_FEATURES for p in ("b", "w")] + ["c_nd_rate_recent"]

    def _x(self, X: pd.DataFrame) -> np.ndarray:
        return X[self.cols].fillna(self.fill_).to_numpy(dtype=float)

    def fit(self, X: pd.DataFrame, y) -> WithinBetweenLogistic:
        self.fill_ = X[self.cols].median()          # medians from training rows only
        self.pipe_ = Pipeline([("sc", StandardScaler()),
                               ("lr", LogisticRegression(C=self.C, max_iter=5000))])
        self.pipe_.fit(self._x(X), np.asarray(y))
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return self.pipe_.predict_proba(self._x(X))[:, 1]

    def coefficients(self) -> pd.DataFrame:
        coef = self.pipe_.named_steps["lr"].coef_[0]
        return (pd.DataFrame({"term": self.cols, "standardised_log_odds": coef})
                .sort_values("standardised_log_odds", key=np.abs, ascending=False))


def _fit(name: str, params: dict, train: pd.DataFrame, test: pd.DataFrame):
    if name == "within_between_logistic":
        m = WithinBetweenLogistic(params["C"]).fit(train, train["y"].to_numpy())
        p = m.predict_proba(test)
        return m, p, p
    col = {"two_level_rank": "x2_score", "rule_plus_rounds": "x3_score"}[name]
    m = SingleScoreModel(col).fit(train, train["y"].to_numpy())
    return m, m.predict_proba(test), m.rank_score(test)


def run_exploratory(n_boot: int = 1000) -> pd.DataFrame:
    proto, frames = load_frames()
    OUT.mkdir(parents=True, exist_ok=True)
    feat = add_exploratory_columns(frames["P"])
    names = list(LABELS)
    # ---- development: rolling origin, same folds as the pre-specified models ----------
    folds = list(rolling_origin_folds(feat, proto, 1))
    val_idx = np.concatenate([v for _, _, v in folds])
    y_val = feat["y"].to_numpy()[val_idx]
    oof = feat.iloc[val_idx][["iu_key", "iso2", "country", "year", "y",
                              "covid_stress_year"]].copy()
    selected, log = {}, []
    for name in names:
        grid = [{"C": c} for c in C_GRID] if name == "within_between_logistic" else [{}]
        best = None
        for params in grid:
            p, r = np.full(len(feat), np.nan), np.full(len(feat), np.nan)
            for _, tr, va in folds:
                _, p[va], r[va] = _fit(name, params, feat.iloc[tr], feat.iloc[va])
            loss = log_loss(y_val, p[val_idx])
            log.append({"model": name, "params": json.dumps(params), "pooled_log_loss": loss})
            if best is None or loss < best[0]:
                best = (loss, params, p[val_idx], r[val_idx])
        selected[name] = {"params": best[1], "pooled_log_loss": best[0]}
        oof[f"p_{name}"], oof[f"r_{name}"] = best[2], best[3]
    pd.DataFrame(log).to_csv(OUT / "grid_search_log.csv", index=False)
    (OUT / "selected_configs.json").write_text(json.dumps(selected, indent=2), "utf-8")
    ref_oof = pd.read_parquet(paths.PROCESSED / "predictions_development_oof.parquet")
    ref_oof = ref_oof[ref_oof["scenario"] == "P"][
        ["iu_key", "year"] + [f"{k}_{m}" for m in REFERENCE for k in ("p", "r")]]
    oof = oof.merge(ref_oof, on=["iu_key", "year"], how="left").reset_index(drop=True)
    everything = REFERENCE + names
    rank_cols = {m: f"r_{m}" for m in everything}
    rows, ci_rows, diff_rows = [], [], []
    dev_sets = {"development folds 2019-2022": oof,
                "development folds, non-COVID (2019, 2022)": oof[~oof["covid_stress_year"]]}
    # ---- held-out years: fit once on development, exactly as the main pipeline -------
    tr = final_training_index(feat, proto, 1)
    held = feat.iloc[held_out_index(feat, proto)]
    held = held[held["eligible_primary"] & held["y"].notna()].copy()
    for name in names:
        model, p, r = _fit(name, selected[name]["params"], feat.iloc[tr], held)
        held[f"p_{name}"], held[f"r_{name}"] = p, r
        if name == "within_between_logistic":
            model.coefficients().to_csv(OUT / "coefficients_within_between.csv", index=False)
    ref_held = pd.read_parquet(paths.PROCESSED / "predictions_heldout.parquet")
    ref_held = ref_held[ref_held["scenario"] == "P"][
        ["iu_key", "year"] + [f"{k}_{m}" for m in REFERENCE for k in ("praw", "r")]]
    ref_held = ref_held.rename(columns={f"praw_{m}": f"p_{m}" for m in REFERENCE})
    held = held.merge(ref_held, on=["iu_key", "year"], how="left")
    held_sets = {"locked test 2023-2024 (already opened; NOT an independent test)":
                 held[held["window"] == "locked_test"],
                 "2025 stress year (already seen)": held[held["window"] == "shock_stress_2025"]}
    for label, d in (dev_sets | held_sets).items():
        d = d.reset_index(drop=True)
        pe = point_estimates(d, everything, rank_cols)
        pe.insert(0, "evaluation", label)
        rows.append(pe)
        ci, diffs = cluster_bootstrap(d, everything, "history_rule", rank_cols, n_boot,
                                      proto["seed"])
        for t, store in ((ci, ci_rows), (diffs, diff_rows)):
            t.insert(0, "evaluation", label)
            store.append(t)
    metrics = pd.concat(rows)
    metrics["status"] = "EXPLORATORY POST HOC"
    metrics.to_csv(OUT / "exploratory_metrics.csv", index=False)
    pd.concat(ci_rows).to_csv(OUT / "exploratory_intervals.csv", index=False)
    pd.concat(diff_rows).to_csv(OUT / "exploratory_differences_vs_rule.csv", index=False)
    keep = ["iu_key", "iso2", "country", "year", "y", "window"] + \
           [f"{k}_{m}" for m in names for k in ("p", "r")]
    held[keep].to_parquet(paths.PROCESSED / "predictions_exploratory_heldout.parquet",
                          index=False)
    (OUT / "README.md").write_text(__doc__.strip() + "\n", encoding="utf-8")
    write_run_manifest("exploratory_posthoc", {"n_boot": n_boot, "models": names,
                                               "predictions_digest": frame_digest(held[keep])})
    return metrics
