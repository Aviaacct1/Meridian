#!/usr/bin/env python3
r"""Both engines on one route, side by side, from a single engine run.

    py -3.12 compare_engines.py --origin SJC --dest SFO --dest-airport TPE ^
        --competing SFO,OAK,SJC --carrier BR --seats 333 --freq 7

John's question of 9 August, and it is the right one: how do I run them on different switches, and
how do I know. This is the answer to both. It does NOT read AVIA_FORECAST_ENGINE, because the point
is to see the two numbers together rather than one at a time: comparing by flipping a switch and
squinting at yesterday's answer is how a difference goes unnoticed.

THE ENGINE RUNS ONCE. route_forecast.forecast produces the QSI forecast and, since 9 August, also
returns the connection-set summary BT2 needs. So both numbers come from one calculation and any
difference between them is the model, never a different input.

WHAT TO LOOK AT, in order.

  1. THE TWO NUMBERS AND THEIR RATIO. Wide apart is not automatically wrong: the engine and BT2
     disagree by design, one building demand from catchment and capture, the other reading the
     airline's capacity decision. A ratio near 1.0 on a route you know well is reassuring; a ratio
     of 3 on a route you know well is the thing to chase before anyone else does.
  2. THE DOMAIN VERDICT. BT2 refuses routes whose market sits below anything it was trained on,
     which is usually a leaked market at a secondary airport. There the engine is the right tool
     and the comparison is not a fair fight.
  3. THE LOAD FACTOR each implies. An airline planner reads that before either passenger number,
     and a forecast implying 96% or 41% is telling you something the headline hides.
  4. THE RIGHTS VERDICT, if a carrier is named.

The honest test is not which number is closer to the other. It is whether the number an airline
would receive looks defensible to someone who knows the route. That judgement is yours; this puts
both in front of you with the same inputs so it can be made in one sitting.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import os
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--origin", required=True)
    ap.add_argument("--dest", required=True, help="destination metro codes, comma separated")
    ap.add_argument("--dest-airport", default=None, help="the specific arrival airport")
    ap.add_argument("--competing", required=True, help="the catchment's competing airports")
    ap.add_argument("--carrier", default=None)
    ap.add_argument("--seats", type=float, required=True, help="seats per departure")
    ap.add_argument("--freq", type=float, default=7.0, help="weekly frequency per direction")
    ap.add_argument("--months", type=float, default=12.0)
    ap.add_argument("--launch-month", type=int, default=6)
    ap.add_argument("--week", default=os.environ.get("AVIA_WEEK"))
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--sabre", default=None)
    ap.add_argument("--oag", default=None)
    ap.add_argument("--block-min", type=int, default=540)
    a = ap.parse_args()

    root = os.environ.get("AVIA_LOCAL_CACHE") or ""
    sabre = a.sabre or os.path.join(root, "sabre.duckdb")
    oag = a.oag or os.path.join(root, "oag.duckdb")
    for p, nm in ((sabre, "Sabre"), (oag, "OAG")):
        if not os.path.exists(p):
            sys.exit("%s store not found at %s. Set AVIA_LOCAL_CACHE or pass --sabre / --oag." % (nm, p))
    if not a.week:
        sys.exit("no schedule week given. Pass --week or set AVIA_WEEK, e.g. 2025-06.")

    dest_codes = [x.strip().upper() for x in a.dest.split(",") if x.strip()]
    competing = [x.strip().upper() for x in a.competing.split(",") if x.strip()]
    dest_airport = (a.dest_airport or dest_codes[0]).upper()
    origin = a.origin.upper()

    import route_forecast as RF
    fc = RF.forecast(sabre, oag, a.week, origin, dest_codes, competing,
                     year=a.year, freq=a.freq, block_min=a.block_min,
                     dest_airport=dest_airport, airline=a.carrier,
                     # EACH-WAY, which is the engine's convention: route_forecast computes
                     # annual_capacity as seats x freq x weeks and its comment records that a
                     # previous x2 "halved the reported load factor against each-way demand".
                     annual_capacity=a.seats * a.freq * 52.0 * (a.months / 12.0))

    # THE CONVENTIONS DIFFER AND MIXING THEM IS THE ERROR THIS TOOL EXISTS TO PREVENT, so it is
    # stated here. The QSI engine works EACH-WAY. BT2's seats_ly is BOTH DIRECTIONS, because
    # bt2_discover and bt2_profile sum both. Everything below is reported TWO-WAY, which is the
    # convention a client and an airline planner use, so the engine figure is doubled and BT2's is
    # left alone. On 9 August 2026 the first version of this tool passed a two-way capacity into the
    # each-way parameter and then divided an each-way forecast by two-way seats, which halved every
    # load factor and made the engine look badly low on SJC-TPE against John's known 115-135k.
    qsi_pax = 2.0 * float(fc.get("carried_forecast") or 0)
    seats = a.seats * a.freq * 2.0 * 52.0 * (a.months / 12.0)

    print("=" * 78)
    print("%s-%s  %s  %.0f seats x %.1f weekly, %.0f months. Schedule week %s"
          % (origin, dest_airport, a.carrier or "carrier not named", a.seats, a.freq,
             a.months, a.week))
    print("=" * 78)
    print("  seats offered, both directions   %s  (all figures below are TWO-WAY)" % format(int(seats), ","))

    print("\nQSI ENGINE  (catchment, capture, connecting feed). Engine works each-way; doubled here")
    print("  forecast                         %s passengers" % format(int(qsi_pax), ","))
    print("  measured market, two-way         %s" % format(int(2 * (fc.get("natural_market") or 0)), ","))
    print("  capture share                    %.4f" % (fc.get("qsi_share") or 0))
    print("  connecting feed                  %s behind, %s beyond"
          % (format(int(2 * (fc.get("feed_behind") or 0)), ","),
             format(int(2 * (fc.get("feed_beyond") or 0)), ",")))
    print("  implied load factor              %.1f%%" % (100.0 * qsi_pax / seats if seats else 0))

    print("\nBT2  (capacity anchor, trained on 6,524 launches)")
    if a.carrier:
        import route_context as RC
        d = RC.build(origin, dest_airport, a.carrier, aircraft_seats=a.seats, freq=a.freq,
                     months=a.months, launch_mon=a.launch_month, year=a.year,
                     engine_payload=fc)
        if not d.get("ok"):
            print("  cannot forecast:")
            for m in d["missing"]:
                print("    %s" % m)
        else:
            os.environ["AVIA_FORECAST_ENGINE"] = "bt2"   # this tool always shows both
            import importlib
            import bt2_forecast as BF
            importlib.reload(BF)
            r = BF.forecast(d, mode="scheduled")
            if not r.get("ok"):
                print("  REFUSED (%s), and that is the finding rather than a failure:"
                      % r.get("domain", "error"))
                print("    %s" % r.get("reason"))
            else:
                bp = r["pax"]
                print("  forecast                         %s passengers" % format(int(bp), ","))
                print("  range                            %s to %s"
                      % (format(int(r["lo"]), ","), format(int(r["hi"]), ",")))
                print("  confidence tier                  %s" % r["tier"])
                print("  domain                           %s, seats are %.1fx the existing market"
                      % (r["domain"], r["seats_over_market"]))
                if r.get("domain_note"):
                    print("    %s" % r["domain_note"])
                print("  implied load factor              %.1f%%" % (100.0 * bp / seats if seats else 0))
                print("\nSIDE BY SIDE")
                print("  QSI engine                       %s" % format(int(qsi_pax), ","))
                print("  BT2                              %s" % format(int(bp), ","))
                if qsi_pax > 0:
                    print("  BT2 over QSI                     %.2fx" % (bp / qsi_pax))
                print("  Read the load factors before the passenger numbers: a planner will.")
    else:
        print("  no carrier named, so BT2 cannot be run. Pass --carrier.")

    if a.carrier:
        try:
            import traffic_rights as TR
            v = TR.check(a.carrier.upper(), origin, dest_airport,
                         period=(a.week[:4] + "-%") if a.week else "2025-%")
            m = TR.message(v)
            if m:
                print("\nTRAFFIC RIGHTS")
                print("  %s" % m)
        except Exception as e:                              # noqa: BLE001
            print("\n  traffic rights not checked: %s" % e)


if __name__ == "__main__":
    main()
