#!/usr/bin/env python3
"""Draw the deck's figures from the engine output, and say what did not draw.

The visual layer was the deck's largest gap: the generated document carried
tables and numbers and not a single figure, so a prose page ran about 60% empty
and the whole thing read thinner than the work behind it. This module is the
build-time step that closes it. It renders PNGs into a run directory and hands
back the paths, and `spec_from_research` places them.

Two figures, and only two. A figure has to earn its page:

    route_map      the great circle, on the page that opens the forecast. It
                   states physically what is being proposed and it carries the
                   sector distance and block time, which nothing else in the
                   deck says.
    demand_build   the market, the three legs of demand the nonstop reaches,
                   and the line the aircraft actually carries at the planned
                   load factor. That is the forecast argument on one page.

Everything else the deck shows is a lookup and belongs in a table.

REPORTING, NOT FALLING BACK. Three silent fallbacks surfaced in this codebase
on 6 August, all the same shape: a missing config key, a missing function and an
empty column each substituted a default without saying so. Nothing here
substitutes anything. A figure that cannot be drawn is absent, and the reason is
returned in `notes`, printed by the runner and written into the audit.

Avia Solutions Limited. All rights reserved.
"""

import os


def _ll(pair):
    """A [lat, lon] pair from the engine, as the (lon, lat) the maps take."""
    try:
        lat, lon = float(pair[0]), float(pair[1])
    except (TypeError, ValueError, IndexError):
        return None
    if lat == 0.0 and lon == 0.0:
        return None                      # null island is an unpopulated field
    return (lon, lat)


def _endpoints(fc):
    """Coordinates for both ends, from the catchment block or the airport block.

    The engine puts them in `catchment` as origin_ll and dest_ll. The offline
    stub has no catchment and carries the origin only, from the command line, so
    a stub run draws no map and says why rather than drawing one endpoint.
    """
    cat = fc.get("catchment") or {}
    o = _ll(cat.get("origin_ll"))
    d = _ll(cat.get("dest_ll"))
    if o is None:
        ob = fc.get("origin") or {}
        o = _ll([ob.get("lat"), ob.get("lon")])
    if d is None:
        db = fc.get("dest") or {}
        d = _ll([db.get("lat"), db.get("lon")])
    return o, d


def _city(block, fallback=""):
    return (block or {}).get("city") or (block or {}).get("iata") or fallback


def build(fc, outdir, source=None, want=("route_map", "demand_build")):
    """Render the figures for this route.

    Returns (figures, notes).

    figures  {slot: absolute path}, carrying only what was drawn
    notes    {slot: reason} for every requested figure that was not drawn
    """
    figures, notes = {}, {}
    fc = fc or {}
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    origin_city = _city(fc.get("origin"), "the origin")
    dest_city = _city(fc.get("dest"), "the destination")

    if "route_map" in want:
        o, d = _endpoints(fc)
        if o is None or d is None:
            notes["route_map"] = (
                "no coordinates for %s; the engine returns them in "
                "catchment.origin_ll and catchment.dest_ll, and a stub forecast "
                "carries neither"
                % ("either endpoint" if o is None and d is None else
                   "the destination" if d is None else "the origin"))
        else:
            path = os.path.join(outdir, "fig_route_map.png")
            try:
                import avia_maps
                avia_maps.route_map(path, origin=o, destination=d,
                                    origin_label=origin_city,
                                    destination_label=dest_city)
                figures["route_map"] = path
            except ImportError as e:
                notes["route_map"] = (
                    "%s. avia_maps needs matplotlib and basemap; install "
                    "basemap or the deck runs without a map" % e)
            except Exception as e:
                notes["route_map"] = "%s: %s" % (type(e).__name__, e)

    if "demand_build" in want:
        dem = fc.get("demand") or {}
        cap = fc.get("capacity") or {}
        market = dem.get("natural")
        if not market:
            notes["demand_build"] = ("demand.natural is empty, so there is no "
                                     "catchment market to draw the build against")
        else:
            path = os.path.join(outdir, "fig_demand_build.png")
            try:
                import avia_charts
                got = avia_charts.demand_build(
                    path, market=market, p2p_carried=dem.get("p2p_carried"),
                    feed_behind=dem.get("feed_behind"),
                    feed_beyond=dem.get("feed_beyond"),
                    carried=dem.get("total"), load=cap.get("load"),
                    origin_city=origin_city, dest_city=dest_city,
                    year=fc.get("year"),
                    **({"source": source} if source else {}))
                if got:
                    figures["demand_build"] = path
                else:
                    notes["demand_build"] = (
                        "the three carried legs are all empty: p2p_carried, "
                        "feed_behind and feed_beyond sum to zero")
            except ImportError as e:
                notes["demand_build"] = "%s. avia_charts needs matplotlib" % e
            except Exception as e:
                notes["demand_build"] = "%s: %s" % (type(e).__name__, e)

    return figures, notes


# ---------------------------------------------------------------------------
# Airport figures, from the stores rather than from the research prose.
#
# John, 7 August: "Given all the data we have I am sure there is valuable data
# we could create charts with." The research findings are single-sourced points
# and always will be, so they carry no series to plot. The stores do.
#
# Which end each chart is about is fixed here rather than left to the caller,
# because a destination passenger series on the origin airport page is the kind
# of error that reads as carelessness.
# ---------------------------------------------------------------------------

AIRPORT_FIGURES = ("airport_pax", "airport_haul", "airport_airlines",
                   "airport_load", "dest_pax")


def _profile_module():
    """airport_profile lives in app/, which is not always on the path."""
    try:
        import airport_profile as AP
        return AP
    except ImportError:
        pass
    import sys
    # Found by landmark rather than by relative candidates. This block previously ended in
    # a hardcoded C:\AviaDev\app, which worked and breaks point 4 of the tool standard: a
    # path in code is a path that is wrong on the next machine.
    import deck_paths as _DP
    cand = _DP.engine_dir(os.path.dirname(os.path.abspath(__file__)))
    if cand:
        if cand not in sys.path:
            sys.path.insert(0, cand)
        try:
            import airport_profile as AP
            return AP
        except ImportError:
            pass
    return None


def _carrier_names(fc):
    """IATA code to airline name, from the tool's own reference.

    `app/airline_names.py` already holds this for the dashboard typeahead, so
    the chart uses it rather than shipping a second copy that drifts. A caller
    may override or extend it through fc["carrier_names"]. A code the map does
    not hold still plots, as its code, which is what the engine does too.
    """
    names = {}
    try:
        import airline_names as AN
        names.update(AN.AIRLINES)
    except Exception:
        pass
    names.update((fc or {}).get("carrier_names") or {})
    return names


def _stores(given=None):
    """Store paths from config, or whatever the caller passed instead."""
    st = dict(given or {})
    if st.get("oag") and st.get("aci") and st.get("t100"):
        return st
    try:
        import config as CFG
        st.setdefault("oag", str(CFG.OAG_DUCKDB))
        st.setdefault("aci", str(CFG.ACI_DUCKDB))
        st.setdefault("t100", str(CFG.T100_DUCKDB))
    except Exception:
        pass
    return st


def _pax_series(AP, iata, country, st):
    """Passengers a year at an airport, from the source its audience trusts."""
    got = AP.pax_by_year(iata, country, stores=st)
    if got["series"]:
        return got["series"], got["label"], got["kind"], ""
    return [], got.get("label"), None, "; ".join(got["notes"])


def build_airport(fc, outdir, stores=None, want=AIRPORT_FIGURES):
    """Render the airport charts for both ends of the route.

    Returns (figures, notes, sources). Same contract as build() on the first
    two: a chart that cannot be drawn honestly is absent and the reason comes
    back in notes. `sources` is the attribution line for each drawn chart, for
    the caller to place under the figure on the slide.
    """
    figures, notes, sources = {}, {}, {}
    fc = fc or {}
    want = set(want or ())
    if not want:
        return figures, notes, sources
    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    AP = _profile_module()
    if AP is None:
        for slot in want:
            notes[slot] = ("airport_profile could not be imported; app/ is not "
                           "on sys.path for this process")
        return figures, notes, sources
    try:
        import avia_charts as AC
    except ImportError as e:
        for slot in want:
            notes[slot] = "%s. the airport charts need matplotlib" % e
        return figures, notes, sources

    st = _stores(stores)
    ob, db = fc.get("origin") or {}, fc.get("dest") or {}
    o_iata = (ob.get("iata") or "").upper()
    d_iata = (db.get("iata") or "").upper()
    o_city = _city(ob, o_iata or "the origin")
    d_city = _city(db, d_iata or "the destination")

    prof = None
    if o_iata and st.get("oag") and os.path.exists(st["oag"]):
        country = ob.get("country") or AP.aci_country(st.get("aci") or "", o_iata)
        prof = AP.profile(st["oag"], o_iata, home_country=country)
    elif want & {"airport_haul", "airport_airlines", "airport_load"}:
        for slot in want & {"airport_haul", "airport_airlines", "airport_load"}:
            notes[slot] = ("no OAG store at %s, or the forecast carries no "
                           "origin IATA" % st.get("oag"))

    def draw(slot, fn, src_label="", **kw):
        """Render one chart and record the source line for its slide.

        The source is NOT baked into the PNG for deck use. It belongs under the
        figure in the deck's own typography, which is also what the build audit
        checks for; a line printed inside the image at 7pt in the chart's font
        satisfies neither.
        """
        if slot not in want:
            return
        path = os.path.join(outdir, "fig_%s.png" % slot)
        try:
            if fn(path, embed_source=False, **kw):
                figures[slot] = path
                sources[slot] = AC.airport_source(
                    slot, src_label or kw.get("label", ""))
            else:
                notes[slot] = ("the series is too short to plot; three years "
                               "are the minimum and the store holds fewer")
        except Exception as e:
            notes[slot] = "%s: %s" % (type(e).__name__, e)

    # passengers at the origin, from ACI or DOT
    if o_iata:
        country = ob.get("country") or AP.aci_country(st.get("aci") or "", o_iata)
        pax, label, kind, why = _pax_series(AP, o_iata, country, st)
        if pax:
            # `kind` reaches the chart, so the title and axis say which
            # measure this is. Without it a DOT departing count and an ACI
            # throughput both print as "total passengers".
            draw("airport_pax", AC.airport_pax, series=pax, airport=o_city,
                 label=label, measure=kind)
        elif "airport_pax" in want:
            notes["airport_pax"] = why or "no passenger series for %s" % o_iata

        if prof and prof.get("ok") and pax and "airport_load" in want:
            lf, lnote = AP.effective_load_factor(prof["seats"], pax, kind)
            if lf and "CHECK THE UNITS" in lnote:
                # AN IMPLAUSIBLE LOAD FACTOR IS NOT DRAWN. The first version put
                # the chart on the slide and filed the warning in the audit, so
                # a 159% load factor would have gone to a client with a note
                # nobody reads. If the two series are not measuring the same
                # thing, the answer is no chart, and the reason said out loud.
                notes["airport_load"] = lnote
            elif lf:
                draw("airport_load", AC.airport_load, src_label=label,
                     series=lf, airport=o_city, pax_label=label,
                     halved=(kind == "throughput"))
            else:
                notes["airport_load"] = lnote

    if prof and prof.get("ok"):
        if prof.get("haul"):
            draw("airport_haul", AC.airport_haul, haul=prof["haul"],
                 airport=o_city)
        elif "airport_haul" in want:
            notes["airport_haul"] = "; ".join(prof["notes"]) or "no market split"
        if prof.get("airlines"):
            draw("airport_airlines", AC.airport_airlines,
                 airlines=prof["airlines"], airport=o_city,
                 year=prof["latest"], names=_carrier_names(fc))
        elif "airport_airlines" in want:
            notes["airport_airlines"] = "no carrier column in the OAG store"

    # the destination's own traffic, for the sections about the far end
    if d_iata and "dest_pax" in want:
        country = db.get("country") or AP.aci_country(st.get("aci") or "", d_iata)
        pax, label, dkind, why = _pax_series(AP, d_iata, country, st)
        if pax:
            draw("dest_pax", AC.airport_pax, series=pax, airport=d_city,
                 label=label, measure=dkind)
        else:
            notes["dest_pax"] = why or "no passenger series for %s" % d_iata

    return figures, notes, sources


def route_facts(fc):
    """The lines that sit under the route map. Figures only, no adjectives.

    Each is read from the engine's own field. Where a field is unpopulated the
    line is dropped rather than estimated: an invented block time on a sales
    deck is the kind of number a planner checks first.
    """
    out = []
    nm = fc.get("distance_nm")
    if nm:
        out.append("Sector distance %s nm, great circle."
                   % format(int(nm), ","))
    mins = fc.get("block_min")
    if mins:
        out.append("Block time %dh %02dm each way."
                   % (int(mins) // 60, int(mins) % 60))
    sch = (fc.get("schedule") or {}).get("outbound") or {}
    if sch.get("dep") and sch.get("arr"):
        out.append("Illustrative timing, outbound %s to %s local."
                   % (sch["dep"], sch["arr"]))
    return out
