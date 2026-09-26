# Meridian calibration record 2026

Written by W10 (final calibration test). Version 1.0, 26 September 2026, RULED. Carries
ONE figure set, ruled by John on 26 September 2026, which the product carries into Routes
and republishes yearly. Sections 1 to 10 are the evidence; section 0 is the ruling. Every figure cites a log line. Every figure in this record quotes the line in
bt2/bt2_experiments.log that produced it; a figure with no log line does not exist.

Avia Solutions Limited. All rights reserved.

## 0. The ruled figure set (John, 26 September 2026)

Meridian's calibrated forecast, scored on 6,524 real route launches (2016-2019, 2024 and
2025) against the local nonstop passengers each route actually carried in its launch year
(Sabre MIDT), is within +-20% of the outturn on 88% of launches and within +-10% on 78%
(calibrated: fitted on the full history and graded on the same launches). On launches the
model never saw, portfolios of twenty routes are within +-20% on 94%. Calibration rule B
(learning rate 0.07, 1,200 iterations, minimum leaf 4, 79 leaves), declared; blind route
level 60.5% within +-20% and 35.2% within +-10%, never published as a single-route figure.
Environment: python 3.12.10, scikit-learn 1.9.0, numpy 2.3.5, scipy 1.18.0, airportsdata
20260803. Artefact: E:\Avia\bt2_relaxed\bt2_model_v1_3.pkl, version "1.4 26Sep2026 rule B
sabre", built 26 September 2026 (log line W10-RULE-B-BUILT); the estimator in the artefact
is the estimator that produced the pair (W10-PICKLE-STAMP, W10-CALIB-GRID).

The host's line: "calibrated means fitted on the full history of 6,524 launches and graded
on the same launches; the portfolio figure is graded on launches the model never saw."

The ruled sentence for every surface, exactly: calibrated 88% within +-20% and 78% within
+-10% on 6,524 launches; blind evidence as portfolios of twenty (94%) only, never a
single-route blind figure. It replaces 89 / 82 on 2,915 and 92 / 86 on 6,524 everywhere,
and goes live in the same step as the rebuilt artefact (John's ruling 2 of 26 September).

## 1. What the claim is

Meridian's calibrated accuracy claim is measured by bt2/bt2_claimset.py: a gradient-boosted
median regression (BT2) predicting nonstop O&D per seat on a sample of real route launches,
graded as forecast over outturn within +-20% and within +-10%. "Calibrated" means fitted on
the full history and graded on it; "blind" means leave-one-cohort-out. The blind figures
are published as portfolios only, never as a single-route figure (standing rule).

## 2. The two pairs in circulation, and what separates them

| Pair | Sample | Fit config | Outturn basis | Environment | Log line |
|---|---|---|---|---|---|
| 89 / 82 | 2,915 launches, 2016-2019 and 2025 | FITTED_KW (it=800, minleaf=5, leaves=63) | Sabre MIDT throughout | 9 Aug, sklearn 1.7.2, airportsdata 20260315 (undeclared) | bt2_claimset docstring: reproduces 89.2 / 81.4 |
| 92 / 86 | 6,524 launches, 2016-2019, 2024, 2025 | CALIB_KW (it=1600, minleaf=3, leaves=95), the memorisation rule | Mixed: 595 US domestic on DOT DB1B, 5,929 on Sabre MIDT | 9 Aug, sklearn 1.7.2, airportsdata 20260315 (undeclared) | 131 (V1.3-RULE), 137 (MIXED-EFFECT), 138 (V1.3-MIXED), 391 (MIXED-BASIS-FOUND) |
| 83.2 / 70.0 | 6,524 launches, as above | FITTED_KW | Sabre MIDT throughout | 13 Aug declared: python 3.12.10, sklearn 1.9.0, numpy 2.3.5, scipy 1.18.0, airportsdata 20260803 | 389 (DECLARED-BASELINE); reproduced 22 Sep, E:\Avia\probe\claimset-22Sep.log |

Source: bt2/bt2_experiments.log, lines as stated; bt2/bt2_claimset.py; bt2/bt2_mixed_basis.py.

The point a reader needs: the 92/86 and the 83.2/70.0 are the same 6,524 launches. Nine
points of the difference between them come from the fit configuration and the library
version, not from the sample or the outturn basis. Line 137 records the memorisation config
Sabre-throughout at 92.6/86.1 against mixed at 91.9/85.6, so the mixed basis costs about half
a point; line 378 records sklearn 1.7.2 to 1.9.0 moving the FITTED_KW pair by 1.4 and 2.4
points while the blind figure held at 60.9 on both.

## 3. The declared baseline (item 2): reproduced 25 September 2026

Run by John on the workstation, E:\Avia\probe\claimset-W10-25Sep.log, reported by the
controller (W10-RULINGS, 25 Sep late): all eight figures to the decimal on the declared
build. Calibrated 83.2 / 70.0 (published-rule estimator, in-sample), blind route 60.9,
tier A 88.2, portfolios of 10 and 20 87.7 / 93.2, segments 72.6 / 39.8, n=6,524, Sabre
throughout, target nonstop. Log line W10-ITEM2-BASELINE-REPRODUCED (build line sklearn 1.9.0; tier A n=653, portfolios
650 and 323 baskets, segments n=2,988 and 1,486).

## 4. The catchment radius (item 1): closed, ruled (A) 22 September 2026

Finding from the code, 22 September, no run: the catchment radius in app/route_forecast.py
(haul_radius_km, 220 km) does not enter the claimset. BT2's capture feature is built by
bt2/bt2_capture.py from the connection builder; grep of bt2_lib.py, bt2_g12_exp.py,
bt2_gbm.py, bt2_capture.py and app/bt2_capture_core.py for "radius", "catchment",
"route_forecast" and "qsi_capture_share" returns nothing. Under the live engine
(--engine bt2 since 22 Sep) the QSI capture share that the radius feeds is replaced by the
model's own local figure. The BHX-inside-London symptom (Jol item 33) comes from the
competing-airport radius in app/cortex_app.py (calibrated_forecast radius_km=220,
RE.competing_airports at line 1010), a separate constant. Controller's ruling, 22 Sep
evening (W10-RULINGS): (A), the item moves to W2 under JOL-FEEDBACK-REGISTER R6; the
engine demand logic stays frozen with no exception. Consequence for this record: the
published figures are unaffected by any catchment radius setting, by construction.
Evidence noted for the series: W2's finding (commit 30e3e78) that catchment measurement
changed silently when C:\Avia stopped existing, so catchment runs before and after that
date are not one series; the date is not established in this record.

## 5. The 92/86 pair (item 3): does not reproduce; the configuration gives 91 / 85

Run by John on the workstation, E:\Avia\probe\mixed-W10-25Sep.log, reported by the
controller (W10-RULINGS, 25 Sep late): bt2_mixed_basis.py, the V1.3 memorisation
configuration on the declared library, Sabre throughout 90.9 / 83.5, mixed basis 91.1 /
84.8, blind 60.9 (Sabre) / 60.1 (mixed). The published 92 / 86 was the same configuration
on sklearn 1.7.2 and airportsdata 20260315; on the declared environment it reads 91 / 85.
The pair is reproducible in method and moves with the library, as line 378 predicted for an
unregularised fit. "Mixed basis" for a client: US domestic launches are graded against US
DOT DB1B ticket data and all other launches against Sabre MIDT; it costs about half a
point against Sabre throughout at this configuration. Log line W10-ITEM3-MIXED-REPRODUCED (build line sklearn 1.9.0; ruler median DOT over Sabre
1.015, 67.6% agreement within +-20%; US slice graded on DOT blind 51.6%, calibrated 90.4%).

## 6. Recommended figure set (W10, 26 September 2026, revised on the calibration grid; John rules)

The calibration rule is a declared choice (V1.3-RULE, 9 August), and the grid of 26
September (W10-CALIB-GRID) shows it is a free one: from the blind reference to the
memorisation rule the blind route figure holds at 60.5-60.9% within +-20% and the blind
portfolios of twenty at 93-95%, while the in-sample pair moves from 74 / 57 to 91 / 84.
On John's positioning (believable, not too good; one sample and one method across the
methodology and the accuracy sections) W10 recommends rule B (learning rate 0.07, 1,200
iterations, minimum leaf 4, 79 leaves), Sabre throughout: calibrated 88% within +-20% and
78% within +-10% on 6,524 real launches (2016-2019, 2024, 2025), scored against the local
nonstop passengers each route carried in its launch year; blind portfolios of twenty 94%
within +-20%; the actual inside the model's own p25-p75 band on 57% of launches.
Environment: python 3.12.10, sklearn 1.9.0, numpy 2.3.5, scipy 1.18.0, airportsdata
20260803. Condition: the estimator fitted under rule B is the one written into
bt2_model_v1_3.pkl, so the pair describes the model that answers a route. The mixed
basis (595 US domestic launches on DOT DB1B) reads 86 / 75 under B and 88 / 80 under C
and is John's choice for the US audience.

Superseded by this section: the 26 Sep morning recommendation of 73 / 56 for the blind
estimator (the pickle as it stands), and the market ceiling (rejected, section 8).

## 7. Yearly republication

Each year, after the Sabre and OAG stores carry the new full year: (1) build the new cohort
with bt2/bt2_discover.py, bt2_profile.py, bt2_capture.py, bt2_base.py, bt2_metro.py and
bt2_growth.py into E:\Avia\bt2_relaxed and add it to AVIA_BT2_COHORTS; (2) run
bt2/bt2_claimset.py and bt2/bt2_calib_grid.py with py -3.12 -s on the declared
environment (or the newly declared one, re-pinned in app/requirements.txt first) and log
both; (3) John re-declares the calibration rule on the grid, on the same positioning
(believable, not too good; one sample, one rule, one estimator); (4) rebuild the artefact
with bt2/bt2_build_v13.py --calib <rule> --basis sabre, read it back with
bt2/bt2_pickle_stamp.py, and log W10-RULE-<rule>-BUILT; (5) rebuild the evidence file and
histogram with --out-app on the DevPC and commit them with the new sentence in one commit;
(6) restart the server; (7) re-run the face-validity register (routes/FACE-VALIDITY-
REGISTER-25Sep2026.md) on the new artefact and record it. A figure with no log line does
not exist, and the sentence never changes before the artefact does.

## 8. The scope of the record, and a basis fault on the live path (24 September 2026)

What the record grades, from the code (bt2_gbm.py, bt2_discover.py lines 78-84,
bt2_profile.py, bt2_lib.py): actual is launch_pax, Sabre NON-STOP passengers on the
unordered pair in the launch year, both directions; seats_ly is OAG seats in the operated
months, both directions; the target is log(actual / seats_ly); rows with actual above 1.1 x
seats_ly are excluded. The published pairs therefore describe how well the model predicts
the local nonstop passengers a launched route carried, given the seats the airline flew.
They do not describe the connecting feed (never graded), a route whose capacity Meridian
chose (bt2_forecast labels that case INDICATIVE), a year beyond the launch year, or a
catchment (base_mkt is the raw pair). The mix (log lines W10-RECORD-MIX-RELAXED and -CANON, 26 Sep): on 6,524, short-haul
4,455 (68%) and long-haul 2,069 (32%); international 4,160; FSC 4,685 and LCC 1,839; pair
market under 8k O&D 4,369 (67%), 8-25k 1,453, 25-80k 628, over 80k 74; Europe-North
America 203, Asia-Europe 167. On 2,915: long-haul 1,147 (39%), under 8k 1,230 (42%),
Europe-North America 139. The passengers-per-seat ratio the record grades has a median of
0.68 (6,524) and 0.62 (2,915).

What the record says about a new long-haul nonstop's year-one local traffic as a share of
the pair's existing O&D: 0.29 where the pair carries 25-80k today, 0.11-0.15 above 80k;
Europe-North America median 0.74 (0.40-1.91) on 6,524 and 0.61 (0.35-1.15) on 2,915.
And what it says about capacity: re-predicting every launch at half and double its seats
moves the model's passengers by 0.51x and 1.99x (elasticity 0.98-0.99 on 6,524, 0.90-0.95
on 2,915). The model predicts a load factor given a schedule; it does not predict what a
market would support, and the record cannot be read as if it did.

The basis fault, from the code: app/route_context.py line 346 builds the live seats_ly both
directions, matching training, so bt2_forecast.forecast returns a two-way local figure;
app/cortex_app.py line 1311 passes it as p2p_demand_override and app/route_forecast.py line
656 sets the each-way `captured` to it (line 853: demand is each-way; line 911: carried is
each-way). The local leg is therefore doubled on every forecast the calibrated engine
answers. Arithmetic on routes/FACE-VALIDITY-REGISTER-25Sep2026.md: EDI-BOS local 68,492
"each way" on 153 seats at 7x is 1.23 x each-way seats, above the 1.1 ceiling the model was
trained under; as a two-way figure it is 0.61. Confirmation from the saved payload is
pending (W10-STATUS block 4). The fix is one line on W1's path and does not move the
record, which is two-way on both sides.

## 9. The model the app runs is not the estimator any calibrated pair describes (25 September 2026)

bt2/bt2_build_v13.py fits the calibrated configuration (lines 73-81), prints its pair, and
then pickles q25, q50 and q75 fitted with the blind configuration (lr=0.04, it=600,
minleaf=60, l2=5.0) on all rows of the mixed basis (lines 128-131). app/bt2_forecast.py
loads that pickle. So 83.2 / 70.0 and 91 / 85 each describe an estimator that is fitted,
printed and discarded; the estimator that answers a client's route is the blind
configuration fitted on every launch, whose leave-one-cohort-out route-level figure is
60.9% within +-20% (60.1% on the mixed basis) and whose in-sample pair has never been
printed. Measured 26 Sep (log line W10-PICKLE-STAMP): the pickle is E:\Avia\bt2_relaxed\
bt2_model_v1_3.pkl, built 13 Aug 2026 on the declared environment (sklearn 1.9.0,
airportsdata 20260803), n_train 6,524, target nonstop; its q50 is the blind configuration
(lr 0.04, it 600, leaves 31, minleaf 60, l2 5.0). Its own in-sample pair, confirmed on the
declared library (W10-PICKLE-INSAMPLE-CONFIRMED): 73.4% within +-20% and 56.0% within
+-10% Sabre throughout, 73.3 / 56.3 on the mixed basis, with the actual inside the model's
p25-p75 band on 51.2% of launches. Three pairs therefore exist for one sample of 6,524:
91 / 85 (memorisation estimator, never runs), 83.2 / 70.0 (published-rule estimator,
never runs) and 73.4 / 56.0 (the estimator that answers a client; blind route level
60.9 / 60.1 within +-20%). For John's ruling on the stand sentence: either the
pickle is rebuilt on the calibrated configuration so the app runs the estimator the pair
describes, or the sentence carries the blind pair for the model that runs.

The outturn clause, for a host: each forecast is scored against the passengers the route
actually carried in its launch year, from the month it started to December, for routes
launched in 2016-2019, 2024 and 2025, from Sabre MIDT, or from US DOT DB1B ticket data
for US domestic routes launched up to 2024.

## 10. What the model says about a route Avia has forecast by hand (26 September 2026)

Internal reference only; the client forecast is not quoted on any client-facing surface.
Avia's December 2025 forecast for Aeroporto di Bologna (BLQ_ShortTermForecast(ADF).xlsx,
sheet 2025:2031, Egnyte Archive/2025/Bologna - Traffic Forecast Update 2025/Forecast/
ShortTerm) assumed a generic US full-service carrier daily to New York JFK from April 2028
on a 155-seat A321XLR, with a 285-seat 787-9 for April to October from 2029: 85,250 seats
in 2028 (nine months) and 168,790 a full year, at 74.5-77.8% load factor, so by arithmetic
circa 65,600 two-way passengers in 2028 and circa 129,500 in a full year, local and
connecting together. Meridian with the schedule prior (W10-PRIOR-PREVIEW-2): the record's
comparable launches put the schedule at 226-287 seats and 2.9-5.1 a week, with United's
own comparable launches at 213 seats near daily, so Avia's schedule is inside the prior's
range; the model's local at the median schedule is 41,675 two-way in the 2025 base year
(0.40 per two-way seat, the Europe-North America record median), circa 65-70k at Avia's
full-year seats and circa 75k with growth to 2029; the current V1 feed adds circa 70k
two-way, for a total of circa 145k against 129.5k. The two agree within 15% on the
schedule an airline would fly and on the total; the residual is in the connecting feed,
which the record has never scored. Thursday's 216,000 two-way local at a 77W daily was
the same model asked about a schedule the record would not have offered, with the local
leg doubled by the basis fault.
