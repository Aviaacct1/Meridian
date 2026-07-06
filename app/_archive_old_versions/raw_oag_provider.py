#!/usr/bin/env python3
"""
Avia Solutions  Raw OAG Schedule Provider (Chat 23)
=====================================================
Implements ScheduleProvider that takes raw OAG Analyser Excel exports,
runs the Connection Builder at the hub airport, and produces Itinerary
objects for the QSI engine.

This replaces the ExcelScheduleProvider (which reads pre-computed QSI files)
with a provider that generates itineraries from scratch  the key missing
piece for processing genuinely new routes.

Pipeline position:
    Raw OAG files  OAG Parser  Connection Builder  RawOAGProvider  QSI Engine

Validation: BA LHR-SJC  compare connection counts and QSI scores
against the pre-computed QSILHR/QSISJC files.
"""

import os
import sys
from collections import defaultdict
from typing import List, Dict, Optional, Tuple, Set, Any

sys.path.insert(0, '/mnt/project')

from providers import Itinerary, ScheduleProvider
from oag_parser import (
    read_oag_xlsx, read_mct_xls, build_mct_lookup,
    _parse_time_to_minutes, _parse_hhmm_to_minutes,
)
from connection_builder import (
    build_connections, create_proposed_service,
    load_alliance_data, load_lcc_list,
    parse_days_string, get_dom_int,
)


# ============================================================================
# FLIGHT  LEG CONVERTER
# ============================================================================

def flight_to_leg(flight, idx: int) -> Dict:
    """Convert an oag_parser.Flight to connection builder leg dict."""
    dep_mins = _parse_hhmm_to_minutes(flight.dep_time)
    arr_mins = _parse_hhmm_to_minutes(flight.arr_time)
    flying_mins = _parse_time_to_minutes(flight.flying_time_str) or 0
    if flying_mins == 0:
        flying_mins = _parse_time_to_minutes(flight.elapsed_time_str) or 0
    dep_day_set = parse_days_string(flight.days_of_op)
    arr_day_str = flight.arr_day_offset
    if arr_day_str and str(arr_day_str).strip():
        arr_day_set = parse_days_string(str(arr_day_str))
    else:
        arr_day_set = dep_day_set.copy()

    return {
        'id': idx,
        'carrier': flight.carrier or '',
        'carrier_name': flight.carrier_name or '',
        'flight_no': str(flight.flight_no or ''),
        'dep_airport': flight.dep_airport or '',
        'dep_terminal': flight.dep_terminal or '',
        'dep_city': flight.dep_city or '',
        'dep_country': flight.dep_country or '',
        'arr_airport': flight.arr_airport or '',
        'arr_terminal': flight.arr_terminal or '',
        'arr_city': flight.arr_city or '',
        'arr_country': flight.arr_country or '',
        'dep_time': flight.dep_time,
        'arr_time': flight.arr_time,
        'dep_time_mins': dep_mins,
        'arr_time_mins': arr_mins,
        'dep_days': flight.days_of_op or '',
        'arr_days': str(arr_day_str) if arr_day_str else flight.days_of_op or '',
        'dep_day_set': dep_day_set,
        'arr_day_set': arr_day_set,
        'flying_time': flight.flying_time_str,
        'flying_mins': flying_mins,
        'dom_int': get_dom_int(flight.dep_country or '', flight.arr_country or ''),
        'seats': flight.seats or 0,
        'is_proposed': False,
    }


def connection_to_itinerary(cnx: Dict, use_origin_as_city: bool = False) -> Itinerary:
    """
    Convert connection builder output dict to Itinerary object.
    
    use_origin_as_city: If True, the city/airport are the leg1 ORIGIN
        (beyond city). Used for QSI 1 where we're measuring the beyond
        city's connectivity, not the final destination.
        If False, city/airport are the leg2 DESTINATION (standard).
    """
    if use_origin_as_city:
        city = cnx.get('dep_airport', '')  # origin of leg1
        airport = cnx.get('dep_airport', '')
    else:
        city = cnx.get('city_label', '')
        airport = cnx.get('airport_label', '')

    return Itinerary(
        city=city,
        airport=airport,
        route_label=cnx.get('route_label', ''),
        dep_airport=cnx.get('dep_airport', ''),
        cnx_airport=cnx.get('cnx_airport', ''),
        carrier_l1=cnx.get('leg1_carrier', ''),
        carrier_l2=cnx.get('leg2_carrier', ''),
        freq=cnx.get('frequency', 0),
        elapsed=int(cnx.get('elapsed_time', 0)),
        cnx_type=cnx.get('cnx_type', 'INTERLINING'),
        is_proposed=(cnx.get('leg1_is_proposed', False) or
                     cnx.get('leg2_is_proposed', False)),
    )


# ============================================================================
# RAW OAG PROVIDER
# ============================================================================

class RawOAGProvider(ScheduleProvider):
    """
    ScheduleProvider that generates itineraries from raw OAG schedule files.

    QSI Direction 1 (beyond home hub):
        Leg1 = flights arriving at hub from beyond cities
        Leg2 = flights departing hub to destination
        Connection: Beyond  Hub  Destination

    QSI Direction 2 (beyond destination):
        Leg1 = flights arriving at dest from origin
        Leg2 = flights departing dest to beyond cities
        Connection: Origin  Dest  Beyond
    """

    def __init__(self,
                 home_oag_file: str,
                 dest_oag_file: str,
                 home_airport: str,
                 dest_airport: str,
                 proposed_service: Dict = None,
                 home_mct_file: str = None,
                 dest_mct_file: str = None,
                 home_beyond_filter: Set[str] = None,
                 dest_beyond_filter: Set[str] = None,
                 catchment_airports: Dict[str, List[str]] = None,
                 alliance_file: str = None,
                 lcc_file: str = None,
                 min_connect: int = 20,
                 max_connect: int = 720,
                 default_mct: int = 90):

        self.home_oag_file = home_oag_file
        self.dest_oag_file = dest_oag_file
        self.home_airport = home_airport.upper()
        self.dest_airport = dest_airport.upper()
        self.proposed_service = proposed_service
        self.home_mct_file = home_mct_file
        self.dest_mct_file = dest_mct_file
        self.home_beyond_filter = home_beyond_filter
        self.dest_beyond_filter = dest_beyond_filter
        self.catchment_airports = catchment_airports or {}
        self.alliance_file = alliance_file
        self.lcc_file = lcc_file
        self.min_connect = min_connect
        self.max_connect = max_connect
        self.default_mct = default_mct

        self._cache: Dict[str, List[Itinerary]] = {}
        self._build_log: List[str] = []
        self._stats: Dict[str, Any] = {}
        self._alliances = None
        self._lcc_set = None

    def _log(self, msg: str):
        self._build_log.append(msg)
        print(msg)

    def _ensure_resources(self):
        if self._alliances is None:
            self._alliances = load_alliance_data(self.alliance_file)
            self._lcc_set = load_lcc_list(self.lcc_file)

    #  ScheduleProvider interface 

    def get_itineraries(self, direction: str) -> List[Itinerary]:
        if direction in self._cache:
            return self._cache[direction]
        self._ensure_resources()
        if direction == 'qsi1':
            result = self._build_qsi1()
        elif direction == 'qsi2':
            result = self._build_qsi2()
        else:
            result = []
        self._cache[direction] = result
        return result

    def get_metadata(self) -> Dict[str, Any]:
        return {
            'provider_type': 'RawOAGProvider',
            'home_oag_file': os.path.basename(self.home_oag_file),
            'dest_oag_file': os.path.basename(self.dest_oag_file),
            'home_airport': self.home_airport,
            'dest_airport': self.dest_airport,
            'has_proposed_service': self.proposed_service is not None,
            'stats': self._stats,
        }

    #  QSI Direction 1: Beyond Home Hub 

    def _build_qsi1(self) -> List[Itinerary]:
        """Beyond  Home Hub  Destination."""
        self._log(f"\n{''*60}")
        self._log(f"QSI 1: Beyond {self.home_airport}  {self.dest_airport}")
        self._log(f"{''*60}")

        meta, flights, beyond_dests = read_oag_xlsx(
            self.home_oag_file, self.home_airport)
        self._log(f"  OAG: {meta['file']}  {len(flights)} flights")

        included = self._resolve_beyond(beyond_dests, self.home_beyond_filter)
        self._log(f"  Beyond filter: {len(included)} cities" if included else "  Beyond filter: ALL")

        # Leg 1: arrivals at hub from beyond cities
        leg1 = []
        for idx, f in enumerate(flights):
            if f.direction and f.direction.upper() == 'ARR':
                if included and f.dep_airport not in included:
                    continue
                leg1.append(flight_to_leg(f, idx))

        # Leg 2: departures from hub to destination (+ catchment)
        dest_set = {self.dest_airport} | set(self.catchment_airports.get('dest', []))
        leg2 = []
        for idx, f in enumerate(flights):
            if f.direction and f.direction.upper() == 'DEP':
                if f.arr_airport in dest_set:
                    leg2.append(flight_to_leg(f, len(flights) + idx))

        # Inject proposed service
        if self.proposed_service:
            ps = self._make_proposed('outbound')
            leg2.append(ps)
            self._log(f"  Proposed: {ps['carrier']} {self.home_airport}"
                       f"{self.dest_airport} dep {ps['dep_time']}")

        self._log(f"  Leg1 (arrivals): {len(leg1)}  Leg2 (departures): {len(leg2)}")
        if not leg1 or not leg2:
            self._log("   No legs  skipping")
            return []

        # MCT
        mct = self._load_mct(self.home_mct_file, self.home_airport)

        # Build connections
        valid, failed = build_connections(
            leg1, leg2, self._alliances, mct, self._lcc_set,
            self.min_connect, self.max_connect, self.default_mct,
            hub_airport=self.home_airport)

        self._log(f"  Connections: {len(valid)} valid, {len(failed)} MCT fail")

        # Filter by beyond inclusion (dep_airport = beyond city origin)
        if included:
            pre = len(valid)
            valid = [c for c in valid if c['dep_airport'] in included]
            if len(valid) != pre:
                self._log(f"  After filter: {len(valid)}")

        # For QSI 1: city = beyond city (leg1 origin), not destination
        itineraries = [connection_to_itinerary(c, use_origin_as_city=True) for c in valid]
        cities = set(it.city for it in itineraries)
        self._stats['qsi1'] = {
            'flights': len(flights), 'leg1': len(leg1), 'leg2': len(leg2),
            'valid': len(valid), 'failed': len(failed),
            'itineraries': len(itineraries), 'cities': len(cities),
        }
        self._log(f"   {len(itineraries)} itineraries, {len(cities)} cities")
        return itineraries

    #  QSI Direction 2: Beyond Destination 

    def _build_qsi2(self) -> List[Itinerary]:
        """Origin  Destination  Beyond."""
        self._log(f"\n{''*60}")
        self._log(f"QSI 2: {self.home_airport}  {self.dest_airport}  Beyond")
        self._log(f"{''*60}")

        meta, flights, beyond_dests = read_oag_xlsx(
            self.dest_oag_file, self.dest_airport)
        self._log(f"  OAG: {meta['file']}  {len(flights)} flights")

        included = self._resolve_beyond(beyond_dests, self.dest_beyond_filter)
        self._log(f"  Beyond filter: {len(included)} cities" if included else "  Beyond filter: ALL")

        # Leg 1: arrivals at dest from origin
        home_set = {self.home_airport} | set(self.catchment_airports.get('home', []))
        leg1 = []
        for idx, f in enumerate(flights):
            if f.direction and f.direction.upper() == 'ARR':
                if f.dep_airport in home_set:
                    leg1.append(flight_to_leg(f, idx))

        # Inject proposed (inbound arrival at dest)
        if self.proposed_service:
            ps = self._make_proposed('inbound')
            leg1.append(ps)
            self._log(f"  Proposed: {ps['carrier']} {self.home_airport}"
                       f"{self.dest_airport} arr {ps['arr_time']}")

        # Leg 2: departures from dest to beyond
        leg2 = []
        for idx, f in enumerate(flights):
            if f.direction and f.direction.upper() == 'DEP':
                if included and f.arr_airport not in included:
                    continue
                leg2.append(flight_to_leg(f, len(flights) + idx))

        self._log(f"  Leg1 (arrivals from origin): {len(leg1)}  Leg2 (departures): {len(leg2)}")
        if not leg1 or not leg2:
            self._log("   No legs  skipping")
            return []

        mct = self._load_mct(self.dest_mct_file, self.dest_airport)

        valid, failed = build_connections(
            leg1, leg2, self._alliances, mct, self._lcc_set,
            self.min_connect, self.max_connect, self.default_mct,
            hub_airport=self.dest_airport)

        self._log(f"  Connections: {len(valid)} valid, {len(failed)} MCT fail")

        if included:
            pre = len(valid)
            valid = [c for c in valid if c['airport_label'] in included]
            if len(valid) != pre:
                self._log(f"  After filter: {len(valid)}")

        # For QSI 2: city = beyond city (leg2 destination)  standard
        itineraries = [connection_to_itinerary(c, use_origin_as_city=False) for c in valid]
        cities = set(it.city for it in itineraries)
        self._stats['qsi2'] = {
            'flights': len(flights), 'leg1': len(leg1), 'leg2': len(leg2),
            'valid': len(valid), 'failed': len(failed),
            'itineraries': len(itineraries), 'cities': len(cities),
        }
        self._log(f"   {len(itineraries)} itineraries, {len(cities)} cities")
        return itineraries

    #  Helpers 

    def _resolve_beyond(self, beyond_dests, explicit_filter) -> Set[str]:
        if explicit_filter:
            return explicit_filter
        if beyond_dests:
            included = {d['airport'] for d in beyond_dests
                        if d.get('include', '').upper() == 'IN'}
            if included:
                return included
        return set()

    def _make_proposed(self, direction: str) -> Dict:
        ps = self.proposed_service
        return create_proposed_service(
            origin=self.home_airport,
            destination=self.dest_airport,
            carrier=ps.get('carrier', 'XX'),
            freq=ps.get('frequency', 7),
            dep_time=ps.get('dep_time', '0900'),
            arr_time=ps.get('arr_time', '1200'),
            dep_days=ps.get('dep_days', '1234567'),
            flying_time=ps.get('flying_time_mins', 600),
            dep_country=ps.get('dep_country', ''),
            arr_country=ps.get('arr_country', ''),
            dep_city=self.home_airport,
            arr_city=self.dest_airport,
        )

    def _load_mct(self, mct_file, airport) -> Dict:
        if mct_file and os.path.exists(mct_file):
            try:
                entries = read_mct_xls(mct_file)
                mct = build_mct_lookup(entries, airport)
                self._log(f"  MCT: {len(mct)} rules for {airport}")
                return mct
            except Exception as e:
                self._log(f"  MCT warning: {e}")
        return {}

    @staticmethod
    def load_beyond_from_oag(oag_file: str, airport: str) -> Tuple[Set[str], Set[str]]:
        """Load beyond destination lists from OAG file."""
        _, _, beyond = read_oag_xlsx(oag_file, airport)
        included = {d['airport'] for d in beyond if d.get('include', '').upper() == 'IN'}
        excluded = {d['airport'] for d in beyond if d.get('include', '').upper() == 'OUT'}
        return included, excluded


# ============================================================================
# MULTI-HUB RAW OAG PROVIDER
# ============================================================================

class MultiHubRawOAGProvider(ScheduleProvider):
    """
    ScheduleProvider that builds itineraries from raw OAG data across
    MULTIPLE competitor hub airports  matching what the QSI Excel files
    contain.
    
    The QSI model evaluates the ENTIRE competitive landscape. For BA LHR-SJC,
    this means connections not just through LHR, but also through FRA (LH),
    CDG (AF), AMS (KL), EWR (UA), ORD (UA/AA), JFK (multiple), etc.
    
    For QSI Direction 1 (beyond home hub):
        Run connection builder at the home hub for EVERY beyond city:
        - Which carriers fly BeyondCity  Hub  Destination?
        - What are their elapsed times, frequencies, connection types?
        
    This requires:
        1. The home OAG file (contains all arrivals/departures at LHR)
        2. The dest OAG file (contains all arrivals/departures at SJC)
        
    The home OAG file tells us which carriers arrive at LHR from Paris,
    and which carriers depart LHR for... well, SJC doesn't exist yet as a
    destination from LHR. BUT the competitor hubs (FRA, CDG etc.) DO serve
    SJC indirectly  the beyond passenger from Paris can:
        a) Fly PARLHRSJC on BA (the proposed service)
        b) Fly PARCDGSFOSJC on AF (competitor via CDG)
        c) Fly PARFRASFOSJC on LH (competitor via FRA)
    
    So for full QSI we actually need OAG data for ALL intermediate hubs.
    In the original Excel workflow, the analyst runs the Connection Builder
    separately for each hub using OAG data pulled for that specific hub.
    
    This multi-hub provider automates that by:
        - Using the home OAG file for the home hub connections
        - Using the dest OAG file for the dest hub connections
        - Accepting additional hub OAG files for competitor hubs
    
    Parameters:
        home_oag_file: OAG file for home airport
        dest_oag_file: OAG file for dest airport
        hub_oag_files: Dict of hub_code -> oag_file_path for competitor hubs
        home_airport, dest_airport: IATA codes
        proposed_service: Dict with proposed service params
        home_beyond_filter: Set of included beyond airports (home side)
        dest_beyond_filter: Set of included beyond airports (dest side)
        ... (same optional params as RawOAGProvider)
    """

    def __init__(self,
                 home_oag_file: str,
                 dest_oag_file: str,
                 home_airport: str,
                 dest_airport: str,
                 hub_oag_files: Dict[str, str] = None,
                 proposed_service: Dict = None,
                 home_beyond_filter: Set[str] = None,
                 dest_beyond_filter: Set[str] = None,
                 mct_files: Dict[str, str] = None,
                 catchment_airports: Dict[str, List[str]] = None,
                 alliance_file: str = None,
                 lcc_file: str = None,
                 min_connect: int = 20,
                 max_connect: int = 720,
                 default_mct: int = 90):

        self.home_oag_file = home_oag_file
        self.dest_oag_file = dest_oag_file
        self.home_airport = home_airport.upper()
        self.dest_airport = dest_airport.upper()
        self.hub_oag_files = hub_oag_files or {}
        self.proposed_service = proposed_service
        self.home_beyond_filter = home_beyond_filter
        self.dest_beyond_filter = dest_beyond_filter
        self.mct_files = mct_files or {}
        self.catchment_airports = catchment_airports or {}
        self.alliance_file = alliance_file
        self.lcc_file = lcc_file
        self.min_connect = min_connect
        self.max_connect = max_connect
        self.default_mct = default_mct

        self._cache: Dict[str, List[Itinerary]] = {}
        self._build_log: List[str] = []
        self._stats: Dict[str, Any] = {}
        self._alliances = None
        self._lcc_set = None

        # Ensure home/dest are in hub_oag_files
        if self.home_airport not in self.hub_oag_files:
            self.hub_oag_files[self.home_airport] = self.home_oag_file
        if self.dest_airport not in self.hub_oag_files:
            self.hub_oag_files[self.dest_airport] = self.dest_oag_file

    def _log(self, msg: str):
        self._build_log.append(msg)
        print(msg)

    def _ensure_resources(self):
        if self._alliances is None:
            self._alliances = load_alliance_data(self.alliance_file)
            self._lcc_set = load_lcc_list(self.lcc_file)

    def get_itineraries(self, direction: str) -> List[Itinerary]:
        if direction in self._cache:
            return self._cache[direction]
        self._ensure_resources()
        if direction == 'qsi1':
            result = self._build_multi_qsi1()
        elif direction == 'qsi2':
            result = self._build_multi_qsi2()
        else:
            result = []
        self._cache[direction] = result
        return result

    def get_metadata(self) -> Dict[str, Any]:
        return {
            'provider_type': 'MultiHubRawOAGProvider',
            'home_airport': self.home_airport,
            'dest_airport': self.dest_airport,
            'hub_count': len(self.hub_oag_files),
            'hubs': list(self.hub_oag_files.keys()),
            'stats': self._stats,
        }

    def _build_multi_qsi1(self) -> List[Itinerary]:
        """
        QSI 1: Beyond  Hub  Destination, across ALL hubs.
        
        For each hub airport with an OAG file:
            - Leg1 = flights arriving at hub from beyond cities
            - Leg2 = flights departing hub toward destination
            - Build connections at that hub
        
        The home hub includes the proposed service.
        Competitor hubs use their existing schedules only.
        """
        self._log(f"\n{'='*60}")
        self._log(f"MULTI-HUB QSI 1: Beyond  Hubs  {self.dest_airport}")
        self._log(f"Hubs: {list(self.hub_oag_files.keys())}")
        self._log(f"{'='*60}")

        all_itineraries = []
        hub_stats = {}

        # Resolve home-side beyond filter
        _, home_flights, home_beyond = read_oag_xlsx(
            self.home_oag_file, self.home_airport)
        home_included = self._resolve_beyond(home_beyond, self.home_beyond_filter)

        for hub_code, oag_file in self.hub_oag_files.items():
            self._log(f"\n   Hub: {hub_code} ")
            
            if not os.path.exists(oag_file):
                self._log(f"     File not found: {oag_file}")
                continue

            meta, flights, beyond = read_oag_xlsx(oag_file, hub_code)
            self._log(f"    OAG: {len(flights)} flights")

            # For the home hub, use the home beyond filter
            # For competitor hubs, use the same beyond filter
            # (we want the same set of beyond cities across all hubs)
            included = home_included

            # Leg 1: arrivals at this hub from beyond cities
            leg1 = []
            for idx, f in enumerate(flights):
                if f.direction and f.direction.upper() == 'ARR':
                    if included and f.dep_airport not in included:
                        continue
                    leg1.append(flight_to_leg(f, idx))

            # Leg 2: departures from this hub toward destination
            dest_set = {self.dest_airport} | set(self.catchment_airports.get('dest', []))
            leg2 = []
            for idx, f in enumerate(flights):
                if f.direction and f.direction.upper() == 'DEP':
                    if f.arr_airport in dest_set:
                        leg2.append(flight_to_leg(f, len(flights) + idx))

            # Inject proposed service only at home hub
            if hub_code == self.home_airport and self.proposed_service:
                ps = create_proposed_service(
                    origin=self.home_airport,
                    destination=self.dest_airport,
                    carrier=self.proposed_service.get('carrier', 'XX'),
                    freq=self.proposed_service.get('frequency', 7),
                    dep_time=self.proposed_service.get('dep_time', '0900'),
                    arr_time=self.proposed_service.get('arr_time', '1200'),
                    dep_days=self.proposed_service.get('dep_days', '1234567'),
                    flying_time=self.proposed_service.get('flying_time_mins', 600),
                    dep_country=self.proposed_service.get('dep_country', ''),
                    arr_country=self.proposed_service.get('arr_country', ''),
                    dep_city=self.home_airport,
                    arr_city=self.dest_airport,
                )
                leg2.append(ps)
                self._log(f"    + Proposed service injected")

            self._log(f"    Leg1: {len(leg1)}  Leg2: {len(leg2)}")

            if not leg1 or not leg2:
                self._log(f"    Skipped (no legs)")
                hub_stats[hub_code] = {'itineraries': 0, 'skipped': True}
                continue

            # MCT
            mct = {}
            mct_file = self.mct_files.get(hub_code)
            if mct_file and os.path.exists(mct_file):
                try:
                    entries = read_mct_xls(mct_file)
                    mct = build_mct_lookup(entries, hub_code)
                except Exception:
                    pass

            # Build connections
            valid, failed = build_connections(
                leg1, leg2, self._alliances, mct, self._lcc_set,
                self.min_connect, self.max_connect, self.default_mct,
                hub_airport=hub_code)

            # Filter by beyond inclusion
            if included:
                valid = [c for c in valid if c['dep_airport'] in included]

            # Convert  use origin as city (beyond city)
            hub_itineraries = [connection_to_itinerary(c, use_origin_as_city=True)
                               for c in valid]
            
            cities = set(it.city for it in hub_itineraries)
            self._log(f"     {len(hub_itineraries)} itineraries, {len(cities)} cities")
            
            hub_stats[hub_code] = {
                'itineraries': len(hub_itineraries),
                'cities': len(cities),
                'valid': len(valid),
                'failed': len(failed),
            }
            all_itineraries.extend(hub_itineraries)

        total_cities = set(it.city for it in all_itineraries)
        self._stats['qsi1'] = {
            'total_itineraries': len(all_itineraries),
            'total_cities': len(total_cities),
            'hubs': hub_stats,
        }
        self._log(f"\n  TOTAL QSI 1: {len(all_itineraries)} itineraries, "
                   f"{len(total_cities)} cities across {len(hub_stats)} hubs")

        return all_itineraries

    def _build_multi_qsi2(self) -> List[Itinerary]:
        """
        QSI 2: Origin  Hub  Beyond, across ALL hubs.
        
        For each hub with OAG data:
            - Leg1 = flights arriving at hub from origin side
            - Leg2 = flights departing hub to beyond cities
        """
        self._log(f"\n{'='*60}")
        self._log(f"MULTI-HUB QSI 2: {self.home_airport}  Hubs  Beyond")
        self._log(f"{'='*60}")

        all_itineraries = []
        hub_stats = {}

        # Resolve dest-side beyond filter
        _, dest_flights, dest_beyond = read_oag_xlsx(
            self.dest_oag_file, self.dest_airport)
        dest_included = self._resolve_beyond(dest_beyond, self.dest_beyond_filter)

        for hub_code, oag_file in self.hub_oag_files.items():
            self._log(f"\n   Hub: {hub_code} ")
            
            if not os.path.exists(oag_file):
                self._log(f"     File not found: {oag_file}")
                continue

            meta, flights, beyond = read_oag_xlsx(oag_file, hub_code)

            # Leg 1: arrivals at this hub from origin side
            home_set = {self.home_airport} | set(self.catchment_airports.get('home', []))
            leg1 = []
            for idx, f in enumerate(flights):
                if f.direction and f.direction.upper() == 'ARR':
                    if f.dep_airport in home_set:
                        leg1.append(flight_to_leg(f, idx))

            # Inject proposed at dest hub (arrival)
            if hub_code == self.dest_airport and self.proposed_service:
                ps = create_proposed_service(
                    origin=self.home_airport,
                    destination=self.dest_airport,
                    carrier=self.proposed_service.get('carrier', 'XX'),
                    freq=self.proposed_service.get('frequency', 7),
                    dep_time=self.proposed_service.get('dep_time', '0900'),
                    arr_time=self.proposed_service.get('arr_time', '1200'),
                    dep_days=self.proposed_service.get('dep_days', '1234567'),
                    flying_time=self.proposed_service.get('flying_time_mins', 600),
                    dep_country=self.proposed_service.get('dep_country', ''),
                    arr_country=self.proposed_service.get('arr_country', ''),
                    dep_city=self.home_airport,
                    arr_city=self.dest_airport,
                )
                leg1.append(ps)
                self._log(f"    + Proposed service injected (arrival)")

            # Leg 2: departures from this hub to beyond cities
            leg2 = []
            for idx, f in enumerate(flights):
                if f.direction and f.direction.upper() == 'DEP':
                    if dest_included and f.arr_airport not in dest_included:
                        continue
                    leg2.append(flight_to_leg(f, len(flights) + idx))

            self._log(f"    Leg1: {len(leg1)}  Leg2: {len(leg2)}")

            if not leg1 or not leg2:
                hub_stats[hub_code] = {'itineraries': 0, 'skipped': True}
                continue

            mct = {}
            mct_file = self.mct_files.get(hub_code)
            if mct_file and os.path.exists(mct_file):
                try:
                    entries = read_mct_xls(mct_file)
                    mct = build_mct_lookup(entries, hub_code)
                except Exception:
                    pass

            valid, failed = build_connections(
                leg1, leg2, self._alliances, mct, self._lcc_set,
                self.min_connect, self.max_connect, self.default_mct,
                hub_airport=hub_code)

            if dest_included:
                valid = [c for c in valid if c['airport_label'] in dest_included]

            # QSI 2: city = destination (standard)
            hub_itineraries = [connection_to_itinerary(c, use_origin_as_city=False)
                               for c in valid]

            cities = set(it.city for it in hub_itineraries)
            self._log(f"     {len(hub_itineraries)} itineraries, {len(cities)} cities")

            hub_stats[hub_code] = {
                'itineraries': len(hub_itineraries),
                'cities': len(cities),
            }
            all_itineraries.extend(hub_itineraries)

        total_cities = set(it.city for it in all_itineraries)
        self._stats['qsi2'] = {
            'total_itineraries': len(all_itineraries),
            'total_cities': len(total_cities),
            'hubs': hub_stats,
        }
        self._log(f"\n  TOTAL QSI 2: {len(all_itineraries)} itineraries, "
                   f"{len(total_cities)} cities across {len(hub_stats)} hubs")

        return all_itineraries

    def _resolve_beyond(self, beyond_dests, explicit_filter) -> Set[str]:
        if explicit_filter:
            return explicit_filter
        if beyond_dests:
            included = {d['airport'] for d in beyond_dests
                        if d.get('include', '').upper() == 'IN'}
            if included:
                return included
        return set()


# ============================================================================
# VALIDATION COMPARISON
# ============================================================================

def compare_providers(raw_prov: RawOAGProvider, excel_prov, direction: str) -> Dict:
    """Compare RawOAGProvider vs ExcelScheduleProvider output."""
    raw = raw_prov.get_itineraries(direction)
    excel = excel_prov.get_itineraries(direction)

    def city_stats(its):
        d = defaultdict(lambda: {'count': 0, 'freq': 0, 'routes': set()})
        for it in its:
            d[it.city]['count'] += 1
            d[it.city]['freq'] += it.freq
            d[it.city]['routes'].add(it.route_label)
        return d

    rc, ec = city_stats(raw), city_stats(excel)
    both = set(rc) & set(ec)

    return {
        'direction': direction,
        'raw_itineraries': len(raw), 'excel_itineraries': len(excel),
        'raw_cities': len(rc), 'excel_cities': len(ec),
        'cities_both': len(both),
        'cities_raw_only': sorted(set(rc) - set(ec)),
        'cities_excel_only': sorted(set(ec) - set(rc)),
    }
