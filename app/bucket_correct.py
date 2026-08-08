#!/usr/bin/env python3
r"""
Avia Cortex - all-data bucket calibration applied to the LIVE forecast.
=======================================================================
The engine is calibrated on all the launch history (Mark's approach: backtest on ALL data, no hold-out). The
bucket model (bucket_model.json, 60 airport archetypes x direction/intl/market/haul sub-factors, in-sample 55.6%
within +/-20%) is that calibration. Here it nudges a live forecast: each airport sits in a bucket, and a route
has two endpoints, so we take the origin's OUTbound factor and the destination's INbound factor for the route's
segment and combine them (geometric mean), clamped so it can only ever be a bounded correction, never a wild one.
Defaults to 1.0 (no change) for any airport/segment the model doesn't cover.
"""
import json, os, math

_M = None
_AP = None
LOAD_FAILURES = []      # read by the callers and printed by the runner


def _model():
    """The bucket model. A model that does not load SAYS so.

    7 August: bucket_model.json was missing from the working copy and this
    returned empty factors, so the correction was off and every forecast on that
    copy was uncorrected with nothing to say why. An empty factor table and a
    table of ones are indistinguishable in the output, which is exactly why the
    absence has to be announced rather than absorbed.
    """
    global _M
    if _M is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bucket_model.json")
        try:
            _M = json.load(open(path))
        except Exception as e:
            _M = {"airport_bucket": {}, "factors": {}}
            msg = ("bucket_correct: bucket_model.json did not load (%s: %s). The "
                   "airport bucket correction is OFF and demand is uncorrected."
                   % (type(e).__name__, e))
            LOAD_FAILURES.append(msg)
            print("WARNING: %s" % msg)
    return _M


def _ap():
    global _AP
    if _AP is None:
        try:
            import airportsdata
            _AP = airportsdata.load("IATA")
        except Exception:
            _AP = {}
    return _AP


def _mktband(m):
    return "t" if m < 15000 else "s" if m < 50000 else "m" if m < 150000 else "L"


def _haulband(g):
    return "sh" if g < 800 else "md" if g < 2500 else "lg" if g < 6000 else "xl"


def forecast_factor(dep, arr, market, gcd_km, clamp=(0.7, 1.4)):
    """Bounded all-data calibration multiplier for a live route forecast (1.0 = no change)."""
    M = _model(); ab = M.get("airport_bucket", {}); F = M.get("factors", {})
    dep = (dep or "").upper(); arr = (arr or "").upper()
    ap = _ap(); dc = ap.get(dep, {}).get("country"); ac = ap.get(arr, {}).get("country")
    intl = "I" if (dc and ac and dc != ac) else "D"
    mk = _mktband(market or 0); hb = _haulband(gcd_km or 0)
    fd = F.get(f"{ab.get(dep)}|out|{intl}|{mk}|{hb}", 1.0) if dep in ab else 1.0
    fa = F.get(f"{ab.get(arr)}|in|{intl}|{mk}|{hb}", 1.0) if arr in ab else 1.0
    f = math.sqrt(float(fd) * float(fa))
    return max(clamp[0], min(clamp[1], f))
