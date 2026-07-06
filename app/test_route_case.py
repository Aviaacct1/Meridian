#!/usr/bin/env python3
"""
Avia Solutions - acceptance test for the generalised route pipeline.
====================================================================
Locks in the Genoa-New York reference so the general path (RouteCase + assess.py) cannot
silently drift as the pipeline is extended. Two layers:

  STRUCTURAL (always run, no data needed)
    - a RouteCase round-trips through JSON unchanged,
    - the airport sets partition correctly (catchment/calibration exclude cache-only; the
      cache set includes the cross-border competitor).

  ACCEPTANCE (runs only when the data files are present)
    - assess.py genoa_nyc <dump>, offline, reproduces genoa_nyc_case.json to tolerance:
      population, the GOA-New York natural catchment, the repatriated demand, and the route
      and annual P&L. Skips (does not fail) if the GeoNames dump / drive cache / fitted
      params / reference output are not beside the app, so it is safe to run anywhere.

RUN:
    py -3.12 test_route_case.py            # plain runner, prints PASS/SKIP per check
    pytest test_route_case.py              # also works under pytest
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from route_case import RouteCase, genoa_nyc

# reference numbers (from genoa_nyc_case.json, the validated hand-built run)
REF_FILE = os.path.join(HERE, "genoa_nyc_case.json")
TOL_ABS = 1e-3                      # the general path should match to the rounding floor
DUMP_CANDIDATES = ["cities5000.txt", "IT.txt"]


# --------------------------------------------------------------- structural tests
def test_routecase_roundtrips():
    """A case survives to_dict -> from_dict unchanged (so saved cases reload exactly)."""
    rc = genoa_nyc()
    rc2 = RouteCase.from_dict(rc.to_dict())
    assert rc2.to_dict() == rc.to_dict(), "RouteCase did not round-trip through its dict form"


def test_airport_sets_partition():
    """Cache-only competitors stay out of catchment scoring and calibration but in the cache."""
    rc = genoa_nyc()
    catchment = rc.airport_codes("catchment")
    calibration = rc.airport_codes("calibration")
    cache = rc.airport_codes("cache")
    assert "NCE" in cache, "cache set should include the cache-only competitor (Nice)"
    assert "NCE" not in catchment, "Nice must not be scored in the catchment"
    assert "NCE" not in calibration, "Nice must not be a calibration target"
    assert catchment == ["GOA", "MXP", "LIN", "BGY", "TRN", "BLQ"]
    assert rc.home in catchment, "home airport must be among the catchment airports"


# --------------------------------------------------------------- acceptance test
def _find_dump():
    for name in DUMP_CANDIDATES:
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            return p
    return None


def _data_ready():
    """All inputs for the offline acceptance run present?"""
    dump = _find_dump()
    cache = os.path.join(HERE, "genoa_drive.json")
    params = os.path.join(HERE, "genoa_catchment_params.json")
    observed = os.path.join(HERE, "cases", "genoa_nyc_observed.json")
    return dump and all(os.path.exists(p) for p in (cache, params, observed, REF_FILE)), dump


def test_genoa_acceptance():
    """assess.py genoa_nyc, offline, reproduces the validated reference within tolerance."""
    ready, dump = _data_ready()
    if not ready:
        print("SKIP test_genoa_acceptance: data files not beside the app "
              "(need cities5000.txt, genoa_drive.json, genoa_catchment_params.json, "
              "cases/genoa_nyc_observed.json, genoa_nyc_case.json)")
        return "skip"

    ref = json.load(open(REF_FILE))
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "out.json")
        cmd = [sys.executable, os.path.join(HERE, "assess.py"), "genoa_nyc", dump, "--out", out]
        r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
        assert r.returncode == 0, f"assess.py failed:\n{r.stdout}\n{r.stderr}"
        new = json.load(open(out))

    def close(a, b, label):
        assert abs(float(a) - float(b)) <= TOL_ABS, f"{label}: ref {a} vs new {b}"

    for k in ("population", "natural", "current", "repatriated", "directional_demand",
              "econ_lf", "bus_lf"):
        close(ref[k], new[k], k)
    for k in ("gross_rev", "total_cost", "profit", "margin", "breakeven_lf"):
        close(ref["route_pnl"][k], new["route_pnl"][k], "route." + k)
    for k in ("annual_gross_rev", "annual_total_cost", "annual_profit"):
        close(ref["annual_pnl"][k], new["annual_pnl"][k], "annual." + k)
    return "pass"


# --------------------------------------------------------------- plain runner
def _run_all():
    structural = [test_routecase_roundtrips, test_airport_sets_partition]
    passed = skipped = 0
    for fn in structural:
        fn()
        print(f"PASS {fn.__name__}")
        passed += 1
    res = test_genoa_acceptance()
    if res == "skip":
        skipped += 1
    else:
        print("PASS test_genoa_acceptance (general path reproduces genoa_nyc_case.json)")
        passed += 1
    print(f"\n{passed} passed, {skipped} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(_run_all())
