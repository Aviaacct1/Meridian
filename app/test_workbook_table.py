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

        # the Connecting feed sheet (19 August 2026, Jol's review): the top-N city
        # rows plus an All-other row must TOTAL to the same carried leg the Cover
        # prints, and every figure column names the service year
        fc = _fc(grown=True)
        fc["demand"]["behind_pdew"] = [
            {"code": "SEA", "name": "Seattle", "country": "US", "base": 40000,
             "share": 0.06, "forecast": 5000, "pdew": 13.7}]
        fc["demand"]["beyond_pdew"] = [
            {"code": "MNL", "name": "Manila", "country": "PH", "base": 80000,
             "share": 0.03, "forecast": 9000, "pdew": 24.7},
            {"code": "BKK", "name": "Bangkok", "country": "TH", "base": 60000,
             "share": 0.03, "forecast": 6000, "pdew": 16.4}]
        # 20 August 2026 (John, checking the EVA pack): the demand column completes to
        # the full uncapped market the same way the forecast column completes to the
        # carried leg, using feed_behind_base/feed_beyond_base - the same source the
        # shown cities' own "base" figures are drawn from, so additive with them.
        fc["demand"]["feed_behind_base"] = 55000
        fc["demand"]["feed_beyond_base"] = 200000
        out = os.path.join(tmp, "feed.xlsx")
        CWB.build_workbook(out, fc, {"airline_name": "CI", "analyst": "A", "date": "d",
                                     "plan_lf": 0.875, "capture_basis": "m",
                                     "econ_fare": 975})
        wb = openpyxl.load_workbook(out, data_only=True)
        ws = wb["Connecting feed"]
        txt = [[c.value for c in row] for row in ws.iter_rows(min_row=1, max_row=30)]
        flat = ["|".join(str(v) for v in row if v is not None) for row in txt]
        check("feed headers carry the service year",
              any("Market demand 2028" in s for s in flat)
              and any("forecast 2028" in s.lower() for s in flat))
        check("All-other rows drawn on both legs",
              sum(1 for s in flat if "All other connecting markets" in s) == 2)
        # carried_split legs from the fixture: behind 7400, beyond 23200 scaled to
        # connecting_carried 22392 -> behind 5414, beyond 16978
        totals = [row for row in txt if row[0] == "Total"]
        t_beh, t_bey = totals[0][6], totals[1][6]
        check("behind total equals the carried leg", abs(t_beh - 5414) <= 1, t_beh)
        check("beyond total equals the carried leg", abs(t_bey - 16978) <= 1, t_bey)
        t_beh_dem, t_bey_dem = totals[0][4], totals[1][4]
        check("behind demand completes to the full market", t_beh_dem == 55000, t_beh_dem)
        check("beyond demand completes to the full market", t_bey_dem == 200000, t_bey_dem)
        check("note states both columns now reconcile",
              any("both columns now agree" in s for s in flat))

        # the Departure curve sheet (19 August 2026): raw curve + the dashboard's own
        # carried transform + a native chart; must reconcile with the headline at the
        # chosen departure and never exist without an optimiser curve
        fc = _fc(grown=True)
        fc["capacity"]["plan_cap"] = 0.875
        fc["schedule"].update({
            "outbound": {"sector": "SJC-TPE", "dep": "20:59", "arr": "02:44+2"},
            "inbound": {"sector": "TPE-SJC", "dep": "20:14", "arr": "17:59"},
            "indicative": False, "basis": "optimised",
            "optimised": {"unrestricted_dep": "00:30", "restricted": ["21:00-06:00"],
                          "curve": [
                              {"dep": 0, "hhmm": "00:00", "total": 30000, "beyond": 26000,
                               "behind": 4000, "permitted": False},
                              {"dep": 720, "hhmm": "12:00", "total": 12000, "beyond": 9000,
                               "behind": 3000, "permitted": True},
                              {"dep": 1259, "hhmm": "20:59", "total": 15000, "beyond": 11500,
                               "behind": 3500, "permitted": True},
                              {"dep": 1410, "hhmm": "23:30", "total": 26000, "beyond": 22500,
                               "behind": 3500, "permitted": False}]}})
        out = os.path.join(tmp, "curve.xlsx")
        CWB.build_workbook(out, fc, {"airline_name": "BR", "analyst": "A", "date": "d",
                                     "plan_lf": 0.875, "capture_basis": "m",
                                     "econ_fare": 975})
        wb = openpyxl.load_workbook(out)
        check("departure curve sheet exists", "Departure curve" in wb.sheetnames)
        ws = wb["Departure curve"]
        cr = {str(r[0].value): [c.value for c in r] for r in ws.iter_rows(min_row=5, max_row=8)}
        check("curve reconciles with the headline at the chosen departure",
              abs(cr["20:59"][3] - fc["demand"]["connecting_carried"] * 2) < 3
              and abs(cr["20:59"][6] - fc["demand"]["total"] * 2) < 3)
        check("permitted flags carried", cr["00:00"][1] == "no" and cr["12:00"][1] == "yes")
        check("native chart embedded", len(ws._charts) == 1)
        nt = " ".join(str(c.value) for row in ws.iter_rows(min_row=9) for c in row if c.value)
        check("curve note states ceiling and source",
              "aircraft ceiling" in nt and "Meridian analysis" in nt)
        wb2 = openpyxl.load_workbook(os.path.join(tmp, "grown.xlsx"))
        check("no curve, no sheet, never fabricated",
              "Departure curve" not in wb2.sheetnames)
    print("\n%d checks, %d failed%s" % (CHECKS, len(FAIL),
          ": " + ", ".join(FAIL) if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
