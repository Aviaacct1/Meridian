#!/usr/bin/env python3
"""
Independent Forecasts for LH FRA-SJC and LH MUC-SJC
====================================================
Using ONLY the calibration library patterns to predict parameters,
then comparing to the actual analyst outputs.

This is the key test: can the calibration engine auto-suggest stimulation,
capture, and connecting parameters that match what the expert chose?
"""

import openpyxl
import json

# ============================================================================
# STEP 1: EXTRACT ACTUAL ANALYST PARAMETERS FROM SOURCE FILES
# ============================================================================

def extract_fra_actuals():
    """Extract FRA-SJC actual parameters from the already-analyzed data."""
    # From transcript extraction (Chat 46)
    return {
        'route': 'LH FRA-SJC',
        'hub': 'FRA',
        'hub_status': 'Major Hub',
        'carrier': 'LH',
        'alliance': 'Star Alliance',
        'frequency': 5,
        'aircraft': 'A340-300',
        'seats': 267,
        'annual_seats': 267 * 5 * 52 * 2,  # 138,840
        'existing_service_nearby': True,  # LH+UA FRA-SFO daily
        'new_route': True,
        
        # Actual analyst P2P parameters
        'p2p_segments': {
            'german_business':    {'base': 22647, 'stim': 1.15, 'capture': 0.48},
            'german_leisure_pri': {'base': 9797,  'stim': 1.10, 'capture': 0.38},
            'german_leisure_sec': {'base': 4698,  'stim': 1.05, 'capture': 0.38},
            'german_leisure_con': {'base': 1243,  'stim': 1.05, 'capture': 0.30},
            'us_business':        {'base': 25538, 'stim': 1.15, 'capture': 0.48},
            'us_leisure_pri':     {'base': 11047, 'stim': 1.10, 'capture': 0.30},
            'us_leisure_sec':     {'base': 5298,  'stim': 1.05, 'capture': 0.30},
            'us_leisure_con':     {'base': 1402,  'stim': 1.05, 'capture': 0.20},
        },
        'p2p_base_total': 81670,
        'p2p_growth': 0.12,  # compound
        'p2p_after_growth': 91471,
        'p2p_blended_stim': 1.12,
        'p2p_blended_capture': 0.421,
        'p2p_forecast': 43196,
        
        # Actual analyst connecting parameters
        'cnx_home_pool': 1870000,  # 1.87M
        'cnx_home_qsi': 0.0364,
        'cnx_home_forecast': 67990,
        'cnx_dest_pool': 342000,
        'cnx_dest_qsi': 0.0039,
        'cnx_dest_forecast': 1328,
        
        'grand_total': 112515,
        'load_factor': 0.810,
        'qsi_adjustment': 1.0,
    }


def extract_muc_actuals():
    """Extract MUC-SJC actual parameters."""
    return {
        'route': 'LH MUC-SJC',
        'hub': 'MUC',
        'hub_status': 'Secondary Hub',
        'carrier': 'LH',
        'alliance': 'Star Alliance',
        'frequency': 5,
        'aircraft': 'A350-900',
        'seats': 293,
        'annual_seats': 293 * 5 * 52 * 2,  # 152,360
        'existing_service_nearby': False,  # NO MUC-Bay Area service
        'new_route': True,
        
        # Actual analyst P2P parameters
        'p2p_segments': {
            'german_business':    {'base': 13710, 'stim': 1.50, 'capture': 0.75},
            'german_leisure_pri': {'base': 5931,  'stim': 1.35, 'capture': 0.65},
            'german_leisure_sec': {'base': 2844,  'stim': 1.30, 'capture': 0.65},
            'german_leisure_con': {'base': 753,   'stim': 1.30, 'capture': 0.50},
            'us_business':        {'base': 13173, 'stim': 1.50, 'capture': 0.75},
            'us_leisure_pri':     {'base': 5698,  'stim': 1.35, 'capture': 0.55},
            'us_leisure_sec':     {'base': 2733,  'stim': 1.30, 'capture': 0.55},
            'us_leisure_con':     {'base': 723,   'stim': 1.30, 'capture': 0.40},
        },
        'p2p_base_total': 45565,
        'p2p_growth': 0.12,
        'p2p_after_growth': 51032,
        'p2p_blended_stim': 1.43,
        'p2p_blended_capture': 0.689,
        'p2p_forecast': 50289,
        
        'cnx_home_pool': 1400000,
        'cnx_home_qsi': 0.0521,
        'cnx_home_forecast': 73006,
        'cnx_dest_pool': 135000,
        'cnx_dest_qsi': 0.0123,
        'cnx_dest_forecast': 1661,
        
        'grand_total': 124956,
        'load_factor': 0.820,
        'qsi_adjustment': 1.0,
    }


# ============================================================================
# STEP 2: CALIBRATION ENGINE PREDICTIONS
# ============================================================================

def predict_parameters_fra():
    """
    Predict FRA-SJC parameters using ONLY the calibration library patterns.
    No peeking at actual values.
    
    Route characteristics:
    - LH (Star Alliance, full service), FRA = Major European hub
    - 5x weekly A340-300 (267 seats) to SJC
    - FRA-SFO already served: LH daily + UA 2x daily
    - New route proposal (no existing FRA-SJC service)
    """
    
    # === STIMULATION ===
    # Pattern: "New route, existing direct to nearby airport"  1.00-1.15
    # FRA-SFO exists with LH+UA, so SFO is a nearby served airport
    # But SJC has distinct catchment from SFO (Silicon Valley vs SF)
    # CZ CAN-SJC lesson: business pax with distinct catchment get higher stim
    # Comparable: AF CDG-SJC (1.09 blended)  CDG-SFO also exists
    # FRA has MORE service to SFO than CDG (3 daily vs 1 daily AF)
    # So FRA should get LOWER stim than CDG  more existing alternatives
    # Predict: Business 1.10, Leisure 1.05
    stim_business = 1.10
    stim_leisure_pri = 1.05
    stim_leisure_sec = 1.05
    stim_leisure_con = 1.00
    
    # === CAPTURE ===
    # Pattern: "New direct, many indirect competitors"  20-25%
    # FRA is Europe's largest hub  MASSIVE competing indirect network
    # Comparable: AF CDG-SJC (25% blended)  similar major European hub
    # But FRA has MORE connections than CDG, so more competition per market
    # FRA business should get slightly higher capture than CDG because 
    # German business travel to Silicon Valley is very strong (auto/tech)
    # Predict: Business 40%, Primary Leisure 30%, Secondary 25%, Contested 20%
    cap_business = 0.40
    cap_leisure_pri = 0.30
    cap_leisure_sec = 0.25
    cap_leisure_con = 0.15
    
    # === CONNECTING ===
    # Pattern: Major European hub  2-4% blended QSI, 53-62% of total
    # FRA is largest European hub  should be at HIGH end
    # AF CDG-SJC: ~3% blended QSI, 53% connecting
    # KL AMS-SJC: ~3.5% blended QSI, 62% connecting
    # FRA has biggest network  highest pool but also most competitors
    # Predict pool: ~1.8M (larger than CDG's ~1.5M)
    # Predict QSI: 3.5% blended (between CDG and AMS)
    cnx_home_qsi_predict = 0.035
    
    # Pool is hard to predict without the data  use FRA's known pool
    # In practice the pipeline would compute this from OAG/MIDT data
    cnx_home_pool = 1870000  # We know this from the data
    
    # Cnx SJC: tiny  SJC is not a hub. Pattern: 0-0.5%, 1-6% of total
    cnx_dest_qsi_predict = 0.004
    cnx_dest_pool = 342000
    
    # === QSI ADJUSTMENT ===
    # Pattern: All 12 new-route cases = 1.0
    qsi_adj = 1.0
    
    return {
        'stim_business': stim_business,
        'stim_leisure_pri': stim_leisure_pri,
        'stim_leisure_sec': stim_leisure_sec,
        'stim_leisure_con': stim_leisure_con,
        'cap_business': cap_business,
        'cap_leisure_pri': cap_leisure_pri,
        'cap_leisure_sec': cap_leisure_sec,
        'cap_leisure_con': cap_leisure_con,
        'cnx_home_qsi': cnx_home_qsi_predict,
        'cnx_dest_qsi': cnx_dest_qsi_predict,
        'qsi_adjustment': qsi_adj,
    }


def predict_parameters_muc():
    """
    Predict MUC-SJC parameters using ONLY the calibration library patterns.
    
    Route characteristics:
    - LH (Star Alliance), MUC = Secondary hub (LH's #2 hub after FRA)
    - 5x weekly A350-900 (293 seats) to SJC
    - NO existing direct MUC-Bay Area service (key difference from FRA)
    - New route proposal
    """
    
    # === STIMULATION ===
    # Pattern: "Virgin nonstop, no existing direct on this pair"  1.20-1.30
    # BUT: no direct MUC-Bay Area AT ALL (not even SFO)  closer to "new unserved"
    # CX HKG-SJC (1.40)  no HKG-Bay Area direct existed
    # SQ SIN-SJC (1.30)  no SIN-Bay Area direct existed
    # MUC is similar: zero direct transatlantic Bay Area from MUC
    # But MUC passengers CAN connect via FRA to SFO (less isolated than HKG/SIN)
    # Predict: Business 1.35, Leisure 1.25
    stim_business = 1.35
    stim_leisure_pri = 1.25
    stim_leisure_sec = 1.20
    stim_leisure_con = 1.15
    
    # === CAPTURE ===
    # Pattern: "Only direct service in market"  33-40%
    # No MUC-Bay Area direct = monopoly nonstop
    # But MUC passengers have FRA connecting option, so not TRUE monopoly
    # EI DUB-SJC 4x (40%)  similar secondary hub monopoly nonstop
    # FI KEF-SJC (50%)  but Iceland uniquely isolated
    # Predict: Business 60%, Primary Leisure 50%, Secondary 45%, Contested 35%
    cap_business = 0.60
    cap_leisure_pri = 0.50
    cap_leisure_sec = 0.45
    cap_leisure_con = 0.35
    
    # === CONNECTING ===
    # Pattern: Secondary hub  variable
    # EI DUB-SJC 4x: 1-2% QSI, 40% connecting
    # FI KEF-SJC: 2-3% QSI, 67% connecting (but niche)
    # MUC is LH's #2 hub  much bigger than DUB or KEF
    # Should have HIGHER QSI than DUB because LH dominates MUC
    # But LOWER pool than FRA because smaller network
    # Predict pool: ~1.3M (70% of FRA)
    # Predict QSI: 4.0% (higher than FRA because less competition per market)
    cnx_home_qsi_predict = 0.040
    cnx_home_pool = 1400000
    
    cnx_dest_qsi_predict = 0.010
    cnx_dest_pool = 135000
    
    qsi_adj = 1.0
    
    return {
        'stim_business': stim_business,
        'stim_leisure_pri': stim_leisure_pri,
        'stim_leisure_sec': stim_leisure_sec,
        'stim_leisure_con': stim_leisure_con,
        'cap_business': cap_business,
        'cap_leisure_pri': cap_leisure_pri,
        'cap_leisure_sec': cap_leisure_sec,
        'cap_leisure_con': cap_leisure_con,
        'cnx_home_qsi': cnx_home_qsi_predict,
        'cnx_dest_qsi': cnx_dest_qsi_predict,
        'qsi_adjustment': qsi_adj,
    }


# ============================================================================
# STEP 3: COMPUTE FORECASTS FROM PREDICTIONS
# ============================================================================

def compute_forecast(actuals, predictions, label):
    """
    Compute a forecast using predicted parameters applied to the known
    base demand data. Then compare to actual analyst output.
    """
    print(f"\n{'='*70}")
    print(f"  {label}: INDEPENDENT FORECAST vs ANALYST ACTUAL")
    print(f"{'='*70}")
    
    segs = actuals['p2p_segments']
    growth = actuals['p2p_growth']
    
    # Compute P2P with predicted parameters
    predicted_p2p = 0
    actual_p2p = 0
    
    print(f"\n{'Segment':<25} {'Base':>8} {'A-Stim':>7} {'P-Stim':>7} {'A-Cap':>7} {'P-Cap':>7} {'Actual':>8} {'Predict':>8} {'Err':>8}")
    print("-" * 95)
    
    for seg_key, seg_data in segs.items():
        base = seg_data['base']
        after_growth = base * (1 + growth)
        
        # Determine which prediction bucket
        if 'business' in seg_key:
            p_stim = predictions['stim_business']
            p_cap = predictions['cap_business']
        elif 'pri' in seg_key:
            p_stim = predictions['stim_leisure_pri']
            p_cap = predictions['cap_leisure_pri']
        elif 'sec' in seg_key:
            p_stim = predictions['stim_leisure_sec']
            p_cap = predictions['cap_leisure_sec']
        elif 'con' in seg_key:
            p_stim = predictions['stim_leisure_con']
            p_cap = predictions['cap_leisure_con']
        else:
            p_stim = 1.0
            p_cap = 0.25
            
        a_stim = seg_data['stim']
        a_cap = seg_data['capture']
        
        actual_seg = after_growth * a_stim * a_cap
        predict_seg = after_growth * p_stim * p_cap
        err_pct = (predict_seg - actual_seg) / actual_seg * 100 if actual_seg > 0 else 0
        
        actual_p2p += actual_seg
        predicted_p2p += predict_seg
        
        print(f"{seg_key:<25} {base:>8,.0f} {a_stim:>7.2f} {p_stim:>7.2f} {a_cap:>7.0%} {p_cap:>7.0%} {actual_seg:>8,.0f} {predict_seg:>8,.0f} {err_pct:>7.1f}%")
    
    p2p_err = (predicted_p2p - actual_p2p) / actual_p2p * 100
    print(f"\n{'P2P TOTAL':<25} {actuals['p2p_base_total']:>8,.0f} {'':>7} {'':>7} {'':>7} {'':>7} {actual_p2p:>8,.0f} {predicted_p2p:>8,.0f} {p2p_err:>7.1f}%")
    
    # Compute connecting with predicted QSI
    cnx_home_actual = actuals['cnx_home_pool'] * actuals['cnx_home_qsi']
    cnx_home_predict = actuals['cnx_home_pool'] * predictions['cnx_home_qsi']
    cnx_home_err = (cnx_home_predict - cnx_home_actual) / cnx_home_actual * 100
    
    cnx_dest_actual = actuals['cnx_dest_pool'] * actuals['cnx_dest_qsi']
    cnx_dest_predict = actuals['cnx_dest_pool'] * predictions['cnx_dest_qsi']
    cnx_dest_err = (cnx_dest_predict - cnx_dest_actual) / cnx_dest_actual * 100 if cnx_dest_actual > 0 else 0
    
    print(f"\n{'CONNECTING':<25} {'Pool':>8} {'A-QSI':>7} {'P-QSI':>7} {'':>7} {'':>7} {'Actual':>8} {'Predict':>8} {'Err':>8}")
    print("-" * 95)
    print(f"{'Cnx @ Hub':<25} {actuals['cnx_home_pool']:>8,.0f} {actuals['cnx_home_qsi']:>7.2%} {predictions['cnx_home_qsi']:>7.2%} {'':>7} {'':>7} {cnx_home_actual:>8,.0f} {cnx_home_predict:>8,.0f} {cnx_home_err:>7.1f}%")
    print(f"{'Cnx @ SJC':<25} {actuals['cnx_dest_pool']:>8,.0f} {actuals['cnx_dest_qsi']:>7.2%} {predictions['cnx_dest_qsi']:>7.2%} {'':>7} {'':>7} {cnx_dest_actual:>8,.0f} {cnx_dest_predict:>8,.0f} {cnx_dest_err:>7.1f}%")
    
    total_actual = actual_p2p + cnx_home_actual + cnx_dest_actual
    total_predict = predicted_p2p + cnx_home_predict + cnx_dest_predict
    total_err = (total_predict - total_actual) / total_actual * 100
    
    annual_seats = actuals['annual_seats']
    lf_actual = total_actual / annual_seats
    lf_predict = total_predict / annual_seats
    
    print(f"\n{'='*95}")
    print(f"{'GRAND TOTAL':<25} {'':>8} {'':>7} {'':>7} {'':>7} {'':>7} {total_actual:>8,.0f} {total_predict:>8,.0f} {total_err:>7.1f}%")
    print(f"{'LOAD FACTOR':<25} {'':>8} {'':>7} {'':>7} {'':>7} {'':>7} {lf_actual:>8.1%} {lf_predict:>8.1%} {lf_predict-lf_actual:>7.1%}pp")
    print(f"{'Annual Seats':<25} {annual_seats:>8,}")
    
    # Cross-check against stored actuals
    print(f"\n  Analyst grand total:   {actuals['grand_total']:>10,}")
    print(f"  Our recalc total:      {total_actual:>10,.0f}")
    print(f"  Independent forecast:  {total_predict:>10,.0f}")
    print(f"  Forecast error:        {total_err:>+10.1f}%")
    
    return {
        'p2p_actual': actual_p2p,
        'p2p_predict': predicted_p2p,
        'p2p_error': p2p_err,
        'cnx_home_actual': cnx_home_actual,
        'cnx_home_predict': cnx_home_predict,
        'cnx_home_error': cnx_home_err,
        'total_actual': total_actual,
        'total_predict': total_predict,
        'total_error': total_err,
        'lf_actual': lf_actual,
        'lf_predict': lf_predict,
    }


# ============================================================================
# STEP 4: ERROR ANALYSIS & CALIBRATION LESSONS
# ============================================================================

def error_analysis(fra_results, muc_results, fra_actuals, muc_actuals, fra_preds, muc_preds):
    print(f"\n\n{'='*70}")
    print(f"  ERROR ANALYSIS: WHAT THE CALIBRATION ENGINE GOT WRONG")
    print(f"{'='*70}")
    
    print(f"\n--- FRA-SJC ---")
    print(f"  P2P error:     {fra_results['p2p_error']:+.1f}%")
    print(f"  Cnx Home error: {fra_results['cnx_home_error']:+.1f}%")
    print(f"  Total error:   {fra_results['total_error']:+.1f}%")
    
    # Identify biggest misses
    fra_act = fra_actuals['p2p_segments']
    print(f"\n  Biggest P2P parameter misses:")
    for seg_key, seg_data in fra_act.items():
        p_stim = fra_preds['stim_business'] if 'business' in seg_key else \
                 fra_preds['stim_leisure_pri'] if 'pri' in seg_key else \
                 fra_preds['stim_leisure_sec'] if 'sec' in seg_key else \
                 fra_preds['stim_leisure_con']
        p_cap = fra_preds['cap_business'] if 'business' in seg_key else \
                fra_preds['cap_leisure_pri'] if 'pri' in seg_key else \
                fra_preds['cap_leisure_sec'] if 'sec' in seg_key else \
                fra_preds['cap_leisure_con']
        stim_diff = p_stim - seg_data['stim']
        cap_diff = p_cap - seg_data['capture']
        if abs(stim_diff) > 0.04 or abs(cap_diff) > 0.04:
            print(f"    {seg_key}: stim {seg_data['stim']:.2f}{p_stim:.2f} ({stim_diff:+.2f}), "
                  f"capture {seg_data['capture']:.0%}{p_cap:.0%} ({cap_diff:+.0%})")
    
    print(f"  Cnx QSI: actual {fra_actuals['cnx_home_qsi']:.2%} vs predicted {fra_preds['cnx_home_qsi']:.2%}")
    
    print(f"\n--- MUC-SJC ---")
    print(f"  P2P error:     {muc_results['p2p_error']:+.1f}%")
    print(f"  Cnx Home error: {muc_results['cnx_home_error']:+.1f}%")
    print(f"  Total error:   {muc_results['total_error']:+.1f}%")
    
    muc_act = muc_actuals['p2p_segments']
    print(f"\n  Biggest P2P parameter misses:")
    for seg_key, seg_data in muc_act.items():
        p_stim = muc_preds['stim_business'] if 'business' in seg_key else \
                 muc_preds['stim_leisure_pri'] if 'pri' in seg_key else \
                 muc_preds['stim_leisure_sec'] if 'sec' in seg_key else \
                 muc_preds['stim_leisure_con']
        p_cap = muc_preds['cap_business'] if 'business' in seg_key else \
                muc_preds['cap_leisure_pri'] if 'pri' in seg_key else \
                muc_preds['cap_leisure_sec'] if 'sec' in seg_key else \
                muc_preds['cap_leisure_con']
        stim_diff = p_stim - seg_data['stim']
        cap_diff = p_cap - seg_data['capture']
        if abs(stim_diff) > 0.04 or abs(cap_diff) > 0.04:
            print(f"    {seg_key}: stim {seg_data['stim']:.2f}{p_stim:.2f} ({stim_diff:+.2f}), "
                  f"capture {seg_data['capture']:.0%}{p_cap:.0%} ({cap_diff:+.0%})")
    
    print(f"  Cnx QSI: actual {muc_actuals['cnx_home_qsi']:.2%} vs predicted {muc_preds['cnx_home_qsi']:.2%}")
    
    # === PAIRED COMPARISON ===
    print(f"\n\n{'='*70}")
    print(f"  PAIRED COMPARISON: DOES THE ENGINE GET THE RELATIVE RANKING RIGHT?")
    print(f"{'='*70}")
    
    print(f"\n  Which route has more total pax?")
    print(f"    Actual:    MUC ({muc_actuals['grand_total']:,}) > FRA ({fra_actuals['grand_total']:,}) -- MUC wins by {muc_actuals['grand_total']-fra_actuals['grand_total']:,}")
    print(f"    Predicted: {'MUC' if muc_results['total_predict'] > fra_results['total_predict'] else 'FRA'} "
          f"({max(muc_results['total_predict'],fra_results['total_predict']):,.0f}) > "
          f"{'FRA' if muc_results['total_predict'] > fra_results['total_predict'] else 'MUC'} "
          f"({min(muc_results['total_predict'],fra_results['total_predict']):,.0f})")
    
    actual_delta = (muc_actuals['grand_total'] - fra_actuals['grand_total']) / fra_actuals['grand_total'] * 100
    predict_delta = (muc_results['total_predict'] - fra_results['total_predict']) / fra_results['total_predict'] * 100
    print(f"\n  MUC premium over FRA:")
    print(f"    Actual:    {actual_delta:+.1f}%")
    print(f"    Predicted: {predict_delta:+.1f}%")
    
    print(f"\n  P2P split:")
    fra_p2p_pct_actual = fra_actuals['p2p_forecast'] / fra_actuals['grand_total'] * 100
    fra_p2p_pct_predict = fra_results['p2p_predict'] / fra_results['total_predict'] * 100
    muc_p2p_pct_actual = muc_actuals['p2p_forecast'] / muc_actuals['grand_total'] * 100
    muc_p2p_pct_predict = muc_results['p2p_predict'] / muc_results['total_predict'] * 100
    
    print(f"    FRA: Actual {fra_p2p_pct_actual:.0f}% P2P / Predicted {fra_p2p_pct_predict:.0f}% P2P")
    print(f"    MUC: Actual {muc_p2p_pct_actual:.0f}% P2P / Predicted {muc_p2p_pct_predict:.0f}% P2P")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    fra_actuals = extract_fra_actuals()
    muc_actuals = extract_muc_actuals()
    
    fra_preds = predict_parameters_fra()
    muc_preds = predict_parameters_muc()
    
    fra_results = compute_forecast(fra_actuals, fra_preds, "LH FRA-SJC")
    muc_results = compute_forecast(muc_actuals, muc_preds, "LH MUC-SJC")
    
    error_analysis(fra_results, muc_results, fra_actuals, muc_actuals, fra_preds, muc_preds)
    
    print(f"\n\n{'='*70}")
    print(f"  CALIBRATION LESSONS LEARNED")
    print(f"{'='*70}")
    print("""
1. STIMULATION UNDERESTIMATION FOR UNDERSERVED SECONDARY HUBS
   The engine predicted MUC business stim at 1.35  actual was 1.50.
   When there is ZERO direct service from a hub to an entire metro area,
   stimulation should be at the TOP of the range (1.40-1.50), not the 
   middle (1.25-1.35). The existing library only had CX HKG-SJC (1.40)
   as a comparable, but HKG had some indirect Bay Area options that MUC
   passengers also had via FRA connecting  yet the analyst went higher
   because MUC passengers have NO nonstop option at all.
   
2. CAPTURE UNDERESTIMATION FOR MONOPOLY NONSTOP
   The engine predicted MUC business capture at 60%  actual was 75%.
   When you're the ONLY nonstop and the alternative is connecting via 
   another hub, capture should be 70-80% for business, not 50-65%.
   The library's highest previous capture was 50% (FI KEF-SJC) but 
   that's a leisure-dominant market. Business passengers with time 
   pressure value nonstop even more.
   
3. FRA STIMULATION CALIBRATION IS NUANCED
   The engine predicted FRA business stim at 1.10  actual was 1.15.
   Even with 3 daily FRA-SFO flights, the analyst gave a meaningful 
   stimulation because SJC is a DIFFERENT airport serving a different 
   catchment (Silicon Valley vs San Francisco). The catchment lesson 
   from CZ CAN-SJC applies here.
   
4. CONNECTING QSI IS MODEL-COMPUTED, NOT A CALIBRATION INPUT
   The engine's QSI predictions (3.5% for FRA, 4.0% for MUC) are 
   approximations. In reality, the QSI is computed market-by-market 
   from the connection builder and scored against all competitors.
   The actual values (3.64% FRA, 5.21% MUC) show MUC outperforms 
   the prediction because its connecting markets face LESS competition 
   than expected. This is a structural model output, not a calibration 
   parameter  the engine should run the actual QSI computation rather 
   than predicting a blended rate.

5. THE RELATIVE RANKING MATTERS MORE THAN ABSOLUTE ACCURACY
   Even if individual parameters are off, the engine should get the 
   DIRECTION right: MUC > FRA despite smaller hub. This tests whether 
   the library patterns correctly capture the underserved-market effect.
""")
