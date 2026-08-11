#!/usr/bin/env python3
"""
Avia Solutions - Aircraft Economics / Route P&L module.
=======================================================
Python rebuild of the "Project Maverick Airline Route Profitability Model"
(Feb 2025). Completes the integrated business plan: demand (QSI) -> revenue
(revenue_forecast) -> COST + PROFIT (this) -> report.

Single-route TURNAROUND economics (out + back):
  Revenue  = cabin fares (pax x fare x 2) + cargo + charges recovery
  Variable = fuel, airframe & engine maintenance, catering, landing & per-pax
             charges (both ends), en-route navigation, ground handling
  Direct fixed   = ownership/lease, insurance, crew   (allocated via $/block-hour)
  Indirect fixed = admin/overhead + sales (% of net revenue)
  -> turnaround profit, margin, cost per seat, CASK, breakeven load factor

Aircraft costs are held as $/block-hour rates; airport charges per airport;
en-route via the Maverick formula. Rate tables are seeded here from the model's
worked example and will be populated across types from Egnyte operating models.
Validation target: Maverick BA LCY-EDI E190 = rev $22,158, cost $14,912,
profit $7,246, margin 32.7%.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional

# Standard disclaimer - MUST appear on every aircraft economics output (report, exports,
# slides, tables). Full text and rationale in "Aircraft economics - disclaimer.md".
DISCLAIMER_FULL = (
    "These aircraft economics outputs are indicative and intended for directional planning "
    "and comparison only. They are not a statement of the actual cost or profitability of any "
    "specific airline, aircraft or route. The figures are built from generic and published "
    "industry assumptions, including appraiser lease rates and values, OEM-indicative "
    "maintenance reserves, standardised utilisation by airline business model, and published "
    "or benchmark airport and air navigation charges. They do not reflect any individual "
    "operator's cabin configuration (LOPA), specific weight variant (MTOW), negotiated aircraft "
    "acquisition or lease terms, fuel hedging position, maintenance or component support "
    "agreements, crew costs, overhead structure, ancillary revenue or internal accounting "
    "policies. Actual results will differ, in some cases materially. These outputs should not be "
    "relied upon as a forecast of any particular operator's results, and Avia Solutions accepts "
    "no liability for any decision taken on the basis of them."
)
DISCLAIMER_SHORT = (
    "Indicative, for directional guidance only. Built on generic published assumptions, not any "
    "airline's actual LOPA, MTOW, contract terms or internal P&L. Actual results will differ."
)

# ---------------------------------------------------------------- aircraft DB
# Per-block-hour rates (USD). fuel via burn x price; maint = airframe+engine.
AIRCRAFT: Dict[str, dict] = {
    # Per-block-hour USD rates. fuel via burn x price; maint = airframe+engine combined.
    # CALIBRATION (27 June): fuel_burn from published cruise/block data (citable, current);
    # cost levels anchored as tagged in 'src': E190 = Maverick LCY-EDI worked example
    # (validated 0.3%); E170/Saab = Maverick Cost/BH; A330/787 = LHLCC 2015 (maint) with
    # crew/ownership re-anchored to Belobaba Form41 2013 + FAA YE2023 categories (prior
    # widebody crew/ownership were too high); narrowbody = FAA NB category + easyJet unit
    # cost; turboprop/RJ = EUROCONTROL/FAA RJ. See "Aircraft Economics Sourcing Reference.md".
    # Refine further from in-house LHLCC/Avianca/Uzbekistan/PaceLab models.
    # --- Regional / turboprop ---
    "ATR72":  dict(econ_seats=70, bus_seats=0,  mtow_kg=23000, cargo_cap_kg=0, fuel_burn_kg_per_bh=620,  maint_per_bh=380, crew_per_bh=470, ownership_per_bh=360, price_usd=20e6, annual_util_bh=2200, range_km=1500, category="Regional", src="EUROCONTROL Dash8 + turboprop benchmark; burn ATR factsheet"),
    "DH8D":   dict(econ_seats=78, bus_seats=0,  mtow_kg=30000, cargo_cap_kg=0, fuel_burn_kg_per_bh=720,  maint_per_bh=430, crew_per_bh=520, ownership_per_bh=440, price_usd=25e6, annual_util_bh=2200, range_km=2000, category="Regional", src="EUROCONTROL Dash8 $1,921/fh all-in; burn published"),
    # REGIONAL JET FUEL BURN CORRECTED 10 August 2026 against reported actuals. See the note below
    # the table. The previous figures ran at 0.51 to 0.75 of what US operators actually burned.
    "CRJ900": dict(econ_seats=76, bus_seats=12, mtow_kg=38300, cargo_cap_kg=0, fuel_burn_kg_per_bh=1474, maint_per_bh=520, crew_per_bh=640, ownership_per_bh=560, price_usd=25e6, annual_util_bh=1900, range_km=2900, category="Regional", src="burn: US DOT Form 41 P-5.2 2023 fuel issued over airborne hours, blocked with the T-100 measured ratio 0.708 (was 1,100, 0.75x actual); rest FAA YE2023 RJ61-99 category"),
    "E170":   dict(econ_seats=62, bus_seats=10, mtow_kg=38600, cargo_cap_kg=0, fuel_burn_kg_per_bh=1431, maint_per_bh=470, crew_per_bh=650, ownership_per_bh=560, price_usd=25e6, annual_util_bh=1708, range_km=3900, category="Regional", src="burn: US DOT Form 41 P-5.2 2023, T-100 block ratio 0.715 (was 920, 0.64x actual); rest Maverick Cost/BH + FAA RJ"),
    "E190":   dict(econ_seats=88, bus_seats=10, mtow_kg=51800, cargo_cap_kg=0, fuel_burn_kg_per_bh=1950, maint_per_bh=529.1, crew_per_bh=712.9, ownership_per_bh=731.7, price_usd=6.27e6, annual_util_bh=1708, range_km=4500, category="Regional", src="burn: SCALED from the well-sampled E170/E175 Form 41 2023 cluster, NOT from the type's own row, which is JetBlue alone on 102 airborne hours during the year it retired the fleet and reads 46% above a heavier-per-tonne E175; corroborated by Aircraft Commerce Issue 64 at 1,923-1,980 block (was 1,105.5)"),
    "E195":   dict(econ_seats=120,bus_seats=0,  mtow_kg=52300, cargo_cap_kg=0, fuel_burn_kg_per_bh=2116, maint_per_bh=540, crew_per_bh=720, ownership_per_bh=760, price_usd=27e6, annual_util_bh=1900, range_km=4800, category="Regional", src="burn: SCALED from the corrected E190 on the module's own prior E195/E190 ratio of 1.085; no US operator files P-5.2 for the type, so derived, not measured; rest FAA RJ category"),
    "SF34":   dict(econ_seats=50, bus_seats=0,  mtow_kg=22000, cargo_cap_kg=0, fuel_burn_kg_per_bh=600,  maint_per_bh=300, crew_per_bh=420, ownership_per_bh=300, price_usd=8e6,  annual_util_bh=2000, range_km=1700, category="Regional", src="turboprop benchmark; burn published"),
    # --- Narrowbody (LCC / FSC). FAA NB<165k non-fuel ~ maint1004/crew1336/own586 ---
    "A319":   dict(econ_seats=144,bus_seats=0,  mtow_kg=75500, cargo_cap_kg=0, fuel_burn_kg_per_bh=2200, maint_per_bh=900, crew_per_bh=1150, ownership_per_bh=700, price_usd=35e6, annual_util_bh=2300, range_km=6700, category="Narrowbody", src="FAA YE2023 NB<165k; burn published"),
    "A320":   dict(econ_seats=180,bus_seats=0,  mtow_kg=78000, cargo_cap_kg=0, fuel_burn_kg_per_bh=2400, maint_per_bh=1000, crew_per_bh=1300, ownership_per_bh=900, price_usd=45e6, annual_util_bh=2300, range_km=6100, category="Narrowbody", src="FAA NB<165k (Belobaba A320 2013 non-fuel ~2,094 inflated); burn published"),
    "A20N":   dict(econ_seats=186,bus_seats=0,  mtow_kg=79000, cargo_cap_kg=0, fuel_burn_kg_per_bh=2050, maint_per_bh=960, crew_per_bh=1300, ownership_per_bh=1200, price_usd=50e6, annual_util_bh=2300, range_km=6500, category="Narrowbody", src="FAA NB + neo lease premium (IBA ~$400k/mo); burn published"),
    "A321":   dict(econ_seats=200,bus_seats=16, mtow_kg=93500, cargo_cap_kg=0, fuel_burn_kg_per_bh=2750, maint_per_bh=1100, crew_per_bh=1380, ownership_per_bh=950, price_usd=50e6, annual_util_bh=2300, range_km=5900, category="Narrowbody", src="FAA NB>=165k; burn published"),
    "A21N":   dict(econ_seats=206,bus_seats=16, mtow_kg=97000, cargo_cap_kg=0, fuel_burn_kg_per_bh=2400, maint_per_bh=1050, crew_per_bh=1380, ownership_per_bh=1300, price_usd=55e6, annual_util_bh=2300, range_km=7400, category="Narrowbody", src="FAA NB>=165k + neo lease (IBA ~$460k/mo); burn published"),
    "A21X":   dict(econ_seats=162,bus_seats=20, mtow_kg=101000,cargo_cap_kg=2000, fuel_burn_kg_per_bh=2500, maint_per_bh=1100, crew_per_bh=1500, ownership_per_bh=1500, price_usd=65e6, annual_util_bh=2400, range_km=8700, category="Narrowbody-LR", src="A321neo + weight delta (NO clean XLR public data); burn A321LR proxy"),
    "B738":   dict(econ_seats=189,bus_seats=0,  mtow_kg=79000, cargo_cap_kg=0, fuel_burn_kg_per_bh=2600, maint_per_bh=1000, crew_per_bh=1300, ownership_per_bh=900, price_usd=45e6, annual_util_bh=2300, range_km=5400, category="Narrowbody", src="FAA NB<165k; EUROCONTROL 737NG $4,337/fh; burn published"),
    "B38M":   dict(econ_seats=189,bus_seats=0,  mtow_kg=82000, cargo_cap_kg=0, fuel_burn_kg_per_bh=2250, maint_per_bh=980, crew_per_bh=1300, ownership_per_bh=1300, price_usd=52e6, annual_util_bh=2300, range_km=6500, category="Narrowbody", src="FAA NB + MAX lease premium; burn published"),
    "B752":   dict(econ_seats=199,bus_seats=0,  mtow_kg=115000,cargo_cap_kg=2000, fuel_burn_kg_per_bh=3300, maint_per_bh=1100, crew_per_bh=1400, ownership_per_bh=600, price_usd=20e6, annual_util_bh=2800, range_km=7200, category="Narrowbody-LR", src="EUROCONTROL 757 $5,357/fh; old type low ownership; burn published"),
    # --- Comac (Jessica, 3 Jul 2026: needed for Asia routes). PROXY economics, flagged: no
    # published maintenance reserves and thin appraiser coverage, so maint/ownership anchor to
    # the A320/E190 families with an early-type support premium. Seats/MTOW/range published. ---
    "C919":   dict(econ_seats=156,bus_seats=8,  mtow_kg=77900, cargo_cap_kg=0, fuel_burn_kg_per_bh=2400, maint_per_bh=1100, crew_per_bh=1300, ownership_per_bh=1100, price_usd=50e6, annual_util_bh=2300, range_km=5500, category="Narrowbody", src="PROXY: A320-family anchors + early-type premium; LEAP-1C burn ~ceo level; ER seats/MTOW/range published; value well below $99m list"),
    "C909":   dict(econ_seats=90, bus_seats=0,  mtow_kg=43500, cargo_cap_kg=0, fuel_burn_kg_per_bh=2204, maint_per_bh=600, crew_per_bh=713, ownership_per_bh=500, price_usd=20e6, annual_util_bh=1708, range_km=3300, category="Regional", src="PROXY (ARJ21-700, renamed C909): E190 anchors + premium; CF34-10A burn ~E190+13%, carried through the E190 correction of 10 Aug 2026; seats/MTOW/range published"),
    # --- Widebody / long-haul. RE-ANCHORED: Belobaba A330-200 2013 non-fuel ~$3,053 (x1.4
    # infl ~$4,300) => prior crew/ownership were too high; A330 maint $964 from LHLCC 2015 ---
    "B763":   dict(econ_seats=245,bus_seats=24, mtow_kg=186000,cargo_cap_kg=10000, fuel_burn_kg_per_bh=5200, maint_per_bh=1600, crew_per_bh=1500, ownership_per_bh=900, price_usd=30e6, annual_util_bh=3500, range_km=11000, category="Widebody", src="EUROCONTROL 767 $6,675/fh; old type low ownership; burn published"),
    "A333":   dict(econ_seats=277,bus_seats=30, mtow_kg=233000,cargo_cap_kg=15000, fuel_burn_kg_per_bh=6000, maint_per_bh=964, crew_per_bh=1500, ownership_per_bh=1800, price_usd=90e6, annual_util_bh=3800, range_km=11300, category="Widebody", src="LHLCC 2015 (fuel $3,012/maint $964 per BH); Belobaba A330 non-fuel anchor; burn published"),
    "A339":   dict(econ_seats=287,bus_seats=30, mtow_kg=251000,cargo_cap_kg=15000, fuel_burn_kg_per_bh=5400, maint_per_bh=1100, crew_per_bh=1600, ownership_per_bh=2600, price_usd=110e6, annual_util_bh=4000, range_km=13300, category="Widebody", src="A330 anchor + neo lease (IBA ~$800-900k/mo); burn published"),
    "B788":   dict(econ_seats=242,bus_seats=28, mtow_kg=228000,cargo_cap_kg=12000, fuel_burn_kg_per_bh=5000, maint_per_bh=950, crew_per_bh=1550, ownership_per_bh=2200, price_usd=115e6, annual_util_bh=4200, range_km=13500, category="Widebody", src="EUROCONTROL 787 $7,184/fh; Belobaba WB non-fuel anchor; burn published"),
    "B789":   dict(econ_seats=290,bus_seats=30, mtow_kg=254000,cargo_cap_kg=14000, fuel_burn_kg_per_bh=5400, maint_per_bh=1050, crew_per_bh=1650, ownership_per_bh=2500, price_usd=135e6, annual_util_bh=4300, range_km=14000, category="Widebody", src="EUROCONTROL 787 + IBA lease ~$1.0m/mo; burn published"),
    "A359":   dict(econ_seats=300,bus_seats=36, mtow_kg=280000,cargo_cap_kg=16000, fuel_burn_kg_per_bh=5800, maint_per_bh=1200, crew_per_bh=1700, ownership_per_bh=2700, price_usd=150e6, annual_util_bh=4400, range_km=15000, category="Widebody", src="A350 newest; FAA WB + lease; burn published"),
    "B77W":   dict(econ_seats=340,bus_seats=40, mtow_kg=351000,cargo_cap_kg=20000, fuel_burn_kg_per_bh=7500, maint_per_bh=1900, crew_per_bh=2000, ownership_per_bh=1900, price_usd=90e6, annual_util_bh=4500, range_km=13600, category="Widebody", src="EUROCONTROL 777 $9,507/fh; large WB; burn published"),

    # ---------------------------------------------------------------- added 10 August 2026
    # Seventeen types the 2025 schedule flies and this table did not hold, so the optimiser could not
    # offer them: EVA operates the 787-10 on sectors of SJC-TPE length and it was invisible.
    #
    # WHAT IS MEASURED AND WHAT IS NOT, per row, and the src field says so for each:
    #   seats and premium seats  OAG 2025 median for the type, measured
    #   fuel burn                US DOT Form 41 P-5.2 2023 over T-100 measured block ratio where the
    #                            sample supports it, else Aircraft Commerce published block
    #   range and MTOW           manufacturer documents and type certificate data sheets
    #   maint, crew, ownership, price, utilisation
    #                            SCALED from the nearest held type by MTOW inside the same category.
    #                            NOT SOURCED. Ownership in particular is unpublishable for every one
    #                            of these: OWNERSHIP_PROVENANCE below returns "none" for them, the
    #                            payload flags it, and the P&L reports contribution before ownership
    #                            with a break-even rather than asserting a lease rate.
    #
    # TWO FORM 41 ROWS WERE REJECTED after checking who files them. The 747-8 row is UPS, Polar and
    # Atlas on 204 hours, which is the FREIGHTER, and the 787-10 row is United alone on 101 hours and
    # reads below the 787-9, which a heavier stretch does not do. Both use the Aircraft Commerce
    # passenger figure instead. That is the same sample-size trap the E190 sprang earlier the same day.
    "A388":   dict(econ_seats=427,bus_seats=90, mtow_kg=575000,cargo_cap_kg=3890, fuel_burn_kg_per_bh=12019, maint_per_bh=3113, crew_per_bh=3276, ownership_per_bh=3113, price_usd=147.436e6, annual_util_bh=4500, range_km=14800, category="Widebody", src="seats OAG 2025 median; burn Aircraft Commerce block, flight-planned; range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from B77W on the MTOW ratio, not sourced"),
    "B748":   dict(econ_seats=276,bus_seats=88, mtow_kg=447696,cargo_cap_kg=16920, fuel_burn_kg_per_bh=10089, maint_per_bh=2423, crew_per_bh=2551, ownership_per_bh=2423, price_usd=114.794e6, annual_util_bh=4500, range_km=14310, category="Widebody", src="seats OAG 2025 median; burn Aircraft Commerce Issue 113 passenger 747-8, 9,300 to 10,878 block, midpoint. The Form 41 2023 row is UPS, Polar and Atlas, i.e. FREIGHTERS, on 204 hours: different empty weight, zero-fuel weight and mission, so not usable here; range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from B77W on the MTOW ratio, not sourced"),
    "B773":   dict(econ_seats=351,bus_seats=42, mtow_kg=299370,cargo_cap_kg=0, fuel_burn_kg_per_bh=6683, maint_per_bh=1283, crew_per_bh=1818, ownership_per_bh=2887, price_usd=160.377e6, annual_util_bh=4400, range_km=11140, category="Widebody", src="seats OAG 2025 median; burn Aircraft Commerce block, flight-planned; range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from A359 on the MTOW ratio, not sourced"),
    "B772":   dict(econ_seats=239,bus_seats=43, mtow_kg=297556,cargo_cap_kg=0, fuel_burn_kg_per_bh=6046, maint_per_bh=1275, crew_per_bh=1807, ownership_per_bh=2869, price_usd=159.405e6, annual_util_bh=4400, range_km=13084, category="Widebody", src="seats OAG 2025 median; burn Form 41 2023 + T-100 block ratio; range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from A359 on the MTOW ratio, not sourced"),
    "B781":   dict(econ_seats=280,bus_seats=38, mtow_kg=254011,cargo_cap_kg=13000, fuel_burn_kg_per_bh=5500, maint_per_bh=1050, crew_per_bh=1650, ownership_per_bh=2500, price_usd=135.006e6, annual_util_bh=4300, range_km=11750, category="Widebody", src="seats OAG 2025 median; burn Aircraft Commerce Issue 121, GEnx-1B at 337 seats, 5,199 to 5,552 block. The Form 41 row is United alone on 101 hours and reads BELOW the 787-9, which a heavier stretch does not do; range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from B789 on the MTOW ratio, not sourced"),
    "A332":   dict(econ_seats=244,bus_seats=20, mtow_kg=242000,cargo_cap_kg=0, fuel_burn_kg_per_bh=5345, maint_per_bh=1001, crew_per_bh=1558, ownership_per_bh=1870, price_usd=93.4764e6, annual_util_bh=3800, range_km=13450, category="Widebody", src="seats OAG 2025 median; burn Form 41 2023 + T-100 block ratio; range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from A333 on the MTOW ratio, not sourced"),
    "B764":   dict(econ_seats=184,bus_seats=54, mtow_kg=204116,cargo_cap_kg=0, fuel_burn_kg_per_bh=4909, maint_per_bh=1756, crew_per_bh=1646, ownership_per_bh=988, price_usd=32.9219e6, annual_util_bh=3500, range_km=10371, category="Widebody", src="seats OAG 2025 median; burn Form 41 2023 + T-100 block ratio (thin: 146 hours, Delta and United; corroborated by Aircraft Commerce at 5,000); range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from B763 on the MTOW ratio, not sourced"),
    "B753":   dict(econ_seats=210,bus_seats=24, mtow_kg=122449,cargo_cap_kg=0, fuel_burn_kg_per_bh=3343, maint_per_bh=1325, crew_per_bh=1742, ownership_per_bh=1641, price_usd=69.4298e6, annual_util_bh=2300, range_km=6420, category="Narrowbody", src="seats OAG 2025 median; burn Form 41 2023 + T-100 block ratio (thin: 116 hours, United and Delta; Aircraft Commerce gives 3,573 to 4,101); range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from A21N on the MTOW ratio, not sourced"),
    "B39M":   dict(econ_seats=163,bus_seats=16, mtow_kg=88314,cargo_cap_kg=0, fuel_burn_kg_per_bh=2011, maint_per_bh=1039, crew_per_bh=1303, ownership_per_bh=897, price_usd=47.2267e6, annual_util_bh=2300, range_km=6110, category="Narrowbody", src="seats OAG 2025 median; burn Form 41 2023 + T-100 block ratio; range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from A321 on the MTOW ratio, not sourced"),
    "B739":   dict(econ_seats=161,bus_seats=19, mtow_kg=85139,cargo_cap_kg=4877, fuel_burn_kg_per_bh=2397, maint_per_bh=1018, crew_per_bh=1350, ownership_per_bh=1350, price_usd=53.9906e6, annual_util_bh=2300, range_km=4750, category="Narrowbody", src="seats OAG 2025 median; burn Form 41 2023 + T-100 block ratio; range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from B38M on the MTOW ratio, not sourced"),
    "A223":   dict(econ_seats=140,bus_seats=0, mtow_kg=70896,cargo_cap_kg=5052, fuel_burn_kg_per_bh=2191, maint_per_bh=845, crew_per_bh=1080, ownership_per_bh=657, price_usd=32.8657e6, annual_util_bh=2300, range_km=6300, category="Narrowbody", src="seats OAG 2025 median; burn Form 41 2023 + T-100 block ratio; range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from A319 on the MTOW ratio, not sourced"),
    "B737":   dict(econ_seats=137,bus_seats=2, mtow_kg=70080,cargo_cap_kg=5181, fuel_burn_kg_per_bh=2176, maint_per_bh=835, crew_per_bh=1067, ownership_per_bh=650, price_usd=32.4874e6, annual_util_bh=2300, range_km=6037, category="Narrowbody", src="seats OAG 2025 median; burn Form 41 2023 + T-100 block ratio; range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from A319 on the MTOW ratio, not sourced"),
    "B734":   dict(econ_seats=165,bus_seats=0, mtow_kg=68039,cargo_cap_kg=0, fuel_burn_kg_per_bh=2494, maint_per_bh=811, crew_per_bh=1036, ownership_per_bh=631, price_usd=31.5413e6, annual_util_bh=2300, range_km=3889, category="Narrowbody", src="seats OAG 2025 median; burn Aircraft Commerce block, flight-planned; range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from A319 on the MTOW ratio, not sourced"),
    "A221":   dict(econ_seats=97,bus_seats=12, mtow_kg=63730,cargo_cap_kg=3760, fuel_burn_kg_per_bh=1711, maint_per_bh=760, crew_per_bh=971, ownership_per_bh=591, price_usd=29.5437e6, annual_util_bh=2300, range_km=6700, category="Narrowbody", src="seats OAG 2025 median; burn Form 41 2023 + T-100 block ratio; range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from A319 on the MTOW ratio, not sourced"),
    "B733":   dict(econ_seats=143,bus_seats=0, mtow_kg=63276,cargo_cap_kg=0, fuel_burn_kg_per_bh=2325, maint_per_bh=754, crew_per_bh=964, ownership_per_bh=587, price_usd=29.3332e6, annual_util_bh=2300, range_km=2963, category="Narrowbody", src="seats OAG 2025 median; burn Aircraft Commerce block, flight-planned; range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from A319 on the MTOW ratio, not sourced"),
    "B735":   dict(econ_seats=152,bus_seats=8, mtow_kg=61689,cargo_cap_kg=4460, fuel_burn_kg_per_bh=2186, maint_per_bh=735, crew_per_bh=940, ownership_per_bh=572, price_usd=28.5975e6, annual_util_bh=2300, range_km=2963, category="Narrowbody", src="seats OAG 2025 median; burn Aircraft Commerce block, flight-planned; range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from A319 on the MTOW ratio, not sourced"),
    "B717":   dict(econ_seats=98,bus_seats=12, mtow_kg=54885,cargo_cap_kg=0, fuel_burn_kg_per_bh=2104, maint_per_bh=654, crew_per_bh=836, ownership_per_bh=509, price_usd=25.4434e6, annual_util_bh=2300, range_km=3815, category="Narrowbody", src="seats OAG 2025 median; burn Form 41 2023 + T-100 block ratio; range and MTOW researched 10 Aug 2026; maint, crew, ownership, price and utilisation SCALED from A319 on the MTOW ratio, not sourced"),
}

# ----------------------------------------------------- regional jet fuel burn, corrected 10 Aug 2026
# The regional jet burns above were 0.51 to 0.75 of what US operators actually burned, and the fault
# went unnoticed because the whole band was wrong together: an internal consistency check across the
# module agreed with itself. It was found by going outside, to reported actuals.
#
# METHOD. US DOT Form 41 Schedule P-5.2 for calendar 2023 reports fuel ISSUED and AIRBORNE hours by
# aircraft type. Fuel over hours at 3.039 kg per US gallon gives a per-airborne-hour rate; T-100 for
# the same year gives air time over ramp-to-ramp time by the same aircraft type code, which converts
# it to a per-block-hour rate without assuming a taxi allowance. Measured ratios run 0.65 to 0.75 on
# the regionals against 0.88 to 0.92 on the widebodies, which is the taxi share of a short sector.
#
# THE SAME TEST VALIDATES EVERYTHING ELSE. Every mainline narrowbody and widebody in this table sits
# between 0.99 and 1.13 of reported actual. The fault was confined to the regional jets.
#
# SAMPLE SIZE MATTERS AND CAUGHT US OUT ONCE. The first pass took each type's own Form 41 row. The
# E190's row is JetBlue alone on 102 airborne hours, in the year it retired the fleet, and reads
# 2,916 kg per airborne hour against a five-carrier E175 cluster spanning 1,828 to 2,133. An aircraft
# a third heavier than an E175 does not burn 46% more, so that row is not a measurement of the type.
# The E190 is therefore SCALED from the well-sampled E170 and E175 rows and lands at 1,950 block,
# which Aircraft Commerce Issue 64 independently brackets at 1,923 to 1,980. John caught this by
# holding the result against a route he knows is flown: read a row with fewer than a few hundred
# hours or a single carrier as an indication, not a figure.
#
# NOT CORRECTED, and deliberately. ATR72, DH8D and SF34 are turboprops with no US Form 41 rows, so
# there is no measurement. Their burns come from manufacturer published block figures rather than
# from the worked example and the FAA category that produced the regional jet errors, and ATR's own
# factsheet gives block fuel paired with block time, so they do not share the fault. They remain
# unverified against reported actuals and should be checked if a European source ever allows it.
#
# WHAT THIS DOES TO A ROUTE. It roughly doubles the fuel line on a regional jet route. Every regional
# P&L the tool produced before this date understated fuel by that much.

# ----------------------------------------------------- where the ownership leg comes from
# Added 10 August 2026. Four independent searches, three of them external, failed to find a single
# current type-and-age market value or lease rate in free public form; appraiser licences permit
# internal use but not publication. So Avia cannot defend an ownership figure in public, and must not
# be the only public source of one.
#
# This records which of the ownership figures above rest on a citable source and which do not, from
# the June 2026 assumptions register. It exists so a client-facing renderer can suppress an assumed
# figure rather than print it silently, and so nobody has to guess later.
#
#   citable   an appraiser or manufacturer financing publication names the value or lease rate
#   proxy     interpolated from a neighbouring type in the register, no direct source
#   none      no entry in the register at all; the figure's origin is not recorded anywhere
OWNERSHIP_PROVENANCE = {
    "A320": "citable", "A20N": "citable", "A21N": "citable", "A333": "citable",
    "A339": "citable", "A359": "citable", "B789": "citable", "B38M": "citable",
    "A319": "proxy", "A321": "proxy", "A21X": "proxy",
}
for _k in AIRCRAFT:
    OWNERSHIP_PROVENANCE.setdefault(_k, "none")
del _k


def ownership_is_publishable(code):
    """True only where the ownership leg rests on a named public source. Everything else is an Avia
    assumption and belongs in a break-even statement rather than on a slide."""
    return OWNERSHIP_PROVENANCE.get(code) == "citable"

# ----------------------------------------------------- sector-aware maintenance
# HEAVY maintenance reserve, $/flight-hour, by Airbus type and sector length (FH/FC).
# Source: Airbus "2024-2025 Maintenance Reserves booklet, Excel tool v2.1" (Egnyte
# 02 Knowledge / Industry Reports / Airbus / Briefings / Nov 2024). The booklet's
# six-component reserve model (airframe C/D checks 6/12/18/24-yr, engine shop visit
# + LLP, APU, landing gear, thrust reverser) was re-implemented and validated against
# the workbook's own cached A321neo outputs to within rounding (engine 31.8 vs 32 $/eng-FH;
# 6-yr check 302,886 vs 302,909; 12-yr 563,742 vs 563,718). Each curve is the mean
# reserve $/FH across the type's engine options at Airbus's assumed annual utilisation.
# These are HEAVY maintenance only (C/D + overhauls + LLP); they EXCLUDE A/B line
# maintenance, transit/daily checks and defect rectification. The booklet states the
# values are indicative and exclude any commercial OEM discount. Generated 27 June 2026.
MAINT_HEAVY_RESERVE_PER_FH = {
    'A319': {1: 1287.5, 1.5: 981.1, 2: 823.0, 2.5: 733.3, 3: 673.2, 3.5: 626.2, 4: 587.4, 4.5: 563.4, 5: 543.2},
    'A320': {1: 1325.6, 1.5: 1011.3, 2: 849.6, 2.5: 757.9, 3: 696.7, 3.5: 648.8, 4: 609.1, 4.5: 584.1, 5: 563.0},
    'A20N': {1: 1354.5, 1.5: 970.5, 2: 781.4, 2.5: 688.6, 3: 631.2, 3.5: 592.0, 4: 561.0, 4.5: 541.0, 5: 524.8},
    'A321': {1: 1484.2, 1.5: 1146.5, 2: 964.9, 2.5: 869.3, 3: 803.7, 3.5: 751.2, 4: 708.0, 4.5: 680.4, 5: 656.4},
    'A21N': {1: 1825.3, 1.5: 1300.2, 2: 1059.2, 2.5: 957.5, 3: 879.2, 3.5: 817.0, 4: 763.6, 4.5: 739.3, 5: 719.4},
    'A21X': {3: 917.3, 3.5: 846.3, 4: 786.6, 4.5: 755.0, 5: 728.4, 5.5: 705.6, 6: 685.7, 6.5: 674.5, 7: 665.0, 7.5: 657.0},
    'A333': {2: 2674.1, 3: 1820.2, 4: 1441.1, 5: 1259.6, 6: 1149.6, 7: 1087.2, 8: 1035.5, 9: 996.6, 10: 962.6, 12: 908.3},
    'A339': {2: 3440.4, 3: 2567.6, 4: 2055.4, 5: 1716.5, 6: 1458.8, 7: 1272.9, 8: 1184.9, 9: 1155.0, 10: 1130.0, 12: 1080.5},
    'A359': {4: 2437.5, 5: 2024.5, 6: 1706.1, 7: 1477.9, 8: 1374.8, 9: 1338.9, 10: 1308.6, 12: 1247.4},
}

# Heavy maintenance (the reserve above) as a share of TOTAL maintenance DMC. The
# remainder is A/B line maintenance, transit/daily checks and defect rectification,
# which the Airbus reserve excludes. Total maint $/FH = heavy reserve / this share.
# Default 0.78 (line maintenance ~22% of DMC); tunable per John's operating judgement.
MAINT_HEAVY_SHARE_OF_DMC = 0.78


def _interp_reserve(curve: dict, sector_fh: float) -> float:
    """Linear interpolation of heavy-reserve $/FH against sector (FH/FC); clamps at
    the ends of the booklet's sector grid (reserve flattens at long sector)."""
    xs = sorted(curve)
    if sector_fh <= xs[0]:
        return curve[xs[0]]
    if sector_fh >= xs[-1]:
        return curve[xs[-1]]
    for i in range(1, len(xs)):
        if sector_fh <= xs[i]:
            x0, x1 = xs[i - 1], xs[i]
            t = (sector_fh - x0) / (x1 - x0)
            return curve[x0] + t * (curve[x1] - curve[x0])
    return curve[xs[-1]]


def maintenance_total_per_fh(aircraft: str, sector_fh: float,
                             heavy_share: float = MAINT_HEAVY_SHARE_OF_DMC):
    """Total maintenance $/flight-hour for an Airbus type at a given sector length,
    grossed up from the Airbus heavy-reserve curve by the heavy share of DMC.
    Returns None for types without an Airbus reserve curve (caller falls back to
    the block-hour anchor)."""
    curve = MAINT_HEAVY_RESERVE_PER_FH.get(aircraft)
    if not curve:
        return None
    return _interp_reserve(curve, sector_fh) / heavy_share


# --------------------------------------------------- ownership (cost of capital)
# Ownership is the user cost of capital of the aircraft: economic depreciation plus
# the cost of capital on the asset. It applies to owned AND leased aircraft, so it is
# anchored on aircraft VALUE and the appraiser LEASE rate (the market's bundled price
# of exactly that capital cost), not on lease alone. Per the DVB/Ascend lease-rate-
# factor decomposition, a market lease = economic depreciation (~50%) + cost of debt
# (~25%) + SG&A (~6%) + lessor margin (~17%). So the OWNER's economic cost = the
# market lease stripped of the lessor's load (SG&A + margin), and the LEASED cost =
# the full market lease. A fleet blends the two (only ~half the global fleet is leased).
#
# Lease rates ($'000/month, new, full-life) read from current appraiser charts:
#   Airbus Appraiser & Investor Forum, Dec 2025 (5-appraiser average); Boeing Aircraft
#   Financing Outlook, Mar 2025. Values are representative current points off the charts
#   (not to-the-dollar). ceo/older-gen and A321XLR are flagged proxies. Generated 27 June 2026.
OWNERSHIP_LEASE_NEW_USD000_PM = {
    # Firmed from the appraiser chart pages (Airbus Dec 2025 / Boeing 1H2024 average lines):
    # A20N/A21N/A339/A359 = new full-life; A320/A333 = 10-yr half-life (no new ceo traded);
    # A339 900 is appraiser average (market feedback ~1,050); A359 1,150 average (likely ~1,400).
    # A319/A321/A21X are proxies (no own chart): A319 below A320ceo, A321 above, A21X = A321neo + XLR premium.
    'A319': 190, 'A320': 250, 'A20N': 400, 'A321': 290, 'A21N': 450, 'A21X': 500,
    'A333': 440, 'A339': 900, 'A359': 1150, 'B789': 1000, 'B38M': 400,
}
# Appraiser new market value ($M) - the value anchor behind the lease (cross-check / framing).
OWNERSHIP_VALUE_NEW_USDM = {
    'A319': 25, 'A320': 45, 'A20N': 53, 'A321': 50, 'A21N': 65, 'A21X': 72,
    'A333': 90, 'A339': 110, 'A359': 158, 'B789': 150, 'B38M': 55,
}
# Lease/value retention by aircraft age (years). New=1.0; lease roughly halves over
# ~10-12 years (Airbus deck: A320neo new ~$400K/mo vs A320ceo 10yr ~$220K/mo).
LEASE_AGE_RETENTION = {0: 1.0, 5: 0.80, 10: 0.55, 15: 0.42, 20: 0.32, 25: 0.24}
OWNERSHIP_LESSOR_LOAD = 0.20      # lessor SG&A + margin on top of owner cost (DVB/Ascend LRF, 2018)
OWNED_LEASE_SHARE = 0.53          # share of fleet LEASED (Cirium/CAPA 2025: "just over half", 53%)

# Utilisation is driven by SECTOR LENGTH, not aircraft body. Airbus (A&I Forum, April 2026,
# FR24 actuals) shows annual block hours rising with sector length and plateauing: short sectors
# waste the day on turns, long sectors fly near-continuously (capped ~14-16 hr/day by crew/maint/
# curfew). This is why the A321XLR (long sectors) reaches ~4,900 FH/yr, the highest single-aisle,
# near widebody levels, despite being a narrowbody. Per-type 2025 actuals that anchor the curve
# (Iberia/Aer Lingus, FH/yr): A319 2,237, A320 ~3,100, A321 3,432, A321LR ~4,860, A321XLR ~4,900,
# A330 ~5,300, A350 5,710. Curve below is representative BLOCK hours/yr vs sector block-hours/leg
# (Airbus shape, scaled to Cirium all-operator levels ~3,400 NB / ~4,950 WB average).
UTIL_SECTOR_CURVE_BH = {1.0: 2600, 1.5: 3000, 2.0: 3300, 3.0: 3800, 4.0: 4200,
                        5.0: 4500, 7.0: 4900, 10.0: 5300, 14.0: 5600}
# Airline business model lifts/lowers util at a given sector (turn-time efficiency, asset-sweat):
# ULCC (Ryanair/Wizz fast turns) highest, regional lowest.
UTIL_AIRLINE_MULT = {'ULCC': 1.10, 'LCC': 1.05, 'FSC': 1.00, 'Charter': 1.00, 'Regional': 0.88}

# Crew cost per block hour by airline business model. The per-type crew_per_bh is the
# FULL-SERVICE baseline (FSC = 1.00, so the validated E190/Maverick reference is unchanged).
# A ULCC pays lower scales, flies a denser single-class cabin with a leaner cabin-crew
# complement and no long-haul allowances, so its crew cost per block hour is well below an
# FSC's; LCC between; regional and charter modestly below. (Productivity, i.e. annual block
# hours, is handled separately in utilisation, so this multiplier is the pay/complement
# difference, not the hours difference.) Anchored on airline staff-cost-per-block-hour
# comparisons (Ryanair/Wizz vs IAG/Lufthansa); judgement until the pre-launch citation sweep.
CREW_AIRLINE_MULT = {'ULCC': 0.62, 'LCC': 0.80, 'FSC': 1.00, 'Regional': 0.88, 'Charter': 0.92}


def _interp_retention(age: float) -> float:
    pts = sorted(LEASE_AGE_RETENTION)
    if age <= pts[0]:
        return LEASE_AGE_RETENTION[pts[0]]
    if age >= pts[-1]:
        return LEASE_AGE_RETENTION[pts[-1]]
    for i in range(1, len(pts)):
        if age <= pts[i]:
            a0, a1 = pts[i - 1], pts[i]
            t = (age - a0) / (a1 - a0)
            return LEASE_AGE_RETENTION[a0] + t * (LEASE_AGE_RETENTION[a1] - LEASE_AGE_RETENTION[a0])
    return LEASE_AGE_RETENTION[pts[-1]]


def util_bh(airline_type: str, sector_bh: float) -> float:
    """Annual block-hour utilisation from sector length (block hours/leg) and airline type.
    Interpolates the Airbus-anchored sector curve, then applies the airline-type multiplier."""
    pts = sorted(UTIL_SECTOR_CURVE_BH)
    if sector_bh <= pts[0]:
        base = UTIL_SECTOR_CURVE_BH[pts[0]]
    elif sector_bh >= pts[-1]:
        base = UTIL_SECTOR_CURVE_BH[pts[-1]]
    else:
        base = None
        for i in range(1, len(pts)):
            if sector_bh <= pts[i]:
                x0, x1 = pts[i - 1], pts[i]
                t = (sector_bh - x0) / (x1 - x0)
                base = UTIL_SECTOR_CURVE_BH[x0] + t * (UTIL_SECTOR_CURVE_BH[x1] - UTIL_SECTOR_CURVE_BH[x0])
                break
    return base * UTIL_AIRLINE_MULT.get(airline_type, 1.0)


def ownership_per_bh(aircraft: str, airline_type: str = 'FSC', aircraft_age: float = 0.0,
                     sector_bh: float = 2.0, lease_share: float = OWNED_LEASE_SHARE,
                     lessor_load: float = OWNERSHIP_LESSOR_LOAD):
    """Blended ownership $/block-hour from appraiser lease/value, by sector-driven utilisation,
    airline type and aircraft age. Returns (None, None) for types without appraiser data so the
    caller falls back to the type's hand-set ownership_per_bh."""
    lease_new = OWNERSHIP_LEASE_NEW_USD000_PM.get(aircraft)
    if lease_new is None:
        return None, None
    lease_month = lease_new * 1000.0 * _interp_retention(aircraft_age)   # $/month at this age
    owned_month = lease_month / (1 + lessor_load)                        # owner economic cost
    blended_month = lease_share * lease_month + (1 - lease_share) * owned_month
    util = util_bh(airline_type, sector_bh)
    return blended_month * 12.0 / util, util


# ---------------------------------------------------------------- airport DB
# landing per turnaround (MTOW-based, seeded); pax charge per pax; ground handling
# per turnaround; APD/charges recovery per pax. Country -> en-route unit rate.
AIRPORTS: Dict[str, dict] = {
    "LCY": dict(country="UK", landing_per_turn=1072.0, pax_charge_per_pax=5.378,
                ground_handling_per_turn=1905.0, recovery_per_pax=21.42),
    "EDI": dict(country="UK", landing_per_turn=278.0, pax_charge_per_pax=6.722,
                ground_handling_per_turn=0.0, recovery_per_pax=0.0),
    # indicative (not from a validated source) - for long-haul sanity / Genoa illustration
    "GOA": dict(country="Italy", landing_per_turn=1500.0, pax_charge_per_pax=22.0,
                ground_handling_per_turn=2500.0, recovery_per_pax=45.0),
    "JFK": dict(country="US", landing_per_turn=2800.0, pax_charge_per_pax=28.0,
                ground_handling_per_turn=3200.0, recovery_per_pax=0.0),
    # indicative (not from a validated source) - Caribbean winter-sun illustration (Punta Cana)
    "PUJ": dict(country="Caribbean", landing_per_turn=1300.0, pax_charge_per_pax=25.0,
                ground_handling_per_turn=2000.0, recovery_per_pax=0.0),
}

ENROUTE_RATE_USD = {"UK": 73.20, "France": 70.11, "Switzerland": 119.11,
                    "Germany": 90.26, "Greece": 38.49, "Spain": 71.80,
                    "Netherlands": 66.68, "Denmark": 471.91, "Ireland": 29.71,
                    "Portugal": 37.24, "Italy": 78.91, "Belgium": 70.79,
                    "Luxembourg": 70.79, "US": 20.00}
NM_TO_KM = 1.852


def enroute_charge(mtow_kg, distance_nm, airspace: Dict[str, float]):
    """Maverick formula per leg: rate x sqrt(MTOW/50000) x (km-40)/100, summed
    over each country's airspace share. airspace = {country: fraction}."""
    km = distance_nm * NM_TO_KM
    import math
    factor = math.sqrt(mtow_kg / 50000.0) * (km - 40) / 100.0
    return sum(ENROUTE_RATE_USD.get(c, 0) * frac for c, frac in airspace.items()) * factor


@dataclass
class Incentive:
    """Home-airport route-development support. waiver_pct discounts the HOME
    airport's aeronautical charges; support_per_turn is marketing/route funding
    paid to the airline per turnaround. Both improve the airline's route P&L -
    the airport is buying viability. ramp_years optionally tapers the package."""
    home: str = ""               # which airport code is offering support
    waiver_pct: float = 0.0      # 0..1 of home landing+pax+handling charges waived
    support_per_turn: float = 0.0


@dataclass
class RoutePnL:
    airline: str
    aircraft: str
    origin: str
    dest: str
    distance_nm: float
    block_min_oneway: float
    econ_lf: float
    bus_lf: float
    econ_fare_ow: float
    bus_fare_ow: float
    fuel_price_usd_kg: float = 0.68
    cargo_yield_per_tkm: float = 0.40
    cargo_lf: float = 0.70
    overhead_pct: float = 0.05
    sales_pct: float = 0.05
    nav_override: Optional[float] = None
    airspace: Dict[str, float] = field(default_factory=dict)
    # --- airport charges as a per-route INPUT layer (declared, overridable, inflated) ---
    charge_base_year: int = 2025      # vintage of the AIRPORTS table values
    model_year: int = 2026            # year to inflate charges to
    charge_inflation: float = 0.03    # annual airport-charge inflation, declared
    origin_charges: Optional[dict] = None   # analyst override (e.g. from RDC), current-year
    dest_charges: Optional[dict] = None
    incentive: Optional[Incentive] = None
    # --- sector-aware maintenance (Airbus types) ---
    taxi_min_oneway: float = 15.0           # block - taxi = flight time; sector = flight hrs/leg
    maint_heavy_share: float = MAINT_HEAVY_SHARE_OF_DMC  # heavy reserve as share of total DMC
    # --- ownership (cost of capital), by airline type + aircraft age ---
    airline_type: str = "FSC"               # ULCC / LCC / FSC / Regional / Charter -> utilisation
    aircraft_age: float = 0.0               # years; scales lease/value down its age curve
    lease_share: float = OWNED_LEASE_SHARE  # share of fleet leased (rest owned); tunable
    # --- airline-specific FIXED-COST overrides (Expert view): set the actual carrier's numbers instead of the
    # carrier-type defaults. Any left None fall back to the modelled/type value, so this is purely additive.
    ownership_per_bh_override: Optional[float] = None   # $/block-hour ownership or lease, replaces the model
    crew_per_bh_override: Optional[float] = None        # $/block-hour crew, replaces the type baseline x mult
    annual_util_bh_override: Optional[float] = None     # annual block hours, drives the insurance/ownership util
    # --- Form 41 cost calibration (optional): anchor generic cost to the carrier's filed CASM ---
    casm_benchmark_c: Optional[float] = None      # carrier system CASM, US cents/ASK (Form 41 + T1)
    carrier_avg_stage_km: Optional[float] = None  # carrier avg stage length km, for the stage adjustment

    def _charges(self, code, override):
        """Resolved airport charges: override (current-year, e.g. RDC) wins;
        else the AIRPORTS table value inflated from charge_base_year to model_year."""
        if override is not None:
            c = dict(AIRPORTS.get(code, {})); c.update(override); return c, "input/RDC"
        base = AIRPORTS.get(code)
        if base is None:
            raise KeyError(f"No charges for {code}; pass {code} charges via origin_charges/dest_charges")
        infl = (1 + self.charge_inflation) ** (self.model_year - self.charge_base_year)
        c = {k: (v * infl if isinstance(v, (int, float)) and k.endswith(("per_turn", "per_pax")) else v)
             for k, v in base.items()}
        return c, f"table {self.charge_base_year}->{self.model_year} @ +{self.charge_inflation:.0%}/yr"

    def compute(self) -> dict:
        ac = AIRCRAFT[self.aircraft]
        o, o_src = self._charges(self.origin, self.origin_charges)
        d, d_src = self._charges(self.dest, self.dest_charges)
        bh = 2 * self.block_min_oneway / 60.0
        econ_ow = ac["econ_seats"] * self.econ_lf
        bus_ow = ac["bus_seats"] * self.bus_lf
        pax_turn = 2 * (econ_ow + bus_ow)
        # revenue
        econ_rev = 2 * econ_ow * self.econ_fare_ow
        bus_rev = 2 * bus_ow * self.bus_fare_ow
        cargo_rev = ac["cargo_cap_kg"]/1000.0 * self.cargo_lf * self.distance_nm*NM_TO_KM * self.cargo_yield_per_tkm * 2
        net_rev = econ_rev + bus_rev + cargo_rev
        charges_recovery = (o["recovery_per_pax"] + d["recovery_per_pax"]) * pax_turn
        gross_rev = net_rev + charges_recovery
        # variable
        fuel = ac["fuel_burn_kg_per_bh"] * bh * self.fuel_price_usd_kg
        # maintenance: sector-aware from the Airbus heavy-reserve curve for Airbus types
        # (charged on flight hours, where heavy maintenance actually accrues); all other
        # types stay on the block-hour anchor. flight time = block - taxi, per leg.
        flight_min_oneway = max(self.block_min_oneway - self.taxi_min_oneway, 10.0)
        sector_fh = flight_min_oneway / 60.0
        flight_h_turn = 2 * flight_min_oneway / 60.0
        maint_total_per_fh = maintenance_total_per_fh(self.aircraft, sector_fh, self.maint_heavy_share)
        if maint_total_per_fh is not None:
            maintenance = maint_total_per_fh * flight_h_turn
            heavy_resv = maint_total_per_fh * self.maint_heavy_share
            maint_basis = (f"Airbus MR 2024-25 sector-aware: {heavy_resv:.0f} $/FH heavy resv "
                           f"@ {sector_fh:.1f}h / {self.maint_heavy_share:.0%} share = {maint_total_per_fh:.0f} $/FH total")
        else:
            maintenance = ac["maint_per_bh"] * bh
            maint_basis = f"block-hour anchor: {ac['maint_per_bh']:.0f} $/BH"
        catering = 2.648 * pax_turn
        # airport charges per end (landing fixed per turnaround; per-pax x pax; handling per turn)
        def airport_charge(c):
            return c["landing_per_turn"], c["pax_charge_per_pax"] * pax_turn, c["ground_handling_per_turn"]
        o_land, o_pax, o_hand = airport_charge(o)
        d_land, d_pax, d_hand = airport_charge(d)
        # incentive: waive a % of the HOME airport's aeronautical charges
        waiver_value = 0.0
        inc = self.incentive
        if inc and inc.waiver_pct:
            if inc.home == self.origin:
                waiver_value = inc.waiver_pct * (o_land + o_pax + o_hand)
            elif inc.home == self.dest:
                waiver_value = inc.waiver_pct * (d_land + d_pax + d_hand)
        landing = o_land + d_land
        per_pax = o_pax + d_pax
        handling = o_hand + d_hand
        nav = self.nav_override if self.nav_override is not None else enroute_charge(ac["mtow_kg"], self.distance_nm, self.airspace)
        variable = fuel + maintenance + catering + landing + per_pax + nav + handling
        # direct fixed
        # ownership: value/lease-based cost of capital, blended owned+leased, by airline-type
        # util and aircraft age (covered types); else the type's hand-set $/block-hour anchor.
        sector_bh_leg = self.block_min_oneway / 60.0      # block hours per leg -> sector util
        if self.ownership_per_bh_override is not None:     # AIRLINE OVERRIDE wins
            ownership = self.ownership_per_bh_override * bh
            eff_util = self.annual_util_bh_override or ac["annual_util_bh"]
            own_basis = f"airline override: {self.ownership_per_bh_override:,.0f} $/BH"
        else:
            own_per_bh, own_util = ownership_per_bh(self.aircraft, self.airline_type,
                                                    self.aircraft_age, sector_bh_leg, self.lease_share)
            if own_per_bh is not None:
                ownership = own_per_bh * bh
                eff_util = self.annual_util_bh_override or own_util   # sector util, or the airline's override
                own_basis = (f"appraiser lease/value, {self.airline_type} util {own_util:,.0f} BH/yr "
                             f"@ {sector_bh_leg:.1f}h sector, age {self.aircraft_age:.0f}, "
                             f"{self.lease_share:.0%} leased = {own_per_bh:,.0f} $/BH")
            else:
                ownership = ac["ownership_per_bh"] * bh
                eff_util = self.annual_util_bh_override or ac["annual_util_bh"]
                own_basis = f"hand-set anchor: {ac['ownership_per_bh']:.0f} $/BH"
        insurance = 0.01 * ac["price_usd"] * (bh / eff_util)
        if self.crew_per_bh_override is not None:          # AIRLINE OVERRIDE wins
            crew = self.crew_per_bh_override * bh
            crew_basis = f"airline override: {self.crew_per_bh_override:,.0f} $/BH"
        else:
            crew_mult = CREW_AIRLINE_MULT.get(self.airline_type, 1.0)
            crew = ac["crew_per_bh"] * crew_mult * bh
            crew_basis = (f"{ac['crew_per_bh']:.0f} $/BH FSC baseline x {crew_mult:.2f} "
                          f"({self.airline_type}) = {ac['crew_per_bh'] * crew_mult:.0f} $/BH")
        direct_fixed = ownership + insurance + crew
        # indirect fixed
        admin = self.overhead_pct * net_rev
        sales = self.sales_pct * net_rev
        indirect_fixed = admin + sales
        total_cost_standalone = variable + direct_fixed + indirect_fixed
        # Form 41 calibration (optional): scale the generic cost to the carrier's FILED system CASM,
        # adjusted to this route's stage length (CASM rises on shorter sectors, so a system average
        # is stretched up on a short route and down on a long one). Inactive unless a benchmark is
        # supplied, so default behaviour is unchanged.
        casm_calibration = None; casm_target_c = None
        _ask0 = (ac["econ_seats"] + ac["bus_seats"]) * self.distance_nm * NM_TO_KM * 2
        if self.casm_benchmark_c and self.carrier_avg_stage_km and _ask0 > 0:
            _rk = max(self.distance_nm * NM_TO_KM, 50.0)
            casm_target_c = self.casm_benchmark_c * (self.carrier_avg_stage_km / _rk) ** 0.35
            _model_c = total_cost_standalone / _ask0 * 100.0
            if _model_c > 0:
                casm_calibration = casm_target_c / _model_c
                total_cost_standalone *= casm_calibration
        support = inc.support_per_turn if inc else 0.0
        incentive_value = waiver_value + support          # what the airport contributes
        # standalone = route on its own; with-incentive = airline's actual P&L given support
        profit_standalone = gross_rev - total_cost_standalone
        profit_with_incentive = profit_standalone + incentive_value
        seats = ac["econ_seats"] + ac["bus_seats"]
        cask = total_cost_standalone / (seats * self.distance_nm*NM_TO_KM * 2)
        pax_var = catering + per_pax + indirect_fixed
        fixed_costs = total_cost_standalone - pax_var
        denom = gross_rev - pax_var
        lam = fixed_costs / denom if denom else 0
        cur_lf = (econ_ow + bus_ow) / seats
        breakeven_lf = cur_lf * lam
        return dict(gross_rev=gross_rev, net_rev=net_rev, charges_recovery=charges_recovery,
                    econ_rev=econ_rev, bus_rev=bus_rev, cargo_rev=cargo_rev,
                    fuel=fuel, maintenance=maintenance, catering=catering,
                    landing=landing, per_pax=per_pax, nav=nav, handling=handling,
                    variable=variable, ownership=ownership, insurance=insurance, crew=crew,
                    direct_fixed=direct_fixed, admin=admin, sales=sales, indirect_fixed=indirect_fixed,
                    total_cost=total_cost_standalone, profit=profit_standalone, margin=profit_standalone/gross_rev,
                    casm_calibration=casm_calibration, casm_target_c=casm_target_c,
                    incentive_value=incentive_value, profit_with_incentive=profit_with_incentive,
                    margin_with_incentive=profit_with_incentive/gross_rev,
                    cost_per_seat=total_cost_standalone/seats, cask=cask, pax_turn=pax_turn,
                    breakeven_lf=breakeven_lf, load_factor=cur_lf,
                    origin_charge_basis=o_src, dest_charge_basis=d_src,
                    sector_fh=sector_fh, maint_basis=maint_basis, own_basis=own_basis,
                    crew_basis=crew_basis, eff_util=eff_util, block_hours_turn=bh)


# ----------------------------------------------------- report-wiring adapter
# Map the QSI RouteConfig.carrier_type label to an airline business model.
_AIRLINE_TYPE_MAP = {
    'full service': 'FSC', 'fsc': 'FSC', 'legacy': 'FSC', 'network': 'FSC',
    'low cost': 'LCC', 'low-cost': 'LCC', 'lcc': 'LCC',
    'ultra low cost': 'ULCC', 'ultra-low-cost': 'ULCC', 'ulcc': 'ULCC',
    'regional': 'Regional', 'charter': 'Charter', 'leisure': 'Charter',
}
# Best-effort map of common config aircraft strings to the economics AIRCRAFT keys.
_AIRCRAFT_CODE_MAP = {
    '787-800': 'B788', '787-8': 'B788', '787-9': 'B789', '789': 'B789', '788': 'B788',
    '737-800': 'B738', '737-8': 'B38M', '777-300er': 'B77W',
    'a320neo': 'A20N', 'a321neo': 'A21N', 'a321xlr': 'A21X', 'a330-900': 'A339',
    'a350-900': 'A359', 'a330-300': 'A333',
}


def airline_type_from_carrier(carrier_type) -> str:
    return _AIRLINE_TYPE_MAP.get(str(carrier_type or '').strip().lower(), 'FSC')


def map_aircraft_code(code) -> str:
    """Map a config aircraft string to an economics AIRCRAFT key (pass through if already valid)."""
    s = str(code or '').strip()
    if s in AIRCRAFT:
        return s
    return _AIRCRAFT_CODE_MAP.get(s.lower(), s)


def route_pnl_from_config(cfg, results=None, *, econ_fare_ow, bus_fare_ow,
                          aircraft=None, econ_lf=None, bus_lf=None,
                          airline_type=None, aircraft_age=0.0, **kw) -> 'RoutePnL':
    """Build a RoutePnL from a QSI RouteConfig (+ forecast results) and the economics
    inputs that live outside the QSI config (fares, airline type, age, charges). Block time
    comes from cfg.flight_time_hrs (+ taxi); load factor defaults to the forecast LF."""
    lf = results.get('load_factor') if isinstance(results, dict) else None
    block = (getattr(cfg, 'flight_time_hrs', 0) or 0) * 60 + 15.0     # flight + taxi -> block
    # optional: anchor cost to the carrier's Form 41 CASM (set AVIA_ECON_FORM41=1)
    import os as _os
    if _os.environ.get("AVIA_ECON_FORM41", "").strip().lower() in ("1", "true", "on", "yes"):
        try:
            import econ_benchmark
            _bm = econ_benchmark.carrier_casm(getattr(cfg, 'airline_code', None)
                                              or getattr(cfg, 'airline_name', None))
            if _bm:
                kw.setdefault('casm_benchmark_c', _bm[0]); kw.setdefault('carrier_avg_stage_km', _bm[1])
        except Exception:
            pass
    return RoutePnL(
        airline=getattr(cfg, 'airline_name', '') or getattr(cfg, 'airline_code', ''),
        aircraft=map_aircraft_code(aircraft or getattr(cfg, 'aircraft_type', '')),
        origin=getattr(cfg, 'home_airport_code', ''),
        dest=getattr(cfg, 'dest_airport_code', ''),
        distance_nm=getattr(cfg, 'distance_nm', 0) or 0,
        block_min_oneway=block,
        econ_lf=econ_lf if econ_lf is not None else (lf if lf is not None else 0.80),
        bus_lf=bus_lf if bus_lf is not None else (lf if lf is not None else 0.80),
        econ_fare_ow=econ_fare_ow, bus_fare_ow=bus_fare_ow,
        airline_type=airline_type or airline_type_from_carrier(getattr(cfg, 'carrier_type', None)),
        aircraft_age=aircraft_age, **kw)


# ----------------------------------------------------- annual / network P&L
@dataclass
class AnnualRoutePnL:
    """Annualise a turnaround RoutePnL: scale by the annual turnarounds operated, and
    report the fleet requirement. Everything in the turnaround P&L is per-turnaround and
    per-block-hour, so annual = turnaround x (frequency/week x operating weeks); the new
    network output is aircraft_required = annual block hours / the aircraft's annual util.
    Set econ_lf/bus_lf on the underlying RoutePnL to the OPERATING-SEASON load factors
    (a 30-week summer service should use the season's plateau, not the annual mean)."""
    route_pnl: 'RoutePnL'
    freq_per_week: float
    operating_weeks: float = 52.0

    def compute(self) -> dict:
        t = self.route_pnl.compute()
        n = self.freq_per_week * self.operating_weeks          # annual turnarounds (round trips)
        annual_bh = n * t['block_hours_turn']
        util = t.get('eff_util') or 1.0
        aircraft_frac = annual_bh / util if util else 0.0
        import math
        out = {'annual_turnarounds': n, 'annual_block_hours': annual_bh,
               'aircraft_required_fractional': aircraft_frac,
               'aircraft_required': int(math.ceil(aircraft_frac)) if aircraft_frac else 0,
               'annual_pax': t['pax_turn'] * n,
               'util_per_aircraft': util, 'margin': t['margin'],
               'margin_with_incentive': t['margin_with_incentive']}
        for k in ('gross_rev', 'net_rev', 'fuel', 'maintenance', 'variable', 'ownership',
                  'insurance', 'crew', 'direct_fixed', 'indirect_fixed', 'total_cost',
                  'profit', 'incentive_value', 'profit_with_incentive'):
            out['annual_' + k] = t[k] * n
        out['_turn'] = t
        return out


def network_pnl(items):
    """Aggregate a list of AnnualRoutePnL into a network P&L. Fleet is shared, so total
    aircraft = ceil(sum of fractional aircraft demand), not the sum of per-route ceilings."""
    import math
    res = {k: 0.0 for k in ('annual_gross_rev', 'annual_total_cost', 'annual_profit',
                            'annual_block_hours', 'annual_pax', 'aircraft_required_fractional')}
    rows = []
    for it in items:
        c = it.compute()
        for k in res:
            res[k] += c.get(k, 0.0)
        rows.append((it.route_pnl.origin, it.route_pnl.dest, it.route_pnl.aircraft, c))
    res['aircraft_required'] = int(math.ceil(res['aircraft_required_fractional']))
    res['margin'] = res['annual_profit'] / res['annual_gross_rev'] if res['annual_gross_rev'] else 0.0
    res['routes'] = rows
    return res


def route_pnl_from_revenue(cfg, results, rev_cfg, *, aircraft=None, **econ) -> 'RoutePnL':
    """Build a RoutePnL sourcing the cabin fares from a revenue_forecast.RevenueConfig, so
    revenue and cost share one set of fare inputs. Economy = fares_p2p['Y'] x fare_weight,
    Business = fares_p2p['J'] x fare_weight (the Avia weighted one-way fares)."""
    fw = getattr(rev_cfg, 'fare_weight', 1.0) or 1.0
    fares = getattr(rev_cfg, 'fares_p2p', {}) or {}
    econ_fare = float(fares.get('Y', 0) or 0) * fw
    bus_fare = float(fares.get('J', 0) or 0) * fw
    return route_pnl_from_config(cfg, results, econ_fare_ow=econ_fare, bus_fare_ow=bus_fare,
                                 aircraft=aircraft, **econ)


if __name__ == "__main__":
    # 1) Maverick reference reproduced (no incentive; charges are 2025 table, no inflation)
    r = RoutePnL("British Airways", "E190", "LCY", "EDI", 294, 68.60,
                 econ_lf=0.74, bus_lf=0.74, econ_fare_ow=119, bus_fare_ow=236,
                 nav_override=1296, charge_base_year=2025, model_year=2025)
    x = r.compute()
    print("BA LCY-EDI E190 (Maverick reference vs rebuild):")
    print(f"  revenue {x['gross_rev']:,.0f} (ref 22,158)  cost {x['total_cost']:,.0f} (ref 14,912)  profit {x['profit']:,.0f} (ref 7,246)  margin {x['margin']:.1%} (ref 32.7%)")
    print(f"  maintenance {x['maintenance']:,.0f}  [{x['maint_basis']}]")
    print(f"  ownership {x['ownership']:,.0f}  [{x['own_basis']}]")

    # 2) A321XLR GOA-JFK with an airport incentive package (Genoa illustration, indicative charges)
    inc = Incentive(home="GOA", waiver_pct=0.50, support_per_turn=1500)
    g = RoutePnL("New entrant", "A21X", "GOA", "JFK", 3500, 540,
                 econ_lf=0.78, bus_lf=0.65, econ_fare_ow=360, bus_fare_ow=1500,
                 airspace={"Italy":0.10,"France":0.05,"US":0.05}, incentive=inc,
                 airline_type="LCC", aircraft_age=2)
    y = g.compute()
    print("\nA321XLR GOA-JFK with Genoa incentive (50% charge waiver + $1,500/turn support; indicative):")
    print(f"  standalone:      profit {y['profit']:,.0f}   margin {y['margin']:.1%}   breakeven LF {y['breakeven_lf']:.1%}")
    print(f"  airport incentive value/turn: {y['incentive_value']:,.0f}")
    print(f"  with incentive:  profit {y['profit_with_incentive']:,.0f}   margin {y['margin_with_incentive']:.1%}")
    print(f"  maintenance {y['maintenance']:,.0f}  [{y['maint_basis']}]")
    print(f"  ownership {y['ownership']:,.0f}  [{y['own_basis']}]")
    print(f"  origin charges: {y['origin_charge_basis']}   dest charges: {y['dest_charge_basis']}")
