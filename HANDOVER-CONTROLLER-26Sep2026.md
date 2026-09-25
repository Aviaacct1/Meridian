# HANDOVER: programme controller, 26 September 2026, 03:30 BST (chat 4, day one)

For controller chat 4 continuing, or chat 5 if this one compacts. Supersedes
HANDOVER-CONTROLLER-24Sep2026.md except where this file points at it (workstation procedure,
section 4 there, unchanged; W1 acceptance detail, section 2 there). Everything here is true at
the files on the mounted clone at C:\AviaDev at the time of writing; John has NOT yet run the
commit block at the foot of this file. Workstation: 0eb7139 = origin/main (John's paste, 25 Sep).

## 1. Where the programme stands, one screen

Read the umbrella's Status block first: it carries THE CRITICAL PATH (five lines, locked 26
Sep), the table, and the sweep rulings. In one paragraph: the day found that Meridian reads
demand at 2 to 2.6 times Avia's own analysts on hub-ended long-haul (routes/FACE-VALIDITY-
REGISTER-25Sep2026.md, twenty routes from Avia's client forecasts on Egnyte, run on the
workstation); the mechanism is two-sided (V1 flat connecting feed 10-25x the analysts', which
the record never scored; a local over-read on small origins); John lifted the engine freeze
conditionally (pre-mortem 21) and the fix is the critical path: W10 diagnosis 29 Sep, John's
decision 30 Sep, W1 build 1-6 Oct, acceptance 7-8 Oct, video 8-10 Oct, freeze 10 Oct. W10's
baseline reproduced to the decimal; the V1.3 refit gives 91 / 85 on 6,524; John ruled the stand
sentence (one model, one record, one pair; 6,524 in writing, "about six and a half thousand"
spoken) and the stand flow (Optimise, explain, Run the visitor's case; three-line read-out).
The wall artwork must reach the designer by 2 Oct; the site must be live and John must have a
TAO mailbox before invitations go. W8 v1.1 was already issued; that owed item was stale.

## 2. Rulings John gave on 25-26 Sep, all verbatim in the umbrella decisions log

Freeze conditional; Bologna is the mild case; (b) ruled then found to be the existing design;
profit objective not revived; register from Avia's own forecasts; Knock indicative; SJC-TPE the
control; stand sentence (item 55); 6,524 precise in writing; Optimise-then-Run flow and the
host's explanation; visitor types; wall artwork by 2 Oct (no accuracy figure on the wall,
controller ruling); pens ordered this week ("Meridian" plus the web address, John's steer);
site live before invitations; invitations from John's TAO address only.

## 3. What the controller owes, in order (26 Sep)

1. John runs the commit block below (nine files).
2. FRIDAY NOTE, one phone screen, from this file's section 1 and the critical path.
3. W9 prompt (Opus), from routes/W9-RULINGS.md (four sections now) and the umbrella's W9
   section, with the one-page Full Vision brief John sends today (ask: panel sizes, file
   specification, price per panel, artwork deadline; reply by Mon 29 Sep).
4. Chase John for: items 40 and 44 (today), step C answers 5, 6, 11, 12; item 7 confirmation;
   the W10 paste (prompt text in the chat of 25 Sep evening, and W10-RULINGS' last two
   sections); W2's two spec blocks; the DevPC `git log --oneline -3`.
5. The Optimise half of the register (block in the chat, NOC-CDG spelling corrected) when John
   has twenty minutes; fill routes/FACE-VALIDITY-REGISTER-25Sep2026.md section B.
6. W1 queue (24 Sep handover section 3, item 1 now closed) behind the engine fix: new items:
   market_build step-5 note says "both directions" on an each-way figure (label, cortex_app
   circa 1448 area, market_build note text); the sweep-versus-run demand gap (113,382 v 148,271
   on BLQ-JFK) explained from the code and stated on the page; the B789-below-A21X local read
   in Test B (unexplained).
7. Rewrite this handover at the end of every day.

## 4. Traps found on 25 Sep

- `optimised` is a TOP-LEVEL key of /api/optimise's payload, not schedule.optimised.
- The market_build step-2 figure is EACH WAY; its step-5 note wrongly says "both directions".
- The sweep already reads demand at aircraft="A21N" (_cell_kw); do not propose anchoring it.
- bt2 runs need $env:PYTHONNOUSERSITE = "1" or the roaming sklearn 1.7.2 may load.
- bt2_paths reports the MCT master at E:\Avia\MCT Master List.xlsx, the launcher at
  E:\Avia\Reference Tables\MCT Master List.xlsx; the claimset ran, so it did not need it.
- Three times now a controller ruled ahead of the payload or the code (chat 3 twice, chat 4
  once on option (b)). Read the code path before ruling on a mechanism.
- The Egnyte research pass was done by a subagent (65 tool calls); its table is in the register
  file; Abha figures come from an embedded table via Egnyte AI and the Bologna route pax were
  not readable (20MB model, download blocked).

## 5. Probe artefacts on the workstation

E:\Avia\probe\BLQ-JFK-25Sep\opt_BLQ-JFK.json; E:\Avia\probe\FACE-25Sep\run_*.json and
runs.csv (twenty fixed-input Runs); claimset-W10-25Sep.log; mixed-W10-25Sep.log. The Optimise
half (opt_*.json, opts.csv) is not yet run.

## 6. Diary (amended 26 Sep)

26 Sep: commit; Friday note; W9 prompt and Full Vision brief; John: items 40, 44, names, post 1,
list email, item 7; W2 mailbox route ask if tenant. 27 Sep: W6 wall words to W3. 29 Sep: W10
diagnosis and pickle stamp; Full Vision spec; W2 mailbox route; site live; invitations from
here if the mailbox exists. 30 Sep: John decides the engine fix; graphics artwork under way.
1-6 Oct: W1 builds, W10 re-scores. 2 Oct: artwork to the designer; W2 capture demonstrable.
3 Oct: W3 to Jol and Nick (provisional charts); W10 record v1; Postmark decision. 6 Oct week:
solicitor; invitations latest. 7-8 Oct: acceptance; W3 re-runs; laptop proof; screenshots for
W4 v3. 8-10 Oct: video. 10 Oct: freeze, known issues frozen, no store refresh. 11-12 Oct:
trials. 16 Oct: Suzanna. 20 Oct: setup. 21-23 Oct: Routes; order-ready 21 Oct.

## 7. Commit block for today's files

**DevPC**
```
cd C:\AviaDev
git pull
git add GTM-STRATEGY-ROUTES-2026.md HANDOVER-CONTROLLER-26Sep2026.md routes/FACE-VALIDITY-REGISTER-25Sep2026.md routes/W2-RULINGS.md routes/W3-RULINGS.md routes/W4-RULINGS.md routes/W6-RULINGS.md routes/W9-RULINGS.md routes/W10-RULINGS.md COMMIT-MSG-26Sep2026-controller-day-one.txt
git commit -F COMMIT-MSG-26Sep2026-controller-day-one.txt
git push
git log --oneline -1
```
