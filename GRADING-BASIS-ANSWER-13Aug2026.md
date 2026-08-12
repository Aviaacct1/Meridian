# Grading basis: questions 1 and 2 answered, and what changed on 13 August

Version 1.0, 13 August 2026. Avia Solutions. Answers `GRADING-BASIS-QUESTION-12Aug2026.md` v3.0
questions 1 and 2, both from the code and neither needing a run.

**THE CONSEQUENCE IN ONE SENTENCE.** Under both options the published claim describes a quantity the
client is never shown, so the choice is not between A and B but between re-grading on the number
that appears on the page and stating plainly that the claim covers an input rather than an output.

---

## 1. Is the engine's `p2p_carried` the same quantity as `launch_pax`?

**No. There are four transformations between them and a client's P2P number passes through all
four.** The document says that if they differ, option A carries the same fault as option B and the
choice collapses. It differs.

### The four steps, named

| | step | where | what it does |
|---|---|---|---|
| 1 | `captured` | `route_forecast` up to line 751 | the uncapped local DEMAND leg: catchment, capture share, stimulation, growth, market factor, haul trim and the size adjustment |
| 2 | the plan cap | line 760, `carried = min(total_demand, annual_capacity x max_plan_lf)` | caps P2P and connecting TOGETHER at 87.5% of seats, then line 772 pro-rates P2P down by `carried / total_demand` |
| 3 | the connectivity floor | lines 790 to 803 | re-splits the carried total, `conn_carried = max(engine_conn, resplit_conn)` and `p2p_carried = carried - conn_carried` |
| 4 | what the client reads | the payload's `p2p_carried` | the output of step 3 |

`launch_pax` passes through none of them. It is a count of passengers whose whole journey was the
nonstop, at whatever load factor the airline actually achieved, with no cap, no pro-rating and no
re-split.

### The same chain in passengers, on the case we have frozen

SJC-TPE, China Airlines A350-900 at 306 seats, 4x weekly, 2028, post-recovery growth, two-way. Every
figure below is already in `bt2_experiments.log`; the arithmetic between them reconciles to the
passenger.

| step | two-way P2P | factor |
|---|---|---|
| 1. `captured`, the uncapped local demand leg | 87,948 | |
| 2. after the 87.5% plan cap pro-rate | 83,408 | x0.9484 |
| 3. after the connectivity floor re-split | 50,068 | x0.6003 |
| 4. what the client is shown | **50,068** | |

The pro-rate factor is `carried / total_demand` = 111,384 / 117,448 = 0.9484, and 87,948 x 0.9484 is
83,408, which is FLOOR-VISIBLE's floor-off figure exactly. Step 3 is FLOOR-VISIBLE's floor-on
figure.

**So the number a claim measured on `launch_pax` would describe and the number on the page differ by
a factor of 1.757 on this case.**

### Two properties of step 2 worth stating separately

The cap pro-rates the LOCAL leg because CONNECTING demand competed for the same seats. A route whose
connecting feed is over-large therefore reports a smaller P2P figure, with no change in the local
market at all. Given what 13 August measured about the feed level, that is not a hypothetical
coupling.

And the cap can only ever reduce, so `p2p_carried` is bounded above by seats x 0.875 x the P2P share
while `launch_pax` is bounded by nothing. On a capacity-bound case, which all three frozen baseline
cases are, the reported P2P is arithmetic on seats rather than an output of the demand model.

## 2. `launch_pax` stated exactly

`bt2_discover` lines 60 to 68 and 84.

```
sum(passengers) FROM sabre
WHERE itinerary = 'NON-STOP'
  AND source_year = L
  AND origin_airport IS NOT NULL AND destination_airport IS NOT NULL
  AND origin_airport <> destination_airport
GROUP BY least(origin_airport, destination_airport), greatest(origin_airport, destination_airport)
```

- **Both directions are SUMMED, not averaged.** The pair is undirected by `least` and `greatest`.
- **The full calendar year L**, not the months operated. A route launching in November carries only
  November and December traffic under a label that names the year.
- **No cabin condition, no point-of-sale condition, no carrier condition** and no itinerary condition
  beyond `NON-STOP`. The carrier recorded beside it is chosen separately as the largest
  `operating_airline` by passengers, `row_number() ... ORDER BY sum(passengers) DESC` with `rn = 1`,
  so it names the busiest operator and not necessarily the launching one.
- Two exclusions are applied afterwards in Python at line 92: `base_mkt < MINBASE` (2,000) or
  `launch_pax > MAXRATIO x base_mkt` (5). On cohort 2024 those removed 1,652 of 2,518 candidates.

### A basis difference inside the discovery rule itself

`launch_pax` is filtered to `itinerary='NON-STOP'`. `base_mkt` at line 76 is
`sum(passengers) FROM sabre WHERE source_year = L-1` with **no itinerary filter at all**, so it
counts connecting itineraries as well.

The two exclusions therefore compare a nonstop-only numerator against an all-itineraries
denominator. `MINBASE` is a lower bar than it reads, because the base is the whole market rather
than the nonstop market, and `MAXRATIO` bites less often than a like-for-like ratio would. Neither
is wrong as long as it is stated, and it has not been stated anywhere. It bears on Task 3, since the
leaked secondary airport question turns on where the 250 market floor sits.

## 3. What changed on 13 August, which v3.0 could not know

**The feed that sits on top under option A over-reads actual connecting traffic by circa ten times.**
RECUT-RESULT, measured on 1,891 routes re-levelled to the shipped `qsi_k` of 1.0: median actual over
feed 0.098, and 0.235 on the best cell in the table, long haul into an Asian or Gulf hub. Three
candidate explanations were closed by measurement: the two board sources return identical `qshare`,
so it is not a scale artefact; the grading year is worth 3% of connecting-specific growth, so it is
not an immature ruler; and SJC-TPE sits inside the population rather than outside it.

That changes what option A buys. Option A has looked the safer choice all week because the published
92% and 86% were measured on the local quantity and nothing would need restating. It now means
attaching a calibrated local leg to an uncalibrated connecting leg and showing the client the sum.
The claim would describe the half that is calibrated while the number on the page carries the half
that is not.

**And question 4's candidate answer needs one correction.** It proposes replacing the floor with an
explicit multiplier taken from the FLOOR-EVIDENCED cuts. Those were measured on the FLAT feed. The
live path runs the QSI feed at a different level, and 13 August also found that the hub and haul cuts
are confounded with each other: holding haul constant the hub effect falls from x2.01 to x1.22 on
long haul and x1.74 on short haul. A multiplier table built from marginal cuts would double-count
the overlap. The design is still right; the numbers have to be re-cut conditionally.

## 4. What this leaves you deciding

The choice as v3.0 framed it does not survive question 1. Both options need re-grading on whatever
quantity ends up on the page, because `p2p_carried` is not `launch_pax` under either.

What is genuinely open is narrower and it is commercial rather than technical.

1. **Re-grade on the client's number.** Score the calibrated model against the quantity the payload
   actually reports, after the cap and after the floor. It is the honest claim and BASIS-COSTS-33-POINTS
   suggests it comes back well below 92 and 86.
2. **Publish the claim on a named intermediate.** Keep the figures and state precisely what they
   describe, which is the uncapped local demand leg before the cap and the floor. It survives a
   technical annex and it does not survive a sales conversation.
3. **Change what the page shows** so the claim and the number are the same quantity, which means
   deciding whether the cap and the floor belong between the model and the client at all.

I would not start the wiring until that is chosen, because the wiring is where the claim attaches
and attaching it before the quantity is settled is the fault this document was written to prevent.

Avia Solutions Limited. All rights reserved.
