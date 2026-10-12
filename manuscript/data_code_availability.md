# Data and code availability (draft statement)

**Code.** All code, configuration, audit tables, evaluation tables and figures are at
https://github.com/Isaac25-lgtm/lf-mda-interruption-prediction (MIT licence for code).
The tagged release matching the manuscript and a Zenodo DOI are **not yet created**.

**Data.** The study uses only openly accessible secondary data:

- WHO ESPEN lymphatic filariasis implementation-unit data, 2014-2025, downloaded on
  12 October 2026 from https://espen.afro.who.int/maps-data/data-query-tools/download-data.
  The raw files are not redistributed. `lf-mda download` retrieves them, and
  `data/manifests/espen_sources.csv` lists the SHA-256 checksum of each file analysed.
  ESPEN revises its database, so a later download may differ.
- UCDP Georeferenced Event Dataset version 26.1 (CC BY 4.0), https://ucdp.uu.se/downloads/.
- ESPEN implementation-unit geometry (2024 provisional cartography), used only to derive
  centroids, areas and spatial joins.

**Dashboard.** A Streamlit dashboard reading the stored results is in `dashboard/`. A
public URL will be added here once it has been deployed and checked. The dashboard is
supplementary and does not replace the tables and figures in the paper.

**Ethics.** Only aggregate programme data about administrative units were used; no
individual-level data. Whether a formal exemption is required has not yet been confirmed.

**Before submission, check:** the journal's data-availability wording, whether ESPEN
permits the derived implementation-unit table in `dashboard/data/` to be public, and the
exact UCDP citation for version 26.1.
