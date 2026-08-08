#!/usr/bin/env python3
r"""
Avia Solutions - where the deck renderer finds the engine.
==========================================================
One resolver, so a folder move cannot break the renderer in three different ways.

Written 8 August 2026, when the renderer moved from
    <project>\Deck Generator\v4
to
    <repo>\deck
and four files turned out to be finding the engine folder by counting directories up
from their own location, each in a slightly different way:

  * run_observatory_pitch.py  went two levels up and appended "app". At the new depth
    that resolves to C:\app. This is the live Observatory entry point, so the move would
    have broken deck generation, not just a test.
  * test_visual_layer.py      the same, and it failed loudly on import, which is how the
    other three were found.
  * deck_figures.py           tried two relative candidates and then a hardcoded
    C:\AviaDev\app, which works and breaks point 4 of the tool standard.
  * forecast_spec.py          looked for its own contract file two levels up, which was
    already wrong before the move.

Counting folders encodes the layout in every file that does it. Looking for a landmark
does not, so the next move costs nothing.

The landmark is cortex_app.py, which is the service and is the one file guaranteed to sit
in the engine folder.
"""
import os
import sys

LANDMARK = "cortex_app.py"


def engine_dir(start=None, levels=4):
    """The engine folder (the one holding cortex_app.py), or None.

    Walks up from `start`, or from this module, trying <parent>/app at each level. Also
    accepts AVIA_APP_DIR for a layout that does not put the engine beside the renderer.
    Returns None rather than raising, so a caller can decide whether it is fatal; use
    require_engine_dir() where it is.
    """
    env = os.environ.get("AVIA_APP_DIR")
    if env and os.path.isfile(os.path.join(env, LANDMARK)):
        return os.path.abspath(env)
    here = os.path.abspath(start or os.path.dirname(os.path.abspath(__file__)))
    for cand in _candidates(here, levels):
        if os.path.isfile(os.path.join(cand, LANDMARK)):
            return cand
    return None


def _candidates(here, levels):
    seen = []
    d = here
    for _ in range(max(1, levels)):
        d = os.path.dirname(d)
        if not d or d in (os.path.dirname(d),):        # reached the drive root
            break
        for c in (os.path.join(d, "app"), d):
            c = os.path.abspath(c)
            if c not in seen:
                seen.append(c)
    return seen


def require_engine_dir(start=None, who="the deck renderer"):
    """engine_dir(), but a miss says where it looked and stops.

    A fallback must report. The reason this module exists is that a path assumption
    failed quietly in one place and loudly in another, and the loud one is the only
    reason anybody noticed.
    """
    d = engine_dir(start)
    if d:
        return d
    here = os.path.abspath(start or os.path.dirname(os.path.abspath(__file__)))
    raise SystemExit(
        "%s cannot find the engine folder, the one holding %s.\n"
        "Looked, from %s upwards:\n  %s\n"
        "Set AVIA_APP_DIR if the engine is not beside the renderer."
        % (who, LANDMARK, here, "\n  ".join(_candidates(here, 4))))


def on_path(start=None, who="the deck renderer"):
    """Put the engine folder and the renderer folder on sys.path, engine first."""
    app = require_engine_dir(start, who)
    renderer = os.path.dirname(os.path.abspath(__file__))
    for p in (renderer, app):
        if p not in sys.path:
            sys.path.insert(0, p)
    return app


if __name__ == "__main__":
    print("renderer:", os.path.dirname(os.path.abspath(__file__)))
    print("engine:  ", engine_dir() or "NOT FOUND")
