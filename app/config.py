#!/usr/bin/env python3
"""
Avia Solutions QSI Auto - single source of truth for all data paths.
====================================================================
Nothing in this project hardcodes a file path. Every path the tool reads or
writes resolves through this module.

The home of the project
-----------------------
The canonical home is Egnyte at "18 Products/QSI". Everything durable lives
there: the application releases, the reference tables, the reference cases,
the documentation, the generated outputs, and the shared DuckDB snapshot.
Whatever Claude or development environment you work in is a working checkout;
Egnyte is the source of truth that survives moving between environments.

The 91GB Sabre master and the OAG schedules are shared company data and stay
in their own home at "18 Products/Data". The project reads them there; it does
not copy them into the QSI home.

Three roots
-----------
1. DATA_ROOT  - the Egnyte mount, or a local copy on the laptop build. Both the
   shared master data and the QSI home hang off it.
2. PROJECT_HOME - "18 Products/QSI" under DATA_ROOT. The project's own files.
3. LOCAL_CACHE - a fast local (non-synced) drive for the DuckDB stores. The
   store is large and write-heavy during ingest, so it is built locally and a
   read-only snapshot is published to PROJECT_HOME/"Data Store" when stable.

Two builds
----------
- shared (default): DATA_ROOT auto-detects the Egnyte mount, for team testing.
- laptop: DATA_ROOT points at a local copied-down home, for the offline demo.

Switch with AVIA_QSI_BUILD. Override any root or path with the matching
environment variable noted below. Standard library only, so it runs offline.
"""

from __future__ import annotations

import os
from pathlib import Path

# ----------------------------------------------------------------------------
# Build target
# ----------------------------------------------------------------------------
BUILD = os.environ.get("AVIA_QSI_BUILD", "shared").strip().lower()
if BUILD not in ("shared", "laptop"):
    raise ValueError(f"AVIA_QSI_BUILD must be 'shared' or 'laptop', got {BUILD!r}")

# Where this code physically runs from (the working checkout). Not a data path.
APP_DIR = Path(__file__).resolve().parent


def _env_path(var: str, default: Path) -> Path:
    value = os.environ.get(var)
    return Path(value).expanduser() if value else default


# ----------------------------------------------------------------------------
# Root 1: DATA_ROOT
# ----------------------------------------------------------------------------
# Egnyte mounts at a different drive on each machine:
#   - Home PC:        Z:/Shared/Company Data
#   - Secure laptops: P:/CompanyData
#   - Shared Teams:   P:/ (standardised)
# Rather than hardcode one, the resolver tries each candidate and picks the
# first whose "18 Products" marker folder actually exists, so the same code
# runs everywhere with no per-machine edit. AVIA_EGNYTE_ROOT overrides all.
_EGNYTE_CANDIDATES = [
    Path("Z:/Shared/Company Data"),
    Path("Z:/Shared/CompanyData"),
    Path("P:/CompanyData"),
    Path("P:/Company Data"),
    Path("P:/Shared/Company Data"),
]
_EGNYTE_MARKER = "18 Products"


def _resolve_egnyte_root() -> Path:
    """Pick the Egnyte mount present on this machine; env var wins if set."""
    override = os.environ.get("AVIA_EGNYTE_ROOT")
    if override:
        return Path(override).expanduser()
    for cand in _EGNYTE_CANDIDATES:
        if (cand / _EGNYTE_MARKER).is_dir():
            return cand
    return _EGNYTE_CANDIDATES[0]  # nominal fallback when run off-network


if BUILD == "shared":
    DATA_ROOT = _resolve_egnyte_root()
else:  # laptop
    DATA_ROOT = _env_path("AVIA_LOCAL_ROOT", APP_DIR.parent / "data_root")

# ----------------------------------------------------------------------------
# Root 2: PROJECT_HOME  (18 Products/QSI)
# ----------------------------------------------------------------------------
PROJECT_HOME = _env_path("AVIA_QSI_HOME", DATA_ROOT / "18 Products" / "QSI")

APPLICATION_DIR = _env_path("AVIA_APPLICATION_DIR", PROJECT_HOME / "Application")
REFERENCE_TABLES_DIR = _env_path("AVIA_REFERENCE_TABLES_DIR", PROJECT_HOME / "Reference Tables")
REFERENCE_CASES_DIR = _env_path("AVIA_REFERENCE_CASES_DIR", PROJECT_HOME / "Reference Cases")
REFERENCE_CASE_DIR = _env_path("AVIA_REFERENCE_CASE_DIR", REFERENCE_CASES_DIR / "BA LHR-SJC")
OUTPUT_DIR = _env_path("AVIA_OUTPUT_DIR", PROJECT_HOME / "Outputs")
DOCUMENTATION_DIR = _env_path("AVIA_DOCUMENTATION_DIR", PROJECT_HOME / "Documentation")
LAPTOP_BUILD_DIR = _env_path("AVIA_LAPTOP_BUILD_DIR", PROJECT_HOME / "Laptop Build")

# The published, read-only DuckDB snapshots live in the QSI home.
DATA_STORE_SNAPSHOT_DIR = _env_path("AVIA_DATA_STORE_SNAPSHOT_DIR", PROJECT_HOME / "Data Store")

# ----------------------------------------------------------------------------
# Root 3: LOCAL_CACHE  (fast local drive for the DuckDB stores)
# ----------------------------------------------------------------------------
LOCAL_CACHE = _env_path("AVIA_LOCAL_CACHE", Path.home() / ".avia_qsi" / "data_store")
SABRE_DUCKDB = _env_path("AVIA_SABRE_DUCKDB", LOCAL_CACHE / "sabre.duckdb")
OAG_DUCKDB = _env_path("AVIA_OAG_DUCKDB", LOCAL_CACHE / "oag.duckdb")
# US DOT stores (built from the DOT extracts; see build_db1b_store.py / load_t100.py / load_p12.py).
# Aggregated, so small; live next to sabre.duckdb.
DB1B_DUCKDB = _env_path("AVIA_DB1B_DUCKDB", LOCAL_CACHE / "db1b.duckdb")      # US domestic O&D (od_market)
T100_DUCKDB = _env_path("AVIA_T100_DUCKDB", LOCAL_CACHE / "t100.duckdb")      # US capacity/seats/LF (seg)
# ACI airport traffic, monthly, worldwide. Built by load_aci.py from the hand-
# maintained workbook on Egnyte. TOTAL THROUGHPUT: arrivals + departures +
# transit, domestic and international together. Not O&D, not one direction.
ACI_DUCKDB = _env_path("AVIA_ACI_DUCKDB", LOCAL_CACHE / "aci.duckdb")         # non-US airport traffic (aci_monthly)
FORM41_DUCKDB = _env_path("AVIA_FORM41_DUCKDB", LOCAL_CACHE / "form41_p12.duckdb")  # carrier P&L / CASM
CASM_BENCHMARK = _env_path("AVIA_CASM_BENCHMARK", LOCAL_CACHE / "casm_benchmark.duckdb")  # carrier CASM/RASM + stage

# ----------------------------------------------------------------------------
# Root 4: ASSETS  (imagery and fonts: data with a rights record, never in the repo)
# ----------------------------------------------------------------------------
# Added 8 August 2026, when the deck renderer moved into the repo as deck/ and its
# imagery libraries did not. 102MB of Observatory photography and 34MB of brand
# imagery are data, and each carries a rights determination per image, so they live
# beside the stores and are configured, not bundled. C:/assets on the Dev PC and
# D:\assets on the workstation; AVIA_ASSETS moves the root in one place.
ASSETS_DIR = _env_path("AVIA_ASSETS", Path("C:/assets"))
# 51 images plus library.json, the manifest the deck generator reads.
OBS_LIBRARY_DIR = _env_path("AVIA_OBS_LIBRARY", ASSETS_DIR / "observatory_library")
# 15 images plus rights.json, the per-image rights determination.
BRAND_LIBRARY_DIR = _env_path("AVIA_BRAND_LIBRARY", ASSETS_DIR / "brand_library")
# Per-engagement photography and the generated chart PNGs for the BA LHR-SJC and
# GOA-NYC reference decks. build_ba_sjc.py and build_goa_nyc.py need this to
# reproduce those two decks; nothing on the live path reads it.
ENGAGEMENT_ASSETS_DIR = _env_path("AVIA_ENGAGEMENT_ASSETS", ASSETS_DIR / "engagement")

# ----------------------------------------------------------------------------
# Shared master data (18 Products/Data) - read in place, never copied
# ----------------------------------------------------------------------------
SABRE_RAW_DIR = _env_path("AVIA_SABRE_RAW_DIR", DATA_ROOT / "18 Products" / "Data" / "Sabre" / "ODPOO")
OAG_RAW_DIR = _env_path("AVIA_OAG_RAW_DIR", DATA_ROOT / "18 Products" / "Data" / "OAG")

# ----------------------------------------------------------------------------
# OAG parser lookups
# ----------------------------------------------------------------------------
AIRPORT_DB = _env_path("AVIA_AIRPORT_DB", REFERENCE_TABLES_DIR / "Airport_Database.xlsx")
CITY_LOOKUP = _env_path("AVIA_CITY_LOOKUP", REFERENCE_TABLES_DIR / "OAG_Airport__City_Lookup_DS_25Feb11.xlsx")

# ----------------------------------------------------------------------------
# Connection builder lookups
# ----------------------------------------------------------------------------
# Minimum connect times. OAG no longer supplies these, so Avia owns the master.
# It changes slowly (only when airport investment improves connect times), so it
# is a maintained reference table updated by exception, not a feed.
MCT_MASTER = _env_path("AVIA_MCT_MASTER", REFERENCE_TABLES_DIR / "MCT Master List.xlsx")

# ----------------------------------------------------------------------------
# Document authorship (applied to every generated Excel, Word, PowerPoint)
# ----------------------------------------------------------------------------
DOC_AUTHOR = "Avia Solutions"

ALL_PATHS = {
    "DATA_ROOT": DATA_ROOT,
    "PROJECT_HOME": PROJECT_HOME,
    "APPLICATION_DIR": APPLICATION_DIR,
    "REFERENCE_TABLES_DIR": REFERENCE_TABLES_DIR,
    "REFERENCE_CASE_DIR": REFERENCE_CASE_DIR,
    "OUTPUT_DIR": OUTPUT_DIR,
    "DOCUMENTATION_DIR": DOCUMENTATION_DIR,
    "LAPTOP_BUILD_DIR": LAPTOP_BUILD_DIR,
    "DATA_STORE_SNAPSHOT_DIR": DATA_STORE_SNAPSHOT_DIR,
    "LOCAL_CACHE": LOCAL_CACHE,
    "SABRE_DUCKDB": SABRE_DUCKDB,
    "OAG_DUCKDB": OAG_DUCKDB,
    "DB1B_DUCKDB": DB1B_DUCKDB,
    "T100_DUCKDB": T100_DUCKDB,
    "ACI_DUCKDB": ACI_DUCKDB,
    "FORM41_DUCKDB": FORM41_DUCKDB,
    "CASM_BENCHMARK": CASM_BENCHMARK,
    "SABRE_RAW_DIR": SABRE_RAW_DIR,
    "OAG_RAW_DIR": OAG_RAW_DIR,
    "AIRPORT_DB": AIRPORT_DB,
    "CITY_LOOKUP": CITY_LOOKUP,
    "MCT_MASTER": MCT_MASTER,
}


def ensure_output_dir() -> Path:
    """Create the output folder if absent and return it."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def ensure_local_cache() -> Path:
    """Create the local DuckDB cache folder if absent and return it."""
    LOCAL_CACHE.mkdir(parents=True, exist_ok=True)
    return LOCAL_CACHE


def describe() -> str:
    lines = [f"Avia QSI config  |  build = {BUILD}", f"  APP_DIR (checkout) = {APP_DIR}"]
    for name, path in ALL_PATHS.items():
        lines.append(f"  {name} = {path}")
    return "\n".join(lines)


def check_exists() -> dict:
    return {name: path.exists() for name, path in ALL_PATHS.items()}


if __name__ == "__main__":
    print(describe())
    print("\nPresent on this machine:")
    for name, present in check_exists().items():
        print(f"  [{'x' if present else ' '}] {name}")
