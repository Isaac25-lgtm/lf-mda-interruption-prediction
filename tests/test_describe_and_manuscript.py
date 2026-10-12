"""Descriptive analyses on SYNTHETIC panels, and consistency of the manuscript template."""
import re
import string

import pytest
from conftest import panel_from_patterns

from lf_mda import paths
from lf_mda.describe import (
    burden_by_year,
    country_persistence,
    level_by_year,
    recovery,
    repeat_interruptions,
)


def test_burden_counts_population_of_interrupted_units_only():
    panel = panel_from_patterns({("XA", 1): "mmmNmmmmmmmm", ("XA", 2): "mmmmmmmmmmmm"})
    b = burden_by_year(panel)
    r = b[(b["cohort"] == "primary") & (b["year"] == 2017)].iloc[0]
    assert r["eligible_ius"] == 2 and r["interrupted_ius"] == 1
    pop_2017 = 100000 + 1000 * 3                       # synthetic population in 2017
    assert r["population_in_interrupted_ius_millions"] == pytest.approx(pop_2017 / 1e6)
    assert r["share_population_in_interrupted_ius"] == pytest.approx(0.5)
    quiet = b[(b["cohort"] == "primary") & (b["year"] == 2019)].iloc[0]
    assert quiet["interrupted_ius"] == 0 and quiet["population_in_interrupted_ius_millions"] == 0


def test_missing_report_adds_nothing_to_the_burden():
    panel = panel_from_patterns({("XA", 1): "mmmRmmmmmmmm", ("XA", 2): "mmmmmmmmmmmm"})
    b = burden_by_year(panel)
    assert b["interrupted_ius"].sum() == 0


def test_recovery_distinguishes_resumption_from_stopping():
    panel = panel_from_patterns({
        ("XA", 1): "mmmNmmmmmmmm",     # resumes after 1 year
        ("XA", 2): "mmmNNNmmmmmm",     # resumes after 3 years
        ("XA", 3): "mmmNPPPPPPPP",     # moves to surveillance: not a resumption
        ("XA", 4): "mmmmmmmmmmNN",     # still not delivered when data end
    })
    summ, within = recovery(panel)
    pre = summ[summ["era"] == "2016-2019"].iloc[0]
    assert pre["interruption_onsets"] == 3
    assert pre["resumed_MDA"] == 2 and pre["moved_to_assessment_or_surveillance"] == 1
    w = within.set_index(["era", "years_since_onset"])
    assert w.loc[("2016-2019", 1), "share_resumed"] == pytest.approx(1 / 3)
    assert w.loc[("2016-2019", 3), "share_resumed"] == pytest.approx(2 / 3)
    late = summ[summ["era"] == "2022-2024"].iloc[0]
    assert late["still_not_delivered_at_end_of_data"] == 1 and late["resumed_MDA"] == 0


def test_recovery_only_counts_onsets_that_could_be_followed():
    """An onset in 2024 has one year of follow-up; it must not count against 3-year recovery."""
    panel = panel_from_patterns({("XA", 1): "mmmmmmmmmmNm", ("XA", 2): "mmmmmmmmNmmm"})
    _, within = recovery(panel)
    w = within.set_index(["era", "years_since_onset"])
    assert w.loc[("2022-2024", 1), "onsets_with_follow_up"] == 2
    assert w.loc[("2022-2024", 3), "onsets_with_follow_up"] == 1


def test_level_separates_country_wide_from_local_failures():
    patterns = {("XA", i): "mmmNmmmmmmmm" for i in range(1, 5)}             # all miss 2017
    patterns |= {("XB", 1): "mmmNmmmmmmmm"} | {("XB", i): "m" * 12 for i in range(2, 6)}
    t = level_by_year(panel_from_patterns(patterns)).set_index("year")
    assert t.loc[2017, "events_where_every_IU_missed"] == 4
    assert t.loc[2017, "events_where_half_or_fewer_IUs_missed"] == 1
    assert t.loc[2017, "share_where_every_IU_missed"] == pytest.approx(0.8)


def test_repeat_interruptions_shares_sum_to_one():
    panel = panel_from_patterns({("XA", 1): "mmmNmmNmmmmm", ("XA", 2): "mmmNmmmmmmmm",
                                 ("XA", 3): "m" * 12})
    rep = repeat_interruptions(panel).set_index("interrupted_years")
    assert rep["share_of_ius"].sum() == pytest.approx(1)
    assert rep["share_of_all_interruptions"].sum() == pytest.approx(1)
    assert rep.loc[2, "ius"] == 1 and rep.loc[2, "share_of_all_interruptions"] == pytest.approx(2 / 3)


def test_country_persistence_runs_on_small_panels():
    patterns = {(c, i): ("mmmNNmmmmmmm" if c == "XA" else "m" * 12)
                for c in ("XA", "XB") for i in range(1, 7)}
    tab, stats = country_persistence(panel_from_patterns(patterns), min_ius=5)
    assert stats["country_year_pairs"] > 0
    assert set(tab.columns) >= {"majority_prev", "country_years", "share"}


# ---- manuscript template -----------------------------------------------------------------
TEMPLATE = paths.ROOT / "manuscript" / "manuscript_template.md"


def _placeholders() -> set[str]:
    text = TEMPLATE.read_text(encoding="utf-8")
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def test_template_contains_no_hand_typed_result_numbers_in_findings():
    """The abstract's findings must be built from placeholders, not typed figures."""
    text = TEMPLATE.read_text(encoding="utf-8")
    findings = text.split("**Findings.**")[1].split("**Conclusions.**")[0]
    stripped = re.sub(r"\{[a-zA-Z0-9_]+\}", "", findings)
    stripped = re.sub(r"20[12]\d(-20[12]\d)?", "", stripped)        # calendar years are fine
    stripped = stripped.replace("20% capacity", "")
    assert not re.search(r"\d", stripped), re.findall(r"[^.]*\d[^.]*", stripped)


def test_template_declares_the_proxy_label_and_open_items():
    text = " ".join(TEMPLATE.read_text(encoding="utf-8").split())
    assert "has not been independently verified" in text
    assert "[citation needed" in text and "[to do" in text


results_present = pytest.mark.skipif(
    not (paths.EVALUATION / "locked_test" / "LOCK.json").exists()
    or not (paths.PROCESSED / "panel.parquet").exists(),
    reason="result files not present")


@results_present
def test_every_placeholder_has_a_value_from_result_files():
    from lf_mda.manuscript import build_facts
    facts = build_facts()
    missing = _placeholders() - set(facts)
    assert not missing, f"placeholders with no value: {sorted(missing)}"
    assert all(isinstance(v, str) and v and "nan" not in v.lower() for v in facts.values()), \
        {k: v for k, v in facts.items() if "nan" in str(v).lower()}
