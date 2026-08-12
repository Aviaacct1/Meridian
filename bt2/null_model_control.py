"""Is the sector figure forecasting, or is it arithmetic on seats?

WHY THIS EXISTS. On the relaxed sample, moving the grading target from launch_pax to sector traffic
took the blind route-level figure from 60.9% to 78.5% and the long-haul international FSC segment
from 39.8% to 73.7%. Before that number goes anywhere it has to survive the obvious objection.

THE OBJECTION. The model predicts passengers per seat and multiplies by seats_ly, and sector traffic
on a leg is close to seats times an achieved load factor. Load factor sits in a narrow band across
almost every route in the world. The local market's share of those same seats does not: it runs from
a few per cent on a hub-feed route to nearly all of them on a point-to-point one. So a target that is
nearly a load factor is easier to hit within +-20% than a target that is a share, and the gain could
be a property of the QUANTITY rather than of the model.

THE CONTROL. Forecast every route as seats_ly times the median ratio of the OTHER cohorts, leave one
cohort out, and score it exactly as bt2_claimset scores the model. That is a model with no features
at all: one number per cohort, learned from history, applied to seats. Whatever it scores is the
floor, and the model's claim is the distance above it.

    A null at 70-something and a model at 78.5 means the features are worth eight points and the
    claim is mostly seats. A null in the forties means the model is doing the work.

Run it under each target, because the answer differs by target and that difference is the point:

    $env:AVIA_BT2_TARGET = "nonstop"; py -3.12 null_model_control.py
    $env:AVIA_BT2_TARGET = "sector";  py -3.12 null_model_control.py

IT ALSO REPORTS THE TARGET'S OWN DISPERSION, the spread of actual over seats_ly, because that is the
mechanism the objection rests on. If sector's interquartile range is a third of nonstop's, the null
model will score well for a reason that has nothing to do with aviation and everything to do with
arithmetic, and the two figures should be read together.

Avia Solutions Limited. All rights reserved.
"""
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bt2_lib as B                                                     # noqa: E402
from bt2_score import within                                            # noqa: E402


def _pct(v, q):
    s = sorted(v)
    return s[min(int(q * (len(s) - 1) + 0.5), len(s) - 1)]


def main():
    rows = [r for r in B.load_clean() if r["actual"] > 0 and r["seats_ly"] > 0]
    print("\nNULL MODEL CONTROL. target %s, n=%d, cohorts %s"
          % (B.TARGET, len(rows), ",".join(str(c) for c in B.COHORTS)))

    ratio = [r["actual"] / r["seats_ly"] for r in rows]
    print("\n  THE TARGET'S OWN DISPERSION, actual over seats_ly")
    print("    median %.3f  IQR %.3f to %.3f  p10 %.3f  p90 %.3f"
          % (statistics.median(ratio), _pct(ratio, 0.25), _pct(ratio, 0.75),
             _pct(ratio, 0.10), _pct(ratio, 0.90)))
    print("    IQR spans a factor of %.2f. The narrower this is, the more a constant scores."
          % (_pct(ratio, 0.75) / max(_pct(ratio, 0.25), 1e-9)))

    out = []
    for L in B.COHORTS:
        tr = [r for r in rows if r["cohort"] != L]
        te = [r for r in rows if r["cohort"] == L]
        if not tr or not te:
            continue
        # ONE NUMBER, learned from the other cohorts. The median rather than the mean because the
        # ratio is bounded below by zero and has a long right tail, and a mean would be dragged by
        # the artifact-adjacent routes the 1.1x rule leaves in.
        k = statistics.median(r["actual"] / r["seats_ly"] for r in tr)
        for r in te:
            f = r["seats_ly"] * k
            out.append({"c": L, "fc": f, "act": r["actual"], "ratio": f / r["actual"], "k": k})

    print("\n  THE NULL, leave one cohort out, seats x the other cohorts' median ratio")
    for L in B.COHORTS:
        ks = {o["k"] for o in out if o["c"] == L}
        if ks:
            print("    cohort %s learned k = %.4f" % (L, list(ks)[0]))
    r20 = 100.0 * sum(1 for o in out if within(o["ratio"])) / len(out)
    r10 = 100.0 * sum(1 for o in out if within(o["ratio"], 0.10)) / len(out)
    print("    route level, within +-20%%   %5.1f%%   n=%d" % (r20, len(out)))
    print("    route level, within +-10%%   %5.1f%%" % r10)

    import random
    for n in (10, 20):
        random.seed(11)
        groups = []
        for L in B.COHORTS:
            co = [o for o in out if o["c"] == L]
            random.shuffle(co)
            groups += [co[i:i + n] for i in range(0, len(co), n) if len(co[i:i + n]) == n]
        sh = []
        for g in groups:
            A = sum(o["act"] for o in g)
            if A > 0:
                sh.append(sum(o["fc"] for o in g) / A)
        if sh:
            print("    portfolios of %-2d           %5.1f%%   %d baskets"
                  % (n, 100.0 * sum(1 for x in sh if within(x)) / len(sh), len(sh)))

    print("\n  BY SEGMENT, the null")
    seg = [("short-haul, domestic or LCC",
            lambda r: r["gcd"] < 2500 and (r["dom"] or r["typ"] == "LCC")),
           ("long-haul, international, FSC",
            lambda r: r["gcd"] >= 2500 and not r["dom"] and r["typ"] != "LCC")]
    order = [r for L in B.COHORTS for r in rows if r["cohort"] == L]
    for label, fn in seg:
        v = [o["ratio"] for o, r in zip(out, order) if fn(r)]
        if v:
            print("    %-30s %5.1f%%   n=%d"
                  % (label, 100.0 * sum(1 for x in v if within(x)) / len(v), len(v)))

    print("\n  READ IT AGAINST bt2_claimset's BLIND FIGURE ON THE SAME TARGET AND SAMPLE.")
    print("  The model's claim is the distance above this floor, not the figure itself.")


if __name__ == "__main__":
    main()
