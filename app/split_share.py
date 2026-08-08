#!/usr/bin/env python3
r"""
Avia Solutions - P2P/connecting split by airport connectivity (total-preserving re-split).
==================================================================================================
An airport is a hub to the degree its Sabre passengers TRANSFER through it rather than start/end there. Two
tables, best first:
  region_localness.json  - REGION-WEIGHTED: transfer share at each hub BY PARTNER REGION (build_hub_connectivity_
                           region.py). Directional, so a US->TPE route uses TPE's transfer-share-for-North-America
                           (high) not TPE's diluted average. p2p_share(o,d) = local_o[reg_d] x local_d[reg_o].
  hub_localness.json     - airport-average fallback (build_hub_connectivity.py). p2p_share = local_o x local_d.
Unknown airports/regions fall back to the airport average, then the global localness. A true point-to-point pax
is local at BOTH ends, hence the product.

Used in the engine total-preserving: total = captured + feed (UNCHANGED); p2p = total x p2p_share, connecting =
total x (1 - p2p_share); and the re-split only ever RAISES connecting (never cuts it), so an under-scored hub
can't regress a route below the engine's own estimate.
"""
import os, json

_HERE = os.path.dirname(os.path.abspath(__file__))
_REGION_PATH = os.path.join(_HERE, "region_localness.json")
_AVG_PATH = os.path.join(_HERE, "hub_localness.json")

_REGION = None          # {hub: {region: localness}}
_LOCAL = None           # {hub: localness}  (airport average)
_GLOBAL = 0.97
_APT = None             # airportsdata for the region lookup

REGION = {
    "GB": "EU", "IE": "EU", "FR": "EU", "DE": "EU", "ES": "EU", "IT": "EU", "NL": "EU", "BE": "EU",
    "CH": "EU", "AT": "EU", "PT": "EU", "SE": "EU", "NO": "EU", "DK": "EU", "FI": "EU", "PL": "EU",
    "CZ": "EU", "GR": "EU", "RO": "EU", "HU": "EU", "HR": "EU", "RS": "EU", "BG": "EU", "SK": "EU",
    "UA": "EU", "IS": "EU", "LU": "EU", "EE": "EU", "LV": "EU", "LT": "EU", "CY": "EU", "MT": "EU",
    "US": "NA", "CA": "NA",
    "MX": "LATAM", "BR": "LATAM", "AR": "LATAM", "CL": "LATAM", "CO": "LATAM", "PE": "LATAM",
    "EC": "LATAM", "BO": "LATAM", "PY": "LATAM", "UY": "LATAM", "VE": "LATAM", "PA": "LATAM",
    "CR": "LATAM", "GT": "LATAM", "DO": "LATAM", "CU": "LATAM", "JM": "LATAM", "BZ": "LATAM",
    "HN": "LATAM", "NI": "LATAM", "SV": "LATAM", "TT": "LATAM",
    "AE": "MEA", "SA": "MEA", "QA": "MEA", "IL": "MEA", "TR": "MEA", "JO": "MEA", "KW": "MEA",
    "OM": "MEA", "BH": "MEA", "LB": "MEA", "EG": "MEA",
    "ZA": "AFR", "KE": "AFR", "NG": "AFR", "ET": "AFR", "MA": "AFR", "TN": "AFR", "GH": "AFR",
    "TZ": "AFR", "MU": "AFR",
    "JP": "APAC", "KR": "APAC", "AU": "APAC", "NZ": "APAC", "SG": "APAC", "HK": "APAC", "TW": "APAC",
    "TH": "APAC", "MY": "APAC",
    "CN": "CN", "IN": "IN", "ID": "ID", "VN": "VN",
}


LOAD_FAILURES = []      # read by the callers and printed by the runner


def _load():
    """Load the localness tables. A table that does not load SAYS so.

    7 August: both tables were missing from the working copy for weeks and this
    function absorbed it, so the re-split was simply off and every forecast taken
    on that copy carried an uncorrected point to point and connecting split with
    nothing on the screen or in the log to say why. Third instance of that shape
    in this codebase, after the airport_capture shim and the empty backtest
    column, so the failure is now recorded in LOAD_FAILURES and printed once.
    """
    global _REGION, _LOCAL, _GLOBAL, _APT
    if _REGION is not None:
        return
    _REGION, _LOCAL = {}, {}
    for path in (_REGION_PATH, _AVG_PATH):     # region table wins; hub_localness fills any airport it lacks
        try:
            with open(path, encoding="utf-8") as fh:
                d = json.load(fh)
            _GLOBAL = float(d.get("global_localness", _GLOBAL))
            for k, v in (d.get("region") or {}).items():
                _REGION.setdefault(k, v)
            for k, v in (d.get("local") or {}).items():
                _LOCAL.setdefault(k, float(v))
        except Exception as e:
            msg = ("split_share: %s did not load (%s: %s). The hub localness "
                   "re-split is OFF and the point to point and connecting split "
                   "is the engine's own, uncorrected."
                   % (os.path.basename(path), type(e).__name__, e))
            LOAD_FAILURES.append(msg)
            print("WARNING: %s" % msg)
    try:
        import airportsdata
        _APT = airportsdata.load("IATA")
    except Exception:
        _APT = None


def _region_of(airport):
    if _APT is None:
        return "OTH"
    r = _APT.get((airport or "").upper())
    return REGION.get((r.get("country") if r else "") or "", "OTH")


def localness(airport, partner_region=None):
    """The airport's P2P-localness (1 = spoke, low = big connecting hub). If a partner_region is given and a
    region-weighted cell exists, use it (directional); else the airport average; else global."""
    _load()
    a = (airport or "").upper()
    if partner_region is not None:
        cell = _REGION.get(a)
        if cell is not None and partner_region in cell:
            return float(cell[partner_region])
    return float(_LOCAL.get(a, _GLOBAL))


def p2p_share(origin, dest):
    """True point-to-point share of a route's onboard demand, from both endpoints' (directional) connectivity."""
    _load()
    ro, rd = _region_of(origin), _region_of(dest)
    lo = localness(origin, rd)          # origin scored for traffic to the destination's region
    ld = localness(dest, ro)            # destination scored for traffic from the origin's region
    return max(0.02, min(1.0, lo * ld))


def resplit(carried_total, origin, dest):
    """Total-preserving split of a carried onboard total into (p2p, connecting). Sum == carried_total."""
    sh = p2p_share(origin, dest)
    p2p = carried_total * sh
    return p2p, carried_total - p2p, sh


def available():
    _load()
    return bool(_REGION or _LOCAL)


if __name__ == "__main__":
    _load()
    src = "region-weighted" if _REGION else ("airport-average" if _LOCAL else "NONE")
    print(f"loaded {len(_REGION)} region hubs + {len(_LOCAL)} airport scores; global {_GLOBAL:.3f}; source {src}")
    for o, d in (("SJC", "TPE"), ("DOH", "ATL"), ("SFO", "LHR"), ("LGW", "AGP"), ("SJC", "SFO")):
        print(f"  {o}-{d}: p2p_share {p2p_share(o, d):.2f}  (connecting {100*(1-p2p_share(o,d)):.0f}%)")
