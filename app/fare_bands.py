#!/usr/bin/env python3
"""Measured fares render as bands on self-serve surfaces (audit R5, 16 August 2026).

The Work Order permits repackaged analysis and forbids extracts; a measured market
fare printed in currency to the cent is a Sabre statistic travelling whole. The
tool's own written rule was index-only for fares, and the build had drifted from it.
Self-serve surfaces (the portal payload, the workbook, the packs and decks the portal
serves) show the band; the exact figure stays server-side and inside Avia-delivered
engagement work.

THE GRID IS FIXED AND STATED, not proportional, so a reader cannot recover the exact
figure from the band edges: $25 bands below $500, $50 to $1,500, $100 above. Band
labels carry no currency symbol; the surface adds its own.

deck/forecast_spec.py carries the same grid as a literal helper (the deck's import
path to app/ is not guaranteed at render time); change the grid in BOTH places or in
neither.

Avia Solutions Limited. All rights reserved.
"""


def band(value):
    """{"lo": int, "hi": int, "label": "400-425"} or None for no usable fare."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v <= 0:
        return None
    width = 25 if v < 500 else 50 if v < 1500 else 100
    lo = int(v // width) * width
    return {"lo": lo, "hi": lo + width, "label": "%d-%d" % (lo, lo + width)}
