"""Status mapping, IU-year panel construction, cohort eligibility and outcome classes.

Design rules enforced here:
* a missing report or a missing IU-year is a missing label, never an interruption;
* eligibility uses only information dated t-1 or earlier; outcome-year fields are used
  only to classify the outcome;
* lags are joins on (IU, year), never positional shifts over a gappy panel;
* contradictory rows are quarantined, not turned into positives.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from . import paths

FIRST_YEAR, LAST_YEAR = 2014, 2025

ROW_CLASSES = ["delivered", "non_delivery", "legitimate_pause_IA", "surveillance_or_stopped",
               "not_endemic", "missing_JRF", "missing_iu_year", "contradictory", "unknown"]

# Outcome class of an eligible IU-year, given the row class observed in the outcome year.
OUTCOME_FROM_ROW_CLASS = {
    "delivered": "delivered",
    "non_delivery": "reported_interruption",
    "legitimate_pause_IA": "legitimate_pause_IA",
    "surveillance_or_stopped": "surveillance_or_stopped",
    "not_endemic": "surveillance_or_stopped",
    "missing_JRF": "missing_JRF",
    "missing_iu_year": "missing_iu_year",
    "contradictory": "contradictory",
    "unknown": "unknown",
}

RENAME = {
    "admin0Iso2": "iso2", "admin0Iso3": "iso3", "admin0": "country", "admin1": "admin1",
    "admin1Id": "admin1_id", "iusName": "iu_name", "iuId": "iu_id", "iuCode": "iu_code",
    "iusAdm": "iu_admin_level", "endemicity": "endemicity_raw", "endemicityId": "endemicity_id",
    "popReq": "pop_req", "popTrg": "pop_trg", "popTreat": "pop_treat", "cov": "cov",
    "epiCov": "epi_cov", "mdaScheme": "scheme", "popTot": "pop_tot", "cumMda": "cum_mda",
    "mda": "mda", "effMda": "eff_mda", "mdaN": "mda_n", "effMdaN": "eff_mda_n",
    "epiMda": "epi_mda", "epiEffMda": "epi_eff_mda", "epiMdaN": "epi_mda_n",
    "epiEffMdaN": "epi_eff_mda_n",
}


def load_protocol(path: Path | None = None) -> dict:
    with open(path or paths.CONFIG / "protocol.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_status_map(path: Path | None = None) -> pd.DataFrame:
    smap = pd.read_csv(path or paths.CONFIG / "status_map_reviewed.csv", dtype=str,
                       keep_default_na=False)
    if smap["raw_endemicity"].duplicated().any():
        raise ValueError("status map has duplicated raw_endemicity values")
    bad = set(smap["row_class"]) - set(ROW_CLASSES)
    if bad:
        raise ValueError(f"status map uses unknown row classes: {bad}")
    return smap


def classify_rows(typed: pd.DataFrame, status_map: pd.DataFrame | None = None) -> pd.DataFrame:
    """Attach status code and row class to each observed IU-year row.

    Precedence: (1) unmapped status -> unknown; (2) status contradicted by treatment
    fields -> contradictory; (3) otherwise the reviewed status-map class.
    """
    smap = load_status_map() if status_map is None else status_map
    df = typed.rename(columns=RENAME).copy()
    df["year"] = df["year"].astype(int)
    df["iu_id"] = df["iu_id"].astype(int)
    df["iu_key"] = df["iso2"] + "-" + df["iu_id"].astype(str)
    if df.duplicated(["iu_key", "year"]).any():
        n = int(df.duplicated(["iu_key", "year"]).sum())
        raise ValueError(f"{n} duplicated IU-year rows; resolve before labelling")
    code = dict(zip(smap["raw_endemicity"], smap["status_code"]))
    klass = dict(zip(smap["raw_endemicity"], smap["row_class"]))
    df["status_code"] = df["endemicity_raw"].map(code)
    df["status_mapped"] = df["status_code"].notna()
    df["status_code"] = df["status_code"].fillna("UNMAPPED")
    mapped = df["endemicity_raw"].map(klass).fillna("unknown")

    treated = (df["pop_treat"] > 0) | (df["mda"] == 1) | (df["scheme"] != "Not delivered")
    not_treated = ~(df["pop_treat"] > 0) | (df["mda"] != 1)
    contradiction = pd.Series("", index=df.index)
    contradiction[(mapped == "non_delivery") & treated] = "non_delivery_but_treatment_recorded"
    contradiction[(mapped == "delivered") & not_treated] = "delivered_but_no_treatment_recorded"
    no_treat_expected = mapped.isin(["legitimate_pause_IA", "surveillance_or_stopped",
                                     "not_endemic", "missing_JRF"])
    contradiction[no_treat_expected & treated] = "no_mda_status_but_treatment_recorded"
    contradiction[(mapped == "non_delivery") & ~(df["pop_req"] > 0)] = \
        "non_delivery_but_no_population_requiring"
    df["contradiction"] = contradiction
    df["row_class"] = mapped.where(contradiction == "", "contradictory")
    df["delivered_flag"] = (df["row_class"] == "delivered").astype(int)
    return df


def build_panel(rows: pd.DataFrame, protocol: dict | None = None) -> pd.DataFrame:
    """Build the complete IU x year grid with lags, eligibility and outcome classes."""
    proto = protocol or load_protocol()
    coh = proto["cohort"]
    years = np.arange(FIRST_YEAR, LAST_YEAR + 1)
    static_cols = ["iu_key", "iso2", "iso3", "country", "iu_id"]
    ius = rows.sort_values("year").groupby("iu_key", as_index=False).agg(
        {c: "last" for c in static_cols[1:]} | {"year": ["min", "max", "nunique"]})
    ius.columns = ["iu_key", "iso2", "iso3", "country", "iu_id", "first_row_year",
                   "last_row_year", "n_row_years"]
    grid = ius.merge(pd.DataFrame({"year": years}), how="cross")
    panel = grid.merge(rows.drop(columns=["iso2", "iso3", "country", "iu_id"]),
                       on=["iu_key", "year"], how="left")
    panel["row_present"] = panel["status_code"].notna()
    panel["row_class"] = panel["row_class"].fillna("missing_iu_year")
    panel["status_code"] = panel["status_code"].fillna("NOROW")
    panel["gap_type"] = np.select(
        [panel["row_present"], panel["year"] < panel["first_row_year"],
         panel["year"] > panel["last_row_year"]],
        ["", "before_first_row", "after_last_row"], default="internal_gap")

    # rounds delivered before the extract window; constant within IU by construction
    panel["rounds_before_2014"] = (panel["cum_mda"] - panel["mda_n"]).clip(lower=0)
    panel["rounds_before_2014"] = panel.groupby("iu_key")["rounds_before_2014"].transform("max")

    lag_cols = ["row_class", "status_code", "epi_eff_mda_n", "cum_mda", "mda_n", "epi_cov",
                "cov", "epi_eff_mda", "pop_req", "pop_tot", "scheme"]
    for lag in (1, 2, 3):
        src = panel[["iu_key", "year"] + lag_cols].copy()
        src["year"] = src["year"] + lag
        src = src.rename(columns={c: f"{c}_l{lag}" for c in lag_cols})
        panel = panel.merge(src, on=["iu_key", "year"], how="left")
        panel[f"row_class_l{lag}"] = panel[f"row_class_l{lag}"].fillna("before_window")

    req_l1 = panel["row_class_l1"].isin(["delivered", "non_delivery"]) \
        if coh["requires_mda_at_lag1"] else True
    recent = np.zeros(len(panel), dtype=bool)
    for lag in coh["recent_delivery_lags"]:
        recent |= (panel[f"row_class_l{lag}"] == "delivered").to_numpy()
    in_years = panel["year"].between(coh["first_target_year"], coh["last_target_year"])
    panel["eligible_broad"] = (req_l1 & recent & in_years).astype(bool)
    panel["eff_rounds_obs_l1"] = panel["epi_eff_mda_n_l1"]
    panel["eff_rounds_ub_l1"] = panel["epi_eff_mda_n_l1"] + panel["rounds_before_2014"]
    max_eff = coh["max_observed_effective_rounds_at_lag1"]
    panel["eligible_primary"] = panel["eligible_broad"] & (panel["eff_rounds_obs_l1"] <= max_eff)
    panel["eligible_strict"] = panel["eligible_broad"] & (panel["eff_rounds_ub_l1"] <= max_eff)
    panel["eligible_incident"] = panel["eligible_primary"] & (panel["row_class_l1"] == "delivered")

    panel["outcome_class"] = panel["row_class"].map(OUTCOME_FROM_ROW_CLASS)
    panel["y"] = np.select(
        [panel["outcome_class"] == "reported_interruption", panel["outcome_class"] == "delivered"],
        [1.0, 0.0], default=np.nan)

    # lifecycle label for every row, used for accounting outside the cohort
    never = (panel["row_class"] == "non_delivery") & (panel["cum_mda"] == 0)
    panel["lifecycle_class"] = np.select(
        [never, (panel["row_class"] == "non_delivery") & panel["eligible_broad"],
         panel["row_class"] == "non_delivery"],
        ["never_started", "reported_interruption", "non_delivery_outside_cohort"],
        default=panel["row_class"])

    panel = _add_hindsight(panel)
    panel = _add_window(panel, proto)
    return panel.sort_values(["iso2", "iu_id", "year"]).reset_index(drop=True)


def _add_hindsight(panel: pd.DataFrame) -> pd.DataFrame:
    """What the IU did after a non-delivery spell. AUDIT ONLY - uses future years.

    Never a feature and never part of eligibility. `hs_next` is the first row class
    observed after the run of consecutive non-delivery years that contains year t.
    """
    wide = panel.pivot(index="iu_key", columns="year", values="row_class")
    years = sorted(wide.columns)
    nxt = pd.DataFrame("censored", index=wide.index, columns=years)
    for i in range(len(years) - 2, -1, -1):
        y, y1 = years[i], years[i + 1]
        following = wide[y1]
        nxt[y] = np.where(following == "non_delivery", nxt[y1], following)
    long = nxt.stack().rename("hs_next").reset_index()
    long.columns = ["iu_key", "year", "hs_next"]
    panel = panel.merge(long, on=["iu_key", "year"], how="left")
    panel.loc[panel["row_class"] != "non_delivery", "hs_next"] = ""
    panel["hs_group"] = panel["hs_next"].map({
        "": "", "delivered": "resumed_mda", "legitimate_pause_IA": "moved_to_IA_or_surveillance",
        "surveillance_or_stopped": "moved_to_IA_or_surveillance",
        "not_endemic": "moved_to_IA_or_surveillance", "censored": "censored",
    }).fillna("other_or_missing")
    return panel


def _add_window(panel: pd.DataFrame, proto: dict) -> pd.DataFrame:
    w = proto["windows"]
    year = panel["year"]
    panel["window"] = np.select(
        [year.between(*w["development"]), year.between(*w["locked_test"]),
         year.isin(w["shock_stress_test"])],
        ["development", "locked_test", "shock_stress_2025"], default="not_a_target_year")
    panel["covid_stress_year"] = year.isin(w["covid_stress_years"])
    return panel


def analysis_set(panel: pd.DataFrame, cohort: str = "primary") -> pd.DataFrame:
    """Eligible IU-years with a usable binary outcome for the named cohort."""
    col = f"eligible_{cohort}"
    return panel[panel[col] & panel["y"].notna()].copy()


def country_year_flags(panel: pd.DataFrame, release: pd.DataFrame | None = None) -> pd.DataFrame:
    """Country-year reporting diagnostics (carried-forward populations, non-reporting)."""
    obs = panel[panel["row_present"]].copy()
    obs["pop_same_as_prev"] = obs["pop_tot"] == obs["pop_tot_l1"]
    obs["has_prev"] = obs["pop_tot_l1"].notna()
    g = obs.groupby(["iso2", "country", "year"])
    out = g.agg(n_iu=("iu_key", "size"),
                n_delivered=("row_class", lambda s: int((s == "delivered").sum())),
                n_non_delivery=("row_class", lambda s: int((s == "non_delivery").sum())),
                n_not_reported=("row_class", lambda s: int((s == "missing_JRF").sum())),
                n_with_prev=("has_prev", "sum"),
                n_pop_same=("pop_same_as_prev", "sum")).reset_index()
    out["share_pop_carried_forward"] = np.where(out["n_with_prev"] > 0,
                                                out["n_pop_same"] / out["n_with_prev"], np.nan)
    out["flag_population_carried_forward"] = out["share_pop_carried_forward"] >= 0.95
    out["flag_whole_country_not_reported"] = out["n_not_reported"] == out["n_iu"]
    if release is not None:
        out = out.merge(release, on=["iso2", "year"], how="left")
    return out
