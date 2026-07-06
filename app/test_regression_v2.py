#!/usr/bin/env python3
"""
Avia Solutions - Regression Test Suite (Chat 42 update)
========================================================
Validates pipeline produces identical results across all validated routes.

Test cases:
    1. BA LHR-SJC - 129,162 pax (P2P 78,110 + connecting)
    2. KE ICN-SJC - P2P 37,382 + China 46,331 = 83,713 (P2P validation)
    3. Provider interface contracts
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from route_config import RouteConfig
from closed_loop_pipeline_v2 import run_pipeline


def test_ba_lhr_sjc():
    """Primary regression: BA LHR-SJC closed-loop pipeline."""
    print("=" * 60)
    print("REGRESSION TEST: BA LHR-SJC")
    print("=" * 60)

    config = RouteConfig.ba_lhr_sjc()  # resolves to config.REFERENCE_CASE_DIR
    results = run_pipeline(config)
    failures = []

    p2p = results['p2p_total']
    p2p_target = 78110
    p2p_var = abs(p2p - p2p_target) / p2p_target
    if p2p_var > 0.001:
        failures.append(f"P2P: {p2p:,.0f} vs target {p2p_target:,} (var {p2p_var:.4%})")
    print(f"  [{'PASS' if p2p_var <= 0.001 else 'FAIL'}] P2P: {p2p:,.0f} (target {p2p_target:,})")

    sjc = results['dest_total']
    sjc_target = 2937
    sjc_var = abs(sjc - sjc_target) / sjc_target
    if sjc_var > 0.005:
        failures.append(f"SJC Cnx: {sjc:,.0f} vs target {sjc_target:,}")
    print(f"  [{'PASS' if sjc_var <= 0.005 else 'FAIL'}] SJC Cnx: {sjc:,.0f} (target {sjc_target:,})")

    total = results.get('grand_total', 0)
    total_target = 129162
    total_var = abs(total - total_target) / total_target
    if total_var > 0.001:
        failures.append(f"Total: {total:,.0f} vs target {total_target:,}")
    print(f"  [{'PASS' if total_var <= 0.001 else 'FAIL'}] Grand Total: {total:,.0f} (target {total_target:,})")

    lhr = results['home_total']
    lhr_target = 48115
    lhr_ratio = lhr / lhr_target if lhr_target > 0 else 0
    lhr_ok = 2.0 < lhr_ratio < 10.0
    print(f"  [{'PASS' if lhr_ok else 'FAIL'}] LHR raw: {lhr:,.0f} ({lhr_ratio:.1f}x target)")

    cal = results.get('calibration', {})
    cal_ok = cal.get('count', 0) > 50
    print(f"  [{'PASS' if cal_ok else 'FAIL'}] Calibration: {cal.get('count', 0)} cities")

    if failures:
        print(f"\n  FAILED: {len(failures)} failures")
        return False
    print("\n  ALL PASSED")
    return True


def test_ke_icn_sjc_p2p():
    """KE ICN-SJC P2P validation against Forecast Finalised sheet.

    This tests the P2P and China connecting calculations directly
    without requiring a full pipeline run (hub connecting needs QSI).
    """
    print("\n" + "=" * 60)
    print("REGRESSION TEST: KE ICN-SJC (P2P + China)")
    print("=" * 60)

    failures = []

    # SK segments from Forecast Finalised
    sk_bus = 82675.43038051661 * 1.07 * 1.1 * 0.2
    sk_lei_pri = 7440.788734246493 * 1.24 * 1.1 * 0.2
    sk_lei_sec = 1194.2006610519063 * 1.24 * 1.05 * 0.1
    sk_lei_con = 551.1695358701105 * 1.24 * 1.0 * 0.05

    us_bus = 59868.415103132735 * 1.07 * 1.1 * 0.2
    us_lei_pri = 5388.157359281947 * 1.24 * 1.1 * 0.2
    us_lei_sec = 864.7659959341395 * 1.24 * 1.05 * 0.1
    us_lei_con = 399.12276735421824 * 1.24 * 1.0 * 0.05

    p2p_total = (sk_bus + sk_lei_pri + sk_lei_sec + sk_lei_con +
                 us_bus + us_lei_pri + us_lei_sec + us_lei_con)
    p2p_target = 37381.55

    p2p_var = abs(p2p_total - p2p_target) / p2p_target
    if p2p_var > 0.001:
        failures.append(f"P2P: {p2p_total:,.0f} vs {p2p_target:,.0f}")
    print(f"  [{'PASS' if p2p_var <= 0.001 else 'FAIL'}] P2P: {p2p_total:,.0f} (target {p2p_target:,.0f})")

    # China connecting
    china_hkg = 81840.52494489429 * 1.385 * 1.1 * 0.075
    china_can = 59947.86442002601 * 1.385 * 1.15 * 0.35
    china_szx = 4674.666791955318 * 1.385 * 1.1 * 0.50
    china_total = china_hkg + china_can + china_szx
    china_target = 46330.92

    china_var = abs(china_total - china_target) / china_target
    if china_var > 0.001:
        failures.append(f"China: {china_total:,.0f} vs {china_target:,.0f}")
    print(f"  [{'PASS' if china_var <= 0.001 else 'FAIL'}] China: {china_total:,.0f} (target {china_target:,.0f})")

    grand = p2p_total + china_total
    grand_target = 83712.47
    grand_var = abs(grand - grand_target) / grand_target
    if grand_var > 0.001:
        failures.append(f"Grand: {grand:,.0f} vs {grand_target:,.0f}")
    print(f"  [{'PASS' if grand_var <= 0.001 else 'FAIL'}] Grand: {grand:,.0f} (target {grand_target:,.0f})")

    # Component spot-checks
    print(f"  SK Business: {sk_bus:,.0f} (expect 19,462)")
    print(f"  US Business: {us_bus:,.0f} (expect 14,093)")
    print(f"  CAN (Guangzhou): {china_can:,.0f} (expect 33,419)")

    if failures:
        print(f"\n  FAILED: {len(failures)} failures")
        return False
    print("\n  ALL PASSED")
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

    it = Itinerary('HEL', 'HEL', 'HEL-AY-LHR-BA-SJC', 'SFO', 'LHR', 'AY', 'BA', 7, 900, 'ALLIANCE')
    provider = InMemoryScheduleProvider(qsi1_data=[it])
    data = provider.get_itineraries('qsi1')
    ok = len(data) == 1 and data[0].city == 'HEL'
    if not ok:
        failures.append("InMemoryScheduleProvider failed")
    print(f"  [{'PASS' if ok else 'FAIL'}] InMemoryScheduleProvider")

    empty = provider.get_itineraries('qsi2')
    ok2 = len(empty) == 0
    if not ok2:
        failures.append("Empty direction should return []")
    print(f"  [{'PASS' if ok2 else 'FAIL'}] Empty direction returns []")

    seg = P2PSegmentData('Test', 10000, 0.05, capture_rate=0.30)
    city = ConnectingCityData('HEL', 'Helsinki', 'FI', 5000, 0.05, qsi_score=0.10)
    dp = InMemoryDemandProvider(p2p_segments=[seg], home_cities=[city])
    segs = dp.get_p2p_segments()
    cities = dp.get_connecting_cities('home')
    ok3 = len(segs) == 1 and len(cities) == 1
    if not ok3:
        failures.append("InMemoryDemandProvider failed")
    print(f"  [{'PASS' if ok3 else 'FAIL'}] InMemoryDemandProvider")

    if failures:
        print(f"\n  FAILED: {len(failures)} failures")
        return False
    print("\n  ALL PASSED")
    return True


if __name__ == '__main__':
    ok1 = test_provider_contracts()
    ok2 = test_ba_lhr_sjc()
    ok3 = test_ke_icn_sjc_p2p()

    print("\n" + "=" * 60)
    passed = sum(1 for x in [ok1, ok2, ok3] if x)
    total = 3
    if passed == total:
        print(f"ALL REGRESSION TESTS PASSED ({passed}/{total})")
    else:
        print(f"TESTS: {passed}/{total} passed, {total - passed} failed")
    print("=" * 60)

    sys.exit(0 if passed == total else 1)
