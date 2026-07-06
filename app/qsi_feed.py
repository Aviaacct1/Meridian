#!/usr/bin/env python3
"""
Avia Cortex - Engine V2: the schedule-quality QSI connecting feed (opt-in; back-test first).
=============================================================================================
V1's feed counts ALL onward connections at a flat calibrated capture x alliance coefficient,
so departure time cannot move the forecast. V2 makes the feed a real QSI: for each onward
market it enumerates the new route's connection AND the competing one-stop itineraries over
rival hubs, scores every itinerary with the FROZEN Avia QSI (qsi_score.itinerary_qsi,
validated against the analyst QSI@SJC workbooks), and gives the new route its fair share:

    share_M = QSI(new route's connections to M) / QSI(all one-stop itineraries to M)
    feed_M  = k x share_M x measured connecting market M     (k = global calibration, replaces
                                                              V1's flat capture x conn_coeff)

The scorer is the analyst method exactly: frequency x elapsed-time decay (vs the market's
minimum-elapsed routing) x connection-type (online/alliance/interline) x service-level.
Alliance quality therefore moves INSIDE the itinerary score; when this feed is on, feed_side
must NOT also apply conn_coeff (that would double count). Departure time enters through the
hub arrival: it sets each connection's layover, hence elapsed time, hence the QSI share.
Illegal connections (buffer < MCT from mct_master.csv, 60 default) score zero. This SCORES
QUALITY AND COMPETES FOR SHARE; it is not the parked mct_bank haircut (a uniform supply
filter that back-tested worse - see HANDOVER_Engine_V2.md section 2).

Markets are keyed by onward airport (beyond side) / feeder airport (behind side), matching
route_feed's market keys. Nonstops on origin->M are excluded from both market and competition:
the Sabre market V1 measures is the ALREADY-CONNECTING traffic only, and keeping the same
definition preserves the calibration's comparability with V1.

Boards come from a provider (wave_cache.OagBoards live, wave_cache.CacheBoards for the many
back-test runs). Pure module: no engine imports at module level; route_feed will lazy-import
this behind feed_cfg['qsi_feed'] once the discrimination pre-test passes.

Tunables (cfg dict; defaults = frozen/V1 values): circuity 1.35, max_connect 720,
freq_cap 14.0 (route_qsi precedent), min_hub_freq 3.0, logit_lambda 1.0 (proportional).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from qsi_score import itinerary_qsi          # the frozen analyst QSI - single source of truth
import mct_bank as MB                        # MCT master load + cascading lookup (60 default)

CONN_FREQ_CAP = 14.0     # cap a routing's weekly connectable frequency (2x daily), as route_qsi
MIN_HUB_FREQ = 3.0       # a competitor hub needs at least this weekly frequency from the origin
MAX_CONNECT = 720        # analyst Connection Builder window; scoring makes long layovers near-
                         # worthless anyway, so this cap is about compute, not methodology
DEFAULT_CIRCUITY = 1.35  # same screen as route_feed.on_the_way

# Alliance code normalisation: OAG alliance strings -> the short codes route_feed uses.
_ALLIANCE_NORM = {
    "ONEWORLD": "OW", "OW": "OW",
    "STAR ALLIANCE": "*A", "STAR": "*A", "*A": "*A",
    "SKYTEAM": "ST", "SKY TEAM": "ST", "ST": "ST",
}


def _alli(carrier, alliance_str=""):
    """Alliance code for a leg: the OAG alliance column when present, else the carrier map."""
    s = str(alliance_str or "").strip().upper()
    if s in _ALLIANCE_NORM:
        return _ALLIANCE_NORM[s]
    if s and s not in ("NONE", "-", "N/A", "NULL"):
        return s                                   # unrecognised but named: still comparable
    try:
        from route_feed import ALLIANCE
        return ALLIANCE.get(str(carrier or "").upper(), "")
    except Exception:
        return ""


def _cnx_type(c1, a1, c2, a2):
    """ONLINE / ALLIANCE / INTERLINING, as classify_connection in the analyst Connection Builder."""
    if c1 and c1 == c2:
        return "ONLINE"
    if a1 and a2 and a1 == a2:
        return "ALLIANCE"
    return "INTERLINING"


def _gap(arr_mins, dep_mins):
    """Connection time in minutes, overnight-aware (dep before arr rolls to the next day)."""
    g = dep_mins - arr_mins
    return g + 1440 if g < 0 else g


_COORD_FAIL = False


def _circuity_ok(a, via, b, factor):
    """origin->via->b must be <= factor x direct. Pass-through when coordinates are unknown
    (synthetic tests / minor airports), matching route_feed.on_the_way's behaviour."""
    global _COORD_FAIL
    if _COORD_FAIL:
        return True
    try:
        from route_feed import _coords, _gc
        ca, cv, cb = _coords(a), _coords(via), _coords(b)
        if not ca or not cv or not cb:
            return True
        direct = _gc(ca, cb)
        if not direct or direct <= 100:
            return True
        return ((_gc(ca, cv) or 0) + (_gc(cv, cb) or 0)) <= factor * direct
    except Exception:
        _COORD_FAIL = True
        return True


def _collapse(leg1s, leg2s, cnx_apt, cnx_country, mct, max_connect, freq_cap):
    """Collapsed one-stop itineraries over cnx_apt: for each (onward carrier, connection type)
    keep the best legal pairing (minimum elapsed) with the connectable weekly frequency, capped.
    This is the containment that keeps enumeration to tens of itineraries per market: the full
    pair-by-pair day matching is the analyst Connection Builder's job at pitch level; at feed
    level the min-of-frequencies approximation is applied identically to the new route and every
    competitor, so the shares stay comparable.
    leg1s arrive at cnx_apt (need arr_mins, flying, carrier, alliance, freq, dep_country);
    leg2s depart it (need dep_mins, flying, carrier, alliance, freq, arr_country)."""
    # the four DOM/INT MCT combinations once per connect point, not per leg pair
    mct4 = {(i, o): MB.mct_for(mct, cnx_apt, inbound_intl=i, onward_intl=o)
            for i in (True, False) for o in (True, False)}
    out = {}
    for l1 in leg1s:
        a = l1.get("arr_mins")
        f1 = l1.get("flying") or 0
        if a is None or f1 <= 0:
            continue
        inbound_intl = _intl(l1.get("dep_country"), cnx_country)
        for l2 in leg2s:
            d = l2.get("dep_mins")
            f2 = l2.get("flying") or 0
            if d is None or f2 <= 0:
                continue
            need = mct4[(inbound_intl, _intl(l2.get("arr_country"), cnx_country))]
            g = _gap(a, d)
            if g < need or g > max_connect:
                continue
            elapsed = f1 + g + f2
            ct = _cnx_type(l1.get("carrier"), l1.get("alliance"),
                           l2.get("carrier"), l2.get("alliance"))
            key = (l2.get("carrier"), ct)
            f = min(l1.get("freq") or 1, l2.get("freq") or 1)
            cur = out.get(key)
            if cur is None:
                out[key] = {"elapsed": elapsed, "frequency": f, "cnx_type": ct}
            else:
                cur["elapsed"] = min(cur["elapsed"], elapsed)
                cur["frequency"] = cur["frequency"] + f
    itins = list(out.values())
    for it in itins:
        it["frequency"] = min(it["frequency"], freq_cap)
    return itins


def _intl(country, hub_country):
    """International transfer leg if the far-end country differs from the connect point's."""
    if not country or not hub_country:
        return True
    return str(country).strip().upper() != str(hub_country).strip().upper()


def _board_country(rows, side):
    """The connect point's own country: the mode of its legs' near-end country."""
    from collections import Counter
    key = "dep_country" if side == "dep" else "arr_country"
    cc = Counter(str(r.get(key) or "").strip().upper() for r in rows if r.get(key))
    return cc.most_common(1)[0][0] if cc else None


def _share(new_itins, comp_itins, logit_lambda=1.0):
    """The new route's fair share of one market: proportional share of QSI points (the analyst
    method), with an optional logit exponent held in reserve if proportional under-discriminates.
    All itineraries here are one-stop, so the service-level coefficient cancels by construction."""
    allit = new_itins + comp_itins
    if not allit:
        return 0.0
    me = min(it["elapsed"] for it in allit)
    q_new = q_all = 0.0
    for it in allit:
        q = itinerary_qsi(it["frequency"], it["elapsed"], me, it["cnx_type"], n_stops=1)
        if logit_lambda != 1.0 and q > 0:
            q = q ** logit_lambda
        it["qsi"] = q
        q_all += q
    for it in new_itins:
        q_new += it.get("qsi", 0.0)
    return (q_new / q_all) if q_all > 0 else 0.0


def _dep_boards(boards, week, airports):
    out = {}
    for a in airports:
        try:
            out[a] = boards.dep_rows(week, a)
        except Exception:
            out[a] = []
    return out


def _grouped_dep_board(boards, week, airport):
    """(rows-by-destination, board country) for an airport's departure board, memoised on the
    provider object so the dep-time sweep and the 4000-route pre-test group each board once."""
    memo = getattr(boards, "_qf_grouped", None)
    if memo is None:
        memo = {}
        setattr(boards, "_qf_grouped", memo)
    key = (week, airport)
    if key not in memo:
        try:
            rows = boards.dep_rows(week, airport)
        except Exception:
            rows = []
        by_arr = {}
        for r in rows:
            if r.get("arr"):
                by_arr.setdefault(r["arr"], []).append(r)
        memo[key] = (by_arr, _board_country(rows, "dep"))
    return memo[key]


def _candidate_hubs(origin_boards, exclude, min_hub_freq):
    """Airports served from the origin catchment with material frequency: the competitor
    connect points. Sabre would narrow this to hubs observed carrying the market; OAG-side
    the serves-the-market test below does the same job without a second store dependency."""
    freq = {}
    for rows in origin_boards.values():
        for r in rows:
            arr = r.get("arr")
            if not arr or arr in exclude:
                continue
            freq[arr] = freq.get(arr, 0.0) + (r.get("freq") or 0)
    return {h for h, f in freq.items() if f >= min_hub_freq}


def beyond_capture(boards, week, origin_airports, hub, markets, airline,
                   dep_time_mins, flying_mins, freq, mct=None, cfg=None, detail=False):
    """BEYOND side: {onward airport M: the new route's QSI share of the one-stop competition
    for origin->M}. The new route's itineraries connect at `hub` off the proposed arrival
    (dep_time_mins + flying_mins); competitors connect over every rival hub the catchment can
    reach, including other carriers' existing service into `hub` itself."""
    cfg = cfg or {}
    circ = cfg.get("circuity", DEFAULT_CIRCUITY)
    fcap = cfg.get("freq_cap", CONN_FREQ_CAP)
    maxc = cfg.get("max_connect", MAX_CONNECT)
    minhf = cfg.get("min_hub_freq", MIN_HUB_FREQ)
    lam = cfg.get("logit_lambda", 1.0)
    if mct is None:
        mct = MB.load_mct()

    hub_rows = boards.dep_rows(week, hub)
    hub_country = _board_country(hub_rows, "dep")
    onward = {}
    for r in hub_rows:
        if r.get("arr"):
            onward.setdefault(r["arr"], []).append(r)

    arr_mins = (int(dep_time_mins) + int(flying_mins)) % 1440
    o0 = origin_airports[0] if origin_airports else None
    leg1_new = {"arr_mins": arr_mins, "flying": int(flying_mins),
                "carrier": (airline or "").upper(), "alliance": _alli(airline),
                "freq": min(float(freq or 7), fcap), "dep_country": None}
    # the new leg's DOM/INT at the hub from the origin airport's country vs the hub's
    try:
        from route_feed import _coords  # noqa: F401  (only to confirm module presence)
        import airportsdata
        ap = airportsdata.load("IATA")
        rec = ap.get((o0 or "").upper())
        leg1_new["dep_country"] = rec["country"] if rec else None
    except Exception:
        pass

    origin_boards = _dep_boards(boards, week, list(origin_airports))
    cand = _candidate_hubs(origin_boards, exclude=set(origin_airports), min_hub_freq=minhf)
    # one pass per board: group every candidate hub's board by onward destination, hoist the
    # origin->hub legs and the hub's country out of the market loop (this is what makes the
    # 4000-route pre-test minutes, not hours)
    leg1s_by_hub = {}
    for ob in origin_boards.values():
        for r in ob:
            if r.get("arr") in cand:
                leg1s_by_hub.setdefault(r["arr"], []).append(r)
    hub_info = {}
    for h in cand:
        leg1s = leg1s_by_hub.get(h)
        if not leg1s:
            continue
        by_arr, hc = _grouped_dep_board(boards, week, h)
        hub_info[h] = (leg1s, by_arr, hc)

    shares, dmap = {}, {}
    for m in markets:
        rows_m = onward.get(m)
        new_itins = []
        if rows_m:
            new_itins = _collapse([leg1_new], rows_m, hub, hub_country, mct, maxc, fcap)
        comp_itins = []
        for h, (leg1s, by_arr, hc) in hub_info.items():
            if h == m:
                continue          # origin->M nonstop: not part of the connecting market
            rows_hm = by_arr.get(m)
            if not rows_hm:
                continue
            if not _circuity_ok(o0, h, m, circ):
                continue
            comp_itins.extend(_collapse(leg1s, rows_hm, h, hc, mct, maxc, fcap))
        s = _share(new_itins, comp_itins, lam)
        shares[m] = s
        if detail:
            dmap[m] = {"share": s, "n_new": len(new_itins), "n_comp": len(comp_itins),
                       "best_new": min((it["elapsed"] for it in new_itins), default=None),
                       "best_comp": min((it["elapsed"] for it in comp_itins), default=None)}
    return (shares, dmap) if detail else shares


def behind_capture(boards, week, origin_airports, dest_airports, feeders, airline,
                   dep_time_mins, mct=None, cfg=None, detail=False):
    """BEHIND side, the mirror: {feeder airport Y: the new route's QSI share of the one-stop
    competition for Y->destination}. The new route's itineraries connect at the ORIGIN: feeder
    arrivals into the origin against the proposed origin->D departure. Competitors are Y->H'->D
    over every hub Y can reach."""
    cfg = cfg or {}
    circ = cfg.get("circuity", DEFAULT_CIRCUITY)
    fcap = cfg.get("freq_cap", CONN_FREQ_CAP)
    maxc = cfg.get("max_connect", MAX_CONNECT)
    minhf = cfg.get("min_hub_freq", MIN_HUB_FREQ)
    lam = cfg.get("logit_lambda", 1.0)
    if mct is None:
        mct = MB.load_mct()

    o0 = origin_airports[0] if origin_airports else None
    d0 = dest_airports[0] if dest_airports else None
    inbound = {}
    org_country = None
    for o in origin_airports:
        try:
            rows = boards.arr_rows(week, o)
        except Exception:
            rows = []
        if rows and org_country is None:
            org_country = _board_country(rows, "arr")
        for r in rows:
            if r.get("dep"):
                inbound.setdefault(r["dep"], []).append(r)

    # the proposed onward leg origin->D: dep time + the route's own flying time
    leg2_new_flying = cfg.get("route_flying_mins")
    leg2_new = {"dep_mins": int(dep_time_mins) % 1440, "flying": int(leg2_new_flying or 0) or 1,
                "carrier": (airline or "").upper(), "alliance": _alli(airline),
                "freq": min(float(cfg.get("route_freq", 7)), fcap), "arr_country": None}

    shares, dmap = {}, {}
    feeder_boards = {}
    for y in feeders:
        rows_y = inbound.get(y)
        new_itins = []
        if rows_y:
            new_itins = _collapse(rows_y, [leg2_new], o0, org_country, mct, maxc, fcap)
        comp_itins = []
        if y not in feeder_boards:
            yb_by_arr, _yc = _grouped_dep_board(boards, week, y)
            feeder_boards[y] = yb_by_arr
        yb_by_arr = feeder_boards[y]
        cand = {h for h, rows in yb_by_arr.items()
                if h not in origin_airports and h not in dest_airports
                and sum(r.get("freq") or 0 for r in rows) >= minhf}
        for h in cand:
            by_arr, hc = _grouped_dep_board(boards, week, h)
            rows_hd = []
            for d in dest_airports:
                rows_hd.extend(by_arr.get(d) or [])
            if not rows_hd:
                continue
            if not _circuity_ok(y, h, d0, circ):
                continue
            comp_itins.extend(_collapse(yb_by_arr.get(h) or [], rows_hd, h, hc, mct, maxc, fcap))
        s = _share(new_itins, comp_itins, lam)
        shares[y] = s
        if detail:
            dmap[y] = {"share": s, "n_new": len(new_itins), "n_comp": len(comp_itins)}
    return (shares, dmap) if detail else shares


def optimise_dep(boards, week, origin_airports, hub, markets, market_size, airline,
                 flying_mins, freq, step=30, mct=None, cfg=None):
    """The departure-time optimiser: grid over the day, objective = total QSI-share-weighted
    market (what an airline maximises when it times the flight for the wave). Returns
    (best_dep_mins, {market: share at best}). Replaces mct_bank.optimise's connectable-share
    objective with the QSI fair share."""
    if mct is None:
        mct = MB.load_mct()
    best_dep, best_val, best_shares = 0, -1.0, {}
    for dep in range(0, 1440, step):
        shares = beyond_capture(boards, week, origin_airports, hub, markets, airline,
                                dep, flying_mins, freq, mct=mct, cfg=cfg)
        v = sum((market_size.get(m, 0.0) if market_size else 1.0) * s
                for m, s in shares.items())
        if v > best_val:
            best_val, best_dep, best_shares = v, dep, shares
    return best_dep, best_shares
