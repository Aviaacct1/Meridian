#!/usr/bin/env python3
"""
Avia Cortex - research smoke test.  Run this once after setting ANTHROPIC_API_KEY to confirm the
key, the anthropic package, the web search tool and the verification layer all work, before you
spend time (and pennies) generating full pitch decks.

    setx ANTHROPIC_API_KEY "sk-ant-..."      (once, new terminal after)   OR
    $env:ANTHROPIC_API_KEY = "sk-ant-..."    (this session only)
    py -3.12 test_research.py
"""
import research_provider as RP
import pitch_verify as PV

p = RP.get_provider()
print("provider:", type(p).__name__, "| available:", p.available(), "| model:", getattr(p, "model", "?"))
if not p.available():
    print("Not available. Set ANTHROPIC_API_KEY and run:  py -3.12 -m pip install anthropic")
    raise SystemExit(1)

ctx = {"origin": "SJC", "destination": "TPE", "origin_city": "San Jose",
       "destination_city": "Taipei", "airline": "BR"}
queries = ["San Jose California metro population 2024",
           "Santa Clara County GDP 2023", "tech companies San Jose with Taiwan operations"]
print("\nresearching one block via web search…")
findings, meta = p.research_block("Economic context", queries, ctx)
print("meta:", meta)
print(f"\nmodel returned {len(findings)} raw finding(s)")

kept, audit = PV.verify_findings(findings, ctx, fetch_back=True)
print(f"\n{len(kept)} kept after the deterministic checks; running adjudication…\n")
final = []
for k in kept:
    snip = k.pop("_page", None)
    ok = p.adjudicate(k.get("claim", ""), k.get("value", ""), snip) if snip else True
    tag = f"{k.get('confidence')}|{'adj-OK' if ok else 'adj-DROP'}"
    print(f"  [{tag}] {k.get('value')} {k.get('unit')} - {k.get('claim')[:66]}")
    print(f"        {k.get('source_name')}  {k.get('url')}")
    if ok:
        final.append(k)
print(f"\n{len(final)} finding(s) survive to the slide.")
print("\nverification decisions:")
for a in audit:
    tag = a.get("keep") and f"KEEP({a['keep']})" or f"DROP({a.get('drop')})"
    print(f"  {tag}: {a.get('claim')}")
