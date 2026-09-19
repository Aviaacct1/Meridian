# Meridian to World Routes: launch-readiness strategy and handover

19 September 2026. World Routes 21-23 October; 4x3m stand booked; a former OAG demo
professional hired to staff it. Boeing demo 13 October (Wendy Sowers) is the dress rehearsal.
John is travelling 20-27 September (UAE), then Italy (3 days) and Paris (3 days) with work
deadlines between, so his hands-on time before Routes is a few days at most. Everything below
is written to be run by Fable-led chats with John deciding, not building.

Umbrella: `GTM-STRATEGY-ROUTES-2026.md`. Commercial detail: `ROUTES-COMMERCIAL-PLAN-19Sep2026.md`.
Companion: `PROMPT-for-Fable-Routes-19Sep2026.txt` (paste into a new chat to start the work).
Register of everything else open: `MASTER-TASK-LIST.md`. This note supersedes the Routes-related
sequencing in that list; the list's other items stand.

---

## 1. The view

**The 15-minute cold forecast is a product problem, not a demo problem, and the demo design has
to assume it is not fully solved by 21 October.** Three answers run in parallel, and only the
first is engineering:

1. **Make cold runs faster** (section 3). There is a built-but-unswitched lever that likely
   removes most of the wait: the Sabre pre-aggregation store (`preagg.py`) replaces the four
   full per-route Sabre scans with point lookups, reproduces the live query to the penny, and is
   gated off pending an identity check. Switching it on is the single highest-value task before
   Routes. Alongside it: a persistent result cache (today's caches are in-process and die on
   restart) and pre-warming.
2. **Run and Optimise live, research later** (section 4, John's design). The visitor's own route
   runs LIVE with Run for everyone, and with Optimise for the interested, on parts pre-warmed by
   airport, not by route (3.6); Optimise is the USP (the time-of-day chart and the best way to
   fly the route) so it must be demonstrable, which sets the speed target. The researched pitch
   deck never runs on the stand: explained with examples, queued as the visitor leaves, emailed
   within 30 minutes. Every queued pitch is a lead record.
3. **Assume the venue network is poor** (section 5). Compute is in Surrey; the stand needs a
   browser and a thin pipe, plus a 5G backup and an offline fallback that still tells the story.

**Commercially**: the go-to-market umbrella (`GTM-STRATEGY-ROUTES-2026.md`) holds the
decisions of 19 September: licence confirmed verbally by OAG and Sabre with letters chased (in
hand for the show, a gate for the first contract); a soft stated price with a written expiring
launch-customer discount; two milestones, demo-ready 21 October and order-ready 7 November.

---

## 2. The calendar, working backwards

| Window | John | Work |
|---|---|---|
| 19-20 Sep | Here | Decisions only: this note, the licence question, the demo shape, who owns what |
| 21-27 Sep | UAE | Speed workstream (3.1-3.3), request-queue design (4.2), lead capture spec |
| 28 Sep-7 Oct | Italy, Paris, deadlines | Build: request queue + email + lead capture; deck; pre-warm list; stand materials |
| 8-12 Oct | Here (short) | Boeing rehearsal prep; **code freeze for demo paths 10 Oct** |
| 13 Oct | Boeing demo | Dress rehearsal: full demo flow, timed, on hotel wifi |
| 14-18 Oct | Here | Fix only what Boeing exposed; train the stand professional; print; pre-warm runs |
| 19-20 Oct | Travel | Final pre-warm; freeze; fallback kit packed |
| 21-23 Oct | Routes | Stand |

The freeze on 10 October is deliberate: the demo path must be stable for a week before Boeing,
and Boeing must exercise exactly what Routes will.

---

## 3. Speed workstream (the engineering)

### 3.1 Measure before touching anything (day 1)
Instrument one cold Optimise and one cold Run on SJC-TPE and on an unfamiliar pair, and write
down where the seconds go: Sabre aggregates (connecting_market, behind_market, p2p), the
departure-time sweep (candidates × refine steps × feed scoring), the airline × frequency × season
sweep in /api/optimise (7 frequencies × 3 seasons × up to 3 airlines when nothing is fixed),
catchment/drive-time, and the market brief. No optimisation until the profile exists; the
codebase has been burned by guessing.

### 3.2 Switch on the pre-aggregation store
`preagg.py` (July, review fix R1) already replaces the per-route Sabre full scans with point
lookups from `build_preagg.py`'s derived tables and reproduces the live query exactly; it is used
only when a preagg store is configured, and the identity check that would confirm the swap was
never run on the live path. Task: build the preagg store on the workstation, run the identity
check on the pinned routes (SJC-TPE, GOA-NYC, the acceptance set), confirm penny-identical
outputs, configure it, measure again. Expected to remove most of the Sabre cost, which is
expected to be most of the wait; the measurement will say.

### 3.3 Persist the caches
Every cache the app holds today (`S` optimum cache, market brief, `_CFG_SEATS_CACHE`,
`_DEMO_CATCH_CACHE`, `_TREND_CACHE`) is in-process and lost on restart. A restart the night
before Routes would throw away every pre-warmed route. Task: one on-disk result cache keyed on
the full run signature (route, airline, aircraft, seats, freq, season, dep_time, curfews,
partners, forecast year, store vintage) storing the complete forecast payload, read before any
compute, written after. Store vintage in the key so a data refresh invalidates cleanly. Keep it
simple: a DuckDB or JSON-per-key file under LOCAL_CACHE.

### 3.4 Narrow the default demo sweep
/api/optimise with nothing fixed sweeps 7 frequencies × 3 seasons × 3 airlines. For the stand,
default the demo profile to annual season and a named airline (the visitor names their own),
which cuts the sweep by 9x before any engine change. Keep the full sweep available behind a
switch; do not remove it.

### 3.5 Workstation headroom
DONATELLO is a Core Ultra 9 with 64GB. The DuckDB run rules (memory cap, threads 4) were set for
a 16GB box. Raise the caps for the workstation deliberately and measure; this is free speed if
the queries are memory- or thread-bound.

### 3.6 Pre-warm BY AIRPORT, not by route (John, 19 September)
3,500 delegates, 200+ airports, each pitching eight or more routes: the routes cannot be
guessed. They do not need to be. Most of the cold cost is per-airport, not per-pair: catchment
and drive times, competing airports, origin-side Sabre aggregates, the destination hub's boards
and feeders. So the cache (3.3) is keyed at COMPONENT level as well as whole-run level, and the
pre-warm script warms every attending airport as an origin and as a destination. Any pair a
visitor names then runs on warm parts. The attending-airport list is published before the show;
add to it as the delegate list firms up. The 50-route panel (4.3) is the rehearsed demo set, not
a guess at demand.

### 3.7 Three runs, three costs, and which ones the stand shows (John, 19 September)
- **Run assessment**: the engine call, circa 10 seconds today plus whatever the Sabre scans cost
  cold. With the airline named and the departure left blank it ALREADY produces the time-of-day
  chart (optimise_departure runs inside the forecast), so the USP the Taipei airlines liked is in
  every Run. Shown to everyone.
- **Optimise**: the sweep over airline x aircraft x frequency x season on top of the departure
  optimisation; 10-15 minutes cold today. This is the function that makes an interested visitor
  want to buy, so it is DEMONSTRATED on the stand for those who lean in, and it must be
  demonstrable: warm parts, the narrowed default sweep (3.4), and PROGRESSIVE DISPLAY, the
  departure curve first, then the sweep table filling row by row as candidates finish, so the
  wait is the demonstration rather than a spinner. That progressive rendering is a build item
  (the August progress-indicator gap, now with a reason).
- **Researched pitch**: web research plus deck generation, minutes, needs the internet whatever
  the venue does. Explained on the stand with pre-built examples; queued as the visitor leaves
  and emailed within 30 minutes.
Acceptance tests: with preagg on and airports pre-warmed, Run on a never-run pair answers in
under 30 seconds, and Optimise on the narrowed default finishes in under three minutes with the
first result on screen inside 30 seconds. Measure both in 3.1 and again after 3.2-3.6.

---

## 4. Demo design (the product on the stand)

### 4.1 The stand flow (John's design, 19 September)
1. The visitor names their airport, a route they are pitching, and their target airline. The
   stand professional runs it LIVE with Run: market background paints itself on route entry,
   forecast lands, time-of-day curve, tail chart, economics. Seconds. They see how easy it is,
   and whether it matches what they have done or gives them something they had not thought of.
2. For the interested, OPTIMISE, live: "what is the best way to fly this", airline, gauge,
   frequency, departure, with the screen filling progressively while the stand professional
   talks it through. Under three minutes. This is the moment that sells.
3. The researched pitch is explained with two pre-built examples on the laptop, never run live.
   As the visitor leaves, the stand professional enters name, company, role, email and consent
   on the request form and queues the pitch against the exact run just shown (the one-run
   definition guarantees the deck carries the same numbers). It emails within 30 minutes: an
   active follow-up they can use in their next meeting. Every queued pitch is a lead record.
4. The 50-route panel (4.3) is for walk-ups with no route in mind, for the opening line, and for
   Plan B.

### 4.1a Two plans, one stand (a wired connection is being taken; assume it may fail)
- **Plan A, wired works**: live Run against the Surrey workstation; pitch queued and emailed in
  30 minutes; leads captured to the store.
- **Plan B, network dead**: the laptop build (4.5) runs the same live Run offline; the panel's
  packs are pre-rendered on the laptop; pitch requests still go out because the queue lives on
  the workstation in Surrey, relayed by phone tethering when possible or typed in that evening.
  The visitor's only difference is whether the email arrives in 30 minutes or that night.
  Plan B is only real if the laptop build is proven by 1 October.

### 4.2 Build list for the requested tier
- A **request form** on the dashboard (stand mode): name, company, role, email, route, airline,
  consent tick. Persisted to a lead store. The website already has a Cloudflare D1 binding and a
  working contact function (`functions/api/contact.js`); reuse the pattern, or a local DuckDB
  table on the workstation, whichever the new chat finds quicker. It must survive restarts.
- **Email on completion**: the existing background job pattern (`/api/pitch/start`,
  `/api/report/start`, job_watch) plus a sender. Cloudflare Email Routing cannot send; use a
  transactional sender (Resend, Postmark, or Microsoft Graph from the Avia tenant, which the
  Outlook connector already reaches). Attach the HTML pack and workbook; link to nothing that
  needs a login.
- **A queue view** for the stand: what is running, what is sent, what failed. Failures must be
  visible on the stand, not discovered from a visitor's complaint.
- **Stand mode**: a query flag or environment switch that defaults the sweep (3.4), shows the
  request form, and puts the pre-warmed panel one click away. Expert mode STAYS VISIBLE in the
  nav (John, 19 September): it is evidence of depth; the stand professional simply does not open
  it.

### 4.3 The pre-warmed panel (commercial decision, John)
Choose 40-60 routes that will resonate with the delegates likely to visit: the exhibitor
airports' obvious unserved long-haul pairs, the routes Avia has pitched publicly (SJC-TPE,
Bologna, Genoa-NYC, Tampa, Zagreb), and a spread across regions so any visitor sees a
neighbour. Run them all through both Run and Optimise the week before, and again the night
before. Add the delegate list's airports as it becomes available.

### 4.4 What the stand professional needs
A 90-second story, a 4-minute demo script on two routes, the request form, the fallback kit
(4.5), and a one-page "what Meridian is and is not" (measured, calibrated, physics-capped; the
three classes of number; what "calibrated 89% within 20%" does and does not claim, per the
Atlas ruling). Train them on 14-16 October against the frozen build. They do not open Expert mode; they may point at it.

### 4.5 Fallback kit (assume something fails)
- The **laptop build** (config.py `BUILD=laptop`, DATA_ROOT local) running the tool offline on
  a stand laptop with the stores copied. This exists in config; the new chat must prove it
  actually runs, cold, on a laptop, with the current stores, before 10 October. If it does, the
  venue network stops being a single point of failure.
- Pre-rendered HTML packs for the pre-warmed panel on the laptop, openable from a folder.
- A 3-minute screen recording of the full flow, for the moment nothing else works.
- A 5G router plus phone tethering as the primary network, venue wifi as backup, not the
  reverse.

---

## 5. Hosting and network

Compute stays on DONATELLO behind the Cloudflare tunnel; the stand needs a browser only. The
things to check before Boeing: tunnel and workstation uptime monitoring with an alert to John's
phone; a documented restart procedure the stand professional can trigger by phone call to
someone at Fairoaks; Cloudflare Access allowing the stand laptop and the stand professional's
email; the request-queue emails not being caught by Access. The Jarek-era Basic-auth username
question (master list 1.5) matters now: if leads are attributed from the username field, every
lead will read you@carrier.com. Attribute from the request form, not from auth.

---

## 6. The presentation and the pack

- **Stand deck (PowerPoint)**: rebuild `Avia_Cortex_Process_and_Methodology.pptx` (2 July) into
  a 10-slide stand deck: the problem (route decisions on thin evidence), what Meridian does in
  the three-classes-of-number framing, the accuracy claim stated exactly as ruled (calibrated
  leads, blind only as portfolios), two worked routes, the product family, pricing on request.
  Observatory palette, Avia author metadata, en-GB. Check it against the methodology note for
  Nick before it goes near a slide, so the two never contradict each other.
- **The emailed pack**: the HTML pitch and workbook the tool already produces, plus a one-page
  cover note template with the follow-up ask and the stand professional's and John's contacts.
  Confirm the pack's every figure carries its source line and that no figure labelled
  illustrative survives; that principle was ruled on 24 August.
- **Website**: it is noindex behind Access. If it is to be pointed at from the stand, either the
  IT firm launches before Routes (`SITE_ENV=production` is the whole switch) or the stand points
  at a one-page landing behind nothing. Decide by 1 October; Jol's rewrite pace sets it.

---

## 7. Commercial path

John's instinct: take interest and follow-ups at Routes, offer a few firms year-1 launch pricing
as paid beta testers, resolve hosting and support issues with them, launch properly after.
That is the right shape, with these gates and decisions:

1. **Licence clearance, week one, before any price exists.** Sabre MI and OAG licences govern
   what derived outputs may be sold and to whom. The Boeing arrangement was derived-outputs-only
   by design. Get the position in writing from Avia's own licence terms (and RDC/ACI closure,
   already on the estate list) and, if needed, from Sabre. If the answer is restrictive, the
   product is sold as a service with Avia running it, not as tool access; that changes the
   pitch, not the demo.
2. **Beta offer, one page**: what the client gets (tool access for named users, N routes per
   month, packs, a quarterly review call), what they give (feedback, a reference if satisfied,
   patience on hosting), price and term (year 1 fixed, year 2 at list less a stated discount),
   and what is excluded (no liability for decisions taken on outputs; the disclaimer already in
   the economics module says it). Keep it to three tiers at most: airport, airline, adviser.
3. **Hosting per client**: today one shared instance with one shared password behind Access.
   Paid beta needs at least per-client Access policies and separate usage logging, not a
   rebuild. The user model (Jarek's permissions point) comes after the first paying client
   exists, not before.
4. **Lead handling**: every request-form lead and every business card into one list (the
   D1/DuckDB store from 4.2), tagged by interest and route, with a 48-hour follow-up from John or
   Jol carrying the pack and the beta one-pager. The follow-up cadence is where the sales are;
   the stand only starts them.
5. **What to promise on the stand**: the tool as demonstrated, packs by email, beta pricing "on
   request, limited places", and nothing about features not in the frozen build. Day-of-week
   allocation, fare in the QSI score and the new aircraft types' economics are post-Routes.

---

## 8. Who does what

- **John**: decisions (licence, pricing, panel list, website go/no-go, freeze date), the Boeing
  demo, training the stand professional, follow-ups after Routes.
- **Fable chats** (the prompt): the speed workstream, the request queue and email, lead capture,
  stand mode, the laptop-build proof, the deck rebuild, pre-warm scripts, this note kept current.
- **Jol**: website copy; the stand one-pagers' wording; second reviewer on the deck.
- **Nick**: methodology consistency check across note, deck and any accuracy statement; a
  second pair of eyes on the pre-warmed panel's outputs before they are shown.
- **Jess**: Atlas is on the stand too (Boeing wants both); the same freeze and rehearsal apply.
- **Stand professional**: the demo, the request form, nothing else; trained 14-16 October.

---

## 9. Standing rules for every chat that picks this up

Read `MASTER-TASK-LIST.md` first. Git is the only place code lives; pull before editing, commit
and push after, and never run git against a mounted clone from Cowork (hand John or the DevPC
the block). Command blocks are labelled DevPC / Workstation Remote / Workstation Actual and open
with `cd`. Measure before optimising. Flag, never fill. No figure without a source line. Nothing
illustrative on a client-facing surface. Demo-path freeze 10 October; after that, exceptional
changes only, tested on the Boeing flow first.
