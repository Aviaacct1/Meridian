#!/usr/bin/env python3
"""
Avia Cortex - quick eyeball of the MCT schedule-banking effect. Runs a few hub routes with banking
OFF then ON and prints the beyond feed and the total forecast side by side, so you can see how much
schedule connectivity moves the numbers before committing to the full back-test.

    py -3.12 test_mct.py

Banking is opt-in and OFF by default in the live tool; this script only flips it for the comparison.
"""
import cortex_app as C

ROUTES = [
    ("SJC", "TPE", "CI"),      # San Jose - Taipei, China Airlines (onward beyond TPE into Asia)
    ("SJC", "LHR", "BA"),      # San Jose - London, BA (onward beyond LHR into Europe)
    ("Manchester", "Chicago", "AA"),   # onward beyond ORD across the US
    ("Bristol", "New York", "B6"),     # JetBlue beyond JFK
]

hdr = f"{'route':20} {'ai':4} {'feed off':>10} {'feed on':>10} {'delta':>7} | {'total off':>10} {'total on':>10} {'delta':>7}"
print(hdr)
print("-" * len(hdr))
for o, d, al in ROUTES:
    try:
        a = C.calibrated_forecast(o, d, airline=al, mct_banking=False, with_econ=False)
        b = C.calibrated_forecast(o, d, airline=al, mct_banking=True, with_econ=False)
    except Exception as e:
        print(f"{o}-{d:12} {al or '-':4} ERROR {e}")
        continue
    if not a.get("ok") or not b.get("ok"):
        print(f"{o}-{d:12} {al or '-':4} ERR {a.get('error') or b.get('error')}")
        continue
    fa, fb = a["demand"], b["demand"]
    f1, f2 = fa["feed_beyond"], fb["feed_beyond"]
    t1, t2 = fa["total"], fb["total"]
    fd = f"{(f2 - f1) / f1 * 100:+.0f}%" if f1 else "-"
    td = f"{(t2 - t1) / t1 * 100:+.0f}%" if t1 else "-"
    print(f"{o + '-' + d:20} {al or '-':4} {f1:>10,} {f2:>10,} {fd:>7} | {t1:>10,} {t2:>10,} {td:>7}")

print("\nBanking weights each onward market by the share of its frequency connectable within MCT of the "
      "optimised hub arrival. A large drop means the hub's onward bank is poorly timed for that arrival; "
      "little change means it was already well connected. Next step: the full back-test against outturn.")
