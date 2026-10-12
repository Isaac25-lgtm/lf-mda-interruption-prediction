"""Repository-relative paths used across the pipeline."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"
RAW_ESPEN = ROOT / "data" / "raw" / "espen_lf"
MANIFESTS = ROOT / "data" / "manifests"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
AUDIT = REPORTS / "audit"
FIGURES = REPORTS / "figures"
TABLES = REPORTS / "tables"
EVALUATION = REPORTS / "evaluation"
RUNS = REPORTS / "runs"
MODELS = ROOT / "models"
