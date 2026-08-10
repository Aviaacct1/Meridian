#!/usr/bin/env python3
"""Avia Solutions - what this machine is running, when two machines disagree.

    py -3.12 env_report.py

Written 10 August 2026 after the Dev PC returned 134,580 two-way on SJC-TPE against 134,616 from a
second machine reading the SAME stores. A 0.03% gap is immaterial to a deck and material to trust:
the same code on the same data must give the same answer, and where it does not the cause belongs in
writing rather than in a shrug. The stores are named by path, so a difference here is the
environment, never the data.

Prints the resolved run context, the library versions that reach into the catchment, whether the
water-boundary check is active, and the competing airport set the forecast will use. Run it on both
machines and diff the output.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def main():
    import duckdb
    import airportsdata
    import cortex_app as CA
    import route_engine as RE
    import geo_resolve as GEO

    origin = sys.argv[1] if len(sys.argv) > 1 else "SJC"
    radius = float(sys.argv[2]) if len(sys.argv) > 2 else 220.0

    ctx = CA._live_ctx()
    print("python          %s" % sys.version.split()[0])
    print("duckdb          %s" % duckdb.__version__)
    print("airportsdata    %s" % getattr(airportsdata, "__version__", "unknown"))
    try:
        import global_land_mask                       # noqa: F401
        print("water check     ON  (global-land-mask installed)")
    except ImportError:
        # Said plainly. With the check off, a coastal or island catchment keeps cells that fall over
        # water and the market reads high. Jessica's fix of 3 July is inert on a machine without it.
        print("water check     OFF (global-land-mask NOT installed, coastal catchments over-read)")

    print("sabre store     %s" % (os.environ.get("AVIA_SABRE") or "default C:\\Avia\\sabre.duckdb"))
    print("oag store       %s" % (os.environ.get("AVIA_OAG") or "default C:\\Avia\\oag.duckdb"))
    print("oag week        %s" % ctx["week"])
    print("sabre year      %s" % ctx["year"])
    print("freq switch     %s" % (os.environ.get("AVIA_FREQ_SENSITIVE") or "off"))
    print("freq reference  %s" % (os.environ.get("AVIA_FREQ_REF") or "7.0 (default)"))
    print("forecast engine %s" % (os.environ.get("AVIA_FORECAST_ENGINE") or "qsi (default)"))

    om = GEO.resolve_metro(origin, served_index=ctx["served"], dump=CA.DUMP, expand=False)
    ap = RE._airports()
    o = ap.get(om["primary"])
    served = set(ctx["served_codes"]) or None
    comp = sorted(r["iata"] for r in RE.competing_airports(o, radius, served, True))
    print("origin          %s -> %s" % (origin, om["primary"]))
    print("competing (%d)   %s" % (len(comp), " ".join(comp)))


if __name__ == "__main__":
    main()
