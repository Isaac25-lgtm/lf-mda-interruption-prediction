# Label decisions

The outcome is an **administrative proxy**: the WHO ESPEN endemicity status of an
implementation unit (IU) in a given year, as reported through the Joint Reporting Form
"after final correction". It is not independent proof that a round was missed, and no
medicine-request (JRSM) data were available to confirm that a round was planned.
**No programme officer has reviewed these labels yet.**

Numbers below come from `reports/audit/` and are reproduced by `lf-mda audit`.

## Status values and their classes

The reviewed mapping is `config/status_map_reviewed.csv`. The reviewer so far is the code
author, not a programme expert.

| ESPEN status | Class | Role |
|---|---|---|
| Endemic (under MDA) | delivered | candidate negative |
| Endemic (MDA not delivered) | non_delivery | candidate positive if the IU is in the cohort |
| Endemic (pending IA) | legitimate_pause_IA | excluded, counted |
| Endemic (under post-intervention surveillance) | surveillance_or_stopped | excluded, counted |
| Non-endemic | not_endemic | excluded, counted |
| Not reported | missing_JRF | missing label, never an interruption |
| Endemicity unknown | unknown | excluded, counted |
| Endemic (under targeted treatment) | unknown | new in 2025, 8 rows, undocumented |

An IU-year with no row in the extract is `missing_iu_year`, also a missing label.

## Precedence

1. A status not in the map becomes `unknown`.
2. A status contradicted by the treatment fields becomes `contradictory` and is
   quarantined. Examples: "MDA not delivered" with people treated; "under MDA" with
   nobody treated; a no-MDA status with treatment recorded.
3. Otherwise the mapped class applies.

In the real data the status and the treatment fields agree almost perfectly: every
"under MDA" row has `popTreat > 0` and `mda = 1`, and 0.02% of delivered or
non-delivery rows are contradictory. This means the status is essentially a
restatement of the treatment fields, which makes it coherent but not independently
verified.

## Who is in the cohort (decided at 31 December of year t-1)

An IU-year t is eligible when, using only records dated t-1 or earlier:

- the IU required MDA at t-1 (status "under MDA" or "MDA not delivered"); and
- it delivered MDA in t-1 or t-2 (an active programme); and
- it had fewer than 5 observed effective rounds at t-1 (`epiEffMdaN <= 4`).

Outcome-year fields (`popReq(t)`, status at t, treatment at t) classify the outcome
only. Tests prove that changing outcome-year values does not change eligibility.

## Why the effective-round restriction exists

WHO guidance is that an IU with at least five effective rounds moves to pre-TAS and
TAS rather than another round. `Endemic (pending IA)` exists as a status only from
2021, so before 2021 a pause for assessment looks the same as a missed round.

Hindsight check (events up to 2022; what the IU did after the run of non-delivery years):

| Group | Resumed MDA | Moved to assessment or surveillance |
|---|---|---|
| Primary cohort (fewer than 5 effective rounds) | 78% | 16% |
| Excluded (5 or more effective rounds) | 56% | 43% |

This check uses later years. It is an audit of the label and is never a model input.
A later move to surveillance does not prove the earlier non-delivery was legitimate
(an IU can miss a round and still pass its assessment), so 16% is an upper bound on
contamination, not an error rate.

## Known weaknesses

- Effective rounds are observed only from 2014. An IU with many earlier rounds can
  still enter the primary cohort. The `strict` cohort adds rounds delivered before 2014
  and is reported as a sensitivity analysis.
- "Delivered in t-1 or t-2" is a proxy for "another round was expected". It is recorded
  as `expected_round_evidence = proxy`; nothing here is "verified planned".
- All values are the current corrected values, not what was known at each decision date.
- 2025 rows for countries missing from the release log are of uncertain status.

## What is needed to call the label validated

1. Review of `reports/audit/expert_review_sample.csv` by NTD programme officers with
   knowledge of the countries concerned. The sample has five strata: positives,
   negatives, positives excluded by the round restriction, pending-IA cases and
   contradictory rows. Reviewing positives alone estimates only the positive
   predictive value.
2. Ideally, historical JRSM planning data to confirm that a round was requested. This
   is not public; obtaining it would need a request to ESPEN, which the researcher has
   chosen not to pursue for this open-data study.

Until then, results must be described as predicting a reported status.
