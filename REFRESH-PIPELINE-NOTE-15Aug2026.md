# Data refresh pipeline: the facts on the ground, 15 August 2026

For the September build session. Established by reading Jess's actual Egnyte folders
this session, not assumed. John's plan: Jess downloads to Egnyte, the workstation picks
up and ingests unwatched (September holiday test), OAG API later removes the manual step.

## Where the downloads live

- OAG monthly regional runs: `/Shared/Company Data/18 Products/QSI/Data Store/`
  (folder id e7f479f5-329d-4e8a-9db9-223ea2196aa8). 628 files as of 15 August plus an
  `old/` subfolder the loader must NOT descend into for current work.
- Sabre annual world extracts: `/Shared/Company Data/18 Products/Data/Sabre/ODPOO/`
  (folder id 43639896-1747-45fc-b347-9a60f74ed389). Also holds Jess's extraction
  scripts (`Data Extraction*.py`) and `Sabre_header_check.txt`, the field template the
  format validator should be built against.
- `/Shared/Company Data/18 Products/Data/OAG/` exists and is EMPTY. Either adopt it as
  the pickup folder for new OAG drops or ignore it; decide with Jess, do not guess.

## Naming, as it actually is

- OAG monthly: `<Region> <Mon> <YYYY>.xlsx`, e.g. `Africa Apr 2024.xlsx`. Seven
  regions; circa 45-57MB each. Years present: 2015-2019 and 2023-2025.
  TOLERANCE REQUIRED: spelling varies ("Latin America" and "Latin america", "MiddlE
  East" and "Middle East"). Canonicalise case-folded; never fail an ingest on case.
- OAG half-month: `<Region> 01Apr to 15Apr <YYYY>.xlsx`. These belong to the
  half-year union spine (AVIA_BT2_HALFYEAR) and must be routed there or skipped,
  NEVER ingested onto the monthly label spine.
- Sabre annual: `World<YYYY><variant>-1av002013-235-<timestamp>.csv`, 5-7.6GB.
  The variant token is inconsistent (POO, NDPOO, Poo, PooND, POOND): parse the YEAR,
  ignore the variant. 2013-2019 and 2021-2024 present in the folder; no 2020 file
  (never extracted) and the 2025 file is not in the folder (already ingested to E:).

## Rules the pickup job must carry (each earned, not cautious)

1. Manifest per source: name, checksum, label, row count. Re-run cannot double-load
   (the T-100 double-load scar); a re-arrived label is a deliberate drop-and-reload
   (`oag_drop_period.py`), never a second copy.
2. Format refusal against the agreed template (`Sabre_header_check.txt` for Sabre;
   OAG field selection workbook for OAG). Wrong columns refuse loudly. The
   capacity-versus-schedule export trap lives here.
3. THE VINTAGE GUARD (load-bearing): the engine takes max(source_year) as its base
   year. A partial-year Sabre file must land under a monthly/partial label and NEVER
   advance the annual vintage until the year is complete. `sabre_years.check()` is
   the checking half; the ingest rule is the other half.
4. Validate after every ingest (`validate_oag_load.py`) and write a status line
   (source, label, rows, pass/fail, date) surfaced on the /watch page as store
   freshness. September's unwatched test is only a test if failure is visible:
   Jess glances at that line after each upload.
5. DuckDB single-writer: bracket ingest with portal stop/start and call
   `db_registry.reset()` on restart (closes the 6 July S16 item).
6. Egnyte drive quirk: use listdir-style walks (`oag_ingest_periodic.py` line 133
   comment) and agree the folder layout with Jess before coding the walk.

## Cadence (corrected 15 August)

OAG monthly regional (what Jess already produces; weekly only when the OAG API
arrives). Sabre monthly WANTED for seasonality but the extraction template does not
exist yet: design it with Jess, and the vintage guard ships BEFORE the first monthly
file. T-100 monthly (2-3 months lag). DB1B quarterly (4-6 months lag).

## Already done in code (this session)

`route_watch.py` reads weekly labels where an airport has them and falls back to the
monthly spine, per-airport, so the Watch page works against Jess's monthly template
as it stands. Known-answer tested both forms.

## Commissioning plan

Catch up all sources to end July WATCHED (fix what trips), then the September
unwatched month, verdict when John returns.

Avia Solutions Limited. All rights reserved.
