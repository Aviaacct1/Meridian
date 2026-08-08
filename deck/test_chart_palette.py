#!/usr/bin/env python3
r"""Every colour in the deck charts comes from the Observatory palette, and no brand colour fills
a series.

Written 8 August 2026, the day the deck charts were found to be using twenty colours of which not
one appeared in Observatory Brand Guidelines v1.3: #002060 and #00B0F0 are Office theme defaults,
#FFA800 an amber, #2E8B57 the CSS named seagreen, #C0392B a Flat UI red. Those charts go into
client decks.

WHY THIS SUITE EXISTS AT ALL. test_airport_charts.py has 36 checks and every one passed while the
palette was wrong, because they check what a chart SAYS: its title, its unit, its period, whether
actual is distinguished from forecast, whether it carries a source, whether a line breaks at a
missing year. Not one of them checks what it looks like. The same pattern accounts for six of the
eight defects recorded in the 8 August handover, all of which passed a green suite and were caught
only by reading the rendered page. A test that cannot see a fault will not stop it returning.

The two rules from section 5 of the guide, which are what this asserts:

    "Brand colour identifies; data colour distinguishes. They stay apart."
    "Assign hues in the fixed order, brass first, always the observed series."

and Signal Red is reserved for averages, targets, thresholds and alerts, never a category.

    py -3.12 test_chart_palette.py

Avia Solutions Limited. All rights reserved.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import avia_charts as AC                                          # noqa: E402

SRC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "avia_charts.py")
SRC = open(SRC_PATH, encoding="utf-8").read()

# The guide's own hexes, typed out here rather than imported, so this suite fails if the module
# ever redefines one. A test that reads its expected values from the thing under test proves only
# that the file agrees with itself.
GUIDE = {
    "S1_BRASS": "#D4A249", "S2_PRUSSIAN": "#3D6A88", "S3_VERDIGRIS": "#5F8D7A",
    "S4_OXBLOOD": "#A9553F", "S5_SLATE": "#8793A0", "S6_PLUM": "#7B617F",
    "S7_OLIVE": "#9C8A4E", "SIGNAL_RED": "#CE3B2A",
}
# Brand and structural tones. These may carry type, axes, gridlines and grounds. They may NOT
# fill a data series, which is the whole of the fault this suite guards.
STRUCTURAL = ("INK", "BODY", "MUTED", "AXIS", "GRID", "PAPER", "NAVY", "GREY")
# Calls that put ink on a data mark rather than on type.
FILL_CALLS = r"ax\.(?:bar|barh|plot|fill_between|scatter|pie|stackplot)\("

checks = failed = 0


def check(label, cond, note=""):
    global checks, failed
    checks += 1
    ok = bool(cond)
    if not ok:
        failed += 1
    print("%-58s %s %s" % (label, "PASS" if ok else "FAIL", note))


# --- the guide's values, exactly -----------------------------------------------------------
for name, hexv in GUIDE.items():
    check("%s is the guide's hex" % name, getattr(AC, name, None) == hexv,
          "%s vs %s" % (getattr(AC, name, None), hexv))

# --- no colour from outside the sanctioned set ---------------------------------------------
# Only hexes inside quotes, so a colour NAMED in a comment is not read as a colour USED in code.
# The first run of this suite failed on its own documentation: the palette block explains what each
# retired hue was ("was #FFA800", and so on) and a bare regex counted those as live literals.
literals = sorted({h.upper() for h in re.findall(r"""["']\s*(#[0-9A-Fa-f]{6})\s*["']""", SRC)})
sanctioned = {c.upper() for c in AC.SANCTIONED if isinstance(c, str) and c.startswith("#")}
stray = [h for h in literals if h not in sanctioned]
check("every hex in the module is in SANCTIONED", not stray, stray or "%d literals" % len(literals))

# The old palette by name, so a revert is caught even if it is renamed on the way back in.
RETIRED = ["#021D49", "#002060", "#FFA800", "#00B0F0", "#1F6FB2", "#145A6E",
           "#8A8A8A", "#C9D9EC", "#2E8B57", "#C0392B", "#B7C2D2", "#E3E9F1",
           "#B37600", "#E4EEF8", "#5A7EA6", "#8FAECD", "#F2F5F9", "#DCEAF6",
           "#EFF3E8", "#BFCBD8"]
back = [h for h in RETIRED if h.upper() in literals]
check("none of the twenty retired colours is back", not back, back or "clean")

# --- no brand or structural tone filling a data series -------------------------------------
# One deliberate exception, commented at its call site: the two airport locator markers on the
# route map, which are type furniture beside their labels and would vanish into the route line.
ALLOWED_STRUCTURAL_FILLS = 1
fills = []
for line_no, line in enumerate(SRC.splitlines(), start=1):
    if re.search(FILL_CALLS, line) or re.match(r"\s*(cols|colors)\s*=", line):
        for tone in STRUCTURAL:
            if re.search(r"\b%s\b" % tone, line):
                fills.append((line_no, tone, line.strip()[:70]))
check("no structural tone fills a series, bar the documented one",
      len(fills) <= ALLOWED_STRUCTURAL_FILLS,
      "%d found: %s" % (len(fills), [(n, t) for n, t, _ in fills]))

# --- Signal Red is reserved -----------------------------------------------------------------
red_fills = []
for line_no, line in enumerate(SRC.splitlines(), start=1):
    if re.match(r"\s*(cols|colors)\s*=", line) and re.search(r"SIGNAL_RED|RED_LINE", line):
        red_fills.append(line_no)
    if re.search(r"ax\.(?:bar|barh|pie|stackplot|fill_between)\(", line) and \
            re.search(r"SIGNAL_RED|RED_LINE", line):
        red_fills.append(line_no)
check("Signal Red never fills a category", not red_fills, red_fills or "reserved for thresholds")
check("Signal Red is still used for a threshold rule",
      re.search(r"ax\.plot\([^)]*(SIGNAL_RED|RED_LINE)", SRC) is not None,
      "the guide's DO: show a target as a Signal Red rule")

# --- the observed series is brass ------------------------------------------------------------
check("MID, the primary series alias, is brass", AC.MID == GUIDE["S1_BRASS"], AC.MID)
check("the retired aliases point at data colours, not brand",
      AC.ORANGE in GUIDE.values() and AC.CYAN in GUIDE.values(),
      "%s, %s" % (AC.ORANGE, AC.CYAN))

# --- the ramp is brass-derived, so muting a series stays in its own hue ----------------------
check("the covid bar is a step of the observed series, not a second hue",
      AC.COVID_BAR in (AC.RAMP_PALE, AC.RAMP_LIGHT, AC.RAMP_DEEP), AC.COVID_BAR)
check("the covid band is the pale end of the ramp",
      AC.COVID_BAND in (AC.RAMP_PALE, AC.GRID, AC.PAPER), AC.COVID_BAND)

# --- unused constants are gone, not remapped ------------------------------------------------
check("TEAL is gone", not hasattr(AC, "TEAL"))
check("GREEN is gone", not hasattr(AC, "GREEN"))

print("\n%d checks, %d failed" % (checks, failed))
sys.exit(1 if failed else 0)
