#!/usr/bin/env python3
"""
Avia Cortex - researched airline route pitch (Stage 2).
=======================================================
build_pitch(fc, inputs) runs the market-research query framework through a research provider
(Claude web search by default), verifies every finding with pitch_verify, then assembles the
full pitch deck via city_pair_pptx_generator, backed by the calibrated forecast for all the
numbers. The model never supplies a commercial figure: forecast, catchment and economics come
from Cortex. Returns (deck_path, audit). Falls back to a clear error if no research key is set.
"""
import os
import sys
import json
import tempfile

import market_research_module as MRM
import city_pair_pptx_generator as CPG

# Paths come from config, never from here. config resolves every one through _env_path,
# so a machine moves its assets by setting AVIA_ASSETS and changing no code.
try:
    import config as _CFG
except Exception:                                   # pragma: no cover
    _CFG = None

# The Observatory deck path is the product, and from 8 August 2026 it is the default.
# AVIA_DECK_STYLE=legacy returns the unstyled generator, which is kept only as a way back.
# It was opt-in from the day it was written until 8 August, the variable was never set, and
# so no deck the application produced had ever been through it. A switch that has to be
# turned on to get the finished product is a switch pointing the wrong way.
OBSERVATORY = os.environ.get("AVIA_DECK_STYLE", "observatory").lower() != "legacy"

# The renderer lives in the repo, beside app/, as deck/. AVIA_DECK_V4 stays as an override
# for a machine that has not moved yet, and should be retired once every machine has.
_V4 = os.environ.get("AVIA_DECK_V4") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "deck")
if OBSERVATORY and _V4 not in sys.path:
    sys.path.insert(0, _V4)

# The imagery library is data with a rights record, so it is configured rather than
# bundled: see config.ASSETS_DIR. The fixture assets that render_observatory and
# test_visual_layer both read DO travel with the code, so they resolve inside deck/.
OBS_LIBRARY = os.environ.get("AVIA_OBS_LIBRARY") or (
    str(_CFG.OBS_LIBRARY_DIR) if _CFG is not None
    else os.path.join("C:" + os.sep, "assets", "observatory_library"))
OBS_ASSETS = os.path.join(_V4, "assets_obs")

# A fallback must report. Both of these were silent: a missing deck/ folder failed on
# import, and a missing library folder dropped the imagery resolver at line 417 below
# and built a deck with no photography and no complaint.
_DECK_OK = os.path.isdir(_V4)
_LIBRARY_OK = os.path.isdir(OBS_LIBRARY)
if OBSERVATORY and not _DECK_OK:
    sys.stderr.write(
        "pitch_report: the Observatory renderer is not at %s.\n"
        "  Set AVIA_DECK_V4 to the deck folder, or AVIA_DECK_STYLE=legacy to fall back.\n"
        % _V4)
if OBSERVATORY and _DECK_OK and not _LIBRARY_OK:
    sys.stderr.write(
        "pitch_report: the Observatory imagery library is not at %s, so decks will build\n"
        "  without photography. Set AVIA_OBS_LIBRARY or AVIA_ASSETS to where it lives.\n"
        % OBS_LIBRARY)
OBS_SAFE_FONTS = os.environ.get("AVIA_DECK_SAFE_FONTS", "1") != "0"
# Product decks are published by The Aviation Observatory, the separate company, not
# by Avia Solutions. Deliberate departure from the Avia house rule, product only.
DECK_AUTHOR = os.environ.get("AVIA_DECK_AUTHOR", "The Aviation Observatory")
import research_provider as RP
import pitch_verify as PV

# Which blocks are researched. Optional blocks used to be cut, and the cap of seven
# then cut one of the eight that remained, so a hub long-haul pitch reached the deck
# with no education section, no non-cannibalisation section and no economic context.
# The relevance matrix already decides what earns a place; a second cap on top of it
# was removing sections nobody had chosen to remove. Set AVIA_RESEARCH_RELEVANCE to
# "essential,include" and AVIA_RESEARCH_MAX_BLOCKS lower for a cheap test run.
_RESEARCH_RELEVANCE = set(
    x.strip() for x in os.environ.get(
        "AVIA_RESEARCH_RELEVANCE", "essential,include,optional").split(",") if x.strip())
_MAX_BLOCKS = int(os.environ.get("AVIA_RESEARCH_MAX_BLOCKS", "12"))


def _enum(name, val, default=None):
    cls = getattr(MRM, name, None)
    if cls is None:
        return default
    for cand in (val, val.upper()):
        m = getattr(cls, cand, None)
        if m is not None:
            return m
    # match by .value
    for m in cls:
        if getattr(m, "value", None) == val:
            return m
    return default


def _profiles(carrier_type):
    ct = (carrier_type or "FSC").upper()
    route_type = "lcc_p2p" if ct in ("LCC", "ULCC") else "hub_longhaul"
    return _enum("DemandProfile", "mixed"), _enum("RouteType", route_type), _enum("BuyerType", "airline")


def _connecting_cities(dem, top=15):
    # onward markets beyond the destination hub only (the "connecting via the hub" story); the behind
    # feed is domestic origin-side traffic and would mislabel this slide.
    rows = []
    for r in (dem.get("beyond_pdew") or []):
        rows.append({"city": r.get("name") or r.get("code"), "pax": round((r.get("pdew") or 0) * 365)})
    rows.sort(key=lambda x: -x["pax"])
    return rows[:top]


def _pptx_config(fc, inputs):
    o = fc["origin"]; d = fc["dest"]; dem = fc["demand"]; cap = fc["capacity"]
    ec = fc.get("economics") or {}
    airline = inputs.get("airline_name") or fc.get("airline") or "the airline"
    fmt = lambda n: f"{round(n or 0):,}"
    total = dem.get("total") or 0; load = cap.get("load") or 0
    exec_sum = (f"Cortex forecasts {fmt(total)} passengers each way per year on a nonstop "
                f"{o['city']} to {d['city']} service, flying at {round(load*100)}% load on a "
                f"{cap.get('aircraft','')} at {cap.get('freq','')} times a week. Demand is measured "
                f"from Sabre Global Demand Data point-of-origin traffic in the {o['city']} catchment, with the airline's "
                f"connecting feed behind {o['city']} and beyond {d['city']} added. The research that "
                f"follows is auto-compiled from cited public sources; verify figures before use.")
    why = [
        {"title": "Measured local market", "text":
            f"{fmt(dem.get('natural'))} each-way O&D in the catchment; the nonstop captures "
            f"{round((dem.get('qsi_share') or 0)*100)}% of it."},
        {"title": "Connecting feed", "text":
            f"The airline adds {fmt(dem.get('feed_behind'))} behind {o['city']} and "
            f"{fmt(dem.get('feed_beyond'))} beyond {d['city']} each way."},
        {"title": "Fits the aircraft", "text":
            f"{fmt(cap.get('carried'))} carried each way at {round(load*100)}% planned load on the "
            f"{cap.get('aircraft','')}."},
    ]
    return {
        "headline": f"{o['city']} to {d['city']}: a route pitch for {airline}",
        "origin": o["iata"], "destination": d["iata"], "origin_city": o["city"], "dest_city": d["city"],
        "airline_name": airline, "aircraft_type": cap.get("aircraft", ""), "seats": ec.get("seats", ""),
        "frequency": cap.get("freq", ""), "date": inputs.get("date", ""),
        "client_name": airline, "executive_summary": exec_sum,
        # ANCHOR ON THE CARRIED FIGURE (23 August 2026): dem.get("captured") is the raw uncapped
        # P2P demand (46,671 on the SJC-TPE case that surfaced this), not what the route actually
        # carries; grand_total above is already the carried total, so p2p_total + cnx_home_total +
        # cnx_dest_total did not sum to grand_total on the same slide. Same fault, same fix as
        # pitch_html.py and cortex_workbook.py's carried_split(): p2p_carried is the carried figure,
        # falling back to total only when there is no airline feed to carry (dashboard's own
        # convention for that case).
        "forecast": {"grand_total": total, "load_factor": load,
                     "p2p_total": dem.get("p2p_carried") if dem.get("p2p_carried") is not None else total,
                     "cnx_home_total": dem.get("feed_behind"),
                     "cnx_dest_total": dem.get("feed_beyond")},
        "connecting_cities": _connecting_cities(dem),
        "assumptions": {"qsi_adjustment": 1.0, "qsi_ceiling": 1.0,
                        "stimulation": dem.get("stimulation") or 1.0, "capture_rate": dem.get("qsi_share") or 0.0},
        "why_points": why,
    }


# Slide types that carry evidence and therefore must carry an attribution line.
# Covers, contents, dividers and the closing frame make no claim, so they do not.
_CONTENT_SLIDES = {"stat_row", "keynumbers", "table", "figure", "prose", "grid", "plate"}


def _deck_audit(spec):
    """What to read after a run, without opening the deck.

    Three things go wrong silently on this path: the value gets blanked and no
    slide qualifies as a key number, a slide loses its attribution line, and a
    section arrives with evidence but no argument. Report all three.
    """
    slides = spec["slides"]
    try:
        import deck_spec as DS
        over = DS.check(spec, verbose=False)
    except Exception:
        over = []
    return {
        "slides": len(slides),
        "over_budget": len(over),
        "over_budget_detail": over[:20],
        "by_type": {t: sum(1 for s in slides if s["type"] == t)
                    for t in sorted({s["type"] for s in slides})},
        "keynumbers_slides": sum(1 for s in slides if s["type"] == "keynumbers"),
        "keynumbers_values": sum(len(s.get("items") or []) for s in slides
                                 if s["type"] == "keynumbers"),
        "slides_without_source": [
            "%s (%s)" % (s.get("title") or s["type"], s["type"])
            for s in slides if s["type"] in _CONTENT_SLIDES and not s.get("source")],
    }


def _prose_from_file(path, deck_blocks):
    """Section prose written outside the pipeline, subject to the same guard.

    Used when the writing pass is done by hand or in a chat session rather than by a
    metered API call. The file is {"executive_summary": str, "blocks": {block_id: str}}.
    Every paragraph is still checked against that block's findings, and one that
    introduces a figure the research did not source is rejected, not repaired, exactly
    as the model-written path is. The provenance is recorded as "file" so a deck built
    this way is never mistaken for one the pipeline wrote unaided.
    """
    import json as _json
    import pitch_prose as PP
    with open(path, encoding="utf-8") as fh:
        doc = _json.load(fh)
    by_id = dict(doc.get("blocks") or {})
    notes, flags = {}, {}
    for b in deck_blocks:
        text = (by_id.get(b["block_id"]) or "").strip()
        if not text:
            notes[b["block_id"]] = "no paragraph supplied"
            continue
        stray = PP.check_no_new_figures(text, b["findings"])
        if stray:
            notes[b["block_id"]] = "rejected, figures not in findings: %s" % ", ".join(stray[:5])
            continue
        b["presentation_text"] = text
        notes[b["block_id"]] = "ok"
        f = PP.house_style_flags(text)
        if f:
            flags[b["block_id"]] = f
    summary = (doc.get("executive_summary") or "").strip()
    allowed = [f for b in deck_blocks for f in (b.get("findings") or [])]
    snote = "ok"
    if summary:
        stray = PP.check_no_new_figures(summary, allowed)
        if stray:
            summary, snote = "", "rejected, figures not in findings: %s" % ", ".join(stray[:5])
    out = {"source": "file", "blocks": notes, "executive_summary": summary,
           "executive_summary_note": snote,
           "written": sum(1 for v in notes.values() if v == "ok")}
    if flags:
        out["house_style_flags"] = flags
    return out


def _write_prose(prov, deck_blocks, ctx, forecast_line=""):
    """Fill presentation_text on every block, and write the one-page proposition.

    The provider owns the model client, so the writing pass rides on it rather than
    opening a second connection. A replay provider has no client, and the run then
    proceeds with no prose, which the report already flags. Every paragraph is
    checked against the findings before it is accepted.
    """
    getter = getattr(prov, "_client_obj", None)
    if not callable(getter):
        return {"skipped": "provider has no model client"}
    try:
        client = getter()
    except Exception as e:
        return {"skipped": "no model client: %s" % e}
    import pitch_prose as PP
    notes, flags = {}, {}
    for b in deck_blocks:
        text, note = PP.write_block(client, b["block_id"], b["block_name"],
                                    b["findings"], ctx)
        b["presentation_text"] = text
        notes[b["block_id"]] = note
        f = PP.house_style_flags(text)
        if f:
            flags[b["block_id"]] = f
    summary, snote = PP.write_executive_summary(client, deck_blocks, ctx, forecast_line)
    out = {"blocks": notes, "executive_summary": summary, "executive_summary_note": snote,
           "written": sum(1 for v in notes.values() if v == "ok")}
    if flags:
        out["house_style_flags"] = flags
    return out


def build_pitch(fc, inputs=None, provider=None, fetch_back=True, contract=None,
                currency="USD", prose_file=None):
    """Returns (deck_path, html_path, audit_dict).

    contract   a deck_contract dict. Without it the deck carries no forecast.
    currency   stated by the caller, following the asset's home jurisdiction. It is
               written into the revenue column head and never inferred.
    prose_file section prose written outside the pipeline, same guard applied.
    Raises RuntimeError if no research provider is available.
    """
    inputs = dict(inputs or {})
    o = fc["origin"]; d = fc["dest"]
    _code = (inputs.get("airline_name") or fc.get("airline") or "").strip()
    try:
        import airline_names as AN
        inputs["airline_name"] = AN.AIRLINES.get(_code.upper()) or _code or "the airline"
    except Exception:
        inputs["airline_name"] = _code or "the airline"
    prov = provider or RP.get_provider()
    if not prov.available():
        raise RuntimeError("No research provider available: set ANTHROPIC_API_KEY (and install the "
                           "anthropic package) on the server, or choose the non-researched Full report.")

    dp, rt, bt = _profiles(fc.get("carrier_type"))
    cfg = MRM.RouteResearchConfig(
        origin=o["iata"], destination=d["iata"], origin_city=o["city"], destination_city=d["city"],
        origin_country=o.get("country", ""), destination_country=d.get("country", ""),
        airline=(inputs.get("airline_name") or fc.get("airline") or ""),
        demand_profile=dp, route_type=rt, buyer_type=bt)
    blocks = MRM.generate_queries(cfg)

    ctx = {"origin": o["iata"], "destination": d["iata"], "origin_city": o["city"],
           "destination_city": d["city"], "airline": (inputs.get("airline_name") or fc.get("airline") or "")}
    research_blocks, audit = {}, {"route": f'{o["iata"]}-{d["iata"]}', "blocks": []}
    done = 0
    for b in blocks:
        rel = getattr(getattr(b, "relevance", None), "value", str(getattr(b, "relevance", ""))).lower()
        if rel not in _RESEARCH_RELEVANCE or done >= _MAX_BLOCKS:
            continue
        queries = [getattr(q, "query", str(q)) for q in getattr(b, "queries", [])]
        raw, meta = prov.research_block(getattr(b, "name", b.block_id), queries, ctx)
        kept, block_audit = PV.verify_findings(raw, ctx, fetch_back=fetch_back)
        # second-pass adjudication: does the cited page text actually support the specific claim?
        final = []
        adjudicator = getattr(prov, "adjudicate", None)
        for f in kept:
            snip = f.pop("_page", None)
            if snip and adjudicator and not adjudicator(f.get("claim", ""), f.get("value", ""), snip):
                block_audit.append({"claim": (f.get("claim") or "")[:80],
                                    "drop": "adjudication:not-supported", "url": f.get("url")})
                continue
            conf = f.get("confidence", "cited")
            lbl = {"verified": "verified", "official-source": "source-cited",
                   "unverified": "cited", "cited": "cited"}.get(conf, conf)
            src = (f.get("source_name") or "").strip()
            f["source_name"] = f"{src} - {lbl}" if src else lbl
            # The legacy generator printed "claim (value)" on one bullet, so the
            # figure had to be blanked to avoid printing it twice. The
            # Observatory renderer sets the value as a separate display number
            # beside the sentence, which is the house idiom, so it NEEDS the
            # value. Keep it, and blank a copy only for the legacy path.
            f["value_display"] = f.get("value") or ""
            if not OBSERVATORY:
                f["value"] = ""
            final.append(f)
        if final:
            research_blocks[b.block_id] = {
                "findings": final, "summary": PV.block_summary(final),
                "block_name": getattr(b, "name", b.block_id), "relevance": rel}
        audit["blocks"].append({"block": b.block_id, "relevance": rel, "found": len(raw or []),
                                "kept": len(final), "search_meta": meta, "decisions": block_audit})
        done += 1

    # The quantitative core. Without a contract the deck is research only, which is
    # what the first live run produced, so the absence is recorded rather than left
    # to be noticed.
    fcspec, fcline, assumptions = None, "", []
    figures, route_facts, fig_sources = {}, [], {}
    if OBSERVATORY:                   # forecast_spec lives with the v4 renderers
        import forecast_spec as FS
        if contract:
            fcspec = FS.from_contract(contract, currency=currency)
            fcline = FS.headline_sentence(contract)
            assumptions = FS.assumptions_from_contract(contract)
            audit["forecast"] = dict(FS.describe(fcspec), source="deck contract")
            audit["figures"] = {"drawn": [], "not_drawn": {
                "route_map": "contract path: deck_figures reads the engine "
                             "output, not a deck contract",
                "demand_build": "contract path: deck_figures reads the engine "
                                "output, not a deck contract"}}
        elif fc.get("demand") and not fc.get("_stub"):
            # The figures are drawn BEFORE the forecast spec, because the
            # segments table drops the rows the chart takes and has to know
            # whether the chart drew.
            import deck_figures as DF
            figdir = os.path.join(tempfile.gettempdir(),
                                  'avia_figs_{}_{}'.format(o["iata"], d["iata"]))
            figures, fig_notes = DF.build(fc, figdir, source=FS.SOURCE)
            route_facts = DF.route_facts(fc)
            charted = bool(figures.get("demand_build"))
            fcspec = FS.from_forecast(fc, currency=currency, charted=charted)
            fcline = FS.headline_from_forecast(fc)
            assumptions = FS.assumptions_from_forecast(fc)
            audit["forecast"] = dict(FS.describe(fcspec), source="calibrated engine")
            audit["figures"] = {"drawn": sorted(figures), "not_drawn": fig_notes}
            if not charted:
                # a fallback that reports: the table quietly reverting to the
                # full build is exactly the shape of bug we fixed on 6 August
                audit["figures"]["segments_table"] = (
                    "reverted to the full demand build, because the chart that "
                    "would have carried the volume rows did not draw")
            # Does the schedule as entered stand up commercially. Never blocks: a
            # client may print the schedule they asked for. It just says so first.
            # _schedule_sized is set by the runner when --freq auto chose the
            # frequency. It changes what a thin fill MEANS: on a frequency the
            # user entered it is an input to change, on a sized one the market is
            # the constraint and no frequency fixes it.
            _v = FS.schedule_viability(fc, sized=bool(fc.get("_schedule_sized")))
            if _v:
                audit["schedule_viability"] = _v
        else:
            audit["forecast"] = {"present": False,
                                 "note": "no contract and no engine demand; research only"}

    # The airport charts. These come from the STORES, not from the research, so
    # they are drawn whether or not there is a forecast: a research-only deck
    # still has an origin and a destination, and the OAG, ACI and DOT series for
    # both exist regardless. They are what fills the research sections, which ran
    # about 60% empty on every deck before this.
    if OBSERVATORY:
        try:
            import deck_figures as DF
            figdir = os.path.join(tempfile.gettempdir(),
                                  'avia_figs_{}_{}'.format(o["iata"], d["iata"]))
            afigs, anotes, asrc = DF.build_airport(fc, figdir)
            figures.update(afigs)
            fig_sources.update(asrc)
            fa = audit.setdefault("figures", {"drawn": [], "not_drawn": {}})
            fa["drawn"] = sorted(set(fa.get("drawn") or []) | set(afigs))
            fa.setdefault("not_drawn", {}).update(anotes)
        except Exception as e:
            audit.setdefault("figures", {}).setdefault("not_drawn", {})[
                "airport_charts"] = "%s: %s" % (type(e).__name__, e)

    config = _pptx_config(fc, inputs)
    base = f'AviaCortex_Pitch_{o["iata"]}_{d["iata"]}'
    deck_path = os.path.join(tempfile.gettempdir(), base + ".pptx")
    if OBSERVATORY:
        # house-style path: research -> deck_spec -> Observatory PowerPoint
        import spec_from_research as SFR
        import render_pptx as RPX
        import avia_slots
        # PV.block_summary returns a verification count, "5 sourced findings (3
        # verified against the cited page)". The legacy generator set it as a
        # caption under the bullets. The Observatory path reads `summary` as the
        # section's opening paragraph AND as the divider strap, so a build
        # statistic would print as the argument on a client-facing sales deck.
        # Strip it for the deck and keep it in the audit. The section is then
        # correctly reported as thin by missing_prose, which is the true state
        # until a writing pass fills presentation_text.
        deck_blocks = [{"block_id": bid, "block_name": b.get("block_name") or bid,
                        "relevance": b.get("relevance", "include"),
                        "summary": "", "presentation_text": "",
                        "data_gaps": [], "findings": b["findings"]}
                       for bid, b in research_blocks.items()]
        # The writing pass. Findings remain the only source of fact; a paragraph
        # that introduces a figure of its own is rejected and the section is
        # reported as thin rather than shipped.
        prose_audit = (_prose_from_file(prose_file, deck_blocks) if prose_file
                       else _write_prose(prov, deck_blocks, ctx, fcline))
        if prose_audit:
            audit["prose"] = prose_audit
        deck_research = {"origin_city": o["city"], "destination_city": d["city"],
                         "executive_summary": prose_audit.get("executive_summary", "")
                         if prose_audit else "",
                         "blocks": deck_blocks}
        spec = SFR.build_spec(
            deck_research, forecast=fcspec,
            codename=config.get("codename") or f'{o["iata"]}-{d["iata"]}',
            title=config.get("deck_title")
                  or f'A direct link between\n{o["city"]} and {d["city"]}',
            strap=config.get("strap") or "",
            prepared_for=config.get("prepared_for") or o.get("name") or "",
            date=config.get("date") or "",
            include_optional=True, max_sections=len(deck_blocks),
            assumptions=assumptions, forecast_line=fcline, author=DECK_AUTHOR,
            figures=figures, route_facts=route_facts, fig_sources=fig_sources)
        resolver = None
        if os.path.isdir(OBS_LIBRARY):
            resolver = avia_slots.SlotResolver(
                brand_library=OBS_LIBRARY, project=spec["meta"]["codename"],
                origin=(o.get("lon"), o.get("lat")) if o.get("lon") else None,
                use="confidential")
        RPX.render(spec, deck_path, safe_fonts=OBS_SAFE_FONTS,
                   assets_dir=OBS_ASSETS, resolver=resolver)
        audit["sections_without_prose"] = SFR.missing_prose(deck_research)
        audit["deck"] = _deck_audit(spec)
        audit["block_verification"] = {bid: b.get("summary", "")
                                       for bid, b in research_blocks.items()}
    else:
        CPG.generate_presentation(config, research_blocks, deck_path)
    # the interactive HTML digital pitch (self-contained, emailable, iPad-friendly)
    html_path = os.path.join(tempfile.gettempdir(), base + ".html")
    try:
        import pitch_html as PH
        with open(html_path, "w", encoding="utf-8") as fh:
            fh.write(PH.build_html_pitch(fc, research_blocks, inputs))
    except Exception:
        html_path = None
    audit["blocks_researched"] = done
    audit["total_kept"] = sum(x["kept"] for x in audit["blocks"])
    return deck_path, html_path, audit
