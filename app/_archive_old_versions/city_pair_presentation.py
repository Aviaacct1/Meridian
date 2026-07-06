"""
Avia Solutions  City Pair Presentation Bridge
================================================
Converts QSI pipeline output + research data into a JSON config
and invokes the PPTX generator to produce a branded presentation.

Usage:
    from city_pair_presentation import PresentationBuilder
    
    builder = PresentationBuilder(
        airline="British Airways", airline_code="BA",
        origin="LHR", destination="SJC",
        origin_city="London", dest_city="San Jose",
        origin_country="United Kingdom", dest_country="United States",
    )
    
    # Load from pipeline results
    builder.load_pipeline_results(pipeline_result)
    
    # Add research data
    builder.load_research_json("CX_HKG_SJC_Research.json")
    
    # Generate
    output_path = builder.generate("output.pptx")
"""

import json
import subprocess
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path


@dataclass
class ScheduleConfig:
    outbound_dep: str = ""
    outbound_arr: str = ""
    return_dep: str = ""
    return_arr: str = ""
    op_days: str = ""


@dataclass
class ForecastSegment:
    label: str = ""
    base_demand: float = 0
    cagr: float = 0
    grown_demand: float = 0
    stimulation: float = 1.0
    stimulated_demand: float = 0
    capture_rate: float = 0
    forecast: float = 0
    ptew: float = 0


@dataclass
class ConnectingCity:
    code: str = ""
    name: str = ""
    country: str = ""
    base_demand: float = 0
    share: float = 0
    forecast: float = 0
    ptew: float = 0


@dataclass
class RevenueData:
    y1_p2p_pax: float = 0
    y1_cnx_pax: float = 0
    y1_total_pax: float = 0
    y1_lf: float = 0
    y1_pax_rev: float = 0
    y1_cargo: float = 0
    y1_total_rev: float = 0
    y2_p2p_pax: float = 0
    y2_cnx_pax: float = 0
    y2_total_pax: float = 0
    y2_lf: float = 0
    y2_pax_rev: float = 0
    y2_cargo: float = 0
    y2_total_rev: float = 0
    y3_p2p_pax: float = 0
    y3_cnx_pax: float = 0
    y3_total_pax: float = 0
    y3_lf: float = 0
    y3_pax_rev: float = 0
    y3_cargo: float = 0
    y3_total_rev: float = 0


class PresentationBuilder:
    """Builds the JSON config for the PPTX generator from pipeline data."""
    
    def __init__(self, airline: str, airline_code: str,
                 origin: str, destination: str,
                 origin_city: str, dest_city: str,
                 origin_country: str = "", dest_country: str = "",
                 **kwargs):
        self.config = {
            "airline_name": airline,
            "airline_code": airline_code,
            "origin": origin,
            "destination": destination,
            "origin_city": origin_city,
            "dest_city": dest_city,
            "origin_country": origin_country,
            "dest_country": dest_country,
            "hub_name": kwargs.get("hub_name", origin_city),
            "frequency": kwargs.get("frequency", 7),
            "aircraft_type": kwargs.get("aircraft_type", ""),
            "seats": kwargs.get("seats", 0),
            "demand_driver": kwargs.get("demand_driver", "Mixed"),
            "route_type": kwargs.get("route_type", "Hub long-haul"),
            "buyer_type": kwargs.get("buyer_type", "Airport pitch"),
            "client_name": kwargs.get("client_name", ""),
            "date": kwargs.get("date", ""),
            "confidentiality": kwargs.get("confidentiality",
                "Confidential  Prepared for discussion purposes only"),
        }
        
        # Initialise empty sections
        self.config["schedule"] = {}
        self.config["forecast"] = {}
        self.config["research"] = {}
        self.config["market_data"] = {}
        self.config["airport_data"] = {}
        self.config["why_points"] = []
        self.config["closing_points"] = []
    
    def set_headline(self, headline: str):
        """Set the cover slide headline."""
        self.config["headline"] = headline
        return self
    
    def set_schedule(self, outbound_dep: str, outbound_arr: str,
                     return_dep: str, return_arr: str,
                     op_days: str = "Daily"):
        """Set the schedule details."""
        self.config["schedule"] = {
            "outbound_dep": outbound_dep,
            "outbound_arr": outbound_arr,
            "return_dep": return_dep,
            "return_arr": return_arr,
            "op_days": op_days,
        }
        return self
    
    def load_pipeline_results(self, result: dict):
        """
        Load forecast data from pipeline run results.
        
        Expected keys in result:
            - p2p_total, cnx_home_total, cnx_dest_total, grand_total
            - load_factor, annual_seats
            - segments: list of dicts with label, base_demand, etc.
            - connecting_cities_home: list of dicts
        """
        fc = self.config.get("forecast", {})
        
        # Core forecast numbers
        fc["p2p_total"] = result.get("p2p_total", 0)
        fc["cnx_home_total"] = result.get("cnx_home_total", 0)
        fc["cnx_dest_total"] = result.get("cnx_dest_total", 0)
        fc["grand_total"] = result.get("grand_total", 0)
        fc["load_factor"] = result.get("load_factor", 0)
        fc["annual_seats"] = result.get("annual_seats", 0)
        
        # Segments
        if "segments" in result:
            fc["segments"] = result["segments"]
        
        # Connecting cities
        if "connecting_cities_home" in result:
            fc["connecting_cities_home"] = result["connecting_cities_home"]
        if "connecting_cities_dest" in result:
            fc["connecting_cities_dest"] = result["connecting_cities_dest"]
        
        # Revenue
        if "revenue" in result:
            fc["revenue"] = result["revenue"]
        
        self.config["forecast"] = fc
        return self
    
    def load_from_route_config(self, route_config):
        """
        Load from a RouteConfig object (from the pipeline).
        Extracts aircraft, frequency, schedule, and demand parameters.
        """
        rc = route_config
        
        self.config["frequency"] = getattr(rc, "frequency", 7)
        self.config["aircraft_type"] = getattr(rc, "aircraft_type", "")
        self.config["seats"] = getattr(rc, "seats_per_flight", 0)
        
        # Extract P2P demand segments if available
        if hasattr(rc, "p2p_segments"):
            segments = []
            for seg in rc.p2p_segments:
                segments.append({
                    "label": seg.get("label", ""),
                    "base_demand": seg.get("base_demand", 0),
                    "cagr": seg.get("cagr", 0),
                    "stimulation": seg.get("stimulation", 1.0),
                    "capture_rate": seg.get("capture_rate", 0),
                })
            if segments:
                self.config["forecast"]["segments"] = segments
        
        return self
    
    def load_research_json(self, filepath: str):
        """Load research data from a JSON file (produced by market_research_executor)."""
        with open(filepath, "r") as f:
            data = json.load(f)
        
        research = self.config.get("research", {})
        
        # Map research blocks to presentation sections
        if "blocks" in data:
            for block in data["blocks"]:
                block_name = block.get("block_name", "")
                findings = block.get("findings", [])
                
                if "economic" in block_name.lower():
                    research["economic"] = {
                        "findings": findings,
                        "citations": block.get("citations", []),
                    }
                elif "trade" in block_name.lower():
                    trade_items = []
                    for f in findings:
                        trade_items.append({
                            "metric": f.get("title", ""),
                            "value": f.get("value", ""),
                        })
                    research["trade"] = trade_items
                    research["trade_source"] = self._extract_source(block)
                    
                elif "tourism" in block_name.lower() or "visitor" in block_name.lower():
                    research["tourism"] = {
                        "outbound_visitors": self._find_value(findings, "outbound"),
                        "inbound_visitors": self._find_value(findings, "inbound"),
                        "growth_rate": self._find_value(findings, "growth"),
                        "spending": self._find_value(findings, "spending"),
                    }
                    research["tourism_source"] = self._extract_source(block)
                    
                elif "corporate" in block_name.lower() or "tech" in block_name.lower():
                    companies = []
                    for f in findings:
                        if isinstance(f, dict) and "company" in f:
                            companies.append(f)
                    research["corporate_links"] = companies
                    research["corporate_source"] = self._extract_source(block)
                    
                elif "diaspora" in block_name.lower() or "vfr" in block_name.lower():
                    research["diaspora"] = {
                        "text": "\n".join(
                            f.get("text", str(f)) for f in findings
                        )
                    }
                    research["diaspora_source"] = self._extract_source(block)
        
        self.config["research"] = research
        return self
    
    def set_why_points(self, points: List[Dict[str, str]]):
        """Set the 'Why this route?' key points. Each dict: {title, text}."""
        self.config["why_points"] = points
        return self
    
    def set_closing_points(self, points: List[str]):
        """Set the closing slide bullet points."""
        self.config["closing_points"] = points
        return self
    
    def set_market_data(self, market_data: dict):
        """
        Set market background data for charts.
        
        Expected keys:
            p2p_trend: {years, direct, indirect}
            seasonality: {months, values}
            connecting_home: {cities: [{city, demand}]}
            competitors: [{carrier, alliance, frequency, aircraft, seats}]
        """
        self.config["market_data"] = market_data
        return self
    
    def set_airport_data(self, airport_data: dict):
        """Set airport overview data."""
        self.config["airport_data"] = airport_data
        return self
    
    def set_cover_image(self, image_path: str):
        """Set background image for cover and closing slides."""
        self.config["cover_image"] = image_path
        return self

    def set_images(self, cover: str = None, closing: str = None,
                   contents: str = None, **section_images):
        """Set background images for multiple slides.
        
        Args:
            cover: Cover slide image path/URL
            closing: Closing slide image path/URL
            contents: Contents page image path/URL
            **section_images: section_1, section_2, etc. for divider slides
        """
        images = {}
        if cover: images["cover"] = cover
        if closing: images["closing"] = closing
        if contents: images["contents"] = contents
        images.update(section_images)
        self.config["images"] = images
        if cover:
            self.config["cover_image"] = cover
        return self

    def set_connecting_hubs(self, hubs: list):
        """Set connecting hub data for pie chart.
        
        Args:
            hubs: List of dicts with keys: hub, share, pax
                  e.g. [{"hub": "SFO", "share": 0.32, "pax": 59900}, ...]
        """
        self.config.setdefault("market_data", {})["connecting_hubs"] = hubs
        return self

    def set_alliance_split(self, alliances: list):
        """Set alliance capacity split for pie chart.
        
        Args:
            alliances: List of dicts with keys: alliance, seats
                       e.g. [{"alliance": "Star Alliance", "seats": 45200}, ...]
        """
        self.config.setdefault("market_data", {})["alliance_split"] = alliances
        return self

    def set_appendix(self, companies: list = None,
                     methodology_detail: str = None,
                     sensitivity_matrix: dict = None,
                     cannibalization: dict = None):
        """Set appendix slide data.
        
        Args:
            companies: List of dicts for company table
            methodology_detail: Extended methodology text
            sensitivity_matrix: Dict with 'headers' and 'rows'
            cannibalization: Dict with 'headers', 'table', 'note'
        """
        appendix = {}
        if companies: appendix["companies"] = companies
        if methodology_detail: appendix["methodology_detail"] = methodology_detail
        if sensitivity_matrix: appendix["sensitivity_matrix"] = sensitivity_matrix
        if cannibalization: appendix["cannibalization"] = cannibalization
        self.config["appendix"] = appendix
        return self

    def set_sensitivity(self, scenarios: list):
        """Set sensitivity analysis data for inline forecast section.
        
        Args:
            scenarios: List of dicts with keys: parameter, base, downside, impact
        """
        self.config.setdefault("forecast", {})["sensitivity"] = scenarios
        return self
    
    def generate(self, output_path: str = None,
                 generator_path: str = None) -> str:
        """
        Generate the PPTX presentation.
        
        Args:
            output_path: Where to save the .pptx file
            generator_path: Path to city_pair_pptx_generator.js
            
        Returns:
            Path to the generated file
        """
        if output_path is None:
            origin = self.config["origin"]
            dest = self.config["destination"]
            airline = self.config["airline_name"].replace(" ", "_")
            output_path = f"{origin}_{dest}_{airline}.pptx"
        
        if generator_path is None:
            # Look in same directory as this script
            this_dir = os.path.dirname(os.path.abspath(__file__))
            generator_path = os.path.join(this_dir, "city_pair_pptx_generator.js")
        
        # Write config to temp JSON
        config_path = output_path.replace(".pptx", "_config.json")
        with open(config_path, "w") as f:
            json.dump(self.config, f, indent=2, default=str)
        
        # Invoke the Node.js generator
        cmd = ["node", generator_path, "--config", config_path, "--output", output_path]
        
        print(f"\nGenerating presentation: {output_path}")
        print(f"Config: {config_path}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"ERROR: {result.stderr}")
            raise RuntimeError(f"PPTX generation failed: {result.stderr}")
        
        print(result.stdout)
        
        # Clean up config file (optional  useful to keep for debugging)
        # os.remove(config_path)
        
        return output_path
    
    def get_config(self) -> dict:
        """Return the current config dict (for inspection or manual editing)."""
        return self.config
    
    def save_config(self, filepath: str):
        """Save config to JSON for later use or editing."""
        with open(filepath, "w") as f:
            json.dump(self.config, f, indent=2, default=str)
        print(f"Config saved: {filepath}")
    
    # ---- Internal helpers ----
    
    def _extract_source(self, block: dict) -> str:
        citations = block.get("citations", [])
        if citations:
            sources = [c.get("source", "") for c in citations[:3]]
            return "Source: " + "; ".join(s for s in sources if s)
        return ""
    
    def _find_value(self, findings: list, keyword: str) -> str:
        for f in findings:
            if isinstance(f, dict):
                text = f.get("text", "") or f.get("value", "") or str(f)
            else:
                text = str(f)
            if keyword.lower() in text.lower():
                return text
        return "DATA REQUIRED"


# =============================================================================
# QUICK-USE FUNCTIONS
# =============================================================================

def from_pipeline_result(config_obj, pipeline_result: dict,
                         output_path: str = None) -> str:
    """
    One-shot: take a RouteConfig + pipeline result and generate a presentation.
    
    Args:
        config_obj: RouteConfig from the pipeline
        pipeline_result: dict from run_pipeline()
        output_path: where to save
        
    Returns:
        Path to generated PPTX
    """
    builder = PresentationBuilder(
        airline=getattr(config_obj, "airline_name", "Airline"),
        airline_code=getattr(config_obj, "airline_code", "XX"),
        origin=getattr(config_obj, "origin", "XXX"),
        destination=getattr(config_obj, "destination", "YYY"),
        origin_city=getattr(config_obj, "origin_city", "Origin"),
        dest_city=getattr(config_obj, "dest_city", "Destination"),
        origin_country=getattr(config_obj, "origin_country", ""),
        dest_country=getattr(config_obj, "dest_country", ""),
        frequency=getattr(config_obj, "frequency", 7),
        aircraft_type=getattr(config_obj, "aircraft_type", ""),
        seats=getattr(config_obj, "seats_per_flight", 0),
    )
    
    builder.load_pipeline_results(pipeline_result)
    return builder.generate(output_path)


if __name__ == "__main__":
    # Demo: generate BA LHR-SJC from the test config
    print("City Pair Presentation Bridge  Demo")
    print("=" * 50)
    
    builder = PresentationBuilder(
        airline="British Airways", airline_code="BA",
        origin="LHR", destination="SJC",
        origin_city="London", dest_city="San Jose",
        origin_country="United Kingdom", dest_country="United States",
    )
    
    # In production, these would come from the pipeline
    builder.config["headline"] = "Demo presentation from pipeline bridge"
    builder.config["forecast"]["grand_total"] = 129162
    builder.config["forecast"]["p2p_total"] = 51483
    builder.config["forecast"]["cnx_home_total"] = 68782
    builder.config["forecast"]["load_factor"] = 0.829
    
    builder.save_config("demo_config.json")
    print("\nConfig saved. Run with: node city_pair_pptx_generator.js --config demo_config.json")
