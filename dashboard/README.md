# Dashboard

A Streamlit research dashboard over the stored results of this study. It reads files;
it never trains or scores a model.

## Run locally

```bash
python -m pip install -r requirements.txt     # or: pip install -e ".[dev]"
streamlit run dashboard/app.py
```

Then open http://localhost:8501.

## Pages

| Page | Shows |
|---|---|
| Study overview | Headline counts, gate decision, Africa map of interruption rate by country and year |
| Data quality | Reported status by year, cohort flow, reporting gaps, contradictions, release dates |
| Implementation-unit map | One point per IU, coloured by reported status and cohort membership |
| Risk explorer | Stored out-of-sample scores per IU for a chosen year, country and approach |
| Model comparison | Estimates with country-clustered intervals; differences against the history rule |
| Capacity prioritisation | Interruptions each ranking would have found at a chosen support capacity |
| Validation & uncertainty | Country jackknife, yearly stability, countries held out of training, sensitivity analyses |
| Methods | Design summary |
| Limitations & citation | What the results do not show; sources; how to cite |

## What it reads

| File | Built by |
|---|---|
| `dashboard/data/iu_year.parquet`, `country_year.csv`, `countries.csv`, `info.json` | `lf-mda dashboard-data` |
| `reports/audit/*.csv` | `lf-mda audit` |
| `reports/evaluation/**/*.csv` | `lf-mda develop`, `lock`, `loco`, `sensitivity` |
| `reports/figures/*.png` | `lf-mda report` |

Scores shown for 2019-2022 are out-of-fold development predictions. Scores for
2023-2024 come from the single locked-test run, and 2025 is the stress year.

If `dashboard/data/iu_year.parquet` is missing, the app shows a small made-up dataset
under a red **DEMONSTRATION — SYNTHETIC DATA** banner.

## Deploy to Streamlit Community Cloud

Not done yet. It needs the repository owner's own sign-in.

1. Go to https://share.streamlit.io and sign in.
2. Choose **Create app**, then **Deploy a public app from GitHub**.
3. Repository `Isaac25-lgtm/lf-mda-interruption-prediction`, branch `main`, main file
   path `dashboard/app.py`.
4. Under **Advanced settings** choose Python 3.12. No secrets are needed.
5. Deploy. The app installs from the root `requirements.txt`, which holds only the
   dashboard's runtime (no CatBoost, no scikit-learn).
6. Open every page once, then add the URL to the top of the root `README.md` and change
   the dashboard badge.

The app holds about 60,000 IU-year rows in one cached table and should run within the
free tier. If it does not, move to a managed host rather than cutting the validation
pages.

## Tests

`tests/test_dashboard.py` renders every page, checks the research-only banner, checks
the synthetic fallback and its label, confirms the capacity control recomputes from
stored scores, and statically confirms the dashboard imports no modelling library.
