#!/usr/bin/env python3
"""
Avia Solutions - offline global drive times from a friction raster (the real catchment fix).
============================================================================================
Straight-line distance mis-draws every catchment where geography bites (Genoa->Milan is a 3.5hr
Apennine drive that great-circle reads as 1.5hr), and the QSI forecast is demand off the catchment,
so a mis-drawn catchment mis-sizes the forecast. This computes REAL road travel times, offline, for
ANY airport on Earth, so the tool runs for whoever walks up at World Routes - Cardiff, Stansted,
Tahiti, Timbuktu - with nothing pre-built per airport.

Method: a global motorized friction surface (Malaria Atlas Project 2019, GeoTIFF, band = minutes to
travel one metre, land from 85N to 60S). For an airport we window the raster to a box around it, turn
friction into a per-pixel minutes-to-cross cost, and run a least-cost accumulation (scikit-image MCP)
outward from the airport pixel. Every populated place's drive time is then read straight off the
result. Only the patch around the named airport is read, so it stays fast and offline on a laptop.

Needs (on the machine with the data): pip install rasterio scikit-image numpy, and the friction
GeoTIFF (e.g. C:\\Avia\\friction_2019.tif). Wire into qsi_capture_share by filling Locale.drive_min;
catchment.run_catchment already prefers drive_min over great-circle when present.

    from drive_times import DriveTimes
    dt = DriveTimes(r"C:\\Avia\\friction_2019.tif")
    mins = dt.times_from("LHR", 51.4706, -0.4619, [(51.5,-0.12),(51.45,-2.58)])  # London, Bristol
"""
import math, os

DEG_M = 111_320.0          # metres per degree latitude (mean)
WINDOW_KM = 450.0          # half-box read around an airport (>> the 220km catchment radius)
NODATA_MIN_PER_M = 0.06    # impassable / sea fallback friction (slow), keeps MCP finite


class DriveTimes:
    def __init__(self, friction_path, window_km=WINDOW_KM):
        self.path = friction_path
        self.window_km = window_km
        self._ok = os.path.exists(friction_path)

    def available(self):
        return self._ok

    def times_from(self, code, ap_lat, ap_lon, points):
        """Return [minutes] from the airport to each (lat, lon) in points via least-cost road travel.
        Returns None if the raster or libraries are absent (caller falls back to great-circle)."""
        if not self._ok:
            return None
        try:
            import numpy as np
            import rasterio
            from rasterio.windows import from_bounds
            from skimage.graph import MCP_Geometric
        except Exception:
            return None

        dlat = self.window_km / 111.0
        dlon = self.window_km / (111.0 * max(math.cos(math.radians(ap_lat)), 0.05))
        with rasterio.open(self.path) as src:
            win = from_bounds(ap_lon - dlon, ap_lat - dlat, ap_lon + dlon, ap_lat + dlat,
                              src.transform).round_offsets().round_lengths()
            fr = src.read(1, window=win).astype("float64")
            tr = src.window_transform(win)
            nod = src.nodata

        if fr.size == 0:
            return None
        # friction (min/m) -> minutes to CROSS one pixel = friction * pixel_length_m
        px_deg = abs(tr.a)                                   # pixel width in degrees
        lat0 = ap_lat
        pix_m = 0.5 * (px_deg * DEG_M + px_deg * DEG_M * max(math.cos(math.radians(lat0)), 0.05))
        bad = ~np.isfinite(fr)
        if nod is not None:
            bad |= (fr == nod)
        bad |= (fr <= 0)
        fr[bad] = NODATA_MIN_PER_M
        cost = fr * pix_m                                    # minutes per pixel traverse

        def rc(lat, lon):
            col = int((lon - tr.c) / tr.a)
            row = int((lat - tr.f) / tr.e)
            return row, col

        H, W = cost.shape
        ar, ac = rc(ap_lat, ap_lon)
        ar = min(max(ar, 0), H - 1); ac = min(max(ac, 0), W - 1)
        mcp = MCP_Geometric(cost)
        cum, _ = mcp.find_costs([(ar, ac)])

        out = []
        for (lat, lon) in points:
            r, c = rc(lat, lon)
            if 0 <= r < H and 0 <= c < W and np.isfinite(cum[r, c]):
                out.append(float(cum[r, c]))
            else:
                # outside the window: fall back to great-circle at 70 km/h
                gc = _gc_km(ap_lat, ap_lon, lat, lon)
                out.append(gc / 70.0 * 60.0)
        return out


def _gc_km(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c - a), math.radians(d - b)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))


def _self_test():
    """Prove the least-cost logic on a SYNTHETIC raster (no real file needed): a fast plain with a
    slow mountain wall between the airport and a town behind it. The detour time must exceed the
    straight-line time - the Genoa/Milan effect in miniature."""
    import numpy as np
    try:
        from skimage.graph import MCP_Geometric
    except Exception:
        print("scikit-image not installed; install it on the data machine. Logic test skipped.")
        return
    n = 200
    fast = 0.0008                       # ~75 km/h plain (min per metre)
    cost = np.full((n, n), fast * 1000) # 1km pixels -> minutes per pixel
    cost[:, 100:110] = fast * 1000 * 25  # a mountain wall, 25x slower, with a gap
    cost[150:160, 100:110] = fast * 1000 # a pass through the wall at the bottom
    mcp = MCP_Geometric(cost)
    cum, _ = mcp.find_costs([(20, 20)])         # airport on the left plain
    behind = cum[20, 180]                       # town straight across the wall
    near = cum[20, 60]                          # town on the same side
    straight_equiv = (180 - 20) * fast * 1000   # if the wall weren't there
    print(f"same-side town: {near:6.0f} min")
    print(f"behind-wall town (must detour to the pass): {behind:6.0f} min "
          f"vs {straight_equiv:.0f} min if no mountains")
    print("PASS: mountains force a longer drive" if behind > straight_equiv * 1.3
          else "CHECK: barrier not biting")


def _check(path):
    """Open the REAL raster and compute known drive times, so a silent great-circle fallback shows
    up. Genoa->Milan should be ~3 to 3.5hr (the Apennines); Sacramento->San Francisco ~1.5hr."""
    import importlib
    for lib in ("numpy", "rasterio", "skimage"):
        try:
            importlib.import_module(lib)
            print(f"  {lib}: OK")
        except Exception as e:
            print(f"  {lib}: MISSING -> {e}")
    dt = DriveTimes(path)
    print(f"raster path: {path}\nraster present on disk: {dt.available()}")
    tests = [("GOA", 44.4133, 8.8375, [("Milan MXP", 45.630, 8.728), ("Genoa centre", 44.411, 8.933)]),
             ("SMF", 38.6954, -121.5908, [("San Francisco", 37.615, -122.389), ("Sacramento", 38.58, -121.49)])]
    for code, la, lo, pts in tests:
        times = dt.times_from(code, la, lo, [(p[1], p[2]) for p in pts])
        if times is None:
            print(f"{code}: times_from returned None -> falling back to great-circle (raster/libs not used)")
        else:
            for (nm, _, _2), t in zip([(p[0], p[1], p[2]) for p in pts], times):
                print(f"{code} -> {nm}: {t:.0f} min")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "--check":
        _check(sys.argv[2])
    else:
        _self_test()
