# QSI Tool: Project Handover Note

Author: Avia Solutions
Date: 26 June 2026
Purpose: a complete handover so a new chat in this project (or a colleague) can continue without losing any progress or knowledge. The project's memory files also carry this across chats automatically, but this is the single readable record. Where a fact is a validated number, it is stated exactly.

---

## 1. What the tool is, and the one rule

Avia is rebuilding and extending its QSI route-forecasting tool so it runs offline on a laptop and produces an integrated airline business plan: QSI demand, plus revenue, aircraft economics, socio-economic and competition. The QSI method itself is the established Avia method and must not change. The work is the data layer, the automation, the validation, and filling the capability gaps (chiefly aircraft economics).

QSI logic in one line: schedule quality drives an airline's share of a market; share times market demand gives the passenger forecast.

The discipline, set by John: validate then improve. The back-test must first reproduce the analyst's number with the original settings (baseline). Only then layer improvements as measurable toggles, so a real improvement is always distinguishable from a bug. Much of the historic "method" is manual-era shortcut, not truth; automation lets us compute the full analysis and decide what to cut after seeing it.

---

## 2. The validated QSI method (the crown jewels: do not lose these)

Confirmed against the analyst SJC QSI@SJC workbook (Cathay Pacific 2024) and the production code.

QSI score per itinerary:

    qsi = Frequency x ET-coeff x connection-type-coeff x service-level-coeff

- ET-coeff (excess-time penalty, relative to the minimum-elapsed routing for that city):
  `et_coeff = 1 / ((int(excess_hrs / 0.1) + 1) ^ 0.8)`  with factor 0.8, interval 0.1.
  Validated EXACT against the analyst lookup: 0.10 hr -> 0.574, 0.20 -> 0.415, 0.50 -> 0.238, 0.90 -> 0.158, 1.00 -> 0.147, 6.10 -> 0.037. The nonstop advantage comes through ET (nonstop = minimum elapsed = ET 1.0).
- Connection-type-coeff: ONLINE 1.00 / ALLIANCE 0.75 / INTERLINE 0.25. The 2024 SJC workbook uses 0.75. The older 2013 default in the code is 0.615 (see open decisions).
- Service-level-coeff: non-stop 1.00 / one-stop 0.20 / two-stop 0.40. This was the missing piece. The analyst's "QSI 1 Calc" appears to read freq x ET x cnx, but the one-stop 0.20 IS applied. Proof: SJC-HKG nonstop fair share was 12% without it versus the analyst's circa 65.6%; adding one-stop 0.20 lifts it to the right order.
- Fair share = route_qsi / market_qsi.
- The method computes QSI 1 (origin to hub to beyond, outbound) and QSI 2 (the reverse) and reports the AVERAGE of the two fair shares.
- There is NO calibration or scaling to Sabre/MIDT bookings anywhere in the analyst method. Fair share straight from QSI IS the deliverable, then applied to market size.

Acceptance test for a faithful rebuild: reproduce the analyst's Cathay SJC-HKG result (the workbook's "Total QSI Score for Market" circa 65.6%) on the same hub, 2024 week and MCT inputs.

Production-code status: the live engine is `QSIEngine` in `app/closed_loop_pipeline_v2.py`. It was missing the service-level coeff and that has now been fixed (see section 6). Its ET-coeff matches the analyst lookup exactly. Bidirectional averaging is present and correct.

---

## 3. Where everything lives

- Canonical home (source of truth): Egnyte `18 Products/QSI`, with subfolders Application, Data Store, Reference Tables, Reference Cases/BA LHR-SJC, Outputs, Documentation, Laptop Build. Raw 91GB Sabre/OAG masters stay at `18 Products/Data`, read in place, never copied.
- Working store and scratch: `C:\Avia` on John's PC. Holds the DuckDB stores and the runnable scripts. This folder is mounted into the Cowork session.
- Cowork project folder: `C:\Users\Carte\OneDrive\Documents\Claude\Projects\Avia QSI Tool` (OneDrive-synced; this note, the deck, the docs and the app working copy live here).
- The model: Egnyte is home; the Claude/Cowork environment is a working checkout; publish to Egnyte at milestones. John develops mostly at home (Egnyte mapped to Z:). Secure work laptops map P:; a future Teams account maps P:.
- `app/config.py` is the single source of truth for all paths. It auto-detects the Egnyte mount by trying candidates and picking the one whose "18 Products" folder exists (override with `AVIA_EGNYTE_ROOT`). No per-machine path edits needed. Shared-vs-laptop build switch via `AVIA_QSI_BUILD`.

---

## 4. The data stores: exact state

### Sabre demand store: `C:\Avia\sabre.duckdb` (table `sabre`)
- Circa 15.3GB, 286,507,723 rows, 12 distinct travel years 2013-2024 INCLUDING 2020.
- Row counts by year: 2013 26.2M (POO), 2014 27.9M, 2015 28.2M (POO), 2016 27.1M, 2017 27.5M, 2018 28.3M, 2019 28.1M, 2020 14.2M, 2021 12.3M, 2022 19.7M, 2023 23.5M, 2024 23.4M. All ND except 2013 and 2015 which are directional (POO).
- Source = ODPOO master at `18 Products/Data/Sabre/ODPOO`. The store is essentially the full global market (2013 alone = 2.72bn passengers), not a sample.
- ONLY GAP: 2025. The "World2025POONDBest" forward best-estimate file failed a DuckDB CSV dialect sniff. `sabre_ingest.py` read_csv has been hardened (strict_mode=false, null_padding=true, delimiter fallback). ACTION: John drops the updated `sabre_ingest.py` into `C:\Avia` and re-runs `ingest_all_years.py` (only 2025 retries). If it then errors on column mapping, paste the 2025 file's first 3 lines. 2025 is worth it: forecasts done this year use 2025 base data, so loading it lets Avia produce outputs before the analyst.
- Schema (table `sabre`): origin_airport, destination_airport, marketing/operating_airline, cabin_class, year, connecting_airport1-3 (+city/country), leg1-4 op/mkt airline, poo_airport/city/country (true origin), passengers, avg_base/total_fare_usd, base/total_revenue_usd, distance_km, directionality, source_year.
- NOT reachable from the Cowork sandbox (too large). Queries run on John's PC.

### OAG schedules store: `C:\Avia\oag.duckdb` (table `oag`)
- Circa 165MB, 28 region-weeks, 3.14m flights. IS reachable and queryable from the sandbox (unlike sabre.duckdb).
- Weeks held: 2017 (29 May, 30 Oct), 2019 (27 May), 2025 (partial). Jess pulled WHOLE REGIONS (Europe, North America, Latin America, Africa, Middle East, Asia, Southwest Pacific = 7 files per date) rather than an airport list: 100% coverage, no missing-connection risk.
- OAG history limit is 2015 (Nick). So the schedule back-test runs 2015 onward only. The BA LHR-SJC 2013 reference and the Chicago/Ricondo 2012-14 studies fall outside OAG and stay Sabre-demand-only.
- Schema mirrors the cleaned OAG field set: carrier, dep/arr airport/city/country/region/terminal, local times, days, seats + cabin, eff dates, elapsed/flying/ground, stops, aircraft, alliance, carrier_category, dup_marker, pass_class, gcd_km/mi, asks, frequency, seats_total; tagged week/region/year/source_file.
- Jess delivers the REMAINING OAG weeks Monday (see section 9 handoff).

### Licence note
Avia licenses OAG Schedules Analyser only, NOT Traffic Analyser. So OAG is the schedules side; demand AND fares both come from Sabre (ODPOO), which we hold.

---

## 5. What is validated end-to-end

1. Demand generator (the "two airport codes, no manual upload" demand half). `sabre_generate_demand.py` emits the exact 20-column Sabre layout the pipeline reads, single-connection filtered, with a direct/indirect split weighting (`--factor-direct 1.166 --factor-indirect 1.044`). On the full BA LHR-SJC run it reproduces Ollie's hand-pull at all three levels: direct 1,485,885 (-0.04%), indirect 4,633,686 (-0.04%), total 6,119,571 (-0.04%). Meets John's "within 5% at each level" bar (direct/indirect split is a client deliverable, so each level must match, not just the total).
2. End-to-end forecast chain. Raw store -> auto demand extract -> forecast engine -> convergence reproduces the analyst number: BA LHR-SJC grand total 129,152 versus 129,162 (-0.01%) at 82.9% LF. `run_forecast.py` does this in one command.
3. Destination scope derivation. The connection builder, run against the real LHR OAG week with GCD circuity, reproduces Ollie's hand IN/OUT scope. A single circuity cut at 1.25 agrees with Ollie 100% (keeps 96/96 IN, drops 46/46 OUT). Ollie's hand scope was, in effect, a circuity threshold of about 1.25. This is why getting the great-circle distance field mattered most.
4. QSI scoring on real data, through MCT to capture. The full chain (real OAG -> connection builder -> real MCT master -> circuity cut -> QSI scorer) runs end-to-end. Full multi-hub run on the Phase A file (35 hubs, 2.37m connections, 1.16m kept after circuity) gives a realistic full-competition capture.
5. Back-test / calibration framework. See section 8.

Outstanding to make the schedule-side back-test fully calibrated: validate the corrected QSI engine against an analyst capture workbook for a route where we hold both its OAG pull and its capture sheet (the Cathay HKG-SJC / EVA TPE-SJC 2024 cases once their OAG is in the store), and add QSI2 where a script is still one-directional.

---

## 6. Code and scripts: inventory and state

All runnable scripts live in `C:\Avia` (and most also in the project `app/` working copy). Run locally with `py -3.12` from the app directory so the imports resolve.

Demand side (Sabre):
- `sabre_ingest.py` - DuckDB ingest, one year per run; cleans two-space nulls, casts numerics, tags directionality/source_year. Hardened read_csv for the 2025 file.
- `ingest_all_years.py` - bulk ingest, globs ODPOO, infers year + directionality, skips loaded years.
- `sabre_generate_demand.py` - the connecting-demand generator (validated, above). `--factor-direct 1.166 --factor-indirect 1.044`, `--combine-directions` for 2013/2015.
- `sabre_generate_p2p.py` - point-to-point market generator (Residents = catchment-origin, Visitors = hub-origin, by cabin tier).
- `sabre_generate_extract.py` - full 20-col extract generator.
- `run_forecast.py` - one-command end-to-end (reads demand_extract.csv -> pipeline + convergence -> forecast).
- `convergence.py` - back-test LF convergence helper (non-invasive; needs a known target LF, so it is a back-test tool, not forward).

Schedule side (OAG):
- `oag_ingest.py` - ingest one OAG region/airport xlsx into oag.duckdb; maps spaced or machine headers to a stable schema; idempotent per (week, region).
- `ingest_all_oag.py` - bulk OAG loader over the Data Store folder; infers week + region; skips loaded.
- `connection_builder.py` - builds timed connections at a hub against MCT. Reads the standard OAG columns; auto-detects the sheet by header (handles v1 'OAG' and v2 job-id sheet names); reads via python-calamine (fast; openpyxl fallback) so it ingests the 75MB Phase A file natively; captures the v2 fields (alliance, carrier category/LCC, dup marker, GCD km/mi, ASKs, pass class). Single connection, layover > MCT (default 90, floor 20), max 720 min, single stop.
- `schedule_chain.py` - splits a raw single-airport OAG export into arrivals/departures, builds connections per hub, derives served scope, applies a tunable pareto/circuity hub cut. Data-driven alliances and LCC exclusion from the v2 flags (falls back to bundled lists for v1). GCD circuity filter, default cut 1.25 (tunable). Market-scoping (origins/dests) so a full single-hub file does not all-pairs explode.
- `run_multihub_qsi.py` - one command: load -> data-driven alliances/LCC -> build connections over every hub into the catchment -> inject the proposed service -> real MCT -> circuity cut -> QSI capture per beyond market. `load_legs_any()` takes a folder/glob/comma-list. CLI example: `--oag "<Hub Airports file>" --catchment SFO,LAX,SJC,SAN,OAK --proposed BA,LHR,SJC,1700,2000,645 --circuity 1.25 --mct <master>`.
- `qsi_market.py` - the authoritative QSI1 + QSI2 market validation script (alliance 0.75, one-stop 0.20, both directions averaged). Use this to reproduce SJC-HKG and to run GOA-NYC. Run locally (the sandbox sees a truncated OneDrive copy).
- `goa_qsi_test.py` - store-driven GOA-NYC QSI straight from oag.duckdb (no spreadsheet load).

Forecast and analysis:
- `goa_nyc_forecast.py` - transparent first-draft Genoa-NYC forecast; every input labelled MEASURED or ASSUMED; takes QSI capture from run_multihub_qsi when `--oag` given.
- `back_test.py` - v1 point-to-point floor back-test.
- `back_test_v2.py` - auto-detects launch year/carrier/base per O&D, computes floor/actual/uplift segmented by route type, runs the one-stop coeff as a sensitivity.
- `back_test_cohort.py` - auto-discovers every new long-haul nonstop O&D per launch-year cohort, forecasts the floor from contemporaneous pre-launch data, compares to outturn, prints the capture-band uplift table, and runs the blind hold-out accuracy test. Data-quality guards (genuinely virgin over two prior years, min base market, sanity cap). General: any city pair, any haul, any service type, domestic included.
- `comparator_extract.py` - read-only comparator-routes analysis on sabre.duckdb (built for the Genoa call).

Aircraft economics:
- `app/aircraft_economics.py` (242 lines) - the route P&L module. See section 7.

Lookups: `airport_city_country.csv`, `destination_scope_LHR.csv` (Ollie's cut-3 scope, a validation reference not a maintained input), the MCT master (below).

Config and reference:
- `app/config.py` - single source of truth (above). `config.MCT_MASTER` wired.
- MCT master: Avia owns it now (OAG no longer provides it). `MCT Master List.xlsx` at Egnyte `18 Products/QSI/Reference Tables/`. `connection_builder.load_mct_data` reads it with zero code change (3,668 keys; LHR same-terminal 60min, cross-terminal 75-90). Update by exception (changes only when airport investment improves connect times).

Production app: `app/avia_qsi_auto_v3.py` (Streamlit POC) plus circa 30 supporting modules. The fix made this work: `QSIEngine` in `closed_loop_pipeline_v2.py` now applies the service-level coeff (`service_coeff = nonstop_coeff if cnx blank else onestop_coeff`); `providers.py` Itinerary gained a `service_coeff` field; `assumptions_log.py` logs the coeffs and sets defaults (nonstop 1.0, one-stop 0.20). getattr defaults mean no breakage for configs lacking the field.

Deps for John locally: `pip install python-calamine airportsdata duckdb pandas openpyxl`.

---

## 7. Aircraft economics module (the rebuilt profitability leg)

The tool previously had no operating-cost or profitability code, so it never answered "does the route make money", the decision an airline network planner actually makes. That is now built.

- Anchor: "Project Maverick" (`Airline Route Profitability Model_Feb 18 2025.xlsx`, Egnyte Archive 2025/Mundys-LCY). `app/aircraft_economics.py` reproduces its worked example (BA LCY-EDI E190 Premium) to within 0.3%: revenue 22,098, cost 14,905 (variable 9,619 exact, direct-fixed 3,387 exact), profit 7,193, margin 32.5%, breakeven LF 44.5%.
- Key formulae learned: per-pax charges and charges-recovery apply to ALL turnaround pax (both legs), not half; ownership and crew held as $/block-hour; indirect (admin + sales) = 5% of NET (fare) revenue each; en-route nav = unit_rate x sqrt(MTOW/50000) x (km-40)/100.
- Coverage: 23 aircraft types (regional, narrowbody LCC/FSC, widebody), each with a `src` tag declaring its calibration basis. E190 is the validated Maverick anchor; A330/787 from the LHLCC 2015 model plus Belobaba/FAA non-fuel anchor; narrowbody from FAA YE2023 + easyJet; RJ/turboprop from FAA/EUROCONTROL. Widebody crew and ownership were corrected down to match Belobaba A330-200. Fuel burns are published cruise/block values.
- Charges + incentives are a per-route INPUT layer, not a stored global database: origin/dest charges override (current-year, e.g. RDC) wins, else the AIRPORTS table value is inflated from a declared base year at a declared rate, with the basis shown in the output. An Incentive line (home airport, waiver_pct, support_per_turn) models route-development support. Output gives standalone vs with-incentive margin.
- Citable sourcing reference: `Aircraft Economics Sourcing Reference.md` (project folder) holds the tiered free/paywalled databases and the Belobaba 2013 / FAA YE2023 / EUROCONTROL anchors, the stage-length adjustment, and CASK/RASK benchmarks.
- Knowledge folder sweep: `Knowledge Folder Asset Map.md` (project folder, 26 June) catalogues what the 02 Knowledge folder holds to firm the module: current OEM appraiser lease rates (the ownership leg) in the Airbus A&I Forum briefings and Boeing conference decks; the Airbus maintenance reserves database with a live Excel tool (the maintenance leg); the in-house FAA Opex extract; Aircraft Commerce per-type maintenance studies; and Nick's live traffic forecasting workbook (the demand companion to QSI). Recommended sequence is in that file.

Optional next builds (logged, John to direct): ingest the Airbus maintenance reserves Excel to replace the maintenance anchor; build the ownership leg from current OEM lease rates age-adjusted by the IBA/Ishka lease-rate-factor method; adopt the fuller Avianca cost line-items (air navigation, ramp and traffic, route fixed, pax compensation, commissions, promotions, cargo); build the annual network P&L layer (Maverick "Airline P&L 2"); wire economics into the report.

---

## 8. Calibration findings (the accuracy story)

From the cohort back-test on the data we hold (real MCT, data-quality guards, 120 routes):

- Uplift (actual / QSI floor) is a MONOTONIC FUNCTION OF MODELLED CAPTURE, not a flat factor. Capture-band table: 0-5% capture -> 14.50x (FSC 15.72 / LCC 11.63), 5-15% -> 11.05x, 15-40% -> 6.91x, 40-80% -> 5.03x, 80-100% -> 2.63x. FSC above LCC in the dense and mid bands; they converge to about 2.5x at high capture.
- Interpretation: the high-capture asymptote of about 2x is irreducible stimulation plus leakage recapture (even when QSI captures the whole point-to-point market, actual is about twice the floor). Everything above 2x is QSI under-crediting the nonstop as connecting competition thickens. So forecast = floor x capture-band uplift, one transparent lookup table in the style of Avia's existing ET-coeff lookup.
- Blind hold-out (train 2018+2019, forecast 2025 launches with no look-ahead, n=40): median absolute error 33%, within +-50% = 72%, errors balanced so the calibration is unbiased but noisy. Caveat: 2019 train versus 2025 test straddles COVID, plus stale 2019 OAG and a single split, so 33% is close to a worst case. The big misses cluster in the 80-100% band where the floor already meets or exceeds actual.
- Refinement (method, do regardless of more data): at high capture trust the floor (about 1x) and condition on base-market size, not a flat band factor.
- Real, publishable accuracy needs the full data suite (Monday's OAG weeks let us train/test across more years and rotate the hold-out).

A standing roadmap item is the QSI-vs-revealed-preference blend: with real MCT, the GOA hub split came out AMS-heavy versus Sabre's FCO-heavy reality, because QSI rewards Schiphol's low MCT. QSI scores schedule quality, not revealed preference; blending in Sabre observed routing is John's "leaving traffic on the table" point.

---

## 9. People, and who answers what

- Ollie (the OS/JZ initials on the 2013 BA workbooks; JZ is the second analyst) built the BA LHR-SJC reference. He left about seven years ago, so Nick reviews the historic method cold rather than recalling it. For 2013-era specifics, the working papers are the source.
- Nick - reviews the method; currently on the Zagreb project. He answers the OAG scoping questions and confirmed Sabre is already calibrated.
- Jol - socio-economic module. Ralph - airline economics and fare analysis. Each historically pulled their own Sabre/OAG, which is why the tool downloads once, comprehensively.
- Jess - does the OAG pulls (she has capacity). Delivering the remaining OAG weeks Monday.
- Antonio - pulled the Cathay 2024 data and knows the current Sabre pull/weighting setting. He, not Nick, is the right person to confirm the direct/indirect split weighting. `Antonio_weighting_question.md` is drafted with the 1.17/1.04 split for him to recognise. Do not send the older "no weighting" Nick reply, it is wrong.

Sabre weighting nuance: Nick said Sabre grosses to full market itself and Ollie's factor-up was a manual tweak. But Ollie (2015) and Antonio (2024) used near-identical split weightings independently, so it is a systematic transmitted step, and the direct/indirect split is a client deliverable that must match within 5% at each level. So the split weighting stays in; Antonio confirms the current setting.

---

## 10. Open decisions for John

1. Alliance coefficient: 0.615 (2013 code default) versus 0.75 (2024 SJC workbook). Left at 0.615; John's call. Config lives in `assumptions_log.py` and `input_validator.py`.
2. Is `QSIEngine` the live forecasting path, or does the app currently ingest pre-scored Excel QSI_SCORED files? This sets the urgency of the service-coeff fix. If the app ingests Excel, client forecasts are already Excel-correct and QSIEngine is the not-yet-live automation to fix before cutover.
3. Re-baseline the BA LHR-SJC = 129,162 regression after the service-coeff fix. The fix changes every forecast's nonstop-vs-connecting balance, so the target will move. Re-validate the corrected engine against the analyst SJC QSI@SJC Excel outputs; the engine should now match the Excel, and that becomes the new acceptance target.
4. The four Nick mapping questions, mostly resolved by data: marketing vs operating carrier (carrier attribution is across the operating legs, pending final confirm); true origin vs board point (= board point, confirmed by data); cabin aggregation (= sum across cabin); directional vs non-directional (combine both directions for the 2013 and 2015 directional years).

---

## 11. Operating mechanics and gotchas (read before running)

- OneDrive truncation race: editing a file on the OneDrive-synced project folder and then reading it back via bash in the sandbox can return a truncated copy, and stale .pyc can be reused. Workaround: treat the Edit/Write tool result as authoritative (do not re-read to verify); build and test from a sandbox-local /tmp copy; for pptx edit the XML in /tmp then pack; set PYTHONPYCACHEPREFIX off the synced tree.
- Sandbox limits: each bash call is independent (no cwd/env carryover), about a 45s cap per call, processes die between calls, and there is no Egnyte mount. So heavy ingest and big-file parsing run on John's PC; the sandbox builds and tests on small fixtures or the 999-row sample.
- `sabre.duckdb` (circa 15GB) is too large for the sandbox; queries run on John's PC and John pastes the output. `oag.duckdb` (165MB) IS reachable in the sandbox, so OAG-driven QSI runs can be done here.
- Ingest must run in a NON-admin cmd (an elevated session cannot see the user's mapped Egnyte drive). Use python.org 3.12 (the Microsoft Store Python had an import quirk); disable the Store python.exe App Execution Aliases.
- The big Phase A OAG file (75MB) defeats openpyxl one-pass; read with python-calamine (already wired into connection_builder).

---

## 12. Immediate next steps

Monday handoff (when Jess's extra OAG weeks land):
1. Ingest the new OAG files: `py -3.12 C:\Avia\ingest_all_oag.py` (idempotent; loads only the new weeks).
2. Add the new week strings to `OAG_WEEKS` in `back_test_cohort.py` (and `back_test_v2.py`).
3. Extend the cohorts / route library (more base years now possible: 2022/2023/2024).
4. Re-run `back_test_cohort.py` locally (real sabre + oag + MCT) for firmer per-type, density-conditioned calibration factors, and rotate the hold-out for a publishable accuracy figure.
5. Load Sabre 2025 (drop the hardened `sabre_ingest.py`, re-run `ingest_all_years.py`; paste the 2025 header if it errors on mapping).

Nick-independent build work:
- Wire `connection_builder` / `run_multihub_qsi` to pull legs per market from `oag.duckdb` via SQL (a WHERE on hubs/catchment) instead of loading xlsx. This is the step that makes the regional store drive a fast Genoa-NYC / SJC run; then re-point `goa_nyc_forecast --oag` at the store.
- Add QSI2 averaging to any script still one-directional.
- Validate the corrected QSI engine against an analyst capture workbook (Cathay HKG-SJC or EVA TPE-SJC 2024) once their OAG is in the store, and re-baseline the regression.
- Aircraft economics: ingest the Airbus maintenance reserves Excel and build the ownership leg from current OEM lease rates (see the asset map).

Deferred (good fits, wrong place to start): Knock (a catchment + leakage + stimulation problem, not a QSI-core problem; John's "if it can do this, it's solved" stress test); the catchment apportionment layer (drive-time/isochrone engine, the reusable 2011 Istanbul template is the generic method); the charges pool (compute landing/parking for circa 200 airports x dominant types from public tariffs, declared + inflated + overridable, refresh every 1-2 years; long-term, only if the product takes off).

---

## 13. Companion documents and the memory

In the project folder: this note, `Knowledge Folder Asset Map.md`, `Aircraft Economics Sourcing Reference.md`, `OAG download scope for the integrated forecasting tool.docx`, `OAG field selection.xlsx`, the Genoa deck and Sabre pack, and the drafted emails (Antonio weighting question, Nick follow-ups).

The project's memory files carry the same knowledge into any new chat automatically. The index is in MEMORY.md; the files are: qsi-project-state, qsi-open-judgement-calls, qsi-people, qsi-catchment-design, qsi-oag-scope, qsi-method-improvements, qsi-aircraft-economics, qsi-knowledge-assets. If anything in this note and a memory file disagree, the memory files plus the live code are the ground truth: verify against the current code before asserting, since point-in-time notes can age.
