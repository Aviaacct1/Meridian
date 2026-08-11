#!/usr/bin/env python3
"""Avia Solutions - which airport moved, when two machines disagree on a QSI share.

    py -3.12 bt2\\coord_check.py

WHY THIS EXISTS. On 11 August the acceptance test returned qsi_share 0.2510 on one machine and
0.2513 on another, reading the SAME stores at the same commit. The stores were identical, the water
check made no difference, and only n_stops 0 and 1 ever reach itinerary_qsi so the two-stop change
could not be the cause. The one remaining difference was airportsdata: 20260315 against 20260803.

That is not a trivial difference. airportsdata supplies every coordinate the engine uses, so a
release that corrects one airport's position shifts a great-circle distance, which shifts a circuity
screen, which can add or drop a competing hub, which moves the QSI share. The library version is
therefore an INPUT TO THE FORECAST and belongs beside the store vintage, not in the background.

This prints the coordinates of the airports that actually decide SJC-TPE and diffs them against the
reference below, which was measured on airportsdata 20260315. Run it on any machine that disagrees
and it names the airport rather than leaving the difference as a version number.
"""
import sys

# Measured on airportsdata 20260315, 11 August 2026, the release every figure in
# commit-message-9 and -10 was produced on.
REFERENCE_VERSION = "20260315"
REFERENCE = {
    "APC": [38.21319, -122.28069], "BKK": [13.6811, 100.747], "CAN": [23.3924, 113.299],
    "CCR": [37.98966, -122.0569], "FAT": [36.77656, -119.71883], "HKG": [22.3089, 113.915],
    "HND": [35.5523, 139.78], "ICN": [37.4691, 126.451], "KIX": [34.4273, 135.244],
    "MCE": [37.28475, -120.51392], "MNL": [14.5086, 121.02], "MRY": [36.58695, -121.84278],
    "NRT": [35.7647, 140.386], "OAK": [37.72126, -122.22115], "PEK": [40.0801, 116.585],
    "PVG": [31.1434, 121.805], "SCK": [37.89441, -121.23874], "SFO": [37.61881, -122.37542],
    "SIN": [1.35019, 103.994], "SJC": [37.36299, -121.92862], "SMF": [38.69544, -121.59078],
    "STS": [38.50969, -122.81289], "TPE": [25.0777, 121.233], "TSA": [25.0694, 121.552],
}


def main():
    import airportsdata
    ver = getattr(airportsdata, "__version__", "?")
    ap = airportsdata.load("IATA")
    print(f"airportsdata on this machine: {ver}")
    print(f"reference measured on:        {REFERENCE_VERSION}")
    if str(ver) == REFERENCE_VERSION:
        print("Same release. Any difference in qsi_share is NOT the coordinates.")

    moved, missing = [], []
    for code, ref in sorted(REFERENCE.items()):
        rec = ap.get(code)
        if not rec:
            missing.append(code)
            continue
        here = [round(rec["lat"], 5), round(rec["lon"], 5)]
        if here != ref:
            # metres, near enough, for a sense of whether it is a correction or a rounding change
            dlat = (here[0] - ref[0]) * 111_320
            dlon = (here[1] - ref[1]) * 111_320 * 0.79   # cos(37 deg), the Bay Area / Taipei band
            moved.append((code, ref, here, (dlat ** 2 + dlon ** 2) ** 0.5))

    if missing:
        print(f"\nABSENT from this release: {', '.join(missing)}")
    if not moved:
        print("\nEvery airport that decides SJC-TPE is in the same position as the reference.")
        print("The coordinates are NOT the cause. Look at duckdb, then at the store vintage.")
        return 0
    print(f"\n{len(moved)} airport(s) MOVED against the reference:")
    for code, ref, here, m in sorted(moved, key=lambda t: -t[3]):
        print(f"  {code}  {ref} -> {here}   circa {m:,.0f} m")
    print("\nA coordinate move shifts a great-circle distance, which shifts the circuity screen,")
    print("which can add or drop a competing hub and move the QSI share. Decide whether the new")
    print("position is a correction worth adopting, then PIN the version so both machines agree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
