#!/usr/bin/env python3
"""Offline test of the track-record page's shipped-configuration arm: the dedicated
loader (no destination lift, the double-correction trap), the card's presence when the
control file exists and its clean absence when it does not, and the two bases named on
the rendered page.

    py -3.12 test_track_control.py

Every number here is a TEST FIXTURE.

Avia Solutions Limited. All rights reserved.
"""
import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import track_record as TR

FAIL = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-58s %s %s" % (name, "PASS" if cond else "FAIL", str(detail)[:70]))
    if not cond:
        FAIL.append(name)


def write_control(path, n=60):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["route", "dep", "arr", "carrier", "year",
                                           "forecast_pax", "outturn_pax", "fc_over_out",
                                           "natural", "p2p_outturn"])
        w.writeheader()
        for i in range(n):
            ratio = 0.7 + (i % 12) * 0.06          # a spread either side of 1.00
            w.writerow({"route": "AAA-B%02d" % i, "dep": "AAA", "arr": "B%02d" % i,
                        "carrier": "XX", "year": 2016 + (i % 4),
                        "forecast_pax": round(50000 * ratio), "outturn_pax": 50000,
                        "fc_over_out": round(ratio, 3),
                        "natural": 60000, "p2p_outturn": 40000})
        # an ungraded row: no outturn ratio, must be skipped not zeroed
        w.writerow({"route": "AAA-ZZZ", "dep": "AAA", "arr": "ZZZ", "carrier": "XX",
                    "year": 2019, "forecast_pax": 1000, "outturn_pax": "",
                    "fc_over_out": "", "natural": 100, "p2p_outturn": ""})


def main():
    with tempfile.TemporaryDirectory() as tmp:
        cp = os.path.join(tmp, "bt_v1_control.csv")
        write_control(cp)
        rows = TR.load_control(cp)
        check("control rows load", len(rows) == 60, len(rows))
        check("ungraded row skipped, not zeroed",
              all(r["ratio"] > 0 for r in rows), "")
        # THE DOUBLE-CORRECTION TRAP: the control loader must return fc_over_out exactly
        # as produced. load_rows applies the destination lift to engine-era files; the
        # control was made by the engine that already carries the fix.
        raw = {}
        for r in csv.DictReader(open(cp)):
            if r["fc_over_out"]:
                raw[r["route"]] = float(r["fc_over_out"])
        check("no destination lift on the control arm",
              all(abs(r["ratio"] - raw[r["route"]]) < 1e-9 for r in rows), "")
        s = TR._stats([r["ratio"] for r in rows])
        control = {"stats": s, "hist": TR._hist([r["ratio"] for r in rows]),
                   "years": sorted({r["year"] for r in rows}), "name": "bt_v1_control.csv"}
        card = TR._control_card(control)
        check("card names the shipped basis",
              "shipped configuration, pinned launch set" in card, "")
        check("card names the calibrated basis as the OTHER basis",
              "calibrated" in card, "")
        check("card carries the evidence file name", "bt_v1_control.csv" in card, "")
        check("no card without a control", TR._control_card(None) == "", "")
        check("no card on empty stats", TR._control_card({"stats": None}) == "", "")
        # the whole-engine page carries the card beside the claim set
        fixture_rows = [{"route": "AAA-BBB", "dep": "AAA", "arr": "BBB", "year": 2018,
                         "region": "Europe", "carrier": "XX", "type": "FSC",
                         "ratio": 1.0 + (i % 9 - 4) * 0.05, "ratio_corr": 1.0,
                         "forecast": 50000.0, "outturn": 50000.0, "forecastable": True}
                        for i in range(40)]
        html = TR.render_total(TR.total_track(fixture_rows), "master_backtest_scored.csv",
                               control=control)
        check("whole-engine page renders the arm beside the claim set",
              "The engine as shipped" in html and "bt_v1_control.csv" in html, "")
        html2 = TR.render_total(TR.total_track(fixture_rows), "master_backtest_scored.csv")
        check("page renders clean without the arm",
              "The engine as shipped" not in html2 and "card" in html2, "")
        # the path resolver honours the env override
        os.environ["AVIA_BT_CONTROL"] = cp
        try:
            import importlib
            importlib.reload(TR)
            check("AVIA_BT_CONTROL override resolves", TR._control_path() == cp,
                  TR._control_path())
        finally:
            del os.environ["AVIA_BT_CONTROL"]
            importlib.reload(TR)
    print("\n%d checks, %d failed%s" % (CHECKS, len(FAIL),
          ": " + ", ".join(FAIL) if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
