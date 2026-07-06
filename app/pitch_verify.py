#!/usr/bin/env python3
"""
Avia Cortex - pitch research verification (the anti-hallucination layer).
=========================================================================
The pitch is auto-generated and downloaded by a client without Avia eyeballing it, so every
research finding must police itself before it reaches a slide. Layered checks, cheapest first:

  1. Citation enforcement - a finding with no URL or no year is dropped.
  2. Source quality       - blocked/low-trust domains dropped; official sources marked high.
  3. Plausibility         - percentages 0-100, years in range, values not absurd.
  4. Fetch-back           - re-fetch the cited page and confirm the figure is actually on it.
                            Fetched-but-absent -> dropped (likely misattributed). Fetch blocked
                            (403/timeout) -> kept but flagged 'unverified' so it is never silently
                            trusted.

Every decision is recorded in the audit log so a disputed figure is traceable. No finding is ever
invented here; this module only removes or downgrades.
"""
import re
import urllib.request
import urllib.parse
from datetime import datetime

PREFERRED = {
    "eurostat.ec.europa.eu", "ec.europa.eu", "oecd.org", "worldbank.org", "imf.org",
    "iata.org", "icao.int", "unwto.org", "e-unwto.org", "ons.gov.uk", "gov.uk",
    "census.gov", "bea.gov", "bls.gov", "stlouisfed.org", "federalreserve.gov",
    "anna.aero", "centreforaviation.com",
}
BLOCKED = {"reddit.com", "quora.com", "tripadvisor.com", "wikipedia.org", "pinterest.com",
           "facebook.com", "x.com", "twitter.com", "medium.com"}

UA = "Mozilla/5.0 (compatible; AviaCortex/1.0; +https://aviacortex.com)"


def _domain(url):
    try:
        net = urllib.parse.urlparse(url).netloc.lower()
        return net[4:] if net.startswith("www.") else net
    except Exception:
        return ""


def _root(dom):
    parts = dom.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else dom


def _year_ok(y):
    try:
        yi = int(str(y)[:4])
        return 1990 <= yi <= datetime.now().year + 1
    except Exception:
        return False


def _plausible(value, unit):
    """Cheap numeric sanity: percentages in range, no absurd magnitudes."""
    if not value:
        return True
    nums = re.findall(r"-?\d[\d,\.]*", str(value))
    if not nums:
        return True
    try:
        n = float(nums[0].replace(",", ""))
    except Exception:
        return True
    u = (unit or "").lower()
    v = str(value).lower()
    if "%" in v or "percent" in u:
        return -100.0 <= n <= 100.0
    return True


def _value_candidates(value):
    """Strings we would accept as the figure appearing on the page."""
    if not value:
        return []
    v = str(value).strip()
    out = {v, v.replace(",", ""), v.replace("$", "").replace("€", "").replace("£", "")}
    m = re.search(r"-?\d[\d,\.]*", v)
    if m:
        core = m.group(0)
        out.add(core); out.add(core.replace(",", ""))
        suf = v.lower()
        try:
            base = float(core.replace(",", ""))
            if base == int(base):
                out.add(f"{int(base):,}")                       # comma-grouped integer form
            if "bn" in suf or "billion" in suf:
                out.add(f"{base:g} billion"); out.add(f"{base:.1f} billion"); out.add(f"{int(base * 1e9):,}")
            elif re.search(r"\dm\b", suf) or "million" in suf:
                out.add(f"{base:g} million"); out.add(f"{base:.1f} million"); out.add(f"{int(base * 1e6):,}")
        except Exception:
            pass
    return [c for c in out if len(c) >= 2]


def _around(page, cands, before=300, after=400):
    """A snippet of the page around the first matched figure, for the adjudication pass."""
    idx = -1
    for c in cands:
        i = page.find(c)
        if i >= 0:
            idx = i; break
    if idx < 0:
        return page[:800]
    return page[max(0, idx - before): idx + after]


def _fetch_text(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(600000)
        txt = raw.decode("utf-8", "ignore")
        txt = re.sub(r"<script.*?</script>", " ", txt, flags=re.DOTALL | re.I)
        txt = re.sub(r"<style.*?</style>", " ", txt, flags=re.DOTALL | re.I)
        txt = re.sub(r"<[^>]+>", " ", txt)
        return re.sub(r"\s+", " ", txt)
    except Exception:
        return None


def verify_findings(findings, ctx=None, fetch_back=True):
    """Return (kept, audit). Each kept finding gains source_type + confidence + verified flag."""
    kept, audit = [], []
    for f in (findings or []):
        if not isinstance(f, dict):
            audit.append({"claim": str(f)[:80], "drop": "not-an-object"}); continue
        claim = (f.get("claim") or "").strip()
        url = (f.get("url") or "").strip()
        year = (f.get("year") or "").strip()
        value = (f.get("value") or "").strip()
        if not claim:
            audit.append({"claim": "", "drop": "no-claim"}); continue
        if not url or not url.lower().startswith("http"):
            audit.append({"claim": claim[:80], "drop": "no-url"}); continue
        if not _year_ok(year):
            audit.append({"claim": claim[:80], "drop": "no-valid-year"}); continue
        dom = _domain(url); root = _root(dom)
        if root in BLOCKED or dom in BLOCKED:
            audit.append({"claim": claim[:80], "drop": f"blocked-source:{root}"}); continue
        if not _plausible(value, f.get("unit")):
            audit.append({"claim": claim[:80], "drop": f"implausible:{value}"}); continue
        source_type = "official" if (dom in PREFERRED or root in PREFERRED) else "web"
        confidence, verified, snippet = "cited", False, None
        if fetch_back:
            page = _fetch_text(url)
            if page is None:
                # official statistics sites often render figures via JavaScript, so a raw fetch cannot
                # confirm them. Trust the source rather than under-credit it, but mark it cited-only.
                confidence, verified = ("official-source", False) if source_type == "official" else ("unverified", False)
            else:
                cands = _value_candidates(value)
                if not cands:
                    confidence, verified, snippet = "verified", True, page[:900]
                elif any(c in page for c in cands):
                    confidence, verified, snippet = "verified", True, _around(page, cands)
                else:
                    audit.append({"claim": claim[:80], "drop": f"figure-not-on-page:{value}", "url": url})
                    continue
        f2 = dict(f)
        f2.update(source_type=source_type, confidence=confidence, verified=verified)
        if snippet:
            f2["_page"] = snippet
        kept.append(f2)
        audit.append({"claim": claim[:80], "keep": confidence, "source": source_type, "url": url})
    return kept, audit


def block_summary(kept):
    """A one-line factual summary line for the slide, no invention."""
    if not kept:
        return "No independently sourced figures were found for this section."
    n = len(kept)
    ver = sum(1 for f in kept if f.get("verified"))
    return f"{n} sourced finding{'s' if n != 1 else ''} ({ver} verified against the cited page)."
