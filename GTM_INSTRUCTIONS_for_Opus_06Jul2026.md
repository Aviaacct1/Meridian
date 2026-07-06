# Avia Cortex - route to market: instructions for Opus

Fable, 6 July 2026. Supersedes the priority ordering in REVIEW_Avia_Cortex_Fable_06Jul2026.md where they differ. John has settled the commercial frame; do not re-litigate it, build to it.

## Fixed commercial decisions (context, not tasks)

- Licence price anchors at £10-15k/year (RDC/OAG/Sabre shelf), plus a one-off onboarding fee and consultancy days at normal rates. Never price against study replacement.
- Data model: customer brings their own Sabre/OAG licences; Cortex ships as methodology + software + published calibration. Avia redistributes nothing. Data-rights confirmation letters are John's task, not code, but nothing installs on customer hardware before they exist.
- Deployment: offline, on-prem, one machine per licence. No SaaS, no multi-tenant work.
- Timeline: friendly-airport access from mid-August 2026 (hosted on Avia hardware, remote or supervised); World Routes stand late September 2026 with a live demo and an early-adopter programme (4-5 airports, from January 2027, free or nominal); general release after Routes 2027.
- **John's product requirement, binding: Cortex prepares BOTH annual and seasonal (summer/winter) forecasts, and the seasonal forecast must be validated, not an assumed split presented as a forecast.** Seasonal is promoted from quarter-work to launch-blocking. A tool that only forecasts annual totals does not go to market.

## Standing rules (unchanged from the 5 July review; hold them)

1. Never spend a full run on a change a --limit 100 identity check can verify.
2. Never let two model changes share one run without an attribution plan.
3. No calibration factor ships as default without two independent year-groups agreeing on sign and rough size, expressed as a capped factor.
4. Determinism recipe on every run: AVIA_DUCKDB_THREADS=1, PYTHONHASHSEED=0, --jobs for parallelism, preagg on.
5. Verify on the real local copy, never through the OneDrive mount.

---

## Phase A - foundations (week of 7 July; everything else depends on this)

**A1. Version control.** `git init` in the real local working copy (not OneDrive). First commit = current state, tagged against bt_v2_6yr_factored.csv. Thereafter: every calibration-affecting change commits with a message naming the baseline it was verified against. Acceptance: `git log` explains the last week to a stranger.

**A2. Quarantine.** Product modules stay in app/; calibration harness to calib/; one-off scripts to research/; run CSVs out of the tree; delete the dead legacy modules (avia_qsi_auto_v3, calibration_library_v8, commercial_reasonableness_engine, business_case_mode, closed_loop_pipeline_v2, connection_builder, cross_route_validator, cre_pce_bridge - confirm nothing imports them first, then delete; git makes it reversible). Fix imports, run the syntax gate. Acceptance: app/ contains only files the product needs to run.

**A3. Pinned environment.** Generate requirements.lock.txt with ==; DEPLOY_DEMO venv built from the lock file; db_registry reads store paths from one config file instead of 93 hardcoded C:\Avia paths. Acceptance: a fresh venv from the lock file serves the portal.

**A4. Calibration/runtime configuration match.** Decide the canonical water-mask state (recommendation: mask ON, it is the better science and the demo machine has it installed), then ONE confirming run in that configuration to re-verify the type-aware trim (FSC/ULCC 0.85, LCC 0.95) and re-size if the mask moves it. That CSV becomes the single canonical baseline; retire every mask-off oracle. warm_demo asserts mask state and interpreter identity at startup and refuses to serve on mismatch. Acceptance: the number the portal serves is traceable to the baseline the Track record page shows.

## Phase B - honesty surfacing (July; demo-blocking)

**B1. Feed fallback made visible.** route_feed.py silent V2-to-V1 fallback (lines circa 270/287): log the exception, stamp the forecast payload with feed_method (qsi_v2 / v1_fallback), badge it in the portal, and have backtest exclude fallback routes from grading unless --allow-fallback. Acceptance: a deliberately broken feed produces a visible badge, not a quiet number.

**B2. Induced badge.** Detect the thin/absent-history condition at forecast time (the backtest's forecastable/induced split, applied live). Induced results render with a distinct badge and framing: measured market shown, headline number suppressed, comparable-launches range shown instead (B3). Never the same visual authority as a calibrated P2P forecast. Acceptance: GOA-JFK renders calibrated; a true white-space pair renders INDUCED with a range.

**B3. Comparable-launches panel, presentation version.** From the graded 6-year store: nearest analogues by route type, haul, catchment size, carrier type, pre-existing indirect traffic; render "launches like this reached X-Y in year one; middle half A-B" with named routes. This is a lookup over data already built, not new science. The full stimulation model stays Phase F.

**B4. Confidence band on the result card (F1).** "Half of comparable forecasts landed within x1.4" on the main tile, peer basis one click away, fed from the canonical baseline (A4). Plus the prior review's cheap items: F2 resolution chips + retired-IATA aliases, M6 sanity rails (market-multiple and LF-ceiling flags into the CRE badge), F7-F10 result-card polish.

## Phase C - seasonal forecasts, first-class and validated (July-August; launch-blocking per John)

Foundation already built: seasonality_engine.season_shares (validated splits: leisure 0.72/0.28, transatlantic 0.65/0.35, flat 0.54/0.46, middle_east 0.48/0.52), route_forecast season/season_share/season_weeks parameters, /api/forecast?season=. Outstanding, in order:

**C1. One-season calibration NOW.** For routes the OAG tag marks summer-only or winter-only, the annual Sabre outturn IS the season actual, so the data is already in hand. Extend backtest to grade seasonal forecasts against these (--season-grade), producing a seasonal accuracy read by route type and haul. This is the validation John requires; run it before Routes so the seasonal claim on the stand is "graded", not "assumed". Acceptance: a seasonal row on the Track record page with its own n and band.

**C2. Season selector in the dashboard.** Annual / summer / winter on the main form, season and season_share visible on the result card, capacity shown as the season's weeks. One day of front-end work; the API already takes it.

**C3. Seasonal economics + the optimise season axis.** Thread season through aircraft_select and the P&L (_econ_block) so a summer-only service is costed on summer weeks, utilisation and seasonal ownership allocation; then give optimise a season axis so it can answer "year-round at 3/week vs summer-only daily" by economics. Use seasonality_check.py as the base. Acceptance: the Genoa case produces a coherent summer-only P&L that differs from annual/52 by more than a divisor.

**C4. Monthly profile honesty.** Until Nick's monthly 2023-2025 Sabre pull lands, the within-season profile is assumed: label it as such in the portal and methodology page ("seasonal split: OAG capacity-validated; monthly shape: assumed profile pending monthly O&D"). When the pull lands, replace the assumed profile, re-run C1, and re-grade year-round-with-peak routes (the Genoa class). Do not let an assumed profile render unlabelled.

**C5. Seasonal outputs in the deliverables.** Season columns in the workbook export and a season slide in the deck (D2). An airport pitching a summer service hands the airline a summer case.

## Phase D - Routes readiness (August; freeze circa 5 September)

**D1. Demo deployment executed.** DEPLOY_DEMO.md carried out on the actual demo laptop: C:\AviaDemo, lock-file venv, OneDrive out of the path, warm_demo green, D1-D10 checklist walked twice. Rehearse the failure lines (D4 wrong-resolution recovery, D5 thin-GDS pivot).

**D2. Deck generator v1.** HANDOVER_Deck_Generator.md scope: full .pptx route case (BA SJC quality bar) from a forecast payload - forecast, catchment, QSI shares, seasonality, P&L, methodology annex. Plain first version; it is the take-away product. Acceptance: one command from a forecast to a deck John would put in front of an airline.

**D3. Friendly-airport access (mid-August).** Hosted on Avia hardware only (remote session or supervised): force a non-default AVIA_PASSWORD, unique per airport; access log; demo dataset scoped to their region. No induced cases in their hands unsupervised. Collect structured feedback (what confused, what they'd pay for, current study/subscription spend).

**D4. Stand collateral support.** Demo script covering the four case types (underserved, reinstatement, seasonal summer-only, honest-band story); a one-page early-adopter programme sheet; the five-minute spend survey. Content is John's; Opus builds the demo tables and keeps warm_demo loading them.

## Phase E - early-adopter productisation (October-December; install-blocking)

**E1. Customer-extract ingestion path.** The main engineering gap between demo and product: documented loaders that build sabre.duckdb/oag.duckdb equivalents from a customer's own MIDT and OAG extracts (their scope, their licence), with schema validation, coverage checks, and the preagg build wrapped in. Acceptance: a synthetic "customer extract" round-trips to a working forecast on a clean machine.

**E2. Install story.** Scripted installer or documented build: pinned venv, config file, licence key (simple signed file; no telemetry beyond an optional licence ping), forced password on first run, db_registry.reset() wired to the data-reload path. Target: an airport IT generalist installs it in an afternoon with the guide.

**E3. Pilot-hardening.** Parameterise SQL (or enforce ^[A-Z0-9]{3}$ at the API boundary), lock LAST_FC/PITCH_JOBS, report-currency layer (dated rates CSV, stamped on outputs), pytest suite for the pure functions (QSI scorer fixtures, market_factor_for, season_shares, preagg SQL vs the synthetic store).

**E4. Documentation set.** User guide, methodology document (the canonical claim from M4 stated plainly), data-ingestion guide, quarterly recalibration runbook. The Track record page is the marketing; keep it aggregate (never ship per-route calibration CSVs - data rights).

## Phase F - the induced model (Q4 2026 - Q1 2027; the hard one, after Routes)

Comparable-market distribution model over the graded launch library (B3 made quantitative): analogue selection, range estimation, presented as a range with named comparators, graded against the induced slice of the back-test. Do NOT attempt a gravity-model stimulation coefficient first. Ships when it beats the current median 0.14 under-read on held-out years - if it does not, the honest INDUCED badge remains the product answer.

## Explicitly deferred (do not spend runs on these)

- Reinstatement discount: fails the two-year rule (118 routes, one year); revisit when 2025 outturn firms up.
- Coverage gross-up recalibration: add the user override (one day, Phase E3 scope), recalibrate later.
- mct_banking: stays parked.
- Any SaaS/multi-tenant work, per the fixed decisions.

## Sequence summary

July: A1-A4, B1-B4, C1-C2. August: C3-C5, D1-D3, freeze 5 September. September: rehearse, Routes. Q4: E1-E4, F, pilots signed for January 2027.
