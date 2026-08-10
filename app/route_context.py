#!/usr/bin/env python3
r"""Assemble the twenty-one BT2 inputs for a live route. One place, calling the engine for its own.

    import route_context as RC
    d = RC.build("SJC", "TPE", carrier="BR", aircraft_seats=333, freq=7, months=12,
                 launch_mon=6, engine_payload=fc)
    import bt2_forecast as BF; BF.forecast(d)

John's ruling of 9 August: everything is calculated in one place. So anything the QSI engine already
works out is READ FROM THE ENGINE and not recomputed here. Duplicating capture or connection logic
in a second module is how two copies of a tool drift apart, which this estate has already paid for.

WHERE EACH INPUT COMES FROM, and every one is knowable before the route flies.

  from the CALLER      the schedule being tested: carrier, seats per departure, weekly frequency,
                       months operating, launch month. capacity_frame.py enumerates the credible
                       options so the caller picks from evidence rather than inventing one
  from the ENGINE      capa, the QSI capture at that frequency, read from qsi_share
  from SABRE           base_mkt, the measured O&D on the pair in the latest full year, and
                       mkt_growth, that year over the one before
  from OAG             the carrier's departing seats at each endpoint and the airport totals, which
                       are the base-strength features, plus the sister-airport flag from Sabre
  computed             gcd, dom, gauge, ncar, seats_ly

THE ONE GAP, and it is smaller than I first wrote it. BT2 needs qcx, the connection-competition
strength, and legs_n, the schedule density at the endpoints. bt2_capture computes both by calling
the engine's connection builder itself.

I ORIGINALLY RECORDED THAT THE LIVE ENGINE DOES NOT USE THE CONNECTION BUILDER. THAT WAS WRONG and
the correction matters, because a QSI forecast that did not build connections would not be a QSI
forecast at all. route_forecast.forecast calls qsi_capture_share and dest_metro_share; both call
route_qsi.airport_qsi_to_dest; that imports build_connections and load_mct_data from
connection_builder and runs them with minimum connect times, alliances and low-cost handling. The
capture share at the centre of every Meridian forecast is computed from built and scored
connections. The mistake was searching route_forecast.py for the string and concluding from its
absence, one level above where the call actually happens.

What is true is narrower: the engine RETURNS neither aggregate. qcx and legs_n are summaries over a
connection set the engine already builds and then discards. So closing the gap is not new
computation, it is returning two numbers from work already done.

    TO CLOSE IT: route_qsi.airport_qsi_to_dest should return the connection-competition components
    and the leg count alongside the QSI it already returns, and route_forecast should pass them
    through in its payload beside qsi_share.

Until then build() FAILS CLOSED without them rather than substituting a neutral value, because a
neutral value here is a wrong forecast that looks right.

Avia Solutions Limited. All rights reserved.
"""
import json
import math
import os

import duckdb

WEEKS = 52.0


def _store(name):
    p = os.environ.get("AVIA_%s_DUCKDB" % name.upper())
    if p and os.path.exists(p):
        return p
    for r in [os.environ.get("AVIA_LOCAL_CACHE"),
              os.path.join("E:" + os.sep, "Avia"), os.path.join("C:" + os.sep, "Avia")]:
        if r and os.path.exists(os.path.join(r, "%s.duckdb" % name)):
            return os.path.join(r, "%s.duckdb" % name)
    return None


def _lcc_set():
    try:
        import connection_builder as CB
        return set(CB.DEFAULT_LCC_LIST)
    except Exception:                                       # noqa: BLE001
        return set()


def market(a, b, year=None, con=None):
    """Sabre O&D on the unordered pair, both directions, and the growth on the year before.

    This is BT2's base_mkt and it is NOT the engine's natural_market: the engine grosses its market
    up for off-GDS coverage and widens it to the catchment, while BT2 was trained on the raw pair
    total. Feeding the engine's number in would move every forecast by the coverage factor.
    """
    db = _store("sabre")
    if not db:
        return None, None, "no Sabre store found"
    close = con is None
    con = con or duckdb.connect(db, read_only=True)
    try:
        con.execute("SET memory_limit='3GB'; SET threads=3")
        if year is None:
            year = con.execute("SELECT max(source_year) FROM sabre").fetchone()[0]
        rows = dict(con.execute("""
          SELECT source_year, sum(passengers) FROM sabre
          WHERE source_year IN (?, ?)
            AND least(origin_airport, destination_airport) = ?
            AND greatest(origin_airport, destination_airport) = ?
          GROUP BY 1""", [year, year - 1, min(a, b), max(a, b)]).fetchall())
        cur = float(rows.get(year) or 0)
        prev = float(rows.get(year - 1) or 0)
        if cur <= 0:
            return None, None, ("no Sabre traffic between %s and %s in %s, so base_mkt cannot be "
                                "measured. BT2 was not trained on markets of zero." % (a, b, year))
        growth = (cur / prev) if prev >= 500 else 1.0
        return cur, growth, None
    finally:
        if close:
            con.close()


def base_strength(carrier, a, b, month, con=None):
    """The carrier's departing seats at each endpoint in a month, and every carrier's total there.

    Same construction as bt2_base: region duplicates deduped by max, because the store holds one row
    per region label and summing them counts the same service several times.
    """
    db = _store("oag")
    if not db:
        return None
    close = con is None
    con = con or duckdb.connect(db, read_only=True)
    try:
        con.execute("SET memory_limit='3GB'; SET threads=3")
        rows = con.execute("""
          SELECT dep_airport, carrier, max(cnt) s FROM (
            SELECT dep_airport, carrier, region, sum(try_cast(seats_total AS BIGINT)) cnt
            FROM oag WHERE service_type='J' AND week = ? AND dep_airport IN (?, ?)
            GROUP BY 1,2,3) GROUP BY 1,2""", [month, a, b]).fetchall()
        own = {a: 0.0, b: 0.0}
        tot = {a: 0.0, b: 0.0}
        for ap_, car, s in rows:
            tot[ap_] = tot.get(ap_, 0.0) + float(s or 0)
            if car == carrier:
                own[ap_] = float(s or 0)
        return {"base_seats_a": own[a], "base_seats_b": own[b],
                "airport_seats_a": tot[a], "airport_seats_b": tot[b]}
    finally:
        if close:
            con.close()


def sister_flag(a, b, year, con=None):
    """Whether the metro pair already had established nonstop service, over 1,500 passengers, in the
    year before. bt2_metro's own definition, reused rather than restated."""
    db = _store("sabre")
    if not db:
        return None
    close = con is None
    con = con or duckdb.connect(db, read_only=True)
    try:
        import airportsdata
        M = airportsdata.load("IATA")
        ca, cb = M.get(a, {}), M.get(b, {})
        if not ca or not cb:
            return None
        con.execute("SET memory_limit='3GB'; SET threads=3")
        v = con.execute("""
          SELECT sum(passengers) FROM sabre
          WHERE itinerary='NON-STOP' AND source_year = ?
            AND origin_airport <> destination_airport
            AND origin_airport IN (SELECT DISTINCT origin_airport FROM sabre WHERE 1=0)
        """, [year - 1]).fetchone()
        # The metro test needs the city of every airport, which airportsdata gives directly, so the
        # pair is resolved in Python rather than by a join the store cannot do.
        rows = con.execute("""
          SELECT origin_airport, destination_airport, sum(passengers) FROM sabre
          WHERE itinerary='NON-STOP' AND source_year = ? AND origin_airport <> destination_airport
          GROUP BY 1,2 HAVING sum(passengers) > 1500""", [year - 1]).fetchall()
        key = tuple(sorted(["%s|%s" % (ca.get("city"), ca.get("country")),
                            "%s|%s" % (cb.get("city"), cb.get("country"))]))
        for o, d, _p in rows:
            mo, md = M.get(o, {}), M.get(d, {})
            if not mo or not md:
                continue
            k = tuple(sorted(["%s|%s" % (mo.get("city"), mo.get("country")),
                              "%s|%s" % (md.get("city"), md.get("country"))]))
            if k == key and {o, d} != {a, b}:
                return True
        return False
    finally:
        if close:
            con.close()


def build(a, b, carrier, aircraft_seats, freq, months=12, launch_mon=6, year=None,
          engine_payload=None, qcx=None, legs_n=None, ncar=1, pre_month=None):
    """The BT2 route dict, or a dict with ok=False naming exactly what is missing."""
    a, b, carrier = a.upper(), b.upper(), carrier.upper()
    miss = []

    capa = None
    if engine_payload is not None:
        capa = engine_payload.get("qsi_share")
        if legs_n is None:
            legs_n = engine_payload.get("legs_n")
        if qcx is None:
            # The three connection-type sums come from the engine, computed over the connection set
            # it already builds. The weighting is BT2's definition, so it is applied HERE and not in
            # the engine: online counts in full, alliance at three quarters, interline at a quarter,
            # exactly as bt2_lib combines the capture components.
            so = engine_payload.get("s_online")
            sa = engine_payload.get("s_alliance")
            si = engine_payload.get("s_interline")
            if so is not None or sa is not None or si is not None:
                qcx = float(so or 0.0) + 0.75 * float(sa or 0.0) + 0.25 * float(si or 0.0)
    if capa is None:
        miss.append("capa: pass the engine payload, whose qsi_share is the capture BT2 needs")
    if qcx is None:
        miss.append("qcx: the engine payload carries no s_online/s_alliance/s_interline. Call route_forecast.forecast, which now returns them from the connection set it builds.")
    if legs_n is None:
        miss.append("legs_n: the engine payload carries none. Call route_forecast.forecast, which now returns it.")

    bm, growth, err = market(a, b, year)
    if err:
        miss.append(err)
    if miss:
        return {"ok": False, "missing": miss}

    import airportsdata
    M = airportsdata.load("IATA")
    if a not in M or b not in M:
        return {"ok": False, "missing": ["%s or %s is not in the airport table" % (a, b)]}
    la1, lo1 = math.radians(M[a]["lat"]), math.radians(M[a]["lon"])
    la2, lo2 = math.radians(M[b]["lat"]), math.radians(M[b]["lon"])
    h = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    gcd = 2 * 6371 * math.asin(math.sqrt(h))

    yr = year or 0
    if not pre_month:
        import datetime
        y = yr or datetime.date.today().year
        pre_month = "%04d-%02d" % (y, max(1, min(12, int(launch_mon))))
    bs = base_strength(carrier, a, b, pre_month) or {}
    sf = sister_flag(a, b, (yr or 0) + 1) if yr else None

    # Seats offered in the forecast window, both directions, on the same construction as the
    # back-test: seats per departure times weekly frequency times both directions times the share
    # of the year operated.
    seats_ly = float(aircraft_seats) * float(freq) * 2.0 * WEEKS * (float(months) / 12.0)

    return {"ok": True,
            "seats_ly": seats_ly, "base_mkt": bm, "capa": float(capa), "freq": float(freq),
            "legs_n": int(legs_n), "months": int(months), "gcd": gcd,
            "typ": "LCC" if carrier in _lcc_set() else "FSC",
            "dom": M[a].get("country") == M[b].get("country"),
            "gauge": float(aircraft_seats), "ncar": int(ncar),
            "launch_mon": int(launch_mon), "qcx": float(qcx), "mkt_growth": float(growth),
            "carrier": carrier,
            "base_seats_a": bs.get("base_seats_a"), "base_seats_b": bs.get("base_seats_b"),
            "airport_seats_a": bs.get("airport_seats_a"), "airport_seats_b": bs.get("airport_seats_b"),
            "sister_flag": bool(sf),
            "_provenance": {"base_mkt_year": year, "pre_month": pre_month,
                            "capa_from": "engine qsi_share",
                            "sister_flag_resolved": sf is not None}}


if __name__ == "__main__":
    import sys
    a, b, car = (sys.argv[1:4] + ["SJC", "TPE", "BR"])[:3]
    print(json.dumps(build(a, b, car, aircraft_seats=333, freq=7,
                           engine_payload={"qsi_share": 0.42, "qcx": 2.3, "legs_n": 1800},
                           year=2024, launch_mon=6), indent=2, default=str))
