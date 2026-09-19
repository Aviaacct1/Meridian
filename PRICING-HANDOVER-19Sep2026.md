# Meridian pricing: handover note

Author: Avia Solutions. Decisions taken during The Aviation Observatory website
build sessions of 2-3 August 2026, recorded here 19 September 2026. Copied into the
Meridian repo 21 September 2026 by the Routes programme controller; the original and the
decision trail live in the Observatory website repo (E:\Avia\Observatory Website, BUILD-NOTES.md).
Status in one line: the pricing structure and headline figures were settled and are published
on the staging site, but four commercial items were deliberately left unset and the whole grid
remains provisional until legal clears the product names.

## 1. What was agreed

Publication in full. Meridian's prices are printed on the site: £15,000, £20,000 or £25,000
a year by airport size (small, medium, large). Decided by John Carter on 2 August 2026, on
the brand designer's recommendation, reversing his own earlier same-day decision to show
from-figures only. The reasoning that carried it: an institution whose proposition is "we
publish our error" cannot gate its prices behind a call without undermining the proposition;
the direct competitor publishes no pricing, so printed prices are a stated differentiator on
the comparison page; and procurement conversations start better from a number.

Licence shape. Annual licence, per airport, per organisation, three named seats. Every tier
is the full tool: the price steps with airport size, never with features held back.
Feature-gating was rejected as inconsistent with the candour position; airport size was
chosen as the price driver because it tracks the value of the licence to the buyer.

Metering. 100 generated presentations a year are included across the three seats. Beyond
100, each presentation is charged per document at the rate stated in the licence. The
rationale, stated on the pricing page itself: presentation generation is Meridian's only
variable cost, so it is the only thing metered, and heavy use becomes a line item rather
than a renegotiation. Forecasts, scenarios and exports are unlimited within fair use.

Stated omissions. Two figures are deliberately unpublished, and the page says so rather
than staying silent (designer ruling of 3 August). The lines as published: "Size steps are
set from published passenger numbers and confirmed in the quotation; we do not print the
thresholds," and for the overage, the "rate is stated in the licence and we do not print it."

Size determination. Airport size is agreed in the quotation from published passenger
numbers. A provisional draft that printed thresholds (5m and 25m passengers) was removed.

Sales channel. Sales-led: request a quotation, receive a written proposal with the exact
price and licence terms, pay by invoice. Self-serve card and subscription is planned but not
built. Trials are free and take no payment details.

Adjacent pricing decisions taken in the same sessions. The Observatory Global Forecast is
£15,000 a year, three seats, covering the tool and the annual edition. The Design Day module
is quoted, priced per airport as an addition to an OGF licence, and is never sold alone.
Consultancies and multi-airport groups are quoted on their portfolio. Academic and
government licences are priced separately and available on request (John, 3 August). All
prices are exclusive of VAT, in sterling. The middle Meridian tier carries a brass top rule
as the single point of emphasis; no "most popular" badge.

## 2. Where it is implemented

The Observatory website repo (git history carries the decision trail; BUILD-NOTES.md the
reasoning at each round). The prices appear on /pricing/, the Meridian page (lede, FAQ and
SoftwareApplication JSON-LD offers at 15000/20000/25000 GBP), the products page stat bar
("£15-25k a year, published"), and the competitor comparison page. Pricing data also lives
in src/_data/site.json. The site is staging-only, noindex throughout, with a banner stating
pricing is provisional and not for publication.

## 3. Not finalised, and who owes what

1. The presentation overage rate. No figure exists anywhere. It must be set before the first
   licence is issued, and it is the commercially significant one: Meridian's margin depends
   on presentation generation cost.
2. Internal size thresholds. The public policy is settled; the internal thresholds that
   implement it were never fixed.
3. Design Day module price. "Quoted" is the whole policy so far.
4. Academic and government levels. On-request is agreed; the discount basis is not.
5. Final commercial sign-off. The figures go live only with the launch sign-off that also
   clears the names; the staging banner says exactly that.
6. Data-provider cost stability. Meridian's only variable cost depends on it; never
   resolved. Worth closing before the overage rate is set, since one prices the other.

## 4. The decision sequence, for the record

2 August, morning: from-figures public, sales-led. 2 August, evening: designer brief argues
full publication; John rules for the full grid with exclusions stated. 3 August: designer
rules that the unpublished thresholds and overage rate must be stated omissions, not silent
ones; implemented same day. 3 August, later: academic and government on-request added on
John's instruction. Every step is a dated commit in the website repo and a dated entry in
BUILD-NOTES.md.
