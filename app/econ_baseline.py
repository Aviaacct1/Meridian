#!/usr/bin/env python3
r"""Avia Solutions - a frozen record of what the route economics returns, so a change can be undone.

    py -3.12 econ_baseline.py capture  [path]     write the golden file
    py -3.12 econ_baseline.py check    [path]     re-run and diff against it

WHY. On 10 August 2026 the decision was taken to stop presenting a route profit that rests on an
ownership cost Avia cannot source. Four independent searches, three of them external, failed to find
a single current type-and-age lease rate in free public form, and appraiser licences permit internal
use but not publication. Rather than hide the assumption, the output moves to contribution before
ownership plus the ownership cost at which the route breaks even, so the number Avia cannot defend
becomes the question put to the airline rather than an answer asserted to it.

Before that change, this captures what the economics returns today, figure by figure, on a fixed set
of routes. The rule for the change is that it must be ADDITIVE: every field recorded here must come
back identical afterwards. A field that moves is a regression, not a feature, and `check` will say so.

Nothing here depends on the ownership figures being right. It only depends on them not changing.

Avia Solutions Limited. All rights reserved.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

DEFAULT_PATH = os.path.join(HERE, "econ_baseline.json")

# Reference routes. Two are the SJC-TPE cases behind the August 2026 carrier scenarios, so the
# baseline is anchored on work that has been checked against a number John already knew. The third
# exercises a narrowbody on a short sector, where the cost mix is quite different.
CASES = [
    dict(name="SJC-TPE CI A359 5x, carrier seats",
         origin="SJC", dest="TPE", airline="CI", carrier_type="FSC",
         aircraft="A359", freq=5, seats=306),
    dict(name="SJC-TPE BR B77W 4x, carrier seats",
         origin="SJC", dest="TPE", airline="BR", carrier_type="FSC",
         aircraft="B77W", freq=4, seats=333),
    dict(name="SJC-TPE CI B789 7x, generic seats (the verified case)",
         origin="SJC", dest="TPE", airline="CI", carrier_type="FSC",
         aircraft="B789", freq=7, seats=None),
]

# The figures that must not move. Everything the economics block returns that a client could read.
FIELDS = ["econ_fare", "market_fare", "effective_fare", "connecting_share", "prorate",
          "econ_lf", "bus_lf", "spilled", "seats", "revenue", "fuel", "maintenance", "crew",
          "ownership", "airport_nav_other", "total_cost", "profit", "margin", "breakeven_lf",
          "annual_profit", "aircraft_required"]


def _run(case):
    import cortex_app as CA
    r = CA.calibrated_forecast(case["origin"], case["dest"], airline=case["airline"],
                               carrier_type=case["carrier_type"], aircraft=case["aircraft"],
                               freq=case["freq"], seats=case.get("seats"), with_econ=True)
    if not r.get("ok"):
        return {"error": r.get("error")}
    if not r.get("economics_ok"):
        return {"error": r.get("economics_error", "economics not returned")}
    e = r["economics"]
    out = {f: e.get(f) for f in FIELDS}
    # carried and load factor too, so a change to the forecast is caught as well as one to the P&L
    out["_carried_each_way"] = r["demand"]["total"]
    out["_load_factor"] = r["capacity"]["load"]
    return out


# The switches that change the answer. Recorded with the baseline and checked on the way back,
# because on 10 August 2026 a check run without AVIA_FREQ_SENSITIVE reported two moved fields against
# a baseline captured with it on, and for a minute that looked like a regression in the engine.
ENV_KEYS = ["AVIA_FREQ_SENSITIVE", "AVIA_FREQ_REF", "AVIA_FORECAST_ENGINE", "AVIA_WATER_CHECK",
            "AVIA_OD_SOURCE"]


def _env():
    return {k: os.environ.get(k, "") for k in ENV_KEYS}


def capture(path=DEFAULT_PATH):
    data = {"note": "Frozen before the contribution-before-ownership change, 10 August 2026. "
                    "Every figure here must be reproduced exactly by any additive change.",
            "env": _env(), "cases": {}}
    for c in CASES:
        data["cases"][c["name"]] = _run(c)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
    return path, data


def check(path=DEFAULT_PATH):
    """Re-run and compare. Returns (ok, list of differences). A difference in ANY field is a
    regression: the change was supposed to add fields, not move them."""
    with open(path, encoding="utf-8") as fh:
        blob = json.load(fh)
    old = blob["cases"]
    diffs = []
    was_env = blob.get("env") or {}
    now_env = _env()
    for k in ENV_KEYS:
        if was_env.get(k, "") != now_env.get(k, ""):
            diffs.append("ENVIRONMENT %s: captured %r, now %r. Fix this before reading anything "
                         "below as a regression." % (k, was_env.get(k, ""), now_env.get(k, "")))
    if diffs:
        return False, diffs
    for c in CASES:
        name = c["name"]
        new = _run(c)
        was = old.get(name, {})
        for f in sorted(set(list(was) + list(new))):
            a, b = was.get(f), new.get(f)
            if a is None and b is None:
                continue
            if isinstance(a, float) and isinstance(b, float):
                if abs(a - b) > max(abs(a), abs(b)) * 1e-9:
                    diffs.append(f"{name} | {f}: {a} -> {b}")
            elif a != b:
                diffs.append(f"{name} | {f}: {a} -> {b}")
    return (not diffs), diffs


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "capture"
    path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PATH
    if mode == "capture":
        p, data = capture(path)
        print("written:", p)
        for name, v in data["cases"].items():
            if "error" in v:
                print(f"  {name}: FAILED {v['error']}")
            else:
                print(f"  {name}: profit {v['profit']:,.0f} margin {v['margin']:.3f} "
                      f"ownership {v['ownership']:,.0f} carried ew {v['_carried_each_way']:,.0f}")
    else:
        ok, diffs = check(path)
        print("IDENTICAL, no field moved" if ok else "REGRESSION, %d field(s) moved:" % len(diffs))
        for d in diffs:
            print("  ", d)
        sys.exit(0 if ok else 1)
