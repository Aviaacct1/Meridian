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

DISCLAIMER = (
    "This forecast has been prepared by Avia Solutions Limited for the party named on the cover and "
    "for the purpose stated in it. It rests on data licensed to Avia Solutions and on assumptions "
    "stated in the methodology pages that follow. Forecasts are estimates and outturn will differ. "
    "No part of this document may be reproduced or relied upon by any other party without the "
    "written consent of Avia Solutions Limited.")

SRC = "Source: AviaSolutions analysis (Avia Cortex), Sabre MI and OAG schedules."


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
        read = ("US DOT O&D Survey (DB1B) for the US domestic markets, Sabre MI for the rest, "
                "and OAG schedules")
    return "Source: AviaSolutions analysis (Avia Cortex), %s." % read


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


def _disclaimer():
    return S.prose([(None, DISCLAIMER)], title="Basis of this document",
                   source="Avia Solutions Limited. All rights reserved.")


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
             ("Planned load factor", _pct(e1.get("total_load_factor"), 1), True)]
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
                   source="Source: OAG schedules, AviaSolutions analysis.")


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
    return S.keynumbers(items, title="The opportunity",
                        subtitle=("Addressable market at %s, before stimulation and before capture" % yr)
                                 if yr else "Addressable market before stimulation and before capture",
                        source=(ss.get("catchment_note") or _src(c)))


def _forecast_table(c):
    """Sep 25 slide 32, in its own column order: market, capture, forecast, per trip.

    THE COLUMNS ARE THE 2025 DECK'S, not ours, because a client who has seen that table should be
    able to read this one without being taught it. Where the payload cannot fill a column it is
    left as a dash rather than dropped, so the shape is recognisable.
    """
    ss = _g(c, "segment_forecast", "summary", default={})
    dep = _g(c, "economics_year1", "total_departures_annual_two_way")

    def row(label, blk):
        fc = blk.get("forecast")
        ptew = (fc / dep) if (fc and dep) else None
        return [label, _k(blk.get("base_annual_demand")), _k(blk.get("demand_after_stimulation")),
                _pct(blk.get("capture_rate"), 1), _k(fc), _n(ptew, 0)]

    rows = [row("Total point to point", ss.get("point_to_point_total") or {}),
            row("Connecting at %s" % _g(c, "connecting_at_hub", "hub", default="the hub"),
                ss.get("connecting_at_hub_total") or {}),
            row("Connecting at %s" % _g(c, "route_metadata", "origin_airport", default="the origin"),
                ss.get("connecting_at_destination_total") or {}),
            row("Grand total", ss.get("grand_total") or {})]
    rm = c.get("route_metadata") or {}
    return S.table({"head": ["Market", "Base annual demand (000s)", "After stimulation (000s)",
                             "Capture rate", "Forecast traffic (000s)", "Per trip each way"],
                    "rows": rows, "total": True},
                   title="Traffic forecast",
                   subtitle="%s weekly, year 1 at %s" % (_n(rm.get("frequency_per_week")),
                                                         rm.get("service_year") or "maturity"),
                   bullets=["Passengers per trip each way. Demand on double connections is excluded.",
                            _g(ss, "grand_total", "_basis",
                               default="carried, after the plan load factor cap")],
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
    rows = [[str(x.get("nr") or i + 1), x.get("city_name") or x.get("city_code") or "",
             x.get("country") or "", _n(x.get("annual_demand")), _pct(x.get("airline_share"), 1),
             _n(x.get("annual_forecast")), _n(x.get("pdew"), 1)]
            for i, x in enumerate(cities)]
    leg = _g(c, "segment_forecast", "summary",
             "connecting_at_hub_total" if key == "connecting_at_hub" else "connecting_at_destination_total",
             "forecast")
    sub = None
    if leg:
        shown = sum((x.get("annual_forecast") or 0) for x in cities)
        sub = ("The fifteen largest cities, %s passengers of a leg of %s"
               % (_n(shown), _n(leg)))
    return S.table({"head": ["", "City", "Country", "Annual demand", "Share captured",
                             "Forecast", "Per day each way"], "rows": rows},
                   title=title, subtitle=sub, source=_src(c))


def _method_pages(c):
    """Sep 25 slides 36 to 39. Prose, and every claim in it is read from the contract.

    The schedule page carries what the restriction costs, which the 2025 deck could only describe
    in words: its slide 37 says the schedule "seeks to mitigate night curfew restrictions at SJC"
    and states no figure, because none was computed.
    """
    rm = c.get("route_metadata") or {}
    ss = c.get("summary_and_schedule") or {}
    out = [S.divider(number=1, title="The forecast", strap="Methodology", family="operations")]

    base = [(None, "The forecast takes a base year of measured origin and destination demand and "
                   "grows it to the service year, at which the route is assumed to have reached "
                   "maturity."),
            ("Base and growth",
             "Service year %s. %s" % (rm.get("service_year") or "not stated",
                                      _g(c, "_settings", "growth_basis",
                                         default="Growth basis as reported in the run."))),
            ("Measurement",
             "Passenger demand is measured from Sabre MI, which is MIDT adjusted for bookings made "
             "outside the global distribution systems. Schedules and capacity are measured from OAG.")]
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
        sched.append(("Night restrictions", cur))
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
           ("Level", _g(c, "_settings", "feed_level",
                        default="Connecting level as reported in the run.")),
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


def _catchment(c):
    """Sep 25 slide 41. The map where one has been drawn, the zone definitions where it has not."""
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
    fig = _g(c, "catchment", "map_image")
    if fig:
        return S.figure(fig, title="The catchment",
                        table={"head": ["Zone", "Definition"], "rows": rows} if rows else None,
                        source=_src(c))
    if not rows:
        return None
    return S.table({"head": ["Zone", "Definition"], "rows": rows},
                   title="The catchment",
                   subtitle=_g(c, "summary_and_schedule", "catchment_note"),
                   source=_src(c))


# --- assembly ---------------------------------------------------------------

def build_pack(contract, *, codename, title=None, prepared_for="", date="",
               confidentiality="Commercial in Confidence", author="Avia Solutions",
               alliance=None, prior=None):
    """The spec. Pages that cannot be filled are dropped and the caller is told which."""
    c = contract
    rm = c.get("route_metadata") or {}
    strap = "%s to %s" % (rm.get("origin_airport") or "", rm.get("destination_airport") or "")
    spec = S.deck(codename=codename, title=title or strap, strap=strap,
                  prepared_for=prepared_for, event="", date=date,
                  confidentiality=confidentiality, author=author)
    meta = {"title": title}
    pages = [_cover(c, meta), _disclaimer(), _summary(c), _competition(alliance), _opportunity(c),
             _forecast_table(c),
             _connecting(c, "connecting_at_hub",
                         "Passengers connecting at %s" % _g(c, "connecting_at_hub", "hub", default="the hub")),
             _connecting(c, "connecting_at_destination",
                         "Passengers connecting at %s" % (rm.get("origin_airport") or "the origin"))]
    pages += _method_pages(c)
    pages += [_against_prior(c, prior), _catchment(c)]
    dropped = []
    for name, p in zip(["cover", "disclaimer", "summary", "competition", "opportunity",
                        "forecast table", "connecting at the hub", "connecting at the origin"],
                       pages[:8]):
        if p is None:
            dropped.append(name)
    if pages[-2] is None:
        dropped.append("this forecast against the last")
    if pages[-1] is None:
        dropped.append("catchment")
    spec["slides"] = [p for p in pages if p is not None]
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

    spec, dropped = build_pack(c, codename=a.codename or _g(c, "route_metadata", "origin_airport", default="Pack"),
                               title=a.title or None, prepared_for=a.prepared_for, date=a.date,
                               alliance=alliance, prior=prior)
    S.paginate(spec)
    problems = S.check(spec)
    print("%d pages" % len(spec["slides"]))
    for d in dropped:
        print("   DROPPED  %s: nothing in the contract to fill it" % d)
    if problems:
        for p in (problems if isinstance(problems, list) else [problems]):
            print("   CHECK    %s" % p)

    import render_pptx as RPX
    RPX.render(spec, a.out, safe_fonts=a.safe_fonts)
    print("wrote %s" % a.out)


if __name__ == "__main__":
    main()
