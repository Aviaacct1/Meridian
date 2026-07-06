"""
direct_service_overlay.py  Direct Service Competition Layer

Addresses the structural gap in QSI models: connecting city passengers who
have nonstop or strong one-stop alternatives to the destination that don't
appear in the connection-based QSI denominator.

Two layers:
  1. Nonstop Injection: adds virtual nonstop itineraries to the QSI
     denominator for cities with nonstop service to the destination.
  2. Expert Override: applies learned penalty factors for cities where
     expert judgment consistently compresses the raw capture.

Usage:
    overlay = DirectServiceOverlay(
        nonstop_services=[
            NonstopService('DEL', carriers=['AI'], freq=7, flight_time_min=960),
            NonstopService('SIN', carriers=['SQ','UA'], freq=28, flight_time_min=930),
        ],
        expert_overrides={'COK': 0.03, 'TRV': 0.02, 'PNQ': 0.08},
    )
    
    adjusted = overlay.apply(raw_captures, itineraries, config)
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
import math


@dataclass
class NonstopService:
    """Nonstop service from a connecting city to the destination metro area."""
    city_code: str
    carriers: List[str] = field(default_factory=list)
    frequency: int = 7          # Weekly frequency
    flight_time_min: int = 600  # Flight time in minutes
    dest_airport: str = ''      # e.g., 'SFO' for Bay Area
    notes: str = ''


class DirectServiceOverlay:
    """
    Adjusts raw QSI capture rates to account for direct service competition
    that the connection-based QSI model cannot see.
    
    Layer 1  Nonstop Injection:
        For each city with a nonstop to the destination, computes the QSI
        score that nonstop service would achieve, adds it to the city's
        QSI denominator, and recomputes the capture rate.
        
    Layer 2  Expert Override:
        For cities with known expert penalties (accumulated over time),
        replaces the computed capture with the expert-specified value.
        These are cities where expert judgment indicates factors the
        model can't capture (brand preference, visa routing, cultural
        affinity, pricing, etc.)
    
    The overlay is designed to be ADDITIVE to the learning system:
    - Every route run produces a comparison of raw vs adjusted vs expert
    - Over time, Layer 2 overrides accumulate from expert decisions
    - When enough examples exist, the system can predict overrides
    """
    
    def __init__(self,
                 nonstop_services: List[NonstopService] = None,
                 expert_overrides: Dict[str, float] = None,
                 et_decay_factor: float = 0.8,
                 et_decay_interval: float = 0.1):
        """
        Args:
            nonstop_services: List of nonstop services to destination
            expert_overrides: Dict of city_code -> capture_rate overrides
            et_decay_factor: Elapsed time decay factor (must match QSI engine)
            et_decay_interval: ET decay interval (must match QSI engine)
        """
        self.nonstop_services = {ns.city_code: ns for ns in (nonstop_services or [])}
        self.expert_overrides = expert_overrides or {}
        self.et_decay_factor = et_decay_factor
        self.et_decay_interval = et_decay_interval
        self._audit: List[str] = []
    
    def _et_coefficient(self, elapsed_minutes: int) -> float:
        """Compute elapsed time coefficient (must match QSI engine curve)."""
        hours = elapsed_minutes / 60.0
        return self.et_decay_factor ** (hours * self.et_decay_interval)
    
    def _nonstop_qsi(self, ns: NonstopService) -> float:
        """Compute QSI score for a nonstop service.
        
        Nonstop gets:
        - cnx_coeff = 1.0 (ONLINE quality  best possible)
        - et_coeff from flight time (short = high score)
        - frequency multiplier
        
        Returns the total QSI score for this nonstop service.
        """
        et = self._et_coefficient(ns.flight_time_min)
        qsi = ns.frequency * 1.0 * et  # freq * online * et
        return qsi
    
    def apply(self,
              raw_captures: Dict[str, float],
              itineraries: list,
              proposed_carrier: str = '',
              ) -> Dict[str, float]:
        """
        Apply both layers to raw capture rates.
        
        Args:
            raw_captures: Dict of city_code -> raw capture rate from QSI engine
            itineraries: List of all Itinerary objects (for QSI denominator)
            proposed_carrier: Carrier code of proposed service
            
        Returns:
            Dict of city_code -> adjusted capture rate
        """
        self._audit = []
        adjusted = dict(raw_captures)
        
        #  Layer 1: Nonstop Injection 
        ns_adjustments = 0
        for city, ns in self.nonstop_services.items():
            if city not in raw_captures:
                continue
            
            # Get current QSI breakdown for this city
            city_its = [it for it in itineraries if it.city == city]
            if not city_its:
                continue
            
            ek_qsi = sum(it.qsi for it in city_its 
                        if it.carrier_l1 == proposed_carrier 
                        or it.carrier_l2 == proposed_carrier)
            total_qsi = sum(it.qsi for it in city_its)
            
            if total_qsi <= 0:
                continue
            
            # Add nonstop QSI to denominator
            ns_qsi = self._nonstop_qsi(ns)
            new_total = total_qsi + ns_qsi
            new_capture = ek_qsi / new_total
            
            old_capture = raw_captures[city]
            if abs(new_capture - old_capture) > 0.0001:
                self._audit.append(
                    f"  NS {city}: {old_capture:.4f} -> {new_capture:.4f} "
                    f"(+{ns_qsi:.1f} QSI from {','.join(ns.carriers)} "
                    f"{ns.frequency}x {ns.flight_time_min}m nonstop)"
                )
                adjusted[city] = new_capture
                ns_adjustments += 1
        
        if ns_adjustments:
            self._audit.insert(0, f"[Layer 1: Nonstop Injection] {ns_adjustments} cities adjusted")
        
        #  Layer 2: Expert Overrides 
        eo_adjustments = 0
        for city, override_capture in self.expert_overrides.items():
            if city in adjusted:
                old = adjusted[city]
                adjusted[city] = override_capture
                self._audit.append(
                    f"  EO {city}: {old:.4f} -> {override_capture:.4f} (expert override)"
                )
                eo_adjustments += 1
        
        if eo_adjustments:
            self._audit.append(f"[Layer 2: Expert Override] {eo_adjustments} cities adjusted")
        
        return adjusted
    
    @property
    def audit(self) -> List[str]:
        return self._audit
    
    def summary(self) -> str:
        """Return a summary of the overlay configuration."""
        lines = [f"DirectServiceOverlay:"]
        lines.append(f"  Nonstop services: {len(self.nonstop_services)} cities")
        for city, ns in sorted(self.nonstop_services.items()):
            lines.append(f"    {city}: {','.join(ns.carriers)} {ns.frequency}x/wk "
                        f"{ns.flight_time_min}m to {ns.dest_airport}")
        lines.append(f"  Expert overrides: {len(self.expert_overrides)} cities")
        for city, cap in sorted(self.expert_overrides.items()):
            lines.append(f"    {city}: {cap:.4f}")
        return '\n'.join(lines)


# 
# FACTORY FUNCTIONS  build overlays for known route types
# 

def build_sjc_nonstops() -> List[NonstopService]:
    """
    Build nonstop service list for the San Jose/San Francisco Bay Area.
    
    These are nonstop services from major connecting cities to SFO or SJC.
    Only includes INTERNATIONAL long-haul nonstops relevant to hub
    competition analysis. Domestic US nonstops are not relevant since
    all international connecting cities are international.
    
    Data vintage: approximate Aug 2019 schedules.
    In production, this would be refreshed from live OAG data.
    """
    return [
        # Indian cities with nonstop to SFO
        NonstopService('DEL', carriers=['AI'], frequency=7, 
                       flight_time_min=960, dest_airport='SFO',
                       notes='Air India DEL-SFO nonstop'),
        NonstopService('BLR', carriers=['AI'], frequency=4,
                       flight_time_min=1050, dest_airport='SFO',
                       notes='Air India BLR-SFO nonstop (launched 2018)'),
        
        # Asian hubs with nonstop to SFO (also QSI hubs)
        NonstopService('SIN', carriers=['SQ', 'UA'], frequency=28,
                       flight_time_min=930, dest_airport='SFO',
                       notes='SQ 3x daily, UA daily'),
        NonstopService('HKG', carriers=['CX', 'UA'], frequency=21,
                       flight_time_min=660, dest_airport='SFO'),
        NonstopService('NRT', carriers=['NH', 'UA', 'JL'], frequency=21,
                       flight_time_min=570, dest_airport='SFO'),
        NonstopService('PEK', carriers=['CA', 'UA'], frequency=14,
                       flight_time_min=660, dest_airport='SFO'),
        NonstopService('PVG', carriers=['MU', 'UA', 'CA'], frequency=21,
                       flight_time_min=690, dest_airport='SFO'),
        NonstopService('ICN', carriers=['KE', 'OZ', 'UA'], frequency=21,
                       flight_time_min=600, dest_airport='SFO'),
        NonstopService('TPE', carriers=['BR', 'CI'], frequency=14,
                       flight_time_min=660, dest_airport='SFO'),
        
        # European hubs with nonstop to SFO (also QSI hubs)
        NonstopService('LON', carriers=['BA', 'VS', 'UA'], frequency=28,
                       flight_time_min=660, dest_airport='SFO'),
        NonstopService('FRA', carriers=['LH', 'UA'], frequency=14,
                       flight_time_min=690, dest_airport='SFO'),
        NonstopService('AMS', carriers=['KL'], frequency=7,
                       flight_time_min=660, dest_airport='SFO'),
        NonstopService('IST', carriers=['TK'], frequency=7,
                       flight_time_min=780, dest_airport='SFO'),
    ]
