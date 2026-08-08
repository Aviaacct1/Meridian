"""Avia house-style maps: route map, catchment map, beyond-market map."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np

NAVY = "#021D49"
SEA = "#DCEAF6"
LAND = "#F1F3E6"
COAST = "#B9C6D4"
ORANGE = "#FFA800"
RED = "#C0392B"
MID = "#1F6FB2"

LHR = (-0.4614, 51.4706)
SJC = (-121.9289, 37.3626)
SFO = (-122.375, 37.619)


def _gc(a, b, n=240):
    """Great-circle path as arrays of longitude and latitude."""
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


def _unwrap(lon, ref):
    """`lon` moved into the 360 degree window centred on `ref`.

    Sydney to Los Angeles is 129 degrees apart the short way and 231 the long
    way, and in plain -180 to 180 coordinates it reads as the long way. The map
    drew the great circle right across Africa, which is not a near miss, it is
    the wrong hemisphere. Everything below works in the unwrapped frame and only
    the frame corners go back to Basemap.
    """
    while lon - ref > 180.0:
        lon -= 360.0
    while lon - ref < -180.0:
        lon += 360.0
    return lon


def _frame(a, b, pad=0.28, min_span=12.0, grow_lon=1.0, grow_lat=1.0):
    """Map corners that hold both endpoints with room around them.

    The frame used to be the fixed North Atlantic window the LHR to SJC deck
    needed, so every other route was drawn either off the edge or as a hairline
    in a corner. It is now computed from the endpoints, in the unwrapped
    longitude frame, so a pair straddling the antimeridian frames the short way
    round. Basemap accepts corner longitudes beyond 180 for a cylindrical
    projection, which is what makes that possible without reprojecting.
    """
    lons = sorted([a[0], _unwrap(b[0], a[0])])
    lats = sorted([a[1], b[1]])
    dlon = max(lons[1] - lons[0], min_span) * grow_lon
    dlat = max(lats[1] - lats[0], min_span * 0.6) * grow_lat
    cx, cy = sum(lons) / 2.0, sum(lats) / 2.0
    half_x = (lons[1] - lons[0]) / 2.0 + dlon * pad
    half_y = (lats[1] - lats[0]) / 2.0 + dlat * pad
    lo0, lo1 = cx - half_x, cx + half_x
    la0 = max(-82.0, cy - half_y)
    la1 = min(82.0, cy + half_y)
    if lo0 >= -179.0 and lo1 <= 179.0:
        return (lo0, lo1, la0, la1)
    # the frame crosses the antimeridian: slide the whole window east so both
    # corners are positive, and the callers shift their longitudes to match
    shift = 360.0 if lo0 < -179.0 else 0.0
    return (lo0 + shift, lo1 + shift, la0, la1)


# Height over width, as the figure will actually be drawn. A deck page is
# landscape, so a map shallower than the first is a letterbox sliver and one
# deeper than the second is a portrait column with the slide empty either side.
ASPECT_LO, ASPECT_HI = 0.30, 0.62


def _shaped_frame(a, b, lo=ASPECT_LO, hi=ASPECT_HI, tries=6):
    """A frame that holds the pair AND sets on a landscape page.

    The plain frame is right about geography and wrong about shape. Auckland to
    Santiago is 114 degrees of longitude and four of latitude, which framed
    honestly gave a map 2,016 pixels wide and 105 tall: a hairline. Birmingham
    to Edinburgh gave the opposite, a portrait column.

    Mercator's vertical stretch grows with latitude, so the printed shape cannot
    be worked out from the degrees alone. Basemap is asked what aspect the frame
    actually produces and the frame is grown on its short side until the answer
    falls between lo and hi. Growing only ever adds context around the route, so
    no iteration can push an endpoint out of the picture.
    """
    grow_lon = grow_lat = 1.0
    corners = _frame(a, b, grow_lon=grow_lon, grow_lat=grow_lat)
    for _ in range(tries):
        lo0, lo1, la0, la1 = corners
        m = Basemap(projection="merc", llcrnrlon=lo0, urcrnrlon=lo1,
                    llcrnrlat=la0, urcrnrlat=la1, resolution=None)
        aspect = m.aspect
        if lo <= aspect <= hi:
            return corners
        if aspect > hi:
            grow_lon *= min(2.5, aspect / hi)
        else:
            grow_lat *= min(2.5, lo / max(aspect, 0.01))
        corners = _frame(a, b, grow_lon=grow_lon, grow_lat=grow_lat)
    return corners


def route_map(path, origin=LHR, destination=SJC, origin_label="London Heathrow",
              destination_label="San Jose", w=9.6, h=4.05, dpi=210):
    """Great-circle route map between two points, framed on the pair.

    origin and destination are (lon, lat) tuples. The defaults reproduce the
    LHR to SJC map the Redwood deck used, so existing callers are unchanged.
    """
    lo0, lo1, la0, la1 = _shaped_frame(origin, destination)
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    m = Basemap(projection="merc", llcrnrlon=lo0, urcrnrlon=lo1,
                llcrnrlat=la0, urcrnrlat=la1, resolution="l", ax=ax)
    fig.set_size_inches(w, w * m.aspect)
    m.drawmapboundary(fill_color=SEA)
    m.fillcontinents(color=LAND, lake_color=SEA)
    m.drawcoastlines(linewidth=0.5, color=COAST)
    m.drawcountries(linewidth=0.5, color=COAST)
    # every longitude below is expressed in the frame's own window, which for a
    # route across the antimeridian runs past 180 rather than wrapping
    def into_frame(lon):
        v = _unwrap(lon, (lo0 + lo1) / 2.0)
        return v + 360.0 if v < lo0 else v

    lons, lats = _gc(origin, destination)
    gx, gy = m([into_frame(v) for v in lons], lats)
    ax.plot(gx, gy, color=RED, linewidth=2.6, zorder=6, solid_capstyle="round")
    o_lon, d_lon = into_frame(origin[0]), into_frame(destination[0])
    # the label sits on the outside of each endpoint, so the two never collide
    west_first = o_lon <= d_lon
    labels = []
    for lon, lat, label, dx, dy, ha in [
            (o_lon, origin[1], origin_label,
             (-0.06 if west_first else 0.012), (0.030 if west_first else -0.055),
             ("right" if west_first else "left")),
            (d_lon, destination[1], destination_label,
             (0.012 if west_first else -0.06), (-0.055 if west_first else 0.030),
             ("left" if west_first else "right"))]:
        x, y = m(lon, lat)
        ax.plot(x, y, "o", color=NAVY, markersize=10, zorder=7,
                markeredgecolor="white", markeredgewidth=1.6)
        xr = ax.get_xlim()[1]
        yr = ax.get_ylim()[1]
        labels.append((ax.text(x + dx * xr, y + dy * yr, label, fontsize=13,
                               fontweight="bold", color=NAVY, ha=ha,
                               va="center", zorder=8), x, y, dx, dy, xr, yr))
    _keep_labels_inside(fig, ax, labels)
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
    return path


def _keep_labels_inside(fig, ax, labels):
    """Turn a label that would run off the frame back into it.

    An endpoint near the edge of its own frame pushes its label outside the
    figure, where the saved PNG clips it: on Edinburgh to Austin the origin sits
    close to the eastern edge and the label read "Edinbur". The width is
    measured after a draw pass rather than estimated from a character count,
    because a guess that is close enough for one place name is not close enough
    for the next one.

    Flipping puts the label on the route side of its marker, which is empty
    water or the frame margin on every shape tested.
    """
    fig.canvas.draw()
    box = ax.get_window_extent()
    edge = 10.0        # a label touching the frame reads as clipped even when it fits
    for txt, x, y, dx, dy, xr, yr in labels:
        ext = txt.get_window_extent(fig.canvas.get_renderer())
        if ext.x0 >= box.x0 + edge and ext.x1 <= box.x1 - edge:
            continue
        txt.set_ha("left" if txt.get_ha() == "right" else "right")
        txt.set_position((x - dx * xr, y + dy * yr))



def catchment_map(path, w=5.6, h=5.0, dpi=210):
    """SJC service area: primary, secondary and contested zones."""
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    m = Basemap(projection="merc", llcrnrlon=-123.15, urcrnrlon=-120.85,
                llcrnrlat=36.35, urcrnrlat=38.35, resolution="i", ax=ax)
    fig.set_size_inches(w, w * m.aspect)
    m.drawmapboundary(fill_color=SEA)
    m.fillcontinents(color="#F4F6EC", lake_color=SEA)
    m.drawcoastlines(linewidth=0.6, color="#9FB0C2")
    m.drawcounties(linewidth=0.45, color="#C8D2DE")

    def zone(clon, clat, rx, ry, colour, alpha):
        t = np.linspace(0, 2 * np.pi, 180)
        lons = clon + rx * np.cos(t)
        lats = clat + ry * np.sin(t)
        x, y = m(lons, lats)
        ax.fill(x, y, color=colour, alpha=alpha, zorder=3,
                edgecolor=colour, linewidth=1.4)

    zone(-121.93, 37.31, 0.38, 0.33, "#1F6FB2", 0.36)      # primary
    zone(-121.88, 37.10, 0.66, 0.64, "#7FC6F0", 0.26)      # secondary
    zone(-122.21, 37.62, 0.28, 0.26, "#FFA800", 0.32)      # contested with SFO

    for lon, lat, lab, col in [(SJC[0], SJC[1], "SJC", NAVY),
                               (SFO[0], SFO[1], "SFO", "#8A5A00"),
                               (-122.221, 37.721, "OAK", "#8A5A00")]:
        x, y = m(lon, lat)
        ax.plot(x, y, "o", color=col, markersize=9, zorder=8,
                markeredgecolor="white", markeredgewidth=1.4)
        ax.text(x, y - 0.028 * ax.get_ylim()[1], lab, fontsize=11,
                fontweight="bold", color=col, ha="center", va="top", zorder=9)
    for lon, lat, lab in [(-121.86, 37.30, "San Jose"),
                          (-122.08, 37.39, "Mountain View"),
                          (-122.14, 37.44, "Palo Alto"),
                          (-121.98, 36.97, "Santa Cruz"),
                          (-121.89, 36.60, "Monterey"),
                          (-121.77, 37.68, "Livermore"),
                          (-121.31, 37.40, "to Modesto"),
                          (-121.55, 36.68, "Salinas")]:
        x, y = m(lon, lat)
        ax.plot(x, y, "s", color="#4A5A6E", markersize=3, zorder=7)
        ax.text(x, y + 0.006 * ax.get_ylim()[1], lab, fontsize=8.0, fontweight="bold",
                color="#3A4A5E", ha="center", va="bottom", zorder=7)
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
    return path


def beyond_map(path, cities, title_free=True, w=9.4, h=3.5, dpi=210):
    """Europe / Middle East / Africa markets beyond London, sized by demand."""
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    m = Basemap(projection="merc", llcrnrlon=-14, urcrnrlon=62,
                llcrnrlat=22, urcrnrlat=63, resolution="l", ax=ax)
    m.drawmapboundary(fill_color=SEA)
    m.fillcontinents(color=LAND, lake_color=SEA)
    m.drawcoastlines(linewidth=0.5, color=COAST)
    m.drawcountries(linewidth=0.5, color=COAST)
    xl, yl = m(LHR[0], LHR[1])
    mx = max(c[3] for c in cities)
    for name, lon, lat, dem in cities:
        x, y = m(lon, lat)
        ax.plot([xl, x], [yl, y], color=MID, linewidth=0.9, alpha=0.55, zorder=4)
        r = 5 + 16 * (dem / mx) ** 0.5
        ax.plot(x, y, "o", color=ORANGE, markersize=r, alpha=0.9, zorder=6,
                markeredgecolor=NAVY, markeredgewidth=0.9)
        ax.text(x, y + 0.022 * ax.get_ylim()[1],
                "%s\n%s" % (name, "{:,.0f}".format(dem)), fontsize=7.4,
                fontweight="bold", color=NAVY, ha="center", va="bottom", zorder=7)
    ax.plot(xl, yl, "o", color=NAVY, markersize=12, zorder=8,
            markeredgecolor="white", markeredgewidth=1.6)
    ax.text(xl, yl - 0.030 * ax.get_ylim()[1], "London", fontsize=11,
            fontweight="bold", color=NAVY, ha="center", va="top", zorder=8)
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
    return path
