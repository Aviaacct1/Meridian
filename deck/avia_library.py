#!/usr/bin/env python3
"""The Observatory brand library: ingest, metadata and validation.

Every frame in the library carries its record in two places, deliberately:

  1. Inside the file. PNG text chunks and JPEG EXIF, so a frame that is emailed,
     copied or dragged out of the folder still says what it is and who cleared it.
  2. In brand_library/library.json, which is what the deck generator reads.

Losing provenance is how a library turns into a folder of pictures nobody dares
publish. Both copies are written on ingest and checked on validate.

Usage
-----
    python3 avia_library.py ingest  drop/*.png --sheet collection1.tsv
    python3 avia_library.py ingest  drop/06.png --family field \\
            --subject taxiway-geometry --title "Navigation" --collection 1
    python3 avia_library.py validate
    python3 avia_library.py list [--family field]
    python3 avia_library.py plan                # the export list still wanted

Avia Solutions Limited. All rights reserved.
"""

import argparse
import glob
import json
import os
import re
import shutil
import sys
from datetime import date

FAMILIES = ("field", "operations", "globe", "instruments")
REGIONS = ("europe", "north-america", "latin-america", "mena", "south-asia",
           "apac", "pacific", "africa", "any")
# "any" is for the atmospheric frames in the Globe family: a wing over cloud, a
# cloudscape, contrails at altitude. They belong to no region and are usable on
# any deck, so they must not sit in a region's pool and crowd out its own frame.
EXTS = (".png", ".jpg", ".jpeg", ".webp")

AUTHOR = "Avia Solutions"
COPYRIGHT = "Copyright Avia Solutions Limited. All rights reserved."
MIN_LONG_EDGE = 1400
TARGET_ASPECT = 1.5          # 3:2
ASPECT_TOL = 0.22

# Exposure: a gross-failure net, not a judgement of quality.
#
# This check has been recalibrated three times, and each time a new batch showed
# the previous rule was measuring the wrong thing. It first tested a headline
# zone the renderer never uses, because type sits on a navy panel beside the
# photograph rather than over it. It then used whole-frame median, which on a
# night frame measures the ocean, the sky and the unlit asphalt, so it rejected
# an East Asia globe and a runway threshold that are among the best frames held.
#
# The conclusion is that no single luminance statistic decides whether a frame
# is good. So the check no longer tries. It measures lit energy, the share of
# the frame that is clearly lit multiplied by how bright that lit part is, and
# the floor is set at 60 per cent of the weakest frame already in each family.
# That catches what is indefensible - a frame at 271 that is black with a smudge
# - and stays silent on everything that is a matter of taste. The measurements
# are written into every frame's record so they can be sorted and reviewed;
# the eye decides, the net only stops the obviously broken.
LIT_FLOOR = {
    "globe":        403,
    "field":        653,
    "operations":  1821,
    "instruments":  418,
}
MIN_P95 = 40      # a frame with no highlight at all has no focal point


def here():
    return os.path.dirname(os.path.abspath(__file__))


def lib_dir(root=None):
    """Where the brand library lives.

    An explicit root wins. Otherwise AVIA_BRAND_LIBRARY, then AVIA_ASSETS/brand_library,
    then the folder beside this module, which is where it sat until 8 August 2026.

    The last of those is kept only so an unmoved machine still works, and it is the reason
    the wrong path in avia_config.json went unnoticed: the configured
    C:/Avia/deck_generator/observatory_library did not exist, and this fell back to the
    folder next to the code, so the library resolved by accident rather than by setting.
    """
    if root:
        return root
    env = os.environ.get("AVIA_BRAND_LIBRARY")
    if env:
        return env
    assets = os.environ.get("AVIA_ASSETS")
    if assets:
        return os.path.join(assets, "brand_library")
    default = os.path.join("C:" + os.sep, "assets", "brand_library")
    if os.path.isdir(default):
        return default
    return os.path.join(here(), "brand_library")


def manifest_path(root=None):
    return os.path.join(lib_dir(root), "library.json")


def load(root=None):
    p = manifest_path(root)
    if not os.path.exists(p):
        return {"_schema": "avia observatory brand library v1", "frames": {}}
    with open(p) as f:
        return json.load(f)


def save(m, root=None):
    with open(manifest_path(root), "w") as f:
        json.dump(m, f, indent=1, sort_keys=True)


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(s).lower())).strip("-")


def canonical_name(family, subject, ext=".png"):
    return "%s-%s%s" % (family, slug(subject), ext)


# ---------------------------------------------------------------------------
def write_file_metadata(src, dest, meta):
    """Embed the record in the file itself, writing src to dest in one pass.

    Written rather than copied-then-rewritten: some mounts refuse to truncate a
    file that already exists, and a half-written library frame is worse than none.
    """
    from PIL import Image
    ext = os.path.splitext(dest)[1].lower()
    desc = "%s. Observatory %s family. %s" % (
        meta.get("title") or meta["subject"], meta["family"],
        meta.get("use", ""))
    if ext == ".png":
        from PIL.PngImagePlugin import PngInfo
        im = Image.open(src)
        info = PngInfo()
        info.add_text("Title", meta.get("title") or meta["subject"])
        info.add_text("Author", AUTHOR)
        info.add_text("Copyright", COPYRIGHT)
        info.add_text("Description", desc)
        info.add_text("Source", meta.get("cleared", ""))
        info.add_text("Software", "Avia Observatory brand library")
        info.add_text("Comment", json.dumps(
            {k: v for k, v in meta.items() if k != "file"}, sort_keys=True))
        im.save(dest, pnginfo=info)
        return "png-text"
    if ext in (".jpg", ".jpeg"):
        shutil.copy2(src, dest)
        try:
            import piexif
            exif = {"0th": {piexif.ImageIFD.Artist: AUTHOR.encode(),
                            piexif.ImageIFD.Copyright: COPYRIGHT.encode(),
                            piexif.ImageIFD.ImageDescription: desc.encode()},
                    "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
            piexif.insert(piexif.dump(exif), dest)
            return "exif"
        except ImportError:
            return "exif-skipped, piexif not installed"
    shutil.copy2(src, dest)
    return "none"


def _divider_scrim(w, h):
    """The renderer's own multiply gradient, as a per-pixel multiplier."""
    import numpy as np
    yy, xx = np.mgrid[0:h, 0:w]
    t = np.clip(xx / float(w) * 0.5 + yy / float(h) * 0.5, 0, 1)
    a = np.where(t <= 0.6, 0.58 + (0.08 - 0.58) * (t / 0.6),
                 0.08 + (0.30 - 0.08) * ((t - 0.6) / 0.4))
    return 1.0 - a


def luma(path):
    """Luminance as supplied, and as the renderer will actually show it."""
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)
    y = 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]
    h, w = y.shape
    lit = y > 40
    return {"median": float(np.median(y)), "mean": float(y.mean()),
            "treated": float(np.median(y * _divider_scrim(w, h))),
            "p95": float(np.percentile(y, 95)),
            "lit_area": float(lit.mean() * 100),
            "lit_mean": float(y[lit].mean()) if lit.any() else 0.0,
            "energy": float(lit.mean() * 100 * (y[lit].mean() if lit.any() else 0.0)),
            "under12": float((y < 12).mean() * 100)}


def check_image(path, family=None):
    """Returns (ok, notes). Aspect, size and exposure, per the sourcing brief."""
    from PIL import Image
    notes = []
    w, h = Image.open(path).size
    if max(w, h) < MIN_LONG_EDGE:
        notes.append("long edge %d px, under the %d px floor" % (max(w, h), MIN_LONG_EDGE))
    ar = w / float(h)
    if abs(ar - TARGET_ASPECT) > ASPECT_TOL:
        notes.append("aspect %.2f:1, not 3:2 (crop before use)" % ar)
    if h > w:
        notes.append("portrait: every slot in the deck is landscape")
    if family in LIT_FLOOR:
        L = luma(path)
        if L["energy"] < LIT_FLOOR[family]:
            notes.append("lit energy %.0f, below the %s net of %d: too little of "
                         "the frame carries any picture at all"
                         % (L["energy"], family, LIT_FLOOR[family]))
        if L["p95"] < MIN_P95:
            notes.append("no highlight anywhere: brightest 5%% reaches only %.0f"
                         % L["p95"])
    return (not notes), notes


# ---------------------------------------------------------------------------
def ingest(src, family, subject, title=None, region=None, collection=None,
           restrict=None, restrict_note=None, use=None, cleared=None,
           root=None, dry_run=False):
    if family not in FAMILIES:
        sys.exit("family must be one of %s" % (FAMILIES,))
    if region and region not in REGIONS:
        sys.exit("region must be one of %s" % (REGIONS,))
    if family == "globe" and not region:
        sys.exit("a globe frame needs --region (or --region any): the cover "
                 "keys off it")

    ext = os.path.splitext(src)[1].lower()
    if ext not in EXTS:
        sys.exit("unsupported file type %s" % ext)
    name = canonical_name(family, subject, ext)
    dest_dir = os.path.join(lib_dir(root), family)
    dest = os.path.join(dest_dir, name)

    ok, notes = check_image(src, family)
    meta = {
        "file": "%s/%s" % (family, name),
        "family": family,
        "subject": slug(subject),
        "title": title or subject.replace("-", " ").title(),
        "collection": collection,
        "region": region,
        "use": use or USE_BY_FAMILY[family],
        "cleared": cleared or "Observatory library%s, Avia Solutions, %s" % (
            ", Collection %s" % collection if collection else "", date.today().isoformat()),
        "author": AUTHOR,
        "ingested": date.today().isoformat(),
        "checks": notes or ["ok"],
        "exposure": {k: round(v, 1) for k, v in luma(src).items()},
    }
    if restrict:
        meta["restrict"] = restrict
        meta["restrict_note"] = restrict_note or "Not auto-selected."
    if dry_run:
        return meta, dest, ok

    os.makedirs(dest_dir, exist_ok=True)
    if os.path.exists(dest):
        sys.exit("%s already exists. Remove it first, or choose a new subject."
                 % dest)
    meta["embedded"] = write_file_metadata(src, dest, meta)
    m = load(root)
    m["frames"][meta["file"]] = meta
    save(m, root)
    return meta, dest, ok


USE_BY_FAMILY = {
    "field": "Report covers, network and capacity sections, full-bleed dividers.",
    "operations": "Dashboard headers, live-status areas, operations section openers.",
    "globe": "Flagship covers, first-chapter openers, closing pages. Region-keyed.",
    "instruments": "Methodology sections, about and provenance pages, appendices.",
}


def validate(root=None):
    m = load(root)
    problems = []
    for rel, meta in sorted(m["frames"].items()):
        p = os.path.join(lib_dir(root), rel)
        if not os.path.exists(p):
            problems.append("%s: in the manifest, missing on disk" % rel)
            continue
        ok, notes = check_image(p, meta.get("family"))
        if not ok:
            problems.append("%s: %s" % (rel, "; ".join(notes)))
        if meta["family"] == "globe" and not meta.get("region"):
            problems.append("%s: globe frame with no region" % rel)
        if not meta.get("cleared"):
            problems.append("%s: no rights record" % rel)
    for family in FAMILIES:
        d = os.path.join(lib_dir(root), family)
        if not os.path.isdir(d):
            continue
        for p in glob.glob(os.path.join(d, "*")):
            if os.path.splitext(p)[1].lower() not in EXTS:
                continue
            rel = "%s/%s" % (family, os.path.basename(p))
            if rel not in m["frames"]:
                problems.append("%s: on disk, not in the manifest" % rel)
    counts = {f: len([1 for r in m["frames"] if r.startswith(f + "/")])
              for f in FAMILIES}
    return problems, counts


def coverage(root=None):
    """Where the library is thin, against the slots a route deck opens."""
    m = load(root)
    counts = {f: [] for f in FAMILIES}
    regions = {r: 0 for r in REGIONS}
    for rel, meta in m["frames"].items():
        if meta.get("restrict"):
            continue
        counts[meta["family"]].append(rel)
        if meta["family"] == "globe" and meta.get("region"):
            regions[meta["region"]] += 1
    need = {"field": 4, "operations": 3, "instruments": 4, "globe": 2}
    lines = []
    for f in FAMILIES:
        have = len(counts[f])
        lines.append("  %-12s %d held, %d wanted for a repeat-free deck%s"
                     % (f, have, need[f], "" if have >= need[f] else "   SHORT"))
    lines.append("  globe by region, two wanted each so cover and closing differ:")
    for r in REGIONS:
        lines.append("     %-14s %d%s" % (r, regions[r],
                                          "" if regions[r] >= 2 else "   SHORT"))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# The 20-frame Collection 1 contact sheet, and where each frame belongs.
# Export each at full size with the name in the second column.
PLAN = [
    ("01", "The Meridian",       "globe",       "meridian-wing-sunrise",     None, "Atmospheric long view. Cover alternative."),
    ("02", "Global Systems",     "globe",       "europe-night-wide",         "europe", "HELD"),
    ("03", "Observation",        "instruments", "transit-telescope",         None, ""),
    ("04", "Infrastructure",     "field",       "tower-apron-dusk",          None, ""),
    ("05", "The Horizon",        "instruments", "mountain-observatory",      None, "Provenance and heritage pages."),
    ("06", "Navigation",         "field",       "taxiway-geometry",          None, "The strongest Field composition on the sheet."),
    ("07", "Atmospheric Layers", "globe",       "cloud-tops",                None, ""),
    ("08", "Data & Evidence",    "instruments", "plotted-chart-pen",         None, "Methodology openers."),
    ("09", "Long View",          "globe",       "sun-glint-contrails",       None, ""),
    ("10", "Meteorology",        "globe",       "cyclone-from-space",        None, "Use sparingly: reads as disruption."),
    ("11", "Precision",          "instruments", "brass-sector-scale",        None, ""),
    ("12", "Route Networks",     "globe",       "route-network-map",         None, "A diagram, not a photograph. Mood use only."),
    ("13", "Research",           "instruments", "desk-books-lamp",           None, ""),
    ("14", "Take-off",           "field",       "rotation-dusk",             None, ""),
    ("15", "Continents",         "globe",       "earth-limb-coastline",      None, "Confirm the region before filing."),
    ("16", "Night Operations",   "operations",  "apron-night-wet",           None, ""),
    ("17", "Instruments",        "instruments", "cockpit-gauges",            None, ""),
    ("18", "Cartography",        "instruments", "chart-drawing-pens",        None, ""),
    ("19", "Signals",            "operations",  "radar-head-sunset",         None, ""),
    ("20", "Perspective",        "globe",       "contrail-altitude",         None, ""),
]


def plan_text(root=None):
    m = load(root)
    held = set(m["frames"])
    out = ["Collection 1: export each frame at full size with this filename.",
           "",
           "| # | Frame | Family | Filename | Status |",
           "|---|---|---|---|---|"]
    for num, title, family, subject, region, note in PLAN:
        fn = canonical_name(family, subject)
        rel = "%s/%s" % (family, fn)
        status = "held" if rel in held else "**wanted**"
        out.append("| %s | %s | %s | `%s` | %s |" % (num, title, family, fn, status))
    out.append("")
    out.append("Globe frames also need a region: europe, north-america, "
               "latin-america, mena, apac or africa.")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("ingest")
    i.add_argument("src")
    i.add_argument("--family", required=True, choices=FAMILIES)
    i.add_argument("--subject", required=True)
    i.add_argument("--title")
    i.add_argument("--region", choices=REGIONS)
    i.add_argument("--collection")
    i.add_argument("--restrict")
    i.add_argument("--restrict-note")
    i.add_argument("--cleared")
    i.add_argument("--dry-run", action="store_true")

    sub.add_parser("validate")
    sub.add_parser("plan")
    sub.add_parser("coverage")
    l = sub.add_parser("list")
    l.add_argument("--family", choices=FAMILIES)

    a = ap.parse_args()
    if a.cmd == "ingest":
        meta, dest, ok = ingest(a.src, a.family, a.subject, a.title, a.region,
                                a.collection, a.restrict, a.restrict_note,
                                cleared=a.cleared, dry_run=a.dry_run)
        print("%s -> %s%s" % (os.path.basename(a.src), meta["file"],
                              "" if ok else "   CHECK: " + "; ".join(meta["checks"])))
    elif a.cmd == "validate":
        problems, counts = validate()
        print("LIBRARY: " + ", ".join("%s %d" % (k, v) for k, v in counts.items()))
        if problems:
            print("%d problem(s):" % len(problems))
            for p in problems:
                print("   " + p)
        else:
            print("clean")
    elif a.cmd == "coverage":
        print(coverage())
    elif a.cmd == "plan":
        print(plan_text())
    elif a.cmd == "list":
        m = load()
        for rel, meta in sorted(m["frames"].items()):
            if a.family and meta["family"] != a.family:
                continue
            print("%-52s %-12s %-14s %s" % (
                rel, meta["family"], meta.get("region") or "-",
                "RESTRICTED: " + meta.get("restrict_note", "")
                if meta.get("restrict") else meta.get("title", "")))


if __name__ == "__main__":
    main()
