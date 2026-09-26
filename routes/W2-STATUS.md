# W2 stand flow: status

Version 15, 27 September 2026. Written by the W2 build chat for the controller; rewritten each
session, never appended. routes/README.md v1 read and followed. W2-RULINGS.md read from the 22
September entries to the end, including all nine sections written since v14, and acted on below.
Umbrella Status block, critical path 2A and pre-mortem 32-33 read. Dates here follow the rulings
file and the commit log; this session's own clock reads 26 September, which the controller has
already noted as a one-day discrepancy in the weekday labels.

W2 did not write for five days. Nothing in this file assumes the controller remembers v14.

## Live state

| Item | State | Next |
|---|---|---|
| TAO mailbox route (item 60) | ANSWERED below, due Tue 29 Sep | John chooses; one of the two routes needs nobody's permission |
| Same-day pack (2A) | Queue, three states, hold setting, reviewer view and email field BUILT and tested | W3's build step wired to the queue; a real send on the 11-12 Oct trial |
| Old-engine first-screen line | Controller's #engineNote checked, correct wording and position | Carry the same line into the pack cover (with W3) |
| Two presentation slips (27 Sep) | BOTH FIXED | Nothing |
| No Avia Solutions on stand screens | FOUR found, four fixed | Reported below; one was outside W2's named files |
| No economics figure (pre-mortem 33) | Three surfaces were showing one; all three now withheld behind a switch that defaults off | Returns when the controller accepts the basis |
| Catchment radius under R6 (W10 item 1) | NOT STARTED, and it needs a workstation run | The before-and-after the ruling asks for cannot be produced from the Dev PC; see below |
| Stand mode | NOT BUILT. It exists only as the MCT refusal in cortex_app | After the pack, or it does not land |
| Lead-store rewire, capture buttons | Store built 21 Sep; the app still writes the JSONL | 2 Oct |
| Laptop build | Waiting on John's two spec blocks | 8 Oct, and John is away 6-9 Oct |
| Progressive Optimise (item 5) | Deferred to after Routes, accepted | Nothing |

## 1. John's TAO mailbox: the answer

**Recommendation: a Microsoft 365 Business Basic subscription bought in the name of The Aviation
Observatory Ltd, on its own tenant, with John as its administrator.** Achievable on Monday without
asking anyone, because John buys it himself and administers it himself. £5.40 per user per month
billed annually, £6.48 monthly (Microsoft's UK page, read 27 September). It gives
john@aviationobservatory.com as a real mailbox, sending and receiving, and it appears in Outlook
beside his Avia account rather than replacing it. Setup is a domain verification TXT record and an
MX record, both of which W2 adds; Postmark's DKIM and Return-Path records are untouched, because
Postmark aligns through the Return-Path rather than through MX or SPF.

Three reasons beyond speed. TAO is a separate company and will need its own mail whatever happens
after Routes, so this is not a workaround. It keeps the Observatory's mail out of Avia's tenant,
which is the position the entity was formed to hold. And it removes the IT firm from the critical
path permanently, rather than for this one request.

**The alternative, if John would rather not run a second tenant: a mailbox on the domain from
Fasthosts,** who already hold the registration, added to Outlook as an ordinary IMAP account. Same
effect for sending and receiving, one supplier, no tenant to administer. Slightly worse in that
the mailbox is then tied to the registrar.

**What does NOT work, stated so it is not attempted:** Cloudflare Email Routing alone. It forwards
inbound mail and does not send, so it cannot be John's sending address. It is still worth having
for the domain's other inboxes and the DMARC reports, and it comes with the zone move (item 20),
but it is not an answer to this question. Postmark is the product's transactional sender and is
not John's personal address; using it for his own mail would mix the reputation we are about to
warm with the invitations.

**The route through Avia's tenant is achievable only through the IT firm and W2 does not recommend
it**, for the entity reason above. If John wants it anyway, this is the paragraph to forward, and
nothing in it can be done by an ordinary user account:

> Please could you add the domain aviationobservatory.com to our Microsoft 365 tenant and create a
> licensed mailbox john@aviationobservatory.com for John Carter, with send-as permission from his
> existing account. The domain already carries live DNS records for a transactional email provider:
> a DKIM TXT record at 20260919185744pm._domainkey and a CNAME pm-bounces pointing to pm.mtasv.net.
> Please do not remove or overwrite either, and if you publish an SPF record for the domain please
> include Microsoft only; the provider aligns through its own return path and does not need to be
> in SPF. We need this by Tuesday 29 September for a product launch at a conference in October.

**Until one of these exists, John sends no invitations from an Avia address.** That is the
controller's ruling and W2 has nothing to add to it except that the choice is a purchase decision
rather than a technical one, and both options work.

## 2. The same-day pack: built this session

`app/pack_queue.py`, 395 lines, on the same DuckDB store as the lead record. `app/test_pack_queue.py`
holds 60 checks, 0 failed. The lead is the person and the job is one pack for one run, so a visitor
who comes back for a second route gets a second job and one record.

WHAT THE THREE STATES DO, each a check rather than an intention:

- NOW is the host's tick on the email field. The job sends when the build passes its own checks,
  with no hold and no human step.
- HOLD is the default. The build runs at once, then the job waits the configured hold and sends
  itself unless a reviewer pauses it. The countdown is on the queue page.
- PAUSED stops it, with a one-line reason the queue shows, and it is released by hand.

A BUILD THAT FAILS ANY CHECK GOES TO PAUSED AND NEVER TO SEND. There is no code path from a failed
check to a delivered pack; the test asserts it for a job a day past its clock. A SEND IS NOT
RECORDED WITHOUT THE PROVIDER'S OWN MESSAGE ID, for the 21 September reason. A released job
restarts its clock rather than firing the moment it is released.

THE HOLD IS A SETTING in minutes, stored, changed at the top of the queue page with no restart, and
read at the moment each build passes. Zero is a real value and means send on pass; it is held
apart from unset, so an unconfigured store still defaults to 30 rather than to zero.

THE HOLDING EMAIL: a paused job appears once on `needs_holding_email()` and is recorded against its
own provider id when sent, so the visitor is told the same day and told once.

ENDPOINTS: `POST /api/pack/request` (the email field), `GET /api/pack/list`, `GET /api/pack/job`,
`POST /api/pack/action` (pause, send_now, release, note), `GET|POST /api/pack/hold`,
`GET /api/pack/preview`.

THE REVIEWER'S VIEW is `/demo/queue`: newest first, one line a job with visitor, route, state,
countdown and reviewer note, two actions only, and a preview button that appears once the build has
written a file. It polls every ten seconds, because a hold running out is the thing it exists to
show. It is built to be read on a phone between conversations.

THE EMAIL FIELD is at the foot of the result page inside the existing report row, so it is on both
Run and Optimise. It carries name and company, the consent tick, and one tick for "send as soon as
it is built". It sends `STATE.lastQ`, which is the run on the screen, so the pack reproduces what
the visitor watched.

WHAT IS NOT DONE. The build step is W3's generator and is not yet called: a job sits at `queued`
until something marks it built. The sender is not written either, so nothing leaves yet. Both are
small against what is now in place, and both are next. The one-page preview is a hook that says
plainly there is no preview yet rather than returning a blank page.

W3 SUPPLIES THE BUILD CHECKS. W2's side is ready for them: `mark_built(job, ok=False,
failed_check="...")` is the whole interface, and the text W3 passes is what the reviewer reads.

## 3. The stand-surface audit (no Avia Solutions, no economics)

FOUR PLACES NAMED AVIA ON A SCREEN. All four fixed to The Aviation Observatory:

1. `cortex_dashboard.html`, the pack request: "Held for approval by the Avia team."
2. `cortex_dashboard.html`, after a send: "further requests need a release by the Avia team."
3. `cortex_dashboard.html`, the economics panel: "a lease rate ... which Avia does not publish."
4. `cortex_help.html`: "send it to the Avia team."

The fourth is OUTSIDE W2'S NAMED FILES. `cortex_help.html` has no owner in README's table and it
is in the dashboard's own navigation, so leaving a known breach in place seemed worse than editing
it. Announced here; the controller can move it to another workstream and W2 will stop touching it.
Nothing else in W2's files names Avia on a screen: the page titles, the launcher window title and
the footers all read The Observatory already, and the remaining matches are code comments and the
copyright line in docstrings.

THREE SURFACES SHOWED AN ECONOMICS FIGURE, which is what the controller asked W2 to report:

1. The Economics entry in the left navigation, and the `/economics` page behind it, which states a
   route P&L.
2. The "+ Economics" button in the Output control on the result page.
3. `#econRow` on the result page itself, whose headline is "Annual contribution towards ownership"
   and whose table states Revenue and a full cost breakdown.

All three are now WITHHELD behind `AVIA_SHOW_ECONOMICS`, which defaults OFF. The navigation entry,
the button and the row are removed from the page rather than hidden, so nothing answers with a
figure; `/economics` returns a short page saying the view is withheld while the cost basis is
checked, rather than a 404 or a blank. The server prints which way the switch is set on every
start. The Optimise contribution ranking is ordinal and is untouched, per the ruling.

This is a suppression with a named condition, not a sixth default-off switch: it is stated on every
server start and it comes back when the controller accepts the basis. W2 would rather the
controller ruled the switch away entirely once pre-mortem 33 closes than leave it in the code.

## 4. The old engine, and the two presentation slips

THE FIRST-SCREEN LINE IS CORRECT AS THE CONTROLLER LEFT IT. `#engineNote` renders before the basis
whenever `forecast_engine.local_leg` is anything other than "calibrated model", and the wording is
the ruled sentence verbatim. W2 changed nothing and will carry the same sentence into the pack
cover with W3 rather than write a second version of it.

SLIP ONE, "incl. feed" on a point-to-point carrier. Fixed: the phrase now appears only when the
connecting figure is above zero.

SLIP TWO, the rotation diagram drawing seven days for a 3x schedule. This was not a drawing
problem. `drawTail` read `d.capacity.frequency`; the payload's key is `cap.freq`. Every branch fell
through to a literal 7, so an Optimise result at 3x, where the visitor has typed nothing in the
frequency box, silently drew a daily rotation and printed "Pattern basis: daily". Fixed to read the
right key, and where no frequency can be established from the run the diagram is WITHHELD rather
than drawn on an assumed one. The pattern function itself was already right: at 3x it draws three
days and states in full that consecutive days are a working assumption and day-of-week allocation
is not modelled.

This is the same shape as the MCT and friction faults: a lookup that misses, a neutral default
substituted in silence. Fourth and fifth instances. The remedy is the same each time.

## 5. The friction raster, and a risk the launcher carries

Logged: the catchment-distance commit went in under the controller's subject at 30e3e78.

The launcher now sets `AVIA_DRIVE_TIMES=1` and echoes "road drive times on", and W1 measured the
effect properly (identical on the calibrated model, -3.2% to +4.1% on the market-share engine).
But NOTHING IN THE LAUNCHER POINTS AT THE RASTER, and `config` resolved it from the cache and the
Egnyte root, neither of which holds it. If `AVIA_FRICTION` is not set at machine scope on
donatello, the switch is on, the raster is not found, and the console says STRAIGHT LINE while the
launcher's own echo says road times. W2 has not been able to confirm which it is.

FIXED so the question cannot arise again: `config.FRICTION_RASTER` now resolves from `AVIA_ROOT`
first, which is the variable the launcher sets and the one a cloned product drive carries. Road
times then work on a new workstation with nothing set by hand, which is the direction John stated
on 24 September. The console line is in the runbook's start checklist as a stop condition.

## 6. Postmark: the plan, the cost and the fallback

From Postmark's own pricing page, read 27 September: the free developer plan is 100 emails a month;
BASIC is $15.00 a month for 10,000, PRO $16.50, PLATFORM $18.00, all with the same 10,000 included
and differing on features, custom domains and user seats.

W2 RECOMMENDS BASIC at $15.00 a month. 10,000 covers the stand many times over; the difference to
Pro is overage pricing and features the stand does not use. WAITING ON JOHN to approve the upgrade.
Under his ruling it is bought only after every test send from aviationobservatory.com is delivered
with a message id and lands in the inbox at both a Microsoft 365 address and a Gmail address.

THE FALLBACK PROVIDER, named now so a switch on 3 October costs a day: **Amazon SES**. Reasons: an
HTTP API and an SMTP endpoint, both with explicit per-message identifiers; DKIM by CNAME records of
the same shape we already publish, so the DNS work is an addition rather than a rebuild; and no
approval queue of the kind that cost us three hours on 21 September, beyond the standard sandbox
removal. The transport already sits behind one module with an injectable poster, so the change is
a new `Transport` class and a selector value, not a rebuild. W2 has not written it and will not
until it is needed.

DECISION DATE 3 OCTOBER stands: Postmark upgraded or replaced.

NOT YET DONE and owed before any invitation: the zone move to Cloudflare (item 20), the four
records recreated and re-verified there, and delivery re-proven from the Observatory domain with a
message id. The zone move is also what W6's site launch waits on, so it should not sit behind the
pack build; W2 will take it next session unless the controller would rather it went first.

## 7. The catchment radius under R6: why there is no before-and-after yet

The ruling asks for the before and after on the London, Milan and New York competing sets. That
cannot be produced from the Dev PC: the competing set is built from the OAG served index, which
needs `oag.duckdb` on the workstation. W2 can write the change and a script that prints the three
sets both ways, but John has to run it, and he runs one workstation session a day.

W2's view on the design, unchanged by anything since: the radius is the wrong instrument for the
Birmingham case, because the distance is measured from the origin AIRPORT and not from the city, so
Heathrow to Birmingham is 140 km while Luton to Birmingham is 114 km, and one radius gives two
different London catchments depending on which airport the visitor typed. The classification in
`app/airport_catchment_geo.csv` already marks BHX and LHR as primary and the London secondaries as
secondary, and no code reads it. John's banded starting values can be implemented as ruled; W2 asks
only that the primary-airport rule is measured alongside them in the same run, since the script
costs nothing extra and the ruling's own principle is that separate primary-metro markets must not
merge. If the answer is not in hand by 6 October it does not land before 10 October and W2 will say
so rather than rush it.

## 8. The venue line

No disagreement, and no figure that changes the order. The demo is a browser on the core laptop
against the Surrey workstation over the Cloudflare tunnel, which moves JSON, not files. The one
thing that is not small is a pack preview or a download the stand pulls, and those are single-digit
megabytes. W9's 20/10 Mbit/s line with router and WiFi covers it and 4G is a sound second route.
The measurement W2 would rather have is latency than bandwidth, because the visitor watches a
progress line; that is a reason to keep the wired line rather than rely on the hall's WiFi, which
W9 has already recommended.

## 9. Delivered this session

- `routes/STAND-RUNBOOK.md` v1, which did not exist. It collects every binding runbook line from
  the rulings since 24 September: the start procedure, the five console lines that must be right
  before the stand opens, the incident and log rules, the same-day pack operation, the named-route
  handover, and the 10-23 October store freeze. W4's host manual stays the host's document; this
  is the operator's.

## 10. Needed from John

1. WHICH MAILBOX ROUTE, by Tuesday. A purchase decision, not a technical one.
2. THE TWO SPEC BLOCKS: the DevPC `C:\Avia` store inventory with sizes and dates, and the core
   laptop's make, RAM, architecture, free disk and Python. The 8 October laptop proof needs them
   before 6 October, because John is away 6-9 October. If they cannot come by 5 October, W2 needs
   a named person who can run the block instead.
3. APPROVAL to buy Postmark Basic at $15.00 a month, conditional on the test sends passing.
4. THE NAMED REVIEWER for the pack queue and their hours for 21-23 October (umbrella item 62).
   The queue is built and nobody is assigned to it.
5. WHICH TABLET the capture front end runs on, and how it reaches the form under Plan B.
6. One workstation run for the catchment before-and-after, once W2 has written the script.

## 11. Conflicts seen

1. `cortex_help.html` has no owner in README's table and W2 has edited it, for the reason in
   section 3. It needs an owner.
2. The critical path puts stand mode after the pack and the laptop build, and W2 agrees, but stand
   mode is the thing that makes "no Avia Solutions on a stand screen" and "no economics figure"
   enforceable as a mode rather than as a global setting. Applied globally, as they are now, they
   also apply to John's own working sessions and to the Taif proposal work. W2 has taken the
   conservative reading. If John needs economics for Taif before pre-mortem 33 closes, that is a
   ruling, and the switch exists for it.

## 12. Dates

Mailbox route Tue 29 Sep. Capture buttons and the lead-store rewire Fri 2 Oct. Postmark decision
3 Oct. Catchment answer 6 Oct or not at all. Laptop proof 8 Oct, John away 6-9 Oct. Freeze 10 Oct.
Trials 11-12 Oct. Suzanna 16 Oct.

## 13. A broken main, and how it happened again

While this session was working, commit **b478b97** (W1, 27 Sep) staged and pushed W2's
uncommitted `app/cortex_app.py` and `app/cortex_dashboard.html` under a W1 subject. The pushed
`cortex_app.py` therefore carries `import pack_queue as PQ` while `app/pack_queue.py` is not in
the repository. A pull and restart on the workstation fails at import and the server does not
start. W2's block adds the missing module and closes it; b478b97 is otherwise sound and is not
reverted.

THE WORKSTATION SHOULD NOT PULL AND RESTART UNTIL THAT BLOCK HAS LANDED.

This is the second time: **30e3e78** on 22 September swept the catchment-distance work the same
way. The cause is a commit that stages the whole working tree rather than the files its
workstream owns, and the README's ownership table cannot prevent it because the two chats share
one clone. W2 is not asking for anyone to be told off; it is asking the controller to rule that
every commit names its files, because the failure mode is a main that does not start and nobody
finds out until a restart.

## 14. Commits

- **30e3e78**, 22 Sep, under the controller's subject: the catchment distance report.
- OWED, block with John: this session. `pack_queue.py`, `test_pack_queue.py`, the queue endpoints
  and view, the email field, the economics switch, the two presentation slips, the Avia naming,
  the `AVIA_ROOT` raster resolution, `STAND-RUNBOOK.md` and this file.

Tests on the Dev PC before the commit: pack queue 60, lead store 47, friction 28, MCT 14, demo flow
89. All 0 failed. The dashboard's script block parses.
