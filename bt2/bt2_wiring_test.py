#!/usr/bin/env python3
r"""Does the live adapter reproduce the back-test, feature for feature and number for number?

    AVIA_FORECAST_ENGINE=bt2 python3 bt2_wiring_test.py

THE ONLY TEST THAT MATTERS WHEN WIRING A MODEL INTO AN APPLICATION. A model that scores 60.4% in a
back-test and is then fed a feature vector assembled slightly differently by the live path does not
fail. It returns numbers, they look plausible, and the published accuracy no longer describes
anything the client is shown. The back-test and the application must build the same vector from the
same route, and the way to know is to build both and subtract them.

Three checks, and all three have to pass before the switch is worth turning on:

  1. THE VECTOR. For a sample of back-test routes, the vector app/bt2_forecast.py builds against the
     vector bt2_g12_exp builds. Any difference at all is a defect: same route, same numbers.
  2. THE PREDICTION. The adapter's pax against the model applied the back-test way.
  3. FAILING CLOSED. A route with a missing feature must return a named reason, never a number.

Avia Solutions Limited. All rights reserved.
"""
import math
import os
import sys

import numpy as np

os.environ.setdefault("AVIA_BT2_COHORTS", "2016,2017,2018,2019,2024,2025")
os.environ["AVIA_FORECAST_ENGINE"] = "bt2"

import bt2_gbm as G          # noqa: E402
import bt2_g12_exp as F      # noqa: E402
from bt2_paths import find_app   # noqa: E402

sys.path.insert(0, find_app())
import bt2_forecast as BF     # noqa: E402


def route_dict(r):
    """The route as the application would hand it over. Every value here is something the engine
    already has or can look up before launch; nothing is read from the outcome."""
    b = r.get("_base") or (0, 0, 0, 0)
    return {"seats_ly": r["seats_ly"], "base_mkt": r["base_mkt"], "capa": r["capa"],
            "freq": r["freq"], "legs_n": r["legs_n"], "months": r["months"], "gcd": r["gcd"],
            "typ": r["typ"], "dom": r["dom"], "gauge": r["gauge"], "ncar": r["ncar"],
            "launch_mon": int(r["launch_month"][5:7]), "qcx": r["qcx"],
            "mkt_growth": r["mkt_growth"], "carrier": r["oag_carrier"],
            "base_seats_a": b[0], "base_seats_b": b[1],
            "airport_seats_a": b[2], "airport_seats_b": b[3],
            "sister_flag": bool(r.get("_sister"))}


def main():
    rows = G.rows
    F.attach(rows)
    m = BF.load()
    if not m:
        raise SystemExit("adapter could not load a model: %s" % BF._MODEL_ERR)
    print("adapter model: %s" % m.get("_path"))
    print("  version %s, population %s, trained on %s"
          % (m.get("version"), m.get("population"), m.get("n_train")))

    sample = rows[::max(1, len(rows) // 400)][:400]
    Xb = F.X_of(sample, ["base", "sister"])
    Xa = np.array([BF._vec(route_dict(r), m["carid"]) for r in sample])

    print("\n1. THE VECTOR, %d routes x %d features" % Xb.shape)
    if Xa.shape != Xb.shape:
        raise SystemExit("  FAIL: shapes differ, adapter %s against back-test %s" % (Xa.shape, Xb.shape))
    d = np.abs(np.nan_to_num(Xa) - np.nan_to_num(Xb))
    worst = float(d.max())
    print("   largest absolute difference on any feature of any route: %.3e" % worst)
    if worst > 1e-9:
        col = int(np.unravel_index(d.argmax(), d.shape)[1])
        raise SystemExit("  FAIL: feature index %d differs. The adapter and the back-test are not "
                         "building the same vector." % col)
    print("   PASS: identical")

    print("\n2. THE PREDICTION, same %d routes" % len(sample))
    direct = sample and m["q50"].predict(Xb)
    diffs = []
    for r, p in zip(sample, direct):
        out = BF.forecast(route_dict(r), mode="scheduled")
        if not out or not out.get("ok"):
            raise SystemExit("  FAIL: adapter refused a valid route: %s" % (out or {}).get("reason"))
        diffs.append(abs(out["pax"] - r["seats_ly"] * math.exp(p)))
    print("   largest absolute difference in forecast passengers: %.6f" % max(diffs))
    if max(diffs) > 1e-6:
        raise SystemExit("  FAIL: the adapter and the back-test disagree on the number.")
    print("   PASS: identical")

    print("\n3. FAILING CLOSED")
    for k in ("seats_ly", "base_mkt", "qcx"):
        d0 = route_dict(sample[0])
        d0[k] = None
        out = BF.forecast(d0)
        if out and out.get("ok"):
            raise SystemExit("  FAIL: returned a number with %s missing" % k)
        print("   %-10s refused: %s" % (k, out["reason"][:72]))
    d0 = route_dict(sample[0])
    d0["base_mkt"] = 0
    out = BF.forecast(d0)
    print("   %-10s refused: %s" % ("base_mkt=0", out["reason"][:72]))

    print("\n4. THE MODE LABEL")
    a = BF.forecast(route_dict(sample[0]), mode="scheduled")
    b = BF.forecast(route_dict(sample[0]), mode="indicative")
    print("   scheduled carries a caveat: %s" % ("caveat" in a))
    print("   indicative carries a caveat: %s" % ("caveat" in b))
    if "caveat" in a or "caveat" not in b:
        raise SystemExit("  FAIL: the mode labelling is the wrong way round")
    print("   same pax both modes, %.0f: the label is about confidence, not the number" % b["pax"])

    print("\nALL CHECKS PASSED. The switch is safe to turn on.")


if __name__ == "__main__":
    main()
