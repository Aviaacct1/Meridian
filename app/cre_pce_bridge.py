#!/usr/bin/env python3
"""
Avia Solutions - CRE-PCE Integration Bridge
=============================================
Connects the Commercial Reasonableness Engine (CRE) to the
Predictive Calibration Engine (PCE) for intelligent parameter
adjustment during closed-loop forecast iteration.

PURPOSE:
  When the CRE identifies that a forecast is unreasonable (e.g.,
  150% LF, impossible connecting shares), the bridge module consults
  the PCE's calibration library knowledge to determine what parameter
  values are appropriate for this route type, rather than using the
  CRE's hardcoded scaling rules.

  This produces forecasts where the *assumptions* are defensible,
  not just the *answer*.

ARCHITECTURE:
  1. PCE suggests initial parameters before first pipeline run
  2. CRE checks the output after the run
  3. Bridge interprets CRE failures and maps them to PCE parameters
  4. Bridge computes informed adjustments using PCE's knowledge
  5. ClosedLoopRunner applies the changes and re-runs

  The bridge replaces the ClosedLoopRunner's _diagnose() method
  with a PCE-informed version that knows what parameter ranges are
  sensible for this specific route profile.

INTEGRATION POINTS:
  - Called from the portal after pipeline run if closed-loop is enabled
  - Uses PCE's CalibrationSuggestion to bound parameter adjustments
  - Feeds back into RouteConfig for re-runs
  - Records all adjustments for assumptions log transparency

LAST UPDATED: February 2026
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import copy
import math


# =============================================================================
# IMPORTS - graceful degradation if either engine unavailable
# =============================================================================

try:
    from commercial_reasonableness_engine import (
        CommercialReasonablenessEngine, CREResult, CommercialBounds,
        CheckStatus, run_cre, get_bounds_for_route_type,
        ClosedLoopRunner, ClosedLoopResult, RerunRecord,
    )
    HAS_CRE = True
except ImportError:
    HAS_CRE = False

try:
    from predictive_calibration_engine import (
        PredictiveCalibrationEngine, RouteProfile, CalibrationSuggestion,
        SegmentSuggestion, from_route_config, quick_predict,
    )
    HAS_PCE = True
except ImportError:
    HAS_PCE = False


# =============================================================================
# DIAGNOSTIC CATEGORY - what kind of problem the CRE found
# =============================================================================

class DiagnosticCategory(Enum):
    """Categories of CRE failure mapped to parameter adjustments."""
    LF_TOO_HIGH = "lf_too_high"             # Most common: overestimated demand
    LF_TOO_LOW = "lf_too_low"               # Underestimated or frequency too high
    LF_MODERATELY_HIGH = "lf_moderately_high"  # Above target but not critical
    CNX_SHARE_TOO_HIGH = "cnx_share_too_high"  # Connecting dominates unrealistically
    CNX_SHARE_TOO_LOW = "cnx_share_too_low"    # Connecting underrepresented
    P2P_SHARE_IMPLAUSIBLE = "p2p_implausible"  # P2P share outside expected range
    ZERO_COMPONENT = "zero_component"         # Missing P2P or connecting entirely
    CITY_OUTLIERS = "city_outliers"            # Individual city captures implausible
    MULTIPLE_FAILURES = "multiple_failures"    # More than one critical check failed


# =============================================================================
# DIAGNOSIS RESULT - maps a CRE failure to a parameter change
# =============================================================================

@dataclass
class InformedDiagnosis:
    """PCE-informed parameter change recommendation."""
    category: DiagnosticCategory
    parameter: str                   # RouteConfig attribute to change
    old_value: float
    new_value: float
    reason: str
    pce_range: Tuple[float, float]   # What the PCE says is reasonable
    confidence: str                  # How confident the PCE is in this range
    priority: int = 1                # 1=highest (adjust first), 3=lowest


# =============================================================================
# MAIN BRIDGE CLASS
# =============================================================================

class CREPCEBridge:
    """
    Bridges CRE diagnostics with PCE parameter knowledge.
    
    Instead of the CRE's hardcoded adjustment rules (e.g., "reduce
    QSI by 20%"), the bridge asks the PCE "what QSI adjustment is
    typical for a route with these characteristics?" and adjusts
    toward that informed target.
    
    This means:
    - New routes get parameters learned from 22+ historical cases
    - Adjustments are bounded by what's been observed in practice
    - The assumptions log can cite comparable cases as justification
    """
    
    def __init__(self, config, pce_suggestion: Optional['CalibrationSuggestion'] = None):
        """
        Args:
            config: RouteConfig object
            pce_suggestion: Optional pre-computed PCE suggestion. If not provided,
                           the bridge will generate one from the config.
        """
        self.config = config
        self._suggestion = pce_suggestion
        self._profile = None
    
    @property
    def suggestion(self) -> Optional['CalibrationSuggestion']:
        """Lazy-load PCE suggestion if not provided."""
        if self._suggestion is None and HAS_PCE:
            try:
                self._profile = from_route_config(self.config)
                engine = PredictiveCalibrationEngine()
                self._suggestion = engine.predict(self._profile)
            except Exception:
                self._suggestion = None
        return self._suggestion
    
    def diagnose(self, cre_result: CREResult) -> Optional[InformedDiagnosis]:
        """
        Interpret CRE failures and produce a PCE-informed parameter adjustment.
        
        Returns None if no adjustment needed (all checks pass).
        """
        if cre_result is None:
            return None
        
        # Classify the type of failure
        category = self._classify_failure(cre_result)
        if category is None:
            return None
        
        # Get the PCE suggestion for this route
        sug = self.suggestion
        
        # Route to the appropriate handler
        handlers = {
            DiagnosticCategory.LF_TOO_HIGH: self._handle_lf_too_high,
            DiagnosticCategory.LF_MODERATELY_HIGH: self._handle_lf_moderately_high,
            DiagnosticCategory.LF_TOO_LOW: self._handle_lf_too_low,
            DiagnosticCategory.CNX_SHARE_TOO_HIGH: self._handle_cnx_share_high,
            DiagnosticCategory.CNX_SHARE_TOO_LOW: self._handle_cnx_share_low,
            DiagnosticCategory.CITY_OUTLIERS: self._handle_city_outliers,
            DiagnosticCategory.ZERO_COMPONENT: self._handle_zero_component,
            DiagnosticCategory.MULTIPLE_FAILURES: self._handle_multiple_failures,
        }
        
        handler = handlers.get(category, self._handle_lf_too_high)
        return handler(cre_result, sug)
    
    def _classify_failure(self, cre_result: CREResult) -> Optional[DiagnosticCategory]:
        """Map CRE check results to a diagnostic category.
        
        IMPORTANT: Also check raw_load_factor directly, because the CRE
        may internally adjust numbers making its checks pass even when
        the raw pipeline output is unreasonable.
        """
        # First check raw LF directly (bypass CRE adjustments)
        raw_lf = getattr(cre_result, 'raw_load_factor', 0)
        bounds = cre_result.bounds or CommercialBounds()
        if raw_lf > getattr(bounds, 'lf_max_credible', 0.95):
            return DiagnosticCategory.LF_TOO_HIGH
        if raw_lf > getattr(bounds, 'lf_target_high', 0.85):
            return DiagnosticCategory.LF_MODERATELY_HIGH
        if raw_lf < getattr(bounds, 'lf_min_viable', 0.50) and raw_lf > 0:
            return DiagnosticCategory.LF_TOO_LOW

        # Then check CRE checks for other issues
        failures = [c for c in cre_result.checks
                    if c.status in (CheckStatus.FAIL, CheckStatus.CRITICAL)]
        
        if not failures:
            return None
        
        if len(failures) > 2:
            return DiagnosticCategory.MULTIPLE_FAILURES
        
        # Classify by the most critical failure
        for check in failures:
            name_lower = check.name.lower()
            if 'load factor' in name_lower:
                lf = check.actual_value
                bounds = cre_result.bounds or CommercialBounds()
                lf_max = getattr(bounds, 'lf_max_credible', 0.95)
                lf_target = getattr(bounds, 'lf_target_high', 0.85)
                if lf > lf_max:
                    return DiagnosticCategory.LF_TOO_HIGH
                elif lf > lf_target:
                    return DiagnosticCategory.LF_MODERATELY_HIGH
                elif lf < getattr(bounds, 'lf_min_viable', 0.50):
                    return DiagnosticCategory.LF_TOO_LOW
            elif 'connecting share' in name_lower or 'connecting balance' in name_lower:
                if check.actual_value > check.acceptable_range[1]:
                    return DiagnosticCategory.CNX_SHARE_TOO_HIGH
                else:
                    return DiagnosticCategory.CNX_SHARE_TOO_LOW
            elif 'p2p share' in name_lower:
                return DiagnosticCategory.P2P_SHARE_IMPLAUSIBLE
            elif 'zero' in name_lower:
                return DiagnosticCategory.ZERO_COMPONENT
            elif 'outlier' in name_lower or 'capture' in name_lower:
                return DiagnosticCategory.CITY_OUTLIERS
        
        # Default: if we got here, most likely an LF issue
        lf = cre_result.raw_load_factor
        if lf > 0.85:
            return DiagnosticCategory.LF_TOO_HIGH
        elif lf < 0.50:
            return DiagnosticCategory.LF_TOO_LOW
        return DiagnosticCategory.LF_MODERATELY_HIGH
    
    # -------------------------------------------------------------------------
    # HANDLERS: Each failure type maps to a specific parameter adjustment
    # -------------------------------------------------------------------------
    
    def _handle_lf_too_high(self, cre_result: CREResult, sug) -> InformedDiagnosis:
        """
        LF critically high (>95%). Primary lever: QSI adjustment.
        
        Uses PURE proportional reduction to target LF. The PCE suggestion is
        logged for reference but never overrides proportional arithmetic.
        
        Previous versions blended PCE with proportional and bounded by PCE range,
        which caused oscillation: PCE pulled adjustment up while LF needed it down.
        """
        current_adj = getattr(self.config, 'qsi_adjustment', 1.0)
        lf = cre_result.raw_load_factor
        bounds = cre_result.bounds or CommercialBounds()
        target_lf = getattr(bounds, 'lf_target_high', 0.85)
        
        # Proportional adjustment accounting for fixed P2P component.
        # P2P doesn't change with QSI adjustment — only connecting does.
        # target_total = target_lf * capacity
        # connecting_needed = target_total - p2p
        # new_adj = adj_current * (connecting_needed / connecting_current)
        if lf > 0:
            capacity = getattr(self.config, 'annual_capacity', 0)
            raw = cre_result.raw_results if hasattr(cre_result, 'raw_results') else {}
            p2p_total = raw.get('p2p_total', 0)
            cnx_total = raw.get('home_total', 0) + raw.get('dest_total', 0)
            
            if capacity > 0 and cnx_total > 0 and p2p_total > 0:
                target_total = target_lf * capacity
                cnx_needed = max(0, target_total - p2p_total)
                new_adj = current_adj * (cnx_needed / cnx_total)
            else:
                # Fallback to simple proportional if components unknown
                new_adj = current_adj * (target_lf / lf)
        else:
            new_adj = 0.5
        
        # Floor at 0.05 (never zero out the forecast entirely)
        new_adj = max(0.05, new_adj)
        
        # Log PCE for reference but don't let it override
        pce_info = ""
        pce_range = (0.05, 1.0)
        if sug is not None:
            pce_adj = sug.qsi_adjustment
            pce_range = (max(0.05, pce_adj * 0.5), min(1.0, pce_adj * 1.5))
            pce_info = f" PCE suggests {pce_adj:.3f} (advisory, not applied)."
            confidence = sug.confidence
        else:
            confidence = "LOW"
        
        reason = (f"LF {lf:.0%} too high. "
                 f"Proportional: {current_adj:.3f} * ({target_lf:.0%}/{lf:.0%}) = {new_adj:.3f}."
                 f"{pce_info}")
        
        return InformedDiagnosis(
            category=DiagnosticCategory.LF_TOO_HIGH,
            parameter='qsi_adjustment',
            old_value=current_adj,
            new_value=round(new_adj, 3),
            reason=reason,
            pce_range=pce_range,
            confidence=confidence,
            priority=1,
        )
    
    def _handle_lf_moderately_high(self, cre_result: CREResult, sug) -> InformedDiagnosis:
        """
        LF above target (85-95%). Primary lever: QSI ceiling.
        
        The ceiling caps individual city QSI scores. Lowering it
        prevents outlier cities from inflating the total while
        preserving the overall QSI structure.
        """
        current_ceil = getattr(self.config, 'qsi_ceiling', 1.0)
        lf = cre_result.raw_load_factor
        bounds = cre_result.bounds or CommercialBounds()
        
        if sug is not None:
            # PCE informs what QSI adj is typical  if current ceiling
            # is already at or below PCE suggestion, use qsi_adjustment instead
            if current_ceil <= 0.40:
                return self._handle_lf_too_high(cre_result, sug)
            
            # Step down ceiling proportionally
            target_lf = getattr(bounds, 'lf_target_high', 0.85)
            overshoot = (lf - target_lf) / target_lf  # e.g., 0.12 for 95% vs 85%
            reduction = min(0.20, overshoot * 0.50)  # Cap at 0.20 step
            new_ceil = max(0.30, current_ceil - reduction)
            
            pce_range = (0.30, 0.90)
            confidence = sug.confidence
            reason = (f"LF {lf:.0%} moderately above target. "
                     f"Reducing QSI ceiling from {current_ceil:.2f} to {new_ceil:.2f} "
                     f"to cap outlier city contributions")
        else:
            new_ceil = max(0.30, current_ceil - 0.15)
            pce_range = (0.30, 1.0)
            confidence = "LOW"
            reason = (f"LF {lf:.0%} above target. Stepping ceiling down "
                     f"from {current_ceil:.2f} to {new_ceil:.2f}")
        
        return InformedDiagnosis(
            category=DiagnosticCategory.LF_MODERATELY_HIGH,
            parameter='qsi_ceiling',
            old_value=current_ceil,
            new_value=round(new_ceil, 2),
            reason=reason,
            pce_range=pce_range,
            confidence=confidence,
            priority=2,
        )
    
    def _handle_lf_too_low(self, cre_result: CREResult, sug) -> InformedDiagnosis:
        """
        LF below viable (<50%). Primary lever: frequency reduction.
        
        Never inflate demand to fix low LF  reduce frequency instead.
        The CRE/PCE should not fabricate passengers.
        """
        current_freq = getattr(self.config, 'frequency', 7)
        lf = cre_result.raw_load_factor
        total = cre_result.raw_total
        seats_per_flight = getattr(self.config, 'seats', 214)
        
        # Calculate what frequency gives ~70% LF
        if total > 0 and seats_per_flight > 0:
            target_cap = total / 0.70
            ideal_freq = max(1, round(target_cap / (seats_per_flight * 52 * 2)))
        else:
            ideal_freq = max(1, current_freq - 2)
        
        # Never increase frequency to fix low LF
        new_freq = min(ideal_freq, current_freq - 1)
        new_freq = max(1, new_freq)
        
        pce_range = (1, current_freq)
        confidence = "MEDIUM" if sug else "LOW"
        reason = (f"LF {lf:.0%} below viable threshold. "
                 f"Reducing frequency from {current_freq}x to {new_freq}x/week "
                 f"to target ~70% LF. Demand ({total:,.0f} pax) does not justify "
                 f"current capacity.")
        
        return InformedDiagnosis(
            category=DiagnosticCategory.LF_TOO_LOW,
            parameter='frequency',
            old_value=current_freq,
            new_value=new_freq,
            reason=reason,
            pce_range=pce_range,
            confidence=confidence,
            priority=1,
        )
    
    def _handle_cnx_share_high(self, cre_result: CREResult, sug) -> InformedDiagnosis:
        """
        Connecting share too high. Reduce QSI adjustment to bring
        connecting traffic back into expected range.
        """
        current_adj = getattr(self.config, 'qsi_adjustment', 1.0)
        
        if sug is not None:
            # PCE tells us what cnx share is expected
            expected_range = sug.cnx_share_range
            pce_adj = sug.qsi_adjustment
            # Target the PCE's QSI adjustment directly
            new_adj = max(0.10, min(pce_adj, current_adj * 0.80))
            pce_range = (max(0.10, pce_adj * 0.7), min(1.0, pce_adj * 1.3))
            confidence = sug.confidence
            reason = (f"Connecting share exceeds expected range "
                     f"({expected_range[0]:.0%}-{expected_range[1]:.0%}). "
                     f"PCE suggests QSI adj {pce_adj:.3f}. "
                     f"Adjusting from {current_adj:.3f} to {new_adj:.3f}")
        else:
            new_adj = max(0.10, current_adj * 0.75)
            pce_range = (0.10, 1.0)
            confidence = "LOW"
            reason = (f"Connecting share too high. Reducing QSI adjustment "
                     f"from {current_adj:.3f} to {new_adj:.3f}")
        
        return InformedDiagnosis(
            category=DiagnosticCategory.CNX_SHARE_TOO_HIGH,
            parameter='qsi_adjustment',
            old_value=current_adj,
            new_value=round(new_adj, 3),
            reason=reason,
            pce_range=pce_range,
            confidence=confidence,
            priority=1,
        )
    
    def _handle_cnx_share_low(self, cre_result: CREResult, sug) -> InformedDiagnosis:
        """
        Connecting share too low for a hub route. Increase QSI adjustment
        or ceiling to capture more connecting traffic.
        """
        current_adj = getattr(self.config, 'qsi_adjustment', 1.0)
        
        if sug is not None:
            pce_adj = sug.qsi_adjustment
            # Increase toward PCE target
            new_adj = min(1.0, max(pce_adj, current_adj * 1.25))
            pce_range = (max(0.10, pce_adj * 0.7), min(1.0, pce_adj * 1.3))
            confidence = sug.confidence
            reason = (f"Connecting share below expected. PCE suggests "
                     f"QSI adj {pce_adj:.3f}. Increasing from "
                     f"{current_adj:.3f} to {new_adj:.3f}")
        else:
            new_adj = min(1.0, current_adj * 1.20)
            pce_range = (0.10, 1.0)
            confidence = "LOW"
            reason = (f"Connecting share too low. Increasing QSI adjustment "
                     f"from {current_adj:.3f} to {new_adj:.3f}")
        
        return InformedDiagnosis(
            category=DiagnosticCategory.CNX_SHARE_TOO_LOW,
            parameter='qsi_adjustment',
            old_value=current_adj,
            new_value=round(new_adj, 3),
            reason=reason,
            pce_range=pce_range,
            confidence=confidence,
            priority=2,
        )
    
    def _handle_city_outliers(self, cre_result: CREResult, sug) -> InformedDiagnosis:
        """
        Individual city capture rates are implausible. Lower QSI ceiling
        to cap the outliers.
        """
        current_ceil = getattr(self.config, 'qsi_ceiling', 1.0)
        new_ceil = max(0.30, current_ceil - 0.10)
        
        pce_range = (0.30, 0.80)
        confidence = "MEDIUM" if sug else "LOW"
        reason = (f"City-level capture outliers detected. "
                 f"Reducing QSI ceiling from {current_ceil:.2f} to {new_ceil:.2f} "
                 f"to cap individual city contributions")
        
        return InformedDiagnosis(
            category=DiagnosticCategory.CITY_OUTLIERS,
            parameter='qsi_ceiling',
            old_value=current_ceil,
            new_value=round(new_ceil, 2),
            reason=reason,
            pce_range=pce_range,
            confidence=confidence,
            priority=2,
        )
    
    def _handle_zero_component(self, cre_result: CREResult, sug) -> InformedDiagnosis:
        """
        A major component (P2P or connecting) is zero. This is usually
        a data problem, not a parameter problem. Flag for analyst review.
        """
        return InformedDiagnosis(
            category=DiagnosticCategory.ZERO_COMPONENT,
            parameter='qsi_adjustment',
            old_value=getattr(self.config, 'qsi_adjustment', 1.0),
            new_value=getattr(self.config, 'qsi_adjustment', 1.0),  # No change
            reason="Zero component detected - likely a data issue requiring "
                   "analyst review rather than parameter adjustment",
            pce_range=(0.10, 1.0),
            confidence="LOW",
            priority=3,
        )
    
    def _handle_multiple_failures(self, cre_result: CREResult, sug) -> InformedDiagnosis:
        """
        Multiple critical failures. Address LF first (the dominant lever),
        and flag that the route needs comprehensive analyst review.
        """
        lf = cre_result.raw_load_factor
        if lf > 0.85:
            return self._handle_lf_too_high(cre_result, sug)
        elif lf < 0.50:
            return self._handle_lf_too_low(cre_result, sug)
        else:
            return self._handle_lf_moderately_high(cre_result, sug)


# =============================================================================
# ENHANCED CLOSED-LOOP RUNNER: Uses bridge instead of hardcoded rules
# =============================================================================

class InformedClosedLoopRunner:
    """
    Enhanced closed-loop runner that uses the CRE-PCE bridge for
    parameter adjustments instead of the original hardcoded rules.
    
    The key difference from ClosedLoopRunner:
    - _diagnose() consults the PCE through the bridge
    - Adjustments are bounded by what the PCE considers reasonable
    - The adjustment trail records PCE confidence and comparable cases
    - Convergence is faster because adjustments are better-informed
    """
    
    MAX_RERUNS = 3
    
    def __init__(self, config, pipeline_fn, output_path_fn=None,
                 bounds=None, log_fn=None,
                 pce_suggestion=None):
        """
        Args:
            config: RouteConfig object (will be modified in place)
            pipeline_fn: callable(config, output_path) -> results dict
            output_path_fn: callable() -> temp file path
            bounds: optional CommercialBounds override
            log_fn: optional callable(str) for logging
            pce_suggestion: optional pre-computed CalibrationSuggestion
        """
        self.config = config
        self.pipeline_fn = pipeline_fn
        self.output_path_fn = output_path_fn
        self.bounds = bounds
        self.log = log_fn or (lambda msg: None)
        self.bridge = CREPCEBridge(config, pce_suggestion)
    
    def _get_output_path(self):
        if self.output_path_fn:
            return self.output_path_fn()
        import tempfile
        return tempfile.mktemp(suffix='.xlsx')
    
    def run(self) -> 'InformedClosedLoopResult':
        """
        Execute the informed closed-loop:
        pipeline -> CRE -> bridge diagnose -> adjust -> repeat.
        """
        result = InformedClosedLoopResult()
        result.pce_suggestion_available = self.bridge.suggestion is not None
        if self.bridge.suggestion:
            result.pce_confidence = self.bridge.suggestion.confidence
            result.pce_route_label = self.bridge.suggestion.route_label
            result.comparable_cases_count = len(self.bridge.suggestion.comparable_cases)
        
        # --- Initial run ---
        # If PCE has a suggested LF range, apply it to bounds
        if self.bridge.suggestion:
            pce_sug = self.bridge.suggestion
            if hasattr(pce_sug, 'suggested_lf_range') and pce_sug.suggested_lf_range:
                pce_lf_low, pce_lf_high = pce_sug.suggested_lf_range
                if 0.40 < pce_lf_low < 0.95 and 0.40 < pce_lf_high < 0.95:
                    b = self.bounds or CommercialBounds()
                    b.lf_target_low = pce_lf_low
                    b.lf_target_high = pce_lf_high
                    # Max credible should be slightly above target high
                    b.lf_max_credible = min(pce_lf_high + 0.08, 0.95)
                    self.bounds = b
                    self.log(f"  PCE LF range: {pce_lf_low:.0%}-{pce_lf_high:.0%} "
                             f"(max credible: {b.lf_max_credible:.0%})")

        self.log("Informed closed-loop: initial pipeline run")
        output_path = self._get_output_path()
        try:
            pipeline_results = self.pipeline_fn(self.config, output_path)
        except Exception as e:
            result.error = str(e)
            result.convergence_note = f"Pipeline failed: {e}"
            return result
        
        result.initial_results = copy.deepcopy(pipeline_results)
        
        initial_cre = run_cre(self.config, pipeline_results, self.bounds)
        result.initial_cre = initial_cre
        self.log(f"  Initial: {pipeline_results['grand_total']:,.0f} pax, "
                 f"{pipeline_results.get('load_factor', 0):.1%} LF, "
                 f"CRE confidence {initial_cre.confidence_score}/100")
        
        # Check if initial run is already reasonable
        # IMPORTANT: Check the RAW pipeline load factor, not CRE-adjusted checks.
        # The CRE may cosmetically adjust numbers to make checks pass, but the
        # closed-loop needs to re-run the actual pipeline with different parameters.
        raw_lf = pipeline_results.get('load_factor', 0)
        b = self.bounds or CommercialBounds()
        needs_rerun = (
            raw_lf > b.lf_max_credible or
            raw_lf < b.lf_min_viable or
            pipeline_results.get('grand_total', 0) <= 0
        )
        self.log(f"  Raw LF={raw_lf:.1%}, bounds=[{b.lf_min_viable:.0%},{b.lf_max_credible:.0%}], needs_rerun={needs_rerun}")
        if not needs_rerun:
            # Also check the CRE checks for non-LF issues
            has_critical = any(
                c.status in (CheckStatus.FAIL, CheckStatus.CRITICAL)
                for c in initial_cre.checks
            )
            needs_rerun = has_critical
            self.log(f"  CRE checks: {len(initial_cre.checks)} total, has_critical={has_critical}")
        
        if not needs_rerun:
            result.final_results = pipeline_results
            result.final_cre = initial_cre
            result.converged = True
            result.convergence_note = "Initial run passed all CRE checks"
            self.log("  No re-runs needed -- forecast within bounds")
            return result
        
        self.log(f"  Entering re-run loop (max {self.MAX_RERUNS})")
        
        # --- Re-run loop ---
        current_results = pipeline_results
        current_cre = initial_cre
        
        for iteration in range(1, self.MAX_RERUNS + 1):
            # Use bridge for PCE-informed diagnosis
            diagnosis = self.bridge.diagnose(current_cre)
            if diagnosis is None:
                self.log(f"  Re-run {iteration}: bridge.diagnose returned None "
                         f"(raw_lf={getattr(current_cre, 'raw_load_factor', '?')}, "
                         f"adj_lf={getattr(current_cre, 'adjusted_load_factor', '?')})")
                result.converged = True
                result.convergence_note = f"Converged after {iteration - 1} re-run(s)"
                break
            
            # Check if diagnosis recommends no change (e.g., zero component)
            if abs(diagnosis.new_value - diagnosis.old_value) < 0.001:
                self.log(f"  Re-run {iteration}: no change ({diagnosis.parameter} "
                         f"{diagnosis.old_value} -> {diagnosis.new_value})")
                result.convergence_note = (
                    f"No parameter change possible for {diagnosis.category.value}. "
                    f"Analyst review required."
                )
                break
            
            # Apply the parameter change
            self.log(f"  Re-run {iteration}: {diagnosis.parameter} "
                     f"{diagnosis.old_value} -> {diagnosis.new_value} "
                     f"[{diagnosis.category.value}] "
                     f"(PCE confidence: {diagnosis.confidence})")
            
            setattr(self.config, diagnosis.parameter, diagnosis.new_value)
            result.config_changes[diagnosis.parameter] = {
                'original': result.config_changes.get(diagnosis.parameter, {}).get(
                    'original', diagnosis.old_value),
                'final': diagnosis.new_value,
            }
            
            # Re-run pipeline
            output_path = self._get_output_path()
            try:
                current_results = self.pipeline_fn(self.config, output_path)
            except Exception as e:
                result.error = str(e)
                result.convergence_note = f"Pipeline failed on re-run {iteration}: {e}"
                break
            
            # Re-run CRE
            current_cre = run_cre(self.config, current_results, self.bounds)
            
            # Record
            rerun_rec = InformedRerunRecord(
                iteration=iteration,
                category=diagnosis.category.value,
                parameter_changed=diagnosis.parameter,
                old_value=diagnosis.old_value,
                new_value=diagnosis.new_value,
                reason=diagnosis.reason,
                pce_range=diagnosis.pce_range,
                pce_confidence=diagnosis.confidence,
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
            
            # Check convergence using RAW pipeline LF
            rerun_lf = current_results.get('load_factor', 0)
            lf_ok = b.lf_min_viable <= rerun_lf <= b.lf_max_credible
            total_ok = current_results.get('grand_total', 0) > 0
            has_critical = any(
                c.status in (CheckStatus.FAIL, CheckStatus.CRITICAL)
                for c in current_cre.checks
            )
            if lf_ok and total_ok and not has_critical:
                result.converged = True
                result.convergence_note = f"Converged after {iteration} re-run(s)"
                self.log(f"  Converged after {iteration} re-run(s)")
                break
        
        if not result.converged and not result.error:
            result.convergence_note = (
                f"Did not converge after {self.MAX_RERUNS} re-runs. "
                f"Analyst review required."
            )
            self.log(f"  WARNING: did not converge after {self.MAX_RERUNS} re-runs")
        
        result.final_results = current_results
        result.final_cre = current_cre
        return result


# =============================================================================
# DATA CLASSES FOR INFORMED CLOSED-LOOP OUTPUT
# =============================================================================

@dataclass
class InformedRerunRecord:
    """Records one informed closed-loop re-run attempt."""
    iteration: int
    category: str                    # DiagnosticCategory value
    parameter_changed: str
    old_value: float
    new_value: float
    reason: str
    pce_range: Tuple[float, float]   # What PCE considers reasonable
    pce_confidence: str              # PCE confidence level
    result_total: float
    result_lf: float
    cre_confidence: int
    cre_adjusted: bool


@dataclass
class InformedClosedLoopResult:
    """Complete output from the informed closed-loop process."""
    # Re-run tracking
    reruns_performed: int = 0
    max_reruns: int = 3
    
    # PCE context
    pce_suggestion_available: bool = False
    pce_confidence: str = ""
    pce_route_label: str = ""
    comparable_cases_count: int = 0
    
    # History
    rerun_history: List[InformedRerunRecord] = field(default_factory=list)
    
    # Initial vs final
    initial_results: Dict = field(default_factory=dict)
    initial_cre: Optional[CREResult] = None
    final_results: Dict = field(default_factory=dict)
    final_cre: Optional[CREResult] = None
    
    # Config changes
    config_changes: Dict = field(default_factory=dict)
    
    # Outcome
    converged: bool = False
    convergence_note: str = ""
    error: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'reruns_performed': self.reruns_performed,
            'converged': self.converged,
            'convergence_note': self.convergence_note,
            'pce_available': self.pce_suggestion_available,
            'pce_confidence': self.pce_confidence,
            'comparable_cases': self.comparable_cases_count,
            'config_changes': self.config_changes,
            'rerun_history': [
                {
                    'iteration': r.iteration,
                    'category': r.category,
                    'param': r.parameter_changed,
                    'old': r.old_value,
                    'new': r.new_value,
                    'pce_range': list(r.pce_range),
                    'pce_confidence': r.pce_confidence,
                    'reason': r.reason,
                    'total': r.result_total,
                    'lf': r.result_lf,
                    'cre_confidence': r.cre_confidence,
                }
                for r in self.rerun_history
            ],
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def apply_pce_to_config(config, suggestion: 'CalibrationSuggestion') -> List[str]:
    """
    Apply PCE suggestion to a RouteConfig before the first pipeline run.
    
    Returns a list of changes made for the assumptions log.
    """
    changes = []
    
    # QSI adjustment
    old_adj = getattr(config, 'qsi_adjustment', 1.0)
    if suggestion.qsi_adjustment != old_adj:
        config.qsi_adjustment = suggestion.qsi_adjustment
        changes.append(f"QSI adjustment: {old_adj:.3f} -> {suggestion.qsi_adjustment:.3f} "
                       f"({suggestion.qsi_adj_reasoning})")
    
    # Growth rate
    old_growth = getattr(config, 'home_growth', 0.10)
    if suggestion.growth_rate != old_growth:
        config.home_growth = suggestion.growth_rate
        config.dest_growth = suggestion.growth_rate
        changes.append(f"Growth rate: {old_growth:.1%} -> {suggestion.growth_rate:.1%} "
                       f"({suggestion.growth_reasoning})")
    
    return changes


def run_informed_closed_loop(config, pipeline_fn, output_path_fn=None,
                              bounds=None, log_fn=None,
                              pce_suggestion=None) -> InformedClosedLoopResult:
    """Convenience function for informed closed-loop execution."""
    runner = InformedClosedLoopRunner(
        config, pipeline_fn, output_path_fn, bounds, log_fn, pce_suggestion
    )
    return runner.run()


# =============================================================================
# SELF-TEST
# =============================================================================

if __name__ == '__main__':
    print("CRE-PCE Integration Bridge - Self Test")
    print("=" * 55)
    
    # Test 1: Bridge initialisation without PCE
    print("\nTest 1: Bridge without PCE suggestion")
    
    class MockConfig:
        airline_code = 'XX'
        home_airport_code = 'TPE'
        dest_airport_code = 'SJC'
        frequency = 7
        seats = 280
        aircraft_type = '787'
        carrier_type = 'Full Service'
        route_type = 'Hub Long-Haul'
        hub_status = 'Major Hub'
        is_new_route = True
        qsi_adjustment = 1.0
        qsi_ceiling = 1.0
    
    cfg = MockConfig()
    bridge = CREPCEBridge(cfg, pce_suggestion=None)
    
    if HAS_CRE:
        # Create a mock CRE result with high LF
        mock_cre = CREResult(
            adjusted=False,
            raw_load_factor=1.50,
            raw_total=200000,
            checks=[
                type('Check', (), {
                    'name': 'Load Factor', 
                    'status': CheckStatus.CRITICAL,
                    'actual_value': 1.50,
                    'acceptable_range': (0.50, 0.95),
                    'message': 'LF 150% exceeds maximum',
                })()
            ],
            bounds=CommercialBounds(),
        )
        
        diagnosis = bridge.diagnose(mock_cre)
        if diagnosis:
            print(f"  Category: {diagnosis.category.value}")
            print(f"  Parameter: {diagnosis.parameter}")
            print(f"  Old: {diagnosis.old_value}, New: {diagnosis.new_value}")
            print(f"  PCE range: {diagnosis.pce_range}")
            print(f"  Confidence: {diagnosis.confidence}")
            print(f"  Reason: {diagnosis.reason[:80]}...")
            print("  PASS: Diagnosis generated correctly")
        else:
            print("  FAIL: No diagnosis returned for 150% LF")
    else:
        print("  SKIP: CRE not available")
    
    # Test 2: Bridge with PCE suggestion
    print("\nTest 2: Bridge with PCE suggestion")
    if HAS_PCE and HAS_CRE:
        try:
            profile = RouteProfile(
                origin='LHR', destination='SJC',
                carrier='BA', carrier_type='Full Service',
                hub_status='Major Hub', frequency=7, seats=214,
                new_route=False,
            )
            engine = PredictiveCalibrationEngine()
            sug = engine.predict(profile)
            
            bridge2 = CREPCEBridge(cfg, pce_suggestion=sug)
            diagnosis2 = bridge2.diagnose(mock_cre)
            if diagnosis2:
                print(f"  Category: {diagnosis2.category.value}")
                print(f"  PCE-informed adj: {diagnosis2.new_value:.3f}")
                print(f"  PCE range: {diagnosis2.pce_range}")
                print(f"  Confidence: {diagnosis2.confidence}")
                print(f"  PASS: PCE-informed diagnosis generated")
            else:
                print("  FAIL: No diagnosis with PCE")
        except Exception as e:
            print(f"  ERROR: {e}")
    else:
        missing = []
        if not HAS_PCE:
            missing.append("PCE")
        if not HAS_CRE:
            missing.append("CRE")
        print(f"  SKIP: {' and '.join(missing)} not available")
    
    # Test 3: No failures = no diagnosis
    print("\nTest 3: Clean CRE result (no failures)")
    if HAS_CRE:
        clean_cre = CREResult(
            adjusted=False,
            raw_load_factor=0.80,
            raw_total=100000,
            checks=[
                type('Check', (), {
                    'name': 'Load Factor',
                    'status': CheckStatus.PASS,
                    'actual_value': 0.80,
                    'acceptable_range': (0.50, 0.95),
                    'message': 'OK',
                })()
            ],
        )
        bridge3 = CREPCEBridge(cfg)
        diag3 = bridge3.diagnose(clean_cre)
        if diag3 is None:
            print("  PASS: No diagnosis for clean result (correct)")
        else:
            print(f"  FAIL: Unexpected diagnosis: {diag3.reason}")
    
    # Test 4: LF too low
    print("\nTest 4: Low LF diagnosis")
    if HAS_CRE:
        low_cre = CREResult(
            adjusted=False,
            raw_load_factor=0.29,
            raw_total=30000,
            checks=[
                type('Check', (), {
                    'name': 'Load Factor',
                    'status': CheckStatus.FAIL,
                    'actual_value': 0.29,
                    'acceptable_range': (0.50, 0.95),
                    'message': 'LF below viable',
                })()
            ],
            bounds=CommercialBounds(),
        )
        bridge4 = CREPCEBridge(cfg)
        diag4 = bridge4.diagnose(low_cre)
        if diag4 and diag4.category == DiagnosticCategory.LF_TOO_LOW:
            print(f"  Category: {diag4.category.value}")
            print(f"  Parameter: {diag4.parameter} -> {diag4.new_value}")
            print(f"  PASS: Correctly diagnosed low LF")
        else:
            print(f"  FAIL: Expected LF_TOO_LOW, got {diag4.category.value if diag4 else 'None'}")
    
    print("\n=== All self-tests complete ===")
