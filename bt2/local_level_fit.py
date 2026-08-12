"""What multiplier does the engine's LOCAL leg need, and does cutting it by segment earn its place?

THE FINDING THIS ANSWERS. On 730 long-haul international FSC routes the engine's
captured_uncapped read a median 0.617 of actual local outturn, so it under-reads the local market
by circa 1.6x on the segment Avia pitches most often. That figure survived three basis corrections
on 13 August because it contains no seats and needs no join: both sides come from the same arm row
at the same graded year.

WHY A LEVEL RATHER THAN A RECONCILIATION. The seats cross-check tried to repair this by pulling the
engine towards the airline's own gauge. The synthetic check established that a clamp or a switch
only reaches routes wrong in the TAIL, and a median of 0.617 is a fault in the MIDDLE. A level
correction addresses the middle directly, needs no aircraft, and loses no population to a join.

    engine = captured_uncapped, the P2P forecast leg BEFORE the 87.5% plan cap and containing no
             connecting feed at all. backtest line 630 records it as the same numerator as
             fc_over_p2p, and this script checks that rather than trusting it.
    actual = p2p_outturn, pure point-to-point Sabre outturn in the graded year.

Both are the graded year, so there is no year mismatch of the kind that invalidated the cross-check
twice.

THE THREE DISCIPLINES THIS RUN IS BUILT AROUND, each one paid for earlier in the programme.

  CONDITIONAL, NOT MARGINAL. HUB-EFFECT-IS-MOSTLY-HAUL of 13 August: a hub effect measured at x2.01
  on the margin fell to x1.22 within long haul, because the hub group was 38% long haul against the
  non-hub group's 22%. So the haul and type cuts are reported as a CROSS-TAB as well as singly, and
  a cut is only worth having if it holds inside the other.

  LEAVE ONE COHORT OUT. Every multiplier is learned on the other cohorts and applied to the held-out
  one. A multiplier fitted on the routes it is scored on will always look good.

  A LEVEL CANNOT FIX A SPREAD. RECUT-RESULT and FEED-IS-UNINFORMATIVE both ended there. So the
  ceiling is reported: what the band would read if every cut's median were corrected perfectly, which
  is the most any level correction of this shape can ever buy. If the ceiling is close to the
  uncorrected figure, the answer is that the engine's local leg is not off by a level at all.

    py -3.12 local_level_fit.py --arm ..\app\backtest_control_11Aug2026.csv

USE THE CONTROL ARM, not the qsi-feed one, unless you mean otherwise. captured_uncapped is the local
leg and should be identical across the two, but the control is the shipped configuration and it is
the one a correction would be applied on top of.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import math
import os
import statistics
import sys


def parse_args():
    p = argparse.ArgumentParser(description="The multiplier the engine's local leg needs.")
    p.add_argument("--arm", required=True, help="a backtest.py arm CSV")
    p.add_argument("--min-pax", type=float, default=100.0,
                   help="ignore routes whose local outturn is below this, default 100")
    p.add_argument("--band", type=float, default=0.20)
    p.add_argument("--out", default=None)
    return p.parse_args()


def _f(d, k):
    try:
        return float(d.get(k) or 0)
    except (TypeError, ValueError):
        return 0.0


def _q(v, p):
    s = sorted(v)
    return s[min(int(p * (len(s) - 1) + 0.5), len(s) - 1)]


def _hit(v, band):
    return 100.0 * sum(1 for x in v if abs(x - 1.0) <= band) / len(v) if v else 0.0


def haul(r):
    g = r["gcd"]
    return "1 <1500km" if g < 1500 else "2 1500-3000" if g < 3000 else \
           "3 3000-6000" if g < 6000 else "4 >6000km"


def main():
    a = parse_args()
    if not os.path.exists(a.arm):
        sys.exit("arm CSV not found: %r" % a.arm)
    with open(a.arm, newline="", encoding="utf-8") as f:
        arm = list(csv.DictReader(f))

    rows, ctl_bad = [], 0
    for r in arm:
        eng, act = _f(r, "captured_uncapped"), _f(r, "p2p_outturn")
        if eng <= 0 or act < a.min_pax:
            continue
        try:
            L = int(float(r.get("year")))
        except (TypeError, ValueError):
            continue
        # CONTROL: the arm already carries fc_over_p2p. If the ratio computed here does not
        # reproduce it, captured_uncapped is not the numerator backtest line 630 says it is and
        # nothing below can be trusted.
        stated = r.get("fc_over_p2p")
        mine = eng / act
        try:
            if stated not in ("", None) and abs(float(stated) - mine) > 0.02 * max(mine, 1e-9):
                ctl_bad += 1
        except ValueError:
            pass
        rows.append({"route": r.get("route"), "cohort": L, "engine": eng, "actual": act,
                     "gcd": _f(r, "gcd_km"), "typ": (r.get("type") or "?"),
                     "region": (r.get("region") or "?"),
                     "dom": (r.get("dep_country") or "") == (r.get("arr_country") or "") != "",
                     "needed": act / eng})

    print("arm %s: %d rows, %d scoreable" % (os.path.basename(a.arm), len(arm), len(rows)))
    print("control: %d rows where my engine/actual disagrees with the arm's own fc_over_p2p by "
          "more than 2%%" % ctl_bad)
    if ctl_bad > 0.01 * max(len(rows), 1):
        sys.exit("STOPPING. captured_uncapped is not the numerator behind fc_over_p2p on this arm.")
    if not rows:
        return

    need = [r["needed"] for r in rows]
    print("\nTHE MULTIPLIER THE ENGINE NEEDS, actual over forecast. Above 1.0 it UNDER-reads.")
    print("  ALL ROUTES  n=%d  median %.3f  IQR %.3f to %.3f  within +-%.0f%% %.1f%%"
          % (len(rows), statistics.median(need), _q(need, 0.25), _q(need, 0.75),
             100 * a.band, _hit([r["engine"] / r["actual"] for r in rows], a.band)))

    def block(title, key):
        print("\n%s" % title)
        print("   %-26s %6s %8s %19s %9s" % ("cut", "n", "median", "IQR", "in band"))
        g = {}
        for r in rows:
            g.setdefault(key(r), []).append(r)
        for lab in sorted(g, key=str):
            v = [x["needed"] for x in g[lab]]
            print("   %-26s %6d %8.3f %8.3f to %8.3f %8.1f%%"
                  % (str(lab), len(v), statistics.median(v), _q(v, 0.25), _q(v, 0.75),
                     _hit([x["engine"] / x["actual"] for x in g[lab]], a.band)))
        return g

    block("BY HAUL", haul)
    block("BY CARRIER TYPE", lambda r: r["typ"])
    block("BY DOMESTIC OR INTERNATIONAL", lambda r: "domestic" if r["dom"] else "international")
    # THE CROSS-TAB, because HUB-EFFECT-IS-MOSTLY-HAUL showed a marginal cut can carry another cut's
    # mix. A type effect is only real if it survives inside a haul band.
    block("HAUL x TYPE, the conditional view", lambda r: "%s / %s" % (haul(r), r["typ"]))
    block("BY COHORT, to see whether the level drifts with vintage", lambda r: r["cohort"])

    # ---- DOES A CUT EARN ITS PLACE? Leave one cohort out, global against segmented. ----
    def evaluate(name, key):
        scored = []
        for L in sorted({r["cohort"] for r in rows}):
            tr = [r for r in rows if r["cohort"] != L]
            te = [r for r in rows if r["cohort"] == L]
            if not tr or not te:
                continue
            gm = statistics.median(r["needed"] for r in tr)
            by = {}
            for r in tr:
                by.setdefault(key(r), []).append(r["needed"])
            by = {k: statistics.median(v) for k, v in by.items() if len(v) >= 30}
            for r in te:
                m = by.get(key(r), gm)
                scored.append(r["engine"] * m / r["actual"])
        return _hit(scored, a.band), len(scored)

    print("\nDOES THE CUT EARN ITS PLACE? Multiplier learned on the other cohorts, applied to the")
    print("held-out one. A segment needs 30 training routes or it falls back to the global number.")
    base = _hit([r["engine"] / r["actual"] for r in rows], a.band)
    print("   %-34s %6.1f%%" % ("uncorrected", base))
    for nm, key in (("one global multiplier", lambda r: "all"),
                    ("by haul", haul),
                    ("by carrier type", lambda r: r["typ"]),
                    ("by haul x type", lambda r: "%s / %s" % (haul(r), r["typ"]))):
        pc, n = evaluate(nm, key)
        print("   %-34s %6.1f%%   n=%d" % (nm, pc, n))

    # ---- THE CEILING. Correct every cut's median PERFECTLY, on the same routes, which is fitted
    # and therefore optimistic. It is the most a level correction of this shape can ever buy.
    print("\nTHE CEILING, fitted on the same routes and therefore not achievable in practice.")
    for nm, key in (("perfect global level", lambda r: "all"),
                    ("perfect haul x type level", lambda r: "%s / %s" % (haul(r), r["typ"]))):
        by = {}
        for r in rows:
            by.setdefault(key(r), []).append(r["needed"])
        by = {k: statistics.median(v) for k, v in by.items()}
        print("   %-34s %6.1f%%" % (nm, _hit([r["engine"] * by[key(r)] / r["actual"]
                                              for r in rows], a.band)))
    print("   If the ceiling sits close to the uncorrected figure, the engine's local leg is not")
    print("   off by a LEVEL and no multiplier will rescue it. The spread is then the whole story.")

    if a.out:
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["route", "cohort", "gcd_km", "type", "region", "domestic",
                        "engine_local", "p2p_outturn", "needed_multiplier"])
            for r in rows:
                w.writerow([r["route"], r["cohort"], round(r["gcd"]), r["typ"], r["region"],
                            int(r["dom"]), round(r["engine"]), round(r["actual"]),
                            round(r["needed"], 4)])
        print("\nwrote %s" % a.out)


if __name__ == "__main__":
    main()
