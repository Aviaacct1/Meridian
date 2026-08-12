#!/usr/bin/env python3
r"""Avia Solutions - does the LIVE assembly reproduce the TRAINING inputs on the training routes.

    py -3.12 bt2_input_check.py --cohort 2018 --n 60
    py -3.12 bt2_input_check.py --cohort 2018 --n 60 --bt2-dir E:\Avia\bt2_relaxed

WHY. bt2_wiring_test.py passed on 9 August 2026 with a largest difference of 0.000e+00 and did not
catch the fault that stopped the wiring three days later. It proved that bt2_forecast._vec and
bt2_g12_exp.X_of build the same vector FROM THE SAME INPUTS, feeding both sides from the training
rows. It never called route_context, so it could not see that route_context was building capa from a
different quantity altogether.

This closes that gap the only way it can be closed: take routes the training chain has already
scored, ask the LIVE path for the same three numbers, and compare. capture_L.csv holds what training
recorded. route_context.capture_inputs is what a client's forecast will use.

WHAT A PASS LOOKS LIKE. capa, qcx and legs_n identical to within floating point on every route
sampled. The two chains now import one implementation, so anything else means the live path is being
handed different arguments rather than running different code, and the arguments are the answer.

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


def training_rows(bt2, cohort):
    """The recorded capture row joined to the launch profile, which carries the frequency and the
    distance the capture was computed at. Both are needed: capa is a function of frequency and the
    block time is a function of distance, so comparing without them compares nothing."""
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
                    "qcx": (float(r["so_ab"] or 0) + 0.75 * float(r["sa_ab"] or 0)
                            + 0.25 * float(r["si_ab"] or 0) + float(r["so_ba"] or 0)
                            + 0.75 * float(r["sa_ba"] or 0) + 0.25 * float(r["si_ba"] or 0)),
                })
            except (TypeError, ValueError):
                continue
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", type=int, default=2018)
    ap.add_argument("--n", type=int, default=40, help="routes to sample; every route is one OAG "
                                                      "leg query, so keep it modest")
    ap.add_argument("--bt2-dir")
    ap.add_argument("--seed", type=int, default=12)
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
    worst = {"capa": 0.0, "qcx": 0.0, "legs_n": 0.0}
    worst_on = {}
    checked, refused = 0, []
    for r in rows:
        got, err = RC.capture_inputs(r["a"], r["b"], r["freq"], r["gcd"], r["pre_month"])
        if err:
            refused.append("%s-%s %s: %s" % (r["a"], r["b"], r["pre_month"], err))
            continue
        checked += 1
        for k in ("capa", "qcx", "legs_n"):
            d = abs(float(got[k]) - float(r[k]))
            if d > worst[k]:
                worst[k], worst_on[k] = d, "%s-%s %s: training %s, live %s" % (
                    r["a"], r["b"], r["pre_month"], r[k], got[k])

    print("\n%d route(s) compared, %d refused" % (checked, len(refused)))
    for line in refused[:10]:
        print("   REFUSED", line)
    if len(refused) > 10:
        print("   ... and %d more" % (len(refused) - 10))
    if not checked:
        raise SystemExit("NOT A PASS. No route could be compared, so nothing was tested.")
    print("\nlargest difference on any route sampled:")
    for k in ("capa", "qcx", "legs_n"):
        print("   %-8s %.3e   %s" % (k, worst[k], worst_on.get(k, "")))

    # The tolerance is floating point, not a judgement. The two chains import one implementation, so
    # a difference above this is a difference in the ARGUMENTS and the arguments are the finding.
    # Widening a tolerance to swallow a difference is how this codebase lost a scoring basis twice.
    tol = {"capa": 1e-9, "qcx": 1e-6, "legs_n": 0.0}
    bad = [k for k in tol if worst[k] > tol[k]]
    if bad:
        print("\nNOT A PASS. %s differ(s) by more than floating point. The live path and the "
              "training chain now run the same code, so the difference is in what each is handed: "
              "check the month label, the frequency and the distance first." % ", ".join(bad))
        sys.exit(1)
    print("\nPASS. The live assembly reproduces the training inputs on every route sampled.")


if __name__ == "__main__":
    main()
