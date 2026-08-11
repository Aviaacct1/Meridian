#!/usr/bin/env python3
"""Avia Solutions - acceptance test for the connecting build of 11 August 2026.

Run this after pulling, on the workstation, before anything is built on top. It asserts every number
quoted in commit-message-9-11Aug2026.txt against the engine as it stands, so "the repo produces what
was reported" is a measurement rather than a claim. Anything that moves is printed with expected
against actual rather than swallowed.

    $env:AVIA_OAG   = "C:\\Avia\\oag.duckdb"
    $env:AVIA_SABRE = "C:\\Avia\\sabre.duckdb"
    $env:AVIA_LOCAL_CACHE = "C:\\Avia"
    $env:AVIA_FREQ_SENSITIVE = "1"
    py -3.12 app\\verify_connecting_build.py            # everything, circa four minutes
    py -3.12 app\\verify_connecting_build.py --quick    # skips the departure optimiser

Exits non-zero if any check fails, so it can be wired into a deploy step.

THE VINTAGE MATTERS. Every figure below was measured on OAG week 2026-05-25 and Sabre year 2025. The
script checks the stores first and says so plainly if they have moved on, because a failure against a
newer store is a different thing from a regression and must not be read as one.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

EXPECTED_WEEK, EXPECTED_YEAR = "2026-05-25", 2025
QUICK = "--quick" in sys.argv

FAILS = []
CHECKS = 0


def check(label, got, want, tol=0.0, note=""):
    """One assertion, printed either way. tol is absolute; 0 means exact."""
    global CHECKS
    CHECKS += 1
    if isinstance(want, (int, float)) and isinstance(got, (int, float)):
        ok = abs(float(got) - float(want)) <= tol
        g, w = (f"{got:,.4f}".rstrip("0").rstrip("."), f"{want:,.4f}".rstrip("0").rstrip("."))
    else:
        ok = got == want
        g, w = str(got), str(want)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label:<52} {g:>14}"
          + ("" if ok else f"   expected {w}") + (f"   {note}" if note else ""))
    if not ok:
        FAILS.append(f"{label}: got {g}, expected {w}")


def section(t):
    print(f"\n--- {t}")


def main():
    import duckdb
    oag, sabre = os.environ.get("AVIA_OAG"), os.environ.get("AVIA_SABRE")
    # The environment wins where it is set and correct. Where it is not, look in the two places the
    # stores actually live and SAY which was used. Written 11 August after the run was pointed at
    # C:\Avia on the dev PC, where there are no stores at all: the workstation keeps them on E:.
    # Silence here would read as a code failure when it is a path.
    if not (oag and os.path.exists(oag)) or not (sabre and os.path.exists(sabre)):
        for root in (r"E:\Avia", r"C:\Avia", "/mnt/e/Avia"):
            o, s = os.path.join(root, "oag.duckdb"), os.path.join(root, "sabre.duckdb")
            if os.path.exists(o) and os.path.exists(s):
                if oag or sabre:
                    print(f"  NOTE: AVIA_OAG / AVIA_SABRE did not resolve; using {root}")
                oag, sabre = o, s
                break
    if not (oag and sabre and os.path.exists(oag) and os.path.exists(sabre)):
        print("Could not find the stores. Set AVIA_OAG and AVIA_SABRE, or place oag.duckdb and")
        print("sabre.duckdb under E:\\Avia (workstation) or C:\\Avia.")
        print(f"  AVIA_OAG   = {os.environ.get('AVIA_OAG')!r}")
        print(f"  AVIA_SABRE = {os.environ.get('AVIA_SABRE')!r}")
        return 2
    os.environ["AVIA_OAG"], os.environ["AVIA_SABRE"] = oag, sabre
    print(f"stores: {oag}\n        {sabre}")
    week = duckdb.connect(oag, read_only=True).execute("SELECT max(week) FROM oag").fetchone()[0]
    year = duckdb.connect(sabre, read_only=True).execute(
        "SELECT max(source_year) FROM sabre").fetchone()[0]

    print("Avia Solutions - connecting build acceptance test, 11 August 2026")
    print(f"store vintage: OAG week {week}, Sabre year {year}")
    if (week, year) != (EXPECTED_WEEK, EXPECTED_YEAR):
        print(f"\n  *** STORES HAVE MOVED ON (measured on {EXPECTED_WEEK} / {EXPECTED_YEAR}).")
        print("      Differences below are a data change, NOT a regression. Re-baseline the")
        print("      expected values before reading any failure as a fault.")
    print(f"AVIA_FREQ_SENSITIVE = {os.environ.get('AVIA_FREQ_SENSITIVE')!r}")

    # The environment fingerprint, printed with every run. Written 11 August after this test
    # returned qsi_share 0.2513 on one machine against 0.2510 on another, reading the same stores
    # and the same commit. A failing number without the environment beside it costs an hour to
    # place; with it, the diff is one line. Same reason env_report.py exists.
    import platform
    vers = []
    for mod in ("duckdb", "airportsdata"):
        try:
            vers.append(f"{mod} {__import__(mod).__version__}")
        except Exception:
            try:
                from importlib.metadata import version as _v
                vers.append(f"{mod} {_v(mod)}")
            except Exception:
                vers.append(f"{mod} ?")
    try:
        import global_land_mask  # noqa: F401
        water = "ON"
    except Exception:
        water = "OFF"
    print(f"environment: python {platform.python_version()}, {', '.join(vers)}, "
          f"water check {water}")

    section("1. QSI coefficients, the frozen method")
    import qsi_score as Q
    check("two-stop service coefficient", Q.TWOSTOP_COEFF, 0.04, note="was 0.40, DOT 10/2/0.4")
    check("one-stop service coefficient", Q.ONESTOP_COEFF, 0.20)
    check("alliance connection coefficient", Q.CNX_COEFF["ALLIANCE"], 0.75)
    check("interline is weighted, not excluded", Q.CNX_COEFF["INTERLINING"], 0.25)
    check("elapsed-time curve at +0.1h", round(Q.et_coeff(0.1), 3), 0.574)

    section("2. The hub arrival is in the HUB's local time")
    import qsi_feed as QF
    check("SJC 11:00 + 825min block -> TPE local", QF._hub_arrival_mins("SJC", "TPE", 660, 825, {}),
          1005, note="16:45, was 00:45")
    check("SJC 12:00 -> TPE local", QF._hub_arrival_mins("SJC", "TPE", 720, 825, {}), 1065,
          note="17:45")
    check("an explicit hub_arr_mins overrides",
          QF._hub_arrival_mins("SJC", "TPE", 720, 825, {"hub_arr_mins": 930}), 930)

    section("3. Alliance classification, both sides normalised")
    check("DL SkyTeam onto CI ST", QF._cnx_type("DL", "SkyTeam", "CI", "ST"), "ALLIANCE")
    check("UA Star onto CI ST", QF._cnx_type("UA", "Star Alliance", "CI", "ST"), "INTERLINING")
    check("UA Star onto BR *A", QF._cnx_type("UA", "Star Alliance", "BR", "*A"), "ALLIANCE")
    check("two unaligned carriers are NOT partners", QF._cnx_type("WN", "0", "B6", "0"),
          "INTERLINING", note="'0' must not compare equal")
    check("same carrier is online", QF._cnx_type("KE", "SkyTeam", "KE", "SkyTeam"), "ONLINE")

    section("4. OAG boards deduped, day masks unioned")
    from wave_cache import OagBoards, carrier_flights
    boards = OagBoards(oag)
    tpe, sjc = boards.dep_rows(week, "TPE"), boards.arr_rows(week, "SJC")
    check("TPE departure board, distinct flights", len(tpe), 448, note="2,495 raw rows")
    check("SJC arrival board, distinct flights", len(sjc), 331, note="930 raw rows")
    yvr = [r for r in tpe if r["arr"] == "YVR" and r["carrier"] == "BR"]
    check("BR TPE-YVR appears once", len(yvr), 1, note="14 raw rows")
    check("BR TPE-YVR weekly frequency", (yvr[0]["freq"] if yvr else 0), 7.0)
    xmn = [r for r in tpe if r["arr"] == "XMN" and r["carrier"] == "AE" and r["dep_mins"] == 520]
    check("AE TPE-XMN masks unioned to daily", (xmn[0]["freq"] if xmn else 0), 7.0,
          note="'123 5 7' + '   4 6 '")

    section("5. Carrier counts are distinct flights, not raw rows")
    import route_feed as RF
    check("hub_dominance CI at TPE", round(RF.hub_dominance(oag, week, "TPE", "CI"), 5), 0.18080,
          tol=0.00002, note="0.21002 on raw rows")
    check("hub_dominance BR at TPE", round(RF.hub_dominance(oag, week, "TPE", "BR"), 5), 0.18527,
          tol=0.00002, note="0.24690 on raw rows")

    section("6. Restricted hours: nothing assumed by default")
    check("no origin restriction by default", RF.parse_windows(None), [])
    check("window parses", RF.parse_windows("23:00-06:00"), [(1380, 360)])
    check("23:30 is inside 23:00-06:00", RF.in_window(1410, [(1380, 360)]), True)
    check("06:00 is outside", RF.in_window(360, [(1380, 360)]), False)
    check("22:30 is outside", RF.in_window(1350, [(1380, 360)]), False)

    section("7. Partner carriers: empty unless named")
    check("no partners by default", QF.partner_map("CI", None), {})
    check("Southwest named as CI's partner", QF.partner_map("CI", ["WN"]), {"WN": "ST"})

    section("8. Engine anchors that must NOT have moved")
    # forecast_year is PINNED TO THE BASE YEAR here so growth_years is zero. These anchors measure
    # the engine core on the data as it stands; the default output is now the year AFTER the base,
    # which grows the market and every figure derived from it. Leaving the year unpinned made all
    # three read 1.20x on 11 August, which is the growth working, not a regression.
    import cortex_app as CA
    r = CA.calibrated_forecast("SJC", "TPE", airline="CI", carrier_type="FSC",
                               aircraft="A359", seats=306, freq=4, dep_time_mins=720,
                               forecast_year=EXPECTED_YEAR)
    d = r["demand"]
    # qsi_share IS KEYED TO THE airportsdata RELEASE, deliberately, rather than hidden behind a
    # loose tolerance. The library supplies every coordinate the engine uses, so a corrected airport
    # position shifts a circuity screen and moves the share: 0.2510 on 20260315 and 0.2513 on
    # 20260803, same commit, same stores, measured 11 August 2026. requirements.txt pins 20260803.
    # A tolerance wide enough to swallow both would also swallow a real regression, and this file
    # already carries three instances of a scoring basis drifting because a band was loosened.
    try:
        _adv = str(__import__("airportsdata").__version__)
    except Exception:
        _adv = "?"
    _want_qsi = 0.2513 if _adv >= "20260803" else 0.2510
    check("qsi_share", round(d["qsi_share"], 4), _want_qsi, tol=0.0001,
          note=f"expected for airportsdata {_adv}")
    check("measured market, each way", round(d["natural"]), 160915, tol=1)
    check("beyond base, each way", round(d["feed_beyond_base"]), 608084, tol=1)
    check("behind base, each way", round(d["feed_behind_base"]), 156765, tol=1)

    section("9. The raw connecting feed against the 2025 analyst, his 12:00 schedule")
    import route_engine as RE
    ap = RE._airports()
    comp = [x["iata"] for x in RE.competing_airports(ap["SJC"], 220.0, None, True)]
    base = dict(behind_cap=0.10, dom_gain=1.0, dom_floor=1.0, cnx_online=1.0, cnx_alliance=0.615,
                cnx_interline=0.25, circuity=1.35, factor_indirect=1.044, mct_banking=False,
                qsi_feed=True, dep_time_mins=720, flying_mins=825, route_freq=4,
                route_origin="SJC", qsi_k=1.0, qsi_k_behind=1.0)
    for lbl, partners, wb, wh in (("no partner named", None, 12583, 5967),
                                  ("Southwest a partner", ["WN"], 12467, 11613)):
        cfg = dict(base)
        if partners:
            cfg["partner_carriers"] = partners
        bt, _, _ = RF.feed_side(sabre, oag, week, comp, "TPE", year, beyond=True,
                                airline="CI", feed_cfg=dict(cfg), detail=True)
        ht, _, _ = RF.behind_feed(sabre, oag, week, ["SJC"], ["TPE"], year,
                                  airline="CI", feed_cfg=dict(cfg), detail=True)
        check(f"beyond two-way, {lbl}", round(2 * bt), wb, tol=2,
              note=f"analyst 12,007 = {2 * bt / 12007:.2f}x")
        check(f"behind two-way, {lbl}", round(2 * ht), wh, tol=2,
              note=f"analyst 13,992 = {2 * ht / 13992:.2f}x")

    if not QUICK:
        section("10. Departure optimiser, and the San Jose night restriction")
        CA.S.clear()
        r1 = CA.calibrated_forecast("SJC", "TPE", airline="CI", carrier_type="FSC",
                                    aircraft="A359", seats=306, freq=4)
        check("CI optimised departure", r1["schedule"]["outbound"]["dep"], "00:30",
              note="CI flies SFO-TPE at 01:05")
        check("CI optimised arrival at TPE", r1["schedule"]["outbound"]["arr"], "06:15+1")
        CA.S.clear()
        r2 = CA.calibrated_forecast("SJC", "TPE", airline="CI", carrier_type="FSC",
                                    aircraft="A359", seats=306, freq=4,
                                    restricted_hours="23:00-06:00")
        o2 = r2["schedule"]["optimised"] or {}
        check("under a 23:00-06:00 curfew", r2["schedule"]["outbound"]["dep"], "06:30")
        check("return arrival clears the curfew", o2.get("return_arrival"), "12:00")
        check("the unrestricted optimum is reported", o2.get("unrestricted_dep"), "00:30")
    else:
        print("\n--- 10. departure optimiser SKIPPED (--quick)")

    section("11. The forecast year, and the analyst's total on his own basis")
    import json as _json
    basis = _json.loads(CA.api_basis().body.decode())
    check("/api/basis reports the Sabre base year", basis.get("sabre_year"), EXPECTED_YEAR)
    check("default forecast year is base + 1", basis.get("default_forecast_year"), EXPECTED_YEAR + 1)
    check("ten years offered", len(basis.get("years") or []), 10)

    # The analyst's SJC-TPE deck is YE Jun 2028 at 4x: 107,857 two-way at 86.4% on 124,800 seats.
    # Run on HIS basis - his 12:00 schedule, Southwest counted as a partner as his scope states, the
    # connectivity floor off because the QSI feed no longer under-reads, and grown to his year.
    r = CA.calibrated_forecast("SJC", "TPE", airline="CI", carrier_type="FSC", aircraft="A359",
                               seats=306, freq=4, dep_time_mins=720, partner_carriers="WN",
                               split_floor=False, forecast_year=2028)
    tot = 2 * r["demand"]["total"]
    check("total two-way, YE2028 basis", round(tot), 111384, tol=2,
          note=f"analyst 107,857 = {tot / 107857:.2f}x")
    check("within 10% of the analyst deck, and OVER", 1.0 <= tot / 107857 <= 1.10, True)

    print(f"\n{'=' * 74}")
    if FAILS:
        print(f"{len(FAILS)} of {CHECKS} checks FAILED:")
        for f in FAILS:
            print(f"   {f}")
        return 1
    print(f"ALL {CHECKS} CHECKS PASSED. The repo reproduces the 11 August connecting build.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
