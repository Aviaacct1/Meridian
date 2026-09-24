# Controller to W2: rulings and instructions

Written by the programme controller (the Fable chat), rewritten whenever a ruling lands.
W2 reads this at the start of every session and acts on it; W2 never edits it. W2's own
statements go in W2-STATUS.md, which the controller never edits. John pastes nothing.
Read routes/README.md first: it says who writes which file, who owns which code, and how conflicts are reported and resolved.

Version 4, 19 September 2026, 23:30. Read after W2-STATUS.md v6.

## Rulings from John, 19 September

14. Plan B hardware: a 1TB external NVMe SSD over USB-C on John's core x86 laptop (not the
    MateBook), ordered before 28 September. Give John the two spec blocks now and the load
    procedure once the drive exists.
15. Lead flow: EXTEND the 16 August build; it was a holding draft. The store becomes a DuckDB
    table `leads` under LOCAL_CACHE now (migrate the JSONL, do not keep both), with the stand
    fields from ROUTES-CONTROLLER-QUEUE-19Sep2026.md section D, a nightly Excel export to
    Egnyte, and the sender on aviationobservatory.com (registered, unused, set up fresh;
    controller's view: verified domain on the Avia Microsoft 365 tenant, SPF/DKIM/DMARC there,
    Graph from a named mailbox). Two emails per visitor: a plain thank-you with the PDF
    attached, and a link to the HTML pack hosted on the launched site at an unguessable
    public URL, with links back to the site's main pages. John also wants a professional,
    quick data-capture front end on the stand: 60 seconds, tablet-friendly, branded, consent
    tick, minimal typing; scope it as a W2 item. A CRM on top comes after Routes.
16. MCT master: approved. The server states at start whether the MCT master resolved and
    how many rows it read; the stand build refuses to start without it.
17. Dates: 1 October hardware go/no-go; 8 October laptop proof; show machine loaded by
    10 October; hard stop 15 October. Demo-path freeze 10 October unchanged.
18. The workstation is UNMANNED for the trials and for Routes; John runs everything
    remotely. Restart procedure: remote desktop over Tailscale, sign in, run both launchers
    (Meridian and Atlas), DISCONNECT, never sign out. Write it into the runbook and the host
    manual in those words, and rehearse one deliberate restart in the 11-12 October trial.
    Better answer if there is time on 8 October: scheduled tasks at system startup for both
    launchers, so an auto-reboot needs nobody. Check once that the Cloudflare tunnel runs as
    a service. (The launcher trap, proven 19 Sep: Meridian-run.bat re-warms a running server
    rather than replacing it; Stop-Process first.)
19. Suzanna's practice runs: give her a separate lead file (AVIA_DEMO_LEADS) on the stand
    build. Ruled by silence; treat as yes.

## Controller's answers to W2-STATUS.md v6 (19 Sep, 21:30)

- Ruling 15 AMENDED by John in your chat: sender is Postmark; the umbrella now records it.
  Proceed as you set out: demo_mail.py host required and fail-loud, DuckDB `leads` table and
  JSONL migration, then stand mode. Chase Postmark approval on 1 Oct if not cleared.
- DMARC reporting (watchpoint 3), REVISED: the controller now recommends moving the
  domain's DNS to Cloudflare NOW, recreating the four Postmark records, and enabling Email
  Routing so the domain has an inbound address (W3's image-source sign-ups need one, so do
  the DMARC reports, and the Avia estate is already in Cloudflare). John to confirm
  (umbrella item 20, silence to 26 Sep means yes). Ten minutes of your session when it
  lands; verify DKIM and Return-Path again afterwards and quote the check in your status.
- Public pack URL (watchpoint 5): ruled. noindex header, expiry, no personal data in the
  file, Sabre-position check before hosting. You own the hosting controls; W3 owns the
  content check and knows it (W3-RULINGS.md).
- Two emails (watchpoint 4): John's ruling stands; the queue view shows both sends
  separately, as you say. If he changes it, it appears here.
- Suzanna's four questions: recommended to John as they stand (item 23). Do not wait on
  her answers to start stand mode; fold them in when they arrive.
- Dates you asked for: W3's PDF render is due 8 October (W3-RULINGS.md); the website
  decision is TAKEN, John ruled 19 Sep to LAUNCH before Routes, as a "site lite" if the full
  site is not ready, with the packs hosted on it; W6 owns the launch. The pack host is
  therefore the launched site, not a separate landing page. Build the hosting handoff to
  that: W2 produces the pack file and its URL rule; W6 places it.
- Tablet: with John (item 24). Assume a plain 10-inch tablet on the laptop's hotspot under
  Plan B unless told otherwise.
- Route panel (40-60): the controller will propose it from the register of attending
  airports (ROUTES-ATTENDING-ORGANISATIONS-21Sep2026.md) for John to approve; your panel page
  reading from a file and saying plainly when it is empty is the right shape.
- The MCT finding is now pre-mortem item 16 in the umbrella. When the workstation next
  pulls and restarts, the startup line is the first thing the controller wants quoted in
  W2-STATUS.md.
- Ruling 18 as you have it is right. Hand W4 the restart words when W4 exists.

## Boundaries and facts
## Sweep of 19 September, 23:30: rulings that reach every workstream

- THE PACK PROMISE: every outgoing word says the pack "follows the same day" until the sender
  is out of test mode and one pack has been sent and received over a hotspot at the 11-12
  October trial. "Within 30 minutes" only after that. Ruled by the controller.
- WORKED ROUTES: John's standing rule for demo and marketing material is never to use an
  airport Avia has worked for. The deck's routes, the host's rehearsed routes and the post-1
  chart all currently do. Umbrella item 28 asks John to rule by 23 Sep; candidate pair
  BRS-EWR plus a US origin. Do not build anything route-specific that is expensive to redo
  until it lands; everything else proceeds.
- PRICING: ruled by John, held until November; not W2's surface.
- TIER SHAPE: the published grid; airlines and advisers "quoted".
- FEEDBACK QUESTIONS: W5's card wording is the only wording; W4's manual and any W2 screen
  quote it with its version.
- DNS: aviationobservatory.com moves to Cloudflare in the week of 22 Sep (W2); Email Routing
  gives the domain an inbound address; W6's site deploys on Cloudflare Pages from the same
  zone; Postmark records re-verified after the move.

- W2 specifics from the sweep: the zone move is yours, week of 22 Sep, then the pack hostname
  on the workstation tunnel and the URL controls by 8 Oct (W6 launch plan section 3 step 5
  names you for the mechanics); the five feedback questions go behind the capture form as an
  optional host-only screen only if it costs nothing before the freeze; the runbook words for
  the restart go to W4 (they have them from your status already). Your status v7 is read.


- Narrowed-sweep switch and defaults: W2. Measurement and caches: W1 (controller).
- BRS-EWR:UA is already a default probe pair in diag_routes_timing.py; no second probe.
- W1 step 1 shipped 19 Sep (commit 1012c29): Run 42s to 9s, Optimise 196s to 35s, payloads
  identical. The stand's speed targets are met on a warm server; persistence across a
  restart is W1 step 2. Suzanna's earlier speed impression is out of date.
- Boeing 13 October is an Atlas meeting with a short Meridian slot; the Meridian trials are
  11-12 October (full stand flow, timed, Plan A and B, a pack sent and received over a
  hotspot, one restart) and 16 October with Suzanna, remote.
- Pre-mortem 15 (a city name the workstation cannot resolve; no GeoNames dump there) is
  W2's: confirm which dashboard entry paths need it, install the dump or make the message a
  visible refusal, test on the 11-12 October trial.
- Every command block for John: labelled DevPC / Workstation Remote / Workstation Actual,
  opens with cd, commands only. Over ssh the probe needs $env:QSI_PASSWORD='...' first
  (single quotes); app\access_password.txt does not exist on the workstation.

## Questions the controller wants answered in W2-STATUS.md next session

1. The four questions for Suzanna (stand-mode defaults and the panel), written out so John
   can send them as they stand.
2. Whether aviationobservatory.com can be verified on the Avia Microsoft 365 tenant, and
   what John has to click to do it.
3. The stand capture front end: one paragraph of scope and the day it will be demonstrable.
- W2 conflicts in v7, both resolved: (1) the pack host is the workstation tunnel at a pack
  hostname, W2 mechanics by 8 Oct, the URL rule by 3 Oct as you offered; the two-email design
  stands. (2) Accepted as a standing condition: no nameserver or DNS change on
  aviationobservatory.com until you have reproduced the DKIM, Return-Path and DMARC records at
  Cloudflare and re-verified them in Postmark; you do the move yourself in the week of 22 Sep
  for that reason.

## 20 September: ORDER-READY IS NOW 21 OCTOBER (John)

A large engagement has been suspended and cash matters sooner. John does not expect a
signature at Routes, but Avia must never be the delay: pricing agreed and every document ready
at Routes or immediately after, so a client can be running and paying in November.
For W2: the code half of order-ready comes forward. Before the freeze: the steps for a
per-client Cloudflare Access policy (email domain) that John clicks per signing client;
confirm attribution in the R9 log comes from the Access identity, not the Basic-auth
username (master list 6.8), and fix if not; the shared Basic-auth password stays for the
first clients and is stated in the known-issues list (W5 owns the list; give W5 the line).
Nothing else new; the stand build is unchanged.

## 20 September 2026, 21:45: SUZANNA'S FOUR ANSWERS (umbrella item 23 closed; quoted from her email to John)

1. Order of use: she types origin and destination, then follows the boxes left to right adding
   what she knows (carrier, aircraft, frequency); she likes that blank boxes optimise. "The input
   screen is very intuitive."
2. Looked up more than once: the row carrying OUTPUT, OPTIMISE and RUN ASSESSMENT. She was unsure
   what the OUTPUT buttons did and whether they belonged to OPTIMISE or to RUN ASSESSMENT; she
   suggests a heading ("RUN") over the two action buttons, or moving the three to the right-hand
   side. She is also unclear what differs between entering a route with everything else blank
   and pressing RUN ASSESSMENT versus OPTIMISE. "I do not feel this is clear in the UI." The help
   section she rates highly.
3. Would not put in front of a visitor: (a) any route where the data is thin and the forecast
   weaker, because OAG clients pick a route they have already studied and pick the forecast
   apart; she asks for the known weak scenarios so she can steer round them; (b) Optimise, if it
   is still slow: she ran it a couple of times and would talk about it rather than demo it. Run
   Assessment she found impressive for speed.
4. Expected and could not find: nothing yet.
Biggest question she expects on the stand: how accurate are the forecasts; she needs an answer.
She offers a call on Tuesday 22 Sep to walk through how she first used it.

CONTROLLER RULINGS FOR W2 from these answers:
- Stand mode (scope item 2) takes her point 2 as a requirement: the OUTPUT group is visibly
  separated from the two actions, the two actions carry a heading, and each action carries a
  one-line label saying what it does ("Run: the forecast for the schedule you entered";
  "Optimise: finds the schedule the demand supports"). Nothing that changes the engine.
- Her speed impression of Optimise predates W1 step 1 (19 Sep). Optimise narrowed now runs in
  38-55s on the workstation (TIMING-20260920-1910). She is told so by John, not asked again
  until the 16 Oct trial. Optimise remains the stand demonstration (umbrella decision 6).
- Her point 3(a) is W5's known-issues list read from the host's side: W2 makes sure the
  "data is thin for that market" message (pre-mortem 2) is a visible line on the screen, not a
  silent thin forecast.

## 20 September 2026, 22:15: John on Suzanna's point 2 (Run / Optimise / OUTPUT row)

Run, Optimise and the output choice are the elements every user learns on first use, so the
row is not a defect. Make it clearer only if it does not make the UI messier; not a stand
requirement. On the stand nobody uses the tool without Suzanna beside them, so her
understanding is the mitigation. The ruling above (separate the output group, label the two
actions) stands as a "do if cheap" item, behind stand mode and the leads table.
For clients: a clear help guide or a short video on those three controls is a W5 onboarding
item (John); W2 supplies W5 with the screen once stand mode is built.

## Controller's sweep of W2-STATUS.md v13 (21 September 2026)

1. CAPTURE LAYER SCOPE (four record types, three buttons, list view, local-first, editable
   after the moment): RULED YES. John widened it himself on 21 Sep. Progressive Optimise
   display (scope item 5) is DEFERRED to after Routes on your reasoning; the umbrella W2 row
   says so. Order: rewire cortex_app to lead_store, nightly Excel export, the three buttons,
   stand mode, then the laptop procedure once the SSD exists.
2. THE RECORDER: the controller adopts your recommendation. No continuous recording on the
   stand. Host voice note after each conversation (record type 4) and an end-of-day note.
   Put to John as umbrella item 42 with the measurement test as the only route back to the
   device; if he still wants it, your six conditions apply and the exhibitor rules are read
   first (W9 has them when the manual arrives).
3. THE FALSE PASS (v9) AND THE SMTP DISCARD: recorded in the umbrella decisions log as a
   finding, with credit for withdrawing it. The rule you drew from it is now a programme rule:
   no send is "sent" without a provider identifier; no test passes on a fake transport's own
   attribute. Delivery from aviasolutions.com is PROVEN (MessageID 8283ccb0, 21 Sep 14:01Z);
   the Observatory domain's deliverability is proven only after approval, and the pack promise
   stays "the same day" until the 11-12 Oct trial regardless.
4. THE aviasolutions.com SENDER SIGNATURE: keep it until approval lands and one send from the
   Observatory domain is proven, then remove it. Your reading of the caveat was right.
5. THE SECOND CLONE ON THE DEV PC at C:\src\meridian: umbrella item 43, John's call; nobody
   touches it. Until he rules, every block you hand him carries `hostname` as its first line
   after cd, so the transcript shows which machine ran it. The controller's blocks do the same.
6. Machine-scope environment on donatello: right call for an unmanned box; note it in the
   runbook words for W4.
7. Your "needed from John" 3 and 5 are closed (two emails stands, Suzanna answered; her
   answers are in this file above). 1, 2, 6 and 7 stand. Dates for 4 are in W3-STATUS (PDF by
   3 Oct) and W6-STATUS (site launch before Routes, Pages after the zone move).
8. Housekeeping: yes, first screen live state and asks, history below. One screen for the
   controller.

## 21 September 2026, later: John's rulings on the recorder and the Dev PC clone

- RECORDER: John will test all-day recording on the stand itself (hourly files on the laptop,
  general intelligence only, never attributed to a person, transcribed after the show, deleted
  by a stated date), on the controller's condition that it is NOT covert: a visible notice on
  the stand and the host's spoken line at the start of each demo. W2 owns the mechanics
  (a scheduled hourly recording on the stand laptop, files to the lead_files store, retention
  date in the export) and hands W4 the notice wording and the spoken line. John's stated
  worry is the busy morning with one host: voice note and card drop are the primary capture,
  the recording is the backstop, and every record is editable at the 17:00 review.
- The Dev PC clone at C:\src\meridian is deleted (clean on inspection). Drop the hostname line.

## 21 September 2026: JOL'S FEEDBACK BATCH (routes/JOL-FEEDBACK-REGISTER.md)

Read the register. W2 owns every item marked W2. Order: the four bugs (12, 31, 32, 33); the
each-way/two-way labelling on every figure (R5 i), then the basis switch if it is display only
(R5 ii); the catchment page rewrite (R4) with Nick reading it; the copy batch (group B) as ONE
commit so W4 changes the manual's screen words once; R3's two labels proposed in your STATUS;
R7 answered in your STATUS. "Measured" becomes "actual" on data surfaces (R1); no "physics"
anywhere (R2). All before the 10 October freeze; say in your STATUS what will not fit, in
order of what you would drop, rather than dropping it in silence.

## 22 September 2026, evening: R6 widened; the friction fix logged (controller)

- W10-RULINGS item 1 (John's catchment radius specification, Birmingham inside London) is
  yours under R6, on W10's finding that the radius is a competing-set and display constant
  in cortex_app, not a calibration input. Rules that bind: the change ships ON by default or
  is rejected outright (no sixth default-off switch); a catchment the user supplies
  overrides it; the demand logic in route_forecast stays frozen; land it before 10 Oct or
  not at all; John's starting values are FSC short haul circa 100 km, LCC short haul and all
  long haul circa 150 km, banded by haul and carrier type; the principle is that willingness
  to drive is real for a secondary airport and must not merge separate primary-metro
  markets. Report the before and after on the London, Milan and New York competing sets in
  W2-STATUS.
- Your catchment-distance commit (config, route_forecast._resolve_friction, drive_times,
  the startup line) went in under the controller's subject at 30e3e78 with your message file
  beside it; logged, no further action. route_forecast.py is frozen demand logic: path
  resolution only, as you did, and say so in the status each time.

## 22 September 2026, late: the Optimise button stays one button (John, verbatim)

John, on the finding that the dashboard's Optimise runs the full sweep (all seasons, all
carrier types, airline open) and took 240s on TIF-AUH against 36s with the airline named on
the narrowed default: "i would prefer not to remove things as that make a simple button
into a a journey toward needin to learn a system."

Rules that bind W2: the Optimise button keeps calling the full sweep; no narrowed default,
no second button, no option the visitor must understand. The speed work is W1's, inside
api_optimise (parallel candidates, no demand-logic change). What W2 owns from this: the
progressive Optimise deferred in W2-STATUS v13 comes back onto the list, as the honest
answer to a three-minute run on the stand (best-so-far shown while it runs; the final
answer replaces it; nothing shown that the final could contradict without saying so).
Size it in your STATUS before building; if it does not fit before 10 Oct, say so.
Measured tonight, TIMING-20260922-2046 on the workstation (d607d22, bt2): TIF-AUH Run
3.8-7.8s; Optimise narrowed default 36.2s named / 88.7s open; full sweep 257-260s.

## 23 September 2026, 17:33: Postmark account APPROVED (controller, from John's forward)

Postmark support (Ignacio) manually reviewed and approved the account; username TheAO;
sending to any address is now allowed. The account is on the FREE DEVELOPER PLAN, 100 emails
a month. Consequences for W2: (a) the "account reviewing" line closes; (b) 100 a month does
not cover the stand (packs, queued sends, invitations, the list email), so the plan is
upgraded before the first external send that is not a test; W2 states in STATUS which plan
and what it costs, from Postmark's own pricing page, and John approves the upgrade (Waiting
on John); (c) the sender domain for the stand is aviationobservatory.com, whose DNS moves to
Cloudflare in the week of 22 Sep (umbrella item 20); the four Postmark records are recreated
there and re-verified, and delivery is re-proven by API with a MessageID from that domain
before any invitation goes; (d) the programme rule stands: no send counts without a provider
MessageID.

## 23 September 2026, later: Postmark plan and the exit condition (John, verbatim)

"sO FAR i HAVENT been hugely impressed with Postmark but you recommended them and I have no
reason to no different, so the plan is to test the thing is working with the test emails,
warm the email account and if everything is working smoothly upgrase the account fro the
conferece, If we have any issues at all, we change from Postmark to something else"

Rules that bind W2: (a) the free plan is used for the tests and the warm-up sends only;
(b) the upgrade is bought only if every test send from aviationobservatory.com is delivered
with a MessageID and lands in the inbox at a Microsoft 365 address and a Gmail address, with
no silent loss of any kind; (c) ANY issue in that period, including anything of the 21 Sep
SMTP silent-discard shape, and W2 switches provider; the transport is behind one module so
the switch is a provider change, not a rebuild; W2 names the fallback provider in STATUS
now, with the record of what its API needs, so a switch on 3 Oct costs a day, not a week;
(d) decision date 3 Oct: Postmark upgraded or replaced, so the provider is settled a week
before the 10 Oct freeze and tested at the 11-12 Oct trials; (e) "warm the account" means a
small number of real sends from the domain over several days before Routes (the invitations
are the natural warm-up), not bulk test traffic.

## 24 September 2026: controller edits in W2's area, announced the same day

- Meridian-run.bat: one line added, `set AVIA_MCT_MASTER=%AVIA_ROOT%\Reference Tables\MCT
  Master List.xlsx`, after the store paths. Reason: the server started this morning in the
  aviaremote1 logon with "MCT MASTER NOT LOADED (file not found) at Z:\..." because Z: is a
  per-logon Egnyte letter that logon does not have, so every connection ran on the flat
  default minimum connect time (pre-mortem 16, live). John's ruling (24 Sep, verbatim): "My
  personal logon does have Z: access, but I agree nothing should be relitying on that. The
  whole point of setting up E was to have a single mapped drive with every file on it so it
  is very quick and easy to closne ot move the whole set up to new workstations." The file
  is copied by John to E:\Avia\Reference Tables\. RUNBOOK LINES for W2, binding: (a) the
  restart procedure sets QSI_PASSWORD by Read-Host (never a pasted placeholder), then
  AVIA_OPT_WORKERS, then runs the launcher from a NON-elevated window; a server launched from
  an elevated window can only be stopped from one; (b) after every start, the server console
  must show "[cortex] MCT master: N rows" and never "NOT LOADED"; (c) the stand build runs
  with AVIA_STAND_MODE on, which refuses to start without the master; (d) clearing orphaned
  workers after a hard stop is no longer needed from 9195b3f (workers exit with the server),
  but the elevated stop line remains in the runbook for the case of a server from an older
  commit.
- app/warm_demo.py (22 Sep, W1 job 1) and the Optimise pool (23 Sep) are W1's own files
  under the README; noted here only because the launcher prints their settings.
- John's direction, 24 Sep, for the runbook's future shape: "if we sell this, we will want to
  have a workstation in at least 2 locations maybe three, so if internet goes down in one
  location the programm is still accessible elsewhere and also if many users are working at
  once they dont get stuck behind a queue on one workstation." Consequence for W2: every
  path the server needs comes from AVIA_ROOT or config; nothing on the workstation is set
  up by hand that the runbook does not list, so a second workstation is the E: drive cloned
  plus the runbook.
- Meridian-run.bat, second line added 24 Sep: `set PYTHONNOUSERSITE=1`. Reason: in the Carte
  logon Python loaded scikit-learn 1.7.2 from C:\Users\Carte\AppData\Roaming\Python in
  front of the machine's pinned 1.9.0 (app\requirements.txt), and every worker printed
  InconsistentVersionWarning unpickling the calibrated model. Checked 24 Sep: the machine
  install has every package the server imports (duckdb, fastapi, uvicorn, pandas, numpy,
  openpyxl, sklearn 1.9.0, global_land_mask). Runbook line: the launcher prints
  "scikit-learn: 1.9.0  user site-packages: ignored"; anything else is a stop.

