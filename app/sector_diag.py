#!/usr/bin/env python3
"""
Avia Solutions - sector traffic profile by year (diagnostic).
=============================================================
Prints the EXACT carried traffic on each flown SJC route, year by year, so the operating
window (launch, ramp, cut) and any thin-data year show themselves. Uses the same sector_traffic
walk as the validation harness (every itinerary that flies the orig-dest leg, both directions,
P2P + all connecting feed). This is what isolates a real route cut from a data gap: a route that
was operating should show a full year of traffic; a near-zero year means cut or missing slice,
not underperformance.

RUN:
    py -3.12 sector_diag.py --sabre "C:\\Avia\\sabre.duckdb"
    py -3.12 sector_diag.py --sabre "C:\\Avia\\sabre.duckdb" --years 2013-2020
"""
import argparse, os, sys
from validate_sjc import sector_traffic

HERE = os.path.dirname(os.path.abspath(__file__))

# orig, dest, label, seats, freq  (capacity = seats*freq*52*2)
LEGS = [
    ("SJC", "LHR", "BA  London",     214, 7),
    ("SJC", "FRA", "LH  Frankfurt",  267, 5),
    ("SJC", "NRT", "NH  Tokyo",      240, 7),
    ("SJC", "PEK", "CA  Beijing",    280, 7),
]


def main():
    ap = argparse.ArgumentParser(description="Sector traffic by year for the flown SJC routes.")
    ap.add_argument("--sabre", required=True, help="sabre.duckdb")
    ap.add_argument("--years", default="2013-2026", help="inclusive year range, e.g. 2013-2020")
    a = ap.parse_args()
    if not os.path.exists(a.sabre):
        sys.exit(f"sabre store not found at {a.sabre}")
    lo, hi = (int(x) for x in a.years.split("-"))
    years = list(range(lo, hi + 1))

    print(f"Sector carried traffic by year (both directions, P2P + all connecting feed).\n")
    print(f"{'route':16} {'cap/yr':>8} " + " ".join(f"{y:>7}" for y in years))
    print("-" * (26 + 8 * len(years)))
    for orig, dest, label, seats, freq in LEGS:
        cap = seats * freq * 52 * 2
        cells = []
        for y in years:
            try:
                v = sector_traffic(a.sabre, orig, dest, y)
            except Exception as e:
                v = None
            cells.append(f"{v:>7,.0f}" if v else f"{'-':>7}")
        print(f"{label:16} {cap:>8,.0f} " + " ".join(cells))
    print("\nRead: the first/last non-zero year = the route's operating window. A lone near-zero "
          "year inside the window = a data gap, not underperformance. Achieved LF = carried / cap.")


if __name__ == "__main__":
    main()
