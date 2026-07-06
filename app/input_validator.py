#!/usr/bin/env python3
"""
Avia Solutions  Input Validation & Configuration Layer (Chat 14)
==================================================================
Validates user inputs and builds a RouteConfig for the QSI pipeline.

This is the programmatic equivalent of the "cover page" from the original
workbook specification. It sits between user input (whether from a web form,
Excel template, or CLI) and the pipeline, ensuring:

    1. All required fields are present
    2. IATA codes are valid
    3. Numeric parameters are within reasonable bounds
    4. Mode-specific fields are provided (Business Case targets)
    5. Sensible defaults are applied where appropriate
    6. Helpful error messages guide the user to fix issues

The validated output is a RouteConfig ready for the pipeline.

Validation Target: BA LHR-SJC regression must still pass through this layer.

Dependencies:
    - providers.py (Chat 12)
    - route_config.py (Chat 12)
    - calibration_model.py (Chat 13)
"""

from config import REFERENCE_CASE_DIR
import os
import math
from dataclasses import dataclass, field
from datetime import time as dtime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


# ============================================================================
# ENUMS  Valid dropdown values
# ============================================================================

class RunMode(Enum):
    """Pipeline operating mode."""
    FORECAST = 'forecast'
    BUSINESS_CASE = 'business_case'


class RouteType(Enum):
    """Route type classification."""
    LCC_P2P = 'lcc_p2p'
    HUB_FEED = 'hub_feed'
    LONG_HAUL = 'long_haul'
    CHARTER_LEISURE = 'charter_leisure'
    MIXED = 'mixed'


class CarrierType(Enum):
    """Carrier type classification."""
    ULTRA_LCC = 'ultra_lcc'
    LCC = 'lcc'
    HYBRID = 'hybrid'
    FULL_SERVICE = 'full_service'
    CHARTER = 'charter'


class MarketMaturity(Enum):
    """Market maturity classification."""
    NEW_ROUTE = 'new_route'
    EXISTING_UNDERSERVED = 'existing_underserved'
    EXISTING_COMPETITIVE = 'existing_competitive'
    MATURE = 'mature'


class DemandDriver(Enum):
    """Primary demand driver."""
    BUSINESS = 'business'
    LEISURE = 'leisure'
    VFR_DIASPORA = 'vfr_diaspora'
    MIXED = 'mixed'


class SeasonalProfile(Enum):
    """Seasonal demand profile."""
    YEAR_ROUND = 'year_round'
    SUMMER_PEAK = 'summer_peak'
    WINTER_PEAK = 'winter_peak'
    DUAL_PEAK = 'dual_peak'


class IndirectCompetition(Enum):
    """Quality of indirect competition."""
    NONE = 'none'
    POOR = 'poor'
    REASONABLE = 'reasonable'
    STRONG = 'strong'


class SurfaceCompetition(Enum):
    """Surface competition classification."""
    NONE = 'none'
    RAIL_UNDER_3HRS = 'rail_under_3hrs'
    RAIL_UNDER_5HRS = 'rail_under_5hrs'
    ROAD_SIGNIFICANT = 'road_significant'


# ============================================================================
# AIRCRAFT DATABASE
# ============================================================================

@dataclass
class AircraftSpec:
    """Aircraft type specification."""
    code: str
    name: str
    typical_seats: int      # Typical economy-heavy config
    max_seats: int          # Max single-class
    min_seats: int          # Premium-heavy config
    range_nm: int           # Max range in nautical miles
    category: str           # 'narrowbody' | 'widebody' | 'regional'


# Common aircraft types used in route assessments
AIRCRAFT_DB = {
    # Narrowbody
    '319': AircraftSpec('319', 'Airbus A319', 140, 156, 110, 3700, 'narrowbody'),
    '320': AircraftSpec('320', 'Airbus A320', 170, 186, 140, 3300, 'narrowbody'),
    '20N': AircraftSpec('20N', 'Airbus A320neo', 170, 194, 140, 3500, 'narrowbody'),
    '321': AircraftSpec('321', 'Airbus A321', 200, 236, 170, 3200, 'narrowbody'),
    '21N': AircraftSpec('21N', 'Airbus A321neo', 200, 244, 170, 4000, 'narrowbody'),
    '21X': AircraftSpec('21X', 'Airbus A321XLR', 200, 244, 170, 4700, 'narrowbody'),
    '737': AircraftSpec('737', 'Boeing 737-800', 175, 189, 140, 2935, 'narrowbody'),
    '738': AircraftSpec('738', 'Boeing 737-800', 175, 189, 140, 2935, 'narrowbody'),
    '7M8': AircraftSpec('7M8', 'Boeing 737 MAX 8', 178, 200, 150, 3550, 'narrowbody'),
    '7M9': AircraftSpec('7M9', 'Boeing 737 MAX 9', 193, 220, 170, 3550, 'narrowbody'),
    # Widebody
    '332': AircraftSpec('332', 'Airbus A330-200', 260, 406, 210, 7250, 'widebody'),
    '333': AircraftSpec('333', 'Airbus A330-300', 290, 440, 240, 6350, 'widebody'),
    '338': AircraftSpec('338', 'Airbus A330-800neo', 260, 406, 220, 8150, 'widebody'),
    '339': AircraftSpec('339', 'Airbus A330-900neo', 287, 440, 240, 7200, 'widebody'),
    '359': AircraftSpec('359', 'Airbus A350-900', 300, 440, 250, 8100, 'widebody'),
    '35K': AircraftSpec('35K', 'Airbus A350-1000', 350, 480, 300, 8700, 'widebody'),
    '388': AircraftSpec('388', 'Airbus A380-800', 500, 853, 380, 8000, 'widebody'),
    '764': AircraftSpec('764', 'Boeing 767-400', 245, 375, 200, 5625, 'widebody'),
    '772': AircraftSpec('772', 'Boeing 777-200', 280, 440, 230, 5240, 'widebody'),
    '77W': AircraftSpec('77W', 'Boeing 777-300ER', 350, 550, 280, 7370, 'widebody'),
    '778': AircraftSpec('778', 'Boeing 777-8', 350, 440, 280, 8730, 'widebody'),
    '779': AircraftSpec('779', 'Boeing 777-9', 400, 426, 350, 7285, 'widebody'),
    '788': AircraftSpec('788', 'Boeing 787-8', 240, 381, 200, 7355, 'widebody'),
    '789': AircraftSpec('789', 'Boeing 787-9', 280, 420, 230, 7635, 'widebody'),
    '78J': AircraftSpec('78J', 'Boeing 787-10', 318, 440, 270, 6430, 'widebody'),
    '787': AircraftSpec('787', 'Boeing 787-800', 214, 381, 180, 7355, 'widebody'),
    # Regional
    'E75': AircraftSpec('E75', 'Embraer E175', 76, 88, 60, 2000, 'regional'),
    'E90': AircraftSpec('E90', 'Embraer E190', 100, 114, 80, 2450, 'regional'),
    'E95': AircraftSpec('E95', 'Embraer E195', 120, 136, 100, 2600, 'regional'),
    'E2E': AircraftSpec('E2E', 'Embraer E195-E2', 132, 146, 108, 2600, 'regional'),
}


# ============================================================================
# DISTANCE CALCULATION
# ============================================================================

def haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great circle distance in nautical miles."""
    R_NM = 3440.065
    lat1, lon1, lat2, lon2 = [math.radians(x) for x in [lat1, lon1, lat2, lon2]]
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 2 * R_NM * math.asin(min(1.0, math.sqrt(a)))


# ============================================================================
# VALIDATION RESULT
# ============================================================================

@dataclass
class ValidationIssue:
    """Single validation issue."""
    field: str
    severity: str  # 'error' | 'warning'
    message: str
    suggestion: str = ''


@dataclass
class ValidationResult:
    """Complete validation result."""
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    applied_defaults: Dict[str, Any] = field(default_factory=dict)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == 'error']

    def summary(self) -> str:
        lines = []
        if self.valid:
            lines.append(" VALIDATION PASSED")
        else:
            lines.append(" VALIDATION FAILED")
        
        for e in self.errors:
            lines.append(f"  ERROR   [{e.field}]: {e.message}")
            if e.suggestion:
                lines.append(f"           {e.suggestion}")
        
        for w in self.warnings:
            lines.append(f"  WARNING [{w.field}]: {w.message}")
            if w.suggestion:
                lines.append(f"           {w.suggestion}")
        
        if self.applied_defaults:
            lines.append("  Defaults applied:")
            for k, v in self.applied_defaults.items():
                lines.append(f"    {k} = {v}")
        
        return '\n'.join(lines)


# ============================================================================
# DEFAULT PARAMETER TABLES
# ============================================================================

# QSI coefficient defaults by carrier type
QSI_DEFAULTS_BY_CARRIER = {
    CarrierType.FULL_SERVICE: {
        'online_coeff': 1.0,
        'alliance_coeff': 0.615,
        'interline_coeff': 0.25,
        'et_decay_factor': 0.8,
        'et_decay_interval': 0.1,
    },
    CarrierType.LCC: {
        'online_coeff': 1.0,
        'alliance_coeff': 0.0,    # LCCs don't have alliance partners
        'interline_coeff': 0.0,   # No interline agreements
        'et_decay_factor': 0.8,
        'et_decay_interval': 0.1,
    },
    CarrierType.ULTRA_LCC: {
        'online_coeff': 1.0,
        'alliance_coeff': 0.0,
        'interline_coeff': 0.0,
        'et_decay_factor': 0.8,
        'et_decay_interval': 0.1,
    },
    CarrierType.HYBRID: {
        'online_coeff': 1.0,
        'alliance_coeff': 0.3,    # Some have loose alliances
        'interline_coeff': 0.1,
        'et_decay_factor': 0.8,
        'et_decay_interval': 0.1,
    },
    CarrierType.CHARTER: {
        'online_coeff': 1.0,
        'alliance_coeff': 0.0,
        'interline_coeff': 0.0,
        'et_decay_factor': 0.8,
        'et_decay_interval': 0.1,
    },
}

# Stimulation factor defaults by carrier type and market maturity
# Key insight from John: LCCs get higher stimulation (they create new demand),
# legacy carriers get lower (they capture existing demand)
STIMULATION_DEFAULTS = {
    (CarrierType.FULL_SERVICE, MarketMaturity.NEW_ROUTE): {'business': 1.15, 'leisure': 1.10},
    (CarrierType.FULL_SERVICE, MarketMaturity.EXISTING_UNDERSERVED): {'business': 1.10, 'leisure': 1.05},
    (CarrierType.FULL_SERVICE, MarketMaturity.EXISTING_COMPETITIVE): {'business': 1.05, 'leisure': 1.02},
    (CarrierType.FULL_SERVICE, MarketMaturity.MATURE): {'business': 1.02, 'leisure': 1.00},
    (CarrierType.LCC, MarketMaturity.NEW_ROUTE): {'business': 1.25, 'leisure': 1.40},
    (CarrierType.LCC, MarketMaturity.EXISTING_UNDERSERVED): {'business': 1.15, 'leisure': 1.30},
    (CarrierType.LCC, MarketMaturity.EXISTING_COMPETITIVE): {'business': 1.05, 'leisure': 1.15},
    (CarrierType.LCC, MarketMaturity.MATURE): {'business': 1.00, 'leisure': 1.05},
    (CarrierType.ULTRA_LCC, MarketMaturity.NEW_ROUTE): {'business': 1.20, 'leisure': 1.45},
    (CarrierType.ULTRA_LCC, MarketMaturity.EXISTING_UNDERSERVED): {'business': 1.10, 'leisure': 1.35},
    (CarrierType.ULTRA_LCC, MarketMaturity.EXISTING_COMPETITIVE): {'business': 1.00, 'leisure': 1.20},
    (CarrierType.ULTRA_LCC, MarketMaturity.MATURE): {'business': 1.00, 'leisure': 1.10},
    (CarrierType.HYBRID, MarketMaturity.NEW_ROUTE): {'business': 1.15, 'leisure': 1.25},
    (CarrierType.HYBRID, MarketMaturity.EXISTING_UNDERSERVED): {'business': 1.10, 'leisure': 1.15},
    (CarrierType.HYBRID, MarketMaturity.EXISTING_COMPETITIVE): {'business': 1.05, 'leisure': 1.08},
    (CarrierType.HYBRID, MarketMaturity.MATURE): {'business': 1.02, 'leisure': 1.02},
    (CarrierType.CHARTER, MarketMaturity.NEW_ROUTE): {'business': 1.00, 'leisure': 1.30},
    (CarrierType.CHARTER, MarketMaturity.EXISTING_UNDERSERVED): {'business': 1.00, 'leisure': 1.20},
    (CarrierType.CHARTER, MarketMaturity.EXISTING_COMPETITIVE): {'business': 1.00, 'leisure': 1.10},
    (CarrierType.CHARTER, MarketMaturity.MATURE): {'business': 1.00, 'leisure': 1.00},
}

# Growth rate defaults by market maturity
GROWTH_DEFAULTS = {
    MarketMaturity.NEW_ROUTE: 0.05,
    MarketMaturity.EXISTING_UNDERSERVED: 0.04,
    MarketMaturity.EXISTING_COMPETITIVE: 0.03,
    MarketMaturity.MATURE: 0.025,
}

# Reasonableness bounds  outside these triggers warnings, far outside triggers errors
BOUNDS = {
    'frequency': {'min': 1, 'max': 28, 'warn_max': 21, 'desc': 'flights per week'},
    'seats': {'min': 50, 'max': 615, 'warn_min': 70, 'warn_max': 500, 'desc': 'seats per flight'},
    'growth_rate': {'min': -0.05, 'max': 0.15, 'warn_min': 0.0, 'warn_max': 0.08, 'desc': 'annual growth rate'},
    'stimulation': {'min': 0.80, 'max': 1.60, 'warn_min': 0.90, 'warn_max': 1.45, 'desc': 'stimulation factor'},
    'capture_rate': {'min': 0.0, 'max': 1.0, 'warn_max': 0.70, 'desc': 'P2P capture rate'},
    'qsi_ceiling': {'min': 0.1, 'max': 1.0, 'desc': 'QSI ceiling'},
    'load_factor_target': {'min': 0.50, 'max': 0.95, 'warn_min': 0.60, 'warn_max': 0.92, 'desc': 'target load factor'},
    'online_coeff': {'min': 0.5, 'max': 1.5, 'desc': 'online connection coefficient'},
    'alliance_coeff': {'min': 0.0, 'max': 1.0, 'desc': 'alliance connection coefficient'},
    'interline_coeff': {'min': 0.0, 'max': 0.5, 'desc': 'interline connection coefficient'},
}


# ============================================================================
# INPUT SCHEMA
# ============================================================================

@dataclass
class RouteInput:
    """
    Raw user input for a route assessment.
    
    This is what comes from the web form / Excel template / CLI.
    All fields are Optional  validation determines what's missing.
    """
    # Section 1: Mode
    mode: str = 'forecast'  # 'forecast' | 'business_case'
    
    # Business Case targets (only if mode = business_case)
    target_load_factor_y1: Optional[float] = None
    target_load_factor_mature: Optional[float] = None
    target_p2p_split: Optional[float] = None    # P2P as fraction of total
    target_cnx_balance: Optional[float] = None   # Home hub cnx / total cnx
    min_frequency: Optional[int] = None
    
    # Section 2: Route Characteristics
    origin: str = ''            # IATA airport code
    destination: str = ''       # IATA airport code
    route_type: str = 'long_haul'
    carrier_type: str = 'full_service'
    carrier_code: str = ''      # 2-letter IATA airline code
    carrier_name: str = ''
    market_maturity: str = 'new_route'
    
    # Section 3: Demand Profile
    demand_driver: str = 'mixed'
    seasonal_profile: str = 'year_round'
    business_share: Optional[float] = None   # 0-1, fraction that is business
    
    # Section 4: Service Parameters
    frequency: int = 7
    aircraft_type: str = ''      # IATA aircraft code
    seats: Optional[int] = None  # Override aircraft default
    dep_time_outbound: str = ''  # HH:MM format
    dep_time_return: str = ''    # HH:MM format
    flight_time_hrs: Optional[float] = None
    
    # Section 5: Competitive Context
    existing_direct: bool = False
    existing_direct_carrier: str = ''
    existing_direct_frequency: int = 0
    indirect_competition: str = 'reasonable'
    surface_competition: str = 'none'
    
    # Section 6: QSI Overrides (expert adjustments)
    qsi_ceiling: Optional[float] = None
    qsi_adjustment: Optional[float] = None
    online_coeff: Optional[float] = None
    alliance_coeff: Optional[float] = None
    interline_coeff: Optional[float] = None
    et_decay_factor: Optional[float] = None
    et_decay_interval: Optional[float] = None
    
    # Section 7: Data file paths
    home_qsi_file: str = ''
    dest_qsi_file: str = ''
    forecast_file: str = ''
    
    # Growth overrides
    home_growth: Optional[float] = None
    dest_growth: Optional[float] = None
    stimulation_business: Optional[float] = None
    stimulation_leisure: Optional[float] = None


# ============================================================================
# AIRPORT LOOKUP (lightweight)
# ============================================================================

# Core airports we encounter in route assessments  loaded from project data
# This is a lightweight lookup; the full database is in Airport_Database.xlsx
KNOWN_AIRPORTS = {
    # Major hubs
    'LHR': ('LON', 'London Heathrow', 51.4706, -0.4619),
    'LGW': ('LON', 'London Gatwick', 51.1537, -0.1821),
    'STN': ('LON', 'London Stansted', 51.8850, 0.2389),
    'LTN': ('LON', 'London Luton', 51.8747, -0.3683),
    'SJC': ('SJC', 'San Jose', 37.3626, -121.929),
    'SFO': ('SFO', 'San Francisco', 37.6213, -122.379),
    'OAK': ('OAK', 'Oakland', 37.7213, -122.221),
    'JFK': ('NYC', 'New York JFK', 40.6399, -73.7787),
    'EWR': ('NYC', 'Newark', 40.6925, -74.1687),
    'LAX': ('LAX', 'Los Angeles', 33.9425, -118.408),
    'ORD': ('CHI', 'Chicago O\'Hare', 41.9786, -87.9048),
    'ATL': ('ATL', 'Atlanta', 33.6367, -84.4281),
    'DFW': ('DFW', 'Dallas-Fort Worth', 32.8968, -97.038),
    'IAD': ('WAS', 'Washington Dulles', 38.9445, -77.4558),
    'MIA': ('MIA', 'Miami', 25.7932, -80.2906),
    'BOS': ('BOS', 'Boston', 42.3643, -71.0052),
    'SEA': ('SEA', 'Seattle', 47.4490, -122.309),
    'DEN': ('DEN', 'Denver', 39.8561, -104.674),
    'TPA': ('TPA', 'Tampa', 27.9755, -82.5332),
    'AMS': ('AMS', 'Amsterdam Schiphol', 52.3086, 4.7639),
    'CDG': ('PAR', 'Paris CDG', 49.0128, 2.5500),
    'FRA': ('FRA', 'Frankfurt', 50.0333, 8.5706),
    'MUC': ('MUC', 'Munich', 48.3538, 11.7861),
    'FCO': ('ROM', 'Rome Fiumicino', 41.8003, 12.2389),
    'MAD': ('MAD', 'Madrid', 40.4936, -3.5668),
    'BCN': ('BCN', 'Barcelona', 41.2971, 2.0785),
    'IST': ('IST', 'Istanbul', 41.2753, 28.7519),
    'DXB': ('DXB', 'Dubai', 25.2528, 55.3644),
    'DOH': ('DOH', 'Doha', 25.2731, 51.6081),
    'AUH': ('AUH', 'Abu Dhabi', 24.4430, 54.6511),
    'SIN': ('SIN', 'Singapore Changi', 1.3502, 103.994),
    'HKG': ('HKG', 'Hong Kong', 22.3089, 113.915),
    'NRT': ('TYO', 'Tokyo Narita', 35.7647, 140.386),
    'HND': ('TYO', 'Tokyo Haneda', 35.5523, 139.780),
    'ICN': ('SEL', 'Seoul Incheon', 37.4692, 126.451),
    'PEK': ('BJS', 'Beijing Capital', 40.0801, 116.585),
    'PVG': ('SHA', 'Shanghai Pudong', 31.1434, 121.805),
    'BKK': ('BKK', 'Bangkok Suvarnabhumi', 13.6811, 100.747),
    'DEL': ('DEL', 'Delhi', 28.5562, 77.1000),
    'BOM': ('BOM', 'Mumbai', 19.0887, 72.8679),
    'JNB': ('JNB', 'Johannesburg', -26.1392, 28.2460),
    'TPE': ('TPE', 'Taipei Taoyuan', 25.0777, 121.233),
    'SYD': ('SYD', 'Sydney', -33.9461, 151.177),
    'MEL': ('MEL', 'Melbourne', -37.6733, 144.843),
    'YYZ': ('YTO', 'Toronto Pearson', 43.6772, -79.6306),
    'YVR': ('YVR', 'Vancouver', 49.1947, -123.184),
    'GRU': ('SAO', 'Sao Paulo Guarulhos', -23.4356, -46.4731),
    'BOG': ('BOG', 'Bogota', 4.7016, -74.1469),
    'KEF': ('REK', 'Reykjavik Keflavik', 63.9850, -22.6056),
    'CPH': ('CPH', 'Copenhagen', 55.6180, 12.6508),
    'OSL': ('OSL', 'Oslo Gardermoen', 60.1939, 11.1004),
    'ARN': ('STO', 'Stockholm Arlanda', 59.6519, 17.9186),
    'HEL': ('HEL', 'Helsinki', 60.3172, 24.9633),
    'MAN': ('MAN', 'Manchester', 53.3537, -2.2750),
    'EDI': ('EDI', 'Edinburgh', 55.9500, -3.3725),
    'DUB': ('DUB', 'Dublin', 53.4213, -6.2701),
    'NOC': ('NOC', 'Ireland West Knock', 53.9103, -8.8186),
    'ZRH': ('ZRH', 'Zurich', 47.4647, 8.5492),
    'VIE': ('VIE', 'Vienna', 48.1103, 16.5697),
    'LIS': ('LIS', 'Lisbon', 38.7813, -9.1359),
    'WAW': ('WAW', 'Warsaw', 52.1657, 20.9671),
    'PRG': ('PRG', 'Prague', 50.1008, 14.2600),
    'BUD': ('BUD', 'Budapest', 47.4298, 19.2611),
    'SOF': ('SOF', 'Sofia', 42.6952, 23.4063),
    'CAI': ('CAI', 'Cairo', 30.1219, 31.4056),
    'ADD': ('ADD', 'Addis Ababa', 8.9779, 38.7994),
    'NBO': ('NBO', 'Nairobi', -1.3192, 36.9278),
    'CMB': ('CMB', 'Colombo', 7.1808, 79.8844),
    'KUL': ('KUL', 'Kuala Lumpur', 2.7456, 101.710),
    'CGK': ('JKT', 'Jakarta', -6.1256, 106.656),
    'MNL': ('MNL', 'Manila', 14.5086, 121.020),
    'CAN': ('CAN', 'Guangzhou', 23.3925, 113.299),
}


def lookup_airport(code: str) -> Optional[Tuple[str, str, float, float]]:
    """Look up airport: returns (city_code, name, lat, lon) or None."""
    code = code.upper().strip()
    if code in KNOWN_AIRPORTS:
        return KNOWN_AIRPORTS[code]
    return None


def compute_distance(origin: str, destination: str) -> Optional[float]:
    """Compute great circle distance in nautical miles between two IATA codes."""
    o = lookup_airport(origin)
    d = lookup_airport(destination)
    if o and d:
        return haversine_nm(o[2], o[3], d[2], d[3])
    return None


# ============================================================================
# DISTANCE BAND CLASSIFICATION
# ============================================================================

def classify_distance_band(distance_nm: float) -> str:
    """Classify route by distance."""
    if distance_nm < 500:
        return 'domestic_short'
    elif distance_nm < 1500:
        return 'short_haul'
    elif distance_nm < 3000:
        return 'medium_haul'
    elif distance_nm < 5000:
        return 'long_haul'
    else:
        return 'ultra_long_haul'


# ============================================================================
# INPUT VALIDATOR
# ============================================================================

class InputValidator:
    """
    Validates a RouteInput and produces a validated RouteConfig.
    
    Usage:
        validator = InputValidator()
        result = validator.validate(route_input)
        if result.valid:
            config = validator.build_config(route_input)
        else:
            print(result.summary())
    """

    def __init__(self, project_dir: str = None):
        self.project_dir = project_dir or str(REFERENCE_CASE_DIR)

    def validate(self, inp: RouteInput) -> ValidationResult:
        """Run all validation checks on the input."""
        issues = []
        warnings = []
        defaults = {}

        #  Section 1: Mode 
        self._validate_mode(inp, issues, warnings)

        #  Section 2: Route Characteristics 
        self._validate_route(inp, issues, warnings, defaults)

        #  Section 4: Service Parameters 
        self._validate_service(inp, issues, warnings, defaults)

        #  Section 5: Competitive Context 
        self._validate_competition(inp, issues, warnings)

        #  Section 6: QSI Overrides 
        self._validate_qsi_params(inp, issues, warnings, defaults)

        #  Section 7: Data Files 
        self._validate_files(inp, issues, warnings)

        #  Cross-field validation 
        self._cross_validate(inp, issues, warnings)

        has_errors = any(i.severity == 'error' for i in issues)
        result = ValidationResult(
            valid=not has_errors,
            issues=issues,
            warnings=[i for i in issues if i.severity == 'warning'],
            applied_defaults=defaults,
        )
        return result

    def _validate_mode(self, inp, issues, warnings):
        """Validate operating mode and business case targets."""
        try:
            RunMode(inp.mode)
        except ValueError:
            issues.append(ValidationIssue(
                'mode', 'error',
                f"Invalid mode '{inp.mode}'",
                "Must be 'forecast' or 'business_case'"
            ))
            return

        if inp.mode == 'business_case':
            if inp.target_load_factor_y1 is None:
                issues.append(ValidationIssue(
                    'target_load_factor_y1', 'error',
                    'Business Case mode requires Year 1 target load factor',
                    'Typical range: 0.60-0.80 for Year 1'
                ))
            elif not (0.3 <= inp.target_load_factor_y1 <= 0.98):
                issues.append(ValidationIssue(
                    'target_load_factor_y1', 'error',
                    f'Target LF {inp.target_load_factor_y1:.0%} is outside plausible range',
                    'Must be between 30% and 98%'
                ))
            
            if inp.target_load_factor_mature is not None:
                if not (0.5 <= inp.target_load_factor_mature <= 0.98):
                    issues.append(ValidationIssue(
                        'target_load_factor_mature', 'warning',
                        f'Mature LF target {inp.target_load_factor_mature:.0%} is unusual',
                        'Typical mature load factors are 75%-92%'
                    ))

    def _validate_route(self, inp, issues, warnings, defaults):
        """Validate route characteristics."""
        # Origin
        if not inp.origin:
            issues.append(ValidationIssue(
                'origin', 'error', 'Origin airport is required',
                'Enter a 3-letter IATA code (e.g., LHR, SJC, AMS)'
            ))
        elif len(inp.origin) != 3 or not inp.origin.isalpha():
            issues.append(ValidationIssue(
                'origin', 'error',
                f"'{inp.origin}' is not a valid IATA airport code",
                'Must be exactly 3 letters'
            ))
        else:
            o = lookup_airport(inp.origin)
            if not o:
                issues.append(ValidationIssue(
                    'origin', 'warning',
                    f"'{inp.origin}' not found in airport database",
                    'Code accepted but distance calculations and city mapping unavailable. '
                    'You may need to provide city_code manually.'
                ))

        # Destination
        if not inp.destination:
            issues.append(ValidationIssue(
                'destination', 'error', 'Destination airport is required',
                'Enter a 3-letter IATA code'
            ))
        elif len(inp.destination) != 3 or not inp.destination.isalpha():
            issues.append(ValidationIssue(
                'destination', 'error',
                f"'{inp.destination}' is not a valid IATA airport code",
                'Must be exactly 3 letters'
            ))
        elif inp.origin and inp.origin == inp.destination:
            issues.append(ValidationIssue(
                'destination', 'error',
                'Origin and destination cannot be the same airport'
            ))
        else:
            d = lookup_airport(inp.destination)
            if not d:
                issues.append(ValidationIssue(
                    'destination', 'warning',
                    f"'{inp.destination}' not found in airport database",
                    'Code accepted but distance calculations unavailable.'
                ))

        # Distance-based checks
        dist = compute_distance(inp.origin, inp.destination) if inp.origin and inp.destination else None
        if dist:
            band = classify_distance_band(dist)
            # Check aircraft range vs distance
            if inp.aircraft_type and inp.aircraft_type.upper() in AIRCRAFT_DB:
                ac = AIRCRAFT_DB[inp.aircraft_type.upper()]
                if dist > ac.range_nm * 1.05:  # 5% margin
                    issues.append(ValidationIssue(
                        'aircraft_type', 'error',
                        f'{ac.name} range ({ac.range_nm}nm) insufficient for '
                        f'{inp.origin}-{inp.destination} ({dist:.0f}nm)',
                        'Select an aircraft with longer range'
                    ))
            
            # Route type vs distance sanity
            if inp.route_type == 'lcc_p2p' and dist > 3000:
                issues.append(ValidationIssue(
                    'route_type', 'warning',
                    f'LCC P2P route type unusual for {dist:.0f}nm distance',
                    'Consider long_haul or mixed for routes over 3,000nm'
                ))

        # Validate enums
        try:
            RouteType(inp.route_type)
        except ValueError:
            issues.append(ValidationIssue(
                'route_type', 'error',
                f"Invalid route type '{inp.route_type}'",
                f"Valid options: {', '.join(r.value for r in RouteType)}"
            ))

        try:
            CarrierType(inp.carrier_type)
        except ValueError:
            issues.append(ValidationIssue(
                'carrier_type', 'error',
                f"Invalid carrier type '{inp.carrier_type}'",
                f"Valid options: {', '.join(c.value for c in CarrierType)}"
            ))

        try:
            MarketMaturity(inp.market_maturity)
        except ValueError:
            issues.append(ValidationIssue(
                'market_maturity', 'error',
                f"Invalid market maturity '{inp.market_maturity}'",
                f"Valid options: {', '.join(m.value for m in MarketMaturity)}"
            ))

    def _validate_service(self, inp, issues, warnings, defaults):
        """Validate service parameters."""
        # Frequency
        self._check_bounds('frequency', inp.frequency, issues, warnings)

        # Aircraft
        if inp.aircraft_type:
            ac_code = inp.aircraft_type.upper()
            if ac_code in AIRCRAFT_DB:
                ac = AIRCRAFT_DB[ac_code]
                if inp.seats is None:
                    defaults['seats'] = ac.typical_seats
                elif inp.seats < ac.min_seats or inp.seats > ac.max_seats:
                    issues.append(ValidationIssue(
                        'seats', 'warning',
                        f'{inp.seats} seats unusual for {ac.name} '
                        f'(typical range: {ac.min_seats}-{ac.max_seats})',
                        f'Default would be {ac.typical_seats}'
                    ))
            else:
                issues.append(ValidationIssue(
                    'aircraft_type', 'warning',
                    f"Aircraft code '{inp.aircraft_type}' not in database",
                    'Seats must be specified manually'
                ))
                if inp.seats is None:
                    issues.append(ValidationIssue(
                        'seats', 'error',
                        'Seats required when aircraft type is not in database'
                    ))
        elif inp.seats is None:
            issues.append(ValidationIssue(
                'seats', 'error',
                'Either aircraft_type or seats must be specified'
            ))

        if inp.seats is not None:
            self._check_bounds('seats', inp.seats, issues, warnings)

        # Departure times
        if inp.dep_time_outbound:
            if not self._parse_time(inp.dep_time_outbound):
                issues.append(ValidationIssue(
                    'dep_time_outbound', 'error',
                    f"Invalid time format '{inp.dep_time_outbound}'",
                    'Use HH:MM format (e.g., 15:30)'
                ))

        if inp.dep_time_return:
            if not self._parse_time(inp.dep_time_return):
                issues.append(ValidationIssue(
                    'dep_time_return', 'error',
                    f"Invalid time format '{inp.dep_time_return}'",
                    'Use HH:MM format (e.g., 21:30)'
                ))

    def _validate_competition(self, inp, issues, warnings):
        """Validate competitive context."""
        try:
            IndirectCompetition(inp.indirect_competition)
        except ValueError:
            issues.append(ValidationIssue(
                'indirect_competition', 'error',
                f"Invalid indirect competition '{inp.indirect_competition}'",
                f"Valid: {', '.join(i.value for i in IndirectCompetition)}"
            ))

        try:
            SurfaceCompetition(inp.surface_competition)
        except ValueError:
            issues.append(ValidationIssue(
                'surface_competition', 'error',
                f"Invalid surface competition '{inp.surface_competition}'",
                f"Valid: {', '.join(s.value for s in SurfaceCompetition)}"
            ))

        if inp.existing_direct and inp.existing_direct_frequency == 0:
            issues.append(ValidationIssue(
                'existing_direct_frequency', 'warning',
                'Existing direct service flagged but frequency is 0',
                'Set the competitor frequency or set existing_direct=False'
            ))

    def _validate_qsi_params(self, inp, issues, warnings, defaults):
        """Validate QSI parameter overrides."""
        # Apply carrier-type defaults for any unset QSI parameters
        try:
            ct = CarrierType(inp.carrier_type)
        except ValueError:
            ct = CarrierType.FULL_SERVICE

        carrier_defaults = QSI_DEFAULTS_BY_CARRIER.get(ct, QSI_DEFAULTS_BY_CARRIER[CarrierType.FULL_SERVICE])

        for param in ['online_coeff', 'alliance_coeff', 'interline_coeff',
                       'et_decay_factor', 'et_decay_interval']:
            val = getattr(inp, param, None)
            if val is not None:
                if param in BOUNDS:
                    self._check_bounds(param, val, issues, warnings)
            else:
                defaults[param] = carrier_defaults[param]

        # QSI ceiling
        if inp.qsi_ceiling is not None:
            self._check_bounds('qsi_ceiling', inp.qsi_ceiling, issues, warnings)

    def _validate_files(self, inp, issues, warnings):
        """Validate data file paths exist."""
        for label, path in [
            ('home_qsi_file', inp.home_qsi_file),
            ('dest_qsi_file', inp.dest_qsi_file),
            ('forecast_file', inp.forecast_file),
        ]:
            if path:
                full = path if os.path.isabs(path) else os.path.join(self.project_dir, path)
                if not os.path.exists(full):
                    issues.append(ValidationIssue(
                        label, 'error',
                        f"File not found: {path}",
                        f"Check the file exists at {full}"
                    ))

    def _cross_validate(self, inp, issues, warnings):
        """Cross-field validation checks."""
        # Distance vs flight time
        dist = compute_distance(inp.origin, inp.destination) if inp.origin and inp.destination else None
        if dist and inp.flight_time_hrs:
            expected_speed = dist / inp.flight_time_hrs  # knots
            if expected_speed < 300:
                issues.append(ValidationIssue(
                    'flight_time_hrs', 'warning',
                    f'Flight time {inp.flight_time_hrs}h implies {expected_speed:.0f}kts '
                    f'for {dist:.0f}nm  unusually slow',
                    'Check flight time or route distance'
                ))
            elif expected_speed > 600:
                issues.append(ValidationIssue(
                    'flight_time_hrs', 'warning',
                    f'Flight time {inp.flight_time_hrs}h implies {expected_speed:.0f}kts '
                    f'for {dist:.0f}nm  unusually fast',
                    'Check flight time or route distance'
                ))

        # Carrier type vs route type sanity
        if inp.carrier_type in ('ultra_lcc', 'lcc') and inp.route_type == 'hub_feed':
            issues.append(ValidationIssue(
                'route_type', 'warning',
                f'{inp.carrier_type} carrier type with hub_feed route type is unusual',
                'LCCs typically operate P2P; consider lcc_p2p or mixed'
            ))

        # Load factor vs capacity sanity (Business Case mode)
        if inp.mode == 'business_case' and inp.target_load_factor_y1 and inp.target_load_factor_mature:
            if inp.target_load_factor_y1 > inp.target_load_factor_mature:
                issues.append(ValidationIssue(
                    'target_load_factor_y1', 'warning',
                    f'Year 1 LF ({inp.target_load_factor_y1:.0%}) exceeds mature LF '
                    f'({inp.target_load_factor_mature:.0%})',
                    'Year 1 is typically lower than mature; check targets'
                ))

    def _check_bounds(self, param: str, value, issues, warnings):
        """Check a numeric value against its defined bounds."""
        if param not in BOUNDS:
            return
        b = BOUNDS[param]
        if value < b['min']:
            issues.append(ValidationIssue(
                param, 'error',
                f"{param} = {value} below minimum {b['min']} ({b.get('desc', '')})"
            ))
        elif value > b['max']:
            issues.append(ValidationIssue(
                param, 'error',
                f"{param} = {value} above maximum {b['max']} ({b.get('desc', '')})"
            ))
        elif 'warn_min' in b and value < b['warn_min']:
            issues.append(ValidationIssue(
                param, 'warning',
                f"{param} = {value} is below typical range ({b.get('desc', '')})",
                f"Typical minimum: {b['warn_min']}"
            ))
        elif 'warn_max' in b and value > b['warn_max']:
            issues.append(ValidationIssue(
                param, 'warning',
                f"{param} = {value} is above typical range ({b.get('desc', '')})",
                f"Typical maximum: {b['warn_max']}"
            ))

    @staticmethod
    def _parse_time(time_str: str) -> Optional[dtime]:
        """Parse HH:MM to time object."""
        try:
            parts = time_str.strip().split(':')
            if len(parts) == 2:
                h, m = int(parts[0]), int(parts[1])
                if 0 <= h <= 23 and 0 <= m <= 59:
                    return dtime(h, m)
        except (ValueError, IndexError):
            pass
        return None

    # ================================================================
    # BUILD CONFIG  Produces RouteConfig from validated input
    # ================================================================

    def build_config(self, inp: RouteInput) -> 'RouteConfig':
        """
        Build a RouteConfig from validated input.
        
        MUST call validate() first and check result.valid == True.
        Applies defaults where user hasn't specified values.
        """
        from route_config import RouteConfig
        from providers import ExcelScheduleProvider, ExcelDemandProvider

        cfg = RouteConfig()

        # Route identity
        cfg.airline_code = inp.carrier_code.upper() if inp.carrier_code else ''
        cfg.airline_name = inp.carrier_name
        cfg.home_airport_code = inp.origin.upper()
        cfg.dest_airport_code = inp.destination.upper()

        # City codes from lookup
        o = lookup_airport(inp.origin)
        d = lookup_airport(inp.destination)
        cfg.home_city_code = o[0] if o else inp.origin.upper()
        cfg.dest_city_code = d[0] if d else inp.destination.upper()

        # Schedule
        cfg.frequency = inp.frequency
        cfg.aircraft_type = inp.aircraft_type.upper() if inp.aircraft_type else ''

        # Seats: user override > aircraft default
        if inp.seats is not None:
            cfg.seats = inp.seats
        elif cfg.aircraft_type in AIRCRAFT_DB:
            cfg.seats = AIRCRAFT_DB[cfg.aircraft_type].typical_seats
        else:
            cfg.seats = 0  # Will have been caught in validation

        # Times
        if inp.dep_time_outbound:
            cfg.outbound_dep = self._parse_time(inp.dep_time_outbound)
        if inp.dep_time_return:
            cfg.return_dep = self._parse_time(inp.dep_time_return)

        # Flight time
        if inp.flight_time_hrs:
            cfg.flight_time_hrs = inp.flight_time_hrs
        elif o and d:
            dist = haversine_nm(o[2], o[3], d[2], d[3])
            cfg.flight_time_hrs = dist / 460  # Rough estimate at 460kts

        # QSI parameters  user override > carrier default
        try:
            ct = CarrierType(inp.carrier_type)
        except ValueError:
            ct = CarrierType.FULL_SERVICE
        cd = QSI_DEFAULTS_BY_CARRIER.get(ct, QSI_DEFAULTS_BY_CARRIER[CarrierType.FULL_SERVICE])

        cfg.online_coeff = inp.online_coeff if inp.online_coeff is not None else cd['online_coeff']
        cfg.alliance_coeff = inp.alliance_coeff if inp.alliance_coeff is not None else cd['alliance_coeff']
        cfg.interline_coeff = inp.interline_coeff if inp.interline_coeff is not None else cd['interline_coeff']
        cfg.et_decay_factor = inp.et_decay_factor if inp.et_decay_factor is not None else cd['et_decay_factor']
        cfg.et_decay_interval = inp.et_decay_interval if inp.et_decay_interval is not None else cd['et_decay_interval']
        cfg.qsi_ceiling = inp.qsi_ceiling if inp.qsi_ceiling is not None else 1.0
        cfg.qsi_adjustment = inp.qsi_adjustment if inp.qsi_adjustment is not None else 1.0

        # Providers
        if inp.home_qsi_file:
            home_path = inp.home_qsi_file if os.path.isabs(inp.home_qsi_file) else \
                os.path.join(self.project_dir, inp.home_qsi_file)
            dest_path = inp.dest_qsi_file if inp.dest_qsi_file else home_path
            if not os.path.isabs(dest_path):
                dest_path = os.path.join(self.project_dir, dest_path)
            cfg.schedule_provider = ExcelScheduleProvider(
                qsi1_file=home_path,
                qsi2_file=dest_path,
            )

        if inp.forecast_file:
            fc_path = inp.forecast_file if os.path.isabs(inp.forecast_file) else \
                os.path.join(self.project_dir, inp.forecast_file)
            
            # Build P2P config with defaults based on route characteristics
            p2p_config = self._build_default_p2p_config(inp)
            
            cfg.demand_provider = ExcelDemandProvider(
                forecast_file=fc_path,
                p2p_config=p2p_config,
                home_growth=inp.home_growth if inp.home_growth is not None else GROWTH_DEFAULTS.get(
                    MarketMaturity(inp.market_maturity), 0.03),
                dest_growth=inp.dest_growth if inp.dest_growth is not None else GROWTH_DEFAULTS.get(
                    MarketMaturity(inp.market_maturity), 0.03),
            )

        return cfg

    def _build_default_p2p_config(self, inp: RouteInput) -> Dict[str, Any]:
        """Build default P2P segment configuration from route characteristics."""
        try:
            ct = CarrierType(inp.carrier_type)
            mm = MarketMaturity(inp.market_maturity)
        except ValueError:
            ct = CarrierType.FULL_SERVICE
            mm = MarketMaturity.NEW_ROUTE

        stim = STIMULATION_DEFAULTS.get((ct, mm), {'business': 1.10, 'leisure': 1.05})

        biz_stim = inp.stimulation_business if inp.stimulation_business is not None else stim['business']
        lei_stim = inp.stimulation_leisure if inp.stimulation_leisure is not None else stim['leisure']

        growth = inp.home_growth if inp.home_growth is not None else GROWTH_DEFAULTS.get(mm, 0.03)

        # Default P2P structure  placeholder that gets overwritten
        # when actual demand data is loaded from the forecast file
        return {
            'segments': [
                {
                    'name': 'Business',
                    'base_demand': 0,
                    'growth_rate': growth,
                    'stimulation': biz_stim,
                    'capture_rate': 0.0,
                },
                {
                    'name': 'Leisure/VFR',
                    'base_demand': 0,
                    'growth_rate': growth,
                    'stimulation': lei_stim,
                    'capture_rate': 0.0,
                },
            ],
        }

    # ================================================================
    # CONVENIENCE  Validate + Build in one step
    # ================================================================

    def process(self, inp: RouteInput) -> Tuple[Optional['RouteConfig'], ValidationResult]:
        """
        Validate and build config in one step.
        Returns (config, result) where config is None if validation failed.
        """
        result = self.validate(inp)
        if result.valid:
            config = self.build_config(inp)
            return config, result
        return None, result


# ============================================================================
# BA LHR-SJC REGRESSION  Must pass through this layer
# ============================================================================

def ba_lhr_sjc_input() -> RouteInput:
    """Create the BA LHR-SJC route input for regression testing."""
    inp = RouteInput()
    inp.mode = 'forecast'
    inp.origin = 'LHR'
    inp.destination = 'SJC'
    inp.route_type = 'long_haul'
    inp.carrier_type = 'full_service'
    inp.carrier_code = 'BA'
    inp.carrier_name = 'British Airways'
    inp.market_maturity = 'new_route'
    inp.demand_driver = 'mixed'
    inp.seasonal_profile = 'year_round'
    inp.frequency = 7
    inp.aircraft_type = '787'
    inp.seats = 214
    inp.dep_time_outbound = '15:30'
    inp.dep_time_return = '21:30'
    inp.flight_time_hrs = 11.0
    inp.existing_direct = False
    inp.indirect_competition = 'strong'
    inp.surface_competition = 'none'
    inp.home_qsi_file = 'QSILHR_v1_OS_JZ_17Feb15.xlsx'
    inp.dest_qsi_file = 'QSISJC.xlsx'
    inp.forecast_file = 'BA_Fcst_LHRSJC_JZ_23Feb2015_FINAL_without_INDIA.xlsm'
    inp.home_growth = 0.09
    inp.dest_growth = 0.10
    inp.stimulation_business = 1.15
    inp.stimulation_leisure = 1.00
    return inp


# ============================================================================
# CLI
# ============================================================================

def main():
    """Run validation regression test."""
    print("=" * 60)
    print("INPUT VALIDATION & CONFIGURATION  Chat 14")
    print("=" * 60)

    # Test 1: Valid BA LHR-SJC input
    print("\n--- Test 1: BA LHR-SJC (valid input) ---")
    inp = ba_lhr_sjc_input()
    validator = InputValidator()
    result = validator.validate(inp)
    print(result.summary())

    if result.valid:
        config = validator.build_config(inp)
        print(f"\n  RouteConfig: {config.summary()}")
        print(f"  Annual capacity: {config.annual_capacity:,}")
        print(f"  Home city: {config.home_city_code}")
        print(f"  Dest city: {config.dest_city_code}")
        print(f"  Online coeff: {config.online_coeff}")
        print(f"  Alliance coeff: {config.alliance_coeff}")
        print(f"  Interline coeff: {config.interline_coeff}")
        
        dist = compute_distance('LHR', 'SJC')
        print(f"  Distance: {dist:.0f}nm ({classify_distance_band(dist)})")

    # Test 2: Invalid inputs  should catch errors
    print("\n--- Test 2: Invalid inputs ---")
    bad = RouteInput()
    bad.origin = ''
    bad.destination = 'X'
    bad.frequency = 50
    bad.aircraft_type = '747'  # Not in DB
    bad.seats = None
    result2 = validator.validate(bad)
    print(result2.summary())

    # Test 3: Business Case mode missing targets
    print("\n--- Test 3: Business Case mode (missing targets) ---")
    bc = RouteInput()
    bc.mode = 'business_case'
    bc.origin = 'LHR'
    bc.destination = 'SJC'
    bc.aircraft_type = '789'
    result3 = validator.validate(bc)
    print(result3.summary())

    # Test 4: Range check  narrowbody on ultra-long-haul
    print("\n--- Test 4: A320 on LHR-SJC (range error) ---")
    range_test = RouteInput()
    range_test.origin = 'LHR'
    range_test.destination = 'SJC'
    range_test.aircraft_type = '320'
    range_test.seats = 170
    range_test.carrier_code = 'U2'
    range_test.carrier_type = 'lcc'
    result4 = validator.validate(range_test)
    print(result4.summary())

    # Test 5: LCC with sensible defaults
    print("\n--- Test 5: LCC route (check default coefficients) ---")
    lcc = RouteInput()
    lcc.origin = 'LHR'
    lcc.destination = 'DUB'
    lcc.carrier_type = 'lcc'
    lcc.carrier_code = 'FR'
    lcc.carrier_name = 'Ryanair'
    lcc.aircraft_type = '7M8'
    lcc.frequency = 14
    lcc.market_maturity = 'mature'
    lcc.route_type = 'lcc_p2p'
    result5 = validator.validate(lcc)
    print(result5.summary())
    if result5.valid:
        lcc_cfg = validator.build_config(lcc)
        print(f"  Alliance coeff: {lcc_cfg.alliance_coeff} (should be 0.0 for LCC)")
        print(f"  Interline coeff: {lcc_cfg.interline_coeff} (should be 0.0 for LCC)")

    # Test 6: Full pipeline regression through validator
    print("\n--- Test 6: Full pipeline regression (BA LHR-SJC through validator) ---")
    inp6 = ba_lhr_sjc_input()
    config6, result6 = validator.process(inp6)
    if config6:
        # Override P2P config with the actual BA values (from route_config.py)
        # The validator builds default P2P; for regression we need the actual values
        from route_config import RouteConfig as RC
        ba_config = RC.ba_lhr_sjc()
        
        # Verify key parameters match
        checks = [
            ('airline_code', config6.airline_code, ba_config.airline_code),
            ('home_airport', config6.home_airport_code, ba_config.home_airport_code),
            ('dest_airport', config6.dest_airport_code, ba_config.dest_airport_code),
            ('frequency', config6.frequency, ba_config.frequency),
            ('seats', config6.seats, ba_config.seats),
            ('online_coeff', config6.online_coeff, ba_config.online_coeff),
            ('alliance_coeff', config6.alliance_coeff, ba_config.alliance_coeff),
            ('interline_coeff', config6.interline_coeff, ba_config.interline_coeff),
        ]
        
        all_pass = True
        for name, got, expected in checks:
            match = '' if got == expected else ''
            if got != expected:
                all_pass = False
            print(f"  {match} {name}: {got} (expected {expected})")
        
        print(f"\n  Regression: {'PASS ' if all_pass else 'FAIL '}")
    else:
        print(f"  Validation failed: {result6.summary()}")

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main()
