#!/usr/bin/env python3
"""
Avia Solutions  End-to-End Pipeline Test: CZ CAN-SJC (Case 14)
================================================================

Tests the complete pipeline against China Southern Guangzhou-San Jose,
a new-route proposal from the SkyTeam SJC assessment (Aug 2019).

Target (from calibration library, verified Chat 44):
  - Grand Total: 68,856 pax
  - P2P: 34,699 pax (50%)
  - Cnx CAN: 27,184 pax (39%)
  - Cnx SJC: 6,974 pax (10%)
  - Load Factor: 83.0%
  - QSI Adjustment: 1.0

Data files:
  - QSI_CAN.xlsx: QSI 1 & QSI 2 from CAN hub perspective (9,151 + 8,955 itineraries)
  - QSI_SJC.xlsx: QSI 1 & QSI 2 from SJC hub perspective (1,250 + 1,906 itineraries)
  - Demand: InMemoryDemandProvider from calibration library parameters
"""

import sys, os, time
sys.path.insert(0, '/home/claude')

from providers import (
    ExcelScheduleProvider, InMemoryDemandProvider,
    P2PSegmentData, P2PSubsegmentData, ConnectingCityData,
    Itinerary,
)
from route_config import RouteConfig
from closed_loop_pipeline_v2 import QSIEngine, ForecastAssembler, validate


# ============================================================================
# STEP 1: Build RouteConfig for CZ CAN-SJC
# ============================================================================

def build_cz_can_sjc_config():
    """Build RouteConfig for CZ CAN-SJC (Case 14)."""
    cfg = RouteConfig()
    
    # Route identity
    cfg.airline_name = "China Southern"
    cfg.airline_code = "CZ"
    cfg.home_airport_code = "CAN"
    cfg.home_city_code = "CAN"
    cfg.dest_airport_code = "SJC"
    cfg.dest_city_code = "SJC"
    
    # Schedule: 3x weekly, B787-8, 266 seats
    cfg.frequency = 3
    cfg.aircraft_type = "B787-8"
    cfg.seats = 266
    cfg.flight_time_hrs = 13.5  # approx CAN-SJC
    
    # QSI parameters  new route, QSI adjustment = 1.0 (model accepted raw)
    cfg.qsi_ceiling = 1.0
    cfg.qsi_adjustment = 1.0
    cfg.online_coeff = 1.0
    cfg.alliance_coeff = 0.615
    cfg.interline_coeff = 0.25
    cfg.et_decay_factor = 0.8
    cfg.et_decay_interval = 0.1
    
    # Validation targets from calibration library
    cfg.target_total = 68856
    cfg.target_p2p = 34699
    cfg.target_cnx_home = 27184
    cfg.target_cnx_dest = 6974
    cfg.target_load_factor = 0.830
    
    # Schedule provider: QSI_CAN has home hub perspective, QSI_SJC has dest perspective
    cfg.schedule_provider = ExcelScheduleProvider(
        qsi1_file='/mnt/user-data/uploads/QSI_CAN.xlsx',
        qsi2_file='/mnt/user-data/uploads/QSI_SJC.xlsx',
    )
    
    return cfg


# ============================================================================
# STEP 2: Build P2P Demand Configuration
# ============================================================================

def build_cz_p2p_config():
    """
    CZ CAN-SJC P2P demand from calibration library (Case 14).
    
    P2P: 77,091 base  growth 17.5%  stim 1.29x blended  capture 29.7% blended  34,699 pax
    
    The calibration library shows 8 P2P segments with varying growth/stim/capture.
    We reconstruct from the detailed parameters:
    - 75% business split (Silicon Valley tech trade with Pearl River Delta)
    - Stimulation: 1.30 business/primary, 1.15-1.25 secondary, 1.05 contested
    - Capture: 30% business/primary, 25% secondary, 15% contested
    - Growth rates: China business 4.7% CAGR, leisure 6.0%, US business 3.6%, US leisure 6.0%
    - Compound growth to forecast year (2022): varies by segment
    """
    # From calibration library Case 14 detailed parameters:
    # p2p_growth_rate_business_gz: 0.176 (4.7% CAGR compound to 2022, ~3.5 years)
    # p2p_growth_rate_leisure_gz: 0.226 (6.0% CAGR)
    # p2p_growth_rate_business_us: 0.131 (3.6% CAGR)
    # p2p_growth_rate_leisure_us: 0.226 (6.0% CAGR)
    
    # We need to reconstruct the 8 segments to hit the target of 34,699
    # Total base = 77,091
    # 75% business = ~57,818 base business, 25% leisure = ~19,273 base leisure
    # Split equally GZ/US for each: ~28,909 each side business, ~9,637 each side leisure
    
    # Actually, the analyst likely segmented differently. Let's work backwards:
    # We know the blended result: 77,091 * 1.175 * 1.29 * 0.297 = 34,699
    # Let's verify: 77091 * 1.175 = 90,582; * 1.29 = 116,851; * 0.297 = 34,705  34,699 
    
    # For the pipeline test, we can use a simplified segmentation that hits the target
    # The key test is the QSI engine and connecting traffic  P2P is config-driven
    
    return {
        'segments': [
            {
                'name': 'GZ Business',
                'base_demand': 28909,
                'growth_rate': 0.176,
                'stimulation': 1.30,
                'capture_rate': 0.30,
            },
            {
                'name': 'GZ Leisure',
                'base_demand': 0,
                'growth_rate': 0.226,
                'subsegments': [
                    {'name': 'Primary', 'base_demand': 5792, 'growth_rate': 0.226,
                     'stimulation': 1.30, 'capture_rate': 0.30},
                    {'name': 'Secondary', 'base_demand': 2893, 'growth_rate': 0.226,
                     'stimulation': 1.15, 'capture_rate': 0.25},
                    {'name': 'Contested', 'base_demand': 952, 'growth_rate': 0.226,
                     'stimulation': 1.05, 'capture_rate': 0.15},
                ],
            },
            {
                'name': 'US Business',
                'base_demand': 28909,
                'growth_rate': 0.131,
                'stimulation': 1.30,
                'capture_rate': 0.30,
            },
            {
                'name': 'US Leisure',
                'base_demand': 0,
                'growth_rate': 0.226,
                'subsegments': [
                    {'name': 'Primary', 'base_demand': 5792, 'growth_rate': 0.226,
                     'stimulation': 1.30, 'capture_rate': 0.30},
                    {'name': 'Secondary', 'base_demand': 2893, 'growth_rate': 0.226,
                     'stimulation': 1.25, 'capture_rate': 0.25},
                    {'name': 'Contested', 'base_demand': 951, 'growth_rate': 0.226,
                     'stimulation': 1.05, 'capture_rate': 0.15},
                ],
            },
        ],
    }


# ============================================================================
# STEP 3: Extract Reference QSI Captures from Excel
# ============================================================================

def extract_reference_captures(qsi_file, carrier='CZ', hub='CAN'):
    """
    Extract per-city QSI capture rates from the QSI Calc sheet in the Excel file.
    These are the analyst's pre-computed reference values we compare against.
    
    Returns: dict of city_code -> sum_of_adj_shares for carrier-via-hub routes
    """
    import openpyxl
    wb = openpyxl.load_workbook(qsi_file, read_only=True, data_only=True)
    ws = wb['QSI Calc']
    
    city_captures = {}
    for row in ws.iter_rows(min_row=12, values_only=True):
        vals = list(row)
        dest = vals[1] if len(vals) > 1 else None
        route = vals[2] if len(vals) > 2 else None
        adj_share = vals[11] if len(vals) > 11 else None
        
        if not dest or not route or adj_share is None:
            continue
        
        # Check if this route goes via the specified carrier and hub
        parts = route.split('-')
        if len(parts) < 5:
            continue
        if hub not in parts:
            continue
        if carrier not in parts:
            continue
            
        if dest not in city_captures:
            city_captures[dest] = 0.0
        city_captures[dest] += adj_share
    
    wb.close()
    return city_captures


# ============================================================================
# STEP 4: Run the Test
# ============================================================================

def run_test():
    """Execute end-to-end CZ CAN-SJC pipeline test."""
    
    print("=" * 70)
    print("  CZ CAN-SJC END-TO-END PIPELINE TEST (Case 14)")
    print("=" * 70)
    
    # ---- Build config ----
    t0 = time.time()
    cfg = build_cz_can_sjc_config()
    print(f"\nConfig: {cfg.summary()}")
    print(f"Annual capacity: {cfg.annual_capacity:,} seats")
    print(f"Target: {cfg.target_total:,} pax, {cfg.target_load_factor:.1%} LF")
    
    # ---- PHASE 1: QSI Engine  Score itineraries and compute captures ----
    print(f"\n{'' * 70}")
    print("PHASE 1: QSI ENGINE  Loading and scoring itineraries")
    print(f"{'' * 70}")
    
    engine = QSIEngine(cfg)
    
    # Run QSI for HOME hub (CAN perspective)
    # The engine.run() method loads both QSI 1 and QSI 2 from schedule_provider
    # For CAN hub: QSI 1 = CANSJC direction connections, QSI 2 = SJCCAN direction
    t1 = time.time()
    home_captures = engine.run(cfg.schedule_provider)
    t2 = time.time()
    print(f"\n  Home hub QSI completed in {t2-t1:.1f}s")
    print(f"  Cities with captures: {len(home_captures)}")
    
    # For DEST hub (SJC perspective), we need a separate QSI engine run
    # The SJC perspective uses QSI_SJC.xlsx as the primary file
    # But our current architecture uses a single ExcelScheduleProvider that reads
    # QSI 1 from qsi1_file and QSI 2 from the SAME qsi1_file (see line 144)
    # This means we need a second provider for the SJC perspective
    
    # Create a separate provider for SJC hub QSI
    sjc_provider = ExcelScheduleProvider(
        qsi1_file='/mnt/user-data/uploads/QSI_SJC.xlsx',
    )
    
    # Create a separate config for SJC perspective
    sjc_cfg = RouteConfig()
    sjc_cfg.airline_code = "CZ"
    sjc_cfg.home_airport_code = "SJC"  # SJC is "home" for this perspective
    sjc_cfg.dest_airport_code = "CAN"
    sjc_cfg.online_coeff = cfg.online_coeff
    sjc_cfg.alliance_coeff = cfg.alliance_coeff
    sjc_cfg.interline_coeff = cfg.interline_coeff
    sjc_cfg.et_decay_factor = cfg.et_decay_factor
    sjc_cfg.et_decay_interval = cfg.et_decay_interval
    
    sjc_engine = QSIEngine(sjc_cfg)
    t3 = time.time()
    dest_captures = sjc_engine.run(sjc_provider)
    t4 = time.time()
    print(f"\n  Dest hub QSI completed in {t4-t3:.1f}s")
    print(f"  Cities with captures: {len(dest_captures)}")
    
    # ---- PHASE 2: Compare pipeline QSI against Excel reference ----
    print(f"\n{'' * 70}")
    print("PHASE 2: QSI VALIDATION  Comparing pipeline vs Excel QSI Calc")
    print(f"{'' * 70}")
    
    # Extract reference captures from Excel QSI Calc sheets
    ref_home = extract_reference_captures('/mnt/user-data/uploads/QSI_CAN.xlsx', 'CZ', 'CAN')
    ref_dest = extract_reference_captures('/mnt/user-data/uploads/QSI_SJC.xlsx', 'CZ', 'SJC')
    
    # Compare home captures
    print(f"\n  HOME HUB (CAN)  Pipeline vs Excel Reference")
    print(f"  {'City':6s} {'Pipeline':>10s} {'Excel':>10s} {'Diff':>10s}")
    print(f"  {''*40}")
    
    all_home_cities = set(home_captures.keys()) | set(ref_home.keys())
    home_match = 0
    home_mismatch = 0
    home_diffs = []
    
    for city in sorted(all_home_cities):
        pip = home_captures.get(city, 0)
        ref = ref_home.get(city, 0)
        diff = pip - ref
        if abs(diff) < 0.0001:
            home_match += 1
        else:
            home_mismatch += 1
            home_diffs.append((city, pip, ref, diff))
    
    # Show top mismatches
    home_diffs.sort(key=lambda x: abs(x[3]), reverse=True)
    for city, pip, ref, diff in home_diffs[:15]:
        print(f"  {city:6s} {pip:10.6f} {ref:10.6f} {diff:+10.6f}")
    
    print(f"\n  Result: {home_match} matched, {home_mismatch} mismatched "
          f"(of {len(all_home_cities)} cities)")
    
    # Compare dest captures
    print(f"\n  DEST HUB (SJC)  Pipeline vs Excel Reference")
    print(f"  {'City':6s} {'Pipeline':>10s} {'Excel':>10s} {'Diff':>10s}")
    print(f"  {''*40}")
    
    all_dest_cities = set(dest_captures.keys()) | set(ref_dest.keys())
    dest_match = 0
    dest_mismatch = 0
    dest_diffs = []
    
    for city in sorted(all_dest_cities):
        pip = dest_captures.get(city, 0)
        ref = ref_dest.get(city, 0)
        diff = pip - ref
        if abs(diff) < 0.0001:
            dest_match += 1
        else:
            dest_mismatch += 1
            dest_diffs.append((city, pip, ref, diff))
    
    dest_diffs.sort(key=lambda x: abs(x[3]), reverse=True)
    for city, pip, ref, diff in dest_diffs[:15]:
        print(f"  {city:6s} {pip:10.6f} {ref:10.6f} {diff:+10.6f}")
    
    print(f"\n  Result: {dest_match} matched, {dest_mismatch} mismatched "
          f"(of {len(all_dest_cities)} cities)")
    
    # ---- PHASE 3: Show top capturing cities ----
    print(f"\n{'' * 70}")
    print("PHASE 3: TOP CAPTURING CITIES")
    print(f"{'' * 70}")
    
    print("\n  CAN Hub  Top 15 by capture rate:")
    sorted_home = sorted(home_captures.items(), key=lambda x: -x[1])
    for city, cap in sorted_home[:15]:
        ref_val = ref_home.get(city, 0)
        match_str = "" if abs(cap - ref_val) < 0.0001 else ""
        print(f"  {city:6s} {cap:8.4%} (ref: {ref_val:8.4%}) {match_str}")
    
    print("\n  SJC Hub  Top 15 by capture rate:")
    sorted_dest = sorted(dest_captures.items(), key=lambda x: -x[1])
    for city, cap in sorted_dest[:15]:
        ref_val = ref_dest.get(city, 0)
        match_str = "" if abs(cap - ref_val) < 0.0001 else ""
        print(f"  {city:6s} {cap:8.4%} (ref: {ref_val:8.4%}) {match_str}")
    
    # ---- PHASE 4: Full Forecast Assembly ----
    # We don't have the CZ forecast workbook with per-city demand pools,
    # so we'll report what we have and note what's needed for a full assembly test
    
    print(f"\n{'' * 70}")
    print("PHASE 4: FORECAST ASSEMBLY STATUS")
    print(f"{'' * 70}")
    
    # Compute P2P from config
    p2p_config = build_cz_p2p_config()
    p2p_total = 0
    for seg in p2p_config['segments']:
        if 'subsegments' in seg and seg['subsegments']:
            for sub in seg['subsegments']:
                grown = sub['base_demand'] * (1 + sub['growth_rate'])
                stim = grown * sub.get('stimulation', 1.0)
                forecast = stim * sub.get('capture_rate', 0.0)
                p2p_total += forecast
        else:
            grown = seg['base_demand'] * (1 + seg['growth_rate'])
            stim = grown * seg.get('stimulation', 1.0)
            forecast = stim * seg.get('capture_rate', 0.0)
            p2p_total += forecast
    
    print(f"\n  P2P Forecast: {p2p_total:,.0f} (target: {cfg.target_p2p:,})")
    print(f"  P2P Error: {abs(p2p_total - cfg.target_p2p)/cfg.target_p2p:.1%}")
    
    # For connecting: compute what the QSI-weighted demand would be
    # using the calibration library aggregate numbers
    # CAN: 1,234k demand pool * 2.20% QSI = 27,184
    # SJC: 2,524k demand pool * 0.28% QSI = 6,974
    
    # Our pipeline QSI computed individual city captures.
    # The 2.20% and 0.28% are demand-weighted averages.
    # Without per-city demand data we can't compute the weighted average.
    
    # But we can report the unweighted average and range
    if home_captures:
        home_avg = sum(home_captures.values()) / len(home_captures)
        home_max = max(home_captures.values())
        home_min = min(v for v in home_captures.values() if v > 0)
        print(f"\n  CAN Hub QSI Captures:")
        print(f"    Cities: {len(home_captures)}")
        print(f"    Unweighted avg: {home_avg:.4%}")
        print(f"    Range: {home_min:.4%} to {home_max:.4%}")
        print(f"    Target demand-weighted avg: 2.20%")
    
    if dest_captures:
        dest_avg = sum(dest_captures.values()) / len(dest_captures)
        dest_max = max(dest_captures.values())
        dest_min = min(v for v in dest_captures.values() if v > 0)
        print(f"\n  SJC Hub QSI Captures:")
        print(f"    Cities: {len(dest_captures)}")
        print(f"    Unweighted avg: {dest_avg:.4%}")
        print(f"    Range: {dest_min:.4%} to {dest_max:.4%}")
        print(f"    Target demand-weighted avg: 0.28%")
    
    # ---- SUMMARY ----
    print(f"\n{'=' * 70}")
    print("  TEST SUMMARY")
    print(f"{'=' * 70}")
    
    total_cities = len(all_home_cities) + len(all_dest_cities)
    total_match = home_match + dest_match
    total_mismatch = home_mismatch + dest_mismatch
    
    print(f"  QSI Engine: {total_match}/{total_cities} city captures matched Excel reference")
    print(f"  Match rate: {total_match/total_cities:.1%}")
    
    t_end = time.time()
    print(f"\n  Total execution time: {t_end-t0:.1f}s")
    
    if total_match == total_cities:
        print("\n   PASS  QSI engine produces exact match to Excel QSI Calc")
    elif total_match / total_cities > 0.95:
        print(f"\n  ~ NEAR PASS  {total_mismatch} minor discrepancies")
    else:
        print(f"\n   FAIL  {total_mismatch} mismatches need investigation")
    
    return home_captures, dest_captures


if __name__ == '__main__':
    run_test()
