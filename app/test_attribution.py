#!/usr/bin/env python3
"""Offline checks for the Sabre attribution pass (audit R3/R4, 18 August 2026).

The Work Order requires "Sabre Global Demand Data" clearly stated wherever it is a
material input. These checks read the client-facing surface files as text and assert
two things per surface: the contractual name is present, and the variant that used to
stand in for it is gone. Text checks, not renders, so they run without stores and
catch a regression the moment a surface is edited.

    py -3.12 test_attribution.py

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(os.path.dirname(HERE), "deck")
sys.path.insert(0, HERE)

FAIL = []
CHECKS = 0
FULL = "Sabre Global Demand Data"


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
    import attribution as A
    check("constant carries the contractual name", A.SABRE_GDD == FULL)
    check("source line carries the contractual name", FULL in A.SOURCE_LINE)

    dash = rd(HERE, "cortex_dashboard.html")
    check("dashboard basis line", FULL in dash)
    check("dashboard rails carry no bare 'Sabre O&D'",
          "provRail('Sabre O&amp;D'" not in dash and "Sabre O&amp;D','Monthly" not in dash)

    for fname, gone in (("cortex_economics.html", None),
                        ("cortex_catchment.html", None),
                        ("cortex_help.html", "measured Sabre origin-and-destination")):
        txt = rd(HERE, fname)
        check("%s carries the full name" % fname, FULL in txt)
        if gone:
            check("%s variant gone" % fname, gone not in txt)

    app_py = {"cortex_app.py": ['"Sabre O&D"', '"Sabre ODPOO"'],
              "cortex_workbook.py": ['"Sabre O&D year"'],
              "methodology_page.py": ["Sabre GDS bookings", "against Sabre MIDT"],
              "track_record.py": ["Sabre MIDT"],
              "airport_profile.py": ['SABRE = "Sabre ODPOO'],
              "pitch_html.py": ["from Sabre origin-and-destination"],
              "pitch_report.py": ["from Sabre point-of-origin traffic in"]}
    for fname, gones in app_py.items():
        txt = rd(HERE, fname)
        check("%s carries the full name" % fname, FULL in txt)
        for g in gones:
            check("%s: %r gone" % (fname, g[:28]), g not in txt)

    fp = rd(DECK, "forecast_pack.py")
    check("forecast_pack SRC contractual", FULL in fp and "Sabre MI and OAG" not in fp)
    check("opportunity slide never drops the source",
          'source=(("%s  %s" % (note, _src(c))) if note else _src(c))' in fp)
    fs = rd(DECK, "forecast_spec.py")
    check("forecast_spec SOURCE contractual", FULL in fs and "Sabre MIDT" not in fs)

    ftc = rd(HERE, "forecast_to_contract.py")
    check("contract _source is set (workbook Source cell)",
          'contract["_source"] = _ATTR' in ftc)

    print("\n%d checks, %d failed%s" % (CHECKS, len(FAIL),
          ": " + ", ".join(FAIL) if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
