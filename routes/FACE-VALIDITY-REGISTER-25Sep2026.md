# Face-validity register, 25 September 2026 (v2, evening)

Controller file. Purpose: measure, before any engine change, how far Meridian's answer sits
from the figures Avia's own analysts put on new routes for clients (John, 25 Sep: "that
will give you a range of routes with the numbers the analyst thought were reasonable and
were provided to clients who agreed. We then forecast those for 2027. ours doesnt need to
match but we should be directionally near them mostly"). Nothing here is client-facing; the
client forecasts are used as internal reference only. Pre-mortem 21; umbrella decisions
log 25 Sep. Sources are Egnyte paths, read 25 Sep (controller's research pass); the
analyst figure is quoted as the document states it, two-way annual passengers on the route
unless marked. SJC-TPE is the control John judges sensible.

## A. The comparison set: analyst figure stated, Meridian run on the same inputs

Meridian is run as a fixed-input Run (airline, aircraft, weekly frequency, season as the
analyst assumed) for forecast year 2027, then as a blank-form Optimise on the same pair.
Columns filled by the probe: Meridian two-way (Run), local / connecting each way, the
Optimise answer, and the ratio Meridian / analyst.

| # | Pair | Airline | Aircraft (Meridian code) | Freq, season | Analyst figure (two-way, year) | Source | Meridian Run | Optimise | Ratio |
|---|---|---|---|---|---|---|---|---|---|
| 1 | NOC-FRA | LH | E195 | 3x, annual | 19,379 (2028) | Knock Airport - Route Forecasts/Report/SENT 08 Jun 2026/Lufthansa E195 MUC BER FRA - NOC - Jun 2026.pptx | | | |
| 2 | NOC-BER | LH | E195 | 3x, annual | 19,277 (2028) | same | | | |
| 3 | NOC-MUC | LH | E195 | 3x, annual | 15,770 (2028) | same | | | |
| 4 | NOC-CDG | AF | A223 | 4x, annual | 54,390 (2028) | Knock .../Air France CDG-NOC - May 2026.pptx | | | |
| 5 | NOC-ZRH | WK | A20N | 1x, summer | 9,475 (2028) | Knock .../Edelweiss ZRH-NOC - 18 May 2026.pptx | | | |
| 6 | NOC-CPH | SK | CRJ900 | 2x, annual | 16,146 (2028) | Knock .../SAS CPH-NOC - May 2026.pptx | | | |
| 7 | NOC-KTW | W6 | A320 | 1x, annual | 13,538 (2028) | Knock .../Wizz Air KTW-NOC - Jun 2026.pptx | | | |
| 8 | AHB-IST | TK | B738 | 7x, annual | 94,631 (2030) | Archive/2025/Touwaik - Abha/Report/Abha Traffic Response - V32 MASTER.docx (draft; figures via the embedded route table) | | | |
| 9 | AHB-IST | XY | A21N | 7x, annual | 106,538 (2030) | same | | | |
| 10 | AHB-DXB | XY | A21N | 7x, annual | 106,830 (2030) | same | | | |
| 11 | AHB-ADD | ET | B38M | 3x, annual | 44,504 (2030) | same | | | |
| 12 | AHB-KWI | J9 | A21N | 3x, annual | 46,729 (2030) | same | | | |
| 13 | AHB-DEL | XY | A21N | 4x, annual | 61,296 (2030) | same | | | |
| 14 | EDI-BOS | B6 | A21N (153 seats) | 7x, annual | 91,062 (year 1, 2020) | Archive/2018/Scotland JetBlue Boston/Report/Sent/Scotland Boston JetBlue FINAL 28Mar2018.pdf (pre-COVID) | | | |
| 15 | EDI-JFK | B6 | A21N (153 seats) | 7x, annual | 94,397 (year 1) | Archive/2019/Scotland Routes 2019/Report/FINAL/jetBlue JFK final.pdf (pre-COVID) | | | |
| 16 | EDI-ATL | DL | B763 (211 seats) | 5x, summer | 58,439 (year 1, Apr-Oct) | .../Delta ATL final.pdf | | | |
| 17 | EDI-PVG | HO | B789 (322 seats) | 2x, annual | 52,753 (year 1) | .../Juneyao Air PVG final.pdf | | | |
| 18 | EDI-HKG | HX | A333 (311 seats) | 2x, annual | 52,404 (year 1) | .../Hong Kong Airlines HKG final.pdf | | | |
| 19 | EDI-CAN | CZ | B788 (228 seats) | 2x, annual | 36,391 (year 1) | .../China Southern CAN final.pdf | | | |
| 20 | EDI-DEL | 6E | A21N (220 seats) | 2x, summer | 39,686 (year 1) | .../IndiGo DEL final.pdf | | | |
| 21 | BLQ-JFK | UA (generic US FSC in the report) | A21X | 7x, annual | not stated; daily A321XLR year one, B787-9 summers from 2029 | Archive/2025/Bologna - Traffic Forecast Update 2025/Report/SENT 5 Dec 2025/AdB Traffic Forecast Update 2025 FINAL.pptx | 115,934 (25 Sep Test B) | UA 7x B77W 222,950 | n/a |
| C | SJC-TPE | CI | A359 | 7x, annual | circa 120k with curfew (Taipei pitch) | John | 172,216 unrestricted; 112,282 curfew (24 Sep) | Starlux 7x A359 194,922 | control |

Rows 8-13 are 2030 figures on a draft; the Scotland rows are pre-COVID year-1 figures and
John's own caveat applies ("a 100k potential route in 2018 is unlikely to be a 200k
potential route now"). The Knock rows are the cleanest comparison: sent to the client in
May-June 2026, first full year 2028, local and connecting stated.

## B. Assumed but without a passenger figure (frequency and aircraft only; Optimise compared to the analyst's schedule)

Bologna 2025: LOT WAW E195 5x; Condor FRA A320 7x; Air Arabia SHJ A20N 3x; Air Canada YYZ
A21X 4x/3x; Saudia JED A21X 3x; Qatar DOH A321 5x. LCY (Project Lightning, 2 Apr 2025):
LOT WAW E295 14x; Air Dolomiti MUC/VIE E190 14x; Wideroe OSL E290 7x; Finnair HEL E190 14x;
TAP LIS E190 14x. These are run as blank-form Optimise only, to see whether the tool's
schedule is in the analyst's class (regional or narrowbody, 3x to 14x) or a widebody.

## C. Not usable (no route figures): Tashkent, Shakira/Barranquilla, Zagreb 2026, Plovdiv, KMIA.

## Results

### Results, 25 Sep evening: fixed-input Runs on the analyst's inputs, forecast year 2027 (John's paste)

Workstation at 0eb7139, eight workers, MCT master. meridian_2way = carried (2 x demand.total);
demand_2way = 2 x demand.total_demand; local_ew = demand.p2p_carried each way.

| pair | al | ac | f | s | analyst | meridian_2way | ratio | demand_2way | local_ew |
|---|---|---|---|---|---|---|---|---|---|
| NOC-FRA | LH | E195 | 3 | annual | 19,379 | 33,306 | 1.72 | 94,958 | 2,453 |
| NOC-BER | LH | E195 | 3 | annual | 19,277 | 9,766 | 0.51 | 9,766 | 2,388 |
| NOC-MUC | LH | E195 | 3 | annual | 15,770 | 33,306 | 2.11 | 56,262 | 2,022 |
| NOC-CDG | AF | A223 | 4 | annual | 54,390 | 53,872 | 0.99 | 136,678 | 10,190 |
| NOC-ZRH | WK | A20N | 1 | summer | 9,475 | 9,114 | 0.96 | 20,906 | 3,087 |
| NOC-CPH | SK | CRJ900 | 2 | annual | 16,146 | 16,380 | 1.01 | 43,436 | 3,945 |
| NOC-KTW | W6 | A320 | 1 | annual | 13,538 | 4,666 | 0.34 | 4,666 | 2,323 |
| AHB-IST | TK | B738 | 7 | annual | 94,631 | 68,804 | 0.73 | 68,804 | 20,342 |
| AHB-IST | XY | A21N | 7 | annual | 106,538 | 141,414 | 1.33 | 223,436 | 41,809 |
| AHB-DXB | XY | A21N | 7 | annual | 106,830 | 141,414 | 1.32 | 235,394 | 45,809 |
| AHB-ADD | ET | B38M | 3 | annual | 44,504 | 25,968 | 0.58 | 25,968 | 6,027 |
| AHB-KWI | J9 | A21N | 3 | annual | 46,729 | 60,606 | 1.30 | 76,842 | 24,811 |
| AHB-DEL | XY | A21N | 4 | annual | 61,296 | 80,808 | 1.32 | 107,986 | 30,994 |
| EDI-BOS | B6 | A21N (153) | 7 | annual | 91,062 | 97,460 | 1.07 | 230,924 | 32,442 |
| EDI-JFK | B6 | A21N (153) | 7 | annual | 94,397 | 97,460 | 1.03 | 243,468 | 28,451 |
| EDI-ATL | DL | B763 (211) | 5 | summer | 58,439 | 51,696 | 0.88 | 92,380 | 9,315 |
| EDI-PVG | HO | B789 (322) | 2 | annual | 52,753 | 58,604 | 1.11 | 124,826 | 12,365 |
| EDI-HKG | HX | A333 (311) | 2 | annual | 52,404 | 56,602 | 1.08 | 107,032 | 14,988 |
| EDI-CAN | CZ | B788 (228) | 2 | annual | 36,391 | 41,496 | 1.14 | 86,094 | 7,703 |
| EDI-DEL | 6E | A21N (220) | 2 | summer | 39,686 | 21,560 | 0.54 | 26,670 | 8,152 |

Controller's reading (25 Sep, before the local_model and area_today columns and before the
Optimise block):
1. The carried ratio near 1.0 on fourteen rows is the seat cap, not agreement. On every one
   of them meridian_2way equals seats x freq x weeks x 2 x 0.875 (E195 3x 33,306; A223 4x
   53,872; A21N 7x 141,414; 153-seat A21N 7x 97,460; 322-seat 789 2x 58,604). The analyst
   sized the aircraft to the demand; the tool fills the aircraft from a demand that is 2 to
   5 times the analyst's: NOC-FRA 94,958 against 19,379; NOC-CDG 136,678 against 54,390;
   EDI-BOS 230,924 against 91,062; EDI-JFK 243,468 against 94,397; AHB-DXB 235,394 against
   106,830; EDI-PVG 124,826 against 52,753.
2. Where demand is below the cap the tool UNDER-reads by about half: NOC-BER 0.51, NOC-KTW
   0.34, AHB-ADD 0.58, AHB-IST TK 0.73, EDI-DEL 0.54.
3. The over-read rows all end at a hub of the named airline (FRA, MUC, CDG, CPH, IST, DXB,
   BOS, JFK, PVG, HKG, CAN); the under-read rows do not (BER for LH, KTW for W6, ADD is ET's
   hub but the read is low, DEL for 6E). Local carried is far below the analyst's local on
   the Knock rows (NOC-FRA 4,906 two-way against 16,600; NOC-CDG 20,380 against 50,000), so
   the over-read is in the connecting feed and the local is under. Hypothesis, to be
   confirmed from local_model and the feed fields, not asserted: the connecting feed on a
   hub route is several times the analyst's view (NOC-FRA analyst 2,800 connecting) and
   the local read on a thin regional route is half the analyst's.
4. The pattern is two-sided and systematic, not Bologna's: the level of the connecting feed
   at hubs, and the level of local demand on thin routes, both against the figures Avia
   put in front of clients this year.

### Results, 25 Sep evening (2): the demand fields (John's paste)

| pair | al | analyst | demand_2way | local_model (ew) | area_today (ew) | cnx_ew | induced |
|---|---|---|---|---|---|---|---|
| NOC-FRA | LH | 19,379 | 94,958 | 8,247 | 188,190 | 14,200 | False |
| NOC-BER | LH | 19,277 | 9,766 | 2,787 | 159,682 | 2,496 | False |
| NOC-MUC | LH | 15,770 | 56,262 | 3,005 | 168,439 | 14,631 | False |
| NOC-CDG | AF | 54,390 | 136,678 | 23,423 | 404,324 | 16,746 | False |
| NOC-ZRH | WK | 9,475 | 20,906 | 14,163 | 180,470 | 1,470 | False |
| NOC-CPH | SK | 16,146 | 43,436 | 10,426 | 137,834 | 4,245 | False |
| NOC-KTW | W6 | 13,538 | 4,666 | 2,723 | 298,281 | 10 | False |
| AHB-IST | TK | 94,631 | 68,804 | 27,288 | 17,124 | 14,060 | False |
| AHB-IST | XY | 106,538 | 223,436 | 94,193 | 17,124 | 28,898 | False |
| AHB-DXB | XY | 106,830 | 235,394 | 106,616 | 130,635 | 24,898 | False |
| AHB-ADD | ET | 44,504 | 25,968 | 12,630 | 16,467 | 6,957 | False |
| AHB-KWI | J9 | 46,729 | 76,842 | 34,856 | 12,134 | 5,492 | False |
| AHB-DEL | XY | 61,296 | 107,986 | 46,247 | 17,870 | 9,410 | False |
| EDI-BOS | B6 | 91,062 | 230,924 | 68,492 | 56,645 | 16,289 | False |
| EDI-JFK | B6 | 94,397 | 243,468 | 68,341 | 145,441 | 20,280 | False |
| EDI-ATL | DL | 58,439 | 92,380 | 28,985 | 44,267 | 16,533 | False |
| EDI-PVG | HO | 52,753 | 124,826 | 20,992 | 23,392 | 16,937 | False |
| EDI-HKG | HX | 52,404 | 107,032 | 26,060 | 32,388 | 13,313 | False |
| EDI-CAN | CZ | 36,391 | 86,094 | 12,084 | 8,037 | 13,045 | False |
| EDI-DEL | 6E | 39,686 | 26,670 | 20,337 | 29,451 | 2,628 | False |

Feed demand each way, by arithmetic on the annual rows (demand_2way / 2 less local_model
grown to 2027; seasonal rows ZRH, ATL, DEL excluded because local_model is annual):
NOC-FRA circa 38,900 (analyst connecting 2,800 two-way); NOC-MUC circa 25,000 (analyst
2,000); NOC-CDG circa 44,000 (analyst 4,400); NOC-CPH circa 10,900 (analyst 1,600); EDI-BOS
circa 44,000 (analyst 48,000 two-way, the one row where the analyst also had a large feed);
EDI-PVG circa 41,000; EDI-CAN circa 30,000; EDI-HKG circa 26,000. Local against the
analyst's local (two-way): NOC-FRA 17k v 16,600 (agrees); NOC-CDG 48.7k v 50,000 (agrees);
NOC-CPH 21.7k v 14,600; NOC-BER 5.8k v 18,000; NOC-MUC 6.2k v 13,800; NOC-KTW 5.7k v
13,300; EDI-BOS 142k v 43,000. Local against the service area's traffic today: AHB-IST XY
94,193 from 17,124 (5.5x the existing market); AHB-KWI 2.9x; AHB-DEL 2.6x; EDI-CAN 1.5x;
EDI-BOS 1.2x; AHB-DXB 0.82; EDI-PVG 0.90; EDI-HKG 0.80; NOC rows 0.02-0.08.

Controller's reading, 25 Sep late:
1. THE FEED. On a regional route into a major hub the connecting feed is 10 to 25 times the
   analyst's figure and is most of the tool's demand (NOC-FRA 39k each way of 47k). The
   feed level is the V1 flat capture (one share of the hub's beyond and behind markets for
   every route, set 15 Aug); Frankfurt's market is so large that a flat share of it dwarfs
   a three-weekly E195. Avia's analysts put connecting at 8-15% of the route on these
   (Knock rows) and 53% on EDI-BOS; the tool's feed does not scale with the route.
2. THE LOCAL, two ways. On thin non-hub routes the local read is half to a third of the
   analyst's (BER, MUC, KTW). On small origins the model gives a new route several times
   the service area's existing traffic (AHB rows on flynas and Jazeera, EDI-CAN, EDI-BOS):
   stimulation with nothing to bound it. Where the origin's own market is large and
   established the local is close to the analyst (NOC-FRA, NOC-CDG).
3. WHY THE RECORD DID NOT CATCH IT (hypothesis for W10 to confirm from the scoring basis):
   the back-test scores carried passengers on realised launches, where the airline chose
   the capacity and filled it; a model that reads demand at 2 to 5 times and then caps at
   seats x load factor scores well on that record. "Capacity is the biggest predictor" is
   this in one sentence. The 89/82 pair may be substantially a capacity claim.
4. The fix, in shape, is the analysts' own practice: connecting feed as a share of the
   route's own size, with the share depending on haul and hub, not a share of the hub's
   market; and a bound on local stimulation relative to the service area. Both measured
   on the back-test before anything ships (John's ruling).

John, 25 Sep: Knock is "one of the hardest airports to forecast for ... much more art than
science", so the NOC rows are INDICATIVE and the finding rests on Edinburgh and Abha. On
the seven Edinburgh rows the tool is 2.0-2.6x the analyst on every hub-ended long-haul
(BOS 2.5x, JFK 2.6x, PVG 2.4x, HKG 2.0x, CAN 2.4x, ATL summer 1.6x) and 0.7x on the one
non-hub summer route (DEL). At EDI-BOS the local alone (137k two-way) is 3.2x the analyst's
local and exceeds the service area's whole Boston traffic today (113k two-way); the feed
(88k) is 1.8x the analyst's 48k. Both mechanisms, on a large established airport.

### Results, 26 Sep: the register re-run after the go-live (rule B + basis fix, 8bb87a3; John's paste)

| pair | al | analyst | carried 2way | ratio | demand 2way | dem_ratio (25 Sep) | local ew | cnx ew |
|---|---|---|---|---|---|---|---|---|
| NOC-FRA | LH | 19,379 | 33,306 | 1.72 | 94,958 | 4.90 (4.90) | 2,453 | 14,200 |
| NOC-BER | LH | 19,277 | 9,766 | 0.51 | 9,766 | 0.51 (0.51) | 2,388 | 2,496 |
| NOC-MUC | LH | 15,770 | 33,306 | 2.11 | 56,262 | 3.57 (3.57) | 2,022 | 14,631 |
| NOC-CDG | AF | 54,390 | 53,872 | 0.99 | 103,814 | 1.91 (2.51) | 4,888 | 22,048 |
| NOC-ZRH | WK | 9,475 | 9,114 | 0.96 | 11,440 | 1.21 (2.21) | 2,970 | 1,587 |
| NOC-CPH | SK | 16,146 | 16,380 | 1.01 | 31,496 | 1.95 (2.69) | 2,336 | 5,854 |
| NOC-KTW | W6 | 13,538 | 4,666 | 0.34 | 4,666 | 0.34 (0.34) | 2,323 | 10 |
| AHB-IST | TK | 94,631 | 31,720 | 0.34 | 31,720 | 0.34 (0.73) | 9,378 | 6,482 |
| AHB-IST | XY | 106,538 | 127,122 | 1.19 | 127,122 | 1.19 (2.10) | 37,584 | 25,977 |
| AHB-DXB | XY | 106,830 | 112,346 | 1.05 | 112,346 | 1.05 (2.20) | 36,392 | 19,780 |
| AHB-ADD | ET | 44,504 | 15,136 | 0.34 | 15,136 | 0.34 (0.58) | 3,513 | 4,055 |
| AHB-KWI | J9 | 46,729 | 41,066 | 0.88 | 41,066 | 0.88 (1.64) | 13,570 | 6,963 |
| AHB-DEL | XY | 61,296 | 53,500 | 0.87 | 53,500 | 0.87 (1.76) | 20,520 | 6,230 |
| EDI-BOS | B6 | 91,062 | 97,460 | 1.07 | 154,924 | 1.70 (2.54) | 24,451 | 24,279 |
| EDI-JFK | B6 | 94,397 | 97,460 | 1.03 | 182,082 | 1.93 (2.58) | 21,614 | 27,117 |
| EDI-ATL | DL | 58,439 | 51,696 | 0.88 | 67,950 | 1.16 (1.58) | 7,026 | 18,821 |
| EDI-PVG | HO | 52,753 | 58,604 | 1.11 | 97,266 | 1.84 (2.37) | 7,566 | 21,736 |
| EDI-HKG | HX | 52,404 | 56,602 | 1.08 | 79,132 | 1.51 (2.04) | 10,294 | 18,007 |
| EDI-CAN | CZ | 36,391 | 41,496 | 1.14 | 67,454 | 1.85 (2.37) | 4,098 | 16,650 |
| EDI-DEL | 6E | 39,686 | 14,620 | 0.37 | 14,620 | 0.37 (0.67) | 5,527 | 1,782 |

Controller's reading, 26 Sep:
1. The local fix did what W10 said on every row the calibrated model answers. Excluding Knock
   (indicative), the median demand ratio falls from 2.04 to 1.16; rows within 0.8-1.25 of the
   analyst rise from none of thirteen to five (AHB-IST XY, AHB-DXB, AHB-KWI, AHB-DEL, EDI-ATL).
   EDI-BOS local is now 48.9k two-way against the analyst's 43k local (1.14x, was 3.2x).
2. FOUR KNOCK ROWS ARE UNCHANGED TO THE PASSENGER (NOC-FRA, BER, MUC, KTW): the calibrated model
   did not answer them and the old QSI engine did. Check forecast_engine.declined in their saved
   JSONs before reading anything into those four.
3. THE FEED is now the leading over-read on long-haul demand: connecting is 50-80% of carried on
   EDI-PVG, CAN, ATL, HKG and the NOC hub rows. The carried headline stays within 15% of the
   analyst on every Edinburgh long-haul row because the aircraft fills; the excess is in demand
   and spill. The feed job (controller as W1) starts from these rows.
4. A NEW UNDER-READ, sharper after the fix: routes below their seat cap now read at about a third
   of the analyst (AHB-IST on Turkish 0.34, AHB-ADD 0.34, EDI-DEL 0.37, NOC-KTW 0.34, NOC-BER
   0.51). The halving is correct on basis; the question is whether the model, the analysts, or
   both are wrong on thin routes. EDI-DEL's analyst row states 45,760 seats for a summer-only 2x
   A321, which is a full year of seats, so that row is itself suspect. AHB-IST on Turkish reads
   a quarter of flynas on the same pair and gauge: a carrier effect in the model that needs
   explaining before the stand. For W10, owner of the record: one question, measured, not
   assumed.


## Acceptance Optimise after the go-live and notices commit, 26 Sep 2026 evening

| Pair | Optimise pick | Two-way carried | Local each way | Connecting each way | Airfield note |
|---|---|---|---|---|---|
| SOU-JFK | AA A21N 7x | 124,852 | 31,143 | 31,283 | blank |
| BLQ-JFK | DL A333 7x | 146,028 | 14,702 | 58,312 | blank |
| SJC-TPE | JX A359 5x | 134,116 | 30,144 | 36,915 | blank |

Source: workstation Optimise run pasted by John, 26 Sep 2026.

Controller's reading. SJC-TPE is now close to the circa 120k curfew pitch: acceptable. BLQ-JFK
lands near the Avia 2025 figure but for the wrong reason: connecting is circa 80% of carried and
a widebody still wins. Bologna Optimise is not demonstrated until the feed fix and the schedule
prior land. The blank airfield note is not yet evidence either way: it may mean no type was
NOT_FEASIBLE, or that the notices commit is not live. Check the per-row airfield field.
