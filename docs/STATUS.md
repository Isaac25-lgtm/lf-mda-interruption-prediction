# Project status

**Updated:** 2026-10-12 · **Lifecycle phase:** 11 of 11 reached (release), with the
scientific limits listed below · **Protocol:** v1.1

A new session can resume from this file, `docs/DECISIONS.md` and `docs/ISSUES.md`
without any chat history.

## Where things stand

| Item | State |
|---|---|
| Scientific gate | `GO_ON_PROXY_LABEL`; independent information `LIMITED`; expert label review **pending** |
| Source data | 48 ESPEN LF IU-level country files, 2014-2025, retrieved 2026-10-12; checksums in `data/manifests/espen_sources.csv` |
| Context data | UCDP GED 26.1; ESPEN IU geometry (2024 cartography) for 5,501 IUs |
| Cohort and events | `reports/audit/events_by_window.csv` |
| Models trained | 10 pre-specified approaches under scenarios P and E; 3 exploratory post hoc approaches |
| Validation | Development: rolling origin 2019-2022 (two rounds, both archived). Locked test 2023-2024: opened **once**. 2025: stress year. Leave-one-country-out on development years |
| Main result | No fitted model improved on the fixed history rule. Under the public-data lag, all approaches were near chance. See `reports/RESULTS_SUMMARY.md` |
| Descriptive results | Burden, country-level clustering, recovery: `reports/descriptive/` |
| Manuscript | Full first draft, generated: `manuscript/manuscript_draft.md` |
| Dashboard | Runs locally (`streamlit run dashboard/app.py`); 10 pages; **not deployed** |
| Tests | See "Verification" below |
| Git | `main` on https://github.com/Isaac25-lgtm/lf-mda-interruption-prediction |

## Phases

| Phase | State | Evidence |
|---|---|---|
| 0 Bootstrap | Done | `pyproject.toml`, CI workflow, licence |
| 1 Literature, sources, ethics | Done with gaps | `docs/LITERATURE_*.md`, `docs/ETHICS_DATA_USE.md`; gaps in `docs/ISSUES.md` N3-N6 |
| 2 Raw data and manifest | Done | `data/manifests/` |
| 3 Profiling and label audit | Done; expert review pending | `reports/audit/label_audit.md` |
| 4 Predictors | Done; rainfall and travel time not used | `config/features.yaml` |
| 5 Descriptive analysis | Done | `reports/descriptive/`, figures 3-5 and 13-15 |
| 6 Protocol freeze and baselines | Done | `config/protocol.yaml` v1.0, amended to v1.1 before the test |
| 7 Machine learning | Done; one refinement round used, second declined | `docs/DECISIONS.md` |
| 8 Locked evaluation | Done, once | `reports/evaluation/locked_test/` |
| 9 Interpretation, tables, uncertainty | Done | `reports/tables/`, `reports/evaluation/explain/` |
| 10 Dashboard | Done locally; deployment needs the owner | `dashboard/` |
| 11 Release packaging | Pushed; no tag, no Zenodo DOI | this file |

## Verification

```bash
python -m pytest -q                      # unit, adversarial, pipeline, dashboard tests
lf-mda audit                             # reproduces reports/audit/
lf-mda lock                              # reproduces the locked test (same fingerprint)
streamlit run dashboard/app.py           # http://localhost:8501
```

## What only a person can do next

1. **Get the labels reviewed.** Send `reports/audit/expert_review_sample.csv` (200 rows
   in five strata) to NTD programme officers who know the countries concerned.
   Without this the paper cannot claim the outcome is valid.
2. **Recruit at least one programme co-author** and confirm that 31 December is a
   realistic decision date.
3. **Add the missing citations** flagged in the manuscript draft, and read the two
   sources that were only checked by title (`docs/LITERATURE_MATRIX.md`).
4. **Confirm with ESPEN** that the derived IU table in `dashboard/data/` may be public.
5. **Confirm ethics and journal requirements**; complete the official TRIPOD+AI form.
6. **Deploy the dashboard** (`dashboard/README.md`), then tag a release and archive it
   on Zenodo.
7. **Search Scopus, Web of Science and Google Scholar** before claiming novelty.

## Next steps a coding agent could take

- When 2026 ESPEN data are released, score the frozen models and the three exploratory
  approaches on 2026 as the first truly untouched year.
- Reconstruct IU lineage across boundary changes and repeat the audit.
- Add rainfall (CHIRPS) and travel time as context and re-run development only.
- Repeat the descriptive analysis at country-year level with funding or supply
  indicators if any become public.
