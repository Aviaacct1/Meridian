# Kick-off prompt for a Fable review of the Avia Cortex QSI tool

Paste the block below as the opening message to a new Fable session in this project.

---

You are Fable, reviewing the Avia Cortex QSI route-forecasting tool for John Carter, MD of Avia
Solutions. This is a fresh, independent review, not a continuation of the build. Your job is to look
hard at four things and report honestly, weaknesses first, no cheerleading: the code and structure,
the tool's viability as a product sold to airports, the development next steps, and a realistic
pathway to selling a licensed version. John values candour and peer-level reasoning; tell him what is
weak, not just what is impressive.

## What the tool is

Avia Cortex is a route-forecasting engine an airport uses to build a case to an airline for a new
route. Given a city pair it measures the addressable O&D market from Sabre MIDT, apportions it across
competing airports by a frozen analyst QSI share (schedule quality, not population), adds the
connecting feed, caps at the aircraft and frequency, and attaches a route P&L. It runs offline on a
laptop for a stand at World Routes (target: late September 2026). The engine is DuckDB over two local
stores: C:\Avia\sabre.duckdb (MIDT O&D, ~91GB) and C:\Avia\oag.duckdb (OAG schedules). A FastAPI
portal (cortex_app.py, port 8010) is the front end; backtest.py is the calibration harness that grades
the engine's as-if forecasts against real outturn across six years of launches.

## Read first (do not take the summary below on trust; verify against the code)

- The auto-memory index MEMORY.md and the qsi-* notes, especially qsi-opus-progress, qsi-project-state,
  qsi-engine-v2, qsi-review-for-opus. These record what was done and why.
- REVIEW_QSI_for_Opus_05Jul2026.md (project root) - the previous review and its fix list.
- SEASONAL_MODE_design_note.md, SEASONALITY_CHECK.md, DEPLOY_DEMO.md, requirements.txt (in app/).
- Core engine: app/route_forecast.py, route_feed.py, qsi_feed.py, qsi_score.py, catchment.py,
  sabre_catchment.py, oag_served.py, coverage.py, aircraft_economics.py, aircraft_select.py,
  seasonality_engine.py, water_check.py, db_registry.py.
- Portal: app/cortex_app.py. Calibration: app/backtest.py, analyze_calib.py, analyze_tail.py,
  verify_identity.py, build_preagg.py, preagg.py.

## Current state, as of the latest build (verify, don't assume)

The runtime was rebuilt for speed and safety: a Sabre pre-aggregation layer, a multiprocessing route
pool, a per-worker DuckDB memory cap (the machine has 16GB and froze repeatedly before the cap), and
determinism fixes so a route forecasts the same number twice. A full six-year back-test now runs in
about two hours rather than 7-15. The engine is calibrated: a type-aware P2P level trim (FSC/ULCC
0.85, LCC 0.95) sized on the hit rate, not the median, so it lifts the share of routes inside a tight
band without moving the ones already right. A seasonal forecast mode (annual/summer/winter) was just
added. Demo hardening exists (warm_demo.py, a local non-OneDrive deployment guide).

Known weaknesses already on the table, which you should assess and may extend: the tool under-forecasts
INDUCED, new-market routes badly (median 0.14 of outturn) because there is no history for a market that
does not exist yet, and that is exactly the case an airport most wants to pitch; the honest forecast
scatter is wide (only ~25% of forecastable routes land within +/-20% even after calibration, roughly
half within a factor of 1.4); seasonal demand is currently an assumed monthly profile pending a monthly
Sabre pull; and the operating setup is fragile (runs have been fought with OneDrive file corruption and
two conflicting Python installs).

## What to review

### 1. Structure and code

Assess the architecture and whether it is a product or a pile of experiments. The app/ folder holds the
real engine alongside a large number of one-off scripts, an _archive_old_versions folder, and duplicate
working files (_ck_*, _btk_*, _rf_* and similar). Judge: module boundaries and coupling; what is the
actual product surface versus experimental cruft that should be quarantined; error handling and failure
surfacing; test coverage (there are a few test_*.py and pretest scripts, is that enough); the DuckDB
access and memory model; the determinism and reproducibility story; and the operational fragility
(OneDrive, dual Python, no pinned environment until recently). Call out anything that would embarrass
the tool in front of an airline network planner or a due-diligence buyer. Flag correctness risks in the
methodology, not just style.

### 2. Product viability for airports

Does it actually solve an airport's problem, which is convincing an airline that a route will work?
Weigh the demand-forecast credibility given the scatter above and the induced-route weakness; the value
of the honest confidence bands versus a competitor's confident single number; the economics/P&L and the
seasonal capability; and whether the outputs (portal, deck, workbook) are what an airport's air-service
development team and an airline's network planner would actually accept. Place it against the landscape:
Sabre Market Intelligence / AirVision, OAG, Cirium Diio, ForwardKeys, and the ASM/Routes consultancy
model that airports currently pay for. Where does this win, where does it lose, and is "honest, offline,
airport-owned" a real wedge or a nice-to-have.

### 3. Development next steps

Prioritise the open work by value to the airport buyer, not by ease. The known queue includes: the
induced/new-market under-read (a stimulation and comparable-market modelling job, the highest-value and
hardest); the seasonal engine's optimise axis and its one-season calibration; the monthly Sabre data
dependency (a pull has been drafted for the data provider); a reinstatement discount; possible
recalibration of the coverage gross-up factors; and the front-end confidence-band and resolution-chip
items from the prior review. Add anything you think is missing. Say what you would do in the next month
versus the next quarter.

### 4. Pathway to selling a licensed version

This is the part John most wants your view on. How does an internal consultancy tool become a licensed
product an airport pays for. Address, at minimum: the DATA-RIGHTS question, which is likely the binding
constraint, since the forecasts are derived from Sabre MIDT and OAG data and a licensed product cannot
simply redistribute that, so work through whether the customer brings their own data licence, whether
Avia needs redistribution rights, or whether the product ships as a methodology over the customer's
data. Then the deployment model (multi-tenant SaaS versus on-prem/airport-owned, which the offline
design already leans toward); pricing and packaging (per-seat, per-airport, per-case, subscription
versus consultancy-plus-tool); the defensible IP and moat (the frozen analyst QSI, the validated
methodology, the calibration evidence base) versus what a competitor could replicate; the go-to-market
motion (airports as buyers, the ACI/Routes channel); and the credibility bar and validation an airline
would demand before trusting the numbers in a real negotiation. Give a staged commercial pathway, from
where it is now (an internal tool with a World Routes demo) to a first paid pilot to a licensed product,
with the gating risks at each stage named plainly.

## Output

Write a structured review, findings tagged by severity and effort where useful, weaknesses and risks
up front, a clear prioritised list at the end, and a separate honest section on the licensing pathway
with the data-rights question resolved one way or the other. UK English, active voice, no em dashes,
peer-level. Do not soften the commercial risks to be encouraging; John needs the real picture to decide
whether to invest in productising this.
