#!/usr/bin/env python3
r"""The with/without direct competition split: measured, validated, then shipped.

John's ruling, 18 August 2026: the 2025 analyst's competed/uncompeted sub-rows
(0.0%/1.5% over TPE, 0.2%/4.7% at SJC on the CI case) go back into the client
tables, worked out properly. The design honours the k decision: V1 CARRIES THE
LEVEL, untouched; the gated QSI feed provides the per-market SHAPE; this script
renormalises the QSI-shaped market shares to the V1 leg totals, classifies each
market as competed or not, and prints the bucket capture rates beside the
analyst's, which is the validation. Nothing here changes the engine or any
shipped number: two ordinary runs and arithmetic.

CLASSIFICATION (the ruling's rule, catchment plus other servicing airports):
a BEYOND market is competed when a nonstop flies from ANY catchment airport of
the origin to that city in the OAG snapshot week; a BEHIND market is competed
when a nonstop flies from that city to the destination. City codes expand to
same-city airports via airportsdata where available.

Run on the WORKSTATION (stores):

    py -3.12 competition_split.py SJC TPE --airline CI --aircraft A359 --seats 306
        --freq 4 --forecast-year 2028

Avia Solutions Limited. All rights reserved.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


# --- pure arithmetic (fixture-tested offline) --------------------------------

def renormalise(rows, leg_total):
    """Scale market forecasts so they sum to the V1 leg total. rows =
    [{"city_code", "annual_demand", "annual_forecast"}]. Returns new rows with
    "alloc" added; None when the rows carry no forecast to shape with."""
    ssum = sum((r.get("annual_forecast") or 0) for r in rows)
    if ssum <= 0 or leg_total <= 0:
        return None
    out = []
    for r in rows:
        rr = dict(r)
        rr["alloc"] = (r.get("annual_forecast") or 0) * leg_total / ssum
        out.append(rr)
    return out


def flatness(rows):
    """Coefficient of variation of the market SHARES (forecast/base). Near zero
    means the shape arm returned flat shares and there is nothing to distribute
    with; the caller says so and stops rather than shipping a fake split."""
    shares = [(r.get("annual_forecast") or 0) / b
              for r in rows for b in [(r.get("annual_demand") or 0)] if b > 0]
    n = len(shares)
    if n < 2:
        return 0.0
    m = sum(shares) / n
    if m <= 0:
        return 0.0
    var = sum((s - m) ** 2 for s in shares) / n
    return (var ** 0.5) / m


def bucket(rows, competed):
    """Two buckets from allocated rows. competed = set of city codes. Returns
    {"competed": {...}, "uncompeted": {...}} with base, alloc, capture."""
    out = {}
    for name, member in (("competed", True), ("uncompeted", False)):
        sel = [r for r in rows if (r.get("city_code") in competed) == member]
        base = sum((r.get("annual_demand") or 0) for r in sel)
        alloc = sum((r.get("alloc") or 0) for r in sel)
        out[name] = {"n": len(sel), "base": base, "alloc": alloc,
                     "capture": (alloc / base) if base > 0 else None}
    return out


# --- the run -----------------------------------------------------------------

def _city_airports(code):
    """The city code itself plus same-city airports, best effort."""
    aps = {code}
    try:
        import airportsdata
        db = airportsdata.load("IATA")
        rec = db.get(code)
        if rec and rec.get("city"):
            city, country = rec["city"], rec.get("country")
            for k, v in db.items():
                if v.get("city") == city and v.get("country") == country:
                    aps.add(k)
    except Exception:
        pass
    return aps


def _served(con, week, dep_aps, arr_aps):
    q = ("SELECT 1 FROM oag WHERE week = ? AND dep_airport IN (%s) "
         "AND arr_airport IN (%s) LIMIT 1"
         % (",".join("?" * len(dep_aps)), ",".join("?" * len(arr_aps))))
    return bool(con.execute(q, [week] + sorted(dep_aps) + sorted(arr_aps)).fetchall())


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("origin"); ap.add_argument("dest")
    ap.add_argument("--airline", default=""); ap.add_argument("--aircraft", default="A359")
    ap.add_argument("--seats", type=float, default=0.0)
    ap.add_argument("--freq", type=int, default=4)
    ap.add_argument("--forecast-year", type=int, default=0)
    ap.add_argument("--partners", default="")
    ap.add_argument("--reference", default="beyond=0.0,1.5 behind=0.2,4.7",
                    help="the analyst's competed,uncompeted %% rates for comparison")
    ap.add_argument("--json-out", default="", help="write the result as JSON here")
    a = ap.parse_args()

    import cortex_app as CA
    import cortex_workbook as CWB

    def run(level):
        os.environ["AVIA_FEED_LEVEL"] = level
        fc = CA.calibrated_forecast(
            a.origin, a.dest, airline=(a.airline or None), aircraft=a.aircraft,
            seats=(a.seats or None), freq=a.freq, with_econ=True,
            forecast_year=(a.forecast_year or None),
            partner_carriers=(a.partners or None))
        if not fc.get("ok"):
            raise SystemExit("run at level %s failed: %s" % (level, fc.get("error")))
        if fc.get("warnings"):
            print("NOTE: the %s run carries warnings: %s" % (level, fc["warnings"]))
        return fc

    print("Arm 1: the SHIPPED configuration (V1 level)")
    fc_v1 = run("v1")
    print("Arm 2: the QSI feed (per-market shape only; its level is discarded)")
    fc_q = run("qsi")
    os.environ["AVIA_FEED_LEVEL"] = "v1"   # leave the process as shipped

    dem = fc_v1["demand"]
    _p2p, behind_t, beyond_t, _tot = CWB.carried_split(dem)
    legs = {"beyond": (fc_q["demand"].get("beyond_pdew") or [], beyond_t),
            "behind": (fc_q["demand"].get("behind_pdew") or [], behind_t)}

    # classification
    import db_registry
    import config as CFG
    oag_db = os.environ.get("AVIA_OAG", str(CFG.OAG_DUCKDB))
    week = fc_v1.get("week")
    cat_aps = set((fc_v1.get("catchment") or {}).get("observed_share") or {})
    cat_aps.add(a.origin.upper())
    dest_aps = _city_airports(a.dest.upper())
    con = db_registry.con_ro(oag_db)
    ref = {}
    for part in (a.reference or "").split():
        k, _, v = part.partition("=")
        try:
            ref[k] = tuple(float(x) for x in v.split(","))
        except ValueError:
            pass
    verdicts = {}
    try:
        for leg, (rows, total) in legs.items():
            print("\n== Connecting %s: leg total (V1, carried) %.0f ==" % (leg, total))
            fl = flatness(rows)
            if fl < 0.05:
                print("  THE QSI ARM RETURNED FLAT SHARES (cv %.3f): there is no shape "
                      "to distribute with, and the split is NOT built from this. The "
                      "wiring of the qsi feed path wants inspection first." % fl)
                verdicts[leg] = {"ok": False, "reason": "flat shares, cv %.3f" % fl}
                continue
            alloc = renormalise(rows, total)
            if not alloc:
                verdicts[leg] = {"ok": False, "reason": "no rows to allocate"}
                continue
            competed = set()
            for r in alloc:
                c = (r.get("city_code") or "").upper()
                if not c:
                    continue
                if leg == "beyond":
                    hit = _served(con, week, cat_aps, _city_airports(c))
                else:
                    hit = _served(con, week, _city_airports(c), dest_aps)
                if hit:
                    competed.add(r.get("city_code"))
            b = bucket(alloc, competed)
            for name in ("competed", "uncompeted"):
                x = b[name]
                cap = ("%.2f%%" % (x["capture"] * 100)) if x["capture"] is not None else "-"
                print("  %-11s n=%2d  base %10.0f  allocated %8.0f  capture %s"
                      % (name, x["n"], x["base"], x["alloc"], cap))
            rname = leg
            if rname in ref and all(b[n]["capture"] is not None
                                    for n in ("competed", "uncompeted")):
                rc, ru = ref[rname]
                print("  analyst reference: competed %.1f%%, uncompeted %.1f%%" % (rc, ru))
            verdicts[leg] = {"ok": True, "buckets": b,
                             "competed_cities": sorted(competed)}
    finally:
        con.close()

    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as fh:
            json.dump(verdicts, fh, indent=1, default=str)
        print("\nwrote %s" % a.json_out)
    print("\nRead the bucket rates against the analyst's before any wiring: the "
          "split ships only if this validates.")


if __name__ == "__main__":
    main()
