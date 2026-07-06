# Avia Cortex - World Routes demo deployment

The one rule behind all of this: the demo laptop must run from a plain local folder with a pinned
virtual environment, never from the OneDrive-synced project. During development OneDrive stalled a
build for 20 minutes, froze the machine, and repeatedly served half-written module files to tooling.
A sync pause or a conflicted copy mid-demo would be fatal on a stand. The steps below move the demo
onto local disk, pin the Python, and give one command to bring it up in a known-good state.

## One-time setup (do this before travelling)

Copy the app to a local folder off OneDrive. `C:\AviaDemo\` is the assumed home throughout.

```
robocopy "C:\Users\Carte\OneDrive\Documents\Claude\Projects\Avia QSI Tool\app" C:\AviaDemo /E
```

Build a pinned virtual environment inside it so the wrong Python can never resolve (the dev machine
has two 3.12 installs, which is what flipped the water check on and off during development):

```
py -3.12 -m venv C:\AviaDemo\.venv
C:\AviaDemo\.venv\Scripts\python -m pip install -r C:\AviaDemo\requirements.txt
```

Confirm it runs, then freeze the exact versions and keep that lock file as the real pin:

```
C:\AviaDemo\.venv\Scripts\python -m pip freeze > C:\AviaDemo\requirements.lock.txt
```

Put the data where the app expects it. The stores default to `C:\Avia\sabre.duckdb` and
`C:\Avia\oag.duckdb`; keep them there, or copy them local and pass `--sabre` / `--oag` to warm-up.
The pre-aggregation store (`E:\preagg.duckdb`) speeds forecasts but is optional for the portal. The
wave cache (`qsi_wave_cache_6yr.duckdb`) and the GeoNames dump the catchment resolver needs should
sit alongside the app in `C:\AviaDemo\`.

## Every session: one command

```
C:\AviaDemo\.venv\Scripts\python C:\AviaDemo\warm_demo.py --python C:\AviaDemo\.venv\Scripts\python.exe
```

That clears any stale listener on 8010, launches the server single-threaded with a fixed hash seed
(so a route typed twice returns the same number), waits for it to answer, logs in, runs three
showcase forecasts to populate the Methodology bridge and warm the caches, checks pitch health and
the water mask, and opens the Dashboard, Track record and Methodology tabs. Re-running it is safe; if
the server is already up it just re-warms.

Pass `--no-browser` to warm without opening tabs, `--sabre` / `--oag` if the stores are not at
`C:\Avia`, and `--password` (or set `AVIA_PASSWORD`) to override the login.

## Pre-stand checklist (the demo failure modes)

- [ ] OneDrive paused, or the demo folder is genuinely outside any synced path. (D1)
- [ ] Launching with the venv's `python.exe`, not a bare `py -3.12`. (D2)
- [ ] `global-land-mask` installed in the venv, so the water check is ON (warm-up prints this). (D5)
- [ ] Do NOT click the researched pitch live; it needs internet, an API key and minutes. Pre-generate
      the pack and open the HTML. Pre-flight blocks it gracefully if clicked. (D3)
- [ ] GeoNames dump present, so coastal/city-name routes resolve instead of erroring out. (D4/D5)
- [ ] warm_demo has run since the last restart, so the Methodology bridge has a LAST_FC. (D6)
- [ ] No back-test or build job running; it would drain the laptop and lock a store. (D7)
- [ ] Power settings set so the lid/sleep does not kill the server between sessions. (D8)
- [ ] Port 8010 free at launch; warm-up clears a stale listener automatically. (D9)
- [ ] Rehearse the "resolved to SOU - Southampton (GB)" recovery line for a mistyped code. (D4)

## Stopping

The server runs in its own console window. Close that window to stop it, or run
`Get-Process python | Stop-Process` if it detaches.
