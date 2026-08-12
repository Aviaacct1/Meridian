#!/usr/bin/env python3
r"""Avia Solutions - the three BT2 inputs the training chain and the live path must build the same way.

    import bt2_capture_core as CORE
    legs = CORE.load_legs(con, "2025-06", {"SJC", "TPE"})
    comp = CORE.components(legs, "SJC", "TPE", alliances, mct, lcc, coords, block)
    capa = CORE.capa_from_components(comp, block, freq)

WHY THIS FILE EXISTS. Until 12 August 2026 these three quantities were built by one piece of code in
training and a different piece of code in the live path, and nobody had compared them.

    capa      TRAINING  bt2_capture.cap_from, qns / (qns + qcx): the proposed nonstop's frequency
                        against the one-stop itineraries between the same two airports, averaged
                        over the two directions. A nonstop-versus-connecting share of the PAIR's own
                        service, measured median 0.9168 and tenth percentile 0.4896 on the pin's
                        four cohorts.
              LIVE      route_context line 194 set it to the engine's qsi_share, which is the share
                        of the CATCHMENT's traffic to the destination won at the origin airport, and
                        reads 0.059 at daily on SJC-TPE. A different quantity on a different scale.
                        Every live route would have entered the model below the tenth percentile of
                        training, silently, and the published accuracy would have described nothing
                        the client sees.

    qcx       TRAINING  bt2_lib line 60, BOTH directions summed and with no one-stop factor.
              LIVE      one set of engine sums, one direction.

    legs_n    TRAINING  len(legs) from load_legs: every OAG leg touching either endpoint in the
                        pre-launch week.
              LIVE      the connection-set leg count from route_qsi, which is a different count over
                        a different set.

bt2_wiring_test.py could not have caught any of it. It proved that bt2_forecast._vec and
bt2_g12_exp.X_of build the same vector FROM THE SAME INPUTS, feeding both sides from the training
rows, and never called route_context at all.

THE FIX IS ONE IMPLEMENTATION RATHER THAN TWO, which is John's ruling of 9 August applied to the
three inputs it was not applied to. This module is that implementation. bt2/bt2_capture.py imports
it for training and app/route_context.py imports it for the live path, so the two cannot drift.

TWO QUANTITIES ARE CALLED qcx AND THEY ARE NOT THE SAME. Inside cap_from, qcx carries the 0.20
one-stop factor. The MODEL FEATURE called qcx does not, and sums both directions. Naming them alike
is most of how this went wrong, so each is built by its own named function below and neither is
derived from the other.

Avia Solutions Limited. All rights reserved.
"""
import statistics

# Weightings. BT2's definition of how a connecting itinerary competes with a nonstop, not the
# engine's, so they live on this side and are stated once.
W_ALLIANCE = 0.75
W_INTERLINE = 0.25
ONESTOP = 0.20


def elapsed_penalty(el, mn):
    """How far an itinerary's elapsed time falls behind the best available, as a decay. bt2_capture's
    own _et, reproduced here rather than imported from it, because bt2 imports the engine and a cycle
    between the two is worse than one shared formula. route_qsi carries the same five lines for the
    connection-set summary it returns, and a change to any of them is a change to all of them."""
    x = (el - mn) / 60.0
    return 1.0 if x <= 0 else 1.0 / ((int(x / 0.1) + 1) ** 0.8)


def load_legs(con, mon, apset):
    """Every scheduled OAG leg touching either endpoint in the representative week of a month.

    mon is a MONTH label, "2025-06". The window is the 15th to the 21st, which is what the training
    chain used for every one of the 6,524 launches, so a live route asking the model a question must
    use the same construction or it is asking a different question.

    The p16 and p01 fallbacks are the Asia split-month labels. bt2/migrate_oag_asia_labels.py folded
    those on 11 August 2026 and the fallbacks are now dead on a migrated store, but they are kept
    because an unmigrated copy of the store would otherwise return no legs at all and the caller
    would read that as a route with no competition.
    """
    import connection_builder as CB
    s = "(" + ",".join("'%s'" % a for a in apset) + ")"
    base = """SELECT DISTINCT carrier, flight_no, dep_airport, arr_airport, dep_terminal,
      arr_terminal, dep_country, arr_country, local_dep_time, local_arr_time,
      days_of_op, arr_days_of_op, flying_time, elapsed_time, alliance, carrier_category
      FROM oag WHERE week=? AND service_type='J'
      AND (dep_airport IN %s OR arr_airport IN %s)
      AND try_cast(strftime(try_cast(eff_from AS date), '%%d') AS int) IS NOT NULL
      AND try_cast(eff_from AS date) <= ?::date AND try_cast(eff_to AS date) >= ?::date"""
    w_lo, w_hi = f"{mon}-15", f"{mon}-21"
    rows = con.execute(base % (s, s), [mon, w_hi, w_lo]).fetchall()
    if not rows:
        rows = con.execute(base % (s, s), [mon + "p16", w_hi, w_lo]).fetchall()
        if not rows:
            rows = con.execute(base % (s, s), [mon + "p01", w_hi, w_lo]).fetchall()
    legs = []
    for r in rows:
        (car, fno, dep, arr, dt, at, dc, ac, ldt, lat, dop, adop, fly, el, alli, cat) = r
        try:
            dtm = CB.parse_time_hhmm(ldt)
        except Exception:                                   # noqa: BLE001
            dtm = None
        try:
            atm = CB.parse_time_hhmm(lat)
        except Exception:                                   # noqa: BLE001
            atm = None
        L = {'carrier': str(car).strip(), 'flight_no': str(fno or '').strip(),
             'dep_airport': str(dep).strip(), 'arr_airport': str(arr).strip(),
             'dep_terminal': str(dt or '').strip(), 'arr_terminal': str(at or '').strip(),
             'dep_country': str(dc or '').strip(), 'arr_country': str(ac or '').strip(),
             'dep_time_mins': dtm, 'arr_time_mins': atm,
             'flying_mins': CB._parse_duration_mins(fly or el),
             'dep_day_set': CB.parse_days_string(dop),
             'arr_day_set': CB.parse_days_string(adop or dop),
             'alliance': str(alli or '').strip(), 'carrier_category': str(cat or '').strip(),
             'id': len(legs)}
        L['dom_int'] = CB.get_dom_int(L['dep_country'], L['arr_country'])
        legs.append(L)
    return legs


def components(legs, a, b, alliances, mct, lcc, coords, block, circuity=1.25):
    """Per direction: (S_online, S_alliance, S_interline, mn). Sums are frequency times the elapsed
    penalty, by connection type, over the one-stop itineraries between the same two airports."""
    import connection_builder as CB
    import schedule_chain as SC
    out = []
    for oo, dd in ((a, b), (b, a)):
        leg1 = [l for l in legs if l['dep_airport'] == oo]
        leg2 = [l for l in legs if l['arr_airport'] == dd]
        if not leg1 or not leg2:
            out.append((0.0, 0.0, 0.0, block))
            continue
        valid, _ = CB.build_connections(leg1, leg2, alliances, mct, lcc, 20, 720, 90, hub_airport=None)
        valid = SC.circuity_filter(valid, coords, circuity)
        mn = min([c['elapsed_time'] for c in valid] + [block]) if valid else block
        S = {'ONLINE': 0.0, 'ALLIANCE': 0.0, 'INTERLINING': 0.0}
        for c in valid:
            S[c['cnx_type']] = S.get(c['cnx_type'], 0.0) + c['frequency'] * elapsed_penalty(
                c['elapsed_time'], mn)
        out.append((S['ONLINE'], S['ALLIANCE'], S['INTERLINING'], mn))
    return out


def cap_from(so, sa, si, mn, block, freq, w_all=W_ALLIANCE, w_int=W_INTERLINE, onestop=ONESTOP):
    """One direction's nonstop share. THE qcx INSIDE THIS FUNCTION IS NOT THE MODEL FEATURE: it
    carries the 0.20 one-stop factor and covers one direction only."""
    qcx = onestop * (so + w_all * sa + w_int * si)
    qns = freq * elapsed_penalty(block, mn)
    return qns / (qns + qcx) if (qns + qcx) else 0.0


def capa_from_components(comp, block, freq):
    """THE MODEL'S capa FEATURE. The mean of the two directions, exactly as bt2_capture writes
    cap_actual: statistics.mean of cap_from on (a to b) and on (b to a) at the actual frequency."""
    (so1, sa1, si1, mn1), (so2, sa2, si2, mn2) = comp
    return statistics.mean([cap_from(so1, sa1, si1, mn1, block, freq),
                            cap_from(so2, sa2, si2, mn2, block, freq)])


def qcx_feature_from_components(comp):
    """THE MODEL'S qcx FEATURE, bt2_lib line 60. BOTH directions summed, and NO one-stop factor.
    Different from the qcx inside cap_from, which is why it is built here and not derived."""
    (so1, sa1, si1, _m1), (so2, sa2, si2, _m2) = comp
    return (so1 + W_ALLIANCE * sa1 + W_INTERLINE * si1
            + so2 + W_ALLIANCE * sa2 + W_INTERLINE * si2)


def load_mct(default_mct=90):
    """The minimum connect time master, and WHERE IT CAME FROM, returned together.

    THE DEFAULT IS OFF, AND THAT IS NOT AN OVERSIGHT. It is what the training capture was built
    with, and the live path has to reproduce training or the published accuracy stops describing
    the number a client is shown.

    MEASURED, 12 August 2026, on forty routes of cohort 2018 against capture_2018.csv:

        no master   thirty-nine of forty routes agree to the file's own write precision. Median
                    ratio of live over training 1.0000, upper quartile 1.0000, maximum 1.0011.
        master on   twenty routes stop agreeing and every one of them reads HIGH. Median 1.0549,
                    upper quartile 1.3637, maximum 1.8379. MXP-TXL online rises by a factor of
                    1.41, MDW-PWM by 1.78, DUS-LJU alliance by 1.54, in every case with the
                    minimum elapsed time unchanged, so the same candidates are found and more of
                    them survive.

    So capa, the model's third feature and one the published 92% and 86% are fitted on, was computed
    with the 90 minute default at every airport. That is a real property of the training data and it
    was not written down anywhere before today. The master itself is not in question: E:\\Avia and
    C:\\Avia hold byte-identical copies, md5 2d7e8a27f2f167b4992345b1f4fde299.

    I FIRST CONCLUDED THE OPPOSITE AND IT IS WITHDRAWN. I read NNG-YTY, where the live path read
    0.38 of training, as the master being absent live. It is not: that route returns 0.3822 with the
    master and 0.3822 without it, unchanged to four decimals. Reasoning from a mechanism ahead of
    measuring it, which is the pattern this programme keeps paying for.

    TO TURN IT ON, which is a real improvement to the input and a departure from what was measured:

        AVIA_BT2_MCT=1     both chains load the master

    Setting it means the training cohorts must be rebuilt with it and the model re-measured before
    any accuracy figure is quoted against a forecast that used it.
    """
    import os
    import connection_builder as CB
    if os.environ.get("AVIA_BT2_MCT", "").strip().lower() not in ("1", "true", "on"):
        return {}, ("OFF by default, which is the state capture_L.csv was built in. Set "
                    "AVIA_BT2_MCT=1 to load the master, and rebuild the cohorts if you do.")
    cands = []
    env = os.environ.get("AVIA_MCT_MASTER")
    if env:
        cands.append(env)
    try:
        from config import MCT_MASTER
        cands.append(str(MCT_MASTER))
    except Exception:                                       # noqa: BLE001
        pass
    for root in (os.environ.get("AVIA_LOCAL_CACHE"),
                 os.path.join("E:" + os.sep, "Avia"), os.path.join("C:" + os.sep, "Avia")):
        if root:
            cands.append(os.path.join(root, "MCT Master List.xlsx"))
    tried = []
    for c in cands:
        if not c:
            continue
        tried.append(c)
        if not os.path.isfile(c):
            continue
        try:
            mct = CB.load_mct_data(c, default_mct)
        except Exception as exc:                            # noqa: BLE001
            return {}, "found %s but could not read it: %s" % (c, exc)
        if mct:
            return mct, c
        return {}, "read %s and it produced no minimum connect times" % c
    return {}, ("no MCT master found. Looked in: %s. Set AVIA_MCT_MASTER."
                % ", ".join(tried) if tried else "no candidate paths")


def block_minutes(gcd_km):
    """The block time bt2_capture assumes for the proposed nonstop, int(km / 13.5) + 30. It is the
    reference the elapsed penalty is measured against, so it must match training rather than the
    engine's own block_min, which is computed from nautical miles on a different curve."""
    return int(float(gcd_km) / 13.5) + 30
