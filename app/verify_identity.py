#!/usr/bin/env python3
r"""
Avia Solutions - identity harness for the runtime fixes (REVIEW_QSI_for_Opus_05Jul2026, items 1-3).
====================================================================================================
The runtime work (R1 pre-aggregation, R2 multiprocessing, R3 connection registry, R4 pin ordering)
is PURE PERFORMANCE: it must not move a single forecast. This harness is the guard the brief asks
for FIRST. It runs the back-test over the first N pinned routes and diffs every output cell against
the same routes in a known-good baseline CSV. Any non-identical cell fails the run. Minutes, not a
full run: nothing here is a modelling change, so nothing here earns a full pass over the store.

Two ways to use it:

  1. Drive the back-test itself (default). It shells out to backtest.py with the SAME flags that
     produced the baseline, capped to --limit N, writes a temp CSV, then diffs:

         py -3.12 verify_identity.py --oag C:\Avia\oag.duckdb --sabre C:\Avia\sabre.duckdb

     Defaults reproduce the V1 6-year baseline: --feed-fix --routes-file pinned_6yr_v2.json,
     diffed against bt_v1_6yr.csv. For the V2 baseline pass --v2 (adds --qsi-feed with the locked
     knobs and diffs against bt_v2_6yr.csv).

  2. Diff a candidate you already ran (--candidate my_run.csv): skips the subprocess and just diffs.
     Use this to check a full parallel run against the baseline after the fact.

WHY the key match, not row order: R2's process pool returns routes out of order, so rows are matched
on (dep, arr, year) and sorted before compare. Row ORDER may differ; every value must not.

PIN NOTE: the 6-year runbook Step 3 names pinned_6yr.json; the Opus kick-off brief names
pinned_6yr_v2.json, and the first row of bt_v1_6yr.csv (NAS-TPA 2016) is the first entry of
pinned_6yr_v2.json. Default is pinned_6yr_v2.json; if a matched route is MISSING from the baseline,
try --routes-file pinned_6yr.json (the harness reports missing keys explicitly so this is obvious).
"""
import argparse, csv, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

# Every column backtest.py writes. All must match to the penny for a pure-performance change.
KEY = ("dep", "arr", "year")
COMPARE_COLS = ("route", "dep", "arr", "dep_country", "arr_country", "type", "year", "region",
                "carrier", "hub_dest", "forecast_pax", "captured_uncapped", "capacity",
                "feed_beyond", "feed_behind", "p2p_outturn", "fc_over_p2p", "outturn_pax",
                "fc_over_out", "natural", "propensity", "propensity_basis", "gcd_km")


def _load(path):
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    idx = {}
    for r in rows:
        idx[(r["dep"], r["arr"], str(r["year"]))] = r
    return rows, idx


# Column classes for tolerance grading. RATIO cols carry 3-dp ratios; PAX cols are integer pax/km.
# The rest (codes, type, region, basis) must always match exactly.
RATIO_COLS = {"fc_over_p2p", "fc_over_out", "propensity"}
PAX_COLS = {"forecast_pax", "captured_uncapped", "capacity", "feed_beyond", "feed_behind",
            "p2p_outturn", "outturn_pax", "natural", "gcd_km"}


def _cells_equal(a, b):
    """Exact match. Numeric strings compared as numbers so 0.88 == 0.880; everything else as text.
    Empty string only equals empty string (a blank ratio must stay blank)."""
    if a == b:
        return True
    if a == "" or b == "":
        return False
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return False


def _severity(col, a, b, tol_pax, tol_ratio):
    """'ok' identical, 'tol' numeric drift within tolerance (float-order noise), 'bad' material."""
    if _cells_equal(a, b):
        return "ok"
    if a == "" or b == "":
        return "bad"
    try:
        d = abs(float(a) - float(b))
    except (TypeError, ValueError):
        return "bad"
    if col in RATIO_COLS:
        return "tol" if d <= tol_ratio else "bad"
    if col in PAX_COLS:
        return "tol" if d <= tol_pax else "bad"
    return "bad"


def run_backtest(a, out_csv):
    cmd = [sys.executable, os.path.join(HERE, "backtest.py"),
           "--oag", a.oag, "--sabre", a.sabre,
           "--routes-file", a.routes_file, "--limit", str(a.limit), "--out", out_csv]
    if a.v2:
        cmd += ["--qsi-feed", "--wave-cache", a.wave_cache,
                "--qsi-k", str(a.qsi_k), "--qsi-k-behind", str(a.qsi_k_behind),
                "--qsi-lambda", str(a.qsi_lambda)]
    else:
        cmd += ["--feed-fix"]
    if a.extra:
        cmd += a.extra.split()
    # Deterministic candidate: single DuckDB thread (fixed SUM reduction order -> stable top-N cuts)
    # and a fixed hash seed (stable set iteration). Caller can override by pre-setting either var.
    env = dict(os.environ)
    env.setdefault("AVIA_DUCKDB_THREADS", "1")
    env.setdefault("PYTHONHASHSEED", "0")
    print("running:", " ".join(cmd), "\n(AVIA_DUCKDB_THREADS=%s PYTHONHASHSEED=%s)\n"
          % (env["AVIA_DUCKDB_THREADS"], env["PYTHONHASHSEED"]))
    t = __import__("time").time()
    subprocess.run(cmd, check=True, env=env)
    print(f"\nback-test finished in {__import__('time').time()-t:.0f}s\n")


def main():
    ap = argparse.ArgumentParser(description="Row-for-row identity check of a back-test run vs a baseline.")
    ap.add_argument("--oag", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--sabre", default=r"C:\Avia\sabre.duckdb")
    ap.add_argument("--baseline", default=None,
                    help="known-good CSV (default bt_v1_6yr.csv, or bt_v2_6yr.csv with --v2)")
    ap.add_argument("--routes-file", default=os.path.join(HERE, "pinned_6yr_v2.json"))
    ap.add_argument("--limit", type=int, default=100, help="cap to the first N pinned routes")
    ap.add_argument("--candidate", default=None,
                    help="diff this already-run CSV instead of shelling out to backtest.py")
    ap.add_argument("--v2", action="store_true",
                    help="reproduce the V2 baseline (adds --qsi-feed at the locked knobs; diffs vs bt_v2_6yr.csv)")
    ap.add_argument("--wave-cache", default=os.path.join(HERE, "qsi_wave_cache_6yr.duckdb"))
    ap.add_argument("--qsi-k", type=float, default=0.65)
    ap.add_argument("--qsi-k-behind", type=float, default=1.41)
    ap.add_argument("--qsi-lambda", type=float, default=0.5)
    ap.add_argument("--extra", default=None, help="extra flags passed through to backtest.py verbatim")
    ap.add_argument("--show", type=int, default=25, help="max mismatching rows to print")
    ap.add_argument("--tol-pax", type=float, default=0.0,
                    help="absolute pax/km tolerance; drift within it counts as float-order noise, "
                         "not a material change (default 0 = exact identity)")
    ap.add_argument("--tol-ratio", type=float, default=0.0,
                    help="absolute tolerance on the 3-dp ratio columns (default 0 = exact)")
    a = ap.parse_args()

    baseline = a.baseline or os.path.join(HERE, "bt_v2_6yr.csv" if a.v2 else "bt_v1_6yr.csv")
    if not os.path.exists(baseline):
        print(f"baseline not found: {baseline}"); return 2

    if a.candidate:
        cand_path = a.candidate
    else:
        cand_path = os.path.join(tempfile.gettempdir(), "verify_identity_candidate.csv")
        run_backtest(a, cand_path)

    _, base_idx = _load(baseline)
    cand_rows, _ = _load(cand_path)
    print(f"baseline {os.path.basename(baseline)}: {len(base_idx)} rows")
    print(f"candidate {os.path.basename(cand_path)}: {len(cand_rows)} rows\n")

    tol_on = a.tol_pax > 0 or a.tol_ratio > 0
    missing, material, tol_only = [], [], []
    col_bad = {c: 0 for c in COMPARE_COLS}
    col_tol = {c: 0 for c in COMPARE_COLS}
    for r in cand_rows:
        k = (r["dep"], r["arr"], str(r["year"]))
        base = base_idx.get(k)
        if base is None:
            missing.append(k); continue
        bad, tol = [], []
        for c in COMPARE_COLS:
            s = _severity(c, base.get(c, ""), r.get(c, ""), a.tol_pax, a.tol_ratio)
            if s == "bad":
                bad.append((c, base.get(c, ""), r.get(c, ""))); col_bad[c] += 1
            elif s == "tol":
                tol.append((c, base.get(c, ""), r.get(c, ""))); col_tol[c] += 1
        if bad:
            material.append((k, bad + tol))
        elif tol:
            tol_only.append((k, tol))

    checked = len(cand_rows) - len(missing)
    print(f"routes checked (present in both): {checked}")
    if missing:
        print(f"\n{len(missing)} candidate routes NOT in baseline (pin/flag mismatch, not an engine diff):")
        for k in missing[:a.show]:
            print("   ", "-".join(k[:2]), k[2])
        print("   -> if these are real launches, the baseline used a different pin; try --routes-file pinned_6yr.json")
    if tol_on:
        print(f"within-tolerance (float-order noise, |pax|<={a.tol_pax:g}, |ratio|<={a.tol_ratio:g}): "
              f"{len(tol_only)} routes")

    if not material and not tol_only:
        print(f"\nPASS: all {checked} matched routes identical across every column. "
              "Pure-performance change confirmed.")
        return 0
    if not material:
        print(f"\nPASS (within tolerance): {checked - len(tol_only)} identical, {len(tol_only)} within "
              "float-order tolerance, 0 material. No model change.")
        return 0

    print(f"\nFAIL: {len(material)} of {checked} matched routes differ MATERIALLY. Per-column material counts:")
    for c in COMPARE_COLS:
        if col_bad[c]:
            print(f"   {c:20} {col_bad[c]}" + (f"  (+{col_tol[c]} within-tol)" if col_tol[c] else ""))
    print(f"\nfirst {min(a.show, len(material))} materially different routes (bad first, then within-tol):")
    for k, diffs in material[:a.show]:
        print(f"  {'-'.join(k[:2])} {k[2]}:")
        for c, bv, cv in diffs:
            print(f"     {c:18} baseline={bv!r}  candidate={cv!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
