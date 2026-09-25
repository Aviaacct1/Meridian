# Meridian calibration record 2026

Written by W10 (final calibration test). Version 0.4, 26 September 2026, DRAFT. The
definitive version carries ONE figure set, ruled by John, and is what the product carries
into Routes and republishes yearly. Every figure in this record quotes the line in
bt2/bt2_experiments.log that produced it; a figure with no log line does not exist.

Avia Solutions Limited. All rights reserved.

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
throughout, target nonstop. Log line in bt2_experiments.log to follow John's paste to W10.

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
point against Sabre throughout at this configuration. Log line to follow John's paste.

## 6. Recommended figure set

Not yet stated. Will be one line: within 20% X% of the time and within 10% Y% of the time,
on N real launches, basis named, fit configuration named, environment named.

## 7. Yearly republication

To be written: the sample refresh (new cohort), the script, the environment pins, the log
line, and who rules.

## 8. The scope of the record, and a basis fault on the live path (24 September 2026)

What the record grades, from the code (bt2_gbm.py, bt2_discover.py lines 78-84,
bt2_profile.py, bt2_lib.py): actual is launch_pax, Sabre NON-STOP passengers on the
unordered pair in the launch year, both directions; seats_ly is OAG seats in the operated
months, both directions; the target is log(actual / seats_ly); rows with actual above 1.1 x
seats_ly are excluded. The published pairs therefore describe how well the model predicts
the local nonstop passengers a launched route carried, given the seats the airline flew.
They do not describe the connecting feed (never graded), a route whose capacity Meridian
chose (bt2_forecast labels that case INDICATIVE), a year beyond the launch year, or a
catchment (base_mkt is the raw pair). The mix of the sample by haul, scope, region pair and
market size is printed by bt2/bt2_record_mix.py and will be entered here from its log line.

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
