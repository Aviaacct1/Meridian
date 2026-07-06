#!/usr/bin/env python3
"""
Avia Solutions  Market Research Module (Chat 38/39)
=====================================================
Generates structured web research queries and organises outputs
for city pair route assessment presentations.

Maps directly to the 8 research blocks from the City Pair Presentation
Template (Sections 5A5H):
    Block 1: Corporate / Technology Links (5A)
    Block 2: Tourism / Visitor Data (5B)
    Block 3: Trade and Investment (5C)
    Block 4: Education / Student Links (5D)
    Block 5: Diaspora / VFR Population (5E)
    Block 6: Passenger Profile (5F)
    Block 7: Non-Cannibalization Evidence (5G)
    Block 8: Case Study / Comparable Route (5H)
    Block 9: Airport Overview (Section 8)
    Block 10: Economic Context (background for Section 4)

Each block has:
    - Relevance classification: ESSENTIAL / INCLUDE / OPTIONAL per route type
    - Auto-generated search queries tuned to the specific city pair
    - Output schema for structured data capture
    - Source priority (which sources to prefer)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class DemandProfile(Enum):
    BUSINESS = "business"
    LEISURE = "leisure"
    VFR_DIASPORA = "vfr_diaspora"
    MIXED = "mixed"

class RouteType(Enum):
    HUB_LONGHAUL = "hub_longhaul"
    LCC_P2P = "lcc_p2p"
    CHARTER_LEISURE = "charter_leisure"
    SIXTH_FREEDOM = "sixth_freedom"

class BuyerType(Enum):
    AIRPORT = "airport"
    AIRLINE = "airline"
    FUND = "fund"

class Relevance(Enum):
    ESSENTIAL = "essential"
    INCLUDE = "include"
    OPTIONAL = "optional"
    SKIP = "skip"


@dataclass
class ResearchQuery:
    """A single search query with metadata."""
    query: str
    block: str
    priority: int  # 1=highest
    preferred_sources: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class ResearchBlock:
    """A research block with relevance classification and queries."""
    block_id: str
    name: str
    section_ref: str  # e.g., "5A"
    relevance: Relevance
    queries: List[ResearchQuery] = field(default_factory=list)
    output_schema: Dict = field(default_factory=dict)
    rationale: str = ""


@dataclass
class RouteResearchConfig:
    """Complete research configuration for a city pair."""
    origin: str  # IATA code
    destination: str  # IATA code
    origin_city: str
    destination_city: str
    origin_country: str
    destination_country: str
    airline: str
    demand_profile: DemandProfile
    route_type: RouteType
    buyer_type: BuyerType
    hub_airport: str = ""
    origin_region: str = ""  # e.g., "Silicon Valley", "Greater Bay Area"
    destination_region: str = ""


# ============================================================================
# RELEVANCE MATRIX
# ============================================================================

def get_relevance_matrix(
    demand_profile: DemandProfile,
    route_type: RouteType,
    buyer_type: BuyerType
) -> Dict[str, Relevance]:
    """
    Determines which research blocks are essential, included, or optional
    based on route characteristics.

    This encodes expert judgment about what matters for different route types.
    """

    # Start with defaults
    matrix = {
        "corporate_links": Relevance.OPTIONAL,
        "tourism":         Relevance.OPTIONAL,
        "trade":           Relevance.OPTIONAL,
        "education":       Relevance.OPTIONAL,
        "diaspora":        Relevance.OPTIONAL,
        "passenger_profile": Relevance.INCLUDE,
        "non_cannibalization": Relevance.OPTIONAL,
        "case_study":      Relevance.INCLUDE,
        "airport_overview": Relevance.INCLUDE,
        "economic_context": Relevance.INCLUDE,
    }

    # Demand profile adjustments
    if demand_profile == DemandProfile.BUSINESS:
        matrix["corporate_links"] = Relevance.ESSENTIAL
        matrix["trade"] = Relevance.ESSENTIAL
        matrix["education"] = Relevance.INCLUDE
        matrix["tourism"] = Relevance.INCLUDE
    elif demand_profile == DemandProfile.LEISURE:
        matrix["tourism"] = Relevance.ESSENTIAL
        matrix["corporate_links"] = Relevance.OPTIONAL
        matrix["trade"] = Relevance.OPTIONAL
    elif demand_profile == DemandProfile.VFR_DIASPORA:
        matrix["diaspora"] = Relevance.ESSENTIAL
        matrix["tourism"] = Relevance.INCLUDE
        matrix["corporate_links"] = Relevance.OPTIONAL
    elif demand_profile == DemandProfile.MIXED:
        matrix["corporate_links"] = Relevance.ESSENTIAL
        matrix["tourism"] = Relevance.ESSENTIAL
        matrix["trade"] = Relevance.INCLUDE
        matrix["diaspora"] = Relevance.INCLUDE

    # Route type adjustments
    if route_type == RouteType.HUB_LONGHAUL:
        matrix["economic_context"] = Relevance.ESSENTIAL
        if demand_profile in (DemandProfile.BUSINESS, DemandProfile.MIXED):
            matrix["corporate_links"] = Relevance.ESSENTIAL
    elif route_type == RouteType.LCC_P2P:
        matrix["tourism"] = Relevance.ESSENTIAL
        matrix["corporate_links"] = Relevance.OPTIONAL
        matrix["trade"] = Relevance.OPTIONAL
    elif route_type == RouteType.SIXTH_FREEDOM:
        matrix["economic_context"] = Relevance.ESSENTIAL
        matrix["diaspora"] = Relevance.INCLUDE

    # Buyer type adjustments
    if buyer_type == BuyerType.AIRPORT:
        matrix["airport_overview"] = Relevance.ESSENTIAL
        matrix["non_cannibalization"] = Relevance.INCLUDE
    elif buyer_type == BuyerType.FUND:
        matrix["economic_context"] = Relevance.ESSENTIAL
        matrix["passenger_profile"] = Relevance.ESSENTIAL

    return matrix


# ============================================================================
# QUERY GENERATOR
# ============================================================================

def generate_queries(config: RouteResearchConfig) -> List[ResearchBlock]:
    """
    Generate all research blocks with relevance classification and
    targeted search queries for the given route.
    """

    matrix = get_relevance_matrix(
        config.demand_profile, config.route_type, config.buyer_type
    )

    blocks = []

    # ---- BLOCK 1: Corporate / Technology Links (5A) ----
    b1_queries = []
    if matrix["corporate_links"] != Relevance.SKIP:
        # Origin  Destination corporate links
        b1_queries.append(ResearchQuery(
            query=f"{config.origin_country} companies offices {config.destination_city}",
            block="corporate_links", priority=1,
            preferred_sources=["Chamber of Commerce", "government trade body", "SEC filings"],
            notes="Major companies from origin with presence at destination"
        ))
        # Destination  Origin corporate links
        b1_queries.append(ResearchQuery(
            query=f"{config.destination_country} companies {config.origin_city} {config.origin_region or ''}".strip(),
            block="corporate_links", priority=1,
            preferred_sources=["Company websites", "business directories"],
            notes="Major companies from destination with presence at origin"
        ))
        # Tech-specific (if business demand)
        if config.demand_profile in (DemandProfile.BUSINESS, DemandProfile.MIXED):
            if config.origin_region:
                b1_queries.append(ResearchQuery(
                    query=f"{config.origin_region} technology companies {config.destination_country} operations",
                    block="corporate_links", priority=2,
                    preferred_sources=["TechCrunch", "Crunchbase", "company press releases"],
                    notes="Tech sector cross-border presence"
                ))
            if config.destination_region:
                b1_queries.append(ResearchQuery(
                    query=f"{config.destination_region} companies {config.origin_country} investment",
                    block="corporate_links", priority=2,
                    preferred_sources=["Financial press", "government investment bodies"],
                    notes="Destination region companies investing in origin country"
                ))

    blocks.append(ResearchBlock(
        block_id="corporate_links",
        name="Corporate / Technology Links",
        section_ref="5A",
        relevance=matrix["corporate_links"],
        queries=b1_queries,
        output_schema={
            "companies": [{"name": "", "hq_country": "", "subsidiary_city": "", "employees": "", "sector": ""}],
            "total_companies_origin_to_dest": 0,
            "total_companies_dest_to_origin": 0,
            "key_sectors": [],
        },
        rationale="Corporate presence drives business travel demand"
    ))

    # ---- BLOCK 2: Tourism / Visitor Data (5B) ----
    b2_queries = []
    if matrix["tourism"] != Relevance.SKIP:
        b2_queries.append(ResearchQuery(
            query=f"{config.origin_country} visitors {config.destination_country} tourism statistics 2024",
            block="tourism", priority=1,
            preferred_sources=["UNWTO", "national tourism board", "government statistics"],
            notes="Outbound visitors from origin to destination country"
        ))
        b2_queries.append(ResearchQuery(
            query=f"{config.destination_country} visitors {config.origin_country} tourism arrivals 2024",
            block="tourism", priority=1,
            preferred_sources=["UNWTO", "national tourism board"],
            notes="Outbound visitors from destination to origin country"
        ))
        b2_queries.append(ResearchQuery(
            query=f"{config.destination_city} tourism visitor spending trends",
            block="tourism", priority=2,
            preferred_sources=["Tourism board annual report", "Mastercard destination index"],
            notes="Destination tourism metrics and trends"
        ))

    blocks.append(ResearchBlock(
        block_id="tourism",
        name="Tourism / Visitor Data",
        section_ref="5B",
        relevance=matrix["tourism"],
        queries=b2_queries,
        output_schema={
            "origin_to_dest_visitors": {"annual": 0, "year": "", "growth_rate": "", "source": ""},
            "dest_to_origin_visitors": {"annual": 0, "year": "", "growth_rate": "", "source": ""},
            "visitor_spending": {"total": "", "per_visitor": "", "source": ""},
            "purpose_breakdown": {"business": "", "leisure": "", "vfr": "", "source": ""},
        }
    ))

    # ---- BLOCK 3: Trade and Investment (5C) ----
    b3_queries = []
    if matrix["trade"] != Relevance.SKIP:
        b3_queries.append(ResearchQuery(
            query=f"{config.origin_country} {config.destination_country} bilateral trade volume 2024",
            block="trade", priority=1,
            preferred_sources=["Dept of Commerce", "national statistics office", "World Bank"],
            notes="Bilateral trade data"
        ))
        # Metro-level if available
        b3_queries.append(ResearchQuery(
            query=f"{config.origin_city} metro exports {config.destination_country}",
            block="trade", priority=2,
            preferred_sources=["Bureau of Economic Analysis", "metro trade statistics"],
            notes="Metro-level trade data for the origin city"
        ))
        b3_queries.append(ResearchQuery(
            query=f"{config.destination_country} foreign direct investment {config.origin_country} 2024",
            block="trade", priority=2,
            preferred_sources=["UNCTAD", "national investment body"],
            notes="FDI flows between countries"
        ))

    blocks.append(ResearchBlock(
        block_id="trade",
        name="Trade and Investment",
        section_ref="5C",
        relevance=matrix["trade"],
        queries=b3_queries,
        output_schema={
            "bilateral_trade": {"total": "", "exports": "", "imports": "", "year": "", "source": ""},
            "metro_exports": {"total": "", "metro": "", "year": "", "source": ""},
            "fdi": {"origin_to_dest": "", "dest_to_origin": "", "year": "", "source": ""},
        }
    ))

    # ---- BLOCK 4: Education / Student Links (5D) ----
    b4_queries = []
    if matrix["education"] != Relevance.SKIP:
        b4_queries.append(ResearchQuery(
            query=f"{config.destination_country} students studying {config.origin_country} university enrollment",
            block="education", priority=2,
            preferred_sources=["IIE Open Doors", "education ministry", "HESA"],
            notes="Student flows between countries"
        ))
        b4_queries.append(ResearchQuery(
            query=f"{config.origin_city} university partnerships {config.destination_country}",
            block="education", priority=3,
            preferred_sources=["University websites", "education press"],
            notes="Institutional links"
        ))

    blocks.append(ResearchBlock(
        block_id="education",
        name="Education / Student Links",
        section_ref="5D",
        relevance=matrix["education"],
        queries=b4_queries,
        output_schema={
            "students_dest_in_origin": {"count": 0, "year": "", "source": ""},
            "students_origin_in_dest": {"count": 0, "year": "", "source": ""},
            "key_universities": [],
        }
    ))

    # ---- BLOCK 5: Diaspora / VFR Population (5E) ----
    b5_queries = []
    if matrix["diaspora"] != Relevance.SKIP:
        b5_queries.append(ResearchQuery(
            query=f"{config.destination_country} born population {config.origin_city} metro area census",
            block="diaspora", priority=1 if matrix["diaspora"] == Relevance.ESSENTIAL else 2,
            preferred_sources=["Census bureau", "ACS", "national statistics"],
            notes="Diaspora population at origin"
        ))
        b5_queries.append(ResearchQuery(
            query=f"{config.origin_country} born population {config.destination_city} census expatriate",
            block="diaspora", priority=2,
            preferred_sources=["Census", "immigration statistics"],
            notes="Diaspora population at destination"
        ))

    blocks.append(ResearchBlock(
        block_id="diaspora",
        name="Diaspora / VFR Population",
        section_ref="5E",
        relevance=matrix["diaspora"],
        queries=b5_queries,
        output_schema={
            "dest_born_at_origin": {"count": 0, "metro_area": "", "year": "", "source": ""},
            "origin_born_at_dest": {"count": 0, "metro_area": "", "year": "", "source": ""},
        }
    ))

    # ---- BLOCK 6: Passenger Profile (5F) ----
    b6_queries = []
    if matrix["passenger_profile"] != Relevance.SKIP:
        b6_queries.append(ResearchQuery(
            query=f"{config.origin_city} {config.destination_city} air passenger demographics purpose of travel",
            block="passenger_profile", priority=2,
            preferred_sources=["CAA survey", "DOT", "Sabre MI (internal)"],
            notes="Passenger characteristics on this route or corridor"
        ))

    blocks.append(ResearchBlock(
        block_id="passenger_profile",
        name="Passenger Profile",
        section_ref="5F",
        relevance=matrix["passenger_profile"],
        queries=b6_queries,
        output_schema={
            "purpose_split": {"business": "", "leisure": "", "vfr": "", "source": ""},
            "cabin_split": {"premium": "", "economy": "", "source": ""},
        }
    ))

    # ---- BLOCK 7: Non-Cannibalization Evidence (5G) ----
    b7_queries = []
    if matrix["non_cannibalization"] != Relevance.SKIP:
        b7_queries.append(ResearchQuery(
            query=f"{config.airline} new route launch market stimulation evidence",
            block="non_cannibalization", priority=3,
            preferred_sources=["CAPA", "Aviation Week", "airline investor presentations"],
            notes="Evidence that new service grows market"
        ))
        # If competing nearby airport exists
        if config.origin in ("SJC",):
            b7_queries.append(ResearchQuery(
                query="ANA San Jose SFO market stimulation DOT T-100",
                block="non_cannibalization", priority=2,
                preferred_sources=["DOT T-100", "Sabre MI (internal)"],
                notes="SJC-specific: ANA SJC launched without cannibalising SFO"
            ))
        if config.origin in ("STN", "LTN", "LGW"):
            b7_queries.append(ResearchQuery(
                query=f"{config.origin} London market stimulation separate catchment",
                block="non_cannibalization", priority=2,
                notes="London secondary airport  prove separate catchment"
            ))

    blocks.append(ResearchBlock(
        block_id="non_cannibalization",
        name="Non-Cannibalization Evidence",
        section_ref="5G",
        relevance=matrix["non_cannibalization"],
        queries=b7_queries,
        output_schema={
            "case_studies": [{"route": "", "result": "", "year": "", "source": ""}],
            "market_growth_evidence": "",
        }
    ))

    # ---- BLOCK 8: Case Study / Comparable Route (5H) ----
    b8_queries = []
    if matrix["case_study"] != Relevance.SKIP:
        b8_queries.append(ResearchQuery(
            query=f"{config.airline} new long haul route launch success performance",
            block="case_study", priority=2,
            preferred_sources=["CAPA", "FlightGlobal", "airline press releases"],
            notes="Comparable recent route launch by the target airline"
        ))
        b8_queries.append(ResearchQuery(
            query=f"new airline route {config.destination_city} launch performance load factor",
            block="case_study", priority=3,
            preferred_sources=["Aviation Week", "airline results"],
            notes="Other carriers' experience at the destination"
        ))

    blocks.append(ResearchBlock(
        block_id="case_study",
        name="Case Study / Comparable Route",
        section_ref="5H",
        relevance=matrix["case_study"],
        queries=b8_queries,
        output_schema={
            "comparable_route": {"carrier": "", "route": "", "launch_year": "", "performance": "", "source": ""},
        }
    ))

    # ---- BLOCK 9: Airport Overview (Section 8) ----
    b9_queries = []
    if matrix["airport_overview"] != Relevance.SKIP:
        b9_queries.append(ResearchQuery(
            query=f"{config.origin} airport passenger statistics growth 2024",
            block="airport_overview", priority=1 if config.buyer_type == BuyerType.AIRPORT else 3,
            preferred_sources=["Airport authority", "ACI", "FAA"],
            notes="Origin airport traffic data"
        ))
        b9_queries.append(ResearchQuery(
            query=f"{config.origin} airport development expansion plans",
            block="airport_overview", priority=2,
            preferred_sources=["Airport master plan", "planning documents"],
            notes="Airport development context"
        ))

    blocks.append(ResearchBlock(
        block_id="airport_overview",
        name="Airport Overview",
        section_ref="S8",
        relevance=matrix["airport_overview"],
        queries=b9_queries,
        output_schema={
            "annual_passengers": {"count": 0, "year": "", "growth": "", "source": ""},
            "international_passengers": {"count": 0, "year": "", "source": ""},
            "development_plans": "",
        }
    ))

    # ---- BLOCK 10: Economic Context (Section 4 background) ----
    b10_queries = []
    if matrix["economic_context"] != Relevance.SKIP:
        b10_queries.append(ResearchQuery(
            query=f"{config.origin_city} GDP economy household income 2024",
            block="economic_context", priority=1,
            preferred_sources=["Census", "BEA", "national statistics"],
            notes="Origin economic indicators"
        ))
        b10_queries.append(ResearchQuery(
            query=f"{config.destination_city} economy GDP growth outlook 2025",
            block="economic_context", priority=1,
            preferred_sources=["IMF", "World Bank", "national statistics"],
            notes="Destination economic outlook"
        ))
        b10_queries.append(ResearchQuery(
            query=f"{config.origin_country} {config.destination_country} air service agreement bilateral",
            block="economic_context", priority=3,
            preferred_sources=["ICAO", "government aviation authority"],
            notes="Regulatory context  bilateral agreements"
        ))

    blocks.append(ResearchBlock(
        block_id="economic_context",
        name="Economic Context",
        section_ref="S4",
        relevance=matrix["economic_context"],
        queries=b10_queries,
        output_schema={
            "origin_gdp": {"value": "", "growth": "", "source": ""},
            "dest_gdp": {"value": "", "growth": "", "source": ""},
            "household_income": {"origin": "", "dest": "", "source": ""},
            "bilateral_agreement": "",
        }
    ))

    return blocks


# ============================================================================
# SUMMARY AND REPORTING
# ============================================================================

def summarise_research_plan(config: RouteResearchConfig, blocks: List[ResearchBlock]) -> str:
    """Produce a human-readable summary of the research plan."""

    lines = []
    lines.append("=" * 70)
    lines.append(f"MARKET RESEARCH PLAN: {config.origin}-{config.destination}")
    lines.append(f"Airline: {config.airline}")
    lines.append(f"Route Type: {config.route_type.value}")
    lines.append(f"Demand Profile: {config.demand_profile.value}")
    lines.append(f"Buyer Type: {config.buyer_type.value}")
    lines.append("=" * 70)

    total_queries = 0
    essential_count = 0
    include_count = 0
    optional_count = 0

    for block in blocks:
        rel = block.relevance
        if rel == Relevance.ESSENTIAL:
            essential_count += 1
        elif rel == Relevance.INCLUDE:
            include_count += 1
        elif rel == Relevance.OPTIONAL:
            optional_count += 1

        marker = {
            Relevance.ESSENTIAL: " ESSENTIAL",
            Relevance.INCLUDE: " INCLUDE",
            Relevance.OPTIONAL: " OPTIONAL",
            Relevance.SKIP: " SKIP",
        }[rel]

        lines.append(f"\n{marker}  Block: {block.name} ({block.section_ref})")
        if block.rationale:
            lines.append(f"  Rationale: {block.rationale}")

        for i, q in enumerate(block.queries, 1):
            total_queries += 1
            prio = "HIGH" if q.priority == 1 else "MED" if q.priority == 2 else "LOW"
            lines.append(f"  Query {i} [{prio}]: \"{q.query}\"")
            if q.preferred_sources:
                lines.append(f"    Sources: {', '.join(q.preferred_sources)}")
            if q.notes:
                lines.append(f"    Notes: {q.notes}")

    lines.append(f"\n{'=' * 70}")
    lines.append(f"SUMMARY: {total_queries} queries across {len(blocks)} blocks")
    lines.append(f"  Essential: {essential_count} | Include: {include_count} | Optional: {optional_count}")
    lines.append(f"{'=' * 70}")

    return "\n".join(lines)


# ============================================================================
# TEST: BA LHR-SJC (original validation)
# ============================================================================

def test_ba_lhr_sjc():
    """Test against the original BA LHR-SJC case."""

    config = RouteResearchConfig(
        origin="SJC",
        destination="LHR",
        origin_city="San Jose",
        destination_city="London",
        origin_country="United States",
        destination_country="United Kingdom",
        airline="British Airways",
        demand_profile=DemandProfile.MIXED,
        route_type=RouteType.HUB_LONGHAUL,
        buyer_type=BuyerType.AIRPORT,
        hub_airport="LHR",
        origin_region="Silicon Valley",
        destination_region="",
    )

    blocks = generate_queries(config)
    summary = summarise_research_plan(config, blocks)
    print(summary)

    # Validate expectations
    relevances = {b.block_id: b.relevance for b in blocks}
    total_queries = sum(len(b.queries) for b in blocks)

    assert relevances["corporate_links"] == Relevance.ESSENTIAL, "Corporate should be ESSENTIAL for mixed business"
    assert relevances["tourism"] == Relevance.ESSENTIAL, "Tourism should be ESSENTIAL for mixed demand"
    assert relevances["airport_overview"] == Relevance.ESSENTIAL, "Airport should be ESSENTIAL for airport buyer"
    assert relevances["economic_context"] == Relevance.ESSENTIAL, "Economic should be ESSENTIAL for hub longhaul"
    assert total_queries >= 15, f"Expected 15+ queries, got {total_queries}"

    print(f"\n BA LHR-SJC: {total_queries} queries, relevances correct")
    return config, blocks


# ============================================================================
# TEST: CATHAY PACIFIC HKG-SJC (cross-route validation)
# ============================================================================

def test_cx_hkg_sjc():
    """
    Test against Cathay Pacific HKG-SJC  fundamentally different from BA:
    - Asian mega-hub vs European hub
    - Different diaspora dynamics (large Chinese/Asian-American population in Bay Area)
    - Greater Bay Area integration (SkyPier ferry, Shenzhen, Guangzhou)
    - Different competitive landscape (no Star Alliance at SJC for Asia routes)
    """

    config = RouteResearchConfig(
        origin="SJC",
        destination="HKG",
        origin_city="San Jose",
        destination_city="Hong Kong",
        origin_country="United States",
        destination_country="Hong Kong",
        airline="Cathay Pacific",
        demand_profile=DemandProfile.MIXED,
        route_type=RouteType.HUB_LONGHAUL,
        buyer_type=BuyerType.AIRPORT,
        hub_airport="HKG",
        origin_region="Silicon Valley",
        destination_region="Greater Bay Area",
    )

    blocks = generate_queries(config)
    summary = summarise_research_plan(config, blocks)
    print(summary)

    # Validate expectations
    relevances = {b.block_id: b.relevance for b in blocks}
    total_queries = sum(len(b.queries) for b in blocks)

    # Same demand profile as BA so relevances should match
    assert relevances["corporate_links"] == Relevance.ESSENTIAL
    assert relevances["tourism"] == Relevance.ESSENTIAL
    assert relevances["diaspora"] == Relevance.INCLUDE  # Mixed demand = INCLUDE
    assert relevances["airport_overview"] == Relevance.ESSENTIAL  # Airport buyer

    # But queries should be HKG-specific
    all_query_texts = [q.query for b in blocks for q in b.queries]
    assert any("Hong Kong" in q for q in all_query_texts), "Should have HKG queries"
    assert any("Greater Bay Area" in q for q in all_query_texts), "Should have GBA queries"
    assert any("Silicon Valley" in q for q in all_query_texts), "Should have SV queries"

    print(f"\n CX HKG-SJC: {total_queries} queries, relevances correct, HKG-specific queries present")
    return config, blocks


# ============================================================================
# TEST: KLM AMS-TPA (leisure-oriented hub route)
# ============================================================================

def test_klm_ams_tpa():
    """
    Test against KLM AMS-TPA  leisure-dominant market:
    - Leisure/tourism demand driver (Florida theme parks, beaches)
    - European hub to US leisure destination
    - Different diaspora profile (Dutch community in Florida)
    - Seasonal demand pattern
    """

    config = RouteResearchConfig(
        origin="TPA",
        destination="AMS",
        origin_city="Tampa",
        destination_city="Amsterdam",
        origin_country="United States",
        destination_country="Netherlands",
        airline="KLM",
        demand_profile=DemandProfile.LEISURE,
        route_type=RouteType.HUB_LONGHAUL,
        buyer_type=BuyerType.AIRPORT,
        hub_airport="AMS",
        origin_region="Tampa Bay",
        destination_region="",
    )

    blocks = generate_queries(config)
    summary = summarise_research_plan(config, blocks)
    print(summary)

    # Validate leisure-specific relevances
    relevances = {b.block_id: b.relevance for b in blocks}
    total_queries = sum(len(b.queries) for b in blocks)

    assert relevances["tourism"] == Relevance.ESSENTIAL, "Tourism ESSENTIAL for leisure"
    assert relevances["corporate_links"] == Relevance.OPTIONAL, "Corporate OPTIONAL for leisure"
    assert relevances["trade"] == Relevance.OPTIONAL, "Trade OPTIONAL for leisure"
    assert relevances["economic_context"] == Relevance.ESSENTIAL, "Economic ESSENTIAL for hub longhaul"

    # Leisure queries should mention tourism-relevant terms
    all_query_texts = [q.query for b in blocks for q in b.queries]
    assert any("Tampa" in q for q in all_query_texts), "Should have Tampa queries"
    assert any("Netherlands" in q or "Amsterdam" in q for q in all_query_texts), "Should have NL queries"

    print(f"\n KLM AMS-TPA: {total_queries} queries, leisure relevances correct")
    return config, blocks


# ============================================================================
# TEST: ICELANDAIR KEF-SJC (LCC/hybrid leisure route)
# ============================================================================

def test_fi_kef_sjc():
    """
    Test against Icelandair KEF-SJC  leisure/hybrid:
    - Seasonal route
    - Iceland as stopover destination
    - Smaller carrier, lower frequency
    """

    config = RouteResearchConfig(
        origin="SJC",
        destination="KEF",
        origin_city="San Jose",
        destination_city="Reykjavik",
        origin_country="United States",
        destination_country="Iceland",
        airline="Icelandair",
        demand_profile=DemandProfile.LEISURE,
        route_type=RouteType.HUB_LONGHAUL,  # Icelandair uses KEF as connecting hub
        buyer_type=BuyerType.AIRPORT,
        hub_airport="KEF",
        origin_region="Silicon Valley",
        destination_region="",
    )

    blocks = generate_queries(config)
    summary = summarise_research_plan(config, blocks)
    print(summary)

    relevances = {b.block_id: b.relevance for b in blocks}
    total_queries = sum(len(b.queries) for b in blocks)

    assert relevances["tourism"] == Relevance.ESSENTIAL
    assert relevances["corporate_links"] == Relevance.OPTIONAL

    all_query_texts = [q.query for b in blocks for q in b.queries]
    assert any("Iceland" in q for q in all_query_texts)
    assert any("Reykjavik" in q or "KEF" in q for q in all_query_texts)

    print(f"\n FI KEF-SJC: {total_queries} queries, leisure/hub relevances correct")
    return config, blocks


# ============================================================================
# COMPARISON ANALYSIS
# ============================================================================

def compare_all_routes():
    """Run all test cases and compare the output patterns."""

    print("\n" + "=" * 70)
    print("CROSS-ROUTE COMPARISON")
    print("=" * 70)

    tests = [
        ("BA LHR-SJC", test_ba_lhr_sjc),
        ("CX HKG-SJC", test_cx_hkg_sjc),
        ("KLM AMS-TPA", test_klm_ams_tpa),
        ("FI KEF-SJC", test_fi_kef_sjc),
    ]

    results = []
    for name, fn in tests:
        print(f"\n{'=' * 70}")
        print(f"TESTING: {name}")
        print(f"{'=' * 70}")
        config, blocks = fn()
        total_q = sum(len(b.queries) for b in blocks)
        essential = sum(1 for b in blocks if b.relevance == Relevance.ESSENTIAL)
        include = sum(1 for b in blocks if b.relevance == Relevance.INCLUDE)
        optional = sum(1 for b in blocks if b.relevance == Relevance.OPTIONAL)
        results.append((name, total_q, essential, include, optional))

    print("\n" + "=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print(f"{'Route':<20} {'Queries':>8} {'Essential':>10} {'Include':>8} {'Optional':>9}")
    print("-" * 55)
    for name, tq, ess, inc, opt in results:
        print(f"{name:<20} {tq:>8} {ess:>10} {inc:>8} {opt:>9}")

    print("\n All cross-route tests passed")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    compare_all_routes()
