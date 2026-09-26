# W10 status: FINAL CALIBRATION TEST

Written by W10 only, rewritten every session. Version 9, 26 September 2026, close of the
26 Sep session. Supersedes v1-v8 in full. Clone at e7eaf9d plus uncommitted W10 files
listed in the commit block. Every figure below has a log line in bt2/bt2_experiments.log
(W10-* lines, 26 Sep) or is quoted from the controller's rulings file pending John's paste.

## One line for John

The record scored two-way local nonstop passengers carried on realised launches with the
airline's seats known and never scored the feed; the model the app runs is the blind
estimator (73 / 56 in-sample, 61 / 36 blind), not the one any published pair describes;
its passengers scale one for one with seats; the live path doubled its two-way answer by
treating it as each way; and Optimise now has a tested fix, the schedule prior, that puts
Bologna-New York in the class of Avia's own 2025 forecast.

## State of the four jobs (W10-RULINGS, 25 Sep)

| Job | State | Evidence |
|---|---|---|
| 1. Pickle stamp and its own pair | DONE 26 Sep | W10-PICKLE-STAMP, W10-PICKLE-INSAMPLE-CONFIRMED |
| 2. Outturn clause | DONE 26 Sep | Section below |
| 3. Diagnosis of the two register mechanisms | DONE 26 Sep | Code facts plus W10-BASIS-IN-THE-PAYLOAD, W10-RECORD-MIX-RELAXED, -CANON |
| 4. Fix options with scores | DONE 26 Sep, for John's ruling 30 Sep | W10-CEILING-*, W10-SCHEDULE-PRIOR*, W10-PRIOR-PREVIEW-1, -2 |
| Items 2 and 3 of 22 Sep | Run 25 Sep by John (controller's report) | Log lines owed on John's paste of the two logs |

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
   87 / 80 on n=6,524 (John). The cost of a lighter rule is a noisier estimator route by
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

## Build list for W1 (and W2 where marked), 1-6 October, for John's approval

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
W10-PRIOR-PREVIEW-1, W10-PRIOR-PREVIEW-2. Logs on the workstation under E:\Avia\probe\
(pickle-stamp-W10.log, pickle-stamp-W10-s.log, recordmix-relaxed-W10.log,
recordmix-canon-W10.log, ceiling-relaxed-W10.log, ceiling-canon-W10.log,
schedprior-relaxed-W10.log, schedprior-lookup-BLQ-W10.log, prior-preview-W10.log,
prior-preview-W10-2.log). Every W10 run uses py -3.12 -s: the Carte logon's user
site-packages carry sklearn 1.7.2, and the 25 Sep claimset and mixed runs should be
checked for the same on their build lines.

Scripts, all read-only, all in bt2/: bt2_pickle_stamp.py, bt2_record_mix.py,
probe_payload_keys.py, bt2_ceiling_test.py, bt2_schedule_prior.py, bt2_prior_preview.py.

## Outstanding

1. John's paste of claimset-W10-25Sep.log and mixed-W10-25Sep.log (build line and
   figures): two log lines, then the record's 83.2 / 70.0 and 91 / 85 cite log lines
   rather than the rulings file.
2. John's rulings, 30 Sep: the stand pair; the sample; option 1; option 2b; the airfield
   and range alerts.
3. W10 writes bt2/schedule_prior.csv and its fitting script on the ruling (one session).
4. CALIBRATION-RECORD-2026.md v1 to the controller by 3 Oct, from log lines only.
5. Yearly republication: the record's section 7 (the new cohort, the scripts, the pins,
   who rules), written with v1.

## Commit block

**DevPC**
```
cd C:\AviaDev
git pull
git add routes/W10-STATUS.md routes/CALIBRATION-RECORD-2026.md bt2/bt2_experiments.log bt2/probe_payload_keys.py bt2/bt2_ceiling_test.py bt2/bt2_schedule_prior.py bt2/bt2_prior_preview.py bt2/bt2_calib_grid.py routes/COMMIT-MSG-26Sep2026-w10-pickle-stamp.txt
git commit -F routes/COMMIT-MSG-26Sep2026-w10-pickle-stamp.txt
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
