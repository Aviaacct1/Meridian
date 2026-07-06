#!/usr/bin/env python3
"""
Avia Solutions  QSI Route Forecast Portal v4.0 (Chat 28)
==========================================================
Streamlit web portal with two data-source paths:

PATH A  Pre-computed QSI (existing, validated):
  Upload separate Home QSI + Dest QSI + Forecast file.
  Uses ExcelScheduleProvider + ExcelDemandProvider.
  This is the Chat 22 workflow, unchanged.

PATH B  New Route Assessment (new):
  Upload a SINGLE QSI template file (with Leg 1.1/2.1/1.2/2.2 sheets).
  Upload raw Sabre/MIDT files for connecting demand.
  Uses SingleExtractOAGProvider + MIDTDemandProvider.
  This enables genuinely new route assessments without pre-computed files.

Completes the three-chat plan from Chat 23:
  Chat 24: SingleExtractOAGProvider
  Chat 25: MIDTDemandProvider
  Chat 26: Portal integration (this file)

Regression target: BA LHR-SJC = 129,162 passengers (Path A, unchanged).
"""

import os
import sys
import io
import tempfile
import traceback
from datetime import datetime, time as dtime
from typing import Dict, Optional, Any, List

import streamlit as st
import pandas as pd

#  Pipeline imports 
from providers import (
    ExcelScheduleProvider, ExcelDemandProvider,
    P2PSegmentData, P2PSubsegmentData, ConnectingCityData,
)
from single_extract_oag_provider import SingleExtractOAGProvider
from midt_demand_provider import MIDTDemandProvider
from route_config import RouteConfig
from closed_loop_pipeline_v2 import run_pipeline
from departure_time_grid import (
    TimeShiftProvider, TimeGridRunner, GridSearchResult,
    write_grid_output,
)
from input_validator import (
    KNOWN_AIRPORTS, AIRCRAFT_DB,
    RouteInput, InputValidator, ValidationResult,
    lookup_airport, compute_distance, classify_distance_band,
)


# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Avia Solutions  QSI Route Forecast",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================================
# CUSTOM STYLING
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    .stApp { font-family: 'DM Sans', sans-serif; }

    .portal-header {
        background: linear-gradient(135deg, #0a1628 0%, #1a2d4a 50%, #0d3b66 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border-bottom: 3px solid #e8a83e;
    }
    .portal-header h1 {
        color: #ffffff; font-family: 'DM Sans', sans-serif;
        font-weight: 700; font-size: 1.8rem; margin: 0; letter-spacing: -0.5px;
    }
    .portal-header p { color: #8ba4c4; font-size: 0.9rem; margin: 0.3rem 0 0 0; }

    .metric-card {
        background: #f8f9fc; border: 1px solid #e2e8f0;
        border-radius: 10px; padding: 1.2rem; text-align: center;
    }
    .metric-card .label {
        font-size: 0.75rem; color: #6b7c93; text-transform: uppercase;
        letter-spacing: 0.5px; font-weight: 600;
    }
    .metric-card .value {
        font-size: 1.6rem; font-weight: 700; color: #0a1628;
        font-family: 'JetBrains Mono', monospace; margin-top: 0.3rem;
    }
    .metric-card .sub { font-size: 0.7rem; color: #8ba4c4; margin-top: 0.2rem; }

    .verdict-pass {
        background: #d4edda; color: #155724; padding: 0.4rem 1rem;
        border-radius: 6px; font-weight: 700; display: inline-block; font-size: 0.85rem;
    }
    .verdict-fail {
        background: #f8d7da; color: #721c24; padding: 0.4rem 1rem;
        border-radius: 6px; font-weight: 700; display: inline-block; font-size: 0.85rem;
    }
    .verdict-marginal {
        background: #fff3cd; color: #856404; padding: 0.4rem 1rem;
        border-radius: 6px; font-weight: 700; display: inline-block; font-size: 0.85rem;
    }

    .section-label {
        font-size: 0.7rem; font-weight: 600; color: #6b7c93;
        text-transform: uppercase; letter-spacing: 1px;
        margin-bottom: 0.5rem; padding-bottom: 0.3rem; border-bottom: 2px solid #e8a83e;
    }

    .path-card {
        border: 2px solid #e2e8f0; border-radius: 10px; padding: 1rem;
        margin-bottom: 0.5rem;
    }
    .path-card.active { border-color: #e8a83e; background: #fdf8ef; }
    .path-card h4 { margin: 0 0 0.3rem 0; color: #0a1628; font-size: 0.95rem; }
    .path-card p { margin: 0; color: #6b7c93; font-size: 0.8rem; }

    .provider-badge {
        display: inline-block; padding: 0.2rem 0.6rem; border-radius: 12px;
        font-size: 0.7rem; font-weight: 600; letter-spacing: 0.5px;
    }
    .provider-badge.precomputed { background: #e2efda; color: #155724; }
    .provider-badge.newroute { background: #cce5ff; color: #004085; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# HEADER
# ============================================================================

st.markdown("""
<div class="portal-header">
    <h1> QSI Route Forecast Portal</h1>
    <p>Avia Solutions  Quality of Service Index Pipeline v4.0 &nbsp; | &nbsp;
    22 modules &nbsp; | &nbsp; Pre-computed + New Route Assessment</p>
</div>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE
# ============================================================================

defaults = {
    'results': None,
    'output_bytes': None,
    'run_log': [],
    'last_config_summary': "",
    'p2p_segments': [],
    'data_source': 'precomputed',
    'grid_results': [],
    'grid_output_bytes': None,
    'grid_search_result': None,
    'last_grid_config': None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ============================================================================
# HELPERS
# ============================================================================

def save_uploaded(uploaded_file) -> str:
    """Save an uploaded file to a temp location and return the path."""
    tmp_dir = tempfile.mkdtemp()
    path = os.path.join(tmp_dir, uploaded_file.name)
    with open(path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return path


def save_multiple_uploads(uploaded_files) -> List[str]:
    """Save multiple uploaded files and return list of paths."""
    paths = []
    for uf in (uploaded_files or []):
        paths.append(save_uploaded(uf))
    return paths


def fmt(n, decimals=0):
    if n is None:
        return ""
    if isinstance(n, float) and 0 < n < 1:
        return f"{n:.1%}"
    if decimals > 0:
        return f"{n:,.{decimals}f}"
    return f"{int(n):,}"


def metric_card(label, value, sub=""):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    return f'<div class="metric-card"><div class="label">{label}</div><div class="value">{value}</div>{sub_html}</div>'


# ============================================================================
# SIDEBAR  ROUTE CONFIGURATION
# ============================================================================

with st.sidebar:
    st.markdown("###  Route Configuration")

    #  DATA SOURCE SELECTION 
    st.markdown('<div class="section-label">Data Source</div>', unsafe_allow_html=True)
    data_source = st.radio(
        "Assessment type",
        ["Pre-computed QSI Files", "New Route Assessment"],
        horizontal=True,
        help="Pre-computed: use existing QSI workbooks. New Route: build from raw OAG legs + MIDT demand.",
        label_visibility="collapsed",
    )
    st.session_state.data_source = 'precomputed' if data_source == "Pre-computed QSI Files" else 'newroute'

    if st.session_state.data_source == 'precomputed':
        st.markdown('<span class="provider-badge precomputed">VALIDATED PATH</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="provider-badge newroute">NEW ROUTE PATH</span>', unsafe_allow_html=True)

    #  Operating Mode 
    st.markdown('<div class="section-label">Operating Mode</div>', unsafe_allow_html=True)
    mode = st.selectbox("Mode", ["Forecast", "Business Case"])

    #  Route Identity 
    st.markdown('<div class="section-label">Route Identity</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        origin = st.text_input("Origin (IATA)", value="", max_chars=3, placeholder="LHR").upper().strip()
    with col2:
        destination = st.text_input("Dest (IATA)", value="", max_chars=3, placeholder="SJC").upper().strip()

    carrier_name = st.text_input("Airline Name", placeholder="British Airways")
    carrier_code = st.text_input("Airline Code", value="", max_chars=2, placeholder="BA").upper().strip()

    carrier_type = st.selectbox("Carrier Type",
        ["Full Service", "LCC", "Ultra LCC", "Hybrid", "Charter"])
    ct_map = {"Full Service": "full_service", "LCC": "lcc", "Ultra LCC": "ultra_lcc",
              "Hybrid": "hybrid", "Charter": "charter"}

    route_type = st.selectbox("Route Type",
        ["Long Haul", "Hub Feed", "LCC Point-to-Point", "Charter/Leisure", "Mixed"])

    market_maturity = st.selectbox("Market Maturity",
        ["New Route", "Existing Underserved", "Existing Competitive", "Mature"])

    #  Service Parameters 
    st.markdown('<div class="section-label">Service Parameters</div>', unsafe_allow_html=True)
    frequency = st.number_input("Weekly Frequency", min_value=1, max_value=28, value=7)

    ac_options = sorted(AIRCRAFT_DB.keys())
    ac_display = [f"{k}  {AIRCRAFT_DB[k].name} ({AIRCRAFT_DB[k].typical_seats}s)" for k in ac_options]
    ac_idx = st.selectbox("Aircraft Type", range(len(ac_options)),
                          format_func=lambda i: ac_display[i],
                          index=ac_options.index('787') if '787' in ac_options else 0)
    aircraft_type = ac_options[ac_idx]
    ac_spec = AIRCRAFT_DB[aircraft_type]
    seats = st.number_input("Seats", min_value=50, max_value=900, value=ac_spec.typical_seats)

    #  QSI Coefficients 
    st.markdown('<div class="section-label">QSI Coefficients</div>', unsafe_allow_html=True)
    is_lcc = ct_map[carrier_type] in ('lcc', 'ultra_lcc')
    online_coeff = st.number_input("Online", min_value=0.0, max_value=2.0, value=1.0, step=0.05, format="%.3f")
    alliance_coeff = st.number_input("Alliance", min_value=0.0, max_value=2.0,
                                     value=0.0 if is_lcc else 0.615, step=0.05, format="%.3f")
    interline_coeff = st.number_input("Interline", min_value=0.0, max_value=2.0,
                                      value=0.0 if is_lcc else 0.25, step=0.05, format="%.3f")
    qsi_ceiling = st.number_input("QSI Ceiling", min_value=0.1, max_value=2.0, value=1.0, step=0.05, format="%.2f")

    #  Growth Assumptions 
    st.markdown('<div class="section-label">Growth Assumptions</div>', unsafe_allow_html=True)
    home_growth = st.number_input("Home Growth", min_value=-0.10, max_value=0.30, value=0.09, step=0.01, format="%.2f")
    dest_growth = st.number_input("Dest Growth", min_value=-0.10, max_value=0.30, value=0.10, step=0.01, format="%.2f")

    #  New Route: MIDT settings 
    if st.session_state.data_source == 'newroute':
        st.markdown('<div class="section-label">MIDT / Sabre Settings</div>', unsafe_allow_html=True)
        catchment_share_home = st.number_input(
            "Catchment Share (Home)", min_value=0.0, max_value=1.0, value=1.0,
            step=0.05, format="%.2f",
            help="Share of broader catchment captured at home airport (e.g., SJC share of Bay Area)")
        catchment_share_dest = st.number_input(
            "Catchment Share (Dest)", min_value=0.0, max_value=1.0, value=1.0,
            step=0.05, format="%.2f")
        min_demand_threshold = st.number_input(
            "Min City Demand", min_value=0, max_value=1000, value=0,
            help="Minimum annual pax to include a connecting city")
    else:
        catchment_share_home = 1.0
        catchment_share_dest = 1.0
        min_demand_threshold = 0

    #  Distance calculation 
    if origin and destination and len(origin) == 3 and len(destination) == 3:
        dist = compute_distance(origin, destination)
        if dist:
            band = classify_distance_band(dist)
            st.info(f" {origin}{destination}: {dist:,.0f} nm ({band.replace('_', ' ')})")


# ============================================================================
# MAIN TABS
# ============================================================================

if st.session_state.data_source == 'newroute':
    tab1, tab2, tab3, tab4 = st.tabs([
        " Data Upload & Run", " Results", " Comparison", " Time Grid"
    ])
else:
    tab1, tab2, tab3 = st.tabs([
        " Data Upload & Run", " Results", " Comparison"
    ])
    tab4 = None


# ============================================================================
# TAB 1: UPLOAD & RUN
# ============================================================================

with tab1:

    # ================================================================
    # PATH A: PRE-COMPUTED QSI FILES
    # ================================================================
    if st.session_state.data_source == 'precomputed':
        st.markdown("### Upload Pre-computed QSI Files")
        st.caption("Upload the analyst-prepared QSI workbooks and forecast file. "
                    "This is the validated path matching Chat 22.")

        col_up1, col_up2, col_up3 = st.columns(3)
        with col_up1:
            st.markdown(f"**Home Hub QSI File** (QSI{origin or 'LHR'}.xlsx)")
            home_qsi_upload = st.file_uploader("Home QSI", type=['xlsx', 'xlsm', 'xls'],
                                               key='home_qsi', label_visibility="collapsed")
        with col_up2:
            st.markdown(f"**Destination QSI File** (QSI{destination or 'SJC'}.xlsx)")
            dest_qsi_upload = st.file_uploader("Dest QSI", type=['xlsx', 'xlsm', 'xls'],
                                               key='dest_qsi', label_visibility="collapsed")
        with col_up3:
            st.markdown("**Forecast / Demand File**")
            forecast_upload = st.file_uploader("Forecast", type=['xlsx', 'xlsm', 'xls'],
                                               key='forecast', label_visibility="collapsed")

    # ================================================================
    # PATH B: NEW ROUTE ASSESSMENT
    # ================================================================
    else:
        st.markdown("### New Route Assessment  Raw Data Upload")
        st.caption("Upload a QSI template file with OAG leg sheets and Sabre/MIDT demand files. "
                    "The system will auto-detect hubs, build connections, and compute QSI scores from scratch.")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("####  Schedule Data")
            st.markdown("**QSI Template File** (with Leg 1.1, 2.1, 1.2, 2.2 sheets)")
            qsi_template_upload = st.file_uploader(
                "QSI Template", type=['xlsx', 'xlsm', 'xls'],
                key='qsi_template', label_visibility="collapsed",
                help="Single QSI template file containing all OAG leg data")
            if qsi_template_upload:
                st.success(f" {qsi_template_upload.name}")

            st.markdown("**MCT Files** (optional  Minimum Connection Times)")
            mct_uploads = st.file_uploader(
                "MCT files", type=['xlsx', 'xlsm', 'xls'],
                key='mct_files', label_visibility="collapsed",
                accept_multiple_files=True)
            if mct_uploads:
                st.caption(f"{len(mct_uploads)} MCT file(s) uploaded")

        with col_b:
            st.markdown("####  Demand Data (Sabre/MIDT)")
            st.markdown(f"**Home Connecting** (e.g., {origin or 'LON'}{destination or 'SJC'}XXX.xlsx)")
            home_cnx_uploads = st.file_uploader(
                "Home connecting", type=['xlsx', 'xlsm', 'xls'],
                key='home_cnx', label_visibility="collapsed",
                accept_multiple_files=True,
                help="Sabre extract: connecting traffic beyond home hub")
            if home_cnx_uploads:
                st.caption(f"{len(home_cnx_uploads)} file(s): {', '.join(f.name for f in home_cnx_uploads)}")

            st.markdown(f"**Dest Connecting** (e.g., {destination or 'SJC'}{origin or 'LON'}XXX.xlsx)")
            dest_cnx_uploads = st.file_uploader(
                "Dest connecting", type=['xlsx', 'xlsm', 'xls'],
                key='dest_cnx', label_visibility="collapsed",
                accept_multiple_files=True,
                help="Sabre extract: connecting traffic beyond destination")
            if dest_cnx_uploads:
                st.caption(f"{len(dest_cnx_uploads)} file(s): {', '.join(f.name for f in dest_cnx_uploads)}")

            st.markdown("**P2P Demand** (optional  for auto-detect from MIDT)")
            p2p_uploads = st.file_uploader(
                "P2P MIDT", type=['xlsx', 'xlsm', 'xls'],
                key='p2p_midt', label_visibility="collapsed",
                accept_multiple_files=True)

        # City lookup file (optional)
        st.markdown("**City Lookup File** (optional  OAG airport/city mapping)")
        city_lookup_upload = st.file_uploader(
            "City lookup", type=['xlsx', 'xlsm', 'xls'],
            key='city_lookup', label_visibility="collapsed")

    st.markdown("---")

    # ================================================================
    # P2P SEGMENTS  both paths need these
    # ================================================================
    st.markdown("### P2P Demand Segments")
    if st.session_state.data_source == 'precomputed':
        st.caption("Configure point-to-point demand. Connecting city data is read from the forecast file.")
    else:
        st.caption("Configure point-to-point demand segments. Connecting city demand comes from the MIDT files above.")

    # Initialize with BA LHR-SJC defaults if empty
    if not st.session_state.p2p_segments:
        st.session_state.p2p_segments = [
            {'name': 'UK Business', 'base_demand': 71441.55, 'growth': 0.10,
             'stimulation': 1.15, 'capture_rate': 0.40, 'subsegments': []},
            {'name': 'UK Leisure/VFR', 'base_demand': 0, 'growth': 0.10,
             'stimulation': 1.0, 'capture_rate': 0.0, 'subsegments': [
                 {'name': 'Primary', 'base_demand': 36385.76, 'growth': 0.10,
                  'stimulation': 1.0, 'capture_rate': 0.25},
                 {'name': 'Secondary', 'base_demand': 17448.74, 'growth': 0.10,
                  'stimulation': 1.0, 'capture_rate': 0.25},
                 {'name': 'Contested', 'base_demand': 4617.68, 'growth': 0.10,
                  'stimulation': 1.0, 'capture_rate': 0.10},
             ]},
            {'name': 'US Business', 'base_demand': 65946.05, 'growth': 0.10,
             'stimulation': 1.15, 'capture_rate': 0.15, 'subsegments': []},
            {'name': 'US Leisure/VFR', 'base_demand': 0, 'growth': 0.10,
             'stimulation': 1.0, 'capture_rate': 0.0, 'subsegments': [
                 {'name': 'Primary', 'base_demand': 33586.86, 'growth': 0.10,
                  'stimulation': 1.0, 'capture_rate': 0.25},
                 {'name': 'Secondary', 'base_demand': 16106.53, 'growth': 0.10,
                  'stimulation': 1.0, 'capture_rate': 0.25},
                 {'name': 'Contested', 'base_demand': 4262.47, 'growth': 0.10,
                  'stimulation': 1.0, 'capture_rate': 0.10},
             ]},
        ]

    for i, seg in enumerate(st.session_state.p2p_segments):
        with st.expander(f"Segment {i+1}: {seg['name']}", expanded=False):
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                seg['name'] = st.text_input("Name", value=seg['name'], key=f"sn_{i}")
            with c2:
                seg['base_demand'] = st.number_input("Base Demand", value=float(seg['base_demand']),
                                                     step=1000.0, key=f"sd_{i}", format="%.2f")
            with c3:
                seg['growth'] = st.number_input("Growth", value=float(seg['growth']),
                                                step=0.01, key=f"sg_{i}", format="%.2f")
            with c4:
                seg['stimulation'] = st.number_input("Stimulation", value=float(seg['stimulation']),
                                                     step=0.05, key=f"ss_{i}", format="%.2f")
            with c5:
                seg['capture_rate'] = st.number_input("Capture Rate", value=float(seg['capture_rate']),
                                                      step=0.05, key=f"sc_{i}", format="%.2f")
            if seg['subsegments']:
                st.markdown("**Subsegments:**")
                for j, sub in enumerate(seg['subsegments']):
                    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
                    with sc1:
                        sub['name'] = st.text_input("Name", value=sub['name'], key=f"bn_{i}_{j}")
                    with sc2:
                        sub['base_demand'] = st.number_input("Base Demand", value=float(sub['base_demand']),
                                                             step=1000.0, key=f"bd_{i}_{j}", format="%.2f")
                    with sc3:
                        sub['growth'] = st.number_input("Growth", value=float(sub['growth']),
                                                        step=0.01, key=f"bg_{i}_{j}", format="%.2f")
                    with sc4:
                        sub['stimulation'] = st.number_input("Stimulation", value=float(sub['stimulation']),
                                                             step=0.05, key=f"bs_{i}_{j}", format="%.2f")
                    with sc5:
                        sub['capture_rate'] = st.number_input("Capture Rate", value=float(sub['capture_rate']),
                                                              step=0.05, key=f"bc_{i}_{j}", format="%.2f")

    btn1, btn2, _ = st.columns([1, 1, 4])
    with btn1:
        if st.button(" Add Segment"):
            st.session_state.p2p_segments.append({
                'name': f'Segment {len(st.session_state.p2p_segments)+1}',
                'base_demand': 0, 'growth': 0.05, 'stimulation': 1.0,
                'capture_rate': 0.10, 'subsegments': []
            })
            st.rerun()
    with btn2:
        if len(st.session_state.p2p_segments) > 1 and st.button(" Remove Last"):
            st.session_state.p2p_segments.pop()
            st.rerun()

    st.markdown("---")

    # ================================================================
    # READINESS CHECKS
    # ================================================================
    ready = True
    issues = []
    if not origin or len(origin) != 3:
        issues.append(" Origin airport required"); ready = False
    if not destination or len(destination) != 3:
        issues.append(" Destination airport required"); ready = False

    if st.session_state.data_source == 'precomputed':
        if not home_qsi_upload:
            issues.append(" Home Hub QSI file required"); ready = False
        if not dest_qsi_upload:
            issues.append(" Destination QSI file required"); ready = False
        if not forecast_upload:
            issues.append(" Forecast/Demand file required"); ready = False
    else:
        if not qsi_template_upload:
            issues.append(" QSI Template file required (with Leg sheets)"); ready = False
        if not home_cnx_uploads and not dest_cnx_uploads:
            issues.append(" No MIDT connecting demand files  connecting traffic will be zero")

    for iss in issues:
        st.warning(iss)

    # ================================================================
    # RUN PIPELINE
    # ================================================================
    if st.button(" Run Pipeline", type="primary", disabled=not ready, use_container_width=True):
        with st.spinner("Running QSI pipeline  scoring itineraries across all hubs..."):
            try:
                log = []
                log.append(f"[{datetime.now():%H:%M:%S}] Pipeline started")
                log.append(f"  Route: {carrier_code} {origin}-{destination}")
                log.append(f"  Aircraft: {aircraft_type} ({seats}s), {frequency}x/wk")
                log.append(f"  Data source: {st.session_state.data_source}")

                # Build P2P config (shared by both paths)
                p2p_config = {'segments': []}
                for seg in st.session_state.p2p_segments:
                    seg_dict = {
                        'name': seg['name'], 'base_demand': seg['base_demand'],
                        'growth_rate': seg['growth'], 'seasonality': 1.0,
                        'stimulation': seg['stimulation'], 'capture_rate': seg['capture_rate'],
                    }
                    if seg['subsegments']:
                        seg_dict['subsegments'] = [{
                            'name': s['name'], 'base_demand': s['base_demand'],
                            'growth_rate': s['growth'], 'seasonality': 1.0,
                            'stimulation': s['stimulation'], 'capture_rate': s['capture_rate'],
                        } for s in seg['subsegments']]
                    p2p_config['segments'].append(seg_dict)

                # Build RouteConfig
                cfg = RouteConfig()
                cfg.airline_name = carrier_name or carrier_code
                cfg.airline_code = carrier_code
                cfg.home_airport_code = origin
                cfg.dest_airport_code = destination
                o_info = lookup_airport(origin)
                d_info = lookup_airport(destination)
                cfg.home_city_code = o_info[0] if o_info else origin
                cfg.dest_city_code = d_info[0] if d_info else destination
                cfg.frequency = frequency
                cfg.aircraft_type = aircraft_type
                cfg.seats = seats
                cfg.qsi_ceiling = qsi_ceiling
                cfg.qsi_adjustment = 1.0
                cfg.online_coeff = online_coeff
                cfg.alliance_coeff = alliance_coeff
                cfg.interline_coeff = interline_coeff
                cfg.et_decay_factor = 0.8
                cfg.et_decay_interval = 0.1

                # ==== PATH A: Pre-computed ====
                if st.session_state.data_source == 'precomputed':
                    home_qsi_path = save_uploaded(home_qsi_upload)
                    dest_qsi_path = save_uploaded(dest_qsi_upload)
                    forecast_path = save_uploaded(forecast_upload)
                    log.append(f"  Files: {home_qsi_upload.name}, {dest_qsi_upload.name}, {forecast_upload.name}")

                    cfg.schedule_provider = ExcelScheduleProvider(
                        qsi1_file=home_qsi_path, qsi2_file=dest_qsi_path,
                    )
                    cfg.demand_provider = ExcelDemandProvider(
                        forecast_file=forecast_path, p2p_config=p2p_config,
                        home_growth=home_growth, dest_growth=dest_growth,
                    )

                # ==== PATH B: New Route ====
                else:
                    qsi_template_path = save_uploaded(qsi_template_upload)
                    log.append(f"  QSI Template: {qsi_template_upload.name}")

                    # MCT files
                    mct_file_map = {}
                    if mct_uploads:
                        for mf in mct_uploads:
                            mct_path = save_uploaded(mf)
                            # Try to extract airport code from filename
                            name_upper = mf.name.upper()
                            for apt_code in KNOWN_AIRPORTS:
                                if apt_code in name_upper:
                                    mct_file_map[apt_code] = mct_path
                                    break
                            else:
                                # Use generic key
                                mct_file_map[mf.name] = mct_path
                        log.append(f"  MCT files: {list(mct_file_map.keys())}")

                    # City lookup
                    city_lookup_path = None
                    if city_lookup_upload:
                        city_lookup_path = save_uploaded(city_lookup_upload)

                    # Build SingleExtractOAGProvider
                    cfg.schedule_provider = SingleExtractOAGProvider(
                        qsi_file=qsi_template_path,
                        origin_airport=origin,
                        dest_airport=destination,
                        proposed_carrier=carrier_code or 'XX',
                        use_city_codes=True,
                        city_lookup_file=city_lookup_path,
                        mct_files=mct_file_map,
                    )
                    log.append(f"  Schedule: SingleExtractOAGProvider")

                    # Save MIDT files
                    home_cnx_paths = save_multiple_uploads(home_cnx_uploads) if home_cnx_uploads else []
                    dest_cnx_paths = save_multiple_uploads(dest_cnx_uploads) if dest_cnx_uploads else []
                    p2p_paths = save_multiple_uploads(p2p_uploads) if p2p_uploads else []

                    if home_cnx_paths or dest_cnx_paths:
                        log.append(f"  MIDT home: {len(home_cnx_paths)} files, dest: {len(dest_cnx_paths)} files")

                    # Build MIDTDemandProvider
                    cfg.demand_provider = MIDTDemandProvider(
                        home_cnx_files=home_cnx_paths,
                        dest_cnx_files=dest_cnx_paths,
                        p2p_files=p2p_paths,
                        p2p_config=p2p_config,
                        home_growth=home_growth,
                        dest_growth=dest_growth,
                        catchment_share_home=catchment_share_home,
                        catchment_share_dest=catchment_share_dest,
                        city_lookup_file=city_lookup_path,
                        min_demand_threshold=min_demand_threshold,
                    )
                    log.append(f"  Demand: MIDTDemandProvider")

                # Common config
                cfg.target_total = 0
                cfg.target_p2p = 0
                cfg.target_cnx_home = 0
                cfg.target_cnx_dest = 0
                cfg.target_load_factor = 0.0

                log.append(f"[{datetime.now():%H:%M:%S}] Config: {cfg.summary()}")
                st.session_state.last_config_summary = cfg.summary()

                # Capture stdout
                old_stdout = sys.stdout
                sys.stdout = captured = io.StringIO()
                try:
                    output_path = tempfile.mktemp(suffix='.xlsx')
                    results = run_pipeline(cfg, output_path)
                    with open(output_path, 'rb') as f:
                        st.session_state.output_bytes = f.read()
                finally:
                    sys.stdout = old_stdout
                    for line in captured.getvalue().strip().split('\n'):
                        if line.strip():
                            log.append(f"  {line}")

                log.append(f"[{datetime.now():%H:%M:%S}] Complete: {results['grand_total']:,} pax, "
                           f"{results['load_factor']:.1%} LF")

                # Log provider metadata
                if hasattr(cfg.schedule_provider, 'get_metadata'):
                    meta = cfg.schedule_provider.get_metadata()
                    ptype = meta.get('provider_type', 'unknown')
                    if ptype == 'SingleExtractOAGProvider':
                        stats = meta.get('stats', {})
                        log.append(f"  Schedule stats: {stats.get('qsi1_itineraries', '?')} QSI1 + "
                                   f"{stats.get('qsi2_itineraries', '?')} QSI2 itineraries, "
                                   f"{stats.get('qsi1_hubs', '?')} hubs detected")

                if hasattr(cfg.demand_provider, 'get_metadata'):
                    meta = cfg.demand_provider.get_metadata()
                    ptype = meta.get('provider_type', 'unknown')
                    if ptype == 'MIDTDemandProvider':
                        stats = meta.get('stats', {})
                        log.append(f"  MIDT stats: home={stats.get('home_raw_records', 0)} records / "
                                   f"{stats.get('home_final_cities', 0)} cities, "
                                   f"dest={stats.get('dest_raw_records', 0)} records / "
                                   f"{stats.get('dest_final_cities', 0)} cities")

                st.session_state.results = results
                st.session_state.run_log = log
                st.success(f" Pipeline complete  **{results['grand_total']:,} passengers**, "
                           f"**{results['load_factor']:.1%}** load factor")

            except Exception as e:
                log.append(f"[{datetime.now():%H:%M:%S}] ERROR: {str(e)}")
                st.session_state.run_log = log
                st.error(f"Pipeline failed: {str(e)}")
                with st.expander("Full traceback"):
                    st.code(traceback.format_exc())

    if st.session_state.run_log:
        with st.expander(" Pipeline Log", expanded=False):
            st.code('\n'.join(st.session_state.run_log), language='text')


# ============================================================================
# TAB 2: RESULTS
# ============================================================================

with tab2:
    results = st.session_state.results
    if results is None:
        st.info("Run the pipeline from the 'Data Upload & Run' tab to see results here.")
    else:
        path_badge = ("precomputed" if st.session_state.data_source == 'precomputed'
                       else "newroute")
        path_label = ("PRE-COMPUTED" if st.session_state.data_source == 'precomputed'
                       else "NEW ROUTE")
        st.markdown(f'### Results: {st.session_state.last_config_summary} '
                    f'<span class="provider-badge {path_badge}">{path_label}</span>',
                    unsafe_allow_html=True)

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(metric_card("Grand Total", fmt(results['grand_total']), "Annual pax"),
                        unsafe_allow_html=True)
        with m2:
            st.markdown(metric_card("Load Factor", f"{results['load_factor']:.1%}"),
                        unsafe_allow_html=True)
        with m3:
            pct = f"{results['p2p_total']/results['grand_total']:.0%}" if results['grand_total'] else ""
            st.markdown(metric_card("P2P", fmt(results['p2p_total']), pct),
                        unsafe_allow_html=True)
        with m4:
            pct = f"{results['home_total']/results['grand_total']:.0%}" if results['grand_total'] else ""
            st.markdown(metric_card("Cnx Home", fmt(results['home_total']), pct),
                        unsafe_allow_html=True)
        with m5:
            pct = f"{results['dest_total']/results['grand_total']:.0%}" if results['grand_total'] else ""
            st.markdown(metric_card("Cnx Dest", fmt(results['dest_total']), pct),
                        unsafe_allow_html=True)

        st.markdown("---")

        # PTEW
        denom = frequency * 52 * 2 if frequency > 0 else 1
        ptew = results['grand_total'] / denom
        pt1, pt2, pt3 = st.columns(3)
        with pt1:
            st.markdown(metric_card("PTEW Total", f"{ptew:.1f}", "Pax per trip each way"),
                        unsafe_allow_html=True)
        with pt2:
            st.markdown(metric_card("PTEW P2P", f"{results['p2p_total']/denom:.1f}"),
                        unsafe_allow_html=True)
        with pt3:
            cnx = results['home_total'] + results['dest_total']
            st.markdown(metric_card("PTEW Connecting", f"{cnx/denom:.1f}"),
                        unsafe_allow_html=True)

        st.markdown("---")

        # P2P detail
        st.markdown("#### P2P Breakdown")
        if 'p2p_detail' in results:
            rows = []
            for seg in results['p2p_detail']:
                rows.append({
                    'Segment': seg.get('name', ''),
                    'Base Demand': f"{seg.get('base_demand', 0):,.0f}",
                    'Growth': f"{seg.get('growth', 0):.0%}",
                    'Stimulation': f"{seg.get('stimulation', 1.0):.2f}",
                    'Capture': f"{seg.get('capture_rate', 0):.0%}",
                    'Forecast': f"{seg.get('forecast', 0):,.0f}",
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)

        # Connecting cities
        for label, key in [("Top Connecting  Home Hub", 'home_results'),
                           ("Top Connecting  Destination", 'dest_results')]:
            st.markdown(f"#### {label}")
            if key in results and results[key]:
                data = sorted(results[key], key=lambda x: -x.get('forecast', 0))[:25]
                rows = [{
                    'City': r.get('city', ''), 'Name': r.get('name', ''),
                    'Base Demand': f"{r.get('base_demand', 0):,.0f}",
                    'QSI Capture': f"{r.get('qsi_capture', 0):.4f}" if r.get('qsi_capture') else "",
                    'Expert QSI': f"{r.get('original_qsi', 0):.4f}" if r.get('original_qsi') else "",
                    'Cal Factor': f"{r.get('calibration_factor', 0):.3f}" if r.get('calibration_factor') else "",
                    'Forecast': f"{r.get('forecast', 0):,.0f}",
                } for r in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.caption("No data available.")

        st.markdown("---")
        if st.session_state.output_bytes:
            fn = f"QSI_Forecast_{origin}_{destination}_{carrier_code}_{datetime.now():%Y%m%d}.xlsx"
            st.download_button(" Download Output Workbook", data=st.session_state.output_bytes,
                               file_name=fn, type="primary", use_container_width=True,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ============================================================================
# TAB 3: COMPARISON
# ============================================================================

with tab3:
    st.markdown("###  Analyst Comparison")
    st.markdown("Enter the result your analyst team produced. **Target: within 5% = trusted tool.**")

    results = st.session_state.results
    if results is None:
        st.info("Run the pipeline first, then enter analyst results here.")
    else:
        st.markdown(f"**Pipeline:** {results['grand_total']:,} pax, {results['load_factor']:.1%} LF")
        st.markdown("---")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Analyst Results:**")
            at = st.number_input("Total Passengers", min_value=0, value=0, step=1000, key="at")
            ap = st.number_input("P2P Passengers", min_value=0, value=0, step=1000, key="ap")
            ah = st.number_input("Cnx Home", min_value=0, value=0, step=1000, key="ah")
            ad = st.number_input("Cnx Dest", min_value=0, value=0, step=100, key="ad")
            al = st.number_input("Load Factor (%)", min_value=0.0, max_value=100.0,
                                 value=0.0, step=0.1, key="al")

        with c2:
            st.markdown("**Variance:**")
            if at > 0:
                vt = (results['grand_total'] - at) / at
                within_5 = abs(vt) <= 0.05

                if within_5:
                    st.markdown('<span class="verdict-pass"> WITHIN 5%  TOOL TRUSTED</span>',
                                unsafe_allow_html=True)
                elif abs(vt) <= 0.10:
                    st.markdown('<span class="verdict-marginal"> WITHIN 10%  REVIEW CALIBRATION</span>',
                                unsafe_allow_html=True)
                else:
                    st.markdown('<span class="verdict-fail"> EXCEEDS 10%  INVESTIGATE</span>',
                                unsafe_allow_html=True)

                st.markdown("---")

                comparisons = [
                    ("Grand Total", results['grand_total'], at, vt),
                    ("P2P", results['p2p_total'], ap,
                     (results['p2p_total'] - ap) / ap if ap > 0 else None),
                    ("Cnx Home", results['home_total'], ah,
                     (results['home_total'] - ah) / ah if ah > 0 else None),
                    ("Cnx Dest", results['dest_total'], ad,
                     (results['dest_total'] - ad) / ad if ad > 0 else None),
                ]

                for label, pv, av, var in comparisons:
                    if var is not None:
                        color = ("#155724" if abs(var) <= 0.05
                                 else ("#856404" if abs(var) <= 0.10 else "#721c24"))
                        icon = "" if abs(var) <= 0.05 else ("" if abs(var) <= 0.10 else "")
                        diff = pv - av
                        st.markdown(
                            f"""**{label}** &nbsp; Pipeline: {pv:,} &nbsp;|&nbsp; Analyst: {av:,}
                            &nbsp;|&nbsp; <span style="color:{color};font-weight:700">{icon} {var:+.1%} ({diff:+,})</span>""",
                            unsafe_allow_html=True)

                if al > 0:
                    lf_diff = results['load_factor'] * 100 - al
                    st.markdown(
                        f"""**Load Factor** &nbsp; Pipeline: {results['load_factor']:.1%}
                        &nbsp;|&nbsp; Analyst: {al:.1f}% &nbsp;|&nbsp;  {lf_diff:+.1f} pp""",
                        unsafe_allow_html=True)

                st.markdown("---")
                if within_5:
                    st.success("Pipeline and analyst results are well-aligned. Calibration is sound.")
                else:
                    st.warning(f"""
                    **Total variance: {vt:+.1%}**

                    Review: P2P capture rates & stimulation, connecting city QSI calibration factors,
                    and base demand inputs. The tiered default calibration may diverge from expert values
                    for specific city pairs.
                    """)
            else:
                st.caption("Enter analyst total passengers to see comparison.")


# ============================================================================


# ============================================================================
# TAB 4: TIME GRID (New Route path only) -- LIVE PIPELINE RUNS (Chat 28)
# ============================================================================

if tab4 is not None:
    with tab4:
        st.markdown("### \u23f0 Departure Time Grid Search")
        st.caption("Run the full QSI pipeline at multiple departure times to identify "
                    "the optimal schedule. Each scenario shifts the proposed service timing, "
                    "rebuilds hub connections, and re-runs the complete engine.")

        if st.session_state.data_source != 'newroute':
            st.info("Time grid analysis is available in New Route Assessment mode. "
                     "Switch to 'New Route Assessment' in the sidebar.")
        elif not st.session_state.results:
            st.info("\u261d Run the pipeline once from the Data Upload tab to establish "
                     "the base case before running time grid analysis.")
        else:
            st.markdown("#### \U0001f4cb Grid Configuration")

            # Grid definition controls
            col_g1, col_g2, col_g3 = st.columns(3)
            with col_g1:
                grid_start = st.time_input("Grid start (dep from origin)",
                                           value=dtime(14, 0), key='grid_start')
                grid_end = st.time_input("Grid end (dep from origin)",
                                         value=dtime(23, 0), key='grid_end')
            with col_g2:
                grid_step = st.selectbox("Step interval", [30, 60, 90, 120], index=1,
                                         format_func=lambda x: f"{x} minutes",
                                         key='grid_step')
                n_scenarios = st.number_input("Max scenarios", min_value=2, max_value=12,
                                              value=6, key='grid_max')
            with col_g3:
                ft_out = st.number_input("Block time outbound (min)",
                                         min_value=60, max_value=1200, value=625,
                                         step=5, key='ft_out',
                                         help="Flying time origin to destination in minutes")
                ft_ret = st.number_input("Block time return (min)",
                                         min_value=60, max_value=1200, value=660,
                                         step=5, key='ft_ret',
                                         help="Flying time destination to origin in minutes")

            # Calculate preview of scenarios
            import datetime as dt_module
            scenarios_preview = []
            current = dt_module.datetime.combine(dt_module.date.today(), grid_start)
            end_dt = dt_module.datetime.combine(dt_module.date.today(), grid_end)
            while current <= end_dt and len(scenarios_preview) < n_scenarios:
                dep_hhmm = current.strftime("%H%M")
                dep_mins = int(dep_hhmm[:2]) * 60 + int(dep_hhmm[2:])
                arr_mins = (dep_mins + ft_out) % 1440
                arr_h, arr_m = divmod(arr_mins, 60)
                scenarios_preview.append({
                    'dep': current.strftime("%H:%M"),
                    'dep_hhmm': dep_hhmm,
                    'arr': f"{arr_h:02d}:{arr_m:02d}",
                })
                current += dt_module.timedelta(minutes=grid_step)

            if scenarios_preview:
                times_str = ', '.join(f"{s['dep']}\u2192{s['arr']}" for s in scenarios_preview)
                st.markdown(f"**{len(scenarios_preview)} scenarios:** {times_str}")
                est_secs = len(scenarios_preview) * 45
                st.caption(f"Estimated runtime: {est_secs // 60}m {est_secs % 60}s "
                           f"({len(scenarios_preview)} \u00d7 ~45s per scenario)")

            st.markdown("---")

            # Dest QSI file for bidirectional grid (optional)
            st.markdown("**Destination QSI Template** (optional, for bidirectional analysis)")
            dest_qsi_grid_upload = st.file_uploader(
                "Dest QSI for grid", type=['xlsx', 'xlsm', 'xls'],
                key='dest_qsi_grid', label_visibility="collapsed",
                help="If provided, each scenario also shifts connections at the destination hub. "
                     "Use the dest-perspective QSI template file.")

            st.markdown("---")

            # RUN GRID BUTTON
            can_run = (len(scenarios_preview) >= 2 and
                       st.session_state.results is not None)

            if st.button("\U0001f50d Run Time Grid Search", type="primary",
                        disabled=not can_run, use_container_width=True):

                grid_progress = st.progress(0)
                grid_status = st.empty()
                grid_log_area = st.empty()
                grid_log_lines = []

                def grid_callback(idx, total, dep_time, status):
                    pct = (idx + (1 if status in ('done', 'error') else 0)) / total
                    grid_progress.progress(min(pct, 1.0))
                    icon = "\u2705" if status == 'done' else ("\u274c" if status == 'error' else "\u23f3")
                    msg = f"{icon} Scenario {idx+1}/{total}: {dep_time} dep -- {status}"
                    grid_log_lines.append(msg)
                    grid_status.text(msg)

                try:
                    grid_status.text("Preparing time grid search...")

                    # We need to recreate the provider from the uploaded files
                    # (session state has the file paths from the original run)
                    # But the simpler approach: we check if the config was stored

                    # Recreate SingleExtractOAGProvider from uploaded template
                    qsi_template_path_grid = save_uploaded(qsi_template_upload)

                    mct_file_map_grid = {}
                    if mct_uploads:
                        for mf in mct_uploads:
                            mct_path = save_uploaded(mf)
                            name_upper = mf.name.upper()
                            for apt_code in KNOWN_AIRPORTS:
                                if apt_code in name_upper:
                                    mct_file_map_grid[apt_code] = mct_path
                                    break
                            else:
                                mct_file_map_grid[mf.name] = mct_path

                    city_lookup_path_grid = None
                    if city_lookup_upload:
                        city_lookup_path_grid = save_uploaded(city_lookup_upload)

                    base_provider = SingleExtractOAGProvider(
                        qsi_file=qsi_template_path_grid,
                        origin_airport=origin,
                        dest_airport=destination,
                        proposed_carrier=carrier_code or 'XX',
                        use_city_codes=True,
                        city_lookup_file=city_lookup_path_grid,
                        mct_files=mct_file_map_grid,
                    )

                    # Dest provider (optional)
                    dest_base_provider = None
                    dest_qsi_grid_path = None
                    if dest_qsi_grid_upload:
                        dest_qsi_grid_path = save_uploaded(dest_qsi_grid_upload)
                        dest_base_provider = SingleExtractOAGProvider(
                            qsi_file=dest_qsi_grid_path,
                            origin_airport=destination,
                            dest_airport=origin,
                            proposed_carrier=carrier_code or 'XX',
                            use_city_codes=True,
                            city_lookup_file=city_lookup_path_grid,
                            mct_files=mct_file_map_grid,
                        )

                    # Build RouteConfig for grid
                    grid_cfg = RouteConfig()
                    grid_cfg.airline_name = carrier_name or carrier_code
                    grid_cfg.airline_code = carrier_code
                    grid_cfg.home_airport_code = origin
                    grid_cfg.dest_airport_code = destination
                    o_info = lookup_airport(origin)
                    d_info = lookup_airport(destination)
                    grid_cfg.home_city_code = o_info[0] if o_info else origin
                    grid_cfg.dest_city_code = d_info[0] if d_info else destination
                    grid_cfg.frequency = frequency
                    grid_cfg.aircraft_type = aircraft_type
                    grid_cfg.seats = seats
                    grid_cfg.qsi_ceiling = qsi_ceiling
                    grid_cfg.qsi_adjustment = 1.0
                    grid_cfg.online_coeff = online_coeff
                    grid_cfg.alliance_coeff = alliance_coeff
                    grid_cfg.interline_coeff = interline_coeff
                    grid_cfg.et_decay_factor = 0.8
                    grid_cfg.et_decay_interval = 0.1
                    grid_cfg.target_total = 0
                    grid_cfg.target_p2p = 0
                    grid_cfg.target_cnx_home = 0
                    grid_cfg.target_cnx_dest = 0
                    grid_cfg.target_load_factor = 0.0

                    # Build demand provider (same as main run)
                    p2p_config_grid = {'segments': []}
                    for seg in st.session_state.p2p_segments:
                        seg_dict = {
                            'name': seg['name'], 'base_demand': seg['base_demand'],
                            'growth_rate': seg['growth'], 'seasonality': 1.0,
                            'stimulation': seg['stimulation'], 'capture_rate': seg['capture_rate'],
                        }
                        if seg['subsegments']:
                            seg_dict['subsegments'] = [{
                                'name': s['name'], 'base_demand': s['base_demand'],
                                'growth_rate': s['growth'], 'seasonality': 1.0,
                                'stimulation': s['stimulation'], 'capture_rate': s['capture_rate'],
                            } for s in seg['subsegments']]
                        p2p_config_grid['segments'].append(seg_dict)

                    # Re-save MIDT files
                    home_cnx_paths_g = save_multiple_uploads(home_cnx_uploads) if home_cnx_uploads else []
                    dest_cnx_paths_g = save_multiple_uploads(dest_cnx_uploads) if dest_cnx_uploads else []
                    p2p_paths_g = save_multiple_uploads(p2p_uploads) if p2p_uploads else []

                    grid_cfg.demand_provider = MIDTDemandProvider(
                        home_cnx_files=home_cnx_paths_g,
                        dest_cnx_files=dest_cnx_paths_g,
                        p2p_files=p2p_paths_g,
                        p2p_config=p2p_config_grid,
                        home_growth=home_growth,
                        dest_growth=dest_growth,
                        catchment_share_home=catchment_share_home,
                        catchment_share_dest=catchment_share_dest,
                        city_lookup_file=city_lookup_path_grid,
                        min_demand_threshold=min_demand_threshold,
                    )

                    grid_cfg.schedule_provider = base_provider

                    # Create TimeGridRunner
                    runner = TimeGridRunner(
                        base_config=grid_cfg,
                        base_provider=base_provider,
                        origin=origin,
                        destination=destination,
                        carrier=carrier_code or 'XX',
                        flying_time_outbound=ft_out,
                        flying_time_return=ft_ret,
                        dest_base_provider=dest_base_provider,
                        callback=grid_callback,
                    )

                    # Generate scenarios
                    start_str = grid_start.strftime("%H:%M")
                    end_str = grid_end.strftime("%H:%M")
                    grid_scenarios = runner.generate_grid(
                        start=start_str,
                        end=end_str,
                        step_minutes=grid_step,
                        max_scenarios=n_scenarios,
                    )

                    grid_status.text(f"Running {len(grid_scenarios)} scenarios...")

                    # Capture stdout
                    old_stdout = sys.stdout
                    sys.stdout = io.StringIO()
                    try:
                        grid_result = runner.run(grid_scenarios)
                    finally:
                        sys.stdout = old_stdout

                    grid_progress.progress(1.0)
                    grid_status.text(f"Grid search complete: {len(grid_result.scenarios)} scenarios "
                                     f"in {grid_result.total_elapsed:.0f}s")

                    # Write Excel output
                    import tempfile as tf_mod
                    grid_xlsx_path = tf_mod.mktemp(suffix='.xlsx')
                    write_grid_output(grid_result, grid_xlsx_path)
                    with open(grid_xlsx_path, 'rb') as gf:
                        st.session_state.grid_output_bytes = gf.read()

                    st.session_state.grid_search_result = grid_result
                    st.session_state.grid_results = [
                        {
                            'dep_time': s.dep_time_origin,
                            'arr_hub': s.arr_time_hub,
                            'dep_hub': s.dep_time_hub,
                            'arr_origin': s.arr_time_origin,
                            'grand_total': s.grand_total,
                            'p2p': round(s.p2p_total),
                            'cnx_home': round(s.cnx_home_total),
                            'cnx_dest': round(s.cnx_dest_total),
                            'load_factor': s.load_factor,
                            'n_cities_home': s.n_cities_home,
                            'n_cities_dest': s.n_cities_dest,
                            'itineraries_qsi1': s.itineraries_qsi1,
                            'itineraries_qsi2': s.itineraries_qsi2,
                            'elapsed': s.elapsed_seconds,
                            'error': s.error,
                        }
                        for s in grid_result.scenarios
                    ]

                    if grid_result.best_scenario:
                        best = grid_result.best_scenario
                        st.success(
                            f"\u2705 **Optimal: {best.dep_time_origin} departure** "
                            f"\u2192 {best.grand_total:,} pax, {best.load_factor:.1%} LF"
                        )

                except Exception as e:
                    grid_progress.progress(1.0)
                    grid_status.text(f"Grid search failed: {str(e)}")
                    st.error(f"Time grid search failed: {str(e)}")
                    with st.expander("Full traceback"):
                        st.code(traceback.format_exc())

                # Show log
                if grid_log_lines:
                    with st.expander("Grid Search Log", expanded=False):
                        st.code('\n'.join(grid_log_lines), language='text')

            # ============================================================
            # DISPLAY GRID RESULTS
            # ============================================================
            grid_result_obj = st.session_state.grid_search_result
            grid_data = st.session_state.grid_results

            if grid_result_obj and grid_data:
                st.markdown("---")
                st.markdown("#### \U0001f3c6 Grid Search Results")

                # Summary metrics
                best = grid_result_obj.best_scenario
                if best and len(grid_result_obj.ranked) >= 2:
                    worst = grid_result_obj.ranked[-1]
                    delta = best.grand_total - worst.grand_total
                    pct_range = (delta / worst.grand_total * 100) if worst.grand_total else 0

                    gm1, gm2, gm3, gm4 = st.columns(4)
                    with gm1:
                        st.markdown(metric_card("Best Time",
                                    best.dep_time_origin, f"dep {origin}"),
                                    unsafe_allow_html=True)
                    with gm2:
                        st.markdown(metric_card("Best Total",
                                    f"{best.grand_total:,}", f"{best.load_factor:.1%} LF"),
                                    unsafe_allow_html=True)
                    with gm3:
                        st.markdown(metric_card("Worst Total",
                                    f"{worst.grand_total:,}", worst.dep_time_origin),
                                    unsafe_allow_html=True)
                    with gm4:
                        st.markdown(metric_card("Range",
                                    f"{delta:+,}", f"{pct_range:+.1f}%"),
                                    unsafe_allow_html=True)

                # Ranked table
                st.markdown("##### Scenario Ranking")
                rows = []
                for rank, gr in enumerate(sorted(grid_data,
                                                  key=lambda x: -(x.get('grand_total', 0)
                                                                    if not x.get('error') else 0)),
                                           1):
                    if gr.get('error'):
                        rows.append({
                            'Rank': rank,
                            f'Dep {origin}': gr.get('dep_time', ''),
                            f'Arr {destination}': gr.get('arr_hub', ''),
                            f'Dep {destination}': gr.get('dep_hub', ''),
                            f'Arr {origin}': gr.get('arr_origin', ''),
                            'Grand Total': 'ERROR',
                            'LF': '',
                            'P2P': '',
                            'Cnx Home': '',
                            'Cnx Dest': '',
                            'Time (s)': f"{gr.get('elapsed', 0):.0f}",
                        })
                    else:
                        best_total = best.grand_total if best else 0
                        delta_v = gr.get('grand_total', 0) - best_total
                        rows.append({
                            'Rank': rank,
                            f'Dep {origin}': gr.get('dep_time', ''),
                            f'Arr {destination}': gr.get('arr_hub', ''),
                            f'Dep {destination}': gr.get('dep_hub', ''),
                            f'Arr {origin}': gr.get('arr_origin', ''),
                            'Grand Total': f"{gr.get('grand_total', 0):,}",
                            'LF': f"{gr.get('load_factor', 0):.1%}",
                            'P2P': f"{gr.get('p2p', 0):,}",
                            'Cnx Home': f"{gr.get('cnx_home', 0):,}",
                            'Cnx Dest': f"{gr.get('cnx_dest', 0):,}",
                            'Time (s)': f"{gr.get('elapsed', 0):.0f}",
                        })
                st.dataframe(rows, use_container_width=True, hide_index=True)

                # BAR CHART: Grand total by departure time
                st.markdown("##### Total Passengers by Departure Time")
                chart_data = [
                    {'dep_time': gr['dep_time'], 'Grand Total': gr['grand_total']}
                    for gr in grid_data if not gr.get('error')
                ]
                if chart_data:
                    import pandas as pd
                    df_chart = pd.DataFrame(chart_data)
                    st.bar_chart(df_chart.set_index('dep_time'), y='Grand Total',
                                 color='#e8a83e', use_container_width=True)

                # STACKED BAR: P2P / Cnx Home / Cnx Dest breakdown
                st.markdown("##### Traffic Breakdown by Departure Time")
                breakdown_data = [
                    {
                        'dep_time': gr['dep_time'],
                        'P2P': gr.get('p2p', 0),
                        'Cnx Home': gr.get('cnx_home', 0),
                        'Cnx Dest': gr.get('cnx_dest', 0),
                    }
                    for gr in grid_data if not gr.get('error')
                ]
                if breakdown_data:
                    df_bd = pd.DataFrame(breakdown_data)
                    st.bar_chart(df_bd.set_index('dep_time'),
                                 color=['#0d3b66', '#e8a83e', '#8ba4c4'],
                                 use_container_width=True)

                # Itinerary counts
                st.markdown("##### Connection Window Impact")
                st.caption("Number of valid itineraries at each departure time "
                           "-- shows how the connection window shifts.")
                itin_data = [
                    {
                        'dep_time': gr['dep_time'],
                        'QSI1 Itineraries': gr.get('itineraries_qsi1', 0),
                        'QSI2 Itineraries': gr.get('itineraries_qsi2', 0),
                    }
                    for gr in grid_data if not gr.get('error')
                ]
                if itin_data:
                    df_itin = pd.DataFrame(itin_data)
                    st.bar_chart(df_itin.set_index('dep_time'),
                                 color=['#0a1628', '#336699'],
                                 use_container_width=True)

                # City sensitivity analysis
                if grid_result_obj.city_sensitivity:
                    st.markdown("##### Top City Sensitivity")
                    st.caption("Cities most affected by departure time changes "
                               "-- ordered by absolute passenger range.")
                    sens_rows = []
                    for cs in grid_result_obj.city_sensitivity[:20]:
                        row_s = {
                            'City': cs.get('city', ''),
                            'Best Time': cs.get('best_time', ''),
                            'Max Pax': f"{cs.get('max_pax', 0):,.0f}",
                            'Min Pax': f"{cs.get('min_pax', 0):,.0f}",
                            'Range': f"{cs.get('range', 0):,.0f}",
                            'Range %': f"{cs.get('range_pct', 0):.1f}%",
                        }
                        sens_rows.append(row_s)
                    st.dataframe(sens_rows, use_container_width=True, hide_index=True)

                # Download buttons
                st.markdown("---")
                dl1, dl2, _ = st.columns([1, 1, 2])
                with dl1:
                    if st.session_state.grid_output_bytes:
                        fn = (f"TimeGrid_{origin}_{destination}_{carrier_code}_"
                              f"{datetime.now():%Y%m%d}.xlsx")
                        st.download_button(
                            "\U0001f4e5 Download Grid Workbook",
                            data=st.session_state.grid_output_bytes,
                            file_name=fn, type="primary",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                with dl2:
                    if st.session_state.output_bytes:
                        fn2 = (f"QSI_Forecast_{origin}_{destination}_{carrier_code}_"
                               f"{datetime.now():%Y%m%d}.xlsx")
                        st.download_button(
                            "\U0001f4e5 Download Base Case Workbook",
                            data=st.session_state.output_bytes,
                            file_name=fn2,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#8ba4c4;font-size:0.75rem;padding:1rem;">
Avia Solutions  QSI Route Forecast Portal v4.0  Chat 28<br>
22 modules | Pre-computed + New Route Assessment paths<br>
Validated: BA LHR-SJC, KLM AMS-TPA, KE ICN-SJC, SQ SIN-SJC, CX HKG-SJC, FI KEF-SJC<br>
<br>
<em>This tool is provided for internal use by Avia Solutions Limited and its authorised clients.
Forecasts are indicative and subject to professional review. All data remains confidential.</em>
</div>
""", unsafe_allow_html=True)
