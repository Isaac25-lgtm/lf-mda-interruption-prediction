# Ethics and data use

## Nature of the data

All data are secondary, aggregate, programme-level records about administrative units.
There are no records about individual people, so there is no personal or
person-identifying data. No ethics approval has been sought. Whether a journal or the
researcher's institution requires a formal exemption letter is **not yet checked** and
must be confirmed before submission.

## Sources and what their terms say

| Source | Access (verified 2026-10-12) | Stated terms | How this repository treats it |
|---|---|---|---|
| WHO ESPEN LF IU-level data, 2014-2025 | Public download form; no login, key, registration or terms click-through | The download page and the ESPEN disclaimer state **no licence and no reuse terms**. | Raw files are not committed. `lf-mda download` re-fetches them. |
| WHO general dataset terms (`who.int/about/policies/publishing/data-policy/terms-and-conditions`) | Public page | Royalty-free right to "use, reproduce, extract, download, copy, distribute" datasets and include them in other products for public-health purposes; attribution to WHO and the countries required; no commercial promotion; no sale. | Applied by analogy. **It is not confirmed that these terms govern the ESPEN portal.** |
| ESPEN IU geometry (2024 provisional cartography) | Public map endpoint used by ESPEN's own pages | None stated | Used only to derive IU centroids, areas and point-in-polygon joins. Polygons are not committed. |
| UCDP Georeferenced Event Dataset 26.1 | Open download | "All datasets are free of charge and licensed under CC BY 4.0", with citation | Raw archive not committed; only derived counts are used. |

## Open point for the researcher

A small derived table (`dashboard/data/`) holding IU names, status class, centroid and
stored risk scores is committed so the public dashboard can run. This is a
redistribution of derived ESPEN content under terms ESPEN has not stated. If ESPEN
advises that this is not permitted, delete `dashboard/data/` from the repository and
its history; the dashboard then shows only aggregate results.

## Attribution to use

> WHO Expanded Special Project for Elimination of Neglected Tropical Diseases (ESPEN).
> Lymphatic filariasis implementation-unit level data, 2014-2025. Accessed 12 October
> 2026 from https://espen.afro.who.int. Underlying data were reported by national NTD
> programmes of the countries listed in `data/manifests/espen_sources.csv`.

> Davies S, Pettersson T, Öberg M. Organized violence 1989-2025, and violent political
> protests. Journal of Peace Research, 2026. https://doi.org/10.1093/jopres/xjag046
>
> Sundberg R, Melander E. Introducing the UCDP Georeferenced Event Dataset. Journal of
> Peace Research 2013;50(4).

These are the citations the UCDP download page lists for GED 26.1 (read 2026-10-12).
The page states "All datasets are free of charge and licensed under CC BY 4.0."

## Risk of harm from the outputs

- A risk ranking of districts could be misread as a judgement of programme staff or
  used to withdraw support. The stated purpose is to direct extra supervision.
- The label is unverified, so individual IU "risk" values may be wrong for reasons
  that have nothing to do with the programme (reporting, legitimate pauses).
- Most of the signal is at country level. Presenting district rankings as precise
  would overstate what the data support.

The dashboard therefore carries a retrospective research-only label on every page,
shows the validation uncertainty next to any ranking, and explains what "risk" means.

## What has not been done

- No collaborator, ministry or WHO office has reviewed or endorsed this work.
- No expert review of the labels has taken place.
- No request for non-public data has been made, by the researcher's decision.
