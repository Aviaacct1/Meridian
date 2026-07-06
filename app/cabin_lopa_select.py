#!/usr/bin/env python3
"""
Avia Solutions - cabin + LOPA selection.
==============================================================================
Extends aircraft selection from GAUGE-only to GAUGE + LOPA. For a route's stimulated
cabin demand (First/Business/Premium-economy/Economy, route-current from Sabre - see
qsi-cabin-lopa), it scores each available layout and picks the one that earns the most,
so a premium-rich config wins where the front fills (e.g. SJC-LHR) and a denser config
wins where it does not (e.g. a leisure route). Same jet, different config, different P&L.

Revenue model: each cabin earns its fare up to its OWN demand; economy overflow op-ups into
empty premium seats at the economy fare, but only at OPUP_EFFICIENCY (airlines protect premium
inventory and op-up dilutes it), so surplus premium seats are largely dead weight on an
economy-heavy route. Cost is gauge-level, so for one gauge the best LOPA is the highest-revenue
one; across gauges the selector nets revenue against the aircraft's annual cost (aircraft_select).
"""
from __future__ import annotations

CABINS = ["first", "business", "premium_coach", "coach"]
OPUP_EFFICIENCY = 0.6   # share of empty premium seats economy overflow can actually fill


def fare_ladder(econ_fare_ow, first=4.0, business=3.0, premium=1.6):
    return {"first": econ_fare_ow * first, "business": econ_fare_ow * business,
            "premium_coach": econ_fare_ow * premium, "coach": econ_fare_ow}


def cabin_demand(total_each_way, mix, stim=1.0):
    """Each-way annual demand by cabin from the route's Sabre cabin shares (stimulated)."""
    return {c: total_each_way * mix.get(c, 0.0) * stim for c in CABINS}


def score_config(lopa, demand_ew, fares, freq, opup_efficiency=OPUP_EFFICIENCY):
    cap = {c: lopa.get(c, 0) * freq * 52 for c in CABINS}
    filled = {c: min(demand_ew.get(c, 0), cap[c]) for c in CABINS}
    rev_ew = sum(filled[c] * fares[c] for c in CABINS)
    empty_premium = sum(max(cap[c] - filled[c], 0) for c in ("first", "business", "premium_coach"))
    coach_overflow = max(demand_ew.get("coach", 0) - cap["coach"], 0)
    opup = min(coach_overflow, empty_premium * opup_efficiency)
    rev_ew += opup * fares["coach"]
    seats_cap = sum(cap.values())
    carried = sum(filled.values()) + opup
    return {"revenue_two_way": round(rev_ew * 2), "total_lf": round(carried / seats_cap, 3) if seats_cap else 0.0,
            "seats": sum(lopa.get(c, 0) for c in CABINS), "carried_each_way": round(carried),
            "empty_premium_each_way": round(empty_premium - opup), "fill": {c: round(filled[c]) for c in CABINS}}


def choose_lopa(aircraft, airline_iata, demand_ew, fares, freq, store=None, opup_efficiency=OPUP_EFFICIENCY):
    """Best LOPA variant for one aircraft against the route's cabin demand (max revenue)."""
    from lopa import variants_for
    vs = variants_for(aircraft, airline_iata, store=store)
    scored = []
    for name, lop in vs.items():
        s = score_config(lop, demand_ew, fares, freq, opup_efficiency)
        s["variant"] = name; s["lopa"] = lop
        scored.append(s)
    scored.sort(key=lambda x: -x["revenue_two_way"])
    return (scored[0] if scored else None), scored


if __name__ == "__main__":
    variants = {"with_first": {"first": 8, "business": 42, "premium_coach": 39, "coach": 127},
                "no_first":   {"first": 0, "business": 48, "premium_coach": 40, "coach": 128}}
    fares = fare_ladder(600.0); freq = 7

    def run(label, total_ew, mix):
        dem = cabin_demand(total_ew, mix, stim=1.05)
        scored = []
        for name, lop in variants.items():
            s = score_config(lop, dem, fares, freq); s["variant"] = name; scored.append(s)
        scored.sort(key=lambda x: -x["revenue_two_way"])
        print(f"\n{label}: {total_ew:,}/yr each way")
        for s in scored:
            print(f"   {s['variant']:11} rev ${s['revenue_two_way']:>12,}  LF {s['total_lf']:.0%}  "
                  f"empty premium {s['empty_premium_each_way']:>6,}/yr")
        print(f"   -> BEST: {scored[0]['variant']}")

    run("PREMIUM-HEAVY (SJC-LHR type)", 60000, {"first": 0.03, "business": 0.20, "premium_coach": 0.12, "coach": 0.65})
    run("ECONOMY-HEAVY (leisure type)", 60000, {"first": 0.0, "business": 0.05, "premium_coach": 0.04, "coach": 0.91})
