# HANDOVER: programme controller, 23 September 2026, 00:30 BST (rolling)

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
