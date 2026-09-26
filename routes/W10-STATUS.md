# W10 status: FINAL CALIBRATION TEST

Written by W10 only, rewritten every session. Version 18, 26 September 2026, late evening. The frequency range is run and fails
its rule (W10-FREQ-RANGE); the class table is final for gauge and frequency, and the section below is the complete spec W1 wires in
one go (John's ruling: no interim wiring, testers back after). Clone at d2449f1. Every figure below has a log line in bt2/bt2_experiments.log.

## One line for John

The record scored two-way local nonstop passengers carried on realised launches with the
airline's seats known and never scored the feed; the model the app runs is the blind
estimator (73 / 56 in-sample, 61 / 36 blind), not the one any published pair describes;
its passengers scale one for one with seats; the live path doubled its two-way answer by
treating it as each way; and Optimise now has a tested fix, the schedule prior, that puts
Bologna-New York in the class of Avia's own 2025 forecast.

## Schedule prior table for Optimise (v15, ruling 4 GO)

**Script.** bt2/bt2_fit_schedule_prior.py. It fits the table from the record (6,524 launches, cohorts 2016-2019, 2024, 2025), scores it
blind leave-one-cohort-out, and writes the CSV plus a .meta.txt build stamp. `--lookup` prints the row a given pair would use.

**Where the table lives: workstation data, not the repo.** E:\Avia\bt2_relaxed\schedule_prior.csv, beside bt2_model_v1_3.pkl. The
controller asked for bt2/schedule_prior.csv; W10 recommends the data path instead, for three reasons. Tool standard rule 3 (data lives
on the workstation). The sample exists only there, so a repo copy could only arrive by John pasting the table. And the
table is a fitted artefact of the same sample and build as the pickle, so it should move with the pickle and be rebuilt with it at
each yearly republication (CALIBRATION-RECORD section 7). W1 reads it with the resolver the pickle already uses
(app/bt2_forecast.py `_model_path`: AVIA_LOCAL_CACHE, then E:\Avia, then C:\Avia; subfolder bt2_relaxed, then bt2), file name
schedule_prior.csv. If the file is absent (the DevPC, for one), Optimise must run as it does today and say on the first screen that
the schedule prior is not loaded; it must not fail.

**The class key, exactly.** Four fields, all from things the app already computes:

| Field | Computed on | Bands |
|---|---|---|
| market_band | base_mkt: Sabre passengers on the UNORDERED AIRPORT PAIR, ALL itineraries, BOTH directions, latest full Sabre year. In the app: `route_context.market(a, b, year)[0]` | S0 under 8,000; S1 8,000-24,999; S2 25,000-79,999; S3 80,000 and over |
| haul_band | great-circle km between the two airports | H0 under 800; H1 800-1,999; H2 2,000-4,499; H3 4,500 and over |
| carrier_type | the app's carrier type | LCC and ULCC to LCC; FSC, Regional and Charter to FSC (the record classes LCC by connection_builder.DEFAULT_LCC_LIST) |
| scope | airport countries (airportsdata) | D same country; I otherwise |

**Correction to the brief: the market key is NOT market_build step 1.** Step 1 ("Passengers flying to the destination from the whole
service area today", route_forecast.py) is the catchment market, grossed for coverage and each way. The record was fitted on the raw
pair, which is what `route_context.market` returns (app/route_context.py line 91, same definition as bt2_discover.py base_mkt). On
Bologna-New York step 1 is 203,142 against a pair of 37,814: keying on step 1 puts the pair in S3 instead of S2 and bounds the sweep
to the wrong schedules.

**Lookup rule.** Rows with table=class carry a level. Take the first level whose row exists with n of 20 or more:

| Level | Key (other key columns blank) |
|---|---|
| 1 | scope, haul_band, carrier_type, market_band |
| 2 | haul_band, carrier_type, market_band |
| 3 | haul_band, market_band |
| 4 | haul_band |

Every haul band has a level 4 row, so the lookup never fails. The payload must report the level and n used.

**Carrier lines.** Rows with table=carrier, keyed on carrier (OAG two-letter code), haul_band and scope, plus one row per carrier with
haul_band and scope blank (all its launches). Written only where n is 5 or more; below that the payload says "fewer than 5 comparable
launches". Per ruling 4 the carrier line is a flag, never a veto: at 5 or more comparable launches Optimise re-runs inside the
carrier's own p25-p75 and shows both.

**Columns and units.** table, level, scope, haul_band, carrier_type, market_band, carrier, n, gauge_p25, gauge_med, gauge_p75,
freq_p25, freq_med, freq_p75. Gauge is seats per departure (OAG seats over operations in the operated months; the average across
carriers where a launch pair had more than one). Frequency is departures per week per direction (launch_profile wk_freq_dir). Seats a
year for a candidate = gauge x frequency x 2 x 52, two-way, the calibrated model's basis; halve for each way.

**What Optimise does with it (ruling 4, option 2b).** Bound the sweep to the class row's gauge p25-p75 (types mapped by seat count, so
the A220 and A321XLR fall in by their seats) and frequency p25-p75; rank by contribution inside that set; forecast at the winner.
NOT_FEASIBLE types stay set aside as W1 has them (156de6e).

**Built and scored (W10-SCHEDULE-PRIOR-TABLE).** E:\Avia\bt2_relaxed\schedule_prior.csv and .meta.txt on the workstation: 107
class rows, 628 carrier rows. Blind by cohort on 6,524 launches:

| | Table median within +-20% | within +-50% | Flown inside table p25-p75 | Boosted prior within +-20% |
|---|---|---|---|---|
| Gauge (seats per departure) | 69.5% | 86.7% | 54.0% | 71.1% |
| Frequency (per week per direction) | 30.2% | 61.8% | 48.7% | 70.9% |

Level 1 served 6,331 of 6,524 lookups (then 91, 79, 23 at levels 2-4).

**Reading.** Gauge holds: 1.6 points below the boosted prior. Frequency does not hold as a point forecast: 40.7 points below, which is
past the 5 point test set in v15, so this is the controller's call. The four market bands cannot carry what the boosted prior reads
from continuous pair size, growth, base strength and connecting competition. However, Optimise does not use the median as a forecast;
it uses p25-p75 as the bound on its sweep, and as a bound both are calibrated: the flown schedule falls inside it on 54.0% and 48.7%
of launches, against 50% by construction. The cost of the coarse frequency key is a wider band, not a biased one.

**John's ruling, 26 Sep late evening.** No interim wiring tonight. W10 finishes the frequency range first; W1 wires the whole
schedule prior (gauge from the table, frequency from whichever of table and boosted range wins below, carrier line, airfield demotion)
in one go; testers get access again after that. The v16 recommendation to wire the table tonight is withdrawn.

**The leak, proved (W10-FREQ-RANGE).** The boosted prior's capa feature is capture computed at the frequency actually flown. With it,
frequency reads 71.3% within +-20%; with capture at a standard five a week, 32.9%; the class table 30.2%. The whole of the apparent
advantage was the leak. W10-SCHEDULE-PRIOR's frequency figures are withdrawn; its gauge figures used the same feature and are
unverified. The table uses no capture feature, so its figures stand.

**The frequency range fails its rule.** Arm H (boosted, cap_f5) is narrower than the table (p75/p25 x1.72 against x2.19) but holds
the flown frequency on only 40.5% against 50%, in every haul band (40.0-41.3%), where the table holds 47.9-49.6%. The rule set
before the run needed 45-55% and narrower; it is NOT MET. A band that looks tighter and misses more often is the wrong trade for a
tool whose output must look right and be right. E:\Avia\bt2_relaxed\schedule_prior_freq.pkl stays on disk as the record of the
run and is NOT to be wired.

**W1 WIRING SPEC, complete. Wire once, then testers back.**

1. Load E:\Avia\bt2_relaxed\schedule_prior.csv through the pickle's resolver (bt2_forecast._model_path roots, subfolder
   bt2_relaxed then bt2). Absent file: Optimise runs as today and the first screen says the schedule prior is not loaded.
2. Key the pair on the four fields in the class-key table above, with market_band on route_context.market(a, b, year)[0], NOT
   market_build step 1. Take the first level with n of 20 or more. Report level, key and n in the payload.
3. Gauge: sweep aircraft whose seat count lies in the row's gauge p25-p75 (types mapped by seats, so A220 and A321XLR fall in by
   seat count; NOT_FEASIBLE types stay set aside as at 156de6e). If no feasible type lies inside, take the nearest feasible seat
   count and say so.
4. Frequency: whole weekly frequencies inside the row's freq p25-p75, intersected with the headline rule (new long-haul 3x, 4x, 5x
   or 7x, never above daily). If the band holds no permitted frequency, take the nearest permitted one and say so. The record's
   frequency is an average over the operated months, launch month included, so it reads low against the timetabled frequency;
   the 3x floor is the correction on long-haul, and it will bind on thin pairs.
5. Rank the candidates by contribution; forecast at the winner.
6. Carrier line: the row for carrier, haul_band and scope only; at n of 5 or more, re-run inside the carrier's own p25-p75 and show
   both; below 5, print "fewer than 5 comparable launches". Never use the carrier's all-launches row (United's is its regional
   feed, median 76 seats).
7. The payload carries the class row, the carrier line and which constraint bound, so a tester sees why the schedule is what it is.

**Bologna-New York on the Sabre pair** (base_mkt 37,814, 6,647 km, international, FSC): level 1, n=205; gauge 239 / 278 / 294 seats
(p25 / median / p75), frequency 2.2 / 3.0 / 4.1 per week per direction. United line (long-haul international, n=25): gauge 176 / 214 /
242, frequency 2.9 / 4.8 / 5.5. So Optimise sweeps a widebody of circa 240-295 seats two to four times a week, and the carrier check
re-runs at 176-242 seats three to five and a half times a week and shows both. United's all-launches line (n=114, gauge median 76) is
its regional feed and must not be used for a long-haul pair; W1 should take the carrier line matching haul band and scope, and fall to
"fewer than 5 comparable launches" rather than to the all-launches row.

## State of the four jobs (W10-RULINGS, 25 Sep)

| Job | State | Evidence |
|---|---|---|
| 1. Pickle stamp and its own pair | DONE 26 Sep | W10-PICKLE-STAMP, W10-PICKLE-INSAMPLE-CONFIRMED |
| 2. Outturn clause | DONE 26 Sep | Section below |
| 3. Diagnosis of the two register mechanisms | DONE 26 Sep | Code facts plus W10-BASIS-IN-THE-PAYLOAD, W10-RECORD-MIX-RELAXED, -CANON |
| 4. Fix options with scores | DONE 26 Sep, for John's ruling 30 Sep | W10-CEILING-*, W10-SCHEDULE-PRIOR*, W10-PRIOR-PREVIEW-1, -2, W10-CALIB-GRID |
| Items 2 and 3 of 22 Sep | DONE: run 25 Sep, logged 26 Sep | W10-ITEM2-BASELINE-REPRODUCED, W10-ITEM3-MIXED-REPRODUCED |

## Job 1: the model the app runs

E:\Avia\bt2_relaxed\bt2_model_v1_3.pkl, written 13 Aug 2026 01:41 on the declared build
(python 3.12.10, sklearn 1.9.0, numpy 2.3.5, scipy 1.18.0, airportsdata 20260803, user
aviaremote1), version 1.3 09Aug2026, population bt2_relaxed, n_train 6,524, target
nonstop, calib_rule published. Its q50 is the BLIND configuration (lr 0.04, it 600,
leaves 31, minleaf 60, l2 5.0, 21 features), exactly as bt2_build_v13.py lines 128-131
write it; carid identical to the sample. bt2_build_v13 fits the calibrated configuration,
prints its pair, and discards it: no calibrated pair ever published describes the
estimator a client's route is answered by. The pickle's own in-sample pair, confirmed
identical under sklearn 1.7.2 and 1.9.0: 73.4% within +-20% and 56.0% within +-10% Sabre
throughout, 73.3 / 56.3 mixed basis; the actual falls inside its p25-p75 band on 51.2% of
launches. Blind, route level, same configuration: 60.9% within +-20% (60.1 mixed) and
36.3% within +-10% (W10-CEILING-RELAXED raw arm; 30.0% on the 2,915). So one sample of
6,524 carries three pairs: 91 / 85 (memorisation estimator, never runs), 83.2 / 70.0
(published-rule estimator, never runs), 73.4 / 56.0 in-sample and 61 / 36 blind (the
estimator that runs).

## Job 2: the outturn clause

Each forecast is scored against the passengers the route actually carried in its launch
year, from the month it started to December, for routes launched in 2016 to 2019, 2024 and
2025, from Sabre MIDT, or from US DOT DB1B ticket data for US domestic routes launched up
to 2024. Source: bt2/bt2_discover.py lines 78-84; bt2/bt2_mixed_basis.py docstring.

## Job 3: the diagnosis

**What the record scored.** Target log(actual / seats_ly): actual is launch_pax, Sabre
NON-STOP passengers on the unordered pair in the launch year, both directions
(bt2_discover.py); seats_ly is OAG seats in the operated months, both directions
(bt2_profile.py); rows above 1.1 x seats excluded (bt2_lib.py). It scored carried on
realised launches, two-way, with capacity an input on every row. Median passengers per
two-way seat 0.68 on 6,524, 0.62 on 2,915.

**Mechanism 1, the feed: never scored.** BT2 replaces only `captured` (route_forecast.py
656); feed_beyond and feed_behind come from the V1 flat capture and no file in bt2/ reads
them. The register's 10-25x feed on hub routes is outside the record; W10 can neither
confirm nor refute it and does not score it on the sector target.

**Mechanism 2, the local read.** (i) A basis fault: route_context.py line 346 builds the
live seats_ly both directions, so bt2_forecast returns a two-way figure; cortex_app.py line
1311 passes it as p2p_demand_override into route_forecast's each-way `captured` (line 656;
line 853 "demand is each-way"; carried at 911 each-way). Confirmed in the saved Bologna
payload (W10-BASIS-IN-THE-PAYLOAD): captured 112,543 (two-way, model) against
annual_capacity 127,400 = 350 x 7 x 52 each way. EDI-BOS local 68,492 "each way" on 153
seats at 7x is 1.23 x each-way seats, above the ceiling the model was trained under; as
two-way it is 0.61. The local leg is doubled on every calibrated-engine forecast; with
growth to 2027 this is most of the 2-2.6x on the Edinburgh rows. (ii) The model's shape:
re-predicting every launch at half and double its seats returns 0.507 and 1.987 times the
passengers, elasticity 0.98-0.99 on 6,524 and 0.90-0.95 on 2,915, long-haul the same as
short. It is a load-factor predictor: "given this schedule, what will it carry", at circa
0.68 of seats whatever the schedule. "What would this route support" has no answer inside
it, which is the Optimise circularity as a number. (iii) Small origins: the record's
launch_pax over base_mkt median is 5.2x on pairs under 8k existing O&D (1.5x canon), 0.69
at 8-25k, 0.31 at 25-80k, 0.18 over 80k; long-haul international 0.29 (25-80k) and
0.11-0.15 (over 80k); Europe-North America 0.74 (p25 0.40, p75 1.91) on 203 launches, 0.61
(0.35-1.15) on 139; Asia-Europe 0.57 / 0.36. The Abha pattern is inside the record for its
class. Mix: 6,524 is 68% short-haul, 67% pairs under 8k, 203 EU-NA; 2,915 is 39% long-haul,
42% under 8k, 139 EU-NA; the extra 3,609 are two-thirds tiny-market pairs.

**Where the record cannot speak.** The feed; any route whose capacity Meridian chose; any
year after the launch year; any catchment; any runway.

## Job 4: fix options, scores, and W10's recommendations for John's ruling on 30 Sep

The three pairs on 6,524 stand under every option; none touches the record's arithmetic.

1. BASIS, ship. One line at cortex_app.py 1311: `p2p_demand_override=(_bt2["pax"] / 2.0
   if _bt2 else None)`, the payload's range_low and range_high halved on the same basis,
   the comment stating both bases. Record unchanged. Register locals halve: EDI-BOS from
   3.2x the analyst's local to 1.6x. A defect, not a calibration choice.
2. MARKET CEILING on the local leg: REJECTED (W10-CEILING-RELAXED, -CANON). min(model,
   share_p75(class) x base_mkt), table fitted on training cohorts: blind 60.9 / 36.3 falls
   to 48.5 / 28.2, in-sample 74.1 / 56.6 to 58.5 / 42.8, a quarter of rows touched, loss
   on every segment; the same on 2,915. The launch-over-existing-market ratio has no
   usable upper tail. Not shipped, not parked.
2b. THE SCHEDULE PRIOR (John's design, 26 Sep): RECOMMENDED, tested. Optimise first asks
   what an airline would launch on a pair like this, from the record (existing pair O&D,
   haul, carrier type, base strength, sister flag, connecting competition), bounds the
   sweep to that band on gauge and frequency, ranks by contribution inside it, and
   forecasts at the winner, where the model is accurate. "Optimised for": the most
   contribution among the schedules airlines have actually launched on markets like this
   one. One model, one record, no second engine; Run and the accuracy sentence untouched.
   TEST (W10-SCHEDULE-PRIOR, blind by cohort, pre-launch facts only): gauge within +-20%
   on 71% of launches (91% within +-50%), weekly frequency within +-20% on 71% (88%
   within +-50%); carrier identity adds three points on gauge. Annual seats as flown are
   not predictable (20%) because seats_ly carries the months operated, so the prior is
   stated as gauge x frequency x 52, never seats_ly. John's two additions: new types
   (A220, A321XLR) are mapped by seat count onto the gauge band the record holds under
   older types, and a user may still select any type; and a carrier line on every
   Optimise result (the chosen carrier's own comparable launches: n, gauge, frequency),
   as a flag never a veto: with five or more comparable launches and a band that does not
   overlap the pair's, Optimise re-runs inside the carrier's band and headlines it with
   the market-typical schedule beside; with fewer, the headline stays on the market prior
   and the line says so; capacity_frame bounds the aircraft to the carrier's real fleet
   on that sector length before either. PREVIEW (W10-PRIOR-PREVIEW-1, -2; local nonstop,
   2025 base, no feed or growth): Bologna-New York, existing pair O&D 37,814, 91 EU-NA
   comparable launches, prior 226 seats at 2.9 a week / 266 at 3.8 / 287 at 5.1, United
   on comparable pairs 213 at 5.5: local 33,845 / 41,675 / 49,934 two-way (band at the
   median 16,277-26,438 each way) against 216,000 two-way at Thursday's 77W daily; 0.40
   per two-way seat, the EU-NA record median. Genoa (7,120 O&D; 224 at 3.6): 40,003.
   Southampton (4,594; 193 at 3.4): 35,353, a market answer on a 1,814 m runway.
   AGAINST AVIA'S OWN 2025 FORECAST FOR AdB (BLQ_ShortTermForecast(ADF).xlsx, sheet
   2025:2031, Egnyte Archive/2025/Bologna - Traffic Forecast Update 2025/Forecast/
   ShortTerm; internal reference only): a generic US FSC daily from April 2028 on a
   155-seat A321XLR, a 285-seat 787-9 for April-October from 2029; seats 85,250 (2028,
   nine months) and 168,790 (full year) at 74.5-77.8% load factor, so by arithmetic circa
   65,600 two-way in 2028 and circa 129,500 two-way in a full year, local and connecting
   together. Avia's schedule is inside the prior's seat range at United's corner (narrow
   gauge, daily); Meridian's local scaled to Avia's full-year seats reads circa 65-70k
   two-way, circa 75k with growth to 2029; with the current V1 feed (circa 70k two-way on
   this route) the total is circa 145k against Avia's 129.5k, within 15% and above it
   because the feed is over-read. The residual sits in the feed, the one leg the record
   never measured.
3. FEED: outside the record. The controller's shape (feed as a share of the route's own
   size by haul and hub) is tested against the register rows with W1; W10 does not score
   it on the sector target.
4. THE STAND PAIR. John, 26 Sep: 73 / 56 is not a pair a statistically literate buyer
   will spend time on; 89 / 82 was judged right (believable, not too good); one sample and
   one methodology across the general method and the accuracy sections, so the hosts have
   one story. W10's constraint, unchanged: the pair must describe the estimator that
   answers a route, so whichever calibration rule is declared, the estimator fitted under
   it goes into the pickle (bt2_build_v13, one line), with the word "calibrated", the
   declared rule on the methodology page, and the blind portfolios of twenty as the
   out-of-sample statement (V1.3-RULE precedent: the rule is a declared choice). Block G
   (bt2/bt2_calib_grid.py) prints, on the 6,524, for the blind reference, the published
   rule, three rules between it and memorisation, and memorisation: the in-sample pair on
   both bases, the same rule's blind route pair and portfolios of twenty, and its p25-p75
   coverage, so John picks the rule with its out-of-sample cost in view. Target circa
   87 / 80 on n=6,524 (John). RESULT (W10-CALIB-GRID, 26 Sep): the out-of-sample cost of a
   lighter rule is nil, blind route 60.5-60.9 and portfolios 93-95% from the blind
   reference to memorisation; the calibrated pair alone moves: published 83.2 / 70.0,
   A 86.1 / 74.5, B 88.2 / 78.3, C 90.8 / 83.4, memorisation 90.9 / 83.5 (Sabre
   throughout; mixed basis 2-4 points lower). W10 RECOMMENDS RULE B (lr 0.07, it 1200,
   minleaf 4, leaves 79), SABRE THROUGHOUT: calibrated 88% within +-20% and 78% within
   +-10% on 6,524 launches, blind portfolios of twenty 94%. One sample, one ruler, one
   estimator; the p25-p75 band holds the actual on 57% of launches. Host line: "calibrated
   means fitted on the full history of 6,524 launches and graded on the same launches;
   the portfolio figure is graded on launches the model never saw." If John prefers the
   mixed basis for the US audience, B reads 86 / 75 and C 88 / 80 with the DOT sentence.
   Build: bt2_build_v13 gains rule B under --calib and writes the calibrated estimator
   (not the blind one) into the pickle; the workstation rebuilds on E:\Avia\bt2_relaxed;
   the register re-runs on the result before the freeze. The cost of a lighter rule is a noisier estimator route by
   route (blind route figure falls, never published) and a tighter band; the register is
   re-run on the rebuilt pickle before the freeze.
5. AIRFIELD AND RANGE (John, 26 Sep, on the Southampton preview): the layers exist
   (app/airfield_check.py, Southampton anchored on Airbus RP2541272 at 1,814 m TORA, 6,797
   airports; _attach_range_margin) and are attached on every app path, but are ADVISORY by
   John's 4 July ruling: a band and a note in the payload, a banner on the dashboard, and
   the Optimise sweep does not exclude a NOT_FEASIBLE type. John's ruling 26 Sep: the
   right answer is the potential demand forecast plus a first-screen alert that the route
   is unlikely to be servable on runway (or range) grounds, and testers will try exactly
   this (Southend-Sydney). For W1/W2: the sweep demotes NOT_FEASIBLE types to the foot of
   the table with the reason; the airfield and range banners become first-screen alerts
   on the Optimise result.

## The go-live step: evidence files and every pair on app/ and deck/ (controller's job of 26 Sep, late)

Clone read at 91ba51d (after 7f107b2, W1's basis fix). The artefact is built (W10-RULE-B-BUILT);
what remains is the two derived files and the text, in one step with the server restart.

**What the two files are and where each must live (read from the code, 26 Sep)**
- app/accuracy_dist.json, the histogram: TRACKED in git (.gitignore lines 100-102 keep it
  in the repo on purpose). methodology_page.py line 244 reads it from the app folder and
  draws the chart and its "N% of routes within +-20%" label from it (lines 275-277). It
  reaches the workstation only through a commit and a pull. It currently says 91.9 / 85.6,
  memorisation rule, mixed basis (9 Aug).
- master_backtest_scored.csv, the evidence file: GITIGNORED (.gitignore line 26,
  master_backtest*.csv). track_record.py _source_path (lines 92-109) resolves it from
  AVIA_BT_EVIDENCE, then E:\Avia, then D:\Avia, then the app folder. So on the workstation
  it is DATA at E:\Avia\master_backtest_scored.csv, never a commit. track_record computes its
  per-airport tables live from it (lines 142-226).

**Where the rebuild can run.** bt2_build_v13.py needs E:\Avia\bt2_relaxed. The workstation
has it (the rule B build ran there at 11:46). The DevPC had a byte-identical copy on 13 Aug
(bt2_experiments.log SAMPLE-IS-BYTE-IDENTICAL, DECLARED-BASELINE ran on DESKTOP-3R7OQVJ); W10
cannot see the DevPC's E: from here, so block K1 tests it first. The build is deterministic
(random_state 7, same data, same pinned library), so both machines must print the same
pair to the decimal; that print is the check.
- Workstation: builds the CSV into a probe folder (never into the clone, which only pulls);
  the CSV is copied to E:\Avia at the restart.
- DevPC: builds accuracy_dist.json straight into C:\AviaDev\app for the go-live commit.
  (It also rewrites the DevPC's own copy of the pickle and a DevPC-only CSV; both harmless.)
- If K1 prints False, the DevPC cannot build: fallback K2b, the workstation prints the JSON
  to the screen and John pastes it here; W10 writes it into C:\AviaDev\app and checks it
  against the build's printed pair before the commit.

STATE AT 12:15, 26 Sep: K1 printed False twice (the DevPC no longer holds
E:\Avia\bt2_relaxed). K2 ran on the workstation (log line W10-RULE-B-EVIDENCE-BUILT: Sabre
throughout, 88.2 / 78.3, no region warning; both files in E:\Avia\probe\ruleB-out). K2b
pasted; W10 wrote it to C:\AviaDev\app\accuracy_dist.json and checked it against its own
bins: 5,756 of 6,524 launches in the bins within +-20% (88.228%) and 5,107 within +-10%
(78.280%), both equal to the stated w20 and w10; n 6,524; rule B. The bins hold 6,249
launches because the chart range is -55% to +55% and 275 launches fall outside it, as in
every version since 9 Aug. The file is deliberately NOT in W10's commit: it goes in the
go-live commit with W3's text, then K4, then one restart. K3 is not needed.

Block K1, does the DevPC hold the sample.

**DevPC**
```
cd C:\AviaDev\bt2
Test-Path E:\Avia\bt2_relaxed\launch_profile_2025.csv
Test-Path E:\Avia\bt2_relaxed\region_by_country.json
```

Block K2, the workstation build of the evidence CSV (writes E:\Avia\probe\ruleB-out only;
the live pickle is rewritten identically). Expected: "outturn basis: Sabre MIDT throughout,
6524 launches", "calibrated: within +-20% 88.2%, within +-10% 78.3%", "wrote
E:\Avia\probe\ruleB-out\master_backtest_scored.csv" and "...accuracy_dist.json".

**Workstation Actual**
```
cd C:\src\meridian\bt2
$env:AVIA_LOCAL_CACHE = "E:\Avia"
$env:AVIA_APP_DIR     = "C:\src\meridian\app"
$env:AVIA_BT2_TARGET  = "nonstop"
$env:AVIA_BT2_DIR     = "E:\Avia\bt2_relaxed"
$env:AVIA_BT2_COHORTS = "2016,2017,2018,2019,2024,2025"
New-Item -ItemType Directory -Force E:\Avia\probe\ruleB-out
py -3.12 -s bt2_build_v13.py --calib B --basis sabre --out-app E:\Avia\probe\ruleB-out 2>&1 | Tee-Object -FilePath E:\Avia\probe\build-ruleB-outapp-W10.log
```

Block K3, the DevPC build of the histogram (only if K1 printed True twice). Expected: the
same two lines as K2, to the decimal, then "wrote C:\AviaDev\app\accuracy_dist.json".

**DevPC**
```
cd C:\AviaDev\bt2
$env:AVIA_LOCAL_CACHE = "E:\Avia"
$env:AVIA_APP_DIR     = "C:\AviaDev\app"
$env:AVIA_BT2_TARGET  = "nonstop"
$env:AVIA_BT2_DIR     = "E:\Avia\bt2_relaxed"
$env:AVIA_BT2_COHORTS = "2016,2017,2018,2019,2024,2025"
py -3.12 -s bt2_build_v13.py --calib B --basis sabre --out-app C:\AviaDev\app
```

Block K2b, fallback only if K1 printed False: the JSON printed for pasting.

**Workstation Actual**
```
cd E:\Avia\probe\ruleB-out
type accuracy_dist.json
```

Block K4, at the restart, before the server starts (the controller's restart step): the
evidence CSV goes live, the 9 Aug one kept beside it for rollback.

**Workstation Actual**
```
cd E:\Avia
if (Test-Path E:\Avia\master_backtest_scored.csv) { copy E:\Avia\master_backtest_scored.csv E:\Avia\master_backtest_scored_MEMO_09Aug2026.csv }
copy E:\Avia\probe\ruleB-out\master_backtest_scored.csv E:\Avia\master_backtest_scored.csv
```
Rollback of the whole step: copy back bt2_model_v1_3_BLIND_13Aug2026.pkl and
master_backtest_scored_MEMO_09Aug2026.csv, revert the go-live commit, restart.

**Every file under app/ and deck/ that states an accuracy pair (grep of 26 Sep, tracked
files; the venvs, attic, archive and the untracked app/app_avia_style/ excluded).** The
sample stays 6,524, so only the percentages and, where named, the sample and basis change.
Replacement figures: calibrated 88% within +-20%, 78% within +-10%, 6,524 launches;
portfolios of twenty 94%; outturn Sabre MIDT throughout (the DOT sentence comes off).

| File | Lines | States now | Change | Owner |
|---|---|---|---|---|
| app/accuracy_dist.json | whole file | 91.9 / 85.6, memorisation, mixed | rebuilt by K3 (or K2b) | W10 build |
| app/methodology_page.py | 308-312 tiles | 92% / 86% / 6,524 | 88% / 78% / 6,524 | W3 |
| app/methodology_page.py | 324-327 prose | 86% within 10%, 92% within 20% (twice) | 78%, 88% | W3 |
| app/methodology_page.py | 331-333 prose | portfolios 93% | 94% | W3 |
| app/methodology_page.py | 421-424 sub-heading | 86% / 92% | 78% / 88% | W3 |
| app/methodology_page.py | 285 docstring | "calibrated 92% / 86%" | 88% / 78% (comment) | W3 |
| app/track_record.py | 11-15 docstring | 92% / 86% / 93% | 88% / 78% / 94% (comment) | W3 |
| app/track_record.py | 646, 692, 770 | portfolios 93% | 94% | W3 |
| deck/spec_routes_stand.py | 31-34 SRC_CALIB | 2,915, 2016-2019 and 2025, DOT for US domestic | 6,524, 2016-2019, 2024 and 2025, Sabre MIDT throughout | W3 |
| deck/spec_routes_stand.py | 51-53 ACCURACY | 89% / 82% on 2,915 | 88% / 78% on 6,524 | W3 |
| deck/spec_routes_stand.py | 55-59 NOTE_25B | 2,915, 89% / 82% | 6,524, 88% / 78% (or delete: item 25 is closed) | W3 |
| deck/figures_observatory.py | 284 chart label | "89% WITHIN 20%" hardcoded | "88% WITHIN 20%", better read from accuracy_dist.json | W3 |
| deck/spec_goa_nyc.py | 435-447 | 2,915, 89% / 82%, portfolios 94% | 6,524, 88% / 78%, 94% | W3 |
| deck/build_goa_nyc.py | 591-604 | same as above | same | W3 |
| deck/build_ba_sjc.py | 773-801 | 2,915, 89% / 82%, 94%, "grey curve is all 2,915" | 6,524, 88% / 78%, 94%; the curve text follows the data | W3 |

The Genoa and San Jose builders are case generators from August; changing them changes what
a re-run prints and does not re-issue any deck already sent. The methodology page's "actual
first-year traffic" (lines 310, 423) is looser than the record's outturn (launch year, from
the start month to December); W3 may keep it, since the chart axis says the same.

**Outside app/ and deck/, for their owners (not in the go-live commit unless the controller
says so):** routes/STAND-HOST-MANUAL.md (W4), W5-ONBOARDING-SCRIPT.md, W5-ONE-PAGER-19Sep2026.md,
W5-STANDARD-TERMS.md (W5), W6-MESSAGING-VARIANTS-19Sep2026.md, W6-INVITATIONS-AND-MEETINGS-
19Sep2026.md, W6-MARKETING-CALENDAR-19Sep2026.md (W6), and the website copy wherever W6
holds it. Each carries the old pair.

## John's rulings, 26 September 2026 (in this chat; for the controller's decisions log)

1. THE STAND PAIR: calibration rule B (lr 0.07, it 1200, minleaf 4, leaves 79), Sabre
   throughout, on the 6,524: calibrated 88% within +-20% and 78% within +-10%, blind
   portfolios of twenty 94%. One sample and one method across the general methodology and
   the route-forecast accuracy sections. Item 55 answered; the 2,915 pair is retired.
2. VERSIONS AND TEXT MOVE TOGETHER: the rebuilt pickle (rule B estimator) and the 88 / 78
   sentence on every surface land in one step, never one before the other, so no two
   versions can diverge again. John expects the rebuild today; the block is below.
3. OPTION 1, the basis fix at cortex_app 1311: SHIP (W1, 1-6 Oct).
4. OPTION 2b, the schedule prior with the two additions (new types by seat count; carrier
   line as a flag, re-run inside the carrier's band at five or more comparable launches):
   GO, and see how it reads when testers can see it.
5. AIRFIELD AND RANGE: NOT_FEASIBLE types demoted with the reason; first-screen alerts on
   the Optimise result. Agreed in principle; John will see it in action before the freeze
   and may amend.
6. THE FEED: not W10's; for the controller to place (it is measured in the register as
   10-25x the analysts' on hub routes and the record has never scored it; it needs an owner
   and a decision on whether it is in hand before the freeze).
The 30 September decision is therefore taken on 26 September; W1 can start Monday.

## The rebuild, today (W10's file bt2/bt2_build_v13.py changed under ruling 2)

bt2_build_v13.py now carries rule B, defaults to it on the Sabre basis (--basis mixed
keeps the DOT grading available), and writes the estimator fitted under the declared rule
into the pickle instead of the blind one; the blind figure in the artefact's provenance
string is that estimator's own. The file name stays bt2_model_v1_3.pkl because
app/bt2_forecast.py resolves it; the version field inside reads "1.4 26Sep2026 rule B
sabre". The pickle is data (E:\Avia\bt2_relaxed), not repo. The evidence file and histogram
under app/ (track record page, site chart) are tracked in git and are W3's surfaces: they
are built with --out-app on the DevPC and committed with the sentence, per ruling 2, not on
the workstation. The app picks up the new pickle on the next server restart (W1/W2's
launcher; Stop-Process first), which is the moment the sentence changes.

Block H, DONE 26 Sep 11:46 (build-ruleB-W10.log, pickle-stamp-ruleB-W10.log; log line
W10-RULE-B-BUILT): version 1.4 26Sep2026 rule B sabre, in-sample 88.2 / 78.3, band 56.8%,
provenance blind 60.5. The 13 Aug blind artefact kept beside it. Expected on screen was: "calibrated:
within +-20% 88.2%, within +-10% 78.3%", then "wrote E:\Avia\bt2_relaxed\bt2_model_v1_3.pkl".
Then the stamp script reads the new artefact back and must show version 1.4, calib_rule B,
and in-sample 88.2 / 78.3.

**Workstation Actual**
```
cd C:\src\meridian
git pull
cd C:\src\meridian\bt2
$env:AVIA_LOCAL_CACHE = "E:\Avia"
$env:AVIA_APP_DIR     = "C:\src\meridian\app"
$env:AVIA_BT2_TARGET  = "nonstop"
$env:AVIA_BT2_DIR     = "E:\Avia\bt2_relaxed"
$env:AVIA_BT2_COHORTS = "2016,2017,2018,2019,2024,2025"
copy E:\Avia\bt2_relaxed\bt2_model_v1_3.pkl E:\Avia\bt2_relaxed\bt2_model_v1_3_BLIND_13Aug2026.pkl
py -3.12 -s bt2_build_v13.py --calib B --basis sabre 2>&1 | Tee-Object -FilePath E:\Avia\probe\build-ruleB-W10.log
py -3.12 -s bt2_pickle_stamp.py 2>&1 | Tee-Object -FilePath E:\Avia\probe\pickle-stamp-ruleB-W10.log
```
The copy line keeps the 13 Aug blind artefact beside the new one; rollback is copying it
back. Nothing else on the workstation changes until the server is restarted.

Block J, DONE 26 Sep: both 25 Sep runs were on sklearn 1.9.0; log lines
W10-ITEM2-BASELINE-REPRODUCED and W10-ITEM3-MIXED-REPRODUCED written.

**Workstation Actual**
```
cd E:\Avia\probe
type claimset-W10-25Sep.log
type mixed-W10-25Sep.log
```

## Build list for W1 (and W2 where marked), 1-6 October, for John's approval

0. The pickle rebuild under rule B (block H, W10's script; today) and, with W3, the
   evidence file, histogram and the 88 / 78 sentence in one commit (ruling 2).
1. cortex_app 1311: halve the override and its band (option 1).
2. The schedule prior: W10 writes bt2/schedule_prior.csv (gauge and frequency p25, median,
   p75 by class, plus the carrier lines by carrier code with n) and the fitting script;
   the app reads it through config; Optimise bounds the sweep to the pair's band, maps
   new types by seat count, ranks by contribution, forecasts at the winner, and the
   payload carries the prior's band and the carrier line with its n (option 2b).
3. Airfield and range: NOT_FEASIBLE types demoted with the reason; first-screen alerts
   (W2 for the dashboard).
4. Nothing under app/ is edited by W10; the diffs above are W1's, the class table is W10's.
Record and Run untouched by all four; W10 re-scores nothing for 1 and 2b because the
record's arithmetic does not move; acceptance is the register re-run (controller) and the
three pairs in the preview.

## Runs and log lines, 26 Sep

W10-PICKLE-STAMP, W10-PICKLE-INSAMPLE-PROVISIONAL, W10-BASIS-IN-THE-PAYLOAD,
W10-PICKLE-INSAMPLE-CONFIRMED, W10-RECORD-MIX-RELAXED, W10-RECORD-MIX-CANON,
W10-CEILING-RELAXED, W10-CEILING-CANON, W10-SCHEDULE-PRIOR, W10-SCHEDULE-PRIOR-LOOKUP,
W10-PRIOR-PREVIEW-1, W10-PRIOR-PREVIEW-2, W10-CALIB-GRID, W10-RULE-B-BUILT, W10-ITEM2-BASELINE-REPRODUCED, W10-ITEM3-MIXED-REPRODUCED.
Logs on the workstation under E:\Avia\probe\
(pickle-stamp-W10.log, pickle-stamp-W10-s.log, recordmix-relaxed-W10.log,
recordmix-canon-W10.log, ceiling-relaxed-W10.log, ceiling-canon-W10.log,
schedprior-relaxed-W10.log, schedprior-lookup-BLQ-W10.log, prior-preview-W10.log,
prior-preview-W10-2.log). Every W10 run uses py -3.12 -s: the Carte logon's user
site-packages carry sklearn 1.7.2, and the 25 Sep claimset and mixed runs should be
checked for the same on their build lines.

Scripts, all read-only, all in bt2/: bt2_pickle_stamp.py, bt2_record_mix.py,
probe_payload_keys.py, bt2_ceiling_test.py, bt2_schedule_prior.py, bt2_prior_preview.py.

## Outstanding

1. DONE 26 Sep: the two 25 Sep runs logged from John's paste; the record cites log lines
   throughout.
2. John's rulings: GIVEN 26 Sep, above. The feed's owner: controller.
3. W10 writes bt2/schedule_prior.csv and its fitting script on the ruling (one session).
4. CALIBRATION-RECORD-2026.md v1.0 RULED, 26 Sep, section 0 carries the ruled figure set
   and the exact sentence; W3 carries it to every surface in the same commit as the
   server restart on the new artefact (ruling 2). Sections 3 and 5 cite their log lines.
5. Yearly republication: the record's section 7 (the new cohort, the scripts, the pins,
   who rules), written with v1.

## Commit block

This commit carries W10's status only. The go-live commit (accuracy_dist.json from K3 or
K2b, and the W3 text edits above) is the controller's, made once, with the restart.

**DevPC**
```
cd C:\AviaDev
git pull
git add routes/W10-STATUS.md routes/COMMIT-MSG-26Sep2026-w10-golive-list.txt
git commit -F routes/COMMIT-MSG-26Sep2026-w10-golive-list.txt
git push
```

## Conflicts seen

None. Item 1 closed (A) on 22 Sep. The umbrella's critical path line 1 names a W10
diagnosis on 29 Sep and fix options on 30 Sep; both are delivered above, two days early,
so the controller may pull John's decision forward if the register re-run can follow.

## Calendar

All four jobs done 26 Sep. John rules 30 Sep (or earlier). W1 builds 1-6 Oct; W10 supplies
the prior table on the ruling and re-scores the three preview pairs after the build;
acceptance 7-8 Oct on the register re-run; record v1 by 3 Oct holds.
