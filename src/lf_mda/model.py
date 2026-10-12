"""Model registry: baselines, penalised logistic regression and one gradient-boosted model.

The set is deliberately small and fixed in config/protocol.yaml. All preprocessing
(imputation, scaling, encoding) lives inside the fitted object, so it is learned from
training rows only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .baselines import PrevalenceModel, SingleScoreModel
from .features import categorical_features, feature_names


@dataclass
class ModelSpec:
    name: str
    kind: str                      # prevalence | score | logistic | catboost
    groups: list[str] = field(default_factory=list)
    score_column: str | None = None
    label: str = ""
    features: list[str] | None = None   # explicit predictor list; overrides `groups`


SPECS = [
    ModelSpec("prevalence", "prevalence", label="No-skill prevalence"),
    ModelSpec("country_prior_rate", "score", score_column="c_nd_rate_recent_full",
              label="Country prior-year non-delivery rate"),
    ModelSpec("history_rule", "score", score_column="rule_score", label="Fixed history rule"),
    ModelSpec("logistic_iu_only", "logistic", ["history"],
              label="Logistic, IU history only"),
    # Added in refinement round 1 (docs/DECISIONS.md, A3): five predictors only.
    ModelSpec("logistic_parsimonious", "logistic", label="Logistic, five predictors",
              features=["h_nd_count_3", "h_cum_mda", "h_epi_cov_last_round",
                        "a_nd_rate_recent", "c_nd_rate_recent"]),
    ModelSpec("logistic_history", "logistic", ["history", "country"],
              label="Logistic, programme history"),
    ModelSpec("logistic_history_context", "logistic", ["history", "country", "context"],
              label="Logistic, history + context"),
    ModelSpec("catboost_history", "catboost", ["history", "country"],
              label="CatBoost, programme history"),
    ModelSpec("catboost_history_context", "catboost", ["history", "country", "context"],
              label="CatBoost, history + context"),
    ModelSpec("catboost_history_country_id", "catboost", ["history", "country", "identity"],
              label="CatBoost, history + country identity"),
]
SPEC_BY_NAME = {s.name: s for s in SPECS}


def grid_for(spec: ModelSpec, proto: dict) -> list[dict]:
    m = proto["models"]
    if spec.kind == "logistic":
        return [{"C": c} for c in m["logistic_grid"]["C"]]
    if spec.kind == "catboost":
        g = m["catboost_grid"]
        return [{"depth": d, "l2_leaf_reg": l2} for d, l2 in product(g["depth"], g["l2_leaf_reg"])]
    return [{}]


class LogisticModel:
    def __init__(self, features: list[str], cat: list[str], C: float):
        self.features, self.cat, self.C = features, cat, C
        self.num = [f for f in features if f not in cat]

    def fit(self, X: pd.DataFrame, y) -> "LogisticModel":
        pre = ColumnTransformer([
            ("num", Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)),
                              ("sc", StandardScaler())]), self.num),
            ("cat", OneHotEncoder(handle_unknown="ignore"), self.cat),
        ])
        self.pipe_ = Pipeline([("pre", pre),
                               ("lr", LogisticRegression(C=self.C, max_iter=5000))])
        self.pipe_.fit(X[self.features], np.asarray(y))
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return self.pipe_.predict_proba(X[self.features])[:, 1]

    def coefficients(self) -> pd.DataFrame:
        names = self.pipe_.named_steps["pre"].get_feature_names_out()
        coef = self.pipe_.named_steps["lr"].coef_[0]
        out = pd.DataFrame({"term": names, "standardised_log_odds": coef})
        out["odds_ratio_per_sd"] = np.exp(out["standardised_log_odds"])
        return out.sort_values("standardised_log_odds", key=np.abs, ascending=False)


class CatBoostModel:
    def __init__(self, features: list[str], cat: list[str], depth: int, l2_leaf_reg: float,
                 fixed: dict):
        self.features, self.cat = features, cat
        self.params = dict(depth=depth, l2_leaf_reg=l2_leaf_reg, **fixed)

    def _prep(self, X: pd.DataFrame) -> pd.DataFrame:
        Z = X[self.features].copy()
        for c in self.cat:
            Z[c] = Z[c].fillna("none").astype(str)
        return Z

    def fit(self, X: pd.DataFrame, y) -> "CatBoostModel":
        from catboost import CatBoostClassifier
        self.model_ = CatBoostClassifier(
            loss_function="Logloss", verbose=0, allow_writing_files=False, thread_count=4,
            cat_features=self.cat, **self.params)
        self.model_.fit(self._prep(X), np.asarray(y))
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return self.model_.predict_proba(self._prep(X))[:, 1]

    def shap_importance(self, X: pd.DataFrame) -> pd.DataFrame:
        from catboost import Pool
        pool = Pool(self._prep(X), cat_features=self.cat)
        sv = self.model_.get_feature_importance(pool, type="ShapValues")[:, :-1]
        return (pd.DataFrame({"feature": self.features,
                              "mean_abs_shap_log_odds": np.abs(sv).mean(axis=0)})
                .sort_values("mean_abs_shap_log_odds", ascending=False))


def build_model(spec: ModelSpec, params: dict, proto: dict, manifest: dict | None = None):
    if spec.kind == "prevalence":
        return PrevalenceModel()
    if spec.kind == "score":
        return SingleScoreModel(spec.score_column)
    feats = spec.features or feature_names(spec.groups, manifest)
    feats = [f for f in feats if f != "c_nd_rate_recent_full"]  # baseline-only column
    cat = categorical_features(feats, manifest)
    if spec.kind == "logistic":
        return LogisticModel(feats, cat, params["C"])
    if spec.kind == "catboost":
        return CatBoostModel(feats, cat, params["depth"], params["l2_leaf_reg"],
                             proto["models"]["catboost_fixed"])
    raise ValueError(f"unknown model kind {spec.kind}")


def rank_score(model, X: pd.DataFrame, p: np.ndarray) -> np.ndarray:
    """Score used to rank units: the raw rule/prior score for baselines, else p."""
    return model.rank_score(X) if hasattr(model, "rank_score") else p
