#!/usr/bin/env python3
"""
Avia Cortex - research provider (fills the market-research query framework with sourced findings).
==================================================================================================
A thin, swappable interface so the pitch pipeline does not care which model does the web research.
The Anthropic provider uses Claude's server-side web_search tool and returns STRICT JSON findings,
each carrying a claim, a value, a year and a working source URL. The prompt forbids unsourced
figures: no citation means the finding is dropped downstream. Swap the provider (Gemini, etc.)
without touching the pitch builder.

Key is read from the environment (ANTHROPIC_API_KEY); never hard-coded. Model is configurable via
AVIA_RESEARCH_MODEL (default a current Claude Sonnet).
"""
import os
import json
import re

DEFAULT_MODEL = os.environ.get("AVIA_RESEARCH_MODEL", "claude-sonnet-4-6")
ADJ_MODEL = os.environ.get("AVIA_ADJUDICATE_MODEL", "claude-haiku-4-5-20251001")

# Authoritative sources are preferred; content farms and forums are discouraged at the search step.
PREFERRED_DOMAINS = [
    "eurostat.ec.europa.eu", "ec.europa.eu", "oecd.org", "worldbank.org", "imf.org",
    "iata.org", "icao.int", "unwto.org", "e-unwto.org", "ons.gov.uk", "gov.uk",
    "census.gov", "bea.gov", "bls.gov", "statista.com", "tradingeconomics.com",
    "anna.aero", "centreforaviation.com", "routesonline.com", "airport-technology.com",
]
BLOCKED_DOMAINS = ["reddit.com", "quora.com", "tripadvisor.com", "wikipedia.org",
                   "pinterest.com", "facebook.com", "x.com", "twitter.com"]

SYSTEM = (
    "You are an aviation market-research analyst compiling sourced facts for an airline route pitch. "
    "Report only figures you have found on a retrievable public web page, and give a working source URL "
    "and the year for every figure. Cite the PRIMARY source: the original publisher of the data (a "
    "national statistics office, Eurostat, OECD, World Bank, IMF, UNWTO, IATA, ICAO, the airport "
    "authority, or the company's own filing), not a blog, trade body, press release or news article that "
    "merely repeats someone else's number. Make each claim state precisely what the figure measures and "
    "the geography and year it applies to. Never estimate, extrapolate or invent a number. If you cannot "
    "find a primary-sourced figure for a question, omit it. Return ONLY a JSON array, no prose."
)

FINDING_SPEC = (
    'Return a JSON array of findings. Each finding is an object with EXACTLY these keys: '
    '"claim" (a COMPLETE, self-contained sentence stating the fact in full, with the figure and the '
    'year and place written into the sentence so it reads well as-is on a slide, e.g. "US visitor '
    'arrivals to Taiwan reached 651,264 in 2024, a record high."), "value" (the single headline figure '
    'from that sentence, for emphasis, e.g. "651,264" or "$185.7bn" or "34%"; leave "" only for a '
    'purely qualitative fact), "unit" (e.g. "passengers", "USD", "%", or ""), "year" (4-digit string), '
    '"source_name" (the publisher), "url" (the exact page the fact is on). NEVER write a placeholder '
    'like "this many", "a specific amount" or "this figure" in the claim; always write the actual '
    'number into the sentence. Prefer facts that carry a figure, but a well-sourced qualitative fact '
    'that materially supports the route (for example a named company operating in both cities) is '
    'allowed with "value" left "". Omit anything you cannot attach a real URL and year to. '
    'Maximum 5 findings. Return [] if nothing is sourced.'
)


class ResearchProvider:
    """Interface. Implementations fill one research block with sourced findings."""
    def available(self):
        return False

    def research_block(self, block_name, queries, ctx):
        raise NotImplementedError


def _extract_json_array(text):
    """Pull the first JSON array out of a model reply, tolerant of code fences / stray prose."""
    if not text:
        return []
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
        return data if isinstance(data, list) else []
    except Exception:
        return []


class AnthropicResearchProvider(ResearchProvider):
    def __init__(self, model=None, max_uses=5, timeout=120):
        self.model = model or DEFAULT_MODEL
        self.max_uses = max_uses
        self.timeout = timeout
        self._key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        self._client = None

    def available(self):
        if not self._key:
            return False
        try:
            import anthropic  # noqa: F401
            return True
        except Exception:
            return False

    def _client_obj(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._key, timeout=self.timeout)
        return self._client

    def research_block(self, block_name, queries, ctx):
        """Run one block's questions through Claude + web search. Returns (findings, meta)."""
        client = self._client_obj()
        qlines = "\n".join(f"- {q}" for q in queries[:8])
        route = (f'Route: {ctx.get("origin_city")} ({ctx.get("origin")}) to '
                 f'{ctx.get("destination_city")} ({ctx.get("destination")}); '
                 f'airline {ctx.get("airline") or "new entrant"}.')
        prompt = (f"{route}\nResearch block: {block_name}.\nAnswer these questions with sourced, "
                  f"current figures:\n{qlines}\n\n{FINDING_SPEC}")
        try:
            resp = client.messages.create(
                model=self.model, max_tokens=1500, system=SYSTEM,
                messages=[{"role": "user", "content": prompt}],
                tools=[{"type": "web_search_20250305", "name": "web_search",
                        "max_uses": self.max_uses, "blocked_domains": BLOCKED_DOMAINS}],
            )
        except Exception as e:
            return [], {"error": str(e), "block": block_name}
        # concatenate the model's text blocks (the final answer carries the JSON)
        text = ""
        searches = 0
        for blk in (resp.content or []):
            t = getattr(blk, "type", "")
            if t == "text":
                text += getattr(blk, "text", "")
            elif t in ("server_tool_use", "web_search_tool_result"):
                searches += 1
        findings = _extract_json_array(text)
        return findings, {"block": block_name, "searches": searches,
                          "model": self.model, "raw_chars": len(text)}

    def adjudicate(self, claim, value, snippet, model=None):
        """Second-pass check: does the cited page text actually support this exact claim and value,
        including what the number refers to? Returns True (supported) / False (not). A cheap no-search
        call on a small model. Fails open to True on any API error, so a transient blip never nukes a
        finding the deterministic checks already passed; it only removes clear misreads."""
        if not snippet:
            return True
        try:
            client = self._client_obj()
            prompt = (f"Claim: {claim}\nReported value: {value}\n\nExcerpt from the cited source page:\n"
                      f'"""{snippet[:1600]}"""\n\nDoes this excerpt support that exact claim and value, '
                      f"including what the number refers to and its geography and year? "
                      f"Reply with ONE word: SUPPORTED or NOT_SUPPORTED.")
            resp = client.messages.create(model=(model or ADJ_MODEL), max_tokens=16,
                                           messages=[{"role": "user", "content": prompt}])
            txt = ""
            for blk in (resp.content or []):
                if getattr(blk, "type", "") == "text":
                    txt += getattr(blk, "text", "")
            return "NOT_SUPPORTED" not in txt.upper()
        except Exception:
            return True


def get_provider(name=None):
    """Factory. Defaults to Anthropic; extend here for Gemini or others."""
    name = (name or os.environ.get("AVIA_RESEARCH_PROVIDER", "anthropic")).lower()
    if name == "anthropic":
        return AnthropicResearchProvider()
    return AnthropicResearchProvider()
