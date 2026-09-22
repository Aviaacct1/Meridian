# Meridian calibration record 2026

Written by W10 (final calibration test). Version 0.1, 22 September 2026, DRAFT. The
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

## 3. The declared baseline (item 2)

To be completed from W10's run. Target figures, from log line 389 and the controller's 22
Sep run: calibrated 83.2 / 70.0, blind route 60.9, tier A 88.2, portfolios of 10 and 20
87.7 / 93.2, segments 72.6 (short-haul domestic or LCC) / 39.8 (long-haul international
FSC), n=6,524, Sabre throughout, target nonstop.

## 4. The catchment radius (item 1)

Finding, 22 September 2026, from reading the code (no run): the catchment radius in
app/route_forecast.py (haul_radius_km, 220 km) does not enter the claimset. BT2's capture
feature is built by bt2/bt2_capture.py from the connection builder, and no file in the
training chain references a radius or the catchment. Under the live engine (--engine bt2
since 22 Sep) the QSI capture share that the radius feeds is replaced by BT2's own local
figure. The BHX-inside-London symptom (Jol item 33) comes from the competing-airport radius
in app/cortex_app.py (calibrated_forecast radius_km=220, RE.competing_airports), a separate
constant. Awaiting the controller's re-ruling on how item 1 is measured; see W10-STATUS.md.

## 5. The 92/86 pair, reproduce or replace (item 3)

To be completed from W10's run of bt2/bt2_mixed_basis.py on the declared environment.

## 6. Recommended figure set

Not yet stated. Will be one line: within 20% X% of the time and within 10% Y% of the time,
on N real launches, basis named, fit configuration named, environment named.

## 7. Yearly republication

To be written: the sample refresh (new cohort), the script, the environment pins, the log
line, and who rules.
