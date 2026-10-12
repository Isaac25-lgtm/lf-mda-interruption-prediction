# Literature search log

All searches below were run on **2026-10-12**. Counts are as returned on that date. The
raw PubMed and Europe PMC output is reproducible with the query strings shown.

## Verdict on novelty

No paper, preprint, repository or deployed tool was found that predicts non-delivery of
an expected LF MDA round at implementation-unit level and validates the prediction on
later years. The claim that this is new is therefore **defensible but not proven**:
several indexes were not searched (see "Not searched"). Do not write "first ever".

One deployed tool narrows the practical gap and must be discussed in any paper: the
ESPEN Implementation Unit Planner shows, per IU, whether funding for planned MDA is
secured. That is direct, forward-looking information about likely non-delivery, held
by programmes and partners, and it is probably a stronger signal than treatment
history. This study does not use it and cannot show that a history-based score adds
anything to it.

## Structured database searches

PubMed via NCBI E-utilities and Europe PMC via its REST API. Europe PMC searches full
text and includes preprints (medRxiv, bioRxiv), so its counts are much larger.

| # | Query | PubMed | Europe PMC |
|---|---|---|---|
| 1 | `("lymphatic filariasis") AND ("mass drug administration") AND (interrupt* OR "missed round*" OR "non-delivery" OR "not delivered") AND (predict* OR forecast* OR "machine learning")` | 18 | 718 |
| 2 | `("mass drug administration") AND ("machine learning" OR "gradient boosting" OR "random forest") AND (coverage OR delivery OR interruption) AND (programme OR program)` | 2 | 132 |
| 3 | `ESPEN AND ("lymphatic filariasis") AND (predict* OR "machine learning" OR forecast*)` | 3 | 77 |
| 4 | `("Expanded Special Project for Elimination of Neglected Tropical Diseases") AND (predict* OR model*) AND ("mass drug administration")` | 3 | 100 |
| 5 | `("lymphatic filariasis") AND ("mass drug administration") AND ("implementation unit*") AND (predict* OR "risk score" OR "prediction model")` | 0 | 82 |
| 6 | `("neglected tropical diseases") AND ("mass drug administration") AND (interruption OR disruption) AND (predict* OR "risk factors") AND (district OR "implementation unit")` | 3 | 352 |

### Screening of PubMed results (titles; top 15 by relevance for query 1, all for 2-6)

"Interrupt" in this literature almost always means interruption of *transmission*, not
of programme delivery. None of the records addresses the study question.

| Record | Topic | Same question? |
|---|---|---|
| Michael 2016, BMC Med, 10.1186/s12916-016-0557-y | Transmission dynamics and eradication | No |
| Shaw 2023, PLoS NTD, 10.1371/journal.pntd.0011347 | GEOFIL endgame strategy simulation | No |
| Stolk 2015, Adv Parasitol, 10.1016/bs.apar.2014.12.005 | Transmission modelling frameworks | No |
| Collyer 2020, PLoS NTD, 10.1371/journal.pntd.0008644 | Prevalence thresholds for elimination | No |
| Jambulingam 2016, Parasit Vectors, 10.1186/s13071-016-1768-y | Required duration of MDA, India | No |
| Borlase 2022, Lancet Glob Health, 10.1016/S2214-109X(22)00360-6 | Modelled effect of COVID-19 delays on seven NTDs | Related: consequence of interruption, not its prediction |
| Kabore 2021, AJTMH, 10.4269/ajtmh.21-0408 | Restarting NTD programmes after COVID-19, West Africa | Related context, descriptive |
| Talbot 2008; Cantey 2010 (two papers) | Individual compliance with MDA | No (individual, not programme) |
| Maddren 2023, PLoS NTD, 10.1371/journal.pntd.0010853 | Individual longitudinal compliance, review | No |
| Mhiche 2025, PLoS NTD, 10.1371/journal.pntd.0012219 | Onchocerciasis MDA coverage determinants, one district | Related: coverage, explanatory |
| Bogus 2016, AJTMH, 10.4269/ajtmh.15-0591 | Community attitudes to MDA after Ebola | No |
| Eneanya 2021, PLoS NTD, 10.1371/journal.pntd.0009091 | Geospatial onchocerciasis prevalence | No |
| Farah 2026, PLoS NTD, 10.1371/journal.pntd.0012639 | Effect of ending LF MDA on STH prevalence | No |
| Cano 2018, Parasit Vectors, 10.1186/s13071-018-2655-5 | Co-endemic filarial areas | No |
| Downs 2025, Health Aff Sch, 10.1093/haschl/qxaf136 | Changing NTD landscape and policy | Related context |
| Dixon 2026, Sci Data, 10.1038/s41597-026-06852-w | HISTONCHO onchocerciasis intervention histories dataset | Related data resource (different disease) |
| Kura 2023; Vinkeles Melchers 2020 | Onchocerciasis and loiasis projections | No |
| Drame 2016; Sabesan 2013; Aye 2018; Chong 2021; Owusu 2015 | Diagnostics, risk mapping, STH or transmission | No |

The Europe PMC result sets (77 to 718 records) were **not** screened record by record.
This is a limitation of the search.

## Web searches (general search engine, 2026-10-12)

| Query | Outcome |
|---|---|
| machine learning predict mass drug administration interruption / "missed rounds" lymphatic filariasis implementation unit ESPEN | No predictive study of programme non-delivery. Found baseline prevalence mapping with ML, and mechanistic models of the effect of missing a round. |
| ESPEN data predictive model MDA non-delivery / "treatment gap" / "missed MDA" forecasting programme performance | Found ESPEN's 2021-2030 PC forecasts, which project rounds still needed and **assume** forecast rounds are delivered at effective coverage. No model of non-delivery. |
| ESPEN API LF IU-level data documentation | No public API documentation or key requirement found. |

## Repository search (GitHub API, 2026-10-12)

| Query | Repositories |
|---|---|
| ESPEN lymphatic filariasis mass drug administration prediction | 0 |
| mass drug administration interruption prediction machine learning | 1 (this project's own repository) |
| lymphatic filariasis MDA coverage prediction model | 0 |

## Deployed tools checked

| Tool | What it does | Overlap |
|---|---|---|
| ESPEN Implementation Unit Planner | Shows IU-level funding status for planned MDA and surveys, from JRSM submissions validated by partners | High practical overlap for the decision; no predictive model; not used here |
| ESPEN 2021-2030 PC forecasts | Projects remaining rounds per IU from endemicity, effective rounds and surveys | Assumes delivery; does not model failure |

## Not searched

Scopus and Web of Science (no access), Google Scholar (no reproducible query
interface), medRxiv directly (covered only through Europe PMC), CRAN, PyPI, conference
abstracts and thesis repositories. These must be searched before any novelty claim is
made in a manuscript. If a substantially identical study is found, raise
`NOVELTY_GATE_FAILED`.
