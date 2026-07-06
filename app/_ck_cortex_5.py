#!/usr/bin/env python3
"""
Avia Cortex - Route Forecasting: local web app (working prototype).
===================================================================
A small FastAPI server that drives the REAL QSI / catchment / economics engines and
serves the Avia Cortex dashboard. Loads the Genoa case once at startup (catchment +
calibrated parameters + OSRM drive times + the Sabre-derived demand), then each request
re-runs the fast engine (bounded repatriation -> implied load factor -> route P&L) for
the inputs the user sets. The slow, data-heavy prep (Sabre point-of-origin) is read from
genoa_nyc_case.json, so the app needs neither the 15 GB store nor internet at run time.

RUN (on your machine):
    cd "C:\\Users\\Carte\\OneDrive\\Documents\\Claude\\Projects\\Avia QSI Tool\\app"
    py -3.12 -m pip install fastapi uvicorn
    py -3.12 -m uvicorn cortex_app:app --port 8000
    # then open http://localhost:8000

First, generate the case once (so the Sabre-derived demand is baked in):
    py -3.12 genoa_nyc.py cities5000.txt --sabre "C:\\Avia\\sabre.duckdb" --bus-fare 750
"""
import json, os, sys, math
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import geonames as G, routing as R, catchment as C, route_demand as RD

DUMP = os.path.join(HERE, "cities5000.txt")
CACHE = os.path.join(HERE, "genoa_drive.json")
PARAMS = os.path.join(HERE, "genoa_catchment_params.json")
CASE = os.path.join(HERE, "genoa_nyc_case.json")
OBS_CACHE = os.path.join(HERE, "cases", "genoa_nyc_observed.json")
DASH = os.path.join(HERE, "cortex_dashboard.html")


def _latest_served_index():
    """The most recent served_*.json (OAG served index) in the app folder, or None."""
    import glob
    files = sorted(glob.glob(os.path.join(HERE, "served_*.json")))
    return files[-1] if files else None

CENTRE = (44.4133, 8.8375)
COORD = {"GOA": (44.4133, 8.8375), "MXP": (45.6306, 8.7281), "LIN": (45.4451, 9.2767),
         "BGY": (45.6739, 9.7042), "TRN": (45.2008, 7.6497), "BLQ": (44.5354, 11.2887)}
NAMES = {"GOA": "Genoa", "MXP": "Milan MXP", "LIN": "Milan Linate",
         "BGY": "Bergamo", "TRN": "Turin", "BLQ": "Bologna"}
# fallbacks if genoa_nyc_case.json is not present yet (from John's validated run)
FALLBACK = {"propensity": 0.0283, "natural": 92542, "current": 7036,
            "observed_split": {"MXP": 433668, "LIN": 55167, "BLQ": 44038,
                               "TRN": 12476, "GOA": 7036, "BGY": 939}}
DIST_NM, BLOCK_MIN = 3500, 540

app = FastAPI(title="Avia Cortex - Route Forecasting")
S = {}


@app.on_event("startup")
def _load():
    fit = json.load(open(PARAMS)) if os.path.exists(PARAMS) else {"logit_scale": 0.008, "value_of_time_per_hr": 60.0}
    locs = G.near_point(DUMP, CENTRE[0], CENTRE[1], 220, countries=["IT", "FR"], min_pop=5000, propensity=1.0)
    R.load_drive_time_matrix(locs, CACHE)
    airports = [C.Airport(c, lat=la, lon=lo) for c, (la, lo) in COORD.items()]
    params = C.CatchmentParams(method="gencost", logit_scale=fit["logit_scale"],
                               value_of_time_per_hr=fit["value_of_time_per_hr"])
    case = json.load(open(CASE)) if os.path.exists(CASE) else FALLBACK
    observed = case.get("observed_split", FALLBACK["observed_split"])
    propensity = case.get("propensity", FALLBACK["propensity"])
    natural = case.get("natural", FALLBACK["natural"])
    current = case.get("current", FALLBACK["current"])
    sv, _ = RD.calibrate_service_values(locs, airports, params, propensity, observed)
    tot_obs = sum(observed.values()) or 1.0
    S.update(locs=locs, airports=airports, params=params, sv=sv, propensity=propensity,
             natural=natural, current=current,
             observed_share={c: observed.get(c, 0) / tot_obs for c in COORD},
             pop=sum(l.population for l in locs))
    S["served_index"] = _latest_served_index()
    print(f"[cortex] loaded {len(locs)} locales, propensity {propensity:.4f}, natural {natural:,.0f}")
    print(f"[cortex] served index: {S['served_index'] or 'none (run validate_task_one.py / build a served_*.json)'}")


@app.get("/", response_class=HTMLResponse)
def home():
    if os.path.exists(DASH):
        return open(DASH, encoding="utf-8").read()
    return "<h1>Avia Cortex</h1><p>cortex_dashboard.html not found.</p>"


@app.get("/api/assess")
def assess(capture: float = 0.65, freq: int = 7, econ_fare: float = 345.0,
           bus_fare: float = 750.0, aircraft: str = "A21X", econ_share: float = 0.90,
           plan_lf: float = 0.85, incentive: bool = False):
    b = RD.bounded_repatriation(S["natural"], S["current"], capture=capture)
    each_way = b["home_total"]
    out = {
        "inputs": dict(capture=capture, freq=freq, econ_fare=econ_fare, bus_fare=bus_fare,
                       aircraft=aircraft, plan_lf=plan_lf, incentive=incentive),
        "catchment": {"population": S["pop"], "observed_share": S["observed_share"],
                      "names": NAMES},
        "demand": {"natural": S["natural"], "current": S["current"],
                   "leaked": b["leaked_pool"], "repatriated": b["repatriated"],
                   "directional": each_way, "propensity": S["propensity"]},
    }
    try:
        from aircraft_economics import AIRCRAFT, RoutePnL, AnnualRoutePnL, Incentive
        ac = AIRCRAFT[aircraft]
        e_yr = ac["econ_seats"] * freq * 52
        b_yr = ac["bus_seats"] * freq * 52
        e_lf = (each_way * econ_share) / e_yr if e_yr else 0
        b_lf = (each_way * (1 - econ_share)) / b_yr if b_yr else 0
        served = min(e_lf, plan_lf) * e_yr + min(b_lf, plan_lf) * b_yr
        spilled = max(each_way - served, 0.0)
        e_lf, b_lf = min(e_lf, plan_lf), min(b_lf, plan_lf)
        inc = Incentive(home="GOA", waiver_pct=0.50, support_per_turn=1500) if incentive else None
        rp = RoutePnL("New entrant", aircraft, "GOA", "JFK", DIST_NM, BLOCK_MIN,
                      econ_lf=e_lf, bus_lf=b_lf, econ_fare_ow=econ_fare, bus_fare_ow=bus_fare,
                      airspace={"Italy": 0.10, "France": 0.05, "US": 0.05},
                      airline_type="LCC", aircraft_age=2, incentive=inc)
        y = rp.compute()
        annual = AnnualRoutePnL(rp, freq, 52).compute()
        pk = "annual_profit" if "annual_profit" in annual else "profit"
        out["economics"] = {
            "implied_econ_lf": (each_way * econ_share) / e_yr if e_yr else 0,
            "econ_lf": e_lf, "bus_lf": b_lf, "spilled": spilled,
            "revenue": y["gross_rev"], "fuel": y["fuel"], "maintenance": y["maintenance"],
            "crew": y["crew"], "ownership": y["ownership"] + y["insurance"],
            "airport_nav_other": y["landing"] + y["per_pax"] + y["handling"] + y["nav"] + y["catering"] + y["admin"] + y["sales"],
            "total_cost": y["total_cost"], "profit": y["profit"], "margin": y["margin"],
            "breakeven_lf": y["breakeven_lf"], "annual_profit": annual.get(pk, 0),
            "profit_with_incentive": y.get("profit_with_incentive"),
            "seats": ac["econ_seats"] + ac["bus_seats"]}
        out["economics_ok"] = True
    except Exception as e:
        out["economics_ok"] = False
        out["economics_error"] = str(e)
    return JSONResponse(out)


@app.get("/api/route")
def api_route(origin: str, dest: str, capture: float = 0.30, freq: int = 7,
              econ_fare: float = 345.0, bus_fare: float = 1400.0, aircraft: str = "A21X",
              econ_share: float = 0.80, plan_lf: float = 0.85, fuel_price: float = 0.90):
    """The GENERAL path: enter ANY two cities and drive route_engine.assess. Genoa-New York uses
    its calibration cache + observed Sabre split (validated); any other pair is a first-cut
    ESTIMATE (transferred parameters, gravity propensity). Capture defaults to a prior; the
    OAG-QSI capture is parked as experimental until rebuilt at service level."""
    import route_engine as RE
    o = (origin or "").strip().lower()
    is_genoa = o in ("genoa", "genova", "goa")
    kw = {}
    if is_genoa:
        if os.path.exists(OBS_CACHE):
            kw["observed_cache"] = OBS_CACHE
        if os.path.exists(CACHE):
            kw["drive_cache"] = CACHE
    try:
        r = RE.assess(origin, dest, served_index=S.get("served_index"), capture=capture, freq=freq,
                      econ_fare=econ_fare, bus_fare=bus_fare, aircraft=aircraft,
                      econ_share=econ_share, plan_lf=plan_lf, fuel_price=fuel_price, **kw)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=200)
    nat = r["natural_catchment_demand"]; cur = r["current_home_demand"]
    payload = {
        "ok": True,
        "title": f"{r['origin']['city']} → {r['dest']['city']}",
        "origin": r["origin"], "dest": r["dest"],
        "fidelity": r.get("fidelity"), "capture": r.get("capture"),
        "capture_basis": r.get("capture_basis"),
        "catchment": {"population": r["catchment_population"],
                      "observed_share": r.get("airport_share", {}),
                      "names": r.get("airport_names", {}), "home": r["origin"]["iata"]},
        "demand": {"natural": nat, "current": cur, "leaked": max(nat - cur, 0.0),
                   "repatriated": r["repatriated"], "directional": r["directional_demand"],
                   "propensity": r["propensity"], "propensity_basis": r.get("propensity_basis"),
                   "propensity_crosscheck": r.get("propensity_crosscheck")},
        "economics_ok": r.get("economics_ok", False),
    }
    if r.get("economics_ok"):
        payload["economics"] = r["economics"]
    else:
        payload["economics_error"] = r.get("economics_error")
    return JSONResponse(payload)
