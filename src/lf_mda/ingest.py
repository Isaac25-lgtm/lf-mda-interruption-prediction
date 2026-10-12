"""Acquire and load WHO ESPEN lymphatic filariasis IU-level extracts.

Downloads use the same unauthenticated endpoint that the public ESPEN "Download data"
form calls (see config/data_sources.yaml). Files are written byte-for-byte as served
and described in a manifest with SHA-256 checksums. Nothing here fabricates data: a
failed or empty download is recorded as such.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import yaml

from . import paths

USER_AGENT = "lf-mda-interruption-prediction research (github.com/Isaac25-lgtm)"

MANIFEST_COLUMNS = [
    "country_iso2", "country_name", "url", "http_status", "retrieved_utc",
    "server_filename", "local_filename", "bytes", "sha256", "n_rows", "n_cols",
    "status", "note",
]

# Schema of the 2014-2025 LF IU extract as actually served on 2026-10-12.
# The header is NOT identical across countries: `admin2` is absent for countries whose
# IUs sit at ADM1 (DZ, LR, LS), and `admin3` / `altAdmin2` appear only for some
# countries. These three are therefore optional; every other column is required.
OPTIONAL_COLUMNS = ["admin2", "admin3", "altAdmin2"]
REQUIRED_COLUMNS = [
    "id", "continent", "region", "whoRegion", "admin0", "admin0Id", "admin0Fip",
    "admin0Iso2", "admin0Iso3", "admin1", "admin1Id", "admin2Id", "admin3Id",
    "iusAdm", "iusName", "iuId", "iuCode", "year", "endemicity", "popReq", "popTrg",
    "popTreat", "cov", "epiCov", "mdaScheme", "endemicityId", "popTot", "popPreSAC",
    "popSAC", "popAdult", "cumMda", "mda", "effMda", "mdaN", "effMdaN", "epiMda",
    "epiEffMda", "epiMdaN", "epiEffMdaN",
]

NUMERIC_COLUMNS = [
    "year", "popReq", "popTrg", "popTreat", "cov", "epiCov", "endemicityId", "popTot",
    "popPreSAC", "popSAC", "popAdult", "cumMda", "mda", "effMda", "mdaN", "effMdaN",
    "epiMda", "epiEffMda", "epiMdaN", "epiEffMdaN",
]


class SchemaError(ValueError):
    """Raised when a raw file does not match the expected ESPEN LF schema."""


def load_sources(config_path: Path | None = None) -> dict:
    path = config_path or paths.CONFIG / "data_sources.yaml"
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)["espen_lf"]


def local_name(iso2: str, from_year: int, to_year: int) -> str:
    return f"espen_lf_iu_{iso2}_{from_year}_{to_year}.csv"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _count_rows(data: bytes) -> tuple[int, int]:
    text = data.decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return 0, 0
    return len(rows) - 1, len(rows[0])


def download_country(src: dict, iso2: str, name: str, out_dir: Path,
                     session: requests.Session, force: bool = False) -> dict:
    """Download one country extract and return its manifest row."""
    url = src["base_url"] + src["path_template"].format(
        country=iso2, disease=src["disease"], level=src["level"],
        from_year=src["from_year"], to_year=src["to_year"])
    fname = local_name(iso2, src["from_year"], src["to_year"])
    target = out_dir / fname
    row = dict.fromkeys(MANIFEST_COLUMNS, "")
    row.update(country_iso2=iso2, country_name=name, url=url, local_filename=fname)
    if target.exists() and not force:
        data = target.read_bytes()
        n_rows, n_cols = _count_rows(data)
        row.update(status="kept_existing", bytes=len(data), sha256=sha256_bytes(data),
                   n_rows=n_rows, n_cols=n_cols, note="file already present; not re-downloaded")
        return row
    try:
        resp = session.get(url, timeout=180)
    except requests.RequestException as exc:  # network failure is recorded, not hidden
        row.update(status="error", note=f"{type(exc).__name__}: {exc}"[:300])
        return row
    row["http_status"] = resp.status_code
    row["retrieved_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    disp = resp.headers.get("Content-Disposition", "")
    if "filename=" in disp:
        row["server_filename"] = disp.split("filename=")[1].split(";")[0].strip('"')
    ctype = resp.headers.get("Content-Type", "")
    if resp.status_code != 200 or "csv" not in ctype:
        row.update(status="error", note=f"unexpected response; content-type={ctype}"[:300])
        return row
    data = resp.content
    n_rows, n_cols = _count_rows(data)
    target.write_bytes(data)
    row.update(bytes=len(data), sha256=sha256_bytes(data), n_rows=n_rows, n_cols=n_cols,
               status="ok" if n_rows > 0 else "empty",
               note="" if n_rows > 0 else "header only or no rows returned")
    return row


def download_all(out_dir: Path | None = None, manifest_path: Path | None = None,
                 countries: list[str] | None = None, force: bool = False) -> pd.DataFrame:
    src = load_sources()
    out_dir = out_dir or paths.RAW_ESPEN
    manifest_path = manifest_path or paths.MANIFESTS / "espen_sources.csv"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    previous = {}
    if manifest_path.exists():
        prev = pd.read_csv(manifest_path, dtype=str, keep_default_na=False)
        previous = {r["country_iso2"]: r for r in prev.to_dict("records")}
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    rows = []
    for entry in src["countries"]:
        iso2, name = entry["iso2"], entry["name"]
        if countries and iso2 not in countries:
            if iso2 in previous:
                rows.append(previous[iso2])
            continue
        row = download_country(src, iso2, name, out_dir, session, force=force)
        if row["status"] == "kept_existing" and iso2 in previous:
            # keep the original retrieval record, but re-verify the checksum
            old = dict(previous[iso2])
            if old.get("sha256") and old["sha256"] != row["sha256"]:
                old.update(status="checksum_mismatch",
                           note="local file differs from manifest checksum")
            row = old
        else:
            time.sleep(float(src.get("request_delay_seconds", 3)))
        print(f"{iso2} {row['status']} rows={row['n_rows']}", flush=True)
        rows.append(row)
    manifest = pd.DataFrame(rows, columns=MANIFEST_COLUMNS)
    manifest.to_csv(manifest_path, index=False)
    return manifest


def read_raw_file(path: Path) -> pd.DataFrame:
    """Read one raw extract with every field as text, so nothing is coerced silently."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    extra = [c for c in df.columns if c not in REQUIRED_COLUMNS + OPTIONAL_COLUMNS]
    if missing or extra:
        raise SchemaError(f"{path.name}: missing required columns {missing}; "
                          f"unrecognised columns {extra}")
    df["schema_optional_present"] = ",".join(c for c in OPTIONAL_COLUMNS if c in df.columns)
    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df["source_file"] = path.name
    return df


def load_raw(raw_dir: Path | None = None) -> pd.DataFrame:
    """Concatenate all raw country extracts (text-typed)."""
    raw_dir = raw_dir or paths.RAW_ESPEN
    files = sorted(raw_dir.glob("espen_lf_iu_*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No ESPEN LF extracts in {raw_dir}. Run `python -m lf_mda.cli download`.")
    frames = []
    for f in files:
        df = read_raw_file(f)
        if len(df):
            frames.append(df)
    return pd.concat(frames, ignore_index=True)


def coerce_numeric(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convert numeric fields, reporting blanks and unparseable values per column.

    Blank strings become NaN (never zero). Returns (typed frame, diagnostics table).
    """
    df = raw.copy()
    diag = []
    for col in NUMERIC_COLUMNS:
        text = df[col].astype(str).str.strip()
        blank = text.eq("") | text.str.lower().isin(["null", "na", "nan", "none"])
        num = pd.to_numeric(text.where(~blank), errors="coerce")
        bad = num.isna() & ~blank
        diag.append({"column": col, "n": len(df), "n_blank": int(blank.sum()),
                     "n_unparseable": int(bad.sum()),
                     "examples_unparseable": "; ".join(sorted(text[bad].unique())[:5]),
                     "n_zero": int((num == 0).sum()), "n_negative": int((num < 0).sum()),
                     "min": num.min(), "max": num.max()})
        df[col] = num
    for col in ["endemicity", "mdaScheme", "admin0", "admin1", "admin2", "iusName", "iuCode"]:
        df[col] = df[col].astype(str).str.strip()
    return df, pd.DataFrame(diag)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Download ESPEN LF IU-level extracts")
    ap.add_argument("--countries", nargs="*", help="ISO2 codes (default: all)")
    ap.add_argument("--force", action="store_true", help="re-download existing files")
    args = ap.parse_args(argv)
    manifest = download_all(countries=args.countries, force=args.force)
    print(manifest["status"].value_counts().to_string())


if __name__ == "__main__":
    main()
