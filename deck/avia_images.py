#!/usr/bin/env python3
"""Avia deck generator: licensed image store, built from Wikimedia Commons.

Why this exists
---------------
Commercially licensable stock coverage of named secondary airports and named
corporate campuses is thin to non-existent: no stock library can obtain a property
release for a trademarked campus, so that content sits in editorial-only, where a
client pitch deck cannot use it. Wikimedia Commons is the only source with real
depth on both. So the generator never resolves an image by keyword at render time.
It selects from this store, and every file in the store carries its licence record.

Run on the workstation, not on a dev PC and not in a sandbox. The store is data:
it lives at the path in avia_config.json and never in the tool repo.

Usage
-----
    python3 avia_images.py fop-refresh
    python3 avia_images.py fop Italy
    python3 avia_images.py fetch --subject "San Jose International Airport" \
                                 --tag sjc_terminal --country "United States" \
                                 --limit 12
    python3 avia_images.py fetch-set airports.json
    python3 avia_images.py list --tag sjc_terminal
    python3 avia_images.py credits --tags sjc_terminal,apple_park

Run fop-refresh before the first fetch. Until it has run the panorama table is
a twelve-country seed and every other country reads "unknown", which blocks a
published use and is advisory on a confidential one.

Rules this enforces
-------------------
1. Every file stores its full extmetadata block. That is the licence record.
2. ShareAlike files may be PLACED but not TREATED. Cropping or colour-grading a
   CC BY-SA image creates an adaptation, which would then have to be released
   under BY-SA. Unmodified placement in a deck is a collection, which is safe.
   Files are flagged `treatable: false` and the generator must honour it.
3. Freedom of panorama. Most countries permit commercial reproduction of a
   building photographed from a public place; a short and shifting list does
   not. Each file records the panorama status of the country it was taken in,
   from a table refreshed off Commons by `fop-refresh`. The status blocks a
   published use and is advisory on a confidential one.
4. Non-free, fair-use and "permission" templates are rejected outright.

Avia Solutions Limited. All rights reserved.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
UA = ("AviaDeckGenerator/1.0 (https://aviasolutions.com; "
      "john.carter@aviasolutions.com) python-urllib")

# Licences we accept, in order of preference. Anything not matching is rejected.
ACCEPTED = [
    ("public domain", "pd", True),
    ("cc0", "cc0", True),
    ("cc by 4.0", "cc-by-4.0", True),
    ("cc by 3.0", "cc-by-3.0", True),
    ("cc by 2.5", "cc-by-2.5", True),
    ("cc by 2.0", "cc-by-2.0", True),
    ("cc by-sa 4.0", "cc-by-sa-4.0", False),   # placeable, not treatable
    ("cc by-sa 3.0", "cc-by-sa-3.0", False),
    ("cc by-sa 2.5", "cc-by-sa-2.5", False),
    ("cc by-sa 2.0", "cc-by-sa-2.0", False),
]
REJECT_MARKERS = ("non-free", "fair use", "fairuse", "permission", "noncommercial",
                  "non-commercial", "nc-", "nd-", "no derivative", "gfdl only")

# ---------------------------------------------------------------------------
# Freedom of panorama
# ---------------------------------------------------------------------------
# Most of the world has it. Section 62 CDPA 1988 permits photographs of
# buildings permanently situated in a public place, including commercial use,
# which is why photographing a terminal has never been a problem in UK
# practice; the United States has its own provision for architectural works at
# 17 USC 120(a); Germany's UrhG s59 is broader still. The exceptions are a
# short list, and they move: Belgium had none until 27 June 2016 and now has
# one that covers commercial use.
#
# That last fact is the point. A list of countries hardcoded here would be
# wrong within a couple of years and nobody would notice. So the table is data,
# refreshed from Commons by `fop-refresh`, written to the store beside the
# images, and carrying the date it was pulled. What is below is a seed of the
# entries with a source behind them, used only until the first refresh runs.
FOP_TABLE_FILE = "fop_countries.json"
FOP_SOURCE = "https://commons.wikimedia.org/wiki/Commons:Freedom_of_panorama/AllRules"

# status values, from the point of view of a photograph of a BUILDING:
#   "ok"       buildings may be reproduced commercially
#   "none"     no exception, or one that excludes commercial use
#   "unknown"  not established. Treated as "none" for a published use.
FOP_SEED = {
    "united kingdom": ("ok", "CDPA 1988 s62, commercial use permitted"),
    "united states": ("ok", "17 USC 120(a), architectural works"),
    "germany": ("ok", "UrhG s59"),
    "belgium": ("ok", "panorama exception of 27 June 2016, commercial included"),
    "france": ("none", "2016 exception excludes commercial use"),
    "italy": ("none", "no panorama exception"),
    "greece": ("none", "no panorama exception"),
    "ukraine": ("none", "no panorama exception"),
    "belarus": ("none", "no panorama exception"),
    "luxembourg": ("none", "no panorama exception"),
    "sweden": ("none", "commercial use excluded"),
    "united arab emirates": ("none", "limited to broadcast programmes"),
}
FOP_SEED_DATE = "6 August 2026"

_FOP_CACHE = {}


def load_fop_table(store=None):
    """The refreshed table if the workstation has pulled one, else the seed."""
    if store:
        p = os.path.join(store, FOP_TABLE_FILE)
        if os.path.exists(p):
            if p not in _FOP_CACHE:
                with open(p, encoding="utf-8") as f:
                    _FOP_CACHE[p] = json.load(f)
            return _FOP_CACHE[p]
    return {"pulled": FOP_SEED_DATE, "source": "seed, verified by hand",
            "countries": {k: {"status": v[0], "note": v[1]}
                          for k, v in FOP_SEED.items()}}


def fop_status(country, store=None):
    """(status, note) for a photograph of a building in this country."""
    if not country:
        return "unknown", "no country recorded for the search"
    row = load_fop_table(store)["countries"].get(country.strip().lower())
    if not row:
        return "unknown", "not in the panorama table"
    return row["status"], row.get("note", "")


MIN_WIDTH = 1600          # below this an image will not carry a full-bleed slide
MIN_HEIGHT = 900
MAX_PER_ARTIST = 2        # one photographer's series is not a set of options

# Words that carry no discriminating power in a search, so a match on them alone
# means nothing. The first live run returned a beach in Goa, India for a search
# on "Genoa Cristoforo Colombo Airport", because Commons full-text matched the
# common words and the near-miss place name.
STOPWORDS = {"airport", "international", "the", "of", "and", "a", "an", "city",
             "terminal", "station", "port", "national", "de", "di", "del", "la",
             "le", "el", "at", "in", "on", "night", "aerial", "view"}

# Commons files cities under their local name. A search for Genoa must accept
# Genova, or the relevance filter throws away the best results: on the first
# live run the strongest Genoa airport frames were titled "Genova Airport".
# Aviation-relevant pairs only; extend as routes appear.
ALIASES = [
    {"genoa", "genova"}, {"milan", "milano"}, {"rome", "roma"},
    {"turin", "torino"}, {"naples", "napoli"}, {"florence", "firenze"},
    {"venice", "venezia"}, {"munich", "munchen", "muenchen"},
    {"cologne", "koln", "koeln"}, {"nuremberg", "nurnberg", "nuernberg"},
    {"vienna", "wien"}, {"prague", "praha"}, {"warsaw", "warszawa"},
    {"moscow", "moskva"}, {"athens", "athina", "athinai"},
    {"lisbon", "lisboa"}, {"seville", "sevilla"}, {"zurich", "zuerich"},
    {"geneva", "geneve", "genf"}, {"basel", "basle", "bale"},
    {"copenhagen", "kobenhavn", "koebenhavn"}, {"gothenburg", "goteborg"},
    {"antwerp", "antwerpen"}, {"bruges", "brugge"}, {"brussels", "bruxelles"},
    {"the hague", "hague", "haag"}, {"bucharest", "bucuresti"},
    {"belgrade", "beograd"}, {"beijing", "peking"}, {"mumbai", "bombay"},
    {"chennai", "madras"}, {"kolkata", "calcutta"}, {"yangon", "rangoon"},
    {"saigon", "chi", "minh"}, {"seoul", "incheon"}, {"tokyo", "tokio"},
]


def _fold(text):
    """Strip diacritics, so Zurich matches Zuerich and Munchen matches Munich.

    Folds before any split. Splitting on [^A-Za-z0-9] first would break
    "Munchen" into "M" and "nchen" at the umlaut and lose the match.
    """
    w = unicodedata.normalize("NFKD", text or "")
    w = "".join(c for c in w if not unicodedata.combining(c))
    return w.replace("\u00df", "ss").replace("\u00f8", "o").replace("\u0141", "L").lower()


def _words(text):
    """Folded token set of a free-text field."""
    return set(t for t in re.split(r"[^a-z0-9]+", _fold(text)) if t)


def _expand(token):
    """A token plus any local-name variants of it."""
    t = _fold(token)
    out = {t}
    for group in ALIASES:
        if t in group:
            out |= group
    return out


# ---------------------------------------------------------------------------
def _config(path=None):
    here = os.path.dirname(os.path.abspath(__file__))
    cfg = path or os.environ.get("AVIA_CONFIG") or os.path.join(here, "avia_config.json")
    if not os.path.exists(cfg):
        sys.exit("No config at %s.\n"
                 "Copy avia_config.example.json to avia_config.json and set "
                 "image_store." % cfg)
    with open(cfg) as f:
        raw = f.read()
    try:
        conf = json.loads(raw)
    except ValueError as err:
        hint = ""
        if "\\" in raw and "\\\\" not in raw:
            hint = ("\n\nLikely cause: single backslashes in a Windows path. JSON "
                    "reads \\A and \\d as escape sequences, so C:\\Avia fails.\n"
                    "Use forward slashes, which Python handles on Windows:\n"
                    '    "image_store": "C:/Avia/deck_images"')
        sys.exit("%s is not valid JSON: %s%s" % (cfg, err, hint))
    if not conf.get("image_store"):
        sys.exit("%s has no image_store. Set it to where the licensed images "
                 "should live, for example C:/Avia/deck_images" % cfg)
    return conf


def _api(params):
    params = dict(params, format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def _clip(text, n):
    """Trim to a word boundary, so a reason never breaks mid-word."""
    text = text or ""
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0]
    return (cut or text[:n]) + "..."


def _plain(v):
    """extmetadata values arrive as HTML. Strip it."""
    if not v:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(v))).strip()


def _key_tokens(subject):
    """The words in a subject that actually identify it."""
    toks = [t for t in re.split(r"[^A-Za-z0-9]+", subject.lower()) if len(t) > 2]
    return [t for t in toks if t not in STOPWORDS]


def classify(meta):
    """Return (licence_id, treatable, reason) or (None, False, reason) to reject."""
    blob = " ".join(_plain(meta.get(k, {}).get("value", "")).lower()
                    for k in ("LicenseShortName", "License", "UsageTerms",
                              "Copyrighted", "Permission"))
    for bad in REJECT_MARKERS:
        if bad in blob:
            return None, False, "rejected: %s" % bad
    for needle, lic, treatable in ACCEPTED:
        if needle in blob:
            return lic, treatable, "ok"
    return None, False, "no recognised licence in: %s" % blob[:120]


def relevant(subject, title, description, categories=""):
    """Is this file plausibly of the subject? Returns (keep, reason, score).

    A title match is worth more than a description match. Commons descriptions
    are free text and often name a whole province, so "Genova" in a caption may
    mean the photograph was taken in the region rather than at the airport: on
    the first Genoa run that let a photograph of mountains rank first. The
    filter still keeps those, because a regional shot is sometimes the right
    plate, but they rank below anything named for the subject.
    """
    keys = _key_tokens(subject)
    if not keys:
        return True, "no distinctive terms to check", 0
    in_title = _words(title)
    in_text = _words(" ".join((description or "", categories or "")))
    hits, score = [], 0
    for k in keys:
        variants = _expand(k)
        found = variants & in_title
        where = "title"
        if not found:
            found = variants & in_text
            where = "text"
        if not found:
            continue
        shown = k if k in found else "%s as %s" % (k, sorted(found)[0])
        hits.append(shown if where == "title" else "%s (text only)" % shown)
        score += 3 if where == "title" else 1
    if hits:
        return True, "matched " + ", ".join(hits), score
    return False, "no match on %s" % ", ".join(keys), 0


def search(subject, limit=20, min_width=MIN_WIDTH, default_country=None,
           store=None):
    """Search Commons for files on a subject and return scored candidates."""
    r = _api({"action": "query", "generator": "search",
              "gsrsearch": "filetype:bitmap %s" % subject,
              "gsrnamespace": "6", "gsrlimit": min(limit * 4, 100),
              "prop": "imageinfo",
              "iiprop": "url|size|extmetadata|mime",
              "iiurlwidth": "2400"})
    out = []
    for page in r.get("query", {}).get("pages", []):
        ii = (page.get("imageinfo") or [{}])[0]
        if not ii or ii.get("mime") not in ("image/jpeg", "image/png"):
            continue
        if (ii.get("width") or 0) < min_width or (ii.get("height") or 0) < MIN_HEIGHT:
            continue
        meta = ii.get("extmetadata", {})
        lic, treatable, reason = classify(meta)
        if lic is None:
            continue
        country = _plain(meta.get("Country", {}).get("value", "")).lower()
        desc = _plain(meta.get("ImageDescription", {}).get("value", ""))
        cats = _plain(meta.get("Categories", {}).get("value", ""))
        ok, why, score = relevant(subject, page["title"], desc, cats)
        if not ok:
            continue
        # The Country field is usually empty. Guessing it from words in the
        # filename is worse than useless: on the Genoa run it flagged the two
        # files with "Italy" in the title and passed five that were equally
        # Italian. Freedom of panorama depends on where the shutter fell, which
        # the operator knows from the subject, so it is declared per search.
        if not country:
            country = (default_country or "").lower()
        out.append({
            "relevance": why,
            "score": score,
            "title": page["title"],
            "url": ii.get("url"),
            "thumb": ii.get("thumburl"),
            "width": ii.get("width"),
            "height": ii.get("height"),
            "licence": lic,
            "treatable": treatable,
            "fop_status": fop_status(country, store)[0],
            "country": country,
            "artist": _plain(meta.get("Artist", {}).get("value", "")),
            "credit": _plain(meta.get("Credit", {}).get("value", "")),
            "licence_url": _plain(meta.get("LicenseUrl", {}).get("value", "")),
            "description": desc[:400],
            "date": _plain(meta.get("DateTimeOriginal", {}).get("value", "")),
            "extmetadata": {k: _plain(v.get("value", "")) for k, v in meta.items()},
        })
    # Rank by match strength, then permissiveness, then size. FOP risk is no
    # longer a sort key: once the country is declared, every file from one
    # search carries the same flag, and sorting on it only pushed the single
    # best Genoa frame to eighth behind a photograph of some mountains.
    out.sort(key=lambda c: (-c["score"], not c["treatable"], -c["width"]))
    # cap any one photographer: the first live run returned eight frames from a
    # single uploader's series, which is one option dressed as eight
    seen, capped = {}, []
    for c in out:
        who = (c["artist"] or c["credit"] or "unattributed").lower()[:60]
        seen[who] = seen.get(who, 0) + 1
        if seen[who] > MAX_PER_ARTIST:
            continue
        capped.append(c)
    return capped[:limit]


def fetch(subject, tag, store, limit=8, dry_run=False, country=None):
    """Search, download and record. Returns the manifest entries written."""
    os.makedirs(os.path.join(store, tag), exist_ok=True)
    manifest_path = os.path.join(store, "manifest.json")
    manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else {}
    entries = manifest.setdefault(tag, [])
    have = {e["title"] for e in entries}
    written = []
    for cand in search(subject, limit=limit, default_country=country,
                       store=store):
        if cand["title"] in have:
            continue
        ext = os.path.splitext(cand["url"])[1].lower() or ".jpg"
        slug = re.sub(r"[^a-z0-9]+", "_",
                      cand["title"].replace("File:", "").lower()).strip("_")[:60]
        fname = "%s_%s%s" % (tag, hashlib.sha1(
            cand["title"].encode()).hexdigest()[:8], ext)
        dest = os.path.join(store, tag, fname)
        flags = []
        if cand["fop_status"] != "ok":
            flags.append("FOP:%s" % cand["fop_status"])
        if not cand["treatable"]:
            flags.append("place only")
        print("  %2d  %-38s %-13s %9s  %-21s %s" % (
            cand["score"], slug[:38], cand["licence"],
            "%sx%s" % (cand["width"], cand["height"]),
            ", ".join(flags), _clip(cand["relevance"], 40)))
        if not dry_run:
            req = urllib.request.Request(cand["url"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r, open(dest, "wb") as f:
                f.write(r.read())
            time.sleep(0.4)          # be polite to Commons
        entry = dict(cand, file=os.path.relpath(dest, store), tag=tag,
                     subject=subject, fetched=time.strftime("%Y-%m-%d"))
        entries.append(entry)
        written.append(entry)
    if not dry_run:
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=1)
    return written


# ---------------------------------------------------------------------------
# Unattended selection
# ---------------------------------------------------------------------------
# There is no version of this where a person approves images for every airport
# in the world, so the rules have to be safe with nobody watching. What decides
# the architectural-copyright risk is what is in front of the lens, not which
# country the file came from: an aircraft on an Italian apron carries no
# architect's copyright, the terminal behind it does.
SUBJECT_RISK = {
    # a building is the subject, so an architect's copyright may subsist and
    # runs for their life plus seventy years
    "terminal": "architecture", "concourse": "architecture",
    "interior": "architecture", "pier": "architecture", "tower": "architecture",
    "station": "architecture", "stadium": "architecture", "museum": "architecture",
    "campus": "architecture", "hotel": "architecture", "hangar": "architecture",
    # a townscape carries modern architecture and, in Italy, heritage property
    # the state charges to reproduce commercially. Both ends are caught.
    "skyline": "architecture", "city": "architecture", "centre": "architecture",
    "oldtown": "architecture", "cathedral": "architecture", "square": "architecture",
    # nothing with an architect in front of the lens
    "airside": "clear", "apron": "clear", "runway": "clear", "taxiway": "clear",
    "aircraft": "clear", "airfield": "clear", "ramp": "clear", "stand": "clear",
    "coast": "clear", "harbour": "clear", "port": "clear", "quay": "clear",
    "landscape": "clear", "mountains": "clear", "countryside": "clear",
    "vineyard": "clear", "beach": "clear", "river": "clear", "lake": "clear",
}

# Licences a machine may act on alone. ShareAlike is absent deliberately: the
# Observatory grade is an adaptation, and so is a crop to fit a fixed frame,
# either of which would pull the whole deck into BY-SA. A ShareAlike file can
# still be placed by hand, unmodified, in the generic Avia style.
AUTO_LICENCES = {"pd", "cc0", "cc-by-4.0", "cc-by-3.0", "cc-by-2.5", "cc-by-2.0"}


def slot_risk(slot, subject=""):
    """Is a protected building the subject of this slot? Unknown means yes."""
    for token in _words(slot) | _words(subject):
        if token in SUBJECT_RISK:
            return SUBJECT_RISK[token]
    return "architecture"


def auto_ok(entry, slot, subject="", use="confidential"):
    """May this stored file be placed with nobody looking? (ok, reason).

    use   "confidential", a deliverable circulated to a named recipient, or
          "published", anything that goes on a website, into a tender or into
          a press release.

    Panorama risk turns on the use, not on the file. A photograph of a terminal
    in a confidential pitch deck is the ordinary practice of the industry and
    has never caused anyone a problem. The same photograph on a public website
    is a different act with a different audience, and in the handful of
    countries without a panorama exception it is the one worth stopping. So the
    flag advises on a confidential deck and blocks on a published one.
    """
    lic = (entry.get("licence") or "").lower()
    if lic not in AUTO_LICENCES:
        return False, "ShareAlike, so grading or cropping would adapt it"
    if lic.startswith("cc-by") and not (entry.get("artist") or entry.get("credit")):
        return False, "attribution required and no author recorded"
    if entry.get("fop_status", "unknown") != "ok" \
            and slot_risk(slot, subject) == "architecture":
        if use == "published":
            return False, "building is the subject, no panorama exception, published use"
        return True, "placed: no panorama exception, but confidential circulation"
    return True, "clear for unattended use"


# ---------------------------------------------------------------------------
def fop_refresh(store, show=0, force=False):
    """Pull the panorama country table off Commons and write it to the store.

    The first run is a probe. Commons renders each country through its own
    template and the exact wording is not something this could be tested
    against offline, so the command reports how it classified everything and
    refuses to replace a good table with a thin parse. Use --show to print the
    raw blocks and tighten MARKERS if the classification is coming out wrong.
    """
    r = _api({"action": "parse", "page": "Commons:Freedom of panorama/AllRules",
              "prop": "text"})
    html = (r.get("parse") or {}).get("text") or ""
    if not html:
        sys.exit("Commons returned no page text. Nothing written.")

    # rendered HTML, split on the country headings
    chunks = re.split(r"<h[23][^>]*>(.*?)</h[23]>", html)
    rows, unclear = {}, []
    for i in range(1, len(chunks) - 1, 2):
        country = _plain(chunks[i]).replace("[edit]", "").strip()
        body = _plain(chunks[i + 1])
        if not country or len(country) > 60:
            continue
        status, why = _classify_fop(body)
        rows[country.lower()] = {"status": status, "note": why,
                                 "text": body[:600]}
        if status == "unknown":
            unclear.append(country)

    print("parsed %d country blocks from Commons" % len(rows))
    for st in ("ok", "none", "unknown"):
        n = sum(1 for v in rows.values() if v["status"] == st)
        print("   %-8s %d" % (st, n))
    for country in sorted(rows)[:show]:
        print("\n--- %s [%s]\n%s" % (country, rows[country]["status"],
                                      rows[country]["text"][:300]))
    if unclear:
        print("\nnot classified (%d): %s" % (len(unclear),
              ", ".join(sorted(unclear)[:25]) + (" ..." if len(unclear) > 25 else "")))

    dest = os.path.join(store, FOP_TABLE_FILE)
    if len(rows) < 100 and not force:
        sys.exit("\nOnly %d countries parsed, which is too few to trust. The page "
                 "layout has probably changed.\nNothing written. Re-run with "
                 "--show 3 to see the blocks, or --force to write anyway." % len(rows))
    if sum(1 for v in rows.values() if v["status"] == "unknown") > len(rows) * 0.4 \
            and not force:
        sys.exit("\nOver 40 per cent unclassified, so the markers no longer match "
                 "the page wording.\nNothing written. Re-run with --show 5 and send "
                 "the output back.")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump({"pulled": time.strftime("%d %B %Y"), "source": FOP_SOURCE,
                   "countries": rows}, f, indent=1, ensure_ascii=False)
    _FOP_CACHE.pop(dest, None)
    print("\nwritten to %s" % dest)
    return rows


# Read from the point of view of a photograph of a building. Order matters:
# the negative forms are tested before the positive ones, because "not OK for
# commercial use" contains "OK".
MARKERS = [
    ("none", r"not ok"),
    ("none", r"no freedom of panorama"),
    ("none", r"\bnot\b[^.]{0,40}\bpermitted\b"),
    ("none", r"non-?commercial"),
    ("none", r"\bnot\b[^.]{0,30}\bcommercial\b"),
    ("none", r"only[^.]{0,30}\bnon-?commercial\b"),
    ("ok",   r"\bok\b"),
    ("ok",   r"freedom of panorama[^.]{0,40}\bexists\b"),
    ("ok",   r"\bpermitted\b"),
]


BUILDING_WORDS = ("building", "architect", "architectur", "structure", "edifice")


def _classify_fop(text):
    """Classify for BUILDINGS, which is the only thing our slots photograph.

    Plenty of countries read "OK for buildings, not OK for sculptures". Reading
    the block as one lump would find "not OK" and block terminal photographs
    across a lot of perfectly clear jurisdictions, so where the text separates
    the two, the clause about buildings is the one that counts.
    """
    t = " ".join((text or "").lower().split())[:900]
    if not t:
        return "unknown", "no text"
    clauses = [c.strip() for c in re.split(r"[.;]| but | however |, and | whereas ", t)
               if c.strip()]
    building = [c for c in clauses if any(w in c for w in BUILDING_WORDS)]
    for scope, label in ((building, "buildings clause"), ([t], "whole entry")):
        for chunk in scope:
            for status, pattern in MARKERS:
                m = re.search(pattern, chunk)
                if m:
                    return status, "%s, matched %r" % (label, m.group(0)[:30])
    return "unknown", "no marker matched"


def credits(store, tags):
    """Attribution block for the deck's credits slide. Required for every CC BY file."""
    manifest = json.load(open(os.path.join(store, "manifest.json")))
    lines = []
    for tag in tags:
        for e in manifest.get(tag, []):
            if e["licence"].startswith("pd") or e["licence"] == "cc0":
                continue
            lines.append("%s, %s, %s" % (
                e["title"].replace("File:", ""),
                e["artist"] or "unattributed",
                e["licence"].upper().replace("CC-", "CC ")))
    return lines


# ---------------------------------------------------------------------------
# The subject sets. One line per slot the generator can ask for.
# ---------------------------------------------------------------------------
def default_set(airport_name, airport_iata, city, extras=None):
    """Standard slots for any route deck. Extend per route."""
    s = [
        ("%s_terminal" % airport_iata.lower(), "%s airport terminal" % airport_name),
        ("%s_airside" % airport_iata.lower(), "%s airport aircraft apron" % airport_name),
        ("%s_skyline" % airport_iata.lower(), "%s skyline aerial" % city),
        ("%s_city" % airport_iata.lower(), "%s city centre" % city),
    ]
    return s + list(extras or [])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch")
    f.add_argument("--subject", required=True)
    f.add_argument("--tag", required=True)
    f.add_argument("--limit", type=int, default=8)
    f.add_argument("--country", help="where the subject is, for the freedom-of-"
                                     "panorama check, e.g. Italy")
    f.add_argument("--dry-run", action="store_true")

    fs = sub.add_parser("fetch-set",
                        help="JSON file: [[tag, subject, limit?, country?], ...]")
    fs.add_argument("path")
    fs.add_argument("--country")
    fs.add_argument("--dry-run", action="store_true")

    ls = sub.add_parser("list")
    ls.add_argument("--tag")

    fr = sub.add_parser("fop-refresh",
                        help="pull the freedom-of-panorama country table off "
                             "Commons into the store")
    fr.add_argument("--show", type=int, default=0,
                    help="print this many parsed country blocks")
    fr.add_argument("--force", action="store_true")

    fp = sub.add_parser("fop", help="what the table says about a country")
    fp.add_argument("country")

    cr = sub.add_parser("credits")
    cr.add_argument("--tags", required=True)

    a = ap.parse_args()
    store = _config()["image_store"]
    os.makedirs(store, exist_ok=True)

    if a.cmd == "fetch":
        print("%s -> %s%s" % (a.subject, a.tag,
              "" if a.country else "\n  (no --country given: the freedom-of-"
              "panorama check cannot run)"))
        print("  %2s  %-38s %-13s %9s  %-21s %s"
              % ("#", "file", "licence", "pixels", "flags", "matched on"))
        n = fetch(a.subject, a.tag, store, a.limit, a.dry_run, a.country)
        print("%s %d file(s)" % ("would take" if a.dry_run else "took", len(n)))
    elif a.cmd == "fetch-set":
        for row in json.load(open(a.path)):
            tag, subject = row[0], row[1]
            limit = row[2] if len(row) > 2 else 8
            country = row[3] if len(row) > 3 else a.country
            print("%s -> %s" % (subject, tag))
            fetch(subject, tag, store, limit, a.dry_run, country)
    elif a.cmd == "list":
        manifest = json.load(open(os.path.join(store, "manifest.json")))
        for tag, entries in sorted(manifest.items()):
            if a.tag and tag != a.tag:
                continue
            print("%s (%d)" % (tag, len(entries)))
            for e in entries:
                print("   %-40s %-14s treatable=%s panorama=%s" % (
                    os.path.basename(e["file"]), e["licence"],
                    e["treatable"], e.get("fop_status", "unknown")))
    elif a.cmd == "fop-refresh":
        fop_refresh(store, a.show, a.force)
    elif a.cmd == "fop":
        t = load_fop_table(store)
        st, note = fop_status(a.country, store)
        print("%s: %s%s" % (a.country, st, " (%s)" % note if note else ""))
        print("table pulled %s from %s" % (t.get("pulled"), t.get("source")))
    elif a.cmd == "credits":
        for line in credits(store, a.tags.split(",")):
            print(line)


if __name__ == "__main__":
    main()
