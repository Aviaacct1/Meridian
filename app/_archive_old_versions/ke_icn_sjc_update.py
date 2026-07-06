#!/usr/bin/env python3
"""
Avia Solutions  KE ICN-SJC Factory Method & Updated Regression Test
====================================================================
Chat 42 deliverables:
  1. RouteConfig.ke_icn_sjc() factory method 
  2. Updated regression test with KE as third anchor
  3. Calibration library pipeline-validated addendum

Based on the FcstKE_ICNSJC_212Aug19.xlsm "Forecast Finalised" sheet data.
This is the Aug 2019 vintage, forecast year ~2020-2021.
"""

import os
import sys
from datetime import time as dtime
from typing import Dict, Any

# ================================================================
# 1. FACTORY METHOD  to be added to route_config_v2.py
# ================================================================

def ke_icn_sjc_factory_method():
    """
    Returns the code block for RouteConfig.ke_icn_sjc() factory method.
    To be inserted into route_config_v2.py after klm_ams_tpa().
    """
    return '''
    @classmethod
    def ke_icn_sjc(cls, project_dir: str = '/mnt/project') -> 'RouteConfig':
        """
        Korean Air ICN-SJC (Aug 2019 vintage, forecast year 2020).
        Target: P2P 37,382 pax (from Forecast Finalised sheet)
        
        Key characteristics:
        - New route proposal (KE not operating ICN-SJC, but operates ICN-SFO)
        - Sixth-freedom Asian hub carrier  massive connecting network at ICN
        - QSI adjustment = 1.0 (model accepted raw  new route)
        - P2P split: SK visitors 58%, US residents 42%
        - Business split: SK 90% business / US 80% business
        - China connecting markets (HKG/CAN/SZX) treated separately
        - Base year: 2017 Sabre data with growth to 2020
        - Proxy schedule analysis (SZX-SJC HU used as schedule proxy)
        """
        cfg = cls()
        cfg.airline_name = "Korean Air"
        cfg.airline_code = "KE"
        cfg.home_airport_code = "ICN"
        cfg.home_city_code = "SEL"
        cfg.dest_airport_code = "SJC"
        cfg.dest_city_code = "SJC"

        cfg.frequency = 7  # daily
        cfg.aircraft_type = "B787-8"  # proxy from schedule sheet
        cfg.seats = 213  # from Proposed Schedule sheet
        cfg.outbound_dep = dtime(12, 40)  # proxy SZX times
        cfg.outbound_arr = dtime(10, 25)
        cfg.return_dep = dtime(12, 25)
        cfg.return_arr = dtime(17, 55)
        cfg.flight_time_hrs = 12.75  # ~12:45

        # QSI parameters
        cfg.qsi_ceiling = 0.85
        cfg.qsi_adjustment = 1.0  # new route  model accepted raw
        cfg.online_coeff = 1.0
        cfg.alliance_coeff = 0.615
        cfg.interline_coeff = 0.25
        cfg.et_decay_factor = 0.8
        cfg.et_decay_interval = 0.1

        # Validation targets from Forecast Finalised sheet
        # P2P total: 37,382 (SK 21,681 + US 15,700)
        # China connecting: 46,331 (HKG 9,351 + CAN 33,419 + SZX 3,561)
        # Hub connecting at ICN: not populated in file (requires QSI run)
        # Hub connecting at SJC: not populated in file (requires QSI run)
        cfg.target_p2p = 37382
        cfg.target_china_cnx = 46331
        cfg.target_total = 83713  # P2P + China only (connecting requires QSI)
        cfg.target_cnx_home = 0  # not available from this file
        cfg.target_cnx_dest = 0  # not available from this file
        cfg.target_load_factor = 0.0  # not calculable without full connecting

        # P2P demand provider config
        p2p_config = _ke_icn_sjc_p2p_config()
        cfg.demand_provider = ExcelDemandProvider(
            forecast_file=os.path.join(project_dir, 'FcstKE_ICNSJC_212Aug19.xlsm'),
            p2p_config=p2p_config,
            home_growth=0.112,  # 11.2% compound for ICN connecting
            dest_growth=0.044,  # 4.4% for SJC connecting
        )

        # Schedule provider  uses QSI files for ICN and SJC
        cfg.schedule_provider = ExcelScheduleProvider(
            qsi1_file=os.path.join(project_dir, 'OAGICN_AUG18.xlsx'),
            qsi2_file=os.path.join(project_dir, 'OAGSJC_Aug18.xlsx'),
        )

        return cfg
'''


def ke_icn_sjc_p2p_config():
    """
    KE ICN-SJC P2P demand configuration from Forecast Finalised sheet.
    
    Structure mirrors BA LHR-SJC with visitor/resident segments
    and business/leisure splits within each.
    
    South Korea (Visitors): 58% of P2P, 90% business
    US (Residents): 42% of P2P, 80% business
    
    Growth rates: SK 7% (business), 24% (leisure); US 7% (business), 24% (leisure)
    """
    return {
        'segments': [
            {
                'name': 'SK Business',
                'base_demand': 82675.43038051661,
                'growth_rate': 0.07,
                'seasonality': 1.0,
                'stimulation': 1.1,
                'capture_rate': 0.20,
                # Expected forecast: 19,461.80
            },
            {
                'name': 'SK Leisure/VFR',
                'base_demand': 0,  # computed from subsegments
                'growth_rate': 0.24,
                'seasonality': 1.0,
                'stimulation': 1.0,
                'capture_rate': 0.0,
                'subsegments': [
                    {'name': 'Primary', 'base_demand': 7440.788734246493, 'growth_rate': 0.24,
                     'seasonality': 1.0, 'stimulation': 1.1, 'capture_rate': 0.20},
                    {'name': 'Secondary', 'base_demand': 1194.2006610519063, 'growth_rate': 0.24,
                     'seasonality': 1.0, 'stimulation': 1.05, 'capture_rate': 0.10},
                    {'name': 'Contested', 'base_demand': 551.1695358701105, 'growth_rate': 0.24,
                     'seasonality': 1.0, 'stimulation': 1.0, 'capture_rate': 0.05},
                ],
            },
            {
                'name': 'US Business',
                'base_demand': 59868.415103132735,
                'growth_rate': 0.07,
                'seasonality': 1.0,
                'stimulation': 1.1,
                'capture_rate': 0.20,
                # Expected forecast: 14,093.02
            },
            {
                'name': 'US Leisure/VFR',
                'base_demand': 0,
                'growth_rate': 0.24,
                'seasonality': 1.0,
                'stimulation': 1.0,
                'capture_rate': 0.0,
                'subsegments': [
                    {'name': 'Primary', 'base_demand': 5388.157359281947, 'growth_rate': 0.24,
                     'seasonality': 1.0, 'stimulation': 1.1, 'capture_rate': 0.20},
                    {'name': 'Secondary', 'base_demand': 864.7659959341395, 'growth_rate': 0.24,
                     'seasonality': 1.0, 'stimulation': 1.05, 'capture_rate': 0.10},
                    {'name': 'Contested', 'base_demand': 399.12276735421824, 'growth_rate': 0.24,
                     'seasonality': 1.0, 'stimulation': 1.0, 'capture_rate': 0.05},
                ],
            },
        ],
        # China connecting markets (separate from hub connecting)
        'china_connecting': [
            {'city': 'HKG', 'base_demand': 81840.52494489429, 'growth_rate': 0.385,
             'stimulation': 1.1, 'capture_rate': 0.075,
             # Expected: 9,351
             },
            {'city': 'CAN', 'base_demand': 59947.86442002601, 'growth_rate': 0.385,
             'stimulation': 1.15, 'capture_rate': 0.35,
             # Expected: 33,419
             },
            {'city': 'SZX', 'base_demand': 4674.666791955318, 'growth_rate': 0.385,
             'stimulation': 1.1, 'capture_rate': 0.50,
             # Expected: 3,561
             },
        ],
    }


# ================================================================
# 2. VALIDATION  verify the P2P calculation matches exactly
# ================================================================

def validate_ke_p2p():
    """Validate P2P calculation against Forecast Finalised values."""
    config = ke_icn_sjc_p2p_config()
    
    print("=" * 60)
    print("KE ICN-SJC P2P VALIDATION")
    print("=" * 60)
    
    total_p2p = 0
    
    for seg in config['segments']:
        if seg.get('subsegments'):
            for sub in seg['subsegments']:
                base = sub['base_demand']
                grown = base * (1 + sub['growth_rate'])
                stimmed = grown * sub['stimulation']
                forecast = stimmed * sub['capture_rate']
                total_p2p += forecast
                print(f"  {seg['name']}/{sub['name']}: {base:,.0f}  {grown:,.0f}  {stimmed:,.0f}  {sub['capture_rate']:.0%} = {forecast:,.0f}")
        elif seg['base_demand'] > 0:
            base = seg['base_demand']
            grown = base * (1 + seg['growth_rate'])
            stimmed = grown * seg['stimulation']
            forecast = stimmed * seg['capture_rate']
            total_p2p += forecast
            print(f"  {seg['name']}: {base:,.0f}  {grown:,.0f}  {stimmed:,.0f}  {seg['capture_rate']:.0%} = {forecast:,.0f}")
    
    print(f"\n  P2P Total: {total_p2p:,.0f}")
    
    # China connecting
    total_china = 0
    print("\n  China Connecting:")
    for cn in config['china_connecting']:
        base = cn['base_demand']
        grown = base * (1 + cn['growth_rate'])
        stimmed = grown * cn['stimulation']
        forecast = stimmed * cn['capture_rate']
        total_china += forecast
        print(f"    {cn['city']}: {base:,.0f}  {grown:,.0f}  {stimmed:,.0f}  {cn['capture_rate']:.0%} = {forecast:,.0f}")
    
    print(f"\n  China Total: {total_china:,.0f}")
    print(f"  P2P + China: {total_p2p + total_china:,.0f}")
    
    # Validate against targets
    p2p_target = 37381.55
    china_target = 46330.92
    
    p2p_var = abs(total_p2p - p2p_target) / p2p_target
    china_var = abs(total_china - china_target) / china_target
    
    print(f"\n  P2P variance: {p2p_var:.4%} {'PASS' if p2p_var < 0.01 else 'FAIL'}")
    print(f"  China variance: {china_var:.4%} {'PASS' if china_var < 0.01 else 'FAIL'}")
    
    return p2p_var < 0.01 and china_var < 0.01


# ================================================================
# 3. CALIBRATION LIBRARY ADDENDUM  pipeline-validated data
# ================================================================

KE_ICN_SJC_PIPELINE_ADDENDUM = {
    "route_id": "KE_ICN_SJC_FcstFinalised",
    "description": "KE ICN-SJC from FcstKE_ICNSJC_212Aug19.xlsm Forecast Finalised sheet",
    "vintage": "Aug 2019 file, 2017 base data, forecast year 2020",
    "p2p_validated": {
        "sk_business": {"base": 82675.43, "growth": 0.07, "stim": 1.1, "capture": 0.20, "forecast": 19462},
        "sk_leisure_pri": {"base": 7440.79, "growth": 0.24, "stim": 1.1, "capture": 0.20, "forecast": 2030},
        "sk_leisure_sec": {"base": 1194.20, "growth": 0.24, "stim": 1.05, "capture": 0.10, "forecast": 155},
        "sk_leisure_con": {"base": 551.17, "growth": 0.24, "stim": 1.0, "capture": 0.05, "forecast": 34},
        "us_business": {"base": 59868.42, "growth": 0.07, "stim": 1.1, "capture": 0.20, "forecast": 14093},
        "us_leisure_pri": {"base": 5388.16, "growth": 0.24, "stim": 1.1, "capture": 0.20, "forecast": 1470},
        "us_leisure_sec": {"base": 864.77, "growth": 0.24, "stim": 1.05, "capture": 0.10, "forecast": 113},
        "us_leisure_con": {"base": 399.12, "growth": 0.24, "stim": 1.0, "capture": 0.05, "forecast": 25},
        "total_p2p": 37382,
    },
    "china_connecting_validated": {
        "hkg": {"base": 81841, "growth": 0.385, "stim": 1.1, "capture": 0.075, "forecast": 9351},
        "can": {"base": 59948, "growth": 0.385, "stim": 1.15, "capture": 0.35, "forecast": 33419},
        "szx": {"base": 4675, "growth": 0.385, "stim": 1.1, "capture": 0.50, "forecast": 3561},
        "total_china": 46331,
    },
    "hub_connecting_icn": {
        "status": "Not populated in Forecast Finalised  requires QSI model run",
        "demand_base": {
            "with_direct_comp": 478541,
            "no_direct_comp": 1153589,
            "total": 1632130,
            "growth_rate": 0.112,
        },
        "top_cities": ["MNL", "TYO", "DEL", "BJS", "SHA", "SGN", "TPE", "BOM", "HKG", "CAN"],
    },
    "hub_connecting_sjc": {
        "status": "Not populated in Forecast Finalised  requires QSI model run",
        "demand_base": {
            "with_direct_comp": 1868724,
            "no_direct_comp": 241813,
            "total": 2110537,
            "growth_rate": 0.044,
        },
        "top_cities": ["LAX", "NYC", "YVR", "SEA", "CHI", "LAS", "ATL", "DFW", "BOS", "MEX"],
    },
    "calibration_observations": [
        "QSI adjustment = 1.0 across all segments (new route, model accepted raw)",
        "Factor up = 1.0, Premium = 1.0 (no adjustments)",
        "SK/US P2P capture rates identical at 20% for business  symmetric unlike BA LHR-SJC",
        "Stimulation 1.1 for business (both SK and US)  moderate for new route",
        "SK leisure primary same stim 1.1 and 20% capture as business  unusual",
        "Very high leisure growth rate (24%)  likely post-pandemic compound recovery",
        "China connecting has much higher capture rates (7.5-50%) than hub connecting",
        "CAN (Guangzhou) dominates China connecting at 33,419  72% of China total",
        "SZX (Shenzhen) has 50% capture despite small base  closest catchment?",
        "File is actually a SZX-SJC proxy analysis reused for KE  schedule data is HU not KE",
        "Two vintages exist (Aug18 and Aug19)  both Forecast Finalised sheets are identical",
    ],
}


if __name__ == '__main__':
    ok = validate_ke_p2p()
    print("\n" + "=" * 60)
    print("OVERALL:", "PASS " if ok else "FAIL ")
    print("=" * 60)
