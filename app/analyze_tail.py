#!/usr/bin/env python3
r"""
Avia Solutions - tail diagnostic: is a >2x over-forecast a DEMAND over-read or just a low-load-factor
route we capped correctly?
=====================================================================================================
The back-test caps forecast_pax at the route's ACTUAL flown capacity (OAG, outturn year). So for any
route whose demand meets that capacity, fc_over_out = 1 / (actual load factor): a route we said would
fill but that flew half empty reads 2x with our capacity assumption exactly right. Before trimming the
demand level (item 9) we need to know how much of the >2x tail is that, versus genuine demand over.

For each over-forecast route this prints:
  cap_util  = forecast_pax / capacity   (near 1 -> we are capacity-capped, the LF story)
  act_LF    = outturn_pax  / capacity   (the route's real load factor; low -> it flew empty)
  fc/p2p    = captured_uncapped / p2p   (UNCAPPED demand vs pure P2P carried = the clean demand test)

Reading: a >2x route with cap_util ~1 and low act_LF is NOT a demand-model miss (our demand filled the
plane, the route underperformed). A >2x route with cap_util well below 1 IS a demand over-read.

    py -3.12 analyze_tail.py E:\bt_6yr_det.csv
    py -3.12 analyze_tail.py E:\bt_6yr_det.csv --over 2.0 --show 40
"""
import argparse, csv, os, sys


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _med(xs):
    xs = sorted(v for v in xs if v is not None)
    n = len(xs)
    return None if not n else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)


def main():
    ap = argparse.ArgumentParser(description="Split the over-forecast tail into capacity-capped vs demand over.")
    ap.add_argument("csv", help="a backtest output CSV (e.g. E:\\bt_6yr_det.csv)")
    ap.add_argument("--over", type=float, default=2.0, help="tail threshold on fc_over_out (default 2.0)")
    ap.add_argument("--min-outturn", type=float, default=3000, help="ignore sub-material routes")
    ap.add_argument("--cap-near", type=float, default=0.9, help="cap_util >= this counts as capacity-capped")
    ap.add_argument("--show", type=int, default=30, help="how many tail routes to list")
    a = ap.parse_args()
    if not os.path.exists(a.csv):
        print(f"not found: {a.csv}"); return 2

    rows = list(csv.DictReader(open(a.csv, newline="")))
    tail = []
    for r in rows:
        fo = _f(r.get("fc_over_out"))
        out = _f(r.get("outturn_pax")) or 0
        cap = _f(r.get("capacity")) or 0
        if fo is None or fo <= a.over or out < a.min_outturn:
            continue
        capu = (_f(r.get("forecast_pax")) or 0) / cap if cap else None
        lf = out / cap if cap else None
        r["_capu"], r["_lf"], r["_fo"] = capu, lf, fo
        tail.append(r)

    if not tail:
        print(f"no routes over {a.over}x with outturn >= {a.min_outturn:.0f}"); return 0

    capped = [r for r in tail if r["_capu"] is not None and r["_capu"] >= a.cap_near]
    demand = [r for r in tail if r["_capu"] is not None and r["_capu"] < a.cap_near]
    nocap = [r for r in tail if r["_capu"] is None]

    print(f"\n{os.path.basename(a.csv)}: {len(tail)} routes over {a.over}x (outturn >= {a.min_outturn:.0f})\n")
    print(f"  CAPACITY-CAPPED (cap_util >= {a.cap_near}): {len(capped)} routes "
          f"({100*len(capped)/len(tail):.0f}% of the tail)")
    print(f"     -> our demand filled the metal; the over is low load factor, NOT a demand miss")
    print(f"     median actual LF {(_med([r['_lf'] for r in capped]) or 0):.2f}   "
          f"median fc_over_out {(_med([r['_fo'] for r in capped]) or 0):.2f}   "
          f"(1/LF check: {1/ (_med([r['_lf'] for r in capped]) or 1):.2f})")
    print(f"  DEMAND OVER-READ (cap_util < {a.cap_near}): {len(demand)} routes "
          f"({100*len(demand)/len(tail):.0f}% of the tail)")
    print(f"     -> below capacity, so this IS the demand model over-forecasting")
    print(f"     median fc_over_out {(_med([r['_fo'] for r in demand]) or 0):.2f}   "
          f"median cap_util {(_med([r['_capu'] for r in demand]) or 0):.2f}   "
          f"median fc/p2p {(_med([_f(r.get('fc_over_p2p')) for r in demand]) or 0):.2f}")
    if nocap:
        print(f"  no capacity recorded: {len(nocap)} routes")

    # service pattern (present only on runs built with the seasonal tag; blank on older CSVs)
    svc = {}
    for r in tail:
        k = (r.get("service") or "").strip() or "-"
        svc[k] = svc.get(k, 0) + 1
    if set(svc) - {"-"}:
        print("\n  by service pattern (seasonal = the route flew only ONE of the two OAG seasons):")
        for k in sorted(svc, key=lambda z: -svc[z]):
            print(f"     {k:9} {svc[k]} routes")
        seasonal = svc.get("summer", 0) + svc.get("winter", 0)
        print(f"     -> {seasonal} seasonal routes graded against ANNUAL demand read as over-forecast; "
              "they are a seasonal business case, not a demand miss")

    print(f"\n  {'route':11} {'type':5} {'fc_over_out':>11} {'cap_util':>9} {'act_LF':>7} {'fc/p2p':>7}  bucket")
    for r in sorted(tail, key=lambda z: -(z["_fo"] or 0))[:a.show]:
        b = "CAPPED->low-LF" if (r["_capu"] or 0) >= a.cap_near else "demand-over"
        fp = _f(r.get("fc_over_p2p"))
        print(f"  {r.get('route',''):11} {r.get('type',''):5} {r['_fo']:>11.2f} "
              f"{(r['_capu'] if r['_capu'] is not None else float('nan')):>9.2f} "
              f"{(r['_lf'] if r['_lf'] is not None else float('nan')):>7.2f} "
              f"{(fp if fp is not None else float('nan')):>7.2f}  {b}")

    print(f"\nTakeaway: size the item-9 level trim on the DEMAND-OVER group, not the whole tail - the "
          f"capacity-capped routes are already 'right demand, empty plane' and trimming them would push "
          f"the good routes under.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
