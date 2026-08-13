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
    # THE FIGURES A CLIENT ACTUALLY READS, added 12 August 2026. The fields above catch a change in
    # the economics; these catch a change in the FORECAST that produced them. Without them a
    # consolidation could move the P2P and connecting split, leave the total untouched and pass this
    # check, which is exactly what split_share does: it is total-preserving and moves the split by
    # tens of thousands of passengers.
    d = r.get("demand") or {}
    cap = r.get("capacity") or {}
    for key, field in (("p2p_carried", "_p2p_carried"), ("connecting_carried", "_connecting_carried"),
                       ("p2p_share", "_p2p_share"), ("feed_total", "_feed_total"),
                       ("feed_beyond", "_feed_beyond"), ("feed_behind", "_feed_behind"),
                       ("qsi_share", "_capture_share"), ("natural", "_natural_market"),
                       ("total_demand", "_total_demand_each_way")):
        if key not in d:
            # LOUD, not silent. A renamed payload key would otherwise record None and the baseline
            # would freeze nothing while appearing to pass. That is the failure shape this codebase
            # has now found six times.
            return {"error": "demand payload has no key %r; econ_baseline needs updating" % key}
        out[field] = d[key]
    out["_spill"] = cap.get("spill")
    return out


def _now_utc():
    """Timestamp. datetime.utcnow() is deprecated in python 3.12 and printed a warning over the
    output of the first capture, so the timezone-aware form is used."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _provenance():
    """WHAT PRODUCED THE NUMBERS, recorded beside them.

    The recurring failure this closes: a run is compared against an earlier one and only afterwards
    does anyone establish that the code, the stores or the library versions were not the same. The
    switches in ENV_KEYS were already recorded; this adds the code and the data.

    The commit is READ FROM THE .git FILES, never by running git. A git process on a mounted working
    tree takes .git/index.lock and the mount denies the unlink, which strands the lock and blocks
    every later commit. Reading HEAD and the ref it points at is a plain file read and is safe.
    """
    p = {}
    try:
        root = os.path.dirname(HERE)
        head = open(os.path.join(root, ".git", "HEAD"), encoding="utf-8").read().strip()
        if head.startswith("ref:"):
            ref = head.split(" ", 1)[1].strip()
            p["commit"] = open(os.path.join(root, ".git", ref), encoding="utf-8").read().strip()
            p["branch"] = ref.rsplit("/", 1)[-1]
        else:
            p["commit"], p["branch"] = head, "(detached)"
    except Exception as exc:
        p["commit"] = "unknown (%s)" % exc
    for mod in ("duckdb", "airportsdata"):
        try:
            p[mod] = str(__import__(mod).__version__)
        except Exception:
            p[mod] = "not installed"
    p["python"] = sys.version.split()[0]
    try:
        import cortex_app as CA
        b = json.loads(CA.api_basis().body.decode())
        p["oag_week"] = b.get("oag_week")
        p["sabre_year"] = b.get("sabre_year")
        p["default_forecast_year"] = b.get("default_forecast_year")
    except Exception as exc:
        p["store_vintage"] = "unreadable (%s)" % exc
    return p


# The switches that change the answer. Recorded with the baseline and checked on the way back,
# because on 10 August 2026 a check run without AVIA_FREQ_SENSITIVE reported two moved fields against
# a baseline captured with it on, and for a minute that looked like a regression in the engine.
ENV_KEYS = ["AVIA_FREQ_SENSITIVE", "AVIA_FREQ_REF", "AVIA_FORECAST_ENGINE", "AVIA_WATER_CHECK",
            "AVIA_OD_SOURCE"]


def _env():
    return {k: os.environ.get(k, "") for k in ENV_KEYS}


def capture(path=DEFAULT_PATH):
    data = {"note": "Frozen record of the three SJC-TPE carrier cases. Every figure here must be "
                    "reproduced exactly by any change that is not intended to move the forecast, "
                    "and any change that IS intended to move it must be able to say which fields "
                    "and by how much. Provenance records what produced the numbers.",
            "captured_utc": _now_utc(),
            "provenance": _provenance(), "env": _env(), "cases": {}}
    for c in CASES:
        data["cases"][c["name"]] = _run(c)
    # REFUSE TO WRITE A BASELINE THAT DID NOT RUN. On 12 August 2026 a capture in a fresh shell,
    # with AVIA_OAG and AVIA_SABRE unset, wrote a file in which all three cases were the string
    # "OAG/Sabre databases not found". A later check would have compared errors against errors and
    # reported that nothing had moved. A baseline of failures is worse than no baseline, because it
    # reads as a pass.
    bad = {n: v["error"] for n, v in data["cases"].items() if "error" in v}
    if bad:
        raise SystemExit("NOT WRITTEN. %d of %d cases failed, so there is nothing to freeze:\n  %s"
                         % (len(bad), len(CASES), "\n  ".join(f"{n}: {e}" for n, e in bad.items())))
    # AND REFUSE TO FREEZE THE WRONG BASIS. AVIA_FREQ_SENSITIVE was decided ON on 10 August; with it
    # off the capture share reads 0.32 rather than 0.2513 and the route returns the same demand at
    # every frequency. A baseline captured that way describes a configuration Avia does not use.
    if os.environ.get("AVIA_FREQ_SENSITIVE", "").strip() not in ("1", "true", "on"):
        raise SystemExit("NOT WRITTEN. AVIA_FREQ_SENSITIVE is not set. Set it to \"1\" and re-run: "
                         "with it off the capture share reads 0.32 instead of 0.2513 and the "
                         "forecast does not respond to frequency at all.")
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

    # UNSET AND SET-TO-THE-DEFAULT ARE THE SAME ENVIRONMENT, and treating them as different stopped
    # this check dead on 13 August 2026: the baseline was captured with AVIA_FORECAST_ENGINE unset
    # and the run had it set explicitly to "qsi", which is what unset MEANS. It reported an
    # environment difference and refused to compare a single field, so a switch being wired in could
    # not be proved harmless by the one tool built to prove it.
    #
    # Only variables with a real default belong here, and the default has to match the code that
    # reads it: bt2_forecast line 40 is os.environ.get("AVIA_FORECAST_ENGINE", "qsi").
    _DEFAULTS = {"AVIA_FORECAST_ENGINE": "qsi"}

    def _norm(k, v):
        v = (v or "").strip()
        return _DEFAULTS.get(k, "") if v == "" else v.lower() if k in _DEFAULTS else v

    for k in ENV_KEYS:
        a, b = _norm(k, was_env.get(k, "")), _norm(k, now_env.get(k, ""))
        if a != b:
            diffs.append("ENVIRONMENT %s: captured %r, now %r. Fix this before reading anything "
                         "below as a regression." % (k, was_env.get(k, ""), now_env.get(k, "")))
    if diffs:
        return False, diffs
    # PROVENANCE IS REPORTED, NOT ENFORCED. A different commit is the normal case: the whole point of
    # a baseline is to hold numbers across a code change. But it must be VISIBLE, because the failure
    # this exists to stop is comparing two runs and only later establishing that the code, the stores
    # or the library versions were not the same. A store refresh or an airportsdata release moving a
    # figure is a legitimate reason for a difference and a different thing from a regression.
    notes = []
    was_p = blob.get("provenance") or {}
    now_p = _provenance()
    for k in sorted(set(list(was_p) + list(now_p))):
        if was_p.get(k) != now_p.get(k):
            notes.append("PROVENANCE %s: captured %r, now %r" % (k, was_p.get(k), now_p.get(k)))
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
    # notes first, so the code and store vintage are read BEFORE any moved field is interpreted.
    # ok is decided by diffs alone: a different commit is expected and is not a regression.
    return (not diffs), notes + diffs


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "capture"
    path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PATH
    if mode == "capture":
        p, data = capture(path)
        print("written:", p)
        print("provenance:")
        for k, v in sorted(data["provenance"].items()):
            print(f"    {k:24} {v}")
        print("switches:")
        for k, v in sorted(data["env"].items()):
            print(f"    {k:24} {v!r}")
        print("cases:")
        for name, v in data["cases"].items():
            if "error" in v:
                print(f"  {name}: FAILED {v['error']}")
            else:
                print(f"  {name}: carried ew {v['_carried_each_way']:,.0f} "
                      f"(P2P {v['_p2p_carried'] or 0:,.0f} / cnx {v['_connecting_carried'] or 0:,.0f}) "
                      f"LF {v['_load_factor']:.3f} capture {v['_capture_share'] or 0:.4f} "
                      f"profit {v['profit']:,.0f}")
    else:
        ok, lines = check(path)
        notes = [x for x in lines if x.startswith("PROVENANCE")]
        diffs = [x for x in lines if not x.startswith("PROVENANCE")]
        if notes:
            print("what changed about the RUN (context, read this first):")
            for n in notes:
                print("  ", n)
        print("IDENTICAL, no field moved" if ok else "%d field(s) MOVED:" % len(diffs))
        for d in diffs:
            print("  ", d)
        sys.exit(0 if ok else 1)
