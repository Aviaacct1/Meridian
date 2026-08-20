#!/usr/bin/env python3
r"""The forecast pack: the fifteen pages a forecast run produces on its own.

WHY A SECOND PACK. The 40-page Observatory deck carries research and takes a research pack to
build. Most of the time a person runs a forecast, optimises it, settles on one they like, and wants
THAT forecast as something sendable. John's ruling, 14 August 2026: one forecast, one deck, and
anyone wanting several runs them several times and cuts the slides together by hand.

THE PAGE LIST IS NOT A DESIGN, IT IS A COPY. It is the forecast section of the China Airlines
TPE-SJC deck of 17 September 2025, slides 6, 7, 32 to 41, which is the shape Avia already sells and
a client has already accepted. Cover, disclaimer and a summary page in front of it:

     1 cover                          9 methodology, the divider
     2 disclaimer                    10 methodology, base demand and growth        (Sep 36)
     3 summary, what the tool found  11 methodology, the schedule                  (Sep 37)
     4 competition at both airports  12 methodology, point to point                (Sep 38)
     5 the opportunity, three markets 13 methodology, connecting markets           (Sep 39)
     6 traffic forecast              14 this forecast against the last             (Sep 40)
     7 connecting at the hub         15 the catchment                              (Sep 41)
     8 connecting at the destination

NOTHING HERE COMPUTES A FORECAST. Every figure is read from the deck contract by its own key, and
the contract is checked by app/contract_legs_check.py before it gets here. A key that is absent
produces a stated gap or loses its slide; nothing is filled with the nearest number to hand, which
is the fault that put a 96.8% load factor into a contract on 14 August.

TWO SLIDES ARE CONDITIONAL AND BOTH FAIL OPEN.

  Page 4 needs alliance seat share at the two airports, which comes from the OAG store and not from
  the contract. Pass it or the page is dropped. A competitive claim with no measurement behind it is
  worse than no page.

  Page 14 compares this forecast against a previous one for the same route. A first run of a pair
  has no previous, so the page is dropped rather than drawn empty. Pass --prior to include it.

    py -3.12 forecast_pack.py CONTRACT.json --out pack.pptx --codename "Project Redwood"

Avia Solutions Limited. All rights reserved.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import deck_spec as S                                                   # noqa: E402

# THE PRODUCT IS NOT AVIA SOLUTIONS AND THE DISCLAIMER MUST NOT SAY IT IS. John's correction,
# 14 August 2026: this pack is produced by Meridian, by The Aviation Observatory. The disclaimer
# also has to name the party it was prepared for, which the pack knows and was not printing.
DISCLAIMER = (
    "This forecast has been prepared by The Aviation Observatory{for_whom} using Meridian, its "
    "route forecasting model. It rests on licensed schedule and passenger data and on the "
    "assumptions stated in the methodology pages that follow. Forecasts are estimates and outturn "
    "will differ. No part of this document may be reproduced or relied upon by any other party "
    "without the written consent of The Aviation Observatory.")

# The contractual Sabre name (audit R3; single-sourced in app/attribution.py, carried
# here as a literal because the deck's import path to app/ is not guaranteed).
SRC = "Source: Meridian analysis, The Aviation Observatory; Sabre Global Demand Data; OAG schedules."


def _src(c):
    """The source line, built from what the run reports rather than from what the product claims.

    US airports validate a domestic forecast against US government data, so naming DOT DB1B is
    worth having. Naming it on a figure produced from a Sabre run is the fault found four times in
    the contract on 14 August, committed on purpose. This reads the run's own od_source block, so
    the line can only say DOT when DOT was read, and says so per leg because od_source partitions
    each feed scope rather than taking a side whole.
    """
    od = _g(c, "_settings", "od_source") or {}
    legs = [od.get("point_to_point"), od.get("beyond"), od.get("behind")]
    if not any(legs) or not any("DB1B" in (s or "") for s in legs):
        return SRC
    if all("DB1B" in (s or "") and "Sabre" not in (s or "") for s in legs if s):
        read = "US DOT O&D Survey (DB1B) and OAG schedules"
    else:
        read = ("US DOT O&D Survey (DB1B) for the US domestic markets, Sabre Global "
                "Demand Data for the rest, and OAG schedules")
    return "Source: Meridian analysis, The Aviation Observatory; %s." % read


# --- reading the contract ---------------------------------------------------

def _g(d, *path, default=None):
    """Walk a path of keys, returning default the moment one is missing or None."""
    cur = d
    for k in path:
        if not isinstance(cur, dict) or cur.get(k) is None:
            return default
        cur = cur[k]
    return cur


def _n(v, dp=0):
    """A figure, or an em-free dash when there is none. Never a zero standing in for a gap."""
    if v is None:
        return "-"
    try:
        return "{:,.{}f}".format(float(v), dp)
    except (TypeError, ValueError):
        return str(v)


def _pct(v, dp=1):
    return "-" if v is None else "{:.{}f}%".format(float(v) * 100, dp)


def _k(v):
    """Thousands, the unit the 2025 deck's own forecast table uses."""
    return "-" if v is None else "{:,.1f}".format(float(v) / 1000.0)


# --- the pages --------------------------------------------------------------

def _cover(c, meta):
    o, d = _g(c, "route_metadata", "origin_airport", default=""), _g(c, "route_metadata", "destination_airport", default="")
    al = _g(c, "route_metadata", "airline_name") or _g(c, "route_metadata", "airline_iata") or ""
    line = "%s to %s" % (_g(c, "route_metadata", "origin_city_code", default=o),
                         _g(c, "route_metadata", "destination_city_code", default=d))
    return S.cover(title_lines=[meta["title"] or line] + ([al] if al and al not in (meta["title"] or "") else []),
                   image="cover.hero", family="globe")


def _disclaimer(prepared_for=""):
    who = (" for %s" % prepared_for) if prepared_for else " for the party named on the cover"
    return S.prose([(None, DISCLAIMER.format(for_whom=who))], title="Basis of this document",
                   source="Meridian by The Aviation Observatory. All rights reserved.")


def _summary(c):
    """What the tool found, and on what basis. The page a reader should be able to defend a year on.

    THE BASIS LINE IS THE POINT OF IT. Today's four contract defects all came from a figure
    travelling without its basis, so the frequency, the gauge, the seat source, the year, the growth
    and the connecting floor setting all appear on the same page as the answer.
    """
    rm, e1 = c.get("route_metadata") or {}, c.get("economics_year1") or {}
    ss = _g(c, "segment_forecast", "summary", default={})
    tot = _g(ss, "grand_total", "forecast")
    p2p = _g(ss, "point_to_point_total", "forecast")
    cnx_h = _g(ss, "connecting_at_hub_total", "forecast")
    cnx_d = _g(ss, "connecting_at_destination_total", "forecast")
    cnx = (cnx_h + cnx_d) if (cnx_h is not None and cnx_d is not None) else None
    stats = [("Passengers a year, both directions", _n(tot), True),
             ("Point to point", _n(p2p), False),
             ("Connecting", _n(cnx), False),
             # "Load factor", not "Planned load factor": John's correction, 14 August. The figure is
             # the load factor the forecast produces, and calling it planned invites the reader to
             # take it for an input.
             ("Load factor", _pct(e1.get("total_load_factor"), 1), True)]
    basis = ["%s weekly, %s, %s seats (%s)"
             % (_n(rm.get("frequency_per_week")), rm.get("aircraft_type") or "-",
                _n(rm.get("seats")), _g(c, "summary_and_schedule", "_seats_source", default="seat source not stated")),
             "Service year %s" % (rm.get("service_year") or "not stated"),
             "Connecting floor %s" % ("on" if _g(c, "_settings", "split_floor") else "off"),
             _g(c, "summary_and_schedule", "_schedule_times_need", default="departure time basis not stated")]
    return S.stat_row(stats,
                      panels=[S.panel("The basis of this run", basis)],
                      title="Summary of route forecast",
                      subtitle="%s to %s" % (rm.get("origin_airport") or "", rm.get("destination_airport") or ""),
                      source=_src(c))


def _competition(alliance):
    """Alliance seat share at both airports. Sep 25 slide 6, and it is a MEASUREMENT.

    alliance = {"origin": {"airport": "SJC", "week": "...", "rows": [(alliance, share), ...]},
                "dest":   {...}}
    Dropped entirely when not supplied: an alliance claim with nothing behind it is the sort of
    statement a network planner takes apart in the room.
    """
    if not alliance:
        return None
    rows, heads = [], []
    for side in ("origin", "dest"):
        blk = alliance.get(side) or {}
        for name, share in (blk.get("rows") or []):
            rows.append([blk.get("airport") or side, name, _pct(share, 1)])
        if blk.get("week"):
            heads.append("%s %s" % (blk.get("airport") or side, blk["week"]))
    if not rows:
        return None
    return S.table({"head": ["Airport", "Alliance", "Share of seats"], "rows": rows},
                   title="Alliance seat share at both airports",
                   subtitle=" and ".join(heads) or None,
                   source="Source: OAG schedules, Meridian analysis.")


def _opportunity(c):
    """The three addressable markets. Sep 25 slide 7.

    The labels say MARKET and not forecast, because the 2025 deck's own footnote does and because
    the three are base annual demand before stimulation. Reading them as a forecast is the mistake
    this page invites, so the subtitle names the year and the state.
    """
    ss = c.get("summary_and_schedule") or {}
    items = [(_n(ss.get("point_to_point_market")), "Point to point market"),
             (_n(ss.get("connecting_market_over_hub")),
              "Connecting market over %s" % (_g(c, "connecting_at_hub", "hub", default="the hub"))),
             (_n(ss.get("connecting_market_over_destination")),
              "Connecting market over %s" % (_g(c, "route_metadata", "origin_airport", default="the origin")))]
    yr = _g(c, "route_metadata", "service_year")
    # THE SOURCE LINE IS NEVER DISPLACED (audit R4): the catchment note used to REPLACE
    # the source, leaving Sabre-derived figures on this slide with no Sabre statement.
    # Both now appear, note first, attribution always.
    note = ss.get("catchment_note")
    return S.keynumbers(items, title="The opportunity",
                        subtitle=("Addressable market at %s, before stimulation and before capture" % yr)
                                 if yr else "Addressable market before stimulation and before capture",
                        source=(("%s  %s" % (note, _src(c))) if note else _src(c)))


def _forecast_table(c):
    """Sep 25 slide 32, in its own column order: market, capture, forecast, per trip.

    THE COLUMNS ARE THE 2025 DECK'S, not ours, because a client who has seen that table should be
    able to read this one without being taught it. Where the payload cannot fill a column it is
    left as a dash rather than dropped, so the shape is recognisable.
    """
    ss = _g(c, "segment_forecast", "summary", default={})
    dep = _g(c, "economics_year1", "total_departures_annual_two_way")
    rm = c.get("route_metadata") or {}
    base_yr = _g(c, "route_metadata", "base_year") or _g(c, "_settings", "base_year")
    svc_yr = rm.get("service_year")
    buckets = _g(c, "segment_forecast", "_competition_buckets", default={}) or {}

    def row(label, blk, indent=False):
        fc = blk.get("forecast")
        ptew = (fc / dep) if (fc and dep) else None
        stim = blk.get("stimulation_factor")
        # CAGR, not the cumulative (Mark Kiehl/SJC, 20 August 2026, reviewing the three
        # airline packs): "It's just a big number" - 18.3% over two years reads as
        # alarming where the per-annum rate behind it is roughly half that and stays in
        # single digits. cagr is the SAME figure the cumulative was built from
        # (forecast_to_contract._fill_forecast_table), not a re-derivation; fall back to
        # the cumulative only if an older contract has no cagr field.
        _g_rate = blk.get("cagr")
        if _g_rate is None:
            _g_rate = blk.get("annual_growth_rate")
        return [("   " + label) if indent else label,
                _k(blk.get("base_annual_demand")),
                _pct(_g_rate, 1),
                _k(blk.get("demand_at_service_year")),
                ("-" if stim is None else "x%.2f" % float(stim)),
                _pct(blk.get("capture_rate"), 1),
                _k(fc), _n(ptew, 0)]

    def bucket_rows(key):
        """The competed and uncompeted split beneath its own leg, where the run produced one."""
        out = []
        for b in (buckets.get(key) or []):
            out.append([("   " + str(b.get("bucket"))), _k(b.get("base")), "-", "-", "-",
                        _pct(b.get("capture"), 1), _k(b.get("forecast")), "-"])
        return out

    hub = _g(c, "connecting_at_hub", "hub", default="the hub")
    org = _g(c, "route_metadata", "origin_airport", default="the origin")
    rows = [row("Total point to point", ss.get("point_to_point_total") or {})]
    rows.append(row("Connecting at %s" % hub, ss.get("connecting_at_hub_total") or {}))
    rows += bucket_rows("connecting_at_hub")
    rows.append(row("Connecting at %s" % org, ss.get("connecting_at_destination_total") or {}))
    rows += bucket_rows("connecting_at_destination")
    rows.append(row("Grand total", ss.get("grand_total") or {}))

    def yr(label, y):
        return "%s %s" % (label, y) if y else label

    _cum_note = _g(ss, "point_to_point_total", "annual_growth_rate")
    notes = ["Passengers per trip each way. Demand requiring a connection at both ends is excluded.",
             _g(ss, "grand_total", "_basis", default="carried, after the plan load factor cap"),
             "Base annual demand is measured origin and destination demand, both directions.",
             ("Growth is shown as a compound annual rate." +
              (" The cumulative growth from the base year to the service year is %s." % _pct(_cum_note, 1)
               if _cum_note is not None else "")),
             "Stimulation is applied to the point to point leg only; the connecting legs carry x1.00.",
             _g(c, "segment_forecast", "_competition_basis",
                default="Competed and uncompeted rows appear where the run classified the markets.")]
    return S.table({"head": ["Market", yr("Base annual demand (000s)", base_yr), "Traffic growth (CAGR)",
                             yr("Demand before stimulation (000s)", svc_yr), "Stimulation",
                             "Capture rate", yr("Forecast traffic (000s)", svc_yr),
                             "Per trip each way"],
                    "rows": rows, "total": True},
                   title="Traffic forecast",
                   subtitle="%s weekly, year 1 at %s" % (_n(rm.get("frequency_per_week")),
                                                         svc_yr or "the service year"),
                   bullets=notes,
                   source=_src(c))


def _connecting(c, key, title):
    """Sep 25 slides 33 and 34, one per side.

    THE TABLE IS THE FIFTEEN LARGEST CITIES AND THE PAGE SAYS SO. cortex_app._feed_list takes
    top=15, and a subtotal presented as a leg is one of the four faults corrected on 14 August.
    """
    blk = c.get(key) or {}
    cities = blk.get("cities") or []
    if not cities:
        return None
    # THE THREE-LETTER CODE GOES BEFORE THE CITY NAME. John's correction, 14 August: a planner
    # reads the code first and several of these city names are ambiguous without it.
    rows = [[str(x.get("nr") or i + 1), x.get("city_code") or "",
             x.get("city_name") or x.get("city_code") or "",
             x.get("country") or "", _n(x.get("annual_demand")), _pct(x.get("airline_share"), 1),
             _n(x.get("annual_forecast")), _n(x.get("pdew"), 1)]
            for i, x in enumerate(cities)]
    leg = _g(c, "segment_forecast", "summary",
             "connecting_at_hub_total" if key == "connecting_at_hub" else "connecting_at_destination_total",
             "forecast")
    # THE DEMAND-COLUMN TOTAL, 20 August 2026 (John, checking the EVA pack against the
    # completed forecast column): connecting_market_over_hub/_destination is the FULL
    # uncapped beyond/behind market before capture, the same quantity the fifteen
    # printed cities' own "annual_demand" figures are drawn from, additive with them.
    # 19 August's note calling this "a different quantity, leave it blank" was wrong:
    # checked against route_metadata.catchment_headline, it is the right total to
    # complete to, and it reconciles to the pre-fix numbers Jol first queried.
    #
    # BASIS, 20 August 2026 (Jol's later catch, same day: "connecting market over
    # Taipei 719,500 both directions... but this says each way", the mix he found on
    # the summary page). Fixing THAT defect doubled connecting_market_over_hub/
    # _destination to two-way at the source (Deck Generator/deck_contract.py), which
    # this page had not accounted for: it was written when that field was each way,
    # additive with the city rows with no conversion needed. It is now two-way like
    # the forecast leg above, so it takes the SAME /2.0 treatment as `leg_ew`, not the
    # one this comment used to describe.
    mkt_leg = _g(c, "route_metadata", "catchment_headline",
                 "connecting_market_over_hub" if key == "connecting_at_hub"
                 else "connecting_market_over_destination")
    mkt_leg = (mkt_leg / 2.0) if mkt_leg else 0.0
    # BASIS AND YEAR, Jol's review 19 August 2026. The city rows are EACH WAY (the
    # engine's feed detail) while the contract leg is two-way, and the old subtitle
    # compared one against the other ("23,761 of a leg of 54,518" read as 44% shown
    # when the true each-way coverage is 84%). The subtitle now compares each way
    # against each way and says so. The demand-column year was also mislabelled: the
    # engine GROWS the city detail's base and captured to the forecast year
    # (route_forecast ~line 642), so both figure columns are at the SERVICE year,
    # never the base year.
    #
    # ALL-OTHER ROW, 20 August 2026 (Mark Kiehl/SJC, reviewing the three airline packs):
    # the subtitle above disclosed the gap in prose, but the printed TABLE still only
    # summed the fifteen shown rows, so a reader working from the numbers alone (as
    # Mark did: page 43's 112 PTEW against page 45's ~32) reasonably read the detail
    # page as the whole picture. Mirrors the Excel Connecting-feed fix of 19 August:
    # completes the FORECAST and PDEW columns to the carried leg, and now the DEMAND
    # column to the market total above, both with a named tail row.
    shown = sum((x.get("annual_forecast") or 0) for x in cities)
    shown_dem = sum((x.get("annual_demand") or 0) for x in cities)
    leg_ew = (leg / 2.0) if leg else 0.0
    other = (leg_ew - shown) if (leg_ew and leg_ew > shown + 0.5) else 0.0
    other_dem = (mkt_leg - shown_dem) if (mkt_leg and mkt_leg > shown_dem + 0.5) else 0.0
    if other or other_dem:
        rows.append(["", "", "All other connecting markets", "-",
                     (_n(round(other_dem)) if other_dem else "-"), "-",
                     _n(round(other)), _n(round(other / 365.0 / 2.0, 1), 1)])
    rows.append(["", "", "Total", "-",
                 (_n(round(shown_dem + other_dem)) if (shown_dem or other_dem) else "-"), "-",
                 _n(round(shown + other)), _n(round((shown + other) / 365.0 / 2.0, 1), 1)])
    sub = None
    if leg:
        sub = ("The fifteen largest cities, each way: %s passengers; with the tail of smaller "
               "markets, %s passengers, the same carried leg the summary page states"
               % (_n(shown), _n(leg_ew)))
    svc_yr = _g(c, "route_metadata", "service_year")
    return S.table({"head": ["", "Code", "City", "Country",
                             "Annual demand %s" % svc_yr if svc_yr else "Annual demand",
                             "Share captured",
                             "Forecast %s" % svc_yr if svc_yr else "Forecast",
                             "Per day each way"], "rows": rows, "total": True},
                   title=title, subtitle=sub, source=_src(c))


def _method_pages(c, maps=None):
    """Sep 25 slides 36 to 39, and the process figure in front of them. Prose, and every
    claim in it is read from the contract.

    The schedule page carries what the restriction costs, which the 2025 deck could only describe
    in words: its slide 37 says the schedule "seeks to mitigate night curfew restrictions at SJC"
    and states no figure, because none was computed.
    """
    rm = c.get("route_metadata") or {}
    ss = c.get("summary_and_schedule") or {}
    out = [S.divider(number=1, title="The forecast", strap="Methodology", family="operations")]

    # THE PROCESS ON ONE PAGE (John's ask, 19 August 2026, in the same ruling that took the
    # raw k values off the connecting page): the whole engine as a flow, drawn from this
    # run's own contract figures so the boxes sum to the forecast the summary page states.
    # Fail-open like the maps: no figure, no page, never a diagram with invented numbers.
    img = (maps or {}).get("process")
    if img:
        out.append(S.figure(img, title="Forecast methodology",
                            subtitle="How the forecast is built, on this run's own figures",
                            source=_src(c)))

    # "Reached maturity" was 2025-deck language and wrong for Meridian (Jol's challenge,
    # 19 August 2026): the calibration predicts a route's FIRST year, and route_forecast
    # applies no separate ramp because measured maturation on comparable launches (circa
    # +1% to year two, +10% to year three) is the same size as market growth over the
    # period; applying both would double count. Year 1 is the honest, more conservative
    # claim, so the page now makes it.
    base = [(None, "The forecast takes a base year of measured origin and destination demand and "
                   "grows it to the service year. It is a year 1 forecast: the capture calibration "
                   "is built on the first year of observed route launches, and no separate ramp-up "
                   "is applied, because measured maturation on comparable launches (circa +10% by "
                   "year three) is of the same size as market growth over the period, and applying "
                   "both would double count."),
            ("Base and growth",
             "Service year %s. %s" % (rm.get("service_year") or "not stated",
                                      _g(c, "_settings", "growth_basis",
                                         default="Growth basis as reported in the run."))),
            ("Measurement",
             "Passenger demand is measured from Sabre Global Demand Data, which is MIDT adjusted "
             "for bookings made outside the global distribution systems. Schedules and capacity "
             "are measured from OAG.")]
    out.append(S.prose(base, title="Forecast methodology", subtitle="Base demand and growth", source=_src(c)))

    legs = ss.get("schedule") or []
    sched = [(None, "The forecast is built on the schedule below. A schedule is an input, and the "
                    "basis on which this one was set is stated rather than assumed.")]
    for leg in legs:
        if leg.get("sector") and leg.get("sector") != "TOTAL":
            sched.append((leg["sector"], "departs %s, arrives %s, %s, %s"
                          % (leg.get("dep_time") or "-", leg.get("arr_time") or "-",
                             leg.get("operating_days") or "-", leg.get("aircraft") or "-")))
    sched.append(("Basis", ss.get("_schedule_times_need") or "departure time basis not stated"))
    cur = _g(c, "_settings", "curfew_cost")
    if cur:
        # Coerced, because the renderer takes a cryptic TypeError deep inside python-pptx when a
        # non-string reaches a run, and a contract field that changes shape must not be able to
        # bring the render down. This one did on 15 August.
        sched.append(("Night restrictions", cur if isinstance(cur, str) else str(cur)))
    out.append(S.prose(sched, title="Forecast methodology", subtitle="The schedule", source=_src(c)))

    p2p = [(None, "Point to point demand is the measured origin and destination market between the "
                  "two catchments, grown to the service year, stimulated for the new nonstop "
                  "service, and captured at a rate that reflects the frequency offered, the "
                  "alternative routings available and the strength of the operator at both ends."),
           ("Capture", "Capture rate %s of the addressable market."
            % _pct(_g(c, "segment_forecast", "summary", "point_to_point_total", "capture_rate"), 1)),
           ("Catchment", ss.get("catchment_note") or "Catchment as defined in the catchment page.")]
    out.append(S.prose(p2p, title="Forecast methodology", subtitle="Point to point", source=_src(c)))

    cnx = [(None, "Connecting demand is the already-connecting market at each end, captured through "
                  "a quality of service index. The index scores each routing on total elapsed time, "
                  "the type of connection, whether online, interline or within an alliance, and the "
                  "frequency at which the routing is available. Connections shorter than the minimum "
                  "connect time are excluded, as is demand requiring a connection at both ends."),
           ("Level", str(_g(c, "_settings", "feed_level",
                            default="Connecting level as reported in the run."))),
           ("Capture", "Captured at %s over the hub and %s over the origin."
            % (_pct(_g(c, "segment_forecast", "summary", "connecting_at_hub_total", "capture_rate"), 1),
               _pct(_g(c, "segment_forecast", "summary", "connecting_at_destination_total", "capture_rate"), 1)))]
    out.append(S.prose(cnx, title="Forecast methodology", subtitle="Connecting markets", source=_src(c)))
    return out


def _against_prior(c, prior):
    """Sep 25 slide 40. Dropped when there is no previous forecast, never drawn empty."""
    if not prior:
        return None
    def leg(x, *p):
        return _g(x, "segment_forecast", "summary", *p)
    rows = []
    for label, key in (("Point to point", "point_to_point_total"),
                       ("Connecting at the hub", "connecting_at_hub_total"),
                       ("Connecting at the origin", "connecting_at_destination_total"),
                       ("Total", "grand_total")):
        now, was = leg(c, key, "forecast"), leg(prior, key, "forecast")
        delta = ("%+.1f%%" % (100.0 * (now / was - 1.0))) if (now and was) else "-"
        rows.append([label, _n(was), _n(now), delta])
    return S.table({"head": ["", "Previous forecast", "This forecast", "Change"],
                    "rows": rows, "total": True},
                   title="This forecast against the last",
                   subtitle="Previous service year %s against %s"
                            % (_g(prior, "route_metadata", "service_year") or "-",
                               _g(c, "route_metadata", "service_year") or "-"),
                   source=_src(c))


def _route_page(c, maps):
    """The route as a great circle, with the schedule beneath it, as on the 2025 deck.

    Dropped when the map could not be drawn: the schedule already appears in full on the
    methodology page, so a route page without its map would be a duplicate table."""
    img = (maps or {}).get("route")
    if not img:
        return None
    rm = c.get("route_metadata") or {}
    legs = _g(c, "summary_and_schedule", "schedule", default=[]) or []
    rows = [[leg.get("sector") or "", leg.get("dep_time") or "-", leg.get("arr_time") or "-",
             leg.get("operating_days") or "-", leg.get("aircraft") or "-"]
            for leg in legs if leg.get("sector") and leg.get("sector") != "TOTAL"]
    dist = rm.get("distance_nm")
    return S.figure(img,
                    table=({"head": ["Sector", "Departs", "Arrives", "Days", "Aircraft"],
                            "rows": rows} if rows else None),
                    title="The route",
                    subtitle=("Great circle, %s nm" % _n(dist)) if dist else "Great circle",
                    source="Source: OAG schedules, Meridian analysis.")


BAND_LABELS = [("30", "Within 30 minutes' drive"), ("60", "30 to 60 minutes"),
               ("90", "60 to 90 minutes"), ("120", "90 to 120 minutes"),
               ("999", "Beyond 120 minutes, or not routable")]


def _catchment_end_pages(c, maps):
    """One page per route end: the drive-time map and the population it holds, by band.

    THESE ARE THE FIGURES deck_contract line 280 promised and never wired: zone geometry and
    per-band population from the catchment module. The data comes through the contract from
    cortex_app.catchment_profile, the same function the portal's catchment page reads, so the
    deck and the portal can never show two different catchments for one airport."""
    ends = _g(c, "catchment", "ends", default={}) or {}
    if not ends:
        return []
    pages = []
    for side in ("origin", "destination"):
        p = ends.get(side)
        if not isinstance(p, dict) or not p.get("ok"):
            continue
        ap = p.get("airport") or {}
        bands = p.get("bands") or {}
        rows = [[label, _n(bands.get(key))] for key, label in BAND_LABELS
                if bands.get(key) is not None]
        rows.append(["Total within %s km" % _n(p.get("radius_km")), _n(p.get("total_pop"))])
        bullets = []
        if p.get("drive_available"):
            bullets.append("Drive times are least-cost road times from the same friction model "
                           "the forecast uses.")
        else:
            bullets.append("Drive times were not available for this end; population is shown "
                           "within the radius without banding.")
        if p.get("capture") is not None:
            bullets.append("Measured capture of the home catchment: %s (survey and mobility "
                           "data)." % _pct(p.get("capture"), 1))
        img = (maps or {}).get("catchment_%s" % side)
        title = "The catchment at %s" % (ap.get("code") or side)
        sub = "%s, population %s within %s km" % (ap.get("city") or ap.get("code") or "",
                                                  _n(p.get("total_pop")), _n(p.get("radius_km")))
        table = {"head": ["Drive-time band", "Population"], "rows": rows}
        if img:
            pages.append(S.figure(img, table=table, bullets=bullets, title=title, subtitle=sub,
                                  source="Source: GeoNames population, Meridian drive-time "
                                         "model."))
        else:
            pages.append(S.table(table, bullets=bullets, title=title, subtitle=sub,
                                 source="Source: GeoNames population, Meridian drive-time "
                                        "model."))
    return pages


def _catchment(c, maps=None):
    """Sep 25 slide 41. The per-end map pages where the contract carries the ends; the zone
    definitions table where it does not, with the contract's own reason stated."""
    end_pages = _catchment_end_pages(c, maps)
    if end_pages:
        return end_pages
    # A ZONE VALUE IS EITHER A DICT OR A STRING. The contract carries {"definition": "..."} on some
    # zones and a bare string on others, and assuming the first shape threw on the first real run.
    # Keys beginning with an underscore are the contract's own gap notes and are not zones.
    z = _g(c, "catchment", "zones", default={}) or {}
    rows = []
    for k, v in z.items():
        if str(k).startswith("_"):
            continue
        if isinstance(v, dict):
            text = v.get("definition") or v.get("note") or "-"
        else:
            text = str(v) if v else "-"
        rows.append([str(k).replace("_", " ").title(), text])
    need = _g(c, "catchment", "_ends_need")
    fig = _g(c, "catchment", "map_image")
    if fig:
        return [S.figure(fig, title="The catchment",
                         table={"head": ["Zone", "Definition"], "rows": rows} if rows else None,
                         source=_src(c))]
    if not rows:
        return []
    return [S.table({"head": ["Zone", "Definition"], "rows": rows},
                    title="The catchment",
                    subtitle=_g(c, "summary_and_schedule", "catchment_note"),
                    bullets=([("Population by drive band is not on this page: %s" % need)]
                             if need else None),
                    source=_src(c))]


def render_maps(c, out_dir, codename="pack"):
    """The map images the pack references, drawn before the spec is built.

    Returns {"route": path, "catchment_origin": path, "catchment_destination": path}, each key
    present only when its map was actually drawn. Failures are printed with their reason and the
    pages fall back (the route page is dropped, the catchment pages keep their population tables),
    because a pack that cannot draw a map must still be a pack."""
    maps = {}
    try:
        import avia_maps as AM
    except Exception as e:                                   # noqa: BLE001
        print("   MAPS     avia_maps unavailable (%s: %s); no maps on this pack"
              % (type(e).__name__, e))
        return maps
    os.makedirs(out_dir, exist_ok=True)
    stem = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in (codename or "pack"))
    rm = c.get("route_metadata") or {}
    o, d = rm.get("origin_airport"), rm.get("destination_airport")
    ends = _g(c, "catchment", "ends", default={}) or {}

    def _coords(code, side):
        p = ends.get(side) or {}
        ap = p.get("airport") or {}
        if ap.get("lat") is not None and ap.get("lon") is not None:
            return (float(ap["lon"]), float(ap["lat"])), (ap.get("city") or code)
        try:
            import airportsdata
            rec = airportsdata.load("IATA").get(code or "") or {}
            if rec.get("lat") is not None:
                return (float(rec["lon"]), float(rec["lat"])), (rec.get("city") or code)
        except Exception:
            pass
        return None, code

    try:
        oc, oname = _coords(o, "origin")
        dc, dname = _coords(d, "destination")
        if oc and dc:
            maps["route"] = AM.route_map(os.path.join(out_dir, stem + "_route.png"),
                                         origin=oc, destination=dc,
                                         origin_label=oname, destination_label=dname)
    except Exception as e:                                   # noqa: BLE001
        print("   MAPS     route map failed (%s: %s); the route page is dropped"
              % (type(e).__name__, e))
    for side in ("origin", "destination"):
        p = ends.get(side)
        if not isinstance(p, dict) or not p.get("ok"):
            continue
        try:
            maps["catchment_%s" % side] = AM.catchment_end_map(
                os.path.join(out_dir, "%s_catchment_%s.png" % (stem, side)), p)
        except Exception as e:                               # noqa: BLE001
            print("   MAPS     %s catchment map failed (%s: %s); its page keeps the population "
                  "table" % (side, type(e).__name__, e))
    return maps


def render_process(c, out_dir, codename="pack"):
    """The full forecasting process as one figure, every number from this run's contract.

    THE FIGURE IS A SUM THE READER CAN CHECK. Three lanes: the point to point market
    measured, grown and stimulated then captured; the two connecting markets captured
    through the quality of service index. The three captured legs converge on the year 1
    forecast, and the capacity line beneath it shows the seats the schedule offers and
    the load factor the forecast produces. All annual figures are BOTH DIRECTIONS, the
    same basis as the traffic table, so lane ends sum to the total to the passenger.

    Returns the PNG path, or None when a required figure is missing: a process diagram
    with a gap papered over would be worse than no page, so it fails open like the maps.
    """
    ss = _g(c, "segment_forecast", "summary", default={}) or {}
    p2p = ss.get("point_to_point_total") or {}
    hub = ss.get("connecting_at_hub_total") or {}
    dst = ss.get("connecting_at_destination_total") or {}
    gt = ss.get("grand_total") or {}
    sas = c.get("summary_and_schedule") or {}
    rm = c.get("route_metadata") or {}
    need = (p2p.get("base_annual_demand"), p2p.get("demand_after_stimulation"),
            p2p.get("forecast"), hub.get("forecast"), dst.get("forecast"),
            gt.get("forecast"))
    if any(v is None for v in need):
        return None
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyBboxPatch

        NAVY, GREY, LIGHT, RULE = "#1F3864", "#595959", "#F2F4F8", "#C8CDD6"
        base_yr = rm.get("base_year") or _g(c, "_settings", "base_year") or "base year"
        svc_yr = rm.get("service_year") or "service year"
        hub_ap = _g(c, "connecting_at_hub", "hub", default="the hub")
        org_ap = rm.get("origin_airport") or "the origin"
        hub_mkt = sas.get("connecting_market_over_hub") or hub.get("demand_at_service_year")
        dst_mkt = sas.get("connecting_market_over_destination")
        hub_cap = hub.get("capture_rate") or ((hub["forecast"] / hub_mkt) if hub_mkt else None)
        dst_cap = dst.get("capture_rate") or ((dst["forecast"] / dst_mkt) if dst_mkt else None)
        seats = next((l.get("annual_seats") for l in (sas.get("schedule") or [])
                      if l.get("sector") == "TOTAL"), None)
        lf = _g(c, "economics_year1", "total_load_factor")

        def _f(v):
            return "{:,.0f}".format(float(v))

        fig, ax = plt.subplots(figsize=(12.8, 6.0), dpi=170)
        ax.set_xlim(0, 100), ax.set_ylim(0, 60)
        ax.axis("off")
        fig.patch.set_facecolor("white")

        def box(x, y, w, h, label, value, sub=None, accent=False):
            ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=0.8",
                                        facecolor=(NAVY if accent else LIGHT),
                                        edgecolor=(NAVY if accent else RULE), linewidth=1.0))
            ink = "white" if accent else NAVY
            ax.text(x + w / 2, y + h - 2.4, label.upper(), ha="center", va="center",
                    fontsize=7.4, color=("white" if accent else GREY))
            ax.text(x + w / 2, y + h / 2 - 0.6, value, ha="center", va="center",
                    fontsize=(15 if accent else 13.5), fontweight="bold", color=ink)
            if sub:
                ax.text(x + w / 2, y + 2.2, sub, ha="center", va="center",
                        fontsize=7.2, color=("white" if accent else GREY))

        def arrow(x0, y, x1, label=None, below=False):
            ax.annotate("", xy=(x1, y), xytext=(x0, y),
                        arrowprops={"arrowstyle": "-|>", "color": GREY, "lw": 1.1})
            if label:
                # Lane 1's arrows are short, so a label above them lands on the box
                # titles either side; those labels go beneath the arrow instead.
                ax.text((x0 + x1) / 2, (y - 2.0) if below else (y + 1.6), label,
                        ha="center", va=("top" if below else "bottom"),
                        fontsize=7.4, color=GREY)

        W, H = 17.5, 11.5
        y1, y2, y3 = 45, 27.5, 10          # lane centres-ish (box bottoms)
        # lane 1: point to point
        box(2, y1, W, H, "Point to point market %s" % base_yr, _f(p2p["base_annual_demand"]),
            "measured, both directions")
        _g1 = p2p.get("annual_growth_rate")
        _st = p2p.get("stimulation_factor")
        arrow(2 + W + 0.8, y1 + H / 2, 27.2,
              "grown %s,\nstimulated x%.2f" % (("%+.1f%%" % (100 * _g1)) if _g1 is not None
                                               else "to %s" % svc_yr, float(_st or 1.0)),
              below=True)
        box(28, y1, W, H, "Demand at %s after stimulation" % svc_yr,
            _f(p2p["demand_after_stimulation"]))
        arrow(28 + W + 0.8, y1 + H / 2, 53.2,
              "captured %s" % _pct(p2p.get("capture_rate"), 1), below=True)
        box(54, y1, W, H, "Point to point forecast", _f(p2p["forecast"]))
        # lane 2: over the hub
        box(2, y2, W, H, "Connecting market over %s" % hub_ap, _f(hub_mkt) if hub_mkt else "-",
            "at %s, both directions" % svc_yr)
        arrow(2 + W + 0.8, y2 + H / 2, 53.2,
              "captured %s through the quality of service index" % _pct(hub_cap, 1))
        box(54, y2, W, H, "Connecting at %s" % hub_ap, _f(hub["forecast"]))
        # lane 3: over the origin
        box(2, y3, W, H, "Connecting market over %s" % org_ap, _f(dst_mkt) if dst_mkt else "-",
            "at %s, both directions" % svc_yr)
        arrow(2 + W + 0.8, y3 + H / 2, 53.2,
              "captured %s through the quality of service index" % _pct(dst_cap, 1))
        box(54, y3, W, H, "Connecting at %s" % org_ap, _f(dst["forecast"]))
        # convergence to the total
        for yy in (y1, y2, y3):
            ax.annotate("", xy=(78.2, 33.5), xytext=(54 + W + 0.6, yy + H / 2),
                        arrowprops={"arrowstyle": "-|>", "color": GREY, "lw": 1.1,
                                    "connectionstyle": "arc3,rad=0.12"})
        box(79, 28, 19, 16.5, "Year 1 forecast, %s" % svc_yr, _f(gt["forecast"]),
            "passengers, both directions", accent=True)
        if seats and lf is not None:
            ax.text(88.5, 24.5, "Capacity check: %s seats offered,\n%s load factor"
                    % (_f(seats), _pct(lf, 1)), ha="center", va="top",
                    fontsize=8.0, color=GREY)
        ax.text(2, 2.2, "Passengers a year, both directions, year 1 at %s. Markets are before "
                        "capture; the three captured legs sum to the forecast." % svc_yr,
                ha="left", va="center", fontsize=7.6, color=GREY)
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "%s_process.png"
                            % "".join(ch for ch in str(codename) if ch.isalnum() or ch in "-_"))
        fig.savefig(path, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path
    except Exception as e:                                   # noqa: BLE001
        print("   PROCESS  figure failed (%s: %s); the page is dropped"
              % (type(e).__name__, e))
        return None


# --- assembly ---------------------------------------------------------------

def build_pack(contract, *, codename, title=None, prepared_for="", date="",
               confidentiality="Commercial in Confidence", author="Avia Solutions",
               alliance=None, prior=None, maps=None):
    """The spec. Pages that cannot be filled are dropped and the caller is told which.

    THE PAGE LIST IS NAMED, NOT COUNTED. The first version detected drops by slicing the page
    list at fixed indices, so adding one page would have silently misnamed every drop after it.
    Each entry now carries its own name; a page function may also return a LIST of pages (the
    catchment renders one per route end), in which case an empty list is the drop."""
    c = contract
    rm = c.get("route_metadata") or {}
    strap = "%s to %s" % (rm.get("origin_airport") or "", rm.get("destination_airport") or "")
    spec = S.deck(codename=codename, title=title or strap, strap=strap,
                  prepared_for=prepared_for, event="", date=date,
                  confidentiality=confidentiality, author=author)
    meta = {"title": title}
    named = [("cover", _cover(c, meta)),
             ("disclaimer", _disclaimer(prepared_for)),
             ("summary", _summary(c)),
             ("competition", _competition(alliance)),
             ("opportunity", _opportunity(c)),
             ("the route", _route_page(c, maps)),
             ("forecast table", _forecast_table(c)),
             ("connecting at the hub",
              _connecting(c, "connecting_at_hub",
                          "Passengers connecting at %s" % _g(c, "connecting_at_hub", "hub", default="the hub"))),
             ("connecting at the origin",
              _connecting(c, "connecting_at_destination",
                          "Passengers connecting at %s" % (rm.get("origin_airport") or "the origin")))]
    named += [("methodology", p) for p in _method_pages(c, maps)]
    named += [("this forecast against the last", _against_prior(c, prior))]
    named += [("catchment", _catchment(c, maps))]
    dropped, slides = [], []
    for name, p in named:
        if p is None or (isinstance(p, list) and not p):
            dropped.append(name)
        elif isinstance(p, list):
            slides.extend(p)
        else:
            slides.append(p)
    spec["slides"] = slides
    return spec, dropped


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("contract", help="a deck contract JSON, from app/deck_from_cases.py")
    ap.add_argument("--out", default="forecast_pack.pptx")
    ap.add_argument("--codename", default="", help="project codename for the cover")
    ap.add_argument("--title", default="")
    ap.add_argument("--prepared-for", default="")
    ap.add_argument("--date", default="")
    ap.add_argument("--prior", default="", help="a previous contract for the same route; without "
                                                "one the comparison page is dropped")
    ap.add_argument("--alliance", default="", help="alliance seat share JSON; without it the "
                                                   "competition page is dropped")
    ap.add_argument("--safe-fonts", action="store_true")
    a = ap.parse_args()

    with open(a.contract, encoding="utf-8") as f:
        c = json.load(f)
    prior = json.load(open(a.prior, encoding="utf-8")) if a.prior else None
    alliance = json.load(open(a.alliance, encoding="utf-8")) if a.alliance else None

    # The maps are drawn BEFORE the spec is built, because the spec references them by path.
    # They live beside the output so a pack and its imagery travel together.
    _maps_dir = os.path.join(os.path.dirname(os.path.abspath(a.out)) or ".", "pack_maps")
    maps = render_maps(c, _maps_dir, codename=a.codename
                       or _g(c, "route_metadata", "origin_airport", default="pack"))
    # The process figure travels with the maps: same folder, same fail-open rule.
    _proc = render_process(c, _maps_dir, codename=(a.codename or _g(c, "route_metadata",
                                                                    "origin_airport",
                                                                    default="pack")))
    if _proc:
        maps["process"] = _proc
    spec, dropped = build_pack(c, codename=a.codename or _g(c, "route_metadata", "origin_airport", default="Pack"),
                               title=a.title or None, prepared_for=a.prepared_for, date=a.date,
                               alliance=alliance, prior=prior, maps=maps)
    S.paginate(spec)
    problems = S.check(spec)
    print("%d pages" % len(spec["slides"]))
    for d in dropped:
        print("   DROPPED  %s: nothing in the contract to fill it" % d)
    if problems:
        for p in (problems if isinstance(problems, list) else [problems]):
            print("   CHECK    %s" % p)

    # THE IMAGES. The pack rendered with no resolver, so every slot resolved to nothing and the
    # cover and dividers came out blank; the Observatory path passes avia_slots.SlotResolver and
    # its decks carry imagery. Same resolver here, with the origin airport's coordinates so the
    # cover globe is centred on the departure city as it is on an Observatory deck. Failing to
    # build one is not fatal: the pack still renders, and it says the images are missing rather
    # than producing them silently blank, which is how this went unnoticed.
    resolver = None
    try:
        import avia_slots
        origin = _g(c, "route_metadata", "origin_airport", default="")
        ll = None
        try:
            import airportsdata
            ap = (airportsdata.load("IATA").get(origin) or {})
            if ap.get("lat") is not None:
                ll = (ap["lon"], ap["lat"])
        except Exception:
            ll = None
        # THE IMAGERY IS NOT IN THE REPO AND CONFIG SAYS WHERE IT IS. config.py Root 4 was added
        # on 8 August for exactly this: 102MB of Observatory photography, each image carrying a
        # rights determination, living beside the stores rather than bundled. The first version of
        # this looked in deck/ and found nothing, which is why the cover slot reported empty.
        proj = (a.codename or origin or "pack").lower()
        lib = os.path.join(HERE, "observatory_library")
        store = os.path.join(HERE, "image_store")
        uploads = os.path.join(HERE, "uploads", proj)
        try:
            _app = os.path.join(os.path.dirname(HERE), "app")
            if _app not in sys.path:
                sys.path.insert(0, _app)
            import config as CFG
            lib = str(CFG.OBS_LIBRARY_DIR)
            store = str(getattr(CFG, "IMAGE_STORE_DIR", os.path.join(str(CFG.ASSETS_DIR),
                                                                     "image_store")))
            uploads = os.path.join(str(CFG.ENGAGEMENT_ASSETS_DIR), proj)
        except Exception as e:                               # noqa: BLE001
            print("   IMAGES   config did not resolve (%s); falling back to deck/ folders"
                  % type(e).__name__)
        # ONLY THE BRAND LIBRARY IS REQUIRED. The subject store is built by avia_images.py and
        # need not exist; the uploads folder is per project and exists only once somebody has
        # uploaded images for that project. Warning on either would fire on every correct run,
        # and a warning that always fires is one nobody reads. Absent optional folders are passed
        # as None rather than as a path that is not there.
        if not os.path.isdir(lib):
            print("   IMAGES   brand library not found at %s; the cover will be empty" % lib)
        store = store if os.path.isdir(store) else None
        uploads = uploads if os.path.isdir(uploads) else None
        resolver = avia_slots.SlotResolver(uploads_dir=uploads, subject_store=store,
                                           brand_library=lib, project=proj, origin=ll)
    except Exception as e:                                   # noqa: BLE001
        print("   IMAGES   no resolver (%s: %s); the pack will render without imagery"
              % (type(e).__name__, e))

    import render_pptx as RPX
    RPX.render(spec, a.out, safe_fonts=a.safe_fonts, resolver=resolver)
    if resolver is not None:
        try:
            print(resolver.report())
        except Exception:                                    # noqa: BLE001
            pass
    print("wrote %s" % a.out)


if __name__ == "__main__":
    main()
