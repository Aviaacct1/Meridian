# Meridian: pricing and the commercial offer

Version 0.5 - DRAFT - 20 September 2026 - Avia Solutions - Commercial in Confidence

Written by W8. This is the only file in the Routes 2026 programme that states a price. Every
other document quotes this file and its version. Status is DRAFT until John writes "final" in
the W8 chat, at which point it becomes FINAL with that date and the controller points umbrella
item 37 at it.

Target 26 September 2026. Hard deadline 3 October 2026, when W5 sends the agreement to the
solicitor and the one-pager goes to print.

Every figure carries its source in the same sentence. A figure marked "W8 proposal, decision N"
is not yet John's; N is the number in section 10.

v0.5 replaces everything before it. Four shapes were proposed and withdrawn on John's rulings of
20 September: tiers carrying the long-term forecast, tiers carrying pack blocks, tiers by seat
count, and a flat per-airport rate. The axis is now the number of airports the licence covers.

---

## 1. What Avia is pricing, and what it cannot know yet

John's position, stated 20 September 2026 and governing this file.

- Avia has never sold a software product. What he dislikes as a buyer governs the design: a
  price set by what the buyer can pay rather than what the product delivers; limits on users;
  limits of use.
- The value cannot be known until it is sold. For one airport Meridian is the only route
  forecast they will have; for another it supplements an in-house or third-party forecast. That
  variation is in the buyer's starting point, not in what Avia hands over, so it cannot be
  priced.
- Value arrives over time, as airlines come to trust the forecasts rather than dispute them.
  A rise beyond launch and inflation will be hard to win later, because a board does not see the
  difference, so the day-1 price has to be close to right on little information.
- The researched pitch pack is useful against current practice, but it is AI-researched, so
  either simple and correct or deeper and carrying errors, and any firm with an AI tool could
  produce something like it. It costs circa $10 in tokens. It is therefore not what Avia sells.
- A limit on packs is rejected: it stops the client refining a pack and adds development and
  complexity.
- Seats do not work as the axis. No airport needs more than five and most run two or three, so
  the seat count has no range.
- No consultant holds a seat. A consultant with access could forecast for anybody.
- The accuracy record rests on the raw model, so an unconfigured airport still gets a very good
  forecast. Uploaded catchment lets an airport discuss its catchment accurately; it does not
  change the forecast much.
- Route development is often a GROUP function rather than an airport-by-airport one: five or six
  people at head office doing air service development for many airports.
- Groups drive value hard. A group that knows a single airport costs £15,000 is unlikely to pay
  much beyond £30,000 however many airports it runs, and at £50,000 it would employ a full-time
  resource and build its own model instead.
- The requirement: simple to understand, justifiable, and not likely to inhibit take-up;
  avoiding the £15,000-for-small and £30,000-for-large problem while a large buyer pays circa
  £25,000 to £30,000 and feels it is getting value.

**The axis that survives all of that is the number of airports the licence covers.** It is not
size, because Heathrow covering one airport pays the same as a 1mppa airport covering one. It is
not a limit on use, because nothing in the product is capped. It is not seats, which have no
range. It is scope, which the buyer declares, and it tracks value because an airport has only
one airport's worth of route development to do, while a group head office has an estate's worth.

**The day-1 problem is smaller than it looks.** The licence model of 7 August
(`Avia_QSI_Licence_Model_07Aug2026.xlsx`) puts the fixed base at £526,121 and break-even at 27
to 36 clients depending on price, against a target of 100. The price does not carry the fixed
base; client count does. Section 8 sets out what that means for the numbers below.

**Three answers to "value goes up and the price cannot".**

1. **Publish the accuracy record every year, dated, with that year's n, as something the client
   receives under the agreement rather than a page on a website.** It is the only way a board
   that never touches the tool sees the difference between what it bought in 2026 and what it
   holds in 2029, and it is the same number the purchase was made on. The back-test already
   produces it. Decision 9.
2. **New value arrives as new products at new prices, never as a higher price for the old one.**
   The long-term forecast is the first instance and John has already ruled it that way.
3. **Fix a launch price for three years and never longer.** The clients most likely to become
   heavy users are the ones a long fix would hold at a 2026 price.

---

## 2. The licence

| Airports covered | List, a year |
|---|---|
| One airport | £15,000 (John, 20 Sep, item 37) |
| Two to nine airports | £22,500 (John, 20 Sep, item 37) |
| Ten or more, the whole estate | £30,000 (W8 proposal on John's read of what a group will pay, decision 1) |

Three bands, £7,500 apart. Two of the three list prices are John's of 20 September and are
unchanged, so nothing already carried into W3, W4, W5 and W6 becomes wrong.

**Nothing else varies between the bands.** Every licence carries the whole product: route leads,
route forecast, optimised route forecast, schedule sizing, route economics, Watch monitoring,
expert mode in full, unlimited runs and scenarios, unlimited standard forecast packs, unlimited
researched airline pitch packs under the fair-use clause, every download, the client's own logo,
colours and fonts on the outputs, and named users on the operator's corporate email domain with
no count attached. Nothing that affects the quality of the answer is ever held back, which is the 7 August 2026
ruling that Avia may price convenience and scale but never the quality of the answer.

### The cross-check that says these are not arbitrary numbers

Take John's own observation on team sizes and run it across the bands. A single airport has two
or three people doing route development and pays £15,000, which is £5,000 to £7,500 a head. A
small group such as AGS or Milan SEA has three or four at group level and pays £22,500, which is
£5,600 to £7,500. A large group has five or six at head office and pays £30,000, which is £5,000
to £6,000. Every band lands at roughly £5,000 to £7,500 per person doing air service
development. Two independent ways of reading the problem, seats and estate, arrive at the same
prices.

### Analysis is unrestricted; production is scoped

Run, Optimise, schedule sizing, route economics, expert mode, the workbook and CSV downloads and
the standard Observatory-branded forecast pack work for **any city pair in the world**, on every
licence. An airport at SJC looking at what SFO, OAK and LAX would do on the route it is pitching
is a real benefit it does not have today, and it is not taken away from anybody.

The researched airline pitch pack, the client's own brand on outputs, route leads, the catchment
opportunity scan and Watch are for **covered airports**. The sentence a buyer repeats without
resentment: your brand goes on your airports' work.

The check belongs on the two output points, `/api/report` and `/api/pitch/start`, which the
7 August work records as the only two server-side exits. It leaves the analytical path
untouched. It is not needed before Routes, and it is a condition of the first multi-airport
contract, because from that moment the schedule of covered airports is the only thing holding
the price up. The Sabre audit's R9 log already records the origin airport of every run per
account, so the interim control exists without a build. Decision 8.

### Adding airports

Adding airports moves the client to the band for that count, at the full annual difference, with
the renewal date unchanged (John, 20 September 2026, item 37, applied to bands; pro rata is
gamed). During the launch years the launch percentage applies to the new band, so a launch client
that expands in year two pays 75% of the band it moves into. That is deliberately generous: it
makes expansion cheap in exactly the window Avia most wants it. Decision 2.

### Groups are quoted, not published

Multi-airport groups are quoted on their portfolio and the band table is not published beside
the single-airport price (John, 3 August 2026, recorded in `PRICING-HANDOVER-19Sep2026.md`).
That is also the answer to a small airport asking why a group pays £30,000 for forty airports:
the question does not arise, and if it ever does, airports run volume-based incentive schemes for
airlines themselves.

---

## 2a. What is being sold, stated honestly, because the price rests on it

John, 20 September 2026: **the researched pack is not as good as a handmade Avia study.** The
handmade one carried pages of detailed research from an expert analyst, laid out in the client's
preferred format, and adjusted on their feedback. That does not mean a client would refuse a
lower but good output that lets them run twenty routes a year or more rather than a handful.

That is the proposition and every client-facing surface follows it.

**The claim is not "as good as a consultant, cheaper". It is "not as good, and many times as
many."** A buyer told the pack is consultant-grade finds the gap within weeks and Avia loses the
renewal and the reference together. A buyer told it is a lower standard than Avia by hand, but
good, and that they can cover their whole route list with it, gets what they were sold.

**The two claims stay separate and are never mixed in one sentence.** The forecast is the strong
claim, with the published accuracy record behind it, and it rests on the raw model. The pack is
the volume claim. Neither borrows the other's argument.

**In a small client's own numbers the sentence writes itself.** Knock has paid circa £20,000 for
about six studies by hand. The single-airport licence is £15,000 for as many as they want. Four
times the coverage for a quarter less, without claiming the documents are the same.

**This positioning protects Avia's consultancy book rather than competing with it.** A pack that
matched the handmade standard would undercut Avia's own £3,300 to £5,000 job. A pack that is
honestly a lower standard sits underneath it and feeds it: an airport that runs twenty routes
finds two or three worth pursuing seriously, and those come back to Avia for the hand-built study,
the expert analyst research and the client's own format. Meridian creates consultancy demand.

**The gap is deliberate and the roadmap already names it.** Expert analyst research, the client's
preferred format and adjustment on feedback are the client template option at £5,000 (section 5)
and the Assured package deferred to 2027 (section 9). Nothing is missing by accident.

**Consequence for W3, W4 and W6.** The host says what the pack is not, unprompted, rather than in
answer to a complaint. W8's wording, for W4 to take or rewrite: "this is not the hand-built study
Avia would write for you. It is the same forecast with researched support around it, produced the
same day instead of in three weeks, and you can do it for every route on your list." No surface
anywhere claims consultant-grade research.

---

## 3. Unlimited packs, and the fair-use clause

John accepted on 20 September that the risk is low and that a fair-use clause is the way to
protect Avia in the early years while usage is observed, rather than overage limits. He also
accepted the risk that the cost of search rises over time, as unlikely to swing far enough to
change the answer.

The arithmetic, at John's $10 a pack converted at the 1.3451 in the 7 August licence model, so
£7.43 a pack:

| Packs in a year | Token cost | Share of a £15,000 licence |
|---|---|---|
| 150 | £1,115 | 7.4% |
| 200 | £1,487 | 9.9% |
| 250 | £1,859 | 12.4% |
| 300 | £2,230 | 14.9% |

A £15,000 licence stops contributing at 2,018 packs, or 504 at four times today's token price.
At 200 packs the contribution is £13,513 and the gross margin 90.1%.

Unlimited packs are now settled twice over. On cost, by the arithmetic above. And on
positioning, by section 2a: if the whole proposition is throughput, a cap destroys the only thing
being sold.

**Fair use as a clause in the terms with a stated number, never a counter on the screen.** W8
proposal, decision 3: "a reasonable volume of researched packs for one airport's own route
development programme; Avia will contact the client if usage passes 250 in a licence year."
Nothing blocks, nothing is invoiced, and no number appears in the product.

Two things carry the rest. The R9 compliance log already counts packs per account, so Avia can
see a runaway client and telephone them without building a commercial meter. And the product
answer to a user re-running a route to see whether the research comes out differently is to
**cache the research per city pair with an explicit refresh action**: the same route then returns
the same research unless new research is asked for, which removes the behaviour at close to zero
cost and makes the output reproducible, which the client needs anyway. That is a W1 or W2 item,
it is not before the freeze, and nothing here depends on it.

If the escalation clause ever has to carry a genuine rise in token cost, it already can: Avia may
set more than CPI in the renewal notice.

---

## 4. The launch offer, worked

Settled and not reopened (John, 20 September 2026, umbrella items 29 and 37): year 1 at 50% of
list, year 2 at 75%, year 3 at 85%, then list; three fixed cash prices for years 1 to 3, fixed in
pounds at signature, on a flat 3% illustrative inflator, rounded to the nearest £50. In return
the launch client accepts launch bugs against the known-issues list, gives references, allows use
of its name and brand in Avia's marketing, and signs by 30 November 2026.

| Airports covered | Year 1, 50% | Year 2, 75% | Year 3, 85% | Year 4, list | Three-year total | Three years at list |
|---|---|---|---|---|---|---|
| One | £7,500 | £11,600 | £13,550 | £16,391 | £32,650 | £46,364, a saving of £13,714 |
| Two to nine | £11,250 | £17,400 | £20,300 | £24,586 | £48,950 | £69,545, a saving of £20,595 |
| Ten or more | £15,000 | £23,200 | £27,050 | £32,782 | £65,250 | £92,727, a saving of £27,477 |

Reference list by year, to the nearest pound (W5 judgement call 1, so a buyer with a calculator
does not arrive £50 below the printed cash price):

| Airports covered | Year 1 | Year 2 | Year 3 | Year 4 |
|---|---|---|---|---|
| One | £15,000 | £15,450 | £15,914 | £16,391 |
| Two to nine | £22,500 | £23,175 | £23,870 | £24,586 |
| Ten or more | £30,000 | £30,900 | £31,827 | £32,782 |

Source for every cash figure: W8 arithmetic on John's ruled percentages and inflator, from the
list prices in section 2. The 3% is the illustration; the contractual mechanism is escalation at
not less than UK CPI (section 6). The first two rows are the figures W5 has already built and
verified in the agreement and one-pager, so only the third row is new work.

**Number of launch places: ten** (W8 proposal, decision 5). The limit is Avia's onboarding
capacity in November and December. Ten against 353 registered airport organisations
(`ROUTES-ATTENDING-ORGANISATIONS-21Sep2026.md`, section 1) still reads as limited.

**Years 2 and 3 are fixed cash at signature, not the list as later published** (W8 proposal,
decision 6). Umbrella item 29 says both and they cannot both be true; W5 has drafted fixed cash
in clause 4 and W8 agrees. A launch client is asked for tolerance, references and its brand in
exchange for certainty, and a client told years 2 and 3 may move has not been given certainty.

---

## 5. Options

Offered at 50% of list if adopted in year 1 and 75% in year 2 (John, 20 September 2026, item 29).

| Option | Price | Basis | Source |
|---|---|---|---|
| Meridian route study, one route | £3,500 | per route, invoiced on delivery, no licence, delivered within five working days | W8 proposal, decision 4; umbrella item 35 |
| Client's own catchment loaded | £2,500 | one-off per airport, one price, no banding | W8 proposal, decision 7 |
| Client template mapping | £5,000 | one-off, bespoke, with the fit caveat | John, 20 Sep, item 37 |
| Cortex API | from £15,000 a year | on request, when available | `PRICING_AND_SCOPE_07Aug2026.md` |
| The long-term forecast product | priced separately when it exists | a separate software product that integrates with Meridian | John, 20 Sep |

**The route study is the purchase one person can sign, and it is the answer to the small
airport.** A licence needs a board and procurement that will not clear before the spring for most
of the room in November; a study needs neither.

The price is anchored in Avia's own book, all points John's of 20 September 2026 and all
tentative. Knock, a client of twenty years with small budgets, has paid circa £5,000 for one
forecast, circa £20,000 for about six, and £6,000 for five high-level forecasts WITHOUT
presentations. Tampa paid $40,000 for ten, circa £4,000 each
(`Avia_QSI_Licence_Model_07Aug2026.xlsx`).

Those are not the same product, and the gap between them is the finding. A forecast alone is
circa £1,200. A finished job with the presentation is circa £3,300 to £5,000. **So roughly 70% of
what a small airport pays Avia is the presentation, not the forecast**, which matches John's own
statement that most of Avia's time on a Knock job goes on the presentation.

That qualifies section 1's reading of the researched pack, and section 2a states where it
lands. The pack is reproducible by a group with its own analysts, it is not as good as the
handmade study, and it is also the majority of what a small client pays Avia for. All three
hold. At £3,500 a Meridian study sits
at the bottom of the finished-job range, which is right for a machine-produced document, and
undercuts the single-forecast price by 30%.

**A bare forecast at circa £1,200, workbook only and no presentation, is a possible third product
and is NOT proposed here.** Twelve would equal the single-airport licence, so the ladder would
work, but it carries a sales cost against a small margin. If a small airport would pay £10,000 a
year for the licence, that is the better answer than a £1,200 forecast.

**Four studies is £14,000 and five is £17,500, so past four routes a year the single-airport
licence is cheaper than buying studies.** That is the sentence for the stand.

**Whether Knock is a licence buyer is now an open question with a cheap test attached.** Its
spend is episodic and circa £10,000 a year at its heaviest, so £15,000 is more than it spends
today. John's read, 20 September: Knock might well buy at £10,000 a year rather than pay
consultants, but only if it knew the presentation was good enough, and there may be a niche of
small airports that do not buy today and would buy this at the right price. That cannot be known
from here.

**THE KNOCK TEST, W8's recommendation and the cheapest evidence available anywhere.** Run Meridian
on a route Knock cares about, send the pack, and ask the two questions that follow from section
2a: is this good enough to put in front of an airline, and would twenty of these a year be worth
more to you than five of ours by hand. Not whether it matches the handmade study, because John
has already answered that and it does not. Twenty years of relationship means the answer is
honest rather than polite, and September rather than November means W3 can still act on it.
Decision 10.

**If the answer is £10,000, the mechanism is not a passenger band.** Two routes reopen nothing:
the multi-year prepay, which is already one of the four named discounts and matches Knock's own
two-yearly budget cycle, or quarterly payment, which helps a cash-constrained airport more than a
prepay does since a prepay asks for more up front than Knock spends today. Those pull in opposite
directions and the test should decide which, not a guess.

**What the niche would be worth, recorded so the question is not lost.** If a population of small
regionals exists below the Routes World 353 and a £10,000 product reached fifty of them, that is
£500,000 a year, which roughly doubles the independent licence revenue in section 8. It is a 2027
market, it depends entirely on the pack being good enough, and the Knock test is the first read
on it.

**The catchment load is sold as consistency and credibility, never as accuracy** (John, 20
September 2026: the accuracy record rests on the raw model and an uploaded catchment does not
change the forecast much). What it buys is a team that can defend the catchment numbers in an
airline meeting because they are the airport's own, and one agreed set of numbers rather than
five people producing five different answers.

**No catchment banding.** `PRICING_AND_SCOPE_07Aug2026.md` priced catchment at £2,500 solo and
£5,000 shared off `airport_catchment_geo.csv`. That file has 71 rows with a blank classification
and no code in the product reads it, so the banding has never been exercised. One price cannot be
argued about and can be banded in 2027.

---

## 6. The terms

**Renewal.** Annual and automatic. The client cancels with at least one month's notice; Avia
notifies at three months and two months. A client whose procurement rules forbid evergreen terms
may opt out of automatic renewal on declaring so, at no premium (John, 20 September 2026).

**Escalation.** Not less than UK CPI, ONS all items, twelve months to the preceding December,
with Avia able to set more in the renewal notice. New functions are priced options or, where
folded into core, raise the core price above escalation at a renewal on the same notice, with the
client's right not to renew (John, 20 September 2026). The launch years are the express
exception.

**Avia ending or suspending the service.** Notice, pro-rata refund of the unused year within 30
days, outputs kept by the client, no further liability, and the loss of a data licence named
expressly as a trigger (John, 20 September 2026; W5 clause 15).

**Named discounts, and nothing else.** Launch; multi-year prepay; group; referral. The
agreement's discount line states which one applied (John, 20 September 2026, item 37).

**Net floors**, below which no combination of named discounts goes. The launch offer falls below
them by design and by John's ruling, and is the one exception written into the agreement.

| Airports covered | Floor | Source |
|---|---|---|
| One | £13,500 | W8 proposal, decision 11 |
| Two to nine | £20,000 | John, 20 Sep, item 37 |
| Ten or more | £25,000 | W8 proposal, decision 11 |

**Seats.** Named individuals on the airport operator's own corporate email domain, with no count
attached and no seat charge. **No consultant ever holds a seat** (John, 20 September 2026),
because a consultant with access could produce forecasts for anybody. The solicitor should be
asked to make that an express restriction on use. Advisers and consultancies are a separate
licence at a different price, quoted and not sold before Routes. The airport whose route
development is contracted out, and the airport run under a management contract, are the two cases
to settle in 2027; neither is priced here.

**Payment terms.** Annual in advance, invoice on signature, 14 days, exclusive of VAT, in
sterling, and no early-payment discount (W8 proposal, decision 12). The invoice is already annual
in advance, so an early-payment discount pays twice for the same cash and adds a fifth discount
to a list John has ruled closed at four.

**Quarterly payment, understood but not preferred** (John, 20 September 2026: it is not preferred
for Avia's cash flow, but some clients will have to use it). Offered with a visible premium, at a
clean quarterly figure, which covers the working capital and stops clients defaulting to it:

| Airports covered | Annual | A quarter | Annual equivalent |
|---|---|---|---|
| One | £15,000 | £4,000 | £16,000 |
| Two to nine | £22,500 | £6,000 | £24,000 |
| Ten or more | £30,000 | £8,000 | £32,000 |

A 6.7% premium on each (W8 proposal, decision 14). £4,000 a quarter also falls under a delegated
authority where £15,000 needs a board paper, which is the reason for offering it at all.

**THERE IS NO QUARTERLY LICENCE** (John, 20 September 2026). The licence is annual whichever way
it is paid. Quarterly is a payment method, so the client owes the full year from signature and an
instalment plan does not shorten the commitment. Non-payment of an instalment suspends access
until it is paid, and the year remains due as a debt. That is also why front-loading gains the
client nothing: a client who runs everything in the first quarter still owes the remaining three.

**The on-off pattern: signing for a year, running everything including forecasts in advance,
taking a year off and returning** (John's risk, 20 September 2026). It matters beyond the lost
year, because revenue that is not genuinely recurring is valued on a consultancy multiple rather
than a software one. Four responses, in order of effort:

1. **The product limits it more than any clause.** A forecast is built on the schedules, demand
   data and calibration as at the day it ran. Twelve months later the schedules have moved, the
   competitive set has moved and the accuracy record being cited is last year's. An airline
   network planner asks when the data is from, and a pack dated eighteen months ago does not
   survive the question. Stockpiling works only for a client who is not really pitching anybody.
   The sales language says so from day one: the client licenses the current forecast, not a file.
2. **The launch price is conditional on continuous licensing.** Lapse and the remaining launch
   years are lost and the client returns at the then-current list. It costs nothing, needs no
   enforcement, and does not breach item 29's "no obligation to renew", because the client is
   still free to leave. Decision 15.
3. **A re-onboarding fee of £2,500 on any lapsed licence**, covering account re-provisioning and
   reloading the catchment. Honest work, not a penalty dressed up. Decision 15.
4. **The honest limit, stated rather than papered over.** A launch client who skips year two
   saves £11,600 and pays circa £4,900 more to return, so the incentives still favour a genuinely
   biennial buyer. That is a signal, not a hole: **a client who wants the on-off pattern has
   bought the wrong product.** An airport on a two-year cycle should buy route studies at £3,500.
   Keeping the licence for continuous route development is what makes the revenue actually
   recurring, so the answer to that buyer is to put the study in front of them first, which the
   one-pager already does.

**A MINIMUM TERM IS RULED OUT AND IS NOT REOPENED** (John, 20 September 2026). The licence is
annual and renewable, with no obligation to renew, as item 29 says.

The question was raised and answered on the evidence of the three vendors Avia itself buys from.
Sabre supplies on a minimum three-year contract with discounts for four or five years and the
cash schedule locked at signature. **OAG and RDC are annual renewable**, and they are the closer
analogues, because they sell an annual subscription to an airport, which is what Meridian is;
Sabre supplies a bulk data feed with infrastructure and licensing behind it, which is what
justifies the longer lock. Two of the three comparators, and the two that look like this product,
say annual renewable.

Two things follow rather than a change of term. **The multi-year option below is the Sabre shape
offered as a choice**, so a client who wants that certainty can buy it while the default stays
OAG's. And **the continuity discount matters more without a minimum term**, because it is then the
only thing rewarding a client for staying.

It is also a third cross-check on £15,000. The two comparators closest to Meridian's shape sell
annual renewable at circa £11,000 and circa £20,000, so a £15,000 annual renewable single-airport
licence sits between them on both price and term.

### The permanent renewal discount

John's proposal, 20 September 2026, and it is the right instrument, because it keeps "no
obligation to renew" intact. The client is always free to leave; leaving costs them a price they
cannot get back. It also builds retention, which is what the exit case in section 8 actually
rests on, rather than buying a year of revenue.

Three versions, costed on the 81 independent single-airport clients in the 25% penetration case:

| Version | Steady-state price | Annual cost to Avia | Exit value at 5 to 8 times |
|---|---|---|---|
| 5% from the second renewal, held | £14,250 | £60,750 | £304,000 to £486,000 |
| 5% from the second, 10% from the fourth, held | £13,500 | £121,500 | £608,000 to £972,000 |
| None, keeping only the re-onboarding fee and the launch-year forfeit | £15,000 | nil | nil |

**The test is churn.** A 5% discount pays for itself if it reduces churn by about five percentage
points. A 10% discount has to reduce it by ten, which a discount of that size is unlikely to
achieve, because a client who leaves usually leaves for a reason other than price.

**W8 recommends 5% from the second renewal**, held for as long as the licence is continuous and
lost entirely on a lapse (decision 15). It stands alongside forfeiting the remaining launch years
and the £2,500 re-onboarding fee.

**The discount is off the list price of the year, never off the price last paid** (John's
question, 20 September 2026). Off the price paid compounds, so 95% of 95% of 95% reaches 60% of
the original after ten years, which is not a discount but a slow collapse. Off list, the client
holds a standing 5% below whatever the list is that year.

That gives the accurate sentence for the sales language, which is better than a vague loyalty
claim because the client can check it every year: **the price falls once at the first renewal and
then tracks 5% below list.** Worked on a single airport: year 1 at £15,000; at the first renewal
the list is £15,450 and the client pays £14,700, a fall of £300; thereafter their price rises
with the list and stays 5% under it.

**On paying for it.** W8 recommends leaving the list at £15,000 and accepting £14,250 as the
steady-state price, rather than setting the list at £15,750 so the continuity price is £15,000.
Raising the list preserves the revenue exactly and £15,750 is not harder to sell, but it reopens
a number now sitting in four workstreams' files four days before the solicitor, and it makes the
list a figure that exists to be discounted from, which is the thing John dislikes about software
pricing. If the discount does not buy retention, it is dropped at the first renewal cycle before
it has cost much.

**The continuity price is Avia's best price and carries no further discount**, except the group
rate. The floors in this section govern negotiated discounts for a client that has not yet earned
continuity; an earned continuity price is not negotiated down further. That is also a good
sentence to say to a long-standing client.

### Multi-year, which is two different goods

John, 20 September 2026: he would not be averse to 10% for a multi-year sign-up, and expects
buyers may want more for a three-year contract.

A commitment paid annually gives Avia revenue certainty. A prepay gives certainty plus the cash
and no credit risk. They are not the same good and should not earn the same discount.

**What a three-year prepay is worth to Avia.** The time value of receiving two years early, at an
8% cost of capital, is circa 7% of the total. The avoided churn risk, at 12% a year, is worth
circa 12% more. So a three-year prepay is worth roughly 15 to 19%, which is why 10% is
comfortably profitable and why there is room above it.

W8 proposal, decision 17, applying to any band and worked here on a single airport at the 3%
illustration:

| What the client commits to | Discount | Single airport |
|---|---|---|
| Three years, paid annually | 5% | the continuity discount from day one, instead of earning it at the second renewal |
| Two years, prepaid | 7.5% | £28,150 for the two years |
| Three years, prepaid | 12.5% | £40,550 for the three years, or £13,517 a year |

The three-year commitment paid annually earns the continuity discount immediately rather than at
the second renewal. It is the same number with nothing new to explain, and it converts a discount
Avia was giving away at renewal into something that buys a commitment.

**The answer when a buyer pushes past 12.5%, and it has the advantage of being true.** Twelve and
a half per cent on a three-year prepay is £13,517 a year, which is £17 above the £13,500 floor.
Fifteen per cent is £13,136 a year and breaches it. So the floor is what Avia says in the room:
that is as far as we go, and it is not a negotiating position but the floor set for every client.
The floor and the maximum affordable prepay discount agreeing to within £17 is also a reasonable
sign that both numbers are about right.

**A launch client may prepay the three launch years at no further discount**, being £32,650 for a
single airport, £48,950 for two to nine and £65,250 for ten or more. Nothing stacks, so no rule
is broken, and it is cash upside at a moment when cash matters. Decision 17.

**Contracting entity.** W8's view, for W5 and the solicitor: contract from Avia Solutions Limited
and market as The Aviation Observatory, because the OAG and Sabre licences, the professional
indemnity cover and the liability behind the accuracy record all belong to Avia Solutions
Limited. Umbrella item 31. W8 states a view only; the slot is W5's.

---

## 6a. Terms architecture, as the input W5 drafts from

W8 does not draft the agreement, which is W5's file under `routes/README.md`. This section is
the architecture and the commercial terms; W5 writes the clauses and the solicitor reviews them.

Built from two agreements Avia itself signs, read on Egnyte 20 September 2026 at John's
instruction: the Sabre GLBL Master Agreement of 1 May 2023 with Work Order 1
(`/Shared/Company Data/02 Knowledge/5 Aviation general/Sabre/Sabre 2023/`), and RDC Aviation's
Standard Terms of Use with the RDC contract renewal papers
(`/Shared/Company Data/07 Current Projects/Avia - Benchmark Database Development/Data and
Analysis/RDC Examples/` and `/Shared/Management/.../RDC Aviation/Contracts/`). **Structure and
mechanism are taken; no clause text is copied.** The Sabre agreement is marked Sabre Confidential
on every page and RDC's terms are RDC's copyright.

### The architecture: standard terms plus an Order Form

Sabre signs a Master Agreement once and issues a Work Order per engagement, the Work Order
superseding the Master only for what it covers. Meridian should do the same.

**Standard Terms**, signed once, carrying everything that does not vary: the licence grant and
its restrictions, intellectual property, permitted use, confidentiality, warranty and its limits,
liability and its cap, data protection, renewal and cancellation, escalation, suspension and
termination, Avia's withdrawal of the service, governing law.

**An Order Form per client**, carrying everything that does vary: the band and the price, the
schedule of covered airports, the launch schedule as three fixed cash figures, annual or
quarterly payment, the commencement date, any option purchased, and which named discount applied.

This solves W5's problem directly. The agreement is 17 clauses and four pages with nine open
slots, and every slot is a commercial variable. Moving them to the Order Form leaves standard
terms with no holes in them. It is also the expansion mechanism: a client adding airports or
moving band signs a new Order Form rather than reopening the agreement.

### What to take from Sabre's master agreement

| Mechanism | What Sabre does | What Meridian should do |
|---|---|---|
| Annual adjustment | Tied to a named published index, raised not more than once per calendar year, measured from the later of the effective date or the last adjustment | Avia's CPI clause has the index; it needs the frequency limit and the measurement point |
| Cure periods | 60 days for material breach, 10 days for non-payment | Adopt both |
| Repeat late payment | Right to terminate if undisputed payment defaults twice in any 12 months | Adopt. It is a better answer to the quarterly-payment risk than anything W8 proposed |
| Effects of termination | Access ceases, copies erased, an officer of the client certifies compliance in writing | Adopt, and align it with what a client keeps: delivered outputs stay theirs, the right to run stops |
| Sunset | 12 months' notice to retire a system, with replacement options and a right to let the order lapse | A better-drafted clause 15, and Avia already accepts it from Sabre, so nobody can call it harsh |
| Marketing assistance | References, press releases, a public quote, imagery, demonstrations, site visits and media interviews, each subject to the customer's approval | This is the launch condition on references and use of name and brand, written properly and more specifically than W5's current draft |
| Liability cap | The lesser of fees actually paid for the system in question, or a stated sum | Fees paid is the right basis. The agreement currently has no cap |
| Claims period | One year from accrual | Adopt |
| Express restrictions | No modifying, merging with other software, sublicensing, leasing, or reverse engineering | Adopt |
| Change management | A formal change request process with costs and schedule stated before either party is bound | Adopt for option purchases and band changes |

### What to take from RDC, which is the closer analogue

| Mechanism | What RDC does | What Meridian should do |
|---|---|---|
| **Cancellation notice** | Rolling subscription, **90 days' written notice** to terminate | **Take 90 days, or 60.** W5 drafts one month. Ninety days from the comparator John named is the annual-renewable equivalent of a minimum term, and a stronger retention mechanism than the continuity discount. Decision 19 |
| Named users | A unique personal username per user, for the sole purpose of that person's use | Matches the corporate-domain rule and the no-consultant rule |
| Automated access | No robot, scraper or other automated collection | Adopt, and it also protects the scope limit |
| **Permitted use** | The client may use the content for its own analysis, including extracts in reports and presentations of its own authorship, provided RDC and the software are recognised as the source | **Almost exactly Meridian's clause.** It is the provenance line in contract form, from a company selling to the same buyers |
| Onward use | Explicitly forbidden to use the content in any other systems, products or software services without written agreement | Adopt, **and extend it expressly to training or evaluating any machine learning model**, which RDC's wording predates |
| Third-party data | No warranty that third-party data is accurate or complete, with an undertaking to correct RDC's own errors | The right shape for the OAG and Sabre position, and it sits alongside the accuracy record rather than against it, because the record is about Avia's forecast and not the underlying feeds |
| Eligibility | Real name, address, credit standing | Adopt the credit-standing test, which matters for quarterly payment |
| Governing law | English law, non-exclusive jurisdiction of the English courts | Already in clause 17 |

### The commercial terms the Order Form carries

Every one of these is settled or is a numbered decision in section 11, and none of them belongs
in the standard terms:

the band and the annual price; the schedule of covered airports; the three launch cash figures
and the 30 November 2026 signature date; the four launch conditions; annual or quarterly payment
and the payment premium; any option purchased with its price; the named discount that applied and
the resulting net price against the floor; the continuity discount status; the commencement date
and the renewal date.

### What W8 has not resolved and W5 must put to the solicitor

1. **What a client keeps on termination.** Delivered packs, decks and workbooks are the client's
   and stay theirs. The right to run stops, and Sabre's certification mechanic applies to the
   software itself. The question the solicitor answers is whether a pack already sent to an
   airline is affected at all, and the answer should plainly be no.
2. **The onward-use clause reaching machine learning.** Meridian's outputs are exactly the
   material somebody would train on, and no comparator agreement Avia holds addresses it.
3. **The liability cap figure**, once the basis is fees paid.
4. **Whether 90 days or 60 is the cancellation notice**, which is decision 19.

---

## 7. The host sentence and the one-pager pricing block

**Host sentence**, for W4's manual section 4.4 and any stand conversation. The host's first
question is the qualifying one, because the answer decides which price applies and whether the
person can buy at all:

> "Is route development done here, or at group?"

Then, once only, and nothing further unprompted:

> "Launch clients who sign by the end of November pay half our list price in year one, and we
> hold the year two and year three prices in writing at signature. For a single airport the list
> is £15,000 a year, with no limit on users or on how much you run it. For a group it depends on
> how many airports you cover and we quote it. I will send you the one-pager with the numbers."

If John holds to the silence rule to 3 October (umbrella item 6), the host says only "on request,
limited places" and the sentence above travels in the follow-up one-pager instead.

**The pack promise is "the same day", not thirty minutes.** John's stand flow of 20 September has
the demo finishing on the forecast, because the research takes ten minutes, and the pack reaching
the visitor by email afterwards on the route they asked for, with a pre-made pack on a generic
route to show on the stand. That is sound and changes nothing here, with one exception: the
controller's ruling of 19 September is that every outgoing word says the pack "follows the same
day" until the sender is out of test mode and one pack has been sent and received over a hotspot
at the 11-12 October trial. W2 and W4 own it.

**Two questions go into W5's feedback card and the five meeting briefs** (W8 proposal, decision
13), because they are how the list gets set in November and they cost nothing to ask: how many
route studies did you commission last year and what did they cost; and what do you pay for OAG,
Cirium or RDC. That is the method already decided in July, which is to survey actual spend and
never willingness to pay.

**One-pager pricing block**, in this order: the route study first, because it is the purchase one
person can sign; then the licence with the airports-covered bands and the year 1, 2 and 3 launch
cash prices; then the four launch conditions and the 30 November 2026 signature date; then the
number of places. Figures from sections 4 and 5, quoted with this file's version.

---

## 8. What the pricing is being asked to deliver

Internal only. Never on a client-facing surface.

John's rule, 20 September: Routes World registration is the best available guide to how many
groups and airports take route development seriously, give or take 15%. That gives a universe of
**353 organisations**, 300 to 406 at the stated tolerance, of which roughly 30 are group
operators identifiable by name in the registration list and roughly 323 are independents
(`ROUTES-ATTENDING-ORGANISATIONS-21Sep2026.md`, read 19 September 2026).

Licence revenue at the bands in section 2, groups at £30,000 and independents at £15,000:

| Penetration | Clients | Licence revenue |
|---|---|---|
| 10% | 3 groups, 32 independents | £570,000 |
| 15% | 4 and 48 | £840,000 |
| 20% | 6 and 65 | £1,155,000 |
| 25% | 8 and 81 | £1,455,000 |
| 30% | 9 and 97 | £1,725,000 |
| 100%, the theoretical ceiling | 30 and 323 | £5,745,000 |

Break-even against the £526,121 fixed base
(`Avia_QSI_Licence_Model_07Aug2026.xlsx`) falls at about 10% penetration, or 35 clients. The
7 August target of 100 clients is 28% of that room.

**The whole business, not the licence alone.** At 25% penetration the licence earns £1,455,000;
the long-term forecast product at £15,000 to half of those clients adds £675,000; route studies
at £3,500 to sixty airports that never licence, buying two a year, adds £420,000. That is circa
£2.5m, and circa £2.9m at 30%.

**Why the price is not the thing to optimise.** Raising the whole ladder 20%, to £18,000 and
£36,000, earns £1,746,000 at 25% penetration. If that rise costs five points of penetration, it
earns £1,386,000, which is less than the current ladder earns at 25%. The rise has to cost fewer
than about four points to pay for itself. On John's own reading of how groups negotiate, it would
cost more. **Client count moves the answer roughly twice as hard as price does, and a price rise
buys fewer clients.** The ladder in section 2 is therefore the revenue-maximising choice, not the
cautious one.

That also holds for the exit. A consultancy earning £2.5m is valued on a multiple of earnings; a
software business with recurring revenue, a hundred named airport clients, a published accuracy
record and two products is valued on a multiple of revenue. Client count and retention build that
asset; price per client does not.

---

## 9. What is deliberately not offered before 2027

- **The long-term forecast inside Meridian.** John, 20 September 2026: a separate software
  product that integrates with Meridian and is bought separately. Not a band, not a bundle, not a
  day-1 item.
- **An Assured package**, meaning Avia review of runs or consulting hours. John, 20 September
  2026, item 37: a manual review of hundreds of runs is not viable, not at £5,000, and it puts
  Avia on the hook for every forecast. Assured is a 2027 package, price unset.
- **Airline and adviser licences.** Quoted only. An adviser or consultancy licence is a different
  product at a different price and is not sold before Routes, because a consultant with access
  could forecast for anybody. No airline licence is signed before Sabre's written approval, which
  is separate from the current licence (John, 17 September 2026). Decision 14.
- **A published list.** Quoted in writing to qualified buyers, not published on the website until
  November (John, 20 September 2026, item 29). The group bands are not published at all.
- **Metered runs, metered packs, and any counter visible in the product.**
- **Any size-based price**, and no size thresholds anywhere (John, 20 September 2026, item 37).
- **Any seat charge or seat limit.**
- **Self-serve card payment**, academic and government levels, and the Design Day module price.
  Carried as open from `PRICING-HANDOVER-19Sep2026.md` section 3; none is needed before Routes.

---

## 10. What each other workstream changes when this file says FINAL

- **W3**, pitch page and stand deck: the pricing line quotes this file and its version, nothing
  more. No change to the demo flow.
- **W4**, host manual: replace the section 4.4 pricing wording with section 7 above, including the
  qualifying question, carry the silence rule to 3 October, and carry "the same day" rather than
  any minutes figure. The host needs to know that a group delegation may be the buyer and an
  airport delegation may not be.
- **W5**, agreement and one-pager: the size-banded table goes in full. Clauses 2 and 4 and the
  one-pager's first table carry small, medium and large at £15,000, £20,000 and £25,000 from
  published passenger numbers (`W5-STATUS.md` v3, checklist items 1 and 3); section 4 above
  supersedes them, and the first two launch rows are unchanged arithmetic so only the third is new.
  Slot 3, the internal size thresholds, closes with no figure because no size axis exists. Clause
  2's three seats becomes the corporate-domain term with no count, plus the express restriction
  that no consultant holds a seat. Clause 6, the pack cap, becomes the fair-use wording in section
  3. The agreement needs a schedule of covered airports and a scope clause, and the two spend
  questions go on the feedback card. Slots 2, 4, 5 and 6 fill from sections 4, 5 and 6.
- **W6**, site copy: prices stay unpublished until November, and the group bands are never
  published. The seven files carrying the £15,000 / £20,000 / £25,000 size grid are rewritten to
  this file before the November publication, not before Routes.
- **Controller**: the five meeting targets carry no group head office, and on John's ruling that
  route development is often a group function, at least one should. The largest delegations in the
  room are group teams.

---

## 11. Decisions

John answers yes, no, or a number. Answers are logged in `W8-STATUS.md` with the date and never
re-asked.

### Settled on 20 September 2026 and not reopened

**The single-airport list starts at £15,000 for Routes** (John, 20 September 2026). It is quoted
in writing and unpublished until November. If the evidence after Routes shows £15,000 is too
expensive for an airport of Knock's shape, or a small Caribbean airport, a smaller airport band
may be introduced then, with the evidence behind it. Nothing in the 2026 material carries a
passenger threshold.

**A caution on that evidence.** John's own observation, 20 September: airports of Knock's shape
do not attend World Routes because they cannot afford it. Feedback collected at Frankfurt will
therefore over-represent airports that can afford Frankfurt, which are the least likely to need a
lower band. Decision 10 covers the fix, which is five telephone calls to existing small clients.

The axis is the number of airports covered. Researched packs unlimited with no cap, no overage and
no counter, protected by a fair-use clause rather than overage limits. Token-cost drift accepted
as a risk worth running. Seats are named individuals on the corporate domain with no count and no
charge, and no consultant holds one. The long-term forecast is a separate product. No Avia review
and no consulting before 2027. Analysis of any city pair is never scoped.

### Open

| # | Decision | Answer |
|---|---|---|
| 1 | Three bands by airports covered: £15,000 / £22,500 / £30,000 at one airport, two to nine, ten or more | |
| 2 | Adding airports moves the client to the band at the full annual difference, renewal date unchanged; during the launch years the launch percentage applies to the new band | |
| 3 | Fair use acts at 250 researched packs a licence year, being a telephone call and never a block or an invoice | |
| 4 | Meridian route study at £3,500 a route, first on the one-pager. Closes umbrella item 35 | |
| 5 | Ten launch places | |
| 6 | Years 2 and 3 fixed cash at signature, not the list as later refined. Closes the contradiction in item 29 | |
| 7 | Client's own catchment loaded, £2,500 one-off per airport, sold as consistency and credibility, never as accuracy | |
| 8 | The scope check goes on the two output endpoints, is a condition of the first multi-airport contract rather than of Routes, and the scope clause goes to the solicitor now | |
| 9 | The agreement commits Avia to issue the dated accuracy record with that year's n to every client every year | |
| 10 | The Knock test, in September: run Meridian on a route Knock cares about, send the pack, and ask whether it is good enough to put in front of an airline and whether twenty a year beats five by hand. Then four more existing small clients before November | |
| 11 | Floors of £13,500 / £20,000 / £25,000, governing negotiated discounts only | |
| 12 | Annual in advance, invoice on signature, 14 days, no early-payment discount | |
| 13 | The two spend questions go into W5's feedback card and the five meeting briefs | |
| 14 | Quarterly payment at £4,000 / £6,000 / £8,000 a quarter, a 6.7% premium, as a payment method for an annual licence with the full year due from signature | |
| 15 | Continuity discount of 5% from the second renewal, held while the licence is continuous, lost on a lapse; the continuity price carries no further discount except the group rate; the list stays at £15,000 | |
| 16 | Against the on-off pattern: the launch price is conditional on continuous licensing, and a lapsed licence pays £2,500 re-onboarding to return. No minimum term, so item 29 stands | |
| 17 | Multi-year: three years paid annually earns the 5% continuity discount from day one; two years prepaid 7.5%; three years prepaid 12.5%, which is £17 above the floor and is therefore the maximum. A launch client may prepay the three launch years at no further discount | |
| 18 | The agreement splits into Standard Terms signed once and an Order Form per client carrying the band, covered airports, launch schedule, payment basis and options, on the Sabre master-and-work-order pattern | |
| 19 | Cancellation notice moves from one month to 90 days, or 60, on the RDC precedent | |
| 20 | Airlines and advisers quoted only, and no airline licence signed before Sabre's written approval | |

Copyright Avia Solutions Limited. All rights reserved.
