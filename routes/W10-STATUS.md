# W10 status: FINAL CALIBRATION TEST

Written by W10 only, rewritten every session. Version 3, 25 September 2026, session 3.
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
| 1. Pickle stamp and its own pair | 26 Sep, on John's paste of block A | Script written (bt2/bt2_pickle_stamp.py); the structural answer is already below |
| 2. Outturn clause | Today, below | Done |
| 3. Diagnosis: the two mechanisms against the record | Today, below, from the code; the record's own figures land with block B | Done in substance; blocks B and C confirm |
| 4. Fix options with scores beside 83.2/70.0 and 91/85 | 30 Sep | Shapes below; scores need blocks A-C pasted by 28 Sep |

## Job 1: the model the app runs (structural answer; block A prints the stamp)

bt2/bt2_build_v13.py lines 73-81 fit the CALIB configuration ("published" it=800 minleaf=5
leaves=63; "memorisation" it=1600 minleaf=3 leaves=95) and print the calibrated pair from
it. Lines 128-131 then pickle q25, q50 and q75 fitted with BLIND_KW (lr=0.04, it=600,
minleaf=60, l2=5.0) on all rows. The calibrated estimator is never written to disk. So:
- the estimator app/bt2_forecast.py loads and runs is the blind-configuration model,
  fitted on every launch in the sample on the mixed outturn basis (bt2_build_v13 attaches
  bt2_mixed_basis before fitting);
- 91/85 (mixed-W10-25Sep.log) is the in-sample pair of the memorisation estimator, and
  83.2/70.0 (claimset) of the published-rule estimator; neither estimator runs in the app;
- the pair that describes the app's model is its own q50 scored on its own rows, which
  nobody has printed, and its out-of-sample figure is the blind route-level 60.9 within
  +-20% (60.1 on the mixed basis) with the within +-10% blind figure on the two "within
  +-10%" lines of mixed-W10-25Sep.log (not quoted here until pasted).
Block A prints the pickle's build_env (library and airportsdata), version, population,
n_train, calib_rule, target, the q50's own hyperparameters, the carid check against the
sample, and the in-sample pair on both bases. If build_env is not sklearn 1.9.0 the pickle
would not have loaded on the workstation since 13 Aug, so the expected answer is the
declared build; the paste decides.

Consequence for the stand sentence, for John to rule with the controller: a calibrated pair
can be carried only if the app runs the estimator that produced it (rebuild the pickle with
the calibrated configuration, which then lives outside the training range of its own
quantile bands), or the sentence carries the blind pair for the model that runs. W10's view:
the second is the honest one and the first is a change to the product.

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
of the 2-2.6x local over-read on the Edinburgh rows. Block C confirms from the saved
Bologna payload.
(ii) Shape. Seats is the anchor and a feature, so more seats returns more passengers at a
declining per-seat rate: BLQ-JFK 3x to 7x is x2.33 seats for x1.58 local (elasticity 0.54);
SJC-TPE 7x to 14x is x2 for x1.78 (0.83). Block B measures the record's own elasticity at
half and double seats. On small origins (AHB rows at 2.6-5.5x the service area's existing
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

Block A, job 1 (after the workstation pulls; bt2_pickle_stamp.py is new).

**Workstation Actual**
```
cd C:\src\meridian
git pull
cd C:\src\meridian\bt2
$env:AVIA_LOCAL_CACHE = "E:\Avia"
$env:AVIA_BT2_DIR     = "E:\Avia\bt2_relaxed"
$env:AVIA_APP_DIR     = "C:\src\meridian\app"
$env:AVIA_BT2_COHORTS = "2016,2017,2018,2019,2024,2025"
$env:AVIA_BT2_TARGET  = "nonstop"
py -3.12 bt2_pickle_stamp.py 2>&1 | Tee-Object -FilePath E:\Avia\probe\pickle-stamp-W10.log
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
py -3.12 bt2_record_mix.py 2>&1 | Tee-Object -FilePath E:\Avia\probe\recordmix-relaxed-W10.log
$env:AVIA_BT2_DIR     = "E:\Avia\bt2"
$env:AVIA_BT2_COHORTS = "2016,2017,2018,2019,2025"
py -3.12 bt2_record_mix.py 2>&1 | Tee-Object -FilePath E:\Avia\probe\recordmix-canon-W10.log
```

Block C, the basis check on the saved Bologna payload (read-only).

**Workstation Actual**
```
cd C:\src\meridian\bt2
py -3.12 probe_payload_keys.py E:\Avia\probe\BLQ-JFK-25Sep\opt_BLQ-JFK.json
```

Also wanted, no run: the four "within" lines of section 2 of E:\Avia\probe\mixed-W10-25Sep.log
as they appeared on screen, for the blind within +-10% figure.

## Log lines

Items 2 and 3 ran on 25 Sep (claimset-W10-25Sep.log, mixed-W10-25Sep.log, John's pastes to
the controller). W10 has not seen the pastes; the two log lines for bt2_experiments.log are
written when they are pasted here, in the existing format, before either figure is quoted
in the record. Until then the record quotes the controller's rulings file as the source.

## Commit block

**DevPC**
```
cd C:\AviaDev
git pull
git add routes/W10-STATUS.md routes/CALIBRATION-RECORD-2026.md bt2/bt2_record_mix.py bt2/probe_payload_keys.py bt2/bt2_pickle_stamp.py routes/COMMIT-MSG-25Sep2026-w10-session3.txt
git commit -F routes/COMMIT-MSG-25Sep2026-w10-session3.txt
git push
```
(routes/COMMIT-MSG-24Sep2026-w10-diagnosis.txt is superseded by this one and not added.)

## Conflicts seen

None. Item 1 closed (A). The umbrella's Status says "W10 v1 of 22 Sep; no chat has written
since": correct as committed; v2 of 24 Sep was written and not committed, W10's fault.

## Calendar

Job 1 on block A's paste (26 Sep if pasted). Jobs 2 and 3 delivered today from the code;
record figures on blocks B and C. Job 4 on 30 Sep holds if A-C are pasted by 28 Sep.
Items 2 and 3 done 25 Sep; the record v1 by 3 Oct holds.
