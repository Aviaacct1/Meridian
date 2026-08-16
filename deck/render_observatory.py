#!/usr/bin/env python3
"""Renderer: The Aviation Observatory / Meridian style, HTML and PDF.

Reads a deck spec (see deck_spec.py) and emits a 1920 x 1080 deck in the
Observatory house style: Newsreader for display and body, IBM Plex Mono for
labels and figures, dark navy section dividers, warm off-white content pages,
gold accents, hairline rules instead of filled table headers.

    python3 render_observatory.py                 standalone HTML, opens anywhere
    python3 render_observatory.py --dc            the .dc.html viewer wrapper
    python3 render_observatory.py --pdf           HTML then PDF via headless Chrome

The PDF step needs a Chrome or Chromium binary. It is not available in a Cowork
sandbox, so run it on the workstation:

    chrome --headless --disable-gpu --no-pdf-header-footer \\
           --print-to-pdf=deck.pdf --virtual-time-budget=10000 deck.html

Avia Solutions Limited. All rights reserved.
"""

import base64
import html
import mimetypes
import os
import shutil
import subprocess
import sys

import deck_spec as S

# --- palette ---------------------------------------------------------------
DARK_BG = "#0F1B28"
DARK_INK = "#F4F1EA"
DARK_MUTE = "#9AA7B3"
DARK_LABEL = "#7D8B98"
DARK_RULE = "#2A3A49"
DARK_DIM = "#5A6470"
GOLD = "#D4A249"
GOLD_2 = "#E7C079"

LIGHT_BG = "#E7E4DD"
INK = "#141C25"
MUTE = "#5A6470"
LABEL = "#6B7480"
RULE = "#D8D2C4"
RULE_2 = "#C9C2B2"
GOLD_D = "#B8862F"
CAUTION = "#8A3A2A"
POSITIVE = "#3F6B4A"

SERIF = "'Newsreader',serif"
MONO = "'IBM Plex Mono',monospace"

W, H = 1920, 1080

FONTS = ("https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@"
         "0,6..72,300;0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,300;"
         "1,6..72,400&family=IBM+Plex+Mono:wght@400;500&display=swap")


def e(t):
    return html.escape(str(t)) if t is not None else ""


MAX_EMBED_PX = 1800        # nothing renders wider than this at 1920 x 1080


def _data_uri(path, photo=False, max_px=MAX_EMBED_PX):
    """Base64 data URI. Photographs are re-encoded; line art is left alone.

    A PNG photograph is the wrong container: the globe frames are 2.4MB each as
    PNG and circa 250KB as JPEG at the size they render. Charts and maps stay
    PNG, because JPEG artefacts on hairline rules and small mono type are
    immediately visible.
    """
    if photo:
        try:
            from PIL import Image
            import io
            im = Image.open(path)
            if max(im.size) > max_px:
                im.thumbnail((max_px, max_px), Image.LANCZOS)
            if im.mode in ("RGBA", "P", "LA"):
                im = im.convert("RGB")
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=84, optimize=True, progressive=True)
            return "data:image/jpeg;base64,%s" % base64.b64encode(
                buf.getvalue()).decode("ascii")
        except Exception:
            pass
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as fh:
        return "data:%s;base64,%s" % (mime,
                                      base64.b64encode(fh.read()).decode("ascii"))


def mono(text, size=12, colour=LABEL, ls="0.20em", weight=400, mb=0):
    return ('<div style="font-family:%s;font-size:%dpx;letter-spacing:%s;'
            'color:%s;font-weight:%d;margin-bottom:%dpx;">%s</div>'
            % (MONO, size, ls, colour, weight, mb, e(text).upper()))


# --- page furniture --------------------------------------------------------
def _head(sl, dark=False):
    """Eyebrow, title, italic subtitle, page number. The Observatory header."""
    ink = DARK_INK if dark else INK
    mut = DARK_MUTE if dark else MUTE
    gold = GOLD if dark else GOLD_D
    pg = DARK_LABEL if dark else "#9AA7B3"
    n = len(sl.get("title") or "")
    tsize = 46 if n <= 40 else (42 if n <= 52 else 38)
    out = ['<div style="display:flex;justify-content:space-between;'
           'align-items:flex-start;gap:40px;margin-bottom:28px;"><div>']
    if sl.get("section"):
        out.append(mono(sl["section"], 12, gold, "0.22em", mb=10))
    out.append('<h2 style="font-weight:500;font-size:%dpx;line-height:1.02;'
               'margin:0;color:%s;">%s</h2>' % (tsize, ink, e(sl.get("title"))))
    if sl.get("subtitle"):
        out.append('<div style="font-style:italic;font-size:19px;color:%s;'
                   'margin-top:9px;">%s</div>' % (mut, e(sl["subtitle"])))
    out.append("</div>")
    if sl.get("page"):
        out.append('<div style="font-family:%s;font-size:12px;letter-spacing:'
                   '0.18em;color:%s;padding-top:6px;">%02d</div>'
                   % (MONO, pg, sl["page"]))
    out.append("</div>")
    return "".join(out)


def _source(sl, dark=False):
    if not sl.get("source"):
        return ""
    col = DARK_DIM if dark else LABEL
    return ('<div style="margin-top:auto;padding-top:20px;border-top:1px solid %s;'
            'font-size:12.5px;line-height:1.5;color:%s;">%s</div>'
            % (DARK_RULE if dark else RULE_2, col, e(sl["source"])))


def _panel(p, dark=False):
    tone = p.get("tone", "neutral")
    if tone == "accent":
        bar, lab = GOLD_D, GOLD_D
    elif tone == "caution":
        bar, lab = CAUTION, CAUTION
    else:
        bar, lab = (DARK_RULE if dark else INK), (DARK_LABEL if dark else LABEL)
    body = DARK_INK if dark else INK
    out = ['<div style="border-top:2px solid %s;padding-top:14px;'
           'margin-bottom:26px;">' % bar]
    if p.get("title"):
        out.append(mono(p["title"], 11, lab, "0.18em", mb=12))
    for it in p["items"]:
        out.append('<div style="font-size:17px;line-height:1.42;color:%s;'
                   'margin-bottom:11px;">%s</div>' % (body, e(it)))
    out.append("</div>")
    return "".join(out)


def _callout(c, dark=False):
    tone = c.get("tone", "accent")
    if tone == "dark":
        bg, fg = INK, LIGHT_BG
    elif tone == "caution":
        bg, fg = CAUTION, "#F4F1EA"
    else:
        bg, fg = GOLD_D, "#FFFFFF"
    lines = "".join('<div style="font-size:19px;line-height:1.30;">%s</div>' % e(l)
                    for l in c["lines"])
    return ('<div style="background:%s;color:%s;padding:16px 22px;'
            'font-weight:500;">%s</div>' % (bg, fg, lines))


def _table(t, dark=False, compact=False):
    ink = DARK_INK if dark else INK
    lab = DARK_LABEL if dark else LABEL
    rule = DARK_RULE if dark else RULE
    strong = DARK_INK if dark else INK
    fs = 16 if compact or len(t["rows"]) > 8 else 19
    ws = t.get("widths")
    tot = sum(ws) if ws else None
    out = ['<table style="width:100%;border-collapse:collapse;">']
    out.append('<tr style="border-bottom:1px solid %s;">' % strong)
    for i, h in enumerate(t["head"]):
        wd = (' width="%.1f%%"' % (100.0 * ws[i] / tot)) if ws else ""
        al = "right" if i and _numericish(t, i) else "left"
        out.append('<th%s style="text-align:%s;font-family:%s;font-size:11px;'
                   'font-weight:500;letter-spacing:0.16em;color:%s;'
                   'padding:0 12px 10px 0;">%s</th>'
                   % (wd, al, MONO, lab, e(h).upper()))
    out.append("</tr>")
    n = len(t["rows"])
    for r, row in enumerate(t["rows"]):
        last = t.get("total") and r == n - 1
        bb = strong if last else rule
        out.append('<tr style="border-bottom:%s solid %s;">'
                   % ("2px" if last else "1px", bb))
        for i, cell in enumerate(row):
            al = "right" if i and _numericish(t, i) else "left"
            fam = MONO if (i and _numericish(t, i)) else SERIF
            fw = "500" if last else "400"
            out.append('<td style="text-align:%s;font-family:%s;font-size:%dpx;'
                       'font-weight:%s;color:%s;padding:11px 12px 11px 0;'
                       'line-height:1.3;">%s</td>'
                       % (al, fam, fs, fw, ink, e(cell)))
        out.append("</tr>")
    out.append("</table>")
    return "".join(out)


def _numericish(t, i):
    """A column is numeric if most of its cells start with a digit, $ or sign."""
    vals = [str(r[i]) for r in t["rows"] if i < len(r) and str(r[i]).strip()]
    if not vals:
        return False
    hits = sum(1 for v in vals if v[0].isdigit() or v[0] in "$£€+-")
    return hits >= max(1, len(vals) * 0.6)


def _bullets(bl, dark=False):
    ink = DARK_INK if dark else INK
    out = []
    for item in bl:
        # A bullet is either a (lead, rest) pair or a bare string. forecast_pack's
        # notes are bare strings, which render_pptx has always accepted; the first
        # HTML render of a forecast pack (the demo flow, 16 August 2026) threw here.
        # A bare string is a bullet with no bold lead, not an error.
        lead, rest = item if isinstance(item, (tuple, list)) else (None, item)
        lead = lead or ""
        out.append('<div style="display:flex;gap:14px;margin-bottom:13px;">'
                   '<div style="flex:0 0 6px;height:6px;border-radius:50%%;'
                   'background:%s;margin-top:10px;"></div>'
                   '<div style="font-size:17px;line-height:1.42;color:%s;">'
                   '<span style="font-weight:600;">%s</span> %s</div></div>'
                   % (GOLD_D, ink, e(lead), e(rest)))
    return "".join(out)


def _img(src, style=""):
    return '<img src="%s" alt="" style="%s">' % (e(src), style)


# --- slide renderers -------------------------------------------------------
def r_cover(sl, meta, assets):
    left = ['<div style="flex:0 0 57%%;padding:88px 76px 64px;display:flex;'
            'flex-direction:column;color:%s;">' % DARK_INK]
    left.append('<div style="display:flex;justify-content:space-between;'
                'align-items:flex-start;">')
    left.append('<div style="font-family:%s;font-size:13px;letter-spacing:0.24em;'
                'color:%s;line-height:1.9;">THE AVIATION OBSERVATORY<br>'
                'MERIDIAN &middot; ROUTE CASE ENGINE</div>' % (MONO, DARK_LABEL))
    left.append("</div>")
    left.append('<div style="margin-top:auto;">')
    left.append(mono("%s &middot; %s" % (meta["codename"], meta.get("strap_code", "")),
                     12, GOLD, "0.24em", mb=22)
                if meta.get("strap_code") else
                mono(meta["codename"], 12, GOLD, "0.24em", mb=22))
    lines = sl["title_lines"]
    left.append('<div style="font-weight:300;font-style:italic;font-size:34px;'
                'color:%s;line-height:1;">%s</div>' % (DARK_MUTE, e(lines[0])))
    rest = "<br>".join(e(l) for l in lines[1:])
    left.append('<div style="font-weight:500;font-size:104px;line-height:0.98;'
                'letter-spacing:-0.02em;margin:8px 0 0;">%s</div>' % rest)
    left.append('<div style="height:1px;background:%s;margin:40px 0 26px;"></div>'
                % DARK_RULE)
    left.append('<div style="display:flex;justify-content:space-between;'
                'align-items:flex-end;gap:40px;">')
    left.append('<div style="font-weight:300;font-size:24px;color:#E7E3D9;'
                'max-width:560px;line-height:1.35;">Prepared for %s</div>'
                % e(meta["prepared_for"]))
    meta_lines = [meta["event"], meta["date"].upper(), meta["confidentiality"].upper()]
    if meta.get("status"):
        meta_lines.append(meta["status"])
    left.append('<div style="text-align:right;font-family:%s;font-size:11px;'
                'letter-spacing:0.18em;color:%s;line-height:2;">%s</div>'
                % (MONO, DARK_LABEL, "<br>".join(e(x).upper() for x in meta_lines)))
    left.append("</div>")
    left.append('<div style="margin-top:34px;font-family:%s;font-size:11px;'
                'letter-spacing:0.18em;color:%s;">AVIA SOLUTIONS LIMITED'
                '&nbsp;&nbsp;&middot;&nbsp;&nbsp;AVIASOLUTIONS.COM</div>'
                % (MONO, DARK_DIM))
    left.append("</div></div>")
    fam = sl.get("family") or "globe"
    hero = assets(sl.get("image"), family=fam)
    pos = "50% 14%" if fam == "globe" else "50% 50%"
    right = ('<div style="flex:1;position:relative;border-left:1px solid %s;'
             'overflow:hidden;background:%s;">%s'
             '<div style="position:absolute;inset:0;background:linear-gradient'
             '(120deg,rgba(15,27,40,0.58),rgba(15,27,40,0.08) 60%%,'
             'rgba(15,27,40,0.30));mix-blend-mode:multiply;"></div></div>'
             % (GOLD, DARK_BG,
                _img(hero, "width:100%%;height:100%%;object-fit:cover;"
                           "object-position:%s;display:block;" % pos)
                if hero else _slot("library frame, globe")))
    return _section("Cover", DARK_BG, "".join(left) + right, flex=True, pad=None)


def _slot(label):
    return ('<div style="position:absolute;inset:0;display:flex;align-items:center;'
            'justify-content:center;background:%s;">'
            '<div style="font-family:%s;font-size:12px;letter-spacing:0.24em;'
            'color:%s;">IMAGE SLOT &middot; %s</div></div>'
            % (DARK_BG, MONO, DARK_DIM, e(label).upper()))


def r_divider(sl, meta, assets):
    left = ['<div style="flex:0 0 52%%;padding:88px 76px 64px;display:flex;'
            'flex-direction:column;color:%s;">' % DARK_INK]
    left.append(mono(meta["codename"], 12, DARK_LABEL, "0.24em"))
    left.append('<div style="margin-top:auto;">')
    left.append(mono("Section %s" % sl["number"], 13, GOLD, "0.26em", mb=26))
    left.append('<div style="font-weight:500;font-size:76px;line-height:1.02;'
                'letter-spacing:-0.015em;">%s</div>' % e(sl["title"]))
    left.append('<div style="height:1px;background:%s;margin:34px 0 24px;"></div>'
                % DARK_RULE)
    if sl.get("strap"):
        left.append('<div style="font-weight:300;font-style:italic;font-size:26px;'
                    'color:%s;max-width:620px;line-height:1.35;">%s</div>'
                    % (DARK_MUTE, e(sl["strap"])))
    left.append("</div></div>")
    fam = sl.get("family") or "field"
    img = assets(sl.get("image"), family=fam, prefer=sl.get("prefer"))
    pos = "50% 14%" if fam == "globe" else "50% 50%"
    right = ('<div style="flex:1;position:relative;border-left:1px solid %s;'
             'overflow:hidden;background:%s;">%s'
             '<div style="position:absolute;inset:0;background:linear-gradient'
             '(120deg,rgba(15,27,40,0.58),rgba(15,27,40,0.08) 60%%,'
             'rgba(15,27,40,0.30));mix-blend-mode:multiply;"></div></div>'
             % (GOLD, DARK_BG,
                _img(img, "width:100%%;height:100%%;object-fit:cover;"
                          "object-position:%s;display:block;" % pos)
                if img else _slot("library frame, %s" % fam)))
    return _section("S%s Divider" % sl["number"], DARK_BG,
                    "".join(left) + right, flex=True, pad=None)


def r_contents(sl, meta, assets):
    b = [_head(sl)]
    b.append('<div style="flex:1;display:flex;flex-direction:column;'
             'justify-content:center;">')
    for num, title, page in sl["items"]:
        b.append('<div style="display:flex;align-items:baseline;gap:28px;'
                 'padding:17px 0;border-bottom:1px solid %s;">'
                 '<div style="font-family:%s;font-size:13px;letter-spacing:0.18em;'
                 'color:%s;flex:0 0 40px;">%02d</div>'
                 '<div style="flex:1;font-size:27px;font-weight:400;color:%s;">%s</div>'
                 '<div style="font-family:%s;font-size:16px;color:%s;">%s</div></div>'
                 % (RULE, MONO, GOLD_D, int(num), INK, e(title), MONO, LABEL,
                    "%02d" % page if page else "&mdash;"))
    b.append("</div>")
    return _section("Contents", LIGHT_BG, "".join(b))


def r_grid(sl, meta, assets):
    b = [_head(sl)]
    b.append('<div style="flex:1;display:flex;flex-direction:column;'
             'justify-content:center;">')
    for i, (h, body) in enumerate(sl["rows"]):
        accent = i in sl.get("accent_rows", [])
        b.append('<div style="display:flex;gap:34px;padding:16px 0;'
                 'border-top:1px solid %s;">'
                 '<div style="flex:0 0 300px;font-size:21px;font-weight:600;'
                 'color:%s;line-height:1.22;">%s</div>'
                 '<div style="flex:1;font-size:17.5px;line-height:1.45;color:%s;">'
                 '%s</div></div>'
                 % (INK if accent else RULE_2, GOLD_D if accent else INK,
                    e(h), MUTE if not accent else INK, e(body)))
    b.append('<div style="border-top:1px solid %s;"></div>' % RULE_2)
    if sl.get("callout"):
        b.append('<div style="margin-top:24px;">%s</div>'
                 % _callout(sl["callout"]))
    b.append("</div>")
    b.append(_source(sl))
    return _section(sl["title"][:24], LIGHT_BG, "".join(b))


def r_keynumbers(sl, meta, assets):
    b = [_head(sl)]
    b.append('<div style="flex:1;display:grid;grid-template-columns:1fr 1fr;'
             'gap:0 60px;align-content:center;">')
    for i, (val, stmt) in enumerate(sl["items"]):
        b.append('<div style="padding:22px 0;border-top:1px solid %s;">'
                 '<div style="font-family:%s;font-size:52px;color:%s;'
                 'line-height:1;margin-bottom:14px;">%s</div>'
                 '<div style="font-size:18px;line-height:1.4;color:%s;">%s</div>'
                 '</div>' % (INK if i < 2 else RULE_2, MONO,
                             GOLD_D if i % 2 == 0 else INK, e(val), MUTE, e(stmt)))
    b.append("</div>")
    b.append(_source(sl))
    return _section("Key numbers", LIGHT_BG, "".join(b))


def r_stat_row(sl, meta, assets):
    b = [_head(sl)]
    n = len(sl["stats"])
    b.append('<div style="display:grid;grid-template-columns:repeat(%d,1fr);'
             'gap:0;border-top:1px solid %s;border-bottom:1px solid %s;">'
             % (n, INK, RULE_2))
    for i, (lab, val, accent) in enumerate(sl["stats"]):
        pad = ("26px 34px 26px 0" if i == 0 else
               ("26px 0 26px 34px" if i == n - 1 else "26px 34px"))
        br = ("" if i == n - 1 else "border-right:1px solid %s;" % RULE_2)
        col = GOLD_D if accent else INK
        b.append('<div style="padding:%s;%s">%s'
                 '<div style="font-family:%s;font-size:56px;color:%s;'
                 'line-height:1;">%s</div></div>'
                 % (pad, br, mono(lab, 11, GOLD_D if accent else LABEL,
                                  "0.18em", mb=12), MONO, col, e(val)))
    b.append("</div>")
    img = assets(sl.get("figure"))
    if img:
        b.append('<div style="margin-top:26px;flex:1;min-height:0;'
                 'border:1px solid %s;overflow:hidden;">%s</div>'
                 % (RULE_2, _img(img, "width:100%;height:100%;"
                                      "object-fit:cover;display:block;")))
    if sl.get("table"):
        b.append('<div style="margin-top:26px;">%s%s</div>'
                 % (mono("Schedule and configuration", 12, INK, "0.20em", mb=14),
                    _table(sl["table"], compact=True)))
    if sl.get("callouts"):
        b.append('<div style="display:grid;grid-template-columns:repeat(%d,1fr);'
                 'gap:20px;margin-top:24px;">%s</div>'
                 % (len(sl["callouts"]),
                    "".join(_callout(c) for c in sl["callouts"])))
    b.append(_source(sl))
    return _section("Summary", LIGHT_BG, "".join(b))


def r_table(sl, meta, assets):
    b = [_head(sl)]
    has_side = bool(sl.get("panels") or sl.get("callouts"))
    if sl.get("table2"):
        b.append('<div style="flex:1;display:grid;grid-template-columns:1fr 1fr;'
                 'gap:56px;min-height:0;"><div>%s</div><div>%s</div></div>'
                 % (_table(sl["table"]), _table(sl["table2"])))
        if sl.get("callouts"):
            b.append('<div style="display:grid;grid-template-columns:repeat(%d,1fr);'
                     'gap:20px;margin-top:26px;">%s</div>'
                     % (len(sl["callouts"]),
                        "".join(_callout(c) for c in sl["callouts"])))
    elif has_side:
        side = "".join(_panel(p) for p in sl.get("panels", []))
        side += "".join('<div style="margin-bottom:20px;">%s</div>' % _callout(c)
                        for c in sl.get("callouts", []))
        b.append('<div style="flex:1;display:grid;grid-template-columns:1fr 380px;'
                 'gap:52px;min-height:0;"><div>%s%s</div><div>%s</div></div>'
                 % (_table(sl["table"]),
                    ('<div style="margin-top:26px;">%s</div>'
                     % _bullets(sl["bullets"])) if sl.get("bullets") else "",
                    side))
    else:
        b.append('<div style="flex:1;min-height:0;">%s%s</div>'
                 % (_table(sl["table"]),
                    ('<div style="margin-top:26px;">%s</div>'
                     % _bullets(sl["bullets"])) if sl.get("bullets") else ""))
    b.append(_source(sl))
    return _section(sl["title"][:24], LIGHT_BG, "".join(b))


def r_figure(sl, meta, assets):
    b = [_head(sl)]
    img = assets(sl.get("image"))
    left = (('<div style="border:1px solid %s;background:#FFFFFF;padding:8px;">%s'
             "</div>" % (RULE_2, _img(img, "width:100%;display:block;")))
            if img else
            '<div style="border:1px dashed %s;height:420px;display:flex;'
            'align-items:center;justify-content:center;font-family:%s;'
            'font-size:12px;letter-spacing:0.2em;color:%s;">FIGURE SLOT</div>'
            % (RULE_2, MONO, LABEL))
    if sl.get("bullets"):
        left += '<div style="margin-top:24px;">%s</div>' % _bullets(sl["bullets"])
    side = ""
    if sl.get("table"):
        side += '<div style="margin-bottom:28px;">%s</div>' % _table(sl["table"],
                                                                    compact=True)
    side += "".join(_panel(p) for p in sl.get("panels", []))
    side += "".join('<div style="margin-bottom:20px;">%s</div>' % _callout(c)
                    for c in sl.get("callouts", []))
    b.append('<div style="flex:1;display:grid;grid-template-columns:1fr 420px;'
             'gap:52px;min-height:0;"><div>%s</div><div>%s</div></div>'
             % (left, side))
    b.append(_source(sl))
    return _section(sl["title"][:24], LIGHT_BG, "".join(b))


def r_prose(sl, meta, assets):
    b = [_head(sl)]
    body = []
    for h, para in sl["paras"]:
        if h:
            body.append('<div style="font-size:21px;font-weight:600;color:%s;'
                        'margin:0 0 8px;">%s</div>' % (INK, e(h)))
        body.append('<div style="font-size:17.5px;line-height:1.52;color:%s;'
                    'margin-bottom:24px;">%s</div>' % (MUTE, e(para)))
    side = "".join(_panel(p) for p in sl.get("panels", []))
    side += "".join('<div style="margin-bottom:20px;">%s</div>' % _callout(c)
                    for c in sl.get("callouts", []))
    if side:
        b.append('<div style="flex:1;display:grid;grid-template-columns:1fr 400px;'
                 'gap:56px;min-height:0;"><div>%s</div><div>%s</div></div>'
                 % ("".join(body), side))
    else:
        b.append('<div style="flex:1;columns:2;column-gap:56px;min-height:0;">'
                 '%s</div>' % "".join(body))
    b.append(_source(sl))
    return _section(sl["title"][:24], LIGHT_BG, "".join(b))


def r_thanks(sl, meta, assets):
    img = assets(sl.get("image"), family=sl.get("family") or "globe")
    inner = ('<div style="position:absolute;inset:0;">%s</div>'
             '<div style="position:absolute;inset:0;background:rgba(15,27,40,0.72);">'
             "</div>" % (_img(img, "width:100%;height:100%;object-fit:cover;"
                                   "display:block;") if img else ""))
    body = ('<div style="position:relative;height:100%%;display:flex;'
            'flex-direction:column;align-items:center;justify-content:center;'
            'color:%s;text-align:center;">'
            '<div style="font-weight:500;font-size:92px;line-height:1;">%s</div>'
            '<div style="height:1px;width:220px;background:%s;margin:36px 0 28px;">'
            "</div>"
            '<div style="font-weight:300;font-style:italic;font-size:28px;color:%s;">'
            "%s</div>"
            '<div style="margin-top:52px;font-family:%s;font-size:11px;'
            'letter-spacing:0.22em;color:%s;">AVIA SOLUTIONS LIMITED&nbsp;&nbsp;'
            "&middot;&nbsp;&nbsp;%s&nbsp;&nbsp;&middot;&nbsp;&nbsp;%s</div></div>"
            % (DARK_INK, e(sl["title"]), GOLD, DARK_MUTE, e(sl.get("strap") or ""),
               MONO, DARK_LABEL, e(meta["codename"]).upper(),
               e(meta["confidentiality"]).upper()))
    return _section("Thank you", DARK_BG, inner + body, pad=None, relative=True)


def _evidence_plate(img, subject, source, date, supports, on_ink=False):
    """The only sanctioned container for bespoke photography.

    Grade, frame and caption slug are fixed by chapter 14 and are not negotiable
    per image: one grade, one frame, eight photographers reading as one document.
    """
    frame = GOLD if on_ink else GOLD_D
    if img:
        art = ('<div style="position:relative;line-height:0;">'
               '%s'
               '<div style="position:absolute;inset:0;background:linear-gradient'
               '(180deg,rgba(15,27,40,0.14),rgba(15,27,40,0.46));'
               'mix-blend-mode:multiply;"></div>'
               '<div style="position:absolute;inset:0;background:%s;opacity:0.22;'
               'mix-blend-mode:soft-light;"></div></div>'
               % (_img(img, "display:block;width:100%;height:100%;"
                            "object-fit:cover;"
                            "filter:grayscale(1) contrast(1.04) brightness(1.01);"),
                  GOLD))
    else:
        # rule 04: a mono-ruled diagram, never a stock substitute
        art = ('<div style="aspect-ratio:3/2;display:flex;flex-direction:column;'
               'align-items:center;justify-content:center;background:%s;">'
               '<div style="font-family:%s;font-size:12px;letter-spacing:0.24em;'
               'color:%s;">NO RIGHTS-CLEARED PHOTOGRAPH</div>'
               '<div style="width:120px;height:1px;background:%s;margin:18px 0;">'
               '</div>'
               '<div style="font-family:%s;font-size:10px;letter-spacing:0.18em;'
               'color:%s;">DIAGRAM SUBSTITUTE &middot; NEVER STOCK</div></div>'
               % (LIGHT_BG, MONO, LABEL, GOLD_D, MONO, LABEL))
    slug = ('<div style="font-family:%s;font-size:9px;letter-spacing:0.16em;'
            'color:%s;line-height:1.9;margin-top:10px;">%s<br>SUPPORTS: %s</div>'
            '<div style="height:1px;background:%s;margin-top:8px;"></div>'
            % (MONO, LABEL,
               e("%s &middot; %s &middot; %s" % (subject, source, date)).upper()
               .replace("&AMP;MIDDOT;", "&middot;"),
               e(supports).upper(), RULE))
    return ('<figure style="margin:0;"><div style="border:1px solid %s;'
            'overflow:hidden;">%s</div>%s</figure>' % (frame, art, slug))


def r_plate(sl, meta, assets):
    """A body-grid slide carrying one evidence plate and the claim it supports."""
    b = [_head(sl)]
    img = assets(sl.get("slot"), kind="evidence", subjects=sl.get("subjects"))
    plate = _evidence_plate(img, sl["subject"], sl["credit"], sl["date"],
                            sl["supports"])
    side = []
    for h, para in sl.get("body", []):
        if h:
            side.append('<div style="font-size:21px;font-weight:600;color:%s;'
                        'margin:0 0 8px;">%s</div>' % (INK, e(h)))
        side.append('<div style="font-size:17.5px;line-height:1.52;color:%s;'
                    'margin-bottom:22px;">%s</div>' % (MUTE, e(para)))
    side += [_panel(p) for p in sl.get("panels", [])]
    b.append('<div style="flex:1;display:grid;grid-template-columns:1fr 1fr;'
             'gap:56px;min-height:0;align-content:start;"><div>%s</div>'
             '<div>%s</div></div>' % (plate, "".join(side)))
    b.append(_source(sl))
    return _section("Plate", LIGHT_BG, "".join(b))


RENDERERS = {"plate": r_plate, "cover": r_cover, "contents": r_contents, "divider": r_divider,
             "stat_row": r_stat_row, "keynumbers": r_keynumbers,
             "table": r_table, "figure": r_figure, "prose": r_prose,
             "grid": r_grid, "thanks": r_thanks}


def _section(label, bg, inner, flex=False, pad="60px 72px 40px", relative=False):
    style = ("height:100%%;box-sizing:border-box;background:%s;font-family:%s;"
             "color:%s;overflow:hidden;" % (bg, SERIF,
                                            DARK_INK if bg == DARK_BG else INK))
    if pad:
        style += "padding:%s;" % pad
    style += "display:flex;" + ("" if flex else "flex-direction:column;")
    if relative:
        style += "position:relative;"
    return ('<section data-label="%s" style="%s">%s</section>'
            % (e(label), style, inner))


# --- document --------------------------------------------------------------
SHELL = """<!DOCTYPE html>
<html lang="en-GB"><head><meta charset="utf-8">
<title>%(title)s</title>
<meta name="author" content="Avia Solutions">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="%(fonts)s" rel="stylesheet">
<style>
  html,body{margin:0;background:#11100c;}
  .deck{display:flex;flex-direction:column;align-items:center;gap:24px;padding:24px;}
  section{width:%(w)dpx;height:%(h)dpx;flex:0 0 auto;
          box-shadow:0 10px 40px rgba(0,0,0,0.45);}
  @media print{
    html,body{background:#fff;}
    .deck{gap:0;padding:0;}
    section{box-shadow:none;break-after:page;page-break-after:always;}
    @page{size:%(w)dpx %(h)dpx;margin:0;}
  }
</style></head>
<body><div class="deck">
%(slides)s
</div>
<script>
(function(){
  // scale to viewport when viewed on screen, untouched when printed
  function fit(){
    var s=Math.min((window.innerWidth-48)/%(w)d,1);
    document.querySelectorAll('.deck > section').forEach(function(el){
      el.style.transform='scale('+s+')';
      el.style.transformOrigin='top center';
      el.style.marginBottom=(-%(h)d*(1-s))+'px';
    });
  }
  window.addEventListener('resize',fit); fit();
})();
</script>
</body></html>
"""

DC_SHELL = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="./support.js"></script></head>
<body><x-dc><helmet>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="%(fonts)s" rel="stylesheet">
<style>body{margin:0;background:#11100c;} a{color:#b8862f;text-decoration:none;}</style>
</helmet>
<x-import component-from-global-scope="deck-stage" from="./deck-stage.js" width="%(w)d" height="%(h)d" hint-size="100%%,100%%">
%(slides)s
</x-import></x-dc></body></html>
"""


def render(spec, out_html, assets_dir="assets", dc=False, check=True,
           embed=True, resolver=None):
    """embed=True writes a single self-contained file: images become data URIs."""
    if check:
        S.check(spec)
    cache = {}

    def assets(name, kind="mood", subjects=None, family=None, prefer=None):
        if not name:
            return None
        # a generated figure is not photography: charts and maps resolve directly
        local = os.path.join(assets_dir, name)
        photo = True
        if os.path.exists(local) and name.lower().endswith(".png"):
            p = local
            photo = False
        elif resolver is not None:
            p, _src = resolver.resolve(name, family=family, subjects=subjects,
                                       kind=kind, prefer=prefer)
            if not p:
                return None
        else:
            p = local
        if not os.path.exists(p):
            return None
        if not embed:
            return os.path.relpath(p, os.path.dirname(os.path.abspath(out_html)))
        if p not in cache:
            cache[p] = _data_uri(p, photo=photo)
        return cache[p]

    parts = []
    for sl in spec["slides"]:
        fn = RENDERERS.get(sl["type"])
        if fn is None:
            raise ValueError("no Observatory renderer for slide type %r" % sl["type"])
        parts.append("<!-- %02d %s -->\n%s"
                     % (sl.get("page") or 0, sl["type"].upper(),
                        fn(sl, spec["meta"], assets)))
    doc = (DC_SHELL if dc else SHELL) % {
        "title": e(spec["meta"]["title"]), "fonts": FONTS,
        "w": W, "h": H, "slides": "\n".join(parts)}
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(doc)
    return out_html


def to_pdf(html_path, pdf_path):
    """Headless Chrome. Not available in a sandbox; run this on the workstation."""
    exe = next((c for c in ("google-chrome", "chromium", "chromium-browser",
                            "chrome", "msedge") if shutil.which(c)), None)
    if exe is None:
        print("No Chrome or Chromium found. On the workstation run:\n"
              '  chrome --headless --disable-gpu --no-pdf-header-footer \\\n'
              '         --print-to-pdf="%s" --virtual-time-budget=10000 "%s"'
              % (pdf_path, html_path))
        return None
    subprocess.run([exe, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    "--print-to-pdf=%s" % pdf_path,
                    "--virtual-time-budget=10000", html_path], check=True)
    return pdf_path


if __name__ == "__main__":
    import spec_goa_nyc
    import avia_slots

    spec = spec_goa_nyc.build()
    here = os.path.dirname(os.path.abspath(__file__))
    dc = "--dc" in sys.argv
    out = os.path.join(here, "Project_Liguria_Observatory%s.html"
                       % (".dc" if dc else ""))
    res = avia_slots.SlotResolver(
        uploads_dir=os.path.join(here, "uploads", "liguria"),
        subject_store=os.path.join(here, "image_store"),
        brand_library=os.path.join(here, "observatory_library"),
        project="liguria",
        origin=(8.6375, 44.4133))   # Genoa: the departure city sets the globe
    render(spec, out, assets_dir=os.path.join(here, "assets_obs"), dc=dc,
           embed="--linked" not in sys.argv, resolver=res)
    print("written:", out, "slides:", len(spec["slides"]))
    print(res.report())
    avia_slots.write_upload_guide(
        res, os.path.join(here, "Project_Liguria_image_upload_guide.md"),
        "Project Liguria")
    if "--pdf" in sys.argv:
        to_pdf(out, out.replace(".html", ".pdf"))
