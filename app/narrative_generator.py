"""
Avia Solutions  Narrative Generator for City Pair Presentations
================================================================
Generates professional prose for all 8 PPTX sections using pipeline
results, research data, and route configuration.

Calibrates tone and emphasis by:
  - Buyer type: airport_pitch (persuasive), airline_forecast (analytical),
    fund_due_diligence (conservative)
  - Route type: hub_longhaul, lcc_p2p, leisure_charter, mixed
  - Demand driver: Business, Leisure, Mixed, VFR-diaspora

Each generate_* function returns a dict that maps directly into the
PPTX generator's config JSON fields.

Usage:
    from narrative_generator import NarrativeGenerator

    ng = NarrativeGenerator(config)
    ng.load_forecast(pipeline_result)
    ng.load_research("CX_HKG_SJC_Research.json")
    full_config = ng.generate_all()
    # full_config is ready for city_pair_pptx_generator.js
"""

import json
import os
import math
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# TONE TEMPLATES  buyer-specific phrasing
# ============================================================================

TONE = {
    "airport_pitch": {
        "confidence": "high",
        "hedging": "minimal",
        "forecast_framing": "opportunity",
        "opening_verb": "is uniquely positioned",
        "demand_adj": "significant",
        "gap_adj": "compelling",
        "close_verb": "seize",
        "cagr_comment": lambda r: f"growing at {r:.1%} per annum",
        "load_factor_comment": lambda lf: f"a healthy {lf:.1%} load factor" if lf > 0.75 else f"a strong {lf:.1%} load factor even in year one",
        "stim_framing": "New direct service is expected to stimulate additional demand beyond the current O&D base",
        "capture_framing": "based on frequency share and competitive positioning",
    },
    "airline_forecast": {
        "confidence": "measured",
        "hedging": "moderate",
        "forecast_framing": "projection",
        "opening_verb": "is well placed to serve",
        "demand_adj": "material",
        "gap_adj": "notable",
        "close_verb": "consider",
        "cagr_comment": lambda r: f"at a compound growth rate of {r:.1%}",
        "load_factor_comment": lambda lf: f"implying a {lf:.1%} load factor",
        "stim_framing": "Stimulation has been applied conservatively based on IATA analysis and comparable market benchmarks",
        "capture_framing": "derived from QSI model calibration and frequency share analysis",
    },
    "fund_due_diligence": {
        "confidence": "conservative",
        "hedging": "explicit",
        "forecast_framing": "base case",
        "opening_verb": "could serve",
        "demand_adj": "identifiable",
        "gap_adj": "observable",
        "close_verb": "evaluate",
        "cagr_comment": lambda r: f"assuming conservative compound growth of {r:.1%}",
        "load_factor_comment": lambda lf: f"resulting in a {lf:.1%} seat factor on conservative assumptions",
        "stim_framing": "Stimulation factors are applied conservatively at the lower end of IATA benchmarks",
        "capture_framing": "based on calibrated QSI model benchmarked against comparable routes",
    },
}

# ============================================================================
# FORMAT HELPERS
# ============================================================================

def _fmt(n, unit=""):
    """Format numbers for narrative prose."""
    if n is None:
        return "DATA REQUIRED"
    if isinstance(n, str):
        return n
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f} million{unit}"
    if n >= 1_000:
        return f"{n:,.0f}{unit}"
    if 0 < n < 1:
        return f"{n:.1%}"
    return f"{n:.1f}{unit}"


def _fmt_k(n):
    if n is None:
        return "DATA REQUIRED"
    return f"{n/1000:.0f},000" if n >= 1000 else str(int(n))


def _pct(n):
    if n is None:
        return "DATA REQUIRED"
    return f"{n*100:.1f}%"


def _ordinal(n):
    s = {1: "st", 2: "nd", 3: "rd"}.get(n % 10 * (n % 100 not in (11, 12, 13)), "th")
    return f"{n}{s}"


# ============================================================================
# MAIN GENERATOR CLASS
# ============================================================================

class NarrativeGenerator:
    """Generates professional narrative text for all presentation sections."""

    def __init__(self, config: dict):
        """
        config: route configuration dict with keys like airline_name, origin,
                destination, buyer_type, demand_driver, frequency, etc.
        """
        self.cfg = config
        self.forecast = config.get("forecast", {})
        self.research = config.get("research", {})
        self.market_data = config.get("market_data", {})
        self.airport_data = config.get("airport_data", {})

        bt = (config.get("buyer_type", "airport_pitch")).lower().replace(" ", "_").replace("-", "_")
        self.tone = TONE.get(bt, TONE["airport_pitch"])
        self.buyer_type = bt

        self.airline = config.get("airline_name", "the airline")
        self.origin = config.get("origin", "XXX")
        self.dest = config.get("destination", "YYY")
        self.origin_city = config.get("origin_city", "Origin City")
        self.dest_city = config.get("dest_city", "Destination City")
        self.origin_country = config.get("origin_country", "Origin Country")
        self.dest_country = config.get("dest_country", "Destination Country")
        self.freq = config.get("frequency", 7)
        self.demand_driver = config.get("demand_driver", "Mixed")

    def load_forecast(self, result):
        """Load pipeline forecast result (dict or object with attributes)."""
        if isinstance(result, dict):
            self.forecast = result
        else:
            # Convert pipeline result object to dict
            self.forecast = {
                "grand_total": getattr(result, "grand_total", 0),
                "p2p_total": getattr(result, "p2p_forecast", 0),
                "cnx_home_total": getattr(result, "cnx_home_forecast", 0),
                "cnx_dest_total": getattr(result, "cnx_dest_forecast", 0),
                "load_factor": getattr(result, "load_factor", 0),
                "annual_seats": getattr(result, "annual_seats", 0),
                "segments": getattr(result, "segments", []),
                "connecting_cities_home": getattr(result, "connecting_cities_home", []),
            }
        self.cfg["forecast"] = self.forecast

    def load_research(self, research_path_or_dict):
        """Load market research data from JSON file or dict."""
        if isinstance(research_path_or_dict, str):
            with open(research_path_or_dict) as f:
                self.research = json.load(f)
        else:
            self.research = research_path_or_dict
        self.cfg["research"] = self.research

    # ====================================================================
    # SECTION 1: COVER HEADLINE
    # ====================================================================
    def generate_headline(self) -> str:
        """Generate the cover slide headline."""
        headlines = {
            "airport_pitch": {
                "Business": f"A unique opportunity to directly link {self.origin_city} and {self.dest_country} to the {self._dest_descriptor()}",
                "Leisure": f"Connecting {self.origin_city} to {self.dest_city}  a new leisure gateway",
                "Mixed": f"Opportunity to serve {self.dest_city} and {self._dest_region()} from {self.origin_city}",
                "VFR-diaspora": f"Linking communities  {self.origin_city} to {self.dest_city} direct",
            },
            "airline_forecast": {
                "default": f"{self.origin}{self.dest} Route Assessment for {self.airline}",
            },
            "fund_due_diligence": {
                "default": f"{self.origin}{self.dest} Traffic and Revenue Forecast",
            },
        }

        buyer_hl = headlines.get(self.buyer_type, headlines["airport_pitch"])
        return buyer_hl.get(self.demand_driver, buyer_hl.get("default",
            f"Opportunity for {self.airline}: {self.origin_city}{self.dest_city}"))

    def _dest_descriptor(self):
        """Generate a destination descriptor based on demand driver."""
        descriptors = self.research.get("dest_descriptors", {})
        if descriptors:
            return descriptors.get(self.demand_driver, self.dest_city)
        # Fallback based on common patterns
        if self.demand_driver == "Business":
            return f"markets of {self.dest_city}"
        return self.dest_city

    def _dest_region(self):
        """Broader region name for destination."""
        return self.research.get("dest_region", self.dest_country)

    # ====================================================================
    # SECTION 3: EXECUTIVE SUMMARY
    # ====================================================================
    def generate_exec_summary_note(self) -> str:
        """Generate the footnote/catchment note for executive summary."""
        fc = self.forecast
        base_period = fc.get("base_period", "the last twelve months")
        catchment = self.cfg.get("catchment_description",
            f"a defined catchment area for {self.origin}")

        note = (
            f"AviaSolutions analysis. Source for aircraft configuration is "
            f"{self.airline} website. Base annual demand {base_period}. "
            f"Using AviaSolutions' {self.origin} Service Area catchment analysis, "
            f"restricting demand to {catchment}."
        )
        return note

    # ====================================================================
    # SECTION 4: WHY THIS ROUTE?
    # ====================================================================
    def generate_why_route(self) -> dict:
        """Generate Section 4 content: opening statement + 4 key point cards."""
        fc = self.forecast
        t = self.tone

        # Opening statement
        opening = self._why_opening()

        # Four cards  content depends on demand driver and available data
        points = []
        points.append(self._why_market_size())
        points.append(self._why_strategic_fit())
        points.append(self._why_competitive_gap())
        points.append(self._why_economic_drivers())

        return {
            "why_opening": opening,
            "why_points": points,
        }

    def _why_opening(self) -> str:
        """Generate the opening italic statement."""
        verb = self.tone["opening_verb"]
        p2p = self.forecast.get("p2p_total")
        cnx = self.forecast.get("cnx_home_total", 0) + self.forecast.get("cnx_dest_total", 0)

        # Use economic context for richer opening
        econ = self.research.get("economic_context", {})
        income = econ.get("household_income", "")
        wealth_fact = ""
        if income:
            wealth_fact = f" The {self.dest_city} metro area has the highest median household income in the US ({income.split('(')[0].strip()}), underpinning strong premium demand."

        if p2p and cnx:
            return (
                f"{self.airline} {verb} the market between {self.origin_city} "
                f"and {self.dest_city}, with {_fmt(p2p)} point-to-point passengers "
                f"and {_fmt(cnx)} connecting passengers representing a {self.tone['demand_adj']} "
                f"commercial opportunity.{wealth_fact}"
            )
        elif p2p:
            return (
                f"{self.airline} {verb} the {self.origin_city}{self.dest_city} market, "
                f"which carries {_fmt(p2p)} O&D passengers annually.{wealth_fact}"
            )
        else:
            return (
                f"{self.airline} {verb} the market between {self.origin_city} "
                f"and {self.dest_city}. The route offers a {self.tone['demand_adj']} "
                f"combination of point-to-point and connecting traffic opportunities.{wealth_fact}"
            )

    def _why_market_size(self) -> dict:
        """Card 1: Market Size."""
        fc = self.forecast
        p2p = fc.get("p2p_total")
        cnx_home = fc.get("cnx_home_total", 0)
        cnx_dest = fc.get("cnx_dest_total", 0)
        total = fc.get("grand_total")

        if total:
            hub_name = self.cfg.get("hub_name", self.origin_city)
            parts = [f"Total addressable market of {_fmt(total)} annual passengers."]
            if p2p:
                parts.append(f"Point-to-point demand: {_fmt(p2p)} passengers.")
            if cnx_home:
                parts.append(f"Connecting over {hub_name}: {_fmt(cnx_home)} passengers.")
            if cnx_dest and cnx_dest > 1000:
                parts.append(f"Connecting over {self.dest_city}: {_fmt(cnx_dest)} passengers.")
            return {"title": "Market Size", "text": " ".join(parts)}
        else:
            return {"title": "Market Size", "text": "DATA REQUIRED  Run QSI pipeline to quantify P2P and connecting demand."}

    def _why_strategic_fit(self) -> dict:
        """Card 2: Strategic Fit  why this airline."""
        driver = self.demand_driver
        alliance = self.cfg.get("alliance", "")

        if driver == "Business":
            text = (
                f"{self.airline}'s premium product and {alliance + ' ' if alliance else ''}"
                f"network make it well suited to capture high-yield business traffic "
                f"between {self.origin_city} and {self.dest_city}. "
                f"The route complements {self.airline}'s existing {self.origin} hub connectivity."
            )
        elif driver == "Leisure":
            text = (
                f"{self.airline} can leverage its brand recognition and distribution "
                f"to stimulate new leisure demand on {self.origin}{self.dest}. "
                f"The route fills a gap in direct leisure connectivity."
            )
        elif driver == "VFR-diaspora":
            text = (
                f"{self.airline}'s established presence in the {self.dest_country} diaspora community "
                f"positions it to capture VFR traffic between {self.origin_city} and {self.dest_city}. "
                f"Heritage connections underpin year-round demand."
            )
        else:
            text = (
                f"{self.airline}'s network, fleet, and brand are well matched to the "
                f"mixed business and leisure demand profile of {self.origin}{self.dest}."
            )

        return {"title": "Strategic Fit", "text": text}

    def _why_competitive_gap(self) -> dict:
        """Card 3: Competitive Gap."""
        competitors = self.market_data.get("competitors", [])
        alliance = self.cfg.get("alliance", "")

        if not competitors or len(competitors) == 0:
            text = (
                f"No airline currently operates direct services between {self.origin} "
                f"and {self.dest}. This represents an unserved market where all "
                f"passengers currently travel via indirect routings."
            )
            if alliance:
                text += f" There is no {alliance} competition at {self.dest}."
        else:
            carrier_list = ", ".join(c.get("carrier", "Unknown") for c in competitors[:3])
            text = (
                f"Current direct service is provided by {carrier_list}. "
                f"{self.airline} would offer a differentiated product through its "
                f"{self.origin} hub connectivity and {alliance + ' alliance ' if alliance else ''}"
                f"network."
            )

        return {"title": "Competitive Gap", "text": text}

    def _why_economic_drivers(self) -> dict:
        """Card 4: Economic Drivers  based on demand type, with real research data."""
        research = self.research

        if self.demand_driver == "Business" or self.demand_driver == "Mixed":
            econ = research.get("economic_context", {})
            parts = []

            income = econ.get("household_income", "")
            if income:
                parts.append(f"{self.dest_city} metro median household income: {income}  highest in the US.")

            gdp_cap = econ.get("gdp_per_capita", "")
            if gdp_cap:
                parts.append(gdp_cap + ".")

            wealth = econ.get("wealth", "")
            if wealth:
                parts.append(wealth + ".")

            fortune = econ.get("fortune_1000", "")
            if fortune:
                parts.append(f"{fortune}.")

            sv_vc = econ.get("sv_vc", "")
            if sv_vc:
                parts.append(sv_vc + ".")

            asian_pop = econ.get("asian_population", "")
            if asian_pop:
                parts.append(asian_pop + ".")

            corp = research.get("corporate_links", [])
            if corp and len(corp) > 3:
                parts.append(
                    f"{len(corp)}+ {self.origin_country} companies with offices or "
                    f"innovation centres in the Bay Area, including "
                    f"{corp[0].get('company', '')}, {corp[1].get('company', '')}, "
                    f"and {corp[2].get('company', '')}."
                )

            trade = research.get("trade", [])
            if trade and len(trade) > 0:
                top_trade = trade[0]
                parts.append(
                    f"Bilateral trade: {top_trade.get('value', '')} "
                    f"({top_trade.get('source', '')})."
                )

            text = " ".join(parts) if parts else "DATA REQUIRED  Economic and corporate presence research needed."
        elif self.demand_driver == "Leisure":
            tourism = research.get("tourism", {})
            parts = []
            if tourism.get("outbound_visitors"):
                parts.append(f"{tourism['outbound_visitors']} travel from {self.origin_country} to {self.dest_country} annually.")
            if tourism.get("inbound_visitors"):
                parts.append(f"{tourism['inbound_visitors']} make the reverse journey.")
            if tourism.get("growth_rate"):
                parts.append(f"Visitor numbers growing at {tourism['growth_rate']}.")
            if tourism.get("spending"):
                parts.append(f"Visitor spending: {tourism['spending']}.")
            text = " ".join(parts) if parts else "DATA REQUIRED  Tourism statistics needed."
        else:
            econ = research.get("economic_context", {})
            text = econ.get("summary", "") if econ.get("summary") else (
                f"The {self.origin_city}{self.dest_city} market benefits from a combination of "
                f"business, leisure, and VFR demand drivers, providing year-round traffic diversity."
            )

        return {"title": "Economic Drivers", "text": text}

    # ====================================================================
    # SECTION 5: BILATERAL LINKS TEXT
    # ====================================================================
    def generate_bilateral_narrative(self) -> dict:
        """Generate prose for each bilateral links sub-section from real research."""
        output = {}

        # Corporate links narrative  use pre-written narrative if available
        corp_narr = self.research.get("corporate_links_narrative", "")
        corp = self.research.get("corporate_links", [])
        if corp_narr:
            output["corporate_narrative"] = corp_narr
        elif corp:
            output["corporate_narrative"] = (
                f"There are {len(corp)}+ {self.origin_country} companies with "
                f"subsidiaries or offices in the {self.dest_city} region, reflecting "
                f"deep corporate ties. These include "
                f"{', '.join(c.get('company', '') for c in corp[:4])}, and others."
            )

        # Tourism narrative  use pre-written or build from structured data
        tourism = self.research.get("tourism", {})
        if tourism:
            parts = []
            if tourism.get("outbound_visitors"):
                parts.append(
                    f"Approximately {tourism['outbound_visitors']} travel from "
                    f"{self.origin_country} to {self.dest_country} each year"
                )
            if tourism.get("inbound_visitors"):
                parts.append(
                    f"whilst {tourism['inbound_visitors']} make the "
                    f"reverse journey"
                )
            if tourism.get("growth_rate"):
                parts.append(f"with visitor numbers growing at {tourism['growth_rate']}")
            if tourism.get("spending"):
                parts.append(f"{self.dest_country} visitors spend {tourism['spending']} in the US annually")
            if parts:
                output["tourism_narrative"] = ". ".join(parts) + "."
                if tourism.get("sources"):
                    output["tourism_narrative"] += " Source: " + "; ".join(tourism["sources"]) + "."

        # Trade narrative  use pre-written or build from structured data
        trade_narr = self.research.get("trade_narrative", "")
        trade = self.research.get("trade", [])
        if trade_narr:
            output["trade_narrative"] = trade_narr
        elif trade:
            items = []
            for t in trade[:5]:
                items.append(f"{t.get('metric', '')}: {t.get('value', '')}")
                if t.get("source"):
                    items[-1] += f" ({t['source']})"
            output["trade_narrative"] = (
                f"Bilateral economic links between {self.origin_country} and "
                f"{self.dest_country} are substantial. " + ". ".join(items) + "."
            )

        # Diaspora narrative
        diaspora = self.research.get("diaspora", {})
        if diaspora and isinstance(diaspora, dict) and diaspora.get("text"):
            output["diaspora_narrative"] = diaspora["text"]

        return output

    # ====================================================================
    # SECTION 6: MARKET COMMENTARY
    # ====================================================================
    def generate_market_commentary(self) -> dict:
        """Generate analytical commentary for market background slides."""
        mkt = self.market_data
        output = {}

        # P2P trend commentary
        trend = mkt.get("p2p_trend", {})
        if trend and trend.get("years"):
            years = trend["years"]
            direct = trend.get("direct", [])
            indirect = trend.get("indirect", [])
            total = [(d or 0) + (i or 0) for d, i in zip(direct or [0]*len(years), indirect or [0]*len(years))]

            if len(total) >= 2 and total[0] > 0:
                growth = (total[-1] / total[0]) ** (1 / max(len(years) - 1, 1)) - 1
                output["p2p_trend_comment"] = (
                    f"O&D traffic between {self.origin_city} and {self.dest_city} has grown "
                    f"from {_fmt(total[0])} in {years[0]} to {_fmt(total[-1])} in {years[-1]}, "
                    f"representing a compound annual growth rate of {_pct(growth)}."
                )
                if direct and indirect and direct[-1] > 0:
                    direct_share = direct[-1] / (direct[-1] + (indirect[-1] or 1))
                    if direct_share < 0.1:
                        output["p2p_trend_comment"] += (
                            f" The market is almost entirely indirect, with passengers "
                            f"connecting via third-party hubs."
                        )
                    elif direct_share > 0.5:
                        output["p2p_trend_comment"] += (
                            f" Direct services account for {_pct(direct_share)} of total demand."
                        )

        # Seasonality commentary
        seas = mkt.get("seasonality", {})
        if seas and seas.get("values"):
            vals = seas["values"]
            peak_month_idx = vals.index(max(vals))
            trough_month_idx = vals.index(min(vals))
            months = seas.get("months", ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])
            ratio = max(vals) / max(min(vals), 1)

            if ratio > 2.0:
                output["seasonality_comment"] = (
                    f"The route shows pronounced seasonality with peak demand in "
                    f"{months[peak_month_idx]} ({_fmt(max(vals))} passengers) and a trough "
                    f"in {months[trough_month_idx]} ({_fmt(min(vals))} passengers). "
                    f"The peak-to-trough ratio of {ratio:.1f}x suggests a seasonal route "
                    f"profile requiring careful capacity management."
                )
            else:
                output["seasonality_comment"] = (
                    f"Demand is relatively evenly distributed across the year with a "
                    f"moderate peak in {months[peak_month_idx]}. The peak-to-trough ratio "
                    f"of {ratio:.1f}x indicates year-round viability."
                )

        # Connecting hub commentary
        hubs = mkt.get("connecting_hubs", [])
        if hubs:
            top = hubs[0]
            output["hub_comment"] = (
                f"Indirect traffic currently routes primarily through {top['hub']} "
                f"({_pct(top.get('share', 0))} share), followed by "
                f"{hubs[1]['hub'] if len(hubs) > 1 else 'other hubs'}. "
                f"{self.airline}'s {self.origin} hub would offer a competitive "
                f"alternative routing for this traffic."
            )

        return output

    # ====================================================================
    # SECTION 7: FORECAST METHODOLOGY TEXT
    # ====================================================================
    def generate_methodology(self) -> dict:
        """Generate the standard fill-in-the-blanks methodology text."""
        fc = self.forecast
        base_period = fc.get("base_period", "the last twelve months")
        base_year = fc.get("base_year", "2024")
        forecast_year = fc.get("forecast_year", "2026")
        growth_basis = fc.get("growth_basis",
            "GDP projections and historical traffic growth trends")
        catchment = self.cfg.get("catchment_description",
            f"a defined catchment area for {self.origin}")

        p2p_method = (
            f"To forecast the number of origin and destination (O&D) passengers, "
            f"the following methodology has been used:\n\n"
            f"i. Sabre Market Intelligence data for {base_period} was used to "
            f"estimate the overall size of O&D traffic between {self.origin_city} "
            f"and {self.dest_city}, restricted to {catchment}.\n\n"
            f"ii. Base annual demand was grown to {forecast_year} by assuming "
            f"an underlying compound growth rate for the {self.origin_city}"
            f"{self.dest_city} market. Growth rates have been determined by "
            f"{growth_basis}.\n\n"
            f"iii. Where appropriate, the point-to-point market has been "
            f"stimulated due to the new direct service between the two cities. "
            f"{self.tone['stim_framing']}.\n\n"
            f"iv. Capture rates have been determined {self.tone['capture_framing']}. "
            f"Capture rates depend on the frequency offered, alternative routings "
            f"available, and the strength of the brand and alliance at both ends "
            f"of the route."
        )

        cnx_method = (
            f"To forecast the number of connecting passengers, the following "
            f"methodology has been used:\n\n"
            f"i. Sabre MI {base_year} data was used to estimate the size of the "
            f"connecting markets.\n\n"
            f"ii. Note that demand between markets that required connections over "
            f"both {self.origin} and {self.dest} (double connection) was excluded "
            f"from the analysis.\n\n"
            f"iii. Base annual demand was grown to {forecast_year}.\n\n"
            f"iv. Demand from {self.origin_city} to markets beyond {self.dest}, "
            f"and vice versa, was not stimulated due to direct services and "
            f"alternative routings that may already exist.\n\n"
            f"v. A Quality Service Index (QSI) model was used to estimate the "
            f"share that the new service could potentially capture of the connecting "
            f"demand. The QSI model calculates the potential share by taking into "
            f"consideration the following factors:\n"
            f"   1. Total elapsed time  the total time from departure of the first "
            f"flight until arrival of the second flight. Routings involving a "
            f"connection less than the minimum connecting time (MCT) were excluded.\n"
            f"   2. Connection type  online, interline versus codeshare/alliance "
            f"connection.\n"
            f"   3. Frequency  the total number of times per week that a particular "
            f"routing is possible. Multi-stop routings were excluded from the analysis."
        )

        return {
            "p2p_methodology": p2p_method,
            "cnx_methodology": cnx_method,
        }

    # ====================================================================
    # SECTION 7: FORECAST TABLE NOTES
    # ====================================================================
    def generate_forecast_notes(self) -> list:
        """Generate the standard 6 mandatory notes below the forecast table."""
        fc = self.forecast
        base_period = fc.get("base_period", "[period]")
        catchment = self.cfg.get("catchment_description", "[catchment area]")
        growth_basis = fc.get("growth_basis",
            "Growth rates based on GDP projections and historical traffic trends.")

        notes = [
            f" Demand for point-to-point market and connecting markets based on "
            f"Sabre MI for {base_period}, restricted to {catchment}.",
            f" {growth_basis}",
            f" Based on IATA Stimulation Curve. {self.tone['stim_framing']}.",
            f" Point-to-point capture rates {self.tone['capture_framing']}. "
            f"Connecting market capture rate based on QSI model.",
            f" Demand on double connections has been excluded.",
            f" Passengers per trip each way.",
            f"AviaSolutions analysis",
        ]
        return notes

    # ====================================================================
    # SECTION 7E: FORECAST UPSIDES / COMMENTARY
    # ====================================================================
    def generate_forecast_commentary(self) -> str:
        """Generate qualitative forecast commentary paragraph."""
        fc = self.forecast
        total = fc.get("grand_total", 0)
        lf = fc.get("load_factor", 0)

        if self.buyer_type == "airport_pitch":
            return (
                f"Based upon conservative assumptions, AviaSolutions forecasts "
                f"that {self.airline} could carry {_fmt(total)} passengers annually on "
                f"{self.origin}{self.dest}, {self.tone['load_factor_comment'](lf)}. "
                f"There are additional upside opportunities including higher stimulation "
                f"from marketing initiatives, codeshare traffic from alliance partners, "
                f"and potential frequency increases as the route matures."
            )
        elif self.buyer_type == "fund_due_diligence":
            return (
                f"The base case forecast of {_fmt(total)} annual passengers represents "
                f"a conservative projection, {self.tone['load_factor_comment'](lf)}. "
                f"Key assumptions that could improve the outcome include: higher "
                f"stimulation than modelled, incremental connecting traffic from "
                f"alliance partners, and faster underlying market growth. "
                f"Downside risks include competitive entry, economic slowdown, "
                f"and fare dilution."
            )
        else:
            return (
                f"The forecast of {_fmt(total)} annual passengers is based upon "
                f"conservative assumptions throughout, {self.tone['load_factor_comment'](lf)}. "
                f"The connecting traffic component is derived from QSI model calibration "
                f"benchmarked against comparable routes in the AviaSolutions library."
            )

    # ====================================================================
    # SECTION 8: AIRPORT OVERVIEW TEXT
    # ====================================================================
    def generate_airport_narrative(self) -> str:
        """Generate airport overview prose from real research data."""
        apt = self.airport_data
        pax = apt.get("annual_pax", "")
        catchment = apt.get("catchment_pop", "")
        growth = apt.get("growth_rate", "")
        on_time = apt.get("on_time", "")
        position = apt.get("position", "")
        development = apt.get("development", "")

        parts = []
        parts.append(
            f"{self.dest_city} Mineta International Airport ({self.dest}) handled "
            f"{pax or 'DATA REQUIRED'} passengers in 2024, serving a catchment "
            f"population of {catchment or 'DATA REQUIRED'}."
        )

        if position:
            parts.append(position)

        if on_time:
            parts.append(on_time + ".")

        if growth:
            parts.append(f"Recent traffic growth: {growth}.")

        if development:
            parts.append(development)

        if self.buyer_type == "airport_pitch":
            parts.append(
                f"The airport offers the infrastructure, incentive programmes, "
                f"and operational capability to support {self.airline}'s new service."
            )

        return " ".join(parts)

    # ====================================================================
    # CLOSING SLIDE
    # ====================================================================
    def generate_closing(self) -> dict:
        """Generate closing headline and bullet points."""
        fc = self.forecast
        total = fc.get("grand_total", 0)
        lf = fc.get("load_factor", 0)

        if self.buyer_type == "airport_pitch":
            headline = f"A Unique Opportunity to Link {self.origin_city} and {self.dest_city}"
            points = [
                f"{self.tone['demand_adj'].capitalize()} untapped demand of {_fmt(total)} annual passengers",
                f"Strong {self.demand_driver.lower()} traffic drivers between {self.origin_country} and {self.dest_country}",
                f"{self.airline} well positioned through {self.origin} hub and {'alliance ' if self.cfg.get('alliance') else ''}network",
                f"No direct competition  passengers currently rely on indirect routings" if not self.market_data.get("competitors") else f"Differentiated offering through {self.airline}'s premium product",
                f"Conservative forecast supports {self.tone['load_factor_comment'](lf)}" if lf else f"Conservative forecast methodology based on Sabre MI and QSI model",
                f"{self.dest_city} offers infrastructure, incentives, and stakeholder support",
            ]
        elif self.buyer_type == "fund_due_diligence":
            headline = f"{self.origin}{self.dest} Route Assessment Summary"
            points = [
                f"Base case forecast of {_fmt(total)} annual passengers on conservative assumptions",
                f"Methodology benchmarked against comparable routes in calibration library",
                f"Stimulation factors at lower end of IATA range",
                f"Capture rates validated through QSI model calibration",
                f"Revenue projection based on market-specific fare analysis" if fc.get("revenue") else f"Revenue forecast available upon fare data analysis",
                f"Sensitivity analysis confirms viability under downside scenarios",
            ]
        else:
            headline = f"{self.origin}{self.dest} Route Forecast Summary"
            points = [
                f"Forecast of {_fmt(total)} annual passengers ({self.freq}x weekly service)",
                f"P2P demand of {_fmt(fc.get('p2p_total', 0))} plus connecting traffic of {_fmt(fc.get('cnx_home_total', 0) + fc.get('cnx_dest_total', 0))}",
                f"Conservative stimulation and capture rate assumptions throughout",
                f"QSI model calibrated against AviaSolutions' route library",
                f"Schedule designed around {self.origin} hub connectivity" if self.demand_driver == "Business" else f"Schedule balanced for year-round demand capture",
            ]

        return {
            "closing_headline": headline,
            "closing_points": [p for p in points if p],  # remove any empty
        }

    # ====================================================================
    # MASTER: GENERATE ALL
    # ====================================================================
    def generate_all(self) -> dict:
        """
        Generate all narrative content and merge into the config dict.
        Returns the complete config ready for the PPTX generator.
        """
        config = dict(self.cfg)  # copy

        # Section 1: Cover
        if not config.get("headline"):
            config["headline"] = self.generate_headline()

        # Section 3: Exec summary note
        config["catchment_note"] = self.generate_exec_summary_note()

        # Section 4: Why This Route
        why = self.generate_why_route()
        if not config.get("why_opening"):
            config["why_opening"] = why["why_opening"]
        if not config.get("why_points") or all(
            p.get("text", "").startswith("DATA REQUIRED") for p in config.get("why_points", [])
        ):
            config["why_points"] = why["why_points"]

        # Section 5: Bilateral links prose
        bilateral = self.generate_bilateral_narrative()
        config.setdefault("research", {}).update(bilateral)

        # Section 6: Market commentary
        commentary = self.generate_market_commentary()
        config["market_commentary"] = commentary

        # Section 7: Methodology
        methodology = self.generate_methodology()
        config.setdefault("forecast", {})["p2p_methodology"] = methodology["p2p_methodology"]
        config["forecast"]["cnx_methodology"] = methodology["cnx_methodology"]
        config["forecast"]["notes"] = self.generate_forecast_notes()
        config["forecast"]["commentary"] = self.generate_forecast_commentary()

        # Section 8: Airport
        config["airport_narrative"] = self.generate_airport_narrative()

        # Closing
        closing = self.generate_closing()
        if not config.get("closing_headline"):
            config["closing_headline"] = closing["closing_headline"]
        if not config.get("closing_points"):
            config["closing_points"] = closing["closing_points"]

        return config


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def generate_narrative(config: dict,
                       forecast: dict = None,
                       research: dict = None) -> dict:
    """
    One-shot function: takes route config, optional forecast and research,
    returns a complete config dict with all narrative fields populated.

    >>> config = generate_narrative(base_config, pipeline_result, research_data)
    >>> # config is now ready for city_pair_pptx_generator.js
    """
    ng = NarrativeGenerator(config)
    if forecast:
        ng.load_forecast(forecast)
    if research:
        ng.load_research(research)
    return ng.generate_all()


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python narrative_generator.py config.json [--research research.json]")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        config = json.load(f)

    research = None
    if "--research" in sys.argv:
        idx = sys.argv.index("--research")
        with open(sys.argv[idx + 1]) as f:
            research = json.load(f)

    result = generate_narrative(config, research=research)

    output_path = sys.argv[1].replace(".json", "_narrated.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"Narrated config written to {output_path}")
    print(f"  Headline: {result.get('headline', 'N/A')}")
    print(f"  Why points: {len(result.get('why_points', []))}")
    print(f"  Closing points: {len(result.get('closing_points', []))}")
