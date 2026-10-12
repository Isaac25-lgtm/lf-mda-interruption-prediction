"""SYNTHETIC test fixtures. Nothing here is research data or a research result.

Each IU is described by a 12-character status pattern for 2014-2025:
  M = under MDA (delivered, effective)   m = under MDA (delivered, below 65% coverage)
  N = MDA not delivered                  P = post-intervention surveillance
  I = pending impact assessment          E = non-endemic
  R = not reported                       - = no row in the extract
"""
from __future__ import annotations

import pandas as pd
import pytest

from lf_mda.ingest import OPTIONAL_COLUMNS, REQUIRED_COLUMNS, coerce_numeric
from lf_mda.labels import build_panel, classify_rows, load_protocol

STATUS = {
    "M": ("Endemic (under MDA)", "2"), "m": ("Endemic (under MDA)", "2"),
    "N": ("Endemic (MDA not delivered)", "1"),
    "P": ("Endemic (under post-intervention surveillance)", "3"),
    "I": ("Endemic (pending IA)", "33"), "E": ("Non-endemic", "0"),
    "R": ("Not reported", "999"),
}


def raw_from_patterns(patterns: dict[tuple[str, int], str], pre2014_rounds: int = 0
                      ) -> pd.DataFrame:
    """Build a text-typed frame shaped like `lf_mda.ingest.load_raw` output."""
    rows = []
    for (iso2, iu_id), pattern in patterns.items():
        assert len(pattern) == 12, "pattern must cover 2014-2025"
        cum = pre2014_rounds
        n = eff_n = 0
        for i, ch in enumerate(pattern):
            year = 2014 + i
            if ch == "-":
                continue
            delivered = ch in "Mm"
            effective = ch == "M"
            cum += delivered
            n += delivered
            eff_n += effective
            pop = 100000 + 1000 * i
            requiring = ch in "MmN"
            treat = int(pop * (0.8 if effective else 0.5)) if delivered else 0
            cov = round(100 * treat / pop, 2) if delivered else 0
            name, eid = STATUS[ch]
            rows.append({
                "id": len(rows) + 1, "continent": "Africa", "region": "Synthetic",
                "whoRegion": "AFRO", "admin0": f"Synthetic {iso2}", "admin0Id": 1,
                "admin0Fip": iso2, "admin0Iso2": iso2, "admin0Iso3": iso2 + "X",
                "admin1": f"{iso2}-Region-{iu_id % 2}", "admin1Id": 100 + iu_id % 2,
                "admin2": f"IU{iu_id}", "admin2Id": iu_id, "admin3": "", "altAdmin2": "",
                "admin3Id": 0, "iusAdm": "ADM2", "iusName": f"IU{iu_id}", "iuId": iu_id,
                "iuCode": f"{iso2}X{iu_id:05d}", "year": year, "endemicity": name,
                "popReq": pop if requiring else 0, "popTrg": int(pop * 0.9) if delivered else 0,
                "popTreat": treat, "cov": cov, "epiCov": cov,
                "mdaScheme": "ALB+IVM" if delivered else "Not delivered", "endemicityId": eid,
                "popTot": pop, "popPreSAC": 1, "popSAC": 1, "popAdult": 1, "cumMda": cum,
                "mda": int(delivered), "effMda": int(effective), "mdaN": n, "effMdaN": eff_n,
                "epiMda": int(delivered), "epiEffMda": int(effective), "epiMdaN": n,
                "epiEffMdaN": eff_n,
            })
    df = pd.DataFrame(rows).astype(str)
    df["schema_optional_present"] = ",".join(OPTIONAL_COLUMNS)
    df["source_file"] = "synthetic.csv"
    assert set(REQUIRED_COLUMNS) <= set(df.columns)
    return df


def panel_from_patterns(patterns, **kw) -> pd.DataFrame:
    typed, _ = coerce_numeric(raw_from_patterns(patterns, **kw))
    return build_panel(classify_rows(typed), load_protocol())


@pytest.fixture
def patterns() -> dict:
    return {
        ("XA", 1): "mmmmmmmmmmmm",   # always delivered, never reaches 5 effective rounds
        ("XA", 2): "mmmNmmmNNmmm",   # interruptions, then resumes
        ("XA", 3): "MMMMMNPPPPPP",   # 5 effective rounds, then stops legitimately
        ("XA", 4): "mmRmmmmmmmmm",   # one year not reported
        ("XA", 5): "mm-mmmmmmmmm",   # one year with no row
        ("XA", 6): "NNNNNNNNNNNN",   # never started
        ("XA", 7): "mmmmmmmImmmm",   # pending impact assessment in 2021
        ("XB", 1): "mmmNNNNmmmmm",   # same IU id as XA-1, different country
        ("XB", 2): "mmmmmmmmNmNm",
        ("XB", 3): "EEEEEEEEEEEE",
    }


@pytest.fixture
def panel(patterns) -> pd.DataFrame:
    return panel_from_patterns(patterns)


@pytest.fixture
def cell(panel):
    """Look up one IU-year row of the panel as a Series."""
    def _cell(iso2: str, iu_id: int, year: int) -> pd.Series:
        hit = panel[(panel["iu_key"] == f"{iso2}-{iu_id}") & (panel["year"] == year)]
        assert len(hit) == 1
        return hit.iloc[0]
    return _cell
