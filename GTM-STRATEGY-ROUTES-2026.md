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

Rewritten every session by the programme controller; John reads this on a phone. Session 1,
19 September 2026, 16:00. Clone: DevPC `C:\AviaDev`, HEAD `11a4c3f` (aircraft-econ code committed and pushed 19 Sep,
confirmed by John's paste).

| WS | State | Evidence | Next action | Owner | Date |
|---|---|---|---|---|---|
| W1 Speed and caches | Step 1 SHIPPED 19 Sep, acceptance MET | Commit 1012c29 live on the workstation: Run 35.4 to 9.8s (SJC-TPE), 42.5 to 9.0s (BRS-EWR, cold); Optimise 161 to 65s and 196 to 35s; payloads identical (probe diff PASS). TIMING-20260919-1907 (before) and -1937 (after) on the workstation | Step 2: persistence across a restart (pre-mortem 11) and the pre-warm script over the registered airports; then preagg wiring | Controller | 26 Sep |
| W2 Stand flow | In progress (routes\W2-STATUS.md v6, 19 Sep 20:50) | Commit 2cab1b2: MCT master reports at startup, stand build refuses without it (14 checks); sender set up on Postmark, aviationobservatory.com DKIM and return-path verified, account in test mode pending Postmark approval; capture front end scoped, demonstrable 2 Oct | Stand mode build; DuckDB leads table and JSONL migration; John's items 20-24 | W2 chat / John | 2 Oct front end; 8 Oct laptop proof |
| W3 Presentation | Not started | Old 2 July pptx only | Deck v1 after messaging settles | Controller, Jol, Nick | 3 Oct |
| W4 Host | Not started | Host's name and contact in no document | Manual v1; get host details from John | Controller / John | 10 Oct |
| W5 Leads, feedback, order-ready | Blocked on John | Lead store and email sender undecided | Decisions batch (step C) | John | 25 Sep |
| W6 Messaging, marketing, website, meetings | In progress | Four sentences drafted this session (step C) | John and Jol settle; invitations out | John, Jol | Final 25 Sep; invites 26-29 Sep |
| W7 Rehearsal and freeze | Replanned | Boeing 13 Oct is an ATLAS meeting with 15 minutes of Meridian, not the Meridian dress rehearsal (John to W2, 19 Sep); the umbrella was wrong | Two Meridian trials: 11-12 Oct full stand flow timed, Plan A and B, a pack sent and received; 16 Oct with Suzanna | Controller / John | Freeze 10 Oct unchanged |

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
     Stand F174. Lands Tuesday 20 Oct afternoon; works the stand Wed-Fri 9-5. Stefan Parry
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
6. **Launch offer numbers**: year-1 discount, number of places, expiry date, against the
   £15-25k grid. Silence to 3 Oct: the host says "on request, limited places" only.
7. **Tier shape**: the commercial plan has Airport / Airline / Adviser tiers; the published
   grid prices by airport size only and quotes consultancies on portfolio. Which shape goes
   in the offer sentence and the one-pager? Silence to 3 Oct: the published grid, airlines
   and advisers "quoted".
8. **Pack email pattern**: controller view is two emails, not three: a plain thank-you with
   the PDF attached, and the HTML pack hosted at an unguessable public URL on the launched
   site (no login) linked from that email, because HTML attachments are stripped far more
   often than PDFs and a hosted page is also what a visitor forwards. Three emails triples
   the spam-filter exposure. Your call. Silence to 26 Sep: two emails as described.
9. **Sending domain**: aviationobservatory.com. Is it on the Avia Microsoft 365 tenant, or
   elsewhere? Decides Graph versus a transactional sender, and who sets SPF/DKIM/DMARC.
   Silence to 26 Sep: assumed on the tenant; W2 checks and reports.
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
20. **DMARC reporting route** (W2 watchpoint 3): Postmark's DMARC Digests now (no DNS move
    before the laptop proof; nothing to recreate), Cloudflare DNS and Email Routing after
    Routes. Controller's view; confirm. Silence to 26 Sep: Postmark digests.
21. **Public pack URL controls** (W2 watchpoint 5): noindex header, an expiry, no personal
    data in the file, and every pack checked against the Sabre position (attribution
    constant, fares as bands, no single-route blind figure) before it is hosted. Controller
    rules yes to all four; W2 the hosting controls, W3 the content check. No answer needed
    unless you disagree.
22. **One email or two** (W2 still recommends one). Your 19 Sep ruling of two stands unless
    you say otherwise; the queue view then shows both sends separately.
23. **Send Suzanna the four questions** in W2-STATUS.md now (controller recommends yes, as
    they stand). Silence to 23 Sep: I take it as yes and W2 proceeds on her answers.
24. **Which tablet for the capture front end**, and whether it is yours or bought. Under
    Plan B it reaches the form on the laptop's own hotspot; W2 confirms.
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
3. **Two milestones, not one**: DEMO-READY 21 October (the stand); ORDER-READY 7 November (an
   airport with budget to use this calendar year can sign and be onboarded). Order-ready is a
   checklist (section 3), not a rebuild, and it is where the Routes follow-ups land.
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

## 3. Order-ready by 7 November: the checklist

What has to be true for the first paying client to sign, be onboarded and be supported. None of
it is the full user model; all of it is achievable in the three weeks after Routes.

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
   backing. Never defend a number on the stand; ask about the gap.
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
    19 Sep: OPEN. Step 1 holds boards, MCT and the airport table in process memory only; a
    restart loses them and the first Run on each airport pays circa 30s again. Step 2 is
    the on-disk copy of exactly those parsed boards under LOCAL_CACHE, keyed on the OAG
    store's vintage, plus a warm-up over the registered airports at launch.
12. **The dress rehearsal does not happen.** Found 19 Sep: Boeing 13 Oct is an Atlas meeting
    with a short Meridian slot, not the Routes flow. Answer: two Meridian trials, 11-12 Oct
    (full stand flow after the freeze, timed, Plan A and Plan B, a pack sent and received on
    a hotspot) and 16 Oct with Suzanna; anything Boeing wants beyond its slot is post-Routes.
    Status: open until the 11-12 Oct trial is diaried with a named person at the workstation.
13. **The licence letter has not arrived.** Answer: the verbal confirmations are recorded with
    date and participants on Egnyte; the show proceeds; the letter gates the first contract.
14. **A visitor wants to sign on the stand.** Answer: take the details, thank them, and tell
    them the truth: onboarding opens 7 November and they are first in the queue. A signature
    taken before order-ready is a support problem, not a sale.

15. **A visitor's airport is typed as a city name and the workstation cannot resolve it.**
    Found 19 Sep: three pinned routes errored in the back-test with "a GeoNames dump is
    required to resolve a city name"; the workstation has no GeoNames dump. Answer: confirm
    which entry paths on the dashboard need it (code entry should not); install the dump on
    the workstation or make the message a visible, honest refusal; test with a city-name
    entry on 13 October. Owner: W2. Status: open.
16. **The live server has been running without the MCT master and nobody knew.** Found by
    W2, 19 Sep: a server started in a session without the Z: mapping resolves MCT_MASTER to a
    missing path and cascades every connection to 90 minutes in silence. Answer: 2cab1b2 makes
    the server say at startup how many rows it loaded, and the stand build refuses to start
    without it; the first restart after the workstation pulls it settles whether the testers'
    weeks ran on the master or the default. If they did not, the tester known-issues list
    gets a line and Nick is told. Status: open until that restart.
---

## 7. Who owns what, in one line each

John: decisions, messaging sign-off, meetings, Boeing, host training, follow-ups, pricing.
Jol: copy (website, one-pager, posts), deck review, dry-run sceptic, feedback card.
Nick: methodology consistency across note, deck, pack; second eyes on panel outputs.
Jess: Atlas on the same stand, same freeze, same rehearsal.
Fable chats: everything in the prompt's two tracks; this document kept current.
Stand host: the demo, the form, the manual; nothing else.
