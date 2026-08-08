"""Project Liguria figures: charts and maps for the Genoa - New York deck."""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.basemap import Basemap

from avia_charts import _finish, NAVY, BODY, ORANGE, CYAN, MID, GREY, LIGHT, TEAL

SEA = "#DCEAF6"
LAND = "#F1F3E6"
COAST = "#B9C6D4"
RED = "#C0392B"

GOA = (8.6375, 44.4133)
JFK = (-73.7781, 40.6413)


def _gc(a, b, n=240):
    lon1, lat1 = np.radians(a)
    lon2, lat2 = np.radians(b)
    d = 2 * np.arcsin(np.sqrt(np.sin((lat2 - lat1) / 2) ** 2 +
                              np.cos(lat1) * np.cos(lat2) *
                              np.sin((lon2 - lon1) / 2) ** 2))
    f = np.linspace(0, 1, n)
    A = np.sin((1 - f) * d) / np.sin(d)
    B = np.sin(f * d) / np.sin(d)
    x = A * np.cos(lat1) * np.cos(lon1) + B * np.cos(lat2) * np.cos(lon2)
    y = A * np.cos(lat1) * np.sin(lon1) + B * np.cos(lat2) * np.sin(lon2)
    z = A * np.sin(lat1) + B * np.sin(lat2)
    return (np.degrees(np.arctan2(y, x)),
            np.degrees(np.arctan2(z, np.sqrt(x ** 2 + y ** 2))))


def route_map(path, w=9.6, dpi=210):
    fig = plt.figure(figsize=(w, 4.0))
    ax = fig.add_axes([0, 0, 1, 1])
    m = Basemap(projection="merc", llcrnrlon=-85, urcrnrlon=26,
                llcrnrlat=32, urcrnrlat=64, resolution="l", ax=ax)
    fig.set_size_inches(w, w * m.aspect)
    m.drawmapboundary(fill_color=SEA)
    m.fillcontinents(color=LAND, lake_color=SEA)
    m.drawcoastlines(linewidth=0.5, color=COAST)
    m.drawcountries(linewidth=0.5, color=COAST)
    gx, gy = m(*_gc(GOA, JFK))
    ax.plot(gx, gy, color=RED, linewidth=2.6, zorder=6, solid_capstyle="round")
    for lon, lat, lab, dx, ha in [(JFK[0], JFK[1], "New York", 0.012, "left"),
                                  (GOA[0], GOA[1], "Genoa", -0.014, "right")]:
        x, y = m(lon, lat)
        ax.plot(x, y, "o", color=NAVY, markersize=10, zorder=7,
                markeredgecolor="white", markeredgewidth=1.6)
        ax.text(x + dx * ax.get_xlim()[1], y - 0.055 * ax.get_ylim()[1], lab,
                fontsize=13, fontweight="bold", color=NAVY, ha=ha, va="center",
                zorder=8)
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
    return path


def catchment_map(path, w=6.2, dpi=210):
    """North-west Italy: Genoa and the airports that take its traffic today."""
    fig = plt.figure(figsize=(w, 5.0))
    ax = fig.add_axes([0, 0, 1, 1])
    m = Basemap(projection="merc", llcrnrlon=5.8, urcrnrlon=12.4,
                llcrnrlat=43.2, urcrnrlat=46.6, resolution="i", ax=ax)
    fig.set_size_inches(w, w * m.aspect)
    m.drawmapboundary(fill_color=SEA)
    m.fillcontinents(color=LAND, lake_color=SEA)
    m.drawcoastlines(linewidth=0.6, color="#9FB0C2")
    m.drawcountries(linewidth=0.8, color="#9FB0C2")

    ports = [("Milan Malpensa", 8.7281, 45.6306, "1h58-2h06"),
             ("Milan Linate", 9.2764, 45.4451, "1h43"),
             ("Bergamo", 9.7042, 45.6739, "2h07-2h22"),
             ("Turin", 7.6497, 45.2008, "1h53 to city"),
             ("Nice", 7.2159, 43.6584, "2h22"),
             ("Pisa", 10.3927, 43.6839, "1h50-2h09")]
    gx, gy = m(GOA[0], GOA[1])
    for name, lon, lat, drive in ports:
        x, y = m(lon, lat)
        ax.plot([gx, x], [gy, y], color="#B0682A", linewidth=1.1, alpha=0.6,
                linestyle="--", zorder=4)
        ax.plot(x, y, "o", color=ORANGE, markersize=9, zorder=6,
                markeredgecolor=NAVY, markeredgewidth=1.0)
        ax.text(x, y + 0.016 * ax.get_ylim()[1], "%s\n%s" % (name, drive),
                fontsize=8.0, fontweight="bold", color="#7A4A10", ha="center",
                va="bottom", zorder=7)
    ax.plot(gx, gy, "o", color=NAVY, markersize=15, zorder=8,
            markeredgecolor="white", markeredgewidth=1.8)
    ax.text(gx, gy - 0.030 * ax.get_ylim()[1], "GENOA", fontsize=13,
            fontweight="bold", color=NAVY, ha="center", va="top", zorder=8)
    for lon, lat, lab in [(9.19, 45.464, "Milan"), (7.687, 45.070, "Turin"),
                          (11.343, 44.494, "Bologna"), (10.40, 43.716, "Pisa"),
                          (10.10, 44.80, "Parma"), (9.69, 45.05, "Piacenza")]:
        x, y = m(lon, lat)
        ax.plot(x, y, "s", color="#4A5A6E", markersize=3.5, zorder=5)
        ax.text(x, y - 0.012 * ax.get_ylim()[1], lab, fontsize=7.6,
                color="#3A4A5E", ha="center", va="top", zorder=5)
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
    return path


def traffic(path):
    """Verified points only. The 2015-2023 series is unverified and is not shown."""
    labs = ["2019\n(operator basis)", "2024", "2025", "2026 Jan-Apr"]
    vals = [1537044, 1335095, 1587761, 465000]
    cols = [LIGHT, MID, NAVY, ORANGE]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    b = ax.bar(labs, vals, color=cols, width=0.6)
    for r, v, note in zip(b, vals, ["disputed source", "+4.3%", "+18.1%", "+17.9% y/y"]):
        ax.text(r.get_x() + r.get_width() / 2, v + 40000, "{:,.0f}".format(v),
                ha="center", fontsize=9, fontweight="bold", color=NAVY)
        ax.text(r.get_x() + r.get_width() / 2, v * 0.5, note, ha="center",
                fontsize=8.4, fontweight="bold",
                color="white" if v > 1000000 else NAVY, rotation=0)
    ax.set_ylim(0, 1900000)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: "%.1fm" % (x / 1e6)))
    return _finish(fig, ax, "Genoa Cristoforo Colombo passengers",
                   "Verified data points only (actual). Part-year figure marked.",
                   "Passengers",
                   "Source: ENAC, Air Traffic Data 2025, Airport Traffic Table, published January 2026, for 2025; Genova24 reporting Assaeroporti-consistent data for 2024; "
                   "operator figures reported by advtraining.it and GuidaViaggi, 7 May 2026, for 2026 Jan-Apr. The 2015-2023 annual series could not be verified to a named publisher and is deliberately omitted.",
                   path, legend=False)


def seasonality(path, idx):
    mons = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
            "Oct", "Nov", "Dec"]
    fig, ax = plt.subplots(figsize=(6.5, 3.5))
    cols = [ORANGE if v < 0.75 else MID for v in idx]
    ax.bar(mons, idx, color=cols, width=0.66)
    ax.axhline(1.0, color=NAVY, linestyle="--", linewidth=1.2)
    ax.text(0.1, 1.03, "Annual average", fontsize=8.4, color=NAVY, fontweight="bold")
    for i, v in enumerate(idx):
        ax.text(i, v + 0.03, "%.2f" % v, ha="center", fontsize=8,
                fontweight="bold", color=NAVY)
    ax.set_ylim(0, 1.85)
    return _finish(fig, ax, "Assumed monthly demand index",
                   "Leisure-weighted profile, index 1.00 = annual average (assumption)",
                   "Demand index",
                   "Source: AviaSolutions analysis. This profile is a working assumption pending a monthly Sabre pull; it is not measured Genoa-New York demand.",
                   path, legend=False)


def cost_stack(path, items, revenue):
    """Cost stack per turnaround against gross revenue."""
    fig, ax = plt.subplots(figsize=(6.4, 3.7))
    names = [n for n, _ in items]
    vals = [v for _, v in items]
    cols = [MID, MID, MID, MID, MID, MID, MID, NAVY, NAVY, NAVY, GREY, GREY]
    left = 0
    for (n, v), c in zip(items, cols[:len(items)]):
        ax.barh([0], [v], left=left, color=c, height=0.5,
                edgecolor="white", linewidth=0.8)
        if v > 4000:
            ax.text(left + v / 2, 0, n.split()[0], ha="center", va="center",
                    fontsize=7.4, color="white", fontweight="bold", rotation=90)
        left += v
    ax.barh([1], [revenue], color=ORANGE, height=0.5)
    ax.text(revenue / 2, 1, "Gross revenue $%s" % "{:,.0f}".format(revenue),
            ha="center", va="center", fontsize=9.5, color=NAVY, fontweight="bold")
    ax.text(left / 2, -0.42, "Total cost $%s" % "{:,.0f}".format(left),
            ha="center", va="center", fontsize=9.5, color=NAVY, fontweight="bold")
    ax.annotate("", xy=(revenue, 0.5), xytext=(left, 0.5),
                arrowprops=dict(arrowstyle="<->", color=NAVY, lw=1.4))
    ax.text((left + revenue) / 2, 0.62, "Profit $%s" % "{:,.0f}".format(revenue - left),
            ha="center", fontsize=10, fontweight="bold", color=NAVY)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Cost", "Revenue"])
    ax.set_xlim(0, revenue * 1.12)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: "$%.0fk" % (x / 1000)))
    ax.grid(axis="x", color="#E3E9F1", linewidth=0.8)
    return _finish(fig, ax, "Route result per turnaround",
                   "US dollars per return rotation, central planning case (forecast)",
                   None,
                   "Source: AviaSolutions analysis, Genoa - New York business case, central planning case. Airport charges at both ends are indicative placeholders and are not yet verified.",
                   path, legend=False)


def fuel_sensitivity(path, fuel, profit):
    fig, ax = plt.subplots(figsize=(6.2, 3.5))
    ax.plot(fuel, profit, "o-", color=NAVY, linewidth=2.4, markersize=8)
    ax.axhline(0, color=GREY, linewidth=1.0)
    for x, y in zip(fuel, profit):
        ax.text(x, y + 0.42, "$%.1fm" % y, ha="center", fontsize=9,
                fontweight="bold", color=NAVY)
    ax.axvline(0.90, color=ORANGE, linestyle="--", linewidth=1.4)
    ax.text(0.905, 13.2, "Central planning\ncase $0.90/kg", fontsize=8.4,
            color="#B37600", fontweight="bold", va="top")
    ax.set_xlabel("Jet fuel price, US dollars per kilogramme")
    ax.set_ylim(0, 15)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: "$%.0fm" % x))
    return _finish(fig, ax, "Annual profit against the fuel price",
                   "US dollars per year, network basis, daily service (forecast)",
                   "Annual profit",
                   "Source: AviaSolutions analysis, Genoa - New York business case, scenario grid. Capture rate has no effect across the tested range because the load-factor cap binds throughout.",
                   path, legend=False)
