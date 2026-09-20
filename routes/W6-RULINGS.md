# Controller to W6: rulings and instructions

Written by the programme controller (the Fable chat), rewritten whenever a ruling lands.
W6 reads this at the start of every session and acts on it; W6 never edits it. W6's own
statements go in W6-STATUS.md, which the controller never edits. John pastes nothing.
Read routes/README.md first: it says who writes which file, who owns which code, and how conflicts are reported and resolved.

## RULING 20 September 2026, 14:00 (final, replaces the 13:00 text): TIERS BY USAGE, NOT AIRPORT SIZE (umbrella item 37). SUPERSEDES every "by airport size, three seats, 100 presentations" and every "£15,000 / £20,000 / £25,000" wording below

PROVISIONAL from 20 September 15:00: John has moved pricing to a dedicated chat (W8,
routes/W8-RULINGS.md). The table below is the working assumption until
routes/PRICING-DECISION-2026.md says FINAL (target 26 Sep, hard 3 Oct). Draft structure
around it; do not finish any pricing surface (schedule, one-pager block, host sentence, site
copy) until that file is FINAL, then quote it with its version.

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

## Scope (commercial plan sections 7, 8 and 9; umbrella section 4 and W6)

1. MESSAGING. The four sentences (one-liner; three sub-messages; the offer; the accuracy
   line), drafted in ROUTES-CONTROLLER-QUEUE-19Sep2026.md section B. W6 refines them into
   two or three variants each for John and Jol to choose from by 23 September; John settles
   them by 25 September. The accuracy line is not a variant: it is verbatim and fixed.
2. INVITATIONS to the five pre-arranged meetings, drafted in John's voice, one paragraph
   each, for John to send 26-29 September through the Routes meeting system or email. The
   five are John's pick from ROUTES-ATTENDING-ORGANISATIONS-21Sep2026.md section 3 (he has
   agreed the buyer-test list: Birmingham, Dublin, Vienna, Dallas Fort Worth, Milan SEA;
   reserves there). Each invitation names the route Avia will pre-run for them; W6 proposes
   the route per airport from public pitching activity, stated as a proposal.
3. MARKETING CALENDAR, drafted for approval, never posted by you: week of 22 Sep, John's
   LinkedIn post announcing the stand and "run your route live", with one real chart (the
   SJC-TPE time-of-day curve, from the tool, source line on it), and an email to the client
   and contact list ("book ten minutes on the stand"); week of 29 Sep, the Routes exhibitor
   listing and app profile text, and post 2 (the three classes of number in plain words);
   week of 6 Oct, post 3 (a worked route, the pack as a PDF image); week of 13 Oct, the
   final "see us at F174" note; during the show, one post a day from the stand with the
   visitor's permission and no numbers that identify their pitch. Every piece goes to Jol
   for copy and to John for approval; nothing is published by a chat.
4. WEBSITE, REWRITTEN after John's rulings in your chat. The site to launch is THE AVIATION
   OBSERVATORY site (repository at E:\Avia\Observatory Website, 22 pages, Eleventy; naming
   register: `tao-website`), on aviationobservatory.com, deployed by Avia on Cloudflare Pages
   from the repository, not from the workstation; the IT firm is not on this path. Order of
   work: (1) the repository gets a GitHub remote and is pushed THIS WEEK (John runs your
   block; tool standard 1; until then 22 pages sit in one folder); (2) the competitor comes
   out of the header, footer and every page (eight files) and the prices come out of the
   seven files that carry them, held until November (umbrella item 29); (3) the ruled
   accuracy line goes on the Meridian page, verbatim; (4) a clean-clone build proves the
   Eleventy config; (5) Cloudflare Pages deployment on the zone W2 moves in the week of 22
   Sep, with a preview branch so nothing publishes by accident; (6) the packs are hosted on
   the workstation tunnel at a pack hostname (W2 mechanics, by 8 Oct), linked from the site.
   W6 edits the repository directly through blocks John runs (silence to 23 Sep: yes). A
   review branch and preview before any editor is pointed at the live site; the editor moves
   to this site after Routes.
5. MEETINGS LOGISTICS: each of the five meetings has its route pre-run, the pack printed,
   Optimise live, and the one-pager left behind; W6 keeps the schedule and the pack list.

## Rulings and facts you build to

- Nothing about any competitor in any material, post, page or email. The staging site
  carries a competitor comparison page: it is WITHHELD from the launch (umbrella item 11
  awaits John's confirmation; build the plan on withholding it).
- Pricing on the site: the published grid (£15,000 / £20,000 / £25,000 a year by airport
  size, three seats, 100 presentations included, sales-led) goes live only with John's
  sign-off, per PRICING-HANDOVER-19Sep2026.md section 3 item 5; the "provisional, not for
  publication" banner comes off only then. No discount, places or expiry anywhere until
  John rules (umbrella item 6).
- The accuracy line, verbatim and only this: calibrated leads are within 20% of the
  outcome 89% of the time and within 10% 82% of the time, on 2,915 real launches; blind
  results are reported as portfolios only, never as a single route. No single-route blind
  figure on any surface. The one-sentence explanation of what it describes is open
  (umbrella item 25); until it lands, no copy elaborates on it.
- Product naming on every client surface: Meridian, published by The Aviation Observatory.
  Avia Cortex never appears. Avia Solutions is the consultancy; The Aviation Observatory
  publishes the products.
- Chart on the first post: from the tool, on the current build, unit and period and
  "forecast" stated on the image, source line on it. No chart from research or memory. The
  ROUTE is with John (umbrella item 28); your BRS-EWR proposal is the controller's candidate
  too. Silence to 23 Sep: BRS-EWR.
- The invitations and posts are drafts in John's voice; he edits and sends. The email to
  the contact list goes from John's Avia address; the pack emails go from
  aviationobservatory.com (W2's domain, Postmark).
- Voice for copy: Avia house style, UK English, no em or en dashes, active voice, no
  consultant-generic words; short sentences on LinkedIn; "circa" not "approximately".
- Frankfurt, 21-23 October, stand F174. Suzanna McIntosh hosts.

## Dependencies

- Jol: copy on everything; the site rewrite. W6 writes what Jol must finish, by page, with
  a date, and John carries it to Jol.
- The IT firm: the cutover. W6 writes the request in one paragraph for John to send.
- W2: pack files and URL rule (for hosting); the sender domain.
- W3: the SJC-TPE curve image for post 1 and the pack PDF image for post 3.
- The Observatory site repository is separate from the Meridian repo; C:\src\avia-website
  (the editor) is requested from John as a folder grant (umbrella item 32).


## Sweep of 19 September, 23:30: rulings that reach every workstream

- THE PACK PROMISE: every outgoing word says the pack "follows the same day" until the sender
  is out of test mode and one pack has been sent and received over a hotspot at the 11-12
  October trial. "Within 30 minutes" only after that. Ruled by the controller.
- WORKED ROUTES: John's standing rule for demo and marketing material is never to use an
  airport Avia has worked for. The deck's routes, the host's rehearsed routes and the post-1
  chart all currently do. Umbrella item 28 asks John to rule by 23 Sep; candidate pair
  BRS-EWR plus a US origin. Do not build anything route-specific that is expensive to redo
  until it lands; everything else proceeds.
- PRICING: RULED by John in your chat, held until November; the umbrella records it as item 29
  and the other workstreams have the wording. Your status v5 is read; the remaining item for
  you is the deck's last slide, which carries the grid (W3) and is unaffected.
- TIER SHAPE: the published grid; airlines and advisers "quoted".
- FEEDBACK QUESTIONS: W5's card wording is the only wording; W4's manual and any W2 screen
  quote it with its version.
- DNS: aviationobservatory.com moves to Cloudflare in the week of 22 Sep (W2); Email Routing
  gives the domain an inbound address; W6's site deploys on Cloudflare Pages from the same
  zone; Postmark records re-verified after the move.

- W6 specifics: your five conflicts are resolved above and in the umbrella (scope 4 rewritten;
  IT firm off the path; pricing per item 29, which adopts your recommendation for the site;
  chart per item 28; decision 7 recorded as answered with W2 owning the pack hostname). Your
  status v3 is read. Post 1 and the list email wait on item 28's route only.

## What the controller wants in W6-STATUS.md after session 2

1. The repository push confirmed with the remote's URL and HEAD.
2. The competitor and price removals as a file list, built on a clean clone.
3. Invitations updated to "follows the same day" and to item 28's routes when ruled.

## What the controller wanted after session 1 (delivered)

1. The four sentences in two or three variants each, ready for John and Jol.
2. Five invitation drafts with the proposed pre-run route for each.
3. Post 1 and the contact-list email, drafted.
4. The site launch plan: pages, owners, dates, the two takedowns, the IT firm's paragraph.

## 20 September: ORDER-READY IS NOW 21 OCTOBER (John)

A large engagement has been suspended and cash matters sooner. John does not expect a
signature at Routes, but Avia must never be the delay: pricing agreed and every document ready
at Routes or immediately after, so a client can be running and paying in November.
For W6: the five invitations and the follow-up emails say plainly that an agreement and
onboarding are available immediately after Routes for airports with budget this year. The
website's November pricing ruling is unchanged.

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
W6: messaging sentence 3 (the offer) becomes the launch terms with slots; the site's
November pricing ruling is unchanged; invitations may say launch terms are available at the
meeting.

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
W6: messaging sentence 3 is the launch offer in one sentence; invitations say launch terms
are available at the meeting and close on 30 November. Website: no prices until November.

## 20 September: item 28 CLOSED (John). The worked routes stay SJC-TPE and Bologna-New York;
more may be added later. Build to them now; nothing waits on a route decision. The carrier
for Bologna-New York is still item 26.
W6: post 1 uses the SJC-TPE time-of-day curve as first ruled; the BRS-EWR alternative is dropped. Post 1 and the list email can go to John for approval now.
