# Manuscript outline

**Superseded by the full draft.** The working manuscript is
[`manuscript_draft.md`](manuscript_draft.md), generated from
[`manuscript_template.md`](manuscript_template.md) by `lf-mda manuscript`. Edit the
template, never the draft: every number in the draft is filled in from result files
(`reports/facts.json`).

## Framing

**Title.** Missed rounds of lymphatic filariasis mass drug administration in Africa,
2016-2025: scale, country-level clustering, recovery, and the limits of district-level
prediction from public WHO ESPEN data.

The paper is about the anatomy of interruptions. The prediction comparison is one
section and its result is negative. This framing was adopted after the locked test
(`docs/DECISIONS.md`, D20); the pre-specified prediction analysis is reported unchanged.

| Section | Main message | Key outputs |
|---|---|---|
| Scale | Interrupted IUs held a large share of the population requiring treatment in shock years | Fig 13, Table 5 |
| Level | Most interruptions are country-wide; most variance is between country-years | Fig 4, Fig 14, Table 7 |
| Recovery | Most IUs resume within one to three years; a minority repeat | Fig 15, Table 6 |
| Label audit | The outcome is coherent but unverified; pauses are bounded | `reports/audit/label_audit.md` |
| Prediction | No model beats a three-year history rule; with public-data lag nothing works | Table 3, Fig 6, Fig 9 |
| Transport | Performance varies widely between held-out countries | Fig 11, Table S2 |
| Exploratory | Three structure-aware models, post hoc, also show no gain | Table X |

**Target journal to reconsider after expert review:** PLOS Neglected Tropical Diseases
(research article). Word limit, figure limits, data policy and fees are **not yet
checked**.

## Before submission

1. Expert review of the label sample and a programme co-author.
2. Citations marked **[citation needed]** and **[to do]** in the draft.
3. Ethics statement, funding, competing interests, author contributions.
4. Official TRIPOD+AI checklist; PROBAST+AI self-appraisal.
5. Fuller literature search (`docs/LITERATURE_SEARCH_LOG.md`, "Not searched").
6. Renumber figures and tables for the chosen main set; move the rest to supporting
   information.
7. Tagged release and Zenodo DOI matching the submitted version.
