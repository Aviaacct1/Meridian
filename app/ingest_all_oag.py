#!/usr/bin/env python3
"""
Avia Solutions - bulk OAG ingest.
=================================
Loads every OAG region file in a folder into C:\\Avia\\oag.duckdb, inferring week
and region from the filename, skipping the Hub Airports file and any (week, region)
already loaded. Continue-on-error. Run it again whenever Jess adds more weeks.

  py -3.12 ingest_all_oag.py
  py -3.12 ingest_all_oag.py "<folder>" "<db>"
"""
import os, sys, glob, datetime
import oag_ingest as OI

def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else r"Z:\Shared\Company Data\18 Products\QSI\Data Store"
    db = sys.argv[2] if len(sys.argv) > 2 else r"C:\Avia\oag.duckdb"
    # enumerate with os.listdir, not glob: on the Egnyte virtual drive glob returns nothing
    # where listdir works fine (confirmed 29 Jun 2026).
    try:
        names = os.listdir(folder)
    except (FileNotFoundError, NotADirectoryError, OSError) as e:
        print(f"Cannot read folder {folder}: {e}"); return
    files = sorted(os.path.join(folder, n) for n in names
                   if n.lower().endswith((".xlsx", ".xls", ".xlsm")) and not n.startswith("~$"))
    if not files:
        print(f"No .xlsx files found in {folder} ({len(names)} entries seen)"); return
    print(f"{len(files)} schedule files found in {folder}")

    done = set()
    if os.path.exists(db):
        import duckdb
        con = duckdb.connect(db, read_only=True)
        try:
            done = {(w, r) for w, r in con.execute("SELECT DISTINCT week, region FROM oag").fetchall()}
        except Exception:
            pass
        con.close()

    t0 = datetime.datetime.now()
    for f in files:
        b = os.path.basename(f)
        if b.lower().startswith("hub airports"):
            print(f"skip (not a region file): {b}"); continue
        wk, rg = OI.infer(f)
        if not wk or not rg:
            print(f"SKIP (cannot infer week/region): {b}"); continue
        if (wk, rg) in done:
            print(f"skip (already loaded): {rg} {wk}"); continue
        try:
            t = datetime.datetime.now()
            n, tot = OI.ingest_one(f, wk, rg, db)
            print(f"loaded {rg} {wk}: {n:,} flights ({(datetime.datetime.now()-t).total_seconds():.0f}s); store now {tot:,}", flush=True)
            done.add((wk, rg))
        except Exception as e:
            print(f"FAILED {b}: {str(e).splitlines()[0][:140]}", flush=True)
    print(f"ALL DONE in {(datetime.datetime.now()-t0).total_seconds()/60:.1f} min. Loaded weeks/regions: {len(done)}")

if __name__ == "__main__":
    main()
