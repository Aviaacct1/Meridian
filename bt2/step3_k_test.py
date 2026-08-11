#!/usr/bin/env python3
"""Avia Solutions - STEP 3 of the QSI connecting build, 11 August 2026.

Switches the QSI feed on and measures SJC-TPE against the flat-rate baseline, without editing the
engine. It wraps route_forecast.forecast and injects the four keys the QSI branch needs into the
feed_cfg cortex_app already builds, so everything else on the path is the product's own: the same
catchment, the same reference year, the same aircraft and the same schedule.

The schedule is taken from the payload cortex_app itself returns for this case, 11:00 local departure
and an 825 minute block, so the departure time fed to the QSI branch is the one the product shows.

Arms: the flat-rate baseline, then the QSI feed at k = 1.0 (the 2025 analyst's method, no re-levelling
constant) and at k = 0.06 (the qsi_feed default) for reference.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), "app")
if APP not in sys.path:
    sys.path.insert(0, APP)

import cortex_app as CA                          # noqa: E402
import route_forecast as RF                      # noqa: E402

DEP_TIME_MINS = 11 * 60                          # 11:00 local, the schedule cortex_app returns
FLYING_MINS = 825                                # block minutes for the same schedule
FREQ = 4

_real_forecast = RF.forecast


def _patched(*a, **kw):
    """Add the QSI-feed switches to the feed_cfg cortex_app built, and leave everything else alone."""
    cfg = kw.get("feed_cfg")
    if cfg is not None and _patched.extra:
        cfg.update(_patched.extra)
    return _real_forecast(*a, **kw)


_patched.extra = None
RF.forecast = _patched


def run(label, extra):
    _patched.extra = extra
    CA.S.pop("live", None)                       # no cached payload between arms
    r = CA.calibrated_forecast("SJC", "TPE", airline="CI", carrier_type="FSC",
                               aircraft="A359", seats=306, freq=FREQ)
    d = r["demand"]
    fb = (extra or {}).get("_qsi_fallbacks")
    print(f"{label}")
    print(f"  qsi_share            {d['qsi_share']:.4f}")
    print(f"  beyond base  each way {d['feed_beyond_base']:>12,.0f}   two-way {2*d['feed_beyond_base']:>12,.0f}")
    print(f"  beyond feed  each way {d['feed_beyond']:>12,.0f}   two-way {2*d['feed_beyond']:>12,.0f}")
    print(f"  behind base  each way {d['feed_behind_base']:>12,.0f}   two-way {2*d['feed_behind_base']:>12,.0f}")
    print(f"  behind feed  each way {d['feed_behind']:>12,.0f}   two-way {2*d['feed_behind']:>12,.0f}")
    print(f"  p2p carried  each way {d['p2p_carried']:>12,.0f}   total two-way {2*d['total']:>12,.0f}")
    if extra:
        print(f"  QSI fallbacks to the flat path: {extra.get('_qsi_fallbacks', 0)}")
    return d


def main():
    print(f"AVIA_FREQ_SENSITIVE = {os.environ.get('AVIA_FREQ_SENSITIVE')!r}\n")
    run("BASELINE, flat rate (qsi_feed off, the standard path today)", None)
    print()
    for k in (1.0, 0.06):
        run(f"QSI FEED, k = {k}",
            {"qsi_feed": True, "dep_time_mins": DEP_TIME_MINS, "flying_mins": FLYING_MINS,
             "route_freq": FREQ, "qsi_k": k, "qsi_k_behind": k})
        print()


if __name__ == "__main__":
    main()
