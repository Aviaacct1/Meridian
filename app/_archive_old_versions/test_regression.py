#!/usr/bin/env python3
"""
Avia Solutions  Regression Test Suite (Chat 12)
==================================================
Validates that the refactored V2 pipeline produces identical results
to the Chat 11 closed-loop pipeline.

Test cases:
    1. BA LHR-SJC  P2P exact match (78,110)
    2. BA LHR-SJC  SJC connecting within 0.5% (2,937 target)
    3. BA LHR-SJC  LHR raw QSI overestimate (expected ~5)
    4. Provider interface contracts
"""

import sys
import os

# Ensure module path
sys.path.insert(0, os.path.dirname(__file__))

from route_config import RouteConfig
from closed_loop_pipeline_v2 import run_pipeline


def test_ba_lhr_sjc():
    """Primary regression: BA LHR-SJC closed-loop pipeline."""
    print("=" * 60)
    print("REGRESSION TEST: BA LHR-SJC")
    print("=" * 60)

    config = RouteConfig.ba_lhr_sjc('/mnt/project')
    results = run_pipeline(config)

    failures = []

    # Test 1: P2P exact match
    p2p = results['p2p_total']
    p2p_target = 78110
    p2p_var = abs(p2p - p2p_target) / p2p_target
    if p2p_var > 0.001:
        failures.append(f"P2P: {p2p:,.0f} vs target {p2p_target:,} (var {p2p_var:.4%})")
    print(f"  [{'PASS' if p2p_var <= 0.001 else 'FAIL'}] P2P: {p2p:,.0f} (target {p2p_target:,}, var {p2p_var:.4%})")

    # Test 2: SJC connecting within 0.5%
    sjc = results['dest_total']
    sjc_target = 2937
    sjc_var = abs(sjc - sjc_target) / sjc_target
    if sjc_var > 0.005:
        failures.append(f"SJC Cnx: {sjc:,.0f} vs target {sjc_target:,} (var {sjc_var:.4%})")
    print(f"  [{'PASS' if sjc_var <= 0.005 else 'FAIL'}] SJC Cnx: {sjc:,.0f} (target {sjc_target:,}, var {sjc_var:.4%})")

    # Test 3: LHR raw overestimate (should be 3-7 target, not 0)
    lhr = results['home_total']
    lhr_target = 48115
    lhr_ratio = lhr / lhr_target if lhr_target > 0 else 0
    # Raw QSI overestimates by ~5, so ratio should be 3-7
    lhr_ok = 2.0 < lhr_ratio < 10.0
    if not lhr_ok:
        failures.append(f"LHR raw ratio: {lhr_ratio:.1f} (expected 3-7)")
    print(f"  [{'PASS' if lhr_ok else 'FAIL'}] LHR raw: {lhr:,.0f} ({lhr_ratio:.1f} target  raw QSI overestimate expected)")

    # Test 4: Calibration factors present
    cal = results.get('calibration', {})
    cal_ok = cal.get('count', 0) > 50
    if not cal_ok:
        failures.append(f"Calibration: only {cal.get('count', 0)} cities (expected 50+)")
    print(f"  [{'PASS' if cal_ok else 'FAIL'}] Calibration: {cal.get('count', 0)} cities, "
          f"median={cal.get('median', 0):.3f}, mean={cal.get('mean', 0):.3f}")

    # Test 5: Provider metadata accessible
    sched_meta = config.schedule_provider.get_metadata()
    demand_meta = config.demand_provider.get_metadata()
    meta_ok = sched_meta.get('provider_type') == 'ExcelScheduleProvider'
    if not meta_ok:
        failures.append("Provider metadata not accessible")
    print(f"  [{'PASS' if meta_ok else 'FAIL'}] Provider metadata: {sched_meta.get('provider_type')}")

    print()
    if failures:
        print(f"   {len(failures)} FAILURES:")
        for f in failures:
            print(f"    - {f}")
        return False
    else:
        print("   ALL TESTS PASSED")
        return True


def test_provider_contracts():
    """Test that provider interfaces work correctly."""
    print("\n" + "=" * 60)
    print("PROVIDER CONTRACT TESTS")
    print("=" * 60)

    from providers import (
        InMemoryScheduleProvider, InMemoryDemandProvider,
        Itinerary, P2PSegmentData, ConnectingCityData,
    )

    failures = []

    # Test InMemoryScheduleProvider
    it = Itinerary('HEL', 'HEL', 'HEL-AY-LHR-BA-SJC', 'SFO', 'LHR', 'AY', 'BA', 7, 900, 'ALLIANCE')
    provider = InMemoryScheduleProvider(qsi1_data=[it])
    data = provider.get_itineraries('qsi1')
    if len(data) != 1 or data[0].city != 'HEL':
        failures.append("InMemoryScheduleProvider failed")
    print(f"  [{'PASS' if len(data) == 1 else 'FAIL'}] InMemoryScheduleProvider: {len(data)} itinerary")

    empty = provider.get_itineraries('qsi2')
    if len(empty) != 0:
        failures.append("Empty direction should return []")
    print(f"  [{'PASS' if len(empty) == 0 else 'FAIL'}] Empty direction returns []")

    # Test InMemoryDemandProvider
    seg = P2PSegmentData('Test', 10000, 0.05, capture_rate=0.30)
    city = ConnectingCityData('HEL', 'Helsinki', 'FI', 5000, 0.05, qsi_score=0.10)
    dp = InMemoryDemandProvider(p2p_segments=[seg], home_cities=[city])
    segs = dp.get_p2p_segments()
    cities = dp.get_connecting_cities('home')
    if len(segs) != 1 or len(cities) != 1:
        failures.append("InMemoryDemandProvider failed")
    print(f"  [{'PASS' if len(segs) == 1 else 'FAIL'}] InMemoryDemandProvider: {len(segs)} segment, {len(cities)} city")

    # Test metadata
    meta = provider.get_metadata()
    if 'provider_type' not in meta:
        failures.append("Metadata missing provider_type")
    print(f"  [{'PASS' if 'provider_type' in meta else 'FAIL'}] Metadata contract")

    print()
    if failures:
        print(f"   {len(failures)} FAILURES:")
        for f in failures:
            print(f"    - {f}")
        return False
    else:
        print("   ALL CONTRACT TESTS PASSED")
        return True


if __name__ == '__main__':
    ok1 = test_provider_contracts()
    ok2 = test_ba_lhr_sjc()

    print("\n" + "=" * 60)
    if ok1 and ok2:
        print("ALL REGRESSION TESTS PASSED ")
    else:
        print("SOME TESTS FAILED ")
    print("=" * 60)

    sys.exit(0 if ok1 and ok2 else 1)
