# Predictor availability and the as-of contract

**Decision date:** 31 December of year t-1, for the round expected in year t. Whether
this matches real medicine-ordering and budget deadlines has not been confirmed with a
programme collaborator; it may need to move earlier.

## Two information scenarios

| | Scenario P | Scenario E |
|---|---|---|
| Who | The programme itself | An outside analyst using public ESPEN |
| Newest ESPEN record used for predictors | t-1 | t-2 |
| Newest outcome used for training | t-1 | t-2 |
| Honest name | Programme-information retrospective reconstruction | Approximate as-of evaluation with current corrected values |

Neither is a prospective validation. Both use today's corrected database, not the
values known at the time, because ESPEN does not publish historical snapshots.

Scenario E is evaluated on the same IU-years as scenario P. Cohort membership still
uses t-1 status, which an outside analyst would not have, so E measures the loss from
older predictors and labels, not a complete outside-analyst workflow.

## When ESPEN data became public

Transcribed on 2026-10-12 from https://espen.afro.who.int/maps-data/data-updates into
`config/source_release_calendar.csv`. The log covers only data years 2024 and 2025.

| Data year | First release | Last release in the log | Lag after year-end |
|---|---|---|---|
| 2024 | 25 August 2025 (27 countries) | 8 June 2026 (Ethiopia) | 8 to 17 months |
| 2025 | 9 June 2026 (16 countries) | 31 August 2026 (8 countries) | 5 to 8 months so far; 5 countries with 2025 rows not yet in the log |

So on 31 December of year t-1, year t-1 data were never public, and year t-2 data were
public for most but not all countries (DR Congo and Ethiopia 2024 data appeared after
31 December 2025). A uniform two-year lag is therefore slightly optimistic for the
slowest countries. Release dates before 2025 are not documented on the page, so the
same two-year rule is assumed for earlier years. This assumption is unverified.

## Predictors

The machine-readable manifest is `config/features.yaml`. A predictor is allowed only
if it is listed there with `min_lag_years >= 1` and `derived_from_outcome_year: false`;
the loader rejects anything else.

| Group | Predictors | Newest record used (P / E) |
|---|---|---|
| IU history | non-delivery last year and the year before; counts of delivered and missed rounds in three years; coverage, effectiveness and drug scheme of the last delivered round; cumulative rounds; observed effective rounds; population; years on record | t-1 / t-2 |
| Country and region history | share of the country's other requiring IUs that missed the last round, and the year before; number of IUs requiring MDA; share already under surveillance; share not reported; same-region non-delivery share | t-1 / t-2 |
| Context | conflict events and deaths inside the IU and in the country (UCDP); IU area and population density | conflict t-2 in both; density uses t-1 / t-2 population |
| Identity | country code (one ablation model only) | static |

Conflict uses year t-2 in both scenarios because UCDP GED for a calendar year is
published around June of the following year. Values are from GED 26.1, not from the
version that was current at each decision date.

IU boundaries are the 2024 provisional cartography and are treated as static. An IU
whose boundary changed has its 2024 centroid and area applied to all years. 9% of
primary-cohort IU-years have no geometry (all of Madagascar and Cameroon, parts of
Côte d'Ivoire, Niger and Ethiopia); their context predictors are missing.

## How leakage is prevented and tested

- Eligibility and every predictor are built by joining on (IU, year - lag). There is no
  positional shift over a panel with gaps.
- Imputation, scaling and encoding sit inside the fitted model object, so they are
  learned from training rows only.
- `tests/test_asof_leakage.py` scrambles every record dated after the information
  cutoff and asserts that no predictor changes; injects a deliberately leaky predictor
  and asserts it is caught; and shows that changing outcome-year values does not change
  eligibility.
- `tests/test_splits.py` asserts that training labels are always older than the
  evaluated year by at least the label lag, and that held-out countries never appear
  in training.

## Not used, and why

| Candidate | Reason |
|---|---|
| Outcome-year `popReq`, `popTrg`, `popTreat`, coverage, status | They are the outcome or are recorded with it |
| Cumulative round counters for year t | Include the outcome year |
| ESPEN co-endemicity fields (onchocerciasis, loiasis, WASH) | Available only as a 2024 snapshot from the map endpoint, so they would carry later information into earlier years |
| CHIRPS rainfall | Rainfall for year t is unknown at the decision date; no clear mechanism links a prior-year anomaly to next-year delivery |
| Travel-time raster | Large file and unverified link; not attempted |
| IU Planner funding status | Current plans only, no historical vintages; not confirmed to be openly downloadable |
