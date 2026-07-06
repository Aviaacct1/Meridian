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
import json
import tempfile

import market_research_module as MRM
import city_pair_pptx_generator as CPG
import research_provider as RP
import pitch_verify as PV

# essential + include blocks are researched; optional/skip are left out to control cost/latency
_RESEARCH_RELEVANCE = {"essential", "include"}
_MAX_BLOCKS = 7


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
                f"from Sabre point-of-origin traffic in the {o['city']} catchment, with the airline's "
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
        "forecast": {"grand_total": total, "load_factor": load,
                     "p2p_total": dem.get("captured"), "cnx_home_total": dem.get("feed_behind"),
                     "cnx_dest_total": dem.get("feed_beyond")},
        "connecting_cities": _connecting_cities(dem),
        "assumptions": {"qsi_adjustment": 1.0, "qsi_ceiling": 1.0,
                        "stimulation": dem.get("stimulation") or 1.0, "capture_rate": dem.get("qsi_share") or 0.0},
        "why_points": why,
    }


def build_pitch(fc, inputs=None, provider=None, fetch_back=True):
    """Returns (deck_path, audit_dict). Raises RuntimeError if no research provider is available."""
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
            f["value"] = ""   # the claim sentence already carries the figure; avoid a duplicate on the slide
            final.append(f)
        if final:
            research_blocks[b.block_id] = {"findings": final, "summary": PV.block_summary(final)}
        audit["blocks"].append({"block": b.block_id, "relevance": rel, "found": len(raw or []),
                                "kept": len(final), "search_meta": meta, "decisions": block_audit})
        done += 1

    config = _pptx_config(fc, inputs)
    base = f'AviaCortex_Pitch_{o["iata"]}_{d["iata"]}'
    deck_path = os.path.join(tempfile.gettempdir(), base + ".pptx")
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
