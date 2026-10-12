"""Time-forward and country-blocked splits. No random row splits exist in this project."""
from __future__ import annotations

from collections.abc import Iterator

import numpy as np
import pandas as pd


class SplitError(ValueError):
    """Raised when a split would let training see the evaluation period."""


def assert_time_forward(train_years, eval_years, label_lag: int) -> None:
    """Training labels must be at least `label_lag` years older than every evaluated year."""
    train_years, eval_years = np.asarray(train_years), np.asarray(eval_years)
    if len(train_years) == 0:
        raise SplitError("empty training set")
    if train_years.max() > eval_years.min() - label_lag:
        raise SplitError(
            f"training labels reach {train_years.max()} but evaluation starts in "
            f"{eval_years.min()} with label lag {label_lag}")


def usable(feat: pd.DataFrame, cohort: str = "primary") -> pd.Series:
    return feat[f"eligible_{cohort}"] & feat["y"].notna()


def rolling_origin_folds(feat: pd.DataFrame, proto: dict, label_lag: int,
                         cohort: str = "primary") -> Iterator[tuple[int, np.ndarray, np.ndarray]]:
    """Yield (validation year, train index, validation index) within development years."""
    w = proto["windows"]
    dev = feat["year"].between(*w["development"]) & usable(feat, cohort)
    for year in w["rolling_validation_years"]:
        train = dev & (feat["year"] <= year - label_lag)
        val = dev & (feat["year"] == year)
        if train.sum() == 0 or val.sum() == 0:
            continue
        assert_time_forward(feat.loc[train, "year"], feat.loc[val, "year"], label_lag)
        yield year, np.flatnonzero(train.to_numpy()), np.flatnonzero(val.to_numpy())


def final_training_index(feat: pd.DataFrame, proto: dict, label_lag: int,
                         cohort: str = "primary") -> np.ndarray:
    """Development rows whose labels were available at the first locked-test decision."""
    w = proto["windows"]
    first_test = w["locked_test"][0]
    train = (feat["year"].between(*w["development"]) & usable(feat, cohort)
             & (feat["year"] <= first_test - label_lag))
    held_out = np.r_[np.arange(w["locked_test"][0], w["locked_test"][1] + 1),
                     w["shock_stress_test"]]
    assert_time_forward(feat.loc[train, "year"], held_out, label_lag)
    return np.flatnonzero(train.to_numpy())


def held_out_index(feat: pd.DataFrame, proto: dict) -> np.ndarray:
    """All broad-cohort rows in the locked-test and 2025 stress years (with or without y)."""
    w = proto["windows"]
    mask = feat["year"].between(*w["locked_test"]) | feat["year"].isin(w["shock_stress_test"])
    return np.flatnonzero(mask.to_numpy())


def leave_one_country_out(feat: pd.DataFrame, proto: dict, cohort: str = "primary"
                          ) -> Iterator[tuple[str, np.ndarray, np.ndarray]]:
    """Yield (country, train index, test index) on development years only."""
    dev = feat["year"].between(*proto["windows"]["development"]) & usable(feat, cohort)
    for iso2 in sorted(feat.loc[dev, "iso2"].unique()):
        train = dev & (feat["iso2"] != iso2)
        test = dev & (feat["iso2"] == iso2)
        if set(feat.loc[train, "iso2"]) & set(feat.loc[test, "iso2"]):
            raise SplitError("held-out country appears in training data")
        yield iso2, np.flatnonzero(train.to_numpy()), np.flatnonzero(test.to_numpy())
