#!/usr/bin/env python3
"""
Avia Solutions - Catchment apportionment & leakage engine (Stage 1).
==============================================================================
Apportions a region's air demand across competing airports, the generic Avia
catchment method (Istanbul 2011 demo template; TPA/Bristol/Gatwick leakage studies):

  Each LOCALE (district / postcode with population x propensity-to-fly = demand) is
  allocated across candidate AIRPORTS by accessibility. Two modes:

  1) 'drivetime'  - the transparent default (the Istanbul template): each locale goes to
     its nearest airport by drive time; locales within a CONTESTED BAND of the nearest
     (e.g. 15 min) are split among the airports inside that band. Needs only drive times
     and population.

  2) 'gencost'    - the fuller generalised-cost model (TPA "value of time vs total trip
     cost"): generalised cost(locale, airport) = surface access cost + value_of_time x
     access time + airfare. Demand is shared by a logit on generalised cost, so fares,
     frequency and destinations pull traffic, not distance alone.

Outputs: catchment demand per airport, the LEAKAGE matrix (each airport's natural -
nearest - catchment vs where its demand actually goes), and the REPATRIABLE demand a
new/improved service at a 'home' airport could win back from competitors.

Drive times come from an uploaded matrix, else are estimated from lat/lon (great-circle
x road factor / average speed) for an offline default. POC principle: every input
(drive times, population, propensity, value of time, surface cost, fares) is overridable.
"""
import math
from dataclasses import dataclass, field
from typing import Dict, Optional, List


# ----------------------------------------------------------------- data classes
@dataclass
class Airport:
    code: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    fare: float = 0.0            # representative airfare/total trip cost (gencost mode)
    attractiveness: float = 1.0  # destination-availability size term (gencost share multiplier)
    service_value: float = 0.0   # frequency/service benefit, $ equivalent SUBTRACTED from gen. cost


@dataclass
class Locale:
    name: str
    population: float
    propensity: float = 1.0                      # trips per head (or any demand scalar)
    business_share: float = 0.30                 # fraction of this locale's demand that is business
    lat: Optional[float] = None
    lon: Optional[float] = None
    drive_min: Dict[str, float] = field(default_factory=dict)   # {airport_code: minutes}

    @property
    def demand(self) -> float:
        return self.population * self.propensity

    def demand_by_purpose(self) -> Dict[str, float]:
        return {'business': self.demand * self.business_share,
                'leisure': self.demand * (1.0 - self.business_share)}


@dataclass
class CatchmentParams:
    method: str = "drivetime"            # 'drivetime' or 'gencost'
    contested_band_min: float = 15.0     # drivetime: split locales within this of the nearest
    value_of_time_per_hr: float = 30.0   # gencost: $/hour of access time (used when not segmenting)
    # gencost, segmented: business values time far higher than leisure (the key literature finding)
    vot_by_purpose: Dict[str, float] = field(
        default_factory=lambda: {'business': 60.0, 'leisure': 20.0})
    surface_cost_per_km: float = 0.30    # gencost: $/km surface access (fuel+wear)
    avg_speed_kmh: float = 80.0          # lat/lon -> drive-time proxy
    road_factor: float = 1.30            # great-circle -> road distance multiplier
    logit_scale: float = 0.01            # gencost: larger = sharper (more winner-take-most)
    att_exponent: float = 1.0            # gencost: size-pull dampening (1 raw, 0.5 sqrt, 0 equal) - calibrated
    # water boundary (Jessica, 3 Jul 2026: STT pulled Puerto Rico, IBZ the mainland): when the
    # drive time is ESTIMATED from lat/lon, a locale whose straight line to the airport crosses
    # more than this much contiguous open water is unreachable by road and excluded. 20 km lets
    # bridge/tunnel crossings (Oresund, Storebaelt) and estuaries through; true island-to-island
    # separations are cut. Uploaded drive-time matrices are never second-guessed. Set None = off.
    max_water_gap_km: Optional[float] = 20.0


# ----------------------------------------------------------------- helpers
def great_circle_km(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def _access_km(loc: Locale, ap: Airport, p: CatchmentParams) -> Optional[float]:
    if None not in (loc.lat, loc.lon, ap.lat, ap.lon):
        return great_circle_km(loc.lat, loc.lon, ap.lat, ap.lon) * p.road_factor
    dm = loc.drive_min.get(ap.code)
    return (dm / 60.0) * p.avg_speed_kmh if dm is not None else None


def _drive_min(loc: Locale, ap: Airport, p: CatchmentParams) -> Optional[float]:
    if ap.code in loc.drive_min:
        return loc.drive_min[ap.code]        # a real matrix knows about roads/bridges/ferries
    # estimated from lat/lon: check the pair doesn't drive across open water (island airports)
    if p.max_water_gap_km is not None and None not in (loc.lat, loc.lon, ap.lat, ap.lon):
        try:
            from water_check import road_reachable
            if not road_reachable(loc.lat, loc.lon, ap.lat, ap.lon, p.max_water_gap_km):
                return None
        except Exception:
            pass                             # fail open: behave exactly as before
    km = _access_km(loc, ap, p)
    return (km / p.avg_speed_kmh) * 60.0 if km is not None else None


# ----------------------------------------------------------------- allocation
def allocate_locale(loc: Locale, airports: List[Airport], p: CatchmentParams,
                    vot: float = None) -> Dict[str, float]:
    """Return {airport_code: share} for one locale (shares sum to ~1).
    vot overrides the value of time (used to score a business or leisure segment)."""
    times = {a.code: _drive_min(loc, a, p) for a in airports}
    times = {k: v for k, v in times.items() if v is not None}
    if not times:
        return {}
    if p.method == "drivetime":
        d_min = min(times.values())
        contested = {c: t for c, t in times.items() if t <= d_min + p.contested_band_min}
        # split within the contested band, weighted by inverse drive time (nearer = more)
        w = {c: 1.0 / max(t, 1.0) for c, t in contested.items()}
        s = sum(w.values())
        return {c: w[c] / s for c in w}
    # gencost: generalised cost = surface cost + VoT x time + fare; share by a SIZE-weighted
    # logit (attractiveness = frequency/destinations pull, scales the share linearly, not the cost)
    value_of_time = p.value_of_time_per_hr if vot is None else vot
    by = {a.code: a for a in airports}
    cost = {}
    for c, t in times.items():
        km = _access_km(loc, by[c], p) or (t / 60.0 * p.avg_speed_kmh)
        # generalised cost = surface access cost + VoT x access time + fare - service benefit
        # (frequency/destinations as an equivalent money saving); this is the Avia three-factor model
        cost[c] = (p.surface_cost_per_km * km + value_of_time * (t / 60.0)
                   + by[c].fare - by[c].service_value)
    cmin = min(cost.values())
    ex = {c: max(by[c].attractiveness, 1e-6) ** p.att_exponent * math.exp(-p.logit_scale * (gc - cmin))
          for c, gc in cost.items()}
    s = sum(ex.values())
    return {c: ex[c] / s for c in ex}


def run_catchment(locales: List[Locale], airports: List[Airport],
                  params: CatchmentParams = None, home: str = None,
                  segment: bool = False) -> dict:
    """Allocate every locale; return per-airport catchment demand, the leakage matrix and
    (if home given) the demand leaking from home's natural catchment to each competitor.

    segment=True (gencost only): allocate BUSINESS and LEISURE separately, each with its own
    value of time (business values access time/frequency far higher, fare lower), then sum -
    the segmentation the airport-choice literature says carries the accuracy. Per-purpose
    catchment is returned under 'by_purpose'."""
    p = params or CatchmentParams()
    codes = [a.code for a in airports]
    catchment = {c: 0.0 for c in codes}
    natural = {c: 0.0 for c in codes}                  # demand whose NEAREST airport is c
    leak = {c: {d: 0.0 for d in codes} for c in codes}  # natural[c] -> allocated to d
    if segment and p.method == "gencost":
        segs = [(pp, (lambda loc, pp=pp: loc.demand_by_purpose()[pp]), p.vot_by_purpose[pp])
                for pp in ('business', 'leisure')]
    else:
        segs = [('all', (lambda loc: loc.demand), p.value_of_time_per_hr)]
    by_purpose = {pp: {c: 0.0 for c in codes} for pp, _, _ in segs}
    rows = []
    for loc in locales:
        valid = [a.code for a in airports if _drive_min(loc, a, p) is not None]
        if not valid:
            continue
        nearest = min(valid, key=lambda c: _drive_min(
            loc, next(a for a in airports if a.code == c), p))
        loc_shares = {}
        for pp, demand_fn, vot in segs:
            shares = allocate_locale(loc, airports, p, vot=vot)
            d = demand_fn(loc)
            for c, sh in shares.items():
                catchment[c] += d * sh
                by_purpose[pp][c] += d * sh
                leak[nearest][c] += d * sh
            loc_shares[pp] = {c: round(sh, 3) for c, sh in shares.items()}
        natural[nearest] += loc.demand
        rows.append({'locale': loc.name, 'demand': loc.demand, 'nearest': nearest, 'shares': loc_shares})
    out = {'catchment': catchment, 'natural': natural, 'leakage_matrix': leak,
           'by_purpose': (by_purpose if segment else None), 'locales': rows,
           'total_demand': sum(l.demand for l in locales), 'segmented': bool(segment)}
    if home:
        leaked = {d: leak[home][d] for d in codes if d != home}
        out.update(home=home, home_natural=natural[home], home_retained=leak[home][home],
                   home_leaked=sum(leaked.values()), home_leak_to=leaked,
                   home_repatriable=sum(leaked.values()))
    return out


def tier_split(locales: List[Locale], airports: List[Airport], home: str,
               params: CatchmentParams = None, contested_band: float = 20.0, primary_max: float = 60.0):
    """Split the demand HOME captures from its catchment into Primary / Secondary / Contested tiers,
    each further into business / leisure. Per John's definition: Primary is uncontested and within
    primary_max drive minutes (the airport is the obvious choice); Secondary is uncontested but beyond
    primary_max, out to the catchment edge; Contested is where a competing airport sits at a similar
    drive time (within contested_band, i.e. the overlap zone). Returns {tier: {'business','leisure'}}
    of demand allocated to HOME, or None if HOME is not among the airports."""
    p = params or CatchmentParams()
    home_ap = next((a for a in airports if a.code == home), None)
    if home_ap is None:
        return None
    out = {t: {'business': 0.0, 'leisure': 0.0} for t in ('primary', 'secondary', 'contested')}
    for loc in locales:
        t_home = _drive_min(loc, home_ap, p)
        if t_home is None:
            continue
        comp = [_drive_min(loc, a, p) for a in airports if a.code != home]
        comp = [x for x in comp if x is not None]
        nearest = min(comp) if comp else None
        if nearest is not None and nearest <= t_home + contested_band:
            tier = 'contested'
        elif t_home <= primary_max:
            tier = 'primary'
        else:
            tier = 'secondary'
        d_home = loc.demand * allocate_locale(loc, airports, p).get(home, 0.0)
        bs = getattr(loc, 'business_share', 0.30)
        out[tier]['business'] += d_home * bs
        out[tier]['leisure'] += d_home * (1.0 - bs)
    return out


def calibrate(locales: List[Locale], airports: List[Airport], observed_shares: Dict[str, float],
              params: CatchmentParams = None, segment: bool = False, grids: dict = None) -> dict:
    """Fit the model to an OBSERVED multi-airport split (CAA Passenger Survey or Sabre point-of-
    origin): grid-search the logit scale and a value-of-time multiplier to minimise the squared
    error between modelled and observed airport shares. Validate-then-improve made operational.
    observed_shares = {airport_code: share or volume}. Returns best params, fit (SSE) and shares.
    No scipy dependency (grid search)."""
    import copy
    base = params or CatchmentParams()
    base = copy.copy(base); base.method = "gencost"   # calibration only for the gencost model
    obs = {c: float(observed_shares.get(c, 0.0)) for c in [a.code for a in airports]}
    s_obs = sum(obs.values()) or 1.0
    obs = {c: v / s_obs for c, v in obs.items()}
    g = grids or {}
    scales = g.get('logit_scale', [0.002, 0.004, 0.006, 0.008, 0.01, 0.015, 0.02, 0.03, 0.05])
    vmults = g.get('vot_mult', [0.5, 0.75, 1.0, 1.25, 1.5, 2.0])
    # att_exponent dampens the airport-size pull (raw size swamps access time at exponent 1);
    # the real Genoa run showed this is the decisive lever, so calibrate it too.
    exps = g.get('att_exponent', [0.0, 0.25, 0.5, 0.75, 1.0])
    best = None
    for sc in scales:
        for vm in vmults:
            for ae in exps:
                p = copy.copy(base)
                p.logit_scale = sc
                p.att_exponent = ae
                p.value_of_time_per_hr = base.value_of_time_per_hr * vm
                p.vot_by_purpose = {k: v * vm for k, v in base.vot_by_purpose.items()}
                res = run_catchment(locales, airports, p, segment=segment)
                tot = res['total_demand'] or 1.0
                mod = {c: res['catchment'][c] / tot for c in obs}
                sse = sum((mod[c] - obs[c]) ** 2 for c in obs)
                if best is None or sse < best['sse']:
                    best = {'sse': sse, 'logit_scale': sc, 'vot_mult': vm, 'att_exponent': ae,
                            'params': p,
                            'modelled': {c: round(m, 4) for c, m in mod.items()},
                            'observed': {c: round(o, 4) for c, o in obs.items()}}
    return best


# ---------------------------------------------------- bridge to the demand chain
def addressable_market(result: dict, home: str) -> dict:
    """Turn a catchment run into a ROUTE's addressable market, for the demand forecast.

    Run run_catchment with each locale's propensity set to the DESTINATION's trips-per-head
    (so 'demand' is the destination's air demand, not all-purpose travel). Then for the home
    airport this returns:
      own         - destination demand from home's catchment the model gives home today
      repatriable - destination demand from home's catchment now using competitor airports
                    (the leakage a home nonstop could win back)
      addressable - own + repatriable = the whole market a home service can address
    """
    own = result.get('home_retained', 0.0)
    repatriable = result.get('home_leaked', 0.0)
    return {'home': home, 'own': own, 'repatriable': repatriable,
            'addressable': result.get('home_natural', own + repatriable),
            'leak_to': result.get('home_leak_to', {})}


def forecast_from_addressable(addr: dict, capture: float, stimulation: float = 1.0,
                              recapture_share: float = 1.0) -> dict:
    """First-cut booked-demand from the addressable market: a home nonstop holds its own
    catchment demand and wins `capture` x `recapture_share` of the repatriable leakage, with a
    `stimulation` uplift (new nonstop convenience grows the market). The downstream load-factor /
    capacity convergence (the operating model) then refines this to booked passengers."""
    base = addr['own'] + addr['repatriable'] * capture * recapture_share
    forecast = base * stimulation
    return {'addressable': addr['addressable'], 'own_retained': addr['own'],
            'repatriated': addr['repatriable'] * capture * recapture_share,
            'capture': capture, 'stimulation': stimulation,
            'forecast_pax': forecast}


# ---------------------------------------------------- optional overlays / providers
def apply_observed_overlay(result: dict, observed: Dict[str, float], weight: float = 1.0) -> Dict[str, float]:
    """Blend the modelled catchment with an OBSERVED origin distribution (mobile cell data,
    CAA Passenger Survey, or Sabre point-of-origin). weight 1.0 fully trusts the observed split,
    0.0 keeps the model, in between pulls the model toward the evidence. Rescaled to the model's
    total demand. This is the cell-data refinement: an optional overlay, never a requirement."""
    codes = list(result['catchment'])
    total = sum(result['catchment'].values())
    obs = {c: float(observed.get(c, 0.0)) for c in codes}
    s = sum(obs.values()) or 1.0
    obs_demand = {c: total * obs[c] / s for c in codes}
    return {c: (1 - weight) * result['catchment'][c] + weight * obs_demand[c] for c in codes}


def drive_times_from_provider(locales: List[Locale], airports: List[Airport], provider) -> List[Locale]:
    """Populate each locale's drive_min via a pluggable PROVIDER callable
    provider(loc_lat, loc_lon, ap_lat, ap_lon) -> minutes, e.g. a Google/OSRM/Valhalla isochrone
    service when online. The offline default (no provider) is the lat/lon great-circle proxy."""
    for loc in locales:
        if loc.lat is None or loc.lon is None:
            continue
        for ap in airports:
            if ap.lat is not None and ap.lon is not None:
                loc.drive_min[ap.code] = provider(loc.lat, loc.lon, ap.lat, ap.lon)
    return locales
