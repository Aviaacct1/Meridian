#!/usr/bin/env python3
r"""Preview of Optimise on the schedule prior, for named pairs, without touching app/. W10, Sep 2026.

    $env:AVIA_FORECAST_ENGINE = "bt2"; plus the usual AVIA_* variables
    py -3.12 -s bt2_prior_preview.py BLQ-JFK:UA GOA-JFK:UA SOU-JFK:UA

For each pair: the existing O&D on the raw pair from Sabre (route_context.market, the model's own
base_mkt), the comparable launches in the record (same class as bt2_schedule_prior --lookup), the
prior's schedule band (gauge and weekly frequency at p25, median, p75 of the region-pair set when it
holds 20 or more launches, else of all comparable launches), the carrier's own line, and the
calibrated model's LOCAL NONSTOP forecast at each of the three schedules, through the same
route_context.build and bt2_forecast.forecast the app calls. The model's figure is TWO-WAY (log line
W10-BASIS-IN-THE-PAYLOAD); each way is printed beside it. Current year, no growth carried: the app
adds growth to the forecast year on top. No connecting feed: that is route_forecast's V1 flat capture
and is outside this preview and outside the record. Nothing is written.

Avia Solutions Limited. All rights reserved.
"""
import math
import os
import statistics
import sys

import airportsdata

import bt2_gbm as G
import bt2_lib as B
import bt2_g12_exp as F
from bt2_paths import find_app
from bt2_claimset import _provenance
from bt2_record_mix import region_pair

sys.path.insert(0, find_app())
import route_context as RC        # noqa: E402
import bt2_forecast as BF         # noqa: E402

AP = airportsdata.load("IATA")


def gc_km(a, b):
    la, lo, lb, lob = (math.radians(AP[a]["lat"]), math.radians(AP[a]["lon"]),
                       math.radians(AP[b]["lat"]), math.radians(AP[b]["lon"]))
    h = math.sin((lb - la) / 2) ** 2 + math.cos(la) * math.cos(lb) * math.sin((lob - lo) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def q(v, f):
    v = sorted(v)
    return v[min(len(v) - 1, int(f * len(v)))]


def band(rs):
    return {"gauge": (q([r["gauge"] for r in rs], .25), statistics.median(r["gauge"] for r in rs),
                      q([r["gauge"] for r in rs], .75)),
            "freq": (q([r["freq"] for r in rs], .25), statistics.median(r["freq"] for r in rs),
                     q([r["freq"] for r in rs], .75))}


def main():
    rows = G.rows
    F.attach(rows)
    print("\nrecord: n=%d from %s   engine switch: %s   build: %s"
          % (len(rows), B.BT2, os.environ.get("AVIA_FORECAST_ENGINE"), _provenance()))
    st = BF.status()
    print("model: %s (%s, trained on %s)" % (st.get("model_path"), st.get("population"), st.get("trained_on")))
    # THE BASE YEAR, as the app passes it (cortex_app 1287: year=ctx["year"], the latest Sabre source
    # year). Left to default, route_context builds pre_month from today's calendar year, 2026-01, for
    # which the OAG store holds no legs, and refuses the route by name. Measured 26 Sep 2026.
    import duckdb
    _c = duckdb.connect(RC._store("sabre"), read_only=True)
    YEAR = int(_c.execute("SELECT max(source_year) FROM sabre").fetchone()[0]); _c.close()
    print("base year: %d (latest Sabre source year, as the app passes it); pre-launch month %d-01" % (YEAR, YEAR))
    for spec in sys.argv[1:]:
        pair, _, car = spec.partition(":")
        a, b = pair.split("-")
        car = car or "UA"
        dom = AP[a]["country"] == AP[b]["country"]
        gcd = gc_km(a, b)
        bm, gro, err = RC.market(a, b, year=YEAR)
        print("\n" + "=" * 78)
        print("%s-%s, %s: %.0f km, %s; existing O&D on the raw pair (Sabre, both directions) %s"
              % (a, b, car, gcd, "domestic" if dom else "international",
                 ("{:,.0f}, growth x{:.2f}".format(bm, gro) if bm else "NONE: %s" % err)))
        if not bm:
            continue
        comp = [r for r in rows if r["dom"] == dom and r["typ"] == "FSC"
                and 0.5 * bm <= r["base_mkt"] <= 2.0 * bm and 0.6 * gcd <= r["gcd"] <= 1.6 * gcd]
        rp = region_pair({"ctry_a": AP[a]["country"], "ctry_b": AP[b]["country"], "dom": dom})
        same = [r for r in comp if region_pair(r) == rp]
        use = same if len(same) >= 20 else comp
        print("  comparable launches: %d, of which %s %d; prior taken from %s"
              % (len(comp), rp, len(same), "the %s set" % rp if use is same else "all comparable"))
        if len(use) < 10:
            print("  fewer than 10 comparable launches: the prior cannot be stated for this pair")
            continue
        bd = band(use)
        own = [r for r in rows if r["oag_carrier"] == car]
        cid = {id(r) for r in comp}
        ownc = [r for r in own if id(r) in cid]
        ownl = [r for r in own if r["gcd"] >= 2500 and not r["dom"]]
        print("  %s in the record: %d launches; long-haul international %d (gauge med %s, freq med %s); "
              "on comparable pairs %d%s"
              % (car, len(own), len(ownl),
                 ("%.0f" % statistics.median(r["gauge"] for r in ownl)) if ownl else "n/a",
                 ("%.1f" % statistics.median(r["freq"] for r in ownl)) if ownl else "n/a",
                 len(ownc), (" (gauge med %.0f, freq med %.1f)" % (statistics.median(r["gauge"] for r in ownc),
                                                                     statistics.median(r["freq"] for r in ownc))) if ownc else ""))
        print("  %-10s %6s %6s %14s %14s %12s %12s" % ("schedule", "gauge", "freq", "seats 2-way/yr",
                                                       "local 2-way", "each way", "p25-p75 ew"))
        out = None
        for label, i in (("p25", 0), ("median", 1), ("p75", 2)):
            g, f = bd["gauge"][i], bd["freq"][i]
            ctx = RC.build(a, b, car, aircraft_seats=g, freq=f, months=12, launch_mon=1, year=YEAR)
            if not ctx.get("ok"):
                print("  %-10s %6.0f %6.1f   route context: %s" % (label, g, f, "; ".join(ctx.get("missing", []))))
                continue
            out = BF.forecast(ctx, mode="indicative")
            if not out or not out.get("ok"):
                print("  %-10s %6.0f %6.1f   model: %s" % (label, g, f, (out or {}).get("reason", "switch not set")))
                continue
            print("  %-10s %6.0f %6.1f %14s %14s %12s %12s"
                  % (label, g, f, "{:,.0f}".format(ctx["seats_ly"]), "{:,.0f}".format(out["pax"]),
                     "{:,.0f}".format(out["pax"] / 2), "{:,.0f}-{:,.0f}".format(out["lo"] / 2, out["hi"] / 2)))
        if out and out.get("ok"):
            print("  (local nonstop only, current year, tier %s; the app adds growth to the forecast year and the feed)"
                  % out.get("tier", "?"))


if __name__ == "__main__":
    main()
