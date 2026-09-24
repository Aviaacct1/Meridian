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
Tuesday 22 September 2026, late evening (John in Doha): controller chat 3 (Fable). W1 job 1
is DONE and CONFIRMED BY PASTE: d607d22 (launcher default bt2) is on the DevPC, pushed, pulled
on the workstation and the server restarted; the launcher printed "forecast engine: BT2
(calibrated model; claimset reproduced 22 Sep 2026)". Found on the way: the workstation had
been on 66455af (21 Sep) throughout 22 Sep, so nothing committed on 22 Sep had run there until
tonight; the pull was blocked by three generated files under app/ that the repo tracks (now
stashed on the workstation, untracking is W1 job 7); and one restart tonight ran on QSI for
circa fifteen minutes before the fix reached the workstation. The payload diff of the new
server against this morning's bt2 baseline is still owed, because the pull also brought W2's
30e3e78 changes to config.py, cortex_app.py, drive_times.py and route_forecast.py, recorded
as no behaviour change but not yet measured on the workstation. W10's radius claim verified by
grep; John has not yet confirmed the re-ruling. Order-ready is 21 Oct. Files:
`routes\Wn-STATUS.md` (chat writes), `routes\Wn-RULINGS.md` (controller writes),
`routes\README.md`.

| WS | State | Where it stands | Next action | Owner | Date |
|---|---|---|---|---|---|
| W1 Speed and caches | Job 0 SHIPPED 23 Sep (6065e18 on the workstation, 8 workers); pool-rebuild fix WRITTEN, not yet pushed | Split sweep (9 cells, 63 tasks): full sweep 66.5 / 109.3 / 64.7s, named 30.3 / 32.6 / 18.4s at 8 workers, every payload IDENTICAL to the fixed sequential control (OPT-23Sep-fix-w1 v split-w1 v split-w8 all PASS); sequential now 370 / 410 / 323s; 12 workers FAILED (a worker killed for memory, pool left broken); default stays 8 | MUST FIX (John 24 Sep): curfew-bound headline follows the permitted departure; kill test to finish; worker peak-memory reading during a sweep; launcher refuses empty password; payload `engine` label; disclaimer; untrack app/ generated files; market-brief cost; warm_boards | Controller / John | Rebuild fix live 24 Sep; rest by 3 Oct |
| W2 Stand flow | In progress (v14, 22 Sep) | Delivery proven by Postmark API (MessageID 8283ccb0); lead_store built (ef6de65), app not yet rewired; friction raster never resolved on the workstation, catchment ran on straight-line distance silently, fixed through config, no behaviour change (30e3e78); item 1 radius now W2's under R6 | Sweep: R6 radius plan and lead_store rewiring; data-store freeze line and stale-RDP runbook line owed to W2-RULINGS by the controller | W2 chat / John | Capture demonstrable 2 Oct; laptop proof 8 Oct; radius before 10 Oct or not at all |
| W3 Presentation | In progress (v2, 21 Sep) | Slides 1-6, 9-10 built (3af5158); PDF render proven; Commons probe unrun (item 33); 92/86 coming off the methodology and track record pages | Video script 23 Sep; probe by 26 Sep; video record 26-30 Sep; sweep after the methodology page change | W3 chat / John | Five items to Jol and Nick 3 Oct |
| W4 Host | v2 DONE (21 Sep) | STAND-HOST-MANUAL.md v2, 23 slots; three bridge labels flagged for W3 | v3 after 8 Oct screenshots and W5's known-issues list; John's item 34 | W4 chat / John | v3 mid-Oct |
| W5 Order-ready documents | v0.3 DONE (21 Sep) | Every document exists in draft; seven slots John's or the insurer's; PI cover and TAO bank account bind 21 Oct | Solicitor slot wk 6 Oct; known-issues frozen 10 Oct; disclaimer wording to W1 for item 3 | W5 chat / John | 6 and 10 Oct |
| W6 Messaging, marketing, website, meetings | In progress (v7, 21 Sep) | Sentences in the Observatory voice (variants v3); invitations drafted; post 1 and list email await approval; site still says three seats / 100 presentations | John: five contact names, 2.3 A or B, post 1 and list email by 25 Sep; invitations 26-29 Sep | W6 chat / John | 25-29 Sep |
| W8 Pricing | DONE 20 Sep; v1.1 owed | PRICING-DECISION-2026.md v1.0 FINAL; v1.1 for the TAO Ltd entity line not yet issued | Controller issues v1.1 (entity line only) | Controller | 26 Sep |
| W9 Stand, contract, logistics | NOT OPENED | Contract unsigned pending Charlotte Sullivan's revised form; F124; graphics deadline 3 Oct; pens (item 54) | John opens W9 when the form is back; graphics decision by 30 Sep or logo only | John | Graphics 3 Oct |
| W10 Final calibration test | OPEN, STATUS v1 (22 Sep) | Item 1 re-ruled to W2 (John to confirm); items 2 and 3 proceed: 22 Sep baseline rerun, then 92/86 on 6,524 reproduced or replaced; interim on every surface 89/82 on 2,915 | Controller verifies the radius claim by grep; sweep on the baseline paste; W10 says by 29 Sep whether 3 Oct holds | W10 chat / John | Record v1 by 3 Oct; John rules item 55 |
| W7 Rehearsal and freeze | Diaried | Trials 11-12 Oct remote, 16 Oct with Suzanna; 13 Oct is an Atlas meeting | Nothing until October; controller confirms a named person at the workstation for 11-12 Oct | Controller / John | Freeze 10 Oct |

Still open from earlier reads: (a) W3-STATUS.md v2 is behind the slide build at 3af5158;
(b) W2-RULINGS owes the data-store freeze line (no OAG or Sabre refresh 10 Oct to after
Routes) and the stale-RDP runbook line; (c) Atlas has no row in this table (same stand, same
freeze; Jess); (d) the first Friday note is due 26 Sep and is not written.
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
  not yet run. Cosmetic for W1: the panel prefixes "RuntimeError:", strip the class name.
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
26. **Carrier for slide 8, Bologna-New York.** No default; W3 will not pick an airline.
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
    stand; W3 does the artwork. Silence to 30 Sep: logo only.
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
55. **Which accuracy pair the product publishes.** Interim, on every surface: 89/82 on 2,915.
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
    Status 23 Sep evening: the frequency split takes the full sweep to 66.5 / 109.3 / 64.7s
    and the single-airline case to 18-33s at eight workers, payloads identical; twelve
    workers killed a worker (memory) and the pool stayed broken until restart, so the
    rebuild fix (written, not yet live) is a condition of the freeze, and the worker count
    stays at eight until a worker's peak memory is measured. "About a minute" for Optimise
    is now within reach on the register pairs but is NOT yet released to W6: it needs the
    rebuild fix live and one full day without a pool fault.
---

## 7. Who owns what, in one line each

John: decisions, messaging sign-off, meetings, Boeing, host training, follow-ups, pricing.
Jol: copy (website, one-pager, posts), deck review, dry-run sceptic, feedback card.
Nick: methodology consistency across note, deck, pack; second eyes on panel outputs.
Jess: Atlas on the same stand, same freeze, same rehearsal.
Fable chats: everything in the prompt's two tracks; this document kept current.
Stand host: the demo, the form, the manual; nothing else.
