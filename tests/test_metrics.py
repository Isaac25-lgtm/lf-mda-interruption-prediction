"""Scorer correctness on toy labels with known answers."""
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import average_precision_score, roc_auc_score

from lf_mda.calibrate import PlattCalibrator
from lf_mda.evaluate import (
    all_metrics,
    auroc,
    brier,
    calibration_intercept,
    calibration_slope,
    capture_at,
    log_loss,
    observed_expected,
    pr_auc,
    precision_at,
    stratified_auroc,
    top_k_counts,
)
from lf_mda.uncertainty import cluster_bootstrap, country_jackknife, point_estimates


def test_auroc_known_values():
    y = [0, 0, 1, 1]
    assert auroc(y, [0.1, 0.2, 0.8, 0.9]) == 1.0
    assert auroc(y, [0.9, 0.8, 0.2, 0.1]) == 0.0
    assert auroc(y, [0.5, 0.5, 0.5, 0.5]) == 0.5
    assert np.isnan(auroc([1, 1, 1], [0.1, 0.2, 0.3]))        # one class: undefined


def test_auroc_and_pr_auc_match_scikit_learn():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 500)
    s = np.round(rng.random(500) + 0.3 * y, 2)                # includes ties
    assert auroc(y, s) == pytest.approx(roc_auc_score(y, s))
    assert pr_auc(y, s) == pytest.approx(average_precision_score(y, s))


def test_brier_and_log_loss():
    assert brier([1, 0], [1, 0]) == 0
    assert brier([1, 0], [0.5, 0.5]) == 0.25
    assert log_loss([1, 0], [0.5, 0.5]) == pytest.approx(np.log(2))


def test_calibration_of_a_perfectly_calibrated_model():
    rng = np.random.default_rng(1)
    p = rng.uniform(0.05, 0.95, 20000)
    y = (rng.random(20000) < p).astype(float)
    assert calibration_intercept(y, p) == pytest.approx(0, abs=0.06)
    assert calibration_slope(y, p) == pytest.approx(1, abs=0.06)
    assert observed_expected(y, p) == pytest.approx(1, abs=0.03)


def test_calibration_detects_overconfidence_and_overprediction():
    rng = np.random.default_rng(2)
    p_true = rng.uniform(0.05, 0.95, 20000)
    y = (rng.random(20000) < p_true).astype(float)
    logit = np.log(p_true / (1 - p_true))
    overconfident = 1 / (1 + np.exp(-2 * logit))
    assert calibration_slope(y, overconfident) == pytest.approx(0.5, abs=0.05)
    too_high = 1 / (1 + np.exp(-(logit + 1)))
    assert calibration_intercept(y, too_high) == pytest.approx(-1, abs=0.08)


def test_top_k_without_ties():
    y = [1, 0, 1, 0, 0, 0, 0, 0, 0, 1]
    s = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    assert top_k_counts(y, s, 0.2) == (1.0, 2.0)
    assert capture_at(y, s, 0.2) == pytest.approx(1 / 3)
    assert precision_at(y, s, 0.2) == 0.5
    assert capture_at(y, s, 1.0) == 1.0


def test_top_k_tie_policy_is_expected_value():
    """All ten units tied, 4 events, capacity 20%: expect 2 selected x 40% = 0.8 events."""
    y = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
    tp, k = top_k_counts(y, [3.0] * 10, 0.2)
    assert (tp, k) == (pytest.approx(0.8), 2.0)
    assert capture_at(y, [3.0] * 10, 0.2) == pytest.approx(0.2)   # no better than chance
    # result must not depend on the order of the rows
    assert capture_at(y[::-1], [3.0] * 10, 0.2) == pytest.approx(0.2)


def test_stratified_auroc_ignores_between_stratum_differences():
    # Score separates the two strata perfectly but is uninformative inside each.
    y = np.array([1, 1, 1, 0, 0, 0, 0, 1])
    strata = np.array(["a"] * 4 + ["b"] * 4)
    score = np.array([5, 5, 5, 5, 1, 1, 1, 1])
    assert auroc(y, score) > 0.5
    assert stratified_auroc(y, score, strata) == 0.5
    assert np.isnan(stratified_auroc([1, 1, 0, 0], [1, 2, 3, 4], ["a", "a", "b", "b"]))


def test_platt_calibrator_is_monotone_and_round_trips():
    rng = np.random.default_rng(3)
    p = rng.uniform(0.01, 0.99, 2000)
    y = (rng.random(2000) < p ** 2).astype(int)
    cal = PlattCalibrator().fit(p, y)
    grid = np.linspace(0.01, 0.99, 50)
    assert cal.slope_ > 0 and np.all(np.diff(cal.transform(grid)) > 0)
    restored = PlattCalibrator.from_dict(cal.to_dict())
    np.testing.assert_allclose(restored.apply(grid), cal.transform(grid), rtol=1e-9)
    assert abs(calibration_intercept(y, cal.transform(p))) < 0.1


def _toy_predictions(seed=0, n_countries=6) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for c in range(n_countries):
        for year in (2023, 2024):
            base = rng.uniform(0.05, 0.6)
            for _ in range(40):
                x = rng.normal()
                p = 1 / (1 + np.exp(-(np.log(base / (1 - base)) + x)))
                rows.append({"iso2": f"C{c}", "year": year, "y": float(rng.random() < p),
                             "p_good": p, "p_bad": rng.uniform(0.1, 0.9)})
    return pd.DataFrame(rows)


def test_cluster_bootstrap_is_reproducible_and_brackets_the_estimate():
    df = _toy_predictions()
    a, da = cluster_bootstrap(df, ["good", "bad"], "bad", n_boot=200, seed=7)
    b, _ = cluster_bootstrap(df, ["good", "bad"], "bad", n_boot=200, seed=7)
    pd.testing.assert_frame_equal(a, b)
    row = a[(a["model"] == "good") & (a["metric"] == "auroc")].iloc[0]
    assert row["ci_low"] <= row["estimate"] <= row["ci_high"]
    assert row["n_clusters"] == 6
    d = da[(da["model"] == "good") & (da["metric"] == "auroc")].iloc[0]
    assert d["difference"] > 0 and d["interval_excludes_zero"]


def test_country_jackknife_drops_each_country_once():
    df = _toy_predictions()
    jk = country_jackknife(df, ["good"])
    assert sorted(jk["dropped_country"]) == sorted(df["iso2"].unique())
    assert (jk["dropped_n"] == 80).all()


def test_point_estimates_report_prevalence_with_pr_auc():
    df = _toy_predictions()
    pe = point_estimates(df, ["good"]).iloc[0]
    assert pe["n"] == len(df) and pe["events"] == df["y"].sum()
    assert pe["prevalence"] == pytest.approx(df["y"].mean())
    m = all_metrics(df["y"], df["p_good"], strata=df["iso2"] + df["year"].astype(str))
    assert 0 <= m["within_country_year_auroc"] <= 1
