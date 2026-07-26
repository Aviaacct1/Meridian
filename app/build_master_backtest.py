#!/usr/bin/env python3
r"""
Avia Solutions - assemble the MASTER backtest (spine + every joinable driver). See MASTER_BACKTEST_VARIABLES.md.
====================================================================================================
Does NOT re-run the engine: the graded outcome (fc_over_out) already exists on the spine. This bolts on the
driver columns - the [derive] ones from on-disk assets now, and any [pull] airport-by-year files you extract
from the Sabre/OAG stores. Every airport-year pull is joined at the PRE-LAUNCH vintage (launch year - LAG),
so features are what was knowable before the route launched, never the outturn-year state (no leakage).

    py -3.12 build_master_backtest.py --spine bt_v2_6yr.csv --out master_backtest.csv \
        --airport-year airport_network_by_year.csv --airport-year airport_transfer_by_year.csv

Each --airport-year CSV must have columns: airport, year, <feature...>. Its features are joined TWICE, once for
the origin (dep_<feature>) and once for the destination (arr_<feature>), at year = launch_year - LAG.
"""
import argparse, csv, json, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))


def _rwy():
    try:
        return json.load(open(os.path.join(HERE, "ourairports_runways_cache.json")))
    except Exception:
        return {}


def haul_band(g):
    g = float(g or 0)
    return "sh" if g < 800 else "md" if g < 2500 else "lg" if g < 6000 else "xl"


def sm_band(x):
    return "lo" if x < 3 else "md" if x < 12 else "hi"


def load_airport_year(path):
    """-> {(AIRPORT, year): {feature: value}}, and the feature name list."""
    d = {}
    rd = csv.DictReader(open(path, newline=""))
    feats = [c for c in rd.fieldnames if c not in ("airport", "year")]
    for r in rd:
        d[((r["airport"] or "").upper(), str(r["year"]))] = {f: r[f] for f in feats}
    return d, feats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spine", default="bt_v2_6yr.csv")
    ap.add_argument("--out", default="master_backtest.csv")
    ap.add_argument("--airport-year", action="append", default=[], help="airport,year,<features> pull CSV (repeatable)")
    ap.add_argument("--lag", type=int, default=1, help="join pulls at launch_year - LAG (pre-launch vintage)")
    a = ap.parse_args()

    rwy = _rwy()

    def rw(code):
        v = rwy.get((code or "").upper())
        return (v[0], v[1]) if v else ("", "")

    pulls = [load_airport_year(p) for p in a.airport_year]

    rd = csv.DictReader(open(a.spine, newline=""))
    derived = ["haul_band", "seats_market", "seats_market_band", "domestic",
               "dep_runway_m", "dep_elev_m", "arr_runway_m", "arr_elev_m"]
    pull_cols = []
    for _d, feats in pulls:
        pull_cols += [f"dep_{f}" for f in feats] + [f"arr_{f}" for f in feats]
    out_fields = rd.fieldnames + derived + pull_cols
    w = csv.DictWriter(open(a.out, newline="", mode="w"), fieldnames=out_fields)
    w.writeheader()

    n = cov = 0
    hit = collections.Counter()
    for row in rd:
        nat = float(row.get("natural") or 0); cap = float(row.get("capacity") or 0)
        sm = (cap / nat) if nat > 0 else None
        row["haul_band"] = haul_band(row.get("gcd_km"))
        row["seats_market"] = round(sm, 3) if sm is not None else ""
        row["seats_market_band"] = sm_band(sm) if sm is not None else ""
        row["domestic"] = "1" if row.get("dep_country", "") == row.get("arr_country", "") else "0"
        row["dep_runway_m"], row["dep_elev_m"] = rw(row.get("dep"))
        row["arr_runway_m"], row["arr_elev_m"] = rw(row.get("arr"))
        if row["dep_runway_m"] != "" or row["arr_runway_m"] != "":
            cov += 1
        vintage = str(int(row["year"]) - a.lag) if str(row.get("year", "")).isdigit() else ""
        for (d, feats), src in zip(pulls, a.airport_year):
            for side in ("dep", "arr"):
                rec = d.get(((row.get(side) or "").upper(), vintage), {})
                for f in feats:
                    row[f"{side}_{f}"] = rec.get(f, "")
                if rec:
                    hit[src] += 1
        w.writerow(row); n += 1
    print(f"wrote {a.out}: {n} rows, +{len(derived)} derived, +{len(pull_cols)} pulled cols")
    print(f"  runway cover {cov}/{n} ({100*cov//n}%)")
    for src in a.airport_year:
        print(f"  {src}: {hit[src]} endpoint-matches at vintage (launch-{a.lag})")


if __name__ == "__main__":
    main()
