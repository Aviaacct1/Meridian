# W2 stand flow: status

Version 8, 21 September 2026. Written by the W2 build chat for the controller; rewritten
each session, never appended. routes/README.md v1 read and followed: facts about other
workstreams below are taken from their STATUS files and quoted with the version, never from
memory of a chat. W2-RULINGS.md v1 read and acted on. Dates
corrected from the "21 September" paste. Out of scope and untouched: engine demand logic, and
W1's preagg, caches and pre-warm.

## Where this stands at close

John stopped the session at 20:50 to wait on Postmark. W2 is NOT blocked: the two largest
remaining build items need nothing from anyone and are next session's work.

WAITING ON, in the order it bites:
1. POSTMARK APPROVAL. The account is in test mode, so sending is restricted and no real pack can
   go anywhere. Human review at Postmark's end, requested 19 Sep. This gates the email half of
   item 3 and all domain warming. Chase it if it has not cleared by 1 Oct.
2. THE TWO SPEC BLOCKS from John: the DevPC C:\Avia store inventory with sizes and dates, and
   the core laptop's make, RAM, architecture, free disk and Python. These gate the load
   procedure for the external drive and therefore the 8 Oct laptop proof. The 1 Oct hardware
   go/no-go stands whatever happens.
3. JOHN'S APPROVAL to send Suzanna the four questions in this file. They shape what stand mode
   defaults to, so the longer they wait the more of item 2 is built on W2's guess rather than on
   four weeks of her use.
4. Not blocking today: the DMARC reporting route, W3's PDF date, W6's website date, which tablet
   the capture front end runs on, and John's 40-60 route panel.

PROCEEDING WITHOUT WAITING, next session: stand mode (item 2), then the DuckDB `leads` table and
the JSONL migration (the half of item 3 with no external dependency). If Postmark approves in
the meantime, the demo_mail.py host fix (watchpoint 2) comes forward ahead of both, because it
is the one change that must land before anything real is sent.

THE NEXT RESTART, whenever it happens and for whatever reason, does two jobs at once: it makes
the MCT line speak for the first time, answering whether the live portal has been running
without the master, and it picks up the Postmark variables. Nothing needs restarting for its own
sake while the account is in test mode.

UNCOMMITTED: the commit-hash paragraph at the foot of this file, and this section. Everything
else W2 has produced is on main at 2cab1b2. The next block clears both.

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

**app/send_first_pack.py written, not yet run.** It sends one real message through
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

**2cab1b2**, 19 September, pushed to Aviaacct1/Meridian main (89c9a02..2cab1b2). Ruling 16's MCT
reporter, startup line and stand-mode refusal (app/connection_builder.py, app/cortex_app.py,
app/test_mct_report.py), the .gitignore secrets patterns, and this file. John ran
test_mct_report.py on the DevPC before committing: 14 checks, 0 failed, so the record is on the
run host and not only in a sandbox.

Still owed against it: the first server restart, which is what makes the MCT line speak and
which also picks up the Postmark variables. Nothing needs restarting for its own sake while
Postmark holds the account in test mode.
