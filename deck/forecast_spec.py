#!/usr/bin/env python3
"""Turn a deck data contract into the forecast section of a deck spec.

`deck_contract.py` emits the validated contract; `spec_from_research._forecast_slides`
consumes a flatter shape than the contract holds. This is the translation between
them, and it is the reason a generated deck can carry the quantitative core at all
rather than stopping at the research.

Nothing here computes a forecast. Every figure is read from the contract by its own
key, and a key that is absent produces no row rather than a zero. The contract is
the source of record; if a number looks wrong, it is wrong upstream.

Currency is NOT inferred. The contract carries fares and revenues without stating a
currency, so the caller states it and it is written into the column head. Guessing
it would put the wrong symbol in front of every revenue figure on the page.

Avia Solutions Limited. All rights reserved.
"""

# Attribution is a licence obligation, not a house preference: the Sabre work order
# requires attribution where MIDT is a material input, and OAG schedules underpin the
# capture model. Naming only the engine omits the data owners.
# The contractual Sabre name (audit R3; single-sourced in app/attribution.py, carried
# here as a literal because the deck's import path to app/ is not guaranteed).
SOURCE = "Source: OAG schedules; Sabre Global Demand Data; Meridian analysis, The Aviation Observatory."


def _fare_band_label(dem):
    """R5: a measured market fare renders as a band, never the exact figure. Prefers
    the payload's own band; bands a raw figure itself where an older payload carries
    one. The grid is app/fare_bands.py's, carried here as a literal (the deck's import
    path to app/ is not guaranteed): $25 under 500, $50 to 1,500, $100 above. Change
    the grid in BOTH places or in neither."""
    fb = (dem or {}).get("avg_fare_band")
    if isinstance(fb, dict) and fb.get("label"):
        return fb["label"]
    try:
        v = float((dem or {}).get("avg_fare") or 0)
    except (TypeError, ValueError):
        return None
    if v <= 0:
        return None
    w = 25 if v < 500 else 50 if v < 1500 else 100
    lo = int(v // w) * w
    return "%d-%d" % (lo, lo + w)

# 7. A stat row holds five figures before the columns are too narrow for the numbers
# to sit on one line. At ten they split mid-digit, which reads as a broken deck.
MAX_STATS = 5

# How many onward cities the connecting table shows before it stops being readable.
MAX_CNX_CITIES = 12


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------
def _int(n):
    """Whole number with thousands separators. None stays None, never zero."""
    return None if n is None else "{:,}".format(int(round(float(n))))


def _m(n, dp=1):
    """Millions, house form: 12.4m. Under a million falls back to the count."""
    if n is None:
        return None
    n = float(n)
    return ("%.*fm" % (dp, n / 1e6)) if abs(n) >= 1e6 else _int(n)


def _pct(x, dp=1):
    return None if x is None else "%.*f%%" % (dp, float(x) * 100)


def _one_dp(x):
    return None if x is None else "%.1f" % float(x)


def _row(*cells):
    """A table row with absent values shown as a dash, never as a zero.

    Flag rather than fill: a missing figure must read as missing on the page.
    """
    return ["-" if c is None else str(c) for c in cells]


# ---------------------------------------------------------------------------
def _stats(c, currency):
    """The summary slide. Six figures that state the proposition."""
    meta = c.get("route_metadata") or {}
    sched = c.get("summary_and_schedule") or {}
    tot = ((c.get("segment_forecast") or {}).get("summary") or {}).get("grand_total") or {}
    econ = c.get("economics_year1") or {}
    out = []

    def add(label, value, accent=False):
        # A zero is a field the engine did not populate, not a measured zero. It
        # printed as "0" beside "connecting feed" on the proposition slide, on a
        # page where the feed is part of the sell.
        if value not in (None, "", "0", "0.0", "0.0%", "0%"):
            out.append((label, value, accent))

    add("Forecast passengers, each way, year one", _int(tot.get("forecast")), True)
    add("Passengers each way per day", _one_dp(tot.get("pdew")))
    add("Point to point market in the catchment", _m(sched.get("point_to_point_market")))
    add("Connecting market over the hub", _m(sched.get("connecting_market_over_hub")))
    add("Planned load factor", _pct(econ.get("total_load_factor"), 1))
    if econ.get("total_revenue") is not None:
        add("Year one total revenue, %s" % currency, _m(econ.get("total_revenue")), True)
    add("Aircraft and frequency",
        "%s, %s a week" % (meta.get("aircraft_type"), meta.get("frequency_per_week"))
        if meta.get("aircraft_type") else None)
    return out[:MAX_STATS]


def _schedule_table(c):
    rows = (c.get("summary_and_schedule") or {}).get("schedule") or []
    if not rows:
        return None
    return {"head": ["Sector", "Depart", "Arrive", "Days", "Aircraft", "Seats"],
            "rows": [_row(r.get("sector"), r.get("dep_time"), r.get("arr_time"),
                          r.get("operating_days"), r.get("aircraft"),
                          _int(r.get("seats"))) for r in rows],
            "widths": [2.0, 1.2, 1.2, 1.4, 1.4, 1.0]}


def _segments_table(c):
    """The point to point build: market, growth, stimulation, capture, forecast."""
    sf = c.get("segment_forecast") or {}
    rows = sf.get("rows") or []
    if not rows:
        return None
    body = [_row(r.get("segment"), _int(r.get("base_annual_demand")),
                 _int(r.get("demand_at_service_year")),
                 _one_dp(r.get("stimulation_factor")),
                 _pct(r.get("capture_rate"), 1), _int(r.get("forecast")),
                 _one_dp(r.get("pdew"))) for r in rows]
    t = (sf.get("summary") or {}).get("grand_total")
    if t:
        body.append(_row("Total", _int(t.get("base_annual_demand")),
                         _int(t.get("demand_at_service_year")), "",
                         _pct(t.get("capture_rate"), 1), _int(t.get("forecast")),
                         _one_dp(t.get("pdew"))))
    return {"head": ["Segment", "Base market", "At service year", "Stimulation",
                     "Capture", "Forecast", "PDEW"],
            "rows": body, "widths": [2.8, 1.4, 1.5, 1.2, 1.0, 1.2, 0.9]}


def _connecting_table(c):
    """Onward cities over the hub, largest first."""
    ch = c.get("connecting_at_hub") or {}
    cities = sorted((ch.get("cities") or []),
                    key=lambda r: -(r.get("annual_forecast") or 0))[:MAX_CNX_CITIES]
    if not cities:
        return None
    body = [_row(r.get("city_name"), r.get("country"), _int(r.get("annual_demand")),
                 _pct(r.get("airline_share"), 1), _int(r.get("annual_forecast")),
                 _one_dp(r.get("pdew"))) for r in cities]
    t = ch.get("total") or {}
    if t:
        body.append(_row("All onward cities", "", _int(t.get("annual_demand")), "",
                         _int(t.get("annual_forecast")), _one_dp(t.get("pdew"))))
    return {"head": ["Onward city", "Country", "Market", "Share", "Forecast", "PDEW"],
            "rows": body, "widths": [2.2, 1.8, 1.4, 1.0, 1.3, 0.9]}


def _revenue_table(c, currency):
    """Revenue by line and year. Money in millions, passengers in full."""
    rf = c.get("revenue_forecast") or {}
    years = rf.get("years") or []
    if not years:
        return None
    rev = rf.get("revenue") or {}
    pax = rf.get("passengers") or {}
    lines = [("Point to point", rev.get("point_to_point")),
             ("Connecting over the hub", rev.get("connecting_at_hub")),
             ("Connecting beyond the destination", rev.get("connecting_at_destination")),
             ("Cargo", rev.get("cargo")), ("Ancillary", rev.get("ancillary")),
             ("Total revenue", rev.get("total"))]
    body = []
    if pax.get("total"):
        body.append(_row("Passengers, each way",
                         *[_int(v) for v in pax["total"][:len(years)]]))
    for label, series in lines:
        if series:
            body.append(_row(label, *[_m(v) for v in series[:len(years)]]))
    if rf.get("implied_load_factor"):
        body.append(_row("Implied load factor",
                         *[_pct(v, 1) for v in rf["implied_load_factor"][:len(years)]]))
    return {"head": ["%s, %s" % ("Line", currency)] + [str(y) for y in years],
            "rows": body, "widths": [2.6] + [1.0] * len(years)}


def _callouts(c):
    """One or two lines that say what the table means, drawn from the contract."""
    out = []
    tot = ((c.get("segment_forecast") or {}).get("summary") or {}).get("grand_total") or {}
    meta = c.get("route_metadata") or {}
    econ = c.get("economics_year1") or {}
    if tot.get("forecast") and meta.get("aircraft_type"):
        out.append("%s passengers each way in year one on a %s, %s times a week."
                   % (_int(tot["forecast"]), meta["aircraft_type"],
                      meta.get("frequency_per_week", "")))
    if econ.get("total_load_factor"):
        out.append("Planned at %s load factor." % _pct(econ["total_load_factor"], 0))
    return out


# ---------------------------------------------------------------------------
def from_contract(contract, currency="USD", source=SOURCE):
    """The forecast argument for spec_from_research.build_spec.

    `currency` is stated by the caller, following the asset's home jurisdiction,
    and is written into the revenue column head. It is never inferred here.
    """
    c = contract or {}
    return {
        "summary": {"stats": _stats(c, currency),
                    "schedule": _schedule_table(c),
                    "callouts": _callouts(c)},
        "segments": _segments_table(c),
        "connecting_hub": _connecting_table(c),
        "revenue": _revenue_table(c, currency),
        "source": source,
    }


# ---------------------------------------------------------------------------
# The live engine's own output
# ---------------------------------------------------------------------------
# calibrated_forecast returns a different shape from deck_contract. Rather than
# bridge one pipeline into the other, which would mean re-deriving figures the
# engine has already computed, the engine's output is mapped straight onto the
# same forecast slides. Each figure is read by its own key; anything ambiguous is
# left out and named in describe() rather than guessed at.

def _fc_stats(fc, currency):
    dem = fc.get("demand") or {}
    cap = fc.get("capacity") or {}
    out = []

    def add(label, value, accent=False):
        # A zero is a field the engine did not populate, not a measured zero. It
        # printed as "0" beside "connecting feed" on the proposition slide, on a
        # page where the feed is part of the sell.
        if value not in (None, "", "0", "0.0", "0.0%", "0%"):
            out.append((label, value, accent))

    add("Forecast passengers, each way, year one", _int(dem.get("total")), True)
    add("Passengers each way per day", _one_dp(dem.get("pdew_total")))
    add("Point to point market in the catchment", _m(dem.get("natural")))
    add("Captured by the nonstop", _pct(dem.get("qsi_share"), 1))
    add("Connecting feed behind the origin", _int(dem.get("feed_behind")))
    add("Connecting feed beyond the destination", _int(dem.get("feed_beyond")))
    add("Planned load factor", _pct(cap.get("load"), 1))
    add("Aircraft and frequency",
        "%s, %s a week" % (cap.get("aircraft"), cap.get("freq"))
        if cap.get("aircraft") else None)
    fl = _fare_band_label(dem)
    if fl:
        add("Measured one-way market fare, %s" % currency, fl)
    return out[:MAX_STATS]


def _fc_schedule(fc, show_indicative_times=False):
    """The schedule shape. Times are NOT shown unless they have been optimised.

    _schedule_times departs the origin at 11:00 local on every route in the tool and
    turns the aircraft two hours later. The times are a shape, not a recommendation,
    and fc["schedule"]["indicative"] says so. Printing them on a client-facing page
    invites a network planner to read a placeholder as a proposal, and departure time
    is the one input that decides which connections at either end are reachable.

    Set show_indicative_times only once the optimiser searches time of day. Until
    then the table carries the sectors and the frequency, which are real.
    """
    s = fc.get("schedule") or {}
    legs = [l for l in (s.get("outbound"), s.get("inbound")) if l]
    if not legs:
        return None
    cap = fc.get("capacity") or {}
    timed = show_indicative_times or not s.get("indicative", True)
    if timed:
        return {"head": ["Sector", "Depart", "Arrive", "Frequency", "Aircraft"],
                "rows": [_row(l.get("sector"), l.get("dep"), l.get("arr"),
                              "%s a week" % cap.get("freq"), cap.get("aircraft"))
                         for l in legs],
                "widths": [1.8, 1.1, 1.1, 1.4, 1.3]}
    return {"head": ["Sector", "Frequency", "Aircraft", "Block time"],
            "rows": [_row(l.get("sector"), "%s a week" % cap.get("freq"),
                          cap.get("aircraft"),
                          "%s h %s" % divmod(int(s.get("block_min") or 0), 60)
                          if s.get("block_min") else None)
                     for l in legs],
            "widths": [2.0, 1.4, 1.4, 1.2]}


# The five volume rows the demand chart draws. Where the chart is on the page the
# table drops them, because a figure that repeats the table beside it is the
# house rule's own example of a figure that has not earned its place. Where the
# chart did not draw, the table carries the full build, and the caller reports
# that it reverted rather than leaving the reader to notice a shorter table.
_CHART_ROWS = ("natural", "p2p_carried", "feed_behind", "feed_beyond", "total")


def _fc_segments(fc, charted=False):
    """The demand build, in the order the engine computes it.

    charted   True when deck_figures drew the demand chart for this run, which
              moves the five volume rows onto the chart and leaves the table
              carrying the mechanics: what flies today, what stimulation and
              share were applied, and what the aircraft cannot take.
    """
    dem = fc.get("demand") or {}
    cap = fc.get("capacity") or {}
    rows = [
        ("natural", "Point to point market in the catchment, each way",
         _int(dem.get("natural"))),
        ("current", "Travelling via the origin airport today",
         _int(dem.get("current"))),
        ("stimulation", "Stimulation applied", _one_dp(dem.get("stimulation"))),
        ("qsi_share", "Share captured by the nonstop", _pct(dem.get("qsi_share"), 1)),
        ("p2p_carried", "Point to point carried", _int(dem.get("p2p_carried"))),
        ("feed_behind", "Connecting feed behind the origin", _int(dem.get("feed_behind"))),
        ("feed_beyond", "Connecting feed beyond the destination", _int(dem.get("feed_beyond"))),
        ("total", "Total carried, each way", _int(dem.get("total"))),
        ("spill", "Spill", _int(cap.get("spill"))),
        ("annual_capacity", "Annual capacity", _int(cap.get("annual_capacity"))),
    ]
    if charted:
        rows = [r for r in rows if r[0] not in _CHART_ROWS]
    body = [_row(b, c) for _k, b, c in rows if c is not None]
    if not body:
        return None
    head = "How the build works" if charted else "The demand build"
    return {"head": [head, "Each way per year"], "rows": body,
            "widths": [4.2, 1.6],
            "title": "How the build works" if charted else "Point to point demand"}


def _fc_connecting(fc):
    """Onward markets beyond the destination, which is the connecting story."""
    rows = sorted((fc.get("demand") or {}).get("beyond_pdew") or [],
                  key=lambda r: -(r.get("pdew") or 0))[:MAX_CNX_CITIES]
    if not rows:
        return None
    body = [_row(r.get("name") or r.get("code"), r.get("country"),
                 _one_dp(r.get("pdew")),
                 _int((r.get("pdew") or 0) * 365)) for r in rows]
    return {"head": ["Onward city", "Country", "PDEW", "Each way per year"],
            "rows": body, "widths": [2.2, 1.8, 1.0, 1.5]}


def from_forecast(fc, currency="USD", source=SOURCE, charted=False):
    """The forecast argument, straight from calibrated_forecast output.

    No revenue table: the economics block mixes per-turn and annual figures under
    names that do not state which, and putting the wrong one on a slide is worse
    than leaving the table out. describe() names it as missing so the run says so.

    charted   True when the demand chart was drawn for this run, which takes the
              five volume rows out of the segments table. See _fc_segments.
    """
    fc = fc or {}
    return {
        "summary": {"stats": _fc_stats(fc, currency),
                    "schedule": _fc_schedule(fc),
                    "callouts": _fc_callouts(fc),
                    "basis": _basis_note(fc),
                    "basis_range": basis_range(fc)},
        "segments": _fc_segments(fc, charted=charted),
        "connecting_hub": _fc_connecting(fc),
        "revenue": None,
        "source": source,
    }


# The callout slot holds 58 characters. The long form of the summary callout
# runs to 65 on a six-figure forecast, which is every route the tool is aimed at,
# so it overprinted the slot rather than fitting it. Two forms, and the short one
# is used where the long one will not fit. Both state the same three facts.
CALLOUT_CHARS = 58


def _article(word):
    """'an A21X', not 'a A21X'. Sounded letters, not written vowels: an A, an
    E, an F, an H, an I, an L, an M, an N, an O, an R, an S and an X all open
    with a vowel sound when spoken as a letter, which is how a type code reads.
    """
    w = str(word or "").strip()
    if not w:
        return "a"
    first = w[0].upper()
    if w[:2].isupper() or first.isdigit():        # a code, read out letter by letter
        return "an" if first in "AEFHILMNORSX8" else "a"
    return "an" if first in "AEIOU" else "a"


def _fc_callouts(fc):
    dem = fc.get("demand") or {}
    cap = fc.get("capacity") or {}
    out = []
    if dem.get("total") and cap.get("aircraft"):
        ac, freq = cap["aircraft"], cap.get("freq", "")
        long = ("%s passengers each way in year one on %s %s, %s times a week."
                % (_int(dem["total"]), _article(ac), ac, freq))
        short = ("%s each way in year one, %s %s, %s a week."
                 % (_int(dem["total"]), _article(ac), ac, freq))
        out.append(long if len(long) <= CALLOUT_CHARS else short)
    if cap.get("recommendation"):
        out.append(str(cap["recommendation"]))
    return out


def _basis_note(fc):
    """What KIND of forecast this is, in the client's own document.

    THE RULE, John 7 August: the deck is built from whatever run the user just
    did. If they ran the route with no airline, that is their choice and they may
    have a reason; the report still gets generated. Nothing here decides what to
    forecast. It states the basis of the forecast it was handed, so the reader
    knows which question was answered.

    Two things change the answer materially and neither was on any slide:

      THE AIRLINE. With no carrier in the model there is no network behind the
      route, so the connecting feed is zero and the number is the local market
      alone. The dashboard has said this since it was built ("The market on its
      own"); the deck did not. On EDI to AUS the two readings were 21,865 each
      way with no airline and 8,720 with Delta, of which 6,181 was feed.

      THE MARKET. On a new market the engine floors demand at the capacity
      deployed and models it from comparable launches rather than measuring
      traffic that already flies.

    This is not the counter-case, which belongs in the internal annex. It is the
    basis of Avia's own number, and a forecast that does not say whether it is
    measured or modelled, and for whom, is not finished.
    """
    dem = fc.get("demand") or {}
    conf = fc.get("confidence") or {}
    opt = fc.get("optimised") or {}
    airline = (fc.get("airline") or opt.get("airline") or "").strip()
    bits = []

    if airline:
        bits.append("This forecast is for %s flying the route, on their own "
                    "connections at both ends. A different airline returns a "
                    "different number, because a different network fills the "
                    "aircraft differently." % airline)
        if opt.get("season") and opt["season"] != "annual":
            bits.append("The schedule is a %s service." % opt["season"])
    else:
        bits.append("This forecast has no airline in it, so there is no network "
                    "behind the route and no connecting traffic: it is what a "
                    "nonstop carries from the local market on its own. Naming a "
                    "carrier changes the number, because their connections change "
                    "what the route can fill.")

    if dem.get("induced"):
        bits.append("The route is a new market, so it is modelled from "
                    "comparable launches rather than measured from traffic "
                    "that already flies.")
        nat = dem.get("natural")
        if nat:
            bits.append("The measured point to point market today is %s each way."
                        % _int(nat))
    return " ".join(bits)


def basis_range(fc):
    """The confidence range, for the callout beside the basis prose.

    It sat in the body and pushed that slide to 541 characters against a 430
    budget. A range is a number, and a number on an Avia page belongs in the
    callout rather than buried in the fourth sentence of a paragraph.
    """
    conf = (fc or {}).get("confidence") or {}
    if not (conf.get("low") and conf.get("high")):
        return ""
    return ["Range %s to %s each way." % (_int(conf["low"]), _int(conf["high"])),
            "Covering %s." % (conf.get("coverage")
                              or "about 2 in 3 comparable launches")]


def headline_from_forecast(fc):
    """The forecast in one sentence, for the writing pass to quote exactly."""
    dem = (fc or {}).get("demand") or {}
    cap = (fc or {}).get("capacity") or {}
    if not dem.get("total"):
        return ""
    bits = ["Avia forecasts %s passengers each way in year one" % _int(dem["total"])]
    if dem.get("pdew_total"):
        bits.append("%s passengers each way per day" % _one_dp(dem["pdew_total"]))
    if cap.get("aircraft") and cap.get("freq"):
        bits.append("on a %s operating %s times a week" % (cap["aircraft"], cap["freq"]))
    if cap.get("load"):
        bits.append("at a planned load factor of %s" % _pct(cap["load"], 0))
    return ", ".join(bits) + "."


def headline_sentence(contract):
    """The forecast in one sentence, for the writing pass to quote exactly.

    The writing pass may not introduce a figure of its own, so the forecast has to
    reach it as text. Every number here is read from the contract.
    """
    c = contract or {}
    meta = c.get("route_metadata") or {}
    tot = ((c.get("segment_forecast") or {}).get("summary") or {}).get("grand_total") or {}
    econ = c.get("economics_year1") or {}
    if not tot.get("forecast"):
        return ""
    bits = ["Avia forecasts %s passengers each way in year one" % _int(tot["forecast"])]
    if tot.get("pdew"):
        bits.append("%s passengers each way per day" % _one_dp(tot["pdew"]))
    if meta.get("aircraft_type") and meta.get("frequency_per_week"):
        bits.append("on a %s operating %s times a week"
                    % (meta["aircraft_type"], meta["frequency_per_week"]))
    if econ.get("total_load_factor"):
        bits.append("at a planned load factor of %s" % _pct(econ["total_load_factor"], 0))
    return ", ".join(bits) + "."


def assumptions_from_forecast(fc):
    """The inputs a reader has to be able to challenge. Every one read from fc."""
    dem = (fc or {}).get("demand") or {}
    cap = (fc or {}).get("capacity") or {}
    rows = [
        ("Aircraft", cap.get("aircraft")),
        ("Frequency", "%s a week" % cap.get("freq") if cap.get("freq") else None),
        ("Planned load factor", _pct(cap.get("load"), 1)),
        ("Stimulation applied to the market", _one_dp(dem.get("stimulation"))),
        ("Share of the catchment market captured", _pct(dem.get("qsi_share"), 1)),
        ("Attractiveness exponent", _one_dp(dem.get("att"))),
        ("Measured one-way market fare (band)", _fare_band_label(dem)),
        ("Induced market treatment", "applied" if dem.get("induced") else "not applied"),
        ("Season", ((fc or {}).get("season") or {}).get("mode")),
        ("Base year for the market data", str((fc or {}).get("year") or "") or None),
    ]
    return [(a, b) for a, b in rows if b not in (None, "")]


def assumptions_from_contract(c):
    meta = (c or {}).get("route_metadata") or {}
    econ = (c or {}).get("economics_year1") or {}
    rows = [
        ("Aircraft", meta.get("aircraft_type")),
        ("Seats", _int(meta.get("seats"))),
        ("Frequency", "%s a week" % meta.get("frequency_per_week")
         if meta.get("frequency_per_week") else None),
        ("Service year", str(meta.get("service_year") or "") or None),
        ("Planned load factor", _pct(econ.get("total_load_factor"), 1)),
        ("Average one-way fare, point to point", _int(econ.get("avg_ow_fare_point_to_point"))),
        ("Average one-way fare, connecting", _int(econ.get("avg_ow_fare_connecting"))),
        ("Sector distance", "%s nm" % _int(meta.get("distance_nm"))
         if meta.get("distance_nm") else None),
    ]
    return [(a, b) for a, b in rows if b not in (None, "")]


def describe(fcspec):
    """What made it through, for the run report. Absent tables are named."""
    missing = [k for k in ("segments", "connecting_hub", "revenue") if not fcspec.get(k)]
    s = fcspec.get("summary") or {}
    return {"stats": len(s.get("stats") or []),
            "schedule_rows": len((s.get("schedule") or {}).get("rows") or []),
            "tables_missing": missing}


if __name__ == "__main__":
    import json
    import os
    import sys
    # The contract sits beside this module. The previous default went two levels up, which
    # was wrong before the renderer moved as well as after it, and only showed up here
    # because this is a command-line demo path with an argv override.
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "ba_lhr_sjc_deck_contract.json")
    with open(path, encoding="utf-8") as fh:
        spec = from_contract(json.load(fh), currency=sys.argv[2] if len(sys.argv) > 2 else "USD")
    print(json.dumps(describe(spec), indent=1))
    for k in ("segments", "connecting_hub", "revenue"):
        t = spec.get(k)
        if t:
            print("\n%s: %s" % (k, t["head"]))
            for r in t["rows"][:4]:
                print("   ", r)


# ---------------------------------------------------------------------------
# Commercial viability of the schedule as entered (John, 7 August 2026)
# ---------------------------------------------------------------------------
# A deck that prints a 38% planned load factor argues against its own route: no
# airline flies a transatlantic narrowbody at that fill, and a network planner
# reading it concludes the service fails as proposed. The forecast is not the
# problem, the fixed frequency is. This does not block anything, because a client
# is entitled to print the schedule they asked for, but it says so before they do
# and it says what the demand would actually support.

# The check itself now lives in app/schedule_viability.py, beside the engine, so
# that the dashboard banner and the deck runner read the same implementation and
# cannot drift apart. This is the deck-side entry point and nothing more.

try:
    from schedule_viability import (schedule_viability, VIABLE_LF,  # noqa: F401
                                    MARGINAL_LF, PLANNING_LF)      # noqa: F401
except ImportError as _e:                                          # pragma: no cover
    _VIABILITY_IMPORT_ERROR = str(_e)
    VIABLE_LF, MARGINAL_LF, PLANNING_LF = 0.65, 0.75, 0.80

    def schedule_viability(fc, min_lf=VIABLE_LF, target=PLANNING_LF):
        """The module is not on the path. Say so; do not pass silently.

        A silent None here reads as "the schedule is fine", which is the exact
        failure the check exists to prevent. The runner prints this and the
        audit carries it.
        """
        return {"band": "CHECK NOT RUN", "load_factor": None, "frequency": None,
                "sized_frequency": None,
                "message": "The schedule viability check did not run: %s. "
                           "app/ is not on sys.path for this process, so the "
                           "load factor has NOT been assessed."
                           % _VIABILITY_IMPORT_ERROR,
                "question": ""}
