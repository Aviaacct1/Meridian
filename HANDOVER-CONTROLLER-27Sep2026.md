# HANDOVER: programme controller, 27 September 2026 (chat 4 on Opus, compacted; to chat 5 on Fable)

Supersedes HANDOVER-CONTROLLER-26Sep2026.md, except where this file points at it (its sections 3
and 4: owed items still open, and the traps). From now on the CONTROLLER runs on Fable (John's
standing preference) and the Opus chat that wrote this continues as the W1 BUILD CHAT only:
engine code, acceptance probes, feed options. The controller rules; W1 builds and reports in
routes/W1-STATUS.md like any workstream.

## 1. Where the programme stands, one screen

Engine: large progress on 26 Sep, not yet demo-ready. The local leg was counted twice (fixed;
register median over-read 2.04x to 1.16x). Model 1.4 rule B is live (88 / 78 on 6,524, blind
portfolios of twenty 94%), with John's sentence on every stand surface. The schedule prior is wired
into Optimise (bounds the sweep to what airlines launch on comparable pairs, ranks by contribution,
carrier check). First-screen notices: old-engine notice, airfield demotion, "runway not checked".
Road drive times are ON for the catchment share model (measured side by side: the calibrated model
is unchanged to the passenger; the market-share engine moves -3.2% to +4.1%). The catchment page is
honest about its measure, marks other airports, states who lives nearer another airport by road,
and no longer prints SJC's client survey share or opens on SJC.

Still blocking a demo-ready Meridian, in order:
1. CONNECTING FEED over-reads on hub routes: BLQ-JFK circa 80% of carried, TIF-AUH EY 7x 73%. The
   V1 flat feed was never scored by the record. W1 (Opus chat) owes options with register effect
   to John by Mon 29 Sep.
2. TRAFFIC RIGHTS AND LOSS NOTES: Optimise chose IndiGo for TIF-AUH (fifth freedom) and a -5.6%
   margin schedule without saying so. Code WRITTEN (COMMIT-MSG-27Sep2026-w1-rights-and-loss.txt);
   commit and acceptance probe given to John, result not yet pasted.
3. SOU-JFK: UA B753 5x wins with no runway data ("NOT been checked" now shown); A21N rows are
   MARGINAL at SOU. Needs Boeing 757-300 airport planning data (W1) and John's ruling on whether a
   transatlantic A321neo off Southampton is NOT_FEASIBLE (his intended test answer).
4. SJC-TPE: calibrated model, class S0 level 1, band admits 3x only; CI A359 3x 83,538 against
   John's circa 120k control. W10 has Q1 (leaked secondary-airport pairs) and Q2 (p25-p75 as the
   bound) in W10-RULINGS 27 Sep. John rules on the answer. Not to be hand-tuned.
5. SPEED: 55-63 s per transatlantic Optimise against John's 30 s target; measure what the carrier
   check adds.
Stefan and Suzanna stay OFF until 1-3 are closed.

Stand critical path (umbrella Status block): wall artwork to the designer by 2 Oct (John owes items
40 and 44); invitations gated by the TAO mailbox, site live, five names; W3 pack generator and W2
flow/job states unswept since 22 Sep. FRIDAY NOTE (due 26 Sep) NOT WRITTEN: write it first.

## 2. Rulings and statements from John, 26-27 Sep (record verbatim in the umbrella if not there)

- Schedule prior: "no interim wiring"; W1 wires the whole once; testers back after that.
- Road times: "I would much rather make the change than the caveat." Done, measured first.
- Accuracy positioning (topics memory): 89/82-range believable, not too good; rule B 88/78 stands.
- Taif proposal (Avia work, not stand material): slide 15 must come from the NAMED run on the
  current build (EY A321 7x 2027: 124,852 total, capacity-limited at 87.5%; p2p 33,910; connecting
  90,942; spill 12,402 two-way); the earlier screen figures (p2p 55,926, cnx 68,926, spill 34,722,
  and the $8.9m / 26.3% / $20,019 economics) are from the pre-fix build. Slide 16's drive-time
  generalised cost describes catchment allocation, not the calibrated TIF-AUH forecast.

## 3. Commits: what should now be on origin/main (confirm with John's DevPC git log)

1f1efe prior acceptance fixes; then, in order, if John ran each block:
COMMIT-MSG-27Sep2026-catchment-page-taif.txt; -catchment-wording-client-data.txt;
-catchment-nearer-by-road.txt; Controller 27 Sep W10 Q1/Q2 + register (inline -m message);
-road-times-on.txt (confirmed live: server printed ROAD TIME); -w1-rights-and-loss.txt (pending).
Any COMMIT-MSG file on the mounted clone without a matching commit is an unrun block: re-issue it.

## 4. Workstation facts learnt 26-27 Sep

- Paths: DevPC clone C:\AviaDev; workstation clone C:\src\meridian; data E:\Avia.
- rasterio 1.5.1 and scikit-image 0.26.0 installed into the MACHINE Python with PYTHONNOUSERSITE=1
  and numpy 2.3.5 / scikit-learn 1.9.0 held. John's personal site-packages (C:\Users\Carte\...)
  carry sklearn 1.7.2: any pip or python step in an elevated or personal window must set
  $env:PYTHONNOUSERSITE = "1" first, or it describes the wrong environment.
- A probe window with no $hdr gets 401 and Format-List then prints the PREVIOUS $r. Every probe now
  sets $r = $null and catches failures; keep that pattern.
- schedule_prior.csv v2 lives at E:\Avia\bt2_relaxed (workstation data, not the repo).
- The SJC-TPE raw Sabre pair is ABOVE the 250 floor (calibrated model answers it); the floor fix
  in the prior (market band unkeyed under 250) did not apply to it.

## 5. Waiting on John (full questions in the umbrella; the new ones here)

- Southampton: should Meridian treat an A321neo flying SOU-JFK as NOT_FEASIBLE on runway grounds,
  so the tool says the route is unlikely to be servable (his intended answer for the test case)?
  Silence: it stays MARGINAL and an unchecked B753 wins.
- Are SFO, London, Geneva or Genoa past client airports? They are the catchment page's example
  buttons. Silence: they stay, which risks a client airport on the stand.
- Items 40 and 44 (artwork, 2 Oct), five contact names, TAO mailbox, as before.

## 6. W1 build chat (Opus) queue, in order

1. Acceptance of rights-and-loss (probe given). 2. Feed options with register effect, to John by
29 Sep. 3. Boeing 757-300 runway performance anchors (sourced, not estimated) and the A321neo SOU
verdict once John rules. 4. Carrier-check timing. 5. Old W1 queue (26 Sep handover section 3.6).
