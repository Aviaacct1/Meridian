# W2 stand flow: status

Version 3, 21 September 2026. Written by the W2 build chat for the programme controller.
Rewritten each session, never appended. Scope: handover 4, plus the stand capture front end
added by ruling 15. Out of scope and untouched: engine demand logic, and W1's preagg, caches
and pre-warm. Boundary confirmed: W2 owns the narrowed-sweep switch and its defaults, W1 owns
measurement and caches. BRS-EWR:UA is already a default pair in diag_routes_timing.py.

## The sender changed today, and ruling 15's route is closed

John has no admin rights on the aviasolutions.com Microsoft 365 tenant; his IT firm holds them.
Every step ruling 15 named (adding the domain, the mailbox, DKIM, the Entra app registration
and admin consent for Mail.Send) needs that access, and so does the aviasolutions.com fallback
W2 had proposed. Both routes therefore sat behind a queue John does not control, three weeks
before the freeze. John ruled to set up aviationobservatory.com clean instead.

DONE 21 Sep, and verified by Postmark rather than by reading a form:

    aviationobservatory.com
      DKIM          Verified   20260919185744pm._domainkey   TXT
      Return-Path   Verified   pm-bounces  CNAME  pm.mtasv.net
      SPF           not required; Postmark aligns through the Return-Path
      DMARC         v=DMARC1; p=none;   at _dmarc   (published, no reporting address yet)

Postmark account "TheAO", free trial, upgraded when it is proven. The domain was empty before
this work: zero records of every type, so nothing was overwritten. Registrant on the domain is
The Aviation Observatory Limited. Fasthosts warns DNS changes take up to 24 hours; these
propagated in minutes.

WHY THIS IS BETTER THAN GRAPH, not merely quicker: Postmark's SMTP endpoint takes the Server
API token as both username and password, so app/demo_mail.py needs a host, user and password
change and nothing else. Its fail-loudly behaviour and the 58 fixture checks survive. The Graph
rewrite, which was the largest piece of new code in ruling 15, leaves the critical path.

## Scope items

**1. Laptop build. IN PROGRESS.** Ruling 14: a 1TB external NVMe over USB-C on John's core x86
laptop, which is NOT the DevPC, ordered before 28 Sep.
Evidence: DevPC 19 Sep, HEAD 6bbdc0b. AVIA_QSI_BUILD=laptop moves DATA_ROOT only and drops all
nine reference paths; LOCAL_CACHE is independent of the build. Plan A CLOSED: Meridian runs
through the portal on the Huawei MateBook. The MateBook is not the Plan B machine (HarmonyOS
host, Windows 11 Pro ARM64 in a StratoVirt VM). Sabre store circa 91GB (qsi-duckdb-run-rules,
24 Jul); OAG size still unmeasured.
Next action: the two spec blocks, then the load procedure once the drive exists.

**2. Stand mode. IN PROGRESS.** ?stand=1 with AVIA_STAND_MODE as the machine default, query flag
winning, so Suzanna practises in it from her own browser. Season defaults to year-round, request
form surfaced, panel one click away, Expert stays in the nav, and a visible marker names which
build is answering.
Correction to handover 3.4: the 9x narrowing assumes no airline is named; the stand flow names
one at step 1, so the real saving is 3x from the season alone. Evidence: api_optimise _seasons /
_freqs / cands; cortex_dashboard.html lines 314, 730, 1571.
Next action: build, then a DevPC commit block.

**3. Lead flow. IN PROGRESS.** Ruling 15 as amended above: extend 33c902f, migrate the JSONL to
a DuckDB `leads` table under LOCAL_CACHE with section D's stand fields, nightly Excel export to
Egnyte, sender on aviationobservatory.com through POSTMARK, and two emails per visitor.
Next action: the DuckDB store and the migration, which have no external dependency, then the
demo_mail.py credentials change. See the watchpoints below.

**4. Queue view. IN PROGRESS.** /demo/leads exists as an approval page for quota-held requests.
Postmark now also gives delivery, bounce and complaint data, which is what the stand needs to
show a failed pack rather than guess at one.
Next action: check against running / sent / failed, newest first, failure reason visible.

**5. Progressive Optimise display. NOT STARTED.** /api/optimise/start and job_watch already give
the background job and the cancel path. Display change only. After stand mode.

**6. Stand capture front end. NOT STARTED.** Ruling 15: 60 seconds, tablet-friendly, branded,
consent tick, no typing the host can avoid. Route and airline pre-filled from the run on screen;
pick lists, not free text; everything beyond email optional.
Open question: what tablet, and how it reaches the form under Plan B with no venue network.

## Watchpoints

1. POSTMARK IS IN TEST MODE. Sending is restricted until Postmark approves the account by human
   review. John requested approval 21 Sep. Domain warming cannot start until it clears, so this
   is now the longest lead time in the mail chain. If approval has not cleared by 1 Oct, raise it
   with Postmark rather than waiting.
2. demo_mail.py DEFAULTS AVIA_SMTP_HOST TO smtp.office365.com. With Postmark as the sender that
   default is now wrong, and an unset variable would send the server at Microsoft and fail with
   an authentication error naming the wrong supplier. That is the silent-fallback shape this
   project has been caught by four times. FIX FIRST in item 3: make the host required and fail
   loudly naming AVIA_SMTP_HOST.
3. DMARC HAS NO REPORTING ADDRESS. p=none is published, which states the policy and changes no
   delivery, but reports need somewhere to land and aviationobservatory.com cannot receive mail.
   Fasthosts routes inbound mail to a paid add-on, which W2 will not buy. Three ways to switch
   reporting on, for John: buy Fasthosts email on the domain; move the domain's DNS to
   Cloudflare and use Email Routing, which is free and would also solve pack hosting; or sign up
   to Postmark's DMARC Digests. W2 recommends the Cloudflare move but NOT before the laptop
   proof, because moving nameservers now would mean recreating the records just verified.
   Tighten p=none to quarantine only after reports show clean alignment, which is after Routes.
4. TWO EMAILS. W2 still recommends one, with the PDF attached and the pack link inside it. Two
   messages minutes apart double the filter exposure for nothing the visitor notices. If the
   ruling stands, the queue view must show both sends separately.
5. THE PUBLIC PACK URL. An unguessable link is obscurity, not access control. Before a pack with
   a named airline's route economics sits on a public host it needs checking against the Sabre
   compliance position (attribution constant, fares as bands only, no single-route blind
   figures), plus an expiry, a noindex header, and no personal data in the file.
6. TWO CROSS-WORKSTREAM DEPENDENCIES, both undated. The PDF is W3's build item and the email
   cannot attach what does not exist. The pack host is the launched site, W6's decision 7, due
   1 Oct. Both need a date before 10 Oct.
7. MCT MASTER, ruling 16 approved, and it is more urgent than the laptop. Z: is per logon and
   invisible in ssh sessions, and config._resolve_egnyte_root falls back to the nominal Z: path
   when it finds no marker folder. So a server started over ssh resolves MCT_MASTER to a path
   that does not exist, connection_builder.load_mct_data returns an empty dict in silence, and
   every airport cascades to a flat 90 minutes through route_qsi into
   route_forecast.dest_metro_share. If the live workstation portal has ever been started that
   way it has been running without the MCT master. The startup line ruling 16 approves answers
   this on the first restart.

## Other findings

- BOEING 13 OCT is an Atlas meeting: Atlas shown, outputs compared against Boeing CMO, advice
  sought from the CMO lead, with 15 minutes of Meridian. The umbrella timeline row, pre-mortem
  12 and W7 still need rewriting. W2 proposes two Meridian trials, 11-12 Oct and 16 Oct.
- app/DEPLOY_DEMO.md still says to robocopy the app from the OneDrive project folder. Git is the
  source of truth, so W2 corrects it with the laptop build proof.
- Suzanna has used Meridian circa four weeks. Four questions drafted for John to send. Ruling 19
  taken as yes: her own lead file, so her test records stay out of the Routes store.
- .gitignore extended this session with secrets patterns, so a file holding the Postmark token
  cannot be committed by accident. The token itself lives in the environment, which is what
  demo_mail.py reads, and it has never been written to the repo or to any chat.

## Needed from John

1. The two spec blocks: DevPC C:\Avia store inventory with sizes and dates, and the core
   laptop's make, RAM, architecture, free disk and Python.
2. The Postmark Server API token into the workstation environment as AVIA_SMTP_USER and
   AVIA_SMTP_PASS, with AVIA_SMTP_HOST=smtp.postmarkapp.com and AVIA_SMTP_PORT=587, by setx.
3. Which of the three DMARC reporting routes in watchpoint 3.
4. A view on watchpoint 4 (one email rather than two) and watchpoint 5 (the public pack URL).
5. Dates from W3 for the PDF render and from W6 for the website decision.
6. Approval to send Suzanna the four questions.
7. Still open with the controller: item 18, who is at the workstation for the 11-12 Oct trial.
8. The 40-60 route panel, John's choice, not due until early October.

## Dates

Ruling 17 adopted: 1 Oct hardware go/no-go, 8 Oct laptop proof, show machine loaded by 10 Oct,
hard stop 15 Oct, demo-path freeze 10 Oct unchanged. W2's 8 Oct sending-domain decision point is
now a Postmark approval check rather than a domain fallback, since the domain is verified.

## Commits landed

None yet. This file, its version 1 and 2 predecessors and the .gitignore change go in the first
commit block.
