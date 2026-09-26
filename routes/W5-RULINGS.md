# Controller to W5: rulings and instructions

Written by the programme controller (the Fable chat), rewritten whenever a ruling lands.
W5 reads this at the start of every session and acts on it; W5 never edits it. W5's own
statements go in W5-STATUS.md, which the controller never edits. John pastes nothing.
Read routes/README.md first: it says who writes which file, who owns which code, and how conflicts are reported and resolved.

## PRICING: routes/PRICING-DECISION-2026.md v1.0 is FINAL (John, 20 September 2026). It is the only file that states a price

Every price, band, discount, term and the host sentence come from that file, quoted with its
version. The provisional tier table that stood here from 20 Sep 14:00 is withdrawn. The axis is
AIRPORTS COVERED, not usage, not size, not seats: one airport £15,000; two to nine £22,500; ten or
more £30,000; the whole product in every band, no user count, no metering; fair use at 250
researched packs a year. Launch offer 50% / 75% / 85% as fixed cash, NO LIMIT ON PLACES, sign by
30 November 2026. Continuity discount 5% from the first renewal; multi-year 10% a year for three,
7.5% for two, as a locked cash schedule; 90 days' cancellation notice; Standard Terms plus an
Order Form per client. Route study £2,500 (on the price list, not led on); client catchment load
£3,500. Airlines are NOT sold, quoted or priced anywhere (Sabre licence); advisers price on
request. Read the file's section 10 for your own workstream's changes and section 11 for the
twenty answered decisions.

W5: rebuild to the file. The size-banded table goes in full; bands by airports covered with
the third launch row new (£15,000 / £23,200 / £27,050); Standard Terms plus an Order Form;
90 days' notice; seats become the corporate-domain term with no count and no consultant seat;
the pack cap becomes the fair-use wording; slots 2 and 7 close "none", slot 3 closes with no
figure; a schedule of covered airports and a scope clause; the two spend questions on the
feedback card; the one-pager leads with the licence. Nothing piecemeal to the solicitor: the
whole document in the week of 6 October. Tick the finalisation checklist against the FILE, not
against the 20 Sep rulings above it.

## Scope (umbrella section 3, order-ready by 7 November; commercial plan 5 and 6)

W5 is the DOCUMENT half of order-ready: what has to exist on paper for the first paying
client to sign, be onboarded and be supported. The CODE half (per-client Cloudflare Access
policies and passwords, usage attribution from the Access identity in the R9 log, the lead
store, monitoring and the restart alert) is W2's and is not yours.

1. The two-page agreement: scope (named users, routes per month, presentations included,
   the review call), term and price from the published grid, the year-1 launch-customer
   discount and its expiry (figures from John, umbrella item 6; slots until then), the
   economics disclaimer exactly as it already reads in the tool, the licence position
   stated (OAG and Sabre confirmed verbally that outputs may be shared; letters chased), no
   liability for decisions taken on outputs, data handling (Avia stores no client data,
   outputs only), governing law England and Wales. Drafted for John's lawyer, not as legal
   advice; every clause that needs a lawyer's eye is marked.
2. The invoice template and payment terms (30 days; sterling; VAT exclusive), Avia
   Solutions as author on the file.
3. The onboarding call script, 45 minutes: their first three routes, together; what to show,
   what to ask, what to leave them with.
4. The known-issues list a client receives at onboarding, current as of the freeze:
   day-of-week allocation not yet built; fare not yet in the QSI score; the new aircraft
   types not yet costable (valuation gap); anything Routes exposes, added after the show.
   Written so that a client who is told is a beta client, not a lost one.
5. The feedback card for the stand: five questions the host answers after each substantive
   demo (route; what impressed; what they questioned; what they asked for that we do not
   have; would they pay) and the one line in the pack email inviting a reply.
6. The support arrangement: a named address a named person reads daily, and the promise
   made in the agreement (response time), for John to staff.
7. The licence record: a one-page written record of the verbal confirmations from OAG and
   Sabre (date, participants, what was said), for John to complete and file on Egnyte,
   which stands in for the letters until they arrive.
8. The follow-up sequence after Routes: 48 hours (John or Jol, personally, with the pack and
   the one-pager to the qualified), then two weeks; and the one-pager itself: what the
   client gets, what they give (feedback, a reference if satisfied, patience on hosting),
   price and term, what is excluded. Three tiers at most; the shape is open with John
   (umbrella item 7: the published grid prices by airport size and quotes consultancies on
   portfolio; the commercial plan has Airport, Airline and Adviser tiers).

## Rulings and facts you build to

- Nothing invented: no price, discount, places, expiry, response time or legal wording
  presented as settled that John has not ruled. Slots, marked, with what happens if
  unfilled by 3 October (the offer falls back to "on request").
- The accuracy line, verbatim only: calibrated leads are within 20% of the outcome 89% of
  the time and within 10% 82% of the time, on 2,915 real launches; blind results are
  reported as portfolios only, never as a single route.
- Nothing about any competitor. Naming: Meridian, published by The Aviation Observatory;
  the contracting entity is Avia Solutions Limited unless John says The Aviation Observatory
  Ltd (ask; do not assume).
- Every generated file: Avia Solutions as author and last-modified-by, en-GB proofing at the
  document default, no run-level language elsewhere, verified after build. Word for the
  agreement and the one-pager, Excel for the invoice template, markdown in
  C:\AviaDev\routes\ for the scripts and lists.
- Dates: agreement and one-pager drafts to John by 3 October so his lawyer has October;
  feedback card to Jol by 8 October; known-issues list frozen 10 October; everything
  order-ready by 7 November.

## What the controller wants in W5-STATUS.md after session 1
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

- W5 specifics: your two conflicts are fixed in the umbrella (the W5 row rewritten; item 20
  cut to one recommendation). Tier shape ruled as you recommended. Contracting entity is
  umbrella item 31, no default. The one-pager's grid stands; the website holds its prices
  until November (item 29), so the one-pager is the first written price a prospect sees, which
  is what the 19 Sep decision intended. Proceed with the invoice, onboarding script,
  known-issues list and licence-record form.


1. The agreement draft with its marked slots and lawyer flags.
2. The one-pager draft and the question of tier shape put crisply for John.
3. The feedback card and the pack-email line.
4. The list of facts only John can supply, numbered.

## [SUPERSEDED by PRICING-DECISION-2026.md v1.0 where they differ] Pricing, ruled by John 19 September (supersedes item 29's proposal)

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
For W5: every document lands by 10 October, not 3 November: agreement (solicitor's review in
the week of 6 Oct; John supplies the slot), one-pager WITH the numbers John rules by 3 Oct,
invoice template, onboarding script, known-issues list (frozen 10 Oct), licence-record form,
support arrangement, follow-up sequence. The one-pager is PRINTED for the five meetings and
handed to any qualified buyer who asks. Add a slot for a per-route study product (umbrella
item 35): a Meridian route study, the researched pack for one route, priced per route,
invoiced on delivery, no licence; it goes first on the one-pager if John prices it. Payment
terms in the agreement: controller's view is annual in advance, invoice on signature, 14
days, with a small stated discount for payment within 14 days; slot until John rules.

## [SUPERSEDED by PRICING-DECISION-2026.md v1.0 where they differ] 20 September: PRICING DECOUPLED (John). Supersedes every earlier pricing line above.

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
W5: the agreement's price clause is the launch price for year one with the year-2 wording
above; the one-pager leads with the launch terms and says standard pricing follows after
Routes; the grid does NOT appear on the one-pager.

## [SUPERSEDED by PRICING-DECISION-2026.md v1.0 where they differ] 20 September, later: the launch-cohort clause structure (John's working position)

Price clause, with slots for the numbers John rules by 3 Oct: year 1 at a FIXED pound figure
£[X] (John's intent: circa 50% of the standard price he has in mind), for the first [N]
launch clients, offer expiring [date]; year 2, at the client's option, at 75% of the standard
price published by then, capped at [twice] the year-1 price; year 3 onward at the published
standard price; no obligation to renew at any step. The discount is given in return for
structured feedback, a reference if satisfied, and tolerance on hosting while it settles
(these are the client's obligations in clause 3 and are the consideration for the price).
Draft it so the step-up reads as the deal signed, not a rise. Flag for the solicitor: the
"published standard price" must be defined (Avia's price list as published on its website
at the renewal date) or the year-2 clause is unenforceable.

## [SUPERSEDED by PRICING-DECISION-2026.md v1.0 where they differ] 20 September, final: THE LAUNCH OFFER (John). Supersedes the two pricing sections above.

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
W5: the price clause is this, verbatim in structure; "list" is defined as Avia's published
standard price by airport size at the renewal date; the client obligations are the four
conditions above; the signing deadline of 30 November 2026 is in the offer, not the term.
The one-pager leads with "half our list price in year one for launch clients who sign by
30 November" and shows the three bands.

## [SUPERSEDED by PRICING-DECISION-2026.md v1.0 where they differ] 20 September, later: term, renewal and Avia's exit (John)

1. PRICE SCHEDULE: a table on the one-pager and in the agreement showing the client's band
   over three years with list inflated at a stated flat 3% a year FOR ILLUSTRATION ("Avia
   reviews its list annually; this schedule assumes 3% a year"; name no index), and the
   launch client's THREE FIXED CASH PRICES beside it: year 1 at 50% of the band, year 2 at 75%
   of the band times 1.03, year 3 at 85% of the band times 1.03 squared, each rounded to the
   nearest £50 and stated in pounds. Those three figures are contractual; nothing in years
   1-3 refers to a future list. From year 4, the published list at the time.
2. RENEWAL: annual, automatic unless the client gives notice at least one month before the
   renewal date; Avia sends a renewal notice three months before and a reminder two months
   before. The opt-out from auto-renewal is CONDITIONAL, not priced: available only to a
   client that declares in the agreement that its procurement rules do not permit evergreen
   terms; no premium for it. For every other client the clause is standard and stays, and
   the launch terms are offered on the standard agreement as it stands. Solicitor flag on
   the declaration wording.
3. AVIA ENDING OR SUSPENDING THE SERVICE, for any reason including loss or restriction of a
   data licence (OAG, Sabre): Avia gives [three] months' notice where it can; the client
   receives a pro-rata refund of the unused part of the year's fee within 30 days; the client
   keeps every output already delivered and may continue to use it; no further liability on
   either side. Solicitor drafts; W5 marks the clause and the notice period as a slot.
4. The cash-flow terms already proposed stand as slots: annual in advance, invoice on
   signature, 14 days, a small stated discount for payment within 14 days.

## [SUPERSEDED by PRICING-DECISION-2026.md v1.0 where they differ] 20 September, later still: escalation and product change (John)

5. ESCALATION, in every agreement and on the one-pager: "Avia's standard prices are reviewed
   each year and move by at least inflation." Clause: at each renewal the price increases by
   not less than the change in UK CPI (ONS, all items, twelve months to the preceding
   December), and Avia may set a higher increase on the notice given for the renewal. The
   launch cohort's three fixed cash prices are the stated exception for years 1-3; from year
   4 the client is on the published list with the same escalation. The illustration table
   (item 1 above) keeps its flat 3% and says "for illustration; the contractual mechanism is
   clause [n]".
6. NEW FUNCTIONS: new modules and options are offered as priced options the client may accept
   at the prices then published (launch clients: 50% if adopted in year 1, 75% in year 2).
   Where Avia incorporates a function into the core product, Avia may increase the core price
   above the annual escalation at the next renewal, on the same notice as the renewal, and the
   client keeps its right not to renew. State it plainly in the agreement and in one line on
   the one-pager: the expectation is set in the first contract.

## [SUPERSEDED by PRICING-DECISION-2026.md v1.0 where they differ] FINALISATION CHECKLIST for the agreement and one-pager (John, 20 Sep: "cover all of this")

Before either document goes to the solicitor (agreement) or to print (one-pager), W5 confirms
each of these is present, in these terms, and lists them ticked in W5-STATUS.md:

1. Launch offer: 50% / 75% / 85% of the client's band in years 1-3, as three fixed cash
   figures in pounds, rounded to the nearest £50; year 4 onward at the published list.
2. The three-year table with the flat 3% illustrative inflator, labelled "for illustration".
3. The banded list quoted as the reference (£15,000 / £20,000 / £25,000; three seats; 100
   presentations); size determined from published passenger numbers in the quotation.
4. Add-ons at 50% in year 1 or 75% in year 2; new functions as priced options; core-price
   increases above inflation at a renewal where a function is folded into core.
5. Escalation: at least UK CPI (ONS, twelve months to the preceding December) at every
   renewal; the launch years as the stated exception.
6. Term and renewal: annual, automatic; client cancels with one month's notice before the
   renewal date; Avia notifies at three and two months; conditional opt-out for clients
   declaring their procurement rules forbid evergreen terms, no premium.
7. Avia ending or suspending the service: notice, pro-rata refund within 30 days, outputs
   kept, no further liability; loss of a data licence covered expressly.
8. Client obligations for the launch price: tolerance of launch bugs (the known-issues list
   attached), references, use of name and brand in Avia's marketing, signature by 30
   November 2026.
9. Payment: annual in advance, invoice on signature, 14 days, the early-payment discount if
   John rules one; VAT exclusive; sterling.
10. Overage rate for presentations beyond 100 (John's figure) and the review-call promise.
11. Licence position stated; the economics disclaimer verbatim from the tool; no liability
    for decisions taken on outputs; data handling (Avia stores outputs, routes run and the
    user, no client data).
12. Contracting entity, registered number and office; governing law England and Wales.
13. Every lawyer flag resolved or carried to the solicitor with a note; every slot filled or
    the fallback applied; author metadata and en-GB verified on the Word files.

## 21 September 2026: CONTRACTING ENTITY SETTLED (John). Overrides PRICING-DECISION-2026.md v1.0 decision 15

The Aviation Observatory Limited, company number 17411365, registered office 86-90 Paul
Street, London EC2A 4NE, is the party to every client agreement and issues every invoice.
Not Avia Solutions Limited. Slot 1 and one-pager slot G close with it; the solicitor gets the
Standard Terms in that name. Two order-ready facts the agreement must not contradict: PI
cover is being extended to TAO Ltd (no client contract is signed before it is in place; the
agreement's insurance line is worded to the cover as extended, slot until the insurer's
proposal lands) and the invoice template carries TAO Ltd's bank details, which do not yet
exist (slot; the account is opened before the first invoice). VAT status: John states.

## 21 September 2026: the two spend questions, wording (controller, on W4's watchpoint)

The feedback card asks "what do you pay today for your data subscriptions", not a list of
supplier names. Same answer, no third-party name on a client-facing surface.

## Controller's sweep of W5-STATUS.md v4 (21 September 2026)

1. Conflict 1 (section 7 v section 11): you built to section 11, right. W8 owes v1.1.
2. Conflict 2, the quarterly review call: RULED OUT of every band. The file's list of what a
   licence carries is the list; a named Avia contact and one refresh call a year exist only in
   the Programme wrap-around of the old table, which is withdrawn. Nothing recurring in a
   person's time goes in without a price in the file. Question 5 closed. Scope item 1's line
   is superseded.
3. Conflict 3, the economics disclaimer naming Avia Solutions Limited: the clause names BOTH
   ("Avia Solutions Limited, on whose analysis the service is built, and The Aviation
   Observatory Limited"); the wording in the service itself is W1's to change before the freeze
   (app/aircraft_economics.py DISCLAIMER_FULL) and the controller takes that. Flag to the
   solicitor stands.
4. Conflict 4, the band table on the one-pager: RULED. The one-pager the five meetings see
   carries the single-airport price and "groups quoted on the airports covered"; the full
   band table goes on the Order Form and in the quotation to a group, not on the walk-up
   sheet. John's 3 August ruling stands over the 20 September line, which was written for
   the withdrawn usage tiers. Two one-pager variants are not wanted: one sheet, with the
   group line.
5. Judgement 1, twelve months to retire the service: adopted, with the data-licence route
   separate as you have it. Slot 2 closes at twelve months unless John objects (umbrella 47).
6. Judgement 2, non-exclusive jurisdiction: to the solicitor as you say.
7. Judgements 3 and 4: agreed. The licence record never comes back into the repository.
8. Watchpoint 4 (a new company with no trading history): right, and it is John's to answer;
   umbrella item 48 (accounts, insurance certificate, a parent-company letter of comfort from
   Avia Solutions Limited or the Holdings company, ready before the first procurement asks).
9. Your eight asks are umbrella items 31 (PI, bank, VAT), 34-style: solicitor slot (item 49),
   support (item 50), known-issues sign-off (Nick, ruled unless John objects), OAG and Sabre
   told of the party (item 51).

## 26 September 2026: a two-minute feedback card for John's own meetings (controller)

John wants feedback direct from his meetings, not through the hosts. W5 adds a two-minute
version of the feedback card for John: five lines (who, route discussed, what they liked, what
they questioned, next step), usable on paper and on a phone, exported with the lead store on
the evening of 23 Oct. Nothing else changes on the visitor card.

## 26 September 2026, night: THE PAIR IS 88 / 78 ON 6,524 (controller)

Umbrella item 55 is CLOSED (John, 26 Sep): calibration rule B, Sabre throughout, 6,524
launches, 88% within 20% and 78% within 10%; blind portfolios of twenty 94%. John's
sentence, verbatim, is the only accuracy statement on any surface: "When this model was used
to forecast the new routes that launched since 2016, 88% of its forecasts were within 20% of
what the route went on to carry and 78% within 10%, across 6,524 launches. The past does not
predict the future, but that is the record." Spoken: "about six and a half thousand". The
second-question answer: "calibrated means fitted on the full history of 6,524 launches and
graded on the same launches; on launches it never saw, a portfolio of twenty routes lands
within 20% of the actual total 94% of the time." Every file of yours that carries 89 / 82,
92 / 86, 2,915 or the DB1B grading sentence (W10-STATUS v14 lists: W5-ONBOARDING-SCRIPT.md, W5-ONE-PAGER-19Sep2026.md, W5-STANDARD-TERMS.md) is corrected in your
next session and before anything is sent or printed. The product goes live on 88 / 78 at the
next server restart.
