#!/usr/bin/env python3
r"""Assemble the twenty-one BT2 inputs for a live route. One place, calling the engine for its own.

    import route_context as RC
    d = RC.build("SJC", "TPE", carrier="BR", aircraft_seats=333, freq=7, months=12,
                 launch_mon=1, engine_payload=fc)      # months = 13 - launch_mon, always
    import bt2_forecast as BF; BF.forecast(d)

John's ruling of 9 August: everything is calculated in one place. So anything the QSI engine already
works out is READ FROM THE ENGINE and not recomputed here. Duplicating capture or connection logic
in a second module is how two copies of a tool drift apart, which this estate has already paid for.

WHERE EACH INPUT COMES FROM, and every one is knowable before the route flies.

  from the CALLER      the schedule being tested: carrier, seats per departure, weekly frequency,
                       months operating, launch month. capacity_frame.py enumerates the credible
                       options so the caller picks from evidence rather than inventing one
  from bt2_capture_core capa, qcx and legs_n, built by the SAME code the training chain used. These
                       three are NOT read from the engine. They were until 12 August 2026 and it was
                       wrong: see capture_inputs below for the measurement
  from SABRE           base_mkt, the measured O&D on the pair in the latest full year, and
                       mkt_growth, that year over the one before
  from OAG             the carrier's departing seats at each endpoint and the airport totals, which
                       are the base-strength features, plus the sister-airport flag from Sabre
  computed             gcd, dom, gauge, ncar, seats_ly

THE RULING HAS A LIMIT, AND 12 AUGUST 2026 FOUND IT. "Read it from the engine" is right wherever the
engine computes the same quantity. It is wrong wherever the engine computes a quantity that merely
shares a name, and capa was exactly that: the model was trained on a nonstop-versus-connecting share
of the pair's own service and the engine's qsi_share is the share of the catchment's traffic won at
the origin airport. Reading it from the engine fed the model a number below the tenth percentile of
its training on essentially every route, in silence. So capa, qcx and legs_n are now built from
app/bt2_capture_core, which the training chain imports too. One implementation, not one source.

WHAT FOLLOWS IS THE HISTORY OF THAT MISTAKE, kept because the reasoning is still instructive.

BT2 needs qcx, the connection-competition strength, and legs_n, the schedule density at the
endpoints. bt2_capture computes both by calling the engine's connection builder itself.

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
import re

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


_MONTH_LABEL = re.compile(r"^\d{4}-\d{2}$")


def capture_inputs(a, b, freq, gcd_km, pre_month, con=None):
    """capa, qcx and legs_n, built by the SAME code the training chain used.

    THIS IS THE FAULT OF 12 AUGUST 2026 CLOSED. capa was set to the engine's qsi_share, which is the
    share of the catchment's traffic to the destination won at the origin airport and reads 0.059 at
    daily on SJC-TPE. The model was trained on a nonstop-versus-connecting share of the pair's own
    service, median 0.9168 and tenth percentile 0.4896. Every live route would have entered the model
    below the tenth percentile of training, silently, and the published accuracy would have described
    nothing a client is shown. qcx and legs_n were wrong in the same way and for the same reason.

    All three now come from app/bt2_capture_core, which bt2/bt2_capture.py also imports, so the two
    chains cannot build them differently again.

    THE MONTH LABEL IS NOT NEGOTIABLE. Training read a MONTH, "2025-06", and took the schedule rows
    covering the 15th to the 21st. The engine resolves a single-week label such as "2026-05-25", and
    handing one of those to load_legs would build the date window "2026-05-25-15", which is not a
    date. It is refused by name rather than allowed to return nothing, because a route with no legs
    reads as a route with no competition and would score a capa of 1.0.
    """
    import bt2_capture_core as CORE
    if not _MONTH_LABEL.match(str(pre_month or "")):
        return None, ("pre_month must be a MONTH label such as '2025-06'. Got %r. The training "
                      "chain read a month and took the week of the 15th to the 21st; a single-week "
                      "OAG label is a different construction and cannot be substituted." % pre_month)
    db = _store("oag")
    if not db:
        return None, "no OAG store found, so capa, qcx and legs_n cannot be built"
    close = con is None
    con = con or duckdb.connect(db, read_only=True)
    try:
        con.execute("SET memory_limit='3GB'; SET threads=3")
        legs = CORE.load_legs(con, pre_month, {a, b})
        if not legs:
            return None, ("no OAG legs touch %s or %s in %s, so the connection competition cannot "
                          "be measured. An empty leg set is not a route without competition."
                          % (a, b, pre_month))
        import connection_builder as CB
        import schedule_chain as SC
        alliances = SC.alliances_from_legs(legs) or CB.load_alliance_data()
        lcc = SC.lcc_from_legs(legs) or CB.DEFAULT_LCC_LIST
        coords = SC.load_airport_coords()
        # THE MCT MASTER IS OFF, because capture_L.csv was built without it and the live path has to
        # reproduce training. Measured on forty routes of cohort 2018: without the master
        # thirty-nine agree to the training file's write precision, with it twenty stop agreeing and
        # every one reads high. See bt2_capture_core.load_mct for the figures and for the conclusion
        # I withdrew. AVIA_BT2_MCT=1 turns it on for both chains, and turning it on means rebuilding
        # the cohorts before any accuracy figure is quoted.
        mct, mct_src = CORE.load_mct()
        block = CORE.block_minutes(gcd_km)
        comp = CORE.components(legs, a, b, alliances, mct, lcc, coords, block)
        return {"capa": CORE.capa_from_components(comp, block, float(freq)),
                "qcx": CORE.qcx_feature_from_components(comp),
                "legs_n": len(legs),
                "block": block, "pre_month": pre_month,
                "components": [list(c) for c in comp],
                "mct_loaded": bool(mct), "mct_source": mct_src}, None
    finally:
        if close:
            con.close()


def build(a, b, carrier, aircraft_seats, freq, months=12, launch_mon=1, year=None,
          engine_payload=None, qcx=None, legs_n=None, capa=None, ncar=1, pre_month=None):
    """The BT2 route dict, or a dict with ok=False naming exactly what is missing.

    engine_payload is still accepted and is still read for anything the engine works out that BT2
    needs, but capa, qcx and legs_n are NO LONGER TAKEN FROM IT. They are the three the model is most
    sensitive to and the three the engine computes on a different definition; see capture_inputs.
    Passing capa, qcx or legs_n explicitly overrides the computation and is for testing only.

    MONTHS AND LAUNCH_MON ARE NOT INDEPENDENT, and this defaulted to a pair that cannot exist.
    bt2_gbm.X_of feeds the model log(months) as feature six and month_num as feature thirteen. In
    training those two are PERFECTLY COLLINEAR: bt2_profile counts months from the launch month to
    year end, so months_operated = 13 - launch_month in every one of 6,810 rows. The model therefore
    learned on a one-dimensional line through a two-dimensional feature space.

    The old defaults were months=12 with launch_mon=6. That pair occurs ZERO times in training and
    cannot occur by construction: all 192 training rows carrying twelve months launched in January.
    A default call put the model off its own training manifold on every route, silently, which is
    CAPA-IS-NOT-QSI-SHARE of 12 August in a different feature.

    So the default is now launch_mon=1 with months=12, the January case, and an impossible pair is
    REFUSED BY NAME rather than accepted. That is the same treatment load_legs gives a single-week
    OAG label, and for the same reason: a quietly wrong input produces a confident wrong answer.
    """
    a, b, carrier = a.upper(), b.upper(), carrier.upper()
    miss = []

    try:
        _lm, _mo = int(launch_mon), int(months)
    except (TypeError, ValueError):
        return {"ok": False, "missing": ["months and launch_mon must be whole numbers, got %r and %r"
                                         % (months, launch_mon)]}
    if not 1 <= _lm <= 12:
        return {"ok": False, "missing": ["launch_mon must be 1 to 12, got %d" % _lm]}
    if not 1 <= _mo <= 12:
        return {"ok": False, "missing": ["months must be 1 to 12, got %d" % _mo]}
    if _mo > 13 - _lm:
        return {"ok": False, "missing": [
            "months=%d is impossible for launch_mon=%d: a route launching in month %d can operate "
            "at most %d months of its launch year, and the model is trained only on pairs where "
            "months = 13 - launch month. Use launch_mon=1 with months=12 for a full year."
            % (_mo, _lm, _lm, 13 - _lm)]}
    months, launch_mon = _mo, _lm

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

    cap_prov = {}
    if capa is None or qcx is None or legs_n is None:
        got, err = capture_inputs(a, b, freq, gcd, pre_month)
        if err:
            miss.append(err)
        else:
            capa = got["capa"] if capa is None else capa
            qcx = got["qcx"] if qcx is None else qcx
            legs_n = got["legs_n"] if legs_n is None else legs_n
            cap_prov = {k: got[k] for k in ("block", "pre_month", "components", "mct_loaded")}

    bm, growth, err = market(a, b, year)
    if err:
        miss.append(err)
    if miss:
        return {"ok": False, "missing": miss}

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
            "_provenance": dict({"base_mkt_year": year, "pre_month": pre_month,
                                 "capa_from": "bt2_capture_core, the training implementation",
                                 "sister_flag_resolved": sf is not None}, **cap_prov)}


if __name__ == "__main__":
    import sys
    a, b, car = (sys.argv[1:4] + ["SJC", "TPE", "BR"])[:3]
    # No engine payload and no overrides: capa, qcx and legs_n are built from the store by the
    # training implementation, which is the point of the file.
    # launch_mon=6 with the months default of 12 is now REFUSED, correctly: a June launch can only
    # operate seven months of its launch year. Seven is what a June launch means.
    print(json.dumps(build(a, b, car, aircraft_seats=333, freq=7, year=2024, launch_mon=6,
                           months=7, pre_month="2024-06"), indent=2, default=str))
