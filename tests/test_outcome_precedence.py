"""Status mapping, precedence and quarantine of contradictory rows (synthetic data)."""
import numpy as np
import pandas as pd
import pytest

from conftest import panel_from_patterns, raw_from_patterns
from lf_mda.ingest import coerce_numeric
from lf_mda.labels import classify_rows, load_status_map


def _rows(patterns):
    typed, _ = coerce_numeric(raw_from_patterns(patterns))
    return typed


def test_each_status_maps_to_its_class():
    rows = classify_rows(_rows({("XA", 1): "MNPIER------"}))
    got = dict(zip(rows["year"], rows["row_class"]))
    assert got == {2014: "delivered", 2015: "non_delivery", 2016: "surveillance_or_stopped",
                   2017: "legitimate_pause_IA", 2018: "not_endemic", 2019: "missing_JRF"}


def test_unmapped_status_is_unknown_not_positive():
    typed = _rows({("XA", 1): "MMN---------"})
    typed.loc[typed["year"] == 2016, "endemicity"] = "Some new status never seen before"
    rows = classify_rows(typed)
    r = rows[rows["year"] == 2016].iloc[0]
    assert r["row_class"] == "unknown" and r["status_code"] == "UNMAPPED"
    assert not r["status_mapped"]


def test_non_delivery_with_treatment_is_quarantined():
    typed = _rows({("XA", 1): "MMN---------"})
    typed.loc[typed["year"] == 2016, "popTreat"] = 5000
    rows = classify_rows(typed)
    r = rows[rows["year"] == 2016].iloc[0]
    assert r["row_class"] == "contradictory"
    assert r["contradiction"] == "non_delivery_but_treatment_recorded"


def test_delivered_without_treatment_is_quarantined():
    typed = _rows({("XA", 1): "MMM---------"})
    typed.loc[typed["year"] == 2016, ["popTreat", "mda"]] = 0
    rows = classify_rows(typed)
    assert rows[rows["year"] == 2016].iloc[0]["row_class"] == "contradictory"


def test_contradictory_outcome_never_becomes_a_label():
    raw = raw_from_patterns({("XA", 1): "mmmNmmmmmmmm"})
    raw.loc[raw["year"] == "2017", "popTreat"] = "5000"
    typed, _ = coerce_numeric(raw)
    from lf_mda.labels import build_panel
    panel = build_panel(classify_rows(typed))
    r = panel[panel["year"] == 2017].iloc[0]
    assert r["outcome_class"] == "contradictory" and np.isnan(r["y"])


def test_duplicate_iu_year_rows_fail_loudly():
    typed = _rows({("XA", 1): "MMM---------"})
    with pytest.raises(ValueError, match="duplicated IU-year"):
        classify_rows(pd.concat([typed, typed.iloc[[0]]]))


def test_inverting_the_status_map_changes_every_label():
    """Adversarial: swapping delivered and non-delivery must flip outcomes, not pass silently."""
    typed = _rows({("XA", 1): "mmmNmmmNmmmm"})
    smap = load_status_map()
    inverted = smap.copy()
    swap = {"delivered": "non_delivery", "non_delivery": "delivered"}
    inverted["row_class"] = inverted["row_class"].replace(swap)
    a = classify_rows(typed, smap)["row_class"]
    b = classify_rows(typed, inverted)["row_class"]
    assert (a != b).all()


def test_status_map_rejects_unknown_class(tmp_path):
    smap = load_status_map()
    smap.loc[0, "row_class"] = "made_up_class"
    path = tmp_path / "map.csv"
    smap.to_csv(path, index=False)
    with pytest.raises(ValueError, match="unknown row classes"):
        load_status_map(path)


def test_never_started_is_outside_the_cohort(panel, cell):
    for year in range(2016, 2026):
        r = cell("XA", 6, year)
        assert not r["eligible_broad"]
        assert r["lifecycle_class"] == "never_started"


def test_legitimate_stop_after_five_effective_rounds_is_not_an_event(cell):
    r = cell("XA", 3, 2019)                      # non-delivery after 5 effective rounds
    assert r["eligible_broad"] and not r["eligible_primary"]
    assert cell("XA", 3, 2020)["outcome_class"] == "surveillance_or_stopped"


def test_pending_ia_is_excluded_from_the_binary_outcome(cell):
    r = cell("XA", 7, 2021)
    assert r["eligible_primary"] and r["outcome_class"] == "legitimate_pause_IA"
    assert np.isnan(r["y"])


def test_interruption_in_active_programme_is_an_event(cell):
    r = cell("XA", 2, 2017)
    assert r["eligible_primary"] and r["y"] == 1.0
    assert r["outcome_class"] == "reported_interruption"
    assert r["hs_group"] == "resumed_mda"
    assert panel_from_patterns({("XA", 2): "mmmNmmmNNmmm"})["y"].eq(1).sum() == 3
