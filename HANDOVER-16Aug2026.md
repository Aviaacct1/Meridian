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

## ~~OWED FIRST: the acceptance run~~ DONE 15 August late night: PASSED

**The acceptance case passes: CI, A359, 5x weekly at a planned 82.8%, 131,812 two-way at
forecast 2026; steady-state equivalent 121,151, inside the historic 110-135k band; circa
143k at the 2027 default, inside John's 135-145k.** The engine and the k decision were
never the fault. Full account in `bt2/bt2_experiments.log` from ACCEPTANCE-CLOSE: the
Schedule box is the SEASON picker and Unselected let the optimiser run seasonal totals
(which also closes the LF check: the slider reconciles exactly on season weeks); the
forecast-year feature was growing the market at a 20%-clamped post-COVID rebound CAGR;
the pass mark predated the feature.

Two rulings shipped on the back of it (COMMIT-MSG-15Aug2026-forecastyear / -growthtrend):
default forecast year is the next full calendar year, and market growth is the 2015-2019
pre-COVID trend via `market_trend()`, one definition, two-way pair sum, cached (the old
measure scanned the store twice inside every optimiser arm). New diagnostic
`app/sabre_directionality_check.py`: 2013/2015 are POO, all else ND; never measure
cross-year growth one-directional across 2015/2016.

Still owed from the checks: the contract field count (52 v 53 of 56, name the four gaps),
the canonical store root (the workstation resolves C:\Avia\sabre.duckdb; records say
E:\Avia), and the label batch: season and year on the slider line and headline, the Watch
demand header when it serves T-100, the Schedule box renamed to Season.

## Job 1: the Watch page visual layer (John: "stunning visuals are a Meridian basic")

SCOPED 15 August in session, so the next session starts at the build, not the reading:
the daily-seats chart is DEPARTING seats by day of week (John approved; two-way double
counts a based rotation), basis stated on the chart. days_of_op is a seven-character
mask (digits 1-7 = operating days) and the store repeats one schedule record per region
label, so DEDUPE by (carrier, flight_no, dep, arr, dep_time) taking max(mask) BEFORE
summing seats, the capacity_frame.py fix. T-100 monthly reader: follow read_t100's
rules (seg table BY NAME, class F only, origin = departing onboard) but GROUP BY month;
the existing reader is annual. refresh_status.json is {source: {label, result, detail,
date}} at AVIA_REFRESH_STATUS, default E:\Avia\refresh_status.json. Chart grammar: copy
cortex_dashboard.html's season plate (registration corner ticks, PAL constants, brass
observed, ink dashed comparator, direct labels, Newsreader italic annotations) and its
provRail()/.prov CSS for the rail; John approved bringing the Observatory tokens and
fonts into cortex_watch.html, which still runs the old Georgia/#B8860B palette. Fold in
the label batch while in the file: the Watch demand table header must say T-100 when it
serves T-100 (header is hard-coded "Sabre vintage"), the season/basis labels on the
dashboard slider line, and rename the dashboard's "Schedule" box to "Season".

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
- STANDING PRODUCT RULING (John, 15 August, applies to EVERY demand figure including
  these charts): US airports speak in DEPARTING passengers, the rest of the world in
  TWO-WAY. Show both bases everywhere, the measured one plain, the derived one marked ~
  with the factor stated. Already implemented on the Watch demand table; carry it into
  the charts and anywhere else a passenger total appears.
- SECOND STANDING RULING (John, 15 August): dates in HUMAN text spell out as
  DD Month YYYY ("25 May 2026"), because readers span three continents; ISO YYYY-MM-DD
  stays in machine contexts only (payload fields, manifests, the mono provenance rail,
  where the brand guidelines want it). route_watch.pretty_label() is the helper; use it
  on every label a person reads, including chart axes and titles.
- Also verify on a real airport that the demand table's passenger NUMBERS render; on
  John's 15 August screenshots the year rows showed but the figures were not visible,
  which is either a cropped screenshot or a rendering defect. One look settles it.
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

1. ~~Acceptance run + the two small checks.~~ DONE 15 Aug late night, PASSED (see the
   rewritten section above). Still open from the checks: contract field count, canonical
   store root, the label batch.
2. Watch visual layer (Job 1). 1-2 days. NEXT.
3. ~~Cloudflare + password + API key (Job 2).~~ DONE 15 Aug late night, built live in
   John's dashboard: meridian.aviacortex.com -> workstation:8010 and
   atlas.aviacortex.com -> workstation:8000 on the ask-avia (workstation) tunnel, both
   behind Access apps sharing the reusable "meridian" email policy (seven addresses)
   with One-time PIN enabled; verified end to end from the Dev PC (OTP -> Observatory
   sign-in). globalforecast retired: Public Bypass app deleted, route and DNS removed.
   ANTHROPIC_API_KEY set on the workstation. REMAINING: John confirms the origin gate
   (setx QSI_PASSWORD + QSI_DEMO_ENTRY=0, restart, console lines; a WRONG password must
   be rejected), and optionally renames the tunnel to "workstation".
4. Forecast pack Job 2 corrections (HANDOVER-15Aug2026.md carries the list: slide-32
   table columns incl. pre-stimulation forecast-year demand, disclaimer naming The
   Aviation Observatory, airport-code columns, images via SlotResolver, catchment map
   with population). 2-3 days.
5. Track-record page: bt_v1_control.csv as the shipped-configuration arm beside the
   claim set, both bases labelled. 0.5 day.
6. The floor question, measured not argued: with V1 level, is split_floor ON still right
   as default? RECONCILIATION-INVERTS says floor-off is closer on SJC-TPE; the v1_control
   arm ran floor as-shipped. One A/B on the pinned set answers it. 1 day.
7. Routes one-route-per-email flow. 2-3 days. Needed for testers anyway if they
   self-serve. SCOPED IN FULL 16 August (decisions taken with John); build spec below,
   so the next session starts at the first line of code.
   BUILT 16 August, fixture-tested (58 checks in app/test_demo_flow.py; commit owed:
   COMMIT-MSG-16Aug2026-demo-flow.txt). demo_leads / demo_mail / demo_pack, the four
   endpoints + /demo/leads admin page, the dashboard offer, and the render_observatory
   _bullets fix the first HTML pack render surfaced. The live send still waits on the
   aviationobservatory.com mailbox (item 10); until then a send fails loudly and the
   lead is recorded as failed. Workstation still owed: a real end-to-end run and one
   pack eyeballed for the watermark and page set.

   ## Item 7 build spec (16 August, John's decisions inline)

   THE FLOW. After a clean run, the dashboard offers "Email me this forecast": business
   email field + consent tick (marketing consent, stored with the lead). Server builds
   the HTML forecast pack for THAT run, stamps it DEMONSTRATION, and emails it as a
   self-contained attachment. The pitch-jobs pattern (PITCH_JOBS + polling in
   cortex_app) is the template: build in a background thread, the page polls, "sent"
   is the terminal state. The performance memory rules this explicitly: the HTML pack
   may run long and is SENT AFTER, never held on a spinner.

   QUOTA (John's ruling, 16 August): one pack per email PER ROUTE, with the FIRST pack
   free and automatic. Any further request from the same email is HELD PENDING with the
   person's history beside it (what they already had, when), and needs an in-system
   override by the Avia team before it sends. Rationale, his words: one-ever is too
   inflexible (someone meets an airline in 20 minutes and wants 3 routes), but the team
   must never route around the system by making packs and forwarding them, because
   tracking of who got what is the point. The override is therefore ONE TAP on an admin
   page, not a workaround.

   THE PIECES:
   - app/demo_mail.py: M365 SMTP transport (John's choice). smtp.office365.com:587
     STARTTLS. Config from env / the gitignored secrets file, NEVER the repo:
     AVIA_SMTP_HOST (default smtp.office365.com), AVIA_SMTP_PORT (587),
     AVIA_SMTP_USER (the sending mailbox), AVIA_SMTP_PASS. Sender = user. Fail loudly
     with the reason; a failed send leaves the lead recorded with status failed, never
     silently dropped.
   - app/demo_leads.py: the lead store, JSONL at AVIA_DEMO_LEADS (default
     E:\Avia\demo_leads.jsonl; data on the workstation, never in the repo). One line
     per event: ts, email, domain, route, run reference (payload hash or case line),
     consent, status (sent / pending / approved+sent / declined / failed), approver,
     pack filename. The quota check and the history read from this one file.
   - Business-email check: reject the free-mail domains (gmail, outlook, yahoo,
     icloud, proton, etc: a named list in demo_leads.py, editable) with a polite line;
     the demo exists to capture airlines and airports, not hotmail.
   - Endpoints in cortex_app: POST /api/demo/request (validates, quota-checks, builds
     + sends or holds pending; returns the state and, when pending, says so honestly);
     GET /api/demo/leads + POST /api/demo/approve for the admin page; admin page
     /demo/leads behind the existing origin gate (it is already behind Cloudflare +
     QSI_PASSWORD), listing pending requests with history and one-tap Approve /
     Decline. Stand team uses it from a phone.
   - THE PACK: the HTML forecast pack for the run. pitch_html.py renders the
     researched pitch; the demo pack is the FORECAST pack (the 9-page set, John's
     14 Aug ruling) rendered to HTML. If an HTML renderer for the forecast pack does
     not exist yet (check deck/render paths), the first build target is
     forecast_pack spec -> HTML, reusing deck_spec + the dashboard's house CSS.
     DEMONSTRATION watermark: a fixed banner + diagonal watermark in the HTML, and
     "Demonstration" in the title block; not removable by deleting one element.
   - REFUSAL WIRING: a warned run is never emailed (deck_from_cases' rule: the portal
     warns, a client artefact refuses). The request endpoint checks the payload's
     warnings[] and refuses with the reason.
   - Tests, no stores needed: quota logic (first free, second pending, override
     sends, per-route semantics), the domain check, the lead-store round trip, the
     watermark present in rendered HTML, refusal on a warned payload. Mail transport
     tested with a fake SMTP class, never a live send.

   THE SENDER (John, 16 August): **meridian@aviationobservatory.com**. NOT yet up and
   running, and it is a NEW DOMAIN, so the go-live list is longer than a mailbox:
   domain added and verified in the M365 tenant, mailbox created and licensed, SMTP
   AUTH enabled for it, SPF (include:spf.protection.outlook.com), DKIM enabled for the
   domain, a DMARC record, then AVIA_SMTP_USER / AVIA_SMTP_PASS on the workstation
   (setx, new window). A brand-new domain emailing cold recipients at Routes will land
   in spam without SPF/DKIM/DMARC, and ideally sends a trickle of ordinary mail for a
   couple of weeks first, so this list wants doing WELL BEFORE October, not the week
   of the show. None of it blocks the build: the mail module reads config and is
   tested against a fake transport; the live send is the only thing waiting.
8. Refresh commissioning: catch OAG/Sabre up to end July WATCHED via refresh_pickup
   (--plan-only first, paste the plan), then wire the weekly scheduled task + portal
   stop/start bracket with db_registry.reset(). 1 day + Jess's downloads.
9. Tester onboarding: six analysts, access notes, feedback form. 0.5 day.
10. John personally: stand booking decision with Charlotte (hold a stand), brief to the
    brand team, redistribution/PI/legal quotes in motion, the analyst footnote question
    (FOOTNOTE-TENSION-UNRESOLVED), tester email list, Cloudflare hostname.
    ADDED 16 August, THIS WEEK because deliverability needs the lead time, not because
    the build does: set up aviationobservatory.com correctly, end to end, per the item 7
    spec's go-live list: domain registered and added to the M365 tenant, DNS verified,
    the meridian@ mailbox created and licensed, SMTP AUTH enabled for that mailbox, SPF
    (include:spf.protection.outlook.com), DKIM enabled for the domain in Defender/EAC,
    a DMARC record (p=none to start is fine; the record existing is what matters), then
    AVIA_SMTP_USER / AVIA_SMTP_PASS on the workstation via setx. From then until
    October, a trickle of ordinary mail from the mailbox so the domain has a sending
    history before it emails cold prospects at Routes. Done this week, the stand demo
    lands in inboxes; done in October, it lands in spam.
11. Small correction owed in Observatory_Routes2026_stand_brief.docx before it goes to
    the designers: section 3's fascia line said Avia Solutions to match the diaries;
    John ruled 15 August that the exhibitor registers as The Aviation Observatory, so
    fascia, diary and panels all carry the Observatory name, with "An institution of
    Avia Solutions" as the masthead line. The stand concept v0.1 is right as drawn; the
    15 August critique's other five changes (screen as hero, self-serve to the aisle
    edge, the QR beyond the stand, Atlas to the screens, lighting and stools) stand.

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
