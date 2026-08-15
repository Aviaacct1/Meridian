# Handover: 16 August 2026

Version 1.0, written 15 August late evening. Avia Solutions. Read this, then
`bt2/bt2_experiments.log` from K-SWEEP-RESULT (15 August), most recent last. The 15 August
session was long and closed a great deal; this records what stands and what is owed.

---

## What 15 August closed, so nobody reopens it

**The k question is decided and implemented.** The paired six-arm sweep on the pinned set
(E:\Avia\ksweep_15Aug) measured the V2 QSI feed unable to beat the V1 control on the
connecting leg at ANY k (within 20%: 6.0-8.3% across 16.7x of k; V1 8.2%, median 1.01),
and the pre-registered rule fired. John's decision: **V1 carries the level, V2 keeps the
timing** (optimiser, curfew cost, banks; that path never read the qsi_feed flag). Rollback
is `AVIA_FEED_LEVEL=qsi`, no code. The evidence and the product are now the same machine,
which closes the claims-arm mismatch in the evidence's favour. `bt_v1_control.csv` is the
shipped-configuration reference arm. Do not quote k=1.0's connecting median of 1.08 as
vindication: capped numerator, residual denominator, both caveats in K-SWEEP-RESULT.
John's hand-tuned k=0.26 matched the back-test's 0.235 best cell independently.

**The independent review** is at `REVIEW_Meridian_Fable_15Aug2026.md`: show at Routes
(21-23 Oct, Frankfurt), founder-airport beta, launch November, do not sell in October.
R3-R10 (silent failures, provenance, proxy fare, seats basis, cabin sentinel) are all
FIXED and pushed; payloads carry `warnings[]` and `feed_level.basis_ran`; the portal
renders warnings; `deck_from_cases` refuses warned runs unless `--allow-warnings`.

**Shipped and verified on the workstation:** all fixture tests pass there
(`test_feed_provenance.py`, `test_refresh_pickup.py`); `deck_from_cases cases_sjc_tpe.json
--report-only` runs 16 of 16 clean with warnings empty (needs `AVIA_FREQ_SENSITIVE=1`,
which `Meridian-run.bat` now sets); Route Watch is live against real data.

**Also built 15 August:** easy-view additions (seat count box, stimulation posture chip,
floor moved to Expert, Expert split into Judgement / Calibration behind a confirm);
departure chart P2P shaded band, year and basis on the SVG; Route Watch page (+ names
beside codes, DOT T-100 demand trend for US airports, monthly-label fallback matching
Jess's template); `refresh_pickup.py` core with manifest, vintage guard and seven passing
tests; `Meridian-run.bat` launcher; the Routes stand design brief
(`Observatory_Routes2026_stand_brief.docx`); the four-questions note
(`Meridian_four_questions_15Aug2026.docx`: UI, chart, PaxUp, pricing).

---

## OWED FIRST: the acceptance run (ten minutes, do before anything else)

The 6x/85k run John saw was NOT the acceptance case: optimiser-chosen carrier (B77W 358),
default year, floor ON. The acceptance case is: **SJC-TPE, airline CI, aircraft A359, seat
count 306, forecast year 2028, curfew 21:00-06:00, frequency blank, Expert -> Show
calibration constants -> Connectivity floor OFF, Optimise.** Pass mark: 4-5x weekly,
total circa 110-135k two-way (John's historic testing, the 2025 analyst's 107.9k, and the
0.235/0.26 k agreement all point there). If it fails, read `feed_level` in the payload
(level_engine must say v1), then investigate before building anything; rollback exists.

While there, two small checks: the slider line's load factor should reconcile with the
capacity block (an 82.6% against a 358-seat 6x schedule did not obviously, 15 August),
and the contract field count read 52 of 56 against 13 August's recorded 53; same four
named gaps, so likely a stale count, but confirm which.

## Job 1: the Watch page visual layer (John: "stunning visuals are a Meridian basic")

Charts to the Observatory data-visualisation standard (brand guidelines v1.1: brass is
the observed line, ink dashed for comparators, direct labels never legends, registration
ticks, the Inter provenance rail under every figure with source/units/period/method).

- **Daily scheduled seats, this year against last**: from the oag store's `days_of_op`
  and `frequency` for the airport's two snapshot labels (route_watch.pick_weeks already
  returns them); x = day of week or date, two series. This is the chart an ASD team
  opens Monday with.
- **Monthly traffic against the same month last year**: T-100 monthly for US airports
  (store at config.T100_DUCKDB, read only the `seg` table, scheduled class; see
  airport_profile.read_t100's docstring for the traps), ACI/store equivalents elsewhere
  as available; label the vintage.
- Serve as a new `/api/watch/series?airport=` endpoint; draw inline SVG in
  cortex_watch.html in the house grammar (the dashboard's curve code is the pattern).
- Watch page also owed: a "store freshness" line reading refresh_status.json (the
  refresh_pickup wrapper writes it), so September's unwatched test is visible.

## Job 2: Cloudflare access for the six testers

The portal must never be naked on the internet. Order: (1) `AVIA_PASSWORD` set in the
workstation portal environment (login gate returns; NOT in the repo, secrets stay out of
git). (2) A named cloudflared tunnel on the WORKSTATION -> localhost:8010, installed as a
Windows service so it survives reboots. (3) Cloudflare Access policy on the hostname
allowing the testers' email addresses only. NEEDED FROM JOHN before commands can be
written: which hostname on which Cloudflare-managed domain (e.g.
meridian.aviasolutions.com), and the tester email list. Also set ANTHROPIC_API_KEY on the
workstation (`setx`, new key named "workstation" from console.anthropic.com, Settings ->
API keys) so the Watch briefing works.

## The week to 27 August (John's deadline: full working model, then holiday; six-analyst
## beta while away; possibly Bologna or Bristol as a friendly airport)

1. Acceptance run + the two small checks (above). TODAY.
2. Watch visual layer (Job 1). 1-2 days.
3. Cloudflare + password + API key (Job 2). 0.5 day once the hostname is named.
4. Forecast pack Job 2 corrections (HANDOVER-15Aug2026.md carries the list: slide-32
   table columns incl. pre-stimulation forecast-year demand, disclaimer naming The
   Aviation Observatory, airport-code columns, images via SlotResolver, catchment map
   with population). 2-3 days.
5. Track-record page: bt_v1_control.csv as the shipped-configuration arm beside the
   claim set, both bases labelled. 0.5 day.
6. The floor question, measured not argued: with V1 level, is split_floor ON still right
   as default? RECONCILIATION-INVERTS says floor-off is closer on SJC-TPE; the v1_control
   arm ran floor as-shipped. One A/B on the pinned set answers it. 1 day.
7. Routes one-route-per-email flow (demo lead capture: run route -> email HTML pack, one
   per business email, consent tick, demonstration watermark; deck refusal machinery
   already protects it). 2-3 days. Needed for testers anyway if they self-serve.
8. Refresh commissioning: catch OAG/Sabre up to end July WATCHED via refresh_pickup
   (--plan-only first, paste the plan), then wire the weekly scheduled task + portal
   stop/start bracket with db_registry.reset(). 1 day + Jess's downloads.
9. Tester onboarding: six analysts, access notes, feedback form. 0.5 day.
10. John personally: stand booking decision with Charlotte (hold a stand), brief to the
    brand team, redistribution/PI/legal quotes in motion, the analyst footnote question
    (FOOTNOTE-TENSION-UNRESOLVED), tester email list, Cloudflare hostname.

September (parked, deliberate): V2 spread work (per-market bounds, behind mechanism,
competition split) default-off and back-tested first; the local-leg under-read (0.56
median, the real accuracy frontier); monthly Sabre template with Jess + vintage guard
already coded; display currency; PaxUp price discovery at Routes.

---

## Do not disturb

The level/timing split ships as decided; do not re-litigate k without new measurement.
The published claims stay. The half-year OAG union stays off behind AVIA_BT2_HALFYEAR.
origin_share 0.62 / business_share_destination 0.22 remain John's placeholders, named.
avg_ow_fare_connecting, cask, ancillary_revenue remain empty and named (the fare check
against measured Sabre is still owed before any client deck with a revenue page).

## Working rules

Verify, do not assert; state each number's basis before comparing. Follow a field to
where it is set. House style throughout, including code comments. Ask before running
anything over circa twenty minutes. Fixture tests for anything testable without stores.

Avia Solutions Limited. All rights reserved.
