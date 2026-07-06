#!/usr/bin/env python3
"""
Avia Solutions - annual LOPA refresh (Wikipedia airline fleet -> lopa_store.json).
==============================================================================
Refreshes the carrier seat-config store once a year from airline fleet pages on Wikipedia
(free, CC-licensed, structured). SeatGuru shut down Oct 2025, so this replaces the manual
per-pitch lookup. Anything a carrier page doesn't yield still falls back to lopa.AVERAGES.

  fetch_fleet_html(page)      -> the rendered fleet-page HTML (runs at refresh time on a machine
                                 with web access).
  parse_fleet_table(html, ia) -> {AIRCRAFT_code: {first,business,premium_coach,coach,total}}
                                 via pandas.read_html, which handles the multi-level
                                 "Passengers > F/J/W/Y" headers Wikipedia uses.
  update_store(entries, path) -> merge into lopa_store.json with the date + source.

Run annually:  py -3.12 lopa_refresh.py --airline BA   (or --all)
Review the diff before committing - Wikipedia formatting varies by carrier, so treat the
output as a strong draft. Validated: parses the BA 787 family to 35J/25W/154Y=214 etc.
Needs: pandas + lxml (pip install pandas lxml).
"""
from __future__ import annotations
import json, os, re, io, argparse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))

SOURCES = {
    "BA": "British_Airways_fleet", "LH": "Lufthansa_fleet", "KE": "Korean_Air_fleet",
    "CI": "China_Airlines_fleet", "BR": "EVA_Air_fleet", "CA": "Air_China_fleet",
    "NH": "All_Nippon_Airways_fleet", "AF": "Air_France_fleet", "KL": "KLM_fleet",
    "EK": "Emirates_fleet", "SQ": "Singapore_Airlines_fleet",
}

_NAME_CODE = [
    (r"787-?8|787-800", "B788"), (r"787-?9|787-900", "B789"), (r"787-?10", "B78X"),
    (r"A350-?900|350-900", "A359"), (r"A350-?1000|350-1000", "A35K"),
    (r"A330-?900|330-900|A330neo", "A339"), (r"A330-?300|330-300", "A333"),
    (r"777-?300|77W|777-300ER", "B77W"), (r"767-?300", "B763"),
    (r"A321(neo)?\s*XLR|A321XLR", "A21X"), (r"A321neo|A21N|321neo", "A21N"),
    (r"757-?200", "B752"),
]


def aircraft_code(name):
    n = str(name).replace("‑", "-")
    for pat, code in _NAME_CODE:
        if re.search(pat, n, re.I):
            return code
    return None


def fetch_fleet_html(page, lang="en"):
    """Rendered fleet-page HTML via the Wikipedia API (runs at refresh time, needs web access)."""
    import urllib.request, urllib.parse
    url = (f"https://{lang}.wikipedia.org/w/api.php?action=parse&page="
           f"{urllib.parse.quote(page)}&prop=text&format=json&formatversion=2")
    req = urllib.request.Request(url, headers={"User-Agent": "AviaSolutions-LOPA-refresh/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["parse"]["text"]


def _to_int(v):
    m = re.search(r"\d+", str(v).replace(",", ""))
    return int(m.group()) if m else 0


def _classify(header):
    h = str(header).strip().lower()
    if h == "f" or "first" in h:
        return "first"
    if h in ("j", "c") or "business" in h or "club" in h:
        return "business"
    if "premium" in h or "plus" in h or h in ("w", "pey", "w+"):
        return "premium_coach"
    if h == "y" or "economy" in h or ("traveller" in h and "plus" not in h) or h == "eco":
        return "coach"
    return None


def parse_fleet_table(html, airline_iata):
    """Extract LOPA rows from the fleet page HTML -> {AIRCRAFT_code: config}."""
    import pandas as pd
    tables = pd.read_html(io.StringIO(html))
    out = {}
    for t in tables:
        cols = list(t.columns)
        flat = [" ".join(str(x) for x in (c if isinstance(c, tuple) else (c,))) for c in cols]
        if not any("aircraft" in f.lower() for f in flat):
            continue
        cabin_cols = {}
        for c in cols:
            leaf = c[-1] if isinstance(c, tuple) else c
            cab = _classify(leaf)
            if cab and cab not in cabin_cols:
                cabin_cols[cab] = c
        if "coach" not in cabin_cols and "business" not in cabin_cols:
            continue
        ac_col = cols[0]
        for _, row in t.iterrows():
            code = aircraft_code(str(row[ac_col]))
            if not code:
                continue
            seats = {k: _to_int(row[col]) for k, col in cabin_cols.items()}
            entry = {"first": seats.get("first", 0), "business": seats.get("business", 0),
                     "premium_coach": seats.get("premium_coach", 0), "coach": seats.get("coach", 0)}
            entry["total"] = sum(entry.values())
            if entry["total"] == 0:
                continue
            entry["source"] = f"Wikipedia {SOURCES.get(airline_iata, '')}"
            out.setdefault(code, entry)
    return out


def update_store(airline_iata, entries, store_path=None):
    store_path = store_path or os.path.join(HERE, "lopa_store.json")
    store = json.load(open(store_path)) if os.path.exists(store_path) else {"_meta": {}, "airlines": {}}
    store.setdefault("airlines", {}).setdefault(airline_iata.upper(), {}).update(entries)
    store.setdefault("_meta", {})["updated"] = datetime.date.today().isoformat()
    json.dump(store, open(store_path, "w"), indent=2)
    return store_path


def refresh(airline_iata, store_path=None):
    page = SOURCES.get(airline_iata.upper())
    if not page:
        raise ValueError(f"no Wikipedia source for {airline_iata}; add it to SOURCES")
    entries = parse_fleet_table(fetch_fleet_html(page), airline_iata.upper())
    update_store(airline_iata.upper(), entries, store_path)
    return entries


def main():
    ap = argparse.ArgumentParser(description="Refresh the LOPA store from Wikipedia fleet pages.")
    ap.add_argument("--airline", default=None, help="IATA code (e.g. BA)")
    ap.add_argument("--all", action="store_true", help="refresh every airline in SOURCES")
    ap.add_argument("--store", default=None)
    a = ap.parse_args()
    targets = list(SOURCES) if a.all else ([a.airline.upper()] if a.airline else [])
    if not targets:
        ap.error("pass --airline <IATA> or --all")
    for ia in targets:
        try:
            e = refresh(ia, a.store)
            print(f"{ia}: {len(e)} configs -> " + ", ".join(f"{k} {v['total']}" for k, v in e.items()))
        except Exception as ex:
            print(f"{ia}: FAILED ({ex}); type-average fallback still applies")


if __name__ == "__main__":
    main()
