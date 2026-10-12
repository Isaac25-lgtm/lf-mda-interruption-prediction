"""Data loading and shared helpers for the dashboard. No model is trained or scored here."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lf_mda.evaluate import top_k_counts

DATA = ROOT / "dashboard" / "data"
REPORTS = ROOT / "reports"
AUDIT = REPORTS / "audit"
EVAL = REPORTS / "evaluation"
FIGURES = REPORTS / "figures"

INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
BLUE, ORANGE, AQUA, YELLOW, GREY, LIGHT = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100",
                                           "#8a8983", "#d9d8d2")
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

MODEL_LABEL = {
    "prevalence": "No-skill prevalence", "country_prior_rate": "Country prior rate",
    "history_rule": "History rule", "logistic_parsimonious": "Logistic, five predictors",
    "logistic_iu_only": "Logistic, IU history only",
    "logistic_history": "Logistic, programme history",
    "logistic_history_context": "Logistic, history + context",
    "catboost_history": "CatBoost, programme history",
    "catboost_history_context": "CatBoost, history + context",
    "catboost_history_country_id": "CatBoost, history + country ID",
}
MODEL_COLOR = {"history_rule": BLUE, "logistic_history": ORANGE, "catboost_history": AQUA,
               "country_prior_rate": YELLOW}
METRIC_LABEL = {
    "auroc": "AUROC", "within_country_year_auroc": "AUROC within country-year",
    "pr_auc": "PR-AUC", "capture_at_10pct": "Interruptions captured in top 10%",
    "capture_at_20pct": "Interruptions captured in top 20%", "brier": "Brier score",
    "precision_at_20pct": "Precision in top 20%", "log_loss": "Log loss",
}
MAP_GROUP = {
    "Delivered": "Delivered",
    "Reported interruption (unverified proxy)": "Reported interruption (unverified proxy)",
    "Requires MDA, never started": "Not eligible: never started, paused or stopped",
    "Not delivered, outside active cohort": "Not eligible: never started, paused or stopped",
    "Pending impact assessment": "Not eligible: never started, paused or stopped",
    "Post-intervention surveillance": "Not eligible: never started, paused or stopped",
    "Non-endemic": "Non-endemic",
}
MAP_COLOR = {"Delivered": BLUE, "Reported interruption (unverified proxy)": ORANGE,
             "Not eligible: never started, paused or stopped": AQUA,
             "No data": "#3d3d3a", "Non-endemic": LIGHT}


@st.cache_data(show_spinner=False)
def load_info() -> dict:
    f = DATA / "info.json"
    return json.loads(f.read_text("utf-8")) if f.exists() else {}


def is_synthetic() -> bool:
    return not (DATA / "iu_year.parquet").exists()


@st.cache_data(show_spinner="Loading stored results")
def load_iu_year() -> pd.DataFrame:
    f = DATA / "iu_year.parquet"
    if f.exists():
        df = pd.read_parquet(f)
        for c in df.select_dtypes("category").columns:
            df[c] = df[c].astype(str)
    else:
        df = synthetic_iu_year()
    df["map_group"] = df["display_class"].map(MAP_GROUP).fillna("No data")
    return df


def synthetic_iu_year(seed: int = 0) -> pd.DataFrame:
    """Small made-up dataset so the app can be demonstrated without any real data."""
    rng = np.random.default_rng(seed)
    rows = []
    for ci, (iso2, name, lon, lat) in enumerate([("XA", "Synthetic A", 20, 5),
                                                 ("XB", "Synthetic B", 30, -8),
                                                 ("XC", "Synthetic C", 0, 12)]):
        for iu in range(30):
            x, y0 = lon + rng.normal(0, 2), lat + rng.normal(0, 2)
            for year in range(2019, 2026):
                risk = float(np.clip(rng.beta(2, 6) + 0.1 * ci, 0, 1))
                y = float(rng.random() < risk)
                rows.append({"iso2": iso2, "country": name, "iu_id": iu, "year": year,
                             "admin1": f"Region {iu % 3}", "iu_name": f"Synthetic IU {iu}",
                             "display_class": ("Reported interruption (unverified proxy)" if y
                                               else "Delivered"),
                             "cohort_status": "In primary cohort", "eligible_primary": True,
                             "y": y, "lon": x, "lat": y0, "window": "synthetic",
                             "prediction_source": "SYNTHETIC", "row_class_l1": "delivered",
                             "p_history_rule": risk, "r_history_rule": risk,
                             "p_logistic_history": risk, "r_logistic_history": risk})
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def read_csv(rel: str) -> pd.DataFrame | None:
    f = ROOT / rel
    # keep_default_na=False: the ISO code for Namibia is "NA" and must stay a string
    return pd.read_csv(f, keep_default_na=False, na_values=[""]) if f.exists() else None


def stored_models(df: pd.DataFrame) -> list[str]:
    return [c[2:] for c in df.columns if c.startswith("r_")]


def banner() -> None:
    if is_synthetic():
        st.error("**DEMONSTRATION — SYNTHETIC DATA.** No real ESPEN data or model results are "
                 "loaded. Everything shown is made up to demonstrate the interface.", icon="⚠️")
        return
    st.warning(
        "**Retrospective research only.** The outcome is a WHO ESPEN reported status used as "
        "an unverified proxy for a missed treatment round. No programme officer has reviewed "
        "the labels. Do not use these results to judge, fund or defund any programme.",
        icon="⚠️")


def style(fig, height: int = 380, legend_bottom: bool = True):
    fig.update_layout(
        height=height, template="simple_white", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, Arial, sans-serif", size=13),
        margin=dict(l=10, r=10, t=40, b=10), title_font_size=15,
        hoverlabel=dict(font_size=12))
    if legend_bottom:
        fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.24, x=0,
                                      title_text=""))
    fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.18)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.18)", zeroline=False)
    return fig


def capture_summary(y: np.ndarray, score: np.ndarray, frac: float) -> dict:
    tp, k = top_k_counts(y, score, frac)
    total = float(np.nansum(y))
    return {"flagged": k, "captured": tp, "total_events": total,
            "capture": tp / total if total else float("nan"),
            "precision": tp / k if k else float("nan")}


def fmt_ci(est, lo, hi, digits: int = 2) -> str:
    if pd.isna(est):
        return "not estimable"
    if pd.isna(lo):
        return f"{est:.{digits}f}"
    return f"{est:.{digits}f} ({lo:.{digits}f} to {hi:.{digits}f})"
