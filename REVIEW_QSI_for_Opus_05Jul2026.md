# QSI tool review for the Opus development phase - Fable, 5 July 2026

Scope: full review of the route-forecasting pipeline, methodology, front end and demo readiness,
written to be handed to Opus as the working brief for the next few weeks. Every finding is
tagged **[impact: build-stopping / material / minor]** and **[cost: low / medium / high]**.
The final fix list is sequenced so the number of full test runs is the scarce resource being
spent, not analyst time.

Evidence base: this review draws on the live repository and on measured behaviour from the runs
of 3-5 July: the 6-year V1 baseline (bt_v1_6yr.csv, 6,471 routes in 26,054s = 4.0s/route), the
V2 QSI-feed runs (8.3s/route, circa 15h full-set), the lambda grid, the discrimination pre-test,
and the SOU/EIS airfield validation. One framing correction to the brief: the calibration base
is no longer circa 70 points; it is 3,549 graded launches across 2016-2019 + 2024, with the
matched A/B discipline (pinned route sets, re-centred dispersion) already in place. The
overfitting question therefore moves from "too few points overall" to "thin per-bucket counts",
which is assessed in section 2.

Headline for John's stated goal (cut the 2-3x misses): the three largest identified tail
sources, in order, are induced-market routes presented without labelling, the connecting-feed
under-credit on hub totals (V2's case, now proven on six years of matched routes), and the
small-market over-read (<15k markets, median 1.51-1.7x). All three have specific fixes below;
none requires new science.

---

## 1. Runtime diagnosis

Measured: V1 full set 4.0s/route; V2 8.3s/route. At 6,471 routes that is 7.2h and ~15h. The
run is I/O- and scan-dominated, not compute-dominated, and it is embarrassingly parallel by
route. The findings below compound: R1+R2+R3 together should take a full V2 run from ~15h to
well under one hour, which changes what "few iterations" means for every remaining decision.

**R1. Per-route full scans of the MIDT store.** [material] [cost: medium] [gain: ~10-30x on the
sabre side]. Every graded route runs `p2p_traffic` and `sector_traffic` as fresh 8-branch OR
scans over the whole sabre table (string-interpolated SQL, no pushdown-friendly shape), plus
`connecting_market`, `behind_market`, `destination_market_split` and two growth-year market
reads inside the forecast. Call it 6-10 near-full scans of a multi-GB store per route, times
6,471. Fix: one pre-aggregation pass per source_year into small derived tables (or parquet):
(a) `od_pairs(year, origin, dest, pax_p2p, pax_total)` for p2p/sector lookups - note
sector_traffic's adjacency semantics (consecutive legs in the routing) needs a one-off
leg-explosion pass, which DuckDB does in one scan with UNPIVOT-style unioning of the four leg
positions; (b) `conn_markets(year, origin, dest_airport, pax_connecting)` for the feed market
queries. After that, per-route reads are indexed point lookups on tables a thousandth the size.
Verify statically: run `--limit 100` and compare timings and outputs row-for-row against the
same 100 routes from bt_v1_6yr.csv - outputs must be identical to the penny, this is a pure
performance change.

**R2. No parallelism.** [material] [cost: low-medium] [gain: ~6-8x on an 8-core laptop].
The route loop is strictly serial; every store is opened read-only, so a
`multiprocessing.Pool` over route chunks with per-worker connections is safe as-is. The only
shared mutable state is feed_cfg's lazy caches, which are per-process anyway. Combine with R1:
the two multiply. Verify statically (same --limit 100 identity check; row order may differ,
sort before diff).

**R3. Connection churn.** [minor alone, material x volume] [cost: low] [gain: ~1.3-2x].
`_con(db)` opens and closes a fresh DuckDB connection for every query - route_feed alone opens
eight per route (hub_served, hub_fed_by, onward carriers, dominance, markets, feeders, inbound
carriers, behind market). Opening a connection to a large store has real fixed cost. Fix: a
module-level connection registry keyed by path (read-only connections are long-lived and
thread-safe enough for this usage pattern per process). Verify statically.

**R4. Discovery runs even when the pin bypasses it.** [minor] [cost: low] [gain: ~4-7 min/run].
Observed in the 5 July log: the full discovery (11,999 routes, several nonstop_pairs scans)
executes before "6471 routes loaded from pinned set (discovery bypassed)". Move the pin check
above discovery. Verify statically.

**R5. The V2 feed's remaining per-route cost.** [material] [cost: low] [gain: V2's 8.3s back
towards V1's 4.0s]. The wave cache already killed the OAG re-query; the remaining V2 overhead
is the competitor enumeration re-collapsing boards per route. The `_grouped_dep_board` memo is
per-process and per-(week, airport); with R2's process pool it warms per worker, so pre-warming
the memo per worker chunk (group routes by asif week before chunking) keeps the cache hot.
Verify statically.

**R6. Catchment and geo work per route.** [minor] [cost: low]. airportsdata loads and GeoNames
geocoding are already cached; the water check's lru_cache is in place. No action beyond
confirming the caches survive into workers (they re-warm per process; acceptable).

**R7. What NOT to do.** Do not move logic into pandas; the engine's queries belong in DuckDB
and the fix direction is fewer, bigger, earlier queries (pre-aggregation), not dataframe work.
And do not add secondary indexes to the raw sabre table expecting scan relief; DuckDB's wins
here come from small derived tables, projection and predicate pushdown, not b-trees.

Expected end state after R1-R5: full V1-style run ~20-40 minutes, V2 run under an hour, on the
same laptop. That converts the calibration cadence from overnight events into same-day
iterations, which is worth more than any single model refinement below.

---

## 2. QSI methodology soundness

**M1. The core formulation is sound and deliberately conservative.** [assessment, no action].
The scorer is the frozen analyst QSI (frequency x elapsed-time decay vs the market's fastest
routing x connection type x service level, proportional fair share), validated against the
QSI@SJC workbooks and consistent with the industry references (Kayloe, Dague) and JZ's training
material. V2's contribution is not new science; it is applying that scorer to the connecting
feed with competing-itinerary enumeration, levelled by k and dampened by lambda. The 4-5 July
result stands: V2 at k 0.65/1.41, lambda 0.5 beats V1 re-centred on ALL (.592 vs .664), HUB
(.631 vs .675) and material-feed (.422 vs .493) on 1,501 matched routes, and every robustness
cut except forecastable+material-feed (a .015 wash with better within-20%).

**M2. Free parameters vs calibration points.** [material, watch item] [cost: low]. Tuned
parameters in V2: k_beyond, k_behind, lambda - three, plus V1's inherited priors (capture,
stimulation by type, coverage). Against 3,549 graded routes that is not overfitting territory.
The risk concentrates in the per-bucket corrections now queued: the reinstatement discount
rests on 118 routes from one year (2024), the small-market trim on a bucket that mixes real
signal with Sabre coverage floor effects. Rule for Opus: no bucket correction goes default
without (a) at least two independent year-groups agreeing on sign and rough size, and (b) the
correction expressed as a capped factor, not an open multiplier - the airport_fit lesson.

**M3. Structural breaks and COVID.** [assessment + one action] [cost: low]. The store
deliberately excludes 2020-2022; launch years 2016-2019 + 2024-2025 with the reinstated tag
separating post-COVID restarts (313 of 1,035 in 2024) from true launches. The evidence so far
is the strongest argument the method survives the break: 2024 genuinely-new routes grade at
median 0.97 on an engine tuned without any post-COVID data. The action: 2025 launches must stay
out of the grading stats until 2027 outturn exists (they currently drop naturally; keep it that
way), and the reinstatement discount must be re-estimated when 2025's partial outturn firms up.

**M4. Calibration target vs use case.** [material, needs one decision] [cost: low-medium]. The
back-test grades first-full-year outturn, capacity-capped at the flown gauge. The demo use case
is a steady-state forecast at a proposed gauge. Two gaps: launch-year ramp (a Y1 target
under-represents mature demand; --mature/--y3 exist but are not the calibrated default), and
the cap (grading against capped forecasts is right for honesty, wrong if a client reads the
number as unconstrained demand). Decision for John: pick the product's canonical claim ("first
full year, as flown" vs "mature year, unconstrained") and calibrate to that one consistently;
the current mix is defensible for the back-test but must be stated on the Methodology page
either way.

**M5. The level bias is real and uniform.** [material] [cost: low, but costs one run]. The
6-year baseline shows forecastable P2P at median 1.15-1.22 across every launch year once the
China under-read stops masking it. This is a straight Phase 5 re-level (trim capture/
stimulation priors ~15%, re-solve k so FSC-forecastable median = 1.0), and it is the single
cheapest accuracy win available. It also directly serves the 2-3x goal: a 20% level trim pulls
the whole over-forecast tail in with it.

**M6. The 2-3x tail, decomposed.** [material] [cost: medium]. From the 6-year file the tail
is not one problem: (a) induced routes - median 0.15 by construction; the fix is presentation
and CRE flagging, never blending them into headline claims; (b) small markets <15k - median
1.51 over; fix per M2 as a capped factor; (c) hub totals under-credited by the flat feed - V2
is the fix, proven; (d) coverage-floor regions (thin GDS) - these should be flagged LOW
confidence by CRE rather than "fixed", because the error is in what the data can see. A
practical addition for the demo era: a sanity rail in the portal that flags any forecast
exceeding 2.5x the measured addressable market or implying a load factor above the plan
ceiling, routed to the CRE badge rather than silently printed.

**M7. Feed method consistency.** [minor] [cost: low]. When V2 becomes default, remove the V1
conn_coeff path from the default flow entirely rather than leaving two feed models reachable
with expert flags plus mct_banking parked alongside; three feed variants in one engine is how
drift re-enters. Keep V1 available behind one legacy flag for A/B only.

---

## 3. Front end review

**F1. Confidence is invisible on the main result.** [material] [cost: medium]. The dashboard
presents a point number; the Track record page holds the honest bands but only if you go
looking. Put the band on the result card itself: "47,004 each way (half of comparable
forecasts landed within x1.4)" with the peer-group basis a click away. This is the single
highest-value front-end change for the World Routes conversation and directly manages the 2-3x
perception problem, because the tool then never claimed more precision than it has.

**F2. Show what the inputs resolved to, before running.** [material] [cost: low]. The BVI ->
Birdsville incident is a class of failure, not an instance. Echo "SOU - Southampton (GB)" as a
chip under each input as soon as it resolves, so a wrong resolution is caught by eye before a
ten-second run and a confused result. The alias table handles known collisions; the chip
handles the unknown ones.

**F3. Error surfacing is inconsistent.** [minor] [cost: low]. The pitch flow now pre-flights
and reports stages; the optimise flow now explains infeasibility properly. Sweep the remaining
endpoints (report, catchment, economics pages) for the same pattern: any failure a delegate
could trigger should name what was resolved and what to do next, never a bare toast.

**F4. Demo warm-up is manual.** [material for the demo] [cost: low]. Build a warm_demo.py that
starts the server, runs three showcase forecasts (Genoa-New York, SOU-TFS, a reinstatement
case) to populate LAST_FC and the recent chips, opens the dashboard, Track record and
Methodology tabs, and verifies /api/pitch/health and the water check. One command, known-good
state, every time.

**F5. The Methodology and Track record pages are the right pattern - extend it.** [minor]
[cost: medium]. Both are server-rendered, offline-safe and self-updating. The catchment map
into the deck (existing task #36) and the forecast bridge exported as a slide into the PPTX
pack would carry the same transparency into what the client takes away.

**F6. OneDrive is not a deployment target.** [build-stopping for the demo] [cost: low]. The
app currently runs from the synced folder. Sync stalls corrupted module views repeatedly during
this session's development; a mid-demo sync pause or conflicted copy would be fatal. The demo
laptop must run a plain local copy (C:\AviaDemo\), pip-frozen (requirements.txt generated and
pinned), started by the warm-up script, with OneDrive either paused or irrelevant.

### 3b. Look and feel addendum (from the live screenshots, a delegate's-eye view)

Overall verdict: the visual design is a strength, not a gap - clean navy enterprise styling,
consistent cards and typography, a product-family sidebar that sells a roadmap, sensible
defaults, recent-route chips, progressive disclosure done properly, captions under every
number. The findings below are refinements to an already credible surface.

**F7. Result hierarchy inverts the story.** [material] [cost: low]. The four result tiles carry
equal visual weight and ADDRESSABLE MARKET comes first, so the eye lands on 1,168,675 before
the 47,004 forecast. On a stand, someone will read the big number as the answer. Make TOTAL
FORECAST the dominant tile, market as its context, capture share visually linking the two.

**F8. Zero reads as broken.** [minor] [cost: low]. "CONNECTING FEED 0" as a headline number
looks like an error even with the caption. When the value is structurally zero, replace the
number with the reason ("none - U2 does not interline").

**F9. No stage feedback on the main run.** [material for the demo] [cost: low]. The pitch flow
has stage messages; the ten-second main run should too ("measuring the market... scoring
itineraries... fitting the aircraft"). Ten silent seconds on a stand is long, and the stages
are free theatre that also teaches the methodology.

**F10. Highlight the home airport in the catchment bars.** [minor] [cost: low]. The origin
under assessment should be the accent colour so the leakage story lands without narration.

**F11. Palette drift between the dashboard and the server-rendered pages.** [minor] [cost:
low]. Track record and Methodology use their own colour constants; unify with the dashboard's
CSS tokens so a projector shows one product, not two generations.

**F12. Small-screen behaviour untested.** [material if an iPad features at Routes] [cost:
medium]. The dashboard grid is desktop-first; the server-rendered pages are responsive. Test at
~1024px only if the stand plan includes handing over an iPad.

**F13. SOON items are honest but live-looking.** [minor] [cost: low]. Make them visibly
non-interactive (no pointer cursor, no dead navigation) so nobody clicks the roadmap on stage.

(The standalone addendum file REVIEW_QSI_Addendum_LookAndFeel_05Jul2026.md is superseded by
this section; fix-list item 7 includes F7-F10.)

---

## 5. Demo failure modes (offline laptop, World Routes)

| # | Failure | Likelihood | Cheapest mitigation |
|---|---------|-----------|---------------------|
| D1 | OneDrive sync stall / conflicted copy mid-demo | High if run from synced folder | F6: local deployment copy, OneDrive paused [low] |
| D2 | Wrong Python resolves (two 3.12s observed on this machine) | High | Pinned venv inside the demo folder; warm-up script uses its absolute python.exe [low] |
| D3 | Researched pitch attempted live: needs internet + API key + minutes | Certain if clicked | Do not demo it live; pre-generate the pack and open the HTML; pre-flight already blocks gracefully [low] |
| D4 | Audience route hits a missing/retired IATA (TSE-class) or odd name | Medium | Retired-code aliases + F2 resolution chips; rehearse the "resolved to" recovery line [low] |
| D5 | Thin-GDS route returns a near-zero market on stage | Medium | CRE low-confidence badge wording; presenter note: pivot to the Methodology page's coverage step [low] |
| D6 | Methodology bridge empty (no LAST_FC after restart) | Certain after any restart | Warm-up script runs a forecast first [low] |
| D7 | A back-test or cache job left running drains the laptop / locks a store | Medium | Warm-up script checks for running python processes and refuses to start [low] |
| D8 | Laptop sleeps / lid closed between sessions, server dies | Medium | Power settings in the demo checklist; warm-up script idempotent (restart-safe) [low] |
| D9 | Port 8010 already bound from a crashed instance | Medium | Warm-up script kills stale listeners first [low] |
| D10 | Track record asked for an airport with 1-2 routes and someone challenges the peer stats | Medium | Already handled by design (labelled peer fallback); rehearse the explanation once [none] |

---

## Ordered fix list (sequenced to minimise full test runs)

Run budget logic: items 1-8 are verified statically or with --limit 100 identity checks
(minutes); the calibration bundle spends exactly ONE full run, and only after the runtime fixes
make that run cheap. Items marked (Opus) are the multi-week development line; the rest are
pre-Routes.

| # | Fix | Impact / cost | Verification |
|---|-----|---------------|--------------|
| 1 | R4 pin-bypass ordering + R3 connection registry | minor+material / low | static + smoke run |
| 2 | R1 sabre pre-aggregation tables (od_pairs, conn_markets, leg-exploded adjacency) | material / medium | --limit 100 identity vs bt_v1_6yr rows (no full run) |
| 3 | R2 multiprocessing route pool (+R5 week-grouped chunks) | material / low-medium | --limit 100 identity + timing |
| 4 | F6/D1-D2 demo deployment: local copy, pinned venv, requirements.txt | build-stopping (demo) / low | static checklist |
| 5 | F4/D6-D9 warm_demo.py + demo checklist | material (demo) / low | rehearsal |
| 6 | F2 resolution chips + D4 retired-IATA aliases + thin-GDS country fallback | material / low | static |
| 7 | F1 confidence band on the result card (Track record peer basis) | material / medium | static |
| 8 | M6 sanity rails into CRE (market multiple + LF ceiling flags) | material / low | static |
| 9 | **The one calibration run**: Phase 5 bundle - P2P level trim to median 1.0, V2 feed default-on (k 0.65/1.41, lambda 0.5) with k re-solved after the trim, reinstatement discount as a capped factor, small-market capped factor | material / medium | ONE full run (now fast, post 1-3) -> compare vs bt_v1_6yr AND bt_v2_6yr, by-year and by-bucket |
| 10 | M4 decision: canonical forecast claim (Y1-as-flown vs mature) + state it on the Methodology page | material / low | static + wording |
| 11 | M7 feed-path cleanup once V2 confirmed default | minor / low | static + smoke |
| 12 | (Opus) F5 bridge/catchment into the PPTX pack; Track record annex in reports | minor / medium | static |
| 13 | (Opus) Phase 4 face validity at final knobs + dep-time optimiser surfaced as a product feature ("best departure time" tab) | material / medium | uses cached boards, minutes not hours |
| 14 | (Opus) quarterly calibration cadence: new OAG/Sabre load -> re-run pinned sets -> Track record auto-updates; document as a runbook | material / low | scheduled |

Two rules for Opus to hold: never spend a full run on a change that a --limit 100 identity
check can verify, and never let two model changes share one run without a plan for attributing
the result (the k=0.06 artefact and the lambda grid both showed how cheaply a confounded run
misleads).

**POST-SCRIPT - the 6-year verdict landed (5 Jul, bt_v2_6yr.csv, 3,361 matched routes): V2
goes default inside the item 9 bundle.** It beat V1 re-centred on every slice (ALL +.100, HUB
+.079, material-feed +.070) and, decisively, on every launch year with the LARGEST wins in the
years no tuning touched (2016 +.118, 2024 +.080 vs 2017 +.069, 2018 +.091) - the out-of-sample
test passed. Reinstated routes benefit most (+.173). The beyond-2x tail share fell 57.4% to
50.2% before any Phase 5 fix. Carry k 0.65 / k_behind 1.41 / lambda 0.5 into the bundle and
re-solve k after the P2P level trim. The sharpest slice (forecastable + material feed, n=549)
remains a statistical wash (.007); do not spend runs chasing it until the bundle lands.
