"""A missing report or a missing row is a missing label, never an interruption."""
import numpy as np
from conftest import panel_from_patterns, raw_from_patterns

from lf_mda.ingest import coerce_numeric
from lf_mda.labels import analysis_set


def test_not_reported_year_has_no_label(cell):
    r = cell("XA", 4, 2016)
    assert r["eligible_primary"]
    assert r["outcome_class"] == "missing_JRF" and np.isnan(r["y"])


def test_absent_row_has_no_label(cell):
    r = cell("XA", 5, 2016)
    assert not r["row_present"] and r["gap_type"] == "internal_gap"
    assert r["eligible_primary"]
    assert r["outcome_class"] == "missing_iu_year" and np.isnan(r["y"])


def test_missing_labels_are_absent_from_the_analysis_set(panel):
    a = analysis_set(panel, "primary")
    assert a["y"].isin([0.0, 1.0]).all()
    assert not a["outcome_class"].isin(["missing_JRF", "missing_iu_year"]).any()


def test_adding_a_not_reported_year_never_adds_an_event():
    """Adversarial: replace a delivered year by 'Not reported'; event count must not rise."""
    base = panel_from_patterns({("XA", 1): "mmmmmmmmmmmm"})
    pert = panel_from_patterns({("XA", 1): "mmmmmRmmmmmm"})
    assert pert["y"].eq(1).sum() == base["y"].eq(1).sum() == 0
    assert pert["y"].notna().sum() < base["y"].notna().sum()


def test_removing_a_country_year_never_adds_an_event():
    base = panel_from_patterns({("XA", 1): "mmmNmmmmmmmm", ("XA", 2): "mmmmmmmmmmmm"})
    pert = panel_from_patterns({("XA", 1): "mmmNmm-mmmmm", ("XA", 2): "mmmmmm-mmmmm"})
    assert pert["y"].eq(1).sum() <= base["y"].eq(1).sum()


def test_blank_numeric_is_missing_not_zero():
    raw = raw_from_patterns({("XA", 1): "MMM---------"})
    raw.loc[0, "popTreat"] = ""
    raw.loc[1, "popTreat"] = "0"
    raw.loc[2, "popTreat"] = "not-a-number"
    typed, diag = coerce_numeric(raw)
    assert np.isnan(typed.loc[0, "popTreat"]) and typed.loc[1, "popTreat"] == 0
    d = diag.set_index("column").loc["popTreat"]
    assert d["n_blank"] == 1 and d["n_unparseable"] == 1 and d["n_zero"] == 1
