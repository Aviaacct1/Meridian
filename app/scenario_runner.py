#!/usr/bin/env python3
r"""Avia Solutions - a file of route scenarios in, a table out, no Python written by the tester.

    py -3.12 scenario_runner.py cases.json
    py -3.12 scenario_runner.py cases.csv --out taipei_ladder.csv
    py -3.12 scenario_runner.py --template cases_sjc_tpe.json     write a worked example to edit

WHY THIS EXISTS. Every number produced on 12 August 2026 came from a hand-built one-line call to
cortex_app.calibrated_forecast. That does not scale to a tester, and it is how settings drift
between runs: two calls a day apart differ in split_floor or in the growth path and nothing records
which produced which figure. This generalises app/econ_baseline.py, which already freezes three
SJC-TPE cases with full provenance, into something a buyer of the tool could drive.

WHAT IT IS NOT. It does not forecast. Every figure comes from cortex_app.calibrated_forecast, which
is the single place a client number is produced, so a scenario run and the portal answer the same
question with the same code. If the two ever disagree, that is a defect in this file.

THE TWO RULES THE 12 AUGUST WORK ASKED FOR, both of them from something that went wrong.

  FAIL LOUDLY ON A MISSING PAYLOAD KEY. A renamed key would otherwise record a blank and the table
  would read as a clean run. That is the failure shape this codebase has now found six times: a
  missing thing substituting a neutral value in silence.

  REFUSE TO WRITE A RESULTS FILE IN WHICH ANY CASE ERRORED. A capture in a fresh shell on 12 August
  wrote a file in which all three cases were the string "OAG/Sabre databases not found", and a
  later check would have compared errors against errors and reported that nothing had moved.

EVERYTHING IS REPORTED TWO-WAY. The engine works each way and BT2's seats_ly counts both
directions, and mixing the two conventions cost a whole afternoon on 9 August: an each-way forecast
divided by two-way seats halved every load factor and a verdict was drawn from it. Client work is
two-way, so the table is two-way and every column that has been doubled says so in its name.

AND THE TWO LOAD FACTORS ARE SEPARATE COLUMNS. demand_lf is total demand over seats, which answers
whether the demand is there to fill the aeroplane. plan_lf_achieved is what is actually carried over
seats, which is capped at plan_lf_cap and can only ever be the lower of the two. Reading one for the
other is the capped-against-uncapped error that invalidated a comparison quoted for a week.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# Provenance and the switch list come from econ_baseline rather than being restated here, so the
# baseline and a scenario run record the same things about the same run. One implementation.
import econ_baseline as EB                                  # noqa: E402


# ---------------------------------------------------------------------------------------------
# The case

# What a case may set. Anything not named here is rejected by name rather than ignored, because a
# misspelled key that is silently dropped is a run with a setting the tester believes is on.
CASE_KEYS = {
    "name", "origin", "dest", "airline", "carrier_type", "aircraft", "seats", "freq",
    "forecast_year", "growth", "dep_time", "partners", "split_floor", "plan_lf", "season",
    "curfew_origin", "curfew_dest", "traffic_rights", "qsi_k", "qsi_k_behind",
}
REQUIRED_KEYS = ("origin", "dest")

# The payload keys every case must come back with. Named here so a rename in cortex_app stops the
# run instead of blanking a column.
DEMAND_KEYS = ("total_demand", "captured", "feed_total", "p2p_carried", "connecting_carried",
               "qsi_share", "natural", "total")
CAPACITY_KEYS = ("carried", "spill", "load", "annual_capacity")

# The economics fields carried through to the table. Same list econ_baseline freezes, so a scenario
# run and the baseline can be read against each other.
#
# "spilled" is RENAMED in the table. The economics block returns its own each-way spill figure while
# every other volume column here is two-way, and an unlabelled each-way column sitting beside
# two-way ones is the units trap that has now cost this programme two afternoons. It is also not the
# same quantity as capacity.spill, which the SPILL-SUSPECT entry of 10 August records as reporting
# 374,174 against a total demand of 134,616 and computing on some basis nobody has yet established.
# Both are carried, both are named, and neither is presented as the other.
ECON_FIELDS = ("revenue", "fuel", "maintenance", "crew", "ownership", "airport_nav_other",
               "total_cost", "profit", "margin", "breakeven_lf", "annual_profit",
               "aircraft_required", "econ_fare", "market_fare", "effective_fare", "prorate",
               "econ_lf", "spilled")
ECON_COLUMN = {"spilled": "econ_spilled_ew"}


def _num(v, default=None, cast=int):
    """A number from a cases file, which may be JSON or a CSV cell. "306" and "306.0" both mean 306,
    and an empty cell means the default rather than zero."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return default
    return cast(float(v))

# The table, in the order a reader wants it: what was asked, then the demand, then the capacity,
# then the economics, then every switch that produced them.
COLUMNS = (
    "case", "origin", "dest", "airline", "carrier_type", "aircraft", "seats_per_dep", "freq_wk",
    "forecast_year",
    "total_demand_2w", "seats_2w", "demand_lf",
    "p2p_demand_2w", "connecting_demand_2w", "connecting_share",
    "carried_2w", "p2p_carried_2w", "connecting_carried_2w", "spill_2w", "plan_lf_achieved",
    "capture_share", "natural_market_2w",
) + tuple(ECON_COLUMN.get(f, f) for f in ECON_FIELDS) + (
    "growth_basis", "dep_time", "dep_basis", "partners", "split_floor", "plan_lf_cap", "season",
    "qsi_k", "qsi_k_behind", "feed_level_basis",
    # WHICH ENGINE PRODUCED THE LOCAL LEG, per case. Added 13 August 2026 after a run with the
    # switch set returned figures identical to the run without it and NOTHING ON SCREEN COULD SAY
    # WHY: the switch may not have been set, the pull may not have carried the change, or the model
    # may have declined on every case. Three very different answers and no way to tell them apart is
    # the exact failure this runner exists to prevent.
    "local_engine", "engine_mode", "engine_tier", "engine_declined",
    "traffic_rights", "engine", "freq_sensitive", "oag_week", "sabre_year",
)


def _mins(v):
    """A departure time as minutes past local midnight. Accepts "12:00", "0030", 720 or nothing.

    Nothing means the optimiser chooses, which is a different case from 00:00 and must not collapse
    into it, so an empty string returns None rather than zero.
    """
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).strip()
    if not s or s.lower() in ("optimise", "optimize", "auto", "best"):
        return None
    if ":" in s:
        h, m = s.split(":", 1)
        return int(h) * 60 + int(m)
    if s.isdigit() and len(s) in (3, 4):
        return int(s[:-2]) * 60 + int(s[-2:])
    return int(float(s))


def _hhmm(mins):
    if mins is None:
        return "optimised"
    return "%02d:%02d" % (int(mins) // 60, int(mins) % 60)


def _bool(v, default=True):
    if v is None or v == "":
        return default
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("1", "true", "yes", "on", "y")


def _partners(v):
    if not v:
        return []
    if isinstance(v, (list, tuple)):
        return [str(x).strip().upper() for x in v if str(x).strip()]
    return [x.strip().upper() for x in str(v).replace(";", ",").split(",") if x.strip()]


def _growth(v):
    """The growth path. A number is a rate a year to the forecast year. "taper" or nothing leaves
    the engine's own measured taper in place, and the caller is warned, because John's ruling of
    12 August is that the taper measures a 20.00% CAGR, which is the clamp ceiling and a recovery
    burst, and is not appropriate for client work on a route that has not launched."""
    if v is None or v == "" or str(v).strip().lower() in ("taper", "default", "engine"):
        return None
    g = float(v)
    return g / 100.0 if g > 1.0 else g              # 7 and 0.07 both mean seven per cent


# ---------------------------------------------------------------------------------------------
# Running one case

def run_case(case):
    """One scenario through calibrated_forecast. Returns a row dict, or one carrying "error"."""
    unknown = sorted(set(case) - CASE_KEYS)
    if unknown:
        return {"error": "unknown setting(s) %s. A misspelled key is not ignored, because a run "
                         "with a setting the tester believes is on is worse than a run that "
                         "stops." % ", ".join(repr(u) for u in unknown)}
    for k in REQUIRED_KEYS:
        if not case.get(k):
            return {"error": "case has no %s" % k}

    import cortex_app as CA

    freq = _num(case.get("freq"), 7)
    seats = _num(case.get("seats"))
    dep = _mins(case.get("dep_time"))
    partners = _partners(case.get("partners"))
    growth = _growth(case.get("growth"))
    plan_lf = _num(case.get("plan_lf"), 0.875, cast=float)
    split_floor = _bool(case.get("split_floor"), True)
    season = (case.get("season") or "annual").strip().lower()

    kw = dict(airline=(case.get("airline") or None),
              carrier_type=(case.get("carrier_type") or "FSC"),
              aircraft=(case.get("aircraft") or "A21X"),
              freq=freq, seats=seats, plan_lf=plan_lf, split_floor=split_floor,
              season=season, with_econ=True,
              partner_carriers=(partners or None),
              dep_time_mins=dep,
              restricted_hours=(case.get("curfew_origin") or None),
              restricted_hours_dest=(case.get("curfew_dest") or None))
    if _num(case.get("forecast_year")):
        kw["forecast_year"] = _num(case["forecast_year"])
    if growth is not None:
        kw["growth"] = growth
    # THE CONNECTING FEED LEVEL. Left out of a case, the shipped 1.0 applies and the row is identical
    # to every row this runner has produced. Named in a case, it moves the multiplier on the whole
    # connecting capture, which is what makes the shipped level testable against the 0.06 the
    # back-test graded. qsi_k_behind is passed only when named, so it falls back to qsi_k inside
    # route_feed rather than arriving as a None the fallback cannot see past.
    if case.get("qsi_k") is not None:
        kw["qsi_k"] = _num(case["qsi_k"], cast=float)
    if case.get("qsi_k_behind") is not None:
        kw["qsi_k_behind"] = _num(case["qsi_k_behind"], cast=float)

    r = CA.calibrated_forecast(case["origin"], case["dest"], **kw)
    if not r.get("ok"):
        return {"error": r.get("error", "forecast returned ok=False with no error")}

    d, cap, sch = r.get("demand") or {}, r.get("capacity") or {}, r.get("schedule") or {}
    for k in DEMAND_KEYS:
        if k not in d:
            return {"error": "demand payload has no key %r; scenario_runner needs updating" % k}
    for k in CAPACITY_KEYS:
        if k not in cap:
            return {"error": "capacity payload has no key %r; scenario_runner needs updating" % k}
    if not r.get("economics_ok"):
        return {"error": r.get("economics_error", "economics not returned")}
    e = r["economics"]

    # TWO-WAY. The engine returns each way; the seats it was given are each way; a client reads both
    # directions. Ratios are unaffected by the doubling and are left alone.
    def two(x):
        return None if x is None else round(float(x) * 2.0)

    seats_2w = two(cap["annual_capacity"])
    demand_2w = two(d["total_demand"])
    carried_2w = two(cap["carried"])
    p2p_dem_2w = two(d["captured"])
    cnx_dem_2w = two(d["feed_total"])

    row = {
        "case": case.get("name") or "%s-%s %s %s %sx" % (case["origin"], case["dest"],
                                                         case.get("airline") or "",
                                                         case.get("aircraft") or "", freq),
        "origin": case["origin"], "dest": case["dest"],
        "airline": case.get("airline") or "", "carrier_type": kw["carrier_type"],
        "aircraft": kw["aircraft"],
        "seats_per_dep": seats or cap.get("seats") or "",
        "freq_wk": freq, "forecast_year": sch.get("forecast_year") or "",
        "total_demand_2w": demand_2w, "seats_2w": seats_2w,
        "demand_lf": round(demand_2w / seats_2w, 4) if seats_2w else None,
        "p2p_demand_2w": p2p_dem_2w, "connecting_demand_2w": cnx_dem_2w,
        "connecting_share": round(cnx_dem_2w / demand_2w, 4) if demand_2w else None,
        "carried_2w": carried_2w,
        "p2p_carried_2w": two(d["p2p_carried"]), "connecting_carried_2w": two(d["connecting_carried"]),
        "spill_2w": two(cap["spill"]),
        "plan_lf_achieved": round(carried_2w / seats_2w, 4) if seats_2w else None,
        "capture_share": round(float(d["qsi_share"]), 4) if d["qsi_share"] is not None else None,
        "natural_market_2w": two(d["natural"]),
        "growth_basis": sch.get("growth_basis") or "",
        "dep_time": _hhmm(dep), "dep_basis": sch.get("basis") or "",
        "partners": ",".join(partners), "split_floor": split_floor, "plan_lf_cap": plan_lf,
        "season": season,
        # Read from the payload rather than from the case, so the column records what the engine
        # actually applied. A case that names no level and a row that reports no level are two
        # different things: the second means no operator was named and no connecting feed was built.
        "qsi_k": (r.get("feed_level") or {}).get("qsi_k"),
        "qsi_k_behind": (r.get("feed_level") or {}).get("qsi_k_behind"),
        "feed_level_basis": (r.get("feed_level") or {}).get("basis") or "no feed",
        # Read from the payload rather than from the environment, so the column reports what the
        # engine DID and not what the shell was asked for. Those are the two things that differed.
        "local_engine": (r.get("forecast_engine") or {}).get("local_leg") or "unknown",
        "engine_mode": (r.get("forecast_engine") or {}).get("mode") or "",
        "engine_tier": (r.get("forecast_engine") or {}).get("tier") or "",
        "engine_declined": (r.get("forecast_engine") or {}).get("declined") or "",
        "engine": os.environ.get("AVIA_FORECAST_ENGINE", "") or "qsi (default)",
        "freq_sensitive": os.environ.get("AVIA_FREQ_SENSITIVE", "") or "OFF",
        "oag_week": r.get("week") or "", "sabre_year": r.get("year") or "",
    }
    for f in ECON_FIELDS:
        row[ECON_COLUMN.get(f, f)] = e.get(f)

    # TRAFFIC RIGHTS, advisory and never blocking, per the wording rule of 9 August: what we can
    # show a client is that no carrier of this country flies between these two countries anywhere in
    # the world, which is a fact, and not that a bilateral prohibits it, which is a legal claim we
    # cannot source. Starlux is the case to watch: it was founded after 2018, is absent from the
    # 2018 carrier_home reference, and was once silently dropped from the one route it belongs on.
    row["traffic_rights"] = ""
    if _bool(case.get("traffic_rights"), True) and case.get("airline"):
        try:
            import traffic_rights as TR
            v = TR.check(case["airline"].upper(), case["origin"].upper(), case["dest"].upper())
            row["traffic_rights"] = v.get("verdict", "UNKNOWN")
            if v.get("verdict") == "UNKNOWN":
                row["traffic_rights"] = "UNKNOWN: %s" % v.get("reason", "")
        except Exception as exc:                            # noqa: BLE001
            # Recorded in the cell rather than raised. The verdict is advisory, so a failed lookup
            # must not lose a whole run, and it must not read as a clean HOME either.
            row["traffic_rights"] = "CHECK FAILED: %s" % exc
    return row


# ---------------------------------------------------------------------------------------------
# The file of cases

def load_cases(path):
    """A .json file with defaults and cases, or a .csv with one case per row."""
    if path.lower().endswith(".csv"):
        with open(path, encoding="utf-8-sig", newline="") as fh:
            rows = [{k.strip(): (v.strip() if isinstance(v, str) else v)
                     for k, v in r.items() if k and k.strip()} for r in csv.DictReader(fh)]
        return {}, [r for r in rows if any(v for v in r.values())], {}
    with open(path, encoding="utf-8") as fh:
        blob = json.load(fh)
    if isinstance(blob, list):
        return {}, blob, {}
    opts = {k: v for k, v in blob.items() if k not in ("defaults", "cases")}
    return blob.get("defaults") or {}, blob.get("cases") or [], opts


def run(path, out_csv=None):
    defaults, cases, opts = load_cases(path)
    if not cases:
        raise SystemExit("NOT RUN. %s carries no cases." % path)

    # THE FREQUENCY SWITCH. With AVIA_FREQ_SENSITIVE off the engine substitutes the measured airport
    # capture factor and returns the same demand at every frequency, so a frequency ladder comes back
    # flat and only the load factor moves. A tester running a ladder would not necessarily notice.
    # It was decided ON on 10 August 2026, so a run without it stops unless the cases file says
    # plainly that it means to.
    if os.environ.get("AVIA_FREQ_SENSITIVE", "").strip() not in ("1", "true", "on"):
        if not _bool(opts.get("allow_freq_insensitive"), False):
            raise SystemExit(
                "NOT RUN. AVIA_FREQ_SENSITIVE is not set. With it off the capture share is the "
                "measured airport factor at every frequency, so a frequency ladder returns the "
                "same demand at 3x and at 14x and only the load factor moves.\n"
                '  PowerShell:  $env:AVIA_FREQ_SENSITIVE = "1"\n'
                "  or set \"allow_freq_insensitive\": true in the cases file if that is the run "
                "you intend.")

    rows, failed = [], {}
    for i, c in enumerate(cases, 1):
        case = dict(defaults)
        case.update({k: v for k, v in c.items() if v not in (None, "")})
        name = case.get("name") or "case %d" % i
        row = run_case(case)
        if "error" in row:
            failed[name] = row["error"]
            print("  %-52s FAILED  %s" % (name[:52], row["error"]))
            continue
        rows.append(row)
        # The engine is on the console line, not only in the file. A run whose figures match the
        # previous one is either the switch not taking effect or the model declining, and reading a
        # CSV afterwards to find out which is how an evening gets spent.
        _eng = "BT2" if row["local_engine"].startswith("calibrated") else "qsi"
        print("  %-46s %-4s demand %10s  seats %10s  LF %6s  capture %6s"
              % (row["case"][:46], _eng, "{:,}".format(row["total_demand_2w"]),
                 "{:,}".format(row["seats_2w"]),
                 "%.1f%%" % (100 * row["demand_lf"]) if row["demand_lf"] else "-",
                 "%.2f%%" % (100 * row["capture_share"]) if row["capture_share"] else "-"))
        if row["engine_declined"]:
            print("       %s" % row["engine_declined"][:110])

    # REFUSE TO WRITE A RESULTS FILE IN WHICH ANY CASE ERRORED. A table with three rows where five
    # were asked for reads as a completed run, and the two that are missing are exactly the two
    # worth knowing about.
    if failed:
        raise SystemExit(
            "\nNOT WRITTEN. %d of %d cases failed, so the table would be incomplete and would not "
            "say so:\n  %s" % (len(failed), len(cases),
                               "\n  ".join("%s: %s" % (n, e) for n, e in failed.items())))

    out_csv = out_csv or os.path.splitext(path)[0] + "_results.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(COLUMNS), extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    out_json = os.path.splitext(out_csv)[0] + ".json"
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump({"note": "Scenario run. Every figure comes from cortex_app.calibrated_forecast, "
                           "which is the single place a client number is produced. Columns ending "
                           "_2w are both directions and columns ending _ew are each way. demand_lf "
                           "is total demand over seats and answers whether the demand is there to "
                           "fill the aeroplane; plan_lf_achieved is carried over seats, is capped "
                           "at plan_lf_cap and can only ever be the lower of the two. Read one for "
                           "the other and you are comparing a capped figure with an uncapped one. "
                           "spill_2w comes from the capacity block, whose basis the SPILL-SUSPECT "
                           "entry of 10 August 2026 leaves open; econ_spilled_ew is the "
                           "economics block's own each-way figure and is a different quantity.",
                   "run_utc": EB._now_utc(), "cases_file": os.path.abspath(path),
                   "provenance": EB._provenance(), "switches": EB._env(),
                   "columns": list(COLUMNS), "rows": rows}, fh, indent=2, default=str)
    return out_csv, out_json, rows


# ---------------------------------------------------------------------------------------------
# A worked example to start from

TEMPLATE = {
    "note": "Edit and re-run. Seat counts are the carriers' own configurations measured from OAG "
            "2025 on comparable sectors by capacity_frame.frame, not the generic type table: "
            "China Airlines and Starlux fly the A350-900 at 306 against the table's 336, EVA flies "
            "the 787-9 at 278 against 320, and the 777-300ER is 333 at EVA and 358 at China "
            "Airlines against 380. Sizing on the generic figure overstates capacity by 8 to 13% on "
            "these carriers. Growth is the post-recovery path at 7% a year: the engine's default "
            "taper measures a 20.00% CAGR, which is the clamp ceiling and a recovery burst, and is "
            "not to be used for client work. split_floor false makes the connecting leg comparable "
            "with the 2025 analyst; true is what ships.",
    "defaults": {"origin": "SJC", "dest": "TPE", "carrier_type": "FSC", "growth": 0.07,
                 "split_floor": False, "partners": ["WN"], "dep_time": "12:00"},
    "cases": [
        {"name": "SJC-TPE CI A359 306 4x 2027, the analyst's case", "airline": "CI",
         "aircraft": "A359", "seats": 306, "freq": 4, "forecast_year": 2027},
        {"name": "SJC-TPE CI A359 306 5x 2027", "airline": "CI", "aircraft": "A359",
         "seats": 306, "freq": 5, "forecast_year": 2027},
        {"name": "SJC-TPE CI A359 306 4x 2028", "airline": "CI", "aircraft": "A359",
         "seats": 306, "freq": 4, "forecast_year": 2028},
        {"name": "SJC-TPE CI A359 306 5x 2028", "airline": "CI", "aircraft": "A359",
         "seats": 306, "freq": 5, "forecast_year": 2028},
        {"name": "SJC-TPE CI A359 306 6x 2028", "airline": "CI", "aircraft": "A359",
         "seats": 306, "freq": 6, "forecast_year": 2028},
        {"name": "SJC-TPE BR B789 278 4x 2028", "airline": "BR", "aircraft": "B789",
         "seats": 278, "freq": 4, "forecast_year": 2028},
        {"name": "SJC-TPE BR B77W 333 4x 2028", "airline": "BR", "aircraft": "B77W",
         "seats": 333, "freq": 4, "forecast_year": 2028},
        {"name": "SJC-TPE BR B77W 333 7x 2028", "airline": "BR", "aircraft": "B77W",
         "seats": 333, "freq": 7, "forecast_year": 2028},
        {"name": "SJC-TPE JX A359 306 4x 2028, Starlux", "airline": "JX", "aircraft": "A359",
         "seats": 306, "freq": 4, "forecast_year": 2028},
        {"name": "SJC-TPE JX A359 306 7x 2028, Starlux", "airline": "JX", "aircraft": "A359",
         "seats": 306, "freq": 7, "forecast_year": 2028},
        {"name": "SJC-TPE UA B789 257 7x 2028", "airline": "UA", "aircraft": "B789",
         "seats": 257, "freq": 7, "forecast_year": 2028},
        {"name": "SJC-TPE DL A359 306 5x 2028", "airline": "DL", "aircraft": "A359",
         "seats": 306, "freq": 5, "forecast_year": 2028},
        {"name": "SJC-TPE CI A359 306 4x 2028, floor ON as shipped", "airline": "CI",
         "aircraft": "A359", "seats": 306, "freq": 4, "forecast_year": 2028,
         "split_floor": True},
        {"name": "SFO-TPE BR B77W 333 7x 2028, the served control", "origin": "SFO",
         "airline": "BR", "aircraft": "B77W", "seats": 333, "freq": 7, "forecast_year": 2028,
         "dep_time": "01:15"},
        {"name": "SJC-LHR BA B789 216 7x 2028", "dest": "LHR", "airline": "BA",
         "aircraft": "B789", "seats": 216, "freq": 7, "forecast_year": 2028,
         "partners": [], "dep_time": "optimise"},
        {"name": "GOA-JFK DL B739 180 7x 2028", "origin": "GOA", "dest": "JFK", "airline": "DL",
         "aircraft": "B739", "seats": 180, "freq": 7, "forecast_year": 2028,
         "partners": [], "dep_time": "optimise"},
    ],
}


def main():
    ap = argparse.ArgumentParser(description="Run a file of route scenarios through Meridian.")
    ap.add_argument("cases", nargs="?", help="a .json or .csv file of cases")
    ap.add_argument("--out", help="where to write the results table")
    ap.add_argument("--template", metavar="PATH", help="write a worked example and stop")
    a = ap.parse_args()
    if a.template:
        with open(a.template, "w", encoding="utf-8") as fh:
            json.dump(TEMPLATE, fh, indent=2)
        print("written:", a.template)
        print("edit it, then:  py -3.12 scenario_runner.py", a.template)
        return
    if not a.cases:
        ap.error("name a cases file, or --template PATH to write one to start from")
    print("running %s" % a.cases)
    csv_path, json_path, rows = run(a.cases, a.out)
    print("\n%d case(s) written:" % len(rows))
    print("   ", csv_path)
    print("   ", json_path)


if __name__ == "__main__":
    main()
