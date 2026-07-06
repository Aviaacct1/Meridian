#!/usr/bin/env python3
"""
Avia Solutions  Calibration Factor Model (Chat 13)
=====================================================
Predicts the expert calibration adjustment factor for connecting cities.

The calibration factor is the ratio of expert-selected QSI capture rate
to the raw pipeline-computed QSI capture rate. When the pipeline computes
a raw capture rate of 0.25 for Paris, and the expert sets 0.04, the 
calibration factor is 0.04 / 0.25 = 0.16.

KEY FINDING: Machine learning models (Ridge, Random Forest, GBR) all 
perform WORSE than predicting the median for all cities. This is because
calibration factors are driven by expert judgment about market-specific 
conditions (BA's commercial relationships, historical booking patterns,
route-specific competitive dynamics) that aren't captured in the available 
features. With 77 data points and high variance (0.025 to 1.382), there's
insufficient signal for statistical learning.

PRACTICAL APPROACH: A tiered default system using competitive intensity
and hub status reduces MAE by 41% vs the single-median baseline. This is
the recommended approach for the automated system:
    - Load the tier-appropriate default
    - Flag outlier cities where the default may be particularly unreliable
    - Allow analyst override for every city
    - Log every override for learning over time

As the system processes 30-50+ routes, the per-city calibration history
will eventually provide enough data for statistical learning. Until then,
tiered defaults + expert override is the honest answer.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


# ============================================================================
# CALIBRATION TIERS
# ============================================================================

@dataclass
class CalibrationTier:
    """Default calibration factor for a tier of cities."""
    name: str
    description: str
    default: float          # Median calibration factor for this tier
    lower_bound: float      # 25th percentile  below this, flag as unusual
    upper_bound: float      # 75th percentile  above this, flag as unusual
    sample_size: int        # Number of cities in training data
    mae: float              # Mean absolute error when using this default


# Tiers derived from BA LHR-SJC calibration dataset (77 cities)
CALIBRATION_TIERS = {
    'T1_Major_Hub': CalibrationTier(
        name='T1_Major_Hub',
        description='Destination is a major international connecting hub '
                    '(PAR, AMS, FRA, DXB, DOH, IST, SIN, HKG, BKK, NRT, ICN, JNB, DEL, BOM, PEK, SHA)',
        default=0.173,
        lower_bound=0.121,
        upper_bound=0.195,
        sample_size=9,
        mae=0.062,
    ),
    'T2_High_Competition': CalibrationTier(
        name='T2_High_Competition',
        description='Market QSI > 30: many competing routing options through multiple hubs',
        default=0.224,
        lower_bound=0.137,
        upper_bound=0.309,
        sample_size=17,
        mae=0.086,
    ),
    'T3_Medium_Competition': CalibrationTier(
        name='T3_Medium_Competition',
        description='Market QSI 10-30: moderate competition from a few hub alternatives',
        default=0.314,
        lower_bound=0.207,
        upper_bound=0.420,
        sample_size=22,
        mae=0.117,
    ),
    'T4_Low_Competition': CalibrationTier(
        name='T4_Low_Competition',
        description='Market QSI < 10: limited routing alternatives, BA/LHR dominant',
        default=0.265,
        lower_bound=0.153,
        upper_bound=0.411,
        sample_size=29,
        mae=0.110,
    ),
}


# Major hub city codes  cities that are themselves major connecting hubs
# where passengers have many alternative routings, suppressing any single
# carrier's capture rate
MAJOR_HUB_CITIES = {
    'PAR', 'AMS', 'FRA', 'ROM', 'MAD', 'IST', 'DXB', 'DOH',
    'SIN', 'HKG', 'BKK', 'NRT', 'ICN', 'JNB', 'DEL', 'BOM',
    'PEK', 'SHA',
}


# ============================================================================
# TIER CLASSIFICATION
# ============================================================================

def classify_city(city_code: str, market_qsi: float = 0,
                  is_major_hub: Optional[bool] = None) -> str:
    """
    Classify a city into a calibration tier.
    
    Args:
        city_code: IATA city code
        market_qsi: Total market QSI (sum of all competing routings)
        is_major_hub: Override for hub status. If None, uses built-in list.
    
    Returns:
        Tier name string (T1_Major_Hub, T2_High_Competition, etc.)
    """
    if is_major_hub is None:
        is_major_hub = city_code in MAJOR_HUB_CITIES
    
    if is_major_hub:
        return 'T1_Major_Hub'
    elif market_qsi > 30:
        return 'T2_High_Competition'
    elif market_qsi > 10:
        return 'T3_Medium_Competition'
    else:
        return 'T4_Low_Competition'


def get_default_factor(city_code: str, market_qsi: float = 0,
                       is_major_hub: Optional[bool] = None) -> Tuple[float, CalibrationTier]:
    """
    Get the default calibration factor for a city.
    
    Returns:
        (default_factor, tier_info)
    """
    tier_name = classify_city(city_code, market_qsi, is_major_hub)
    tier = CALIBRATION_TIERS[tier_name]
    return tier.default, tier


# ============================================================================
# CALIBRATION RESULT
# ============================================================================

@dataclass
class CityCalibration:
    """Calibration result for a single city."""
    city_code: str
    city_name: str
    country: str
    tier: str
    default_factor: float
    applied_factor: float      # What was actually used (default or override)
    override: bool = False     # True if analyst overrode the default
    pipeline_qsi: float = 0.0
    expert_qsi: float = 0.0   # From historical data, if available
    base_demand: float = 0.0
    market_qsi: float = 0.0
    flag: str = ''             # Warning flag if unusual


@dataclass
class CalibrationReport:
    """Full calibration report for a route assessment."""
    route: str
    n_cities: int
    n_overrides: int
    cities: List[CityCalibration] = field(default_factory=list)
    tier_distribution: Dict[str, int] = field(default_factory=dict)
    mae_vs_expert: float = 0.0  # If expert data available
    
    def summary(self) -> str:
        """One-line summary."""
        return (f"{self.route}: {self.n_cities} cities, {self.n_overrides} overrides, "
                f"tiers={dict(self.tier_distribution)}")


# ============================================================================
# CALIBRATION ENGINE
# ============================================================================

class CalibrationEngine:
    """
    Applies calibration factors to pipeline QSI captures.
    
    Usage:
        engine = CalibrationEngine()
        
        # Apply defaults to all cities
        calibrated = engine.calibrate(city_captures, city_metadata)
        
        # Override specific cities
        engine.set_override('PAR', 0.04)
        engine.set_override('FRA', 0.02)
        calibrated = engine.calibrate(city_captures, city_metadata)
    """
    
    def __init__(self):
        self.overrides: Dict[str, float] = {}
        self.audit: List[str] = []
    
    def set_override(self, city_code: str, factor: float):
        """Set an analyst override for a specific city's calibration factor."""
        self.overrides[city_code] = factor
    
    def clear_overrides(self):
        """Remove all analyst overrides."""
        self.overrides = {}
    
    def calibrate(self, pipeline_captures: Dict[str, float],
                  city_metadata: Dict[str, Dict],
                  market_qsi: Dict[str, float] = None) -> Tuple[Dict[str, float], CalibrationReport]:
        """
        Apply calibration factors to pipeline QSI captures.
        
        Args:
            pipeline_captures: {city_code: raw_pipeline_capture_rate}
            city_metadata: {city_code: {'name': str, 'country': str, 'base_demand': float}}
            market_qsi: {city_code: total_market_qsi} (for tier classification)
        
        Returns:
            (calibrated_captures, calibration_report)
        """
        if market_qsi is None:
            market_qsi = {}
        
        self.audit = []
        self.audit.append(f"Calibration Engine: {len(pipeline_captures)} cities")
        
        calibrated = {}
        report_cities = []
        tier_dist = defaultdict(int)
        n_overrides = 0
        
        for city_code, raw_capture in pipeline_captures.items():
            meta = city_metadata.get(city_code, {})
            mkt_qsi = market_qsi.get(city_code, 0)
            
            # Classify
            tier_name = classify_city(city_code, mkt_qsi)
            tier = CALIBRATION_TIERS[tier_name]
            tier_dist[tier_name] += 1
            
            # Apply override or default
            is_override = city_code in self.overrides
            if is_override:
                factor = self.overrides[city_code]
                n_overrides += 1
            else:
                factor = tier.default
            
            # Compute calibrated capture
            calibrated_capture = raw_capture * factor
            calibrated[city_code] = calibrated_capture
            
            # Flag unusual situations
            flag = ''
            if not is_override:
                if factor < tier.lower_bound * 0.5 or factor > tier.upper_bound * 2:
                    flag = 'EXTREME_OUTLIER'
                elif raw_capture > 0.5:
                    flag = 'HIGH_RAW_QSI'
                elif raw_capture < 0.01:
                    flag = 'LOW_RAW_QSI'
            
            report_cities.append(CityCalibration(
                city_code=city_code,
                city_name=meta.get('name', ''),
                country=meta.get('country', ''),
                tier=tier_name,
                default_factor=tier.default,
                applied_factor=factor,
                override=is_override,
                pipeline_qsi=raw_capture,
                base_demand=meta.get('base_demand', 0),
                market_qsi=mkt_qsi,
                flag=flag,
            ))
        
        # Sort by forecast impact (demand * capture)
        report_cities.sort(key=lambda c: -(c.base_demand * c.applied_factor * c.pipeline_qsi))
        
        report = CalibrationReport(
            route='',
            n_cities=len(report_cities),
            n_overrides=n_overrides,
            cities=report_cities,
            tier_distribution=dict(tier_dist),
        )
        
        self.audit.append(f"  Tiers: {dict(tier_dist)}")
        self.audit.append(f"  Overrides: {n_overrides}")
        self.audit.append(f"  Flags: {sum(1 for c in report_cities if c.flag)}")
        
        return calibrated, report


# ============================================================================
# VALIDATION AGAINST EXPERT DATA
# ============================================================================

def validate_calibration(report: CalibrationReport,
                         expert_captures: Dict[str, float]) -> Dict:
    """
    Compare calibrated captures against expert-selected values.
    
    Args:
        report: CalibrationReport from calibrate()
        expert_captures: {city_code: expert_qsi_capture_rate}
    
    Returns:
        Validation metrics dict
    """
    errors = []
    comparisons = []
    
    for city_cal in report.cities:
        expert = expert_captures.get(city_cal.city_code)
        if expert is None or expert == 0:
            continue
        
        predicted = city_cal.pipeline_qsi * city_cal.applied_factor
        error = abs(predicted - expert)
        pct_error = error / expert if expert > 0 else 0
        
        errors.append(error)
        comparisons.append({
            'city': city_cal.city_code,
            'name': city_cal.city_name,
            'tier': city_cal.tier,
            'pipeline_qsi': city_cal.pipeline_qsi,
            'factor': city_cal.applied_factor,
            'predicted': predicted,
            'expert': expert,
            'error': error,
            'pct_error': pct_error,
            'override': city_cal.override,
        })
    
    if not errors:
        return {'matched': 0}
    
    comparisons.sort(key=lambda x: -x['error'])
    
    return {
        'matched': len(errors),
        'mae': sum(errors) / len(errors),
        'median_ae': sorted(errors)[len(errors) // 2],
        'max_error': max(errors),
        'worst_cities': comparisons[:5],
        'best_cities': comparisons[-5:],
        'all_comparisons': comparisons,
    }


# ============================================================================
# TRAINING DATA ACCUMULATOR
# ============================================================================

class CalibrationTrainingData:
    """
    Accumulates calibration data across route assessments for future
    statistical learning.
    
    Once 30-50 routes are processed, there will be enough data to train
    per-city or per-tier models that can predict calibration factors from
    city characteristics with reasonable accuracy.
    
    Training record format:
        {
            'route': 'BA LHR-SJC',
            'city': 'PAR',
            'carrier': 'BA',
            'hub': 'LHR',
            'pipeline_qsi': 0.231,
            'expert_qsi': 0.040,
            'calibration_factor': 0.173,
            'market_qsi': 79.6,
            'base_demand': 129349,
            'tier': 'T1_Major_Hub',
            'n_routes': 5,
            'distance_km': 340,
            'region': 'W_Europe',
        }
    """
    
    def __init__(self):
        self.records: List[Dict] = []
    
    def add_route(self, route_name: str, carrier: str, hub: str,
                  pipeline_captures: Dict[str, float],
                  expert_captures: Dict[str, float],
                  city_metadata: Dict[str, Dict],
                  market_qsi: Dict[str, float] = None):
        """Add calibration data from a completed route assessment."""
        if market_qsi is None:
            market_qsi = {}
        
        for city_code, pipe_qsi in pipeline_captures.items():
            expert = expert_captures.get(city_code)
            if expert is None or pipe_qsi == 0:
                continue
            
            meta = city_metadata.get(city_code, {})
            mkt = market_qsi.get(city_code, 0)
            
            self.records.append({
                'route': route_name,
                'city': city_code,
                'carrier': carrier,
                'hub': hub,
                'pipeline_qsi': pipe_qsi,
                'expert_qsi': expert,
                'calibration_factor': expert / pipe_qsi,
                'market_qsi': mkt,
                'base_demand': meta.get('base_demand', 0),
                'tier': classify_city(city_code, mkt),
                'n_routes': meta.get('n_routes', 0),
                'distance_km': meta.get('distance_km', 0),
                'region': meta.get('region', ''),
            })
    
    @property
    def n_routes(self) -> int:
        """Number of distinct routes in training data."""
        return len(set(r['route'] for r in self.records))
    
    @property
    def n_cities(self) -> int:
        """Number of distinct cities in training data."""
        return len(set(r['city'] for r in self.records))
    
    @property
    def ready_for_learning(self) -> bool:
        """True if enough data for statistical learning (30+ routes)."""
        return self.n_routes >= 30
    
    def tier_summary(self) -> Dict[str, Dict]:
        """Summarise calibration factors by tier across all routes."""
        tier_data = defaultdict(list)
        for r in self.records:
            tier_data[r['tier']].append(r['calibration_factor'])
        
        summary = {}
        for tier, factors in tier_data.items():
            factors.sort()
            n = len(factors)
            summary[tier] = {
                'count': n,
                'mean': sum(factors) / n,
                'median': factors[n // 2],
                'p25': factors[n // 4],
                'p75': factors[3 * n // 4],
                'min': factors[0],
                'max': factors[-1],
            }
        return summary


# ============================================================================
# CLI TEST
# ============================================================================

def main():
    """Test calibration engine against BA LHR-SJC data."""
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    
    from route_config import RouteConfig
    from closed_loop_pipeline_v2 import QSIEngine
    
    print("=" * 60)
    print("CALIBRATION FACTOR MODEL  Test against BA LHR-SJC")
    print("=" * 60)
    
    # Run pipeline to get raw captures
    config = RouteConfig.ba_lhr_sjc('/mnt/project')
    qsi_engine = QSIEngine(config)
    pipeline_captures = qsi_engine.run(config.schedule_provider)
    
    # Get expert data from demand provider
    home_cities = config.demand_provider.get_connecting_cities('home')
    expert_captures = {c.city_code: c.qsi_score for c in home_cities if c.qsi_score > 0}
    city_metadata = {
        c.city_code: {
            'name': c.city_name,
            'country': c.country,
            'base_demand': c.base_demand,
        } for c in home_cities
    }
    
    # Get market QSI from bidir data
    market_qsi = {}
    for city_code in pipeline_captures:
        for rl, data in qsi_engine.bidir.items():
            if data['city'] == city_code:
                market_qsi[city_code] = data['q1_market']
                break
    
    # Apply calibration
    engine = CalibrationEngine()
    calibrated, report = engine.calibrate(pipeline_captures, city_metadata, market_qsi)
    
    print(f"\n{report.summary()}")
    print(f"\nTier distribution: {report.tier_distribution}")
    
    # Validate against expert
    validation = validate_calibration(report, expert_captures)
    
    print(f"\nValidation against expert data:")
    print(f"  Matched: {validation['matched']} cities")
    print(f"  MAE:     {validation['mae']:.4f}")
    print(f"  Median:  {validation['median_ae']:.4f}")
    
    # Compare with no calibration (raw pipeline) and with single median
    raw_errors = []
    median_errors = []
    tiered_errors = []
    median_factor = 0.267  # From analysis
    
    for comp in validation['all_comparisons']:
        raw_errors.append(abs(comp['pipeline_qsi'] - comp['expert']))
        median_errors.append(abs(comp['pipeline_qsi'] * median_factor - comp['expert']))
        tiered_errors.append(abs(comp['predicted'] - comp['expert']))
    
    n = len(raw_errors)
    print(f"\n  Model comparison ({n} cities):")
    print(f"    Raw pipeline (no calibration):   MAE = {sum(raw_errors)/n:.4f}")
    print(f"    Single median ({median_factor}):        MAE = {sum(median_errors)/n:.4f}")
    print(f"    Tiered defaults:                 MAE = {sum(tiered_errors)/n:.4f}")
    
    print(f"\n  Worst 5 predictions:")
    for c in validation['worst_cities']:
        print(f"    {c['city']:5s} {c['name']:20s} pred={c['predicted']:.4f} "
              f"expert={c['expert']:.4f} err={c['error']:.4f} tier={c['tier']}")
    
    # Compute forecast impact
    print(f"\n  Forecast impact (pax difference vs expert):")
    total_tiered = 0
    total_expert = 0
    for c in validation['all_comparisons']:
        meta = city_metadata.get(c['city'], {})
        demand = meta.get('base_demand', 0) * 1.09  # grown demand
        tiered_pax = demand * c['predicted']
        expert_pax = demand * c['expert']
        total_tiered += tiered_pax
        total_expert += expert_pax
    
    print(f"    Tiered defaults total: {total_tiered:,.0f}")
    print(f"    Expert total:          {total_expert:,.0f}")
    print(f"    Difference:            {total_tiered - total_expert:+,.0f} "
          f"({(total_tiered/total_expert - 1)*100:+.1f}%)")
    
    return calibrated, report, validation


if __name__ == '__main__':
    main()
