"""Raw-file schema checks, manifest integrity and the rule-based gate."""
import hashlib

import pandas as pd
import pytest

from conftest import raw_from_patterns
from lf_mda import paths
from lf_mda.audit import GATE_RULES, evaluate_gate, variance_partition
from lf_mda.ingest import (OPTIONAL_COLUMNS, REQUIRED_COLUMNS, SchemaError, load_sources,
                           read_raw_file)


def _write(tmp_path, df, name="espen_lf_iu_XA_2014_2025.csv"):
    path = tmp_path / name
    df.drop(columns=["schema_optional_present", "source_file"]).to_csv(path, index=False)
    return path


def test_valid_file_loads_as_text(tmp_path):
    df = read_raw_file(_write(tmp_path, raw_from_patterns({("XA", 1): "MMN---------"})))
    assert len(df) == 3 and df["popTreat"].map(type).eq(str).all()


def test_missing_required_column_fails_loudly(tmp_path):
    raw = raw_from_patterns({("XA", 1): "MMN---------"}).drop(columns="endemicity")
    with pytest.raises(SchemaError, match="missing required columns"):
        read_raw_file(_write(tmp_path, raw))


def test_unrecognised_column_fails_loudly(tmp_path):
    raw = raw_from_patterns({("XA", 1): "MMN---------"})
    raw["brand_new_field"] = "1"
    with pytest.raises(SchemaError, match="unrecognised columns"):
        read_raw_file(_write(tmp_path, raw))


def test_optional_columns_are_filled_and_recorded(tmp_path):
    raw = raw_from_patterns({("XA", 1): "MMN---------"}).drop(columns=OPTIONAL_COLUMNS)
    df = read_raw_file(_write(tmp_path, raw))
    assert all(c in df.columns for c in OPTIONAL_COLUMNS)
    assert (df["schema_optional_present"] == "").all()


def test_source_config_lists_48_distinct_countries():
    src = load_sources()
    codes = [c["iso2"] for c in src["countries"]]
    assert len(codes) == len(set(codes)) == 48
    assert src["disease"] == "lf" and src["level"] == "iu"
    assert "{country}" in src["path_template"]


def _good_metrics() -> dict:
    return {"contradiction_share": 0.0005, "n_not_reported_rows": 100,
            "missing_jrf_in_positive": 0, "hindsight_stop_share_primary": 0.10,
            "hindsight_stop_share_excluded": 0.40, "dev_events": 1000, "test_events": 150,
            "test_event_countries": 10, "events_in_mixed_country_years": 600,
            "within_country_year_variance_share": 0.4, "test_n": 700,
            "test_event_country_years": 14, "test_events_effective": 13.0}


def test_gate_passes_only_as_proxy_and_never_claims_expert_review():
    g = evaluate_gate(_good_metrics())
    assert g["decision"] == "GO_ON_PROXY_LABEL"
    assert g["expert_verification"].startswith("PENDING")
    assert g["information_adequacy"] == "LIMITED"


@pytest.mark.parametrize("key,value", [
    ("contradiction_share", 0.2), ("hindsight_stop_share_primary", 0.5),
    ("test_events", 5), ("test_event_countries", 1),
    ("events_in_mixed_country_years", 3), ("within_country_year_variance_share", 0.01),
    ("missing_jrf_in_positive", 4),
])
def test_gate_blocks_modelling_when_a_check_fails(key, value):
    m = _good_metrics() | {key: value}
    assert evaluate_gate(m)["decision"] == "REDESIGN_REQUIRES_APPROVAL"


def test_gate_thresholds_are_declared():
    assert set(GATE_RULES) >= {"max_contradiction_share", "min_locked_test_events"}


def test_variance_partition_extremes():
    whole = pd.DataFrame({"iso2": ["A"] * 4 + ["B"] * 4, "year": 2020,
                          "y": [1.0] * 4 + [0.0] * 4})      # pure country-level outcome
    vp = variance_partition(whole)
    assert vp["between_country_year"] == pytest.approx(1.0)
    assert vp["within_country_year"] == pytest.approx(0.0)
    mixed = pd.DataFrame({"iso2": ["A"] * 4 + ["B"] * 4, "year": 2020,
                          "y": [1.0, 0.0] * 4})             # pure within-country variation
    assert variance_partition(mixed)["within_country_year"] == pytest.approx(1.0)


# ---- real data (skipped on machines without the raw download, e.g. CI) -------------------
real = pytest.mark.skipif(not (paths.MANIFESTS / "espen_sources.csv").exists()
                          or not any(paths.RAW_ESPEN.glob("espen_lf_iu_*.csv")),
                          reason="raw ESPEN extracts not present")


@real
def test_real_files_match_manifest_checksums():
    man = pd.read_csv(paths.MANIFESTS / "espen_sources.csv", dtype=str, keep_default_na=False)
    assert (man["status"] == "ok").all() and len(man) == 48
    for row in man.itertuples():
        data = (paths.RAW_ESPEN / row.local_filename).read_bytes()
        assert hashlib.sha256(data).hexdigest() == row.sha256, row.local_filename


@real
def test_real_files_satisfy_the_schema():
    for f in sorted(paths.RAW_ESPEN.glob("espen_lf_iu_*.csv")):
        df = read_raw_file(f)
        assert set(REQUIRED_COLUMNS) <= set(df.columns)
        assert df["year"].astype(int).between(2014, 2025).all()


def test_namibia_iso_code_is_not_read_as_missing():
    """Regression: pandas reads the string "NA" as missing unless told otherwise."""
    from lf_mda.audit import load_release_calendar
    cal = load_release_calendar()
    assert cal["iso2"].notna().all() and "NA" in set(cal["iso2"])
