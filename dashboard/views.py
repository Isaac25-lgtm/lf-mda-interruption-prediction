"""Dashboard pages. Each function renders one page from stored artifacts only."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import lib
from lib import (AQUA, BLUE, GREY, MAP_COLOR, METRIC_LABEL, MODEL_COLOR, MODEL_LABEL, ORANGE,
                 SEQ_BLUE, banner, capture_summary, fmt_ci, load_info, load_iu_year, read_csv,
                 stored_models, style)

REPO_URL = "https://github.com/Isaac25-lgtm/lf-mda-interruption-prediction"
KEY_MODELS = ["country_prior_rate", "history_rule", "logistic_history", "catboost_history"]


def header(title: str, lead: str) -> None:
    st.title(title)
    st.caption(lead)
    banner()


def label(m: str) -> str:
    return MODEL_LABEL.get(m, m)


def missing(what: str) -> None:
    st.info(f"{what} is not available in this build. Run the pipeline "
            "(`lf-mda all`) to generate it.")


# ------------------------------------------------------------------ 1. overview
def page_overview() -> None:
    header("Predicting interruptions of lymphatic filariasis mass drug administration",
           "A multi-country feasibility audit and prediction study using public WHO ESPEN "
           "implementation-unit data, 2014-2025.")
    info, df = load_info(), load_iu_year()
    m = info.get("metrics", {})
    if m:
        c = st.columns(5)
        c[0].metric("Country files", f"{m['n_countries']}")
        c[1].metric("Implementation units", f"{m['n_ius']:,}")
        c[2].metric("IU-years in cohort", f"{m['primary_n']:,}")
        c[3].metric("Reported interruptions", f"{m['primary_events']:,}")
        c[4].metric("Countries with events", f"{m['primary_event_countries']}")
        st.markdown(
            f"**Feasibility gate:** `{info['gate_decision']}` · **Independent information:** "
            f"`{info['information_adequacy']}` · **Expert label review:** pending · "
            f"ESPEN data retrieved {info['espen_retrieved_utc'][:10]}")
    st.subheader("Where and when rounds were reported as not delivered")
    cy = read_csv("dashboard/data/country_year.csv")
    if cy is None:
        cy = (df[df["cohort_status"] == "In primary cohort"].groupby(["iso2", "country", "year"])
              .agg(eligible_ius=("y", "size"), interruptions=("y", "sum")).reset_index())
        cy["interruption_rate"] = cy["interruptions"] / cy["eligible_ius"]
        cy["iso3"] = None
    left, right = st.columns([3, 2])
    with left:
        year = st.select_slider("Year", sorted(cy["year"].unique()),
                                value=int(cy["year"].max()), key="ov_year")
        sub = cy[cy["year"] == year]
        if sub["iso3"].notna().any():
            fig = px.choropleth(
                sub, locations="iso3", color="interruption_rate", scope="africa",
                color_continuous_scale=SEQ_BLUE, range_color=(0, 1),
                hover_name="country",
                hover_data={"iso3": False, "eligible_ius": True, "interruptions": True,
                            "interruption_rate": ":.0%"},
                labels={"interruption_rate": "Share interrupted",
                        "eligible_ius": "Eligible IUs", "interruptions": "Interruptions"})
            fig.update_geos(showcountries=True, countrycolor="#b9b8b2", showland=True,
                            landcolor="#f0efec", bgcolor="rgba(0,0,0,0)", showframe=False,
                            projection_type="natural earth", fitbounds=False,
                            lataxis_range=[-36, 38], lonaxis_range=[-20, 53])
            fig.update_layout(coloraxis_colorbar=dict(tickformat=".0%", title="Interrupted"))
            st.plotly_chart(style(fig, 520, legend_bottom=False), width="stretch")
            st.caption("Countries in grey had no IU in the active-programme cohort that year. "
                       "Colour is the share of eligible IUs with a reported interruption.")
        else:
            st.dataframe(sub, width="stretch", hide_index=True)
    with right:
        st.markdown(f"**{year}: countries with eligible IUs**")
        t = sub.sort_values("interruption_rate", ascending=False)[
            ["country", "eligible_ius", "interruptions", "interruption_rate"]].copy()
        t["interruptions"] = t["interruptions"].astype(int)
        st.dataframe(
            t, hide_index=True, width="stretch", height=470,
            column_config={"country": "Country", "eligible_ius": "Eligible IUs",
                           "interruptions": "Interruptions",
                           "interruption_rate": st.column_config.ProgressColumn(
                               "Share interrupted", format="percent", min_value=0, max_value=1)})
    if m:
        st.subheader("What the audit found")
        whole = m["events_in_whole_country_failures"] / m["primary_events"]
        st.markdown(
            f"- **Interruptions are largely country-level events.** {whole:.0%} of reported "
            f"interruptions happened in country-years where every eligible IU missed the "
            f"round, and {m['between_country_variance_share'] + 0:.0%} of outcome variance lies "
            f"between countries alone ({1 - m['within_country_year_variance_share']:.0%} between "
            f"country-years).\n"
            f"- **Row counts overstate the evidence.** The locked test has "
            f"{m['test_events']} events, but they come from {m['test_event_country_years']} "
            f"country-years.\n"
            f"- **The label is a proxy.** In the cohort, "
            f"{m['hindsight_resumed_share_primary']:.0%} of non-delivery events were followed by "
            f"resumed MDA and {m['hindsight_stop_share_primary']:.0%} by impact assessment or "
            f"surveillance, which may have been legitimate stops.")
    st.caption(f"Code, protocol and full audit: {REPO_URL}")


# ------------------------------------------------------------------ 2. data quality
def page_quality() -> None:
    header("Data quality", "What the raw ESPEN extracts contain and how the cohort was built.")
    flow = read_csv("reports/audit/cohort_flow.csv")
    status = read_csv("reports/audit/status_by_year.csv")
    if flow is None or status is None:
        return missing("The label audit")
    a, b = st.columns([3, 2])
    with a:
        st.subheader("Reported status by year, all IUs")
        long = status.melt("endemicity_raw", var_name="year", value_name="IUs")
        order = long.groupby("endemicity_raw")["IUs"].sum().sort_values(ascending=False).index
        palette = dict(zip(order, [lib.LIGHT, BLUE, "#6da7ec", ORANGE, GREY, AQUA, "#3d3d3a",
                                   "#c9c8c2"]))
        fig = px.bar(long, x="year", y="IUs", color="endemicity_raw",
                     category_orders={"endemicity_raw": list(order)},
                     color_discrete_map=palette)
        fig.update_traces(marker_line_color="rgba(252,252,251,1)", marker_line_width=1.5)
        st.plotly_chart(style(fig, 430), width="stretch")
        st.caption("'Endemic (pending IA)' appears only from 2021. Before then a pause for "
                   "impact assessment cannot be told apart from non-delivery by status alone.")
    with b:
        st.subheader("Cohort flow")
        st.dataframe(flow, hide_index=True, width="stretch", height=470,
                     column_config={"step": "Step", "n": st.column_config.NumberColumn(
                         "IU-years", format="localized")})
    st.subheader("Reporting gaps and inconsistencies")
    t1, t2, t3, t4 = st.tabs(["Not-reported country-years", "Contradictory rows",
                              "File schema variants", "ESPEN release dates"])
    flags = read_csv("reports/audit/country_year_flags.csv")
    with t1:
        if flags is not None:
            nr = flags[flags["n_not_reported"] > 0][["country", "year", "n_iu",
                                                     "n_not_reported"]]
            st.dataframe(nr.sort_values(["year", "country"]), hide_index=True, width="stretch")
            st.caption("A 'Not reported' year is a missing label. It is never counted as an "
                       "interruption.")
    with t2:
        c = read_csv("reports/audit/contradictions.csv")
        if c is not None:
            st.dataframe(c.sort_values("rows", ascending=False), hide_index=True,
                         width="stretch")
            st.caption("Rows whose status disagrees with the treatment fields are quarantined "
                       "and never become outcome labels.")
    with t3:
        s = read_csv("reports/audit/schema_variants.csv")
        if s is not None:
            v = (s.groupby("schema_optional_present", dropna=False)["admin0Iso2"]
                 .apply(lambda x: ", ".join(sorted(x))).reset_index())
            v.columns = ["Optional columns present", "Countries"]
            st.dataframe(v, hide_index=True, width="stretch")
    with t4:
        cal = read_csv("config/source_release_calendar.csv")
        if cal is not None:
            st.dataframe(cal[["data_year", "country_as_listed", "release_date",
                              "release_type"]], hide_index=True, width="stretch")
            st.caption("Data for a year became public 8 to 17 months after year-end. This is "
                       "why the public-data scenario lags predictors by two years.")


# ------------------------------------------------------------------ 3. IU map
def page_map() -> None:
    header("Implementation-unit map",
           "One point per implementation unit at its centroid. Points show reported status, "
           "not verified events.")
    df = load_iu_year()
    c1, c2, c3 = st.columns([1, 2, 2])
    year = c1.selectbox("Year", sorted(df["year"].unique(), reverse=True), key="map_year")
    countries = ["All countries"] + sorted(df["country"].dropna().unique())
    country = c2.selectbox("Country", countries, key="map_country")
    groups = [g for g in MAP_COLOR if g != "Non-endemic"]
    show = c3.multiselect("Show", list(MAP_COLOR), default=groups, key="map_groups")
    d = df[(df["year"] == year) & df["map_group"].isin(show)]
    if country != "All countries":
        d = d[d["country"] == country]
    no_geo = int(d["lat"].isna().sum())
    d = d.dropna(subset=["lat", "lon"])
    if d.empty:
        st.info("No implementation units with coordinates match this selection.")
        return
    fig = px.scatter_geo(
        d, lat="lat", lon="lon", color="map_group", color_discrete_map=MAP_COLOR,
        category_orders={"map_group": list(MAP_COLOR)}, hover_name="iu_name",
        hover_data={"country": True, "admin1": True, "display_class": True,
                    "cohort_status": True, "lat": False, "lon": False, "map_group": False},
        labels={"display_class": "Status", "cohort_status": "Cohort", "admin1": "Region",
                "country": "Country"})
    fig.update_traces(marker=dict(size=7 if country != "All countries" else 5,
                                  line=dict(width=0.6, color="rgba(252,252,251,0.9)")))
    fig.update_geos(showcountries=True, countrycolor="#b9b8b2", showland=True,
                    landcolor="#f0efec", bgcolor="rgba(0,0,0,0)", showframe=False,
                    showcoastlines=False, projection_type="natural earth")
    if country == "All countries":
        fig.update_geos(lataxis_range=[-36, 38], lonaxis_range=[-20, 53])
    else:
        fig.update_geos(fitbounds="locations")
    st.plotly_chart(style(fig, 620), width="stretch")
    counts = d["map_group"].value_counts().reindex(list(MAP_COLOR)).dropna().astype(int)
    st.dataframe(counts.rename("IUs").rename_axis("Group").reset_index(), hide_index=True,
                 width="stretch")
    note = ("Centroids are derived from ESPEN's 2024 provisional cartography; boundaries "
            "that changed over time are shown at their 2024 position.")
    if no_geo:
        note += (f" {no_geo:,} units in this selection have no geometry in that cartography "
                 f"and are not drawn.")
    st.caption(note)


# ------------------------------------------------------------------ 4. risk explorer
def page_risk() -> None:
    header("Risk explorer",
           "Stored out-of-sample scores for IUs in the active-programme cohort.")
    df = load_iu_year()
    models = stored_models(df)
    if not models:
        return missing("Stored predictions")
    d = df[df["prediction_source"] != "No stored prediction"]
    c1, c2, c3 = st.columns([1, 2, 2])
    year = c1.selectbox("Target year", sorted(d["year"].unique(), reverse=True), key="rk_year")
    d = d[d["year"] == year]
    country = c2.selectbox("Country", ["All countries"] + sorted(d["country"].unique()),
                           key="rk_country")
    default = models.index("logistic_history") if "logistic_history" in models else 0
    model = c3.selectbox("Approach", models, index=default, format_func=label, key="rk_model")
    if country != "All countries":
        d = d[d["country"] == country]
    src = ", ".join(sorted(d["prediction_source"].unique()))
    st.markdown(
        f"**What 'risk' means here.** For each IU the score was produced by a model fitted "
        f"only on earlier years and never on this year's outcomes ({src}). It estimates the "
        f"chance that ESPEN later records 'MDA not delivered' for {year}. It is not a "
        f"statement about why, and most of the signal comes from the country, not the district.")
    has_p = d[f"p_{model}"].notna()
    t = d.loc[has_p, ["country", "admin1", "iu_name", f"p_{model}", f"r_{model}",
                      "display_class", "row_class_l1"]].copy()
    t["row_class_l1"] = t["row_class_l1"].map({"delivered": "Delivered",
                                               "non_delivery": "Not delivered"})
    t = t.sort_values(f"r_{model}", ascending=False).reset_index(drop=True)
    t.insert(0, "rank", np.arange(1, len(t) + 1))
    t = t.drop(columns=f"r_{model}").rename(columns={
        "admin1": "Region", "iu_name": "Implementation unit", f"p_{model}": "Predicted risk",
        "display_class": f"Reported status in {year}", "row_class_l1": "Status the year before",
        "country": "Country", "rank": "Rank"})
    a, b = st.columns([3, 2])
    with a:
        st.dataframe(t, hide_index=True, width="stretch", height=520, column_config={
            "Predicted risk": st.column_config.ProgressColumn(format="percent", min_value=0,
                                                              max_value=1)})
    with b:
        lab = d[has_p & d["y"].notna()]
        if lab["y"].nunique() == 2:
            fig = go.Figure()
            for val, name, color in ((0, "Delivered", BLUE), (1, "Reported interruption", ORANGE)):
                fig.add_histogram(x=lab.loc[lab["y"] == val, f"p_{model}"], name=name,
                                  marker_color=color, xbins=dict(start=0, end=1, size=0.05),
                                  opacity=0.85)
            fig.update_layout(barmode="stack", title="Predicted risk by what was reported",
                              xaxis_title="Predicted risk", yaxis_title="IUs",
                              xaxis_tickformat=".0%")
            st.plotly_chart(style(fig, 360), width="stretch")
        st.metric("IUs with a stored score", f"{int(has_p.sum()):,}")
        if len(lab):
            st.metric("Reported interruptions among them", f"{int(lab['y'].sum()):,}")
        st.caption("Scores for 2019-2022 are out-of-fold development predictions and were used "
                   "to choose models; only 2023-2024 form the locked test.")


# ------------------------------------------------------------------ 5. model comparison
def _interval_tables():
    lock = read_csv("reports/evaluation/locked_test/locked_intervals.csv")
    dev = read_csv("reports/evaluation/development/development_intervals.csv")
    return lock, dev


EVAL_LABEL = {"locked_test_2023_2024": "Locked test 2023-2024 (primary)",
              "stress_2025": "2025 stress year (robustness only)",
              "rolling_2019_2022": "Development folds 2019-2022",
              "non_covid_2019_2022": "Development folds, non-COVID years"}


def forest(ci: pd.DataFrame, metric: str, ref: float | None) -> go.Figure:
    sub = ci[ci["metric"] == metric]
    models = [m for m in MODEL_LABEL if m in set(sub["model"]) and m != "prevalence"]
    sub = sub.set_index("model").reindex(models)
    fig = go.Figure()
    for m in models:
        r = sub.loc[m]
        if pd.isna(r["estimate"]):
            continue
        err = None
        if not pd.isna(r["ci_low"]):
            err = dict(type="data", symmetric=False, array=[r["ci_high"] - r["estimate"]],
                       arrayminus=[r["estimate"] - r["ci_low"]], thickness=2, width=0)
        fig.add_scatter(x=[r["estimate"]], y=[label(m)], mode="markers", error_x=err,
                        marker=dict(size=11, color=MODEL_COLOR.get(m, GREY),
                                    line=dict(width=1.5, color="#fcfcfb")),
                        name=label(m), showlegend=False,
                        hovertemplate=f"{label(m)}<br>{fmt_ci(r['estimate'], r['ci_low'], r['ci_high'])}"
                                      "<extra></extra>")
    if ref is not None:
        fig.add_vline(x=ref, line_dash="dot", line_color=GREY)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_layout(title=METRIC_LABEL.get(metric, metric))
    return fig


def page_models() -> None:
    header("Model comparison",
           "Fixed baselines against logistic regression and CatBoost, with country-clustered "
           "uncertainty.")
    lock, dev = _interval_tables()
    if lock is None:
        return missing("Model evaluation")
    c1, c2 = st.columns(2)
    scen = c1.radio("Information scenario", ["P", "E"], horizontal=True, key="mc_scen",
                    format_func=lambda s: {"P": "P: programme knows last year's result",
                                           "E": "E: public ESPEN data only (two-year lag)"}[s])
    options = [k for k in EVAL_LABEL if k in set(lock["subset"]) | set(dev["subset"])]
    subset = c2.selectbox("Evaluation", options, format_func=EVAL_LABEL.get, key="mc_subset")
    src = lock if subset in set(lock["subset"]) else dev
    ci = src[(src["scenario"] == scen) & (src["subset"] == subset)]
    refs = {"auroc": 0.5, "within_country_year_auroc": 0.5, "capture_at_20pct": 0.2}
    cols = st.columns(3)
    for col, metric in zip(cols, refs):
        with col:
            fig = forest(ci, metric, refs[metric])
            fig.update_xaxes(range=[0, 1])
            st.plotly_chart(style(fig, 400, legend_bottom=False), width="stretch")
    n_cl = int(ci["n_clusters"].iloc[0]) if len(ci) else 0
    st.caption(f"Points are estimates; bars are 95% intervals from a bootstrap that resamples "
               f"whole countries ({n_cl} countries). Dotted lines mark no discrimination (0.5) "
               f"or chance capture (0.2). 'AUROC within country-year' compares IUs only with "
               f"other IUs in the same country and year.")
    wide = ci.assign(value=[fmt_ci(a, b, c) for a, b, c in
                            zip(ci["estimate"], ci["ci_low"], ci["ci_high"])])
    wide = wide[wide["metric"].isin(METRIC_LABEL)].pivot(index="model", columns="metric",
                                                         values="value")
    wide = wide.reindex([m for m in MODEL_LABEL if m in wide.index])
    wide.index = [label(m) for m in wide.index]
    wide = wide.rename(columns=METRIC_LABEL).rename_axis("Approach").reset_index()
    st.dataframe(wide, hide_index=True, width="stretch")
    diffs = read_csv("reports/evaluation/locked_test/locked_differences_vs_rule.csv")
    if diffs is not None and subset in set(diffs["subset"]):
        st.subheader("Does anything beat the history rule?")
        d = diffs[(diffs["scenario"] == scen) & (diffs["subset"] == subset)
                  & diffs["metric"].isin(["auroc", "within_country_year_auroc",
                                          "capture_at_10pct", "capture_at_20pct"])].copy()
        d["Approach"] = d["model"].map(label)
        d["Metric"] = d["metric"].map(METRIC_LABEL)
        d["Difference vs history rule (95% CI)"] = [
            fmt_ci(a, b, c, 3) for a, b, c in zip(d["difference"], d["ci_low"], d["ci_high"])]
        d["Interval excludes zero"] = np.where(d["interval_excludes_zero"], "Yes", "No")
        st.dataframe(d[["Approach", "Metric", "Difference vs history rule (95% CI)",
                        "Interval excludes zero"]], hide_index=True, width="stretch")
        n_yes = int(d["interval_excludes_zero"].sum())
        st.caption(f"{n_yes} of {len(d)} comparisons have an interval that excludes zero. A "
                   "gain is claimed only where it does, and the pre-specified threshold for a "
                   "meaningful gain is 5 percentage points more interruptions captured at 20% "
                   "capacity.")


# ------------------------------------------------------------------ 6. capacity
def page_capacity() -> None:
    header("Capacity prioritisation",
           "If a programme could give extra supervision to a fixed share of IUs, how many "
           "reported interruptions would each ranking have found?")
    df = load_iu_year()
    models = stored_models(df)
    if not models:
        return missing("Stored predictions")
    d = df[(df["prediction_source"] != "No stored prediction") & df["y"].notna()]
    c1, c2, c3 = st.columns([2, 2, 2])
    years = sorted(d["year"].unique())
    default_years = [y for y in years if y in (2023, 2024)] or years[-1:]
    sel_years = c1.multiselect("Target year(s)", years, default=default_years, key="cap_years")
    country = c2.selectbox("Country", ["All countries"] + sorted(d["country"].unique()),
                           key="cap_country")
    frac = c3.select_slider("Support capacity (share of eligible IUs)",
                            [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50], value=0.20,
                            format_func=lambda v: f"{v:.0%}", key="cap_frac")
    d = d[d["year"].isin(sel_years)]
    if country != "All countries":
        d = d[d["country"] == country]
    if d.empty or d["y"].sum() == 0:
        st.info("No reported interruptions in this selection, so capture cannot be computed.")
        return
    y = d["y"].to_numpy(dtype=float)
    show = [m for m in KEY_MODELS if m in models]
    rows = []
    for m in show:
        s = capture_summary(y, d[f"r_{m}"].to_numpy(dtype=float), frac)
        rows.append({"Approach": label(m), "IUs flagged": round(s["flagged"], 1),
                     "Interruptions captured": round(s["captured"], 1),
                     "Share of all interruptions": s["capture"], "Precision": s["precision"]})
    total, n = int(y.sum()), len(y)
    rows.append({"Approach": "Random selection (expected)", "IUs flagged": round(frac * n, 1),
                 "Interruptions captured": round(frac * total, 1),
                 "Share of all interruptions": frac, "Precision": total / n})
    k = st.columns(3)
    k[0].metric("Eligible IU-years", f"{n:,}")
    k[1].metric("Reported interruptions", f"{total:,}")
    k[2].metric("Countries", f"{d['country'].nunique()}")
    a, b = st.columns([3, 2])
    with a:
        fracs = np.linspace(0.02, 1, 50)
        fig = go.Figure()
        fig.add_scatter(x=[0, 1], y=[0, 1], mode="lines", name="Random selection",
                        line=dict(color=GREY, dash="dot", width=1.5))
        for m in show:
            cap = [capture_summary(y, d[f"r_{m}"].to_numpy(dtype=float), f)["capture"]
                   for f in fracs]
            fig.add_scatter(x=np.r_[0, fracs], y=np.r_[0, cap], mode="lines", name=label(m),
                            line=dict(color=MODEL_COLOR[m], width=2.5),
                            hovertemplate="%{x:.0%} flagged<br>%{y:.0%} captured")
        fig.add_vline(x=frac, line_color=GREY, line_width=1)
        fig.update_layout(title="Capture curve", xaxis_title="Share of eligible IUs flagged",
                          yaxis_title="Share of interruptions captured",
                          xaxis_tickformat=".0%", yaxis_tickformat=".0%",
                          hovermode="x unified")
        st.plotly_chart(style(fig, 430), width="stretch")
    with b:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", column_config={
            "Share of all interruptions": st.column_config.NumberColumn(format="percent"),
            "Precision": st.column_config.NumberColumn(format="percent")})
        st.caption("Computed from stored scores and reported outcomes. Tied scores are split "
                   "by expected value, so a rule with few distinct scores is not favoured or "
                   "penalised by row order.")
    if any(yr <= 2022 for yr in sel_years):
        st.info("The selection includes development years (2019-2022). Those scores were used "
                "to choose models, so capture there is optimistic. Only 2023-2024 are the "
                "locked test; 2025 is a stress year.")
    st.caption("This is a retrospective count. It does not show that flagging an IU would "
               "have prevented the interruption.")


# ------------------------------------------------------------------ 7. validation
def page_validation() -> None:
    header("Validation and uncertainty",
           "How stable the results are across countries, years, cohorts and label assumptions.")
    jk = read_csv("reports/evaluation/locked_test/locked_country_jackknife.csv")
    if jk is None:
        return missing("Validation output")
    t1, t2, t3, t4 = st.tabs(["Leave one country out of the test", "By year",
                              "Countries excluded from training", "Sensitivity analyses"])
    with t1:
        j = jk[(jk["scenario"] == "P") & (jk["subset"] == "locked_test_2023_2024")
               & jk["model"].isin(KEY_MODELS)].copy()
        j["Approach"] = j["model"].map(label)
        metric = st.radio("Metric", ["auroc", "capture_at_20pct", "within_country_year_auroc"],
                          format_func=METRIC_LABEL.get, horizontal=True, key="jk_metric")
        fig = px.strip(j, x=metric, y="Approach", color="Approach", hover_name="dropped_country",
                       hover_data={"dropped_events": True, "dropped_n": True, "Approach": False},
                       color_discrete_map={label(m): c for m, c in MODEL_COLOR.items()},
                       labels={metric: METRIC_LABEL[metric], "dropped_events": "Events removed",
                               "dropped_n": "IU-years removed"})
        fig.update_traces(marker=dict(size=9, opacity=0.75), jitter=0.5)
        fig.update_layout(showlegend=False)
        fig.update_xaxes(range=[0, 1])
        st.plotly_chart(style(fig, 360, legend_bottom=False), width="stretch")
        st.caption("Each point is the locked-test result with one country removed. A wide "
                   "spread means the headline number depends on one or two countries.")
    with t2:
        f = lib.FIGURES / "fig10_temporal_stability.png"
        if f.exists():
            st.image(str(f), width="stretch")
            st.caption("2019-2022 are development folds, 2023-2024 the locked test, 2025 the "
                       "stress year. Yearly values rest on few country-years.")
    with t3:
        tr = read_csv("reports/evaluation/country_transport/transport_by_country.csv")
        pooled = read_csv("reports/evaluation/country_transport/transport_pooled_intervals.csv")
        if tr is None:
            missing("Country transport output")
        else:
            st.markdown("Each country was predicted by models trained on **all other "
                        "countries** (development years 2016-2022, no country identity). This "
                        "tests transport across countries in the same calendar years. It is "
                        "not a future-year test.")
            if pooled is not None:
                p = pooled[pooled["metric"].isin(["auroc", "within_country_year_auroc",
                                                  "capture_at_20pct"])].copy()
                p["Approach"] = p["model"].map(label)
                p["Metric"] = p["metric"].map(METRIC_LABEL)
                p["Estimate (95% CI)"] = [fmt_ci(a, b, c) for a, b, c in
                                          zip(p["estimate"], p["ci_low"], p["ci_high"])]
                st.dataframe(p.pivot(index="Approach", columns="Metric",
                                     values="Estimate (95% CI)").reset_index(),
                             hide_index=True, width="stretch")
            s = tr[tr["supports_external_claim"] & tr["model"].isin(KEY_MODELS)].copy()
            s["Approach"] = s["model"].map(label)
            fig = px.scatter(s, x="auroc", y="country", color="Approach",
                             color_discrete_map={label(m): c for m, c in MODEL_COLOR.items()},
                             hover_data={"events": True, "n": True},
                             labels={"auroc": "AUROC in the held-out country", "country": ""})
            fig.add_vline(x=0.5, line_dash="dot", line_color=GREY)
            fig.update_traces(marker=dict(size=10, line=dict(width=1, color="#fcfcfb")))
            fig.update_xaxes(range=[0, 1])
            st.plotly_chart(style(fig, 440), width="stretch")
            st.caption(f"Only the {s['country'].nunique()} countries with at least 10 events "
                       "and 10 non-events are shown; for the others no external claim is made.")
    with t4:
        sens = read_csv("reports/evaluation/sensitivity/sensitivity_metrics.csv")
        if sens is None:
            missing("Sensitivity output")
        else:
            s = sens[sens["model"].isin(KEY_MODELS)].copy()
            s["Approach"] = s["model"].map(label)
            cols = ["analysis", "Approach", "countries", "n", "events", "auroc",
                    "within_country_year_auroc", "capture_at_20pct", "brier"]
            st.dataframe(s[cols].rename(columns=METRIC_LABEL | {
                "analysis": "Analysis", "countries": "Countries", "n": "IU-years",
                "events": "Events"}), hide_index=True, width="stretch", height=560,
                column_config={METRIC_LABEL[k]: st.column_config.NumberColumn(format="%.3f")
                               for k in ("auroc", "within_country_year_auroc",
                                         "capture_at_20pct", "brier")})
            st.caption("Point estimates only. These show direction and stability, not "
                       "confirmed differences.")


# ------------------------------------------------------------------ 8. methods
def page_methods() -> None:
    header("Methods", "How the study was designed, in brief. The repository holds the detail.")
    st.markdown(f"""
**Question.** Among implementation units (IUs) with an active LF treatment programme, can
information available at 31 December of year *t-1* identify the units that will have a
reported interruption in year *t*, and does anything beat a simple rule based on
treatment history?

**Data.** WHO ESPEN LF IU-level extracts for 2014-2025, downloaded for all 48 countries
on the public form. Conflict events come from UCDP GED 26.1. IU centroids and areas
come from ESPEN's 2024 provisional cartography.

**Cohort.** An IU-year is eligible when the IU required MDA in *t-1*, delivered a round
in *t-1* or *t-2*, and had fewer than five observed effective rounds (so another round,
not an impact assessment, was the expected next step). Eligibility uses only *t-1*
information.

**Outcome.** ESPEN status "Endemic (MDA not delivered)" versus "Endemic (under MDA)" in
year *t*. Pending impact assessment, surveillance, non-reporting and contradictory
records are excluded and counted; a missing report is never treated as an interruption.

**Predictors.** IU treatment history, country and region programme history, conflict and
population density. Scenario P uses records to *t-1*; scenario E to *t-2*, reflecting the
delay before ESPEN data are public. A test scrambles all later records and confirms no
predictor changes.

**Approaches.** No-skill prevalence, country prior-year rate, a fixed history rule,
penalised logistic regression and CatBoost with a small fixed grid.

**Validation.** Models are tuned on rolling-origin folds within 2016-2022. The 2023-2024
locked test is scored once. 2020-2021 (COVID-19) and 2025 (funding shock, incomplete
release) are reported as stress periods. Geographic transport is tested by leaving each
country out of training. Uncertainty comes from resampling whole countries.

**Reporting.** TRIPOD+AI items are tracked in `manuscript/tripod_ai_checklist.md`.

Full protocol: [`config/protocol.yaml`]({REPO_URL}/blob/main/config/protocol.yaml) ·
[label decisions]({REPO_URL}/blob/main/docs/LABEL_DECISIONS.md) ·
[decisions log]({REPO_URL}/blob/main/docs/DECISIONS.md)
""")
    f = lib.FIGURES / "fig1_decision_schematic.png"
    if f.exists():
        st.image(str(f), width="stretch")


# ------------------------------------------------------------------ 9. limitations
def page_limits() -> None:
    header("Limitations and citation", "Read this before quoting any number from this site.")
    st.markdown(f"""
### Limitations

1. **Unverified label.** The outcome is a reported status after WHO's final correction.
   No programme officer has reviewed it and no planning data confirm a round was scheduled.
2. **Legitimate stops.** Before 2021 ESPEN had no status for "pending impact assessment",
   so some pauses may be counted as interruptions. Restricting the cohort to IUs with fewer
   than five effective rounds reduces this but cannot remove it.
3. **Country-level shocks.** Most interruptions come from country-years in which most or
   all IUs missed the round. District-level row counts overstate the independent evidence,
   and intervals are wide.
4. **Hindsight data.** All records are current corrected values, not the values known at
   each decision date. This is a retrospective reconstruction, not a prospective trial.
5. **Programmes know more.** National programmes and partners hold funding and planning
   information (for example the ESPEN Implementation Unit Planner) that is not used here
   and is probably more informative than treatment history.
6. **Limited context data.** Rainfall and travel-time predictors from the concept were not
   used; conflict and population density were.
7. **No causal reading.** Model importance values describe associations inside a model.
   They are not reasons a programme missed a round.
8. **Not validated for use.** Nothing here has been tested prospectively or with users.

### Data sources and acknowledgement

- WHO Expanded Special Project for Elimination of Neglected Tropical Diseases (ESPEN),
  lymphatic filariasis implementation-unit data, 2014-2025, https://espen.afro.who.int.
  Underlying data were reported by national NTD programmes.
- Uppsala Conflict Data Program, Georeferenced Event Dataset version 26.1 (CC BY 4.0).

### How to cite

Omoding I. *lf-mda-interruption-prediction: feasibility audit and prediction of reported
lymphatic filariasis MDA interruptions using public WHO ESPEN data* (research software,
version 0.1.0, 2026). {REPO_URL}

This work has not been peer reviewed.
""")
