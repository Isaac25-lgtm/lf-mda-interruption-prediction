# Data

Nothing in `data/raw/` or `data/processed/` is committed. Both are rebuilt by code.

| Folder | Contents | In Git |
|---|---|---|
| `raw/espen_lf/` | 48 country CSV files exactly as served by ESPEN | No |
| `raw/context/espen_iu_geometry/` | IU geometry JSON from ESPEN's public map endpoint | No |
| `raw/context/ucdp/` | UCDP GED 26.1 archive | No |
| `manifests/` | URL, retrieval time, size and SHA-256 of every downloaded file | Yes |
| `processed/` | IU-year panel, context tables, stored predictions | No |

## Getting the data

```bash
lf-mda download     # ESPEN LF IU-level extracts, all countries, 2014-2025 (about 6 minutes)
lf-mda context      # IU geometry and UCDP conflict events
lf-mda audit        # builds the panel and runs the label gate
```

`lf-mda download` calls the same unauthenticated endpoint as the public form at
https://espen.afro.who.int/maps-data/data-query-tools/download-data, one country at a
time with a three-second pause. It keeps existing files and checks them against the
manifest. If ESPEN changes the form, download each country by hand (disease:
Lymphatic filariasis, level: IU, 2014 to 2025) and save the file as
`data/raw/espen_lf/espen_lf_iu_<ISO2>_2014_2025.csv`; the loader validates the schema.

ESPEN revises its database. A later download can differ from the one analysed here;
the manifest checksums identify the exact files behind the reported results
(retrieved 12 October 2026).

## Rights

ESPEN states no licence on its download page. See `docs/ETHICS_DATA_USE.md`. The MIT
licence of this repository covers code only.
