#!/usr/bin/env python3
"""
Avia Cortex - research provider (fills the market-research query framework with sourced findings).
==================================================================================================
A thin, swappable interface so the pitch pipeline does not care which model does the web research.
The Anthropic provider uses Claude's server-side web_search tool and returns STRICT JSON findings,
each carrying a claim, a value, a year and a working source URL. The prompt forbids unsourced
figures: no citation means the finding is dropped downstream. Swap the provider (Gemini, etc.)
without touching the pitch builder.

Key is read from the environment (ANTHROPIC_API_KEY), or from a gitignored
anthropic_key.txt beside this file; never hard-coded. Model is configurable via
AVIA_RESEARCH_MODEL (default a current Claude Sonnet).
"""
import os
import json
import re

# "claude-sonnet-4-6" was never a real Anthropic model ID (John, 22 August: live run
# reported "0 finds" on every block). Every research_block() call was failing at
# client.messages.create() with a model-not-found error, caught silently by the
# try/except below, so raw=[] for every block regardless of the route or the key.
# Current self-serve IDs are claude-fable-5, claude-opus-5, claude-sonnet-5 and
# claude-haiku-4-5-20251001; Sonnet is the right tier for sourced web research.
DEFAULT_MODEL = os.environ.get("AVIA_RESEARCH_MODEL", "claude-sonnet-5")
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
    '"caption" (the line that sits UNDER the headline figure on a slide: UNDER 90 CHARACTERS, and it '
    'must NOT repeat the figure itself. It says what the figure counts, where and when. For the value '
    '"1.59m" a good caption is "Passengers in 2025, up 18.1%, the fastest growth of Italy\'s three '
    'north-western gateways". A caption that restates the whole claim is wrong), '
    '"source_name" (the publisher), "url" (the exact page the fact is on). NEVER write a placeholder '
    'like "this many", "a specific amount" or "this figure" in the claim; always write the actual '
    'number into the sentence. Prefer facts that carry a figure, but a well-sourced qualitative fact '
    'that materially supports the route (for example a named company operating in both cities) is '
    'allowed with "value" left "". Omit anything you cannot attach a real URL and year to. '
    'There is NO cap on the number of findings: return every fact you can source properly, up to '
    '{n}. Do not pad with weak or tangential facts to reach that number, and do not stop at five '
    'good ones if you have found fifteen. Return [] if nothing is sourced.'
)

# Findings the model may return per block. The old cap of five was set before the
# verification layer existed. Roughly six in ten findings are removed downstream by
# pitch_verify and the adjudication pass, so a cap of five was leaving two on a slide.
MAX_FINDINGS = int(os.environ.get("AVIA_RESEARCH_MAX_FINDINGS", "15"))
# Fifteen findings will not fit in 1500 tokens; the reply was being truncated mid-array
# long before the cap was the binding constraint.
MAX_TOKENS = int(os.environ.get("AVIA_RESEARCH_MAX_TOKENS", "8000"))


# MERGED 6 Aug 2026 from the site copy: the server reads its key from a gitignored
# file when the environment variable was not exported into the shell that started
# it, which is how the researched pitch survives a restart.
def _load_api_key():
    """Anthropic key (Avia Solutions): env ANTHROPIC_API_KEY first, else the first non-comment line of
    anthropic_key.txt next to this file - so the researched-pitch key survives a server restart even when
    the env var was not exported into that shell. The file is git-ignored (a secret)."""
    k = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    if k:
        return k
    fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "anthropic_key.txt")
    if os.path.exists(fp):
        for line in open(fp, encoding="utf-8"):
            s = line.strip()
            if s and not s.startswith("#"):
                return s
    return ""


class ResearchProvider:
    """Interface. Implementations fill one research block with sourced findings."""
    def available(self):
        return False

    def research_block(self, block_name, queries, ctx):
        raise NotImplementedError


def _extract_json_array(text):
    """Pull the first JSON array out of a model reply, tolerant of code fences / stray prose.

    A truncated reply has no closing bracket, so the whole block used to return
    nothing and the run reported "found 0" for a block that had in fact found
    plenty. With the finding cap lifted that failure mode matters, so a truncated
    array is salvaged down to its last complete object.
    """
    if not text:
        return []
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            return data if isinstance(data, list) else []
        except Exception:
            pass
    start = text.find("[")
    if start < 0:
        return []
    frag = text[start:]
    for end in range(len(frag), start, -1):
        if frag[end - 1] != "}":
            continue
        try:
            data = json.loads(frag[:end] + "]")
            if isinstance(data, list) and data:
                return data
        except Exception:
            continue
    return []


class AnthropicResearchProvider(ResearchProvider):
    def __init__(self, model=None, max_uses=10, timeout=240):
        self.model = model or DEFAULT_MODEL
        self.max_uses = max_uses
        self.timeout = timeout
        self._key = _load_api_key()
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
                  f"current figures:\n{qlines}\n\n{FINDING_SPEC.format(n=MAX_FINDINGS)}")
        try:
            resp = client.messages.create(
                model=self.model, max_tokens=MAX_TOKENS, system=SYSTEM,
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
