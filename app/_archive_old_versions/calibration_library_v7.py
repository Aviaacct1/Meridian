"""
Avia Solutions  QSI Calibration Library
=========================================
Extracted from completed route forecasts across 35+ development chats.
This file contains structured calibration data for training the
automated calibration learning system.

Each route case captures:
  - Route characteristics (origin, destination, carrier, type, frequency)
  - Raw QSI model outputs
  - Expert-calibrated final outputs
  - The adjustment factors applied (and why)
  - Key observations for pattern recognition

USAGE:
  Import this module to access CALIBRATION_CASES (list of dicts).
  Each case has standardised keys for machine learning ingestion.

LAST UPDATED: February 2026 (Chat 47 -- added LH FRA/MUC-SJC cases, 4 calibration rules from independent forecast test)
"""

# =============================================================================
# CALIBRATION CASES
# =============================================================================

CALIBRATION_CASES = [

    # =========================================================================
    # CASE 1: BA LHR-SJC (British Airways London Heathrow - San Jose)
    # =========================================================================
    {
        "route_id": "BA_LHR_SJC",
        "origin": "LHR",
        "destination": "SJC",
        "origin_city": "LON",
        "destination_city": "SJC",
        "carrier": "BA",
        "carrier_name": "British Airways",
        "alliance": "OneWorld",
        "carrier_type": "Full Service",
        "route_type": "Hub Longhaul",
        "hub_airport": "LHR",
        "hub_status": "Major Hub",  # LHR is one of world's largest hubs
        "frequency": 7,  # daily
        "aircraft": "B777-200",
        "seats_per_flight": 275,  # approximate
        "annual_seats": None,  # to be confirmed from source files
        "departure_time_home": "11:15",
        "departure_time_dest": "15:35",
        "forecast_year": 2015,
        "data_vintage": "Sep2013-Aug2014",
        "existing_service": True,  # BA already operated this route

        # DEMAND
        "p2p_base_demand": None,  # multiple segments, complex
        "p2p_stimulation": 1.15,  # moderate  existing service
        "p2p_capture_rate_range": "15-40%",  # varies by segment (UK Bus/Leisure)
        "p2p_forecast": None,  # to be extracted from final files

        # CONNECTING
        "cnx_home_total_demand": None,
        "cnx_home_qsi_share_blended": 0.195,  # ~19.5%  the key calibration target
        "cnx_home_forecast": None,
        "cnx_dest_forecast": None,
        "cnx_ceiling": 0.85,

        # TOTALS
        "grand_total_forecast": 129162,  # the benchmark target
        "load_factor": 0.80,  # approximate

        # CALIBRATION
        "factor_up": None,
        "qsi_adjustment": None,  # significant adjustments were needed
        "calibration_factors_by_market": {
            # Raw QSI overestimated connecting traffic ~5x
            # Median calibration factor across markets was 0.267
            # Range: 0.025 to 1.382
            "description": "Heavy calibration needed. Raw QSI overestimates connecting traffic.",
            "median_factor": 0.267,
            "factor_range": (0.025, 1.382),
        },

        # CONTEXT
        "notes": [
            "Primary benchmark case  validated extensively across 23+ development chats",
            "BA is a major hub carrier at LHR  massive connecting network",
            "Existing service being re-assessed, not a new route proposal",
            "Multiple time variants tested (original time, new time, 5pm departure)",
            "With/without India variants explored (India connecting market sensitivity)",
            "Cannibalisation analysis performed for SFO overlap",
            "This was the route where the calibration system was built and validated",
            "QSI coefficients from Jonathan (2013)  unchanged since creation",
        ],
        "departure_time_sensitivity": {
            "description": "30-minute departure time changes shifted individual market capture by 15+ percentage points",
            "variants_tested": ["original_time", "new_time", "5pm_SJC_departure"],
        },
    },

    # =========================================================================
    # CASE 2: KLM AMS-TPA (KLM Amsterdam - Tampa)
    # =========================================================================
    {
        "route_id": "KLM_AMS_TPA",
        "origin": "AMS",
        "destination": "TPA",
        "origin_city": "AMS",
        "destination_city": "TPA",
        "carrier": "KL",
        "carrier_name": "KLM Royal Dutch Airlines",
        "alliance": "SkyTeam",
        "carrier_type": "Full Service",
        "route_type": "Hub Longhaul",
        "hub_airport": "AMS",
        "hub_status": "Major Hub",
        "frequency": None,  # to be confirmed
        "aircraft": None,
        "seats_per_flight": None,
        "annual_seats": None,
        "departure_time_home": None,
        "departure_time_dest": None,
        "forecast_year": 2023,
        "data_vintage": None,
        "existing_service": False,  # new route proposal

        # DEMAND
        "p2p_base_demand": None,
        "p2p_stimulation": 1.0,
        "p2p_capture_rate_range": "varies",
        "p2p_forecast": None,

        # CONNECTING
        "cnx_home_total_demand": None,
        "cnx_home_qsi_share_blended": None,
        "cnx_home_forecast": None,
        "cnx_dest_forecast": None,
        "cnx_ceiling": None,

        # TOTALS
        "grand_total_forecast": 74000,  # approximate
        "load_factor": 0.75,  # approximate

        # CALIBRATION
        "factor_up": None,
        "qsi_adjustment": None,
        "calibration_factors_by_market": {},

        # CONTEXT
        "notes": [
            "Validated during pipeline development",
            "AMS is a major hub with strong European feed",
            "TPA is a leisure/VFR destination  different profile from SJC tech market",
        ],
    },

    # =========================================================================
    # CASE 3: EI DUB-SJC 4x Weekly (Aer Lingus Dublin - San Jose)
    # =========================================================================
    {
        "route_id": "EI_DUB_SJC_4x",
        "origin": "DUB",
        "destination": "SJC",
        "origin_city": "DUB",
        "destination_city": "SJC",
        "carrier": "EI",
        "carrier_name": "Aer Lingus",
        "alliance": "None",  # EI is not in a global alliance (IAG subsidiary)
        "carrier_type": "Full Service / Hybrid",
        "route_type": "Hub Longhaul",
        "hub_airport": "DUB",
        "hub_status": "Secondary Hub",  # smaller than LHR/AMS/FRA
        "frequency": 4,
        "aircraft": "A330-200",
        "seats_per_flight": 265,
        "annual_seats": 110240,  # 265  4/wk  52wk  2 sectors
        "departure_time_home": "15:50",
        "arrival_time_dest": "18:55",
        "departure_time_dest": "20:45",
        "arrival_time_home": "14:45",
        "forecast_year": 2025,
        "data_vintage": "Summer 2023 OAG",
        "existing_service": False,  # new route  never operated

        # DEMAND
        "p2p_base_demand": 85863,  # 100% indirect currently
        "p2p_growth_rate": 0.022,  # 2.2% compound
        "p2p_after_growth": 87752,
        "p2p_stimulation": 1.30,  # HIGH  virgin nonstop market
        "p2p_after_stimulation": 114078,
        "p2p_capture_rate": 0.40,  # HIGH  only direct service
        "p2p_forecast": 45631,
        "p2p_business_split": 0.50,
        "p2p_visitor_resident_split": (0.58, 0.42),
        "p2p_primary_secondary_contested": (0.81, 0.13, 0.06),

        # CONNECTING @ HOME HUB (DUB)
        "cnx_home_num_cities": 145,
        "cnx_home_top_cities": {
            "LON": 487434, "PAR": 219418, "BCN": 93151, "AMS": 89594,
            "TLV": 86047, "FRA": 84788, "ROM": 65706, "MUC": 56230,
        },
        "cnx_home_direct_comp_demand": 487434,
        "cnx_home_no_direct_comp_demand": 1373458,
        "cnx_home_direct_comp_qsi_share": 0.0320,
        "cnx_home_no_direct_comp_qsi_share": 0.0106,
        "cnx_home_qsi_share_blended": 0.0162,
        "cnx_home_forecast": 30767,
        "cnx_home_ceiling": 0.85,

        # QSI SCORES (DUB side, top markets)
        "qsi_scores_home": {
            "LON": 0.036106, "PAR": 0.012290, "BCN": 0.007754,
            "AMS": 0.017761, "FRA": 0.006020, "ROM": 0.013182,
            "MAN": 0.092073, "EDI": 0.025589, "GLA": 0.025876,
        },

        # CONNECTING @ DEST (SJC)
        "cnx_dest_num_cities": 25,
        "cnx_dest_top_cities": {
            "LAX": 143948, "SEA": 93703, "LAS": 81830, "PDX": 24918,
        },
        "cnx_dest_qsi_share_blended": 0.0027,
        "cnx_dest_discount_factor": 0.75,
        "cnx_dest_forecast": 1167,
        "cnx_dest_ceiling": 0.85,

        # QSI SCORES (SJC side, top markets)
        "qsi_scores_dest": {
            "LAX": 0.010109, "SEA": 0.008277, "PDX": 0.005410,
            "SLC": 0.005151, "SAN": 0.001649, "PHX": 0.001020,
        },

        # TOTALS
        "grand_total_forecast": 77565,
        "load_factor": 0.704,

        # CALIBRATION
        "factor_up": 1.0,  # no Sabre undercount adjustment
        "premium_adjustment": 1.0,
        "qsi_adjustment": 1.0,  # NO manual QSI override  model accepted raw
        "calibration_factors_by_market": {
            "description": "Clean case  QSI model accepted without adjustment",
        },

        # COMPETITIVE CONTEXT
        "competitive_landscape": {
            "direct_services": "None  new route",
            "key_indirect_hubs": "LHR/BA, FRA/LH, ATL/DL, IAD/UA, PHL/AA, EWR/UA",
            "indirect_share_via_direct_svc": 0.337,  # 33.7% via LGW/LHR
        },

        # CONTEXT
        "notes": [
            "New route  no DUB-SJC service has ever operated",
            "QSI model accepted raw (factor = 1.0)  no expert override needed",
            "Key expert judgment in stimulation (1.30) and capture rate (40%)",
            "265 seats confirmed  416 appearing in some sheets is a labelling error",
            "DUB is a secondary hub  much smaller feed than LHR",
            "P2P segments (China/US Business/Leisure) show zeros  not populated",
            "EI capacity share of Bay-DUB capacity: 31.2%",
            "EI SJC-DUB P2P share of SJC service area: 37.0%",
        ],
    },

    # =========================================================================
    # CASE 4: EI DUB-SJC 7x Daily (Aer Lingus Dublin - San Jose)
    # =========================================================================
    {
        "route_id": "EI_DUB_SJC_7x",
        "origin": "DUB",
        "destination": "SJC",
        "origin_city": "DUB",
        "destination_city": "SJC",
        "carrier": "EI",
        "carrier_name": "Aer Lingus",
        "alliance": "None",
        "carrier_type": "Full Service / Hybrid",
        "route_type": "Hub Longhaul",
        "hub_airport": "DUB",
        "hub_status": "Secondary Hub",
        "frequency": 7,
        "aircraft": "A330-200",
        "seats_per_flight": 265,
        "annual_seats": 192920,  # 265  7/wk  52wk  2
        "departure_time_home": "15:50",
        "departure_time_dest": "20:45",
        "forecast_year": 2025,
        "data_vintage": "Summer 2023 OAG",
        "existing_service": False,  # hypothetical daily variant

        # DEMAND
        "p2p_base_demand": 85863,
        "p2p_stimulation": 1.00,  # NO stimulation  analyst note says "direct service operated in 2019" but John confirms NO service ever operated. Possibly treating as if market already stimulated at daily freq
        "p2p_capture_rate": 0.33,
        "p2p_forecast": 37719,

        # CONNECTING @ DUB
        "cnx_home_direct_comp_qsi_share": 0.0555,
        "cnx_home_no_direct_comp_qsi_share": 0.0184,
        "cnx_home_qsi_share_blended": 0.0281,
        "cnx_home_forecast": 53548,
        "cnx_home_ceiling": 0.85,

        # QSI SCORES (DUB side  higher than 4x due to frequency)
        "qsi_scores_home": {
            "LON": 0.062626, "PAR": 0.021302, "BCN": 0.013698,
            "AMS": 0.029353,
        },

        # CONNECTING @ SJC
        "cnx_dest_forecast": 0,  # deliberately zeroed by analyst
        "cnx_dest_discount_factor": 0.75,

        # TOTALS
        "grand_total_forecast": 91267,
        "load_factor": 0.473,  # very low  daily is over-capacity

        # CALIBRATION
        "factor_up": 1.0,
        "qsi_adjustment": 1.0,

        # CONTEXT
        "notes": [
            "Daily variant of same route  compare with 4x weekly case",
            "47.3% LF at daily = commercially not viable",
            "+75% capacity yields only +18% total pax  severe diminishing returns",
            "Connecting QSI scales near-linearly with frequency (1.62%  2.81%)",
            "P2P capture DROPS (40%  33%) despite higher frequency",
            "SJC connecting deliberately zeroed  no hub function",
            "Stimulation=1.0 despite being a new route  ANOMALY flagged by John",
            "Forecast notes reference 'SJC projected traffic performance in 2023 vs 2019'",
        ],
    },

    # =========================================================================
    # CASE 5: AF CDG-SJC (Air France Paris CDG - San Jose)
    # =========================================================================
    {
        "route_id": "AF_CDG_SJC",
        "origin": "CDG",
        "destination": "SJC",
        "origin_city": "PAR",
        "destination_city": "SJC",
        "carrier": "AF",
        "carrier_name": "Air France",
        "alliance": "SkyTeam",
        "carrier_type": "Full Service",
        "route_type": "Hub Longhaul",
        "hub_airport": "CDG",
        "hub_status": "Major Hub",  # CDG is AF's primary hub
        "frequency": 5,  # Mon Wed Fri Sat Sun
        "aircraft": "B787-9",
        "seats_per_flight": 276,  # config 225 ECO / 21 PY / 30 J
        "annual_seats": 143520,
        "departure_time_home": "10:20",
        "arrival_time_dest": "12:45",
        "departure_time_dest": "14:45",
        "arrival_time_home": "10:40",
        "flight_time_outbound": "11:25",
        "flight_time_inbound": "10:55",
        "forecast_year": 2022,  # Jul 2021 - Jun 2022
        "data_vintage": "Sabre MI Jan-Dec 2018, OAG Aug 2019",
        "existing_service": False,  # new route

        # DEMAND
        "p2p_base_demand": 182449,
        "p2p_growth_rate": 0.0988,  # ~9.9% compound to forecast year
        "p2p_after_growth": 200475,
        "p2p_stimulation": 1.092,  # modest  already well-connected via hubs
        "p2p_after_stimulation": 219011,
        "p2p_capture_rate": 0.248,  # 25% for business/primary, 20% contested
        "p2p_forecast": 54421,
        "p2p_business_split": 0.60,  # 60% business  Silicon Valley tech
        "p2p_visitor_resident_split": (0.43, 0.57),
        "p2p_primary_secondary_contested": (0.622, 0.299, 0.079),

        # P2P BY SEGMENT (detailed)
        "p2p_segments": {
            "france_business": {
                "base": 47072, "growth": 0.10, "stimulation": 1.10,
                "capture": 0.25, "forecast": 14239,
            },
            "france_leisure_primary": {
                "base": 19534, "growth": 0.097, "stimulation": 1.10,
                "capture": 0.25, "forecast": 5893,
            },
            "france_leisure_secondary": {
                "base": 9368, "growth": 0.097, "stimulation": 1.05,
                "capture": 0.25, "forecast": 2698,
            },
            "france_leisure_contested": {
                "base": 2479, "growth": 0.097, "stimulation": 1.05,
                "capture": 0.20, "forecast": 571,
            },
            "us_business": {
                "base": 62398, "growth": 0.10, "stimulation": 1.10,
                "capture": 0.25, "forecast": 18875,
            },
            "us_leisure_primary": {
                "base": 25894, "growth": 0.097, "stimulation": 1.10,
                "capture": 0.25, "forecast": 7812,
            },
            "us_leisure_secondary": {
                "base": 12418, "growth": 0.097, "stimulation": 1.05,
                "capture": 0.25, "forecast": 3576,
            },
            "us_leisure_contested": {
                "base": 3286, "growth": 0.097, "stimulation": 1.05,
                "capture": 0.20, "forecast": 757,
            },
        },

        # CONNECTING @ HOME HUB (CDG)
        "cnx_home_direct_comp_demand": 558078,
        "cnx_home_no_direct_comp_demand": 1624649,
        "cnx_home_direct_comp_qsi_share": 0.00502,
        "cnx_home_no_direct_comp_qsi_share": 0.03639,
        "cnx_home_qsi_share_blended": 0.02837,
        "cnx_home_forecast": 66570,
        "cnx_home_ceiling": 0.85,
        "cnx_home_pct_of_total": 0.533,  # 53% of total  CDG is a proper hub

        # QSI SCORES (CDG side)
        "qsi_scores_home": {
            "LON": 0.003, "DEL": 0.009367, "BLR": 0.020305,
            "FRA": 0.021581, "BCN": 0.046594, "AMS": 0.027587,
            "DUB": 0.018222, "TLV": 0.032641, "BER": 0.028540,
        },

        # CONNECTING @ SJC
        "cnx_dest_direct_comp_demand": 714205,
        "cnx_dest_no_direct_comp_demand": 219736,
        "cnx_dest_qsi_share_blended": 0.00392,
        "cnx_dest_forecast": 3880,
        "cnx_dest_ceiling": 0.85,

        # QSI SCORES (SJC side)
        "qsi_scores_dest": {
            "LAX": 0.014, "SEA": 0.015, "SAN": 0.015,
            "LAS": 0.005357, "SLC": 0.007536, "AUS": 0.003698,
        },

        # TOTALS
        "grand_total_forecast": 124872,
        "load_factor": 0.870,  # 87%  high, suggests daily could work

        # CALIBRATION
        "factor_up": 1.0,
        "premium_adjustment": 1.0,
        "qsi_adjustment": 1.0,  # NO manual QSI override  model accepted raw

        # TRAFFIC MIX
        "traffic_mix": {
            "p2p_pct": 0.436,  # 43.6%
            "cnx_home_pct": 0.533,  # 53.3%  CDG hub connecting dominates
            "cnx_dest_pct": 0.031,  # 3.1%
        },

        # CONTEXT
        "notes": [
            "New route  no existing CDG-SJC service",
            "QSI accepted raw (factor = 1.0)  third consecutive clean case",
            "CDG connecting is 53% of total  proper hub carrier dynamics",
            "P2P capture 25% is lower than EI DUB (40%)  more competing hubs",
            "Stimulation only 1.09  market already well-served indirectly",
            "87% LF at 5x weekly  daily could be commercially viable",
            "60% business split reflects Silicon Valley tech demand to Paris",
            "Growth rates: Business 2.8% CAGR, Leisure 2.7% CAGR, Cnx@CDG 2.1%",
            "QSI WEIGHTINGS sheet contains Asian hub data (TPE/HKG/ICN)  workbook reused",
            "Demand settings sheet has Chinese city catchment data  prior analysis residue",
            "Proxy analysis noted on schedule  times may not be confirmed AF schedule",
        ],
    },

    # =========================================================================
    # CASE 6: KL AMS-SJC (KLM Amsterdam - San Jose)
    # Source files verified: Chat 42
    # =========================================================================
    {
        "route_id": "KL_AMS_SJC",
        "origin": "AMS",
        "destination": "SJC",
        "origin_city": "AMS",
        "destination_city": "SJC",
        "carrier": "KL",
        "carrier_name": "KLM Royal Dutch Airlines",
        "alliance": "SkyTeam",
        "carrier_type": "Full Service",
        "route_type": "Hub Longhaul",
        "hub_airport": "AMS",
        "hub_status": "Major Hub",
        "frequency": 4,  # 4x weekly
        "aircraft": "B787-9",
        "seats_per_flight": 294,  # 30J + 48PY + 216Y
        "seat_config": {"J": 30, "PY": 48, "Y": 216},
        "annual_departures": 416,  # 208 each way
        "annual_seats": 122304,
        "block_time": "11:00/10:30",
        "distance_km": 8785,
        "distance_mi": 5459,
        "forecast_year": 2021,
        "data_vintage": "Sabre 2018, OAG Aug 2019",
        "analysis_date": "29-Jul-2019",
        "analyst": "JZ",
        "existing_service": False,  # new route proposal

        # DEMAND  Year 1
        "p2p_forecast": 36308,
        "p2p_pct": 0.354,
        "p2p_cabin_split": {"Y": 0.84, "PY": 0.08, "J": 0.08},
        "p2p_cagr": 0.03,

        "cnx_home_forecast": 63155,  # connecting at AMS
        "cnx_home_pct": 0.616,
        "cnx_home_cities": 110,
        "cnx_home_top_15": {
            "DEL": 7386, "BER": 4688, "MUC": 3481, "PAR": 2710, "CPH": 2545,
            "MOW": 1990, "BUD": 1944, "BCN": 1898, "DUB": 1777, "DUS": 1646,
            "ROM": 1607, "DXB": 1604, "ZRH": 1554, "STO": 1536, "OSL": 1228,
        },
        "cnx_home_yoy_growth": 0.045,

        "cnx_dest_forecast": 3022,  # connecting at SJC
        "cnx_dest_pct": 0.029,
        "cnx_dest_cities": 11,
        "cnx_dest_all": {
            "LAX": 1370, "SAN": 495, "SEA": 377, "LAS": 377,
            "PDX": 116, "TUS": 64, "RNO": 61, "SNA": 58,
            "BOI": 58, "SLC": 45, "BUR": 2,
        },
        "cnx_dest_yoy_growth": 0.028,

        "grand_total_forecast": 102485,
        "load_factor": 0.838,
        "yr2_total": 106468,
        "yr2_lf": 0.871,
        "yr3_total": 110614,
        "yr3_lf": 0.904,

        # REVENUE  Year 1
        "pax_revenue": 82948799,
        "cargo_revenue": 8736000,
        "ancillary_revenue": 2303863,
        "total_revenue": 93988662,
        "avg_ow_fare": 809.37,
        "prask": 7.72,
        "trask": 8.75,
        "ancillary_per_pax": 22.48,

        # CARGO
        "cargo_capacity_kg": 20000,
        "cargo_lf": 0.60,
        "cargo_yield_per_kg": 1.75,
        "cargo_yield_growth": 0.05,

        # SPILL ANALYSIS
        "spill_c_factor": 1.75,
        "spill_seats": 9797,
        "spill_revenue": 8424790,
        "demand_before_spill": 112282,  # approx: 102485 + 9797

        # CALIBRATION
        "qsi_adjustment": None,  # QSI computed externally, not stored in this workbook
        "factor_up": None,
        "calibration_factors_by_market": {
            "description": "Revenue Forecast template  QSI scores fed in from external workbooks. "
                           "No QSI_AMS_SJC file uploaded, so individual city QSI shares not available. "
                           "Calibration appears embedded in the QSI computation stage, not in the revenue template.",
        },

        # FARES
        "avg_fares": {
            "total_avg_ow": 809.37,
            "p2p": {"Y": 633.10, "PY": 1426.18, "J": 2693.90},
            "cnx_avg": {"Y": 408.73, "PY": 2377.14, "J": 2748.70},
            "fare_weight": 0.85,  # all fares discounted to 85% of raw
        },

        # WORKBOOK RESIDUE
        "residue": {
            "rows_181_184": "Prior analysis: cnx@HKG 43,669 pax, cnx@FRA 188,704 pax, Local 49,593 pax  different route study",
        },

        # CONTEXT
        "notes": [
            "New route  no existing KL AMS-SJC service at time of analysis",
            "Revenue Forecast template (different from QSI calibration template used for BA/AF cases)",
            "Companion to AF CDG-SJC analysis  both done Jul/Aug 2019 for SkyTeam assessment to SJC",
            "Very heavy connecting traffic (61.6%)  typical of AMS mega-hub network",
            "Delhi is #1 connecting city (7,386 pax)  India diaspora to Silicon Valley via AMS",
            "110 AMS connecting cities vs 135 for AF CDG  AMS has slightly fewer but still massive European feed",
            "SJC connecting mirrors AF case: LAX dominant, same 11 US cities",
            "Spill analysis present  demand (~112k) exceeds capacity (122k seats), 9,797 seats spilled",
            "Yr3 LF reaches 90.4%  frequency increase to 5x or daily would be commercially justified",
            "Fare weighting at 0.85 across all markets  standard Avia discount from raw Sabre fares",
            "P2P cabin split 84% Y reflects less premium mix than AF CDG-SJC (which was 60% business)",
            "Cargo revenue significant at $8.7M (9.3% of total)  KLM-Martinair cargo strength",
            "Same analyst (JZ), same OAG vintage (Aug 2019), same Sabre vintage (2018) as AF CDG-SJC",
            "Workbook contains residue from prior analysis (HKG/FRA hub data) in Revenue Fcast rows 181-184",
        ],
    },

    # =========================================================================
    # CASE 7: CI TPE-SJC (China Airlines, 4x Weekly, A350-900)  VERIFIED Chat 43
    # =========================================================================
    {
        "route_id": "CI_TPE_SJC",
        "origin": "TPE",
        "destination": "SJC",
        "carrier": "CI",
        "carrier_name": "China Airlines",
        "alliance": "SkyTeam",
        "route_type": "Hub carrier long-haul",
        "hub_status": "Major Hub (TPE)",
        "frequency": 4,  # 4x weekly
        "operating_days": "1 345 7",
        "aircraft": "A350-900",
        "seats_per_flight": 306,
        "config": "32/31/243",  # Biz/PY/Eco
        "annual_capacity": 127296,  # 306 seats  4 flights  2 directions  ~52 weeks
        "analyst": "JZ",
        "analysis_date": "Jul 2019",
        "sabre_vintage": "Jan-Dec 2018",
        "forecast_year": 2022,
        "schedule_departure": "18:30 TPE  15:00 SJC",
        "schedule_return": "17:25 SJC  21:45+1 TPE",

        # P2P DEMAND
        "p2p_base_demand": 142499,  # total both directions
        "p2p_visitors_share": 0.40,  # 40% visitors (Taiwan origin)
        "p2p_residents_share": 0.60,  # 60% residents (US origin)
        "p2p_business_share": 0.80,  # 80% of visitors are business
        "p2p_leisure_share": 0.20,  # 20% of visitors are leisure
        "p2p_growth_business": 0.125,  # 12.5% CAGR to 2022 (3.4% annual)
        "p2p_growth_leisure": 0.097,  # 9.7% CAGR to 2022 (2.7% annual)
        "p2p_demand_2022": 159513,  # after growth
        "p2p_stimulation": 1.10,  # business and primary leisure
        "p2p_stimulation_secondary": 1.05,  # secondary and contested leisure
        "p2p_demand_after_stim": 175181,
        "p2p_capture_rate": 0.299,  # blended ~30%
        "p2p_capture_business": 0.30,
        "p2p_capture_primary": 0.30,
        "p2p_capture_secondary": 0.30,
        "p2p_capture_contested": 0.20,
        "p2p_forecast": 52330,
        "p2p_pct_of_total": 0.464,  # 46.4%

        # CONNECTING AT TPE (HOME HUB)
        "cnx_home_demand_pool": 1847047,
        "cnx_home_cities": 30,
        "cnx_home_qsi_share_blended": 0.0296,  # 2.96%
        "cnx_home_forecast": 54744,
        "cnx_home_pct_of_total": 0.485,  # 48.5%
        "cnx_home_top_cities": {
            "MNL": {"demand": 249936, "qsi_share": 0.0622, "pax": 15546},
            "SGN": {"demand": 185015, "qsi_share": 0.0556, "pax": 10291},
            "DEL": {"demand": 205572, "qsi_share": 0.0351, "pax": 7225},
            "HKG": {"demand": 111056, "qsi_share": 0.0422, "pax": 4690},
            "HAN": {"demand": 32808, "qsi_share": 0.1092, "pax": 3583},
        },

        # CONNECTING AT SJC (DESTINATION)
        "cnx_dest_demand_pool": 769212,
        "cnx_dest_cities": 8,
        "cnx_dest_qsi_share_blended": 0.00746,  # 0.75%
        "cnx_dest_forecast": 5739,
        "cnx_dest_pct_of_total": 0.051,  # 5.1%

        # GRAND TOTAL
        "grand_total_forecast": 112813,
        "load_factor": 0.886,  # 88.6% (Finalised version)
        "pdew": 271.2,

        # CALIBRATION
        "qsi_adjustment": 1.0,  # all three QSI adjustments = 1.0
        "factor_up": 1.0,
        "premium_factor": 1.0,
        "calibration_factors_by_market": {
            "description": "All three adjustment factors (Factor Up, Actual Factor Up, Premium, QSI) = 1.0. "
                           "Model accepted raw for this new route proposal.",
        },

        # TWO VERSIONS IN WORKBOOK
        "version_notes": {
            "Forecast_sheet": "777-300ER, 323 seats, LF=84.1%  abandoned working version",
            "Forecast_Finalised": "A350-900, 306 seats, LF=88.6%  delivered version",
            "lesson": "Same pattern as AF CDG-SJC: workbook contains abandoned aircraft option",
        },

        # CI SFO PROXY DATA (existing CI SFO service benchmarked)
        "sfo_proxy": {
            "CI_SFO_total": 235967,
            "CI_SFO_cnx_tpe": 139423,  # 59.1%
            "CI_SFO_cnx_sfo": 15797,   # 6.7%
            "CI_SFO_local": 80747,      # 34.2%
            "BR_SFO_total": 390834,
            "BR_SFO_cnx_tpe": 186457,  # 47.7%
            "BR_SFO_local": 173014,    # 44.3%
            "notes": "CI and EVA Air (BR) both serve TPE-SFO. CI SFO used as benchmark for SJC traffic mix.",
        },

        # CANNIBALISATION ANALYSIS
        "cannibalisation": {
            "description": "Separate workbook analyses impact of new CI TPE-SJC on existing CI TPE-SFO service",
            "top_markets_affected": {
                "MNL": {"sfo_without_sjc": 0.051, "sfo_with_sjc": 0.040, "change": -0.216},
                "SGN": {"sfo_without_sjc": 0.115, "sfo_with_sjc": 0.110, "change": -0.043},
                "DEL": {"sfo_without_sjc": 0.015, "sfo_with_sjc": 0.014, "change": -0.067},
                "HKG": {"sfo_without_sjc": 0.168, "sfo_with_sjc": 0.148, "change": -0.119},
                "HAN": {"sfo_without_sjc": 0.089, "sfo_with_sjc": 0.084, "change": -0.056},
            },
            "net_impact": "New SJC service adds total pax across both Bay Area airports but cannibalises CI SFO share by 4-22% per market",
            "lesson": "Largest cannibalisation in markets where SJC offers genuinely shorter ground journey for Silicon Valley pax (MNL -22%, HKG -12%)",
        },

        # CONNECTING INFO (residue from template  actually LHR one-stop data)
        "connecting_info_note": "Conneting Info sheet contains LHR one-stop connection data (BA/UA/VS via LHR)  "
                               "template residue, not TPE connecting data",

        # CONTEXT
        "notes": [
            "New route  CI did not operate TPE-SJC at time of analysis (Jul 2019)",
            "Part of broader SkyTeam SJC assessment alongside AF CDG-SJC and KL AMS-SJC",
            "Same analyst (JZ), same OAG/Sabre vintage as AF and KL cases",
            "Two aircraft versions tested: 777-300ER (abandoned at 84% LF) and A350-900 (delivered at 89% LF)",
            "QSI adjustment = 1.0  confirms pattern: new route proposals accepted raw",
            "P2P capture 30%  between AF CDG-SJC (25%) and EI DUB-SJC (40%), reflecting moderate indirect competition",
            "Stimulation 1.10 for business/primary, 1.05 for secondary/contested  standard for well-served indirect market",
            "TPE connecting dominated by SE Asian markets (MNL, SGN, HAN)  different from European hub profiles",
            "High business share (80% of Taiwan visitors) reflects semiconductor/tech bilateral trade",
            "Revenue template NOT populated (Key Market Metrics has #REF errors, Revenue Forecast empty)",
            "Demand settings sheet shows detailed SJC catchment analysis  SJC vs SFO traffic splits per Chinese city",
            "Demand settings note: '*** should really do Gaussian curve'  analyst flagging area for improvement",
            "Cannibalisation analysis done separately  new SJC service steals 4-22% from CI existing SFO service per market",
        ],
    },

    # =========================================================================
    # CASE: Korean Air ICN-SJC (KE_ICN_SJC_7x)
    # =========================================================================
    {
        "route_id": "KE_ICN_SJC_7x",
        "origin": "ICN",
        "destination": "SJC",
        "origin_city": "SEL",
        "destination_city": "SJC",
        "carrier": "KE",
        "carrier_name": "Korean Air",
        "alliance": "SkyTeam",
        "carrier_type": "Full Service",
        "route_type": "Hub Longhaul",
        "hub_airport": "ICN",
        "hub_status": "Major Hub",
        "frequency": 7,
        "aircraft": "B777-300ER",
        "seats_per_flight": 338,
        "annual_seats": 246064,
        "departure_time_home": None,
        "departure_time_dest": None,
        "forecast_year": 2025,
        "data_vintage": "2019 base, 12.7% CAGR growth",
        "existing_service": False,
        "p2p_base_demand": 184400,
        "p2p_growth_rate": 0.127,
        "p2p_after_growth": 207800,
        "p2p_stimulation": 1.27,
        "p2p_after_stimulation": 262800,
        "p2p_capture_rate": 0.195,
        "p2p_forecast": 51200,
        "p2p_business_split": 0.8,
        "cnx_home_total_demand": 3571900,
        "cnx_home_direct_comp_demand": 2799700,
        "cnx_home_no_direct_comp_demand": 772200,
        "cnx_home_direct_comp_qsi_share": 0.021,
        "cnx_home_no_direct_comp_qsi_share": 0.08,
        "cnx_home_qsi_share_blended": 0.034,
        "cnx_home_forecast": 121500,
        "cnx_home_num_cities": None,
        "cnx_home_top_cities": {
            "TYO": {'demand': 415461, 'qsi': 0.165, 'forecast': 25316},
            "SGN": {'demand': 211197, 'qsi': 0.087, 'forecast': 18415},
            "MNL": {'demand': 454876, 'qsi': 0.05, 'forecast': 10369},
            "BKK": {'demand': 172463, 'qsi': 0.06, 'forecast': 10317},
            "SIN": {'demand': 245532, 'qsi': 0.083, 'forecast': 7017},
            "SHA": {'demand': 354202, 'qsi': 0.042, 'forecast': 5796},
        },
        "cnx_home_ceiling": 0.85,
        "cnx_dest_total_demand": 2128500,
        "cnx_dest_direct_comp_demand": 1910300,
        "cnx_dest_no_direct_comp_demand": 218100,
        "cnx_dest_direct_comp_qsi_share": 0.003,
        "cnx_dest_no_direct_comp_qsi_share": 0.026,
        "cnx_dest_qsi_share_blended": 0.005,
        "cnx_dest_forecast": 11600,
        "cnx_dest_discount_factor": 0.75,
        "cnx_dest_top_cities": {
            "LAX": {'demand': 749483, 'qsi': 0.036, 'forecast': 3907},
            "SAN": {'demand': 27415, 'qsi': 0.093, 'forecast': 2558},
            "LAS": {'demand': 105584, 'qsi': 0.03, 'forecast': 1293},
            "PDX": {'demand': 28893, 'qsi': 0.027, 'forecast': 775},
        },
        "grand_total_forecast": 184400,
        "load_factor": 0.749,
        "qsi_adjustment": 1.0,
        "factor_up": 1.0,
        "calibration_factors_by_market": {
            "description": "Model accepted raw  new route proposal",
        },
        "notes": [
            "Korean Air daily service proposal to SJC",
            "High growth rate (12.7%) reflects post-pandemic recovery compound",
            "Very high stimulation (1.27)  new direct service to established market",
            "ICN is a major hub  connecting traffic 66% of total (121.5k of 184.4k)",
            "TYO dominates connecting at 25.3k  Japan-SJC tech corridor",
            "SE Asian markets (SGN, MNL, BKK) significant  diaspora + tech talent flows",
            "Low P2P capture (19.5%) reflects strong existing indirect competition",
            "Paired with 5x weekly variant for frequency comparison",
            "74.9% LF at daily with 338-seat widebody  marginal commercially",
        ],
    },

    # =========================================================================
    # CASE: Korean Air ICN-SJC (KE_ICN_SJC_5x)
    # =========================================================================
    {
        "route_id": "KE_ICN_SJC_5x",
        "origin": "ICN",
        "destination": "SJC",
        "origin_city": "SEL",
        "destination_city": "SJC",
        "carrier": "KE",
        "carrier_name": "Korean Air",
        "alliance": "SkyTeam",
        "carrier_type": "Full Service",
        "route_type": "Hub Longhaul",
        "hub_airport": "ICN",
        "hub_status": "Major Hub",
        "frequency": 5,
        "aircraft": "A350-900",
        "seats_per_flight": 311,
        "annual_seats": 161720,
        "departure_time_home": None,
        "departure_time_dest": None,
        "forecast_year": 2025,
        "data_vintage": "2019 base, 12.7% CAGR growth",
        "existing_service": False,
        "p2p_base_demand": 184400,
        "p2p_growth_rate": 0.127,
        "p2p_after_growth": 207800,
        "p2p_stimulation": 1.27,
        "p2p_after_stimulation": 262800,
        "p2p_capture_rate": 0.195,
        "p2p_forecast": 51200,
        "cnx_home_total_demand": 3571900,
        "cnx_home_direct_comp_demand": 2799700,
        "cnx_home_no_direct_comp_demand": 772200,
        "cnx_home_direct_comp_qsi_share": 0.018,
        "cnx_home_no_direct_comp_qsi_share": 0.04,
        "cnx_home_qsi_share_blended": 0.023,
        "cnx_home_forecast": 82000,
        "cnx_dest_total_demand": 2128500,
        "cnx_dest_direct_comp_qsi_share": 0.002,
        "cnx_dest_no_direct_comp_qsi_share": 0.018,
        "cnx_dest_qsi_share_blended": 0.004,
        "cnx_dest_forecast": 7600,
        "cnx_dest_discount_factor": 0.75,
        "grand_total_forecast": 140858,
        "load_factor": 0.871,
        "qsi_adjustment": 1.0,
        "factor_up": 1.0,
        "calibration_factors_by_market": {
            "description": "Model accepted raw  new route proposal",
        },
        "notes": [
            "5x weekly variant  compare with 7x daily case",
            "Same P2P forecast (51.2k)  capture rate unchanged at reduced frequency",
            "ICN connecting drops from 121.5k to 82.0k (-33%) at -29% frequency",
            "SJC connecting drops from 11.6k to 7.6k (-34%)",
            "LF improves dramatically: 74.9%  87.1%  commercially viable",
            "Smaller aircraft (A350-900 311 seats vs 777-300ER 338 seats) also helps LF",
            "This is the delivered recommendation  5x with A350 preferred over daily 777",
        ],
    },

    # =========================================================================
    # CASE: Singapore Airlines SIN-SJC (SQ_SIN_SJC)
    # =========================================================================
    {
        "route_id": "SQ_SIN_SJC",
        "origin": "SIN",
        "destination": "SJC",
        "origin_city": "SIN",
        "destination_city": "SJC",
        "carrier": "SQ",
        "carrier_name": "Singapore Airlines",
        "alliance": "Star Alliance",
        "carrier_type": "Full Service",
        "route_type": "Hub Longhaul",
        "hub_airport": "SIN",
        "hub_status": "Major Hub",
        "frequency": 4,
        "aircraft": "A350-900ULR",
        "seats_per_flight": 161,
        "annual_seats": 66976,
        "departure_time_home": None,
        "departure_time_dest": None,
        "forecast_year": 2025,
        "data_vintage": "2019 base",
        "existing_service": False,
        "p2p_base_demand": 59300,
        "p2p_growth_rate": 0.127,
        "p2p_after_growth": 66900,
        "p2p_stimulation": 1.3,
        "p2p_after_stimulation": 86900,
        "p2p_capture_rate": 0.35,
        "p2p_forecast": 30400,
        "cnx_home_total_demand": 1444100,
        "cnx_home_direct_comp_demand": 0,
        "cnx_home_no_direct_comp_demand": 1444100,
        "cnx_home_direct_comp_qsi_share": 0,
        "cnx_home_no_direct_comp_qsi_share": 0.016,
        "cnx_home_qsi_share_blended": 0.016,
        "cnx_home_forecast": 23100,
        "cnx_home_num_cities": None,
        "cnx_dest_total_demand": 722700,
        "cnx_dest_direct_comp_demand": 408500,
        "cnx_dest_no_direct_comp_demand": 314200,
        "cnx_dest_direct_comp_qsi_share": 0.001,
        "cnx_dest_no_direct_comp_qsi_share": 0.002,
        "cnx_dest_qsi_share_blended": 0.002,
        "cnx_dest_forecast": 1200,
        "cnx_dest_discount_factor": 0.75,
        "cnx_dest_top_cities": {
            "PDX": {'demand': 14118, 'qsi': 0.016, 'forecast': 229},
            "SEA": {'demand': 47827, 'qsi': 0.006, 'forecast': 222},
            "LAX": {'demand': 166433, 'qsi': 0.002, 'forecast': 200},
            "LAS": {'demand': 20520, 'qsi': 0.006, 'forecast': 129},
        },
        "grand_total_forecast": 54778,
        "load_factor": 0.818,
        "qsi_adjustment": 1.0,
        "factor_up": 1.0,
        "calibration_factors_by_market": {
            "description": "Model accepted raw  new route proposal",
        },
        "notes": [
            "Ultra-long-range variant (A350-900ULR) with only 161 seats",
            "SIN-SJC is one of the longest routes in the world",
            "P2P dominates (55%) because SIN connecting pool is smaller for US-bound traffic",
            "1.30 stimulation  high for new direct on well-served indirect market",
            "35% capture rate  high due to limited direct alternatives",
            "SJC connecting negligible (1.2k)  SIN routes don't feed US domestic connections",
            "SIN connecting only 23.1k  1.6% QSI share, lowest of major hubs in library",
            "ULR configuration limits capacity but enables route viability at 81.8% LF",
            "Interesting: P2P heavy despite SIN being a major hub  geography matters",
        ],
    },

    # =========================================================================
    # CASE: Cathay Pacific HKG-SJC (CX_HKG_SJC)
    # =========================================================================
    {
        "route_id": "CX_HKG_SJC",
        "origin": "HKG",
        "destination": "SJC",
        "origin_city": "HKG",
        "destination_city": "SJC",
        "carrier": "CX",
        "carrier_name": "Cathay Pacific",
        "alliance": "OneWorld",
        "carrier_type": "Full Service",
        "route_type": "Hub Longhaul",
        "hub_airport": "HKG",
        "hub_status": "Major Hub",
        "frequency": 4,
        "aircraft": "A350-900",
        "seats_per_flight": 280,
        "annual_seats": 116480,
        "departure_time_home": None,
        "departure_time_dest": None,
        "forecast_year": 2028,
        "data_vintage": "Jul 2024-Jun 2025 base, 9.7% CAGR 3yrs",
        "existing_service": False,
        "p2p_base_demand": 66500,
        "p2p_growth_rate": 0.321,
        "p2p_after_growth": 87837,
        "p2p_stimulation": 1.4,
        "p2p_after_stimulation": 122971,
        "p2p_capture_rate": 0.35,
        "p2p_forecast": 43040,
        "p2p_business_split": 0.7,
        "cnx_home_total_demand": 1870000,
        "cnx_home_direct_comp_demand": 0,
        "cnx_home_no_direct_comp_demand": 1870000,
        "cnx_home_no_direct_comp_qsi_share": 0.02542,
        "cnx_home_qsi_share_blended": 0.02542,
        "cnx_home_forecast": 47536,
        "cnx_home_num_cities": 37,
        "cnx_home_top_cities": {
            "BKK": {'forecast': 9177},
            "MNL": {'forecast': 8093},
            "SGN": {'forecast': 5188},
            "DEL": {'forecast': 4741},
            "SIN": {'forecast': 3800},
            "KUL": {'forecast': 2795},
            "PVG": {'forecast': 2598},
            "BOM": {'forecast': 2415},
            "PEK": {'forecast': 1940},
        },
        "cnx_home_ceiling": 0.85,
        "cnx_dest_total_demand": 901900,
        "cnx_dest_direct_comp_demand": 518000,
        "cnx_dest_no_direct_comp_demand": 383900,
        "cnx_dest_direct_comp_qsi_share": 0.001351,
        "cnx_dest_no_direct_comp_qsi_share": 0.009919,
        "cnx_dest_qsi_share_blended": 0.005,
        "cnx_dest_forecast": 4508,
        "cnx_dest_discount_factor": 0.75,
        "cnx_dest_num_cities": 31,
        "grand_total_forecast": 95084,
        "load_factor": 0.816,
        "qsi_adjustment": 1.0,
        "factor_up": 1.0,
        "calibration_factors_by_market": {
            "description": "Model accepted raw  new route proposal",
        },
        "notes": [
            "Cathay Pacific to Silicon Valley  business + VFR/Chinese diaspora demand",
            "1.40 stimulation is highest in library  completely new direct market",
            "HKG connecting dominated by SE Asian cities (BKK #1, MNL #2, SGN #3)",
            "India also significant (DEL #4, BOM #8)  India-SJC tech corridor via HKG",
            "Bidirectional connecting (HKG + SJC)  like BA LHR-SJC architecture",
            "SkyPier ferry integration could add connecting traffic (not modelled)",
            "Most recent case in library (Sep 2025, YE Jun 2028 forecast)",
            "9.7% CAGR growth rate over 3 years  post-pandemic recovery assumption",
            "Pipeline validated at 0.000% variance against target",
        ],
    },

    # =========================================================================
    # CASE: Icelandair KEF-SJC (FI_KEF_SJC)
    # =========================================================================
    {
        "route_id": "FI_KEF_SJC",
        "origin": "KEF",
        "destination": "SJC",
        "origin_city": "REK",
        "destination_city": "SJC",
        "carrier": "FI",
        "carrier_name": "Icelandair",
        "alliance": "None",
        "carrier_type": "Hybrid",
        "route_type": "Hub Longhaul",
        "hub_airport": "KEF",
        "hub_status": "Secondary Hub",
        "frequency": 4,
        "aircraft": "B757-200",
        "seats_per_flight": 183,
        "annual_seats": 76128,
        "departure_time_home": None,
        "departure_time_dest": None,
        "forecast_year": 2025,
        "data_vintage": "2019 base, 2.4% growth",
        "existing_service": False,
        "p2p_base_demand": 38100,
        "p2p_growth_rate": 0.024,
        "p2p_after_growth": 39000,
        "p2p_stimulation": 1.0,
        "p2p_after_stimulation": 39000,
        "p2p_capture_rate": 0.5,
        "p2p_forecast": 19500,
        "cnx_home_total_demand": 1831000,
        "cnx_home_direct_comp_demand": 499100,
        "cnx_home_no_direct_comp_demand": 1331900,
        "cnx_home_direct_comp_qsi_share": 0.011,
        "cnx_home_no_direct_comp_qsi_share": 0.028,
        "cnx_home_qsi_share_blended": 0.023,
        "cnx_home_forecast": 42200,
        "cnx_home_top_cities": {
            "STO": {'demand': 43401, 'qsi': 0.15, 'forecast': 6490},
            "LON": {'demand': 499133, 'qsi': 0.012, 'forecast': 5428},
            "DUB": {'demand': 87924, 'qsi': 0.054, 'forecast': 4762},
            "OSL": {'demand': 25003, 'qsi': 0.169, 'forecast': 4219},
            "CPH": {'demand': 45614, 'qsi': 0.08, 'forecast': 3661},
            "PAR": {'demand': 224684, 'qsi': 0.015, 'forecast': 3471},
        },
        "cnx_home_ceiling": 0.85,
        "cnx_dest_total_demand": 72600,
        "cnx_dest_direct_comp_demand": 18300,
        "cnx_dest_no_direct_comp_demand": 54300,
        "cnx_dest_direct_comp_qsi_share": 0.001,
        "cnx_dest_no_direct_comp_qsi_share": 0.02,
        "cnx_dest_qsi_share_blended": 0.015,
        "cnx_dest_forecast": 1100,
        "cnx_dest_discount_factor": 0.75,
        "cnx_dest_top_cities": {
            "LAX": {'demand': 29182, 'qsi': 0.032, 'forecast': 935},
            "SAN": {'demand': 5648, 'qsi': 0.005, 'forecast': 28},
        },
        "grand_total_forecast": 62794,
        "load_factor": 0.825,
        "qsi_adjustment": 1.0,
        "factor_up": 1.0,
        "calibration_factors_by_market": {
            "description": "Model accepted raw  new route proposal",
        },
        "notes": [
            "Icelandair uniquely uses KEF as Europe-US connecting hub despite small size",
            "50% P2P capture  HIGHEST in library  Iceland uniquely attractive destination",
            "No stimulation (1.0) because SFO direct service already exists  SJC is incremental",
            "KEF connecting is 67% of total  high for a secondary hub due to Icelandair's model",
            "Scandinavian cities dominate connecting (STO, OSL, CPH)  niche Icelandair network",
            "Nordic QSI scores very high (STO 15%, OSL 16.9%)  few competitors on these routings",
            "B757-200 with 183 seats  narrowbody on transatlantic, only case in library",
            "Low growth rate (2.4%)  mature North Atlantic leisure market",
            "82.5% LF at 4x weekly  commercially viable",
        ],
    },

    # =========================================================================
    # CASE 14: CZ CAN-SJC (China Southern Guangzhou - San Jose) -- VERIFIED Chat 44
    # =========================================================================
    {
        "route_id": "CZ_CAN_SJC",
        "origin": "CAN",
        "destination": "SJC",
        "origin_city": "CAN",
        "destination_city": "SJC",
        "carrier": "CZ",
        "carrier_name": "China Southern",
        "alliance": "SkyTeam",
        "carrier_type": "Full Service",
        "route_type": "Hub Longhaul",
        "hub_airport": "CAN",
        "hub_status": "Major Hub",
        "frequency": 3,
        "aircraft": "B787-8",
        "seats_per_flight": 266,
        "annual_seats": 82992,  # 266 * 3 * 52 * 2
        "departure_time_home": None,
        "departure_time_dest": None,
        "forecast_year": 2022,
        "data_vintage": "Sabre MI Jan-Dec 2018, OAG Aug 2019",
        "existing_service": False,  # new route; CZ SFO-CAN used as proxy

        # DEMAND  8 P2P segments
        "p2p_base_demand": 77091,
        "p2p_growth_rate_business_gz": 0.176,  # 4.7% CAGR compound to 2022
        "p2p_growth_rate_leisure_gz": 0.226,   # 6.0% CAGR compound to 2022
        "p2p_growth_rate_business_us": 0.131,  # 3.6% CAGR compound to 2022
        "p2p_growth_rate_leisure_us": 0.226,
        "p2p_growth_rate_compound": 0.1745,    # blended
        "p2p_after_growth": 90541,
        "p2p_stimulation_business": 1.30,
        "p2p_stimulation_primary": 1.30,
        "p2p_stimulation_secondary_gz": 1.15,
        "p2p_stimulation_secondary_us": 1.25,
        "p2p_stimulation_contested": 1.05,
        "p2p_stimulation": 1.29,  # blended weighted average
        "p2p_after_stimulation": 117017,
        "p2p_capture_business": 0.30,
        "p2p_capture_primary": 0.30,
        "p2p_capture_secondary": 0.25,
        "p2p_capture_contested": 0.15,
        "p2p_capture_rate": 0.2965,  # blended
        "p2p_forecast": 34699,
        "p2p_business_split": 0.75,
        "p2p_visitor_resident_split": (0.58, 0.42),
        "p2p_primary_secondary_contested": (0.81, 0.13, 0.06),

        # CONNECTING @ CAN
        "cnx_home_num_cities": 96,
        "cnx_home_total_demand": 1233956,  # after 11.2% growth
        "cnx_home_base_demand": 1109673,
        "cnx_home_growth": 0.112,
        "cnx_home_direct_comp_demand": 168601,  # SHA only has direct
        "cnx_home_no_direct_comp_demand": 1065355,
        "cnx_home_direct_comp_qsi_share": 0.0202,
        "cnx_home_no_direct_comp_qsi_share": 0.0223,
        "cnx_home_qsi_share_blended": 0.0220,
        "cnx_home_forecast": 27184,
        "cnx_home_top_cities": {
            "DEL": {"demand": 202297, "qsi": 0.0443, "forecast": 8970},
            "SHA": {"demand": 168601, "qsi": 0.0240, "forecast": 3409},
            "WUH": {"demand": 17278, "qsi": 0.1310, "forecast": 2263},
            "KTM": {"demand": 3326, "qsi": 0.5383, "forecast": 1791},
            "SGN": {"demand": 182068, "qsi": 0.0062, "forecast": 1126},
            "PER": {"demand": 7380, "qsi": 0.1341, "forecast": 990},
            "TPE": {"demand": 158403, "qsi": 0.0050, "forecast": 797},
            "CTU": {"demand": 22564, "qsi": 0.0262, "forecast": 592},
        },
        "cnx_home_ceiling": 0.85,

        # CONNECTING @ SJC
        "cnx_dest_num_cities": 38,
        "cnx_dest_total_demand": 2524296,  # after 4.4% growth
        "cnx_dest_base_demand": 2417908,
        "cnx_dest_growth": 0.044,
        "cnx_dest_direct_comp_demand": 2179238,
        "cnx_dest_no_direct_comp_demand": 345058,
        "cnx_dest_direct_comp_qsi_share": 0.0009,
        "cnx_dest_no_direct_comp_qsi_share": 0.0143,
        "cnx_dest_qsi_share_blended": 0.0028,
        "cnx_dest_forecast": 6974,
        "cnx_dest_discount_factor": 0.75,

        # TOTALS
        "grand_total_forecast": 68856,
        "load_factor": 0.830,
        "pdew": 220.7,

        # CALIBRATION
        "qsi_adjustment": 1.0,  # all three QSI adjustments = 1.0
        "factor_up": 1.0,
        "premium_factor": 1.0,
        "calibration_factors_by_market": {
            "description": "All adjustment factors = 1.0. Model accepted raw for new route proposal.",
        },

        # PROXY ANALYSIS
        "proxy_analysis": {
            "description": "CZ SFO-CAN used as proxy to calibrate capture rates",
            "cz_sfo_can_behind_cities": "DEL, KTM, SHA, BKK, MNL, BJS top connecting",
            "mc_cs_analysis": "HKG-SJC corridor competitive assessment included",
            "hkg_competitors": "CX (52.7% cap share), HX, SQ, UA",
        },

        # CONTEXT
        "notes": [
            "New route  CZ did not operate CAN-SJC at time of analysis (Aug 2019)",
            "Part of broader SkyTeam SJC assessment alongside AF CDG-SJC, KL AMS-SJC, CI TPE-SJC",
            "Same analyst (JZ), same OAG/Sabre vintage as AF, KL, CI cases",
            "CZ SFO-CAN existing service used as proxy for P2P capture rate calibration",
            "QSI adjustment = 1.0  confirms pattern: new route proposals accepted raw",
            "75% business split  reflects Silicon Valley tech trade with Guangdong/Pearl River Delta",
            "Highest growth rates in library: China business 4.7% CAGR, leisure 6.0% CAGR",
            "CAN connecting dominated by India (DEL #1 at 8,970)  India-SJC corridor via CAN",
            "KTM (Kathmandu) has 53.8% QSI  highest individual city QSI in library (niche monopoly routing)",
            "Only 3x weekly with B787-8 (266 seats)  smallest hub carrier capacity in library",
            "MC/CS Analysis includes HKG-SJC competitive landscape (CX, HX, SQ, UA)",
            "P2P capture 30% business/primary, 25% secondary, 15% contested  most granular differentiation",
            "Stimulation varies: 1.30 business/primary, 1.15-1.25 secondary, 1.05 contested",
            "Traffic split: 48% @CAN hub, 8% @SFO proxy beyond, 44% local P2P",
        ],
    },

    # =========================================================================
    # CASE: Starlux Airlines TPE-SJC (JX_TPE_SJC)
    # =========================================================================
    {
        "route_id": "JX_TPE_SJC",
        "origin": "TPE",
        "destination": "SJC",
        "origin_city": "TPE",
        "destination_city": "SJC",
        "carrier": "JX",
        "carrier_name": "Starlux Airlines",
        "alliance": "None",
        "carrier_type": "Full Service",
        "route_type": "Point to Point",
        "hub_airport": None,
        "hub_status": "Non-Hub",
        "frequency": 3,
        "aircraft": "A350-900",
        "seats_per_flight": 304,
        "annual_seats": 158080,
        "departure_time_home": None,
        "departure_time_dest": None,
        "forecast_year": 2024,
        "data_vintage": "2019 base",
        "existing_service": False,
        "p2p_base_demand": 142499,
        "p2p_segments": {
            "Taiwan Business": {'base': 45600, 'growth': 0.125, 'stim': 1.1, 'capture': 0.4},
            "Taiwan Leisure Primary": {'base': 9333, 'growth': 0.097, 'stim': 1.1, 'capture': 0.4},
            "Taiwan Leisure Secondary": {'base': 1287, 'growth': 0.097, 'stim': 1.05, 'capture': 0.4},
            "Taiwan Leisure Contested": {'base': 780, 'growth': 0.097, 'stim': 1.05, 'capture': 0.25},
            "US Business": {'base': 68400, 'growth': 0.125, 'stim': 1.1, 'capture': 0.4},
            "US Leisure Primary": {'base': 14000, 'growth': 0.097, 'stim': 1.1, 'capture': 0.4},
            "US Leisure Secondary": {'base': 1930, 'growth': 0.097, 'stim': 1.05, 'capture': 0.4},
            "US Leisure Contested": {'base': 1170, 'growth': 0.097, 'stim': 1.05, 'capture': 0.25},
        },
        "p2p_stimulation": 1.1,
        "p2p_capture_rate": 0.38,
        "p2p_forecast": 69736,
        "p2p_business_split": 0.8,
        "cnx_home_forecast": 0,
        "cnx_dest_forecast": 0,
        "grand_total_forecast": 69736,
        "load_factor": 0.441,
        "qsi_adjustment": None,
        "factor_up": 1.0,
        "calibration_factors_by_market": {
            "description": "Pure P2P forecast  no QSI connecting model applied",
        },
        "notes": [
            "P2P only  Starlux has no connecting hub network at TPE",
            "44.1% LF is commercially unviable  oversized aircraft for the market",
            "8-segment P2P model  most granular P2P breakdown in library",
            "Business/Primary segments get 1.10 stim + 40% capture",
            "Contested segments get 1.05 stim + 25% capture  clear differentiation",
            "80% business split  semiconductor/tech bilateral trade",
            "304-seat A350 with only 69.7k pax  massive overcapacity",
            "Compare with CI TPE-SJC (Case 7): same market, different carrier",
            "CI has connecting network; JX does not  explains 112.8k vs 69.7k gap",
            "This case demonstrates why hub connectivity matters for route viability",
        ],
    },

    # =========================================================================
    # CASE 15: BR TPE-SJC Sch1 (EVA Air, 5x Weekly, B787-9, 270 seats)  VERIFIED Chat 45
    # Primary scenario  evening departure from TPE, strong connecting
    # =========================================================================
    {
        "route_id": "BR_TPE_SJC_5x_Sch1",
        "origin": "TPE",
        "destination": "SJC",
        "origin_city": "TPE",
        "destination_city": "SJC",
        "carrier": "BR",
        "carrier_name": "EVA Air",
        "alliance": "Star Alliance",
        "carrier_type": "Full Service",
        "route_type": "Hub Longhaul",
        "hub_airport": "TPE",
        "hub_status": "Major Hub",
        "frequency": 5,
        "operating_days": "1 345 7",
        "aircraft": "B787-9",
        "seats_per_flight": 270,
        "config": "24J/42PY/204Y",
        "annual_seats": 140400,
        "departure_time_home": "20:00 TPE",
        "arrival_time_dest": "16:50 SJC",
        "schedule_return": "18:50 SJC  22:40+1 TPE",
        "analyst": "JZ",
        "analysis_date": "Jul 2017",
        "sabre_vintage": "Jan-Dec 2016",
        "forecast_year": 2019,
        "existing_service": False,

        # P2P DEMAND  mirrored Taiwan/US structure
        "p2p_base_demand": 125261,  # total (000s scaled)
        "p2p_segments": {
            "Taiwan Business": {"base": 40084, "growth": 0.10, "stim": 1.20, "capture": 0.45, "forecast": 23810},
            "Taiwan Leisure Primary": {"base": 8204, "growth": 0.15, "stim": 1.20, "capture": 0.45, "forecast": 5095},
            "Taiwan Leisure Secondary": {"base": 1131, "growth": 0.15, "stim": 1.05, "capture": 0.45, "forecast": 615},
            "Taiwan Leisure Contested": {"base": 685, "growth": 0.15, "stim": 1.05, "capture": 0.20, "forecast": 166},
            "US Business": {"base": 60125, "growth": 0.10, "stim": 1.20, "capture": 0.45, "forecast": 35714},
            "US Leisure Primary": {"base": 12306, "growth": 0.15, "stim": 1.20, "capture": 0.45, "forecast": 7642},
            "US Leisure Secondary": {"base": 1697, "growth": 0.15, "stim": 1.05, "capture": 0.45, "forecast": 922},
            "US Leisure Contested": {"base": 1028, "growth": 0.15, "stim": 1.05, "capture": 0.20, "forecast": 248},
        },
        "p2p_stimulation": 1.20,  # business/primary
        "p2p_stimulation_secondary": 1.05,
        "p2p_capture_rate": 0.447,  # blended
        "p2p_forecast": 74212,
        "p2p_pct_of_total": 0.604,

        # CONNECTING AT TPE (HOME HUB)
        "cnx_home_demand_pool": 2825000,  # approximate from data
        "cnx_home_direct_comp_demand": 362497,
        "cnx_home_no_direct_comp_demand": 1172353,
        "cnx_home_direct_comp_qsi_share": 0.0058,
        "cnx_home_no_direct_comp_qsi_share": 0.0324,
        "cnx_home_qsi_share_blended": 0.0261,  # 2.61%
        "cnx_home_forecast": 40059,
        "cnx_home_pct_of_total": 0.326,
        "cnx_home_top_cities": {
            "SGN": {"demand": 140205, "qsi_share": 0.0825, "pax": 11560},
            "MNL": {"demand": 209052, "qsi_share": 0.0292, "pax": 6095},
            "BKK": {"demand": 22998, "qsi_share": 0.1714, "pax": 3942},
            "SIN": {"demand": 46090, "qsi_share": 0.0635, "pax": 2926},
            "HKG": {"demand": 96406, "qsi_share": 0.0267, "pax": 2578},
            "CEB": {"demand": 12931, "qsi_share": 0.1641, "pax": 2122},
            "JKT": {"demand": 11506, "qsi_share": 0.1600, "pax": 1840},
            "SHA": {"demand": 179859, "qsi_share": 0.0091, "pax": 1642},
            "SEL": {"demand": 182840, "qsi_share": 0.0085, "pax": 1549},
            "DPS": {"demand": 6974, "qsi_share": 0.1721, "pax": 1200},
        },

        # CONNECTING AT SJC (DESTINATION)
        "cnx_dest_demand_pool": 1151000,  # approximate
        "cnx_dest_qsi_share_blended": 0.0074,
        "cnx_dest_forecast": 8508,
        "cnx_dest_pct_of_total": 0.069,
        "cnx_dest_top_cities": {
            "LAX": {"demand": 413080, "qsi_share": 0.017, "pax": 1092},
            "NYC": {"demand": 234458, "qsi_share": 0.012, "pax": 957},
            "PDX": {"demand": 20692, "qsi_share": 0.040, "pax": 835},
            "LAS": {"demand": 22133, "qsi_share": 0.036, "pax": 797},
            "PHX": {"demand": 12748, "qsi_share": 0.051, "pax": 650},
            "ATL": {"demand": 15415, "qsi_share": 0.042, "pax": 649},
            "SAN": {"demand": 10535, "qsi_share": 0.049, "pax": 516},
            "SEA": {"demand": 69351, "qsi_share": 0.027, "pax": 512},
        },

        # GRAND TOTAL
        "grand_total_forecast": 122779,
        "load_factor": 0.874,
        "pdew": 168.7,

        # REVENUE
        "total_lf": 0.876,
        "business_lf": 0.90,
        "py_lf": 0.75,
        "economy_lf": 0.88,
        "avg_ow_fare": 758.42,
        "pax_revenue": 93333000,
        "cargo_revenue": 2496000,
        "ancillary_revenue": 721000,
        "total_revenue": 96551000,
        "yield_rpk": 7.27,
        "prask": 6.37,
        "trask": 6.59,
        "yr2_total": 128398,
        "yr2_lf": 0.915,
        "yr3_total": 133979,
        "yr3_lf": 0.954,
        "traffic_mix": {"p2p": 0.603, "cnx_sjc": 0.071, "cnx_tpe": 0.326},

        # CALIBRATION
        "qsi_adjustment": 1.0,
        "factor_up": 1.0,
        "calibration_factors_by_market": {
            "description": "Model accepted raw  new route proposal. QSI adj = 1.0.",
        },

        # ALT AIRCRAFT
        "alt_aircraft": {"type": "B777-300ER", "seats": 313, "annual_seats": 162760, "lf": 0.754},

        # CONTEXT
        "notes": [
            "New route  EVA Air assessed TPE-SJC as supplement to existing TPE-SFO service",
            "Schedule 1 = 20:00 TPE departure  evening departure catches SE Asian feed connections",
            "Highest connecting share of 4 scenarios (33%)  departure time optimised for TPE hub feed",
            "Top connecting: SGN (11,560), MNL (6,095), BKK (3,942)  SE Asian markets dominate",
            "BKK has 17.1% QSI  high for major market, reflects EVA Air monopoly on TPE-BKK-SJC routing",
            "5x weekly on B787-9 achieves 87.4% LF  commercially strong",
            "Also tested on 777-300ER at same frequency: LF drops to 75.4%",
            "Yr3 LF exceeds 95%  daily service would be commercially justified",
            "Revenue $96.6M total, PRASK 6.37, TRASK 6.59",
            "QSI Weightings sheet shows TPE as major hub: BR 174k pax, CI 124k pax through TPE",
            "Connecting Info sheet is LHR template residue (BA/UA/VS via LHR)  not TPE data",
            "Growth: Business 10% CAGR, Leisure 15% CAGR  conservative vs CI case",
            "P2P capture 45% bus/primary, 20% contested  higher than CI (30%) due to BR hub strength",
            "Analysis done for SJC Airport Authority route development pitch to EVA Air (Jul 2017)",
        ],
    },

    # =========================================================================
    # CASE 16: BR TPE-SJC Sch2 (EVA Air, 4x Weekly, B787-9, 270 seats, 12:00 dep)  VERIFIED Chat 45
    # Midday departure  poor connecting but tests off-peak slot
    # =========================================================================
    {
        "route_id": "BR_TPE_SJC_4x_Sch2",
        "origin": "TPE",
        "destination": "SJC",
        "carrier": "BR",
        "carrier_name": "EVA Air",
        "alliance": "Star Alliance",
        "route_type": "Hub Longhaul",
        "hub_status": "Major Hub",
        "frequency": 4,
        "operating_days": "1 3 5 7",
        "aircraft": "B787-9",
        "seats_per_flight": 270,
        "annual_seats": 112320,
        "departure_time_home": "12:00 TPE",
        "arrival_time_dest": "08:50 SJC",
        "analyst": "JZ",
        "analysis_date": "Jul 2017",
        "forecast_year": 2019,

        # P2P  lower capture at 4x
        "p2p_capture_rate": 0.398,  # blended  reduced from 0.45 to 0.40 for most segments
        "p2p_forecast": 66012,
        "p2p_pct_of_total": 0.735,

        # CONNECTING  drastically lower due to midday departure
        "cnx_home_forecast": 16933,
        "cnx_home_pct_of_total": 0.188,
        "cnx_dest_forecast": 6918,
        "cnx_dest_pct_of_total": 0.077,

        # GRAND TOTAL
        "grand_total_forecast": 89863,
        "load_factor": 0.800,

        # REVENUE
        "total_revenue": 76822000,
        "avg_ow_fare": 787,
        "prask": 6.34,
        "trask": 6.56,
        "traffic_mix": {"p2p": 0.745, "cnx_sjc": 0.076, "cnx_tpe": 0.180},

        # CALIBRATION
        "qsi_adjustment": 1.0,

        "notes": [
            "4x weekly, midday departure (12:00 TPE)  misses SE Asian feed waves",
            "TPE connecting drops from 40,058 (Sch1) to 16,933  58% reduction from departure time alone",
            "SJC connecting also lower but less dramatic: 8,5086,918 (-19%)",
            "P2P also drops due to 4x vs 5x: 74,21266,012 (-11%) with lower capture rate (40% vs 45%)",
            "LF 80.0%  still commercially viable but weaker case",
            "Revenue $76.8M vs $96.6M for Sch1  $20M revenue gap from schedule/frequency choice",
            "Key finding: departure time matters more than frequency for connecting traffic at hub",
        ],
    },

    # =========================================================================
    # CASE 17: BR TPE-SJC Sch3 (EVA Air, 4x Weekly, B787-9, 270 seats, 13:40 dep)  VERIFIED Chat 45
    # Early afternoon  slightly better connecting than Sch2
    # =========================================================================
    {
        "route_id": "BR_TPE_SJC_4x_Sch3",
        "origin": "TPE",
        "destination": "SJC",
        "carrier": "BR",
        "carrier_name": "EVA Air",
        "alliance": "Star Alliance",
        "route_type": "Hub Longhaul",
        "hub_status": "Major Hub",
        "frequency": 4,
        "operating_days": "1 3 5 7",
        "aircraft": "B787-9",
        "seats_per_flight": 270,
        "annual_seats": 112320,
        "departure_time_home": "13:40 TPE",
        "arrival_time_dest": "10:30 SJC",
        "analyst": "JZ",
        "analysis_date": "Jul 2017",
        "forecast_year": 2019,

        # P2P  slightly higher capture than Sch2 due to better time
        "p2p_capture_rate": 0.423,  # business at 42%, primary leisure 45%
        "p2p_forecast": 70243,
        "p2p_pct_of_total": 0.737,

        # CONNECTING
        "cnx_home_forecast": 16905,
        "cnx_home_pct_of_total": 0.177,
        "cnx_dest_forecast": 8112,
        "cnx_dest_pct_of_total": 0.085,

        # GRAND TOTAL
        "grand_total_forecast": 95261,
        "load_factor": 0.848,

        # REVENUE
        "total_revenue": 79311000,
        "avg_ow_fare": 803,
        "prask": 6.55,
        "trask": 6.77,
        "traffic_mix": {"p2p": 0.735, "cnx_sjc": 0.088, "cnx_tpe": 0.177},

        # CALIBRATION
        "qsi_adjustment": 1.0,

        "alt_aircraft": {"type": "B777-300ER", "seats": 313, "annual_seats": 130208, "lf": 0.732},

        "notes": [
            "4x weekly, 13:40 TPE departure  100 minutes later than Sch2",
            "TPE connecting virtually identical to Sch2 (16,905 vs 16,933)  still misses feed waves",
            "SJC connecting higher than Sch2 (8,112 vs 6,918)  better US arrival time (10:30 vs 08:50)",
            "P2P higher than Sch2 (70,243 vs 66,012)  business capture 42% vs 40%",
            "Grand total 95,261 vs 89,863  6% more passengers from 100-min departure shift",
            "LF 84.8% vs 80.0%  meaningful improvement",
            "Revenue $79.3M vs $76.8M  $2.5M from departure time optimisation alone",
            "Key finding: early PM departure catches some US onward connections but still misses TPE feed",
        ],
    },

    # =========================================================================
    # CASE 18: BR TPE-SJC Sch2 5x March (EVA Air, 5x Weekly, B787-9, 12:00 dep)  VERIFIED Chat 45
    # Earlier analysis  5x at midday, different demand base
    # =========================================================================
    {
        "route_id": "BR_TPE_SJC_5x_Sch2_Mar",
        "origin": "TPE",
        "destination": "SJC",
        "carrier": "BR",
        "carrier_name": "EVA Air",
        "alliance": "Star Alliance",
        "route_type": "Hub Longhaul",
        "hub_status": "Major Hub",
        "frequency": 5,
        "operating_days": "1 345 7",
        "aircraft": "B787-9",
        "seats_per_flight": 270,
        "annual_seats": 140400,
        "departure_time_home": "12:00 TPE",
        "analyst": "JZ",
        "analysis_date": "Mar 2017",
        "sabre_vintage": "Jan-Dec 2015",  # earlier vintage than Jul 2017 files
        "forecast_year": 2019,

        # P2P  different demand base (earlier SABRE data + different growth rates)
        "p2p_base_demand": 109801,  # lower base than Jul 2017 analysis
        "p2p_growth_business": 0.14,  # higher growth rate than Jul analysis (14% vs 10%)
        "p2p_growth_leisure": 0.215,  # much higher leisure growth (21.5% vs 15%)
        "p2p_forecast": 67678,
        "p2p_pct_of_total": 0.711,

        # CONNECTING
        "cnx_home_forecast": 19248,
        "cnx_home_pct_of_total": 0.202,
        "cnx_home_note": "No direct competition split  all treated as no-direct-comp",
        "cnx_dest_forecast": 8248,
        "cnx_dest_pct_of_total": 0.087,

        # GRAND TOTAL
        "grand_total_forecast": 95174,
        "load_factor": 0.678,

        # CALIBRATION
        "qsi_adjustment": 1.0,

        "notes": [
            "Earlier analysis (Mar 2017) with different SABRE vintage (2015 vs 2016)",
            "Lower P2P base demand (109.8k vs 125.3k) but higher growth rates compensate",
            "5x at midday  same departure time as Sch2 but with extra frequency",
            "LF only 67.8%  critically low, driven by high capacity (5x  270) with midday schedule",
            "Connecting higher than Sch2 4x Jul (19,248 vs 16,933) due to extra frequency",
            "Compare with Sch1 5x at 20:00: same frequency but connecting drops 40k19k from schedule",
            "This is the worst-performing scenario commercially  combines high capacity with poor schedule",
            "Demonstrates that adding frequency cannot compensate for poor departure time",
        ],
    },

    # =========================================================================
    # CASE 19: LH FRA-SJC (Lufthansa Frankfurt - San Jose) -- VERIFIED Chat 46
    # =========================================================================
    {
        "route_id": "LH_FRA_SJC",
        "origin": "FRA",
        "destination": "SJC",
        "origin_city": "FRA",
        "destination_city": "SJC",
        "carrier": "LH",
        "carrier_name": "Lufthansa",
        "alliance": "Star Alliance",
        "carrier_type": "Full Service",
        "route_type": "Hub Longhaul",
        "hub_airport": "FRA",
        "hub_status": "Major Hub",
        "frequency": 5,
        "aircraft": "A340-300",
        "seats_per_flight": 267,
        "annual_seats": 138840,
        "config": "42/225",
        "departure_time_home": "10:15",
        "departure_time_dest": "14:10",
        "forecast_year": 2016,
        "data_vintage": "OAG/Sabre Aug 2014, forecast Jul 2015",
        "analyst": "JZ",
        "existing_service": False,

        "p2p_base_demand": 81670,
        "p2p_growth_rate": 0.12,
        "p2p_after_growth": 91471,
        "p2p_stimulation_blended": 1.122,
        "p2p_capture_rate_blended": 0.421,
        "p2p_forecast": 43196,
        "p2p_pct_of_total": 0.384,

        "p2p_segments": {
            "german_business": {"base": 22647, "stim": 1.15, "capture": 0.48, "forecast": 14001},
            "german_leisure_primary": {"base": 9797, "stim": 1.10, "capture": 0.38, "forecast": 4586},
            "german_leisure_secondary": {"base": 4698, "stim": 1.05, "capture": 0.38, "forecast": 2099},
            "german_leisure_contested": {"base": 1243, "stim": 1.05, "capture": 0.30, "forecast": 439},
            "us_business": {"base": 25538, "stim": 1.15, "capture": 0.48, "forecast": 15789},
            "us_leisure_primary": {"base": 11047, "stim": 1.10, "capture": 0.30, "forecast": 4083},
            "us_leisure_secondary": {"base": 5298, "stim": 1.05, "capture": 0.30, "forecast": 1869},
            "us_leisure_contested": {"base": 1402, "stim": 1.05, "capture": 0.20, "forecast": 330},
        },

        "cnx_home_demand_pool": 1870000,
        "cnx_home_qsi_share_blended": 0.0364,
        "cnx_home_forecast": 67990,
        "cnx_home_pct_of_total": 0.604,
        "cnx_dest_demand_pool": 342000,
        "cnx_dest_qsi_share_blended": 0.0039,
        "cnx_dest_forecast": 1328,
        "cnx_dest_pct_of_total": 0.012,

        "grand_total_forecast": 112515,
        "load_factor": 0.810,
        "qsi_adjustment": 1.0,
        "bay_area_capture_pct": 0.20,

        "top_cnx_cities_fra": {"DEL": 4101, "MUC": 3554, "PAR": 2946, "MAA": 2725, "BER": 2442},
        "india_corridor_total": 10800,
        "highest_qsi_city": {"AMM": 0.260},

        "key_observations": [
            "FRA is largest connecting demand pool in European library (1.87M)",
            "3.64% QSI is average for major European hub despite FRA's size",
            "India connecting via FRA is a major corridor (~10.8k pax)",
            "60% connecting share is highest European hub percentage",
            "Existing FRA-SFO service (LH daily + UA 2x) means SJC captures only 20% of Bay Area",
            "Revenue Data sheet references Chicago ORD fares -- workbook template reused from prior project",
            "Demand Settings sheet has Chinese city catchment analysis -- residual from CZ/MU analysis",
        ],
    },

    # =========================================================================
    # CASE 20: LH MUC-SJC (Lufthansa Munich - San Jose) -- VERIFIED Chat 46
    # =========================================================================
    {
        "route_id": "LH_MUC_SJC",
        "origin": "MUC",
        "destination": "SJC",
        "origin_city": "MUC",
        "destination_city": "SJC",
        "carrier": "LH",
        "carrier_name": "Lufthansa",
        "alliance": "Star Alliance",
        "carrier_type": "Full Service",
        "route_type": "Hub Longhaul",
        "hub_airport": "MUC",
        "hub_status": "Secondary Hub",  # LH's second hub, smaller than FRA
        "frequency": 5,
        "aircraft": "A350-900",
        "seats_per_flight": 293,
        "annual_seats": 152360,
        "departure_time_home": "12:20",
        "departure_time_dest": "15:30",
        "forecast_year": 2016,
        "data_vintage": "OAG/Sabre Aug 2014, forecast Jul 2015",
        "analyst": "OS",
        "existing_service": False,

        "p2p_base_demand": 45565,
        "p2p_growth_rate": 0.12,
        "p2p_after_growth": 51033,
        "p2p_stimulation_blended": 1.431,
        "p2p_capture_rate_blended": 0.689,
        "p2p_forecast": 50289,
        "p2p_pct_of_total": 0.402,

        "p2p_segments": {
            "german_business": {"base": 10289, "stim": 1.50, "capture": 0.75, "forecast": 12944},
            "german_leisure_primary": {"base": 3920, "stim": 1.35, "capture": 0.65, "forecast": 3440},
            "german_leisure_secondary": {"base": 1880, "stim": 1.30, "capture": 0.65, "forecast": 1590},
            "german_leisure_contested": {"base": 497, "stim": 1.30, "capture": 0.50, "forecast": 323},
            "us_business": {"base": 17711, "stim": 1.50, "capture": 0.75, "forecast": 22274},
            "us_leisure_primary": {"base": 6750, "stim": 1.35, "capture": 0.55, "forecast": 5012},
            "us_leisure_secondary": {"base": 3237, "stim": 1.30, "capture": 0.55, "forecast": 2314},
            "us_leisure_contested": {"base": 1281, "stim": 1.30, "capture": 0.35, "forecast": 583},
        },

        "cnx_home_demand_pool": 1400000,
        "cnx_home_qsi_share_blended": 0.0521,
        "cnx_home_forecast": 73006,
        "cnx_home_pct_of_total": 0.584,
        "cnx_dest_demand_pool": 135000,
        "cnx_dest_qsi_share_blended": 0.0123,
        "cnx_dest_forecast": 1661,
        "cnx_dest_pct_of_total": 0.013,

        "grand_total_forecast": 124956,
        "load_factor": 0.820,
        "qsi_adjustment": 1.0,
        "bay_area_capture_pct": 0.34,
        "zero_metro_direct_service": True,  # KEY FLAG: no MUC-SFO or MUC-SJC existed

        "aircraft_alternatives": {
            "A350-900": {"seats": 293, "lf": 0.82, "status": "SELECTED"},
            "A340-600": {"seats": 297, "lf": 0.81},
            "A340-300": {"seats": 267, "lf": 0.90, "note": "Too tight for operational reliability"},
        },

        "schedule_variants_tested": ["09:30", "10:30", "12:20", "13:20"],
        "schedule_sensitivity": {
            "total_change_0930_to_1220": -1431,
            "pct_change": -0.011,
            "pool_increase_pct": 0.24,
            "qsi_decrease_pp": -1.08,
            "finding": "Pool/QSI offset: later departure increases pool +24% but decreases QSI -1.08pp, net -1.1% total",
        },

        "key_observations": [
            "HIGHEST STIMULATION IN LIBRARY: 1.50 business, 1.35 primary leisure",
            "HIGHEST P2P CAPTURE IN LIBRARY: 75% business, 65% primary leisure",
            "Zero direct MUC-Bay Area service drives extreme stimulation and capture",
            "Secondary hub OUTPERFORMS primary hub FRA by 11% despite smaller network",
            "5.21% blended QSI despite smaller hub -- faces less per-market competition than FRA",
            "Bay Area capture 34% vs FRA's 20% -- MUC passengers prefer SJC to avoid connecting",
            "Three aircraft options assessed -- A340-300 at 90% LF flagged too tight",
            "Multiple schedule variants tested -- 12:20 selected as FINAL",
            "Schedule sensitivity only 1.1% because pool/QSI offset mechanism",
        ],
    },
]


# =============================================================================
# CROSS-CASE CALIBRATION PATTERNS
# =============================================================================

CALIBRATION_PATTERNS = {

    "stimulation_by_market_type": {
        "description": "Demand stimulation factor based on market maturity",
        "patterns": [
            {"condition": "New unserved market (no existing direct anywhere nearby)", "range": (1.30, 1.40), "example": "CX HKG-SJC (1.40)"},
            {"condition": "Virgin nonstop market (no existing direct on this pair)", "range": (1.20, 1.30), "example": "EI DUB-SJC 4x (1.30), KE ICN-SJC (1.27), SQ SIN-SJC (1.30)"},
            {"condition": "New route but well-served indirectly", "range": (1.05, 1.15), "example": "AF CDG-SJC (1.09), CI TPE-SJC (1.10), JX TPE-SJC (1.10)"},
            {"condition": "New route, nearby airport direct  OVERLAPPING catchment (leisure)", "range": (1.00, 1.05), "example": "FI KEF-SJC (1.00  leisure pax will use SFO)"},
            {"condition": "New route, nearby airport direct  DISTINCT catchment (business)", "range": (1.25, 1.30), "example": "CZ CAN-SJC (1.29  SJC tech biz pax won't use SFO)"},
            {"condition": "Existing service re-assessment", "range": (1.00, 1.15), "example": "BA LHR-SJC (1.15)"},
            {"condition": "Mature competitive market", "range": (1.00, 1.05), "example": "N/A"},
        ],
    },

    "p2p_capture_by_competition": {
        "description": "P2P market capture rate based on competitive position",
        "patterns": [
            {"condition": "Unique destination, limited alternatives", "range": (0.40, 0.50), "example": "FI KEF-SJC (50%)"},
            {"condition": "Only direct service in market", "range": (0.33, 0.40), "example": "EI DUB-SJC (40%), JX TPE-SJC (40%)"},
            {"condition": "New direct, some indirect competition", "range": (0.30, 0.35), "example": "CX HKG-SJC (35%), SQ SIN-SJC (35%), CI TPE-SJC (30%)"},
            {"condition": "New direct, many indirect competitors", "range": (0.20, 0.25), "example": "AF CDG-SJC (25%)"},
            {"condition": "New direct, strong existing market", "range": (0.15, 0.20), "example": "KE ICN-SJC (19.5%)"},
            {"condition": "Existing service among competitors", "range": (0.15, 0.25), "example": "BA LHR-SJC segments"},
        ],
    },

    "p2p_capture_by_segment": {
        "description": "Capture rate varies by demand segment type",
        "patterns": [
            {"segment": "Business", "typical_capture": 0.25, "notes": "Higher willingness to pay for direct"},
            {"segment": "Leisure Primary", "typical_capture": 0.25, "notes": "Destination loyalty"},
            {"segment": "Leisure Secondary", "typical_capture": 0.25, "notes": "Some price sensitivity"},
            {"segment": "Leisure Contested", "typical_capture": 0.20, "notes": "Most price-sensitive, lowest capture"},
        ],
    },

    "connecting_share_by_hub_size": {
        "description": "Connecting QSI share scales with hub strength",
        "patterns": [
            {"hub_type": "Major Hub (LHR/CDG/AMS/FRA/TPE/ICN/HKG)", "typical_blended_share": (0.02, 0.04), "cnx_pct_of_total": (0.33, 0.66),
             "cases": "AF CDG-SJC 53%, KL AMS-SJC 62%, CI TPE-SJC 49%, KE ICN-SJC 66%, CX HKG-SJC 55%, BR TPE-SJC 33%(5x eve)-19%(4x mid)"},
            {"hub_type": "Major Hub ULR (SIN)", "typical_blended_share": (0.01, 0.02), "cnx_pct_of_total": (0.40, 0.50),
             "cases": "SQ SIN-SJC 42%  ULR suppresses connecting share despite major hub"},
            {"hub_type": "Secondary Hub (DUB/KEF)", "typical_blended_share": (0.01, 0.03), "cnx_pct_of_total": (0.30, 0.67),
             "cases": "EI DUB-SJC 42%, FI KEF-SJC 67%  KEF outlier due to niche network"},
            {"hub_type": "Non-Hub (SJC/TPA/JX-TPE)", "typical_blended_share": (0.00, 0.005), "cnx_pct_of_total": (0.00, 0.05),
             "cases": "JX TPE-SJC 0%, all SJC-side connecting 1-5%"},
        ],
    },

    "qsi_adjustment_patterns": {
        "description": "When does the raw QSI model need manual override?",
        "patterns": [
            {
                "condition": "New route proposal (pre-launch)",
                "typical_adjustment": 1.0,
                "notes": "Model accepted raw for EI DUB-SJC, AF CDG-SJC. No calibration against actuals needed.",
            },
            {
                "condition": "Existing route re-assessment (matching known traffic)",
                "typical_adjustment": "0.025 to 1.382 (median 0.267)",
                "notes": "BA LHR-SJC required heavy calibration. Raw QSI overestimates connecting ~5x.",
            },
        ],
    },

    "frequency_sensitivity": {
        "description": "How traffic scales with frequency changes",
        "cases": {
            "EI_DUB_SJC": {
                "4x_weekly": {"total": 77565, "lf": 0.704, "cnx_share": 0.0162},
                "7x_daily":  {"total": 91267, "lf": 0.473, "cnx_share": 0.0281},
                "delta_freq": "+75%", "delta_pax": "+18%", "delta_lf": "-23pp",
            },
            "KE_ICN_SJC": {
                "5x_weekly": {"total": 140858, "lf": 0.871, "cnx_share": 0.023},
                "7x_daily":  {"total": 184400, "lf": 0.749, "cnx_share": 0.034},
                "delta_freq": "+40%", "delta_pax": "+31%", "delta_lf": "-12pp",
            },
        },
        "findings": {
            "connecting_elasticity": "Near-linear with frequency in both cases",
            "p2p_elasticity": "Sub-linear  P2P capture drops or holds flat with excess frequency",
            "total_elasticity": "EI: +75% cap  +18% pax; KE: +40% cap  +31% pax",
            "load_factor_impact": "EI: 70%47% (destructive); KE: 87%75% (marginal)",
            "implication": "Frequency viability threshold: warn when projected LF < 65%",
            "aircraft_effect": "KE also downsized aircraft (338311 seats) which compounds the LF improvement",
        },
    },

    "ceiling_parameter": {
        "description": "Maximum QSI capture for any single connecting city",
        "standard_value": 0.85,
        "notes": "Consistent across all cases. Prevents model from over-allocating to dominant cities.",
    },

    "br_tpe_sjc_schedule_sensitivity": {
        "description": "Four-scenario schedule/frequency test for BR TPE-SJC  strongest schedule evidence in library",
        "scenarios": {
            "Sch1_5x_2000": {"grand_total": 122779, "lf": 0.874, "cnx_tpe": 40059, "revenue": 96551000},
            "Sch3_4x_1340": {"grand_total": 95261, "lf": 0.848, "cnx_tpe": 16905, "revenue": 79311000},
            "Sch2_4x_1200": {"grand_total": 89863, "lf": 0.800, "cnx_tpe": 16933, "revenue": 76822000},
            "Sch2_5x_1200_Mar": {"grand_total": 95174, "lf": 0.678, "cnx_tpe": 19248, "revenue": None},
        },
        "findings": {
            "departure_time_impact": "20:00 vs 12:00 TPE: connecting at TPE drops 40k17k (-58%), same frequency",
            "frequency_impact_at_bad_time": "4x5x at 12:00: connecting rises 17k19k (+13%) but LF crashes 80%68%",
            "total_revenue_range": "$76.8M to $96.6M  26% swing from schedule/frequency choice alone",
            "p2p_captures": "45% (5x evening) vs 40% (4x midday) vs 42% (4x early PM)",
            "key_lesson": "Departure time dominates frequency for hub connecting traffic. "
                         "Evening departure at TPE catches SE Asian feed (SGN, MNL, BKK arrivals). "
                         "Midday departure misses all waves regardless of frequency.",
        },
    },

    "br_tpe_sjc_cannibalisation": {
        "description": "Impact of new BR TPE-SJC on existing BR TPE-SFO service  by schedule",
        "methodology": "QSI re-run with and without SJC service to measure SFO share erosion",
        "scenarios": {
            "Sch1_5x_2000": {
                "sgn": {"sfo_change": -0.118, "note": "Largest cannibalisation  SGN connects well via SJC"},
                "mnl": {"sfo_change": -0.071},
                "bkk": {"sfo_change": -0.091},
                "hkg": {"sfo_change": -0.077},
                "sin": {"sfo_change": -0.043},
            },
            "Sch2_4x_1200": {
                "sgn": {"sfo_change": -0.012, "note": "Minimal cannibalisation  midday misses feed"},
                "mnl": {"sfo_change": -0.128},
                "sha": {"sfo_change": -0.021},
                "hkg": {"sfo_change": -0.089},
                "sel": {"sfo_change": -0.029},
            },
            "Sch3_4x_1340": {
                "sgn": {"sfo_change": -0.035},
                "mnl": {"sfo_change": -0.128},
                "sel": {"sfo_change": -0.059},
                "hkg": {"sfo_change": -0.022},
                "sin": {"sfo_change": -0.032},
            },
        },
        "findings": {
            "schedule_dependent": "Cannibalisation varies dramatically by schedule  SGN: -11.8% (evening) vs -1.2% (midday)",
            "mnl_consistent": "MNL cannibalisation ~12-13% regardless of schedule  less time-sensitive market",
            "net_positive": "Total Bay Area pax (SFO+SJC) increases in all scenarios despite cannibalisation",
            "lesson": "Cannibalisation of existing service is schedule-dependent. "
                     "Evening departure at new airport maximises total network pax but also "
                     "maximises cannibalisation. Midday protects existing service but limits new route.",
        },
    },

    "dest_hub_discount": {
        "description": "Discount factor applied to destination hub QSI scores",
        "typical_value": 0.75,
        "notes": "Applied to SJC-side scores in both EI and (implicitly) AF cases",
    },

    "tiered_calibration_defaults": {
        "description": "Default calibration factors by competitive tier (from pipeline development)",
        "tiers": {
            "Major Hub (LHR/CDG/AMS/FRA)": 0.173,
            "High Competition": 0.224,
            "Medium Competition": 0.314,
            "Low Competition": 0.265,
        },
        "notes": "These are starting points for the automated system. Real calibration varies significantly.",
    },

    # =========================================================================
    # CALIBRATION RULES FROM INDEPENDENT FORECAST TESTING (Chat 47)
    # =========================================================================

    "rule_1_zero_hub_metro_service": {
        "description": "NEW CATEGORY: Hub has zero direct service to destination metro area",
        "trigger": "Hub airport has NO direct service to ANY airport in destination metro "
                   "(e.g., zero MUC-SFO AND zero MUC-SJC = zero Bay Area service from MUC)",
        "parameters": {
            "business_stimulation": (1.45, 1.55),
            "leisure_stimulation": (1.30, 1.40),
            "business_capture": (0.70, 0.80),
            "leisure_capture": (0.55, 0.65),
        },
        "evidence": "LH MUC-SJC: 1.50/1.35 stim, 75%/65% capture. Previously highest was CX HKG-SJC (1.40 stim, 35% capture).",
        "impact_if_missing": "Without this rule, blind prediction underestimated MUC-SJC by 24.8% and got relative ranking wrong.",
        "system_requirement": "Must check whether hub has ANY direct service to destination metro before selecting parameters. "
                             "Single Boolean check determines stim category: 'virgin nonstop' (1.15-1.30) vs 'zero hub-metro' (1.45-1.55).",
        "discovered": "Chat 47 independent forecast test",
    },

    "rule_2_catchment_differentiation": {
        "description": "STRENGTHENED: Nearby airport service only depresses stimulation if catchments overlap",
        "trigger": "Existing direct service to nearby airport, but airports serve different passenger catchments "
                   "(e.g., SJC/Silicon Valley tech vs SFO/San Francisco general)",
        "adjustments": {
            "stimulation": "+0.05 above 'existing direct' baseline for business and primary leisure",
            "capture": "+5-8pp above comparable hub benchmark for all segments",
        },
        "evidence_for": [
            "LH FRA-SJC: analyst used 1.15 stim despite 3 daily FRA-SFO flights",
            "CZ CAN-SJC: analyst used 1.30 stim despite CZ SFO-CAN existing",
        ],
        "evidence_against": [
            "FI KEF-SJC: stim=1.00 because Iceland leisure pax WILL drive to SFO (overlapping catchment)",
        ],
        "test_result": "FRA business capture predicted 40% (library benchmark), actual 48%. Gap = SJC distinct catchment.",
        "discovered": "Chat 47 independent forecast test (strengthened from Chat 44 CZ CAN-SJC finding)",
    },

    "rule_3_secondary_equals_primary_capture": {
        "description": "Secondary leisure capture equals primary for strong hub carriers",
        "trigger": "Hub carrier with strong brand recognition in both origin and destination markets",
        "effect": "Secondary leisure capture = primary leisure capture (do NOT apply 5-10pp secondary discount)",
        "evidence": [
            "LH FRA-SJC: 38%/38% for German primary/secondary leisure (identical)",
            "LH MUC-SJC: 65%/65% for German primary/secondary leisure (identical)",
        ],
        "when_to_apply_discount": "Weaker brands or contested markets where carrier is not dominant",
        "discovered": "Chat 47 independent forecast test",
    },

    "rule_4_connecting_qsi_must_be_computed": {
        "description": "CRITICAL: Connecting QSI must be model-computed, never predicted from benchmarks",
        "finding": "Predicting blended QSI from library benchmarks unreliable. MUC prediction (4.0%) was 23% below actual (5.21%).",
        "root_cause": "Connecting QSI is determined market-by-market from connection builder based on each O&D's competitive structure. "
                     "Two hubs of identical size can have very different blended QSI if their connecting markets face different competitive landscapes.",
        "implication": "Calibration engine should always run full connection builder and QSI scorer. "
                      "Never estimate blended connecting QSI from benchmarks or hub-size proxies.",
        "evidence": "FRA 3.64% vs MUC 5.21% -- MUC faces less per-market competition despite smaller hub",
        "discovered": "Chat 47 independent forecast test",
    },

    "lh_fra_vs_muc_paired_comparison": {
        "description": "Most controlled paired comparison in library -- same airline, dest, analyst, vintage",
        "metrics": {
            "fra_total": 112515, "muc_total": 124956, "muc_wins_by_pct": 11.1,
            "fra_p2p": 43196, "muc_p2p": 50289,
            "fra_cnx": 67990, "muc_cnx": 73006,
            "fra_lf": 0.81, "muc_lf": 0.82,
        },
        "key_insight": "Secondary hub outperforms primary hub by 11% because: "
                      "(1) zero metro service drives extreme stim/capture, "
                      "(2) higher Bay Area capture (34% vs 20%), "
                      "(3) less connecting competition per O&D (5.2% vs 3.6% QSI).",
        "implication_for_engine": "Route-level market conditions (stim, capture, Bay Area split) matter more than raw hub size.",
    },

    "independent_forecast_test_results": {
        "description": "Blind prediction test results from Chat 47",
        "test_1_ci_tpe_sjc": {"error_pct": 0.6, "chat": 43},
        "test_2_lh_paired": {
            "round_1": {
                "fra_error_pct": -10.0, "muc_error_pct": -24.8,
                "relative_ranking": "WRONG (predicted FRA wins, actual MUC wins)",
            },
            "round_2_with_rules": {
                "fra_error_pct": 0.4, "muc_error_pct": 0.0,
                "relative_ranking": "CORRECT (MUC wins by 10.4% vs actual 11.1%)",
            },
            "rules_discovered": 4,
            "chat": 47,
        },
        "lesson": "Paired comparison tests are more demanding than single-route accuracy. "
                 "Getting absolute forecast within 10% is useful; getting relative ranking right is essential.",
    },
}


# =============================================================================
# ROUTE-SPECIFIC LEARNINGS
# =============================================================================

ROUTE_LEARNINGS = {

    "BA_LHR_SJC": {
        "lesson": "Heavy calibration needed for existing hub carrier routes",
        "detail": "Raw QSI overestimates connecting traffic ~5x because it doesn't account for: "
                  "VFR/diaspora loyalty, competitor fare dominance, actual booking behaviour. "
                  "Median adjustment factor was 0.267  model was capturing 5x too much connecting traffic.",
        "applicable_to": "Any route where you're trying to match known actual traffic on an existing service",
    },

    "EI_DUB_SJC_frequency": {
        "lesson": "Frequency sensitivity is asymmetric  connecting scales linearly, P2P does not",
        "detail": "4x7x: connecting QSI +73% (near-linear with +75% frequency). "
                  "P2P capture dropped 40%33%. Total only +18% despite +75% capacity. "
                  "LF collapsed from 70.4% to 47.3%.",
        "applicable_to": "Any frequency optimisation decision. Build LF check into portal.",
    },

    "EI_DUB_SJC_stimulation": {
        "lesson": "Stimulation factor highest for virgin nonstop markets",
        "detail": "1.30 for a market with zero existing direct service. "
                  "This is the upper bound we've observed. Represents genuine demand creation.",
        "applicable_to": "New route proposals where no direct service currently exists",
    },

    "AF_CDG_SJC_hub_dynamics": {
        "lesson": "Major hub connecting dominates total traffic",
        "detail": "CDG connecting is 53% of total forecast. DUB connecting was only 40%. "
                  "Hub size directly determines traffic mix and commercial viability.",
        "applicable_to": "Hub carrier route assessments  connecting share scales with hub network size",
    },

    "AF_CDG_SJC_capture": {
        "lesson": "P2P capture rate inversely related to number of competing indirect options",
        "detail": "CDG-SJC capture 25% (many indirect competitors via LHR/AMS/FRA/US hubs). "
                  "DUB-SJC capture 40% (fewer options, DUB is less connected). "
                  "When you're the only game in town, capture is high.",
        "applicable_to": "Setting P2P capture rates for new routes",
    },

    "clean_calibration_cases": {
        "lesson": "New route proposals may not need QSI adjustment",
        "detail": "EI DUB-SJC, AF CDG-SJC, and CI TPE-SJC all had QSI adjustment = 1.0. "
                  "The model works well for new routes where there are no actual traffic numbers to match. "
                  "Calibration difficulty arises when matching existing known performance.",
        "applicable_to": "Setting expectations for calibration complexity by route type",
    },

    "CI_TPE_SJC_cannibalisation": {
        "lesson": "New routes to nearby airports cannibalise existing service unevenly by market",
        "detail": "CI TPE-SJC cannibalised CI TPE-SFO by 4-22% across top markets. "
                  "Markets where SJC offers genuine proximity advantage (MNL -22%, HKG -12%) see "
                  "most switching. Markets where ground journey difference is marginal (SGN -4%, DEL -7%) "
                  "see less. Net effect: total Bay Area pax increases but SFO service weakens.",
        "applicable_to": "Any route proposal to secondary airport near existing service (e.g. STN vs LHR, OAK vs SFO)",
    },

    "CI_TPE_SJC_se_asia_hub": {
        "lesson": "SE Asian hub connecting profile differs fundamentally from European hubs",
        "detail": "TPE top 5 connecting cities: MNL, SGN, DEL, HKG, HAN. "
                  "European hubs (CDG, AMS) feed mostly European city-pairs. "
                  "Asian hubs feed developing-market diaspora routes with very different QSI score distributions.",
        "applicable_to": "Setting QSI expectations for Asian vs European hub carriers",
    },

    "aircraft_type_iteration": {
        "lesson": "Analysts routinely test multiple aircraft types in same workbook",
        "detail": "CI TPE-SJC has 777-300ER (84.1% LF) and A350-900 (88.6% LF). "
                  "AF CDG-SJC had similar. The non-Finalised sheet is the abandoned option. "
                  "Automated system should support multi-aircraft comparison natively.",
        "applicable_to": "Portal design  need aircraft comparison feature",
    },

    "KE_ICN_SJC_frequency_choice": {
        "lesson": "Frequency + aircraft type jointly determine commercial viability",
        "detail": "KE ICN-SJC 7x daily 777 (74.9% LF) vs 5x A350 (87.1% LF). "
                  "Same P2P forecast but connecting drops 33%. LF swing of 12pp. "
                  "Like EI DUB-SJC 4x vs 7x, but here the delivered recommendation was 5x.",
        "applicable_to": "Frequency optimisation  always test reduced frequency with smaller aircraft",
    },

    "SQ_SIN_SJC_ulr_profile": {
        "lesson": "Ultra-long-range routes are P2P dominant regardless of hub size",
        "detail": "SIN is a major hub but SQ SIN-SJC is 55% P2P. Connecting only 1.6% QSI share. "
                  "Distance and ULR aircraft config (161 seats) create a fundamentally different profile "
                  "from European hub routes. Hub size alone doesn't predict traffic mix.",
        "applicable_to": "ULR route proposals  don't apply European hub connecting assumptions",
    },

    "FI_KEF_SJC_niche_hub": {
        "lesson": "Niche hub carriers can achieve very high QSI in underserved connecting markets",
        "detail": "FI KEF-SJC: STO 15%, OSL 16.9% QSI  far above typical 2-4% for major hubs. "
                  "Icelandair's niche is Scandinavia-US where few direct alternatives exist. "
                  "Also 50% P2P capture  highest in library  Iceland tourism uniquely attractive.",
        "applicable_to": "Niche hub carriers (FI, WW, etc.)  don't use major hub QSI benchmarks",
    },

    "JX_TPE_SJC_p2p_only": {
        "lesson": "Without hub connectivity, even strong P2P markets yield unviable load factors",
        "detail": "JX TPE-SJC: 69.7k pax, 44.1% LF with 304-seat A350. "
                  "CI TPE-SJC on same city pair: 112.8k pax, 88.6% LF with 306-seat A350. "
                  "The 43k difference is entirely CI's connecting network. Hub connectivity = commercial viability.",
        "applicable_to": "Non-hub carrier route proposals  flag LF risk if no connecting traffic",
    },

    "CX_HKG_SJC_diaspora_demand": {
        "lesson": "Asian mega-hubs generate connecting traffic dominated by diaspora/VFR flows",
        "detail": "CX HKG-SJC top cities: BKK, MNL, SGN, DEL  diaspora + migrant worker + VFR flows. "
                  "Compare AF CDG-SJC top cities: mostly European business centres. "
                  "Different demand drivers = different seasonality, fare sensitivity, booking patterns.",
        "applicable_to": "Asian vs European hub connecting profile assumptions",
    },

    "CZ_CAN_SJC_china_hub": {
        "lesson": "Chinese hub route has highest growth rates but moderate total due to 3x frequency",
        "detail": "CZ CAN-SJC: business growth 4.7% CAGR, leisure 6.0% CAGR  highest in library. "
                  "But only 3x weekly with 266-seat B787-8 = 82,992 annual seats. "
                  "68,856 pax at 83% LF  commercially viable at low frequency. "
                  "CAN connecting only 2.2% QSI share despite major hub  suggests CAN feed network "
                  "less suited to US-bound connections than European or NE Asian hubs.",
        "applicable_to": "Chinese carrier route proposals  different growth/scale dynamics from European hubs",
    },

    "CZ_CAN_SJC_niche_qsi": {
        "lesson": "Niche connecting markets can have extremely high QSI scores",
        "detail": "KTM (Kathmandu) via CAN: 53.8% QSI  CZ has near-monopoly on this routing. "
                  "Similar to FI KEF-SJC Scandinavian scores (STO 15%, OSL 17%). "
                  "Small demand pools with limited alternatives produce extreme QSI concentration.",
        "applicable_to": "QSI calibration  don't assume all markets have 2-4% QSI range",
    },

    "CZ_CAN_SJC_catchment_stimulation": {
        "lesson": "Same-metro nearby service only depresses stimulation if catchments overlap",
        "detail": "CZ CAN-SJC: JZ used 1.30 stim despite CZ already operating SFO-CAN. "
                  "SJC and SFO have distinct catchments  Silicon Valley tech executives use SJC, "
                  "not SFO. Blind forecast using 1.20 stim (discounting for SFO) was 9.3% low. "
                  "Compare FI KEF-SJC where stim=1.00 because Iceland leisure pax WILL drive to SFO. "
                  "Business pax with distinct catchment = high stim. Leisure pax = low stim.",
        "applicable_to": "Any route where nearby airport has existing service  assess catchment overlap",
    },

    "BR_TPE_SJC_schedule_dominates_frequency": {
        "lesson": "Departure time impacts connecting traffic more than frequency  58% drop from schedule alone",
        "detail": "BR TPE-SJC: 5x at 20:00 = 40,059 connecting at TPE. 5x at 12:00 = 19,248 connecting. "
                  "Same airline, same frequency, same aircraft  departure time alone causes 52% drop. "
                  "Even 4x at 20:00 would outperform 5x at 12:00 on connecting. "
                  "Revenue difference: $96.6M (5x evening) vs est ~$83M (5x midday) = $14M from schedule.",
        "applicable_to": "All hub carrier route assessments  test departure time sensitivity before frequency",
    },

    "BR_TPE_SJC_cannibalisation_is_schedule_dependent": {
        "lesson": "Cannibalisation of existing service varies dramatically by schedule",
        "detail": "BR TPE-SJC cannibalisation of existing BR TPE-SFO: "
                  "SGN market: -11.8% (evening dep) vs -1.2% (midday dep). "
                  "MNL market: -7.1% vs -12.8%  different markets affected by different schedules. "
                  "Net Bay Area pax positive in all scenarios but airline must weigh new route gains "
                  "against existing SFO service erosion.",
        "applicable_to": "Any new route where carrier already serves nearby airport  model both scenarios",
    },

    "BR_TPE_SJC_tpe_feed_waves": {
        "lesson": "TPE hub connecting dominated by SE Asian arrivals in evening wave",
        "detail": "Evening TPE departures connect with SGN (11.6k), MNL (6.1k), BKK (3.9k) arrivals. "
                  "Midday departure misses all SE Asian feed completely. "
                  "SE Asia represents ~70% of TPE connecting traffic to US West Coast. "
                  "Compare with European hubs where feed is more evenly spread across day.",
        "applicable_to": "Any TPE or SE Asian hub assessment  model specific feed wave timing",
    },

    "BR_TPE_SJC_p2p_capture_higher_than_CI": {
        "lesson": "EVA Air P2P capture (45%) higher than China Airlines (30%) for same city pair",
        "detail": "BR TPE-SJC: 45% business/primary capture vs CI TPE-SJC: 30%. "
                  "Likely reflects EVA Air's stronger brand in US market and Star Alliance vs SkyTeam. "
                  "Both assessed by same analyst (JZ) using same methodology. "
                  "Different analyses: BR done 2017 (for airport pitch), CI done 2019 (for airline assessment).",
        "applicable_to": "Carrier brand strength affects P2P capture  don't use single rate for all carriers",
    },

    "LH_FRA_SJC_largest_european_pool": {
        "lesson": "FRA has largest connecting demand pool in European library but average QSI",
        "detail": "FRA connecting pool 1.87M -- largest European hub in library. But blended QSI only 3.64%, "
                  "average for major European hubs. Large pool does not guarantee high QSI share because "
                  "FRA faces intense hub competition (LHR, AMS, CDG all serve similar O&Ds). "
                  "India corridor via FRA to Silicon Valley is ~10.8k pax (DEL+MAA+BLR+BOM).",
        "applicable_to": "European major hub assessments -- pool size and QSI share are independent variables",
    },

    "LH_MUC_SJC_zero_metro_service": {
        "lesson": "Zero direct service to destination metro drives extreme stimulation and capture",
        "detail": "MUC had NO direct Bay Area service (no MUC-SFO, no MUC-SJC). This drove stimulation "
                  "to 1.50 business (highest in library) and capture to 75% business (highest in library). "
                  "Compare FRA with LH+UA to SFO: stim 1.15, capture 48%. Same airline, same destination, "
                  "same data vintage -- the only difference is existing metro service availability.",
        "applicable_to": "Any hub route where the hub has zero existing service to the destination metro area. "
                         "Must check metro-level, not just airport-level service.",
    },

    "LH_FRA_vs_MUC_secondary_beats_primary": {
        "lesson": "Secondary hub can outperform primary hub when secondary market is more underserved",
        "detail": "MUC beats FRA by 11% (124,956 vs 112,515) despite: smaller hub network (1.40M vs 1.87M pool), "
                  "smaller P2P base demand (45.6k vs 81.7k), and secondary hub status. "
                  "The stimulation/capture effect of a monopoly nonstop overwhelms the hub size advantage. "
                  "Also MUC has higher QSI per market (5.2% vs 3.6%) because less competition per individual O&D.",
        "applicable_to": "Any comparison between primary and secondary hub routes -- "
                         "don't assume the bigger hub automatically wins",
    },

    "LH_MUC_SJC_schedule_offset": {
        "lesson": "Hub temporal balance predicts schedule sensitivity magnitude",
        "detail": "MUC schedule shift from 09:30 to 12:20 only changed total pax by 1.1% because "
                  "pool/QSI offset mechanism: later departure increases pool +24% (more European cities connect) "
                  "but decreases QSI -1.08pp (longer waits for overnight Asia/CIS/Middle East arrivals). "
                  "Traffic composition shifts significantly even when total barely moves.",
        "applicable_to": "Hubs with balanced feed from multiple time zones -- schedule sensitivity may be low in total "
                         "even though individual market composition changes dramatically",
    },
}


# =============================================================================
# MODEL PARAMETERS DISCOVERED
# =============================================================================

MODEL_PARAMETERS = {
    "qsi_coefficients": {
        "source": "Jonathan (Avia employee), created 2013",
        "status": "Unchanged since creation  John acknowledges should be updated",
        "alliance_coefficients": {
            "ONLINE": 1.0,
            "ALLIANCE": 0.615,
            "INTERLINING": 0.25,
        },
    },
    "circuity_threshold": {
        "default": 0.30,  # 30%
        "status": "Now treated as variable per route (was fixed for 10 years)",
        "notes": "Based on airport location and airline type",
    },
    "elapsed_time_decay": {
        "status": "Single curve for all routes currently",
        "future": "John wants market-specific curves even if same curve used initially",
    },
    "demand_factor_up_tiers": {
        "description": "Sabre undercount adjustment by demand volume",
        "tiers": {
            ">100,000": 0.35,
            "50,000-100,000": 0.35,
            "5,000-50,000": 0.65,
            "<5,000": 0.75,
        },
        "notes": "From EI DUB-SJC Home Airport Cnx Demand sheet. Applied when Sabre understates actual traffic vs ACI/airport figures.",
    },
}


# =============================================================================
# CASES STILL TO EXTRACT (validated but data not yet structured)
# =============================================================================

PENDING_CASES = [
    # All original pending cases now extracted (Chats 43-47)
    # LH_FRA_SJC -- EXTRACTED (Chat 46-47)
    # LH_MUC_SJC -- EXTRACTED (Chat 46-47)
    # KE_ICN_SJC  EXTRACTED (7x and 5x variants)
    # SQ_SIN_SJC  EXTRACTED
    # CX_HKG_SJC  EXTRACTED
    # FI_KEF_SJC  EXTRACTED
    # JX_TPE_SJC  EXTRACTED
    # CI_TPE_SJC  EXTRACTED (Chat 43)
    "AP_ICN_SJC",       # Air Premia Seoul Incheon - San Jose (files in project, not yet extracted)
    # BR_TPE_SJC  EXTRACTED (Chat 45, 4 schedule variants)
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_case(route_id: str) -> dict:
    """Retrieve a calibration case by route ID."""
    for case in CALIBRATION_CASES:
        if case["route_id"] == route_id:
            return case
    return None


def compare_cases(*route_ids: str) -> None:
    """Print side-by-side comparison of selected cases."""
    cases = [get_case(rid) for rid in route_ids if get_case(rid)]
    if not cases:
        print("No matching cases found.")
        return

    header = f"{'Metric':<35}"
    for c in cases:
        header += f" {c['route_id']:>18}"
    print(header)
    print("-" * len(header))

    metrics = [
        ("Carrier", "carrier"),
        ("Hub Status", "hub_status"),
        ("Frequency", "frequency"),
        ("Seats/flight", "seats_per_flight"),
        ("P2P Base Demand", "p2p_base_demand"),
        ("Stimulation", "p2p_stimulation"),
        ("P2P Capture", "p2p_capture_rate"),
        ("P2P Forecast", "p2p_forecast"),
        ("Cnx Home QSI Share", "cnx_home_qsi_share_blended"),
        ("Cnx Home Forecast", "cnx_home_forecast"),
        ("Grand Total", "grand_total_forecast"),
        ("Load Factor", "load_factor"),
        ("QSI Adjustment", "qsi_adjustment"),
    ]

    for label, key in metrics:
        row = f"{label:<35}"
        for c in cases:
            val = c.get(key, "N/A")
            if isinstance(val, float):
                if val < 1:
                    row += f" {val:>17.3%}"
                else:
                    row += f" {val:>17,.1f}"
            elif isinstance(val, int):
                row += f" {val:>17,}"
            else:
                row += f" {str(val):>18}"
        print(row)


if __name__ == "__main__":
    print(f"Calibration Library: {len(CALIBRATION_CASES)} cases loaded")
    print(f"Pending extraction: {len(PENDING_CASES)} cases")
    print()
    print("=== European Hub Comparison ===")
    compare_cases("AF_CDG_SJC", "LH_FRA_SJC", "LH_MUC_SJC")
    print()
    print("=== Frequency Sensitivity ===")
    compare_cases("EI_DUB_SJC_4x", "EI_DUB_SJC_7x")
