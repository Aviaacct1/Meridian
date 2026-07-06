# QSI Auto - Handover Note

Prepared for the Cowork folder so the project can be picked up cold. This note records what the tool is, which file actually runs, what it needs to produce a result, the current state, and the first jobs to do.

## What it is

A Streamlit web portal that automates the Avia QSI route forecasting method. It takes airline schedule data (OAG/QSI workbooks) and demand data (Sabre/MIDT extracts), runs the QSI capture model, applies commercial calibration, and produces a passenger forecast with a full assumptions trail, an Excel output workbook, and a branded PowerPoint. It is the Python build of the spreadsheet QSI method, structured so the calibration logic and the standardised inputs and outputs can later support a sellable product.

The build follows a three-step automation chain:

1. PCE, the Predictive Calibration Engine. For a new route with no analyst-set parameters (Path B), it predicts the QSI parameters from a 22-case calibration library before the pipeline runs.
2. The pipeline. It scores QSI capture, builds connections, allocates fares, applies seasonality, and produces the passenger and revenue forecast.
3. CRE, the Commercial Reasonableness Engine. After the pipeline runs, it checks the output against commercial bounds, auto-adjusts where a result is implausible, and scores confidence from 0-100 (HIGH / MODERATE / LOW / VERY LOW), flagging anything that needs analyst review.

## Which file to run

Run `avia_qsi_auto_v3.py`. That is the canonical entry point and the latest in the lineage.

The folder you started from carried six or seven parallel versions of the same app, which is normal for something assembled across many chat sessions. The version history runs `qsi_portal_v4 -> v8 -> v9 -> v10 -> v11`, then the line was renamed and extended as `avia_qsi_auto.py` and finally `avia_qsi_auto_v3.py` (internally labelled v12, the one that wired in CRE as an automatic post-pipeline step). Everything earlier is superseded.

I have already done that tidy-up in this folder. The 28 live modules plus the entry point sit at the top level. Every other version has been moved into `_archive_old_versions/` rather than deleted, so nothing is lost if a cross-check is ever needed.

## How to run it

See `RUN.txt` for the exact commands. In short: create a virtual environment, `pip install -r requirements.txt`, then `streamlit run avia_qsi_auto_v3.py`. The portal opens at http://localhost:8501.

Dependencies are light. There is no machine-learning library, no database, and no API key required to run. The full list is streamlit, pandas, openpyxl, xlrd, and python-pptx. The calibration and "learning" logic is pure pandas and rules, not a trained model, so it is transparent and editable.

## Data the tool needs

This is the single most important point for picking the project back up. The code is here. The source data is not.

The validated reference case (BA LHR-SJC) and the Path A pre-computed route both load workbooks that lived in the original Claude working directory at `/mnt/project`. Those files are not in the zip. To reproduce a result you need to put the source workbooks into the `/data` folder and repoint the loader at it. The reference case specifically expects:

- `QSILHR_v1_OS_JZ_17Feb15.xlsx` (the QSI schedule workbook, with the QSI 1 sheet and related sheets)
- `LHR_MCTs.xls` (minimum connection times at Heathrow)
- `Minimum_Cnx_Times_SJC.xls` (minimum connection times at San Jose)
- the Sabre/MIDT demand extracts (filenames follow the pattern `LONSJCxxx.xlsx`, `SJCLONxxx.xlsx`, `P2P_LONBAY_AREA_2013.xlsx`, `NH_P2P_Demand_OS_02Mar15.xlsx`)

These are your own QSI and Sabre source files. They will be on the hard drive near the original models. `RouteConfig.ba_lhr_sjc()` takes a base directory path; the regression test passes `/mnt/project`, so locally you point it at the `/data` folder once the workbooks are in place.

The Sabre extract format the demand provider expects is the standard 20-column MIDT layout. The provider factors raw Sabre bookings up to total market (Sabre captures circa 85% of bookings, varying by market). That logic is documented in the header of `midt_demand_provider.py`.

### Two ways data comes in

- Path A, pre-computed: load an existing analyst-built QSI workbook and reproduce the result. This is the path the reference case and regression test use, and it is the one that needs the source workbooks above.
- Path B, new route: enter route characteristics in the portal, let PCE predict the parameters, and upload OAG/Sabre extracts through Tab 1. This path does not need the historical reference workbooks.

## The validation anchor

The golden number is BA LHR-SJC = 129,162 passengers (P2P 78,110 plus connecting). `test_regression_v2.py` asserts it. Treat that as the regression guard: any change to the pipeline or calibration should be checked against it before the change is trusted. The test runs today but fails at the data-load step because the source workbooks are absent, not because of a code fault. Once `/data` holds the workbooks, run `python test_regression_v2.py`.

## The 16 tabs

1. Data Upload and Run (Path A and Path B)
2. Results (forecast breakdown plus the CRE confidence assessment)
3. Monthly Profile (seasonality engine)
4. Revenue Forecast (passenger, cargo, ancillary)
5. Assumptions Log (72-parameter methodology summary)
6. Business Case (goal-seek plus sensitivity)
7. Output Workbook (standardised Excel export)
8. Q&A Checklist (automated quality control)
9. Spill Analysis (capacity constraint)
10. Market Research (research brief plus findings tracker)
11. Comparison (analyst forecast against pipeline forecast)
12. Validation (cross-route regression suite)
13. Time Grid (departure-time search, new route only)
14. Calibration Engine (predictive parameter suggestion)
15. Fare Allocation (per-market fares from Sabre data)
16. Presentation (PPTX generator with airport, airline, and fund variants)

## Current state

- The full live module set compiles and imports cleanly. There are no missing internal modules.
- The app launches and the upload-driven tabs and Path B work without the historical reference data.
- Path A, the cross-route validation, and the regression test need the source workbooks in `/data` before they will produce numbers.
- The reference logic reproduced 129,162 in the original environment, so the method is sound; what is missing here is the data, not the model.

## Known gaps and porting jobs

These are the things to settle early in Cowork.

1. Restore the source data. Find the QSI and Sabre workbooks listed above, drop them into `/data`, and confirm the reference case returns 129,162. This is the proof that the port is faithful.
2. Hardcoded sandbox paths. Several modules carry `/mnt/project` and `/mnt/user-data/outputs` paths in their demo blocks and default loaders (`departure_time_grid.py`, `closed_loop_pipeline_v2.py`, `route_config.py`, and others). The portal's own run path uses uploaded files, so these do not block normal use, but they should be replaced with a single configurable base path so the tool is portable across machines.
3. Market research tab. `market_research_executor.py` was written for an environment where Claude provides web search; it accepts an optional search function and falls back to stored sample findings when none is supplied. On a local machine that tab will not fetch live sources until a search function is wired in. Decide whether that tab is in scope for the first product or stays manual.
4. Output file authorship. The Excel and PowerPoint generators should stamp the document author and last-modified-by as "Avia Solutions". Confirm `output_workbook.py` and `city_pair_pptx_generator.py` do this before any output goes to a client.
5. One canonical version only. Keep `avia_qsi_auto_v3.py` as the single entry point. If a feature is needed from an archived version, port it forward into the live file rather than reviving the old one.

## Recommended first steps in Cowork

1. Stand the app up locally from this folder and confirm it launches.
2. Restore `/data` and pass the regression test. Until that passes, treat any forecast as unverified.
3. Replace the `/mnt/project` defaults with a configurable base path.
4. Write a short product definition for the first sellable output, scoped to what the tool already does well: the standardised forecast plus the assumptions log plus the Excel and PPTX outputs. That is the recurring-revenue product to scope within twelve months, and this tool is the closest thing to a working version of it.

## File inventory

Live, top level: `avia_qsi_auto_v3.py` (entry) and 28 supporting modules, `Avia_QSI_only.png` (brand asset), `test_regression_v2.py`, `requirements.txt`, `RUN.txt`, this note, and the empty `/data` folder for source workbooks.

Archived, in `_archive_old_versions/`: every superseded portal version, duplicate provider and pipeline files, the older calibration libraries (live one is `calibration_library_v8.py`), and the standalone scripts not used by the portal. Kept for reference, safe to ignore for normal work.
