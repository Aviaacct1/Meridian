# W2 stand flow: status

Version 5, 19 September 2026. Written by the W2 build chat for the controller; rewritten each
session, never appended. W2-RULINGS.md v1 read and acted on. Dates corrected from the "21
September" paste. Out of scope and untouched: engine demand logic, and W1's preagg, caches and
pre-warm.

## Answers to the three questions the controller asked

**1. The four questions for Suzanna, ready to send as they stand.**

> Suzanna, four questions before I finish the stand version of the screen. Answer from how you
> have actually been using it, not how you think it should work.
> 1. On a route you have not run before, what do you open first, and in what order after that?
> 2. What have you had to look up, or work out again, more than once?
> 3. What would you not put in front of a visitor, and why?
> 4. What did you expect to find and could not?
> One line each is plenty. Anything that annoyed you is useful.

Ask about speed separately and only after her next session: W1 step 1 (1012c29) took Run from
42s to 9s and Optimise from 196s to 35s, so anything she says about speed before that is out of
date, and asking now would bank a stale complaint.

**2. Can aviationobservatory.com be verified on the Avia Microsoft 365 tenant, and what does
John click? No, and he clicks nothing.** Verifying a domain needs Global Administrator on that
tenant. John holds an ordinary user account; his IT firm holds the admin rights. The same is
true of the mailbox, the DKIM toggle, and the Entra app registration with admin consent that
Graph sending needs, so every step of ruling 15's sender route ran through a queue he does not
control, three weeks before the freeze. The aviasolutions.com fallback failed for the same
reason. John ruled to set the domain up clean instead, and it is DONE, verified by Postmark:

    DKIM          Verified   20260919185744pm._domainkey   TXT
    Return-Path   Verified   pm-bounces  CNAME  pm.mtasv.net
    SPF           not required; Postmark aligns through the Return-Path
    DMARC         v=DMARC1; p=none;  at _dmarc, no reporting address yet

The domain held zero records of any type beforehand, so nothing was overwritten. Postmark's SMTP
endpoint takes the Server API token as both username and password, so demo_mail.py needs a
credentials change rather than the Graph rewrite, which was the largest piece of new code in
ruling 15. Its fail-loudly behaviour and its 58 fixture checks survive. Workstation environment
set and confirmed: host smtp.postmarkapp.com, port 587, both token variables 36 characters. No
token is in the repo or in any transcript. If the controller still wants M365 mailboxes for the
Observatory later, that is a separate request to the IT firm and it is not on the Routes path.

**3. Stand capture front end: scope, and the day it is demonstrable.**
One page in stand mode, reached from the run on screen, finished in 60 seconds on a tablet held
by the host. Name, company, role, email, phone, plus route and airline pre-filled from the run
just shown, and the run signature carried invisibly so the pack is provably the forecast the
visitor watched. Airline and airport by pick list, never free text. Everything past email is
optional and the form says so, because a host who must complete fields will stop using it by
the second morning. Consent tick and privacy line on the page, Observatory branding, big touch
targets, one screen with no scrolling, and a visible confirmation naming the person and the
route so the host knows it landed. It writes to the `leads` table, so item 3 lands first.
DEMONSTRABLE 2 OCTOBER on the portal, which leaves it a week before the freeze and a fortnight
before the trial. OPEN, and it needs an answer before the 11-12 October trial: which tablet, and
how it reaches the form under Plan B, where the laptop serves only itself and there is no venue
network.

## Scope items

**1. Laptop build. IN PROGRESS.** Ruling 14: 1TB external NVMe over USB-C on John's core x86
laptop, not the DevPC, ordered before 28 Sep. Plan A CLOSED: Meridian runs through the portal on
the MateBook. The MateBook is not the Plan B machine (HarmonyOS host, Windows 11 Pro ARM64 in a
StratoVirt VM). AVIA_QSI_BUILD=laptop moves DATA_ROOT only and drops all nine reference paths;
LOCAL_CACHE is independent of it. Sabre store circa 91GB (qsi-duckdb-run-rules, 24 Jul); OAG
still unmeasured. Next: the two spec blocks, then the load procedure.

**2. Stand mode. IN PROGRESS.** ?stand=1 with AVIA_STAND_MODE as the machine default, query flag
winning, so Suzanna practises in it from her own browser. Season defaults to year-round, request
form surfaced, panel one click away, Expert stays in the nav, and a visible marker names which
build is answering. Correction to handover 3.4: the 9x narrowing assumes no airline is named;
the stand flow names one at step 1, so the real saving is 3x from the season alone. Evidence:
api_optimise _seasons / _freqs / cands; cortex_dashboard.html lines 314, 730, 1571. W1 step 1
has already met the speed targets warm, so this switch is now about what the host sees rather
than about speed. Next: build, then a commit block.

**3. Lead flow. IN PROGRESS.** Ruling 15 as amended: extend 33c902f, migrate the JSONL to a
DuckDB `leads` table under LOCAL_CACHE with section D's stand fields, nightly Excel export to
Egnyte, sender through Postmark, two emails per visitor, the hosted pack linking back to the
site's main pages. Next: the store and the migration, which have no external dependency, then
demo_mail.py.

**4. Queue view. IN PROGRESS.** /demo/leads exists as an approval page for quota-held requests.
Postmark now also gives delivery, bounce and complaint data, which is what the stand needs to
show a failed pack rather than guess at one. Next: check against running / sent / failed,
newest first, failure reason visible.

**5. Progressive Optimise display. NOT STARTED.** Display change only; the background job and
cancel path already exist. After stand mode.

**6. Stand capture front end. NOT STARTED.** Scoped above. Demonstrable 2 Oct.

**7. Pre-mortem 15: a city name the workstation cannot resolve. NOT STARTED.** Newly W2's per
W2-RULINGS.md. Confirm which dashboard entry paths need the GeoNames dump, then either install
it on the workstation or make the failure a visible refusal naming what it could not resolve,
never a silent empty result. Test on the 11-12 October trial. Next: trace the entry paths.

## Done this session

**Ruling 16, the MCT master, BUILT AND TESTED; it speaks at the next restart.**
connection_builder.mct_report() resolves through config exactly as the live callers do and
returns path, exists, rows and error. cortex_app's startup event prints "MCT master: N rows from
<path>", or names the reason it did not load and states the consequence, and stand mode raises
rather than start, so the stand never demonstrates a silent difference from the live tool.
app/test_mct_report.py holds missing, unusable and loaded apart, because they are three
different faults: 14 checks, 0 failed.
THE QUESTION IT ANSWERS: Z: is per logon and invisible in ssh sessions, and
config._resolve_egnyte_root falls back to the nominal Z: path when it finds no marker folder, so
a server started over ssh resolves MCT_MASTER to a path that does not exist, load_mct_data
returns an empty dict in silence, and every airport cascades to a flat 90 minutes through
route_qsi into route_forecast.dest_metro_share, which moves the forecast on any multi-airport
metro. Whether the live portal has ever been started that way is not knowable from a code read.
The next restart answers it, and it is the same restart that picks up the Postmark variables.
VERIFICATION AND ITS LIMIT: both modules compile and the 14 checks pass against a workbook
written for the test. The four inline startup lines cannot run without the server's own
dependencies, so they are proven by compile and by reading. The first restart is their real test.

**The sender.** Set up and verified, as recorded under question 2 above.

## Watchpoints

1. POSTMARK IS IN TEST MODE. Sending is restricted until Postmark approves the account by human
   review; John requested approval 19 Sep. Domain warming cannot start until it clears, so this
   is the longest lead time in the mail chain. Not cleared by 1 Oct, chase it.
2. demo_mail.py DEFAULTS AVIA_SMTP_HOST TO smtp.office365.com. With Postmark as the sender an
   unset variable would send the server at Microsoft and fail naming the wrong supplier. The
   same silent-fallback shape. First fix in item 3: the host becomes required and fails loudly.
3. DMARC HAS NO REPORTING ADDRESS. p=none is published and changes no delivery, but reports need
   somewhere to land and the domain cannot receive mail. Fasthosts routes inbound to a paid
   add-on, which W2 did not buy. Three routes for John: buy Fasthosts email on the domain; move
   the domain's DNS to Cloudflare and use Email Routing, free, which would also answer the pack
   hosting question; or Postmark's DMARC Digests. W2 favours Cloudflare, but not before the
   laptop proof, because moving nameservers now means recreating records just verified. Tighten
   past p=none only after reports show clean alignment, which is after Routes.
4. TWO EMAILS. W2 still recommends one, PDF attached and the pack link inside it. If the ruling
   stands, the queue view must show both sends separately or a half-delivered visitor reads as
   delivered.
5. THE PUBLIC PACK URL. An unguessable link is obscurity, not access control. Before a pack with
   a named airline's route economics sits on a public host it needs checking against the Sabre
   position (attribution constant, fares as bands only, no single-route blind figures), plus an
   expiry, a noindex header, and no personal data in the file.
6. TWO CROSS-WORKSTREAM DEPENDENCIES, both undated. The PDF is W3's and the email cannot attach
   what does not exist. The pack host is W6's decision 7, due 1 Oct. Both need a date before
   10 Oct.
7. RULING 18, THE UNMANNED WORKSTATION. Taken and understood: remote desktop over Tailscale,
   sign in, run both launchers, disconnect, never sign out, with Stop-Process first because
   Meridian-run.bat re-warms a running server rather than replacing it. W2 will write it in
   those words into the runbook and hand W4 the same words for the host manual, and rehearse one
   deliberate restart in the 11-12 October trial. W2 agrees the scheduled-task answer is better
   and will scope it for 8 October, including the check that the Cloudflare tunnel runs as a
   service. Worth stating plainly: an unmanned box makes the MCT startup line above the only
   thing that will ever tell anyone the master did not load.

## Needed from John

1. The two spec blocks: DevPC C:\Avia store inventory with sizes and dates, and the core
   laptop's make, RAM, architecture, free disk and Python.
2. Which of the three DMARC reporting routes in watchpoint 3.
3. A view on watchpoint 4 (one email rather than two) and watchpoint 5 (the public pack URL).
4. Dates from W3 for the PDF render and from W6 for the website decision.
5. Approval to send Suzanna the four questions above.
6. Which tablet for the capture front end, and how it reaches the form under Plan B.
7. The 40-60 route panel, John's choice, not due until early October. The panel page reads a
   list from a file and says plainly that it is empty until one exists.

## Dates

Ruling 17: 1 Oct hardware go/no-go, 8 Oct laptop proof, show machine loaded by 10 Oct, hard stop
15 Oct, freeze 10 Oct. W2 adds: capture front end demonstrable 2 Oct; scheduled-task restart
scoped 8 Oct; Postmark approval checked 1 Oct.

## Commits landed

None yet. The first block carries routes/W2-STATUS.md, the .gitignore secrets patterns, and the
ruling 16 change: app/connection_builder.py, app/cortex_app.py and app/test_mct_report.py. Hash
recorded here when John pastes it.
