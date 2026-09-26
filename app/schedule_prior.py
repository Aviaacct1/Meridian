"""The schedule prior: what airlines actually launch on a pair like this one. W1, 26 September 2026.

WHAT IT IS FOR (John's ruling of 26 September 2026, option 2b). The calibrated model is accurate
GIVEN a schedule; it cannot say what schedule a market supports, and because capacity is its largest
predictor an unbounded Optimise reaches for the biggest aeroplane at the highest frequency (Bologna to
New York on a 777-300ER). So Optimise first asks what airlines launched on comparable pairs, bounds
its sweep to that gauge and frequency, ranks inside the bound by contribution, and forecasts at the
winner. The model and the 88 / 78 record it carries are untouched: the prior only chooses the
schedule the model is asked about.

THE TABLE is workstation data, not code (tool standard rule 3): schedule_prior.csv, fitted by W10
(bt2/bt2_fit_schedule_prior.py, then bt2/bt2_retime_freq.py for v2) on the same 6,524 launches as the
model, and found through the model file's own resolver (bt2_forecast._model_path roots, subfolder
bt2_relaxed then bt2). AVIA_SCHEDULE_PRIOR names a file directly. ABSENT FILE: Optimise runs as it
did before and the payload says the prior is not loaded; it never fails on it.

THE CLASS KEY, exactly as the table was fitted (routes/W10-STATUS.md v21):
  market_band  route_context.market(a, b, year)[0], the RAW two-way Sabre pair. NOT market_build step
               1, which is the catchment market grossed for coverage: on Bologna-New York 203,142
               against a pair of 37,814, and the wrong one puts the pair in the wrong class.
  haul_band    great-circle km.   carrier_type  LCC (LCC and ULCC) or FSC (the rest).
  scope        D same country, I otherwise.   region_pair  bt2_record_mix.region_pair (level 0 only).
Lookup: levels 0 to 4, the first whose row exists with n of 20 or more. Level 4 exists for every haul
band, so the lookup never fails while the file is loaded.

CARRIER LINE: the carrier's row for THIS haul band and scope only, never its all-launches row
(United's all-launches row is its regional feed, median 76 seats). Written by W10 only at n of 5 or
more; absent means "fewer than 5 comparable launches". A flag, never a veto.

Units: gauge is seats per departure; frequency is departures per week per direction (the launching
carrier's first full month, v2).

Avia Solutions Limited. All rights reserved.
"""
from __future__ import annotations

import csv
import math
import os

MIN_CLASS = 20
MIN_CARRIER = 5
FILE_NAME = "schedule_prior.csv"
ENV = "AVIA_SCHEDULE_PRIOR"

# One definition of each region, copied from bt2/bt2_record_mix.py (the app does not import bt2/).
# If W10 changes a set there, this must change with it (the yearly refit checklist carries the line).
EUROPE = set("AT BE BG CH CY CZ DE DK EE ES FI FR GB GR HR HU IE IS IT LT LU LV MT NL NO PL PT RO RS SE SI SK "
             "AL BA MD ME MK UA XK GI JE GG IM FO".split())
NAM = {"US", "CA"}
ASIA = set("CN HK TW JP KR IN PK BD LK NP TH VN MY SG ID PH KH LA MM MO BN MN KZ UZ".split())
MIDEAST = set("AE QA SA OM KW BH JO IL IR IQ LB EG TR".split())

LEVELS = {0: ("scope", "haul_band", "carrier_type", "market_band", "region_pair"),
          1: ("scope", "haul_band", "carrier_type", "market_band"),
          2: ("haul_band", "carrier_type", "market_band"),
          3: ("haul_band", "market_band"),
          4: ("haul_band",)}

_TABLE = None          # (path, class index, carrier index) once loaded
_ERR = None
_AP = None            # airportsdata IATA table, loaded on first use


def market_band(bm):
    return "S0" if bm < 8000 else "S1" if bm < 25000 else "S2" if bm < 80000 else "S3"


def haul_band(km):
    return "H0" if km < 800 else "H1" if km < 2000 else "H2" if km < 4500 else "H3"


def region_pair(ctry_a, ctry_b):
    reg = lambda c: ("EU" if c in EUROPE else "NA" if c in NAM else "AS" if c in ASIA
                     else "ME" if c in MIDEAST else "OT")
    if ctry_a and ctry_a == ctry_b:
        return "domestic " + ("US" if ctry_a == "US" else "EU" if ctry_a in EUROPE else "other")
    s = {reg(ctry_a), reg(ctry_b)}
    return "-".join(sorted(s)) if len(s) == 2 else "intra-" + next(iter(s))


def path():
    p = os.environ.get(ENV)
    if p and os.path.isfile(p):
        return p
    roots = [os.environ.get("AVIA_LOCAL_CACHE"), os.path.join("E:" + os.sep, "Avia"),
             os.path.join("C:" + os.sep, "Avia")]
    for r in roots:
        if not r:
            continue
        for sub in ("bt2_relaxed", "bt2"):
            c = os.path.join(r, sub, FILE_NAME)
            if os.path.isfile(c):
                return c
    return None


def load():
    """(path, class_index, carrier_index) or None with the reason in reason()."""
    global _TABLE, _ERR
    if _TABLE is not None or _ERR is not None:
        return _TABLE
    p = path()
    if not p:
        _ERR = ("no %s found (set %s, or AVIA_LOCAL_CACHE to the data root); Optimise runs unbounded"
                % (FILE_NAME, ENV))
        return None
    try:
        with open(p, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        cls, car = {}, {}
        for t in rows:
            t.setdefault("region_pair", "")          # v1 has no column: read as blank, level 0 never matches
            t["region_pair"] = t.get("region_pair") or ""
            if t["table"] == "class":
                lv = int(t["level"])
                if lv in LEVELS:
                    cls[(lv,) + tuple(t[f] for f in LEVELS[lv])] = t
            elif t["table"] == "carrier":
                car[(t["carrier"], t["haul_band"], t["scope"])] = t
        # Every haul band must have a level 4 row or the lookup can fail; refuse the file by name.
        missing = [h for h in ("H0", "H1", "H2", "H3") if (4, h) not in cls]
        if missing:
            _ERR = "%s has no level 4 row for %s; not loaded" % (p, ", ".join(missing))
            return None
        _TABLE = (p, cls, car)
    except Exception as e:                                   # noqa: BLE001
        _ERR = "%s could not be read (%s); not loaded" % (p, e)
        return None
    return _TABLE


def reason():
    return _ERR


def _num(t, k):
    try:
        return float(t[k])
    except (KeyError, TypeError, ValueError):
        return None


def _band(t):
    return {"n": int(float(t["n"])),
            "gauge_p25": _num(t, "gauge_p25"), "gauge_med": _num(t, "gauge_med"), "gauge_p75": _num(t, "gauge_p75"),
            "freq_p25": _num(t, "freq_p25"), "freq_med": _num(t, "freq_med"), "freq_p75": _num(t, "freq_p75")}


def key(base_mkt, gcd_km, carrier_type, ctry_a, ctry_b):
    ct = "LCC" if (carrier_type or "").upper() in ("LCC", "ULCC") else "FSC"
    k = {"haul_band": haul_band(gcd_km), "carrier_type": ct,
         "market_band": market_band(base_mkt) if base_mkt is not None else None,
         "scope": None, "region_pair": None}
    if ctry_a and ctry_b:
        k["scope"] = "D" if ctry_a == ctry_b else "I"
        k["region_pair"] = region_pair(ctry_a, ctry_b)
    return k


def lookup(k):
    """The class row for key k: {level, key, n, gauge_*, freq_*} or None when the table is absent.
    A field that could not be computed (None) makes every level that needs it skip, so an unknown
    country starts at level 2 and an unmeasured pair starts at level 4, and the payload says so."""
    tab = load()
    if not tab:
        return None
    _, cls, _ = tab
    for lv in sorted(LEVELS):
        fields = LEVELS[lv]
        if any(k.get(f) is None for f in fields):
            continue
        t = cls.get((lv,) + tuple(k[f] for f in fields))
        if t and int(float(t["n"])) >= MIN_CLASS:
            out = _band(t)
            out.update(level=lv, key={f: k[f] for f in fields})
            return out
    return None


def carrier_line(carrier, k):
    """The carrier's row for this haul band and scope, or None (fewer than 5 comparable launches).
    Never the all-launches row."""
    tab = load()
    if not tab or not carrier or not k.get("scope"):
        return None
    t = tab[2].get(((carrier or "").upper(), k["haul_band"], k["scope"]))
    if t and int(float(t["n"])) >= MIN_CARRIER:
        out = _band(t)
        out.update(carrier=carrier.upper(), key={"haul_band": k["haul_band"], "scope": k["scope"]})
        return out
    return None


def permitted_freqs(haul):
    """The headline rule (John, 24 Sep 2026): a new long-haul service launches at 3x, 4x, 5x or 7x
    and never above daily. Shorter sectors keep the 3x to 7x sweep that ran before."""
    return [3, 4, 5, 7] if haul == "H3" else [3, 4, 5, 6, 7]


def freqs_in_band(band, haul):
    """Whole weekly frequencies inside the band's p25-p75, intersected with the headline rule.
    Returns (freqs, how) where how is 'band' or 'nearest to band' (the band held no permitted
    frequency, so the permitted one nearest the band's median is taken and the payload says so)."""
    perm = permitted_freqs(haul)
    lo, hi, med = band.get("freq_p25"), band.get("freq_p75"), band.get("freq_med")
    if lo is None or hi is None:
        return perm, "no frequency band"
    inside = [f for f in perm if lo - 1e-9 <= f <= hi + 1e-9]
    if inside:
        return inside, "band"
    target = med if med is not None else (lo + hi) / 2.0
    return [min(perm, key=lambda f: (abs(f - target), f))], "nearest to band"


def country(iata):
    """ISO country of an airport from airportsdata (the record's own source), or None."""
    global _AP
    if _AP is None:
        try:
            import airportsdata
            _AP = airportsdata.load("IATA")
        except Exception:                                    # noqa: BLE001
            _AP = {}
    rec = _AP.get((iata or "").upper())
    return (rec or {}).get("country") or None
