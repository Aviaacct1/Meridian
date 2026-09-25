# W10 status: FINAL CALIBRATION TEST

Written by W10 only, rewritten every session. Version 4, 26 September 2026, session 3, updated on John's block A paste.
Clone at e7eaf9d. Read this session: W10-RULINGS.md from "22 September 2026, evening" to the
end (six sections); FACE-VALIDITY-REGISTER-25Sep2026.md v2 in full; the umbrella Status
block and critical path of 26 Sep 03:00; bt2/bt2_build_v13.py; app/bt2_forecast.py load path.
Session 2 (24 Sep, v2) was written but never committed; its content is folded in here and
its files are in the commit block below.

## One line for John

The 89/82 record scored the local nonstop passengers a launched route carried, both
directions, on realised launches with the airline's seats known; it never scored the
connecting feed; the model the app runs is not the estimator any calibrated pair describes;
and the live path treats the model's two-way number as each way, doubling the local leg.

## The four jobs and when each lands

| Job | Lands | State |
|---|---|---|
| 1. Pickle stamp and its own pair | DONE 26 Sep | Stamp and in-sample pair measured and confirmed on the declared library |
| 2. Outturn clause | Today, below | Done |
| 3. Diagnosis: the two mechanisms against the record | Delivered from the code; block C confirmed the basis 26 Sep; block B adds the record's own figures | Done in substance |
| 4. Fix options with scores beside 83.2/70.0 and 91/85 | 30 Sep | Shapes below; scores need blocks A-C pasted by 28 Sep |

## Job 1: the model the app runs (block A pasted 26 Sep; log lines W10-PICKLE-STAMP, W10-PICKLE-INSAMPLE-PROVISIONAL)

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

## Job 3: the diagnosis, from the code

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
(ii) Shape. Seats is the anchor and a feature, so more seats returns more passengers at a
declining per-seat rate: BLQ-JFK 3x to 7x is x2.33 seats for x1.58 local (elasticity 0.54);
SJC-TPE 7x to 14x is x2 for x1.78 (0.83). Block B measures the record's own elasticity at
half and double seats. The Bologna sweep (block C) adds a gauge effect: A333 3x to 7x is
x1.26 demand for x2.33 seats, the B77W x1.58, so the model reads the bigger aircraft as
the stronger signal, which is the capacity-aggressiveness feature at work. On small origins (AHB rows at 2.6-5.5x the service area's existing
traffic) the record's launch_pax over base_mkt by market-size band, block B, says whether
launches from small existing markets carry several times that market in year one; until it
runs, the record says nothing on it.
(iii) The Optimise circularity. A model that answers "given this schedule, what will it
carry" gives more demand to a bigger schedule by construction; Optimise sweeps frequency
through it and sizes an aircraft to the answer. bt2_forecast already labels this INDICATIVE
in the payload. The fix is in how Optimise asks, not in the engine.

**Where the record cannot speak.** The feed; any route whose capacity Meridian chose; any
year after the launch year; any catchment (base_mkt is the raw pair). Block B prints the
sample mix (haul, scope, region pair, carrier type, market band) so the long-haul and
Europe-US counts are stated rather than assumed.

## Job 4: fix options for 30 Sep, shape now, scores on the pastes

1. Basis: one line at cortex_app 1311, pass _bt2["pax"] / 2.0 with the basis stated in the
   comment (or return each-way from bt2_forecast with both callers checked). Record score
   unchanged on both pairs (the record is two-way on both sides); register local rows move
   by half; W10 re-scores the register by arithmetic the same day.
2. Optimise anchor: sweep frequency on a market-anchored local (the model at the served
   route's or the analyst's seats, not the swept seats), aircraft sized to demand. Diff in
   cortex_app _cell_kw (W1). Record score unchanged; register Optimise column re-run by the
   controller.
3. Feed: outside the record. The controller's shape (feed as a share of the route's own
   size by haul and hub) needs its own back-test; W10 can score it on the sector target
   (alt_targets, bt2_lib) beside the local pair if John wants a number, one build day.
4. The stand pair: rebuild the pickle on the calibrated configuration (one flag in
   bt2_build_v13, --calib), or carry the blind pair. Scores: both already exist (83.2/70.0
   and 91/85 in-sample; 60.9 blind) plus block A's pair for the pickle as it is.

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

Block B, job 3, the record's mix, share and seat response, both samples.

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

Block C, the basis check on the saved Bologna payload (read-only).

**Workstation Actual**
```
cd C:\src\meridian\bt2
py -3.12 -s probe_payload_keys.py E:\Avia\probe\BLQ-JFK-25Sep\opt_BLQ-JFK.json
```

Also wanted, no run: the four "within" lines of section 2 of E:\Avia\probe\mixed-W10-25Sep.log
as they appeared on screen, for the blind within +-10% figure.

## Log lines

26 Sep: W10-PICKLE-STAMP, W10-PICKLE-INSAMPLE-PROVISIONAL, W10-BASIS-IN-THE-PAYLOAD and
W10-PICKLE-INSAMPLE-CONFIRMED written to bt2/bt2_experiments.log
from John's block A paste. Items 2 and 3 ran on 25 Sep (claimset-W10-25Sep.log, mixed-W10-25Sep.log, John's pastes to
the controller). W10 has not seen the pastes; the two log lines for bt2_experiments.log are
written when they are pasted here, in the existing format, before either figure is quoted
in the record. Until then the record quotes the controller's rulings file as the source.

## Commit block

**DevPC**
```
cd C:\AviaDev
git pull
git add routes/W10-STATUS.md routes/CALIBRATION-RECORD-2026.md bt2/bt2_experiments.log bt2/probe_payload_keys.py routes/COMMIT-MSG-26Sep2026-w10-pickle-stamp.txt
git commit -F routes/COMMIT-MSG-26Sep2026-w10-pickle-stamp.txt
git push
```

## Conflicts seen

None. Item 1 closed (A). The umbrella's Status says "W10 v1 of 22 Sep; no chat has written
since": correct as committed; v2 of 24 Sep was written and not committed, W10's fault.

## Calendar

Job 1 on block A's paste (26 Sep if pasted). Jobs 2 and 3 delivered today from the code;
record figures on blocks B and C. Job 4 on 30 Sep holds if A-C are pasted by 28 Sep.
Items 2 and 3 done 25 Sep; the record v1 by 3 Oct holds.
