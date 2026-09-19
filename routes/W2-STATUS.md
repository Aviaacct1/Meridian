# W2 stand flow: status

Version 2, 21 September 2026. Written by the W2 build chat for the programme controller.
Rewritten each session, never appended. Scope: handover 4, plus the stand capture front end
added by ruling 15. Out of scope and untouched: engine demand logic, and W1's preagg, caches
and pre-warm. Boundary confirmed 21 Sep: W2 owns the narrowed-sweep switch and its defaults,
W1 owns measurement and caches. BRS-EWR:UA is already a default pair in diag_routes_timing.py,
so W2 asks for no second probe.

## Scope items

**1. Laptop build. IN PROGRESS.** Ruling 14: a 1TB external NVMe over USB-C on John's core
x86 laptop, not the MateBook, ordered before 28 Sep.
Evidence: DevPC 19 Sep, HEAD 6bbdc0b. AVIA_QSI_BUILD=laptop moves DATA_ROOT only and drops all
nine reference paths; LOCAL_CACHE is independent of the build, so a machine with
AVIA_LOCAL_CACHE unset finds no stores. Plan A CLOSED: Meridian runs through the portal on the
MateBook. The MateBook is not the Plan B machine (HarmonyOS host, Windows 11 Pro ARM64 in a
StratoVirt VM, 19 Sep). Sabre store circa 91GB (qsi-duckdb-run-rules, 24 Jul; config.py
header); OAG size still unmeasured.
Next action: John runs the two spec blocks; W2 issues the load procedure once the drive exists.

**2. Stand mode. IN PROGRESS.** ?stand=1 with AVIA_STAND_MODE as the machine default, query
flag winning, so Suzanna practises in it from her own browser. Season defaults to year-round,
request form surfaced, panel one click away, Expert stays in the nav, and a visible marker
names which build is answering.
Correction to handover 3.4: the 9x narrowing assumes no airline is named; the stand flow names
one at step 1, so the real saving is 3x from the season alone, and 9x only for a walk-up naming
none. Run is unaffected, it already defaults to annual. Evidence: api_optimise _seasons /
_freqs / cands; cortex_dashboard.html lines 314, 730, 1571.
Next action: build, then a DevPC commit block.

**3. Lead flow. IN PROGRESS.** Ruling 15: extend the 16 August build (33c902f), migrate the
JSONL to a DuckDB `leads` table under LOCAL_CACHE with section D's stand fields, nightly Excel
export to Egnyte, sender on aviationobservatory.com through Graph from a named mailbox, and two
emails per visitor.
Honest scope note: what survives is the quota logic, the pack builder and the 58 fixture checks.
The store and the transport both change, so this is a rebuild of two of the three layers.
Next action: build the DuckDB store and the migration first, because it is the part with no
external dependency. See the five watchpoints below before the mail work starts.

**4. Queue view. IN PROGRESS.** /demo/leads exists as an approval page for quota-held requests.
Next action: check it against the stand requirement (running / sent / failed, newest first,
failure reason visible), then extend rather than build new.

**5. Progressive Optimise display. NOT STARTED.** /api/optimise/start and job_watch already
give the background job and the cancel path (18-19 Aug), so this is a display change.
Next action: after stand mode.

**6. Stand capture front end. NOT STARTED.** New, ruling 15: 60 seconds, tablet-friendly,
branded, consent tick, no typing the host can avoid. Route and airline pre-filled from the run
on screen; airline and airport by pick list, not free text; everything beyond email optional.
Open question for John: what tablet, and how it reaches the form under Plan B, where there is
no venue network and the laptop is serving only itself.
Next action: scope after item 3's store exists, since the form writes to it.

## Watchpoints on ruling 15, before the mail work starts

1. COLD SENDING DOMAIN. aviationobservatory.com has no sending history. A brand-new domain
   mailing airline and airport corporate filters at volume across three days is the textbook
   way to land in junk, and the 30-minute pack is one of the three sub-messages. Set the domain
   up this week rather than in October, send real mail from it from the day it exists, and hold
   aviasolutions.com, which already has SPF and DKIM right and a history, as the fallback.
   W2 recommends a decision point on 8 Oct: if the new domain is not demonstrably delivering to
   external mailboxes by then, Routes sends from aviasolutions.com and the branding waits.
   Pre-mortem 6 tests the sender on 13 Oct, which is too late to discover this.
2. GRAPH NEEDS TENANT ADMIN. Moving off SMTP AUTH is the right call and it is a new dependency:
   app registration, Mail.Send, admin consent, and a secret in the gitignored secrets file per
   the tool standard. If IT is involved, that is days. Start it before the build needs it.
3. TWO EMAILS. W2 recommends one. Two messages minutes apart to someone who has just met you
   doubles the filter exposure and the failure surface for no gain the visitor notices; the PDF
   attaches and the pack link sits inside the same message. If the ruling stands, the queue
   view must show both sends separately or a half-delivered visitor looks delivered.
4. THE PUBLIC PACK URL. An unguessable link is obscurity, not access control: links are
   forwarded, scanned and logged. Before a pack containing a named airline's route economics
   sits on a public host, it needs checking against the Sabre compliance position (attribution
   constant, fares as bands only, no single-route blind figures), plus an expiry, a noindex
   header, and no personal data in the file. W2 will not publish packs publicly until that
   check is recorded.
5. TWO CROSS-WORKSTREAM DEPENDENCIES, both currently undated. The PDF is W3's build item, and
   the email cannot attach what does not exist. The pack host is the launched site, which is
   W6's decision 7, due 1 Oct; if the answer is a landing page, packs have nowhere to live, and
   nobody has yet designed how a pack gets from the workstation to a public host. Both need a
   date before 10 Oct or the two-email design fails on the stand rather than in testing.

## Other findings

- MCT MASTER, ruling 16 approved, and it is more urgent than the laptop. Z: is per logon and
  invisible in ssh sessions (handover 23 Aug, section 5), and config._resolve_egnyte_root falls
  back to the nominal Z: path when no marker folder is found. So any server started over ssh
  resolves MCT_MASTER to a path that does not exist, load_mct_data returns an empty dict in
  silence, and every airport cascades to a flat 90 minutes through route_qsi into
  route_forecast.dest_metro_share. If the live workstation portal has ever been started that
  way, it has been running without the MCT master and nothing said so. The startup line
  ruling 16 approves answers this on the first restart.
- BOEING 13 OCT is an Atlas meeting with 15 minutes of Meridian, so the umbrella timeline row,
  pre-mortem 12 and W7 still need rewriting. Meridian trials proposed 11-12 Oct and 16 Oct.
- app/DEPLOY_DEMO.md still says to robocopy the app from the OneDrive project folder. Git is
  the source of truth, so W2 corrects it with the laptop build proof.
- Suzanna has used Meridian circa four weeks. Four questions drafted for John to send; her
  answers shape stand mode's defaults and the panel. Ruling 19 taken as yes: she gets her own
  lead file so her test records stay out of the Routes store.

## Needed from John

1. The two spec blocks: DevPC C:\Avia store inventory with sizes and dates, and the core
   laptop's make, RAM, architecture, free disk and Python.
2. The aviationobservatory.com domain set up and sending this week, not in October, and the
   Graph app registration started.
3. A view on watchpoint 3 (one email rather than two) and watchpoint 4 (the public pack URL
   against the Sabre position).
4. Dates from W3 for the PDF render and from W6 for the website decision, or the two-email
   design has no delivery path.
5. Approval to send Suzanna the four questions.
6. Still open with the controller: item 18, who is at the workstation for the 11-12 Oct trial.
7. The 40-60 route panel, John's choice, not due until early October. The panel page reads a
   list from a file and says plainly that it is empty until one exists.

## Dates

Ruling 17 adopted: 1 Oct hardware go/no-go, 8 Oct laptop proof, show machine loaded by 10 Oct,
hard stop 15 Oct, demo-path freeze 10 Oct unchanged. W2 adds one: 8 Oct decision on the sending
domain, per watchpoint 1.

## Commits landed

None yet from W2. Version 1 of this file and this version go in the first commit block.
