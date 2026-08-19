#!/usr/bin/env python3
r"""Airport-level series for the deck.

SEATS ARE NOT PASSENGERS, and this module will not let the deck pretend they
are. John, 7 August: "OAG gives schedules." So everything read from OAG here is
CAPACITY, named `seats`, carried with the unit "seats" and attributed to OAG.
Traffic is a different measurement from a different source:

    US airports        US DOT. T-100 for onboard passengers at an airport,
                       DB1B for origin and destination. The audience validates
                       against these and they are free and public.
    everywhere else    Sabre, as origin and destination.

`od_source.py` already makes exactly this choice for the engine and returns the
source label with the number; the same pattern is used below, because a figure
whose source is not attached to it cannot go on an Avia page.

ONBOARD AND ORIGIN-DESTINATION ARE ALSO NOT THE SAME THING. A passenger
connecting at an airport is onboard twice and in the origin and destination
count nowhere. The two are never added and never plotted on one axis.

THE SABRE LICENCE, John 7 August: a calculation on the data is fine, showing the
raw data is not. Every Sabre figure that reaches a deck is therefore an
aggregate, and no row-level extract is ever rendered. A fare series is an INDEX,
rebased, never a published fare.

John, 7 August 2026: the generated deck had no charts in ten research sections.
I said there was nothing to chart, having looked only at the research findings,
which are single sourced points and always will be. That was the wrong place to
look. The charts come from the stores.

WHAT THIS WILL AND WILL NOT CLAIM
---------------------------------
The obvious chart is ten years of passengers at the airport. The store cannot
honestly give it, and the validation note of 24 July says why:

  * 2020 to 2022 are ABSENT. COVID, and never to be interpolated.
  * North America has no monthly labels before 2019, so a US airport has no
    full-year capacity for 2015 to 2018 at all.
  * 2019 is partial in most regions, and coverage varies region by region.

So this module never draws a ten-year line. It reports the years the store
actually holds FOR THIS AIRPORT, and the caller shows the gaps as gaps. That is
the house rule: flag missing years, do not skip past them, and never fill.

It also reads through the same conventions fy_capacity.py established, because
they are the ones that are right:

  * MONTHLY labels only, never mixed with annual, half-year or weekly rows for
    the same year, or the same flights are counted several times over.
  * service_type = 'J', the scheduled passenger filter.
  * seats_total already equals seats x frequency, so it is summed and never
    multiplied by frequency again.
  * The pull is directional, so a two-way total is the sum of both directions.

THE SCHEMA IS PROBED, NOT ASSUMED. Coverage is heterogeneous and columns differ
between pulls, so every query checks the columns it needs exist first and
reports what it could not compute rather than returning a confident zero.

Nothing here is cached and nothing is written. Read only, on the workstation.

Avia Solutions Limited. All rights reserved.
"""

import os

MONTH_RE = "regexp_full_match(week,'[0-9]{4}-[0-9]{2}')"
PAX = "service_type = 'J'"
COVID_YEARS = (2020, 2021, 2022)

# What each series IS, carried with it, because the deck has to label the axis
# and the two are different measurements that must never share one.
SEATS_UNIT = "Seats, departing, each way"
SEATS_SOURCE = "OAG schedules"
ONBOARD_UNIT = "Passengers onboard, both directions"
OD_UNIT = "Passengers, origin and destination, each way"
DOT_T100 = "US DOT T-100 segment"
DOT_DB1B = "US DOT O&D Survey (DB1B)"
# The contractual name (audit R3): this label renders on the Watch page.
SABRE = "Sabre Global Demand Data, Meridian analysis"


ACI = "ACI airport traffic"
US_NAMES = ("US", "USA", "UNITED STATES")


def pax_source(country, aci_available=True):
    """Which traffic source this airport's audience will validate against.

    John's rule, 7 August: "for the US market we have established we have to use
    T-100 DOT data otherwise the US market won't take the product seriously, but
    elsewhere Sabre and ACI is fine." So the US is not a data preference, it is a
    credibility requirement, and it wins even where another source exists.

    Returns (kind, label, unit). `kind` is what the number MEASURES, and the
    caller has to respect it:

      "onboard"     passengers on the aircraft. T-100 and ACI. A load factor can
                    be computed against seats.
      "throughput"  ACI's total at an airport: arrivals PLUS departures PLUS
                    transit. Roughly twice a one-directional count, and it is
                    halved before it meets a departing-seats figure, explicitly
                    and never quietly.
      "od"          origin and destination. Sabre. NOT a load factor numerator.
    """
    if (country or "").strip().upper() in US_NAMES:
        return "dot", DOT_T100, ONBOARD_UNIT
    if aci_available:
        return "aci", ACI, "Passengers, total airport throughput"
    return "sabre", SABRE, OD_UNIT


def throughput_to_departing(series):
    """ACI throughput to a one-directional departing count.

    ACI publishes TOTAL passengers at an airport: arrivals plus departures plus
    transit. OAG seats here are departing and one-directional. Dividing one by
    the other without this step overstates the load factor by roughly two, which
    would put a 160% load factor on a client slide.

    Halving is an approximation and is labelled as one wherever it is used. It
    holds well at a point to point airport where arrivals and departures balance
    over a year, and less well where transit is large.
    """
    return [(y, v / 2.0) for y, v in (series or [])]


def _connect(db):
    import duckdb
    return duckdb.connect(db, read_only=True)


def columns(con, table="oag"):
    """What the store actually has. Queries are built against this, not hope."""
    try:
        return {r[1].lower() for r in con.execute("PRAGMA table_info('%s')" % table).fetchall()}
    except Exception:
        try:
            return {d[0].lower() for d in
                    con.execute("SELECT * FROM %s LIMIT 0" % table).description}
        except Exception:
            return set()


def years_available(con):
    """Years with MONTHLY coverage, and how many months each holds.

    The month count is returned with the year because a year holding four months
    is not a year, and a chart that plots it beside a twelve-month year without
    saying so is wrong. The caller decides the threshold; this only reports.
    """
    rows = con.execute(
        "SELECT CAST(SUBSTR(week,1,4) AS INTEGER) AS y, COUNT(DISTINCT week) AS m "
        "FROM oag WHERE %s AND %s GROUP BY 1 ORDER BY 1" % (MONTH_RE, PAX)).fetchall()
    return {int(y): int(m) for y, m in rows}


def airport_years(con, iata):
    """EVERY year this airport has monthly rows for, with its month count.

    Unfiltered on purpose. A year held with four months and a year not held at
    all are different facts and the caller has to be able to tell them apart:
    reporting a thin year as "absent" is the kind of quietly wrong message this
    codebase keeps having to fix.

    Coverage is per region as well as per year, so a global year list is not
    good enough either. North America has no monthly labels before 2019 while
    Europe has 2015 onwards, so the airport is asked directly.
    """
    rows = con.execute(
        "SELECT CAST(SUBSTR(week,1,4) AS INTEGER) AS y, COUNT(DISTINCT week) AS m "
        "FROM oag WHERE %s AND %s AND UPPER(TRIM(dep_airport)) = ? "
        "GROUP BY 1 ORDER BY 1" % (MONTH_RE, PAX), [iata.upper()]).fetchall()
    return [(int(y), int(m)) for y, m in rows]


def seats_by_year(con, iata, years):
    """Departing seats a year. seats_total is summed, never multiplied again."""
    if not years:
        return []
    ys = ",".join(str(int(y)) for y in years)
    rows = con.execute(
        "SELECT CAST(SUBSTR(week,1,4) AS INTEGER) AS y, "
        "       SUM(COALESCE(TRY_CAST(seats_total AS DOUBLE), 0.0)) AS seats "
        "FROM oag WHERE %s AND %s AND UPPER(TRIM(dep_airport)) = ? "
        "  AND CAST(SUBSTR(week,1,4) AS INTEGER) IN (%s) "
        "GROUP BY 1 ORDER BY 1" % (MONTH_RE, PAX, ys), [iata.upper()]).fetchall()
    return [(int(y), float(s or 0)) for y, s in rows]


def seats_by_year_and_haul(con, iata, years, home_country):
    """Departing seats a year, split domestic / same continent / long haul.

    The split is on the ARRIVAL country against the airport's own, which needs
    arr_country. Where the store lacks it the caller gets None and says so
    rather than being handed a two-way split that pretends to be three.
    """
    cols = columns(con)
    if "arr_country" not in cols or not home_country:
        return None
    ys = ",".join(str(int(y)) for y in years)
    rows = con.execute(
        "SELECT CAST(SUBSTR(week,1,4) AS INTEGER) AS y, "
        "       CASE WHEN UPPER(TRIM(arr_country)) = ? THEN 'Domestic' "
        "            ELSE 'International' END AS band, "
        "       SUM(COALESCE(TRY_CAST(seats_total AS DOUBLE), 0.0)) AS seats "
        "FROM oag WHERE %s AND %s AND UPPER(TRIM(dep_airport)) = ? "
        "  AND CAST(SUBSTR(week,1,4) AS INTEGER) IN (%s) "
        "GROUP BY 1,2 ORDER BY 1,2" % (MONTH_RE, PAX, ys),
        [home_country.upper(), iata.upper()]).fetchall()
    out = {}
    for y, band, s in rows:
        out.setdefault(int(y), {})[band] = float(s or 0)
    return out


def airlines(con, iata, year, limit=8):
    """Who flies from here, by seats, in one year. The competitive picture."""
    cols = columns(con)
    key = "carrier" if "carrier" in cols else ("airline" if "airline" in cols else None)
    if not key:
        return None
    rows = con.execute(
        "SELECT %s AS c, "
        "       SUM(COALESCE(TRY_CAST(seats_total AS DOUBLE), 0.0)) AS seats, "
        "       COUNT(DISTINCT arr_airport) AS routes "
        "FROM oag WHERE %s AND %s AND UPPER(TRIM(dep_airport)) = ? "
        "  AND CAST(SUBSTR(week,1,4) AS INTEGER) = ? "
        "GROUP BY 1 HAVING seats > 0 ORDER BY seats DESC LIMIT %d"
        % (key, MONTH_RE, PAX, int(limit)), [iata.upper(), int(year)]).fetchall()
    return [(str(c), float(s), int(r)) for c, s, r in rows if c]


def profile(db, iata, home_country=None, min_months=10):
    """Everything the deck can honestly say about this airport, plus the gaps.

    Returns {"ok", "iata", "years", "seats", "haul", "airlines", "latest",
             "notes"}. `notes` is never empty on a partial read: a series with a
    hole in it that does not say so is worse than no series.
    """
    out = {"ok": False, "iata": (iata or "").upper(), "years": [], "seats": [],
           "haul": None, "airlines": None, "latest": None, "notes": []}
    if not db or not os.path.exists(db):
        out["notes"].append("the OAG store is not at %s, so no airport series "
                            "could be read" % db)
        return out
    try:
        con = _connect(db)
    except Exception as e:
        out["notes"].append("could not open the OAG store (%s: %s)"
                            % (type(e).__name__, e))
        return out
    try:
        held = airport_years(con, out["iata"])            # everything, unfiltered
        usable = [(y, m) for y, m in held if m >= min_months]
        thin = [(y, m) for y, m in held if m < min_months]
        if not usable:
            out["notes"].append(
                "no year has %d or more months of monthly OAG coverage for %s%s. "
                "North America has no monthly labels before 2019 and 2020 to "
                "2022 are absent everywhere, so a thin airport can legitimately "
                "have nothing chartable."
                % (min_months, out["iata"],
                   "; the store does hold %s" % ", ".join(
                       "%d with %d months" % (y, m) for y, m in thin) if thin else ""))
            return out
        years = [y for y, _m in usable]
        out["years"] = usable
        out["latest"] = max(years)
        out["seats"] = seats_by_year(con, out["iata"], years)

        # The gaps, named, and the three kinds kept apart: a pandemic year, a
        # year the store simply does not hold, and a year it holds too little
        # of to plot. Calling the third "absent" would be untrue.
        span = range(min(years), max(years) + 1)
        thin_years = {y for y, _m in thin}
        missing = [y for y in span if y not in years and y not in thin_years]
        covid = [y for y in missing if y in COVID_YEARS]
        other = [y for y in missing if y not in COVID_YEARS]
        if covid:
            out["notes"].append("%s absent: the pandemic years are not in the "
                                "store and are never interpolated"
                                % ", ".join(str(y) for y in covid))
        if other:
            out["notes"].append("%s absent from the monthly store for this "
                                "airport" % ", ".join(str(y) for y in other))
        if thin:
            out["notes"].append(
                "held but too partial to plot, so left out rather than shown "
                "short: %s" % ", ".join("%d has %d months" % (y, m)
                                        for y, m in thin))
        partial = [(y, m) for y, m in usable if m < 12]
        if partial:
            out["notes"].append("part years included: %s" % ", ".join(
                "%d has %d months" % (y, m) for y, m in partial))

        out["haul"] = seats_by_year_and_haul(con, out["iata"], years, home_country)
        if out["haul"] is None:
            out["notes"].append("no domestic and international split: the store "
                                "has no arr_country column, or the airport's own "
                                "country was not supplied")
        out["airlines"] = airlines(con, out["iata"], out["latest"])
        if out["airlines"] is None:
            out["notes"].append("no airline breakdown: the store has neither a "
                                "carrier nor an airline column")
        out["ok"] = bool(out["seats"])
        return out
    except Exception as e:
        out["notes"].append("the airport profile query failed (%s: %s)"
                            % (type(e).__name__, e))
        return out
    finally:
        try:
            con.close()
        except Exception:
            pass


def pax_by_year(iata, country, years=None, stores=None):
    """Annual passengers at the airport, from the source its audience trusts.

    NEITHER READER IS WIRED YET, and this says so rather than pretending. As of
    7 August 2026 `config.py` registers `T100_DUCKDB` but no module in the tool
    queries it, and ACI is data Avia holds with no store registered at all. The
    contract is defined here so that ingesting either one makes the charts work
    without touching the deck: give this a table with an airport code, a year or
    a month, and a passenger count, and it will find it.

    stores  {"t100": path, "aci": path}, defaulting to config.py. Paths come
            from config or the environment and are never hardcoded.

    Returns {"series", "kind", "label", "unit", "notes"}.
    """
    out = {"series": [], "kind": None, "label": None, "unit": None, "notes": []}
    st = dict(stores or {})
    if not st:
        try:
            import config as CFG
            st = {"t100": str(getattr(CFG, "T100_DUCKDB", "")),
                  "aci": str(getattr(CFG, "ACI_DUCKDB", ""))}
        except Exception as e:
            out["notes"].append("config.py did not load (%s), so no store paths "
                                "are known" % e)
            return out

    us = (country or "").strip().upper() in US_NAMES
    order = [("dot", st.get("t100"), DOT_T100, ONBOARD_UNIT, "onboard")] if us else [
        ("aci", st.get("aci"), ACI, "Passengers, total airport throughput", "throughput")]
    for kind, path, label, unit, measures in order:
        if not path:
            out["notes"].append(
                "%s is the required source for this airport but no store path is "
                "registered%s" % (label, ". ACI_DUCKDB is not in config.py: the "
                                  "data exists but has never been ingested"
                                  if kind == "aci" else ""))
            continue
        if not os.path.exists(path):
            out["notes"].append("%s is the required source but its store is not "
                                "at %s" % (label, path))
            continue
        # Both stores are built and both schemas were inspected, so both are
        # read explicitly. `_read_pax` is kept only for a store that arrives in
        # a shape nobody has looked at yet.
        got, note = (read_aci(path, iata, years) if kind == "aci"
                     else read_t100(path, iata, years))
        if got:
            out.update({"series": got, "kind": measures, "label": label,
                        "unit": unit})
            if note:
                out["notes"].append(note)
            return out
        out["notes"].append("%s store opened but returned nothing for %s%s"
                            % (label, iata, ": " + note if note else ""))
    if us:
        out["notes"].append("US airports are graded on DOT and nothing else. "
                            "Sabre is not substituted here, because a US audience "
                            "checks the number against TranStats and a Sabre "
                            "figure it cannot reproduce costs more credibility "
                            "than a missing chart.")
    return out


def read_aci(path, iata, years=None, min_months=12):
    """The ACI series for one airport, read against the schema we built.

    `load_aci.py` fixed this store's shape on 7 August 2026, so it is queried
    directly rather than probed. Probing it is actively unsafe: `aci_monthly`
    has both an `airport` column and an `iata` column, and `airport` holds the
    NAME, so a probe that tries `airport` first matches on the wrong column,
    finds nothing for "EDI", and falls through to the `aci_coverage` view. That
    view sums every month present, so a year an airport reported eight months of
    arrives on the chart looking like a whole year that fell 30%.

    A YEAR IS ONLY A YEAR AT TWELVE MONTHS. Short years are excluded and named,
    which is the same rule the OAG reader applies. Across the store 80% of
    airport-years are complete, so this refuses more often than it might look,
    and refusing is the point.

    Returns (series, note).
    """
    try:
        con = _connect(path)
    except Exception as e:
        return [], "could not open the ACI store at %s (%s)" % (path, e)
    try:
        rows = con.execute(
            "SELECT year, COUNT(DISTINCT ym) AS months, SUM(passengers) AS pax "
            "FROM aci_monthly WHERE UPPER(TRIM(iata)) = ? "
            "GROUP BY 1 ORDER BY 1", [iata.upper()]).fetchall()
    except Exception as e:
        return [], "the ACI store did not answer as expected (%s: %s)" % (
            type(e).__name__, e)
    finally:
        try:
            con.close()
        except Exception:
            pass
    if not rows:
        return [], "%s is not in the ACI store" % iata.upper()
    whole = [(int(y), float(p or 0)) for y, m, p in rows if int(m) >= min_months]
    short = [(int(y), int(m)) for y, m, _p in rows if int(m) < min_months]
    if years:
        keep = set(years)
        whole = [(y, p) for y, p in whole if y in keep]
        short = [(y, m) for y, m in short if y in keep]
    note = ""
    if short:
        note = ("left out because the airport did not report every month: %s. "
                "A blank in ACI means no return was filed, not no traffic, so a "
                "short year is not plotted short." % ", ".join(
                    "%d reported %d months" % (y, m) for y, m in short))
    if not whole:
        return [], (note or "no complete year for %s in the ACI store"
                    % iata.upper())
    return whole, note


T100_TABLE = "seg"
T100_SCHEDULED = "F"


def read_t100(path, iata, years=None, min_months=12, service_class=T100_SCHEDULED):
    """Departing onboard passengers at a US airport, from DOT T-100 segment.

    Read explicitly against the store at `E:\\Avia\\Usmarket data\\t100.duckdb`,
    inspected 7 August 2026, and NOT probed. Two reasons.

    THE STORE HOLDS THE SAME DATA TWICE, IN TWO TABLES. `seg` is the parsed
    table, 3,821,033 rows with named columns. `t100` is the same 3,821,033 rows
    unparsed as column00 to column28. Anything that walks the table list can
    take either, and anything that sums both doubles the airport. Only `seg` is
    read here, by name.

    SCHEDULED SERVICE ONLY. T-100 segment carries scheduled and non-scheduled
    in one table under `class`. At Austin, class F is 99.8% of passengers, L
    (charter) is 0.2%, and G and P are cargo carrying none. OAG seats are
    scheduled, so including charter would inflate the load factor by whatever
    charter the airport happens to do. The share left out is reported, not
    silently dropped.

    T-100 counts passengers ON THE AIRCRAFT departing the airport, which is
    already one-directional. It is NOT halved the way ACI throughput is.

    Coverage runs 2015 to 2024. DOT publishes in arrears, so a US airport's
    series legitimately ends a year behind a non-US one.

    Returns (series, note).
    """
    try:
        con = _connect(path)
    except Exception as e:
        return [], "could not open the T-100 store at %s (%s)" % (path, e)
    try:
        tabs = {r[0].lower() for r in con.execute("SHOW TABLES").fetchall()}
        if T100_TABLE not in tabs:
            return [], ("the T-100 store has no %r table. Tables seen: %s. This "
                        "reader will not fall back to another one, because the "
                        "store also holds the same rows unparsed."
                        % (T100_TABLE, ", ".join(sorted(tabs)) or "none"))
        rows = con.execute(
            "SELECT year, COUNT(DISTINCT month) AS months, "
            "       SUM(TRY_CAST(passengers AS DOUBLE)) AS pax "
            "FROM %s WHERE UPPER(TRIM(origin)) = ? AND UPPER(TRIM(class)) = ? "
            "GROUP BY 1 ORDER BY 1" % T100_TABLE,
            [iata.upper(), service_class.upper()]).fetchall()
        other = con.execute(
            "SELECT SUM(TRY_CAST(passengers AS DOUBLE)) FROM %s "
            "WHERE UPPER(TRIM(origin)) = ? AND UPPER(TRIM(class)) <> ?"
            % T100_TABLE, [iata.upper(), service_class.upper()]).fetchone()
    except Exception as e:
        return [], "the T-100 store did not answer as expected (%s: %s)" % (
            type(e).__name__, e)
    finally:
        try:
            con.close()
        except Exception:
            pass
    if not rows:
        return [], "%s has no scheduled T-100 service in the store" % iata.upper()
    whole = [(int(y), float(p or 0)) for y, m, p in rows if int(m) >= min_months]
    short = [(int(y), int(m)) for y, m, _p in rows if int(m) < min_months]
    if years:
        keep = set(years)
        whole = [(y, p) for y, p in whole if y in keep]
        short = [(y, m) for y, m in short if y in keep]
    sched = sum(p for _y, p in whole) or 1.0
    note = ("scheduled service only (T-100 class %s); non-scheduled and cargo "
            "left out, %.1f%% of this airport's T-100 passengers"
            % (service_class, 100.0 * float(other[0] or 0)
               / (float(other[0] or 0) + sched)))
    if short:
        note += ("; left out as incomplete: %s" % ", ".join(
            "%d has %d months" % (y, m) for y, m in short))
    if not whole:
        return [], note
    return whole, note


def read_t100_monthly(path, iata, service_class=T100_SCHEDULED):
    """Departing onboard passengers by MONTH at a US airport, from DOT T-100 segment.

    read_t100's rules, unchanged (its docstring carries the evidence): the `seg` table
    BY NAME because the store holds the same rows twice and probing can take the
    unparsed copy; scheduled class only; `origin` because T-100 counts passengers on
    the aircraft departing, one-directional, never halved. The one difference is the
    grain: GROUP BY year AND month, for the Watch page's month-against-same-month
    chart. A missing month is absent from the result, not zero: DOT publishes in
    arrears and a blank is a not-yet-filed return.

    Returns (series, note) with series as [(year, month, pax)] ascending.
    """
    try:
        con = _connect(path)
    except Exception as e:
        return [], "could not open the T-100 store at %s (%s)" % (path, e)
    try:
        tabs = {r[0].lower() for r in con.execute("SHOW TABLES").fetchall()}
        if T100_TABLE not in tabs:
            return [], ("the T-100 store has no %r table. Tables seen: %s. This "
                        "reader will not fall back to another one, because the "
                        "store also holds the same rows unparsed."
                        % (T100_TABLE, ", ".join(sorted(tabs)) or "none"))
        rows = con.execute(
            "SELECT TRY_CAST(year AS INTEGER), TRY_CAST(month AS INTEGER), "
            "       SUM(TRY_CAST(passengers AS DOUBLE)) "
            "FROM %s WHERE UPPER(TRIM(origin)) = ? AND UPPER(TRIM(class)) = ? "
            "GROUP BY 1, 2 ORDER BY 1, 2" % T100_TABLE,
            [iata.upper(), service_class.upper()]).fetchall()
    except Exception as e:
        return [], "the T-100 store did not answer as expected (%s: %s)" % (
            type(e).__name__, e)
    finally:
        try:
            con.close()
        except Exception:
            pass
    series = [(int(y), int(m), float(p or 0)) for y, m, p in rows
              if y is not None and m is not None and 1 <= int(m) <= 12]
    if not series:
        return [], "%s has no scheduled T-100 service in the store" % iata.upper()
    note = ("scheduled service only (T-100 class %s); DOT publishes in arrears, so "
            "the series legitimately ends behind a non-US airport's" % service_class)
    return series, note


def read_aci_monthly(path, iata):
    """Two-way terminal passengers by MONTH from the ACI store, for one airport.

    Reads `aci_monthly` directly against the schema load_aci.py fixed on 7 August
    2026 (read_aci's docstring carries why probing this store is unsafe). ACI
    throughput is arrivals plus departures plus transit, TWO-WAY, the opposite basis
    to T-100; the caller labels it. A month the airport did not report is absent from
    the result, never zero: a blank in ACI is an unfiled return, not empty terminals.

    Returns (series, note) with series as [(year, month, pax)] ascending.
    """
    if not path or not os.path.exists(path):
        return [], "no ACI store at %s" % path
    try:
        con = _connect(path)
    except Exception as e:
        return [], "could not open the ACI store at %s (%s)" % (path, e)
    try:
        rows = con.execute(
            "SELECT TRY_CAST(year AS INTEGER), TRY_CAST(month AS INTEGER), "
            "       SUM(passengers) FROM aci_monthly "
            "WHERE UPPER(TRIM(iata)) = ? GROUP BY 1, 2 ORDER BY 1, 2",
            [iata.upper()]).fetchall()
    except Exception as e:
        return [], "the ACI store did not answer as expected (%s: %s)" % (
            type(e).__name__, e)
    finally:
        try:
            con.close()
        except Exception:
            pass
    series = [(int(y), int(m), float(p or 0)) for y, m, p in rows
              if y is not None and m is not None and 1 <= int(m) <= 12]
    if not series:
        return [], "%s is not in the ACI store" % iata.upper()
    return series, ("ACI monthly returns; a month the airport did not file is a gap "
                    "on the chart, not a zero")


def aci_country(path, iata):
    """The country ACI files this airport under, or "" if it is not in the store.

    Used so the deck does not have to be told a country before it can apply the
    rule that US airports are graded on DOT. The store carries country NAMES,
    and inconsistently: "United Kingdom" but "USA". `US_NAMES` already covers
    both spellings of the one that matters.
    """
    if not path or not os.path.exists(path):
        return ""
    try:
        con = _connect(path)
    except Exception:
        return ""
    try:
        row = con.execute("SELECT country FROM aci_monthly "
                          "WHERE UPPER(TRIM(iata)) = ? AND country <> '' LIMIT 1",
                          [iata.upper()]).fetchone()
        return (row[0] if row and row[0] else "")
    except Exception:
        return ""
    finally:
        try:
            con.close()
        except Exception:
            pass


def _read_pax(path, iata, years=None):
    """Find an airport passenger series in whatever shape the store arrived in.

    For T-100, which is not yet built, so its column names are not yet fixed.
    Rather than guess one and fail silently on another, the plausible names are
    tried in order and the one that resolves is used.

    THE CODE COLUMNS ARE TRIED BEFORE `airport`. In the ACI store `airport` is
    the airport's NAME, and a probe that reached for it first matched a column
    of names against a three-letter code and quietly returned nothing.
    """
    try:
        con = _connect(path)
    except Exception as e:
        return [], "could not open %s (%s)" % (path, e)
    try:
        tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
        for t in tables:
            cols = columns(con, t)
            apt = next((c for c in ("iata", "airport_code", "origin", "apt",
                                    "airport") if c in cols), None)
            pax = next((c for c in ("passengers", "pax", "total_passengers",
                                    "pax_total", "onboard") if c in cols), None)
            yr = next((c for c in ("year", "yr") if c in cols), None)
            mon = next((c for c in ("month", "period", "yyyymm") if c in cols), None)
            if not (apt and pax and (yr or mon)):
                continue
            ysel = yr if yr else "CAST(SUBSTR(CAST(%s AS VARCHAR),1,4) AS INTEGER)" % mon
            sql = ("SELECT %s AS y, SUM(TRY_CAST(%s AS DOUBLE)) AS p FROM %s "
                   "WHERE UPPER(TRIM(%s)) = ? GROUP BY 1 ORDER BY 1"
                   % (ysel, pax, t, apt))
            rows = con.execute(sql, [iata.upper()]).fetchall()
            rows = [(int(y), float(p or 0)) for y, p in rows if y and p]
            if years:
                rows = [(y, p) for y, p in rows if y in set(years)]
            if rows:
                return rows, "read from table %s (%s, %s)" % (t, apt, pax)
        return [], ("no table in %s has an airport code, a passenger count and a "
                    "year or month together. Tables seen: %s"
                    % (os.path.basename(path), ", ".join(tables) or "none"))
    except Exception as e:
        return [], "%s: %s" % (type(e).__name__, e)
    finally:
        try:
            con.close()
        except Exception:
            pass


def effective_load_factor(seats, pax, pax_kind):
    """Airport-level effective load factor: how full the aircraft leave.

    John's idea, 7 August, and a good chart for an airline: seats from OAG,
    passengers from the traffic source, the ratio year by year.

    IT ONLY WORKS WITH ONBOARD DATA, AND THIS REFUSES OTHERWISE. T-100 counts
    passengers ON THE AIRCRAFT, so T-100 over OAG seats is a load factor.
    Sabre and DB1B count ORIGIN AND DESTINATION, which is a different thing: a
    passenger connecting through the airport is onboard a departing aircraft and
    is not in the airport's origin and destination count at all. Dividing O&D by
    seats therefore produces a number that looks exactly like a load factor,
    reads far too low, and is wrong by however much the airport connects. On a
    slide in front of a network planner that is the kind of error that ends the
    meeting.

    Returns (series, note). The series is empty where it cannot be computed and
    the note says why, so the caller can print the reason instead of the chart.
    """
    note_unit = ""
    if pax_kind == "throughput":
        # ACI counts arrivals plus departures plus transit; the seats are
        # departing and one-directional. Halved here, explicitly, and the
        # approximation is carried into the caller's note rather than buried.
        pax = throughput_to_departing(pax)
        note_unit = ("airport throughput halved to a departing count so it "
                     "meets departing seats; an approximation that holds where "
                     "arrivals and departures balance over a year and less well "
                     "where transit is large. ")
    elif pax_kind != "onboard":
        return [], ("no airport load factor: the traffic source measures origin "
                    "and destination, not passengers onboard, and the ratio of "
                    "one to the other is not a load factor. It needs an onboard "
                    "or throughput source: US DOT T-100 for a US airport, ACI "
                    "elsewhere.")
    s, p = dict(seats or []), dict(pax or [])
    both = sorted(set(s) & set(p))
    if not both:
        return [], ("no airport load factor: the seats and the passengers do not "
                    "share a single year. Seats cover %s and passengers %s."
                    % (sorted(s) or "nothing", sorted(p) or "nothing"))
    out = [(y, p[y] / s[y]) for y in both if s.get(y)]
    skipped = [y for y in both if not s.get(y)]
    note = note_unit
    if skipped:
        note += ("%s left out of the load factor: no seats recorded"
                 % ", ".join(str(y) for y in skipped))
    # A load factor outside a plausible band means the two series are not
    # measuring the same thing, and saying so beats putting 160% on a slide.
    odd = [(y, v) for y, v in out if v > 1.05 or v < 0.20]
    if odd:
        note += (" CHECK THE UNITS: %s outside a plausible load factor, which "
                 "usually means the passenger count and the seat count are not "
                 "the same direction or the same basis."
                 % ", ".join("%d at %.0f%%" % (y, v * 100) for y, v in odd))
    return out, note.strip()


def cagr(series):
    """Compound annual growth across a series of (year, value).

    Computed across the ACTUAL span, and the span is returned with it, because
    a growth rate quoted without its period is not a number anybody can check.
    Returns (rate, first_year, last_year) or None where it cannot be computed.
    """
    pts = [(int(y), float(v)) for y, v in (series or []) if v and v > 0]
    if len(pts) < 2:
        return None
    pts.sort()
    (y0, v0), (y1, v1) = pts[0], pts[-1]
    n = y1 - y0
    if n <= 0:
        return None
    return ((v1 / v0) ** (1.0 / n) - 1.0, y0, y1)
