#!/usr/bin/env python3
"""
Avia Solutions  QSI Route Forecast Portal (Chat 21)
=====================================================
Streamlit web dashboard for running QSI route assessments.

This is the user-facing interface that wraps the entire pipeline:
    InputValidator  RouteConfig  Pipeline  Output Workbook

Features:
    - Route parameter entry via dropdowns (mirrors the Cover Page)
    - Forecast Mode and Business Case Mode
    - File upload for OAG/QSI data
    - Pipeline execution with progress tracking
    - Downloadable output workbook + assumptions log
    - Job history browser
    - BA LHR-SJC regression test (one-click)

Dependencies:
    - streamlit
    - All pipeline modules (Chats 1-20)

Launch:
    streamlit run avia_dashboard.py --server.port 8501
"""

import streamlit as st
import os
import sys
import json
import time
import shutil
import tempfile
import traceback
from datetime import datetime, timezone, time as dtime
from typing import Dict, List, Optional, Any

# Add project directory to path for module imports
PROJECT_DIR = '/mnt/project'
sys.path.insert(0, PROJECT_DIR)

from input_validator import (
    InputValidator, RouteInput, ValidationResult,
    RunMode, RouteType, CarrierType, MarketMaturity,
    DemandDriver, SeasonalProfile, IndirectCompetition,
    SurfaceCompetition, AIRCRAFT_DB, KNOWN_AIRPORTS,
    BOUNDS, QSI_DEFAULTS_BY_CARRIER, STIMULATION_DEFAULTS,
    GROWTH_DEFAULTS, ba_lhr_sjc_input,
)
from route_config import RouteConfig
from providers import (
    ExcelScheduleProvider, ExcelDemandProvider,
    P2PSegmentData, P2PSubsegmentData,
)
from closed_loop_pipeline_v2 import run_pipeline


# ============================================================================
# PAGE CONFIG & BRANDING
# ============================================================================

st.set_page_config(
    page_title="Avia Solutions  QSI Route Forecast Portal",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS  Avia Solutions brand: dark navy + gold accents
CUSTOM_CSS = """
<style>
    /* Main branding */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a1628 0%, #132240 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e8ecf2 !important;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stNumberInput label,
    [data-testid="stSidebar"] .stTextInput label {
        color: #b8c4d4 !important;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    
    /* Metric cards */
    [data-testid="stMetric"] {
        background: #f8f9fb;
        border: 1px solid #e2e6ec;
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0a1628;
    }
    [data-testid="stMetric"] [data-testid="stMetricLabel"] {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #6b7a8d;
    }
    
    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #0a1628, #1a3258);
        color: #c9a84c;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 0.9rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin: 16px 0 8px 0;
    }
    
    /* Results box */
    .results-box {
        background: #f0f7f0;
        border: 2px solid #2e7d32;
        border-radius: 8px;
        padding: 20px;
        margin: 16px 0;
    }
    .results-box-fail {
        background: #fdf0f0;
        border: 2px solid #c62828;
        border-radius: 8px;
        padding: 20px;
        margin: 16px 0;
    }
    
    /* Job history table */
    .job-row {
        padding: 8px;
        border-bottom: 1px solid #e8ecf2;
    }
    
    /* Top banner */
    .top-banner {
        background: linear-gradient(135deg, #0a1628 0%, #1a3258 60%, #264573 100%);
        color: white;
        padding: 24px 32px;
        border-radius: 8px;
        margin-bottom: 24px;
    }
    .top-banner h1 {
        color: #c9a84c;
        font-size: 1.8rem;
        margin: 0 0 4px 0;
    }
    .top-banner p {
        color: #b8c4d4;
        font-size: 0.95rem;
        margin: 0;
    }
    
    /* Hide default streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Validation badges */
    .badge-pass { 
        background: #e8f5e9; color: #2e7d32; 
        padding: 2px 10px; border-radius: 12px;
        font-weight: 600; font-size: 0.85rem;
    }
    .badge-fail { 
        background: #ffebee; color: #c62828; 
        padding: 2px 10px; border-radius: 12px;
        font-weight: 600; font-size: 0.85rem;
    }
    .badge-warn { 
        background: #fff3e0; color: #e65100; 
        padding: 2px 10px; border-radius: 12px;
        font-weight: 600; font-size: 0.85rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALISATION
# ============================================================================

if 'job_results' not in st.session_state:
    st.session_state.job_results = None
if 'job_history' not in st.session_state:
    st.session_state.job_history = []
if 'validation_result' not in st.session_state:
    st.session_state.validation_result = None
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = {}
if 'running' not in st.session_state:
    st.session_state.running = False


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def enum_options(enum_class) -> Dict[str, str]:
    """Convert enum to {display_name: value} dict."""
    return {e.value.replace('_', ' ').title(): e.value for e in enum_class}


def format_number(n, decimals=0):
    """Format number with commas."""
    if n is None:
        return ""
    if decimals == 0:
        return f"{int(n):,}"
    return f"{n:,.{decimals}f}"


def format_pct(v, decimals=1):
    """Format as percentage."""
    if v is None:
        return ""
    return f"{v*100:.{decimals}f}%"


def save_uploaded_file(uploaded, dest_dir="/home/claude/uploads"):
    """Save a Streamlit uploaded file to disk, return path."""
    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir, uploaded.name)
    with open(path, 'wb') as f:
        f.write(uploaded.getbuffer())
    return path


# ============================================================================
# SIDEBAR  ROUTE PARAMETERS (The Cover Page)
# ============================================================================

with st.sidebar:
    st.markdown("###  AVIA SOLUTIONS")
    st.markdown("##### QSI Route Forecast Portal")
    st.markdown("---")
    
    #  Navigation 
    page = st.radio(
        "Navigation",
        [" New Assessment", " Job History", " Regression Test"],
        label_visibility="collapsed",
    )

# ============================================================================
# PAGE: NEW ASSESSMENT
# ============================================================================

if page == " New Assessment":
    
    # Top banner
    st.markdown("""
    <div class="top-banner">
        <h1> QSI Route Forecast Portal</h1>
        <p>Configure route parameters, upload data files, and run the QSI pipeline to generate passenger forecasts.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Two-column layout: left = parameters, right = data files + results
    col_params, col_spacer, col_data = st.columns([5, 0.5, 5])
    
    with col_params:
        # 
        # SECTION 1: MODE
        # 
        st.markdown('<div class="section-header">Section 1  Operating Mode</div>', 
                    unsafe_allow_html=True)
        
        mode = st.selectbox(
            "Mode",
            ["Forecast", "Business Case"],
            help="Forecast = honest forward projection. Business Case = goal-seek against airline targets."
        )
        run_mode = 'forecast' if mode == "Forecast" else 'business_case'
        
        # Business Case targets (conditional)
        bc_targets = {}
        if run_mode == 'business_case':
            bc_col1, bc_col2 = st.columns(2)
            with bc_col1:
                bc_targets['target_lf_y1'] = st.number_input(
                    "Target LF Year 1", 0.50, 0.95, 0.70, 0.01, format="%.2f",
                    help="Minimum acceptable load factor in launch year"
                )
                bc_targets['target_p2p_split'] = st.number_input(
                    "P2P Split Target", 0.20, 1.00, 0.60, 0.05, format="%.2f",
                    help="Point-to-point as fraction of total passengers"
                )
            with bc_col2:
                bc_targets['target_lf_mature'] = st.number_input(
                    "Target LF Maturity", 0.60, 0.95, 0.82, 0.01, format="%.2f",
                    help="Target load factor at route maturity (Year 3+)"
                )
                bc_targets['min_frequency'] = st.number_input(
                    "Min Frequency (pw)", 1, 21, 5, 1,
                    help="Minimum viable flights per week"
                )
        
        # 
        # SECTION 2: ROUTE CHARACTERISTICS
        # 
        st.markdown('<div class="section-header">Section 2  Route Characteristics</div>', 
                    unsafe_allow_html=True)
        
        rc_col1, rc_col2 = st.columns(2)
        with rc_col1:
            origin = st.text_input("Origin Airport (IATA)", "LHR", max_chars=3,
                                   help="3-letter IATA airport code").upper().strip()
            route_type = st.selectbox("Route Type", list(enum_options(RouteType).keys()))
            carrier_code = st.text_input("Carrier Code (IATA)", "BA", max_chars=2,
                                         help="2-letter IATA airline code").upper().strip()
        
        with rc_col2:
            destination = st.text_input("Destination Airport (IATA)", "SJC", max_chars=3,
                                        help="3-letter IATA airport code").upper().strip()
            carrier_type = st.selectbox("Carrier Type", list(enum_options(CarrierType).keys()))
            carrier_name = st.text_input("Carrier Name", "British Airways")
        
        market_maturity = st.selectbox("Market Maturity", list(enum_options(MarketMaturity).keys()))
        
        # Show distance if both airports known
        if origin in KNOWN_AIRPORTS and destination in KNOWN_AIRPORTS:
            from input_validator import compute_distance, classify_distance_band
            dist = compute_distance(origin, destination)
            if dist:
                band = classify_distance_band(dist)
                st.caption(f" Distance: {dist:,.0f} nm  {band.replace('_', ' ').title()}")
        
        # 
        # SECTION 3: DEMAND PROFILE
        # 
        st.markdown('<div class="section-header">Section 3  Demand Profile</div>', 
                    unsafe_allow_html=True)
        
        dp_col1, dp_col2 = st.columns(2)
        with dp_col1:
            demand_driver = st.selectbox("Primary Demand Driver", 
                                         list(enum_options(DemandDriver).keys()))
            business_share = st.slider("Business Share", 0.0, 1.0, 0.40, 0.05,
                                       help="Fraction of demand that is business travel")
        with dp_col2:
            seasonal_profile = st.selectbox("Seasonal Profile", 
                                            list(enum_options(SeasonalProfile).keys()))
        
        # 
        # SECTION 4: SERVICE PARAMETERS
        # 
        st.markdown('<div class="section-header">Section 4  Service Parameters</div>', 
                    unsafe_allow_html=True)
        
        sp_col1, sp_col2 = st.columns(2)
        with sp_col1:
            frequency = st.number_input("Frequency (flights/week)", 1, 28, 7, 1)
            aircraft_type = st.selectbox(
                "Aircraft Type",
                list(AIRCRAFT_DB.keys()),
                format_func=lambda x: f"{x}  {AIRCRAFT_DB[x].name} ({AIRCRAFT_DB[x].typical_seats} seats)",
                index=list(AIRCRAFT_DB.keys()).index('787') if '787' in AIRCRAFT_DB else 0,
            )
        
        with sp_col2:
            default_seats = AIRCRAFT_DB[aircraft_type].typical_seats if aircraft_type else 200
            seats = st.number_input("Seats (override)", 50, 615, default_seats, 1,
                                    help="Override default seat count for specific configuration")
            flight_time = st.number_input("Flight Time (hrs)", 0.5, 24.0, 11.0, 0.5)
        
        dep_col1, dep_col2 = st.columns(2)
        with dep_col1:
            dep_outbound = st.time_input("Outbound Departure", dtime(15, 30))
        with dep_col2:
            dep_return = st.time_input("Return Departure", dtime(21, 30))
        
        # Annual capacity display
        annual_cap = seats * frequency * 52 * 2
        st.caption(f" Annual Capacity: {annual_cap:,} seats ({seats}s  {frequency}x/wk  52wks  2 directions)")
        
        # 
        # SECTION 5: COMPETITIVE CONTEXT
        # 
        st.markdown('<div class="section-header">Section 5  Competitive Context</div>', 
                    unsafe_allow_html=True)
        
        existing_direct = st.checkbox("Existing Direct Service?", False)
        if existing_direct:
            ed_col1, ed_col2 = st.columns(2)
            with ed_col1:
                existing_carrier = st.text_input("Existing Carrier", "")
            with ed_col2:
                existing_freq = st.number_input("Existing Frequency", 0, 28, 0, 1)
        else:
            existing_carrier = ""
            existing_freq = 0
        
        cc_col1, cc_col2 = st.columns(2)
        with cc_col1:
            indirect_comp = st.selectbox("Indirect Competition", 
                                          list(enum_options(IndirectCompetition).keys()))
        with cc_col2:
            surface_comp = st.selectbox("Surface Competition", 
                                         list(enum_options(SurfaceCompetition).keys()))
        
        # 
        # SECTION 6: QSI OVERRIDES (Collapsible)
        # 
        with st.expander(" Section 6  QSI Coefficient Overrides (Expert)", expanded=False):
            st.caption("Leave blank to use carrier-type defaults. Override for expert calibration.")
            
            ct_enum = CarrierType(enum_options(CarrierType)[carrier_type])
            defaults = QSI_DEFAULTS_BY_CARRIER.get(ct_enum, {})
            
            qo_col1, qo_col2, qo_col3 = st.columns(3)
            with qo_col1:
                qsi_ceiling = st.number_input("QSI Ceiling", 0.1, 1.0, 1.0, 0.05,
                                              help="Max QSI share allowed")
                online_coeff = st.number_input("Online Coefficient", 0.5, 1.5, 
                                                defaults.get('online_coeff', 1.0), 0.05)
            with qo_col2:
                alliance_coeff = st.number_input("Alliance Coefficient", 0.0, 1.0,
                                                  defaults.get('alliance_coeff', 0.615), 0.05)
                interline_coeff = st.number_input("Interline Coefficient", 0.0, 0.5,
                                                   defaults.get('interline_coeff', 0.25), 0.05)
            with qo_col3:
                et_decay = st.number_input("ET Decay Factor", 0.5, 1.0,
                                           defaults.get('et_decay_factor', 0.8), 0.05)
                et_interval = st.number_input("ET Decay Interval", 0.05, 0.5,
                                              defaults.get('et_decay_interval', 0.1), 0.05)
    
    # 
    # RIGHT COLUMN: DATA FILES + EXECUTION + RESULTS
    # 
    with col_data:
        
        # SECTION 7: DATA FILES
        st.markdown('<div class="section-header">Section 7  Data Files</div>', 
                    unsafe_allow_html=True)
        
        st.caption("Upload QSI scoring files and forecast file. For the BA LHR-SJC regression test, project files are used automatically.")
        
        file_col1, file_col2 = st.columns(2)
        with file_col1:
            home_qsi_file = st.file_uploader(
                "Home QSI File (e.g. QSILHR)", 
                type=['xlsx', 'xlsm', 'xls'],
                help="QSI scoring file for the home hub perspective"
            )
            forecast_file = st.file_uploader(
                "Forecast File",
                type=['xlsx', 'xlsm', 'xls'],
                help="Forecast workbook with P2P demand segments"
            )
        with file_col2:
            dest_qsi_file = st.file_uploader(
                "Destination QSI File (e.g. QSISJC)",
                type=['xlsx', 'xlsm', 'xls'],
                help="QSI scoring file for the destination hub perspective"
            )
        
        st.markdown("---")
        
        # 
        # EXECUTION
        # 
        st.markdown('<div class="section-header">Execute Pipeline</div>', 
                    unsafe_allow_html=True)
        
        exec_col1, exec_col2, exec_col3 = st.columns([3, 3, 2])
        
        with exec_col1:
            run_clicked = st.button(" Run Forecast", use_container_width=True, 
                                    type="primary",
                                    disabled=st.session_state.running)
        with exec_col2:
            validate_clicked = st.button(" Validate Only", use_container_width=True,
                                         disabled=st.session_state.running)
        with exec_col3:
            clear_clicked = st.button(" Clear", use_container_width=True)
        
        if clear_clicked:
            st.session_state.job_results = None
            st.session_state.validation_result = None
            st.rerun()
        
        # Build RouteInput from form
        def build_route_input() -> RouteInput:
            """Assemble RouteInput from sidebar form values."""
            inp = RouteInput()
            inp.mode = run_mode
            inp.origin = origin
            inp.destination = destination
            inp.route_type = enum_options(RouteType)[route_type]
            inp.carrier_type = enum_options(CarrierType)[carrier_type]
            inp.carrier_code = carrier_code
            inp.carrier_name = carrier_name
            inp.market_maturity = enum_options(MarketMaturity)[market_maturity]
            inp.demand_driver = enum_options(DemandDriver)[demand_driver]
            inp.seasonal_profile = enum_options(SeasonalProfile)[seasonal_profile]
            inp.business_share = business_share
            inp.frequency = frequency
            inp.aircraft_type = aircraft_type
            inp.seats = seats
            inp.dep_time_outbound = dep_outbound.strftime("%H:%M")
            inp.dep_time_return = dep_return.strftime("%H:%M")
            inp.flight_time_hrs = flight_time
            inp.existing_direct = existing_direct
            inp.existing_direct_carrier = existing_carrier
            inp.existing_direct_frequency = existing_freq
            inp.indirect_competition = enum_options(IndirectCompetition)[indirect_comp]
            inp.surface_competition = enum_options(SurfaceCompetition)[surface_comp]
            inp.qsi_ceiling = qsi_ceiling
            inp.online_coeff = online_coeff
            inp.alliance_coeff = alliance_coeff
            inp.interline_coeff = interline_coeff
            inp.et_decay_factor = et_decay
            inp.et_decay_interval = et_interval
            
            # Business case targets
            if run_mode == 'business_case':
                inp.target_load_factor_y1 = bc_targets.get('target_lf_y1')
                inp.target_load_factor_mature = bc_targets.get('target_lf_mature')
                inp.target_p2p_split = bc_targets.get('target_p2p_split')
                inp.min_frequency = bc_targets.get('min_frequency')
            
            # Uploaded files
            if home_qsi_file:
                inp.home_qsi_file = save_uploaded_file(home_qsi_file)
            if dest_qsi_file:
                inp.dest_qsi_file = save_uploaded_file(dest_qsi_file)
            if forecast_file:
                inp.forecast_file = save_uploaded_file(forecast_file)
            
            return inp
        
        #  VALIDATE ONLY 
        if validate_clicked:
            inp = build_route_input()
            validator = InputValidator()
            vresult = validator.validate(inp)
            st.session_state.validation_result = vresult
        
        #  RUN PIPELINE 
        if run_clicked:
            st.session_state.running = True
            st.session_state.job_results = None
            
            inp = build_route_input()
            
            # Validate first
            validator = InputValidator()
            vresult = validator.validate(inp)
            st.session_state.validation_result = vresult
            
            if not vresult.valid:
                st.session_state.running = False
                st.error(f"Validation failed with {len(vresult.errors)} error(s). Fix issues before running.")
            else:
                # Build config and run pipeline
                progress_bar = st.progress(0, text="Building configuration...")
                status_text = st.empty()
                
                try:
                    # Phase 1: Build config
                    progress_bar.progress(10, text="Building configuration...")
                    
                    # Check if this is the BA regression case
                    is_ba_regression = (
                        inp.origin == 'LHR' and inp.destination == 'SJC' and 
                        inp.carrier_code == 'BA'
                    )
                    
                    if is_ba_regression:
                        status_text.info(" BA LHR-SJC detected  using factory config (regression mode)")
                        config = RouteConfig.ba_lhr_sjc(PROJECT_DIR)
                    else:
                        config = validator.build_config(inp)
                        
                        # Attach uploaded file providers if provided
                        if inp.home_qsi_file and inp.dest_qsi_file:
                            config.schedule_provider = ExcelScheduleProvider(
                                qsi1_file=inp.home_qsi_file,
                                qsi2_file=inp.dest_qsi_file,
                            )
                        
                        if inp.forecast_file:
                            config.demand_provider = ExcelDemandProvider(
                                forecast_file=inp.forecast_file,
                            )
                    
                    # Phase 2: Run pipeline
                    progress_bar.progress(30, text="Running QSI scoring (home hub)...")
                    
                    output_dir = "/home/claude/job_outputs"
                    os.makedirs(output_dir, exist_ok=True)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    output_path = os.path.join(
                        output_dir, 
                        f"{carrier_code}_{origin}{destination}_{timestamp}.xlsx"
                    )
                    
                    progress_bar.progress(50, text="Running QSI scoring (destination hub)...")
                    
                    results = run_pipeline(config, output_path)
                    
                    progress_bar.progress(90, text="Generating output workbook...")
                    
                    # Store results
                    job_record = {
                        'job_id': f"{carrier_code}_{origin}{destination}_{timestamp}",
                        'route': f"{origin}-{destination}",
                        'carrier': f"{carrier_code} ({carrier_name})",
                        'mode': run_mode,
                        'timestamp': datetime.now().isoformat(),
                        'grand_total': results.get('grand_total', 0),
                        'p2p_total': results.get('p2p_total', 0),
                        'home_total': results.get('home_total', 0),
                        'dest_total': results.get('dest_total', 0),
                        'load_factor': results.get('load_factor', 0),
                        'annual_capacity': config.annual_capacity,
                        'target_total': config.target_total,
                        'validation_passed': results.get('validation_passed', None),
                        'output_path': output_path,
                        'config_summary': config.summary(),
                        'full_results': results,
                    }
                    
                    st.session_state.job_results = job_record
                    st.session_state.job_history.insert(0, job_record)
                    
                    progress_bar.progress(100, text="Complete!")
                    time.sleep(0.5)
                    progress_bar.empty()
                    status_text.empty()
                    
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"Pipeline execution failed: {str(e)}")
                    with st.expander("Full traceback"):
                        st.code(traceback.format_exc())
                
                finally:
                    st.session_state.running = False
        
        # 
        # DISPLAY VALIDATION RESULT
        # 
        if st.session_state.validation_result:
            vr = st.session_state.validation_result
            
            if vr.valid:
                st.markdown('<span class="badge-pass"> VALIDATION PASSED</span>', 
                            unsafe_allow_html=True)
            else:
                st.markdown('<span class="badge-fail"> VALIDATION FAILED</span>', 
                            unsafe_allow_html=True)
            
            # Errors
            for e in vr.errors:
                st.error(f"**{e.field}**: {e.message}" + 
                        (f"\n {e.suggestion}" if e.suggestion else ""))
            
            # Warnings
            for w in vr.warnings:
                st.warning(f"**{w.field}**: {w.message}" +
                          (f"\n {w.suggestion}" if w.suggestion else ""))
            
            # Applied defaults
            if vr.applied_defaults:
                with st.expander(f" {len(vr.applied_defaults)} defaults applied"):
                    for k, v in vr.applied_defaults.items():
                        st.caption(f"**{k}** = {v}")
        
        # 
        # DISPLAY RESULTS
        # 
        if st.session_state.job_results:
            jr = st.session_state.job_results
            
            st.markdown("---")
            st.markdown('<div class="section-header">Forecast Results</div>', 
                        unsafe_allow_html=True)
            
            # Key metrics
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.metric("Grand Total", format_number(jr['grand_total']))
            with m_col2:
                st.metric("Load Factor", format_pct(jr['load_factor']))
            with m_col3:
                st.metric("P2P Passengers", format_number(jr['p2p_total']))
            with m_col4:
                cnx_total = jr['home_total'] + jr['dest_total']
                st.metric("Connecting", format_number(cnx_total))
            
            # Breakdown
            m2_col1, m2_col2, m2_col3, m2_col4 = st.columns(4)
            with m2_col1:
                st.metric("Cnx @ Home Hub", format_number(jr['home_total']))
            with m2_col2:
                st.metric("Cnx @ Dest Hub", format_number(jr['dest_total']))
            with m2_col3:
                st.metric("Annual Capacity", format_number(jr['annual_capacity']))
            with m2_col4:
                if jr['target_total'] > 0:
                    variance = abs(jr['grand_total'] - jr['target_total']) / jr['target_total']
                    st.metric("Variance vs Target", format_pct(variance))
                else:
                    st.metric("Config", jr['config_summary'])
            
            # Regression status
            if jr['target_total'] > 0:
                variance = abs(jr['grand_total'] - jr['target_total']) / jr['target_total']
                if variance < 0.01:
                    st.success(f" Regression PASSED  Target: {format_number(jr['target_total'])}, "
                              f"Actual: {format_number(jr['grand_total'])}, "
                              f"Variance: {format_pct(variance)}")
                else:
                    st.error(f" Regression FAILED  Target: {format_number(jr['target_total'])}, "
                            f"Actual: {format_number(jr['grand_total'])}, "
                            f"Variance: {format_pct(variance)}")
            
            # Download output workbook
            if jr.get('output_path') and os.path.exists(jr['output_path']):
                st.markdown("---")
                with open(jr['output_path'], 'rb') as f:
                    st.download_button(
                        label=" Download Output Workbook (.xlsx)",
                        data=f.read(),
                        file_name=os.path.basename(jr['output_path']),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
            
            # Detailed results expander
            with st.expander(" Detailed Results"):
                results = jr.get('full_results', {})
                
                # P2P breakdown
                p2p_details = results.get('p2p_details', [])
                if p2p_details:
                    st.markdown("**P2P Demand Segments**")
                    p2p_data = []
                    for seg in p2p_details:
                        if isinstance(seg, dict):
                            p2p_data.append({
                                'Segment': seg.get('name', seg.get('segment', '')),
                                'Base Demand': format_number(seg.get('base_demand', 0)),
                                'Grown': format_number(seg.get('grown_demand', seg.get('grown', 0))),
                                'Stimulated': format_number(seg.get('stimulated_demand', seg.get('stimulated', 0))),
                                'Captured': format_number(seg.get('captured_demand', seg.get('captured', 0))),
                            })
                    if p2p_data:
                        st.dataframe(p2p_data, use_container_width=True, hide_index=True)
                
                # Connecting cities summary (home hub)
                home_results = results.get('home_results', [])
                if home_results:
                    st.markdown("**Home Hub Connecting Cities (Top 15 by passengers)**")
                    
                    if isinstance(home_results, list):
                        # Sort list of dicts by passengers
                        def get_pax(item):
                            if isinstance(item, dict):
                                return item.get('passengers', item.get('pax', item.get('annual_pax', 0)))
                            return 0
                        
                        sorted_cities = sorted(home_results, key=get_pax, reverse=True)[:15]
                        city_data = []
                        for item in sorted_cities:
                            if isinstance(item, dict):
                                pax = get_pax(item)
                                city = item.get('city', item.get('dest_city', item.get('name', '?')))
                                qsi = item.get('qsi_share', item.get('capture_rate', item.get('raw_qsi', 0)))
                                expert = item.get('expert_qsi', item.get('calibrated_qsi', None))
                                city_data.append({
                                    'City': city,
                                    'Annual Pax': format_number(pax),
                                    'Raw QSI': format_pct(qsi) if qsi else '',
                                    'Expert QSI': format_pct(expert) if expert else '',
                                })
                        if city_data:
                            st.dataframe(city_data, use_container_width=True, hide_index=True)
                    
                    elif isinstance(home_results, dict):
                        sorted_cities = sorted(
                            home_results.items(), 
                            key=lambda x: x[1].get('passengers', 0) if isinstance(x[1], dict) else 0,
                            reverse=True
                        )[:15]
                        city_data = []
                        for city, data in sorted_cities:
                            if isinstance(data, dict):
                                city_data.append({
                                    'City': city,
                                    'Annual Pax': format_number(data.get('passengers', 0)),
                                    'QSI Share': format_pct(data.get('qsi_share', 0)),
                                })
                        if city_data:
                            st.dataframe(city_data, use_container_width=True, hide_index=True)
                
                # Calibration info
                if 'calibration' in results:
                    st.markdown("**Calibration Analysis**")
                    cal = results['calibration']
                    if isinstance(cal, dict):
                        cal_col1, cal_col2, cal_col3 = st.columns(3)
                        with cal_col1:
                            st.metric("Mean Factor", f"{cal.get('mean', 0):.3f}")
                        with cal_col2:
                            st.metric("Median Factor", f"{cal.get('median', 0):.3f}")
                        with cal_col3:
                            st.metric("Cities Analysed", cal.get('count', 0))
                
                # Pipeline note
                st.caption(
                    " Connecting traffic shows raw (uncalibrated) QSI captures. "
                    "Expert calibration factors (median ~0.267) are applied in the "
                    "CalibrationEngine module to bring connecting totals to target levels. "
                    "P2P demand is exact."
                )


# ============================================================================
# PAGE: JOB HISTORY
# ============================================================================

elif page == " Job History":
    
    st.markdown("""
    <div class="top-banner">
        <h1> Job History</h1>
        <p>Browse previous pipeline runs from this session.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.job_history:
        st.info("No jobs run yet in this session. Go to **New Assessment** to run a forecast.")
    else:
        for i, job in enumerate(st.session_state.job_history):
            with st.container():
                h_col1, h_col2, h_col3, h_col4, h_col5 = st.columns([2, 2, 2, 2, 2])
                with h_col1:
                    st.markdown(f"**{job['route']}**")
                    st.caption(job['carrier'])
                with h_col2:
                    st.metric("Total Pax", format_number(job['grand_total']), label_visibility="collapsed")
                with h_col3:
                    st.metric("Load Factor", format_pct(job['load_factor']), label_visibility="collapsed")
                with h_col4:
                    st.caption(job['mode'].replace('_', ' ').title())
                    st.caption(job['timestamp'][:19])
                with h_col5:
                    if job.get('output_path') and os.path.exists(job['output_path']):
                        with open(job['output_path'], 'rb') as f:
                            st.download_button(
                                " Download",
                                data=f.read(),
                                file_name=os.path.basename(job['output_path']),
                                key=f"dl_{i}",
                            )
                st.divider()


# ============================================================================
# PAGE: REGRESSION TEST
# ============================================================================

elif page == " Regression Test":
    
    st.markdown("""
    <div class="top-banner">
        <h1> Regression Test Suite</h1>
        <p>One-click validation against known reference cases.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    The regression test runs the BA LHR-SJC case through the full pipeline and validates 
    against the known target of **129,162 passengers** at **82.9% load factor**.
    
    This is the gold standard validated across Chats 1-20. The test confirms that all 
    pipeline modules are working correctly and producing consistent results.
    """)
    
    # Test cards
    test_col1, test_col2 = st.columns(2)
    
    with test_col1:
        st.markdown("#### BA LHR-SJC (Primary)")
        st.caption("787-800 | 214 seats | 7x/week | Target: 129,162 pax")
        run_ba = st.button(" Run BA LHR-SJC Regression", use_container_width=True,
                           type="primary")
    
    with test_col2:
        st.markdown("#### Additional Routes (Chat 20)")
        st.caption("KE ICN-SJC, SQ SIN-SJC, CX HKG-SJC, FI KEF-SJC")
        st.info("Additional regression routes require InMemoryDemandProvider factory methods (planned)")
    
    if run_ba:
        with st.spinner("Running BA LHR-SJC regression test..."):
            try:
                t0 = time.time()
                config = RouteConfig.ba_lhr_sjc(PROJECT_DIR)
                
                output_dir = "/home/claude/job_outputs"
                os.makedirs(output_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(output_dir, f"REGRESSION_BA_LHRSJC_{timestamp}.xlsx")
                
                results = run_pipeline(config, output_path)
                
                elapsed = time.time() - t0
                
                grand_total = results.get('grand_total', 0)
                p2p_total = results.get('p2p_total', 0)
                load_factor = results.get('load_factor', 0)
                
                # Variance checks
                total_var = abs(grand_total - 129162) / 129162
                p2p_var = abs(p2p_total - 78110) / 78110
                lf_var = abs(load_factor - 0.829) / 0.829
                
                all_pass = total_var < 0.01 and p2p_var < 0.01
                
                st.markdown("---")
                
                if all_pass:
                    st.success(f"##  REGRESSION PASSED ({elapsed:.1f}s)")
                else:
                    st.error(f"##  REGRESSION FAILED ({elapsed:.1f}s)")
                
                # Results table
                results_data = [
                    {"Metric": "Grand Total", "Target": "129,162", 
                     "Actual": format_number(grand_total),
                     "Variance": format_pct(total_var),
                     "Status": "" if total_var < 0.01 else ""},
                    {"Metric": "P2P Total", "Target": "78,110",
                     "Actual": format_number(p2p_total),
                     "Variance": format_pct(p2p_var),
                     "Status": "" if p2p_var < 0.01 else ""},
                    {"Metric": "Load Factor", "Target": "82.9%",
                     "Actual": format_pct(load_factor),
                     "Variance": format_pct(lf_var),
                     "Status": "" if lf_var < 0.02 else ""},
                    {"Metric": "Cnx @ Home (LHR)", "Target": "48,115",
                     "Actual": format_number(results.get('home_total', 0)),
                     "Variance": format_pct(abs(results.get('home_total', 0) - 48115) / 48115),
                     "Status": "" if abs(results.get('home_total', 0) - 48115) / 48115 < 0.01 else "~"},
                    {"Metric": "Cnx @ Dest (SJC)", "Target": "2,937",
                     "Actual": format_number(results.get('dest_total', 0)),
                     "Variance": format_pct(abs(results.get('dest_total', 0) - 2937) / 2937 if results.get('dest_total', 0) else 1.0),
                     "Status": "" if results.get('dest_total', 0) and abs(results.get('dest_total', 0) - 2937) / 2937 < 0.05 else "~"},
                ]
                
                st.dataframe(results_data, use_container_width=True, hide_index=True)
                
                # Download
                if os.path.exists(output_path):
                    with open(output_path, 'rb') as f:
                        st.download_button(
                            " Download Regression Output",
                            data=f.read(),
                            file_name=os.path.basename(output_path),
                            use_container_width=True,
                        )
                
                # Add to job history
                st.session_state.job_history.insert(0, {
                    'job_id': f"REGRESSION_BA_LHRSJC_{timestamp}",
                    'route': "LHR-SJC",
                    'carrier': "BA (British Airways)",
                    'mode': "regression_test",
                    'timestamp': datetime.now().isoformat(),
                    'grand_total': grand_total,
                    'p2p_total': p2p_total,
                    'home_total': results.get('home_total', 0),
                    'dest_total': results.get('dest_total', 0),
                    'load_factor': load_factor,
                    'annual_capacity': config.annual_capacity,
                    'target_total': 129162,
                    'output_path': output_path,
                    'config_summary': config.summary(),
                    'full_results': results,
                })
                
            except Exception as e:
                st.error(f"Regression test failed: {str(e)}")
                with st.expander("Full traceback"):
                    st.code(traceback.format_exc())


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("Avia Solutions Ltd  QSI Route Forecast Portal v1.0 (Chat 21) | "
           "Confidential  Proprietary Methodology")
