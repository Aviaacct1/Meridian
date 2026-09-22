# HANDOVER: programme controller, 22 September 2026, 08:00 BST

For controller chat 3 (Fable). Chat 2 ran 20-22 Sep, compacted once, and closes here. Read
this after `PROMPT-for-Fable-Controller3-22Sep2026.txt` (the brief) and before the umbrella.
`PROMPT-for-Fable-Routes-19Sep2026.txt` (the original brief) and
`HANDOVER-CONTROLLER-20Sep2026.md` (chat 1's handover) stay binding where this file is
silent; do not re-read them in full, they cost context. Everything below is true at the
commit John runs from the closing message of chat 2 (subject "Controller 22 Sep: W10 (final
calibration test) created ..."); confirm HEAD before anything else.

## 1. What changed since the 20 Sep handover, in one screen

- Order-ready is 21 Oct (was 7 Nov). Pricing is FINAL (routes/PRICING-DECISION-2026.md
  v1.0, W8 closed; v1.1 owed for the TAO Ltd entity line). Nothing else states a price.
- Entity: The Aviation Observatory Limited (17411365, 86-90 Paul Street, London EC2A 4NE)
  is the exhibitor, the contracting party and the brand; Avia pays Informa meanwhile as an
  intercompany loan; VAT registration as an intending trader is with the accountant. PI cover
  and a TAO bank account are the binding constraints on order-ready (pre-mortem 17).
- Stand F124 (not F174; a 19 Sep transcription error was fixed in twelve files). W9 exists
  for stand, contract, exhibitor manual, badges, kit. Contract unsigned pending Charlotte
  Sullivan's revised form; graphics deadline 3 Oct; Routes 360 declined unless John says.
- W1 step 2 CLOSED: on-disk boards and land-path caches; Run cold 17 / 20 / 13s on QSI,
  warm 8-11s; Optimise 38-53s. "About a minute" is released to W6 for Run.
- The calibrated engine (BT2) is the on-screen engine from 22 Sep: server on donatello is
  running `--engine bt2`; claimset baseline reproduced exactly; timings faster than QSI. The
  launcher still DEFAULTS TO QSI, so the next restart silently reverts. First W1 job below.
- Item 25 settled in substance on John's sentence. W10 created (final calibration test):
  catchment radius first, then the 22 Sep baseline, then reproduce or replace 92/86 on
  6,524; ONE figure set to John by 3 Oct. Interim on every surface: 89/82 on 2,915.
- Jol's 43-item feedback triaged (routes/JOL-FEEDBACK-REGISTER.md, rulings R1-R8) into
  W2, W3, W4. Each-way / two-way on every figure is John's most important item; "actual"
  not "measured"; no "physics"; catchment page rewritten before the freeze.
- Messaging is in The Aviation Observatory's voice, not Avia's (W6 variants v3). Recording
  on the stand is tested on the day, market intelligence only, never per person.
- Postmark: account "reviewing"; delivery proven by API with a MessageID; the SMTP path
  discarded three messages silently. Programme rule: no send counts without a provider
  MessageID.

## 2. The ten workstreams and who runs them

Controller runs W1 and W7 in its own chat. W2, W3, W4, W5, W6, W9, W10 are Opus chats John
opens from paste-ready prompts; W8 is closed. Each chat reads routes/README.md, its
Wn-RULINGS.md (controller writes) and writes its Wn-STATUS.md. The umbrella Status block is
the single truth; a chat's status changes nothing until the sweep puts it there.

| WS | Chat state at handover | Its rulings file version | Next controller action |
|---|---|---|---|
| W1 | in this chat | n/a | launcher default bt2; engine label; disclaimer; market-brief cost; warm_boards run |
| W2 | open, STATUS v13 | W2-RULINGS (Jol section added 21 Sep) | sweep after lead_store rewiring; data-store freeze line owed to W2-RULINGS; runbook line on stale sessions |
| W3 | open, STATUS v2 | W3-RULINGS (22 Sep accuracy section) | sweep after methodology page change and the video script (23 Sep) |
| W4 | open, STATUS v2 | W4-RULINGS (Jol section) | v3 after 8 Oct screenshots |
| W5 | open, STATUS v0.3 | W5-RULINGS (TAO entity) | solicitor slot wk 6 Oct; known-issues frozen 10 Oct |
| W6 | open, STATUS v7 | W6-RULINGS (voice, "about a minute") | John's approvals 25 Sep; invitations 26-29 Sep |
| W8 | closed | W8-RULINGS (decision 15 override) | v1.1 of the pricing file for TAO Ltd |
| W9 | not yet opened | W9-RULINGS v1 | John opens it once Charlotte's form is back |
| W10 | not yet opened | W10-RULINGS v1 | John opens it from the prompt in chat 2; catchment text may be pasted verbatim |
| W7 | controller | n/a | trials 11-12 Oct remote, 16 Oct with Suzanna; freeze 10 Oct |

## 3. W1, the controller's own code, exactly where it stands

Committed: `app/wave_cache.py` on-disk boards (`AVIA_BOARDS_DISK`, `AVIA_BOARDS_DIR`,
`disk_stats()`), `app/water_check.py` land-path sqlite (`AVIA_WATER_DISK`, `AVIA_WATER_DIR`,
`land_path_stats()`), `app/warm_boards.py` with `routes/PREWARM-AIRPORTS.txt` (196 codes,
tiers 1-2; tier 3 not mapped; run it in the week of 12 Oct and again 19 Oct).

Owed, in order:
1. `app/warm_demo.py`: default `--engine bt2`; replace the "accuracy NOT re-measured since
   the 13 Aug rebuild" warning with "claimset reproduced 22 Sep 2026". `Meridian-run.bat`
   unchanged if it passes no engine flag; check.
2. `app/cortex_app.py` calibrated_forecast() (circa lines 1218-1272): the payload's
   top-level `engine` string says "route_forecast (calibrated)" whichever engine ran;
   provenance.local_leg is right. Make the top-level string agree.
3. `app/aircraft_economics.py DISCLAIMER_FULL`: names both companies (The Aviation
   Observatory Limited, affiliated to Avia Solutions Limited); W5 has the wording ruling.
4. Market-brief first-call cost (6-8s), measure before touching.
5. Data-store freeze rule (no OAG or Sabre refresh from 10 Oct to after Routes) into the
   umbrella and W2-RULINGS; W2 runbook line: sign out stale RDP sessions before trials.
6. Atlas row for Jess (same stand, same freeze); not yet in the Status table.

Evidence files on the workstation: `E:\Avia\probe\claimset-22Sep.log`,
`TIMING-20260922-0628` (bt2 probe), r2 / r4 / r5 diffs PASS. Rollback of the engine is the
launcher flag `--engine qsi`; nothing else.

## 4. Machines and traps learned in chat 2 (adds to the 20 Sep handover section 2)

- John is travelling (Doha this week) on a MateBook; access is RustDesk over Tailscale to
  the DevPC (desktop-3r7oqvj, 100.109.119.6) and the workstation (donatello,
  100.77.239.22). Bat files `Donatello-Connect.bat`, `DevPC-Connect.bat`,
  `Avia-RustDesk-Connect.bat` were handed to him in chat 2 (sidebar), not committed.
- E: on the workstation is a per-logon mapped drive. Invisible to ssh and to WMI-launched
  processes; `Test-Path D:\Avia\bt2_relaxed` is False from those contexts, so E: is not
  simply D: either. Anything that needs E: runs in an RDP PowerShell window (Workstation
  Actual), with `Tee-Object` to a log so it survives the disconnect.
- A python process owned by another logon (carte) needs an elevated prompt to stop;
  elevated windows lose E:; relaunch from a non-elevated window.
- `Meridian-run.bat` re-warms a running server. Stop the 8010 listener first
  (`Get-NetTCPConnection -LocalPort 8010 -State Listen`), or you measure old code.
- The DevPC had a second clone at `C:\src\meridian` (not John's doing); deleted 21 Sep.
  If W2 blocks run on the wrong machine again, check for it.
- Informa Condition 5.3: organiser data lists never into a third-party AI; delegate names
  never pasted into any chat. Organisation names only.

## 5. Waiting on John, open at handover (umbrella numbers)

4 host contract details; 10 host training dates; 11 competitor page off the site; 13 the
five meetings (invitations 26-29 Sep); 19 Suzanna's practice quota; 20 DNS move (silence =
yes); 21-22 pack URL controls and two emails (ruled unless he objects); 24 tablet; 26
Bologna-New York carrier; 27 rights records; 33 W3 probe run by 26 Sep; 34 W4's three; 36
order-ready code half; 38 Charlotte's revised form, sign, file in the TAO Legal folder; 39
Routes 360 (declined by silence); 40 graphics by 3 Oct; 44 sentence 2.3 A or B; 45 third
video route; 46 Suzanna session wk 29 Sep; 47 twelve months' notice; 48 TAO no trading
history; 49 solicitor slot wk 6 Oct; 50 support address; 51 OAG and Sabre told; 52 VAT
registration; 53 ask Nick "actual, calibrated, capped"; 54 pens; 55 which accuracy pair (by
3 Oct, on W10's record); 56 open the W10 chat. Plus: five contact names (Thu), approve post 1
and the list email, SSD by Sun 28 Sep, PI chase, W8 v1.1.

## 6. Diary

23 Sep W3 video script; 25 Sep sentences, contacts, post 1; 26 Sep FRIDAY NOTE (first one,
not yet written), item 33 probe, W1 launcher change committed; 26-29 Sep invitations; wk 29
Sep Suzanna session; 29 Sep W10 says if 3 Oct holds; 3 Oct W3 five items to Jol and Nick,
graphics to Informa, W10 record v1, John rules item 55; wk 6 Oct solicitor; 8 Oct laptop
proof and screenshots; 10 Oct FREEZE and data-store freeze; 11-12 Oct remote trials; 12 Oct
warm_boards over the register; 13 Oct Atlas meeting (not a Meridian trial); 16 Oct trial with
Suzanna; 19 Oct warm-up; 20 Oct Suzanna lands; 21-23 Oct Routes, F124; 21 Oct order-ready;
30 Nov launch offer closes.

## 6a. Added 22 Sep evening, after the commit

30e3e78 swept W2's catchment-distance fix and W10's session 1 into the controller's commit.
W10 found the catchment radius is not a calibration input; item 1 re-ruled to W2 under R6
(W10-RULINGS evening section, W2-RULINGS, umbrella decision). Freeze exception withdrawn.
W10 is OPEN and proceeds with items 2 and 3; John has not yet confirmed the re-ruling.
W2 is on STATUS v14. First sweep in chat 3: W10 (baseline paste), W2 (R6 radius plan).
Verify W10's claim with one grep before relying on it: haul_radius_km and DEMAND_RADIUS_KM
must not appear in bt2/ or in the claimset's feature build.

## 7. Mistakes in chat 2 worth not repeating

- Ran `git -C . status` (read-only) against the mount once. Do not.
- Claimed item 25 needed a two-day build before reading calibrated_forecast(); the wiring
  existed. Read the code before sizing anything.
- Gave John item numbers instead of the questions; he cannot use numbers on a phone. List
  the full question every time.
- Edited a workstream's file (the F124 fix) without announcing it in that workstream's
  rulings file the same day; W4 caught it. Rule now in README.
- Let John's catchment radius specification live only in the chat; the compaction lost the
  verbatim text and W10-RULINGS item 1 is a restatement. Anything John writes that a
  workstream must build to goes into a file the same turn.
- Handed a rollback block (engine to QSI) without confirming whether he ran it; the server
  state had to be inferred. Ask for the paste before recording state.
- Chat 2 reached compaction at circa 60 hours of work. Write the handover BEFORE the chat
  is full, at the end of each working day, as a rolling file; then closing costs nothing.
