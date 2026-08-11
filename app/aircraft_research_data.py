#!/usr/bin/env python3
r"""Avia Solutions - sourced technical and value data for aircraft types the economics module lacks.

Researched 10 August 2026. Every figure carries a source; a figure without one is None and is
reported as a gap. Nothing here is an estimate: where the open web does not hold a number, the entry
says so, because a gap that is visible can be closed and a guess that looks like a fact cannot.

STATUS follows the June 2026 assumptions register legend:
  current   authoritative source within about eighteen months
  dated     authoritative but older; usable with the vintage stated
  proxy     no direct source; a placeholder that must be replaced
  judgement Avia expert default, anchored on a cited relative

WHAT IS AND IS NOT HERE. Technical data is well covered: manufacturer airport planning documents and
type certificate data sheets are public and current. VALUES AND LEASE RATES ARE LARGELY NOT, because
current per-type appraisals sit behind IBA, Cirium Ascend and Aircraft Value News subscriptions. Of
the types below, most value cells are either absent or pre-2023. That is a finding rather than a
research failure and it needs an appraiser instruction, not more searching.

THREE DEFINITIONS THAT MUST NOT BE MIXED.
  BLOCK burn includes taxi; TRIP burn does not; CRUISE fuel flow is neither. Where a source published
  trip or cruise, the entry says so and the figure understates block.
  CARGO here is the belly limit where a real one is published. A manufacturer's "maximum structural
  payload" is passengers plus bags plus cargo and is NOT a belly allowance; it is not used.
  RANGE is at typical two-class payload where the manufacturer states it. Several older types have no
  public text figure at a stated payload, only a payload-range graph.

Avia Solutions Limited. All rights reserved.
"""

# key: dict of field -> (value, status, source). value None means not found.
RESEARCH = {
    # ---------------------------------------------------------------- widebodies
    "B781": {   # Boeing 787-10, the one that bears on SJC-TPE
        "range_km": (11750, "dated", "Airfinance Journal, Air Investor 2020 p53, at 336 seats. "
                     "Boeing's product page quotes 7,500 nm on a different payload basis; the "
                     "longest 787-10 sector actually flown in OAG 2025 is 10,982 km"),
        "mtow_kg": (254011, "current", "Boeing 787 ACAP D6-58333 Rev P section 2.1.3, Dec 2024. "
                    "An increased-weight option at 260,360 kg was FAA-certified Mar 2026, per "
                    "airframe rather than fleet-wide"),
        "fuel_burn_kg_per_bh": (5500, "dated", "Aircraft Commerce Issue 121, Dec 2018, GEnx-1B at "
                                "337 seats, 5,199 to 5,552 kg per block hour on LHR-AUS to LHR-SCL; "
                                "midpoint taken. Trent 1000-J3 burns 1.7 to 2.1% more"),
        "price_usd": (153_100_000, "dated", "Air Investor 2020 p57, five-appraiser average: Avitas "
                      "157.1, Collateral Verifications 156.0, IBA 155.2, MBA 142.9, Oriel 154.4"),
        "lease_usd_month": (1_050_000, "dated", "Air Investor 2020 p58, five appraisers spanning "
                            "828k to 1,193k; midpoint taken"),
        "cargo_cap_kg": (13000, "current", "IAG Cargo 787-10 fleet page, typical saleable capacity "
                         "on a 256-seat British Airways aircraft; configuration-specific"),
    },
    "A332": {
        "range_km": (13450, "current", "Airbus A330 Family Facts and Figures, Apr 2025, 242t "
                     "variant at 210 to 250 seats"),
        "mtow_kg": (242000, "current", "Airbus A330 ACAP, Dec 2025; 230 to 242t by weight variant, "
                    "top variant taken"),
        "fuel_burn_kg_per_bh": (4800, "dated", "Aircraft Commerce Issue 57, Apr 2008, 4,520 to "
                                "5,110 kg per block hour at 233t and 253 seats with no belly cargo, "
                                "so a light mission; DOES NOT reconcile cleanly with the held A330-300 "
                                "at 6,000 and needs confirming before the two sit side by side"),
        "price_usd": (None, "proxy", "not found; IBA Jan 2026 gives direction only"),
        "lease_usd_month": (None, "proxy", "not found"),
        "cargo_cap_kg": (None, "proxy", "no published belly weight limit; volume 132.4 cubic metres, "
                         "27 LD3, Airbus A330 ACAP Dec 2025"),
    },
    "A343": {
        "range_km": (13149, "dated", "Aircraft Commerce Issue 52, Jun 2007, -300E at 295 seats "
                     "three-class"),
        "mtow_kg": (276500, "current", "Airbus A340-200/-300 ACAP section 2-1-1, Nov 2024; "
                    "253.5 to 276.5t by weight variant, top variant taken"),
        "fuel_burn_kg_per_bh": (6300, "dated", "Aircraft Commerce Issue 52, Jun 2007, 6,040 to "
                                "6,570 kg per block hour on 11 to 14 hour sectors, taxi included"),
        "price_usd": (None, "proxy", "no current appraisal; half-life 5 to 20m USD by build year, "
                      "Ishka Oct 2016, is fourteen years old and pre-dates the type's collapse"),
        "lease_usd_month": (None, "proxy", "320k USD at ten years old, Collateral Verifications via "
                            "Leeham Dec 2013; thirteen years old and not usable"),
        "cargo_cap_kg": (14200, "dated", "Aircraft Commerce Issue 52, Jun 2007, structural underfloor "
                         "payload with a standard passenger load, -300E"),
    },
    "A35K": {
        "range_km": (16480, "current", "FlightGlobal Oct 2023, 8,900 nm at maximum passenger payload. "
                     "Airbus markets 9,100 nm without stating the payload basis"),
        "mtow_kg": (322000, "current", "EASA TCDS EASA.A.151, 1 Jul 2026. Airbus markets 324t, above "
                    "the certified limit, and its own Jul 2025 ACAP tops at 319t"),
        "fuel_burn_kg_per_bh": (6500, "dated", "Aircraft Commerce Issue 121, Dec 2018, 6,340 to "
                                "6,720 kg per block hour at 327 seats, Trent XWB-97, 10 to 15 hour "
                                "sectors; midpoint taken"),
        "price_usd": (164_000_000, "current", "financed new-delivery transactions 2024: 163m Virgin "
                      "Atlantic and circa 165m British Airways, via Airfinance Global Dec 2024. "
                      "These are financing amounts, not appraisals"),
        "lease_usd_month": (1_450_000, "current", "1.4 to 1.5m USD per month new, Collateral "
                            "Verifications at the ISTAT Appraisers' Views, via Airfinance Global "
                            "Dec 2024"),
        "cargo_cap_kg": (14400, "dated", "Aircraft Commerce Issue 121, Dec 2018, typical REVENUE "
                         "cargo, falling to 6,900 kg at a full passenger load. The 52,500 kg "
                         "certificated compartment total is not a revenue figure"),
    },
    "A388": {
        "range_km": (14800, "current", "Airbus A380 product page, Jul 2024, at four-class 545 seats"),
        "mtow_kg": (575000, "current", "Airbus A380 ACAP section 2-1-1, Nov 2024; 480 to 575t by "
                    "weight variant, top variant taken"),
        "fuel_burn_kg_per_bh": (None, "proxy", "no block figure published by any acceptable source. "
                                "The only measured data is TRIP fuel over trip time, 11,800 to 13,400 "
                                "kg per hour from 2,745 actual flights, Jung and Choi, Aerospace 11(8) "
                                "665, Aug 2024, which excludes taxi and therefore understates block"),
        "price_usd": (None, "proxy", "no appraisal found. Disclosed transactions at about twelve "
                      "years are 33 to 40m USD, but all are Emirates lease buyouts under contractual "
                      "option rather than arm's-length trades"),
        "lease_usd_month": (None, "proxy", "no operating-lease market; the fleet is airline-owned"),
        "cargo_cap_kg": (3890, "dated", "Aircraft Commerce Issue 97, Dec 2014, typical REVENUE belly "
                         "freight on a passenger service, volume-limited at full load. The 51,402 kg "
                         "certificated total is structural and unattainable in service"),
    },
    "B772": {
        "range_km": (13084, "current", "Boeing technical characteristics via Wikipedia specification "
                     "table, at 301 seats three-class. Aircraft Commerce Issue 60 gives 14,168 km at "
                     "305 seats on a different weight basis"),
        "mtow_kg": (297556, "current", "EASA TCDS IM.A.003 Issue 20, May 2026, top certified weight"),
        "fuel_burn_kg_per_bh": (6500, "dated", "Aircraft Commerce Issue 60, Oct 2008, 6,340 to 6,670 "
                                "kg per block hour, LHR-NRT at 305 seats. The same conversion "
                                "reproduces the 777-300ER at 6,900 to 7,020, inside Avia's own "
                                "6,800 to 7,100 anchor, which validates the method"),
        "price_usd": (None, "proxy", "not found; EETC prospectuses are the most likely free route"),
        "lease_usd_month": (None, "proxy", "not found"),
        "cargo_cap_kg": (None, "proxy", "no published belly weight limit; volume 160.3 cubic metres, "
                         "32 LD3 plus bulk, Boeing D6-58329 Rev E Dec 2024"),
    },
    "B77L": {
        "range_km": (15844, "current", "Boeing technical characteristics via Wikipedia specification "
                     "table, maximum design range"),
        "mtow_kg": (347814, "current", "EASA TCDS IM.A.003 Issue 20, May 2026, increased-weight option"),
        "fuel_burn_kg_per_bh": (7100, "dated", "Aircraft Commerce Issue 60, Oct 2008, 7,080 to 7,110 "
                                "kg per block hour, YYZ-HKG at 301 seats. A sixteen-hour sector at "
                                "near-maximum weight, not comparable hour for hour with a shorter one"),
        "price_usd": (None, "proxy", "not found"),
        "lease_usd_month": (None, "proxy", "not found"),
        "cargo_cap_kg": (None, "proxy", "no published belly weight limit. Fitting the three optional "
                         "auxiliary tanks cuts the aft hold from 14 to 8 LD3"),
    },
    "B773": {
        "range_km": (11140, "dated", "Aircraft Commerce Issue 60, Oct 2008, at 368 seats three-class, "
                     "GE90-94B; range varies materially by engine, 10,454 to 11,140 km"),
        "mtow_kg": (299370, "current", "EASA TCDS IM.A.003 Issue 20, May 2026. All sixty built were "
                    "specified at this weight"),
        "fuel_burn_kg_per_bh": (None, "proxy", "not found. The Aircraft Commerce fuel study covers "
                                "four of the five passenger 777 variants and omits the -300 non-ER"),
        "price_usd": (None, "proxy", "not found"),
        "lease_usd_month": (None, "proxy", "not found"),
        "cargo_cap_kg": (None, "proxy", "no published belly weight limit; volume 213.9 cubic metres, "
                         "44 LD3 plus bulk, Boeing D6-58329 Rev E Dec 2024"),
    },
    "B748": {
        "range_km": (14310, "dated", "Boeing news release, Aug 2015; payload basis not stated"),
        "mtow_kg": (447696, "current", "Boeing 747-8 ACAP D6-58326-3 Rev C section 2.1.2, Aug 2023; "
                    "a single weight option for the passenger aircraft"),
        "fuel_burn_kg_per_bh": (None, "proxy", "not found for the passenger variant. EUROCONTROL "
                                "carries no fuel data for the B748 and Aircraft Commerce has no "
                                "747-8I analysis. The freighter figure is not a substitute: different "
                                "empty weight, different zero-fuel weight, different mission"),
        "price_usd": (None, "proxy", "no appraisal. Disclosed transactions at seven to nine years are "
                      "about 135m USD, Reuters May 2024"),
        "lease_usd_month": (None, "proxy", "no operating-lease market for the passenger aircraft"),
        "cargo_cap_kg": (16920, "current", "Lufthansa Cargo belly fleet page, commercial belly "
                         "capacity, 22 LD3 forward and 16 aft"),
    },
    "B753": {
        "range_km": (6420, "dated", "Boeing news release, Oct 2000, RB211-535E4B; no payload or "
                     "configuration stated. The commonly quoted 6,288 km at 243 seats traces to "
                     "Boeing pages now withdrawn and could not be verified at source"),
        "mtow_kg": (122449, "current", "Boeing 757 ACAP D6-58327 Rev H section 2.1.4, Dec 2024; a "
                    "single weight, identical across engines"),
        "fuel_burn_kg_per_bh": (None, "proxy", "no block figure. Aircraft Commerce Issue 43, Oct 2005, "
                                "publishes trip fuel over FLIGHT time, about 3,945 to 4,190 kg per "
                                "flight hour at 245 seats, which is above the block figure"),
        "price_usd": (None, "proxy", "the only appraisal found is a 2001 EETC at 64.4 to 64.8m USD "
                      "for new aircraft, twenty-five years old and useless for a 20 to 25 year "
                      "airframe"),
        "lease_usd_month": (None, "proxy", "not found; Aircraft Commerce publishes the 757-200 only"),
        "cargo_cap_kg": (None, "proxy", "no published belly weight limit; volume 67.5 cubic metres"),
    },
    "B764": {
        "range_km": (10371, "dated", "Aircraft Commerce Issue 46, Jun 2006, at 243 seats three-class; "
                     "corroborated at 10,418 km by the Boeing specification table"),
        "mtow_kg": (204116, "current", "Boeing 767 ACAP D6-58328 Rev K, Dec 2024; a single weight, "
                    "identical across engines"),
        "fuel_burn_kg_per_bh": (5000, "dated", "Aircraft Commerce Issue 46, Jun 2006, 4,910 to 5,120 "
                                "kg per hour, LAX-ARN at 243 seats, CF6-80C2B8. The source is "
                                "ambiguous between block and flight time, so the span covers both"),
        "price_usd": (None, "proxy", "not found"),
        "lease_usd_month": (None, "proxy", "not found"),
        "cargo_cap_kg": (None, "proxy", "no published belly weight limit; volume 138.9 cubic metres, "
                         "38 LD2 plus bulk. All 37 built are CF6-powered"),
    },
    # ---------------------------------------------------------------- narrowbodies
    "A221": {
        "range_km": (6700, "current", "Airbus A220-100 product page, Jul 2024, at 100 to 120 "
                     "two-class seats"),
        "mtow_kg": (63730, "current", "Airbus A220-100 Airport Planning Publication Issue 032, "
                    "Oct 2023"),
        "fuel_burn_kg_per_bh": (1250, "dated", "Aircraft Commerce Issue 142, Jun 2022, CAE Flight "
                                "Plan Manager, 1,130 to 1,360 kg per block hour across 200 to 860 nm; "
                                "midpoint taken. Trip fuel excludes taxi, so this understates block, "
                                "and every sector in the study carries a 22 to 42 kt tailwind"),
        "price_usd": (None, "proxy", "not found from a named appraiser"),
        "lease_usd_month": (None, "proxy", "not found from a named appraiser"),
        "cargo_cap_kg": (3760, "current", "Airbus A220-100 APP Issue 032, Oct 2023, structural "
                         "combined hold limit, 23.3 cubic metres"),
    },
    "A223": {
        "range_km": (6300, "current", "Airbus A220-300 product page, Jul 2024, at 120 to 150 "
                     "two-class seats"),
        "mtow_kg": (70896, "current", "Airbus A220-300 Airport Planning Publication Issue 031, "
                    "Oct 2023"),
        "fuel_burn_kg_per_bh": (1390, "dated", "Aircraft Commerce Issue 142, Jun 2022, 1,245 to "
                                "1,535 kg per block hour across 200 to 860 nm; midpoint taken. Same "
                                "trip-fuel and tailwind caveats as the -100"),
        "price_usd": (36_100_000, "dated", "Cirium Aircraft Value Guide, Mar 2022, new-delivery "
                      "full-life market value. IBA gave 39.2m base value new in Feb 2023"),
        "lease_usd_month": (250_000, "dated", "Cirium Aircraft Value Guide Mar 2022 gives 245k on a "
                            "nine to ten year lease; IBA gave 260.5k in Jan 2023"),
        "cargo_cap_kg": (5052, "current", "Airbus A220-300 APP Issue 031, Oct 2023, structural "
                         "combined hold limit; binds before the 5,705 kg of spare payload under MZFW"),
    },
    "A31N": {
        "range_km": (6850, "current", "Airbus A319neo product page, Jul 2024, at 120 to 150 "
                     "two-class seats"),
        "mtow_kg": (75500, "current", "Airbus A319 Aircraft Characteristics section 2-1-1, Jun 2024, "
                    "top of three weight variants"),
        "fuel_burn_kg_per_bh": (None, "proxy", "not found. Aircraft Commerce excluded the type from "
                                "its 2022 study because fewer than a hundred have been ordered"),
        "price_usd": (None, "proxy", "not found; the 2018 list price of 101.5m USD is not a market "
                      "value"),
        "lease_usd_month": (None, "proxy", "not found"),
        "cargo_cap_kg": (None, "proxy", "no published mass limit; volume 32 cubic metres, four "
                         "LD3-45W"),
    },
    "B717": {
        "range_km": (3815, "current", "EUROCONTROL Aircraft Performance Database, B712, at 54,885 kg"),
        "mtow_kg": (54885, "current", "EUROCONTROL APD and FAA Federal Register special conditions "
                    "25-144-SC, May 1999, high gross weight build"),
        "fuel_burn_kg_per_bh": (None, "proxy", "no block figure. Boeing published trip fuel per seat "
                                "only: 18.1, 26.7 and 48.7 kg per seat at 300, 500 and 1,000 nm at "
                                "106 seats"),
        "price_usd": (2_150_000, "current", "IBA data Jun 2026 via MyAirTrade FleetStatus, half-life "
                      "current market value 1.975 to 2.321m USD across airframes built 1999 to 2006, "
                      "so twenty to twenty-seven years old; midpoint taken"),
        "lease_usd_month": (35_000, "current", "IBA data Jun 2026, market lease 32k to 38k USD; "
                            "midpoint taken"),
        "cargo_cap_kg": (None, "proxy", "no published mass limit; volume 26.5 cubic metres"),
    },
    "B733": {
        "range_km": (2963, "current", "EUROCONTROL Aircraft Performance Database, B733; payload "
                     "condition not stated"),
        "mtow_kg": (63276, "current", "Boeing 737 Classic ACAP D6-58325-6 Rev E section 2.1.6, "
                    "Nov 2023, CFM56-3B2 top weight option"),
        "fuel_burn_kg_per_bh": (None, "proxy", "no block figure. Long-range cruise fuel flow of "
                                "2,250 kg per hour is a cruise figure and must not be used as block"),
        "price_usd": (None, "proxy", "IBA prints its own not-available marker against the type and "
                      "every broker listing is price on request. Of 1,113 built, 758 are retired, "
                      "169 stored and 39 written off: the type trades as part-out feedstock rather "
                      "than as an appraised flying asset"),
        "lease_usd_month": (None, "proxy", "as above"),
        "cargo_cap_kg": (None, "proxy", "no published mass limit; volume 30.2 cubic metres"),
    },
    "B734": {
        "range_km": (3889, "current", "EUROCONTROL Aircraft Performance Database, B734; payload "
                     "condition not stated"),
        "mtow_kg": (68039, "current", "Boeing 737 Classic ACAP Rev E section 2.1.7, Nov 2023, top "
                    "weight option"),
        "fuel_burn_kg_per_bh": (None, "proxy", "no block figure; cruise fuel flow 2,377 kg per hour"),
        "price_usd": (None, "proxy", "not found for a passenger airframe. The only figure located is "
                      "7.1m USD average across 35 FREIGHTERS in a 2018 securitisation, which is "
                      "eight years old and the wrong configuration"),
        "lease_usd_month": (None, "proxy", "not found"),
        "cargo_cap_kg": (None, "proxy", "no published mass limit; volume 38.9 cubic metres"),
    },
    "B735": {
        "range_km": (2963, "current", "EUROCONTROL Aircraft Performance Database, B735; payload "
                     "condition not stated"),
        "mtow_kg": (61689, "current", "Boeing 737 Classic ACAP Rev E section 2.1.8, Nov 2023, top "
                    "weight option"),
        "fuel_burn_kg_per_bh": (None, "proxy", "no block figure; cruise fuel flow 2,100 kg per hour"),
        "price_usd": (None, "proxy", "the only figure is a 3.25m USD asking price for a 1992 airframe "
                      "on a broker marketplace, which is neither a transaction nor an appraisal"),
        "lease_usd_month": (None, "proxy", "not found"),
        "cargo_cap_kg": (4460, "dated", "ANA Cargo Dimension Guide 2019, structural compartment "
                         "limits, forward 1,573 kg and aft 2,888 kg"),
    },
    "B736": {
        "range_km": (5648, "dated", "Frawley, International Directory of Civil Aircraft, data to "
                     "Oct 2002, high gross weight. Boeing has withdrawn its 737NG product pages and "
                     "publishes payload-range only as a graph"),
        "mtow_kg": (65544, "current", "Boeing 737NG ACAP D6-58325-7 Rev C section 2.1.1, Oct 2025, "
                    "top of three certified weights"),
        "fuel_burn_kg_per_bh": (2345, "dated", "Aircraft Commerce Issue 58, Jun 2008, Jeppesen data, "
                                "about 2,330 to 2,360 kg per block hour on a 671 nm sector at 132 "
                                "seats; midpoint taken. Reported at second hand and not re-fetched, "
                                "so one grade less reliable than the other Aircraft Commerce figures"),
        "price_usd": (None, "proxy", "not found; only 69 were built between 1998 and 2007"),
        "lease_usd_month": (None, "proxy", "not found"),
        "cargo_cap_kg": (None, "proxy", "no published mass limit; volume 21.4 cubic metres"),
    },
    "B737": {
        "range_km": (6037, "dated", "Frawley, International Directory of Civil Aircraft, data to "
                     "Oct 2002, high gross weight at 126 seats"),
        "mtow_kg": (70080, "current", "Boeing 737NG ACAP Rev C section 2.1.2, Oct 2025, top of three "
                    "certified weights"),
        "fuel_burn_kg_per_bh": (None, "proxy", "TWO SOURCES DIVERGE BY ABOUT 40% AND ARE NOT "
                                "RECONCILED. Aircraft Commerce Issue 142, Jun 2022, gives about "
                                "1,460 to 1,780 kg per block hour at 110 seats on tailwind sectors "
                                "with trip fuel; Issue 58, Jun 2008, gives about 2,380 to 2,425 at "
                                "149 seats with block fuel. The gap is passenger load, taxi fuel and "
                                "wind. A single figure should come from a fresh flight-plan run "
                                "against a stated payload and sector, not from either study"),
        "price_usd": (None, "proxy", "not found from a named appraiser; IBA notes values declining "
                      "without publishing a figure"),
        "lease_usd_month": (None, "proxy", "not found from a named appraiser"),
        "cargo_cap_kg": (5181, "current", "Delta Cargo aircraft specification, structural compartment "
                         "limit; volume 28.4 cubic metres"),
    },
    "B739": {
        "range_km": (4750, "current", "Aircraft Commerce Issue 123, Apr 2019, at a full 179-seat "
                     "payload. Boeing's 5,900 km assumes optional winglets and auxiliary tanks"),
        "mtow_kg": (85139, "current", "Boeing 737NG ACAP Rev C section 2.1.5, Oct 2025, with winglets"),
        "fuel_burn_kg_per_bh": (2460, "current", "Aircraft Commerce Issue 123, Apr 2019, Lido/Flight, "
                                "2,305 to 2,613 kg per block hour across 682 to 2,165 nm at a full "
                                "179-seat payload; midpoint taken. This source publishes genuine "
                                "block fuel and block time, taxi and APU included"),
        "price_usd": (32_000_000, "current", "IBA Aircraft Market Intelligence Report via AviTrader, "
                      "Oct 2025: 32 to 34m USD for a 2019 build, 21.5 to 22.5m for a 2011 build. The "
                      "younger figure is taken; production ended in 2019 so there is no new value"),
        "lease_usd_month": (300_000, "current", "IBA via AviTrader, Oct 2025, 298k to 307k USD for "
                            "newer aircraft and 223k to 252k mid-life"),
        "cargo_cap_kg": (4877, "current", "Aircraft Commerce Issue 123, Apr 2019, remaining REVENUE "
                         "payload at 179 passengers including bags, not a structural limit"),
    },
    "B39M": {
        "range_km": (6110, "current", "Boeing 737 MAX product page, at 175 to 195 two-class seats"),
        "mtow_kg": (88314, "current", "Boeing 737 MAX ACAP D6-38A004 Rev K section 2.1.5, Jul 2025, "
                    "top of three certified weights"),
        "fuel_burn_kg_per_bh": (None, "proxy", "not found. No acceptable source publishes a MAX 9 "
                                "figure; scaling from the MAX 8 would be an assumption and is not "
                                "done here"),
        "price_usd": (None, "proxy", "no appraiser publishes a MAX 9 value; IBA's Jul 2026 release "
                      "covers the MAX 8 and A320neo only, and IBA has noted MAX 9 demand lagging "
                      "every other variant"),
        "lease_usd_month": (None, "proxy", "not found"),
        "cargo_cap_kg": (None, "proxy", "no published mass limit; volume 50.5 cubic metres"),
    },
}

# Types in the gap list that were NOT researched on 10 August 2026, because the session's web search
# budget was exhausted. Named so the gap is visible rather than implied by absence.
NOT_RESEARCHED = [
    "E175", "E290", "E295", "ERJ135", "ERJ145", "CRJ200", "CRJ550", "CRJ700", "CRJ1000",
    "AT42", "DH8A", "DH8B", "DH8C", "DHC6", "SU95", "F100", "MD82", "AN24", "B190", "E120", "SW4",
]

FIELDS = ["range_km", "mtow_kg", "fuel_burn_kg_per_bh", "price_usd", "lease_usd_month",
          "cargo_cap_kg"]


# ---------------------------------------------------------------- conflicts, and what settled them
# Six conflicts were put to two external models with search, on 10 August 2026, alongside Avia's own
# research. Recorded here because a conflict that is resolved and not written down gets re-opened.
CONFLICTS = {
    "A350-1000 MTOW": (
        "SETTLED at 322,000 kg. EASA TCDS EASA.A.151 certifies 322t. Airbus facts and figures give "
        "MTOW 322,000 kg and maximum TAXI weight 322,900 kg, which is the likely origin of the "
        "324t marketing figure; the July 2025 airport planning document at 319t is an earlier weight "
        "variant. Both external checks agree on 322t."),
    "E190 and E175 block burn": (
        "RESOLVED against reported actuals, and the module is wrong. Form 41 Schedule P-5.2 for 2023, "
        "read from E:\\Avia\\Usmarket data\\F41_P52, reports fuel issued and airborne hours by "
        "aircraft type for US carriers. Fuel over hours, converted at 3.039 kg per USG and adjusted "
        "to a block basis with a 20 minute taxi allowance, gives E190 2,386, E170 1,616 and CRJ900 "
        "1,704 kg per block hour. The module holds 1,106, 920 and 1,100, so it runs at 0.46 to 0.65 "
        "of reported actual on the regional band. Aircraft Commerce Issue 64 was closer to the truth "
        "than the module, not further from it, and my consistency check was worthless here because "
        "the whole regional band was wrong TOGETHER, so it agreed with itself. THE SAME TEST "
        "VALIDATES THE MAINLINE: every narrowbody and widebody held sits between 0.94 and 1.10 of "
        "reported actual. The fault is confined to the regional types."),
    "CRJ200 range": (
        "STILL OPEN, and the document and the arithmetic disagree. The Issue 66 specification table "
        "is explicitly headed 'Range with full payload and LRC' and gives 1,645 nm ER and 2,005 nm "
        "LR, which is the only place in the article where a full-payload basis is stated; on that "
        "evidence the HIGHER pair is the full-payload one and the earlier reading here was wrong. "
        "But the arithmetic will not support it: at MZFW 19,958 kg and MTOW 24,041 kg full payload "
        "leaves 4,083 kg of fuel, which at 1,088 kg per block hour is 3.75 hours, roughly 1,690 nm "
        "gross of reserves. A stated header and a weight limit cannot both be right. Do not put "
        "either pair in a deliverable labelled full payload until the weights behind the table are "
        "read."),
    "A330-200 against A330-300 burn": (
        "EXPLAINED, and more like for like than first thought. Issue 57 runs BOTH variants on one "
        "methodology: 233t airframes, full three-class loads of 253 passengers on the -200 and 295 "
        "on the -300, 20 minutes taxi, long-range cruise at M0.82, June winds. So the -200 result is "
        "not an empty-aircraft case, though it carries no belly freight. The source supports a real "
        "-200 advantage on the modelled missions but does not support attributing the whole gap to "
        "the airframe. Do not quote the two side by side without matching stage length, payload and "
        "engine."),
    "737-700 block burn": (
        "RESOLVED, and it was a denominator error rather than a 40% difference in aeroplanes. Issue "
        "142 labels its columns Flight time and Trip fuel, despite the standing BLOCK FUEL "
        "PERFORMANCE page heading. Trip fuel over FLIGHT time gives 2,047 to 2,251 kg per hour; the "
        "1,460 to 1,780 figure came from dividing trip fuel by the longer BLOCK time, which mixes a "
        "numerator that excludes taxi with a denominator that includes it. Issue 58, which does "
        "include 20 minutes of taxi in both, converts to 2,327 to 2,369 kg per block hour. The two "
        "studies agree within about 10% once the denominator is handled consistently, and the "
        "residual is the 3.34 tonne payload difference and 2022's tailwinds."),
    "787-10 range": (
        "NOT RESOLVED. No pre and post table on a common payload basis exists in public sources. The "
        "11,750 km payload-defined figure is used, corroborated by the longest 787-10 sector actually "
        "flown in OAG 2025 at 10,982 km."),
}

# ---------------------------------------------------------------- Form 41, reported actuals
# US DOT Form 41 Schedule P-5.2, calendar 2023, from E:\Avia\Usmarket data\F41_P52\T_F41SCHEDULE_P52.csv
# joined to the DOT aircraft type table in dot_support.duckdb. Fuel ISSUED over AIRBORNE hours, at
# 3.039 kg per US gallon.
#
# This is the only source here drawn from what airlines actually spent and actually flew, rather than
# from a flight-planning system. It validated every mainline type the module holds to within 6% and
# found the regional band running at half of reported actual.
#
# THREE CAVEATS, and the first is the soft one.
#   1. The schedule reports AIRBORNE hours, not block hours. The block figures below apply a 20 minute
#      taxi allowance over an assumed airborne time per sector, which is Avia's assumption, not DOT's.
#      It matters most on the short-sector types, where it moves the answer by up to 20%.
#   2. One year, 2023, and US carriers only. A European regional operator flies shorter sectors.
#   3. Sample size varies enormously: the E175 rests on 1,329 airborne hours across five carriers and
#      is solid; the E190 on 102 hours at one carrier and is indicative. Hours are carried below so a
#      reader can see which is which.
F41_2023 = {
    # Keyed on the MODULE key wherever one exists, not on a display name: keying "ERJ-145" while the
    # module calls it ERJ145 meant the fill-in pack showed no burn for a type that had been measured.
    # name: (kg per airborne hour, kg per block hour as adjusted, airborne hours in the sample)
    "ERJ145":     (1552, 1012, 184),
    "CRJ200":     (1544, 1029, 173),
    "CRJ700":     (1938, 1542, 245),
    "E175":       (1957, 1581, 1329),
    "E170":       (2001, 1616, 80),
    "CRJ900":     (2083, 1704, 465),
    "E190":       (2916, 2386, 102),
    "717-200":    (2873, 2320, 177),
    "A220-300":   (2582, 2159, 104),
    "737 MAX 8":  (2361, 2050, 995),
    "A320neo":    (2442, 2121, 551),
    "A319":       (2712, 2341, 865),
    "A321neo":    (2719, 2387, 666),
    "737-800":    (2814, 2458, 2499),
    "A320":       (2816, 2460, 1444),
    "737-900ER":  (2827, 2483, 1236),
    "A321":       (3276, 2891, 1560),
    "757-200":    (3561, 3205, 536),
    "757-300":    (3887, 3413, 116),
    "767-300ER":  (4749, 4452, 915),
    "787-8":      (5128, 4895, 196),
    "787-9":      (5492, 5258, 287),
    "767-400ER":  (5500, 5211, 146),
    "787-10":     (5536, 5266, 101),
    "A330-200":   (5806, 5542, 151),
    "A330-300":   (6265, 5960, 144),
    "A350-900":   (6305, 6053, 125),
    "777-200ER":  (6844, 6571, 516),
    "777-300ER":  (8121, 7815, 185),
    "747-8":      (8362, 8046, 204),
}

# What Form 41 does to this session's own research, type by type. Kept because a research figure that
# has been checked against reported actuals is worth more than one that has not.
F41_VERDICT = {
    "B781": "5,500 researched against 5,266 reported, 1.04x. STANDS.",
    "B772": "6,500 researched against 6,571 reported, 0.99x. STANDS.",
    "B764": "5,000 researched against 5,211 reported, 0.96x. STANDS.",
    "B739": "2,460 researched against 2,483 reported, 0.99x. STANDS.",
    "A332": "4,800 researched against 5,542 reported, 0.87x. REPLACE with 5,542: the Aircraft "
            "Commerce mission was a light 233t airframe with no belly cargo, exactly as flagged.",
    "A223": "1,390 researched against 2,159 reported, 0.64x. REPLACE with 2,159. The Issue 142 study "
            "is trip fuel on tailwind sectors and does not transfer.",
    "B717": "was NOT FOUND, now 2,320 from reported actuals.",
    "B748": "was NOT FOUND, now 8,046 from reported actuals.",
    "B753": "was NOT FOUND, now 3,413 from reported actuals.",
    "B773": "still NOT FOUND: Form 41 carries the -300ER, not the non-ER.",
    "B39M": "still NOT FOUND for the MAX 9 specifically; the MAX 8 reports 2,050.",
}

# ---------------------------------------------------------------- Aircraft Commerce, flight-planned
# Genuine BLOCK figures, taxi included, from an external check that opened the articles and stated
# the article's own density of 6.55 lb per US gallon rather than importing one. These close types
# Form 41 does not carry, because US carriers do not fly them or do not report them separately.
#
# HOW THESE SIT AGAINST FORM 41, which is the reconciliation that matters. Where both exist, the
# reported actuals run ABOVE the flight plans on most types: A330-300 5,960 reported against 4,745 to
# 5,447 planned, E190 2,386 against 1,923 to 1,980. That is the expected direction. A flight plan is
# an optimised mission in still conditions; reported fuel carries weather, ATC routing, holding,
# tankering and every non-optimal day of the year. Two run the other way, the 747-8 and the 777-300
# non-ER, and neither has a large Form 41 sample.
#
# POLICY, therefore: prefer Form 41 where the sample supports it, and treat an Aircraft Commerce
# figure as a floor that probably runs a few per cent light of what an operator will actually see.
AC_BLOCK = {
    # key: (low, high, source)
    "A388":   (10989, 13049, "Aircraft Commerce Issue 113, Aug 2017, five missions, GP7270 and "
                             "Trent 970, block fuel including taxi. Closes a gap where the only "
                             "prior figure was trip fuel over trip time"),
    "B748":   (9300, 10878, "Aircraft Commerce Issue 113, Aug 2017, passenger 747-8, five missions. "
                            "Form 41 reports 8,046 on 204 airborne hours, so the reported actual is "
                            "BELOW the plan here, which is unusual and unexplained"),
    "B773":   (6382, 6984, "Aircraft Commerce Issue 68, Feb 2010, 390 passengers, PW4098, taxi "
                           "included. The non-ER, which Form 41 does not separate from the -300ER"),
    "B753":   (3573, 4101, "Aircraft Commerce Issue 59, Aug 2008, RB211-535E4B, 20 minute taxi. "
                           "Form 41 reports 3,413 on 116 airborne hours"),
    "B733":   (2278, 2372, "Aircraft Commerce Issue 45, Apr 2006, block fuel and block time with 20 "
                           "minute taxi. Sits just below the Form 41 737-800 at 2,458, which is the "
                           "right direction for a smaller, older airframe"),
    "B734":   (2422, 2567, "Aircraft Commerce Issue 45, Apr 2006, genuine block basis"),
    "B735":   (2101, 2272, "Aircraft Commerce Issue 45, Apr 2006, genuine block basis"),
    "B39M":   (1768, 2210, "Aircraft Commerce Issue 137, Aug 2021, 152 and 170 passenger cases. "
                           "Form 41 reports the MAX 8 at 2,050, so the MAX 9 range is credible"),
}

# E2 hold limits, from the airport planning manual an earlier check could not open.
E2_CARGO = {
    "E290": (3500, "Embraer E-Jets E2 APM-5824 Revision 25, 29 Nov 2024: forward 1,590 kg plus aft "
                   "1,910 kg. A SUM of compartment maxima, so it may not be simultaneously "
                   "achievable within the centre of gravity envelope"),
    "E295": (4930, "Embraer E-Jets E2 APM-5824 Revision 25, 29 Nov 2024: forward 2,375 kg plus aft "
                   "2,555 kg. Same caveat on summing"),
}

# Confirmed after the main pass, by an external check that reached documents Avia's own research
# could not open. Recorded separately so the provenance stays visible.
LATE_CONFIRMED = {
    "SW4": {"cargo_cap_kg": (748, "current",
            "FAA Type Certificate Data Sheet A18SW Revision 3, 1 Dec 2000, archived copy: nose "
            "compartment 800 lb / 362.9 kg and rear 385.6 kg, the same limits for SA227-CC and -DC. "
            "The arithmetic total is subject to centre of gravity and loading limits. Reached by an "
            "external check after the FAA Dynamic Regulatory System proved unopenable here; a second "
            "external check independently returned the same two figures.")},
    "E120": {"cargo_cap_kg": (550, "current",
             "EASA Type Certificate Data Sheet EASA.IM.A.188 Issue 02, 31 Jan 2022, section III.9 "
             "and Note 5: 550 kg maximum baggage, raisable to 700 kg by Embraer Engineering Order "
             "120-208046. NOTE a second check could not confirm this from FAA A31SO, which it could "
             "not open; the EASA sheet was read directly here, so the figure stands, but the "
             "proportion of the fleet embodying the 700 kg change is unknown.")},
}

# Values and lease rates: three independent research paths, two of them external, all conclude that
# current per-type appraisals are not available in free public form for these types. EETC prospectuses
# and airline filings cover some US-operated types but did not yield usable figures. This is now a
# settled finding rather than an open search: closing it needs an appraiser instruction to IBA,
# Cirium Ascend or Avitas, which is a commercial decision rather than a research task.


def coverage():
    """How much of the research actually landed, by field. Counting is the honest headline."""
    out = {}
    for f in FIELDS:
        got = sum(1 for v in RESEARCH.values() if v.get(f, (None,))[0] is not None)
        out[f] = (got, len(RESEARCH))
    return out


if __name__ == "__main__":
    print("types researched: %d of %d in the gap list" % (len(RESEARCH),
                                                          len(RESEARCH) + len(NOT_RESEARCHED)))
    for f, (got, tot) in coverage().items():
        print("  %-22s %2d of %2d found" % (f, got, tot))
