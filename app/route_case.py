#!/usr/bin/env python3
"""
Avia Solutions - RouteCase: the single definition of a route to assess.
=======================================================================
Everything the catchment -> demand -> load-factor -> P&L chain needs that is SPECIFIC to a
route lives here, in one serialisable object. The Genoa-New York build proved the chain;
this turns that one hard-coded example into a tool that runs ANY origin-destination by
swapping the case, not the code.

A RouteCase carries:
  - catchment geography  : home airport, search centre/radius, GeoNames countries + min pop
  - candidate airports   : the airports the catchment chooses between, each with a raw size
                           pull (annual pax, millions) used only to seed calibration
  - destination market   : the airports that make up the destination (e.g. NYC = JFK/EWR/LGA)
                           and the one used for the route P&L sector
  - observed-split scope  : the Sabre point-of-origin country / cities that define the residents
  - service / economics  : aircraft, sector distance and block time, overflown airspace, airline
                           type and age, and the planning defaults (capture, frequency, fares...)

Calibration OUTPUT (logit_scale, att_exponent, value_of_time) is NOT stored here; it is the
fitted-parameters JSON the calibration step writes. The case is the input; the fit is derived.

Offline principle: a case may point at a cached observed split (observed_cache), so the whole
chain runs with no Sabre connection - the laptop / World Routes path. When a live Sabre store
is supplied the assess step queries it and can refresh that cache.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple


@dataclass
class CandidateAirport:
    """An airport the catchment apportions demand across."""
    code: str
    lat: float
    lon: float
    size_pull_m: float = 1.0     # raw annual pax (millions); seeds the size term, then calibrated
    name: str = ""               # display name for decks / tables
    calibrate: bool = True       # include in the Sabre calibration target?
    cache_only: bool = False     # build a drive-time entry but keep out of catchment scoring


@dataclass
class RouteCase:
    # ---- identity
    case_id: str                                    # e.g. "genoa_nyc"
    title: str = ""                                 # e.g. "Genoa - New York"
    home: str = ""                                  # the proposed-service airport, e.g. "GOA"

    # ---- catchment geography
    centre: Tuple[float, float] = (0.0, 0.0)        # (lat, lon) search centre
    radius_km: float = 220.0
    countries: List[str] = field(default_factory=list)   # GeoNames country filter, e.g. ["IT","FR"]
    min_pop: float = 5000.0

    # ---- candidate airports
    airports: List[CandidateAirport] = field(default_factory=list)

    # ---- destination market
    dest_name: str = ""                             # e.g. "New York"
    dest_airports: List[str] = field(default_factory=list)   # e.g. ["JFK","EWR","LGA"]
    primary_dest: str = ""                          # the airport used for the P&L sector, e.g. "JFK"

    # ---- observed-split scope (Sabre point-of-origin)
    poo_country: Optional[str] = None               # e.g. "IT"
    poo_cities: Optional[List[str]] = None          # explicit point-of-origin city codes, if known
    observed_cache: Optional[str] = None            # JSON cache for offline runs (relative to case file)

    # ---- airline identity (optional; None/blank = airline-agnostic / generic pitch)
    airline_name: str = ""                          # e.g. "British Airways"; blank = generic
    airline_iata: str = ""                          # e.g. "BA"; blank = generic
    alliance: str = ""                              # e.g. "oneworld"; informs connecting online/alliance coeff
    service_year: Optional[int] = None              # the deck's maturity/service year; None = current
    hub_airport: str = ""                           # the carrier's connecting hub; blank = defaults to home

    # ---- service / economics
    aircraft: str = "A21X"                          # an AIRCRAFT code, or "AUTO" to auto-select best-fit-for-profit
    fleet: Optional[List[str]] = None               # candidate AIRCRAFT codes for AUTO selection (the airline's fleet); None = all in-range
    cabin_config: Optional[Dict[str, int]] = None   # {"business","premium_coach","coach"}; None = the aircraft's 2-class default
    sector_nm: float = 3500.0
    block_min: float = 540.0                        # one-way block time, minutes
    airspace: Dict[str, float] = field(default_factory=dict)   # {country: $/km overflight}
    airline_type: str = "LCC"
    aircraft_age: int = 2

    # planning defaults (every one overridable on the assess CLI)
    capture: float = 0.65                           # share of leaked own-catchment a nonstop wins
    frequency: int = 7                              # flights/week each way
    econ_share: float = 0.90                        # economy share of demand
    bus_fare_ow: float = 1300.0                     # one-way business fare
    premium_fare_ow: float = 1300.0                 # full-business-cabin sensitivity fare
    econ_fare_ow: Optional[float] = None            # pinned one-way economy yield; None = derive from avg_fare
    fuel_price_usd_kg: Optional[float] = None        # planning jet fuel $/kg; None = module default (0.68)
    market_factor: Optional[float] = None            # demand multiplier (1.0 neutral; e.g. 0.86 = -14% soft market)
    seasonality_profile: Optional[List[float]] = None  # 12 monthly demand indices Jan-Dec (mean 1.0); seasonality default
    natural_override: Optional[float] = None         # residence-based home-catchment demand; bypasses catchment apportionment when the gencost model over-states a small origin next to a mega-hub
    fare_basis: str = "rt"                          # Sabre avg_total_fare: "rt" (halve) or "ow"
    plan_lf: float = 0.875                           # planning load-factor cap (no route runs 95%)
    stimulation: float = 1.15                       # new-nonstop market uplift

    # home-airport route-development support, applied only when --incentive is set
    incentive_waiver_pct: float = 0.50              # share of home aeronautical charges waived
    incentive_support_per_turn: float = 1500.0      # marketing/route funding per turnaround

    # ---- cache filenames (relative to the case file's folder unless absolute)
    drive_cache: Optional[str] = None               # e.g. "genoa_drive.json"
    params_file: Optional[str] = None               # fitted-params JSON, e.g. "genoa_catchment_params.json"

    # ----------------------------------------------------------------- accessors
    @property
    def centre_lat(self) -> float:
        return self.centre[0]

    @property
    def centre_lon(self) -> float:
        return self.centre[1]

    def calibration_airports(self) -> List[CandidateAirport]:
        """The airports scored against the Sabre observed split (cache-only / excluded dropped)."""
        return [a for a in self.airports if a.calibrate and not a.cache_only]

    def catchment_airports(self) -> List[CandidateAirport]:
        """The airports the catchment apportions over (everything not cache-only)."""
        return [a for a in self.airports if not a.cache_only]

    def cache_airports(self) -> List[CandidateAirport]:
        """Every airport a drive-time cache should cover (includes cache-only competitors)."""
        return list(self.airports)

    def names(self) -> Dict[str, str]:
        return {a.code: (a.name or a.code) for a in self.airports}

    def airport_codes(self, which: str = "catchment") -> List[str]:
        pick = {"catchment": self.catchment_airports, "calibration": self.calibration_airports,
                "cache": self.cache_airports}[which]
        return [a.code for a in pick()]

    def to_airport_objs(self, which: str = "catchment", with_size: bool = False):
        """Build catchment.Airport objects. with_size sets attractiveness from size_pull_m
        (used for calibration); otherwise attractiveness stays neutral (1.0)."""
        from catchment import Airport
        pick = {"catchment": self.catchment_airports, "calibration": self.calibration_airports,
                "cache": self.cache_airports}[which]
        objs = []
        for a in pick():
            objs.append(Airport(a.code, lat=a.lat, lon=a.lon,
                                attractiveness=(a.size_pull_m if with_size else 1.0)))
        return objs

    def resolve(self, attr: str, base_dir: str) -> Optional[str]:
        """Turn a relative cache/params/observed path into an absolute one, against base_dir."""
        val = getattr(self, attr)
        if not val:
            return None
        return val if os.path.isabs(val) else os.path.join(base_dir, val)

    def resolve_existing(self, attr: str, base_dir: str, extra_dirs: Optional[List[str]] = None,
                         default_name: Optional[str] = None) -> Optional[str]:
        """Find an existing data file (cache / params / observed) for the case. A case can sit in
        a cases/ folder while its data files live beside the app modules, so look in base_dir
        first, then the extra dirs (e.g. the app directory). Falls back to base_dir/<name> for a
        not-yet-written output path."""
        val = getattr(self, attr) or default_name
        if not val:
            return None
        if os.path.isabs(val):
            return val
        for d in [base_dir] + (extra_dirs or []):
            cand = os.path.join(d, val)
            if os.path.exists(cand):
                return cand
        return os.path.join(base_dir, val)

    # ----------------------------------------------------------------- (de)serialise
    def to_dict(self) -> dict:
        d = asdict(self)
        d["centre"] = list(self.centre)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "RouteCase":
        d = dict(d)
        d["centre"] = tuple(d.get("centre", (0.0, 0.0)))
        d["airports"] = [CandidateAirport(**a) if isinstance(a, dict) else CandidateAirport(*a)
                         for a in d.get("airports", [])]
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path_or_id: str, search_dirs: Optional[List[str]] = None) -> "RouteCase":
        """Load a case from a JSON path, or by id from a cases/ folder. Returns the case and
        remembers nothing global - the caller resolves relative paths via .resolve(base_dir)."""
        path = _find_case_file(path_or_id, search_dirs)
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    @classmethod
    def load_with_dir(cls, path_or_id: str, search_dirs: Optional[List[str]] = None):
        path = _find_case_file(path_or_id, search_dirs)
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f)), os.path.dirname(os.path.abspath(path))


def _find_case_file(path_or_id: str, search_dirs: Optional[List[str]]) -> str:
    if os.path.isfile(path_or_id):
        return path_or_id
    here = os.path.dirname(os.path.abspath(__file__))
    dirs = (search_dirs or []) + [os.path.join(here, "cases"), here, os.getcwd()]
    stem = path_or_id if path_or_id.endswith(".json") else path_or_id + ".json"
    for d in dirs:
        cand = os.path.join(d, stem)
        if os.path.isfile(cand):
            return cand
    raise FileNotFoundError(
        f"route case '{path_or_id}' not found (looked for {stem} in: {', '.join(dirs)})")


# --------------------------------------------------------------------- built-in factory
def genoa_nyc() -> RouteCase:
    """The validated Genoa-New York case, as a RouteCase. This reproduces exactly what the
    hard-coded genoa_nyc.py / calibrate_genoa.py / build_genoa_cache.py used, so the general
    path can be checked against the original numbers."""
    return RouteCase(
        case_id="genoa_nyc",
        title="Genoa - New York",
        home="GOA",
        centre=(44.4133, 8.8375),
        radius_km=220.0,
        countries=["IT", "FR"],
        min_pop=5000.0,
        airports=[
            CandidateAirport("GOA", 44.4133, 8.8375, 1.2, "Genoa"),
            CandidateAirport("MXP", 45.6306, 8.7281, 28.5, "Milan MXP"),
            CandidateAirport("LIN", 45.4451, 9.2767, 9.3, "Milan Linate"),
            CandidateAirport("BGY", 45.6739, 9.7042, 17.0, "Bergamo"),
            CandidateAirport("TRN", 45.2008, 7.6497, 4.5, "Turin"),
            CandidateAirport("BLQ", 44.5354, 11.2887, 9.9, "Bologna"),
            # Nice: a cross-border competitor for western Liguria. Kept in the drive-time cache
            # but OUT of the Italian-origin Sabre calibration target and out of catchment scoring,
            # because raw drive time overstates Italian cross-border use without a border penalty.
            CandidateAirport("NCE", 43.6584, 7.2159, 14.0, "Nice", calibrate=False, cache_only=True),
        ],
        dest_name="New York",
        dest_airports=["JFK", "EWR", "LGA"],
        primary_dest="JFK",
        poo_country="IT",
        observed_cache="genoa_nyc_observed.json",
        aircraft="A21X",
        sector_nm=3500.0,
        block_min=540.0,
        airspace={"Italy": 0.10, "France": 0.05, "US": 0.05},
        airline_type="LCC",
        aircraft_age=2,
        capture=0.30,             # start-up capture (proven seasonal case); 0.65 over-reached to a daily. UNFIRMED pending the SJC outturn back-test.
        frequency=7,
        econ_share=0.80,          # 2024 Sabre: premium share 20% (business 15.8% + first 1.9% + prem coach 2.3%)
        bus_fare_ow=1400.0,       # entrant single-aisle business yield (2024 mkt J $2,381 OW; entrant prices below)
        premium_fare_ow=1800.0,   # richer business product (upper sensitivity)
        econ_fare_ow=345.0,       # entrant economy yield, below the $509 mkt average to attract leaked traffic
        fuel_price_usd_kg=0.90,   # through-cycle planning jet fuel (model default 0.68 too low for 2026)
        seasonality_profile=[0.527, 0.448, 0.701, 1.173, 1.128, 1.264, 1.381, 1.637, 1.260, 1.047, 0.689, 0.747],
        fare_basis="ow",          # real Italy-NYC monthly profile, Sabre MI Mar2025-Feb2026 (Aug/Feb 3.65x)
        # NOTE: natural_override is available to floor demand at the residence (POS) level, but for
        # the proven method we leave it off and use the calibrated catchment with a START-UP capture
        # of 0.30 (not 0.65). POS shows current Genoa-area NYC ~10k; the apportionment's larger figure
        # is current + induced demand, and how much a nonstop induces is the open question the SJC
        # outturn back-test must settle before this capture is firmed.
        plan_lf=0.875,
        stimulation=1.15,
        incentive_waiver_pct=0.50,
        incentive_support_per_turn=1500.0,
        drive_cache="genoa_drive.json",
        params_file="genoa_catchment_params.json",
    )


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Inspect or export a route case.")
    ap.add_argument("case", nargs="?", default="genoa_nyc", help="case id or JSON path")
    ap.add_argument("--export", default=None, help="write the case to this JSON path")
    a = ap.parse_args()
    try:
        rc = RouteCase.load(a.case)
    except FileNotFoundError:
        if a.case == "genoa_nyc":
            rc = genoa_nyc()
        else:
            raise
    print(f"{rc.case_id}: {rc.title}  home {rc.home}  dest {rc.dest_name} {rc.dest_airports}")
    print(f"  catchment airports: {rc.airport_codes('catchment')}")
    print(f"  calibration target: {rc.airport_codes('calibration')}")
    print(f"  aircraft {rc.aircraft}  sector {rc.sector_nm:.0f}nm  block {rc.block_min:.0f}min")
    if a.export:
        rc.save(a.export)
        print(f"exported to {a.export}")
