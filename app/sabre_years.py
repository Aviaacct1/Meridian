#!/usr/bin/env python3
"""
Avia Solutions - what a Sabre source_year actually contains.
============================================================
MEASURED on the store, 15 August 2026, by grouping source_year against year:

    source_year   year rows                       note
    2013-2019     the same year                   clean
    2020          DOES NOT EXIST                  a request returns nothing, in silence
    2021          2020: 14,197,338                53.5% of the vintage is COVID-year travel
                  2021: 12,316,299
    2022-2025     the same year                   clean

Every other vintage carries one travel year under its own label. The 2021 file carries
two, and the 2020 file was never loaded, so `WHERE source_year = 2021` returns a blend
that is mostly the COVID year and `WHERE source_year = 2020` returns an empty market
rather than an error.

EXPOSURE TODAY IS NIL, checked before this was written rather than assumed: the engine
takes max(source_year), which is 2025; the BT2 cohorts are 2016, 2017, 2018, 2019, 2024
and 2025; backtest.py excludes 2020-2023 from the clean sample; and airport_profile.py
line 69 names 2020-2022 absent and never to be interpolated. This exists so the trap
cannot be walked into later, not because something walked into it.

THE REAL FIX, when somebody wants those years, is to filter on `year` rather than
`source_year`. The two are identical in every vintage but 2021, so the change is safe
to verify one year at a time, and it makes 2020 reachable for the first time. It is not
made here: source_year appears 106 times across 47 files and changing it wholesale would
move any figure previously fitted on the blend without saying so.
"""

# source_year values whose contents do not match their label.
MIXED = {2021: "holds 2020 and 2021 travel, 53.5% of it 2020"}
ABSENT = {2020: "never loaded; a request returns an empty market, not an error"}


def check(year):
    """A note naming what a source_year really contains, or None when it is clean.

    Never raises and never changes a figure. A caller that wants to refuse can act on
    the note; a caller that wants to proceed carries it, which is the difference between
    a stated basis and a silent one.
    """
    if year is None:
        return None
    try:
        y = int(year)
    except (TypeError, ValueError):
        return None
    if y in ABSENT:
        return f"Sabre source_year {y}: {ABSENT[y]}"
    if y in MIXED:
        return f"Sabre source_year {y}: {MIXED[y]}"
    return None


if __name__ == "__main__":
    for y in (2019, 2020, 2021, 2024, 2025):
        print(f"  {y}: {check(y) or 'clean'}")
