# Jarek's feedback against the old methodology and the industry standard, 24 August 2026

Purpose: before adding Jarek's points (full list in `JAREK-FEEDBACK-24Aug2026.md`, alongside this
file) to the development programme, each is checked against two things: Avia's own QSI practice
before Meridian, and the wider industry-standard QSI model. This gives a defensible answer to
"should we build this" beyond a single tester's preference, and separates genuine methodology gaps
from product/UX work.

## Sources checked, on Egnyte

- **Avia's core in-house QSI methodology**, as filed in proposals 2015-2021 (e.g.
  `/Shared/Company Data/05 Proposals/.../Appendix - Route Dev_QSI Methodology.docx`). Three
  factors only: total elapsed time, connection type (online/codeshare/interline), frequency.
  Output includes cannibalisation effects. No fare, no aircraft type, no day-of-week.
- **Avia's post-pandemic refinements**, 2021-2023 (`13 Route Development/Marketing
  Material/Presentations/Forecasting and QSI Methodology post-pandemic...`). Adds: fleet-change
  sensitivity ("we also account for rapid changes in airline fleets which can impact QSI scores"),
  an explicit flag that fare/low-fare stimulus was NOT properly captured by traditional QSI and
  was expected to matter more ("ticket prices could be a more important driver behind route
  success... traditional QSI approaches did not factor in low fare stimulus other than through
  generic assumptions"), Sabre Forward Bookings for cabin/fare mix, IATA country-pair traffic
  forecasts as a cross-check input, and a stated need to re-run QSI seasonally as schedules move.
- **InterVISTAS / Sabre Profit Essentials QSI methodology** (`12 AviaForecasts/04 QSI
  Model/Data/InterVISTAS QSI Methodology.pdf`, 2011). This is the closest thing the industry has
  to a QSI standard: developed originally for the US CAB, run commercially by Sabre as Profit
  Essentials, used by airlines, airports, manufacturers, governments and consultants worldwide
  (there is no separate IATA QSI standard; QSI is a US CAB-derived methodology that became the de
  facto cross-industry convention, and Profit Essentials is its dominant commercial
  implementation). Documents a ten-factor model, six commonly used: directness of service, elapsed
  travel time, aircraft type (seat-capacity band, smaller coefficient range than directness),
  day-of-week, time of departure, frequency. Four more exist but are route/city calibration-heavy
  and often left off: city presence, carrier preference, yield (fare sensitivity), share gap.
  Explicit industry caution: yield and city-presence factors take considerable calibration effort
  per route/city and were left out even by InterVISTAS on a live client engagement for that
  reason.

## Reading

Avia's current three-factor QSI (elapsed time, connection type, frequency) is the historical
Avia model, unchanged, and it is also the cautious subset of the wider industry model, since it
is exactly the three factors any implementation keeps and the calibration-heavy ones are the ones
routinely dropped even by specialist users of the full model. That is a defensible position, not
a gap by itself. What follows sorts Jarek's list by whether it closes a real, precedented gap
against that wider model and Avia's own stated ambitions, or whether it is product work with no
methodology content.

## Must have

None. Nothing on Jarek's list is a correctness problem in what Meridian currently claims to do.
The curfew item (5 in the companion file) is the one live-bug-shaped report and it resolved to a
labelling issue, not a demand error; it sits in the should-have list below on that basis.

## Should have, methodology

**Fare in the QSI build-up (item 6, fare half).** Precedented twice over: it is Profit
Essentials' "yield" factor, and it is a gap Avia's own 2021-2023 refinement note already named
explicitly as a post-pandemic weakness. The industry caution applies just as much here: yield
calibration is route/city-specific and takes real effort, which is exactly why InterVISTAS itself
left it off a live engagement. Meridian already carries fare in the catchment-choice generalised-
cost logit (access layer), just not in the QSI capture score itself; the honest framing on return
is "extend fare into the capture layer," not "add fare from nothing." Properly scoped, not a
quick add.

**Aircraft type as a QSI coefficient (item 6, aircraft half).** A standard Profit Essentials
factor (seat-capacity band, jet vs turboprop), and Avia's own post-pandemic note flagged fleet
sensitivity as a live concern. Note the industry evidence is that this factor carries a much
smaller coefficient range than directness of service, so it is worth building but should not be
oversold to a client as a major swing factor. Moderate effort: Meridian already has a
carrier's-own-seat-configuration override for capacity sizing; this asks for the same input to
feed a QSI perception coefficient, which is a different, smaller piece of work.

**Alliance / codeshare sensitivity testing (item 8, alliance half).** This is not a new idea, it
is close to the core use case the InterVISTAS document itself demonstrates (QSI's standard
application to alliance and codeshare share-shift). Meridian already has the named-partner
override mechanism; extending it to a listed, flexible what-if is a natural and well-precedented
extension, not new methodology risk.

## Should have, product/UX (no methodology risk)

- OAG week / Sabre year selection plus a comparison tab (item 3): directly answers Avia's own
  2021-2023 note that QSI should be re-run seasonally as schedules move; currently the tool can
  only do that by a fresh session, not a comparison.
- MCT/terminal manual override (item 8, MCT half): the connection-building machinery already
  exists (`mct_bank.py`); this exposes it as a scenario input rather than building anything new.
- User/market permissions, and Expert Mode behind a permission (items 1, 12): governance, matters
  more as testers become clients with sensitive markets (IFC, Dubai, Macquarie-type
  confidentiality), not a methodology question.
- Curfew labelling fix (item 5): make the theoretical-optimum figure explicitly labelled as
  theoretical, and either search the return leg properly within the curfew or label it
  explicitly indicative. Low effort relative to value given it already surfaced as tester
  confusion once.
- Aircraft required to operate the schedule (item 9): straightforward output from the existing
  aircraft economics module.
- Cannibalisation and share-of-total-market reporting (item 11, cannibalisation half): this was
  already a stated OUTPUT of Avia's pre-Meridian methodology ("the model can also consider
  potential effects of cannibalization on routes"). Worth a direct check of whether Meridian
  still produces this before treating it as new work; it may be a re-instatement rather than a
  build.

## Nice to have

- Auto-generated market background before running assumptions (item 4): genuinely useful and
  consistent with Avia's own general route-development sequence (market analysis before the
  specific forecast), but a substantial UX build, not a methodology gap.
- Visual outputs, interactive maps, hover detail (item 7): high perceived value per Jarek
  ("clients love it") but pure presentation layer.
- Save/load scenarios, JSON export/import, comparison tabs across airlines/frequencies/timings
  (item 13): product convenience, no methodology content.
- CSV/export completeness for charts and visuals (item 11, export half): finishing work on an
  already-strong feature.
- Double-stop QSI (item 14): real Avia precedent ("we used to model such cases, although very
  rarely, e.g. for TPE") but rare in practice by Jarek's own account, and the industry-standard
  document itself treats indirect service as one-stop/single-connection rather than routinely
  extending further. Low frequency of use argues for nice-to-have over should-have despite being
  a precedented capability.
- Sensitivity charts / Monte Carlo on fare and frequency (item 15): no industry-standard precedent
  in the documents reviewed; Profit Essentials' own stimulation modules are scenario-based rather
  than Monte Carlo. Worth doing once fare is genuinely in the model, not before.
- Fully agentic assistant (item 16): no detail given, long-term direction only.

## Suggested order on return

1. Curfew labelling fix (should have, product, already caused live confusion).
2. Fare into the QSI capture layer (should have, methodology, the single highest-precedent gap
   against both the industry standard and Avia's own stated post-pandemic ambition).
3. Aircraft-type QSI coefficient (should have, methodology, moderate effort, rides alongside the
   fare work since both touch the capture score).
4. Alliance/codeshare sensitivity UI (should have, methodology-adjacent, mechanism already exists).
5. OAG week/Sabre year selection and comparison tab; MCT override; permissions and Expert Mode
   gating (should have, product, roughly parallel tracks, no sequencing dependency between them).
6. Cannibalisation/share-of-market reporting: verify current state before scoping as new work.
7. Everything in the nice-to-have list, unscheduled, revisit after the above closes.

Day-of-week frequency allocation (raised separately by John, 24 August, not from Jarek's list)
sits alongside item 2 in effort and precedent, since it is also a genuine capture-model extension
rather than a display fix; sequence it with the fare and aircraft-type work rather than
separately.
