# Handover: what was attempted, what was found, and why the prediction work stops here

**For:** anyone picking this project up, with or without the original team.
**Snapshot date:** 12 October 2026. Figures quoted here are from that run; the
generated files named beside them are the authority if anything differs.

## 1. The short version

We set out to predict which districts (implementation units, IUs) in African
lymphatic filariasis programmes would miss their next round of mass drug
administration (MDA), using only public WHO ESPEN data, and to test whether
statistical or machine-learning models beat a simple rule based on treatment history.

Every planned stage was carried out: data acquisition, label audit, protocol, model
development, a locked test, transport across countries, sensitivity analyses, a
dashboard and a manuscript draft. The result is that **no model improved on the
simple rule**, and the evidence shows why: the limit is in what the data contain, not
in how the models were built.

**The prediction line of work stops here for a scientific reason, not because it was
left unfinished.** Section 2 sets out that reason. The descriptive findings (how
often rounds are missed, how many people are affected, that failures are mostly
country-wide, how fast programmes recover) stand on their own and are the basis of the
manuscript.

## 2. Why the prediction work stops

### It was completed

| Planned stage | Done | Where to see it |
|---|---|---|
| Acquire all accessible ESPEN LF data | Yes, 48 countries | `data/manifests/espen_sources.csv` |
| Audit the outcome before modelling | Yes | `reports/audit/label_audit.md` |
| Freeze a protocol before fitting anything | Yes | `config/protocol.yaml` |
| Baselines, logistic regression, CatBoost | Yes, 10 approaches | Section 5 below |
| Diagnose poor performance and refine on development data only | Yes, one documented round | `docs/DECISIONS.md` |
| Score a locked later-year test once | Yes | `reports/evaluation/locked_test/LOCK.json` |
| Test in countries left out of training | Yes | `reports/evaluation/country_transport/` |
| Sensitivity analyses | Yes | `reports/evaluation/sensitivity/` |
| Try further model ideas | Yes, 3 exploratory approaches | `reports/evaluation/exploratory_posthoc/` |
| Dashboard, tables, figures, manuscript draft | Yes | `dashboard/`, `reports/`, `manuscript/` |

### The stopping rule was set in advance and it was reached

Before any model was fitted, the protocol fixed what would count as success: a model
had to capture at least 5 percentage points more interruptions than the history rule
when the top 20% of IUs are flagged, with a 95% interval above zero, on a later-year
test opened once. It also fixed a limit of two refinement rounds after a poor
development result, after which feasibility had to be reassessed.

- The primary candidate model missed the criterion: it captured 10.0 percentage points
  *fewer* interruptions than the rule (95% interval -29.1 to +9.7).
- None of the other six fitted models met it.
- In both development rounds every tuned model chose the strongest regularisation on
  offer, which means the best-fitting version of each model was the one closest to
  "predict the average for everyone". More tuning would move further in that
  direction, not towards a better model. The second refinement round was therefore
  declined.
- Three further models designed around the structure of the data did not help either.

### The evidence says the limit is in the data

The audit found that about 61% of the variation in the outcome lies between
country-years, and that a country's failure in one year says little about the next.
District history cannot predict a national shock, and the public data do not contain
the things that would (funding, medicine supply, campaign plans). Section 6 gives the
full list of reasons with the evidence for each.

Continuing to add models to the same data would be model proliferation. It would also
reuse test years that every approach in this repository has now seen. The
scientifically sound options are to stop, or to change the inputs (Section 8).

## 3. What we were trying to do

**Question.** Among IUs with an active LF programme, can information available at 31
December of year t-1 identify the units that will have a reported interruption in year
t? Does a model do better than a simple history rule? Does context (conflict,
population density) add anything?

**Intended use.** A ranking so that a programme with limited supervision capacity
could give extra attention to the 10% or 20% of IUs most at risk. Never for judging or
defunding programmes.

**Design choices worth knowing.**

| Choice | What and why |
|---|---|
| Unit | One IU in one year |
| Outcome | ESPEN status "MDA not delivered" versus "under MDA". A reported status, not verified |
| Cohort | Required MDA at t-1, delivered in t-1 or t-2, fewer than 5 observed effective rounds. The last condition removes IUs that were due for impact assessment, where non-delivery is often legitimate |
| Two information scenarios | P: records to t-1 (what a programme knows). E: records to t-2 (what is public at the time) |
| Windows | Development 2016-2022; locked test 2023-2024; 2020-2021 and 2025 treated as stress years |
| Uncertainty | Bootstrap that resamples whole countries, because events cluster by country |

## 4. What was built and what is deployed

**Pipeline.** `lf-mda download` to `lf-mda dashboard-data`; one command, `lf-mda all`,
runs everything after the download. See `docs/REPRODUCIBILITY.md`.

**Deployed.** A Streamlit dashboard is live at
https://lf-mda-interruption-prediction-kubq9wrtrramveajwfh8qg.streamlit.app/ and is
redeployed automatically on every push to `main`.

What the deployed dashboard is and is not:

- It shows **stored** results: the audit, the descriptive findings, the model
  comparison, and for each IU the out-of-sample score each approach produced.
- It does **not** run a model. No model is served as a live prediction service, and
  none should be: no model earned that.
- Scores for 2019-2022 are development (out-of-fold) predictions; 2023-2024 are from
  the single locked-test run; 2025 is the stress year.

**Fitted model files** are not in Git. `lf-mda lock` rebuilds them exactly; their
SHA-256 digests are in `models/model_digests.json`.

## 5. Every approach that was trained

Generated by `lf-mda report` from the result files (scenario P, locked test
2023-2024: 705 IU-years, 130 interruptions).

<!-- MODELS:START -->
| Approach | Role | Predictors | Setting chosen on development folds | Development log loss | Locked-test AUROC (95% CI) | Interruptions captured in top 20% (95% CI) | Difference from history rule, percentage points (95% CI) |
|---|---|---|---|---|---|---|---|
| No-skill prevalence |  | None (training prevalence for every IU) | none to tune | 0.695 | 0.50 (0.50 to 0.50) | 0.20 (0.20 to 0.20) | -27.7 (-47.9 to +0.0) |
| Country prior rate |  | Country's non-delivery rate the year before | none to tune | 0.686 | 0.59 (0.39 to 0.81) | 0.36 (0.12 to 0.63) | -11.5 (-37.0 to +13.5) |
| History rule | Comparator | Fixed points: missed t-1, missed t-2 or t-3, ineffective round at t-1 | none to tune | 0.688 | 0.65 (0.43 to 0.82) | 0.48 (0.20 to 0.68) | reference |
| Logistic, five predictors |  | 5: missed rounds in 3 years, cumulative rounds, last coverage, region and country non-delivery rates | C = 0.001 | 0.680 | 0.66 (0.44 to 0.81) | 0.42 (0.14 to 0.63) | -6.2 (-25.2 to +9.1) |
| Logistic, IU history only | Primary candidate | IU treatment history (11 predictors) | C = 0.001 | 0.678 | 0.64 (0.43 to 0.79) | 0.38 (0.13 to 0.59) | -10.0 (-29.1 to +9.7) |
| Logistic, programme history |  | IU history plus country and region programme history (17) | C = 0.001 | 0.687 | 0.67 (0.48 to 0.81) | 0.41 (0.17 to 0.59) | -6.9 (-22.7 to +9.4) |
| Logistic, history + context |  | Programme history plus conflict and population density (24) | C = 0.001 | 0.706 | 0.56 (0.32 to 0.76) | 0.18 (0.02 to 0.47) | -30.0 (-53.6 to +5.1) |
| CatBoost, programme history |  | IU history plus country and region programme history (17) | depth = 1, l2_leaf_reg = 30 | 0.732 | 0.62 (0.35 to 0.81) | 0.27 (0.01 to 0.50) | -20.8 (-57.2 to +5.1) |
| CatBoost, history + context |  | Programme history plus conflict and population density (24) | depth = 1, l2_leaf_reg = 30 | 0.754 | 0.59 (0.33 to 0.78) | 0.25 (0.00 to 0.49) | -23.1 (-57.2 to +6.1) |
| CatBoost, history + country ID |  | Programme history plus country identity (18) | depth = 1, l2_leaf_reg = 30 | 0.731 | 0.56 (0.31 to 0.77) | 0.16 (0.00 to 0.44) | -31.5 (-63.6 to +11.3) |
<!-- MODELS:END -->

Hyperparameter grids, including every setting that lost, are in
`reports/evaluation/development/grid_search_log.csv` (round 1) and
`reports/evaluation/development_round0/grid_search_log.csv` (round 0).

The three exploratory approaches tried after the test (a within/between-country
logistic model, a country-then-district ranking, and the rule with a term for fewer
cumulative rounds) are in `reports/tables/tableX_exploratory_posthoc.md`. The closest
was the rule with the extra term: +3.1 percentage points (-2.9 to +6.8).

## 6. The result, stated exactly

- **No model improved on the history rule.** That is the finding.
- The rule had the highest share of interruptions captured at 20% capacity: 48%
  (95% interval 20% to 68%), against 16% to 42% for the fitted models.
- **The rule was not shown to be better than the models either.** Every difference has
  an interval that includes zero. With 130 events from only 14 country-years, the test
  cannot separate them. The accurate summary is "a simple rule does at least as well",
  not "the rule beat machine learning".
- The rule's AUROC was 0.65 (0.43 to 0.82). That is modest. The rule is not a good
  predictor; it is just not a worse one.
- Within a country and year, the fitted models ranked IUs with an AUROC of 0.65 to
  0.73, while the rule was at 0.50 on the test (0.39 in 2023, 0.80 in 2024). So the
  rule's advantage comes from ranking *between* countries. This is the one place where
  models may hold something the rule lacks, and it is uncertain.
- With only data that were public at the decision date (scenario E), every approach
  was near chance (AUROC 0.45 to 0.60).
- Predicted probabilities were poorly calibrated: after the planned recalibration,
  models predicted about twice as many interruptions as occurred.

## 7. Why the models did not beat the rule

Ordered by how much each explains.

| # | Reason | Evidence | File |
|---|---|---|---|
| 1 | **Interruptions are mostly country-wide shocks.** When a country's medicines or funding fail, every IU misses together, and nothing in one IU's history distinguishes it. | 40% of interruptions were in country-years where every eligible IU missed; 70% where most did; 61% of outcome variance is between country-years | `reports/audit/clustering_bands.csv`, `variance_partition.csv` |
| 2 | **The shocks are not persistent**, so even country history predicts them poorly. | A country where most IUs missed did so again the next year in 32% of cases, against 19% otherwise; correlation of a country's rate with the previous year 0.30 | `reports/descriptive/country_persistence.csv` |
| 3 | **The causes are not in the data.** Funding status, medicine supply and campaign plans are known nationally before the year starts and are absent from public ESPEN extracts. | ESPEN's IU Planner holds IU-level funding status but publishes no historical versions | `docs/LITERATURE_SEARCH_LOG.md` |
| 4 | **The world kept changing.** A model trained on earlier years met a different base rate each time. | Yearly interruption rate in the cohort ran from 8% (2017) to 48% (2021), then 13% (2024) and 30% (2025). In the 2020-2021 validation years every approach was near chance | `reports/audit/primary_cohort_outcome_class_by_year.csv` |
| 5 | **There is far less independent information than the row count suggests.** | 8,795 IU-years, but the locked test's 130 events come from 14 country-years, roughly 13 effective events | `reports/audit/variance_partition.csv` |
| 6 | **Flexible models overfit the country-year pattern.** Country-level predictors take one value per country-year, so a flexible model can memorise which country-years were bad. | Every tuned model chose the strongest regularisation in both rounds. CatBoost's log loss was 0.82, then 0.73 after regularisation, against 0.695 for no skill | `reports/evaluation/development*/grid_search_log.csv` |
| 7 | **A rule cannot overfit.** It has no fitted parameters, so shifts between years cost it nothing, and "missed last year" quietly carries the country signal. | Rule AUROC 0.65 on the test and 0.85 in the 2025 stress year | `reports/tables/table3_performance.md` |
| 8 | **The within-country signal is real but small and unstable.** | Rule's within-country-year AUROC: 0.75 in non-COVID development years, 0.39 in 2023, 0.80 in 2024 | `reports/evaluation/locked_test/locked_metrics.csv` |
| 9 | **The outcome is noisy.** Some "interruptions" were probably legitimate pauses. | Up to 16% of cohort interruptions were followed by impact assessment or surveillance rather than resumed MDA | `reports/audit/hindsight_adjudication.csv` |
| 10 | **Performance does not carry between countries.** | With each country held out, the rule's AUROC ranged from 0.05 to 0.95 and was below 0.5 in 11 of the 20 countries with enough events | `reports/evaluation/country_transport/transport_by_country.csv` |
| 11 | **Public data arrive too late.** | With a two-year lag, AUROC 0.45 to 0.60 for all approaches | `reports/evaluation/sensitivity/scenario_P_vs_E_locked_test.csv` |

## 8. What can be trusted, and what was not perfect

### Sound, and safe to build on

- Raw data are checksummed and re-downloadable; nothing was typed by hand.
- The outcome was audited before modelling; missing reports are never counted as
  interruptions.
- No predictor can read the outcome year: tests scramble all later records and confirm
  nothing changes, and a deliberately leaky predictor is caught.
- Splits are forward in time or by country; there are no random row splits.
- The protocol was frozen before fitting; the one amendment was made on development
  data and is dated; the locked test was opened once; a re-run reproduced identical
  predictions.
- Every experiment is logged, including the ones that lost.
- The automated test suite passes locally, and CI runs it on every push.

### Not perfect, and a successor should know

The process was rigorous, but the modelling was not flawless. These are its weak points:

| Weak point | Consequence |
|---|---|
| The outcome has not been reviewed by any programme expert | Every result describes a reported status |
| One refinement round was needed, and its five-predictor model was chosen using all development years | That model's development figures are optimistic |
| Calibration failed on the test years | Only rankings can be discussed, not probabilities |
| Context was limited to conflict and population density; rainfall and travel time were never tested | "Context adds nothing" cannot be claimed |
| 9% of cohort IU-years, including all of Madagascar and Cameroon, have no geometry | Context results rest on an incomplete sample |
| Changes of IU boundaries were not reconciled | Some IUs lose their history |
| Records are today's corrected values, not what was known at the time | A retrospective reconstruction, not a prospective test |
| CatBoost was not re-tuned inside each held-out-country fold | Slight optimism for CatBoost in the transport analysis |
| The decision date (31 December) was never confirmed with a programme | The prediction clock may be wrong |
| The paper was reframed after the test results | The prediction analysis is reported as pre-specified, but readers must be told the order of events |

Full list: `docs/ISSUES.md`.

## 9. What would change the answer

In order of expected value. Each needs something this project did not have.

| # | Next step | Needs | Why it could matter |
|---|---|---|---|
| 1 | **Expert review of the labels** | NTD programme officers; `reports/audit/expert_review_sample.csv` (200 rows) | Without it nothing here can be called validated. It may also show the outcome is cleaner or dirtier than assumed |
| 2 | **Add planning and funding information** | Historical JRSM or IU Planner data, by agreement with ESPEN or national programmes | This is where the cause of country-wide failures is recorded. It is the most likely route to real predictive value |
| 3 | **Model the country-year, not the district** | Reason 1 above; country-level indicators such as donor funding, medicine shipments, elections, conflict | The question "which countries will miss next year" matches where the variation is |
| 4 | **Combine levels** | Step 3 | A country-level signal for *whether*, plus the within-country ranking that the fitted models may have, for *where* |
| 5 | **Test on 2026 data when ESPEN releases it** | Nothing but time | 2026 is the first year no approach here has seen. Score the frozen models and the three exploratory ones on it before changing anything |
| 6 | **Reconstruct IU lineage across boundary changes** | ESPEN cartography by year | Restores history for split or merged IUs |
| 7 | **Add rainfall and travel time** | CHIRPS and an accessibility raster | Completes the context test the concept asked for |
| 8 | **Use the descriptive findings** | A programme co-author | The burden, clustering and recovery results are publishable in their own right (`manuscript/manuscript_draft.md`) |

## 10. Rules for whoever continues

1. **Do not treat 2023, 2024 or 2025 as a test again.** Every approach here has seen
   them. Any new model claim needs a year nobody has analysed.
2. **Change the protocol only by amendment**: add a dated entry to
   `config/protocol.yaml` and `docs/DECISIONS.md`, with the reason.
3. **Do not redefine the outcome to get a better score.** If the outcome changes, say
   why on substantive grounds and report both.
4. **Every new predictor goes in `config/features.yaml`** with its source and lag, and
   the leakage tests must still pass.
5. **Keep the comparator.** Any future model must be compared with the history rule on
   the same IU-years, with country-clustered uncertainty.
6. **Do not describe the label as validated** until experts have reviewed it.
7. **Raw data, boundary polygons and model binaries stay out of Git.**

## 11. Picking it up in ten minutes

```bash
git clone https://github.com/Isaac25-lgtm/lf-mda-interruption-prediction.git
cd lf-mda-interruption-prediction
python -m venv .venv            # then activate it
python -m pip install -e ".[dev]"
python -m pytest -q             # should pass without any data
lf-mda download                 # about 6 minutes
lf-mda context
lf-mda all                      # rebuilds every result; the locked test reproduces
streamlit run dashboard/app.py
```

Read, in this order:

1. This file.
2. `reports/RESULTS_SUMMARY.md` for the numbers.
3. `docs/DECISIONS.md` for every choice and when it was made.
4. `docs/ISSUES.md` for threats to validity.
5. `reports/audit/label_audit.md` for the outcome.
6. `manuscript/manuscript_draft.md` for the paper as it stands.
7. `IDE_RESEARCH_MASTER_CONTEXT.md` for the original brief.
