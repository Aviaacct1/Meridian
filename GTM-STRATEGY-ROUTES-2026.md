# Meridian go-to-market: World Routes 2026 and the launch after it

19 September 2026. THE UMBRELLA. One place for the strategy, the decisions, the two milestones,
the integrated timeline and the pre-mortem, so nothing is overlooked that bites at the show.
The detail lives in two companions and this document points at them rather than repeating them:

- `HANDOVER-ROUTES-19Sep2026.md`: engineering and the stand flow (speed, caches, pre-warm by
  airport, request queue and email, stand mode, laptop build, Plan A/B).
- `ROUTES-COMMERCIAL-PLAN-19Sep2026.md`: sales funnel, deck and pack and imagery, host manual,
  pricing structure, leads and feedback, website, marketing calendar, meetings, competitors.
- `PROMPT-for-Fable-Routes-19Sep2026.txt`: how a new chat picks either track up.
- `MASTER-TASK-LIST.md`: everything else open.

---

## Status

Rewritten every session by the programme controller; John reads this on a phone. As at
Friday 26 September 2026, 03:00 BST (John in the UAE): controller chat 4, day one, after the
sweep of every STATUS file (W2 v14 of 22 Sep, W3 v2 and W4 v2 and W5 v4 and W6 v7 of 20-21
Sep, W8 v2 of 20 Sep, W10 v1 of 22 Sep; no chat has written since). The day's finding: the
face-validity register (routes/FACE-VALIDITY-REGISTER-25Sep2026.md) shows Meridian's demand
at 2 to 2.6 times Avia's own analysts on every hub-ended long-haul from Edinburgh, split
between a connecting feed 10-25x the analysts' (the V1 flat capture, never scored by the
record) and a local over-read on small origins; John lifted the engine freeze conditionally
(pre-mortem 21) and the fix is the critical path. W10's baseline reproduced to the decimal
and the V1.3 refit gives 91 / 85 on 6,524; John ruled the stand sentence (item 55). Workstation
on 0eb7139 = origin. The wall artwork must reach the designer by 2 Oct, the site must be live
and John must have a TAO mailbox before invitations go. Files: `routes\Wn-STATUS.md` (chat
writes), `routes\Wn-RULINGS.md` (controller writes), `routes\README.md`.

THE CRITICAL PATH, locked 26 Sep, in order; nothing below a line starts before the line above
it is safe:
1. ENGINE FIX. W10 diagnosis Mon 29 Sep (pickle stamp, the two mechanisms against the record,
   outturn clause); John decides the fix Tue 30 Sep from options with back-test scores; W1
   builds and W10 re-scores 1-6 Oct; acceptance 7-8 Oct (three-pair diff, the register
   re-run); W3 re-runs every figure and records the video 8-10 Oct; freeze 10 Oct. Slip here
   moves everything after it; the fallback is the fixed-input demo path with the limitation
   in the known-issues list.
2. STAND GRAPHICS. Today: John decides item 40 (wall or logo) and item 44 (2.3 A or B); Full
   Vision brief sent asking spec by 29 Sep. 27 Sep W6 words to W3. 29 Sep-1 Oct W3 artwork.
   2 Oct to the designer. No accuracy figure on the wall.
2A. THE SAME-DAY PACK (John, 26 Sep: "needs to be clear and centre before we talk about
   locked"). The visitor's own run leaves the stand as a presentation the same day. Ruled
   26 Sep, controller, John to confirm (item 61): the BUILD is automatic and the SEND is
   approved by a person. On the result page the host types the visitor's email (temporary
   field at the foot of the run, W2); the run is queued as a pack job with the run's own
   inputs (W2's lead store and queue, built 21 Sep, app not yet rewired); the pack (deck plus
   workbook, W3's generator with automatic imagery from the cleared library, mood frames
   where coverage fails) is built on the workstation without anyone touching it; a named
   reviewer in the UK opens the queue view, checks formatting only (not content), and
   presses send; Postmark delivers from the Observatory domain with the ruled two emails.
   AMENDED 26 Sep (John): three states per job, NOW (host, sends on the build's own checks,
   no review), HOLD (default, auto-sends 30 minutes after the build passes unless paused),
   PAUSED (reviewer, with a reason); the build's checks are the safety net where nobody
   looks; a failed check goes to PAUSED. Offline capture (email and route on the card, run later) is the
   fallback if the queue fails on the day, and the host manual carries it. Owners: W2 (email
   field, queue job, queue view with approve/send, failure states, the runbook), W3 (pack
   template fixed on the ruled sentences, automatic images, one-click build from a run),
   John (the reviewer's name and hours for 21-23 Oct: item 62). Proven end to end on the
   11-12 Oct trial with a real email; rehearsed with Suzanna 16 Oct.
3. INVITATIONS. Gate: John's TAO mailbox (W2 says the route by 29 Sep; the tenant ask goes
   today if that is the route) AND the site live (W6, first version, competitor page
   withheld) AND the five contact names (John). Then send, 29 Sep at the earliest, week of 6
   Oct at the latest. The reply-to-forecast handover for a named route gets a written owner
   (W2) before the first invitation goes.
4. ORDER-READY. Solicitor slot week of 6 Oct; PI cover at TAO Ltd (binding on 21 Oct, John);
   TAO bank account and VAT (John, accountant); support address and reader (John); known
   issues frozen 10 Oct with the long-haul segment and feed limitation stated; Nick signs.
5. STAND OPERATIONS. W2: Optimise-then-Run flow with inputs carried, "Direct service today"
   fix, lead-store rewire and capture buttons by 2 Oct, laptop proof 8 Oct (needs John's two
   spec blocks), runbook with the freeze and RDP lines; W4 v3 after 8 Oct screenshots; a named
   person at the workstation 11-12 Oct; Suzanna 16 Oct; setup 20 Oct.

| WS | State | Where it stands (evidence) | Next action | Owner | Date |
|---|---|---|---|---|---|
| W1 Speed, caches, controller build | Acceptance PASSED 24-25 Sep; queue item 1 CLOSED (run_ diff IDENTICAL, DUB-DFW named 7x) | Workstation 0eb7139 = origin; baseline OPT-24Sep-final-w8; named Optimise 24.3 / 22.3 / 16.2s; BLQ-JFK and register probes saved under E:\Avia\probe | Engine fix from W10's write-up 1-6 Oct; market_build step-5 label and the sweep-v-run sentence; launcher empty-password refusal; then the queue | Controller | Fix 6 Oct; queue by freeze |
| W2 Stand flow | v14 (22 Sep), not swept by W2 since | lead_store built, app not rewired; Postmark approved 23 Sep (W2 does not yet know); catchment distance fixed via config (30e3e78); friction raster never resolved | Optimise-then-Run flow (inputs carried); "Direct service today: None" fix; rewire and capture buttons; John's TAO mailbox route by 29 Sep; runbook lines (freeze, RDP, restart); Postmark first real send and warm-up; progressive Optimise DEFERRED to after Routes on measured timing (controller ruling, John to confirm, item 59) | W2 chat / John (two spec blocks, tablet) | Capture 2 Oct; laptop proof 8 Oct |
| W3 Presentation, pack, video | v2 (21 Sep); slides 1-6, 9-10 built; 7-8 held; PDF proven; pitch page and video NOT STARTED; probe unrun | 3af5158 plus the pricing and PDF commits; figures provisional (W3-RULINGS 23 and 25 Sep) | Wall artwork 29 Sep-1 Oct; probe by 26 Sep or mood frames; slides to Jol and Nick 3 Oct with charts marked provisional; re-run every figure 7-8 Oct; video 8-10 Oct (Bologna as fixed XLR daily); conflicts 1-4 ruled below | W3 chat / John (items 26, 45) | 3 Oct review; 10 Oct video |
| W4 Host | v2 DONE (21 Sep) | STAND-HOST-MANUAL.md v2, 862 lines, 23 slots | v3 after 8 Oct screenshots: three visitor types, the four Optimise lines, the three-line read-out, the accuracy sentence once, 6,524 in writing | W4 chat / John (item 34) | v3 mid-Oct; slots as John answers |
| W5 Order-ready documents | v0.3 DONE (21 Sep); eight asks open, all John's | Standard Terms, Order Form, one-pager, invoice, onboarding, known issues v0.1, licence record, feedback card | Solicitor slot wk 6 Oct; PI cover at TAO Ltd (binding on 21 Oct); bank and VAT; support; quarterly call ruling; Nick to sign known issues; OAG/Sabre in writing; twelve months' notice (silence 3 Oct) | W5 chat / John | 6 and 10 Oct |
| W6 Messaging, site, invitations | v7 (20 Sep); sentences v3; invitations v3; post 1 and list email drafted; site removals at 6d153d2, clean-clone proof unrun, Pages waits on the zone | Sentence 1-HELD ("about a minute") RELEASED by the controller 26 Sep for single-run wording; 1-LIVE stands for the whole demonstration | Site FIRST VERSION LIVE before invitations (competitor page withheld; seats/presentations off); wall words to W3 27 Sep; bio for John; invitations from the TAO address only, when John has one, with the five names | W6 chat / John (names, 2.3, post 1, list email) | Site by 29 Sep; invitations 29 Sep-6 Oct |
| W8 Pricing | DONE; v1.1 FINAL 21 Sep already carries the TAO Ltd entity line | PRICING-DECISION-2026.md v1.1 (W8-STATUS v2) | Nothing; the controller's "v1.1 owed" was stale and is closed | W8 | Closed |
| W9 Stand, contract, logistics | OPENS 26 Sep | Full Vision named 24 Sep; F124; contract form with Charlotte open | Brief to Full Vision today (spec by 29 Sep); graphics decision today; pens order this week; setup plan 20 Oct; who carries what | John / W9 chat | Brief 26 Sep; artwork 2 Oct |
| W10 Final calibration test | Items 2 and 3 DONE 25 Sep; diagnosis widened | Baseline to the decimal on the declared build; V1.3 refit 91 / 85 on 6,524, blind 60.9; segments 72.6 / 39.8 | Pull; pickle build stamp and confirmed pair; the two mechanisms against the record; outturn clause; fix options with scores by 30 Sep | W10 chat | 29 Sep; 30 Sep; record v1 3 Oct |
| W7 Rehearsal and freeze | Diaried | Trials 11-12 Oct remote, 16 Oct Suzanna | Named person at the workstation 11-12 Oct (John); freeze 10 Oct on the corrected engine | Controller / John | 10 Oct |

Controller rulings from this sweep, announced in the rulings files the same day:
- W3 conflict 1 (deck author): file metadata author and last-modified-by stay Avia Solutions
  (standing rule); slide branding is the Observatory. Conflict 2: the slide text is John's
  sentence of 25 Sep (item 55), figure to follow W10; 25(b) wording withdrawn from the notes.
  Conflict 3: 3 Oct. Conflict 4: W3's proposal accepted, amended: charts regenerate after the
  engine fix acceptance on 7-8 Oct, not after the 10 Oct freeze, so printed matter is on
  accepted figures.
- W2 item 5 (progressive Optimise): deferred to after Routes on the measured timing (named
  24s, open sweep under 90s); the host says "about a minute" and shows the methodology page.
  John to confirm (item 59).
- W6 sentence 1-HELD released for single-run wording; 1-LIVE ("under five minutes") stands for
  the demonstration as a whole.
- W6 risk 1 (named-route reply to forecast): W2 writes the step and owns it; John forwards the
  reply to the stand build the same day; it is in the runbook before the first invitation.
- W8 v1.1: already issued by W8 on 21 Sep; the controller's owed item is closed.
Still open from earlier reads: (c) Atlas has no row in this table (Jess); (d) the first Friday
note is written today as the close of this session.

## What is left, by owner, as at 19 September, 22:45

**John, this week (dates are the chats' dates, not mine):**
1. Item 28 CLOSED 20 Sep: SJC-TPE and Bologna-New York stay.
2. Item 26, by 23 Sep: the carrier for Bologna-New York (if item 28 keeps it).
3. Item 25 SETTLED 22 Sep (John's sentence; the calibrated model is the on-screen engine).
   Item 55, by 3 Oct: which accuracy pair, on W10's record. Item 56, today: open the W10 chat.
4. Item 33, by 26 Sep: run W3's coverage probe on the workstation (block in W3's chat).
5. The four messaging sentences: pick from W6-MESSAGING-VARIANTS-19Sep2026.md by 25 Sep.
6. The five meeting contacts by 25 Sep; invitations out 26-29 Sep (drafts in
   W6-INVITATIONS-AND-MEETINGS-19Sep2026.md).
7. Item 14: order the 1TB external NVMe SSD before 28 Sep; run W2's two spec blocks.
8. Item 31: the contracting entity for the agreement (Avia Solutions Limited or The Aviation
   Observatory Ltd), so the solicitor can start; and name the solicitor.
9. Item 23: send Suzanna W2's four questions (as they stand in W2-STATUS.md).
10. Item 34: W4's three (second and third phone contacts; your stand hours; the competitor
    sentence in manual 4.4).
11. Postmark: chase approval on 1 Oct if not cleared (W2 watches).
12. Item 6, by 3 Oct: launch offer numbers (year-1 discount, places, expiry) or "on request".
13. Item 24: which tablet for the capture front end.
14. W6's dashboard task: the OAuth app and auth Worker pointed at tao-website and the Access
    policy on its /admin (W6 writes the steps); the launch-switch commit has landed.
15. The running git block for the controller's files (below) whenever convenient.

**Controller (this chat), next session:** push the item 37 tier table into W5 (clause 2 and the
schedule), W3 (pitch page pricing line), W4 (host sentence, 4.4 pricing slot) and W6 (site
copy, still unpublished until November): DONE 20 Sep in the four rulings files, chats pick it
up at their next run. Then W1 step 2 (persistence and warm-up) with the probe
diff; the pre-warm airport list with IATA codes from the register; the 40-60 route panel
proposal for John; sweep of all six status files; Friday note on 26 Sep; diary the 11-12 and
16 Oct trials; re-read the delegate list week of 12 Oct.

**W2 chat:** zone move (wk 22 Sep) with Postmark re-verification; demo_mail host fail-loud;
DuckDB leads table and JSONL migration; stand mode; capture front end (2 Oct); queue view;
progressive Optimise; laptop load procedure once the SSD exists (proof 8 Oct); pre-mortem 15
(GeoNames); scheduled-task restart if time (8 Oct); pack hostname and URL rule (3 Oct).

**W3 chat:** PDF render off the full pack; the 20-minute pitch page with the route map,
time-of-day curve and tail chart; probe results and the second-source recommendation; slides
7-8 from runs 29 Sep-1 Oct; the full sweep 2 Oct; to Jol and Nick 3 Oct.

**W4 chat:** manual v2 after Suzanna's answers; pricing wording swapped to John's of 19 Sep;
"follows the same day" in 6.5; screenshots after 8 Oct; Word copy; training 14-16 Oct.

**W5 chat:** invoice template, onboarding script, known-issues list (draft 1 Oct, frozen 10
Oct), licence-record form, follow-up sequence; agreement to solicitor 3 Oct; feedback card
to Jol 8 Oct.

**W6 chat:** Pages project and preview (the launch switch landed at e02dd1b on tao-website); competitor out of eight files
and prices out of eight places; accuracy line onto the Meridian page; clean-clone build
proven; sentences and invitations finalised on John's picks; post 1 and list email out
24-25 Sep once item 28 names the chart; exhibitor listing text (wk 29 Sep).

**NEW 20 Sep, order-ready pulled to 21 Oct, so by 3 Oct John also rules:** the launch offer
(discount, places, expiry), the presentation overage rate, the internal size thresholds,
payment terms (controller's view: annual in advance, invoice on signature, 14 days, a small
discount for payment within 14 days), the contracting entity (31), and the solicitor's slot
in the week of 6 Oct. And whether a PER-ROUTE STUDY (a Meridian route study delivered as a
pack, priced per route, invoiced on delivery) goes on the one-pager as the fast-entry product
that a route development manager can buy without procurement (item 35).

**Open decisions with no default (cannot be silence-ruled):** 25, 26, 28, 31, 34, 24, and the
five contacts.

**Found this session, not in any document:**
- The 29 August aircraft-economics CODE is uncommitted on the DevPC: `9cb5ed1` carries the CSV
  only; `aircraft_econ_loader.py`, `test_aircraft_econ_table.py` and the edits to
  `aircraft_economics.py`, `config.py`, `cortex_app.py` (`/api/aircraft`, fallback list
  removed) are modified or untracked. Master list "Closed 29 Aug" and item 1.1 are wrong as
  written; the workstation, if it pulled, has a table with no loader.
- `app/preagg.duckdb.tmp` on the DevPC holds 24GB of DuckDB temp from a 5 July build that did
  not finish (the 16GB box); `app/preagg.duckdb` (77MB, 5 July) is of unknown state. Treat no
  preagg store as existing; build on the workstation (step D). The 24GB is deletable.
- Estate index v11 (8 Aug) still says "World Routes early October"; the umbrella governs.
- Master list 2.4 (does the 89/82 claim describe the engine the client sees) is still open;
  the standing accuracy wording is fixed regardless, and pre-mortem 9 depends on it.
- `C:\src\meridian\app\access_password.txt` does not exist: the workstation server takes its
  password from `QSI_PASSWORD` in the launching account's environment. Any probe run over
  ssh must set `$env:QSI_PASSWORD` first (single quotes).
- Working tree also carries an uncommitted +58 lines on HANDOVER-23Aug2026.md and three
  binary test outputs (master list 5.10).
- The preagg store is NOT reachable from the live app: `cortex_app.py` and `config.py` carry no
  preagg hook; only `backtest.py --preagg` and `route_feed.py` (`feed_cfg["preagg"]`) know it.
  "Switch it on" (handover 3.2) therefore needs a small wiring change on the demo path before
  the freeze, after the identity check passes. `sector_adj` is optional by design; the core
  tables are `od_p2p` and `od_single`.
- No stage timing exists in the run path (only job-level `elapsed_s`), so measurement is
  from outside: `diag_routes_timing.py` (HTTP wall clock in stand order, plus an in-process
  cProfile mode for attribution). Evidence files: `TIMING-<date>.md` at repo root.

## Decisions log

- 19 Sep 2026: the six decisions in section 1 (licence in hand for the show; soft price with
  expiring launch discount; two milestones; messaging before invitations; no competitor
  approaches; Optimise demonstrated on the stand).
- 19 Sep 2026: programme controller appointed; this Status block is the single truth.
- 19 Sep 2026: W1 STEP 1 SHIPPED and MEASURED on the workstation (commit 1012c29, server
  restarted, before/after on the same two pairs, same day). Run: SJC-TPE 35.4s to 9.8s cold and
  8.9s warm; BRS-EWR (cold, nothing warmed it) 42.5s to 9.0s. Optimise, narrowed default:
  161s to 65s and 196s to 35s. Every saved Run payload identical before and after. The
  handover's two acceptance tests are met by memoisation alone. The launcher trap bit once on
  the way: a pull does not replace a running server, and Meridian-run.bat re-warms rather
  than relaunches, so the process must be stopped first (Stop-Process, then relaunch).
- 19 Sep 2026 (John, in the W2 chat): the pack SENDER is POSTMARK, not Microsoft Graph. Reason:
  verifying a domain, creating a mailbox and consenting a Graph app on the Avia Microsoft 365
  tenant all need Global Administrator, which the IT firm holds and John does not; three
  weeks before the freeze that queue is not on the Routes path. aviationobservatory.com set up
  clean on Postmark: DKIM verified, Return-Path verified, DMARC p=none published, no reporting
  address yet. Postmark account in TEST MODE until its human review clears (requested 19
  Sep; chase 1 Oct). Ruling 15 amended accordingly; two emails per visitor stands.
- 19 Sep 2026: W2 FINDING, material. config._resolve_egnyte_root falls back to the nominal
  Z: path when no marker folder is found, and Z: is per logon and invisible to ssh, so a
  server started over ssh resolves MCT_MASTER to a path that does not exist, load_mct_data
  returns an empty dict in silence, and every connection cascades to a flat 90 minutes,
  which moves the forecast on any multi-airport metro. Whether the live portal has ever run
  that way is not knowable from the code. Fixed at 2cab1b2 (the server states rows loaded or
  the reason, stand mode refuses to start without the master); the NEXT RESTART after the
  workstation pulls 2cab1b2 answers the question. Pre-mortem item 16 added.
- 19 Sep 2026 (John, in the W3 chat): airport-specific photography is required in the deck
  and the packs, from more than one online source with paid stock held for the gaps, at
  least three images per airport; the Observatory mood frames and charts stay. The
  image-source accounts are held by The Aviation Observatory and wait for a mailbox on that
  domain. Slide 8 is Bologna-New York (carrier still to name). W3-RULINGS item 4 widened.
- 19 Sep 2026: W3 FINDINGS. (a) The delivered JPEG re-encode in deck/render_pptx.py dropped
  every rights record; fixed and proven (commit 45a5210), and the build now fails on a bare
  image. Every JPEG in the China Airlines TPE-SJC deck of 19 Aug (94 of them) carries no
  record, most from C:\assets\engagement, which has no manifest at all; nothing from that
  folder goes on a Routes surface. (b) The 2 July deck contradicts Nick's 23 Aug note in
  four places (one engine or two; accuracy in words versus the ruled pair; two pre-fix
  validation figures; naming). (c) master list 3.3b answered; 2.4 is now stand-critical.
- 19 Sep 2026 (John, in the W3 chat): pack, PDF and imagery pulled forward from 8 Oct to
  3 Oct so all four W3 items reach Jol and Nick together; the PDF is the FULL researched pack
  and the HTML is a separate 20-minute airline pitch page with interactive charts.
- 19 Sep 2026 (John, in the W6 chat): the site to launch before Routes is THE AVIATION
  OBSERVATORY site, not the Avia Solutions site; domain aviationobservatory.com (the .aero
  name in the repo dropped); Jol is not writing copy now, W6 prepares it and John approves;
  the site is deployed by Avia itself on Cloudflare Pages from the repository, not from the
  workstation; the Avia website editor is pointed at the Observatory site AFTER Routes. W6
  findings: the Observatory site repo (E:\Avia\Observatory Website, 22 pages, last commit 3
  Aug) has NO git remote, which breaks tool standard 1 and is fixed this week; the competitor
  is named in the site's header and footer on every page (eight files) and comes out before
  launch; prices sit in seven files; the site carries no accuracy claim yet.
- 19 Sep 2026 (John, in the W6 chat, after the sweep): pricing HELD until November, as item
  29 now records; and the Observatory site is built to work IDENTICALLY to the Avia site
  (Cloudflare Pages with wrangler.toml, the SITE_ENV and SITE_URL pattern, a preview
  environment, the push script, the Sveltia editor on the same auth Worker and Access policy,
  a Pages Function for the forms), all before cutover except body-text editing, which waits
  for November. The pack host is the workstation tunnel at a pack hostname, W2 mechanics by 8
  Oct; W2's conflict that the pack "had nowhere to live" is closed by that. W2's condition
  stands: no nameserver or DNS change on aviationobservatory.com until W2 has reproduced the
  DKIM, Return-Path and DMARC records at the new host and re-verified them in Postmark.
- 19 Sep 2026 (controller rulings at the sweep): (i) THE PACK PROMISE: every outgoing word
  says the pack "follows the same day" until the sender is out of test mode and one pack has
  been sent and received over a hotspot at the 11-12 Oct trial; "within 30 minutes" only
  after that. (ii) TIER SHAPE: the published grid, airlines and advisers "quoted" (W5's
  recommendation adopted; silence rule to 3 Oct unchanged). (iii) The five stand feedback
  questions are W5's card wording everywhere; W2 adds them as an optional host-only screen
  after the capture form only if it costs nothing before the freeze.
- 20 Sep 2026 (John): worked routes stay SJC-TPE and Bologna-New York; more may be added
  later. Item 28 closed; the never-worked-airport rule set aside for these two.
- 20 Sep 2026 (John): the pricing and term points of today are consolidated as a 13-point
  finalisation checklist in routes\W5-RULINGS.md; W5 ticks it in its status before the
  agreement goes to the solicitor and the one-pager to print.
- 20 Sep 2026 (John, later): every agreement states that prices move by at least inflation
  each year (UK CPI); new functions are priced options or, if folded into core, raise the
  core price above inflation at a renewal. Expectation set in the first contract.
- 20 Sep 2026 (John, later): three FIXED cash prices for years 1-3 on a flat 3% illustrative
  inflator; annual auto-renewal with one month's cancellation and Avia's notices at three and
  two months; a clause for Avia ending the service (notice, pro-rata refund, outputs kept).
- 20 Sep 2026 (John, final): LAUNCH OFFER 50% / 75% / 85% of list in years 1 to 3, list being
  the banded grid; add-ons at 50% in year 1 or 75% in year 2; in return for tolerance of
  launch bugs, references, use of name and brand in marketing, and signing by 30 November
  2026. Item 29 rewritten; W3, W4, W5, W6 carry the wording.
- 20 Sep 2026 (John, latest, final): TIERS BY USAGE, NOT SIZE. One product in every tier
  (Run, Optimise, schedule sizing, route economics). Forecast £15,000 (standard pack, 2
  users, no researched packs) / Pitch £22,500 (up to 100 researched packs a year, brand
  skin, 3 users) / Programme £27,500 (unlimited packs, client catchment loaded once at
  onboarding and at renewal only, Watch, 5 users, named contact). List carries headroom for
  the named discounts day-to-day selling will need; Tier 2 net floor £20,000; in-year
  upgrade at the full annual difference, never pro rata. Client template mapping stays a
  bespoke £5,000 option with a fit caveat. Assured (review, consulting) is a 2027 package,
  out of all Routes material. Item 37; item 29 amended; W3, W4, W5, W6 carry it. This
  reconciles the 7 Aug usage-axis position with the 2-3 Aug website price points, raised.
- 20 Sep 2026 (John): PRICING DECOUPLED. Launch terms firm before Routes (a fixed year-1
  price for a fixed cohort with an expiry, offered in writing at the meetings and on
  request); standard pricing held in mind, not published or quoted at Routes, set after the
  show on feedback. Item 29 rewritten; W3, W4, W5 and W6 carry the wording.
- 20 Sep 2026 (John): ORDER-READY MOVES TO 21 OCTOBER. A large engagement has been suspended
  and cash matters sooner than planned. John does not expect a signature at Routes (every
  purchase is corporate and needs approvals) but AVIA MUST NEVER BE THE DELAY: pricing agreed
  and every document ready at Routes or immediately after, so a client can be running and
  paying in November. Decision 3 of 19 Sep amended: demo-ready and order-ready are the same
  date. Consequences: W5's documents all land by 10 Oct with the solicitor's review inside
  that; pricing becomes FIRM numbers by 3 Oct (launch offer, overage rate, size thresholds,
  payment terms, entity); the code half of order-ready is done before the freeze where it is
  a dashboard task (per-client Access policy) and otherwise written into the known-issues
  list rather than built; pre-mortem 14 rewritten; the one-pager with real numbers is
  printed for the five meetings and handed to any qualified buyer on request.
- 19 Sep 2026: DATE CORRECTION. Several entries above and the commit messages 6bbdc0b to
  1012c29 say "21 Sep"; the controller misdated them. Everything so dated happened on
  Saturday 19 September 2026 (the timing files and the workstation clock agree). File
  contents corrected; commit messages left as they are.
- 19 Sep 2026: John's rulings on the pack: TWO emails (plain thank-you plus PDF attached;
  HTML pack HOSTED on the launched site at a public unguessable URL, linked, with links back
  to the main pages, and the same page is how the UK analysts review live packs and send a
  correction); aviationobservatory.com is registered and unused, set it up as the sender from
  scratch; a branded HTML email where it renders, plain text fallback. Host training is
  remote (video sessions on the frozen build); Suzanna and Stefan have both used the tool.
  Website launches as a "site lite" if the full site is not ready, with Q&A added after
  Routes from the questions asked. A voice note-taker for Suzanna is under consideration
  (needs a consent line on the stand).
- 19 Sep 2026: preagg chain on the workstation: build DONE (od_p2p 1,157,577; od_single
  5,780,022; sector_adj 859,129 rows in 426s; E:\Avia\preagg.duckdb written). Run A (no
  preagg, 100 pinned routes, single-threaded) DONE in 618s, 85 routes scored, 3 errored for a
  missing GeoNames dump on the workstation, 12 dropped by the back-test's own rules. Identity
  check running. The back-test's own accuracy tables are the raw uncalibrated 2016 pin and
  are NOT the product claim; they are ignored here.
- 19 Sep 2026 (John, answers to the decisions batch):
  1. Pricing: the structure exists (PRICING-HANDOVER-19Sep2026.md, from the Observatory site
     build of 2-3 Aug): £15,000 / £20,000 / £25,000 a year by airport size, three seats, 100
     presentations included, sales-led, published in full on the staging site. The soft
     expected list for the offer sentence is therefore that grid. STILL OPEN: launch-customer
     discount, number of places, expiry; the overage rate; the airline and adviser tiers of
     the commercial plan, which the grid does not carry.
  2. Meetings: John can sign in to the Routes site; the delegate list is read in a browser
     session with the controller and the five targets chosen from it. Same session yields
     the attending-airport list (5).
  3. Email sender: the domain is aviationobservatory.com, set up to send. John's pattern
     under consideration: a plain thank-you email first, then the PDF and the HTML in
     separate emails so one blocked type does not lose the other, with a line to come back
     to the stand if they have not arrived within the hour. Controller view in Waiting on
     John 8.
  4. Lead store: DuckDB. A basic CRM on top of that table is a post-Routes item.
  5. Attending airports: from the delegate list (see 2).
  6. Stand host: Suzanna McIntosh, suzanna.mcintosh@gmail.com, already in Cloudflare Access.
     Stand F124. Lands Tuesday 20 Oct afternoon; works the stand Wed-Fri 9-5. Stefan Parry
     (summer intern) may join her.
  7. Website: LAUNCH before Routes; linked from the emails and the conference bio.
- 19 Sep 2026: PREAGG IDENTITY CHECK PASSED on the workstation: 85 of 85 pinned routes
  identical across every column, no-preagg baseline against preagg, same code, single
  thread (E:\Avia\preagg_check\identity.log). Wiring preagg into the live path is therefore a
  pure performance change. MEASURED saving on the back-test path: 548s against 618s, 11%,
  circa 0.8s a route (baseline file cache warm, so this flatters the baseline). Preagg is not
  where most of the stand's 42-second Run goes; the in-process profile decides what is.
- 19 Sep 2026 (John, rulings 14-17): Plan B hardware is a 1TB external NVMe SSD over USB-C on
  John's core x86 laptop, ordered before 28 Sep. Lead flow: EXTEND the 16 Aug build, which was
  a holding draft; the store becomes a DuckDB `leads` table now (nightly Excel export to
  Egnyte), a CRM can sit on top after Routes; and the stand gets a professional, quick
  data-capture front end (60 seconds, tablet-friendly, consent, branded), a W2 build item.
  MCT master reports rather than defaults silently: yes. Laptop dates: 1 Oct hardware
  go/no-go, 8 Oct proof, show machine loaded by 10 Oct, hard stop 15 Oct.
- 19 Sep 2026: MEETINGS are chosen by likelihood of buying, not by relationship (John);
  relationships come to the stand anyway. The direct competitor's 22 published client logos
  are cross-checked against the register (20 present) in the organisations file, section 8.
- 19 Sep 2026: from W2's first status file (routes\W2-STATUS.md): Boeing 13 Oct is an Atlas
  meeting, so the Meridian dress rehearsal moves to two trials, 11-12 Oct and 16 Oct; the
  request form and lead store exist since 16 Aug (demo_leads.py JSONL store, demo_mail.py M365
  SMTP, /api/demo/*, 58 checks) and are extended rather than replaced (controller view,
  John to confirm); the narrowed sweep boundary is W2 the switch, W1 the measurement.
- 19 Sep 2026: Routes World 2026 is in FRANKFURT (relocated; same dates). Registered
  organisations and the 90 exhibitors read from the matchmaking platform and recorded in
  ROUTES-ATTENDING-ORGANISATIONS-21Sep2026.md (organisations only, no delegate names): the
  pre-warm airport set (decision 5) and the controller's proposed five meetings (decision 2)
  are in that file, awaiting John's pick. An organisation-level master list of all delegates
  (company, type, country, count) is still to build; a person-level pull was blocked by the
  environment's privacy control and is not attempted again.
- 19 Sep 2026: HOW CHATS ARE RUN (John). This chat, on Fable, is the controller: status,
  decisions, W1 engineering judgement, the Friday note. Build workstreams run in dedicated
  chats on Opus. Every new chat is started from a complete paste-ready prompt written by the
  controller, model named, reading its files by path; John never copies text out of files.
  Each build chat ends with a five-line report John pastes into the controller.
- 19 Sep 2026: John away 20-27 Sep; the preagg store build plus its identity check runs
  unattended on the workstation over that week (block issued). Pre-warming routes is NOT
  started: every app cache is in-process and dies at restart; the persistent cache (W1)
  comes first.
- 19 Sep 2026: the uncommitted 29 August aircraft-economics code is COMMITTED before the
  freeze (John: it was a fix that emerged after he left for holiday and was held back so it
  could not break anything while he was away). Commit block issued; one live check on the
  workstation owed before 10 Oct.
- 19 Sep 2026: the 24GB `app/preagg.duckdb.tmp` on the DevPC is checked for duplication
  before removal, not removed on suspicion (John). Check block issued.
- 19 Sep 2026: check done. DevPC `preagg.duckdb` holds `od_p2p` (1,157,577 rows) and
  `od_single` (5,780,022 rows) and NO `sector_adj`: the 5 July build died on the heavy
  sector table and the 24GB is its spill. Removal block issued; the Routes store is built on
  the workstation with raised memory and a local temp dir.

- 20 Sep 2026 (John, in the W8 chat, 18:00): PRICING FINAL. routes\PRICING-DECISION-2026.md v1.0;
  bands by airports covered (£15,000 / £22,500 / £30,000), whole product in every band, no
  seat count, fair use at 250 packs, no limit on launch places, years 2-3 fixed cash,
  continuity 5% from first renewal, multi-year 10%/7.5% locked, 90 days' notice, Standard
  Terms plus Order Form, study £2,500, catchment load £3,500, airlines not sold (Sabre
  licence). Items 6, 35, 37 closed; 29 superseded where it differs. W3-W6 rulings repointed.
- 20 Sep 2026: W1 step 2a MEASURED. Boards persist across a restart (1,203 written on restart 1,
  read back on restart 2, none rewritten); probe --diff PASS on three pairs. Cold Run 33.6/53.3/
  23.3s to 21.3/42.0/20.8s (SJC-TPE, BRS-EWR, DUB-DFW); warm 11.6/10.3/8.5s. The in-process
  profile (TIMING-20260920-1545) puts the remaining cold cost in the catchment's land-path
  searches, not the boards; step 2b persists those (written, awaiting commit and restarts 3-4).
  The market brief costs 6-8s on first entry of any route; noted, not yet attributed.

- 20 Sep 2026 (John, 19:30): MESSAGING is in THE AVIATION OBSERVATORY'S voice; Avia appears only
  as the affiliate with its credential. Sentence 1 promises the forecast "while you wait, in
  under five minutes" ("about a minute" only when W1's restart-proof numbers allow it, Run
  only); 2.1 "the optimal time to fly it"; 2.2 "a full presentation pack follows the same
  day"; 2.3 as an affiliation clause; 3 is the W8 host sentence. Meetings: the five stand as a
  start (Dublin and SEA are groups); every invitation asks the airport to name a route and the
  forecast is prepared ahead of the meeting. W6-RULINGS carries it.

- 20 Sep 2026, 21:45: Suzanna's four answers received (item 23 closed). Consequences: W2 stand
  mode separates OUTPUT from the two actions and labels each; W4's manual takes her order of use
  and a weak-scenario list from W5's known-issues list; John tells her Optimise is now 38-55s;
  the accuracy sentence (item 25) is the host's priority slot.

- 20 Sep 2026, 22:15 (John): the Run / Optimise / OUTPUT row is learned on first use, not a
  defect; clearer only if it stays clean; Suzanna's understanding is the stand mitigation; a
  client help guide or video is an onboarding item (W5). ACCURACY on the stand is forecast
  against the visitor's own forecast: everyone understands the 89% claim the same way (item
  25), and the gap is placed on the methodology page's bridge chart, step by step, rather than
  argued on the total (pre-mortem 3, manual 7.6; W4 writes the walk-through). The bridge exists
  in the build (methodology_page.py, tied to the last run); the controller checks it renders on
  the workstation build and reads for a lay visitor before the freeze.

- 21 Sep 2026: GAP FOUND. No workstream owned the exhibitor contract, stand build, manual
  deadlines, badges, kit and setup. W9 created (routes\W9-RULINGS.md v1). The contract is not
  signed; Informa's emails say stand F124 where every document says F124; graphics close 3 Oct.

- 21 Sep 2026 (John): THE CONTRACTING ENTITY IS THE AVIATION OBSERVATORY LIMITED for everything
  from day one (exhibitor contract, client agreements, invoices). Item 31 closed; W8 decision 15
  overridden; order-ready gains PI cover extension and a TAO Ltd bank account (pre-mortem 17).

- 21 Sep 2026 (John): the stand is F124. F174 was a transcription error of 19 Sep carried into
  twelve files; all corrected 21 Sep.

- 21 Sep 2026: W2 FINDINGS (v13). (a) Postmark's SMTP endpoint accepted and silently discarded
  three messages its policy forbade while the API refused the same message with the reason;
  transport moved to the API (3406f0a). (b) W2's v9 recorded a false PASS on the evidence of a
  script printing SENT and withdrew it; programme rule from today: no send counts without a
  provider MessageID, and no test passes on a fake transport's own attribute. (c) Delivery
  proven 21 Sep 14:01Z from aviasolutions.com to itself (MessageID 8283ccb0); the Observatory
  domain is proven only after approval. (d) Blocks labelled Workstation Actual ran on the Dev
  PC because a second clone exists at C:\src\meridian there (item 43). (e) Env vars now at
  Machine scope on donatello. Capture layer widened by John to four record types; progressive
  Optimise deferred to after Routes; recorder: W2 recommends against, item 42.
- 21 Sep 2026: W6 v7 read: sentences redrafted in the Observatory voice; invitations ask the
  airport to name a route; site licence copy contradicts the pricing file (W6 fixes next);
  the named-route handover is ruled (John forwards to the controller the same day).

- 21 Sep 2026: W1 STEP 2 CLOSED, MEASURED. Boards (2a, pickles under LOCAL_CACHE\boards) and
  catchment land paths (2b, sqlite under LOCAL_CACHE\water_check) persist across restarts.
  Cold Run on a freshly started server: SJC-TPE 16.9s, BRS-EWR 20.2s, DUB-DFW 13.4s, identical
  on restarts 4 and 5 (TIMING-20260920-1910, -20260921-1607); day-one baseline was 33.6 / 53.3 /
  23.3s (restart 1) and the in-process profile fell from 118.8s to 37.5s, the remainder being
  route_feed.score / qsi_feed._collapse (frozen engine, the warm floor of 8-11s). Payloads
  identical to the pre-change baseline on every restart (probe --diff PASS). Acceptance in the
  brief met: Run on a never-run pair under 30s cold; Optimise narrowed 38-53s with first result
  inside 30s. Pre-mortem 11 CLOSED. "About a minute" released to W6 for the forecast (Run).
  Left for W1: the market brief's 6-8s first call; warm_boards over the register before the
  show; the straight-line gap cache only if time.

- 21 Sep 2026 (John): the stand TV carries a DEMO VIDEO loop; the 9 Sep video job becomes W3
  scope item 5 (silent, subtitled, 3-4 minutes, Bordeaux and Boise plus a third hub, item 45;
  first cut 3 Oct, final on the frozen build, loaded by 15 Oct).

- 21 Sep 2026: W3 v2 and W4 v2 read. W3: PDF render proven, slide 10 on final pricing, the
  pitch page's three figures found already built (curve, maps, tail chart), video dated. W4:
  manual v2 on Suzanna's answers and the bridge walk-through; three bridge labels flagged as
  modeller's words, now W3's to change before the freeze. Rulings: product decks are authored
  by The Aviation Observatory; slides 7-8 go to review 3 Oct on current-build charts and are
  regenerated after the freeze; the spend question names no supplier.

- 21 Sep 2026: W5 v4 read: every order-ready document exists in draft (Standard Terms plus
  Order Form, one-pager, invoice, onboarding script, known-issues, licence record, feedback
  card). Rulings: no quarterly review call in any band; the disclaimer names both companies
  and the in-service wording is W1's; the walk-up one-pager carries the single-airport price
  with groups quoted, the band table on the Order Form only; twelve months' retirement notice.
  New items 47-51. PI cover and the TAO bank account are now the binding constraints on
  order-ready, not the drafting.

- 21 Sep 2026 (John): Jol's 43-item layman's read (3 Sep, Egnyte) triaged into
  routes/JOL-FEEDBACK-REGISTER.md: four bugs, one copy batch, the catchment page rewritten
  before the freeze, "actual" for "measured" on data surfaces, no "physics", and EACH-WAY /
  TWO-WAY labelled on every figure with a display switch on the dashboard (John: the most
  important item; the TPE work went wrong on it; US reads departing, the rest two-way).
  W2 and W3 carry it; W4 changes screen words once. (No W10 for Jol's items; W10 was
  created 22 Sep for the calibration, below.)

- 22 Sep 2026 (controller, W1): THE CALIBRATED ENGINE TEST. bt2/bt2_claimset.py on the
  workstation reproduced the 13 Aug baseline exactly (calibrated 83.2 / 70.0, blind 60.9,
  tier A 88.2, portfolios 87.7 / 93.2, segments 72.6 / 39.8, sample 6,524 Sabre-only; log
  E:\Avia\probe\claimset-22Sep.log). Server restarted on `--engine bt2`: Run cold 16.8 /
  16.6 / 12.1s (SJC-TPE, BRS-EWR, DUB-DFW), warm 9.2 / 9.5 / 7.2s, Optimise 42.5 / 40.6 /
  34.4s, all faster than QSI (TIMING-20260922-0628). Demand each way, QSI to BT2: BRS-EWR
  captured 215,554 to 42,708 and total 314,524 to 134,598; DUB-DFW 36,495 to 81,592; SJC-TPE
  54,151 to 61,090. John: the Dublin rise is partly Ryanair positioning traffic from the UK
  buying Dublin-originating tickets; Nick confirmed the figures are correct. Ruling (John):
  ONE model; the calibrated model is the core product and the QSI switch was only ever left
  default-off pending re-measurement. The controller's earlier line that item 25 needed a
  two-day build was wrong; the wiring exists in calibrated_forecast(). W1 flips the launcher
  default to `--engine bt2` and replaces the stale "accuracy NOT re-measured since 13 Aug"
  warning with the 22 Sep date. The server stays on BT2 from today; the rollback is the
  launcher flag. Defect found: the payload's top-level `engine` string reads "route_forecast
  (calibrated)" on both engines while provenance.local_leg is right; W1 fixes the label.
- 22 Sep 2026 (John): ITEM 25 SETTLED IN SUBSTANCE. The stand sentence: this forecast uses
  the model tested on real launches; 89% were within 20% and 82% within 10%; we cannot say
  that of a single route, but it is the same model; the record is republished yearly. The open
  half is which pair the product publishes. Interim: 89/82 on 2,915 on every surface (the
  ruled line). The 92/86 on 6,524 (V1.3-MIXED, 9 Aug) comes off the methodology and track
  record pages now (W3 instructed) because nobody can say what built it. John's inclination:
  the larger sample, if it reproduces. W10 produces the evidence; John rules by 3 Oct.
- 22 Sep 2026 (John): W10 CREATED, "final calibration test", an Opus chat, routes/
  W10-RULINGS.md v1. Order of work: catchment radius first (John's specification, item 1:
  Birmingham inside London at the flat 220 km; narrowing banded by haul and carrier type,
  radius and capture fitted together in search_adjustments.py with cross-validation; ships on
  by default inside the definitive calibration or is rejected; the fitted radius is the
  default a supplied catchment overrides; no sixth default-off switch), then the 22 Sep
  baseline reproduced, then the 92/86 pair reproduced or replaced, ending in ONE figure set.
  This opens the frozen demand logic for that one item only, on condition it lands by 3 Oct
  with the accuracy re-measured, or not at all. W10 owns bt2/ and search_adjustments.py; any
  app/ change goes through W1 as a one-line diff. Flag: the controller restated John's
  catchment text from notes after a context compaction lost the original; John can paste the
  original into the W10 chat and the controller will replace the section verbatim.

- 22 Sep 2026, evening (controller; John to confirm): W10-STATUS v1 shows the catchment
  radius does not enter the BT2 claimset; item 1 as specified measures nothing. Re-ruled:
  item 1 goes to W2 under R6 as the competing-airport radius in cortex_app (on by default or
  rejected; supplied catchment overrides; before 10 Oct or not at all). The freeze exception
  of this morning is WITHDRAWN; demand logic frozen, no exception. W10 proceeds with items 2
  and 3. W2 found the friction raster was never resolved on the workstation (hardcoded
  C:\Avia), so catchment has run on straight-line distance silently; fixed through config,
  no behaviour change, road times stay off (30e3e78). Commit 30e3e78 carried W2's and W10's
  uncommitted work under the controller's subject; their message files are in the commit.

- 22 Sep 2026, late (John): THE OPTIMISE BUTTON STAYS ONE BUTTON. Verbatim: "i would prefer
  not to remove things as that make a simple button into a a journey toward needin to learn a
  system." Context: on TIF-AUH (Taif-Abu Dhabi, airline open) the dashboard's Optimise ran the
  full sweep (all seasons, all carrier types, candidates open, frequency-sensitive re-runs
  per frequency) in 240s on the stand flow and 257-260s in the harness; the narrowed default
  took 36.2s with Etihad named and 88.7s open; Run 3.8-7.8s (TIMING-20260922-2046, d607d22,
  bt2). Mechanism read in api_optimise: candidates x types x seasons x eight forecasts each.
  Consequence: no narrowed default and no second button; W1 makes the full sweep faster in
  api_optimise (parallel candidates, no demand logic touched, same payload diff); W2 brings
  progressive Optimise back onto its list. Until measured, "about a minute" is a Run claim
  only; Optimise on the stand is "a few minutes, the host talks through the methodology page
  while it runs" (W4 manual, W6 script). The 38-53s Optimise figures of 22 Sep morning are
  to be read as the narrowed default with the airline named until the three-pair full-probe
  table says otherwise.
- 22 Sep 2026, late (controller): tonight's workstation findings. (a) The workstation was
  on 66455af (21 Sep) all day; nothing committed on 22 Sep ran there until d607d22 was pulled
  at circa 20:00. (b) The pull was blocked by three generated files under app/ that the repo
  tracks (Network_PnL_Genoa.xlsx, Route_Economics_slide.pptx, Route_Economics_test.xlsx);
  stashed on the workstation; untracking is W1 job 7. (c) One restart ran on QSI for circa
  fifteen minutes before the launcher fix arrived. (d) The server's password comes from
  $env:QSI_PASSWORD in the launching window only; app\access_password.txt does not exist on
  the workstation; an unset variable starts the server with the shared password OFF behind
  Cloudflare Access alone. W1: the launcher refuses an empty password and prints the source,
  never the value. W2: the runbook's restart procedure starts with the set line. Pre-mortem
  18. (e) W1 job 1 CLOSED 22:30: server on BT2 by default on d607d22; payload diff against the
  morning's engine-bt2 save PASS, all three Run payloads IDENTICAL (my --skip-full made the
  first diff void; the second was run in full).

- 23 Sep 2026 (John): FREQUENCY GOES INTO THE DEPARTURE-OPTIMUM CACHE KEY, inside the freeze.
  Verbatim: "I have been noticing odd results on occasion in the last 23 houts. The Taif result
  optimised changed a couple of times as I ran it. Our model should be consistent It sounds
  like this is the cause of that inconsisteny so we should absolutely fix it and inclde freq
  in the opt method." Context: W1 job 0 (parallel Optimise, 345e2e3) measured 5.5-6x (full
  sweep 78.6 / 85.2 / 58.7s at 8 workers against 466.7 / 429.0 / 332.3s at 1) with Run
  payloads identical, but the SJC-TPE full-sweep payload differed in 57 fields, all in the
  final forecast's departure block (beyond feed 0.058 -> 0.047, the curve). Cause, read in
  code: the departure-optimum cache S[_dk] in calibrated_forecast omitted the weekly
  frequency, which optimise_departure receives and qsi_feed uses (itinerary frequency = the
  lower leg); the 7x sizing pass filled the cache and every later call on the pair in the
  same process, the final Optimise forecast and any later Run included, read the 7x curve.
  The eight-worker figure was the fresh one. Fifth instance of the missing-key silent default.
  Consequences: (a) W1 adds freq to the key (one line; no demand logic changed); (b) feed
  figures move on any route whose chosen or entered frequency is not 7x; (c) W3 re-runs every
  SJC-TPE and Bologna-New York figure in the deck, pack and video after the fix and compares,
  before 3 Oct; (d) the three-run pool test repeats with a fresh control, since today's
  control carries the cached figure; (e) a cell now runs a departure optimisation per
  frequency, so the sweep is slower per cell and the worker count matters more; measured next.
- 23 Sep 2026, evening (controller): W1 JOB 0 PASSED. Three-run test on 4e5dd3c: sequential
  control after the cache fix 491.6 / 523.4 / 404.6s (SJC-TPE, BRS-EWR, DUB-DFW full sweep;
  named 72.9 / 97.0 / 67.3s); eight workers 96.9 / 117.3 / 91.0s (named 54.6 / 76.3 / 55.2s);
  --diff OPT-23Sep-fix-w1 v OPT-23Sep-fix-w8 PASS on all nine payloads. The fixed
  sequential run also matched the 22 Sep eight-worker full sweep on SJC-TPE exactly, which
  confirms the cache diagnosis from the sequential side. Both pre-fix saves (OPT-23Sep-w1,
  -w8) are superseded. Twelve workers not run: nine cells cannot use them. Next: split a
  cell by frequency so the single-airline case parallelises; same test, same diff.
  Server left on eight workers, BT2, 4e5dd3c. Also 23 Sep: ssh to donatello as aviaremote1
  refused the password (RustDesk route used instead); the launching window on 22-23 Sep was
  elevated ("Administrator" title) and E: was present, but the restart procedure says
  non-elevated; a click inside a running probe's console pauses it (QuickEdit), do not.
- 23 Sep 2026, late evening (controller): W1 JOB 0 SHIPPED WITH THE FREQUENCY SPLIT. On
  6065e18 the sweep is two stages (9 sizing forecasts, then 63 frequency tasks) so the
  single-airline Optimise uses the pool too. Measured on the workstation, every payload
  identical to OPT-23Sep-fix-w1: sequential 370.0 / 410.3 / 323.0s full, 56.8 / 78.2 /
  55.4s named; eight workers 66.5 / 109.3 / 64.7s full, 30.3 / 32.6 / 18.4s named. Twelve
  workers: a worker was killed mid-sweep (memory: 3GB DuckDB cap plus the process's own) and
  the pool stayed broken so every later Optimise failed in two seconds; sixteen not run.
  Default stays eight. Fix written (a broken pool is discarded and rebuilt on the next call,
  the failed job reports it): COMMIT-MSG-23Sep2026-w1-pool-rebuild.txt, not yet pushed.
  The server was found down at 20:15 (dashboard "Failed to fetch"); relaunched on 6065e18 at
  eight workers. The sequential control being faster on the split code (370 v 491s on
  SJC-TPE) with identical output is recorded as unexplained.
- 24 Sep 2026 (John): MUST FIX, a curfew that moves the departure must move the headline.
  Verbatim: "Lets log taht as a must fix. If the curfew starts at 2100 and the curfew says
  the route at 20:59 is the best route available and it is 130k, the resulting forecast
  should show 130k, and you use the chart to show what the forecast would have been if the
  curefew hadnt restricted the choice of start times." Context: SJC-TPE, China Airlines 7x
  A359, curfew at origin 21:00-06:00 moved the outbound from 00:15 to 20:59 and the headline
  stayed 172,216 (77,414 local, 94,802 feed) because since 15 Aug the feed LEVEL is the V1
  flat capture and only the timing comes from the QSI model; the curve is scaled to the
  headline, so the departure cannot move the number. Ruling: when a restriction binds, the
  connecting-feed headline is the flat level scaled by the permitted departure's score
  against the unrestricted optimum (the cost the optimiser already returns), the chart
  shows the unrestricted figure as what the route would have carried, and the page says so
  in words. Unrestricted runs are unchanged. This is an approved exception to the demand
  freeze, confined to restricted runs; W1 builds it; acceptance is the three-pair diff
  (unrestricted payloads IDENTICAL) plus a restricted SJC-TPE run whose headline equals the
  curve at the chosen departure. Wording on the page and in the pack: W3, W4 informed.
- 24 Sep 2026 (John): "the optimise times have all been super wuick" on the eight-worker
  server with the MCT master loaded, recorded as the first user-side reading of job 0.
- 24 Sep 2026 (John): RULING, Optimise headline with nothing selected. Kill test step 2
  completed on the rebuilt pool (pass) but returned EVA B789 5x winter 51,196 for SJC-TPE
  with season and airline blank, the same result John called nonsense on 23 Sep; the
  annual China Airlines 7x A359 row (172,216) only appears when season is set to annual.
  Cause: api_optimise ranks every row, seasonal included, by nearest-to-80% load factor;
  economics never enter the choice, so a thin winter schedule beats a 7x annual one.
  Verbatim: "to paraphrase we will change to do the optimised annual if nothing is
  selected.  but if there is an optimised seasonal case that is better that emerges, it
  will put a note in the result that a X service winter summer would achive a higher LF if
  they were to run that (i.e. select summer and optimise again.  Then we have told them and
  they can decide what they want to do". Build (W1): season blank means the headline is the
  annual row carrying the most two-way passengers within the viable load factor band (band
  limits to be set by John; 65-85% is the working assumption until then); seasonal rows
  stay in the sweep table; when a seasonal row beats the chosen annual row on load factor
  the result carries one line naming it ("A 5x weekly B789 winter-only service would run at
  76.7% load factor; select Winter and Optimise again to see it") and no line otherwise; an
  explicit Annual, Summer or Winter selection is honoured as today and the line is
  suppressed. Ships with the curfew must-fix (same selection code), acceptance is the
  three-pair diff plus a blank-form SJC-TPE run whose headline is the annual row, run three
  times with identical output. Panel wording that "optimised" means the best-supported
  schedule by demand, not the most profitable, goes to W4.
- 24 Sep 2026: kill test on 19d94df, eight workers. Mid-sweep worker kill: panel showed
  "Optimise failed: a worker process was terminated (memory or crash); the pool has been
  rebuilt, run Optimise again" (PASS); the next Optimise completed (PASS). Idle-worker case
  Idle-worker case run 14:30: the pool manager took the other seven down with the killed
  worker (count 0), the next Optimise rebuilt it (count 8) and completed in 74s. PASS both.
- 24 Sep 2026 (John): RULING, the blank-form Optimise searches 3x to 7x weekly only. First run
  of the passengers-in-band rule returned Starlux 14x A359 (163,061 each way, 73.2%): demand
  rises with frequency (7x 91,639, 10x 124,131, 14x 163,061 on the sweep table) so the biggest
  schedule inside the band always wins. Verbatim: "I 100% agree that a new long haul route on
  a new service will almost only ever launch a 3x 4x 5x or 7x and providing numbers beyond
  that just makes the tool look foolish.  One of the relationships that emerged in the
  calibration is that the biggest predictor of a new route demand is the capacity that is put
  on.  Partly self fulfilling as the airlines discount to fill the capacity they have added,
  but when looking at forecasts that was one of the bigger vairables in being accurate but is
  not really the same as forecasting demand from usual factors.  I agree that an optimisednew
  route should be capped to look at 7x max and everything before." Two concerns raised and
  answered: the departure curve is per rotation and is unchanged by the cap; on a route with
  direct service the headline is an additional service in a market already served (W4 wording
  line, W2 first fixes "Direct service today: None" on SJC-TPE). Build: 10x and 14x removed
  from the blank sweep (a fixed frequency runs as before); selection rule of the morning
  unchanged. Also found 24 Sep: GET /api/optimise had returned 422 since the 23 Sep split
  (decorator landed on _cell_kw); restored. The sweep table is now in the payload
  (optimised.sweep). W10 question queued: 7x to 14x adding 78% demand on one gauge.
- 24 Sep 2026 (evening): W1 acceptance. Blank-form SJC-TPE Optimise three times identical
  (Starlux 7x A359 annual, 194,922 two-way; the sweep chose 91,639 each way at 82.3% and the
  returned run reports 87.5% with the floor on). Winter selected: Starlux 7x A359 winter-only,
  81,564. Curfew run SJC-TPE CI 7x A359, origin 21:00-06:00: departure 20:59, local 77,414
  unchanged, connecting 94,802 to 34,868, headline 172,216 to 112,282; the factor is the
  departure optimiser's own score ratio (16,415 / 44,630 = 0.368: a 20:59 departure lands
  Taipei at 02:44 and misses the morning bank). First attempt scaled the feed before the
  connectivity re-split and moved local too (77,414 to 63,194); moved after the re-split,
  connecting leg only, spill refilled. The seasonal note is restricted to rows inside the
  band (a summer row at the 87.5% plan cap is spill, not a better fill). Three-pair probe
  on 3x-7x: full 56.6 / 78.7 / 60.7s, named 28.3 / 26.3 / 16.2s; run_SJC-TPE IDENTICAL to
  OPT-23Sep-split-w8; run_BRS-EWR differed by two QSI-share fields against a baseline taken
  before the MCT master, so a same-day control was taken on 68a23d4 (CTRL-24Sep-68a23d4) and
  the diff against it closes the acceptance. OPT-24Sep-select-w8 is the baseline from now on.
- 24 Sep 2026 16:59: the server died mid-request on the DUB-DFW cold Run ("connection
  forcibly closed", then no listener). No Application or System event (no crash, no memory
  exhaustion); its console closed with it so nothing was read. Suspected a Ctrl+C or window
  close while the on-screen keyboard was up; unproven. Fix shipped (ac97cd3): the server runs
  in a PowerShell window that stays open after an exit and every line is teed to
  app\logs\server-<stamp>.log. Pre-mortem 20: nobody touches the server window at the stand;
  W2 runbook line. Second DUB-DFW run completed.
- 25 Sep 2026 (John's paste): workstation C:\src\meridian on main at 0eb7139 = origin/main,
  "Controller 24 Sep close", over eae2757 (carried ranking) and ac97cd3. The workstation runs
  the carried commit; W1 queue item 1 half met (DUB-DFW named-7x probe still to run). DevPC
  log not yet pasted.
- 25 Sep 2026 (John): BOLOGNA-NEW YORK OPTIMISE LOOKS HIGH. Verbatim: "The optimse tool
  chooses United at 7x a week 77w and 222k pax, if you set it to 5x week we get AA 138k on a
  77w. Honestly, 222k a week for a launch route to Bologna seems high. It seems to be becasue
  Venice is 14x but Venice is a global destination, Blogna is lovely but not a global
  destination. I beleive we did a light touch Bologna forecast last year which assumed a 321
  in winter and wide body in summer." Found on Egnyte: /Shared/Archive/2025/Bologna - Traffic
  Forecast Update 2025/Report/SENT 5 Dec 2025/AdB Traffic Forecast Update 2025 FINAL.pptx
  (Avia for AdB, 5 Dec 2025): "A major U.S. Full Service Carrier is expected to launch a
  year-round daily service to New York (JFK or EWR) from Apr 2028 with A321XLR aircraft. From
  Summer 2029 the service will utilise a widebody aircraft (e.g. B787-9) and switch back to
  A321XLR during the winter months. Year-round usage of widebody aircraft is expected in the
  long term after 2031." The report states no route-level passenger figure for New York in
  its text; the route rows live in Forecast/ShortTerm/BLQ_ShortTermForecast(ADF).xlsx (not
  read, 20MB). No mechanism named until the payload (sweep table, market_build) is read;
  block issued to John. Bears on W3 (Bologna-New York figures already provisional, W3-RULINGS
  23 Sep) and W10 (frequency response question).
- 25 Sep 2026 (John's paste): W1 QUEUE ITEM 1 CLOSED. --diff OPT-24Sep-select-w8 v
  OPT-24Sep-final-w8 on the workstation at 0eb7139: run_SJC-TPE, run_BRS-EWR, run_DUB-DFW
  IDENTICAL (the pass condition); the 208 opt_ differences are the new `carried` field on
  every sweep row (absent before eae2757) and DUB-DFW named moving 6x to 7x (capacity 97,656
  to 113,932, carried 85,449 to 99,690, competition_split rows following the frequency), which
  is the carried ranking doing what it was built to do. The two DUB-BOS files in the select
  folder are the stale pair the 24 Sep handover says to ignore.
- 25 Sep 2026 (controller): first BLQ-JFK probe block was wrong: `optimised` is a TOP-LEVEL
  key of the /api/optimise payload (cortex_app circa 3025, final["optimised"]), not
  schedule.optimised; the 24 Sep handover's "schedule.optimised" wording is the run payload's
  block on a restricted run. The market_build did print: whole-service-area today 203,142;
  local by the calibrated model 108,062; carried to the forecast year 112,543 (x1.0415);
  seat-limited to 84,613 (x0.7518); point-to-point carried 84,613 two-way. The connecting
  figure and the chosen cell are not yet read; second block issued.
- 25 Sep 2026 (John's pastes, sweep table and demand block): BLQ-JFK on 0eb7139, blank form.
  Sweep: UA B77W 7x annual chosen, demand 113,382 each way, carried 111,475 each way (222,950
  two-way, the seat cap: 350 x 7 x 52 x 0.875) at 83.9%; DL A333 7x 100,298 / 89,817 on 282
  seats; demand rises with frequency on every cell (UA 3x 71,961 to 7x 113,382). Demand block
  of the returned run, EACH WAY: total_demand 148,271 = local 112,543 (market_build "carried
  forward to the forecast year") + feed 35,728; carried 111,475 = p2p 84,613 (76%) +
  connecting 26,862 (24%; beyond 6,298, behind 20,564); induced False. So the 222,950 headline
  is circa 169k local and circa 54k connecting two-way. THE CONTROLLER'S FIRST READING (62%
  connecting, by subtraction from the market_build) WAS WRONG: the market_build's local
  figures are each way, and its step-5 note "Passengers flying only this route, both
  directions" mislabels an each-way figure (W1 wording defect, queue item 12; John's
  terminology ruling, each-way and two-way always labelled). The high figure is the LOCAL
  model: 108,062 each way captured from a service area flying to New York today of 203,142
  (53% before growth), 225k two-way local demand against Avia's December 2025 AdB assumption
  of a daily A321XLR (circa 112k-124k two-way as a working calculation). Not Venice by any
  step in the payload; the frequency-sensitive capture and the share the calibrated model
  gives a new nonstop of its service area's existing traffic are the two things to question,
  both W10, both frozen before Routes. The sweep's 113,382 against the run's 148,271 is the
  known sweep-versus-run demand difference recorded on SJC-TPE at acceptance (91,639 at 82.3%
  against 87.5% with the floor on); the size of the gap here (31%) goes to W1 to explain from
  the code, no change. W3-RULINGS and W10-RULINGS corrected the same day.
- 25 Sep 2026 (John): BOLOGNA-NEW YORK, the gauge and the number. Verbatim: "77w and 222k
  for a new route just feels like the aircraft is too big for a new route. It is more likely
  to start smaller and test demand and I suspect 77w 222k would make people think our tool
  if not mad, was extremely positive. For me that causes two issues 1) we need to make sure
  we are confident in that number and understand why it happens so we cna see if it causes
  similar reults elsewhere and if we think that is fine or wrong 2) possibly change the
  route as a route for the video if it is giving us any kind of concern." Controller: issue 1
  decides issue 2; two measurements issued the same day, no code change: (a) the local
  capture ratio (market_build step 2 / step 1) on every saved register pair against BLQ-JFK,
  to see whether 53% is the model's habit or this route's; (b) BLQ-JFK fixed at United 7x on
  A21X, B789 and B77W, to see whether local demand rises with the gauge (the capacity effect
  John named on 24 Sep, which would make the carried ranking prefer the biggest aircraft in
  any fleet). Hypothesis to test, not asserted: the optimiser tends to the largest gauge in
  the fleet wherever demand is capacity-driven (SJC-TPE chose the A359, DUB-DFW an A333 with
  "upsize" spill, BLQ-JFK the B77W). Video route decision after the two pastes; the video
  records 26-30 Sep, so the decision is due 26 Sep.
- 25 Sep 2026 (John's paste, Test A): local capture step (market_build step 2 / step 1) on
  the saved baseline run payloads against BLQ-JFK, each way: BRS-EWR area today 1,462,299,
  local model 38,124, ratio 0.026, p2p share of carried 0.317; DUB-DFW 32,858 / 61,695, ratio
  1.878 (a new market: the model gives more than flies today), p2p share 0.389; SJC-TPE
  190,395 / 51,631, ratio 0.271, p2p share 0.45; BLQ-JFK 203,142 / 108,062, ratio 0.532, p2p
  share 0.759. Reading: the capture ratio is NOT a constant habit of the model; it depends
  on what the service area contains (London inside Bristol's area, San Francisco inside San
  Jose's, nothing inside Dublin's). BLQ-JFK's 53% is the highest ratio of the three routes
  that have an existing market, and whether Venice's own New York traffic is inside
  Bologna's service area decides whether that 53% is a share of hub-connecting passengers
  (aggressive, arguable) or a share of another airport's home nonstop market (wrong). The
  payload's catchment block (observed_share, names) and demand.natural / current / captured
  / qsi_share answer that; block issued. Test B (gauge response) still to run.
- 25 Sep 2026 (John's paste, Test B): BLQ-JFK, United, 7x, gauge fixed, each way. A21X:
  local 69,649, total_demand 108,266, carried 57,967 (capacity.seats blank; the generic
  table). B789 (257 seats, UA configuration): local 61,057, total 99,317, carried 81,854.
  B77W (350): local 108,062, total 148,271, carried 111,475. Local demand moves with the
  gauge (+55% from A21X to B77W; the 789 below the A21X is unexplained and goes to W1 to
  read from the code). MECHANISM, from the code's own words (cortex_app circa 1266-1270):
  "The model is anchored on seats ... when the CALLER named a carrier configuration the seat
  count is the airline's own judgement and the back-test measured exactly that case. When
  seats is None the gauge comes from the generic type table, which is Meridian's choice, and
  anchoring on it is circular." The calibrated model takes seats x frequency as an input,
  because launched capacity predicted outturn on the record (John, 24 Sep). Inside Optimise
  the tool chooses the gauge, reads the demand off that gauge, and the carried ranking then
  prefers the largest aircraft in band. A predictor has become a lever. This is systematic,
  not Bologna's: SJC-TPE chose Starlux's A359, DUB-DFW an A333 with "upsize" spill, BLQ-JFK
  the B77W. Frequency was taken out of the same loop by John's 3x-7x ruling on 24 Sep; gauge
  is still in it. Answers John's issue 1: the number is explained, it will recur on every
  blank-form Optimise with a widebody in the fleet, and the controller's view is that it is
  wrong as a product answer (it reports what the route would carry if an airline chose that
  metal, not what an airline should choose). Options put to John as item 58.
- 25 Sep 2026 (John): ITEM 58 RULED (b), ANCHOR THE SWEEP. Verbatim: "I agree that we should
  go with B. One thing that is relebant in the earlier drafts I think we also used to optimise
  fr airline profitability. From memory we removed it beasue the profitability is generic to
  LCC, FSC, ULCC and Reg, and so deemed not accurate enough for a forecast but useful enough
  as a directional guide to an airport. I am wondering whether that was a mistake, if we had
  optimising for the the best margin wuld be another way of removing these large heavy
  aircraft, so bring that back might achieve the same goal." Controller's answer: profit as
  the objective would not remove the loop, because the loop is in the demand read, not in
  the objective; a 77W that the model fills to 84% with demand it created from the 77W's own
  seats has the lowest unit cost in the sweep and would win on margin too, most likely by
  more. The earlier removal stands for the reason given (generic economics by carrier type).
  Profit returns, if at all, as a directional second line on the anchored sweep after Routes
  (backlog). W1 builds (b) now, in the controller chat: reference gauge per airline = the
  smallest long-haul type in that airline's sweep; demand read once per airline x season at
  the reference gauge and 7x (the existing stage-1 sizing pass, re-anchored), frequency rows
  3x-7x from that demand, aircraft sized to carry it within the band; Run untouched.
  Acceptance: three-pair run_ diff IDENTICAL against OPT-24Sep-final-w8; BLQ-JFK sweep table
  before and after; blank-form SJC-TPE three times identical. Freeze exception approved by
  John, confined to api_optimise selection code. W3, W4, W6, W10 rulings lines follow the
  acceptance, not before.
- 25 Sep 2026 (John), on the anchored sweep and SJC-TPE: "remember the TPE deck includes the
  curfew, but I would hope the numbers do end up being consistnet". Noted for W3: the deck
  figures are curfew runs (the 24 Sep must-fix moved the connecting leg on restricted runs),
  so the W3 re-run after the anchored sweep compares like with like: Optimise result, then
  the same schedule as a curfew Run, both on the new server, against the circa 120k figure
  presented to the Taipei carriers.
- 25 Sep 2026 (controller, CORRECTION, before any code was touched): OPTION (b) IS ALREADY
  HOW THE SWEEP WORKS. Read in api_optimise before building: _cell_kw (cortex_app 2605) runs
  every sweep forecast with aircraft="A21N", so stage 1 and stage 2 read demand at a generic
  A321neo gauge for every airline and frequency, and aircraft_select.select_aircraft then
  sizes the aircraft to that demand within the band. The B77W on BLQ-JFK is not the gauge
  loop choosing the biggest aircraft: it is the aircraft that carries the A21N-anchored
  demand of 113,382 each way at 7x (113,382 / (7 x 52 x 0.875) = 356 seats). The loop shows
  only afterwards, when the returned run re-reads the chosen 77W and reports 148,271 (the 31%
  sweep-versus-run gap). Test B's A21X reading (108,266 total at 7x) is the same anchored
  demand within the generic-seat difference between A21N and A21X. So the question is back
  where Test A left it: the calibrated model's read of BLQ-JFK at a narrowbody anchor is
  226k two-way total (69.6k local each way on an A21X in Test B; 53% of the service area's
  existing New York traffic plus feed), about double Avia's own December 2025 AdB
  assumption. That is engine demand logic, frozen, and W10's. Item 58 is re-put with the
  options that remain. The controller ruled (b) without reading the sweep code first, which
  is the mistake chat 3 recorded twice; recorded here as the third time.
- 25 Sep 2026 (John): THE ENGINE FREEZE IS CONDITIONAL, NOT ABSOLUTE. Verbatim: "engine not
  changing was a ruling based on a degree of confidence that the numbers emerging were
  sensibe, if we find numbers like this that would make the tool look wrong we have to
  change it. We are launching to the worlds air service experts, many will naturally just
  have a feel for the answer and where our numers are way off that will immediately make
  people dismiss it. and that would destroy the opportunity to sell it reputationally for
  good. So we cannot keep to a ruling just because that is our stated preferred plan if the
  pla has to change it has to change." Also, earlier the same day: "seems like we stuck in a
  circle untol W10 and W1 have fixed the calibration of the engine we cant say what the
  final numbers are and therefore whether the Bologna forecast stands or will reduce."
  Ruling as recorded: the engine demand logic may change before Routes where a measured
  face-validity failure is found; every change is measured on the back-test before it ships
  (the accuracy pair is re-scored, item 55), applied by W1 from a diff W10 writes up
  (README code ownership unchanged), and accepted by the three-pair probe plus the
  face-validity register. The 10 Oct demo-path freeze then freezes the corrected engine.
  Consequences accepted: the video cannot be recorded on figures that may move (record
  window moves to after acceptance, 8-10 Oct at the latest); W3's SJC-TPE and BLQ-JFK
  figures stay provisional to the same date; W4 v3 wording follows. Programme: (1) 25-26
  Sep, face-validity register: blank-form Optimise on circa twelve routes an air-service
  planner has a feel for, tool answer beside an analogue actual from the stores, to measure
  how widespread the over-read is before anything is changed; (2) 29 Sep, W10 diagnosis:
  long-haul capture share, frequency response, seat anchor in indicative mode, and what mix
  of long-haul secondary-city launches the 2,915 contain; (3) 30 Sep, John decides the fix
  from measured options; (4) 1-6 Oct, W1 builds, W10 re-scores; (5) 7-8 Oct acceptance, W3
  re-runs every figure, video recorded; (6) 10 Oct freeze. Pre-mortem 21 added.
- 25 Sep 2026 (John), SJC-TPE is not a face-validity concern: "SJC TPE with a curfew says 120k
  not sure what the non curfew was but probabky arund 172k so dont think thta is too
  different." Matches the 24 Sep acceptance: CI 7x A359 unrestricted 172,216 two-way,
  curfew 21:00-06:00 at origin 112,282; the Taipei deck's circa 120k is the curfew case.
  SJC-TPE stays on the register as the control (a route John judges sensible), not as a
  suspect.
- 25 Sep 2026 (John): THE FACE-VALIDITY REGISTER IS AVIA'S OWN CLIENT FORECASTS. Verbatim:
  "W10 is open but notihing has happend fo 2 days. Can I suggest you go and look at the
  forecast s on egynte prepared by the team in the last 12 months and maybe even soem pre
  covid. A 100k potential route in 2018 is unlikely to be a 200k potential route now. so
  that will give you a range of routes with the numbers the analyst thought were reasonable
  and were profived to clients who agreed. We then forecast those for 2027. ours doesnt need
  to match but we should be directionally near them mostly." Done the same evening: 71 route
  assumptions read off Egnyte (Bologna 2025, LCY Lightning 2025, Abha 2025, Tashkent 2025,
  Shakira 2023, Zagreb 2026, Knock 2026 and 2018, Scotland 2018 and 2019); twenty with a
  stated passenger figure form the comparison set in routes/FACE-VALIDITY-REGISTER-
  25Sep2026.md v2 (Knock 2026 the cleanest: sent to the client, first full year 2028, local
  and connecting stated). The twelve-route register of the afternoon is superseded. Meridian
  runs each as a fixed-input Run on the analyst's inputs for 2027, then a blank Optimise.
  W10's job 1 (analogues from the stores) is withdrawn; W10 keeps the diagnosis (29 Sep)
  and the fix options (30 Sep), and gets the register results as its evidence.
- 25 Sep 2026 (John's paste, the register Runs): twenty fixed-input Runs on the analysts'
  own inputs, table and reading in routes/FACE-VALIDITY-REGISTER-25Sep2026.md (Results).
  Headline: fourteen of twenty are seat-capped, so the carried figure agrees with the
  analyst only because both fill the aircraft; the demand behind it is 2 to 5 times the
  analyst's on every route ending at the airline's hub (NOC-FRA 94,958 v 19,379; EDI-JFK
  243,468 v 94,397; AHB-DXB 235,394 v 106,830), while the five routes below the cap read at
  about half the analyst's figure (NOC-KTW 0.34, NOC-BER 0.51, EDI-DEL 0.54, AHB-ADD 0.58,
  AHB-IST TK 0.73). Local carried on the Knock rows is a third of the analyst's local. The
  over-read is systematic on hub routes and the under-read systematic on thin ones; not
  Bologna's alone. Diagnosis needs local_model, area_today and the feed fields per row
  (in the saved JSONs); Optimise block still to run.
- 25 Sep 2026 (John's paste, the demand fields): the register's second table and the
  controller's reading are in routes/FACE-VALIDITY-REGISTER-25Sep2026.md. Two mechanisms:
  (1) the V1 flat connecting capture gives a regional route into a major hub a feed 10-25x
  the analyst's (NOC-FRA circa 39k each way against 2,800 two-way; NOC-CDG 44k against
  4,400), because it is a share of the hub's market and does not scale with the route;
  (2) the local read is half to a third of the analyst's on thin non-hub routes (BER, MUC,
  KTW) and several times the service area's existing traffic on small origins (AHB-IST
  flynas 5.5x, KWI 2.9x, DEL 2.6x, EDI-CAN 1.5x). Where the origin's own market is large
  the local agrees (NOC-FRA 17k v 16,600; NOC-CDG 48.7k v 50,000). Hypothesis for W10: the
  back-test scores carried on realised launches, so a model that over-reads demand and
  caps at seats x LF scores well; the 89/82 pair may be substantially a capacity claim, and
  item 55 must be answered with that in view. Fix shape (not yet a fix): feed as a share of
  the route's own size by haul and hub, and a bound on local stimulation against the
  service area; measured on the back-test first. W10 diagnosis 29 Sep; options 30 Sep.
- 25 Sep 2026 (John), the Knock caveat: "worth noting that NOC is probably one of the hardest
  airports to forecast for. It shares its catchment with essentially all Irish airports but
  has very little reason to be the main point of entry. Analyst forecasts tend to use much
  more art than science on Noc forecasts so I would not be surprised to see discrepancies
  there, but not on Edi or larger airports, they should all be consistt." Applied: the Knock
  rows are downgraded to indicative in the register. The Edinburgh rows carry the finding on
  their own: EDI-BOS analyst 91,062 (43,000 local, 48,000 connecting), tool 230,924 (local
  137k two-way, 3.2x the analyst and 1.2x the service area's whole Boston traffic today;
  feed 88k, 1.8x); EDI-JFK 243,468 v 94,397; EDI-PVG 124,826 v 52,753 (local 42k, feed 82k);
  EDI-HKG 107,032 v 52,404; EDI-CAN 86,094 v 36,391 (local 24k from a service area flying
  16k). Two to two and a half times on every hub-ended long-haul from a large established
  airport, in both the local and the feed; the pre-COVID caveat does not cover a factor of
  2.5. The finding stands without Knock.
- 25 Sep 2026 (John's paste of W10's message, dated 24 Sep, "session 1 state"): W10 has run
  nothing; its clone was at 7c15c3d; it had not read the 22 Sep evening re-ruling of item 1
  (W10-RULINGS, option (A)) and reports item 1 "blocked on you"; item 2 (claimset baseline)
  block is with John, unrun; item 3 traced (92/86 built on sklearn 1.7.2 / airportsdata
  20260315, memorisation config, mixed basis; expected lower on the declared environment).
  W10's three code facts are accepted as evidence: the BT2 claimset's capture feature comes
  from bt2_capture.py via the connection builder and no file in the training chain
  references route_forecast or a radius. That matters for the register finding: the scored
  model and the product's demand path share bt2_forecast but not route_forecast's feed, so
  the flat V1 feed that produces the hub over-read is OUTSIDE what the 89/82 record scored.
  Controller's ruling to W10 (rulings file, 25 Sep late): item 1 is (A), as ruled 22 Sep,
  John's confirmation is step C item 7; item 2 runs first, on John's paste; the diagnosis
  of 29 Sep adds the register's two tables and must state which of the two mechanisms the
  record scored (local via bt2_forecast) and which it never saw (feed via route_forecast).
- 25 Sep 2026, late (John's paste): W10 ITEM 2 PASSED. bt2_claimset.py on the workstation,
  E:\Avia\bt2_relaxed, six cohorts, target nonstop, PYTHONNOUSERSITE set: build python
  3.12.10, sklearn 1.9.0, numpy 2.3.5, scipy 1.18.0, airportsdata 20260803; n=6,524 (286
  pax>1.1x-seats artefacts excluded). Calibrated 83.2 / 70.0; blind route 60.9; tier A 88.2
  (n=653); portfolios of 10 and 20 87.7 / 93.2; segments blind 72.6 (short-haul, domestic or
  LCC, n=2,988) / 39.8 (long-haul, international, FSC, n=1,486). All eight figures equal the
  22 Sep baseline to the decimal (W10-STATUS v1 line 54). Log E:\Avia\probe\claimset-W10-
  25Sep.log. The record's own weakest segment, long-haul international FSC at 39.8% blind,
  is the segment the register found over-read by 2-2.6x and the one a Routes visitor will
  type. Block 3 (item 3, mixed basis) may run now.
- 25 Sep 2026, late (John's paste): W10 ITEM 3 RUN on the declared environment
  (bt2_mixed_basis.py, sklearn 1.9.0, airportsdata 20260803, n=6,524; log E:\Avia\probe\
  mixed-W10-25Sep.log). Ruler: 595 US domestic launches regraded on DOT, median DOT/Sabre
  1.015, sources agree within 20% on 67.6%. Model: Sabre throughout blind 60.9 / calibrated
  90.9 (within 10%: 36.3 / 83.5); mixed basis blind 60.1 / calibrated 91.1 (within 10%: 35.7
  / 84.8). US slice: graded on Sabre 61.0 / 94.3, on DOT 51.6 / 90.4. So 92/86 becomes 91/85
  on the declared environment: the mixed basis costs nothing, the library about a point.
  The 91/85 and the claimset's 83/70 are the same 6,524 launches with different fit
  configurations (memorisation it=1600/minleaf=3/leaves=95 against the declared it=800/
  minleaf=5/leaves=63); the blind figure is 60.9 under both. Item 3 is answered; item 55 is
  now a choice between 91/85 (memorisation fit, 6,524), 83/70 (declared fit, 6,524) and the
  interim 89/82 (2,915), all "history known", with blind 61 route-level and 88-93 in
  portfolios beneath every one of them, and long-haul international FSC at 40 blind. W10's
  record v1 states all of this on one page; John rules by 3 Oct. Controller's view for that
  ruling, not a ruling: the honest stand sentence quotes a calibrated pair AND the blind
  portfolio figure, never the calibrated pair alone, and the long-haul segment figure goes
  in the known-issues list.
- 25 Sep 2026, late (John): RULING, THE STAND ACCURACY SENTENCE IS ONE MODEL, ONE RECORD, ONE
  PAIR. Verbatim: "If you are an ASD person and walk past the stnand, and have a 3 min
  oconversation including 2 mins demo. Your question will likely be how accurate is it. this
  needs to be met with when it was used to forecast new routes that have istorically
  launched since 2015 it achieved X/Y within 20/10 over a sample of 7000. That does meant
  the past will predict the future but that is the result. We cannot started talking about
  calibrated, different fits, pickles, part working models, That is far roo comple for a
  stand conversation. For anyone at the conference the andswer is we have one model that has
  produce the forecast you have just done and historically it achieved this. Post Routes
  before sale we can conitinue to refine the model so we do have one tru model but if we
  dont have time before Routes to iron that our we still need to stick to the simple
  explanation." Controller's reading: the sentence shape is ruled; the figures in it are the
  record's, not rounded up: the sample is 6,524 launches (say "circa 6,500", not 7,000) from
  the 2016-2019, 2024 and 2025 cohorts (say "since 2016", not 2015); X/Y is the pair for the
  model the app runs, 91 / 85 subject to W10 matching the pickle to tonight's refit, else
  whatever W10 measures on the pickle. Everything about fits, environments, blind and
  portfolio figures goes to the methodology page, the known-issues list and the host
  manual's second-question answer, never into the first sentence. Item 55 resolves this way
  by 3 Oct; the interim 89/82 stays on the surfaces until W10 confirms the pickle.
- 25 Sep 2026, late (John): TWO RULINGS ON THE STAND. (1) The sample: "sample use the precise
  number it feels more acurate the person on the stand and reduce to circa 6500 but we
  should be precise in writing". So: 6,524 in every written surface; the host may say "about
  six and a half thousand". (2) Optimise on the stand, verbatim: "My one major concern with
  this, is that isf we say 91% is +- 20% and then we start producing forecasts like teh
  Bologna 222k year one, people will begin to question the 91% claim. Obviously 1 in 10 can
  be out with this logic and if the average person only runs one or two on the stand outr
  chances of being questionsed are lower but in practice if I work for Tamp a I will run one
  route I have already done and know my answer and see what the machine gives. Also I would
  expect the optimised version to be the best route or the closest to my number. In practice
  that isnt what optimise can ever do as we wont know the subjective criteria someone has
  steered toward their answer. So I think the people manning the stand have to have a 100%
  clear explanation of what optimise is, so that when an answer comes out that is different
  to what the person expects they can explain it and then RUN an option that closely matches
  the route the person was considering i.e. aircraft, frequence, alirnline, start time, etc
  and hopefully that will be closer as the true model test." Ruling as recorded: the stand
  flow is Optimise, explain, then Run the visitor's own case; the host's explanation of
  Optimise is a W4 deliverable in the manual and is rehearsed; W2's flow keeps Run one click
  from the Optimise result with the visitor's inputs carried across. Controller's caution,
  from the register: a fixed Run on the visitor's own schedule is also 2-2.6x the analyst on
  hub-ended long-haul (the Edinburgh rows WERE fixed Runs), but because the aircraft fills,
  the carried headline the visitor sees is seats x frequency x load factor and often agrees
  with theirs (EDI-JFK 97,460 against the analyst's 94,397); what gives it away is the
  demand and spill line ("demand exceeds 7x A321: 73,000 spilled"). The host must be able to
  read that line as well as the headline. The engine fix remains the real answer.
- 25 Sep 2026, late (John), on the visitor types: "there will be many different types, many
  wont have a idea, many will run routes they havent seen and expect the answers to be
  correct and use the results for teh airlines straightaway. so keep in mind theyre will be
  a range ... Of course their route forecast hasnt been back tested so if they different it
  could be theires that is wrong, but we will never know and what will matter to the person
  is what feels right." Recorded for W4 (the manual covers three visitor types: knows the
  route, no route in mind, will take the pack to an airline) and for the engine work: the
  test is face validity to a planner, which is why the register compares against Avia's own
  analysts rather than against actuals alone.
- 25 Sep 2026, late (John): "Please keep in mind that we need to design the stand hand
  graphics to the graphic designed before the 2 Oct". Ruling as recorded: the wall graphics
  artwork is with the designer by 2 Oct, so the chain is pulled forward: graphics decision
  (item 40, full wall or logo only) and sentence 2.3 (item 44) are decided TODAY 26 Sep, not
  30 Sep; the Full Vision brief goes today asking for panel sizes, file specification, price
  and artwork deadline by Monday 29 Sep; W6 hands the wall words (the one-liner, the product
  name, the site address) to W3 on 27 Sep; W3 artwork 29 Sep to 1 Oct; to the designer 2
  Oct. Controller's ruling on what is printed: the wall carries the one-liner, the name and
  the site, NOT the accuracy figure, because the pair is not confirmed until W10 reads the
  pickle (29 Sep) and may change once more with the engine fix; the accuracy sentence lives
  on the screen, the leaflet and the pack, which can change until 10 Oct. Say if you want the
  number on the wall regardless; then it is 91 / 85 on 6,524 and the fix cannot move it.
- 26 Sep 2026, early (John): THREE INSTRUCTIONS. Verbatim: "Order any pens or giveaways, get a
  website up and running so we can refer to it on the company bio that we could post pre
  rouets today if we wanted and needs to be ready before we send invites so if anyone
  receives it they can see who TAO is. Also my email for thos invites nees to be the TAO one
  not Avia." Rulings as recorded: (1) W9 orders the pens this week (item 54: Observatory name
  and site address; John approves the artwork and pays; W9 drafts the order). (2) W6 launches
  the site BEFORE the invitations go: a first version that says who The Aviation Observatory
  is, what Meridian does (the one-liner), the Routes stand (F124, 21-23 Oct) and how to reach
  us; the competitor comparison page is withheld (19 Sep ruling, item 11) and the price grid
  is on only if it is PRICING-DECISION-2026.md v1.0 word for word; "three seats / 100
  presentations" comes off first. The company bio for a pre-Routes post links to it. (3) The
  invitations go from John's Aviation Observatory address, not Avia's. That needs a mailbox
  John can send and receive from at aviationobservatory.com before the invitations go, which
  is the long pole: it is either a mailbox on the Microsoft tenant (tenant admin is not
  John's; ask the administrator today) or Cloudflare Email Routing for inbound (item 20, DNS
  move) with an outbound sender John can use from Outlook; W2 states which is achievable by
  29 Sep and what John must ask for. Invitations do not go from an Avia address as a
  fallback; they wait for the TAO address.
- 26 Sep 2026 (John): "what does progressive optimise mean. also there is still lots of work
  in the streams that needs doing and is not mentioned. Fix the presentations, adding images
  automatically, demo process i.e. entering an email so that the run they have done can be
  run as a presentation and sent to them. How do we do that. Add a temproary add email to the
  bottm of the run so when they get a numbers result they type their email and the
  presentation is then run and sent to them outside the stand tool but automatically. Or do
  we do that but have someone in UK review the deck not for content but for formatting issues
  and send it manually, or do we just capture the email and the desired route offline and run
  it wehn we have itme, etc etc. All of this needs to be thought thru and decided and set up
  on top of the other changes. Agree they are not as important as getting the engine and the
  forercasts right, but need to be clear and centre before we talk about locked." Answered:
  critical path line 2A and items 61-62; W2 and W3 rulings the same day. Progressive Optimise
  = showing the best schedule found so far while the sweep is still running, instead of a
  spinner until it finishes; deferred (item 59) because the sweep is now under ninety seconds.
- 26 Sep 2026 (John), the same-day pack, amending item 61. Verbatim: "I agree with your
  selection in principle but we need work arounds. What if someone needs the presentation
  right then to take to an airline meeting. Waiting for someone in UK to invisbly vet the
  presentation would be perverse and make it feel unautomated. No one on the stand has the
  knwoeldged to check the presentation, so when it is needed becomes a point. now, automatic,
  in 30 mins send to UK but auto sent after 30 mins if no one has time to review. UK person
  has chance to pause an auto send if the deck produced is utter nonsense, but we need to
  make this slick as I am not sure of the volume, If we have 20 over 3 days that is doable
  but if we had 150 over 2 days probably not if we dont want to deay the send too long."
  RULED (item 61 as amended): every pack job has one of three states set at the stand: NOW
  (the host ticks it for a visitor who needs it for a meeting; sends the moment the build
  passes its own checks, no human review); HOLD (the default: sends automatically 30 minutes
  after the build passes unless a reviewer pauses it); PAUSED (a reviewer stops it with a
  reason; released by hand or re-run). The build's own checks stand in for a reviewer where
  nobody looks: the build completed, every section rendered, no placeholder or missing figure,
  the ruled sentences present, images resolved or mood frames substituted, file author Avia
  Solutions; a build that fails a check goes to PAUSED, never to send. The reviewer's view is
  a list with a one-page PDF preview per job so a glance is enough; at 150 jobs in two days
  that is one every ten minutes of the show and the 30-minute auto-send keeps the flow if the
  reviewer is behind. W2 builds the states, the timer and the checks hook; W3 supplies the
  build checks and the preview. Item 62 (the reviewer) stands, with the volume caveat.
- 26 Sep 2026 (John), three rulings on the pack. Verbatim: "For these decks Avia Solutions is
  not the author Aviation Observatory will be the author. The times I made up 30 mins might be
  45 or an hour i,e the longer it takes a presentation to arrive the less speedy will be the
  impression and the question about whether it was blocked by email blockers etc comes up.
  But if the manual checks finds things then send something wrong is worse. My preference is
  that the default is that automatic send is the goal and fine because we are so confident in
  the presentation decks but in 4 weeks I am not sure we will reach that point hence the
  thought about manual intervention. Problem is Jess and Jol are rightly QA professionals and
  will never want to release something until it is perfect and spending 4 hours per
  presentation fixingthem wont be an option either." RULED: (1) AUTHOR: every product output
  (visitor pack deck and workbook, PDF, stand deck, video, pens, wall) carries The Aviation
  Observatory as author and last-modified-by; Avia Solutions stays the author of Avia's own
  deliverables and the programme files. The controller's ruling of 26 Sep on W3 conflict 1 is
  REVERSED. (2) HOLD TIME is a setting, not a constant: John sets it (30, 45, 60 minutes or
  zero); the goal is zero, automatic send. (3) THE REVIEWER IS A PAUSE, NOT A QA PASS: the
  reviewer never edits a deck; a job either sends as built or is paused and the visitor gets a
  short holding email the same day ("your pack follows tomorrow morning") with the pack sent
  once the template fault is fixed. The QA effort goes BEFORE Routes, on the generator, not on
  the outputs: a rehearsal batch of 30-50 packs on the register routes, built automatically in
  the week of 6-8 Oct, QA'd by Jess and Jol against a written formatting standard; every fault
  found is fixed in the TEMPLATE and the batch re-run until a whole batch passes; then the
  hold timer is set by John from what that batch showed. Item 62 (reviewer name and hours)
  stands; with the pause-only rule it is a small job.
## Waiting on John

1. CLOSED 19 Sep: HEAD `11a4c3f` confirmed and pushed.
2. CLOSED 19 Sep: aircraft-econ code committed at `11a4c3f`. Live check on the workstation
   still owed before 10 Oct (master list 6.6).
3. **The timing block (step B)**: issued 19 Sep. Commit the probe on the DevPC, pull on the
   workstation, restart the server, run it, paste the table. If not by 23 Sep: W1 cannot start, the 21 Oct speed acceptance is at risk
   from day one, and the stand plan is written on the Plan B assumption (pre-rendered panel,
   pitches queued for the evening).
4. **Stand host's name, contact and start date; the stand number.** In no document. Needed
   for W4 and for the Cloudflare Access policy (pre-mortem 7).
5. CLOSED 19 Sep: six of seven answered (Decisions log). Open remainder below.
6. CLOSED 20 Sep by PRICING-DECISION-2026.md v1.0: 50% year 1, NO LIMIT on places, expiry 30
   November 2026; overage replaced by fair use at 250 packs; payment annual in advance, 14 days;
   entity still item 31.
7. **Tier shape**: CLOSED 20 Sep by item 37 for airports (three capability tiers). Airlines
   and advisers remain "quoted"; the commercial plan's Airline / Adviser tiers are not
   priced for Routes.
8. CLOSED 20 Sep: two emails per visitor (John's 19 Sep ruling stands; item 22 records it).
9. CLOSED 20 Sep: not on the tenant and it does not need to be; Postmark is the sender,
   domain verified 19 Sep (W2-STATUS v7). Inbound mail comes with the Cloudflare move (item 20).
10. **Host training**: the plan says 14-16 Oct in person; Suzanna lands 20 Oct afternoon.
    Proposal: two remote sessions 14-16 Oct on the frozen build over video, and an in-person
    run-through on the stand or hotel on the evening of 20 Oct. Silence to 1 Oct: as proposed.
11. **Site launch and the competitor page**: the staging site carries a competitor
    comparison page and the full price grid under a "provisional" banner. Launching before
    Routes puts both public, against the 19 Sep ruling of nothing about any competitor in
    any material, and ahead of the final commercial sign-off the pricing note requires.
    Decision needed: launch with the comparison page withheld and the grid signed off, or
    revise the rulings. No default; this one needs an answer.
12. CLOSED 19 Sep: delegate list read; organisations recorded.
14. CLOSED 19 Sep: 1TB external NVMe SSD, USB-C, on the core x86 laptop; order before 28 Sep.
15. CLOSED 19 Sep: extend; DuckDB `leads` table now; professional capture front end on the
    stand (W2); CRM after Routes.
16. CLOSED 19 Sep: yes, the MCT master reports and the stand build refuses to start without it.
17. CLOSED 19 Sep: agreed (1 Oct go/no-go, 8 Oct proof, 10 Oct loaded, 15 Oct hard stop).
18. CLOSED 19 Sep as a question, reopened as a build item. The workstation is unmanned; John
    runs everything remotely, including Boeing. Restart procedure for Routes: remote desktop
    over Tailscale, sign in, run both launchers, DISCONNECT (never sign out, which kills the
    servers). Written into the runbook and host manual; rehearsed once in the 11-12 Oct trial
    with a deliberate restart. Better answer for W2 if time on 8 Oct: scheduled tasks at
    system startup for Meridian and Atlas, so an auto-reboot needs nobody. Check once that
    the Cloudflare tunnel runs as a service.
19. **Suzanna's practice runs**: they write to the lead store and use the one-pack quota. Give
    her a separate lead file (AVIA_DEMO_LEADS) on the stand build. Silence: separate file.
25. **WHAT THE 89% DESCRIBES, the stand sentence.** SETTLED IN SUBSTANCE 22 Sep (decisions
    log). John's sentence stands: this forecast uses the model tested on real launches; 89%
    within 20%, 82% within 10%; we cannot say that of a single route; the record is
    republished yearly. The calibrated model IS the on-screen engine from 22 Sep (`--engine
    bt2`), so the earlier worry that the screen ran a different model is closed. What remains
    is item 55. Nick signs the sentence (John asks him with item 53). Master list 2.4 and
    pre-mortem 9 close on this.
26. **Carrier for slide 8, Bologna-New York, and now the figure.** Carrier: no default; W3
    will not pick an airline. Figure (25 Sep): the tool's blank-form answer is United 7x B77W,
    222,950 two-way, of which circa 169k local and circa 54k connecting (the demand block);
    the local demand alone (225k two-way) is about double Avia's December 2025 AdB assumption
    of a daily A321XLR. Decide whether the demo case is the tool's own Optimise answer with
    the local/connecting split stated, or a fixed input (A321XLR daily, the 2025 shape).
    Silence to 30 Sep: the tool's own answer with the split stated, because the stand
    demonstrates Optimise and a hand-picked schedule is not the product; W10 carries the
    capture-share question.
27. **Decks already sent without rights records** (the 94 JPEGs in the CI deck): the
    controller's ruling is that nothing is re-sent; the exposure is an internal provenance
    gap, not a client obligation, and it goes on the master list as a post-Routes review
    of C:\assets\engagement against its sources. Say if you disagree.
28. CLOSED 20 Sep (John): the worked routes STAY SJC-TPE and Bologna-New York; more may be
    added later. John's never-worked-airport rule for demo and marketing material is set
    aside for these two by his own decision; W6's post-1 chart therefore uses SJC-TPE as
    first ruled, and W4's rehearsed routes stand. Carrier for Bologna-New York still open
    (item 26).
29. SUPERSEDED 20 Sep 18:00 by PRICING-DECISION-2026.md v1.0 where they differ (years 2 and 3
    are FIXED CASH, bands by airports covered). Kept for the record:
    LAUNCH OFFER at Routes: year 1 at 50% of list, year 2 at 75% of list, year 3 at 85% of
    list, then list; no obligation to renew at any step. LIST is the standard price of the
    tier chosen (£15,000 / £22,500 / £27,500 a year; tiers by usage, item 37, NOT by
    airport size), so a launch client pays year 1 at 50% of its tier: £7,500, £11,250 or £13,750, fixed in
    pounds at signing; years 2 and 3 follow the list as published at each renewal. Add-on
    options discussed (the Global Forecast, Design Day, a per-route study if John prices it,
    item 35): 50% off if adopted in year 1, 75% of list if adopted in year 2. In return the
    launch client accepts launch bugs with understanding (the known-issues list), gives
    references, allows use of its name and brand in Avia's marketing, and SIGNS BY 30
    NOVEMBER 2026 (the time pressure). The list is quoted in writing to qualified buyers on
    the one-pager and in the agreement as the reference for the discount; it is NOT
    published on the website until November and may be refined after Routes, which moves
    years 2 and 3, never a signed year 1. The host, if asked: "launch clients who sign by the
    end of November pay half our list price in year one; the list is £15,000 to £27,500 a
    year depending on how much of the tool the airport wants." Still to rule (item 6): the
    number of launch places, the overage rate (now the per-pack price above 100 on Tier 2),
    payment terms, the entity (size thresholds closed by item 37).
    TERM AND RENEWAL (John, 20 Sep, later): the one-pager and agreement show a three-year
    schedule with list inflated at a stated flat 3% a year for illustration (list is reviewed
    annually; no index named), and the launch client gets THREE FIXED CASH PRICES for years 1,
    2 and 3 (50%, 75% and 85% of the inflated band), so they have price certainty if they
    proceed. Renewal is annual and automatic unless the client cancels at least one month
    before the renewal date; Avia notifies three months and again two months before. The
    auto-renewal opt-out is CONDITIONAL, not priced (John asked about a 10% premium; the
    controller advised against): available only to a client that declares its procurement
    rules do not permit evergreen terms; for everyone else the clause is standard and stays,
    and the launch terms are offered on the standard agreement as it stands. AVIA ENDING THE
    SERVICE: the agreement states what happens if Avia withdraws or suspends the service for
    any reason, including loss of a data licence: notice, a pro-rata refund of the unused part
    of the year's fee, the client keeps every output already delivered, and no further
    liability. Solicitor drafts the clause; W5 marks it.
    ANNUAL ESCALATION (John, 20 Sep, later): every agreement states that the standard price
    moves each year by AT LEAST inflation (UK CPI, ONS, twelve months to the preceding
    December), applied at each renewal; the launch cohort's three fixed cash prices are the
    stated exception, and from year four the client is on the list and the same escalation.
    NEW FUNCTIONS: offered as priced options the client may accept, or, where Avia folds a
    function into the core product, the core price may rise above the annual escalation at a
    renewal on the same notice as the renewal itself. The expectation is set in the first
    contract, not the second.
30. CLOSED 19 Sep by the controller: the pack promise reads "follows the same day" everywhere
    until proven at the 11-12 Oct trial.
31. CLOSED 21 Sep (John; "settled ages ago"): THE AVIATION OBSERVATORY LIMITED, company number
    17411365, registered office 86-90 Paul Street, London EC2A 4NE, contracts and invoices for
    everything from day one, so the business is self-contained. This overrides W8 decision 15
    (Avia Solutions Limited); W8 issues v1.1 with the correction. Two formalities outstanding,
    now on the order-ready checklist: PI insurance extended to TAO Ltd (the insurer owes a
    proposal; no client contract is signed before it is in place) and a TAO Ltd bank account
    (needed before the first invoice). Egnyte: /Shared/Management/Management Information/A3/
    The Aviation Observatory/.
32. CLOSED 19 Sep: `Aviaacct1/tao-website` pushed at 2df95ee; W6 edits it through John's
    blocks; C:\src\avia-website read.
35. CLOSED 20 Sep: Meridian route study £2,500 per route (PRICING-DECISION-2026.md v1.0, decision
    4), on the price list, the licence leads the one-pager. Original text: (20 Sep, controller's proposal after the
    cash change): a Meridian route study, the researched pack for one route, priced per route
    (Avia's own consultancy anchor is the reference), invoiced on delivery, no licence, no
    procurement of a tool. It is the purchase a route development manager can sign off alone
    in November; the licence is the purchase that needs a board. Both on the one-pager, the
    study first. Needs a price from you; W5 carries the slot. Silence to 3 Oct: not offered.
36. **Order-ready code half before the freeze**: per-client Cloudflare Access policy per
    signing client (dashboard task, W2 writes the steps, John clicks); attribution from the
    Access identity confirmed (master list 6.8); the shared Basic-auth password stays for the
    first clients and is stated in the known-issues list; monitoring is the restart procedure
    plus John's phone. Ruled by the controller; say if you disagree.
37. CLOSED 20 Sep 18:00: PRICING IS FINAL in routes\PRICING-DECISION-2026.md v1.0 (W8; twenty
    decisions answered by John the same day, section 11). Bands by AIRPORTS COVERED: one £15,000;
    two to nine £22,500; ten or more £30,000; the whole product in every band, no user count. The
    usage-tier table that stood here is withdrawn; the four rulings files carry a pointer only.
33. **W3's coverage probe**: one unattended run on the workstation by 26 Sep (W3 has the
    block); without it W3 drops airport photography and ships mood frames and charts.
34. **W4's three**: a second and third phone contact who can reach the workstation; your
    stand hours and meeting slots; approve or rewrite the competitor sentence in manual 4.4.
20. **DMARC reporting and the domain's DNS**: move aviationobservatory.com DNS to Cloudflare
    in the week of 22 Sep (W2 recreates the four Postmark records and re-verifies; Email
    Routing then gives the domain an inbound mailbox, which W3's image-source sign-ups and the
    DMARC reports need; W6's site launch on Cloudflare Pages uses the same zone). Silence to
    26 Sep: yes.
21. **Public pack URL controls** (W2 watchpoint 5): noindex header, an expiry, no personal
    data in the file, and every pack checked against the Sabre position (attribution
    constant, fares as bands, no single-route blind figure) before it is hosted. Controller
    rules yes to all four; W2 the hosting controls, W3 the content check. No answer needed
    unless you disagree.
22. **One email or two** (W2 still recommends one). Your 19 Sep ruling of two stands unless
    you say otherwise; the queue view then shows both sends separately.
23. CLOSED 20 Sep 21:45: Suzanna answered all four (W2-RULINGS and W4-RULINGS carry her words).
    Input screen intuitive; the OUTPUT / OPTIMISE / RUN ASSESSMENT row is unclear (stand-mode
    requirement); she wants the known weak scenarios; Optimise slow in her experience (pre step 1);
    accuracy is the question she expects. Offers a call Tue 22 Sep.
24. **Which tablet for the capture front end**, and whether it is yours or bought. Under
    Plan B it reaches the form on the laptop's own hotspot; W2 confirms.
38. **TODAY, 21 Sep: billing details to Charlotte Sullivan (Informa)** so the contract is
    finalised. RULED 21 Sep (John): the exhibitor is THE AVIATION OBSERVATORY LIMITED (17411365,
    86-90 Paul Street, London EC2A 4NE). Stand number CONFIRMED F124 (John, 21 Sep); every
    programme file corrected from F174 the same day. Open until Charlotte's populated form is
    signed. VAT number: John's. Consequence of silence: the last shell stand is not held indefinitely and
    the 3 Oct graphics deadline is missed.
39. **Routes 360 membership, £5,000 a year** (three email campaigns, competition promotion).
    Controller's view: worth it only if the three campaigns can carry the launch offer to
    the registered list before and after the show; ask Charlotte for the send dates and
    audience size before deciding. Silence to 3 Oct: not bought.
40. **Graphics by 3 Oct**: full inlay circa EUR 3,740 or overlay circa EUR 3,980 plus VAT, or
    fascia and counter logo only (included). Controller's view: one printed back wall with
    the one-liner and the accuracy line is what makes a 12 sqm shell read as a product
    stand; W3 does the artwork. Silence to 30 Sep: logo only. PULLED FORWARD 25 Sep late: decision needed 26 Sep so the artwork reaches the designer by 2 Oct (John); the wall carries no accuracy figure (controller ruling, decisions log).
41. CLOSED 21 Sep: the contract files in /Shared/Management/Management Information/A3/The
    Aviation Observatory/Legal/.
42. RULED 21 Sep (John, with the controller's condition): the all-day recording is TESTED ON
    THE STAND on the day, hourly files on the laptop, for general market intelligence only,
    nothing attributed to an individual, transcribed after the show, deleted by a stated date.
    CONDITION: a visible notice on the stand and the host's spoken line at the start of a
    demo; nothing covert (German law, §201 StGB, and Informa condition 4.5). The host's voice
    note and the fifteen-second card drop are the primary capture; the recording is the
    backstop for a busy morning. Stefan as second pair of hands on the busy days. W2 and W4
    carry it.
43. CLOSED 21 Sep: the stray clone at C:\src\meridian on the Dev PC was inspected (clean: no
    changes, nothing unpushed, no stash) and deleted. Test-Path False. The `hostname` line
    comes out of the blocks.
44. **Sentence 2.3, version A or B** (W6-MESSAGING-VARIANTS v3). Controller's view: B on the
    stand and in the invitations, A where one line is all there is. Silence to 25 Sep: B.
45. **The third video scenario, a larger hub for a long-haul pitch** (never a client airport):
    Vienna, Brussels, Lisbon or Copenhagen; Denver, Phoenix, Minneapolis or Seattle. Bordeaux
    and Boise stand from 9 Sep. Silence to 26 Sep: Copenhagen and Denver.
46. **A Suzanna session on the current build before the 16 Oct trial**, week of 29 Sep, so her
    Optimise view is current (W4 watchpoint 4; controller agrees). Book it with her on Tuesday's
    call. Silence: the 16 Oct trial is her first sight of it.
47. **Twelve months' notice to retire the service** (W5 judgement, controller adopts; the Sabre
    sunset shape). Silence to 3 Oct: twelve months.
48. **TAO Ltd has no trading history**: what a procurement department gets when it asks for
    accounts, insurance and a credit reference. Controller's view: the PI certificate once
    extended, and a letter of comfort from Avia Solutions Limited (or the Holdings company)
    standing behind the service; ask the accountant which. Needed before the first airport
    asks, which could be November.
49. **The solicitor and a slot in the week of 6 October** for the whole document set.
50. **Support: the address, the named person who reads it every working day, and the response
    time.** Appears in five documents. Controller's suggestion: support@aviationobservatory.com
    once Email Routing exists (item 20), read by John, one working day.
51. **Have OAG and Sabre been told the contracting party is The Aviation Observatory Limited?**
    Memory says both approved launching through a separate entity verbally on 17 Sep; the
    written confirmation is still owed and the licence record form (W5) captures the calls.
    Known-issues sign-off: Nick, unless you say otherwise.
52. **Register The Aviation Observatory Limited for VAT** as an intending trader (accountant);
    the Informa invoice is then reclaimable under the pre-registration rule; Avia pays it
    meanwhile as an intercompany loan. The invoice template needs the VAT number.
53. **Ask Nick** whether the three classes of number can be renamed "actual, calibrated,
    capped" (Jol's feedback R1; John: "measured" implies an estimate in ASD). Until he answers,
    slide 4 and manual section 2 keep his words and every data surface says "actual".
54. **Pens as the stand giveaway**, Observatory name and site address, ordered this week (W9).
55. **Which accuracy pair the product publishes.** RULED IN SHAPE 25 Sep (John): one model,
    one record, one pair, in the sentence "When this model was used to forecast the new
    routes that launched since 2016, X% of its forecasts were within 20% of what the route
    went on to carry and Y% within 10%, across circa 6,500 launches. The past does not
    predict the future, but that is the record." X/Y = the pair of the model the app runs
    (bt2_model_v1_3.pkl): 91 / 85 on 6,524 if W10 confirms the pickle is the 1.9.0 V1.3
    rebuild scored tonight; otherwise the pair W10 measures on the pickle. W10 states the
    outturn period in one clause for the sentence. Interim until then: 89/82 on 2,915.
    W10 reproduces the 22 Sep baseline, tests the catchment radius, and reproduces or replaces
    92/86 on 6,524; John rules on ONE figure set by 3 Oct. Silence to 3 Oct: the interim pair
    ships and the 92/86 pair stays off every surface.
56. **Open the W10 chat** from the prompt in the controller chat of 22 Sep, and paste the
    original catchment radius text into it if you still have it (the controller restated it).
    Silence: W10 does not start and item 55 defaults to the interim pair.
13. **Pick the five meetings**: John agreed the buyer-test list 19 Sep (Birmingham, Dublin,
    Vienna, Dallas Fort Worth, Milan SEA; reserves in the organisations file, section 3).
    Open point: whether one competitor-client airport goes on the five as a deliberate test
    of budget-holders; controller view is no, the 19 Sep ruling stands until a paid client
    exists, and those airports are Suzanna's priority walk-ups instead. Invitations 26-29 Sep.
58. **THE BOLOGNA-NEW YORK NUMBER, RE-PUT 25 Sep (decision by 26 Sep).** Option (b) was
    ruled and then found to be the existing design (decisions log, 25 Sep correction): the
    sweep already reads demand at an A21N anchor and sizes the aircraft to it; the 77W is the
    aircraft that carries an anchored demand of 226k two-way at 7x. The number is the
    calibrated model's read of the route, not the optimiser's choice of metal. Remaining
    options, none of which changes the engine: (a) LEAVE the Optimise answer and state on the
    page what it is (demand read at a narrowbody anchor, aircraft sized to carry it); (c) the
    VIDEO uses Bologna-New York as a fixed A321XLR daily Run (Test B: 57,967 carried each way,
    115,934 two-way, the 2025 shape), with the Optimise answer shown and explained in the
    stand demo only; (d) a GAUGE RULE of the same kind as the 3x-7x rule: a new long-haul
    route is sized on the airline's smallest long-haul type unless that type cannot carry the
    demand at 7x within the band, in which case the tool says so ("demand exceeds a daily
    787-9; the next gauge is ...") rather than silently reaching for the 77W. (d) is a
    selection-code change in api_optimise, two days, and needs a ruling from John on what
    "smallest long-haul type" means (XLR-class where the airline has it, otherwise the
    smallest widebody); it does not lower the 226k, it changes what the tool proposes an
    airline should fly. (e) W10 tests whether the 53% capture and the frequency response are
    what the 2,915 launches support; no change before Routes either way. Controller's view:
    (c) for the video now, (e) for the record, and (d) only if John wants the stand answer to
    read as a launch schedule rather than a sized one; (a) is the fallback wording in any
    case. Consequence of silence to 26 Sep: (c) and (e), and the Optimise answer on the stand
    stays United 7x B77W with the basis stated.
59. **Progressive Optimise deferred to after Routes.** W2 proposed it (v14); the controller
    rules yes on the measured timing (named Optimise 24.3 / 22.3 / 16.2s, open sweep 52.5 /
    86.9 / 52.6s on 24 Sep): a best-so-far display is not worth the build inside the freeze
    when the host can say "about a minute" and show the methodology page. Silence: deferred.
60. **John's Aviation Observatory mailbox.** Invitations go from it, not Avia (26 Sep). W2 names
    the route by 29 Sep; if it is a tenant mailbox the ask to the administrator goes today.
    Consequence of silence: invitations wait; the five meetings become walk-ups if not sent by
    6 Oct.
61. **The same-day pack: automatic build, approved send.** Ruled by the controller 26 Sep
    (critical path 2A) from John's three options (fully automatic; automatic with a UK
    formatting review then send; capture offline and run later). Confirm, or choose another.
    Silence: as ruled.
62. **The UK reviewer for the queue during Routes**: a named person, their hours on 21-23 Oct
    (UK afternoon covers the Frankfurt day), and a second name. Consequence of silence: packs
    build and nobody sends them; the fallback becomes the plan.
57. **Confirm the git state for chat 4**: HALF CLOSED 25 Sep. Workstation pasted: HEAD
    0eb7139 on main, equal to origin/main, "Controller 24 Sep close: ..."; below it eae2757
    (W1 carried ranking) and ac97cd3 (server console). W1 queue item 1's first half is met.
    Still owed: `git log --oneline -3` from the DevPC (C:\AviaDev). Consequence of silence: the controller records no
    machine state, every command block this week is written on the assumption that the
    workstation is on that commit, and a stale workstation would show 23 Sep behaviour
    (Optimise headline by load factor, no curfew must-fix) in any demo John runs.

---

## 1. Decisions taken 19 September (John)

1. **Licence position**: OAG and Sabre have both confirmed on calls, with multiple witnesses,
   that Avia may use the tool at Routes and share its outputs. Written confirmation is being
   chased. Notification obligations are met. Status: IN HAND for the show; the letter remains a
   gate for the first paid contract, not for Routes.
2. **Pricing approach**: SAY A SOFT NUMBER. An expected list price, stated as soft, plus a
   written year-1 launch-customer discount that visibly expires, for a stated small number of
   places. Not silent testing: budget holders with calendar-year money cannot act on "still
   deciding", and the reaction to a real figure is the only pricing feedback worth having. List
   is refined after Routes from that reaction. The numbers themselves come from the pricing
   chat and go in the follow-up one-pager, never on the stand unprompted; if asked, the host
   gives the expected range and the launch offer in one sentence.
3. **Two milestones, not one** (AMENDED 20 Sep): DEMO-READY 21 October (the stand); ORDER-READY
   now ALSO 21 October (an airport with budget to use this calendar year can sign and be
   onboarded the week it asks). Order-ready is a checklist (section 3), not a rebuild; the
   documents are ready by the 10 Oct freeze and the checklist is closed by 20 Oct.
4. **Messaging gates the meetings**: invitations go 26-29 September, after the message is
   settled (section 4). Late requests at Routes are rarely honoured, so the message comes first
   this week.
5. **Competitors**: no comparison approaches to a competitor's clients before launch; know
   their positioning cold; nothing about them in any material (commercial plan, section 10).
6. **Optimise on the stand**: demonstrated for the interested, it is the USP; Run for
   everyone; the researched pitch explained with examples and queued on departure (handover,
   3.7 and 4.1).

---

## 2. The strategy in one paragraph

Leave Routes with named, qualified people who ran their own route live on the stand, hold a
pack with their numbers in their inbox, and have agreed a follow-up. Convert three to five of
them into year-1 launch customers by 7 November on a soft list price with a written, expiring
discount, host them on per-client access while the full product hardens, and use their feedback
and references to set list price and launch properly in the new year. The stand starts sales;
the 48-hour follow-up and the order-ready checklist close them.

---

## 3. Order-ready by 21 October (was 7 November; amended 20 Sep): the checklist

What has to be true for the first paying client to sign, be onboarded and be supported. None of
it is the full user model. Documents by 10 October (W5); dashboard tasks by 20 October (W2 and
John); anything not achievable by then is written into the known-issues list a client receives,
never left as a surprise. Avia is never the delay in signing someone up.

- Per-client Cloudflare Access policy (their email domain) and a unique password per client;
  the shared tester password retired for paying clients.
- Usage attribution per client in the R9 log, from the Access identity, not the Basic-auth
  username (master list 1.5).
- A two-page agreement: scope (users, routes per month, packs, review call), term and price,
  year-1 discount and its expiry, the economics disclaimer as already written in the tool, the
  licence position stated, no liability for decisions taken on outputs, data handling (Avia
  stores no client data; outputs only).
- Invoice template and payment terms; a support address that a named person reads daily; an
  onboarding call script (45 minutes: their first three routes, together).
- The licence letters from OAG and Sabre, or a documented record of the verbal confirmations
  (date, participants, what was said) held on Egnyte until the letters arrive.
- The known-issues list current, sent with onboarding: day-of-week, fare, the new aircraft
  types' economics, and anything Routes exposes. A client who is told is a beta client; one who
  finds out is a lost one.
- Monitoring and a restart procedure for the workstation and tunnel, with an alert to John's
  phone (handover, section 5).
- ADDED 21 Sep: PI insurance cover extended to The Aviation Observatory Limited (insurer's
  proposal awaited; a formality, but no client contract is signed without it) and a bank
  account in TAO Ltd's name for the first invoice. Owner: John. Pre-mortem 17.

---

## 4. Messaging, settled this week (John, Jol; a Fable chat drafts)

Four sentences everything else hangs off. Draft by 23 September, final by 25 September, then
the invitations go.

- The one-liner: run your route forecast on the stand, in seconds, built on 25 years of QSI
  practice and calibrated against real launches.
- Three sub-messages: the time-of-day optimisation (the USP); the researched pack in your
  inbox in 30 minutes; independent, senior, no house view to sell.
- The offer, in one sentence: expected list price (soft), launch customers this year at a
  stated year-1 discount, a stated number of places.
- The accuracy line, exactly as ruled: calibrated leads (89% within 20%, 82% within 10% on
  2,915 launches), blind evidence as portfolios only.

---

## 5. Integrated timeline

| Week | Commercial (John, Jol) | Technical (Fable chats) | Decisions due |
|---|---|---|---|
| 22-28 Sep (John in UAE) | Messaging drafted and settled; pricing numbers confirmed from the pricing chat; meeting targets chosen; invitations out 26-29 | Profile the three run types; preagg identity check; persistent cache design; request queue and email design put to John | Sender for emails; lead store (DuckDB vs CRM); website launch-or-landing by 1 Oct |
| 29 Sep-5 Oct (Italy) | Deck v1 reviewed; one-pager drafted; LinkedIn post 1; exhibitor listing updated | Preagg on if identical; cache built and tested across restart; request queue built; stand mode; laptop build proof by 1 Oct | Panel of 50 routes; attending-airport list for pre-warm |
| 6-12 Oct (Paris, deadlines) | Host manual v1; feedback card; post 2; website built (chosen path) | Progressive Optimise display; PDF render; imagery rights fix; pre-warm scripts run; **freeze 10 Oct** | Freeze confirmed |
| 13 Oct | **Boeing demo: the dress rehearsal**, timed, on hotel wifi, full flow including a queued pack | | What Boeing exposed |
| 14-18 Oct | Host trained 14-16; dry run 16; print; final posts | Fix only what Boeing exposed; final pre-warm; fallback kit | Go/no-go on Plan B kit |
| 19-20 Oct | Travel | Final pre-warm; freeze | |
| 21-23 Oct | **Routes**: stand, five meetings, daily lead review | Queue and workstation watched from Fairoaks | |
| 24 Oct-7 Nov | 48-hour follow-ups; one-pager to the qualified; order-ready checklist closed | Per-client access; attribution; monitoring | **Order-ready 7 Nov** |
| Nov-Dec | First launch customers onboarded; feedback into the master list; list price set | Day-of-week, fare, the engine queue resumes | Launch pricing announced |

---

## 6. Pre-mortem: what bites at the show, and the answer to each

Written as if it happened. Each has an owner and a mitigation already in the plans.

1. **The wired connection fails on the morning of day one.** Answer: 5G router primary, venue
   secondary, laptop build proven by 1 October (handover 4.1a, 4.5). If the laptop build is not
   proven, the stand runs the panel's pre-rendered packs and the queue goes out that night.
2. **A visitor's airport is not in the stores, or the run returns something silly.** Small
   airports with thin Sabre coverage, or a route beyond every type's range. Answer: the host's
   line ("the data is thin for that market; let me show you a neighbour and we will run yours
   properly and send it"); the request form captures it; the pack is checked by a person before
   it is sent for any route the engine flagged. Pre-warm by airport will surface most of these
   before the show; the attending-airport list is the test set.
3. **The forecast contradicts the visitor's own numbers.** Answer: this is the product working.
   The host says so: "a gap is informative; which side do you think is right, and why", captures
   the reason, and the follow-up is exactly that conversation. Nick's methodology note is the
   backing. Never defend a number on the stand; ask about the gap. ADDED 20 Sep (John): the
   visitor is comparing forecasts, not outcomes; the host opens the methodology page's bridge
   chart for the run just made and places the gap on a step (110k v 120k: where the 10k sits;
   150k v 50k: the case for ours, theirs captured for a proper look). Status: bridge exists in
   the build; walk-through owed by W4; controller checks the page on the workstation before
   the freeze.
4. **A competitor's client, or the competitor, tests the host.** Answer: commercial plan 10;
   the one honest sentence; no comparison; capture what they say.
5. **The host quotes a price, or a feature that is not in the build.** Answer: the manual's
   "what not to say" page and the training; the soft price and launch offer as a single
   rehearsed sentence; the known-issues list in the host's pocket.
6. **A pack fails to send, or sends with a wrong figure.** Answer: the queue view on the stand
   shows failures; every pack is the one-run definition; a person eyeballs any flagged route
   before send; the sender domain and SPF/DKIM are tested on 13 October, not 21 October.
7. **Cloudflare Access blocks the stand laptop or the host.** Answer: both added to the policy
   and tested on 13 October; the public landing page needs no Access.
8. **Lead consent and GDPR.** Answer: the consent tick on the form, the privacy line on the
   card, the lead store on Avia's own infrastructure, exported to Egnyte, nothing to a third
   party without a decision.
9. **The accuracy claim is challenged by someone who knows the field.** Answer: the ruling is
   the answer: calibrated leads, blind as portfolios, never a single-route blind figure; the
   host does not go beyond it and offers John.
10. **John is not on the stand when the buyer is.** Answer: the host's brief includes when John
    is on the stand; the request form books a follow-up slot; the deck and pack carry John's
    contact; the five pre-arranged meetings are John's.
11. **The workstation restarts and loses every pre-warmed route.** Answer: the persistent
    cache (handover 3.3) is the whole point; proven across a restart before freeze. Status
    21 Sep: CLOSED. Boards and catchment land paths persist on disk under LOCAL_CACHE, keyed
    on store and rule vintage; cold Run after a restart is 13-20s on three pairs, identical
    across two restarts, payloads identical to baseline. The register warm-up runs before
    20 Oct so the show's airports are on disk.
12. **The dress rehearsal does not happen.** Found 19 Sep: Boeing 13 Oct is an Atlas meeting
    with a short Meridian slot, not the Routes flow. Answer: two Meridian trials, 11-12 Oct
    (full stand flow after the freeze, timed, Plan A and Plan B, a pack sent and received on
    a hotspot) and 16 Oct with Suzanna; anything Boeing wants beyond its slot is post-Routes.
    Status: open until the 11-12 Oct trial is diaried with a named person at the workstation.
13. **The licence letter has not arrived.** Answer: the verbal confirmations are recorded with
    date and participants on Egnyte; the show proceeds; the letter gates the first contract.
14. **A visitor wants to sign on the stand.** (REWRITTEN 20 Sep.) Answer: take the details,
    thank them, and say the truth: the agreement and the invoice can be with them the same
    day, and onboarding is a 45-minute call in the week they choose. The host does not
    negotiate; John or Jol does, within 48 hours, with the one-pager already in the visitor's
    hand. Avia is never the delay.
15. **A visitor's airport is typed as a city name and the workstation cannot resolve it.**
    Found 19 Sep: three pinned routes errored in the back-test with "a GeoNames dump is
    required to resolve a city name"; the workstation has no GeoNames dump. Answer: confirm
    which entry paths on the dashboard need it (code entry should not); install the dump on
    the workstation or make the message a visible, honest refusal; test with a city-name
    entry on 13 October. Owner: W2. Status: open.
17. **A client wants to sign in the week after Routes and the PI cover or the bank account is
    not in TAO Ltd's name.** Found 21 Sep. Answer: the insurer's proposal is chased now and
    accepted before 21 Oct; the bank account is opened in October so the first invoice carries
    TAO Ltd's details; if either slips, the agreement is signed with a stated effective date on
    the cover and the invoice waits, and the client is told which, never surprised. Owner:
    John. Status: open.
16. **The live server has been running without the MCT master and nobody knew.** Found by
    W2, 19 Sep: a server started in a session without the Z: mapping resolves MCT_MASTER to a
    missing path and cascades every connection to 90 minutes in silence. Answer: 2cab1b2 makes
    the server say at startup how many rows it loaded, and the stand build refuses to start
    without it; the first restart after the workstation pulls it settles whether the testers'
    weeks ran on the master or the default. If they did not, the tester known-issues list
    gets a line and Nick is told. Status: open until that restart.
18. **A restart from a fresh window starts the server with no password.** Found 22 Sep: the
    password is read from $env:QSI_PASSWORD in the launching window, there is no password
    file on the workstation, and an empty value turns the shared password OFF in silence
    behind Cloudflare Access. Answer: the launcher refuses to start on an empty password and
    prints where the password came from (never the value); the runbook's restart procedure
    begins with the set line; rehearsed in the 11-12 Oct trial. Owner: W1 (launcher), W2
    (runbook). Status: open.
19. **The Optimise button takes four to eight minutes on the stand.** Found 22 Sep, measured
    on the workstation (d607d22, bt2, TIMING-22Sep-d607d22-full): the dashboard's Optimise
    runs the full sweep (all seasons, all carrier types, airline open, eight forecasts per
    cell) and took 460s on SJC-TPE, 429s on BRS-EWR, 334s on DUB-DFW, 257-260s on TIF-AUH; the narrowed
    default with the airline named is 36-57s, which is what the 22 Sep morning figures
    measured. No pair has been under four minutes on the flow a visitor drives. John's
    ruling: one button, nothing removed. Answer: W1 runs the sweep's independent forecasts
    in parallel processes in api_optimise (no demand logic touched, same payload diff), then
    re-measures; W2 shows best-so-far while it runs (progressive Optimise, must fit before
    10 Oct); until measured, "about a minute" is a Run claim only and the host says "a few
    minutes; let me show you the methodology page while it runs". Owner: W1, W2, W4, W6.
    Status 23 Sep: full sweep MEASURED at 96.9 / 117.3 / 91.0s on eight workers with every
    payload identical to the sequential run (after the departure-cache fix); the named
    single-airline case is still 55-76s and is next; W2's progressive display still needed.
    Status 24 Sep: 3x-7x sweep (John's ruling) full 56.6 / 78.7 / 60.7s, named 28.3 / 26.3 /
    16.2s on eight workers, MCT master loaded. "About a minute" is now measured for the
    named case and is within two minutes for the open sweep on every register pair.
20. **The server window is one keystroke from taking the stand down.** Found 24 Sep 16:59:
    the server exited cleanly mid-request with no crash record, which is the shape of a
    Ctrl+C or a closed console; its console vanished with it. Shipped (ac97cd3): the server
    runs in a PowerShell window that stays open after an exit and logs to app\logs. Rule for
    the stand (W2 runbook): the server window is minimised and never clicked; the host works
    only in the browser; if the dashboard says "Failed to fetch", the host runs the launcher
    from the runbook block, nothing else. Owner: W1 (done), W2 (runbook line).
    Status 23 Sep evening: the frequency split takes the full sweep to 66.5 / 109.3 / 64.7s
    and the single-airline case to 18-33s at eight workers, payloads identical; twelve
    workers killed a worker (memory) and the pool stayed broken until restart, so the
    rebuild fix (written, not yet live) is a condition of the freeze, and the worker count
    stays at eight until a worker's peak memory is measured. "About a minute" for Optimise
    is now within reach on the register pairs but is NOT yet released to W6: it needs the
    rebuild fix live and one full day without a pool fault.
21. **A number an air-service expert can feel is wrong.** Found 25 Sep on Bologna-New York:
    the blank-form Optimise returned United 7x B77W, 222,950 two-way, against Avia's own
    December 2025 assumption for AdB of a daily A321XLR; the calibrated model reads 226k
    two-way of demand at a narrowbody anchor (53% of the service area's existing New York
    traffic plus feed). John's ruling: the freeze is conditional on the numbers being
    sensible; where they are not, the engine changes before Routes, measured on the
    back-test first. Answer: the face-validity register (twelve routes, tool against
    analogue actuals) by 26 Sep; W10 diagnosis 29 Sep; fix decided 30 Sep; built and
    re-scored 1-6 Oct; accepted 7-8 Oct; video after acceptance. Owner: controller (W1
    build), W10 (diagnosis, re-score), W3 (re-run), John (the fix decision). Status: open.

22. **Stand internet, power and screen are not on any list.** The demo runs on the Surrey
    workstation through Cloudflare, so the stand needs a wired exhibitor internet line (Informa
    or Full Vision order, with a deadline), 4G as the second route, the Plan B laptop as the
    third; a TV or monitor for the video loop and the demo screen (hire or carry); power,
    extension leads, EU plugs. Owner: W9 (order and dates), W2 (the three routes tested on
    11-12 Oct). Status: open, 26 Sep.
23. **Email capture at a German show needs a privacy line.** The host types a visitor's email
    and the lead store keeps it: a one-line notice at the point of capture, a privacy page on
    the site, a retention date, and Informa condition 5.3 on delegate data all apply. Owner:
    W6 (site page), W2 (the line on the capture screen, retention in the store), W5 (the
    words). Status: open.
24. **The pack lands in a corporate spam folder.** A new domain sending attachments to airport
    and airline inboxes during the show: Postmark warm-up (ruled), SPF/DKIM/DMARC (item 20),
    AND every pack email carries a download link to the hosted pack (item 21 controls) so a
    stripped attachment still delivers; the holding email is short and plain. Owner: W2.
    Status: open.
25. **Pack builds and live demos compete for the same workstation.** Eight Optimise workers
    plus a queue of pack builds during the busiest hour: builds run at lower priority, one at
    a time, and never while a live Optimise is running; measured in the rehearsal batch and
    on 11-12 Oct with demos running. Owner: W2 (queue), controller (measurement). Status:
    open.
26. **Nothing printed for the hand.** Pens are ruled; a leaflet or card with the one-liner, the
    site and John's TAO address, and TAO business cards for John and Suzanna, are not. Print
    deadlines fall with the wall artwork. Owner: W6 (words), W9 (print and delivery to the
    Messe with the pens: address, deadline, who receives). Status: open.
27. **People on the stand.** Exhibitor badges for John, Suzanna and Stefan from Informa; a rota
    with breaks so two people are always on; who holds the laptop overnight (nothing left on
    the stand); equipment insurance; John's own travel and the 20 Oct setup day. Owner: W9,
    John. Status: open.
28. **After the show.** Who follows up which lead, by when, with what (the order form, the
    one-pager, a meeting); the lead store exported on the evening of 23 Oct; the marketing
    calendar's post-Routes posts. Owner: W6, W5, John. Status: open.
29. **"Can I have a trial?"** A visitor asks for access after the show. The position (a paid
    launch licence only; a rehearsed route pack as the taster; no free logins) is not written
    anywhere the host can read. Owner: W8 to state it in one line, W4 to carry it. Status:
    open.
30. **The register's routes are not the visitors' routes.** Twenty routes were tested; the
    stand will see hundreds. Before the freeze, W2's 40-60 route panel is run through the
    accepted engine and every answer read by John or Nick for face validity, so the known
    weak scenarios list (W4 3.3a, W5 known issues) is built from evidence not guesswork.
    Owner: controller (the run), John and Nick (the read). Status: open; after the fix.

---

## 7. Who owns what, in one line each

John: decisions, messaging sign-off, meetings, Boeing, host training, follow-ups, pricing.
Jol: copy (website, one-pager, posts), deck review, dry-run sceptic, feedback card.
Nick: methodology consistency across note, deck, pack; second eyes on panel outputs.
Jess: Atlas on the same stand, same freeze, same rehearsal.
Fable chats: everything in the prompt's two tracks; this document kept current.
Stand host: the demo, the form, the manual; nothing else.
