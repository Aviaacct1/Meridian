#!/usr/bin/env python3
r"""Avia Solutions - airport charges for the route P&L, with provenance, per airport pair.

WHY THIS EXISTS. On a short sector airport and handling charges are the largest line in the route
P&L: on LCY-EDI they were 56% of cost against fuel at 15%. Until 10 August 2026 the forecast path
passed route_engine.DEFAULT_CHARGES for BOTH ends of every route, a flat 2,000 USD landing, 1,500
handling and 20 USD a passenger, and it did so even where the module already held real figures for
the airport. LCY and EDI were both in aircraft_economics.AIRPORTS and both ignored. Measured at 155
passengers, the generic set charged 13,200 USD a turn against 5,130 held, and omitted 3,320 USD of
charges recovery, which is revenue. An 11,390 USD swing on a route reporting a 1,980 USD loss, which
is why the tool called a route unprofitable that BA CityFlyer flies daily.

WHAT IT DOES. Resolves charges for one airport in this order, and says which was used:

  measured    an entry in airport_charges.json, populated from RDC AirportCharges or the airport's
              own published schedule, with a source and a date
  held        an entry in aircraft_economics.AIRPORTS, which is a small seeded set
  generic     route_engine.DEFAULT_CHARGES, a placeholder that is not this airport

LANDING FEES ARE WEIGHT BASED, so an entry may give landing_per_tonne and the fee is computed
against the aircraft's MTOW. That is what makes a table of a few hundred airports work across every
aircraft type instead of needing a cell per airport per type. A flat landing_per_turn is accepted
where an airport's schedule genuinely is flat, or where only a worked example is available.

WHAT IT IS NOT. Published charges are a CEILING. Most carriers negotiate below them and many airports
offer new-route incentives that waive them entirely for a period. Nothing here knows what a carrier
actually pays, so the P&L treats charges as a declared plug the client sets, and the payload names
the provenance so a reader can tell a measured figure from a placeholder.

Avia Solutions Limited. All rights reserved.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.environ.get("AVIA_AIRPORT_CHARGES") or os.path.join(HERE, "airport_charges.json")

FIELDS = ("landing_per_turn", "landing_per_tonne", "pax_charge_per_pax",
          "ground_handling_per_turn", "recovery_per_pax")

_CACHE = None


def _load():
    """The populated store, or an empty dict. Never raises: a missing file means nothing is
    measured yet, which is a state the caller must handle anyway."""
    global _CACHE
    if _CACHE is None:
        _CACHE = {}
        try:
            with open(STORE, encoding="utf-8") as fh:
                blob = json.load(fh)
            _CACHE = {str(k).strip().upper(): v for k, v in (blob.get("airports") or {}).items()}
        except Exception:
            _CACHE = {}
    return _CACHE


def reload_store():
    """Drop the cache, so a freshly populated file is picked up without a restart."""
    global _CACHE
    _CACHE = None
    return _load()


def charges_for(iata, mtow_kg=None):
    """(charges dict for RoutePnL, provenance, source string) for one airport.

    mtow_kg lets a weight-based landing fee be computed for the aircraft actually being flown. Left
    None, a per-tonne entry falls back to its flat figure if it has one, and otherwise to generic,
    because guessing a weight would put an invented number into a client's P&L.
    """
    import route_engine as RE
    code = (iata or "").strip().upper()

    rec = _load().get(code)
    if rec:
        out = {k: float(rec.get(k) or 0.0) for k in
               ("pax_charge_per_pax", "ground_handling_per_turn", "recovery_per_pax")}
        per_t = rec.get("landing_per_tonne")
        if per_t and mtow_kg:
            out["landing_per_turn"] = float(per_t) * (float(mtow_kg) / 1000.0)
        elif rec.get("landing_per_turn"):
            out["landing_per_turn"] = float(rec["landing_per_turn"])
        else:
            out["landing_per_turn"] = float(RE.DEFAULT_CHARGES["landing_per_turn"])
            return out, "part measured", (str(rec.get("source") or "") +
                                          " (landing fell back to the generic figure)")
        return out, "measured", str(rec.get("source") or "airport_charges.json, source not stated")

    try:
        from aircraft_economics import AIRPORTS
        held = AIRPORTS.get(code)
    except Exception:
        held = None
    if held:
        out = {k: float(held.get(k) or 0.0) for k in
               ("landing_per_turn", "pax_charge_per_pax", "ground_handling_per_turn",
                "recovery_per_pax")}
        return out, "held", "aircraft_economics.AIRPORTS, seeded set"

    return dict(RE.DEFAULT_CHARGES), "generic", ("route_engine.DEFAULT_CHARGES placeholder, "
                                                 "NOT this airport")


def pair_charges(origin, dest, mtow_kg=None):
    """Both ends at once, with a single provenance for the pair: the WEAKER of the two, because a
    P&L is only as sourced as its weakest input and the far end is the known weak point."""
    o, po, so = charges_for(origin, mtow_kg)
    d, pd, sd = charges_for(dest, mtow_kg)
    rank = {"measured": 3, "part measured": 2, "held": 1, "generic": 0}
    worst = po if rank.get(po, 0) <= rank.get(pd, 0) else pd
    return {
        "origin": o, "dest": d,
        "origin_provenance": po, "dest_provenance": pd,
        "origin_source": so, "dest_source": sd,
        "provenance": worst,
        "is_plug": worst in ("generic", "held"),
    }


def coverage():
    """How many airports are populated, for the audit."""
    return sorted(_load())


if __name__ == "__main__":
    import sys
    pairs = sys.argv[1:] or ["LCY", "EDI", "SJC", "TPE"]
    print("store: %s (%d airports populated)" % (STORE, len(coverage())))
    for a in pairs:
        c, prov, src = charges_for(a, mtow_kg=51800)
        print("  %-4s %-13s landing %8.0f  pax %6.2f  handling %8.0f  recovery %6.2f  | %s"
              % (a, prov, c["landing_per_turn"], c["pax_charge_per_pax"],
                 c["ground_handling_per_turn"], c["recovery_per_pax"], src))
