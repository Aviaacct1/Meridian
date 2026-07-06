#!/usr/bin/env python3
"""
Avia Solutions - route-specific demand (the repatriable-leakage case).
======================================================================
The calibrated general catchment says GOA wins a small share of ALL trips, because GOA
serves few destinations. That is the wrong question for a NEW route. The right question
for, say, GOA-New York is: how much New-York-bound demand in GOA's catchment leaks to
Milan TODAY (because GOA has no NYC service), and how much would a GOA nonstop repatriate?

Method (same calibrated generalised-cost engine, applied to ONE destination market):
  - Each locale's demand for the market = population x market_propensity (NYC trips/head).
  - Airports compete on access time (calibrated VoT) + a NYC SERVICE benefit per airport
    (service_value: a nonstop is worth more than a one-stop, nothing if the airport has no
    NYC service). attractiveness is neutral here (=1); for one destination the airport's
    general size does not matter, its NYC service does.
  - BASELINE: the home airport has no NYC service -> the market allocates to the competitors
    (mostly the Milan nonstop). SCENARIO: the home airport gains a nonstop (its NYC
    service_value) -> it captures its nearby market on the drive-time advantage.
  - Repatriated = home's market demand in the scenario (was leaking in the baseline).

service_value is the money-equivalent of NYC service quality at each airport; set it from the
QSI of NYC service there (nonstop frequency / connection quality), or by hand for a first cut.
"""
import math
from catchment import Airport, CatchmentParams, run_catchment, addressable_market


def market_allocation(locales, airports, params, propensity, service_values, home,
                      no_service_penalty=1e6):
    """Allocate ONE destination market across airports. service_values = {code: $ NYC benefit}.
    Airports absent from service_values (or the home in the baseline) are treated as offering no
    NYC service (a large generalised-cost penalty). Returns the per-airport market demand."""
    aps = []
    for a in airports:
        sv = service_values.get(a.code)
        penalty = 0.0 if sv is not None else no_service_penalty
        aps.append(Airport(a.code, lat=a.lat, lon=a.lon, fare=a.fare,
                           attractiveness=1.0, service_value=(sv or 0.0) - penalty))
    locs = [type(l)(l.name, l.population, propensity=propensity, business_share=l.business_share,
                    lat=l.lat, lon=l.lon, drive_min=dict(l.drive_min)) for l in locales]
    return run_catchment(locs, aps, params, home=home)


def calibrate_service_values(locales, airports, params, propensity, observed_shares,
                             home=None, iters=120, damp=0.6):
    """Fit each airport's NYC service value (the alternative-specific constant) so the model
    reproduces the OBSERVED NYC O&D split (Sabre). Standard market-share / constants calibration:
    iteratively nudge each constant by (1/logit_scale) x ln(observed/modelled), damped, recentred.
    Returns ({code: service_value}, modelled_shares). This makes the BASELINE match reality, so
    the home nonstop's repatriation is then bounded by its real catchment, not by guesswork."""
    codes = [a.code for a in airports]
    obs = {c: float(observed_shares.get(c, 0.0)) for c in codes}
    s = sum(obs.values()) or 1.0
    obs = {c: v / s for c, v in obs.items()}
    ls = max(params.logit_scale, 1e-6)
    sv = {c: 0.0 for c in codes}
    mod = {}
    for _ in range(iters):
        res = market_allocation(locales, airports, params, propensity, sv, home=home)
        tot = res['total_demand'] or 1.0
        mod = {c: res['catchment'][c] / tot for c in codes}
        for c in codes:
            if obs[c] > 0 and mod[c] > 0:
                sv[c] += damp * (1.0 / ls) * math.log(obs[c] / mod[c])
            elif obs[c] <= 0:
                sv[c] -= damp * 40.0            # no real service -> push the constant down
        m = sum(sv.values()) / len(sv)          # recentre to stop drift
        sv = {c: sv[c] - m for c in codes}
    return sv, mod


def bounded_repatriation(natural_home, current_home, capture=0.65):
    """The DEFENSIBLE repatriation: a home nonstop wins back demand from its OWN catchment that
    currently leaks, not from the whole region. Bounded by the home's natural (nearest-airport)
    market. natural_home = home's nearest-airport demand for the destination; current_home = what
    the home already carries; capture = share of the leaked own-catchment a nonstop wins (the rest
    stay with the incumbent gateway for frequency / onward connections). Avoids the free-running
    logit scenario over-reaching beyond the catchment."""
    pool = max(natural_home - current_home, 0.0)          # own-catchment demand leaking today
    repat = pool * capture
    return {'natural': natural_home, 'current': current_home, 'leaked_pool': pool,
            'capture': capture, 'repatriated': repat, 'home_total': current_home + repat}


def repatriation(locales, airports, params, propensity, service_values, home):
    """Baseline (home has no NYC service) vs scenario (home gains its NYC service): the
    home airport's repatriated market demand and the resulting addressable market."""
    base_sv = {k: v for k, v in service_values.items() if k != home}     # home: no service
    base = market_allocation(locales, airports, params, propensity, base_sv, home)
    scen = market_allocation(locales, airports, params, propensity, service_values, home)
    base_home = base['catchment'][home]
    scen_home = scen['catchment'][home]
    addr = addressable_market(scen, home)
    return {
        'market_demand_total': scen['total_demand'],
        'home': home,
        'baseline_home': base_home,                 # home's NYC demand today (no service)
        'scenario_home': scen_home,                 # home's NYC demand with a nonstop
        'repatriated': scen_home - base_home,       # demand a nonstop wins back from competitors
        'baseline_split': base['catchment'],
        'scenario_split': scen['catchment'],
        'addressable': addr,
        'leak_to_in_baseline': {c: base['catchment'][c] for c in base['catchment'] if c != home},
    }
