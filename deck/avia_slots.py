#!/usr/bin/env python3
"""Image slot resolution for the deck generator.

A deck spec never names a file. It names a *slot*: what the picture is for, and
which Observatory photography family it must come from. The resolver decides
what actually fills it, in a fixed order of preference:

    1. The tool user's upload for this project, matched to the slot
    2. The tool user's upload matched to the slot's subject tags
    3. The licensed subject store, keyed by subject (Commons and stock, built
       by avia_images.py)
    4. The Observatory brand library, keyed by photography family
    5. A labelled empty slot, which the renderer draws deliberately

That order is the product: an airport that uploads its own photography gets its
own photography, and everything it does not upload still comes out finished.

Nothing here fetches anything. Fetching is avia_images.py, which runs on the
workstation and writes the licensed store. This module only chooses.

Avia Solutions Limited. All rights reserved.
"""

import glob
import hashlib
import json
import os
import re

import avia_images

FAMILIES = ("operations", "field", "globe", "instruments")
EXTS = (".jpg", ".jpeg", ".png", ".webp")

# The Globe family holds one frame per region. The cover takes the region of
# the DEPARTURE city, which personalises the document without leaving the
# library: mood stays Observatory, it just looks like the client's part of the
# world. Boxes are west, south, east, north in degrees, tested in order.
REGION_BOXES = [
    ("europe",        (-25.0, 34.0, 45.0, 72.0)),
    ("mena",          (-18.0, 12.0, 63.0, 40.0)),
    ("south-asia",    (60.0, 4.0, 92.0, 37.0)),
    ("africa",        (-18.0, -35.0, 52.0, 34.0)),
    ("pacific",       (-180.0, -30.0, -130.0, 30.0)),  # Hawaii and the mid-Pacific
    ("north-america", (-170.0, 14.0, -52.0, 72.0)),
    ("latin-america", (-95.0, -56.0, -33.0, 14.0)),
    ("apac",          (60.0, -48.0, 180.0, 55.0)),
    ("apac",          (-180.0, -48.0, -140.0, 30.0)),   # the dateline tail
]
# Pacific is tested before north-america so Honolulu draws the Hawaiian islands
# rather than the continental United States, and before the APAC dateline tail so
# the islands never turn up on a Tokyo or Sydney cover.
#
# South Asia is split out of APAC deliberately. One pool spanning Mumbai to
# Sydney means a Mumbai cover can come up centred on Japan, which a client
# notices immediately. Tested before the wider APAC box so it wins.


def region_for(lon, lat, default="europe"):
    """Which Globe frame a departure city takes. Longitude first, as in GIS."""
    for name, (w, s, e, n) in REGION_BOXES:
        if w <= lon <= e and s <= lat <= n:
            return name
    return default


def _licence_name(lic):
    """cc-by-sa-3.0 -> CC BY-SA 3.0, for the credits slide."""
    parts = (lic or "").split("-")
    if parts[:2] == ["cc", "by"]:
        rest = parts[2:]
        if rest[:1] == ["sa"]:
            return "CC BY-SA " + " ".join(rest[1:])
        return "CC BY " + " ".join(rest)
    return {"pd": "Public domain", "cc0": "CC0"}.get(lic, (lic or "").upper())


class SlotResolver:
    """Resolves spec slots to files. One instance per deck build.

    uploads_dir   where the tool user's own images land, per project
    subject_store the licensed store built by avia_images.py, tag subfolders
    brand_library the Observatory four families, one subfolder per family
    """

    def __init__(self, uploads_dir=None, subject_store=None, brand_library=None,
                 project=None, region=None, origin=None, use="confidential"):
        """region  the Globe frame this deck's cover takes, or origin=(lon, lat).

        use     "confidential" for a deliverable circulated to a named
                recipient, "published" for a website, tender or release.
                Panorama risk is advisory on the first and blocking on the
                second, so this is set once per engagement, not per image.
        """
        self.uploads_dir = uploads_dir
        self.subject_store = subject_store
        self.brand_library = brand_library
        self.project = project or "deck"
        self.origin = origin
        self.use = use
        self.region = region or (region_for(*origin) if origin else None)
        self.log = []
        self.refused = []    # (slot, file, why) for the rights report
        self.placed = []     # store entries actually used, for credits
        self._used = set()
        self._lib = self._load_library_rights()
        self._manifest = self._load_manifest()
        self._store = self._load_store()

    # -- inputs -------------------------------------------------------------
    def _load_manifest(self):
        """Optional uploads/manifest.json: {"slot": "file.jpg", ...}.

        Lets a user map their own filenames onto slots without renaming.
        """
        if not self.uploads_dir:
            return {}
        p = os.path.join(self.uploads_dir, "manifest.json")
        if not os.path.exists(p):
            return {}
        try:
            with open(p) as f:
                return json.load(f)
        except ValueError:
            self.log.append(("manifest", "unreadable", p))
            return {}

    def _load_library_rights(self):
        """The library manifest: region keys, restrictions and provenance.

        Reads brand_library/library.json, written by avia_library.py, and falls
        back to the older rights.json so an existing folder keeps working.

        A frame marked "restrict" is never auto-selected. Collection 1's gate
        frame carries a legible British Airways livery, which is fine on a BA
        deck and wrong on anyone else's, and that is not a judgement to leave
        to a hash.
        """
        if not self.brand_library:
            return {}
        p = os.path.join(self.brand_library, "library.json")
        if os.path.exists(p):
            try:
                with open(p) as f:
                    return json.load(f).get("frames", {})
            except ValueError:
                return {}
        p = os.path.join(self.brand_library, "rights.json")
        if not os.path.exists(p):
            return {}
        try:
            with open(p) as f:
                return json.load(f)
        except ValueError:
            return {}

    def _lib_meta(self, path):
        if not self.brand_library:
            return {}
        rel = os.path.relpath(path, self.brand_library).replace(os.sep, "/")
        return self._lib.get(rel) or {}

    def _load_store(self):
        if not self.subject_store:
            return {}
        p = os.path.join(self.subject_store, "manifest.json")
        if not os.path.exists(p):
            return {}
        with open(p) as f:
            return json.load(f)

    # -- helpers ------------------------------------------------------------
    @staticmethod
    def _tokens(path):
        """Filename split into whole tokens, lowercased.

        Tag matching is on tokens, never substrings: the tag "port" must not
        match "airport.aerial.jpg", which is exactly the kind of quiet mismatch
        that puts the wrong photograph on a client's slide.
        """
        stem = os.path.splitext(os.path.basename(path))[0].lower()
        return set(t for t in re.split(r"[^a-z0-9]+", stem) if t)

    def _tag_match(self, paths, tag):
        """Every token of the tag must appear as a token of the filename."""
        want = set(t for t in re.split(r"[^a-z0-9]+", tag.lower()) if t)
        if not want:
            return None
        hits = [p for p in paths
                if os.path.splitext(p)[1].lower() in EXTS
                and want <= self._tokens(p)]
        return sorted(hits)[0] if hits else None

    @staticmethod
    def _first(paths):
        paths = sorted(p for p in paths if os.path.splitext(p)[1].lower() in EXTS)
        return paths[0] if paths else None

    def _pick(self, candidates, slot):
        """Deterministic choice, avoiding a frame already used in this deck.

        Deterministic because two builds of the same deck must be identical, or
        a client watches the pictures move between drafts. No-repeat because the
        same runway on two consecutive dividers reads as a mistake, and with a
        small library a hash will collide often enough to matter.
        """
        if not candidates:
            return None
        candidates = sorted(candidates)
        fresh = [c for c in candidates if c not in self._used] or candidates
        h = int(hashlib.sha1(("%s/%s" % (self.project, slot)).encode()).hexdigest()[:8], 16)
        chosen = fresh[h % len(fresh)]
        self._used.add(chosen)
        return chosen

    @staticmethod
    def _sep(a, b):
        """Great-circle separation in degrees, good enough for choosing a frame."""
        import math
        lon1, lat1 = math.radians(a[0]), math.radians(a[1])
        lon2, lat2 = math.radians(b[0]), math.radians(b[1])
        return math.degrees(math.acos(max(-1.0, min(1.0,
            math.sin(lat1) * math.sin(lat2) +
            math.cos(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)))))

    # -- resolution ---------------------------------------------------------
    MAX_PLATES = 4          # chapter 14, rule 03: four evidence plates a report

    def resolve(self, slot, family=None, subjects=None, kind="mood",
                rights=None, prefer=None, generic_ok=False,
                generic_family="field"):
        """Return (path_or_None, source).

        kind      "mood" (library only) or "evidence" (bespoke permitted)
        rights    the licence or credit for an evidence plate. Chapter 14:
                  "No rights, no plate." An evidence image without a rights
                  record is refused, and the slot falls back to a diagram.
        generic_ok  where nothing clears, accept a library frame as a generic
                  equivalent, captioned illustrative. Only for plates that
                  carry no place-specific claim. Default off.
        """
        subjects = subjects or []

        if kind == "evidence":
            if len([r for r in self.log if r[3] == "evidence" and r[1] != "-"]) \
                    >= self.MAX_PLATES:
                return self._note(slot, None, "refused, four-plate limit reached",
                                  kind)
            return self._resolve_evidence(slot, subjects, rights,
                                          generic_ok, generic_family)
        return self._resolve_mood(slot, family, prefer=prefer)

    def _resolve_evidence(self, slot, subjects, rights,
                          generic_ok=False, generic_family="field"):
        if self.uploads_dir and os.path.isdir(self.uploads_dir):
            named = self._manifest.get(slot)
            if named:
                p = os.path.join(self.uploads_dir, named)
                if os.path.exists(p):
                    if not (rights or self._rights_for(named)):
                        return self._note(slot, None,
                                          "refused, no rights recorded", "evidence")
                    return self._note(slot, p, "upload, manifest", "evidence")
            hit = self._first(glob.glob(os.path.join(self.uploads_dir, slot + ".*")))
            if hit:
                if not (rights or self._rights_for(os.path.basename(hit))):
                    return self._note(slot, None, "refused, no rights recorded",
                                      "evidence")
                return self._note(slot, hit, "upload, named for the slot", "evidence")
            everything = glob.glob(os.path.join(self.uploads_dir, "*"))
            for tag in subjects:
                hit = self._tag_match(everything, tag)
                if hit:
                    if not (rights or self._rights_for(os.path.basename(hit))):
                        continue
                    return self._note(slot, hit, "upload, subject %s" % tag,
                                      "evidence")
        # The licensed store, most specific subject tag first, so an airport
        # frame beats a city frame and a city frame beats a regional one.
        # Nobody is going to approve images for every airport in the world, so
        # every candidate has to clear auto_ok() on its own.
        for tag in subjects:
            entries = self._store.get(tag) or []
            cleared, byfile = [], {}
            for e in entries:
                p = os.path.join(self.subject_store, e["file"])
                if not os.path.exists(p):
                    continue
                ok, why = avia_images.auto_ok(e, slot, e.get("subject", ""),
                                              use=self.use)
                if not ok:
                    self.refused.append((slot, os.path.basename(p), why))
                    continue
                cleared.append(p)
                byfile[p] = e
            hit = self._pick(cleared, slot)
            if hit:
                self.placed.append(byfile[hit])
                return self._note(slot, hit, "licensed store, subject %s" % tag,
                                  "evidence")
        # A generic equivalent, where the plate is decorative rather than
        # evidential. The spec has to say so: a library frame captioned as a
        # named airport would be presenting one place as another, which is the
        # one thing a plate must never do. So it is captioned illustrative and
        # the subject name is dropped.
        if generic_ok:
            path, src = self._resolve_mood(slot + ".generic", family=generic_family)
            if path:
                self.log.pop()          # re-file it as the evidence slot it fills
                return self._note(slot, path,
                                  "generic library frame, illustrative only",
                                  "evidence")
        # rule 04: a mono-ruled diagram, never a stock substitute
        return self._note(slot, None, "no photograph: diagram substitute",
                          "evidence")

    def _rights_for(self, filename):
        """uploads/rights.json maps filename to photographer or licence."""
        if not self.uploads_dir:
            return None
        p = os.path.join(self.uploads_dir, "rights.json")
        if not os.path.exists(p):
            return None
        try:
            with open(p) as f:
                return json.load(f).get(filename)
        except ValueError:
            return None

    def _resolve_mood(self, slot, family=None, prefer=None):
        """Library only. Chapter 14: never a client photograph, never stock.

        prefer  a filename token the slide would rather have, e.g. "runway" on
                the airport divider. Advisory: if the library does not hold it,
                the family choice stands.
        """

        if family and self.brand_library:
            d = os.path.join(self.brand_library, family)
            if os.path.isdir(d):
                every = [p for p in glob.glob(os.path.join(d, "*"))
                         if os.path.splitext(p)[1].lower() in EXTS]
                # a restricted frame is only ever reachable by explicit preference
                usable = [p for p in every if not self._lib_meta(p).get("restrict")]
                if prefer:
                    hit = self._tag_match(every, prefer)
                    if hit:
                        return self._note(slot, hit,
                                          "brand library, %s, preferred %s"
                                          % (family, prefer), "mood")
                # the Globe family is keyed by region, from the rights record
                if family == "globe" and self.region:
                    # within a region, prefer the frame whose centre is nearest
                    # the departure city: Lagos should not draw East Africa
                    inr = [p for p in usable
                           if self._lib_meta(p).get("region") == self.region]
                    withc = [p for p in inr if self._lib_meta(p).get("centre")]
                    if self.origin and len(withc) > 1:
                        fresh = [p for p in withc if p not in self._used] or withc
                        fresh.sort(key=lambda p: self._sep(
                            self._lib_meta(p)["centre"], self.origin))
                        self._used.add(fresh[0])
                        return self._note(slot, fresh[0],
                                          "brand library, globe, %s, nearest"
                                          % self.region, "mood")
                    # the departure region's own frames first, then the
                    # atmospheric frames, which belong to no region
                    for pool, why in (
                            ([p for p in usable
                              if self._lib_meta(p).get("region") == self.region],
                             self.region),
                            ([p for p in usable
                              if self._lib_meta(p).get("region") == "any"],
                             "atmospheric")):
                        hit = self._pick(pool, slot)
                        if hit:
                            return self._note(slot, hit,
                                              "brand library, globe, %s" % why,
                                              "mood")
                hit = self._pick(usable, slot)
                if hit:
                    return self._note(slot, hit, "brand library, %s" % family,
                                      "mood")
        return self._note(slot, None,
                          "empty, awaiting library %s" % (family or "frame"),
                          "mood")

    def _note(self, slot, path, source, kind="mood"):
        self.log.append((slot, os.path.basename(path) if path else "-", source,
                         kind))
        return path, source

    # -- reporting ----------------------------------------------------------
    def report(self):
        """What filled every slot, and what is still empty. Print at build time."""
        filled = [r for r in self.log if r[1] != "-"]
        empty = [r for r in self.log if r[1] == "-"]
        plates = [r for r in self.log if r[3] == "evidence"]
        out = ["IMAGE SLOTS: %d filled, %d empty (%d evidence plates, limit %d)"
               % (len(filled), len(empty), len(plates), self.MAX_PLATES)]
        for slot, fn, src, kind in self.log:
            out.append("   %-9s %-24s %-30s %s" % (kind.upper(), slot, fn, src))
        if self.refused:
            out.append("")
            out.append("REFUSED ON RIGHTS: %d file(s) held in the store but not "
                       "placed" % len(self.refused))
            for slot, fn, why in self.refused:
                out.append("   %-24s %-30s %s" % (slot, fn[:30], why))
        return "\n".join(out)

    def credits(self):
        """Attribution lines for the credits slide, for what was actually placed.

        Built from the files used, not from the store, so the deck never
        credits an image it did not carry and never omits one it did.
        """
        lines = []
        for e in self.placed:
            lic = (e.get("licence") or "").lower()
            if lic in ("pd", "cc0"):
                continue
            lines.append("%s, %s, %s" % (
                (e.get("title") or "").replace("File:", ""),
                e.get("artist") or "unattributed", _licence_name(lic)))
        return sorted(set(lines))

    def upload_template(self):
        """The list a tool user needs: every empty slot, and what it wants."""
        return [{"slot": s, "kind": k,
                 "wants": src.replace("empty, awaiting ", "")}
                for s, fn, src, k in self.log if fn == "-"]


def write_upload_guide(resolver, path, deck_title=""):
    """Write the drop-in guide the airport gets with the deck."""
    rows = resolver.upload_template()
    rows = [r for r in rows if r["kind"] == "evidence"]
    lines = ["# Image upload guide%s" % (" - %s" % deck_title if deck_title else ""),
             "",
             "Only evidence plates take client photography. Covers, section dividers,",
             "full-bleed frames and the closing page are Observatory library frames",
             "and are not open to upload (Brand Guidelines v1.3, chapter 14).",
             "",
             "Drop image files into the uploads folder for this project and rebuild.",
             "Name each file for its slot, for example `airport.aerial.jpg`, or map",
             "your own filenames in `manifest.json`:",
             "",
             "```json",
             json.dumps({r["slot"]: "your-file-name.jpg" for r in rows[:3]}, indent=2),
             "```",
             "",
             "JPEG, PNG or WebP, landscape, at least 2400 px on the long edge.",
             "Crop to 3:2 or 4:3. Every plate is graded, framed and captioned to the",
             "house recipe on placement, so supply the original rather than a",
             "treated file.",
             "",
             "**No rights, no plate.** Record the photographer or licence for each",
             "file in `rights.json`, keyed by filename. A file without a rights",
             "entry is refused and the slot falls back to a diagram.",
             "",
             "At most four plates in a report, one to a page.",
             "",
             "| Slot | What it wants |", "|---|---|"]
    for r in rows:
        lines.append("| `%s` | %s |" % (r["slot"], r["wants"]))
    if not rows:
        lines.append("| - | every slot is filled |")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path
