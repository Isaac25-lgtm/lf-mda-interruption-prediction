"""LF MDA interruption research dashboard.

Run locally:  streamlit run dashboard/app.py

The app only reads stored, validated artifacts (audit tables, evaluation tables and
stored predictions). It never trains a model and never computes a "risk" from outcome
labels. If the derived data file is absent it falls back to a clearly labelled
synthetic demonstration.
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="LF MDA interruption research", page_icon="🧭", layout="wide")

import views  # noqa: E402  (must follow set_page_config)
from lib import load_info  # noqa: E402

PAGES = [
    st.Page(views.page_overview, title="Study overview", icon="🧭", url_path="overview",
            default=True),
    st.Page(views.page_quality, title="Data quality", icon="🧪", url_path="data-quality"),
    st.Page(views.page_map, title="Implementation-unit map", icon="🗺️", url_path="map"),
    st.Page(views.page_risk, title="Risk explorer", icon="🔎", url_path="risk"),
    st.Page(views.page_models, title="Model comparison", icon="📊", url_path="models"),
    st.Page(views.page_capacity, title="Capacity prioritisation", icon="🎯",
            url_path="capacity"),
    st.Page(views.page_validation, title="Validation & uncertainty", icon="📐",
            url_path="validation"),
    st.Page(views.page_methods, title="Methods", icon="📘", url_path="methods"),
    st.Page(views.page_limits, title="Limitations & citation", icon="⚖️",
            url_path="limitations"),
]

nav = st.navigation(PAGES)
with st.sidebar:
    info = load_info()
    st.caption("LF MDA interruption research · v0.1.0")
    if info:
        st.caption(f"Results built {info['built_utc'][:10]} · ESPEN data retrieved "
                   f"{info['espen_retrieved_utc'][:10]}")
    st.caption(f"[Source code and protocol]({views.REPO_URL})")
nav.run()
