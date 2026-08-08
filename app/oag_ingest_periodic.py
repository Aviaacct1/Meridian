#!/usr/bin/env python3
r"""
Avia Solutions - OAG schedules ingest (period-aware).
=====================================================
Extends oag_ingest.py to load the full-schedule pulls Jess downloads from OAG,
which are named by PERIOD rather than by a week-commencing date:

    Asia Jan 2015.xlsx        -> period 2015-01  (monthly)
    Middle East H1 2015.xlsx  -> period 2015-H1  (half-year)
    North America 2015.xlsx   -> period 2015     (whole year, one file)

The original ingest_all_oag.py infers (week, region) from a "wc 27May19" token and
SKIPS every one of the names above (proved: 0 of 31 for the 2015 pull). This driver
adds monthly / half-year / quarter / annual inference, stamps a DISTINCT period key
per file so the twelve monthly Asia files do not overwrite one another, and reuses
oag_ingest.ingest_one and its COLMAP UNCHANGED - so the 45-column layout and the
DuckDB store schema are identical to the existing weekly data. Old weekly names are
still inferred (backward compatible), so a mixed folder loads in one pass.

  py -3.12 oag_ingest_periodic.py                 # default Egnyte folder + C:\Avia\oag.duckdb
  py -3.12 oag_ingest_periodic.py "<folder>" "<db>"
  py -3.12 oag_ingest_periodic.py --dry           # infer only, load nothing (safe preflight)

Author: Avia Solutions.
"""
import os, sys, re, datetime, argparse
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # always run from this script's own folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # sibling imports work from any cwd
import oag_ingest as OI            # reuse COLMAP, REGIONS, MONTHS, infer (weekly), ingest_one


def infer_period(fname):
    """Return (period_key, region, grain) for a schedules file, or (None, region, None).

    Tries, in order: existing weekly 'wc' date (backward compatible) -> monthly
    'Mon YYYY' -> half-year 'H1/H2 YYYY' -> quarter 'Q1..Q4 YYYY' -> whole-year 'YYYY'.
    period_key always starts YYYY so oag_ingest.ingest_one derives the year correctly.
    """
    base = os.path.basename(fname)
    region = next((r for r in OI.REGIONS if r.lower() in base.lower()), None)

    # 1) existing weekly style ('Europe wc 27May19.xlsx') - behaviour unchanged
    wk, rg = OI.infer(base)
    if wk:
        return wk, (rg or region), "week"

    # 2) monthly: a 3-letter month token followed by a 4-digit year ('Jan 2015')
    m = re.search(r'\b([A-Za-z]{3})[a-z]*\s+(20\d{2})\b', base)
    if m and m.group(1).lower() in OI.MONTHS:
        return f"{m.group(2)}-{OI.MONTHS[m.group(1).lower()]:02d}", region, "month"

    # 3) half-year ('H1 2015', 'H2-2015')
    m = re.search(r'\bH([12])\D{0,3}(20\d{2})\b', base, re.I)
    if m:
        return f"{m.group(2)}-H{m.group(1)}", region, "half"

    # 4) quarter ('Q3 2015')
    m = re.search(r'\bQ([1-4])\D{0,3}(20\d{2})\b', base, re.I)
    if m:
        return f"{m.group(2)}-Q{m.group(1)}", region, "quarter"

    # 5) whole year - a bare 4-digit year and nothing more granular ('North America 2015')
    m = re.search(r'\b(20\d{2})\b', base)
    if m:
        return m.group(1), region, "year"

    return None, region, None


def _read_fast(xlsx):
    """Read the first sheet with python_calamine DIRECTLY and return a nullable-string
    DataFrame of just the mapped columns. Skips pandas' read_excel type-inference path
    (sanitize_objects), which is the slow, memory-heavy step on 200MB+ sheets."""
    import python_calamine, pandas as pd
    rows = python_calamine.CalamineWorkbook.from_path(xlsx).get_sheet_by_index(0).to_python(skip_empty_area=True)
    if not rows:
        return pd.DataFrame(columns=list(OI.COLMAP)), 0
    header = [str(c).strip() for c in rows[0]]
    raw = pd.DataFrame(rows[1:], columns=header)         # C-speed build, no NA sanitiser
    clean = pd.DataFrame()
    for tgt, srcs in OI.COLMAP.items():
        src = next((s for s in srcs if s in raw.columns), None)
        if src is None:
            clean[tgt] = pd.array([pd.NA] * len(raw), dtype="string")
            continue
        col = raw[src]
        # Excel holds numbers as floats, so seats/flight_no/days_of_op arrive as 96.0,
        # 267.0, 1234567.0. Render every integer-valued CELL as a clean int string so
        # flight keys match the existing weekly rows ("267" not "267.0") and day-pattern
        # parsing works. Leave dates, genuine text (alphanumeric flight nos) and true
        # decimals untouched. Handles mixed/object columns, not just pure-float ones.
        if pd.api.types.is_datetime64_any_dtype(col):
            clean[tgt] = col.astype("string"); continue
        num = pd.to_numeric(col, errors="coerce")
        is_int = num.notna() & (num % 1 == 0)
        out = col.astype("string")
        if bool(is_int.any()):
            out = out.mask(is_int, num.where(is_int).astype("Int64").astype("string"))
        clean[tgt] = out
    return clean, len(raw)


def ingest_one_fast(xlsx, period, region, db):
    """Same store write as oag_ingest.ingest_one, but via _read_fast. Idempotent on
    (period, region); COLMAP and the 45-column layout are unchanged."""
    import duckdb
    year = int(period[:4])
    clean, _ = _read_fast(xlsx)
    clean["week"] = period; clean["region"] = region; clean["year"] = year
    clean["source_file"] = os.path.basename(xlsx)
    clean = clean[OI.COLS]
    con = duckdb.connect(db)
    con.register("clean", clean)
    con.execute("CREATE TABLE IF NOT EXISTS oag AS SELECT * FROM clean WHERE 0=1")
    con.execute("DELETE FROM oag WHERE week=? AND region=?", [period, region])
    con.execute("INSERT INTO oag SELECT * FROM clean")
    n = con.execute("SELECT count(*) FROM oag WHERE week=? AND region=?", [period, region]).fetchone()[0]
    tot = con.execute("SELECT count(*) FROM oag").fetchone()[0]
    con.close()
    return n, tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?", default=r"Z:\Shared\Company Data\18 Products\QSI\Data Store")
    ap.add_argument("db", nargs="?", default=r"C:\Avia\oag.duckdb")
    ap.add_argument("--dry", action="store_true", help="infer and report only; load nothing")
    ap.add_argument("--only", help="load only files whose name contains this text (e.g. \"Africa H1\")")
    ap.add_argument("--force", action="store_true", help="re-ingest and overwrite periods already in the store")
    a = ap.parse_args()

    try:
        names = os.listdir(a.folder)          # listdir, not glob (Egnyte virtual drive)
    except OSError as e:
        print(f"Cannot read folder {a.folder}: {e}"); return
    files = sorted(os.path.join(a.folder, n) for n in names
                   if n.lower().endswith((".xlsx", ".xls", ".xlsm")) and not n.startswith("~$"))
    if not files:
        print(f"No schedule files in {a.folder} ({len(names)} entries seen)"); return
    print(f"{len(files)} schedule files in {a.folder}\n")

    done = set()
    if os.path.exists(a.db) and not a.dry:
        import duckdb
        con = duckdb.connect(a.db, read_only=True)
        try:
            done = {(w, r) for w, r in con.execute("SELECT DISTINCT week, region FROM oag").fetchall()}
        except Exception:
            pass
        con.close()

    plan, skips = [], []
    for f in files:
        b = os.path.basename(f)
        if b.lower().startswith("hub airports"):
            print(f"skip (not a region file): {b}"); continue
        pk, rg, grain = infer_period(f)
        if not pk or not rg:
            skips.append(b); print(f"SKIP  cannot infer  {b}"); continue
        plan.append((f, pk, rg, grain))

    if a.only:
        plan = [t for t in plan if a.only.lower() in os.path.basename(t[0]).lower()]
        print(f"--only {a.only!r}: {len(plan)} file(s) selected")
    print(f"\n{len(plan)} files resolved, {len(skips)} unresolved.")
    seen = {}
    for f, pk, rg, grain in plan:
        seen.setdefault((pk, rg), []).append(os.path.basename(f))
    clashes = {k: v for k, v in seen.items() if len(v) > 1}
    if clashes:
        print("WARNING - these files share a (period, region) key and would overwrite each other:")
        for k, v in clashes.items():
            print(f"   {k}: {v}")

    if a.dry:
        for f, pk, rg, grain in plan:
            print(f"  would load  period={pk:8} region={rg:15} grain={grain:7} <- {os.path.basename(f)}")
        print(f"\nDRY RUN. {len(plan)} files would load into {len(seen)} (period, region) slots.")
        return

    t0 = datetime.datetime.now()
    for f, pk, rg, grain in plan:
        if (pk, rg) in done and not a.force:
            print(f"skip (already loaded; use --force to overwrite): {rg} {pk}"); continue
        try:
            t = datetime.datetime.now()
            print(f"reading {os.path.basename(f)} ({os.path.getsize(f)/1e6:.0f}MB)...", flush=True)
            n, tot = ingest_one_fast(f, pk, rg, a.db)   # fast calamine read; COLMAP unchanged
            print(f"loaded {rg} {pk} [{grain}]: {n:,} flights "
                  f"({(datetime.datetime.now()-t).total_seconds():.0f}s); store now {tot:,}", flush=True)
            done.add((pk, rg))
        except Exception as e:
            print(f"FAILED {os.path.basename(f)}: {str(e).splitlines()[0][:140]}", flush=True)
    print(f"ALL DONE in {(datetime.datetime.now()-t0).total_seconds()/60:.1f} min. "
          f"Slots loaded this run: {len(plan)}")


if __name__ == "__main__":
    main()
