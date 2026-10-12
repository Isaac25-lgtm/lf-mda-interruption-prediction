"""Descriptive epidemiology of reported MDA interruptions: burden, level, recovery.

These analyses describe what was reported. They involve no model and no held-out test,
so they are not affected by the limits on predictive evidence. They inherit the label
caveat: an "interruption" is a reported status, and in the broad cohort some may be
legitimate pauses for impact assessment.

Two cohorts are reported side by side:
  primary - active programmes with fewer than 5 observed effective rounds (conservative);
  broad   - all active programmes (upper bound; includes units due for assessment).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from . import paths
from .audit import variance_partition
from .evaluate import auroc

OUT = paths.REPORTS / "descriptive"
ERAS = {"2016-2019": (2016, 2019), "2020-2021 (COVID-19)": (2020, 2021),
        "2022-2024": (2022, 2024), "2025": (2025, 2025)}


def _labelled(panel: pd.DataFrame, cohort: str) -> pd.DataFrame:
    return panel[panel[f"eligible_{cohort}"] & panel["y"].notna()].copy()


def burden_by_year(panel: pd.DataFrame) -> pd.DataFrame:
    """IUs and population in units with a reported interruption, per year and cohort.

    `pop_req` is the population requiring treatment in the IU that year. Population "in
    interrupted IUs" is therefore people living where the round was reported not
    delivered; it is not a count of confirmed missed doses.
    """
    rows = []
    for cohort in ("primary", "broad"):
        a = _labelled(panel, cohort)
        for year, g in a.groupby("year"):
            ev = g[g["y"] == 1]
            rows.append({
                "cohort": cohort, "year": int(year), "eligible_ius": len(g),
                "interrupted_ius": len(ev), "share_ius_interrupted": len(ev) / len(g),
                "population_requiring_millions": g["pop_req"].sum() / 1e6,
                "population_in_interrupted_ius_millions": ev["pop_req"].sum() / 1e6,
                "share_population_in_interrupted_ius":
                    ev["pop_req"].sum() / g["pop_req"].sum() if g["pop_req"].sum() else np.nan,
                "countries_in_cohort": g["iso2"].nunique(),
                "countries_with_interruption": ev["iso2"].nunique(),
            })
    return pd.DataFrame(rows)


def burden_by_country(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cohort in ("primary", "broad"):
        a = _labelled(panel, cohort)
        g = a.groupby(["iso2", "country"]).apply(lambda d: pd.Series({
            "iu_years": len(d), "interrupted_iu_years": int(d["y"].sum()),
            "years_with_interruption": int(d.loc[d["y"] == 1, "year"].nunique()),
            "person_rounds_requiring_millions": d["pop_req"].sum() / 1e6,
            "person_rounds_in_interrupted_ius_millions":
                d.loc[d["y"] == 1, "pop_req"].sum() / 1e6}), include_groups=False).reset_index()
        g.insert(0, "cohort", cohort)
        rows.append(g)
    out = pd.concat(rows)
    tot = out.groupby("cohort")["person_rounds_in_interrupted_ius_millions"].transform("sum")
    out["share_of_all_missed_person_rounds"] = out["person_rounds_in_interrupted_ius_millions"] / tot
    return out.sort_values(["cohort", "person_rounds_in_interrupted_ius_millions"],
                           ascending=[True, False])


def level_by_year(panel: pd.DataFrame, cohort: str = "primary") -> pd.DataFrame:
    """How much of each year's interruptions came from country-wide failures."""
    a = _labelled(panel, cohort)
    cy = a.groupby(["iso2", "year"])["y"].agg(n="size", ev="sum").reset_index()
    cy["rate"] = cy["ev"] / cy["n"]
    cy["band"] = pd.cut(cy["rate"], [-1, 0.5, 0.999999, 1],
                        labels=["half or fewer IUs", "most IUs", "every IU"])
    t = cy.pivot_table(index="year", columns="band", values="ev", aggfunc="sum",
                       fill_value=0, observed=False)
    t.columns = [f"events_where_{c.replace(' ', '_')}_missed" for c in t.columns]
    t["events"] = t.sum(axis=1)
    for c in list(t.columns[:-1]):
        t[c.replace("events_where", "share_where")] = t[c] / t["events"]
    # within a single year, "between country-years" is simply "between countries"
    vp = {year: variance_partition(g)["between_country"] for year, g in a.groupby("year")}
    t["variance_share_between_countries"] = t.index.map(vp)
    return t.reset_index()


def level_by_era(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cohort in ("primary", "broad"):
        a = _labelled(panel, cohort)
        for era, (lo, hi) in (ERAS | {"all years": (2016, 2025)}).items():
            g = a[a["year"].between(lo, hi)]
            vp = variance_partition(g)
            cy = g.groupby(["iso2", "year"])["y"].agg(["size", "sum"])
            rate = cy["sum"] / cy["size"]
            rows.append({"cohort": cohort, "era": era, "iu_years": len(g),
                         "events": int(g["y"].sum()), "prevalence": g["y"].mean(),
                         "variance_between_countries": vp["between_country"],
                         "variance_between_country_years": vp["between_country_year"],
                         "variance_within_country_year": vp["within_country_year"],
                         "share_events_every_iu_missed":
                             cy.loc[rate == 1, "sum"].sum() / max(g["y"].sum(), 1),
                         "share_events_most_ius_missed":
                             cy.loc[rate > 0.5, "sum"].sum() / max(g["y"].sum(), 1)})
    return pd.DataFrame(rows)


def recovery(panel: pd.DataFrame, cohort: str = "primary") -> tuple[pd.DataFrame, pd.DataFrame]:
    """What happened after an interruption began (first non-delivery after a delivered year).

    Returns (spell table summary by era, cumulative recovery by years since onset).
    A spell that moved to impact assessment or surveillance is a different exit from
    resumed MDA and is counted separately.
    """
    wide = panel.pivot(index="iu_key", columns="year", values="row_class")
    onset = panel[panel[f"eligible_{cohort}"] & (panel["y"] == 1)
                  & (panel["row_class_l1"] == "delivered")][["iu_key", "iso2", "year"]]
    recs = []
    for r in onset.itertuples():
        seq = wide.loc[r.iu_key]
        length, exit_ = 0, "still not delivered at end of data"
        for y in range(r.year, 2026):
            v = seq.get(y)
            if v == "non_delivery":
                length += 1
                continue
            exit_ = {"delivered": "resumed MDA",
                     "legitimate_pause_IA": "moved to assessment or surveillance",
                     "surveillance_or_stopped": "moved to assessment or surveillance",
                     "not_endemic": "moved to assessment or surveillance"}.get(
                         v, "no usable record")
            break
        recs.append({"iu_key": r.iu_key, "iso2": r.iso2, "onset_year": r.year,
                     "years_not_delivered": length, "exit": exit_,
                     "follow_up_years": 2025 - r.year})
    sp = pd.DataFrame(recs)
    sp["era"] = pd.cut(sp["onset_year"], [2015, 2019, 2021, 2024, 2025],
                       labels=list(ERAS))
    summ = sp.groupby("era", observed=True).apply(lambda d: pd.Series({
        "interruption_onsets": len(d), "countries": d["iso2"].nunique(),
        "resumed_MDA": int((d["exit"] == "resumed MDA").sum()),
        "moved_to_assessment_or_surveillance":
            int((d["exit"] == "moved to assessment or surveillance").sum()),
        "still_not_delivered_at_end_of_data":
            int((d["exit"] == "still not delivered at end of data").sum()),
        "no_usable_record": int((d["exit"] == "no usable record").sum()),
        "median_years_not_delivered_if_resumed":
            d.loc[d["exit"] == "resumed MDA", "years_not_delivered"].median(),
    }), include_groups=False).reset_index()
    rows = []
    for era, d in sp.groupby("era", observed=True):
        for k in (1, 2, 3):
            base = d[d["follow_up_years"] >= k]         # onsets observable for k more years
            if base.empty:
                continue
            resumed = ((base["exit"] == "resumed MDA") & (base["years_not_delivered"] <= k)).sum()
            rows.append({"era": era, "years_since_onset": k, "onsets_with_follow_up": len(base),
                         "resumed_within": int(resumed), "share_resumed": resumed / len(base)})
    return summ, pd.DataFrame(rows)


def repeat_interruptions(panel: pd.DataFrame, cohort: str = "primary") -> pd.DataFrame:
    a = _labelled(panel, cohort)
    per = a.groupby("iu_key")["y"].agg(years_in_cohort="size", interrupted_years="sum")
    dist = per["interrupted_years"].astype(int).value_counts().sort_index()
    out = dist.rename("ius").rename_axis("interrupted_years").reset_index()
    out["share_of_ius"] = out["ius"] / out["ius"].sum()
    out["share_of_all_interruptions"] = (out["ius"] * out["interrupted_years"]
                                         / (out["ius"] * out["interrupted_years"]).sum())
    return out


def country_persistence(panel: pd.DataFrame, cohort: str = "primary", min_ius: int = 5
                        ) -> tuple[pd.DataFrame, dict]:
    """Does a country's interruption rate one year tell us about the next?"""
    a = _labelled(panel, cohort)
    cy = a.groupby(["iso2", "year"])["y"].agg(n="size", rate="mean").reset_index()
    cy = cy[cy["n"] >= min_ius]
    prev = cy.rename(columns={"rate": "rate_prev", "n": "n_prev"}).assign(year=lambda d: d["year"] + 1)
    j = cy.merge(prev, on=["iso2", "year"])
    j["majority"] = j["rate"] > 0.5
    j["majority_prev"] = j["rate_prev"] > 0.5
    tab = (j.groupby("majority_prev")["majority"].agg(country_years="size", next_year_majority="sum")
           .reset_index())
    tab["share"] = tab["next_year_majority"] / tab["country_years"]
    rho, p = spearmanr(j["rate_prev"], j["rate"])
    stats = {"country_year_pairs": len(j), "spearman_rho": float(rho),
             "spearman_p": float(p),
             "auroc_prev_rate_for_majority_failure":
                 auroc(j["majority"].astype(float), j["rate_prev"]),
             "majority_failure_country_years": int(j["majority"].sum()),
             "min_ius_per_country_year": min_ius}
    return tab, stats


def run_descriptive() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    panel = pd.read_parquet(paths.PROCESSED / "panel.parquet")
    by = burden_by_year(panel)
    bc = burden_by_country(panel)
    ly = level_by_year(panel)
    le = level_by_era(panel)
    summ, rec = recovery(panel)
    summ_b, rec_b = recovery(panel, "broad")
    rep = repeat_interruptions(panel)
    tab, stats = country_persistence(panel)
    by.to_csv(OUT / "burden_by_year.csv", index=False)
    bc.to_csv(OUT / "burden_by_country.csv", index=False)
    ly.to_csv(OUT / "level_by_year.csv", index=False)
    le.to_csv(OUT / "level_by_era.csv", index=False)
    summ.to_csv(OUT / "recovery_summary_by_era.csv", index=False)
    rec.to_csv(OUT / "recovery_within_years.csv", index=False)
    summ_b.to_csv(OUT / "recovery_summary_by_era_broad.csv", index=False)
    rec_b.to_csv(OUT / "recovery_within_years_broad.csv", index=False)
    rep.to_csv(OUT / "repeat_interruptions.csv", index=False)
    tab.to_csv(OUT / "country_persistence.csv", index=False)
    (OUT / "country_persistence_stats.json").write_text(json.dumps(stats, indent=2), "utf-8")
    return stats
