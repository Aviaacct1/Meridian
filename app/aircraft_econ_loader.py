#!/usr/bin/env python3
"""
Loader for the aircraft economics reference table (29 August 2026).

THE ONLY READER of reference_tables/aircraft_econ.csv (path from config, never
hardcoded). 68 types, one row per `key`, built from Stefan Parry's sourced
fill-in pack plus the four same-day closures. The table's rules are ENFORCED
HERE STRUCTURALLY rather than trusted, so no consumer can break them:

1. STATUS carries through. held / held-amber-proxy / new-sourced / open ride on
   every record, and amber/proxy must reach any output that prints the figures.
   The one `open` row (A31N) has its flagged fields (seats, cargo) NULLED at
   load with the flag text as the reason; they cannot be used because they do
   not exist past this point.
2. BURN BASIS. Only a burn whose `burn_basis_resolved` starts BLOCK is accepted
   as a block-hour burn. THERE IS NO CONVERSION PATH IN THIS CODEBASE between
   block, trip and cruise, deliberately: a TRIP or UNSTATED burn on a new row is
   missing, full stop. ONE CARVE-OUT, John's ruling of 29 August 2026: held and
   held-amber-proxy rows with an UNSTATED basis keep their burn, because it is
   the same figure the live tool has always run on and the table must not
   silently de-cost 22 live types; each carries burn_basis_note = "basis
   unstated, under query" through to output. TRIP is never carved out: an
   unstated basis might be block, a trip basis is known not to be.
3. `NOT FOUND (...)` cells are deliberate recorded absences. They parse to None
   with the reason kept in `absences`, and can never surface as display text.
4. The valuation columns (current market value, monthly lease, condition, and
   price outside the held 42) are EMPTY BY DECISION pending the IBA/Cirium/EETC
   choice. They parse to None and nothing here or downstream fills, estimates
   or scales them: a type without costs cannot be costed yet and the record
   says so via `costable`/`uncostable_reasons`.
5. NO INVENTION. Every figure a record carries traces to its row; `source` and
   `source_date` ride on the record so any surface can cite them. Nothing is
   interpolated or scaled from a neighbouring type anywhere in this module.
"""

import csv
import os

from config import AIRCRAFT_ECON_TABLE

# The numeric columns, table name -> record name (legacy AIRCRAFT field names,
# so 24 existing consumers keep working unchanged).
_NUMERIC = {
    "econ_seats": "econ_seats",
    "bus_seats": "bus_seats",
    "mtow_kg": "mtow_kg",
    "range_km": "range_km",
    "fuel_burn_kg_per_bh": "fuel_burn_kg_per_bh",
    "cargo_cap_kg": "cargo_cap_kg",
    "maint_per_bh": "maint_per_bh",
    "crew_per_bh": "crew_per_bh",
    "ownership_per_bh": "ownership_per_bh",
    "annual_util_bh": "annual_util_bh",
    "price_usd": "price_usd",
    "current market value USD": "current_market_value_usd",
    "monthly lease USD": "monthly_lease_usd",
}

# What a row must hold before the P&L may cost it. Valuation columns are NOT in
# this list by design: price_usd and the per-BH cost lines are what the current
# P&L runs on, and the empty valuation columns block nothing that worked before
# while remaining empty themselves (rule 4).
_COSTABLE_REQUIRED = ("econ_seats", "mtow_kg", "range_km", "fuel_burn_kg_per_bh",
                      "maint_per_bh", "crew_per_bh", "ownership_per_bh",
                      "annual_util_bh", "price_usd")

_STATUSES = {"held", "held-amber-proxy", "new-sourced", "open"}


def _cell(raw):
    """(value, absence_reason). '' -> (None, None); 'NOT FOUND (...)' -> (None, text)."""
    v = (raw or "").strip()
    if not v:
        return None, None
    if v.upper().startswith("NOT FOUND"):
        return None, v          # a recorded absence, never a value (rule 3)
    return v, None


def _num(raw):
    v, reason = _cell(raw)
    if v is None:
        return None, reason
    try:
        return float(v.replace(",", "")), None
    except ValueError:
        # Unparseable text in a numeric column is an absence with the text as
        # its reason, not a number and not display text.
        return None, v


def load_table(path=None):
    """Parse and enforce. Returns {key: record}; raises if the table is absent
    or malformed - there is NO fallback table in code, that is the point."""
    path = str(path or AIRCRAFT_ECON_TABLE)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"aircraft economics table not found at {path} - the tool has no "
            f"embedded fallback; set AVIA_AIRCRAFT_ECON_TABLE or restore the file")
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            key = (row.get("key") or "").strip()
            if not key:
                continue
            status = (row.get("status") or "").strip()
            if status not in _STATUSES:
                raise ValueError(f"{key}: unknown status {status!r} - the loader "
                                 f"refuses rather than guesses")
            rec = {
                "key": key,
                "type_name": (row.get("type") or "").strip(),
                "oag_codes": [c.strip().upper() for c in
                              (row.get("OAG codes") or "").replace(";", "/").split("/")
                              if c.strip()],
                "held": (row.get("held?") or "").strip() == "held",
                "status": status,
                "flags": (row.get("flags") or "").strip(),
                "priority": int(float(row.get("priority") or 0)),
                "sectors_2025": int(float((row.get("2025 sectors") or "0").replace(",", "") or 0)),
                "source": (row.get("source") or "").strip(),
                "source_date": (row.get("source date") or "").strip(),
                "avia_provenance": (row.get("existing Avia provenance") or "").strip(),
                "notes": (row.get("notes") or "").strip(),
                "burn_basis": (row.get("burn_basis_resolved") or "").strip(),
                "condition_assumed": _cell(row.get("condition assumed (half-life / full-life)"))[0],
                "absences": {},
            }
            for col, name in _NUMERIC.items():
                val, reason = _num(row.get(col))
                rec[name] = val
                if reason:
                    rec["absences"][name] = reason

            # RULE 2: burn admission. BLOCK stands; UNSTATED on a HELD row is
            # carried under the labelled carve-out; everything else is missing.
            rec["burn_basis_note"] = None
            basis = rec["burn_basis"].upper()
            if rec["fuel_burn_kg_per_bh"] is not None and not basis.startswith("BLOCK"):
                if basis.startswith("UNSTATED") or basis == "":
                    if status in ("held", "held-amber-proxy"):
                        rec["burn_basis_note"] = ("burn basis unstated, under query "
                                                  "(held-row carve-out, 29 August 2026)")
                    else:
                        rec["absences"]["fuel_burn_kg_per_bh"] = (
                            "burn basis unstated - not usable as block (rule 2, no conversion)")
                        rec["fuel_burn_kg_per_bh"] = None
                else:   # TRIP, CRUISE, anything not block: never converted, never carved out
                    rec["absences"]["fuel_burn_kg_per_bh"] = (
                        f"burn basis {rec['burn_basis']} - not block; "
                        f"conversion is prohibited (rule 2)")
                    rec["fuel_burn_kg_per_bh"] = None

            # RULE 1: the open row's flagged fields are nulled at load. The flags
            # column names seats and cargo; they cease to exist past this point.
            if status == "open":
                for f in ("econ_seats", "bus_seats", "cargo_cap_kg"):
                    if rec.get(f) is not None:
                        rec["absences"][f] = f"open-row flagged field, not usable: {rec['flags']}"
                        rec[f] = None

            # bus_seats blank on a costable row means none recorded; the held
            # rows all state it, so this only softens nothing that is used.
            if rec["bus_seats"] is None and "bus_seats" not in rec["absences"]:
                rec["bus_seats"] = 0.0

            # Costable? Name every missing piece rather than a bare no (rule 4).
            missing = [f for f in _COSTABLE_REQUIRED if rec.get(f) is None]
            rec["costable"] = (status != "open") and not missing
            rec["uncostable_reasons"] = ([] if rec["costable"] else
                ((["status 'open': row under query with Stefan"] if status == "open" else []) +
                 [f"{f}: {rec['absences'].get(f, 'empty pending the IBA/Cirium/EETC valuation decision')}"
                  for f in missing]))
            out[key] = rec
    if not out:
        raise ValueError(f"aircraft economics table at {path} parsed to zero rows")
    return out


def table_row_count(path=None):
    """Data rows in the CSV, for the row-count lock in the tests."""
    path = str(path or AIRCRAFT_ECON_TABLE)
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return sum(1 for r in csv.DictReader(fh) if (r.get("key") or "").strip())
