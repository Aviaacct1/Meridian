
## 27 September 2026, W1 build chat (Opus): rights-and-loss acceptance

Workstation probe pasted by John after COMMIT-MSG-27Sep2026-w1-rights-and-loss.txt:
| Pair | Pick | Two-way | Margin | Rights note | Loss note | Seconds |
|---|---|---|---|---|---|---|
| TIF-AUH | EY A20N 3x | 48,048 | -4.1% | 6E, GF, IX, J9 set aside | contributes, loses at generic ownership | 26.7 |
| SOU-JFK | UA B753 5x | 102,658 | 52.5% | none | none | 56.9 |
| BLQ-JFK | DL A339 7x | 145,802 | 27.0% | none | none | 58.6 |
| SJC-TPE | CI A359 3x | 83,538 | 32.6% | none | none | 26.3 |
All four in. PASS on the fix: TIF-AUH no longer picks a fifth-freedom carrier; US and Italian
pairs unchanged. NEW FLAG: route margins of 52.5% (B753 transatlantic), 32.6% (A359) and 27.0% (A339) are not
credible; economics basis (generic type table, proxy fare) to be checked before any economics
screen is shown. Queue: feed options (29 Sep), B753 runway anchors, margin check, carrier-check timing.


## 27 September 2026: feed options measured on the register (tools/probe_register.ps1, 8010 V1 against 8011 QSI level)

Analyst schedules, forecast year 2027, 21 rows with an analyst figure (BLQ-JFK has none).
V1 feed (shipped): median Meridian/analyst 1.01; 14 of 21 within +-20%.
QSI level (AVIA_FEED_LEVEL=qsi): median 1.01; 13 of 21 within +-20%; SJC-TPE rises 128,162 to
183,856 (control circa 120k); AHB-IST TK 31,720 to 79,206.
Reading: on the analysts' own schedules the V1 feed does not inflate totals; the QSI level is not
better and breaks the control. The misses are thin or small-origin routes, over (NOC-FRA 1.72, NOC-MUC
2.11, both E195 3x at the 87.5% cap) and under (NOC-KTW 0.33, AHB-IST TK 0.34, AHB-ADD 0.34, EDI-DEL
0.37, NOC-BER 0.49). The high connecting shares (BLQ-JFK 80%, TIF-AUH 73%) arise where Optimise or
the user puts a large-hub carrier on more seats; on the analysts' BLQ-JFK schedule (UA A21X 7x) the
share is 54%. Open: on uncapped rows the calibrated local leg moves with the feed level (AHB-IST TK
local 9,378 to 13,823); to be explained before any feed change.
Source: E:\Avia\probe\register_feed_20260926-1634.csv, pasted by John.


## 27 September 2026: fare basis measured (tools/fare_check.py, Sabre 2025, ND)

USD per passenger as Sabre states them (one-way on the evidence: LHR-JFK economy total 536).
| Pair | Premium share | All-cabin total (what the P&L uses for economy) | Economy total | Economy base | Premium total | Premium base |
|---|---|---|---|---|---|---|
| EDI-BOS | 14.0% | 784 | 535 | 247 | 2,317 | 1,468 |
| EDI-JFK | 19.8% | 978 | 564 | 272 | 2,656 | 1,844 |
| BLQ-JFK | 11.0% | 639 | 478 | 265 | 1,945 | 1,344 |
| SJC-TPE | 16.7% | 861 | 600 | 449 | 2,161 | 1,991 |
| SOU-JFK | 7.4% | 1,012 | 935 | 526 | 1,980 | 1,468 |
| LHR-JFK | 32.7% | 1,269 | 536 | 267 | 2,777 | 2,027 |
Finding: every economy seat is priced at the all-cabin fare, 1.1x to 2.4x the economy fare, while
the premium cabin is priced at a fixed 1,400 (below every measured premium fare). Economy seats are
most of the aircraft, so revenue and margin are overstated on long-haul. Taxes: total includes
government taxes and carrier surcharges, base excludes both; true airline revenue lies between.
Next: margin effect of cabin fares (total and base) via econ_fare/bus_fare overrides; then the fix.

## 27 September 2026: b478b97 carried W2's uncommitted work

`git add` on whole files swept W2's session edits in cortex_app.py and cortex_dashboard.html into
the cabin-fares commit (pack queue endpoints, email field, AVIA_SHOW_ECONOMICS switch default OFF,
rotation and "incl. feed" slips). Read in full from the diff; nothing there conflicts with the fare
change. cortex_app.py imports pack_queue, which was untracked: committed separately
(COMMIT-MSG-27Sep2026-w2-pack-queue-module.txt) so a clean clone starts. Controller: W2 should be
told, and the rule for every chat is to commit its own files before another chat's block runs.
Economics screens are withheld by default until pre-mortem 33 is accepted; the API still returns
economics, and AVIA_SHOW_ECONOMICS=1 shows them.


## 27 September 2026: cabin fares live (b478b97 + 03f6ad9), acceptance passed

fare_source cabin+premium on all five; two-way passengers unchanged. Margin before / after:
EDI-BOS B6 A21N 7x 46.5% / 34.4%; BLQ-JFK UA A21X 7x 38.3% / 27.1%; SJC-TPE CI A359 7x 16.3% / 4.4%;
SOU-JFK UA B753 5x 52.5% / 34.1%; TIF-AUH EY A321 7x 21.4% / 4.3% (contribution 2.5m USD a year,
breakeven 79.1%). Europe-US margins still read high because fares include taxes (UK and Italian
departure taxes); economics stays WITHHELD on the stand (AVIA_SHOW_ECONOMICS off) and pre-mortem 33
stays open until a sourced tax table exists, after Routes. Taif slide 15 economics replaced by the
figures above, labelled "fares as sold, including taxes".
Next (built, not yet committed): Optimise's aircraft sizing ranks on the measured cabin fares
instead of the distance proxy (COMMIT-MSG-27Sep2026-w1-optimise-measured-fares.txt).

## 27 September 2026: Optimise on measured fares, acceptance and timing

Blank-form Optimise after the measured-fare commit: SOU-JFK UA B753 5x 102,658 (unchanged, runway
unchecked note shown); BLQ-JFK AA B788 7x 143,298, 83.3%, margin 17.8% (was DL A339 145,802); SJC-TPE
CI A359 3x 83,538 (unchanged); TIF-AUH EY A20N 3x 48,048, margin -17.3% on a premium fare from 24
bookings (thin-sample note built, COMMIT-MSG-27Sep2026-w1-thin-fare-note.txt).
Timing: cold 94.5 / 83.1 / 38.5 / 23.6 s; warm SOU-JFK 44.4 s, BLQ-JFK 55.3 s. The fare lookup costs
nothing warm. Launch warm-up for Optimise referred to W2 (W2-RULINGS 27 Sep). Warm transatlantic
Optimise is still 44-55 s against John's 30 s: next W1 job, measured breakdown first (stage 1 cells,
stage 2 tasks, seasonal cells, carrier check, final forecast).
