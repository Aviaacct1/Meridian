"""Avia house-style charts for the route-pitch deck generator.

Every chart carries its own title, unit and period so it stands alone on the
slide, per Avia chart-labelling rules. Actual and forecast are always distinguished.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os

# ---------------------------------------------------------------------------
# PALETTE. Observatory Brand Guidelines v1.3, section 5. Replaced 8 August 2026.
#
# Until then this module carried its own palette of ten colours, none of which appeared in the
# brand guide: #002060 and #00B0F0 are Office theme defaults, #FFA800 an amber, #2E8B57 the CSS
# named seagreen, #C0392B a Flat UI red. These charts go into client decks, so the deck was
# arriving in a scheme the brand does not contain. The 36 checks in test_airport_charts.py all
# passed throughout, because they check what a chart SAYS, its title, unit, period, source and
# gap handling, and nothing checks what it looks like.
#
# The guide's two rules that decide everything below:
#   "Brand colour identifies; data colour distinguishes. They stay apart."
#   "Assign hues in the fixed order, brass first, always the observed series."
# and Signal Red is reserved for averages, targets and thresholds, never a category.
#
# STRUCTURE, not series. Ink and body carry type and axes; they must never fill a series.
INK        = "#0F1B28"      # titles, direct labels
BODY       = "#26313B"      # axis labels, tick labels, body type
MUTED      = "#6E6A5E"      # source lines, de-emphasised annotation
AXIS       = "#C9C2B2"      # axis spines
GRID       = "#E2DCCC"      # gridlines
PAPER      = "#F6F3EC"      # figure ground

# CATEGORICAL SERIES, assigned in the guide's fixed order. S3 is Verdigris everywhere, so these
# names are the series numbers and not the colours: renaming a hue must not renumber a series.
S1_BRASS     = "#D4A249"    # always the observed series
S2_PRUSSIAN  = "#3D6A88"
S3_VERDIGRIS = "#5F8D7A"
S4_OXBLOOD   = "#A9553F"
S5_SLATE     = "#8793A0"    # de-emphasised or "other" categories
S6_PLUM      = "#7B617F"
S7_OLIVE     = "#9C8A4E"

# SEQUENTIAL RAMP, for one measure by intensity and for muting within a series.
RAMP_PALE  = "#F1E6CD"
RAMP_LIGHT = "#E4C489"
RAMP_DEEP  = "#A97C33"      # brass-deep, for a direct label on the observed series

# RESERVED. Averages, targets, thresholds, alerts. Never a category.
SIGNAL_RED = "#CE3B2A"

# The set any colour in this module must come from. Asserted by test_chart_palette.py so the
# scheme cannot drift back one inline hex at a time, which is how it drifted in the first place.
SANCTIONED = {INK, BODY, MUTED, AXIS, GRID, PAPER,
              S1_BRASS, S2_PRUSSIAN, S3_VERDIGRIS, S4_OXBLOOD, S5_SLATE, S6_PLUM, S7_OLIVE,
              RAMP_PALE, RAMP_LIGHT, RAMP_DEEP, SIGNAL_RED, "white"}

# Names the rest of the module already uses, mapped to their role rather than their old hue.
NAVY     = INK              # was #021D49, used for titles and bold direct labels
ORANGE   = S2_PRUSSIAN      # was #FFA800, the second series in a stack or a grouped pair
CYAN     = S3_VERDIGRIS     # was #00B0F0, the third series
MID      = S1_BRASS         # was #1F6FB2, the PRIMARY series: brass, per the guide
GREY     = MUTED            # was #8A8A8A, source line and de-emphasised type
LIGHT    = RAMP_LIGHT       # was #C9D9EC, a muted step of the observed series
RED_LINE = SIGNAL_RED       # was #C0392B, a threshold rule: the guide's sanctioned use

# TEAL (#145A6E) and GREEN (#2E8B57) were defined and never used. Removed rather than remapped:
# an unused colour constant is a hue waiting to be spent without a decision.

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.edgecolor": AXIS,
    "axes.labelcolor": BODY,
    "text.color": BODY,
    "xtick.color": BODY,
    "ytick.color": BODY,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
})


def _finish(fig, ax, title, sub, ylab, source, path, legend=True):
    # The subtitle is WRAPPED, not left to run. A long one used to overflow the
    # right edge and, because it is a child of the axes, tight_layout shrank the
    # plot to make room for text that was off the page anyway: the load factor
    # chart came out squeezed into the left half of its own frame.
    lines = []
    if sub:
        import textwrap
        lines = textwrap.wrap(sub, 108) or [sub]
    ax.set_title(title, fontsize=12.5, fontweight="bold", color=NAVY,
                 loc="left", pad=16 + 13 * max(0, len(lines) - 1))
    if lines:
        ax.text(0, 1.022, "\n".join(lines), transform=ax.transAxes,
                fontsize=9.5, color=BODY, ha="left", va="bottom",
                linespacing=1.35)
    if ylab:
        ax.set_ylabel(ylab, fontsize=9.5)
    if legend:
        ax.legend(frameon=False, fontsize=8.6, loc="upper center",
                  bbox_to_anchor=(0.5, -0.07), ncol=3, handlelength=1.4)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    if source:
        fig.text(0.005, 0.005, source, fontsize=7.2, color=GREY, ha="left")
    fig.tight_layout(rect=[0, 0.055, 1, 1])
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def thousands(x, pos):
    return "{:,.0f}".format(x)


def bayarea_lhr(path):
    yrs = [2014, 2015, 2016, 2017, 2018, 2019]
    sfo = [911760, 1020149, 989098, 978355, 1027982, 1050777]
    sjc = [0, 0, 73954, 110863, 107458, 115101]
    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    ax.bar(yrs, sfo, color=MID, label="SFO - London Heathrow", width=0.62)
    ax.bar(yrs, sjc, bottom=sfo, color=ORANGE,
           label="SJC - London Heathrow (BA, from May 2016)", width=0.62)
    for x, a, b in zip(yrs, sfo, sjc):
        ax.text(x, a + b + 16000, "{:,.0f}".format(a + b), ha="center",
                fontsize=8.4, fontweight="bold", color=NAVY)
    ax.axvline(2015.5, color=NAVY, linestyle=":", linewidth=1.2)
    ax.text(2015.58, 1245000, "BA launches SJC\n4 May 2016", fontsize=8.2,
            color=NAVY, fontweight="bold", va="top")
    ax.set_ylim(0, 1330000)
    ax.yaxis.set_major_formatter(FuncFormatter(thousands))
    ax.set_xticks(yrs)
    return _finish(fig, ax,
                   "Bay Area to London Heathrow passengers",
                   "Two-way passengers by airport, calendar years 2014-2019 (actual)",
                   "Passengers per year",
                   "Source: US DOT / BTS International Report - Passengers, retrieved 5 August 2026; annual totals summed from published monthly rows. AviaSolutions analysis.",
                   path)


def carrier_sfo(path):
    yrs = [2015, 2016, 2017, 2018, 2019]
    ba = [459879, 443887, 431696, 429805, 427710]
    ua = [265311, 267055, 291091, 317500, 338230]
    vs = [294651, 278156, 255568, 280677, 284837]
    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    w = 0.26
    xs = range(len(yrs))
    ax.bar([x - w for x in xs], ba, w, color=S1_BRASS, label="British Airways")
    ax.bar(list(xs), ua, w, color=S2_PRUSSIAN, label="United")
    ax.bar([x + w for x in xs], vs, w, color=S3_VERDIGRIS, label="Virgin Atlantic")
    ax.annotate("United +27.5%\n2015 to 2019", xy=(4, 338230), xytext=(2.35, 430000),
                fontsize=8.4, fontweight="bold", color=NAVY,
                arrowprops=dict(arrowstyle="->", color=NAVY, lw=1.1))
    ax.set_xticks(list(xs))
    ax.set_xticklabels(yrs)
    ax.set_ylim(0, 520000)
    ax.yaxis.set_major_formatter(FuncFormatter(thousands))
    return _finish(fig, ax,
                   "SFO - London Heathrow passengers by carrier",
                   "Two-way passengers, calendar years 2015-2019 (actual)",
                   "Passengers per year",
                   "Source: US DOT / BTS International Report - Passengers, retrieved 5 August 2026. AviaSolutions analysis.",
                   path)


def sjc_traffic(path):
    yrs = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
    v = [9799527, 10796725, 12480232, 14319292, 15650444, 4711577, 7357441,
         11333723, 12097160, 11851270, 10675167]
    cols = [MID] * 5 + [LIGHT] * 3 + [MID] * 3
    fig, ax = plt.subplots(figsize=(6.6, 3.7))
    ax.bar(yrs, v, color=cols, width=0.66)
    ax.axhline(15650444, color=ORANGE, linestyle="--", linewidth=1.4)
    ax.text(2015, 15900000, "2019 peak 15.65m", fontsize=8.4, color=RAMP_DEEP,
            fontweight="bold")
    ax.annotate("2025: 10.68m\n-31.8% on 2019", xy=(2025, 10675167),
                xytext=(2021.4, 13600000), fontsize=8.6, fontweight="bold",
                color=NAVY, arrowprops=dict(arrowstyle="->", color=NAVY, lw=1.1))
    ax.set_ylim(0, 17600000)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: "%.0fm" % (x / 1e6)))
    ax.set_xticks(yrs)
    ax.set_xticklabels([str(y)[2:] for y in yrs])
    return _finish(fig, ax,
                   "San Jose Mineta total passengers",
                   "Calendar years 2015-2025 (actual); pale bars are pandemic years",
                   "Passengers per year",
                   "Source: City of San Jose Airport Department, Annual Status Report on the Airport Master Plan for Calendar Year 2025, 8 July 2026; flysjc.com and FAA passenger boarding data for prior years. AviaSolutions analysis.",
                   path, legend=False)


def gdp_per_worker(path):
    labs = ["United States", "California", "Santa Clara County", "San Francisco",
            "Silicon Valley", "San Mateo County"]
    v2025 = [192361, 235390, 325429, 328613, 336515, 366403]
    cols = [S5_SLATE, S5_SLATE, RAMP_LIGHT, RAMP_LIGHT, S1_BRASS, RAMP_LIGHT]
    fig, ax = plt.subplots(figsize=(6.4, 3.5))
    b = ax.barh(labs, v2025, color=cols, height=0.62)
    for r, val in zip(b, v2025):
        ax.text(val + 6000, r.get_y() + r.get_height() / 2,
                "${:,.0f}".format(val), va="center", fontsize=9,
                fontweight="bold", color=NAVY)
    ax.set_xlim(0, 430000)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: "$%.0fk" % (x / 1000)))
    ax.set_xlabel("GDP per worker, 2025, constant 2025 US dollars")
    return _finish(fig, ax,
                   "GDP per worker by area",
                   "2025, constant 2025 US dollars (actual)",
                   None,
                   "Source: Moody's Economy.com, analysed by the Silicon Valley Institute for Regional Studies, 2026 Silicon Valley Index public data file, April 2026.",
                   path, legend=False)


def marketcap(path):
    labs = ["US passenger\nairlines (combined)", "Meta Platforms", "Broadcom",
            "Apple", "Alphabet / Google", "NVIDIA"]
    v = [122, 1490, 2010, 4510, 4620, 5370]
    cols = [S1_BRASS] + [S5_SLATE] * 5
    fig, ax = plt.subplots(figsize=(6.4, 3.5))
    b = ax.barh(labs, v, color=cols, height=0.62)
    for r, val in zip(b, v):
        ax.text(val + 90, r.get_y() + r.get_height() / 2,
                "$%.2ftn" % (val / 1000) if val >= 1000 else "$%dbn" % val,
                va="center", fontsize=9, fontweight="bold", color=NAVY)
    ax.set_xlim(0, 6600)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: "$%.1ftn" % (x / 1000)))
    ax.set_xlabel("Market capitalisation, 5 August 2026, US dollars")
    return _finish(fig, ax,
                   "Market capitalisation of the five largest",
                   "US dollars, 5 August 2026 (actual)",
                   None,
                   "Source: StockAnalysis.com (S&P Global Market Intelligence data), intraday 5 August 2026. US passenger airline aggregate is AviaSolutions analysis of listed US passenger carriers.",
                   path, legend=False)


def revenue_flow(path, years, p2p, cnx_hub, cnx_dest, cargo, anc):
    fig, ax = plt.subplots(figsize=(4.5, 3.35))
    xs = range(len(years))
    m = 1e6
    b = [0] * len(years)
    series = [("Point to point", [v / m for v in p2p], NAVY),
              ("Connecting at London", [v / m for v in cnx_hub], MID),
              ("Connecting at San Jose", [v / m for v in cnx_dest], CYAN),
              ("Cargo", [v / m for v in cargo], ORANGE),
              ("Ancillary", [v / m for v in anc], GREY)]
    for name, vals, col in series:
        ax.bar(list(xs), vals, 0.55, bottom=b, color=col, label=name)
        b = [x + y for x, y in zip(b, vals)]
    for x, t in zip(xs, b):
        ax.text(x, t + 3, "$%.1fm" % t, ha="center", fontsize=8.6,
                fontweight="bold", color=NAVY)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["Year %d" % (i + 1) for i in range(len(years))])
    ax.set_ylim(0, max(b) * 1.18)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: "$%.0fm" % x))
    return _finish(fig, ax, "Revenue build up by flow",
                   "US$ million per year, years 1 to 3 (forecast)", None,
                   "Source: AviaSolutions analysis.", path)


def revenue_cabin(path, years, biz, prem, coach):
    fig, ax = plt.subplots(figsize=(4.5, 3.35))
    xs = range(len(years))
    m = 1e6
    b = [0] * len(years)
    for name, vals, col in [("Business (Club World)", [v / m for v in biz], NAVY),
                            ("Premium coach (World Traveller Plus)",
                             [v / m for v in prem], MID),
                            ("Coach (World Traveller)", [v / m for v in coach], CYAN)]:
        ax.bar(list(xs), vals, 0.55, bottom=b, color=col, label=name)
        b = [x + y for x, y in zip(b, vals)]
    for x, t in zip(xs, b):
        ax.text(x, t + 3, "$%.1fm" % t, ha="center", fontsize=8.6,
                fontweight="bold", color=NAVY)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["Year %d" % (i + 1) for i in range(len(years))])
    ax.set_ylim(0, max(b) * 1.18)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: "$%.0fm" % x))
    return _finish(fig, ax, "Passenger revenue build up by cabin",
                   "US$ million per year, years 1 to 3 (forecast)", None,
                   "Source: AviaSolutions analysis. Cabin split from the 787-8 three-class configuration and MIDT cabin mix.",
                   path)


# ---------------------------------------------------------------------------
# Parameterised. Everything above this line is keyed to LHR-SJC or GOA-NYC and
# is a rewrite, not a parameterisation. Everything below takes its numbers from
# the engine and is safe to call for any city pair.
# ---------------------------------------------------------------------------

def demand_build(path, *, market, p2p_carried, feed_behind, feed_beyond,
                 carried, load, origin_city, dest_city, year=None,
                 source="Source: OAG schedules, Sabre MIDT, AviaSolutions "
                        "analysis (Avia Cortex).", w=8.6, h=4.3):
    """Where year one traffic comes from, and what the aircraft takes of it.

    Two columns and a line, which is the whole forecast argument on one page.
    The left column is the point to point market in the catchment. The right
    column stacks the three legs of demand the nonstop can reach. The dashed
    line is what the aircraft carries at the planned load factor, so where the
    line falls below the stack the gap is spill and the eye sees the capacity
    constraint without being told.

    No arithmetic is assumed between the columns. The engine applies
    stimulation and a share between the market and the captured leg, so drawing
    the two as a subtraction would state a relationship the numbers do not
    carry. Every bar is a figure read from the engine and nothing between them
    is inferred.

    market        point to point market in the catchment, each way per year
    p2p_carried   the share of that market the nonstop captures
    feed_behind   connecting feed behind the origin
    feed_beyond   connecting flow beyond the destination
    carried       total carried each way at the planned load factor
    load          planned load factor as a fraction, or None
    """
    legs = [("Point to point captured", p2p_carried, NAVY),
            ("Feed behind %s" % origin_city, feed_behind, MID),
            ("Feed beyond %s" % dest_city, feed_beyond, CYAN)]
    legs = [(n, float(v or 0), c) for n, v, c in legs]
    stack_total = sum(v for _n, v, _c in legs)
    if stack_total <= 0 or not market:
        return None

    fig, ax = plt.subplots(figsize=(w, h))
    ax.bar([0], [float(market)], 0.5, color=LIGHT, edgecolor=MID, linewidth=1.0)
    ax.text(0, float(market) * 1.012, "{:,.0f}".format(market), ha="center",
            va="bottom", fontsize=9.6, fontweight="bold", color=NAVY)

    base = 0.0
    for name, val, col in legs:
        if val <= 0:
            continue
        ax.bar([1], [val], 0.5, bottom=base, color=col, label=name)
        if val > stack_total * 0.07:      # below this the label will not fit
            ax.text(1, base + val / 2.0, "{:,.0f}".format(val), ha="center",
                    va="center", fontsize=9.0, fontweight="bold", color="white")
        base += val
    ax.text(1, base * 1.012, "{:,.0f}".format(base), ha="center", va="bottom",
            fontsize=9.6, fontweight="bold", color=NAVY)

    carried = float(carried or 0)
    if carried:
        ax.plot([0.7, 1.3], [carried, carried], color=RED_LINE, linewidth=1.8,
                linestyle="--", zorder=8)
        lf = "at %.0f%% load factor" % (load * 100) if load else "on the schedule"
        # Where the aircraft takes the whole stack the line and the stack top are
        # the same number, and printing it twice reads as an error. Where it does
        # not, the gap between them is the spill and the figure has to say so.
        if abs(carried - base) <= max(base * 0.005, 1):
            lab = "Carried in full\n%s" % lf
        else:
            lab = "Carried %s\n%s\nSpill %s" % (lf, "{:,.0f}".format(carried),
                                                "{:,.0f}".format(base - carried))
        ax.text(1.40, carried, lab, fontsize=8.8, fontweight="bold",
                color=RED_LINE, va="center", ha="left", zorder=9, linespacing=1.5)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Point to point market\nin the catchment",
                        "Demand available\nto the nonstop"], fontsize=9.5)
    ax.set_xlim(-0.6, 2.35)
    ax.set_ylim(0, max(float(market), base, carried) * 1.16)
    ax.yaxis.set_major_formatter(FuncFormatter(thousands))
    # the legend sits in the empty right third of the plot, not under the axis:
    # the tick labels run to two lines and a legend beneath them collided with
    # the second line of both
    ax.legend(frameon=False, fontsize=8.8, loc="upper right", handlelength=1.2,
              borderaxespad=0.6, labelspacing=0.7)
    period = "year one%s (forecast)" % (", %s" % year if year else "")
    return _finish(fig, ax, "Where the year one traffic comes from",
                   "%s to %s, passengers each way per year, %s"
                   % (origin_city, dest_city, period),
                   "Passengers each way per year", source, path, legend=False)


# ---------------------------------------------------------------------------
# Airport charts. These take their numbers from airport_profile.py, which reads
# OAG and ACI, and they return None rather than an empty frame when the store
# cannot support them. A chart that cannot be drawn honestly is reported as a
# reason in the build log; it is never drawn thin and left to be queried.
#
# SEATS ARE NOT PASSENGERS and the two never share an axis here. OAG gives
# schedules, so anything read from it is capacity. Passengers come from ACI or
# from US DOT, and which one is named on the chart.
# ---------------------------------------------------------------------------

PANDEMIC = (2020, 2021, 2022)

# The source text for each airport chart, in one place, because the deck needs
# the same string the chart would print. On a slide the line belongs in house
# typography under the figure, not baked into the PNG at 7pt in the chart's own
# font, so `embed_source=False` leaves it off the image and the caller sets it
# on the slide. A chart saved on its own keeps the default and stands alone.
AIRPORT_SOURCES = {
    "airport_pax": "Source: %(label)s. AviaSolutions analysis.",
    "airport_haul": "Source: OAG schedules. AviaSolutions analysis.",
    "airport_airlines": "Source: OAG schedules. AviaSolutions analysis.",
    "airport_load": ("Source: OAG schedules for seats, %(label)s for "
                     "passengers. AviaSolutions analysis."),
}


def airport_source(slot, label=""):
    """The source line for an airport chart, for a caller placing it on a slide."""
    tpl = AIRPORT_SOURCES.get("airport_pax" if slot == "dest_pax" else slot, "")
    return tpl % {"label": label or "the store"} if tpl else ""


COVID_BAND = RAMP_PALE
COVID_INK = MUTED
# a pandemic bar has to stay legible against the band it sits in, so it is a
# muted version of the series colour rather than the palest tint available
COVID_BAR = RAMP_LIGHT


def _covid_band(ax, span, y=0.97):
    """Shade 2020 to 2022 and name it, so those years read as discountable.

    ACI reported right through the pandemic, so the years are real and are
    plotted. What they are not is comparable: a reader drawing a trend through
    2019 to 2023 has to be able to see at a glance which points to set aside.
    Shading and labelling the period does that without deleting the data.

    Where a store genuinely lacks the years, the same band explains the hole,
    which is a better answer than an unexplained gap in the middle of a chart.
    """
    lo, hi = min(span), max(span)
    a, b = max(lo - 0.5, 2019.5), min(hi + 0.5, 2022.5)
    if b <= a:
        return False
    ax.axvspan(a, b, color=COVID_BAND, zorder=0)
    ax.text((a + b) / 2.0, y, "Covid", transform=ax.get_xaxis_transform(),
            ha="center", va="top", fontsize=8.8, fontweight="bold",
            color=COVID_INK, zorder=1)
    return True


def _volume(x, pos=None):
    """A seat or passenger count, in the unit a reader expects to see it in.

    Thousands up to a million and millions above it. "4100k" is not how anybody
    writes four million seats, and it appeared on the first airline chart.
    """
    x = float(x)
    if abs(x) < 1:
        return "0"
    if abs(x) >= 1e6:
        m = x / 1e6
        # One decimal below ten million, every time. Dropping it on values that
        # happen to sit near a whole number printed 3.05m as "3m", understating
        # it by 1.6%, and a chart whose precision varies bar to bar invites the
        # question of which bars were rounded.
        return ("%.0fm" if abs(m) >= 10 else "%.1fm") % m
    return "%.0fk" % (x / 1e3)


def _volume_axis(ax, top, horizontal=False):
    """Whole-unit gridlines, so an axis never reads 0m, 2m, 5m, 8m, 10m.

    The default locator picks steps of 2.5m and a millions formatter rounds them
    to 2m and 8m, which is a chart that misstates its own gridlines.
    """
    from matplotlib.ticker import MultipleLocator
    step = 1e5
    for cand in (1e5, 2e5, 5e5, 1e6, 2e6, 5e6, 1e7, 2e7, 5e7, 1e8):
        step = cand
        if top / cand <= 6:
            break
    # The tick format is decided ONCE from the step, so every gridline on an
    # axis carries the same precision. Deciding per value gave "0, 5.0m, 10m",
    # which reads as three different units on one axis.
    if step >= 1e6:
        fmt = lambda v, p=None: "0" if abs(v) < 1 else "%.0fm" % (v / 1e6)
    elif top >= 1e6:
        fmt = lambda v, p=None: "0" if abs(v) < 1 else "%.1fm" % (v / 1e6)
    else:
        fmt = lambda v, p=None: "0" if abs(v) < 1 else "%.0fk" % (v / 1e3)
    axis = ax.xaxis if horizontal else ax.yaxis
    axis.set_major_locator(MultipleLocator(step))
    axis.set_major_formatter(FuncFormatter(fmt))


def _year_axis(ax, years):
    """Ticks for every year in the span, so an absent year reads as a gap.

    A chart drawn only at the years that exist silently closes the hole: 2019
    sits next to 2023 and the line slopes gently through four years that are not
    there. Ticking the whole span leaves the gap visible.
    """
    span = list(range(min(years), max(years) + 1))
    ax.set_xticks(span)
    ax.set_xticklabels([str(y)[2:] for y in span], fontsize=8.8)
    ax.set_xlim(min(span) - 0.7, max(span) + 0.7)
    return span


def airport_pax(path, *, series, airport, label, measure="throughput",
                absent=(), embed_source=True, w=8.6, h=3.8):
    """Passengers a year at the airport, with the years the store lacks left open.

    series   [(year, passengers)], complete years only
    label    the source, e.g. "ACI airport traffic", printed on the chart
    measure  "throughput" (ACI: arrivals plus departures plus transit) or
             "onboard" (US DOT T-100: departing passengers only)
    absent   years inside the span with no figure, named in the subtitle

    THE TITLE AND THE AXIS FOLLOW THE MEASURE. They used to be fixed at "total
    passengers" whichever source was behind them, which put Edinburgh's ACI
    throughput of 17.0m on one page and Austin's DOT departing count of 10.3m
    on another, both captioned the same way. A reader would take Edinburgh for
    the larger airport; Austin's throughput is 21.8m. Two measures under one
    caption is the worst kind of chart error, because nothing on the page
    betrays it.
    """
    onboard = (measure == "onboard")
    what = "departing passengers" if onboard else "total passengers"
    axis = ("Departing passengers per year" if onboard
            else "Passengers per year")
    basis = ("Passengers boarding at the airport, one direction. "
             if onboard else
             "Total airport throughput: arrivals, departures and transit. ")
    pts = [(int(y), float(v)) for y, v in (series or []) if v]
    if len(pts) < 3:
        return None
    years = [y for y, _v in pts]
    vals = [v for _y, v in pts]
    fig, ax = plt.subplots(figsize=(w, h))
    span = _year_axis(ax, years)
    banded = _covid_band(ax, span)
    cols = [COVID_BAR if y in PANDEMIC else MID for y in years]
    ax.bar(years, vals, color=cols, width=0.66, zorder=2)
    top = max(vals)
    for y, v in pts:
        ax.text(y, v + top * 0.02, "%.1f" % (v / 1e6), ha="center", fontsize=8.4,
                fontweight="bold", color=NAVY, zorder=3)
    ax.set_ylim(0, top * 1.16)
    _volume_axis(ax, top * 1.16)

    # Growth is quoted across the span it was measured over, never bare, and it
    # is taken across the years actually held rather than the years on the axis.
    grow = ""
    if len(pts) >= 2 and pts[0][1] > 0:
        n = pts[-1][0] - pts[0][0]
        if n > 0:
            r = (pts[-1][1] / pts[0][1]) ** (1.0 / n) - 1.0
            grow = "; %+.1f%% a year compound %d-%d" % (r * 100, pts[0][0], pts[-1][0])
    # Absent years are reported, but the pandemic ones are explained by the band
    # rather than listed: "no figure for 2020, 2021, 2022" beside a panel already
    # marked Covid says the same thing twice.
    other = [y for y in sorted(absent or ()) if y not in PANDEMIC]
    gap = "; no figure for %s" % ", ".join(str(y) for y in other) if other else ""
    if banded:
        shown = [y for y in years if y in PANDEMIC]
        note = (" Shaded years are Covid affected and are not comparable."
                if shown else " The shaded years are not held for this airport.")
    else:
        note = ""
    return _finish(fig, ax, "%s %s" % (airport, what),
                   "%sCalendar years %d-%d (actual)%s%s.%s"
                   % (basis, span[0], span[-1], grow, gap, note),
                   axis,
                   airport_source("airport_pax", label) if embed_source else None,
                   path, legend=False)


def airport_haul(path, *, haul, airport, embed_source=True, w=8.6, h=3.8):
    """Departing seats a year split domestic and international.

    CAPACITY, not traffic. OAG gives schedules, so the axis says seats and the
    title says capacity: a reader who takes this for passengers has been misled
    by the chart, not by their own carelessness.

    haul   {year: {"Domestic": seats, "International": seats}}
    """
    if not haul:
        return None
    years = sorted(int(y) for y in haul)
    if len(years) < 3:
        return None
    dom = [float(haul[y].get("Domestic", 0.0)) for y in years]
    itl = [float(haul[y].get("International", 0.0)) for y in years]
    if not any(dom) and not any(itl):
        return None
    fig, ax = plt.subplots(figsize=(w, h))
    span = _year_axis(ax, years)
    _covid_band(ax, span)
    ax.bar(years, dom, 0.66, color=S1_BRASS, label="Domestic", zorder=2)
    ax.bar(years, itl, 0.66, bottom=dom, color=S2_PRUSSIAN, label="International",
           zorder=2)
    tot = [a + b for a, b in zip(dom, itl)]
    top = max(tot)
    for y, t, i in zip(years, tot, itl):
        if t:
            ax.text(y, t + top * 0.025, "%.0f%% intl" % (100.0 * i / t),
                    ha="center", fontsize=8.2, fontweight="bold", color=NAVY,
                    zorder=3)
    ax.set_ylim(0, top * 1.16)
    _volume_axis(ax, top * 1.16)
    return _finish(fig, ax, "%s departing seats by market" % airport,
                   "Calendar years %d-%d (actual). Scheduled passenger services, "
                   "departing seats, one direction" % (span[0], span[-1]),
                   "Seats per year",
                   airport_source("airport_haul") if embed_source else None, path)


def airport_airlines(path, *, airlines, airport, year, names=None,
                     embed_source=True, w=8.6, h=4.0):
    """Who flies from the airport, by departing seats, in one year.

    airlines   [(carrier, seats, routes)] already ranked
    names      {code: airline name}, optional. A slide that says "FR" and "U2"
               reads as an extract from a schedule file rather than as a chart,
               so the name is used where the caller can supply one and the code
               is kept alongside it, since that is what a planner searches on.
    """
    rows = [(str(c), float(s), int(r)) for c, s, r in (airlines or []) if s > 0]
    if len(rows) < 3:
        return None
    rows = rows[:8][::-1]                      # barh draws bottom up
    tot = sum(s for _c, s, _r in rows)
    nm = {str(k).upper(): v for k, v in (names or {}).items()}

    def who(code):
        full = nm.get(code.upper())
        return "%s (%s)" % (full, code) if full else code

    labs = ["%s  -  %d route%s" % (who(c), r, "" if r == 1 else "s")
            for c, _s, r in rows]
    vals = [s for _c, s, _r in rows]
    cols = [MID] * len(rows)
    cols[-1] = NAVY                            # the largest, drawn last
    fig, ax = plt.subplots(figsize=(w, h))
    b = ax.barh(labs, vals, color=cols, height=0.66)
    for bar, v in zip(b, vals):
        ax.text(v + max(vals) * 0.012, bar.get_y() + bar.get_height() / 2,
                "%s  (%.0f%%)" % (_volume(v), 100.0 * v / tot) if tot else "",
                va="center", fontsize=8.6, fontweight="bold", color=NAVY)
    ax.set_xlim(0, max(vals) * 1.24)
    _volume_axis(ax, max(vals) * 1.24, horizontal=True)
    ax.set_xlabel("Departing seats, %d" % year, fontsize=9.5)
    return _finish(ax.figure, ax, "Airlines at %s by capacity" % airport,
                   "Departing seats, one direction, calendar year %d (actual). "
                   "Share is of the airlines shown" % year,
                   None,
                   airport_source("airport_airlines") if embed_source else None,
                   path, legend=False)


def airport_load(path, *, series, airport, pax_label, halved=False,
                 embed_source=True, w=8.6, h=3.6):
    """Effective load factor at the airport: passengers over departing seats.

    Two sources on one number, so the chart says so. Where the passenger figure
    is ACI throughput it has been halved to a departing count before meeting
    departing seats, and the subtitle says that rather than leaving a reader to
    wonder why an airport is 78% full.

    series   [(year, fraction)]
    """
    pts = [(int(y), float(v)) for y, v in (series or []) if v]
    if len(pts) < 3:
        return None
    years = [y for y, _v in pts]
    vals = [v * 100 for _y, v in pts]
    fig, ax = plt.subplots(figsize=(w, h))

    # THE LINE IS BROKEN AT EVERY MISSING YEAR. Plotted at the years it has, a
    # line joins 2019 straight to 2023 and draws a gentle four-year decline
    # through a period the store holds nothing for. Every year in the span is
    # given a point and the absent ones are left as gaps, so the line stops.
    have = dict(zip(years, vals))
    span_years = list(range(min(years), max(years) + 1))
    ys = [have.get(y, float("nan")) for y in span_years]
    span = _year_axis(ax, years)
    _covid_band(ax, span)
    ax.plot(span_years, ys, color=S1_BRASS, linewidth=2.2, marker="o", markersize=5,
            zorder=3)
    for y, v in zip(years, vals):
        ax.text(y, v + 1.6, "%.0f%%" % v, ha="center", fontsize=8.4,
                fontweight="bold", color=NAVY, zorder=4)
    # A gap outside the pandemic has no band to explain it, so it gets its own.
    gaps = [y for y in span_years if y not in have and y not in PANDEMIC]
    for y in gaps:
        ax.axvspan(y - 0.5, y + 0.5, color=RAMP_PALE, zorder=0)
    if gaps:
        ax.text(sum(gaps) / float(len(gaps)), 0.04,
                "no figure", transform=ax.get_xaxis_transform(),
                ha="center", va="bottom", fontsize=8.2, color=GREY)
    lo, hi = min(vals), max(vals)
    ax.set_ylim(max(0, lo - (14 if gaps else 10)), min(100, hi + 10))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: "%.0f%%" % x))
    approx = (" Airport throughput is halved to a departing count to meet "
              "departing seats, which is an approximation." if halved else "")
    return _finish(fig, ax, "%s effective load factor" % airport,
                   "Passengers over departing seats, calendar years %d-%d "
                   "(actual).%s" % (span[0], span[-1], approx),
                   "Passengers per departing seat",
                   airport_source("airport_load", pax_label) if embed_source
                   else None, path, legend=False)


def route_map(path):
    """Great-circle LHR-SJC on a plain world outline, Atlantic-centred."""
    import numpy as np
    fig = plt.figure(figsize=(9.4, 4.3))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.set_facecolor(PAPER)
    fig.patch.set_facecolor(PAPER)
    try:
        import geopandas  # optional
        world = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
        world.plot(ax=ax, color=GRID, edgecolor=AXIS, linewidth=0.5)
    except Exception:
        pass
    lhr = (-0.4614, 51.4706)
    sjc = (-121.9289, 37.3626)
    lon1, lat1 = np.radians(lhr)
    lon2, lat2 = np.radians(sjc)
    d = 2 * np.arcsin(np.sqrt(np.sin((lat2 - lat1) / 2) ** 2 +
                              np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2))
    f = np.linspace(0, 1, 200)
    A = np.sin((1 - f) * d) / np.sin(d)
    B = np.sin(f * d) / np.sin(d)
    x = A * np.cos(lat1) * np.cos(lon1) + B * np.cos(lat2) * np.cos(lon2)
    y = A * np.cos(lat1) * np.sin(lon1) + B * np.cos(lat2) * np.sin(lon2)
    z = A * np.sin(lat1) + B * np.sin(lat2)
    lat = np.degrees(np.arctan2(z, np.sqrt(x ** 2 + y ** 2)))
    lon = np.degrees(np.arctan2(y, x))
    ax.plot(lon, lat, color=S1_BRASS, linewidth=2.4, zorder=5)
    for (px, py), lab, ha in [(lhr, "London Heathrow", "left"),
                              (sjc, "San Jose", "right")]:
        # Ink deliberately, and test_chart_palette.py allows it here. These two markers locate
        # named airports beside their labels; they are type furniture rather than a data series,
        # and in brass they would disappear into the route line they sit on.
        ax.plot([px], [py], "o", color=NAVY, markersize=9, zorder=6)
    ax.set_xlim(-135, 25)
    ax.set_ylim(20, 72)
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path
