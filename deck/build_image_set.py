#!/usr/bin/env python3
"""Build the fetch-set input for avia_images.py, one row per image slot.

Why this exists
---------------
An airport sales deck wants a photograph of that airport. avia_images.py can
fetch one with its licence record attached, but it needs a subject string per
slot, and a subject built from an IATA code alone ("BLQ airport terminal")
finds nothing. So the airport name and its city come from airportsdata, and the
set of airports to cover comes from the engine's own airport table, ranked by
size, because that is the population a visitor at a route development show
actually names.

The list is an input, not data: it is regenerated from the two sources rather
than edited by hand, and the photographs it produces live in the store on the
workstation, never in this repo.

Usage
-----
    python3 build_image_set.py --top 400 --airport-only \\
        --out routes2026_probe.json
    python3 build_image_set.py --top 400 --out routes2026_set.json

Then:

    python3 avia_images.py fetch-set routes2026_probe.json --dry-run

Avia Solutions Limited. All rights reserved.
"""

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ATTRS = os.path.join(HERE, "..", "app", "airport_attributes.json")

# The six of the Routes worked routes and the five meeting airports, kept in
# whatever the size ranking does, because Genoa is small and is exactly the
# case worth measuring.
ALWAYS = ["SJC", "TPE", "BLQ", "GOA", "JFK", "EWR",
          "BHX", "DUB", "VIE", "DFW", "MXP", "LIN"]

# Three of these are the airport itself and two are its city. A deck carrying one
# photograph of an airport looks thin, so the acceptance is three usable airport
# images per airport, which is what the airport slots below are measured against.
AIRPORT_SLOTS = ("terminal", "airside", "aerial")

SLOTS = {
    "terminal": "%(airport)s terminal",
    "airside":  "%(airport)s aircraft apron",
    "aerial":   "%(airport)s aerial view",
    "skyline":  "%(city)s skyline aerial",
    "city":     "%(city)s city centre",
}


def clean_name(name):
    """airportsdata files some airports as 'Bologna / Borgo Panigale Airport'.

    The slash is a filing convention, not how anyone writes the name, and it
    splits the search tokens badly. Everything else is left alone: the official
    name is what Commons files the photographs under.
    """
    return " ".join(name.replace("/", " ").split())


def build(top, slots, limit, attrs_path=ATTRS):
    import airportsdata
    ref = airportsdata.load("IATA")
    with open(attrs_path, encoding="utf-8") as f:
        table = json.load(f)["airports"]

    ranked = sorted(table.items(), key=lambda kv: -(kv[1].get("size_m") or 0))
    codes = [c for c, _ in ranked[:top]]
    codes += [c for c in ALWAYS if c not in codes]

    rows, skipped = [], []
    for code in codes:
        a = ref.get(code)
        if not a or not a.get("name"):
            skipped.append(code)
            continue
        fields = {"airport": clean_name(a["name"]),
                  "city": a.get("city") or clean_name(a["name"])}
        for slot in slots:
            rows.append(["%s_%s" % (code.lower(), slot),
                         SLOTS[slot] % fields, limit, a.get("country") or ""])
    return rows, skipped


def main():
    ap = argparse.ArgumentParser(description=__doc__,
          formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", type=int, default=400,
                    help="how many airports, by size, from the engine table")
    ap.add_argument("--slots", default="terminal,airside,aerial,skyline,city",
                    help="comma-separated: %s" % ", ".join(sorted(SLOTS)))
    ap.add_argument("--airport-only", action="store_true",
                    help="the three airport slots only, which is what the "
                         "three-images-per-airport acceptance is measured on")
    ap.add_argument("--limit", type=int, default=6,
                    help="candidates to take per slot")
    ap.add_argument("--attrs", default=ATTRS)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    slots = (list(AIRPORT_SLOTS) if a.airport_only
             else [s.strip() for s in a.slots.split(",") if s.strip()])
    bad = [s for s in slots if s not in SLOTS]
    if bad:
        raise SystemExit("unknown slot(s): %s" % ", ".join(bad))

    rows, skipped = build(a.top, slots, a.limit, a.attrs)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=1)
    print("wrote %s: %d rows, %d airports, %d slot(s) each"
          % (a.out, len(rows), len(rows) // max(1, len(slots)), len(slots)))
    if skipped:
        print("   NOT IN THE AIRPORT REFERENCE, so left out and not guessed "
              "at (%d): %s" % (len(skipped), ", ".join(sorted(skipped))))


if __name__ == "__main__":
    main()
