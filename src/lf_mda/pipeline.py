"""Modelling pipeline: development (rolling origin), locked test, transport, sensitivity.

Order of use, enforced by files on disk:
  1. `develop`  - tunes and compares models on development years only;
  2. `lock`     - fits the selected configurations once and scores the held-out years;
  3. `loco`     - leave-one-country-out transport on development years;
  4. `sensitivity`, `explain` - derived from saved predictions and fitted models.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from . import paths
from .calibrate import PlattCalibrator
from .evaluate import log_loss
from .features import build_features, check_frame_against_manifest, load_context, load_manifest
from .labels import load_protocol
from .model import SPEC_BY_NAME, SPECS, build_model, grid_for, rank_score
from .splits import (
    final_training_index,
    held_out_index,
    leave_one_country_out,
    rolling_origin_folds,
)
from .uncertainty import cluster_bootstrap, country_jackknife, point_estimates

DEV_DIR = paths.EVALUATION / "development"
LOCK_DIR = paths.EVALUATION / "locked_test"
LOCO_DIR = paths.EVALUATION / "country_transport"
SENS_DIR = paths.EVALUATION / "sensitivity"
EXPLAIN_DIR = paths.EVALUATION / "explain"
LOCO_MODELS = ["country_prior_rate", "history_rule", "logistic_iu_only", "logistic_history",
               "catboost_history"]


# ------------------------------------------------------------------ helpers
TEXT_SUFFIXES = {".yaml", ".yml", ".csv", ".json", ".md"}


def sha256_file(path: Path) -> str:
    """SHA-256 of a file. Text files are hashed with LF line endings so that the same
    content gives the same fingerprint on Windows and on a fresh Git checkout."""
    data = Path(path).read_bytes()
    if Path(path).suffix.lower() in TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def frame_digest(df: pd.DataFrame) -> str:
    h = pd.util.hash_pandas_object(df.reset_index(drop=True), index=False).to_numpy()
    return hashlib.sha256(h.tobytes()).hexdigest()


def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=paths.ROOT, capture_output=True,
                              text=True, timeout=10).stdout.strip() or "no-commit"
    except Exception:
        return "unavailable"


def write_run_manifest(step: str, extra: dict) -> Path:
    import catboost
    import sklearn
    paths.RUNS.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    man = {
        "step": step, "utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "git_commit": git_commit(),
        "python": sys.version.split()[0], "platform": platform.platform(),
        "packages": {"pandas": pd.__version__, "numpy": np.__version__,
                     "scikit-learn": sklearn.__version__, "catboost": catboost.__version__},
        "protocol_sha256": sha256_file(paths.CONFIG / "protocol.yaml"),
        "features_sha256": sha256_file(paths.CONFIG / "features.yaml"),
        "status_map_sha256": sha256_file(paths.CONFIG / "status_map_reviewed.csv"),
        "raw_manifest_sha256": sha256_file(paths.MANIFESTS / "espen_sources.csv"),
    } | extra
    out = paths.RUNS / f"{now.strftime('%Y%m%dT%H%M%SZ')}_{step}.json"
    out.write_text(json.dumps(man, indent=2, default=str), encoding="utf-8")
    return out


def load_frames() -> tuple[dict, dict[str, pd.DataFrame]]:
    """Feature frames for both information scenarios, validated against the manifest."""
    proto = load_protocol()
    panel = pd.read_parquet(paths.PROCESSED / "panel.parquet")
    context = load_context()
    frames = {}
    for scen, cfg in proto["information_scenarios"].items():
        feat = build_features(panel, cfg["feature_lag"], context)
        check_frame_against_manifest(feat)
        extra = panel.loc[panel["eligible_broad"], ["iu_key", "year", "hs_group", "row_class_l1"]]
        frames[scen] = feat.merge(extra, on=["iu_key", "year"], how="left")
    return proto, frames


def available_specs(frames: dict) -> list:
    has_context = any(c.startswith("x_") for c in next(iter(frames.values())).columns)
    return [s for s in SPECS if has_context or "context" not in s.groups]


def _fit_predict(spec, params, proto, manifest, train: pd.DataFrame, test: pd.DataFrame):
    model = build_model(spec, params, proto, manifest).fit(train, train["y"].to_numpy())
    p = model.predict_proba(test)
    return model, p, rank_score(model, test, p)


# ------------------------------------------------------------------ development
def run_development(n_boot: int = 500) -> dict:
    proto, frames = load_frames()
    manifest = load_manifest()
    DEV_DIR.mkdir(parents=True, exist_ok=True)
    specs = available_specs(frames)
    grid_log, selected, calibrators, oof_frames = [], {}, {}, []
    for scen, feat in frames.items():
        lag = proto["information_scenarios"][scen]["label_lag"]
        folds = list(rolling_origin_folds(feat, proto, lag))
        val_idx = np.concatenate([v for _, _, v in folds])
        oof = feat.iloc[val_idx][["iu_key", "iso2", "country", "year", "y", "covid_stress_year",
                                  "hs_group", "row_class_l1", "eligible_incident",
                                  "eligible_strict"]].copy()
        oof["scenario"] = scen
        selected[scen], calibrators[scen] = {}, {}
        for spec in specs:
            best = None
            for params in grid_for(spec, proto):
                p = np.full(len(feat), np.nan)
                r = np.full(len(feat), np.nan)
                for _, tr, va in folds:
                    _, p[va], r[va] = _fit_predict(spec, params, proto, manifest,
                                                   feat.iloc[tr], feat.iloc[va])
                loss = log_loss(feat["y"].to_numpy()[val_idx], p[val_idx])
                grid_log.append({"scenario": scen, "model": spec.name,
                                 "params": json.dumps(params), "pooled_log_loss": loss})
                if best is None or loss < best[0]:
                    best = (loss, params, p[val_idx], r[val_idx])
            selected[scen][spec.name] = {"params": best[1], "pooled_log_loss": best[0]}
            print(f"[develop] scenario {scen} {spec.name}: {best[1]} "
                  f"log loss {best[0]:.4f}", flush=True)
            oof[f"p_{spec.name}"], oof[f"r_{spec.name}"] = best[2], best[3]
            cal = PlattCalibrator().fit(best[2], oof["y"].to_numpy())
            calibrators[scen][spec.name] = cal.to_dict()
        oof_frames.append(oof)
    oof_all = pd.concat(oof_frames, ignore_index=True)
    oof_all.to_parquet(paths.PROCESSED / "predictions_development_oof.parquet", index=False)
    pd.DataFrame(grid_log).to_csv(DEV_DIR / "grid_search_log.csv", index=False)
    (DEV_DIR / "selected_configs.json").write_text(json.dumps(selected, indent=2), "utf-8")
    (DEV_DIR / "calibrators.json").write_text(json.dumps(calibrators, indent=2), "utf-8")

    names = [s.name for s in specs]
    rank_cols = {m: f"r_{m}" for m in names}
    comparator = proto["models"]["primary_comparator"]
    metric_rows, ci_rows, diff_rows = [], [], []
    for scen, sub in oof_all.groupby("scenario"):
        sub = sub.reset_index(drop=True)
        subsets = {"rolling_2019_2022": sub,
                   "non_covid_2019_2022": sub[~sub["covid_stress_year"]],
                   "covid_2020_2021": sub[sub["covid_stress_year"]]}
        subsets |= {f"year_{y}": g for y, g in sub.groupby("year")}
        for name, d in subsets.items():
            d = d.reset_index(drop=True)
            pe = point_estimates(d, names, rank_cols)
            pe.insert(0, "subset", name)
            pe.insert(0, "scenario", scen)
            metric_rows.append(pe)
            if name in ("rolling_2019_2022", "non_covid_2019_2022"):
                ci, df_ = cluster_bootstrap(d, names, comparator, rank_cols, n_boot,
                                            proto["seed"])
                for t, store in ((ci, ci_rows), (df_, diff_rows)):
                    t.insert(0, "subset", name)
                    t.insert(0, "scenario", scen)
                    store.append(t)
    pd.concat(metric_rows).to_csv(DEV_DIR / "development_metrics.csv", index=False)
    pd.concat(ci_rows).to_csv(DEV_DIR / "development_intervals.csv", index=False)
    pd.concat(diff_rows).to_csv(DEV_DIR / "development_differences_vs_rule.csv", index=False)
    write_run_manifest("develop", {"n_boot": n_boot, "models": names,
                                   "oof_digest": frame_digest(oof_all)})
    return selected


def primary_candidate(selected: dict) -> str:
    """Model (not a baseline) with the lowest pooled rolling-origin log loss, scenario P.

    This applies the pre-specified selection rule in config/protocol.yaml. It uses
    development folds only.
    """
    fitted = {m: v["pooled_log_loss"] for m, v in selected["P"].items()
              if SPEC_BY_NAME[m].kind in ("logistic", "catboost")}
    return min(fitted, key=fitted.get)


# ------------------------------------------------------------------ locked test
def _model_path(scen: str, name: str, kind: str) -> Path:
    ext = {"catboost": "cbm"}.get(kind, "joblib")
    return paths.MODELS / f"{scen}_{name}.{ext}"


def run_locked_test(n_boot: int | None = None, amend: str | None = None) -> dict:
    proto, frames = load_frames()
    manifest = load_manifest()
    if not (DEV_DIR / "selected_configs.json").exists():
        raise RuntimeError("run `develop` first: no selected configurations found")
    selected = json.loads((DEV_DIR / "selected_configs.json").read_text("utf-8"))
    calibrators = json.loads((DEV_DIR / "calibrators.json").read_text("utf-8"))
    fingerprint = {
        "protocol_sha256": sha256_file(paths.CONFIG / "protocol.yaml"),
        "features_sha256": sha256_file(paths.CONFIG / "features.yaml"),
        "selected_sha256": sha256_file(DEV_DIR / "selected_configs.json"),
        "raw_manifest_sha256": sha256_file(paths.MANIFESTS / "espen_sources.csv"),
    }
    lock_file = LOCK_DIR / "LOCK.json"
    history = []
    if lock_file.exists():
        prior = json.loads(lock_file.read_text("utf-8"))
        history = prior.get("history", [])
        if prior["fingerprint"] != fingerprint and not amend:
            raise RuntimeError(
                "The locked test has already been opened with a different protocol, feature "
                "set, model selection or data. Re-opening it would be test reuse. If this is "
                "a documented protocol amendment, pass --amend 'reason' and record it in "
                "docs/DECISIONS.md.")
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    paths.MODELS.mkdir(parents=True, exist_ok=True)
    n_boot = n_boot or 2000
    specs = available_specs(frames)
    names = [s.name for s in specs]
    preds, digests = [], {}
    for scen, feat in frames.items():
        lag = proto["information_scenarios"][scen]["label_lag"]
        tr = final_training_index(feat, proto, lag)
        ho = held_out_index(feat, proto)
        train, held = feat.iloc[tr], feat.iloc[ho]
        out = held[["iu_key", "iso2", "country", "admin1", "iu_id", "iu_name", "year", "y",
                    "window", "outcome_class", "eligible_primary", "eligible_strict",
                    "eligible_incident", "eligible_broad", "row_class_l1"]].copy()
        out["scenario"] = scen
        out["train_years"] = f"{train['year'].min()}-{train['year'].max()}"
        out["n_train"] = len(train)
        for spec in specs:
            params = selected[scen][spec.name]["params"]
            model, p_raw, r = _fit_predict(spec, params, proto, manifest, train, held)
            cal = PlattCalibrator.from_dict(calibrators[scen][spec.name])
            out[f"praw_{spec.name}"] = p_raw
            out[f"p_{spec.name}"] = cal.apply(p_raw)
            out[f"r_{spec.name}"] = r
            path = _model_path(scen, spec.name, spec.kind)
            if spec.kind == "catboost":
                model.model_.save_model(str(path))
            else:
                joblib.dump(model, path)
            digests[path.name] = sha256_file(path)
        preds.append(out)
    pred = pd.concat(preds, ignore_index=True)
    pred.to_parquet(paths.PROCESSED / "predictions_heldout.parquet", index=False)

    rank_cols = {m: f"r_{m}" for m in names}
    comparator = proto["models"]["primary_comparator"]
    metric_rows, ci_rows, diff_rows, jk_rows = [], [], [], []
    for scen, sub in pred.groupby("scenario"):
        prim = sub[sub["eligible_primary"] & sub["y"].notna()]
        subsets = {"locked_test_2023_2024": prim[prim["window"] == "locked_test"],
                   "year_2023": prim[prim["year"] == 2023],
                   "year_2024": prim[prim["year"] == 2024],
                   "stress_2025": prim[prim["window"] == "shock_stress_2025"]}
        for name, d in subsets.items():
            d = d.reset_index(drop=True)
            if d.empty:
                continue
            pe = point_estimates(d, names, rank_cols)
            raw = point_estimates(d.drop(columns=[f"p_{m}" for m in names]).rename(
                columns={f"praw_{m}": f"p_{m}" for m in names}), names, rank_cols)
            for col in ("brier", "log_loss", "calibration_intercept", "calibration_slope",
                        "observed_expected_ratio"):
                pe[f"uncalibrated_{col}"] = raw[col].to_numpy()
            pe.insert(0, "subset", name)
            pe.insert(0, "scenario", scen)
            metric_rows.append(pe)
            if name in ("locked_test_2023_2024", "stress_2025"):
                ci, df_ = cluster_bootstrap(d, names, comparator, rank_cols, n_boot,
                                            proto["seed"])
                jk = country_jackknife(d, names, rank_cols)
                for t, store in ((ci, ci_rows), (df_, diff_rows), (jk, jk_rows)):
                    t.insert(0, "subset", name)
                    t.insert(0, "scenario", scen)
                    store.append(t)
    metrics = pd.concat(metric_rows)
    metrics.to_csv(LOCK_DIR / "locked_metrics.csv", index=False)
    pd.concat(ci_rows).to_csv(LOCK_DIR / "locked_intervals.csv", index=False)
    diffs = pd.concat(diff_rows)
    diffs.to_csv(LOCK_DIR / "locked_differences_vs_rule.csv", index=False)
    pd.concat(jk_rows).to_csv(LOCK_DIR / "locked_country_jackknife.csv", index=False)
    (paths.MODELS / "model_digests.json").write_text(json.dumps(digests, indent=2), "utf-8")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    history.append({"utc": now, "amend_reason": amend or "", "fingerprint": fingerprint,
                    "predictions_digest": frame_digest(pred)})
    lock = {"first_opened_utc": history[0]["utc"], "last_run_utc": now,
            "primary_candidate": primary_candidate(selected),
            "primary_comparator": comparator,
            "fingerprint": fingerprint, "times_run": len(history),
            "note": ("Re-running with an identical fingerprint reproduces the same numbers and "
                     "is not test reuse. Any run with a changed fingerprint is logged here."),
            "history": history}
    lock_file.write_text(json.dumps(lock, indent=2), "utf-8")
    write_run_manifest("lock", {"n_boot": n_boot, "model_digests": digests,
                                "predictions_digest": frame_digest(pred)})
    return {"metrics": metrics, "differences": diffs}


# ------------------------------------------------------------------ country transport
def run_loco(n_boot: int = 1000, min_events: int = 10) -> pd.DataFrame:
    proto, frames = load_frames()
    manifest = load_manifest()
    LOCO_DIR.mkdir(parents=True, exist_ok=True)
    feat = frames["P"]
    specs = [SPEC_BY_NAME[m] for m in LOCO_MODELS]
    names = [s.name for s in specs]
    selected = json.loads((DEV_DIR / "selected_configs.json").read_text("utf-8"))["P"]
    parts, tuning = [], []
    for iso2, tr, te in leave_one_country_out(feat, proto):
        train, test = feat.iloc[tr], feat.iloc[te]
        out = test[["iu_key", "iso2", "country", "year", "y"]].copy()
        groups = train["iso2"].to_numpy()
        for spec in specs:
            grid = grid_for(spec, proto)
            best_params = grid[0]
            if spec.kind == "catboost":
                # Not nested (see docs/DECISIONS.md D14): each fit takes ~15 s, so the
                # configuration chosen on the temporal development folds is reused.
                best_params = selected[spec.name]["params"]
            elif len(grid) > 1:  # nested tuning inside the training countries only
                best_loss = np.inf
                for params in grid:
                    p = np.full(len(train), np.nan)
                    for a, b in GroupKFold(n_splits=3).split(train, groups=groups):
                        _, p[b], _ = _fit_predict(spec, params, proto, manifest,
                                                  train.iloc[a], train.iloc[b])
                    loss = log_loss(train["y"].to_numpy(), p)
                    if loss < best_loss:
                        best_loss, best_params = loss, params
            model, p, r = _fit_predict(spec, best_params, proto, manifest, train, test)
            out[f"p_{spec.name}"], out[f"r_{spec.name}"] = p, r
            tuning.append({"held_out_country": iso2, "model": spec.name,
                           "params": json.dumps(best_params)})
        parts.append(out)
        print(f"LOCO {iso2}: n={len(test)} events={int(test['y'].sum())}", flush=True)
    pred = pd.concat(parts, ignore_index=True)
    pred.to_parquet(paths.PROCESSED / "predictions_country_transport.parquet", index=False)
    pd.DataFrame(tuning).to_csv(LOCO_DIR / "nested_tuning_log.csv", index=False)
    rank_cols = {m: f"r_{m}" for m in names}
    pooled = point_estimates(pred, names, rank_cols)
    pooled.insert(0, "subset", "all_held_out_countries_pooled")
    ci, diffs = cluster_bootstrap(pred, names, proto["models"]["primary_comparator"], rank_cols,
                                  n_boot, proto["seed"])
    rows = []
    for iso2, d in pred.groupby("iso2"):
        ev, nonev = int(d["y"].sum()), int((1 - d["y"]).sum())
        pe = point_estimates(d.reset_index(drop=True), names, rank_cols)
        pe.insert(0, "supports_external_claim", ev >= min_events and nonev >= min_events)
        pe.insert(0, "country", d["country"].iloc[0])
        pe.insert(0, "iso2", iso2)
        rows.append(pe)
    per_country = pd.concat(rows)
    pooled.to_csv(LOCO_DIR / "transport_pooled_metrics.csv", index=False)
    ci.to_csv(LOCO_DIR / "transport_pooled_intervals.csv", index=False)
    diffs.to_csv(LOCO_DIR / "transport_differences_vs_rule.csv", index=False)
    per_country.to_csv(LOCO_DIR / "transport_by_country.csv", index=False)
    write_run_manifest("loco", {"n_boot": n_boot, "models": names,
                                "predictions_digest": frame_digest(pred)})
    return pooled


# ------------------------------------------------------------------ sensitivity
def run_sensitivity() -> pd.DataFrame:
    proto, _ = load_frames()
    SENS_DIR.mkdir(parents=True, exist_ok=True)
    pred = pd.read_parquet(paths.PROCESSED / "predictions_heldout.parquet")
    oof = pd.read_parquet(paths.PROCESSED / "predictions_development_oof.parquet")
    flags = pd.read_csv(paths.AUDIT / "country_year_flags.csv", keep_default_na=False,
                        na_values=[""])
    names = [c[2:] for c in pred.columns if c.startswith("p_")]
    rank_cols = {m: f"r_{m}" for m in names}
    p = pred[pred["scenario"] == "P"].merge(
        flags[["iso2", "year", "flag_population_carried_forward", "release_date"]],
        on=["iso2", "year"], how="left")
    lt = p[p["window"] == "locked_test"]
    prim = lt[lt["eligible_primary"] & lt["y"].notna()]
    cy = prim.groupby(["iso2", "year"])["y"].transform("mean")
    missing = lt[lt["eligible_primary"] & lt["outcome_class"].isin(["missing_JRF",
                                                                    "missing_iu_year"])]
    s25 = p[(p["window"] == "shock_stress_2025") & p["eligible_primary"] & p["y"].notna()]
    d = oof[oof["scenario"] == "P"]
    subsets = {
        "primary: locked test 2023-2024": prim,
        "incident cohort (delivered at t-1)": prim[prim["eligible_incident"]],
        "strict cohort (<5 rounds incl. pre-2014)": prim[prim["eligible_strict"]],
        "broad cohort (no round restriction; model extrapolates)":
            lt[lt["eligible_broad"] & lt["y"].notna()],
        "mixed country-years only (both outcomes present)": prim[(cy > 0) & (cy < 1)],
        "excluding carried-forward country-years":
            prim[~prim["flag_population_carried_forward"].fillna(False)],
        "missing labels counted as interruptions":
            pd.concat([prim, missing.assign(y=1.0)]),
        "missing labels counted as delivered":
            pd.concat([prim, missing.assign(y=0.0)]),
        "stress 2025 (all)": s25,
        "stress 2025, countries in ESPEN release log only": s25[s25["release_date"].notna()],
        "development folds: all events": d,
        "development folds: excluding events later moved to IA/surveillance":
            d[~((d["y"] == 1) & (d["hs_group"] == "moved_to_IA_or_surveillance"))],
        "development folds: non-COVID years": d[~d["covid_stress_year"]],
    }
    rows = []
    for name, sub in subsets.items():
        sub = sub.reset_index(drop=True)
        if sub.empty or sub["y"].nunique() < 2:
            rows.append(pd.DataFrame([{"analysis": name, "model": "", "n": len(sub),
                                       "events": int(sub["y"].sum()) if len(sub) else 0,
                                       "note": "not estimable (one outcome class)"}]))
            continue
        pe = point_estimates(sub, names, rank_cols)
        pe.insert(0, "countries", sub["iso2"].nunique())
        pe.insert(0, "analysis", name)
        rows.append(pe)
    out = pd.concat(rows, ignore_index=True)
    out.to_csv(SENS_DIR / "sensitivity_metrics.csv", index=False)

    # scenario P versus E on identical IU-years
    comp = []
    for scen, sub in pred.groupby("scenario"):
        sub = sub[(sub["window"] == "locked_test") & sub["eligible_primary"] & sub["y"].notna()]
        pe = point_estimates(sub.reset_index(drop=True), names, rank_cols)
        pe.insert(0, "scenario", scen)
        comp.append(pe)
    pd.concat(comp).to_csv(SENS_DIR / "scenario_P_vs_E_locked_test.csv", index=False)
    write_run_manifest("sensitivity", {"analyses": list(subsets)})
    return out


# ------------------------------------------------------------------ interpretation
def run_explain() -> None:
    proto, frames = load_frames()
    manifest = load_manifest()
    EXPLAIN_DIR.mkdir(parents=True, exist_ok=True)
    selected = json.loads((DEV_DIR / "selected_configs.json").read_text("utf-8"))
    feat = frames["P"]
    train = feat.iloc[final_training_index(feat, proto, 1)]
    for name in ("logistic_history", "logistic_history_context", "logistic_iu_only"):
        if name not in selected["P"]:
            continue
        m = build_model(SPEC_BY_NAME[name], selected["P"][name]["params"], proto, manifest)
        m.fit(train, train["y"].to_numpy())
        m.coefficients().to_csv(EXPLAIN_DIR / f"coefficients_{name}.csv", index=False)
    for name in ("catboost_history", "catboost_history_context"):
        if name not in selected["P"]:
            continue
        m = build_model(SPEC_BY_NAME[name], selected["P"][name]["params"], proto, manifest)
        m.fit(train, train["y"].to_numpy())
        m.shap_importance(train).to_csv(EXPLAIN_DIR / f"shap_importance_{name}.csv", index=False)
    write_run_manifest("explain", {})
