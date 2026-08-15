# Meridian - independent review, Fable, 15 August 2026

Version 1.0, 15 August 2026. Avia Solutions. Scope: what stands between Meridian and a beta a
client can use, with the Routes timetable in view. Evidence: the C:\AviaDev repository as read this
session, bt2/bt2_experiments.log in full for 13-15 August and by entry for the earlier programme,
HANDOVER-15Aug2026.md and KICKOFF-15Aug2026.md (both partly superseded by the log and marked so
below), REVIEW_Avia_Cortex_Fable_06Jul2026.md, two agent-verified code audits run this session
(silent-failure hunt; capture and feed path verification), and an Egnyte survey of the historic QSI
method (sources named in section 7). Findings tagged [critical / material / minor] with effort in
days. Weaknesses first throughout. Where a figure appears, its file or log entry is named; where I
could not verify, I say so.

---

## The verdict, first

**Show it at Routes. Do not sell it there.** Demo plus structured beta, launch in November, is the
right call, and it is achievable. The reasoning in one paragraph: the science underneath Meridian is
now better evidenced than anything comparable in the market, and the 14-15 August work is the best
of the whole programme. But the product today ships a connecting feed at a level its own back-test
refutes by circa ten times on the median route (RECUT-RESULT, 13 August, and the 15 August entries
that removed the last opposing evidence), the published accuracy figures were measured on a
different arm from the one the portal runs (THE-EVIDENCE-AND-THE-PRODUCT-ARE-DIFFERENT-ENGINES,
15 August), and the live path can lose its entire feed layer to a swallowed exception and present
the result as a clean forecast (this review, R3). None of those three can be caveated away in front
of a network planner. All three are closable inside the two-week decision window, and the closing
run for the first two is the same run.

To the drift concern in your note: Meridian is still recognisably the house QSI method, and in most
places a measured version of it. There are two genuine departures, and one of them is in the old
method's favour. Section 7 has the full comparison.

---

## 1. What stands between this and a client beta

These are the items that cannot ship at all, even with a caveat. Everything else in this review is
material or minor and either ships with a stated limitation or waits.

**R1. The connecting feed level. qsi_k 1.0 is wrong, not unproven.** [critical] [2-3 days of work
plus one overnight run; the decision is then John's]

The evidence chain, all in the log: the shipped level over-reads actual connecting traffic by circa
ten times on the median back-test route (RECUT-RESULT, 13 August, 1,891 routes, median actual over
feed 0.098, cross-checked against LEVEL-VS-SHAPE within 0.8%). The best cell in the whole table,
long haul into a named Asian or Gulf hub, the SJC-TPE cell, still needs k circa 0.235, 4.26x below
shipped (SJC-TPE-IS-INSIDE). The two arguments that kept 1.0 alive are both now withdrawn by the
programme's own work: the 2.07x/2.50x "Sabre transfer under-count" was a mislabelled measurement of
a different quantity (FLOOR-EVIDENCED-WAS-MISREAD, 14 August), and its ceiling is bounded at circa
1.15x by load-factor arithmetic (UNDER-COUNT-IS-IMPOSSIBLE); the apparent agreement with the 2025
analyst was first a base-year misread (ANALYST-BASE-NOT-FORECAST) and then a market-definition
difference (BEHIND-MARKET-IDENTIFIED, 15 August). The log's own words: the over-read finding now
stands unopposed.

This is not an abstract calibration point. The chain qsi_k to feed to frequency to total is measured
(K-REACHES-THE-FREQUENCY-CHOICE): at k 1.0 the optimiser returns ten weekly widebodies on SJC-TPE
with connecting at 55% of the route; at k circa 0.1 the total falls to circa 127,000 and the
optimiser returns 4-5x weekly, which is what your own testing produced (120-135k) and within 20% of
the 2025 analyst's 107.9k. The feed level also reaches the LOCAL number through the capacity cap on
every bound route (CAP-COUPLES-THE-LEGS). So the single number k is currently setting the aircraft,
the frequency, the mix and the P2P figure on hub routes.

What settles it: the rewritten paired k sweep (K-SWEEP-PROBE-IS-NOT-A-RESULT closed the invalid
first version; the tool now requires the pinned route set and pairs scoring across arms). One
addition is required before the run is worth making: a per-leg connecting grade. The team's own
entry THE-SWEEP-CANNOT-SEE-A-MIX-ERROR says it plainly: a total-based hit rate is satisfied by an
inflated feed on top of a short local leg, so a k chosen on fc_over_out maximises the compensation.
fc_over_p2p grades the local leg; nothing grades the connecting leg against outturn. Add that
column, run the arms overnight (circa 44 minutes per arm on your note, so six arms is an evening),
and pick k from the connecting-leg grade with the V1 flat feed as the control to beat. My
expectation from the existing table is that k lands between 0.1 and 0.35, possibly cut by hub type;
if V2 at its best k cannot beat V1 on the paired measure, SCHEDULE-BANKING is the precedent and V1
ships. Either outcome is fine for November. Shipping 1.0 is not.

**R2. The accuracy evidence and the product are different machines.** [critical] [1-2 days plus one
pinned run, shareable with the R1 run]

THE-EVIDENCE-AND-THE-PRODUCT-ARE-DIFFERENT-ENGINES (15 August) states it exactly: the back-test's
default arm runs the V1 flat feed, the portal runs the V2 QSI feed at k 1.0, and the published 89%
and 82% come from bt2_claims.py, a gradient-boosted claim set that never reads capacity and is not
what the portal computes (CAP-IS-NOT-IN-THE-PUBLISHED-CLAIM). So the first question any airline
analyst or DD reviewer asks, "is this the accuracy of the tool I am looking at", currently has an
uncomfortable answer.

I am not proposing the claims move; that is your standing decision and the published wording is
BINDING per the BT2 programme note. I am saying the configuration that ships must be the
configuration that was graded. Once R1 fixes k, run one arm on the pinned route set in exactly the
shipped configuration: V2 feed at the chosen k (or V1 if it wins), od_source auto, the 0.875 cap,
current turnarounds. Whatever that arm returns is the number the portal's track-record page shows
beside the claim set, each labelled with what produced it. That sentence, "the figure beside this
forecast was measured on this configuration", is the whole credibility position, and today it
cannot be said.

**R3. The live path fails silent, in three layers.** [critical] [1-2 days]

The 6 July review flagged the V2-to-V1 fallback as silent (S3). It is still open, and this
session's audit found it is worse than recorded:

- route_forecast.py lines 642-645: the entire feed block is wrapped in one except that zeroes both
  feed sides and empties the detail maps. Any failure in the feed layer, a missing MCT file, a
  broken wave cache, a db_registry fault, deletes the largest component of a hub forecast and the
  payload shows a legitimate-looking thin feed. Nothing distinguishes "no feed" from "feed layer
  crashed".
- route_feed.py lines 286-287 and 444-445: when the V2 branch throws, the route drops to the V1
  flat feed and increments _qsi_fallbacks, which only backtest.py reads. cortex_app never reads it,
  and the payload still emits feed_level claiming qsi_k with dep_basis "optimised for this
  airline's connections". A run that silently reverted to V1 is labelled a V2 run.
- qsi_feed.py lines 301-304, 316-319, 463-466: a failed departure-board read returns an empty row
  set in silence. On the beyond side an empty competitor set drives the share calculation to 1.0,
  which at k 1.0 captures the entire connecting market; on the behind side the mirror failure
  zeroes the leg. And _circuity_ok (lines 152-172) sets a module-global flag on the first exception
  and returns True forever after, so one coordinate failure disables the circuity screen for the
  rest of the process.

The fix is the one the contract layer already models: the payload states the feed basis that
actually ran, the same way forecast_engine and feed_level report themselves, and a fallback or a
zeroed layer is named on the page. The legs check passes a crashed-feed contract today because the
arithmetic still coheres; consistency checks cannot catch this, only provenance can.

**R4. The provenance block contradicts the engine, on the exact claim the US pitch depends on.**
[critical because of Job 1, not because of size] [0.5 days]

od_source.py line 63 now defaults AVIA_OD_SOURCE to "auto" ("John's decision, 15 August" in the
docstring), so a default US domestic run reads DB1B. cortex_app.py line 1236 still reports
`os.environ.get("AVIA_OD_SOURCE", "sabre")`, so the payload, and through _settings every deck,
prints "sabre" while the P2P leg read DOT. The whole point of Job 1 is the sentence "DOT DB1B for
the US domestic markets"; the tool currently reads DOT and says Sabre. The same flip means a
backtest.py rerun today silently reads DOT for 2016-2019 US markets, so the 9 August reproduction
chain no longer reproduces without anyone having touched a switch. Stale "off unless set" comments
remain at od_source.py 33 and 312 and route_feed.py 243. One symptom, three small fixes, and the
re-measure the handover already orders.

**R5. The fare under every revenue figure.** [critical for any deck with a P&L page] [1-2 days]

Two parts. First, silent substitution: od_source._sabre_fare returns 0.0 on any failure with a
docstring claiming the gap is stated downstream; downstream, cortex_app only adopts avg_fare when
positive, and _econ_block line 562 then substitutes max(180, dist_nm x 0.11), a distance proxy,
reported as economics.econ_fare with no provenance flag. A missing fare becomes an invented fare
indistinguishable from a measured one. Second, the unverified level: the handover carries the
point-to-point one-way fare at 2,055.65 with the note that whether it is right needs a sourced
comparison against Sabre's measured fare, and it multiplies through every revenue figure on the
deck. Flag the proxy on the page, and close the fare check before any deck with a revenue page
reaches a client. avg_ow_fare_connecting, cask and ancillary_revenue remain empty and are named as
such; empty and named is acceptable for beta, silent proxy is not.

---

## 2. The five open questions, confirmed, refuted or reframed

The build team's own 14-15 August work already moved most of these, and moved them correctly. My
verdict on each, having verified the code independently (line cites checked this session; several
of the runbook's cites have drifted, corrected below):

**Q1, qsi_k.** Confirmed, and it is the right first question; see R1. One reframe: this is no
longer a "calibration gap". The level is measured wrong and the remaining work is a decision run,
not research. The runbook cite drifted: the objective is now route_feed.py lines 712-720, the
carried cap is route_forecast.py line 826, the floor line 867.

**Q2, the feed scored one way.** Confirmed in code: beyond_capture and behind_capture
(qsi_feed.py lines 342-343 and 442-443) take a single outbound dep_time_mins and no return-time
parameter exists anywhere in the module; the return is curfew-screened but never scored
(optimise_departure scores only the outbound at route_feed.py 712-720). THE-ROTATION-IS-NOT-A-LOOP
makes it worse than the runbook states: the return time is arrival plus a turn, the curfew screen
assumes a closed loop that no widebody flies, and each movement needs screening on its own time.
Material, not critical: ship with the caveat that connection quality is scored on the outbound
departure, and build the return scoring in the beta window. [3-5 days when it comes]

**Q3, the objective destroys yield when the cap binds.** Confirmed as a mechanism, but the team's
own reframe is correct and better than the question: on a capacity-bound route the objective cannot
move the total at all, only the mix (CAP-IS-THE-CROWDING), a passenger weight is algebraically null
(WEIGHT-IS-A-NULL-TEST) or degenerate after the cap (WEIGHT-AFTER-THE-CAP-INVERTS), and the only
instrument that settles it is revenue per seat. The missing input is the connecting fare, and the
0.855 yield ratio is now measured on census data with a transfer check across distance bands
(CONNECTING-YIELD-MEASURED, THE-YIELD-RATIO-TRANSFERS). Verdict: the objective stays as it is for
the demo with the chart note that shipped on 14 August (THE-CHART-SHOULD-HAVE-SAID-SO), and the
revenue objective is the first post-Routes build. Using 0.85, with 0.8 as the prudent client
setting, is right. [2-3 days once avg_ow_fare_connecting is populated; DB1B coupons now give the US
figure, a Sabre fares pull gives international]

**Q4, no term for the operating airline's own service at a competing airport.** Confirmed, and it
is the most under-weighted of the five. Verified this session: capture is entirely airport-level.
airport_qsi_to_dest takes no airline parameter (route_qsi.py lines 42-44), forecast() never passes
the airline into capture (route_forecast.py 540-541), catchment.py and sabre_catchment.py contain
no carrier term, and repatriated is hard-set to 0.0 at route_forecast.py line 759. China Airlines'
own SFO-TPE service enters only as an anonymous competitor in the denominator; the model cannot
know the incumbent at SFO and the proposed operator at SJC are the same airline, so repatriation is
counted as pure gain with no offsetting loss. Two aggravations. First, the knowledge exists in the
repo and is unread: calibration_library_v8.py records the analyst's own CI/BR finding that a new
SJC service cannibalises CI's SFO share by 4-22% per market, and nothing on the live path reads
that library. Second, section 7: the historic house method HAD this step, a QSI re-run with and
without the new service. Meridian dropped a check the 25-year method always ran. Beta ships with
the limitation stated in the methodology page; the fix is an airline-level second pass over the
existing QSI machinery. [5-10 days, post-Routes]

**Q5, local capture blind to departure time.** Confirmed (no time-of-day input anywhere in
qsi_score or qsi_capture; the engine says so itself at route_feed.py 818-820). Two reframes. It is
not drift: the 25-year QSI never had a time-of-day term either, so this is method-faithful. And the
"optimiser pushes into the incumbent bank" worry is partly answered by
OPTIMISER-MATCHES-THE-MARKET, though see section 5 for the limit of that validation. Minor for
beta; a schedule-differentiation term is a research item, not a product item.

---

## 3. Silent failures not previously found

The log records its silent-default instances with a running count; the count itself has slipped
(two entries claim SIXTH, two claim seventh, then ninth: the true count is at least eleven). This
session's audit adds ten more, verified against the code and checked as absent from the log. R3,
R4 and R5 above cover the five worst (the feed-layer swallow, the invisible V1 fallback, the board
reads and circuity flag, the od_source payload contradiction, the proxy fare). The rest:

**R6. Economics runs on the generic seat table even when the carrier's own count is known.**
[material] [1 day] _econ_block takes no seats parameter (cortex_app.py 557-560); the seats override
reaches annual_capacity (line 1034) but never the P&L, so the agreed SJC-TPE case caps demand at
306 seats while load factors, spill and economics run at the table's 336. capacity.load and
economics.econ_lf disagree by circa 10% in one payload. This is the FIXED-GAUGE defect's twin,
one layer further down, and the same shape as the four contract defects: two bases under one name.

**R7. The forecast pack prints "Connecting floor off" on every deck.** [material] [0.5 days]
forecast_to_contract.py 376-377 reads fc["settings"]["split_floor"], which nothing writes, so the
value is always None and forecast_pack.py line 158 renders an affirmative "off", including on
default runs where the floor is on. Unrepaired residue of SETTINGS-WAS-NEVER-WRITTEN: the fix wrote
_settings from the payload but this one field still reads a key nothing populates. A wrong
methodology statement on a client pack's basis page.

**R8. The measured cabin split is unreachable from the dashboard.** [material] [0.5 days]
/api/forecast and /api/report hard-default econ_share to 0.85 (cortex_app.py 1450, 2078), so the
measured-share branch (1083-1088) can never fire from either endpoint and every default run gets
the old 85/15 assumption labelled "set by the caller" when no caller set it. The sentinel is also
inconsistent: /api/optimise treats 0 as "measure it", /api/forecast uses 0 literally and produces
nonsense economics without warning.

**R9. The growth fallback mislabels itself.** [minor] [0.5 days] If the two Sabre market reads
throw, growth is silently 0.03 (cortex_app.py 840-845) while growth_basis still reads "measured
market CAGR tapered...", and that string reaches the deck. One distinct basis string in the except.

**R10. AUTO gauge failure silently sizes the route on an A21X.** [minor] [0.5 days] The auto-gauge
pre-pass swallows its exception (cortex_app.py 1492-1495) and falls through to A21X with no payload
flag, so a widebody-length request that failed sizing gets a narrowbody cap presented as normal.

A pattern observation for the beta window rather than a finding: the 6 July review counted circa
200 broad except blocks on the product surface and set one rule, a fallback that changes the answer
must never be silent. Every one of R3 and R6-R10 is that rule violated. The rule is right; it has
not yet been applied as a single deliberate pass, and each new feature has re-introduced the shape.
Half a day of grep and triage per module, and the legs check plus payload provenance make it
sustainable. [3-4 days across the beta window]

---

## 4. Where the numbers are wrong rather than merely unproven

The programme measures more than any forecasting shop I have seen, so the failure mode has shifted:
when it goes wrong it is now usually a right number attached to the wrong quantity. The log itself
caught four on 14-15 August (the 2.07x/2.50x mislabel, the base-year comparison, cost_pax read as
carried passengers, the DB1B fare basis). Add these:

Wrong today, on the live path: qsi_k 1.0 (R1); the payload's od_source mode field (R4); the
economics seat basis on any run with a carrier configuration (R6); the forecast pack's floor line
(R7); the cabin split label (R8). Wrong until 14 August, now fixed and held by the legs check: the
four contract defects, including a client-facing grand total 12.3% double-counted at a 96.8%
implied load factor.

Unproven, and named as such, which is the correct state: the 2,055.65 fare level (R5); origin_share
0.62 and business_share_destination 0.22 (placeholders, labelled as such, still holding back the
eight-segment table); the catchment parameters outside the Genoa-era geography (6 July S12, still
open); and, the largest one, the connecting leg's accuracy against outturn, which no measure
currently grades (THE-SWEEP-CANNOT-SEE-A-MIX-ERROR names the gap; R1 closes it as a by-product).

One number to stop quoting: the 3% total agreement with the 2025 analyst. ANALYST-MEASURED and
RECONCILIATION-INVERTS establish it is two offsetting errors, connecting 19% under his figure by
one definition and local 14% over. The log says "do not quote the total agreement without saying
so"; my stronger version is do not quote it at all until the market-definition question
(FOOTNOTE-TENSION-UNRESOLVED) is answered by whoever built his deck.

---

## 5. What the team has convinced itself of

The 14-15 August entries are unusually self-correcting, four withdrawals in two days, all of them
right to be withdrawn. Remaining places where I read conviction ahead of evidence:

**"The optimiser's chosen times match the market" validates the connecting-only objective.**
OPTIMISER-MATCHES-THE-MARKET compares against China Airlines, EVA and United at SFO, three carriers
that all time for hub banks. The test cannot distinguish "the objective is right" from "the
comparators share the objective". A point-to-point operator on the same sector, a leisure carrier
or a low-cost long-haul entrant, has no comparator in that test, and for exactly those carriers the
objective would time the departure for connections they do not carry. Keep the closure (no code
change needed now), drop the word "validated"; the revenue objective supersedes the question anyway.

**"The contract is fixed and held by invariants; none of the defects were in the engine"
(HANDOVER-15Aug2026).** True as written and easy to over-read. The legs check verifies consistency,
not correctness, which its own log entry states; a contract built from a crashed feed (R3) or a
proxy fare (R5) passes all four invariants. The invariant layer is excellent and it is one layer.

**"Three things closed on 14 August should not be reopened."** Two of the three closures rest on
the current objective staying connecting-only (the null-weight argument dies the moment yield
enters the objective) and on the cap staying a brake for an over-read that R1 will shrink.
LF-CAP-CLOSED itself says the cap stays global "until the over-read it absorbs is fixed at source";
fixing k IS fixing it at source, so the cap percentile and the optimiser objective both come back
for one look after R1 lands. Closed for now is right; closed is not.

**The handover and kickoff themselves.** Written 14 August evening, superseded within a day on
their centrepiece: Job 3's "best candidate" for the 19% gap was ruled out
(COMPETITION-SPLIT-IS-NOT-THE-GAP) and the gap itself retired as a definition difference
(BEHIND-MARKET-IDENTIFIED); Job 1's "the behind-San Jose leg is entirely US domestic" was measured
wrong (DOT-IS-DOMESTIC-ONLY-MEASURED, the behind market is Portland-to-Taipei, not
Portland-to-San-Jose, so DOT cannot see any SJC-TPE leg). The team caught both itself, which is the
system working, but anyone starting from the handover alone would spend days on a ruled-out
candidate. Retire the 15 August handover's Job 3 framing formally in the next kickoff.

**The competition split.** Still worth building, but its justification is now Job 2's table rows
and method quality, not the connecting gap. QSI-FEED-SETS-EVERY-CAPTURE is the deeper finding:
per-market captures already run 0.04% to 26.2% with no bound above and near-zero below, and the
behind side reads twenty to ninety times below the beyond side on TPA-AUS at a fortress origin.
After R1 re-levels the feed, look at the SPREAD next, per-market bounds and the behind-side
mechanism, before adding a competition dimension on top of an unexamined distribution.

---

## 6. The 6 July review, closed and open

Closed: S1 git (repo, tags, commit-message discipline; the platform standard is being followed).
S2 substantially (warm_demo asserts the mask package, check_env names it; whether the confirming
run in the canonical configuration was done I could not verify from the repo, say if it was). S4
induced routes, properly closed: the portal now models new-market routes from comparable launches,
bands them 0.55-1.19, and labels the basis on the payload (cortex_app.py 1119-1135); this was the
6 July review's most dangerous item and it was fixed the right way. S16 partially (db_registry has
reset(); nothing calls it yet).

Open, carried to the beta window with the same tags: S3 silent feed fallback [critical then, worse
now, R3]. S5 quarantine [material]: app/ has grown from 153 to 243 Python files; the workshop is
winning. S6 tests [material]: 20 test and check scripts now exist and the fixture culture in bt2 is
excellent, but there is still no pytest configuration and nothing runs on change. S7 broad excepts
[material, R3/R6-R10]. S8 SQL interpolation [material]: backtest.py lines 262-263 still
f-string airport codes into SQL; the API boundary still validates with strip/upper only. S9 LAST_FC
unguarded [material for any multi-user beta]. S10 USD-only economics [material for European beta
airports]. S11 [material]: requirements.lock.txt still absent, hardcoded C:\Avia paths remain in
product modules. S13 coverage overrides [now partly retired by events: DOT replaces the n=4 US
factor on US routes, per COVERAGE-IS-A-GROSS-DOWN, which is the better fix; the override principle
still does not reach the other regions]. S14 monolith, S15 default password, S17 airfield MARGINAL
wiring: unchanged [minor].

The 6 July data-rights position (customer holds the data licences, Avia ships methodology, software
and calibration) has had no visible movement in the repo. For a November launch with beta airports
this is on the critical path in the commercial sense even though it is not code: the written
confirmation against the actual Sabre and OAG contracts, and the customer-extract ingestion path,
both remain undone. Flagging, not scoping, here.

---

## 7. Meridian against the 25-year QSI method

Your concern was that two months of accuracy-driven change may have made the tool unrecognisable
against the house method. I had the historic record surveyed on Egnyte this session: the 2013
templates (QSI New Template (OS DS) 26Apr13.xlsx and the Calibration Template, in /Shared/Company
Data/12 AviaForecasts/04 QSI Model/), the Connection Builder v4.0, the 2014 user guide, the 2015
methodology appendix (Israel Airport Authority proposal), the 2019 training template, the 2023
post-pandemic methodology deck, the BA LHR-SJC reference workbook in this repo, and the 2025
analyst deck with calibration_library_v8.py. The comparison, without varnish:

**Where Meridian is the same method.** The connecting layer is the house QSI almost exactly:
itinerary score from frequency, elapsed time against the market minimum, and connection type
(online over alliance over interline), share as own QSI over total market QSI, below-MCT and
double-connection exclusions, circuity screening. Those are the same three factors every client
document from 2015 to the 2025 deck names. The P2P structure is the same pipeline as the BA
workbook's Forecast sheet: base demand, growth to forecast year, stimulation, capture, and
stimulation applies to P2P only with connecting at 1.00, which Meridian preserves and the 2025
analyst confirms. QSI captures only the indirect portion of a beyond market in both. An airline can
be walked through Meridian's forecast in the same sentences the 2015 appendix used. On
explainability the answer is yes.

**Where Meridian is the method, upgraded and now measured.** P2P capture: the old method used
analyst judgment by segment and catchment tier (the BA workbook's 40%/22% business rates were
judgment; the tier shares were judgment); Meridian derives it from a catchment choice model plus
QSI service values. That is drift in mechanism but it is the drift the method always wanted, and
the back-test grades it, which no judgment rate ever was. Turnarounds measured from OAG rather than
assumed; the 0.875 cap now sitting on a measured 85.5th percentile of 4,963 real launches; the
0.855 connecting yield ratio measured on census data; growth measured rather than the BA workbook's
flat 9%/7.5% compound. The 2023 deck's post-pandemic corrections (current-season schedules,
conservative growth) are subsumed by measurement. This is Meridian being "more technical, better"
as you put it, with the evidence to say so.

**The two genuine departures.**

First, in the old method's favour: **cannibalisation**. The house method measured it with a QSI
re-run with and without the new service, and the 2025 analyst's own working recorded 4-22%
per-market erosion of CI's SFO share. Meridian has no term at all (Q4/R11 above, repatriated
hard-set to 0.0). The 25-year method ran a check the new tool dropped. Restore it in the beta
window and the drift story inverts into a strength.

Second, new to Meridian and currently mis-set: **the feed level k**. The old method never shipped
an uncalibrated share: the 2013 Calibration Template tuned the adjustment factor until predicted
share matched actual bookings, and connecting fair share was capped and adjusted. k 1.0 on the live
path is an uncalibrated share multiplier, which is precisely the thing the house method's
calibration step existed to prevent. R1 is therefore not a departure from the method; completing it
is a return to it. That is also the honest answer to "have we turned a key function off": no
function is off, but the method's own calibration discipline was not applied to its newest
component, and one legacy strength (cannibalisation) was left behind in the Excel era.

Also true and worth stating: capacity and spill did not exist in the old method at all (load factor
was an output, never a constraint), so the cap, the optimiser, the P&L, the seasonality and the
back-test are all new capability with no historic counterpart to drift from.

**The explanation for an airline**, one paragraph, which the methodology page should carry: demand
measured from Sabre MIDT (US domestic: DOT census), grown on measured market growth, stimulated on
the IATA curve for P2P only; capture from a calibrated airport-choice model over drive time and
schedule quality; connecting feed from the same QSI scoring the firm has used for 25 years,
calibrated against six years of graded route launches; capped at the aircraft; priced from measured
fares. Every sentence of that is true today except "calibrated" on the feed, and R1 makes it true.

---

## 8. What a client or a DD reviewer asks that the tool cannot yet answer

1. "Is the accuracy figure on your track-record page the accuracy of the configuration I am
   using?" Not today (R2).
2. "What data produced this number?" The payload can currently contradict itself (R4), a crashed
   feed is unlabelled (R3), and a proxy fare is unflagged (R5). After those: yes, and better than
   any competitor, because the labels exist.
3. "You forecast our airline gaining at SJC. How much comes off our own SFO service?" No answer
   (Q4). The 2025 analyst answered it by hand; the tool cannot.
4. "What is your connecting fare assumption?" Empty field, named as empty, but empty
   (avg_ow_fare_connecting; cask and ancillary_revenue likewise).
5. "Why 0.62 origin share and 22% destination business share?" Placeholders, named as yours to
   set. Fine for beta if the page says so; a DD reviewer will find them in segment_inputs.py.
6. "Under what licence do you sell forecasts derived from Sabre and OAG data?" The 6 July position
   exists on paper; the written confirmation does not.
7. "Does your catchment model hold outside the geography it was fitted in?" Unproven (S12); the
   Knock-style stress test remains unrun.
8. "Can I see the seasonal split?" Assumed profile pending the monthly pull; unchanged since July.

None of these except 1 and 2 blocks a demo; all of them shape the beta caveat list.

---

## 9. The beta path

**Cannot ship at all, close before Routes** (order matters, total circa 8-11 working days plus two
overnight runs, inside your two-week window):

| # | Item | Effort |
|---|------|--------|
| 1 | R4 od_source payload truth, comment cleanup, re-measure | 0.5d |
| 2 | R3 feed provenance: basis-that-ran on payload and page, fallback named, board-read and circuity failures surfaced | 1-2d |
| 3 | R5 proxy-fare flag, fare check against measured Sabre fare | 1-2d |
| 4 | R1 per-leg connecting grade added to the paired sweep tool, arms run overnight on the pinned set, k decided (your call on the number; V1 is the control to beat) | 2-3d + 1 night |
| 5 | R2 one pinned arm in the exact shipped configuration; track-record page states what was measured on what | 1-2d + 1 night |
| 6 | R6 seats into the economics block | 1d |
| 7 | R7/R8 pack floor line and cabin-split reachability | 1d |

**Ships at Routes with a stated caveat** (the caveat list IS the methodology page):
one-directional connection scoring (Q2); no repatriation term, stated exactly as the DD question in
section 8 phrases it (Q4); connecting-demand optimiser objective with the flat-total note already
on the chart (Q3); segment placeholders named as user-set; assumed seasonal profile; catchment
fitted primarily on European geography; US DOT for US domestic only, labelled.

**Beta window, September to November, in value order:** revenue-per-seat objective once the
connecting fare lands (Q3, 2-3d); return-direction scoring and per-movement curfew screening (Q2,
3-5d); repatriation as an airline-level QSI second pass, restoring the house method's own check
(Q4, 5-10d); the silent-fallback rule applied as one deliberate pass with pytest catching
regressions (3-4d); competition-split rows for the forecast table (Job 2, after the spread look in
section 5); the Job 2 pack corrections; quarantine of app/ before any external eye sees the repo
(2d); data-rights letter and ingestion path in parallel, since November launch depends on them
commercially even though no code does.

**The decision you asked for:** at Routes, show it. Demo underserved and reinstatement cases plus
SJC-TPE with the corrected contract; put the track-record page, the caveat list and the "measured
on this configuration" sentence in front of every planner who asks a hard question, because that
audience rewards exactly this posture. Sign beta airports there, three to five, launch November
with the beta findings folded in. Selling licences in October, before R1/R2 have a graded arm
behind the shipped configuration and before the data-rights letter exists, would put the one asset
this programme has that nobody else has, the honest evidence base, at risk on its first public
outing. The evidence says the product is circa two weeks from demo-clean and one calibration
decision from claim-clean, and that is a strong position for mid-October, not a weak one.

---

*Fable, 15 August 2026. Primary evidence: bt2/bt2_experiments.log entries as named; code as read
this session at the line numbers given; agent audit reports (silent-failure hunt; capture path
verification); Egnyte documents as pathed in section 7. Figures not measured this session carry
their log entry or file name; none are from recall.*
