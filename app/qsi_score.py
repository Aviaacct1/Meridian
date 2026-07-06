#!/usr/bin/env python3
"""
Avia Solutions - QSI scoring (single source of truth for the validated QSI method).
==============================================================================
The established Avia QSI score, validated against the analyst SJC QSI@SJC workbooks
(Cathay 2024; reproduces the SJC-HKG "Total QSI Score for Market" ~65.6%):

    qsi = Frequency x ET-coeff x connection-type-coeff x service-level-coeff

  ET-coeff (excess-time penalty vs the MINIMUM-elapsed routing for that market):
    et = 1 / ((int(excess_hrs / ET_INTERVAL) + 1) ^ ET_FACTOR)     ET_FACTOR 0.8, ET_INTERVAL 0.1
    Reproduces the analyst lookup exactly: 0.10->0.574, 0.20->0.415, 0.50->0.238,
    0.90->0.158, 1.00->0.147, 6.10->0.037. The nonstop advantage comes through ET
    (nonstop = minimum elapsed -> ET 1.0).
  connection-type-coeff: ONLINE 1.00 / ALLIANCE 0.75 / INTERLINING 0.25
  service-level-coeff:   nonstop 1.00 / one-stop 0.20 / two-stop 0.40

Fair share = route_qsi / market_qsi. The full method computes QSI1 (outbound) and
QSI2 (the reverse) and reports the AVERAGE of the two fair shares; callers holding
both directions should average them.

ONE definition of the coefficients and the formula lives here, so the runners and the
production engine cannot drift apart again (alliance previously sat at 0.615 in one
runner and 0.75 in another, which understated capture). Change the method in one place.
"""

ET_FACTOR = 0.8
ET_INTERVAL = 0.1

# Connection-type coefficient (online vs alliance vs interline). 2024 SJC workbook = 0.75.
CNX_COEFF = {'ONLINE': 1.00, 'ALLIANCE': 0.75, 'INTERLINING': 0.25, 'INTERLINE': 0.25}

# Service-level coefficient by number of connection stops (nonstop 0 / one-stop 1 / two-stop 2).
NONSTOP_COEFF = 1.00
ONESTOP_COEFF = 0.20
TWOSTOP_COEFF = 0.40
SERVICE_COEFF = {0: NONSTOP_COEFF, 1: ONESTOP_COEFF, 2: TWOSTOP_COEFF}


def et_coeff(excess_hrs):
    """Excess-time penalty relative to the market's minimum-elapsed routing (hours)."""
    if excess_hrs <= 0:
        return 1.0
    return 1.0 / ((int(excess_hrs / ET_INTERVAL) + 1) ** ET_FACTOR)


def et_coeff_from_minutes(elapsed_min, min_elapsed_min):
    return et_coeff((elapsed_min - min_elapsed_min) / 60.0)


def cnx_coeff(cnx_type):
    return CNX_COEFF.get(str(cnx_type).upper(), 0.0)


def service_coeff(n_stops):
    n = int(n_stops)
    return SERVICE_COEFF.get(n, TWOSTOP_COEFF if n >= 2 else NONSTOP_COEFF)


def itinerary_qsi(frequency, elapsed_min, min_elapsed_min, cnx_type, n_stops=1):
    """QSI score for one itinerary within a market.
    min_elapsed_min = the market's best (minimum-elapsed) routing, for the ET penalty."""
    return (frequency
            * et_coeff_from_minutes(elapsed_min, min_elapsed_min)
            * cnx_coeff(cnx_type)
            * service_coeff(n_stops))
