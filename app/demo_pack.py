#!/usr/bin/env python3
r"""The demonstration forecast pack: one run, rendered to a self-contained HTML file.

THE PACK IS THE FORECAST PACK, NOT THE PITCH. pitch_html.py renders the researched
airline pitch; this renders the forecast pack (the page set of John's 14 August ruling)
through the renderer that already existed for it: deck/forecast_pack.py builds the spec
from the deck contract, and deck/render_observatory.py renders a spec to a single HTML
file with the imagery embedded as data URIs. Nothing here computes a forecast and
nothing here draws a page; this module is the join plus the watermark.

A WARNED RUN IS NEVER PACKED. deck_from_cases' rule holds here: the portal warns, a
client artefact refuses. refuse_if_warned raises with the warnings named, and the
request endpoint calls it before any build starts.

THE WATERMARK is three independent layers, so it does not come off by deleting one
element: the cover carries DEMONSTRATION as its confidentiality line (in the spec, so
it is on the rendered page image of the cover); a stylesheet rule stamps every page
diagonally through CSS generated content, which has no element to delete; and a fixed
banner names the basis at the top of the file, with the document title amended to match.

Avia Solutions Limited. All rights reserved.
"""
import datetime
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_DECK = os.path.join(os.path.dirname(HERE), "deck")
for _p in (HERE, _DECK):
    if _p not in sys.path:
        sys.path.insert(0, _p)

DEFAULT_PACKS_DIR = r"E:\Avia\demo_packs"


def packs_dir():
    """Where built packs live: on the workstation with the data, never in the repo."""
    return os.environ.get("AVIA_DEMO_PACKS", "").strip() or DEFAULT_PACKS_DIR


def refuse_if_warned(fc):
    """A warned run is refused with its warnings named. The dashboard has already shown
    them; a pack that leaves the building must not carry a number the page will
    misdescribe."""
    warns = (fc or {}).get("warnings") or []
    if warns:
        raise RuntimeError("this run is not clean and is not emailed: "
                           + "; ".join(str(w) for w in warns))
    if not (fc or {}).get("ok"):
        raise RuntimeError("the forecast did not succeed: %s"
                           % (fc or {}).get("error", "no reason given"))


def run_ref(params):
    """A short stable reference for the run: the hash of its own parameters, so the lead
    store can say which run a pack was built from without storing the payload."""
    canon = json.dumps(params or {}, sort_keys=True, default=str)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:12]


# --- the watermark ----------------------------------------------------------

_STAMP_CSS = """
  /* DEMONSTRATION watermark (demo_pack.py). The rule stamps every page through CSS
     generated content: there is no watermark element on the page to delete, and the
     banner below is a second, independent layer. */
  .deck > section{position:relative;}
  .deck > section::after{content:"DEMONSTRATION";position:absolute;top:50%;left:50%;
    transform:translate(-50%,-50%) rotate(-28deg);font-family:Arial,sans-serif;
    font-weight:700;font-size:110px;letter-spacing:0.18em;color:rgba(120,90,30,0.10);
    pointer-events:none;white-space:nowrap;z-index:9;}
  .avia-demo-banner{position:fixed;top:0;left:0;right:0;z-index:99;background:#11100c;
    color:#c9a44a;border-bottom:1px solid #c9a44a;font-family:Arial,sans-serif;
    font-size:11px;letter-spacing:0.14em;text-transform:uppercase;text-align:center;
    padding:6px 10px;}
  @media print{.avia-demo-banner{position:static;}}
"""

_BANNER = ('<div class="avia-demo-banner">Demonstration forecast · Meridian, by The '
           'Aviation Observatory · not for reliance</div>')


def stamp_demonstration(html):
    """Inject the watermark layers into a rendered pack. Pure text-in, text-out, so the
    fixture test needs no renderer. Insertion points are the shell's own markers; if a
    marker is missing the layer is prepended rather than dropped, because a demo pack
    with no watermark is the failure that must not happen silently."""
    css = "<style>%s</style>" % _STAMP_CSS
    if "</head>" in html:
        html = html.replace("</head>", css + "\n</head>", 1)
    else:
        html = css + html
    if "<body>" in html:
        html = html.replace("<body>", "<body>" + _BANNER, 1)
    else:
        html = _BANNER + html
    if "<title>" in html:
        html = html.replace("<title>", "<title>DEMONSTRATION · ", 1)
    return html


# --- the build --------------------------------------------------------------

def _resolver(contract, codename):
    """Best-effort imagery resolver, the forecast_pack.main pattern condensed. None on
    any failure: the pack still renders, without photography, and the reason is
    printed rather than swallowed into a blank cover nobody explains."""
    try:
        import avia_slots
        origin = ((contract.get("route_metadata") or {}).get("origin_airport") or "")
        ll = None
        try:
            import airportsdata
            ap = (airportsdata.load("IATA").get(origin) or {})
            if ap.get("lat") is not None:
                ll = (ap["lon"], ap["lat"])
        except Exception:
            ll = None
        proj = (codename or origin or "pack").lower()
        lib = os.path.join(_DECK, "observatory_library")
        store = os.path.join(_DECK, "image_store")
        uploads = os.path.join(_DECK, "uploads", proj)
        try:
            import config as CFG
            lib = str(CFG.OBS_LIBRARY_DIR)
            store = str(getattr(CFG, "IMAGE_STORE_DIR",
                                os.path.join(str(CFG.ASSETS_DIR), "image_store")))
            uploads = os.path.join(str(CFG.ENGAGEMENT_ASSETS_DIR), proj)
        except Exception as e:                               # noqa: BLE001
            print("   IMAGES   config did not resolve (%s); falling back to deck/ "
                  "folders" % type(e).__name__)
        store = store if os.path.isdir(store) else None
        uploads = uploads if os.path.isdir(uploads) else None
        if not os.path.isdir(lib):
            print("   IMAGES   brand library not found at %s; the cover will be plain"
                  % lib)
        return avia_slots.SlotResolver(uploads_dir=uploads, subject_store=store,
                                       brand_library=lib, project=proj, origin=ll)
    except Exception as e:                                   # noqa: BLE001
        print("   IMAGES   no resolver (%s: %s); the pack renders without imagery"
              % (type(e).__name__, e))
        return None


def build_demo_pack_html(fc, out_path, catchment_ends=None, prepared_for="",
                         codename="Meridian demonstration"):
    """Forecast payload in, watermarked self-contained HTML out. Raises with the reason
    on a warned run or a failed build; the caller records the lead accordingly."""
    refuse_if_warned(fc)
    import forecast_to_contract as FTC
    import forecast_pack as FP
    import deck_spec as S
    import render_observatory as RO

    contract = FTC.contract_from_forecast(fc, currency="USD",
                                          catchment_ends=catchment_ends)
    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)
    maps = FP.render_maps(contract, os.path.join(out_dir, "pack_maps"),
                          codename=codename)
    today = datetime.date.today()
    spec, dropped = FP.build_pack(contract, codename=codename,
                                  prepared_for=prepared_for,
                                  date="%d %s" % (today.day, today.strftime("%B %Y")),
                                  confidentiality="DEMONSTRATION",
                                  author="The Aviation Observatory",
                                  maps=maps)
    spec["meta"]["status"] = "DEMONSTRATION"
    S.paginate(spec)
    for d in dropped:
        print("   DROPPED  %s: nothing in the contract to fill it" % d)
    RO.render(spec, out_path, embed=True, resolver=_resolver(contract, codename))
    with open(out_path, encoding="utf-8") as fh:
        html = fh.read()
    html = stamp_demonstration(html)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out_path
