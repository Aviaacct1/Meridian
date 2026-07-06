#!/usr/bin/env python3
"""
Avia Solutions - LOPA store (cabin layout by airline + aircraft).
==============================================================================
The route economics and the deck cabin layer need the Layout of Passenger Accommodation
(seats by First / Business / Premium-economy / Economy) for the airline and aircraft on a
route. SeatGuru shut down on 31 Oct 2025, so the old "look it up on the airline website each
pitch" route is gone. This is a STATIC store, refreshed once a year from an internet source,
with an AVERAGE-LOPA fallback per aircraft type when a specific carrier's config is missing.

Refresh sources (annual), in order of preference:
  - airline fleet tables on Wikipedia / Wikidata: free, CC-licensed, structured, genuinely
    downloadable -> the default refresh feed (parse fleet pages into lopa_store.json).
  - aeroLOPA (aerolopa.com): the quality standard for accurate seat maps, for manual
    verification of a specific carrier when pitching (visual, not a bulk download).
  - FlightSeatmap.com (6,100 airlines) / SeatMaps.com (739) as cross-checks.
  - Cirium / ch-aviation fleet feed if a paid authoritative source is wanted.

The carrier-specific configs live in lopa_store.json (refreshable, no code change). The
per-type AVERAGES live here as the fallback so the model always returns a usable LOPA.
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))

# Average / typical LOPA per aircraft type (the fallback when a carrier config is missing).
# Seats by cabin; total matches the aircraft_economics AIRCRAFT seat count where possible.
# These are representative long-haul three-class layouts; refine from the annual feed.
AVERAGES = {
    "B788": {"first": 0, "business": 30, "premium_coach": 21, "coach": 184, "total": 235},
    "B789": {"first": 0, "business": 30, "premium_coach": 28, "coach": 232, "total": 290},
    "B78X": {"first": 0, "business": 34, "premium_coach": 28, "coach": 256, "total": 318},
    "A359": {"first": 0, "business": 36, "premium_coach": 24, "coach": 240, "total": 300},
    "A35K": {"first": 0, "business": 44, "premium_coach": 28, "coach": 287, "total": 359},
    "A333": {"first": 0, "business": 30, "premium_coach": 21, "coach": 226, "total": 277},
    "A339": {"first": 0, "business": 30, "premium_coach": 28, "coach": 229, "total": 287},
    "B763": {"first": 0, "business": 24, "premium_coach": 0, "coach": 221, "total": 245},
    "B77W": {"first": 8, "business": 40, "premium_coach": 24, "coach": 268, "total": 340},
    "A21X": {"first": 0, "business": 20, "premium_coach": 0, "coach": 162, "total": 182},
    "A21N": {"first": 0, "business": 16, "premium_coach": 0, "coach": 190, "total": 206},
    "B752": {"first": 0, "business": 16, "premium_coach": 0, "coach": 183, "total": 199},
}


def load_store(path=None):
    """The refreshable carrier-specific store. Missing file = empty (averages still work)."""
    path = path or os.path.join(HERE, "lopa_store.json")
    if not os.path.exists(path):
        return {"_meta": {"note": "no store file; using type averages only"}, "airlines": {}}
    return json.load(open(path))


def get_lopa(aircraft, airline_iata=None, variant=None, store=None):
    """Return the LOPA for an airline+aircraft (optionally a named variant), falling back to the
    type average. Result carries its source so the deck can footnote it. Never returns None for a
    known aircraft type: a missing carrier config degrades to the average, an unknown type to None."""
    store = store if store is not None else load_store()
    air = (store.get("airlines", {}).get((airline_iata or "").upper(), {}) if airline_iata else {})
    entry = air.get(aircraft)
    if entry:
        # an airline+type may hold several named variants (e.g. BA 787-9 8-first vs no-first)
        if isinstance(entry, dict) and "variants" in entry:
            vs = entry["variants"]
            chosen = (vs.get(variant) if variant else None) or vs.get(entry.get("default")) or next(iter(vs.values()))
            return {**chosen, "source": entry.get("source", "store"), "airline": airline_iata,
                    "aircraft": aircraft, "variant": variant or entry.get("default"), "basis": "carrier"}
        return {**entry, "source": entry.get("source", "store"), "airline": airline_iata,
                "aircraft": aircraft, "basis": "carrier"}
    avg = AVERAGES.get(aircraft)
    if avg:
        return {**avg, "source": "type average (carrier config not in store)", "airline": airline_iata,
                "aircraft": aircraft, "basis": "average"}
    return None


def variants_for(aircraft, airline_iata, store=None):
    """All named LOPA variants a carrier flies for a type (so the selector can choose the best fit)."""
    store = store if store is not None else load_store()
    entry = store.get("airlines", {}).get((airline_iata or "").upper(), {}).get(aircraft)
    if entry and isinstance(entry, dict) and "variants" in entry:
        return entry["variants"]
    lop = get_lopa(aircraft, airline_iata, store=store)
    return {"default": lop} if lop else {}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Look up a LOPA (carrier config or type average).")
    ap.add_argument("aircraft"); ap.add_argument("--airline", default=None); ap.add_argument("--variant", default=None)
    a = ap.parse_args()
    lop = get_lopa(a.aircraft, a.airline, a.variant)
    if not lop:
        print(f"no LOPA for {a.aircraft} (unknown type)")
    else:
        print(f"{a.airline or 'generic'} {a.aircraft}"
              + (f" [{lop.get('variant')}]" if lop.get('variant') else "")
              + f": F{lop['first']} J{lop['business']} W{lop['premium_coach']} Y{lop['coach']} "
              f"= {lop['total']}  ({lop['basis']}: {lop['source']})")
