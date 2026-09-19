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


def _optimise(op, base, q, timeout=1800):
    """Start the background sweep and poll until done. Returns (seconds, state, error)."""
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
                return round(time.perf_counter() - t0, 1), "done", ""
            if st in ("error", "cancelled"):
                return round(time.perf_counter() - t0, 1), st, str(j.get("error", ""))[:80]
        return round(time.perf_counter() - t0, 1), "TIMEOUT", ""
    except Exception as e:                                   # noqa: BLE001
        return round(time.perf_counter() - t0, 1), "ERR", str(e)[:80]


def measure_pair(op, base, origin, dest, airline, skip_full):
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
    rows.append(("Run, cold (airline named, dep blank, AUTO gauge)", *_timed(op, base + "/api/forecast?" + urllib.parse.urlencode(qa))))
    rows.append(("Run, warm (same query again)", *_timed(op, base + "/api/forecast?" + urllib.parse.urlencode(qa))))
    rows.append(("Run, fixed departure 10:00 (no departure sweep)",
                 *_timed(op, base + "/api/forecast?" + urllib.parse.urlencode(dict(qa, dep_time="10:00")))))
    rows.append(("catchment profile, origin", *_timed(op, base + "/api/catchment?" + urllib.parse.urlencode({"origin": origin}))))
    rows.append(("Optimise, narrowed default (airline named, annual)",
                 *_optimise(op, base, dict(qa, freq=0))))
    if not skip_full:
        rows.append(("Optimise, full sweep (nothing fixed)",
                     *_optimise(op, base, dict(q, airline="", aircraft="", season="", freq=0))))
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
    a = ap.parse_args()
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
            rows = measure_pair(op, a.base, o, d, al, a.skip_full)
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
