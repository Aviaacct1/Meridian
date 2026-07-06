# Avia Cortex - independent review, Fable, 6 July 2026

Scope: code and structure, product viability for airports, development priorities, and the pathway to a licensed product. Written against the live repository, the 5 July review and its fix-list progress, and the calibration evidence (bt_6yr_det, bt_v2_6yr_factored). Findings tagged [critical / material / minor] and effort in days where useful. Weaknesses first throughout.

One framing point before the detail. The engineering work since 5 July was genuinely good: byte-reproducible runs, a 7x pre-aggregation speedup, a verified parallel pool, and a calibration sized on hit rate rather than median. None of that is the risk any more. The risk has moved to three places: what the tool cannot yet do (induced routes), what it hides when it fails (silent fallbacks), and what the business around it does not yet have (data rights, version control, a second person who understands it).

---

## 1. Code and structure

### The blocking findings

**S1. The repository is not under version control.** [critical] [0.5 days]. There is no git history. A forecasting product whose commercial claim is "calibrated against 3,549 graded launches" cannot show which code produced which baseline. The 5 July session already paid for this: when the identity check failed, there was no pristine prior commit to diff against, and diagnosis took a day of A/B toggles that `git bisect` does in an hour. Before anything else: `git init`, commit the current state, tag it against bt_v2_6yr_factored.csv, and commit every calibration-affecting change with the baseline it produced. This is also the first thing a due-diligence reviewer asks for, and "there is no history" ends that conversation.

**S2. The calibration/runtime configuration match is unproven.** [critical] [0.5 days to verify]. The live trim (FSC/ULCC 0.85, LCC 0.95) was sized on mask-off runs (the interim calibration path), while the demo machine has global-land-mask installed in at least one Python, so live forecasts may run mask-on. Mask state moves coastal catchments by double digits (NAS-TPA 14,163 mask-off vs circa 12,133 mask-on). If the demo serves mask-on forecasts through a mask-off calibration, every coastal route carries an unquantified extra trim. Decide the canonical configuration, re-run the one confirming baseline in that configuration, and make warm_demo assert it at startup. The two-Python problem makes this worse: which interpreter serves the demo decides which calibration regime you are silently in.

**S3. The V2 feed fails silent.** [critical] [1 day]. route_feed.py lines 270 and 287: any exception inside the QSI feed or MCT path drops the route to the V1 flat-capture feed with nothing but a counter increment, and under --jobs>1 the parent process prints that counter as zero. A hub forecast can lose half its feed and present as a clean result. In a back-test this pollutes the evidence base; on a stand it produces a confidently wrong number with no tell. Fix: surface the feed method actually used on every forecast (a small badge: "feed: QSI V2" / "feed: V1 fallback"), log the exception, and make the backtest refuse to grade a route whose feed fell back unless a flag says otherwise.

**S4. Induced routes are unlabelled in the live portal.** [critical] [2-3 days]. The forecastable/induced split exists only in backtest.py. The portal will happily forecast a market with no history, produce the known median 0.14 under-read, and present it with the same visual authority as a calibrated P2P forecast. This is the single most dangerous behaviour in the product because the induced case is exactly what an airport wants to pitch. The fix for September is presentation, not science: detect the thin/absent-history condition at forecast time, badge the result INDUCED with different framing ("measured market is X; comparable new-market launches reached 3-7x this"), and never print the raw number as the headline. The modelling fix comes later (section 3).

### The material findings

**S5. app/ is a workshop, not a product.** [material] [2 days]. 153 .py files, of which circa 45 form the actual product surface (traced from cortex_app.py and route_forecast.py). The rest: circa 520KB of dead legacy modules that nothing imports (avia_qsi_auto_v3.py at 242KB, calibration_library_v8.py at 142KB, commercial_reasonableness_engine.py, business_case_mode.py and friends), 11 scratch duplicates (_ck*, _btk*, _rf*), 34 archived files, plus 35 CSVs of run outputs and several client xlsx/pptx files mixed into the source tree. Quarantine: product modules stay in app/, calibration harness to calib/, one-off scripts to research/, run outputs out of the tree entirely, dead legacy deleted (git makes deletion safe). Half a day of moves, one day of import fixing. The payoff is not tidiness; it is that a second developer, a pilot customer's IT department, or a buyer's reviewer can see what the product is.

**S6. No test automation.** [material] [3-5 days initial]. Ten manual scripts, print-only, no pytest, no CI, no assertions that run on change. verify_identity.py is a genuinely good harness but it needs the stores and John's machine. What is missing is the cheap layer: unit tests on pure functions (QSI scorer against known fixtures, market_factor_for, season_shares, the preagg SQL against the synthetic store already built for it), runnable in seconds without data. The synthetic-sabre test that caught two preagg builder bugs proves the value; it should be a pytest file, not a memory of a session.

**S7. Error handling swallows too much.** [material] [ongoing]. Circa 200 broad `except Exception` blocks across the product modules, many silent. The pattern that matters: a fallback that changes the answer (feed, airfield check, catchment water clip) must never be silent; a fallback that degrades presentation (a missing city name) may be. Sweep the product surface against that one rule.

**S8. SQL is assembled by f-string interpolation, including values that arrive from portal inputs.** [material] [1-2 days]. backtest.py lines 231-257 and equivalents interpolate airport codes directly into SQL. Portal input validation is `.strip().upper()` only. Exposure today is low (localhost, single user, cookie auth) and DuckDB is read-only, but a licensed on-prem product cannot ship this: parameterise, or at minimum enforce `^[A-Z0-9]{3}$` at the API boundary. A due-diligence reviewer greps for exactly this.

**S9. Global state in the portal is unguarded.** [material] [1 day]. LAST_FC and PITCH_JOBS have no locking; concurrent requests can interleave. Irrelevant for a one-laptop demo, disqualifying for any multi-user deployment. Note it in the code and fix it when the deployment model is decided; do not ship a licensed version with it.

**S10. Economics are USD-only.** [material] [2-3 days]. aircraft_economics.py carries no FX handling. A Genoa case quoting airport charges and a P&L in dollars is a visible wart in front of a European airport board, and John's own convention (currency follows asset jurisdiction) says the tool is wrong by his standards. A simple report-currency layer (rates as a dated CSV input, clearly stamped) is enough; do not build live FX.

**S11. Environment and deployment fragility, partially fixed.** [material] [1 day to finish]. requirements.txt now covers the server but pins with >= not ==; requirements.lock.txt is referenced but absent; two Python 3.12 installs with different packages produce different catchment numbers (the mask gotcha in S2); 93 hardcoded C:\Avia paths; OneDrive has corrupted module views repeatedly and served a truncated backtest.py as recently as 5 July. DEPLOY_DEMO.md has the right answer (local copy, pinned venv). Finish it: generate the lock file, make db_registry read store paths from one config, and rehearse the deployment on the actual demo laptop.

**S12. The catchment parameters are single-airport calibrated.** [material, correctness] [research item]. The logit scale, attractiveness exponent and value-of-time multipliers in catchment.py were fitted around the Genoa work. The back-test grades outcomes globally, which gives some comfort that the whole pipeline centres, but the apportionment layer itself has not been validated outside one geography. The Knock-style stress test in the method notes is the right instrument; run it on two or three contrasting catchments (one multi-airport metro, one isolated regional) before claiming the catchment layer generalises.

**S13. Coverage gross-up factors are hardcoded with no override.** [material] [1 day]. coverage.py fixes the GDS coverage factors per country and haul band. A systematic error in one region biases every route touching it, and the user-override principle (the POC rule that every key input can be overridden) does not reach this input. Add the override and a provenance note per factor; recalibration itself is a quarter item.

### The minor findings

**S14.** cortex_app.py is a 64KB monolith mixing routing, HTML and model calls; split when multi-user work starts, not before. [minor]
**S15.** Default password "aviacortex2026" in source; fine for the demo, must be forced-set on any customer install. [minor]
**S16.** Nothing calls db_registry.reset(); wire it to the quarterly data reload so cached connections cannot point at a replaced store. [minor]
**S17.** The airfield MARGINAL band is computed but not wired into aircraft selection, so the picker can recommend a runway-limited type without a flag; John's filter-vs-advisory decision is the blocker, not code. [minor pending decision]
**S18.** The preagg sector_adj table is optional and its build has failed twice on this machine (memory, temp-dir I/O); sector_traffic full-scans when absent. Acceptable, but the runbook should say plainly which runs need it. [minor]

### What is sound

Worth stating once, without inflation. The determinism story is now real and proven (byte-identical repeat runs, the two ANY_VALUE/tiebreaker root causes found and fixed properly rather than papered over). db_registry is a clean pattern. The preagg layer reproduces the hot queries exactly, proven on a synthetic store including the count-once edge cases. The calibration discipline (pinned route sets, one change per run, the bucketing-artefact catch that killed a fake market-size gradient before it shipped) is better than most professional forecasting shops manage. The economics constants are sourced and cited (Airbus reserves, appraiser lease curves) rather than invented. And the honest Track-record page is a product asset no competitor shows. The problem is not the science; it is everything around the science that a customer would touch.

---

## 2. Product viability for airports

### The uncomfortable frame first

An airport does not buy a forecast; it buys a meeting that goes well. The airline's network planning team will run its own numbers in its own model and will never adopt Cortex's figure. So the product's real job is narrower than "forecast accurately": it must get the airport a serious hearing, survive twenty minutes of adversarial questioning from a network planner, and leave behind a case document the airline's analyst can reproduce the logic of. Judged against that bar rather than against oracle accuracy, the picture changes in both directions.

**Where the scatter hurts less than it looks.** Circa 25% of forecastable routes within +/-20%, half within a factor of 1.4, is unimpressive as a headline and roughly the honest state of the entire industry, which simply never publishes its record. No consultancy shows a graded six-year back-test because most would not survive it. An airline planner knows this. Presenting "half of comparable forecasts landed within x1.4, and here is the full distribution" is a stronger credibility move with that audience than a competitor's confident single number, because it signals the tool was built by people who have been on the receiving end of consultant hockey sticks. The band is only a weakness with the naive buyer, and the naive buyer is not who signs off a route.

**Where the induced weakness hurts more than it looks.** The routes an airport most wants to pitch are the ones that do not exist yet, and there the tool reads 0.14 of outturn. Until the comparable-market layer exists, Cortex is a tool for underserved-market cases (measured demand, wrong or absent capacity) and reinstatement cases, not for true white-space pitches. That is still most of the volume of air-service development work, but be honest about the boundary in every conversation, because the first airline that catches an induced number presented as calibrated will retell the story.

**The output question.** An airport ASD team is two or three people who live in PowerPoint and email. The portal is the demo instrument and the analyst's cockpit; the deck and workbook are the product the customer actually consumes. The deck generator is therefore not an add-on, it is the revenue surface, and it is still unbuilt. Conversely the airline side consumes evidence: the methodology page, the track record, the assumptions register. Both outputs exist in embryo and both matter more than any further portal polish.

### Against the landscape

Sabre Market Intelligence / AirVision, Cirium Diio Mi and OAG sell data and analytics workbenches: superb at describing what is, silent on what would happen if you launched. They are also priced and shaped for airlines and large hubs. ASM and the Routes-adjacent consultancies sell exactly what Cortex produces, at £20-50k per study, hand-made, unvalidated, slow. Volaire and a few boutiques sit in between. Nobody in that landscape hands an airport a calibrated engine it owns and can run on Tuesday for a route its CEO thought of on Monday.

So the wedge is real, and it is specifically this: **speed and ownership for the mid-size airport that cannot justify an in-house analyst but currently pays consultancy rates per case.** "Honest" strengthens the wedge with the airline audience; "offline, airport-owned" strengthens it with airports burned by per-seat SaaS pricing and with the data-rights structure below. But the wedge is narrow: large hubs have in-house teams with their own MIDT feeds, and tiny airports buy one study every three years and will not license software. The addressable segment is perhaps the 200-400 airports globally in the 0.5m-15m passenger range with active route development ambitions, of which a realistic early market is the few dozen John can reach through existing relationships and the Routes channel.

The competitive risk is not the data houses building a forecaster (they have no incentive to publish accuracy) and not another consultancy copying the method (they could, in a year, but would then have to show their own back-test). It is that the wedge customer solves the problem with a cheaper habit: asking their incumbent consultancy to do it, or believing the airline will do the work anyway. The counter is the per-case economics: if a licence costs less than two ASM studies a year, the finance case makes itself.

Verdict: viable as a product line, not as a standalone software company. It works as consultancy-plus-tool from Avia, priced against the study budget it replaces, with the software licence as the renewal mechanism. It does not work, on current evidence, as venture-shaped SaaS, and nothing in this review should be read as recommending that path.

---

## 3. Development priorities

Ordered by value to the airport buyer. "Month" means before Routes prep freezes (circa end August); "quarter" means Q4 2026.

### Next month (ship-blocking for Routes)

| # | Item | Why first | Effort |
|---|------|-----------|--------|
| 1 | S2 calibration/mask configuration decision + one confirming run | every live number depends on it | 0.5d + 1 run |
| 2 | S1 git + S5 quarantine + S11 lock file | makes everything after it safe and diagnosable | 2-3d |
| 3 | S4 induced badge + comparable-launches panel (presentation layer) | the most dangerous demo failure, and the most asked-for case type | 2-3d |
| 4 | S3 feed-method badge + fallback logging | silent wrong numbers end credibility | 1d |
| 5 | F1 confidence band on the result card | the honesty wedge, made visible where the eye lands | 1-2d |
| 6 | F2 resolution chips + retired-IATA aliases; M6 sanity rails; F7-F10 result-card polish | demo failure modes D4-D5, cheap | 2-3d |
| 7 | Demo deployment executed and rehearsed on the actual laptop (warm_demo, pinned venv, OneDrive out) | D1-D2 are the highest-likelihood failures | 1d + rehearsals |
| 8 | Deck generator to a first working BA-SJC-quality output | it is the product the customer keeps | 4-6d |

Items 1-7 are circa two working weeks. Item 8 is the long pole; start it in parallel and accept a plain first version. Everything else on the list (reinstatement discount, seasonal optimise axis, coverage recalibration) should be refused for September; the reinstatement discount in particular fails the two-year-agreement rule (118 routes, one year) and should wait for 2025 outturn rather than ship half-evidenced.

### Next quarter

1. **The stimulation/comparable-market model for induced routes.** The hard, valuable one. The workable shape: build a launch-analogue library from the six-year back-test store itself (thousands of graded launches with route type, catchment size, carrier type, pre-existing indirect traffic), forecast an induced route as a distribution over its nearest analogues rather than from its own absent history, and present it as a range with named comparators ("routes like this one reached 45-120k; the middle half landed 60-90k"). That is honest, matches how airline planners actually think about white space, and reuses evidence already built. Do not attempt a gravity-model stimulation coefficient first; calibrating one on the same thin data is how the 0.14 becomes a confident 0.5 that is still wrong.
2. Monthly Sabre pull lands: seasonal calibration on one-season routes (data already in hand for those), then the optimise season axis with seasonal economics.
3. S12 catchment generalisation stress tests; S13 coverage overrides then recalibration.
4. S10 report currency. S8/S9 parameterised SQL and state locking, as pilot-readiness items.
5. Quarterly calibration cadence as a documented runbook (new OAG/Sabre load, pinned re-run, Track record auto-update), with db_registry.reset() wired in. This cadence is also a licensing asset: "recalibrated quarterly" is a sentence competitors cannot say.

---

## 4. Pathway to a licensed version

### Data rights, resolved

The question is whether a product whose every output derives from Sabre MIDT and OAG data can be sold. Take a position: **it can, but only in the configuration where the customer holds the data licences and Avia ships methodology, software and calibration.** Work through the three options.

*Avia acquires redistribution rights.* Sabre and OAG both sell redistribution/OEM arrangements, priced for the likes of Cirium. For a firm of Avia's size the fee would dwarf the product revenue for years, and negotiation alone would outlast the window. Discard.

*Avia serves forecasts computed on its own licensed data (SaaS with bundled data).* A forecast number is derived data. Standard MIDT and OAG terms permit internal use and permit including derived insights in consultancy deliverables; they prohibit providing third parties with data, or derivations that substitute for the data, as a service. A subscription product whose value is "query our MIDT-derived engine" walks straight into that clause. Some vendors would tolerate it, all would want paying, and the product would carry a termination-clause risk no airport procurement team should accept. Discard as the primary model; it is negotiable later from a position of strength.

*Customer brings their own licences; the product ships as methodology over the customer's data.* This works, and the offline architecture was accidentally built for it. Most target airports already subscribe to OAG in some form, and MIDT extracts scoped to an airport's own catchment are a routine purchase (and far smaller than 91GB, which solves the deployment size problem at the same time). Cortex ships as: the software, the frozen QSI methodology, the calibration constants and the published track record; the customer's Sabre/OAG extracts load through a documented ingestion path; forecasts are computed on their machine from their data. Avia redistributes nothing. Two actions make this real rather than assumed: get the position confirmed in writing against Avia's actual Sabre and OAG contracts (I am not a lawyer, and specific derived-data clauses vary by agreement and vintage), and build the customer-extract ingestion path, which does not exist today and is the main engineering gap between demo and product.

One nuance to preserve: the calibration evidence base itself (the 3,549 graded launches) was computed on Avia's licensed data. Publishing the aggregate track record (medians, bands, hit rates) is comfortably an insight, not a redistribution; shipping the underlying per-route CSV to customers is not. Keep the evidence aggregate in anything that leaves the building.

### Deployment, pricing, moat

**Deployment:** on-prem/airport-owned wins, and not just for data rights. It matches the offline design, avoids building a multi-tenant platform Avia cannot staff, and turns the buyer's IT-security review from a SaaS interrogation into a desktop-software rubber stamp. Ship as a pinned installer (the DEPLOY_DEMO work generalises), one machine per licence, no telemetry beyond a licence ping.

**Pricing:** anchor on the study budget it replaces, not on software comparables. A shape that fits the buyer: Stage 1 pilots at £25-40k/year including onboarding, data-ingestion setup and a support allowance; licensed product at circa £30-60k/year per airport by size, with Avia consultancy days on top for pitch support. Per-case pricing undersells the tool's always-on value and invites the buyer to ration usage; per-seat pricing is meaningless for a two-person ASD team. The price watchpoint: stay clearly below the cost of two incumbent studies a year, because that is the arithmetic the airport's finance director will do.

**Moat, honestly.** The methodology is replicable: QSI is published art, and any competent shop with MIDT and OAG could rebuild the pipeline in a year. What is hard to copy is the graded six-year evidence base and the willingness to publish it, the quarterly recalibration cadence, and the analyst judgement frozen in the scorer. That is a 12-24 month head start and a positioning asset, not a patent. Two protections worth the effort: document the frozen QSI thoroughly (it currently lives partly in Ollie/JZ-era knowledge and John's head, which is key-person risk, not IP), and keep publishing the track record so that "show us your back-test" becomes the question every competitor gets asked.

### The staged pathway

**Stage 0, now to Routes (Jul-Sep 2026).** Cortex is a consultancy instrument. Sell studies and route cases produced with it; the tool appears as Avia's advantage, not as a SKU. Deliverables leave as decks and workbooks, which keeps data rights untested. Blocking risks: the demo failing in public (mitigated by section 3 items 1-7), and an airline planner discrediting a number on the stand (mitigated by the confidence band, the induced badge, and never demoing an induced case as calibrated).

**Stage 1, first paid pilots (Q4 2026 - Q2 2027).** Two or three airports John already knows, sold as consultancy-plus-tool: an annual engagement in which the airport gets the tool on its own machine, its own data licences confirmed, training, and Avia support on live cases. Price £25-40k. Success measure is renewal intent and cases actually taken to airlines, not licence revenue. Blocking risks, plainly: the data-rights confirmation letter (do not install on customer hardware without it); the ingestion path not existing yet; support falling entirely on John (cap pilots at three for exactly this reason); and the induced boundary disappointing a pilot whose pet route is white space (set the boundary in the sales conversation, not after).

**Stage 2, licensed product (from mid-2027, only if pilots renew).** Installer, licence terms, documentation, a named second person for support, the comparable-market induced model shipped, quarterly recalibration operating as a service. Blocking risks: support economics at more than a handful of customers; a data vendor changing posture once the product is visible (the written confirmation from Stage 1 is the insurance); and the evidence base ageing if the recalibration cadence slips.

The honest summary of the commercial picture: this is a strong consultancy multiplier today, a plausible £100-300k/year licence line within 18 months if pilots convert, and not a software company. Invest on that basis and the downside is bounded at the cost of the productisation work, most of which improves the consultancy either way.

---

## 5. Prioritised list (single sequence)

1. Git, quarantine, pinned environment (S1, S5, S11). Everything else becomes safer.
2. Calibration/mask configuration decision + confirming run (S2).
3. Induced badge and comparable-launches presentation (S4).
4. Feed-method badge and fallback surfacing (S3).
5. Confidence band on the result card (F1), then chips/rails/polish (F2, M6, F7-F10).
6. Demo deployment rehearsed on the real laptop (S11, D1-D9).
7. Deck generator first working version.
8. August: three to five friendly-airport walkthroughs; fix what confuses them.
9. Routes (late September): stand, staffed, pre-booked meetings, demo of underserved and reinstatement cases only.
10. Q4: data-rights letters; pilot agreements; ingestion path; comparable-market induced model; monthly Sabre and seasonal calibration; parameterised SQL and locking for pilot installs.

---

*Fable, 6 July 2026. Evidence: repository state as read this session, agent-verified module reviews (inventory, portal/calibration, feed/catchment/economics), bt_6yr_det and bt_v2_6yr_factored calibration reads, and the 5 July review and progress notes.*
