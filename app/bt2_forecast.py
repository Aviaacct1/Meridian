#!/usr/bin/env python3
r"""BT2 as Meridian's forecast, behind a switch, with a revert that is one setting.

    import bt2_forecast as BF
    out = BF.forecast(route)          # None when it cannot answer, and it says why

WHY THIS EXISTS. Until 9 August 2026 nothing in app/ loaded a BT2 model: every pickle reference in
the live tree was in app/attic. The published accuracy came from BT2 and the number a client saw
came from the QSI engine, which scores 17% within +-20% blind on its own back-test against BT2's
60.4%. John's ruling of 9 August: BT2 becomes the forecast, the QSI engine keeps the breakdown, and
there is a way back if it goes wrong.

THE CIRCULARITY, and it decides the whole design. BT2 is anchored on capacity. In a back-test the
airline chose that capacity and BT2 was scored on how well it read the market given that choice. In
a forecast, capacity is sometimes an input and sometimes something Meridian picks. Those are not the
same question and must not return the same confidence:

    SCHEDULED   the caller supplied aircraft and frequency, so seats are an INPUT. This is what the
                back-test measured and the accuracy figures describe it. Answer and stand behind it.
    INDICATIVE  the optimiser chose the schedule, so seats are an OUTPUT of Meridian. Anchoring on
                them and reporting the result as a forecast is circular: EDI-AUS on 8 August 2026
                returned carried = capacity x load factor exactly. Answered, labelled, and the
                caller is told the number describes the schedule rather than the market.

FAIL CLOSED. Every path that cannot produce an honest number returns None with a reason rather than
a default. A silent fallback to a neutral value is the failure mode this codebase has found four
times: a missing table substituting 1.0 inside a bare except, and nothing reporting anything.

REVERTING is one setting and takes effect on the next request:

    AVIA_FORECAST_ENGINE=qsi     the QSI engine, as before. THE DEFAULT
    AVIA_FORECAST_ENGINE=bt2     BT2 for the number, QSI for the breakdown

Avia Solutions Limited. All rights reserved.
"""
import math
import os
import pickle

ENGINE = os.environ.get("AVIA_FORECAST_ENGINE", "qsi").strip().lower()
MODEL_ENV = "AVIA_BT2_MODEL"

_MODEL = None
_MODEL_ERR = None


def _model_path():
    p = os.environ.get(MODEL_ENV)
    if p and os.path.isfile(p):
        return p
    root = os.environ.get("AVIA_LOCAL_CACHE")
    cands = []
    for r in [root, os.path.join("E:" + os.sep, "Avia"), os.path.join("C:" + os.sep, "Avia")]:
        if not r:
            continue
        # the relaxed sample is the current production population; the canon folder is the fallback
        for sub in ("bt2_relaxed", "bt2"):
            cands.append(os.path.join(r, sub, "bt2_model_v1_3.pkl"))
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


def load():
    """The model, or None with the reason recorded. Loaded once and kept."""
    global _MODEL, _MODEL_ERR
    if _MODEL is not None or _MODEL_ERR is not None:
        return _MODEL
    p = _model_path()
    if not p:
        _MODEL_ERR = ("no bt2_model_v1_3.pkl found. Set %s, or AVIA_LOCAL_CACHE to the data root."
                      % MODEL_ENV)
        return None
    try:
        with open(p, "rb") as fh:
            _MODEL = pickle.load(fh)
        _MODEL["_path"] = p
    except Exception as e:                                  # noqa: BLE001
        # SAY WHAT THE READER IS RUNNING, because the commonest cause is a version mismatch and the
        # bare exception does not name either side. A pickled scikit-learn estimator is VERSION
        # LOCKED: bt2_model_v1_3.pkl was written under an older release and 1.9.0 fails on it with
        # "No module named '_loss'" because sklearn's internal module paths moved. On 13 August 2026
        # that message alone cost an hour of narrowing down, and the fix is one rebuild.
        _hint = ""
        if "_loss" in str(e) or "module" in str(e).lower():
            try:
                import sklearn
                _sv = sklearn.__version__
            except Exception:                               # noqa: BLE001
                _sv = "unknown"
            _hint = (". This reads like a scikit-learn version mismatch: a pickled estimator can "
                     "only be loaded by a compatible release. This process has scikit-learn %s. "
                     "Rebuild the artefact under it with bt2/bt2_build_v13.py, and re-measure the "
                     "claim set, because a rebuilt model is a different model." % _sv)
        _MODEL_ERR = "could not load %s: %s%s" % (p, e, _hint)
        return None
    return _MODEL


def status():
    """What the switch is doing right now, for the dashboard and for a run log."""
    m = load()
    return {"engine": ENGINE, "model_loaded": bool(m), "error": _MODEL_ERR,
            "model_path": (m or {}).get("_path"),
            "population": (m or {}).get("population"),
            "trained_on": (m or {}).get("n_train"),
            "provenance": (m or {}).get("provenance")}


# The feature vector, in the order bt2_model._vec builds it, then the five v1.2 additions. Written
# out rather than imported so a change in either file cannot silently reorder the other.
REQUIRED = ("seats_ly", "base_mkt", "capa", "freq", "legs_n", "months", "gcd",
            "typ", "dom", "gauge", "ncar", "launch_mon", "qcx")
OPTIONAL = ("mkt_growth", "carrier", "base_seats_a", "base_seats_b",
            "airport_seats_a", "airport_seats_b", "sister_flag")


def _vec(r, carid):
    f = [math.log(r["seats_ly"]), math.log(r["base_mkt"]), r["capa"],
         math.log(max(r["freq"], .5)), math.log(1 + r["legs_n"]),
         math.log(r["months"]), math.log(max(r["gcd"], 100)),
         1.0 if r["typ"] == "LCC" else 0.0, 1.0 if r["dom"] else 0.0,
         r["gauge"], r["ncar"], math.log(r["seats_ly"] / r["base_mkt"]),
         int(r["launch_mon"]), math.log(1 + r["qcx"]),
         math.log(max(min(float(r.get("mkt_growth", 1.0)), 5.0), 0.2)),
         carid.get(r.get("carrier", ""), 0)]
    sa, sb = float(r.get("base_seats_a") or 0), float(r.get("base_seats_b") or 0)
    ta, tb = float(r.get("airport_seats_a") or 0), float(r.get("airport_seats_b") or 0)
    f += [math.log1p(min(sa, sb)), math.log1p(max(sa, sb)),
          (sa / ta if ta else 0.0), (sb / tb if tb else 0.0),
          1.0 if r.get("sister_flag") else 0.0]
    return f


# THE DOMAIN GUARD. Measured on the 6,524 training launches, 9 August 2026: the pair's existing
# market runs from a floor of 250 passengers a year (the discovery rule's own minimum) with a median
# of 3,779, and seats offered over that market reaches a maximum of 1,107 times with a 99th
# percentile of 163.
#
# WHY IT MATTERS, found by wiring SJC-TPE through the whole chain rather than by reasoning about it.
# Sabre records 212 passengers a year between San Jose and Taipei against 283,412 for SFO-TPE.
# Silicon Valley's Taipei demand books out of San Francisco: the pair's own bookings are empty
# because the market has LEAKED to the primary airport.
#
# THE FIRST VERSION OF THIS GUARD WAS WRONG, and the wiring test caught it by refusing training
# routes. It keyed on the seats-over-market ratio alone and called 289 times "beyond anything BT2
# has been trained on", which is false: the training set reaches 1,107. The ratio is a SYMPTOM. The
# signal is the market itself being below the floor BT2 has ever seen, because a pair carrying 212
# passengers a year between two airports of this size is not a thin market, it is a market measured
# in the wrong place.
#
# The scope limit underneath is real and worth stating. BT2 was trained on pairs that already carried
# traffic, because the discovery rule requires at least 250. A secondary airport whose demand books
# from the primary is precisely the case that rule excludes, and precisely the case Meridian's
# catchment machinery was built for. There, the QSI engine is the right tool and BT2 is not.
TRAIN_MIN_BASE = 250.0        # the discovery floor: no training route had a thinner market
TRAIN_MAX_RATIO = 1107.0      # the largest seats-over-market ever seen in training
TRAIN_P99_RATIO = 163.0


def domain(route):
    """IN, MARGINAL or OUT, with the ratio and a note. Never guesses."""
    try:
        bm = float(route.get("base_mkt") or 0)
        s = float(route.get("seats_ly") or 0)
    except (TypeError, ValueError):
        return "UNKNOWN", None, "seats_ly or base_mkt is not a number"
    if bm <= 0 or s <= 0:
        return "UNKNOWN", None, "seats_ly and base_mkt must both be positive"
    r = s / bm
    if bm < TRAIN_MIN_BASE:
        return "OUT", r, (
            "The pair records only %.0f passengers a year, below the %.0f floor of every route BT2 "
            "has been trained on. On a pair between airports of any size that usually means the "
            "market has leaked to a larger airport nearby and is being measured in the wrong place: "
            "San Jose to Taipei records 212 a year while San Francisco to Taipei records 283,412. "
            "The catchment engine measures a leaked market and BT2 cannot. Use the QSI engine."
            % (bm, TRAIN_MIN_BASE))
    if r > TRAIN_MAX_RATIO:
        return "OUT", r, (
            "This route offers %.0f times the seats of its existing market, beyond the %.0f maximum "
            "of anything in training, so the model would be extrapolating rather than forecasting."
            % (r, TRAIN_MAX_RATIO))
    if r > TRAIN_P99_RATIO:
        return "MARGINAL", r, (
            "This route offers %.0f times the seats of its existing market, above the 99th "
            "percentile of the launches BT2 was trained on, so few comparable cases exist. Treat "
            "the number as indicative and read the range rather than the point." % r)
    return "IN", r, ""


def check(route):
    """What is missing, named. Returns [] when the route can be forecast."""
    bad = []
    for k in REQUIRED:
        v = route.get(k)
        if v is None or (isinstance(v, str) and not v.strip()):
            bad.append(k)
    for k in ("seats_ly", "base_mkt"):
        try:
            if float(route.get(k) or 0) <= 0:
                bad.append("%s must be positive" % k)
        except (TypeError, ValueError):
            bad.append("%s is not a number" % k)
    return bad


def forecast(route, mode="scheduled"):
    """The BT2 forecast for one route, or None with a reason.

    mode is 'scheduled' when the caller supplied the aircraft and frequency, which is what the
    back-test measured, and 'indicative' when Meridian chose them, which is the circular case.
    """
    if ENGINE != "bt2":
        return None
    m = load()
    if not m:
        return {"ok": False, "reason": _MODEL_ERR}
    missing = check(route)
    if missing:
        return {"ok": False, "reason": "cannot forecast, missing or invalid: " + ", ".join(missing)}
    verdict, ratio, note = domain(route)
    if verdict == "OUT":
        # Refused rather than caveated. A number this far outside the training set is not a forecast
        # with a wide range, it is an extrapolation dressed as one, and the caller has a better tool.
        return {"ok": False, "domain": verdict, "seats_over_market": round(ratio, 1),
                "reason": note, "use_instead": "qsi"}
    import numpy as np
    x = np.array([_vec(route, m["carid"])])
    p50 = float(m["q50"].predict(x)[0])
    p25 = float(m["q25"].predict(x)[0])
    p75 = float(m["q75"].predict(x)[0])
    seats = float(route["seats_ly"])
    iqr = p75 - p25
    out = {
        "ok": True,
        "pax": seats * math.exp(p50),
        "lo": seats * math.exp(p25),
        "hi": seats * math.exp(p75),
        "iqr_log": iqr,
        "tier": "A" if (iqr <= 0.090 and not route.get("sister_flag")) else "B",
        "mode": mode,
        "engine": "bt2",
        "model": m.get("version"),
        "population": m.get("population"),
        "domain": verdict,
        "seats_over_market": round(ratio, 1),
    }
    if note:
        out["domain_note"] = note
    if mode != "scheduled":
        # Said in the payload, not in a comment, because a caller that does not read this will
        # present a circular number as a market forecast.
        out["caveat"] = ("INDICATIVE. Meridian chose the aircraft and frequency, so the capacity "
                         "this forecast is anchored on is an output of Meridian rather than an "
                         "airline decision. The number describes the schedule as much as the "
                         "market. The published accuracy was measured on routes where the airline "
                         "had chosen the capacity and does not describe this case.")
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(status(), indent=2, default=str))
