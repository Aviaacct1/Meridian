# W2 stand flow: status

Version 14, 22 September 2026. Written by the W2 build chat for the controller; rewritten each
session, never appended. routes/README.md v1 read and followed: facts about other workstreams
are taken from their STATUS files and quoted with the version, never from memory of a chat.
W2-RULINGS.md v1 read and acted on. Restructured this version at the controller's request: live
state and asks on the first screen, history below. Out of scope and untouched: engine demand
logic, and W1's preagg, caches and pre-warm.

## Live state

Nothing blocks W2's own build. The mail half waits on Postmark; everything else is W2's to do.

| Item | State | Next |
|---|---|---|
| 1 Laptop build | Plan A closed, Plan B waiting on two spec blocks from John | Load procedure once the SSD and the spec arrive |
| 2 Stand mode | Not built | Next session, then a commit block |
| 3 Lead flow | Store built and tested, app not rewired | Rewire cortex_app, migrate the JSONL, nightly Excel export |
| 4 Queue view | Exists as an approval page | Running / sent / failed, newest first, reason visible |
| 5 Progressive Optimise | Proposed for deferral to after Routes | Controller's ruling |
| 6 Stand capture layer | Store built for all four record types, 47 checks | Three capture buttons after the rewire |
| 7 Pre-mortem 15, city names | Not started | Trace the dashboard entry paths |

Delivery is proven end to end: one real message through the Postmark API on 21 Sep, MessageID
8283ccb0-72f6-42c2-ab93-cd1da557c215, John confirmed arrival. The Observatory domain's own
deliverability is NOT proven and cannot be until the account clears review, because a pending
account restricts the recipient to the From domain.

## Owed to the controller today

A commit block is with John and not yet run: the catchment distance report
(COMMIT-MSG-22Sep2026-w2-catchment-distance.txt). Everything else W2 has produced is on main at
ef6de65.

## Needed from John

1. The two spec blocks: DevPC C:\Avia store inventory with sizes and dates, and the core laptop's
   make, RAM, architecture, free disk and Python. These gate the 8 Oct laptop proof.
2. Approval to send Suzanna the four questions (below). They shape what stand mode defaults to.
3. A view on watchpoint 4, one email rather than two, and watchpoint 5, the public pack URL.
4. Which of the three DMARC reporting routes in watchpoint 3.
5. Which tablet for the capture front end, and how it reaches the form under Plan B.
6. The 40-60 route panel, early October.

## Waiting on, in the order it bites

1. POSTMARK APPROVAL. Account in review since 19 Sep. Gates the email half of item 3 and all
   domain warming. Chase on 1 October.
2. The two spec blocks above.
3. Not blocking: the DMARC reporting route, which tablet, and the route panel.

The next restart of the portal, whenever it happens, does three jobs at once: it makes the MCT
line speak for the first time, it makes the new catchment distance line speak, and it picks up
the Postmark variables. Nothing needs restarting for its own sake while the account is in review.

## The catchment finding, 22 September, for W10

Found while tracing Jol item 33, Birmingham inside a London catchment. It is reported here
because it bears on W10's calibration record, not because W2 has changed any engine behaviour.

The catchment allocates population to airports by road time where the friction raster is present
and by great circle where it is not, and it chose between the two in silence. Proven on
donatello: C:\Avia absent, FRICTION_PATH resolving to C:\Avia\friction_2019.tif which does not
exist, drive engine None, and the raster present the whole time at
E:\Avia\2020_motorized_friction_surface.geotiff. Every catchment run has been great circle. A
second layer sat under it: DriveTimes.available() tested only that the file existed, never that
rasterio, numpy and scikit-image were installed, so a machine without the read libraries would
report ready and then return great-circle times for every route.

Fixed as a REPORT, with no behaviour change. config.py resolves FRICTION_RASTER and publishes it
in ALL_PATHS; route_forecast.friction_report() opens the raster for its band count and names each
failure separately; drive_times.available() now means usable; cortex_app states on every start
whether the catchment is measuring in road time or straight lines. Road times stay off behind
AVIA_DRIVE_TIMES, defaulting off, because switching them on moves every forecast and that is
W10's call, not a variable set the week before Routes. Not a silent default-off switch: the
server says which setting is in force every time it starts. test_friction_report.py, 28 checks,
0 failed; MCT 14, lead store 47, demo flow 89, all unchanged.

THE LINE W10 NEEDS. The friction raster is an undeclared environment dependency of the same class
as the airportsdata version already tracked in CALIBRATION-RECORD-2026.md section 2. The engine's
catchment measurement changed when C:\Avia stopped existing, with no code change and no log
entry, so runs from either side of that moment are not one comparable series. It belongs in the
environment rows and in the yearly republication in section 7. It does not move the claim
figures: no file in the BT2 training chain (bt2_claimset, bt2_capture, bt2_base, bt2_build_v13,
bt2_gbm) references the catchment or drive times, which agrees with the controller's own finding
in section 4. It does move the live product: the market built over the competing airports, the
catchment the user sees, and any run on the QSI engine.

BIRMINGHAM ITSELF STAYS for Routes, on John's ruling of 22 September that he would rather live
with the oddity than change catchment for every airport. His preferred route is a per-airport
catchment override, the same mechanism an airport would use to supply its own measured
catchment, set at the start of a client's use rather than after they have a baseline to compare
against. W2 notes that app/airport_capture.py already holds the capture half of that design
(AIRPORT_CAPTURE, one entry, SJC 0.32, sourced) and that the catchment half does not exist.
Design and ruling belong to W10.

## The four questions for Suzanna, ready to send as they stand

> Suzanna, four questions before I finish the stand version of the screen. Answer from how you
> have actually been using it, not how you think it should work.
> 1. On a route you have not run before, what do you open first, and in what order after that?
> 2. What have you had to look up, or work out again, more than once?
> 3. What would you not put in front of a visitor, and why?
> 4. What did you expect to find and could not?
> One line each is plenty. Anything that annoyed you is useful.

Ask about speed separately and only after her next session: W1 step 1 (1012c29) took Run from 42s
to 9s and Optimise from 196s to 35s, so anything she says about speed before that is out of date.

## Dates

Ruling 17: 1 Oct hardware go/no-go, 8 Oct laptop proof, show machine loaded by 10 Oct, freeze
10 Oct, hard stop 15 Oct. W2 adds: capture front end demonstrable 2 Oct; pack URL rule to W6 by
3 Oct; scheduled-task restart scoped 8 Oct; Postmark approval checked 1 Oct.

## Commits landed

- **2cab1b2**, 19 Sep. Ruling 16's MCT reporter, the startup line and the stand-mode refusal; the
  .gitignore secrets patterns.
- **3406f0a**, 21 Sep. The API transport, after SMTP reported success for three messages Postmark
  never received. 89 checks, 0 failed.
- **ef6de65**, 21 Sep. app/lead_store.py and app/test_lead_store.py, the store for all four record
  types. 47 checks, 0 failed against duckdb 1.5.5.
- OWED, block with John: the catchment distance report. 28 new checks, 0 failed.

---

Everything below is the record behind the state above. The controller need not read it to act.

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

**5. Progressive Optimise display. PROPOSED FOR DEFERRAL to after Routes; see the
proposal above.** Display change only; the background job and
cancel path already exist. After stand mode.

**6. Stand capture layer. IN PROGRESS. The store is built and tested.**
app/lead_store.py: one DuckDB table for all four record types, an append-only lead_events
log beside it, and lead_files for card photographs, voice notes and packs. app/
test_lead_store.py holds the seven properties that are load-bearing: 47 checks, 0 failed,
run against duckdb 1.5.5, the version donatello pins. The other suites are unaffected:
test_demo_flow.py 89, test_mct_report.py 14, both 0 failed.
WHAT THE DESIGN COMMITS TO, and each is a check rather than an intention: the record exists
from the moment the host captures it and does not depend on any pack; it stays editable
afterwards, because the useful detail arrives once the visitor has gone; notes append rather
than replace; the event log is append-only, so what happened stays answerable after a record
is corrected; the PROVIDER is the authority on whether a pack went, through
provider_message_id, provider_status and reconcile(); John's 16 August quota ruling is carried
across unchanged, first pack free, the rest held, a failed send still free; and migrate_jsonl
counts unreadable lines rather than dropping them, because a migration that loses records in
silence is worse than one that refuses.
NOT YET DONE: cortex_app is NOT rewired to it. The JSONL store is still what the running app
uses, deliberately, so there is a working system at every point before the freeze. Rewiring,
the nightly Excel export and the three capture buttons are next, in that order.

**6a. Superseded note, scope widened by John 21 Sep.** Four record types,
three buttons, list view, local-first, editable after the moment. See the proposal above.
Next: the DuckDB leads table, which all four record types sit on, starts now.

**7. Pre-mortem 15: a city name the workstation cannot resolve. NOT STARTED.** Newly W2's per
W2-RULINGS.md. Confirm which dashboard entry paths need the GeoNames dump, then either install
it on the workstation or make the failure a visible refusal naming what it could not resolve,
never a silent empty result. Test on the 11-12 October trial. Next: trace the entry paths.

## Done 21 September

**THE FIRST END-TO-END SEND IS OWED, AND IT WOULD HAVE FAILED.** The controller asked for
one real pack email through demo_mail.py. Reading it before running it found that it cannot
send under Postmark at all: SmtpTransport set `self.sender = self.cfg["user"]` and send_pack
puts that in the From header. Under M365 the username IS the mailbox so the two coincided;
under Postmark the username is a 36-character Server API token, and a token in a From header
is not a deliverable message.

WHY 58 PASSING CHECKS MISSED IT, which is the part worth carrying forward: the mail fixture
injects a FakeTransport that carries its own `sender` attribute, so the suite never reached
the one line that resolves the real sender. The first live send would have been the test.

FIXED in app/demo_mail.py: AVIA_SMTP_FROM names the sending address, falling back to
AVIA_SMTP_USER only when that looks like an address, so M365 behaviour is unchanged.
AVIA_SMTP_HOST is now required with no default, which closes watchpoint 2 in the same edit:
it defaulted to smtp.office365.com and an unset variable would have sent the server at the
wrong supplier and failed naming Microsoft. app/test_demo_flow.py gains nine checks covering
both, including that a token never reaches a From header: 67 checks, 0 failed, run here.

**CORRECTION TO VERSION 9, WHICH RECORDED A FALSE PASS.** Version 9 of this file said the
first end-to-end send was PROVEN on the evidence of the script printing SENT. It was not.
Nothing had been delivered, and nothing had even reached Postmark. The claim is withdrawn and
replaced by what follows. W2 put that in the record and the controller could have relied on it.

**SMTP REPORTED SUCCESS THREE TIMES FOR MESSAGES POSTMARK NEVER RECEIVED.** The sequence,
because the conclusion matters more than the fault:

- Three sends from donatello printed SENT. smtplib raised nothing.
- Postmark's own API, queried with the same token, returned `TotalCount 0`. No messages, on
  any stream, ever.
- The token was confirmed to match the server's own (John compared it; neither value was
  written down). The API authenticated with it. So the credential was never the problem.
- The SMTP banner on port 587 from donatello was read directly and is genuinely Postmark
  (`p-pm-outboundg02c-aws-euwest1c.smtpservice.postmarkapp.com`), so nothing was intercepting.
- The identical message posted to Postmark's HTTP API returned, in one call:
  `ErrorCode 412: While your account is pending approval, all recipient addresses must share
  the same domain as the 'From' address. The domain of the 'From' address is
  'aviationobservatory.com', but you are attempting to send email to the following domain(s):
  'aviasolutions.com'.`

So Postmark's SMTP endpoint accepted, acknowledged and discarded three messages that its own
policy forbade, while its API refused the same message and said why. Three hours went into a
fault the API would have named immediately.

**TRANSPORT CHANGED TO THE API, on that evidence rather than on preference.** app/demo_mail.py
gains ApiTransport and a selector; the API is the default, SMTP stays available behind
AVIA_MAIL_TRANSPORT=smtp. Both build the same EmailMessage, so the two cannot drift. A refusal
now raises carrying Postmark's own wording, and acceptance returns a MessageID, which is also
exactly what the queue view needs to show a pack as accepted by the provider rather than merely
handed to a socket. app/test_demo_flow.py locks the 412 case as a regression: 67 checks became
89, 0 failed.

**app/send_first_pack.py no longer claims what it cannot show.** It reported SENT because
nothing raised, and this file repeated it. It now refuses to call a send successful without a
provider identifier, and says so plainly when it has none.

**DELIVERY IS NOW PROVEN, 21 September 14:01Z.** Sent through the API from
john.carter@aviasolutions.com to the same address, since while the account is pending approval
the recipient domain must match the From domain. Postmark returned
MessageID 8283ccb0-72f6-42c2-ab93-cd1da557c215 and John confirmed arrival in his inbox, headers
showing the message as sent. WHAT IS STILL NOT PROVEN: the Observatory domain's own
deliverability, because that test had to send as aviasolutions.com without our DKIM. That waits
on approval, which Postmark quotes at 24 hours with weekend requests answered on the Monday.

**The aviasolutions.com signature has now earned its keep twice** and still stays. While the
account is pending, it is the only From and the only recipient that any test can use. It goes
once approval lands, not before.

**Four machine and account faults surfaced getting there, and they are the carry-forward.**
They cost most of the day and none of them was a code fault.
1. Blocks labelled "Workstation Actual" were running on the DEV PC. whoami returned
   desktop-3r7oqvj\carte. The Dev PC carries a second clone at C:\src\meridian alongside
   C:\AviaDev, so the path looks identical on both machines and the prompt does not
   distinguish them. The Avia tool standard's first two rules exist to stop exactly this.
   What that second clone is for, and whether it should exist, is John's call; W2 has touched
   nothing.
2. A pull's summary line was read as a commit's. "4 files changed, 164 insertions(+)" was
   git pull reporting the controller's ce0e3a6, and W2 took it for John's commit, so W2
   believed work was pushed that was still sitting uncommitted. Every W2 block now ends with
   git log --oneline -1, which names the commit rather than only its hash.
3. setx writes to the SETTING account's User scope. HOST, PORT, USER and PASS were set on
   donatello under aviaremote1; FROM was set on the Dev PC under carte, so donatello never had
   it. All five are now at MACHINE scope on donatello, which is what an unmanned box needs: a
   scheduled task at boot runs as neither account and would see neither User hive. Ruling 18's
   8 October scheduled-task work can now assume they are there.
4. A Machine-scope write does not reach a shell already running, the same trap as setx one
   level up. The reload loop is in the block for that reason.

**app/send_first_pack.py, written and now run.** It sends one real message through
demo_mail.send_pack, prints the resolved host, from and credential LENGTH only, warns if the
sender and the credential are identical, and names the three things to check in Postmark
afterwards. Its attachment is a plainly labelled transport test, not a forecast pack, because
a pack with invented numbers should not leave the building even once; the pack rides the same
transport through /api/demo/request once the lead store exists. Verified here only to the
extent of compiling and refusing cleanly with no configuration. THE SEND ITSELF IS OWED and
needs, in order: the DevPC commit and push, a workstation pull, setx AVIA_SMTP_FROM, a new
window, then the run.

**The aviasolutions.com sender signature: DO NOT REMOVE IT YET.** The controller asked for it
to be removed so the unauthenticated-domain banner stops slowing the review, with the caveat
"if we need it for test sends, keep it until the first send is proven". That caveat is the
branch that applies. While the account is in test mode Postmark restricts recipients to
confirmed sender signatures, and john.carter@aviasolutions.com is the only one on the account,
so it is the only address the first send can go to. Removing it first would leave no valid
recipient and block the send it is meant to unblock. Order: send, prove, then remove the
signature and check whether the aviasolutions.com domain row goes with it. W2 could not reach
the Postmark tab this session to read the signature list; the browser did not respond.

## Done 19 September

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

1. POSTMARK IS REVIEWING. Request in, account state "reviewing" as at 21 Sep. Sending stays
   restricted to confirmed sender signatures until it clears, and domain warming cannot start,
   so this is still the longest lead time in the mail chain. Not cleared by 1 Oct, chase it.
2. CLOSED 21 Sep. AVIA_SMTP_HOST no longer defaults to smtp.office365.com; it is required and
   says so. Fixed alongside the sender-identity fault above, since both came from the same
   assumption that the supplier would always be Microsoft.
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
6. CROSS-WORKSTREAM DEPENDENCIES, now dated from the sibling files rather than assumed.
   W3-STATUS.md (session 1, 19 Sep): the PDF render is "Not started, and now unblocked"; the
   workstation check passed 19 Sep with Chrome, pikepdf 10.10.0 and pillow 12.3.0 present, so
   nothing needs installing; proven end to end 22-25 Sep; and John pulled the pack, the PDF and
   the imagery forward from 8 October to 3 October. The email therefore has a PDF to attach well
   before the freeze, and W2's watchpoint on it is closed.
   W6-STATUS.md (v2, 19 Sep 22:10) asks W2 for two things: "the pack URL rule and hosting
   controls so W6 can place the files by 16 Oct", and "the mail records on the launch domain,
   which the web cutover must not disturb". Both are now W2 deliverables and are dated below.
7. RULING 18, THE UNMANNED WORKSTATION. Taken and understood: remote desktop over Tailscale,
   sign in, run both launchers, disconnect, never sign out, with Stop-Process first because
   Meridian-run.bat re-warms a running server rather than replacing it. W2 will write it in
   those words into the runbook and hand W4 the same words for the host manual, and rehearse one
   deliberate restart in the 11-12 October trial. W2 agrees the scheduled-task answer is better
   and will scope it for 8 October, including the check that the Cloudflare tunnel runs as a
   service. Worth stating plainly: an unmanned box makes the MCT startup line above the only
   thing that will ever tell anyone the master did not load.

## Conflicts seen

Raised here for the controller's sweep to resolve, per README.md. W2 has changed nothing on
either account.

1. **The hosted pack may have nowhere to live.** Ruling 15 requires two emails, the second
   carrying a link to the HTML pack "hosted on the launched site". W6-STATUS.md v2 records that
   the domain is still owed from John by 22 September and that "silence past 29 Sep and the
   14 Oct cutover is not holdable, so the fallback landing page becomes the plan". A landing
   page has no place to put per-visitor packs. So on W6's own stated fallback, half of ruling
   15's email design has no delivery path, and nobody has yet designed how a pack travels from
   the workstation to a public host in any case. W2's view, offered rather than taken: the
   single email with the PDF attached, which W2 has recommended twice on deliverability grounds,
   also removes this dependency entirely. If the controller holds the two-email design, the
   pack host needs an owner and a date that does not sit behind the domain decision.
2. **The web cutover could break the mail records.** W6 names "the mail records on the launch
   domain, which the web cutover must not disturb" as a W2 dependency. Stated precisely so it is
   not lost: aviationobservatory.com now carries a DKIM TXT at 20260919185744pm._domainkey, a
   CNAME pm-bounces to pm.mtasv.net, and a DMARC TXT at _dmarc. If the launch domain turns out
   to be this one, then a nameserver move, a host migration, or the "Restore Default DNS
   Records" control in the Fasthosts panel would remove all three and sending would stop
   silently, with the first symptom being packs not arriving at Routes. W2 asks that no
   nameserver or DNS change is made on aviationobservatory.com without W2 reproducing those
   three records at the new host first and verifying them in Postmark afterwards.

## What other workstreams are waiting on from W2

- **W6, by 16 October**: the pack URL rule and the hosting controls. W2 will deliver the rule by
  3 October, to sit alongside W3's pack and PDF which John pulled to the same date. It will
  cover the unguessable path, an expiry, a noindex header, no personal data in the file, and the
  Sabre position (attribution constant, fares as bands only, no single-route blind figures).
  W3-STATUS.md draws the same line from the other side: a public URL is a published use while
  the emailed PDF is confidential, so the same photograph can be right in one and wrong in the
  other. The rule has to be written once and used by both.
- **W4**: the restart words verbatim for the host manual, which W2 will lift unchanged from
  ruling 18 (remote desktop over Tailscale, sign in, run both launchers, disconnect, never sign
  out, with Stop-Process first because Meridian-run.bat re-warms a running server rather than
  replacing it); the request form and queue view design, which W4 has already written sections
  3.5, 5.5 and 6.1 against; the tablet answer; and the Postmark approval date, which W2 chases
  on 1 October. W4-STATUS.md confirms it has read this file at v6.
