"""Predictor construction under an explicit as-of (information lag) contract.

Every feature for target year t is computed from rows dated t - info_lag or earlier.
`info_lag=1` is information scenario P (programme knows its own t-1 results);
`info_lag=2` is scenario E (public ESPEN data lag). Conflict features additionally obey
the UCDP publication lag. The manifest in config/features.yaml is machine-checked, and
`assert_no_future_dependence` proves by perturbation that no feature reads later rows.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from . import paths
from .spatial import UCDP_MIN_LAG

KEY_COLS = ["iu_key", "iso2", "country", "admin1", "iu_id", "iu_name", "year", "y", "window",
            "covid_stress_year", "outcome_class", "eligible_broad", "eligible_primary",
            "eligible_strict", "eligible_incident"]

SCHEMES = ["ALB+IVM", "ALB+DEC", "ALBx2", "IDA"]


def load_manifest(path: Path | None = None) -> dict:
    with open(path or paths.CONFIG / "features.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def feature_names(groups: list[str], manifest: dict | None = None) -> list[str]:
    man = manifest or load_manifest()
    return [name for name, spec in man["features"].items() if spec["group"] in groups]


def categorical_features(names: list[str], manifest: dict | None = None) -> list[str]:
    man = manifest or load_manifest()
    return [n for n in names if man["features"][n].get("type") == "categorical"]


def validate_manifest(manifest: dict) -> None:
    """Reject any feature that is declared to use outcome-year or future information."""
    for name, spec in manifest["features"].items():
        if spec.get("derived_from_outcome_year", True):
            raise ValueError(f"feature {name} is flagged as derived from the outcome year")
        if int(spec.get("min_lag_years", 0)) < 1:
            raise ValueError(f"feature {name} has min_lag_years < 1; future leakage not allowed")
        if spec["group"] not in manifest["groups"]:
            raise ValueError(f"feature {name} has unknown group {spec['group']}")


def _at(info: pd.DataFrame, keys: list[str], offset: int, cols: list[str], suffix: str):
    src = info[keys + ["year"] + cols].copy()
    src["year"] = src["year"] + offset
    return src.rename(columns={c: f"{c}{suffix}" for c in cols})


def _country_year_table(panel: pd.DataFrame) -> pd.DataFrame:
    obs = panel[panel["row_present"]]
    g = obs.groupby(["iso2", "year"])
    cy = g.agg(
        c_n_iu=("iu_key", "size"),
        c_n_req=("row_class", lambda s: int(s.isin(["delivered", "non_delivery"]).sum())),
        c_n_nd=("row_class", lambda s: int((s == "non_delivery").sum())),
        c_n_pis=("row_class", lambda s: int((s == "surveillance_or_stopped").sum())),
        c_n_endemic=("row_class", lambda s: int((~s.isin(["not_endemic", "unknown",
                                                           "missing_JRF"])).sum())),
        c_n_nr=("row_class", lambda s: int((s == "missing_JRF").sum())),
    ).reset_index()
    return cy


def _admin1_year_table(panel: pd.DataFrame) -> pd.DataFrame:
    obs = panel[panel["row_present"] & panel["admin1_id"].notna()]
    g = obs.groupby(["iso2", "admin1_id", "year"])
    return g.agg(
        a_n_req=("row_class", lambda s: int(s.isin(["delivered", "non_delivery"]).sum())),
        a_n_nd=("row_class", lambda s: int((s == "non_delivery").sum())),
    ).reset_index()


def build_features(panel: pd.DataFrame, info_lag: int = 1,
                   context: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    """Return one row per broad-cohort IU-year with keys, outcome and predictors."""
    if info_lag < 1:
        raise ValueError("info_lag must be >= 1: predictors may not use the outcome year")
    L = info_lag
    base = panel.loc[panel["eligible_broad"], KEY_COLS].copy()
    info = panel[["iu_key", "year", "row_class", "epi_cov", "epi_eff_mda", "epi_eff_mda_n",
                  "cum_mda", "scheme", "pop_req", "pop_tot", "admin1_id", "row_present"]].copy()
    info["nd"] = np.where(info["row_class"].isin(["delivered", "non_delivery"]),
                          (info["row_class"] == "non_delivery").astype(float), np.nan)
    info["dl"] = np.where(info["row_class"].isin(["delivered", "non_delivery"]),
                          (info["row_class"] == "delivered").astype(float), np.nan)
    info["present"] = info["row_present"].astype(float)
    cols = ["nd", "dl", "epi_cov", "epi_eff_mda", "epi_eff_mda_n", "cum_mda", "scheme",
            "pop_req", "pop_tot", "admin1_id", "row_class", "present"]
    f = base
    for k in range(3):
        f = f.merge(_at(info, ["iu_key"], L + k, cols, f"_k{k}"), on=["iu_key", "year"], how="left")

    out = base.copy()
    out["h_nd_recent"] = f["nd_k0"].to_numpy()
    out["h_nd_prev"] = f["nd_k1"].to_numpy()
    nd3 = f[["nd_k0", "nd_k1", "nd_k2"]]
    out["h_nd_count_3"] = nd3.sum(axis=1, min_count=1).to_numpy()
    out["h_delivered_count_3"] = f[["dl_k0", "dl_k1", "dl_k2"]].sum(axis=1, min_count=1).to_numpy()
    out["h_any_nd_prev2"] = (f[["nd_k1", "nd_k2"]].sum(axis=1, min_count=1) > 0).astype(float).where(
        f[["nd_k1", "nd_k2"]].notna().any(axis=1)).to_numpy()
    # coverage and scheme of the most recent delivered round within the 3-year window
    cov = pd.Series(np.nan, index=f.index)
    eff = pd.Series(np.nan, index=f.index)
    scheme = pd.Series("none", index=f.index, dtype=object)
    for k in (2, 1, 0):
        d = f[f"dl_k{k}"] == 1
        cov = cov.where(~d, f[f"epi_cov_k{k}"])
        eff = eff.where(~d, f[f"epi_eff_mda_k{k}"])
        scheme = scheme.where(~d, f[f"scheme_k{k}"])
    out["h_epi_cov_last_round"] = cov.clip(0, 150).to_numpy()
    out["h_ineffective_recent"] = np.where(f["dl_k0"] == 1, 1 - f["epi_eff_mda_k0"],
                                           np.where(f["nd_k0"] == 1, 0.0, np.nan))
    out["h_scheme_last_round"] = scheme.where(scheme.isin(SCHEMES), "none").to_numpy()
    out["h_eff_rounds_obs"] = f["epi_eff_mda_n_k0"].to_numpy()
    out["h_cum_mda"] = f["cum_mda_k0"].to_numpy()
    out["h_log_pop_tot"] = np.log1p(f["pop_tot_k0"]).to_numpy()

    # ---- country-level programme history (leave-one-out for the IU itself) -----------
    cy = _country_year_table(panel)
    for k, tag in ((0, "recent"), (1, "prev")):
        c = _at(cy, ["iso2"], L + k, ["c_n_iu", "c_n_req", "c_n_nd", "c_n_pis", "c_n_endemic",
                                      "c_n_nr"], f"_{tag}")
        out = out.merge(c, on=["iso2", "year"], how="left")
    own_nd = f["nd_k0"].fillna(0).to_numpy()
    own_req = f["nd_k0"].notna().astype(float).to_numpy()
    denom = out["c_n_req_recent"] - own_req
    out["c_nd_rate_recent"] = np.where(denom > 0, (out["c_n_nd_recent"] - own_nd) / denom, np.nan)
    out["c_nd_rate_recent_full"] = np.where(out["c_n_req_recent"] > 0,
                                            out["c_n_nd_recent"] / out["c_n_req_recent"], np.nan)
    out["c_nd_rate_prev"] = np.where(out["c_n_req_prev"] > 0,
                                     out["c_n_nd_prev"] / out["c_n_req_prev"], np.nan)
    out["c_log_n_requiring"] = np.log1p(out["c_n_req_recent"])
    out["c_share_surveillance"] = np.where(out["c_n_endemic_recent"] > 0,
                                           out["c_n_pis_recent"] / out["c_n_endemic_recent"], np.nan)
    out["c_not_reported_share_prev"] = np.where(out["c_n_iu_prev"] > 0,
                                                out["c_n_nr_prev"] / out["c_n_iu_prev"], np.nan)
    out = out.drop(columns=[c for c in out.columns if c.startswith("c_n_")])

    # ---- admin1 neighbours (leave-one-out) ------------------------------------------
    a1 = _admin1_year_table(panel)
    tmp = out[["iu_key", "iso2", "year"]].copy()
    tmp["admin1_id"] = f["admin1_id_k0"].to_numpy()
    a = _at(a1, ["iso2", "admin1_id"], L, ["a_n_req", "a_n_nd"], "")
    tmp = tmp.merge(a, on=["iso2", "admin1_id", "year"], how="left")
    d1 = tmp["a_n_req"] - own_req
    out["a_nd_rate_recent"] = np.where(d1 > 0, (tmp["a_n_nd"] - own_nd) / d1, np.nan)

    # ---- context: geometry and conflict ----------------------------------------------
    if context is not None:
        geo = context["iu_geo"]
        out = out.merge(geo[["iso2", "iu_id", "lon", "lat", "area_km2"]], on=["iso2", "iu_id"],
                        how="left")
        out["x_log_area_km2"] = np.log(out["area_km2"].where(out["area_km2"] > 0))
        out["x_log_pop_density"] = np.log((f["pop_tot_k0"].to_numpy() / out["area_km2"])
                                          .where(out["area_km2"] > 0))
        has_geo = out["lat"].notna()
        clag = max(L, UCDP_MIN_LAG)
        iu = context["conflict_iu_year"]
        ct = context["conflict_country_year"].copy()
        ct["iso2"] = ct["iso2"].replace({"TZ": "TZ"})
        ev = pd.Series(0.0, index=out.index)
        dth = pd.Series(0.0, index=out.index)
        for k in range(3):
            j = out[["iso2", "iu_id", "year"]].merge(
                _at(iu, ["iso2", "iu_id"], clag + k,
                    ["iu_conflict_events", "iu_conflict_deaths"], ""),
                on=["iso2", "iu_id", "year"], how="left")
            if k == 0:
                out["x_conflict_iu_events_recent"] = np.log1p(
                    j["iu_conflict_events"].fillna(0)).where(has_geo.to_numpy()).to_numpy()
            ev += j["iu_conflict_events"].fillna(0).to_numpy()
            dth += j["iu_conflict_deaths"].fillna(0).to_numpy()
        out["x_conflict_iu_events_3y"] = np.log1p(ev).where(has_geo)
        out["x_conflict_iu_deaths_3y"] = np.log1p(dth).where(has_geo)
        ctz = ct.copy()
        zz = ctz[ctz["iso2"] == "TZ"].assign(iso2="ZZ")  # Zanzibar shares Tanzania's totals
        ctz = pd.concat([ctz, zz], ignore_index=True)
        j = out[["iso2", "year"]].merge(
            _at(ctz, ["iso2"], clag, ["ctry_conflict_events", "ctry_conflict_deaths"], ""),
            on=["iso2", "year"], how="left")
        out["x_conflict_ctry_events_recent"] = np.log1p(j["ctry_conflict_events"].fillna(0)).to_numpy()
        out["x_conflict_ctry_deaths_recent"] = np.log1p(j["ctry_conflict_deaths"].fillna(0)).to_numpy()
        out = out.drop(columns=["area_km2"])

    out["id_country"] = out["iso2"]
    out["rule_score"] = history_rule_score(out)
    out["info_lag"] = L
    return out.reset_index(drop=True)


def history_rule_score(feat: pd.DataFrame) -> pd.Series:
    """Fixed, pre-specified operational rule (config/protocol.yaml: models.history_rule)."""
    nd = feat["h_nd_recent"].fillna(0)
    prev = feat["h_any_nd_prev2"].fillna(0)
    ineff = feat["h_ineffective_recent"].fillna(0)
    cov = feat["h_epi_cov_last_round"].fillna(100).clip(0, 100)
    tie = 0.5 * (1 - cov / 100) * (1 - nd)
    return 4 * nd + 2 * prev + 1 * ineff + tie


def load_context(processed: Path | None = None) -> dict[str, pd.DataFrame] | None:
    processed = processed or paths.PROCESSED
    names = ["iu_geo", "conflict_iu_year", "conflict_country_year"]
    if not all((processed / f"{n}.parquet").exists() for n in names):
        return None
    return {n: pd.read_parquet(processed / f"{n}.parquet") for n in names}


def check_frame_against_manifest(feat: pd.DataFrame, manifest: dict | None = None) -> None:
    man = manifest or load_manifest()
    validate_manifest(man)
    allowed = set(man["features"]) | set(KEY_COLS) | set(man["non_predictor_columns"])
    unknown = [c for c in feat.columns if c not in allowed]
    if unknown:
        raise ValueError(f"columns not declared in config/features.yaml: {unknown}")
    for name, spec in man["features"].items():
        if name not in feat.columns or spec.get("type") == "categorical":
            continue
        lo, hi = spec.get("valid_range", [None, None])
        col = feat[name].dropna()
        if lo is not None and (col < lo).any():
            raise ValueError(f"{name} below valid range {lo}: min {col.min()}")
        if hi is not None and (col > hi).any():
            raise ValueError(f"{name} above valid range {hi}: max {col.max()}")


def assert_no_future_dependence(panel: pd.DataFrame, target_year: int, info_lag: int = 1,
                                context: dict[str, pd.DataFrame] | None = None,
                                seed: int = 0) -> None:
    """Perturb every row dated after the information cutoff; features must not change.

    Outcome-year and later values of all time-varying fields are scrambled. Keys,
    eligibility and outcome columns are kept so the same IU-years are compared.
    """
    rng = np.random.default_rng(seed)
    man = load_manifest()
    names = [n for n in man["features"] if n != "id_country"]
    ref = build_features(panel, info_lag, context)
    ref = ref[ref["year"] == target_year].set_index("iu_key")
    pert = panel.copy()
    future = pert["year"] > target_year - info_lag
    for col in ["epi_cov", "cov", "epi_eff_mda", "epi_eff_mda_n", "cum_mda", "pop_req", "pop_tot",
                "pop_treat", "mda"]:
        pert.loc[future, col] = rng.permutation(pert.loc[future, col].to_numpy()) * 3 + 7
    pert.loc[future, "scheme"] = "IDA"
    pert.loc[future, "row_class"] = rng.choice(["delivered", "non_delivery", "missing_JRF"],
                                               size=int(future.sum()))
    pert.loc[future, "row_present"] = True
    if context is not None:
        context = {k: v.copy() for k, v in context.items()}
        for key in ("conflict_iu_year", "conflict_country_year"):
            cmask = context[key]["year"] > target_year - max(info_lag, UCDP_MIN_LAG)
            for col in context[key].columns:
                if col.endswith(("events", "deaths")):
                    context[key].loc[cmask, col] = 99999
    new = build_features(pert, info_lag, context)
    new = new[new["year"] == target_year].set_index("iu_key").reindex(ref.index)
    for name in [n for n in names if n in ref.columns] + ["rule_score"]:
        a, b = ref[name], new[name]
        same = (a == b) | (a.isna() & b.isna())
        if pd.api.types.is_float_dtype(a):
            same |= np.isclose(a.astype(float), b.astype(float), equal_nan=True)
        if not same.all():
            raise AssertionError(
                f"feature {name} for target year {target_year} changed when rows after "
                f"{target_year - info_lag} were perturbed: future information leak")
