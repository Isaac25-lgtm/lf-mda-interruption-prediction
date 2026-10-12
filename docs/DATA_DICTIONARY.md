# Data dictionary

## Raw ESPEN LF IU-level extract (as served on 2026-10-12)

Definitions are from the official dictionary
(https://espen.afro.who.int/sites/default/files/content/document/Lymphatic_Filariasis_EN_FR_PT.pdf).
Column names in the download are camelCase and differ from the dictionary's names.
"Observed" notes come from this project's audit.

| Download column | Dictionary name | Definition (dictionary) | Observed |
|---|---|---|---|
| `admin0`, `admin0Iso2`, `admin0Iso3` | ADMIN0, ADMIN0ISO2/3 | Country name and ISO codes | `ZZ` is ESPEN's code for Tanzania (Zanzibar) |
| `admin1`, `admin1Id` | ADMIN1, ADMIN1ID | First administrative level | |
| `admin2`, `admin2Id` | ADMIN2, ADMIN2ID | Second administrative level | `admin2` absent for DZ, LR, LS |
| `admin3`, `admin3Id` | ADMIN3, ADMIN3ID | Third administrative level | `admin3` present only for CD, ET, KE, MG |
| `altAdmin2` | Alt_ADMIN2 | Alternative ADMIN2 name | Present only for CM, GH, GM, MZ, NE, TD |
| `iusAdm` | IUs_ADM | Administrative level at which IUs are defined | ADM1, ADM2 or ADM3 |
| `iusName`, `iuId`, `iuCode` | IUs_NAME, IU_ID, IU_CODE | IU name, ESPEN IU ID, alphanumeric code | `iuId` is unique across countries in this extract; the project still keys on country + `iuId` |
| `year` | Year | Year | 2014-2025 |
| `popTot`, `popPreSAC`, `popSAC`, `popAdult` | PopTot, ... | Reported or estimated populations | Some country-years repeat the previous year's values exactly |
| `endemicity` | Endemicity | "Reported LF Endemicity status through JRF after final correction" | Eight distinct values; see `docs/LABEL_DECISIONS.md` |
| `endemicityId` | Endemicity_ID | ID of the endemicity category | 0, 1, 2, 3, 33, 99, 999; blank for "under targeted treatment" |
| `popReq` | PopReq | Population requiring treatment (JRF) | Equal to `popTot` in almost all MDA-requiring rows |
| `popTrg` | PopTrg | Population targeted | |
| `popTreat` | PopTreat | Population treated | Exceeds `popTot` in 494 delivered rows |
| `cov` | Cov | Programme coverage = treated / targeted | Percent; above 100 in 17% of delivered rows |
| `epiCov` | EpiCov | Epidemiological coverage = treated / requiring | Percent; above 100 in 4% of delivered rows; maximum 887 |
| `mdaScheme` | MDA_scheme | Scheme giving the maximum coverage | ALB+IVM, ALB+DEC, ALBx2, IDA, Not delivered |
| `cumMda` | Cum_MDA | Cumulative MDA rounds since inception | `cumMda - mdaN` is constant within every IU |
| `mda`, `epiMda` | MDA, EpiMDA | MDA implemented (0/1), from programme / epidemiological coverage | Identical to each other in every row |
| `effMda`, `epiEffMda` | EffMDA, EpiEffMDA | Effective round (coverage at least 65%) | |
| `mdaN`, `epiMdaN` | MDA_n, EpiMDA_n | Cumulative rounds "since 2013" | In this extract the count starts in 2014: `mdaN` in 2014 equals `mda` in 2014 for every IU |
| `effMdaN`, `epiEffMdaN` | EffMDA_n, EpiEffMDA_n | Cumulative effective rounds "since 2013" | Starts in 2014, as above |
| (absent) | JRF_submitted | Whether the JRF was submitted | **Not in the download.** Non-reporting is identified by status `Not reported` |
| (absent) | PopNoTx | Population no longer requiring treatment | **Not in the download** |

## Derived panel (`data/processed/panel.parquet`)

One row per IU and year for every IU and every year 2014-2025, including years with no
record.

| Column | Meaning |
|---|---|
| `iu_key` | `<ISO2>-<iuId>`; the join key |
| `row_present`, `gap_type` | Whether the extract has a record; if not, whether the year is before the IU's first record, after its last, or an internal gap |
| `status_code`, `row_class` | Short status code and class after precedence rules |
| `contradiction` | Reason a record was quarantined, if any |
| `row_class_l1` to `_l3` | Class one to three years earlier (joined on IU and year) |
| `rounds_before_2014` | `cumMda - mdaN`; rounds delivered before the extract window |
| `eff_rounds_obs_l1`, `eff_rounds_ub_l1` | Effective rounds at t-1: observed since 2014, and observed plus all rounds before 2014 |
| `eligible_broad`, `eligible_primary`, `eligible_strict`, `eligible_incident` | Cohort flags (`config/protocol.yaml`) |
| `outcome_class`, `y` | Outcome class in year t; `y` is 1 for reported interruption, 0 for delivered, missing otherwise |
| `lifecycle_class` | Accounting class for every row, including `never_started` |
| `hs_next`, `hs_group` | What followed a non-delivery spell. Audit only: uses later years, never a predictor |
| `window`, `covid_stress_year` | Development, locked test or 2025 stress; COVID-19 flag |

## Predictors

See `config/features.yaml` (machine-checked) and `docs/PREDICTOR_AVAILABILITY.md`.
