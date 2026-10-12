# Derived dashboard data

Built by `lf-mda dashboard-data`. These files hold **derived** values only:

- `iu_year.parquet`: one row per implementation unit and year (2016-2025) with the
  reported status class, cohort flags, the unit's centroid, and stored out-of-sample
  risk scores. No raw ESPEN file and no boundary polygon is included.
- `country_year.csv`, `countries.csv`: country-level summaries and codes.
- `info.json`: build time, gate decision and headline counts.

## Sources and attribution

- WHO Expanded Special Project for Elimination of Neglected Tropical Diseases (ESPEN),
  lymphatic filariasis implementation-unit data, 2014-2025, accessed 12 October 2026,
  https://espen.afro.who.int. Underlying data were reported by national NTD programmes.
- Centroids derived from ESPEN's 2024 provisional implementation-unit cartography.

ESPEN states no licence on its download page. These derived files are shared for
public-health research under the reasoning in `docs/ETHICS_DATA_USE.md`. If ESPEN
advises that this is not permitted, delete this folder; the dashboard then runs in its
labelled synthetic demonstration mode.

Status values are reported administrative statuses, not verified events. Risk scores
are research outputs and must not be used to judge or fund any programme.
