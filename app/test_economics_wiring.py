#!/usr/bin/env python3
"""
Quick test of the economics wiring into the report workbook.
Run:  py -3.12 test_economics_wiring.py
Writes 'Route_Economics_test.xlsx' and prints the key P&L numbers.
"""
import aircraft_economics as ae
from output_workbook import StandardOutputWriter


# Build a RoutePnL two ways to exercise both the direct path and the config adapter.
# (1) Direct - the Genoa A321XLR illustration.
inc = ae.Incentive(home="GOA", waiver_pct=0.50, support_per_turn=1500)
rp_direct = ae.RoutePnL(
    "New entrant", "A21X", "GOA", "JFK", 3500, 540,
    econ_lf=0.78, bus_lf=0.65, econ_fare_ow=360, bus_fare_ow=1500,
    airspace={"Italy": 0.10, "France": 0.05, "US": 0.05}, incentive=inc,
    airline_type="LCC", aircraft_age=2,
)

# (2) Via the RouteConfig adapter (maps carrier_type -> airline_type, aircraft string -> key).
class _Cfg:
    airline_name = "New entrant"; airline_code = "XX"
    home_airport_code = "GOA"; dest_airport_code = "JFK"
    distance_nm = 3500; flight_time_hrs = 8.75
    aircraft_type = "a321xlr"; carrier_type = "Low Cost"

rp_adapter = ae.route_pnl_from_config(
    _Cfg(), {"load_factor": 0.78}, econ_fare_ow=360, bus_fare_ow=1500,
    aircraft_age=2, airspace={"Italy": 0.10, "France": 0.05, "US": 0.05}, incentive=inc,
)

for tag, rp in [("direct", rp_direct), ("adapter", rp_adapter)]:
    x = rp.compute()
    print(f"\n[{tag}] {rp.aircraft} {rp.origin}-{rp.dest}  airline_type={rp.airline_type}")
    print(f"  revenue {x['gross_rev']:,.0f}  cost {x['total_cost']:,.0f}  "
          f"profit {x['profit']:,.0f}  margin {x['margin']:.1%}  breakeven {x['breakeven_lf']:.1%}")
    print(f"  maintenance {x['maintenance']:,.0f}  [{x['maint_basis']}]")
    print(f"  ownership   {x['ownership']:,.0f}  [{x['own_basis']}]")
    print(f"  with incentive: profit {x['profit_with_incentive']:,.0f}  margin {x['margin_with_incentive']:.1%}")

# Render the Route Economics sheet (no full pipeline needed for this focused test).
writer = StandardOutputWriter(config=None, results=None, route_pnl=rp_direct,
                              frequency_per_week=4, operating_weeks=30)
writer._write_route_economics()
if 'Sheet' in writer.wb.sheetnames:
    del writer.wb['Sheet']
writer.wb.save("Route_Economics_test.xlsx")
print("\nWrote Route_Economics_test.xlsx (open the 'Route Economics' sheet).")

# Render the client P&L slide from the same RoutePnL (real numbers).
from economics_slide import slide_from_route_pnl
slide_from_route_pnl(rp_direct, "Route_Economics_slide.pptx",
                     title="Genoa-New York: A321XLR route economics")
print("Wrote Route_Economics_slide.pptx (the deck slide).")
