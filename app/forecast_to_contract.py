"""The join between the live forecast and the Observatory deck, which has never existed.

WHAT WAS MISSING. The 40-page Observatory deck is built and the forecast is built, and nothing
connected them. run_observatory_pitch.py says so in its own docstring: "deck_contract.py is not yet
wired into the connector, so the fc handed in here carries route identity and placeholder demand
only. Nothing in the deck reads a number from it." Everything downstream of the contract already
works: deck_contract.build_contract emits it, forecast_spec turns it into slides, and
spec_from_research renders them. The break is at this one join, and deck_contract still expects the
shape assess.py produced in the June chain rather than the payload calibrated_forecast returns.

    from forecast_to_contract import contract_from_forecast
    fc = cortex_app.calibrated_forecast("SJC", "TPE", airline="CI", aircraft="A359", seats=306,
                                        freq=4, forecast_year=2028, growth=0.07,
                                        partner_carriers=["WN"], with_econ=True)
    contract = contract_from_forecast(fc, currency="USD")

NOTHING HERE COMPUTES A FORECAST. Every figure is read from the payload by its own key and mapped
to the contract's own key. A key that is absent produces None rather than a zero, because a zero
reads as a measurement and a None reads as a gap.

THE THREE MAPPINGS THAT ARE NOT OBVIOUS, stated here rather than discovered later. Each of them is
the shape of an error this programme has already paid for.

  CARRIED AGAINST DEMAND. The payload carries BOTH: demand.total is CARRIED each way, after the
  87.5% plan cap, and demand.total_demand is uncapped demand each way. CAPPED-VS-UNCAPPED of 12
  August records a claim quoted for a week that compared one against the other. The contract's
  directional_demand takes the CARRIED figure, because the P&L downstream is built on passengers
  who fly, and the uncapped figure is carried alongside as demand_uncapped_ew so the two can never
  be confused again.

  SEATS. deck_contract._seats_for falls back to the generic AIRCRAFT table, where the A350-900 is
  336 seats. China Airlines flies it at 306. Sizing the deck on the generic figure would overstate
  capacity by 8 to 13% on exactly the carriers in the SJC-TPE set, so the actual seat count from the
  forecast is passed as a cabin_config and the type table's own business fraction is scaled to it.

  EACH WAY AGAINST TWO WAY. The payload is EACH WAY throughout; scenario_runner doubles for its own
  table. The contract takes each-way figures, so nothing is doubled here, and every key this module
  writes ends _ew where it could be mistaken.

Avia Solutions Limited. All rights reserved.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# deck_contract lives in the deck generator folder, whose name carries a space. Found by path
# rather than by an import hook, and named loudly if it is not there, because a silent fallback to
# a hand-built contract is how a deck ends up describing a route nobody forecast.
_GEN = os.path.join(os.path.dirname(HERE), "Deck Generator")
if _GEN not in sys.path:
    sys.path.insert(0, _GEN)


def _need(fc):
    """Everything this module reads, checked once and named together rather than failing one at a
    time three frames down. Returns a list of what is missing."""
    miss = []
    if not fc.get("ok"):
        miss.append("the forecast did not succeed: %s" % fc.get("error", "no reason given"))
        return miss
    if not fc.get("economics_ok"):
        miss.append("economics unavailable, so the P&L blocks cannot be built: %s"
                    % fc.get("economics_error", "no reason given"))
    for k in ("demand", "capacity", "origin", "dest", "distance_nm"):
        if k not in fc:
            miss.append("payload has no %r" % k)
    return miss


def case_and_outputs(fc):
    """The two dicts deck_contract.build_contract takes, mapped from the live payload.

    Returned separately from the contract itself so a caller can inspect or override the mapping
    before it is used, and so the mapping can be tested without building a deck.
    """
    dem, cap = fc["demand"], fc["capacity"]
    o, d = fc["origin"], fc["dest"]
    sch = fc.get("schedule") or {}
    ec = fc.get("economics") or {}

    # SEATS: the forecast's own figure, not the type table's. See the docstring.
    seats_total = cap.get("seats")
    cabin_config = None
    if seats_total:
        try:
            from aircraft_economics import AIRCRAFT as _AC
            _t = _AC.get(cap.get("aircraft")) or {}
            _tb, _tc = float(_t.get("bus_seats", 0)), float(_t.get("econ_seats", 0))
            _tt = _tb + _tc
            # The type's business FRACTION applied to the carrier's actual total. The split is the
            # type's and the total is the carrier's, which is the honest combination when the LOPA
            # is not known: it never contradicts the seat count the forecast was run on.
            _b = round(seats_total * (_tb / _tt)) if _tt else 0
            cabin_config = {"business": _b, "premium_coach": 0, "coach": int(seats_total) - _b}
        except Exception:                                    # noqa: BLE001
            cabin_config = {"business": 0, "premium_coach": 0, "coach": int(seats_total)}

    case = {
        "aircraft": cap.get("aircraft"),
        "cabin_config": cabin_config,
        "sector_nm": fc.get("distance_nm"),
        "home": o.get("iata") or o.get("code"),
        "primary_dest": d.get("iata") or d.get("code"),
        "hub_airport": d.get("iata") or d.get("code"),       # the destination IS the hub on a feed route
        "service_year": sch.get("forecast_year") or fc.get("year"),
        "frequency": cap.get("freq"),
        # route_metadata reads these three by their own names and they were empty on every case.
        # There is no IATA metro code in the payload, so the airport code stands in and is named as
        # doing so: a deck that prints the airport where a city code belongs is right far more often
        # than not, and a blank is wrong every time.
        "airline_iata": fc.get("airline"),
        "airline": fc.get("airline"),
        "origin_city_code": o.get("city_code") or o.get("iata") or o.get("code"),
        "destination_city_code": d.get("city_code") or d.get("iata") or d.get("code"),
        "origin_city": o.get("city"),
        "dest_city": d.get("city"),
        # block_hours_per_departure is computed by deck_contract as case["block_min"]/60 and the
        # payload has carried block_min all along. It was empty only because nothing passed it.
        "block_min": fc.get("block_min"),
    }

    outputs = {
        "natural": dem.get("natural"),
        "current": dem.get("current"),
        "capture": dem.get("qsi_share"),
        # CARRIED, not uncapped. The uncapped figure travels beside it under its own name.
        "directional_demand": dem.get("total"),
        "demand_uncapped_ew": dem.get("total_demand"),
        "p2p_carried_ew": dem.get("p2p_carried"),
        "connecting_carried_ew": dem.get("connecting_carried"),
        "feed_total_ew": dem.get("feed_total"),
        # THE P2P LEG BEFORE THE CAP, added 14 August 2026 so the contract's
        # point_to_point_total can state a demand and a carried figure that are the same leg.
        # captured_demand is the local market after stimulation and after the bucket correction,
        # which is demand_after_stimulation in the contract's own vocabulary. There is no
        # pre-stimulation figure in the payload, so demand_at_service_year stays a named gap
        # rather than being filled with the nearest number to hand.
        "p2p_demand_ew": dem.get("captured"),
        # The two feed sides SEPARATELY, because the contract splits the connecting leg between a
        # hub table and a destination table and had no figure to split it on. These are pre-cap, so
        # they are used as a RATIO and never as a level.
        "feed_beyond_ew": dem.get("feed_beyond"),
        "feed_behind_ew": dem.get("feed_behind"),
        "frequency": cap.get("freq"),
        "econ_lf": ec.get("econ_lf"),
        "bus_lf": ec.get("bus_lf"),
        # THE ECONOMICS BLOCK IS PER TURN, established from cortex_app rather than assumed: it
        # builds charges_per_turn as y["landing"] + y["nav"] + y["handling"] with no division, so
        # every y figure is one round trip. deck_contract multiplies econ_rev + bus_rev by turns to
        # reach the year, which is the right shape for a per-turn input.
        #
        # The payload carries ONE passenger revenue figure rather than a cabin split, so the whole
        # of it goes in econ_rev and bus_rev is zero. That is correct for every total downstream,
        # because deck_contract only ever sums the two, and it is NAMED here because anything that
        # reads econ_rev alone would be reading a blended figure under a cabin label.
        #
        # gross_rev includes cargo, which has its own line, so cargo is taken out first or the
        # passenger revenue and the average fare would both carry it.
        "route_pnl": dict(
            {k: ec.get(k) for k in
             ("revenue", "fuel", "maintenance", "crew", "ownership",
              "airport_nav_other", "total_cost", "profit", "margin", "breakeven_lf")},
            econ_rev=((ec.get("revenue") or 0) - ((ec.get("raw") or {}).get("cargo_rev") or 0)),
            bus_rev=0.0,
            cargo_rev=((ec.get("raw") or {}).get("cargo_rev") or 0),
            load_factor=(fc.get("capacity") or {}).get("load"),
            _revenue_basis="per turn; econ_rev is blended passenger revenue with cargo removed"),
        # annual_pax is what deck_contract's `carried` falls back to, and without it carried is 0,
        # which takes every average-fare and yield figure in economics_year1 down with it. The
        # payload's demand.total is CARRIED each way, so this is that doubled and nothing else.
        "annual_pnl": {"profit": ec.get("annual_profit"),
                       "aircraft_required": ec.get("aircraft_required"),
                       "annual_pax": (round((dem.get("total") or 0) * 2) or None)},
        "observed_split": (fc.get("catchment") or {}).get("observed_share"),
        # PROVENANCE TRAVELS WITH THE NUMBERS. A deck built from a forecast must be able to say
        # which engine produced it and at what connecting level, because from 13 August 2026 those
        # are two different things and the payload reports both.
        "forecast_engine": fc.get("forecast_engine"),
        "feed_level": fc.get("feed_level"),
        # And WHICH SOURCE the market came from, per leg. A slide that names DOT DB1B on a
        # figure produced from Sabre is the same fault as the four found in the contract on
        # 14 August, committed on purpose, so the source line has to be built from what the
        # run reports rather than from what the product claims.
        "od_source": fc.get("od_source"),
        "load_factor": cap.get("load"),
        "spill_ew": cap.get("spill"),
    }
    return case, outputs


def connecting_from_forecast(fc):
    """The connecting argument build_contract takes, from the payload's own feed detail.

    THE CITY ROWS WERE ALREADY THERE. cortex_app's _feed_list carries code, name, country, base,
    share, forecast and pdew per city whenever the engine returned its detail, which is exactly what
    the contract's connecting tables want, and the first version of this adapter passed None and
    left four blocks empty for no reason.

    DIRECTION, stated rather than assumed, because getting these two the wrong way round is the
    error this programme made twice on 13 August. route_feed.feed_side defines beyond as the origin
    CATCHMENT to the destinations BEYOND the hub, and behind as the hub's FEEDERS to the route
    destination. case["hub_airport"] is set to the destination, so beyond traffic is what connects
    at that hub and it maps to connecting_at_hub. behind maps to connecting_at_destination.

    VERIFY THIS ON THE FIRST DECK. The totals are printed in the payload as feed_beyond and
    feed_behind, so the two tables must sum to those two figures and not to each other's.
    """
    dem = fc.get("demand") or {}

    # nr AND pdew ARE INCLUDED BECAUSE ONE OF THE TWO LISTS IS PASSED STRAIGHT THROUGH.
    # build_contract wraps the HUB cities itself, adding nr as i+1 and computing pdew, but writes
    # "cities": dest_cities for the destination list exactly as given. emit_workbook then reads
    # c["nr"] on both, so a destination row without it raises KeyError 'nr' and no workbook is
    # written. Supplying both on both lists costs nothing, since build_contract overwrites them on
    # the hub side, and it means the two lists reach the writer in the same shape.
    try:
        import deck_contract as _DC
        _pdew = _DC.pdew
    except Exception:                                        # noqa: BLE001
        _pdew = lambda x: round((x or 0) / 728.0, 1)         # deck_contract's own DAYS_2WAY

    def _rows(lst):
        out = []
        for c in (lst or []):
            if c.get("base") is None and c.get("forecast") is None:
                continue          # a pdew-only row, from the trimmed path: no demand to table
            out.append({"nr": len(out) + 1,
                        "city_code": c.get("code"), "city_name": c.get("name"),
                        "country": c.get("country"), "annual_demand": c.get("base"),
                        "airline_share": c.get("share"), "annual_forecast": c.get("forecast"),
                        "pdew": _pdew(c.get("forecast") or 0)})
        return out

    hub_rows, dest_rows = _rows(dem.get("beyond_pdew")), _rows(dem.get("behind_pdew"))
    if not hub_rows and not dest_rows:
        return None

    # ONE BASIS FOR THE ROWS AND THE LEG. Added 14 August 2026.
    #
    # The city rows are the RAW feed. route_forecast scales its feed detail to the carried
    # connecting leg only when split_floor is ON (line 867, _sc = conn_carried / feed); with the
    # floor OFF, which is what every SJC-TPE case runs, the detail stays at the pre-cap level while
    # connecting_carried is lower. A table of pre-cap cities under a post-cap leg total is two
    # bases in one block, and it is how a subtotal comes to exceed the leg it belongs to.
    #
    # So the rows are scaled to the carried leg here, by the same ratio for every city, which keeps
    # each city's SHARE of the leg exactly as the engine measured it and moves only the level. The
    # factor is reported rather than applied silently: a deck that shows a city carrying 400
    # passengers should be able to say whether that is before or after the aircraft filled up.
    # THE DENOMINATOR IS THE SIDES, NOT feed_total, and getting that wrong double-scaled the one
    # case that runs the floor. When split_floor is ON, route_forecast line 867 has ALREADY scaled
    # the detail by conn_carried / feed and scaled feed_beyond and feed_behind with it, but it never
    # reassigns `feed`, so demand.feed_total stays the RAW pre-floor figure. Dividing the carried leg
    # by that reapplied a scaling that had already happened: on SJC-TPE, where FLOOR-EVIDENCED
    # measures the floor at 2.19x, a top-fifteen subtotal of 49% became 107% of its own leg.
    #
    # feed_beyond + feed_behind is the feed AS THE ROWS NOW STAND on either setting, so the ratio is
    # 1.0 when the engine has already done the work and the cap ratio when it has not. No flag is
    # read and none needs to be: the figures say which case they are in.
    _feed = (dem.get("feed_beyond") or 0.0) + (dem.get("feed_behind") or 0.0)
    _carried = dem.get("connecting_carried")
    _scale, _basis = 1.0, "raw feed; carried connecting leg not reported by the engine"
    if _feed and _carried is not None and _feed > 0:
        _scale = float(_carried) / float(_feed)
        _basis = ("carried, after the plan load factor cap; city rows scaled from the raw feed by "
                  "%.4f, shares unchanged" % _scale)
        if abs(_scale - 1.0) > 1e-9:
            for _r in hub_rows + dest_rows:
                if _r.get("annual_forecast") is not None:
                    _r["annual_forecast"] = round(_r["annual_forecast"] * _scale)
                    _r["pdew"] = _pdew(_r["annual_forecast"])
    return {"hub_cities": hub_rows, "dest_cities": dest_rows,
            "hub_market": dem.get("feed_beyond_base"), "dest_market": dem.get("feed_behind_base"),
            "_rows_basis": _basis, "_rows_scale": round(_scale, 4)}


def _expand(v, keys):
    """A scalar applied to all eight segments, or a dict taken as given, or None.

    A SCALAR IS A DELIBERATE SIMPLIFICATION AND THE CONTRACT SAYS SO. With one capture rate on
    every segment the table stops being the bottom-up build the BA deck did and becomes a
    decomposition of a total that was computed another way. Still worth showing, because the split
    itself is the point of the page, but it must not be presented as eight independent judgements
    when it is one repeated eight times.
    """
    if v is None:
        return None, False
    if isinstance(v, dict):
        return {k: v.get(k) for k in keys}, False
    return {k: float(v) for k in keys}, True


def segments_from_case(fc, seg_case, base_year, service_year):
    """(rows, total, note) for the eight-segment block, from the case's judgement inputs."""
    import segment_inputs as SI
    if not seg_case:
        ti = SI.tier_inputs(fc)
        why = ti.get("error") or ("catchment tiers are available (%s) but no segment judgement "
                                  "inputs were given" % ti.get("basis", ""))
        return None, None, "the eight-segment table needs: " + why
    flat = []
    j = {"origin_share": seg_case.get("origin_share"),
         "business_share_destination": seg_case.get("business_share_destination")}
    for name in ("growth", "stim", "capture"):
        j[name], one = _expand(seg_case.get(name), SI.SEGMENT_KEYS)
        if one:
            flat.append(name)
    rows, total, note = SI.segment_rows(fc, j, base_year, service_year)
    if rows and flat:
        note = (note or "") + (". One %s applied to every segment, so this table is a split of the "
                               "route total rather than eight independent judgements"
                               % " and one ".join(flat))
    return rows, total, note


def contract_from_forecast(fc, currency="USD", growth_rate=None, ancillary_per_pax=None,
                           segment_rows=None, connecting=None, segments=None,
                           catchment_ends=None):
    """The deck data contract for one live forecast, or a RuntimeError naming what is missing.

    catchment_ends, when given, is {"origin": profile, "destination": profile} from
    cortex_app.catchment_profile: band populations and locale points per route end, for the
    pack's catchment maps. A profile that failed carries ok=False with its reason and is
    written as a named gap, so the page falls back to the zone definitions and says why
    rather than drawing a map with nothing behind it."""
    miss = _need(fc)
    if miss:
        raise RuntimeError("cannot build a contract: " + "; ".join(miss))
    import deck_contract as DC
    case, outputs = case_and_outputs(fc)
    if connecting is None:
        connecting = connecting_from_forecast(fc)
    # The growth path the forecast actually ran, so the deck's years 2 and 3 project on the same
    # rate rather than on a default nobody chose. GROWTH-IS-THE-GAP of 12 August: the engine's own
    # taper measures a 20.00% CAGR, which is the clamp ceiling, and John's ruling is that client
    # work states its own path.
    if growth_rate is None:
        growth_rate = ((fc.get("projection") or {}).get("cagr")
                       or (fc.get("schedule") or {}).get("growth_rate"))
    # THE EIGHT-SEGMENT TABLE. Built when the case names the judgement inputs, and left as
    # deck_contract's own gap with a note saying exactly which are outstanding when it does not.
    _seg_note = None
    if segment_rows is None:
        _base = (fc.get("projection") or {}).get("base_year") or fc.get("year")
        _svc = (fc.get("schedule") or {}).get("forecast_year") or _base
        try:
            segment_rows, _seg_total, _seg_note = segments_from_case(fc, segments, _base, _svc)
        except Exception as e:                               # noqa: BLE001
            segment_rows, _seg_note = None, "%s: %s" % (type(e).__name__, e)
    contract = DC.build_contract(case, outputs, connecting=connecting, growth_rate=growth_rate,
                                 ancillary_per_pax=ancillary_per_pax, segment_rows=segment_rows)
    # Currency is NOT inferred, which is forecast_spec's own rule: the contract carries fares and
    # revenues without stating one, so the caller states it and it goes into the column head.
    # Guessing would put the wrong symbol in front of every revenue figure on the page.
    contract["currency"] = currency
    contract["_source_engine"] = (outputs.get("forecast_engine") or {}).get("local_leg")
    # THE WORKBOOK'S SOURCE CELL (audit R4): deck_contract.emit_workbook prints
    # contract["_source"], which nothing set, so every exported workbook carried an
    # EMPTY Source cell under Sabre-derived figures. The contractual wording is
    # app/attribution.py's; imported here rather than retyped.
    try:
        from attribution import SOURCE_LINE as _ATTR
    except Exception:                                        # noqa: BLE001
        _ATTR = ("Source: AviaSolutions analysis (Avia Cortex); Sabre Global Demand "
                 "Data; OAG schedules.")
    contract["_source"] = _ATTR
    # THE AIRLINE'S NAME, not "Generic (airline-agnostic)" (the 18 August cosmetic):
    # deck_contract defaults the name when the case carries none, but the run KNOWS
    # its airline. Resolved from the payload's code, best effort; the code itself is
    # the honest fallback, and "Generic" never prints on a named-airline run.
    _rm = contract.get("route_metadata") or {}
    _al = ((fc.get("airline") or _rm.get("airline_iata") or "") or "").strip()
    if _al and (_rm.get("airline_name") in (None, "", "Generic (airline-agnostic)")):
        _nm = None
        try:
            import airline_names as _AN
            _hits = _AN.search(_al, 1) or []
            if _hits and str(_hits[0].get("code") or "").upper() == _al.upper():
                _nm = _hits[0].get("name") or _hits[0].get("label")
        except Exception:                                    # noqa: BLE001
            _nm = None
        _rm["airline_name"] = _nm or _al
        _rm.setdefault("airline_iata", _al)
    # THE RUN SETTINGS THE PACK ALREADY ASKS FOR. deck/forecast_pack.py reads _settings for the
    # connecting floor, the growth basis, the curfew cost and the feed level, and until now
    # NOTHING WROTE IT: all four reads took their default, including the curfew cost shipped on
    # 14 August, which could therefore never have reached the page it was built for. Written from
    # the payload rather than from the case, so it states what the run did.
    _sched = fc.get("schedule") or {}
    _opt = _sched.get("optimised") or {}
    _fl = outputs.get("feed_level") or {}
    # THESE TWO ARE READ AS PROSE. deck/forecast_pack.py prints _settings.curfew_cost and
    # _settings.feed_level straight into a sentence, so they must be sentences. The first version
    # of this block wrote dicts and the renderer threw on the first real contract. The structured
    # figures are kept beside them under their own keys, so nothing is lost and neither consumer
    # has to guess a shape.
    _curfew = None
    if _opt.get("cost_pax"):
        _curfew = ("The permitted departure costs circa %s connecting passengers a year against an "
                   "unrestricted departure at %s. The figure is connecting DEMAND at the two "
                   "departure times, not carried passengers: on a capacity-bound route the seats "
                   "sell either way and the carried cost is smaller."
                   % ("{:,.0f}".format(_opt["cost_pax"]), _opt.get("unrestricted_dep") or "-"))
    _feed = None
    if _fl:
        _feed = ("Connecting level k = %s (%s); the back-tested level is %s."
                 % (_fl.get("qsi_k"), _fl.get("basis") or "basis not stated",
                    _fl.get("back_test_k")))
    contract["_settings"] = {
        # The payload's own record of the floor the run USED (cortex_app writes it from the
        # feed_cfg the engine read). The old chain read fc["settings"], which no module has
        # ever written, so every deck said "off"; it stays only as the fallback for replayed
        # contracts built before 15 August.
        "split_floor": fc.get("split_floor",
                              (fc.get("settings") or {}).get("split_floor",
                                                             (case or {}).get("split_floor"))),
        "warnings": fc.get("warnings") or [],
        "growth_basis": _sched.get("growth_basis"),
        "base_year": fc.get("year"),
        "curfew_cost": _curfew,
        "curfew_cost_detail": ({"cost_pax": _opt.get("cost_pax"),
                                "unrestricted_dep": _opt.get("unrestricted_dep")}
                               if _opt.get("cost_pax") else None),
        "feed_level": _feed,
        "feed_level_detail": (_fl or None),
        "od_source": outputs.get("od_source"),
    }
    # THE CATCHMENT ENDS. Population by drive-time band and the locale points, one block per
    # route end, produced by the same catchment_profile the portal's map page reads. The pack
    # draws its maps from these; an end that failed keeps its reason so the page can say it.
    if isinstance(contract.get("catchment"), dict):
        _ce = catchment_ends or {}
        _good = {s: p for s, p in _ce.items() if isinstance(p, dict) and p.get("ok")}
        if _good:
            contract["catchment"]["ends"] = _good
            _bad = {s: p.get("error", "no reason recorded") for s, p in _ce.items()
                    if s not in _good}
            if _bad:
                contract["catchment"]["_ends_partial"] = (
                    "; ".join("%s: %s" % (s, w) for s, w in sorted(_bad.items())))
        else:
            contract["catchment"]["_ends_need"] = (
                "; ".join("%s: %s" % (s, (p or {}).get("error", "no profile"))
                          for s, p in sorted(_ce.items()))
                or "no catchment profiles were passed; deck_from_cases computes them from the "
                   "live context (GeoNames dump plus the drive engine)")
    _fill_hardcoded(contract, fc, case)
    _fill_forecast_table(contract, fc)
    _fill_competition(contract, fc)
    # The note travels whether the table built or not: a populated block says on what basis, and an
    # empty one says which inputs are outstanding, so the gap report reads as an instruction.
    if _seg_note and isinstance(contract.get("segment_forecast"), dict):
        contract["segment_forecast"]["_rows_need"] = _seg_note
    return contract


def _fill_forecast_table(contract, fc):
    """The three columns slide 32 has and the contract did not carry.

    deck_contract line 454 sets demand_at_service_year to None with the note "no pre-stimulation
    local leg in the payload", which was true of the block it reads and not of the payload as a
    whole: demand.stimulation is reported, so the pre-stimulation figure is the post-stimulation
    one divided by it. That is arithmetic on two figures in the same payload, not a new estimate.

    Filled per leg:
        demand_at_service_year   grown to the service year, BEFORE stimulation
        stimulation_factor       1.0 on the connecting legs, which the engine does not stimulate
        annual_growth_rate       total growth from the base year to the service year, not a CAGR,
                                 because that is the column the 2025 deck carries

    Nothing is invented. Where stimulation is absent or zero the field keeps its _need note.
    """
    ss = ((contract.get("segment_forecast") or {}).get("summary")) or {}
    dem = fc.get("demand") or {}
    stim = dem.get("stimulation")

    # ONE BASIS, EACH WAY, EVERY COLUMN FROM ITS OWN PAYLOAD KEY (the 18 August 2026
    # defect, found the night the three-airline tables were built: the old patching
    # divided CAPTURED-after-stimulation by the stimulation factor and compared it
    # against the TWO-WAY pair market, so growth printed -80.6% and the row did not
    # multiply through. Same decomposition as the workbook: the payload's schedule
    # block carries growth_rate/growth_years, natural is the GROWN each-way market
    # before stimulation and capture, p2p_carried is the carried forecast, and the
    # capture printed is the EFFECTIVE rate after the capacity allocation so
    # grown x stim x capture = forecast in the reader's own arithmetic.
    sch = fc.get("schedule") or {}
    try:
        _gy = float(sch.get("growth_years") or 0)
        _gr = float(sch.get("growth_rate") or 0)
    except (TypeError, ValueError):
        _gy = _gr = 0.0
    _cum = ((1.0 + _gr) ** _gy - 1.0) if _gy else 0.0

    def _n(v):
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    natural = _n(dem.get("natural"))
    p2p_c = _n(dem.get("p2p_carried")) or _n(dem.get("captured"))
    blk = ss.get("point_to_point_total")
    if isinstance(blk, dict) and natural and natural > 0:
        _stim = float(stim) if stim else 1.0
        blk["base_annual_demand"] = round(natural / (1.0 + _cum)) if _cum else round(natural)
        blk["annual_growth_rate"] = round(_cum, 4)
        blk["demand_at_service_year"] = round(natural)
        blk.pop("_demand_at_service_year_need", None)
        blk["stimulation_factor"] = _stim
        blk["demand_after_stimulation"] = round(natural * _stim)
        if p2p_c and p2p_c > 0:
            blk["capture_rate"] = round(p2p_c / (natural * _stim), 4)
            blk["forecast"] = round(p2p_c)
        blk["_basis"] = ("each way; base decomposed from the grown market at the "
                         "payload's growth rate; capture is the effective rate after "
                         "the capacity allocation, so the row multiplies through")

    # The connecting legs' base_annual_demand arrives GROWN (the engine grows feed
    # bases with the market), so the same decomposition applies: state the grown
    # figure as the service-year column and derive the base-year column from it.
    # The engine does not stimulate connecting demand, and stating the 1.0 is the
    # point: a reader seeing a blank assumes the leg was stimulated too.
    for key in ("connecting_at_hub_total", "connecting_at_destination_total"):
        cb = ss.get(key)
        if not isinstance(cb, dict):
            continue
        base = _n(cb.get("base_annual_demand"))
        cb["stimulation_factor"] = cb.get("stimulation_factor") or 1.0
        if base and base > 0:
            cb["demand_at_service_year"] = round(base)
            cb["base_annual_demand"] = round(base / (1.0 + _cum)) if _cum else round(base)
            cb["annual_growth_rate"] = round(_cum, 4)
            cb.pop("_demand_at_service_year_need", None)


def _fill_competition(contract, fc):
    """The competed and uncompeted rows the forecast table needs, from the run's own bucket.

    cortex_app already builds competition_split from direct_competition, which classifies each
    connecting market on whether a nonstop exists in the scheduled week. The rates are OBSERVED,
    not assumed: the engine applies one capture per market and this reports what that produced in
    each bucket. It is not the two-rate model the 2025 analyst used, and the note says so, because
    a reader who has seen his table will otherwise assume it is.
    """
    cs = fc.get("competition_split")
    if not cs:
        return
    ss = ((contract.get("segment_forecast") or {}).get("summary")) or {}
    out, scales = {}, {}
    for side, key in (("beyond", "connecting_at_hub"), ("behind", "connecting_at_destination")):
        tot = ((cs.get(side) or {}).get("totals")) or {}
        rows = []
        for label, bucket in (("Direct competition", "direct"),
                              ("No direct competition", "no_direct")):
            blk = tot.get(bucket) or {}
            if not blk.get("markets"):
                continue
            rows.append({"bucket": label, "markets": blk.get("markets"),
                         "base": blk.get("base"), "capture": blk.get("capture"),
                         "forecast": blk.get("forecast")})
        if not rows:
            continue
        # THE ROWS AND THE LEG ARE NOT ON ONE BASIS, and the rows sit under the leg in the table.
        # competition_split is built from the feed DETAIL, which is each way and, with the split
        # floor off, at the pre-cap level; the contract's leg is two-way and post-cap. Measured on
        # the shipped floor-ON case the rows summed to 15,872 against a leg of 31,745, 2.0000x to
        # the passenger. Each side is scaled to its own leg by ONE ratio, so every bucket's SHARE
        # is exactly as the engine measured it and only the level moves. This is the fix
        # FLOOR-DOUBLE-SCALED settled for the city rows on 14 August, applied to the same shape.
        leg_blk = ss.get("connecting_at_hub_total" if key == "connecting_at_hub"
                         else "connecting_at_destination_total") or {}
        leg_fc, leg_base = leg_blk.get("forecast"), leg_blk.get("base_annual_demand")
        sum_fc = sum((r.get("forecast") or 0) for r in rows)
        sum_base = sum((r.get("base") or 0) for r in rows)
        s_fc = (leg_fc / sum_fc) if (leg_fc and sum_fc) else 1.0
        s_base = (leg_base / sum_base) if (leg_base and sum_base) else 1.0
        for r in rows:
            r["forecast"] = round((r.get("forecast") or 0) * s_fc)
            r["base"] = round((r.get("base") or 0) * s_base)
            # Recomputed rather than carried: the two scalings differ, so the ratio the client
            # reads must be the ratio of the two numbers printed beside it.
            r["capture"] = (round(r["forecast"] / r["base"], 4) if r["base"] else None)
        scales[key] = {"forecast_scale": round(s_fc, 4), "base_scale": round(s_base, 4)}
        out[key] = rows
    if out:
        sf = contract.setdefault("segment_forecast", {})
        sf["_competition_buckets"] = out
        sf["_competition_scale"] = scales
        sf["_competition_basis"] = (
            "A market has direct competition where a nonstop already operates in the scheduled "
            "week (%s). The capture rates shown are MEASURED from the run, one rate per market "
            "applied by the engine and reported by bucket, not two rates assumed in advance."
            % (cs.get("week") or "week not stated"))


def _fill_hardcoded(contract, fc, case):
    """Fill the fields build_contract writes as a literal None, which no argument can reach.

    These are not gaps in the model. deck_contract sets origin_city_code, destination_city_code and
    both schedule legs' dep_time and arr_time to None in the dict literal itself, with a _need note
    beside them, so passing them in `case` does nothing at all: the first version of this adapter
    did exactly that and they stayed empty. They are filled here, after the contract is built, and
    each one is filled only where the payload genuinely carries it.

    Nothing is invented. A field the payload cannot supply is left as deck_contract wrote it, so its
    _need note still reads and the gap report still counts it.
    """
    rm = contract.get("route_metadata") or {}
    # No IATA metro code exists in the payload, so the airport code stands in, and the _need note is
    # rewritten to say so rather than left claiming a lookup is outstanding.
    if rm.get("origin_city_code") is None and case.get("origin_city_code"):
        rm["origin_city_code"] = case["origin_city_code"]
        rm["_origin_city_need"] = "airport code standing in; no IATA metro code in the payload"
    if rm.get("destination_city_code") is None and case.get("destination_city_code"):
        rm["destination_city_code"] = case["destination_city_code"]
        rm["_dest_city_need"] = "airport code standing in; no IATA metro code in the payload"

    # THE SCHEDULE TIMES ARE INDICATIVE AND MUST SAY SO. cortex_app._schedule_times returns
    # {"outbound": {"dep","arr"}, "inbound": {...}, "indicative": True}, and its own docstring calls
    # them illustrative: not curfew-, slot- or connection-optimised. A deck printing a departure
    # time an airline reads as a proposal, with no note, is worse than one printing none, so the
    # basis is carried onto the block rather than dropped at the boundary.
    sch = fc.get("schedule") or {}
    legs = contract.get("summary_and_schedule", {}).get("schedule") or []
    for row, key in zip(legs, ("outbound", "inbound")):
        leg = sch.get(key) or {}
        if row.get("dep_time") is None and leg.get("dep"):
            row["dep_time"] = leg["dep"]
        if row.get("arr_time") is None and leg.get("arr"):
            row["arr_time"] = leg["arr"]
    if legs:
        contract["summary_and_schedule"]["_schedule_times_need"] = (
            (sch.get("basis") or "indicative") if sch.get("indicative")
            else "departure time %s" % (sch.get("basis") or "set by the caller"))

    # breakeven_load_factor is produced by the economics module and deck_contract does not read it.
    ec = fc.get("economics") or {}
    e1 = contract.get("economics_year1") or {}
    if e1.get("breakeven_load_factor") is None and ec.get("breakeven_lf") is not None:
        e1["breakeven_load_factor"] = ec["breakeven_lf"]


def _selftest():
    """The mapping against a payload shaped like the real one, with known answers.

    Checks the three traps named in the docstring rather than that the code runs: carried against
    uncapped, the carrier's seat count against the type table's, and each way staying each way.
    """
    fc = {"ok": True, "economics_ok": True, "airline": "CI", "distance_nm": 5637,
          "origin": {"iata": "SJC", "city": "San Jose"}, "dest": {"iata": "TPE", "city": "Taipei"},
          "schedule": {"forecast_year": 2028},
          "demand": {"natural": 180000, "current": 120000, "qsi_share": 0.251, "total": 55692,
                     "total_demand": 58724, "p2p_carried": 41704, "connecting_carried": 13988,
                     "feed_total": 13988},
          "capacity": {"aircraft": "A359", "seats": 306, "freq": 4, "load": 0.875, "spill": 3032},
          "economics": {"revenue": 1, "profit": 2, "annual_profit": 3, "econ_lf": 0.9, "bus_lf": 0.7},
          "catchment": {"observed_share": {"SJC": 0.3}},
          "forecast_engine": {"local_leg": "qsi engine"}, "feed_level": {"qsi_k": 1.0}}
    case, out = case_and_outputs(fc)
    ok = True

    def chk(label, got, want):
        nonlocal ok
        good = got == want
        ok = ok and good
        print("  %-46s %-12s %s" % (label, got, "OK" if good else "EXPECTED %s" % (want,)))

    chk("directional_demand is CARRIED, not uncapped", out["directional_demand"], 55692)
    chk("the uncapped figure travels separately", out["demand_uncapped_ew"], 58724)
    chk("seats come from the forecast, not the table", case["cabin_config"]["business"]
        + case["cabin_config"]["coach"], 306)
    chk("frequency", case["frequency"], 4)
    chk("service year from the schedule block", case["service_year"], 2028)
    chk("hub is the destination on a feed route", case["hub_airport"], "TPE")
    chk("capture is the qsi share", out["capture"], 0.251)
    print("\n  A359 in the generic table is 336 seats; the contract must carry 306, which is what")
    print("  China Airlines actually flies. That single line is an 8 to 13% capacity error on")
    print("  every carrier in the SJC-TPE set if it is got wrong.")
    return 0 if ok else 1


if __name__ == "__main__":
    print("forecast_to_contract selftest")
    raise SystemExit(_selftest())
