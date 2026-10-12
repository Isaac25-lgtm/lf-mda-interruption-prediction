# Research ledger

Every factual claim the project makes, where it comes from, and how far it has been
checked. A claim not listed here should not appear in a manuscript.

Status: **Verified** = checked against the primary source or computed by this
repository's code on 2026-10-12. **Unverified** = taken from the concept document or
from memory and not checked.

## Claims about the data (computed here)

| Claim | Source file | Status |
|---|---|---|
| ESPEN serves LF IU-level data for 48 countries, 2014-2025, without login or key | `data/manifests/espen_sources.csv` | Verified |
| Number of IU-year records, IUs and countries | `reports/audit/gate_decision.json` | Verified |
| Eight distinct status values; "pending IA" first appears in 2021 | `reports/audit/status_values.csv` | Verified |
| The download has no `JRF_submitted` column | `reports/audit/label_audit.md` | Verified |
| Status and treatment fields disagree in 0.02% of delivered or non-delivery rows | `reports/audit/gate_decision.json` | Verified |
| Cohort size, events, countries per window | `reports/audit/events_by_window.csv` | Verified |
| Share of events in whole-country failures; variance partition | `reports/audit/clustering_bands.csv`, `variance_partition.csv` | Verified |
| What followed non-delivery, by cohort | `reports/audit/hindsight_adjudication.csv` | Verified |
| Coverage above 100%, treated above population | `reports/audit/coverage_qc.csv` | Verified |
| ESPEN release dates for 2024 and 2025 data | `config/source_release_calendar.csv` (transcribed from the ESPEN updates page) | Verified |
| All model performance figures | `reports/evaluation/`, `reports/tables/` | Verified (computed); conditional on the proxy label |

## Claims about the literature

| Claim | Source | Status |
|---|---|---|
| Fuller et al. 2023 analysed 3,880 delivered MDAs in 647 districts of 10 West African countries, 2007-2020, with a hierarchical linear model; data not public; no out-of-sample validation | Article page, DOI 10.1371/journal.pntd.0011146 | Verified from the article page (not from a full careful read of the PDF) |
| Fuller et al. used ACLED for violence | Same | Verified |
| Ng et al. 2025 documents ESPEN data-quality problems using STH examples from four countries | Article page, DOI 10.1093/trstmh/traf005 | Verified from the article page |
| DOIs for Burgert-Brucker 2020, Maroto-Camino 2019, Galiwango 2026, Riley 2020, Collins 2016, Riley 2021, Van Calster 2019, TRIPOD+AI, PROBAST+AI resolve to the stated papers | Crossref | Verified (metadata only) |
| Content of Burgert-Brucker 2020, Maroto-Camino 2019 and Galiwango 2026 | Concept document | **Unverified** beyond title |
| The WHO 2025 LF report recorded 571 IUs requiring MDA and 386 implementing it in the African Region | Concept document | **Unverified.** Not used in any analysis. Do not quote without reading the report |
| An IU with at least five effective rounds proceeds to pre-TAS/TAS | General WHO programme guidance, recalled from memory | **Unverified citation.** The rule is supported empirically by the hindsight check, but a WHO reference must be added before submission |
| Major external NTD funding was suspended in early 2025 | General knowledge | **Unverified citation.** A reference must be added before submission |
| The ESPEN IU Planner shows IU-level funding status from JRSM submissions | ESPEN tool description page | Verified from the page |
| ESPEN's 2021-2030 forecasts assume forecast rounds are delivered | Web search summary of an ESPEN technical note | **Partly verified**; read the note before citing |
| UCDP GED 26.1 is CC BY 4.0 with the Davies et al. 2026 and Sundberg & Melander 2013 citations | UCDP downloads page; DOI checked in Crossref | Verified |

## Claims that must not be made

- That this is the first study of its kind.
- That the model is validated, or ready to guide programme decisions.
- That any predictor causes interruptions.
- That performance in countries left out of training amounts to external validation in
  general; only the countries listed as supported in
  `reports/evaluation/country_transport/transport_by_country.csv` have their own estimates.
- That context does not matter; only conflict and population density were tested.
- Anything about collaborators, endorsements, ethics approval or journal acceptance,
  none of which exist yet.
- That a model is deployed. The public dashboard shows stored research results; no
  model runs as a prediction service.
