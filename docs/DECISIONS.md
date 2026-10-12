# Decisions log

Every methodological decision, in the order it was made, with the evidence behind it.
Decisions D1-D12 were made on 2026-10-12 **before any model was fitted**. Anything
decided after seeing model performance is marked as such.

| # | Decision | Reason | Decided |
|---|---|---|---|
| D1 | Acquire data through the endpoint the public ESPEN "Download data" form calls (`/api/download-data/{country}/lf/iu/2014/2025`). | The form needs no login, key or terms click-through; the path is published in the site's own public route table; `robots.txt` does not disallow `/api/`. One request per country, 3 s apart. | Before modelling |
| D2 | Treat `admin2`, `admin3` and `altAdmin2` as optional columns; fail on any other schema difference. | The 48 country files have four header variants (39-41 columns). | Before modelling |
| D3 | Identify non-reporting from the status value `Not reported`. | The dictionary lists `JRF_submitted`, but the extract does not contain it. | Before modelling |
| D4 | Primary cohort = IU required MDA at t-1, delivered MDA in t-1 or t-2, and had **fewer than 5 observed effective rounds** at t-1. | An IU with 5 or more effective rounds is due for impact assessment, so non-delivery there is often legitimate. In the data, 43% of such "non-delivery" events were followed by assessment or surveillance, against 16% in the retained cohort. The rule uses only t-1 information. | Before modelling |
| D5 | `Endemic (pending IA)` and post-intervention surveillance in the outcome year are excluded from the binary outcome and counted. | They are legitimate pauses or stops. | Before modelling |
| D6 | Keep three sensitivity cohorts: `broad` (no round restriction), `strict` (rounds before 2014 also counted), `incident` (delivered at t-1). | Effective rounds are observed only from 2014, so D4 is imperfect; these bound the effect. | Before modelling |
| D7 | Windows: development 2016-2022 (rolling validation years 2019-2022), **locked test 2023-2024**, 2025 as a stress year. This replaces the concept's provisional 2024-2025 locked test. | See "2025" below. The concept explicitly made its windows provisional pending the audit. | Before modelling |
| D8 | 2020-2021 stay in the data and are reported separately as COVID-19 stress years. | Dropping them would overstate normal-period performance. | Before modelling |
| D9 | Scenario E (public-data lag) uses features and training labels lagged two years on the same IU-years as scenario P. | The ESPEN release log shows year y data appearing 8 to 17 months after year-end. Cohort membership still uses t-1 status, so E measures the cost of delayed information, not a full external-analyst simulation. | Before modelling |
| D10 | Penalised logistic regression without country fixed or random effects; country enters only through country-level history features. One ablation adds country identity to CatBoost. | A country effect cannot be estimated for an unseen country, and the transport question needs models that do not depend on identity. | Before modelling |
| D11 | Context predictors limited to conflict (UCDP GED 26.1) and population density from ESPEN IU geometry. CHIRPS rainfall and travel-time rasters were not used. | Rainfall for year t is unknown at the decision date and a prior-year anomaly has no clear mechanism for next-year delivery; the travel-time raster is large and its link was not verified. Recorded as a limitation, not as evidence that these factors do not matter. | Before modelling |
| D12 | Dropped `h_log_pop_req` and `h_req_share`. | Population requiring treatment equals total population in almost every cohort row, so both were redundant with `h_log_pop_tot`. | Before modelling |
| D13 | IU-level derived values (status class, centroid, stored risk scores) are committed for the dashboard; raw extracts and boundary polygons are not. | ESPEN states no licence on its download page. WHO's general dataset terms allow reproduction and distribution for public-health purposes with attribution. Committing only a derived table is the conservative reading; the owner can remove `dashboard/data/` if ESPEN advises otherwise. | Before modelling |

| D14 | In leave-one-country-out transport, hyperparameters are tuned inside the training countries for the logistic model only. CatBoost reuses the configuration selected on the temporal development folds. | One CatBoost fit takes about 15 s on the development machine, so nested tuning would need several hours. Consequence: the held-out country contributed to choosing among four shallow CatBoost configurations, a small optimistic bias for CatBoost in the transport analysis. Decided before any transport result was seen. | Before any transport result |

## 2025 as a stress year (D7), decided before modelling

1. **External shock.** The suspension of major external NTD programme funding in early
   2025 could not have been anticipated at a December 2024 decision point. In the
   primary cohort the reported interruption rate was 13% in 2024 (43 of 324) and 30%
   in 2025 (71 of 233).
2. **Incomplete release.** ESPEN released 2025 data in June and August 2026. Five
   countries with 2025 delivery or non-delivery rows (CD, ET, GH, MG, TD) are not in
   the release log, so the status of those rows is uncertain.
3. **No follow-up.** A 2025 non-delivery cannot yet be checked against what the IU did
   next, which is the only label check available in public data.

The primary temporal test is therefore 2023-2024. Results for 2025 are reported as
robustness evidence and must not be pooled into the primary estimate.

## Gate thresholds

The thresholds in `lf_mda.audit.GATE_RULES` were set by the code author after profiling
the data. They are judgement calls, recorded so that a reader can disagree with them.
They are not external standards, and passing them does not validate the label.

## Decisions made after seeing development results

See the dated entries appended below. None may use locked-test results.
