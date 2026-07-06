#!/usr/bin/env python3
"""
Avia Solutions - Commercial Reasonableness Engine (CRE)
=======================================================
Sits between the raw QSI pipeline output and the final forecast.
Applies analyst-like commercial judgment to ensure any auto-generated
forecast makes credible sense before being presented.

PURPOSE:
  When the pipeline runs on raw data for a route it hasn't seen before,
  the uncalibrated output often produces nonsensical results (150% LF,
  negative load factors, impossible connecting shares). An analyst would
  never report these -- they'd adjust parameters and re-run.

  This engine automates that review cycle:
    1. Run initial forecast with default/predicted parameters
    2. Check output against commercial bounds
    3. Identify which parameters are driving unreasonable results
    4. Adjust the most impactful parameter
    5. Re-run and check again
    6. Repeat until output falls within acceptable bounds or max iterations hit
    7. Produce a confidence-scored output with full adjustment trail

COMMERCIAL BOUNDS (from 22-case calibration library):
  - Load factor: 50-95% (target 65-85% for viable route)
  - P2P share of total: 15-80% depending on route type
  - Connecting share: 20-85% depending on hub strength
  - Stimulation factor: 1.0-1.5 (new market) or 0.8-1.0 (mature)
  - Capture rate: 10-50% depending on competitive intensity
  - QSI adjustment: 0.15-1.0 (median 0.27 for existing routes, 1.0 for new)
  - Annual growth: 2-8% for established markets, up to 15% for new

ADJUSTMENT PRIORITY ORDER:
  When load factor is too high (most common problem):
    1. Reduce QSI capture rates (connecting traffic is usually the culprit)
    2. Reduce P2P capture rate
    3. Reduce stimulation factors
    4. Suggest increasing frequency (if demand genuinely supports it)

  When load factor is too low:
    1. Increase stimulation (market may be under-estimated)
    2. Increase capture rates
    3. Suggest reducing frequency or downsizing aircraft
    4. Flag that route may not be commercially viable

FREQUENCY OPTIMISATION:
  Rather than just flagging bad LF, the engine can suggest optimal frequency:
    - Given the demand, what frequency produces 75% LF?
    - What's the minimum viable frequency for 65% LF?
    - What's the maximum supportable frequency at 80% LF?

ARCHITECTURE:
  CommercialBounds     - defines acceptable ranges per route type
  ReasonablenessCheck  - single check result (pass/flag/fail)
  AdjustmentRecord     - logs each parameter change and its effect
  CREResult            - complete output including adjusted forecast
  CommercialReasonablenessEngine - main engine class

INTEGRATION:
  Called by the portal after run_pipeline() returns:

    from commercial_reasonableness_engine import CommercialReasonablenessEngine

    cre = CommercialReasonablenessEngine(config, pipeline_results)
    cre_result = cre.run()

    if cre_result.adjusted:
        # Show user the adjusted forecast with explanation
        # Offer side-by-side: raw vs adjusted
    else:
        # Raw forecast passed all checks - present as-is

LAST UPDATED: February 2026
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import math
import copy
import json
from datetime import datetime


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class CheckStatus(Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    CRITICAL = "critical"


class AdjustmentType(Enum):
    SCALE_CNX_HOME = "scale_connecting_home"
    SCALE_CNX_DEST = "scale_connecting_dest"
    SCALE_CNX_BOTH = "scale_connecting_both"
    SCALE_P2P = "scale_p2p"
    SCALE_STIM = "scale_stimulation"
    FREQ_CHANGE = "frequency_change"
    AIRCRAFT_CHANGE = "aircraft_change"
    FLAG_NONVIABLE = "flag_nonviable"


MAX_ITERATIONS = 10
DEFAULT_SEATS = 214
DEFAULT_FREQUENCY = 7


# =============================================================================
# COMMERCIAL BOUNDS
# =============================================================================

@dataclass
class CommercialBounds:
    """Acceptable ranges for commercial parameters, by route type."""

    # Load factor bounds
    lf_min_viable: float = 0.50      # Below this = commercially non-viable
    lf_target_low: float = 0.65      # Lower end of healthy range
    lf_target_high: float = 0.82     # Upper end of presentable range
    lf_max_credible: float = 0.90    # Above this = looks artificially high to airlines
    lf_impossible: float = 1.00      # Hard ceiling

    # P2P share of total traffic
    p2p_share_min: float = 0.10
    p2p_share_max: float = 0.90
    p2p_share_typical: float = 0.40

    # Connecting traffic share
    cnx_share_min: float = 0.10
    cnx_share_max: float = 0.90
    cnx_share_typical: float = 0.60

    # Home vs dest connecting balance
    home_dest_ratio_min: float = 0.3   # Home should be at least 30% of connecting
    home_dest_ratio_max: float = 15.0  # Home shouldn't exceed 15x dest

    # QSI capture rate bounds
    qsi_capture_min: float = 0.01
    qsi_capture_max: float = 0.60
    qsi_capture_typical: float = 0.15

    # Stimulation factor bounds
    stim_min: float = 0.90
    stim_max: float = 1.50
    stim_typical: float = 1.10

    # P2P capture rate bounds
    p2p_capture_min: float = 0.10
    p2p_capture_max: float = 0.50
    p2p_capture_typical: float = 0.25

    # Growth rate bounds (annual)
    growth_min: float = 0.01
    growth_max: float = 0.15
    growth_typical: float = 0.04

    # Default QSI capture for unmatched cities
    default_capture_min: float = 0.005
    default_capture_max: float = 0.10
    default_capture_typical: float = 0.03

    label: str = "Default"


def get_bounds_for_route_type(carrier_type: str, route_type: str,
                               hub_status: str = 'Major Hub',
                               is_new_route: bool = True) -> CommercialBounds:
    """
    Return appropriate commercial bounds based on route characteristics.
    Derived from patterns in the 22-case calibration library.
    """
    bounds = CommercialBounds()

    ct = carrier_type.lower() if carrier_type else ''
    rt = route_type.lower() if route_type else ''
    hs = hub_status.lower() if hub_status else ''

    # LCC routes: high P2P share, lower connecting, higher stimulation
    if 'lcc' in ct or 'ultra' in ct:
        bounds.p2p_share_typical = 0.70
        bounds.p2p_share_min = 0.40
        bounds.cnx_share_typical = 0.30
        bounds.cnx_share_max = 0.60
        bounds.stim_min = 1.05
        bounds.stim_typical = 1.25
        bounds.stim_max = 1.50
        bounds.p2p_capture_typical = 0.30
        bounds.p2p_capture_max = 0.50
        bounds.label = "LCC"

    # Hub feed / long-haul full service: connecting dominant
    elif 'hub' in rt or 'long' in rt:
        if 'major' in hs:
            bounds.cnx_share_typical = 0.65
            bounds.cnx_share_min = 0.30
            bounds.p2p_share_typical = 0.35
            bounds.qsi_capture_typical = 0.20
            bounds.qsi_capture_max = 0.45
            bounds.label = "Major Hub Long-Haul"
        elif 'secondary' in hs:
            bounds.cnx_share_typical = 0.50
            bounds.p2p_share_typical = 0.50
            bounds.qsi_capture_typical = 0.30
            bounds.qsi_capture_max = 0.55
            bounds.label = "Secondary Hub Long-Haul"
        else:
            bounds.cnx_share_typical = 0.40
            bounds.p2p_share_typical = 0.60
            bounds.label = "Non-Hub Long-Haul"

        bounds.stim_typical = 1.05
        bounds.stim_max = 1.20

    # Charter/leisure
    elif 'charter' in ct or 'leisure' in rt:
        bounds.p2p_share_typical = 0.85
        bounds.cnx_share_typical = 0.15
        bounds.cnx_share_max = 0.30
        bounds.stim_typical = 1.15
        bounds.p2p_capture_typical = 0.35
        bounds.lf_target_low = 0.75
        bounds.lf_target_high = 0.88
        bounds.label = "Charter/Leisure"

    # New route adjustments
    if is_new_route:
        bounds.stim_min = max(bounds.stim_min, 1.0)
        bounds.stim_typical = max(bounds.stim_typical, 1.10)
        bounds.lf_target_low = max(bounds.lf_target_low - 0.05, 0.55)

    return bounds


# =============================================================================
# CHECK AND ADJUSTMENT RECORDS
# =============================================================================

@dataclass
class ReasonablenessCheck:
    """Result of a single commercial reasonableness check."""
    name: str
    status: CheckStatus
    actual_value: float
    acceptable_range: Tuple[float, float]
    message: str
    severity: int = 0  # 0=info, 1=warning, 2=fail, 3=critical
    suggested_action: str = ""

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'status': self.status.value,
            'actual': self.actual_value,
            'range': list(self.acceptable_range),
            'message': self.message,
            'severity': self.severity,
            'action': self.suggested_action,
        }


@dataclass
class AdjustmentRecord:
    """Records a single parameter adjustment and its effect."""
    iteration: int
    adjustment_type: AdjustmentType
    parameter: str
    old_value: float
    new_value: float
    reason: str
    lf_before: float
    lf_after: float
    total_before: float
    total_after: float

    @property
    def lf_delta(self) -> float:
        return self.lf_after - self.lf_before

    def to_dict(self) -> Dict:
        return {
            'iteration': self.iteration,
            'type': self.adjustment_type.value,
            'parameter': self.parameter,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'reason': self.reason,
            'lf_before': self.lf_before,
            'lf_after': self.lf_after,
            'total_before': self.total_before,
            'total_after': self.total_after,
        }


@dataclass
class FrequencyRecommendation:
    """Frequency optimisation output."""
    current_frequency: int
    current_lf: float
    recommended_frequency: int
    recommended_lf: float
    min_viable_frequency: int       # Minimum for 65% LF
    max_supportable_frequency: int  # Maximum for 80% LF
    demand_total: float
    seats_per_flight: int
    reasoning: str

    def to_dict(self) -> Dict:
        return {
            'current_freq': self.current_frequency,
            'current_lf': self.current_lf,
            'recommended_freq': self.recommended_frequency,
            'recommended_lf': self.recommended_lf,
            'min_viable_freq': self.min_viable_frequency,
            'max_supportable_freq': self.max_supportable_frequency,
            'demand_total': self.demand_total,
            'seats': self.seats_per_flight,
            'reasoning': self.reasoning,
        }


@dataclass
class CREResult:
    """Complete output from the Commercial Reasonableness Engine."""
    # Was the forecast adjusted?
    adjusted: bool = False

    # Original (raw) results
    raw_results: Dict = field(default_factory=dict)
    raw_load_factor: float = 0.0
    raw_total: float = 0.0

    # Adjusted results (if adjusted)
    adjusted_results: Dict = field(default_factory=dict)
    adjusted_load_factor: float = 0.0
    adjusted_total: float = 0.0

    # All checks performed
    checks: List[ReasonablenessCheck] = field(default_factory=list)

    # Adjustment trail
    adjustments: List[AdjustmentRecord] = field(default_factory=list)
    iterations_used: int = 0

    # Frequency recommendation
    frequency_rec: Optional[FrequencyRecommendation] = None

    # Bounds used
    bounds: Optional[CommercialBounds] = None

    # Overall confidence score (0-100)
    confidence_score: int = 50
    confidence_reasoning: str = ""

    # Summary messages
    summary: List[str] = field(default_factory=list)

    # Analyst review flag
    needs_analyst_review: bool = True
    review_reasons: List[str] = field(default_factory=list)

    def passed_all_checks(self) -> bool:
        return all(c.status in (CheckStatus.PASS, CheckStatus.WARNING) for c in self.checks)

    def critical_failures(self) -> List[ReasonablenessCheck]:
        return [c for c in self.checks if c.status == CheckStatus.CRITICAL]

    def to_dict(self) -> Dict:
        return {
            'adjusted': self.adjusted,
            'raw_lf': self.raw_load_factor,
            'raw_total': self.raw_total,
            'adjusted_lf': self.adjusted_load_factor,
            'adjusted_total': self.adjusted_total,
            'checks': [c.to_dict() for c in self.checks],
            'adjustments': [a.to_dict() for a in self.adjustments],
            'iterations': self.iterations_used,
            'frequency_rec': self.frequency_rec.to_dict() if self.frequency_rec else None,
            'confidence_score': self.confidence_score,
            'confidence_reasoning': self.confidence_reasoning,
            'summary': self.summary,
            'needs_analyst_review': self.needs_analyst_review,
            'review_reasons': self.review_reasons,
        }


# =============================================================================
# MAIN ENGINE
# =============================================================================

class CommercialReasonablenessEngine:
    """
    Automated analyst review cycle for QSI forecasts.

    Takes raw pipeline output, checks it against commercial bounds,
    and iteratively adjusts parameters until the forecast is credible.
    """

    def __init__(self, config, pipeline_results: Dict,
                 bounds: Optional[CommercialBounds] = None):
        self.config = config
        self.raw_results = copy.deepcopy(pipeline_results)
        self.working = copy.deepcopy(pipeline_results)

        # Get seats and frequency from config
        self.seats = getattr(config, 'seats', DEFAULT_SEATS)
        self.frequency = getattr(config, 'frequency', DEFAULT_FREQUENCY)
        self.capacity = self.seats * self.frequency * 52 * 2  # annual both-way

        # Select bounds
        if bounds:
            self.bounds = bounds
        else:
            ct = getattr(config, 'carrier_type', 'Full Service')
            rt = getattr(config, 'route_type', 'Hub Long-Haul')
            hs = getattr(config, 'hub_status', 'Major Hub')
            nr = getattr(config, 'is_new_route', True)
            self.bounds = get_bounds_for_route_type(ct, rt, hs, nr)

    def _lf(self, total: float = None) -> float:
        """Calculate load factor."""
        t = total if total is not None else self.working.get('grand_total', 0)
        return t / self.capacity if self.capacity > 0 else 0.0

    def _lf_for_freq(self, total: float, freq: int) -> float:
        """Load factor at a given frequency."""
        cap = self.seats * freq * 52 * 2
        return total / cap if cap > 0 else 0.0

    # =========================================================================
    # CHECKS
    # =========================================================================

    def check_load_factor(self) -> ReasonablenessCheck:
        """Check 1: Is the load factor within credible bounds?"""
        lf = self._lf()
        b = self.bounds

        if lf > b.lf_impossible:
            return ReasonablenessCheck(
                "Load Factor", CheckStatus.CRITICAL, lf,
                (b.lf_target_low, b.lf_target_high),
                f"Load factor {lf:.1%} exceeds 100% - physically impossible",
                severity=3,
                suggested_action="Reduce connecting traffic captures or increase frequency"
            )
        elif lf > b.lf_max_credible:
            return ReasonablenessCheck(
                "Load Factor", CheckStatus.FAIL, lf,
                (b.lf_target_low, b.lf_target_high),
                f"Load factor {lf:.1%} exceeds credible maximum ({b.lf_max_credible:.0%})",
                severity=2,
                suggested_action="Scale down connecting captures; likely overestimated"
            )
        elif lf < b.lf_min_viable:
            return ReasonablenessCheck(
                "Load Factor", CheckStatus.FAIL, lf,
                (b.lf_target_low, b.lf_target_high),
                f"Load factor {lf:.1%} below minimum viable ({b.lf_min_viable:.0%})",
                severity=2,
                suggested_action="Reduce frequency or flag route as non-viable"
            )
        elif lf < b.lf_target_low:
            return ReasonablenessCheck(
                "Load Factor", CheckStatus.WARNING, lf,
                (b.lf_target_low, b.lf_target_high),
                f"Load factor {lf:.1%} below target range ({b.lf_target_low:.0%}-{b.lf_target_high:.0%})",
                severity=1,
                suggested_action="Consider lower frequency or stimulation uplift"
            )
        elif lf > b.lf_target_high:
            return ReasonablenessCheck(
                "Load Factor", CheckStatus.WARNING, lf,
                (b.lf_target_low, b.lf_target_high),
                f"Load factor {lf:.1%} above target range - possible overestimate",
                severity=1,
                suggested_action="Review capture assumptions; consider higher frequency"
            )
        else:
            return ReasonablenessCheck(
                "Load Factor", CheckStatus.PASS, lf,
                (b.lf_target_low, b.lf_target_high),
                f"Load factor {lf:.1%} within target range",
            )

    def check_total_passengers(self) -> ReasonablenessCheck:
        """Check 2: Total passenger count plausibility."""
        total = self.working.get('grand_total', 0)
        # Very rough heuristic: per-flight demand
        flights_per_year = self.frequency * 52 * 2
        pax_per_flight = total / flights_per_year if flights_per_year > 0 else 0
        min_pax = self.seats * 0.3  # 30% of seat capacity
        max_pax = self.seats * 1.1  # 110% of seat capacity (slight spill OK)

        if pax_per_flight > max_pax:
            return ReasonablenessCheck(
                "Total Passengers", CheckStatus.FAIL, total,
                (min_pax * flights_per_year, max_pax * flights_per_year),
                f"{total:,.0f} pax = {pax_per_flight:.0f}/flight vs {self.seats} seats",
                severity=2,
                suggested_action="Overestimated demand; reduce captures"
            )
        elif pax_per_flight < min_pax:
            return ReasonablenessCheck(
                "Total Passengers", CheckStatus.WARNING, total,
                (min_pax * flights_per_year, max_pax * flights_per_year),
                f"{total:,.0f} pax = {pax_per_flight:.0f}/flight (low for {self.seats}-seat aircraft)",
                severity=1,
                suggested_action="Consider smaller aircraft or fewer frequencies"
            )
        else:
            return ReasonablenessCheck(
                "Total Passengers", CheckStatus.PASS, total,
                (min_pax * flights_per_year, max_pax * flights_per_year),
                f"{total:,.0f} pax = {pax_per_flight:.0f}/flight looks reasonable",
            )

    def check_p2p_share(self) -> ReasonablenessCheck:
        """Check 3: Is the P2P vs connecting split reasonable?"""
        total = self.working.get('grand_total', 0)
        p2p = self.working.get('p2p_total', 0)
        if total <= 0:
            return ReasonablenessCheck(
                "P2P Share", CheckStatus.WARNING, 0.0,
                (self.bounds.p2p_share_min, self.bounds.p2p_share_max),
                "No demand to check P2P share",
                severity=1
            )
        share = p2p / total
        b = self.bounds
        if share < b.p2p_share_min:
            return ReasonablenessCheck(
                "P2P Share", CheckStatus.WARNING, share,
                (b.p2p_share_min, b.p2p_share_max),
                f"P2P share {share:.0%} is very low - connecting may be overestimated",
                severity=1,
                suggested_action="Review connecting capture rates"
            )
        elif share > b.p2p_share_max:
            return ReasonablenessCheck(
                "P2P Share", CheckStatus.WARNING, share,
                (b.p2p_share_min, b.p2p_share_max),
                f"P2P share {share:.0%} is very high - connecting may be underestimated",
                severity=1,
                suggested_action="Review hub connectivity and connecting demand sources"
            )
        else:
            return ReasonablenessCheck(
                "P2P Share", CheckStatus.PASS, share,
                (b.p2p_share_min, b.p2p_share_max),
                f"P2P share {share:.0%} within expected range",
            )

    def check_connecting_balance(self) -> ReasonablenessCheck:
        """Check 4: Home vs destination connecting traffic balance."""
        home = self.working.get('home_total', 0)
        dest = self.working.get('dest_total', 0)
        b = self.bounds

        if home == 0 and dest == 0:
            return ReasonablenessCheck(
                "Connecting Balance", CheckStatus.WARNING, 0.0,
                (b.home_dest_ratio_min, b.home_dest_ratio_max),
                "No connecting traffic on either side",
                severity=1
            )

        if dest > 0:
            ratio = home / dest
        elif home > 0:
            ratio = 999.0
        else:
            ratio = 1.0

        if ratio > b.home_dest_ratio_max:
            return ReasonablenessCheck(
                "Connecting Balance", CheckStatus.WARNING, ratio,
                (b.home_dest_ratio_min, b.home_dest_ratio_max),
                f"Home/Dest ratio {ratio:.1f}x - home hub heavily dominant",
                severity=1,
                suggested_action="Verify destination hub has limited connectivity"
            )
        elif ratio < b.home_dest_ratio_min:
            return ReasonablenessCheck(
                "Connecting Balance", CheckStatus.WARNING, ratio,
                (b.home_dest_ratio_min, b.home_dest_ratio_max),
                f"Home/Dest ratio {ratio:.2f}x - destination stronger than home",
                severity=1,
                suggested_action="Unusual pattern; verify home hub is correctly identified"
            )
        else:
            return ReasonablenessCheck(
                "Connecting Balance", CheckStatus.PASS, ratio,
                (b.home_dest_ratio_min, b.home_dest_ratio_max),
                f"Home/Dest ratio {ratio:.1f}x within expected range",
            )

    def check_zero_components(self) -> ReasonablenessCheck:
        """Check 5: Flag if any major component is zero."""
        p2p = self.working.get('p2p_total', 0)
        home = self.working.get('home_total', 0)
        dest = self.working.get('dest_total', 0)
        zeros = []
        if p2p == 0:
            zeros.append("P2P")
        if home == 0:
            zeros.append("Home connecting")
        if dest == 0:
            zeros.append("Dest connecting")

        if len(zeros) >= 2:
            return ReasonablenessCheck(
                "Zero Components", CheckStatus.FAIL, len(zeros),
                (0, 0),
                f"Multiple components are zero: {', '.join(zeros)}",
                severity=2,
                suggested_action="Check data inputs; likely missing demand or QSI data"
            )
        elif len(zeros) == 1:
            return ReasonablenessCheck(
                "Zero Components", CheckStatus.WARNING, 1,
                (0, 0),
                f"{zeros[0]} is zero - check inputs",
                severity=1,
                suggested_action=f"Verify {zeros[0]} data is available"
            )
        else:
            return ReasonablenessCheck(
                "Zero Components", CheckStatus.PASS, 0,
                (0, 0),
                "All demand components present",
            )

    def check_city_capture_outliers(self) -> ReasonablenessCheck:
        """Check 6: Flag any individual city captures that look extreme."""
        outliers = []
        for side_key in ['home_results', 'dest_results']:
            side = self.working.get(side_key, [])
            if not isinstance(side, list):
                continue
            for city_data in side:
                if not isinstance(city_data, dict):
                    continue
                cap_rate = city_data.get('capture_rate', city_data.get('qsi_capture', 0))
                city = city_data.get('city', city_data.get('city_code', '???'))
                if cap_rate > self.bounds.qsi_capture_max:
                    outliers.append(f"{city}: {cap_rate:.1%}")

        if outliers:
            return ReasonablenessCheck(
                "City Captures", CheckStatus.WARNING, len(outliers),
                (0, 0),
                f"{len(outliers)} city capture outliers: {'; '.join(outliers[:5])}",
                severity=1,
                suggested_action="Cap outlier captures or review QSI parameters"
            )
        else:
            return ReasonablenessCheck(
                "City Captures", CheckStatus.PASS, 0,
                (0, 0),
                "No individual city capture outliers detected",
            )

    def check_connecting_share(self) -> ReasonablenessCheck:
        """Check 7: Is total connecting share within bounds?"""
        total = self.working.get('grand_total', 0)
        p2p = self.working.get('p2p_total', 0)
        cnx = total - p2p
        b = self.bounds

        if total <= 0:
            return ReasonablenessCheck(
                "Connecting Share", CheckStatus.WARNING, 0.0,
                (b.cnx_share_min, b.cnx_share_max),
                "No demand to check connecting share",
                severity=1
            )

        share = cnx / total
        if share > b.cnx_share_max:
            return ReasonablenessCheck(
                "Connecting Share", CheckStatus.WARNING, share,
                (b.cnx_share_min, b.cnx_share_max),
                f"Connecting share {share:.0%} exceeds typical max ({b.cnx_share_max:.0%})",
                severity=1,
                suggested_action="Scale down connecting captures"
            )
        elif share < b.cnx_share_min:
            return ReasonablenessCheck(
                "Connecting Share", CheckStatus.WARNING, share,
                (b.cnx_share_min, b.cnx_share_max),
                f"Connecting share {share:.0%} below typical min ({b.cnx_share_min:.0%})",
                severity=1,
                suggested_action="Verify hub connectivity data is loaded"
            )
        else:
            return ReasonablenessCheck(
                "Connecting Share", CheckStatus.PASS, share,
                (b.cnx_share_min, b.cnx_share_max),
                f"Connecting share {share:.0%} within expected range",
            )

    def check_demand_concentration(self) -> ReasonablenessCheck:
        """Check 8: Is demand too concentrated in one city?"""
        for side_key, label in [('home_results', 'Home'), ('dest_results', 'Dest')]:
            side = self.working.get(side_key, [])
            if not isinstance(side, list) or len(side) < 2:
                continue
            side_total = sum(
                c.get('captured_pax', c.get('pax', 0))
                for c in side if isinstance(c, dict)
            )
            if side_total <= 0:
                continue
            for city_data in side:
                if not isinstance(city_data, dict):
                    continue
                pax = city_data.get('captured_pax', city_data.get('pax', 0))
                city = city_data.get('city', city_data.get('city_code', '???'))
                if pax / side_total > 0.50:
                    return ReasonablenessCheck(
                        "Demand Concentration", CheckStatus.WARNING,
                        pax / side_total,
                        (0.0, 0.50),
                        f"{label} side: {city} accounts for {pax/side_total:.0%} of connecting traffic",
                        severity=1,
                        suggested_action="Review whether single-city dominance is realistic"
                    )

        return ReasonablenessCheck(
            "Demand Concentration", CheckStatus.PASS, 0.0,
            (0.0, 0.50),
            "No excessive single-city concentration detected",
        )

    def run_all_checks(self) -> List[ReasonablenessCheck]:
        """Run all 8 checks and return results."""
        return [
            self.check_load_factor(),
            self.check_total_passengers(),
            self.check_p2p_share(),
            self.check_connecting_share(),
            self.check_connecting_balance(),
            self.check_zero_components(),
            self.check_city_capture_outliers(),
            self.check_demand_concentration(),
        ]

    # =========================================================================
    # ADJUSTMENTS
    # =========================================================================

    def _scale_connecting(self, factor: float, side: str = 'both') -> AdjustmentRecord:
        """Scale connecting traffic by factor."""
        lf_before = self._lf()
        total_before = self.working['grand_total']

        home_old = self.working.get('home_total', 0)
        dest_old = self.working.get('dest_total', 0)

        if side in ('home', 'both'):
            self.working['home_total'] = home_old * factor
        if side in ('dest', 'both'):
            self.working['dest_total'] = dest_old * factor

        self.working['grand_total'] = (
            self.working.get('p2p_total', 0) +
            self.working.get('home_total', 0) +
            self.working.get('dest_total', 0)
        )
        self.working['load_factor'] = self._lf()

        adj_type = {
            'home': AdjustmentType.SCALE_CNX_HOME,
            'dest': AdjustmentType.SCALE_CNX_DEST,
            'both': AdjustmentType.SCALE_CNX_BOTH,
        }[side]

        return AdjustmentRecord(
            iteration=0,  # set by caller
            adjustment_type=adj_type,
            parameter=f"connecting_{side}",
            old_value=home_old + dest_old if side == 'both' else (home_old if side == 'home' else dest_old),
            new_value=self.working.get('home_total', 0) + self.working.get('dest_total', 0)
                      if side == 'both'
                      else (self.working.get('home_total', 0) if side == 'home'
                            else self.working.get('dest_total', 0)),
            reason=f"Scale {side} connecting by {factor:.2f}",
            lf_before=lf_before,
            lf_after=self._lf(),
            total_before=total_before,
            total_after=self.working['grand_total'],
        )

    def _scale_p2p(self, factor: float) -> AdjustmentRecord:
        """Scale P2P traffic by factor."""
        lf_before = self._lf()
        total_before = self.working['grand_total']
        p2p_old = self.working.get('p2p_total', 0)

        self.working['p2p_total'] = p2p_old * factor
        self.working['grand_total'] = (
            self.working['p2p_total'] +
            self.working.get('home_total', 0) +
            self.working.get('dest_total', 0)
        )
        self.working['load_factor'] = self._lf()

        return AdjustmentRecord(
            iteration=0,
            adjustment_type=AdjustmentType.SCALE_P2P,
            parameter="p2p_total",
            old_value=p2p_old,
            new_value=self.working['p2p_total'],
            reason=f"Scale P2P by {factor:.2f}",
            lf_before=lf_before,
            lf_after=self._lf(),
            total_before=total_before,
            total_after=self.working['grand_total'],
        )

    def _compute_frequency_rec(self) -> FrequencyRecommendation:
        """Compute optimal frequency recommendation."""
        total = self.working.get('grand_total', 0)
        seats = self.seats
        freq = self.frequency

        # Target: 75% LF
        target_cap_75 = total / 0.75 if total > 0 else 0
        rec_freq_75 = max(1, round(target_cap_75 / (seats * 52 * 2)))

        # Min viable: 65% LF
        target_cap_65 = total / 0.65 if total > 0 else 0
        max_freq = max(1, round(target_cap_65 / (seats * 52 * 2)))

        # Max supportable: 80% LF
        target_cap_80 = total / 0.80 if total > 0 else 0
        min_freq = max(1, round(target_cap_80 / (seats * 52 * 2)))

        current_lf = self._lf_for_freq(total, freq)
        rec_lf = self._lf_for_freq(total, rec_freq_75)

        if rec_freq_75 == freq:
            reasoning = f"Current {freq}x/week produces {current_lf:.0%} LF - good match"
        elif rec_freq_75 > freq:
            reasoning = (f"Demand supports {rec_freq_75}x/week at 75% LF "
                        f"(current {freq}x = {current_lf:.0%} LF)")
        else:
            reasoning = (f"Recommend reducing to {rec_freq_75}x/week for 75% LF "
                        f"(current {freq}x = {current_lf:.0%} LF)")

        return FrequencyRecommendation(
            current_frequency=freq,
            current_lf=current_lf,
            recommended_frequency=rec_freq_75,
            recommended_lf=rec_lf,
            min_viable_frequency=min_freq,
            max_supportable_frequency=max_freq,
            demand_total=total,
            seats_per_flight=seats,
            reasoning=reasoning,
        )

    # =========================================================================
    # ITERATIVE ADJUSTMENT LOOP
    # =========================================================================

    def _iterate_adjustments(self) -> Tuple[List[AdjustmentRecord], int]:
        """
        Iteratively adjust parameters until load factor is within bounds.
        Follows analyst priority: connecting first, then P2P, then frequency.
        """
        adjustments = []
        b = self.bounds

        for iteration in range(1, MAX_ITERATIONS + 1):
            lf = self._lf()

            # Check if within acceptable range
            if b.lf_target_low <= lf <= b.lf_target_high:
                break

            if lf > b.lf_max_credible:
                # Too high: scale down connecting first
                cnx_total = (self.working.get('home_total', 0) +
                            self.working.get('dest_total', 0))
                p2p = self.working.get('p2p_total', 0)

                if cnx_total > p2p * 0.5:
                    # Connecting is the bigger contributor - scale it down
                    target_total = self.capacity * b.lf_target_high
                    needed_cnx = target_total - p2p
                    factor = needed_cnx / cnx_total if cnx_total > 0 else 0.5
                    factor = max(0.1, min(factor, 0.95))  # Don't zero out
                    adj = self._scale_connecting(factor, 'both')
                    adj.iteration = iteration
                    adjustments.append(adj)
                else:
                    # P2P is dominant - scale it down
                    target_total = self.capacity * b.lf_target_high
                    needed_p2p = target_total - cnx_total
                    factor = needed_p2p / p2p if p2p > 0 else 0.5
                    factor = max(0.1, min(factor, 0.95))
                    adj = self._scale_p2p(factor)
                    adj.iteration = iteration
                    adjustments.append(adj)

            elif lf < b.lf_min_viable:
                # Too low: don't inflate demand, just note it
                # The frequency recommendation will handle this
                break

            elif lf < b.lf_target_low:
                # Slightly low but viable - leave it, freq rec will advise
                break

            elif lf > b.lf_target_high:
                # Slightly above target - gentle reduction
                target_total = self.capacity * b.lf_target_high
                current_total = self.working['grand_total']
                factor = target_total / current_total if current_total > 0 else 0.9
                factor = max(0.5, min(factor, 0.99))

                cnx_total = (self.working.get('home_total', 0) +
                            self.working.get('dest_total', 0))
                if cnx_total > self.working.get('p2p_total', 0):
                    adj = self._scale_connecting(factor, 'both')
                else:
                    adj = self._scale_p2p(factor)
                adj.iteration = iteration
                adjustments.append(adj)

        return adjustments, len(adjustments)

    # =========================================================================
    # CONFIDENCE SCORING
    # =========================================================================

    def _score_confidence(self, checks: List[ReasonablenessCheck],
                          adjustments: List[AdjustmentRecord],
                          adjusted: bool) -> Tuple[int, str]:
        """Score confidence 0-100 based on checks and adjustments."""
        score = 100
        reasons = []

        # Deduct for check failures
        for c in checks:
            if c.status == CheckStatus.CRITICAL:
                score -= 30
                reasons.append(f"Critical: {c.name}")
            elif c.status == CheckStatus.FAIL:
                score -= 15
                reasons.append(f"Fail: {c.name}")
            elif c.status == CheckStatus.WARNING:
                score -= 5
                reasons.append(f"Warning: {c.name}")

        # Deduct for adjustments
        if adjusted:
            score -= min(20, len(adjustments) * 5)
            reasons.append(f"Required {len(adjustments)} adjustments")

        # Bonus for being in the sweet spot
        lf = self._lf()
        if 0.70 <= lf <= 0.82:
            score += 5
            reasons.append("LF in sweet spot (70-82%)")

        score = max(0, min(100, score))

        if score >= 80:
            reasoning = "High confidence - forecast within commercial bounds"
        elif score >= 60:
            reasoning = "Moderate confidence - some parameters outside norms"
        elif score >= 40:
            reasoning = "Low confidence - significant adjustments needed"
        else:
            reasoning = "Very low confidence - forecast requires substantial analyst review"

        if reasons:
            reasoning += f" ({'; '.join(reasons[:3])})"

        return score, reasoning

    # =========================================================================
    # MAIN RUN METHOD
    # =========================================================================

    def run(self) -> CREResult:
        """Execute the full CRE process."""
        result = CREResult()
        result.raw_results = copy.deepcopy(self.raw_results)
        result.raw_load_factor = self._lf(self.raw_results.get('grand_total', 0))
        result.raw_total = self.raw_results.get('grand_total', 0)
        result.bounds = self.bounds

        # Run initial checks
        initial_checks = self.run_all_checks()

        # Determine if adjustment needed
        needs_adjustment = any(
            c.status in (CheckStatus.FAIL, CheckStatus.CRITICAL)
            for c in initial_checks
        )

        if needs_adjustment:
            # Run iterative adjustments
            adjustments, iterations = self._iterate_adjustments()
            result.adjustments = adjustments
            result.iterations_used = iterations
            result.adjusted = True

        # Run checks again on (possibly adjusted) working data
        final_checks = self.run_all_checks()
        result.checks = final_checks

        # Set adjusted results
        result.adjusted_results = copy.deepcopy(self.working)
        result.adjusted_load_factor = self._lf()
        result.adjusted_total = self.working.get('grand_total', 0)

        # Frequency recommendation
        result.frequency_rec = self._compute_frequency_rec()

        # Confidence score
        result.confidence_score, result.confidence_reasoning = self._score_confidence(
            final_checks, result.adjustments, result.adjusted
        )

        # Analyst review flag
        result.needs_analyst_review = (
            result.confidence_score < 70 or
            any(c.status in (CheckStatus.FAIL, CheckStatus.CRITICAL) for c in final_checks)
        )
        result.review_reasons = []
        if result.adjusted:
            result.review_reasons.append(
                f"Forecast was auto-adjusted ({result.iterations_used} iterations)"
            )
        for c in final_checks:
            if c.status in (CheckStatus.FAIL, CheckStatus.CRITICAL):
                result.review_reasons.append(f"{c.name}: {c.message}")
        if result.confidence_score < 60:
            result.review_reasons.append(
                f"Low confidence score ({result.confidence_score}/100)"
            )

        # Build summary
        result.summary = self._build_summary(result)

        return result

    def _build_summary(self, result: CREResult) -> List[str]:
        """Build human-readable summary lines."""
        lines = []
        lines.append(f"=== Commercial Reasonableness Engine Report ===")
        ac = getattr(self.config, 'airline_code', '??')
        ho = getattr(self.config, 'home_airport_code', '???')
        de = getattr(self.config, 'dest_airport_code', '???')
        lines.append(f"Route: {ac} {ho}-{de}")
        lines.append(f"Bounds profile: {self.bounds.label}")
        lines.append("")

        # Raw vs adjusted
        if result.adjusted:
            lines.append(f"Raw forecast:      {result.raw_total:>10,.0f} pax  "
                        f"{result.raw_load_factor:>6.1%} LF")
            lines.append(f"Adjusted forecast: {result.adjusted_total:>10,.0f} pax  "
                        f"{result.adjusted_load_factor:>6.1%} LF")
            lines.append(f"Adjustments: {result.iterations_used} iterations")
        else:
            lines.append(f"Forecast: {result.raw_total:>10,.0f} pax  "
                        f"{result.raw_load_factor:>6.1%} LF")
            lines.append("No adjustments needed")

        lines.append("")

        # Frequency recommendation
        if result.frequency_rec:
            fr = result.frequency_rec
            lines.append(f"Frequency analysis:")
            lines.append(f"  Current: {fr.current_frequency}x/week -> "
                        f"Recommended: {fr.recommended_frequency}x/week")
            lines.append(f"  Viable range: {fr.min_viable_frequency}x - "
                        f"{fr.max_supportable_frequency}x/week")
            lines.append(f"  {fr.reasoning}")

        lines.append("")

        # Check summary
        passes = sum(1 for c in result.checks if c.status == CheckStatus.PASS)
        warns = sum(1 for c in result.checks if c.status == CheckStatus.WARNING)
        fails = sum(1 for c in result.checks
                    if c.status in (CheckStatus.FAIL, CheckStatus.CRITICAL))
        lines.append(f"Checks: {passes} passed, {warns} warnings, {fails} failures")

        for c in result.checks:
            if c.status != CheckStatus.PASS:
                lines.append(f"  [{c.status.value.upper()}] {c.name}: {c.message}")

        lines.append("")
        lines.append(f"Confidence: {result.confidence_score}/100 - "
                     f"{result.confidence_reasoning}")
        lines.append(f"Analyst review: "
                     f"{'RECOMMENDED' if result.needs_analyst_review else 'Optional'}")
        if result.review_reasons:
            for r in result.review_reasons:
                lines.append(f"  - {r}")

        return lines


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def run_cre(config, pipeline_results: Dict,
            bounds: Optional[CommercialBounds] = None) -> CREResult:
    """Convenience function to run CRE in one call."""
    engine = CommercialReasonablenessEngine(config, pipeline_results, bounds)
    return engine.run()


def print_cre_report(result: CREResult):
    """Print CRE results to console."""
    for line in result.summary:
        print(line)


# =============================================================================
# CLOSED-LOOP RE-RUN ENGINE
# =============================================================================

@dataclass
class RerunRecord:
    """Records one closed-loop re-run attempt."""
    iteration: int
    parameter_changed: str
    old_value: float
    new_value: float
    reason: str
    result_total: float
    result_lf: float
    cre_confidence: int
    cre_adjusted: bool


@dataclass
class ClosedLoopResult:
    """Complete output from the closed-loop re-run process."""
    # Did re-runs happen?
    reruns_performed: int = 0
    max_reruns: int = 3

    # History of each re-run
    rerun_history: List[RerunRecord] = field(default_factory=list)

    # Initial run (before any re-runs)
    initial_results: Dict = field(default_factory=dict)
    initial_cre: Optional[CREResult] = None

    # Final run (after all re-runs)
    final_results: Dict = field(default_factory=dict)
    final_cre: Optional[CREResult] = None

    # Config changes accumulated
    config_changes: Dict = field(default_factory=dict)

    # Did we achieve a reasonable result?
    converged: bool = False
    convergence_note: str = ""

    def to_dict(self) -> Dict:
        return {
            'reruns_performed': self.reruns_performed,
            'converged': self.converged,
            'convergence_note': self.convergence_note,
            'rerun_history': [
                {
                    'iteration': r.iteration,
                    'param': r.parameter_changed,
                    'old': r.old_value,
                    'new': r.new_value,
                    'reason': r.reason,
                    'total': r.result_total,
                    'lf': r.result_lf,
                    'confidence': r.cre_confidence,
                }
                for r in self.rerun_history
            ],
            'config_changes': self.config_changes,
        }


class ClosedLoopRunner:
    """
    Wraps the pipeline + CRE in a closed loop.

    Instead of just scaling the output numbers (which is cosmetic),
    this modifies the actual RouteConfig parameters and re-runs the
    full pipeline. The result is a forecast where the *assumptions*
    are defensible, not just the *answer*.

    ADJUSTMENT PRIORITY (analyst logic):
      1. qsi_adjustment - scales all connecting QSI scores
         Most effective lever: a 0.1 reduction typically cuts connecting
         traffic by 15-25%. This is what an analyst adjusts first.

      2. qsi_ceiling - caps individual city QSI scores
         Prevents outlier cities from inflating totals. Lowering from
         1.0 to 0.6 is common for non-dominant hubs.

      3. frequency - if demand is genuinely low, reduce frequency
         Only used when demand is too low, never to fix overestimates.

    MAX 3 RE-RUNS to prevent infinite loops. If the forecast hasn't
    converged after 3 parameter adjustments, it flags for analyst review.
    """

    MAX_RERUNS = 3

    def __init__(self, config, pipeline_fn, output_path_fn=None,
                 bounds: Optional[CommercialBounds] = None,
                 log_fn=None):
        """
        Args:
            config: RouteConfig object (will be modified in place)
            pipeline_fn: callable that takes (config, output_path) and returns results dict
            output_path_fn: callable that returns a temp file path for output
            bounds: optional CommercialBounds override
            log_fn: optional callable(str) for logging
        """
        self.config = config
        self.pipeline_fn = pipeline_fn
        self.output_path_fn = output_path_fn
        self.bounds = bounds
        self.log = log_fn or (lambda msg: None)

    def _get_output_path(self):
        if self.output_path_fn:
            return self.output_path_fn()
        import tempfile
        return tempfile.mktemp(suffix='.xlsx')

    def _diagnose(self, cre_result: CREResult) -> Optional[dict]:
        """
        Diagnose what parameter to change based on CRE checks.
        Returns dict with 'parameter', 'new_value', 'reason' or None if OK.
        """
        lf = cre_result.adjusted_load_factor if cre_result.adjusted else cre_result.raw_load_factor
        b = cre_result.bounds or CommercialBounds()

        # Case 1: LF too high (most common) - reduce connecting captures
        if lf > b.lf_max_credible:
            current_adj = getattr(self.config, 'qsi_adjustment', 1.0)
            # Calculate what factor would bring LF to target
            target_lf = b.lf_target_high
            reduction_needed = target_lf / lf if lf > 0 else 0.5
            # Apply reduction to qsi_adjustment (conservative: don't go below 0.1)
            new_adj = max(0.10, current_adj * reduction_needed)
            # Don't change by more than 50% at once
            new_adj = max(current_adj * 0.50, new_adj)
            return {
                'parameter': 'qsi_adjustment',
                'old_value': current_adj,
                'new_value': round(new_adj, 3),
                'reason': f"LF {lf:.0%} exceeds {b.lf_max_credible:.0%} ceiling; "
                          f"reducing QSI adjustment from {current_adj:.3f} to {new_adj:.3f}",
            }

        # Case 2: LF moderately high - try qsi_ceiling reduction
        if lf > b.lf_target_high:
            current_ceil = getattr(self.config, 'qsi_ceiling', 1.0)
            if current_ceil > 0.40:
                # Step down ceiling
                new_ceil = max(0.30, current_ceil - 0.15)
                return {
                    'parameter': 'qsi_ceiling',
                    'old_value': current_ceil,
                    'new_value': round(new_ceil, 2),
                    'reason': f"LF {lf:.0%} above target {b.lf_target_high:.0%}; "
                              f"capping QSI ceiling from {current_ceil:.2f} to {new_ceil:.2f}",
                }
            else:
                # Ceiling already low, reduce adjustment instead
                current_adj = getattr(self.config, 'qsi_adjustment', 1.0)
                new_adj = max(0.10, current_adj * 0.80)
                return {
                    'parameter': 'qsi_adjustment',
                    'old_value': current_adj,
                    'new_value': round(new_adj, 3),
                    'reason': f"LF {lf:.0%} still above target with low ceiling; "
                              f"reducing QSI adjustment to {new_adj:.3f}",
                }

        # Case 3: LF too low - suggest frequency reduction (don't inflate demand)
        if lf < b.lf_min_viable:
            current_freq = getattr(self.config, 'frequency', 7)
            if current_freq > 1:
                # Calculate what frequency gives ~70% LF
                total = cre_result.raw_total
                seats = getattr(self.config, 'seats', 214)
                target_cap = total / 0.70 if total > 0 else seats * 52 * 2
                new_freq = max(1, round(target_cap / (seats * 52 * 2)))
                new_freq = max(1, min(new_freq, current_freq - 1))  # At least reduce by 1
                return {
                    'parameter': 'frequency',
                    'old_value': current_freq,
                    'new_value': new_freq,
                    'reason': f"LF {lf:.0%} below viable {b.lf_min_viable:.0%}; "
                              f"reducing frequency from {current_freq}x to {new_freq}x/week",
                }

        # No change needed
        return None

    def run(self) -> ClosedLoopResult:
        """
        Execute the closed-loop: pipeline -> CRE -> diagnose -> adjust -> repeat.
        """
        result = ClosedLoopResult()

        # --- Initial run ---
        self.log("Closed-loop: initial pipeline run")
        output_path = self._get_output_path()
        pipeline_results = self.pipeline_fn(self.config, output_path)
        result.initial_results = copy.deepcopy(pipeline_results)

        initial_cre = run_cre(self.config, pipeline_results, self.bounds)
        result.initial_cre = initial_cre
        self.log(f"  Initial: {pipeline_results['grand_total']:,.0f} pax, "
                 f"{pipeline_results.get('load_factor', 0):.1%} LF, "
                 f"CRE confidence {initial_cre.confidence_score}/100")

        # Check if initial run is already reasonable
        has_critical = any(
            c.status in (CheckStatus.FAIL, CheckStatus.CRITICAL)
            for c in initial_cre.checks
        )
        if not has_critical:
            result.final_results = pipeline_results
            result.final_cre = initial_cre
            result.converged = True
            result.convergence_note = "Initial run passed all CRE checks"
            self.log("  No re-runs needed - forecast within bounds")
            return result

        # --- Re-run loop ---
        current_results = pipeline_results
        current_cre = initial_cre

        for iteration in range(1, self.MAX_RERUNS + 1):
            diagnosis = self._diagnose(current_cre)
            if diagnosis is None:
                result.converged = True
                result.convergence_note = f"Converged after {iteration - 1} re-runs"
                break

            # Apply the parameter change
            param = diagnosis['parameter']
            old_val = diagnosis['old_value']
            new_val = diagnosis['new_value']
            reason = diagnosis['reason']

            self.log(f"  Re-run {iteration}: {param} {old_val} -> {new_val} ({reason})")
            setattr(self.config, param, new_val)
            result.config_changes[param] = {
                'original': result.config_changes.get(param, {}).get('original', old_val),
                'final': new_val,
            }

            # Re-run pipeline
            output_path = self._get_output_path()
            current_results = self.pipeline_fn(self.config, output_path)

            # Re-run CRE
            current_cre = run_cre(self.config, current_results, self.bounds)

            # Record
            rerun_rec = RerunRecord(
                iteration=iteration,
                parameter_changed=param,
                old_value=old_val,
                new_value=new_val,
                reason=reason,
                result_total=current_results.get('grand_total', 0),
                result_lf=current_results.get('load_factor', 0),
                cre_confidence=current_cre.confidence_score,
                cre_adjusted=current_cre.adjusted,
            )
            result.rerun_history.append(rerun_rec)
            result.reruns_performed = iteration

            self.log(f"    -> {current_results['grand_total']:,.0f} pax, "
                     f"{current_results.get('load_factor', 0):.1%} LF, "
                     f"CRE confidence {current_cre.confidence_score}/100")

            # Check if we've converged
            has_critical = any(
                c.status in (CheckStatus.FAIL, CheckStatus.CRITICAL)
                for c in current_cre.checks
            )
            if not has_critical:
                result.converged = True
                result.convergence_note = f"Converged after {iteration} re-run(s)"
                self.log(f"  Converged after {iteration} re-run(s)")
                break

        if not result.converged:
            result.convergence_note = (
                f"Did not converge after {self.MAX_RERUNS} re-runs. "
                f"Analyst review required."
            )
            self.log(f"  WARNING: did not converge after {self.MAX_RERUNS} re-runs")

        result.final_results = current_results
        result.final_cre = current_cre
        return result


def run_closed_loop(config, pipeline_fn, output_path_fn=None,
                    bounds=None, log_fn=None) -> ClosedLoopResult:
    """Convenience function for closed-loop execution."""
    runner = ClosedLoopRunner(config, pipeline_fn, output_path_fn, bounds, log_fn)
    return runner.run()


# =============================================================================
# SELF-TEST
# =============================================================================

if __name__ == '__main__':
    print("Commercial Reasonableness Engine - Self Test")
    print("=" * 50)

    class MockConfig:
        airline_code = 'LX'
        home_airport_code = 'TPE'
        dest_airport_code = 'ZRH'
        frequency = 7
        seats = 214
        aircraft_type = '787'
        carrier_type = 'Full Service'
        route_type = 'Hub Long-Haul'
        hub_status = 'Major Hub'
        is_new_route = True

        @property
        def annual_capacity(self):
            return self.seats * self.frequency * 52 * 2

    config = MockConfig()

    # Test 1: Overestimated forecast (150% LF)
    cap = config.annual_capacity
    r1 = {'p2p_total': 30000, 'home_total': 120000, 'dest_total': 80000,
          'grand_total': 230000, 'load_factor': 230000 / cap,
          'home_results': [], 'dest_results': []}
    print(f"\nTest 1 (overestimated): {r1['load_factor']:.1%} LF")
    cre1 = CommercialReasonablenessEngine(config, r1)
    res1 = cre1.run()
    print(f"  -> {res1.adjusted_total:,.0f} pax, {res1.adjusted_load_factor:.1%} LF")
    print(f"  Iterations: {res1.iterations_used}, Confidence: {res1.confidence_score}/100")

    # Test 2: Underestimated (30% LF)
    r2 = {'p2p_total': 15000, 'home_total': 20000, 'dest_total': 10000,
          'grand_total': 45000, 'load_factor': 45000 / cap,
          'home_results': [], 'dest_results': []}
    print(f"\nTest 2 (underestimated): {r2['load_factor']:.1%} LF")
    cre2 = CommercialReasonablenessEngine(config, r2)
    res2 = cre2.run()
    print(f"  -> {res2.adjusted_total:,.0f} pax, {res2.adjusted_load_factor:.1%} LF")
    if res2.frequency_rec:
        print(f"  Freq rec: {res2.frequency_rec.recommended_frequency}x/week "
              f"(from {res2.frequency_rec.current_frequency}x)")
    print(f"  Confidence: {res2.confidence_score}/100")

    # Test 3: Reasonable (80% LF)
    r3 = {'p2p_total': 40000, 'home_total': 55000, 'dest_total': 30000,
          'grand_total': 125000, 'load_factor': 125000 / cap,
          'home_results': [], 'dest_results': []}
    print(f"\nTest 3 (reasonable): {r3['load_factor']:.1%} LF")
    cre3 = CommercialReasonablenessEngine(config, r3)
    res3 = cre3.run()
    print(f"  -> Adjusted: {res3.adjusted}, Confidence: {res3.confidence_score}/100")

    # Test 4: BA LHR-SJC benchmark
    c4 = MockConfig()
    c4.airline_code = 'BA'
    c4.home_airport_code = 'LHR'
    c4.dest_airport_code = 'SJC'
    c4.frequency = 7
    c4.seats = 214
    cap4 = c4.annual_capacity
    r4 = {'p2p_total': 78110, 'home_total': 48115, 'dest_total': 2937,
          'grand_total': 129162, 'load_factor': 129162 / cap4,
          'home_results': [], 'dest_results': []}
    print(f"\nTest 4 (BA LHR-SJC): {r4['load_factor']:.1%} LF")
    cre4 = CommercialReasonablenessEngine(c4, r4)
    res4 = cre4.run()
    print(f"  -> Adjusted: {res4.adjusted}, Confidence: {res4.confidence_score}/100")
    if res4.frequency_rec:
        print(f"  Freq rec: {res4.frequency_rec.recommended_frequency}x/week")

    print("\n=== All tests complete ===")
