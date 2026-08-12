"""Does the airline's own gauge choice improve our forecast, on the routes where we are weakest?

JOHN'S PROPOSAL, 13 August 2026. The QSI engine estimates demand from catchment, capture share and
stimulation, knowing nothing about the aircraft. Seats times a constant load factor estimates it from
the aircraft, knowing nothing about the market. Those are two independent readings of one quantity,
so where they disagree there is information, and the question is whether reconciling them beats the
engine on its own.

WHY LONG HAUL. The null control of 13 August put a featureless constant at 74.5% within +-20% on the
sector total for long-haul international FSC routes, against the model's 73.7%, while on the LOCAL
market the same constant scores 33.4%. So the aircraft tells you how many passengers will be on
board and not how many of them are flying the route rather than through it. On long haul that split
is most of the answer and it is where the connecting feed lives, which is why this runs on the local
leg rather than on the total.

THE LEFT-HAND SIDE IS captured_uncapped, the engine's local demand BEFORE the 87.5% plan cap and
containing no feed at all. Using forecast_pax instead would put the cap and the connecting feed into
a comparison that is supposed to isolate the local market.

THE CONDITION THIS RESTS ON, and it belongs on the page as much as in this docstring. Seats only
carry information when the gauge is somebody else's judgement. Every route here is one an airline
actually launched at a gauge an airline actually chose, so the condition holds by construction in the
back-test. In the live tool it holds when a client brings a proposed aircraft and FAILS when the tool
picks the gauge itself or a user sweeps frequencies, because then the seat count is our own
assumption coming back round. Any feature built on this has to know which case it is in and say so.

EVERY LEARNED PARAMETER IS LEAVE-ONE-COHORT-OUT. k, the band width and the divergence threshold are
all fitted on the other cohorts and applied to the held-out one. A rule with a free parameter chosen
on the same routes it is scored on will always look good and will mean nothing.

    py -3.12 seats_crosscheck.py --arm ..\app\backtest_qsifeed_11Aug2026.csv

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from bt2_paths import BT2, find_app                                     # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description="Engine against seats x k on the local leg.")
    p.add_argument("--arm", required=True, help="a backtest.py arm CSV")
    p.add_argument("--cohorts", default=os.environ.get("AVIA_BT2_COHORTS",
                                                       "2016,2017,2018,2019,2024,2025"))
    p.add_argument("--segment", choices=("longhaul", "all"), default="longhaul",
                   help="longhaul is gcd>=2500km, international, not LCC, which is bt2_claimset's "
                        "own definition and the segment the engine is weakest on")
    p.add_argument("--min-pax", type=float, default=100.0)
    p.add_argument("--out", default=None)
    return p.parse_args()


def within(r, tol=0.20):
    return r is not None and abs(r - 1.0) <= tol


def _f(d, k):
    try:
        return float(d.get(k) or 0)
    except (TypeError, ValueError):
        return 0.0


def _score(name, pairs, note=""):
    """pairs is a list of (forecast, actual)."""
    r = [f / a for f, a in pairs if f and f > 0 and a and a > 0]
    if not r:
        print("   %-34s no scoreable routes" % name)
        return
    print("   %-34s %5.1f%%  %5.1f%%   median %5.3f  n=%d %s"
          % (name, 100.0 * sum(1 for x in r if within(x)) / len(r),
             100.0 * sum(1 for x in r if within(x, 0.10)) / len(r),
             statistics.median(r), len(r), note))


def main():
    a = parse_args()
    cohorts = [int(c) for c in a.cohorts.split(",") if c.strip()]
    if not os.path.exists(a.arm):
        sys.exit("arm CSV not found: %r" % a.arm)

    sys.path.insert(0, find_app())
    import connection_builder as CB
    lcc = set(CB.DEFAULT_LCC_LIST)

    # SEATS COME FROM launch_profile, NOT FROM THE ARM. LF-MEASUREMENT-VOID established that the
    # arm's capacity column is annualised at 52 weeks in both directions from a schedule snapshot,
    # so load factors built on it are not load factors. seats_ly is seats actually operated over the
    # months operated, and it is the denominator that produced the 0.783.
    prof = {}
    for L in cohorts:
        p = os.path.join(BT2, "launch_profile_%d.csv" % L)
        if not os.path.exists(p):
            continue
        with open(p, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                prof[(r["a"], r["b"], L)] = r

    with open(a.arm, newline="", encoding="utf-8") as f:
        arm = list(csv.DictReader(f))

    rows, miss = [], 0
    for r in arm:
        dep, arr = (r.get("dep") or "").strip(), (r.get("arr") or "").strip()
        try:
            L = int(float(r.get("year")))
        except (TypeError, ValueError):
            continue
        pr = prof.get((min(dep, arr), max(dep, arr), L))
        if not pr:
            miss += 1
            continue
        # SEATS MUST BE ANNUALISED AND THE FIRST RUN OF THIS SCRIPT DID NOT DO IT. seats_ly is the
        # seats operated in the LAUNCH year over the MONTHS OPERATED; the arm's outturn is the
        # GRADED year, L+1, a full twelve months. Dividing one by the other varies by a factor of
        # six with nothing but the launch month, and it inflated the spread enough that seats x k on
        # the sector total scored 21.1% here against the 74.5% the null control gave for the same
        # segment on a matched basis. months_operated was in launch_profile the whole time.
        _m = float(pr.get("months_operated") or 0)
        seats = float(pr.get("seats_ly") or 0)
        if _m <= 0:
            continue
        seats = seats * 12.0 / _m
        gcd = float(pr.get("gcd_km") or 0)
        dom = (pr.get("ctry_a") == pr.get("ctry_b") and pr.get("ctry_a") != "")
        typ = "LCC" if (pr.get("carrier") in lcc or pr.get("oag_carrier") in lcc) else "FSC"
        if a.segment == "longhaul" and not (gcd >= 2500 and not dom and typ != "LCC"):
            continue
        p2p_out = _f(r, "p2p_outturn")
        eng = _f(r, "captured_uncapped")
        if seats <= 0 or p2p_out < a.min_pax or eng <= 0:
            continue
        rows.append({"route": r.get("route"), "cohort": L, "seats": seats, "gcd": gcd,
                     "months": _m, "engine": eng, "actual": p2p_out,
                     "sector": _f(r, "outturn_pax")})

    print("arm %s: %d rows, %d without a launch_profile match" % (os.path.basename(a.arm),
                                                                 len(arm), miss))
    print("segment %s: %d routes scoreable" % (a.segment, len(rows)))
    if rows:
        mm = sorted(r["months"] for r in rows)
        print("months operated in the launch year: median %.0f, p10 %.0f, p90 %.0f. Seats are "
              "annualised by this before any division." % (mm[len(mm) // 2],
                                                           mm[int(0.1 * len(mm))],
                                                           mm[int(0.9 * len(mm))]))
    print()
    if len(rows) < 100:
        print("FEWER THAN 100 ROUTES. A threshold or a band fitted on this many is not a result.")
    if not rows:
        return

    print("   %-34s %6s %6s   %-13s" % ("", "+-20%", "+-10%", ""))

    # THE BASELINE and the two single estimators.
    _score("1 engine alone, captured_uncapped", [(r["engine"], r["actual"]) for r in rows])

    # k is the LOCAL load factor here, actual over seats, learned leave one cohort out.
    ks = {}
    for L in cohorts:
        tr = [r for r in rows if r["cohort"] != L]
        if tr:
            ks[L] = statistics.median(r["actual"] / r["seats"] for r in tr)
    if ks:
        print("\n   k learned per held-out cohort: %s"
              % ", ".join("%s %.4f" % (L, v) for L, v in sorted(ks.items())))
    _score("2 seats x k alone", [(r["seats"] * ks.get(r["cohort"], 0), r["actual"]) for r in rows])

    # THE RECONCILIATIONS. Each takes the engine and moves it towards seats x k by a different rule.
    _score("3 geometric mean of the two",
           [(math.sqrt(max(r["engine"], 1e-9) * max(r["seats"] * ks.get(r["cohort"], 0), 1e-9)),
             r["actual"]) for r in rows])

    # 4 CLAMP: the engine, held inside a band around seats x k. The band is learned leave one cohort
    # out as the interquartile spread of log(engine / seats x k) on the other cohorts, so it is the
    # observed disagreement between the two estimators rather than a number chosen to look good.
    for L in cohorts:
        tr = [r for r in rows if r["cohort"] != L and ks.get(r["cohort"])]
        if not tr:
            continue
        d = sorted(math.log(r["engine"] / (r["seats"] * ks[r["cohort"]])) for r in tr)
        lo, hi = d[len(d) // 4], d[3 * len(d) // 4]
        for r in [x for x in rows if x["cohort"] == L]:
            r["band"] = (lo, hi)
    cl = []
    for r in rows:
        k = ks.get(r["cohort"])
        if not k or "band" not in r:
            continue
        ref = r["seats"] * k
        e = math.log(r["engine"] / ref)
        cl.append((ref * math.exp(min(max(e, r["band"][0]), r["band"][1])), r["actual"]))
    _score("4 engine clamped into the band", cl, "band = IQR of log disagreement")

    # 5 SWITCH: take seats x k only where the two diverge beyond the learned band, engine otherwise.
    sw = []
    for r in rows:
        k = ks.get(r["cohort"])
        if not k or "band" not in r:
            continue
        ref = r["seats"] * k
        e = math.log(r["engine"] / ref)
        sw.append((ref if (e < r["band"][0] or e > r["band"][1]) else r["engine"], r["actual"]))
    _score("5 switch to seats x k when outside", sw)

    # HOW OFTEN DO THEY DISAGREE, and by how much. The rules above are only worth anything if the
    # disagreement is large, and its size is the thing to report whatever the scores say.
    dis = sorted(r["engine"] / (r["seats"] * ks[r["cohort"]])
                 for r in rows if ks.get(r["cohort"]))
    if dis:
        def q(p):
            return dis[min(int(p * (len(dis) - 1) + 0.5), len(dis) - 1)]
        print("\n   ENGINE OVER SEATS x k: median %.3f, IQR %.3f to %.3f, p10 %.3f, p90 %.3f"
              % (statistics.median(dis), q(0.25), q(0.75), q(0.10), q(0.90)))
        print("   A median far from 1.0 means the two estimators disagree SYSTEMATICALLY, which is a")
        print("   level difference and not information. Information is in the spread around it.")

    # AND THE SAME CONSTANT ON THE SECTOR TOTAL, which is the comparison that motivated the question.
    sk = {}
    for L in cohorts:
        tr = [r for r in rows if r["cohort"] != L and r["sector"] > 0]
        if tr:
            sk[L] = statistics.median(r["sector"] / r["seats"] for r in tr)
    if sk:
        print("\n   FOR CONTRAST, the same routes graded on the SECTOR total")
        _score("  seats x k, sector target",
               [(r["seats"] * sk.get(r["cohort"], 0), r["sector"]) for r in rows if r["sector"] > 0])
        print("   If this is far above every local figure above, the aircraft predicts how many")
        print("   passengers are ON BOARD and not how many are flying the route, which is the")
        print("   split the client is actually buying and the one the feed lives in.")

    if a.out and rows:
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["route", "cohort", "gcd_km", "seats_ly", "engine_local", "seats_x_k",
                        "p2p_outturn", "sector_outturn", "engine_over_ref"])
            for r in rows:
                k = ks.get(r["cohort"]) or 0
                ref = r["seats"] * k
                w.writerow([r["route"], r["cohort"], round(r["gcd"]), round(r["seats"]),
                            round(r["engine"]), round(ref), round(r["actual"]),
                            round(r["sector"]), round(r["engine"] / ref, 4) if ref else ""])
        print("\nwrote %s" % a.out)


if __name__ == "__main__":
    main()
