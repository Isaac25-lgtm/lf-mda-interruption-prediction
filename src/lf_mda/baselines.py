"""Explicit baselines that every model must be compared against."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression


class PrevalenceModel:
    """No-skill baseline: every unit gets the training prevalence."""

    def fit(self, X: pd.DataFrame, y) -> "PrevalenceModel":
        self.p_ = float(np.mean(y))
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return np.full(len(X), self.p_)


class SingleScoreModel:
    """Maps one pre-computed score to a probability with a one-variable logistic model.

    Used for the fixed history rule (`rule_score`) and the country prior rate
    (`c_nd_rate_recent_full`). The score defines the ranking; the logistic fit only
    supplies probabilities so calibration can be assessed on the same footing as models.
    """

    def __init__(self, column: str):
        self.column = column

    def _x(self, X: pd.DataFrame) -> np.ndarray:
        return X[self.column].fillna(self.fill_).to_numpy(dtype=float).reshape(-1, 1)

    def fit(self, X: pd.DataFrame, y) -> "SingleScoreModel":
        self.fill_ = float(X[self.column].median())
        self.model_ = LogisticRegression(C=1e6, max_iter=1000).fit(self._x(X), np.asarray(y))
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return self.model_.predict_proba(self._x(X))[:, 1]

    def rank_score(self, X: pd.DataFrame) -> np.ndarray:
        return X[self.column].fillna(self.fill_).to_numpy(dtype=float)
