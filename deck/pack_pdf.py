#!/usr/bin/env python3
"""Render a Meridian pack to A4 PDF with headless Chrome, and stamp it as Avia's.

Why Chrome and not a Python HTML-to-PDF library
-----------------------------------------------
The pack draws its charts in the browser, in inline SVG built by its own script.
A library that parses the HTML never runs that script, so it produces a pack with
the words and none of the figures. Chrome renders the page exactly as the visitor
sees it, which is also the point: the PDF and the page cannot disagree.

Render the SERVER's URL rather than a saved file wherever there is one. A file
opened from disk cannot reach the fonts or any data the page fetches, and a pack
that silently loses a chart is worse than one that fails.

Chrome stamps its own author on the file, so the metadata is rewritten afterwards
and read back to confirm it took. A PDF that goes to a visitor carries Avia
Solutions, never Chromium or Skia.

Usage
-----
    python3 pack_pdf.py http://127.0.0.1:8010/pack/SJC-TPE -o pack.pdf
    python3 pack_pdf.py C:/tmp/pack.html -o pack.pdf --author "Avia Solutions"

Avia Solutions Limited. All rights reserved.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse

AUTHOR = "Avia Solutions"
A4_PT = (595.276, 841.890)          # 210 x 297 mm at 72 points to the inch
A4_TOL = 3.0

# Where Chrome lives. AVIA_CHROME overrides everything, as config should.
CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
    "/opt/pw-browsers/chromium",
]


def find_chrome(explicit=None):
    for c in [explicit, os.environ.get("AVIA_CHROME")]:
        if c and os.path.exists(c):
            return c
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    for c in CANDIDATES:
        if os.path.exists(c):
            return c
    raise SystemExit(
        "No Chrome found. Set AVIA_CHROME to the browser executable, or pass "
        "--chrome. Checked PATH and:\n  " + "\n  ".join(CANDIDATES))


def as_url(target):
    if "://" in target:
        return target
    path = os.path.abspath(target)
    if not os.path.exists(path):
        raise SystemExit("No such file: %s" % path)
    return "file:///" + urllib.parse.quote(path.replace(os.sep, "/"))


def render(target, out, chrome=None, wait_ms=2500, timeout=120):
    """Print the page to PDF. Returns the path, or raises."""
    exe = find_chrome(chrome)
    profile = tempfile.mkdtemp(prefix="avia_pdf_")
    cmd = [exe,
           "--headless=new",
           "--disable-gpu",
           "--no-sandbox",
           "--no-first-run",
           "--no-pdf-header-footer",
           "--user-data-dir=%s" % profile,
           # The page draws its charts from script, so give it time to run
           # before the print. Chrome prints the DOM it has, not the DOM it
           # will have.
           "--virtual-time-budget=%d" % wait_ms,
           "--print-to-pdf=%s" % os.path.abspath(out),
           as_url(target)]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        sys.stderr.write((r.stderr or b"").decode("utf-8", "replace")[-2000:])
        raise SystemExit("Chrome produced no PDF for %s" % target)
    return out, time.time() - t0, os.path.basename(exe)


def stamp(path, author=AUTHOR, title=None):
    """Rewrite the metadata Chrome wrote, then read it back."""
    import pikepdf
    with pikepdf.open(path, allow_overwriting_input=True) as pdf:
        with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
            meta["dc:creator"] = [author]
            meta["xmp:CreatorTool"] = author
            if title:
                meta["dc:title"] = title
        pdf.docinfo["/Author"] = author
        pdf.docinfo["/Creator"] = author
        pdf.docinfo["/Producer"] = author
        if title:
            pdf.docinfo["/Title"] = title
        pdf.save(path)
    return verify(path, author)


def verify(path, author=AUTHOR):
    """Fails loud rather than shipping a pack stamped by the renderer."""
    import pikepdf
    problems = []
    with pikepdf.open(path) as pdf:
        info = {k: str(v) for k, v in pdf.docinfo.items()}
        for key in ("/Author", "/Creator", "/Producer"):
            if info.get(key) != author:
                problems.append("%s is %r, not %r" % (key, info.get(key), author))
        pages = len(pdf.pages)
        sizes = set()
        for pg in pdf.pages:
            box = [float(x) for x in pg.MediaBox]
            sizes.add((round(box[2] - box[0], 1), round(box[3] - box[1], 1)))
        for w, h in sizes:
            if abs(w - A4_PT[0]) > A4_TOL or abs(h - A4_PT[1]) > A4_TOL:
                problems.append("a page is %.0f x %.0f pt, not A4 (%.0f x %.0f)"
                                % (w, h, A4_PT[0], A4_PT[1]))
    return pages, sorted(sizes), problems


def main():
    ap = argparse.ArgumentParser(description=__doc__,
          formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="the pack's URL, or a local .html file")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--chrome", help="browser executable; AVIA_CHROME also sets it")
    ap.add_argument("--author", default=AUTHOR)
    ap.add_argument("--title", help="the PDF title, e.g. 'Meridian - SJC to TPE'")
    ap.add_argument("--wait-ms", type=int, default=2500,
                    help="virtual time given to the page's charts before printing")
    a = ap.parse_args()

    out, secs, exe = render(a.target, a.out, a.chrome, a.wait_ms)
    pages, sizes, problems = stamp(out, a.author, a.title)
    print("wrote %s (%d pages, %.1f KB) in %.1fs with %s"
          % (out, pages, os.path.getsize(out) / 1024.0, secs, exe))
    print("   page size: %s" % ", ".join("%.0f x %.0f pt" % s for s in sizes))
    for p in problems:
        print("   PROBLEM: %s" % p)
    if not problems:
        print("   checks passed: A4 on every page, author and producer are %s"
              % a.author)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
