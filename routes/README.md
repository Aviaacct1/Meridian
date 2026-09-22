# routes/: how the Routes 2026 workstreams are controlled

Owned by the programme controller (the Fable chat). Every workstream chat reads this file
first. Version 1, 19 September 2026.

## The files and who writes them

| File | Written by | Read by |
|---|---|---|
| ../GTM-STRATEGY-ROUTES-2026.md (umbrella: Status, Decisions log, Waiting on John, pre-mortem) | controller only | everyone |
| Wn-RULINGS.md | controller only | workstream n |
| Wn-STATUS.md | workstream n only, rewritten each session | controller, and any other workstream that needs a fact |
| ../MASTER-TASK-LIST.md | controller only | everyone |
| STAND-HOST-MANUAL.md and other deliverables | the owning workstream | everyone |
| PRICING-DECISION-2026.md (the only file that states a price; others quote it with its version) | W8 only | everyone |

Nobody edits another's file. If a workstream believes another's status is wrong, it says so
in its own status under "Conflicts seen", and the controller resolves it in the umbrella and
both rulings files. A fact needed from another workstream is taken from that workstream's
STATUS file, never from memory of a chat, and quoted with the file's version.

## Code ownership, so two chats never edit the same lines

| Area | Owner | Others |
|---|---|---|
| app/cortex_app.py: the run path (api_forecast, api_optimise, calibrated_forecast, caches) | W1 | W2 touches only the stand-mode switch, startup lines and /api/demo endpoints; both pull before every edit and commit small |
| app/wave_cache.py, route_feed.py, catchment.py, water_check.py, preagg.py, backtest.py, config.py cache paths | W1 | nobody |
| app/demo_*.py, connection_builder.py, cortex_dashboard.html, the lead store, queue view, stand mode, laptop build, launcher | W2 | nobody |
| deck/, app/pitch_html.py, imagery, PDF render | W3 | nobody |
| routes/*.md documents | W4, W5, W6, W8, W9, W10 each their own | nobody |
| bt2/ (scripts, logs, CALIBRATION-RECORD-2026.md), search_adjustments.py | W10 | nobody; W1 applies any app/ diff W10 writes up |
| diag_routes_timing.py | W1 | anyone runs it |
| engine demand logic (route_forecast, qsi_*, capture, feed levels) | FROZEN before Routes | nobody (the 22 Sep catchment exception was withdrawn the same day; the radius is a cortex_app display constant, W2 under R6) |

A merge conflict on pull is reported in the STATUS file and to John, never resolved by a
chat on its own.

## Git discipline, every chat

Pull before editing. One commit message file per commit (COMMIT-MSG-<date>-<workstream>-
<topic>.txt), never reused. Commit only your own files plus your STATUS file. Hand John the
block; he runs it; his paste is the record. Never run git against a mounted clone. The
workstation pulls; it never commits.

## The controller's sweep

When John says "sweep", or at least once a day while the chats are active, the controller
reads every Wn-STATUS.md, updates the umbrella's Status block, logs decisions John made
inside any chat, moves cross-workstream facts into the rulings files that need them, and
lists conflicts with a ruling on each. Nothing a chat writes in its status changes the plan
until the sweep has put it in the umbrella.

## Standing rules that bind every chat

The prompt file ../PROMPT-for-Fable-Routes-19Sep2026.txt, verbatim. In particular: measure
before optimising; flag rather than fill; nothing invented; nothing about any competitor;
the accuracy line verbatim and only as ruled; Avia house style; demo-path freeze 10 October.
