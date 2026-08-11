#!/usr/bin/env python3
"""Avia Solutions - the SJC-TPE connecting baseline, 11 August 2026.

Runs calibrated_forecast on the handover's anchor case and prints the connecting figures a change to
the feed has to be measured against: the beyond and behind bases, the capture rate returned on every
market, and the two totals. It prints the DISTINCT capture rates rather than a summary, because the
point of the baseline is that today every market gets the same rate.

Anchor: SJC-TPE, China Airlines, A350-900 at 306 seats, 4x weekly, AVIA_FREQ_SENSITIVE=1.
Expected from the 11 August measurement: qsi_share 0.2510, beyond base 1,216,168, beyond forecast
46,772, behind base 313,530, behind forecast 14,542.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), "app")
if APP not in sys.path:
    sys.path.insert(0, APP)

import cortex_app as CA                          # noqa: E402


def main():
    r = CA.calibrated_forecast("SJC", "TPE", airline="CI", carrier_type="FSC",
                               aircraft="A359", seats=306, freq=4)
    if not r.get("ok", True) and r.get("error"):
        print("FAILED:", r["error"])
        return

    print(f"AVIA_FREQ_SENSITIVE = {os.environ.get('AVIA_FREQ_SENSITIVE')!r}")
    for k in ("qsi_share", "natural_market", "total_demand", "carried_forecast",
              "beyond_base", "beyond_feed", "behind_base", "behind_feed", "capture_share"):
        if k in r:
            v = r[k]
            print(f"  {k:20} {v:,.4f}" if isinstance(v, float) else f"  {k:20} {v}")

    for side in ("beyond", "behind"):
        rows = r.get(f"{side}_feed_list") or r.get(f"{side}_list") or []
        if not rows:
            continue
        base = sum(x.get("base") or 0 for x in rows)
        fc = sum(x.get("forecast") or 0 for x in rows)
        shares = sorted({round(x.get("share") or 0, 6) for x in rows})
        print(f"  {side}: {len(rows)} markets, base {base:,.0f}, forecast {fc:,.0f}")
        print(f"    distinct capture rates: {shares}")


if __name__ == "__main__":
    main()
