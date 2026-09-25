#!/usr/bin/env python3
r"""The model the app actually runs: its build stamp and its own in-sample pair. W10, September 2026.

    cd C:\src\meridian\bt2
    $env:AVIA_LOCAL_CACHE, AVIA_BT2_DIR, AVIA_APP_DIR, AVIA_BT2_COHORTS, AVIA_BT2_TARGET as for bt2_claimset
    py -3.12 bt2_pickle_stamp.py

Resolves the pickle exactly as app/bt2_forecast.py does (AVIA_BT2_MODEL, then AVIA_LOCAL_CACHE, then
E:\Avia, then C:\Avia; bt2_relaxed before bt2), loads it, prints every metadata field it carries, and
then scores ITS OWN q50 estimator in-sample on the rows of the sample AVIA_BT2_DIR points at, on both
outturn bases, within +-20% and +-10%. Read-only: nothing is written or refitted.

WHY. bt2_build_v13.py fits the calibrated figure with the CALIB configuration and prints it, then
pickles q25/q50/q75 fitted with BLIND_KW on all rows (lines 128-131). The estimator the app loads is
therefore the blind-configuration model, and no calibrated pair ever published describes it. This
script prints what does.

Avia Solutions Limited. All rights reserved.
"""
import math
import os
import pickle
import sys

import bt2_gbm as G
import bt2_lib as B
import bt2_g12_exp as F
from bt2_paths import find_app
from bt2_score import within
from bt2_claimset import _provenance

sys.path.insert(0, find_app())
import bt2_forecast as BF  # noqa: E402


def rate(rows, fc, tol=0.20):
    v = [f / r["actual"] for f, r in zip(fc, rows) if r["actual"] > 0]
    return 100.0 * sum(1 for x in v if within(x, tol)) / len(v)


def main():
    p = BF._model_path()
    print("\npickle resolved by bt2_forecast._model_path(): %s" % p)
    print("this process: %s" % _provenance())
    if not p:
        print("NO PICKLE FOUND. The app would decline every route; stop here.")
        return
    with open(p, "rb") as fh:
        m = pickle.load(fh)
    print("size %d bytes, mtime %s" % (os.path.getsize(p), __import__("time").ctime(os.path.getmtime(p))))
    print("\n=== STAMP: every metadata field in the artefact ===")
    for k in sorted(m):
        if k in ("q50", "q25", "q75", "carid"):
            continue
        print("  %-14s %s" % (k, m[k]))
    est = m["q50"]
    print("  q50 estimator  %s" % type(est).__name__)
    try:
        print("  q50 params     lr=%s it=%s leaves=%s minleaf=%s l2=%s loss=%s quantile=%s"
              % (est.learning_rate, est.max_iter, est.max_leaf_nodes, est.min_samples_leaf,
                 est.l2_regularization, est.loss, est.quantile))
        print("  q50 fitted     n_features_in=%s, iterations run=%s" % (est.n_features_in_, est.n_iter_))
    except Exception as e:                                   # noqa: BLE001
        print("  q50 params     not readable: %s" % e)
    print("  carid          %d carriers in the artefact, %d in this sample, %s"
          % (len(m.get("carid", {})), len(G.carid),
             "IDENTICAL" if m.get("carid") == G.carid else "DIFFERENT: the live feature vector and the "
             "training vector disagree on carrier identity"))

    rows = G.rows
    F.attach(rows)
    print("\n=== IN-SAMPLE: the artefact's own q50 on n=%d rows from %s, target %s ==="
          % (len(rows), B.BT2, B.TARGET))
    X = F.X_of(rows, ["base", "sister"])
    if X.shape[1] != getattr(est, "n_features_in_", X.shape[1]):
        print("  FEATURE WIDTH MISMATCH: sample builds %d features, artefact expects %d. Stop."
              % (X.shape[1], est.n_features_in_))
        return
    fc = [r["seats_ly"] * math.exp(v) for r, v in zip(rows, est.predict(X))]
    print("  Sabre throughout:  within +-20%% %5.1f%%   within +-10%% %5.1f%%"
          % (rate(rows, fc), rate(rows, fc, 0.10)))
    try:
        import bt2_mixed_basis as MB
        sab = [r["actual"] for r in rows]
        n_dot = MB.attach(rows)
        print("  mixed basis (%d US domestic on DOT DB1B): within +-20%% %5.1f%%   within +-10%% %5.1f%%"
              % (n_dot, rate(rows, fc), rate(rows, fc, 0.10)))
        for r, a in zip(rows, sab):
            r["actual"] = a
    except SystemExit as e:
        print("  mixed basis not scored: %s" % e)
    lo = [r["seats_ly"] * math.exp(v) for r, v in zip(rows, m["q25"].predict(X))]
    hi = [r["seats_ly"] * math.exp(v) for r, v in zip(rows, m["q75"].predict(X))]
    cov = sum(1 for r, a, b in zip(rows, lo, hi) if a <= r["actual"] <= b) / len(rows)
    print("  actual inside the artefact's p25-p75 range: %.1f%% of rows (50%% if the quantiles are honest)"
          % (100.0 * cov))
    print("\n  Reading: the pair above is what the model the app runs scores on the launches it was fitted on.")
    print("  The blind leave-one-cohort-out figure for the same configuration is in bt2_claimset (route level).")


if __name__ == "__main__":
    main()
