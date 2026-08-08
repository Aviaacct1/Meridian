#!/usr/bin/env python3
"""Move the reconciliation files between the two copies, one step at a time.

Companion to audit_split.py, and written for the same reason: hand-copying tool
files between locations is what created the split, and doing the copying by hand
again is how a second one starts. This carries an explicit manifest taken from the
audit of 6 August 2026, so every file that moves does so because it is named here.

Behaviour that matters:

  * DRY RUN BY DEFAULT. Nothing is written without --apply.
  * Every file it would overwrite is backed up first, under a timestamped folder,
    so any step can be undone.
  * The two secret files are hard-blocked. They can never be a source or a
    destination, whatever is asked for, because SITE is local and WORK is synced
    to OneDrive and a key that crosses that line is a key that has left the building.
  * cortex_app.py and research_provider.py are hard-blocked. Each side holds
    functions the other does not, so copying either way deletes working code. They
    are hand merges and the script will not pretend otherwise.
  * After copying, source and destination are compared byte for byte and the step
    fails loudly if they do not match.

    py -3.12 reconcile_split.py --site "C:\\AviaDev\\app" --work "...\\Avia QSI Tool\\app" --step 2
    py -3.12 reconcile_split.py --site ... --work ... --step 2 --apply

Run the steps in order, test the tool after each, and re-run audit_split.py to see
the list shorten.

Avia Solutions Limited. All rights reserved.
"""

import argparse
import hashlib
import os
import shutil
import sys
from datetime import datetime

# Never copied, in either direction, for any reason.
BLOCKED = {
    "anthropic_key.txt": "secret; SITE is local, WORK syncs to OneDrive",
    "access_password.txt": "secret; SITE is local, WORK syncs to OneDrive",
    # 7 Aug: the two copies are now byte-identical and a line-by-line comparison
    # found nothing held only on SITE, so the merge itself is complete. The block
    # stays anyway. This file carries the sign-in layer, the session handling and
    # the run metering, and the cost of a wrong wholesale copy is the site going
    # dark; the cost of patching it by hand is ten minutes. Retire the block only
    # when someone decides to, not because it happens to be identical today.
    "cortex_app.py": "hand merge: carries the sign-in, session and metering layer; "
                     "patch it, never copy it. Identical on both sides at 7 Aug 2026",
    "research_provider.py": "hand merge: SITE holds _load_api_key, WORK the finding-cap and caption work",
}

# Deliberately left where they are, and why. Printed so the decision is visible.
LEAVE = {
    "preagg.duckdb": "a data store; data lives on the workstation, not in the tree",
    "app_avia_style/": "the frozen rollback copy; not part of the live tool",
    # 7 Aug: appeared on WORK and briefly read as 48 files of drift. It is the
    # drive-time cache catchment_master.py writes, lat/lon to minutes, computed
    # and regenerable, and it belongs to whichever machine did the computing.
    # Copying it between copies would be copying a cache. Gitignore it too.
    "_dt_cache/": "a computed cache; regenerable, machine-local, never copied",
    "venv/": "a virtual environment inside the tool tree; 11,064 files, and the "
             "reason audit_split.py does not finish. Add it to that skip list",
}

# The manifest. step -> list of (relative path, direction). Direction is the side
# the file is taken FROM, and follows the audit: the side that holds the newer or
# only copy.
STEPS = {
    2: ("the engine correction that removes the neutral shims", [
        ("airport_capture.py", "site"),
    ]),
    3: ("the rest of the July engine work, plus the data and pages it depends on", [
        ("route_forecast.py", "site"),
        ("sabre_catchment.py", "site"),
        ("backtest.py", "site"),
        ("aircraft_economics.py", "site"),
        ("aircraft_select.py", "site"),
        ("route_deck.py", "site"),
        ("cortex_workbook.py", "site"),
        ("airport_attributes.json", "site"),
        ("airport_capture_factors.json", "site"),
        ("airport_catchment_geo.csv", "site"),
        ("bias_correction_model.joblib", "site"),
        ("bt_v2_6yr.csv", "site"),
        ("cortex_dashboard.html", "site"),
        ("cortex_catchment.html", "site"),
    ]),
    4: ("the track record fix: the evidence file and its reader move together", [
        ("master_backtest_scored.csv", "work"),
        ("track_record.py", "work"),
    ]),
    6: ("the dashboard pass: range advisory, banner placement, run caption, "
        "induced labelling and the help page, all written on the WORK side", [
        ("aircraft_select.py", "work"),
        ("cortex_dashboard.html", "work"),
        ("cortex_help.html", "work"),
        ("cortex_catchment.html", "work"),
    ]),
    7: ("modules the merged cortex_app imports that the working copy never had. "
        "Run missing_modules.py first and add anything else it names", [
        ("cortex_entry.py", "site"),
        ("bucket_correct.py", "site"),
        ("split_share.py", "site"),
    ]),
    5: ("the methodology proof card and the deck and research work", [
        ("methodology_page.py", "work"),
        ("pitch_verify.py", "work"),
        ("pitch_prose.py", "work"),
        ("pitch_report.py", "work"),
        ("city_pair_pptx_generator.py", "work"),
    ]),
    8: ("7 August, the visual layer and the schedule viability banner. Checked "
        "before adding: a line-by-line comparison of all four files found NOTHING "
        "held only on SITE, so each copy here is strictly additive. pitch_report "
        "on SITE had never received the 7 August --prose path either, so the site "
        "copy could not build a deck from hand-written section prose", [
        ("schedule_viability.py", "work"),      # NEW, the single implementation
        ("pitch_report.py", "work"),            # figure build, audit, --prose path
        ("cortex_dashboard.html", "work"),      # the viability banner
        # Found by the 7 August audit, not by today's work, and the more serious
        # of the two: SITE still asked the writing pass for 85 words with no
        # character cap, against WORK's 65 words under 430 characters. The whole
        # content budget is built on that 430, and the renderer's new prose
        # sizing is built on it too, so a deck written by the site copy would
        # have overflowed every prose slot on the page.
        ("pitch_prose.py", "work"),
    ]),
    9: ("the three model tables the WORK engine has been running without. "
        "bucket_correct.py, split_share.py and route_forecast.py are on both "
        "sides and all three load these by path; both loaders fall back to a "
        "neutral factor on any exception and say nothing, so on WORK the bucket "
        "correction and the hub-localness re-split have simply been off. Same "
        "shape as the airport_capture_factors.json failure of 6 August, and the "
        "reason both loaders now report", [
        ("bucket_model.json", "site"),
        ("hub_localness.json", "site"),
        ("region_localness.json", "site"),
        # and the two loaders, which now record the absence in LOAD_FAILURES and
        # print it once rather than returning a neutral factor in silence
        ("split_share.py", "work"),
        ("bucket_correct.py", "work"),
    ]),
    11: ("7 August, sizing the schedule from demand instead of taking --freq on "
         "trust. The frequency is a fixed point, because demand depends on the "
         "schedule quality that frequency sets, so it is solved by running the "
         "engine round the loop. Lives beside the engine, like schedule_viability, "
         "so the dashboard can use it next", [
        ("schedule_sizing.py", "work"),          # NEW
        ("test_schedule_sizing.py", "work"),     # NEW, 20 checks, no engine needed
        # the first live run found the case the loop cannot solve: an INDUCED
        # route floors demand at deployed capacity, so the load factor does not
        # move with frequency and the search walks to one flight a week. The
        # sizer now refuses and says why; the viability message now knows whether
        # the schedule was entered or sized, because a thin fill means different
        # things in the two cases.
        ("schedule_viability.py", "work"),
        ("pitch_report.py", "work"),
        # NOT listed here: forecast_spec.py, spec_from_research.py and
        # run_observatory_pitch.py also changed for the same finding, but they
        # live in Deck Generator/v4 and there is only ONE copy of that folder.
        # This reconciler covers app/ alone. If the site is ever to build decks
        # it needs AVIA_DECK_V4 pointing at the project's v4, because the
        # default resolves to C:\AviaDev\Deck Generator\v4, which does not exist.
    ]),
    12: ("7 August, airport-level series for the deck charts. Reads the OAG store "
         "through fy_capacity's conventions: MONTHLY labels only, service_type J, "
         "seats_total summed and never multiplied by frequency again. It refuses "
         "to draw a ten-year line the store cannot support and names the three "
         "kinds of gap separately: a pandemic year, a year not held, and a year "
         "held too thin to plot", [
        ("airport_profile.py", "work"),        # NEW
        ("test_airport_profile.py", "work"),   # NEW, 36 checks, builds its own store
        ("check_airport.py", "work"),          # NEW, what the stores hold per airport
        ("test_check_airport.py", "work"),     # NEW, 22 checks, builds all three stores
        ("check_t100.py", "work"),             # NEW, inspects the DOT store before use
        ("pitch_report.py", "work"),           # calls DF.build_airport for the charts
    ]),
    13: ("7 August, the ACI store. Turns the hand-maintained monthly workbook on "
         "Egnyte into aci.duckdb, so non-US airport traffic is queryable on the "
         "same footing as OAG and Sabre. Three variants exist in that folder, "
         "MONTH, YTD and YE, describing the same traffic three ways; only MONTH "
         "is loaded, for the same reason oag.duckdb is read at monthly labels "
         "only. A blank in the source means the airport did not report and is "
         "NEVER written as a zero", [
        ("load_aci.py", "work"),           # NEW, the loader
        ("test_load_aci.py", "work"),      # NEW, 40 checks, builds its own workbook
        ("check_aci.py", "work"),          # NEW, post-build verification, read-only
        ("config.py", "work"),             # ACI_DUCKDB registered
    ]),
    10: ("7 August, the environment check. Installing matplotlib and basemap into "
         "the global 3.12 downgraded numpy and could not delete the old copy, and "
         "pip reported that as a warning and exited zero. check_env.py is the "
         "thing that now notices. requirements.txt never listed the deck "
         "generator's packages, which is why they were installed by hand", [
        ("check_env.py", "work"),           # NEW
        ("requirements.txt", "work"),       # the deck generator's packages added
    ]),
    14: ("8 August, the fifteen modules held ONLY on WORK. Found by comparing the "
         "two trees file by file rather than checking the files a step names: 156 "
         "top-level .py files are common to both and 155 of those are byte-"
         "identical, but 28 exist on WORK alone and none of them is in git. "
         "Thirteen are July check scratch and are left where they are. These "
         "fifteen are not. The first eight are single-copy anywhere: the other "
         "seven also sit in a 24 June snapshot on Egnyte at 18 Products/QSI/"
         "Application, so they are recoverable, but that snapshot is six weeks "
         "stale and the estate index points at it as though it were the tool. "
         "Nothing here is imported by the live service, so this step adds no risk "
         "to a running forecast; it exists so that the first commit is the whole "
         "tool rather than the part of it that happened to be on the right side", [
        # single-copy anywhere: the OAG store's own maintenance tooling, and
        # yesterday's catchment work, which has a runbook in the project root
        ("catchment_master.py", "work"),
        ("oag_ingest_periodic.py", "work"),
        ("validate_oag_load.py", "work"),
        ("check_oag_grain.py", "work"),
        ("oag_drop_period.py", "work"),
        ("oag_sweep_mistags.py", "work"),
        ("scan_stores.py", "work"),
        ("build_od_fare.py", "work"),
        # also on Egnyte at 24 June: the previous pipeline and its dependents.
        # avia_qsi_auto_v3 reaches departure_time_grid.py, which holds the
        # specification and the reference numbers for the departure-time work
        # (129,162 at 21:30, circa 139,302 at 17:00 on BA LHR-SJC)
        ("avia_qsi_auto_v3.py", "work"),
        ("calibration_library_v8.py", "work"),
        ("commercial_reasonableness_engine.py", "work"),
        ("business_case_mode.py", "work"),
        ("cross_route_validator.py", "work"),
        ("cre_pce_bridge.py", "work"),
        ("closed_loop_pipeline_v2.py", "work"),
    ]),
    15: ("8 August, the ACI test suite going the other way. Step 13 moved "
         "test_load_aci.py from WORK to SITE and the two then diverged again: the "
         "WORK copy is 310 lines against SITE's 255 and was written 53 minutes "
         "later. The ten checks SITE lacks are the part-year refusal, the months-"
         "reported message, the throughput-not-onboard label, the ACI attribution, "
         "and the code-column match. Those guard three of the six defects that a "
         "green suite missed on 8 August, so SITE currently holds the weaker "
         "suite and it is the tree the migration was going to take", [
        ("test_load_aci.py", "work"),
    ]),
}

CHECK = {
    2: "Run a pitch. The neutral shim warning should be gone.",
    3: "Run a forecast for a route you know. Compare it against the site's answer.",
    4: "Restart the service and open /trackrecord. It should report 2,915 routes.",
    5: "Open /methodology. The proof card should be the first thing under the header.",
    7: ("Re-run missing_modules.py. It should report nothing missing. Then run the "
        "deck command again."),
    11: ("py -3.12 test_schedule_sizing.py in app/ should report 20 checks and none "
         "failed. Then run the deck with --freq auto and read the SCHEDULE SIZED block: "
         "it prints every round of the loop, so the answer is never a black box."),
    12: ("py -3.12 test_airport_profile.py in app/ should report 36 checks and none "
         "failed. It builds a DuckDB carrying the store's own traps, so it exercises "
         "the queries rather than mocking them. Then, for any airport a deck is "
         "wanted for:\n"
         "   py -3.12 check_airport.py EDI\n"
         "which reports year by year what OAG and ACI each hold and which of the "
         "four airport charts can be drawn from them."),
    13: ("py -3.12 test_load_aci.py in app/ should report 45 checks and none failed. "
         "The store is BUILT at C:\\Avia\\aci.duckdb, 7 Aug 2026: 1,732 airports, "
         "249,803 airport-months, Sep-2007 to Dec-2025, no colliding rows. Rebuild "
         "when the workbook is refreshed, --inspect first, then verify:\n"
         "   py -3.12 load_aci.py --inspect --xlsx \"...MONTH_ACI Monthly Time Series(NO).xlsx\"\n"
         "   py -3.12 load_aci.py --xlsx \"...\" --out C:\\Avia\\aci.duckdb\n"
         "   py -3.12 check_aci.py EDI LHR AUS INV"),
    10: ("Run check_env.py on every Python that runs any part of this tool. It exits "
         "non-zero when something required is missing or broken, so it can gate a deploy."),
    9: ("Run a route you know on both copies and compare the total and the point to "
        "point / connecting split. They should now agree. If WORK moves, that is the "
        "bucket correction and the hub re-split coming back on, and every WORK-side "
        "forecast taken before today was missing both."),
    8: ("Restart the service and run a route at a thin frequency: the dashboard should "
        "show a viability banner asking whether to proceed, above the charts, on both a "
        "plain run and an OPTIMISE run. Then run test_visual_layer.py in Deck "
        "Generator/v4, which should report 32 checks and none failed. cortex_app.py is "
        "NOT in this step; it stays a hand merge and takes _attach_viability plus its "
        "two call sites separately."),
    6: ("Run AUS to EDI twice, once blank and once through OPTIMISE. Each should open with "
        "a line saying which question it answered, and the three feasibility banners should "
        "now sit above the charts rather than below them. Then read /help."),
    14: ("Nothing to test on the running service: none of the fifteen is imported by it. "
         "The check is that the tree is now complete.\n"
         "   py -3.12 missing_modules.py            should report nothing missing\n"
         "   py -3.12 capability_audit.py --tree \".\\app\" --out CAPABILITY_AUDIT.md\n"
         "Re-run the audit AFTER this step, not before: the version John has was run on a "
         "tree missing these fifteen, so its orphan list is wrong. Then run a forecast for "
         "a route you know and confirm the number has not moved, which is the point."),
    15: ("py -3.12 test_load_aci.py in app/ on the SITE copy should now report 53 checks and "
         "none failed, the count recorded in the 8 August handover, and ten more than the "
         "SITE copy reported before this step. Note the count in CHECK 13 above says 45; one "
         "of the two is out of date, so read the number the run prints rather than trusting "
         "either note."),
}


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def when(path):
    try:
        return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%d %b %Y %H:%M")
    except OSError:
        return "absent"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", required=True, help="the copy run.bat launches")
    ap.add_argument("--work", required=True, help="the working copy")
    ap.add_argument("--step", type=int, required=True, choices=sorted(STEPS),
                    help="which step of the reconciliation to run")
    ap.add_argument("--apply", action="store_true",
                    help="actually copy. Without this nothing is written")
    ap.add_argument("--backup-dir", default="",
                    help="where overwritten files are kept (default: beside the "
                         "destination, in _reconcile_backup)")
    args = ap.parse_args()

    roots = {"site": os.path.abspath(args.site), "work": os.path.abspath(args.work)}
    for k, v in roots.items():
        if not os.path.isdir(v):
            sys.exit("not a directory (%s): %s" % (k, v))

    title, files = STEPS[args.step]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print("=" * 78)
    print("STEP %d  %s" % (args.step, title))
    print("SITE %s" % roots["site"])
    print("WORK %s" % roots["work"])
    print("MODE %s" % ("APPLY, files will be written" if args.apply
                       else "DRY RUN, nothing will be written"))
    print("=" * 78)

    planned, skipped, failed = [], [], []
    for rel, src_side in files:
        name = os.path.basename(rel)
        if name in BLOCKED:
            skipped.append((rel, "BLOCKED: %s" % BLOCKED[name]))
            continue
        dst_side = "work" if src_side == "site" else "site"
        src = os.path.join(roots[src_side], rel)
        dst = os.path.join(roots[dst_side], rel)
        if not os.path.exists(src):
            skipped.append((rel, "source missing on %s" % src_side.upper()))
            continue
        if os.path.exists(dst) and sha1(src) == sha1(dst):
            skipped.append((rel, "already identical"))
            continue
        planned.append((rel, src_side, dst_side, src, dst))

    if planned:
        print("\nTO COPY  (%d)" % len(planned))
        for rel, ss, ds, src, dst in planned:
            new = "" if os.path.exists(dst) else "   NEW on %s" % ds.upper()
            print("  %-34s %s -> %s   %s | %s%s"
                  % (rel, ss.upper(), ds.upper(), when(src), when(dst), new))
    if skipped:
        print("\nNOT COPIED  (%d)" % len(skipped))
        for rel, why in skipped:
            print("  %-34s %s" % (rel, why))

    print("\nLEFT ALONE DELIBERATELY")
    for rel, why in LEAVE.items():
        print("  %-34s %s" % (rel, why))
    print("\nHAND MERGE, NEVER COPIED")
    for rel, why in BLOCKED.items():
        if rel.endswith(".py"):
            print("  %-34s %s" % (rel, why))

    if not args.apply:
        print("\n" + "=" * 78)
        print("DRY RUN. Re-run with --apply to write these %d file(s)." % len(planned))
        print("=" * 78)
        return

    if not planned:
        print("\nNothing to do.")
        return

    backup_root = args.backup_dir or os.path.join(
        os.path.dirname(roots["work"]), "_reconcile_backup", "step%d_%s" % (args.step, stamp))
    print("\nBACKUP %s" % backup_root)
    for rel, ss, ds, src, dst in planned:
        try:
            if os.path.exists(dst):
                bak = os.path.join(backup_root, ds, rel)
                os.makedirs(os.path.dirname(bak), exist_ok=True)
                shutil.copy2(dst, bak)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            if sha1(src) != sha1(dst):
                failed.append((rel, "copied but the two do not match"))
            else:
                print("  copied  %-34s %s -> %s" % (rel, ss.upper(), ds.upper()))
        except Exception as e:
            failed.append((rel, str(e)))

    print("\n" + "=" * 78)
    if failed:
        print("FAILED  (%d). The originals are in the backup folder above." % len(failed))
        for rel, why in failed:
            print("  %-34s %s" % (rel, why))
        sys.exit(1)
    print("STEP %d DONE. %d file(s) copied, originals backed up." % (args.step, len(planned)))
    print("NOW CHECK: %s" % CHECK.get(args.step, "run the tool."))
    print("Then re-run audit_split.py; this step's files should no longer be listed.")
    print("=" * 78)


if __name__ == "__main__":
    main()
