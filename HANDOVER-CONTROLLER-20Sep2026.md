# HANDOVER: programme controller, 20 September 2026, 15:00

For the NEXT controller chat (Fable). The first controller chat ran 19-20 Sep, compacted
once, and closes here so the new one has the capacity to research and decide. Read this after
`PROMPT-for-Fable-Routes-19Sep2026.txt` (the brief, still binding) and before the umbrella.
Everything below is true at commit e38f76a on `Aviaacct1/Meridian` main plus the uncommitted
controller edits listed in section 8.

## 1. How the programme is run (John's rules, added to the brief during the first chat)

- Every command block is labelled DevPC / Workstation Remote / Workstation Actual, one machine
  per block, `cd` first, commands only. John never copies text from inside a file: anything he
  must paste is given in the chat message itself.
- Every new chat gets a complete paste-ready prompt with the model named. Controller on Fable;
  workstream chats on Opus. Each prompt points the chat at `routes/README.md`, its own
  `routes/Wn-RULINGS.md` (controller writes) and `routes/Wn-STATUS.md` (the chat writes);
  nobody edits the other's file. Facts cross workstreams only via STATUS files, quoted with
  version.
- The "sweep" (README): on John's word "sweep", the controller re-reads every STATUS file,
  reconciles conflicts in the umbrella and the rulings files, and rewrites the Status block.
- Never run git against the mounted clone. Hand John a DevPC block. One commit-message file
  per commit (`COMMIT-MSG-<date>-<slug>.txt`); W3 reused one once and the wrong subject went in.
- The umbrella `GTM-STRATEGY-ROUTES-2026.md`: Status block rewritten every session (one phone
  screen); Decisions log; Waiting on John, numbered, with the consequence of silence; the
  pre-mortem as a checklist, items never deleted. Friday note on Fridays; the first is due
  26 Sep and has not been written.
- Honesty over comfort; flag rather than fill; no figure without a source in the sentence;
  nothing "illustrative" client-facing; nothing about any competitor in any material.

## 2. Machines and access

- DevPC: `C:\AviaDev` (clone). Cowork mounts `C:\AviaDev` and the project folder; the mount
  can read and write files but must not run git. Python is available in the device shell.
- Workstation DONATELLO, unmanned: clone `C:\src\meridian`, data root `E:\Avia` (mapped over
  `D:\Avia`). Access from the DevPC over Tailscale: ssh for commands (password: John types it;
  in PowerShell set `$env:QSI_PASSWORD='...'` with single quotes, `$` expands otherwise); RDP
  only for a restart (sign in, run the launchers, DISCONNECT, never sign out; RDP evicts
  whoever is at the screen). Launcher `.\Meridian-run.bat` runs `warm_demo.py` and serves
  `127.0.0.1:8010`. The launcher re-warms a running server rather than replacing it, so
  `Stop-Process -Id <pid> -Force` first or you measure old code (this happened once).
- Timing probe `diag_routes_timing.py` (repo root): `--pairs`, `--skip-full`,
  `--profile ORIG-DEST:AL`, `--save-json DIR`, `--diff BEFORE AFTER` (exit 1 on any payload
  difference, volatile keys ignored). Port defaults to 8010 now. Evidence files TIMING-*.md
  on the workstation.
- Chrome extension reaches the Grip (Routes matchmaking) platform when John has it open; the
  person-level pull is blocked by the PII classifier; organisation-level harvest from rendered
  cards works. The extension drops mid-read; ask John "is Chrome open" and resume.

## 3. Where W1 (the controller's own workstream) stands

Step 1 SHIPPED at 1012c29: `wave_cache.shared(oag_db)` one boards object per store per
process with an RLock (`AVIA_SHARED_BOARDS=0` to A/B); `mct_bank.load_mct` memoised on (path,
mtime_ns, size); `airportsdata.load` memoised at cortex_app import returning shallow copies
(`AVIA_APDATA_MEMO=0`). Measured on the workstation: Run SJC-TPE 35.4s to 9.8s cold and 8.9s
warm; BRS-EWR 42.5s to 9.0s; Optimise narrowed 161s to 65s and 196s to 35s; payload diff
PASS. Both acceptance targets in the brief are met. Profile of one Run before step 1 (42.9s):
Sabre is not in the top 45 by time; the cost was `wave_cache._row_to_leg` (836,930 calls),
catchment `water_check`, and `airportsdata.load` 32 times.

Preagg: store built on the workstation at `E:\Avia\preagg.duckdb` (od_p2p, od_single,
sector_adj 859,129 rows; 426s); `verify_identity.py` PASS 85/85; the back-test saving was
only 11%. The live app has NO preagg hook (only `backtest.py --preagg` and
`route_feed` feed_cfg["preagg"]); wiring it is step 3 and is only worth doing if a profile
after step 2 shows the feed query on the critical path.

STEP 2, NOT STARTED, the next controller job: persist the shared boards, the MCT table and
the airport table under `LOCAL_CACHE` keyed on store vintage (path, mtime_ns, size) so a
server restart does not pay the cold cost; then a warm-up pass at startup over the airports
in the Routes register (`ROUTES-ATTENDING-ORGANISATIONS-21Sep2026.md`, needs IATA codes
adding, not yet done). Method: `--save-json` before, change, restart, `--save-json` after,
`--diff`; report cold and warm Run and Optimise on SJC-TPE, BRS-EWR and one unfamiliar pair.
Code ownership per README: W1 owns the run path in `cortex_app.py`, `wave_cache.py`,
`route_feed.py`, `catchment.py`, `water_check.py`, `preagg.py`, `config.py` cache paths.
The engine's demand logic is frozen. Demo-path freeze 10 Oct.

Also owed by the controller: a proposal to John for a 40-60 route panel (he ruled SJC-TPE and
Bologna-New York stay as the worked routes and may add more; item 26, the carrier for
Bologna-New York, is his).

## 4. The other workstreams, one line each (detail in their STATUS files)

- W2 Stand flow (Opus, v7): MCT master reports at startup (2cab1b2); Postmark is the sender,
  domain verified, account in TEST MODE awaiting approval (expected Mon 22 Sep; chase 1 Oct);
  MateBook is ARM64 so Plan A only; Plan B needs an x86 laptop and a 1TB external NVMe SSD
  (item 14, John to order by 28 Sep). Next: DNS to Cloudflare week of 22 Sep (item 20),
  DuckDB leads table, stand mode, capture front end demonstrable 2 Oct, laptop proof 8 Oct.
- W3 Presentation (Opus): slides 1-6, 9-10 built (3af5158); provenance fix proven (45a5210);
  PDF is the full researched pack, HTML the 20-minute pitch page; Commons coverage probe
  written, unrun (item 33, John runs it on the workstation by 26 Sep, needs `fop-refresh`
  first); slides 7-8 wait on the worked-route runs 29 Sep-1 Oct. All four items to Jol and
  Nick 3 Oct.
- W4 Host (Opus): STAND-HOST-MANUAL.md v1 (648 lines, 27 slots). v2 after Suzanna's answers
  (item 23, John to send W2's four questions) and the 8 Oct screenshots. Host: Suzanna
  McIntosh, suzanna.mcintosh@gmail.com, stand F124, lands Tue 20 Oct, works Wed-Fri 9-5;
  Stefan Parry may join. Item 34: John owes second and third phone contacts, his stand hours,
  and the competitor sentence in manual 4.4.
- W5 Order-ready documents (Opus, v0.2 committed 3197c43): agreement and one-pager v0.2 to
  the 20 Sep term rulings; invoice, onboarding script, known-issues list, licence-record form
  to come; agreement to the solicitor 3 Oct; item 31 (entity: Avia Solutions Limited or The
  Aviation Observatory Ltd; and the solicitor's name) is John's.
- W6 Messaging, marketing, website, meetings (Opus, committed a03d2b6): launch offer in the
  messaging and invitations; the site to launch is The Aviation Observatory site
  (`Aviaacct1/tao-website`, Eleventy, Cloudflare Pages), competitor name in header and footer
  of 8 files and prices in 8 places must come out; pricing not published until November;
  four sentences for John by 25 Sep; five contacts by 25 Sep (buyer-test meetings: Birmingham,
  Dublin, Vienna, Dallas Fort Worth, Milan SEA; reserves in the organisations file);
  invitations 26-29 Sep.
- W7 Rehearsal and freeze: 13 Oct "Boeing" is an Atlas meeting, not a Meridian trial;
  Meridian trials are 11-12 Oct (remote, one restart) and 16 Oct with Suzanna. Nothing until
  October; the controller diaries the trials. Freeze 10 Oct.
- W8 Pricing and the commercial offer (Opus, NEW 20 Sep): owns the tiers and every number;
  produces `routes/PRICING-DECISION-2026.md`; target 26 Sep, hard 3 Oct. Umbrella item 37 is
  provisional until W8 says FINAL. Rulings in `routes/W8-RULINGS.md` v1.

## 5. Pricing: where it stands and why it moved to W8

On 20 Sep John ruled the launch offer (50/75/85, three fixed cash prices, sign by 30 Nov),
the term clauses, the escalation, the named-discount principle and the no-pro-rata rule,
and then the tier table was rewritten four times in the controller chat: by size (2-3 Aug
grid) to by option (£15k/£20k/£25k) to by usage (£15k/£22.5k/£27.5k with a 100-pack cap).
John's unease, unresolved: the Tier 1 to 2 step is weak for a buyer who does not yet value
the researched pack, and Tier 3 gives a large airport no reason to pay more. The controller's
last, unanswered proposal: Tier 2 sells the airline meeting (demo closes on the pack); Tier 3
sells the board, headlined by bundling the client's Avia Global Forecast entry. W8 takes it
from there. The controller does not price anything; it waits for W8's file.

## 6. Waiting on John, open at handover (numbers are the umbrella's)

6 launch places, overage or per-pack rate, payment terms, entity (now W8's to close with him);
14 SSD order by 28 Sep; 20 DNS to Cloudflare (silence to 26 Sep = yes); 21-22 pack URL controls
and two emails (ruled unless he objects); 23 send Suzanna the four questions (silence to 23
Sep = yes); 24 tablet; 25 the accuracy sentence, what the 89% describes, by 26 Sep, Nick signs;
26 carrier for Bologna-New York by 23 Sep; 27 and 35 as recorded; 31 entity and solicitor;
33 W3 probe run by 26 Sep; 34 W4's three; 36 order-ready code half (ruled unless he objects);
37 provisional, to W8. The four messaging sentences and five contacts by 25 Sep.

## 7. Diary

22 Sep Postmark approval expected; 23 Sep items 23 and 26; 25 Sep sentences and contacts;
26 Sep Friday note, items 20, 25, 33, W8 target; 26-29 Sep invitations; 29 Sep-1 Oct worked
route runs for W3; 2 Oct capture front end demonstrable; 3 Oct W3 four items to Jol and Nick,
W5 agreement to solicitor, W8 hard deadline; 8 Oct laptop proof and screenshots; 10 Oct
freeze; 11-12 Oct remote trial; 13 Oct Atlas meeting; 16 Oct trial with Suzanna; 20 Oct
Suzanna lands; 21-23 Oct Routes, stand F124; 21 Oct order-ready; 30 Nov launch offer closes.

## 8. Uncommitted at handover, and the mistakes worth not repeating

Uncommitted controller edits (John runs the block in the closing message): this file,
`routes/W8-RULINGS.md`, `routes/README.md` (W8 rows), the umbrella (W8 in Status, item 37
marked provisional), and one line at the top of the W3-W6 rulings blocks marking the tier
table provisional. `git status` also shows modified `HANDOVER-23Aug2026.md`,
`diag_tpe_sjc_catchment_decomp.py`, three `app/*.xlsx|pptx` and `routes/W5-STATUS.md`, plus
four old COMMIT-MSG files untracked: not the controller's; ask John whose before adding.

Mistakes made once: dated all 19 Sep work "21 Sep" (file contents fixed, commit subjects not;
the organisations file keeps its misnamed date); measured after-run timings against a server
that had not been restarted; the probe defaulted to port 8000 (fixed); asked John to copy
text from a file (do not); two contradictory recommendations in one item after an edit (W5
caught it; one recommendation per item); reused commit-message file (W3). A 24GB
`app/preagg.duckdb.tmp` was found on the DevPC, checked and deleted; watch for it again.
