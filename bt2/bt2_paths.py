#!/usr/bin/env python3
r"""BT2 path resolution. One place, so a host is described by environment and never by code.

Written 8 August 2026. Every BT2 script had its paths hardcoded to a Cowork session mount,
/sessions/wizardly-peaceful-tesla/mnt/..., which was correct in the chat that wrote them and
resolves on neither the Dev PC nor the workstation. Twelve files, twenty-one occurrences, eight
distinct targets. The practical effect is that BT2 could not be run at all, and BT2 produces the
published accuracy claims of 89% within +-20% and 82% within +-10%.

That matters beyond the inconvenience. A claim that cannot be reproduced on demand is a claim that
cannot be defended, and this one appears on the website and in client decks.

Usage, replacing the hardcoded constants at the top of each script:

    from bt2_paths import BT2, OAG, SABRE, APP, US_MARKET, mct_master

Every resolver takes an environment override first, so nothing needs editing to move machines:

    AVIA_BT2_DIR       the bt2 folder itself          default: the folder this module is in
    AVIA_LOCAL_CACHE   the data root                  E:\Avia on the workstation, C:\Avia on the Dev PC
    AVIA_OAG_DUCKDB    the OAG store                  default: <data root>\oag.duckdb
    AVIA_SABRE_DUCKDB  the Sabre store                default: <data root>\sabre.duckdb
    AVIA_APP_DIR       the Meridian engine folder     default: found by looking for cortex_app.py
    AVIA_US_MARKET     the US DOT extract folder      default: <data root>\Usmarket data
    AVIA_MCT_MASTER    the MCT master workbook        default: <data root>\MCT Master List.xlsx

Resolvers return None rather than a wrong path when they cannot find something, and the loud
variants stop with the list of places tried. A path resolver that guesses is worse than one that
fails, because the run continues against the wrong data.

BT2 IS NOT A STANDALONE MODEL. bt2_capture imports the QSI connection builder from the Meridian
engine, so APP has to resolve for the capture stage to run at all. That dependency is the reason
BT2 cannot simply replace the engine: it consumes it.

Avia Solutions Limited. All rights reserved.
"""
import os

BT2 = os.environ.get("AVIA_BT2_DIR") or os.path.dirname(os.path.abspath(__file__))

# Conventional data roots, in the order a host is likely to use them. E: first because the
# workstation is the run host and its single data root is E:\Avia; see the naming and structure
# register. The bt2 folder's own parent is last, because bt2 sits beside the stores today.
_ROOTS = [
    os.environ.get("AVIA_LOCAL_CACHE"),
    os.path.join("E:" + os.sep, "Avia"),
    os.path.join("C:" + os.sep, "Avia"),
    os.path.dirname(BT2),
]


def _first_existing(*paths):
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


def _in_roots(name, env=None):
    return _first_existing(os.environ.get(env) if env else None,
                           *[os.path.join(r, name) for r in _ROOTS if r])


OAG = _in_roots("oag.duckdb", "AVIA_OAG_DUCKDB")
SABRE = _in_roots("sabre.duckdb", "AVIA_SABRE_DUCKDB")
US_MARKET = _in_roots("Usmarket data", "AVIA_US_MARKET")


def mct_master():
    """The MCT master workbook. OAG stopped supplying these, so Avia owns the master and it
    changes slowly. Returned by call rather than at import, because most stages do not need it
    and a missing workbook should not stop them loading."""
    return _in_roots("MCT Master List.xlsx", "AVIA_MCT_MASTER")


def find_app(loud=True):
    """The Meridian engine folder, the one holding cortex_app.py.

    Found by landmark, never by counting directories up. Four modules in the deck renderer were
    resolving a sibling folder by folder depth and every one of them broke when the renderer moved
    a single level on 8 August, including the live entry point.
    """
    env = os.environ.get("AVIA_APP_DIR")
    if env and os.path.isfile(os.path.join(env, "cortex_app.py")):
        return env
    tried = []
    for root in (os.path.join("C:" + os.sep, "src", "meridian"),
                 os.path.join("D:" + os.sep, "src", "meridian"),
                 os.path.join("C:" + os.sep, "AviaDev"),
                 os.path.dirname(BT2)):
        cand = os.path.join(root, "app")
        tried.append(cand)
        if os.path.isfile(os.path.join(cand, "cortex_app.py")):
            return cand
    if loud:
        raise SystemExit(
            "bt2_paths: cannot find the Meridian engine folder, the one holding cortex_app.py.\n"
            "Looked in:\n  " + "\n  ".join(tried) + "\n"
            "Set AVIA_APP_DIR. BT2's capture stage imports the QSI connection builder.")
    return None


APP = find_app(loud=False)


def require(**named):
    """Stop with a readable message naming everything missing, rather than one at a time.

        require(OAG=OAG, APP=APP)
    """
    missing = [k for k, v in named.items() if not v]
    if missing:
        raise SystemExit(
            "bt2: cannot resolve %s on this machine.\n"
            "Set the matching variable, or AVIA_LOCAL_CACHE to the data root "
            "(E:\\Avia on the workstation, C:\\Avia on the Dev PC)."
            % ", ".join(missing))


if __name__ == "__main__":
    for k, v in (("BT2", BT2), ("OAG", OAG), ("SABRE", SABRE),
                 ("APP", APP), ("US_MARKET", US_MARKET), ("MCT", mct_master())):
        print("  %-10s %s" % (k, v or "NOT FOUND"))
