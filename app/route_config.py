#!/usr/bin/env python3
"""
Avia Solutions  Route Configuration (Chat 12)
================================================
Enhanced RouteConfig that bundles route parameters with provider references.

Each route assessment is fully defined by a RouteConfig instance that specifies:
    1. Route identity (airline, airports, schedule)
    2. QSI parameters (coefficients, ceiling, adjustment)
    3. Capacity parameters (aircraft, frequency, seats)
    4. Provider references (where to get schedule, demand, QSI data)
    5. Validation targets (for regression testing)

Factory methods create pre-configured instances for validated routes.
"""

from config import REFERENCE_CASE_DIR
import os
from datetime import time as dtime
from typing import Dict, Optional, Any

from providers import (
    ScheduleProvider, DemandProvider, QSICaptureProvider,
    ExcelScheduleProvider, ExcelDemandProvider,
    P2PSegmentData, P2PSubsegmentData,
)


class RouteConfig:
    """Complete configuration for a route assessment."""

    def __init__(self):
        #  Route identity 
        self.airline_name = ""
        self.airline_code = ""
        self.home_airport_code = ""
        self.home_city_code = ""
        self.dest_airport_code = ""
        self.dest_city_code = ""

        #  Schedule 
        self.frequency = 7
        self.aircraft_type = ""
        self.seats = 0
        self.outbound_dep = None  # time object
        self.outbound_arr = None
        self.return_dep = None
        self.return_arr = None
        self.flight_time_hrs = 0

        #  QSI parameters 
        self.qsi_ceiling = 1.0
        self.qsi_adjustment = 1.0
        self.online_coeff = 1.0
        self.alliance_coeff = 0.615
        self.interline_coeff = 0.25
        self.et_decay_factor = 0.8
        self.et_decay_interval = 0.1

        #  Providers (set by factory methods or manually) 
        self.schedule_provider: Optional[ScheduleProvider] = None
        self.demand_provider: Optional[DemandProvider] = None
        self.qsi_capture_provider: Optional[QSICaptureProvider] = None

        #  Validation targets (for regression) 
        self.target_total = 0
        self.target_p2p = 0
        self.target_cnx_home = 0
        self.target_cnx_dest = 0
        self.target_load_factor = 0.0

    @property
    def annual_capacity(self):
        return self.seats * self.frequency * 52 * 2

    @property
    def cnx_coeffs(self):
        return {
            'ONLINE': self.online_coeff,
            'ALLIANCE': self.alliance_coeff,
            'INTERLINING': self.interline_coeff,
        }

    def summary(self) -> str:
        """One-line summary for audit logs."""
        return (f"{self.airline_code} {self.home_airport_code}-{self.dest_airport_code} "
                f"| {self.aircraft_type} {self.seats}s {self.frequency}x/wk")

    # ================================================================
    # FACTORY METHODS  Validated Routes
    # ================================================================

    @classmethod
    def ba_lhr_sjc(cls, project_dir: str = None) -> 'RouteConfig':
        """
        BA LHR-SJC (Feb 2015, without India).
        Target: 129,162 pax, 82.9% LF
        
        This is the primary regression test case validated across Chats 1-11.
        """
        if project_dir is None:
            project_dir = str(REFERENCE_CASE_DIR)
        cfg = cls()
        cfg.airline_name = "British Airways"
        cfg.airline_code = "BA"
        cfg.home_airport_code = "LHR"
        cfg.home_city_code = "LON"
        cfg.dest_airport_code = "SJC"
        cfg.dest_city_code = "SJC"

        cfg.frequency = 7
        cfg.aircraft_type = "787-800"
        cfg.seats = 214
        cfg.outbound_dep = dtime(15, 30)
        cfg.outbound_arr = dtime(18, 30)
        cfg.return_dep = dtime(21, 30)
        cfg.return_arr = dtime(15, 55)
        cfg.flight_time_hrs = 11.0

        cfg.qsi_ceiling = 1.0
        cfg.qsi_adjustment = 1.0

        # Validation targets
        cfg.target_total = 129162
        cfg.target_p2p = 78110
        cfg.target_cnx_home = 48115
        cfg.target_cnx_dest = 2937
        cfg.target_load_factor = 0.829

        #  Schedule provider: Excel QSI files 
        # QSILHR contains BOTH QSI 1 and QSI 2 for the LHR perspective
        # QSISJC contains BOTH QSI 1 and QSI 2 for the SJC perspective
        cfg.schedule_provider = ExcelScheduleProvider(
            qsi1_file=os.path.join(project_dir, 'QSI Forecast', 'QSI', '@LHR',
                                   'QSI@LHR v1 (OS JZ) 17Feb15.xlsx'),
            qsi2_file=os.path.join(project_dir, 'QSI Forecast', 'QSI', '@SJC',
                                   'QSI@SJC.xlsx'),
        )
        # Note: qsi1_file is used for BOTH QSI 1 and QSI 2 of the home perspective
        # qsi2_file is used for BOTH QSI 1 and QSI 2 of the dest perspective

        #  Demand provider: Forecast file with P2P config 
        p2p_config = _ba_lhr_sjc_p2p_config()
        cfg.demand_provider = ExcelDemandProvider(
            forecast_file=os.path.join(project_dir, 'QSI Forecast',
                                       'BA Fcst LHR-SJC v2 (JZ OS) 03Mar15 without INDIA.xlsm'),
            p2p_config=p2p_config,
            home_growth=0.09,
            dest_growth=0.10,
        )

        return cfg


# ================================================================
# P2P CONFIGURATION HELPERS
# ================================================================

def _ba_lhr_sjc_p2p_config() -> Dict[str, Any]:
    """
    BA LHR-SJC P2P demand configuration.
    
    Values from BA_Fcst_LHRSJC_JZ_23Feb2015_FINAL_without_INDIA.xlsm,
    validated in Chat 1 (QSI Forecast Engine) and Chat 6 (Assembly Loop).
    """
    return {
        'segments': [
            {
                'name': 'UK Business',
                'base_demand': 71441.55,
                'growth_rate': 0.10,
                'seasonality': 1.0,
                'stimulation': 1.15,
                'capture_rate': 0.40,
            },
            {
                'name': 'UK Leisure/VFR',
                'base_demand': 0,  # computed from subsegments
                'growth_rate': 0.10,
                'seasonality': 1.0,
                'stimulation': 1.0,
                'capture_rate': 0.0,
                'subsegments': [
                    {'name': 'Primary', 'base_demand': 36385.76, 'growth_rate': 0.10,
                     'seasonality': 1.0, 'stimulation': 1.0, 'capture_rate': 0.25},
                    {'name': 'Secondary', 'base_demand': 17448.74, 'growth_rate': 0.10,
                     'seasonality': 1.0, 'stimulation': 1.0, 'capture_rate': 0.25},
                    {'name': 'Contested', 'base_demand': 4617.68, 'growth_rate': 0.10,
                     'seasonality': 1.0, 'stimulation': 1.0, 'capture_rate': 0.10},
                ],
            },
            {
                'name': 'US Business',
                'base_demand': 65946.05,
                'growth_rate': 0.10,
                'seasonality': 1.0,
                'stimulation': 1.15,
                'capture_rate': 0.15,
            },
            {
                'name': 'US Leisure/VFR',
                'base_demand': 0,
                'growth_rate': 0.10,
                'seasonality': 1.0,
                'stimulation': 1.0,
                'capture_rate': 0.0,
                'subsegments': [
                    {'name': 'Primary', 'base_demand': 33586.86, 'growth_rate': 0.10,
                     'seasonality': 1.0, 'stimulation': 1.0, 'capture_rate': 0.25},
                    {'name': 'Secondary', 'base_demand': 16106.53, 'growth_rate': 0.10,
                     'seasonality': 1.0, 'stimulation': 1.0, 'capture_rate': 0.25},
                    {'name': 'Contested', 'base_demand': 4262.47, 'growth_rate': 0.10,
                     'seasonality': 1.0, 'stimulation': 1.0, 'capture_rate': 0.10},
                ],
            },
        ],
    }
