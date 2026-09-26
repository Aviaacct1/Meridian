# Controller to W10: rulings and instructions (FINAL CALIBRATION TEST)

Written by the programme controller (the Fable chat), rewritten whenever a ruling lands. W10
reads this at the start of every session and acts on it; W10 never edits it. W10's own
statements go in routes/W10-STATUS.md, which the controller never edits. John pastes nothing.
Read routes/README.md first.

Version 1, 22 September 2026.

## Why W10 exists (John, 22 September 2026)

The product carries two accuracy pairs and neither is settled. 89/82 on 2,915 launches (5 Aug,
v1.2) reproduces from bt2/bt2_claimset.py at 89.2/81.4. 92/86 on 6,524 (9 Aug, V1.3-MIXED,
bt2/bt2_experiments.log line 138, a mixed DOT and Sabre basis) is on the website, the
methodology page and the track record page, and nobody can say today which chat or script
produced it ("find what built it" has been open since 13 Aug). John's ruling: one new chat,
one logged methodology, one final set of tests, ending in the definitive calibration record
the product carries into Routes. John's inclination is the larger sample (circa 6,500) rather
than 2,915, provided it reproduces. W10 does not choose for him; W10 produces the evidence and
he rules.

Interim, on every surface until W10 reports: 89/82 on 2,915, the ruled line in W3-RULINGS.
The 92/86 pair comes off the methodology page and the track record page now (W3 instructed).

## Scope and ownership

- W10 owns bt2/ (scripts, logs, the calibration record) and search_adjustments.py. W10 may
  read anything. W10 changes nothing under app/ and nothing on the demo path; a change the
  calibration needs in app/route_forecast.py is written up in W10-STATUS as a one-line diff
  and the controller carries it to W1, who applies it. Reason: two chats never edit the same
  lines (README code ownership).
- The engine demand logic is FROZEN before Routes (README). John's ruling of 22 Sep opens it
  for ONE item, the catchment radius below, on two conditions: it lands by 3 October with the
  accuracy re-measured on the same claimset, or it does not land at all. Nothing else in the
  demand logic moves.
- Data: E:\Avia on the workstation, read through config, never a hardcoded path. No data-store
  refresh from 10 October to after Routes.
- Every run is logged in bt2/bt2_experiments.log in the existing format (date, script, flags,
  sample, the eight figures) and summarised in routes/CALIBRATION-RECORD-2026.md, the
  deliverable. A figure with no log line does not exist.
- Machines: the tests run on the workstation (Workstation Remote over ssh for scripts that need
  no server; Workstation Actual for anything that must see E: from a logon). E: is a per-logon
  mapped drive, invisible to ssh and WMI-launched processes; a detached job that "sees no E:"
  is the known trap, not a data problem.
- Commit blocks labelled DevPC; the workstation only pulls. Never git against a mounted clone.

## Item 1: catchment radius, settled before the final calibration runs (John, 22 September 2026)

CONTROLLER'S NOTE. John set this out in the controller chat on 22 September in a message the
controller has restated here point by point; the original wording was lost when that chat's
context was compacted. If John still has the text, he pastes it into this chat and the
controller replaces this section with it verbatim. Nothing below is the controller's
invention; every point is John's.

Symptom. A short-haul London route returns Birmingham inside the London catchment. Jol raised
it as feedback item 33 (routes/JOL-FEEDBACK-REGISTER.md). At the stand a visitor who knows
the UK will see it at once, and the catchment page is on the demo path.

Mechanism, as the code stands. app/route_forecast.py haul_radius_km(gcd_km) returns a flat
220 km whatever the haul; DEMAND_RADIUS_KM = 110.0; catchment_mult at line 536 applies the
result. At 220 km, Birmingham (circa 160 km from Heathrow by road) falls inside London.

History. On 30 June a haul-scaled radius was tried, widening for long haul; it moved the
2,500-6,000 km band's ratio from 1.36 to 1.55 and was reverted. The conclusion recorded then:
the short-haul-under, long-haul-over residual is a real effect that needs a different lever
from radius. That conclusion stands; W10 does not re-run the widening.

Principle. Willingness to drive is real for a secondary airport and must be kept; it must not
merge separate primary-metro markets. A radius that lets London absorb Birmingham has crossed
that line.

What is untested and what W10 tests. Narrowing, banded by haul and by carrier type. John's
working values (illustrative, for the search to start from, not a ruling): full-service
short haul circa 100 km; low-cost short haul and all long haul circa 150 km. W10 fits radius
and capture in the same pass through search_adjustments.py with the cross-validation control
that script already has, on the current calibration (the 13 Aug baseline reproduced 22 Sep)
before anything else changes, so the effect of the radius is measured alone.

Rules. (a) Rollback is one line (the constants), so the change is cheap to reverse. (b) No
sixth default-off switch: whatever W10 concludes ships ON by default inside the definitive
calibration, or is rejected outright; the product does not carry another dormant option.
(c) The fitted radius is the default; a catchment the user supplies (the £3,500 catchment
load in PRICING-DECISION-2026.md v1.0) overrides it. (d) The test's pass mark is the whole
claimset, not the London case: a narrowing that fixes Birmingham and worsens the calibrated
pair is reported and rejected. (e) The result, either way, is a log line, a paragraph in the
calibration record, and a one-line diff for W1 if it ships.

## Item 2: reproduce the 22 September baseline first

Before any change: run bt2/bt2_claimset.py as the controller ran it on 22 Sep 06:xx
(E:\Avia\probe\claimset-22Sep.log) and match it exactly: calibrated 83.2 / 70.0, blind 60.9,
tier A 88.2, portfolios 87.7 / 93.2, segments 72.6 / 39.8, sample 6,524 Sabre-only. This is
the 13 Aug baseline (bt2_experiments.log lines 377-390). A mismatch stops the workstream and
is reported to the controller before anything else runs.

## Item 3: the 92/86 pair, reproduce or replace

Find what built V1.3-MIXED (log line 138, 9 Aug): the script, the flags, the sample
definition, the DOT and Sabre mix. If it reproduces, document it so that anyone can re-run
it, and state plainly what "mixed basis" means for a client reading the figure. If it does
not reproduce within the time available, say so, and the product carries the pair that does
reproduce. Either way W10 ends with ONE recommended figure set, stated as: within 20% X% of
the time and within 10% Y% of the time, on N real launches, with the basis named, and John
rules on it. The claim is republished yearly (John, item 25), so the record must say how.

## Reporting

routes/W10-STATUS.md, rewritten every session: what ran, the log lines, what changed, what is
blocked, the commit block. Target: calibration record v1 to John by 3 October so W3 can carry
the figure on the slides, the pack and the site before the 10 October freeze. If 3 October
is not achievable, say so by 29 September; the interim pair then ships and W10 continues for
the yearly republication.

## 22 September 2026, evening: ITEM 1 RE-RULED on W10-STATUS v1 (controller; John to confirm)

W10's conflict is upheld. The catchment radius does not enter the BT2 claimset, so the test
in item 1 cannot measure what it was written to measure, and a "no worsening" result would
be false. Ruling: (A). Item 1 moves to W2 under JOL-FEEDBACK-REGISTER R6 as a competing-set
and display question on the cortex_app competing-airport radius; John's rules (b) and (c)
apply there unchanged (on by default or rejected outright; a supplied catchment overrides).
W10 records in CALIBRATION-RECORD-2026.md, with the greps, that the radius does not enter
the published figures. The freeze exception in the umbrella (22 Sep) is withdrawn: the
engine demand logic stays frozen with no exception. W10 proceeds with items 2 and 3 now.
Option (B), the QSI back-test arms, is not run unless John asks for it. W2's finding on the
friction raster (COMMIT-MSG-22Sep2026-w2-catchment-distance.txt, in commit 30e3e78) is
evidence for the record: catchment measurement changed silently when C:\Avia stopped
existing, so pre- and post- runs are not one series; state the date if it can be found.
Announced here the same day. Commit 30e3e78 carried W10's session 1 files under the
controller's subject; W10's own message is routes/COMMIT-MSG-22Sep2026-w10-session1.txt.

## 25 September 2026: a third question for the record, the local capture on a new long-haul nonstop (controller; corrected same day)

Bologna-New York, blank-form Optimise on 0eb7139, 25 Sep (E:\Avia\probe\BLQ-JFK-25Sep\
opt_BLQ-JFK.json), each way: local demand by the calibrated model 108,062 from a service area
flying to New York today of 203,142 (53% before growth), 112,543 in the forecast year; feed
35,728; total_demand 148,271; carried 111,475 on a 350-seat B77W at 7x (222,950 two-way),
76% local. John's reading: 222k "for a launch route to Bologna seems high"; Avia's December
2025 AdB forecast assumed a daily A321XLR (circa half the local demand the tool gives).
Questions for W10, alongside the frequency response and the split-floor share-of-total
behaviour (24 Sep): (a) what share of a service area's existing traffic to the destination
the calibrated model gives a new long-haul nonstop, and what the 2,915 launches say about
that share on Europe-to-US secondary-city routes; (b) the frequency response inside the
local demand (UA 3x 71,961 to 7x 113,382 each way on the sweep). No engine change before
Routes; the answer goes in CALIBRATION-RECORD-2026.md as a stated limitation if it cannot
be tested by 3 Oct. An earlier version of this section put the question on the connecting
share; the payload's demand block shows connecting at 24%, so that reading is withdrawn.
Also from 24 Sep, for the record: the workstation runs the MCT master (3,668 rows) and
scikit-learn 1.9.0 with user site-packages ignored; W10 and Nick build on that environment.

## 25 September 2026, evening: THE FREEZE IS CONDITIONAL; W10's job widens (controller, John's ruling)

John's ruling, verbatim in the umbrella decisions log 25 Sep: the engine freeze "was a ruling
based on a degree of confidence that the numbers emerging were sensibe, if we find numbers
like this that would make the tool look wrong we have to change it." The case: Bologna-New
York blank-form Optimise on 0eb7139 returns United 7x B77W, 222,950 two-way; the model reads
226k two-way of demand at the sweep's A21N anchor (local 108,062 each way from a service
area flying to New York today of 203,142; feed 35,728); Avia's own December 2025 forecast
for AdB assumed a daily A321XLR. The sweep is already anchored on a narrowbody (cortex_app
_cell_kw, aircraft="A21N"); the 77W is the aircraft sized to carry the anchored demand, so
the number is the engine's read, not the optimiser's choice.

W10's programme to 3 Oct, in this order; items 2 and 3 of 22 Sep continue underneath:
1. By 26 Sep: analogue actuals for the register in routes/FACE-VALIDITY-REGISTER-25Sep2026.md
   from OAG and T-100 (a comparable launch or the served route's actual, source and year
   stated per row). The controller runs the probe and fills the tool columns.
2. By 29 Sep, the diagnosis, measured on the record, one page in W10-STATUS:
   (a) what share of a service area's existing traffic to the destination the calibrated
       model gives a new long-haul nonstop, and what the 2,915 launches say about that share
       on Europe-to-US secondary-city routes (Test A, umbrella 25 Sep: BRS-EWR 0.026,
       SJC-TPE 0.271, BLQ-JFK 0.532, DUB-DFW 1.878);
   (b) the frequency response inside the local demand (BLQ-JFK UA 3x 71,961 to 7x 113,382
       each way; SJC-TPE 7x to 14x +78% on 24 Sep) against what the launches show;
   (c) the seat anchor in indicative mode: the model was scored on realised launches with
       the airline's capacity known; test whether it is calibrated for "given this schedule,
       what will it carry" and not for "what would this route support", which is the
       Optimise question. If so the fix is in how Optimise asks the engine, not the engine.
   (d) the mix of the 2,915: how many long-haul, how many from secondary cities, how many
       Europe-US; and where the record cannot speak, say so.
3. By 30 Sep: the fix options, each as a diff W1 can apply, each with its back-test score
   beside the current 89/82 on 2,915 (a fix that lowers the pair is still a fix; item 55
   moves with it). John decides 30 Sep. W1 builds 1-6 Oct; W10 re-scores; acceptance 7-8
   Oct; the 10 Oct freeze is of the corrected engine.
The bt2 environment: workstation runs the MCT master (3,668 rows), sklearn 1.9.0, user
site-packages ignored. If 29 Sep is not achievable, say so on 26 Sep with what is.

## 25 September 2026, later: W10 job 1 withdrawn; the register is Avia's own forecasts (controller)

John's instruction (umbrella decisions log, 25 Sep, verbatim there): the face-validity
comparison is against the figures Avia's analysts put on new routes for clients, not
against analogues from the stores. The controller has read the Egnyte record and written
routes/FACE-VALIDITY-REGISTER-25Sep2026.md v2: twenty routes with a stated analyst figure
(Knock 2026, Abha 2025, Scotland 2018-19 pre-COVID, Bologna 2025) and eleven with a
schedule only. The controller runs the probe on the workstation and fills the results;
job 1 of the previous section (analogues by 26 Sep) is withdrawn. Jobs 2 and 3 stand with
their dates (diagnosis 29 Sep, fix options with back-test scores 30 Sep) and the register's
results are W10's evidence for both. If the W10 chat has been idle since 22 Sep, its next
STATUS says what ran, and if nothing ran, says that.

## 25 September 2026, late: reply to W10's 24 Sep message (controller)

Your 24 Sep message reached the controller on 25 Sep via John. In order:
- Item 1: re-ruled (A) on 22 Sep evening, in this file above; you were not blocked, the
  ruling was here. John's confirmation is umbrella step C item 7 and does not hold you.
- Item 2: run first, on John's paste, exactly as your block has it. Nothing is re-scored
  until the baseline reproduces to the decimal.
- Item 3: as traced; run after item 2 matches.
- Your three code facts are accepted and matter more than you knew: the register (this
  file, previous section; routes/FACE-VALIDITY-REGISTER-25Sep2026.md, Results) shows the
  product's demand at 2 to 2.6 times Avia's own analysts on every hub-ended long-haul from
  Edinburgh, split between a local over-read (bt2_forecast, which the record scored) and a
  connecting feed 10-25 times the analysts' (route_forecast's V1 flat capture, which by
  your greps the record never scored). Your 29 Sep diagnosis states, with the greps, which
  of the two the 89/82 record measured and which it did not, what the record scored
  (carried or demand, and against what actual), and what the record says about the local
  read on Europe-to-US and Europe-to-Asia long-haul from an established airport. If the
  answer is that the record scored carried on realised launches, say so in one sentence at
  the top; John reads it on a phone.
- Pull first: your clone was at 7c15c3d; origin is at 0eb7139 or later.

## 25 September 2026, late: items 2 and 3 done; what W10 owes for the stand sentence (controller)

Item 2 PASSED tonight (claimset-W10-25Sep.log: all eight figures to the decimal, declared
build). Item 3 RUN (mixed-W10-25Sep.log): V1.3 configuration on the declared library, Sabre
throughout 90.9 / 83.5, mixed 91.1 / 84.8, blind 60.9 / 60.1. John's ruling (umbrella, 25 Sep
late): the stand carries ONE pair for THE model the app runs. So W10's next job, before the
diagnosis: read the build stamp of the bt2_model_v1_3.pkl the workstation loads (path from
bt2_forecast.load, AVIA_LOCAL_CACHE), state which library and configuration built it, and
whether tonight's 91 / 85 is its in-sample pair; if the pickle is not the 1.9.0 V1.3 rebuild,
score the pickle itself and report that pair. Also state, in one clause a host can say, the
outturn period the record scores against. Then the diagnosis of 29 Sep as ruled.

## 26 September 2026, evening: W10-STATUS v9 ACCEPTED IN FULL (controller)

Read in full with the log lines 518-527. Every finding stands as evidence: the pickle stamp
and its pair, the outturn clause, the basis defect at cortex_app 1311 (confirmed by the
controller against route_context.py 346, seats_ly x 2.0), the seat elasticity, the small-
origin ratios, the ceiling rejection, the schedule prior's blind test and the previews. Two
days early, and the critical path moves with you: John rules on options 1, 2b, 4 and 5 by
Mon 29 Sep; W1 ships option 1 on 29 Sep as job 0 with a new baseline; W1 builds 2b and 5 on
30 Sep to 3 Oct from your bt2/schedule_prior.csv, which you write the moment John rules.
Answers: (a) the 25 Sep claimset and mixed runs were made with $env:PYTHONNOUSERSITE = "1" set
in the window and both build lines read sklearn 1.9.0; the two log lines you owe can cite
E:\Avia\probe\claimset-W10-25Sep.log and mixed-W10-25Sep.log with the figures as pasted in
the umbrella decisions log (25 Sep late). (b) John's rulings given in your chat (the schedule
prior design, contribution not profit, the carrier line, new types by seat count, the
airfield and range alerts) are in the umbrella as reported by you; if you hold his words
verbatim, put them in your next STATUS so the umbrella can quote him rather than you.
(c) Your build list is adopted as W1's, in your order; the airfield demotion and first-screen
alerts are shared with W2 for the dashboard. (d) CALIBRATION-RECORD-2026.md v1 by 3 Oct
stands, from log lines only, and now carries the three pairs for one sample with the plain
statement of which one the product runs. (e) The stand sentence's figures are item 55 in the
umbrella; John decides; nothing on any surface changes until he does.

## 26 September 2026, late: W10 COMPLETE; one job left for the next session (controller)

Your v12 and commit acf4a1e are accepted; John's six rulings are in the umbrella decisions log
as you recorded them, item 55 closed at rule B 88 / 78. The basis fix is committed at 7f107b2.
One job remains yours before the restart, because ruling 2 requires the pickle and the pair
text to go live in one step: run bt2_build_v13.py with --out-app to rebuild the evidence file
(master_backtest_scored.csv) and histogram (accuracy_dist.json) on rule B, state where it can
run (the DevPC has no E:\Avia stores unless you know otherwise; if it cannot, give the
workstation block that writes to a folder John can copy from, and the DevPC commit block),
and list every file under app/ and deck/ that states a pair so the one commit carries them all.
Then the controller restarts the server once. Also, for the record: your v12 header says
"Clone at e7eaf9d"; origin is at 7f107b2.
