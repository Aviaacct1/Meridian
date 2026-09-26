# W10 status: FINAL CALIBRATION TEST

Written by W10 only, rewritten every session. Version 8, 26 September 2026, session 3; option 2 rejected; option 2b (the schedule prior) TESTED and holds; W10 recommends it for 30 Sep.
Clone at e7eaf9d. Read this session: W10-RULINGS.md from "22 September 2026, evening" to the
end (six sections); FACE-VALIDITY-REGISTER-25Sep2026.md v2 in full; the umbrella Status
block and critical path of 26 Sep 03:00; bt2/bt2_build_v13.py; app/bt2_forecast.py load path.
Session 2 (24 Sep, v2) was written but never committed; its content is folded in here and
its files are in the commit block below.

## One line for John

The record scored the local nonstop passengers a launched route carried, two-way, given
the seats the airline flew; it never scored the feed; the model that answers a client is
the blind-configuration estimator (73 / 56 in-sample, 61 blind), not the one any calibrated
pair describes; its passengers scale one for one with seats, so Optimise cannot ask it what
a market supports; and the live path doubles its two-way answer by treating it as each
way. One line fixes the doubling; the Optimise question needs a market anchor; the stand
carries the pair for the model that runs.

## The four jobs and when each lands

| Job | Lands | State |
|---|---|---|
| 1. Pickle stamp and its own pair | DONE 26 Sep | Stamp and in-sample pair measured and confirmed on the declared library |
| 2. Outturn clause | Today, below | Done |
| 3. Diagnosis: the two mechanisms against the record | DONE 26 Sep: code, block C (basis) and block B (the record's own figures) | Log lines W10-RECORD-MIX-RELAXED, -CANON |
| 4. Fix options with scores | DONE 26 Sep: option 2 scored by block D and rejected; the rest below | For John's ruling 30 Sep |

## Job 1: the model the app runs (DONE 26 Sep; log lines W10-PICKLE-STAMP, W10-PICKLE-INSAMPLE-PROVISIONAL, W10-PICKLE-INSAMPLE-CONFIRMED)

The pickle the workstation loads is E:\Avia\bt2_relaxed\bt2_model_v1_3.pkl, written 13 Aug
01:41 under the declared build (sklearn 1.9.0, airportsdata 20260803, user aviaremote1),
version 1.3 09Aug2026, population bt2_relaxed, n_train 6,524, target nonstop, calib_rule
published. Its q50 estimator is the BLIND configuration (lr 0.04, it 600, leaves 31,
minleaf 60, l2 5.0, 21 features, 600 iterations), exactly as bt2_build_v13 lines 128-131
write it; carid identical to the sample. The artefact's own provenance string records the
calibrated estimator at 84.7 / 72.6 on the mixed basis and blind 60.1, and that estimator
is not in the file. So: 91 / 85 is NOT the pickle's in-sample pair, and neither is 83.2 /
70.0 or 84.7 / 72.6; each describes an estimator that was fitted, printed and discarded.

The pickle's own in-sample pair, CONFIRMED on sklearn 1.9.0 with user site-packages
ignored (log line W10-PICKLE-INSAMPLE-CONFIRMED, identical to the first run to the
decimal): Sabre throughout 73.4 / 56.0, mixed basis 73.3 / 56.3, actual inside its p25-p75
band on 51.2% of rows (an honest band). The first run had unpickled under the Carte
logon's sklearn 1.7.2; it moved nothing here, but every W10 block runs with -s from now on. The controller's note that the workstation runs 1.9.0 with
user site-packages ignored describes the server logon, not an RDP PowerShell as Carte;
every W10 block from here carries py -3.12 -s for that reason.

For John's ruling on the stand sentence: the model that answers a route has an in-sample
pair of circa 73 / 56 and a blind route-level figure of 60.9 (60.1 mixed) within +-20%. A
higher calibrated pair can be carried only by rebuilding the pickle on that configuration,
which is a product change (the p25-p75 band would then come from a near-memorising fit).
W10's view stands: carry the pair for the model that runs.

## Job 2: the outturn clause

Each forecast is scored against the passengers the route actually carried in its launch
year, from the month it started to December, for routes launched in 2016 to 2019, 2024 and
2025, from Sabre MIDT, or from US DOT DB1B ticket data for US domestic routes launched up
to 2024. Source: bt2/bt2_discover.py lines 78-84 (Sabre NON-STOP, source_year = launch
year, unordered pair, both directions); bt2/bt2_mixed_basis.py docstring (DB1B coverage
2000-2024, 2016 Q1 absent and scaled, nothing for 2025).

## Job 3: the diagnosis (DONE 26 Sep)

**What the record scored.** bt2_gbm.py: target log(actual / seats_ly), forecast seats_ly x
exp(prediction). actual = launch_pax, Sabre NON-STOP passengers on the unordered pair in the
launch year, both directions (bt2_discover.py lines 78-84). seats_ly = OAG seats in the
operated months on the pair, both directions (bt2_profile.py; wk_freq_dir halves the ops).
bt2_lib.py excludes rows where actual exceeds 1.1 x seats_ly. The record is therefore:
given the seats the airline flew, how many local nonstop passengers did the route carry in
its launch year, two-way. Capacity is an input on every row. It scored carried on realised
launches.

**Mechanism 1, the connecting feed: never scored.** BT2 replaces only `captured`
(route_forecast.py line 656). feed_beyond and feed_behind come from the V1 flat capture; no
file in bt2/ reads them (grep feed_beyond, feed_behind: nothing in bt2/). The sector target
in bt2_lib (alt_targets) would grade local plus feed together, and was never the published
basis. The register's 10-25x feed on hub routes is outside the record entirely; the record
can neither confirm nor refute it.

**Mechanism 2, the local read: a basis fault, then the model's shape.**
(i) Basis. route_context.py line 346 builds the live seats_ly as seats x freq x 2 x 52 x
months/12, both directions, matching training, so bt2_forecast returns a TWO-WAY local
figure. cortex_app.py line 1311 passes it as p2p_demand_override; route_forecast.py line
656 sets `captured` to it, and `captured` is each-way (line 853 "demand is each-way";
annual_capacity each-way seats; carried at line 911 each-way). The local leg is doubled on
every forecast the calibrated engine answers. Arithmetic on the register: EDI-BOS local
68,492 "each way" on 153 seats at 7x is 1.23 x each-way seats (55,692), above the 1.1
ceiling the model was trained under and cannot exceed; as two-way it is 0.61. AHB-DXB
106,616 on A21N 7x: 1.33 each way, 0.67 two way. BLQ-JFK 108,062 at the A21N anchor: the
same shape. NOC-CDG 23,423 on A223 4x: 0.41 two way. Three register rows are impossible as
each-way outputs of this model. With growth to 2027 added, the doubling accounts for most
of the 2-2.6x local over-read on the Edinburgh rows. Block C, pasted 26 Sep, shows the two bases meeting in
one line of arithmetic: forecast_engine mode scheduled, range 89,724 to 143,116 and
captured 112,543 (the model's two-way figure carried to 2027) beside annual_capacity
127,400, which is 350 seats x 7 x 52, each way; carried = min(total_demand 148,271,
127,400 x 0.875) = 111,475, the payload's total. The model was anchored on seats_ly
254,800 (both directions) and its answer is set against each-way seats. On Bologna the
per-seat ratio is 0.42 two-way, so this route alone does not exceed the ceiling; the
Edinburgh and Abha rows do, and the code settles it either way.
(ii) Shape, measured on the record (block B, 26 Sep). Re-predicting every launch at half
and at double its seats, the model returns 0.507 and 1.987 times the passengers (blind
configuration; 0.506 and 1.980 fitted): implied elasticity 0.98-0.99 on 6,524 and
0.90-0.95 on 2,915, long-haul the same as short. The model is a load-factor predictor:
passengers scale one for one with seats and the per-seat rate barely moves. The live
sweep reads lower (BLQ-JFK B77W 3x to 7x elasticity 0.54, A333 0.28) because the sweep
moves frequency and the frequency feature with the seats, which the record test holds;
the direction is the same and the conclusion does not depend on which.
(iii) The Optimise circularity, now a number. "Given this schedule, what will it carry" is
what the model was fitted and scored on, and it answers it at circa 0.68 of seats whatever
the schedule. "What would this route support" has no answer inside it: every capacity is
supported at the same load factor, so Optimise sweeping schedules through it and sizing an
aircraft to the result is circular by construction, as bt2_forecast's INDICATIVE caveat
already says. The fix is in how Optimise asks (option 2), not in the engine.
(iv) The share of a service area's existing traffic (block B). The record's nearest
quantity is launch_pax over base_mkt, the pair's own O&D before launch. On established
markets the two samples agree: a new long-haul international nonstop carries a median 0.29
of the pair's existing O&D in year one where that O&D is 25-80k (n=302 relaxed / 244
canon) and 0.15 / 0.11 above 80k (n=42 / 36). Europe-North America: median 0.74 (p25
0.40, p75 1.91) on 203 launches relaxed, 0.61 (0.35-1.15) on 139 canon, at 0.40 / 0.35
passengers per two-way seat. Asia-Europe 0.57 / 0.36. On tiny existing markets (under 8k
pair O&D) the median launch carries 5.2x the existing pair traffic (relaxed) or 1.5x
(canon): a launch into a near-empty pair is mostly new traffic, which is the Abha pattern
(flynas IST 5.5x the service area) and is inside the record for that class. The register's
Test A ratios are on the service area, not the raw pair, so the comparison is directional:
BLQ-JFK 0.53 and SJC-TPE 0.27 are inside the EU-NA and long-haul ranges; DUB-DFW 1.88 is at
the EU-NA p75; BRS-EWR 0.026 is below the p25 of every class.
(v) The mix. 6,524: short-haul 4,455 (68%), long-haul 2,069 (32%); international 4,160;
FSC 4,685, LCC 1,839; pair market under 8k 4,369 (67%), 8-25k 1,453, 25-80k 628, over 80k
74; EU-NA 203 (3.1%), AS-EU 167, AS-NA 64. 2,915: long-haul 1,147 (39%); under 8k 1,230
(42%); EU-NA 139 (4.8%), AS-EU 109. The relaxed sample's extra 3,609 launches are
two-thirds tiny-market pairs, which is what buys its higher blind figure and its lower
calibrated pair. "Secondary city" is not a field in the record; the market-size band is
the nearest proxy and is reported instead.

**Where the record cannot speak.** The feed; any route whose capacity Meridian chose; any
year after the launch year; any catchment (base_mkt is the raw pair). Block B prints the
sample mix (haul, scope, region pair, carrier type, market band) so the long-haul and
Europe-US counts are stated rather than assumed.

## Job 4: fix options for 30 Sep, each as a diff W1 can apply, with its score

Scores beside the three pairs on 6,524 (83.2 / 70.0 published-rule estimator; 91 / 85
memorisation; 73.4 / 56.0 the estimator that runs, blind 60.9). None of the four options
changes the record's two-way arithmetic, so the pairs stand under each; what moves is the
register.

1. BASIS, one line. cortex_app.py line 1311: `p2p_demand_override=(_bt2["pax"] / 2.0 if
   _bt2 else None)` with a comment stating that bt2_forecast returns both directions
   (route_context line 346) and route_forecast's captured is each-way (line 853); and the
   payload's range_low and range_high halved on the same basis so the band matches. Score:
   record unchanged (log lines W10-BASIS-IN-THE-PAYLOAD, W10-PICKLE-INSAMPLE-CONFIRMED).
   Register: every BT2 local row halves; EDI-BOS local 137k two-way becomes 68k against the
   analyst's 43k (1.6x, from 3.2x); BLQ-JFK local at 7x falls from 112,543 to 56,272 each
   way and the 7x B77W no longer fills. W10 recommends this ships regardless of the rest;
   it is a defect, not a calibration choice.
2. OPTIMISE ANCHOR, a market ceiling on the local leg: SCORED AND REJECTED (log lines
   W10-CEILING-RELAXED, W10-CEILING-CANON). forecast = min(model, share_p75(class) x
   base_mkt), table fitted on the training cohorts for the blind arm: blind route level
   60.9 / 36.3 falls to 48.5 / 28.2 on 6,524 (53.8 / 30.0 to 45.8 / 24.1 on 2,915),
   in-sample 74.1 / 56.6 to 58.5 / 42.8, a quarter of rows touched, the loss on every
   segment including EU-NA long-haul. The record says a launch-over-existing-market ratio
   has no usable upper tail (short-haul tiny markets p75 16.5x), so a cap either never
   bites or bites the right answers with the wrong ones. Not shipped, not parked; a
   different anchor is needed and W10 has none inside this record.
   What that leaves for Optimise, for John to rule: (a) Optimise stops claiming to answer
   "what would this route support" and becomes a schedule comparison at the visitor's
   gauge, frequencies ranked by economics with the model's carried at each, labelled as
   such; or (b) the local leg for Optimise comes from a demand anchor outside the model
   (the QSI engine's catchment demand, which the register shows under-reads thin routes by
   half and which is a second engine, against the one-model rule). W10's view: (a) before
   Routes, with the limitation stated in the known-issues list; (b) is a programme, not a
   fix. Either way the Run path and the record are untouched.
2b. THE SCHEDULE PRIOR (John, 26 Sep, after the ceiling result; W10 agrees and this is
   the recommended Optimise fix). The model is accurate given the schedule; what went
   wrong at Bologna is that Optimise chose a schedule no airline would launch, because the
   model rewards every seat added. So Optimise first asks what an airline would actually
   launch on a pair like this, and the record holds 6,524 real answers: on a pair with
   this existing O&D, haul and carrier type, airlines flew this gauge at this frequency.
   The aircraft sweep is bounded to schedules the record says are credible for the pair
   (capacity_frame.py, 9 Aug, already bounds the carrier half: the aircraft each credible
   operator flies on comparable sectors), and contribution picks within that set; the
   model then forecasts at the chosen schedule, where it is accurate. "Optimised for":
   the most contribution among the schedules airlines have actually launched on markets
   like this one. One model, one record, no second engine; Run and the accuracy sentence
   untouched. John's two additions: (i) new types such as the A220 and A321XLR are not in
   the history yet, so the prior is expressed in seats per departure and frequency, not
   aircraft type, and the type table maps a new type onto the gauge band the record
   already holds under older types; a user who selects a new type still runs it; over the
   years the record catches up on its own. (ii) A carrier cross-check on every Optimise
   result: the chosen carrier's own launches on comparable pairs (n, gauge, frequency),
   printed beside the answer, with "fewer than N comparable launches" stated when that is
   the case. How it feeds the decision (W10's proposal, 26 Sep, for John): a flag, never a
   veto. Where the carrier has five or more comparable launches and its own band does not
   overlap the pair's prior band, Optimise re-runs the sweep inside the carrier's own band
   and shows both answers, headline on the carrier's ("as United launches such routes"),
   the market-typical schedule beside it; where the carrier has fewer than five, the
   headline stays on the market prior and the line says so; capacity_frame bounds the
   aircraft to what the carrier actually flies on sectors of that length before either.
   The tool never says an airline would not do it; it shows the airline's own pattern so
   the host can. SCORE (block E, log lines W10-SCHEDULE-PRIOR, W10-SCHEDULE-PRIOR-LOOKUP): the record
   predicts gauge to within +-20% on 71% of launches (91% within +-50%) and weekly
   frequency to within +-20% on 71% (88% within +-50%), blind by cohort, from pre-launch
   facts alone; carrier identity adds three points on gauge. Annual seats as flown are not
   predictable (20% within +-20%) because seats_ly carries the months operated, which is
   launch timing, so the prior is expressed as gauge x frequency x 52 and never as
   seats_ly. THE PRIOR HOLDS. For a Bologna-shaped pair the record's comparable launches
   are a 270-seat widebody at three to four a week (64 Europe-North America launches) or
   a 180-220 seat aircraft near daily (United's six comparable launches at gauge 219, 5.8
   a week); a 77W daily is outside the range and would not have been offered. W10
   RECOMMENDS 2b for John's ruling on 30 Sep. The build for W1: (1) the prior as a CSV in
   bt2/ read through config (gauge and frequency p25-p75 by class, plus the carrier line),
   or the fitted prior pickled beside the model; (2) Optimise's sweep bounded to the
   prior's p25-p75 on gauge and frequency for the pair, new types mapped by seat count;
   (3) contribution ranks within the set; (4) the model forecasts at the winner; (5) the
   payload carries the prior's range and the carrier line with its n. Record and Run
   untouched. W10 writes the class table and the carrier lines; W1 wires them.
3. FEED. Outside the record. The controller's shape (feed as a share of the route's own
   size by haul and hub) cannot be scored on this record and W10 says so rather than
   scoring it on the sector target, which grades a quantity nobody publishes. W1 builds it
   against the register rows (analyst connecting on the Knock and Edinburgh rows) as the
   test, with the controller.
4. THE STAND PAIR. No code. John rules: 73 / 56 in-sample and blind 61 / 36 (within
   +-20 / +-10, route level, W10-CEILING-RELAXED raw arm) for the model that runs, with the outturn clause; or rebuild the pickle on the published-rule
   configuration (bt2_build_v13 writes the blind estimator at line 129; a one-line change
   writes the calibrated one) and carry 83.2 / 70.0 with the p25-p75 band then coming from
   a lightly regularised fit. W10 recommends the first.

## Blocks for John

Block A2, DONE 26 Sep (pickle-stamp-W10-s.log). Kept for the yearly republication.

**Workstation Actual**
```
cd C:\src\meridian\bt2
$env:AVIA_LOCAL_CACHE = "E:\Avia"
$env:AVIA_BT2_DIR     = "E:\Avia\bt2_relaxed"
$env:AVIA_APP_DIR     = "C:\src\meridian\app"
$env:AVIA_BT2_COHORTS = "2016,2017,2018,2019,2024,2025"
$env:AVIA_BT2_TARGET  = "nonstop"
py -3.12 -s bt2_pickle_stamp.py 2>&1 | Tee-Object -FilePath E:\Avia\probe\pickle-stamp-W10-s.log
```

Block B, DONE 26 Sep (recordmix-relaxed-W10.log, recordmix-canon-W10.log). Kept for the yearly republication.

**Workstation Actual**
```
cd C:\src\meridian\bt2
$env:AVIA_LOCAL_CACHE = "E:\Avia"
$env:AVIA_APP_DIR     = "C:\src\meridian\app"
$env:AVIA_BT2_TARGET  = "nonstop"
$env:AVIA_BT2_DIR     = "E:\Avia\bt2_relaxed"
$env:AVIA_BT2_COHORTS = "2016,2017,2018,2019,2024,2025"
py -3.12 -s bt2_record_mix.py 2>&1 | Tee-Object -FilePath E:\Avia\probe\recordmix-relaxed-W10.log
$env:AVIA_BT2_DIR     = "E:\Avia\bt2"
$env:AVIA_BT2_COHORTS = "2016,2017,2018,2019,2025"
py -3.12 -s bt2_record_mix.py 2>&1 | Tee-Object -FilePath E:\Avia\probe\recordmix-canon-W10.log
```

Block C, DONE 26 Sep. Kept for reference.

**Workstation Actual**
```
cd C:\src\meridian\bt2
py -3.12 -s probe_payload_keys.py E:\Avia\probe\BLQ-JFK-25Sep\opt_BLQ-JFK.json
```

Block D, DONE 26 Sep (ceiling-relaxed-W10.log, ceiling-canon-W10.log). Kept for the record.

Block F, John's question of 26 Sep: what the new logic gives for Bologna, Genoa and
Southampton to New York (bt2/bt2_prior_preview.py, new; after the workstation pulls). Reads
the raw pair O&D from Sabre, states the prior's band and the carrier line, and runs the
model at the p25, median and p75 schedules through the app's own route_context and
bt2_forecast. Local nonstop only, two-way and each way; the feed is not in it.

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
$env:AVIA_FORECAST_ENGINE = "bt2"
py -3.12 -s bt2_prior_preview.py BLQ-JFK:UA GOA-JFK:UA SOU-JFK:UA 2>&1 | Tee-Object -FilePath E:\Avia\probe\prior-preview-W10.log
```

Block E, DONE 26 Sep (schedprior-relaxed-W10.log, schedprior-lookup-BLQ-W10.log). The script
now also scores the annualised target (gauge x freq x 52); re-run when convenient, same
command, to put that figure in the log.

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
py -3.12 -s bt2_schedule_prior.py 2>&1 | Tee-Object -FilePath E:\Avia\probe\schedprior-relaxed-W10.log
py -3.12 -s bt2_schedule_prior.py --lookup base_mkt=55000 gcd=6600 intl typ=FSC carrier=UA 2>&1 | Tee-Object -FilePath E:\Avia\probe\schedprior-lookup-BLQ-W10.log
```
The lookup's base_mkt of 55,000 is a placeholder for Bologna-New York's existing pair O&D,
which W10 does not hold; the payload's "current" field reads 25,582 and "natural" 203,142
(catchment), so run it again with the raw pair figure if the controller has it.

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
py -3.12 -s bt2_ceiling_test.py 2>&1 | Tee-Object -FilePath E:\Avia\probe\ceiling-relaxed-W10.log
$env:AVIA_BT2_DIR     = "E:\Avia\bt2"
$env:AVIA_BT2_COHORTS = "2016,2017,2018,2019,2025"
py -3.12 -s bt2_ceiling_test.py 2>&1 | Tee-Object -FilePath E:\Avia\probe\ceiling-canon-W10.log
```

Also wanted, no run: the four "within" lines of section 2 of E:\Avia\probe\mixed-W10-25Sep.log
as they appeared on screen, for the blind within +-10% figure.

## Log lines

26 Sep: W10-PICKLE-STAMP, W10-PICKLE-INSAMPLE-PROVISIONAL, W10-BASIS-IN-THE-PAYLOAD,
W10-PICKLE-INSAMPLE-CONFIRMED, W10-RECORD-MIX-RELAXED, W10-RECORD-MIX-CANON, W10-CEILING-RELAXED,
W10-CEILING-CANON, W10-SCHEDULE-PRIOR and W10-SCHEDULE-PRIOR-LOOKUP written to bt2/bt2_experiments.log
from John's block A paste. Items 2 and 3 ran on 25 Sep (claimset-W10-25Sep.log, mixed-W10-25Sep.log, John's pastes to
the controller). W10 has not seen the pastes; the two log lines for bt2_experiments.log are
written when they are pasted here, in the existing format, before either figure is quoted
in the record. Until then the record quotes the controller's rulings file as the source.

## Commit block

**DevPC**
```
cd C:\AviaDev
git pull
git add routes/W10-STATUS.md routes/CALIBRATION-RECORD-2026.md bt2/bt2_experiments.log bt2/probe_payload_keys.py bt2/bt2_ceiling_test.py bt2/bt2_schedule_prior.py bt2/bt2_prior_preview.py routes/COMMIT-MSG-26Sep2026-w10-pickle-stamp.txt
git commit -F routes/COMMIT-MSG-26Sep2026-w10-pickle-stamp.txt
git push
```

## Conflicts seen

None. Item 1 closed (A). The umbrella's Status says "W10 v1 of 22 Sep; no chat has written
since": correct as committed; v2 of 24 Sep was written and not committed, W10's fault.

## Calendar

All four jobs done 26 Sep. John decides 30 Sep on: the stand pair; the sample; option 1
(ship); option 2b (recommended, tested). Outstanding for the record: John's pastes of the
25 Sep claimset and mixed logs (build line and figures), then record v1 by 3 Oct.
