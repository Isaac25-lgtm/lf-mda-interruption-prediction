# Reproducibility

## Environment

- Python 3.10 or later (developed on 3.12.10, Windows 11). No GPU is needed.
- Dependencies are declared in `pyproject.toml`; the exact versions used for the
  reported run are in `requirements.lock`.

```bash
git clone https://github.com/Isaac25-lgtm/lf-mda-interruption-prediction.git
cd lf-mda-interruption-prediction
python -m venv .venv
# Windows PowerShell:   .venv\Scripts\Activate.ps1
# Linux / macOS:        source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
```

## Full pipeline

| Step | Command | Time on the development laptop | Writes |
|---|---|---|---|
| 1 | `lf-mda download` | about 6 min | `data/raw/espen_lf/`, `data/manifests/espen_sources.csv` |
| 2 | `lf-mda context` | about 10 min | geometry, UCDP archive, `data/processed/*.parquet` |
| 3 | `lf-mda audit` | under 1 min | `reports/audit/`, `data/processed/panel.parquet` |
| 4 | `lf-mda develop` | about 40 min | `reports/evaluation/development/` |
| 5 | `lf-mda lock` | about 15 min | `reports/evaluation/locked_test/`, `models/` |
| 6 | `lf-mda loco` | about 15 min | `reports/evaluation/country_transport/` |
| 7 | `lf-mda sensitivity` and `lf-mda explain` | a few min | `reports/evaluation/sensitivity/`, `explain/` |
| 8 | `lf-mda report` | under 1 min | `reports/figures/`, `reports/tables/`, `manuscript/figures_and_tables.md` |
| 9 | `lf-mda dashboard-data` | under 1 min | `dashboard/data/` |
| 10 | `streamlit run dashboard/app.py` | | local dashboard at http://localhost:8501 |

`lf-mda all` runs steps 3 to 9 and stops before any model is fitted if the gate is not GO.
Steps 4 to 6 refuse to run without a GO gate decision on disk.

## Determinism

- One seed (`config/protocol.yaml: seed`) drives CatBoost, the bootstrap and sampling.
- Every run writes a manifest to `reports/runs/` with the Git commit, package versions
  and SHA-256 of the protocol, feature manifest, status map and raw-data manifest.
- `lf-mda lock` records a fingerprint in `reports/evaluation/locked_test/LOCK.json`.
  Re-running with the same fingerprint reproduces the same predictions. Running with a
  changed protocol, feature set, model selection or data is refused unless
  `--amend "reason"` is given, and every run is appended to the lock history.
- `tests/test_pipeline.py` fits the models twice on a synthetic panel and requires
  identical predictions.

CatBoost results can differ in late decimal places across operating systems and
CatBoost versions. Compare against the committed tables to three decimals.

## What will not reproduce exactly

- **ESPEN revises its data.** A fresh download may differ from the files analysed
  here. The manifest holds the checksums of the files used (retrieved 12 October 2026);
  `tests/test_ingest_and_gate.py` fails if local files do not match it.
- **UCDP releases new versions.** The code pins version 26.1.
- **The ESPEN download form is not a documented API.** If it changes, follow the manual
  procedure in `data/README.md`.

## What is and is not in Git

Committed: code, configuration, manifests, audit tables, evaluation tables, figures,
the derived dashboard table and model digests. Not committed: raw downloads, the
row-level panel and predictions in `data/processed/`, boundary polygons and model
binaries.
