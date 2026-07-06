#!/usr/bin/env python3
"""
Demo: a Network P&L for a Genoa base flying three NYC-area routes on one A321XLR.
Run:  py -3.12 test_network.py   ->  writes Network_PnL_Genoa.xlsx
Shows the network layer: several routes sharing a fleet, with totals and the frame count.
"""
from aircraft_economics import RoutePnL, AnnualRoutePnL, network_pnl
from network_report import write_network_workbook

# Indicative US charges for airports not in the seeded AIRPORTS table (per-route input layer).
ewr = dict(country="US", landing_per_turn=2600.0, pax_charge_per_pax=26.0,
           ground_handling_per_turn=3000.0, recovery_per_pax=0.0)
bos = dict(country="US", landing_per_turn=2200.0, pax_charge_per_pax=22.0,
           ground_handling_per_turn=2600.0, recovery_per_pax=0.0)

common = dict(econ_lf=0.78, bus_lf=0.65, econ_fare_ow=360, bus_fare_ow=1500,
              airline_type="LCC", aircraft_age=2,
              airspace={"Italy": 0.10, "France": 0.05, "US": 0.05})

r_jfk = RoutePnL("New entrant", "A21X", "GOA", "JFK", 3500, 540, **common)
r_ewr = RoutePnL("New entrant", "A21X", "GOA", "EWR", 3520, 545, dest_charges=ewr, **common)
r_bos = RoutePnL("New entrant", "A21X", "GOA", "BOS", 3450, 535, dest_charges=bos, **common)

# 30-week summer programme; different weekly frequency per route.
net = network_pnl([
    AnnualRoutePnL(r_jfk, freq_per_week=4, operating_weeks=30),
    AnnualRoutePnL(r_ewr, freq_per_week=3, operating_weeks=30),
    AnnualRoutePnL(r_bos, freq_per_week=2, operating_weeks=30),
])

write_network_workbook(net, "Network_PnL_Genoa.xlsx",
                       title="Genoa base - summer NYC network (A321XLR)")

from economics_slide import slide_from_network
slide_from_network(net, "Network_PnL_Genoa_slide.pptx",
                   title="Genoa base: summer NYC network economics",
                   subtitle="Annual network P&L, indicative. One A321XLR LCC, three NYC routes, 30-week summer.")

print("Wrote Network_PnL_Genoa.xlsx and Network_PnL_Genoa_slide.pptx")
for o, d, ac, c in net['routes']:
    print(f"  {o}-{d} {ac}: profit {c['annual_profit']:,.0f}  margin {c['margin']:.1%}  "
          f"frames {c['aircraft_required_fractional']:.2f}")
print(f"  NETWORK: profit {net['annual_profit']:,.0f}  margin {net['margin']:.1%}  "
      f"fleet {net['aircraft_required']} aircraft ({net['aircraft_required_fractional']:.2f} frames)")
