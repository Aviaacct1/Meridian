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
import json, os, sys, math, hashlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse

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
CATCH = os.path.join(HERE, "cortex_catchment.html")
HELP = os.path.join(HERE, "cortex_help.html")
ECON = os.path.join(HERE, "cortex_economics.html")


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

# ---------------------------------------------------------------- password gate
# A shared-password login in front of everything, so the tunnelled site is private. Set the password
# with the AVIA_PASSWORD environment variable; the cookie token is derived from it, so changing the
# password logs everyone out. This is belt-and-braces alongside Cloudflare Access at the edge.
APP_PASSWORD = os.environ.get("AVIA_PASSWORD", "aviacortex2026")
_AUTH_TOKEN = hashlib.sha256(("cortex-session::" + APP_PASSWORD).encode()).hexdigest()[:40]
LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Avia Cortex</title><style>
body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;background:#0E1B33;
font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.box{background:#fff;border-radius:14px;padding:34px 32px;width:340px;box-shadow:0 10px 40px rgba(0,0,0,.35)}
.mark{width:40px;height:40px;border-radius:10px;background:linear-gradient(135deg,#2F6BF0,#5C8DF6);display:flex;
align-items:center;justify-content:center;margin-bottom:16px}
h1{font-size:18px;color:#16324F;margin:0 0 2px}p{font-size:13px;color:#6B7A85;margin:0 0 20px}
input{width:100%;box-sizing:border-box;padding:11px 13px;border:1px solid #E6EBF2;border-radius:9px;font-size:14px;margin-bottom:12px}
button{width:100%;padding:11px;background:#2F6BF0;color:#fff;border:none;border-radius:9px;font-weight:600;font-size:14px;cursor:pointer}
.err{color:#D84C4C;font-size:12.5px;margin-bottom:10px;font-weight:600}</style></head>
<body><form class="box" method="post" action="/login">
<div class="mark"><svg viewBox="0 0 24 24" width="22" height="22" fill="none"><path d="M3 12c4 0 5-7 9-7s5 14 9 7" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/></svg></div>
<h1>Avia Cortex</h1><p>Route Forecasting &middot; private preview</p>{{ERR}}
<input type="password" name="password" placeholder="Password" autofocus autocomplete="current-password">
<button type="submit">Enter</button></form></body></html>"""


@app.middleware("http")
async def _auth_gate(request: Request, call_next):
    path = request.url.path
    if path in ("/login", "/logout", "/favicon.ico") or request.cookies.get("cortex_auth") == _AUTH_TOKEN:
        return await call_next(request)
    if path.startswith("/api/"):
        return JSONResponse({"ok": False, "error": "unauthorised - please log in"}, status_code=401)
    return RedirectResponse("/login")


@app.get("/login", response_class=HTMLResponse)
def _login_form(bad: int = 0):
    return LOGIN_HTML.replace("{{ERR}}", '<div class="err">Wrong password.</div>' if bad else "")


@app.post("/login")
async def _login_submit(request: Request):
    from urllib.parse import parse_qs
    body = (await request.body()).decode("utf-8", "ignore")
    pw = parse_qs(body).get("password", [""])[0]
    if pw.strip() == APP_PASSWORD.strip():
        resp = RedirectResponse("/", status_code=303)
        resp.set_cookie("cortex_auth", _AUTH_TOKEN, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 14)
        return resp
    return RedirectResponse("/login?bad=1", status_code=303)


@app.get("/logout")
def _logout():
    resp = RedirectResponse("/login")
    resp.delete_cookie("cortex_auth")
    return resp


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


# ============================================================================
# CALIBRATED LIVE ENGINE
# Drives route_forecast.forecast (this session's back-tested engine: the country
# COVERAGE gross-up, the alliance-weighted CONNECTING FEED, the att size-pull, the
# capacity cap) for ANY city pair, reusing route_engine's city -> airport / metro /
# served-week resolution. /api/forecast is what makes the portal show the VALIDATED
# number, not the older route_engine.assess demand model.
# ============================================================================
STIM_BY_TYPE = {"FSC": 1.15, "LCC": 1.35, "ULCC": 1.80, "REGIONAL": 1.15, "CHARTER": 1.80}


def _db_paths():
    return (os.environ.get("AVIA_SABRE", r"C:\Avia\sabre.duckdb"),
            os.environ.get("AVIA_OAG", r"C:\Avia\oag.duckdb"))


def _live_ctx():
    """Latest OAG week + Sabre year + served index, resolved once and cached in S."""
    if "live" in S:
        return S["live"]
    import duckdb, oag_served as OAS
    sabre_db, oag_db = _db_paths()
    week = year = None; served_obj = None
    try:
        c = duckdb.connect(oag_db, read_only=True)
        week = c.execute("SELECT max(week) FROM oag").fetchone()[0]; c.close()
    except Exception:
        pass
    try:
        c = duckdb.connect(sabre_db, read_only=True)
        year = c.execute("SELECT max(source_year) FROM sabre").fetchone()[0]; c.close()
    except Exception:
        pass
    si = _latest_served_index()
    if si:
        try:
            served_obj = OAS.load_index(si)
        except Exception:
            served_obj = None
    served_codes = set()
    if served_obj:
        try:
            served_codes = set(OAS.served_set(served_obj))
        except Exception:
            served_codes = set()
    S["live"] = dict(sabre_db=sabre_db, oag_db=oag_db, week=week, year=year,
                     served=served_obj, served_codes=served_codes)
    return S["live"]


def _econ_block(each_way, aircraft, freq, home, dest_airport, gcd, econ_share, plan_lf,
                econ_fare, bus_fare, fuel_price, carrier_type, weeks=52.0):
    try:
        import route_engine as RE
        from aircraft_economics import AIRCRAFT, RoutePnL, AnnualRoutePnL
        ac = AIRCRAFT[aircraft]
        e_yr = ac["econ_seats"] * freq * weeks; b_yr = ac["bus_seats"] * freq * weeks
        e_lf = min((each_way * econ_share) / e_yr if e_yr else 0, plan_lf)
        b_lf = min((each_way * (1 - econ_share)) / b_yr if b_yr else 0, plan_lf)
        dist_nm = round(gcd / 1.852); bmin = round(RE.block_min(dist_nm))
        fare = econ_fare if (econ_fare and econ_fare > 0) else max(180, round(dist_nm * 0.11))
        at = carrier_type if carrier_type in ("FSC", "LCC", "ULCC") else "LCC"
        fp_used = fuel_price if (fuel_price and fuel_price > 0) else 0.90
        rp = RoutePnL("New entrant", aircraft, home, dest_airport, dist_nm, bmin,
                      econ_lf=e_lf, bus_lf=b_lf, econ_fare_ow=fare, bus_fare_ow=bus_fare,
                      airline_type=at, aircraft_age=2, origin_charges=RE.DEFAULT_CHARGES,
                      dest_charges=RE.DEFAULT_CHARGES, fuel_price_usd_kg=fp_used)
        y = rp.compute(); annual = AnnualRoutePnL(rp, freq, weeks).compute()
        pk = "annual_profit" if "annual_profit" in annual else "profit"
        spilled = max(each_way - (e_lf * e_yr + b_lf * b_yr), 0.0)
        # cost model for the live slider panel: every rate the browser needs to recompute the P&L
        # as fares/fuel/frequency/load-factor/premium sliders move, without another server call.
        _pax = y.get("pax_turn") or 1
        cost_model = {
            "econ_seats": ac["econ_seats"], "bus_seats": ac["bus_seats"],
            "fuel_kg_per_turn": (y["fuel"] / fp_used) if fp_used else 0.0,
            "fixed_per_turn": (y["maintenance"] + y["landing"] + y["nav"] + y["handling"]
                               + y["ownership"] + y["insurance"] + y["crew"]),
            "per_pax_cost": (y["catering"] + y["per_pax"]) / _pax,
            "recovery_per_pax": y["charges_recovery"] / _pax,
            "cargo_rev": y["cargo_rev"],
            "indirect_rate": ((y["admin"] + y["sales"]) / y["net_rev"]) if y.get("net_rev") else 0.10,
            "ref_fuel_price": fp_used, "econ_share": econ_share, "plan_lf": plan_lf,
            "econ_fare": fare, "bus_fare": bus_fare, "freq": freq, "each_way": each_way,
        }
        return {"economics_ok": True, "economics": {
            "econ_fare": fare, "econ_lf": round(e_lf, 3), "bus_lf": round(b_lf, 3), "spilled": round(spilled),
            "seats": ac["econ_seats"] + ac["bus_seats"], "revenue": y["gross_rev"],
            "fuel": y["fuel"], "maintenance": y["maintenance"], "crew": y["crew"],
            "ownership": y["ownership"] + y["insurance"],
            "airport_nav_other": (y["landing"] + y["per_pax"] + y["handling"] + y["nav"]
                                  + y["catering"] + y["admin"] + y["sales"]),
            "total_cost": y["total_cost"], "profit": y["profit"], "margin": y["margin"],
            "breakeven_lf": y["breakeven_lf"], "annual_profit": annual.get(pk, 0),
            "aircraft_required": annual.get("aircraft_required"), "cost_model": cost_model, "raw": y}}
    except Exception as e:
        return {"economics_ok": False, "economics_error": str(e)}


def _schedule_times(o_code, d_code, o, d, block_min, dep_out=11.0, turn_h=2.0):
    """Indicative local dep/arr clock times from block time and an approximate timezone offset (by
    longitude). Illustrative only: not curfew-, slot- or connection-optimised, but gives the schedule
    a sensible shape. Outbound departs the origin late morning; the return turns at the destination."""
    def tz(a):
        try:
            return round((a.get("lon") or 0.0) / 15.0)
        except Exception:
            return 0
    bh = (block_min or 0) / 60.0
    tzo, tzd = tz(o), tz(d)

    def hhmm(x):
        x = x % 24.0
        h = int(x); m = int(round((x - h) * 60.0))
        if m == 60:
            h = (h + 1) % 24; m = 0
        return f"{h:02d}:{m:02d}"

    def leg(dep_local, tz_from, tz_to):
        arr = dep_local + bh + (tz_to - tz_from)
        day = 0
        while arr >= 24:
            arr -= 24; day += 1
        while arr < 0:
            arr += 24; day -= 1
        suffix = "+1" if day == 1 else ("+2" if day >= 2 else ("-1" if day < 0 else ""))
        return hhmm(dep_local), hhmm(arr) + suffix

    do, ao = leg(dep_out, tzo, tzd)
    dep_ret = ((dep_out + bh + (tzd - tzo)) + turn_h) % 24.0
    dr, ar = leg(dep_ret, tzd, tzo)
    return {"outbound": {"sector": f"{o_code}-{d_code}", "dep": do, "arr": ao},
            "inbound": {"sector": f"{d_code}-{o_code}", "dep": dr, "arr": ar},
            "block_min": block_min, "indicative": True}


def calibrated_forecast(origin, dest, airline=None, carrier_type="FSC", aircraft="A21X",
                        freq=7, stimulation=None, growth=0.0, growth_years=0, econ_share=0.85,
                        plan_lf=0.85, econ_fare=None, bus_fare=1400.0, fuel_price=None,
                        radius_km=220.0, with_econ=True, att_exponent=None, catchment_mult=1.0,
                        coverage_override=None, market_override=None, share_override=None,
                        feed_behind_cap=0.10, feed_dom_gain=1.0, feed_dom_floor=1.0,
                        cnx_online=1.0, cnx_alliance=0.615, cnx_interline=0.25,
                        circuity=1.35, factor_indirect=1.044, mct_banking=False, season="annual"):
    """Any city pair through the CALIBRATED engine (route_forecast.forecast). season = annual (default)
    / summer / winter runs a seasonal service: demand scaled to the season's share of the year, capacity
    over the season's weeks."""
    import route_forecast as RF, route_engine as RE, oag_served as OAS
    import geo_resolve as GEO, sabre_catchment as SC
    ctx = _live_ctx()
    if not ctx.get("week") or not ctx.get("year"):
        return {"ok": False, "error": "OAG/Sabre databases not found - set AVIA_OAG / AVIA_SABRE "
                                       "or place them at C:\\Avia."}
    airline = (airline or "").strip().upper() or None
    ct = (carrier_type or "FSC").upper()
    idx = ctx["served"]; served = OAS.served_set(idx) if idx else None
    try:
        om = GEO.resolve_metro(origin, served_index=idx, dump=DUMP, expand=False)
        dm = GEO.resolve_metro(dest, served_index=idx, dump=DUMP, expand=True)
    except Exception as e:
        return {"ok": False, "error": f"could not resolve '{origin}' -> '{dest}': {e}"}
    home = om["primary"]; dest_airport = dm["primary"]; dest_codes = dm["airports"]
    ap = RE._airports(); o = ap.get(home); d = ap.get(dest_airport)
    if not o or not d:
        return {"ok": False, "error": "airport resolution failed for one endpoint"}
    gcd = RE.gc_km(o["lat"], o["lon"], d["lat"], d["lon"])
    bmin = round(RE.block_min(gcd / 1.852))
    competing = [r["iata"] for r in RE.competing_airports(o, radius_km, served, True)]
    stim = stimulation if stimulation is not None else STIM_BY_TYPE.get(ct, 1.15)
    feed_cfg = {"behind_cap": feed_behind_cap, "dom_gain": feed_dom_gain, "dom_floor": feed_dom_floor,
                "cnx_online": cnx_online, "cnx_alliance": cnx_alliance, "cnx_interline": cnx_interline,
                "circuity": circuity, "factor_indirect": factor_indirect, "mct_banking": bool(mct_banking)}
    # SEASONAL: scale annual demand by the season's share (haul + type profile) and run capacity over the
    # season's weeks. season='annual' leaves everything unchanged.
    import seasonality_engine as SE
    _rt = "intra_european" if gcd < 1500 else "transatlantic" if gcd < 6000 else "europe_asia"
    _ds = "leisure" if ct in ("LCC", "ULCC") else "mixed"
    season_share = SE.season_share_for(season, route_type=_rt, demand_split=_ds)
    season_weeks = 28.0 if season == "summer" else 24.0 if season == "winter" else 52.0
    try:
        r = RF.forecast(ctx["sabre_db"], ctx["oag_db"], ctx["week"], home, dest_codes, competing,
                        year=ctx["year"], aircraft=aircraft, freq=freq, block_min=bmin,
                        stimulation=stim, dest_airport=dest_airport, airline=airline,
                        growth=growth, growth_years=growth_years, feed_cfg=feed_cfg,
                        att_exponent=att_exponent, catchment_mult=catchment_mult,
                        coverage_override=coverage_override, market_override=market_override,
                        share_override=share_override, max_plan_lf=plan_lf,
                        market_factor=RF.market_factor_for(carrier_type),   # item-9 type-aware P2P trim
                        season=season, season_share=season_share, season_weeks=season_weeks)
    except Exception as e:
        return {"ok": False, "error": f"forecast failed: {e}"}
    try:
        split, _mkt, _ = SC.destination_market_split(ctx["sabre_db"], competing, dest_codes, year=ctx["year"])
        tot = sum(split.values()) or 1.0
        shares = {c: round(split.get(c, 0.0) / tot, 4) for c in competing}
    except Exception:
        shares = {}
    # label by city, but disambiguate airports that share a city (the London group) with the code
    _by_city = {}
    for c in competing:
        if c in ap:
            _by_city.setdefault(_city_of(ap, c), []).append(c)
    names = {}
    for c in competing:
        if c in ap:
            _city = _city_of(ap, c)
            names[c] = (f"{_city} ({c})" if len(_by_city.get(_city, [])) > 1 else _city)
    def _feed_list(detailmap, pdewmap, top=15):
        dm = detailmap or {}
        if dm:
            rows = sorted(dm.items(), key=lambda kv: -(kv[1].get("captured") or 0))
            out = []
            for c, dd in rows[:top]:
                pv = dd.get("pdew") or 0
                if pv <= 0:
                    continue
                out.append({"code": c,
                            "name": _city_of(ap, c),
                            "country": (ap[c].get("country") if c in ap else ""),
                            "base": round(dd.get("base") or 0), "share": round(dd.get("share") or 0, 4),
                            "forecast": round(dd.get("captured") or 0), "pdew": round(pv, 1)})
            return out
        rows = sorted((pdewmap or {}).items(), key=lambda kv: -kv[1])
        return [{"code": c, "name": (ap[c]["city"] if (c in ap and ap[c].get("city")) else c),
                 "country": (ap[c].get("country") if c in ap else ""), "pdew": v}
                for c, v in rows[:top] if v and v > 0]
    beyond_list = _feed_list(r.get("beyond_detail"), r.get("beyond_pdew"))
    behind_list = _feed_list(r.get("behind_detail"), r.get("behind_pdew"))
    _feed_base = lambda dm: round(sum((v.get("base") or 0) for v in (dm or {}).values()))
    beyond_base = _feed_base(r.get("beyond_detail")); behind_base = _feed_base(r.get("behind_detail"))
    each_way = r["total_demand"]
    out = {
        "ok": True, "title": f'{o["city"]} → {d["city"]}', "engine": "route_forecast (calibrated)",
        "origin": {"iata": home, "city": o["city"], "country": o["country"], "metro": om["airports"]},
        "dest": {"iata": dest_airport, "city": d["city"], "country": d["country"], "metro": dest_codes},
        "airline": airline, "carrier_type": ct,
        "catchment": {"home": home, "observed_share": shares, "names": names},
        "demand": {"natural": r["natural_market"], "current": r["current_via_origin"],
                   "captured": r["captured_demand"], "qsi_share": r["qsi_share"], "dest_share": r["dest_share"],
                   "coverage_gross_up": r["coverage_gross_up"], "premium_share": r["premium_share"],
                   "feed_total": r["connecting_feed"], "feed_beyond": r["feed_beyond"],
                   "feed_behind": r["feed_behind"], "feed_beyond_base": beyond_base, "feed_behind_base": behind_base,
                   "total": each_way, "avg_fare": r["avg_fare"],
                   "att": r.get("att_exponent"), "stimulation": r.get("stimulation"),
                   "pdew_total": round(each_way / 365.0 / 2.0, 1),
                   "beyond_pdew": beyond_list, "behind_pdew": behind_list},
        "capacity": {"carried": r["carried_forecast"], "spill": r["spill"], "load": r["planned_load_factor"],
                     "annual_capacity": r["annual_capacity"], "recommendation": r["recommendation"],
                     "aircraft": aircraft, "freq": freq},
        "season": {"mode": r.get("season", "annual"), "share": r.get("season_share", 1.0),
                   "weeks": round(season_weeks)},
        "schedule": _schedule_times(home, dest_airport, o, d, bmin),
        "distance_nm": round(gcd / 1.852), "block_min": bmin, "week": ctx["week"], "year": ctx["year"],
    }
    if with_econ:
        out.update(_econ_block(each_way, aircraft, freq, home, dest_airport, gcd, econ_share,
                               plan_lf, econ_fare, bus_fare, fuel_price, ct, weeks=season_weeks))
    return out


@app.get("/api/fleet")
def api_fleet(airline: str = "", distance_nm: float = 0.0):
    """The aircraft an airline actually flies (families), optionally range-filtered, for the picker."""
    try:
        import airline_fleets as AF
        from aircraft_economics import AIRCRAFT
        dist_km = (distance_nm * 1.852) if distance_nm and distance_nm > 0 else None
        codes, known = AF.fleet_for(airline, list(AIRCRAFT.keys()), dist_km)
        return JSONResponse({"fleet": sorted(codes), "known": known, "airline": (airline or "").upper()})
    except Exception as e:
        return JSONResponse({"fleet": [], "known": False, "error": str(e)})


@app.get("/api/route_status")
def api_route_status(origin: str = "", dest: str = "", airline: str = ""):
    """Does this origin-destination already operate nonstop today (OAG)? Flag before a full forecast."""
    try:
        import duckdb, geo_resolve as GEO
        ctx = _live_ctx()
        if not ctx.get("week"):
            return JSONResponse({"ok": False, "error": "OAG not available"})
        idx = ctx["served"]
        om = GEO.resolve_metro(origin, served_index=idx, dump=DUMP, expand=False)
        dm = GEO.resolve_metro(dest, served_index=idx, dump=DUMP, expand=True)
        home = om["primary"]; dest_codes = dm["airports"]
        ph = ",".join("?" * len(dest_codes))
        con = duckdb.connect(ctx["oag_db"], read_only=True)
        try:
            rows = con.execute(f"SELECT carrier, COUNT(*) FROM oag WHERE week=? AND dep_airport=? "
                               f"AND arr_airport IN ({ph}) GROUP BY carrier ORDER BY 2 DESC",
                               [ctx["week"], home] + list(dest_codes)).fetchall()
        finally:
            con.close()
        total = sum(int(n or 0) for _, n in rows)
        carriers = [{"carrier": c, "weekly": int(n or 0)} for c, n in rows if c]
        al = (airline or "").strip().upper()
        return JSONResponse({"ok": True, "exists": total > 0, "weekly_flights": total,
                             "carriers": carriers[:6], "origin": home, "dest": dm["primary"],
                             "airline_operates": any(c["carrier"] == al for c in carriers) if al else False})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})


@app.get("/api/forecast")
def api_forecast(origin: str, dest: str, airline: str = "", carrier_type: str = "FSC",
                 aircraft: str = "A21X", freq: int = 7, econ_share: float = 0.85,
                 plan_lf: float = 0.85, econ_fare: float = 0.0, bus_fare: float = 1400.0,
                 fuel_price: float = 0.0, growth_years: int = 0, econ: bool = True,
                 stimulation: float = 0.0, growth: float = 0.0, att_exponent: float = -1.0,
                 catchment_mult: float = 1.0, coverage_override: float = 0.0,
                 market_override: float = 0.0, share_override: float = 0.0,
                 feed_behind_cap: float = 0.10, feed_dom_gain: float = 1.0, feed_dom_floor: float = 1.0,
                 cnx_online: float = 1.0, cnx_alliance: float = 0.615, cnx_interline: float = 0.25,
                 circuity: float = 1.35, factor_indirect: float = 1.044, mct_banking: int = 0,
                 season: str = "annual"):
    """The CALIBRATED any-city-pair forecast (coverage + feed + alliance). ~10s per call. The
    override args (default sentinels = off) are the Expert hooks: adjust any stage of the engine."""
    fc = calibrated_forecast(
        origin, dest, airline=airline, carrier_type=carrier_type, aircraft=aircraft, freq=freq,
        econ_share=econ_share, plan_lf=plan_lf, econ_fare=(econ_fare or None), bus_fare=bus_fare,
        fuel_price=(fuel_price or None), growth_years=growth_years, with_econ=econ,
        stimulation=(stimulation if stimulation > 0 else None), growth=growth,
        att_exponent=(att_exponent if att_exponent >= 0 else None), catchment_mult=catchment_mult,
        coverage_override=(coverage_override if coverage_override > 0 else None),
        market_override=(market_override if market_override > 0 else None),
        share_override=(share_override if share_override > 0 else None),
        feed_behind_cap=feed_behind_cap, feed_dom_gain=feed_dom_gain, feed_dom_floor=feed_dom_floor,
        cnx_online=cnx_online, cnx_alliance=cnx_alliance, cnx_interline=cnx_interline,
        circuity=circuity, factor_indirect=factor_indirect, mct_banking=bool(mct_banking),
        season=season)
    if isinstance(fc, dict) and fc.get("ok"):
        # ADVISORY airfield check (John, 4 Jul: advisory first, filtering later once trusted):
        # can the chosen aircraft actually use both fields on this mission? Never blocks the
        # forecast; UNKNOWN stays silent. The dashboard shows the binding end's verdict.
        try:
            import airfield_check as AFC
            dist_km = float(fc.get("distance_nm") or 0) * 1.852
            o_iata = (fc.get("origin") or {}).get("iata")
            d_iata = (fc.get("dest") or {}).get("iata")
            if dist_km > 0 and o_iata and d_iata:
                co = AFC.capability(aircraft, o_iata, dist_km, plan_lf=plan_lf)
                cd = AFC.capability(aircraft, d_iata, dist_km, plan_lf=plan_lf)
                known = [x for x in ((o_iata, co), (d_iata, cd)) if x[1].get("band") != "UNKNOWN"]
                if known:
                    apt, bind = min(known, key=lambda x: x[1].get("max_pax") or 10 ** 9)
                    fc["airfield"] = {"band": bind["band"], "airport": apt,
                                      "max_pax": bind.get("max_pax"), "seats": bind.get("seats"),
                                      "note": bind.get("note")}
        except Exception:
            pass
        global LAST_FC
        import time as _t
        LAST_FC = {"fc": fc, "when": _t.time()}      # feeds the /methodology bridge chart
    return JSONResponse(fc)


LAST_FC = None   # the most recent successful dashboard forecast, for the /methodology bridge

# Display-name overrides where the airportsdata 'city' field is the nearest town, not the name
# anyone uses (John, 4 Jul 2026: a package refresh started calling Knock 'Charlestown'). Curated;
# extend as oddities surface. Applied wherever the dashboard renders airport names.
CITY_OVERRIDES = {
    "NOC": "Knock", "EIS": "Tortola", "STT": "St Thomas", "SXM": "St Maarten",
    "LDY": "Derry", "MME": "Teesside", "NQY": "Newquay", "HUY": "Humberside",
}


def _city_of(ap, c):
    return CITY_OVERRIDES.get(c) or (ap[c]["city"] if c in ap and ap[c].get("city") else c)


@app.get("/methodology", response_class=HTMLResponse)
def methodology_page_route():
    """Methodology (John, 4 Jul 2026): a lay-person, graphic walk-through of how the forecast
    is built, with a bridge chart tied to the LAST forecast run on the dashboard."""
    try:
        import methodology_page as MP
        return HTMLResponse(MP.render(LAST_FC))
    except Exception as e:
        return HTMLResponse(f"<h3>Methodology page unavailable: {e}</h3>", status_code=500)


@app.get("/catchment", response_class=HTMLResponse)
def catchment_page():
    if os.path.exists(CATCH):
        return open(CATCH, encoding="utf-8").read()
    return "<h1>Catchment</h1><p>cortex_catchment.html not found.</p>"


@app.get("/help", response_class=HTMLResponse)
def help_page():
    if os.path.exists(HELP):
        return open(HELP, encoding="utf-8").read()
    return "<h1>Help</h1><p>cortex_help.html not found.</p>"


@app.get("/economics", response_class=HTMLResponse)
def economics_page():
    if os.path.exists(ECON):
        return open(ECON, encoding="utf-8").read()
    return "<h1>Economics</h1><p>cortex_economics.html not found.</p>"


@app.get("/api/catchment")
def api_catchment(place: str = "", origin: str = ""):
    """Drive-time catchment for one airport: the populated places within 220km, each with its
    least-cost drive minutes to the airport (same friction raster the forecast uses), banded
    0-30 / 30-60 / 60-90 / 90-120 / 120+. Returns total catchment population, the population
    reachable inside 120 minutes, and the measured capture share where we hold survey/mobility
    truth (SJC etc.). Feeds the Catchment map page."""
    q = (place or origin or "").strip()
    if not q:
        return JSONResponse({"ok": False, "error": "no airport given"})
    try:
        import route_engine as RE, geo_resolve as GEO, route_forecast as RF
        import airport_capture as ACAP
        ctx = _live_ctx()
        om = GEO.resolve_metro(q, served_index=ctx.get("served"), dump=DUMP, expand=False)
        home = om["primary"]
        ap = RE._airports(); o = ap.get(home)
        if not o or o.get("lat") is None:
            return JSONResponse({"ok": False, "error": f"could not resolve '{q}' to an airport"})
        olat, olon = float(o["lat"]), float(o["lon"])
        radius = 220.0
        locs = G.near_point(DUMP, olat, olon, radius, min_pop=5000, propensity=1.0)
        pts = [(l.lat, l.lon) for l in locs]
        times = None
        try:
            dt = RF._drive_engine()
            if dt is not None:
                times = dt.times_from(home, olat, olon, pts)
        except Exception:
            times = None
        BANDS = [30, 60, 90, 120]
        band_pop = {30: 0.0, 60: 0.0, 90: 0.0, 120: 0.0, 999: 0.0}
        out = []; total = 0.0
        for i, l in enumerate(locs):
            drive = None
            if times and i < len(times) and times[i] is not None:
                try:
                    drive = float(times[i])
                except Exception:
                    drive = None
            b = 999
            for bb in BANDS:
                if drive is not None and drive <= bb:
                    b = bb; break
            pop = float(l.population or 0)
            total += pop; band_pop[b] += pop
            out.append({"lat": round(float(l.lat), 4), "lon": round(float(l.lon), 4),
                        "pop": int(pop), "drive": (round(drive) if drive is not None else None),
                        "name": getattr(l, "name", "") or ""})
        out.sort(key=lambda r: -r["pop"])
        cap = ACAP.capture_for(home)
        reach120 = band_pop[30] + band_pop[60] + band_pop[90] + band_pop[120]
        return JSONResponse({"ok": True,
            "airport": {"code": home, "city": o.get("city") or q, "country": o.get("country") or "",
                        "name": o.get("name") or "", "lat": olat, "lon": olon},
            "radius_km": radius, "total_pop": int(total), "reach_120_pop": int(reach120),
            "bands": {str(k): int(v) for k, v in band_pop.items()},
            "capture": (round(float(cap), 3) if cap is not None else None),
            "drive_available": bool(times), "locales": out[:500]})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})


def _route_distance_km(origin, dest):
    """Cheap great-circle distance for the pair (resolve airports, no forecast)."""
    try:
        import route_engine as RE, geo_resolve as GEO
        ctx = _live_ctx()
        om = GEO.resolve_metro(origin, served_index=ctx.get("served"), dump=DUMP, expand=False)
        dm = GEO.resolve_metro(dest, served_index=ctx.get("served"), dump=DUMP, expand=True)
        ap = RE._airports(); o = ap.get(om["primary"]); d = ap.get(dm["primary"])
        return RE.gc_km(o["lat"], o["lon"], d["lat"], d["lon"]) if (o and d) else None
    except Exception:
        return None


def _candidate_airlines(origin, dest, dist_km, limit=3):
    """Airlines that could plausibly fly this sector: the biggest carriers based at the destination and
    origin airports (OAG) whose KNOWN fleet includes a range-feasible aircraft. Destination-based
    carriers come first, since they scoop the beyond-destination feed (e.g. JetBlue behind JFK). Only
    carriers we can fleet-check are auto-suggested, so we never propose an out-of-fleet aircraft."""
    try:
        import duckdb, geo_resolve as GEO, airline_fleets as AF
        from aircraft_economics import AIRCRAFT
        ctx = _live_ctx(); avail = list(AIRCRAFT.keys())

        def top(place, expand, n):
            m = GEO.resolve_metro(place, served_index=ctx.get("served"), dump=DUMP, expand=expand)
            codes = m["airports"] if expand else [m["primary"]]
            ph = ",".join("?" * len(codes))
            con = duckdb.connect(ctx["oag_db"], read_only=True)
            try:
                rows = con.execute(f"SELECT carrier, COUNT(*) FROM oag WHERE week=? AND dep_airport IN ({ph}) "
                                   f"GROUP BY carrier ORDER BY 2 DESC LIMIT ?", [ctx["week"]] + codes + [n]).fetchall()
            finally:
                con.close()
            return [r[0] for r in rows if r[0]]

        out = []
        for c in top(dest, True, 8) + top(origin, False, 5):
            cu = (c or "").upper()
            if cu in out:
                continue
            fleet, known = AF.fleet_for(cu, avail, dist_km)
            if known and fleet:
                out.append(cu)
            if len(out) >= limit:
                break
        return out
    except Exception:
        return []


def _explain_infeasible(origin, dest, dist_km, plan_lf=0.85):
    """A useful failure message instead of 'no range-feasible fleet' (John, 4 Jul 2026, BVI-JFK):
    name what the inputs RESOLVED to (misresolution is the usual surprise), separate aircraft
    RANGE from RUNWAY capability, and when the runway is the binding problem, say so and refer
    to the Avia aircraft performance feasibility work with Airbus/Boeing."""
    try:
        import geo_resolve as GEO
        from aircraft_economics import AIRCRAFT
        ctx = _live_ctx()
        mo = GEO.resolve_metro(origin, served_index=ctx.get("served"), dump=DUMP, expand=False)
        md = GEO.resolve_metro(dest, served_index=ctx.get("served"), dump=DUMP, expand=False)
        o, d = mo["primary"], md["primary"]
        where = (f"{origin} resolved to {o} ({mo.get('country', '?')}), {dest} to {d} "
                 f"({md.get('country', '?')}); sector {dist_km:,.0f} km.")
        in_range = [c for c, ac in AIRCRAFT.items() if ac["range_km"] >= dist_km * 1.03]
        if not in_range:
            longest = max(AIRCRAFT.values(), key=lambda ac: ac["range_km"])["range_km"]
            return (f"{where} That is beyond the range of any aircraft in the database "
                    f"(longest ~{longest:,.0f} km) - check the resolved airports are the "
                    f"ones you meant.")
        try:
            import airfield_check as AFC
            res = AFC.screen(in_range, o, d, dist_km, plan_lf=plan_lf)
            bands = {c: r.get("band") for c, r in res.items()}
            if bands and all(b == "NOT_FEASIBLE" for b in bands.values() if b != "UNKNOWN") \
                    and any(b == "NOT_FEASIBLE" for b in bands.values()):
                worst = min((r for r in res.values() if r.get("band") == "NOT_FEASIBLE"),
                            key=lambda r: r.get("max_pax") or 0)
                best_alt = max(((c, AFC.max_sector_km(c, o, plan_lf=plan_lf)) for c in in_range),
                               key=lambda t: t[1])
                return (f"{where} Aircraft RANGE is not the problem - the RUNWAY is: no "
                        f"range-capable type can lift a viable load off the field for this "
                        f"sector (e.g. TORA {worst.get('tora_m', 0):,.0f} m). Longest viable "
                        f"sector from {o} at plan load: ~{best_alt[1]:,.0f} km on the "
                        f"{best_alt[0]}. This is exactly what an Avia aircraft performance "
                        f"feasibility study (with Airbus/Boeing) resolves - or test the "
                        f"runway-extension scenario in the airfield check.")
        except Exception:
            pass
        return (f"{where} No airline in the fleet map operates a type that covers this sector - "
                f"name an airline explicitly, or the sector may need equipment nobody based "
                f"there flies.")
    except Exception:
        return "no airline with a range-feasible fleet for this sector"


@app.get("/api/optimise")
def api_optimise(origin: str, dest: str, airline: str = "", carrier_type: str = "FSC",
                 econ_share: float = 0.85, plan_lf: float = 0.85, bus_fare: float = 1400.0,
                 season: str = "annual"):
    """Blank inputs choose the best PATH. The operating airline changes the demand (its connecting
    feed), so the optimiser evaluates a shortlist of plausible airlines, computes each one's demand,
    then picks the airline + aircraft + weekly frequency that maximise annual profit. The aircraft is
    always within the chosen airline's real fleet (so no Ryanair on a widebody). A seasonal service
    (season=summer/winter) sizes the gauge on the season's demand over its operating weeks."""
    season_weeks = 28.0 if season == "summer" else 24.0 if season == "winter" else 52.0
    al = (airline or "").strip().upper()
    dist_km = _route_distance_km(origin, dest)
    if not dist_km:
        return JSONResponse({"ok": False, "error": "could not resolve the city pair"})
    dist_nm = dist_km / 1.852
    cands = [al] if al else (_candidate_airlines(origin, dest, dist_km) or [None])
    import aircraft_select as ASsel
    at = carrier_type if carrier_type in ("FSC", "LCC", "ULCC") else "FSC"
    fare = max(180, round(dist_nm * 0.11))
    best = None
    for cand in cands:
        fc = calibrated_forecast(origin, dest, airline=(cand or None), carrier_type=carrier_type,
                                 aircraft="A21N", freq=7, with_econ=False, season=season)
        if not fc.get("ok"):
            continue
        demand = fc["demand"]["total"]
        if demand <= 0:
            continue
        for freq in [3, 4, 5, 6, 7, 10, 14]:
            try:
                code, ranked = ASsel.select_aircraft(dist_nm, demand, freq, plan_lf=plan_lf,
                                econ_share=econ_share, econ_fare_ow=fare, bus_fare_ow=bus_fare,
                                airline_type=at, airline_iata=(cand or None), weeks=season_weeks)
            except Exception:
                continue
            prof = ranked[0]["annual_profit"]
            if best is None or prof > best["annual_profit"]:
                best = {"airline": cand, "aircraft": code, "freq": freq,
                        "annual_profit": prof, "demand": demand}
    if best is None:
        return JSONResponse({"ok": False, "error": _explain_infeasible(origin, dest, dist_km, plan_lf)})
    final = calibrated_forecast(origin, dest, airline=(best["airline"] or None), carrier_type=carrier_type,
                                aircraft=best["aircraft"], freq=best["freq"], econ_share=econ_share,
                                plan_lf=plan_lf, bus_fare=bus_fare, with_econ=True, season=season)
    if isinstance(final, dict):
        final["optimised"] = {"airline": best["airline"], "airline_auto": (not al) and bool(best["airline"]),
                              "aircraft": best["aircraft"], "freq": best["freq"],
                              "annual_profit": round(best["annual_profit"])}
    return JSONResponse(final)


def _xlsx_to_csv_zip(xlsx_path, zip_path):
    """Every sheet of the workbook as a CSV inside one zip (values as displayed, no formatting).
    For users whose IT policy or workflow prefers CSV over Excel downloads (Jessica, 3 Jul 2026)."""
    import csv as _csv
    import io
    import re
    import zipfile
    import openpyxl
    wb = openpyxl.load_workbook(xlsx_path, data_only=True, read_only=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for ws in wb.worksheets:
            buf = io.StringIO()
            w = _csv.writer(buf)
            for row in ws.iter_rows(values_only=True):
                if any(v is not None for v in row):
                    w.writerow(["" if v is None else v for v in row])
            safe = re.sub(r"[^A-Za-z0-9 _-]", "_", ws.title).strip() or "sheet"
            zf.writestr(safe + ".csv", buf.getvalue())
    wb.close()
    return zip_path


@app.get("/api/report")
def api_report(origin: str, dest: str, airline: str = "", carrier_type: str = "FSC",
               aircraft: str = "A21X", freq: int = 7, econ_share: float = 0.85, plan_lf: float = 0.85,
               econ_fare: float = 0.0, bus_fare: float = 1400.0, fuel_price: float = 0.0, growth_years: int = 0,
               part: str = "both", season: str = "annual"):
    """Forecast deliverables from the live forecast: part='deck' returns the Forecast Summary PPTX,
    part='xlsx' the Forecast Excel workbook, part='csv' the workbook's sheets as a zipped CSV
    bundle, part='both' a zip of deck + workbook."""
    import tempfile, route_deck as RDECK
    fc = calibrated_forecast(origin, dest, airline=(airline or None), carrier_type=carrier_type,
                             aircraft=aircraft, freq=freq, econ_share=econ_share, plan_lf=plan_lf,
                             econ_fare=(econ_fare or None), bus_fare=bus_fare,
                             fuel_price=(fuel_price or None), growth_years=growth_years, with_econ=True,
                             season=season)
    if not fc.get("ok"):
        return JSONResponse(fc, status_code=400)
    if not fc.get("economics_ok"):
        return JSONResponse({"ok": False, "error": "economics unavailable for the deck"}, status_code=400)
    dem = fc["demand"]; cap = fc["capacity"]; ec = fc["economics"]; raw = ec.get("raw") or {}
    o = fc["origin"]; d = fc["dest"]
    sh = fc["catchment"]["observed_share"]; nm = fc["catchment"]["names"]; home = fc["catchment"]["home"]
    full_split = sorted([((nm.get(c) or c), v) for c, v in sh.items()], key=lambda t: -t[1])
    split = full_split[:7]
    fmt = lambda n: f"{round(n or 0):,}"
    try:
        import airport_capture as _ACAP
        capture_basis = ("measured, survey and mobility data" if _ACAP.capture_for(home) is not None
                         else "modelled from drive time and competing service")
    except Exception:
        capture_basis = "modelled from drive time and competing service"
    catchment_text = (
        f"Addressable market: {fmt(dem['natural'])} each way per year, from Sabre O&D in the {o['city']} catchment.\n\n"
        f"Assumed capture with own nonstop: {dem.get('qsi_share', 0) * 100:.1f}%  ({capture_basis}).\n\n"
        f"Coverage gross-up: x{dem.get('coverage_gross_up', 1):.2f}.\n\n"
        f"Stimulation: x{(dem.get('stimulation') or 1):.2f} for the new nonstop.\n\n"
        f"Connecting feed adds behind {fmt(dem.get('feed_behind'))} and beyond {fmt(dem.get('feed_beyond'))} each way.")
    forecast = {
        "market": fmt(dem["natural"]), "captured": fmt(dem["captured"]),
        "feed": fmt(dem["feed_total"]), "total": fmt(dem["total"]),
        "split": split, "catchment_rows": full_split, "home_label": (nm.get(home) or home),
        "behind_pdew": dem.get("behind_pdew") or [], "beyond_pdew": dem.get("beyond_pdew") or [],
        "subtitle": f'{o["city"]} to {d["city"]}',
        "fit_lines": [
            (cap.get("recommendation") or f'Fits {cap["freq"]}x/week {cap["aircraft"]}.'),
            f'Carries {fmt(cap["carried"])} each way at {round((cap.get("load") or 0) * 100)}% load.',
            f'Coverage x{dem.get("coverage_gross_up", 1):.2f}; origin QSI share {dem.get("qsi_share", 0) * 100:.1f}%.',
            f'Feed: behind {fmt(dem.get("feed_behind"))}, beyond {fmt(dem.get("feed_beyond"))}.',
        ],
    }
    pnl = dict(raw)
    meta = {
        "title": f'{o["city"]} to {d["city"]}',
        "subtitle": f'{(airline or fc.get("airline") or "New entrant")} · {cap["aircraft"]} · {cap["freq"]}x/week',
        "origin": o["iata"], "origin_name": o["city"], "dest": d["city"], "aircraft": cap["aircraft"],
        "annual_profit": ec.get("annual_profit", 0), "frequency": cap["freq"],
        "sector_nm": fc.get("distance_nm", 0), "fare_ow": ec.get("econ_fare", 0), "plan_lf": plan_lf,
        "maint_basis": raw.get("maint_basis", ""), "own_basis": raw.get("own_basis", ""),
        "pnl_subtitle": f'Per-rotation economics on the {cap["aircraft"]}, indicative planning assumptions',
        "disclaimer": "Indicative, for directional guidance only. Calibrated central estimate; not any airline's actual costs.",
        "full_report": True, "catchment_text": catchment_text,
    }
    base = f'AviaCortex_{o["iata"]}_{d.get("iata", d["city"])}'
    tmpd = tempfile.gettempdir()
    deck_path = os.path.join(tmpd, base + ".pptx")
    xlsx_path = os.path.join(tmpd, base + ".xlsx")
    import datetime as _dt
    PPTX_MT = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    XLSX_MT = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    want_deck = part in ("deck", "both")
    want_xlsx = part in ("xlsx", "both", "csv")
    if want_deck:
        try:
            RDECK.build_deck(deck_path, forecast, pnl, meta)
        except Exception as e:
            return JSONResponse({"ok": False, "error": f"deck build failed: {e}"}, status_code=500)
    if want_xlsx:
        try:
            import cortex_workbook as CWB
            CWB.build_workbook(xlsx_path, fc, {"airline_name": (airline or fc.get("airline")),
                "analyst": "Avia Solutions", "date": _dt.date.today().strftime("%d %b %Y"),
                "plan_lf": plan_lf, "capture_basis": capture_basis, "econ_fare": ec.get("econ_fare")})
        except Exception as e:
            if part in ("xlsx", "csv"):
                return JSONResponse({"ok": False, "error": f"workbook build failed: {e}"}, status_code=500)
            want_xlsx = False
    if part == "csv":
        try:
            csv_zip = os.path.join(tmpd, base + "_csv.zip")
            _xlsx_to_csv_zip(xlsx_path, csv_zip)
            return FileResponse(csv_zip, filename=base + "_csv.zip", media_type="application/zip")
        except Exception as e:
            return JSONResponse({"ok": False, "error": f"csv export failed: {e}"}, status_code=500)
    if part == "xlsx":
        return FileResponse(xlsx_path, filename=base + ".xlsx", media_type=XLSX_MT)
    if part == "deck" or not want_xlsx:
        return FileResponse(deck_path, filename=base + ".pptx", media_type=PPTX_MT)
    import zipfile
    zip_path = os.path.join(tmpd, base + "_report.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(deck_path, base + ".pptx"); zf.write(xlsx_path, base + ".xlsx")
    return FileResponse(zip_path, filename=base + "_report.zip", media_type="application/zip")


PITCH_JOBS = {}   # job_id -> {state, file, name, error, kept, blocks, started}


def _stage(job_id, text):
    j = PITCH_JOBS.get(job_id)
    if j is not None and j.get("state") == "running":
        j["stage"] = text


def _run_pitch_job(job_id, p):
    import tempfile, zipfile, datetime as _dt
    import pitch_report as PR, cortex_workbook as CWB
    try:
        _stage(job_id, "sizing the market and running the forecast")
        fc = calibrated_forecast(p["origin"], p["dest"], airline=(p["airline"] or None),
                                 carrier_type=p["carrier_type"], aircraft=p["aircraft"], freq=p["freq"],
                                 econ_share=p["econ_share"], plan_lf=p["plan_lf"],
                                 econ_fare=(p["econ_fare"] or None), bus_fare=p["bus_fare"],
                                 fuel_price=(p["fuel_price"] or None), with_econ=True,
                                 season=p.get("season", "annual"))
        if not fc.get("ok"):
            PITCH_JOBS[job_id] = {"state": "error", "error": fc.get("error", "forecast failed")}; return
        o = fc["origin"]; d = fc["dest"]
        inputs = {"airline_name": (p["airline"] or fc.get("airline")),
                  "date": _dt.date.today().strftime("%d %b %Y")}
        _stage(job_id, "researching and verifying sources (the long step)")
        deck_path, html_path, audit = PR.build_pitch(fc, inputs)
        _stage(job_id, "building the deck, workbook and pack")
        base = f'AviaCortex_Pitch_{o["iata"]}_{d["iata"]}'
        tmpd = tempfile.gettempdir()
        files = [(deck_path, base + ".pptx")]
        if html_path:
            files.append((html_path, base + ".html"))
        try:
            import airport_capture as _ACAP
            cb = ("measured, survey and mobility data" if _ACAP.capture_for(fc["catchment"]["home"]) is not None
                  else "modelled from drive time and competing service")
            xlsx_path = os.path.join(tmpd, base + ".xlsx")
            CWB.build_workbook(xlsx_path, fc, {"airline_name": inputs["airline_name"], "analyst": "Avia Solutions",
                "date": inputs["date"], "plan_lf": p["plan_lf"], "capture_basis": cb})
            files.append((xlsx_path, base + ".xlsx"))
        except Exception:
            pass
        try:
            audit_path = os.path.join(tmpd, base + "_audit.json")
            with open(audit_path, "w", encoding="utf-8") as fh:
                json.dump(audit, fh, indent=2)
            files.append((audit_path, "research_audit.json"))
        except Exception:
            pass
        zip_path = os.path.join(tmpd, base + ".zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for pth, arc in files:
                zf.write(pth, arc)
        PITCH_JOBS[job_id] = {"state": "done", "file": zip_path, "name": base + ".zip",
                              "html": html_path, "html_name": base + ".html",
                              "kept": audit.get("total_kept"), "blocks": audit.get("blocks_researched")}
    except RuntimeError as e:
        PITCH_JOBS[job_id] = {"state": "error", "error": str(e)}
    except Exception as e:
        PITCH_JOBS[job_id] = {"state": "error", "error": f"pitch build failed: {e}"}


@app.get("/api/pitch/start")
def api_pitch_start(origin: str, dest: str, airline: str = "", carrier_type: str = "FSC",
                    aircraft: str = "A21X", freq: int = 7, econ_share: float = 0.85,
                    plan_lf: float = 0.85, econ_fare: float = 0.0, bus_fare: float = 1400.0,
                    fuel_price: float = 0.0, season: str = "annual"):
    """Kick off a researched airline pitch as a background job (it runs web research + verification,
    which takes minutes, longer than the tunnel's request timeout). Returns a job_id to poll."""
    import threading, uuid, time
    # PRE-FLIGHT (Jessica, 3 Jul 2026: clicked Generate and got silence): fail fast and clearly
    # if the research provider isn't wired, instead of running the whole forecast first.
    try:
        import research_provider as RP
        if not RP.get_provider().available():
            return JSONResponse({"ok": False, "error":
                "Research provider not configured on this server: ANTHROPIC_API_KEY is not set "
                "(or the anthropic package is missing). Use the standard Full report for the "
                "unresearched pack, or see /api/pitch/health."}, status_code=503)
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"research provider unavailable: {e}"},
                            status_code=503)
    job_id = uuid.uuid4().hex[:12]
    params = dict(origin=origin, dest=dest, airline=airline, carrier_type=carrier_type, aircraft=aircraft,
                  freq=freq, econ_share=econ_share, plan_lf=plan_lf, econ_fare=econ_fare, bus_fare=bus_fare,
                  fuel_price=fuel_price, season=season)
    PITCH_JOBS[job_id] = {"state": "running", "started": time.time(), "stage": "starting"}
    threading.Thread(target=_run_pitch_job, args=(job_id, params), daemon=True).start()
    return JSONResponse({"ok": True, "job_id": job_id})


@app.get("/api/pitch/status")
def api_pitch_status(job_id: str):
    j = PITCH_JOBS.get(job_id)
    if not j:
        return JSONResponse({"ok": False, "error": "unknown job"}, status_code=404)
    out = {"ok": True, "state": j.get("state")}
    if j.get("state") == "running":
        import time
        out["stage"] = j.get("stage", "")
        if j.get("started"):
            out["elapsed_s"] = int(time.time() - j["started"])
    if j.get("state") == "error":
        out["error"] = j.get("error")
    if j.get("state") == "done":
        out["kept"] = j.get("kept"); out["blocks"] = j.get("blocks")
    return JSONResponse(out)


@app.get("/api/pitch/file")
def api_pitch_file(job_id: str):
    j = PITCH_JOBS.get(job_id)
    if not j or j.get("state") != "done":
        return JSONResponse({"ok": False, "error": "not ready"}, status_code=404)
    return FileResponse(j["file"], filename=j["name"], media_type="application/zip")


@app.get("/api/pitch/html")
def api_pitch_html(job_id: str):
    """Just the interactive HTML digital pitch, no zip - open and use it straight away on an iPad."""
    j = PITCH_JOBS.get(job_id)
    if not j or j.get("state") != "done" or not j.get("html"):
        return JSONResponse({"ok": False, "error": "not ready"}, status_code=404)
    return FileResponse(j["html"], filename=j.get("html_name", "pitch.html"), media_type="text/html")


@app.get("/trackrecord")
def trackrecord(airport: str = ""):
    """Track record (John, 4 Jul 2026): per-airport back-test evidence - forecast vs actual
    first-full-year outturn for every launched route in the graded sample. Server-rendered;
    reads the newest evidence CSV on the server (track_record.SOURCES), so the page upgrades
    itself when the 6-year sample lands."""
    from fastapi.responses import HTMLResponse
    try:
        import track_record as TR
        return HTMLResponse(TR.page(airport or None))
    except Exception as e:
        return HTMLResponse(f"<h3>Track record unavailable: {e}</h3>", status_code=500)


@app.get("/api/pitch/health")
def api_pitch_health():
    """Confirms the research provider is wired: is the key visible to THIS server process, and is the
    anthropic package installed. Browse to /api/pitch/health to diagnose the 'no provider' error."""
    try:
        import research_provider as RP
        prov = RP.get_provider()
        has_key = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
        try:
            import anthropic  # noqa: F401
            has_pkg = True
        except Exception:
            has_pkg = False
        return JSONResponse({"ok": True, "available": prov.available(), "has_key": has_key,
                             "anthropic_installed": has_pkg, "model": getattr(prov, "model", None)})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})


@app.get("/api/aircraft")
def api_aircraft():
    """Aircraft types the economics module knows, for the dashboard picker."""
    try:
        from aircraft_economics import AIRCRAFT
        return JSONResponse({"aircraft": sorted(AIRCRAFT.keys())})
    except Exception:
        return JSONResponse({"aircraft": ["A21X", "A21N", "A20N", "B38M", "B789", "B788", "A333", "A339"]})


@app.get("/api/lookup")
def api_lookup(q: str = "", kind: str = "airport", limit: int = 8):
    """Typeahead: recognise an airline by code or name, or an airport by code, city or name."""
    q = (q or "").strip()
    if len(q) < 1:
        return JSONResponse({"results": []})
    if kind == "airline":
        try:
            import airline_names as AN
            return JSONResponse({"results": AN.search(q, limit)})
        except Exception:
            return JSONResponse({"results": []})
    # airports - rank served (real scheduled service) first so big hubs beat tiny fields
    import route_engine as RE
    ap = RE._airports(); qu = q.upper(); ql = q.lower()
    served = _live_ctx().get("served_codes") or set()
    matches = []
    for r in ap.values():
        code = r.get("iata")
        if not code or r.get("lat") is None:
            continue
        city = (r.get("city") or ""); name = (r.get("name") or "")
        if code == qu:
            pri = 0
        elif code.startswith(qu) and len(qu) >= 2:
            pri = 1
        elif ql in city.lower() or ql in name.lower():
            pri = 2
        else:
            continue
        svc = 0 if (served and code in served) else 1
        matches.append((pri, svc, len(city or name), city or name, r))
    matches.sort(key=lambda m: (m[0], m[1], m[2], m[3]))
    res = [{"code": r["iata"],
            "label": f'{(r.get("city") or r.get("name"))} ({r["iata"]}), {r.get("country","")}'}
           for *_, r in matches[:limit]]
    return JSONResponse({"results": res})
