# Open issues and threats to validity

Ordered by how much each could change the conclusions. "Evidence" points to the file
that shows the problem.

## Could invalidate or reverse conclusions

| # | Issue | Evidence | What would resolve it |
|---|---|---|---|
| I1 | **The label has not been verified.** It is a reported status after WHO's final correction. Nobody with programme knowledge has reviewed it, and no planning data confirm a round was scheduled. | `docs/LABEL_DECISIONS.md` | Expert review of `reports/audit/expert_review_sample.csv`; historical JRSM data |
| I2 | **Legitimate stops inside the positive class.** Up to 16% of primary-cohort events were followed by impact assessment or surveillance. | `reports/audit/hindsight_adjudication.csv` | Same as I1; the `strict` and hindsight-filtered sensitivity analyses bound the effect |
| I3 | **Few independent events.** The locked test has 130 events from 14 country-years. After a country-year design effect that is roughly 13 effective events. | `reports/audit/variance_partition.csv` | More years of data; analysis at country-year level; nothing in the current data |
| I4 | **Hindsight records.** All values are the current corrected database. A status may have been revised after the decision date. | `docs/PREDICTOR_AVAILABILITY.md` | Archived ESPEN snapshots, which are not published |

## Limit what can be claimed

| # | Issue | Evidence | Consequence |
|---|---|---|---|
| I5 | Effective rounds are observed only from 2014, so the expected-round restriction lets through IUs with long earlier histories. | `rounds_before_2014` in the panel | `strict` cohort reported as sensitivity |
| I6 | 2025 is partly released and coincides with a funding shock. Five countries with 2025 rows are missing from the release log. | `reports/audit/country_year_flags.csv` | 2025 is a stress year only |
| I7 | The two-year public-data lag is an assumption before 2025; release dates are documented only for 2024 and 2025 data. | `config/source_release_calendar.csv` | Scenario E is "approximate" |
| I8 | Scenario E keeps the scenario P cohort, which an outside analyst could not construct. | `config/protocol.yaml` | E measures information loss, not a full outside workflow |
| I9 | IU definitions change in 26 countries. An IU created after a split has no history under its new ID and enters the cohort late. Parent-child lineage was not reconstructed. | `reports/audit/iu_lineage_counts.csv` | Possible loss of history; boundary-change sensitivity analysis not done |
| I10 | IU geometry is the 2024 vintage. 9% of cohort IU-years, including all of Madagascar and Cameroon, have no geometry, so their context predictors are missing. | `data/manifests/context_sources.csv` | Context results rest on an incomplete sample |
| I11 | Context is limited to conflict and population density. Rainfall and travel time were not used. | `docs/DECISIONS.md` D11 | "Context adds nothing" would be an overstatement; only these two were tested |
| I12 | CatBoost hyperparameters were not re-tuned inside each leave-one-country-out fold. | `docs/DECISIONS.md` D14 | Small optimistic bias for CatBoost in the transport analysis |
| I13 | The five predictors of `logistic_parsimonious` were chosen using all development years. | `docs/DECISIONS.md` round 1 | Its development estimates are optimistic; the locked test is the check |
| I14 | Coverage values above 100% and populations repeated from the previous year exist in the raw data. | `reports/audit/coverage_qc.csv`, `country_year_flags.csv` | Coverage is clipped and used only as a predictor |
| I15 | Gate thresholds were set by the code author after profiling the data. | `docs/DECISIONS.md` | They document a judgement; they do not validate the label |
| I16 | Predicted probabilities were poorly calibrated on the test years: after the pre-specified recalibration, models predicted about twice as many interruptions as occurred. The recalibration was fitted on folds dominated by 2020-2021. | `reports/evaluation/locked_test/locked_metrics.csv` | Only rankings, not probabilities, can be discussed. The pre-specified recalibration made the Brier score worse than no recalibration |
| I17 | The history rule's ranking within countries was unstable on the test: 0.39 in 2023 and 0.80 in 2024. | `reports/evaluation/locked_test/locked_metrics.csv` | The rule's advantage in share captured comes from ranking across countries, not within them |
| I18 | Three models were designed after the locked test was opened. | `docs/DECISIONS.md` D19 | Labelled exploratory; they cannot support a claim of improvement |
| I19 | The paper was reframed after the test results. | `docs/DECISIONS.md` D20 | The pre-specified prediction analysis is reported unchanged; a reader should still be told the order of events, and the manuscript says so |
| I20 | "Population in interrupted IUs" is the population requiring treatment in those IUs, not a count of people who missed a dose. In the broad cohort it includes IUs that may have paused legitimately. | `src/lf_mda/describe.py` | Report both cohorts; describe the broad figure as an upper bound |
| I21 | Recovery estimates for interruptions that began in 2022-2024 rest on short follow-up and shrinking denominators. | `reports/descriptive/recovery_within_years.csv` | Do not read the lower recent recovery as a confirmed trend |

## Not done

| # | Item | Why it matters |
|---|---|---|
| N1 | Expert review of labels | Without it the model cannot be called validated |
| N2 | Confirmation with a programme that 31 December t-1 is a real decision point | The prediction clock may be wrong |
| N3 | Literature search in Scopus, Web of Science, Google Scholar, thesis and conference indexes | Novelty claim is provisional |
| N4 | Reading the full text of Galiwango et al. 2026 and the WHO 2025 LF progress report | Cited in the concept; not verified here |
| N5 | Ethics exemption and journal requirements | Needed before submission |
| N6 | Confirmation from ESPEN that the derived IU table may be public | See `docs/ETHICS_DATA_USE.md` |
| N7 | Public dashboard deployment, tagged release, Zenodo DOI | Need the repository owner |
| N8 | Decision-curve analysis | Not done: no defensible threshold probability or cost of a missed interruption was available |
| N9 | Formal sample-size calculation for clustered prediction data (Riley et al.) | Only a design-effect approximation was computed |
| N10 | Study registration | TRIPOD+AI asks for it |
