#!/usr/bin/env python3
"""Embed the Observatory brand faces in a .pptx.

Why
---
PowerPoint has no font fallback list. A deck that asks for Newsreader on a
machine without it gets whatever the reader's PowerPoint decides to substitute,
and the document stops looking like ours. Embedding puts the faces in the file.

Support. Windows PowerPoint has honoured embedded fonts for years. Mac
PowerPoint could not until the 2019 subscription builds; PowerPoint 2016 for
Mac can display an embedded font but cannot embed one, and anything older
ignores them. Google Slides and LibreOffice ignore them too. So embedding
raises the floor, it does not guarantee the outcome: a PDF still does.

Licensing. Newsreader and IBM Plex Mono are both under the SIL Open Font
Licence, which expressly permits the fonts to be "bundled, embedded,
redistributed and/or sold with any software". No permission is needed and none
is implied for any other face: a commercial font's OS/2 fsType bits decide
whether it may be embedded at all, and this module refuses one that says no.

Variable fonts. Google ships Newsreader as a variable font. PowerPoint expects
static TrueType, so a variable source is instanced to the weights the deck uses
before it goes in. Skipping that step is the usual reason an embedded font
renders wrong rather than not at all.

Avia Solutions Limited. All rights reserved.
"""

import argparse
import glob
import json
import os
import re
import shutil
import zipfile

REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
FONT_REL = ("http://schemas.openxmlformats.org/officeDocument/2006/"
            "relationships/font")

# The faces the Observatory renderer asks for, and the styles it actually sets.
BRAND = {
    "Newsreader": {"regular": 400, "bold": 600, "italic": 400},
    "IBM Plex Mono": {"regular": 400},
}

# fsType is a bit field in the OS/2 table. 2 means the font may not be embedded
# at all. 0 is installable embedding, 4 is preview and print, 8 is editable.
FSTYPE_NO_EMBED = 0x0002


def font_store(explicit=None):
    """Where the staged faces live. Config, never a path inside the repo.

    Font binaries are data. They belong on the workstation beside the image
    store, not committed to a tool's repository.
    """
    if explicit:
        return explicit
    if os.environ.get("AVIA_FONT_STORE"):
        return os.environ["AVIA_FONT_STORE"]
    here = os.path.dirname(os.path.abspath(__file__))
    cfg = os.environ.get("AVIA_CONFIG") or os.path.join(here, "avia_config.json")
    if os.path.exists(cfg):
        try:
            with open(cfg) as f:
                conf = json.load(f)
        except ValueError:
            conf = {}
        if conf.get("font_store"):
            return conf["font_store"]
        if conf.get("image_store"):
            # a sensible neighbour of the image store, so one setting covers both
            return os.path.join(os.path.dirname(conf["image_store"]),
                                "deck_fonts")
    raise SystemExit(
        "No font_store set. Add it to avia_config.json, for example\n"
        '    "font_store": "C:/Avia/deck_fonts"\n'
        "or set AVIA_FONT_STORE. Font binaries are data and must not live in "
        "the tool repo.")


def _face_files(src_dir):
    """Every TrueType or OpenType file under a directory."""
    out = []
    for ext in ("ttf", "otf", "TTF", "OTF"):
        out += glob.glob(os.path.join(src_dir, "**", "*." + ext), recursive=True)
    return sorted(set(out))


def _family(path):
    from fontTools.ttLib import TTFont
    f = TTFont(path, lazy=True)
    try:
        for rec in f["name"].names:
            if rec.nameID == 16:            # typographic family, if present
                return str(rec)
        for rec in f["name"].names:
            if rec.nameID == 1:
                return str(rec)
    finally:
        f.close()
    return os.path.splitext(os.path.basename(path))[0]


def _embeddable(path):
    """(ok, reason). Refuses a font whose own licence bits forbid embedding."""
    from fontTools.ttLib import TTFont
    f = TTFont(path, lazy=True)
    try:
        fs = getattr(f.get("OS/2"), "fsType", 0) or 0
    finally:
        f.close()
    if fs & FSTYPE_NO_EMBED:
        return False, "the font's own fsType bits forbid embedding"
    return True, "fsType %d" % fs


def _is_variable(path):
    from fontTools.ttLib import TTFont
    f = TTFont(path, lazy=True)
    try:
        return "fvar" in f
    finally:
        f.close()


def prepare(src_dir, out_dir, brand=None):
    """Turn a folder of downloaded fonts into the static faces a deck needs.

    Returns {family: {style: path}}. Variable sources are instanced; static
    sources are copied through.
    """
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    brand = brand or BRAND
    os.makedirs(out_dir, exist_ok=True)
    found, report = {}, []

    for path in _face_files(src_dir):
        fam = _family(path)
        if fam not in brand:
            continue
        ok, why = _embeddable(path)
        if not ok:
            report.append(("skip", os.path.basename(path), why))
            continue
        italic = bool(re.search(r"italic", os.path.basename(path), re.I))
        for style, weight in brand[fam].items():
            if (style == "italic") != italic:
                continue
            dest = os.path.join(out_dir, "%s-%s.ttf"
                                % (fam.replace(" ", ""), style))
            if _is_variable(path):
                f = TTFont(path)
                axes = {"wght": weight}
                axes = {k: v for k, v in axes.items()
                        if k in {a.axisTag for a in f["fvar"].axes}}
                inst = instancer.instantiateVariableFont(f, axes,
                                                         updateFontNames=False)
                inst.save(dest)
                report.append(("instanced", os.path.basename(dest),
                               "%s wght %d" % (fam, weight)))
            else:
                shutil.copyfile(path, dest)
                report.append(("copied", os.path.basename(dest), fam))
            found.setdefault(fam, {})[style] = dest

    missing = [f for f in brand if f not in found]
    return found, report, missing


def embed(pptx_path, faces, out_path=None):
    """Write the faces into the package. faces: {family: {style: ttf path}}.

    Everything is done on the packed XML because python-pptx models no part of
    this. The children of p:presentation are in a fixed schema order, so the
    font list is inserted after notesSz rather than appended: moving an element
    in that element is enough to make PowerPoint refuse the file.
    """
    out_path = out_path or pptx_path
    tmp = out_path + ".tmp"

    plan, rid = [], 900          # high ids, clear of anything python-pptx wrote
    for family, styles in sorted(faces.items()):
        entry = {"family": family, "styles": []}
        for style in ("regular", "bold", "italic", "boldItalic"):
            path = styles.get(style)
            if not path or not os.path.exists(path):
                continue
            rid += 1
            entry["styles"].append((style, "rId%d" % rid, path,
                                    "font%d.fntdata" % rid))
        if entry["styles"]:
            plan.append(entry)
    if not plan:
        raise ValueError("no usable font files to embed")

    with zipfile.ZipFile(pptx_path) as zin, \
            zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        names = set(zin.namelist())
        for item in zin.infolist():
            data = zin.read(item.filename)

            if item.filename == "[Content_Types].xml":
                xml = data.decode("utf-8")
                if 'Extension="fntdata"' not in xml:
                    xml = xml.replace(
                        "<Types ",
                        "<Types ", 1)
                    xml = re.sub(
                        r"(<Types[^>]*>)",
                        r'\1<Default Extension="fntdata" '
                        r'ContentType="application/x-fontdata"/>', xml, count=1)
                data = xml.encode("utf-8")

            elif item.filename == "ppt/presentation.xml":
                xml = data.decode("utf-8")
                lst = ["<p:embeddedFontLst>"]
                for entry in plan:
                    lst.append('<p:embeddedFont><p:font typeface="%s" '
                               'pitchFamily="18" charset="0"/>'
                               % _esc(entry["family"]))
                    for style, rel, _p, _f in entry["styles"]:
                        lst.append('<p:%s r:id="%s"/>' % (style, rel))
                    lst.append("</p:embeddedFont>")
                lst.append("</p:embeddedFontLst>")
                block = "".join(lst)
                # schema order: ... sldSz, notesSz, smartTags, embeddedFontLst
                if "<p:embeddedFontLst>" not in xml:
                    m = re.search(r"<p:notesSz[^>]*/>", xml)
                    if not m:
                        raise ValueError("no p:notesSz in presentation.xml, so "
                                         "the insertion point is unknown")
                    xml = xml[:m.end()] + block + xml[m.end():]
                # tell PowerPoint the fonts are whole faces, not subsets.
                # python-pptx's template already sets saveSubsetFonts, and
                # adding it again makes the XML invalid, so set each attribute
                # only where it is absent.
                m = re.search(r"<p:presentation\b[^>]*>", xml)
                tag = m.group(0)
                new = tag
                for attr, val in (("embedTrueTypeFonts", "1"),
                                  ("saveSubsetFonts", "0")):
                    if re.search(r'\b%s="' % attr, new):
                        new = re.sub(r'\b%s="[^"]*"' % attr,
                                     '%s="%s"' % (attr, val), new)
                    else:
                        new = new.replace("<p:presentation",
                                          '<p:presentation %s="%s"'
                                          % (attr, val), 1)
                xml = xml.replace(tag, new, 1)
                data = xml.encode("utf-8")

            elif item.filename == "ppt/_rels/presentation.xml.rels":
                xml = data.decode("utf-8")
                add = "".join(
                    '<Relationship Id="%s" Type="%s" Target="fonts/%s"/>'
                    % (rel, FONT_REL, fn)
                    for entry in plan for _s, rel, _p, fn in entry["styles"])
                xml = xml.replace("</Relationships>", add + "</Relationships>")
                data = xml.encode("utf-8")

            zout.writestr(item, data)

        for entry in plan:
            for _style, _rel, path, fname in entry["styles"]:
                target = "ppt/fonts/" + fname
                if target in names:
                    continue
                with open(path, "rb") as fh:
                    zout.writestr(target, fh.read())

    shutil.move(tmp, out_path)
    return out_path


def _esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def check(pptx_path):
    """What a reader will actually find in the package."""
    out = []
    with zipfile.ZipFile(pptx_path) as z:
        fonts = [n for n in z.namelist() if n.startswith("ppt/fonts/")]
        pres = z.read("ppt/presentation.xml").decode("utf-8")
        ct = z.read("[Content_Types].xml").decode("utf-8")
        rels = z.read("ppt/_rels/presentation.xml.rels").decode("utf-8")
        declared = re.findall(r'<p:font typeface="([^"]+)"', pres)
        used = set()
        for n in z.namelist():
            if n.startswith("ppt/slides/slide") and n.endswith(".xml"):
                used |= set(re.findall(r'typeface="([^"]+)"',
                                       z.read(n).decode("utf-8")))
        out.append(("font parts", len(fonts)))
        out.append(("declared", ", ".join(declared) or "none"))
        out.append(("used on slides", ", ".join(sorted(used)) or "none"))
        out.append(("content type", "yes" if 'Extension="fntdata"' in ct else "MISSING"))
        out.append(("relationships", len(re.findall(FONT_REL, rels))))
        missing = sorted(u for u in used if u not in declared)
        out.append(("used but not embedded", ", ".join(missing) or "none"))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prepare", help="instance and stage the brand faces")
    p.add_argument("src", help="folder of downloaded font files")
    p.add_argument("-o", "--out", default=None,
                   help="defaults to font_store from avia_config.json")

    e = sub.add_parser("embed", help="write staged faces into a .pptx")
    e.add_argument("pptx")
    e.add_argument("--fonts", default=None,
                   help="defaults to font_store from avia_config.json")
    e.add_argument("-o", "--out")

    c = sub.add_parser("check", help="report what is in the package")
    c.add_argument("pptx")

    a = ap.parse_args()
    if a.cmd == "prepare":
        out = font_store(a.out)
        found, report, missing = prepare(a.src, out)
        for what, name, why in report:
            print("  %-10s %-34s %s" % (what, name, why))
        for fam in missing:
            print("  MISSING    %s: no file for this family in %s" % (fam, a.src))
        print("%d family(ies) staged in %s" % (len(found), out))
    elif a.cmd == "embed":
        store = font_store(a.fonts)
        faces = staged(store)
        if not faces:
            raise SystemExit("no staged fonts in %s. Run prepare first." % store)
        embed(a.pptx, faces, a.out)
        for k, v in check(a.out or a.pptx):
            print("  %-24s %s" % (k, v))
    elif a.cmd == "check":
        for k, v in check(a.pptx):
            print("  %-24s %s" % (k, v))


def staged(fonts_dir):
    """Read back what prepare() wrote."""
    faces = {}
    for path in glob.glob(os.path.join(fonts_dir, "*.ttf")):
        base = os.path.splitext(os.path.basename(path))[0]
        if "-" not in base:
            continue
        fam, style = base.rsplit("-", 1)
        for known in BRAND:
            if known.replace(" ", "") == fam:
                faces.setdefault(known, {})[style] = path
    return faces


if __name__ == "__main__":
    main()
