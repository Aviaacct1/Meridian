#!/usr/bin/env python3
r"""Avia Solutions - does the LIVE assembly reproduce the TRAINING inputs on the training routes.

    py -3.12 bt2_input_check.py --cohort 2018 --n 40
    py -3.12 bt2_input_check.py --cohort 2018 --n 40 --bt2-dir E:\Avia\bt2_relaxed

WHY. bt2_wiring_test.py passed on 9 August 2026 with a largest difference of 0.000e+00 and did not
catch the fault that stopped the wiring three days later. It proved that bt2_forecast._vec and
bt2_g12_exp.X_of build the same vector FROM THE SAME INPUTS, feeding both sides from the training
rows. It never called route_context, so it could not see that route_context was building capa from a
different quantity altogether.

This closes that gap the only way it can be closed: take routes the training chain has already
scored, ask the LIVE path for the same three numbers, and compare. capture_L.csv holds what training
recorded. route_context.capture_inputs is what a client's forecast will use.

WHAT THE FIRST VERSION GOT WRONG, 12 August 2026, and it is worth recording. It printed the LARGEST
difference and nothing else. One route differing while thirty-nine match is a different finding from
forty routes differing, and a maximum cannot tell them apart, so the run failed without saying what
had failed. It now reports HOW MANY routes matched, the DISTRIBUTION of the ratio between them, and
for the worst routes a component-by-component comparison against the six sums and the two minimum
elapsed times the training CSV already carries. That last table names the mechanism: sums scaled
with the minimum elapsed times matching is a weighting or a frequency difference, and minimum
elapsed times differing is a different connection set.

WHAT A FAILURE MEANS. Not that the model is wrong. That the number a client would be shown was
produced from inputs the published accuracy does not describe, which is the same fault in a
different place and must be fixed before anything is wired.

Run it on the Workstation, where the OAG store and the BT2 artefacts both resolve.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _bt2_dir(given=None):
    for c in (given, os.environ.get("AVIA_BT2_DIR"),
              os.path.join("E:" + os.sep, "Avia", "bt2_relaxed"),
              os.path.join("E:" + os.sep, "Avia", "bt2"),
              os.path.join("C:" + os.sep, "Avia", "bt2_relaxed")):
        if c and os.path.isdir(c):
            return c
    return None


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def training_rows(bt2, cohort):
    """The recorded capture row joined to the launch profile, which carries the frequency and the
    distance the capture was computed at. Both are needed: capa is a function of frequency and the
    block time is a function of distance, so comparing without them compares nothing.

    The six per-direction sums and the two minimum elapsed times are kept as well, because they are
    what turns a failure into a diagnosis."""
    cap_path = os.path.join(bt2, "capture_%d.csv" % cohort)
    prof_path = os.path.join(bt2, "launch_profile_%d.csv" % cohort)
    for p in (cap_path, prof_path):
        if not os.path.isfile(p):
            raise SystemExit("NOT RUN. %s does not exist. Name the BT2 data folder with --bt2-dir "
                             "or set AVIA_BT2_DIR." % p)
    prof = {}
    with open(prof_path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            prof[(r["a"], r["b"])] = r
    out = []
    with open(cap_path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            p = prof.get((r["a"], r["b"]))
            if not p or not r.get("cap_actual") or not r.get("legs_n"):
                continue
            try:
                out.append({
                    "a": r["a"], "b": r["b"], "pre_month": r["pre_month"],
                    "freq": max(1.0, float(p["wk_freq_dir"] or 1)),
                    "gcd": float(p["gcd_km"] or 0) or 1000.0,
                    "capa": float(r["cap_actual"]), "legs_n": int(r["legs_n"]),
                    # The MODEL FEATURE qcx, bt2_lib line 60: both directions, no one-stop factor.
                    "qcx": (_f(r["so_ab"]) + 0.75 * _f(r["sa_ab"]) + 0.25 * _f(r["si_ab"])
                            + _f(r["so_ba"]) + 0.75 * _f(r["sa_ba"]) + 0.25 * _f(r["si_ba"])),
                    "comp": [[_f(r["so_ab"]), _f(r["sa_ab"]), _f(r["si_ab"]), _f(r["mn_ab"])],
                             [_f(r["so_ba"]), _f(r["sa_ba"]), _f(r["si_ba"]), _f(r["mn_ba"])]],
                    "block": _f(r["block"]),
                })
            except (TypeError, ValueError):
                continue
    return out


def _dist(name, ratios):
    """The shape of the disagreement, not one number from it."""
    if not ratios:
        return "   %-8s no comparable route" % name
    rs = sorted(ratios)
    n = len(rs)
    return ("   %-8s n=%d  min %.4f  p25 %.4f  median %.4f  p75 %.4f  max %.4f"
            % (name, n, rs[0], rs[max(0, n // 4)], statistics.median(rs),
               rs[min(n - 1, 3 * n // 4)], rs[-1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", type=int, default=2018)
    ap.add_argument("--n", type=int, default=40, help="routes to sample; every route is one OAG "
                                                      "leg query, so keep it modest")
    ap.add_argument("--bt2-dir")
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--show", type=int, default=3, help="worst routes to break down component by "
                                                        "component")
    a = ap.parse_args()

    bt2 = _bt2_dir(a.bt2_dir)
    if not bt2:
        raise SystemExit("NOT RUN. No BT2 data folder found. Use --bt2-dir or set AVIA_BT2_DIR.")
    rows = training_rows(bt2, a.cohort)
    if not rows:
        raise SystemExit("NOT RUN. cohort %d has no usable capture rows in %s" % (a.cohort, bt2))
    random.Random(a.seed).shuffle(rows)
    rows = rows[:a.n]
    print("BT2 folder %s, cohort %d, %d route(s) sampled" % (bt2, a.cohort, len(rows)))

    import route_context as RC
    tol = {"capa": 1e-9, "qcx": 1e-6, "legs_n": 0.0}
    matched = {k: 0 for k in tol}
    ratios = {"capa": [], "qcx": []}
    worst = []
    checked, refused = 0, []
    mct_seen = set()

    for r in rows:
        got, err = RC.capture_inputs(r["a"], r["b"], r["freq"], r["gcd"], r["pre_month"])
        if err:
            refused.append("%s-%s %s: %s" % (r["a"], r["b"], r["pre_month"], err))
            continue
        checked += 1
        mct_seen.add(bool(got.get("mct_loaded")))
        diffs = {k: abs(float(got[k]) - float(r[k])) for k in tol}
        for k in tol:
            if diffs[k] <= tol[k]:
                matched[k] += 1
        for k in ratios:
            if float(r[k]):
                ratios[k].append(float(got[k]) / float(r[k]))
        worst.append((max(diffs["capa"], diffs["qcx"] / 100.0), r, got, diffs))

    print("\n%d route(s) compared, %d refused" % (checked, len(refused)))
    for line in refused[:10]:
        print("   REFUSED", line)
    if len(refused) > 10:
        print("   ... and %d more" % (len(refused) - 10))
    if not checked:
        raise SystemExit("NOT A PASS. No route could be compared, so nothing was tested.")

    # THE MCT MASTER, reported rather than assumed. The training chain loads it through config and
    # then through bt2_paths.mct_master; the live path has only the first of those. An empty minimum
    # connect time table lets every itinerary through at the 90 minute default, which changes the
    # connection set and every sum over it.
    print("\nMCT master loaded on the live path: %s"
          % ("yes" if mct_seen == {True} else "no" if mct_seen == {False} else "mixed %s" % mct_seen))

    print("\nroutes matching to floating point:")
    for k in ("capa", "qcx", "legs_n"):
        print("   %-8s %d of %d" % (k, matched[k], checked))

    print("\nlive over training, across the sample:")
    for k in ("capa", "qcx"):
        print(_dist(k, ratios[k]))

    bad = [k for k in tol if matched[k] < checked]
    if not bad:
        print("\nPASS. The live assembly reproduces the training inputs on every route sampled.")
        return

    # THE DIAGNOSIS. Sums scaled with mn matching is a weighting or a frequency difference; mn
    # differing is a different connection set. The training CSV carries both, so this is free.
    worst.sort(key=lambda t: -t[0])
    print("\nworst %d route(s), component by component. Each direction is "
          "(online, alliance, interline, min elapsed):" % min(a.show, len(worst)))
    for _s, r, got, diffs in worst[:a.show]:
        print("\n  %s-%s %s   freq %.1f   gcd %.0f km   block training %.0f live %s"
              % (r["a"], r["b"], r["pre_month"], r["freq"], r["gcd"], r["block"],
                 got.get("block")))
        for i, side in enumerate(("a to b", "b to a")):
            t = r["comp"][i]
            l = got["components"][i]
            print("    %-7s training %10.3f %10.3f %10.3f  mn %6.0f" % (side, t[0], t[1], t[2], t[3]))
            print("    %-7s live     %10.3f %10.3f %10.3f  mn %6.0f" % ("", l[0], l[1], l[2], l[3]))
            for j, nm in enumerate(("online", "alliance", "interline")):
                if t[j] and l[j]:
                    print("    %-7s %-9s live over training %.4f" % ("", nm, l[j] / t[j]))
        print("    capa  training %.5f  live %.5f   qcx training %.4f  live %.4f"
              % (r["capa"], got["capa"], r["qcx"], got["qcx"]))

    print("\nNOT A PASS. %s differ(s) on %s. The two chains now run the same code, so the "
          "difference is in what each is handed. Read the table above: sums scaled with the minimum "
          "elapsed times matching is a weighting or a frequency difference; minimum elapsed times "
          "differing is a different connection set."
          % (", ".join(bad), ", ".join("%d of %d routes" % (checked - matched[k], checked)
                                       for k in bad)))
    sys.exit(1)


if __name__ == "__main__":
    main()
