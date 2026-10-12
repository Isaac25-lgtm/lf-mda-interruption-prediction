"""Splits are time-forward or country-blocked; training never sees the evaluated period."""
import numpy as np
import pandas as pd
import pytest

from lf_mda.labels import load_protocol
from lf_mda.splits import (
    SplitError,
    assert_time_forward,
    final_training_index,
    held_out_index,
    leave_one_country_out,
    rolling_origin_folds,
)


@pytest.fixture
def feat() -> pd.DataFrame:
    rng = np.random.default_rng(1)
    rows = [{"iu_key": f"{c}-{i}", "iso2": c, "year": y, "y": float(rng.integers(0, 2)),
             "eligible_primary": True}
            for c in ("XA", "XB", "XC") for i in range(5) for y in range(2016, 2026)]
    return pd.DataFrame(rows)


def test_time_forward_assertion():
    assert_time_forward([2016, 2017, 2018], [2019], label_lag=1)
    with pytest.raises(SplitError):
        assert_time_forward([2016, 2019], [2019], label_lag=1)
    with pytest.raises(SplitError):
        assert_time_forward([2016, 2018], [2019], label_lag=2)     # public-data lag
    with pytest.raises(SplitError):
        assert_time_forward([], [2019], label_lag=1)


def test_rolling_folds_train_strictly_before_validation(feat):
    proto = load_protocol()
    for lag in (1, 2):
        folds = list(rolling_origin_folds(feat, proto, lag))
        assert [f[0] for f in folds] == proto["windows"]["rolling_validation_years"]
        for year, tr, va in folds:
            assert feat.iloc[tr]["year"].max() <= year - lag
            assert set(feat.iloc[va]["year"]) == {year}
            assert not set(tr) & set(va)


def test_final_training_never_touches_held_out_years(feat):
    proto = load_protocol()
    lo, hi = proto["windows"]["locked_test"]
    for lag in (1, 2):
        tr = feat.iloc[final_training_index(feat, proto, lag)]
        assert tr["year"].max() <= lo - lag
    held = feat.iloc[held_out_index(feat, proto)]
    assert set(held["year"]) == set(range(lo, hi + 1)) | set(proto["windows"]["shock_stress_test"])
    assert not set(final_training_index(feat, proto, 1)) & set(held_out_index(feat, proto))


def test_shuffled_timestamps_break_the_split_guard(feat):
    """Adversarial: if years are scrambled so a 'training' row is from the future, fail."""
    with pytest.raises(SplitError):
        assert_time_forward(np.array([2016, 2017, 2024]), np.array([2023, 2024]), 1)


def test_unlabelled_rows_are_never_used_for_training(feat):
    proto = load_protocol()
    feat.loc[feat["year"] == 2018, "y"] = np.nan
    for _, tr, _ in rolling_origin_folds(feat, proto, 1):
        assert feat.iloc[tr]["y"].notna().all()


def test_leave_one_country_out_is_disjoint_by_country(feat):
    proto = load_protocol()
    seen = []
    for iso2, tr, te in leave_one_country_out(feat, proto):
        assert set(feat.iloc[te]["iso2"]) == {iso2}
        assert iso2 not in set(feat.iloc[tr]["iso2"])
        assert feat.iloc[te]["year"].between(*proto["windows"]["development"]).all()
        seen.append(iso2)
    assert seen == ["XA", "XB", "XC"]


def test_protocol_windows_do_not_overlap():
    w = load_protocol()["windows"]
    dev = set(range(w["development"][0], w["development"][1] + 1))
    test = set(range(w["locked_test"][0], w["locked_test"][1] + 1))
    stress = set(w["shock_stress_test"])
    assert not dev & test and not dev & stress and not test & stress
    assert set(w["rolling_validation_years"]) <= dev
    assert max(dev) < min(test) < min(stress)
