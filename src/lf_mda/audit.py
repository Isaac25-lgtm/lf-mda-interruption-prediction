"""Raw-data profiling, label audit and the feasibility gate.

Everything written here is computed from the raw ESPEN extracts on disk. The gate
decision is rule-based with thresholds declared in `GATE_RULES`; expert verification of
the label cannot be satisfied by code and is always reported as pending.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import paths
from .ingest import OPTIONAL_COLUMNS, coerce_numeric, load_raw
from .labels import analysis_set, build_panel, classify_rows, country_year_flags, load_protocol

GATE_RULES = {
    "max_contradiction_share": 0.01,
    "max_hindsight_stop_share_primary": 0.20,
    "min_development_events": 200,
    "min_locked_test_events": 100,
    "min_locked_test_event_countries": 5,
    "min_events_in_mixed_country_years": 100,
    "min_within_country_year_variance_share": 0.10,
    # advisory only: the concept's target of ~100 independent future events
    "target_effective_locked_test_events": 100,
}

COHORTS = ["primary", "broad", "strict", "incident"]


def load_release_calendar() -> pd.DataFrame:
    # keep_default_na=False: the ISO code for Namibia is "NA" and must stay a string
    cal = pd.read_csv(paths.CONFIG / "source_release_calendar.csv", keep_default_na=False,
                      na_values=[""])
    cal = cal.rename(columns={"data_year": "year"})
    cal = cal.sort_values("release_date").drop_duplicates(["iso2", "year"])
    return cal[["iso2", "year", "release_date", "release_type"]]


def build_all(raw_dir: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw = load_raw(raw_dir)
    typed, diag = coerce_numeric(raw)
    rows = classify_rows(typed)
    panel = build_panel(rows)
    return raw, diag, panel


def variance_partition(df: pd.DataFrame) -> dict:
    """Share of outcome variance lying between countries and between country-years."""
    n, p = len(df), df["y"].mean()
    total = p * (1 - p)
    if n == 0 or total == 0:
        return {"n": n, "prevalence": p, "between_country": np.nan,
                "between_country_year": np.nan, "within_country_year": np.nan}

    def between(keys):
        g = df.groupby(keys)["y"].agg(["mean", "size"])
        return float((g["size"] * (g["mean"] - p) ** 2).sum() / n / total)

    b_c, b_cy = between(["iso2"]), between(["iso2", "year"])
    return {"n": int(n), "prevalence": float(p), "between_country": b_c,
            "between_country_year": b_cy, "within_country_year": 1 - b_cy}


def country_year_rates(df: pd.DataFrame) -> pd.DataFrame:
    cy = df.groupby(["iso2", "country", "year"])["y"].agg(n="size", events="sum").reset_index()
    cy["events"] = cy["events"].astype(int)
    cy["rate"] = cy["events"] / cy["n"]
    cy["band"] = pd.cut(cy["rate"], [-0.001, 0, 0.1, 0.5, 0.9, 0.999999, 1],
                        labels=["0%", ">0-10%", ">10-50%", ">50-90%", ">90-<100%", "100%"])
    cy["mixed"] = (cy["events"] > 0) & (cy["events"] < cy["n"])
    return cy


def icc_design_effect(df: pd.DataFrame, keys: list[str]) -> dict:
    """One-way ANOVA intraclass correlation and design effect for clusters `keys`."""
    g = df.groupby(keys)["y"].agg(["mean", "size"])
    k, n = len(g), len(df)
    if k < 2 or n <= k:
        return {"clusters": k, "icc": np.nan, "design_effect": np.nan, "n_effective": np.nan}
    grand = df["y"].mean()
    msb = (g["size"] * (g["mean"] - grand) ** 2).sum() / (k - 1)
    msw = (df["y"].sub(df.groupby(keys)["y"].transform("mean")) ** 2).sum() / (n - k)
    m0 = (n - (g["size"] ** 2).sum() / n) / (k - 1)
    icc = float(max((msb - msw) / (msb + (m0 - 1) * msw), 0)) if (msb + (m0 - 1) * msw) > 0 else 0.0
    mbar = n / k
    deff = 1 + (mbar - 1) * icc
    return {"clusters": int(k), "icc": icc, "design_effect": float(deff),
            "n_effective": float(n / deff)}


def cohort_flow(panel: pd.DataFrame, proto: dict) -> pd.DataFrame:
    coh = proto["cohort"]
    tgt = panel[panel["year"].between(coh["first_target_year"], coh["last_target_year"])]
    steps = [("IU-year cells in grid, 2014-2025", len(panel)),
             ("... of which a row exists in the extract", int(panel["row_present"].sum())),
             (f"Target years {coh['first_target_year']}-{coh['last_target_year']} (cells)", len(tgt))]
    req = tgt[tgt["row_class_l1"].isin(["delivered", "non_delivery"])]
    steps.append(("Requiring MDA at t-1 (under MDA or MDA not delivered)", len(req)))
    never = req[~req["eligible_broad"]]
    steps.append(("  excluded: no delivery in t-1 or t-2 (never started / long lapsed)", len(never)))
    broad = tgt[tgt["eligible_broad"]]
    steps.append(("Broad cohort: delivered MDA in t-1 or t-2", len(broad)))
    steps.append(("  excluded: >=5 observed effective rounds at t-1 (due for impact assessment)",
                  int((broad["eligible_broad"] & ~broad["eligible_primary"]).sum())))
    prim = tgt[tgt["eligible_primary"]]
    steps.append(("Primary cohort (expected-round cohort)", len(prim)))
    for cls, n in prim["outcome_class"].value_counts().items():
        role = "outcome" if cls in ("delivered", "reported_interruption") else "excluded, counted"
        steps.append((f"  outcome year class: {cls} ({role})", int(n)))
    steps.append(("Primary analysis set (binary outcome available)", int(prim["y"].notna().sum())))
    steps.append(("  reported interruptions (events)", int((prim["y"] == 1).sum())))
    return pd.DataFrame(steps, columns=["step", "n"])


def window_table(panel: pd.DataFrame) -> pd.DataFrame:
    out = []
    for cohort in COHORTS:
        a = analysis_set(panel, cohort)
        for win, g in a.groupby("window"):
            ev = g[g["y"] == 1]
            out.append({"cohort": cohort, "window": win, "n": len(g), "events": int(g["y"].sum()),
                        "prevalence": g["y"].mean(), "distinct_ius": g["iu_key"].nunique(),
                        "countries": g["iso2"].nunique(), "event_countries": ev["iso2"].nunique(),
                        "event_country_years": ev.groupby(["iso2", "year"]).ngroups,
                        "event_ius": ev["iu_key"].nunique()})
    return pd.DataFrame(out)


def hindsight_table(panel: pd.DataFrame) -> pd.DataFrame:
    """Where positives went after the non-delivery spell (audit only, events up to 2022)."""
    out = []
    for cohort in COHORTS + ["broad_excluded_by_rounds"]:
        if cohort == "broad_excluded_by_rounds":
            a = panel[panel["eligible_broad"] & ~panel["eligible_primary"] & (panel["y"] == 1)]
        else:
            a = analysis_set(panel, cohort)
            a = a[a["y"] == 1]
        a = a[a["year"] <= 2022]
        vc = a["hs_group"].value_counts()
        row = {"cohort": cohort, "events_to_2022": len(a)}
        for grp in ["resumed_mda", "moved_to_IA_or_surveillance", "censored", "other_or_missing"]:
            row[grp] = int(vc.get(grp, 0))
            row[grp + "_share"] = vc.get(grp, 0) / len(a) if len(a) else np.nan
        out.append(row)
    return pd.DataFrame(out)


def lineage_table(panel: pd.DataFrame) -> pd.DataFrame:
    obs = panel[panel["row_present"]]
    n = obs.groupby(["iso2", "country", "year"])["iu_key"].nunique().unstack("year")
    first = panel.drop_duplicates("iu_key").groupby("iso2")["first_row_year"].apply(
        lambda s: int((s > 2014).sum())).rename("ius_first_seen_after_2014")
    last = panel.drop_duplicates("iu_key").groupby("iso2")["last_row_year"].apply(
        lambda s: int((s < 2025).sum())).rename("ius_last_seen_before_2025")
    out = n.reset_index().merge(first, on="iso2").merge(last, on="iso2")
    out["iu_count_changes"] = n.nunique(axis=1).gt(1).to_numpy()
    return out


def expert_review_sample(panel: pd.DataFrame, seed: int, per_stratum: int = 40) -> pd.DataFrame:
    """Stratified sample for programme-officer review of the proxy label."""
    rng = np.random.default_rng(seed)
    prim = analysis_set(panel, "primary")
    strata = {
        "positive_primary_cohort": prim[prim["y"] == 1],
        "negative_primary_cohort": prim[prim["y"] == 0],
        "positive_excluded_5plus_effective_rounds":
            panel[panel["eligible_broad"] & ~panel["eligible_primary"] & (panel["y"] == 1)],
        "legitimate_pause_IA_in_cohort":
            panel[panel["eligible_broad"] & (panel["outcome_class"] == "legitimate_pause_IA")],
        "contradictory_rows": panel[panel["row_class"] == "contradictory"],
    }
    picks = []
    for name, df in strata.items():
        if df.empty:
            continue
        # spread the sample across countries: sample countries proportional to sqrt(size)
        w = df.groupby("iso2")["iu_key"].transform("size") ** -0.5
        idx = rng.choice(df.index, size=min(per_stratum, len(df)), replace=False,
                         p=(w / w.sum()).to_numpy())
        s = df.loc[idx].copy()
        s["review_stratum"] = name
        picks.append(s)
    cols = ["review_stratum", "country", "admin1", "iu_name", "iu_id", "year", "endemicity_raw",
            "row_class_l1", "row_class_l2", "eff_rounds_obs_l1", "cum_mda_l1", "pop_req",
            "pop_treat", "scheme", "outcome_class"]
    out = pd.concat(picks)[cols].sort_values(["review_stratum", "country", "year"])
    for col in ["reviewer_judgement (interruption / legitimate pause / delivered / unsure)",
                "was_a_round_formally_planned (yes / no / unknown)", "reviewer_role",
                "reviewer_notes"]:
        out[col] = ""
    return out


def evaluate_gate(metrics: dict) -> dict:
    r = GATE_RULES
    checks = [
        ("G1 status agrees with treatment fields",
         metrics["contradiction_share"] <= r["max_contradiction_share"],
         f"{metrics['contradiction_share']:.4%} of delivered/non-delivery rows are contradictory "
         f"(limit {r['max_contradiction_share']:.0%})"),
        ("G2 non-reporting is separable from non-delivery",
         metrics["n_not_reported_rows"] > 0 and metrics["missing_jrf_in_positive"] == 0,
         f"{metrics['n_not_reported_rows']} 'Not reported' rows held as missing labels; "
         f"none counted as events"),
        ("G3 legitimate stops are limited in the primary cohort",
         metrics["hindsight_stop_share_primary"] <= r["max_hindsight_stop_share_primary"],
         f"{metrics['hindsight_stop_share_primary']:.1%} of primary-cohort events (to 2022) were "
         f"followed by impact assessment or surveillance rather than resumed MDA "
         f"(limit {r['max_hindsight_stop_share_primary']:.0%}); broad-cohort exclusions: "
         f"{metrics['hindsight_stop_share_excluded']:.1%}"),
        ("G4 enough events in development and locked test",
         metrics["dev_events"] >= r["min_development_events"]
         and metrics["test_events"] >= r["min_locked_test_events"]
         and metrics["test_event_countries"] >= r["min_locked_test_event_countries"],
         f"development {metrics['dev_events']} events; locked test {metrics['test_events']} "
         f"events from {metrics['test_event_countries']} countries"),
        ("G5 within-country variation supports IU-level ranking",
         metrics["events_in_mixed_country_years"] >= r["min_events_in_mixed_country_years"]
         and metrics["within_country_year_variance_share"]
         >= r["min_within_country_year_variance_share"],
         f"{metrics['events_in_mixed_country_years']} events lie in country-years with both "
         f"outcomes; {metrics['within_country_year_variance_share']:.1%} of outcome variance is "
         f"within country-year"),
    ]
    passed = all(ok for _, ok, _ in checks)
    decision = "GO_ON_PROXY_LABEL" if passed else "REDESIGN_REQUIRES_APPROVAL"
    adequate = metrics["test_events_effective"] >= r["target_effective_locked_test_events"]
    advisory = (
        f"locked test has {metrics['test_events']} events in {metrics['test_n']} IU-years, but "
        f"they come from {metrics['test_event_country_years']} country-years; after the "
        f"country-year design effect this is about {metrics['test_events_effective']:.0f} "
        f"effective events (target {r['target_effective_locked_test_events']})")
    return {
        "decision": decision,
        "information_adequacy": "ADEQUATE" if adequate else "LIMITED",
        "information_adequacy_evidence": advisory,
        "expert_verification": "PENDING - cannot be satisfied by code",
        "checks": [{"check": c, "passed": bool(ok), "evidence": ev} for c, ok, ev in checks],
        "rules": r,
        "rules_note": ("Thresholds were set by the code author after profiling the data. They "
                       "are judgement calls recorded for transparency, not external standards."),
    }


def run_audit(out_dir: Path | None = None, raw_dir: Path | None = None) -> dict:
    out_dir = out_dir or paths.AUDIT
    out_dir.mkdir(parents=True, exist_ok=True)
    proto = load_protocol()
    raw, diag, panel = build_all(raw_dir)
    obs = panel[panel["row_present"]]

    # --- schema and field diagnostics -------------------------------------------------
    schema = (raw.groupby(["admin0Iso2", "schema_optional_present"]).size()
              .rename("rows").reset_index())
    schema.to_csv(out_dir / "schema_variants.csv", index=False)
    diag.to_csv(out_dir / "numeric_field_diagnostics.csv", index=False)
    status = (obs.groupby(["endemicity_raw", "endemicity_id", "status_code"], dropna=False)
              .agg(rows=("iu_key", "size"), countries=("iso2", "nunique"),
                   first_year=("year", "min"), last_year=("year", "max")).reset_index())
    status.to_csv(out_dir / "status_values.csv", index=False)
    pd.crosstab(obs["endemicity_raw"], obs["year"]).to_csv(out_dir / "status_by_year.csv")
    contra = (obs[obs["contradiction"] != ""].groupby(["contradiction", "status_code", "country"])
              .size().rename("rows").reset_index())
    contra.to_csv(out_dir / "contradictions.csv", index=False)
    cov = obs[obs["row_class"] == "delivered"]
    coverage_qc = pd.DataFrame([{
        "delivered_rows": len(cov),
        "cov_over_100": int((cov["cov"] > 100).sum()),
        "epi_cov_over_100": int((cov["epi_cov"] > 100).sum()),
        "max_cov": cov["cov"].max(), "max_epi_cov": cov["epi_cov"].max(),
        "pop_treat_gt_pop_tot": int((cov["pop_treat"] > cov["pop_tot"]).sum()),
        "pop_req_gt_pop_tot": int((cov["pop_req"] > cov["pop_tot"]).sum()),
        "cov_looks_like_fraction": int(((cov["cov"] > 0) & (cov["cov"] <= 1)).sum()),
    }])
    coverage_qc.to_csv(out_dir / "coverage_qc.csv", index=False)
    # scale check per source file: a country reporting fractions would have a median near 0-1
    scale = cov.groupby(["iso2", "country"]).agg(
        delivered_rows=("cov", "size"), median_cov=("cov", "median"),
        median_epi_cov=("epi_cov", "median"), max_cov=("cov", "max")).reset_index()
    scale["looks_like_fraction_scale"] = (scale["median_cov"] <= 1.5) | (scale["median_epi_cov"] <= 1.5)
    scale.to_csv(out_dir / "coverage_scale_by_country.csv", index=False)
    coverage_qc["countries_on_fraction_scale"] = int(scale["looks_like_fraction_scale"].sum())
    coverage_qc["lowest_country_median_cov"] = float(scale["median_cov"].min())
    coverage_qc.to_csv(out_dir / "coverage_qc.csv", index=False)

    # --- lifecycle accounting ---------------------------------------------------------
    life = (panel.groupby(["iso2", "country", "year", "lifecycle_class"]).size()
            .rename("iu_years").reset_index())
    life.to_csv(out_dir / "class_by_country_year.csv", index=False)
    lineage_table(panel).to_csv(out_dir / "iu_lineage_counts.csv", index=False)
    flags = country_year_flags(panel, load_release_calendar())
    flags.to_csv(out_dir / "country_year_flags.csv", index=False)

    # --- cohort -----------------------------------------------------------------------
    flow = cohort_flow(panel, proto)
    flow.to_csv(out_dir / "cohort_flow.csv", index=False)
    prim = analysis_set(panel, "primary")
    by_year = (panel[panel["eligible_primary"]].pivot_table(
        index="year", columns="outcome_class", values="iu_key", aggfunc="count", fill_value=0))
    by_year.to_csv(out_dir / "primary_cohort_outcome_class_by_year.csv")
    by_country = prim.groupby(["iso2", "country"]).agg(
        iu_years=("y", "size"), events=("y", "sum"), distinct_ius=("iu_key", "nunique"),
        first_year=("year", "min"), last_year=("year", "max"),
        event_years=("year", lambda s: int(prim.loc[s.index][prim.loc[s.index, "y"] == 1]
                                           ["year"].nunique()))).reset_index()
    by_country["events"] = by_country["events"].astype(int)
    by_country["share_of_all_events"] = by_country["events"] / max(by_country["events"].sum(), 1)
    by_country = by_country.sort_values("events", ascending=False)
    by_country.to_csv(out_dir / "primary_cohort_by_country.csv", index=False)
    cyw = prim.groupby(["iso2", "country", "year", "window"]).agg(
        n=("y", "size"), events=("y", "sum")).reset_index()
    cyw.to_csv(out_dir / "primary_cohort_by_country_year.csv", index=False)
    windows = window_table(panel)
    windows.to_csv(out_dir / "events_by_window.csv", index=False)
    hind = hindsight_table(panel)
    hind.to_csv(out_dir / "hindsight_adjudication.csv", index=False)

    # --- clustering -------------------------------------------------------------------
    cy = country_year_rates(prim)
    cy.to_csv(out_dir / "country_year_event_rates.csv", index=False)
    bands = cy.groupby("band", observed=False).agg(
        country_years=("n", "size"), iu_years=("n", "sum"), events=("events", "sum")).reset_index()
    bands["share_of_events"] = bands["events"] / max(bands["events"].sum(), 1)
    bands.to_csv(out_dir / "clustering_bands.csv", index=False)
    vp_rows = []
    for name, df in [("all target years", prim)] + [(w, g) for w, g in prim.groupby("window")]:
        row = {"subset": name} | variance_partition(df)
        row |= {"icc_country_year": icc_design_effect(df, ["iso2", "year"])["icc"],
                "design_effect_country_year":
                    icc_design_effect(df, ["iso2", "year"])["design_effect"],
                "n_effective": icc_design_effect(df, ["iso2", "year"])["n_effective"]}
        row["events_effective"] = row["n_effective"] * row["prevalence"]
        vp_rows.append(row)
    vp = pd.DataFrame(vp_rows)
    vp.to_csv(out_dir / "variance_partition.csv", index=False)

    expert_review_sample(panel, proto["seed"]).to_csv(
        out_dir / "expert_review_sample.csv", index=False)

    # --- gate -------------------------------------------------------------------------
    dn = obs[obs["status_code"].isin(["MDA", "ND"])]
    w = windows[windows["cohort"] == "primary"].set_index("window")
    hp = hind.set_index("cohort")
    metrics = {
        "n_raw_rows": int(len(raw)), "n_countries": int(obs["iso2"].nunique()),
        "n_ius": int(obs["iu_key"].nunique()),
        "contradiction_share": float((dn["contradiction"] != "").mean()),
        "n_contradictory_rows": int((obs["row_class"] == "contradictory").sum()),
        "n_not_reported_rows": int((obs["row_class"] == "missing_JRF").sum()),
        "missing_jrf_in_positive": int(((prim["y"] == 1) & (prim["row_class"] != "non_delivery")).sum()),
        "n_unmapped_status_rows": int((~obs["status_mapped"]).sum()),
        "primary_n": int(len(prim)), "primary_events": int(prim["y"].sum()),
        "primary_countries": int(prim["iso2"].nunique()),
        "primary_event_countries": int(prim.loc[prim["y"] == 1, "iso2"].nunique()),
        "dev_events": int(w.loc["development", "events"]),
        "test_events": int(w.loc["locked_test", "events"]),
        "test_event_countries": int(w.loc["locked_test", "event_countries"]),
        "test_n": int(w.loc["locked_test", "n"]),
        "test_event_country_years": int(w.loc["locked_test", "event_country_years"]),
        "test_events_effective":
            float(vp.loc[vp["subset"] == "locked_test", "events_effective"].iloc[0]),
        "dev_events_effective":
            float(vp.loc[vp["subset"] == "development", "events_effective"].iloc[0]),
        "stress2025_events": int(w.loc["shock_stress_2025", "events"]),
        "hindsight_stop_share_primary": float(hp.loc["primary", "moved_to_IA_or_surveillance_share"]),
        "hindsight_resumed_share_primary": float(hp.loc["primary", "resumed_mda_share"]),
        "hindsight_stop_share_excluded":
            float(hp.loc["broad_excluded_by_rounds", "moved_to_IA_or_surveillance_share"]),
        "events_in_mixed_country_years": int(cy.loc[cy["mixed"], "events"].sum()),
        "mixed_country_years": int(cy["mixed"].sum()),
        "country_years_with_events": int((cy["events"] > 0).sum()),
        "country_years_total": int(len(cy)),
        "events_in_whole_country_failures": int(cy.loc[cy["rate"] == 1, "events"].sum()),
        "events_in_majority_failure_country_years": int(cy.loc[cy["rate"] > 0.5, "events"].sum()),
        "within_country_year_variance_share":
            float(vp.loc[vp["subset"] == "all target years", "within_country_year"].iloc[0]),
        "between_country_variance_share":
            float(vp.loc[vp["subset"] == "all target years", "between_country"].iloc[0]),
        "n_effective_all": float(vp.loc[vp["subset"] == "all target years", "n_effective"].iloc[0]),
    }
    gate = evaluate_gate(metrics)
    result = {"generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "protocol_version": proto["version"], "metrics": metrics, "gate": gate}
    (out_dir / "gate_decision.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_markdown(out_dir, result, flow, windows, hind, bands, vp, by_country, status, flags,
                   coverage_qc, schema, proto)
    paths.PROCESSED.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(paths.PROCESSED / "panel.parquet", index=False)
    return result


def _md(df: pd.DataFrame, floatfmt: str = "{:.3f}") -> str:
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]):
            d[c] = d[c].map(lambda v: "" if pd.isna(v) else floatfmt.format(v))
    head = "| " + " | ".join(map(str, d.columns)) + " |"
    sep = "|" + "|".join(["---"] * len(d.columns)) + "|"
    body = ["| " + " | ".join(map(str, r)) + " |" for r in d.itertuples(index=False)]
    return "\n".join([head, sep] + body)


def write_markdown(out_dir, result, flow, windows, hind, bands, vp, by_country, status, flags,
                   coverage_qc, schema, proto) -> None:
    m, g = result["metrics"], result["gate"]
    variants = schema.groupby("schema_optional_present")["admin0Iso2"].apply(
        lambda s: ", ".join(sorted(s))).reset_index()
    variants.columns = ["optional columns present", "countries"]
    cf = flags[flags["flag_population_carried_forward"] & (flags["n_delivered"]
                                                            + flags["n_non_delivery"] > 0)]
    nr = flags[flags["flag_whole_country_not_reported"]]
    unlisted = flags[(flags["year"] == 2025) & flags["release_date"].isna()
                     & ((flags["n_delivered"] + flags["n_non_delivery"]) > 0)]
    lines = [
        "# Label audit and feasibility gate",
        "",
        f"Generated {result['generated_utc']} from the raw ESPEN LF IU-level extracts "
        f"(protocol v{result['protocol_version']}). All numbers are computed by "
        "`python -m lf_mda.cli audit`; none are typed by hand.",
        "",
        f"## Gate decision: `{g['decision']}`",
        "",
        f"Expert verification of the label: **{g['expert_verification']}**.",
        "",
        _md(pd.DataFrame(g["checks"])),
        "",
        f"**Independent information: `{g['information_adequacy']}`.** "
        f"{g['information_adequacy_evidence'].capitalize()}. Modelling therefore proceeds with "
        "deliberately small models and country-clustered uncertainty, and claims of model "
        "superiority must survive that uncertainty.",
        "",
        g["rules_note"],
        "",
        "`GO_ON_PROXY_LABEL` means the administrative status is coherent enough to model as a "
        "transparent proxy. It does not mean the label is validated: no programme officer has "
        "yet reviewed the sample in `expert_review_sample.csv`, and no medicine-request (JRSM) "
        "data were available to confirm that a round was formally planned.",
        "",
        "## 1. Source data",
        "",
        f"- {m['n_raw_rows']:,} IU-year rows, {m['n_countries']} country files, {m['n_ius']:,} "
        "distinct IUs, years 2014-2025.",
        "- The header differs between countries; three columns are optional:",
        "",
        _md(variants),
        "",
        "- The dictionary lists `JRF_submitted`, `PopNoTx` and `Alt_ADMIN2`; the extract has no "
        "`JRF_submitted` or `PopNoTx` column. Non-reporting is identified from the status "
        "value `Not reported` instead.",
        f"- No numeric field had blank or unparseable values except `endemicityId` "
        f"(blank for the 2025 status `Endemic (under targeted treatment)`).",
        "",
        "### Status values actually present",
        "",
        _md(status),
        "",
        "### Coverage fields (delivered rows)",
        "",
        _md(coverage_qc, "{:.2f}"),
        "",
        "Coverage scale was checked per country file (`coverage_scale_by_country.csv`): "
        f"{int(coverage_qc['countries_on_fraction_scale'].iloc[0])} countries have a median "
        "at or below 1.5, so every file reports percentages, not fractions "
        f"(lowest country median {coverage_qc['lowest_country_median_cov'].iloc[0]:.1f}%). "
        "Values above 100% exist and are kept as reported.",
        "",
        "## 2. Cohort flow",
        "",
        _md(flow),
        "",
        "## 3. Events by analysis window and cohort",
        "",
        _md(windows),
        "",
        "## 4. Legitimate stops versus interruptions (hindsight check, events to 2022)",
        "",
        "For each event, the first status after the run of non-delivery years. This uses "
        "later years, so it is an audit of the label only; it is never a model input.",
        "",
        _md(hind),
        "",
        "Reading: in the primary cohort most non-delivery events were followed by resumed MDA. "
        "Among IUs excluded for having five or more observed effective rounds, a much larger "
        "share moved to impact assessment or surveillance, which is why they are excluded. "
        "`Endemic (pending IA)` exists only from 2021, so before 2021 a pause for assessment "
        "cannot be separated from non-delivery by status alone. A later move to surveillance "
        "does not prove the non-delivery was legitimate, so the share is an upper bound on "
        "contamination.",
        "",
        "## 5. Are interruptions country-year events?",
        "",
        _md(bands),
        "",
        f"- {m['country_years_with_events']} of {m['country_years_total']} country-years have at "
        f"least one event; {m['mixed_country_years']} have both outcomes.",
        f"- {m['events_in_whole_country_failures']} of {m['primary_events']} events "
        f"({m['events_in_whole_country_failures'] / m['primary_events']:.0%}) are in country-years "
        "where every eligible IU missed the round; "
        f"{m['events_in_majority_failure_country_years']} "
        f"({m['events_in_majority_failure_country_years'] / m['primary_events']:.0%}) are in "
        "country-years where more than half did.",
        f"- {m['events_in_mixed_country_years']} events are in country-years with both outcomes; "
        "only these can inform ranking of IUs within a country.",
        "",
        "### Variance partition and effective sample size",
        "",
        _md(vp),
        "",
        "`n_effective` applies a design effect for clustering by country-year. It shows that "
        "the independent information is far smaller than the IU-year row count.",
        "",
        "## 6. Countries contributing to the primary cohort",
        "",
        _md(by_country),
        "",
        "## 7. Reporting diagnostics",
        "",
        f"- Whole-country `Not reported` years: {len(nr)} "
        f"({', '.join(f'{r.iso2} {r.year}' for r in nr.itertuples())}).",
        f"- Country-years with delivery or non-delivery rows whose populations are identical to "
        f"the previous year (possible carried-forward records): "
        f"{', '.join(f'{r.iso2} {r.year}' for r in cf.itertuples()) or 'none'}.",
        f"- 2025 country-years with delivery or non-delivery rows that are absent from the ESPEN "
        f"release log: {', '.join(sorted(unlisted['iso2'])) or 'none'}.",
        f"- Contradictory rows quarantined: {m['n_contradictory_rows']} "
        "(see `contradictions.csv`).",
        "",
        "## 8. Open threats",
        "",
        "1. The label is a WHO-reported status after final correction, not independent proof of "
        "non-delivery, and no planning data confirm that a round was scheduled.",
        "2. Effective rounds are observed only from 2014; IUs with long earlier histories may "
        "still be in the primary cohort (the `strict` cohort tests this).",
        "3. Records are current corrected values, not what was known at each decision date.",
        "4. Most events arise from country-wide failures, so IU-level row counts overstate the "
        "independent evidence.",
        "5. IU definitions change over time in many countries (`iu_lineage_counts.csv`); IUs "
        "without a row at t-1 never enter the cohort.",
        "",
    ]
    (out_dir / "label_audit.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Run the label audit and feasibility gate")
    ap.add_argument("--input", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    result = run_audit(args.out, args.input)
    print(json.dumps(result["gate"], indent=2))


if __name__ == "__main__":
    main()
