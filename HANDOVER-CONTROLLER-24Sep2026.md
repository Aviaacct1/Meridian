# HANDOVER: programme controller, 24 September 2026, 20:00 BST

For controller chat 4 (Fable), opening 25 September. This file consolidates
HANDOVER-CONTROLLER-22Sep2026.md and HANDOVER-CONTROLLER-23Sep2026.md; read those two only
where this file points at them. Everything here is true at the last commit John ran from
chat 3 (the block at the end of this file, subject "Controller 24 Sep close: ..."). The
workstation is on main at that commit or one behind it (the records commit touches no code).

## 1. Where the programme stands, one screen

World Routes, Frankfurt, 21-23 Oct 2026, stand F124, The Aviation Observatory Limited.
Order-ready 21 Oct. Demo-path freeze 10 Oct. No data-store refresh 10 Oct to after Routes.
John is in the UAE until circa 2 Oct, reading on a phone and an HP Envy work laptop whose
Enter and Backspace keys fail intermittently in consoles (an on-screen keyboard works; an
external keyboard, wired or wireless, bypasses it; he is buying one). Company IT blocks an
elevated PowerShell on that laptop. RustDesk is the route to the workstation and the DevPC;
ssh to the workstation refuses the password; the DevPC has no sshd (needs an elevated
window on the DevPC via RustDesk to install).

W1 is the only workstream that moved 22-24 Sep. It shipped everything it owed and passed
acceptance (section 2). W2, W3, W4, W5, W6, W8, W10 have not been swept since 22 Sep and
each has work due this week (section 5). W9 opens 25 Sep because Informa named the stand
contractor on 24 Sep (section 6). Postmark is approved (section 7). The week's decisions
(step C) have still not been put to John in one message (section 8). The first Friday note
is due 26 Sep and is not written.

## 2. W1: what shipped 22-24 Sep, and the acceptance

Commits on origin, in order: d607d22 launcher default bt2; 345e2e3 parallel Optimise pool;
4e5dd3c freq in the departure-cache key (John's ruling 23 Sep); 6065e18 two-stage sweep
split; 657dc49 and 6969833 pool rebuild after a dead worker; 9195b3f workers die with the
server; 5e0b597 MCT master from the product drive; 19d94df PYTHONNOUSERSITE; 68a23d4
records; then 24 Sep: curfew must-fix and selection rule; sweep table in the payload; GET
/api/optimise restored (decorator had landed on _cell_kw since 6065e18, 422 on every direct
GET; the browser and the harness use /api/optimise/start so nobody saw it); blank sweep
3x-7x; seasonal note in-band only; restriction applied after the connectivity re-split;
ac97cd3 server console kept open and teed to app\logs; then the carried-ranking commit
(COMMIT-MSG-24Sep2026-w1-select-on-carried.txt) with the day's records.

What the code now does, in the words a chat needs:
- Optimise runs cells (candidate airline x carrier type x season) in a process pool of
  AVIA_OPT_WORKERS (default 8), each worker DuckDB pinned to 3GB / 2 threads; stage 1 sizes
  each cell at 7x, stage 2 runs each cell at each frequency; rows come back in order. A dead
  worker mid-job reports "Optimise failed: a worker process was terminated ...; the pool has
  been rebuilt, run Optimise again"; a dead idle worker is rebuilt at the next submit.
  Workers exit when the server dies. Kill test 24 Sep PASS on both cases.
- Frequency blank: the sweep is 3x, 4x, 5x, 6x, 7x. A fixed frequency of any value runs as
  before. (John, verbatim in the umbrella: "a new long haul route on a new service will
  almost only ever launch a 3x 4x 5x or 7x and providing numbers beyond that just makes the
  tool look foolish".)
- Selection: season blank means the headline is the ANNUAL row carrying the most passengers
  (carried = demand capped at seats x freq x weeks x plan LF) within the presentable band
  VIABLE_LF 0.65 to PRESENT_LF_CAP 0.85 (the cap is a WORKING ASSUMPTION; John has not set
  it); a seasonal row that plans better INSIDE the band earns one sentence ("select Winter
  and Optimise again"); an explicit season runs the same rule over its own rows with no
  sentence; no row in band falls to most carried above the floor with a selection_note; no
  annual row viable but a seasonal one falls to that seasonal row with a note; nothing
  viable keeps the not_viable report. The payload's optimised block carries objective,
  present_lf_cap, selection_note, seasonal_note and the whole sweep table (airline,
  aircraft, freq, season, lf, demand, carried, seats, chosen).
- Curfew (John's must-fix 24 Sep): when the permitted departure is not the unrestricted
  optimum, calibrated_forecast passes score / unrestricted_score from the departure
  optimiser as feed_cfg restriction_factor; route_forecast applies it AFTER the connectivity
  re-split, to the connecting leg only (local unchanged, spill refilled in the legs'
  proportion), and the feed aggregates, PTEW maps and detail rows follow. schedule.optimised
  gains restriction_factor and unrestricted_connecting_carried only when a restriction
  bound; the dashboard curfew line says the headline carries the restricted departure and
  what the route would carry unrestricted; the chart's unrestricted peak shows it by
  construction. Unrestricted runs are byte-for-byte unchanged.
- The server runs in a PowerShell window (-NoExit) and tees every line to
  app\logs\server-<stamp>.log; the launcher prints "server log: ...". app/logs/ is
  gitignored. A RuntimeError written for the panel is shown without its class name.

Acceptance, all on the workstation, eight workers, MCT master loaded, sklearn 1.9.0:
- Blank-form SJC-TPE Optimise three times: Starlux 7x A359 annual, 194,922 two-way, every
  time (the sweep chose 91,639 each way at 82.3%; the returned run reports 87.5% with the
  induced floor on; the basis line states both).
- Winter selected: Starlux 7x A359 winter-only, 81,564 two-way.
- Curfew SJC-TPE, CI, A359, 7x, origin 21:00-06:00: departure 20:59, local 77,414
  unchanged, connecting 94,802 to 34,868, headline 172,216 to 112,282; the factor 0.368 is
  the optimiser's own score ratio (16,415 / 44,630): a 20:59 departure lands Taipei at
  02:44 and misses the morning bank. "63% lost to the restriction" on the curfew line is
  correct.
- Three-pair probe (SJC-TPE:CI, BRS-EWR:UA, DUB-DFW:EI): run_ payloads IDENTICAL against
  the 23 Sep baseline (SJC-TPE) and against a same-day control on 68a23d4 (BRS-EWR,
  DUB-DFW; E:\Avia\probe\CTRL-24Sep-68a23d4). The two-field BRS-EWR difference against the
  23 Sep folder was the MCT master, which the 23 Sep baseline predates.
- BASELINE FROM NOW: E:\Avia\probe\OPT-24Sep-final-w8. Timing on it: full sweep 52.5 /
  86.9 / 52.6s, named 24.3 / 22.3 / 16.2s, Run cold 12.5-16.9s, warm 7.9-9.6s. "About a
  minute" is measured for the named Optimise; the open sweep is under ninety seconds on
  every register pair. Timing tables in C:\src\meridian\TIMING-20260924-*.md.

Findings on the way, recorded in the umbrella decisions log:
- The connectivity re-split (split floor, on since 16 Aug) reports local and connecting as
  shares of the carried total (45/55 on SJC-TPE). W10 question.
- Demand rises with frequency (SJC-TPE Starlux 7x 91,639, 10x 124,131, 14x 163,061 each
  way) and dips 6x to 7x on DUB-DFW (139,237 to 138,747). W10 questions.
- The tool's CI 7x A359 SJC-TPE figure (172,216 two-way) is well above the circa 120k
  presented to the Taipei airlines; W3 re-runs SJC-TPE and BLQ-JFK on this server and
  compares (W3-RULINGS 23 Sep already marks those figures provisional).
- Market background shows "Direct service today: None" for SJC-TPE (two nonstop operators
  in the OAG week): W2 check, now on the demo path because of the existing-market line.
- Server died 24 Sep 16:59 mid-request on a DUB-DFW cold Run: clean exit, no Application or
  System event, console gone. Suspected Ctrl+C or window close while the on-screen keyboard
  was up; unproven. Pre-mortem 20; W2 runbook lines written in W2-RULINGS.

## 3. W1 queue, in order

1. Confirm the carried commit is on the workstation (the close block below pulls it) and
   that DUB-DFW named picks 7x on the next probe (it did on OPT-24Sep-final-w8).
2. Launcher refuses an empty password and prints the source (env or file), never the value.
3. Payload top-level `engine` label (cortex_app calibrated_forecast, circa 1218-1272).
4. DISCLAIMER_FULL naming both companies (W5 wording).
5. Untrack the three app/ generated outputs (stashed on the workstation 22 Sep); gitignore.
6. Market-brief first-call cost 6-8s, profile first.
7. TIF-AUH strip flags (22 Sep handover section 1).
8. "access: shared password ON" / "entry: DEMO sign-in OFF" print per job, not once.
9. warm_boards over the register, weeks of 12 and 19 Oct.
10. The band's upper limit once John sets it (PRESENT_LF_CAP in api_optimise).
11. Twelve or sixteen workers only after a memory reading during a sweep (server 3.9-4.6 GB,
    workers 2.4-2.8 GB each on 23 Sep; twelve broke the pool, cause unproven).

## 4. Workstation and DevPC procedure that worked (John's pastes are the record)

- Elevated PowerShell window: stops and pulls.
  cd C:\src\meridian; Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like
  '*cortex_app*' -or $_.CommandLine -like '*multiprocessing.spawn*' } | ForEach-Object {
  Stop-Process -Id $_.ProcessId -Force }; git pull; git log --oneline -1.
  A server launched from one window is stopped only from a window with at least its rights.
  "re-warming (no relaunch)" in the launcher output means the stop did not happen.
- Normal PowerShell window: launches. cd C:\src\meridian; $env:QSI_PASSWORD = Read-Host
  'Meridian password'; .\Meridian-run.bat. NEVER a pasted placeholder (two were pasted
  literally into $env:QSI_PASSWORD on 23 and 24 Sep). The launcher must print "MCT master:
  3,668 rows", "scikit-learn: 1.9.0  user site-packages: ignored", "optimise workers: 8",
  "forecast engine: BT2" and "server log: ...". A separate PowerShell window opens for the
  server and stays open; nobody clicks or types in it.
- Second normal window: probes and API calls. The probe reads QSI_PASSWORD from the
  environment (set it by Read-Host in that window too). Direct API calls use a Basic header
  built from a SecureString prompt:
  $pw = Read-Host 'Meridian password' -AsSecureString; $plain = [Runtime.InteropServices.
  Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($pw));
  $hdr = @{ Authorization = "Basic " + [Convert]::ToBase64String([Text.Encoding]::UTF8.
  GetBytes("meridian:" + $plain)) }; $plain = $null. A GET on /api/optimise needs &season=
  to sweep seasons (the endpoint default is "annual"; the browser sends blank).
- Probe: python diag_routes_timing.py --pairs "SJC-TPE:CI,BRS-EWR:UA,DUB-DFW:EI"
  --save-json E:\Avia\probe\<NAME>; then --diff <BASELINE> <NAME>. The diff counts opt_
  differences into FAIL; the pass condition after a selection change is the run_ lines.
  --skip-full saves the run_ files without the full sweep. The 23 Sep register pair is
  DUB-DFW:EI, not DUB-BOS (two stale DUB-BOS files sit in OPT-24Sep-select-w8; ignore).
- DevPC: cd C:\AviaDev; git pull; git add <files>; git commit -F COMMIT-MSG-<date>-<slug>.txt;
  git push; git log --oneline -1. The controller writes files on the mounted clone and never
  runs git there.
- The workstation was left on a detached HEAD (68a23d4) for the control run on 24 Sep and
  put back on main; if `git pull` ever says "not currently on a branch", `git checkout main`
  first.
- Access accounts: workstation logon aviaremote1 (Z: not mapped there; E: is the product
  drive mapped over D:); Carte logon has Z:. Nothing may depend on Z:.

## 5. The other workstreams: state at the last sweep (22 Sep) and what is due

Read the Wn-STATUS.md files on the first sweep; the Status table in the umbrella carries
the 22 Sep picture. In brief:
- W2 Stand flow (v14, 22 Sep): lead_store built, app not rewired; progressive Optimise back
  on the list (John: one button, nothing removed; must fit before 10 Oct); R6 radius plan;
  Postmark ruling recorded (section 7); runbook lines written 24 Sep (W2-RULINGS); STILL
  OWED from the controller: the data-store freeze line and the stale-RDP line. W2 also owns
  "Direct service today: None" and the curfew field labels (John entered a curfew at the
  destination by mistake on 24 Sep; the two fields need clearer labels).
- W3 Presentation (v2, 21 Sep): slides 1-6, 9-10 built; video script due 23 Sep (not seen);
  item 33 probe by 26 Sep; SJC-TPE and BLQ-JFK figures provisional until re-run on this
  server (W3-RULINGS 23 Sep); 92/86 off the methodology and track record pages.
- W4 Host manual v2 done; v3 after 8 Oct screenshots. Wording owed from the controller
  (NOT YET WRITTEN in W4-RULINGS): "about a minute" is now measured for the named Optimise
  and Run; the open sweep is "under two minutes"; "optimised" means the best-supported
  schedule by demand within the planning band, not the most profitable; an existing market
  is framed as an additional service in a market already served by N weekly flights.
- W5 Order-ready v0.3 done; solicitor slot week of 6 Oct; known issues frozen 10 Oct;
  disclaimer wording to W1 (queue item 4).
- W6 Messaging (v7, 21 Sep): four sentences, five contact names, post 1 and list email all
  await John (25 Sep); invitations 26-29 Sep; site still says three seats / 100
  presentations. Same wording lines as W4 owed in W6-RULINGS. W6 also drafts the wall
  graphics words for W9 once the sentences are picked.
- W8 Pricing: v1.0 FINAL; v1.1 (TAO Ltd entity line only) owed by the controller, 26 Sep.
- W10 Final calibration test (v1, 22 Sep): baseline rerun then 92/86 on 6,524 reproduced or
  replaced; says by 29 Sep whether 3 Oct holds; item 1 re-ruled to W2 (John to confirm).
  New questions for W10 from 24 Sep: the frequency response (7x to 14x +78% on SJC-TPE; the
  6x-7x dip on DUB-DFW) and the split floor's share-of-total behaviour. W10 and Nick also
  need telling that the workstation now runs with the MCT master and sklearn 1.9.0.
- W7 Rehearsal: trials 11-12 Oct remote, 16 Oct with Suzanna; a named person at the
  workstation for 11-12 Oct still needed.

## 6. W9 opens 25 Sep: the Informa email

Informa (exhibitor services) confirmed participation on 24 Sep 17:51 and introduced Full
Vision (routes@fullvision.co.uk) as the shell scheme contractor, who will also quote wall
graphics at additional cost and have been asked to liaise with John directly. W9-RULINGS
carries the ruling and W9's first five jobs (deadline table checked against Full Vision's
own artwork date; a one-page brief for John to send asking for inclusions, graphic sizes,
file specification, price per panel and deadline; the graphics decision for John by 30 Sep,
full graphics or logo panel only; what travels with whom; setup 20 Oct). The stand contract
paperwork (revised form from Charlotte Sullivan) is still open but Informa treats
participation as confirmed. The W9 prompt: write it from W9-RULINGS.md and the 19 Sep
brief's W9 section in the umbrella (section 5 there), Opus, complete and paste-ready, on
the first day of chat 4.

## 7. Postmark

Account approved 23 Sep (username TheAO, free plan 100/month). John's ruling, verbatim in
W2-RULINGS 22 Sep late: test with the test emails, warm the account, upgrade for the
conference if everything is smooth, switch provider on any issue at all; decision 3 Oct;
the fallback provider is named in W2-STATUS. W2's next STATUS should show the first real
test send and the warm-up schedule.

## 8. Step C: the decisions John has not been asked in one message

Put them in ONE message, full questions, with the consequence of silence, on day one:
item 26 (Bologna-New York carrier); 44 (sentence 2.3 A or B; silence 25 Sep = B); 45 (third
video route; silence 26 Sep = Copenhagen and Denver); 33 (W3 probe by 26 Sep); the five
contact names; post 1 and the list email approval; confirmation of the item 1 re-ruling to
W2; the accuracy pair (item 55, on W10's record by 3 Oct); the Optimise band's upper limit
(0.85 working assumption); the graphics decision (30 Sep); who is at the workstation 11-12
Oct; whether Suzanna's practice runs count against the quota (pre-mortem 19).

## 9. Diary

25 Sep: chat 4 opens; step C message; W9 prompt; W4/W6/W2 rulings lines; W8 v1.1.
26 Sep: FIRST FRIDAY NOTE (one phone screen); Full Vision brief sent by John; W3 probe.
29 Sep: W10 says whether 3 Oct holds. 30 Sep: graphics decision. 3 Oct: W10 record v1;
Postmark decision; accuracy pair; graphics artwork (to confirm against Full Vision).
6 Oct week: solicitor. 8 Oct: screenshots for W4 v3. 10 Oct: demo-path freeze, known issues
frozen, no data refresh from here. 11-12 Oct: remote trials. 16 Oct: trial with Suzanna.
20 Oct: setup. 21-23 Oct: Routes; order-ready 21 Oct.

## 10. Mistakes from chat 3 worth not repeating

- Two pasteable placeholders went into $env:QSI_PASSWORD literally. Read-Host only.
- I named the third register pair DUB-BOS from memory; it is DUB-DFW. Read the baseline
  folder's file names before writing a probe block.
- My first curfew implementation scaled the feed before the re-split and moved local; my
  first reading of the factor (0.736) was wrong and the tool (0.368) was right. Get the
  payload before asserting a mechanism.
- The 23 Sep split separated a route decorator from its function; a direct GET of every
  endpoint after any refactor of cortex_app is now part of W1's acceptance.
- "Most passengers" on demand is not "most passengers carried" once the aircraft is full.
- The control run needed a detached checkout on the workstation; say so in the block and
  put it back on main in the same message.
