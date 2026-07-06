#!/usr/bin/env python3
"""
Avia Solutions - integrated route assessment (the catchment-to-profit chain).
==============================================================================
One call runs the whole tool as a chain for a proposed route:

  catchment (who lives near the airport x destination trip-rate)
    -> addressable market + leakage (catchment.py)
    -> QSI capture of a home nonstop (run_multihub_qsi / qsi_market - supplied as `capture`)
    -> booked-pax forecast (x stimulation, recapture of leakage)
    -> implied load factor for a proposed aircraft + frequency
    -> route P&L and annual / fleet economics (aircraft_economics.py)

The QSI `capture` is passed in (computed by the store-driven multi-hub QSI run); everything
else is wired here. economics = the RoutePnL constructor kwargs (airline, origin, dest,
distance_nm, block_min_oneway, fares, airline_type, aircraft_age, charges, incentive...);
this orchestrator fills in the aircraft and the load factors from the demand forecast.
"""
from catchment import run_catchment, addressable_market, forecast_from_addressable


def assess_route(locales, airports, home, capture, *,
                 aircraft=None, frequency_per_week=None, operating_weeks=52.0,
                 stimulation=1.15, recapture_share=1.0,
                 catchment_params=None, segment=True, economics=None):
    """Run catchment -> addressable -> forecast, and (if aircraft + frequency + economics given)
    the implied load factor and the route/annual P&L. Returns the full chain in one dict."""
    res = run_catchment(locales, airports, catchment_params, home=home, segment=segment)
    addr = addressable_market(res, home)
    fc = forecast_from_addressable(addr, capture, stimulation, recapture_share)
    out = {'catchment': res['catchment'], 'addressable': addr, 'forecast': fc}

    if aircraft and frequency_per_week and economics is not None:
        from aircraft_economics import AIRCRAFT, RoutePnL, AnnualRoutePnL
        ac = AIRCRAFT[aircraft]
        seats = ac['econ_seats'] + ac['bus_seats']
        annual_seats = seats * frequency_per_week * operating_weeks * 2   # both directions
        implied_lf = (fc['forecast_pax'] / annual_seats) if annual_seats else 0.0
        out['annual_seats'] = annual_seats
        out['implied_load_factor'] = implied_lf
        # route P&L at the implied load factor (one LF for both cabins here; refine per cabin later)
        rp = RoutePnL(aircraft=aircraft, econ_lf=implied_lf, bus_lf=implied_lf, **economics)
        out['route_pnl'] = rp.compute()
        out['annual_pnl'] = AnnualRoutePnL(rp, frequency_per_week, operating_weeks).compute()
        out['route_pnl_obj'] = rp
    return out
