"""Lags are joins on (country, IU, year); identifiers never bleed across countries."""
import numpy as np
from conftest import panel_from_patterns


def test_same_iu_id_in_two_countries_stays_separate(panel, cell):
    assert panel["iu_key"].nunique() == 10
    assert cell("XA", 1, 2018)["y"] == 0.0      # XA-1 delivered in 2018
    assert cell("XB", 1, 2018)["y"] == 1.0      # XB-1 did not


def test_lag_skips_no_years_over_a_gap(cell):
    """IU XA-5 has no 2016 row. For target 2017 the t-1 value must be missing, not 2015's."""
    r = cell("XA", 5, 2017)
    assert r["row_class_l1"] == "missing_iu_year"
    assert r["row_class_l2"] == "delivered"
    assert not r["eligible_broad"]              # not known to require MDA at t-1


def test_positional_shift_would_be_wrong_here(panel):
    """Guard against a blind `shift`: the observed-row predecessor of 2017 is 2015."""
    obs = panel[(panel["iu_key"] == "XA-5") & panel["row_present"]].sort_values("year")
    blind = obs["row_class"].shift(1)[obs["year"] == 2017].iloc[0]
    joined = panel[(panel["iu_key"] == "XA-5") & (panel["year"] == 2017)]["row_class_l1"].iloc[0]
    assert blind == "delivered" and joined == "missing_iu_year"


def test_iu_first_seen_late_has_no_history_and_is_not_eligible_at_once():
    panel = panel_from_patterns({("XA", 9): "-----mmmNmmm"})
    first = panel[panel["year"] == 2019].iloc[0]       # first row; no t-1
    assert first["gap_type"] == "" and not first["eligible_broad"]
    assert panel[panel["year"] == 2020].iloc[0]["eligible_broad"]
    assert panel[panel["year"] == 2014].iloc[0]["gap_type"] == "before_first_row"


def test_iu_dissolved_gives_missing_label_not_event():
    panel = panel_from_patterns({("XA", 9): "mmmmmm------"})
    r = panel[panel["year"] == 2020].iloc[0]
    assert r["eligible_primary"] and r["outcome_class"] == "missing_iu_year"
    assert np.isnan(r["y"]) and r["gap_type"] == "after_last_row"


def test_rounds_before_2014_are_constant_within_iu():
    panel = panel_from_patterns({("XA", 1): "mmmNmmmmmmmm"}, pre2014_rounds=6)
    assert set(panel["rounds_before_2014"]) == {6}
    row = panel[panel["year"] == 2018].iloc[0]
    assert row["eligible_primary"] and not row["eligible_strict"]
