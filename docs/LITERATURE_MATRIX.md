# Literature matrix

Status of each source on 2026-10-12. "DOI verified" means the DOI resolved in Crossref
to the stated authors, title and journal. "Read" says how much of the paper was
actually read for this project; nothing is described beyond that.

| Source | DOI verified | Read | What it did | What it leaves open |
|---|---|---|---|---|
| Fuller BB, Harris V, Parker C, et al. 2023. Contextual determinants of mass drug administration performance: modelling fourteen years of lymphatic filariasis treatments in West Africa. PLoS Negl Trop Dis 17(2):e0011146 | Yes | Article page | Hierarchical linear model of epidemiological coverage for 3,880 **delivered** MDAs in 647 districts of 10 West African countries, 2007-2020. Predictors: rainfall, temperature, violence (ACLED), COVID-19, Ebola, isolation, population density, Ramadan, prior rounds, treatment hiatus, focal MDA. Data from the USAID NTD database, not public. No out-of-sample or future-year validation. | Rounds that were not delivered; prediction before the year; public, reproducible data; any comparison with a simple history rule |
| Ng CW, Maddren R, Anderson RM. 2025. Challenges in assessing the impact of infection and disease control interventions over the past decade based on the ESPEN database. Trans R Soc Trop Med Hyg 119(7):767-770 | Yes | Article page | Documents ESPEN data-quality problems using soil-transmitted helminthiasis in Kenya, Ethiopia, Nigeria and Senegal: uncertain denominators, incomplete numerators, duplicate reporting, coverage above 100% (59% of Senegal data points). | LF records were not examined. This project profiles LF separately (see below) |
| Burgert-Brucker CR, Zoerhoff KL, Headland M, et al. 2020. Risk factors associated with failing pre-transmission assessment surveys (pre-TAS) in lymphatic filariasis elimination programs. PLoS Negl Trop Dis 14(6):e0008301 | Yes | Title and abstract level only | Risk factors for failing pre-TAS | Different outcome (survey failure, not delivery) |
| Maroto-Camino C, Hernandez-Pastor P, Awaca N, et al. 2019. Improved assessment of mass drug administration and health district management performance to eliminate lymphatic filariasis. PLoS Negl Trop Dis 13(7):e0007337 | Yes | Title only | Assessment of MDA and district management performance | Not a prediction of delivery |
| Galiwango, Kyomukama, Babirye, et al. 2026. Potential of machine learning for prevention and control of neglected tropical diseases: a scoping review. Commun Med 6(1) | Yes | Title only (publisher page required sign-in) | Scoping review of ML for NTDs | **Not read.** Whether it covers programme-delivery prediction is unverified |
| WHO. Global programme to eliminate lymphatic filariasis: progress report, 2025. Wkly Epidemiol Rec 101(39) | Not checked | Not read | Cited in the concept for 571 IUs requiring MDA and 386 implementing in the African Region in 2025 | **Figures not verified by this project.** They are not used in any analysis |
| ESPEN Implementation Unit Planner | n/a | Tool description page | IU-level funding status for planned MDA | See search log: a stronger forward-looking signal that this study does not use |

## Corrections to the concept document

- Fuller et al. used **ACLED** for violence, not UCDP. This project uses UCDP because it
  is openly downloadable without registration.
- Fuller et al. already examined "treatment hiatus" as a predictor of coverage, so the
  idea that history matters is not new; the outcome and the predictive framing are.
- Maroto-Camino et al.'s title concerns assessment of MDA and district management
  performance; the concept's description "independent verification of MDA coverage"
  is a paraphrase that was not checked against the full text.

## How the ESPEN LF records compare with Ng et al.'s STH findings

Checked on the downloaded LF extract (`reports/audit/coverage_qc.csv`):

- Programme coverage above 100% occurs in 2,175 of 12,449 delivered LF rows (17%), and
  epidemiological coverage above 100% in 494 (4%). The maximum is 887%.
- People treated exceed total population in 494 delivered rows.
- Coverage is stored as a percentage in every country file with delivered rounds
  (`reports/audit/coverage_scale_by_country.csv`).
- The status field and the treatment fields agree in all but 0.02% of delivered or
  non-delivery rows.

So the denominator problems Ng et al. describe for STH are also visible in LF
coverage values. Coverage is therefore used here only as a clipped predictor and never
as the outcome.

## Contribution this study can actually claim

| Dimension | Closest prior work | This study, as executed |
|---|---|---|
| Outcome | Coverage of delivered campaigns (Fuller) | Reported non-delivery among active programmes, with an audited proxy label |
| Framing | Retrospective association | Prediction at a decision date, with time-forward and country-held-out evaluation |
| Comparator | None | Fixed history rule and country prior rate, then logistic regression and CatBoost |
| Data | Restricted programme database | Public ESPEN download, scripted and checksummed |
| Finding | Context is associated with coverage | See README and `reports/` for what the data support |

The contribution is methodological and descriptive. It is conditional on the label
being accepted as a proxy and on the novelty search above.
