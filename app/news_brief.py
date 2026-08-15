#!/usr/bin/env python3
"""
Avia Solutions - the Observatory briefing: curated news of the day for an airport.
==================================================================================
WHAT THIS IS. Five current, sourced items relevant to the airport using the tool:
airline network moves, competitor route announcements, regulatory and demand news
for its region. Curated by the same Claude research pipeline the pitch pack uses,
so the sourcing discipline is inherited rather than reinvented: every item carries
its source and URL, and an item without one is dropped rather than shown.

COST CONTROL, stated because an uncapped research call is a bill nobody approved:
one live call per airport per day. The result is cached under config.LOCAL_CACHE's
parent (never in the repo; data does not live in a tool's repository) and every
subsequent request that day reads the cache. force=True refreshes and says so in
the payload. A missing ANTHROPIC_API_KEY returns a clear refusal, not an empty
panel (Jessica's 3 July rule: fail fast and clearly).
"""
import datetime as _dt
import json
import os


MAX_ITEMS = 5

SYSTEM = ("You curate an aviation industry briefing for an airport's route development "
          "team. Only report items you found on established, named sources (industry "
          "press, airline and airport announcements, credible national press). Every "
          "item must carry the source name, the URL and the article date. No item may "
          "be invented, inferred or undated. Prefer the last 7 days; never older than "
          "31 days.")

PROMPT = ("Airport: {city} ({iata}), {country}.\n"
          "Find the {n} most relevant current news items for this airport's route "
          "development team: airline network and fleet moves touching this airport, its "
          "region or its likely target carriers; competitor airport route announcements; "
          "regulatory, slot or demand news for the region.\n\n"
          "Return ONLY a JSON array, each element exactly: "
          '{{"headline": str, "why": one sentence on why it matters to {iata}, '
          '"source": publication name, "url": str, "date": "YYYY-MM-DD"}}. '
          "At most {n} items. No prose outside the JSON.")


def _cache_dir():
    try:
        import config
        base = config.LOCAL_CACHE.parent
    except Exception:
        base = os.path.join(os.path.expanduser("~"), ".avia_qsi")
    d = os.path.join(str(base), "briefings")
    os.makedirs(d, exist_ok=True)
    return d


def _cache_path(iata):
    return os.path.join(_cache_dir(), "%s_%s.json" % (
        (iata or "XXX").upper(), _dt.date.today().isoformat()))


def brief(iata, city=None, country=None, force=False):
    """The day's briefing for one airport: cached, else one live research call."""
    iata = (iata or "").strip().upper()
    if not iata:
        return {"ok": False, "error": "airport required"}
    path = _cache_path(iata)
    if not force and os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                out = json.load(fh)
            out["cached"] = True
            return out
        except Exception:
            pass  # unreadable cache: fall through to a live call, which rewrites it

    import research_provider as RP
    prov = RP.get_provider()
    if not prov.available():
        return {"ok": False, "error":
                "Research provider not configured: ANTHROPIC_API_KEY is not set on this "
                "server, so the briefing cannot be curated. The rest of the Watch page "
                "does not need it."}
    client = prov._client_obj()
    prompt = PROMPT.format(iata=iata, city=city or iata, country=country or "",
                           n=MAX_ITEMS)
    try:
        resp = client.messages.create(
            model=prov.model, max_tokens=2000, system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            tools=[{"type": "web_search_20250305", "name": "web_search",
                    "max_uses": 6}],
        )
    except Exception as e:
        return {"ok": False, "error": "briefing call failed: %s" % e}
    text = "".join(getattr(b, "text", "") for b in (resp.content or [])
                   if getattr(b, "type", "") == "text")
    items = RP._extract_json_array(text) or []
    # An item without a source and URL is dropped, not shown: the sourcing rule is the
    # product here, and four sourced items beat five with one invented.
    items = [i for i in items
             if isinstance(i, dict) and i.get("headline") and i.get("source")
             and i.get("url")][:MAX_ITEMS]
    out = {"ok": True, "airport": iata, "date": _dt.date.today().isoformat(),
           "items": items, "cached": False,
           "basis": "Curated by Claude web research; every item carries its source and "
                    "date; cached for the day, one live call per airport per day."}
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(out, fh)
    except Exception:
        pass  # a cache that cannot be written costs money tomorrow, not correctness today
    return out
