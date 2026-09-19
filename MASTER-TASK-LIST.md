# Meridian master task list

**19 September 2026: World Routes (21-23 October) now governs sequencing.** The umbrella is
`GTM-STRATEGY-ROUTES-2026.md` (decisions, two milestones, integrated timeline, pre-mortem). The launch-readiness
strategy, calendar and workstreams are in `HANDOVER-ROUTES-19Sep2026.md`, with a kickoff prompt in
`PROMPT-for-Fable-Routes-19Sep2026.txt`; the commercial side (sales, pack and imagery, host
manual, pricing, leads and feedback, website, marketing, meetings, competitors) is in
`ROUTES-COMMERCIAL-PLAN-19Sep2026.md`. That note supersedes the freeze calendar and the
"after Boeing" build queue below: speed (preagg switch-on, persistent cache, pre-warm), the
request-queue-with-email demo tier, stand mode, the laptop-build proof and the stand deck come
first; the engine items (4.1, 4.4) stay post-Routes. Website: 1.7 resolved 1 September (editor
lists all 24 pages, saves to main); `markets`, `benchmarks`, `data` have zero inbound links, decide
at launch; reinstate a review branch with a preview when the IT firm takes the site live.

Started 29 August 2026, on John's instruction that every open job lives in one place. This file
is the register: a job exists when it is on this list, and it closes here with a date and where
the evidence is. Update it in the session that opens or closes a job, commit with the work.

Calendar constraints the ordering respects: John away to 16 September; changes 27 August to
mid-September are exceptional and remote-approved only; HARD FREEZE mid-September through World
Routes (early October); Boeing demo 13 October. Engine work therefore lands after 13 October
unless John rules otherwise.

## 1. Open now, remote-safe (may move while John is away)

- **1.1 Workstation pull of the aircraft-econ commit.** Behaviour-identical bar the CRJ900
  cargo line (0 -> 2,756 kg, sourced). John's call on timing mid-beta. Evidence when done: a
  pulled workstation and one forecast run clean.
- **1.2 job_watch cross-page cancellation bug.** Background optimise job appears to die when a
  user types on Track Record or Economics. Blocked on one diagnostic: what
  `/api/optimise/status?job_id=<the one that died>` returns when it reproduces (error /
  cancelled / still running decides server-kill vs display-loss). No fix attempt until then.
  Open since 24 August; testers may hit it.
- **1.3 Tester feedback intake.** Collect as it arrives against TESTERS-KNOWN-ISSUES-23Aug2026.md
  and JAREK-FEEDBACK-24Aug2026.md; triage on return. Jarek's is triaged and prioritised
  (JAREK-FEEDBACK-PRIORITISATION-24Aug2026.md, John's visual-first ruling inside).
- **1.4 Range/payload advisory did not surface for Antonio (30 August).** He ran a 7M8 on
  BLQ-JFK and saw no warning. VERIFIED 30 August: the machinery exists end-to-end and should
  have fired - the sector is 6,647 km against the B38M's 6,500 km book range, ratio 1.023,
  which lands the top band ("AT THE LIMIT... expect a payload restriction in normal winter
  conditions"), and the dashboard has a banner that renders exactly that message. So either
  `_attach_range_margin`'s bare try/except swallowed a failure in silence (the silent-fallback
  shape; likely candidate is the catchment origin_ll read), or the banner rendered and was
  missable. DIAGNOSTIC, 30 seconds when convenient: run Bologna -> New York, aircraft B38M,
  no airline, Run assessment, and look for the RANGE banner above the KPIs. Banner absent =
  code path bug, fix the except to report; banner present = a visibility question for the
  UX-overwhelm pass (2.5). Do not fix blind during the freeze.
- **1.5 Basic-auth username is ignored (Antonio, 29 August).** He signed in with the dummy
  you@carrier.com left in the username field and the shared password, and got in. By design
  today: the per-user gate is Cloudflare Access (email OTP), the Basic auth is a shared second
  factor and its username field validates nothing. Two follow-ons, neither urgent: state in the
  tester instructions that the username field is cosmetic, or validate it; and confirm the R9
  usage log attributes users from the Cloudflare identity header, not the Basic-auth username,
  or per-user attribution (the usage-data asset, 5.7) is recording you@carrier.com.
- **1.6 Jol's website-editor access (1 September).** OAuth to the editor fails with "no access
  to avia-website": the GitHub account he authorised with lacks collaborator access at the
  moment of authorising. Diagnostic sent 1 September (signed-in account check; direct visit to
  github.com/Aviaacct1/avia-website, 404 = invite pending or wrong account; revoke the OAuth
  app and retry if the repo is visible; popup blocker explains the dead first click). John's
  check from anywhere: repo Settings -> Collaborators, is Jol accepted, pending, or absent,
  and under which username. RESOLVED 1 September: Jol is in after trial and error; superseded
  by 1.7.
- **1.7 Website editor does not mirror the live site (Jol, 1 September).** The admin editor at
  website.aviacortex.com/admin shows pages and text bearing no resemblance to what
  website.aviacortex.com displays (e.g. the About page). Two candidate causes, different fixes:
  the live site is serving an older build and the deploy pipeline is not rebuilding on push
  (pipeline setting), or the editor's admin config points at content files the site's templates
  do not render (config fix in the repo). Needs a session with the avia-website clone, which is
  not in the current mounts. Jol told 1 September: click Discard on the local-draft prompt, and
  HOLD ALL REWRITES until the mirror is confirmed, or good copy goes into the wrong files.
  Jol's substantive finding stands regardless: the draft site copy "needs a complete rewrite",
  which is the review the estate register says the site is awaiting.

## 2. Decisions, no code (unblock capability from anywhere)

- **2.1 Valuation source: IBA / Cirium / EETC.** The single blocker between the 26 new aircraft
  types and being costable. Decision plus data acquisition; the loader takes the columns the day
  they fill.
- **2.2 Stefan query: burn basis on the 22 held types** marked "UNSTATED - do not convert;
  query" in aircraft_econ.csv. Answering retires the carve-out label ("basis unstated, under
  query") from live output. If any answer is TRIP, that type's burn becomes missing by rule -
  price that consequence when the answer lands.
- **2.3 Stefan query: A31N.** Seats (180 recorded vs A319 exit limit 160) and cargo (recorded as
  volume, not hold weight). Row stays status `open`, fields refused at load, until resolved.
- **2.4 The accuracy question (estate index, open since 8 August).** Whether the published 89%
  within +/-20% / 82% within +/-10% describes what a client is shown: the figures are BT2's,
  the app forecasts with the QSI engine. Either the product forecasts with BT2 or the QSI engine
  is scored on the BT2 basis. John wanted this settled in days; it predates the beta. Ask the
  same question of Atlas before the OGF is sold.
- **2.5 UX-overwhelm design question.** How the coming visual depth (2.x below, item 4.2)
  sits on the dashboard without burying a first-time user. Progressive disclosure is the agreed
  direction (the market background strip is the template); the actual design ruling is John's,
  and it gates the visual build, not the other way round.

## 3. On return, before the freeze bites (16 September to ~mid-September window is thin;
## most of this is triage, not build)

- **3.1 Tester comments.** John's stated first job on return.
- **3.2 Day-of-week allocation SPEC (not build).** Ruled "properly, very soon" (24 August);
  engine work, so the build waits for after Boeing unless John overrules his own freeze. Ready
  when the build starts: `days_of_op` confirmed present in the OAG store; the tail chart is
  week-native with the engine seam built (`tailPattern()` reads `schedule.operating_days` the
  day the engine sends it); memory note `meridian-day-allocation-backlog` has the data caveats
  (Sabre demand carries no day-of-week; allocation basis needs deciding, likely OAG's own
  day-pattern as the weighting proxy, stated as such).
- **3.3 Methodology follow-ups for Nick.** (a) Expect the hardest probing on the induced-demand
  floor (note section 4.4); an expansion of when it triggers, the supporting sample and whether
  it can dominate a small market is drafted-on-request. (b) UNANSWERED: whether the old
  `Avia_Cortex_Process_and_Methodology.pptx` (2 July, project folder) overlaps or contradicts
  the new note; check before Nick works from both.
- **3.4 Curfew UI polish.** The inverted-entry guard shipped 24 August; remaining from Jarek's
  report: confirm the theoretical-optimum figure reads as theoretical at a glance on the page
  (labels exist; a first-time-user check, not a build).

## 4. After Boeing (13 October), the build queue in John's ruled order

- **4.1 Day-of-week allocation, the build** (from the 3.2 spec). Frequency allocated to real
  days; feeds the tail chart's dormant branch; updates the testers' known-issues list item 2.
- **4.2 Visual quick wins** (John's visual-first ruling, 24 August): interactive routing maps,
  hover detail on origin/destination/connection points, dynamic behind/beyond routing visuals,
  export completeness for charts and visuals. Each scoped for genuine quick-win effort before
  committing; gated on the 2.5 design ruling. (The market background panel and tail chart,
  the first two of this family, shipped 24 August.)
- **4.3 Product items, no methodology risk:** OAG week / Sabre year selection plus a comparison
  tab; MCT/terminal manual override exposed as a scenario input; save/load scenarios (JSON
  down/up); user/market permissions and Expert Mode behind a permission (needs a user model;
  currently one shared password).
- **4.4 Engine phase: fare into the QSI capture score, and an aircraft-type coefficient.**
  Strongest methodology precedent on Jarek's list (Profit Essentials factors; named gaps in
  Avia's own 2021-23 post-pandemic notes), deferred behind visuals by John's ruling, not on
  merit. Both touch the capture score; build together. Note the industry caution: yield
  calibration is route-specific and expensive; aircraft-type carries a small coefficient range
  and must not be oversold.
- **4.5 Aircraft-required refinement.** The tail chart states the count; Jarek also wanted it as
  a stated output item in exports. Small, rides with 4.2's export work.
- **4.6 Cannibalisation / share-of-total-market reporting.** Was a stated OUTPUT of the
  pre-Meridian methodology; verify what Meridian already produces before scoping as new work.
- **4.7 Return-leg curfew search.** The return leg is drawn, flagged when it lands inside a
  restriction; a proper search within the curfew is the finish. Display/schedule layer.
- **4.8 Per-side connection exclusion (Antonio, 30 August).** "What if we assume no connections
  beyond BLQ?" A scenario control to switch off either feed side (behind the origin / beyond the
  destination) for a conservative or P2P-only case. The engine half-exists: feed_behind_cap=0
  kills the behind side from Expert mode; the beyond side has no exposed zero and neither is a
  labelled scenario control. Small build, real analyst need, output must state the exclusion on
  the page and in every export.

## 5. Parked, revisit deliberately (not scheduled)

- **5.1 Double-stop QSI module.** Real Avia precedent (TPE) but rare in use; nice-to-have.
- **5.2 Sensitivity / Monte Carlo on fare and frequency.** Only sensible once fare is in the
  capture score (4.4); no industry-standard precedent found in the reviewed documents.
- **5.3 Fully agentic assistant.** Direction only, no detail given.
- **5.4 Fixed-departure curve backlog.** A fixed dep_time kills the departure curve; the SJC
  workaround (widened curfew) stands; real fix is a chosen time still showing on the curve.
- **5.5 Long-run feedback loader** (Observatory radar for runs over 10s). Design is NOT in the
  repo; find it before rebuilding it.
- **5.6 Fleet delivery layer** (airline, type, year) so a 2028 forecast knows the 787-10;
  Mark/SJC ask, own forward OAG filings as the source.
- **5.7 Usage-data asset.** Route-search history as a data asset; consent banked via ToU;
  commercial/ethical question parked with counsel.
- **5.8 Engine V2 legality inversion.** The 9 red checks in test_qsi_feed.py; the feed is
  permanently gated off on the live path (level = V1 flat by the 15 August k-decision), so this
  is only worth fixing if Engine V2 is ever revisited.
- **5.9 Legacy regression harness (test_regression_v2.py).** Runs only with Egnyte mounted;
  documents the 2013 assembly with the uncalibrated raw feed (4.0x). Historical reference, not
  a target; retire or re-target deliberately, don't chase the reds.
- **5.10 Working-tree housekeeping.** Untracked COMMIT-MSG/PROMPT/diag files and two modified
  working files (HANDOVER-23Aug2026.md, diag_tpe_sjc_catchment_decomp.py) on the DevPC; sweep
  into a tidy-up commit deliberately, not blind.

## 6. Verification checks owed (quick, but a run is not verified until its check is done)

Each is minutes of work at the live tool or the DevPC; they exist here so none of them relies
on anyone's memory. Tick off with a date and what was seen.

- **6.1 BLQ range-banner diagnostic** (the 1.4 case, Antonio). Bologna -> New York, aircraft
  B38M, no airline, Run assessment. Banner above the KPIs = visibility question; no banner =
  the advisory's bare try/except swallowed a failure and the fix is to make the except report.
- **6.2 Market background live checks, 24 August batch.** The panel is confirmed working in
  general (John, live, 24 August), but three specifics were never individually confirmed:
  the carrier-share cell on SJC-TPE (real data, or the honest "this Sabre extract holds no
  carrier column" note - tells us whether the store carries a carrier field); the first
  uncached brief's load time on the workstation; Genoa-New York as the second route.
- **6.3 Inverted-curfew guard live.** Enter Jarek's exact 05:30-23:00 curfew at the origin and
  confirm the run stops with the swap message reading well on screen.
- **6.4 Caller-set return arrival live.** Set a Return arrival, confirm the schedule line reads
  "return arrival HH:MM set by the caller; departure derived from it", and try one infeasible
  arrival to see the "needs a second aircraft or an earlier outbound" flag.
- **6.5 Tail chart on both sector lengths.** One long-haul run (SJC-TPE: expect 2 tails) and
  one short-haul (expect 1 tail, mostly-free row); confirm the pattern basis line reads as a
  labelled working assumption at sub-daily frequency.
- **6.6 Aircraft-econ commit on the workstation.** Pull, restart, one forecast on a CRJ900
  route if convenient (the one behaviour change: a small cargo line appears, table-sourced
  2,756 kg vs the old placeholder 0); /api/aircraft should list 42 types plus known_uncostable.
- **6.7 DevPC record of the two head-of-suite tests.** test_aircraft_econ_table.py (expect
  "42 checks, 0 failed") and test_economics_wiring.py scrolled off the 29 August foreach paste;
  they passed in the sandbox on the same files, but the DevPC record was never sighted.
- **6.8 R9 usage-log attribution** (the 1.5 case). Confirm the log attributes users from the
  Cloudflare identity header, not the Basic-auth username, or every tester is recorded as
  you@carrier.com.

## Closed since this list began

(record closures here with date and evidence)
- 29 Aug 2026: aircraft economics table-driven per the tool standard; 42-check rule-lock test;
  full suite run, two known reds only. Commit COMMIT-MSG-29Aug2026-aircraft-econ-table.txt.
