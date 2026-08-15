#!/usr/bin/env python3
"""
Avia Solutions - refresh pickup, tested against the folder as it actually is.
=============================================================================
Every name below is real or a real variant from the Egnyte survey of 15 August.
No store, no network:  py -3.12 test_refresh_pickup.py
"""
import datetime
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import refresh_pickup as RP

TODAY = datetime.date(2026, 8, 15)


def test_monthly_names_with_real_variants():
    for name, region, label in [
        ("Africa Apr 2024.xlsx", "Africa", "2024-04"),
        ("Latin america Jul 2025.xlsx", "Latin America", "2025-07"),
        ("MiddlE East Dec 2023.xlsx", "Middle East", "2023-12"),
        ("Southwest Pacific Jan 2019.xlsx", "Southwest Pacific", "2019-01"),
    ]:
        c = RP.classify(name, today=TODAY)
        assert c["action"] == "ingest" and c["region"] == region and c["label"] == label, (name, c)


def test_halfmonth_routes_to_its_own_spine():
    c = RP.classify("Asia 01Apr to 15Apr 2024.xlsx", today=TODAY)
    assert c["action"] == "hold" and c["source"] == "oag_halfmonth", c


def test_sabre_variants_parse_on_year_not_token():
    for name, year, d in [
        ("World2013POO-1av002013-235-20260423121045.csv", 2013, "POO"),
        ("World2016NDPOO-1av002013-235-20260424073031.csv", 2016, "ND"),
        ("World2019PooND-1av002013-235-20260423221120.csv", 2019, "ND"),
    ]:
        c = RP.classify(name, today=TODAY)
        assert c["source"] == "sabre_annual" and c["year"] == year, (name, c)
        assert c["directionality"] == d, (name, c)
        assert c["action"] == "confirm", "complete years plan as confirm, never auto: %r" % c


def test_vintage_guard_holds_the_current_year():
    c = RP.classify("World2026POO-1av002013-235-20260901.csv", today=TODAY)
    assert c["action"] == "hold" and "base year" in c["reason"], c


def test_junk_and_tooling():
    assert RP.classify("Data Extraction.py", today=TODAY)["action"] == "skip"
    assert RP.classify("random notes.docx", today=TODAY)["action"] == "refuse"
    assert RP.classify("Atlantis Apr 2024.xlsx", today=TODAY)["action"] == "refuse"


def test_manifest_new_skip_reingest():
    with tempfile.TemporaryDirectory() as d:
        f1 = os.path.join(d, "Africa Apr 2024.xlsx")
        open(f1, "wb").write(b"version one")
        os.mkdir(os.path.join(d, "old"))                      # never descended into
        open(os.path.join(d, "old", "Africa Apr 2015.xlsx"), "wb").write(b"x")
        p = RP.plan(d, {}, today=TODAY)
        assert len(p["ingest"]) == 1 and p["ingest"][0]["name"] == "Africa Apr 2024.xlsx", p
        key, fp = p["ingest"][0]["key"], p["ingest"][0]["fingerprint"]
        man = {key: {"name": "Africa Apr 2024.xlsx", "fingerprint": fp}}
        p2 = RP.plan(d, man, today=TODAY)
        assert not p2["ingest"] and len(p2["skip"]) == 1, "unchanged file must skip: %r" % p2
        open(f1, "wb").write(b"version two, corrected extract")
        p3 = RP.plan(d, man, today=TODAY)
        assert not p3["ingest"] and len(p3["reingest"]) == 1, p3
        assert "dropped and reloaded" in p3["reingest"][0]["reason"]


def test_status_write_and_read():
    with tempfile.TemporaryDirectory() as d:
        sp = os.path.join(d, "refresh_status.json")
        RP.write_status(sp, "oag_monthly", "2026-07", "PASS", "7 file(s) ingested")
        st = json.load(open(sp, encoding="utf-8"))
        assert st["oag_monthly"]["result"] == "PASS" and st["oag_monthly"]["label"] == "2026-07"


def main():
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS  %s" % name)
            except AssertionError as e:
                fails += 1
                print("FAIL  %s: %s" % (name, e))
            except Exception as e:  # noqa: BLE001
                fails += 1
                print("ERROR %s: %s: %s" % (name, type(e).__name__, e))
    print("%d failure(s)" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
