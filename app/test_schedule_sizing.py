#!/usr/bin/env python3
"""Offline test of the schedule sizer. No engine, no stores, no network.

    py -3.12 test_schedule_sizing.py

The engine is replaced by a model of it: demand rises with frequency but less
than proportionally, which is the behaviour that makes the frequency a fixed
point in the first place. Every number here is a TEST FIXTURE.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schedule_sizing as SS

FAIL = []
CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    print("%-52s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


def engine(seats=200, weeks=52.0, base=60000.0, elasticity=0.35, cap=True):
    """A stand-in for calibrated_forecast, as a function of frequency alone.

    Demand grows with frequency to the power of `elasticity`, which is the
    schedule-quality effect: more frequency wins more share, but with strongly
    diminishing returns. That is what makes cutting the frequency reduce demand
    by less than it reduces capacity, and so what makes the loop converge.
    """
    def f(freq):
        demand = base * (freq / 7.0) ** elasticity
        capacity = seats * freq * weeks
        carried = min(demand, capacity) if cap else demand
        return {"ok": True,
                "demand": {"total": round(carried)},
                "capacity": {"freq": freq, "aircraft": "A21X",
                             "load": carried / capacity if capacity else 0.0,
                             "annual_capacity": capacity}}
    return f


# --- 1. it converges downward on an over-scheduled route ---------------------
r = SS.size_schedule(engine(seats=200, base=60000.0), freq_start=14)
check("over-scheduled route sizes down", r["ok"] and r["freq"] < 14,
      "14 -> %s a week" % r["freq"])
check("converged", r["converged"], r["note"])
check("lands near the planning load", abs(r["load"] - 0.80) < 0.12,
      "%.1f%%" % (r["load"] * 100))
check("the path is recorded", len(r["path"]) >= 2, r["path"])
check("the forecast at that frequency comes back",
      r["fc"] and r["fc"]["capacity"]["freq"] == r["freq"])

# --- 2. a schedule already right is left alone -------------------------------
# find the frequency the model settles on, then start there
settled = r["freq"]
r2 = SS.size_schedule(engine(seats=200, base=60000.0), freq_start=settled)
check("a correctly sized schedule is not moved", r2["freq"] == settled,
      "%s -> %s" % (settled, r2["freq"]))
check("and it says so in one round", r2["rounds"] == 1, "%d round(s)" % r2["rounds"])

# --- 3. the 38% load factor case from John's review --------------------------
# a thin market on a big schedule: this is what produced the deck that argued
# against its own route
thin = SS.size_schedule(engine(seats=235, base=22000.0), freq_start=5)
check("the thin-market case sizes down hard", thin["freq"] < 5,
      "5 -> %s a week, %.0f%% load" % (thin["freq"], thin["load"] * 100))
check("and the result is a schedule that fills", thin["load"] > 0.55,
      "%.0f%%" % (thin["load"] * 100))

# --- 4. bounds ---------------------------------------------------------------
tiny = SS.size_schedule(engine(seats=300, base=400.0), freq_start=7)
check("never sizes below the floor", tiny["freq"] >= SS.MIN_FREQ, tiny["freq"])
huge = SS.size_schedule(engine(seats=90, base=900000.0), freq_start=7, max_freq=21)
check("never sizes above the ceiling", huge["freq"] <= 21, huge["freq"])

# --- 5. failure reports rather than passing the input back silently ----------
def boom(freq):
    raise RuntimeError("store unavailable")


bad = SS.size_schedule(boom, freq_start=6)
check("an engine exception is reported", not bad["ok"] and "store unavailable" in bad["note"])
check("and the frequency it started with comes back", bad["freq"] == 6, bad["freq"])

notok = SS.size_schedule(lambda f: {"ok": False, "error": "no route"}, freq_start=6)
check("a failed forecast is reported", not notok["ok"] and "no route" in notok["note"])

noload = SS.size_schedule(lambda f: {"ok": True, "capacity": {"freq": f}}, freq_start=6)
check("a missing load factor is reported",
      not noload["ok"] and "load factor" in noload["note"])

# --- 6. oscillation is named, not hidden -------------------------------------
def flipflop(freq):
    # 4 wants 6, 6 wants 4: the classic two-cycle
    load = {4: 0.90, 5: 0.85, 6: 0.55}.get(freq, 0.80)
    return {"ok": True, "capacity": {"freq": freq, "load": load}}


osc = SS.size_schedule(flipflop, freq_start=4, max_rounds=6)
check("the neighbour test picks the closest fill to target",
      osc["ok"] and abs(osc["load"] - SS.PLANNING_LF) <= 0.06,
      "%d a week at %.0f%%" % (osc["freq"], osc["load"] * 100))

# a genuine two-cycle, with no neighbour that helps, must still be named
def hardcycle(freq):
    load = {3: 1.00, 4: 0.60, 5: 0.60, 2: 1.00}.get(freq, 0.80)
    return {"ok": True, "capacity": {"freq": freq, "load": load}}


hc = SS.size_schedule(hardcycle, freq_start=3, max_rounds=6)
check("a true oscillation is named rather than hidden",
      hc["ok"] and (("oscillated" in hc["note"]) or ("not settled" in hc["note"])),
      hc["note"])

# --- 6b. rounding is half up, not banker's -----------------------------------
def exact_half(freq):
    # at 4 a week and 90% load the implied frequency is exactly 4.5
    return {"ok": True, "capacity": {"freq": freq, "load": 0.90 if freq == 4 else 0.72}}


half = SS.size_schedule(exact_half, freq_start=4)
check("a .5 implied frequency rounds up, not to even", half["freq"] == 5,
      "%d a week at %.0f%%" % (half["freq"], half["load"] * 100))

# --- 7. non-convergence is named ---------------------------------------------
class Drift(object):
    """Never settles: the load always asks for one more than it was given."""
    def __call__(self, freq):
        return {"ok": True, "capacity": {"freq": freq, "load": 0.80 * (freq + 1) / freq}}


slow = SS.size_schedule(Drift(), freq_start=2, max_rounds=3)
check("non-convergence is named", not slow["converged"] and "not settled" in slow["note"],
      slow["note"])

# --- 8. describe() is readable ------------------------------------------------
d = SS.describe(r)
check("describe prints the path", "path:" in d and "->" in d)
print("\n" + d)

print("\n%d checks, %d failed" % (CHECKS, len(FAIL)))
if FAIL:
    print("FAILED: %s" % ", ".join(FAIL))
sys.exit(1 if FAIL else 0)
