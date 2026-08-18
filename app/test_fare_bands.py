#!/usr/bin/env python3
"""Offline checks for R5: measured fares render as bands on self-serve surfaces.

    py -3.12 test_fare_bands.py

Every fare here is a TEST FIXTURE.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(os.path.dirname(HERE), "deck")
for p in (HERE, DECK):
    sys.path.insert(0, p)

import fare_bands as FB

FAIL = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-62s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


def rd(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as fh:
        return fh.read()


def main():
    # the grid: $25 under 500, $50 to 1,500, $100 above
    check("412 bands to 400-425", FB.band(412)["label"] == "400-425")
    check("499.99 stays in the 25 grid", FB.band(499.99)["label"] == "475-500")
    check("500 moves to the 50 grid", FB.band(500)["label"] == "500-550")
    check("1499 in the 50 grid", FB.band(1499)["label"] == "1450-1500")
    check("1500 moves to the 100 grid", FB.band(1500)["label"] == "1500-1600")
    check("band edges are integers", isinstance(FB.band(412)["lo"], int))
    check("zero fare is None, not a zero band", FB.band(0) is None)
    check("junk is None", FB.band("n/a") is None)
    check("no currency symbol in the label", "$" not in FB.band(412)["label"])

    # the deck helper carries the same grid
    import forecast_spec as FS
    check("spec prefers the payload's band",
          FS._fare_band_label({"avg_fare_band": {"label": "400-425"}}) == "400-425")
    check("spec bands a raw figure the same way",
          FS._fare_band_label({"avg_fare": 412}) == "400-425")
    check("spec grids agree at 500", FS._fare_band_label({"avg_fare": 500}) == "500-550")
    check("spec grids agree at 1500", FS._fare_band_label({"avg_fare": 1500}) == "1500-1600")
    check("spec returns None on no fare", FS._fare_band_label({}) is None)

    # the surfaces: exact fare gone, band in
    ca = rd(HERE, "cortex_app.py")
    check("payload carries avg_fare_band", '"avg_fare_band": FB.band(' in ca)
    check("payload exact avg_fare gone", '"avg_fare": r["avg_fare"]' not in ca)
    check("opportunities banded", '"avg_fare_band": FB.band(fw / pax)' in ca)
    check("opportunities exact gone", '"avg_fare": round(fw / pax' not in ca)
    dash = rd(HERE, "cortex_dashboard.html")
    check("dashboard renders the band", "avg_fare_band" in dash)
    check("dashboard money(avg_fare) gone", "money(dem.avg_fare)" not in dash)
    wb = rd(HERE, "cortex_workbook.py")
    check("workbook fare line banded", "fare_bands.band(ec.get" in wb)
    fs_txt = rd(DECK, "forecast_spec.py")
    check("deck assumptions banded",
          '("Measured one-way market fare (band)", _fare_band_label(dem))' in fs_txt)

    print("\n%d checks, %d failed%s" % (CHECKS, len(FAIL),
          ": " + ", ".join(FAIL) if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
