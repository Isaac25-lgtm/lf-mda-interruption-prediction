# TRIPOD+AI tracking

Working tracker against TRIPOD+AI (Collins et al., BMJ 2024;385:e078378,
https://doi.org/10.1136/bmj-2023-078378). Item topics below are paraphrased from
memory of the statement. **Before submission, complete the official checklist from the
EQUATOR Network and replace this tracker with it.**

Status: Done = reported in the repository; Partial = started; Open = not yet done.

| Topic | Status | Where |
|---|---|---|
| Title identifies the study type, target population and outcome | Partial | Title in `manuscript/manuscript_template.md`; it leads with the descriptive findings and names the prediction evaluation |
| Structured abstract | Done (draft) | `manuscript/manuscript_draft.md` |
| Background, rationale and existing models | Done | `docs/LITERATURE_MATRIX.md`, `docs/LITERATURE_SEARCH_LOG.md` |
| Objectives | Done | `manuscript/manuscript_draft.md`, Introduction |
| Data sources, dates and settings | Done | `docs/DATA_DICTIONARY.md`, `data/manifests/` |
| Participants (units), eligibility | Done | `docs/LABEL_DECISIONS.md`, `config/protocol.yaml` |
| Data preparation and quality checks | Done | `reports/audit/label_audit.md` |
| Outcome definition and how it was assessed | Done, with proxy caveat | `docs/LABEL_DECISIONS.md` |
| Predictors: definition and timing | Done | `config/features.yaml`, `docs/PREDICTOR_AVAILABILITY.md` |
| Sample size | Done | `reports/audit/events_by_window.csv`, `variance_partition.csv` |
| Missing data handling | Done | Missing labels excluded and bounded; predictor imputation inside the model pipeline |
| Analytical methods, model types, tuning | Done | `config/protocol.yaml`, `src/lf_mda/model.py`, `reports/evaluation/development/grid_search_log.csv` |
| Class imbalance handling | Done | No resampling or weighting was used |
| Evaluation: measures, calibration, uncertainty | Done | `src/lf_mda/evaluate.py`, `src/lf_mda/uncertainty.py` |
| Fairness | Partial | Performance by country reported; no formal fairness framework applied |
| Model output and how predictions are used | Done | Risk ranking for top 10% and 20% capacity |
| Differences between development and evaluation data | Done | Windows and stress years in `config/protocol.yaml` |
| Ethical approval | Open | Exemption not yet confirmed (`docs/ETHICS_DATA_USE.md`) |
| Open science: protocol, registration, data and code sharing | Partial | Protocol and code public; **study not registered**; raw data re-downloadable |
| Patient and public involvement | Open | None. No programme staff were involved |
| Flow of units, with numbers | Done | `reports/figures/fig2_cohort_flow.png` |
| Characteristics by data set | Done | `reports/tables/table1_cohort_by_window.csv`, `table2_population_by_country.csv` |
| Full model specification | Partial | Coefficients and model digests saved; binaries not committed |
| Performance with confidence intervals | Done | `reports/tables/table3_performance.csv` |
| Model updating | Not applicable | No updating was done |
| Interpretation, limitations, usability | Done | README, dashboard "Limitations" page, `docs/ISSUES.md` |
| Funding and conflicts of interest | Open | To be supplied by the researcher |

PROBAST+AI (Moons et al., BMJ 2025;388:e082505) should be used as a self-appraisal
before submission. The main risk-of-bias concerns already identified are the unverified
outcome, the use of corrected rather than as-known data, and the small number of
independent country-years in the test.
