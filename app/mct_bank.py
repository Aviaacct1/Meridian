#!/usr/bin/env python3
"""
Avia Cortex - MCT schedule-banking for the connecting feed (opt-in, back-test before default).
==============================================================================================
Turns the connecting feed from "assumes connectivity" into "proves connectivity". At the hub it
reads the onward departure bank from OAG (which carries local departure times), and for the new
flight's hub arrival it counts an onward flight as connectable only if it departs at least the MCT
after arrival (within a sensible window, same-day or overnight). Each onward market is then weighted
by the share of its weekly frequency that is genuinely connectable. It also picks the arrival time
that maximises the connectable market, which is what an airline does when it times the flight to hit
the wave, and which turns the indicative dep/arr times into real ones.

MCT comes from mct_master.csv (Airport x DOM/INT category); where the master is silent, default 60.
Inbound to the hub is treated as international (the new long-haul leg); onward is domestic or
international by comparing the onward arrival country with the hub country.
"""
import os
import csv

HERE = os.path.dirname(os.path.abspath(__file__))
MCT_CSV = os.path.join(HERE, "mct_master.csv")
DEFAULT_MCT = 60


def load_mct(path=MCT_CSV):
    """{(airport, dom_int): minutes}. dom_int is DOMDOM/DOMINT/INTDOM/INTINT."""
    d = {}
    try:
        with open(path, newline="") as fh:
            for r in csv.DictReader(fh):
                try:
                    d[(r["airport"].upper(), r["dom_int"].upper())] = int(float(r["mct_min"]))
                except Exception:
                    pass
    except Exception:
        pass
    return d


def mct_for(mct, airport, inbound_intl=True, onward_intl=True, default=DEFAULT_MCT):
    """Minutes for a connection at `airport`: cascading exact category -> airport max -> default."""
    cat = ("INT" if inbound_intl else "DOM") + ("INT" if onward_intl else "DOM")
    ap = (airport or "").upper()
    if (ap, cat) in mct:
        return mct[(ap, cat)]
    vals = [v for (a, c), v in mct.items() if a == ap]
    return max(vals) if vals else default


def _mins(t):
    """Local time -> minutes past midnight. Handles 1810, '18:10', '810', ints; None if unparseable."""
    if t is None:
        return None
    s = str(t).strip().replace(":", "").replace(".", "")
    if not s.isdigit():
        return None
    s = s.zfill(4)
    try:
        h, m = int(s[:-2]), int(s[-2:])
        return h * 60 + m if (h <= 23 and m <= 59) else None
    except Exception:
        return None


def _dow(days):
    """Weekly frequency from a days-of-op string like '1234567' or '1.3.5.7'."""
    if not days:
        return 1
    n = sum(1 for c in str(days) if c in "1234567")
    return n or 1


def hub_bank(oag_db, week, hub, hub_country=None):
    """Onward departures from the hub: {onward_airport: [(dep_mins, weekly_freq, onward_intl), ...]}."""
    import duckdb
    con = duckdb.connect(oag_db, read_only=True)
    try:
        rows = con.execute(
            "SELECT arr_airport, arr_country, dep_country, local_dep_time, days_of_op FROM oag "
            "WHERE week=? AND dep_airport=?", [week, hub]).fetchall()
    finally:
        con.close()
    if hub_country is None:
        # the hub's own country is the mode of dep_country on its departures
        from collections import Counter
        cc = Counter(r[2] for r in rows if r[2])
        hub_country = cc.most_common(1)[0][0] if cc else None
    bank = {}
    for arr, arr_country, _dc, dep_t, days in rows:
        dm = _mins(dep_t)
        if dm is None or not arr:
            continue
        onward_intl = (hub_country is None) or (str(arr_country).strip() != str(hub_country).strip())
        bank.setdefault(arr, []).append((dm, _dow(days), onward_intl))
    return bank


def connectable_share(deps, arr_mins, mct_fn, window=360):
    """Fraction of a city's onward weekly frequency connectable within [arr+MCT, arr+MCT+window].
    Considers same-day and overnight (dep + 1440) connections. mct_fn(onward_intl) -> minutes."""
    tot = sum(f for _, f, _ in deps)
    if not tot:
        return 0.0
    conn = 0
    for dm, f, oi in deps:
        need = mct_fn(oi)
        for base in (dm, dm + 1440):
            gap = base - arr_mins
            if need <= gap <= need + window:
                conn += f
                break
    return conn / tot


def optimise(bank, mct, hub, market=None, window=360, step=30):
    """Pick the hub arrival time (grid over the day) that maximises connectable market, and return
    (best_arr_mins, {onward_airport: connectable_share at that arrival}). market weights cities by
    their O&D size; if None, every city counts equally by frequency."""
    def mct_fn(onward_intl):
        return mct_for(mct, hub, inbound_intl=True, onward_intl=onward_intl)

    def score(arr):
        s = 0.0
        for city, deps in bank.items():
            w = (market.get(city, 0.0) if market else 1.0)
            if w > 0:
                s += w * connectable_share(deps, arr, mct_fn, window)
        return s

    best_arr, best = 0, -1.0
    for arr in range(0, 1440, step):
        v = score(arr)
        if v > best:
            best, best_arr = v, arr
    shares = {city: connectable_share(deps, best_arr, mct_fn, window) for city, deps in bank.items()}
    return best_arr, shares


def hhmm(mins):
    if mins is None:
        return "-"
    mins %= 1440
    return f"{mins // 60:02d}:{mins % 60:02d}"
