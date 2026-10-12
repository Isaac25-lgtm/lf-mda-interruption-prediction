# MASTER IDE RESEARCH HANDOVER — Lymphatic Filariasis MDA Interruption Prediction

> **Document class:** Autonomous coding-agent execution brief, scientific protocol context, quality-assurance contract and publication/demonstration delivery specification.  
> **Project:** WHO ESPEN lymphatic filariasis (LF) implementation-unit mass drug administration (MDA) interruption prediction.  
> **Repository:** https://github.com/Isaac25-lgtm/lf-mda-interruption-prediction  
> **Target branch:** `main` (feature branches/PRs encouraged).  
> **Document date:** 12 October 2026.  
> **Status:** Research *concept* approved for a feasibility audit; **outcome validity, actual sample size, event counts and predictive performance NOT YET VERIFIED**.  
> **Audience:** Claude Code, Codex, other trusted IDE research/coding agents, collaborating methodologists and publication co-authors.  
> **One project only:** This handover is exclusively for the LF–ESPEN project. Do not combine it with, import content from, or commit anything belonging to another research project.

---

## 0. Agent operating contract — read this before writing code

You are a senior research software engineer, biostatistician, machine-learning methodologist, public-health epidemiologist, data steward, and independent quality reviewer assigned to **execute this complete research project in the local IDE from a clean repository**. You will acquire legally available data, assess feasibility, write tested pipelines, fit appropriate baselines and ML models *if justified*, conduct scientifically valid validation, produce all publication-ready research artifacts, build a polished Streamlit dashboard, and push a clean, reviewable repository to the URL above when the release gates pass. The researcher is responsible for final scientific decisions, permissions and manuscript submission. Your outputs must be reproducible by a second researcher.

**Priority hierarchy:** research integrity and legal/ethical data use > label and timing validity > statistical correctness > honest uncertainty > reproducibility > model performance > dashboard appearance. No metric or attractive demo can overrule an invalid outcome or leaky experiment. This is not a Kaggle contest. **Never invent results, downloads, literature findings, author approvals, model metrics, or deployment success.** A lower but valid score is preferable to a higher invalid one. The objective is rigorous publishable research, not a promise of perfection or journal acceptance.

**Autonomy:** Work continuously through steps that can actually be completed. Resolve ordinary dependency, file-format, encoding, mapping, numerical and environment problems without asking repeatedly. Log all changes. **When a fatal scientific gate fails, stop downstream modelling, report the evidence and request the investigator's decision; do not silently relabel, lower standards, substitute an unrelated outcome or keep trying dozens of models.** Administrative blockers such as access permissions may be reported as `BLOCKED`, with work on harmless supporting tasks continuing. Never claim an absent file was downloaded or a test passed.

**Repository scope and permissions:** Read/write/push only this repository. Confirm `git remote -v`, branch, user identity and current state before operations. Never force-push, overwrite the researcher's work, publish secrets, or push restricted data. User requests an eventual push of fully tested code and documentation to GitHub; treat this as permission for routine commits/pushes **once content, confidentiality, reproducibility and scientific gates are satisfied**. Present an explicit go/no-go finding and preserve the complete run log. If the repo is not accessible/authenticated, prepare a verified local commit and provide exact instructions; never falsely report a push.

**Minimum transparent project state:** Maintain `docs/STATUS.md` with a timestamp, lifecycle phase, completed tasks, data access status, scientific gates, verified/blocked items, next commands and links to available results; `docs/DECISIONS.md` with every major methodological change and rationale; `docs/ISSUES.md` with unresolved threats; `docs/RESEARCH_LEDGER.md` for claims and citations; and `reports/runs/` for immutable run manifests. A coding agent should be able to resume without chat history.

### Non-negotiable instructions

1. **Start with a plan, a repository/environment audit and real data acquisition.** Do not jump straight to CatBoost.
2. **Keep raw source files byte-for-byte unchanged**, record URL, selection choices, timestamp, checksum, and allowable license/use. Never commit large raw downloads by default.
3. **Do not fabricate 'expected treatment interruption'.** Distinguish a reported non-delivery from a round formally planned but not carried out.
4. **No training on outcome-year or future-corrected predictors.** Honor actual publication/release cutoffs for predictors *and historical training labels*.
5. **Make baselines strong and explicit.** Random and rule-based baselines, country history, pooled intercept, and appropriate logistic model precede ML.
6. **Preserve a locked last-period test.** Tune only on earlier periods. Do not repeatedly peek at held-out results or rework models in response to the final test.
7. **No p-hacking or model proliferation.** Investigate low performance through documented diagnostics and development-only experiments; make protocol amendments prospectively and disclose deviations.
8. **Build and test the dashboard only on validated artifacts.** Before that, a clearly marked demo shell is acceptable. Do not show fake probabilities as actual research output.
9. **Publication artifacts must derive from code**, with tables/figures/captions/checklists and DOI/source traceability. Make manuscript claims no stronger than evidence.
10. **Never leak API tokens, private source materials, person-identifying data, or confidential programme information.** If WHO supplies non-public planning data, honor its terms and separate it from the open reproducibility path.

### What success means

A successful **feasibility phase** may conclude `GO`, `REDESIGN_REQUIRES_APPROVAL`, or `NO-GO`; accurately reaching `NO-GO` is a successful scientific audit. A successful **full research phase** has validated labels, adequate observations, accepted protocol, leak-resistant modelling, saved and repeatable fitted artifacts, calibrated and uncertainty-qualified held-out results, a polished research dashboard using eligible data, complete paper figures/tables, passing tests and a clean GitHub push. It does **not** mean guaranteeing high AUROC or forcing CatBoost to win.

---

## 1. Scientific identity and the precise research question

**Working scientific title:** *Predicting Interruptions of Lymphatic Filariasis Mass Drug Administration in Active Programmes Across Africa: Development and Temporal and Geographical Validation of Statistical and Machine Learning Models Using Public WHO ESPEN Data.*

**One-sentence question:** Among implementation units (IUs) with an active LF treatment programme for which another treatment round would ordinarily be expected, can information genuinely available **before** the treatment year identify units that subsequently have a *reported interruption*, and do contextual variables provide value beyond their known treatment history?

**Domain and unit:** African LF elimination programmes; one WHO ESPEN implementation unit in one treatment year (`IU_ID × year`). Repeated observations within IUs, nested within countries, are **not independent rows**. This project does not diagnose individuals or predict infection risk.

**Intended decision:** Before next year's mass-drug-administration activities, an NTD programme or partner with scarce supervisory/contingency support chooses the IUs requiring extra attention. The goal is a valid risk *ranking* for support allocation, not punishment, defunding, or false claims that retrospective ranking prevents interruptions.

### Context and importance

LF can cause lymphoedema and hydrocele and is targeted for elimination through repeated MDA and morbidity management. WHO's 2025 LF report (published October 2026) recorded hundreds of implementation units internationally that still required MDA without recorded delivery. In the African Region it recorded **571 IUs requiring MDA and 386 implementing it in 2025**. These figures establish that reported non-delivery matters but **do not imply that 185 are true interruptions in previously active programmes**. Never turn that subtraction into our sample or event count. A never-started programme, legitimate pause for impact assessment, post-intervention surveillance, absent Joint Reporting Form (JRF), and documented missed planned round are distinct states. Actual 2014–2025 country/IU counts remain unknown pending download.

### Research aim and no more than three objectives

**Aim:** Determine whether historical programme and pre-decision contextual information can prospectively-style predict reported LF MDA interruption among active African implementation units, and whether more complex modelling provides independent predictive and operational value.

1. **Outcome and data validity:** Construct and audit a multi-country IU-year panel that separates reported interruptions, delivered rounds, non-reporting, never-started programmes and legitimate pauses; evaluate how reliable an 'expected round' proxy is against expert judgement and, if available, prior-year medicine-request plans.
2. **Predictive development and comparison:** Evaluate a fixed history rule, appropriate hierarchical/penalized logistic regression, and CatBoost; compare history-only versus context-augmented predictors and a delayed public-data scenario against an internal programme-information scenario.
3. **Transport, calibration and decision value:** Quantify time-forward performance, cross-country heterogeneity/holdout performance when supportable, uncertainty, calibration and the proportion of genuine interruptions captured at realistic supervision capacity.

**Pre-specified scientific nulls:** History alone may be sufficient. Context may offer no additional out-of-sample value. Country identity may dominate. A scientifically valid non-superiority finding only has value when label validity and precision support it; 'our model did not win' alone is not a publishable claim.

---

## 2. Literature positioning and our real contribution

**Most important exact comparator:** Fuller BB et al. (2023), *Contextual determinants of mass drug administration performance: Modelling fourteen years of lymphatic filariasis treatments in West Africa*, *PLOS Neglected Tropical Diseases*, DOI https://doi.org/10.1371/journal.pntd.0011146. It analysed **3,880 delivered MDAs across 647 districts in 10 West African countries during 2007–2020**, associating epidemiological treatment coverage with programme rounds, rainfall, temperature, conflict, epidemics and other context using multilevel regression. It was explanatory, included delivered campaigns, used restricted data and did not establish future-year predictive generalization. **Never claim Fuller did not study this disease or these contextual factors.**

**Critical data-quality source (must be read and incorporated):** Ng CW, Maddren R, Anderson RM (2025), *Challenges in assessing the impact of infection and disease control interventions over the past decade based on the Expanded Special Project for the Elimination of Neglected Topical Diseases (ESPEN) database*, *Transactions of the Royal Society of Tropical Medicine and Hygiene* 119(7):767–770, DOI https://doi.org/10.1093/trstmh/traf005. It documents reporting, denominator, consistency and coverage problems in ESPEN, based substantially on soil-transmitted helminthiasis illustrations. **Do not casually generalize all quantitative data-quality findings to LF; inspect LF records separately.**

Other competitors: Burgert-Brucker et al. (2020) on failure of pre-transmission-assessment surveys (different outcome; DOI https://doi.org/10.1371/journal.pntd.0008301); Maroto-Camino et al. (2019) on independent verification of MDA coverage (DOI https://doi.org/10.1371/journal.pntd.0007337); Galiwango et al. (2026), review of NTD ML applications (DOI https://doi.org/10.1038/s43856-026-01706-3); WHO ESPEN Implementation Unit Planner (important deployed tool, even if no peer-reviewed prediction); WHO 2025 LF report https://www.who.int/publications/journals/weekly-epidemiological-record/wer101-39.

### Closest work versus proposed contribution

| Dimension | Existing best-known work | Our *testable* advancement |
|---|---|---|
| Outcome | Fuller: coverage **of delivered campaigns** | Reported **non-delivery of expected rounds** in previously active IUs; construct/independently check labels |
| Question | Retrospective factors associated with coverage | Forecast failure before programme action; prediction at real information cutoff |
| Comparison | Hierarchical explanatory regression | History-only operational rule **versus** parsimonious regression **versus** one gradient-boosted model |
| Evaluation | Primarily explanatory estimates | Rolling-origin, frozen later-year assessment and held-out countries if feasible |
| Context | Rainfall, conflict, isolation linked to coverage | Does historical context add **future predictive value beyond programme history**? |
| Value | Explanatory guidance | Calibrated risk and captured interruptions among top 10–20% of eligible IUs |
| Replication | Restricted historical MDA database | Public ESPEN downloads + versioned preprocessing and code, subject to data reuse terms |

**Novelty is conditional.** Do not assert 'first ever' unless repeated dated searches in PubMed, Europe PMC, Scopus (if accessible), medRxiv, Google Scholar, GitHub, CRAN, PyPI, conference and thesis indexes support it. Maintain `docs/LITERATURE_SEARCH_LOG.md` with query, platform, date, results, screened articles, DOI, exact/related/same-question status, and why prior work does or does not already answer the question. Pay special attention to independent ESPEN applications and WHO operational forecasting/planning products. If a substantially identical predictive tool/paper exists, raise `NOVELTY_GATE_FAILED`.

---

## 3. Data inventory, official links and acquisition workflow

| Resource | Role | Starting URL / access caveat |
|---|---|---|
| WHO ESPEN LF IU-level data | Main reported IU/year treatments and status | https://espen.afro.who.int/maps-data/data-query-tools/download-data — public **download form**, not a verified unauthenticated API |
| WHO LF dictionary | Understand `IU_ID`, status, flags and denominator definitions | https://espen.afro.who.int/sites/default/files/content/document/Lymphatic_Filariasis_EN_FR_PT.pdf |
| ESPEN updates | Assess backdating/release timing and revisions | https://espen.afro.who.int/maps-data/data-updates |
| ESPEN IU Planner | Deployed tool against which decision novelty must be checked | https://espen.afro.who.int/tools-resources/advanced-analytical-tools/implementation-unit-planner |
| UCDP Georeferenced Event Dataset | Open conflict context; dates and data-vintage rules required | https://ucdp.uu.se/downloads/ |
| CHIRPS | Pre-decision rainfall/anomaly context | https://www.chc.ucsb.edu/data/chirps |
| Global access/travel time surface | Static accessibility covariate; check raster use and geography | https://malariaatlas.org/research-project/accessibility-to-cities/ (verify active links before download) |
| Optional WorldPop / official IU boundaries | Population/geospatial features only if verified | https://www.worldpop.org/ and ESPEN map resources |
| Optional WHO/ESPEN historical JRSM | Proof that a treatment round was requested/planned | **Not publicly verified**; institutional request + written terms may be necessary |

### Exact main-data procedure

1. Create `data/raw/espen_lf/` locally. In a browser visit official ESPEN **Download data** form. Select **Lymphatic Filariasis**, **implementation-unit (IU) level**, **2014–2025** and one endemic reporting country; download once and record file type/columns/encoding. Repeat for eligible African countries, or use an officially documented permitted API if one exists. Do **not** fabricate a query endpoint or evade rate limits/robot protection. Automated browser download is allowed only if terms and access support it.
2. Keep every original file and source label untouched; store SHA-256, URL, country, date, source selection, file size, original name and data snapshot date in `data/manifests/espen_sources.csv`. Store an `institutional_perms.md` describing reuse and attribution rights. If terms do not permit redistribution, keep the transformed panel untracked and make public code able to reconstruct it from lawful user-provided files.
3. Verify all country files against official column definitions. Actual field names/coding trump assumptions. Avoid silently interpreting string `'0'` as numeric without diagnostics. Treat missing, suppressed, zero and blank as different until examined. Detect whether coverage is expressed as fraction or percentage **per field and source**, never assume `0.7` and `70` mean the same.
4. Do not fetch all climate/conflict rasters until the core LF outcome audit passes. Context data may be expensive, less timely and scientifically irrelevant if the primary label is invalid.
5. Make acquisition re-runnable or provide an explicit guided/manual fetch procedure with automated validation; no synthetic files may masquerade as raw ESPEN downloads.

**Fields to inspect (dictionary-dependent, verify exact schema):** `ADMIN0ISO3`, `ADMIN0`, `ADMIN1`, `ADMIN2`, `IUs_NAME`, `IU_ID`, `IU_CODE`, `Year`, `PopTot`, `PopReq`, `PopNoTx`, `PopTrg`, `PopTreat`, `Cov`, `EpiCov`, `MDA`, `EffMDA`, `EpiMDA`, `EpiEffMDA`, `MDA_n`, `EpiMDA_n`, `MDA_scheme`, `Endemicity`, `Endemicity_ID`, `JRF_submitted`. Presence of column in a dictionary does **not** establish completeness, stable coding, validity or same meaning across countries and years.

### Initial local commands (illustrative: agent must adapt to real repo and OS)

```bash
# Before any code, check Git/OS/Python and install only justified dependencies
git clone https://github.com/Isaac25-lgtm/lf-mda-interruption-prediction.git
cd lf-mda-interruption-prediction
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pytest -q
python -m lf_mda.audit --input data/raw/espen_lf --out reports/audit
```

These commands are a **target interface that the IDE agent must implement**, not a claim that files/scripts already exist. Document working commands and platform-specific differences in `README.md`. If full-country downloads are blocked, enter `BLOCKED_DATA_ACCESS`; do not replace them with synthetic records and proceed as though empirical modelling occurred.

---

## 4. Cohort, status taxonomy and the **fatal label gate**

**Primary estimand:** the probability of a *reported interruption of an expected LF treatment round during year t* among IUs *known by the decision date at end of t−1* to have active programmes. The outcome is a WHO-reported/recorded programme status, not independent proof of non-delivery.

**Crucial separation:** `PopReq(t)>0` and 'not delivered' in the retrospective year-t report establish reported non-delivery among units later known to require treatment. They do **not** prove that a medicine-request-supported campaign was planned or that the IU was eligible for prediction at 31 Dec t−1. For a prospective-style eligible set, use pre-cutoff `PopReq(t−1)` and pre-cutoff status/planning info only. Outcome-year fields can adjudicate the eventual observed status but must not enter eligibility/prediction features.

**Provisional inclusion:** IU required LF MDA according to pre-decision information; evidence of delivery in t−1 or t−2; not known to be under impact assessment, non-endemic, post-intervention surveillance or legitimate pause before t. The final rule and its operational interpretation require domain expert approval. Recently 'delivered' does not necessarily imply another formal campaign was planned; mark `expected_round_evidence = proxy`, not 'verified planned'. If formally dated JRSM plans arrive, maintain a stronger `planned_round_confirmed` outcome as a separate validation or revised-primary option with investigator sign-off.

**Outcome classes (apply in a declared precedence order and QA cross-tabs):**

| Class | Observed evidence | Analytic role |
|---|---|---|
| `reported_interruption_status` | submitted JRF, outcome-year requirement, documented `MDA not delivered – Endemic` status | Candidate positive; **not** externally validated by field status alone |
| `delivered` | submitted programme information and consistent positive delivery, not conflicting | Candidate negative |
| `legitimate_pause_IA` | officially under impact assessment | Exclude from binary outcome; report number |
| `surveillance_or_stopped` | post-intervention surveillance, non-endemic or legitimate stop | Exclude and separately account |
| `never_started` | no prior delivery despite due status | Exclude from primary active-programme cohort; count |
| `missing_JRF` | report not submitted | **Missing label**, not automatically failure |
| `missing_iu_year` | known IU absent from current-year extraction | Missing label, not interruption |
| `contradictory` | e.g. status not delivered but `PopTreat>0`/`EpiMDA=1` | Quarantine for QA; no automatic positive |
| `inferred_non_delivery` | JRF submitted, `EpiMDA=0`, status unmapped; possible missing-derived false zero | Sensitivity only after field inspection |
| `unknown` | any other ambiguous coding | Exclude from primary, tabulate |

**Outcome engineering checks:** inspect actual `Endemicity` distinct raw values, numeric codes, years, country variations and missingness; confirm relationship to official legend. Verify that `MDA`, `EpiMDA` and `EpiEffMDA` aren't mere transformations of missing/coverage columns. Check `PopTreat > 0` when flags equal zero, `PopReq=0` when treatment occurs, coverage above 100%, impossible denominators, duplicate IU-year records, country boundary shifts, rows absent for only some years and regression-to-mean reporting. Ambiguous status values require a maintained manually reviewed mapping CSV, not brittle keyword regex alone.

**Independent validation of labels:** request cross-country NTD programme officer review using a stratified sample of positives, apparent negatives and ambiguous cases from relevant countries. A 50-record review focused only on positives estimates positive predictive value of the label, not sensitivity/specificity; add reviews of negatives and questionable codes if feasible. Report reviewer identity/role (with consent), country coverage, sampling logic, agreement, uncertainty and whether planned round evidence was verified. The original `~70% confirmed` rule is **provisional and needs investigator/domain agreement**, not a universal scientific fact. A knowledgeable officer in Uganda cannot automatically verify specific campaigns in a different country. Ask ESPEN whether historical IU-level **Joint Request for Selected Medicines (JRSM)** planning/medicine requests can be accessed, and secure terms before use.

**Do not declare a 'valid label' until:** mapping is reproducible, contradictory states resolved or excluded, the due/expected distinction is documented, retrospective eligibility is separated from outcome-year classification, and sample of external programme judgments provides credible support. If inadequate, issue `STOP_LABEL_INVALID` and do not train an interruption model.

---

## 5. Effective sample size, event volume and selection bias

Immediately following outcome construction, write `reports/audit/label_audit.md` and machine-readable tables by **country × year × class** with: IU-year counts; distinct IUs; years observed; eligible active IUs; reported interruptions; delivered; missing JRF; never started; impact assessment; surveillance/stopped; inferred/contradictory; frequency of boundary/name/code change; number of countries contributing each event; and developments/test-window counts.

Evaluate selection consequences: excluding all missing reports may produce biased optimistic forecasts if nonreporting is associated with programme failure. Compare alternative missingness scenarios; if unknown, declare partial identifiability rather than guessing. Examine attrition as IUs legitimately exit MDA and absence of follow-up; avoid conditioning on a future outcome when selecting eligible units.

**Quantitative adequacy is not 'rows × years'**. Repeated IU observations and strong country clustering lower effective independent information. Calculate prevalence, events per development split, unique event-producing IUs/countries, simple statistical model complexity and precision of performance intervals. Use recognized clinical prediction model sample-size methods *critically adapted* for clustered programme data; these are not automatic universal guarantees for CatBoost. A provisional target in concept is ~100 independent future events for reasonably interpretable validation with tighter intervals desirable, but model superiority depends on the paired discordance and meaningful gain. Compute study-specific feasibility with sensitivity to clustering. If insufficient events, downsize model, aggregate only if substantively valid, lengthen outcome horizon only if no test contamination, or **ask to end the study**. Never change the outcome simply to increase event counts without explicit approval.

**Window design:** Current concept proposes 2014–2025 extraction; development 2016–2019; stress evaluation of 2020–2021; candidate development evaluation 2022–2023 and final frozen 2024–2025. These are **provisional**. Recalculate after audit, especially if 2022–2025 positives are insufficient. Treatment during COVID-19 is an unpredictable shock at a Dec 2019 decision point; don't simply drop 2020–21 and claim normal-world generalization. Report separate stress tests and justify exclusions prospectively.

### Hard decision matrix

- `GO`: valid label or accepted transparent proxy, sufficiently distributed usable events, feasible prediction-time scenario, baseline experiment demonstrates an estimable problem, novelty remains defensible.
- `REDESIGN_REQUIRES_APPROVAL`: usable data but target definition / validation claim must change; list alternatives with losses to novelty.
- `NO-GO`: meaningful positive/negative labels cannot be distinguished, too few independent events for any scientifically useful analysis, serious unrecoverable leakage or no practical information advantage.
- `BLOCKED`: source website/admin restrictions or expert verification awaited; proceed on tests, scaffold and literature *without inventing empirical findings*.

---

## 6. Prediction clock and as-of leakage contract

**Proposed forecast clock:** 31 December in year t−1 for year t. Confirm with programme collaborator whether this is meaningful relative to medicine ordering, budget deadlines and campaign scheduling; it may need to move earlier to match a real support decision.

**Information scenario P (internal programme):** programme plausibly knows its own t−1 outcomes, funding/plans and current statuses at the decision cutoff. Public ESPEN extract is a proxy for the information the programme might have held then. If no historical original records, call this *programme-information retrospective reconstruction*, not a proven faithful live simulation.

**Information scenario E (external analyst using public ESPEN):** both feature **and training outcome** availability must follow their **actual historical public release dates**. Year t−1 is often not available at end of t−1; the latest may be t−2 or earlier. Do not assume uniformly t−2: construct `source_release_calendar.csv` from archived update logs and per-country snapshots if possible. For each fold `t`, train only on labels available by cutoff, and compute features using only data published by cutoff. If historical data vintages do not exist, label this scenario *approximate as-of evaluation with current corrected historical values*. **Never call hindsight backtesting equivalent to real-time prospective validation.**

**Common leakage sources:** outcome-year endemicity, current-year `MDA`, cumulative `EpiMDA_n(t)`, current-year `PopTreat`, `PopTrg`, `PopReq` as features or advance eligibility, standardized features computed globally, fitted imputation using full data, conflict events finalized after relevant cutoff, back-cast WorldPop estimates incorporating future censuses, data revisions, post-outcome data from joint reporting form, encoded target categories and country aggregate ratios computed from the entire dataset.

Build a machine-checked feature manifest (`config/features.yaml` + `data/processed/feature_provenance.parquet`) with: source, units, valid range, observed interval, earliest historical release date, lag logic, missing-data rule, clipping, which scenario allows it and whether derived using outcome-year information. Implement tests that generate deliberately future-only predictors and assert they are **rejected**. There must be zero future-feature exceptions in primary models.

---

## 7. End-to-end data science cycle and numbered execution phases

Each phase has code, tests, generated reports and a scientific gate. Add `make`/PowerShell/`python -m ...` documented commands. Do not mark a phase complete until outputs exist and the relevant tests pass.

### Phase 0 — Repository and environment bootstrap

- Clone/open correct repo, inspect remote and branch, record Python/platform/GPU (GPU is not required), storage and runtime budget. Confirm no conflicting pre-existing work.
- Create `.gitignore`, `pyproject.toml` with pinned practical versions, `.python-version` or supported Python version policy, `uv.lock`/`requirements.lock` where appropriate, a CLI entry point, optional Dockerfile, `LICENSE` chosen by owner (do not assume data rights), `CITATION.cff`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` optional, and a clean status/decision file.
- Write deterministic seed policy, legal sources notice, reproducibility quickstart, comprehensive `README.md` with structured metadata and **meaningful colored status badges** (Python, CI, license, data status, dashboard) that reflect actual live CI/release status; never false green 'validated' badges.
- Install only needed dependencies (pandas, numpy, pyarrow, scikit-learn, scipy, statsmodels, CatBoost, Plotly, Streamlit, geopandas, rasterio, shap as justified); keep heavyweight geospatial extras optional.

### Phase 1 — Literature, source and ethics lock

- Verify source DOIs and official links. Read Ng et al. 2025, Fuller 2023, ESPEN dictionary and IU planner details. Record precise overlaps/gaps and data rights. Ask for expert involvement; do not claim collaborators have approved unless documented.
- Produce `docs/SCIENTIFIC_PROTOCOL.md`, `docs/LITERATURE_MATRIX.md`, `docs/LITERATURE_SEARCH_LOG.md`, `docs/ETHICS_DATA_USE.md`, `docs/PUBLICATION_STANDARDS.md`. Explicitly distinguish verified facts, proposed choices, unverified points and fatal conditions.

### Phase 2 — Obtain raw ESPEN data and produce manifest

- Execute permitted form/API downloads or guide user to obtain files and then automatically import; checksum and archive untouched originals outside Git; implement input validation, encoding, schema and duplicate checks.
- Produce a detailed **source-by-source coverage report** so omissions of countries/years are visible rather than silently pooling incompletely observed data. Record whether data use prohibits rehosting.

### Phase 3 — Raw-data profiling and label audit **before model fitting**

- Implement/extend audited Python modules for field coercion, status mapping, IU/year linkage and lifecycle states. The earlier `espen_lf_audit.py` is a **prototype tested only on synthetic data**, not a validated parser; use it as guidance, challenge its assumptions, write unit tests and fix issues on actual extracts.
- Build missing country × IU × year grid cautiously; a missing row is **not** a no-MDA outcome. Preserve country-specific IDs, detect repeated IU_ID across countries, document 2014 lack of history.
- Create full audit markdown + parquet/csv tables, figures showing missingness/event distribution and an expert-review sample with balanced representations. Ask for actual expert verification; cannot mark it complete by code.
- **Gate:** issue evidence-based `GO / REDESIGN / NO-GO` before proceeding to advanced modelling.

### Phase 4 — Preprocessing and predictor construction

- Clean inconsistent numeric encoding, missingness and impossible values with documented QA decisions. Check coverage ratio scaling and denominator rules. Handle distinct status categories by country and year. Do not impute outcome to negative.
- Build true year-index lags per IU using joins on `(country, IU_ID, year)`, never a blind row `shift` over a gappy panel. For known boundary changes, reconcile lineage from source history or exclude affected units in sensitivity runs; don't assume stable IU codes.
- Optional spatial join to UCDP events, CHIRPS anomalies, travel time, population density after label gate. Use exact spatial boundary and CRS documentation, distinguish historic from contemporary boundaries, missing geometry and exposure periods, plus spatial aggregation design. Features constructed with historical publication cutoff.
- Split by decision time **before** train-dependent preprocessing; fit encoding, scaling and imputation in development folds only; store pipelines and feature manifests.

### Phase 5 — Descriptive analysis and diagnostic visualization

- Publication-ready counts by country/year, class transitions, missing reporting, attrition, descriptive event rates, comparison across programme maturity and geographies. Show denominators/units. Use appropriately scoped maps; avoid misleading color scales when many areas lack observations. Generate actual figures from data with alt-text and captions.
- Baseline variance and class-prevalence diagnostics; estimate trivial strategy performance; if little predictable variation exists, document this rather than pretending ML can fix it.

### Phase 6 — Protocol freeze and baseline models

- Freeze `config/protocol.yaml` (revisions with date and explanation): outcome, eligibility, dates, feature cutoff, splits, performance hierarchy, meaningful improvement criterion, model count and small hyperparameter budget.
- Implement a no-skill prevalence baseline, prior-period/country-only rates, **pre-specified treatment-history rule**, and parsimonious logistic model; country random effects or penalized fixed effects chosen according to actual event support and new-country inference. Country random intercept cannot meaningfully be estimated for unseen countries as if identity were known; marginalize or use hierarchical shrinkage and evaluate explicitly.
- Rolling-origin evaluation on **development** years only; nested inner folds for tuning and imputation. Ensure logistic, rules and ML evaluated on identical eligible test IU-years and proper score vectors.

### Phase 7 — Bounded, justified machine learning

- Start with CatBoost constrained by event counts. Compare history-only and history+context; optionally country identity on/off. Use small fixed grids, shallow trees, calibration on disjoint validation records, early stopping and random seeds. Avoid comparing dozens of methods without hypotheses.
- If legitimate underperformance persists, inspect feature absence, label noise, class sparsity, calibration, transformations and cross-country domain shifts. A justified change could include gradient-boosting variant or monotonic rule-based logistic/GAM, but **no unapproved architecture expansion** and no final-test-guided selection. Log every experiment, including failed ones.

### Phase 8 — Locked independent evaluation

- Only once: open frozen end years after protocol selection. Refit on eligible development records, generate held-out predictions, archive model digests, compute CIs; never use these outcomes for tuning.
- Report AUROC, PR-AUC with prevalence, Brier/log loss, calibration intercept/slope and reliability plot, score distributions, capture@top10%/20% and captured additional interruptions per support capacity. Standard error must reflect repeated IUs and country clustering. Use proper paired comparisons and confidence intervals; no claims of meaningful gains if interval crosses zero.
- Evaluate geographic transport via country-blocked splits **without training on the held-out country's years**; nested tuning within remaining countries, compare to country-agnostic baseline. If small eligible positives, do not imply external validity. Keep temporal and country-holdout experiments analytically distinct.
- Validate absence of obvious country shortcuts and sensitivity to COVID disruption, missing reports, alternative risk population, ambiguous status, country leaveouts, boundary changes, conflicting flags and approximate historical data releases.

### Phase 9 — Interpretability, publication tables and uncertainty

- For logistic models, coefficients/odds ratios with uncertainty and cautious interpretation. For CatBoost, SHAP/permutation importance *as model associations*, not causal programme risk factors. No claim that rainfall directly causes a missed treatment from predictive associations.
- Export reproducible Table 1 cohort/missingness, Table 2 study population/events/countries, Table 3 discrimination/calibration/capture, Table 4 ablations/sensitivity, appropriate extended appendices; Figures cohort flow, study geography (only if geocoded), outcomes across years, performance/PR/ROC, calibration, risk/capture chart, stability/transport, explainability. All figure values come from actual runs and have units, sample sizes and citations.

### Phase 10 — Streamlit research dashboard

- Build **after validated scores exist**, with professional responsive layout, clear scientific branding and accessible fonts/contrasts. Suggested navigation: `Study overview`, `Data quality`, `Implementation-unit map`, `Risk explorer`, `Model comparison`, `Capacity prioritization`, `Validation & uncertainty`, `Methods`, `Limitations & citation`.
- Show verified date range, number of IUs/countries, model version, and explicit **retrospective research-only** label. Maps distinguish `no data`, `not eligible`, `genuine interruption`, `delivered` and `unverified`; predictions only if the model and geospatial joins are reliable. Do not publish subcountry risk rankings that domain partners judge misleading or restricted.
- Ability to choose an evaluation year/country and top 10/20% support level must recompute *stored valid held-out predictions*, not infer from outcome labels or update the trained model on request. Provide performance CI and baseline comparison. Explain exactly what 'risk' means and potential harm from misinterpretation.
- `dashboard/app.py` should load versioned model/processed public artifacts efficiently via caching; provide a **clear fallback** to a reproducible aggregate synthetic tutorial if full public data rights unconfirmed, with a prominent `DEMONSTRATION — SYNTHETIC DATA` label. Do not overstate results.
- Deploy on Streamlit Community Cloud if size, availability and terms permit; escalate to Cloud Run/other managed hosting only if free constraints materially degrade reliability. Ensure app does not attempt multi-country training on startup. Record hosted link in README and final manuscript resources once real. Include uptime checks and graceful error messages.

### Phase 11 — Release, GitHub and paper-ready packaging

- Run unit/integration/scientific and dashboard tests; run real reproducibility smoke test from clean environment. Run privacy/data-license audit, all file sizes/secrets scan, broken-link check, citation audit, dependency checks. Ensure model artifact source/version checksums and deterministic prediction examples.
- Provide a professionally formatted `README.md`: concise problem, literature novelty, citation block, real status badges, architecture diagram, pipeline quickstart, data acquisition, models, evaluation, paper figures, dashboard link, honest limitations, provenance, attribution, license, reproducibility and contact/issue instructions. Use clear headings, Markdown tables and a few purposeful colorful badges, **not decorative untrue scientific success indicators**.
- Commit small purposeful changes in stages (`build: ...`, `data: ...`, `model: ...`, `dashboard: ...`, `docs: ...`), avoid force pushing; create PR if review required. Push only after no secrets/private datasets and verified tests. Tag a version (`v0.1-audit`, later `v1.0-research-release`) appropriate to actual completion; don't pretend publication is already accepted.
- Register a public GitHub release and prepare Zenodo DOI archiving if owner authorizes repository/release and contents. Include dashboard URL in scientific paper only after verifying accessible URL; permanent code/archive link remains primary reproducibility reference.

---

## 8. Required repository tree — adapt only with explanation

```text
lf-mda-interruption-prediction/
├── README.md                        # Professional entrypoint + real badges/status/links
├── IDE_RESEARCH_MASTER_CONTEXT.md   # This entire handover, copied without scientific dilution
├── LICENSE                          # Code license, not an ESPEN data license
├── CITATION.cff
├── pyproject.toml
├── .gitignore
├── .env.example                     # No real secrets
├── .github/workflows/ci.yml
├── config/
│   ├── protocol.yaml                # FROZEN before final evaluation
│   ├── features.yaml
│   ├── data_sources.yaml
│   └── status_map_reviewed.csv
├── data/
│   ├── README.md                     # Access/permissions, no unapproved raw data
│   ├── raw/espen_lf/.gitkeep
│   ├── raw/context/.gitkeep
│   ├── manifests/.gitkeep
│   └── processed/.gitkeep
├── src/lf_mda/
│   ├── __init__.py
│   ├── cli.py
│   ├── ingest.py
│   ├── audit.py
│   ├── labels.py
│   ├── iu_lineage.py
│   ├── vintages.py
│   ├── spatial.py
│   ├── features.py
│   ├── splits.py
│   ├── baselines.py
│   ├── model.py
│   ├── calibrate.py
│   ├── evaluate.py
│   ├── uncertainty.py
│   └── render_paper.py
├── tests/
│   ├── fixtures/                    # Synthetic unit tests only, never research 'results'
│   ├── test_outcome_precedence.py
│   ├── test_missing_not_failure.py
│   ├── test_asof_leakage.py
│   ├── test_iu_lineage.py
│   ├── test_splits.py
│   ├── test_metrics.py
│   └── test_dashboard.py
├── dashboard/
│   ├── app.py
│   ├── pages/
│   ├── assets/
│   └── README.md
├── reports/
│   ├── audit/
│   ├── figures/
│   ├── tables/
│   ├── evaluation/
│   └── runs/
├── models/README.md                 # Only permissible, versioned fitted models
├── manuscript/
│   ├── outline.md
│   ├── results_traceability.md
│   ├── tripod_ai_checklist.md
│   ├── figures_and_tables.md
│   └── data_code_availability.md
└── docs/
    ├── STATUS.md
    ├── SCIENTIFIC_PROTOCOL.md
    ├── LITERATURE_MATRIX.md
    ├── LITERATURE_SEARCH_LOG.md
    ├── PUBLICATION_STANDARDS.md
    ├── RESEARCH_LEDGER.md
    ├── ETHICS_DATA_USE.md
    ├── DATA_DICTIONARY.md
    ├── LABEL_DECISIONS.md
    ├── PREDICTOR_AVAILABILITY.md
    ├── DECISIONS.md
    ├── ISSUES.md
    └── REPRODUCIBILITY.md
```

**Data exclusions from Git:** original country downloads, any nonpublic plans, derived tables disallowed by ESPEN, credentials, `.env`, caches, oversized shapefiles and model binaries when source/data rights are unclear. `.gitignore` default-denies `data/raw/**` and local secrets. Check Git LFS/asset hosting policies for legitimate larger model artifacts.

---

## 9. Performance-debugging and controlled improvement playbook

When a development-fold model performs poorly, do **not** automatically add XGBoost, Random Forest, neural networks or search hundreds of hyperparameters. Investigate systematically, record the evidence, repair at the earliest stage and rerun on **development-only** periods:

| Symptom | Questions to investigate | Permitted response |
|---|---|---|
| Near-chance AUROC/PR | Correct label coding? IUs actually active? Missing years? Little prevalence variation? | QA label/sample; compare prevalence and history rule; halt if no usable signal |
| Great random-split score, poor future-year score | Was a random split used? Are outcomes/regimens/revisions leaking? Policy shocks? | Remove random split claims; inspect cutoff, drift, country mix; frozen test untouched |
| CatBoost underperforms rule | Overfit? Few events? Country shortcuts? Poor temporal features? | Stronger regularization, shallower depth, history-only model, simple GAM; retain rule if best |
| Good AUROC but poor calibration | Class weighting? Oversampling? Distribution shift? | Calibrate on separate development folds, inspect calibration by year/country, acknowledge uncertainty |
| Good pooled, poor new-country | Country ID/mean exposure shortcut; differing codes/distributions? | Feature ablation; train without country ID; present transport failure accurately |
| Missing/contradictory labels | JRF not submitted? Coding status derived from coverage? Legitimate pauses? | Manual coding map review, expert adjudication; **do not convert unknown to 0** |
| Unstable estimates, huge CIs | Few event countries? Bootstrap design wrong? Too many degrees of freedom? | Reduce model complexity, wider uncertainty, possibly stop |
| Context variables 'help' implausibly | Same-year rainfall/conflict or later revised data? Historical covariate provenance? | Inspect release dates/spatial join; remove leaky features and recompute development results |
| Map disagreeing with table | Geometry mismatch, CRS, country/IU code reuse or suppressed shapes? | Fix keyed spatial join; no geographic conclusions until verified |
| Metric varies across reruns | Seed not fixed? differing splits? sample order? nondeterministic pipeline? | Seed and hash datasets/config; correct sample ordering; CI reproducibility test |

**Search budget and protocol discipline:** choose a small fixed grid first. After a poor development result, permit up to two documented diagnostic/refinement rounds before reassessing feasibility or requesting approval for a more radical model or outcome. Any choice motivated by final held-out metrics must be labelled exploratory; evaluate on a *new future untouched dataset* before making confirmatory claims. Never silently redefine outcome, discard hard countries, search only winning seeds, suppress negative comparisons, or move thresholds after seeing the test result.

---

## 10. Statistical evaluation contract (publication grade)

### Comparators and deployment realism

A simple history rule is the mandatory main comparator. Report no-skill/prior rate and country-only baselines; show if a sophisticated model merely learns prior-country reporting differences. The earliest decision date dictates predictor sets and label availability. A model cannot be called operationally superior solely because it has good retrospective discrimination if the national programme already knows more up-to-date data.

### Metrics and estimands

- AUROC (discrimination) and PR-AUC **alongside event prevalence**, not alone.
- At an actionable top-k capacity (10% and 20% of eligible IUs): true positives, precision/PPV, sensitivity/recall, extra genuine interruptions identified over rule, paired Δcapture and cluster uncertainty; optionally number needed to screen.
- Probability calibration: Brier score, intercept, slope, risk-stratified reliability and expected/observed count. If event count too low for stable calibration, report and do not claim it.
- Sensitivity to missing labels, test period, country, stage, reporting completeness and contextual exposure, with confidence intervals and uncertainty over clustering.
- Decision-curve/net benefit only when threshold probabilities map to a defensible intervention trade-off and compatible prevalence; otherwise prefer top-k utility without misuse of DCA.
- No 'accuracy = X%' headline for class-imbalanced interruptions; no claim of causality from SHAP importance.

**Uncertainty:** resample at relevant independent clusters (country for multinational target; IU within-country for selected analyses), respect calendar/block dependence and report exact number of countries/events. If only a few countries contribute outcomes, naive country-bootstrap intervals may be unreliable: use sensitivity/jackknife over countries and explicitly flag uncertainty. Calibration plots need event support and honest bins/smoothers.

---

## 11. Ten scientific publication standards — fatal gates apply

| # | Standard | Mandatory proof for this project | Fatal failure example |
|---|---|---|---|
| S1 | Real consequential problem | LF programme interruption and pre-year support decision defined with practitioner | No plausible action informed by predicted risk |
| S2 | Defensible originality | Detailed Fuller 2023 + Ng 2025 + operational-tool comparison and dated literature log | Identical question rigorously answered already |
| S3 | Authentic legally obtainable data | Verified ESPEN provenance, files, permissions, reusable retrieval instructions | Dataset inaccessible/unusable or redistribution violates license |
| S4 | Valid outcome and decision-time data | Reported status, expected-round evidence, expert review and availability register | Cannot tell genuine interruption from non-report/legitimate pause |
| S5 | Adequate independent information | Events and distinct IUs/countries per split; power/precision justified | Too few events for meaningful estimation/validation |
| S6 | Rigorous statistics & ML | Appropriate history rule, parsimonious regression, bounded CatBoost; leak-free training | Invalid split or unavoidable label leakage |
| S7 | Honest validation & transport | Locked later years; new-country evaluation only when supportable; calibration | Test reuse or claim of external validation from mixed-country random rows |
| S8 | Scientific improvement over prior work | Test whether context/ML adds *meaningful* future value over history rule | Study only repeats Fuller's coverage associations without new inference |
| S9 | Decision value & safety | Real supervision capacity, cost of misses/false alarms, risk communication | Risk ranking provides no user advantage or causes unacceptable harm |
| S10 | Publication/reproducibility/feasibility | Verified code/results, TRIPOD+AI relevance, appropriate ethics, journal fit/waiver check | Fabricated citation/result, unreproducible pipeline or permission breach |

Averaged numeric 'quality scores' are prohibited as substitutes for evidence. Every claim must link to run IDs, tables, papers or officially documented source. Career fit is separate: this study is applied predictive global-health analytics, not by itself a clinical deep-learning publication.

---

## 12. Scientific reporting, figures, journal target and authorship

**First-choice journal to revisit after results:** *PLOS Neglected Tropical Diseases*. Other possible matches: *BMJ Global Health*, *The Lancet Regional Health – Africa* if broad country validity and programme co-authorship are defensible. The journal, article type, word limit, figure rules, supplementary material, reference style, data availability, ethics, preprint policy and APC/Research4Life waiver rules must be **rechecked at submission date**. Author institution/location, funding and eligibility determine waivers; never promise a free publication as certain.

**Follow journal instructions to the letter after a journal is selected.** TRIPOD+AI (https://www.equator-network.org/reporting-guidelines/tripod-statement/) for prediction models where applicable, PROBAST+AI design/appraisal as relevant, and domain-specific guidance on routinely collected programme data. Report unit of prediction, eligibility, numbers at each flow step, target prevalence, year/country missingness, model specification, number of parameters, validation, all performance metrics with CIs, ethics, source versions, code status, limitations and practitioner feedback.

**Actual final paper must include appropriately numbered, authored visual and tabular artifacts:** conceptual pre-treatment decision schematic; *actual* IU eligibility/flowchart with real counts; study-country map with rights-checked geography; time-series of outcome events and missing data; baseline versus ML predictive comparison; calibration plot; top-k capture curve; temporal and country transfer analysis; uncertainty tables; ablations; SHAP interpreted cautiously. Do not invent counts, charts, legend scales or significance stars. Auto-generate each manuscript figure from the saved evaluated artifacts with fixed seeds and proper captions/alternative text.

**Manuscript link strategy:** public source repository, permanent Zenodo software/data-if-licensed DOI, public Streamlit dashboard URL (verified live), separate raw data source links. The dashboard is supplemental and does **not** replace core manuscript figures, result tables or peer-reviewable reproducibility. Freeze a tagged snapshot matching the manuscript. Citation metadata must be generated from actual authorship approvals; don't invent coauthors.

---

## 13. Testing, continuous integration and release gates

**Unit tests:** status precedence and unknown handling; duplicate and conflicting rows; year gaps; country+IU composite keys; non-report must not equal interruption; release-date cutoff; missingness behavior; feature train-fit isolation; scorer correctness on known toy labels; calibration monotonicity/sanity; `top_k` tie policy; unsupported country testing; plotting/chart serialization.

**Integration tests:** one synthetic mini-country **explicitly marked synthetic** plus one real source-country file if legally available; deterministic end-to-end auditing; schema error fails loudly; geospatial joins row-preserving; two successive clean environment runs produce same approved report/hash or acceptable deterministic-tolerance match.

**Scientific adversarial tests:** deliberately inject an outcome-year covariate, shuffle timestamps, reuse country identifiers, duplicate IU across files, invert status mapping, remove one country's records, add a JRF-missing year, perturb label prevalence, and confirm pipeline either rejects invalid input or clearly changes status. Check no naive leakage on test split.

**Dashboard tests:** launches without attempting training; pages render without private raw data; controls do what labels promise; no hypothetical result appears as empirical; link/accessibility and synthetic demo labels are visible; caching is resource-safe; handles missing model gracefully.

**Release checklist:**

```text
[ ] Raw legal downloads verified (or publicly reproducible acquisition documented)
[ ] Source manifest/checksums and exact field dictionary recorded
[ ] Outcome class mapping, eligible population and external expert label plan validated
[ ] Real events by year/country reported; model event adequacy justified
[ ] Prediction timing and data revisions documented; leakage tests pass
[ ] Baselines run; bound model choices justified; development evaluation reproducible
[ ] Frozen final test used once; evaluation scripts and uncertainties verified
[ ] All claims link to real figures/tables, model/run IDs and valid references
[ ] Restricted/nonpublic data and secrets absent from Git history and release assets
[ ] Streamlit dashboard tested against saved evaluation artifacts
[ ] README/CITATION/protocol/methods/dictionary/reports checked for consistency
[ ] Git CI green (real status), locally reproducible, no false badges
[ ] Git push/PR and release link verified, not merely commanded
[ ] Journal-specific checklist and manuscript link targets drafted, no invented acceptance
```

---

## 14. First autonomous IDE session: required action and reply format

1. Verify correct repository and inspect what already exists. Read this entire file and concept source references; create a concise action plan in `docs/STATUS.md`.
2. Confirm ESPEN source format/terms and retrieve one test country through official means; record what was *actually* accessed. Create robust loader and schema audit tests.
3. Attempt full lawful country retrieval. If the form requires user interaction, prepare a precise download checklist and validate files automatically when placed in folder. Continue synthetic **software tests only** in the meantime.
4. Run the **real** label/event/eligibility feasibility audit as soon as files exist, using immutable event tables and proper missing/legitimate-pause classes.
5. Present a scientific `GO/REDESIGN/NO-GO` with actual counts and remaining unverified expert confirmation. **STOP before model fitting if evidence does not support it.**
6. If gate passes and investigator accepts protocol choices, implement reproducible modelling, evaluation, manuscript assets and dashboard in order. Preserve locked test.
7. Push a safe, documented, tested research repository when the release checklist passes; publish/live-link dashboard after appropriate deployment checks. Do not claim the paper is accepted.

**Every session ends with this report:**

```text
REPOSITORY: Isaac25-lgtm/lf-mda-interruption-prediction
PHASE: [0..11]
SCIENTIFIC_GATE: [GO | REDESIGN_REQUIRES_APPROVAL | NO-GO | BLOCKED | NOT_YET_ASSESSED]
ACTUAL_SOURCE_DATA: [verified files, years, countries, version; or unavailable]
LABEL_COUNTS: [real counts by window; or NOT AVAILABLE]
MODELS_TRAINED: [what really ran; or NONE]
VALIDATION: [development-only or locked-test once; no invented metrics]
TESTS: [command, passed/failed count]
FILES_CHANGED: [paths]
GIT: [branch, commit, pushed URL or unpushed reason]
DASHBOARD: [local URL/public URL verified or NOT DEPLOYED]
RISKS/BLOCKERS: [items and evidence]
NEXT ACTIONS: [precise next autonomous steps]
```

**Absolute rule:** An invalid label or dataset cannot be rescued with 'better hyperparameters'. Do not confuse model complexity with publishable originality. Work to completion when scientifically possible, and stop with an evidence-backed explanation when it is not.

---

## 15. Reference and provenance register

**Scientific:** Fuller et al. 2023, DOI [10.1371/journal.pntd.0011146](https://doi.org/10.1371/journal.pntd.0011146); Ng et al. 2025, DOI [10.1093/trstmh/traf005](https://doi.org/10.1093/trstmh/traf005); Maroto-Camino et al. 2019, DOI [10.1371/journal.pntd.0007337](https://doi.org/10.1371/journal.pntd.0007337); Burgert-Brucker et al. 2020, DOI [10.1371/journal.pntd.0008301](https://doi.org/10.1371/journal.pntd.0008301); Galiwango et al. 2026, DOI [10.1038/s43856-026-01706-3](https://doi.org/10.1038/s43856-026-01706-3); WHO LF 2025 report at https://www.who.int/publications/journals/weekly-epidemiological-record/wer101-39.

**Methods and reporting:** Riley et al. 2020, [10.1136/bmj.m441](https://doi.org/10.1136/bmj.m441); Collins et al. 2016 [10.1002/sim.6787](https://doi.org/10.1002/sim.6787); Riley et al. 2021 [10.1002/sim.9025](https://doi.org/10.1002/sim.9025); calibration Van Calster et al. 2019 [10.1186/s12916-019-1466-7](https://doi.org/10.1186/s12916-019-1466-7); TRIPOD+AI [10.1136/bmj-2023-078378](https://doi.org/10.1136/bmj-2023-078378); PROBAST+AI [10.1136/bmj-2024-082505](https://doi.org/10.1136/bmj-2024-082505). Agents must recheck references before manuscript submission and distinguish unverified bibliographic details.

**Concept authority:** The companion user-provided `PUBLICATIONS_Two_Research_Concept_Papers.md`/`.docx`, Version 1.0, 12 Oct 2026, supplies extended literature and prose. This handover refines implementability and flags errors/unknowns rather than substituting invented evidence. Keep source document out of repo only if author/collaborator sharing restrictions require it; cite its research protocol where appropriate.
