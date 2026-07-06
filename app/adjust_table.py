#!/usr/bin/env python3
"""
Avia Solutions - the master adjustment table, back-solved from outturn.
====================================================================================
The product's real value is a table of corrections that pulls forecasts onto actual, cell by
cell, and grows as more routes launch. This does NOT guess variables; it reads the gap the
engine already leaves (outturn / forecast, after coverage + capture) and, for each cell with
enough evidence, emits the residual multiplier that would close it. A cell only earns a
PUBLISHED adjustment once it clears a trust gate: minimum sample AND the number holds across
the two halves of the period (early vs late years). Below the gate the cell stays "directional".

The cells, coarsest to finest:
    carrier type                     (FSC / LCC / ULCC / Regional)   - the launch-tier check
    carrier type x origin country    (LCC discipline varies by country)
    carrier x origin country         (Ryanair-IT != Wizz-IT != Ryanair-FR) - the secret sauce

Run AFTER a back-test so backtest_results.csv is current:
    py -3.12 adjust_table.py                  # reads app/backtest_results.csv
    py -3.12 adjust_table.py --min-n 8 --tol 0.25
Writes adjust_master.csv (every cell, with a trust flag) for the engine to load later.
"""
import argparse, csv, os, statistics as st
from collections import defaultdict

SHRINK_K = 6.0          # pull a cell's raw ratio toward 1.0 by n/(n+K) - thin cells barely move
CLAMP = (0.4, 2.5)      # no single cell may swing a forecast more than this


def _shrink(ratios):
    m = st.median(ratios); n = len(ratios)
    s = 1.0 + (m - 1.0) * n / (n + SHRINK_K)
    return min(CLAMP[1], max(CLAMP[0], s)), m, n


def _stable(ratios_early, ratios_late, tol):
    """A cell is stable if early- and late-period medians agree within tol (relative)."""
    if len(ratios_early) < 2 or len(ratios_late) < 2:
        return None
    a, b = st.median(ratios_early), st.median(ratios_late)
    if a <= 0 or b <= 0:
        return None
    return abs(a - b) / ((a + b) / 2.0) <= tol


def main():
    ap = argparse.ArgumentParser()
    HERE = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--csv", default=os.path.join(HERE, "backtest_results.csv"))
    ap.add_argument("--min-n", type=int, default=6, help="routes a cell needs to be PUBLISHED")
    ap.add_argument("--tol", type=float, default=0.30, help="max early-vs-late gap to call a cell stable")
    ap.add_argument("--basis", choices=["total", "p2p"], default="p2p",
                    help="p2p = outturn P2P / captured (the demand engine); total = outturn / forecast")
    ap.add_argument("--out", default=os.path.join(HERE, "adjust_master.csv"))
    a = ap.parse_args()

    rows = []
    with open(a.csv, newline="") as fh:
        for d in csv.DictReader(fh):
            try:
                if a.basis == "p2p":
                    num = float(d["p2p_outturn"]); den = float(d["captured_uncapped"])
                else:
                    num = float(d["outturn_pax"]); den = float(d["forecast_pax"])
                yr = int(float(d["year"]))
            except Exception:
                continue
            if den <= 0 or num <= 0:
                continue
            r = num / den
            if r < 0.05 or r > 20:
                continue
            rows.append(dict(r=r, yr=yr, typ=(d.get("type") or "?").strip(),
                             carrier=(d.get("carrier") or "?").strip(),
                             oc=(d.get("dep_country") or "?").strip(),
                             region=(d.get("region") or "?").strip()))
    if not rows:
        print("no usable rows"); return
    yrs = sorted(set(x["yr"] for x in rows)); mid = yrs[len(yrs)//2] if yrs else 0

    dims = [
        ("carrier_type",           lambda x: (x["typ"],)),
        ("carrier_type|country",   lambda x: (x["typ"], x["oc"])),
        ("carrier|country",        lambda x: (x["carrier"], x["oc"])),
    ]
    out = []
    print(f"{len(rows)} routes, basis={a.basis}, split year @ {mid}, publish gate n>={a.min_n} & stable(+/-{a.tol:.0%})\n")
    for dim_name, keyfn in dims:
        grp = defaultdict(list); early = defaultdict(list); late = defaultdict(list)
        for x in rows:
            k = keyfn(x); grp[k].append(x["r"])
            (early if x["yr"] < mid else late)[k].append(x["r"])
        print(f"== {dim_name} ==")
        printed = 0
        for k in sorted(grp, key=lambda z: -len(grp[z])):
            factor, raw, n = _shrink(grp[k])
            stable = _stable(early.get(k, []), late.get(k, []), a.tol)
            published = (n >= a.min_n) and (stable is True)
            flag = "PUBLISH" if published else ("thin" if n < a.min_n else "unstable")
            out.append(dict(dim=dim_name, cell="|".join(map(str, k)), n=n,
                            raw_ratio=round(raw, 3), factor=round(factor, 3),
                            stable=("" if stable is None else stable), published=published))
            if n >= max(3, a.min_n // 2) and printed < 18:
                mark = "  <-- PUBLISH" if published else ""
                print(f"   {'|'.join(map(str,k)):24} n={n:3}  raw {raw:5.2f}  ->factor {factor:5.2f}  {flag}{mark}")
                printed += 1
        print()

    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["dim","cell","n","raw_ratio","factor","stable","published"])
        w.writeheader()
        for r in out:
            w.writerow(r)
    npub = sum(1 for r in out if r["published"])
    print(f"wrote {a.out}  ({len(out)} cells, {npub} published)")
    # the launch read: is FSC ~1.0 and even, and which coarse cells clear the gate
    fsc = [x["r"] for x in rows if x["typ"] == "FSC"]
    if fsc:
        print(f"\nFSC launch check: n={len(fsc)} median {st.median(fsc):.2f} "
              f"(target ~1.0). {'READY BAND' if 0.8 <= st.median(fsc) <= 1.25 else 'not yet centred'}")


if __name__ == "__main__":
    main()
