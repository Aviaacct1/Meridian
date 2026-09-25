#!/usr/bin/env python3
r"""What the calibration record can and cannot say about a new long-haul nonstop. W10, September 2026.

    AVIA_BT2_DIR=E:\Avia\bt2          py -3.12 bt2_record_mix.py     the 2,915 canon
    AVIA_BT2_DIR=E:\Avia\bt2_relaxed  py -3.12 bt2_record_mix.py     the 6,524 relaxed sample

Reads the same rows as bt2_claimset.py, fits nothing new for the mix, and answers four questions from
routes/W10-RULINGS.md (25 September):

  BASIS    what the record graded: launch_pax (Sabre NON-STOP on the unordered pair, both directions)
           over seats_ly (OAG seats in the operated months, both directions). Printed, not assumed.
  MIX      how many launches by haul, domestic or international, region pair, carrier type, and by the
           size of the pair's existing market, so a reader knows where the record can speak.
  SHARE    the record's analogue of Test A: launch_pax over base_mkt, the new nonstop's first-year
           local traffic as a share of the pair's existing O&D, by class (median and quartiles).
  SEATS    the model's own response to seats, on its own rows: the blind config and the fitted config
           are each fitted on all rows, and every row is re-predicted at half and at double its seats
           (the capacity-aggressiveness feature moves with it, as it does live). The median pax ratio
           is the seat elasticity the live path inherits when Optimise sweeps frequency.

Nothing here changes an artefact or a log; the run is logged by hand in bt2_experiments.log.

Avia Solutions Limited. All rights reserved.
"""
import copy
import math
import statistics
from collections import Counter, defaultdict

import bt2_gbm as G
import bt2_lib as B
import bt2_g12_exp as F
from bt2_claimset import _provenance, SPEC, G12, BLIND_KW, FITTED_KW

EUROPE = set("AT BE BG CH CY CZ DE DK EE ES FI FR GB GR HR HU IE IS IT LT LU LV MT NL NO PL PT RO RS SE SI SK "
             "AL BA MD ME MK UA XK GI JE GG IM FO".split())
NAM = {"US", "CA"}
ASIA = set("CN HK TW JP KR IN PK BD LK NP TH VN MY SG ID PH KH LA MM MO BN MN KZ UZ".split())
MIDEAST = set("AE QA SA OM KW BH JO IL IR IQ LB EG TR".split())


def region_pair(r):
    a, b = r.get("ctry_a", ""), r.get("ctry_b", "")
    s = {("EU" if c in EUROPE else "NA" if c in NAM else "AS" if c in ASIA else "ME" if c in MIDEAST else "OT")
         for c in (a, b)}
    if r["dom"]:
        return "domestic " + ("US" if a == "US" else "EU" if a in EUROPE else "other")
    return "-".join(sorted(s)) if len(s) == 2 else "intra-" + next(iter(s))


def q(v):
    v = sorted(v)
    if not v:
        return "n/a"
    p = lambda f: v[min(len(v) - 1, int(f * len(v)))]
    return "med %.3f (p25 %.3f, p75 %.3f)" % (statistics.median(v), p(0.25), p(0.75))


def main():
    rows = G.rows
    F.attach(rows)
    print("\nsample: n=%d, cohorts %s, from %s" % (len(rows), ",".join(str(c) for c in B.COHORTS), B.BT2))
    print("target: %s   build: %s" % (B.TARGET, _provenance()))

    print("\n=== BASIS: what the record graded ===")
    ratio = [r["actual"] / r["seats_ly"] for r in rows]
    print("  actual = launch_pax, Sabre NON-STOP, unordered pair, BOTH DIRECTIONS (bt2_discover.py)")
    print("  seats_ly = OAG seats in the operated months, BOTH DIRECTIONS (bt2_profile.py; wk_freq_dir halves ops)")
    print("  actual / seats_ly: %s, max %.3f (rows above 1.1 are excluded as artefacts)"
          % (q(ratio), max(ratio)))
    print("  so a model output of seats_ly x exp(p) is a TWO-WAY local nonstop figure on the same basis")

    print("\n=== MIX: where the record can speak ===")
    classes = {
        "haul": lambda r: "short <2,500 km" if r["gcd"] < 2500 else "long >=2,500 km",
        "haul band": lambda r: B.haul_band(r["gcd"]),
        "scope": lambda r: "domestic" if r["dom"] else "international",
        "region pair": region_pair,
        "carrier type": lambda r: r["typ"],
        "pair market band": lambda r: B.size_band(r["base_mkt"]),
        "long-haul international by carrier type": lambda r: (r["typ"] if (r["gcd"] >= 2500 and not r["dom"]) else None),
    }
    for name, fn in classes.items():
        c = Counter(fn(r) for r in rows if fn(r) is not None)
        tot = sum(c.values())
        print("  %s:" % name)
        for k, n in sorted(c.items(), key=lambda kv: -kv[1]):
            print("    %-36s %5d  %5.1f%%" % (k, n, 100.0 * n / tot))

    print("\n=== SHARE: launch_pax / base_mkt, the new nonstop's year-one local traffic over the pair's existing O&D ===")
    print("  (Test A in the umbrella measures the model's local against the service area's traffic to the destination;")
    print("   this is the nearest quantity the record holds, on the raw pair, before any catchment)")
    for name in ("haul", "scope", "region pair", "pair market band"):
        fn = classes[name]
        g = defaultdict(list)
        for r in rows:
            g[fn(r)].append(r["actual"] / r["base_mkt"])
        print("  by %s:" % name)
        for k, v in sorted(g.items(), key=lambda kv: -len(kv[1])):
            print("    %-36s n=%5d  %s" % (k, len(v), q(v)))
    lh = [r for r in rows if r["gcd"] >= 2500 and not r["dom"]]
    for band in ("S2", "S3"):
        v = [r["actual"] / r["base_mkt"] for r in lh if B.size_band(r["base_mkt"]) == band]
        print("  long-haul international, pair market %s: n=%d  %s" % (band, len(v), q(v)))
    for rp in ("EU-NA", "AS-EU"):
        v = [r["actual"] / r["base_mkt"] for r in lh if region_pair(r) == rp]
        w = [r["actual"] / r["seats_ly"] for r in lh if region_pair(r) == rp]
        print("  %s long-haul: n=%d  share %s  pax/seat %s" % (rp, len(v), q(v), q(w)))

    print("\n=== SEATS: the model's response to its own seat anchor, all rows, both configs ===")
    X, y = F.X_of(rows, G12), G.y_of(rows)
    for label, kw in (("blind config", BLIND_KW), ("fitted config", FITTED_KW)):
        m = G.make(SPEC, **kw)
        m.fit(X, y)
        base = m.predict(X)
        print("  %s:" % label)
        for mult in (0.5, 2.0, 7.0 / 3.0):
            alt = copy.deepcopy(rows)
            for r in alt:
                r["seats_ly"] *= mult
            p = m.predict(F.X_of(alt, G12))
            rat = [mult * math.exp(pa - pb) for pa, pb in zip(p, base)]
            el = [math.log(x) / math.log(mult) for x in rat]
            print("    seats x%.3f: pax ratio %s; implied elasticity med %.2f" % (mult, q(rat), statistics.median(el)))
            g = defaultdict(list)
            for r, x in zip(rows, rat):
                g[classes["haul"](r)].append(x)
            for k, v in sorted(g.items()):
                print("      %-20s pax ratio %s" % (k, q(v)))


if __name__ == "__main__":
    main()
