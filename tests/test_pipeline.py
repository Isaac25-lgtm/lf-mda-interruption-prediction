"""End-to-end model fitting on a SYNTHETIC panel: determinism, isolation, locked-test guard.

Synthetic data here exist only to test software behaviour. No number produced by these
tests is a research result.
"""
import json

import numpy as np
import pandas as pd
import pytest
from conftest import panel_from_patterns

from lf_mda import pipeline
from lf_mda.features import build_features, load_manifest
from lf_mda.labels import load_protocol
from lf_mda.model import SPEC_BY_NAME, SPECS, build_model, grid_for, rank_score
from lf_mda.splits import final_training_index, held_out_index


def synthetic_panel(seed: int = 0, n_countries: int = 5, n_ius: int = 30) -> pd.DataFrame:
    """SYNTHETIC mini-countries with persistent, country-clustered non-delivery."""
    rng = np.random.default_rng(seed)
    patterns = {}
    for c in range(n_countries):
        country_bad = rng.random(12) < 0.15                 # country-wide bad years
        for i in range(n_ius):
            prone = rng.random() < 0.3
            chars, prev_n = [], False
            for t in range(12):
                p = 0.03 + 0.5 * country_bad[t] + 0.15 * prone + 0.25 * prev_n
                miss = rng.random() < p
                chars.append("N" if miss else "m")
                prev_n = miss
            chars[0] = chars[1] = "m"                       # every IU starts active
            patterns[(f"X{chr(65 + c)}", i + 1)] = "".join(chars)
    return panel_from_patterns(patterns)


@pytest.fixture(scope="module")
def feat() -> pd.DataFrame:
    return build_features(synthetic_panel(), 1)


@pytest.fixture(scope="module")
def proto() -> dict:
    return load_protocol()


def _fit_twice(spec_name, params, proto, feat):
    man = load_manifest()
    tr = feat.iloc[final_training_index(feat, proto, 1)]
    te = feat.iloc[held_out_index(feat, proto)]
    out = []
    for _ in range(2):
        m = build_model(SPEC_BY_NAME[spec_name], params, proto, man).fit(tr, tr["y"].to_numpy())
        out.append(m.predict_proba(te))
    return out


@pytest.mark.parametrize("name,params", [
    ("prevalence", {}), ("history_rule", {}), ("country_prior_rate", {}),
    ("logistic_history", {"C": 0.1}), ("catboost_history", {"depth": 2, "l2_leaf_reg": 3}),
])
def test_models_are_deterministic_and_return_probabilities(name, params, proto, feat):
    fast = json.loads(json.dumps(proto))
    fast["models"]["catboost_fixed"]["iterations"] = 30
    a, b = _fit_twice(name, params, fast, feat)
    np.testing.assert_array_equal(a, b)
    assert np.all((a >= 0) & (a <= 1)) and not np.isnan(a).any()


def test_preprocessing_is_learned_from_training_rows_only(proto, feat):
    """Changing held-out feature values must not change a model fitted on training rows."""
    man = load_manifest()
    tr = feat.iloc[final_training_index(feat, proto, 1)]
    m1 = build_model(SPEC_BY_NAME["logistic_history"], {"C": 1.0}, proto, man)
    m1.fit(tr, tr["y"].to_numpy())
    scaler = m1.pipe_.named_steps["pre"].named_transformers_["num"].named_steps["sc"]
    imputer = m1.pipe_.named_steps["pre"].named_transformers_["num"].named_steps["imp"]
    np.testing.assert_allclose(imputer.statistics_, tr[m1.num].median().to_numpy(), rtol=1e-9)
    assert scaler.n_samples_seen_ == len(tr)


def test_training_rows_never_include_held_out_years(proto, feat):
    tr = feat.iloc[final_training_index(feat, proto, 1)]
    assert tr["year"].max() < proto["windows"]["locked_test"][0]
    assert tr["y"].notna().all() and tr["eligible_primary"].all()


def test_history_rule_ranks_by_the_fixed_score(proto, feat):
    man = load_manifest()
    tr = feat.iloc[final_training_index(feat, proto, 1)]
    te = feat.iloc[held_out_index(feat, proto)]
    m = build_model(SPEC_BY_NAME["history_rule"], {}, proto, man).fit(tr, tr["y"].to_numpy())
    r = rank_score(m, te, m.predict_proba(te))
    np.testing.assert_array_equal(r, te["rule_score"].to_numpy())


def test_model_set_is_bounded_and_matches_the_protocol(proto):
    listed = set(proto["models"]["baselines"] + proto["models"]["statistical"]
                 + proto["models"]["machine_learning"])
    assert {s.name for s in SPECS} == listed
    assert len(SPECS) <= 10
    n_configs = sum(len(grid_for(s, proto)) for s in SPECS)
    assert n_configs <= 30                                  # no model proliferation


def test_locked_test_refuses_a_changed_fingerprint(tmp_path, monkeypatch):
    """Adversarial: re-opening the locked test after changing the protocol must fail."""
    dev, lock = tmp_path / "development", tmp_path / "locked_test"
    dev.mkdir()
    lock.mkdir()
    (dev / "selected_configs.json").write_text("{}", "utf-8")
    (dev / "calibrators.json").write_text("{}", "utf-8")
    (lock / "LOCK.json").write_text(json.dumps({
        "fingerprint": {"protocol_sha256": "a-different-protocol"}, "history": [
            {"utc": "2026-01-01T00:00:00Z"}]}), "utf-8")
    monkeypatch.setattr(pipeline, "DEV_DIR", dev)
    monkeypatch.setattr(pipeline, "LOCK_DIR", lock)
    monkeypatch.setattr(pipeline, "load_frames", lambda: (load_protocol(), {}))
    monkeypatch.setattr(pipeline, "sha256_file", lambda p: "current-hash")
    with pytest.raises(RuntimeError, match="already been opened"):
        pipeline.run_locked_test()


def test_modelling_commands_require_a_go_gate(tmp_path, monkeypatch):
    from lf_mda import cli, paths
    monkeypatch.setattr(paths, "AUDIT", tmp_path)
    with pytest.raises(SystemExit, match="No gate decision"):
        cli._require_gate()
    (tmp_path / "gate_decision.json").write_text(json.dumps(
        {"gate": {"decision": "REDESIGN_REQUIRES_APPROVAL"}}), "utf-8")
    with pytest.raises(SystemExit, match="not permitted"):
        cli._require_gate()
    (tmp_path / "gate_decision.json").write_text(json.dumps(
        {"gate": {"decision": "GO_ON_PROXY_LABEL"}}), "utf-8")
    cli._require_gate()
