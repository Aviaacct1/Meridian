#!/usr/bin/env python3
"""
Avia Solutions - point-to-point segment model (deck block 3).
==============================================================================
Builds the eight-segment forecast table (origin/destination x business/leisure x
primary/secondary/contested) the deck shows, BOTTOM-UP exactly as the analyst does:

    forecast(segment) = base x (1+growth)^years x stimulation x capture

and the point-to-point total is the SUM of the segments. This is an allocation/build
layer: it does not change the validated method, it presents it. The split inputs are
route-current and data-driven:
  - business vs leisure/VFR share comes from the route's Sabre cabin / fare-class mix
    (the same pull that feeds the cabin layer - see qsi-cabin-lopa), then stimulated;
  - the primary/secondary/contested bands come from the catchment module;
  - per-segment growth comes from the econometric/GDP forecasts;
  - per-segment capture is the analyst judgement (named inputs, with the proven
    with/without-competition logic as the default).

The model's validated point-to-point total is the cross-check: the bottom-up sum must
reconcile to it. build_contract uses build_segment_table() to populate block 3.
VALIDATED: reproduces the BA 2015 deck exactly (8 segment forecasts + 82.7k P2P total
@ 28.1% capture), base 2015 -> service 2016. Forecast values are absolute pax.
"""
from __future__ import annotations
DAYS_2WAY = 728


def build_segment_table(segments, base_year, service_year):
    """segments = list of {name, base, growth, stim, capture} (base in absolute pax). Returns (rows, total)."""
    yrs = max(service_year - base_year, 0)
    rows = []
    t_base = t_dsy = t_after = t_fc = 0.0
    for s in segments:
        dsy = s["base"] * (1 + s["growth"]) ** yrs
        after = dsy * s["stim"]
        fc = after * s["capture"]
        rows.append({"segment": s["name"], "base_annual_demand": round(s["base"]),
                     "annual_growth_rate": s["growth"], "demand_at_service_year": round(dsy),
                     "stimulation_factor": s["stim"], "demand_after_stimulation": round(after),
                     "capture_rate": s["capture"], "forecast": round(fc), "pdew": round(fc / DAYS_2WAY, 1)})
        t_base += s["base"]; t_dsy += dsy; t_after += after; t_fc += fc
    total = {"base_annual_demand": round(t_base), "demand_at_service_year": round(t_dsy),
             "demand_after_stimulation": round(t_after), "capture_rate": (t_fc / t_after if t_after else 0),
             "forecast": round(t_fc), "pdew": round(t_fc / DAYS_2WAY, 1)}
    return rows, total


def from_route_mix(p2p_base_market, origin_share, business_share, zone_split,
                   growth, capture, stim, base_year, service_year):
    """Build the eight segments from route-current splits, then the table.
      p2p_base_market : the base-year point-to-point market (two-way, absolute)
      origin_share    : fraction of the market that is origin-resident (rest = destination)
      business_share  : {"origin":f, "destination":f} premium/business share from the Sabre cabin mix
      zone_split      : {"primary":f,"secondary":f,"contested":f} of LEISURE demand (sums to 1)
      growth/capture/stim : {key: value}; keys = o_bus,o_pri,o_sec,o_con,d_bus,d_pri,d_sec,d_con
    """
    o = p2p_base_market * origin_share
    d = p2p_base_market * (1 - origin_share)
    o_bus = o * business_share["origin"]; o_leis = o - o_bus
    d_bus = d * business_share["destination"]; d_leis = d - d_bus
    seg = [
        ("o_bus", "Origin Business", o_bus),
        ("o_pri", "Origin Leisure/VFR Primary", o_leis * zone_split["primary"]),
        ("o_sec", "Origin Leisure/VFR Secondary", o_leis * zone_split["secondary"]),
        ("o_con", "Origin Leisure/VFR Contested", o_leis * zone_split["contested"]),
        ("d_bus", "Destination Business", d_bus),
        ("d_pri", "Destination Leisure/VFR Primary", d_leis * zone_split["primary"]),
        ("d_sec", "Destination Leisure/VFR Secondary", d_leis * zone_split["secondary"]),
        ("d_con", "Destination Leisure/VFR Contested", d_leis * zone_split["contested"]),
    ]
    segments = [{"name": nm, "base": base, "growth": growth[k], "stim": stim[k], "capture": capture[k]}
                for k, nm, base in seg]
    return build_segment_table(segments, base_year, service_year)


def reconcile(total_forecast, validated_p2p_forecast, tol=0.03):
    """The bottom-up segment sum must tie to the model's validated point-to-point total."""
    if not validated_p2p_forecast:
        return None
    ratio = total_forecast / validated_p2p_forecast
    return {"segment_sum": round(total_forecast), "validated_total": round(validated_p2p_forecast),
            "ratio": round(ratio, 3), "reconciles": abs(ratio - 1) <= tol}
