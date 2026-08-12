"""The three quantities the calibrated model could be graded against, one per training pair.

WHY. Q1-ANSWERED-NO established that the engine's p2p_carried is not launch_pax: four
transformations sit between them and on the frozen SJC-TPE case the two differ by a factor of 1.757.
So the published claim describes a quantity no client is shown, and the question John asked is what
each candidate basis does to the claim set rather than which one sounds right.

THE THREE TARGETS, all measured on the SAME pair in the SAME launch year, so only the definition
moves:

  nonstop      sum(passengers) WHERE itinerary = 'NON-STOP'. bt2_discover's launch_pax, which is
               what the model is trained on today and what every published figure describes.

  p2p_outturn  sum(passengers) WHERE connecting_airport1 IS NULL OR TRIM(...) = ''. backtest.py's
               own local definition, and the denominator the pin scores fc_over_p2p against. It
               ought to equal the nonstop figure and NOBODY HAS CHECKED, which is why it is here as
               a target in its own right rather than assumed away.

  sector       the leg-adjacency total: every itinerary in which the two airports are consecutive,
               counted once per itinerary. backtest.py's sector_traffic, which is the whole sector
               a client is shown, P2P and connecting feed together.

THE CONTROL COMES FIRST. launch_pax is recomputed here with bt2_discover's own filter and compared
against the value discovery already wrote. If the two disagree the pipeline is wrong and the two new
targets cannot be trusted either, so the check is reported before anything else and a material
disagreement stops the run.

WHAT THIS DOES NOT DO. It does not refit anything and it does not touch the model. It writes
alt_targets_L.csv per cohort; bt2_lib reads it under AVIA_BT2_TARGET and everything downstream
refits itself.

    py -3.12 build_alt_targets.py --sabre E:\Avia\sabre.duckdb

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from bt2_paths import BT2, SABRE                                        # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description="Per-pair grading targets at the launch year.")
    p.add_argument("--sabre", default=SABRE, help="the Sabre store")
    p.add_argument("--cohorts", default=os.environ.get("AVIA_BT2_COHORTS", "2016,2017,2018,2019,2024,2025"))
    p.add_argument("--tol", type=float, default=0.005,
                   help="fractional disagreement on the control before the run stops, default 0.5%%")
    return p.parse_args()


# bt2_discover lines 60 to 68, reproduced rather than imported: discover builds its filter inside a
# larger discovery query and lifting it out is what makes the control a control.
SQL_NONSTOP = """
SELECT least(origin_airport, destination_airport) a,
       greatest(origin_airport, destination_airport) b,
       SUM(passengers) p
FROM sabre
WHERE itinerary = 'NON-STOP' AND source_year = ?
  AND origin_airport IS NOT NULL AND destination_airport IS NOT NULL
  AND origin_airport <> destination_airport
GROUP BY 1, 2"""

# backtest.py p2p_traffic, which screens on the connecting column rather than on the itinerary label.
SQL_P2P = """
SELECT least(origin_airport, destination_airport) a,
       greatest(origin_airport, destination_airport) b,
       SUM(passengers) p
FROM sabre
WHERE source_year = ?
  AND origin_airport IS NOT NULL AND destination_airport IS NOT NULL
  AND origin_airport <> destination_airport
  AND (connecting_airport1 IS NULL OR TRIM(connecting_airport1) = '')
GROUP BY 1, 2"""

# build_preagg.SQL_SECTOR_ADJ, including the DISTINCT that counts an itinerary once per pair rather
# than once per leg occurrence. Verified against a hand-built case on 13 August: a nonstop of 100, a
# beyond of 40, a behind of 25 and an itinerary where the two airports are not consecutive returns
# 165 and excludes the fourth.
SQL_SECTOR = """
WITH r AS (
    SELECT rowid AS rid, CAST(passengers AS DOUBLE) AS pax,
           origin_airport AS o, destination_airport AS d,
           NULLIF(connecting_airport1, '') AS c1,
           NULLIF(connecting_airport2, '') AS c2,
           NULLIF(connecting_airport3, '') AS c3
    FROM sabre WHERE source_year = ?
),
legs AS (
    SELECT rid, pax, o  AS f, COALESCE(c1, d) AS t FROM r
    UNION ALL SELECT rid, pax, c1 AS f, COALESCE(c2, d) AS t FROM r WHERE c1 IS NOT NULL
    UNION ALL SELECT rid, pax, c2 AS f, COALESCE(c3, d) AS t FROM r WHERE c2 IS NOT NULL
    UNION ALL SELECT rid, pax, c3 AS f, d              AS t FROM r WHERE c3 IS NOT NULL
),
pr AS (
    SELECT DISTINCT rid, pax, LEAST(f, t) AS a, GREATEST(f, t) AS b
    FROM legs WHERE f IS NOT NULL AND t IS NOT NULL
)
SELECT a, b, SUM(pax) FROM pr GROUP BY 1, 2"""


def main():
    a = parse_args()
    cohorts = [int(c) for c in a.cohorts.split(",") if c.strip()]
    if not os.path.exists(a.sabre):
        sys.exit("Sabre store not found: %r" % a.sabre)
    import duckdb

    print("BT2 folder %s" % BT2)
    print("cohorts %s\n" % ", ".join(str(c) for c in cohorts))

    con = duckdb.connect(a.sabre, read_only=True)
    try:
        try:
            from db_registry import apply_limits
            apply_limits(con)
        except Exception:                                    # noqa: BLE001
            con.execute("SET memory_limit='8GB'")

        for L in cohorts:
            src = os.path.join(BT2, "launches_%d.csv" % L)
            if not os.path.exists(src):
                print("cohort %d: no launches_%d.csv, skipped" % (L, L))
                continue
            with open(src, newline="", encoding="utf-8") as f:
                disc = list(csv.DictReader(f))
            want = {(r["a"], r["b"]) for r in disc}
            print("cohort %d: %d pairs from launches_%d.csv" % (L, len(want), L))

            got = {}
            for name, sql in (("nonstop", SQL_NONSTOP), ("p2p", SQL_P2P), ("sector", SQL_SECTOR)):
                t0 = time.time()
                got[name] = {(x, y): float(p or 0) for x, y, p in con.execute(sql, [L]).fetchall()
                             if (x, y) in want}
                print("   %-8s %6.1fs, %d pairs matched" % (name, time.time() - t0, len(got[name])))

            # THE CONTROL. Recomputed nonstop against what discovery wrote. A disagreement means the
            # filter here is not the filter there, and then neither of the other two targets can be
            # held against the published figures.
            bad, worst = 0, (0.0, None)
            for r in disc:
                k = (r["a"], r["b"])
                had, now = float(r["launch_pax"] or 0), got["nonstop"].get(k, 0.0)
                if had <= 0:
                    continue
                d = abs(now - had) / had
                if d > a.tol:
                    bad += 1
                if d > worst[0]:
                    worst = (d, "%s-%s had %.0f now %.0f" % (k[0], k[1], had, now))
            print("   CONTROL: %d of %d pairs disagree with discovery by more than %.1f%%"
                  % (bad, len(disc), 100 * a.tol))
            if worst[1]:
                print("            worst %.2f%%: %s" % (100 * worst[0], worst[1]))
            if bad > 0.01 * max(len(disc), 1):
                sys.exit("   STOPPING. More than one pair in a hundred disagrees with discovery, so "
                         "the filter reproduced here is not the filter discovery used and the two "
                         "new targets cannot be trusted. Settle that before rerunning.")

            out = os.path.join(BT2, "alt_targets_%d.csv" % L)
            with open(out, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["a", "b", "cohort", "nonstop", "p2p_outturn", "sector"])
                for r in disc:
                    k = (r["a"], r["b"])
                    w.writerow([k[0], k[1], L,
                                round(got["nonstop"].get(k, 0.0)),
                                round(got["p2p"].get(k, 0.0)),
                                round(got["sector"].get(k, 0.0))])
            print("   wrote %s\n" % os.path.basename(out))

        # DOES THE ITINERARY LABEL AGREE WITH THE CONNECTING COLUMN? Asked across every cohort at
        # once, because it is a property of the store rather than of a sample, and because the pin
        # grades fc_over_p2p against one definition while the model trains on the other.
        tot = {"n": 0, "same": 0, "p2p_higher": 0, "ns_higher": 0}
        for L in cohorts:
            p = os.path.join(BT2, "alt_targets_%d.csv" % L)
            if not os.path.exists(p):
                continue
            with open(p, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    ns, pp = float(r["nonstop"]), float(r["p2p_outturn"])
                    if ns <= 0 and pp <= 0:
                        continue
                    tot["n"] += 1
                    if abs(pp - ns) <= 0.005 * max(ns, 1):
                        tot["same"] += 1
                    elif pp > ns:
                        tot["p2p_higher"] += 1
                    else:
                        tot["ns_higher"] += 1
        if tot["n"]:
            print("ITINERARY LABEL AGAINST THE CONNECTING COLUMN, n=%d pairs" % tot["n"])
            print("   agree to 0.5%%           %5.1f%%" % (100.0 * tot["same"] / tot["n"]))
            print("   connecting-column higher %5.1f%%" % (100.0 * tot["p2p_higher"] / tot["n"]))
            print("   NON-STOP label higher    %5.1f%%" % (100.0 * tot["ns_higher"] / tot["n"]))
            print("   If these are not the same quantity, the model trains on one and the pin")
            print("   grades fc_over_p2p against the other, and that is a basis difference nobody")
            print("   has recorded.")
    finally:
        con.close()


if __name__ == "__main__":
    main()
