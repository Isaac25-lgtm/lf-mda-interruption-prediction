"""Fill the manuscript template with numbers read from result files.

`manuscript/manuscript_template.md` holds the prose with `{placeholders}`. This module
builds every placeholder value from the audit, descriptive and evaluation outputs,
writes them to `reports/facts.json`, and renders `manuscript/manuscript_draft.md`.
No number in the draft is typed by hand; a missing placeholder fails loudly.
"""
from __future__ import annotations

import json

import pandas as pd

from . import paths

LOCK = paths.EVALUATION / "locked_test"
DEV = paths.EVALUATION / "development"
LOCO = paths.EVALUATION / "country_transport"
SENS = paths.EVALUATION / "sensitivity"
EXPLO = paths.EVALUATION / "exploratory_posthoc"
DESC = paths.REPORTS / "descriptive"
NAMES = {"history_rule": "the history rule", "logistic_iu_only": "logistic regression on IU history",
         "logistic_parsimonious": "the five-predictor logistic model",
         "logistic_history": "logistic regression on programme history",
         "logistic_history_context": "logistic regression with context",
         "catboost_history": "CatBoost on programme history",
         "catboost_history_context": "CatBoost with context",
         "catboost_history_country_id": "CatBoost with country identity",
         "country_prior_rate": "the country prior-year rate"}


def pct(x: float, d: int = 0) -> str:
    return f"{100 * x:.{d}f}%"


def ci(est: float, lo: float, hi: float, d: int = 2) -> str:
    if pd.isna(est):
        return "not estimable"
    if pd.isna(lo):
        return f"{est:.{d}f}"
    return f"{est:.{d}f} (95% CI {lo:.{d}f} to {hi:.{d}f})"


def ci_pct(est: float, lo: float, hi: float) -> str:
    """A share with its interval, as percentages."""
    if pd.isna(est):
        return "not estimable"
    return f"{100 * est:.0f}% (95% CI {100 * lo:.0f}% to {100 * hi:.0f}%)"


def ci_pp(est: float, lo: float, hi: float) -> str:
    """A difference between two shares, in percentage points."""
    if pd.isna(est):
        return "not estimable"
    return f"{100 * est:+.1f} percentage points (95% CI {100 * lo:+.1f} to {100 * hi:+.1f})"


def _ci_lookup(table: pd.DataFrame, value_col: str = "estimate"):
    def get(model: str, metric: str, d: int = 2, **filters) -> str:
        t = table
        for k, v in filters.items():
            t = t[t[k] == v]
        r = t[(t["model"] == model) & (t["metric"] == metric)].iloc[0]
        if metric.startswith("capture_at"):
            fmt = ci_pp if value_col == "difference" else ci_pct
            return fmt(r[value_col], r["ci_low"], r["ci_high"])
        return ci(r[value_col], r["ci_low"], r["ci_high"], d)
    return get


def build_facts() -> dict:
    gate = json.loads((paths.AUDIT / "gate_decision.json").read_text("utf-8"))
    m = gate["metrics"]
    f: dict[str, str] = {}
    # ---- data and cohort ----
    f["n_rows"] = f"{m['n_raw_rows']:,}"
    f["n_country_files"] = str(m["n_countries"])
    f["n_ius"] = f"{m['n_ius']:,}"
    f["primary_n"] = f"{m['primary_n']:,}"
    f["primary_events"] = f"{m['primary_events']:,}"
    f["primary_prev"] = pct(m["primary_events"] / m["primary_n"], 1)
    f["primary_countries"] = str(m["primary_countries"])
    f["primary_event_countries"] = str(m["primary_event_countries"])
    f["contradiction_pct"] = pct(m["contradiction_share"], 2)
    f["n_not_reported"] = f"{m['n_not_reported_rows']:,}"
    flow = pd.read_csv(paths.AUDIT / "cohort_flow.csv")
    step = dict(zip(flow["step"].str.strip(), flow["n"]))
    f["broad_cells"] = f"{next(v for k, v in step.items() if k.startswith('Broad cohort')):,}"
    f["excluded_rounds"] = f"{next(v for k, v in step.items() if k.startswith('excluded: >=5')):,}"
    f["never_started_excluded"] = \
        f"{next(v for k, v in step.items() if k.startswith('excluded: no delivery')):,}"
    win = pd.read_csv(paths.AUDIT / "events_by_window.csv").set_index(["cohort", "window"])
    f["dev_n"] = f"{int(win.loc[('primary', 'development'), 'n']):,}"
    f["dev_events"] = f"{int(win.loc[('primary', 'development'), 'events']):,}"
    f["test_n"] = str(m["test_n"])
    f["test_events"] = str(m["test_events"])
    f["test_countries"] = str(int(win.loc[("primary", "locked_test"), "countries"]))
    f["test_event_countries"] = str(m["test_event_countries"])
    f["test_event_cy"] = str(m["test_event_country_years"])
    f["test_events_effective"] = f"{m['test_events_effective']:.0f}"
    f["s25_n"] = str(int(win.loc[("primary", "shock_stress_2025"), "n"]))
    f["s25_events"] = str(m["stress2025_events"])
    f["broad_n"] = f"{int(win.loc['broad']['n'].sum()):,}"
    f["broad_events"] = f"{int(win.loc['broad']['events'].sum()):,}"
    cov = pd.read_csv(paths.AUDIT / "coverage_qc.csv").iloc[0]
    f["cov_over100_pct"] = pct(cov["cov_over_100"] / cov["delivered_rows"])
    f["epi_cov_over100_pct"] = pct(cov["epi_cov_over_100"] / cov["delivered_rows"])
    # ---- label audit ----
    f["hs_resumed_pct"] = pct(m["hindsight_resumed_share_primary"])
    f["hs_stop_pct"] = pct(m["hindsight_stop_share_primary"])
    f["hs_stop_excl_pct"] = pct(m["hindsight_stop_share_excluded"])
    # ---- clustering ----
    f["whole_country_pct"] = pct(m["events_in_whole_country_failures"] / m["primary_events"])
    f["majority_pct"] = pct(m["events_in_majority_failure_country_years"] / m["primary_events"])
    f["between_cy_pct"] = pct(1 - m["within_country_year_variance_share"])
    f["between_c_pct"] = pct(m["between_country_variance_share"])
    f["cy_total"] = str(m["country_years_total"])
    f["cy_with_events"] = str(m["country_years_with_events"])
    f["cy_mixed"] = str(m["mixed_country_years"])
    # ---- burden ----
    b = pd.read_csv(DESC / "burden_by_year.csv").set_index(["cohort", "year"])
    pk = b.loc["broad", "population_in_interrupted_ius_millions"].idxmax()
    f["peak_year"] = str(pk)
    for cohort in ("primary", "broad"):
        for yr in (2019, 2021, 2024, 2025):
            r = b.loc[(cohort, yr)]
            f[f"{cohort}_pop_{yr}"] = f"{r['population_in_interrupted_ius_millions']:.0f}"
            f[f"{cohort}_popshare_{yr}"] = pct(r["share_population_in_interrupted_ius"])
            f[f"{cohort}_iushare_{yr}"] = pct(r["share_ius_interrupted"])
    f["primary_total_person_rounds"] = \
        f"{b.loc['primary', 'population_in_interrupted_ius_millions'].sum():.0f}"
    f["broad_total_person_rounds"] = \
        f"{b.loc['broad', 'population_in_interrupted_ius_millions'].sum():.0f}"
    bc = pd.read_csv(DESC / "burden_by_country.csv", keep_default_na=False, na_values=[""])
    top = bc[bc["cohort"] == "primary"].head(4)
    f["top_countries"] = ", ".join(f"{r.country} ({pct(r.share_of_all_missed_person_rounds)})"
                                   for r in top.itertuples())
    f["top4_share"] = pct(top["share_of_all_missed_person_rounds"].sum())
    # ---- recovery ----
    rec = pd.read_csv(DESC / "recovery_within_years.csv").set_index(["era", "years_since_onset"])
    for tag, era in (("pre", "2016-2019"), ("covid", "2020-2021 (COVID-19)"),
                     ("post", "2022-2024")):
        for k in (1, 2, 3):
            f[f"rec_{tag}_{k}"] = pct(rec.loc[(era, k), "share_resumed"])
        f[f"rec_{tag}_n"] = str(int(rec.loc[(era, 1), "onsets_with_follow_up"]))
    rep = pd.read_csv(DESC / "repeat_interruptions.csv").set_index("interrupted_years")
    f["never_interrupted_pct"] = pct(rep.loc[0, "share_of_ius"])
    f["repeat_ius_pct"] = pct(rep.loc[rep.index >= 2, "share_of_ius"].sum())
    f["repeat_ius_n"] = f"{int(rep.loc[rep.index >= 2, 'ius'].sum()):,}"
    f["repeat_events_pct"] = pct(rep.loc[rep.index >= 2, "share_of_all_interruptions"].sum())
    ps = json.loads((DESC / "country_persistence_stats.json").read_text("utf-8"))
    pt = pd.read_csv(DESC / "country_persistence.csv").set_index("majority_prev")
    f["persist_rho"] = f"{ps['spearman_rho']:.2f}"
    f["persist_pairs"] = str(ps["country_year_pairs"])
    f["persist_auroc"] = f"{ps['auroc_prev_rate_for_majority_failure']:.2f}"
    f["persist_after_failure"] = pct(pt.loc[True, "share"])
    f["persist_after_ok"] = pct(pt.loc[False, "share"])
    le = pd.read_csv(DESC / "level_by_era.csv").set_index(["cohort", "era"])
    f["between_cy_2025_pct"] = pct(le.loc[("primary", "2025"), "variance_between_country_years"])
    f["whole_country_2025_pct"] = pct(le.loc[("primary", "2025"), "share_events_every_iu_missed"])
    # ---- models: development ----
    dci = pd.read_csv(DEV / "development_intervals.csv")
    dev = _ci_lookup(dci[dci["scenario"] == "P"])
    dm = pd.read_csv(DEV / "development_metrics.csv")
    dmP = dm[dm["scenario"] == "P"].set_index(["subset", "model"])
    f["dev_rule_within"] = dev("history_rule", "within_country_year_auroc",
                               subset="rolling_2019_2022")
    f["dev_rule_within_noncovid"] = f"{dmP.loc[('non_covid_2019_2022', 'history_rule'), 'within_country_year_auroc']:.2f}"
    f["dev_rule_cap_noncovid"] = pct(dmP.loc[("non_covid_2019_2022", "history_rule"),
                                             "capture_at_20pct"])
    f["dev_covid_auroc_range"] = "{:.2f} to {:.2f}".format(
        *dmP.loc["covid_2020_2021"].drop("prevalence")["auroc"].agg(["min", "max"]))
    sel = json.loads((DEV / "selected_configs.json").read_text("utf-8"))["P"]
    f["dev_ll_prevalence"] = f"{sel['prevalence']['pooled_log_loss']:.3f}"
    f["dev_ll_catboost"] = f"{sel['catboost_history']['pooled_log_loss']:.3f}"
    lock = json.loads((LOCK / "LOCK.json").read_text("utf-8"))
    prim = lock["primary_candidate"]
    f["primary_candidate"] = NAMES[prim]
    f["dev_ll_primary"] = f"{sel[prim]['pooled_log_loss']:.3f}"
    r0 = json.loads((paths.EVALUATION / "development_round0" / "selected_configs.json")
                    .read_text("utf-8"))["P"]
    f["dev0_ll_catboost"] = f"{r0['catboost_history']['pooled_log_loss']:.2f}"
    f["n_approaches"] = str(len(sel))
    # ---- models: locked test ----
    lci = pd.read_csv(LOCK / "locked_intervals.csv")
    L = _ci_lookup(lci)
    P = dict(scenario="P", subset="locked_test_2023_2024")
    for tag, model in (("rule", "history_rule"), ("prim", prim), ("lh", "logistic_history"),
                       ("cb", "catboost_history"), ("cpr", "country_prior_rate")):
        f[f"lt_{tag}_auroc"] = L(model, "auroc", **P)
        f[f"lt_{tag}_within"] = L(model, "within_country_year_auroc", **P)
        f[f"lt_{tag}_cap20"] = L(model, "capture_at_20pct", **P)
        f[f"lt_{tag}_cap10"] = L(model, "capture_at_10pct", **P)
    ld = pd.read_csv(LOCK / "locked_differences_vs_rule.csv")
    D = _ci_lookup(ld, "difference")
    f["lt_prim_vs_rule_cap20"] = D(prim, "capture_at_20pct", 3, **P)
    f["lt_prim_vs_rule_auroc"] = D(prim, "auroc", 3, **P)
    d20 = ld[(ld["scenario"] == "P") & (ld["subset"] == "locked_test_2023_2024")
             & (ld["metric"] == "capture_at_20pct")
             & ~ld["model"].isin(["prevalence", "country_prior_rate"])]
    f["n_models_vs_rule"] = str(len(d20))
    cleared = int(((d20["difference"] >= 0.05) & (d20["ci_low"] > 0)).sum())
    below = int((d20["difference"] < 0).sum())
    f["n_models_cleared"] = "none" if cleared == 0 else str(cleared)
    f["n_models_cap_below_rule"] = "all" if below == len(d20) else str(below)
    f["verdict"] = "was not met" if not ((d20[d20["model"] == prim]["difference"] >= 0.05)
                                         & (d20[d20["model"] == prim]["ci_low"] > 0)).any() \
        else "was met"
    lm = pd.read_csv(LOCK / "locked_metrics.csv")
    lmP = lm[(lm["scenario"] == "P") & (lm["subset"] == "locked_test_2023_2024")].set_index("model")
    fitted = lmP.drop(index=["prevalence"])
    f["lt_oe_range"] = "{:.2f} to {:.2f}".format(fitted["observed_expected_ratio"].min(),
                                                 fitted["observed_expected_ratio"].max())
    f["lt_brier_rule_cal"] = f"{lmP.loc['history_rule', 'brier']:.3f}"
    f["lt_brier_rule_raw"] = f"{lmP.loc['history_rule', 'uncalibrated_brier']:.3f}"
    f["lt_within_models_range"] = "{:.2f} to {:.2f}".format(
        *lmP.drop(index=["prevalence", "country_prior_rate", "history_rule"])
        ["within_country_year_auroc"].agg(["min", "max"]))
    lmE = lm[(lm["scenario"] == "E") & (lm["subset"] == "locked_test_2023_2024")].set_index("model")
    f["E_auroc_range"] = "{:.2f} to {:.2f}".format(
        *lmE.drop(index=["prevalence"])["auroc"].agg(["min", "max"]))
    E = dict(scenario="E", subset="locked_test_2023_2024")
    f["E_rule_auroc"] = L("history_rule", "auroc", **E)
    f["E_rule_cap20"] = L("history_rule", "capture_at_20pct", **E)
    S = dict(scenario="P", subset="stress_2025")
    f["s25_rule_auroc"] = L("history_rule", "auroc", **S)
    f["s25_rule_cap20"] = L("history_rule", "capture_at_20pct", **S)
    f["s25_prim_auroc"] = L(prim, "auroc", **S)
    f["s25_cb_auroc"] = L("catboost_history", "auroc", **S)
    yr = lm[lm["scenario"] == "P"].set_index(["subset", "model"])
    for y in (2023, 2024):
        f[f"rule_within_{y}"] = f"{yr.loc[(f'year_{y}', 'history_rule'), 'within_country_year_auroc']:.2f}"
        f[f"rule_cap20_{y}"] = pct(yr.loc[(f"year_{y}", "history_rule"), "capture_at_20pct"])
        f[f"events_{y}"] = str(int(yr.loc[(f"year_{y}", "history_rule"), "events"]))
    jk = pd.read_csv(LOCK / "locked_country_jackknife.csv")
    j = jk[(jk["scenario"] == "P") & (jk["subset"] == "locked_test_2023_2024")
           & (jk["model"] == "history_rule")]
    f["jk_rule_cap20_range"] = "{:.0f}% to {:.0f}%".format(100 * j["capture_at_20pct"].min(),
                                                           100 * j["capture_at_20pct"].max())
    f["jk_rule_auroc_range"] = "{:.2f} to {:.2f}".format(j["auroc"].min(), j["auroc"].max())
    f["pop_ratio_2025_2024"] = "{:.1f}".format(
        b.loc[("primary", 2025), "population_in_interrupted_ius_millions"]
        / b.loc[("primary", 2024), "population_in_interrupted_ius_millions"])
    # ---- transport ----
    tci = pd.read_csv(LOCO / "transport_pooled_intervals.csv")
    T = _ci_lookup(tci)
    f["loco_rule_auroc"] = T("history_rule", "auroc")
    f["loco_rule_within"] = T("history_rule", "within_country_year_auroc")
    f["loco_prim_auroc"] = T(prim, "auroc")
    f["loco_prim_cap20"] = T(prim, "capture_at_20pct")
    f["loco_rule_cap20"] = T("history_rule", "capture_at_20pct")
    f["loco_cb_auroc"] = T("catboost_history", "auroc")
    tr = pd.read_csv(LOCO / "transport_by_country.csv", keep_default_na=False, na_values=[""])
    sup = tr[tr["supports_external_claim"].astype(str).str.lower() == "true"]
    f["loco_supported"] = str(sup["iso2"].nunique())
    f["loco_total"] = str(tr["iso2"].nunique())
    rr = sup[sup["model"] == "history_rule"]["auroc"]
    f["loco_rule_country_range"] = f"{rr.min():.2f} to {rr.max():.2f}"
    f["loco_rule_below_half"] = str(int((rr < 0.5).sum()))
    # ---- sensitivity ----
    s = pd.read_csv(SENS / "sensitivity_metrics.csv").set_index(["analysis", "model"])
    for tag, name in (("strict", "strict cohort (<5 rounds incl. pre-2014)"),
                      ("incident", "incident cohort (delivered at t-1)"),
                      ("mixed", "mixed country-years only (both outcomes present)")):
        f[f"sens_{tag}_rule_cap20"] = pct(s.loc[(name, "history_rule"), "capture_at_20pct"])
        f[f"sens_{tag}_prim_cap20"] = pct(s.loc[(name, prim), "capture_at_20pct"])
        f[f"sens_{tag}_events"] = str(int(s.loc[(name, "history_rule"), "events"]))
    # ---- exploratory ----
    x = pd.read_csv(EXPLO / "exploratory_differences_vs_rule.csv")
    X = _ci_lookup(x, "difference")
    lt = "locked test 2023-2024 (already opened; NOT an independent test)"
    f["x3_vs_rule_cap20"] = X("rule_plus_rounds", "capture_at_20pct", 3, evaluation=lt)
    f["x1_vs_rule_cap20"] = X("within_between_logistic", "capture_at_20pct", 3, evaluation=lt)
    f["x2_vs_rule_cap20"] = X("two_level_rank", "capture_at_20pct", 3, evaluation=lt)
    xd = x[(x["metric"] == "capture_at_20pct") & (x["model"] != prim)]
    f["x_any_clear"] = "None" if not ((xd["difference"] >= 0.05) & (xd["ci_low"] > 0)).any() \
        else "At least one"
    src = pd.read_csv(paths.MANIFESTS / "espen_sources.csv", keep_default_na=False)
    f["retrieved"] = src["retrieved_utc"].min()[:10]
    return f


def render_manuscript() -> str:
    facts = build_facts()
    (paths.REPORTS / "facts.json").write_text(json.dumps(facts, indent=2), encoding="utf-8")
    template = (paths.ROOT / "manuscript" / "manuscript_template.md").read_text("utf-8")
    try:
        text = template.format_map(facts)
    except KeyError as exc:
        raise KeyError(f"manuscript template uses a placeholder with no value: {exc}") from exc
    out = paths.ROOT / "manuscript" / "manuscript_draft.md"
    out.write_text(text, encoding="utf-8")
    words = len(text.split())
    return f"wrote {out.relative_to(paths.ROOT)} ({words:,} words, {len(facts)} facts)"
