# Start here - QSI Auto Cowork project

This folder is the starting point for rebuilding and extending the QSI route forecasting tool in Cowork. Read this first, then the numbered docs, in order. It is written so someone who has not seen the project before can pick it up cold.

## What the project is

Avia forecasts passenger demand on a route using the QSI method: schedule quality drives an airline's share of a market, and that share applied to market demand gives a passenger forecast. The method lives today in a set of Excel models that analysts run by hand, pulling Sabre demand data and OAG schedule data for each route.

Over Christmas 2025 a working proof of concept turned that method into a Streamlit web tool. It reads the Sabre and OAG extracts and produces the forecast, the assumptions trail, an Excel output and a PowerPoint. That POC is in the `app` folder.

The next stage, and the main work of this project, is to remove the manual data pull. Avia now holds ten-plus years of global Sabre data (circa 91GB) and will hold European OAG schedules. The tool should query that data itself for any two airport codes, build its own correctly formatted input files, and forecast from there. No external APIs. The end state runs on a laptop with no internet, for live use at World Routes.

## What is in this folder

- `01_HANDOVER_code.md` - what the existing POC is, which file runs it, how it is structured, and its state. Read this to understand the code in `app`.
- `02_DATA_LAYER_BUILD_BRIEF.md` - the design for the new data layer: how to ingest the 91GB, the confirmed Sabre schema, the column mapping, and the build sequence. This is the main technical document.
- `03_UPLOAD_CHECKLIST.md` - exactly what to put in the Cowork project and what to point at on Egnyte, with paths.
- `04_COWORK_KICKOFF_PROMPT.md` - the first message to paste into the Cowork project to set it up well.
- `app/` - the runnable POC. Entry point `avia_qsi_auto_v3.py`. See `app/RUN.txt` and `01_HANDOVER_code.md`.

## The governing principle

Build one route end to end before you build breadth. One route, one year, reproducing a forecast you already have the answer to. That single slice is where the tool either works or shows its problem, and everything after it is scaling rather than discovery. The common way this kind of build wastes time is doing all the ingest, then all the generator, then all the wiring, and only meeting the integration problems at the end on 91GB of data. Do not do that.

The known-answer route is BA London Heathrow to San Jose. The original analyst forecast, its inputs, and its output all exist on Egnyte (see `03_UPLOAD_CHECKLIST.md`), and the POC already carries that route's result as its regression target: 129,162 passengers. If the rebuilt tool reproduces that number from the master data, the front end is faithful.

## The plan in plain English

1. Stand the tool up. Put the `app` code into the Cowork project and get it launching on the shared environment, before touching any data, so you know the inherited POC runs. Settle one config file for all data paths now, so nothing is hardcoded.

2. Prove one route. Load one year of Sabre data (2013) into a fast local store (DuckDB). Take a reference forecast for that year where you hold the analyst's own input and output. Build just enough of the new data generator to produce that one route's input from the store, and tune the three judgement calls (which carrier basis, true origin or board point, how to treat cabin) until the generated input matches the analyst's. Then run it through the tool and confirm the forecast matches. This phase is the whole risk, so give it the time.

3. Widen the data. Load the remaining years (they all read on the same schema, confirmed). Build the catchment and reference tables properly, seeded from the data. Run several more reference forecasts through and record where the tool and the analyst differ and why. That record is the actual product: the codified analyst reasoning.

4. Add OAG and close the loop. Load the European OAG schedules, build the schedule side of the generator, and wire both into the tool so the input step is two airport codes, not a manual upload.

5. Run the full backtest. Push the rest of the roughly 70 historic forecasts through, capturing the differences and the reasoning into the rule set. This is where the tool earns trust.

6. Package the laptop build. Bundle the data store, the reference tables and the app into one offline app for World Routes, with the data paths rewritten to the local drive automatically.

## What to do first

Open `04_COWORK_KICKOFF_PROMPT.md`, check the file paths in `03_UPLOAD_CHECKLIST.md` are right for your setup, then paste the kickoff prompt into the new Cowork project. It tells Cowork to read these docs, confirm the plan, and start with phase 1 above.

## House style for anything the tool or Cowork produces

UK English. Active voice. No em dashes. Plain hyphen for ranges. Document author and last-modified-by set to "Avia Solutions" on any generated Excel, Word or PowerPoint. Numbers as "12.4m passengers" and "$695m". Dates as "29 June 2026".
