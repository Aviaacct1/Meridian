#!/usr/bin/env python3
r"""What could actually fly this route, and with what. The plausible capacity frame.

    python3 capacity_frame.py SJC TPE

WHY THIS EXISTS, and it settles the circularity objection rather than working around it. BT2 is
anchored on capacity, and the worry was that Meridian choosing the capacity and then forecasting
from it is circular: the tool picks a big aircraft and reports that the route carries a lot.

John's point of 9 August, and it is right: capacity is not a free variable. An airline can only fly
a route with an aircraft it operates and that has the range. It flies that aircraft at the seat
count it actually configures. It opens routes of a given length at the frequency it actually uses.
Every one of those is observable in OAG. So for SJC-TPE the set is not "any capacity we like": it is
China Airlines with perhaps three aircraft, EVA with two, Starlux with one, each at a frequency that
carrier actually opens long-haul routes with. Capacity is bounded and enumerable, which makes it a
constraint of the same kind as flying time.

WHAT THIS RETURNS. For each carrier that could credibly fly the pair, the aircraft it operates on
sectors of comparable length, the seats it configures them with, and the frequencies it uses. That
is the option set an airport takes to an airline, and it is the input BT2 needs.

WHAT IT DOES NOT DO. It does not pick one. Picking is what makes the answer circular. It hands the
caller an enumerated set so every option can be forecast and the airport can see which ones work.

Sources: OAG schedules for the aircraft, seats and frequencies; the pair's own great-circle distance
for the range test. Nothing here is assumed, and a carrier with no observed sector of the required
length does not appear.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import os
import sys

import duckdb


def _oag():
    p = os.environ.get("AVIA_OAG_DUCKDB")
    if p and os.path.exists(p):
        return p
    root = os.environ.get("AVIA_LOCAL_CACHE")
    for r in [root, os.path.join("E:" + os.sep, "Avia"), os.path.join("C:" + os.sep, "Avia")]:
        if r and os.path.exists(os.path.join(r, "oag.duckdb")):
            return os.path.join(r, "oag.duckdb")
    return None


def frame(a, b, period="2025-%", min_ops=6, band=0.25):
    """The option set for the unordered pair a-b.

    band widens the sector length either side of the pair's own distance, so 'aircraft this carrier
    flies on routes about this long' is measured rather than assumed from a range table. A range
    table says what an aircraft CAN do; the schedule says what the airline DOES.
    """
    db = _oag()
    if not db:
        sys.exit("no OAG store found. Set AVIA_OAG_DUCKDB or AVIA_LOCAL_CACHE.")
    con = duckdb.connect(db, read_only=True)
    con.execute("SET memory_limit='3GB'; SET threads=3")

    gcd = con.execute("""
      SELECT max(try_cast(gcd_km AS DOUBLE)) FROM oag
      WHERE ((dep_airport=? AND arr_airport=?) OR (dep_airport=? AND arr_airport=?))
    """, [a, b, b, a]).fetchone()[0]
    if not gcd:
        # No scheduled service between the pair in the store, which is expected for a virgin route.
        # Fall back to the great circle from the airport coordinates rather than guessing.
        import airportsdata
        import math
        ap = airportsdata.load("IATA")
        if a not in ap or b not in ap:
            sys.exit("no distance available for %s-%s and one of them is not in the airport table" % (a, b))
        la1, lo1 = math.radians(ap[a]["lat"]), math.radians(ap[a]["lon"])
        la2, lo2 = math.radians(ap[b]["lat"]), math.radians(ap[b]["lon"])
        h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
        gcd = 2 * 6371 * math.asin(math.sqrt(h))
    lo, hi = gcd * (1 - band), gcd * (1 + band)

    # WHO IS A CREDIBLE OPERATOR, and the first version of this got it wrong by asking only for
    # presence at an endpoint. That let British Airways and Emirates into an SJC-TPE frame because
    # they serve Taipei, which is true and useless: neither would fly the pair.
    #
    # Route development says a carrier needs BOTH ends: it must already serve one airport, and it
    # must already fly to the other airport's COUNTRY, which is what says it has the rights, the
    # range and a reason. That is the test applied here, in both directions.
    ctry = {}
    for ap_, cc in con.execute("""
          SELECT dep_airport, any_value(dep_country) FROM oag
          WHERE dep_airport IN (?, ?) GROUP BY 1""", [a, b]).fetchall():
        ctry[ap_] = cc
    ca, cb = ctry.get(a), ctry.get(b)
    if not ca or not cb:
        sys.exit("cannot resolve the country of %s or %s from the schedule store" % (a, b))
    present = {r[0] for r in con.execute("""
      WITH at_a AS (SELECT DISTINCT carrier FROM oag WHERE service_type='J' AND week LIKE ?
                      AND (dep_airport=? OR arr_airport=?)),
           at_b AS (SELECT DISTINCT carrier FROM oag WHERE service_type='J' AND week LIKE ?
                      AND (dep_airport=? OR arr_airport=?)),
           to_ca AS (SELECT DISTINCT carrier FROM oag WHERE service_type='J' AND week LIKE ?
                       AND (dep_country=? OR arr_country=?)),
           to_cb AS (SELECT DISTINCT carrier FROM oag WHERE service_type='J' AND week LIKE ?
                       AND (dep_country=? OR arr_country=?))
      SELECT carrier FROM at_a WHERE carrier IN (SELECT carrier FROM to_cb)
      UNION
      SELECT carrier FROM at_b WHERE carrier IN (SELECT carrier FROM to_ca)
    """, [period, a, a, period, b, b, period, ca, ca, period, cb, cb]).fetchall() if r[0]}

    # AND THE OPERATOR IS BASED AT ONE END. The rule above still let British Airways into an
    # SJC-TPE frame: BA serves Taipei and flies to the United States, so it passes both halves and
    # would never fly the pair. A nonstop between two countries is flown by a carrier of one of
    # them, barring fifth-freedom operations which are rare and are excluded here rather than
    # silently included. Home country is measured, not declared: the country a carrier flies the
    # most departing seats from, per bt2_region.py.
    # Home country is resolved FROM THE PERIOD BEING FRAMED, not from a stored lookup. The first
    # version read carrier_home.json, which bt2_region.py builds from a 2018 reference year on the
    # grounds that a carrier's home is structural and slow moving. A home is. A carrier is not:
    # Starlux was founded after 2018, is absent from that file, and was silently deleted from an
    # SJC-TPE frame, which is the one route it obviously belongs in. A missing lookup entry must
    # never remove an operator without saying so, and here it need not be a lookup at all.
    based = {r[0] for r in con.execute("""
      SELECT carrier FROM (
        SELECT carrier, dep_country,
               row_number() OVER (PARTITION BY carrier
                                  ORDER BY sum(try_cast(seats_total AS DOUBLE)) DESC) rn
        FROM oag WHERE service_type='J' AND week LIKE ?
          AND dep_country IS NOT NULL AND trim(dep_country) <> ''
        GROUP BY 1,2)
      WHERE rn = 1 AND dep_country IN (?, ?)
    """, [period, ca, cb]).fetchall()}
    dropped = present - based
    present = present & based
    if dropped:
        # Said out loud. A filter that quietly halves the option set is worse than no filter.
        print("  excluded as not based in %s or %s: %s"
              % (ca, cb, ", ".join(sorted(dropped)[:12]) + ("..." if len(dropped) > 12 else "")))

    rows = con.execute("""
      SELECT carrier, aircraft_code, any_value(aircraft_name) nm,
             count(*) ops,
             median(try_cast(seats_total AS DOUBLE)) seats,
             median(try_cast(business_seats AS DOUBLE) + try_cast(first_seats AS DOUBLE)) prem,
             count(DISTINCT dep_airport || '-' || arr_airport) routes,
             min(try_cast(gcd_km AS DOUBLE)) km_lo, max(try_cast(gcd_km AS DOUBLE)) km_hi
      FROM oag
      WHERE service_type='J' AND week LIKE ? AND try_cast(stops AS INT)=0
        AND try_cast(gcd_km AS DOUBLE) BETWEEN ? AND ?
      GROUP BY 1,2 HAVING count(*) >= ?
    """, [period, lo, hi, min_ops]).fetchall()

    out = {}
    for car, ac, nm, ops, seats, prem, routes, kl, kh in rows:
        if car not in present or not seats:
            continue
        out.setdefault(car, []).append(
            {"aircraft": ac, "name": nm, "ops": int(ops), "seats": int(seats),
             "premium": int(prem or 0), "routes": int(routes),
             "km_range": (int(kl or 0), int(kh or 0))})
    for car in out:
        out[car].sort(key=lambda d: -d["ops"])
    return gcd, out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--period", default="2025-%")
    ap.add_argument("--band", type=float, default=0.25)
    ap.add_argument("--max-carriers", type=int, default=12)
    x = ap.parse_args()
    a, b = x.a.upper(), x.b.upper()
    gcd, f = frame(a, b, x.period, band=x.band)
    print("%s-%s, %.0f km. Aircraft each carrier actually flies on sectors %.0f to %.0f km, "
          "period %s" % (a, b, gcd, gcd * (1 - x.band), gcd * (1 + x.band), x.period))
    if not f:
        print("  no carrier present at either endpoint operates a sector of this length. "
              "On this evidence the pair has no credible operator, which is itself the finding.")
        return
    order = sorted(f, key=lambda c: -sum(d["ops"] for d in f[c]))
    for car in order[:x.max_carriers]:
        opts = f[car]
        print("\n  %s: %d aircraft option%s" % (car, len(opts), "" if len(opts) == 1 else "s"))
        for d in opts[:5]:
            print("    %-5s %-22s %4d seats (%3d premium)  on %3d routes, %5d sectors, %5d-%5d km"
                  % (d["aircraft"], (d["name"] or "")[:22], d["seats"], d["premium"],
                     d["routes"], d["ops"], d["km_range"][0], d["km_range"][1]))


if __name__ == "__main__":
    main()
