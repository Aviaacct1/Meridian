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
