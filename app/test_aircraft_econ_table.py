#!/usr/bin/env python3
"""
Locks the aircraft economics reference-table rules in place (29 August 2026).

Run directly: py -3.12 test_aircraft_econ_table.py
Standalone-script convention (see BASELINE-23Aug2026.md): prints per-check
PASS/FAIL and exits non-zero on any failure. No stores needed.

What is locked, per the table's own rules:
  1. the A31N (open) flagged fields are refused at load
  2. UNSTATED / TRIP burns are never converted: missing on new rows, and the
     held-row carve-out (John, 29 August 2026) is labelled, not silent
  3. NOT FOUND (...) parses as a recorded absence, never as a value
  4. loader row count matches the table
  5. valuation columns stay empty: nothing fills, estimates or scales them
  6. every costable figure can cite its row (source reachable)
  7. the loaded AIRCRAFT keeps the live shape and the held keys
"""

import sys

FAILURES = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    if cond:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}  {detail}")
        FAILURES.append(name)


def main():
    from aircraft_econ_loader import load_table, table_row_count
    from aircraft_economics import AIRCRAFT, TYPES_KNOWN

    t = load_table()

    print("== rule 4: row count ==")
    check("loader rows == table rows", len(t) == table_row_count(),
          f"{len(t)} vs {table_row_count()}")
    check("all rows keyed and statused",
          all(r["status"] in ("held", "held-amber-proxy", "new-sourced", "open")
              for r in t.values()))

    print("== rule 1: the open row (A31N) ==")
    a = t.get("A31N")
    check("A31N present", a is not None)
    if a:
        check("A31N status open", a["status"] == "open")
        check("A31N seats refused", a["econ_seats"] is None and a["bus_seats"] is None)
        check("A31N cargo refused", a["cargo_cap_kg"] is None)
        check("A31N refusal carries the flag text",
              "not usable" in a["absences"].get("econ_seats", ""))
        check("A31N not costable", not a["costable"])
        check("A31N absent from AIRCRAFT", "A31N" not in AIRCRAFT)

    print("== rule 2: burn basis, never converted ==")
    # TRIP rows: burn refused outright, reason names the prohibition
    for k in ("CRJ550", "B77L", "MD82"):
        r = t[k]
        check(f"{k} TRIP burn missing", r["fuel_burn_kg_per_bh"] is None)
        check(f"{k} reason cites rule 2",
              "conversion is prohibited" in r["absences"].get("fuel_burn_kg_per_bh", ""))
    # UNSTATED on a NEW row: missing
    for k in ("A343", "F100"):
        r = t[k]
        check(f"{k} UNSTATED new-row burn missing", r["fuel_burn_kg_per_bh"] is None)
    # UNSTATED on a HELD row: carried under the labelled carve-out, never silently
    for k in ("A320", "B789", "B77W"):
        r = t[k]
        check(f"{k} held burn carried", r["fuel_burn_kg_per_bh"] is not None)
        check(f"{k} carve-out labelled", (r["burn_basis_note"] or "").startswith("burn basis unstated"))
        check(f"{k} label reaches AIRCRAFT",
              (AIRCRAFT[k].get("burn_basis_note") or "").startswith("burn basis unstated"))
    # BLOCK rows carry no carve-out label
    check("E175 BLOCK burn present, unlabelled",
          t["E175"]["fuel_burn_kg_per_bh"] is not None and t["E175"]["burn_basis_note"] is None)
    # and no conversion helper exists anywhere in the loader
    import aircraft_econ_loader as L
    src = open(L.__file__, encoding="utf-8").read()
    check("no block/trip conversion code in the loader",
          "trip_to_block" not in src and "cruise_to_block" not in src and "* 1." not in
          src.split("def _num")[0])

    print("== rule 3: NOT FOUND is an absence ==")
    su = t["SU95"]
    check("SU95 seats absent", su["econ_seats"] is None)
    check("SU95 absence reason recorded", "NOT FOUND" in su["absences"].get("econ_seats", ""))
    check("no NOT FOUND text survives as a value",
          all(not (isinstance(v, str) and v.upper().startswith("NOT FOUND"))
              for r in t.values() for f, v in r.items() if f != "absences"
              for v in ([v] if not isinstance(v, list) else v)))

    print("== rule 4/5: valuation empty by decision, nothing invented ==")
    check("no market value anywhere",
          all(r["current_market_value_usd"] is None for r in t.values()))
    check("no lease rate anywhere", all(r["monthly_lease_usd"] is None for r in t.values()))
    check("no condition assumed anywhere", all(r["condition_assumed"] is None for r in t.values()))
    check("every uncostable row names its gaps",
          all(r["uncostable_reasons"] for r in t.values() if not r["costable"]))
    check("uncostable reasons cite the valuation decision where that is the gap",
          any("IBA/Cirium/EETC" in x for x in t["E175"]["uncostable_reasons"]))

    print("== provenance and the live shape ==")
    check("every costable row cites source and date",
          all((AIRCRAFT[k]["source"] or AIRCRAFT[k]["src"]) and "source_date" in AIRCRAFT[k]
              for k in AIRCRAFT))
    check("AIRCRAFT holds exactly the held 42",
          set(AIRCRAFT) == {k for k, r in t.items() if r["held"]},
          f"{len(AIRCRAFT)} costable")
    check("status labels ride on AIRCRAFT rows",
          all(AIRCRAFT[k]["status"] in ("held", "held-amber-proxy") for k in AIRCRAFT))
    check("amber types wear the label", AIRCRAFT["E190"]["status"] == "held-amber-proxy")
    legacy = ("econ_seats", "bus_seats", "mtow_kg", "cargo_cap_kg", "fuel_burn_kg_per_bh",
              "maint_per_bh", "crew_per_bh", "ownership_per_bh", "price_usd",
              "annual_util_bh", "range_km", "category", "src")
    check("legacy consumer fields all present",
          all(f in AIRCRAFT[k] for k in AIRCRAFT for f in legacy))
    check("TYPES_KNOWN covers the full table", len(TYPES_KNOWN) == table_row_count())

    print(f"\n{CHECKS} checks, {len(FAILURES)} failed")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
