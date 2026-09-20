# Controller to W3: rulings and instructions

Written by the programme controller (the Fable chat), rewritten whenever a ruling lands.
W3 reads this at the start of every session and acts on it; W3 never edits it. W3's own
statements go in W3-STATUS.md, which the controller never edits. John pastes nothing.
Read routes/README.md first: it says who writes which file, who owns which code, and how conflicts are reported and resolved.

## RULING 20 September 2026, 14:00 (final, replaces the 13:00 text): TIERS BY USAGE, NOT AIRPORT SIZE (umbrella item 37). SUPERSEDES every "by airport size, three seats, 100 presentations" and every "£15,000 / £20,000 / £25,000" wording below

John has ruled the list price is three tiers differing in usage and wrap-around, with ONE
PRODUCT in every tier. Airport size is not a pricing axis and no size definition is to
appear anywhere. Where older wording survives in this file or in your own drafts, replace it
with this table and report the replacement in your STATUS.

| Tier | Price a year | What it includes | Users |
|---|---|---|---|
| 1 Forecast | £15,000 | Meridian in full: calibrated route leads, route forecast (Run), optimised route forecast (Optimise), schedule sizing, route economics; the standard forecast pack (deck and workbook). No researched packs | 2 |
| 2 Pitch | £22,500 | Tier 1 plus up to 100 researched airline pitch packs a year; brand skin (client logo, colours and fonts on Meridian's own layouts) | 3 |
| 3 Programme | £27,500 | Tier 2 with unlimited researched packs (fair use); the client's own defined catchment, loaded once at onboarding and refreshed only at renewal; Watch monitoring across the client's leads; a named Avia contact and one refresh call a year | 5 |

Stand logic, usable verbatim: Tier 1 says which routes; Tier 2 gives you the deck to pitch
them; Tier 3 runs your whole route-development programme. Larger airports pay more because
they pitch more airlines, not because they are large.

Terms that go with the table (W5 drafts them; W3, W4, W6 quote nothing beyond the table and
the host sentence): above 100 packs a Tier 2 client upgrades for the difference or pays the
per-pack overage rate (John still owes the rate, umbrella item 6); an in-year upgrade costs
the FULL annual difference (£7,500 Tier 1 to 2; £5,000 Tier 2 to 3), never pro rata, and the
renewal date does not move; discounts are NAMED only (launch cohort; multi-year prepay;
group, second and later airports under one operator; referral) with a Tier 2 net floor of
£20,000; usage is reported to the client quarterly.

Options, at the launch rate (50% if adopted in year 1, 75% in year 2): client template
mapping £5,000 one-off, bespoke, always worded "Avia maps Meridian's outputs to the client's
template as a one-off exercise; where a researched section does not fit the template's
layouts, Avia proposes the layout"; additional catchment definition £2,500; extra users
(price unset); Cortex API from £15,000 when available. The tiers carry only the brand skin,
never a promise of fit to the client's own template.

NOT IN ANY ROUTES MATERIAL: an Assured or review package, consulting hours, or any Avia
review of runs. The client-catchment load is "available from your onboarding", never
demonstrated on the stand.

The launch offer (item 29) is unchanged and applies to whichever tier is chosen: year 1 at
50% (£7,500 / £11,250 / £13,750, fixed at signing), year 2 at 75%, year 3 at 85%, three
fixed cash prices on the 3% illustrative inflator, sign by 30 November 2026. Host sentence:
"launch clients who sign by the end of November pay half our list price in year one; the
list is £15,000 to £27,500 a year depending on how much of the tool the airport wants".
Still open in item 6: launch places, per-pack overage rate, payment terms, entity.

## Scope (commercial plan section 3; umbrella W3)

1. The 10-slide stand deck, PowerPoint: problem; what Meridian does in the three-classes-of-
   number framing (measured, calibrated, physics-capped); the accuracy claim exactly as ruled;
   two worked routes with real charts from the tool; the product family; the offer on the last
   slide. Observatory palette, Avia Solutions as author and last-modified-by, en-GB proofing
   at the document default with no run-level language elsewhere, A4 not needed (16:9).
2. The HTML pack tuned for a stand conversation (the route on a map, market background,
   forecast, time-of-day curve, tail chart, economics, every figure with its source line).
   W3 owns the pack's CONTENT and rendering; W2 owns how it is hosted and sent.
3. The PDF render of the pack: headless Chrome on the workstation, same content and imagery,
   A4, Avia author metadata. A build item, due 8 October.
4. Imagery: WIDENED by John 19 Sep. Airport-specific photography from more than one online
   source with paid stock held for the gaps, at least three images per airport, with the
   Observatory mood frames and charts kept; every image still carries its rights record and
   the build still refuses a bare one. Formerly: from the rights-managed Observatory library only (C:\assets on the DevPC,
   D:\assets on the workstation, config ASSETS_DIR, rights manifests alongside). Every image
   used carries its rights record; the PNG-to-JPEG step that strips provenance from delivered
   decks (estate index, open) is fixed or worked around before any pack leaves. Hero image per
   pack chosen by destination airport where the library has one.

## Rulings and facts you build to

- Messaging: the four sentences are DRAFT until John and Jol settle them on 25 September.
  Build the deck structure and the two worked routes now; carry the sentences from
  ROUTES-CONTROLLER-QUEUE-19Sep2026.md section B as placeholders and swap them on the 25th.
- The accuracy line, verbatim and only this: calibrated leads are within 20% of the outcome
  89% of the time and within 10% 82% of the time, on 2,915 real launches; blind results are
  reported as portfolios only, never as a single route. No other accuracy figure anywhere.
- Worked routes: SJC-TPE with China Airlines (the case already shown to the Taipei airlines)
  and ONE EUROPEAN transatlantic route, Bologna-New York or Genoa-New York (both exist as
  cases in the tool). Reason: the register of Routes World 2026 (ROUTES-ATTENDING-
  ORGANISATIONS-21Sep2026.md) shows half the airports in the room are European and the US
  is the largest single country; an Asian second example would speak to few of them.
- Pricing on the last slide: the published structure only (PRICING-HANDOVER-19Sep2026.md):
  £15,000 / £20,000 / £25,000 a year by airport size, three seats, 100 presentations
  included, plus "launch places this year on request". No discount figure, no number of
  places, no expiry until John rules (umbrella, Waiting on John, item 6).
- Nothing about any competitor on any surface. Nothing labelled illustrative. No figure
  without a source line in the same place. No feature that is not in the frozen build
  (day-of-week allocation, fare in the QSI score and the new aircraft types' economics are
  post-Routes and do not appear).
- The old deck Avia_Cortex_Process_and_Methodology.pptx (2 July) is the starting material,
  not the answer. Before reusing any slide, check it against Nick's methodology note (master
  list 3.3b says this check was never done) and report any contradiction to the controller
  in W3-STATUS.md rather than resolving it yourself.
- Product naming on every client surface: Meridian, published by The Aviation Observatory.
  Avia Cortex is a development name and never appears.
- Chart labelling: every chart states what it shows, the unit, the period and whether it
  is actual or forecast, on the chart itself.
- Dates: deck v1 to Jol and Nick by 3 October; pack tuning and PDF render by 8 October;
  imagery rights fix by 8 October; demo-path freeze 10 October.

## Controller's answers to W3-STATUS.md v1 (19 Sep, 22:00)

- Q1 item 1, one engine or two: escalated to John as umbrella item 25 with three honest
  routes and a 26 Sep date; W3 does not write around it and does not finalise slides 4-5
  until it lands. The sentence in item 25(b) is the fallback wording; build the slide to
  hold it and swap if (a) lands.
- Q1 item 3: the two July validation figures stay out. Ruled.
- Q3 imagery: John's ruling recorded; run the probe on the workstation and let the measured
  gap decide the second source, exactly as you set out. No contract before Routes.
- Decks already sent (the 94 bare JPEGs): nothing is re-sent; post-Routes review of
  C:\assets\engagement goes on the master list. Umbrella item 27.
- The mailbox your image-source accounts wait on: the controller has recommended moving the
  domain's DNS to Cloudflare now so Email Routing gives an inbound address (umbrella item 20,
  W2 does it). Plan on it from 26 Sep; if it slips, sign up under an Avia address and
  transfer later rather than block the probe's follow-through.
- Slide 8 carrier: with John (item 26).
- The PDF method in Q4 is approved as written. Build it.
- Slides 7 and 8 need runs on the frozen build; take them from the workstation after the
  10 Oct freeze, not before, so the deck's numbers are the show's numbers.
- Commit message hygiene: one message file per commit; a reused file is a wrong subject
  line forever. Noted, not repeated.

## What the controller wants in W3-STATUS.md after session 2
## Sweep of 19 September, 23:30: rulings that reach every workstream

- THE PACK PROMISE: every outgoing word says the pack "follows the same day" until the sender
  is out of test mode and one pack has been sent and received over a hotspot at the 11-12
  October trial. "Within 30 minutes" only after that. Ruled by the controller.
- WORKED ROUTES: John's standing rule for demo and marketing material is never to use an
  airport Avia has worked for. The deck's routes, the host's rehearsed routes and the post-1
  chart all currently do. Umbrella item 28 asks John to rule by 23 Sep; candidate pair
  BRS-EWR plus a US origin. Do not build anything route-specific that is expensive to redo
  until it lands; everything else proceeds.
- PRICING: RULED by John, see the section below; item 29 is closed.
- TIER SHAPE: the published grid; airlines and advisers "quoted".
- FEEDBACK QUESTIONS: W5's card wording is the only wording; W4's manual and any W2 screen
  quote it with its version.
- DNS: aviationobservatory.com moves to Cloudflare in the week of 22 Sep (W2); Email Routing
  gives the domain an inbound address; W6's site deploys on Cloudflare Pages from the same
  zone; Postmark records re-verified after the move.

- W3 specifics: John's 3 October date for all four items and the PDF/HTML split (PDF = the
  full researched pack, HTML = the 20-minute pitch page) are recorded in the umbrella and
  accepted. Build slides 1-6 and 9-10, the PDF render and the pitch page now; hold slides 7-8
  and the pack examples until item 28 names the routes (23 Sep), then run them on the build
  29 Sep-1 Oct as planned. The accuracy sentence (item 25) and the probe run (item 33) are
  with John with your dates.


1. Probe result: coverage by tier of airport, and the recommended second source with the
   licence terms actually read.
2. Slides 1-6, 9-10 built in the Observatory palette, with the placeholder sentences, and
   the en-GB and author metadata verified after build.
3. The print stylesheet and the render step, with one rendered A4 PDF of an existing pack.

## What the controller wanted after session 1 (answered)

1. Where the 2 July deck and Nick's methodology note actually are (path), and whether they
   contradict each other anywhere.
2. The slide-by-slide outline of the ten slides, one line each, before any slide is built.
3. Which imagery the library holds for SJC, TPE, BLQ, GOA, JFK and EWR, with rights status.
4. How the PDF render will be produced and what it needs installed on the workstation.

## Pricing, ruled by John 19 September (supersedes item 29's proposal)

Held until November. The grid does not go on the site before Routes. The host states the
number in person when asked, in the published wording and no other (£15,000, £20,000 or
£25,000 a year by airport size, three seats, 100 presentations included), and says nothing
about an overage rate or a discount because neither exists; it goes to the visitor in writing
within 48 hours in the follow-up one-pager; the grid is published in November with the
order-ready milestone. This wording replaces "on request, limited places".

## 20 September: ORDER-READY IS NOW 21 OCTOBER (John)

A large engagement has been suspended and cash matters sooner. John does not expect a
signature at Routes, but Avia must never be the delay: pricing agreed and every document ready
at Routes or immediately after, so a client can be running and paying in November.
For W3: the deck's last slide adds one line: "agreement and onboarding available immediately
after Routes". Nothing else changes.

## 20 September: PRICING DECOUPLED (John). Supersedes every earlier pricing line above.

Two decisions, kept apart. (i) LAUNCH TERMS are firm and decided before Routes: a fixed
year-1 price for a fixed number of launch parties with an expiry (John's illustration, not
yet the ruling: £5,000 for five parties); offered in writing on the one-pager at the five
meetings and to any qualified buyer who asks; the agreement is signable on those terms at
Routes. (ii) STANDARD PRICING (the £15,000 / £20,000 / £25,000 grid or whatever the feedback
says) is held in mind, NOT published and NOT quoted at Routes; it is set and published after
the show. Year 2 for launch clients: the then-published list less a stated loyalty discount,
no obligation to renew (controller's view; John rules the discount by 3 Oct). Website: no
prices until November. The host's sentence, if asked: "launch terms for the first [N] are
£[X] for year one; our standard pricing is published after Routes." The numbers (X, N,
expiry, loyalty discount, overage rate, payment terms, entity) are John's by 3 Oct; slots
until then.
W3: slide 10 carries the launch terms (slots for X, N, expiry) and "standard pricing published
after Routes"; the grid comes off the slide.

## 20 September, final: THE LAUNCH OFFER (John). Supersedes the two pricing sections above.

Year 1 at 50% of list, year 2 at 75% of list, year 3 at 85% of list, then list; no
obligation to renew. LIST is the banded standard price by airport size (£15,000 / £20,000 /
£25,000 a year, three seats, 100 presentations), so year 1 is £7,500, £10,000 or £12,500,
fixed in pounds at signing; years 2 and 3 follow the list as published at each renewal.
Add-on options (Global Forecast, Design Day, per-route study if priced): 50% off if adopted in
year 1, 75% of list if adopted in year 2. Conditions: the client accepts launch bugs with
understanding (the known-issues list), gives references, allows use of its name and brand in
Avia's marketing, and signs by 30 NOVEMBER 2026. The list is quoted in writing to qualified
buyers on the one-pager and in the agreement; it is not published on the website until
November. Still open (umbrella item 6, by 3 Oct): number of places, overage rate, payment
terms, size thresholds, entity.
W3: slide 10 carries the launch offer (50% / 75% / 85%, the three bands, the 30 November
deadline) and the four conditions in one line each.

## 20 September: item 28 CLOSED (John). The worked routes stay SJC-TPE and Bologna-New York;
more may be added later. Build to them now; nothing waits on a route decision. The carrier
for Bologna-New York is still item 26.
W3: slides 7-8 and the pack examples proceed on these two routes; runs 29 Sep-1 Oct as planned.
