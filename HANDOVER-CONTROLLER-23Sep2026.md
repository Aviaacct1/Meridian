# HANDOVER: programme controller, 24 September 2026, 15:00 BST (rolling; started 23 Sep)

For controller chat 3 (Fable) after a compaction, or chat 4. Read after
`PROMPT-for-Fable-Controller3-22Sep2026.txt` and instead of HANDOVER-CONTROLLER-22Sep2026.md,
which stays binding where this file is silent (sections 2, 4, 5, 7 there are unchanged).
Everything below is true at the commit John runs from the block in the controller chat of
22 Sep late (subject "Controller 23 Sep 00:30: ...", the tonight-findings commit); HEAD on
the workstation is d607d22 plus that pull.

## 1. What happened on 22 Sep evening, one screen

- W1 job 1 CLOSED. d607d22 (launcher default `--engine bt2`, stale warning replaced) is
  committed, pushed, pulled on the workstation, and the server restarted on it; the paste
  read "forecast engine: BT2 (calibrated model; claimset reproduced 22 Sep 2026)". Payload
  diff against the morning's engine-bt2 save: PASS, three Run payloads IDENTICAL, which also
  confirms W2's 30e3e78 friction fix changed nothing on the workstation.
- The workstation had been on 66455af (21 Sep) all day; nothing committed on 22 Sep had run
  there until circa 20:00. Every "the workstation pulled" line before that is untrue.
- The pull was blocked by three tracked generated files under app/ (Network_PnL_Genoa.xlsx,
  Route_Economics_slide.pptx, Route_Economics_test.xlsx), now in a stash on the workstation
  ("workstation generated outputs 22Sep"). Untrack and gitignore them: W1 job 7.
- One restart ran QSI for circa fifteen minutes before the fix arrived (old default).
- Password: the server reads $env:QSI_PASSWORD from the launching window only; there is no
  app\access_password.txt on the workstation; empty means shared password OFF behind
  Cloudflare Access. John set it and restarted; login from the laptop works. Pre-mortem 18.
- THE BIG ONE, pre-mortem 19: the dashboard's Optimise button runs the full sweep (all
  seasons, all carrier types, airline open, eight forecasts per cell under frequency-
  sensitive) and takes 460s SJC-TPE, 429s BRS-EWR, 334s DUB-DFW, 257s TIF-AUH. The narrowed
  default with the airline named (what the 22 Sep morning figures measured) is 44-57s. No
  visitor-driven Optimise has ever been under four minutes. John's ruling, verbatim in
  W2-RULINGS and the decisions log: one button, nothing removed. The fix is W1 job 0.
- Jol-type flags on the TIF-AUH strip, not yet actioned: total forecast (local plus feed)
  shown beside an addressable market that is local only; capture share 17.5% "of the
  catchment market" against P2P 55,925 of 123,373 (45%), two denominators, neither named.
  Goes to W1 (which is right) then W3/W4 wording. Feed is the flat capture: known-issues.

## 1a. 23 Sep daytime, one screen

- W1 job 0 BUILT (345e2e3), the diff exposed a pre-existing defect (departure-optimum cache
  key omitted freq), John ruled the fix in (4e5dd3c, verbatim in the umbrella), and the
  three-run test PASSED: full sweep 96.9 / 117.3 / 91.0s at 8 workers v 491.6 / 523.4 /
  404.6s sequential, all nine payloads identical. Server left on 8 workers, BT2, 4e5dd3c.
  Evidence: E:\Avia\probe\OPT-23Sep-fix-w1 and -w8 (+ .log), TIMING-20260923-*.md.
- Named single-airline Optimise (one cell) is 55-76s and gets nothing from the pool: NEXT
  W1 job is splitting a cell by frequency (task = cand x type x season x freq; the base 7x
  forecast supplies econ_share, so stage 1 = 9 base forecasts in parallel, stage 2 = 63
  frequency forecasts in parallel, then selection and final unchanged). Same three-run test
  (1 / 8 / 12), diff against OPT-23Sep-fix-w1 is the acceptance.
- W3-RULINGS 23 Sep: SJC-TPE and BLQ-JFK figures provisional until re-run on the fixed code.
- Postmark APPROVED 23 Sep 17:33 (free plan, 100/month); John's ruling on plan and exit in
  W2-RULINGS (upgrade only if the domain tests are clean; any issue = switch; decide 3 Oct).
- Traps today: a PowerShell window on the DevPC was mistaken for the workstation (no
  C:\src\meridian, no E:); ssh aviaremote1@donatello refused the password (RustDesk used);
  a placeholder in a block was pasted literally into $env:QSI_PASSWORD (never hand a
  pasteable placeholder); clicking in a console pauses the probe (QuickEdit).

## 1b. 23 Sep evening

- Frequency split SHIPPED (6065e18): full sweep 66.5 / 109.3 / 64.7s, named 30.3 / 32.6 /
  18.4s at 8 workers, all payloads identical to OPT-23Sep-fix-w1. Evidence: OPT-23Sep-split-w1,
  -w8 (+ .log), TIMING-20260923-1859 / -1928.
- 12 workers FAILED (worker killed, pool broken, OPT-23Sep-split-w12 has only the named
  SJC-TPE payload). Default stays 8. Rebuild fix written on the DevPC
  (COMMIT-MSG-23Sep2026-w1-pool-rebuild.txt), NOT pushed, NOT on the workstation: first job
  24 Sep, then the kill test (Stop-Process one worker mid-sweep; expect a reported error,
  then a clean Optimise) and the worker peak-memory reading (Get-Process python during a
  sweep; the one reading taken so far, 2,012 MB, was the server alone with no sweep running).
- Workstation state at close: 6065e18, 8 workers, BT2, QSI_PASSWORD set in the launching
  window (non-elevated, aviaremote1 over RustDesk). Server was found DOWN at 20:15 and
  relaunched; "Failed to fetch" on the public dashboard is the symptom of no listener.
- Still unsent: step C (the week's decisions in one message). Still unwritten: W4 and W6
  wording lines; W2 data-store freeze and runbook lines; W8 v1.1.

## 1c. 24 Sep morning

- Clean start done: elevated window stops the listener and any orphaned pool workers (command
  line contains multiprocessing.spawn); normal window launches. Orphan fix live (9195b3f):
  workers exit when the server process ends.
- MCT MASTER WAS NOT LOADED in the aviaremote1 logon (Z: is a per-logon Egnyte letter):
  every run in that logon to this point used the flat default MCT (pre-mortem 16 live).
  John's ruling: nothing depends on a per-logon letter; E: carries everything so a
  workstation can be cloned (he wants two or three workstations in different locations for
  resilience and load). Launcher now sets AVIA_MCT_MASTER=%AVIA_ROOT%\Reference Tables\MCT
  Master List.xlsx (5e0b597); file copied by John; server 79120 started with "MCT master:
  3,668 rows from E:\Avia\Reference Tables\MCT Master List.xlsx". EVERY BASELINE BEFORE THIS
  (engine-bt2, OPT-23Sep-*) was taken without the master; the acceptance baseline for any
  future W1 change is re-taken on this state; W3's re-run waits for this state.
- sklearn: workers print InconsistentVersionWarning, model pickled under scikit-learn 1.9.0,
  loaded under 1.7.2 from C:\Users\Carte\AppData\Roaming\Python (a per-user package folder
  shadowing the machine install; also shows the server runs in the Carte logon). Which
  version reproduced the 13 Aug claimset on 22 Sep is UNKNOWN. Check owed (one line, both
  logons): py -3.12 -c "import sklearn, sys; print(sklearn.__version__, sklearn.__file__)".
  Goes to W10 and W1; may need the pinned version installed machine-wide.
- SJC-TPE on this server: China Airlines 7x A359 annual 172,216 two-way (77,414 local,
  94,802 feed, 77.3%); winter-only rows had been winning the headline on load factor alone
  (selection ranks nearest-to-80%, not passengers, against the 8 Aug objective): John did
  not rule on the selection change yet; parked behind the curfew must-fix.
- MUST FIX (John, verbatim in the umbrella): a curfew that moves the departure must move
  the headline; the level is flat (15 Aug) so today it does not. W1 builds: restricted runs
  scale the feed headline by permitted-v-unrestricted score; chart shows the unrestricted
  figure; unrestricted runs unchanged; approved freeze exception confined to restricted runs.
- Market background shows "Direct service today: None" for SJC-TPE (two nonstop operators
  in the OAG week). W2 to check the market-brief query against the OAG store.
- Pool kill test DONE 24 Sep afternoon on 19d94df, eight workers, MCT master loaded:
  mid-sweep kill (worker 60684) gave the panel "Optimise failed: a worker process was
  terminated (memory or crash); the pool has been rebuilt, run Optimise again" and the next
  Optimise completed; idle kill (worker 69492) took the other seven down with it (Python's
  pool manager does that itself, count went to 0), the next Optimise completed and the count
  came back to 8. Both cases PASS. Cosmetic for W1: strip "RuntimeError:" from the panel.
- RULING 24 Sep (verbatim in the umbrella decisions log): season blank means the headline
  is the annual row carrying the most two-way passengers within the viable load factor band
  (limits John's to set, 65-85% working assumption); one line names a seasonal row that
  fills better ("select Winter and Optimise again"), nothing otherwise; explicit season
  honoured as today. Cause found: api_optimise ranks all rows by nearest-to-80% LF and
  economics never enter the choice, so EVA B789 5x winter 51,196 beats CI 7x A359 annual
  172,216 on SJC-TPE. Ships with the curfew must-fix; acceptance three-pair diff plus a
  blank-form SJC-TPE run three times identical with the annual row as headline. Panel
  wording ("optimised" = best-supported by demand, not most profitable) to W4.
- HP Envy Enter/Backspace: intermittent (came back on its own 24 Sep 14:30); on-screen
  keyboard works, so an external keyboard (wired or wireless) bypasses it. Not RustDesk.
- Runbook facts: a server launched from one window is stopped only from a window with at
  least its rights (elevated stop, normal launch); "re-warming (no relaunch)" in the
  launcher output means the stop did not happen; QSI_PASSWORD is set by
  `$env:QSI_PASSWORD = Read-Host 'Meridian password'`, never a pasted placeholder (two
  placeholders were pasted literally on 23 and 24 Sep).

## 2. W1 job 0: parallel Optimise (controller's own code)

Design agreed with John 22 Sep: the sweep's cells (candidate x carrier type x season; the
frequency loop stays inside the cell) run in a process pool started with the server, kept
warm; worker count from config (default 8), `--workers 1` is byte-for-byte today's path and
the control; each worker limits DuckDB threads to 1-2; selection logic unchanged, run once
over the collected rows; no demand logic touched. Acceptance: three-pair probe at 1 / 8 / 12
workers, `--diff` PASS against TIMING-22Sep-d607d22-full on every setting, full sweep under
two minutes on the register pairs (target 60-90s; "under a minute" only if measured). If
two minutes is not reached, the next lever is inside the frequency loop and needs John's
explicit ruling first. Workstation: Ultra 9, 20 cores, 64 GB. Written on the DevPC, John
commits, workstation pulls, John runs the probes, pastes are the record.

## 3. W1 queue after job 0

1. Launcher refuses an empty password and prints the source (env or file), never the value.
2. Payload top-level `engine` label (cortex_app calibrated_forecast, circa 1218-1272).
3. DISCLAIMER_FULL naming both companies (W5 wording).
4. Untrack the three app/ generated outputs; gitignore.
5. Market-brief first-call cost, 6-8s measured tonight (8.1 / 7.3 / 6.0s), profile first.
6. The TIF-AUH strip flags (section 1).
7. warm_boards over the register, week of 12 Oct and 19 Oct.

## 4. Owed to other workstreams (write into rulings files, same day)

- W2-RULINGS: written 22 Sep late (one button; progressive Optimise back on the list, must
  fit before 10 Oct; sizing owed in STATUS). Still owed: data-store freeze line (no OAG or
  Sabre refresh 10 Oct to after Routes); runbook restart procedure starts with the set line
  for QSI_PASSWORD; sign out stale RDP sessions before trials.
- W4-RULINGS and W6-RULINGS: "about a minute" is a Run claim only; Optimise is "a few
  minutes; the host talks through the methodology page while it runs" until job 0 is
  measured. NOT YET WRITTEN.
- W8: v1.1 of the pricing file for the TAO Ltd entity line, controller issues.

## 5. Step C, not yet sent: the decisions due this week, full questions in one message

Items 26 (Bologna-New York carrier), 44 (sentence 2.3 A or B; silence 25 Sep = B), 45
(third video route; silence 26 Sep = Copenhagen and Denver), 33 (W3 probe by 26 Sep), the
five contact names (Thu), post 1 and the list email (approve by 25 Sep), whether W9 and W10
chats are open, confirmation of the item 1 re-ruling to W2, and now the Optimise wording
for the host until job 0 lands.

## 6. Diary changes

23-24 Sep job 0 code; 26 Sep FRIDAY NOTE (first), job 0 measured, item 33 probe; the rest as
the 22 Sep handover section 6.

## 7. Mistakes tonight worth not repeating

- Handed a block with a `<placeholder>` in it. Every block is runnable as pasted.
- Put `--skip-full` on a probe meant for a payload diff; the diff was void. Read the
  harness's help before choosing flags.
- Ran read-only git (log, rev-parse, diff --stat) against the mounted clone at the start of
  the session. Not again; John's paste is the record.
- Recorded "workstation pulled" from the umbrella rather than a paste; it was false for a day.
