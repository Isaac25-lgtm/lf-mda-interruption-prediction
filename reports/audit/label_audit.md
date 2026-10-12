# Label audit and feasibility gate

Generated 2026-10-12T15:01:08Z from the raw ESPEN LF IU-level extracts (protocol v1.1). All numbers are computed by `python -m lf_mda.cli audit`; none are typed by hand.

## Gate decision: `GO_ON_PROXY_LABEL`

Expert verification of the label: **PENDING - cannot be satisfied by code**.

| check | passed | evidence |
|---|---|---|
| G1 status agrees with treatment fields | True | 0.0218% of delivered/non-delivery rows are contradictory (limit 1%) |
| G2 non-reporting is separable from non-delivery | True | 1512 'Not reported' rows held as missing labels; none counted as events |
| G3 legitimate stops are limited in the primary cohort | True | 15.9% of primary-cohort events (to 2022) were followed by impact assessment or surveillance rather than resumed MDA (limit 20%); broad-cohort exclusions: 43.0% |
| G4 enough events in development and locked test | True | development 1638 events; locked test 130 events from 11 countries |
| G5 within-country variation supports IU-level ranking | True | 1104 events lie in country-years with both outcomes; 38.6% of outcome variance is within country-year |

**Independent information: `LIMITED`.** Locked test has 130 events in 705 iu-years, but they come from 14 country-years; after the country-year design effect this is about 13 effective events (target 100). Modelling therefore proceeds with deliberately small models and country-clustered uncertainty, and claims of model superiority must survive that uncertainty.

Thresholds were set by the code author after profiling the data. They are judgement calls recorded for transparency, not external standards.

`GO_ON_PROXY_LABEL` means the administrative status is coherent enough to model as a transparent proxy. It does not mean the label is validated: no programme officer has yet reviewed the sample in `expert_review_sample.csv`, and no medicine-request (JRSM) data were available to confirm that a round was formally planned.

## 1. Source data

- 65,454 IU-year rows, 48 country files, 6,236 distinct IUs, years 2014-2025.
- The header differs between countries; three columns are optional:

| optional columns present | countries |
|---|---|
|  | DZ, LR, LS |
| admin2 | AO, BF, BI, BJ, BW, CF, CG, CI, CV, ER, GA, GN, GQ, GW, KM, ML, MR, MU, MW, NA, NG, RW, SC, SL, SN, SS, ST, SZ, TG, TZ, UG, ZA, ZM, ZW, ZZ |
| admin2,admin3 | CD, ET, KE, MG |
| admin2,altAdmin2 | CM, GH, GM, MZ, NE, TD |

- The dictionary lists `JRF_submitted`, `PopNoTx` and `Alt_ADMIN2`; the extract has no `JRF_submitted` or `PopNoTx` column. Non-reporting is identified from the status value `Not reported` instead.
- No numeric field had blank or unparseable values except `endemicityId` (blank for the 2025 status `Endemic (under targeted treatment)`).

### Status values actually present

| endemicity_raw | endemicity_id | status_code | rows | countries | first_year | last_year |
|---|---|---|---|---|---|---|
| Endemic (MDA not delivered) | 1.000 | ND | 5908 | 32 | 2014 | 2025 |
| Endemic (pending IA) | 33.000 | IA | 942 | 15 | 2021 | 2025 |
| Endemic (under MDA) | 2.000 | MDA | 12449 | 32 | 2014 | 2025 |
| Endemic (under post-intervention surveillance) | 3.000 | PIS | 9356 | 27 | 2014 | 2025 |
| Endemic (under targeted treatment) |  | TT | 8 | 2 | 2025 | 2025 |
| Endemicity unknown | 99.000 | UNK | 148 | 5 | 2014 | 2025 |
| Non-endemic | 0.000 | NE | 35131 | 42 | 2014 | 2025 |
| Not reported | 999.000 | NR | 1512 | 23 | 2014 | 2025 |

### Coverage fields (delivered rows)

| delivered_rows | cov_over_100 | epi_cov_over_100 | max_cov | max_epi_cov | pop_treat_gt_pop_tot | pop_req_gt_pop_tot | cov_looks_like_fraction | countries_on_fraction_scale | lowest_country_median_cov |
|---|---|---|---|---|---|---|---|---|---|
| 12449 | 2175 | 494 | 887.43 | 887.43 | 494 | 11 | 1 | 0 | 55.65 |

Coverage scale was checked per country file (`coverage_scale_by_country.csv`): 0 countries have a median at or below 1.5, so every file reports percentages, not fractions (lowest country median 55.6%). Values above 100% exist and are kept as reported.

## 2. Cohort flow

| step | n |
|---|---|
| IU-year cells in grid, 2014-2025 | 74832 |
| ... of which a row exists in the extract | 65454 |
| Target years 2016-2025 (cells) | 62360 |
| Requiring MDA at t-1 (under MDA or MDA not delivered) | 15819 |
|   excluded: no delivery in t-1 or t-2 (never started / long lapsed) | 2858 |
| Broad cohort: delivered MDA in t-1 or t-2 | 12961 |
|   excluded: >=5 observed effective rounds at t-1 (due for impact assessment) | 3503 |
| Primary cohort (expected-round cohort) | 9458 |
|   outcome year class: delivered (outcome) | 6956 |
|   outcome year class: reported_interruption (outcome) | 1839 |
|   outcome year class: surveillance_or_stopped (excluded, counted) | 465 |
|   outcome year class: legitimate_pause_IA (excluded, counted) | 76 |
|   outcome year class: missing_JRF (excluded, counted) | 71 |
|   outcome year class: missing_iu_year (excluded, counted) | 32 |
|   outcome year class: contradictory (excluded, counted) | 19 |
| Primary analysis set (binary outcome available) | 8795 |
|   reported interruptions (events) | 1839 |

## 3. Events by analysis window and cohort

| cohort | window | n | events | prevalence | distinct_ius | countries | event_countries | event_country_years | event_ius |
|---|---|---|---|---|---|---|---|---|---|
| primary | development | 7857 | 1638 | 0.208 | 2051 | 32 | 30 | 75 | 1021 |
| primary | locked_test | 705 | 130 | 0.184 | 450 | 20 | 11 | 14 | 114 |
| primary | shock_stress_2025 | 233 | 71 | 0.305 | 233 | 14 | 8 | 8 | 71 |
| broad | development | 9559 | 2413 | 0.252 | 2071 | 32 | 30 | 79 | 1535 |
| broad | locked_test | 1363 | 197 | 0.145 | 883 | 24 | 16 | 21 | 178 |
| broad | shock_stress_2025 | 504 | 149 | 0.296 | 504 | 17 | 10 | 10 | 149 |
| strict | development | 3166 | 894 | 0.282 | 1233 | 28 | 18 | 51 | 547 |
| strict | locked_test | 481 | 94 | 0.195 | 295 | 14 | 9 | 11 | 79 |
| strict | shock_stress_2025 | 183 | 56 | 0.306 | 183 | 12 | 6 | 6 | 56 |
| incident | development | 6705 | 1255 | 0.187 | 2049 | 32 | 30 | 62 | 1018 |
| incident | locked_test | 596 | 79 | 0.133 | 412 | 19 | 8 | 11 | 79 |
| incident | shock_stress_2025 | 206 | 51 | 0.248 | 206 | 13 | 7 | 7 | 51 |

## 4. Legitimate stops versus interruptions (hindsight check, events to 2022)

For each event, the first status after the run of non-delivery years. This uses later years, so it is an audit of the label only; it is never a model input.

| cohort | events_to_2022 | resumed_mda | resumed_mda_share | moved_to_IA_or_surveillance | moved_to_IA_or_surveillance_share | censored | censored_share | other_or_missing | other_or_missing_share |
|---|---|---|---|---|---|---|---|---|---|
| primary | 1638 | 1284 | 0.784 | 260 | 0.159 | 36 | 0.022 | 58 | 0.035 |
| broad | 2413 | 1717 | 0.712 | 593 | 0.246 | 45 | 0.019 | 58 | 0.024 |
| strict | 894 | 718 | 0.803 | 112 | 0.125 | 18 | 0.020 | 46 | 0.051 |
| incident | 1255 | 1018 | 0.811 | 164 | 0.131 | 19 | 0.015 | 54 | 0.043 |
| broad_excluded_by_rounds | 775 | 433 | 0.559 | 333 | 0.430 | 9 | 0.012 | 0 | 0.000 |

Reading: in the primary cohort most non-delivery events were followed by resumed MDA. Among IUs excluded for having five or more observed effective rounds, a much larger share moved to impact assessment or surveillance, which is why they are excluded. `Endemic (pending IA)` exists only from 2021, so before 2021 a pause for assessment cannot be separated from non-delivery by status alone. A later move to surveillance does not prove the non-delivery was legitimate, so the share is an upper bound on contamination.

## 5. Are interruptions country-year events?

| band | country_years | iu_years | events | share_of_events |
|---|---|---|---|---|
| 0% | 123 | 3099 | 0 | 0.000 |
| >0-10% | 16 | 2112 | 97 | 0.053 |
| >10-50% | 34 | 2110 | 461 | 0.251 |
| >50-90% | 9 | 694 | 503 | 0.274 |
| >90-<100% | 2 | 45 | 43 | 0.023 |
| 100% | 36 | 735 | 735 | 0.400 |

- 97 of 220 country-years have at least one event; 61 have both outcomes.
- 735 of 1839 events (40%) are in country-years where every eligible IU missed the round; 1281 (70%) are in country-years where more than half did.
- 1104 events are in country-years with both outcomes; only these can inform ranking of IUs within a country.

### Variance partition and effective sample size

| subset | n | prevalence | between_country | between_country_year | within_country_year | icc_country_year | design_effect_country_year | n_effective | events_effective |
|---|---|---|---|---|---|---|---|---|---|
| all target years | 8795 | 0.209 | 0.165 | 0.614 | 0.386 | 0.609 | 24.739 | 355.513 | 74.336 |
| development | 7857 | 0.208 | 0.207 | 0.623 | 0.377 | 0.621 | 28.730 | 273.481 | 57.014 |
| locked_test | 705 | 0.184 | 0.311 | 0.462 | 0.538 | 0.451 | 9.899 | 71.220 | 13.133 |
| shock_stress_2025 | 233 | 0.305 | 0.682 | 0.682 | 0.318 | 0.686 | 11.730 | 19.863 | 6.053 |

`n_effective` applies a design effect for clustering by country-year. It shows that the independent information is far smaller than the IU-year row count.

## 6. Countries contributing to the primary cohort

| iso2 | country | iu_years | events | distinct_ius | first_year | last_year | event_years | share_of_all_events |
|---|---|---|---|---|---|---|---|---|
| NG | Nigeria | 2864 | 386 | 551 | 2016 | 2025 | 10 | 0.210 |
| ZM | Zambia | 504 | 271 | 85 | 2016 | 2023 | 7 | 0.147 |
| GW | Guinea-Bissau | 570 | 198 | 109 | 2016 | 2025 | 8 | 0.108 |
| MG | Madagascar | 390 | 183 | 86 | 2016 | 2025 | 5 | 0.100 |
| CD | Democratic Republic of the Congo | 1107 | 149 | 245 | 2016 | 2025 | 2 | 0.081 |
| AO | Angola | 122 | 98 | 37 | 2017 | 2025 | 4 | 0.053 |
| ET | Ethiopia | 358 | 97 | 98 | 2016 | 2025 | 9 | 0.053 |
| MZ | Mozambique | 408 | 71 | 114 | 2017 | 2024 | 3 | 0.039 |
| CF | Central African Republic | 124 | 62 | 32 | 2017 | 2025 | 7 | 0.034 |
| SS | South Sudan | 196 | 49 | 50 | 2018 | 2025 | 5 | 0.027 |
| GQ | Equatorial Guinea | 60 | 45 | 15 | 2022 | 2025 | 3 | 0.024 |
| ZW | Zimbabwe | 85 | 39 | 39 | 2017 | 2025 | 1 | 0.021 |
| TD | Chad | 165 | 32 | 35 | 2017 | 2025 | 4 | 0.017 |
| GN | Guinea | 143 | 27 | 24 | 2016 | 2024 | 4 | 0.015 |
| ZZ | Tanzania (Zanzibar) | 58 | 18 | 11 | 2017 | 2024 | 2 | 0.010 |
| GH | Ghana | 80 | 18 | 24 | 2016 | 2025 | 2 | 0.010 |
| KE | Kenya | 117 | 17 | 23 | 2017 | 2022 | 2 | 0.009 |
| KM | Comoros | 48 | 17 | 17 | 2018 | 2021 | 1 | 0.009 |
| NE | Niger | 51 | 12 | 18 | 2016 | 2019 | 1 | 0.007 |
| SN | Senegal | 249 | 11 | 50 | 2016 | 2023 | 3 | 0.006 |
| LR | Liberia | 86 | 11 | 13 | 2016 | 2025 | 1 | 0.006 |
| UG | Uganda | 23 | 10 | 15 | 2016 | 2019 | 1 | 0.005 |
| TZ | Tanzania (Mainland) | 94 | 7 | 42 | 2016 | 2023 | 2 | 0.004 |
| SL | Sierra Leone | 32 | 3 | 14 | 2016 | 2019 | 2 | 0.002 |
| CM | Cameroon | 246 | 2 | 135 | 2016 | 2022 | 2 | 0.001 |
| CI | Cote d'Ivoire | 272 | 2 | 86 | 2016 | 2021 | 2 | 0.001 |
| BJ | Benin | 70 | 1 | 25 | 2016 | 2020 | 1 | 0.001 |
| CG | Congo | 100 | 1 | 14 | 2016 | 2025 | 1 | 0.001 |
| ER | Eritrea | 11 | 1 | 2 | 2017 | 2023 | 1 | 0.001 |
| BF | Burkina Faso | 70 | 1 | 31 | 2016 | 2022 | 1 | 0.001 |
| ML | Mali | 78 | 0 | 53 | 2016 | 2018 | 0 | 0.000 |
| ST | Sao Tome and Principe | 14 | 0 | 7 | 2019 | 2020 | 0 | 0.000 |

## 7. Reporting diagnostics

- Whole-country `Not reported` years: 30 (CF 2015, GA 2014, GA 2015, GA 2017, GA 2019, GA 2023, GH 2020, GN 2014, GQ 2014, GQ 2015, GQ 2016, GQ 2017, KM 2014, KM 2015, KM 2022, KM 2023, KM 2024, LR 2014, MW 2014, MZ 2015, SL 2014, SS 2015, ST 2014, ST 2015, ST 2017, ZM 2014, ZW 2019, ZW 2021, ZZ 2014, ZZ 2019).
- Country-years with delivery or non-delivery rows whose populations are identical to the previous year (possible carried-forward records): CG 2015, CM 2016, ER 2016, ET 2018, GH 2016, GN 2016, GQ 2021, NE 2024, TD 2016, TD 2020, ZM 2016, ZW 2017.
- 2025 country-years with delivery or non-delivery rows that are absent from the ESPEN release log: CD, ET, GH, MG, TD.
- Contradictory rows quarantined: 187 (see `contradictions.csv`).

## 8. Open threats

1. The label is a WHO-reported status after final correction, not independent proof of non-delivery, and no planning data confirm that a round was scheduled.
2. Effective rounds are observed only from 2014; IUs with long earlier histories may still be in the primary cohort (the `strict` cohort tests this).
3. Records are current corrected values, not what was known at each decision date.
4. Most events arise from country-wide failures, so IU-level row counts overstate the independent evidence.
5. IU definitions change over time in many countries (`iu_lineage_counts.csv`); IUs without a row at t-1 never enter the cohort.
