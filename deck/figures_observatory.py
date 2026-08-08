"""Project Liguria figures in the Observatory / Meridian palette.

Same data as goa_figures.py, drawn to the Meridian style: warm off-white ground,
ink rules, gold accents, serif labels, mono figures. Charts carry no title: the
Observatory slide furniture supplies the heading, so a burnt-in title would
duplicate it. Unit and period stay on the axis, per the Avia chart rule.

Avia Solutions Limited. All rights reserved.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.basemap import Basemap

BG = "#E7E4DD"
INK = "#141C25"
MUTE = "#5A6470"
LABEL = "#6B7480"
RULE = "#D8D2C4"
RULE_2 = "#C9C2B2"
GOLD = "#B8862F"
GOLD_L = "#D4A249"
NAVY = "#0F1B28"
SEA = "#DDD8CB"
LAND = "#EFEBE0"
COAST = "#B9B2A2"
CAUTION = "#8A3A2A"
POSITIVE = "#3F6B4A"

# Observatory Brand Guidelines v1.1, section 05 Data Visualisation.
# A seven-colour categorical set, assigned in this fixed order and never
# reordered chart to chart. The primary or observed series always takes Brass.
BRASS = "#D4A249"
PRUSSIAN = "#3D6A88"
VERDIGRIS = "#5F8D7A"
OXBLOOD = "#A9553F"
SLATE = "#8793A0"
PLUM = "#7B617F"
OLIVE = "#9C8A4E"
CATEGORICAL = [BRASS, PRUSSIAN, VERDIGRIS, OXBLOOD, SLATE, PLUM, OLIVE]

# Reserved. Averages, targets, thresholds and alerts only, never a category.
SIGNAL_RED = "#CE3B2A"

plt.rcParams.update({
    "font.family": "DejaVu Serif",
    "font.size": 11,
    "axes.edgecolor": RULE_2,
    "axes.labelcolor": MUTE,
    "text.color": INK,
    "xtick.color": MUTE,
    "ytick.color": MUTE,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,
})
MONO = {"family": "DejaVu Sans Mono"}

GOA = (8.6375, 44.4133)
JFK = (-73.7781, 40.6413)


def _finish(fig, ax, xlabel=None, ylabel=None, path=None, legend=False):
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10, color=LABEL)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10, color=LABEL)
    if legend:
        ax.legend(frameon=False, fontsize=9.5, loc="upper center",
                  bbox_to_anchor=(0.5, -0.10), ncol=3)
    ax.grid(axis="y", color=RULE, linewidth=0.9)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def _gc(a, b, n=240):
    lon1, lat1 = np.radians(a)
    lon2, lat2 = np.radians(b)
    d = 2 * np.arcsin(np.sqrt(np.sin((lat2 - lat1) / 2) ** 2 +
                              np.cos(lat1) * np.cos(lat2) *
                              np.sin((lon2 - lon1) / 2) ** 2))
    f = np.linspace(0, 1, n)
    A, B = np.sin((1 - f) * d) / np.sin(d), np.sin(f * d) / np.sin(d)
    x = A * np.cos(lat1) * np.cos(lon1) + B * np.cos(lat2) * np.cos(lon2)
    y = A * np.cos(lat1) * np.sin(lon1) + B * np.cos(lat2) * np.sin(lon2)
    z = A * np.sin(lat1) + B * np.sin(lat2)
    return (np.degrees(np.arctan2(y, x)),
            np.degrees(np.arctan2(z, np.sqrt(x ** 2 + y ** 2))))


def route_map(path, w=12.0, dpi=200):
    """The world route map. Slide 4 must carry this."""
    fig = plt.figure(figsize=(w, 5.0))
    ax = fig.add_axes([0, 0, 1, 1])
    m = Basemap(projection="merc", llcrnrlon=-85, urcrnrlon=26,
                llcrnrlat=32, urcrnrlat=64, resolution="l", ax=ax)
    fig.set_size_inches(w, w * m.aspect)
    m.drawmapboundary(fill_color=SEA)
    m.fillcontinents(color=LAND, lake_color=SEA)
    m.drawcoastlines(linewidth=0.6, color=COAST)
    m.drawcountries(linewidth=0.5, color=COAST)
    gx, gy = m(*_gc(GOA, JFK))
    ax.plot(gx, gy, color=GOLD, linewidth=3.0, zorder=6, solid_capstyle="round")
    for lon, lat, lab, dx, ha in [(JFK[0], JFK[1], "NEW YORK", 0.014, "left"),
                                  (GOA[0], GOA[1], "GENOA", -0.016, "right")]:
        x, y = m(lon, lat)
        ax.plot(x, y, "o", color=INK, markersize=11, zorder=7,
                markeredgecolor=BG, markeredgewidth=2.0)
        ax.text(x + dx * ax.get_xlim()[1], y - 0.055 * ax.get_ylim()[1], lab,
                fontsize=15, color=INK, ha=ha, va="center", zorder=8,
                fontdict=MONO)
    ax.text(0.5, 0.055, "3,509.6 NAUTICAL MILES", transform=ax.transAxes,
            ha="center", fontsize=11, color=GOLD, fontdict=MONO)
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
    return path


def catchment_map(path, w=7.4, dpi=200):
    """North-west Italy and the six airports serving Genoa's catchment today."""
    fig = plt.figure(figsize=(w, 6.0))
    ax = fig.add_axes([0, 0, 1, 1])
    m = Basemap(projection="merc", llcrnrlon=5.8, urcrnrlon=12.4,
                llcrnrlat=43.2, urcrnrlat=46.6, resolution="i", ax=ax)
    fig.set_size_inches(w, w * m.aspect)
    m.drawmapboundary(fill_color=SEA)
    m.fillcontinents(color=LAND, lake_color=SEA)
    m.drawcoastlines(linewidth=0.7, color=COAST)
    m.drawcountries(linewidth=0.9, color=COAST)
    ports = [("MALPENSA", 8.7281, 45.6306, "1h58"),
             ("LINATE", 9.2764, 45.4451, "1h43"),
             ("BERGAMO", 9.7042, 45.6739, "2h07"),
             ("TURIN", 7.6497, 45.2008, "1h53"),
             ("NICE", 7.2159, 43.6584, "2h22"),
             ("PISA", 10.3927, 43.6839, "1h50")]
    gx, gy = m(GOA[0], GOA[1])
    for name, lon, lat, drive in ports:
        x, y = m(lon, lat)
        ax.plot([gx, x], [gy, y], color=GOLD, linewidth=1.1, alpha=0.55,
                linestyle=(0, (4, 3)), zorder=4)
        ax.plot(x, y, "o", color=GOLD, markersize=9, zorder=6,
                markeredgecolor=BG, markeredgewidth=1.4)
        ax.text(x, y + 0.018 * ax.get_ylim()[1], "%s  %s" % (name, drive),
                fontsize=8.6, color=INK, ha="center", va="bottom", zorder=7,
                fontdict=MONO)
    ax.plot(gx, gy, "o", color=INK, markersize=16, zorder=8,
            markeredgecolor=BG, markeredgewidth=2.2)
    ax.text(gx, gy - 0.034 * ax.get_ylim()[1], "GENOA", fontsize=14, color=INK,
            ha="center", va="top", zorder=8, fontdict=MONO)
    for lon, lat, lab in [(9.19, 45.464, "Milan"), (7.687, 45.070, "Turin"),
                          (11.343, 44.494, "Bologna"), (10.10, 44.80, "Parma")]:
        x, y = m(lon, lat)
        ax.plot(x, y, "s", color=MUTE, markersize=3.5, zorder=5)
        ax.text(x, y - 0.014 * ax.get_ylim()[1], lab, fontsize=8.4, color=MUTE,
                ha="center", va="top", zorder=5)
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
    return path


def traffic(path):
    labs = ["2019", "2024", "2025", "2026 Jan-Apr"]
    vals = [1537044, 1335095, 1587761, 465000]
    cols = [SLATE, PRUSSIAN, BRASS, INK]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    b = ax.bar(labs, vals, color=cols, width=0.58)
    for r, v, note in zip(b, vals, ["OPERATOR\nBASIS", "+4.3%", "+18.1%", "+17.9%"]):
        ax.text(r.get_x() + r.get_width() / 2, v + 45000, "{:,.0f}".format(v),
                ha="center", fontsize=10.5, color=INK, fontdict=MONO)
        ax.text(r.get_x() + r.get_width() / 2, v * 0.42, note, ha="center",
                va="center", fontsize=8.8, color=BG, fontdict=MONO,
                linespacing=1.5)
    ax.set_ylim(0, 1950000)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: "%.1fm" % (x / 1e6)))
    return _finish(fig, ax, ylabel="Passengers per year, verified points only",
                   path=path)


def seasonality(path, idx):
    mons = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP",
            "OCT", "NOV", "DEC"]
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    cols = [SLATE if v < 1.0 else BRASS for v in idx]
    ax.bar(mons, idx, color=cols, width=0.62)
    ax.axhline(1.0, color=SIGNAL_RED, linestyle=(0, (4, 3)), linewidth=1.3)
    ax.text(0.05, 1.04, "ANNUAL AVERAGE", fontsize=8.6, color=SIGNAL_RED,
            fontdict=MONO)
    for i, v in enumerate(idx):
        ax.text(i, v + 0.035, "%.2f" % v, ha="center", fontsize=8.6, color=INK,
                fontdict=MONO)
    ax.set_ylim(0, 1.85)
    ax.tick_params(axis="x", labelsize=8.6)
    return _finish(fig, ax, ylabel="Demand index, 1.00 = annual average", path=path)


def cost_stack(path, groups, revenue):
    """Seven cost groups, one per categorical colour, in the fixed brand order.

    Twelve stacked segments cannot be told apart at any palette, so the cost
    stack is grouped to seven, which is exactly what the categorical set carries.
    """
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    left = 0
    for i, (name, v) in enumerate(groups):
        ax.barh([0], [v], left=left, color=CATEGORICAL[i % 7], height=0.44,
                edgecolor=BG, linewidth=1.4)
        left += v
    ax.barh([1], [revenue], color=INK, height=0.44)
    ax.text(revenue / 2, 1, "GROSS REVENUE  $%s" % "{:,.0f}".format(revenue),
            ha="center", va="center", fontsize=10, color=BG, fontdict=MONO)
    ax.text(left * 1.012, 0, "TOTAL COST  $%s" % "{:,.0f}".format(left),
            ha="left", va="center", fontsize=9.5, color=INK, fontdict=MONO)
    ax.annotate("", xy=(revenue, 0.5), xytext=(left, 0.5),
                arrowprops=dict(arrowstyle="<->", color=SIGNAL_RED, lw=1.4))
    ax.text((left + revenue) / 2, 0.585,
            "PROFIT  $%s" % "{:,.0f}".format(revenue - left),
            ha="center", va="bottom", fontsize=10.5, color=SIGNAL_RED,
            fontdict=MONO)
    # legend below, in the fixed assignment order
    handles = [plt.Rectangle((0, 0), 1, 1, color=CATEGORICAL[i % 7])
               for i in range(len(groups))]
    ax.legend(handles, ["%s  $%s" % (n, "{:,.0f}".format(v)) for n, v in groups],
              frameon=False, fontsize=8.8, loc="upper center",
              bbox_to_anchor=(0.5, -0.16), ncol=3, handlelength=1.1,
              columnspacing=1.4, handletextpad=0.5)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["COST", "REVENUE"], fontdict=MONO, fontsize=9.5)
    ax.set_xlim(0, revenue * 1.30)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: "$%.0fk" % (x / 1000)))
    ax.grid(axis="x", color=RULE, linewidth=0.9)
    ax.grid(axis="y", visible=False)
    ax.set_axisbelow(True)
    ax.set_xlabel("US dollars per return rotation", fontsize=10, color=LABEL)
    ax.tick_params(labelsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def fuel_sensitivity(path, fuel, profit):
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    ax.plot(fuel, profit, "-", color=INK, linewidth=2.0, zorder=4)
    ax.plot(fuel, profit, "o", color=BRASS, markersize=10, zorder=5,
            markeredgecolor=BG, markeredgewidth=1.6)
    for x, y in zip(fuel, profit):
        ax.text(x, y + 0.5, "$%.1fm" % y, ha="center", fontsize=10, color=INK,
                fontdict=MONO)
    ax.axvline(0.90, color=SIGNAL_RED, linestyle=(0, (4, 3)), linewidth=1.3)
    ax.text(0.907, 13.6, "CENTRAL CASE\n$0.90/KG", fontsize=8.8, color=SIGNAL_RED,
            va="top", fontdict=MONO)
    ax.set_ylim(0, 15)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: "$%.0fm" % x))
    return _finish(fig, ax, xlabel="Jet fuel price, US dollars per kilogramme",
                   ylabel="Annual profit, network basis", path=path)


def accuracy(path):
    """The QSI calibrated accuracy distribution, redrawn in the Meridian palette."""
    import json
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "accuracy_dist.json")
    if not os.path.exists(src):
        return None
    d = json.load(open(src))
    err = np.array(d["err"]) * 100
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    bins = np.arange(-55, 60, 5)
    ax.axvspan(-20, 20, color=BRASS, alpha=0.16, zorder=0)
    ax.hist(np.clip(err, -55, 55), bins=bins, color=PRUSSIAN, edgecolor=BG,
            linewidth=1.0, zorder=2)
    for x in (-20, 20):
        ax.axvline(x, color=SIGNAL_RED, lw=1.2, ls=(0, (4, 3)), zorder=3)
    ax.text(0, ax.get_ylim()[1] * 0.92, "89% WITHIN 20%", ha="center",
            fontsize=11, color=INK, fontdict=MONO)
    return _finish(fig, ax,
                   xlabel="Forecast error against actual first-year passengers (%)",
                   ylabel="Number of route launches", path=path)
