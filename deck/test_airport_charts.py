#!/usr/bin/env python3
"""Offline test of the four airport charts. Renders real PNGs to a temp folder.

    py -3.12 test_airport_charts.py
    py -3.12 test_airport_charts.py --keep C:\\Avia\\chart_check

What this checks is mostly what the charts REFUSE to do, because the failure
mode that matters is not a crash, it is a chart that draws something plausible
and wrong: a passenger series with the pandemic quietly bridged, a seat count
captioned as passengers, a load factor over 100%.

Every number here is a TEST FIXTURE.

Avia Solutions Limited. All rights reserved.
"""
import argparse
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import avia_charts as AC

FAIL = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-58s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


ap = argparse.ArgumentParser()
ap.add_argument("--keep", default="", help="folder to write the PNGs to and keep")
a = ap.parse_args()
out = a.keep or tempfile.mkdtemp(prefix="avia_charts_")
if not os.path.isdir(out):
    os.makedirs(out)


def p(name):
    return os.path.join(out, name)


def drawn(path):
    return bool(path) and os.path.exists(path) and os.path.getsize(path) > 5000


# --- 1. passengers a year, with a hole in the middle --------------------------
# The shape airport_profile actually returns for a European airport: complete
# years either side of a gap the store does not hold.
pax = [(2015, 11.11e6), (2016, 12.35e6), (2017, 13.43e6), (2018, 14.31e6),
       (2019, 14.81e6), (2020, 3.46e6), (2021, 3.03e6), (2022, 11.26e6),
       (2023, 14.41e6), (2024, 15.79e6), (2025, 16.98e6)]
f1 = AC.airport_pax(p("pax.png"), series=pax, airport="Edinburgh",
                    label="ACI airport traffic")
check("the passenger chart renders", drawn(f1), f1)
check("two points cannot make a series",
      AC.airport_pax(p("x.png"), series=pax[:2], airport="X", label="ACI") is None)
check("no data draws nothing rather than an empty frame",
      AC.airport_pax(p("x.png"), series=[], airport="X", label="ACI") is None)

# --- 2. the haul split, which is CAPACITY and must not read as traffic --------
haul = {y: {"Domestic": d, "International": i} for y, d, i in [
    (2017, 3.1e6, 2.4e6), (2018, 3.3e6, 2.7e6), (2019, 3.4e6, 2.9e6),
    (2023, 3.0e6, 3.1e6), (2024, 3.1e6, 3.4e6), (2025, 3.2e6, 3.7e6)]}
f2 = AC.airport_haul(p("haul.png"), haul=haul, airport="Edinburgh")
check("the haul split renders", drawn(f2), f2)
check("a two-year split is not a trend",
      AC.airport_haul(p("x.png"), haul={2023: {"Domestic": 1.0}}, airport="X") is None)
check("an all-zero split draws nothing",
      AC.airport_haul(p("x.png"), airport="X", haul={
          y: {"Domestic": 0.0, "International": 0.0}
          for y in (2021, 2022, 2023)}) is None)

# --- 3. the airline picture ----------------------------------------------------
airlines = [("FR", 4.10e6, 38), ("U2", 3.05e6, 31), ("BA", 1.42e6, 4),
            ("KL", 0.51e6, 1), ("LH", 0.34e6, 3), ("AF", 0.22e6, 2)]
f3 = AC.airport_airlines(p("airlines.png"), airlines=airlines,
                         airport="Edinburgh", year=2025)
check("the airline chart renders", drawn(f3), f3)
check("two carriers are not a competitive picture",
      AC.airport_airlines(p("x.png"), airlines=airlines[:2], airport="X",
                          year=2025) is None)
check("a carrier with no seats is not plotted",
      AC.airport_airlines(p("x.png"), airport="X", year=2025,
                          airlines=[("AA", 0, 1), ("BB", 0, 1), ("CC", 0, 1)]) is None)

# --- 4. effective load factor ---------------------------------------------------
lf = [(2017, 0.812), (2018, 0.826), (2019, 0.841), (2023, 0.788),
      (2024, 0.803), (2025, 0.815)]
f4 = AC.airport_load(p("load.png"), series=lf, airport="Edinburgh",
                     pax_label="ACI airport traffic", halved=True)
check("the load factor chart renders", drawn(f4), f4)
check("a single year is not a load factor series",
      AC.airport_load(p("x.png"), series=lf[:1], airport="X",
                      pax_label="ACI") is None)

# --- 5. the labelling rules, read off the rendered figure ----------------------
# A chart has to stand alone: unit, period, actual or forecast, and a source.
# These are asserted on the text the chart carries, not on the picture.
import matplotlib.pyplot as plt


def texts(fn, **kw):
    """Render once more and collect every string the figure carries."""
    got = {}
    real = AC._finish

    def spy(fig, ax, title, sub, ylab, source, path, legend=True):
        got.update({"title": title, "sub": sub or "", "ylab": ylab or "",
                    "source": source or ""})
        return real(fig, ax, title, sub, ylab, source, path, legend)

    AC._finish = spy
    try:
        fn(**kw)
    finally:
        AC._finish = real
        plt.close("all")
    return got


t1 = texts(AC.airport_pax, path=p("t1.png"), series=pax, airport="Edinburgh",
           label="ACI airport traffic", absent=(2020, 2021, 2022))
check("the passenger chart names its period", "2015-2025" in t1["sub"], t1["sub"][:40])
check("and says whether it is actual or forecast", "(actual)" in t1["sub"])
check("the pandemic years are explained by the band, not listed twice",
      "2020, 2021, 2022" not in t1["sub"] and "shaded" in t1["sub"].lower(),
      t1["sub"])
t1b = texts(AC.airport_pax, path=p("t1b.png"), airport="X",
            label="ACI airport traffic", absent=(2016,),
            series=[(2015, 1e6), (2017, 1.1e6), (2018, 1.2e6), (2019, 1.3e6)])
check("but a gap OUTSIDE the pandemic is still named",
      "no figure for 2016" in t1b["sub"], t1b["sub"])
check("and quotes growth with the span it was measured over",
      "a year compound 2015-2025" in t1["sub"], t1["sub"])
check("and carries a source", "ACI" in t1["source"] and "Avia" in t1["source"])
check("and its axis says passengers", "Passengers" in t1["ylab"], t1["ylab"])

t2 = texts(AC.airport_haul, path=p("t2.png"), haul=haul, airport="Edinburgh")
check("the capacity chart says SEATS on the axis, not passengers",
      "Seats" in t2["ylab"] and "assenger" not in t2["ylab"], t2["ylab"])
check("and says seats in the title too, so it cannot be read as traffic",
      "seats" in t2["title"].lower(), t2["title"])
check("and states the direction, since seats are one way",
      "one direction" in t2["sub"], t2["sub"])
check("and is attributed to OAG, which is schedules",
      "OAG" in t2["source"], t2["source"])

t3 = texts(AC.airport_airlines, path=p("t3.png"), airlines=airlines,
           airport="Edinburgh", year=2025)
check("the airline chart states its single year", "2025" in t3["sub"], t3["sub"])
check("and says what the share is a share OF",
      "share is of the airlines shown" in t3["sub"].lower(), t3["sub"])

t4 = texts(AC.airport_load, path=p("t4.png"), series=lf, airport="Edinburgh",
           pax_label="ACI airport traffic", halved=True)
check("the load factor chart names BOTH sources",
      "OAG" in t4["source"] and "ACI" in t4["source"], t4["source"])
check("and discloses the halving rather than burying it",
      "halved" in t4["sub"] and "approximation" in t4["sub"], t4["sub"])
t4b = texts(AC.airport_load, path=p("t4b.png"), series=lf, airport="X",
            pax_label="US DOT T-100 segment", halved=False)
check("and says nothing about halving when nothing was halved",
      "halved" not in t4b["sub"], t4b["sub"])

# --- 6. the two defects reading the rendered figures caught -------------------
# Neither of these was visible in the checks above, which is the point of them.

# A line plotted only at the years it has joins 2019 to 2023 and draws a gentle
# four-year decline through a hole. The series must carry a break.
import math
captured = {}
_real_plot = AC.plt.Axes.plot


def spy_plot(self, *args, **kw):
    if len(args) >= 2 and hasattr(args[1], "__iter__"):
        captured["x"], captured["y"] = list(args[0]), list(args[1])
    return _real_plot(self, *args, **kw)


AC.plt.Axes.plot = spy_plot
try:
    AC.airport_load(p("gap.png"), series=lf, airport="Edinburgh",
                    pax_label="ACI airport traffic", halved=True)
finally:
    AC.plt.Axes.plot = _real_plot
    plt.close("all")
check("the load factor line covers every year in the span",
      captured.get("x") == list(range(2017, 2026)), captured.get("x"))
check("and BREAKS at the years with no figure, never bridging them",
      [i for i, v in enumerate(captured.get("y", [])) if isinstance(v, float)
       and math.isnan(v)] == [3, 4, 5], captured.get("y"))

# Four million seats is not "4100k".
check("a volume over a million reads in millions", AC._volume(4.10e6) == "4.1m",
      AC._volume(4.10e6))
check("millions carry one decimal, consistently", AC._volume(3.0e6) == "3.0m",
      AC._volume(3.0e6))
check("so 3.05m is never printed as a flat 3m",
      AC._volume(3.05e6) == "3.0m" and AC._volume(3.05e6) != "3m",
      AC._volume(3.05e6))
check("and above ten million the decimal goes", AC._volume(16.98e6) == "17m",
      AC._volume(16.98e6))
check("and under a million stays in thousands", AC._volume(510000) == "510k",
      AC._volume(510000))
check("zero is zero, not 0m", AC._volume(0) == "0", AC._volume(0))

# The airline chart should not go to a client saying "FR" and "U2".
t5 = texts(AC.airport_airlines, path=p("t5.png"), airlines=airlines,
           airport="Edinburgh", year=2025,
           names={"FR": "Ryanair", "U2": "easyJet", "BA": "British Airways"})
check("the airline chart accepts real airline names", drawn(p("t5.png")))

print("\nPNGs in %s" % out)
print("\n%d checks, %d failed" % (CHECKS, len(FAIL)))
if FAIL:
    print("FAILED: %s" % ", ".join(FAIL))
sys.exit(1 if FAIL else 0)
