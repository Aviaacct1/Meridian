#!/usr/bin/env python3
"""
Avia Solutions - integrated business case builder.
One call ties the chain together: QSI demand forecast -> revenue fares -> aircraft
economics (cost + profit) -> the standard output workbook, with the turnaround and
annual P&L and the fleet requirement on a Route Economics sheet.

  from build_business_case import build_business_case
  build_business_case(cfg, results, rev_cfg, "Business_Case.xlsx",
                      airline_type="FSC", aircraft_age=5,
                      origin_charges={...}, dest_charges={...})

Airport charges are a per-route INPUT (the per-route layer): pass origin_charges /
dest_charges for any airport not already in aircraft_economics.AIRPORTS.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def build_business_case(cfg, results, rev_cfg, out_path, *, aircraft=None,
                        airline_type=None, aircraft_age=0.0,
                        origin_charges=None, dest_charges=None, incentive=None,
                        econ_lf=None, bus_lf=None, operating_weeks=52.0,
                        analyst='Avia Solutions'):
    """Build the integrated business-case workbook from a forecast + revenue config."""
    from aircraft_economics import route_pnl_from_revenue
    from output_workbook import StandardOutputWriter
    rp = route_pnl_from_revenue(
        cfg, results, rev_cfg, aircraft=aircraft, airline_type=airline_type,
        aircraft_age=aircraft_age, origin_charges=origin_charges, dest_charges=dest_charges,
        incentive=incentive, econ_lf=econ_lf, bus_lf=bus_lf)
    writer = StandardOutputWriter(
        cfg, results, route_pnl=rp, analyst=analyst,
        frequency_per_week=getattr(cfg, 'frequency', None), operating_weeks=operating_weeks)
    writer.write_all()
    return writer.save(out_path)


if __name__ == "__main__":
    # Demo: BA LHR-SJC integrated business case. Needs the QSI workbooks + demand on this PC.
    # Airport charges for LHR/SJC are INDICATIVE here (not in the validated AIRPORTS table);
    # for a client run, pull both ends from RDC and pass via origin_charges / dest_charges.
    from route_config import RouteConfig
    from convergence import converge_to_load_factor
    from revenue_forecast import RevenueConfig

    cfg = RouteConfig.ba_lhr_sjc()
    res, adj = converge_to_load_factor(cfg, 0.829)
    rev = RevenueConfig()  # default fares; analyst sets the real ones

    lhr = dict(country="UK", landing_per_turn=4000.0, pax_charge_per_pax=35.0,
               ground_handling_per_turn=4000.0, recovery_per_pax=0.0)   # INDICATIVE
    sjc = dict(country="US", landing_per_turn=2000.0, pax_charge_per_pax=15.0,
               ground_handling_per_turn=2500.0, recovery_per_pax=0.0)   # INDICATIVE

    out = build_business_case(
        cfg, res, rev, "BA_LHR_SJC_business_case.xlsx",
        airline_type="FSC", aircraft_age=5,
        origin_charges=lhr, dest_charges=sjc, operating_weeks=52)
    print("wrote", out)
