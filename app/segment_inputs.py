"""The catchment tier split the eight-segment deck table needs, from a live forecast payload.

WHAT THIS CLOSES. segment_forecast.rows is the last structural gap in the deck contract and it is
the table John needs to ship with a draft forecast. segment_model.from_route_mix builds it and
needs four things the engine does not produce, because the engine forecasts a TOTAL and this table
is an ALLOCATION of that total:

    p2p_base_market   HAVE. the payload's natural market, two-way
    zone_split        DERIVED HERE. leisure demand across primary / secondary / contested
    business_share    DERIVED HERE for the origin. NOT derivable for the destination
    origin_share      NOT DERIVABLE. the origin-resident against destination-resident split
    growth/stim/capture per segment   TWENTY-FOUR JUDGEMENT INPUTS, named by the analyst

catchment.tier_split already implements John's own definition, in its own docstring: primary is
uncontested and within the drive-time band, secondary is uncontested but beyond it out to the
catchment edge, contested is where a competing airport sits at a similar drive time. This module
feeds it from the payload and reports what it produced.

NOTHING IS GUESSED. origin_share and the per-segment inputs have NO DEFAULT here. A table built on
an invented directional split would move every row on the page and read as a measurement, so where
they are absent this returns them as missing by name and the contract keeps its _need note. That is
the flag-rather-than-fill rule, and it is the one that matters most on a page a client reads.

WHY IT IS NOT IN calibrated_forecast. tier_split needs drive times from every locale to the home
airport AND to each competitor, so a route with five competing airports is five times the work of
the catchment endpoint. Putting it in the forecast would slow every call for a figure only the deck
path uses. It is called from the deck path instead.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# The eight segment keys segment_model.from_route_mix expects, named once here so a caller can be
# told exactly what is outstanding rather than discovering it one KeyError at a time.
SEGMENT_KEYS = ("o_bus", "o_pri", "o_sec", "o_con", "d_bus", "d_pri", "d_sec", "d_con")


def tier_inputs(fc, dump=None, radius_km=220.0, min_pop=5000,
                contested_band=20.0, primary_max=60.0):
    """{'zone_split', 'business_share_origin', 'tiers', 'basis'} or {'error': why}.

    Reads the airports from the payload's own catchment block, so the tier split is measured over
    exactly the competing set the forecast used rather than a different one assembled here.
    """
    cat = (fc or {}).get("catchment") or {}
    home = cat.get("home")
    coords = cat.get("coords") or {}
    oll = cat.get("origin_ll") or []
    if not home:
        return {"error": "the payload carries no catchment home airport"}
    if not coords:
        return {"error": "the payload carries no competing-airport coordinates"}
    if len(oll) != 2 or oll[0] is None:
        return {"error": "the payload carries no origin coordinates"}

    try:
        import geonames as G
        from catchment import Airport, CatchmentParams, tier_split
    except Exception as e:                                   # noqa: BLE001
        return {"error": "catchment layer unavailable: %s: %s" % (type(e).__name__, e)}

    # THE APP ALREADY KNOWS WHERE THIS IS, and the first version invented a second answer.
    # cortex_app line 30 is DUMP = os.path.join(HERE, "cities5000.txt") and the file sits beside it
    # in app/, so requiring AVIA_GEONAMES made a working install look broken and sent the run
    # looking for a file it already had. John's ruling of 9 August: everything is calculated in one
    # place. A path is calculated in one place too.
    # AN OVERRIDE THAT POINTS AT NOTHING MUST NOT BEAT A WORKING DEFAULT, and the previous version
    # let it. AVIA_GEONAMES was set to a path with no file on it, so the run failed while
    # cities5000.txt sat in app/ where cortex_app line 30 already finds it. An environment variable
    # is a preference, not a promise that the file is there.
    #
    # Candidates in order, and the FIRST ONE THAT EXISTS is used. Where an override is set and
    # misses, the fallback is taken and SAID, because silently ignoring what somebody explicitly
    # asked for is its own kind of wrong.
    tried, used_fallback = [], None
    if dump is None:
        cands = []
        env = os.environ.get("AVIA_GEONAMES")
        if env:
            cands.append(("AVIA_GEONAMES", env))
        try:
            import cortex_app as _CA
            if getattr(_CA, "DUMP", None):
                cands.append(("cortex_app.DUMP", _CA.DUMP))
        except Exception:                                    # noqa: BLE001
            pass
        cands.append(("beside segment_inputs.py", os.path.join(HERE, "cities5000.txt")))
        for label, p in cands:
            tried.append("%s=%s" % (label, p))
            if p and os.path.exists(p):
                dump = p
                if label != "AVIA_GEONAMES" and env:
                    used_fallback = ("AVIA_GEONAMES is set to %r and no file is there, so %s was "
                                     "used instead" % (env, label))
                break
    if not dump or not os.path.exists(dump):
        return {"error": "no GeoNames dump found. Tried: " + "; ".join(tried)}

    try:
        locales = G.near_point(dump, float(oll[0]), float(oll[1]), radius_km,
                               min_pop=min_pop, propensity=1.0)
    except Exception as e:                                   # noqa: BLE001
        return {"error": "could not read locales: %s: %s" % (type(e).__name__, e)}
    if not locales:
        return {"error": "no populated places within %.0fkm of the origin" % radius_km}

    airports = [Airport(code=c, lat=v[0], lon=v[1]) for c, v in coords.items()
                if v and v[0] is not None]
    if home not in {a.code for a in airports}:
        return {"error": "the home airport %s is not in the payload's catchment coords" % home}

    tiers = tier_split(locales, airports, home, CatchmentParams(),
                       contested_band=contested_band, primary_max=primary_max)
    if not tiers:
        return {"error": "tier_split returned nothing for %s" % home}

    leis = {t: tiers[t]["leisure"] for t in ("primary", "secondary", "contested")}
    tot_leis = sum(leis.values())
    bus = sum(tiers[t]["business"] for t in tiers)
    tot = bus + tot_leis
    if tot_leis <= 0 or tot <= 0:
        return {"error": "the tier split produced no demand, so the shares are undefined"}

    return {
        "zone_split": {t: leis[t] / tot_leis for t in leis},
        "business_share_origin": bus / tot,
        "tiers": {t: {"business": round(tiers[t]["business"]),
                      "leisure": round(tiers[t]["leisure"])} for t in tiers},
        "basis": ("catchment.tier_split over %d locales and %d airports within %.0fkm, "
                  "contested band %.0f min, primary within %.0f min"
                  % (len(locales), len(airports), radius_km, contested_band, primary_max)
                  + (". " + used_fallback if used_fallback else "")),
    }


def missing_for_segments(judgement):
    """What the caller still has to name before the eight-segment table can be built.

    judgement = {"origin_share": f, "growth": {k: f}, "stim": {k: f}, "capture": {k: f}}
    Returned as a list of sentences rather than a boolean, because the contract's _need note has to
    say what is outstanding and "incomplete" is not an instruction to anybody.
    """
    j = judgement or {}
    out = []
    if j.get("origin_share") is None:
        out.append("origin_share: the origin-resident share of the point-to-point market. Not "
                   "derivable from the payload, which carries no directional residency split")
    if j.get("business_share_destination") is None:
        out.append("business_share_destination: the destination end's business share. The origin "
                   "end comes from the catchment; the destination end needs the same analysis at "
                   "the far airport or a stated assumption")
    for name in ("growth", "stim", "capture"):
        d = j.get(name) or {}
        gaps = [k for k in SEGMENT_KEYS if d.get(k) is None]
        if gaps:
            out.append("%s: no value for %s" % (name, ", ".join(gaps)))
    return out


def segment_rows(fc, judgement, base_year, service_year, dump=None):
    """(rows, total, note). rows is None when an input is outstanding, and note says which."""
    ti = tier_inputs(fc, dump=dump)
    if "error" in ti:
        return None, None, "catchment tiers unavailable: " + ti["error"]
    miss = missing_for_segments(judgement)
    if miss:
        return None, None, "the eight-segment table needs: " + "; ".join(miss)

    import segment_model as SM
    natural_ew = ((fc.get("demand") or {}).get("natural")) or 0.0
    j = judgement
    rows, total = SM.from_route_mix(
        p2p_base_market=natural_ew * 2.0,          # the payload is each way; this table is two-way
        origin_share=float(j["origin_share"]),
        business_share={"origin": ti["business_share_origin"],
                        "destination": float(j["business_share_destination"])},
        zone_split=ti["zone_split"],
        growth=j["growth"], capture=j["capture"], stim=j["stim"],
        base_year=base_year, service_year=service_year)
    return rows, total, ti["basis"]


if __name__ == "__main__":
    # The judgement check, on a part-filled set, so the message a caller sees is legible.
    j = {"origin_share": 0.62, "growth": {k: 0.03 for k in SEGMENT_KEYS},
         "stim": {k: 1.15 for k in SEGMENT_KEYS},
         "capture": {"o_bus": 0.3, "o_pri": 0.3}}
    print("outstanding inputs:")
    for line in missing_for_segments(j):
        print("  -", line)
