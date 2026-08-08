#!/usr/bin/env python3
"""Run one pitch through the Observatory deck path and report what it produced.

The Observatory branch in app/pitch_report.py had never been driven by a real
provider run. This is the runner for that test, plus a free offline mode so the
plumbing is proved before any money is spent on searches.

Two modes:

  --replay FILE   findings are read from a file, no API key, no network. Free.
                  Use it to prove the path and to see what a section looks like
                  when it carries provider-shaped findings and nothing else.

  --live          the real AnthropicResearchProvider. Needs ANTHROPIC_API_KEY
                  and costs circa $4 a run. This is the one that matters.

Three things are reported after either run, because all three fail silently:

  1. keynumbers slides. Zero means the display value is being blanked again and
     the deck has lost its main visual device.
  2. content slides with no attribution line. An unsourced slide must not leave
     Avia.
  3. sections with findings but no prose. Evidence without an argument.

The forecast is NOT part of this test. deck_contract.py is not yet wired into
the connector, so the fc handed in here carries route identity and placeholder
demand only. Nothing in the deck reads a number from it. Do not read the output
as a forecast of anything.

Avia Solutions Limited. All rights reserved.
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # the renderer folder, <repo>\deck
# The engine folder is found by looking for cortex_app.py, not by counting folders up.
# Until 8 August 2026 this was dirname(dirname(HERE)) + "app", which was right while the
# renderer sat at <project>\Deck Generator\v4 and resolved to C:\app once it moved.
import deck_paths as _DP                                   # noqa: E402
APP = _DP.on_path(HERE, who="run_observatory_pitch")
ROOT = os.path.dirname(APP)


# ---------------------------------------------------------------------------
# The route stub
# ---------------------------------------------------------------------------
def _freq_in(fc):
    return ((fc or {}).get("capacity") or {}).get("freq")


def _warn_induced_with_fixed_gauge(fc, args):
    """The circularity that route_forecast.py warns about, on the deck path.

    On an induced route the engine FLOORS demand at deployed capacity times an
    achieved seat factor, because the market does not pre-exist. The protection
    against that floor being handed an over-large aircraft is the auto gauge,
    and the auto gauge lives in cortex_app's /api/forecast and /api/optimise.
    This runner calls calibrated_forecast directly with whatever --aircraft says,
    so it does not get that protection: choose a big aircraft on a thin new
    market and the forecast fills it because you chose it.

    Named here rather than fixed, because the fix is --aircraft auto in this
    runner and that is its own piece of work.
    """
    dem = (fc or {}).get("demand") or {}
    if not dem.get("induced"):
        return
    nat, tot = dem.get("natural"), dem.get("total")
    share = ("   The measured point to point market is %s each way, so the floor "
             "supplies %.0f%% of the %s headline.\n"
             % (format(int(nat), ","), 100.0 * (tot - nat) / tot, format(int(tot), ","))
             if nat and tot and tot > nat else "")
    if getattr(args, "_from_optimiser", False):
        print("NOTE: INDUCED route. The optimiser chose the airline, gauge, frequency "
              "and season against unfloored demand, so nothing here is circular, but "
              "the total is still floored at the capacity deployed.\n%s   The deck "
              "carries a basis page saying the forecast is modelled rather than "
              "measured." % share)
    elif getattr(args, "_gauge_was_auto", False):
        print("NOTE: INDUCED route. The gauge was sized against unfloored market "
              "demand, so it is not circular, but the total is still floored at "
              "the capacity deployed.\n%s   The deck now carries a basis page "
              "saying the forecast is modelled rather than measured." % share)
    else:
        print("WARNING: the engine classes this as an INDUCED route, so demand is "
              "floored at the capacity you deploy. You fixed the aircraft at %s, so "
              "the forecast partly reflects that choice rather than the market.\n"
              "%s   Re-run with --aircraft auto to size the gauge against the "
              "unfloored market." % ((args.aircraft or "").strip(), share))


def _finish_fc(fc, args):
    """The identity fields the deck needs, on whichever path produced the forecast."""
    fc.setdefault("carrier_type", args.carrier_type)
    for k, v in (("name", args.prepared_for), ("country", args.origin_country)):
        if v:
            fc["origin"].setdefault(k, v)
    if args.dest_country:
        fc["dest"].setdefault("country", args.dest_country)
    return fc


def optimised_fc(args, CA, audit_out=None):
    """Build the deck on the optimiser, which is what the dashboard's button does.

    THE REASON THIS EXISTS, and it supersedes --freq auto for a pitch deck.
    /api/optimise sweeps the operating AIRLINE as well as the gauge, the
    frequency and the season, because the airline changes the demand: its
    connecting feed at both ends is most of the traffic on a thin long-haul.
    Run EDI to AUS with no airline and the engine has no network behind it, so
    the feed is zero and the induced floor supplies the whole answer. Run it
    through the optimiser and a real carrier appears with real feed.

    On the 7 August EDI to AUS run the two modes gave 21,865 each way with no
    airline against 8,720 each way optimised, of which 6,181 was connecting
    feed. A pitch deck is a document aimed AT an airline, so building it with no
    airline in the model is the wrong mode, not a conservative one.

    The endpoint is called as a plain function. It returns a JSONResponse, so the
    body is unpacked here rather than refactoring cortex_app, which is a hand
    merge and hard-blocked in the reconciler.
    """
    resp = CA.api_optimise(
        args.origin, args.dest, airline=(args.airline or ""),
        carrier_type=args.carrier_type,
        aircraft=("" if str(args.aircraft or "").strip().upper()
                  in ("", "AUTO", "UNSELECTED") else args.aircraft),
        freq=(int(args.freq) if str(args.freq).isdigit() else 0),
        season=(args.season or "unselected"))
    fc = json.loads(resp.body)
    if not fc.get("ok"):
        raise SystemExit("Cortex optimise failed: %s" % fc.get("error"))
    o = fc.get("optimised") or {}
    args.aircraft = o.get("aircraft") or args.aircraft
    args.freq = o.get("freq") or args.freq
    if o.get("airline") and not args.airline:
        args.airline = o["airline"]
    print("OPTIMISED: %s, %s, %s a week, %s. Annual profit %s."
          % (o.get("airline") or "no airline found", o.get("aircraft"),
             o.get("freq"), o.get("season"),
             format(int(o.get("annual_profit") or 0), ",")))
    args._from_optimiser = True
    if audit_out is not None:
        audit_out["optimised"] = o
    return fc


def auto_gauge(args, CA, freq):
    """Size the metal to the market, the way /api/forecast already does.

    THE POINT IS `induced_floor=False` ON THE PROBE RUN. On an induced route the
    engine floors demand at deployed capacity times an achieved seat factor, so
    sizing the aircraft against a floored demand sizes it against the aircraft
    you already picked, and the answer is whatever you started with. The probe
    turns the floor off and reads `total_demand`, the unconstrained market, and
    the gauge is chosen against that. cortex_app does exactly this at
    /api/forecast; this runner never did, which is why a deck built with an
    explicit --aircraft has been carrying a capacity-anchored total.

    Returns (code, note) or (None, why not).
    """
    try:
        import aircraft_select as ASsel
        dist_km = CA._route_distance_km(args.origin, args.dest) or 0.0
        dnm = dist_km / 1.852
        if dnm <= 0:
            return None, "the route distance did not resolve"
        probe = CA.calibrated_forecast(
            args.origin, args.dest, airline=(args.airline or None),
            carrier_type=args.carrier_type, aircraft="A21X", freq=int(freq),
            with_econ=False, induced_floor=False)
        if not probe.get("ok"):
            return None, "the unfloored probe run failed: %s" % probe.get("error")
        dem = (probe.get("demand") or {}).get("total_demand")
        if not dem:
            return None, "the probe returned no unconstrained demand"
        at = args.carrier_type if args.carrier_type in ("FSC", "LCC", "ULCC") else "FSC"
        code, _ranked = ASsel.select_aircraft(
            dnm, dem, int(freq), plan_lf=0.85, econ_share=0.85,
            econ_fare_ow=max(180, round(dnm * 0.11)), bus_fare_ow=1400.0,
            airline_type=at, airline_iata=(args.airline or None), weeks=52.0)
        return code, ("sized to %s against %s each way of unfloored market demand "
                      "at %s a week" % (code, format(int(dem), ","), freq))
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)


def live_fc(args, audit_out=None):
    """The real thing: the calibrated Cortex engine for this city pair.

    Needs the OAG and Sabre stores, at AVIA_OAG and AVIA_SABRE or C:\\Avia. The
    engine returns {"ok": False, "error": ...} when it cannot resolve a route or
    reach a store, and that error is raised here rather than quietly falling back
    to the stub, because a deck with an invented forecast is worse than no deck.

    --freq auto sizes the schedule from demand rather than taking the number on
    trust. That costs a few engine runs, because frequency and demand determine
    each other and the answer is a fixed point; see app/schedule_sizing.py.
    """
    import cortex_app as CA

    # The optimiser answers the whole question at once, including the airline,
    # so it comes before anything else and short-circuits the rest.
    if getattr(args, "optimise", False):
        fc = optimised_fc(args, CA, audit_out=audit_out)
        _warn_induced_with_fixed_gauge(fc, args)
        return _finish_fc(fc, args)

    # The gauge first, because the frequency sizer needs to know what it is
    # filling. Both are auto only if asked for; neither changes anything the
    # user set by hand.
    if str(args.aircraft or "").strip().upper() in ("", "AUTO", "UNSELECTED"):
        probe_freq = int(args.freq_start or 7) if not str(args.freq).isdigit() \
            else int(args.freq)
        code, why = auto_gauge(args, CA, probe_freq)
        if code:
            print("AUTO GAUGE: %s" % why)
            args.aircraft = code
            args._gauge_was_auto = True
            if audit_out is not None:
                audit_out["auto_gauge"] = {"aircraft": code, "note": why}
        else:
            args.aircraft = "A21X"
            print("AUTO GAUGE FAILED: %s. Falling back to A21X, which means the "
                  "gauge is an assumption and not a result." % why)
            if audit_out is not None:
                audit_out["auto_gauge"] = {"aircraft": "A21X", "note": "FAILED: %s" % why}

    def run(freq):
        return CA.calibrated_forecast(
            args.origin, args.dest, airline=(args.airline or None),
            carrier_type=args.carrier_type, aircraft=args.aircraft or "A21X",
            freq=int(freq))

    if str(args.freq or "").strip().lower() in ("auto", "size", "sized"):
        import schedule_sizing as SZ
        print("SIZING: finding the frequency the demand supports. A few engine "
              "runs, circa 10 seconds each.")
        sized = SZ.size_schedule(run, freq_start=int(args.freq_start or 7),
                                 target_lf=float(args.plan_lf or SZ.PLANNING_LF))
        print("SIZING: %s" % SZ.describe(sized))
        if audit_out is not None:
            audit_out["schedule_sizing"] = {k: v for k, v in sized.items() if k != "fc"}
        if sized.get("reason") == "engine":
            raise SystemExit("Cortex forecast failed while sizing: %s" % sized["note"])
        if not sized["ok"]:
            # The engine worked; this route simply cannot be sized by frequency.
            # Carry on at the frequency asked for rather than abandoning the deck,
            # and say plainly that the sizing was not used.
            fallback = int(args.freq_start or 7)
            print("SIZING NOT USED: building at %s a week instead. %s"
                  % (fallback, sized["note"]))
            args.freq = fallback
            fc = sized.get("fc") if _freq_in(sized.get("fc")) == fallback else run(fallback)
        else:
            fc = sized["fc"]
            args.freq = sized["freq"]       # so the deck and the cover agree
            fc["_schedule_sized"] = True    # read by the viability check downstream
    else:
        fc = run(int(args.freq or 7))
    if not fc.get("ok"):
        raise SystemExit("Cortex forecast failed: %s" % fc.get("error"))
    _warn_induced_with_fixed_gauge(fc, args)
    return _finish_fc(fc, args)


def stub_fc(args):
    """A route identity with no forecast, for offline plumbing tests only.

    _pptx_config reads demand and capacity to write the legacy executive summary,
    so the keys have to exist. The _stub flag stops these zeros ever reaching the
    deck's forecast section.
    """
    return {
        "_stub": True,
        "origin": {"iata": args.origin, "city": args.origin_city,
                   "country": args.origin_country, "name": args.prepared_for,
                   "lat": args.origin_lat, "lon": args.origin_lon},
        "dest": {"iata": args.dest, "city": args.dest_city,
                 "country": args.dest_country, "name": ""},
        "airline": args.airline,
        "carrier_type": args.carrier_type,
        "demand": {"total": 0, "natural": 0, "captured": 0, "qsi_share": 0.0,
                   "feed_behind": 0, "feed_beyond": 0, "stimulation": 1.0,
                   "beyond_pdew": []},
        "capacity": {"load": 0.0, "aircraft": args.aircraft, "freq": args.freq,
                     "carried": 0},
        "economics": {"seats": 0},
    }


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------
def _norm(s):
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")


class ReplayProvider:
    """Returns saved findings instead of searching. Same interface, no cost.

    research_block is called with the block's display name, not its id, so the
    caller hands in the name-to-id map taken from the same generate_queries
    call the runner will make.
    """

    def __init__(self, findings_by_block, name_to_id):
        self.findings = {_norm(k): v for k, v in findings_by_block.items()}
        self.name_to_id = {_norm(k): _norm(v) for k, v in name_to_id.items()}

    def available(self):
        return True

    def research_block(self, block_name, queries, ctx):
        key = self.name_to_id.get(_norm(block_name), _norm(block_name))
        got = self.findings.get(key, [])
        return list(got), {"block": block_name, "searches": 0, "model": "replay",
                           "raw_chars": 0}

    def adjudicate(self, claim, value, snippet, model=None):
        return True


def to_provider_shape(path):
    """Flatten a market_research_executor JSON down to what a live run returns.

    The provider gives claim, value, unit, year, source_name and url: one inline
    source, no citations list, no relevance_to_case, no presentation_text and no
    block summary. A replay built from a rich executor file would flatter the
    live path. This strips it to the honest shape first.
    """
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    blocks = doc["blocks"] if isinstance(doc, dict) and "blocks" in doc else []
    out = {}
    for b in blocks:
        rows = []
        for f in (b.get("findings") or []):
            cites = f.get("citations") or []
            c = cites[0] if cites else {}
            rows.append({"claim": f.get("claim", ""), "value": f.get("value", ""),
                         "unit": f.get("unit", ""), "year": str(f.get("year", "")),
                         "source_name": c.get("source_name", ""),
                         "url": c.get("url", "")})
        if rows:
            out[b.get("block_id", "")] = rows
    return out


# ---------------------------------------------------------------------------
def report(audit, deck_path, html_path):
    d = audit.get("deck") or {}
    print("\n" + "=" * 72)
    print("ROUTE                 %s" % audit.get("route"))
    print("BLOCKS RESEARCHED     %s" % audit.get("blocks_researched"))
    print("FINDINGS KEPT         %s" % audit.get("total_kept"))
    print("SLIDES                %s   %s" % (d.get("slides"), d.get("by_type")))
    print("-" * 72)
    kn = d.get("keynumbers_slides", 0)
    print("1. KEYNUMBERS SLIDES  %d (%d values)%s"
          % (kn, d.get("keynumbers_values", 0),
             "   <-- ZERO: the value is being blanked again" if not kn else ""))
    ns = d.get("slides_without_source") or []
    print("2. NO SOURCE LINE     %d" % len(ns))
    for s in ns:
        print("      %s" % s)
    thin = audit.get("sections_without_prose") or []
    print("3. NO PROSE           %d" % len(thin))
    for s in thin:
        print("      %s" % s)
    ob = d.get("over_budget", 0)
    print("4. OVER BUDGET        %d slot(s)" % ob)
    for x in (d.get("over_budget_detail") or [])[:6]:
        print("      %s" % x)
    o = audit.get("optimised")
    if o:
        print("-" * 72)
        print("OPTIMISED             %s, %s, %s a week, %s"
              % (o.get("airline") or "no airline", o.get("aircraft"), o.get("freq"),
                 o.get("season")))
        print("   airline %s, season %s, annual profit %s"
              % ("auto-chosen" if o.get("airline_auto") else "as given",
                 "auto-chosen" if o.get("season_auto") else "as given",
                 format(int(o.get("annual_profit") or 0), ",")))
    z = audit.get("schedule_sizing")
    if z:
        print("-" * 72)
        print("SCHEDULE SIZED        %s a week%s"
              % (z.get("freq"), "" if z.get("converged") else "   <-- did not settle"))
        print("   %s" % z.get("note"))
        print("   path: %s" % " -> ".join("%dx at %.0f%%" % (f, l * 100)
                                          for f, l in (z.get("path") or [])))
    v = audit.get("schedule_viability")
    if v:
        print("-" * 72)
        print("!! %s  %s" % (v["band"], v["message"]))
        if v.get("band", "").startswith("OPTIMISER"):
            print("   Reported, not an objection: the optimiser chose it.")
        else:
            print("   The deck was still built. Change --freq and re-run if you "
                  "would rather show the sized schedule.")
    f = audit.get("forecast") or {}
    print("5. FORECAST           %s" % (
        "%s: %d stats, %d schedule rows%s"
        % (f.get("source"), f.get("stats", 0), f.get("schedule_rows", 0),
           ", missing " + ", ".join(f["tables_missing"]) if f.get("tables_missing") else "")
        if f.get("source") else f.get("note", "none")))
    g = audit.get("figures") or {}
    if g:
        drawn = g.get("drawn") or []
        print("7. FIGURES            %d drawn%s"
              % (len(drawn), (": " + ", ".join(drawn)) if drawn else ""))
        for slot, why in sorted((g.get("not_drawn") or {}).items()):
            print("      NOT DRAWN %-14s %s" % (slot, why))
        if g.get("segments_table"):
            print("      TABLE     %-14s %s" % ("segments", g["segments_table"]))
    p = audit.get("prose") or {}
    if p.get("skipped"):
        print("6. PROSE              skipped: %s" % p["skipped"])
    else:
        print("6. PROSE              %d section(s) written, summary %s"
              % (p.get("written", 0), p.get("executive_summary_note", "-")))
        for bid, note in (p.get("blocks") or {}).items():
            if note != "ok":
                print("      %-22s %s" % (bid, note))
        for bid, fl in (p.get("house_style_flags") or {}).items():
            print("      HOUSE STYLE %-14s %s" % (bid, "; ".join(fl)))
    print("-" * 72)
    for b in audit.get("blocks", []):
        drops = [x.get("drop") for x in (b.get("decisions") or []) if x.get("drop")]
        print("  %-22s found %2d  kept %2d  %s"
              % (b["block"], b["found"], b["kept"],
                 ("dropped: " + ", ".join(drops[:4])) if drops else ""))
    print("=" * 72)
    print("DECK  %s" % deck_path)
    print("HTML  %s" % html_path)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--origin", required=True, help="origin IATA, e.g. EDI")
    ap.add_argument("--dest", required=True, help="destination IATA, e.g. AUS")
    ap.add_argument("--origin-city", required=True)
    ap.add_argument("--dest-city", required=True)
    ap.add_argument("--origin-country", default="")
    ap.add_argument("--dest-country", default="")
    ap.add_argument("--origin-lat", type=float, default=None)
    ap.add_argument("--origin-lon", type=float, default=None)
    ap.add_argument("--airline", default="", help="IATA code or name")
    ap.add_argument("--carrier-type", default="FSC", choices=["FSC", "LCC", "ULCC"])
    ap.add_argument("--aircraft", default="")
    ap.add_argument("--freq", default="",
                    help="weekly frequency, or 'auto' to size it from demand at "
                         "the planning load factor rather than take it on trust")
    ap.add_argument("--freq-start", default=7, type=int,
                    help="where --freq auto begins its search; the answer does "
                         "not depend on it, only the number of rounds")
    ap.add_argument("--optimise", action="store_true",
                    help="build on the OPTIMISER rather than a single run: it sweeps "
                         "the airline, the gauge, the frequency and the season for "
                         "maximum profit. The airline is the big one, because its "
                         "connecting feed is most of the traffic on a thin long-haul. "
                         "This is the right mode for a pitch deck and it supersedes "
                         "--freq auto")
    ap.add_argument("--season", default="",
                    help="annual, summer or winter. Blank lets --optimise choose")
    ap.add_argument("--plan-lf", default=0.0, type=float,
                    help="planning load factor --freq auto sizes to (default 0.80)")
    ap.add_argument("--prepared-for", default="", help="the airport the deck is for")
    ap.add_argument("--date", default="", help="cover date, e.g. 6 August 2026")
    ap.add_argument("--replay", metavar="FILE",
                    help="findings file: {block_id: [findings]}, or an executor "
                         "JSON, which is flattened to the provider shape first")
    ap.add_argument("--live", action="store_true",
                    help="use the real provider. Needs ANTHROPIC_API_KEY, circa $4")
    ap.add_argument("--no-fetch-back", action="store_true",
                    help="skip the source fetch-back check (offline)")
    ap.add_argument("--fixture-urls", action="store_true",
                    help="replay only: stamp a fixture URL on findings that carry "
                         "none, so a source-less file still exercises the path. "
                         "The output is a plumbing test, never a deck to show.")
    ap.add_argument("--out", default="", help="copy the deck here when done")
    ap.add_argument("--currency", default="USD",
                    help="follows the asset's home jurisdiction; written into the "
                         "revenue column head, never inferred")
    ap.add_argument("--contract", metavar="FILE",
                    help="a deck_contract JSON. Takes precedence over the engine "
                         "output for the forecast section")
    ap.add_argument("--prose", metavar="FILE",
                    help="section prose written outside the pipeline: "
                         "{\"executive_summary\": str, \"blocks\": {block_id: str}}. "
                         "Every paragraph is checked against that block's findings, so a "
                         "figure the research did not source still rejects the paragraph")
    ap.add_argument("--stub-forecast", action="store_true",
                    help="skip the engine and carry no forecast. Plumbing tests only")
    args = ap.parse_args()

    if not args.live and not args.replay:
        ap.error("choose --replay FILE (free) or --live (circa $4)")

    os.environ["AVIA_DECK_STYLE"] = "observatory"
    import pitch_report as PR

    contract = None
    if args.contract:
        with open(args.contract, encoding="utf-8") as fh:
            contract = json.load(fh)
    pre_audit = {}          # things decided before build_pitch runs, merged after
    if args.stub_forecast:
        fc = stub_fc(args)
        print("FORECAST: stub. The deck will carry no forecast section.")
    else:
        fc = live_fc(args, audit_out=pre_audit)
        print("FORECAST: Cortex engine, %s to %s, %s carried each way."
              % (fc["origin"]["city"], fc["dest"]["city"],
                 format(int(fc["demand"]["total"] or 0), ",")))
        try:
            import airport_capture as _AC
            if getattr(_AC, "SHIMS_USED", None):
                print("WARNING: the engine ran with NEUTRAL shims for %s. No airport "
                      "capture correction was applied. This forecast will not match "
                      "the Meridian site until the real module is in place."
                      % ", ".join(sorted(_AC.SHIMS_USED)))
        except Exception:
            pass
    inputs = {"airline_name": args.airline, "date": args.date}

    provider, fetch_back = None, not args.no_fetch_back
    if args.replay:
        import market_research_module as MRM
        raw = to_provider_shape(args.replay)
        if not raw:                                   # already the flat shape
            with open(args.replay, encoding="utf-8") as fh:
                raw = json.load(fh)
        dp, rt, bt = PR._profiles(args.carrier_type)
        cfg = MRM.RouteResearchConfig(
            origin=args.origin, destination=args.dest, origin_city=args.origin_city,
            destination_city=args.dest_city, origin_country=args.origin_country,
            destination_country=args.dest_country, airline=args.airline,
            demand_profile=dp, route_type=rt, buyer_type=bt)
        if args.fixture_urls:
            # pitch_verify drops any finding without a URL, correctly. A file of
            # hand-assembled source names therefore keeps nothing and proves
            # nothing. Stamping a fixture URL exercises the rest of the path.
            # example.invalid can never resolve, so this can only ever be a test.
            n = 0
            for rows in raw.values():
                for f in rows:
                    if not (f.get("url") or "").startswith("http"):
                        f["url"] = "https://example.invalid/fixture"
                        n += 1
            print("FIXTURE URLS: stamped %d finding(s). PLUMBING TEST ONLY, the "
                  "output deck carries no real attribution." % n)
        name_to_id = {b.name: b.block_id for b in MRM.generate_queries(cfg)}
        provider = ReplayProvider(raw, name_to_id)
        fetch_back = False
        print("REPLAY: %d block(s) from %s, no API call, no fetch-back"
              % (len(raw), os.path.basename(args.replay)))
    else:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            ap.error("ANTHROPIC_API_KEY is not set in this shell")
        print("LIVE: searching. Circa $4 and a few minutes.")

    deck_path, html_path, audit = PR.build_pitch(fc, inputs, provider=provider,
                                                 fetch_back=fetch_back,
                                                 contract=contract,
                                                 currency=args.currency,
                                                 prose_file=args.prose)
    audit.update(pre_audit)     # the sizing decided the frequency before the build
    report(audit, deck_path, html_path)

    # The copy is the last thing that happens and the most likely to fail, because
    # the destination is usually the deck somebody still has open in PowerPoint.
    # Losing a completed build to a locked file, after the engine runs and the
    # research, is not an acceptable way to end.
    out = args.out
    if out:
        import shutil
        try:
            shutil.copy2(deck_path, out)
            print("COPIED %s" % out)
        except (PermissionError, OSError) as e:
            stamped = "%s_%s%s" % (os.path.splitext(out)[0],
                                   __import__("time").strftime("%H%M%S"),
                                   os.path.splitext(out)[1])
            try:
                shutil.copy2(deck_path, stamped)
                print("COULD NOT WRITE %s (%s: %s)" % (out, type(e).__name__, e))
                print("   It is almost certainly open in PowerPoint. Written to")
                print("   %s instead. The build is complete either way." % stamped)
                out = stamped
            except Exception as e2:
                print("COULD NOT WRITE %s (%s) OR %s (%s)."
                      % (out, e, stamped, e2))
                print("   The deck is complete and still at %s" % deck_path)
                out = None
    with open(os.path.splitext(out or deck_path)[0] + "_audit.json", "w",
              encoding="utf-8") as fh:
        json.dump(audit, fh, indent=1, default=str)


if __name__ == "__main__":
    main()
