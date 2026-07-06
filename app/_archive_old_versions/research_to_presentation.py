"""
Avia Solutions  Research-to-Presentation Pipeline
====================================================
Executes live web research for a route, structures findings,
feeds them into the narrative generator, and produces a
fully-populated PPTX presentation.

This module bridges the gap between:
  - market_research_module.py (query generation)
  - market_research_executor.py (findings structure)
  - narrative_generator.py (prose generation)
  - city_pair_pptx_generator.js (PPTX output)

Usage in portal:
    from research_to_presentation import auto_research_and_narrate
    enriched_config = auto_research_and_narrate(pptx_config)

Usage standalone:
    python research_to_presentation.py --config route_config.json
"""

import json
import os
import subprocess
import sys
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Import Avia modules
try:
    from market_research_module import (
        RouteResearchConfig, DemandProfile, RouteType as MRRouteType,
        BuyerType, generate_queries, get_relevance_matrix, Relevance,
    )
    from market_research_executor import (
        ResearchExecutor, ResearchOutput, BlockFindings, Finding, Citation,
        make_finding, add_citation, get_execution_sequence,
        generate_execution_plan, generate_json_output, quick_research,
    )
    from narrative_generator import NarrativeGenerator, generate_narrative
    HAS_MODULES = True
except ImportError as e:
    HAS_MODULES = False
    print(f"Warning: Missing module - {e}")


# ============================================================================
# RESEARCH BLOCK DEFINITIONS  what data each block needs
# ============================================================================

BLOCK_SPECS = {
    "economic_context": {
        "section": "S4",
        "queries": [
            "{dest_city} median household income",
            "{dest_country} GDP growth forecast {year}",
            "{origin_country} GDP growth forecast {year}",
            "{dest_city} population metro area",
            "{dest_city} economic overview",
        ],
        "extract_keys": ["household_income", "gdp_growth", "population", "gdp_origin"],
        "narrative_field": "economic_context",
    },
    "corporate_links": {
        "section": "S5A",
        "queries": [
            "{origin_country} companies headquarters {dest_city}",
            "{origin_country} tech companies {dest_city} offices",
            "{origin_country} companies Silicon Valley" if "{dest_city}" == "San Jose" else "{origin_country} companies {dest_city}",
            "foreign direct investment {origin_country} {dest_country}",
        ],
        "extract_keys": ["companies", "fdi_value"],
        "narrative_field": "corporate_links",
    },
    "tourism": {
        "section": "S5B",
        "queries": [
            "{origin_country} visitors to {dest_country} annual",
            "{dest_country} visitors to {origin_country} annual",
            "tourism {origin_country} {dest_country} visitor numbers growth",
            "{dest_country} visitor spending",
        ],
        "extract_keys": ["outbound_visitors", "inbound_visitors", "growth_rate", "spending"],
        "narrative_field": "tourism",
    },
    "trade": {
        "section": "S5C",
        "queries": [
            "bilateral trade {origin_country} {dest_country} volume",
            "{dest_city} metro exports {origin_country}",
            "trade relationship {origin_country} {dest_country}",
        ],
        "extract_keys": ["trade_volume", "metro_exports"],
        "narrative_field": "trade",
    },
    "diaspora": {
        "section": "S5E",
        "queries": [
            "{origin_country} population in {dest_city}",
            "{origin_country} diaspora {dest_country} census",
            "{origin_country} born residents {dest_city}",
        ],
        "extract_keys": ["diaspora_population", "community_description"],
        "narrative_field": "diaspora",
    },
    "airline_strategy": {
        "section": "S4",
        "queries": [
            "{airline} route network strategy {year}",
            "{airline} new routes {year}",
            "{airline} fleet expansion {year}",
        ],
        "extract_keys": ["strategy_news", "fleet_info"],
        "narrative_field": "airline_strategy",
    },
    "airport_overview": {
        "section": "S8",
        "queries": [
            "{dest} airport annual passengers",
            "{dest} airport development plans",
            "{dest} airport airlines destinations",
            "{dest_city} airport catchment population",
        ],
        "extract_keys": ["annual_pax", "catchment_pop", "intl_airlines", "growth_rate", "development"],
        "narrative_field": "airport_data",
    },
}


# ============================================================================
# QUERY BUILDER  generates search-ready queries from route config
# ============================================================================

def build_queries(cfg: dict) -> Dict[str, List[str]]:
    """Build search queries for each research block from route config."""
    year = str(datetime.now().year)
    subs = {
        "{origin}": cfg.get("origin", ""),
        "{dest}": cfg.get("destination", ""),
        "{origin_city}": cfg.get("origin_city", ""),
        "{dest_city}": cfg.get("dest_city", ""),
        "{origin_country}": cfg.get("origin_country", ""),
        "{dest_country}": cfg.get("dest_country", ""),
        "{airline}": cfg.get("airline_name", ""),
        "{year}": year,
    }

    # Determine which blocks to research based on demand driver
    driver = cfg.get("demand_driver", "Mixed")
    blocks_to_run = ["economic_context", "airport_overview"]

    if driver in ("Business", "Mixed"):
        blocks_to_run.extend(["corporate_links", "trade"])
    if driver in ("Leisure", "Mixed", "VFR-diaspora"):
        blocks_to_run.extend(["tourism"])
    if driver == "VFR-diaspora":
        blocks_to_run.extend(["diaspora"])

    # Always include airline strategy for airport pitches
    buyer = cfg.get("buyer_type", "airport_pitch")
    if buyer == "airport_pitch":
        blocks_to_run.append("airline_strategy")

    queries = {}
    for block_id in blocks_to_run:
        spec = BLOCK_SPECS.get(block_id, {})
        block_queries = []
        for q_template in spec.get("queries", []):
            q = q_template
            for k, v in subs.items():
                q = q.replace(k, v)
            block_queries.append(q)
        queries[block_id] = block_queries

    return queries


# ============================================================================
# STRUCTURED DATA EXTRACTOR  parses search results into structured data
# ============================================================================

def extract_structured_data(block_id: str, search_results: List[dict]) -> dict:
    """
    Extract structured data from web search results for a given block.

    search_results: list of dicts with keys 'query', 'snippets', 'urls'
    Returns dict of extracted values with citations.
    """
    findings = {"findings": [], "citations": [], "raw_text": ""}

    for result in search_results:
        snippets = result.get("snippets", [])
        urls = result.get("urls", [])
        query = result.get("query", "")

        for i, snippet in enumerate(snippets):
            if snippet and len(snippet) > 20:
                citation = {
                    "source": urls[i] if i < len(urls) else "",
                    "text": snippet[:500],
                    "query": query,
                }
                findings["citations"].append(citation)
                findings["raw_text"] += snippet + "\n"

    return findings


# ============================================================================
# RESEARCH RESULTS  NARRATIVE CONFIG
# ============================================================================

def research_to_config(cfg: dict, research_results: Dict[str, dict]) -> dict:
    """
    Convert structured research results into the config format
    expected by the narrative generator.
    """
    research = cfg.get("research", {})
    airport = cfg.get("airport_data", {})

    for block_id, data in research_results.items():
        findings = data.get("findings", [])
        citations = data.get("citations", [])
        raw = data.get("raw_text", "")

        if block_id == "economic_context":
            econ = research.get("economic_context", {})
            # Extract values from raw text using simple pattern matching
            for cite in citations:
                text = cite.get("text", "").lower()
                if "household income" in text or "median income" in text:
                    # Try to find dollar amount
                    import re
                    amounts = re.findall(r'\$[\d,]+(?:\.\d+)?', cite["text"])
                    if amounts:
                        econ["household_income"] = amounts[0]
                if "gdp" in text and ("growth" in text or "forecast" in text or "%"  in text):
                    pcts = re.findall(r'(\d+\.?\d*)%', cite["text"])
                    if pcts:
                        econ["gdp_growth"] = pcts[0] + "%"
                if "population" in text:
                    pops = re.findall(r'([\d,.]+)\s*(?:million|residents|people|population)', cite["text"])
                    if pops:
                        econ["population"] = pops[0]
            econ["citations"] = [c["source"] for c in citations if c.get("source")]
            research["economic_context"] = econ

        elif block_id == "corporate_links":
            # Extract company names from snippets
            companies = []
            for cite in citations:
                text = cite.get("text", "")
                # Companies are hard to auto-extract, store raw for narrative
                if text:
                    companies.append({"text": text, "source": cite.get("source", "")})
            research["corporate_links_raw"] = companies
            research.setdefault("corporate_links", [])

        elif block_id == "tourism":
            tourism = research.get("tourism", {})
            import re
            for cite in citations:
                text = cite.get("text", "")
                if "visitor" in text.lower() or "tourist" in text.lower():
                    # Try to extract visitor numbers
                    nums = re.findall(r'([\d,.]+)\s*(?:million|thousand|visitors|tourists)', text.lower())
                    if nums:
                        dest_country = cfg.get("dest_country", "").lower()
                        origin_country = cfg.get("origin_country", "").lower()
                        if origin_country in text.lower():
                            tourism["inbound_visitors"] = nums[0] + " million" if float(nums[0].replace(",", "")) < 100 else nums[0]
                        elif dest_country in text.lower():
                            tourism["outbound_visitors"] = nums[0] + " million" if float(nums[0].replace(",", "")) < 100 else nums[0]
                if "growth" in text.lower() and "%" in text:
                    pcts = re.findall(r'(\d+\.?\d*)%', text)
                    if pcts:
                        tourism["growth_rate"] = pcts[0] + "% annually"
            tourism["citations"] = [c["source"] for c in citations if c.get("source")]
            research["tourism"] = tourism

        elif block_id == "trade":
            trade_items = []
            for cite in citations:
                text = cite.get("text", "")
                if text and ("trade" in text.lower() or "export" in text.lower() or "billion" in text.lower()):
                    import re
                    amounts = re.findall(r'[\$][\d,.]+\s*(?:billion|million|bn|mn)?', text)
                    if amounts:
                        trade_items.append({
                            "metric": "Trade" if "trade" in text.lower() else "Exports",
                            "value": amounts[0],
                            "source": cite.get("source", ""),
                        })
            research["trade"] = trade_items if trade_items else research.get("trade", [])

        elif block_id == "diaspora":
            diaspora_text = ""
            for cite in citations:
                if cite.get("text"):
                    diaspora_text += cite["text"] + " "
            if diaspora_text.strip():
                research["diaspora"] = {
                    "text": diaspora_text.strip()[:500],
                    "citations": [c["source"] for c in citations if c.get("source")]
                }

        elif block_id == "airport_overview":
            import re
            for cite in citations:
                text = cite.get("text", "")
                if "passenger" in text.lower() and not airport.get("annual_pax"):
                    nums = re.findall(r'([\d,.]+)\s*(?:million|passengers)', text.lower())
                    if nums:
                        airport["annual_pax"] = nums[0] + " million"
                if "catchment" in text.lower() or "population" in text.lower():
                    pops = re.findall(r'([\d,.]+)\s*(?:million|residents|people)', text.lower())
                    if pops and not airport.get("catchment_pop"):
                        airport["catchment_pop"] = pops[0] + " million"
                if "growth" in text.lower() and "%" in text:
                    pcts = re.findall(r'(\d+\.?\d*)%', text)
                    if pcts and not airport.get("growth_rate"):
                        airport["growth_rate"] = pcts[0] + "%"
            airport["citations"] = [c["source"] for c in citations if c.get("source")]

        elif block_id == "airline_strategy":
            strategy_texts = []
            for cite in citations:
                if cite.get("text"):
                    strategy_texts.append(cite["text"][:300])
            research["airline_strategy"] = {
                "news": strategy_texts,
                "citations": [c["source"] for c in citations if c.get("source")]
            }

    cfg["research"] = research
    cfg["airport_data"] = airport
    return cfg


# ============================================================================
# WEB SEARCH EXECUTION  uses subprocess to call web search
# ============================================================================

def execute_web_searches(queries: Dict[str, List[str]],
                         max_results_per_query: int = 3) -> Dict[str, dict]:
    """
    Execute web searches for all research blocks.

    In a Streamlit/portal context, this would use st.session_state or
    an API. In standalone mode, it can use a search API.

    Returns dict of block_id -> {findings, citations, raw_text}
    """
    results = {}

    for block_id, block_queries in queries.items():
        block_results = []
        for query in block_queries:
            # In production, this would call a real search API
            # For now, structure the results format
            block_results.append({
                "query": query,
                "snippets": [],
                "urls": [],
            })
        results[block_id] = extract_structured_data(block_id, block_results)

    return results


# ============================================================================
# MANUAL RESEARCH POPULATOR  for analyst-driven research
# ============================================================================

def create_research_template(cfg: dict) -> dict:
    """
    Create a structured template with all queries pre-filled,
    ready for an analyst (or Claude) to populate with findings.
    """
    queries = build_queries(cfg)
    template = {
        "route": f"{cfg.get('origin', '')}-{cfg.get('destination', '')}",
        "airline": cfg.get("airline_name", ""),
        "generated": datetime.now().isoformat(),
        "blocks": {}
    }

    for block_id, block_queries in queries.items():
        spec = BLOCK_SPECS.get(block_id, {})
        template["blocks"][block_id] = {
            "section": spec.get("section", ""),
            "queries": block_queries,
            "status": "pending",
            "findings": [],
            "values": {k: "" for k in spec.get("extract_keys", [])},
            "sources": [],
        }

    return template


def populate_from_template(cfg: dict, completed_template: dict) -> dict:
    """
    Take a completed research template and merge findings into config.
    """
    research = cfg.get("research", {})
    airport = cfg.get("airport_data", {})

    for block_id, block_data in completed_template.get("blocks", {}).items():
        values = block_data.get("values", {})
        sources = block_data.get("sources", [])

        if block_id == "economic_context":
            research["economic_context"] = {
                "household_income": values.get("household_income", ""),
                "gdp_growth": values.get("gdp_growth", ""),
                "population": values.get("population", ""),
                "citations": sources,
            }
        elif block_id == "tourism":
            research["tourism"] = {
                "outbound_visitors": values.get("outbound_visitors", ""),
                "inbound_visitors": values.get("inbound_visitors", ""),
                "growth_rate": values.get("growth_rate", ""),
                "spending": values.get("spending", ""),
                "citations": sources,
            }
        elif block_id == "trade":
            research["trade"] = [
                {"metric": "Bilateral trade", "value": values.get("trade_volume", "")},
                {"metric": "Metro exports", "value": values.get("metro_exports", "")},
            ]
        elif block_id == "corporate_links":
            # Companies need structured format
            pass  # Handled separately
        elif block_id == "airport_overview":
            airport.update({
                "annual_pax": values.get("annual_pax", ""),
                "catchment_pop": values.get("catchment_pop", ""),
                "intl_airlines": values.get("intl_airlines", ""),
                "growth_rate": values.get("growth_rate", ""),
            })

    cfg["research"] = research
    cfg["airport_data"] = airport
    return cfg


# ============================================================================
# CLAUDE-POWERED RESEARCH  for use within Claude conversations
# ============================================================================

def generate_research_prompt(cfg: dict) -> str:
    """
    Generate a structured prompt that Claude can use to conduct
    web research and return structured findings.

    This is designed to be used in a Claude conversation where
    Claude has web_search access.
    """
    queries = build_queries(cfg)
    airline = cfg.get("airline_name", "the airline")
    origin_city = cfg.get("origin_city", "Origin")
    dest_city = cfg.get("dest_city", "Destination")
    origin_country = cfg.get("origin_country", "")
    dest_country = cfg.get("dest_country", "")

    prompt = f"""Please conduct web research for the {origin_city}{dest_city} route assessment for {airline}.

For each research block below, search for the specified queries, extract the key data points, and provide source citations.

Return your findings as a JSON object with this structure:
{{
  "economic_context": {{
    "household_income": "<value with currency>",
    "gdp_growth": "<percentage>",
    "population": "<value>",
    "summary": "<2-3 sentence summary>",
    "sources": ["<url1>", "<url2>"]
  }},
  "corporate_links": [
    {{"company": "<name>", "hq": "<city>", "subsidiary": "<name>", "location": "<city>"}},
    ...
  ],
  "tourism": {{
    "outbound_visitors": "<{origin_country} visitors to {dest_country}>",
    "inbound_visitors": "<{dest_country} visitors to {origin_country}>",
    "growth_rate": "<annual growth %>",
    "spending": "<visitor spending>",
    "sources": ["<url1>", "<url2>"]
  }},
  "trade": [
    {{"metric": "<name>", "value": "<value with currency>"}},
    ...
  ],
  "airport_data": {{
    "annual_pax": "<passengers with unit>",
    "catchment_pop": "<population with unit>",
    "intl_airlines": "<number>",
    "growth_rate": "<% growth>",
    "sources": ["<url1>"]
  }}
}}

RESEARCH QUERIES BY BLOCK:
"""
    for block_id, block_queries in queries.items():
        spec = BLOCK_SPECS.get(block_id, {})
        prompt += f"\n### {block_id} ({spec.get('section', '')})\n"
        for q in block_queries:
            prompt += f"  - {q}\n"

    prompt += """
CITATION RULES:
- Every factual claim must have a source URL
- Prefer government statistics, aviation industry sources, and reputable news
- Flag single-source claims
- Date-stamp all data
"""
    return prompt


# ============================================================================
# MAIN PIPELINE: AUTO RESEARCH AND NARRATE
# ============================================================================

def auto_research_and_narrate(cfg: dict,
                               research_data: dict = None,
                               web_search_fn=None) -> dict:
    """
    Main pipeline function for portal integration.

    1. If research_data provided, use it directly
    2. If web_search_fn provided, execute live research
    3. Otherwise, generate research prompt for Claude
    4. Feed research into narrative generator
    5. Return enriched config ready for PPTX generator

    Args:
        cfg: Route configuration dict
        research_data: Pre-existing research findings (from JSON upload)
        web_search_fn: Optional callable(query) -> list[snippets]

    Returns:
        Enriched config dict with narrative + research
    """
    # Step 1: Get or generate research data
    if research_data:
        cfg["research"] = research_data
    elif web_search_fn:
        # Execute live web searches
        queries = build_queries(cfg)
        all_results = {}
        for block_id, block_queries in queries.items():
            block_results = []
            for query in block_queries:
                try:
                    snippets = web_search_fn(query)
                    block_results.append({
                        "query": query,
                        "snippets": snippets if isinstance(snippets, list) else [str(snippets)],
                        "urls": [],
                    })
                except Exception as e:
                    block_results.append({
                        "query": query,
                        "snippets": [f"Search error: {e}"],
                        "urls": [],
                    })
            all_results[block_id] = extract_structured_data(block_id, block_results)

        cfg = research_to_config(cfg, all_results)

    # Step 2: Run narrative generator
    if HAS_MODULES:
        cfg = generate_narrative(cfg)

    return cfg


def generate_research_json_template(cfg: dict, output_path: str = None) -> str:
    """
    Generate a JSON template file that can be filled in by an analyst
    or by Claude in a conversation, then uploaded to the portal.
    """
    template = create_research_template(cfg)

    if output_path:
        with open(output_path, "w") as f:
            json.dump(template, f, indent=2)
        return output_path
    else:
        return json.dumps(template, indent=2)


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python research_to_presentation.py --config config.json")
        print("  python research_to_presentation.py --config config.json --template")
        print("  python research_to_presentation.py --config config.json --prompt")
        sys.exit(1)

    with open(sys.argv[1].replace("--config", "").strip() if "--config" not in sys.argv else sys.argv[sys.argv.index("--config") + 1]) as f:
        config = json.load(f)

    if "--template" in sys.argv:
        out = config.get("origin", "XXX") + "_" + config.get("destination", "YYY") + "_research_template.json"
        generate_research_json_template(config, out)
        print(f"Research template: {out}")
    elif "--prompt" in sys.argv:
        prompt = generate_research_prompt(config)
        print(prompt)
    else:
        result = auto_research_and_narrate(config)
        out = sys.argv[sys.argv.index("--config") + 1].replace(".json", "_enriched.json")
        with open(out, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"Enriched config: {out}")
