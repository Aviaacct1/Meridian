# First prompt for the QSI Cowork project

Paste the text below the line into the new Cowork project as the first message, once the `app` folder, the reference-case folder and these documents are in the project. It sets the context, the working rules, and the first task, and it tells Cowork to confirm the plan before building anything.

Adjust the bracketed paths if your setup differs.

---

You are working with me on rebuilding and extending Avia Solutions' QSI route forecasting tool. Before doing anything, read these files in the project, in order: `00_START_HERE.md`, `01_HANDOVER_code.md`, `02_DATA_LAYER_BUILD_BRIEF.md`, `03_UPLOAD_CHECKLIST.md`. They are the full context. The runnable proof of concept is in the `app` folder, entry point `avia_qsi_auto_v3.py`.

The goal of the project: the tool should take any two airport codes, query Avia's own Sabre and OAG data (no external APIs), build its own correctly formatted input files, and produce a QSI passenger forecast. The end state runs offline on a laptop. The forecast method in the existing code is calibrated and must not change; the work is the data layer that feeds it.

How I want you to work:

- Build one route end to end before building breadth. The first proof is reproducing a forecast we already have the answer to: BA London Heathrow to San Jose, where the analyst's inputs and output are in the reference-case folder and the target is 129,162 passengers. Do not build the full ingest, then the full generator, then the wiring; prove the single route first.
- Confirm the plan with me before writing code. At each phase, tell me what you intend to do and what you expect to see, then proceed once I agree.
- Put every file path in one config file. Nothing hardcoded. This is what lets the same code run against Egnyte for the team and against a local drive on the laptop. Clear out any hardcoded paths you find in the existing modules as you go.
- Do not download the 91GB of Sabre data. It is on the Egnyte-mounted drive at [Shared/Company Data/18 Products/Data/Sabre/ODPOO/]. Read it from there. Each annual file is circa 7GB, so load it into a local DuckDB store and query the store, never open the raw CSV whole.
- Ask before anything irreversible: deleting files, overwriting data, changing anything outside the project folder.
- Any document the tool generates (Excel, Word, PowerPoint) uses UK English, active voice, no em dashes, and has its author and last-modified-by set to "Avia Solutions". Numbers as "12.4m passengers", dates as "29 June 2026".

The first task, phase 1: get the existing POC running in this environment. Install its dependencies from `app/requirements.txt`, launch `app/avia_qsi_auto_v3.py` with Streamlit, and confirm it starts. Then create the single config file for data paths and tell me what you found in the existing modules that needs to point at it. Do not start on the data ingest yet.

When you have read the documents, summarise back to me, in your own words, what the project is, what the first route test is, and what you will do in phase 1. Then wait for me to confirm before you begin.

---

## Notes for you, John, not part of the prompt

A few things worth knowing about running this in Cowork:

The kickoff deliberately stops Cowork at "confirm the plan back to me". The first sign of whether it has understood the project is its summary. If that summary is right, you can let it run phase 1 with a light hand. If it is wrong, you have caught it before any code.

Phase 2, proving the single route, is where your and Nick's time matters most. The three judgement calls in the brief (which carrier basis, true origin or board point, how to treat cabin) are decisions only Nick can make against how the reference forecasts were actually built. Cowork can build either way; it cannot know which is right. Settle those three before letting it finalise the generator.

When you reach the directional-versus-non-directional check, it is the single cross-year query described in the brief, not a piece of build work. Have Cowork run it and show you the result for one asymmetric market.

Keep the BA LHR-SJC number, 129,162, as the line you do not cross. Until the rebuilt tool reproduces it from the master data, treat any forecast it produces as unproven, however reasonable it looks.
