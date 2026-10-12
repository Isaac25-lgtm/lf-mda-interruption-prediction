"""Probability recalibration fitted only on out-of-fold, time-forward predictions."""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression

from .evaluate import _logit


class PlattCalibrator:
    """Logistic recalibration p' = sigmoid(a + b * logit(p)). Monotone when b > 0."""

    def fit(self, p, y) -> PlattCalibrator:
        self.model_ = LogisticRegression(C=1e6, max_iter=1000).fit(
            _logit(p).reshape(-1, 1), np.asarray(y))
        self.intercept_ = float(self.model_.intercept_[0])
        self.slope_ = float(self.model_.coef_[0, 0])
        return self

    def transform(self, p) -> np.ndarray:
        return self.model_.predict_proba(_logit(p).reshape(-1, 1))[:, 1]

    def to_dict(self) -> dict:
        return {"intercept": self.intercept_, "slope": self.slope_}

    @classmethod
    def from_dict(cls, d: dict) -> PlattCalibrator:
        obj = cls()
        obj.intercept_, obj.slope_ = d["intercept"], d["slope"]
        obj.model_ = None
        return obj

    def apply(self, p) -> np.ndarray:
        """Transform using stored coefficients (no scikit-learn object needed)."""
        z = self.intercept_ + self.slope_ * _logit(p)
        return 1 / (1 + np.exp(-z))
