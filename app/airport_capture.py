"""Avia Cortex - airport capture overrides (real catchment truth beats the model).
====================================================================================
For airports where we have measured catchment truth - passenger surveys, cell-phone / mobility data,
a dedicated catchment study - that beats the model's drive-time + size-pull allocation, set the
airport's capture SHARE of its catchment market directly here. It is applied when that airport is the
ORIGIN of a forecast route (i.e. it now has the competing nonstop), overriding the modelled QSI share.

Precedence: a user's Expert share override wins; then this table; then the modelled share.

Why this exists: the size-pull that stops small airports over-reading also UNDER-reads a genuine
secondary airport that has its own independent catchment. SJC is the textbook case - the South Bay is
a distinct ~3m catchment, but SFO's size dominates the choice model, so SJC models at ~0.11 when
survey + mobility data show 0.30-0.35 with competing service. This is the airport-by-airport capture
adjustment; seed it from measured data, and from the back-test airport factors where those are stable.
"""
AIRPORT_CAPTURE = {
    # code: capture share of the catchment market with a competing nonstop  (source)
    "SJC": 0.32,   # South Bay distinct ~3m catchment; Avia survey + cell-phone data, 30-35% with service
}


def capture_for(origin):
    """Measured capture share for this origin airport, or None to use the model."""
    return AIRPORT_CAPTURE.get((origin or "").upper())
