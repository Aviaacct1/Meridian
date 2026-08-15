# Kickoff: 16 August 2026

Paste everything below into the new chat as the first message.

---

FIRST, THE MOUNT, BEFORE YOU READ ANYTHING ELSE

Cowork attaches the PROJECT folder automatically, which is
`C:\Users\Carte\OneDrive\Documents\Claude\Projects\Avia QSI Tool`. THAT IS NOT THE REPO.
It holds old handovers and a STALE `app\` copy. Do not read it and never write to it.

THE REPO IS `C:\AviaDev`. ASK FOR IT YOURSELF with the folder-access tool before you read
a line of code.

`E:\Avia` IS ON THE WORKSTATION AND COWORK CANNOT MOUNT IT (it maps D:\Avia; an elevated
window can lose the mapping, D:\Avia is the fallback spelling). Anything under E: is read
by a command John runs; ask for the one command that gets what you need.

THE TWO MACHINES, and do not get this wrong:

- Dev PC, where editing happens: `C:\AviaDev`
- Workstation, where running happens: `C:\src\meridian`, data root `E:\Avia`, portal on
  port 8010, launched by `Meridian-run.bat` (which sets the shipped environment)

Code moves ONLY by git push on the Dev PC then git pull on the Workstation. LABEL EVERY
COMMAND BLOCK WITH THE MACHINE (DEVPC / WORKSTATION REMOTE / ACTUAL WORKSTATION) and put
a cd in front of every command.

NEVER RUN GIT, not even a read-only `git status`. It strands `.git\index.lock` on the
mount. Hand John commit messages as files; he runs every git command himself, and checks
`git status --short` before composing any `git add`, naming only the files you wrote.

PowerShell: `$env:NAME = "value"`, never `set`. One-line commands, no backtick
continuations, no nested quoting inside `python -c`.

DO NOT USE THE MULTIPLE-CHOICE QUESTION TOOL. It does not render for John. Put questions
in the message body as numbered plain text, with your recommendation named.

THE PUBLISHED CLAIMS STAY. THE LEVEL/TIMING SPLIT OF 15 AUGUST STAYS (V1 carries the
forecast level, V2 QSI carries the timing; rollback is AVIA_FEED_LEVEL=qsi): do not
re-litigate k without new measurement. Verify, do not assert. House style throughout.

READ FIRST: `C:\AviaDev\HANDOVER-16Aug2026.md`, then `bt2/bt2_experiments.log` from
K-SWEEP-RESULT (15 August) to the end. The auto-memory index also carries
meridian-15aug-review-and-fixes as READ FIRST on current state.

---

WHERE THINGS STAND, 15 August late evening

The 15 August review verdict (show at Routes, beta, November launch) is accepted and the
whole R3-R10 provenance batch, the easy-view and chart batch, Route Watch, the refresh
pickup core and the launcher are pushed and verified on the workstation. The k sweep ran
paired and clean; V2 was parked as the level by its own pre-registered rule and V1
carries the forecast numbers, which puts the product on the same machine as its accuracy
evidence. Sixteen of sixteen deck cases run with warnings empty.

ONE THING IS OWED BEFORE ANY BUILDING: the acceptance run, ten minutes, exact settings
in the handover (CI, A359, 306 seats, 2028, curfew, frequency blank, connectivity floor
OFF via Expert -> Show calibration constants). Pass mark 4-5x weekly, circa 110-135k
two-way. Ask John to run it and paste the result line before starting Job 1.

TODAY'S TWO JOBS, in order:

JOB 1: THE WATCH PAGE VISUAL LAYER. Charts in the Observatory grammar (brand guidelines
v1.1: brass observed line, dashed comparator, direct labels, registration ticks,
provenance rail): daily scheduled seats this year against last from the oag store's
days_of_op across the two snapshot labels, and monthly traffic against the same month
last year from T-100 for US airports (config.T100_DUCKDB, `seg` table only, scheduled
class; airport_profile.read_t100's docstring holds the traps). New /api/watch/series
endpoint plus inline SVG in cortex_watch.html; the dashboard's departure-curve code is
the house pattern to copy. Add the store-freshness line reading refresh_status.json.

JOB 2: CLOUDFLARE ACCESS FOR THE SIX TESTERS. Password first (AVIA_PASSWORD in the
workstation environment, never the repo), then a named cloudflared tunnel to
localhost:8010 installed as a Windows service, then Cloudflare Access allowing the
tester emails only. ASK JOHN FIRST, numbered plain text: (1) which hostname on which
Cloudflare domain, (2) the tester email list, (3) confirm ANTHROPIC_API_KEY is set on
the workstation (setx; new key named "workstation") so the briefing works.

THEN: the week list in the handover, in its order. End the session by updating the
handover's week list with what moved.

Avia Solutions Limited. All rights reserved.
