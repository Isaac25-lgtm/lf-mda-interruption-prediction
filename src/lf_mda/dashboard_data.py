"""Build the compact, derived dataset that the Streamlit dashboard reads.

The dashboard never trains or re-scores a model. It reads stored predictions:
out-of-fold predictions for development years and the single locked-test / 2025 run.
The file holds derived values only (status class, cohort flags, IU centroid, stored
risk scores); raw ESPEN extracts and boundary polygons are not included.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from . import paths

DASH_DATA = paths.ROOT / "dashboard" / "data"

DISPLAY_CLASS = {
    "delivered": "Delivered",
    "reported_interruption": "Reported interruption (unverified proxy)",
    "never_started": "Requires MDA, never started",
    "non_delivery_outside_cohort": "Not delivered, outside active cohort",
    "legitimate_pause_IA": "Pending impact assessment",
    "surveillance_or_stopped": "Post-intervention surveillance",
    "not_endemic": "Non-endemic",
    "missing_JRF": "No data: not reported",
    "missing_iu_year": "No data: no record",
    "contradictory": "No data: contradictory record",
    "unknown": "No data: status unknown",
}


def build_dashboard_data() -> dict:
    DASH_DATA.mkdir(parents=True, exist_ok=True)
    panel = pd.read_parquet(paths.PROCESSED / "panel.parquet")
    cols = ["iu_key", "iso2", "country", "iu_id", "year", "admin1", "iu_name", "lifecycle_class",
            "outcome_class", "eligible_primary", "eligible_broad", "y", "window",
            "row_class_l1", "eff_rounds_obs_l1", "pop_tot", "epi_cov"]
    base = panel.loc[panel["year"] >= 2016, cols].copy()
    # carry the latest known names onto rows where the IU has no record that year
    names = (panel[panel["row_present"]].sort_values("year")
             .groupby("iu_key")[["admin1", "iu_name"]].last())
    base["admin1"] = base["admin1"].fillna(base["iu_key"].map(names["admin1"]))
    base["iu_name"] = base["iu_name"].fillna(base["iu_key"].map(names["iu_name"]))
    base["display_class"] = base["lifecycle_class"].map(DISPLAY_CLASS).fillna("No data")
    in_cohort_excluded = base["eligible_primary"] & base["y"].isna()
    base["cohort_status"] = np.select(
        [base["eligible_primary"] & base["y"].notna(), in_cohort_excluded,
         base["eligible_broad"]],
        ["In primary cohort", "In cohort, outcome excluded",
         "Excluded: 5+ effective rounds"], default="Not eligible")

    geo_file = paths.PROCESSED / "iu_geo.parquet"
    if geo_file.exists():
        geo = pd.read_parquet(geo_file)[["iso2", "iu_id", "lon", "lat"]]
        base = base.merge(geo, on=["iso2", "iu_id"], how="left")
    else:
        base["lon"] = base["lat"] = np.nan

    info = {"built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "has_predictions": False, "models": []}
    oof_file = paths.PROCESSED / "predictions_development_oof.parquet"
    held_file = paths.PROCESSED / "predictions_heldout.parquet"
    if oof_file.exists() and held_file.exists():
        oof = pd.read_parquet(oof_file)
        held = pd.read_parquet(held_file)
        models = [c[2:] for c in held.columns if c.startswith("p_")]
        keep = ["iu_key", "year"] + [f"{k}_{m}" for m in models for k in ("p", "r")]
        o = oof.loc[oof["scenario"] == "P", keep].assign(prediction_source="Development fold "
                                                         "(out-of-fold, uncalibrated)")
        h = held.loc[(held["scenario"] == "P") & held["eligible_primary"], keep].copy()
        h["prediction_source"] = np.where(h["year"] == 2025, "2025 stress year (held out)",
                                          "Locked test (held out)")
        pred = pd.concat([o, h], ignore_index=True)
        for c in pred.columns:
            if c.startswith(("p_", "r_")):
                pred[c] = pred[c].astype("float32")
        base = base.merge(pred, on=["iu_key", "year"], how="left")
        info.update(has_predictions=True, models=models)
        e_keep = ["iu_key", "year"] + [f"r_{m}" for m in models]
        he = held.loc[(held["scenario"] == "E") & held["eligible_primary"], e_keep]
        he = he.rename(columns={f"r_{m}": f"rE_{m}" for m in models})
        base = base.merge(he, on=["iu_key", "year"], how="left")
    base["prediction_source"] = base.get("prediction_source", pd.Series(index=base.index,
                                                                        dtype=object))
    base["prediction_source"] = base["prediction_source"].fillna("No stored prediction")
    for c in ("lon", "lat", "pop_tot", "epi_cov", "eff_rounds_obs_l1", "y"):
        base[c] = base[c].astype("float32")
    for c in ("iso2", "country", "admin1", "display_class", "cohort_status", "window",
              "prediction_source", "lifecycle_class", "outcome_class", "row_class_l1"):
        base[c] = base[c].astype("category")
    base = base.drop(columns=["iu_key"])
    base.to_parquet(DASH_DATA / "iu_year.parquet", index=False, compression="zstd")

    lab = panel[panel["eligible_primary"] & panel["y"].notna()]
    cy = lab.groupby(["iso2", "iso3", "country", "year"]).agg(
        eligible_ius=("y", "size"), interruptions=("y", "sum")).reset_index()
    cy["interruption_rate"] = cy["interruptions"] / cy["eligible_ius"]
    cy.to_csv(DASH_DATA / "country_year.csv", index=False)
    iso3 = panel.drop_duplicates("iso2")[["iso2", "iso3", "country"]]
    iso3.to_csv(DASH_DATA / "countries.csv", index=False)

    gate = json.loads((paths.AUDIT / "gate_decision.json").read_text("utf-8"))
    src = pd.read_csv(paths.MANIFESTS / "espen_sources.csv")
    info.update(
        n_rows=int(len(base)), gate_decision=gate["gate"]["decision"],
        information_adequacy=gate["gate"]["information_adequacy"],
        expert_verification=gate["gate"]["expert_verification"],
        espen_retrieved_utc=str(src["retrieved_utc"].min()),
        n_countries_downloaded=int(len(src)), metrics=gate["metrics"],
        size_mb=round((DASH_DATA / "iu_year.parquet").stat().st_size / 1e6, 2))
    (DASH_DATA / "info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    return {k: v for k, v in info.items() if k != "metrics"}
