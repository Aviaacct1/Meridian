#!/usr/bin/env python3
"""Avia Solutions - are the eleven zero markets a real schedule, or missing data? 11 August 2026.

`_collapse` drops any leg whose flying time is missing or zero, in silence:

    f2 = l2.get("flying") or 0
    if f2 <= 0: continue

If the onward legs out of Taipei to these eleven markets carry no flying time in the board, the new
route scores zero on 6% of the beyond base for a data reason rather than a schedule reason, and the
two are not the same finding at all. This prints every onward leg for each zero market with its
departure time, flying time and the resulting connection gap against the proposed 16:45 arrival, so
the cause is visible per leg rather than inferred from the total.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), "app")
if APP not in sys.path:
    sys.path.insert(0, APP)

import duckdb                                    # noqa: E402
import qsi_feed as QF                            # noqa: E402
import mct_bank as MB                            # noqa: E402
from wave_cache import OagBoards                 # noqa: E402

DEST = "TPE"
DEP_TIME_MINS, FLYING_MINS = 11 * 60, 825
ZEROS = ["DXB", "TAO", "HKT", "CKG", "WUH", "NGB", "PQC", "AUH", "DMK", "BKI", "BWN"]
WORKING = ["MNL", "PVG", "HKG"]                   # three that do score, for contrast


def main():
    oag = os.environ["AVIA_OAG"]
    c = duckdb.connect(oag, read_only=True)
    week = c.execute("SELECT max(week) FROM oag").fetchone()[0]
    c.close()

    boards = OagBoards(oag)
    mct = MB.load_mct()
    rows = boards.dep_rows(week, DEST)
    hub_country = QF._board_country(rows, "dep")
    onward = {}
    for r in rows:
        if r.get("arr"):
            onward.setdefault(r["arr"], []).append(r)

    arr_mins = (DEP_TIME_MINS + FLYING_MINS) % 1440
    print(f"OAG week {week}. Proposed arrival at {DEST}: {arr_mins // 60:02d}:{arr_mins % 60:02d} "
          f"local, hub country {hub_country}, MAX_CONNECT {QF.MAX_CONNECT} minutes\n")

    for label, mkts in (("ZERO MARKETS", ZEROS), ("MARKETS THAT SCORE, for contrast", WORKING)):
        print(f"--- {label}")
        for m in mkts:
            legs = onward.get(m) or []
            n_noflying = sum(1 for r in legs if not (r.get("flying") or 0) > 0)
            n_nodep = sum(1 for r in legs if r.get("dep_mins") is None)
            reasons = {"no flying time": 0, "no dep time": 0, "under MCT": 0,
                       "over MAX_CONNECT": 0, "legal": 0}
            for r in legs:
                if r.get("dep_mins") is None:
                    reasons["no dep time"] += 1
                    continue
                if not (r.get("flying") or 0) > 0:
                    reasons["no flying time"] += 1
                    continue
                need = MB.mct_for(mct, DEST, inbound_intl=True,
                                  onward_intl=QF._intl(r.get("arr_country"), hub_country))
                g = QF._gap(arr_mins, r["dep_mins"])
                if g < need:
                    reasons["under MCT"] += 1
                elif g > QF.MAX_CONNECT:
                    reasons["over MAX_CONNECT"] += 1
                else:
                    reasons["legal"] += 1
            print(f"  {m:4} {len(legs):>3} onward legs | " +
                  ", ".join(f"{k} {v}" for k, v in reasons.items() if v))
            if legs and reasons["legal"] == 0 and len(legs) <= 6:
                for r in legs[:6]:
                    dm = r.get("dep_mins")
                    dt = f"{dm // 60:02d}:{dm % 60:02d}" if dm is not None else "  none"
                    print(f"        {r.get('carrier','??'):3} dep {dt} flying "
                          f"{r.get('flying')} freq {r.get('freq')} "
                          f"gap {QF._gap(arr_mins, dm) if dm is not None else 'n/a'}")
        print()


if __name__ == "__main__":
    main()
