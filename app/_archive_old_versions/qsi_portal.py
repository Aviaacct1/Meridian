#!/usr/bin/env python3
"""
Avia Solutions  QSI Route Forecast Portal (Chat 22)
=====================================================
Streamlit web portal for running the QSI forecast pipeline.

Upload OAG/QSI schedule files and demand/forecast files,
configure route parameters, run the pipeline, and download
the output workbook.

Includes "Comparison Mode" to validate against analyst results.
"""

import os
import sys
import io
import tempfile
import traceback
from datetime import datetime, time as dtime
from typing import Dict, Optional, Any

import streamlit as st

#  Pipeline imports (from project modules) 
from providers import (
    ExcelScheduleProvider, ExcelDemandProvider,
    P2PSegmentData, P2PSubsegmentData, ConnectingCityData,
)
from route_config import RouteConfig
from closed_loop_pipeline_v2 import run_pipeline
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
    <p>Avia Solutions  Quality of Service Index Pipeline v2.0</p>
</div>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE
# ============================================================================

if 'results' not in st.session_state:
    st.session_state.results = None
if 'output_bytes' not in st.session_state:
    st.session_state.output_bytes = None
if 'run_log' not in st.session_state:
    st.session_state.run_log = []
if 'last_config_summary' not in st.session_state:
    st.session_state.last_config_summary = ""
if 'p2p_segments' not in st.session_state:
    st.session_state.p2p_segments = []


# ============================================================================
# HELPERS
# ============================================================================

def save_uploaded(uploaded_file) -> str:
    tmp_dir = tempfile.mkdtemp()
    path = os.path.join(tmp_dir, uploaded_file.name)
    with open(path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return path


def fmt(n, decimals=0):
    if n is None: return ""
    if isinstance(n, float) and 0 < n < 1: return f"{n:.1%}"
    if decimals > 0: return f"{n:,.{decimals}f}"
    return f"{int(n):,}"


def metric_card(label, value, sub=""):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    return f'<div class="metric-card"><div class="label">{label}</div><div class="value">{value}</div>{sub_html}</div>'


# ============================================================================
# SIDEBAR  ROUTE CONFIGURATION
# ============================================================================

with st.sidebar:
    st.markdown("###  Route Configuration")

    st.markdown('<div class="section-label">Operating Mode</div>', unsafe_allow_html=True)
    mode = st.selectbox("Mode", ["Forecast", "Business Case"])

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

    st.markdown('<div class="section-label">QSI Coefficients</div>', unsafe_allow_html=True)
    is_lcc = ct_map[carrier_type] in ('lcc', 'ultra_lcc')
    online_coeff = st.number_input("Online", min_value=0.0, max_value=2.0, value=1.0, step=0.05, format="%.3f")
    alliance_coeff = st.number_input("Alliance", min_value=0.0, max_value=2.0,
                                     value=0.0 if is_lcc else 0.615, step=0.05, format="%.3f")
    interline_coeff = st.number_input("Interline", min_value=0.0, max_value=2.0,
                                      value=0.0 if is_lcc else 0.25, step=0.05, format="%.3f")
    qsi_ceiling = st.number_input("QSI Ceiling", min_value=0.1, max_value=2.0, value=1.0, step=0.05, format="%.2f")

    st.markdown('<div class="section-label">Growth Assumptions</div>', unsafe_allow_html=True)
    home_growth = st.number_input("Home Growth", min_value=-0.10, max_value=0.30, value=0.09, step=0.01, format="%.2f")
    dest_growth = st.number_input("Dest Growth", min_value=-0.10, max_value=0.30, value=0.10, step=0.01, format="%.2f")

    if origin and destination and len(origin) == 3 and len(destination) == 3:
        dist = compute_distance(origin, destination)
        if dist:
            band = classify_distance_band(dist)
            st.info(f" {origin}{destination}: {dist:,.0f} nm ({band.replace('_', ' ')})")


# ============================================================================
# MAIN TABS
# ============================================================================

tab1, tab2, tab3 = st.tabs([" Data Upload & Run", " Results", " Comparison"])

# ============================================================================
# TAB 1: UPLOAD & RUN
# ============================================================================

with tab1:
    st.markdown("### Upload Data Files")

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

    st.markdown("---")

    #  P2P Segments 
    st.markdown("### P2P Demand Segments")
    st.caption("Configure point-to-point demand. Connecting city data is read from the forecast file.")

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

    # Readiness checks
    ready = True
    issues = []
    if not origin or len(origin) != 3:
        issues.append(" Origin airport required"); ready = False
    if not destination or len(destination) != 3:
        issues.append(" Destination airport required"); ready = False
    if not home_qsi_upload:
        issues.append(" Home Hub QSI file required"); ready = False
    if not dest_qsi_upload:
        issues.append(" Destination QSI file required"); ready = False
    if not forecast_upload:
        issues.append(" Forecast/Demand file required"); ready = False
    for iss in issues:
        st.warning(iss)

    # ================================================================
    # RUN BUTTON
    # ================================================================
    if st.button(" Run Pipeline", type="primary", disabled=not ready, use_container_width=True):
        with st.spinner("Running QSI pipeline  scoring itineraries across all hubs..."):
            try:
                home_qsi_path = save_uploaded(home_qsi_upload)
                dest_qsi_path = save_uploaded(dest_qsi_upload)
                forecast_path = save_uploaded(forecast_upload)

                log = []
                log.append(f"[{datetime.now():%H:%M:%S}] Pipeline started")
                log.append(f"  Route: {carrier_code} {origin}-{destination}")
                log.append(f"  Aircraft: {aircraft_type} ({seats}s), {frequency}x/wk")
                log.append(f"  Files: {home_qsi_upload.name}, {dest_qsi_upload.name}, {forecast_upload.name}")

                # Build P2P config
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

                cfg.schedule_provider = ExcelScheduleProvider(
                    qsi1_file=home_qsi_path, qsi2_file=dest_qsi_path,
                )
                cfg.demand_provider = ExcelDemandProvider(
                    forecast_file=forecast_path, p2p_config=p2p_config,
                    home_growth=home_growth, dest_growth=dest_growth,
                )
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

                log.append(f"[{datetime.now():%H:%M:%S}] Complete: {results['grand_total']:,} pax, {results['load_factor']:.1%} LF")
                st.session_state.results = results
                st.session_state.run_log = log
                st.success(f" Pipeline complete  **{results['grand_total']:,} passengers**, **{results['load_factor']:.1%}** load factor")

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
        st.markdown(f"### Results: {st.session_state.last_config_summary}")

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(metric_card("Grand Total", fmt(results['grand_total']), "Annual pax"), unsafe_allow_html=True)
        with m2:
            st.markdown(metric_card("Load Factor", f"{results['load_factor']:.1%}"), unsafe_allow_html=True)
        with m3:
            pct = f"{results['p2p_total']/results['grand_total']:.0%}" if results['grand_total'] else ""
            st.markdown(metric_card("P2P", fmt(results['p2p_total']), pct), unsafe_allow_html=True)
        with m4:
            pct = f"{results['home_total']/results['grand_total']:.0%}" if results['grand_total'] else ""
            st.markdown(metric_card("Cnx Home", fmt(results['home_total']), pct), unsafe_allow_html=True)
        with m5:
            pct = f"{results['dest_total']/results['grand_total']:.0%}" if results['grand_total'] else ""
            st.markdown(metric_card("Cnx Dest", fmt(results['dest_total']), pct), unsafe_allow_html=True)

        st.markdown("---")

        # PTEW
        denom = frequency * 52 * 2 if frequency > 0 else 1
        ptew = results['grand_total'] / denom
        pt1, pt2, pt3 = st.columns(3)
        with pt1:
            st.markdown(metric_card("PTEW Total", f"{ptew:.1f}", "Pax per trip each way"), unsafe_allow_html=True)
        with pt2:
            st.markdown(metric_card("PTEW P2P", f"{results['p2p_total']/denom:.1f}"), unsafe_allow_html=True)
        with pt3:
            cnx = results['home_total'] + results['dest_total']
            st.markdown(metric_card("PTEW Connecting", f"{cnx/denom:.1f}"), unsafe_allow_html=True)

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
                data = sorted(results[key], key=lambda x: -x.get('forecast', 0))[:20]
                rows = [{
                    'City': r.get('city', ''), 'Name': r.get('name', ''),
                    'Base Demand': f"{r.get('base_demand', 0):,.0f}",
                    'QSI Capture': f"{r.get('qsi_capture', 0):.4f}" if r.get('qsi_capture') else "",
                    'Expert QSI': f"{r.get('original_qsi', 0):.4f}" if r.get('original_qsi') else "",
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
            al = st.number_input("Load Factor (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key="al")

        with c2:
            st.markdown("**Variance:**")
            if at > 0:
                vt = (results['grand_total'] - at) / at
                within_5 = abs(vt) <= 0.05

                if within_5:
                    st.markdown('<span class="verdict-pass"> WITHIN 5%  TOOL TRUSTED</span>', unsafe_allow_html=True)
                elif abs(vt) <= 0.10:
                    st.markdown('<span class="verdict-marginal"> WITHIN 10%  REVIEW CALIBRATION</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="verdict-fail"> EXCEEDS 10%  INVESTIGATE</span>', unsafe_allow_html=True)

                st.markdown("---")

                comparisons = [
                    ("Grand Total", results['grand_total'], at, vt),
                    ("P2P", results['p2p_total'], ap, (results['p2p_total'] - ap) / ap if ap > 0 else None),
                    ("Cnx Home", results['home_total'], ah, (results['home_total'] - ah) / ah if ah > 0 else None),
                    ("Cnx Dest", results['dest_total'], ad, (results['dest_total'] - ad) / ad if ad > 0 else None),
                ]

                for label, pv, av, var in comparisons:
                    if var is not None:
                        color = "#155724" if abs(var) <= 0.05 else ("#856404" if abs(var) <= 0.10 else "#721c24")
                        icon = "" if abs(var) <= 0.05 else ("" if abs(var) <= 0.10 else "")
                        diff = pv - av
                        st.markdown(f"""**{label}** &nbsp; Pipeline: {pv:,} &nbsp;|&nbsp; Analyst: {av:,}
                        &nbsp;|&nbsp; <span style="color:{color};font-weight:700">{icon} {var:+.1%} ({diff:+,})</span>""",
                                    unsafe_allow_html=True)

                if al > 0:
                    lf_diff = results['load_factor'] * 100 - al
                    st.markdown(f"""**Load Factor** &nbsp; Pipeline: {results['load_factor']:.1%}
                    &nbsp;|&nbsp; Analyst: {al:.1f}% &nbsp;|&nbsp;  {lf_diff:+.1f} pp""",
                                unsafe_allow_html=True)

                st.markdown("---")
                if within_5:
                    st.success("Pipeline and analyst results are well-aligned. Calibration is sound.")
                else:
                    variances = {k: v for k, v, _, _ in comparisons if v is not None}
                    st.warning(f"""
                    **Total variance: {vt:+.1%}**

                    Review: P2P capture rates & stimulation, connecting city QSI calibration factors,
                    and base demand inputs. The tiered default calibration may diverge from expert values
                    for specific city pairs.
                    """)
            else:
                st.caption("Enter analyst total passengers to see comparison.")


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#8ba4c4;font-size:0.75rem;padding:1rem;">
Avia Solutions  QSI Route Forecast Portal v2.0  Chat 22<br>
Pipeline: 19 modules | Validated: BA LHR-SJC, KLM AMS-TPA, KE ICN-SJC, SQ SIN-SJC, CX HKG-SJC, FI KEF-SJC
</div>
""", unsafe_allow_html=True)
