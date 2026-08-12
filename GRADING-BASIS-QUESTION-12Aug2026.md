# Grading basis: the question that decides where the calibrated layer attaches

Version 3.0, 12 August 2026 evening. Avia Solutions. For the session that produced
`commit-message-12Aug2026.txt`, `bt2/bt2_pin_score.py` and the GRADE-BASIS entry in
`bt2/bt2_experiments.log`.

Question 3 has been RUN and is answered below. Question 4 has also moved, because the connectivity
floor was measured on the shipped path for the first time tonight. Read both before answering 1 and
2, which are still open and are now the whole of the question.

Paste everything below the line.

---

You wrote the GRADE-BASIS finding: the published 92% within +-20% and 86% within +-10% are measured
against Sabre `itinerary='NON-STOP'` passengers on the pair, which is the local market, while
`fc_over_out` is graded against sector traffic, which counts the connecting feed. You named it as
the first thing to put in front of John before the calibrated layer produces a client number.

He is now choosing between two ways of attaching it. The decision needs measurements rather than
positions, and the four questions below are ordered so that the one which may collapse the choice
comes first.

**Option A.** The calibrated model produces the LOCAL NONSTOP number. The catchment, capture and
connecting machinery adds the feed on top, as it does today. The published claims then describe
exactly the quantity they were measured on and nothing is restated.

**Option B.** The calibrated model produces the client's TOTAL. It is re-graded against sector
traffic on the pin so the claim is earned on the new quantity, which may not come back at 92 and 86.

And state the consequence plainly in your answer, because it is the trade John is actually choosing
between. Under option A the published figures attach to the LOCAL LEG ONLY, so the total number a
client is shown carries no accuracy claim at all. Under option B the claim covers the whole number
but has to be re-earned and may be lower. That is a commercial decision, not a technical one, and it
should be stated in one sentence at the top of what you send back.

## 1. Is the engine's `p2p_carried` the same quantity as `launch_pax`? Answer this first

It is not obviously so, and if it is not then option A has the same fault as option B and both need
re-grading, which collapses the choice into a single question about which quantity to re-grade on.

`p2p_carried` is a CARRIED figure: it comes after the 87.5% plan cap at `route_forecast` line 760
and after `split_share` re-splits the carried total. `launch_pax` is what actually flew.

Name every step between the two and say which of them a client's P2P number passes through.

## 2. State `launch_pax` exactly

`bt2_discover` line 64. Confirm the filter, confirm whether the two directions are summed or
averaged, and name any cabin, point-of-sale or itinerary condition beyond `NON-STOP`. This is the
model's training target and everything else rests on it.

## 3. RUN AND ANSWERED, 12 August 2026 evening, on the Workstation

Do not run it again. The result is below and it changes what questions 1 and 4 are for.

n=1,555 routes scored by both engines, being the 50.6% of the arm's 3,072 the calibrated model can
answer at all.

| graded against | Cortex path | calibrated model | McNemar |
|---|---|---|---|
| pure P2P outturn, the local market | 12.6% | 22.4% | +308 -157, p<0.0001 |
| total outturn, the whole sector | 14.5% | 28.9% | +371 -148, p<0.0001 |

Native blind on the four pin cohorts, 60.2%, n=4,287. Sabre throughout, so it is not the published
60.4%, which regrades US domestic launches onto the DOT.

**THE FIGURE THAT MATTERS IS NOT THE COMPARISON.** Blind against blind, on the same 1,555 routes,
the calibrated model scores **55.4% on its own population, target and grading year and 22.4% on the
pin's**. The three differences you named in GRADE-BASIS are worth 33 points between them.

So the choice has moved. It is not which quantity the published claim attaches to. On the client's
own basis the claim does not survive on either quantity, and what is left is a commercial decision
about what Avia says rather than a technical one about where a layer attaches.

**TWO THINGS TO CLOSE BEFORE THESE FIGURES ARE QUOTED ANYWHERE.**

First, and this is for you because you wrote the script: what does "re-anchored" do? A model that
forecasts the LOCAL market scores BETTER against the larger sector denominator, 28.9% against 22.4%,
which is the wrong way round. Either the re-anchoring changes the quantity being predicted, or the
model over-reads local traffic on this population and the sector denominator is simply nearer. Until
that is stated, none of these numbers can sit beside the 60.4%.

Second, the same script on the same artefacts returned 59.8% on the Dev PC on 12 August and 60.2% on
the Workstation tonight, identical n=4,287 and identical configuration. aviaremote1 is a different
Windows user with its own site-packages and had scikit-learn installed fresh tonight. A published
blind figure that moves with a library version needs the version recorded beside it.

And the overlap is Task 3 sized: 1,517 of the arm's routes the calibrated model cannot answer at
all, because the pair was not virgin by the calibrated rule, or its market sat below the training
floor, which is the leaked secondary airport, or no capture row exists. Separating those three needs
a discovery pass.

## 4. What becomes of the connectivity floor under option A

FLOOR-INVISIBLE, 12 August: `route_forecast` line 760 computes
`carried = min(total_demand, capacity x max_plan_lf)` BEFORE the floor block, and the floor only
re-splits that carried total into P2P and connecting, stated at line 767 as "WITHOUT changing the
total". Under option A the calibrated model produces the P2P leg directly, so there is no carried
total for the floor to re-split and the floor as built has nothing to act on.

FLOOR-EVIDENCED sized that floor on outturn. The multiplier the flat feed needs to reach actual
connecting traffic: x2.07 on 335 routes touching a major Asian hub, x2.50 on 476 long-haul routes
over 6,000 km, and x2.82 on the 147 routes that are BOTH. That last figure is the closest comparator
to SJC-TPE, which is 10,440 km into Taipei, and the floor as applied there is x2.19. Judge the floor
against 2.82, not against 2.07 or 2.50. On the right comparator it is conservative, not aggressive.

**MEASURED ON THE SHIPPED PATH, 12 August 2026 evening, which had not been possible before.**
`app/scenario_runner.py` reports the POST-SPLIT figures, so it sees what the back-test cannot.
SJC-TPE, China Airlines A350-900 at 306 seats, 4x weekly, 2028, identical in every other setting,
two-way:

| | P2P carried | connecting carried | total | spill |
|---|---|---|---|---|
| floor OFF | 83,408 | 27,976 | 111,384 | 6,064 |
| floor ON | 50,068 | 61,316 | 111,384 | 6,064 |

Total-preserving exactly as line 767 states. **The floor moves 33,340 two-way passengers off the
local leg and onto the connecting one**, taking the connecting share from 25.1% to 55.0%.

That is the size of what option A has to replace, and it is a third of the number a client is shown.

Test this candidate answer rather than concluding the floor dies. The correction is still needed
under option A, because the raw feed under-reads by a factor of two to three on exactly those
routes. So the floor stops being a re-split inferred from an airport connectivity table and becomes
an EXPLICIT MULTIPLIER on the connecting leg, taken from the FLOOR-EVIDENCED cuts by haul and hub
type. That is arguably the better design: measured against outturn, stated as a number, visible to
whoever reads the forecast, and applied always rather than only when it happens to lift.

Say whether that works, what it costs, and what it breaks. If it does not work, option A costs the
Asian-hub correction and John needs that on the table before he chooses.

## What not to answer

Do not propose trimming the published claims. Do not propose a fallback between engines: a case the
calibrated layer handles badly is handled inside the one model by giving it the right input.

## Working rules

Verify, do not assert. On 12 August four conclusions in the other session were withdrawn within
hours and the pattern was identical every time: reaching for a measurement without first
establishing that the two quantities were comparable. BEFORE comparing two numbers, state what basis
each is on. Tell John when he is wrong and show him the measurement. Ask before running anything
over about twenty minutes. House style throughout, including code comments.

Avia Solutions Limited. All rights reserved.
