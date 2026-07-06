# Avia Cortex - Engine V2 handover: the schedule-quality QSI connecting feed

Start a NEW chat with this note. It is the design + testing strategy for V2 of the forecast engine.
V1 (the current live tool) is working and well-calibrated; V2 runs in parallel while the team tests V1.
Do NOT change the live feed until V2 back-tests at least as well as V1.

## 1. The problem V2 fixes
A QSI forecast is meant to assess the QUALITY of a connection and allocate demand by it: a high-quality
connection (short total elapsed journey, tight-but-legal layover over MCT, low circuity, online/alliance)
wins MORE of an onward market; a poor one wins LESS. **V1 does not do this.** V1's feed
(route_feed.feed_side / behind_feed) measures the onward O&D market at the hub and applies a flat,
calibrated capture x an alliance coefficient x a circuity screen. It counts *all* connections at an
average capture. It works on the back-test (FSC-forecastable median ~1.0), but for the wrong reason: it
captures the *average* level of connectivity via calibration, not the quality of a *specific* schedule.

Consequence: departure/arrival time does not change V1's forecast at all. But for an airline it is
critical (John, 2 Jul 2026): the arrival time at the hub decides whether you can sell compelling through
fares on the GDS with low total journey time, which is how booking engines rank and display options.
Clients will expect to enter a departure time and get a different forecast, and to optimise the departure
time for maximum connections. V2 must make schedule timing a real lever.

## 2. What was already tried and PARKED (do not repeat)
An MCT "schedule-banking" haircut was built and back-tested (mct_bank.py, opt-in via feed_cfg
['mct_banking'], flag threads /api/forecast?mct_banking=1; test_mct.py; backtest.py --mct-banking;
compare_mct.py). It counts the share of each onward market's frequency that is *connectable* within MCT
of an optimised arrival, and scales the feed down by it. **Verdict: it made the fit slightly WORSE on
every slice** (compare_mct: hub med|ln| +0.043, material-feed +0.033, within-20% flat/down). Why it
failed: launched routes are already reasonably banked by their airlines, so there is little connectivity
variance to explain, and a uniform ~50% haircut is noise. It is PARKED, opt-in and off by default;
the live tool is untouched. Lesson for V2: do not apply a supply filter; SCORE QUALITY and COMPETE FOR
SHARE, so good schedules win and bad ones lose - that discriminates, a haircut does not.

## 3. V2 design - the real QSI connecting model
For each onward market M served through the hub H (e.g. SJC-TPE-onward):
1. Enumerate the FEASIBLE ITINERARIES for O&D (origin -> M): the NEW route's connection
   (origin->H on the proposed schedule, layover, H->M from OAG times) AND the existing competing
   itineraries (other hubs / carriers already serving origin->M, from OAG + Sabre).
2. SCORE each itinerary with a QSI function of: total elapsed journey time, connection buffer above the
   MCT (from mct_master.csv, default 60), circuity, number of stops, and carrier/alliance quality
   (online > alliance > interline). Illegal connections (buffer < MCT) score 0.
3. The new route's CAPTURE of market M = its QSI score / sum of all itineraries' QSI scores (a share,
   logit or proportional), x the measured market size. This REPLACES V1's flat capture x conn_coeff.
4. Departure time enters through step 1-2: change the proposed departure -> different hub arrival ->
   different layover/elapsed for every onward M -> different QSI share. The dep-time optimiser
   (already prototyped as mct_bank.optimise) maximises the total QSI-weighted feed over the day.

connection_builder.py already has the MCT machinery (load_mct_data, lookup_mct cascading, classify_
connection, --arr-time input) and is a good starting scaffold; it needs the elapsed-time QSI scoring
and the competing-itinerary enumeration added, then wiring into feed_side behind a flag.

## 4. Testing / calibration strategy (John's method, formalised)
The acceptance gate: **V2 (QSI feed, re-calibrated) must be at least as accurate as V1 on the back-test.**
Because QSI quality-weighting counts fewer connections than V1's count-all, the level WILL drop and must
be re-calibrated back to outturn, then the DISPERSION compared.

- Phase 0 - Data: the launched-route back-test set already exists (backtest.py over the OAG history,
  ~10 years). The OAG store carries local_dep_time / local_arr_time per flight (oag_store._COLS), so we
  have every launched route's ACTUAL departure time and the hub onward wave with times. Outturn is
  sector_traffic (P2P + all feed, both directions). MCT is mct_master.csv (63 hubs; 60 default).
- Phase 1 - Build the QSI scorer + competing-itinerary enumerator (section 3). Wire into feed_side as an
  opt-in (feed_cfg flag), exactly like mct_banking, so V1 is untouched.
- Phase 2 - Calibrate at ACTUAL flown times: run the QSI feed on every launched route USING ITS REAL
  departure time, and tune the QSI scale / capture level so the modelled feed re-solves to actual
  outturn on average (median forecast/outturn -> 1.0), on the FORECASTABLE subset (real pre-existing
  market), not induced. This makes the optimised model reproduce the actual flown forecast.
- Phase 3 - VALIDATE (the gate): compare_mct-style, matched routes, re-centred to median 1.0, compare
  DISPERSION (med|ln|, within +/-20% / +/-30%) of V2 vs V1 on FORECASTABLE + HUB + material-feed slices.
  V2 must be no worse; ideally better on hub / feed-heavy where it should now discriminate. If worse,
  iterate the QSI weights (elapsed vs buffer vs circuity vs alliance) and re-run.
- Phase 4 - Face-validity of the dep-time lever: with the calibrated V2, optimise each route's departure
  time. For routes flown at a SUB-OPTIMAL time due to slot/curfew limits (e.g. SJC 23:00 embargo vs an
  ideal ~00:30 to TPE), the optimum should predict MORE than actual (the upside of ideal timing); routes
  flown at good times should sit at optimum ~= actual. So optimum/actual should be >= 1 and the biggest
  gaps should line up with known slot/curfew constraints. This is a sanity check, not an accuracy metric.
- Phase 5 - Reweight interacting assumptions: the new feed level interacts with the P2P capture and the
  stimulation priors. Re-run the FULL back-test (total = P2P + V2 feed) and re-tune those priors until
  the TOTAL forecast back-tests at least as well as V1 on every major slice. Iterate. Expect several long
  runs (each full back-test is ~6-8h; use --limit 600 on hub-heavy subsets for fast iteration, full runs
  only to confirm). backtest.py --limit now caps pinned runs too (fixed 2 Jul 2026).

Metrics: primary = dispersion of forecast/outturn on FORECASTABLE hub + material-feed, re-centred
(med|ln| lower, within-20% higher). Guard = total back-test not worse on any major slice. Secondary =
dep-time face validity (Phase 4).

## 5. Assets in place (do not rebuild)
- backtest.py: launched-route back-test vs total outturn; --feed-fix (the live feed model), --mct-banking
  (parked), --routes-file pinned_global.json (identical set A/B; --limit now caps it), --out CSV,
  --min-outturn. asif_forecast() calls RF.forecast(feed_cfg=...). Grades fc_over_out / fc_over_p2p.
- compare_mct.py: matched, re-centred dispersion comparison of two backtest CSVs (reuse for V1-vs-V2).
- mct_bank.py: MCT load + hub onward-wave from OAG times + connectable share + arrival optimiser
  (the optimiser is reusable; the connectable-share metric is the part to REPLACE with QSI quality).
- mct_master.csv: 63 hubs x DOM/INT MCT categories; 60-min default. From Egnyte "MCT Master List.xlsx"
  (/Shared/Company Data/18 Products/QSI/Reference Tables/).
- connection_builder.py: standalone MCT-aware connection builder (scaffold for the QSI scorer).
- route_feed.py: feed_side (beyond) / behind_feed (behind); both now return per-city detail (base O&D +
  share + captured + pdew) via detail=True. The QSI capture replaces the flat cap * conn_coeff here.
- route_forecast.py forecast(): the calibrated engine; threads feed_cfg; returns beyond_detail /
  behind_detail. Has an mct_file param hook (dest_metro_share) - unused by the feed.
- oag_store.py: OAG DuckDB store; columns include local_dep_time, local_arr_time, days_of_op, alliance,
  arr_country/dep_country - everything the QSI scorer needs.
- Memory: qsi-schedule-banking (this thread + PARK verdict), qsi-catchment-design, qsi-share-calibration,
  qsi-method-improvements (validate-then-improve), qsi-report-pitch.

## 6. Sequencing
V2 is a research + engine build. Run it in a FRESH chat, parallel to the team testing live V1. Keep V2
strictly opt-in until Phase 3 passes; only then flip the default. Nothing about V1 changes in the
meantime.

## 7. Open smaller jobs (V1 polish, separate from V2 - see the live chat's task list)
- Catchment map into the deck + workbook (task #36): render the drive-time catchment as a static image.
- Server-render the HTML digital pitch (task #38): content is JS-rendered so iOS previews show only
  headings; render server-side in Python, keep JS only for the sliders.
- Wire catchment.tier_split() into the P2P forecast rows (Primary/Secondary/Contested); classifier built,
  not wired.
- Airport-capture UPLIFT mode: airport_fit.py flagged credible under-read secondaries (MAD ~2.4, LGW,
  EDI, LIS, SEA, DXB) - promote as CAPPED FACTORS (not flat shares) and re-do SJC as an uplift (its flat
  0.32 now over-captures its domestic routes). Quarantine the 4-15x structural outliers (HYD/KHN/BKK):
  those are a FEED under-credit, likely the same thing V2 addresses.
