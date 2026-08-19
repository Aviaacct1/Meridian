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


# OAG equipment code to the aircraft_economics key, for the types the economics module knows.
# Built 10 August 2026 from the codes actually present in the 2025 schedule, read with OAG's own
# aircraft_name beside each one, rather than written from memory. Types with no economics entry are
# absent ON PURPOSE and are reported by name by types_for rather than dropped in silence: the
# 787-10 is one of EVA's three real options on this sector length and the module cannot cost it.
OAG_TO_AIRCRAFT = {
    "320": "A320", "32A": "A320", "32S": "A320", "32N": "A20N",
    "321": "A321", "32B": "A321", "32Q": "A21N", "319": "A319",
    "738": "B738", "73H": "B738", "7M8": "B38M", "757": "B752",
    "AT7": "ATR72", "ATR": "ATR72", "DH4": "DH8D", "CR9": "CRJ900",
    "E70": "E170", "E90": "E190", "E95": "E195", "SF3": "SF34",
    "763": "B763", "76W": "B763",
    "333": "A333", "339": "A339", "359": "A359",
    "788": "B788", "789": "B789", "77W": "B77W",
    # Added 10 August 2026 with the seventeen new economics entries. Until these existed the codes
    # were deliberately absent, because mapping a code to a type the economics cannot cost would have
    # offered an airline an aeroplane with no P&L behind it. EVA's 787-10 is the case that mattered.
    "781": "B781", "772": "B772", "77L": "B772", "773": "B773", "74H": "B748",
    "753": "B753", "764": "B764",
    "332": "A332", "388": "A388",
    "221": "A221", "223": "A223",
    "733": "B733", "734": "B734", "735": "B735", "73E": "B735",
    "73W": "B737", "73G": "B737", "739": "B739", "73J": "B739", "7M9": "B39M", "717": "B717",
}


def to_aircraft_key(code):
    """The economics key for an OAG equipment code, or None when the module has no entry for it."""
    return OAG_TO_AIRCRAFT.get((code or "").strip().upper())


def types_for(carrier, gcd_km, period="2025-%", band=0.25, min_ops=6):
    """What this carrier is OBSERVED to fly on sectors of comparable length, as economics keys.

    The fleet the optimiser picks from was a hand-maintained table, and on 10 August 2026 it was
    wrong on every carrier in the SJC-TPE frame: China Airlines was given a 787-9 it does not fly on
    these sectors and denied the 777-300ER it does, EVA was given an A350-900 it does not fly, and
    Starlux was absent altogether so it fell back to every range-feasible type. A schedule store
    already records what each carrier flies at each sector length, so the table is not needed.

    Returns (keys, unmapped, sectors): keys are economics keys sorted by how much the carrier flies
    them, unmapped names the observed types the economics module cannot cost, and sectors is the
    observed sector count behind the answer. An empty result means OAG has nothing at this length
    for this carrier, and the caller should fall back rather than conclude the carrier flies nothing.
    """
    db = _oag()
    if not db or not carrier:
        return [], [], 0
    con = duckdb.connect(db, read_only=True)
    # The progress bar writes to stdout, which inside the app lands in the server log and in any
    # captured output. Off here; frame() keeps it because it is run from the command line.
    con.execute("SET memory_limit='3GB'; SET threads=3; SET enable_progress_bar=false")
    try:
        # gcd_km=None means ALL sector lengths (19 August 2026): the dashboard's fleet
        # picker runs before a route is resolved, so it has no distance, and until now
        # that sent it to the hand table, which missed AF's A220s and SAS's CRJ900s in
        # one evening. The whole observed fleet is the right picker answer; the engine
        # re-checks range against the actual sector when the run is made.
        if gcd_km:
            lo, hi = gcd_km * (1 - band), gcd_km * (1 + band)
            rows = con.execute("""
              SELECT aircraft_code, any_value(aircraft_name) nm, count(*) ops
              FROM oag
              WHERE service_type='J' AND week LIKE ? AND try_cast(stops AS INT)=0
                AND carrier = ? AND try_cast(gcd_km AS DOUBLE) BETWEEN ? AND ?
              GROUP BY 1 HAVING count(*) >= ? ORDER BY ops DESC
            """, [period, carrier.strip().upper(), lo, hi, min_ops]).fetchall()
        else:
            rows = con.execute("""
              SELECT aircraft_code, any_value(aircraft_name) nm, count(*) ops
              FROM oag
              WHERE service_type='J' AND week LIKE ? AND try_cast(stops AS INT)=0
                AND carrier = ?
              GROUP BY 1 HAVING count(*) >= ? ORDER BY ops DESC
            """, [period, carrier.strip().upper(), min_ops]).fetchall()
    finally:
        con.close()
    keys, unmapped, sectors = [], [], 0
    for row in rows:
        code, nm, ops = row[0], row[1], row[2]
        sectors += int(ops)
        k = to_aircraft_key(code)
        if k is None:
            unmapped.append("%s (%s)" % (code, (nm or "").strip()))
        elif k not in keys:
            keys.append(k)
    return keys, unmapped, sectors


def config_for(carrier, gcd_km, period="2025-%", band=0.25, min_ops=6):
    """{aircraft key: (total seats, premium seats)} as THIS carrier configures the type on sectors of
    comparable length. The generic table in aircraft_economics holds one configuration per type, and
    an airline configures a type to its own product: measured 10 August 2026, China Airlines and
    Starlux fly the A350-900 at 306 seats against the table's 336, EVA the 787-9 at 278 against 320,
    and the 777-300ER is 333 at EVA and 358 at China Airlines against 380. Sizing a schedule on the
    generic number overstates the capacity by 8 to 13% on these carriers."""
    db = _oag()
    if not db or not carrier or not gcd_km:
        return {}
    lo, hi = gcd_km * (1 - band), gcd_km * (1 + band)
    con = duckdb.connect(db, read_only=True)
    con.execute("SET memory_limit='3GB'; SET threads=3; SET enable_progress_bar=false")
    try:
        rows = con.execute("""
          SELECT aircraft_code,
                 median(try_cast(seats_total AS DOUBLE)) seats,
                 median(try_cast(business_seats AS DOUBLE) + try_cast(first_seats AS DOUBLE)) prem,
                 count(*) ops
          FROM oag
          WHERE service_type='J' AND week LIKE ? AND try_cast(stops AS INT)=0
            AND carrier = ? AND try_cast(gcd_km AS DOUBLE) BETWEEN ? AND ?
          GROUP BY 1 HAVING count(*) >= ? ORDER BY ops DESC
        """, [period, carrier.strip().upper(), lo, hi, min_ops]).fetchall()
    finally:
        con.close()
    out = {}
    for code, seats, prem, _ops in rows:
        k = to_aircraft_key(code)
        if k and k not in out and seats:
            out[k] = (int(seats), int(prem or 0))
    return out


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


def frequency_frame(a, b, carriers=None, period="2025-%", band=0.25, con=None):
    """How often a carrier actually opens and runs a route of this length, per direction per week.

    The third side of the frame. Aircraft and seats say what an airline can put on the route; this
    says how often it flies it, and it is the same kind of observable. A carrier that runs its
    comparable long-haul at four weekly does not open a new one at daily, and the schedule says so.

    Returned per carrier: the median, the quartiles and the range across its routes of comparable
    length, so the caller can frame a low, central and high case rather than pick one.
    """
    close = False
    if con is None:
        db = _oag()
        if not db:
            sys.exit("no OAG store found.")
        con = duckdb.connect(db, read_only=True)
        con.execute("SET memory_limit='3GB'; SET threads=3")
        close = True
    try:
        gcd, _ = (None, None)
        import airportsdata
        import math
        ap_ = airportsdata.load("IATA")
        if a in ap_ and b in ap_:
            la1, lo1 = math.radians(ap_[a]["lat"]), math.radians(ap_[a]["lon"])
            la2, lo2 = math.radians(ap_[b]["lat"]), math.radians(ap_[b]["lon"])
            h = (math.sin((la2 - la1) / 2) ** 2
                 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
            gcd = 2 * 6371 * math.asin(math.sqrt(h))
        if not gcd:
            return {}
        lo, hi = gcd * (1 - band), gcd * (1 + band)
        where = ""
        params = [period, lo, hi]
        if carriers:
            where = " AND carrier IN (%s)" % ",".join("?" for _ in carriers)
            params += list(carriers)
        # Weekly frequency per direction on a route-month. days_of_op is a seven-character mask so
        # its digit count is flights per week, but the store holds the SAME schedule record once per
        # region label: UA SFO-TPE in June 2025 is sixty rows carrying two distinct flight numbers,
        # both daily. Summing the mask across rows returned 420 weekly frequencies for United, which
        # is what sent me back to look at a single route-month rather than trust the aggregate.
        # Deduped to one figure per flight number, then summed, which gives the honest fourteen.
        rows = con.execute("""
          WITH d AS (
            SELECT carrier, dep_airport || '-' || arr_airport rt, substr(week,1,7) mon, flight_no,
                   max(length(replace(coalesce(days_of_op,''), '.', ''))) dop
            FROM oag
            WHERE service_type='J' AND week LIKE ? AND try_cast(stops AS INT)=0
              AND try_cast(gcd_km AS DOUBLE) BETWEEN ? AND ? %s
            GROUP BY 1,2,3,4),
          f AS (SELECT carrier, rt, mon, sum(dop) wk FROM d GROUP BY 1,2,3 HAVING sum(dop) > 0)
          SELECT carrier, count(DISTINCT rt) routes,
                 quantile_cont(wk, 0.25) q1, median(wk) med, quantile_cont(wk, 0.75) q3,
                 min(wk) lo, max(wk) hi
          FROM f GROUP BY 1
        """ % where, params).fetchall()
        return {r[0]: {"routes": int(r[1]), "q1": round(float(r[2]), 1),
                       "median": round(float(r[3]), 1), "q3": round(float(r[4]), 1),
                       "min": round(float(r[5]), 1), "max": round(float(r[6]), 1)}
                for r in rows}
    finally:
        if close:
            con.close()


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
    fq = frequency_frame(a, b, carriers=order[:x.max_carriers], period=x.period, band=x.band)
    if fq:
        print("\n  weekly frequency per direction on routes of comparable length")
        print("    %-6s %8s %8s %8s %8s %8s" % ("", "low q1", "median", "high q3", "min", "max"))
        for car in order[:x.max_carriers]:
            d = fq.get(car)
            if d:
                print("    %-6s %8.1f %8.1f %8.1f %8.1f %8.1f   across %d routes"
                      % (car, d["q1"], d["median"], d["q3"], d["min"], d["max"], d["routes"]))


if __name__ == "__main__":
    main()
