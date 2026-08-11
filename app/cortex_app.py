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

# ---------------------------------------------------------------- password gate (Avia Solutions)
# A single shared-password gate (HTTP Basic Auth) in front of EVERY route - pages, static files and all
# /api endpoints - so the tool is protected at the ORIGIN (this server), not by Cloudflare. This lets a
# Cloudflare Access "Bypass" cover *.aviacortex.com without leaving the tool open, and guests need no
# Cloudflare account. Mirrors the Global Forecast tool exactly.
#   Password source, in order: env QSI_PASSWORD, else the first non-comment line of access_password.txt
#   next to this file. Any username is accepted; only the password is checked (constant-time compare).
import base64
import hmac
from starlette.responses import Response as _Response
_REALM = "The Observatory · Meridian"


def _load_password():
    pw = (os.environ.get("QSI_PASSWORD") or "").strip()
    if pw:
        return pw
    fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "access_password.txt")
    if os.path.exists(fp):
        for line in open(fp, encoding="utf-8"):
            s = line.strip()
            if s and not s.startswith("#"):
                return s
    return ""


ACCESS_PASSWORD = _load_password()
print("access: shared password ON (HTTP Basic Auth)." if ACCESS_PASSWORD
      else "NO PASSWORD SET - server is OPEN.")
# DEMO ENTRY: when on (default), the branded sign-in is a look-and-feel facade - any visitor proceeds through to the
# app, even if a shared password is configured, so testers get the entry experience. Set QSI_DEMO_ENTRY=0 to make the
# sign-in enforce the real password instead. (Origin access control for a public deployment is Cloudflare's job.)
DEMO_ENTRY = os.environ.get("QSI_DEMO_ENTRY", "1").strip().lower() not in ("0", "false", "off", "no")
print(f"entry: DEMO sign-in {'ON (any details proceed)' if DEMO_ENTRY else 'OFF (password required)'}.")


_ENTRY_PATHS = {"/signin", "/signout", "/loading", "/error", "/favicon.ico"}


def _session_token():
    return hmac.new(ACCESS_PASSWORD.encode(), b"obs-meridian-session", "sha256").hexdigest() if ACCESS_PASSWORD else ""


def _valid_session(tok):
    return bool(ACCESS_PASSWORD) and bool(tok) and hmac.compare_digest(tok, _session_token())


@app.middleware("http")
async def _gate(request: Request, call_next):
    path = request.url.path
    open_path = path in _ENTRY_PATHS or path.startswith("/static/entry/")   # the entry screens + their photography
    is_html_get = request.method == "GET" and "text/html" in request.headers.get("accept", "")
    # 1) SECURITY gate - only bites when a shared password is configured. Session cookie OR Basic Auth (fallback).
    if ACCESS_PASSWORD and not open_path:
        if not _valid_session(request.cookies.get("obs_session", "")):
            ok = False
            hdr = request.headers.get("authorization", "")
            if hdr.startswith("Basic "):
                try:
                    raw = base64.b64decode(hdr[6:].strip()).decode("utf-8", "replace")
                    ok = hmac.compare_digest(raw.partition(":")[2], ACCESS_PASSWORD)
                except Exception:
                    ok = False
            if not ok:
                if is_html_get:
                    return RedirectResponse("/signin", status_code=302)
                return _Response(status_code=401, headers={"WWW-Authenticate": f'Basic realm="{_REALM}"'})
    # 2) PRESENTATION gate - ALWAYS on, even with no password. The first HTML app page a visitor hits shows the
    #    branded sign-in, so demo testers get the look and feel and click through to the app (see /signin POST).
    if not open_path and is_html_get and not request.cookies.get("obs_entered"):
        return RedirectResponse("/signin", status_code=302)
    return await call_next(request)


# ---- Meridian branded entry screens (sign-in / welcome / loading / error), wired to real state ----
import cortex_entry as ENTRY
from collections import deque
_ENTRY_COUNTER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry_counter.txt")
RECENT_RUNS = deque(maxlen=6)


def _forecast_count():
    try:
        return int((open(_ENTRY_COUNTER).read().strip() or "0"))
    except Exception:
        return 0


def _record_run(origin, dest, season="annual", status="COMPLETE"):
    try:
        open(_ENTRY_COUNTER, "w").write(str(_forecast_count() + 1))
    except Exception:
        pass
    try:
        meta = {"annual": "YEAR-ROUND", "summer": "SUMMER 2026", "winter": "WINTER 2026/27"}.get(season, "YEAR-ROUND")
        RECENT_RUNS.appendleft({"route": f"{(origin or '').upper()} → {(dest or '').upper()}", "meta": meta, "status": status})
    except Exception:
        pass


def _entry_stats():
    return {"forecasts_run": f"{_forecast_count():,}", "recents": list(RECENT_RUNS)}


@app.get("/signin", response_class=HTMLResponse)
def signin_page(next: str = "/welcome", err: int = 0):
    return HTMLResponse(ENTRY.signin(forecasts_run=_entry_stats()["forecasts_run"],
                                     error=("That password was not recognised." if err else ""),
                                     next_url=next, demo=DEMO_ENTRY))


@app.post("/signin")
async def signin_post(request: Request):
    from urllib.parse import parse_qs
    raw = (await request.body()).decode("utf-8", "replace")            # parse the urlencoded form ourselves,
    form = {k: (v[0] if v else "") for k, v in parse_qs(raw, keep_blank_values=True).items()}  # so no python-multipart dependency
    pw = (form.get("password") or "").strip()
    nxt = form.get("next") or "/welcome"
    email = (form.get("email") or "").strip()
    # Real security only when a password is configured, and then it must match. With NO password set (the demo case),
    # the sign-in is a presentation layer: anyone proceeds so testers get the full look and feel through to the app.
    if not DEMO_ENTRY and ACCESS_PASSWORD and not hmac.compare_digest(pw, ACCESS_PASSWORD):
        return RedirectResponse(f"/signin?err=1&next={nxt}", status_code=303)
    resp = RedirectResponse(nxt if nxt.startswith("/") else "/welcome", status_code=303)
    # SESSION cookies (no max-age): they clear when the browser closes, so every new browser session shows the
    # branded sign-in again - what we want for demos. Swap to a max_age later for persistent "stay signed in".
    resp.set_cookie("obs_entered", "1", samesite="lax", path="/")
    if ACCESS_PASSWORD:
        resp.set_cookie("obs_session", _session_token(), httponly=True, samesite="lax", path="/")
    if email:
        resp.set_cookie("obs_user", email.split("@")[0][:40], samesite="lax", path="/")
    return resp


@app.get("/welcome", response_class=HTMLResponse)
def welcome_page(request: Request):
    u = (request.cookies.get("obs_user") or "there").replace(".", " ").replace("_", " ").strip().title() or "there"
    s = _entry_stats()
    return HTMLResponse(ENTRY.welcome(user_name=u, forecasts_run=s["forecasts_run"], recents=s["recents"]))


@app.get("/loading", response_class=HTMLResponse)
def loading_page(ctx: str = "LHR → JFK · SUMMER 2026", done: str = "/"):
    return HTMLResponse(ENTRY.loading(context=ctx, done_url=done))


@app.get("/error", response_class=HTMLResponse)
def error_page(ctx: str = "LHR → JFK · SUMMER 2026", ref: str = "MER-1102"):
    return HTMLResponse(ENTRY.error(context=ctx, err_ref=ref))


@app.get("/signout")
def signout_page():
    resp = RedirectResponse("/signin", status_code=303)
    resp.delete_cookie("obs_session", path="/")
    return resp


# branded entry photography (public prefix, so the sign-in page loads its image before auth)
from fastapi.staticfiles import StaticFiles as _StaticFiles
_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(_STATIC_DIR):
    app.mount("/static", _StaticFiles(directory=_STATIC_DIR), name="static")


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
    return "<h1>The Observatory · Meridian</h1><p>cortex_dashboard.html not found.</p>"


@app.get("/api/assess")
def assess(capture: float = 0.65, freq: int = 7, econ_fare: float = 345.0,
           bus_fare: float = 750.0, aircraft: str = "A21X", econ_share: float = 0.90,
           plan_lf: float = 0.875, incentive: bool = False):
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
              econ_share: float = 0.80, plan_lf: float = 0.875, fuel_price: float = 0.90):
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


def _ownership_view(y, annual, aircraft, freq, weeks, block_min, profit_key):
    """Contribution before ownership, and the ownership cost at which the route breaks even.

    WHY THIS EXISTS, decided 10 August 2026. A route profit rests on an ownership cost, and Avia
    cannot source one: four independent searches, three of them external, found no current
    type-and-age market value or lease rate in free public form, and appraiser licences allow
    internal use but not publication. Publishing our own would make Avia the only public source of a
    lease rate, which is a position we would spend years defending and which we have no business
    holding. Hiding it is worse, because a margin with an invisible assumption breaks the source
    attribution rule more thoroughly than a disclosed weak one.

    So the ownership cost stops being an input we assert and becomes the question we put back. The
    route covers its cash costs and contributes X towards ownership; above an ownership cost of Y it
    does not work. The airline knows Y from its own book and we do not. This is also the same
    reasoning that took profit out of the optimiser's objective on 8 August: nobody outside an
    airline knows how it prices its own capital.

    PURELY ADDITIVE. Every figure the block already returned is untouched, which econ_baseline.py
    checks. profit and margin remain, for internal use and for the sliders; what changes is what a
    client-facing renderer should print, and provenance says which types may show an ownership
    figure at all.
    """
    try:
        from aircraft_economics import OWNERSHIP_PROVENANCE
        own_turn = (y.get("ownership") or 0.0) + (y.get("insurance") or 0.0)
        turns = (freq or 0) * (weeks or 52.0)
        # A turn is a round trip, so the block hours it consumes are twice the one-way block time.
        bh_turn = 2.0 * (block_min or 0) / 60.0
        contrib = (y.get("profit") or 0.0) + own_turn
        util = 0.0
        try:
            from aircraft_economics import AIRCRAFT
            util = float(AIRCRAFT.get(aircraft, {}).get("annual_util_bh") or 0.0)
        except Exception:
            util = 0.0
        be_bh = (contrib / bh_turn) if bh_turn else None
        assumed_bh = 0.0
        try:
            from aircraft_economics import AIRCRAFT
            assumed_bh = float(AIRCRAFT.get(aircraft, {}).get("ownership_per_bh") or 0.0)
        except Exception:
            assumed_bh = 0.0
        # THE READABLE FORM, and the one that carries a warning. A multiple near 1 says the route
        # just covers its ownership. Well above 1 says either a strong route or a light cost base,
        # and the cost base here IS light by construction: the sourcing reference notes that aircraft
        # operating cost is the direct leg only, and full cost is roughly double once ground handling
        # and system overhead are added. So read a multiple around 2 as ordinary and treat anything
        # near 3 as a flag on the P&L rather than a finding about the route.
        multiple = (be_bh / assumed_bh) if (be_bh and assumed_bh) else None
        return {
            "contribution_before_ownership": round(contrib),
            "annual_contribution_before_ownership": round((annual.get(profit_key, 0) or 0)
                                                          + own_turn * turns),
            # The ownership cost per block hour at which this schedule exactly breaks even, and the
            # equivalent monthly lease at the type's annual utilisation, which is the form an airline
            # can check against its own book.
            "ownership_breakeven_per_bh": (round(be_bh) if be_bh is not None else None),
            "ownership_breakeven_per_month": (round(be_bh * util / 12.0)
                                              if (be_bh is not None and util) else None),
            "ownership_assumed_per_bh": (round(assumed_bh) or None),
            "ownership_assumed_per_month": (round(assumed_bh * util / 12.0) if (assumed_bh and util)
                                            else None),
            "ownership_breakeven_multiple": (round(multiple, 2) if multiple else None),
            "ownership_provenance": OWNERSHIP_PROVENANCE.get(aircraft, "none"),
            # The renderer's instruction, so the judgement lives with the data rather than in a deck
            # template somebody forgets to update.
            "ownership_publishable": OWNERSHIP_PROVENANCE.get(aircraft) == "citable",
            "ownership_note": (
                "Ownership is excluded from the headline. The figure shown is what the route "
                "contributes towards ownership after all cash operating costs; the break-even is the "
                "ownership cost at which it stops working. Avia does not publish lease rates: current "
                "type and age values are not available in public form and appraiser data may not be "
                "republished."),
        }
    except Exception:
        return {}


def _econ_block(each_way, aircraft, freq, home, dest_airport, gcd, econ_share, plan_lf,
                econ_fare, bus_fare, fuel_price, carrier_type, weeks=52.0, p2p_share=1.0, prorate=0.67,
                fixed_overrides=None, charges_override=None):
    try:
        import route_engine as RE
        from aircraft_economics import AIRCRAFT, RoutePnL, AnnualRoutePnL
        ac = AIRCRAFT[aircraft]
        e_yr = ac["econ_seats"] * freq * weeks; b_yr = ac["bus_seats"] * freq * weeks
        e_lf = min((each_way * econ_share) / e_yr if e_yr else 0, plan_lf)
        b_lf = min((each_way * (1 - econ_share)) / b_yr if b_yr else 0, plan_lf)
        dist_nm = round(gcd / 1.852); bmin = round(RE.block_min(dist_nm))
        fare = econ_fare if (econ_fare and econ_fare > 0) else max(180, round(dist_nm * 0.11))
        # PRORATE the connecting share: a connecting pax contributes LESS to THIS segment than a local one
        # (the through fare is prorated across both legs and connecting itineraries are discounted). So value
        # the connecting share at a fraction of the local fare, matching how an FSC books the flight. Default
        # 0.67; alliances prorate differently, so it's exposed for adjustment. p2p_share=1 -> no change.
        _psh = p2p_share if (p2p_share is not None) else 1.0
        _mkt_fare, _mkt_bus = fare, bus_fare
        _blend = _psh + (1.0 - _psh) * prorate
        fare = fare * _blend
        bus_fare = (bus_fare * _blend) if (bus_fare and bus_fare > 0) else bus_fare
        at = carrier_type if carrier_type in ("FSC", "LCC", "ULCC") else "LCC"
        fp_used = fuel_price if (fuel_price and fuel_price > 0) else 0.90
        _fo = fixed_overrides or {}
        # CHARGES FOR THIS AIRPORT PAIR, not the generic placeholder. Until 10 August 2026 both ends
        # of every route were charged route_engine.DEFAULT_CHARGES even where the module already held
        # real figures: LCY and EDI were both in aircraft_economics.AIRPORTS and both ignored, which
        # charged 13,200 USD a turn against 5,130 held and dropped 3,320 USD of charges recovery. An
        # 11,390 USD swing on a route the tool then called unprofitable and which BA flies daily.
        # charges_override lets a caller pass a set straight from RDC for one engagement.
        _mtow = ac.get("mtow_kg")
        try:
            import airport_charges as APC
            _ch = APC.pair_charges(home, dest_airport, mtow_kg=_mtow)
        except Exception:
            _ch = {"origin": dict(RE.DEFAULT_CHARGES), "dest": dict(RE.DEFAULT_CHARGES),
                   "origin_provenance": "generic", "dest_provenance": "generic",
                   "origin_source": "fallback", "dest_source": "fallback",
                   "provenance": "generic", "is_plug": True}
        if charges_override:
            for _end in ("origin", "dest"):
                if charges_override.get(_end):
                    _ch[_end] = dict(_ch[_end]); _ch[_end].update(charges_override[_end])
                    _ch[_end + "_provenance"] = "set by the caller"
                    _ch[_end + "_source"] = str(charges_override.get("source")
                                                or "entered for this engagement")
            _ch["provenance"] = "set by the caller"
            _ch["is_plug"] = False
        rp = RoutePnL("New entrant", aircraft, home, dest_airport, dist_nm, bmin,
                      econ_lf=e_lf, bus_lf=b_lf, econ_fare_ow=fare, bus_fare_ow=bus_fare,
                      airline_type=at, aircraft_age=2, origin_charges=_ch["origin"],
                      dest_charges=_ch["dest"], fuel_price_usd_kg=fp_used,
                      ownership_per_bh_override=_fo.get("own_bh"),
                      crew_per_bh_override=_fo.get("crew_bh"),
                      annual_util_bh_override=_fo.get("util_bh"))
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
            # THE PLUG, BROKEN OUT so the user can slide it to their own. Airport and handling
            # charges are a generic placeholder in this tool and on a short sector they dominate
            # everything: on LCY-EDI they are 56% of cost against fuel at 15%. Avia does not hold a
            # charges database, and published charges are a ceiling anyway because most carriers
            # negotiate below them. So the charges come out of the fixed block as their own number,
            # per turn and per passenger, and the client sets them to what they actually pay.
            "charges_per_turn": (y["landing"] + y["nav"] + y["handling"]),
            "charges_per_pax": (y["per_pax"] / _pax) if _pax else 0.0,
            "other_fixed_per_turn": (y["maintenance"] + y["ownership"] + y["insurance"] + y["crew"]),
            "ownership_per_turn": (y["ownership"] + y["insurance"]),
            "catering_per_pax": (y["catering"] / _pax) if _pax else 0.0,
            "charges_basis": _ch["provenance"],
            "per_pax_cost": (y["catering"] + y["per_pax"]) / _pax,
            "recovery_per_pax": y["charges_recovery"] / _pax,
            "cargo_rev": y["cargo_rev"],
            "indirect_rate": ((y["admin"] + y["sales"]) / y["net_rev"]) if y.get("net_rev") else 0.10,
            "ref_fuel_price": fp_used, "econ_share": econ_share, "plan_lf": plan_lf,
            "econ_fare": fare, "bus_fare": bus_fare, "freq": freq, "each_way": each_way,
        }
        return {"economics_ok": True, "economics": {
            "econ_fare": fare, "market_fare": _mkt_fare, "effective_fare": round(fare),
            "connecting_share": round(1.0 - _psh, 3), "prorate": prorate,
            "econ_lf": round(e_lf, 3), "bus_lf": round(b_lf, 3), "spilled": round(spilled),
            "seats": ac["econ_seats"] + ac["bus_seats"], "revenue": y["gross_rev"],
            "fuel": y["fuel"], "maintenance": y["maintenance"], "crew": y["crew"],
            "ownership": y["ownership"] + y["insurance"],
            "airport_nav_other": (y["landing"] + y["per_pax"] + y["handling"] + y["nav"]
                                  + y["catering"] + y["admin"] + y["sales"]),
            "total_cost": y["total_cost"], "profit": y["profit"], "margin": y["margin"],
            "breakeven_lf": y["breakeven_lf"], "annual_profit": annual.get(pk, 0),
            "aircraft_required": annual.get("aircraft_required"), "cost_model": cost_model, "raw": y,
            "charges_provenance": _ch["provenance"], "charges_is_plug": _ch["is_plug"],
            "charges_origin": {"provenance": _ch["origin_provenance"], "source": _ch["origin_source"],
                                **{k: round(v, 2) for k, v in _ch["origin"].items()}},
            "charges_dest": {"provenance": _ch["dest_provenance"], "source": _ch["dest_source"],
                              **{k: round(v, 2) for k, v in _ch["dest"].items()}},
            **_ownership_view(y, annual, aircraft, freq, weeks, bmin, pk)}}
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
                        freq=7, stimulation=None, growth=0.0, growth_years=0, econ_share=None,
                        plan_lf=0.875, econ_fare=None, bus_fare=1400.0, fuel_price=None,
                        radius_km=220.0, with_econ=True, att_exponent=None, catchment_mult=1.0,
                        coverage_override=None, market_override=None, share_override=None,
                        feed_behind_cap=0.10, feed_dom_gain=1.0, feed_dom_floor=1.0,
                        cnx_online=1.0, cnx_alliance=0.615, cnx_interline=0.25,
                        circuity=1.35, factor_indirect=1.044, mct_banking=False, season="annual",
                        induced_floor=True, fixed_overrides=None, seats=None, charges_override=None):
    """Any city pair through the CALIBRATED engine (route_forecast.forecast). season = annual (default)
    / summer / winter runs a seasonal service: demand scaled to the season's share of the year, capacity
    over the season's weeks.

    econ_share left as None takes the MEASURED back-cabin share of this market from Sabre, business
    and first excluded, which is the same definition as the seat counts it is compared against. The
    old fixed 0.85 assumed 15% of every market travels in the front cabin. Measured on SJC-TPE the
    figure is 18.06%, and China Airlines configures 10.5% of its A350-900 as business and first, so
    the front cabin on this route is genuinely oversold and the assumption understated it. There is
    no reason a single figure should hold across a Silicon Valley business market and a leisure
    route. A caller who passes a number still wins, which is what the dashboard slider does.

    seats is the CARRIER'S OWN configuration of the type, each way, and overrides the generic seat
    count in aircraft_economics.AIRCRAFT. The generic table holds one configuration per type, but an
    airline configures a type to its own product. Measured from OAG 2025 on comparable sectors
    (capacity_frame.frame), China Airlines flies the A350-900 at 306 seats and Starlux at 306 against
    the table's 336, EVA flies the 787-9 at 278 against 320, and the 777-300ER is 333 at EVA and 358
    at China Airlines against 380. Sizing a schedule on the generic number overstates the capacity by
    8 to 13% on these carriers and understates the load factor by the same. Left as None the generic
    table is used and nothing changes."""
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
                        annual_capacity=((float(seats) * freq * season_weeks) if seats else None),
                        market_factor=RF.market_factor_for(carrier_type),   # market-size-keyed P2P trim
                        season=season, season_share=season_share, season_weeks=season_weeks,
                        airline_type=ct, induced_floor=induced_floor,
                        airport_capture=__import__("airport_capture").factor_for(home))   # origin correction (dest thin-lift applied inside forecast, market-conditioned)
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
    # CABIN SPLIT. Measured front-cabin share, or the caller's figure, or the old assumption if the
    # measurement is unavailable. Named in the payload so a reader can tell which was used.
    _front = r.get("front_cabin_share")
    if econ_share is None:
        if _front is not None and 0.0 <= _front < 0.5:
            econ_share, cabin_basis = 1.0 - float(_front), "measured, Sabre business and first"
        else:
            econ_share, cabin_basis = 0.85, "assumed 85/15, no measurement available"
    else:
        cabin_basis = "set by the caller"
    each_way = r["total_demand"]               # unconstrained market demand: drives the multi-year build + spill
    carried_ew = r["carried_forecast"]         # capacity-bound forecast: the headline total, economics, PDEW, band
    # MULTI-YEAR BUILD: grow demand at the MEASURED market CAGR (dest market this year vs 2 years back),
    # so a pitch forecasts to the launch year and out ~5 years, not just the current Sabre year. Same
    # measure the back-test uses. Demand grows; capacity is fixed, so the build shows when a route fills
    # and when it needs upsizing. Induced routes start at the comparable-launch fill and mature from there.
    try:
        _m2 = SC.destination_market_split(ctx["sabre_db"], competing, dest_codes, year=ctx["year"] - 2)[1] or 0.0
        _cagr = ((float(_mkt) / _m2) ** 0.5 - 1.0) if (_mkt and _m2 > 0) else 0.03
    except Exception:
        _cagr = 0.03
    _cagr = max(min(_cagr, 0.20), -0.05)          # clamp: a measured burst over 2yr isn't a sustained rate
    _capf = float(r["annual_capacity"] or 0)
    _build = []
    # TAPER the growth beyond ~2 years toward a long-run trend: a hot short-term CAGR compounded flat over
    # 5 years over-projects badly (the maturity back-test showed this). Full rate for yr 1-2, decaying to
    # ~3%/yr by yr 5.
    _LONG_RUN = 0.03
    _cum = 1.0
    for _n in range(0, 6):                        # base year + 5
        if _n > 0:
            _rate = _cagr if _n <= 2 else max(_LONG_RUN, _cagr - (_cagr - _LONG_RUN) * (_n - 2) / 3.0)
            _cum *= (1.0 + _rate)
        _d = each_way * _cum
        _c = min(_d, _capf * plan_lf) if _capf else _d
        _build.append({"year": ctx["year"] + _n, "offset": _n, "demand": round(_d),
                       "carried": round(_c), "load": round(_c / _capf, 3) if _capf else None,
                       "spill": round(max(_d - _c, 0.0))})
    # CONFIDENCE BAND from the 6yr back-test: the forecast is the central estimate, and comparable
    # launches landed in this range about two in three times. New-market (induced) routes are modelled
    # from comparable launches rather than a measured market, so their band is wider. This honest range
    # is the wedge against a competitor's false-precision single number.
    _induced = bool(r.get("induced"))
    # band multipliers = the middle 2-in-3 of forecast-vs-outturn. FORECASTABLE band (0.40-2.15) is now
    # calibrated on the POST-SHIP size trim and validated out-of-sample (calib_interval.py: fit 2016-2018,
    # held-out 2024/2025 coverage ~60-63%, so labelled "about 2 in 3"; pooled all-years band absorbs the
    # slight held-out widening). A size-CONDITIONED band was tested and REJECTED - the per-market-size bands
    # did not hold ~2/3 out of sample (thin-market tightness was fit-year luck), so one honest global band.
    # The demand scatter is genuinely WIDE because +/-20% membership is not predictable at forecast time
    # (the confidence-tier attempt failed, held-out AUC ~0.52-0.58); the width IS the honest uncertainty.
    # Induced band (0.55-1.19) is tighter/downside-skewed (capacity-anchored); still on the old calib_bands
    # figure, its own held-out calibration is pending.
    _bl, _bh = (0.55, 1.19) if _induced else (0.40, 2.15)
    confidence = {"central": round(carried_ew), "low": round(carried_ew * _bl), "high": round(carried_ew * _bh),
                  "modelled": _induced, "coverage": "about 2 in 3 comparable launches",
                  "basis": "new-market: modelled from comparable launches" if _induced
                           else "measured-market forecast, calibrated on 6 years"}
    out = {
        "ok": True, "title": f'{o["city"]} → {d["city"]}', "engine": "route_forecast (calibrated)",
        "origin": {"iata": home, "city": o["city"], "country": o["country"], "metro": om["airports"]},
        "dest": {"iata": dest_airport, "city": d["city"], "country": d["country"], "metro": dest_codes},
        "airline": airline, "carrier_type": ct,
        "catchment": {"home": home, "observed_share": shares, "names": names,
                      "coords": {c: [ap[c]["lat"], ap[c]["lon"]] for c in competing
                                 if c in ap and ap[c].get("lat") is not None},
                      "origin_ll": [o.get("lat"), o.get("lon")], "dest_ll": [d.get("lat"), d.get("lon")]},
        "demand": {"natural": r["natural_market"], "current": r["current_via_origin"],
                   "captured": r["captured_demand"], "qsi_share": r["qsi_share"], "dest_share": r["dest_share"],
                   "coverage_gross_up": r["coverage_gross_up"], "premium_share": r["premium_share"],
                   # premium_share counts premium economy and drives the size pull; front_cabin_share
                   # is business and first only and is the one comparable with a seat count.
                   "front_cabin_share": r.get("front_cabin_share"),
                   "econ_share": round(econ_share, 4), "cabin_basis": cabin_basis,
                   "feed_total": r["connecting_feed"], "feed_beyond": r["feed_beyond"],
                   "feed_behind": r["feed_behind"], "feed_beyond_base": beyond_base, "feed_behind_base": behind_base,
                   "p2p_carried": r.get("p2p_carried"), "connecting_carried": r.get("connecting_carried"),
                   "p2p_share": r.get("p2p_share"),
                   "total": carried_ew, "total_demand": each_way, "avg_fare": r["avg_fare"],
                   "att": r.get("att_exponent"), "stimulation": r.get("stimulation"),
                   "induced": r.get("induced", False), "induced_lf": r.get("induced_lf"),
                   "induced_fare": r.get("induced_fare"),
                   "pdew_total": round(carried_ew / 365.0, 1),   # carried annual each-way pax / 365 = PDEW carried per day each way
                   "beyond_pdew": beyond_list, "behind_pdew": behind_list},
        "capacity": {"carried": r["carried_forecast"], "spill": r["spill"], "load": r["planned_load_factor"],
                     "annual_capacity": r["annual_capacity"], "recommendation": r["recommendation"],
                     "aircraft": aircraft, "freq": freq,
                     # Named so a reader can tell a measured configuration from the generic table.
                     "seats": (int(seats) if seats else None),
                     "seats_source": ("carrier configuration, OAG" if seats else "generic type table")},
        "season": {"mode": r.get("season", "annual"), "share": r.get("season_share", 1.0),
                   "weeks": round(season_weeks)},
        "projection": {"cagr": round(_cagr, 4), "base_year": ctx["year"], "horizon": 5, "build": _build},
        "confidence": confidence,
        "schedule": _schedule_times(home, dest_airport, o, d, bmin),
        "distance_nm": round(gcd / 1.852), "block_min": bmin, "week": ctx["week"], "year": ctx["year"],
    }
    # REVENUE LEG FARE, in priority: (1) a user-set fare always wins; (2) an induced route uses the low
    # stimulation fare that buys the fill; (3) otherwise the MEASURED Sabre market fare/yield, not a
    # distance proxy. This makes the P&L revenue reflect what the market actually pays.
    if r.get("induced") and r.get("induced_fare"):
        _ifare = r["induced_fare"]
        if not (econ_fare and econ_fare > 0):
            econ_fare = _ifare
        bus_fare = min(bus_fare, _ifare * 1.6)   # induced LCC/ULCC are low-yield; cap the premium fare
    if not (econ_fare and econ_fare > 0):
        _mkt_fare = r.get("avg_fare")            # measured Sabre one-way O&D fare for this market
        if _mkt_fare and _mkt_fare > 0:
            econ_fare = round(float(_mkt_fare), 2)
    if with_econ:
        out.update(_econ_block(carried_ew, aircraft, freq, home, dest_airport, gcd, econ_share,
                               plan_lf, econ_fare, bus_fare, fuel_price, ct, weeks=season_weeks,
                               p2p_share=r.get("p2p_share"), fixed_overrides=fixed_overrides,
                               charges_override=charges_override))
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




def _attach_airfield(fc, aircraft, plan_lf=0.875):
    """ADVISORY airfield check, on every path that returns a forecast.

    John, 4 July: advisory first, filtering later once trusted. Can the chosen
    aircraft use both fields on this mission? Never blocks the forecast, and UNKNOWN
    stays silent. The dashboard shows the binding end's verdict.

    Made a helper on 6 August for the same reason as the range margin: it lived
    inside /api/forecast, and OPTIMISE returns through /api/optimise, so the check was
    absent on the one path that actually chooses the aircraft.
    """
    try:
        if not isinstance(fc, dict) or not fc.get("ok"):
            return fc
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
    return fc


def _attach_range_margin(fc, aircraft):
    """ADVISORY range margin, on every path that returns a forecast (John, 6 Aug).

    The candidate filter in aircraft_select is a pass or fail against book range, so
    a route that clears it by 2% and one that clears it by 40% read the same on the
    page. This says which, and only when it is close enough to matter.

    It lives in a helper because the first version sat inside /api/forecast alone, and
    the OPTIMISE button returns through /api/optimise, which never touched it. The
    advisory was therefore absent on exactly the path that chooses the aircraft.
    """
    try:
        if not isinstance(fc, dict) or not fc.get("ok"):
            return fc
        import aircraft_select as _ASel
        _ll = fc.get("catchment") or {}
        _o = _ll.get("origin_ll") or [None, None]
        _d = _ll.get("dest_ll") or [None, None]
        rm = _ASel.range_margin(aircraft, float(fc.get("distance_nm") or 0) * 1.852,
                                origin_lon=_o[1], dest_lon=_d[1])
        if rm:
            fc["range_margin"] = rm
    except Exception:
        pass
    return fc


def _attach_viability(fc):
    """ADVISORY schedule viability, on every path that returns a forecast.

    John, 7 August: the runner warned and the screen did not, so a user working
    on the dashboard could take a 38% load factor all the way to a deck without
    ever being told. It warns; it never blocks and never changes a number.

    A helper for the same reason as the airfield and range checks: /api/optimise
    returns its own forecast, and a check that lives inside /api/forecast alone
    is absent on the path that chooses the schedule.
    """
    try:
        if not isinstance(fc, dict) or not fc.get("ok"):
            return fc
        import schedule_viability as _SV
        v = _SV.schedule_viability(fc)
        if v:
            fc["viability"] = v
    except Exception as e:
        # Reporting, not swallowing. A silent pass here reads on the dashboard
        # as "the load factor is fine", which is the failure the check exists
        # to prevent.
        fc["viability"] = {"band": "CHECK NOT RUN", "load_factor": None,
                           "frequency": None, "sized_frequency": None,
                           "question": "",
                           "message": "The schedule viability check did not "
                                      "run: %s: %s. The load factor has NOT "
                                      "been assessed." % (type(e).__name__, e)}
    return fc


@app.get("/api/forecast")
def api_forecast(origin: str, dest: str, airline: str = "", carrier_type: str = "FSC",
                 aircraft: str = "A21X", freq: int = 7, econ_share: float = 0.85,
                 plan_lf: float = 0.875, econ_fare: float = 0.0, bus_fare: float = 1400.0,
                 fuel_price: float = 0.0, growth_years: int = 0, econ: bool = True,
                 stimulation: float = 0.0, growth: float = 0.0, att_exponent: float = -1.0,
                 catchment_mult: float = 1.0, coverage_override: float = 0.0,
                 market_override: float = 0.0, share_override: float = 0.0,
                 feed_behind_cap: float = 0.10, feed_dom_gain: float = 1.0, feed_dom_floor: float = 1.0,
                 cnx_online: float = 1.0, cnx_alliance: float = 0.615, cnx_interline: float = 0.25,
                 circuity: float = 1.35, factor_indirect: float = 1.044, mct_banking: int = 0,
                 season: str = "annual", own_bh: float = 0.0, crew_bh: float = 0.0, util_bh: float = 0.0):
    """The CALIBRATED any-city-pair forecast (coverage + feed + alliance). ~10s per call. The
    override args (default sentinels = off) are the Expert hooks: adjust any stage of the engine.
    own_bh/crew_bh/util_bh are the airline-specific fixed-cost overrides ($/block-hour, $/block-hour, BH/yr)."""
    _fixed = {k: v for k, v in (("own_bh", own_bh), ("crew_bh", crew_bh), ("util_bh", util_bh)) if v and v > 0}
    # AUTO GAUGE: a blank / "AUTO" / "Unselected" aircraft sizes the metal to MEASURED demand at this frequency
    # (demand first, then the gauge), so an over-large aircraft can never be handed to the engine to fill. Optimise
    # then refines airline and type on top. This is the default assessment path.
    _auto_ac = None
    if (aircraft or "").strip().upper() in ("", "AUTO", "UNSELECTED"):
        try:
            import aircraft_select as ASsel
            _dnm = (_route_distance_km(origin, dest) or 0.0) / 1.852
            _sz = calibrated_forecast(origin, dest, airline=airline, carrier_type=carrier_type,
                                      aircraft="A21X", freq=freq, with_econ=False, induced_floor=False, season=season)
            _dem = (_sz.get("demand", {}) or {}).get("total_demand") if _sz.get("ok") else None
            if _dem and _dnm > 0:
                _at = carrier_type if carrier_type in ("FSC", "LCC", "ULCC") else "FSC"
                _wk = 28.0 if season == "summer" else 24.0 if season == "winter" else 52.0
                aircraft, _ = ASsel.select_aircraft(_dnm, _dem, freq, plan_lf=plan_lf, econ_share=econ_share,
                                econ_fare_ow=max(180, round(_dnm * 0.11)), bus_fare_ow=bus_fare,
                                airline_type=_at, airline_iata=(airline or None), weeks=_wk)
                _auto_ac = aircraft
        except Exception:
            pass
        if not _auto_ac:
            aircraft = "A21X"
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
        season=season, fixed_overrides=(_fixed or None))
    if isinstance(fc, dict) and fc.get("ok"):
        if _auto_ac:
            fc["auto_aircraft"] = _auto_ac      # UI shows which gauge the demand sized to
        _record_run(origin, dest, season)       # feeds the welcome-screen counter + recent runs
        _attach_airfield(fc, aircraft, plan_lf)
        _attach_range_margin(fc, aircraft)
        _attach_viability(fc)

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
        import importlib
        import methodology_page as MP
        importlib.reload(MP)   # evidence pages hot-reload: copy edits go live without a restart
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


def _explain_infeasible(origin, dest, dist_km, plan_lf=0.875):
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


def _group_metros(rows, ap, radius_km=80.0):
    """Cluster destination airports within ~radius_km into one metro market (JFK/EWR/LGA -> New York),
    summing the demand and leakage, so the opportunity scan ranks city markets not split airports."""
    import route_engine as RE
    clusters = []
    for r in rows:
        a = ap.get(r["dest"], {}); la, lo = a.get("lat"), a.get("lon")
        placed = False
        if la is not None and lo is not None:
            for cl in clusters:
                if cl["lat"] is not None and RE.gc_km(la, lo, cl["lat"], cl["lon"]) <= radius_km:
                    cl["rows"].append(r); placed = True; break
        if not placed:
            clusters.append({"lat": la, "lon": lo, "rows": [r]})
    out = []
    for cl in clusters:
        rs = sorted(cl["rows"], key=lambda x: -x["pax"]); head = rs[0]; a = ap.get(head["dest"], {})
        pax = sum(x["pax"] for x in rs); vh = sum(x["via_home"] for x in rs)
        fw = sum(x["avg_fare"] * x["pax"] for x in rs)
        out.append({"dest": head["dest"], "dest_city": a.get("city") or head["dest"],
                    "dest_country": a.get("country") or "", "airports": [x["dest"] for x in rs],
                    "pax": pax, "via_home": vh, "leakage": pax - vh,
                    "home_share": round(vh / pax, 3) if pax else 0.0,
                    "avg_fare": round(fw / pax, 2) if pax else 0.0})
    out.sort(key=lambda x: -x["leakage"])
    return out


@app.get("/api/opportunities")
def api_opportunities(origin: str, limit: int = 25, radius_km: float = 220.0):
    """Airport-led opportunity scan: rank the origin catchment's biggest destination markets by the
    leakage a home nonstop could recapture. This is a fast screen (one aggregate query), not a full
    forecast - the UI lets the user click a row to run the full forecast on it."""
    import route_engine as RE, geo_resolve as GEO, oag_served as OAS, sabre_catchment as SC
    ctx = _live_ctx()
    if not ctx.get("week") or not ctx.get("year"):
        return JSONResponse({"ok": False, "error": "OAG/Sabre databases not found."})
    idx = ctx["served"]
    try:
        om = GEO.resolve_metro(origin, served_index=idx, dump=DUMP, expand=False)
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"could not resolve '{origin}': {e}"})
    home = om["primary"]; ap = RE._airports(); o = ap.get(home)
    if not o:
        return JSONResponse({"ok": False, "error": "airport resolution failed for the origin"})
    sset = OAS.served_set(idx) if idx else None
    competing = [r["iata"] for r in RE.competing_airports(o, radius_km, sset, True)] if o else [home]
    try:   # pull extra airports so grouping still yields ~limit metro markets
        raw = SC.top_destinations(ctx["sabre_db"], competing, home, year=ctx["year"], top=max(int(limit) * 2, 60))
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"opportunity scan failed: {e}"})
    rows = _group_metros(raw, ap)[:int(limit)]
    return JSONResponse({"ok": True, "origin": home, "origin_city": o.get("city") or home,
                         "year": ctx["year"], "catchment": competing, "opportunities": rows})


@app.get("/api/hubbank")
def api_hubbank(origin: str = "", dest: str = "", airline: str = ""):
    """Hub-bank / connectivity view: the onward departure waves at the destination hub, binned into
    two-hour windows, so an airport can see when the hub banks and time the new route's arrival to feed
    them. Reads the OAG departure board at the hub via the wave-cache board reader."""
    import geo_resolve as GEO
    ctx = _live_ctx()
    if not ctx.get("week") or not ctx.get("oag_db"):
        return JSONResponse({"ok": False, "error": "OAG store not found."})
    idx = ctx["served"]
    try:
        dm = GEO.resolve_metro(dest, served_index=idx, dump=DUMP, expand=True)
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"could not resolve '{dest}': {e}"})
    hub = dm["primary"]
    try:
        from wave_cache import OagBoards
        wb = OagBoards(ctx["oag_db"])
        try:
            deps = wb.dep_rows(ctx["week"], hub)
        finally:
            wb.close()
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"hub board query failed: {e}"})
    banks = [{"window": f"{b*2:02d}:00-{b*2+2:02d}:00", "hour": b * 2, "daily_deps": 0.0,
              "services": 0, "dests": {}} for b in range(12)]
    for leg in deps:
        dmn = leg.get("dep_mins")
        if dmn is None:
            continue
        b = min(11, int(dmn // 120))
        bk = banks[b]
        bk["services"] += 1
        bk["daily_deps"] += (leg.get("freq") or 1.0) / 7.0
        a = leg.get("arr")
        if a:
            bk["dests"][a] = bk["dests"].get(a, 0) + 1
    for bk in banks:
        bk["daily_deps"] = round(bk["daily_deps"], 1)
        bk["dests"] = len(bk["dests"])
    peak = max(banks, key=lambda x: x["daily_deps"]) if banks else None
    return JSONResponse({"ok": True, "hub": hub, "hub_city": (dm.get("city") or hub), "week": ctx["week"],
                         "banks": banks, "peak_window": peak["window"] if peak else None,
                         "total_daily_deps": round(sum(b["daily_deps"] for b in banks), 1)})


@app.get("/api/optimise")
def api_optimise(origin: str, dest: str, airline: str = "", carrier_type: str = "FSC",
                 econ_share: float = 0.0, plan_lf: float = 0.875, bus_fare: float = 1400.0,
                 season: str = "annual", aircraft: str = "", freq: int = 0):
    # CONSTRAINED OPTIMISE: any field the client fills is honoured, any left blank is optimised. A fixed aircraft
    # restricts the gauge; a fixed freq restricts the frequency; a fixed airline restricts the operator (handled below).
    """Blank inputs choose the best PATH. The operating airline changes the demand (its connecting
    feed), so the optimiser evaluates a shortlist of plausible airlines, computes each one's demand,
    then picks the airline + aircraft + weekly frequency that maximise annual profit. The aircraft is
    always within the chosen airline's real fleet (so no Ryanair on a widebody). A seasonal service
    (season=summer/winter) sizes the gauge on the season's demand over its operating weeks."""
    al = (airline or "").strip().upper()
    dist_km = _route_distance_km(origin, dest)
    if not dist_km:
        return JSONResponse({"ok": False, "error": "could not resolve the city pair"})
    dist_nm = dist_km / 1.852
    cands = [al] if al else (_candidate_airlines(origin, dest, dist_km) or [None])
    import aircraft_select as ASsel
    fare = max(180, round(dist_nm * 0.11))
    _fixed_ac = (aircraft or "").strip().upper()
    _fixed_ac = _fixed_ac if _fixed_ac not in ("", "AUTO", "UNSELECTED") else None   # client-fixed gauge, else search
    _freqs = [int(freq)] if (freq and int(freq) > 0) else [3, 4, 5, 6, 7, 10, 14]     # client-fixed freq, else sweep
    _types = [carrier_type if carrier_type in ("FSC", "LCC", "ULCC") else "FSC"]   # type follows the operator, not swept (can't fly AA as a ULCC)
    _seasons = [season] if season in ("annual", "summer", "winter") else ["annual", "summer", "winter"]  # unselected = sweep schedule
    # OBJECTIVE, changed 8 August 2026 (John). Passengers subject to the load factor reaching the
    # planning band, not profit. The reasoning is the practice: nobody outside an airline knows how it
    # prices transfer passengers internally and the external costs and revenues are estimates, so
    # profit is directionally indicative guidance on whether a route is likely to make money. It is
    # not the thing to optimise. It stays in the output, labelled, and comes out of the selection.
    #
    # Profit-max also fails in a specific way here. On a new market demand is floored at the capacity
    # deployed, so passengers are a fixed multiple of capacity and profit-max reaches for the largest
    # gauge at the highest frequency: EDI-AUS returned 43,730 two-way at 33% fill on 8 August and
    # called it the best answer, while the tool's own viability banner said no airline would take it.
    #
    # The two constants come from the modules that own them, so there is one definition of each:
    #   schedule_viability.VIABLE_LF   0.65  below this a long-haul schedule is not a proposition
    #   schedule_sizing.PLANNING_LF    0.80  the fill a sized schedule is written to
    # Avia never shows an airline a load factor below 65% and targets the mid to late seventies or low
    # eighties: too high reads as implausible, too low and no airline engages. The old MIN_OPT_LF of
    # 0.55 sat below the floor Avia would ever present, and the fallback below it dropped the floor
    # altogether.
    import schedule_sizing as _SS
    import schedule_viability as _SV
    VIABLE_LF = _SV.VIABLE_LF
    TARGET_LF = _SS.PLANNING_LF
    rows = []
    for cand in cands:
        for ct_i in _types:
            for sea_i in _seasons:
                sea_weeks = 28.0 if sea_i == "summer" else 24.0 if sea_i == "winter" else 52.0
                fc = calibrated_forecast(origin, dest, airline=(cand or None), carrier_type=ct_i,
                                         aircraft="A21N", freq=7, with_econ=False, season=sea_i,
                                         induced_floor=False)   # measured demand for this operator + model + schedule
                if not fc.get("ok"):
                    continue
                # econ_share of 0 from the caller means "measure it". The gauge is chosen on how the
                # demand splits between the cabins, so the split has to be this market's own rather
                # than a flat 15% front cabin applied to Silicon Valley and to a leisure route alike.
                es_i = econ_share if (econ_share and econ_share > 0) else \
                    (fc["demand"].get("econ_share") or 0.85)
                demand = fc["demand"].get("total_demand") or fc["demand"]["total"]   # TRUE demand, not the capacity-bound total
                if demand <= 0:
                    continue
                # The demand above is measured at SEVEN weekly and, with AVIA_FREQ_SENSITIVE off, it is
                # the demand at every frequency, so sizing the whole sweep on it is correct. With the
                # switch ON it is not: capture moves with frequency, so a single daily reading would
                # size a 4x schedule on daily demand and a 14x schedule on the same, overstating the
                # low end and understating the high end. The optimiser would then choose a schedule the
                # forecast disagrees with, which is the /api/forecast against /api/optimise divergence
                # this file has already been caught by twice. Re-read demand per frequency when the
                # switch is on, and only then, so the default path costs nothing.
                _freq_sensitive = os.environ.get("AVIA_FREQ_SENSITIVE", "").strip() in ("1", "true", "on")
                _demand_7 = demand
                for f in _freqs:
                    demand = _demand_7
                    if _freq_sensitive:
                        _fcf = calibrated_forecast(origin, dest, airline=(cand or None), carrier_type=ct_i,
                                                   aircraft="A21N", freq=f, with_econ=False, season=sea_i,
                                                   induced_floor=False)
                        if not _fcf.get("ok"):
                            continue
                        demand = _fcf["demand"].get("total_demand") or _fcf["demand"]["total"]
                        if demand <= 0:
                            continue
                    try:
                        code, ranked = ASsel.select_aircraft(dist_nm, demand, f, plan_lf=plan_lf,
                                        econ_share=es_i, econ_fare_ow=fare, bus_fare_ow=bus_fare,
                                        airline_type=ct_i, weeks=sea_weeks,
                                        airline_iata=(None if _fixed_ac else (cand or None)),
                                        fleet=([_fixed_ac] if _fixed_ac else None))   # honour a client-fixed gauge, else search
                    except Exception:
                        continue
                    prof = ranked[0]["annual_profit"]; lf = ranked[0].get("total_lf") or 0.0
                    rows.append({"airline": cand, "aircraft": code, "freq": f, "ctype": ct_i,
                                 "season": sea_i, "annual_profit": prof, "demand": demand,
                                 "lf": float(lf),
                                 # The seat count the gauge was CHOSEN on, carried through so the
                                 # forecast fills the same aeroplane the optimiser sized. Sizing on
                                 # one configuration and filling on another is the mismatch the plan
                                 # load factor cap already had across three modules.
                                 "seats": ranked[0].get("seats"),
                                 "seats_source": ranked[0].get("seats_source")})
    if not rows:
        return JSONResponse({"ok": False, "error": _explain_infeasible(origin, dest, dist_km, plan_lf)})

    # SELECTION. The schedule whose planned fill sits nearest the target, among those clearing the
    # viable floor. The tie-break is the HIGHER frequency, which is schedule_sizing._closest's own
    # documented rule and is used here rather than reinvented: two schedules the same distance from
    # the target are not equally good to propose, and the one with more flights carries more people
    # and leaves more room in a soft season.
    _closest = lambda rs: min(rs, key=lambda r: (abs(r["lf"] - TARGET_LF), -r["freq"]))
    viable = [r for r in rows if r["lf"] >= VIABLE_LF]
    if viable:
        best = _closest(viable)
        not_viable = None
    else:
        # NOT a silent fallback to profit-max, which is what this did before and is how a 33% fill
        # became the recommended answer. Report the closest any schedule gets and say plainly that
        # none of them is a proposition, because "no schedule reaches 65%, this route does not work"
        # is a real answer an airport pays for and is the screening use the tool is for.
        best = max(rows, key=lambda r: (r["lf"], r["freq"]))
        not_viable = ("No schedule in the search reaches a %.0f%% planned load, which is the floor "
                      "below which a long-haul route is not a proposition. The closest is %s at "
                      "%d a week, planning at %.0f%%. Reported so the route can be screened out on "
                      "the evidence; it is not a recommendation."
                      % (VIABLE_LF * 100, best["aircraft"], best["freq"], best["lf"] * 100))
    final = calibrated_forecast(origin, dest, airline=(best["airline"] or None), carrier_type=best.get("ctype", carrier_type),
                                aircraft=best["aircraft"], freq=best["freq"],
                                econ_share=(econ_share if (econ_share and econ_share > 0) else None),
                                plan_lf=plan_lf, bus_fare=bus_fare, with_econ=True, season=best.get("season", "annual"),
                                seats=best.get("seats"))
    _attach_airfield(final, best["aircraft"], plan_lf)
    _attach_range_margin(final, best["aircraft"])
    _attach_viability(final)
    if isinstance(final, dict):
        # The fill the sweep selected on and the fill the forecast reports are computed differently:
        # the sweep measures against TRUE demand (line above runs the engine with induced_floor=False,
        # deliberately, so the sizing sees the market rather than the floor), while the returned
        # forecast runs with the floor on. On an induced route those diverge, which is why a run on
        # 8 August selected at 57% and reported 58.1%. Both are correct for what they measure, and
        # the difference is now stated rather than left for a reader to notice.
        _sel_lf = best.get("lf")
        _rep_lf = ((final.get("capacity") or {}).get("load"))
        _lf_note = None
        if _sel_lf is not None and _rep_lf is not None and abs(float(_rep_lf) - float(_sel_lf)) >= 0.02:
            _lf_note = ("selected on %.0f%% against the measured market and reports %.0f%% against "
                        "the forecast as returned; the difference is the induced floor, which sets "
                        "demand from the capacity deployed"
                        % (float(_sel_lf) * 100, float(_rep_lf) * 100))
        final["optimised"] = {"airline": best["airline"], "airline_auto": (not al) and bool(best["airline"]),
                              "aircraft": best["aircraft"], "freq": best["freq"],
                              "carrier_type": best.get("ctype"), "carrier_type_auto": carrier_type not in ("FSC", "LCC", "ULCC"),
                              "season": best.get("season"), "season_auto": season not in ("annual", "summer", "winter"),
                              "annual_profit": round(best["annual_profit"]),
                              # what it optimised FOR, so the output says which question it answered
                              "objective": "passengers at the planning load factor",
                              "target_lf": TARGET_LF, "viable_lf": VIABLE_LF,
                              "selected_lf": (round(float(_sel_lf), 3) if _sel_lf is not None else None),
                              "lf_basis_note": _lf_note,
                              "not_viable": not_viable,
                              "candidates": len(rows)}
    _record_run(origin, dest, best.get("season") or "annual")   # feeds the welcome-screen counter + recent runs
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
               aircraft: str = "A21X", freq: int = 7, econ_share: float = 0.85, plan_lf: float = 0.875,
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
    _smode = (fc.get("season") or {}).get("mode", "annual")
    _stag = "" if _smode == "annual" else f" · {_smode} service"
    _cf = fc.get("confidence") or {}
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
        "market_2w": fmt(dem["natural"] * 2), "total_2w": fmt(dem["total"] * 2),   # both-directions annual
        "projection": fc.get("projection"),   # 5-year demand build (each way)
        "split": split, "catchment_rows": full_split, "home_label": (nm.get(home) or home),
        "behind_pdew": dem.get("behind_pdew") or [], "beyond_pdew": dem.get("beyond_pdew") or [],
        "subtitle": f'{o["city"]} to {d["city"]}' + _stag,
        "fit_lines": [
            (cap.get("recommendation") or f'Fits {cap["freq"]}x/week {cap["aircraft"]}.'),
            f'Carries {fmt(cap["carried"])} each way at {round((cap.get("load") or 0) * 100)}% load.',
            f'Coverage x{dem.get("coverage_gross_up", 1):.2f}; origin QSI share {dem.get("qsi_share", 0) * 100:.1f}%.',
            f'Feed: behind {fmt(dem.get("feed_behind"))}, beyond {fmt(dem.get("feed_beyond"))}.',
            (f'New-market: modelled from comparable launches. Likely {fmt(_cf.get("low"))}-{fmt(_cf.get("high"))} each way.'
             if _cf.get("modelled") else
             f'Likely range {fmt(_cf.get("low"))}-{fmt(_cf.get("high"))} each way ({_cf.get("coverage","")}).')
            if _cf else "",
        ],
    }
    pnl = dict(raw)
    meta = {
        "title": f'{o["city"]} to {d["city"]}',
        "subtitle": f'{(airline or fc.get("airline") or "New entrant")} · {cap["aircraft"]} · {cap["freq"]}x/week' + _stag,
        "origin": o["iata"], "origin_name": o["city"], "dest": d["city"], "aircraft": cap["aircraft"],
        "annual_profit": ec.get("annual_profit", 0), "frequency": cap["freq"],
        "sector_nm": fc.get("distance_nm", 0), "fare_ow": ec.get("econ_fare", 0), "plan_lf": plan_lf,
        "maint_basis": raw.get("maint_basis", ""), "own_basis": raw.get("own_basis", ""),
        "pnl_subtitle": f'Per-rotation economics on the {cap["aircraft"]}, indicative planning assumptions',
        "disclaimer": "Indicative, for directional guidance only. Calibrated central estimate; not any airline's actual costs.",
        "full_report": True, "catchment_text": catchment_text,
        "season": fc.get("season", {"mode": "annual", "share": 1.0, "weeks": 52}),
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
                    plan_lf: float = 0.875, econ_fare: float = 0.0, bus_fare: float = 1400.0,
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
        import importlib
        import track_record as TR
        importlib.reload(TR)   # evidence pages hot-reload: copy edits go live without a restart
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
