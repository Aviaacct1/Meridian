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
    def ba_lhr_sjc(cls, project_dir: str = '/mnt/project') -> 'RouteConfig':
        """
        BA LHR-SJC (Feb 2015, without India).
        Target: 129,162 pax, 82.9% LF
        
        This is the primary regression test case validated across Chats 1-11.
        """
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
            qsi1_file=os.path.join(project_dir, 'QSILHR_v1_OS_JZ_17Feb15.xlsx'),
            qsi2_file=os.path.join(project_dir, 'QSISJC.xlsx'),
        )
        # Note: qsi1_file is used for BOTH QSI 1 and QSI 2 of the home perspective
        # qsi2_file is used for BOTH QSI 1 and QSI 2 of the dest perspective

        #  Demand provider: Forecast file with P2P config 
        p2p_config = _ba_lhr_sjc_p2p_config()
        cfg.demand_provider = ExcelDemandProvider(
            forecast_file=os.path.join(project_dir,
                                       'BA_Fcst_LHRSJC_JZ_23Feb2015_FINAL_without_INDIA.xlsm'),
            p2p_config=p2p_config,
            home_growth=0.09,
            dest_growth=0.10,
        )

        return cfg




    @classmethod
    def klm_ams_tpa(cls, project_dir: str = '/mnt/project') -> 'RouteConfig':
        """
        KLM AMS-TPA (2023 vintage, forecast year 2025).
        Target: 79,771 pax, 87.6% LF

        Key characteristics:
        - Existing route (operated in 2019), no stimulation
        - Hub connecting traffic at AMS only (TPA is not a hub)
        - 145 connecting cities scored, QSI ceiling: 0.60
        - Base year: 2019 Sabre data
        - Circuity threshold: 30% (max included 0.2913)
        """
        cfg = cls()
        cfg.airline_name = "KLM"
        cfg.airline_code = "KL"
        cfg.home_airport_code = "AMS"
        cfg.home_city_code = "AMS"
        cfg.dest_airport_code = "TPA"
        cfg.dest_city_code = "TPA"

        cfg.frequency = 3  # 3x weekly (Mon/Wed/Sat)
        cfg.aircraft_type = "A330-300"
        cfg.seats = 292
        cfg.outbound_dep = dtime(10, 30)
        cfg.outbound_arr = dtime(14, 50)
        cfg.return_dep = dtime(16, 55)
        cfg.return_arr = dtime(7, 30)
        cfg.flight_time_hrs = 10.0

        # QSI parameters - from QSIAMS.xlsx QSI Coefficients sheet
        cfg.qsi_ceiling = 0.60
        cfg.qsi_adjustment = 1.0
        cfg.online_coeff = 1.0
        cfg.alliance_coeff = 0.615
        cfg.interline_coeff = 0.25
        cfg.et_decay_factor = 0.8
        cfg.et_decay_interval = 0.1

        # Validation targets from Forecast Finalised
        cfg.target_total = 79771
        cfg.target_p2p = 26711
        cfg.target_cnx_home = 53060
        cfg.target_cnx_dest = 0
        cfg.target_load_factor = 0.876

        # Schedule provider
        cfg.schedule_provider = ExcelScheduleProvider(
            qsi1_file=os.path.join(project_dir, 'QSIAMS.xlsx'),
            qsi2_file=None,
        )

        # Demand provider
        p2p_config = _klm_ams_tpa_p2p_config()
        cfg.demand_provider = ExcelDemandProvider(
            forecast_file=os.path.join(project_dir, 'FcstKLM_AMSTPA.xlsm'),
            p2p_config=p2p_config,
            home_growth=0.1528,
            dest_growth=0.044,
        )

        return cfg


def _klm_ams_tpa_p2p_config() -> Dict[str, Any]:
    """
    KLM AMS-TPA P2P demand configuration.
    Base P2P: 38,617.37, Growth: 15.28%, Stim: 1.0, Capture: 60%
    """
    return {
        'segments': [
            {
                'name': 'Point to Point',
                'base_demand': 38617.37,
                'growth_rate': 0.1528,
                'seasonality': 1.0,
                'stimulation': 1.0,
                'capture_rate': 0.60,
            },
        ],
    }


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
