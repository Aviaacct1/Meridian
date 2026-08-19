#!/usr/bin/env python3
"""The Sabre attribution constant (audit R3, 16 August 2026).

The GDD Work Order requires "Sabre Global Demand Data" to be clearly stated wherever
it is a material input. Before this module, five variant names were in use across the
surfaces (Sabre O&D, Sabre MI, Sabre MIDT, Sabre GDS bookings, Sabre ODPOO) and the
contractual form appeared nowhere. Every client-facing surface now takes its wording
from here; the deck modules carry the same wording as literals with a comment naming
this module, because their import path to app/ is not guaranteed at render time.

Internal code, comments and store labels may still say ODPOO or MIDT; those are not
client surfaces. The rule is: if a client can read it, the name is the contractual
one below.

Avia Solutions Limited. All rights reserved.
"""

# The contractual name, exactly as the Work Order states it.
SABRE_GDD = "Sabre Global Demand Data"

# The short form, for tight UI spots (pills, table headers) on a page that already
# carries the full form at least once.
SABRE_GDD_SHORT = "Sabre GDD"

# The defined gloss, used once on methodology-grade surfaces so a reader knows what
# the data is without the licence in front of them.
SABRE_GDD_GLOSS = ("Sabre Global Demand Data (MIDT bookings adjusted for bookings "
                   "made outside the global distribution systems)")

# The standard source line for figures produced by the forecast run.
# "Avia Cortex" was the development name and "AviaSolutions analysis" the consultancy
# habit; John's ruling, 18 August 2026: the PRODUCT speaks as Meridian, by The
# Aviation Observatory, everywhere a client reads.
SOURCE_LINE = ("Source: Meridian analysis, The Aviation Observatory; Sabre Global "
               "Demand Data; OAG schedules.")
