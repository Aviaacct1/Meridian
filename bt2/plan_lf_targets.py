#!/usr/bin/env python3
r"""What load factor did real launches actually achieve, by carrier type and by haul?

WHY. route_forecast.MAX_PLAN_LF is one global 0.875 applied to every carrier type and every haul,
and carried = min(total_demand, annual_capacity x max_plan_lf) can only ever reduce. So it bites
hardest on the carriers whose economics depend on filling the aircraft, and it does so with no
measured basis behind the number. That is LF-CAP-OPEN, open since 12 August 2026.

WHAT THIS MEASURES, and it is one ratio per launch:

    achieved sector load factor = alt_targets.sector / launch_profile.seats_ly

sector is the leg-adjacency total from build_alt_targets: every itinerary in which the two airports
are consecutive, counted once per itinerary, so it is the whole sector a client is shown, local and
connecting together. That is the correct numerator for a load factor, because the cap applies to the
carried total and not to either leg. seats_ly is bt2_profile's operated seats in the launch year,
summed over both directions across the months the route actually operated.

THREE BASIS CAVEATS, printed by the run as well as recorded here, because they govern how far the
result can be pushed:

  1. THE NUMERATOR NEEDS NO TRANSFER CORRECTION, and the first version of this file said it did.
     It carried a caveat that Sabre under-counts transfer traffic by the 2.07x and 2.50x of
     FLOOR-EVIDENCED, so that these load factors read low. THAT WAS WRONG AND THIS RUN DISPROVED IT.
     FLOOR-EVIDENCED measured "the multiplier the FLAT feed needs to reach" actual connecting, with
     the Sabre residual as the TARGET; it is a measurement of how far the engine's flat feed
     under-read, not of Sabre's own coverage. Applying it as a Sabre correction is arithmetically
     impossible on this population: measured 14 August on 336 long-haul launches, the median
     connecting share of the sector is 0.572, so a 2.50x correction takes the median achieved load
     factor from 0.782 to 1.360 and puts 78% of launches above 100%. At 2.07x it is 1.185 and 71%.
     So the figures below stand as measured and nothing is to be added to them.

  2. THE TWO WINDOWS ARE NOT IDENTICAL. seats_ly covers the months the route operated; sector covers
     source_year = L entire. On a virgin pair the pre-launch months carry no traffic, so the two
     broadly agree, but a route with a gap month has the gap excluded from seats and any traffic in
     it counted. The run reports months_operated so the short launch years can be cut out.

  3. HAUL AND CARRIER TYPE ARE CONFOUNDED, as HUB-EFFECT-IS-MOSTLY-HAUL recorded on 13 August for a
     different quantity. Low-cost carriers fly short and full-service carriers fly long, so a
     marginal cut by type carries the haul mix. Every cut is therefore reported BOTH marginally and
     with haul held, and the conditional figure is the one to read.

THE CONTROL COMES FIRST AND IT IS NOT DECORATION. Passengers on a sector cannot exceed the seats
flown on it. If a material share of launches return a ratio above 1.0 then the numerator and the
denominator are not on one basis and NOTHING below the control line means anything. The run states
the share above 1.0 before it prints a single cut, and stops if it exceeds --max-impossible.

WHAT THIS DOES NOT DO. It does not change MAX_PLAN_LF and it writes nothing the engine reads. It
writes plan_lf_achieved.csv so the cuts can be argued with.

    Workstation:
    cd C:\src\meridian\bt2
    py -3.12 plan_lf_targets.py --oag E:\Avia\oag.duckdb

Avia Solutions Limited. All rights reserved.
"""
import argparse
import csv
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from bt2_paths import BT2, OAG                                          # noqa: E402

# Carrier type resolution, taken from backtest.py lines 39 to 41 rather than reinvented, so one
# definition of a low-cost carrier serves the back-test and this measurement alike.
ULCC = {"FR", "W6", "W9", "WZ", "NK", "F9", "G4", "VY", "U2", "EW", "PC", "DY"}
REGIONAL = {"YV", "OO", "9E", "ZW", "G7", "C5", "EV", "QX", "YX"}
TYPE_BY_CAT = {"LOW COST": "LCC", "LOWCOST": "LCC", "L": "LCC", "MAINLINE": "FSC", "M": "FSC"}

# Haul cuts as feed_level_recut.py uses them, so the two tools can be read side by side.
HAULS = [(0, 1500, "under 1500km"), (1500, 3000, "1500-3000km"),
         (3000, 6000, "3000-6000km"), (6000, 99999, "over 6000km")]


def parse_args():
    p = argparse.ArgumentParser(description="Achieved sector load factor by carrier type and haul.")
    p.add_argument("--oag", default=OAG, help="the OAG store, for the carrier category")
    p.add_argument("--cohorts", default=os.environ.get("AVIA_BT2_COHORTS",
                                                       "2016,2017,2018,2019,2024,2025"))
    p.add_argument("--min-seats", type=float, default=10000.0,
                   help="drop launches below this many operated seats, where the ratio is noise")
    p.add_argument("--min-months", type=int, default=6,
                   help="drop launches operating fewer months than this, see caveat 2")
    p.add_argument("--max-impossible", type=float, default=0.05,
                   help="share of launches allowed above a load factor of 1.0 before the run stops")
    p.add_argument("--out", default=None, help="output CSV, default <BT2>/plan_lf_achieved.csv")
    return p.parse_args()


def haul_of(km):
    for lo, hi, name in HAULS:
        if lo <= km < hi:
            return name
    return "unknown"


def carrier_types(oag_db, carriers):
    """{carrier: FSC/LCC/ULCC/Regional} from the OAG carrier_category, UNKNOWN where the store has
    no category. Never guessed: a carrier with no category is reported as UNKNOWN and cut out, which
    is the flag-rather-than-fill rule."""
    out = {c: "UNKNOWN" for c in carriers}
    for c in carriers:
        if c in ULCC:
            out[c] = "ULCC"
        elif c in REGIONAL:
            out[c] = "Regional"
    unresolved = [c for c, t in out.items() if t == "UNKNOWN"]
    if not unresolved or not oag_db or not os.path.exists(oag_db):
        return out
    import duckdb
    con = duckdb.connect(oag_db, read_only=True)
    try:
        con.execute("SET memory_limit='3GB'; SET threads=3; SET enable_progress_bar=false")
        ph = ",".join("?" * len(unresolved))
        rows = con.execute(f"""
            SELECT carrier, UPPER(TRIM(ANY_VALUE(carrier_category))) cat, COUNT(*) n
            FROM oag WHERE carrier IN ({ph}) GROUP BY carrier
        """, unresolved).fetchall()
    finally:
        con.close()
    for car, cat, _n in rows:
        t = TYPE_BY_CAT.get(cat or "")
        if t:
            out[car] = t
    return out


def load_launches(cohorts):
    """One row per launch, joining the profile to the grading targets. Both files are required: a
    cohort missing either is reported by name and skipped rather than part-counted."""
    recs, missing = [], []
    for L in cohorts:
        prof_p = os.path.join(BT2, "launch_profile_%d.csv" % L)
        targ_p = os.path.join(BT2, "alt_targets_%d.csv" % L)
        if not (os.path.exists(prof_p) and os.path.exists(targ_p)):
            missing.append((L, os.path.basename(prof_p) if not os.path.exists(prof_p)
                            else os.path.basename(targ_p)))
            continue
        with open(targ_p, newline="", encoding="utf-8") as f:
            targ = {(r["a"], r["b"]): r for r in csv.DictReader(f)}
        with open(prof_p, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                t = targ.get((r["a"], r["b"]))
                if not t:
                    continue
                try:
                    seats = float(r["seats_ly"] or 0)
                    sector = float(t["sector"] or 0)
                    nonstop = float(t["nonstop"] or 0)
                    km = float(r["gcd_km"] or 0)
                except (TypeError, ValueError):
                    continue
                recs.append({"a": r["a"], "b": r["b"], "cohort": L,
                             "carrier": (r.get("oag_carrier") or "").strip().upper(),
                             "gcd_km": km, "haul": haul_of(km),
                             "months_operated": int(r.get("months_operated") or 0),
                             "n_carriers": int(r.get("n_carriers") or 0),
                             "seats_ly": seats, "sector": sector, "nonstop": nonstop})
    return recs, missing


def cut(recs, keyfn, label, out_rows, cap=0.875):
    """One block of the report. n, the quartiles, and the share of real launches ABOVE the shipped
    cap, which is the figure the cap has to answer to."""
    groups = {}
    for r in recs:
        groups.setdefault(keyfn(r), []).append(r["lf"])
    print("\n%s" % label)
    print("  %-18s %6s %7s %7s %7s %7s   %% above %.3f" %
          ("", "n", "p25", "median", "p75", "p90", cap))
    for k in sorted(groups, key=lambda g: -len(groups[g])):
        v = sorted(groups[k])
        if len(v) < 15:
            print("  %-18s %6d   too few launches to read" % (str(k), len(v)))
            continue
        q = statistics.quantiles(v, n=100)
        above = 100.0 * sum(1 for x in v if x > cap) / len(v)
        print("  %-18s %6d %7.3f %7.3f %7.3f %7.3f %11.1f%%" %
              (str(k), len(v), q[24], statistics.median(v), q[74], q[89], above))
        out_rows.append({"cut": label, "group": k, "n": len(v), "p25": round(q[24], 4),
                         "median": round(statistics.median(v), 4), "p75": round(q[74], 4),
                         "p90": round(q[89], 4), "pct_above_cap": round(above, 1)})


def main():
    a = parse_args()
    cohorts = [int(c) for c in a.cohorts.split(",") if c.strip()]
    recs, missing = load_launches(cohorts)
    print("BT2 folder %s" % BT2)
    for L, name in missing:
        print("cohort %d SKIPPED: %s not found" % (L, name))
    if not recs:
        sys.exit("No launch has both a launch_profile and an alt_targets file. Run bt2_profile and "
                 "build_alt_targets first; neither is in the repo, both are written to the BT2 "
                 "folder on the run host.")
    print("%d launches joined across %d launch years" % (len(recs), len(cohorts) - len(missing)))

    for r in recs:
        r["lf"] = (r["sector"] / r["seats_ly"]) if r["seats_ly"] > 0 else None

    # THE CONTROL, before any cut is printed. Passengers on a sector cannot exceed the seats flown.
    scored = [r for r in recs if r["lf"] is not None and r["seats_ly"] >= a.min_seats]
    if not scored:
        sys.exit("Every launch was dropped by --min-seats %.0f." % a.min_seats)
    impossible = [r for r in scored if r["lf"] > 1.0]
    share = len(impossible) / len(scored)
    print("\nCONTROL: sector passengers over operated seats")
    print("  %d of %d launches read ABOVE 1.0, which is %.1f%%" %
          (len(impossible), len(scored), 100 * share))
    if impossible:
        w = max(impossible, key=lambda r: r["lf"])
        print("  worst %s-%s %d, %.2f on %.0f seats" %
              (w["a"], w["b"], w["cohort"], w["lf"], w["seats_ly"]))
    if share > a.max_impossible:
        sys.exit("  STOPPING. More than %.0f%% of launches carry more passengers than the seats "
                 "flown, so the Sabre sector total and the OAG operated seats are not on one basis "
                 "and no cut below this line can be read. Settle the basis before rerunning."
                 % (100 * a.max_impossible))
    print("  Within tolerance, so the two are on one basis and the cuts below can be read.")

    # The impossible ones are DROPPED and counted, never truncated to 1.0: a ratio above 1.0 is a
    # measurement fault on that route and clipping it would fold the fault into the median.
    #
    # THEY ARE ALSO WRITTEN OUT, added 14 August. The first version reported the count and the worst
    # case and kept the rows to itself, so an exclusion of 155 launches could not be audited and the
    # standing hypothesis, that they are charter markets where OAG holds thin scheduled service
    # against a full Sabre passenger count, could not be checked by anyone reading the output.
    # An exclusion nobody can inspect is a silent filter with a printed count in front of it.
    excl_p = os.path.join(BT2, "plan_lf_achieved_excluded.csv")
    with open(excl_p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["a", "b", "cohort", "carrier", "gcd_km", "haul",
                                          "months_operated", "n_carriers", "seats_ly", "sector",
                                          "nonstop", "lf", "reason"], extrasaction="ignore")
        w.writeheader()
        for r in sorted(scored, key=lambda x: -x["lf"]):
            if r["lf"] > 1.0:
                w.writerow(dict(r, lf=round(r["lf"], 4), reason="more passengers than seats flown"))
            elif r["months_operated"] < a.min_months:
                w.writerow(dict(r, lf=round(r["lf"], 4),
                                reason="operated %d months, under --min-months %d"
                                       % (r["months_operated"], a.min_months)))
    print("  the excluded launches are written to %s so the filter can be argued with"
          % os.path.basename(excl_p))
    scored = [r for r in scored if r["lf"] <= 1.0 and r["months_operated"] >= a.min_months]
    print("  %d launches scored after dropping the impossible ones and launch years shorter than "
          "%d months" % (len(scored), a.min_months))

    types = carrier_types(a.oag, {r["carrier"] for r in scored if r["carrier"]})
    for r in scored:
        r["ctype"] = types.get(r["carrier"], "UNKNOWN")
    n_unknown = sum(1 for r in scored if r["ctype"] == "UNKNOWN")
    print("  carrier type resolved for %d of %d launches, %d UNKNOWN and reported as such"
          % (len(scored) - n_unknown, len(scored), n_unknown))

    out_rows = []
    cut(scored, lambda r: "ALL", "EVERY LAUNCH", out_rows)
    cut(scored, lambda r: r["haul"], "BY HAUL", out_rows)
    cut(scored, lambda r: r["ctype"], "BY CARRIER TYPE, marginal (carries the haul mix)", out_rows)
    for _lo, _hi, name in HAULS:
        band = [r for r in scored if r["haul"] == name]
        if len(band) >= 30:
            cut(band, lambda r: r["ctype"], "BY CARRIER TYPE within %s, haul held" % name, out_rows)
    cut(scored, lambda r: r["cohort"], "BY LAUNCH YEAR, a vintage control", out_rows)
    cut(scored, lambda r: "single carrier" if r["n_carriers"] <= 1 else "competed",
        "BY COMPETITIVE STRUCTURE", out_rows)

    print("\nHOW TO READ THIS, and it is the whole point of the run.")
    print("  These figures stand as measured and NOTHING is to be added to them for a supposed")
    print("  Sabre transfer under-count. FLOOR-EVIDENCED's 2.07x and 2.50x measure the multiplier")
    print("  the engine's FLAT FEED needed to reach the Sabre residual, with Sabre as the target,")
    print("  and say nothing about Sabre's own coverage. Applied here they are impossible: see")
    print("  caveat 1 in the docstring for the arithmetic and the run that settled it.")
    print("  A cap is an UPPER LIMIT and not a median. Setting it at any median above would spill")
    print("  half of every launch that has actually happened. The figure to read against a")
    print("  candidate cap is the last column, the share of real launches that exceeded it.")

    outp = a.out or os.path.join(BT2, "plan_lf_achieved.csv")
    with open(outp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cut", "group", "n", "p25", "median", "p75", "p90",
                                          "pct_above_cap"])
        w.writeheader()
        w.writerows(out_rows)
    detail = os.path.splitext(outp)[0] + "_routes.csv"
    with open(detail, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["a", "b", "cohort", "carrier", "ctype", "gcd_km", "haul",
                                          "months_operated", "n_carriers", "seats_ly", "sector",
                                          "nonstop", "lf"], extrasaction="ignore")
        w.writeheader()
        for r in sorted(scored, key=lambda x: -x["lf"]):
            r["lf"] = round(r["lf"], 4)
            w.writerow(r)
    print("\nwrote %s and %s" % (os.path.basename(outp), os.path.basename(detail)))


if __name__ == "__main__":
    main()
