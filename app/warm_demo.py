#!/usr/bin/env python3
r"""
Avia Cortex - demo warm-up (REVIEW_QSI_for_Opus_05Jul2026, items 4-5 / F4 / D6-D9).
====================================================================================
One command to bring the portal to a known-good state before a stand session at World Routes:

  1. free port 8010 of any stale listener (D9) so a crashed instance can't block the start;
  2. launch the server with a PINNED python and the determinism env (AVIA_DUCKDB_THREADS=1,
     PYTHONHASHSEED=0) so a route typed twice returns the same number (D2);
  3. wait for it to answer, then log in;
  4. run three showcase forecasts (Genoa-New York, Southampton-Tenerife, the validated LHR-SJC)
     to populate LAST_FC (so the Methodology bridge isn't empty, D6) and warm the caches;
  5. check /api/pitch/health and whether the water-boundary mask is active;
  6. open the Dashboard, Track record and Methodology tabs.

Idempotent: if the server is already up it skips the launch and just re-warms. Safe to re-run.

  py -3.12 warm_demo.py
  py -3.12 warm_demo.py --python C:\AviaDemo\.venv\Scripts\python.exe --sabre C:\Avia\sabre.duckdb
  py -3.12 warm_demo.py --no-browser        (headless: warm only, don't open tabs)

Point --python at the demo venv's python.exe so the server never resolves the wrong 3.12 (the machine
has two; that is what flipped the water check on and off during development).
"""
import argparse, http.cookiejar, os, socket, subprocess, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
# Showcase routes: (origin, dest, label). Kept few and fast so warm-up stays under ~a minute.
SHOWCASE = [("GOA", "JFK", "Genoa - New York"),
            ("SOU", "TFS", "Southampton - Tenerife"),
            ("LHR", "SJC", "London - San Jose (validated case)")]


def _port_open(host, port, timeout=0.5):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return s.connect_ex((host, port)) == 0


def _free_port(port):
    """Kill whatever is listening on `port` (Windows netstat+taskkill; best-effort elsewhere)."""
    if not _port_open("127.0.0.1", port):
        return
    print(f"  port {port} is in use - clearing the stale listener")
    try:
        if os.name == "nt":
            out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True).stdout
            pids = {ln.split()[-1] for ln in out.splitlines()
                    if f":{port} " in ln and "LISTENING" in ln}
            for pid in pids:
                subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True)
        else:
            subprocess.run(["bash", "-lc", f"fuser -k {port}/tcp"], capture_output=True)
        time.sleep(1.5)
    except Exception as e:
        print(f"  (could not auto-clear the port: {e}; close the old window by hand)")


def _pick_python(arg):
    if arg:
        return arg
    venv = os.path.join(HERE, ".venv", "Scripts", "python.exe")   # Windows demo venv, if present
    return venv if os.path.exists(venv) else sys.executable


def _server_env(a):
    env = dict(os.environ)
    env.setdefault("AVIA_DUCKDB_THREADS", "1")   # deterministic live forecasts on the stand
    env.setdefault("PYTHONHASHSEED", "0")
    # THE FREQUENCY SWITCH, set here on 12 August 2026. It was not, so unless the launching shell
    # happened to carry it the portal ran with frequency sensitivity OFF, against the decision of
    # 10 August. With it off the route returns the same demand at 3, 5, 7, 10 and 14 weekly and only
    # the load factor moves, so a planner asking what the seventh frequency buys gets no answer.
    # setdefault, so a shell that names it still wins and a deliberate off is still possible.
    env.setdefault("AVIA_FREQ_SENSITIVE", "1")
    # THE FORECAST ENGINE IS PINNED, NOT INHERITED, and this is deliberately not a setdefault.
    #
    # The calibrated model was wired behind AVIA_FORECAST_ENGINE on 13 August 2026, and on the same
    # evening the shell used to test it carried AVIA_FORECAST_ENGINE=bt2. A server started from that
    # shell would have served model numbers to a client with no announcement, and the model rebuilt
    # that night under the pinned scikit-learn HAS NOT HAD ITS ACCURACY MEASURED: every published
    # figure describes an artefact fitted under a different release.
    #
    # So the demo server takes the engine from THIS FLAG and nowhere else. A stale export in the
    # launching shell cannot reach a client. --engine bt2 opts in, deliberately and visibly, and the
    # value is printed at start-up either way.
    env["AVIA_FORECAST_ENGINE"] = a.engine
    if a.sabre:
        env["AVIA_SABRE"] = a.sabre
    if a.oag:
        env["AVIA_OAG"] = a.oag
    if a.password:
        env["AVIA_PASSWORD"] = a.password
    return env


def _start_server(py, port, env):
    print(f"  launching server: {py} -m uvicorn cortex_app:app --port {port}")
    creation = subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
    return subprocess.Popen([py, "-m", "uvicorn", "cortex_app:app", "--port", str(port)],
                            cwd=HERE, env=env, creationflags=creation)


def _wait_up(base, secs=90):
    t0 = time.time()
    while time.time() - t0 < secs:
        try:
            urllib.request.urlopen(base + "/login", timeout=2)
            return True
        except urllib.error.HTTPError:
            return True          # any HTTP answer means it's up
        except Exception:
            time.sleep(1.0)
    return False


def _opener(base, password):
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    data = urllib.parse.urlencode({"password": password}).encode()
    op.open(base + "/login", data=data, timeout=15)     # sets the cortex_auth cookie in the jar
    return op


def _get(op, url, timeout=120):
    with op.open(url, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "ignore")


def _water_active(py):
    """Ask the SERVER's python whether the land mask is importable (water check on)."""
    try:
        r = subprocess.run([py, "-c", "import global_land_mask"], capture_output=True)
        return r.returncode == 0
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description="Warm the Avia Cortex portal to a demo-ready state.")
    ap.add_argument("--port", type=int, default=8010)
    ap.add_argument("--python", default=None, help="python.exe to launch the server (default: ./.venv else current)")
    ap.add_argument("--sabre", default=None, help="Sabre store path (sets AVIA_SABRE for the server)")
    ap.add_argument("--oag", default=None, help="OAG store path (sets AVIA_OAG for the server)")
    ap.add_argument("--password", default=os.environ.get("AVIA_PASSWORD", "aviacortex2026"))
    ap.add_argument("--engine", choices=("qsi", "bt2"), default="qsi",
                    help="which engine answers. DEFAULT qsi, the shipped one, and the shell cannot "
                         "override it: the model rebuilt on 13 August has not had its accuracy "
                         "measured, so bt2 must be asked for on this line and nowhere else")
    ap.add_argument("--no-browser", action="store_true", help="warm only; do not open browser tabs")
    a = ap.parse_args()
    base = f"http://127.0.0.1:{a.port}"
    py = _pick_python(a.python)

    print("Avia Cortex demo warm-up")
    print(f"  python : {py}")
    print(f"  water-boundary mask: {'ON' if _water_active(py) else 'OFF - run: ' + py + ' -m pip install global-land-mask'}")
    # Said at start-up, every time, because it decides which engine a client is shown and the shell
    # cannot be trusted to carry it. _shell names what was inherited so a surprise is visible.
    _shell = (os.environ.get("AVIA_FORECAST_ENGINE") or "unset").strip().lower()
    print(f"  forecast engine: {a.engine.upper()}"
          + ("  (the shipped QSI engine)" if a.engine == "qsi" else
             "  *** CALIBRATED MODEL, accuracy NOT re-measured since the 13 Aug rebuild ***")
          + (f"   [shell said {_shell}, overridden]" if _shell not in ("unset", a.engine) else ""))

    proc = None
    if _port_open("127.0.0.1", a.port):
        # A SERVER ALREADY UP IS NOT NECESSARILY THE SERVER YOU ASKED FOR. It was started with its
        # own engine and this run cannot change it, so re-warming an existing listener while
        # printing a line that says QSI would be the silent-default shape again.
        print(f"  server already answering on {a.port} - re-warming (no relaunch)")
        print(f"  NOTE: the running server keeps the engine IT was started with, which this run "
              f"cannot see. Restart with --engine {a.engine} if you need certainty.")
    else:
        _free_port(a.port)
        proc = _start_server(py, a.port, _server_env(a))

    if not _wait_up(base):
        print(f"FAILED: server did not answer on {base} within 90s. Check the server console window.")
        return 2
    print("  server up")

    try:
        op = _opener(base, a.password)
    except Exception as e:
        print(f"FAILED: could not log in ({e}). Check AVIA_PASSWORD.")
        return 2

    import json
    ok = 0
    for origin, dest, label in SHOWCASE:
        try:
            t = time.time()
            status, body = _get(op, base + f"/api/forecast?origin={origin}&dest={dest}")
            try:
                good = bool(json.loads(body).get("ok"))
            except Exception:
                good = False
            note = "OK" if good else f"returned {status}"
            print(f"  forecast {label:38} {note}  ({time.time()-t:.0f}s)")
            ok += int(good)
        except Exception as e:
            print(f"  forecast {label:38} ERROR {str(e)[:60]}")

    try:
        status, _ = _get(op, base + "/api/pitch/health", timeout=20)
        print(f"  /api/pitch/health : {status}")
    except Exception as e:
        print(f"  /api/pitch/health : ERROR {str(e)[:60]}")

    print(f"\n{'DEMO READY' if ok else 'WARM-UP INCOMPLETE'}: {ok}/{len(SHOWCASE)} showcase forecasts populated LAST_FC.")
    print(f"  Dashboard    {base}/")
    print(f"  Track record {base}/trackrecord?airport=LGW")
    print(f"  Methodology  {base}/methodology")

    if not a.no_browser:
        import webbrowser
        for path in ("/", "/trackrecord?airport=LGW", "/methodology"):
            webbrowser.open(base + path)
            time.sleep(0.6)

    if proc is not None:
        print("\n  the server is running in its own console window; close that window to stop it.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
