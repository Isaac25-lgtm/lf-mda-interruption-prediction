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

### 2026-10-12, refinement round 1 (after development round 0; locked test unopened)

**What round 0 showed** (rolling-origin folds 2019-2022, scenario P; full output
archived in `reports/evaluation/development_round0/`):

- Pooled AUROC was about 0.60 for every approach, including the no-skill prevalence
  baseline (0.598). That baseline scores above 0.5 only because its constant
  prediction differs by fold year, which shows that pooled AUROC here mostly measures
  differences between years.
- Within country-year, the fixed history rule ranked IUs best (AUROC 0.655). CatBoost
  reached 0.62 and the logistic models 0.53 to 0.59.
- Probabilities were poor: log loss was 0.65 to 0.70 for the baselines and logistic
  models against 0.695 for no skill, and 0.80 to 0.82 for CatBoost, which was strongly
  overconfident (calibration slope about 0.2).
- In 2020 and 2021 pooled AUROC was at or near chance for every approach. In 2019 and
  2022 the rule's within-country-year AUROC was 0.75.

**Diagnosis** (development years only):

1. The selected logistic penalty was at the edge of the grid (C = 0.01), and CatBoost
   log loss fell with shallower trees and a stronger penalty. Both point to overfitting.
2. `h_years_in_extract` has no within-country signal (stratified AUROC 0.50) but a
   pooled AUROC of 0.65. It is a proxy for calendar year, so models used it to
   extrapolate year-level prevalence trends.
3. Country-level predictors take one value per country-year, so a flexible model can
   use them to memorise the outcome of training country-years.
4. Single predictors carry real within-country signal: fewer cumulative rounds
   (stratified AUROC 0.71 when reversed), non-delivery in the same region last year
   (0.65), non-delivery count over three years (0.65), lower coverage of the last round
   (0.60 reversed). The fitted models were not exploiting these.

**Changes made (protocol v1.1), all on development evidence only:**

| # | Change | Reason |
|---|---|---|
| A1 | Remove `h_years_in_extract` | Calendar-time proxy with no within-country signal (diagnosis 2) |
| A2 | Stronger regularisation grids: logistic C in {0.001, 0.01, 0.1}; CatBoost depth in {1, 2}, L2 in {10, 30}, 150 iterations | Diagnosis 1 and 3 |
| A3 | Add one model, `logistic_parsimonious`, with five predictors: `h_nd_count_3`, `h_cum_mda`, `h_epi_cov_last_round`, `a_nd_rate_recent`, `c_nd_rate_recent` | The playbook permits a simple monotone logistic model after a poor development result. The five predictors were chosen from diagnosis 4 |

**Caveats that follow from this.** The predictors in A3 were chosen using all
development years, including the validation folds, so development estimates for
`logistic_parsimonious` are optimistic. Only the locked test is an honest check of it.
This was the first of at most two permitted refinement rounds. No locked-test result
had been computed when these changes were made.

### 2026-10-12, after refinement round 1 (locked test still unopened)

**What round 1 showed** (`reports/evaluation/development/`, scenario P, folds 2019-2022):

- Every tuned model again selected the most regularised setting on offer (logistic
  C = 0.001; CatBoost depth 1, L2 30). CatBoost log loss improved from about 0.82 to
  0.73 but stayed worse than the no-skill value of 0.695.
- Pooled over 2019-2022, no approach differed from the history rule in interruptions
  captured at 20% capacity with an interval excluding zero. The rule still had the
  best or equal-best ranking within country-year (0.655; five-predictor logistic 0.657).
- In the non-COVID folds (2019 and 2022) the logistic models captured 37% to 45% of
  interruptions at 20% capacity against 34% for the rule, with intervals spanning zero.
- In 2020-2021 all approaches were close to chance.

**Decisions:**

| # | Decision | Reason |
|---|---|---|
| D15 | Stop refining. The second permitted round is not used. | Both rounds pushed every model to the most regularised corner of its grid. Further tuning would move towards the intercept-only model, not towards a better one. The limit is the signal in the data, not the hyperparameters |
| D16 | Primary candidate for the locked test: `logistic_iu_only` (C = 0.001). | It has the lowest pooled rolling-origin log loss among fitted models (0.678), which is the selection rule fixed in the protocol |
| D17 | All ten approaches are scored on the locked test, but only the primary candidate against the history rule is the pre-specified comparison. The others are exploratory and unadjusted for multiple comparisons. | Avoids choosing a winner after seeing the test |
| D18 | Leave-one-country-out transport also includes `logistic_iu_only`. | It is the primary candidate |

Expectation recorded before opening the locked test: on development evidence the most
likely result is that no model shows a clear gain over the history rule.

### 2026-10-12, after the locked test was opened

The locked test was opened once (`reports/evaluation/locked_test/LOCK.json`). The
pre-specified criterion for improvement over the history rule was not met by the
primary candidate or by any other fitted model. Everything below was decided **with
knowledge of the locked-test results** and is labelled accordingly.

| # | Decision | Reason | Status of resulting evidence |
|---|---|---|---|
| D19 | Three further approaches were tried at the researcher's request ("propose other models based on the data"): a within/between-country logistic model, a country-then-district ranking, and the history rule with a term for fewer cumulative rounds. They live in `src/lf_mda/exploratory.py` and write to `reports/evaluation/exploratory_posthoc/`. The protocol, the lock fingerprint and Table 3 are untouched. | The audit showed about 60% of variance between country-years, so approaches built around that structure were the natural ones to try | **Exploratory, post hoc.** Tuned on development folds, but designed after the test was seen. Their held-out figures are not an independent test. None cleared the criterion |
| D20 | The paper is reframed. The main results are now the scale of reported interruptions, their country-level clustering and recovery after them; the prediction comparison is one section with a negative result. A descriptive module (`src/lf_mda/describe.py`) was added. | The researcher asked for something publishable. A prediction-tool paper is not supported by the evidence. The descriptive findings do not depend on a held-out test and are the stronger contribution | Descriptive. Not affected by test reuse. Still subject to the proxy-label caveat |
| D21 | A full manuscript draft is generated from a template whose every number is filled from result files (`lf-mda manuscript`). | Prevents hand-typed figures from drifting from the data | The draft is unreviewed and lists its open items |
| D22 | No further model will be evaluated on 2023-2025 as if it were a test. Any future model claim needs data for a year that no one has yet analysed (2026 onwards). | The held-out years have now been seen by every approach in this repository | Standing rule |

**Why the reframing is not outcome switching.** The prediction question, its outcome,
cohort, test window and success criterion are reported exactly as pre-specified, with
their negative result. The descriptive analyses answer objective 1 of the concept
(build and audit the panel) and add burden and recovery measures that use the same
cohort and outcome definitions. Nothing was redefined to obtain a positive result.
