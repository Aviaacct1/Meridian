#!/usr/bin/env python3
r"""
Avia Solutions - Routes speed workstream, step 3.1: MEASURE before touching anything.
======================================================================================
Times the three run types the stand will use, end to end, against a LIVE Meridian server, from
outside the code. Nothing in the demo path changes. Run it against a freshly restarted server for
the cold numbers, then again after each speed change (preagg on, persistent cache, pre-warm) with
the same pairs, and compare the tables.

Stand order is measured, because that is what a visitor sees: the market brief fires on route
entry, then Run (airline named, departure blank, gauge AUTO: the default assessment path, which
already includes the departure-time optimisation), then Run again (warm), then Run with a fixed
departure (the difference against the warm Run is the departure sweep), then Optimise on the
NARROWED default (airline named, annual season), then Optimise with nothing fixed (today's full
sweep: airlines x frequencies x seasons). Every stage is wall clock in seconds.

    Workstation Actual, server already running (Meridian-run.bat), in a second window:

        cd C:\src\meridian
        py -3.12 diag_routes_timing.py                     (server on 127.0.0.1:8010, the launcher's port)
        py -3.12 diag_routes_timing.py --pairs SJC-TPE:CI,BRS-EWR:UA --skip-full
        py -3.12 diag_routes_timing.py --profile SJC-TPE:CI      (in-process cProfile of one Run)
        py -3.12 diag_routes_timing.py --skip-full --save-json E:\Avia\probe\before   (payloads saved)
        py -3.12 diag_routes_timing.py --diff E:\Avia\probe\before E:\Avia\probe\after   (identity)

Password: env QSI_PASSWORD, else app\access_password.txt, the same two places the server reads.
Output: printed, and written to TIMING-<date>-<time>.md beside this script for the record.
"""
import argparse, http.cookiejar, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "app")


def _password():
    p = os.environ.get("QSI_PASSWORD", "").strip()
    if p:
        return p
    fp = os.path.join(APP, "access_password.txt")
    if os.path.exists(fp):
        for line in open(fp, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#"):
                return line
    return ""


def _signin(base, password):
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    data = urllib.parse.urlencode({"password": password, "next": "/welcome",
                                   "email": "timing@aviasolutions.com"}).encode()
    op.open(base + "/signin", data=data, timeout=15)
    if not any(c.name == "obs_entered" for c in jar):
        raise RuntimeError("sign-in returned no obs_entered cookie: password refused or entry page changed")
    return op


def _get(op, url, timeout=1800):
    with op.open(url, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "ignore")


def _timed(op, url, timeout=1800):
    t0 = time.perf_counter()
    err = ""
    try:
        status, body = _get(op, url, timeout)
        try:
            j = json.loads(body)
            if isinstance(j, dict) and j.get("ok") is False:
                err = str(j.get("error", ""))[:80]
        except Exception:
            pass
    except Exception as e:                                   # noqa: BLE001
        status, err = "ERR", str(e)[:80]
    return round(time.perf_counter() - t0, 1), status, err


def _optimise(op, base, q, timeout=1800, save=None):
    """Start the background sweep and poll until done. Returns (seconds, state, note).
    With save=<path>, the finished payload is written there for --diff (23 Sep 2026), and
    the note reports how the sweep ran (cells, workers, sweep seconds from the payload)."""
    t0 = time.perf_counter()
    try:
        _, body = _get(op, base + "/api/optimise/start?" + urllib.parse.urlencode(q), 60)
        job = json.loads(body).get("job_id")
        if not job:
            return round(time.perf_counter() - t0, 1), "ERR", "no job_id: " + body[:80]
        while time.perf_counter() - t0 < timeout:
            time.sleep(2)
            _, body = _get(op, base + "/api/optimise/status?job_id=" + job, 60)
            j = json.loads(body)
            st = j.get("state")
            if st == "done":
                res = j.get("result") or {}
                note = ""
                o = res.get("optimised") if isinstance(res.get("optimised"), dict) else res
                if isinstance(o, dict) and o.get("sweep_workers") is not None:
                    note = "cells %s, workers %s, sweep %ss" % (o.get("sweep_cells"), o.get("sweep_workers"), o.get("sweep_elapsed_s"))
                if save:
                    try:
                        os.makedirs(os.path.dirname(save), exist_ok=True)
                        open(save, "w", encoding="utf-8", newline="\n").write(json.dumps(res, indent=1, sort_keys=True))
                        note = (note + "; " if note else "") + "saved " + os.path.basename(save)
                    except Exception as e:                   # noqa: BLE001
                        note = (note + "; " if note else "") + "save failed: " + str(e)[:40]
                return round(time.perf_counter() - t0, 1), "done", note
            if st in ("error", "cancelled"):
                return round(time.perf_counter() - t0, 1), st, str(j.get("error", ""))[:80]
        return round(time.perf_counter() - t0, 1), "TIMEOUT", ""
    except Exception as e:                                   # noqa: BLE001
        return round(time.perf_counter() - t0, 1), "ERR", str(e)[:80]


def _walk(a, b, path, out, limit=60):
    """Every leaf that differs between two JSON values, as 'path: a -> b'."""
    if len(out) >= limit:
        return
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            _walk(a.get(k, "<absent>"), b.get(k, "<absent>"), path + "/" + str(k), out, limit)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}: list length {len(a)} -> {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            _walk(x, y, f"{path}[{i}]", out, limit)
    elif a != b:
        out.append(f"{path}: {str(a)[:60]} -> {str(b)[:60]}")


VOLATILE = ("elapsed", "when", "started", "job_id", "run_id", "timestamp", "generated",
            "sweep_workers", "sweep_cells")   # how the Optimise sweep ran, not what it found


def diff_json(path_a, path_b):
    """Compare two saved forecast payloads; keys whose name contains a VOLATILE word are
    ignored, everything else must match exactly. Returns (n_differences, lines)."""
    a = json.load(open(path_a, encoding="utf-8"))
    b = json.load(open(path_b, encoding="utf-8"))

    def strip(x):
        if isinstance(x, dict):
            return {k: strip(v) for k, v in x.items() if not any(w in str(k).lower() for w in VOLATILE)}
        if isinstance(x, list):
            return [strip(v) for v in x]
        return x
    out = []
    _walk(strip(a), strip(b), "", out)
    return len(out), out


def measure_pair(op, base, origin, dest, airline, skip_full, save_dir=None):
    rows = []
    q = {"origin": origin, "dest": dest}
    # Sanity row, not a timing: the picker after the 29 Aug aircraft-econ code (master list 6.6
    # expects 42 costable types plus known_uncostable).
    try:
        _, body = _get(op, base + "/api/aircraft", 60)
        j = json.loads(body)
        rows.append(("aircraft picker (/api/aircraft), types listed", 0.0, 200,
                     f"{len(j.get('aircraft', []))} costable, {len(j.get('known_uncostable', {}))} known uncostable"
                     + (f"; error: {j['error'][:60]}" if j.get("error") else "")))
    except Exception as e:                                   # noqa: BLE001
        rows.append(("aircraft picker (/api/aircraft), types listed", 0.0, "ERR", str(e)[:80]))
    qa = dict(q, airline=airline, aircraft="", season="annual") if airline else dict(q, aircraft="", season="annual")
    rows.append(("market brief (route entry)", *_timed(op, base + "/api/market_brief?" + urllib.parse.urlencode(q))))
    run_url = base + "/api/forecast?" + urllib.parse.urlencode(qa)
    rows.append(("Run, cold (airline named, dep blank, AUTO gauge)", *_timed(op, run_url)))
    if save_dir:
        # The Run's payload, saved so a speed change can be proved output-identical (--diff).
        try:
            os.makedirs(save_dir, exist_ok=True)
            _, body = _get(op, run_url)
            fp = os.path.join(save_dir, f"run_{origin}-{dest}_{airline or 'NA'}.json")
            open(fp, "w", encoding="utf-8", newline="\n").write(body)
            rows.append(("Run payload saved for --diff", 0.0, 200, os.path.basename(fp)))
        except Exception as e:                               # noqa: BLE001
            rows.append(("Run payload saved for --diff", 0.0, "ERR", str(e)[:80]))
    rows.append(("Run, warm (same query again)", *_timed(op, base + "/api/forecast?" + urllib.parse.urlencode(qa))))
    rows.append(("Run, fixed departure 10:00 (no departure sweep)",
                 *_timed(op, base + "/api/forecast?" + urllib.parse.urlencode(dict(qa, dep_time="10:00")))))
    rows.append(("catchment profile, origin", *_timed(op, base + "/api/catchment?" + urllib.parse.urlencode({"origin": origin}))))
    _sv = (lambda tag: os.path.join(save_dir, f"opt_{origin}-{dest}_{airline or 'NA'}_{tag}.json")) if save_dir else (lambda tag: None)
    rows.append(("Optimise, narrowed default (airline named, annual)",
                 *_optimise(op, base, dict(qa, freq=0), save=_sv("named"))))
    if not skip_full:
        rows.append(("Optimise, full sweep (nothing fixed)",
                     *_optimise(op, base, dict(q, airline="", aircraft="", season="", freq=0), save=_sv("full"))))
    return rows


def profile_run(origin, dest, airline):
    """In-process cProfile of ONE calibrated_forecast, so the seconds can be attributed to the
    Sabre aggregates, the departure sweep, catchment and the rest. Uses the same environment the
    launcher sets; a second process against the same stores, read-only."""
    root = os.environ.get("AVIA_ROOT") or (r"E:\Avia" if os.path.exists(r"E:\Avia\sabre.duckdb") else r"D:\Avia")
    os.environ.setdefault("AVIA_SABRE", os.path.join(root, "sabre.duckdb"))
    os.environ.setdefault("AVIA_OAG", os.path.join(root, "oag.duckdb"))
    os.environ.setdefault("AVIA_FREQ_SENSITIVE", "1")
    os.environ.setdefault("AVIA_FEED_LEVEL", "v1")
    sys.path.insert(0, APP)
    os.chdir(APP)
    import cProfile, pstats, io
    import cortex_app as CA
    pr = cProfile.Profile()
    t0 = time.perf_counter()
    pr.enable()
    fc = CA.calibrated_forecast(origin, dest, airline=(airline or None), season="annual")
    pr.disable()
    total = time.perf_counter() - t0
    ok = isinstance(fc, dict) and fc.get("ok")
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(45)
    out = ["", f"## In-process profile: {origin}-{dest} {airline or '(no airline)'}: "
               f"{total:.1f}s total, ok={ok}", "", "Top 45 by cumulative time (the engine's own functions;"
           " look for connecting_market / behind_market / p2p_traffic / sector_traffic /"
           " optimise_departure / catchment / market_brief / duckdb execute):", "```"]
    out += [ln.rstrip() for ln in s.getvalue().splitlines() if ln.strip()]
    out.append("```")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Time the stand's run types against a live Meridian server.")
    ap.add_argument("--base", default="http://127.0.0.1:8010",
                    help="the launcher (warm_demo.py) serves on 127.0.0.1:8010")
    ap.add_argument("--pairs", default="SJC-TPE:CI,BRS-EWR:UA",
                    help="comma list of ORIG-DEST:AIRLINE; airline may be blank (ORIG-DEST:)")
    ap.add_argument("--skip-full", action="store_true", help="skip the full nothing-fixed Optimise sweep")
    ap.add_argument("--profile", default="", help="ORIG-DEST:AIRLINE to cProfile one Run in-process (no server needed)")
    ap.add_argument("--save-json", default="", help="directory to save each pair's Run payload (before/after a change)")
    ap.add_argument("--diff", nargs=2, metavar=("BEFORE_DIR", "AFTER_DIR"),
                    help="compare saved Run payloads pair by pair; exit 1 on any difference")
    a = ap.parse_args()
    if a.diff:
        before, after = a.diff
        names = sorted(f for f in os.listdir(before) if f.startswith(("run_", "opt_")) and f.endswith(".json"))
        bad = 0
        for f in names:
            fb = os.path.join(after, f)
            if not os.path.exists(fb):
                print(f"{f}: MISSING in {after}"); bad += 1; continue
            n, lines = diff_json(os.path.join(before, f), fb)
            print(f"{f}: {'IDENTICAL' if n == 0 else str(n) + ' differences'}")
            for ln in lines[:40]:
                print("   ", ln)
            bad += n
        print("\nPASS: every saved Run payload identical (volatile keys ignored)." if bad == 0
              else f"\nFAIL: {bad} differences; the change moved a number or a field.")
        sys.exit(0 if bad == 0 else 1)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    lines = [f"# Routes timing, {datetime.now().strftime('%d %B %Y %H:%M')}",
             f"Server {a.base}; machine {os.environ.get('COMPUTERNAME', '?')}; pairs {a.pairs}. "
             "Seconds, wall clock, measured from outside the server in stand order. "
             "'Cold' = first call since the server process started; restart the server first for a true cold run.", ""]
    if a.profile:
        od, _, al = a.profile.partition(":")
        o, d = od.split("-")
        lines.append(profile_run(o.strip().upper(), d.strip().upper(), al.strip().upper()))
    else:
        pw = _password()
        if not pw:
            print("no password found (QSI_PASSWORD or app\\access_password.txt); if the server runs without one, continue")
        op = _signin(a.base, pw)
        for spec in [s.strip() for s in a.pairs.split(",") if s.strip()]:
            od, _, al = spec.partition(":")
            o, d = od.split("-")
            o, d, al = o.strip().upper(), d.strip().upper(), al.strip().upper()
            print(f"\n{o}-{d} {al or '(no airline)'} ...", flush=True)
            rows = measure_pair(op, a.base, o, d, al, a.skip_full, a.save_json or None)
            lines += [f"## {o}-{d} {al or '(no airline)'}", "", "| Stage | Seconds | HTTP | Error |", "|---|---|---|---|"]
            for name, secs, status, err in rows:
                lines.append(f"| {name} | {secs} | {status} | {err} |")
                print(f"  {secs:>7}s  {status}  {name}  {err}", flush=True)
            lines.append("")
    text = "\n".join(lines) + "\n"
    out = os.path.join(HERE, f"TIMING-{stamp}.md")
    open(out, "w", encoding="utf-8", newline="\n").write(text)
    print("\n" + text)
    print(f"written {out}")


if __name__ == "__main__":
    main()
