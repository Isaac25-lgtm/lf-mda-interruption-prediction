"""Dashboard tests: every page renders, nothing trains, labels and fallbacks are honest."""
import ast
from pathlib import Path

import pytest

streamlit_testing = pytest.importorskip("streamlit.testing.v1")
AppTest = streamlit_testing.AppTest

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "dashboard"
PAGES = ["page_overview", "page_quality", "page_map", "page_risk", "page_models",
         "page_capacity", "page_validation", "page_methods", "page_limits"]


def _page_script(dash: str, page: str, hide_data: bool = False):
    import sys
    sys.path.insert(0, dash)
    import lib
    if hide_data:                       # simulate a checkout with no derived data
        from pathlib import Path as _P
        lib.DATA = _P(dash) / "no_such_folder"
        lib.load_iu_year.clear()
        lib.load_info.clear()
    import views
    getattr(views, page)()


def run_page(page: str, hide_data: bool = False):
    at = AppTest.from_function(_page_script, args=(str(DASH), page, hide_data),
                               default_timeout=120)
    return at.run()


def _all_text(at) -> str:
    parts = []
    for kind in ("title", "caption", "markdown", "warning", "error", "info", "subheader"):
        parts += [str(e.value) for e in getattr(at, kind)]
    return "\n".join(parts)


@pytest.mark.parametrize("page", PAGES)
def test_every_page_renders_without_error(page):
    at = run_page(page)
    assert not at.exception, [e.value for e in at.exception]
    assert len(at.title) == 1


@pytest.mark.parametrize("page", PAGES)
def test_every_page_carries_the_research_only_or_synthetic_label(page):
    text = _all_text(run_page(page))
    assert ("Retrospective research only" in text) or ("SYNTHETIC DATA" in text)


@pytest.mark.parametrize("page", ["page_overview", "page_map", "page_risk", "page_capacity"])
def test_pages_fall_back_to_a_labelled_synthetic_demo_without_data(page):
    at = run_page(page, hide_data=True)
    assert not at.exception, [e.value for e in at.exception]
    assert any("DEMONSTRATION — SYNTHETIC DATA" in str(e.value) for e in at.error)


def test_capacity_control_recomputes_from_stored_scores():
    at = run_page("page_capacity")
    if not at.select_slider:            # no stored predictions in this checkout
        pytest.skip("stored predictions not present")
    before = at.dataframe[0].value.copy()
    at.select_slider(key="cap_frac").set_value(0.50).run()
    after = at.dataframe[0].value
    assert not at.exception
    assert (after["IUs flagged"] > before["IUs flagged"]).all()
    assert (after["Interruptions captured"] >= before["Interruptions captured"]).all()
    random_row = after[after["Approach"].str.startswith("Random")].iloc[0]
    assert random_row["Share of all interruptions"] == pytest.approx(0.50)


def test_dashboard_code_never_trains_or_loads_a_model():
    """Static check: the dashboard must not import modelling libraries or call fit."""
    banned_imports = {"catboost", "sklearn", "joblib", "lf_mda.pipeline", "lf_mda.model"}
    for f in DASH.glob("*.py"):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for n in names:
                assert not any(n == b or n.startswith(b + ".") for b in banned_imports), (f, n)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in ("fit", "fit_transform", "predict_proba"), (f, node.lineno)


def test_dashboard_requirements_exclude_the_modelling_stack():
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    lines = [ln.split("#")[0].strip() for ln in req.splitlines()]
    assert not any(ln.startswith(("catboost", "scikit-learn")) for ln in lines)
    assert any(ln.startswith("streamlit") for ln in lines)
