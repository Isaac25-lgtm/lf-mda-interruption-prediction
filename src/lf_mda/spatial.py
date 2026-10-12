"""Contextual (non-ESPEN-treatment) data: IU geometry and UCDP conflict events.

Only fetched after the label gate. Geometry comes from the public ESPEN map endpoint
(`/api/coendemicity/{country}/{year}`, listed in the site's own public route table) and
is used solely to derive IU centroids, areas and point-in-polygon joins. Boundary
polygons are never committed. Conflict events come from the UCDP Georeferenced Event
Dataset (open download, CC BY 4.0).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from . import paths
from .ingest import USER_AGENT, load_sources

GEO_DIR = paths.ROOT / "data" / "raw" / "context" / "espen_iu_geometry"
UCDP_DIR = paths.ROOT / "data" / "raw" / "context" / "ucdp"
GEO_YEAR = 2024
GEO_PATH = "/api/coendemicity/{country}/{year}"
UCDP_VERSION = "26.1"
UCDP_URL = "https://ucdp.uu.se/downloads/ged/ged261-csv.zip"
# UCDP GED for calendar year y is published around June of y+1, so at a decision cutoff
# of 31 December t-1 the latest complete, final year is t-2.
UCDP_MIN_LAG = 2

CONTEXT_MANIFEST = paths.MANIFESTS / "context_sources.csv"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_manifest(rows: list[dict]) -> None:
    CONTEXT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    new = pd.DataFrame(rows)
    if CONTEXT_MANIFEST.exists():
        old = pd.read_csv(CONTEXT_MANIFEST, dtype=str, keep_default_na=False)
        old = old[~old["local_filename"].isin(new["local_filename"].astype(str))]
        new = pd.concat([old, new.astype(str)], ignore_index=True)
    new.to_csv(CONTEXT_MANIFEST, index=False)


def download_geometry(force: bool = False) -> None:
    src = load_sources()
    GEO_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    rows = []
    for entry in src["countries"]:
        iso2 = entry["iso2"]
        target = GEO_DIR / f"espen_iu_geometry_{iso2}_{GEO_YEAR}.json"
        if target.exists() and not force:
            continue
        url = src["base_url"] + GEO_PATH.format(country=iso2, year=GEO_YEAR)
        row = {"source": "espen_iu_geometry", "country_iso2": iso2, "url": url,
               "retrieved_utc": _now(), "local_filename": target.name, "http_status": "",
               "bytes": "", "sha256": "", "status": "", "note": ""}
        try:
            resp = session.get(url, timeout=180)
            row["http_status"] = resp.status_code
            if resp.status_code == 200 and "json" in resp.headers.get("Content-Type", ""):
                target.write_bytes(resp.content)
                n = len(resp.json().get("geojson", {}).get("features", []))
                row.update(bytes=len(resp.content), sha256=_sha(resp.content), status="ok",
                           note=f"{n} features")
            else:
                row.update(status="error", note="unexpected response")
        except requests.RequestException as exc:
            row.update(status="error", note=f"{type(exc).__name__}: {exc}"[:200])
        print(iso2, row["status"], row["note"], flush=True)
        rows.append(row)
        time.sleep(float(src.get("request_delay_seconds", 3)))
    if rows:
        _write_manifest(rows)


def download_ucdp(force: bool = False, max_attempts: int = 30) -> Path:
    """Download the UCDP GED archive, resuming with HTTP Range if the connection drops."""
    UCDP_DIR.mkdir(parents=True, exist_ok=True)
    target = UCDP_DIR / "ged261-csv.zip"
    if target.exists() and not force:
        return target
    part = UCDP_DIR / "ged261-csv.zip.part"
    headers = {"User-Agent": USER_AGENT}
    total = int(requests.head(UCDP_URL, headers=headers, timeout=60).headers["Content-Length"])
    last_modified = ""
    for _ in range(max_attempts):
        have = part.stat().st_size if part.exists() else 0
        if have >= total:
            break
        try:
            with requests.get(UCDP_URL, headers=headers | {"Range": f"bytes={have}-"},
                              stream=True, timeout=60) as resp:
                resp.raise_for_status()
                last_modified = resp.headers.get("Last-Modified", last_modified)
                with open(part, "ab" if resp.status_code == 206 else "wb") as fh:
                    fh.writelines(resp.iter_content(1 << 16))
        except requests.RequestException:
            time.sleep(3)
    if part.stat().st_size != total:
        raise RuntimeError(f"UCDP download incomplete: {part.stat().st_size} of {total} bytes")
    with zipfile.ZipFile(part) as zf:
        if zf.testzip() is not None:
            raise RuntimeError("UCDP archive failed its integrity check")
    part.replace(target)
    data = target.read_bytes()
    _write_manifest([{"source": f"ucdp_ged_{UCDP_VERSION}", "country_iso2": "", "url": UCDP_URL,
                      "retrieved_utc": _now(), "local_filename": target.name,
                      "http_status": 200, "bytes": len(data), "sha256": _sha(data),
                      "status": "ok", "note": last_modified}])
    return target


def _ring_area_centroid(ring: list) -> tuple[float, float, float]:
    """Signed planar area and centroid of one ring in lon/lat degrees."""
    a = np.asarray(ring, dtype=float)[:, :2]
    x, y = a[:, 0], a[:, 1]
    x1, y1 = np.roll(x, -1), np.roll(y, -1)
    cross = x * y1 - x1 * y
    area = cross.sum() / 2.0
    if abs(area) < 1e-14:
        return 0.0, float(x.mean()), float(y.mean())
    cx = ((x + x1) * cross).sum() / (6.0 * area)
    cy = ((y + y1) * cross).sum() / (6.0 * area)
    return float(area), float(cx), float(cy)


def geometry_summary(geom: dict) -> tuple[float, float, float]:
    """Return (lon, lat, area_km2) of a GeoJSON Polygon/MultiPolygon.

    Area uses a local equal-area approximation (degrees scaled by cos(latitude)), which
    is adequate for ranking IUs by size and density; it is not a survey-grade area.
    """
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    tot = sx = sy = 0.0
    for poly in polys:
        for i, ring in enumerate(poly):
            area, cx, cy = _ring_area_centroid(ring)
            area = abs(area) * (1 if i == 0 else -1)  # holes subtract
            tot += area
            sx += cx * area
            sy += cy * area
    if tot <= 0:
        pts = np.asarray(polys[0][0], dtype=float)
        return float(pts[:, 0].mean()), float(pts[:, 1].mean()), float("nan")
    lon, lat = sx / tot, sy / tot
    km2 = tot * (111.32 ** 2) * np.cos(np.radians(lat))
    return lon, lat, float(km2)


def _point_in_ring(px: np.ndarray, py: np.ndarray, ring: np.ndarray) -> np.ndarray:
    x, y = ring[:, 0], ring[:, 1]
    inside = np.zeros(px.shape, dtype=bool)
    j = len(x) - 1
    for i in range(len(x)):
        cond = (y[i] > py) != (y[j] > py)
        with np.errstate(divide="ignore", invalid="ignore"):
            xint = (x[j] - x[i]) * (py - y[i]) / (y[j] - y[i]) + x[i]
        inside ^= cond & (px < xint)
        j = i
    return inside


def points_in_geometry(px: np.ndarray, py: np.ndarray, geom: dict) -> np.ndarray:
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    out = np.zeros(px.shape, dtype=bool)
    for poly in polys:
        hit = _point_in_ring(px, py, np.asarray(poly[0], dtype=float)[:, :2])
        for hole in poly[1:]:
            hit &= ~_point_in_ring(px, py, np.asarray(hole, dtype=float)[:, :2])
        out |= hit
    return out


def _feature_iu_id(props: dict) -> int | None:
    for key in ("IU_ID", "iu_id", "IUs_ID", "iuID", "iuId"):
        if key in props and props[key] not in (None, ""):
            return int(props[key])
    return None


def load_geometries() -> list[dict]:
    feats = []
    for f in sorted(GEO_DIR.glob("espen_iu_geometry_*.json")):
        iso2 = f.name.split("_")[3]
        data = json.loads(f.read_text(encoding="utf-8"))
        for feat in data.get("geojson", {}).get("features", []):
            iu = _feature_iu_id(feat.get("properties", {}))
            if iu is None or not feat.get("geometry"):
                continue
            feats.append({"iso2": iso2, "iu_id": iu, "geometry": feat["geometry"]})
    return feats


def build_iu_geo_table() -> pd.DataFrame:
    rows = []
    for feat in load_geometries():
        lon, lat, km2 = geometry_summary(feat["geometry"])
        rows.append({"iso2": feat["iso2"], "iu_id": feat["iu_id"], "lon": lon, "lat": lat,
                     "area_km2": km2})
    geo = pd.DataFrame(rows).drop_duplicates(["iso2", "iu_id"])
    return geo


def load_ucdp() -> pd.DataFrame:
    target = UCDP_DIR / "ged261-csv.zip"
    with zipfile.ZipFile(target) as zf:
        name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        raw = zf.read(name)
    cols = ["id", "year", "type_of_violence", "where_prec", "latitude", "longitude",
            "country", "country_id", "region", "best"]
    ged = pd.read_csv(io.BytesIO(raw), usecols=cols, low_memory=False)
    return ged[ged["region"] == "Africa"].reset_index(drop=True)


# UCDP country names -> ESPEN ISO2 (ZZ = Zanzibar is handled spatially, inside Tanzania).
UCDP_COUNTRY_TO_ISO2 = {
    "Algeria": "DZ", "Angola": "AO", "Benin": "BJ", "Botswana": "BW", "Burkina Faso": "BF",
    "Burundi": "BI", "Cameroon": "CM", "Cape Verde": "CV", "Central African Republic": "CF",
    "Chad": "TD", "Comoros": "KM", "Ivory Coast": "CI", "DR Congo (Zaire)": "CD",
    "Equatorial Guinea": "GQ", "Eritrea": "ER", "Kingdom of eSwatini (Swaziland)": "SZ",
    "Ethiopia": "ET", "Gabon": "GA", "Ghana": "GH", "Guinea": "GN", "Guinea-Bissau": "GW",
    "Kenya": "KE", "Lesotho": "LS", "Liberia": "LR", "Madagascar (Malagasy)": "MG",
    "Malawi": "MW", "Mali": "ML", "Mauritania": "MR", "Mauritius": "MU", "Mozambique": "MZ",
    "Namibia": "NA", "Niger": "NE", "Nigeria": "NG", "Congo": "CG", "Rwanda": "RW",
    "Senegal": "SN", "Sierra Leone": "SL", "South Africa": "ZA", "South Sudan": "SS",
    "Tanzania": "TZ", "Gambia": "GM", "Togo": "TG", "Uganda": "UG", "Zambia": "ZM",
    "Zimbabwe (Rhodesia)": "ZW",
}


def build_conflict_tables() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """IU-year and country-year conflict counts from UCDP GED.

    IU-year counts use point-in-polygon on events located to at least second-order
    administrative precision (where_prec <= 4); less precise events contribute to the
    country-year totals only.
    """
    ged = load_ucdp()
    ged["iso2"] = ged["country"].map(UCDP_COUNTRY_TO_ISO2)
    unmapped = sorted(ged.loc[ged["iso2"].isna(), "country"].unique())
    ged = ged.dropna(subset=["iso2"])
    ctry = (ged.groupby(["iso2", "year"])
            .agg(ctry_conflict_events=("id", "size"), ctry_conflict_deaths=("best", "sum"))
            .reset_index())
    precise = ged[ged["where_prec"] <= 4]
    feats = load_geometries()
    by_country: dict[str, list[dict]] = {}
    for feat in feats:
        # Zanzibar polygons sit inside UCDP's "Tanzania"
        by_country.setdefault("TZ" if feat["iso2"] == "ZZ" else feat["iso2"], []).append(feat)
    rows = []
    for iso2, group in precise.groupby("iso2"):
        px, py = group["longitude"].to_numpy(float), group["latitude"].to_numpy(float)
        yrs, deaths = group["year"].to_numpy(), group["best"].to_numpy(float)
        for feat in by_country.get(iso2, []):
            ring = np.asarray(
                (feat["geometry"]["coordinates"][0][0] if feat["geometry"]["type"] ==
                 "MultiPolygon" else feat["geometry"]["coordinates"][0]), dtype=float)
            # cheap bounding-box prefilter over all parts
            allpts = _all_points(feat["geometry"])
            box = ((px >= allpts[:, 0].min()) & (px <= allpts[:, 0].max()) &
                   (py >= allpts[:, 1].min()) & (py <= allpts[:, 1].max()))
            if not box.any():
                continue
            hit = np.zeros(px.shape, dtype=bool)
            hit[box] = points_in_geometry(px[box], py[box], feat["geometry"])
            del ring
            if hit.any():
                agg = pd.DataFrame({"year": yrs[hit], "d": deaths[hit]}).groupby("year").agg(
                    iu_conflict_events=("d", "size"), iu_conflict_deaths=("d", "sum"))
                for yr, r in agg.iterrows():
                    rows.append({"iso2": feat["iso2"], "iu_id": feat["iu_id"], "year": int(yr),
                                 "iu_conflict_events": int(r.iu_conflict_events),
                                 "iu_conflict_deaths": float(r.iu_conflict_deaths)})
    iu = pd.DataFrame(rows, columns=["iso2", "iu_id", "year", "iu_conflict_events",
                                     "iu_conflict_deaths"])
    info = {"ucdp_version": UCDP_VERSION, "n_events_africa": len(ged),
            "n_events_precise": len(precise), "unmapped_countries": unmapped,
            "max_year": int(ged["year"].max())}
    return iu, ctry, info


def _all_points(geom: dict) -> np.ndarray:
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return np.concatenate([np.asarray(p[0], dtype=float)[:, :2] for p in polys])


def build_context(out_dir: Path | None = None) -> dict:
    out_dir = out_dir or paths.PROCESSED
    out_dir.mkdir(parents=True, exist_ok=True)
    geo = build_iu_geo_table()
    geo.to_parquet(out_dir / "iu_geo.parquet", index=False)
    iu, ctry, info = build_conflict_tables()
    iu.to_parquet(out_dir / "conflict_iu_year.parquet", index=False)
    ctry.to_parquet(out_dir / "conflict_country_year.parquet", index=False)
    info["n_iu_with_geometry"] = len(geo)
    (out_dir / "context_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    return info


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Fetch and build contextual data")
    ap.add_argument("step", choices=["download", "build", "all"])
    args = ap.parse_args(argv)
    if args.step in ("download", "all"):
        download_geometry()
        download_ucdp()
    if args.step in ("build", "all"):
        print(json.dumps(build_context(), indent=2))


if __name__ == "__main__":
    main()
