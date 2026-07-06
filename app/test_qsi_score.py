#!/usr/bin/env python3
"""
Avia Solutions - lock test for the frozen QSI method (qsi_score.py).
====================================================================
The QSI coefficients and formula are frozen and validated against the analyst SJC QSI@SJC
workbooks. Before the old coefficient copies in the runners and the production engine are
retired in favour of the single qsi_score module, this test pins down exactly what qsi_score
produces, so any accidental change to the frozen method fails loudly.

It checks:
  - the excess-time (ET) coefficient reproduces the analyst lookup EXACTLY at every published
    point (0.10 -> 0.574, 0.20 -> 0.415, 0.50 -> 0.238, 0.90 -> 0.158, 1.00 -> 0.147,
    6.10 -> 0.037), including the 0.20 float-boundary case,
  - the connection-type and service-level coefficients are the 2024-workbook values,
  - itinerary_qsi multiplies the four terms correctly,
  - the coefficients the production engine (QSIEngine) and runners must share match qsi_score,
    with the SINGLE known divergence called out: the alliance coefficient is 0.75 here (2024
    SJC workbook) versus 0.615 still defaulted in route_config.py. Resolving that is John's
    open decision; adopting 0.75 is what reproduces the SJC-HKG acceptance number.

Pure module, no heavy dependencies - runs anywhere.

RUN:
    py -3.12 test_qsi_score.py
    pytest test_qsi_score.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import qsi_score as Q

# The analyst ET lookup (SJC QSI@SJC workbook), rounded to 3dp as published.
ANALYST_ET_LOOKUP = {0.10: 0.574, 0.20: 0.415, 0.50: 0.238,
                     0.90: 0.158, 1.00: 0.147, 6.10: 0.037}

# Coefficients the engine and the runners must agree on (2024 SJC workbook).
EXPECTED_CNX = {'ONLINE': 1.00, 'ALLIANCE': 0.75, 'INTERLINE': 0.25, 'INTERLINING': 0.25}
EXPECTED_SERVICE = {0: 1.00, 1: 0.20, 2: 0.40}


def test_et_lookup_exact():
    """et_coeff reproduces the analyst lookup to the published 3dp at every point."""
    for excess, expected in ANALYST_ET_LOOKUP.items():
        got = round(Q.et_coeff(excess), 3)
        assert got == expected, f"ET({excess}) = {got}, analyst lookup = {expected}"


def test_et_nonstop_and_floor():
    """A nonstop (minimum elapsed -> zero excess) scores 1.0; negative excess clamps to 1.0."""
    assert Q.et_coeff(0) == 1.0
    assert Q.et_coeff(-1) == 1.0
    assert Q.et_coeff_from_minutes(600, 600) == 1.0          # equal elapsed -> nonstop
    # +6 min over the best routing = 0.1 hr excess -> the first ET step (0.574)
    assert round(Q.et_coeff_from_minutes(606, 600), 3) == 0.574
    # +60 min = 1.0 hr excess -> 0.147
    assert round(Q.et_coeff_from_minutes(660, 600), 3) == 0.147


def test_connection_coefficients():
    for name, val in EXPECTED_CNX.items():
        assert Q.cnx_coeff(name) == val, f"cnx_coeff({name}) = {Q.cnx_coeff(name)}, expected {val}"
    assert Q.cnx_coeff('online') == 1.00          # case-insensitive
    assert Q.cnx_coeff('unknown') == 0.0


def test_service_coefficients():
    for stops, val in EXPECTED_SERVICE.items():
        assert Q.service_coeff(stops) == val, f"service_coeff({stops}) = {Q.service_coeff(stops)}, expected {val}"
    assert Q.service_coeff(3) == 0.40             # >=2 stops clamps to the two-stop weight


def test_itinerary_qsi_product():
    """QSI = frequency x ET x cnx x service, with ET from elapsed vs the market minimum."""
    # nonstop, online, 7x/week, at the market minimum elapsed -> 7 * 1 * 1 * 1 = 7
    assert Q.itinerary_qsi(7, 600, 600, 'ONLINE', n_stops=0) == 7.0
    # alliance one-stop, 14x/week, +6 min over best -> 14 * 0.574 * 0.75 * 0.20
    expected = 14 * Q.et_coeff(0.1) * 0.75 * 0.20
    assert abs(Q.itinerary_qsi(14, 606, 600, 'ALLIANCE', n_stops=1) - expected) < 1e-9


def test_alliance_open_decision_is_flagged():
    """qsi_score holds the 2024-workbook alliance value (0.75). route_config.py still defaults
    0.615; this asserts the canonical value so the engine/runners align on consolidation. If
    this fails, the frozen method was changed - re-check against the analyst workbook."""
    assert Q.CNX_COEFF['ALLIANCE'] == 0.75
    assert Q.ET_FACTOR == 0.8 and Q.ET_INTERVAL == 0.1
    assert Q.NONSTOP_COEFF == 1.00 and Q.ONESTOP_COEFF == 0.20 and Q.TWOSTOP_COEFF == 0.40


def _run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
        passed += 1
    print(f"\n{passed} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run_all())
