# Missed rounds of lymphatic filariasis mass drug administration in Africa, 2016-2025: scale, country-level clustering, recovery, and the limits of district-level prediction from public WHO ESPEN data

**Draft status.** First full draft, generated from `manuscript/manuscript_template.md`
with every number filled in from result files by `lf-mda manuscript`
(ESPEN data retrieved 2026-10-12). It has not been reviewed by a co-author or a
programme expert. Items marked **[to do]** or **[citation needed]** must be resolved
before submission. The outcome is a reported administrative status that has not been
independently verified.

**Author.** Omoding Isaac (affiliation to be confirmed). **[to do: co-authors, including
at least one NTD programme expert who has reviewed the outcome labels]**

---

## Abstract

**Background.** Elimination of lymphatic filariasis (LF) depends on consecutive rounds
of mass drug administration (MDA). When a round is missed, elimination is delayed.
How often rounds are missed, at what scale, at what level of the health system, and
whether missed rounds can be anticipated has not been described across Africa using
public data.

**Methods.** We downloaded implementation-unit (IU) data for 2014-2025 for all
48 countries on the public WHO ESPEN portal (65,454 IU-year records,
6,236 IUs). We defined an active-programme cohort (required MDA in the previous year,
delivered a round in one of the two previous years, fewer than five observed effective
rounds) and classified each IU-year as delivered or as a reported interruption ("MDA
not delivered"), holding non-reporting, pauses for impact assessment and stops for
surveillance apart. We described the population affected, the share of variation lying
between countries, and recovery after an interruption. We then compared a fixed rule
based on treatment history with penalised logistic regression and gradient boosting,
tuned on 2016-2022 and scored once on a locked 2023-2024 test, with uncertainty from
resampling whole countries.

**Findings.** The cohort held 8,795 IU-years and 1,839 reported
interruptions (20.9%) in 32 countries. In 2021, IUs
with a reported interruption held 77 million people requiring treatment
(51% of the cohort's population requiring treatment); across all
active programmes the figure was 175 million. Interruptions were mostly
country-wide: 40% occurred in country-years in which every eligible IU
missed the round, and 61% of outcome variance lay between country-years.
After an interruption that began in 2016-2019, 55% of IUs resumed MDA within
one year and 75% within three. On the locked test (705 IU-years,
130 interruptions from 14 country-years), the history rule
captured 48% (95% CI 20% to 68%) of interruptions at 20% capacity, with AUROC 0.65 (95% CI 0.43 to 0.82).
The pre-specified candidate model, logistic regression on IU history, did not improve on it
(difference in share captured: -10.0 percentage points (95% CI -29.1 to +9.7)), and none of
7 fitted models did. Using only data that would have been public at
the decision date, every approach was close to chance (AUROC 0.45 to 0.60).

**Conclusions.** Missed LF rounds in Africa have been frequent, large in scale and
mostly determined at country level, and most are followed by resumption. Public
programme data do not support district-level prediction beyond a simple rule, and with
realistic publication delays they support none. Early warning should rest on
country-level funding, supply and planning information rather than on district risk
scores. These conclusions rest on a reported status that still needs expert
verification.

## Author summary

Lymphatic filariasis is a disabling parasitic disease that countries are eliminating by
treating whole communities once a year for several years. Missing a year sets a
district back. We used data that the World Health Organization publishes for every
district in Africa to ask three questions: how often are treatment rounds missed, are
these local or national failures, and can they be predicted in time to help? We found
that missed rounds are common, that in the worst year the affected districts were home
to tens of millions of people, and that most missed rounds happen when a whole country
misses at once. Districts usually resume treatment within a year or two. We then
tested whether statistical and machine-learning models could pick out the districts at
risk. They could not do better than a simple rule based on what a district did in the
previous three years, and when we allowed only the data an outside analyst would have
had at the time, nothing worked. The practical message is that the information needed
to anticipate missed rounds sits at national level, in funding and supply plans, not
in district histories.

## Introduction

LF is targeted for elimination as a public health problem through annual MDA and
morbidity management. An IU must deliver several consecutive effective rounds before
it can be assessed for stopping treatment **[citation needed: WHO guidance on the
number of effective rounds before pre-TAS and TAS]**. A missed round therefore delays
the point at which treatment can stop.

Programmes and their partners have limited capacity for supervision and contingency
support, and they must decide where to put it before the treatment year begins. Two
things would help that decision: knowing how large and how frequent interruptions
are, and knowing whether they can be anticipated at the level where support is
allocated.

Previous work has examined how well rounds perform once delivered. Fuller and
colleagues modelled epidemiological coverage of 3,880 delivered LF rounds in ten West
African countries and found associations with rainfall, conflict, epidemics and
programme maturity, using a restricted programme database [1]. That study, by design,
did not include rounds that never took place, and it did not test prediction on later
years. Ng and colleagues documented denominator, reporting and consistency problems
in the ESPEN database using soil-transmitted helminthiasis data [2], which means any
analysis of ESPEN must examine the outcome before modelling it. Modelling studies have
estimated the consequences of missed rounds [3]. A dated search (Supporting
information) found no study that describes or predicts non-delivery of expected LF
rounds at IU level across countries.

We therefore set out to (1) build and audit a multi-country IU-year panel that
separates reported interruptions from non-reporting, never-started programmes and
legitimate pauses; (2) describe the scale, level and aftermath of interruptions; and
(3) test whether a history rule, logistic regression or gradient boosting can identify
IUs at risk before the year begins, on later years and in countries left out of
training. We stated in advance that history alone might be sufficient, that context
might add nothing, and that country might dominate.

## Methods

### Data sources

We downloaded LF IU-level data for 2014-2025 for each of the 48
countries offered by the public ESPEN download form on 2026-10-12. The form requires
no registration. Files were stored unchanged with SHA-256 checksums. The extract
contains, for each IU and year, the endemicity status reported through the Joint
Reporting Form after final correction, populations, population treated, coverage,
the drug scheme and cumulative round counters.

Conflict events came from the UCDP Georeferenced Event Dataset version 26.1 [4,5].
IU centroids and areas were derived from ESPEN's 2024 provisional cartography.

### Outcome

The outcome is the ESPEN status in year t: "Endemic (MDA not delivered)" (reported
interruption) versus "Endemic (under MDA)" (delivered). We treated "Not reported" and
absent records as missing outcomes, never as interruptions. "Endemic (pending IA)",
post-intervention surveillance and non-endemic status in year t were excluded and
counted. Records whose status contradicted the treatment fields were quarantined.

This outcome is an administrative proxy. It was not verified against independent
records, and no medicine-request data were available to confirm that a round had been
planned.

### Cohort and prediction clock

The decision date was 31 December of year t-1. An IU-year t entered the cohort if,
using only records dated t-1 or earlier, the IU required MDA in t-1, had delivered a
round in t-1 or t-2, and had fewer than five effective rounds observed in the extract.
The last condition restricts the cohort to IUs for which another round, rather than an
impact assessment, was the expected next step. Because effective rounds are observed
only from 2014, we also report a stricter cohort that counts all rounds delivered
before 2014, a broad cohort with no round restriction, and an incident cohort of IUs
that had delivered in t-1. Target years were 2016 to 2025.

### Descriptive analysis

For each year we counted eligible IUs, reported interruptions and the population
requiring treatment in IUs with a reported interruption. This is the population of
affected IUs, not a count of confirmed missed doses. We partitioned outcome variance
into components between countries, between country-years and within country-years,
and counted events in country-years in which every, most, or half or fewer eligible
IUs missed the round. For each interruption that began after a delivered round we
recorded whether and when MDA resumed. We measured how well a country's interruption
rate in one year predicted the next.

### Prediction approaches

Predictors described IU treatment history (non-delivery in each of the three
preceding years, coverage and effectiveness of the last round, drug scheme, cumulative
rounds, population), country and region programme history (share of other IUs that
missed the previous round), and context (conflict events in the IU and country,
population density). Under scenario P, predictors and training outcomes used records
up to t-1, as a programme would have. Under scenario E they used records up to t-2,
reflecting the 8 to 17 months that elapsed before ESPEN published a year's data.

We compared 10 approaches: a no-skill prevalence baseline; the country's
prior-year non-delivery rate; a fixed history rule (4 points for non-delivery in t-1,
2 for any non-delivery in t-2 or t-3, 1 for a round in t-1 below 65% coverage, ties
broken by lower coverage); four penalised logistic models; and three CatBoost models.
No resampling or class weighting was used.

### Development, locked test and stress years

The protocol was fixed before any model was fitted. Models were tuned by rolling-origin
validation within 2016-2022 (validation years 2019 to 2022, each using only earlier
years for training), selecting hyperparameters by pooled log loss. The years 2023-2024
formed a locked test that was scored once. We treated 2020-2021 (COVID-19) and 2025 as
stress periods and report them separately; 2025 was assigned to this role before
modelling because of the suspension of major external NTD funding early that year
**[citation needed]**, because 2025 data were still being released, and because a 2025
interruption cannot yet be checked against what followed.

After a first development round in which every model performed poorly, we made one
documented set of changes using development data only: we removed a predictor that
acted as a proxy for calendar year, moved the tuning grids towards stronger
regularisation, and added a five-predictor logistic model. The primary candidate for
the locked test was then fixed as the fitted model with the lowest pooled development
log loss. All approaches were scored on the locked test, but only the comparison of
the primary candidate with the history rule was pre-specified; the others are
exploratory.

### Performance measures and uncertainty

We report the area under the ROC curve (AUROC), the AUROC computed only among IUs in
the same country and year, the share of interruptions captured when the top 10% or
20% of IUs are flagged, the Brier score and calibration measures. Tied scores at the
capacity cut-off were handled by expected value. Intervals are 95% percentile
intervals from 2,000 bootstrap resamples of whole countries, and we repeated the
locked-test analysis leaving out one country at a time. The pre-specified criterion
for a meaningful improvement was a gain of at least 5 percentage points in
interruptions captured at 20% capacity with an interval above zero.

Transport across countries was tested by predicting each country from models trained
on all the others, within development years.

### Reporting and reproducibility

Reporting follows TRIPOD+AI [6]. All code, the protocol, the decisions log and every
result file are public (see Data and code availability). Automated tests confirm that
no predictor changes when records after the information cut-off are scrambled.

## Results

### Data and cohort

The extract held 65,454 IU-year records for 6,236 IUs. Reported status agreed
with the treatment fields in all but 0.02% of delivered or non-delivery
records. Programme coverage exceeded 100% in 17% of delivered records
and epidemiological coverage in 4%, so the denominator problems
described for soil-transmitted helminthiasis [2] are also present in LF records.
1,512 records carried the status "Not reported", mostly as whole-country
years.

Of 12,961 IU-years in active programmes, 3,503 were excluded
because the IU already had five or more observed effective rounds. The primary
analysis set comprised 8,795 IU-years with 1,839 reported
interruptions (20.9%) in 32 countries,
30 of which contributed at least one event (Fig 2, Table 1,
Table 2).

### How far the outcome can be trusted

Among interruptions up to 2022 in the primary cohort, 78% were followed
by resumed MDA and 16% by impact assessment or surveillance. Among IUs
excluded for having five or more effective rounds the latter share was
43%. The restriction therefore removes much, but not all, of the
contamination by legitimate pauses. A later move to surveillance does not prove that
the earlier non-delivery was legitimate, so 16% is an upper bound.

### Scale

In 2019, before the pandemic, IUs with a reported interruption held
36 million people requiring treatment (15% of the
cohort's population requiring treatment). This rose to 77 million
(51%) in 2021, fell to 5 million
(8%) in 2024, and rose again to 13 million
(28%) in 2025 (Fig 13, Table 5). Counting all active programmes,
including IUs with five or more effective rounds, the 2021 figure was
175 million (62%) and the 2025 figure 29
million (29%). Summed over 2016-2025, the primary cohort accumulated
314 million person-rounds in IUs with a reported
interruption (522 million across all active programmes). Four
countries accounted for 66% of this total: Nigeria (34%), Zambia (12%), Madagascar (12%), Democratic Republic of the Congo (9%).

### Level: country-wide rather than local

Of 220 country-years in the cohort, 97 had at least one reported
interruption and only 61 had both outcomes. 40% of
interruptions occurred in country-years in which every eligible IU missed the round,
and 70% in country-years in which more than half did (Fig 4, Fig 14).
61% of outcome variance lay between country-years and 16%
between countries averaged over years (Table 7). In 2025, 72% of
interruptions were in countries where every eligible IU missed.

A country's interruption rate was only weakly related to its rate the year before
(Spearman correlation 0.30 over 142 country-year pairs). A
country in which most IUs missed the round did so again the next year in
32% of cases, against 19% for countries that had
not. Country-wide failures were therefore largely new shocks rather than a standing
condition.

### Recovery and repetition

Of 593 interruptions that began in 2016-2019, 55% were followed by
resumed MDA within one year, 67% within two and 75% within three
(Fig 15, Table 6). For interruptions that began in 2020-2021 the figures were
68%, 83% and 85%; for 2022-2024, with shorter follow-up,
38% resumed within one year.

Of the IUs that were ever in the cohort, 50% never had a reported
interruption. 23% (480 IUs) had two or more, and
these accounted for 69% of all interruptions.

### Can interruptions be predicted?

**Development.** Across the 2019-2022 validation years, no fitted model had a lower
log loss than the no-skill baseline by a useful margin (no-skill 0.695;
best fitted model 0.678; CatBoost 0.732, down from
0.82 before regularisation was strengthened). Every tuned model selected
the most regularised setting offered. In 2020-2021 the pooled AUROC of every approach
ranged from 0.48 to 0.57. Outside those years the history rule ranked IUs
within a country with an AUROC of 0.75 and captured
34% of interruptions at 20% capacity (Table S1).

**Locked test, 2023-2024.** The test comprised 705 IU-years in 20
countries with 130 interruptions, which came from 11
countries and 14 country-years; allowing for clustering by country-year,
this is equivalent to roughly 13 independent events. The history
rule had an AUROC of 0.65 (95% CI 0.43 to 0.82) and captured 48% (95% CI 20% to 68%) of interruptions at
20% capacity and 23% (95% CI 7% to 47%) at 10%. The primary candidate,
logistic regression on IU history, had an AUROC of 0.64 (95% CI 0.43 to 0.79) and captured 38% (95% CI 13% to 59%). The
difference in share captured at 20% capacity was -10.0 percentage points (95% CI -29.1 to +9.7), so the
criterion for a meaningful improvement was not met. Of the 7 fitted
models, none met the criterion and all captured
fewer interruptions than the rule (Table 3, Fig 6, Fig 9). CatBoost on programme
history captured 27% (95% CI 1% to 50%).

The picture within countries was different but no more certain. The rule's AUROC
among IUs of the same country and year was 0.50 (95% CI 0.25 to 0.81); in 2023 it was
0.39 and in 2024 0.80. The fitted models ranged from
0.65 to 0.73 on this measure, with intervals as wide as the rule's.

Leaving out one country at a time, the rule's share captured at 20% capacity ranged
from 41% to 54% and its AUROC from 0.60 to 0.70.

Predicted probabilities were poorly calibrated. After the pre-specified recalibration
on development folds, observed-to-expected ratios were 0.41 to 0.51: models predicted
about twice as many interruptions as occurred, because recalibration was fitted on
years dominated by the pandemic. For the history rule the Brier score was
0.177 after recalibration and 0.146 before.

**Public data only.** Under scenario E, on the same IU-years, AUROC ranged from
0.45 to 0.60 across approaches; the history rule had an AUROC of 0.45 (95% CI 0.24 to 0.65) and
captured 20% (95% CI 5% to 39%) at 20% capacity.

**2025 stress year.** Among 233 IU-years with 71 interruptions, the
history rule had an AUROC of 0.85 (95% CI 0.62 to 0.95) and captured 52% (95% CI 8% to 65%); the
primary candidate had an AUROC of 0.77 (95% CI 0.48 to 0.90) and CatBoost 0.65 (95% CI 0.36 to 0.84). These
figures are robustness evidence only.

**Countries left out of training.** Pooled over held-out countries in development
years, the history rule had an AUROC of 0.59 (95% CI 0.47 to 0.67) and a within-country-year
AUROC of 0.69 (95% CI 0.62 to 0.75); the primary candidate had an AUROC of 0.68 (95% CI 0.59 to 0.75).
Only 20 of 32 countries had enough events and non-events for a
country-specific estimate. Among them the rule's AUROC ranged from
0.05 to 0.95 and was below 0.5 in 11 (Fig 11, Table
S2). Performance in one country therefore says little about another.

**Sensitivity analyses.** In the stricter cohort (94 events) the
rule captured 50% at 20% capacity and the primary candidate
42%; in the incident cohort (79 events),
27% and 29%; in country-years with both
outcomes (78 events), 42% and
36%. Treating the few missing outcomes as all interruptions or all
delivered did not change the results (Table 4).

**Exploratory models proposed after the locked test.** Because most variation is
between country-years, we then tried three further approaches designed around that
structure: a logistic model on country-year means and within-country deviations of
the predictors, a two-level ranking (countries by prior-year rate, then IUs by the
rule), and the rule with an added term for fewer cumulative rounds. These were
designed after the locked-test results were known, so their held-out figures are not
an independent test. None of them met the improvement criterion. Differences
from the rule in share captured at 20% capacity were, respectively:
-23.1 percentage points (95% CI -46.1 to +13.3); -11.5 percentage points (95% CI -36.0 to +12.5); and +3.1 percentage points (95% CI -2.9 to +6.8) (Table X).

## Discussion

### Principal findings

Three findings stand on the descriptive evidence. First, missed LF rounds in African
programmes have been common and large in scale: in the worst year the affected IUs
held 51% of the cohort's population requiring treatment, and the
2025 figure was 2.4 times the 2024 figure. Second, they are
predominantly country-level events: 40% of interruptions occurred when
every eligible IU in a country missed the round, and 61% of the variation
in the outcome lies between country-years. Third,
interruptions are usually temporary: most IUs resume within one to three years, while
a minority of IUs account for most repeat interruptions.

The fourth finding is negative. Neither logistic regression nor gradient boosting
identified IUs at risk better than a fixed rule based on three years of treatment
history. The result held on the locked test, in the 2025 stress year, in countries
left out of training, across sensitivity cohorts, and for three further models
designed after the fact. With the two-year lag that applies to public data, no
approach performed better than chance.

### Interpretation

These findings fit together. If a round is missed because a country's medicines did
not arrive or its funding was interrupted, every IU in that country misses together,
and nothing in an IU's own history distinguishes it. Country-level failure in one
year was itself only weakly related to failure the year before, so country history
does not solve the problem either. The information that would anticipate such events
is funding status, medicine supply and campaign planning, which are known nationally
and to partners before the year begins. ESPEN's Implementation Unit Planner already
displays funding status by IU for planned activities; it was not used here because
historical versions are not public.

The practical implication is that district risk scores built from treatment history
are unlikely to repay the effort of maintaining them. A rule that any programme can
apply by hand does as well, and its main use is within countries that are delivering
but not everywhere. Decision support for avoiding missed rounds should be built at
national level on forward-looking planning data, and the case for publishing that
information alongside treatment data is strengthened by these results.

### Comparison with other studies

Fuller and colleagues showed that context is associated with the coverage achieved by
delivered rounds [1]. Our results concern a different outcome, whether a round happens
at all, and suggest that this is governed at a higher level than the district. The two
conclusions are complementary. Modelling work has estimated the epidemiological cost
of missed rounds [3]; our counts of population affected and of time to resumption
provide empirical inputs for such models.

### Strengths

The study uses only public data, with scripted acquisition and checksums. The outcome
was audited before any model was fitted. The protocol, including the treatment of
2025, was fixed in advance; the test was opened once; every change is logged; and
tests show that predictors cannot read later records. Uncertainty respects the
clustering of events within countries.

### Limitations

The outcome is a reported status after final correction, not independent evidence of
non-delivery, and it has not yet been reviewed by programme experts. Before 2021 ESPEN
had no status for a pending impact assessment, so some legitimate pauses remain among
the interruptions; the population figures for all active programmes are upper bounds
for that reason. Effective rounds are observed only from 2014. The records are the
current corrected values rather than those known at each decision date, so the
analysis is a retrospective reconstruction. Independent information is limited: the
locked test rests on 14 country-years with events, and intervals are
wide, so the absence of an improvement is not proof that none exists. Changes of IU
boundaries were not reconciled. Context was limited to conflict and population
density; rainfall and travel time were not tested. Calibration could not be
established. The literature search did not cover all indexes.

### Conclusions

Across Africa, missed LF treatment rounds have been frequent, have affected very large
populations in shock years, are mostly country-wide, and are usually followed by
resumption. Public programme data do not support district-level prediction of missed
rounds beyond a simple history rule. Efforts to anticipate and prevent missed rounds
should focus on country-level funding, supply and planning signals.

## Declarations

- **Data and code availability.** See `manuscript/data_code_availability.md`.
- **Ethics.** Aggregate programme data about administrative units; no individual data.
  **[to do: confirm whether a formal exemption is required]**
- **Funding, competing interests, author contributions, acknowledgements.** **[to do]**
- **Reporting checklist.** `manuscript/tripod_ai_checklist.md` **[to do: complete the
  official TRIPOD+AI form]**

## Figures and tables

Captions, alternative text and source files are in `manuscript/figures_and_tables.md`.
Suggested main set: Fig 2 (cohort flow), Fig 13 (population affected), Fig 4
(country-year heat map), Fig 15 (recovery), Fig 6 (model comparison), Fig 9 (capture
curve); Table 1, Table 3 and Table 5. The rest are supporting information.

## References

Entries 1, 2, 4, 5 and 6 were checked against Crossref or the publisher's page. Entry
3 was checked in Crossref by DOI only. **[to do: add WHO guidance on effective rounds
and stopping MDA, a source for the 2025 funding suspension, WHO guidance on NTD
activities during COVID-19, and the ESPEN data citation in the journal's format]**

1. Fuller BB, Harris V, Parker C, et al. Contextual determinants of mass drug
   administration performance: modelling fourteen years of lymphatic filariasis
   treatments in West Africa. PLoS Negl Trop Dis. 2023;17(2):e0011146.
   https://doi.org/10.1371/journal.pntd.0011146
2. Ng CW, Maddren R, Anderson RM. Challenges in assessing the impact of infection and
   disease control interventions over the past decade based on the Expanded Special
   Project for the Elimination of Neglected Tropical Diseases (ESPEN) database. Trans
   R Soc Trop Med Hyg. 2025;119(7):767-770. https://doi.org/10.1093/trstmh/traf005
3. Borlase A, et al. Evaluating and mitigating the potential indirect effect of
   COVID-19 on control programmes for seven neglected tropical diseases: a modelling
   study. Lancet Glob Health. 2022. https://doi.org/10.1016/S2214-109X(22)00360-6
   **[to do: complete author list, volume and pages]**
4. Davies S, Pettersson T, Öberg M. Organized violence 1989-2025, and violent
   political protests. J Peace Res. 2026. https://doi.org/10.1093/jopres/xjag046
5. Sundberg R, Melander E. Introducing the UCDP Georeferenced Event Dataset. J Peace
   Res. 2013;50(4). **[to do: pages]**
6. Collins GS, Moons KGM, Dhiman P, et al. TRIPOD+AI statement: updated guidance for
   reporting clinical prediction models that use regression or machine learning
   methods. BMJ. 2024;385:e078378. https://doi.org/10.1136/bmj-2023-078378
