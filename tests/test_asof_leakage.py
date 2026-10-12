"""As-of contract: no predictor or eligibility flag may read the outcome year or later."""
import copy

import numpy as np
import pandas as pd
import pytest

import lf_mda.features as F
from conftest import panel_from_patterns
from lf_mda.features import (assert_no_future_dependence, build_features,
                             check_frame_against_manifest, load_manifest, validate_manifest)


def test_real_manifest_is_valid_and_has_no_outcome_year_features():
    man = load_manifest()
    validate_manifest(man)
    assert all(not s["derived_from_outcome_year"] for s in man["features"].values())
    assert all(s["min_lag_years"] >= 1 for s in man["features"].values())


def test_manifest_rejects_outcome_year_feature():
    man = copy.deepcopy(load_manifest())
    man["features"]["h_nd_recent"]["derived_from_outcome_year"] = True
    with pytest.raises(ValueError, match="derived from the outcome year"):
        validate_manifest(man)


def test_manifest_rejects_zero_lag():
    man = copy.deepcopy(load_manifest())
    man["features"]["h_cum_mda"]["min_lag_years"] = 0
    with pytest.raises(ValueError, match="future leakage"):
        validate_manifest(man)


def test_info_lag_zero_is_refused(panel):
    with pytest.raises(ValueError, match="info_lag must be >= 1"):
        build_features(panel, info_lag=0)


def test_features_do_not_change_when_future_rows_are_scrambled(panel):
    for year in (2017, 2020, 2024):
        for lag in (1, 2):
            assert_no_future_dependence(panel, year, lag)


def test_a_deliberately_leaky_feature_is_caught(panel, monkeypatch):
    """Adversarial: inject a predictor built from the outcome year; the check must fail."""
    original = F.build_features

    def leaky(p, info_lag=1, context=None):
        out = original(p, info_lag, context)
        same_year = p[["iu_key", "year", "pop_treat"]].rename(
            columns={"pop_treat": "h_cum_mda"})          # outcome-year treatment count
        return out.drop(columns="h_cum_mda").merge(same_year, on=["iu_key", "year"], how="left")

    monkeypatch.setattr(F, "build_features", leaky)
    with pytest.raises(AssertionError, match="future information leak"):
        F.assert_no_future_dependence(panel, 2020, 1)


def test_undeclared_column_is_rejected(panel):
    feat = build_features(panel, 1)
    feat["sneaky_outcome_year_coverage"] = 1.0
    with pytest.raises(ValueError, match="not declared"):
        check_frame_against_manifest(feat)


def test_out_of_range_value_is_rejected(panel):
    feat = build_features(panel, 1)
    feat.loc[feat.index[0], "h_nd_recent"] = 7
    with pytest.raises(ValueError, match="above valid range"):
        check_frame_against_manifest(feat)


def test_eligibility_ignores_outcome_year_values():
    """Changing only what happened in year t must not change who was eligible for year t."""
    a = panel_from_patterns({("XA", 1): "mmmmmmmmmmmm", ("XA", 2): "mmmNmmmmmmmm"})
    b = panel_from_patterns({("XA", 1): "mmmmmmmmmmmN", ("XA", 2): "mmmNmmmmmmmP"})
    cols = ["eligible_broad", "eligible_primary", "eligible_strict", "eligible_incident"]
    pd.testing.assert_frame_equal(a.loc[a["year"] == 2025, cols].reset_index(drop=True),
                                  b.loc[b["year"] == 2025, cols].reset_index(drop=True))


def test_scenario_e_reads_one_year_older_than_scenario_p(panel):
    p = build_features(panel, 1).set_index(["iu_key", "year"])
    e = build_features(panel, 2).set_index(["iu_key", "year"])
    # XA-2 missed 2017: scenario P sees it when predicting 2018, scenario E only for 2019
    assert p.loc[("XA-2", 2018), "h_nd_recent"] == 1.0
    assert e.loc[("XA-2", 2018), "h_nd_recent"] == 0.0
    assert e.loc[("XA-2", 2019), "h_nd_recent"] == 1.0


def test_country_rate_excludes_the_iu_itself(panel):
    f = build_features(panel, 1).set_index(["iu_key", "year"])
    # In XB only IUs 1 and 2 require MDA. For XB-1 in 2018 the other IU (XB-2) delivered in 2017.
    assert f.loc[("XB-2", 2018), "c_nd_rate_recent"] == 1.0   # sees XB-1's 2017 non-delivery
    assert f.loc[("XB-2", 2018), "c_nd_rate_recent_full"] == 0.5
    assert np.isfinite(f.loc[("XB-2", 2018), "rule_score"])
