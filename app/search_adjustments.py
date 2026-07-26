#!/usr/bin/env python3
r"""
Avia Solutions - adjustment search harness (the science-project rig).
====================================================================
Test MANY candidate accuracy adjustments through ONE identical scorecard and rank them. The point is not any
single result: it is that every hypothesis is scored the same honest way, nothing is dismissed before it is
tested, and the two columns tell you the two things you need:

  full-data  = fit the adjustment on ALL rows, then grade them. The ceiling / the "how accurate on the full
               data we have" number. This is the figure to quote for the track record (worded as historical fit).
  cross-val  = fit on 4/5, grade the held-out 1/5. The CONTROL. Does the adjustment generalise to a route it
               did not set, or is the full-data lift just fitting noise? The number that means it is REAL.

A hypothesis is SHIP-worthy when BOTH rise. It is PARK-worthy (not dead) when full-data rises but cross-val does
not - revisit it with better features or a real cause, because the control is telling you the correction is
fitting route noise, not a standing bias. The target: a row whose CROSS-VAL column crosses 50%.

    py -3.12 search_adjustments.py bt_v2_6yr.csv          # mature grade (where the 41% baseline lives)
    py -3.12 search_adjustments.py bt_v3_enriched_o0.csv  # same-regime 2024/2025 (offset-0: relative, not magnitude)

ADD A HYPOTHESIS: write one line in HYPOS. A hypothesis is (fit(train_rows) -> model, mult(row, model) -> factor).
The cause-based generators (secondary-airport, catchment overlap, connecting share, hub connectivity) are stubbed
at the bottom and need the airport-attributes join (ENRICHED_BACKTEST_SPEC.md) - that is the next space to test.
"""
import argparse, csv, math, random, itertools


def w20(xs):
    return 100 * sum(1 for x in xs if 0.8 <= x <= 1.2) / len(xs) if xs else 0.0


def band(v):
    return "<15k" if v < 15000 else "15-50k" if v < 50000 else "50-150k" if v < 150000 else ">150k"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--shrink", type=float, default=4.0)
    ap.add_argument("--clamp", type=float, default=0.69)
    ap.add_argument("--floor", type=int, default=6, help="min routes in a group to correct it")
    ap.add_argument("--forecastable-only", action="store_true")
    a = ap.parse_args()
    K, CLAMP, FLOOR = a.shrink, a.clamp, a.floor

    rows = []
    for r in csv.DictReader(open(a.csv, newline="")):
        try:
            fo = float(r.get("fc_over_out") or 0)
        except ValueError:
            fo = 0
        if fo <= 0:
            continue
        if a.forecastable_only and not (float(r.get("natural") or 0) >= float(r.get("p2p_outturn") or 0) > 0):
            continue
        rows.append({"dep": (r.get("dep") or "").upper(), "arr": (r.get("arr") or "").upper(),
                     "typ": r.get("type", ""), "reg": r.get("region", ""), "year": r.get("year", ""),
                     "dc": r.get("dep_country", ""), "ac": r.get("arr_country", ""),
                     "gcd": float(r.get("gcd_km") or 0), "nat": float(r.get("natural") or 0),
                     "psh": float(r.get("p2p_share") or -1), "fo": fo, "lfo": math.log(fo)})
    n = len(rows)
    if not n:
        print("no graded rows"); return

    def shrink(logs):
        return math.exp(-max(-CLAMP, min(CLAMP, sum(logs) / (len(logs) + K))))

    GRID = [round(0.5 + 0.02 * i, 2) for i in range(76)]  # 0.5 .. 2.0

    def opt(fos):
        bf, bc = 1.0, sum(1 for v in fos if 0.8 <= v <= 1.2)
        for f in GRID:
            c = sum(1 for v in fos if 0.8 <= v * f <= 1.2)
            if c > bc:
                bf, bc = f, c
        return bf

    def fitg(train, keyfn, kind):
        g = {}
        for r in train:
            g.setdefault(keyfn(r), []).append(r)
        return {k: (shrink([x["lfo"] for x in rs]) if kind == "s" else opt([x["fo"] for x in rs]))
                for k, rs in g.items() if len(rs) >= FLOOR and keyfn(rs[0]) not in ("", None)}

    def Hg(keyfn, kind):
        return (lambda tr: fitg(tr, keyfn, kind), lambda r, m: m.get(keyfn(r), 1.0))

    def H2(kind):
        def fit(tr):
            return (fitg(tr, lambda r: r["dep"], kind), fitg(tr, lambda r: r["arr"], kind))
        def mult(r, m):
            aa = m[0].get(r["dep"], 1.0); bb = m[1].get(r["arr"], 1.0)
            return aa if abs(math.log(aa)) >= abs(math.log(bb)) else bb
        return (fit, mult)

    def pshband(r):
        p = r["psh"]
        return "n/a" if p < 0 else "<0.3" if p < 0.3 else "0.3-0.7" if p < 0.7 else ">0.7"

    # ---- HYPOTHESIS REGISTRY: add a line here to test a new adjustment ----
    HYPOS = {
        "baseline (no adjustment)": (lambda tr: None, lambda r, m: 1.0),
        "per-airport origin (shrunk)": Hg(lambda r: r["dep"], "s"),
        "per-airport dest (shrunk)": Hg(lambda r: r["arr"], "s"),
        "per-airport origin (optimiser)": Hg(lambda r: r["dep"], "o"),
        "per-airport origin x dest (2way shrunk)": H2("s"),
        "per-airport origin x dest (2way optimiser)": H2("o"),
        "segment: carrier type": Hg(lambda r: r["typ"], "s"),
        "segment: region": Hg(lambda r: r["reg"], "s"),
        "segment: market-size band": Hg(lambda r: band(r["nat"]), "s"),
        "segment: connecting-share band": Hg(pshband, "s"),
        "airport x carrier-type": Hg(lambda r: (r["dep"], r["typ"]), "s"),
        "airport x market-size band": Hg(lambda r: (r["dep"], band(r["nat"])), "s"),
        # --- NEXT SPACE (needs airport-attributes join, ENRICHED_BACKTEST_SPEC.md): ---
        # "cause: secondary-airport x direction": Hg(lambda r: (r["secondary"], r["dir"]), "s"),
        # "cause: catchment-overlap band": Hg(lambda r: overlap_band(r), "s"),
        # "cause: hub-connectivity x haul": Hg(lambda r: (r["hubclass"], haul(r)), "s"),
    }

    # ---- AUTO-ENUMERATED FEATURE SEARCH: every carving and every crossing, so the board picks the grain ----
    # Add a feature here (one line) and it joins the single carvings, the pairwise crossings, and the
    # airport-side interactions automatically. A feature that maps to one value (missing column) is a harmless no-op.
    def _haul(g): return "sh" if g < 800 else "md" if g < 2500 else "lg" if g < 6000 else "xl"
    def _conn(p): return "na" if p < 0 else "ch" if p < 0.3 else "mx" if p < 0.7 else "pp"
    FEAT = {
        "intl": lambda r: "I" if r["dc"] != r["ac"] else "D",   # international vs domestic
        "type": lambda r: r["typ"],                              # FSC / LCC / ULCC / charter
        "haul": lambda r: _haul(r["gcd"]),
        "mkt": lambda r: band(r["nat"]),
        "conn": lambda r: _conn(r["psh"]),                       # connecting-heaviness
        "region": lambda r: r["reg"],
    }
    # CAUSE features from airport_attributes.json (role/hub-class/size per airport, joined on dep and arr).
    # NB: tested as blanket carvings these do NOT beat the mature-grade control (spread wall); their real use
    # is the airport-diagnosis SCREEN (find one airport with a nameable directional bias -> named override, the
    # SJC method), not a factor table. Kept here for any future test / new grade. See qsi-search-harness memory.
    try:
        import json as _json, os as _os
        _AT = _json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                            "airport_attributes.json")))["airports"]
    except Exception:
        _AT = {}
    def _at(code, f, d): return _AT.get((code or "").upper(), {}).get(f, d)
    def _hubb(l): return "mega" if l < 0.55 else "hub" if l < 0.78 else "mix" if l < 0.92 else "p2p"
    def _szb(s): return "xs" if s < 3 else "sm" if s < 15 else "md" if s < 50 else "lg"
    if _AT:
        FEAT.update({
            "dep_role": lambda r: _at(r["dep"], "role", "solo"),
            "arr_role": lambda r: _at(r["arr"], "role", "solo"),
            "dep_hub": lambda r: _hubb(_at(r["dep"], "localness", 0.99)),
            "arr_hub": lambda r: _hubb(_at(r["arr"], "localness", 0.99)),
            "dep_size": lambda r: _szb(_at(r["dep"], "size_m", 0)),
            "arr_size": lambda r: _szb(_at(r["arr"], "size_m", 0)),
        })
    for fn, kf in FEAT.items():
        HYPOS[f"1: {fn}"] = Hg(kf, "s")
    for (n1, k1), (n2, k2) in itertools.combinations(FEAT.items(), 2):
        HYPOS[f"2: {n1}x{n2}"] = Hg(lambda r, a=k1, b=k2: (a(r), b(r)), "s")
    for side in ("dep", "arr"):                                  # airport-side x feature (the SJC intl-inbound kind)
        for fn in ("intl", "type"):
            HYPOS[f"apt {side}x{fn}"] = Hg(lambda r, s=side, a=FEAT[fn]: (r[s], a(r)), "s")

    random.seed(7)
    idx = list(range(n)); random.shuffle(idx)
    bw = w20([r["fo"] for r in rows])
    years = sorted({r["year"] for r in rows if r["year"]})
    late = years[-1] if len(years) >= 2 else None          # the "mouse" test: fit earlier, grade the latest year
    te_idx = [i for i in range(n) if rows[i]["year"] == late] if late else []
    res = []
    for name, (fit, mult) in HYPOS.items():
        m = fit(rows)
        fw = w20([r["fo"] * mult(r, m) for r in rows])
        cv = [None] * n
        for k in range(a.folds):
            test = set(idx[k::a.folds])
            mk = fit([rows[i] for i in range(n) if i not in test])
            for i in test:
                cv[i] = rows[i]["fo"] * mult(rows[i], mk)
        tw = None
        if late:
            mt = fit([rows[i] for i in range(n) if rows[i]["year"] != late])
            tw = w20([rows[i]["fo"] * mult(rows[i], mt) for i in te_idx])
        res.append((name, fw, w20(cv), tw))
    res.sort(key=lambda t: -t[2])
    tcol = f"fwd({late})" if late else "fwd(n/a)"
    print(f"\nHYPOTHESIS LEADERBOARD  ({a.csv}, {n} routes, grade fc/out, baseline within20 {bw:.1f}%)")
    print(f"  DISH = full-data fit (calibrated on all)   MOUSE = fit earlier yrs, grade {late}   HUMAN = 2026/27, pending\n")
    print(f"{'hypothesis':44} {'DISH':>8} {'CV':>8} {'MOUSE '+tcol:>12}")
    for name, fw, cw, tw in res:
        ts = f"{tw:.1f}%" if tw is not None else "  -"
        flag = "  <- generalises" if cw > bw + 0.5 else ""
        print(f"{name:44} {fw:>7.1f}% {cw:>7.1f}% {ts:>12}{flag}")
    print("\nDISH  = ceiling / the number to quote as historical fit (calibrated on all the data we have).")
    print("CV    = fit 4/5, grade held-out 1/5: generalises to an unseen route, same era.")
    print(f"MOUSE = fit the earlier years, grade {late} it never saw: the strongest test we can run today.")
    print("HUMAN = 2026/2027 outturn - the real forward test, we wait for it. Nothing is dead; a weak MOUSE means")
    print("PARK and refine (better features / a cause), not close. Target = MOUSE (and CV) crossing 50%.")


if __name__ == "__main__":
    main()
