# Runbook: wiring the calibrated model into the client path

Version 1.0, 13 August 2026 evening, for the session that builds it. Avia Solutions.

Supersedes Task 4 of *HANDOVER Meridian - the basis problem - 12Aug2026 evening.md*, which held the
wiring on the grading basis. Questions 1 and 2 of that basis are now answered in
`GRADING-BASIS-ANSWER-13Aug2026.md` and the answer changes what the wiring can claim. Read that
document and the 13 August entries in `bt2/bt2_experiments.log` before starting.

## The baseline this is measured against, established 13 August evening

Both machines now agree on every line, on byte-identical data and a declared environment.
Reproduce this before changing anything; if it does not come back, stop and find out why.

```
$env:AVIA_BT2_DIR = "E:\Avia\bt2_relaxed"
$env:AVIA_BT2_COHORTS = "2016,2017,2018,2019,2024,2025"
$env:AVIA_BT2_TARGET = "nonstop"
py -3.12 bt2_claimset.py
```

| | figure |
|---|---|
| calibrated ±20% | 83.2% |
| calibrated ±10% | 70.0% |
| blind, route level | 60.9% |
| tier A | 88.2% |
| portfolios of 10 | 87.7% |
| portfolios of 20 | 93.2% |
| short-haul, domestic or LCC | 72.6% |
| long-haul, international, FSC | 39.8% |
| sister flag set | 424 of 6,524 |

Build: python 3.12.10, sklearn 1.9.0, numpy 2.3.5, scipy 1.18.0, airportsdata 20260803. Both
`DESKTOP-3R7OQVJ` and `Donatello`. `bt2_claimset` stamps all of it on every run.

**This is not the published pair.** The site's 92 and 86 sit on the mixed basis, 595 routes graded
on US DOT DB1B and 5,929 on Sabre MIDT, per V1.3-MIXED of 9 August. Everything above is Sabre
throughout, and nothing in `bt2_claimset` produces the mixed basis. Find what built it before any
restatement is attempted.

## The one sentence

Wire the calibrated model to `captured`, the local demand leg, before the plan cap; keep it behind
`AVIA_FORECAST_ENGINE` default off; and re-baseline it against the frozen cases by a named date,
because five previous improvements were gated off and never turned back on.

## Why this is now worth doing, measured rather than argued

The engine being replaced is poor and cannot be cheaply patched.

| | figure | basis |
|---|---|---|
| QSI engine, local leg | 11.3% within ±20% | 2,948 arm routes, `captured_uncapped` against `p2p_outturn` at L+1 |
| the same, on the pin | 12.6% | 1,555 pin routes |
| calibrated model, same 1,555 routes, same basis | 22.4% | p<0.0001 against the above |
| calibrated model, its own basis | 60.9% blind, route level | 6,524 relaxed, `launch_pax` at L |

`local_level_fit` on 13 August established that no multiplier rescues the engine's local leg. A
perfect level fitted on its own routes scores 10.9%, **below** the uncorrected 11.3%, because the
interquartile range of actual over forecast spans a factor of 8.1 and straddles 1.0 on every cut.
The engine over-reads on the lower quartile and under-reads by six times or more on the upper one.

## The blocker that must be closed first, and it is not the one the handover named

`bt2_gbm.X_of` feeds the model `log(months)` as feature six and `month_num` as feature thirteen. In
training those two are **perfectly collinear**: `months_operated = 13 - launch_month` in every one of
6,810 rows, because `bt2_profile` counts months from the launch month to year end.

`route_context.build` defaults to `months=12, launch_mon=6`. That pair occurs **zero** times in
training and cannot occur by construction. All 192 training rows with twelve months launched in
January.

So a default live call puts the model off its own training manifold on every route. This is
CAPA-IS-NOT-QSI-SHARE of 12 August in a different feature, and it is the reason the build was not
started on 13 August.

**The fix.** `route_context.build` must refuse an inconsistent pair by name rather than accept it,
the way `load_legs` refuses a single-week OAG label. A full-year call means `launch_mon=1` with
`months=12`. Anything else must satisfy `months <= 13 - launch_mon` or stop.

## What the model actually predicts, which nobody had stated

The target is `log(actual / seats_ly)` where `actual` is `launch_pax` over the **full calendar launch
year** and `seats_ly` covers **only the months operated**. So the model predicts **first-year local
nonstop traffic for a route starting in a named month**.

Meridian forecasts a maturity year: `forecast_year` defaults to the base data year plus one and
every client case runs 2027 or 2028. Those are different quantities.

**They reconcile, and the number is measured.** `connecting_maturation` on 13 August, on the local
leg: Y2 over Y1 median 1.013 on n=1,287, Y3 over Y1 median 1.104 on n=550. A first-year output is
within circa 10% of a third-year view. If a maturity adjustment is applied it is x1.104 to Y3 and it
must appear in the payload as a named factor, not folded into the forecast silently.

## The build, in order

### 1. Close the months and launch month fault

`app/route_context.py`, `build()` at line 263. Refuse `months > 13 - launch_mon` by name. Change the
defaults to `launch_mon=1, months=12` so the default call is the January case, which is on the
manifold, and say in the docstring why the two are not independent.

### 2. Wire the model to `captured`

`app/cortex_app.py`, `calibrated_forecast` at line 687. The model replaces `captured`, the local
demand leg, **before** the plan cap at `route_forecast` line 760. Everything downstream is unchanged:
the feed is added, the cap applies, the floor re-splits.

That is option A of the grading basis paper and the only option the null control leaves standing.
Option B, the model producing the client's total, is refuted: `null_model_control` showed a constant
of 0.783 applied to seats scores 77.8% against the model's 78.5% on the sector target, and beats it
on long-haul FSC at 74.5% against 73.7%. The sector figure is a load factor, not a forecast.

### 3. Behind the switch, default off

`AVIA_FORECAST_ENGINE`. The switch already exists and is inert: `cortex_app`, `route_forecast` and
`route_feed` contain no reference to `bt2_forecast` or `route_context`. Default stays on the QSI
engine so no client page moves.

The payload must report which engine produced the number, the same way `feed_level` now reports the
connecting level. A page that does not say which engine answered is the silent-default shape this
codebase has been caught by seven times.

### 4. Re-baseline, and this is the step that must not slip

```
py -3.12 econ_baseline.py check
py -3.12 scenario_runner.py cases_sjc_tpe.json
```

Both with the switch off, to prove nothing moved. Then both with it on, to see what it does. The
frozen figures are in the 13 August handover section 8 and in SJC-TPE-BASELINE.

**Set a date for turning it on.** DEFAULT-OFF-SWITCHES records five verified improvements gated off
and never re-baselined, and that is the failure this project has already paid for once.

## What the wiring does not settle

The claim still describes an input rather than the page. Q1-ANSWERED-NO established four
transformations between the model's quantity and the client's: `captured`, the cap's pro-rating of
the local leg, the connectivity floor, and the payload. On the frozen SJC-TPE case those take 87,948
to 83,408 to 50,068, a factor of 1.757.

So wiring the better engine improves the number without closing the commercial question, which stays
as the three-way choice in `GRADING-BASIS-ANSWER-13Aug2026.md` section 4: re-grade on the client's
number, publish on a named intermediate, or change what the page shows.

## Two open items the build should not touch

The connecting feed runs at `qsi_k = 1.0` and RECUT-RESULT measured it over-reading actual connecting
traffic by circa ten times on the median route. `qsi_k` is now a parameter defaulting to 1.0 so
nothing has moved, and the level is a separate decision from the wiring.

The half-year OAG union is built and off behind `AVIA_BT2_HALFYEAR`. It changes `capa`, `qcx` and
`legs_n` for cohorts 2016 and 2017, so turning it on means rebuilding those captures and re-measuring
the model. Do not combine it with the wiring: two changes to the model's inputs at once cannot be
attributed.

Avia Solutions Limited. All rights reserved.
