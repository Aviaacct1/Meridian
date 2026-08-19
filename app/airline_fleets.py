"""Avia Cortex - airline fleet families, so the aircraft picker ties to what a carrier actually flies
(no Ryanair on an A380). Codes are AIRCRAFT keys in aircraft_economics. Families, not tail-by-tail:
enough to constrain the type sensibly. Unknown airlines fall back to all range-feasible types.
Extend from Egnyte fleet data as it lands.
"""
# narrowbody families available as AIRCRAFT keys: A319 A320 A20N A321 A21N A21X B738 B38M B752 C919
#   plus the A220 family, A221 and A223, costed in aircraft_economics since 10 Aug 2026 -
#   the picker only offers what THIS table lists, so a costed type an operator flies must
#   also appear here (found 19 Aug 2026: AF ran without its A220-300s)
# widebody: B763 A333 A339 B788 B789 A359 B77W ; regional: ATR72 DH8D CRJ900 E170 E190 E195 SF34 C909
FLEETS = {
    # ---- ultra-low-cost / low-cost (the ones that must NOT get a widebody) ----
    "FR": ["B738", "B38M"], "RK": ["B738", "B38M"],
    "U2": ["A319", "A320", "A20N", "A321", "A21N"],
    "W6": ["A320", "A20N", "A321", "A21N"], "W9": ["A320", "A21N"], "W4": ["A321", "A21N"],
    "VY": ["A319", "A320", "A321"], "EW": ["A319", "A320", "A21N"],
    "DY": ["B738", "B38M"], "D8": ["B738", "B38M"],
    "LS": ["B738", "A321"], "BY": ["B738", "B38M", "B788"], "PC": ["A320", "A20N", "A21N"],
    "TO": ["B738"], "HV": ["B738", "B38M"], "V7": ["A319", "A320"], "NT": ["A320"],
    "0B": ["B738"], "XQ": ["B738", "B38M"], "XG": ["B738"], "NO": ["B737", "B789"],
    "G4": ["A319", "A320"], "NK": ["A319", "A320", "A20N", "A321", "A21N"],
    "F9": ["A320", "A20N", "A21N"], "SY": ["B738"], "MX": ["A320", "A21N"],
    "Y4": ["A320", "A21N"], "VB": ["A320", "A21N"], "AK": ["A320", "A20N"], "D7": ["A333", "A359"],
    "FD": ["A320", "A20N"], "QZ": ["A320"], "TR": ["A320", "A21N", "B788"], "5J": ["A320", "A21N", "A333"],
    "VJ": ["A320", "A21N"], "6E": ["A320", "A20N", "A21N"], "SL": ["B738"], "JT": ["B738", "A320"],
    "JQ": ["A320", "A21N", "B788"], "TW": ["B738", "A320"], "7C": ["B738"], "LJ": ["B738"],
    "9C": ["A320", "A21N"], "BX": ["A320", "A321"], "3K": ["A320"], "MM": ["A320"],
    # ---- full-service: short-haul narrowbody + long-haul widebody ----
    "BA": ["A319", "A320", "A20N", "A321", "A21N", "B788", "B789", "A359", "B77W"],
    "LH": ["A319", "A320", "A20N", "A21N", "A333", "A339", "A359", "B789"],
    "AF": ["A223", "A319", "A320", "A21N", "A359", "B789", "B77W"],
    "KL": ["B738", "B38M", "A21N", "B789", "B77W", "A333"],
    "IB": ["A319", "A320", "A21N", "A333", "A359"], "I2": ["A320", "A321"],
    "AZ": ["A319", "A320", "A21N", "A339", "A333"],
    "LX": ["A221", "A223", "A320", "A21N", "A333", "A359"],
    "OS": ["A320", "A321", "B763", "B789"], "SN": ["A319", "A320", "A333"],
    "TP": ["A320", "A21N", "A339", "A333"], "SK": ["A320", "A21N", "A359", "A333"],
    "AY": ["A320", "A321", "A359", "A333"], "EI": ["A320", "A321", "A21N", "A333"],
    "VS": ["A339", "A359", "B789"], "UX": ["B38M", "B789"], "A3": ["A320", "A21N"],
    "LO": ["B738", "E195", "B789"], "TK": ["A321", "A21N", "A333", "A359", "B789", "B77W"],
    "SU": ["A320", "A321", "B738", "A333"], "PS": ["B738", "E195"], "JU": ["A319", "A320", "A21N"],
    "OU": ["A319", "A320", "DH8D"], "RO": ["B738", "A21N"],
    # airBaltic flies the A220-300 and nothing else; the old "A220 if False" dodge
    # dated from before the type had an economics entry.
    "BT": ["A223"],
    # ---- North America ----
    "AA": ["A319", "A320", "A321", "A21N", "B738", "B38M", "B788", "B789", "B77W"],
    "DL": ["A221", "A223", "A319", "A320", "A321", "B738", "A333", "A339", "A359", "B763"],
    "UA": ["A319", "A320", "B738", "B38M", "B789", "B788", "B77W"],
    "WN": ["B738", "B38M"], "B6": ["A223", "A320", "A321", "A21N"],
    "AS": ["B738", "B38M", "A320", "A321"],
    "AC": ["A223", "A319", "A320", "A321", "B38M", "B789", "B77W", "A333"],
    "WS": ["B738", "B38M", "B789"], "HA": ["A21N", "A333", "B789"],
    "AM": ["B738", "B38M", "B789"], "CM": ["B738", "B38M"],
    # ---- Middle East / Africa ----
    "EK": ["B77W", "A359"], "QR": ["A320", "A21N", "A333", "A359", "B789", "B77W"],
    "EY": ["A321", "B788", "B789", "A359", "A339"], "SV": ["A320", "A321", "A333", "B789", "B77W"],
    "MS": ["B738", "B38M", "A333", "B789"], "ET": ["B738", "B38M", "A359", "B788", "B789", "B77W"],
    "RJ": ["A320", "A321", "B788", "B789"], "GF": ["A320", "A21N", "B789"], "WY": ["B738", "A333", "B789"],
    "FZ": ["B738", "B38M"], "XY": ["A320", "A21N"], "AT": ["B738", "B38M", "B788"],
    "KQ": ["B738", "B788"], "SA": ["A320", "A333", "A339"],
    # ---- Asia / Pacific ----
    "SQ": ["A359", "B789", "B77W"], "CX": ["A333", "A359", "B77W"], "JL": ["B738", "A359", "B789", "B77W"],
    "NH": ["B738", "A320", "B788", "B789", "B77W"],
    "KE": ["A223", "B738", "A321", "B789", "A359", "B77W"],
    "OZ": ["A320", "A321", "A359", "B77W"], "TG": ["A320", "A333", "A359", "B789", "B77W"],
    "MH": ["B738", "A333", "A359"], "GA": ["B738", "A333", "B77W"], "PR": ["A320", "A321", "A333", "A359"],
    "BR": ["A321", "B789", "B77W", "A359"], "CI": ["A321", "A359", "B789"],
    "CA": ["A320", "A321", "A359", "B789", "B77W", "C919", "C909"],
    "MU": ["A320", "A321", "A333", "B789", "C919", "C909"],
    "CZ": ["A320", "A321", "A333", "A359", "B789", "C919", "C909"], "HU": ["B738", "A333", "B789"],
    "EU": ["A319", "A320", "C909"],   # Chengdu Airlines - the ARJ21/C909 launch operator
    "AI": ["A320", "A321", "B788", "B789", "B77W"], "UK": ["A320", "A21N", "B788"],
    "VN": ["A321", "A359", "B789"], "QF": ["B738", "A320", "A333", "A359", "B789"],
    "VA": ["B738", "A320"], "NZ": ["A320", "A321", "B789"], "FJ": ["B738", "A339"],
    # ---- Latin America ----
    "LA": ["A320", "A321", "B788", "B789"], "JJ": ["A320", "A321", "B789"],
    "AV": ["A320", "A321", "B788", "B789"], "AR": ["B738", "A330" if False else "A333"],
    "AD": ["A320", "A321", "A339"], "G3": ["B738", "B38M"], "H2": ["A320", "A21N"],
}
# clean out any placeholder non-keys
def _clean(codes):
    return [c for c in codes if isinstance(c, str) and len(c) >= 3]
FLEETS = {k: _clean(v) for k, v in FLEETS.items()}


_OBS_WARNED = set()


def fleet_observed(airline_iata, distance_km, period="2025-%"):
    """What the carrier is measured to fly at this sector length, from OAG, or [] if nothing.

    The table below is hand-maintained and was wrong on every carrier checked on 10 August 2026:
    China Airlines carried a 787-9 it does not fly on 10,000 km sectors and no 777-300ER, EVA carried
    an A350-900 it does not fly, and Starlux was missing entirely so it fell back to every
    range-feasible type. A schedule store answers this question directly, and a measured answer that
    moves with the fleet beats a table someone has to remember to update.
    """
    if not airline_iata or not distance_km:
        return []
    try:
        import capacity_frame as CF
        keys, unmapped, sectors = CF.types_for(airline_iata, distance_km)
    except Exception:
        return []                      # no store, no measurement: the table below still stands
    if unmapped and airline_iata not in _OBS_WARNED:
        # Named, not swallowed. An observed type the economics module cannot cost is a gap in the
        # economics module, and it silently narrows the option set the carrier is offered.
        _OBS_WARNED.add(airline_iata)
        print("fleet_observed: %s flies these at this sector length and the economics module has no "
              "entry, so they are not offered: %s" % (airline_iata, ", ".join(unmapped)))
    return keys if sectors else []


def fleet_for(airline_iata, available_codes, distance_km=None, margin=1.03, observed=True):
    """The airline's fleet, intersected with the codes the economics module knows and (if given) the
    sector range. Returns (codes, known): known=False means fall back to all range-feasible types.

    OAG is asked first when the sector length is known; the table is the fallback, not the source.
    observed=False forces the old behaviour, for reproducing a run made before 10 August 2026."""
    from aircraft_economics import AIRCRAFT
    av = set(available_codes or AIRCRAFT.keys())
    fleet = None
    if observed and distance_km:
        fleet = fleet_observed(airline_iata, distance_km) or None
    if fleet is None:
        fleet = FLEETS.get((airline_iata or "").upper())
    known = fleet is not None
    pool = [c for c in (fleet or av) if c in av and c in AIRCRAFT]
    if distance_km:
        pool = [c for c in pool if AIRCRAFT[c]["range_km"] >= distance_km * margin]
    return pool, known
