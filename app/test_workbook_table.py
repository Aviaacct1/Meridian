#!/usr/bin/env python3
"""Offline end-to-end check of the workbook's Traffic forecast table (18 August
2026): builds a real workbook from a synthetic payload and reads the table back.
The three invariants a network planner checks in the room, plus the decomposition:

  1. the rows SUM to the grand total (the carried allocation),
  2. each row MULTIPLIES through (stimulated x capture = forecast),
  3. base year / growth / grown are decomposed with year-labelled headers,
  4. a steady-state run prints base = grown with growth 0, as before.

    py -3.12 test_workbook_table.py

Every figure here is a TEST FIXTURE.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cortex_workbook as CWB
import openpyxl

FAIL = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-62s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


def _fc(grown=True):
    sch = {"forecast_year": 2028, "base_year": 2025, "growth_rate": 0.0223,
           "growth_years": 3, "growth_basis": "measured pre-COVID trend, tapered",
           "legs": []} if grown else {"legs": []}
    return {
        "ok": True, "origin": {"city": "San Jose", "iata": "SJC", "country": "US"},
        "dest": {"city": "Taipei", "iata": "TPE", "country": "TW"},
        "distance_nm": 5637, "block_min": 825, "week": "2026-05-25", "year": 2025,
        "carrier_type": "FSC", "schedule": sch,
        "demand": {"natural": 203400, "captured": 45400, "qsi_share": 0.251,
                   "stimulation": 1.15, "feed_behind": 7400, "feed_beyond": 23200,
                   "feed_behind_base": 198200, "feed_beyond_base": 768800,
                   "p2p_carried": 33300, "connecting_carried": 22392,
                   "total": 55692, "total_demand": 76000, "pdew_total": 152.6,
                   "beyond_pdew": [], "behind_pdew": [],
                   "avg_fare_band": {"label": "950-1000"}},
        "capacity": {"carried": 55692, "load": 0.875, "freq": 4, "aircraft": "A359",
                     "annual_capacity": 63648, "recommendation": ""},
        "catchment": {"observed_share": {}, "names": {}, "home": "SJC"},
        "economics": {"raw": {}, "econ_fare": 975, "seats": 306},
        "season": {"mode": "annual", "share": 1.0, "weeks": 52},
    }


def _table(fc, tmp, name):
    out = os.path.join(tmp, name)
    CWB.build_workbook(out, fc, {"airline_name": "CI", "analyst": "Avia Solutions",
                                 "date": "18 Aug 2026", "plan_lf": 0.875,
                                 "capture_basis": "measured", "econ_fare": 975})
    wb = openpyxl.load_workbook(out, data_only=True)
    fs = wb["Forecast"]
    return {str(r[0].value): [c.value for c in r]
            for r in fs.iter_rows(min_row=4) if r[0].value}


def main():
    with tempfile.TemporaryDirectory() as tmp:
        rows = _table(_fc(grown=True), tmp, "grown.xlsx")
        hdr, p2p, gt = rows["Market"], rows["Total point to point"], rows["GRAND TOTAL"]
        legs = [rows[k][7] for k in rows
                if k.startswith("Total ") and "point" not in k]
        check("year-labelled headers", "2025" in str(hdr[1]) and "2028" in str(hdr[3]))
        check("base decomposed from grown", abs(p2p[1] - 190.4) < 0.5, p2p[1])
        check("cumulative growth printed", abs(p2p[2] - 0.0684) < 0.003, p2p[2])
        check("grown column carries the grown market", abs(p2p[3] - 203.4) < 0.1)
        check("row multiplies through (effective capture)",
              abs(p2p[5] * p2p[6] - p2p[7]) < 0.6)
        check("rows sum to the grand total",
              abs(p2p[7] + sum(legs) - gt[7]) < 0.15,
              "%s + %s = %s" % (p2p[7], legs, gt[7]))
        check("grand total base column summed", abs(gt[1] - 1095.5) < 0.5, gt[1])
        rows = _table(_fc(grown=False), tmp, "steady.xlsx")
        p2p = rows["Total point to point"]
        check("steady state: base equals grown", p2p[1] == p2p[3])
        check("steady state: growth prints zero", (p2p[2] or 0) == 0)
    print("\n%d checks, %d failed%s" % (CHECKS, len(FAIL),
          ": " + ", ".join(FAIL) if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
