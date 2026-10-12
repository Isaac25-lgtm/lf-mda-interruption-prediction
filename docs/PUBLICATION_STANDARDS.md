# Assessment against the ten publication standards

Assessed on 2026-10-12 against the evidence in this repository. No averaged score is
given: each standard is met, partly met or not met, with the file that shows why.
The assessment is the code author's and has not been reviewed.

| # | Standard | Verdict | Evidence | What is missing |
|---|---|---|---|---|
| S1 | Real, consequential problem | **Partly met** | Reported interruptions affected IUs holding tens of millions of people in shock years (`reports/descriptive/burden_by_year.csv`) | The decision point (31 December, supervision allocation) has not been confirmed with any programme |
| S2 | Defensible originality | **Partly met** | Dated PubMed, Europe PMC and GitHub searches found no equivalent study (`docs/LITERATURE_SEARCH_LOG.md`) | Scopus, Web of Science, Google Scholar and grey literature not searched; ESPEN's IU Planner already serves part of the decision |
| S3 | Authentic, legally obtainable data | **Met for access; open for redistribution** | Public download without registration; checksums (`data/manifests/`) | ESPEN states no licence; whether the derived IU table may be public is unconfirmed (`docs/ETHICS_DATA_USE.md`) |
| S4 | Valid outcome and decision-time data | **Not yet met** | Status is coherent with treatment fields; non-reporting and pauses are separated; cohort uses t-1 information only (`docs/LABEL_DECISIONS.md`) | No expert review; no planning data; records are current corrected values, not as known at the time |
| S5 | Adequate independent information | **Not met for prediction; met for description** | 130 test events come from 14 country-years, about 13 effective events (`reports/audit/variance_partition.csv`) | Nothing in the current data can fix this. Descriptive counts do not depend on it |
| S6 | Rigorous statistics and machine learning | **Met** | Pre-specified baselines and models, small grids, all preprocessing inside the fitted object, leakage tests (`tests/`), every experiment logged | Calibration could not be established |
| S7 | Honest validation and transport | **Met** | Locked test opened once (`LOCK.json`); stress years separated; leave-one-country-out reported with a per-country support rule; post hoc models labelled exploratory | No truly external or prospective data |
| S8 | Scientific improvement over prior work | **Met as a negative and descriptive result** | First multi-country description of scale, level and recovery of LF interruptions from public data; a tested null for district-level prediction | The pre-specified hypothesis that a model would beat the rule was not supported |
| S9 | Decision value and safety | **Partly met** | The results argue against district risk scores and for country-level planning signals; the dashboard carries research-only warnings | No user testing; no cost or threshold analysis; decision-curve analysis not done |
| S10 | Publication, reproducibility, feasibility | **Partly met** | Scripted pipeline, run records, generated tables, figures and manuscript draft; TRIPOD+AI tracker | No co-author, no ethics confirmation, no registration, citations flagged in the draft, no tagged release or DOI |

## Fatal-gate check

| Possible fatal failure | Did it occur? |
|---|---|
| No plausible action informed by the result | No. The result informs where early-warning effort should go |
| Identical question already answered | Not found; search incomplete |
| Data inaccessible or redistribution breach | Access is open. Redistribution of the derived table is the open risk |
| Cannot tell interruption from non-report or legitimate pause | Non-report: separable. Legitimate pause: separable from 2021, bounded before then |
| Too few events for any useful analysis | For model comparison the evidence is thin and is reported as such. For description: no |
| Unavoidable leakage or invalid split | No. Tested |
| Test reuse | No. One opening; later models labelled exploratory |
| Study only repeats prior associations | No |
| Fabricated citation or result | No. Unverified items are listed in `docs/RESEARCH_LEDGER.md` |

## Honest overall position

The work is a sound feasibility study and a credible first draft of a descriptive and
methodological paper. It is **not yet ready to submit**. The single largest gap is S4:
until programme experts have reviewed a sample of the labels, every result describes
a reported status. The second is authorship and review by someone who runs or
supports an LF programme.

As a prediction-tool paper it would fail S5 and S8. As a paper on the anatomy of
interruptions with a tested negative result on prediction, it stands on its
descriptive evidence, subject to S4.
