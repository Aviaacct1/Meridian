# Upload checklist - what to put where

This lists what the Cowork project needs, what to copy in, and what to leave on Egnyte and point at. Check the paths against your own setup before the first session, since folder names can move.

## In the Cowork project folder itself

Copy these in, so Cowork has them locally:

- The `app` folder from this pack. The runnable POC, entry point `avia_qsi_auto_v3.py`.
- All five documents from this pack (`00` to `04`). Cowork reads them to get context.

That is everything code-side. The POC is self-contained once `pip install -r app/requirements.txt` has run.

## On Egnyte, to point at (do not copy 91GB into Cowork)

### Sabre master data
Location: `Shared/Company Data/18 Products/Data/Sabre/ODPOO/`

Twelve uncompressed CSV files, one per year, covering 2013 to 2025 (2020 and 2021 are combined into one file; 2025 is a "Best" part-year cut). Each is circa 7GB. The config file points the data layer at this folder. Do not download these into Cowork; the ingest reads them from the Egnyte-mounted drive.

Housekeeping: an earlier duplicate set exists under `Shared/Company Data/07 Current Projects/Development/Sabre/ODPOO/`. Settle 18 Products as the one home and clear the Development copy, so 91GB does not live in two places.

### Reference case: BA London Heathrow to San Jose (the known-answer route)
Location: `Shared/Company Data/07 Current Projects/San Jose - Route Development/Target Airlines/British Airways/Mar 2015/QSI Forecast/`

This folder holds a complete forecast with all four pieces. Copy the folder into the Cowork project (it is small), because it is the acceptance-test material for phase 2:

- QSI capture model: `QSI/@LHR/QSI@LHR v1 (OS JZ) 17Feb15.xlsx` (this is the exact file the POC regression test names), with the connection-leg workbooks `Cnx Leg1.1 Leg2.1.xlsm` and `Cnx Leg1.2 Leg2.2.xlsm` alongside.
- Analyst input data, in `DATA/`: the SABRE, OAG and FARES subfolders, `LHR MCTs.xls`, and the hand-pulled demand extract `SFO&LAX&SAN - LHR - pax by class BA.xlsx`.
- Forecast model: `BA Fcst LHR-SJC v2 (JZ OS) 03Mar15.xlsm`.
- Analyst output: `Unconstrained outputs LHR-SJC sent to BA.xlsx` (the 129,162 figure).

One thing to note from this case: the demand extract is keyed "SFO & LAX & SAN to LHR", not the San Jose or Bay Area airports you might expect. That is real analyst catchment judgement and is exactly the kind of decision the catchment table has to capture. Worth asking the analyst who built it (initials OS, JZ) why those three airports.

### OAG schedules (to come)
A European OAG schedule download, placed alongside the Sabre data under 18 Products. Not yet uploaded. Needed for phase 4, not phase 2, so it does not hold up the start. When it lands, confirm its format matches what `app/oag_parser.py` already reads.

## To gather before phase 2 (people, not files)

- The catchment definitions the analysts use in practice (how they group airports into a service area), to seed the reference table. First question for Nick.
- A second reference case built off 2013 data, directional, for the very first generator shakedown. Using a 2013-data route keeps the directional-versus-non-directional question out of the first test, since 2013 is one of only two directional years. BA LHR-SJC is the headline target that proves the whole tool, but it was built off roughly 2014 data, which is non-directional, so it is better as the second test than the first.

## Status at the time of writing

- Sabre: all twelve years uploaded and unzipping; the four checked so far (2013, 2016, 2017, 2019) read on one identical schema. The rest were syncing to Egnyte overnight; confirm they are all readable before relying on them.
- OAG: not yet uploaded.
- Reference case: present and complete on Egnyte as above.
