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
        _MODEL_ERR = "could not load %s: %s" % (p, e)
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
    }
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
