#!/usr/bin/env python3
r"""
Avia Solutions - P2P/connecting split by airport connectivity (total-preserving re-split).
==================================================================================================
The engine over-attributes onboard demand to the P2P leg on connecting-heavy routes (a route into a big hub
like DOH/ATL/IST is mostly transfer traffic, not local). This gives the TRUE P2P share of a route from each
endpoint's connectivity, so the forecast's P2P/connecting split, the PDEW connection tables, and the economics
all read correctly, WITHOUT changing the forecast TOTAL (so the +/-20% accuracy on the total is untouched).

    p2p_share(o,d) = local_o x local_d      (a true point-to-point pax is local at BOTH ends)

local[airport] = the airport's own "localness" (1 = pure origin-destination spoke, low = big connecting hub),
fitted by bilinear decomposition of the historical route splits (calib_split_share.py --out) so it isolates the
airport's own hub character from that of its partners. Unknown airports fall back to the global localness.

Usage in the engine (total-preserving): total = captured + feed (unchanged); then
    p2p_carried  = carried_total x p2p_share(o,d)
    conn_carried = carried_total x (1 - p2p_share(o,d))
and the PDEW connecting detail is scaled to conn_carried (its per-city SHAPE from the feed model is kept).
"""
import os, json

_HERE = os.path.dirname(os.path.abspath(__file__))
_TABLE_PATH = os.path.join(_HERE, "hub_localness.json")

_LOCAL = None
_GLOBAL = 0.97          # fallback if the table is absent (near-1 = assume mostly P2P until we know better)


def _load():
    global _LOCAL, _GLOBAL
    if _LOCAL is not None:
        return
    _LOCAL = {}
    try:
        with open(_TABLE_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
        _LOCAL = data.get("local", {}) or {}
        _GLOBAL = float(data.get("global_localness", _GLOBAL))
    except Exception:
        _LOCAL = {}      # no table yet -> p2p_share falls back to global (near 1.0 = no re-split effect)


def localness(airport):
    """The airport's own P2P-localness (1 = spoke, low = big connecting hub); global fallback if unknown."""
    _load()
    return float(_LOCAL.get((airport or "").upper(), _GLOBAL))


def p2p_share(origin, dest):
    """True point-to-point share of a route's onboard demand, from both endpoints' connectivity. In [0.02, 1]."""
    s = localness(origin) * localness(dest)
    return max(0.02, min(1.0, s))


def resplit(carried_total, origin, dest):
    """Total-preserving split of a carried onboard total into (p2p, connecting). Sum == carried_total."""
    sh = p2p_share(origin, dest)
    p2p = carried_total * sh
    return p2p, carried_total - p2p, sh


def available():
    _load()
    return bool(_LOCAL)


if __name__ == "__main__":
    import sys
    _load()
    print(f"loaded {len(_LOCAL)} airport localness scores; global {_GLOBAL:.3f}; table {_TABLE_PATH}")
    for pair in (("DOH", "ATL"), ("LHR", "SJC"), ("SJC", "SFO"), ("LGW", "AGP")):
        if len(sys.argv) == 1:
            print(f"  {pair[0]}-{pair[1]}: p2p_share {p2p_share(*pair):.2f}  "
                  f"(local {localness(pair[0]):.2f} x {localness(pair[1]):.2f})")
