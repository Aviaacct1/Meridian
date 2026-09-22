#!/usr/bin/env python3
"""Rule-lock for the catchment distance measure (route_forecast.friction_report).

Proven on donatello 22 September 2026: the friction raster was resolved from a hardcoded
C:\\Avia that no longer existed, the raster itself sat on the data drive, and every catchment
run fell back to great circle without a word. Same shape as the MCT fault, so the same
remedy: resolve through config, and state which measure is in force rather than choosing in
silence.

These checks hold three things:

  1. Road times are OFF unless asked for, because switching them on moves every forecast and
     that belongs to a calibration, not to whether a file happens to be present on a machine.
  2. friction_report names the state it is in, and never raises, whatever is or is not on disk.
  3. The raster path resolves through config like every other path, and AVIA_FRICTION wins.

Avia Solutions Limited. All rights reserved.
"""
import importlib
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

CHECKS = []


def check(name, got, want):
    ok = got == want
    CHECKS.append((name, ok, got, want))
    return ok


def _reload(**env):
    """Re-import route_forecast with a given environment. DRIVE_TIMES and FRICTION_PATH are read
    at import, so the switch can only be tested by reloading."""
    saved = {}
    for k, v in env.items():
        saved[k] = os.environ.get(k)
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    try:
        import config
        importlib.reload(config)
        import route_forecast
        return importlib.reload(route_forecast), saved
    except Exception:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        raise


def _restore(saved):
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    import config
    importlib.reload(config)
    import route_forecast
    importlib.reload(route_forecast)


def main():
    # ---- 1. OFF by default, whatever is on disk -----------------------------------------
    with tempfile.TemporaryDirectory() as d:
        raster = os.path.join(d, "friction_2019.tif")
        open(raster, "wb").write(b"not a real raster, but it exists")

        RF, saved = _reload(AVIA_FRICTION=raster, AVIA_DRIVE_TIMES=None)
        try:
            r = RF.friction_report()
            check("default: switch off", r["enabled"], False)
            check("default: raster still located", r["exists"], True)
            check("default: road times not available", r["available"], False)
            check("default: no error, this is a choice not a fault", r["error"], None)
            check("default: drive engine is None", RF._drive_engine(), None)
            check("default: path is the resolved raster", os.path.normcase(r["path"]),
                  os.path.normcase(raster))
        finally:
            _restore(saved)

        # ---- 2. Switched on, raster present: it tries, and says so if the libraries fail ----
        RF, saved = _reload(AVIA_FRICTION=raster, AVIA_DRIVE_TIMES="on")
        try:
            r = RF.friction_report()
            check("on: switch reads on", r["enabled"], True)
            check("on: raster found", r["exists"], True)
            # A stub file is not a readable raster. Either DriveTimes reports unavailable or it
            # raises and the error is carried. Both are honest; neither may claim road times.
            check("on: does not claim road times from a stub", r["available"], False)
            check("on: report states a state, not silence",
                  bool(r["error"]) or r["available"] is False, True)
        finally:
            _restore(saved)

    # ---- 3. Switched on, raster absent: named as missing, and it still does not raise ------
    missing = os.path.join(tempfile.gettempdir(), "no_such_friction_raster_20260922.tif")
    if os.path.exists(missing):
        os.remove(missing)
    RF, saved = _reload(AVIA_FRICTION=missing, AVIA_DRIVE_TIMES="on")
    try:
        r = RF.friction_report()
        check("missing: exists False", r["exists"], False)
        check("missing: not available", r["available"], False)
        check("missing: reason named", r["error"], "raster not found")
        check("missing: drive engine None", RF._drive_engine(), None)
        check("missing: report has all five keys",
              sorted(r.keys()), ["available", "enabled", "error", "exists", "path"])
    finally:
        _restore(saved)

    # ---- 4. The switch only accepts the agreed words -------------------------------------
    for word, want in (("1", True), ("true", True), ("yes", True), ("on", True), ("ON", True),
                       ("0", False), ("off", False), ("", False), ("maybe", False)):
        RF, saved = _reload(AVIA_DRIVE_TIMES=word)
        try:
            check("switch %r reads %s" % (word, want), RF.DRIVE_TIMES, want)
        finally:
            _restore(saved)

    # ---- 5. The path resolves through config, and the env var wins ------------------------
    import config
    importlib.reload(config)
    check("config publishes the raster path", "FRICTION_RASTER" in config.ALL_PATHS, True)

    with tempfile.TemporaryDirectory() as d:
        chosen = os.path.join(d, "2020_motorized_friction_surface.geotiff")
        open(chosen, "wb").write(b"x")
        RF, saved = _reload(AVIA_FRICTION=chosen, AVIA_DRIVE_TIMES=None)
        try:
            check("AVIA_FRICTION wins over the candidates",
                  os.path.normcase(RF.FRICTION_PATH), os.path.normcase(chosen))
            check("config agrees with the engine",
                  os.path.normcase(str(importlib.import_module("config").FRICTION_RASTER)),
                  os.path.normcase(chosen))
        finally:
            _restore(saved)

    # ---- 6. No hardcoded C:\Avia left in the resolver -------------------------------------
    src = open(os.path.join(HERE, "route_forecast.py"), encoding="utf-8").read()
    body = src.split("def _resolve_friction():", 1)[1].split("FRICTION_PATH = _resolve_friction()", 1)[0]
    code = "\n".join(l for l in body.splitlines() if not l.strip().startswith("#"))
    code = code.split('"""')[2] if code.count('"""') >= 2 else code
    check("resolver reads config, not a drive letter", "_CFG.FRICTION_RASTER" in code, True)

    failed = [c for c in CHECKS if not c[1]]
    for name, ok, got, want in CHECKS:
        if not ok:
            print("FAIL  %s: got %r, wanted %r" % (name, got, want))
    print("%d checks, %d failed" % (len(CHECKS), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
