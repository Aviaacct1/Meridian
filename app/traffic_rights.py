#!/usr/bin/env python3
r"""Can this airline actually fly this route? Answered from precedent, not from a rights registry.

    python3 traffic_rights.py BA SJC TPE
    python3 traffic_rights.py CI SJC TPE

THE PROBLEM, John, 9 August 2026. If someone asks Meridian for BA on SJC-TPE, the tool should not
silently refuse and should not quietly answer as though it were normal. It should give the number
and say this carrier cannot fly this route, and why. Compiling every bilateral agreement in the
world is not realistic, so the question is whether the answer can be had another way.

IT CAN, AND IT DOES NOT NEED THE LAW. Every scheduled service on earth is in OAG. We do not need to
know what a treaty permits; we need to know whether anything like it is flown. Three tiers, all read
off the schedule:

  HOME       the carrier is based in the country at one end. This is third and fourth freedom, the
             ordinary case, and no question arises.
  PRECEDENT  the carrier is based in neither country, but IT already operates services between them,
             or carriers from its country do. That is a fifth-freedom operation with a live example,
             so it is possible and unusual, and the example is named.
  NO CASE    the carrier is based in neither country and NO carrier from its country operates
             between them anywhere in the world. The honest statement is that no precedent exists in
             worldwide schedules, which is the evidence-based form of "the bilateral does not allow
             this" without pretending to have read the bilateral.

WHY THE WORDING MATTERS. "No airline of this country flies between these two countries anywhere in
the world" is a fact we can show. "This is prohibited by the bilateral" is a legal claim we cannot
source, and a client who knows the sector will catch it. The first is defensible in a room; the
second is the kind of overclaim that costs an engagement.

WHAT THIS DOES NOT DO. It does not know about a treaty signed last month with no services yet
flown, and it will report a genuine new opportunity as having no precedent, which is correct and is
why the verdict is advisory rather than a block. The forecast is still produced.

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
    for r in [os.environ.get("AVIA_LOCAL_CACHE"),
              os.path.join("E:" + os.sep, "Avia"), os.path.join("C:" + os.sep, "Avia")]:
        if r and os.path.exists(os.path.join(r, "oag.duckdb")):
            return os.path.join(r, "oag.duckdb")
    return None


def check(carrier, a, b, period="2025-%", con=None):
    """Verdict for one carrier on one pair. Never blocks; returns the finding and the evidence."""
    close = False
    if con is None:
        db = _oag()
        if not db:
            return {"verdict": "UNKNOWN", "reason": "no OAG store found, so no check was made"}
        con = duckdb.connect(db, read_only=True)
        con.execute("SET memory_limit='3GB'; SET threads=3")
        close = True
    try:
        cc = dict(con.execute("""
          SELECT dep_airport, any_value(dep_country) FROM oag
          WHERE dep_airport IN (?, ?) GROUP BY 1""", [a, b]).fetchall())
        ca, cb = cc.get(a), cc.get(b)
        if not ca or not cb:
            return {"verdict": "UNKNOWN", "reason": "cannot resolve the country of %s or %s" % (a, b)}

        home = con.execute("""
          SELECT dep_country FROM oag
          WHERE carrier = ? AND service_type='J' AND week LIKE ?
            AND dep_country IS NOT NULL AND trim(dep_country) <> ''
          GROUP BY 1 ORDER BY sum(try_cast(seats_total AS DOUBLE)) DESC LIMIT 1
        """, [carrier, period]).fetchone()
        home = home[0] if home else None
        if not home:
            return {"verdict": "UNKNOWN", "carrier": carrier,
                    "reason": "%s operates no scheduled service in the period, so it has no "
                              "observable home country" % carrier}

        base = {"carrier": carrier, "home": home, "country_a": ca, "country_b": cb,
                "pair": "%s-%s" % (a, b)}
        if home in (ca, cb):
            return dict(base, verdict="HOME",
                        note="%s is based in %s, one of the two countries, so this is ordinary "
                             "third and fourth freedom flying." % (carrier, home))

        own = con.execute("""
          SELECT count(*), count(DISTINCT dep_airport || '-' || arr_airport) FROM oag
          WHERE carrier = ? AND service_type='J' AND week LIKE ? AND try_cast(stops AS INT)=0
            AND ((dep_country=? AND arr_country=?) OR (dep_country=? AND arr_country=?))
        """, [carrier, period, ca, cb, cb, ca]).fetchone()
        if own and own[0]:
            return dict(base, verdict="PRECEDENT", sectors=int(own[0]), routes=int(own[1]),
                        note="%s already operates %d sectors on %d route(s) between %s and %s, so "
                             "it holds fifth-freedom rights on this country pair today."
                             % (carrier, own[0], own[1], ca, cb))

        peers = con.execute("""
          SELECT carrier, count(*) n FROM oag
          WHERE service_type='J' AND week LIKE ? AND try_cast(stops AS INT)=0
            AND ((dep_country=? AND arr_country=?) OR (dep_country=? AND arr_country=?))
            AND carrier IN (
              SELECT carrier FROM (
                SELECT carrier, dep_country,
                       row_number() OVER (PARTITION BY carrier
                                          ORDER BY sum(try_cast(seats_total AS DOUBLE)) DESC) rn
                FROM oag WHERE service_type='J' AND week LIKE ?
                  AND dep_country IS NOT NULL AND trim(dep_country) <> ''
                GROUP BY 1,2) WHERE rn=1 AND dep_country = ?)
          GROUP BY 1 ORDER BY 2 DESC LIMIT 5
        """, [period, ca, cb, cb, ca, period, home]).fetchall()
        if peers:
            return dict(base, verdict="PRECEDENT", peers=[p[0] for p in peers],
                        note="%s does not fly between %s and %s, but %s carrier(s) %s do, so the "
                             "country pair is open to %s operators as a fifth freedom."
                             % (carrier, ca, cb, home, ", ".join(p[0] for p in peers), home))

        return dict(base, verdict="NO CASE",
                    note="No carrier based in %s operates any nonstop service between %s and %s "
                         "anywhere in the world in this period. There is no precedent in worldwide "
                         "schedules for %s flying %s-%s, which on the usual reading means the "
                         "traffic rights are not available to a %s carrier on this pair."
                         % (home, ca, cb, carrier, a, b, home))
    finally:
        if close:
            con.close()


def message(v):
    """The line a client should see, given a verdict."""
    if v["verdict"] == "HOME":
        return ""
    if v["verdict"] == "UNKNOWN":
        return "Traffic rights not checked: %s" % v.get("reason", "")
    if v["verdict"] == "PRECEDENT":
        return "UNUSUAL OPERATOR. " + v["note"] + " Treat the forecast as conditional on rights."
    return ("THEORETICAL ONLY. The forecast below is what the market would support if this service "
            "were flown. " + v["note"])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("carrier")
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--period", default="2025-%")
    x = ap.parse_args()
    v = check(x.carrier.upper(), x.a.upper(), x.b.upper(), x.period)
    print("%s on %s: %s" % (v.get("carrier", x.carrier), v.get("pair", "%s-%s" % (x.a, x.b)),
                            v["verdict"]))
    if v.get("home"):
        print("  home %s, route countries %s and %s" % (v["home"], v["country_a"], v["country_b"]))
    print("  %s" % v.get("note", v.get("reason", "")))
    m = message(v)
    if m:
        print("\n  client message:\n    %s" % m)


if __name__ == "__main__":
    main()
