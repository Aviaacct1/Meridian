"""Avia Solutions - Sabre coverage gross-up.
====================================================================================
The measured Sabre O&D market under-records bookings made outside the GDS. LCC-dominated
markets (Poland, Portugal, Romania, Ukraine - Wizz/Ryanair country) book direct on the
airline site, so their point-to-point market reads thin; GDS-mature legacy markets (Britain,
Germany, Austria, US) read full or slightly rich. Short-haul carries a further off-GDS gap
on top, independent of country. These factors gross the measured market back up to true size
BEFORE capture and stimulation, so the engine forecasts a share of the real market, not the
recorded fragment.

Provenance: derived from the feed-inclusive Y2 back-test (backtest_results.csv). Country factor
= median(p2p_outturn / captured) by origin country, shrunk toward 1.0 by sample size (k=8) and
clamped [0.6, 2.0]; the short-haul residual is fitted NET of the country factor (only <800km
still under-reads, at 1.54) so the two axes do not double-count. Origin and destination are
combined as a geometric mean - a country's GDS penetration is a property of the market, not the
direction of travel, so a Poland-Britain route and its reverse get the same gross-up.

This is a v1 launch layer, coarse by design. Large-n, externally-coherent countries (PL, IT, GB,
ES, DE) are the trustworthy corrections; thin-n ones (PT, AT, US at n=4) are heavily shrunk and
should be refit as the sample grows. Unlisted countries default to 1.0 (no correction).
"""
import math

# origin-country coverage factor (shrunk to n, clamped); >1 = Sabre under-records the market
COUNTRY = {
    "PL": 2.00, "PT": 2.00, "RO": 1.32, "UA": 1.30, "SE": 1.11, "FR": 1.08,
    "ES": 1.01, "US": 0.93, "IT": 0.92, "GB": 0.88, "DE": 0.83, "AT": 0.80,
}
DEFAULT = 1.0
CLAMP_LO, CLAMP_HI = 0.55, 2.2


def _haul_resid(gcd_km):
    """Short-sector residual after the country factor: 1.50 at <=600km, tapering to 1.0 by
    1000km so there is no cliff at the band edge; no adjustment beyond that."""
    if gcd_km <= 600.0:
        return 1.50
    if gcd_km >= 1000.0:
        return 1.0
    return 1.0 + 0.50 * (1000.0 - gcd_km) / 400.0


def gross_up(origin_country, dest_country, gcd_km):
    """Multiplier on the measured Sabre P2P market. Combines both endpoints' coverage
    (geometric mean) with the short-haul residual, clamped to a sane range."""
    co = COUNTRY.get((origin_country or "").upper(), DEFAULT)
    cd = COUNTRY.get((dest_country or "").upper(), DEFAULT)
    cc = math.sqrt(co * cd)
    return min(CLAMP_HI, max(CLAMP_LO, cc * _haul_resid(gcd_km)))
