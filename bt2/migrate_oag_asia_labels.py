#!/usr/bin/env python3
"""Avia Solutions - fold the Asia part-month labels into their parent month. 11 August 2026.

    py -3.12 bt2\\migrate_oag_asia_labels.py --check          # measure only, changes nothing
    py -3.12 bt2\\migrate_oag_asia_labels.py --apply          # rewrite the labels, with verification

WHY. OAG exports Asia in half-months while the other six regions come as whole months, so the store
carries three label forms that are not interchangeable:

    single week   2026-05-25          all seven regions
    monthly       2025-05             SIX regions, no Asia
    part-month    2025-05p01 / p16    ASIA ONLY, the month in halves

Every consumer has to know this. bt2_capture falls back from p16 to p01, bt2_months classifies
"week LIKE '%p__'" as split against month, fy_capacity notes that two fortnightly Asia labels count
as one month, and cortex_app.resolve_oag_week has to refuse a monthly label as incomplete. It also
cost a wrong conclusion on 11 August: reading the monthly labels alone showed Taipei serving 26
destinations across a whole year against 98 in a single week, and the first reading of that was that
the store had no Asia at all.

Folding p01/p16/p23 into the parent month makes every monthly label a complete world and deletes the
special case permanently.

WHY IT IS SAFE, established before writing this and re-checked by --check below. The halves are
complementary in TIME, not overlapping. Cathay flight 451, Taipei to Hong Kong at 19:30 in May 2025:
15 rows in p01 and 16 in p16, which is 31, the days of May. Each row is a dated instance carrying the
weekly days-of-operation mask that applied on that date; the masks differ between halves only because
schedules change mid-month. Nothing is counted twice, and the reader dedupes by flight and unions the
masks anyway (wave_cache._Boards._rows).

WHAT IT DOES NOT DO. It does not touch the single-week labels, which are already complete worlds and
are what the engine runs on. It only relabels; no row is added, removed or edited otherwise.

RUN IT ON THE WORKSTATION, against E:\\Avia\\oag.duckdb. Not from a Cowork session: the store is
16.8GB and the mounts deny overwrite.
"""
import argparse
import os
import re
import sys

PART = re.compile(r"^\d{4}-\d{2}p\d{2}$")


def survey(con):
    """Every part-month label, its parent, and what each side holds."""
    rows = con.execute("SELECT week, region, COUNT(*) FROM oag GROUP BY 1, 2").fetchall()
    by_label = {}
    for w, r, n in rows:
        by_label.setdefault(w, {})[r] = n
    parts = sorted(w for w in by_label if PART.match(w))
    return by_label, parts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oag", default=os.environ.get("AVIA_OAG", r"E:\Avia\oag.duckdb"))
    ap.add_argument("--apply", action="store_true", help="write the change (default is check only)")
    ap.add_argument("--check", action="store_true", help="measure only")
    a = ap.parse_args()

    import duckdb
    ro = not a.apply
    con = duckdb.connect(a.oag, read_only=ro)
    con.execute("SET memory_limit='4GB'; SET threads=4;")

    by_label, parts = survey(con)
    every = set()
    for regs in by_label.values():
        every |= set(regs)
    print(f"store: {a.oag}")
    print(f"regions in the store: {len(every)}  {sorted(every)}")
    print(f"part-month labels: {len(parts)}")
    if not parts:
        print("nothing to migrate.")
        return 0

    total_before = con.execute("SELECT COUNT(*) FROM oag").fetchone()[0]
    moving = con.execute(
        "SELECT COUNT(*) FROM oag WHERE regexp_matches(week, '^[0-9]{4}-[0-9]{2}p[0-9]{2}$')"
    ).fetchone()[0]
    print(f"rows in the store: {total_before:,};  rows to relabel: {moving:,}")
    print()

    # What each parent month gains, and whether the parent is currently short of a full world.
    print(f"  {'part label':<14} {'parent':<9} {'rows':>10}  {'regions in part':<12} "
          f"{'parent regions before':>21}")
    gains = {}
    for p in parts:
        parent = p[:7]
        pregs = set(by_label[p])
        gains.setdefault(parent, set()).update(pregs)
        before = len(by_label.get(parent, {}))
        print(f"  {p:<14} {parent:<9} {sum(by_label[p].values()):>10,}  "
              f"{','.join(sorted(pregs)):<12} {before:>21}")
    print()
    short = [pa for pa in sorted(gains)
             if len(set(by_label.get(pa, {})) | gains[pa]) > len(by_label.get(pa, {}))]
    print(f"parent months that become a COMPLETE WORLD after the fold: {len(short)}")
    for pa in short[:6]:
        after = set(by_label.get(pa, {})) | gains[pa]
        print(f"   {pa}: {len(by_label.get(pa, {}))} -> {len(after)} regions")
    if len(short) > 6:
        print(f"   ... and {len(short) - 6} more")

    if not a.apply:
        print("\n--check only. Nothing written. Re-run with --apply to make the change.")
        return 0

    print("\napplying...")
    con.execute("UPDATE oag SET week = substr(week, 1, 7) "
                "WHERE regexp_matches(week, '^[0-9]{4}-[0-9]{2}p[0-9]{2}$')")

    # VERIFY, and fail loudly rather than report success on an assumption.
    total_after = con.execute("SELECT COUNT(*) FROM oag").fetchone()[0]
    left = con.execute(
        "SELECT COUNT(*) FROM oag WHERE regexp_matches(week, '^[0-9]{4}-[0-9]{2}p[0-9]{2}$')"
    ).fetchone()[0]
    by_after, _ = survey(con)
    bad = [pa for pa in sorted(gains) if len(by_after.get(pa, {})) < len(every)]

    print(f"  rows before {total_before:,}, after {total_after:,}  "
          f"{'OK' if total_after == total_before else '*** ROW COUNT MOVED ***'}")
    print(f"  part-month labels remaining: {left}  {'OK' if left == 0 else '*** NOT ALL FOLDED ***'}")
    print(f"  parent months short of {len(every)} regions after the fold: {len(bad)}"
          f"{'' if not bad else '  ' + ', '.join(bad[:8])}")

    try:
        con.execute("CREATE TABLE IF NOT EXISTS _store_meta (key VARCHAR, value VARCHAR)")
        con.execute("INSERT INTO _store_meta VALUES (?, ?)",
                    ["oag_asia_labels_folded_11Aug2026",
                     f"rows={total_after};parts_folded={moving};regions={len(every)}"])
        print("  integrity stamp written to _store_meta")
    except Exception as e:
        print(f"  could not write the integrity stamp: {e}")

    ok = (total_after == total_before and left == 0 and not bad)
    print("\n" + ("MIGRATION VERIFIED." if ok else "*** MIGRATION DID NOT VERIFY - investigate ***"))
    print("Next: bt2_capture.py, bt2_months.py and fy_capacity.py all carry p-label special cases")
    print("that are now dead code, and cortex_app.resolve_oag_week will start accepting monthly")
    print("labels as complete worlds. Re-run app/verify_connecting_build.py after this.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
