"""Avia Cortex - airport capture overrides + systematic capture correction factors.
====================================================================================
Two layers, both keyed on the ORIGIN airport of a forecast route (it now has the competing nonstop):

1. AIRPORT_CAPTURE - measured catchment TRUTH (passenger surveys, mobility data, a catchment study) that
   beats the model's drive-time + size-pull allocation: set the airport's capture SHARE directly.
2. capture_factors (airport_capture_factors.json, from build_airport_capture.py) - a systematic per-airport
   MULTIPLIER learned from the back-test outturn, centring each airport that consistently over/under-forecasts.
   Leave-one-out assessed across the cohort. The share (base) x the factor (correction) = one clean mechanism.

Precedence for the SHARE: a user's Expert override wins; then AIRPORT_CAPTURE; then the model. The factor is a
separate multiplier applied on top of whatever share is used.

Why AIRPORT_CAPTURE exists: the size-pull that stops small airports over-reading also UNDER-reads a genuine
secondary airport with its own catchment. SJC is the textbook case - the South Bay is a distinct ~3m catchment,
but SFO's size dominates the choice model, so SJC models ~0.11 while survey + mobility show ~0.32 with service.
The residual under-forecast beyond that (back-test outturn) is handled by the systematic factor, not a manual bump.
"""
import os, json

AIRPORT_CAPTURE = {
    # code: capture share of the catchment market with a competing nonstop  (source)
    "SJC": 0.32,   # South Bay distinct ~3m catchment; Avia survey + cell-phone data, 30-35% with service
}

# Destination-side pull, keyed on the ARRIVAL airport, but CONDITIONAL ON A THIN MEASURED MARKET. Same catchment
# cause as AIRPORT_CAPTURE, mirror image: SFO dominates the model's allocation of trips DESTINED for the South Bay,
# so demand flying INTO a genuine secondary is under-credited. But that leakage bites where the O&D is THIN and
# catchment-allocated; a big directly-measured market (LHR-SJC) needs no lift, and a blanket 2x over-forecast it.
# So apply the lift ONLY below a market ceiling. (dest: (factor, max_market)). DEMO PROXY - market size stands in
# for "catchment-allocated vs directly-measured"; refine to the real market-bucket model later.
AIRPORT_DEST_THIN = {
    "SJC": (2.0, 200000.0),   # 2x lift on inbound-SJC demand only where the measured O&D < 200k (excludes LHR-SJC)
}

_FACTORS = None
_FACTORS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "airport_capture_factors.json")


# A secondary airport's survey capture (e.g. SJC 0.32) is measured on ITS local catchment. Applied flat to the
# whole metro market it over-recaptures on very large markets (SJC would not pull 32% of the entire Bay Area's
# Boston demand - that traffic is nearer SFO). So the capture holds up to a market its South-Bay catchment can
# supply, then tapers gently (sqrt) above it. Tuned so typical markets (Taipei ~160k) are untouched and only
# large ones (Boston ~655k) come down. DEMO PROXY for the proper point-of-origin recapture model.
CAPTURE_TAPER_MARKET = 250000.0


def capture_for(origin, market=None):
    """Measured capture SHARE for this origin airport, tapered on markets larger than its catchment can supply,
    or None to use the model."""
    base = AIRPORT_CAPTURE.get((origin or "").upper())
    if base is None:
        return None
    if market and float(market) > CAPTURE_TAPER_MARKET:
        base = base * (CAPTURE_TAPER_MARKET / float(market)) ** 0.5
    return float(base)


def dest_thin_factor(dest, market):
    """Destination-side capture lift for an under-credited secondary (SJC inbound), applied ONLY where the
    measured O&D `market` is below the airport's ceiling - so thin catchment-allocated markets get the lift and
    big directly-measured ones (LHR-SJC) do not. Returns 1.0 otherwise."""
    cfg = AIRPORT_DEST_THIN.get((dest or "").upper())
    if not cfg or market is None:
        return 1.0
    factor, max_market = cfg
    return float(factor) if float(market) < float(max_market) else 1.0


def factor_for(origin):
    """Systematic capture-correction MULTIPLIER for this origin airport (>1 lifts an under-forecast airport),
    or 1.0 if none. Loaded from airport_capture_factors.json (build_airport_capture.py). Applied on top of the
    share, so base_share x factor is the single correction."""
    global _FACTORS
    if _FACTORS is None:
        _FACTORS = {}
        try:
            with open(_FACTORS_PATH, encoding="utf-8") as fh:
                _FACTORS = (json.load(fh).get("factors") or {})
        except Exception:
            _FACTORS = {}
    return float(_FACTORS.get((origin or "").upper(), 1.0))
