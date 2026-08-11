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

# Collapse a one-stop itinerary by both operating carriers rather than by the onward carrier alone.
# See the note in _collapse. Default OFF pending the back-test; settable so an arm can be measured
# without editing the module.
COLLAPSE_BY_BOTH_LEGS = os.environ.get("AVIA_QSI_COLLAPSE_BOTH", "0") == "1"

# Alliance code normalisation: OAG alliance strings -> the short codes route_feed uses.
_ALLIANCE_NORM = {
    "ONEWORLD": "OW", "OW": "OW",
    "STAR ALLIANCE": "*A", "STAR": "*A", "*A": "*A",
    "SKYTEAM": "ST", "SKY TEAM": "ST", "ST": "ST",
}


def _alli(carrier, alliance_str=""):
    """Alliance code for a leg: the OAG alliance column when present, else the carrier map.

    "0" is OAG's not-in-an-alliance marker and must fall through to the carrier map rather than be
    treated as a code. Left as a code it compares equal to itself, so two unaligned carriers would
    have scored as alliance partners.
    """
    s = str(alliance_str or "").strip().upper()
    if s in _ALLIANCE_NORM:
        return _ALLIANCE_NORM[s]
    if s and s not in ("NONE", "-", "N/A", "NULL", "0", "0.0", "NAN"):
        return s                                   # unrecognised but named: still comparable
    try:
        from route_feed import ALLIANCE
        return ALLIANCE.get(str(carrier or "").upper(), "")
    except Exception:
        return ""


def _cnx_type(c1, a1, c2, a2):
    """ONLINE / ALLIANCE / INTERLINING, as classify_connection in the analyst Connection Builder.

    BOTH sides are normalised here, and that is the fix rather than a tidy-up. The OAG board carries
    alliance as "Star Alliance", "SkyTeam", "oneworld" or "0", while the proposed route's own leg is
    built with the short code the carrier map returns, "*A", "ST", "OW". Comparing the two raw meant
    the new route was never in an alliance with anybody: "SkyTeam" is not "ST".

    It cost almost nothing on the beyond side, where the new route connects at its own hub onto its
    own onward flights and is ONLINE anyway. On the behind side it cost a factor of four on every
    market: a United or Alaska arrival into San Jose feeding a China Airlines departure is a SkyTeam
    interline as far as the code was concerned, scored at 0.25, while a competing Korean Air routing
    over Seoul flies both legs itself, matches on carrier, and scores 1.00. Competing pairs of real
    board legs compared raw string to raw string and were classified correctly throughout, so the
    penalty fell on the proposed route alone. The tell was China Airlines and EVA returning an
    identical behind capture of 2.0824%, which two carriers in different alliances cannot.
    """
    if c1 and c1 == c2:
        return "ONLINE"
    n1, n2 = _alli(c1, a1), _alli(c2, a2)
    if n1 and n2 and n1 == n2:
        return "ALLIANCE"
    return "INTERLINING"


def _gap(arr_mins, dep_mins):
    """Connection time in minutes, overnight-aware (dep before arr rolls to the next day)."""
    g = dep_mins - arr_mins
    return g + 1440 if g < 0 else g


def _utc_offset_h(code):
    """Approximate UTC offset in whole hours from longitude.

    This is the SAME approximation cortex_app._schedule_times uses to build the schedule the client
    sees on the page, and it is here rather than imported so qsi_feed keeps no engine dependency at
    module level. Holding the two together matters: the connection bank has to be scored against the
    arrival time the product shows, not against a second and slightly different estimate of it. A
    caller that knows the real arrival passes hub_arr_mins and this is not used.
    """
    try:
        from route_feed import _coords
        c = _coords(code)
        return round((c[1] or 0.0) / 15.0) if c else 0
    except Exception:
        return 0


def _hub_arrival_mins(origin, hub, dep_time_mins, flying_mins, cfg):
    """Local clock time of the proposed arrival AT THE HUB, in minutes past midnight.

    THE DEFECT THIS FIXES, found 11 August 2026. This was `(dep_time_mins + flying_mins) % 1440`,
    which adds the block time to the ORIGIN's local departure and reads the answer as if it were the
    hub's local clock. On SJC-TPE that put the aircraft on the ground at Taipei at 00:45 instead of
    16:45, a sixteen-hour error, while every competing leg came off the OAG board correctly in local
    time. Eleven beyond markets carrying 6% of the base then scored zero for being "over MAX_CONNECT"
    when the real connections are two to three hours, and the surviving markets were scored against
    the wrong bank. It is also the explanation for the QSI feed anti-correlating with the 2025
    analyst at Pearson -0.46: not a disagreement about method, a time zone.
    """
    explicit = (cfg or {}).get("hub_arr_mins")
    if explicit is not None:
        return int(explicit) % 1440
    shift = (_utc_offset_h(hub) - _utc_offset_h(origin)) * 60
    return (int(dep_time_mins) + int(flying_mins) + shift) % 1440


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


def partner_map(airline, partners):
    """{carrier: the route airline's alliance code} for carriers named as its partners.

    WHY THIS EXISTS. A connection is priced online, alliance or interline, and a carrier outside the
    three global alliances can only ever be an interline at 0.25. That is right in general and wrong
    wherever a specific commercial agreement exists, which is exactly the case a route pitch is built
    on. The 2025 analyst's own scope says so: behind San Jose he counts "SkyTeam carriers AND
    Southwest Airlines", naming Southwest separately from "basic interline onto other full service
    carriers", and the deck's argument is the Southwest partnership.

    It matters here more than anywhere: Southwest is 77.3% of the distinct arrivals at San Jose, so
    the whole behind-origin feed turns on how its connections are priced. Modelled as an interline
    the behind feed is 5,967 two-way; as a partner it is 11,613, against the analyst's 13,992.

    DEFAULT EMPTY. A partnership is a commercial fact about a deal, not a property of a schedule, and
    the tool must not assume one. It is named by the person running the forecast and it belongs on
    the page beside the number, because a forecast that assumes a partnership and does not say so is
    a different product from one that does not.
    """
    if not airline or not partners:
        return {}
    code = _alli(airline) or f"PARTNERS-{str(airline).upper()}"
    out = {}
    for c in partners:
        c = str(c or "").strip().upper()
        if c and c != str(airline).upper():
            out[c] = code
    return out


def _collapse(leg1s, leg2s, cnx_apt, cnx_country, mct, max_connect, freq_cap, partners=None):
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
            # A named partner is priced as an alliance connection on that leg, and only there.
            _p = partners or {}
            ct = _cnx_type(l1.get("carrier"), _p.get(str(l1.get("carrier") or "").upper()) or l1.get("alliance"),
                           l2.get("carrier"), _p.get(str(l2.get("carrier") or "").upper()) or l2.get("alliance"))
            # COLLAPSE KEY. Keying on the second leg's carrier alone merges every inbound carrier
            # into one entry, keeps the best elapsed of the set and sums their frequency to a single
            # cap. That is not symmetric between the two feed sides: on the beyond side leg 2 is the
            # hub's onward bank and varies across carriers, so the new route gets several entries; on
            # the behind side leg 2 IS the new route, so every feeder arrival collapses into exactly
            # one entry against thirty to ninety competing ones. Keying on both legs treats a
            # distinct pair of operating carriers as the distinct product it is. Under test, not yet
            # the default: it moves the competitor sets on both sides, so it is a change to the
            # scoring and belongs to the back-test rather than to a judgement call.
            key = ((l1.get("carrier"), l2.get("carrier"), ct) if COLLAPSE_BY_BOTH_LEGS
                   else (l2.get("carrier"), ct))
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
    partners = partner_map(airline, cfg.get("partner_carriers"))

    hub_rows = boards.dep_rows(week, hub)
    hub_country = _board_country(hub_rows, "dep")
    onward = {}
    for r in hub_rows:
        if r.get("arr"):
            onward.setdefault(r["arr"], []).append(r)

    # The route origin, for the timezone reference and the circuity screen. origin_airports is the
    # whole catchment and its first entry is whichever airport the catchment builder happened to
    # return first, which on SJC-TPE is Sonoma County rather than San Jose, so the caller names it.
    o0 = (cfg.get("route_origin") or (origin_airports[0] if origin_airports else None))
    arr_mins = _hub_arrival_mins(o0, hub, dep_time_mins, flying_mins, cfg)
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
    # WHICH AIRPORTS MAY BE A COMPETING CONNECTING POINT, and this was wrong in a way that pushed the
    # two feed sides apart. `origin_airports` means different things on the two sides: route_forecast
    # passes the WHOLE 44-airport catchment to the beyond side and the SINGLE route origin to the
    # behind side. Excluding all of origin_airports therefore barred every Bay Area airport from
    # being a connecting point on the beyond side, while the behind side barred only San Jose.
    #
    # San Francisco is the dominant Bay Area gateway, with nonstops to Taipei, Seoul, Tokyo, Hong
    # Kong, Shanghai and Singapore. Removing it from the beyond competition deletes the strongest
    # rival set a San Jose passenger actually has, so the new route's beyond share reads high; keeping
    # it in the behind competition, correctly, made the behind share read low by comparison. Two
    # errors in opposite directions from one inconsistent exclusion.
    #
    # Only the route's own origin is excluded now, which is the behind side's rule and the right one:
    # a passenger does not connect at the airport the flight departs from.
    _ro = cfg.get("route_origin")
    _excl = ({_ro} if (_ro and not cfg.get("exclude_whole_catchment")) else set(origin_airports))
    cand = _candidate_hubs(origin_boards, exclude=_excl, min_hub_freq=minhf)
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
            new_itins = _collapse([leg1_new], rows_m, hub, hub_country, mct, maxc, fcap, partners)
        comp_itins = []
        for h, (leg1s, by_arr, hc) in hub_info.items():
            if h == m:
                continue          # origin->M nonstop: not part of the connecting market
            rows_hm = by_arr.get(m)
            if not rows_hm:
                continue
            if not _circuity_ok(o0, h, m, circ):
                continue
            comp_itins.extend(_collapse(leg1s, rows_hm, h, hc, mct, maxc, fcap, partners))
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
    partners = partner_map(airline, cfg.get("partner_carriers"))

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
            new_itins = _collapse(rows_y, [leg2_new], o0, org_country, mct, maxc, fcap, partners)
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
            comp_itins.extend(_collapse(yb_by_arr.get(h) or [], rows_hd, h, hc, mct, maxc, fcap, partners))
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
